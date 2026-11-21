"""Controlli di scrittura v6 sul testo del PDF: righe "→", connettivi causali sospetti, sigle.
Uso: python3 controlli_testo.py <pdf> [--json uscita.json]
     python3 controlli_testo.py --stile <edizione.py>   (solo §3.4 sui testi di C, senza PDF: prima del rendering)
- Righe "→" (escluse quelle di rimando "→ pag. N"): massimo 5 nel PDF -> ERRORE se di più; AVVISO oltre 20 parole.
- Connettivi causali ("perché", "a causa di", "spinto da", "pesa", "trascina", "sulla scia di", "complice"...) in una
  frase con un movimento di mercato: ERRORE se nel paragrafo non c'è chi dà quella causa (una testata o un nome detti nella
  frase, "secondo X"), né la nostra lettura dichiarata (una volta copre il paragrafo), né la forma di tendenza.
- Fonti (ISTRUZIONI §3.5): nel testo non si dice da dove viene un fatto, le testate stanno nella riga Fonti del pezzo.
  Una testata tra parentesi ("(Reuters)", "(Kitco e AFP)") è un ERRORE ovunque, tabelle comprese; resta solo accanto a un
  livello del mattino, con il suo orario ("(Milano Finanza, 07:40)"). Le testate si riconoscono da fonti.json e dalle
  righe Fonti dell'edizione stessa: una testata nuova vale dal giorno in cui la si usa.
- Sigle (redazione/glossario.json, ovvio=false): alla prima occorrenza (dopo il ticker) la cosa è detta in parole nella
  stessa frase (le radici di "breve" e di "parole"), altrimenti ERRORE. La definizione tra parentesi dopo la sigla passa
  ma è un AVVISO (§3.4: si dice dentro la frase); detta due volte nella stessa frase, in parole e tra parentesi, è un
  ERRORE. Stampa anche l'elenco delle sigle spiegate (va in edizioni.json, campo glossario).
- Lessico di casa (glossario.json, "lessico"): avviso, errore per le voci con "blocca" (termini che restano in inglese,
  calchi).
BLOCCANTI (codice 1): gli ERRORI qui sopra; più di 5 righe "→"; una riga "→" oltre 20 parole.
Ritmo (§3.4): una frase oltre 30 parole è un errore; 4 frasi di fila con media sotto 12 parole (telegramma) un avviso.
Il ritmo si misura sui campi dell'edizione (--edizione <edizione.py>); dal solo PDF è una stima e vale come avviso."""
import json, os, re, subprocess, sys

QUI = os.path.dirname(os.path.abspath(__file__))
MAX_FRECCE = 5
CONNETTIVI = [r"perch[ée]", r"a causa d", r"spint[oaie] da", r"\bpesa\b", r"\bpesano\b", r"trascin", r"sulla scia d",
              r"\bcomplice\b", r"\bper effetto d", r"\bgrazie a\b", r"\bdopo che\b"]
# La voce della redazione ("per noi", "leggiamo") vale come lettura dichiarata: niente etichette né parentesi (v7.7).
# Dichiarata una volta copre il suo paragrafo, come una fonte tra parentesi: non si ripete a ogni frase (G-36: nelle
# edizioni #026-#030 "per noi" era salito a 4 volte ogni 1.000 parole, sempre con le stesse due parole: solo 3 su 41
# erano ripetizioni nello stesso paragrafo, quindi conta di più poterla dire in più modi). La tendenza di un meccanismo
# resta nella frase che lo enuncia, e anche lei si può dire in più modi.
VOCE_RED = r"per noi|secondo noi|la nostra lettura|leggiamo|crediamo|a nostro (?:giudizio|avviso|parere)|lettura della redazione"
VOCE = re.compile(VOCE_RED, re.I)
TENDENZA = r"di solito|in genere|tend(?:e|ono) a|spesso|quasi sempre|di norma"
# L'ultima colonna dell'agenda ("Sopra: ... Sotto: ...") è una tendenza per intestazione ("Come può muovere i mercati, di
# solito"): le sue celle non devono ripeterlo una per una (nelle edizioni #026-#030 erano 28 "di solito" nella sola pag. 5).
AGENDA = r"\bSopra(?: \([^)]{0,30}\))?:|\bSotto(?: \([^)]{0,30}\))?:"
ESENZIONI = re.compile(r"Perch[ée] conta|Il perch[ée] |secondo |stima redazionale|" + AGENDA + "|" + TENDENZA + "|" + VOCE_RED, re.I)
INGLESE = re.compile(r"\b(?:the|of|and|is|are|they're|it's|we|our|some|will|way|total|with|for|to)\b", re.I)

ORARIO = re.compile(r"\b\d{1,2}[:.]\d{2}\b")
_GLOSS = json.load(open(os.path.join(QUI, "glossario.json"), encoding="utf-8"))["voci"]
SIGLE = {n for v in _GLOSS for n in [v["sigla"]] + v.get("varianti", [])}
# Testate note: l'elenco di fonti.json. Le sigle del glossario che sono anche fonti (Fed, BCE, SEC, BoJ...) tra parentesi
# sono quasi sempre la sigla accostata al nome ("la Banca del Giappone (BoJ)"): da sole non fanno una fonte tra parentesi.
NOMI_BASE = [n for n in json.load(open(os.path.join(QUI, "fonti.json"), encoding="utf-8")).get("nomi", []) if n not in SIGLE]
NOMI = list(NOMI_BASE)          # main() aggiunge le testate scritte nelle righe Fonti dell'edizione


def nomi_da_righe(righe):
    """Le testate scritte in una riga Fonti ("Fonti: Kitco, Il Sole 24 Ore; chiusure dell'oro future (FMP)"): i pezzi
    che cominciano con una maiuscola o hanno una grafia da testata (investingLive, dpa-AFX, Money.it), fino a 4 parole."""
    out = []
    for r in righe:
        for pezzo in re.split(r"[,;:()]|\s+e\s+|\s+via\s+", re.sub(r"<[^>]+>", "", str(r))):
            x = pezzo.strip(" .")
            if 2 <= len(x) <= 30 and len(x.split()) <= 4 and re.match(r"[A-ZÀ-Ú]|[a-z]+[A-Z.&-]\w", x) \
                    and x not in SIGLE and x not in ("Fonti", "Fonte") and x not in out:
                out.append(x)
    return out


def _alt(nomi):
    return "|".join(sorted((re.escape(n) for n in nomi), key=len, reverse=True))


def nome_fonte(nomi=None):
    """Regex di una testata nominata nel testo (non conta dove: nella frase o tra parentesi)."""
    return re.compile(r"(?<![\w/])(?:" + _alt(nomi or NOMI) + r")(?![\w/])")


def fonti_tra_parentesi(t, nomi=None):
    """Le parentesi che sono solo un'attribuzione: "(Reuters)", "(Kitco e AFP)", "(dati BLS)". Con un orario dentro
    ("(Milano Finanza, 07:40)") è la fonte di un livello del mattino e resta. Una parentesi che dice anche altro
    ("(BoJ, la banca centrale giapponese)", "(+25% per Reuters)") non è un'attribuzione."""
    nome, sigla = nome_fonte(nomi), re.compile(r"(?<![\w/])(?:" + _alt(SIGLE) + r")(?![\w/])")
    out = []
    for m in re.finditer(r"\(([^()]{2,70})\)", t):
        dentro = m.group(1)
        senza_sigle = sigla.sub("", dentro)          # "(CME FedWatch)" è una sigla accostata, non la testata CME
        if ORARIO.search(dentro) or not nome.search(senza_sigle):
            continue
        resto = nome.sub("", senza_sigle)
        if not re.sub(r"\b(?:dati|fonte|fonti|e|ed|via|del|della|dei|di)\b|[\s,;/]", "", resto):
            out.append(m.group(0))
    return out


def per_testata(t, nomi=None):
    """Quante volte ogni testata è scritta tra parentesi, come sola attribuzione, nel testo t: {"Reuters": 3, "AP": 1}."""
    conta, nome = {}, nome_fonte(nomi)
    for par in fonti_tra_parentesi(t, nomi):
        for n in dict.fromkeys(nome.findall(par)):
            conta[n] = conta.get(n, 0) + 1
    return conta


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


def connettivi(t, coperti=()):
    """Frasi con un connettivo causale e un movimento di mercato, senza chi dà la causa né forma M/S.
    coperti = i paragrafi dell'edizione che nominano chi dà la causa o dichiarano la nostra lettura: valgono per tutte
    le loro frasi."""
    sospetti = []
    ff = frasi(t)
    nome = nome_fonte()
    for i, f in enumerate(ff):
        if any(f[:50] in c for c in coperti) or f.rstrip().endswith("?"):   # una domanda non afferma una causa
            continue
        # chi dà la causa, nominato entro due frasi, copre il paragrafo ("per gli operatori sentiti da X", "secondo X");
        # lo stesso vale per la lettura dichiarata (§3.5)
        vicine = " ".join(ff[max(0, i - 2):i + 3])
        if ESENZIONI.search(f) or nome.search(vicine) or VOCE.search(vicine) or not MOVIMENTO.search(f):
            continue
        for c in CONNETTIVI:
            if re.search(c, f, re.I):
                sospetti.append(f[:130]); break
    return sospetti


def coperti_da(campi):
    """I paragrafi dell'edizione che coprono le loro cause: nominano chi le dà o dichiarano la nostra lettura."""
    nome = nome_fonte()
    return [c for c in campi.values() if nome.search(c) or VOCE.search(c)]


def _etichette():
    """Le parentesi delle etichette che il codice scrive nel nastro e nelle tabelle di pag. 5 ("VIX (volatilità attesa)")."""
    try:
        sys.path.insert(0, QUI)
        import numeri
        voci = [e[0] for e in numeri.TICKER] + [e[0] for _, gruppo in numeri.CRUSCOTTO + numeri.CROSS for e in gruppo]
        return {m for v in voci for m in re.findall(r"\(([^)]+)\)", v)}
    except Exception:  # noqa: BLE001
        return set()


ETICHETTE = _etichette()
_VUOTE = {"della", "delle", "dello", "degli", "sulle", "sugli", "sulla", "nelle", "negli", "dalla", "dalle", "contro",
          "misura", "prima", "sopra", "sotto"}


def _radici(testo, extra=()):
    """Le radici con cui si riconosce una cosa detta in parole: le parole piene del testo, tagliate a 6 lettere."""
    parole = [w for w in re.findall(r"[a-zà-ù]{5,}", testo.lower()) if w not in _VUOTE] + [x.lower() for x in extra]
    return {w[:6] for w in parole}


def sigle(t):
    """Prima occorrenza (dopo il ticker, cioè dopo 'TOP STORY') di ogni sigla non ovvia: la cosa deve essere detta in
    parole nella stessa frase. Torna (mai, doppie, spiegate, tra_parentesi, due_volte):
    mai = nessuna parola che la dica; doppie = definita tra parentesi più di una volta nel numero; spiegate = l'elenco per
    edizioni.json; tra_parentesi = la sigla seguita dalla sua definizione tra parentesi; due_volte = detta in parole e
    ridetta tra parentesi nella stessa frase."""
    flat = re.sub(r"\s+", " ", t)
    m = re.search(r"TOP STORY", flat)
    corpo = flat[m.end():] if m else flat
    mai, doppie, spiegate, tra_parentesi, due_volte = [], [], [], [], []
    for v in _GLOSS:
        if v.get("ovvio"):
            continue
        nomi = [v["sigla"]] + v.get("varianti", [])
        pat = "|".join(re.escape(n) for n in nomi)
        rx = re.compile(rf"(?<![\w/])(?:{pat})(?![\w/])")
        prima = rx.search(corpo)
        if not prima:
            continue
        radici = _radici(v.get("breve", ""), v.get("parole", []))
        avanti, dietro = corpo[prima.end():prima.end() + 110], corpo[max(0, prima.start() - 110):prima.start()]
        # la frase della sigla: indietro fino al punto fermo, avanti fino al punto fermo
        frase_prima = re.split(r"(?<=[.!?])\s", dietro)[-1]
        gloss = re.match(r"(?: [\w/-]+){0,2} ?\((?=[^)]*\s)([^)]{3,60})\)", avanti)
        frase_dopo = re.split(r"(?<=[.!?])\s", avanti[gloss.end():] if gloss else avanti)[0]
        in_parole = any(w.startswith(r) for r in radici for w in re.findall(r"[a-zà-ù]+", (frase_prima + " " + frase_dopo).lower()))
        # la sigla accostata al nome ("l'Agenzia internazionale dell'energia (AIE)") sta lei tra parentesi
        accostata = bool(re.search(r"\([^()]{0,40}$", dietro))
        spieg = len(re.findall(rf"(?<![\w/])(?:{pat})(?![\w/]) ?\((?=[^)]*\s)[^)]{{3,60}}\)", corpo))
        dove = corpo[max(0, prima.start() - 25):prima.end() + 15].strip()
        if not (gloss or in_parole or accostata):
            mai.append(f"{v['sigla']} ({dove})")
            continue
        spiegate.append(v["sigla"])
        if gloss and gloss.group(1) not in ETICHETTE:
            tra_parentesi.append(v["sigla"])
            dette = _radici(gloss.group(1))
            if dette and sum(1 for r in dette if r in frase_prima.lower()) * 2 >= len(dette):
                due_volte.append(f"{v['sigla']} ({dove})")
        if spieg > 1:
            doppie.append(v["sigla"])
    return mai, doppie, spiegate, tra_parentesi, due_volte


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


def edizione(ed):
    """Il dizionario C dell'edizione, con le riscritture del desk già applicate."""
    sys.path.insert(0, QUI)
    import desk
    qui = os.getcwd()
    C = desk._carica(os.path.abspath(ed))
    try:
        desk.applica(C, os.path.dirname(os.path.abspath(ed)))
    except Exception:  # noqa: BLE001
        pass
    os.chdir(qui)
    return C


def _pulito(t):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>|\[\[\w+\]\]", "", str(t)))


def paragrafi(ed, C=None):
    """I testi che il desk può riscrivere (ogni campo è un paragrafo): {campo: testo}."""
    import desk
    return {campo: _pulito(t) for campo, t in desk.campi(C or edizione(ed)).items()}


RIGHE_FONTI = ("fonte", "fonti", "fonte_sx", "fonte_dx")
# ciò che scrive il codice (nastro e tabelle di pag. 5, numeri.py) e i livelli del mattino, che portano orario e fonte
NON_REDAZIONE = ("ticker", "cruscotto", "cruscotto_nota", "cross", "cross_data", "cross_nota", "stamattina", "file", "chiave")


def testi(C):
    """Ciò che la redazione scrive e finisce in pagina, tabelle e riquadri compresi: {dove: testo}. Restano fuori le righe
    Fonti, le tabelle che calcola il codice e i livelli del mattino."""
    out = {}

    def giu(x, dove):
        if isinstance(x, str):
            if re.search(r"[a-zà-ù]{3}", x) and not x.endswith((".png", ".json")):
                out[dove] = _pulito(x)
        elif isinstance(x, dict):
            for k, v in x.items():
                if k not in RIGHE_FONTI and k not in NON_REDAZIONE:
                    giu(v, f"{dove}.{k}" if dove else str(k))
        elif isinstance(x, (list, tuple)):
            for i, v in enumerate(x):
                giu(v, f"{dove}.{i}")
    giu(C, "")
    return out


def righe_fonti(C):
    """Le righe Fonti dell'edizione: quella di ogni pezzo e la tabella di pag. 6 (senza i dati di mercato e la scommessa)."""
    righe = [m.get(k) for m in C.get("moduli") or [] for k in RIGHE_FONTI if isinstance(m, dict) and m.get(k)]
    righe += [r[1] for r in C.get("fonti") or [] if len(r) > 1 and not re.match(r"Dati di mercato|La scommessa", str(r[0]))]
    return righe


def fonti_nei_testi(tt, nomi=None):
    """§3.5: una testata tra parentesi senza l'orario di un livello del mattino: [(dove, "(Testata)")]."""
    return [(dove, par) for dove, t in tt.items() for par in fonti_tra_parentesi(t, nomi)]


def ritmo_campi(campi):
    """§3.4 sui paragrafi dell'edizione. È la misura esatta: sul testo estratto dal PDF titoli, elenchi e tabelle si
    fondono in "frasi" che non esistono."""
    errori, avvisi = [], []
    for campo, t in campi.items():
        lunghe, tele = ritmo([f.strip() for f in re.split(r"(?<=[.!?])\s+", t) if f.strip()])
        errori += [f"{campo}: frase oltre {MAX_PAROLE} parole ({len(g.split())}): spezzala dove cambia l'idea (§3.4): {g[:70]}"
                   for g in lunghe]
        avvisi += [f"{campo}: telegramma, {n} frasi staccate: legale tra loro (e, ma, mentre...) (§3.4): {g[:60]}"
                   for n, g in tele]
    return errori, avvisi


def stile(ed):
    """Solo il ritmo, prima del PDF: python3 controlli_testo.py --stile <edizione.py>"""
    errori, avvisi = ritmo_campi(paragrafi(ed))
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
    ed = sys.argv[sys.argv.index("--edizione") + 1] if "--edizione" in sys.argv else None
    C = edizione(ed) if ed and os.path.exists(ed) else None
    campi = paragrafi(ed, C) if C else None
    # le testate dell'edizione: fonti.json più quelle scritte nelle sue righe Fonti (dal file dell'edizione; senza, dal PDF)
    NOMI[:] = NOMI_BASE + [n for n in nomi_da_righe(righe_fonti(C) if C else re.findall(r"(?m)^Fonti?:[^\n]*(?:\n[^\n]+)*", t))
                           if n not in NOMI_BASE]
    sos = connettivi(t, coperti_da(campi or {}))
    mai, doppie, spiegate, sigle_par, sigle_due = sigle(t)
    # §3.5 sui testi dell'edizione (tabelle e riquadri compresi, righe Fonti escluse): è la misura esatta. Senza il file
    # dell'edizione resta la stima dal PDF, che vale solo come avviso: lì una riga Fonti non si distingue dal testo.
    if C:
        par_fonti = fonti_nei_testi(testi(C))
    else:
        par_fonti = [("PDF", x) for x in fonti_tra_parentesi(re.sub(r"\s+", " ", re.sub(
            r"(?m)^Fonti?:[^\n]*(?:\n[^\n]+)*", " ", t.rsplit("Fonti", 1)[0])))]
    testate = per_testata(" ".join(x for _, x in par_fonti))
    n_fonti = len(par_fonti)
    print(f"Righe →: {len(fr)} (max {MAX_FRECCE}) | cause senza chi le dà: {len(sos)} | sigle non dette in parole: {len(mai)} | "
          f"testate tra parentesi: {n_fonti} (max 0)" + (": " + ", ".join(f"{n} {k}" for n, k in sorted(
              testate.items(), key=lambda x: (-x[1], x[0])))[:90] if testate else ""))
    errori = []
    if len(fr) > MAX_FRECCE:
        errori.append(f"{len(fr)} righe → (massimo {MAX_FRECCE}): tieni solo quelle dove il perché non è ovvio")
    errori += [f"riga → oltre 20 parole: {f[:100]}" for f in lunghe]
    # §3.5: nel testo non si dice da dove viene un fatto. Un solo errore con tutte le parentesi, da togliere in un giro.
    if C and par_fonti:
        errori.append(f"{n_fonti} testate tra parentesi (§3.5): toglile, stanno nella riga Fonti del pezzo; se il nome è parte "
                      "della notizia (accusa, indiscrezione, stima, opinione, spiegazione di qualcuno) dillo nella frase. Sono: "
                      + "; ".join(f"{dove} {par}" for dove, par in par_fonti))
    errori += [f"causa senza chi la dà né lettura dichiarata nel paragrafo (§3.5): {x}" for x in sos]
    errori += [f"sigla senza le sue parole: di' che cos'è nella stessa frase, con parole di tutti (§3.4): {x}" for x in mai]
    errori += [f"sigla spiegata due volte nella stessa frase: togli la parentesi (§3.4): {x}" for x in sigle_due]
    # "secondo X" sta nella frase, mai tra parentesi: "(secondo X)" toglie protagonismo alla redazione.
    piatto = re.sub(r"\s+", " ", t)
    errori += [f"'(secondo {m.group(1).strip()})' tra parentesi: se il nome è parte della notizia dillo nella frase, altrimenti toglilo (§3.5)"
               for m in re.finditer(r"\(secondo ([^)]{2,40})\)", piatto)]
    errori += ["etichetta 'stima redazionale' vietata: scrivi la frase senza etichetta" for _ in re.finditer(r"stim[ae] redazional", piatto, re.I)]
    # v7.7: meno parentesi, voce più nostra. Etichetta tra parentesi, doppia attribuzione e citazioni in inglese.
    errori += ["etichetta '(lettura della redazione)' vietata: dilla con la nostra voce ('per noi', 'leggiamo'), senza parentesi"
               for _ in re.finditer(r"\(\s*lettura della redazione", piatto, re.I)]
    errori += [f"doppia attribuzione '{m.group(0)[:50]}': chi parla va nella frase ('secondo X'), senza 'via' e senza parentesi"
               for m in re.finditer(r"\([^()]{0,40}\bvia\b[^()]{0,40}\)", piatto)]
    # v7.8: le citazioni in inglese restano in originale (i lettori lo leggono), ma brevi: oltre 15 parole è un avviso.
    avvisi = [f"citazione in inglese oltre 15 parole: accorciala «{m.group(1)[:40]}»"
              for m in re.finditer(r"«([^»]{3,300})»", piatto)
              if len(INGLESE.findall(m.group(1))) >= 2 and len(m.group(1).split()) > 15]
    # v8.6 (§3.4): ritmo. Errore solo il periodo oltre 30 parole; avviso il telegramma (4 frasi di fila, media sotto 12 parole).
    # Si misura sui campi dell'edizione (--edizione <edizione.py>, lo passa controlli_tutti.sh): è esatto. Senza il file
    # dell'edizione resta la stima dal PDF, che vale solo come avviso: lì titolo e sommario, i punti di un elenco o una
    # tabella intera si fondono in una "frase" (collaudo del 14/11: 5-6 falsi errori in ognuna delle edizioni #022-#025).
    if campi:
        e_ritmo, a_ritmo = ritmo_campi(campi)
        errori += e_ritmo[:6]
        avvisi += a_ritmo[:3]
    else:
        corpo = piatto.split("TOP STORY", 1)[-1]
        lunghe_prosa, telegrammi = ritmo([_prosa(f) for f in re.split(r"(?<=[.!?])\s+", corpo)])
        avvisi += [f"forse una frase oltre {MAX_PAROLE} parole ({len(g.split())}, stima dal PDF): {g[:80]}" for g in lunghe_prosa[:3]]
        avvisi += [f"telegramma, {n} frasi staccate: legale tra loro (e, ma, mentre...) (§3.4): {g[:70]}"
                   for n, g in telegrammi[:3]]
    # Lessico di casa (glossario.json, "lessico"): un concetto, un nome. Le voci con "blocca" fermano: sono i termini che
    # la stampa finanziaria italiana tiene in inglese e i modi di dire tradotti parola per parola (§3.4).
    lex = json.load(open(os.path.join(QUI, "glossario.json"), encoding="utf-8")).get("lessico", {}).get("voci", [])
    for v in lex:
        trovate = [m.group(0) for rx in v.get("evita", []) for m in re.finditer(rx, piatto, re.I)]
        if len(trovate) > v.get("max", 0):
            (errori if v.get("blocca") else avvisi).append(
                f"lessico: \"{trovate[0]}\" ({len(trovate)} volte): scrivi {v['termine']}")
    for e in errori[:6]:
        print("ERRORE: " + (e if "testate tra parentesi" in e else e[:155]))
    for a in avvisi:
        print("AVVISO: " + a[:155])
    if doppie:
        print("AVVISO: sigle spiegate più di una volta: " + ", ".join(doppie)[:140])
    if sigle_par:
        print("AVVISO: sigle definite tra parentesi (§3.4: la cosa si dice in parole dentro la frase): " + ", ".join(sigle_par)[:120])
    if not C and par_fonti:
        print(f"AVVISO: forse {n_fonti} testate tra parentesi (stima dal PDF): " + ", ".join(x for _, x in par_fonti)[:110])
    print("Sigle spiegate (campo glossario): " + (", ".join(spiegate) or "-")[:150])
    if "--json" in sys.argv:
        json.dump({"frecce": fr, "connettivi": sos, "sigle_mai_spiegate": mai, "sigle_doppie": doppie,
                   "sigle_tra_parentesi": sigle_par, "glossario": spiegate, "errori": errori, "fonti_parentesi": testate},
                  open(sys.argv[sys.argv.index("--json") + 1], "w"), ensure_ascii=False, indent=1)
    if errori:
        sys.exit(1)


if __name__ == "__main__":
    main()
