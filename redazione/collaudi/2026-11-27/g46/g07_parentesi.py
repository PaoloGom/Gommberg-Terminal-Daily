"""G-46 / riga G-07: tutte le parentesi del testo dei PDF #031-#035 (righe Fonti e tabella Fonti di pag. 6 escluse), per
classificarle a mano, e il conteggio del controllo (controlli_testo.fonti_tra_parentesi con le testate di fonti.json più
quelle delle righe Fonti del PDF). Sola lettura. Uso: python3 g07_parentesi.py"""
import glob, os, re, subprocess, sys
R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, R)
import controlli_testo as T

for pdf in sorted(glob.glob(os.path.join(R, "..", "pdf", "2026-11-2[3-7]-gommberg-03[1-5].pdf"))):
    t = subprocess.run(["pdftotext", pdf, "-"], capture_output=True).stdout.decode()
    corpo = t.rsplit("\nNOTE\n", 1)[0]                       # via la tabella Fonti di pag. 6
    fonti = re.findall(r"(?m)^Fonti?:[^\n]*(?:\n[^\n]+)*", corpo)
    corpo = re.sub(r"(?m)^Fonti?:[^\n]*(?:\n[^\n]+)*", " ", corpo)
    flat = re.sub(r"\s+", " ", corpo)
    nomi = T.NOMI_BASE + [n for n in T.nomi_da_righe(fonti) if n not in T.NOMI_BASE]
    tutte = re.findall(r"\(([^()]{1,80})\)", flat)
    etich = {"ETF", "ETF, $", "volatilità attesa", "future, $/oncia"}
    tutte = [x for x in tutte if x not in etich]
    par = T.fonti_tra_parentesi(flat, nomi)
    print(f"== {os.path.basename(pdf)}: parentesi nel testo {len(tutte)}, di cui sola attribuzione per il controllo: {len(par)}")
    for x in tutte:
        print("   (" + x + ")")
