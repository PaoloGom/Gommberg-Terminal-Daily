"""Memoria delle ricerche: dove sono stati trovati i dati difficili e quali sono rimasti mancanti.
Legge le schede "sezione": "ricerca" archiviate in redazione/fatti/ (ultimi 60 giorni) e stampa al massimo 8 righe:
"dato -> fonte che l'ha dato (testata, ricerca che ha funzionato)" e i mancanti recenti. prepara.sh lo chiama ogni mattina.
Scheda (in fatti.json, una per dato che ha richiesto più di una ricerca o che manca):
{"id": "R1", "sezione": "ricerca", "dato": "Kospi, chiusura", "ricerche": ["Kospi closes October 16 2026", ...],
 "esito": "trovato" | "mancante", "fonte": {"testata": "Seoul Economic Daily", "url": "https://..."}}
Uso: python3 ricerche.py [cartella del repository]"""
import datetime as dt, glob, json, os, sys

repo = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
limite = dt.date.today() - dt.timedelta(days=60)
trovati, mancanti = {}, {}
for p in sorted(glob.glob(os.path.join(repo, "redazione", "fatti", "20*.json"))):
    try:
        giorno = dt.date.fromisoformat(os.path.basename(p)[:10])
        schede = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    if giorno < limite:
        continue
    for s in schede:
        if not isinstance(s, dict) or s.get("sezione") != "ricerca" or not s.get("dato"):
            continue
        k = s["dato"].strip().lower()
        if s.get("esito") == "trovato" and s.get("fonte"):
            f = s["fonte"]; r = (s.get("ricerche") or [""])[-1]
            trovati[k] = f"{s['dato']} -> {f.get('testata', '?')} ({(f.get('url') or '')[:60]}); ricerca che ha funzionato: \"{r}\""
            mancanti.pop(k, None)
        elif s.get("esito") == "mancante":
            mancanti[k] = f"{s['dato']} ({giorno:%d/%m}, provate: {len(s.get('ricerche') or [])})"
righe = list(trovati.values())[-6:]
if righe:
    print("Ricerche, dove li abbiamo trovati: " + " | ".join(righe))
if mancanti:
    print("Ricerche, mancati di recente (prova altre strade): " + "; ".join(list(mancanti.values())[-4:]))
