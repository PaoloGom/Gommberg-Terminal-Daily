#!/usr/bin/env python3
"""G-12, studio dei minuti: scarica da GitHub (sola lettura, gh api con GET) i giri degli ultimi GIORNI giorni e i loro
job, e li salva in una cartella. Non lancia nulla e non cambia nulla.

Uso:  python3 misura_scarica.py <cartella di uscita> [giorni=45] [proprietario/repository]
Serve gh autenticato. Scrive runs.json (un elenco di giri) e jobs.json (id del giro -> elenco dei job, tutti i tentativi)."""
import datetime as dt
import json
import os
import subprocess
import sys

USCITA = sys.argv[1]
GIORNI = int(sys.argv[2]) if len(sys.argv) > 2 else 45
REPO = sys.argv[3] if len(sys.argv) > 3 else "PaoloGom/Gommberg-Terminal-Daily"


def gh(percorso):
    out = subprocess.run(["gh", "api", "-X", "GET", f"repos/{REPO}{percorso}"], capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        raise RuntimeError(out.stderr[:300])
    return json.loads(out.stdout)


def main():
    os.makedirs(USCITA, exist_ok=True)
    da = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=GIORNI)).strftime("%Y-%m-%d")
    runs, pagina = [], 1
    while True:
        j = gh(f"/actions/runs?created=%3E%3D{da}&per_page=100&page={pagina}")
        runs += j.get("workflow_runs", [])
        if len(j.get("workflow_runs", [])) < 100:
            break
        pagina += 1
    campi = ("id", "name", "path", "event", "head_branch", "head_sha", "status", "conclusion", "created_at", "updated_at",
             "run_started_at", "run_attempt", "display_title")
    leggeri = [{k: r.get(k) for k in campi} for r in runs]
    json.dump(leggeri, open(os.path.join(USCITA, "runs.json"), "w"), ensure_ascii=False, indent=0)
    jobs = {}
    fj = os.path.join(USCITA, "jobs.json")
    if os.path.exists(fj):
        jobs = json.load(open(fj))
    for i, r in enumerate(leggeri):
        k = str(r["id"])
        if k in jobs:
            continue
        el, p = [], 1
        while True:
            j = gh(f"/actions/runs/{r['id']}/jobs?filter=all&per_page=100&page={p}")
            el += j.get("jobs", [])
            if len(j.get("jobs", [])) < 100:
                break
            p += 1
        jobs[k] = [{c: x.get(c) for c in ("id", "name", "status", "conclusion", "started_at", "completed_at", "labels", "run_attempt", "runner_name", "runner_group_name")}
                   | {"passi": [{"nome": s.get("name"), "da": s.get("started_at"), "a": s.get("completed_at"), "esito": s.get("conclusion")} for s in (x.get("steps") or [])]}
                   for x in el]
        if i % 50 == 0:
            json.dump(jobs, open(fj, "w"))
            print(f"{i}/{len(leggeri)}", flush=True)
    json.dump(jobs, open(fj, "w"))
    print(f"Giri: {len(leggeri)} dal {da}; job: {sum(len(v) for v in jobs.values())}")


if __name__ == "__main__":
    main()
