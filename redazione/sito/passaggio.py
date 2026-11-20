#!/usr/bin/env python3
"""Il passaggio del sito da paologom.github.io/Gommberg-Terminal-Daily a gommberg.com (G-11). Si lancia UNA volta,
nel weekend del passaggio, sull'ultima versione del ramo principale; poi questo file si cancella (resta nello storico).

  python3 redazione/sito/passaggio.py           mostra cosa cambierebbe, senza scrivere (esce con 1 se qualcosa non torna)
  python3 redazione/sito/passaggio.py --scrivi  scrive, solo se tutti i ritocchi mirati riescono (tutto o niente)

Cosa fa: (1) ogni indirizzo assoluto del vecchio sito diventa gommberg.com, anche nella forma codificata dei link di
WhatsApp, nelle pagine, nel feed, nella mappa, nelle edizioni e nei due generatori (pagine.py, newsletter.py) e nel
modello delle email; (2) 404.html con il <base> alla radice; (3) "I numeri" somma per ogni edizione le visite contate
con il vecchio percorso e con il nuovo (GoatCounter conta il percorso, non il dominio); (4) README e tabella dei
riferimenti di PROGETTO.md, frase sull'hosting della privacy; (5) toglie da costruisci.py il ritocco della 404 e dal collaudo il confronto con il
vecchio sito, che non servono più. Non tocca lo storico (righe datate di PROGETTO.md, redazione/archivio/) né i riferimenti
al repository GitHub, che cambiano con G-12.
"""
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VECCHIO, NUOVO = "https://paologom.github.io/Gommberg-Terminal-Daily/", "https://gommberg.com/"
FORME = [(VECCHIO, NUOVO), (VECCHIO.replace("https://", "https%3A//"), NUOVO.replace("https://", "https%3A//")),
         (VECCHIO.replace(":", "%3A").replace("/", "%2F"), NUOVO.replace(":", "%3A").replace("/", "%2F")),
         (VECCHIO.replace("/", "\\/"), NUOVO.replace("/", "\\/"))]
SALTA = {"redazione/PROGETTO.md", "redazione/sito/passaggio.py", "redazione/sito/vecchio_indirizzo.py"}
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
        t = t.replace("https://gommberg.com/ https://gommberg.com/ --pagine 40", "https://gommberg.com/ --pagine 40")
        t = t.replace("collaudo = browser vero su ogni pagina, confronto con il vecchio sito", "collaudo = browser vero su ogni pagina di gommberg.com")
        t = t.replace("- name: Ogni pagina di gommberg.com contro il vecchio sito", "- name: Ogni pagina di gommberg.com")
    if rel == "redazione/sito/costruisci.py":   # il <base> della 404 è già alla radice: il ritocco non serve più
        t = t.replace("""    # 404.html si apre a qualunque profondità, quindi ha un <base> assoluto: qui il sito sta alla radice del dominio.
    # Dopo il passaggio a gommberg.com il file ha già <base href="/"> e questo ritocco non cambia nulla.
    p404 = uscita / "404.html"
    if p404.is_file():
        t = p404.read_text(encoding="utf-8")
        p404.write_text(BASE.sub('<base href="/">', t, count=1), encoding="utf-8")
""", "").replace("""BASE = re.compile(r'<base href="[^"]*">', re.I)
""", "")
    if rel == "README.md":
        t = t.replace("[paologom.github.io/Gommberg-Terminal-Daily]", "[gommberg.com]")
    if rel == "privacy.html":   # chi ospita il sito: ora Cloudflare (il vecchio indirizzo resta su GitHub, solo per reindirizzare)
        t = t.replace("Il sito è ospitato da GitHub, che come ogni servizio di hosting registra dati tecnici di connessione.",
                      "Il sito è ospitato da Cloudflare (Cloudflare, Inc., Stati Uniti), che come ogni servizio di hosting registra "
                      "dati tecnici di connessione; il vecchio indirizzo su GitHub serve solo a reindirizzare qui.")
    return t


def main():
    scrivi = "--scrivi" in sys.argv
    tracciati = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z"], capture_output=True, check=True).stdout
    nuovi, conti = {}, {}          # prima si calcola tutto, poi si scrive: mai un passaggio fatto a metà
    for rel in sorted(x for x in tracciati.decode("utf-8", "surrogateescape").split("\0") if x):
        f = REPO / rel
        if (not f.is_file() or f.is_symlink() or rel.startswith(("redazione/archivio/", "_")) or rel in SALTA
                or not rel.endswith(TESTO) or "__pycache__" in rel):
            continue
        t = f.read_text(encoding="utf-8")
        n = t
        for a, b in FORME:
            n = n.replace(a, b)
        n = ritocchi_mirati(rel, n)
        if n != t:
            nuovi[rel], conti[rel] = n, sum(t.count(a) for a, _ in FORME)
    # PROGETTO.md: solo la riga della tabella dei riferimenti, lo storico resta com'è
    rel = "redazione/PROGETTO.md"
    t = (REPO / rel).read_text(encoding="utf-8")
    n = t.replace("| Sito pubblico (link da condividere) | https://paologom.github.io/Gommberg-Terminal-Daily/ |",
                  f"| Sito pubblico (link da condividere) | https://gommberg.com/ (dal {date.today():%d/%m/%Y}; prima paologom.github.io/Gommberg-Terminal-Daily, che ora reindirizza) |")
    if n != t:
        nuovi[rel], conti[rel] = n, 1
    # i ritocchi mirati cercano righe precise: se un'altra modifica le ha cambiate, va detto e non si scrive nulla
    def dopo(f):
        return nuovi.get(f) or (REPO / f).read_text(encoding="utf-8")
    controlli = [("404.html", lambda x: '<base href="/">' in x, "il <base> della 404 non è alla radice"),
                 ("numeri.html", lambda x: 'const VECCHIO = "/Gommberg-Terminal-Daily/"' in x,
                  "I numeri non somma il vecchio percorso delle edizioni: la riga da ritoccare è cambiata, va adattata a mano"),
                 ("privacy.html", lambda x: "ospitato da GitHub" not in x, "la frase sull'hosting è cambiata, va adattata a mano"),
                 ("redazione/sito/costruisci.py", lambda x: "p404" not in x, "il ritocco della 404 è ancora in costruisci.py"),
                 (".github/workflows/sito.yml", lambda x: "paologom" not in x and "gommberg.com/ https://" not in x,
                  "il collaudo del workflow nomina ancora un secondo sito")]
    mancati = [f"{f}: {msg}" for f, ok, msg in controlli if not ok(dopo(f))]
    for k in nuovi:
        print(f"{conti[k]:4d}  {k}")
    for m in mancati:
        print("ATTENZIONE", m)
    if mancati:
        sys.exit("Niente scritto: prima va sistemato quanto sopra." if scrivi else 1)
    if scrivi:
        for k, n in nuovi.items():
            (REPO / k).write_text(n, encoding="utf-8")
    resto = [k for k in nuovi if k.endswith((".html", ".xml", ".js")) and "Gommberg-Terminal-Daily" in nuovi[k]]
    print(f"{len(nuovi)} file {'cambiati' if scrivi else 'da cambiare'}; pagine che nomineranno ancora il vecchio percorso "
          f"(solo numeri.html, voluto): {resto}")


if __name__ == "__main__":
    main()
