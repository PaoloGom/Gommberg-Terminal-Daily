#!/usr/bin/env python3
"""G-12, studio dei minuti: il filtro "paths" di sito.yml funziona sui giri veri?
Per ogni commit del ramo principale (primo genitore) che la copia locale conosce: i file cambiati, se il filtro di
sito.yml li comprende, se tra loro ci sono file pubblici (la definizione è quella di costruisci.py --pubblici), e se
GitHub ha fatto partire sito.yml per quel commit (runs.json di misura_scarica.py). Sola lettura.

Uso:  python3 misura_filtro_sito.py <repository> <cartella con runs.json>"""
import fnmatch
import json
import os
import subprocess
import sys

REPO, D = sys.argv[1], sys.argv[2]
runs = json.load(open(os.path.join(D, "runs.json")))
partiti = {r["head_sha"]: r for r in runs if os.path.basename(r["path"]) == "sito.yml" and r["event"] == "push" and r["head_branch"] == "main"}


def git(*a, inp=None):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True, input=inp).stdout


def filtro(f):
    """Il filtro di sito.yml: tutto, tranne redazione/**, ma dentro redazione/sito/**, redazione/*.json, redazione/*/*.json."""
    if not f.startswith("redazione/"):
        return True
    return f.startswith("redazione/sito/") or fnmatch.fnmatch(f, "redazione/*.json") and f.count("/") <= 2


righe = []
for riga in git("log", "origin/main", "--first-parent", "--format=%H %cI %s").splitlines():
    sha, quando, titolo = riga.split(" ", 2)
    if not git("rev-parse", "--verify", "-q", sha + "^").strip():
        continue                                   # il primo commit della copia (storia tagliata): niente confronto
    file = [f for f in git("diff", "--no-renames", "--name-only", sha + "^", sha).splitlines() if f]
    pubblici = [f for f in subprocess.run([sys.executable, os.path.join(REPO, "redazione/sito/costruisci.py"), "--pubblici"],
                                          capture_output=True, text=True, input="\n".join(file)).stdout.splitlines() if f]
    righe.append({"sha": sha[:7], "quando": quando[:16], "titolo": titolo[:60], "file": len(file), "filtro": any(filtro(f) for f in file),
                  "pubblici": len(pubblici), "partito": sha in partiti,
                  "solo_per": sorted({f.split("/")[0] if not f.startswith("redazione/") else "/".join(f.split("/")[:2]) for f in file if filtro(f)} - {f.split("/")[0] for f in pubblici})[:4]})

n = len(righe)
part = [x for x in righe if x["partito"]]
print(f"Commit del ramo principale guardati: {n} (dal {righe[-1]['quando']} al {righe[0]['quando']})")
print(f"  sito.yml partito: {len(part)}; di questi con file pubblici cambiati: {sum(1 for x in part if x['pubblici'])}, a vuoto (nessun file pubblico): {sum(1 for x in part if not x['pubblici'])}")
non = [x for x in righe if not x["partito"]]
print(f"  sito.yml non partito: {len(non)}; di questi con file pubblici cambiati: {sum(1 for x in non if x['pubblici'])} (arrivano in linea con il push che li contiene), fermati dal filtro: {sum(1 for x in non if not x['filtro'])}")
print("\nA vuoto (partito senza file pubblici):")
for x in part:
    if not x["pubblici"]:
        print(f"  {x['quando']} {x['sha']} {x['titolo']} - il filtro lo comprende per: {', '.join(x['solo_per'])}")
print("\nNon partito con file pubblici (commit dentro un push più grande, o push fatto con il token del giro):")
for x in non:
    if x["pubblici"]:
        print(f"  {x['quando']} {x['sha']} {x['titolo']} ({x['pubblici']} file pubblici)")
print("\nFermati dal filtro (solo redazione):", sum(1 for x in righe if not x["filtro"]), "commit, es.:", "; ".join(x["titolo"][:40] for x in righe if not x["filtro"])[:400])
