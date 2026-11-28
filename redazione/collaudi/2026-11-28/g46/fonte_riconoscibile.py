"""G-46, punto 7: per ogni approfondimento delle edizioni archiviate (sorgenti/), la riga Fonti e se ha almeno una fonte
riconoscibile (autori.approfondimenti_senza_riconoscibile). Sola lettura, lavora su copie in /tmp/g46/conto.
Uso: python3 fonte_riconoscibile.py"""
import json, os, shutil, sys
R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, R)
import autori as A, controlli_testo as T

tot = n = 0
for g in sorted(os.listdir(os.path.join(R, "sorgenti"))):
    src = os.path.join(R, "sorgenti", g)
    if not os.path.exists(os.path.join(src, "edizione.py")):
        continue
    lav = os.path.join("/tmp/g46/conto", g); os.makedirs(lav, exist_ok=True)
    for f in os.listdir(src):
        if os.path.isfile(os.path.join(src, f)):
            shutil.copy(os.path.join(src, f), lav)
    qui = os.getcwd(); os.chdir(lav)
    try:
        C = T.edizione(os.path.join(lav, "edizione.py"))
    finally:
        os.chdir(qui)
    fatti = json.load(open(os.path.join(R, "fatti", g + ".json"), encoding="utf-8"))
    righe = [(m.get("chiave", "?"), " ".join(str(m.get(k) or "") for k in T.RIGHE_FONTI)) for m in C.get("moduli") or [] if isinstance(m, dict)]
    tot += len(righe)
    for p, nomi in A.approfondimenti_senza_riconoscibile(righe, fatti):
        n += 1
        print(f"{g} {p}: {', '.join(nomi)}")
print(f"Approfondimenti senza una fonte riconoscibile: {n} su {tot}")
