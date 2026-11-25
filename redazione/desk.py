"""Desk: la riscrittura per il lettore, dopo la revisione dei fatti (v8.3, 13/11/2026; G-45, 24/11/2026).

Chi verifica i fatti non è chi sistema la prosa. Il desk riscrive titoli, attacchi e testi per renderli più chiari, ma
non può aggiungere fatti: il codice accetta una riscrittura solo se non porta cifre, nomi o fonti nuove e se resta
non più lunga del 10% (e non più corta del 40%). Né può spostarne o toglierne: una cifra resta sul suo soggetto, e una
frase che porta un fatto che nessun altro campo dice non sparisce. Né può far scattare un controllo di Coerenza che il
testo di prima passava (cifre e versi contro dati.json, rimandi, ipotesi nei titoli). Una proposta respinta lascia il
testo com'era: il desk non blocca mai.

Uso (cartella di lavoro):
  python3 desk.py estrai <edizione.py>     -> desk_incarico.json  [{"campo", "testo"}]  (lo riceve l'agente desk)
  (l'agente scrive desk_proposta.json      -> [{"campo", "testo"}], solo i campi che migliora)
  python3 desk.py verifica <edizione.py>   -> desk_ok.json (accettate) e l'elenco delle respinte col motivo
Il modello applica desk_ok.json da solo al rendering, e solo ai campi rimasti come il desk li ha letti.
"""
import importlib.util
import json
import os
import re
import sys

INC, PRO, OK = "desk_incarico.json", "desk_proposta.json", "desk_ok.json"


def campi(C):
    """I testi che il desk può riscrivere, con un indirizzo stabile."""
    out = {}
    t = C.get("top") or {}
    for k in ("titolo", "dek"):
        if t.get(k):
            out[f"top.{k}"] = t[k]
    if C.get("quadro"):
        out["quadro"] = C["quadro"]
    for i, x in enumerate(C.get("in30") or []):
        out[f"in30.{i}"] = x
    for i, n in enumerate(C.get("notizie") or []):
        for k in ("titolo", "testo"):
            if isinstance(n, dict) and n.get(k):
                out[f"notizie.{i}.{k}"] = n[k]
    for i, a in enumerate(C.get("agenda") or []):
        if len(a) > 3 and "<b>" not in str(a[3]):
            out[f"agenda.{i}.perche"] = a[3]
    for m in C.get("moduli") or []:
        c = m.get("chiave")
        for k in ("titolo", "perche", "quindi", "numero", "guardare"):
            if m.get(k):
                out[f"moduli.{c}.{k}"] = m[k]
        for k in ("testo", "punti"):
            for j, x in enumerate(m.get(k) or []):
                out[f"moduli.{c}.{k}.{j}"] = x
    return out


def imposta(C, campo, testo):
    p = campo.split(".")
    if p[0] == "top":
        C["top"][p[1]] = testo
    elif p[0] == "quadro":
        C["quadro"] = testo
    elif p[0] == "in30":
        C["in30"][int(p[1])] = testo
    elif p[0] == "notizie":
        C["notizie"][int(p[1])][p[2]] = testo
    elif p[0] == "agenda":
        a = list(C["agenda"][int(p[1])]); a[3] = testo; C["agenda"][int(p[1])] = tuple(a)
    elif p[0] == "moduli":
        m = next(x for x in C["moduli"] if x.get("chiave") == p[1])
        if len(p) == 4:
            m[p[2]][int(p[3])] = testo
        else:
            m[p[2]] = testo


def applica(C, cartella="."):
    """Chiamata dal modello prima del rendering."""
    p = os.path.join(cartella, OK)
    if not os.path.exists(p):
        return 0
    attuali, n = campi(C), 0
    for e in json.load(open(p, encoding="utf-8")):
        if attuali.get(e["campo"]) == e["originale"]:
            imposta(C, e["campo"], e["testo"]); n += 1
    print(f"Desk: {n} riscritture applicate")
    return n


NUM = re.compile(r"\d+(?:[.,]\d+)*")
RIMANDO = re.compile(r"\[\[\w+\]\]")
# Una cifra con la sua unità (o col segno): è di qualcuno, e la riscrittura non può dargliene un altro (G-45: nella prova
# del 23/11 "il listino tecnologico di Hong Kong (-3,8%)" era diventato "Hong Kong perde il 3,8%", con l'Hang Seng a -1,9%).
CIFRA = re.compile(r"([+\-−]?)(\d+(?:[.,]\d+)*)\s?(%|pb\b|punti|\$|dollari|euro|miliardi|milioni)")

# ---------------------------------------------------------------- di chi è una cifra (G-45, rifatta il 25/11/2026)
# Non si ricostruisce la sintassi (due versioni a catena di parole sbagliavano ai bordi nei due sensi): si guarda il nome
# a cui la cifra è attaccata, il suo "proprietario", e se ne prende la testa, cioè la parola che dice CHE COSA ha fatto la
# cifra ("il listino tecnologico di Hong Kong": listino tecnologico; "le banche nel listino di Milano": banche; "il rame
# e l'argento": rame e argento). Due regole, una per ogni modo di spostare una cifra:
#  - la testa non sparisce: deve restare nel proprietario della cifra nella riscrittura ("Hong Kong perde il 3,8%" perde
#    "listino tecnologico", "Il listino di Milano perde il 2,4%" perde "banche"). Se nella testa c'è un nome proprio basta
#    quello ("il petrolio Brent" -> "il Brent"); le parole del movimento e della misura (rimbalzo, calo, rendimento,
#    prezzo...) non sono la testa ("il rimbalzo dell'oro (+3,9%)" -> "l'oro rimbalza del 3,9%");
#  - la cifra non passa a un altro: il proprietario nella riscrittura non porta parole che nell'originale c'erano ma
#    appartenevano ad altro ("L'oro guadagna il 2,1% e l'argento il 3,4%" -> "L'argento guadagna il 2,1%...").
# I mercati di dati.json hanno in più il confronto con il valore calcolato (controlli_coerenza.py, in verifica).
ARTICOLI = set("il lo la i gli le l un una uno".split())
PREPOSIZIONI = set("di del della dello dei degli delle dell d a al alla allo ai agli alle all ad da dal dalla dallo dai dagli "
                   "dalle dall in nel nella nello nei negli nelle nell su sul sulla sullo sui sugli sulle sull con col per "
                   "tra fra verso contro sopra sotto".split())
COORD = {"e", "ed", "o"}
LEGAMI = ARTICOLI | PREPOSIZIONI | COORD | set("anche circa quasi oltre più meno poco ciascuna ciascuno entrambi entrambe "
                                               "tutti tutte ben solo appena già ancora dopo prima ieri oggi stamattina "
                                               "ora poi".split())
# congiunzioni che aprono un'altra proposizione: chiudono il gruppo ("Tokyo, dove Toyota perde il 5%": la cifra è di Toyota)
CONFINI = set("mentre ma però perché dove quando se poiché invece cioè".split())
# parole del movimento, della misura e del contenitore: dicono come, quanto o in che forma, non chi ("le azioni di Novo
# Nordisk" sono Novo Nordisk, "l'indice dei prezzi" sono i prezzi)
MISURA = re.compile(r"^(?:azion[ei]|titol[oi]|indic[ei]|compart[oi]|settor[ei]|rialz[oi]|ribass[oi]|cal[oi]|rimbalz[oi]|"
                    r"croll[oi]|aument[oi]|crescita|salita|discesa|perdit[ae]|"
                    r"guadagn[oi]|bals[oi]|flession[ei]|progress[oi]|cadut[ae]|tonf[oi]|risalita|recuper[oi]|variazion[ei]|"
                    r"rendiment[oi]|prezz[oi]|quotazion[ei]|valor[ei]|livell[oi]|seduta|giornata)$")
# verbi (anche congiuntivo, futuro, participio): chiudono il gruppo del soggetto
VERBI = re.compile(r"^(?:(?:perd|cal|scend|ced|guadagn|crol|risal|rimbalz|arretr|chiud|avanz|cresc|tocc|segn|lasc|pes|"
                   r"tras?cin|spin|frena|sostien|rest|pass|port|registr|vol|torn|affond|scivol|ripieg|fless|recuper|"
                   r"sal)(?:e|a|ano|ono|ino|ava|avano|eva|evano|erà|eranno|irà|iranno|ato|ata|ati|ate|uto|uta|"
                   r"so|sa|si|se|ito|ita|endo|ando|gono|go|ga|gano|isce|iscono|ta|to|ti)|"
                   r"pers[oaie]|sces[oaie]|fanno|fa|ha|hanno|è|sono|era|erano|sarà|vale|valgono|rende|rendono|supera|"
                   r"superano)$")
# unità di misura dopo una cifra: non sono un proprietario ("sale di 5 pb al 2,71%")
UNITA = set("pb punti base dollari euro miliardi milioni cento".split())
STOP = {",", ";", ":", ".", "?", "!"}


def _parole(t):
    """Le parole del testo con la maiuscola com'è (serve a riconoscere i nomi propri)."""
    t = re.sub(r"<[^>]+>|\[\[\w+\]\]", " ", t).replace("'", " ").replace("’", " ")
    return re.findall(r"[A-Za-zÀ-ÿ&]+|[(),;:.?!]|\d+(?:[.,]\d+)*", t)


def _radice(w):
    w = w.lower()
    return w[:5] if len(w) > 6 else (re.sub(r"[aeiouhàèéìòù]+$", "", w) or w)


def _piena(w):
    lw = w.lower()
    return lw not in LEGAMI and lw not in CONFINI and not lw[0].isdigit() and not MISURA.match(lw) and \
        not VERBI.match(lw) and lw != "che" and lw not in STOP and lw not in "()"


def _prima(pp):
    """Il gruppo del proprietario risalendo dalla cifra: le parole (in ordine) fino all'articolo che lo apre, al verbo o alla
    punteggiatura. Un verbo subito prima della cifra ("Hong Kong perde il 3,8%") si salta; "X, che perde il 3,8%" porta a X;
    "il rame e l'argento" e "DRAM e NAND" sono un soggetto solo; una parentesi già chiusa è un inciso e si salta."""
    out, k, piene, rel, coord = [], len(pp) - 1, 0, False, None
    while k >= 0:
        w = pp[k]; lw = w.lower()
        if lw == ")":
            while k >= 0 and pp[k] != "(":
                k -= 1
            k -= 1; continue
        if lw == "(":
            k -= 1; continue
        if lw in STOP:
            # "...di Hong Kong: -3,8%" e "Milano, che perde": la punteggiatura subito prima non chiude il gruppo
            if not piene and (lw == ":" or rel):
                k -= 1; continue
            if not piene and lw == ",":
                # "Il decennale, dopo i dati, sale al 4,2%" e "Hong Kong, con il suo listino tecnologico, perde il 3,8%":
                # l'inciso tra due virgole si salta e il soggetto è prima. Se l'inciso apre con un articolo o un nome è
                # un'apposizione, lo stesso soggetto detto in un altro modo ("L'indice della paura, il VIX, scende del
                # 12%"): conta anche lui
                j = max([i for i in range(k) if pp[i] == ","] or [-1])
                if j >= 0 and not any(x in STOP - {","} for x in pp[j:k]):
                    inciso = pp[j + 1:k]
                    if inciso and (inciso[0].lower() in ARTICOLI or inciso[0][:1].isupper()):
                        out = inciso + out
                        piene += sum(_piena(x) for x in inciso)
                    k = j - 1; continue
                k -= 1; continue
            break
        if piene >= 8:
            break
        if coord and (lw[0].isdigit() or VERBI.match(lw)):
            out = out[len(out) - coord:]; break             # "...a 129.902 immatricolazioni e la quota": non è doppio
        if VERBI.match(lw) and not MISURA.match(lw):
            if piene:
                break
            k -= 1; continue
        if lw == "che":
            if piene:
                break
            rel = True; k -= 1; continue
        if lw in CONFINI:
            if piene:
                break
            k -= 1; continue
        if lw in UNITA and k > 0 and (pp[k - 1][0].isdigit() or pp[k - 1].lower() in UNITA):
            k -= 1
            while k >= 0 and (pp[k][0].isdigit() or pp[k].lower() in UNITA):
                k -= 1                                      # un'altra cifra con la sua unità: non è un nome
            continue
        if lw in ARTICOLI and piene:
            if k > 1 and pp[k - 1].lower() in COORD and _piena(pp[k - 2]):
                out.insert(0, w); k -= 1; coord = len(out); continue    # "il rame e l'argento"
            out.insert(0, w); break
        if lw in COORD and piene:
            dopo = pp[k + 1] if k + 1 < len(pp) else ""
            if not (dopo.lower() in ARTICOLI or dopo[:1].isupper()):
                break                                       # "...in Europa e a ottobre immatricola": un'altra proposizione
        out.insert(0, w)
        piene += _piena(w)
        k -= 1
    return out


def _dopo(pp):
    """Quando la cifra apre la frase ("-3,8% per il listino tecnologico di Hong Kong", "Il 3,8% perso dal listino..."): il
    proprietario è il gruppo che segue, fino alla punteggiatura o al verbo."""
    out = []
    for w in pp:
        lw = w.lower()
        if lw in STOP or lw in "()" or lw == "che" or lw in CONFINI or len(out) >= 10:
            break
        if VERBI.match(lw) and not MISURA.match(lw):
            if any(_piena(x) for x in out):
                break
            continue
        out.append(w)
    return out


def proprietario(t, m):
    """Le parole del gruppo a cui è attaccata la cifra m (un match di CIFRA in t)."""
    g = _prima(_parole(t[:m.start()]))
    if not any(_piena(w) for w in g):
        g = _dopo(_parole(t[m.end():]))
    return g


def testa(g):
    """La testa del gruppo: dalla prima parola piena fino alla prima preposizione (le coordinate con "e" ne fanno parte, e
    anche "a 10 anni", "Nasdaq 100": un numero nel nome è il nome). Se ci sono nomi propri restano quelli, con i numeri del
    nome ("il petrolio Brent" vale "il Brent", "il Bund a 30 anni" non vale "il Bund"). Insieme di radici."""
    out, numeri, iniziata = [], [], False
    for i, w in enumerate(g):
        lw = w.lower()
        if not iniziata:
            if not _piena(w):
                continue
            iniziata = True
        if lw[0].isdigit():
            numeri.append(lw); continue
        if lw in PREPOSIZIONI and i + 1 < len(g) and g[i + 1][0].isdigit():
            continue
        if lw in PREPOSIZIONI or lw == "che" or lw in CONFINI or lw in STOP:
            break
        if _piena(w):
            out.append(w)
    propri = [w for w in out if w[:1].isupper()]
    return {_radice(w) for w in (propri + numeri if propri else out + numeri)}


def _frase(t, m):
    """La frase che contiene la cifra m."""
    a = max([x.end() for x in re.finditer(r"[.;!?](?=\s)", t[:m.start()])] or [0])
    b = re.search(r"[.;!?](?=\s|$)", t[m.end():])
    return t[a:m.end() + (b.start() if b else len(t))]


def cambia_soggetto(orig, nuovo):
    """La prima cifra che nella riscrittura ha perso la testa del suo proprietario o è passata a un altro, o None."""
    # a chi altro può passare una cifra: ai proprietari delle altre cifre dell'originale
    altri = {_radice(w) for x in CIFRA.finditer(orig) for w in proprietario(orig, x) if _piena(w)}
    for m in CIFRA.finditer(nuovo):
        prima = [proprietario(orig, x) for x in CIFRA.finditer(orig) if x.group(2) == m.group(2)]
        prima = [g for g in prima if any(_piena(w) for w in g)]
        if not prima:
            continue
        g_ora = proprietario(nuovo, m)
        frase = {_radice(w) for w in (g_ora if any(_piena(w) for w in g_ora) else _parole(_frase(nuovo, m)))}
        teste = [testa(g) for g in prima]
        if all(h - frase for h in teste):
            persa = sorted(min((h - frase for h in teste), key=len))
            return (f"la cifra {m.group(0).strip()} perde chi l'ha fatta ({', '.join(persa)}...): una cifra resta sul suo "
                    "soggetto")
        ora = {_radice(w) for w in proprietario(nuovo, m) if _piena(w)}
        di_prima = set().union(*[{_radice(w) for w in g if _piena(w)} for g in prima])
        altro = (ora - di_prima) & altri
        if altro:
            return (f"la cifra {m.group(0).strip()} passa a {', '.join(sorted(altro))}, che nell'originale era di un'altra "
                    "cifra o di un'altra frase: una cifra resta sul suo soggetto")
    return None


def frase_tolta(orig, nuovo, altri):
    """Una frase dell'originale che porta un fatto che non sta né nella riscrittura né in un altro campo (il desk toglie
    echi, non fatti: nella prova del 23/11 era sparito su che cosa indagava la SEC). Torna l'inizio della frase o None."""
    radici = lambda t: {w[:6] for w in re.findall(r"[a-zà-ù]{5,}", re.sub(r"<[^>]+>", " ", t).lower())}
    resta = radici(nuovo) | radici(altri)
    for f in re.split(r"(?<=[.;])\s+", orig):
        r = radici(f)
        if len(r) >= 6 and len(r - resta) >= 0.6 * len(r):
            return f[:60]
    return None


def _nomi(t, tutti=False):
    """I nomi propri (e le fonti tra parentesi). "BCE." a fine frase è "BCE". Con tutti=True anche quelli in testa alla
    frase: per sapere quali nomi l'originale ha già ("Nvidia perde..." -> "Dopo i conti Nvidia perde..." non porta nomi)."""
    t = re.sub(r"<[^>]+>", " ", t)
    dove = r"(?<![\w'’&.-])" if tutti else r"(?<=[a-zà-ù0-9,;:)»] )"
    nomi = set(re.findall(dove + r"[A-Z][\w&'.-]*", t)) | set(re.findall(r"\(([^)]{2,40})\)", t))
    return {x.rstrip(".-'’") for x in nomi} - {""}


def controlla(orig, nuovo, tutto, campo="", altri=""):
    """Motivo del rifiuto, o None se la riscrittura è accettata. altri = il testo degli altri campi dell'edizione."""
    if isinstance(nuovo, str) and not nuovo.strip() and campo.endswith(".numero"):
        return None   # un "numero" che ripete il resto si toglie
    if not isinstance(nuovo, str) or not nuovo.strip():
        return "vuota"
    extra = set(NUM.findall(nuovo)) - set(NUM.findall(orig))
    if extra:
        return f"cifre nuove {sorted(extra)[:3]}"
    nomi = {x for x in _nomi(nuovo) - _nomi(orig, tutti=True) if x not in tutto}
    if nomi:
        return f"nomi o fonti nuove {sorted(nomi)[:3]}"
    if sorted(RIMANDO.findall(nuovo)) != sorted(RIMANDO.findall(orig)):
        return "rimandi [[...]] cambiati"
    lo, ln = len(orig.split()), len(nuovo.split())
    if lo >= 8 and not (0.6 * lo <= ln <= 1.1 * lo):
        return f"lunghezza {ln} parole contro {lo} (ammesso -40% / +10%)"
    if "—" in nuovo or "–" in nuovo:
        return "trattino lungo"
    motivo = cambia_soggetto(orig, nuovo)
    if motivo:
        return motivo
    tolta = frase_tolta(orig, nuovo, altri)
    if tolta:
        return f"toglie un fatto che nessun altro campo dice (\"{tolta}...\"): il desk toglie echi, non fatti"
    return None


def coerenza_peggiora(C, campo, testo, M):
    """La riscrittura non può far scattare un controllo di Coerenza che il testo di prima passava: controlli_coerenza.py
    ferma l'edizione, e il desk non deve mai poterlo fare. Per i mercati di dati.json è anche la prova più solida che una
    cifra resta sul suo soggetto: "Hong Kong perde il 3,8%" con l'Hang Seng a -1,9% si ferma qui qualunque sia la sintassi.
    Torna il primo errore nuovo, o None (anche se il controllo non si può fare)."""
    try:
        import copy
        import controlli_coerenza as K
        C2 = copy.deepcopy(C)
        imposta(C2, campo, testo)
        prima = (K.cifre_e_direzioni({campo: K._pulisci(campi(C).get(campo, ""))}, M) if M else []) + K.rimandi(C) + K.titoli(C)
        dopo = (K.cifre_e_direzioni({campo: K._pulisci(testo)}, M) if M else []) + K.rimandi(C2) + K.titoli(C2)
    except Exception:  # noqa: BLE001 - un controllo che non si fa non ferma nulla
        return None
    nuovi = [e for e in dopo if e not in prima]
    return nuovi[0][:160] if len(dopo) > len(prima) and nuovi else None


def _mercati_del_giorno(cartella):
    try:
        import controlli_coerenza as K
        p = os.path.join(cartella, "dati.json")
        return K.mercati_del_giorno(json.load(open(p, encoding="utf-8"))) if os.path.exists(p) else {}
    except Exception:  # noqa: BLE001
        return {}


def _carica(ed):
    # L'edizione legge i suoi argomenti da sys.argv: glieli si presta e poi si rimettono quelli di chi chiama. Senza,
    # controlli_testo.py (che passa di qui per il ritmo) perdeva il suo --json e non scriveva più testo.json, il file
    # delle sigle che edizioni_voce.py si aspetta (trovato il 21/11/2026 costruendo la rete del collaudo).
    argv = sys.argv
    sys.argv = [ed, os.getcwd()]
    try:
        spec = importlib.util.spec_from_file_location("edizione_desk", ed)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.argv = argv
    return mod.C


if __name__ == "__main__":
    azione, ed = sys.argv[1], os.path.abspath(sys.argv[2])
    cart = os.getcwd()
    C = _carica(ed)
    os.chdir(cart)
    attuali = campi(C)
    if azione == "estrai":
        json.dump([{"campo": k, "testo": v} for k, v in attuali.items()], open(INC, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"Desk: {len(attuali)} testi in {INC}; proposta attesa in {PRO}")
    elif azione == "verifica":
        tutto = set().union(*[_nomi(v) for v in attuali.values()])
        M = _mercati_del_giorno(cart)
        ok, no = [], []
        for e in json.load(open(PRO, encoding="utf-8")) if os.path.exists(PRO) else []:
            orig = attuali.get(e.get("campo"))
            if orig is None:
                no.append((e.get("campo"), "campo inesistente")); continue
            if e.get("testo") == orig:
                continue
            altri = " ".join(v for k, v in attuali.items() if k != e["campo"])
            motivo = controlla(orig, e.get("testo"), tutto, e["campo"], altri) or \
                coerenza_peggiora(C, e["campo"], e["testo"], M)
            (no.append((e["campo"], motivo)) if motivo else ok.append({"campo": e["campo"], "originale": orig,
                                                                         "testo": e["testo"]}))
        json.dump(ok, open(OK, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"Desk: {len(ok)} riscritture accettate, {len(no)} respinte (restano com'erano)")
        for c, m in no:
            print(f"RESPINTA {c}: {m}")
