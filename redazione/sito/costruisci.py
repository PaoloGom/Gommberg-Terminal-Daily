#!/usr/bin/env python3
"""Il sito pubblico di gommberg.com: copia in una cartella solo ciò che i lettori devono vedere.

Regola: è pubblico ogni file tracciato da git (i file mai aggiunti a git restano fuori; dei tracciati si copia il
contenuto su disco, anche se non ancora committato) tranne la redazione (motore,
istruzioni, prompt), i file e le cartelle nascosti a qualunque profondità (.github, .claude, .env...), le cartelle di
lavoro che cominciano con _ e il README. Della redazione escono solo i file di LETTI, quelli che il sito legge.
I link simbolici non si copiano mai, nemmeno quando è una cartella del percorso a esserlo (potrebbero puntare alla
redazione).

Se una pagina pubblicata nomina un file della redazione che non è in LETTI, lo script lo segnala (AVVISO): o va
aggiunto a LETTI, o la pagina non funzionerebbe su gommberg.com. Al contrario, nominare un file non basta a pubblicarlo.

Scrive anche _headers (Access-Control-Allow-Origin: *, come GitHub Pages: i file del sito restano leggibili da altri
siti, per esempio da un artifact) e _redirects (Cloudflare): "/" e ogni cartella con un index.html servono il loro index.html, e le pagine
in radice si aprono anche senza ".html", come su GitHub Pages. Senza, con html_handling "none" (che lascia gli
indirizzi .html come sono), "/" darebbe 404.

Controlla infine che ogni link interno delle pagine porti a un file pubblicato. Non blocca mai la pubblicazione per
un link (AVVISO ed esce con 0); si ferma solo se un file privato stesse per finire nel sito.

Uso:  python3 redazione/sito/costruisci.py <cartella di uscita> [--anteprima]
      --anteprima  per gli indirizzi di prova: niente statistiche (le visite di prova non si contano) e noindex
La cartella di uscita è nuova o vuota; si riscrive solo se il nome comincia con _ (es. _sito) e l'ha scritta questo
script (la riconosce dalla firma del suo _redirects). Non cancella mai nient'altro.
Lo lancia .github/workflows/sito.yml a ogni push su main (gommberg.com) e su prova (anteprima). Zero token.
"""
import html.parser
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit, unquote

REPO = Path(__file__).resolve().parents[2]
LETTI = ["redazione/glossario.json", "redazione/glossario_sito.json", "redazione/meccanismi.json",
         "redazione/scommessa/pagella.json"]
FIRMA = "# Scritto da redazione/sito/costruisci.py: non modificare a mano."
NOMINATI = re.compile(r"""(?:^|[^A-Za-z0-9_])(redazione/[A-Za-z0-9_./-]+\.[a-z]{2,4})""")
STATISTICHE = re.compile(r'<script[^>]*data-goatcounter=[^>]*>\s*</script>\s*', re.I)


def pubblico(rel: PurePosixPath) -> bool:
    if any(p.startswith(".") for p in rel.parts) or "__pycache__" in rel.parts:
        return False
    return not (rel.parts[0].startswith("_") or rel.parts[0] == "redazione" or str(rel) == "README.md")


def tracciati():
    r = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z"], capture_output=True, check=True)
    return [PurePosixPath(p) for p in r.stdout.decode("utf-8", "surrogateescape").split("\0") if p]


def prepara(uscita: Path):
    if uscita == REPO or uscita in REPO.parents:
        sys.exit("ERRORE: la cartella di uscita non può essere il repository né una cartella che lo contiene")
    if uscita.exists() and (not uscita.is_dir() or any(uscita.iterdir())):
        # si cancella solo una cartella che comincia con _ e che porta la firma di questo script: mai altro
        firma = uscita / "_redirects"
        if not (uscita.is_dir() and uscita.name.startswith("_") and not firma.is_symlink() and firma.is_file()
                and firma.read_text(encoding="utf-8").startswith(FIRMA)):
            sys.exit(f"ERRORE: {uscita} esiste e non è vuota: scegli una cartella nuova (o una _cartella già scritta da questo script)")
        shutil.rmtree(uscita)
    uscita.mkdir(parents=True, exist_ok=True)


def copia(uscita: Path):
    file, saltati = [], []
    for rel in tracciati():
        if not pubblico(rel) and str(rel) not in LETTI:
            continue
        sorgente = REPO / rel
        if sorgente.is_symlink() or not sorgente.is_file() or os.path.realpath(sorgente) != str(REPO / rel):
            saltati.append(str(rel))
            continue
        (uscita / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(sorgente, uscita / rel)
        file.append(rel)
    mancano = [l for l in LETTI if PurePosixPath(l) not in file]
    return file, saltati, mancano


def reindirizzamenti(uscita: Path, file):
    righe = [FIRMA, "# Ogni cartella con index.html si apre dal suo indirizzo; le pagine in radice anche senza .html."]
    cartelle = sorted({f.parent for f in file if f.name == "index.html"}, key=lambda p: (len(p.parts), str(p)))
    for c in cartelle:
        if str(c) == ".":
            righe.append("/ /index.html 200")
        elif " " not in str(c):
            u = "/" + str(c)
            righe += [f"{u} {u}/ 301", f"{u}/ {u}/index.html 200"]
    for f in sorted(file):
        if len(f.parts) == 1 and f.suffix == ".html" and f.name not in ("index.html", "404.html") and " " not in f.name:
            righe.append(f"/{f.stem} /{f.name} 301")
    (uscita / "_redirects").write_text("\n".join(righe) + "\n", encoding="utf-8")
    (uscita / "_headers").write_text("/*\n  Access-Control-Allow-Origin: *\n", encoding="utf-8")
    return len(cartelle)


def ritocchi(uscita: Path, file, anteprima: bool):
    if anteprima:
        for rel in file:
            if rel.suffix == ".html":
                f = uscita / rel
                t = f.read_text(encoding="utf-8")
                n = STATISTICHE.sub("", t).replace("<head>", '<head>\n<meta name="robots" content="noindex">', 1)
                if n != t:
                    f.write_text(n, encoding="utf-8")


class Link(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.link, self.base = [], False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "base" and a.get("href"):
            self.base = True
        for k in ("href", "src"):
            if a.get(k):
                self.link.append(a[k])


def controlla(uscita: Path, file):
    """Link interni delle pagine verso file non pubblicati (per esempio verso la redazione)."""
    problemi = []
    for rel in file:
        if rel.suffix not in (".html", ".js"):
            continue
        testo = (uscita / rel).read_text(encoding="utf-8", errors="replace")
        for n in set(NOMINATI.findall(testo)):
            if n not in LETTI and not n.endswith((".py", ".sh", ".md")):
                problemi.append(f"{rel}: nomina {n}, che non è nel sito (aggiungerlo a LETTI se la pagina lo legge)")
        if rel.suffix != ".html":
            continue
        p = Link()
        p.feed(testo)
        for u in p.link:
            s = urlsplit(u)
            if s.scheme or s.netloc or not s.path or u.startswith(("#", "{", "$")):
                continue
            base = PurePosixPath(".") if (p.base or s.path.startswith("/")) else rel.parent
            dest = PurePosixPath(os.path.normpath(str(base / unquote(s.path.lstrip("/")))))
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
    anteprima = "--anteprima" in sys.argv
    prepara(uscita)
    file, saltati, mancano = copia(uscita)
    n = reindirizzamenti(uscita, file)
    ritocchi(uscita, file, anteprima)
    # ultima difesa: nel sito solo file pubblici, i file di LETTI, _redirects e _headers
    for p in uscita.rglob("*"):
        rel = PurePosixPath(p.relative_to(uscita).as_posix())
        if p.is_file() and str(rel) not in ("_redirects", "_headers") and not pubblico(rel) and str(rel) not in LETTI:
            sys.exit(f"ERRORE: {rel} non è pubblico e stava per finire nel sito")
    tot = sum((uscita / f).stat().st_size for f in file)
    print(f"Sito pubblico: {len(file)} file, {tot / 1e6:.1f} MB{' (anteprima: senza statistiche, noindex)' if anteprima else ''}")
    print(f"Dalla redazione: {', '.join(l for l in LETTI if l not in mancano)}; cartelle con indirizzo proprio: {n}")
    for x in mancano:
        print(f"AVVISO: {x} è in LETTI ma non esiste nel repository")
    for x in saltati:
        print(f"AVVISO: {x} è un link simbolico o non è un file: non pubblicato")
    problemi = controlla(uscita, file)
    for x in problemi[:40]:
        print("AVVISO:", x)


if __name__ == "__main__":
    main()
