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
# Conta come cifra anche un livello senza unità, cioè un numero con la virgola o col punto delle migliaia ("il Nikkei a
# 57.011", "l'euro a 1,08"): scambiarli tra due mercati è lo stesso errore (secondo collaudo del 25/11). Gli interi nudi
# restano parti di un nome ("Nasdaq 100", "il Bund a 10 anni", "dal 2021").
CIFRA = re.compile(r"([+\-−]?)(\d+(?:[.,]\d+)*)(?:\s?(%|pb\b|punti|\$|dollari|euro|miliardi|milioni)|(?<=\d[.,]\d)(?![\d.,]\d)|"
                   r"(?<=\d[.,]\d\d)(?![\d.,]\d)|(?<=\d[.,]\d\d\d)(?![\d.,]\d))")

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
# Dal quarto collaudo (27/11) anche: la cifra non si allarga a un soggetto coordinato che prima non l'aveva fatta; i nomi
# propri di chi l'ha fatta non spariscono dal testo; dopo la cifra non arriva un nome che nell'originale stava fuori dalla
# sua proposizione. Il tempo e la fonte non sono la testa, e un aggettivo dopo il nome della misura è della misura.
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
                    r"rendiment[oi]|prezz[oi]|quotazion[ei]|valor[ei]|livell[oi]|seduta|giornata|cambi[oi])$")
# Tra le parole della misura, quelle del movimento e del valore (non i contenitori come "azioni", "settore", "comparto", né
# "cambio", che nomina una coppia di valute) reggono un aggettivo o un participio che dice com'è la misura e non chi l'ha
# fatta: "il rialzo proposto", "il calo complessivo", "il taglio atteso" (quarto collaudo, 27/11: 3 riscritture vere su 28
# respinte a torto). L'aggettivo si riconosce dalla forma; "il settore tecnologico" resta tecnologico.
MOVIMENTO = re.compile(r"^(?:rialz[oi]|ribass[oi]|cal[oi]|rimbalz[oi]|croll[oi]|aument[oi]|crescita|salita|discesa|perdit[ae]|"
                       r"guadagn[oi]|bals[oi]|flession[ei]|progress[oi]|cadut[ae]|tonf[oi]|risalita|recuper[oi]|"
                       r"variazion[ei]|rendiment[oi]|prezz[oi]|quotazion[ei]|valor[ei]|livell[oi]|tagli[oi])$")
AGGETTIVO = re.compile(r"^[a-zà-ù]{3,}(?:(?:at|it|ut|st|ss|[^aeiou]s|tt)[oaie]|(?:al|il|ar)[ei]|iv[oaie]|ic[oaie]|ich[ei]|"
                       r"[ae]nt[ei]|ari[oae]|os[oaie])$")
# Il tempo e la fonte non sono mai chi ha fatto la cifra: "Mercoledì il calo del 6,16%", "Per Bloomberg il rialzo del
# 25/11 (+3,5%)". Restano nel gruppo (la cifra non cerca un altro proprietario), ma non ne sono la testa.
TEMPO = set("lunedì martedì mercoledì giovedì venerdì sabato domenica gennaio febbraio marzo aprile maggio giugno luglio "
            "agosto settembre ottobre novembre dicembre ieri oggi stamattina stanotte stasera domani".split())
DATA = re.compile(r"^\d{1,2}/\d{1,2}$")
FONTE = {"per", "secondo"}
# verbi (anche congiuntivo, futuro, participio): chiudono il gruppo del soggetto
VERBI = re.compile(r"^(?:(?:perd|cal|scend|ced|guadagn|crol|risal|rimbalz|arretr|chiud|avanz|cresc|tocc|segn|lasc|pes|"
                   r"tras?cin|spin|frena|sostien|rest|pass|port|registr|vol|torn|affond|scivol|ripieg|fless|recuper|"
                   r"sal)(?:e|a|ano|ono|ino|ava|avano|eva|evano|erà|eranno|irà|iranno|ato|ata|ati|ate|uto|uta|"
                   r"so|sa|si|se|ito|ita|endo|ando|gono|go|ga|gano|isce|iscono|ta|to|ti)|"
                   r"pers[oaie]|sces[oaie]|fanno|fa|ha|hanno|è|sono|era|erano|sarà|vale|valgono|rende|rendono|supera|"
                   r"superano)$")
# unità di misura dopo una cifra: non sono un proprietario ("sale di 5 pb al 2,71%")
UNITA = set("pb punti base dollari euro miliardi milioni cento % $".split())
STOP = {",", ";", ":", ".", "?", "!"}
# Il proprietario di una cifra è un gruppo nominale la cui testa non è un complemento di un verbo, un participio o un'altra
# cifra (secondo collaudo del 25/11). Per riconoscerli servono gli ausiliari, la forma del participio e il complemento
# d'agente: "Hong Kong è affossato dalle strette USA: -3,8%" è di Hong Kong, "Il 3,8% perso da Hong Kong" anche.
AUSILIARI = set("è sono era erano sarà saranno stato stata stati state viene vengono venuto venuta ha hanno aveva avevano "
                "si".split())
PARTICIPIO = re.compile(r"^[a-zà-ù]{2,}(?:at|it|ut)[oaie]$|^[a-zà-ù]*(?:pers|sces|mess|chius|spint|pres|tolt|vist|"
                        r"fatt|rott|cors|mos)[oaie]$")
AGENTE = set("da dal dalla dallo dai dagli dalle dall".split())
# un'altra cifra legata da una di queste parole è il termine di paragone, e fa parte di chi è la cifra ("Il Nikkei recupera
# l'1% dopo il -3% di ieri": il -3% è quello di ieri); legata da una virgola o da "a" è la stessa cosa detta in un'altra
# misura, e non conta ("rende il 2,31%, 4 punti base in meno", "sale del 3% a 140 dollari")
RELAZIONE = set("dopo prima contro rispetto dal dalla dai da sopra sotto oltre".split())
LAVORO_MAX = 60        # cifre guardate per campo: oltre, il campo non è un testo dell'edizione e si respinge


def _parole(t):
    """Le parole del testo con la maiuscola com'è (serve a riconoscere i nomi propri)."""
    t = re.sub(r"<[^>]+>|\[\[\w+\]\]", " ", t).replace("'", " ").replace("’", " ")
    return re.findall(r"[A-Za-zÀ-ÿ&]+|[(),;:.?!%$]|\d{1,2}/\d{1,2}(?![\d/])|\d+(?:[.,]\d+)*", t)


def _livello(w):
    """Un numero con la virgola o col punto delle migliaia: è una cifra anche senza unità (un intero nudo è un nome)."""
    return bool(re.fullmatch(r"\d+(?:[.,]\d+)+", w))


def _verbale(pp, k):
    """pp[k] è un verbo, un ausiliare o un participio (questo solo se viene dopo un ausiliare o prima di un "da": "è
    affossato dalle strette", e non "il mercato del lavoro")."""
    lw = pp[k].lower()
    if (VERBI.match(lw) and not MISURA.match(lw)) or lw in AUSILIARI:
        return True
    if PARTICIPIO.match(lw):
        dopo = pp[k + 1].lower() if k + 1 < len(pp) else ""
        prima = pp[k - 1].lower() if k > 0 else ""
        return dopo in AGENTE or prima in AUSILIARI or prima in ("è", "sono", "ha", "hanno")
    return False


def _attributo(pp, k):
    """pp[k] è un aggettivo o un participio attaccato a un nome del movimento o del valore ("il rialzo proposto", "il calo
    complessivo previsto"): dice com'è la misura, non chi l'ha fatta."""
    def agg(i):
        return pp[i][:1].islower() and bool(AGGETTIVO.match(pp[i])) and not MISURA.match(pp[i])
    if not agg(k):
        return False
    j = k - 1
    if j >= 0 and agg(j):
        j -= 1
    return j >= 0 and bool(MOVIMENTO.match(pp[j].lower()))


def _radice(w):
    w = w.lower().lstrip("§")
    return w[:5] if len(w) > 6 else (re.sub(r"[aeiouhàèéìòù]+$", "", w) or w)


def _piena(w):
    lw = w.lower()
    return lw not in LEGAMI and lw not in CONFINI and not lw[0].isdigit() and not MISURA.match(lw) and \
        not VERBI.match(lw) and lw != "che" and lw not in STOP and lw[0] not in "()%$&§"


def _prima(pp):
    """Il gruppo del proprietario risalendo dalla cifra: le parole (in ordine) fino all'articolo che lo apre, al verbo o alla
    punteggiatura. Un verbo subito prima della cifra ("Hong Kong perde il 3,8%") si salta; "X, che perde il 3,8%" porta a X;
    "il rame e l'argento" e "DRAM e NAND" sono un soggetto solo; una parentesi già chiusa è un inciso e si salta.
    Non sono proprietari (si saltano e si risale): un'altra cifra con la sua unità e la sua coda ("tocca i 9.800 dollari a
    tonnellata, +2,2%"; "rende il 2,31%, 4 punti base in meno") e, quando la cifra sta dopo i due punti o la virgola, il
    complemento del verbo ("Hong Kong cede alle strette americane: -3,8%", "...è affossato dalle strette USA: -3,8%")."""
    out, k, piene, rel, coord = [], len(pp) - 1, 0, False, None
    staccata = bool(pp) and pp[-1] in (":", ",")

    def salta_verbo(k):
        while k >= 0 and (_verbale(pp, k) or pp[k].lower() in AUSILIARI or pp[k].lower() in ("non", "ne")):
            k -= 1
        return k

    lavoro = 0
    while k >= 0:
        lavoro += 1
        if lavoro > 400:
            break
        w = pp[k]; lw = w.lower()
        if lw == ")":
            while k >= 0 and pp[k] != "(":
                k -= 1
            k -= 1; continue
        if lw == "(":
            k -= 1; continue
        if lw in STOP:
            if not piene and lw in (":", ",") and not rel:
                staccata = True                             # la cifra non è attaccata al gruppo che si troverà prima
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
        if coord and ((lw[0].isdigit() and (_livello(w) or (k + 1 < len(pp) and pp[k + 1].lower() in UNITA)))
                      or VERBI.match(lw)):
            out = out[len(out) - coord:]; break             # "...a 129.902 immatricolazioni e la quota": non è doppio
        if _attributo(pp, k):
            k -= 1; continue                                # "il rialzo proposto": l'aggettivo è della misura
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
        altra = _livello(w) or (lw in UNITA and k > 0 and (pp[k - 1][0].isdigit() or pp[k - 1].lower() in UNITA))
        if altra:
            # un'altra cifra con la sua unità: non è un nome. Se quello che si è raccolto comincia con una preposizione è la
            # sua coda ("i 9.800 dollari a tonnellata"): si butta, e si risale al soggetto
            if piene and not (out and out[0].lower() in PREPOSIZIONI):
                break
            c = max([i for i, x in enumerate(out[:-1]) if x.lower() in COORD and
                     (out[i + 1].lower() in ARTICOLI or out[i + 1][:1].isupper())] or [-1])
            if piene and c >= 0:
                out = out[c + 1:]; break                    # "perde il 7% a Seul e SK hynix quasi il 6%": SK hynix
            if piene:
                out, piene = [], 0
            elif any(x.lower() in RELAZIONE for x in out):
                out.insert(0, "§" + next((x for x in pp[max(0, k - 3):k + 1][::-1] if x[0].isdigit()), ""))
            k -= 1
            while k >= 0 and (pp[k][0].isdigit() or pp[k].lower() in UNITA):
                k -= 1
            continue
        if lw in ARTICOLI and piene:
            if k > 1 and pp[k - 1].lower() in COORD and _piena(pp[k - 2]):
                out.insert(0, w); k -= 1; coord = len(out); continue    # "il rame e l'argento"
            if staccata and k > 1 and pp[k - 1].lower() in PREPOSIZIONI and _verbale(pp, k - 2):
                out, piene = [], 0                          # "cede per le strette americane: -3,8%": complemento
                k = salta_verbo(k - 2); continue
            j = k - 2 if k > 1 and pp[k - 1].lower() in PREPOSIZIONI else k - 1
            if staccata and j >= 0 and (_livello(pp[j]) or (pp[j].lower() in UNITA and j > 0 and pp[j - 1][0].isdigit())):
                out, piene = [], 0                          # "resta a 51,7 per l'area euro, sotto il 51,9", "52 dollari
                k = j; continue                             # l'oncia, +3,1%": la coda di un'altra cifra
            out.insert(0, w); break
        if lw in PREPOSIZIONI and piene and staccata and k > 0 and _verbale(pp, k - 1):
            out, piene = [], 0                              # "cede alle strette americane: -3,8%": complemento
            k = salta_verbo(k - 1); continue
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
    proprietario è il gruppo che segue, fino alla punteggiatura o al verbo. Se la cifra è seguita da un participio o da un
    ausiliare ("Il 3,8% lasciato sul terreno da Hong Kong", "Il 3,8% è stato perso da Hong Kong") il proprietario è il
    complemento d'agente."""
    if pp and (_verbale(pp, 0) or pp[0].lower() in AUSILIARI or PARTICIPIO.match(pp[0].lower())):
        for j, w in enumerate(pp[:15]):
            if w in STOP:
                break
            if w.lower() in AGENTE:
                return _dopo(pp[j + 1:])
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


def _fonte(g, i):
    """g[i] è il nome di chi dà la notizia, subito dopo "per" o "secondo" ("Per KED Global il Kospi...")."""
    if not g[i][:1].isupper() or g[i].lower() in FONTE:
        return False
    j = i
    while j > 0 and g[j - 1][:1].isupper() and g[j - 1].lower() not in FONTE:
        j -= 1
    return j > 0 and g[j - 1].lower() in FONTE


def testa(g):
    """La testa del gruppo: dalla prima parola piena fino alla prima preposizione (le coordinate con "e" ne fanno parte, e
    anche "a 10 anni", "Nasdaq 100": un numero nel nome è il nome). Se ci sono nomi propri restano quelli, con i numeri del
    nome ("il petrolio Brent" vale "il Brent", "il Bund a 30 anni" non vale "il Bund", "il 10 anni" non vale "il 2
    anni"). Il tempo e la fonte non sono la testa ("Mercoledì il calo", "Per Bloomberg il rialzo del 25/11"). Insieme di
    radici."""
    out, numeri, iniziata = [], [], False
    cifra = lambda j: j < len(g) and g[j][0].isdigit() and (_livello(g[j]) or (j + 1 < len(g) and g[j + 1].lower() in UNITA))
    for i, w in enumerate(g):
        lw = w.lower()
        if DATA.match(lw) or lw in TEMPO or _fonte(g, i):
            continue                                        # il tempo e la fonte non sono chi ha fatto la cifra
        if not iniziata:
            if lw[0].isdigit() and not cifra(i) and i + 1 < len(g) and _piena(g[i + 1]):
                numeri.append(lw)                           # "il 10 anni": il numero è nel nome
            if not _piena(w):
                continue
            iniziata = True
        if lw[0] == "§":
            numeri.append(lw[1:]); continue                 # il termine di paragone
        if lw[0].isdigit():
            if not cifra(i):
                numeri.append(lw)                           # "a 10 anni" è nel nome, "il 2,31" è un'altra cifra
            continue
        if lw in UNITA and i and g[i - 1][0].isdigit():
            continue
        if lw in PREPOSIZIONI and i + 1 < len(g) and g[i + 1][0].isdigit() and not cifra(i + 1):
            continue
        if lw in PREPOSIZIONI or lw == "che" or lw in CONFINI or lw in STOP:
            break
        if _piena(w):
            out.append(w)
    propri = [w for w in out if w[:1].isupper()]
    return {_radice(w) for w in (propri + numeri if propri else out + numeri)}


def _membri(g):
    """I soggetti coordinati del gruppo ("il 10 anni e il 2 anni", "DRAM e NAND"): uno solo se non ci sono."""
    out, cur = [], []
    for i, w in enumerate(g):
        dopo = g[i + 1] if i + 1 < len(g) else ""
        if w.lower() in COORD and cur and (dopo.lower() in ARTICOLI or dopo[:1].isupper()):
            out.append(cur); cur = []
        else:
            cur.append(w)
    return out + [cur] if cur else out


def _coda(t, m):
    """Le parole piene subito dopo la cifra m, fino alla punteggiatura, a una congiunzione o a un verbo ("perdono il 2,4% a
    Milano dopo la BCE"): il complemento della cifra."""
    out = []
    for w in _parole(t[m.end():])[:8]:
        lw = w.lower()
        if lw in STOP or lw in CONFINI or lw in COORD or lw in ("(", ")", "che") or (VERBI.match(lw) and not MISURA.match(lw)):
            break
        if _piena(w):
            out.append(w)
    return out


def _proposizione(t, m):
    """Le parole della proposizione della cifra m: dalla punteggiatura o dalla congiunzione prima a quella dopo."""
    prima, dopo = _parole(t[:m.start()]), _parole(t[m.end():])
    fine = lambda w: w in STOP or w.lower() in CONFINI
    i = max([j for j, w in enumerate(prima) if fine(w)] or [-1])
    j = next((j for j, w in enumerate(dopo) if fine(w)), len(dopo))
    return prima[i + 1:] + dopo[:j]


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
        if not m.group(3):
            # un livello senza unità prende per unità il nome che lo segue: "scende a 129.902 immatricolazioni"
            dopo = _parole(nuovo[m.end():])[:1]
            frase |= {_radice(w) for w in dopo if _piena(w)}
        teste = [testa(g) for g in prima]
        if all(h - frase for h in teste):
            persa = sorted(min((h - frase for h in teste), key=len))
            return (f"la cifra {m.group(0).strip()} perde chi l'ha fatta ({', '.join(persa)}...): una cifra resta sul suo "
                    "soggetto")
        # la cifra non si allarga: ogni soggetto coordinato del proprietario nuovo era già nel proprietario di prima ("Il
        # 10 anni scende di 6 pb, il 2 anni meno" -> "Il 10 anni e il 2 anni scendono di 6 pb", quarto collaudo, 27/11)
        noti = set().union(*[{_radice(w) for w in g if _piena(w) or w[0].isdigit()} for g in prima])
        membri = _membri(g_ora)
        for mb in (membri if len(membri) > 1 else []):
            h = testa(mb)
            if h and not h <= noti:
                return (f"la cifra {m.group(0).strip()} si allarga a {', '.join(sorted(h - noti))}, che nell'originale non "
                        "l'aveva fatta: una cifra resta sul suo soggetto")
        # i nomi propri di chi ha fatto la cifra non spariscono ("il listino tecnologico di Hong Kong" -> "il listino
        # tecnologico"), e dopo la cifra non arriva un nome che nell'originale stava fuori dalla sua proposizione
        # ("perdono il 2,4% a Milano dopo la BCE, meno che a Francoforte" -> "perdono il 2,4% a Francoforte...")
        resta = {_radice(w) for w in _parole(nuovo)}
        propri = {_radice(w) for g in prima for w in g if w[:1].isupper() and _piena(w) and w.lower() not in TEMPO}
        if propri - resta:
            return (f"la cifra {m.group(0).strip()} perde {', '.join(sorted(propri - resta))}, che diceva di chi era: una "
                    "cifra resta sul suo soggetto")
        accanto = noti | {_radice(w) for x in CIFRA.finditer(orig) if x.group(2) == m.group(2) for w in _proposizione(orig, x)}
        nuovi_accanto = {_radice(w) for w in _coda(nuovo, m) if w[:1].isupper()} - accanto
        if nuovi_accanto:
            return (f"dopo la cifra {m.group(0).strip()} arriva {', '.join(sorted(nuovi_accanto))}, che nell'originale non le "
                    "stava accanto: una cifra resta sul suo soggetto")
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


def cifra_tolta(orig, nuovo, altri):
    """Una cifra dell'originale che non sta né nella riscrittura né in un altro campo, o None. ISTRUZIONI §4 punto 8: il
    desk lavora "senza cifre, nomi, fonti o fatti nuovi, e senza spostarne o toglierne", e gli echi si tolgono: una cifra
    detta anche altrove può sparire, una che c'è solo qui no ("Il Bund rende il 2,3% dopo l'asta" -> "Il Bund sale dopo
    l'asta"). Un'eco può essere arrotondata: il -6,16% del Kospi tolto dal sommario resta nel "Seul perde il 6%" del
    titolo, i "92 dollari" del petrolio nei 91,40 del Brent (riscritture vere del 25/11): vale chi sta entro il 3%."""
    def valore(x):
        try:
            return float(re.sub(r"\.(?=\d{3}\b)", "", x).replace(",", "."))
        except ValueError:
            return None
    resta = [v for v in map(valore, NUM.findall(nuovo) + NUM.findall(altri)) if v is not None]
    for m in CIFRA.finditer(orig):
        v = valore(m.group(2))
        if v is not None and not any(abs(v - r) <= 0.03 * max(abs(v), 1e-9) for r in resta):
            return m.group(0).strip()
    return None


def controlla(orig, nuovo, tutto, campo="", altri=""):
    """Motivo del rifiuto, o None se la riscrittura è accettata. altri = il testo degli altri campi dell'edizione."""
    if not isinstance(orig, str) or not isinstance(nuovo, str) or not isinstance(campo, str) or \
            not isinstance(altri, str):
        return "proposta malformata (testo e campo devono essere stringhe)"
    if len(CIFRA.findall(nuovo)) > LAVORO_MAX or len(nuovo) > 4 * len(orig) + 200:
        return "proposta fuori misura per un campo dell'edizione"
    if not nuovo.strip() and campo.endswith(".numero"):
        # un "numero" che ripete il resto si toglie, ma solo se è davvero un'eco
        tolta = cifra_tolta(orig, nuovo, altri)
        return f"toglie la cifra {tolta}, che nessun altro campo dice: il desk toglie echi, non fatti" if tolta else None
    if not nuovo.strip():
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
    tolta = cifra_tolta(orig, nuovo, altri)
    if tolta:
        return f"toglie la cifra {tolta}, che nessun altro campo dice: il desk toglie echi, non fatti"
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
        try:
            proposta = json.load(open(PRO, encoding="utf-8")) if os.path.exists(PRO) else []
        except (OSError, ValueError) as x:
            proposta, _ = [], no.append(("(tutta la proposta)", f"non si legge ({str(x)[:80]})"))
        if not isinstance(proposta, list):
            proposta, _ = [], no.append(("(tutta la proposta)", "non è un elenco di {\"campo\", \"testo\"}"))
        # una proposta malformata (un elemento che non è un oggetto, un campo che non è una stringa) o un errore del
        # controllo si respinge come le altre: il desk non blocca mai, e verifica non esce con una traceback
        for e in proposta:
            campo = e.get("campo") if isinstance(e, dict) else None
            try:
                if not isinstance(campo, str) or not isinstance(e.get("testo"), str):
                    no.append((str(campo if campo is not None else e)[:40], "proposta malformata (campo e testo stringhe)"))
                    continue
                orig = attuali.get(campo)
                if orig is None:
                    no.append((campo, "campo inesistente")); continue
                if e["testo"] == orig:
                    continue
                altri = " ".join(v for k, v in attuali.items() if k != campo)
                motivo = controlla(orig, e["testo"], tutto, campo, altri) or coerenza_peggiora(C, campo, e["testo"], M)
            except Exception as x:  # noqa: BLE001 - un controllo che si rompe respinge, non ferma l'edizione
                motivo = f"controllo non riuscito ({type(x).__name__}): resta com'era"
            (no.append((campo, motivo)) if motivo else ok.append({"campo": campo, "originale": orig, "testo": e["testo"]}))
        json.dump(ok, open(OK, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"Desk: {len(ok)} riscritture accettate, {len(no)} respinte (restano com'erano)")
        for c, m in no:
            print(f"RESPINTA {c}: {m}")
