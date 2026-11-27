"""G-46 / riga G-04: in ogni edizione del primo giorno di uscita della settimana, fin dove arriva "In arrivo" dell'agenda
di pag. 5 (dal PDF). Sola lettura. Uso: python3 g04_agenda.py"""
import datetime as dt, glob, os, re, subprocess, sys
R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, R)
import giorni as G

NOMI = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
for pdf in sorted(glob.glob(os.path.join(R, "..", "pdf", "2026-*-gommberg-*.pdf"))):
    d = dt.date.fromisoformat(os.path.basename(pdf)[:10])
    try:
        primo = G.primo_della_settimana(d)
    except Exception:  # noqa: BLE001
        primo = d.weekday() == 0
    if not primo:
        continue
    t = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True).stdout.decode()
    m = re.search(r"IN ARRIVO(.*?)(?:Testi generati|IL GRAN FINALE)", t, re.S)
    if not m:
        print(f"{d} {d.strftime('%a')}: agenda 'IN ARRIVO' non trovata"); continue
    gg = [NOMI.index(x) for x in re.findall(r"(?m)^\s*(Lun|Mar|Mer|Gio|Ven|Sab|Dom)\s+\d", m.group(1))]
    righe = re.findall(r"(?m)^\s*((?:Lun|Mar|Mer|Gio|Ven|Sab|Dom)\s+\d+[^\n]{0,60})", m.group(1))
    fino = NOMI[max(gg)] if gg else "?"
    ven = "sì" if 4 in gg else "no"
    print(f"{d} ({NOMI[d.weekday()]}): fino a {fino}, venerdì in agenda: {ven}; righe: " + " | ".join(re.sub(r'\s{2,}', ' ', r).strip()[:38] for r in righe))
