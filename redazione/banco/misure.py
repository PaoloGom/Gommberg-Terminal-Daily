"""Banco di prova: rilancia i controlli di un kit (cartella redazione/) sulle edizioni già pubblicate e misura il testo.
Non serve alla redazione del mattino e non costa token: serve a chi cambia regole, controlli, modello o motore.
Uso: python3 misure.py <cartella redazione del kit da provare> <repo con pdf/, edizioni.json, redazione/fatti/> [--json out]
Per ogni edizione con il registro dei fatti: esito dei controlli che non chiedono i file di lavoro del mattino
(PDF e indice, fatti, scrittura, ripetizioni) e le misure di stile (fonti tra parentesi, righe →, parole)."""
import json, os, re, subprocess, sys

KIT, REPO = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
# le misure usano sempre il metro del kit corrente (cartella sopra banco/), così prima e dopo sono confrontabili
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import citazioni


def lancia(*cmd):
    r = subprocess.run(["python3", *cmd], capture_output=True, text=True, cwd=KIT)
    righe = [x for x in (r.stdout + r.stderr).splitlines() if x.startswith(("ERRORE", "- ", "CERCA"))]
    return {"ok": r.returncode == 0, "errori": righe}


def parole(pdf):
    t = subprocess.run(["pdftotext", pdf, "-"], capture_output=True).stdout.decode("utf-8", "replace")
    return len(re.findall(r"\w+", t))


indice = json.load(open(os.path.join(REPO, "edizioni.json"), encoding="utf-8"))
risultati = []
for v in sorted(indice, key=lambda x: x["numero"]):
    pdf, fatti = os.path.join(REPO, v["file"]), os.path.join(REPO, "redazione", "fatti", v["data"] + ".json")
    if not (os.path.exists(pdf) and os.path.exists(fatti)):
        continue
    esito = {"numero": v["numero"], "data": v["data"], "controlli": {
        "pdf_indice": lancia("controlli.py", pdf, os.path.join(REPO, "edizioni.json"), str(v["numero"])),
        "fatti": lancia("controlli_fatti.py", fatti, os.path.join(REPO, "edizioni.json"), v["data"]),
        "scrittura": lancia("controlli_testo.py", pdf),
        "ripetizioni": lancia("controlli_ripetizioni.py", pdf)}}
    misure = {"parole": parole(pdf)}
    misure.update({k: v for k, v in citazioni.esame(pdf)[0].items() if k != "per_pagina"})
    esito["misure"] = misure
    risultati.append(esito)

if "--json" in sys.argv:
    json.dump(risultati, open(sys.argv[sys.argv.index("--json") + 1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for r in risultati:
    c = r["controlli"]
    print(f"#{r['numero']:03d} " + " ".join(f"{k}:{'ok' if x['ok'] else 'ROSSO'}" for k, x in c.items())
          + f" | fonti tra parentesi: {r['misure'].get('parentesi', '-')} | parole: {r['misure']['parole']}")
