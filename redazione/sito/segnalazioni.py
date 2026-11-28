#!/usr/bin/env python3
"""Avviso a Paolo quando un lettore segnala un commento della Gommunity (G-13).

Lo lancia GitHub ogni 3 ore tra le 8 e le 23 di Roma (.github/workflows/segnalazioni.yml, con la sveglia dell'orologio
di Cloudflare, G-58). Legge da gommberg.com l'elenco dei commenti segnalati
che la redazione non ha ancora tolto (/api/lettori/segnalazioni: numero, edizione, quante reti, se è già nascosto; mai
il testo) e tiene una segnalazione di GitHub per commento, assegnata a Paolo e con l'etichetta "gommunity": GitHub gli
manda l'email. Nessun modello, nessun segreto oltre al token del giro.
  - commento mai segnalato prima      apre la segnalazione (al massimo NUOVE per giro: le altre al giro dopo, prima i nascosti)
  - segnalazione aperta, e il commento nel frattempo è stato nascosto dai lettori   aggiunge una riga e lo scrive nel titolo
  - segnalazione chiusa, e il commento è stato segnalato di nuovo dopo la chiusura  la riapre con una riga
Le segnalazioni esistenti si leggono con una sola chiamata per giro (elenco per etichetta, non ricerca).

Il testo del commento non entra mai nella segnalazione: il repository è pubblico, e un commento da togliere non va
copiato altrove. Paolo lo legge dal database, con il comando scritto nella segnalazione (procedura: LETTORI.md).

Se qualcosa non va (il sito non dà l'elenco, GitHub non risponde o rifiuta) lo scrive nel riepilogo e ci riprova al
giro dopo; il giro fallisce, e GitHub avvisa Paolo, solo una volta al giorno (il giro tra le 11 e le 14 di Roma, ORA_AVVISO) o se
è lanciato a mano: un guasto che dura non deve diventare un'email a ogni giro.

Uso:  python3 redazione/sito/segnalazioni.py [--prova]
  --prova  stampa che cosa farebbe, senza toccare GitHub
Solo per le prove: GTD_BASE (il sito al posto di https://gommberg.com/), GTD_ELENCO (un file JSON al posto del sito),
GTD_ESISTENTI (un file JSON al posto dell'elenco delle segnalazioni di GitHub) e GTD_ORA (l'ora di Roma, 0-23)."""
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


ETICHETTA = "gommunity"
NUOVE = 5          # segnalazioni nuove aperte in un giro: una raffica di Segnala non diventa una raffica di email
ORA_AVVISO = range(11, 14)   # i giri di Roma tra le 11 e le 13:59: ne cade sempre uno solo al giorno, sia quello
                             # dell'orologio (11:15) sia quello della riserva di GitHub (11:15 d'inverno, 12:15 d'estate)


def chiave(s):
    """L'inizio del titolo, uguale per sempre: è ciò che lega un commento alla sua segnalazione."""
    return f"La Gommunity: commento n. {s['id']} segnalato"


def titolo(s):
    return chiave(s) + f" (edizione n. {s['ed']:03d})" + (" - nascosto" if s.get("nascosto") else "")


def istante(iso):
    try:
        return dt.datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    except ValueError:
        return None


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
    try:
        return subprocess.run(["gh", *arg], capture_output=True, text=True, timeout=60)
    except Exception as e:  # noqa: BLE001
        return subprocess.CompletedProcess(arg, 1, "", f"{type(e).__name__}: {e}")


def esistenti():
    """Le segnalazioni già fatte, aperte e chiuse, con una sola chiamata. None se GitHub non risponde."""
    try:
        if os.environ.get("GTD_ESISTENTI"):
            return json.load(open(os.environ["GTD_ESISTENTI"], encoding="utf-8"))
        r = gh("issue", "list", "--label", ETICHETTA, "--state", "all", "--limit", "1000", "--json", "number,title,state,closedAt")
        return json.loads(r.stdout) if r.returncode == 0 else None
    except Exception:  # noqa: BLE001
        return None


def stato(s):
    reti = s.get("reti") or 1
    return ("nascosto ai lettori (segnalato da 3 reti diverse)" if s.get("nascosto")
            else f"ancora visibile, segnalato da {reti} {'rete' if reti == 1 else 'reti'}")


def mosse(righe, fatte):
    """Che cosa fare per ogni commento segnalato: [(azione, commento, segnalazione esistente o None)]."""
    out, nuove = [], 0
    for s in righe:
        k = chiave(s)
        i = next((x for x in fatte if x.get("title") == k or str(x.get("title", "")).startswith(k + " ")), None)
        if i is None:
            nuove += 1
            out.append(("apri" if nuove <= NUOVE else "rimanda", s, None))
        elif str(i.get("state", "")).upper() == "CLOSED":
            u, c = istante(s.get("ultima")), istante(i.get("closedAt"))
            if u and c and u > c:
                out.append(("riapri", s, i))
        elif s.get("nascosto") and not str(i.get("title", "")).endswith(" - nascosto"):
            out.append(("nascosto", s, i))
    return out


def esegui(azione, s, i):
    """True se GitHub ha fatto ciò che serviva."""
    if azione == "apri":
        gh("label", "create", ETICHETTA, "--color", "F26B1D", "--description", "Commenti della Gommunity segnalati dai lettori", "--force")
        arg = ["issue", "create", "--title", titolo(s), "--body", testo(s), "--label", ETICHETTA]
        if os.environ.get("GITHUB_REPOSITORY_OWNER"):
            arg += ["--assignee", os.environ["GITHUB_REPOSITORY_OWNER"]]
        r = gh(*arg)
    elif azione == "riapri":
        r = gh("issue", "reopen", str(i["number"]), "--comment",
               f"Segnalato di nuovo il {quando(s.get('ultima'))} (ora di Roma). Ora è {stato(s)}. I comandi sono qui sopra.")
        if r.returncode == 0:
            gh("issue", "edit", str(i["number"]), "--title", titolo(s))
    else:
        r = gh("issue", "comment", str(i["number"]), "--body", f"Altri lettori l'hanno segnalato: ora è {stato(s)}. I comandi sono qui sopra.")
        if r.returncode == 0:
            r = gh("issue", "edit", str(i["number"]), "--title", titolo(s))
    if r.returncode != 0:
        print(f"::warning::GitHub ha rifiutato ({azione}, commento n. {s['id']}): {r.stderr.strip()[:200]}")
    return r.returncode == 0


def main():
    prova = "--prova" in sys.argv
    guasti = 0
    righe = elenco()
    fatte = esistenti() if righe else []
    if righe is None:
        guasti += 1
    elif fatte is None:
        print("::warning::GitHub non ha dato l'elenco delle segnalazioni già fatte: riprovo al prossimo giro.")
        guasti += 1
    elif not righe:
        print("Nessun commento segnalato.")
    else:
        piano = mosse(righe, fatte)
        etichette = {"apri": "Apro", "riapri": "Riapro", "nascosto": "Aggiorno (ora nascosto)", "rimanda": "Al prossimo giro"}
        for azione, s, i in piano:
            print(("Farei - " if prova else "") + etichette[azione] + ": " + titolo(s) + (f" (segnalazione n. {i['number']})" if i else ""))
            if prova and azione == "apri":
                print(testo(s))
            if not prova and azione != "rimanda":
                guasti += not esegui(azione, s, i)
        if not piano:
            print(f"{len(righe)} commenti segnalati, tutti già avvisati.")
    if not guasti:
        return 0
    ora = int(os.environ["GTD_ORA"]) if os.environ.get("GTD_ORA") else dt.datetime.now(ROMA).hour
    if ora in ORA_AVVISO or os.environ.get("A_MANO") == "true":
        print("::error::L'avviso sulle segnalazioni della Gommunity non funziona: vedi gli avvisi qui sopra.")
        return 1          # una volta al giorno il giro fallisce, e GitHub scrive a Paolo
    return 0


if __name__ == "__main__":
    sys.exit(main())
