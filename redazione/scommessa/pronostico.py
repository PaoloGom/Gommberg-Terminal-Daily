"""Pronostico della settimana (si esegue il lunedì).

Uso:
  python3 pronostico.py --origine 2026-10-16 [--redazione redazione.json] [--uscita ../pronostici]

- origine: data dell'ultima chiusura nota (il venerdì precedente). I file in dati/ devono arrivare almeno a quella data
  (aggiornali prima con aggiorna_dati.py).
- redazione.json (obbligatorio): {"spx": {"previsione": 7840, "motivo": "..."}, ...} per tutti gli strumenti di metodo.json (6 dalla versione 1.1). È la scommessa:
  ogni strumento ha una direzione. Lo scarto dalla chiusura di partenza va da 0,1 a 0,5 sigma (metodo.json): sotto 0,1 viene
  portato a 0,1 nella stessa direzione, sopra 0,5 viene limitato a 0,5.
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
ATTIVI = {k: v for k, v in STRUMENTI.items() if k in METODO["strumenti"]}   # gli strumenti della scommessa in vigore


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


def pronostica(origine: pd.Timestamp, redazione: dict):
    vix_d = carica("vix")
    out = {}
    for k, info in ATTIVI.items():
        cfg = METODO["strumenti"][k]
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
        # previsione della redazione, limitata a +-0,5 sigma
        red = redazione.get(k, {})
        if "previsione" not in red:
            raise SystemExit(f"{k}: manca la previsione della redazione (la scommessa richiede una direzione per ogni strumento)")
        x = math.log(red["previsione"] / base) if tipo == "prezzo" else (red["previsione"] - base) * 100
        lim = METODO["redazione"]["scarto_massimo_in_sigma"] * sg
        minimo = METODO["redazione"]["scarto_minimo_in_sigma"] * sg
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
        }
    return out


def prova(origine):
    """Sigma e livelli a +-0,1 / 0,3 / 0,5 sigma per scegliere la previsione della redazione."""
    vix_d = carica("vix")
    print(f"{'Strumento':18s} {'base':>10s} {'sigma':>9s}   giù 0,5 / 0,3 / 0,1   |   su 0,1 / 0,3 / 0,5")
    for k, info in ATTIVI.items():
        s = carica(k)
        s = s[s.index <= origine]
        r = variazioni_giornaliere(s, info["tipo"])
        sg = sigma_alla_data(k, METODO["strumenti"][k]["vol"], r, origine, vix_d)
        b = float(s.iloc[-1])
        liv = [livello(b, m * sg, info["tipo"]) for m in (-0.5, -0.3, -0.1, 0.1, 0.3, 0.5)]
        su = f"{sg:.4f}" if info["tipo"] == "prezzo" else f"{sg:.1f} pb"
        print(f"{k:18s} {b:10.4f} {su:>9s}   " + " / ".join(f"{x:.4f}" for x in liv[:3]) + "   |   " +
              " / ".join(f"{x:.4f}" for x in liv[3:]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--origine", required=True)
    ap.add_argument("--redazione")
    ap.add_argument("--uscita", default=os.path.join(QUI, "..", "pronostici"))
    ap.add_argument("--prova", action="store_true", help="stampa sigma e livelli possibili senza scrivere nulla")
    ap.add_argument("--forza", action="store_true", help="sovrascrive un registro esistente (solo per correggere un errore)")
    a = ap.parse_args()
    origine = pd.Timestamp(a.origine)
    if origine.dayofweek != 4:
        raise SystemExit("--origine deve essere un venerdì (l'ultima chiusura della settimana precedente)")
    red = json.load(open(a.redazione, encoding="utf-8")) if a.redazione else {}
    if a.prova:
        prova(origine)
        return
    if not a.redazione:
        raise SystemExit("serve --redazione (oppure --prova per vedere sigma e livelli)")
    st = pronostica(origine, red)
    lun = (origine + pd.Timedelta(days=3)).date()
    ven = (origine + pd.Timedelta(days=7)).date()
    reg = {"schema": 2, "versione_metodo": METODO["versione"], "data_pronostico": str(lun),
           "settimana": f"{lun}/{ven}", "origine": str(origine.date()), "verdetto_previsto": str(ven + dt.timedelta(days=3)),
           "range_pubblicato": "16-84% (circa 2 settimane su 3 la chiusura cade dentro)", "strumenti": st}
    os.makedirs(a.uscita, exist_ok=True)
    nome = os.path.join(a.uscita, f"{lun}-settimana.json")
    if os.path.exists(nome) and not a.forza:
        raise SystemExit(f"{nome} esiste già: il pronostico della settimana non si riscrive (usa --forza solo per correggere un errore)")
    salva_json(reg, nome)
    print("scritto", nome)
    for k, v in st.items():
        print(f"{v['nome']:18s} base {v['base']:.4f} range {v['range'][0]:.4f}-{v['range'][1]:.4f} "
              f"redazione {v['previsione_redazione']:.4f} (scarto {v['scarto_redazione_sigma']:+.2f} sigma"
              f"{', AGGIUSTATA' if v['aggiustata'] else ''}) p_rialzo {v['prob_rialzo_redazione']:.0%} [{v['metodo']}]")


if __name__ == "__main__":
    main()
