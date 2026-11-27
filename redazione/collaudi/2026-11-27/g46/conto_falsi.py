"""G-46, interventi 1, 3 e 5: i controlli toccati, lanciati sulle dieci edizioni archiviate (16-27/11), per contare prima e
dopo che cosa segnalano. Uso: python3 conto_falsi.py [<cartella redazione da provare>] (default: quella di questo file).
Stampa, per edizione, gli errori di controlli_testo (tutti), i CERCA "dato ufficiale" di controlli_fatti e i problemi
dell'Euro Stoxx 50 di controlli_dati. Sola lettura: lavora su copie in /tmp/g46/conto."""
import glob, os, shutil, subprocess, sys
QUI = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
R = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else QUI
EDI = os.path.join(QUI, "..", "edizioni.json")
tot = {"testo": 0, "ufficiali": 0, "sx5e": 0}
for g in sorted(os.listdir(os.path.join(QUI, "sorgenti"))):
    src = os.path.join(QUI, "sorgenti", g)
    pdf = glob.glob(os.path.join(QUI, "..", "pdf", g + "-gommberg-*.pdf"))
    if not pdf or not os.path.exists(os.path.join(src, "edizione.py")):
        continue
    lav = os.path.join("/tmp/g46/conto", g)
    shutil.rmtree(lav, ignore_errors=True); os.makedirs(lav)
    for f in [x for x in os.listdir(src) if os.path.isfile(os.path.join(src, x))]:
        shutil.copy(os.path.join(src, f), lav)
    shutil.copy(os.path.join(src, "edizione.py"), os.path.join(lav, f"edizione_{g}.py"))
    shutil.copy(os.path.join(QUI, "fatti", g + ".json"), os.path.join(lav, "fatti.json"))
    t = subprocess.run([sys.executable, "-B", os.path.join(R, "controlli_testo.py"), os.path.realpath(pdf[0]), "--edizione",
                        os.path.join(lav, "edizione.py")], cwd=lav, capture_output=True, text=True).stdout
    err_t = [l for l in t.splitlines() if l.startswith("ERRORE")]
    f = subprocess.run([sys.executable, "-B", os.path.join(R, "controlli_fatti.py"), os.path.join(lav, "fatti.json"), EDI, g],
                       cwd=lav, capture_output=True, text=True).stdout
    uff = [l for l in f.splitlines() if "CERCA" in l and "dato ufficiale" in l]
    dd = subprocess.run([sys.executable, "-B", os.path.join(R, "controlli_dati.py"), os.path.join(lav, "dati.json")],
                        cwd=lav, capture_output=True, text=True).stdout
    sx = [l for l in dd.splitlines() if l.startswith("- Euro Stoxx 50")]
    tot["testo"] += len(err_t); tot["ufficiali"] += len(uff); tot["sx5e"] += len(sx)
    print(f"== {g}: controlli_testo {len(err_t)} errori, dati ufficiali da cercare {len(uff)}, Euro Stoxx 50 {len(sx)}")
    for l in err_t + uff + sx:
        print("   " + l[:260])
print("Totale:", tot)
