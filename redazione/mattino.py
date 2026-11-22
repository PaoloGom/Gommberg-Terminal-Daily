#!/usr/bin/env python3
"""Controllo del mattino: l'edizione di oggi è uscita ed è arrivata dappertutto?

Lo lancia GitHub dal lunedì al venerdì verso le 10:15 di Roma (.github/workflows/mattino.yml), mezz'ora dopo l'ora in cui
il giornale deve essere in mano ai lettori. Nessun modello, nessun token: solo il repository, gommberg.com e gli esiti
di GitHub. Se tutto va bene non scrive a nessuno; se qualcosa non va esce con 1, e GitHub avvisa Paolo.

Cosa guarda, nell'ordine in cui l'edizione viaggia (mappa: redazione/ARCHITETTURA.md):
  1. Uscita      edizioni.json del ramo principale ha l'edizione di oggi, con il suo PDF e la sua pagina
  2. Sito        gommberg.com mostra quell'edizione (dati/recenti.json), la pagina e il PDF si aprono, La Gommunity
                 risponde (il servizio dei lettori, /api/lettori/)
  3. Pubblicazione  l'ultimo giro di sito.yml sul ramo principale è di oggi ed è verde
  4. Newsletter  l'ultimo giro di newsletter.yml è di oggi ed è verde, l'invio di oggi esiste in Kit, e il link
                 dell'email (la homepage ferma su questa edizione) si apre
  5. Pannello    la riga dell'edizione è nel registro del pannello, anche online
Nei giorni senza borsa non c'è niente da controllare ed esce con 0.

Uso:  python3 redazione/mattino.py [--adesso]
  --adesso  controlla subito (senza, fuori dalla fascia 10-12 di Roma non fa nulla: GitHub lo sveglia due volte, una
            per l'ora solare e una per l'ora legale, e lavora solo quella giusta)
Variabili: GITHUB_REPOSITORY e GH_TOKEN (esiti di GitHub: senza, quel controllo si salta e lo dice), KIT_API_KEY
(senza, l'invio in Kit non si guarda). Solo per le prove: GTD_BASE (il sito da controllare al posto di
https://gommberg.com/) e GTD_OGGI (AAAA-MM-GG, il giorno da controllare al posto di oggi)."""
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

QUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(QUI)
sys.path.insert(0, QUI)
import giorni as G  # noqa: E402

BASE = os.environ.get("GTD_BASE", "https://gommberg.com/").rstrip("/") + "/"
ROMA = ZoneInfo("Europe/Rome")
NO, NOTE = [], []


def riga(ok, cosa, dettaglio=""):
    print(("OK   " if ok else "NO   ") + cosa + (f": {dettaglio}" if dettaglio else ""))
    if not ok:
        NO.append(cosa)


def get(url, intestazioni=None):
    """(stato, corpo) senza mai lanciare eccezioni; con un parametro in coda perché nessuna cache risponda al posto del sito."""
    if url.startswith(BASE):
        url += ("&" if "?" in url else "?") + "v=" + str(int(time.time()))
    try:
        r = urllib.request.Request(url, headers={"User-Agent": "controllo-gommberg", **(intestazioni or {})})
        with urllib.request.urlopen(r, timeout=30) as f:
            return f.status, f.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:  # noqa: BLE001
        return f"errore {type(e).__name__}", b""


def con_pazienza(prova, tentativi=6, pausa=20):
    """Il sito e GitHub possono essere qualche secondo indietro: si riprova per due minuti prima di dire che non va."""
    for i in range(tentativi):
        ok, dettaglio = prova()
        if ok or i == tentativi - 1:
            return ok, dettaglio
        time.sleep(pausa)


def ultimo_giro(flusso, oggi):
    """L'ultimo giro di un flusso di GitHub sul ramo principale: deve essere di oggi e verde."""
    repo, token = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not (repo and token):
        NOTE.append(f"{flusso}: esito di GitHub non letto (mancano GITHUB_REPOSITORY o GH_TOKEN)")
        return None

    def prova():
        s, corpo = get(f"https://api.github.com/repos/{repo}/actions/workflows/{flusso}/runs?branch=main&per_page=1",
                       {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
        if s != 200:
            return False, f"GitHub risponde {s}"
        giri = json.loads(corpo).get("workflow_runs", [])
        if not giri:
            return False, "nessun giro"
        g = giri[0]
        quando = dt.datetime.fromisoformat(g["created_at"].replace("Z", "+00:00")).astimezone(ROMA)
        if quando.date() != oggi:
            return False, f"l'ultimo giro è del {quando:%d/%m alle %H:%M}, non di oggi"
        if g["status"] != "completed":
            return False, f"ancora in corso dalle {quando:%H:%M}"
        return g["conclusion"] == "success", f"{g['conclusion']} alle {quando:%H:%M}"
    return con_pazienza(prova)


def main():
    adesso = dt.datetime.now(ROMA)
    oggi = dt.date.fromisoformat(os.environ["GTD_OGGI"]) if os.environ.get("GTD_OGGI") else adesso.date()
    a_mano = "--adesso" in sys.argv or os.environ.get("A_MANO") == "true"
    if not a_mano and not 10 <= adesso.hour < 12:
        print(f"Sono le {adesso:%H:%M} di Roma: fuori dalla fascia 10-12 non controllo nulla.")
        return
    if not G.uscita(oggi):
        print(f"{oggi:%d/%m/%Y}: borse chiuse, oggi niente edizione e niente da controllare.")
        return
    n = G.numero(oggi)
    print(f"Controllo del mattino - {oggi:%d/%m/%Y}, edizione #{n:03d}, ore {adesso:%H:%M} di Roma\n")

    # 1. uscita
    voci = json.load(open(os.path.join(REPO, "edizioni.json"), encoding="utf-8"))
    voce = next((v for v in voci if v["data"] == oggi.isoformat()), None)
    if not voce:
        u = max(voci, key=lambda v: v["numero"])
        riga(False, "Uscita", f"l'edizione di oggi non è in edizioni.json (l'ultima è la #{u['numero']:03d} del {u['data']})")
        return
    riga(voce["numero"] == n and os.path.exists(os.path.join(REPO, voce["file"])) and os.path.exists(os.path.join(REPO, "e", f"{n:03d}.html")),
         "Uscita", f"#{voce['numero']:03d} \"{voce['titolo'][:70]}\", {voce['file']}")

    # 2. sito
    def online():
        s, corpo = get(BASE + "dati/recenti.json")
        try:
            primo = json.loads(corpo)["edizioni"][0]["numero"] if s == 200 else None
        except Exception:  # noqa: BLE001
            primo = None
        return primo == n, f"in testa la #{primo:03d}" if isinstance(primo, int) else f"dati/recenti.json risponde {s}"
    ok, d = con_pazienza(online)
    riga(ok, "Sito: l'edizione di oggi è in homepage", d)
    for cosa, url in (("Sito: pagina dell'edizione", f"e/{n:03d}.html"), ("Sito: PDF", voce["file"])):
        s, corpo = get(BASE + url)
        riga(s == 200 and len(corpo) > 1000, cosa, f"{url}: {s}, {len(corpo) // 1024} KB")
    # La Gommunity (G-13): il servizio dei lettori risponde per l'edizione di oggi
    s, corpo = get(BASE + f"api/lettori/{n:03d}")
    try:
        commenti = json.loads(corpo).get("commenti") if s == 200 else None
    except Exception:  # noqa: BLE001
        commenti = None
    riga(isinstance(commenti, list), "Sito: La Gommunity", f"api/lettori/{n:03d}: {s}" + (f", {len(commenti)} commenti" if isinstance(commenti, list) else ", la discussione non si carica"))

    # 3. pubblicazione
    g = ultimo_giro("sito.yml", oggi)
    if g:
        riga(g[0], "Pubblicazione (sito.yml, con la verifica dal vivo)", g[1])

    # 4. newsletter
    g = ultimo_giro("newsletter.yml", oggi)
    if g:
        riga(g[0], "Newsletter: giro di GitHub", g[1])
    if os.environ.get("KIT_API_KEY", "").strip():
        try:
            import newsletter as NL
            invio = NL.invii_esistenti().get(NL.etichetta({"numero": n}))
            riga(bool(invio), "Newsletter: invio in Kit", f"n. {invio.get('id')}, stato {invio.get('status')}" if invio else "nessun invio con l'etichetta di oggi")
        except SystemExit as e:
            riga(False, "Newsletter: invio in Kit", str(e)[:160])
    else:
        NOTE.append("invio in Kit non guardato (manca KIT_API_KEY)")
    s, corpo = get(BASE + f"?n={n}&leggi=1&ref=controllo")
    riga(s == 200 and len(corpo) > 1000, "Newsletter: il link dell'email si apre", f"?n={n}&leggi=1: {s}")

    # 5. pannello
    def nel_registro(testo):
        try:
            return any(x.get("n") == n for x in json.loads(testo))
        except Exception:  # noqa: BLE001
            return False
    p = os.path.join(REPO, "pannello", "registro.json")
    s, corpo = get(BASE + "pannello/registro.json")
    riga(os.path.exists(p) and nel_registro(open(p, encoding="utf-8").read()) and s == 200 and nel_registro(corpo),
         "Pannello: riga dell'edizione", f"nel repository e online ({s})")


if __name__ == "__main__":
    main()
    for x in NOTE:
        print("NOTA " + x)
    print("\n" + ("Tutto a posto." if not NO else ("1 cosa non va: " if len(NO) == 1 else f"{len(NO)} cose non vanno: ") + "; ".join(NO)))
    sys.exit(1 if NO else 0)
