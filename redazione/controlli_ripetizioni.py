"""Controllo ripetizioni dentro l'edizione (AVVISO, non bloccante).
Uso: python3 controlli_ripetizioni.py <pdf | testo.txt> [--json uscita.json]
Divide il testo (pdftotext -layout) nelle sezioni segnate dai kicker (righe tutte maiuscole a margine sinistro)
e cerca cifre (%, pb, $, livelli con decimali) che compaiono in più sezioni di testo. Le sezioni di soli dati
(ticker, cruscotto, cross-asset, scommessa, fonti) non contano.
Punteggio = somma, per ogni cifra ripetuta, delle sezioni in più oltre la prima (0 = nessuna ripetizione).
Principio v6: un fatto ha una casa; pag. 1 titola e riassume, la pagina interna approfondisce senza ripetere le cifre."""
import collections, json, re, subprocess, sys

KICKER = re.compile(r"^([A-ZÀÈÉÌÒÙ0-9][A-ZÀÈÉÌÒÙ0-9 &'/.,:+|-]{2,})\s*$")
ESCLUSE = re.compile(r"^(TICKER|MERCATI|CRUSCOTTO|CROSS-ASSET|LA SCOMMESSA|SCOMMESSA|IL GRAN FINALE|FORECAST|NOTE|FONTI|"
                     r"PAROLE|PER CHI LEGGE|ERRATA|NELLE PAGINE INTERNE|TERMOMETRI)")
MESI = r"(GENNAIO|FEBBRAIO|MARZO|APRILE|MAGGIO|GIUGNO|LUGLIO|AGOSTO|SETTEMBRE|OTTOBRE|NOVEMBRE|DICEMBRE)"
NUM = re.compile(r"(?<![\d,.])[+-]?\d{1,3}(?:\.\d{3})*(?:,\d+)?(?:-\d+(?:,\d+)?)?\s?(?:%|pb|\$)")
LIV = re.compile(r"(?<![\d,.])\d{1,3}(?:\.\d{3})+,\d{1,2}(?![\d%])")  # livelli tipo 7.718,94


def testo_di(path):
    if path.lower().endswith(".pdf"):
        return subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True).stdout.decode("utf-8", "replace")
    return open(path, encoding="utf-8").read()


def sezioni(t):
    parti, nome, buf, pagina = {}, "TICKER", [], 1
    for riga in t.split("\n"):
        pagina += riga.count("\f")
        riga = riga.replace("\f", "")
        m = KICKER.match(riga) if riga and not riga[0].isspace() else None
        if m and sum(c.isalpha() for c in m.group(1)) >= 4:
            parti.setdefault(nome, []).append("\n".join(buf))
            k = re.sub(r"\s*\|\s*", " ", m.group(1)).strip()
            k = re.sub(r"\s+\d{1,2}(?:-\d{1,2})?\s+" + MESI + r".*$", "", k)  # toglie le date dai kicker
            nome, buf = k, []
            continue
        buf.append(riga)
    parti.setdefault(nome, []).append("\n".join(buf))
    return {k: "\n".join(v) for k, v in parti.items()}


def analizza(t):
    occ = collections.defaultdict(set)
    for sez, txt in sezioni(t).items():
        if ESCLUSE.match(sez):
            continue
        for n in NUM.findall(txt) + LIV.findall(txt):
            n = n.lstrip("+-").replace(" ", "")
            if n in ("0%", "0pb", "0$") or re.fullmatch(r"\d%", n):
                continue  # cifre troppo generiche
            occ[n].add(sez)
    rip = {n: sorted(s) for n, s in occ.items() if len(s) >= 2}
    punteggio = sum(len(s) - 1 for s in rip.values())
    return punteggio, rip


def main():
    t = testo_di(sys.argv[1])
    punteggio, rip = analizza(t)
    peggiori = sorted(rip.items(), key=lambda x: (-len(x[1]), x[0]))
    print(f"Ripetizioni: punteggio {punteggio} ({len(rip)} cifre in 2+ sezioni)")
    for n, s in peggiori[:5]:
        print(f"AVVISO: {n} in {len(s)} sezioni: {', '.join(s)}"[:150])
    if "--json" in sys.argv:
        json.dump({"punteggio": punteggio, "ripetute": rip}, open(sys.argv[sys.argv.index("--json") + 1], "w"),
                  ensure_ascii=False, indent=1)
    # BLOCCANTE: una cifra "distintiva" (|valore| >= 1, oppure 2 decimali, oppure un livello) in 3+ sezioni.
    # Le cifre piccole (0,3%, 0,4%...) coincidono spesso per caso tra fatti diversi: restano avvisi.
    def distintiva(n):
        import re as _r
        m = _r.search(r"-?\d[\d.]*(?:,(\d+))?", n)
        if not m:
            return False
        dec = m.group(1) or ""
        try:
            v = abs(float(m.group(0).replace(".", "").replace(",", ".")))
        except ValueError:
            return False
        return v >= 1 or len(dec) >= 2
    gravi = [(n, s) for n, s in peggiori if len(s) >= 3 and distintiva(n)]
    for n, s in gravi:
        print(f"ERRORE: {n} in {len(s)} sezioni ({', '.join(s)}): una sola casa per cifra - nelle altre "
              "sezioni rimanda (\"→ pag. N\") o parla del fatto senza la cifra"[:220])
    sys.exit(1 if gravi else 0)


if __name__ == "__main__":
    main()
