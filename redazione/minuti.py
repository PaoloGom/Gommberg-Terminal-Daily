#!/usr/bin/env python3
"""I minuti di GitHub Actions del mese (G-12, leva 3): una stima dai giri, perché il consumo vero non si legge.

Il consumo vero (GET /users/{utente}/settings/billing/usage) vuole un token con il permesso utente "Plan", che i flussi
non hanno: il token del giro (GITHUB_TOKEN) non è tra quelli ammessi. Per non chiedere permessi nuovi si stima:
  - ogni job finito del mese, dal suo inizio alla sua fine, arrotondato per eccesso al minuto (almeno 1 minuto);
  - i job su ubuntu-slim (1 CPU, 0,002 dollari al minuto) contano un terzo di un minuto Linux standard (0,006);
  - la quota del privato gratuito: 12 dollari al mese = 2.000 minuti Linux standard (QUOTA).
È una stima prudente (arrotonda per eccesso); i job saltati non contano, come per GitHub. Finché il repository è
pubblico i minuti non si pagano: la stima serve a sapere che cosa succederà da privato.
Si contano solo i giri dei flussi del repository (quelli il cui file sta in .github/workflows/). Gli altri li lancia
GitHub per conto suo e non consumano la quota: GitHub Pages ("pages-build-deployment") e Dependabot sono gratuiti
(docs.github.com, Billing, GitHub Actions). Non spariscono in silenzio: quanti sono, nome per nome, sta in
"non_contati" e in una riga dell'uscita. Se lì compare un nome nuovo, va guardato se è gratuito anche quello.

Scrive pannello/minuti.json (lo legge il pannello, che mostra l'allarme al 75%, e lo legge mattino.py). I giri già
contati restano nel file ("giri": id -> minuti), così ogni giorno si chiedono a GitHub solo i giri nuovi.
Lo lancia il job gomm di mattino.yml (una volta al giorno, con l'orologio). Non fallisce mai: se GitHub non risponde
lascia il file com'era e lo dice.

Uso:  python3 redazione/minuti.py [--scrivi]
Variabili: GITHUB_REPOSITORY e GH_TOKEN (senza, non fa nulla). Solo per le prove: GTD_GITHUB (una cartella di risposte
finte: runs.json, jobs_<id>.json, repo.json), GTD_ADESSO (AAAA-MM-GGTHH:MM, UTC) e GTD_MINUTI (il file al posto di
pannello/minuti.json)."""
import datetime as dt
import json
import math
import os
import sys
import urllib.request

QUI = os.path.dirname(os.path.abspath(__file__))
FILE = os.environ.get("GTD_MINUTI") or os.path.join(os.path.dirname(QUI), "pannello", "minuti.json")
QUOTA = 2000                     # minuti Linux standard al mese del privato gratuito (12 dollari a 0,006)
ALLARME = 75                     # percentuale della quota oltre cui il controllo del mattino e il pannello avvisano
PESO = {"ubuntu-slim": 1 / 3}    # rispetto a un minuto Linux standard (prezzi di GitHub: 0,002 contro 0,006 dollari)
NOSTRI = ".github/workflows/"     # dove stanno i flussi del repository: solo i loro giri consumano la quota


def api(percorso):
    finto = os.environ.get("GTD_GITHUB")
    if finto:
        nome = "repo.json" if percorso == "" else ("runs.json" if "/runs?" in percorso else "jobs_" + percorso.split("/runs/")[1].split("/")[0] + ".json")
        return json.load(open(os.path.join(finto, nome), encoding="utf-8"))
    repo, token = os.environ["GITHUB_REPOSITORY"], os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    r = urllib.request.Request(f"https://api.github.com/repos/{repo}{percorso}",
                               headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "User-Agent": "controllo-gommberg"})
    with urllib.request.urlopen(r, timeout=30) as f:
        return json.loads(f.read())


def istante(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def minuti_job(job):
    """Minuti Linux standard di un job finito (None se non è finito o non è partito)."""
    if job.get("conclusion") in (None, "skipped") or not job.get("started_at") or not job.get("completed_at"):
        return None
    secondi = max(0.0, (istante(job["completed_at"]) - istante(job["started_at"])).total_seconds())
    peso = min([PESO.get(x, 1) for x in job.get("labels") or []] or [1])
    return max(1, math.ceil(secondi / 60)) * peso


def stima(precedente, adesso):
    mese = adesso.strftime("%Y-%m")
    # si riparte da zero a ogni mese, e anche da un file scritto quando si contavano tutti i giri (senza "non_contati")
    continua = precedente.get("mese") == mese and "non_contati" in precedente
    giri = dict(precedente.get("giri", {})) if continua else {}
    flussi = dict(precedente.get("flussi", {})) if continua else {}
    non_contati, visti = {}, set()   # nome -> giri del mese, riletto ogni giorno dall'elenco
    pagina = 1
    while True:
        j = api(f"/actions/runs?created=%3E%3D{mese}-01&per_page=100&page={pagina}")
        runs = j.get("workflow_runs", [])
        for run in runs:
            k = str(run["id"])
            percorso = (run.get("path") or "").split("@")[0]
            if not percorso.startswith(NOSTRI):
                nome = os.path.basename(percorso) or run.get("name") or "senza nome"
                non_contati[nome] = non_contati.get(nome, 0) + (k not in visti)
                visti.add(k)
                continue
            if k in giri or run.get("status") != "completed":
                continue
            jobs = api(f"/actions/runs/{run['id']}/jobs?per_page=100").get("jobs", [])
            m = sum(x for x in (minuti_job(job) for job in jobs) if x is not None)
            giri[k] = round(m, 2)
            nome = os.path.basename(percorso)
            flussi[nome] = round(flussi.get(nome, 0) + m, 2)
        if len(runs) < 100 or pagina >= 20:
            break
        pagina += 1
    totale = round(sum(giri.values()), 1)
    privato = bool(api("").get("private"))
    return {"mese": mese, "aggiornato": adesso.strftime("%Y-%m-%dT%H:%MZ"), "quota": QUOTA, "allarme": ALLARME,
            "minuti": totale, "percentuale": round(100 * totale / QUOTA, 1), "privato": privato,
            "metodo": "stima dai giri dei flussi di .github/workflows/: ogni job arrotondato per eccesso al minuto, ubuntu-slim a un terzo; il consumo vero vuole il permesso Plan, che i flussi non hanno",
            "flussi": dict(sorted(flussi.items(), key=lambda x: -x[1])), "non_contati": dict(sorted(non_contati.items())), "giri": giri}


def leggi():
    try:
        return json.load(open(FILE, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def giudizio(m, oggi):
    """(stato, frase) per mattino.py: stato True = va bene, False = allarme, None = solo una nota."""
    if not m or "percentuale" not in m:
        return None, "stima dei minuti di GitHub non ancora calcolata (pannello/minuti.json manca)"
    frase = f"{m['minuti']:g} minuti su {m['quota']} ({m['percentuale']:g}%) a {m['mese']}, stima dai giri del {m['aggiornato'][8:10]}/{m['aggiornato'][5:7]}"
    if m["mese"] != oggi.strftime("%Y-%m") or (oggi - dt.date.fromisoformat(m["aggiornato"][:10])).days > 4:
        return None, "stima dei minuti di GitHub vecchia: " + frase
    if not m.get("privato"):
        return True, frase + "; repository pubblico, per ora non si pagano"
    return m["percentuale"] < m.get("allarme", ALLARME), frase + (f": oltre il {m.get('allarme', ALLARME)}% della quota, finita la quota i flussi si fermano (sito.yml compreso)" if m["percentuale"] >= m.get("allarme", ALLARME) else "")


def main():
    if not os.environ.get("GTD_GITHUB") and not (os.environ.get("GITHUB_REPOSITORY") and (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))):
        print("Minuti di GitHub: mancano GITHUB_REPOSITORY o GH_TOKEN, niente stima.")
        return 0
    adesso = dt.datetime.strptime(os.environ["GTD_ADESSO"], "%Y-%m-%dT%H:%M") if os.environ.get("GTD_ADESSO") else dt.datetime.now(dt.timezone.utc)
    try:
        m = stima(leggi(), adesso)
    except Exception as e:  # noqa: BLE001
        print(f"::warning::Minuti di GitHub non stimati ({type(e).__name__}): resta la stima di ieri.")
        return 0
    print(f"Minuti di GitHub a {m['mese']} (stima dai giri): {m['minuti']:g} su {m['quota']}, {m['percentuale']:g}%"
          + ("" if m["privato"] else " - repository pubblico, per ora non si pagano"))
    for k, v in m["flussi"].items():
        print(f"  {k}: {v:g}")
    if m["non_contati"]:
        print("  non contati, perché non sono flussi di " + NOSTRI + " (GitHub Pages e Dependabot sono gratuiti): "
              + ", ".join(f"{k} ({v} gir{'o' if v == 1 else 'i'})" for k, v in m["non_contati"].items()))
    if "--scrivi" in sys.argv:
        os.makedirs(os.path.dirname(FILE), exist_ok=True)
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump(m, f, ensure_ascii=False, indent=1)
            f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
