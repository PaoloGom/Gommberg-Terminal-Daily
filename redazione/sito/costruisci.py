#!/usr/bin/env python3
"""Il sito pubblico di gommberg.com: copia in una cartella solo ciò che i lettori devono vedere.

Regola, una sola: è pubblico tutto il repository tranne la redazione (motore, istruzioni, prompt), i file nascosti
(.github, .claude, .git...), le cartelle di lavoro che cominciano con _ (come _sito) e il README. Della redazione escono solo i file che il sito legge davvero: lo script li
trova da solo cercando gli indirizzi "redazione/....json|csv" nelle pagine pubblicate, quindi una pagina nuova che
legge un file della redazione non va registrata da nessuna parte.

Scrive anche _redirects (Cloudflare): "/" e ogni cartella con un index.html servono il loro index.html, come su
GitHub Pages; senza, con html_handling "none" (che lascia gli indirizzi .html come sono) "/" darebbe 404.

Controlla infine che ogni link interno delle pagine porti a un file pubblicato. Non blocca mai la pubblicazione:
segnala (AVVISO) ed esce con 0; con --severo esce con 1 se trova problemi (per i collaudi, non per la pubblicazione).

Uso:  python3 redazione/sito/costruisci.py <cartella di uscita> [--anteprima] [--severo]
      --anteprima  per gli indirizzi di prova: toglie lo script delle statistiche (le visite di prova non si contano)
Lo lancia .github/workflows/sito.yml a ogni push su main (gommberg.com) e su prova (anteprima). Zero token.
"""
import html.parser
import os
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlsplit, unquote

REPO = Path(__file__).resolve().parents[2]
ESCLUSI = {"redazione", "README.md"}            # più tutto ciò che comincia con il punto
LETTI = re.compile(r"""["'](redazione/[A-Za-z0-9_./-]+\.(?:json|csv))["']""")
STATISTICHE = re.compile(r'<script[^>]*data-goatcounter=[^>]*>\s*</script>\s*', re.I)
BASE = re.compile(r'<base href="[^"]*">', re.I)


def pubblico(rel: Path) -> bool:
    primo = rel.parts[0]
    return not (primo.startswith((".", "_")) or primo in ESCLUSI or "__pycache__" in rel.parts)


def copia(uscita: Path):
    if uscita.exists():
        shutil.rmtree(uscita)
    uscita.mkdir(parents=True)
    pagine = []
    for radice, cartelle, file in os.walk(REPO):
        r = Path(radice).relative_to(REPO)
        if r.parts and not pubblico(r):
            cartelle[:] = []
            continue
        cartelle[:] = [c for c in cartelle if pubblico(r / c) and (REPO / r / c).resolve() != uscita]
        for f in file:
            rel = r / f
            if not pubblico(rel):
                continue
            (uscita / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / rel, uscita / rel)
            if f.endswith((".html", ".js")):
                pagine.append(rel)
    # i file della redazione che le pagine pubblicate leggono
    letti = set()
    for rel in pagine:
        letti.update(LETTI.findall((uscita / rel).read_text(encoding="utf-8", errors="replace")))
    for l in sorted(letti):
        if (REPO / l).is_file():
            (uscita / l).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / l, uscita / l)
    return pagine, sorted(letti)


def reindirizzamenti(uscita: Path):
    righe = ["# Scritto da redazione/sito/costruisci.py: non modificare a mano.",
             "# Ogni cartella con index.html si apre dal suo indirizzo, come su GitHub Pages."]
    cartelle = sorted({p.parent for p in uscita.rglob("index.html")}, key=lambda p: (len(p.parts), str(p)))
    for c in cartelle:
        rel = c.relative_to(uscita)
        if str(rel) == ".":
            righe.append("/ /index.html 200")
        else:
            u = "/" + rel.as_posix()
            righe += [f"{u} {u}/ 301", f"{u}/ {u}/index.html 200"]
    (uscita / "_redirects").write_text("\n".join(righe) + "\n", encoding="utf-8")
    return len(cartelle)


def ritocchi(uscita: Path, pagine, anteprima: bool):
    # 404.html si apre a qualunque profondità, quindi ha un <base> assoluto: qui il sito sta alla radice del dominio
    p404 = uscita / "404.html"
    if p404.is_file():
        t = p404.read_text(encoding="utf-8")
        p404.write_text(BASE.sub('<base href="/">', t, count=1), encoding="utf-8")
    if anteprima:
        for rel in pagine:
            f = uscita / rel
            if f.suffix == ".html":
                t = f.read_text(encoding="utf-8")
                n = STATISTICHE.sub("", t)
                if n != t:
                    f.write_text(n, encoding="utf-8")


class Link(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.link, self.base = [], None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "base" and a.get("href"):
            self.base = a["href"]
        for k in ("href", "src"):
            if a.get(k) and not (tag == "a" and a.get(k, "").startswith("#")):
                self.link.append(a[k])


def controlla(uscita: Path, pagine):
    problemi = []
    for rel in pagine:
        if rel.suffix != ".html":
            continue
        p = Link()
        p.feed((uscita / rel).read_text(encoding="utf-8", errors="replace"))
        for u in p.link:
            s = urlsplit(u)
            if s.scheme or s.netloc or u.startswith(("mailto:", "tel:", "javascript:", "data:", "#", "{", "$")):
                continue
            if not s.path:
                continue
            if s.path.startswith("/"):
                dest = Path(unquote(s.path.lstrip("/")))
            else:
                base = Path(p.base.lstrip("/")) if p.base and p.base.startswith("/") else rel.parent
                if p.base:   # nella copia pubblica il <base> della 404 è la radice
                    base = Path(".")
                dest = Path(os.path.normpath(base / unquote(s.path)))
            if str(dest).startswith(".."):
                problemi.append(f"{rel}: {u} esce dal sito")
                continue
            f = uscita / dest
            if s.path.endswith("/") or f.is_dir():
                f = f / "index.html"
            if not f.is_file():
                problemi.append(f"{rel}: {u} non porta a nessun file pubblicato")
    return sorted(set(problemi))


def main():
    arg = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not arg:
        sys.exit(__doc__)
    uscita = Path(arg[0]).resolve()
    dentro = uscita == REPO or REPO in uscita.parents
    if dentro and not (uscita.parent == REPO and uscita.name.startswith("_")):
        sys.exit("ERRORE: la cartella di uscita deve stare fuori dal repository o in cima con un nome che comincia con _ (es. _sito)")
    anteprima = "--anteprima" in sys.argv
    pagine, letti = copia(uscita)
    n = reindirizzamenti(uscita)
    ritocchi(uscita, pagine, anteprima)
    file = [p for p in uscita.rglob("*") if p.is_file()]
    print(f"Sito pubblico: {len(file)} file, {sum(p.stat().st_size for p in file) / 1e6:.1f} MB"
          f"{' (anteprima, senza statistiche)' if anteprima else ''}")
    print(f"Dalla redazione, perché il sito li legge: {', '.join(letti) or 'nessuno'}")
    print(f"Cartelle con indirizzo proprio: {n}")
    vietati = [p for p in file if p.relative_to(uscita).parts[0] == "redazione" and str(p.relative_to(uscita)) not in letti]
    if vietati:   # non deve mai succedere: è la ragione per cui esiste questo script
        sys.exit(f"ERRORE: file della redazione nel sito pubblico: {vietati[:5]}")
    problemi = controlla(uscita, pagine)
    for x in problemi[:40]:
        print("AVVISO link:", x)
    if problemi:
        print(f"AVVISO: {len(problemi)} link interni senza file")
    if problemi and "--severo" in sys.argv:
        sys.exit(1)


if __name__ == "__main__":
    main()
