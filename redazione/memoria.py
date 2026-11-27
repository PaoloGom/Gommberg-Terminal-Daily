"""Memoria della redazione: ciò che abbiamo già schedato e verificato nelle edizioni precedenti, pronto da riusare.
Legge redazione/fatti/AAAA-MM-GG.json (le schede archiviate da pubblica.sh) ed edizioni.json. Nessuna chiamata web.
Serve a due cose: la profondità (precedenti, cronologia, numeri già verificati di un tema) e il risparmio (un evento
d'agenda o un fatto di contesto già schedato non si cerca di nuovo).

Uso:
  python3 memoria.py riepilogo [AAAA-MM-GG]            una riga per prepara.sh
  python3 memoria.py agenda [AAAA-MM-GG] [--json F]    eventi futuri già schedati (ora, consenso, fonte)
  python3 memoria.py ultime [AAAA-MM-GG] [--file F]    la memoria delle ultime 5 edizioni (G-42): per ogni approfondimento
                                                       tema, titolo, tesi dichiarata, meccanismi spiegati, attacco; con
                                                       --file la scrive in F e stampa una riga per prepara.sh
  python3 memoria.py tema <parola> [<parola>...] [--giorni 45] [--json F]
                                                       fatti già schedati che contengono ALMENO una delle parole,
                                                       gli approfondimenti già usciti sul tema (da non ripetere) e i
                                                       meccanismi di meccanismi.json che spiegano il passaggio
--json F scrive le schede trovate, pronte da unire a fatti.json: id "MEM-<mmgg>-<id d'origine>", "ripresa" = edizione d'origine, esito del
revisore conservato. Una scheda ripresa vale come le altre per i controlli; nel testo è contesto, mai notizia del giorno.
Variabile: GTD_REPO (default /home/claude/gtd)."""
import ast, datetime as dt, glob, json, os, re, sys, unicodedata

REPO = os.environ.get("GTD_REPO", "/home/claude/gtd")
if not os.path.isdir(os.path.join(REPO, "redazione", "fatti")):
    REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
REGISTRI = {"anomalia", "prime_pagine", "ricerca", "scaletta"}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(s.split())


def archivio(dal, al=None):
    """[(giorno, scheda)] dal più recente, senza registri, scartate ed esiti negativi del revisore."""
    out = []
    for p in sorted(glob.glob(os.path.join(REPO, "redazione", "fatti", "20*.json")), reverse=True):
        try:
            g = dt.date.fromisoformat(os.path.basename(p)[:10])
            schede = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if g < dal or (al and g >= al):
            continue
        for s in schede:
            if (isinstance(s, dict) and s.get("testo") and s.get("data_evento") and s.get("fonti")
                    and s.get("sezione") not in REGISTRI and not s.get("scartata")
                    and s.get("verifica") in (None, "confermato") and not s.get("correzione")):
                out.append((g, s))
    return out


def testata(s):
    f = (s.get("fonti") or [{}])[0]
    return f.get("testata") or "?"


def unici(coppie):
    visti, out = set(), []
    for g, s in coppie:
        k = (s["data_evento"], norm(s["testo"])[:60])
        if k not in visti:
            visti.add(k); out.append((g, s))
    return out


def esporta(coppie, percorso):
    schede = []
    for g, s in coppie:
        c = dict(s); c["id"] = f"MEM-{g:%m%d}-{s.get('id', 'x')}"; c["ripresa"] = g.isoformat()
        schede.append(c)
    json.dump(schede, open(percorso, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Scritte {len(schede)} schede in {percorso}: uniscile a fatti.json (id MEM..), tieni solo quelle che usi")


def riga(g, s, k=190):
    t = " ".join(s["testo"].split())
    t = t if len(t) <= k else t[:k - 3] + "..."
    v = "verificata" if s.get("verifica") == "confermato" else "da riverificare se regge una tesi"
    return f"{s['data_evento'][8:]}/{s['data_evento'][5:7]} | {t} | {testata(s)}, ed. {g:%d/%m} | {v}"


def eventi_futuri(oggi):
    c = [(g, s) for g, s in archivio(oggi - dt.timedelta(days=10), oggi)
         if s.get("sezione") == "agenda" and s["data_evento"] >= oggi.isoformat()]
    return sorted(unici(c), key=lambda x: x[1]["data_evento"])


def approfondimenti(dal):
    try:
        voci = json.load(open(os.path.join(REPO, "edizioni.json"), encoding="utf-8"))
    except Exception:
        return []
    out = []
    for v in sorted(voci, key=lambda x: x["numero"], reverse=True):
        if v.get("data", "") < dal.isoformat():
            continue
        for a in v.get("approfondimenti") or []:
            out.append((v["numero"], v["data"], a.get("tema") or "", a.get("titolo") or ""))
    return out


def spiegati(oggi, quante=5):
    """In quali delle ultime edizioni è già spiegato ogni meccanismo: {"M23": ["2026-11-17", ...]}. Dalla stessa memoria
    che legge chi fa la scaletta (ultime(): meccanismi riconosciuti nel testo, G-42), così tema e memoria dicono lo
    stesso. Nato con G-36: nelle #026-#030 tre meccanismi erano usciti in 4 edizioni su 5, con le stesse parole."""
    out = {}
    for v in ultime(oggi, quante):
        for m in v["meccanismi"]:
            if v["data"] not in out.setdefault(m, []):
                out[m].append(v["data"])
    return out


def meccanismi(parole, quanti=2):
    """I meccanismi di meccanismi.json che toccano il tema: la spiegazione già verificata del passaggio (perché A muove B),
    da dire con le parole del lettore. Prima quelli col tema nel titolo, poi per numero di parole trovate."""
    try:
        voci = json.load(open(os.path.join(REPO, "redazione", "meccanismi.json"), encoding="utf-8"))["voci"]
    except Exception:
        return []
    trovati = []
    for v in voci:
        tit, base = norm(v["titolo"]), norm(" ".join(v.get(k, "") for k in ("titolo", "testo", "quando")))
        n = sum(1 for p in parole if p in base)
        if n:
            trovati.append((-sum(1 for p in parole if p in tit), -n, v["id"], v))
    return [v for *_, v in sorted(trovati, key=lambda x: x[:3])[:quanti]]


# ---------------------------------------------------------------- la memoria delle ultime edizioni (G-42, 27/11/2026)
# La misura del 25/11 (collaudi/2026-11-25/g42/misura.md): il giornale non si ripete nelle frasi (4% della prosa) ma nelle
# tesi e nelle spiegazioni (l'oro che non fa da rifugio in 7 edizioni su 8, il petrolio che guarda al surplus in 6, "il
# prezzo sale e il rendimento scende" rispiegato quattro volte). Chi fa la scaletta, e poi il desk, vede gli
# approfondimenti delle ultime 5 edizioni: tema, titolo, tesi, meccanismi spiegati, attacco. Tutto dal codice, dai
# sorgenti archiviati (redazione/sorgenti/AAAA-MM-GG/edizione.py letto senza eseguirlo, con le riscritture del desk
# applicate come le applica il modello): zero token, nessun riassunto di un modello. Un sorgente che manca o non si legge
# toglie la sua edizione, mai un errore.
#
# I meccanismi si riconoscono nel testo, non solo nell'elenco dichiarato (C["meccanismi"] è dell'edizione intera e spesso
# manca il passaggio spiegato davvero: "il prezzo sale e il rendimento scende" il 17 e il 18/11 non era dichiarato).
# Un meccanismo è spiegato in un pezzo se una sua frase ha tutte le parole di una delle combinazioni qui sotto (testo
# senza accenti e in minuscolo). Le combinazioni sono tarate sulle edizioni dal 16 al 27/11.
SEGNI = {
    "M01": [[r"prezz", r"rendiment", r"contrario|oppost|sale,? e il rendimento|scende,? e il rendimento"]],
    "M02": [[r"10 anni", r"(guarda|segue|dipende|include|conta)\w*\b.{0,60}(crescita|inflazione|prezzi)"]],
    "M03": [[r"curva", r"invertit"]],
    "M04": [[r"sorpres|scarto|differenza", r"attes"], [r"gia nei prezzi|gia nel prezzo|messo nel prezzo|messi nei prezzi"]],
    "M05": [[r"inflazion|prezzi", r"sopra le attese", r"tass|rendiment"]],
    "M06": [[r"\butili|\bmargini", r"futur|lontan|domani|tra qualche anno|tra molti anni", r"\bval|\bpaga|scont|prezzo"]],
    "M07": [[r"correlazion"], [r"azion|borsa", r"titoli di stato|rendiment", r"stessa direzione|direzioni opposte|stesso verso"]],
    "M08": [[r"dollaro", r"(differenz|divario).{0,30}(tass|rendiment)"]],
    "M09": [[r"dollar|yen|franco svizzero", r"rifugio|paura", r"compra|cerca|attira"]],
    "M10": [[r"petrolio|greggio|barile|carburant|benzina", r"inflazion|prezzi al consumo"]],
    "M11": [[r"petrolio|greggio|baril[ei]", r"offerta|domanda|surplus|ne arrivano|ne servono|ce n'e|troppo"]],
    "M12": [[r"backwardation|contango|consegna vicina|consegna lontana"]],
    "M13": [[r"spread", r"btp|bund"]],
    "M14": [[r"\bvix\b", r"misura|paura|volatilita attesa|opzioni"]],
    "M15": [[r"attese|stime|guidance|previsioni", r"conti|trimestral|risultat|ricavi", r"batt|sopra|delud|non bast"]],
    "M16": [[r"composizion"], [r"indic|listino", r"\bpesa|\bpesano|ponderat|una media|dimension", r"societa|titoli|aziende"],
            [r"russell 2000", r"piccol"]],
    "M17": [[r"kospi|taiwan|taipei|seul|corea", r"chip|semicondutt|samsung|sk hynix", r"\bpes|una parte|in linea|sera prima"]],
    "M18": [[r"\byen\b", r"nikkei"]],
    "M19": [[r"lavoro|occupat|buste paga|disoccupaz", r"tass|rendiment"]],
    "M20": [[r"probabilit", r"future", r"scommess|non (sono )?previsioni|ricavat"]],
    "M21": [[r"banche", r"margin|interess", r"tass"]],
    "M22": [[r"\basta\b", r"domanda|coda|rendiment"]],
    "M23": [[r"\boro\b|metallo", r"non paga|non rende|non da (niente|nulla|interessi)|non incass|interessi"]],
    "M24": [[r"\bdazi", r"cost|margin|import"]],
    "M25": [[r"future", r"apertura|stanotte|prima dell", r"anticip|previsione"]],
    "M26": [[r"2 anni", r"(segue|riflette|guarda|legat)\w*\b.{0,60}(attese|fed|banca centrale|tassi)"]],
    "M27": [[r"rendimento reale|\btips\b|breakeven|inflazione attesa|attese di inflazione"]],
    "M28": [[r"commission|intermedia|trading", r"volum|scambi"]],
}
DICHIARATA = re.compile(r"\b(a nostro avviso|per noi|leggiamo|crediamo|secondo noi|la nostra lettura)\b", re.I)
QUANTE = 5


def frasi(t):
    t = re.sub(r"<[^>]+>|\[\[\w+\]\]", " ", str(t or ""))
    return [f.strip() for f in re.split(r"(?<=[.?!])\s+", " ".join(t.split())) if f.strip()]


def riconosci(testi):
    """Gli id dei meccanismi spiegati in questi testi (vedi SEGNI), in ordine di id."""
    fr = [norm(f).replace("’", "'") for t in testi for f in frasi(t)]
    return [m for m, alternative in SEGNI.items()
            if any(all(re.search(p, f) for p in alt) for alt in alternative for f in fr)]


def _moduli_sorgente(path):
    """(meccanismi dichiarati, [moduli]) dal file dell'edizione, letto senza eseguirlo; di ogni modulo solo i campi
    scritti come testo (il resto, grafici compresi, si salta). None se il file manca, non si legge o non ha C."""
    try:
        albero = ast.parse(open(path, encoding="utf-8").read())
    except (OSError, SyntaxError, ValueError):
        return None
    for n in albero.body:
        if isinstance(n, ast.Assign) and any(getattr(x, "id", "") == "C" for x in n.targets) and isinstance(n.value, ast.Dict):
            dich, mods = [], []
            for k, v in zip(n.value.keys, n.value.values):
                chiave = getattr(k, "value", None)
                if chiave == "meccanismi":
                    try:
                        dich = [x for x in ast.literal_eval(v) if isinstance(x, str)]
                    except (ValueError, TypeError, SyntaxError):
                        pass
                elif chiave == "moduli" and isinstance(v, ast.List):
                    for m in v.elts:
                        if not isinstance(m, ast.Dict):
                            continue
                        x = {}
                        for mk, mv in zip(m.keys, m.values):
                            if isinstance(mk, ast.Constant) and mk.value in ("chiave", "tema", "titolo", "perche", "quindi",
                                                                             "testo", "punti"):
                                try:
                                    x[mk.value] = ast.literal_eval(mv)
                                except (ValueError, TypeError, SyntaxError):
                                    pass
                        if x.get("chiave") and isinstance(x.get("titolo"), str):
                            mods.append(x)
            return dich, mods
    return None


def _desk(mods, path):
    """Le riscritture del desk accettate quel giorno, applicate come le applica il modello (solo dove il testo è ancora
    quello che il desk aveva letto): la memoria è ciò che il lettore ha letto."""
    try:
        ok = json.load(open(path, encoding="utf-8"))
    except Exception:
        return
    per = {m["chiave"]: m for m in mods}
    for e in ok if isinstance(ok, list) else []:
        try:
            p = e["campo"].split(".")
            m = per.get(p[1]) if p[0] == "moduli" else None
            if not m:
                continue
            if len(p) == 4 and isinstance(m.get(p[2]), list) and m[p[2]][int(p[3])] == e["originale"]:
                m[p[2]][int(p[3])] = e["testo"]
            elif len(p) == 3 and m.get(p[2]) == e["originale"]:
                m[p[2]] = e["testo"]
        except (KeyError, IndexError, ValueError, TypeError, AttributeError):
            continue


def _tesi(m):
    """La tesi in una riga: la frase del Perché che dichiara la nostra lettura. Se non c'è, il pezzo riporta la lettura di
    altri e la sua tesi è il titolo: niente riga in più."""
    return next((f for f in frasi(m.get("perche")) if DICHIARATA.search(f)), "")


def scheda_modulo(m):
    testo = [t for t in (m.get("testo") or []) if isinstance(t, str)]
    return {"chiave": m.get("chiave"), "tema": str(m.get("tema") or m.get("chiave")), "titolo": m["titolo"],
            "tesi": _tesi(m), "apre": (frasi(testo[0]) or [""])[0] if testo else "",
            "meccanismi": riconosci([m.get("perche"), m.get("quindi")] + testo +
                                    [p for p in (m.get("punti") or []) if isinstance(p, str)])}


def ultime(oggi, quante=QUANTE, repo=None):
    """La memoria: [{"data", "numero", "chiave", "tema", "titolo", "tesi", "apre", "meccanismi"}] degli approfondimenti
    delle ultime `quante` edizioni uscite prima di oggi che hanno il sorgente, dalla più vecchia."""
    repo = repo or REPO
    try:
        numeri = {v["data"]: v["numero"] for v in json.load(open(os.path.join(repo, "edizioni.json"), encoding="utf-8"))}
    except Exception:
        numeri = None
    giorni = []
    for p in sorted(glob.glob(os.path.join(repo, "redazione", "sorgenti", "20*", "edizione.py")), reverse=True):
        d = os.path.basename(os.path.dirname(p))
        if d >= oggi.isoformat() or (numeri is not None and d not in numeri):
            continue
        letto = _moduli_sorgente(p)
        if not letto or not letto[1]:
            continue
        _desk(letto[1], os.path.join(os.path.dirname(p), "desk_ok.json"))
        giorni.append((d, letto[1]))
        if len(giorni) == quante:
            break
    out = []
    for d, mods in reversed(giorni):
        for m in mods:
            try:
                out.append(dict(scheda_modulo(m), data=d, numero=(numeri or {}).get(d)))
            except Exception:  # noqa: BLE001 - un modulo scritto male toglie sé stesso, non la memoria
                continue
    return out


def _gm(d):
    return f"{d[8:]}/{d[5:7]}"


def _taglia(s, k):
    s = " ".join(str(s).split())
    return s if len(s) <= k else s[:k - 3].rsplit(" ", 1)[0] + "..."


def _date(giorni):
    """"17, 19, 23/11": i giorni, con il mese una volta sola se è lo stesso."""
    g = sorted(giorni)
    if len({d[:7] for d in g}) == 1:
        return ", ".join(d[8:] for d in g[:-1]) + (", " if len(g) > 1 else "") + _gm(g[-1])
    return ", ".join(_gm(d) for d in g)


def testo_memoria(voci, titoli_mecc=None):
    """La memoria come la legge chi scrive: due righe di conteggi (temi e meccanismi tornati) e una riga per pezzo."""
    if not voci:
        return "Memoria delle ultime edizioni: nessun sorgente archiviato leggibile, nessun vincolo da qui."
    if titoli_mecc is None:
        try:
            titoli_mecc = {v["id"]: v["titolo"] for v in
                           json.load(open(os.path.join(REPO, "redazione", "meccanismi.json"), encoding="utf-8"))["voci"]}
        except Exception:
            titoli_mecc = {}
    date = sorted({v["data"] for v in voci})
    temi, mecc = {}, {}
    for v in voci:
        temi.setdefault(v["tema"], set()).add(v["data"])
        for m in v["meccanismi"]:
            mecc.setdefault(m, set()).add(v["data"])
    tornati = lambda d: sorted(((k, g) for k, g in d.items() if len(g) > 1), key=lambda x: (-len(x[1]), x[0]))
    righe = [f"Memoria delle ultime {len(date)} edizioni ({_date(date)}), §3.3: tema | titolo | tesi dichiarata | "
             "meccanismi spiegati | attacco.",
             "Temi tornati: " + ("; ".join(f"{t} ({_date(g)})" for t, g in tornati(temi)) or "-"),
             "Meccanismi spiegati più volte: " + ("; ".join(f"{m} {titoli_mecc.get(m, '')} ({_date(g)})"
                                                          for m, g in tornati(mecc)) or "-")]
    for v in voci:
        righe.append(f"{_gm(v['data'])} {v['tema']} | {v['titolo']} | {_taglia(v['tesi'], 120) or '-'} | "
                     f"{', '.join(v['meccanismi']) or '-'} | {_taglia(v['apre'], 75) or '-'}")
    return "\n".join(righe)


PIENE = re.compile(r"[a-z]{5,}|\b(?:oro|fed|bce|btp|pil)\b")
VUOTE_T = set("della delle degli dello dalla dalle dagli sulla sulle sugli nella nelle negli anche ancora quando "
              "perche mentre contro senza prima dopo oltre resta restano tutti tutte quasi molto mercato mercati borsa "
              "borse sopra sotto prezzo prezzi titolo titoli".split())
# parole che non dicono di che cosa parla un attacco: articoli, preposizioni, domande, avverbi di tempo
LEGGERE = set("il lo la i gli le l un una uno un' di del della dei a al alla da dal in nel nella con su sul per tra fra e "
              "ed ma o se non piu anche gia ancora come cosa chi quale quanto perche quando mentre dopo prima oggi ieri "
              "puo possono e' c'e sono prezzo prezzi".split())


def _piene(t):
    return {w[:6] for w in PIENE.findall(norm(t)) if w not in VUOTE_T}


def _soggetto(t):
    """La prima parola che dice di che cosa parla l'attacco ("L'oro cade..." e "L'oro, il rifugio..." aprono tutti e due
    sull'oro): due attacchi sullo stesso soggetto, nella memoria, sono lo stesso modo di aprire."""
    return next((w for w in re.findall(r"[a-z]+", norm(t)) if w not in LEGGERE and len(w) > 2), "")


def segnala(m, voci):
    """Che cosa un pezzo di oggi riprende dalla memoria (per il desk): meccanismi già spiegati, tema o titolo vicini,
    attacco con le stesse prime parole. Solo segnalazioni: decide chi legge, il codice non blocca nulla."""
    s = scheda_modulo(m)
    out = []
    for mid in s["meccanismi"]:
        g = sorted({v["data"] for v in voci if mid in v["meccanismi"]})
        if g:
            out.append(f"{mid} già spiegato il {_date(g)}")
    tit = _piene(s["titolo"])
    for v in voci:
        comuni = tit & _piene(v["titolo"])
        if len(comuni) >= 2 or (v["chiave"] == s["chiave"] and comuni):
            out.append(f"titolo vicino al {_gm(v['data'])} «{v['titolo']}»")
    for v in voci:
        if _soggetto(s["apre"]) and _soggetto(s["apre"]) == _soggetto(v["apre"]):
            out.append(f"apre come il {_gm(v['data'])} «{_taglia(v['apre'], 70)}»")
    return out


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    js = a[a.index("--json") + 1] if "--json" in a else None
    fi = a[a.index("--file") + 1] if "--file" in a else None
    giorni = int(a[a.index("--giorni") + 1]) if "--giorni" in a else 45
    for opz in ("--json", "--giorni", "--file"):
        if opz in a:
            i = a.index(opz); del a[i:i + 2]
    cmd, resto = a[0], a[1:]
    date = [x for x in resto if len(x) == 10 and x[4] == "-" and x[7] == "-"]
    oggi = dt.date.fromisoformat(date[0]) if date else dt.date.today()

    if cmd == "riepilogo":
        ev = eventi_futuri(oggi)
        print(f"Memoria: {len(ev)} eventi futuri già schedati (memoria.py agenda) | per ogni tesi: memoria.py tema <parole> "
              "| storie in corso: memoria.py storie")
    elif cmd == "storie":
        voci = json.load(open(os.path.join(REPO, "edizioni.json"), encoding="utf-8"))
        prec = [v for v in voci if v.get("data", "") < oggi.isoformat() and v.get("termometri")]
        if not prec:
            print("Memoria, storie in corso: nessun termometro archiviato: si scrivono da zero"); return
        v = prec[-1]
        print(f"Memoria, storie in corso (termometri del n. {v['numero']}, {v['data']}): si aggiornano, non si "
              "riscrivono; una storia ferma da 3 edizioni va in 'fermi', poi esce:")
        for r in v["termometri"].get("righe", []):
            print("  " + " | ".join(r))
        if v["termometri"].get("fermi"):
            print("  Fermi: " + v["termometri"]["fermi"])
    elif cmd == "agenda":
        ev = eventi_futuri(oggi)
        if not ev:
            print("Memoria, agenda: nessun evento futuro già schedato: il calendario si cerca per intero"); return
        print(f"Memoria, agenda: {len(ev)} eventi futuri già schedati. Si riusano; si cerca solo ciò che manca "
              "(consenso, ora esatta, eventi nuovi):")
        for g, s in ev[:16]:
            print("  " + riga(g, s, 150))
        if js:
            esporta(ev, js)
    elif cmd == "ultime":
        voci = ultime(oggi)
        t = testo_memoria(voci)
        if not fi:
            print(t); return
        open(fi, "w", encoding="utf-8").write(t + "\n")
        if not voci:
            print(t); return
        conta = {}
        for v in voci:
            for m in v["meccanismi"]:
                conta.setdefault(m, set()).add(v["data"])
        piu = sorted(((m, len(g)) for m, g in conta.items() if len(g) > 1), key=lambda x: (-x[1], x[0]))
        print(f"Memoria delle ultime {len({v['data'] for v in voci})} edizioni (§3.3): leggila prima della scaletta, {fi} "
              f"({len(voci)} pezzi) | meccanismi spiegati più volte: " + (", ".join(f"{m} x{n}" for m, n in piu[:6]) or "-"))
    elif cmd == "tema":
        parole = [norm(x) for x in resto if x not in date]
        if not parole:
            print("Uso: memoria.py tema <parola> [<parola>...]"); return
        dal = oggi - dt.timedelta(days=giorni)
        trovati = []
        for g, s in archivio(dal, oggi):
            if s.get("sezione") == "agenda":
                continue
            base = norm(s["testo"] + " " + " ".join(f.get("citazione") or "" for f in s.get("fonti") or []))
            if any(p in base for p in parole):
                trovati.append((g, s))
        trovati = sorted(unici(trovati), key=lambda x: x[1]["data_evento"], reverse=True)
        usciti = [x for x in approfondimenti(dal) if any(p in norm(x[2] + " " + x[3]) for p in parole)]
        if usciti:
            print("Già scritto (§3.3):")
            for n, d, t, tit in usciti[:5]:
                print(f"  #{n:03d} {d[8:]}/{d[5:7]} {t}: {tit}")
        mecc = meccanismi(parole)
        if mecc:
            gia = spiegati(oggi)
            print("Meccanismi che POSSONO servire al passaggio (meccanismi.json). Si usa solo quello che spiega QUESTA tesi, "
                  "con le parole del lettore e come tendenza; uno che non c'entra o che va contro la tesi confonde: meglio "
                  "nessuno. Uno GIÀ SPIEGATO nelle ultime edizioni: §3.3. L'id di quelli usati va in C[\"meccanismi\"]:")
            for v in mecc:
                ecc = v.get("eccezioni", "-")
                dove = gia.get(v["id"])
                print(f"  {v['id']} {v['titolo']}" + (" - GIÀ SPIEGATO il " + _date(dove) if dove else "")
                      + f" (serve per: {v.get('quando', '-')[:90]}): {v['testo'][:240]} | Non vale se: "
                      f"{ecc[:120]}{'...' if len(ecc) > 120 else ''}")
        if not trovati:
            print("Memoria, tema: nessun fatto già schedato con queste parole"); return
        print(f"Memoria, tema: {len(trovati)} fatti già schedati (i più recenti prima). Sono contesto e precedenti, "
              "mai la notizia di oggi:")
        for g, s in trovati[:14]:
            print("  " + riga(g, s))
        if js:
            esporta(trovati[:14], js)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
