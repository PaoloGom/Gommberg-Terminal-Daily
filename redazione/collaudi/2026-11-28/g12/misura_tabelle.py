#!/usr/bin/env python3
"""G-12, studio dei minuti: dalle risposte salvate da misura_scarica.py costruisce le tabelle dei minuti fatturabili
"da privato" (ogni job arrotondato per eccesso al minuto, almeno 1; ubuntu-slim a un terzo; job saltati a zero).

Due conti per ogni giro:
  - "com'era": con la macchina su cui il job è girato davvero quel giorno;
  - "oggi":    con le tre leve in linea dal 27-28/11: i flussi leggeri (dem, mattino, newsletter, segnalazioni) su
               ubuntu-slim; collaudo.yml solo dal ramo cancello (dei giri storici restano quelli nati da un merge
               "Rilascio ...", uno per rilascio, più quelli lanciati a mano).
Classi: a = dipende dalle edizioni; b = dipende dal lavoro di sviluppo; c = gira a orario comunque;
        d = sparisce (pages-build-deployment: GitHub Pages).

Uso:  python3 misura_tabelle.py <cartella con runs.json e jobs.json> [--json]"""
import collections
import datetime as dt
import json
import math
import os
import statistics
import sys

D = sys.argv[1]
runs = json.load(open(os.path.join(D, "runs.json")))
jobs = json.load(open(os.path.join(D, "jobs.json")))
LEGGERI = {"dem.yml", "mattino.yml", "newsletter.yml", "segnalazioni.yml"}


def ist(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def secondi(j):
    if j.get("conclusion") in (None, "skipped") or not j.get("started_at") or not j.get("completed_at"):
        return None
    return max(0.0, (ist(j["completed_at"]) - ist(j["started_at"])).total_seconds())


def minuti(j):
    s = secondi(j)
    return None if s is None else max(1, math.ceil(s / 60))


def flusso(r):
    return os.path.basename(r["path"])


def lunedi(r):
    g = ist(r["created_at"]).date()
    return (g - dt.timedelta(days=g.weekday())).isoformat()


gomm_ok = []          # istanti dei giri di mattino.yml con il job gomm riuscito: il sito.yml a mano subito dopo è suo
for r in runs:
    if flusso(r) == "mattino.yml" and any(j["name"] == "gomm" and j["conclusion"] == "success" for j in jobs[str(r["id"])]):
        gomm_ok.append(ist(r["created_at"]))


def classe(r):
    """(classe, voce) di un giro."""
    f, ev, ramo, t = flusso(r), r["event"], r.get("head_branch") or "", r.get("display_title") or ""
    if f == "pages-build-deployment":
        return "d", "GitHub Pages (pages-build-deployment)"
    if f == "collaudo.yml":
        return "b", f"collaudo.yml {ev} su {'anteprima-*' if ramo.startswith('anteprima-') else ('altri rami' if ramo not in ('rilascio', 'cancello', 'con-prova', 'main') else ramo)}"
    if f == "sito.yml":
        if ev == "push" and ramo == "main":
            if t.startswith("Edizione #") and " - 20" in t:
                return "a", "sito.yml push main: edizione"
            if t.startswith("Rilascio "):
                return "b", "sito.yml push main: rilascio"
            return "b", "sito.yml push main: altro (correzioni, mail, prove)"
        if ev == "push":
            return "b", "sito.yml push su prova e anteprima-*"
        if any(0 <= (ist(r["created_at"]) - g).total_seconds() <= 240 for g in gomm_ok):
            return "c", "sito.yml lanciato dal GOMM (ripubblica dati/gomm.json)"
        return "b", "sito.yml a mano"
    if f == "newsletter.yml":
        if ev == "push" and t.startswith("Edizione #") and " - 20" in t:
            return "a", "newsletter.yml push main: edizione"
        return "b", f"newsletter.yml {'a mano (prove)' if ev != 'push' else 'push main: altro'}"
    if f == "mattino.yml":
        if ev == "workflow_run":
            return "a", "mattino.yml dopo sito.yml (workflow_run)"
        if ev == "schedule":
            return "c", "mattino.yml a orario (schedule)"
        return "b", f"mattino.yml {ev}"
    if f == "segnalazioni.yml":
        return ("c", "segnalazioni.yml a orario (schedule)") if ev == "schedule" else ("b", "segnalazioni.yml a mano")
    if f == "dem.yml":
        if ev == "schedule":
            return "c", "dem.yml a orario (schedule)"
        if ev == "push" and ramo == "main":
            return "b", "dem.yml push main"
        if ev == "push":
            return "b", "dem.yml push su rami di lavoro (g<NN>, rilascio, con-prova, prova)"
        return "b", "dem.yml a mano"
    return "b", f"{f} {ev}"


def conta(r):
    """(minuti com'era, minuti oggi, job partiti) di un giro, in minuti Linux standard."""
    f = flusso(r)
    era = oggi = 0.0
    n = 0
    for j in jobs[str(r["id"])]:
        m = minuti(j)
        if m is None:
            continue
        n += 1
        slim = "ubuntu-slim" in (j.get("labels") or [])
        era += m / 3 if slim else m
        oggi += m / 3 if (slim or f in LEGGERI) else m
    if f == "pages-build-deployment":
        oggi = 0.0
    if f == "collaudo.yml":
        t, ramo = r.get("display_title") or "", r.get("head_branch") or ""
        if not (ramo == "cancello" or r["event"] == "workflow_dispatch" or (ramo == "rilascio" and t.startswith("Rilascio "))):
            oggi = 0.0
    return era, oggi, n


def tabella(righe, titolo, colonne):
    print(f"\n### {titolo}")
    print("| " + " | ".join(colonne) + " |")
    print("|" + "|".join("---" if i == 0 else "---:" for i in range(len(colonne))) + "|")
    for x in righe:
        print("| " + " | ".join(str(c) for c in x) + " |")


def f1(x):
    return f"{x:.0f}" if abs(x - round(x)) < 0.05 else f"{x:.1f}"


sett = sorted({lunedi(r) for r in runs})
ACC = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0.0, 0.0]))   # (classe, voce) -> settimana -> [giri, era, oggi]
for r in runs:
    if r.get("status") != "completed":
        continue
    c = classe(r)
    era, oggi, n = conta(r)
    a = ACC[c][lunedi(r)]
    a[0] += 1
    a[1] += era
    a[2] += oggi

print(f"Giri: {len(runs)} dal {min(r['created_at'] for r in runs)[:10]} al {max(r['created_at'] for r in runs)[:16]}Z; "
      f"job partiti: {sum(1 for v in jobs.values() for j in v if minuti(j) is not None)}")
primo = {}
for r in runs:
    primo[flusso(r)] = min(primo.get(flusso(r), "9"), r["created_at"][:10])
print("Primo giro di ogni flusso:", ", ".join(f"{k} {v}" for k, v in sorted(primo.items(), key=lambda x: x[1])))

ULT = sett[-3:]
for quale, idx in (("com'era (macchine di quel giorno)", 1), ("oggi (con le tre leve)", 2)):
    righe = []
    tot = collections.defaultdict(float)
    for (cl, voce), per in sorted(ACC.items()):
        riga = [cl, voce] + [f"{per[s][0]} / {f1(per[s][idx])}" if s in per else "" for s in ULT] + [sum(per[s][0] for s in per), f1(sum(per[s][idx] for s in per))]
        righe.append(riga)
        for s in per:
            tot[(cl, s)] += per[s][idx]
            tot[(cl, "tot")] += per[s][idx]
            tot[("tutti", s)] += per[s][idx]
            tot[("tutti", "tot")] += per[s][idx]
    for cl in ("a", "b", "c", "d", "tutti"):
        righe.append([f"**{cl}**", "**totale**"] + [f"**{f1(tot[(cl, s)])}**" for s in ULT] + ["", f"**{f1(tot[(cl, 'tot')])}**"])
    tabella(righe, f"Minuti fatturabili da privato, {quale}: giri / minuti per settimana (lunedì)", ["classe", "flusso ed evento"] + ULT + ["giri 45 gg", "minuti 45 gg"])

# per mese (novembre), per confronto con pannello/minuti.json
nov = collections.defaultdict(float)
for r in runs:
    if r["created_at"].startswith("2026-11") and r.get("status") == "completed":
        nov[flusso(r)] += conta(r)[0]
print("\nNovembre fino a oggi, com'era, per flusso:", ", ".join(f"{k} {f1(v)}" for k, v in sorted(nov.items(), key=lambda x: -x[1])), "| totale", f1(sum(nov.values())))

# quanto dura ogni job (secondi veri), e quanto è cresciuto
print("\n### Durata dei job (secondi veri, solo riusciti)")
print("| flusso / job | n | mediana | p90 | max | minuti fatturati (mediana) | prima metà -> seconda metà (mediane) |")
print("|---|---:|---:|---:|---:|---:|---|")
DUR = collections.defaultdict(list)
for r in runs:
    for j in jobs[str(r["id"])]:
        if j.get("conclusion") == "success" and secondi(j) is not None and flusso(r) != "pages-build-deployment":
            DUR[(flusso(r), j["name"])].append((r["created_at"], secondi(j)))
for k, v in sorted(DUR.items()):
    v.sort()
    s = [x[1] for x in v]
    q = sorted(s)
    m1, m2 = (statistics.median(s[:len(s) // 2]), statistics.median(s[len(s) // 2:])) if len(s) >= 6 else (None, None)
    print(f"| {k[0]} / {k[1]} | {len(s)} | {statistics.median(s):.0f} | {q[min(len(q) - 1, int(0.9 * len(q)))]:.0f} | {max(s):.0f} | {math.ceil(statistics.median(s) / 60)} | "
          + (f"{m1:.0f} -> {m2:.0f}" if m1 is not None else "-") + " |")

# i passi dei due flussi pesanti, giorno per giorno (mediana dei secondi)
print("\n### Passi di collaudo.yml e sito.yml: mediana dei secondi per giorno (solo job riusciti)")
PASSI = collections.defaultdict(lambda: collections.defaultdict(list))
for r in runs:
    if flusso(r) not in ("collaudo.yml", "sito.yml"):
        continue
    for j in jobs[str(r["id"])]:
        if j.get("conclusion") != "success":
            continue
        for p in j.get("passi") or []:
            if p.get("da") and p.get("a") and p.get("esito") == "success":
                PASSI[(flusso(r), j["name"][:22], p["nome"][:44])][r["created_at"][:10]].append((ist(p["a"]) - ist(p["da"])).total_seconds())
giorni = sorted({g for v in PASSI.values() for g in v})
print("| flusso / job / passo | " + " | ".join(g[5:] for g in giorni) + " |")
print("|---|" + "---:|" * len(giorni))
for k, v in sorted(PASSI.items()):
    if max(statistics.median(x) for x in v.values()) < 4:
        continue
    print(f"| {' / '.join(k)} | " + " | ".join(f"{statistics.median(v[g]):.0f}" if g in v else "" for g in giorni) + " |")

# rilasci e push per giorno: il caso peggiore vero
print("\n### Giorno per giorno: rilasci (merge 'Rilascio' su main), giri di collaudo.yml, push su rami di lavoro che hanno acceso un flusso")
per = collections.defaultdict(lambda: collections.Counter())
visti = set()
for r in sorted(runs, key=lambda r: r["created_at"]):
    g, f, t, ramo = r["created_at"][:10], flusso(r), r.get("display_title") or "", r.get("head_branch") or ""
    if t.startswith("Rilascio ") and r["event"] == "push" and ramo in ("main", "rilascio") and r["head_sha"] not in visti:
        visti.add(r["head_sha"])                   # un rilascio = un merge "Rilascio ..." (lo stesso commit su main e su rilascio)
        per[g]["rilasci"] += 1
    if f == "sito.yml" and r["event"] == "push" and ramo == "main" and t.startswith("Edizione #"):
        per[g]["edizioni"] += 1
    if f == "collaudo.yml":
        per[g]["collaudi"] += 1
        per[g]["min_collaudo"] += conta(r)[0]
    if f == "dem.yml" and r["event"] == "push" and ramo != "main":
        per[g]["dem_rami"] += 1
    if f != "pages-build-deployment":
        per[g]["min_era"] += conta(r)[0]
        per[g]["min_oggi"] += conta(r)[1]
print("| giorno | edizioni | rilasci | giri collaudo | minuti collaudo | dem.yml da rami | minuti com'era | minuti oggi |")
print("|---|---:|---:|---:|---:|---:|---:|---:|")
for g in sorted(per):
    p = per[g]
    print(f"| {g} | {p['edizioni']} | {p['rilasci']} | {p['collaudi']} | {f1(p['min_collaudo'])} | {p['dem_rami']} | {f1(p['min_era'])} | {f1(p['min_oggi'])} |")

# le sveglie di GitHub: quante ne sono partite rispetto a quelle scritte nel cron
print("\n### Sveglie 'schedule' di GitHub: partite davvero")
for f in ("segnalazioni.yml", "mattino.yml", "dem.yml"):
    v = sorted(r["created_at"] for r in runs if flusso(r) == f and r["event"] == "schedule")
    if v:
        giorni_n = (ist(v[-1]) - ist(v[0])).days + 1
        print(f"- {f}: {len(v)} partenze in {giorni_n} giorni (dal {v[0][:10]}), ore UTC: {' '.join(x[11:16] for x in v[-8:])}")
