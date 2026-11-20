#!/usr/bin/env python3
"""Collaudo di gommberg.com: apre ogni pagina del sito in un browser vero e la confronta con il sito di riferimento.

  python3 redazione/sito/collaudo.py <sito da provare> [<sito di riferimento>] [--pagine N]
  es.  python3 redazione/sito/collaudo.py https://gommberg.com/ https://paologom.github.io/Gommberg-Terminal-Daily/
  python3 redazione/sito/collaudo.py <sito> --veloce <cartella>   solo HTTP, senza browser, dopo ogni pubblicazione:
       le pagine principali e l'ultima edizione online sono identiche ai file della cartella pubblicata (con qualche
       tentativo, il tempo che Cloudflare le distribuisca), la redazione non è raggiungibile

Per ogni pagina (tutte le pagine fisse, le cartelle, le ultime N edizioni, una pagina inesistente, la homepage ferma su
un'edizione): stato HTTP, errori JavaScript, risorse dello stesso sito che non si caricano, testo visibile; se c'è il
riferimento, il testo deve essere uguale a parte gli indirizzi. Poi controlla che la redazione non sia raggiungibile
(salvo i file che il sito legge). Le statistiche (GoatCounter) sono bloccate: il collaudo non conta come visita.
Esce con 1 se trova un problema. Serve Playwright con Chromium. Non gira nell'attività del mattino.
"""
import asyncio
import json
import re
import sys
import urllib.error
import urllib.request
from playwright.async_api import async_playwright

ARG = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith("--") and sys.argv[i - 1] not in ("--pagine", "--veloce")]
if not ARG:
    sys.exit(__doc__)
PROVA = ARG[0].rstrip("/") + "/"
RIF = ARG[1].rstrip("/") + "/" if len(ARG) > 1 else None
N = int(sys.argv[sys.argv.index("--pagine") + 1]) if "--pagine" in sys.argv else 5
FISSE = ["", "index.html", "archivio.html", "glossario.html", "scommessa.html", "numeri.html", "progetto.html",
         "iscriviti.html", "benvenuto.html", "privacy.html", "basi.html", "ultima/", "pannello/", "consumi/"]
PRIVATI = ["redazione/ISTRUZIONI.md", "redazione/CARTA.md", "redazione/gommberg_engine.py", "redazione/fonti.json",
           "redazione/STATO.md", ".github/workflows/newsletter.yml", ".claude/settings.json", "README.md", "_redirects"]
BLOCCO = re.compile(r"goatcounter\.com|gc\.zgo\.at")


def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "collaudo-gommberg"}), timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:  # noqa: BLE001
        return f"errore {type(e).__name__}", b""


def normalizza(t, base):
    t = t.replace(base, "§/")
    t = re.sub(r"https?://[^\s\"']+", lambda m: m.group(0).split("/", 3)[-1], t)
    return re.sub(r"\s+", " ", t).strip()


async def apri(ctx, base, pagina):
    pg = await ctx.new_page()
    errori, falliti = [], []
    pg.on("pageerror", lambda e: errori.append(str(e)[:140]))
    pg.on("console", lambda m: errori.append("console: " + m.text[:140]) if m.type == "error" and "Failed to load resource" not in m.text else None)

    def fine(r):
        if r.url == base + pagina and r.request.is_navigation_request():
            return   # lo stato della pagina stessa si controlla a parte (la 404 deve rispondere 404)
        if r.url.startswith(base) and r.status >= 400 and not r.url.endswith("favicon.ico"):
            falliti.append(f"{r.status} {r.url[len(base):]}")
    pg.on("response", fine)
    # un PDF aperto dal browser senza schermo si interrompe (scaricamento): conta solo se risponde con un errore
    pg.on("requestfailed", lambda r: falliti.append(f"fallita {r.url[len(base):]}")
          if r.url.startswith(base) and not r.url.split("?")[0].endswith(".pdf") else None)
    stato = None
    try:
        r = await pg.goto(base + pagina, wait_until="networkidle", timeout=45000)
        stato = r.status if r else None
        await pg.wait_for_timeout(800)
        testo = await pg.evaluate("document.body ? document.body.innerText : ''")
        titolo = await pg.title()
    except Exception as e:  # noqa: BLE001
        testo, titolo = "", ""
        errori.append(f"apertura: {str(e)[:140]}")
    await pg.close()
    return stato, titolo, testo, errori, falliti


def veloce(cartella):
    import hashlib
    import time
    from pathlib import Path
    c = Path(cartella)
    ultima = sorted(p.name for p in (c / "e").glob("[0-9][0-9][0-9].html"))[-1]
    file = ["index.html", "edizioni.json", "dati/recenti.json", "e/" + ultima, "feed.xml", "redazione/scommessa/pagella.json"]
    h = lambda b: hashlib.sha256(b).hexdigest()[:12]
    for tentativo in range(12):
        diversi = []
        for f in file:
            s, corpo = get(PROVA + f + "?v=" + str(time.time()))
            if s != 200 or h(corpo) != h((c / f).read_bytes()):
                diversi.append(f"{f}: {s}{'' if s != 200 else ' contenuto diverso'}")
        s, _ = get(PROVA)
        if s != 200:
            diversi.append(f"homepage: {s}")
        if not diversi:
            break
        time.sleep(15)
    privati = [f"{x}: {s}" for x in PRIVATI for s in [get(PROVA + x)[0]] if s != 404]
    for x in diversi:
        print("NO   online diverso da quanto pubblicato:", x)
    for x in privati:
        print("NO   indirizzo privato raggiungibile:", x)
    print(f"{'OK' if not diversi + privati else 'PROBLEMI'}: {PROVA} dopo {tentativo + 1} tentativ{'o' if not tentativo else 'i'}, "
          f"ultima edizione {ultima}, {len(PRIVATI)} indirizzi privati controllati")
    sys.exit(1 if diversi + privati else 0)


async def main():
    if "--veloce" in sys.argv:
        veloce(sys.argv[sys.argv.index("--veloce") + 1])
    s, corpo = get(PROVA + "edizioni.json")
    if s != 200:
        sys.exit(f"ERRORE: {PROVA}edizioni.json risponde {s}")
    ed = json.loads(corpo)
    elenco = ed if isinstance(ed, list) else ed.get("edizioni", [])
    numeri = sorted({int(e["numero"]) for e in elenco if isinstance(e, dict) and e.get("numero")})[-N:]
    pagine = FISSE + [f"e/{n:03d}.html" for n in numeri] + [f"?n={numeri[0]}&leggi=1", "pagina-che-non-esiste.html"]
    problemi = 0
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1440, "height": 900})
        await ctx.route(BLOCCO, lambda r: r.abort())
        for pag in pagine:
            sp, tp, xp, ep, fp = await apri(ctx, PROVA, pag)
            atteso = 404 if pag == "pagina-che-non-esiste.html" else 200
            note = []
            if sp != atteso:
                note.append(f"stato {sp} (atteso {atteso})")
            note += ep + fp
            if not xp.strip():
                note.append("pagina vuota")
            if "non raggiungibile" in xp.lower():
                note.append("messaggio 'non raggiungibile' nella pagina")
            if RIF:
                sr, tr, xr, _, _ = await apri(ctx, RIF, pag)
                if sr == atteso and normalizza(xp, PROVA) != normalizza(xr, RIF):
                    a, c = normalizza(xp, PROVA), normalizza(xr, RIF)
                    i = next((k for k in range(min(len(a), len(c))) if a[k] != c[k]), min(len(a), len(c)))
                    note.append(f"testo diverso dal riferimento dal carattere {i}: «{a[max(0, i - 40):i + 60]}» / «{c[max(0, i - 40):i + 60]}»")
                if tp != tr:
                    note.append(f"titolo diverso: «{tp}» / «{tr}»")
            print(("OK   " if not note else "NO   ") + (pag or "/") + ("" if not note else "\n       " + "\n       ".join(note[:8])))
            problemi += bool(note)
        await b.close()
    for x in PRIVATI:
        s, _ = get(PROVA + x)
        ok = s == 404
        print(("OK   " if ok else "NO   ") + f"privato {x}: {s}")
        problemi += not ok
    for x in ("redazione/glossario.json", "redazione/meccanismi.json", "redazione/glossario_sito.json",
              "redazione/scommessa/pagella.json", "feed.xml", "sitemap.xml", "dati/recenti.json"):
        s, _ = get(PROVA + x)
        print(("OK   " if s == 200 else "NO   ") + f"pubblico {x}: {s}")
        problemi += s != 200
    print(f"\n{'Nessun problema' if not problemi else f'{problemi} problemi'} su {len(pagine)} pagine e {len(PRIVATI) + 7} indirizzi")
    sys.exit(1 if problemi else 0)


if __name__ == "__main__":
    asyncio.run(main())
