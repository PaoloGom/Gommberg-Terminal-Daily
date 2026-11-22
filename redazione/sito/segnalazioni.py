#!/usr/bin/env python3
"""Avviso a Paolo quando un lettore segnala un commento della Gommunity (G-13).

Lo lancia GitHub ogni ora (.github/workflows/segnalazioni.yml). Legge da gommberg.com l'elenco dei commenti segnalati
che la redazione non ha ancora tolto (/api/lettori/segnalazioni: numero, edizione, quante reti, se è già nascosto; mai
il testo) e per ogni commento nuovo apre una segnalazione di GitHub assegnata a Paolo: GitHub gli manda l'email.
Una sola segnalazione per commento, anche se poi viene chiusa. Nessun modello, nessun segreto oltre al token del giro.

Il testo del commento non entra mai nella segnalazione: il repository è pubblico, e un commento da togliere non va
copiato altrove. Paolo lo legge dal database, con il comando scritto nella segnalazione (procedura: LETTORI.md).

Se il sito non risponde non segnala nulla ed esce con 0 (ci riprova tra un'ora): che il servizio dei lettori risponda
lo guarda il controllo del mattino (mattino.py).

Uso:  python3 redazione/sito/segnalazioni.py [--prova]
  --prova  stampa le segnalazioni che aprirebbe, senza toccare GitHub
Solo per le prove: GTD_BASE (il sito al posto di https://gommberg.com/) e GTD_ELENCO (un file JSON al posto del sito)."""
import datetime as dt
import json
import os
import subprocess
import sys
import urllib.request
from zoneinfo import ZoneInfo

BASE = os.environ.get("GTD_BASE", "https://gommberg.com/").rstrip("/") + "/"
ROMA = ZoneInfo("Europe/Rome")


def elenco():
    """I commenti segnalati, o None se l'elenco non si legge."""
    try:
        if os.environ.get("GTD_ELENCO"):
            j = json.load(open(os.environ["GTD_ELENCO"], encoding="utf-8"))
        else:
            r = urllib.request.Request(BASE + "api/lettori/segnalazioni", headers={"User-Agent": "controllo-gommberg"})
            with urllib.request.urlopen(r, timeout=30) as f:
                j = json.loads(f.read())
        righe = j["segnalati"]
        return [s for s in righe if isinstance(s.get("id"), int) and isinstance(s.get("ed"), int)]
    except Exception as e:  # noqa: BLE001
        print(f"::warning::Elenco delle segnalazioni non letto ({type(e).__name__}): riprovo al prossimo giro.")
        return None


def titolo(s):
    return f"La Gommunity: commento n. {s['id']} segnalato (edizione n. {s['ed']:03d})"


def quando(iso):
    try:
        return dt.datetime.fromisoformat(str(iso).replace("Z", "+00:00")).astimezone(ROMA).strftime("%d/%m/%Y alle %H:%M")
    except ValueError:
        return "ora non disponibile"


def testo(s):
    n, reti = s["id"], s.get("reti") or 1
    stato = ("È già nascosto ai lettori: l'hanno segnalato lettori da 3 reti diverse." if s.get("nascosto")
             else f"È ancora visibile: segnalato da {reti} {'rete' if reti == 1 else 'reti'} (alla terza si nasconde da solo).")
    return f"""Un lettore ha segnalato un commento della Gommunity.

- **Commento n. {n}**, edizione n. {s['ed']:03d}: {BASE}e/{s['ed']:03d}.html
- {stato}
- Ultima segnalazione: {quando(s.get('ultima'))} (ora di Roma)

Il testo non è riportato qui di proposito: questa pagina è pubblica.

**Per leggerlo**: Cloudflare, Storage e database, D1, `gommberg-lettori`, Console (https://dash.cloudflare.com/?to=/:account/workers/d1):
```sql
SELECT nome, testo, creato, nascosto FROM commenti WHERE id = {n};
```
**Se va tolto** (offese, diffamazione, pubblicità, consigli di acquisto, dati personali):
```sql
UPDATE commenti SET nascosto = 2 WHERE id = {n};
```
**Se può restare**, le segnalazioni si azzerano e il commento torna visibile:
```sql
DELETE FROM segnalazioni WHERE commento = {n};
UPDATE commenti SET nascosto = 0, segnalazioni = 0 WHERE id = {n};
```
Poi chiudi questa segnalazione. Regole e procedura: `redazione/sito/LETTORI.md`.
"""


def gh(*arg):
    return subprocess.run(["gh", *arg], capture_output=True, text=True, timeout=60)


def gia_aperta(t):
    """True se una segnalazione con questo titolo esiste già, aperta o chiusa. Se GitHub non risponde: None."""
    r = gh("issue", "list", "--state", "all", "--search", f'"{t}" in:title', "--json", "title", "--limit", "20")
    if r.returncode != 0:
        return None
    return any(i.get("title") == t for i in json.loads(r.stdout or "[]"))


def main():
    prova = "--prova" in sys.argv
    righe = elenco()
    if righe is None:
        return 0
    if not righe:
        print("Nessun commento segnalato.")
        return 0
    errori = 0
    for s in righe:
        t = titolo(s)
        if prova:
            print("Aprirei: " + t + "\n" + testo(s))
            continue
        c = gia_aperta(t)
        if c:
            print("Già segnalato: " + t)
            continue
        if c is None:
            print(f"::warning::GitHub non ha risposto alla ricerca di \"{t}\": riprovo al prossimo giro.")
            errori += 1
            continue
        arg = ["issue", "create", "--title", t, "--body", testo(s)]
        if os.environ.get("GITHUB_REPOSITORY_OWNER"):
            arg += ["--assignee", os.environ["GITHUB_REPOSITORY_OWNER"]]
        r = gh(*arg)
        print(("Aperta: " if r.returncode == 0 else "::error::Non aperta: ") + t + (" " + r.stdout.strip() if r.returncode == 0 else " " + r.stderr.strip()[:300]))
        errori += r.returncode != 0
    return 1 if errori else 0     # un giro fallito è già un avviso: GitHub scrive a Paolo


if __name__ == "__main__":
    sys.exit(main())
