#!/usr/bin/env python3
"""Il vecchio indirizzo (paologom.github.io/Gommberg-Terminal-Daily) dopo il passaggio a gommberg.com: per ogni pagina
che esisteva, una pagina che porta subito alla stessa pagina su gommberg.com, conservando ?n=...&leggi=1 (i link delle
email) e #... (le ancore di Impara). Ogni altro indirizzo (PDF, anteprime, pagine mai esistite) lo gira 404.html con lo
stesso criterio. Il feed diventa un avviso con il feed nuovo (i lettori di feed non seguono i reindirizzamenti delle pagine).
Google tratta il reindirizzamento immediato con canonical come uno spostamento permanente.

  python3 redazione/sito/vecchio_indirizzo.py <sito pubblico già passato a gommberg.com> <cartella di uscita>

La cartella di uscita deve essere nuova o vuota (un .git dentro, come in una worktree, si lascia stare): lo script non
cancella mai nulla. Il contenuto va sul ramo orfano vecchio-indirizzo, da cui GitHub Pages pubblica dopo il passaggio;
con G-12 (repository privato) gli stessi file vanno in un repository pubblico con il vecchio nome. Si genera una volta.
"""
import html
import sys
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

NUOVO = "https://gommberg.com/"
STILE = ("body{margin:0;min-height:100vh;display:grid;place-items:center;background:#0E0E0E;color:#F5F3EF;"
         "font:16px/1.5 'IBM Plex Sans',Arial,Helvetica,sans-serif}a{color:#F26B1D}p{max-width:30em;padding:0 24px;text-align:center}")


def pagina(dest, js):
    d = html.escape(dest, quote=True)
    return f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>Gommberg Terminal Daily è su gommberg.com</title>
<link rel="canonical" href="{d}">
<meta property="og:title" content="Gommberg Terminal Daily">
<meta property="og:description" content="I mercati globali spiegati, ogni mattina in 6 pagine. Ora su gommberg.com.">
<meta property="og:url" content="{d}">
<meta property="og:image" content="{NUOVO}assets/copertina.png">
<script>{js}</script>
<meta http-equiv="refresh" content="0; url={d}">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>{STILE}</style>
</head>
<body><p>Il Gommberg Terminal Daily ora è su <a href="{d}">gommberg.com</a>.</p></body>
</html>
"""


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sito, uscita = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    if not (sito / "index.html").is_file() or not (sito / "_redirects").is_file():
        sys.exit(f"ERRORE: {sito} non è un sito pubblico scritto da costruisci.py")
    if uscita == sito or sito in uscita.parents:
        sys.exit("ERRORE: la cartella di uscita non può stare dentro il sito pubblico")
    if uscita.exists() and (not uscita.is_dir() or [p for p in uscita.iterdir() if p.name != ".git"]):
        sys.exit(f"ERRORE: {uscita} non è vuota: serve una cartella nuova (o vuota, anche con il solo .git)")
    if "paologom.github.io" in (sito / "index.html").read_text(encoding="utf-8"):
        sys.exit("ERRORE: il sito pubblico non è ancora passato a gommberg.com (prima passaggio.py --scrivi e costruisci.py)")
    uscita.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted(sito.rglob("*.html")):
        rel = f.relative_to(sito).as_posix()
        if rel == "404.html" or rel.startswith("redazione/"):
            continue
        dest = NUOVO + (rel[:-len("index.html")] if rel.endswith("index.html") else rel)
        js = f'location.replace("{dest}" + location.search + location.hash)'
        (uscita / rel).parent.mkdir(parents=True, exist_ok=True)
        (uscita / rel).write_text(pagina(dest, js), encoding="utf-8")
        n += 1
    js404 = ('location.replace("' + NUOVO + '" + location.pathname.replace(/^\\/Gommberg-Terminal-Daily\\/?/i, "") '
             '+ location.search + location.hash)')
    (uscita / "404.html").write_text(pagina(NUOVO, js404), encoding="utf-8")
    ora = format_datetime(datetime.now(timezone.utc))
    (uscita / "feed.xml").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>
<title>Gommberg Terminal Daily</title><link>{NUOVO}</link>
<description>Il Gommberg Terminal Daily si è spostato su gommberg.com: il feed nuovo è {NUOVO}feed.xml</description>
<language>it-it</language>
<item><title>Il Gommberg si è spostato su gommberg.com</title><link>{NUOVO}</link>
<guid isPermaLink="false">gommberg-trasloco-gommberg-com</guid><pubDate>{ora}</pubDate>
<description>Da oggi il Gommberg Terminal Daily è su gommberg.com. Per continuare a riceverlo qui, aggiungi il feed nuovo: {NUOVO}feed.xml</description></item>
</channel></rss>
""", encoding="utf-8")
    (uscita / ".nojekyll").write_text("", encoding="utf-8")
    (uscita / "README.md").write_text(
        "# Gommberg Terminal Daily\n\nIl sito ora è su **[gommberg.com](https://gommberg.com/)**. Questo ramo contiene solo i "
        "reindirizzamenti dal vecchio indirizzo (generati da `redazione/sito/vecchio_indirizzo.py`).\n", encoding="utf-8")
    print(f"Vecchio indirizzo: {n} pagine di reindirizzamento, 404.html per tutto il resto, feed con l'avviso")


if __name__ == "__main__":
    main()
