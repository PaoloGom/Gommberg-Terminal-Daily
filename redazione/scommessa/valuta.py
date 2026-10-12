"""Monitoraggio e verdetto della Scommessa.

Uso:
  Martedì-venerdì (a che punto siamo):
    python3 valuta.py --settimana ../pronostici/2026-10-19-settimana.json --attuali attuali.json --json stato.json
    attuali.json = {"spx": [7830.1, "2026-10-20"], ...}  (ultimo valore e data; se manca, ultima riga di dati/)
  Lunedì (verdetto della settimana chiusa venerdì):
    python3 valuta.py --settimana ../pronostici/2026-10-12-settimana.json --verdetto --json verdetto.json
    Usa le chiusure del venerdì in dati/ (aggiornale prima). Aggiunge le righe a registro.csv e rigenera PAGELLA.md.
"""
import argparse
import json
import math
import os

import numpy as np
import pandas as pd

from motore import QUANTILI, carica, pinball, punti_lettori, salva_json

QUI = os.path.dirname(os.path.abspath(__file__))
REGISTRO = os.path.join(QUI, "registro.csv")
PAGELLA = os.path.join(QUI, "PAGELLA.md")
PAR_DENTRO = 0.68  # probabilità attesa di cadere nel range 16-84%
PAR_DIREZIONE = json.load(open(os.path.join(QUI, "metodo.json"), encoding="utf-8"))["par_direzione"]
AZIONARI = ["acwi", "spx", "sx5e"]


def x_da_livello(base, liv, tipo):
    return math.log(liv / base) if tipo == "prezzo" else (liv - base) * 100


def segno(x, eps=1e-12):
    return 0 if abs(x) < eps else (1 if x > 0 else -1)


def stato(reg, attuali):
    righe = {}
    for k, v in reg["strumenti"].items():
        if k in attuali:
            ultimo, data = attuali[k]
        else:
            s = carica(k)
            ultimo, data = float(s.iloc[-1]), str(s.index[-1].date())
        base, prev = v["base"], v["previsione_redazione"]
        lo, hi = v["range"]
        var = x_da_livello(base, ultimo, v["tipo"])
        dir_prev = segno(prev - base)
        righe[k] = {"nome": v["nome"], "base": base, "previsione": prev, "ultimo": ultimo, "data": data,
                    "var": var * 100 if v["tipo"] == "prezzo" else var,
                    "var_unita": "%" if v["tipo"] == "prezzo" else "pb",
                    "dentro_range": bool(lo <= ultimo <= hi),
                    "strada_giusta": None if dir_prev == 0 else bool(segno(ultimo - base) == dir_prev)}
    return righe


def verdetto(reg, festivo=False):
    ven = pd.Timestamp(reg["settimana"].split("/")[1])
    righe, nuove = {}, []
    for k, v in reg["strumenti"].items():
        s = carica(k)
        s = s[s.index <= ven]
        data_fin = s.index[-1]
        if data_fin != ven and not festivo:
            raise SystemExit(f"{k}: manca la chiusura di venerdì {ven.date()} (ultima {data_fin.date()}): aggiorna dati/ "
                             "oppure, se venerdì la borsa era chiusa, rilancia con --festivo")
        fin = float(s.iloc[-1])
        base, prev, tipo = v["base"], v["previsione_redazione"], v["tipo"]
        lo, hi = v["range"]
        d, dentro = punti_lettori(base, prev, lo, hi, fin)
        y = x_da_livello(base, fin, tipo)
        qm = np.array([x_da_livello(base, v["quantili_modello"][str(q)], tipo) for q in QUANTILI])
        tilt = x_da_livello(base, prev, tipo)
        lv = np.array(QUANTILI)
        sg = v["sigma"]
        # perdite in unità di sigma: così prezzi e Treasury pesano allo stesso modo
        pm, pr = pinball(y / sg, qm / sg, lv), pinball(y / sg, (qm + tilt) / sg, lv)
        r = {"settimana": reg["settimana"], "strumento": k, "nome": v["nome"], "base": base, "finale": fin,
             "data_finale": str(data_fin.date()), "previsione": prev, "lo": lo, "hi": hi, "punto_direzione": d,
             "punto_range": dentro, "pinball_modello": pm, "pinball_redazione": pr,
             "z": y / sg if sg else float("nan"), "versione_metodo": reg.get("versione_metodo", "0")}
        note = []
        if str(data_fin.date()) != str(ven.date()):
            note.append(f"mercato chiuso venerdì: vale l'ultima chiusura del {data_fin.date()}")
        if k == "brent" and sg and abs(y / sg) > 3:
            note.append("variazione oltre 3 sigma: controllare un possibile cambio di contratto del future")
        r["nota"] = "; ".join(note)
        righe[k] = r
        nuove.append(r)
    df_new = pd.DataFrame(nuove)
    if os.path.exists(REGISTRO):
        old = pd.read_csv(REGISTRO)
        old = old[old["settimana"] != reg["settimana"]]
        df = pd.concat([old, df_new], ignore_index=True)
    else:
        df = df_new
    df.to_csv(REGISTRO, index=False)
    scrivi_pagella(df)
    tot = int(df_new["punto_direzione"].sum() + df_new["punto_range"].sum())
    return righe, {"punti": tot, "su": 2 * len(df_new), "direzione": int(df_new["punto_direzione"].sum()),
                   "range": int(df_new["punto_range"].sum()),
                   "par": round(sum(PAR_DENTRO + PAR_DIREZIONE.get(k, 0.5) for k in df_new["strumento"]), 1)}


def hac_t(d, lag=4):
    d = np.asarray(d, float)
    n, m = len(d), d.mean()
    e = d - m
    v = e @ e / n + sum(2 * (1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n for k in range(1, min(lag, n - 1) + 1))
    return m / math.sqrt(v / n) if v > 0 else float("nan")


def scrivi_pagella(df):
    sett = df.groupby("settimana").agg(direzione=("punto_direzione", "sum"), range=("punto_range", "sum"),
                                       n=("strumento", "count"), pm=("pinball_modello", "mean"),
                                       pr=("pinball_redazione", "mean"))
    n_sett = len(sett)
    punti = int(sett["direzione"].sum() + sett["range"].sum())
    su = int(2 * sett["n"].sum())
    par = round(sum(PAR_DENTRO + PAR_DIREZIONE.get(k, 0.5) for k in df["strumento"]), 1)
    az = df[df["strumento"].isin(AZIONARI)]
    su_az = 100 * float((az["finale"] > az["base"]).mean()) if len(az) else float("nan")
    red_az = 100 * float(az["punto_direzione"].mean()) if len(az) else float("nan")
    cop = 100 * df["punto_range"].mean()
    dirr = 100 * df["punto_direzione"].mean()
    skill = 100 * (1 - df["pinball_redazione"].mean() / df["pinball_modello"].mean())
    t = hac_t(sett["pm"] - sett["pr"]) if n_sett >= 26 else float("nan")
    z = df["z"].dropna()
    L = ["# Pagella della Scommessa (generata da valuta.py, non modificare a mano)", "",
         f"Settimane valutate: {n_sett}. Punti totali: {punti} su {su} (par senza abilità: {par}).", "",
         "| Misura | Valore | Atteso se il metodo è giusto |", "|---|---|---|",
         f"| Chiusure dentro il range 16-84% | {cop:.0f}% | circa 68% |",
         f"| Direzione giusta (previsione della redazione) | {dirr:.0f}% | 50% senza abilità |",
         f"| Abilità della redazione sul modello (perdita quantile) | {skill:+.1f}% | >0 se gli scarti aggiungono valore |",
         f"| t di Diebold-Mariano redazione vs modello | {'n.d. (servono 26 settimane)' if t != t else f'{t:.2f}'} | >=2 per dire che la redazione batte il modello |",
         f"| Azionari: direzione giusta della redazione contro 'sempre su' | {red_az:.0f}% contro {su_az:.0f}% | la redazione deve battere 'sempre su' |",
         f"| Sorprese oltre 2 sigma | {100 * float((z.abs() > 2).mean()):.0f}% | circa 5% |", "",
         "## Settimana per settimana", "", "| Settimana | Direzione | Range | Totale |", "|---|---|---|---|"]
    for s_, r in sett.iterrows():
        L.append(f"| {s_} | {int(r['direzione'])}/{int(r['n'])} | {int(r['range'])}/{int(r['n'])} | {int(r['direzione'] + r['range'])}/{2 * int(r['n'])} |")
    L += ["", "## Per strumento", "", "| Strumento | Settimane | Dentro il range | Direzione giusta |", "|---|---|---|---|"]
    for k, g in df.groupby("nome"):
        L.append(f"| {k} | {len(g)} | {100 * g['punto_range'].mean():.0f}% | {100 * g['punto_direzione'].mean():.0f}% |")
    open(PAGELLA, "w", encoding="utf-8").write("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--settimana", required=True)
    ap.add_argument("--attuali")
    ap.add_argument("--verdetto", action="store_true")
    ap.add_argument("--json")
    ap.add_argument("--festivo", action="store_true", help="venerdì a borse chiuse: vale l'ultima chiusura della settimana")
    a = ap.parse_args()
    reg = json.load(open(a.settimana, encoding="utf-8"))
    if a.verdetto:
        righe, tot = verdetto(reg, a.festivo)
        out = {"righe": righe, "totale": tot}
        print(f"Verdetto {reg['settimana']}: {tot['punti']} punti su {tot['su']} (direzione {tot['direzione']}, "
              f"range {tot['range']}; par {tot['par']})")
    else:
        att = json.load(open(a.attuali, encoding="utf-8")) if a.attuali else {}
        out = {"righe": stato(reg, att)}
        for k, r in out["righe"].items():
            print(f"{r['nome']:18s} ultimo {r['ultimo']:.4g} ({r['data']}) var {r['var']:+.2f}{r['var_unita']} "
                  f"dentro {r['dentro_range']} strada {r['strada_giusta']}")
    if a.json:
        salva_json(out, a.json)


if __name__ == "__main__":
    main()
