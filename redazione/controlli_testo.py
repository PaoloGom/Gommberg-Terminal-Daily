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
  Una testata nominata in un pezzo come fonte ("secondo X", "per X", "lo scrive X") sta anche nella riga Fonti di quel
  pezzo (per pag. 1 e 5: in una delle righe Fonti del numero): altrimenti ERRORE. Chi parla senza nome ("la stampa
  americana", "i media", "notizie secondo cui") non copre una causa ed è un ERRORE se la frase non nomina la testata;
  un'indiscrezione è un ERRORE se il pezzo non dice da quale testata viene.
- Aperture (ISTRUZIONI §1): il testo di un approfondimento apre con un dubbio, ma con la domanda esplicita in due pezzi
  al massimo: oltre, ERRORE (nella #030 erano 5 su 5, nella prova del 21/11 4 su 4).
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
# Chi parla senza nome (§3.5: un'indiscrezione o la spiegazione di qualcuno vogliono il nome della testata). VOCI_GENERICHE
# (stampa, media, giornali) è un errore solo quando fa da fonte (dopo "secondo", "per", "dalla", come soggetto di un verbo del
# dire) e né la frase né quella dopo citano una testata. INDISCREZIONI è sempre una notizia di qualcuno: va bene se la frase,
# quella dopo o il pezzo dicono da quale testata viene. Senza distinzione di maiuscole.
VOCI_GENERICHE = (r"\b(?:(la|le|lo|i|gli|il|dalla|dalle|dai|dagli|dal|della|delle|dei|degli|alla|ai|sulla|sui|una)\s+)?"
                  r"(?:(?:alcun[ie]|divers[ie]|molt[ie]|vari[e]?|cert[ie]|altr[ie])\s+)?(stampa|media|giornali)\b")
INDISCREZIONI = (r"\bindiscrezion[ei]\b|\bfont[ei] anonim[ae]\b|\bfont[ei] vicin[ae]\b|\bvoci di mercato\b|\bresoconto anonimo\b|"
                 r"\bnotizie secondo cui\b")
# verbo del dire coniugato, in qualunque tempo (presente, imperfetto, passato remoto, tempi composti con l'ausiliare e un
# avverbio in mezzo); un infinito ("per spiegare") o un gerundio hanno un altro soggetto e non contano
_DIRE_FINITO = (r"(?:riport|parl|rivel|indic|spieg|raccont|anticip|conferm)(?:a|ano|ava|avano|ò|arono)|(?:riferisc|attribuisc)(?:e|ono)|"
                r"(?:rifer|attribu)(?:iva|ivano|ì|irono)|scriv(?:e|ono|eva|evano)|scriss(?:e|ero)|dic(?:e|ono|eva|evano)|diss(?:e|ero)|"
                r"sostien[e]|sostengono|sostenev(?:a|ano)|sostenn(?:e|ero)|leg(?:a|ano|ava|avano|ò)|dà|danno|dava|davano|diede|diedero")
_DIRE_PARTICIPIO = (r"(?:riport|parl|rivel|indic|spieg|raccont|anticip|conferm)at[oaie]|(?:rifer|attribu)it[oaie]|scritt[oaie]|"
                    r"dett[oaie]|sostenut[oaie]|legat[oaie]|dat[oaie]")
_VERBO_DIRE = (r"(?:(?:ha|hanno|aveva|avevano|avrebbe|avrebbero|ebbe|è|sono|era|erano|è stat[oa]|sono stat[ie])\s+"
               r"(?:[a-zà-ù]+\s+){0,2}?(?:" + _DIRE_PARTICIPIO + r")|" + _DIRE_FINITO + r")\b")
_DIRE = _VERBO_DIRE
_FA_DA_FONTE_PRIMA = re.compile(r"(?:\bsecondo|\bper|\bstando|\briport\w*|\briferit\w*|\briferisc\w*|\bscritt\w*|\bscriv\w*|"
                                r"\bha(?:nno)? scritto|\bcitat\w*|\bappres\w*|\bdiffus\w*|\brilanciat\w*|\banticipat\w*|\bdic(?:e|ono))"
                                r"(?:\s+(?:quanto|a|ad|da))?\s*$", re.I)
_FA_DA_FONTE_DOPO = re.compile(r"^(?:[\s,]+[\w'-]+){0,3}?[\s,]+" + _DIRE, re.I)
ESENZIONI = re.compile(r"Perch[ée] conta|Il perch[ée] |secondo (?!(?:quanto \w+ )?(?:la |i |le |gli |dai |dalla )?(?:alcun[ie] |divers[ie] )?(?:stampa|media|giornali|notizie|"
                       r"indiscrezion|font[ei] anonim|font[ei] vicin|voci di mercato))|"
                       r"stima redazionale|" + AGENDA + "|" + TENDENZA + "|" + VOCE_RED, re.I)
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


MAX_DOMANDE = 2   # §1: la domanda esplicita in apertura in uno o due pezzi dell'edizione al massimo


def aperture_con_domanda(C):
    """Gli approfondimenti il cui testo apre con una domanda esplicita (un "?" nelle prime due frasi): [titolo]."""
    out = []
    for m in C.get("moduli") or []:
        primo = _pulito((m.get("testo") or [""])[0]) if isinstance(m, dict) else ""
        if any(f.rstrip().endswith("?") for f in re.split(r"(?<=[.!?])\s+", primo)[:2]):
            out.append(str(m.get("titolo") or m.get("chiave"))[:45])
    return out


_DICE_PRIMA = re.compile(r"(?:\bsecondo|\bper|\bscriv\w+|\bha(?:nno)? scritto|\briferisc\w+|\bha riferito|\briport\w+|\bdic(?:e|ono)|"
                         r"\bspieg\w+|\bdat[oaie] da|\bsentit[oaie] da\w{0,3}|\bcitat[oaie] da\w{0,3})\s+(?:il |la |l'|i |gli |le )?$", re.I)
_DICE_DOPO = re.compile(r"^,?\s+(?:che cita|citando|scriv\w+|ha scritto|riferisc\w+|ha riferito|riport\w+|rivel\w+|ha rivelato)\b", re.I)


def fuori_dalle_fonti(C, nomi=None):
    """§3.5: una testata nominata in un pezzo come fonte ("secondo X", "per X", "lo scrive X") sta anche nella riga Fonti di
    quel pezzo; per ciò che non è un approfondimento vale una qualsiasi riga Fonti del numero. Torna [(dove, testata)].
    Conta solo quando la testata fa da fonte: "il Tesoro mette all'asta" parla del Tesoro, non lo cita."""
    nome = nome_fonte(nomi)
    tutte = " ".join(str(r) for r in righe_fonti(C)) + " " + " ".join(str(r[1]) for r in C.get("fonti") or [] if len(r) > 1)
    corto = lambda n: re.sub(r"^(?:Il|La|Lo|The) ", "", n)   # noqa: E731

    def cerca(testi_, righe, dove0):
        out = []
        for dove, t in testi_.items():
            for m in nome.finditer(t):
                n = m.group(0)
                if (_DICE_PRIMA.search(t[max(0, m.start() - 30):m.start()]) or _DICE_DOPO.search(t[m.end():m.end() + 25])) \
                        and corto(n).lower() not in righe.lower() and (dove0 + dove, n) not in out:
                    out.append((dove0 + dove, n))
        return out
    fuori, moduli = [], C.get("moduli") or []
    for i, m in enumerate(moduli):
        if isinstance(m, dict):
            fuori += cerca(testi(m), " ".join(str(m.get(k) or "") for k in RIGHE_FONTI), f"moduli.{m.get('chiave', i)}.")
    fuori += cerca(testi({k: v for k, v in C.items() if k != "moduli"}), tutte, "")
    return fuori


# una testata detta come fonte: dopo "secondo/per/scrive/citate da/tra cui/che cita...", dopo una parola di cronaca con
# di/del/dal ("le indiscrezioni del X"), dopo un participio con "da" ("pubblicate dal X"), o prima di un verbo del dire
_CITA_FORTE = (r"\b(?:" + _VERBO_DIRE[3:-3] + r")|\bsecondo|\bstando a\w*|\bscriv\w+|\bha(?:nno)? scritto|\briferisc\w+|\bha riferito|\briport\w+|\bdic(?:e|ono)|"
               r"\bcitat[oaie] da\w*|\bpubblicat\w* da\w*|\btra cui|\bche cita|\bcitando|\bcome scriv\w+|"
               r"\b(?:indiscrezion\w*|notizi\w+|articol\w+|scoop|resoconto|rivelazion\w+|anticipazion\w+|servizio|inchiesta)"
               r"(?:\s+[\w']+){0,2}?\s+(?:di|del|dello|della|dei|degli|delle|dell'|dal|dalla|dallo|dai)")
_FINE = r"\s*(?:il |la |lo |l'|i |gli |le )?$"
_CITA_PRIMA = re.compile(r"(?:" + _CITA_FORTE + r"|\bper|\bspieg\w+|\bsentit[oaie] da\w*|\b[a-zà-ù]+t[oaie] da(?:l|lla|llo|i|gli|lle)?)" + _FINE, re.I)
_CITA_SIGLA = re.compile(r"(?:" + _CITA_FORTE + r")" + _FINE, re.I)
_GEN_A = re.compile(r"^[\s,]*(?:[\w'-]+\s+){0,2}?(?:la |le |i |gli |dalla |dai |della |dei )?(?:stampa|media|giornali)\b", re.I)
# la frase dopo vale solo se riprende la notizia di quella prima: "Lo scrive X", "A rivelarlo è stato X", "L'ha riferito X"
# la frase dopo riprende la notizia di quella prima con un pronome e un verbo del dire ("Lo ha scritto X", "Ne ha dato
# notizia X", "L'ha rivelato X"), con "A rivelarlo è stato X", o con "La notizia..." di cui la testata è soggetto o agente
_RIPRESA_PRONOME = re.compile(r"^(?:A (?:rivelar|riferir|scriver|riportar|anticipar|dar|diffonder|pubblicar)\w*|(?:L[oaie] |L'|Ne )"
                              + _VERBO_DIRE + r")", re.I)
_RIPRESA_NOTIZIA = re.compile(r"^(?:La notizia|Lo scoop|L'indiscrezione)\b", re.I)
# richiamo di un'indiscrezione già detta: articolo determinativo e nessun complemento che porti un fatto nuovo
_RICHIAMO = re.compile(r"\b(?:le |l'|la |queste |quelle |tali )(?:indiscrezion[ei]|voc[ei])\b(?!\s+(?:su|sul|sulla|sullo|sui|sugli|sulle|"
                       r"di|del|della|dei|delle|che|secondo|da|dal|dalla|dai|danno|dà|indicano|parlano)\b)", re.I)
def senza_testata(tt, nomi=None, righe=()):
    """§3.5: chi parla senza nome. Una voce generica (stampa, media, giornali) che fa da fonte, o un'indiscrezione (fonti
    anonime o vicine, voci di mercato, "notizie secondo cui"), è un errore se la sua frase non cita una testata come fonte, né
    la frase dopo riprendendo la stessa notizia ("Lo ha scritto X", "A rivelarlo è stato X"). Il richiamo di
    un'indiscrezione già detta ("le indiscrezioni", con l'articolo e senza un fatto nuovo) è coperto se la frase prima la
    attribuisce a una testata, o se il pezzo l'ha attribuita ("secondo tre fonti citate da X"); un'indiscrezione nuova vuole
    la sua testata nella stessa frase. Una testata solo nominata (il
    soggetto della notizia) non basta; una sigla del glossario copre solo se è una testata dell'edizione (scritta nelle sue
    righe Fonti: il Nikkei giornale, non l'indice) e solo da fonte dichiarata ("secondo il Nikkei"). Torna [(dove, frase)]."""
    nome = nome_fonte(list(nomi or NOMI))
    nelle_righe = " ".join(str(r) for r in righe)
    testate_sigla = [n for n in SIGLE if re.search(r"(?<![\w/])" + re.escape(n) + r"(?![\w/])", nelle_righe)]
    sigla = nome_fonte(testate_sigla) if testate_sigla else None
    gen, ind = re.compile(VOCI_GENERICHE, re.I), re.compile(INDISCREZIONI, re.I)

    def citata(t):      # "Nvidia, riferisce la stampa americana" non cita Nvidia: il verbo ha per soggetto la stampa
        def dopo(m):
            d = _DICE_DOPO.search(t[m.end():m.end() + 25]) or re.match(r",?\s+" + _VERBO_DIRE, t[m.end():m.end() + 40], re.I)
            return d and not _GEN_A.search(t[m.end():m.end() + 60][d.end():])
        return any(_CITA_PRIMA.search(t[max(0, m.start() - 45):m.start()]) or dopo(m) for m in nome.finditer(t)) or \
            bool(sigla and any(_CITA_SIGLA.search(t[max(0, m.start() - 45):m.start()]) for m in sigla.finditer(t)))

    def soggetto(resto):    # la testata subito dopo il verbo, al più con qualche parola in mezzo ("per primo è stato il X")
        n = nome.search(resto)
        return bool(n) and bool(re.fullmatch(r"(?:\s+[a-zà-ù]+){0,4}?\s+(?:il |la |lo |l')?", resto[:n.start()], re.I))

    def ripresa(f):
        m = _RIPRESA_PRONOME.search(f)
        if m:               # la testata è il soggetto: "A rivelarla è stato il X", "Lo ha scritto per primo il X"
            return soggetto(f[m.end():])
        m = _RIPRESA_NOTIZIA.search(f)
        if m:               # la testata è l'agente o l'autrice della notizia: "La notizia è stata data da X", "è del X"
            n = nome.search(f)
            return bool(n) and bool(re.search(r"\b(?:da|dal|dalla|dallo|dai|di|del|della|dello)\s+(?:il |la |lo |l')?$",
                                              f[:n.start()])) and not re.search(r",|\bmentre\b|\be\b", f[m.end():n.start()])
        return False

    def da_fonte(f):    # la voce generica fa da fonte, non è il fatto ("i media di Stato chiudono", "la media mobile")
        for m in gen.finditer(f):
            art, voce = (m.group(1) or "").lower(), m.group(2).lower()
            if voce == "media" and art in ("la", "lo", "una", "della", "alla", "sulla"):
                continue                       # la media, una media: la media dei numeri
            if art in ("dalla", "dalle", "dai", "dagli", "dal") or _FA_DA_FONTE_PRIMA.search(f[max(0, m.start() - 30):m.start()]) \
                    or _FA_DA_FONTE_DOPO.search(f[m.end():m.end() + 45]):
                return True
        return False
    frasi_di = {dove: re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", t)) for dove, t in tt.items()}
    # un'indiscrezione già attribuita nel pezzo ("secondo tre fonti citate da X") copre i suoi richiami ("le indiscrezioni
    # dicono"); una testata citata per un'altra notizia no
    pezzo = lambda d: ".".join(d.split(".")[:2]) if d.split(".")[0] in ("moduli", "notizie", "in30") else d.split(".")[0]   # noqa: E731
    attribuita = {pezzo(d) for d, ff in frasi_di.items() for f in ff if re.search(INDISCREZIONI + r"|\bfont[ei]\b", f, re.I) and citata(f)}
    out = []
    for dove, ff in frasi_di.items():
        for i, f in enumerate(ff):
            if citata(f) or (i + 1 < len(ff) and ripresa(ff[i + 1])):
                continue
            richiamo = _RICHIAMO.search(f) and ((i > 0 and citata(ff[i - 1])) or pezzo(dove) in attribuita)
            if da_fonte(f) or (ind.search(f) and not richiamo):
                out.append((dove, f.strip()[:120]))
    return out


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
    if C:
        fuori = fuori_dalle_fonti(C)
        if fuori:
            errori.append("testate nominate nel testo ma assenti dalla riga Fonti del pezzo (§3.5): aggiungile alla riga Fonti (letta ripresa da "
                          "un'altra testata: \"X, ripresa da Y\"). Sono: "
                          + "; ".join(f"{dove} {n}" for dove, n in fuori))
        anonime = senza_testata(testi(C), righe=righe_fonti(C))
        if anonime:
            errori.append("chi parla senza nome (§3.5): un'indiscrezione o la spiegazione di qualcuno vogliono il nome della testata nella "
                          "frase (e nella riga Fonti); \"la stampa\", \"i media\", \"notizie\" non sono un nome. Cerca nelle schede "
                          "del fatto la testata che lo scrive e mettila nella frase; togli la frase solo se nelle schede la fonte non "
                          "c'è davvero. Sono: " + "; ".join(f"{dove} «{f}»" for dove, f in anonime))
        domande = aperture_con_domanda(C)
        if len(domande) > MAX_DOMANDE:
            errori.append(f"{len(domande)} approfondimenti aprono con una domanda esplicita (massimo {MAX_DOMANDE}): tienila dove rende di "
                          "più e negli altri apri lo stesso dubbio in un'altra forma, senza punto di domanda (un contrasto, "
                          "un'attesa smentita, due prezzi che non tornano insieme) (§1). Sono: " + "; ".join(domande))
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
        print("ERRORE: " + (e if "Sono: " in e else e[:155]))
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
