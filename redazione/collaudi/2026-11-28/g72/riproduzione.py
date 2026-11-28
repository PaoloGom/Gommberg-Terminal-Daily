"""G-72: riproduzione dei due grafici sbagliati della prova #036 (pag. 2). Uso, dalla radice del repository:
  python3 redazione/collaudi/2026-11-28/g72/riproduzione.py [cartella di uscita]
Forma dei dati che ridà la figura: la storia di un anno (redazione/scommessa/dati/spx.csv e vix.csv come sono dopo
l'aggiornamento del lunedì: 260 righe, dal 14/11/2025 al 27/11/2026) ridotta a "MM-GG", filtrata con un confronto tra
testi ("MM-GG" >= inizio del periodo: "10-06" per l'S&P 500, "11-02" per il VIX) e data al motore con la riga del modello
di allora, d = date(2026, mese, giorno). Passano anche le righe dal 14/11 al 31/12 del 2025, disegnate sui giorni del 2026.
Le righe sono in riproduzione_dati.json (scritte il 28/11/2026: l'archivio scorre, tra un anno non le ridarebbe).
Poi confronta le linee disegnate con quelle del PDF (pagina2_linee.json): stessi punti a meno dell'altezza del grafico.
Dopo G-72 il motore rifiuta questa serie (date non crescenti): qui la difesa si spegne apposta, per rivedere il disegno."""
import datetime as dt, json, os, re, sys
QUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(QUI, "..", "..", "..", ".."))
USCITA = sys.argv[1] if len(sys.argv) > 1 else QUI
sys.path.insert(0, os.path.join(REPO, "redazione"))
import gommberg_engine as E  # noqa: E402
import numpy as np  # noqa: E402
E._in_ordine = lambda *a: None          # il motore di allora disegnava ciò che riceveva
R = json.load(open(os.path.join(QUI, "riproduzione_dati.json"), encoding="utf-8"))
SPX, VIX = [tuple(r) for r in R["SPX"]], [tuple(r) for r in R["VIX"]]
d = lambda s: dt.date(2026, int(s[:2]), int(s[3:]))   # "MM-GG" -> data (la riga del modello di allora)
E.linee(os.path.join(USCITA, "riproduzione_spx.png"), [d(x) for x, _ in SPX], [("S&P 500", [v for _, v in SPX], "#111111")],
        largo=515.9 / 72, alto=2.4, note=[(d("11-20"), 6910.39, "20/11"), (d("11-27"), 7297.49, "27/11")])
E.linee(os.path.join(USCITA, "riproduzione_vix.png"), [d(x) for x, _ in VIX], [("VIX", [v for _, v in VIX], "#F26B1D")],
        largo=294.07 / 72, alto=2.9, note=[(d("11-20"), 35.89, "20/11"), (d("11-27"), 23.81, "27/11")])


def punti(tratto):
    return np.array([tuple(map(float, p)) for p in re.findall(r"[ML]\s*(-?[\d.]+)[ ,](-?[\d.]+)", tratto)])


def disegnata(svg):
    for m in re.finditer(r'<path([^>]*?)/>', open(svg, encoding="utf-8").read(), re.S):
        dd = re.search(r'\sd="([^"]*)"', m.group(1), re.S)
        if dd and dd.group(1).count("L") >= 15 and "Z" not in dd.group(1) and "C" not in dd.group(1) and "clip-path" in m.group(1):
            return punti(dd.group(1))


PDF = json.load(open(os.path.join(QUI, "pagina2_linee.json"), encoding="utf-8"))
for nome, f in (("S&P 500", "riproduzione_spx.svg"), ("VIX", "riproduzione_vix.svg")):
    a, b = punti(PDF[nome]), disegnata(os.path.join(USCITA, f))
    riga = f"{nome}: {len(a)} punti nel PDF, {len(b)} nella riproduzione"
    if len(a) == len(b):   # stessa figura a meno di scala e traslazione (l'altezza del grafico la decide l'impaginazione)
        sx, sy = np.polyfit(b[:, 0], a[:, 0], 1), np.polyfit(b[:, 1], a[:, 1], 1)
        riga += (f"; scarto massimo dopo scala e traslazione: x {np.abs(np.polyval(sx, b[:, 0]) - a[:, 0]).max():.3f} pt, "
                 f"y {np.abs(np.polyval(sy, b[:, 1]) - a[:, 1]).max():.3f} pt (scala x {sx[0]:.4f}, y {sy[0]:.4f})")
    print(riga)
