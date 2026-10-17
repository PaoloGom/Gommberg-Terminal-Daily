"""Controlli editoriali (BLOCCANTI salvo AVVISO) sul PDF e sui file del giorno. Uso:
  python3 controlli_contenuti.py <pdf> [--voce voce_indice.json] [--dati dati.json] [--fatti fatti.json] [--repo /home/claude/gtd]
Regole (ISTRUZIONI §5 e §7), ognuna generale:
 estremi   ogni indice principale in dati.json (obbligatori: S&P 500, Nasdaq, Euro Stoxx 50, Nikkei 225, Kospi, Hang Seng)
           con |var| >= 3% compare con la sua cifra in PRIMA PAGINA (dopo il ticker); un obbligatorio assente = ERRORE.
 rari      il movimento più raro di contesto.py (contesto.json, solo se capita meno di una seduta su 20) è citato in
           prima pagina.
 aperture  registro {"sezione": "prime_pagine"} in fatti.json: almeno 3 testate con la loro apertura; se la top story
           non concorda con la maggioranza, serve il "motivo" (§2).
 perche    PERCHÉ = causa con fonte ("(Testata)" in coda o "secondo X"), meccanismo ("di solito", "in genere"), lettura della redazione o
           "causa non chiarita" (solo se il registro dell'anomalia ha tutte le ipotesi "non torna"); "le fonti non
           spiegano" è un ERRORE in qualunque sezione del PDF;
           E QUINDI = qualcosa di osservabile: una cifra, una data, un orario, "oggi/domani/<giorno>" o un rimando.
 prob      una probabilità ha orizzonte (mese, data, riunione, N anni), metodo (future, FedWatch, CDS, sondaggio, stima
           redazionale...) e fonte (secondo X, (X)). Pag. 1-5.
 record    "record", "massimo storico", "da N anni" solo con una scheda di fatti.json che lo dice (ERRORE);
           "massimo/minimo dal <data>" senza scheda = AVVISO (deve venire da una serie calcolata).
 anomalie  sorpresa macro (dato contro attese, da dati.json "macro" o dalle schede) e prezzi contrari (10 anni -3 pb o
           S&P +0,5% su dato caldo; il contrario su dato freddo) = serve una voce {"sezione": "anomalia"} in fatti.json.
 stamattina  orari tra le 06:00 e le 09:29 di Roma; un livello già nella Stamattina dell'edizione precedente = ERRORE.
 moduli    i punti non ripetono le cifre della tabella; graduatorie del testo coerenti con i dati del grafico; moduli tutti
           con lo stesso stampo = AVVISO; quadro trasversale (C["quadro"]) presente."""
import json, os, re, subprocess, sys

ARG = sys.argv[1:]
PDF = ARG[0]
opt = lambda k, d=None: ARG[ARG.index(k) + 1] if k in ARG else d
LAV = os.environ.get("GTD_LAVORO", "/home/claude/lavoro")
VOCE_P, DATI_P, FATTI_P = opt("--voce", f"{LAV}/voce_indice.json"), opt("--dati", f"{LAV}/dati.json"), opt("--fatti", f"{LAV}/fatti.json")
REPO = opt("--repo", os.environ.get("GTD_REPO", "/home/claude/gtd"))
carica = lambda p: json.load(open(p, encoding="utf-8")) if p and os.path.exists(p) else None
VOCE, DATI, FATTI = carica(VOCE_P) or {}, carica(DATI_P), carica(FATTI_P) or []
SCHEDE = [f for f in FATTI if isinstance(f, dict) and f.get("sezione") not in ("anomalia", "prime_pagine") and not f.get("scartata")]
ERR, AVV = [], []
MESI = "gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre"
GIORNI = "oggi|domani|lunedì|martedì|mercoledì|giovedì|venerdì|lun|mar|mer|gio|ven"


def pdftext(p, layout=False):
    a = ["pdftotext"] + (["-layout"] if layout else []) + [p, "-"]
    return subprocess.run(a, capture_output=True).stdout.decode("utf-8", "replace")


RAW = pdftext(PDF)
PAG = RAW.split("\f")
FRASI15 = [f for b in re.split(r"\n\s*\n", "\n\n".join(PAG[:5])) for f in
           re.split(r"(?<=[.;])\s+(?=[A-Z0-9ÀÈÉÌÒÙ\"(])", re.sub(r"\s+", " ", b).strip()) if f]
TUTTO = re.sub(r"\s+", " ", RAW)
_p1 = PAG[0] if PAG else ""
PRIMA = re.sub(r"\s+", " ", _p1[_p1.find("TOP STORY"):] if "TOP STORY" in _p1 else _p1)
it = lambda x, d: f"{x:.{d}f}".replace(".", ",")


def frasi(t):
    return [s.strip() for s in re.split(r"(?<=[.;])\s+(?=[A-Z0-9ÀÈÉÌÒÙ\"(])", t) if s.strip()]


def testo_schede():
    for f in SCHEDE:
        yield (f.get("testo", "") + " " + " ".join(x.get("citazione", "") for x in f.get("fonti", []))).lower(), f


# ---------- estremi (B3) ----------
OBBLIGATORI = {"S&P 500": r"s&p ?500", "Nasdaq": r"nasdaq", "Euro Stoxx 50": r"stoxx ?50", "Nikkei 225": r"nikkei",
               "Kospi": r"kospi|seul|seoul", "Hang Seng": r"hang ?seng"}
if DATI:
    serie = DATI.get("serie", {})
    for nome, rx in OBBLIGATORI.items():
        if not any(re.search(rx, k, re.I) for k in serie):
            ERR.append(f"estremi: {nome} assente da dati.json (indice principale: chiusura dell'ultima seduta conclusa, "
                       "o 'var' con fonte e orario, o 'nd' col motivo: APP_DATI.md §6)")
    for k, s in serie.items():
        if s.get("mercato") not in ("USA", "EU", "UK", "JP", "HK", "KR", "CN") or s.get("tipo_var") == "punti":
            continue
        u = s.get("ultimi") or []
        var = s.get("var") if s.get("var") is not None else ((u[0][1] / u[1][1] - 1) * 100 if len(u) >= 2 and u[1][1] else None)
        if s.get("nd") or var is None or abs(var) < 3:
            continue
        cand = {it(abs(var), 2), it(abs(var), 1)}
        if not any(re.search(r"(?<![\d,])[+-]?" + re.escape(c) + r"\s?%", PRIMA) for c in cand):
            ERR.append(f"estremi: {k} {var:+.2f}% (movimento oltre il 3%) non compare in prima pagina: va citato con la cifra "
                       "(top story, In 30 secondi o una notizia), non solo nel cruscotto")

# ---------- rari e aperture (prima pagina) ----------
PAROLE = {"S&P 500": r"s&p", "Euro Stoxx 50": r"stoxx|borse europee", "ACWI": r"azionario mondiale|acwi",
          "Brent future": r"brent|petrolio", "EUR/USD": r"euro|dollaro", "VIX": r"vix|volatilit",
          "Treasury 10 anni": r"treasury|rendiment", "Treasury 2 anni": r"treasury|rendiment|2 anni"}
CTX = carica(f"{LAV}/contesto.json")
if CTX:
    rari = [m for m in CTX.get("movimenti", []) if abs(m.get("z", 0)) >= 2 and m["serie"] in PAROLE]
    if rari:
        m = max(rari, key=lambda x: abs(x["z"]))
        if not re.search(PAROLE[m["serie"]], PRIMA, re.I):
            ERR.append(f"rari: {m['serie']} {m.get('frase_da', '')} ({m.get('rarita', '')}): il movimento più raro del giorno "
                       "va citato in prima pagina con la sua misura storica")
reg_pp = [f for f in FATTI if isinstance(f, dict) and f.get("sezione") == "prime_pagine"]
if not reg_pp:
    ERR.append("aperture: manca il registro delle aperture in fatti.json: {\"id\": \"P1\", \"sezione\": \"prime_pagine\", "
               "\"testate\": [{\"testata\": ..., \"apertura\": ...}], \"concorda\": true|false, \"motivo\": ...} (§2, §6.2)")
else:
    r = reg_pp[0]
    if len([t for t in r.get("testate", []) if t.get("testata") and t.get("apertura")]) < 3:
        ERR.append("aperture: servono almeno 3 testate, ognuna con 'testata' e 'apertura'")
    if r.get("concorda") is False and not (r.get("motivo") or "").strip():
        ERR.append("aperture: la top story non è l'apertura della maggioranza delle testate: scrivi il 'motivo' della scelta")

# ---------- perche / quindi (B6) ----------
OSSERVABILE = re.compile(r"\d+(?:[.,]\d+)?\s?(?:%|pb|\$|€|mld|mila|punti)|\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+,\d+|"
                         r"\b\d{1,2}[:/]\d{2}\b|\b\d{1,2} (?:" + MESI + r")\b|\b(?:" + GIORNI + r")\b|→ ?pag", re.I)
QUI = os.path.dirname(os.path.abspath(__file__))

def _fonte_tra_parentesi():
    """Regex dell'attribuzione in coda: "(Reuters)", "(Yahoo Finance, FIRSTonline)", "(dati BLS)"."""
    nomi = json.load(open(os.path.join(QUI, "fonti.json"), encoding="utf-8")).get("nomi", [])
    alt = "|".join(sorted((re.escape(n) for n in nomi), key=len, reverse=True))
    return re.compile(r"\([^()]{0,30}\b(?:" + alt + r")\b[^()]{0,40}\)")


FONTE_PAR = _fonte_tra_parentesi()
CAUSA_T = re.compile(r"\bsecondo\b|di solito|in genere|lettura della redazione|causa non chiarita|\bM\d{2}\b", re.I)


class _Causa:
    def search(self, t):
        return CAUSA_T.search(t) or FONTE_PAR.search(t)


CAUSA = _Causa()
VUOTO = re.compile(r"fonti(?: di oggi)? non (?:danno|indicano|spiegano|forniscono)|non danno una spiegazione", re.I)
moduli = VOCE.get("moduli_redazione")
if moduli is None:  # dal PDF: blocchi PERCHÉ / E QUINDI
    blocchi = re.findall(r"(?:^|\n)(PERCHÉ|E QUINDI)\n(.*?)(?=\n\s*\n|\Z)", RAW, re.S)
    coppie, cur = [], {}
    for k, v in blocchi:
        cur["perche" if k == "PERCHÉ" else "quindi"] = re.sub(r"\s+", " ", v)
        if k == "E QUINDI":
            coppie.append(cur); cur = {}
    moduli = [dict(c, titolo=f"modulo {i}") for i, c in enumerate(coppie, 1)]
for i, m in enumerate(moduli, 1):
    nome = (m.get("chiave") or m.get("titolo") or str(i))[:40]
    p, q = m.get("perche", ""), m.get("quindi", "")
    if not p or not q:
        ERR.append(f"perche: modulo {nome} senza perche o quindi"); continue
    if VUOTO.search(p):
        ERR.append(f"perche: modulo {nome}: 'le fonti non spiegano' non è un perché: dopo la ricerca registrata "
                   "(anomalia, §6.2c) scrivi la causa attribuita o la lettura della redazione con i prezzi che la sostengono")
    elif not CAUSA.search(p):
        ERR.append(f"perche: modulo {nome}: serve la causa con fonte ('(Testata)' in coda), un meccanismo o la lettura della redazione: \"{p[:70]}\"")
    if not OSSERVABILE.search(q):
        ERR.append(f"quindi: modulo {nome}: serve una cosa osservabile (livello, data, orario, evento in agenda): \"{q[:70]}\"")

# ---------- probabilità (B5) ----------
for s in FRASI15:
    if len(s.split()) >= 12 and re.search(r"probabilit|scommess|\bprezza", s, re.I) and "%" in s and not re.search(r"stim[ae] redazional", s, re.I):
        manca = [n for n, rx in (("orizzonte", r"\b(?:" + MESI + r")\b|\d{1,2}/\d{1,2}|riunione|(?:\d+|un|due|tre|cinque|dieci) ann[io]|entro|settiman|\banno\b"),
                                 ("metodo", r"future|fedwatch|cds|swap|opzion|sondagg|polymarket|kalshi|cumulat"),
                                 ("fonte", r"\bsecondo\b|\([A-Z]"))
                if not re.search(rx, s, re.I)]
        if manca:
            ERR.append(f"prob: manca {', '.join(manca)}: \"{s[:90]}\"")

# ---------- record (B8) ----------
STOP = set("della delle degli dello sono anche dopo prima contro sulla sulle nella nelle negli questo quella".split())
for s in FRASI15:
    forte = re.search(r"\brecord\b|massim[oi] storic|minim[oi] storic|da (?:oltre |più di )?(?:\d+|un|due|tre|quattro|cinque|sei|"
                      r"sette|otto|nove|dieci) anni|dai tempi d", s, re.I)
    debole = re.search(r"(?:massim|minim)[oi] dal?l?'?\s?\d", s, re.I)
    if not (forte or debole):
        continue
    parole = {w for w in re.findall(r"[a-zà-ù]{5,}", s.lower()) if w not in STOP}
    ok = any(re.search(r"record|massim|minim|highest|lowest|since|più alt|più bass|anni|years", t) and parole & set(re.findall(r"[a-zà-ù]{5,}", t))
             for t, _ in testo_schede())
    if not ok:
        (ERR if forte else AVV).append(f"record: nessuna scheda dice \"{(forte or debole).group(0)}\": \"{s[:80]}\"")

# ---------- "le fonti non spiegano" in qualunque sezione ----------
_vuoto = VUOTO.search(re.sub(r"\s+", " ", RAW))
if _vuoto:
    ERR.append("perche: \"" + _vuoto.group(0) + "\" nel PDF: dopo la ricerca (§6.2c) va la causa attribuita o la lettura della redazione")

# ---------- anomalie (P7) ----------
def sorprese():
    if DATI and DATI.get("macro"):
        for x in DATI["macro"]:
            segno = -1 if x.get("caldo_se") == "giu" else 1
            yield x.get("nome", "?"), (x["dato"] - x["atteso"]) * segno
        return
    rx = [re.compile(r"([+-]?\d+(?:,\d+)?)\s?%[^();%]{0,30}?\(\s*(?:atteso|attese|previsto|consenso)\s*:?\s*([+-]?\d+(?:,\d+)?)"),
          re.compile(r"([+-]?\d+(?:,\d+)?)\s?%[^();%]{0,15}?contro (?:il |lo |l')?([+-]?\d+(?:,\d+)?)\s?% (?:atteso|previsto)")]
    for f in SCHEDE:
        if f.get("sezione") not in ("top_story", "catalizzatori", "macro", "top_news", "calendario", "notizie"):
            continue
        t = f.get("testo", "")
        for r in rx:
            for m in r.finditer(t):
                segno = -1 if re.search(r"disoccupaz|sussid|richieste", t[max(0, m.start() - 60):m.start()], re.I) else 1
                yield t[:40], (float(m.group(1).replace(",", ".")) - float(m.group(2).replace(",", "."))) * segno


def delta(rx, pb):
    for k, s in (DATI or {}).get("serie", {}).items():
        u = s.get("ultimi") or []
        if re.search(rx, k, re.I) and len(u) >= 2 and u[1][1]:
            return (u[0][1] - u[1][1]) * 100 if pb else (u[0][1] / u[1][1] - 1) * 100
    return None


if DATI:
    d10, spx = delta(r"treasury 10|10 anni|ust ?10", True), delta(r"s&p ?500", False)
    anomale = []
    for nome, sorpresa in sorprese():
        if sorpresa > 0 and ((d10 is not None and d10 <= -3) or (spx is not None and spx >= 0.5)):
            anomale.append(f"{nome} sopra le attese ma 10 anni {d10:+.0f} pb / S&P {spx:+.2f}%")
        if sorpresa < 0 and ((d10 is not None and d10 >= 3) or (spx is not None and spx <= -0.5)):
            anomale.append(f"{nome} sotto le attese ma 10 anni {d10:+.0f} pb / S&P {spx:+.2f}%")
    registro = [f for f in FATTI if isinstance(f, dict) and f.get("sezione") == "anomalia"]
    ids_c = {f.get("id") for f in SCHEDE if f.get("tipo") == "C"}
    for a in registro:
        ip, es = a.get("ipotesi") or [], a.get("esito")
        esiti = [x.get("prezzi") for x in ip]
        if not a.get("ricerche") or not (es in ids_c or es in ("ipotesi", "non chiarita")):
            ERR.append(f"anomalie: voce {a.get('id')} incompleta: servono 'ricerche' (le query) ed 'esito' = id di una scheda C, "
                       "\"ipotesi\" o \"non chiarita\" (§6.2c)")
        elif es in ("ipotesi", "non chiarita") and (len(ip) < 2 or any(e not in ("torna", "in parte", "non torna") for e in esiti)):
            ERR.append(f"anomalie: voce {a.get('id')}: con esito \"{es}\" servono almeno 2 'ipotesi', ognuna con 'causa', "
                       "'prevede' e 'prezzi' = torna | in parte | non torna")
        elif es == "ipotesi" and not any(e in ("torna", "in parte") for e in esiti):
            ERR.append(f"anomalie: voce {a.get('id')}: esito \"ipotesi\" ma nessuna ipotesi torna con i prezzi: rivedi le ipotesi")
        elif es == "non chiarita" and any(e in ("torna", "in parte") for e in esiti):
            ERR.append(f"anomalie: voce {a.get('id')}: \"non chiarita\" ma un'ipotesi torna con i prezzi: pubblicala come "
                       "lettura della redazione (esito \"ipotesi\")")
        elif es in ids_c and any(x.get("fonte") == es and x.get("prezzi") == "non torna" for x in ip):
            AVV.append(f"anomalie: voce {a.get('id')}: la causa di {es} non torna con i prezzi: nel PDF va detto")
    if anomale and not registro:
        ERR.append(f"anomalie: fatto controintuitivo ({anomale[0][:90]}) senza registro: aggiungi a fatti.json "
                   "{\"id\": \"A1\", \"sezione\": \"anomalia\", \"fatto\": ..., \"ricerche\": [...], \"ipotesi\": [...], \"esito\": ...} (§6.2c)")

# ---------- stamattina (P10) ----------
def blocco_stamattina(raw):
    m = re.search(r"\nSTAMATTINA\n(.*?)(?:\n[A-ZÀÈÌÒÙ][A-ZÀÈÌÒÙ0-9 '&/.,-]{3,}\n|\f)", raw, re.S)
    return [re.sub(r"\s+", " ", x) for x in re.split(r"\n\s*\n", m.group(1))] if m else []


stam = VOCE.get("stamattina") or blocco_stamattina(RAW)
apertura = VOCE.get("stamattina_titolo", "Stamattina") != "Stamattina" or "COSA GUARDARE ALL'APERTURA" in RAW
if apertura:   # senza livelli del mattino verificati: soglie ed eventi della giornata, orari liberi
    stam = []
elif VOCE.get("stamattina") is not None and not any(re.search(r"\b\d{1,2}[:.]\d{2}\b", s) for s in stam):
    ERR.append("stamattina: nessun livello con orario del mattino: C[\"stamattina_titolo\"] = \"Cosa guardare all'apertura\" "
               "e 2-4 soglie o eventi con orario dall'agenda e dalle chiusure")
for s in stam:
    s = re.sub(r"(?:[Oo]ggi|[Dd]omani) alle \d{1,2}[:.]\d{2}", "", s)   # rimandi all'agenda (anche da colonne vicine nel PDF)
    ore = re.findall(r"\b(\d{1,2})[:.](\d{2})\b", s)
    for h, mi in ore:
        if not (6 <= int(h) < 9 or (int(h) == 9 and int(mi) < 30)):
            ERR.append(f"stamattina: orario {h}:{mi} fuori dalla finestra 06:00-09:29: \"{s[:70]}\"")
try:
    ed = carica(os.path.join(REPO, "edizioni.json")) or []
    prec = max((v for v in ed if v["numero"] < VOCE.get("numero", 10 ** 6)), key=lambda v: v["numero"], default=None)
    if prec and os.path.exists(os.path.join(REPO, prec["file"])):
        # solo prezzi precisi (cambi a 4 decimali, livelli sopra 100 con decimali): rendimenti e % coincidono per caso
        livelli = lambda xs: set(re.findall(r"(?<![\d.,])(?:\d,\d{4}|\d{1,3}(?:\.\d{3})+,\d{2}|\d{3},\d{2})(?![\d%]|\s?pb)", " ".join(xs)))
        rip = livelli(stam) & livelli(blocco_stamattina(pdftext(os.path.join(REPO, prec["file"]))))
        for x in sorted(rip):
            ERR.append(f"stamattina: {x} era già nella Stamattina della #{prec['numero']:03d}: dato vecchio con orario nuovo")
except Exception as e:  # noqa: BLE001
    AVV.append(f"stamattina: confronto con l'edizione precedente non riuscito ({e})")

# ---------- moduli: punti contro tabella, graduatorie, stampo, quadro (B2, B7, B8, B9) ----------
CIFRA = re.compile(r"[+-]?\d{1,3}(?:\.\d{3})*,\d+\s?%?|[+-]?\d+\s?%")
red = VOCE.get("moduli_redazione")
if red:
    for m in red:
        tab = {c.lstrip("+-").replace(" ", "") for r in m.get("righe", [])[1:] for cell in r for c in CIFRA.findall(cell)}
        for p in m.get("punti", []):
            dup = {c.lstrip("+-").replace(" ", "") for c in CIFRA.findall(p)} & tab
            if dup:
                ERR.append(f"moduli: {m.get('chiave')}: un punto ripete la tabella ({', '.join(sorted(dup))}): il punto aggiunge, non ripete")
        testo = " ".join([m.get("titolo", ""), m.get("perche", ""), m.get("quindi", "")] + m.get("punti", [])).lower()
        for g in m.get("grafici", []):
            dati = g.get("dati") or []
            if len(dati) < 3:
                continue
            vmin, vmax = min(v for _, v in dati), max(v for _, v in dati)
            for lab, v in dati:
                w = re.escape(lab.split()[0].lower())
                if len(w) >= 4 and re.search(w + r"[^.;]{0,40}(maglia nera|ultim[ao]\b|peggior|in coda)", testo) and v != vmin:
                    ERR.append(f"moduli: {m.get('chiave')}: il testo dà {lab} in coda, il grafico no ({it(v, 2)})")
                if len(w) >= 4 and re.search(w + r"[^.;]{0,40}(in testa|miglior|guida)", testo) and v != vmax:
                    ERR.append(f"moduli: {m.get('chiave')}: il testo dà {lab} in testa, il grafico no ({it(v, 2)})")
    stampi = {(m.get("misura"), len(m.get("grafici", [])), bool(m.get("righe")), bool(m.get("punti"))) for m in red}
    if len(red) >= 3 and len(stampi) == 1:
        AVV.append("moduli: tutti con lo stesso stampo: varia la composizione secondo il contenuto (§2)")
    for m in red:   # generalizzazioni smentite dalla tabella o dal grafico del modulo
        testo = " ".join([m.get("titolo", ""), m.get("perche", ""), m.get("quindi", "")] + m.get("punti", [])).lower()
        valori = [v for g in m.get("grafici", []) for _, v in (g.get("dati") or [])]
        valori += [float(c.replace(".", "").replace(",", ".").rstrip("% ")) for r in m.get("righe", [])[1:] for cell in r
                   for c in re.findall(r"[+-]\d+(?:,\d+)?\s?%", cell)]
        if re.search(r"(tutt[ei]|le altre)[^.;]{0,30}(in rialzo|salgono|positiv)", testo) and any(v < 0 for v in valori):
            ERR.append(f"moduli: {m.get('chiave')}: \"tutte/le altre in rialzo\" ma tabella o grafico hanno un calo")
        if re.search(r"(tutt[ei]|le altre)[^.;]{0,30}(in calo|scendono|negativ)", testo) and any(v > 0 for v in valori):
            ERR.append(f"moduli: {m.get('chiave')}: \"tutte/le altre in calo\" ma tabella o grafico hanno un rialzo")

# ---------- notizie con un fatto nuovo, indice senza cifre, zero col segno ----------
ASSET = set("""wall street nasdaq dow jones russell s&p euro stoxx ftse mib dax cac nikkei kospi hang seng shanghai shenzhen
tokyo seul hong kong milano londra parigi francoforte madrid piazza affari europa asia borsa borse brent wti treasury btp bund vix
eur usd dollaro euro yen oro petrolio spread indice indici listino listini stato stati uniti""".split())
FONTI_N = set("secondo ansa teleborsa reuters bloomberg axios thestreet investinglive investing cnbc sole radiocor firstonline "
              "yahoo finance milano finanza fxstreet admiral markets lseg ap afp".split())
FATTO = re.compile(r"\butil|ricav|fattur|vendite al dettaglio|inflazion|prezzi|pil\b|occupa|disoccup|sussid|pmi\b|fiducia|produzion|"
                   r"dichiar|annunc|decid|accord|sanzion|dazi|attacc|guerra|tagli|rialzo dei tassi|debito|insolven|stime|conti|"
                   r"trimestr|acquisizion|fusion|offert|licenzi|sciopero|elezion|governo|banca central", re.I)
nt = VOCE.get("notizie_testo") or VOCE.get("notizie") or []
con_fatto = 0
for n in nt:
    propri = [w for w in re.findall(r"(?<![.:] )(?<!^)\b[A-Z][A-Za-z&]{2,}", n) if w.lower() not in ASSET | FONTI_N]
    estremo = any(abs(float(x.replace(",", "."))) >= 3 for x in re.findall(r"[+-](\d+,\d+)\s?%", n))
    if FATTO.search(n) or propri or estremo:
        con_fatto += 1 if (FATTO.search(n) or propri) else 0
    elif re.search(r"[+-]\d|\b(rialzo|calo|sale|scende|salgono|scendono)\b", n, re.I):
        ERR.append(f"notizie: \"{n[:70]}\" riscrive il cruscotto: serve un fatto nuovo (dato, dichiarazione, società, decisione)")
if len(nt) >= 6 and con_fatto < 2:
    ERR.append(f"notizie: solo {con_fatto} con dati macro o società: almeno 2 su 6")
for b in VOCE.get("brevi", []):
    if re.search(r"\d\s?(%|pb|\$)|\d,\d", b):
        ERR.append(f"indice di pag. 1: \"{b}\" porta una cifra: le voci di 'Nelle pagine interne' non ripetono cifre")
for z in sorted(set(re.findall(r"[+-]0,0+\s?%", TUTTO))):
    ERR.append(f"zero col segno: \"{z}\": scrivi 0,0% o \"invariato\", mai un calo o un rialzo")

if "quadro" in VOCE or red is not None:
    if not VOCE.get("quadro"):
        ERR.append("quadro: manca C[\"quadro\"], la frase che legge insieme tassi, dollaro, oro, petrolio e borse (§5)")
    elif VOCE["quadro"][:40] not in TUTTO:
        AVV.append("quadro: la frase non compare nel PDF (motore da aggiornare?)")
else:
    AVV.append("quadro: voce_indice.json senza i campi di redazione (modello vecchio?)")

print(f"Contenuti: {len(ERR)} errori, {len(AVV)} avvisi")
for e in ERR:
    print("ERRORE:", e[:230])
for a in AVV:
    print("AVVISO:", a[:200])
sys.exit(1 if ERR else 0)
