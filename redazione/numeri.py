"""Numeri di mercato dal dati.json del giorno (schema di controlli_dati.py): niente cifre scritte a mano.
- ticker_da_dati(path): le 7 caselle del ticker, con livelli e variazioni del giorno calcolati qui.
- fmt(v, dec), var(v0, v1, tipo, dec): formattazione all'italiana con segno esplicito.
Ogni serie di dati.json che entra nel PDF può avere "etichette": [nomi come compaiono nelle tabelle] e "tipo_var":
"pct" (prezzi, default), "pb" (rendimenti, livello in %), "punti" (VIX). controlli_numeri.py li confronta col PDF."""
import json

# (etichetta nel ticker, serie in dati.json, decimali del livello, unità del livello)
TICKER = [("MSCI ACWI (ETF)", "ACWI", 2, " $"), ("S&amp;P 500", "S&P 500", 2, ""), ("EURO STOXX 50", "Euro Stoxx 50", 2, ""),
          ("UST 10 ANNI", "Treasury 10 anni", 2, "%"), ("BRENT FUTURE", "Brent future", 2, " $"),
          ("EUR/USD", "EUR/USD", 4, ""), ("VIX", "VIX", 2, "")]


def fmt(v, dec=2):
    s = f"{abs(v):,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-" if v < 0 else "") + s


def var(v0, v1, tipo="pct", dec=1):
    if tipo == "pb":
        x, u, dec = round((v0 - v1) * 100), " pb", 0
    elif tipo == "punti":
        x, u = v0 - v1, ""
    else:
        x, u = (v0 / v1 - 1) * 100, "%"
    x = round(x, dec)
    return ("+" if x > 0 else "") + (fmt(x, dec) if x != 0 else fmt(0, dec)) + u


def tipo_var(s):
    return s.get("tipo_var") or ("pb" if s.get("mercato") == "UST" else "pct")


def ticker_da_dati(path="dati.json"):
    S = json.load(open(path, encoding="utf-8"))["serie"]
    out = []
    for et, nome, dec, unita in TICKER:
        s = S[nome]
        (_, v0, _), (_, v1, _) = s["ultimi"][0], s["ultimi"][1]
        t = tipo_var(s)
        out.append((et, fmt(v0, dec) + unita, var(v0, v1, t, 2 if t == "punti" else 1) + " g"))
    return out
