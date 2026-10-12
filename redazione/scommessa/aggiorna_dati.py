"""Aggiunge chiusure giornaliere ufficiali alle serie di dati/ (le serie crescono ogni settimana).

Uso: python3 aggiorna_dati.py nuovi.json
nuovi.json = {"spx": [["2026-10-12", 7809.94], ...], "sx5e": [...], "vix": [...], "brent": [...],
              "ust10": [...], "ust2": [...], "eurusd": [...], "acwi": [...]}
Stesse chiavi dei registri della scommessa (più "vix"). Solo chiusure ufficiali di giorni già finiti: le date di oggi o
future vengono rifiutate, perché i fornitori (es. FMP eod-light) restituiscono già una riga con la data di oggi che è un
valore intraday. Prima si controlla tutto, poi si scrive: o si aggiornano tutte le serie o nessuna.
"""
import datetime as dt
import json
import os
import sys
from zoneinfo import ZoneInfo

import pandas as pd

DATI = os.environ.get("GOMMBERG_DATI", os.path.join(os.path.dirname(os.path.abspath(__file__)), "dati"))
NOMI = {"spx", "sx5e", "vix", "brent", "ust10", "ust2", "eurusd", "acwi"}
oggi = dt.datetime.now(ZoneInfo("Europe/Rome")).date()
nuovi = json.load(open(sys.argv[1], encoding="utf-8"))
if not nuovi:
    print("Nessuna riga nuova: dati/ invariato")
    sys.exit(0)
pulite = {}
for nome, righe in nuovi.items():
    if nome not in NOMI:
        raise SystemExit(f"serie sconosciuta: {nome} (ammesse: {sorted(NOMI)}). Nessun file modificato.")
    out = []
    for d, v in righe:
        t = pd.Timestamp(d)
        if not isinstance(v, (int, float)) or v != v or v <= 0:
            raise SystemExit(f"{nome} {d}: valore non valido {v!r}. Nessun file modificato.")
        if t.dayofweek > 4:
            raise SystemExit(f"{nome} {d}: data di sabato o domenica. Nessun file modificato.")
        if t.date() >= oggi:
            raise SystemExit(f"{nome} {d}: data di oggi o futura, quindi non una chiusura. Nessun file modificato.")
        out.append([t.strftime("%Y-%m-%d"), float(v)])
    pulite[nome] = out
for nome, righe in pulite.items():
    f = os.path.join(DATI, f"{nome}.csv")
    vecchi = pd.read_csv(f) if os.path.exists(f) else pd.DataFrame(columns=["data", "valore"])
    df = pd.concat([vecchi, pd.DataFrame(righe, columns=["data", "valore"])]).drop_duplicates("data", keep="last")
    df = df.sort_values("data").tail(260)  # nel repository pubblico teniamo solo l'ultimo anno
    df.to_csv(f, index=False)
    print(f"{nome}: +{len(righe)} righe, ultima {df['data'].iloc[-1]} = {df['valore'].iloc[-1]}")
