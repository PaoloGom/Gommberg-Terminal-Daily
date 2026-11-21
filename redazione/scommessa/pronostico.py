"""Pronostico della settimana (si esegue il lunedì).

Uso:
  python3 pronostico.py --origine 2026-10-16 [--redazione redazione.json] [--uscita ../pronostici]

- origine: data dell'ultima chiusura nota (il venerdì precedente). I file in dati/ devono arrivare almeno a quella data
  (aggiornali prima con aggiorna_dati.py).
- redazione.json (obbligatorio), metodo 1.3: {"_scenario": "...", "spx": {"mattino_var": 0.6, "tipo": "mattino", "motivo": "..."},
  "ust10": {"mattino_var": -1, "tipo": "catalizzatore", "previsione": 4.80, "motivo": "..."}, ...} per tutti gli strumenti di metodo.json.
  _scenario = la nostra lettura della settimana, cioè il riquadro "La nostra tesi" di pag. 6 così come lo leggerà il lettore:
  che cosa ci aspettiamo e da quale evento datato dipende, poi "Ci smentirebbe:" e il fatto che ci darebbe torto.
  mattino_var = variazione da venerdì già vista stamattina (% per i prezzi, punti base per i tassi; si omette se non verificabile).
  tipo = perché scegliamo quella direzione, uno di metodo.json > redazione > tipi_motivo:
    mattino        il mercato si è già mosso di almeno 0,1 sigma: la direzione è quella, lo scarto è il movimento (tetto 0,3 sigma);
    fondo          mattino fermo e storia che pende al rialzo (borse, oro): su di 0,1 sigma;
    scenario       mattino fermo: la direzione che discende dallo scenario della settimana, 0,1 sigma (serve "previsione");
    catalizzatore  un evento datato nella settimana, scritto nel motivo: unico tipo che può andare contro il mattino, fino a 0,3 sigma
                   (serve "previsione").
Scrive <uscita>/<origine+3gg>-settimana.json e stampa una tabella di controllo. Il grafico si disegna con grafico.py.
"""
import argparse
import datetime as dt
import json
import math
import os

import numpy as np
import pandas as pd

from motore import (STRUMENTI, QUANTILI, carica, variazioni_giornaliere, chiusure_settimanali, vol_rv, vol_ewma,
                    vol_blend, vol_vix, sigma_metodo, quantili_normale, quantili_t, quantili_empirici, prob_rialzo, livello, salva_json)

QUI = os.path.dirname(os.path.abspath(__file__))
METODO = json.load(open(os.path.join(QUI, "metodo.json"), encoding="utf-8"))
ATTIVI = {k: STRUMENTI[k] for k in METODO["strumenti"]}   # gli strumenti della scommessa in vigore, nell'ordine di metodo.json
SMENTITA = "Ci smentirebbe:"   # l'etichetta che pagina6.py mette in grassetto nel riquadro "La nostra tesi"
SCENARIO_MAX = 200             # caratteri: due righe del riquadro, quanto la tesi che si scriveva a mano fino alla n. 026


def controlla_scenario(s):
    """Lo scenario è il testo che il lunedì si stampa in pag. 6: una posizione e che cosa la smentirebbe, in due righe."""
    if not s:
        raise SystemExit(f'manca "_scenario": che cosa ci aspettiamo questa settimana e da quale evento datato dipende, poi '
                         f'"{SMENTITA}" e il fatto che ci darebbe torto (APP_LUNEDI.md §3)')
    prima, _, dopo = s.partition(SMENTITA)
    if s.count(SMENTITA) != 1 or len(prima.split()) < 4 or len(dopo.split()) < 3:
        raise SystemExit(f'"_scenario": prima che cosa ci aspettiamo, poi una volta sola "{SMENTITA}" e il fatto che ci darebbe '
                         f'torto (APP_LUNEDI.md §3)')
    if len(s) > SCENARIO_MAX:
        raise SystemExit(f'"_scenario" è lungo {len(s)} caratteri, il massimo è {SCENARIO_MAX}: è il riquadro "La nostra tesi" di '
                         f'pag. 6, due righe. Togli ciò che è già scritto nei sei motivi')


def sigma_alla_data(chiave, vol, r, t, vix_d=None):
    rr = r[r.index <= t]
    v = float(vix_d[vix_d.index <= t].iloc[-1]) if vol == "vix" else None
    return sigma_metodo(vol, rr, v)


def z_storici(chiave, vol, tipo, s, r, origine, vix_d, settimane=520):
    """Variazioni settimanali passate divise per la sigma che il metodo avrebbe stimato allora (solo passato)."""
    w = chiusure_settimanali(s)
    w = w[w.index <= origine]
    z = []
    for i in range(max(1, len(w) - settimane), len(w)):
        t0, t1 = w.index[i - 1], w.index[i]
        if len(r[r.index <= t0]) < 260:
            continue
        sg = sigma_alla_data(chiave, vol, r, t0, vix_d)
        y = math.log(w.iloc[i] / w.iloc[i - 1]) if tipo == "prezzo" else (w.iloc[i] - w.iloc[i - 1]) * 100
        if sg > 0:
            z.append(y / sg)
    return np.array(z)


def strumenti_settimana(variabile=None):
    """I 6 fissi più, se c'è, lo strumento della settimana (preparato da variabile.py in dati/var_*.json)."""
    att = {k: dict(v) for k, v in ATTIVI.items()}
    if variabile:
        meta_p = os.path.join(QUI, "dati", variabile + ".json")
        if not os.path.exists(meta_p):
            raise SystemExit(f"{variabile}: manca {meta_p}: prepara lo strumento con variabile.py")
        m = json.load(open(meta_p, encoding="utf-8"))
        att[variabile] = {"nome": m["nome"], "tipo": m["tipo"], "unita": m.get("unita", ""), "variabile": True,
                          "motivo_scelta": m.get("motivo_scelta", "")}
    return att


def pronostica(origine: pd.Timestamp, redazione: dict, variabile=None):
    vix_d = carica("vix")
    out = {}
    for k, info in strumenti_settimana(variabile).items():
        cfg = METODO["strumenti"].get(k, {"vol": "rv20", "forma": "normale"})   # lo strumento variabile: il metodo base
        tipo = info["tipo"]
        s = carica(k)
        s = s[s.index <= origine]
        if s.index[-1] < origine - pd.Timedelta(days=1):
            raise SystemExit(f"{k}: dati fermi al {s.index[-1].date()}, serve la chiusura del {origine.date()}: aggiorna dati/")
        r = variazioni_giornaliere(s, tipo)
        base = float(s.iloc[-1])
        data_base = str(s.index[-1].date())
        sg = sigma_alla_data(k, cfg["vol"], r, origine, vix_d)
        if cfg["forma"] == "normale":
            qx = quantili_normale(0.0, sg)
        elif cfg["forma"] == "t5":
            qx = quantili_t(0.0, sg, 5)
        else:
            z = z_storici(k, cfg["vol"], tipo, s, r, origine, vix_d)
            qx = quantili_empirici(0.0, sg, z) if len(z) >= 156 else quantili_t(0.0, sg, 5)
        # previsione della redazione (metodo 1.3): si parte dal mattino, ogni chiamata ha un tipo, la convinzione ha un tetto
        red = redazione.get(k, {})
        cfg_r = METODO["redazione"]
        minimo = cfg_r["scarto_minimo_in_sigma"] * sg
        soglia = cfg_r.get("soglia_mattino_in_sigma", 0.1) * sg
        tipi = cfg_r.get("tipi_motivo")
        tipo_m, g = red.get("tipo"), None
        if red.get("mattino_var") is not None:
            mv = float(red["mattino_var"])
            g = math.log(1 + mv / 100) if tipo == "prezzo" else mv
            if abs(g) > 3 * sg:
                raise SystemExit(f"{k}: mattino_var {mv} vale {g / sg:+.1f} sigma: controlla il dato (% per i prezzi, punti base per i tassi)")
        mosso = g is not None and abs(g) >= soglia
        if tipi:
            if tipo_m not in tipi:
                raise SystemExit(f"{k}: manca il tipo del motivo, uno tra {', '.join(tipi)} (APP_LUNEDI.md §3)")
            if not str(red.get("motivo", "")).strip():
                raise SystemExit(f"{k}: manca il motivo")
            if tipo_m == "mattino":
                if not mosso:
                    raise SystemExit(f"{k}: tipo 'mattino' ma da venerdì il mercato non si è mosso di almeno "
                                     f"{cfg_r.get('soglia_mattino_in_sigma', 0.1)} sigma: scegli fondo, scenario o catalizzatore")
                red = dict(red, previsione=livello(base, g, tipo))          # la direzione è quella del mattino
            elif mosso and tipo_m != "catalizzatore":
                raise SystemExit(f"{k}: il mercato si è già mosso di {g / sg:+.2f} sigma: il tipo è 'mattino', oppure "
                                 f"'catalizzatore' se un evento datato ti fa andare contro")
            elif tipo_m == "fondo":
                if METODO["par_direzione"].get(k, 0.5) <= 0.5:
                    raise SystemExit(f"{k}: tipo 'fondo' vale solo dove la storia pende al rialzo (par_direzione sopra 0,5)")
                red = dict(red, previsione=livello(base, minimo, tipo))     # la tendenza di fondo è al rialzo
        if "previsione" not in red:
            raise SystemExit(f"{k}: manca la previsione della redazione (la scommessa richiede una direzione per ogni strumento)")
        x = math.log(red["previsione"] / base) if tipo == "prezzo" else (red["previsione"] - base) * 100
        lim = cfg_r["scarto_massimo_in_sigma"] * sg
        if tipi and tipo_m in cfg_r.get("tipi_a_scarto_minimo", ()):
            lim = minimo
        tilt = max(-lim, min(lim, x))
        if abs(tilt) < minimo:
            if x == 0:
                raise SystemExit(f"{k}: previsione uguale alla chiusura di partenza: scegli una direzione")
            tilt = math.copysign(minimo, x)
        out[k] = {
            "nome": info["nome"], "unita": info["unita"], "tipo": tipo,
            "base": base, "data_base": data_base,
            "sigma": sg, "sigma_unita": "log-rendimento" if tipo == "prezzo" else "punti base",
            "metodo": f"{cfg['vol']}|{cfg['forma']}",
            "quantili_modello": {str(q): livello(base, x, tipo) for q, x in zip(QUANTILI, qx)},
            "mediana_modello": base,
            "range": [livello(base, qx[QUANTILI.index(0.16)], tipo), livello(base, qx[QUANTILI.index(0.84)], tipo)],
            "previsione_redazione": livello(base, tilt, tipo),
            "scarto_redazione_sigma": round(tilt / sg, 3) if sg else 0.0,
            "motivo_redazione": red.get("motivo", ""),
            "aggiustata": bool(abs(tilt - x) > 1e-12),
            "prob_rialzo_modello": 0.5,
            "prob_rialzo_redazione": prob_rialzo(tilt, sg, cfg["forma"]),
            "tipo_motivo": tipo_m or "",
            "mattino_sigma": None if g is None else round(g / sg, 3),
            "contro_mattino": bool(mosso and tilt * g < 0),
        }
        if info.get("variabile"):
            out[k].update(variabile=True, motivo_scelta=info.get("motivo_scelta", ""))
    return out


def prova(origine, variabile=None):
    """Sigma e livelli a +-0,1 / 0,2 / 0,3 sigma per scegliere la previsione della redazione (0,1 = predefinito)."""
    vix_d = carica("vix")
    print(f"{'Strumento':18s} {'base':>10s} {'sigma':>9s}   giù 0,3 / 0,2 / 0,1   |   su 0,1 / 0,2 / 0,3")
    for k, info in strumenti_settimana(variabile).items():
        s = carica(k)
        s = s[s.index <= origine]
        r = variazioni_giornaliere(s, info["tipo"])
        sg = sigma_alla_data(k, METODO["strumenti"].get(k, {"vol": "rv20"})["vol"], r, origine, vix_d)
        b = float(s.iloc[-1])
        liv = [livello(b, m * sg, info["tipo"]) for m in (-0.3, -0.2, -0.1, 0.1, 0.2, 0.3)]
        su = f"{sg:.4f}" if info["tipo"] == "prezzo" else f"{sg:.1f} pb"
        so = METODO["redazione"].get("soglia_mattino_in_sigma", 0.1) * sg
        so = f"{(math.exp(so) - 1) * 100:.2f}%" if info["tipo"] == "prezzo" else f"{so:.1f} pb"
        print(f"{k:18s} {b:10.4f} {su:>9s}   " + " / ".join(f"{x:.4f}" for x in liv[:3]) + "   |   " +
              " / ".join(f"{x:.4f}" for x in liv[3:]) + f"   |   mattino: conta da +-{so}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--origine", required=True)
    ap.add_argument("--redazione")
    ap.add_argument("--uscita", default=os.path.join(QUI, "..", "pronostici"))
    ap.add_argument("--prova", action="store_true", help="stampa sigma e livelli possibili senza scrivere nulla")
    ap.add_argument("--forza", action="store_true", help="sovrascrive un registro esistente (solo per correggere un errore)")
    ap.add_argument("--variabile", help="lo strumento della settimana (var_<chiave>, preparato con variabile.py)")
    a = ap.parse_args()
    origine = pd.Timestamp(a.origine)
    if origine.dayofweek != 4:
        raise SystemExit("--origine deve essere un venerdì (l'ultima chiusura della settimana precedente)")
    if a.variabile and os.environ.get("GTD_STRUMENTO_SETTIMANA") != "1":
        raise SystemExit("Lo strumento della settimana è sospeso dal 14/11/2026 (APP_LUNEDI.md §3b): rilancia senza "
                         "--variabile, la scommessa esce con i sei mercati fissi")
    red = json.load(open(a.redazione, encoding="utf-8")) if a.redazione else {}
    if a.prova:
        prova(origine, a.variabile)
        return
    if not a.redazione:
        raise SystemExit("serve --redazione (oppure --prova per vedere sigma e livelli)")
    scenario = " ".join(str(red.get("_scenario", "")).split())
    if METODO["redazione"].get("tipi_motivo"):
        controlla_scenario(scenario)
    st = pronostica(origine, red, a.variabile)
    motivi = [v["motivo_redazione"].strip().lower() for v in st.values()]
    if METODO["redazione"].get("tipi_motivo") and len(set(motivi)) < len(motivi):
        raise SystemExit("due mercati hanno lo stesso motivo: ogni riga dice che cosa muove o che cosa aspetta QUEL mercato")
    lun = (origine + pd.Timedelta(days=3)).date()
    ven = (origine + pd.Timedelta(days=7)).date()
    # schema 3 (21/11/2026): lo scenario è il testo che pagina6.py stampa il lunedì nel riquadro "La nostra tesi"
    reg = {"schema": 3, "versione_metodo": METODO["versione"], "data_pronostico": str(lun),
           "settimana": f"{lun}/{ven}", "origine": str(origine.date()), "verdetto_previsto": str(ven + dt.timedelta(days=3)),
           "range_pubblicato": "16-84% (circa 2 settimane su 3 la chiusura cade dentro)", "scenario": scenario, "strumenti": st}
    os.makedirs(a.uscita, exist_ok=True)
    nome = os.path.join(a.uscita, f"{lun}-settimana.json")
    if os.path.exists(nome) and not a.forza:
        raise SystemExit(f"{nome} esiste già: il pronostico della settimana non si riscrive (usa --forza solo per correggere un errore)")
    salva_json(reg, nome)
    print("scritto", nome)
    for k, v in st.items():
        print(f"{v['nome']:18s} base {v['base']:.4f} range {v['range'][0]:.4f}-{v['range'][1]:.4f} "
              f"redazione {v['previsione_redazione']:.4f} (scarto {v['scarto_redazione_sigma']:+.2f} sigma"
              f"{', AGGIUSTATA' if v['aggiustata'] else ''}) p_rialzo {v['prob_rialzo_redazione']:.0%} [{v['metodo']}] "
              f"tipo {v['tipo_motivo'] or '-'}, mattino {'n.d.' if v['mattino_sigma'] is None else format(v['mattino_sigma'], '+.2f') + ' sigma'}"
              f"{' CONTRO IL MATTINO' if v['contro_mattino'] else ''}")
    contro = [v["nome"] for v in st.values() if v["contro_mattino"]]
    if len(contro) > 2:
        print(f"AVVISO: {len(contro)} chiamate contro il mattino ({', '.join(contro)}): di norma non più di 2 su 6. Rileggi i catalizzatori.")


if __name__ == "__main__":
    main()
