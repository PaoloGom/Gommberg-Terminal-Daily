"""G-46 / tema delle note "fonti deboli o poche negli approfondimenti": per ogni approfondimento delle #031-#035, le testate
della sua riga Fonti (escluse le fonti dei dati di mercato: FMP, EODHD, curva del Tesoro), con il livello di fonti.json
ricavato dalle schede del giorno (agenzia o primaria = 1; sito in livello_1 = 1, livello_2 = 2, fuori elenco = 3).
"Grandi" = le testate globali del passo dei sensori (ISTRUZIONI §4.2: Reuters, Bloomberg, FT, WSJ) più AP, AFP, dpa-AFX,
ANSA, Radiocor/Sole 24 Ore, Milano Finanza. Sola lettura. Uso: python3 fonti_approfondimenti.py"""
import glob, json, os, re, subprocess, sys
R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, R)
import autori as A

DATI = re.compile(r"\b(FMP|EODHD|chiusure|curva|livell|volumi|target|CME)\b", re.I)
GRANDI = ("reuters", "bloomberg", "financial times", "wall street journal", "wsj", "ap", "afp", "dpa-afx", "ansa", "radiocor",
          "sole 24 ore", "milano finanza")


def livello_nome(n, schede):
    k = n.lower().split(" (")[0].strip()
    best = None
    for s in schede:
        for f in s.get("fonti") or []:
            t = (f.get("testata") or "").lower()
            if t.split(" (")[0].strip() == k or (len(k) > 3 and t.startswith(k)):
                lv = 1 if (f.get("agenzia") or f.get("primaria")) else A.livello(f.get("url", ""))
                best = lv if best is None else min(best, lv)
    return best


tot = {"pezzi": 0, "testate": 0, "liv3": 0, "con_grande": 0, "max2": 0}
for pdf in sorted(glob.glob(os.path.join(R, "..", "pdf", "2026-11-2[3-7]-gommberg-03[1-5].pdf"))):
    g = os.path.basename(pdf)[:10]
    schede = [s for s in json.load(open(os.path.join(R, "fatti", g + ".json"), encoding="utf-8")) if isinstance(s, dict)]
    t = subprocess.run(["pdftotext", pdf, "-"], capture_output=True).stdout.decode()
    print(f"== {os.path.basename(pdf)}")
    for m in re.finditer(r"APPROFONDIMENTO \| ([^\n]+)\n(.*?)\nFonti: ([^\n]+(?:\n[^\n]+)?)", t, re.S):
        tema, riga = m.group(1).strip(), re.sub(r"\s+", " ", m.group(3)).split("Testi generati")[0].strip(" .")
        nomi = [x.strip(" .") for x in re.split(r"[,;]", riga) if x.strip(" .") and not DATI.search(x)]
        lv = [(n, livello_nome(n, schede)) for n in nomi]
        grande = [n for n in nomi if any(re.search(r"(?<![\w-])" + re.escape(x) + r"(?![\w-])", n.lower()) for x in GRANDI)]
        deboli = [n for n, l in lv if l == 3]
        tot["pezzi"] += 1; tot["testate"] += len(nomi); tot["liv3"] += len(deboli)
        tot["con_grande"] += bool(grande); tot["max2"] += len(nomi) <= 2
        print(f"   {tema:<16} testate {len(nomi)} | grandi {len(grande)} ({', '.join(grande)}) | fuori elenco: {', '.join(deboli) or '-'}"
              f" | {'; '.join(f'{n}={l}' for n, l in lv)}")
print("Totale:", tot)
