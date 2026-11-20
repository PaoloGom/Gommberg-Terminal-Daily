#!/usr/bin/env python3
"""Il passaggio del sito da paologom.github.io/Gommberg-Terminal-Daily a gommberg.com (G-11). Si lancia UNA volta,
nel weekend del passaggio, sull'ultima versione del ramo principale; poi questo file si cancella (resta nello storico).

  python3 redazione/sito/passaggio.py           mostra cosa cambierebbe, senza scrivere
  python3 redazione/sito/passaggio.py --scrivi  scrive

Cosa fa: (1) ogni indirizzo assoluto del vecchio sito diventa gommberg.com, anche nella forma codificata dei link di
WhatsApp, nelle pagine, nel feed, nella mappa, nelle edizioni e nei due generatori (pagine.py, newsletter.py) e nel
modello delle email; (2) 404.html con il <base> alla radice; (3) "I numeri" somma per ogni edizione le visite contate
con il vecchio percorso e con il nuovo (GoatCounter conta il percorso, non il dominio); (4) README e tabella dei
riferimenti di PROGETTO.md. Non tocca lo storico (righe datate di PROGETTO.md, redazione/archivio/) né i riferimenti
al repository GitHub, che cambiano con G-12.
"""
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VECCHIO, NUOVO = "https://paologom.github.io/Gommberg-Terminal-Daily/", "https://gommberg.com/"
FORME = [(VECCHIO, NUOVO), (VECCHIO.replace("https://", "https%3A//"), NUOVO.replace("https://", "https%3A//")),
         (VECCHIO.replace(":", "%3A").replace("/", "%2F"), NUOVO.replace(":", "%3A").replace("/", "%2F")),
         (VECCHIO.replace("/", "\\/"), NUOVO.replace("/", "\\/"))]
SALTA = {"redazione/PROGETTO.md", "redazione/sito/passaggio.py", "redazione/sito/vecchio_indirizzo.py",
         "redazione/sito/collaudo.py", ".github/workflows/sito.yml"}
TESTO = (".html", ".js", ".json", ".xml", ".py", ".md", ".css", ".txt", ".sh", ".csv", ".yml")


def ritocchi_mirati(rel, t):
    if rel == "404.html":
        t = t.replace('<base href="/Gommberg-Terminal-Daily/">', '<base href="/">')
    if rel == "numeri.html":
        vecchio = 'const v = await Promise.all(ult.map((e) => Promise.all([conta(PRE + "e/" + pad(e.numero) + ".html"), conta("pdf-" + pad(e.numero))])));'
        nuovo = ('// prima di gommberg.com il sito stava in /Gommberg-Terminal-Daily/: per le edizioni di allora si sommano i due percorsi\n'
                 '    const VECCHIO = "/Gommberg-Terminal-Daily/";\n'
                 '    const pagina = (p) => PRE === VECCHIO ? conta(PRE + p) : Promise.all([conta(PRE + p), conta(VECCHIO + p)])\n'
                 '      .then(([a, b]) => a == null && b == null ? null : (a || 0) + (b || 0));\n'
                 '    const v = await Promise.all(ult.map((e) => Promise.all([pagina("e/" + pad(e.numero) + ".html"), conta("pdf-" + pad(e.numero))])));')
        t = t.replace(vecchio, nuovo)
        t = t.replace("// es. /Gommberg-Terminal-Daily/", "// es. /")
    if rel == ".github/workflows/sito.yml":   # il vecchio sito non è più un riferimento: il collaudo prova solo gommberg.com
        t = t.replace("https://gommberg.com/ https://paologom.github.io/Gommberg-Terminal-Daily/ --pagine 40", "https://gommberg.com/ --pagine 40")
        t = t.replace("collaudo = browser vero su ogni pagina, confronto con il vecchio sito", "collaudo = browser vero su ogni pagina di gommberg.com")
        t = t.replace("- name: Ogni pagina di gommberg.com contro il vecchio sito", "- name: Ogni pagina di gommberg.com")
    if rel == "README.md":
        t = t.replace("[paologom.github.io/Gommberg-Terminal-Daily]", "[gommberg.com]")
    return t


def main():
    scrivi = "--scrivi" in sys.argv
    cambi = {}
    for f in sorted(REPO.rglob("*")):
        rel = f.relative_to(REPO).as_posix()
        if rel == ".github/workflows/sito.yml" and f.is_file():
            t = f.read_text(encoding="utf-8")
            n = ritocchi_mirati(rel, t)
            if n != t:
                cambi[rel] = 1
                if scrivi:
                    f.write_text(n, encoding="utf-8")
            continue
        if (not f.is_file() or rel.startswith((".git/", "redazione/archivio/", "_")) or rel in SALTA
                or not rel.endswith(TESTO) or "__pycache__" in rel):
            continue
        t = f.read_text(encoding="utf-8", errors="strict")
        n = t
        for a, b in FORME:
            n = n.replace(a, b)
        n = ritocchi_mirati(rel, n)
        if n != t:
            cambi[rel] = sum(t.count(a) for a, _ in FORME)
            if scrivi:
                f.write_text(n, encoding="utf-8")
    # PROGETTO.md: solo la riga della tabella dei riferimenti, lo storico resta com'è
    p = REPO / "redazione/PROGETTO.md"
    t = p.read_text(encoding="utf-8")
    n = t.replace("| Sito pubblico (link da condividere) | https://paologom.github.io/Gommberg-Terminal-Daily/ |",
                  f"| Sito pubblico (link da condividere) | https://gommberg.com/ (dal {date.today():%d/%m/%Y}; prima paologom.github.io/Gommberg-Terminal-Daily, che ora reindirizza) |")
    if n != t:
        cambi["redazione/PROGETTO.md (tabella)"] = 1
        if scrivi:
            p.write_text(n, encoding="utf-8")
    for k, v in cambi.items():
        print(f"{v:4d}  {k}")
    resto = [f.relative_to(REPO).as_posix() for f in REPO.rglob("*") if f.is_file() and f.suffix in (".html", ".xml", ".js")
             and not f.relative_to(REPO).as_posix().startswith((".git/", "_", "redazione/archivio/"))
             and "Gommberg-Terminal-Daily" in f.read_text(encoding="utf-8", errors="replace")]
    print(f"{len(cambi)} file {'cambiati' if scrivi else 'da cambiare'}; pagine che nominano ancora il vecchio percorso: {resto if scrivi else '(dopo --scrivi)'}")


if __name__ == "__main__":
    main()
