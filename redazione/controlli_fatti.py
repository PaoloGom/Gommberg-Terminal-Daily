"""Controllo delle schede dei fatti (fonti, date, novità, esito della revisione) prima della pubblicazione.
Uso: python3 controlli_fatti.py <fatti.json> <edizioni.json> <data AAAA-MM-GG> [--prima-della-revisione]
Esce con codice 1 e l'elenco dei problemi se qualcosa non va.

Schema di fatti.json: lista di schede
{"id": "N01", "sezione": "top_story|top_news|catalizzatori|agenda|macro|deep_dive|scommessa",
 "testo": "il fatto come appare nel PDF", "data_evento": "AAAA-MM-GG",
 "novita": "per un tema già uscito: qual è lo sviluppo nuovo (altrimenti null)",
 "fonti": [{"testata": "Reuters", "url": "https://...", "data_pubblicazione": "AAAA-MM-GG", "citazione": "frase originale"}],
 "verifica": "confermato|errato|non_conclusivo" (scritto dal revisore), "nota_revisore": "..."}"""
import datetime as dt, json, os, sys
from urllib.parse import urlparse

QUI = os.path.dirname(os.path.abspath(__file__))
fatti_p, indice_p, oggi_s = sys.argv[1], sys.argv[2], sys.argv[3]
prima_revisione = "--prima-della-revisione" in sys.argv
oggi = dt.date.fromisoformat(oggi_s)
F = json.load(open(os.path.join(QUI, "fonti.json"), encoding="utf-8"))
L1, L2, NO = set(F["livello_1"]), set(F["livello_2"]), set(F["vietate"])


def livello(url):
    h = (urlparse(url).hostname or "").lower()
    parti = h.split(".")
    for i in range(len(parti) - 1):
        d = ".".join(parti[i:])
        if d in NO:
            return 0
        if d in L1:
            return 1
        if d in L2:
            return 2
    return 3


voci = json.load(open(indice_p, encoding="utf-8"))
prec = sorted({v["data"] for v in voci if v["data"] < oggi_s})
ultima = dt.date.fromisoformat(prec[-1]) if prec else oggi - dt.timedelta(days=3)
gia_usciti = " | ".join(n for v in voci if v["data"] < oggi_s for n in v.get("notizie", [])).lower()

fatti = json.load(open(fatti_p, encoding="utf-8"))
problemi, avvisi = [], []
ids = [f.get("id") for f in fatti]
if len(ids) != len(set(ids)):
    problemi.append("id duplicati nelle schede")
fatti = [f for f in fatti if not f.get("scartata")]
for f in fatti:
    i, sez = f.get("id", "?"), f.get("sezione", "")
    fonti = f.get("fonti") or []
    if not f.get("testo") or not f.get("data_evento"):
        problemi.append(f"{i}: mancano testo o data_evento"); continue
    if not fonti:
        problemi.append(f"{i}: nessuna fonte"); continue
    livelli, testate = [], set()
    for s in fonti:
        lv = livello(s.get("url", ""))
        if lv == 0:
            problemi.append(f"{i}: fonte vietata {s.get('url')}")
        if not s.get("url", "").startswith("http") or not s.get("citazione") or not s.get("data_pubblicazione"):
            problemi.append(f"{i}: fonte senza url, citazione o data di pubblicazione ({s.get('testata')})")
        livelli.append(lv); testate.add((s.get("testata") or s.get("url")).lower())
    if not (1 in livelli or sum(1 for x in livelli if x == 2) >= 2 and len(testate) >= 2):
        problemi.append(f"{i}: fonti insufficienti (serve 1 di livello 1 o 2 testate di livello 2; livelli {livelli})")
    ev = dt.date.fromisoformat(f["data_evento"])
    pubs = [dt.date.fromisoformat(s["data_pubblicazione"]) for s in fonti if s.get("data_pubblicazione")]
    if sez == "agenda":
        if ev < oggi:
            problemi.append(f"{i}: evento in agenda già passato ({ev})")
    elif sez in ("top_story", "top_news", "catalizzatori"):
        # Notizie e catalizzatori: l'evento deve essere successivo all'edizione precedente,
        # salvo uno sviluppo nuovo dichiarato e sostenuto da una fonte pubblicata dopo.
        if ev < ultima:
            if not f.get("novita"):
                problemi.append(f"{i}: evento del {ev}, non successivo all'ultima edizione ({ultima}), senza novità dichiarata")
            elif not any(p > ultima or p == oggi for p in pubs):
                problemi.append(f"{i}: novità dichiarata ma nessuna fonte pubblicata dopo l'ultima edizione")
        if pubs and max(pubs) < ev:
            problemi.append(f"{i}: le fonti sono precedenti all'evento ({max(pubs)} < {ev})")
    if pubs and max(pubs) < oggi - dt.timedelta(days=7) and sez != "deep_dive":
        avvisi.append(f"{i}: fonte più recente del {max(pubs)}, oltre 7 giorni")
    if sez in ("top_story", "top_news") and gia_usciti and f["testo"][:40].lower() in gia_usciti:
        problemi.append(f"{i}: titolo identico a una notizia già uscita")
    v = f.get("verifica")
    if not prima_revisione:
        if sez in ("top_story", "top_news", "catalizzatori", "agenda") and v is None:
            problemi.append(f"{i}: non verificato dal revisore")
        if v == "errato":
            problemi.append(f"{i}: segnato ERRATO dal revisore: {f.get('nota_revisore', '')}")
        if v == "non_conclusivo":
            problemi.append(f"{i}: verifica non conclusiva: togliere il fatto dal PDF o attribuirlo e ripetere la verifica")

print(f"Schede: {len(fatti)} | ultima edizione: {ultima} | avvisi: {len(avvisi)}")
for a in avvisi:
    print("AVVISO: " + a)
if problemi:
    respinti = sorted({p.split(":")[0] for p in problemi if p.split(":")[0] in ids})
    print("PROBLEMI:\n- " + "\n- ".join(problemi))
    print("DA_TOGLIERE: " + ",".join(respinti)); sys.exit(1)
print("OK: schede dei fatti in regola")
