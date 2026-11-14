"""Controlli di scrittura v6 sul testo del PDF: righe "→", connettivi causali sospetti, sigle.
Uso: python3 controlli_testo.py <pdf> [--json uscita.json]
     python3 controlli_testo.py --stile <edizione.py>   (solo §3.4 sui testi di C, senza PDF: prima del rendering)
- Righe "→" (escluse quelle di rimando "→ pag. N"): massimo 5 nel PDF -> ERRORE se di più; AVVISO oltre 20 parole.
- Connettivi causali ("perché", "a causa di", "spinto da", "pesa", "trascina", "sulla scia di", "complice"...):
  AVVISO per ogni riga che li contiene senza fonte: ammessi solo con scheda C in fatti.json e la fonte in coda "(Testata)"
  (o "secondo X" per stime, opinioni, indiscrezioni).
- Sigle (redazione/glossario.json, ovvio=false): AVVISO se compaiono ma non sono mai spiegate tra parentesi,
  o se sono spiegate più di una volta. Stampa anche l'elenco delle sigle spiegate (va in edizioni.json, campo glossario).
BLOCCANTI (codice 1): più di 5 righe "→"; una riga "→" oltre 20 parole; una sigla non ovvia la cui prima occorrenza
(dopo il ticker) non è spiegata tra parentesi; un connettivo causale in una frase con un movimento di mercato senza
la fonte "(Testata)" nella frase o nel suo paragrafo (due frasi prima o dopo). Più di 15 fonti tra parentesi sono
un errore (ISTRUZIONI §3.5); le sigle spiegate due volte sono solo un avviso.
Ritmo (§3.4): una frase oltre 30 parole è un errore; 4 frasi di fila con media sotto 12 parole (telegramma) un avviso.
Il ritmo si misura sui campi dell'edizione (--edizione <edizione.py>); dal solo PDF è una stima e vale come avviso."""
import json, os, re, subprocess, sys

QUI = os.path.dirname(os.path.abspath(__file__))
MAX_FRECCE = 5
CONNETTIVI = [r"perch[ée]", r"a causa d", r"spint[oaie] da", r"\bpesa\b", r"\bpesano\b", r"trascin", r"sulla scia d",
              r"\bcomplice\b", r"\bper effetto d", r"\bgrazie a\b", r"\bdopo che\b"]
# La voce della redazione ("per noi", "leggiamo") vale come lettura dichiarata: niente etichette né parentesi (v7.7).
VOCE_RED = r"per noi|la nostra lettura|leggiamo|a nostro (?:giudizio|avviso)|lettura della redazione"
ESENZIONI = re.compile(r"Perch[ée] conta|Il perch[ée] |secondo |stima redazionale|di solito|in genere|tende a|" + VOCE_RED, re.I)
INGLESE = re.compile(r"\b(?:the|of|and|is|are|they're|it's|we|our|some|will|way|total|with|for|to)\b", re.I)

def _fonte_tra_parentesi():
    """Regex dell'attribuzione in coda: "(Reuters)", "(Yahoo Finance, FIRSTonline)", "(dati BLS)"."""
    nomi = json.load(open(os.path.join(QUI, "fonti.json"), encoding="utf-8")).get("nomi", [])
    alt = "|".join(sorted((re.escape(n) for n in nomi), key=len, reverse=True))
    return re.compile(r"\([^()]{0,30}\b(?:" + alt + r")\b[^()]{0,40}\)")


FONTE_PAR = _fonte_tra_parentesi()



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
    """Frasi con un connettivo causale e un movimento di mercato, senza fonte "(Testata)" né forma M/S."""
    sospetti = []
    ff = frasi(t)
    for i, f in enumerate(ff):
        # una fonte in coda al paragrafo copre il paragrafo: basta una "(Testata)" entro due frasi (ISTRUZIONI §2)
        vicine = " ".join(ff[max(0, i - 2):i + 3])
        if ESENZIONI.search(f) or FONTE_PAR.search(vicine) or not MOVIMENTO.search(f):
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


MAX_PAROLE, MEDIA, FILA = 30, 12, 4   # §3.4: periodo da spezzare; telegramma = FILA frasi di fila con media sotto MEDIA parole


def _prosa(f):
    """Il frammento se è prosa; None per intestazioni, tabelle o colonne unite dall'estrazione del PDF."""
    if not f:
        return None
    f = re.sub(r"^(?:IL QUADRO|PERCH[ÉE]|E QUINDI|DA GUARDARE|IL NUMERO)\s+", "", f.strip())
    if re.search(r"\||[▲▼■→]|\b[A-ZÀ-Ú]{3,}(?: [A-ZÀ-Ú]{3,})+\b|\d{2}/\d{2}.*\d{2}/\d{2}|^(?:Fonti?\b|Notizie e conti|Titolo Chi è)", f):
        return None
    if sum(1 for w in f.split() if re.fullmatch(r"[+-]?[\d.,]+%?", w)) >= 6:
        return None
    return f


def ritmo(ff):
    """ff = frasi in ordine (None interrompe la fila). Torna (frasi oltre MAX_PAROLE, [(n, testo) dei telegrammi]):
    telegramma = almeno FILA frasi consecutive la cui lunghezza media resta sotto MEDIA parole."""
    lunghe = [f for f in ff if f and len(f.split()) > MAX_PAROLE]
    tele, fila = [], []
    for f in ff + [None]:
        if f and re.search(r"[a-zà-ù]{3}", f):
            fila.append(f); continue
        n = len(fila)
        if n >= FILA:   # la finestra di FILA frasi più telegrafica decide
            if min(sum(len(x.split()) for x in fila[i:i + FILA]) for i in range(n - FILA + 1)) < MEDIA * FILA:
                tele.append((n, " ".join(fila)))
        fila = []
    return lunghe, tele


def ritmo_campi(ed):
    """§3.4 sui testi del dizionario C (ogni campo è un paragrafo), con le riscritture del desk già applicate.
    È la misura esatta: sul testo estratto dal PDF titoli, elenchi e tabelle si fondono in "frasi" che non esistono."""
    sys.path.insert(0, QUI)
    import desk
    qui = os.getcwd()
    C = desk._carica(os.path.abspath(ed))
    try:
        desk.applica(C, os.path.dirname(os.path.abspath(ed)))
    except Exception:  # noqa: BLE001
        pass
    os.chdir(qui)
    errori, avvisi = [], []
    for campo, t in desk.campi(C).items():
        t = re.sub(r"<[^>]+>|\[\[\w+\]\]", "", str(t))
        lunghe, tele = ritmo([f.strip() for f in re.split(r"(?<=[.!?])\s+", t) if f.strip()])
        errori += [f"{campo}: frase oltre {MAX_PAROLE} parole ({len(g.split())}): spezzala dove cambia l'idea (§3.4): {g[:70]}"
                   for g in lunghe]
        avvisi += [f"{campo}: telegramma, {n} frasi staccate: legale tra loro (e, ma, mentre...) (§3.4): {g[:60]}"
                   for n, g in tele]
    return errori, avvisi


def stile(ed):
    """Solo il ritmo, prima del PDF: python3 controlli_testo.py --stile <edizione.py>"""
    errori, avvisi = ritmo_campi(ed)
    for e in errori:
        print("ERRORE: " + e[:155])
    for a in avvisi:
        print("AVVISO: " + a[:155])
    print(f"Stile (§3.4): {len(errori)} errori, {len(avvisi)} avvisi")
    sys.exit(1 if errori else 0)


def main():
    if sys.argv[1] == "--stile":
        return stile(sys.argv[2])
    pdf = sys.argv[1]
    t, tl = testo(pdf), testo(pdf, layout=True)
    fr = frecce(t)
    lunghe = [f for f in fr if len(f.split()) > 20]
    sos = connettivi(t)
    mai, doppie, spiegate = sigle(t)
    n_fonti = len(FONTE_PAR.findall(re.sub(r"\s+", " ", t.rsplit("Fonti", 1)[0])))
    print(f"Righe →: {len(fr)} (max {MAX_FRECCE}) | cause senza fonte: {len(sos)} | sigle non spiegate: {len(mai)}")
    errori = []
    if len(fr) > MAX_FRECCE:
        errori.append(f"{len(fr)} righe → (massimo {MAX_FRECCE}): tieni solo quelle dove il perché non è ovvio")
    errori += [f"riga → oltre 20 parole: {f[:100]}" for f in lunghe]
    errori += [f"causa senza fonte '(Testata)' in coda: {x}" for x in sos]
    errori += [f"sigla non spiegata alla prima occorrenza: {x}" for x in mai]
    # Stile delle fonti (§3): la fonte di un fatto firma in coda "(Testata)"; "secondo X" solo fuori parentesi, per stime,
    # opinioni e citazioni. "(secondo X)" mescola le due forme e toglie protagonismo alla redazione.
    piatto = re.sub(r"\s+", " ", t)
    errori += [f"fonte tra parentesi con 'secondo': scrivi \"({m.group(1).strip()})\" ('secondo X' solo per stime e citazioni, fuori parentesi)"
               for m in re.finditer(r"\(secondo ([^)]{2,40})\)", piatto)]
    errori += ["etichetta 'stima redazionale' vietata: scrivi la frase senza etichetta" for _ in re.finditer(r"stim[ae] redazional", piatto, re.I)]
    # v7.7: meno parentesi, voce più nostra. Etichetta tra parentesi, doppia attribuzione e citazioni in inglese.
    errori += ["etichetta '(lettura della redazione)' vietata: dilla con la nostra voce ('per noi', 'leggiamo'), senza parentesi"
               for _ in re.finditer(r"\(\s*lettura della redazione", piatto, re.I)]
    errori += [f"doppia attribuzione '{m.group(0)[:50]}': chi parla va nella frase ('secondo X'), tra parentesi una sola testata, senza 'via'"
               for m in re.finditer(r"\([^()]{0,40}\bvia\b[^()]{0,40}\)", piatto)]
    # v7.8: le citazioni in inglese restano in originale (i lettori lo leggono), ma brevi: oltre 15 parole è un avviso.
    avvisi = [f"citazione in inglese oltre 15 parole: accorciala «{m.group(1)[:40]}»"
              for m in re.finditer(r"«([^»]{3,300})»", piatto)
              if len(INGLESE.findall(m.group(1))) >= 2 and len(m.group(1).split()) > 15]
    # v8.6 (§3.4): ritmo. Errore solo il periodo oltre 30 parole; avviso il telegramma (4 frasi di fila, media sotto 12 parole).
    # Si misura sui campi dell'edizione (--edizione <edizione.py>, lo passa controlli_tutti.sh): è esatto. Senza il file
    # dell'edizione resta la stima dal PDF, che vale solo come avviso: lì titolo e sommario, i punti di un elenco o una
    # tabella intera si fondono in una "frase" (collaudo del 14/11: 5-6 falsi errori in ognuna delle edizioni #022-#025).
    ed = sys.argv[sys.argv.index("--edizione") + 1] if "--edizione" in sys.argv else None
    if ed and os.path.exists(ed):
        e_ritmo, a_ritmo = ritmo_campi(ed)
        errori += e_ritmo[:6]
        avvisi += a_ritmo[:3]
    else:
        corpo = piatto.split("TOP STORY", 1)[-1]
        lunghe_prosa, telegrammi = ritmo([_prosa(f) for f in re.split(r"(?<=[.!?])\s+", corpo)])
        avvisi += [f"forse una frase oltre {MAX_PAROLE} parole ({len(g.split())}, stima dal PDF): {g[:80]}" for g in lunghe_prosa[:3]]
        avvisi += [f"telegramma, {n} frasi staccate: legale tra loro (e, ma, mentre...) (§3.4): {g[:70]}"
                   for n, g in telegrammi[:3]]
    # v7.8 (§9.4): lessico di casa (glossario.json, "lessico"): un concetto, un nome.
    lex = json.load(open(os.path.join(QUI, "glossario.json"), encoding="utf-8")).get("lessico", {}).get("voci", [])
    for v in lex:
        trovate = [m.group(0) for rx in v.get("evita", []) for m in re.finditer(rx, piatto, re.I)]
        if len(trovate) > v.get("max", 0):
            avvisi.append(f"lessico: \"{trovate[0]}\" ({len(trovate)} volte): scrivi \"{v['termine']}\"")
    for e in errori[:6]:
        print("ERRORE: " + e[:155])
    for a in avvisi:
        print("AVVISO: " + a[:155])
    if doppie:
        print("AVVISO: sigle spiegate più di una volta: " + ", ".join(doppie)[:140])
    if n_fonti > 15:
        print(f"ERRORE: {n_fonti} fonti tra parentesi nel testo (massimo 15): togli quelle di dati, eventi e notizie "
              "confermate da 2+ testate (stanno nella riga Fonti); restano cause, notizie e dati da fonte singola")
    print("Sigle spiegate (campo glossario): " + (", ".join(spiegate) or "-")[:150])
    if "--json" in sys.argv:
        json.dump({"frecce": fr, "connettivi": sos, "sigle_mai_spiegate": mai, "sigle_doppie": doppie,
                   "glossario": spiegate, "errori": errori},
                  open(sys.argv[sys.argv.index("--json") + 1], "w"), ensure_ascii=False, indent=1)
    if errori or n_fonti > 15:
        sys.exit(1)


if __name__ == "__main__":
    main()
