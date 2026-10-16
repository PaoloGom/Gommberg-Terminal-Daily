"""Controlli di scrittura v6 sul testo del PDF: righe "→", connettivi causali sospetti, sigle.
Uso: python3 controlli_testo.py <pdf> [--json uscita.json]
- Righe "→" (escluse quelle di rimando "→ pag. N"): massimo 5 nel PDF -> ERRORE se di più; AVVISO oltre 20 parole.
- Connettivi causali ("perché", "a causa di", "spinto da", "pesa", "trascina", "sulla scia di", "complice"...):
  AVVISO per ogni riga che li contiene senza "secondo": ammessi solo con scheda C in fatti.json e "secondo <testata>".
- Sigle (redazione/glossario.json, ovvio=false): AVVISO se compaiono ma non sono mai spiegate tra parentesi,
  o se sono spiegate più di una volta. Stampa anche l'elenco delle sigle spiegate (va in edizioni.json, campo glossario).
BLOCCANTI (codice 1): più di 5 righe "→"; una riga "→" oltre 20 parole; una sigla non ovvia la cui prima occorrenza
(dopo il ticker) non è spiegata tra parentesi; un connettivo causale in una frase con un movimento di mercato senza
"secondo <testata>". Le sigle spiegate due volte sono solo un avviso."""
import json, os, re, subprocess, sys

QUI = os.path.dirname(os.path.abspath(__file__))
MAX_FRECCE = 5
CONNETTIVI = [r"perch[ée]", r"a causa d", r"spint[oaie] da", r"\bpesa\b", r"\bpesano\b", r"trascin", r"sulla scia d",
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
        if not seg or re.match(r"pag\.?\s*\d|(Lun|Mar|Mer|Gio|Ven|Sab|Dom) \d", seg, re.I):
            continue  # rimando o intestazione di colonna
        frase = re.split(r"(?<=[.!?])\s", seg)[0]
        righe.append(frase)
    return righe


MOVIMENTO = re.compile(r"[+-]\d|\b(sal[ei]|salgono|scend[eo]|scendono|cal[ai]|calano|cede|cedono|guadagn|perd[eo]|"
                       r"rialz|ribass|vendite|acquisti|chiude|chiusura|rimbalz|crolla|corre|tonfo)", re.I)


def frasi(t):
    flat = re.sub(r"\s+", " ", t)
    return [f.strip() for f in re.split(r"(?<=[.;!?])\s+", flat) if f.strip()]


def connettivi(t):
    """Frasi con un connettivo causale e un movimento di mercato, senza 'secondo <testata>' né forma M/S."""
    sospetti = []
    for f in frasi(t):
        if ESENZIONI.search(f) or not MOVIMENTO.search(f):
            continue
        for c in CONNETTIVI:
            if re.search(c, f, re.I):
                sospetti.append(f[:130]); break
    return sospetti


def sigle(t):
    """Prima occorrenza (dopo il ticker, cioè dopo 'TOP STORY') di ogni sigla non ovvia: deve avere la parentesi."""
    g = json.load(open(os.path.join(QUI, "glossario.json"), encoding="utf-8"))["voci"]
    flat = re.sub(r"\s+", " ", t)
    m = re.search(r"TOP STORY", flat)
    corpo = flat[m.end():] if m else flat
    mai, doppie, spiegate = [], [], []
    for v in g:
        if v.get("ovvio"):
            continue
        nomi = [v["sigla"]] + v.get("varianti", [])
        pat = "|".join(re.escape(n) for n in nomi)
        rx = re.compile(rf"(?<![\w/])(?:{pat})(?![\w/])")
        prima = rx.search(corpo)
        if not prima:
            continue
        dopo = corpo[prima.end():prima.end() + 70]
        prima_ok = bool(re.match(r"(?: [\w/-]+){0,2} ?\((?=[^)]*\s)[^)]{3,60}\)", dopo)) or \
            bool(re.search(r"\([^()]{0,40}$", corpo[max(0, prima.start() - 45):prima.start()]))
        spieg = len(re.findall(rf"(?<![\w/])(?:{pat})(?![\w/]) ?\((?=[^)]*\s)[^)]{{3,60}}\)", corpo))
        if not prima_ok:
            mai.append(f"{v['sigla']} ({corpo[max(0, prima.start() - 25):prima.end() + 15].strip()})")
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
    sos = connettivi(t)
    mai, doppie, spiegate = sigle(t)
    print(f"Righe →: {len(fr)} (max {MAX_FRECCE}) | cause senza fonte: {len(sos)} | sigle non spiegate: {len(mai)}")
    errori = []
    if len(fr) > MAX_FRECCE:
        errori.append(f"{len(fr)} righe → (massimo {MAX_FRECCE}): tieni solo quelle dove il perché non è ovvio")
    errori += [f"riga → oltre 20 parole: {f[:100]}" for f in lunghe]
    errori += [f"causa senza 'secondo <testata>': {x}" for x in sos]
    errori += [f"sigla non spiegata alla prima occorrenza: {x}" for x in mai]
    for e in errori[:6]:
        print("ERRORE: " + e[:155])
    if doppie:
        print("AVVISO: sigle spiegate più di una volta: " + ", ".join(doppie)[:140])
    print("Sigle spiegate (campo glossario): " + (", ".join(spiegate) or "-")[:150])
    if "--json" in sys.argv:
        json.dump({"frecce": fr, "connettivi": sos, "sigle_mai_spiegate": mai, "sigle_doppie": doppie,
                   "glossario": spiegate, "errori": errori},
                  open(sys.argv[sys.argv.index("--json") + 1], "w"), ensure_ascii=False, indent=1)
    if errori:
        sys.exit(1)


if __name__ == "__main__":
    main()
