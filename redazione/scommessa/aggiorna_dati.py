"""Aggiunge osservazioni giornaliere alle serie storiche di dati/ (le serie crescono ogni settimana e servono ai backtest).

Uso: python3 aggiorna_dati.py nuovi.json
nuovi.json = {"spx": [["2026-10-12", 7809.94], ...], "sx5e": [...], "vix": [...], "brent_future": [...],
              "ust10": [...], "ust2": [...], "eurusd": [...], "acwi": [...]}
Solo chiusure ufficiali (mai valori intraday). Le date già presenti vengono sovrascritte con il valore nuovo.
"""
import json
import os
import sys

import pandas as pd

DATI = os.environ.get("GOMMBERG_DATI", os.path.join(os.path.dirname(os.path.abspath(__file__)), "dati"))
nuovi = json.load(open(sys.argv[1], encoding="utf-8"))
NOMI = {"spx", "sx5e", "vix", "brent_future", "ust10", "ust2", "eurusd", "acwi"}
for nome, righe in nuovi.items():
    if nome not in NOMI:
        raise SystemExit(f"serie sconosciuta: {nome} (ammesse: {sorted(NOMI)})")
    for d, v in righe:
        pd.Timestamp(d)  # errore se la data non è valida
        if not isinstance(v, (int, float)) or v != v or v <= 0:
            raise SystemExit(f"{nome} {d}: valore non valido {v!r}")
        if pd.Timestamp(d).dayofweek > 4:
            raise SystemExit(f"{nome} {d}: data di sabato o domenica")
    righe = [[pd.Timestamp(d).strftime("%Y-%m-%d"), float(v)] for d, v in righe]
    f = os.path.join(DATI, f"{nome}.csv")
    vecchi = pd.read_csv(f) if os.path.exists(f) else pd.DataFrame(columns=["data", "valore"])
    add = pd.DataFrame(righe, columns=["data", "valore"])
    df = pd.concat([vecchi, add]).drop_duplicates("data", keep="last").sort_values("data")
    df = df.tail(260)  # nel repository pubblico teniamo solo l'ultimo anno: basta al modello (20 sedute) e limita i dati dei fornitori
    df.to_csv(f, index=False)
    print(f"{nome}: {len(add)} righe, ultima {df['data'].iloc[-1]} = {df['valore'].iloc[-1]}")
