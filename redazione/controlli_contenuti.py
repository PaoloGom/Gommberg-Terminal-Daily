"""Controlli editoriali (BLOCCANTI salvo AVVISO) sul PDF e sui file del giorno. Uso:
  python3 controlli_contenuti.py <pdf> [--voce voce_indice.json] [--dati dati.json] [--fatti fatti.json] [--repo /home/claude/gtd]
Regole (ISTRUZIONI §5 e §7), ognuna generale:
 estremi   ogni indice principale in dati.json (obbligatori: S&P 500, Nasdaq, Euro Stoxx 50, Nikkei 225, Kospi, Hang Seng)
           con |var| >= 3% compare con la sua cifra nel PDF; un obbligatorio assente da dati.json = ERRORE.
 perche    PERCHÉ = causa con fonte ("secondo"), meccanismo ("di solito", "in genere") o "causa non chiarita";
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
SCHEDE = [f for f in FATTI if isinstance(f, dict) and f.get("sezione") != "anomalia" and not f.get("scartata")]
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
        if not any(re.search(r"(?<![\d,])[+-]?" + re.escape(c) + r"\s?%", TUTTO) for c in cand):
            ERR.append(f"estremi: {k} {var:+.2f}% (movimento oltre il 3%) non compare nel PDF: va citato con la cifra")

# ---------- perche / quindi (B6) ----------
OSSERVABILE = re.compile(r"\d+(?:[.,]\d+)?\s?(?:%|pb|\$|€|mld|mila|punti)|\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+,\d+|"
                         r"\b\d{1,2}[:/]\d{2}\b|\b\d{1,2} (?:" + MESI + r")\b|\b(?:" + GIORNI + r")\b|→ ?pag", re.I)
CAUSA = re.compile(r"\bsecondo\b|di solito|in genere|causa non chiarita|\bM\d{2}\b", re.I)
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
                   "(anomalia) scrivi 'causa non chiarita' + cosa guardare, o la spiegazione attribuita")
    elif not CAUSA.search(p):
        ERR.append(f"perche: modulo {nome}: serve la causa con fonte ('secondo X'), un meccanismo o 'causa non chiarita': \"{p[:70]}\"")
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
        if not a.get("ricerche") or not (a.get("esito") == "non chiarita" or a.get("esito") in ids_c):
            ERR.append(f"anomalie: voce {a.get('id')} incompleta: servono 'ricerche' (le query) ed 'esito' = id di una scheda C o \"non chiarita\"")
    if anomale and not registro:
        ERR.append(f"anomalie: fatto controintuitivo ({anomale[0][:90]}) senza registro: aggiungi a fatti.json "
                   "{\"id\": \"A1\", \"sezione\": \"anomalia\", \"fatto\": ..., \"ricerche\": [...], \"esito\": \"C0x\" | \"non chiarita\"}")

# ---------- stamattina (P10) ----------
def blocco_stamattina(raw):
    m = re.search(r"\nSTAMATTINA\n(.*?)(?:\n[A-ZÀÈÌÒÙ][A-ZÀÈÌÒÙ0-9 '&/.,-]{3,}\n|\f)", raw, re.S)
    return [re.sub(r"\s+", " ", x) for x in re.split(r"\n\s*\n", m.group(1))] if m else []


stam = VOCE.get("stamattina") or blocco_stamattina(RAW)
for s in stam:
    ore = re.findall(r"\b(\d{1,2})[:.](\d{2})\b", s)
    for h, mi in ore:
        if not (6 <= int(h) < 9 or (int(h) == 9 and int(mi) < 30)):
            ERR.append(f"stamattina: orario {h}:{mi} fuori dalla finestra 06:00-09:29: \"{s[:70]}\"")
try:
    ed = carica(os.path.join(REPO, "edizioni.json")) or []
    prec = max((v for v in ed if v["numero"] < VOCE.get("numero", 10 ** 6)), key=lambda v: v["numero"], default=None)
    if prec and os.path.exists(os.path.join(REPO, prec["file"])):
        livelli = lambda xs: set(re.findall(r"\d{1,3}(?:\.\d{3})*,\d{2,4}", " ".join(xs)))
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
