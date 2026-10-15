"""Controlli di scrittura v6 sul testo del PDF: righe "→", connettivi causali sospetti, sigle.
Uso: python3 controlli_testo.py <pdf> [--json uscita.json]
- Righe "→" (escluse quelle di rimando "→ pag. N"): massimo 5 nel PDF -> ERRORE se di più; AVVISO oltre 20 parole.
- Connettivi causali ("perché", "a causa di", "spinto da", "pesa", "trascina", "sulla scia di", "complice"...):
  AVVISO per ogni riga che li contiene senza "secondo": ammessi solo con scheda C in fatti.json e "secondo <testata>".
- Sigle (redazione/glossario.json, ovvio=false): AVVISO se compaiono ma non sono mai spiegate tra parentesi,
  o se sono spiegate più di una volta. Stampa anche l'elenco delle sigle spiegate (va in edizioni.json, campo glossario).
Esce con codice 1 solo per l'errore sulle righe "→"."""
import json, os, re, subprocess, sys

QUI = os.path.dirname(os.path.abspath(__file__))
MAX_FRECCE = 5
CONNETTIVI = [r"perch[ée]", r"a causa d", r"spint[oaie] da", r"\bpes[ao]\b", r"\bpesano\b", r"trascin", r"sulla scia d",
              r"\bcomplice\b", r"\bper effetto d", r"\bgrazie a\b", r"\bdopo che\b"]
ESENZIONI = re.compile(r"Perch[ée] conta|secondo |stima redazionale|di solito|in genere|tende a", re.I)


def testo(pdf, layout=False):
    a = ["pdftotext"] + (["-layout"] if layout else []) + [pdf, "-"]
    return subprocess.run(a, capture_output=True).stdout.decode("utf-8", "replace")


def frecce(t):
    righe = []
    flat = re.sub(r"\s+", " ", t)
    for m in re.finditer(r"→\s*([^→]{0,240})", flat):
        seg = m.group(1).strip()
        if not seg or re.match(r"pag\.?\s*\d", seg, re.I):
            continue  # rimando o intestazione di colonna
        frase = re.split(r"(?<=[.!?])\s", seg)[0]
        righe.append(frase)
    return righe


def connettivi(t_layout):
    sospetti = []
    for r in t_layout.split("\n"):
        r = " ".join(r.split())
        if not r or ESENZIONI.search(r):
            continue
        for c in CONNETTIVI:
            if re.search(c, r, re.I):
                sospetti.append(r[:110]); break
    return sospetti


def sigle(t):
    g = json.load(open(os.path.join(QUI, "glossario.json"), encoding="utf-8"))["voci"]
    flat = re.sub(r"\s+", " ", t)
    mai, doppie, spiegate = [], [], []
    for v in g:
        if v.get("ovvio"):
            continue
        nomi = [v["sigla"]] + v.get("varianti", [])
        pat = "|".join(re.escape(n) for n in nomi)
        occ = re.findall(rf"(?<![\w/])(?:{pat})(?![\w/])", flat)
        if not occ:
            continue
        spieg = len(re.findall(rf"(?<![\w/])(?:{pat})(?![\w/]) ?\((?=[^)]*\s)[^)]{{3,60}}\)", flat)) + \
            len(re.findall(rf"\([^()]{{0,40}}(?<![\w/])(?:{pat})(?![\w/])\)", flat))
        if spieg == 0:
            mai.append(v["sigla"])
        else:
            spiegate.append(v["sigla"])
            if spieg > 1:
                doppie.append(v["sigla"])
    return mai, doppie, spiegate


def main():
    pdf = sys.argv[1]
    t, tl = testo(pdf), testo(pdf, layout=True)
    fr = frecce(t)
    lunghe = [f for f in fr if len(f.split()) > 20]
    sos = connettivi(tl)
    mai, doppie, spiegate = sigle(t)
    print(f"Righe →: {len(fr)} (max {MAX_FRECCE}) | connettivi sospetti: {len(sos)} | sigle non spiegate: {len(mai)}")
    for f in lunghe[:2]:
        print(f"AVVISO: riga → oltre 20 parole: {f[:90]}")
    for s in sos[:4]:
        print(f"AVVISO: causa senza 'secondo <testata>'? {s}")
    if mai:
        print("AVVISO: sigle mai spiegate tra parentesi: " + ", ".join(mai)[:140])
    if doppie:
        print("AVVISO: sigle spiegate più di una volta: " + ", ".join(doppie)[:140])
    print("Sigle spiegate (campo glossario): " + (", ".join(spiegate) or "-")[:150])
    if "--json" in sys.argv:
        json.dump({"frecce": fr, "connettivi": sos, "sigle_mai_spiegate": mai, "sigle_doppie": doppie,
                   "glossario": spiegate}, open(sys.argv[sys.argv.index("--json") + 1], "w"), ensure_ascii=False, indent=1)
    if len(fr) > MAX_FRECCE:
        print(f"ERRORE: {len(fr)} righe → (massimo {MAX_FRECCE}): tieni solo quelle dove il perché non è ovvio")
        sys.exit(1)


if __name__ == "__main__":
    main()
