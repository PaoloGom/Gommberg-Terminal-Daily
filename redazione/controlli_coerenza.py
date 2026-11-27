"""Il testo regge contro i dati (G-45, 24/11/2026). Uso (cartella di lavoro):
  python3 controlli_coerenza.py <edizione.py> --dati dati.json [--prima-della-revisione]

Le regole ci sono già (ISTRUZIONI §3.1, §3.4, §3.6): qui si controlla che siano applicate, sul testo che il lettore legge
(il file dell'edizione con le riscritture del desk). Due parti.

1. IL CODICE (bloccante, zero token), su ciò che si può confrontare con dati.json:
 cifre      una variazione o un livello scritto accanto al nome di un mercato di dati.json è quello calcolato: "Hong Kong
            perde il 3,8%" con l'Hang Seng a -1,9% si ferma, "il listino tecnologico di Hong Kong (-3,8%)" no (la cifra è
            del listino, non dell'indice). "circa", "quasi", "più di" valgono come tali: "l'oro cede più del 2%" con
            -4,6% si ferma. Senza periodo vale la seduta; "in una settimana", "in cinque sedute" la settimana; "da inizio
            anno" l'anno; altri periodi non si confrontano.
 direzioni  un mercato di dati.json che nella frase sale, scende o resta fermo, senza periodo e senza "se", "quando",
            "di solito", lo fa davvero nella seduta (il dollaro è l'inverso di EUR/USD).
 rimandi    "→ pag. N" porta a un pezzo che parla della stessa cosa: la frase e il pezzo hanno almeno un nome o due
            parole piene in comune.
 titoli     un titolo porta il fatto e, se c'è, la causa verificata: mai un'ipotesi ("forse", "potrebbe", "sembra").

2. IL RAGIONAMENTO (dentro la revisione che già c'è, ISTRUZIONI §4.7): con --prima-della-revisione il codice scrive
   coerenza_incarico.json, cioè i prezzi del giorno e le frasi da giudicare (i Perché, i titoli, le frasi che danno una
   causa, la prima volta di un fatto che muove la storia). Il revisore risponde in coerenza.json, frase per frase:
     [{"id": "R01", "esito": "regge" | "non_regge", "nota": "che cosa non torna, in una frase", "rimedio": "..."}]
   Al giro finale una frase "non_regge" ancora uguale nel testo ferma l'edizione, con il suo rimedio. pubblica.sh
   archivia incarico e risposta tra i sorgenti; il collaudo, rifacendo un'edizione uscita prima di G-45 (senza incarico
   archiviato), salta il ragionamento con un avviso (GTD_SENZA_RAGIONAMENTO=1).
"""
import json, os, re, sys

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)

INCARICO, RISPOSTA = "coerenza_incarico.json", "coerenza.json"
RIMEDI = ("chi la dà", "lettura con i prezzi", "solo il fatto", "spiegare il fatto", "titolo col fatto")

# ------------------------------------------------------------------ i mercati di dati.json e come li chiama il testo
# (regex sul testo minuscolo, serie candidate, tipo di nome). "luogo": una città che, dopo "a" o "in", è un posto e non
# il soggetto ("Samsung perde il 7% a Seul"). "inverso": il dollaro sale quando EUR/USD scende.
MERCATI = [
    (r"s&p(?: ?500)?", ("S&P 500",), ""),
    (r"wall street", ("S&P 500", "Nasdaq"), "luogo"),
    (r"nasdaq(?! ?100)(?: comp\.?| composite)?", ("Nasdaq",), ""),
    (r"russell(?: 2000)?", ("Russell 2000",), ""),
    (r"euro ?stoxx(?: 50)?|borse europee|l'europa", ("Euro Stoxx 50",), ""),
    (r"ftse ?mib|piazza affari|milano", ("FTSE MIB",), "luogo"),
    (r"nikkei(?: 225)?|tokyo", ("Nikkei 225",), "luogo"),
    (r"hang seng|hong kong", ("Hang Seng",), "luogo"),
    (r"kospi|seul", ("Kospi",), "luogo"),
    (r"(?:treasury|titolo di stato americano|rendimento) a 10 anni|(?:il |del |dal |al )10 anni|decennale americano",
     ("Treasury 10 anni",), ""),
    (r"(?:treasury|titolo di stato americano|rendimento) a 2 anni|(?:il |del |dal |al )2 anni", ("Treasury 2 anni",), ""),
    (r"spread(?: tra btp e bund| btp-bund)?", ("Spread Italia",), ""),
    (r"eur/usd|cambio euro-dollaro|euro-dollaro|l'euro(?! ?stoxx)", ("EUR/USD",), ""),
    (r"dollaro", ("EUR/USD",), "inverso"),
    (r"brent(?: future)?|petrolio", ("Brent future",), ""),
    (r"(?<!d')\boro(?: future)?\b", ("Oro future", "Oro"), ""),
    (r"vix|indice della paura", ("VIX",), ""),
]
ALIAS = re.compile("|".join(f"(?P<m{i}>{rx})" for i, (rx, _, _) in enumerate(MERCATI)))
TESTE = {"borsa", "borse", "piazza", "listino", "indice", "mercato"}     # "la Borsa di Tokyo" è l'indice
GENITIVO = re.compile(r"\b(?:di|del|della|dei|delle|degli|dell')\s*$")
NUM = re.compile(r"(?<![\w,.])([+\-−]?)(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?)(?![\d])\s?"
                 r"(%|per cento|pb\b|punti base|punti|\$|dollari)?")
STACCO = re.compile(r"[;:]| e (?:il|lo|la|l'|i|gli|le) | mentre | ma | invece | dopo che | perché | anche se ")
# Quando una cifra NON è la variazione di chiusura del giorno (quarto collaudo, 27/11: 4 falsi allarmi su 5 nelle edizioni
# vere venivano tutti da qui). Si confronta con la seduta di dati.json solo ciò che nulla, nella proposizione che porta la
# cifra, colloca altrove (non una relativa, un inciso, un "dopo aver" o un'altra proposizione coordinata: "Il Kospi, che
# ieri aveva chiuso in calo, sale del 6,3%" si confronta):
#  - un altro periodo: la settimana, l'anno, un mese diverso da quello della seduta, "da inizio anno", "dai minimi";
#  - un altro momento della stessa seduta: l'apertura, la mattina, il minimo o il massimo toccato ("è arrivato a perdere
#    il 4,6%"); se la cifra è detta della chiusura ("chiude in rialzo del 6,3%") vale la chiusura. Scoperto, dichiarato:
#    "in apertura", "in mattinata", "in seduta" esentano sempre, perché senza i prezzi dentro la seduta non si decide;
#  - un altro giorno: una data o un giorno della settimana diversi da quello della seduta, "il giorno prima", i tempi che
#    raccontano un prima (imperfetto e trapassato: "era salito", "cedeva").
# Non è una variazione nemmeno un livello in punti di un indice che si muove in percentuale ("si avvicina ai 5.000
# punti"): si confronta solo nelle forme di livello riconosciute (a, al, chiude a, sotto, sopra).
PERIODO = re.compile(r"settiman|base settimanale|cinque sedute|\b5 sedute|inizio (?:dell')?anno|\bnel 20\d\d|\bmes[ei]\b|\banno\b|"
                     r"\bsedute\b|\bgiorni\b|\bdal \d|\bdai? (?:minimi|massimi|picco)|\bdal (?:minimo|massimo|picco)|trimestr|"
                     r"scors[oa]|di fila|\bin \w+ sedute|\bfuture sull|"
                     # un altro giorno
                     r"il giorno (?:prima|dopo|precedente|successivo)|la vigilia|la seduta precedente|l'altro ieri|"
                     r"\b(?:era|erano|aveva|avevano)\b|\b\w+(?:eva|evano|ava|avano)\b")
DENTRO = re.compile(r"stamattina|in mattinata|nel pomeriggio|in apertura|all'apertura|in avvio|in seduta|durante la seduta|"
                    r"nel corso della seduta|minim[oi] (?:della|di) seduta|massim[oi] (?:della|di) seduta|a un certo punto|"
                    r"nel momento peggiore|nel momento migliore|"
                    r"(?:arrivat[oaie]|fino) a (?:perdere|cedere|lasciare|guadagnare|salire|scendere|toccare|segnare|bruciare)")
CHIUSURA = re.compile(r"\bchiu(?:de|dono|so|sa|si|se|sura)\b")
MESI = ("gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre").split()
GIORNI = "lunedì martedì mercoledì giovedì venerdì sabato domenica".split()
DATA = re.compile(r"\b(\d{1,2})(?:/(\d{1,2})| (" + "|".join(MESI) + r"))\b")
# ciò che nella frase non è la proposizione della cifra: parentesi, relative e "dopo aver" tra virgole
INCISO = re.compile(r"\([^)]*\)|,\s*(?:che|dove|il cui|la cui|i cui|le cui|dopo aver)\b[^,]*(?:,|$)")
# dove finisce, dopo la cifra, la sua proposizione
FINE = re.compile(r",|" + STACCO.pattern + r"| e | ed | dopo aver| che ")


def proposizione(t):
    return INCISO.sub(" ", t)


def fuori_seduta(t, giorno, chiude=False):
    """La proposizione (minuscola) colloca le sue cifre fuori dalla seduta di chiusura del giorno (AAAA-MM-GG)? Con
    chiude=True la cifra è detta della chiusura: i momenti dentro la seduta non contano."""
    t = proposizione(t)
    if PERIODO.search(t) or (not chiude and DENTRO.search(t)):
        return True
    try:
        import datetime as dt
        g = dt.date.fromisoformat(giorno)
    except (TypeError, ValueError):
        return bool(DATA.search(t) or re.search(r"\b(?:" + "|".join(GIORNI + MESI) + r")\b", t))
    for d in DATA.finditer(t):
        mese = int(d.group(2)) if d.group(2) else MESI.index(d.group(3)) + 1
        if (int(d.group(1)), mese) != (g.day, g.month):
            return True
    resto = DATA.sub(" ", t)
    if any(re.search(rf"\b{x}\b", resto) for x in MESI if x != MESI[g.month - 1]):
        return True                                 # un altro mese è un altro periodo; quello della seduta no
    return any(re.search(rf"\b{x}\b", resto) for x in GIORNI if x != GIORNI[g.weekday()])


SETT = re.compile(r"settiman|cinque sedute|\b5 sedute")
# il periodo detto in testa alla frase vale per le sue cifre ("Su base settimanale: il FTSE MIB perde il 3,6% e ...")
ANNO = re.compile(r"inizio (?:dell')?anno|\bnel 20\d\d")
COND = re.compile(r"\bse\b|\bquando\b|\bcon cui\b|frequenza|\bin cui\b|\bnei quali\b|\bnelle quali\b|di solito|in genere|tend(?:e|ono) a|spesso|di norma|quasi sempre|\w+rebbe(?:ro)?\b|"
                  r"potrebbe|dovrebbe|\bpuò\b|\bpossono\b", re.I)
GIU = re.compile(r"\b(?:cede|cedono|perde|perdono|scende|scendono|sceso|scesa|cala|calano|calato|arretra|crolla|affonda|"
                 r"scivola|ripiega|si indebolisce|in calo|in meno|giù|flette|lascia sul terreno|chiude in ribasso)\b")
SU = re.compile(r"\b(?:sale|salgono|salito|salita|guadagna|guadagnano|risale|risalito|risalita|rimbalza|rimbalzato|avanza|balza|vola|si rafforza|"
                r"si apprezza|in rialzo|in più|chiude in rialzo|in salita)\b")
FERMO = re.compile(r"\b(?:quasi fermo|quasi ferma|quasi fermi|resta fermo|resta ferma|fermo|ferma|fermi|invariato|"
                   r"invariata|poco mosso|poco mossa|poco mossi|quasi non si muove|non si muove|stabile)\b")
QUASI = re.compile(r"(?:quasi|poco meno d(?:i|el|ell'|ello)|sfiora(?:ndo)?)\s*(?:il |l'|lo )?$")
OLTRE = re.compile(r"(?:più d(?:i|el|ell'|ello)|oltre(?: il| l'| lo)?|poco più d(?:i|el|ell'|ello)|sopra(?: il| l'| lo)?)\s*$")
CIRCA = re.compile(r"(?:circa|intorno a(?:l|ll')?|attorno a(?:l|ll')?|vicino a(?:l|ll')?)\s*(?:il |l'|lo )?$")
LIVELLO = re.compile(r"(?:\ba|\bal|\ba quota|chiude a|chiuso a)\s*$")
PRIMA = re.compile(r"(?:\bda|\bdal|\bdallo|\bdai)\s*$")
SOGLIA_SOTTO = re.compile(r"(?:sotto(?: i| il| quota)?|sotto i)\s*$")
SOGLIA_SOPRA = re.compile(r"(?:sopra(?: i| il| quota)?|oltre i|oltre quota)\s*$")


def _num(s):
    return float(s.replace(".", "").replace(",", "."))


def _dec(s):
    return len(s.split(",")[1]) if "," in s else 0


def _pulisci(t):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>|\[\[\w+\]\]", "", str(t))).strip()


def frasi(t):
    return [f.strip() for f in re.split(r"(?<=[.!?])\s+(?=[A-ZÀÈÉÌÒÙ«\"(])", _pulisci(t)) if f.strip()]


# ------------------------------------------------------------------ i numeri del giorno
def mercati_del_giorno(D):
    """{serie: {"v0", "v1", "g" (1 seduta), "s" (1 settimana), "a" (da inizio anno), "tipo" (pct | pb | spread)}}."""
    import datetime as dt
    import numeri as N
    out = {}
    for nome, s in (D.get("serie") or {}).items():
        if s.get("tipo") == "intraday":
            continue                       # la seduta di stamattina vale solo in "Stamattina": non si confronta qui
        u = N.completa(nome, s)
        if len(u) < 2 or not isinstance(u[0][1], (int, float)) or not isinstance(u[1][1], (int, float)):
            continue
        t = N.tipo_riga(nome, s)
        d0, v0, v1 = str(u[0][0])[:10], float(u[0][1]), float(u[1][1])
        st = N.storia(nome, s)

        def rif(prima_del):
            k = [d for d in st if d <= prima_del]
            return st[max(k)] if k else None
        diff = lambda a, b: None if b is None else ((a - b) * 100 if t == "pb" else (a - b) if t in ("spread", "punti")
                                                     else (a / b - 1) * 100)
        sett = rif((dt.date.fromisoformat(d0) - dt.timedelta(days=7)).isoformat())
        d1 = str(u[1][0])[:10]
        sett_prima = rif((dt.date.fromisoformat(d1) - dt.timedelta(days=7)).isoformat())   # la settimana chiusa ieri
        anno = rif(f"{int(d0[:4]) - 1}-12-31")
        out[nome] = {"v0": v0, "v1": v1, "data": d0, "tipo": t, "g": diff(v0, v1), "s": diff(v0, sett), "a": diff(v0, anno),
                     "s2": diff(v1, sett_prima),
                     "pct_g": (v0 / v1 - 1) * 100}
    return out


def _fmt(x, d=2):
    return f"{x:+.{d}f}".replace(".", ",")


def scheda_prezzi(M):
    """La tabella dei prezzi per il revisore: livello, seduta e settimana, con la direzione detta in parole."""
    righe = []
    for nome, m in M.items():
        u = {"pb": " pb", "spread": " pb", "punti": " punti"}.get(m["tipo"], "%")
        dec = 0 if m["tipo"] in ("pb", "spread") else 2
        soglia = {"pb": 1.5, "spread": 1.5, "punti": 0.3}.get(m["tipo"], 0.15 if nome == "EUR/USD" else 0.3)
        verso = "fermo" if abs(m["g"]) < soglia else ("su" if m["g"] > 0 else "giù")
        r = f"{nome} {m['v0']:g} al {m['data']}: seduta {_fmt(m['g'], dec)}{u}" + \
            (f" ({_fmt(m['pct_g'], 1)}%)" if m["tipo"] == "punti" else "") + f" ({verso})"
        if m["s"] is not None:
            r += f", settimana {_fmt(m['s'], dec)}{u}"
        if nome == "EUR/USD":
            r += " | il dollaro va al contrario: EUR/USD giù = dollaro forte"
        righe.append(r)
    return righe


# ------------------------------------------------------------------ 1a. cifre e direzioni accanto ai mercati
def _alias(m):
    i = int(next(k for k, v in m.groupdict().items() if v)[1:])
    return MERCATI[i]


def _governato(prima):
    """Il nome del mercato è complemento di un altro nome ("il listino tecnologico di Hong Kong"): la cifra non è sua."""
    g = GENITIVO.search(prima)
    if not g:
        return False
    parole = re.findall(r"[a-zà-ù]+", prima[:g.start()].lower())
    return bool(parole) and parole[-1] not in TESTE


def _tra_parentesi(fl, a):
    """Il nome sta dentro una parentesi già chiusa ("il VIX (volatilità attesa sull'S&P 500) sale"): non è il soggetto."""
    return fl.rfind("(", 0, a.start()) > fl.rfind(")", 0, a.start()) and ")" in fl[a.end():]


def _locativo(prima):
    return bool(re.search(r"(?:\ba|\bin|\bsu)\s*$", prima.lower()))


def _attese(m, orizzonte):
    """Il valore con cui confrontare: per il tipo della serie e per il periodo."""
    return m.get(orizzonte)


CONTA = {"cifre": 0, "direzioni": 0, "rimandi": 0}


def cifre_e_direzioni(campi, M):
    err = []
    for dove, testo in campi.items():
        if dove.startswith(("stamattina",)):
            continue
        for f in frasi(testo):
            fl = f.lower()
            als = [a for a in ALIAS.finditer(fl)]
            nums = [n for n in NUM.finditer(f)]
            legati, gia = set(), set()
            for n in nums:
                # il mercato più vicino prima della cifra, nella stessa proposizione, oppure subito prima di "(" della cifra
                cand = [a for a in als if a.end() <= n.start()]
                if not cand:
                    continue
                cand = [a for a in cand if not _tra_parentesi(fl, a)]
                if not cand:
                    continue
                a = cand[-1]
                tra = re.sub(r"\([^)]*\)", " ", fl[a.end():n.start()])
                if STACCO.search(tra) or len(tra.split()) > 10:
                    continue
                if re.search(r"(?<![.!?] )\b[A-Z][a-zA-Z&]{2,}", re.sub(r"\([^)]*\)", " ", f[a.end():n.start()])):
                    continue                    # un altro soggetto con un nome (una società) tra il mercato e la cifra
                rx, serie, genere = _alias(a)
                prima = fl[:a.start()]
                if _governato(prima) or (genere in ("luogo",) and _locativo(prima)):
                    continue
                s = next((x for x in serie if x in M), None)
                if not s or s in gia:
                    continue                    # dopo la prima cifra di un mercato, le altre raccontano la seduta
                dopo = fl[n.end():n.end() + 60]
                if re.match(r"\s*(?:di|del|della|dei|delle|degli|dell')\b", dopo):
                    continue                    # "il 40% del listino": una quota, non una variazione
                taglio = FINE.search(dopo)
                dopo = dopo[:taglio.start()] if taglio else dopo
                if ALIAS.search(" ".join(dopo.split()[:4])):
                    continue                    # "perde il 2,4% Tokyo": il soggetto viene dopo la cifra
                inizio = max([x.end() for x in STACCO.finditer(fl[:a.start()])] or [0])
                frase_mercato = fl[inizio:n.end()] + dopo      # la proposizione: periodo e "se" si cercano qui
                if COND.search(frase_mercato):
                    continue                    # ipotesi, regola generale o frequenza: non è la seduta di oggi
                finestra = fl[a.end():n.end()] + dopo          # il verbo del mercato: dopo il suo nome
                m = M[s]
                testa = fl[max(a.end(), n.start() - 30):n.start()]
                segno, cifra, unita = n.group(1), n.group(2), (n.group(3) or "").strip()
                x, tol = _num(cifra), 0.5 * 10 ** -_dec(cifra) + 1e-9
                lettura = None
                # livelli: "a 22.410,80 punti", "al 4,92%", "da 106", "sotto i 3.520 $"
                livello_unita = unita in ("punti", "$", "dollari") or (unita in ("%",) and m["tipo"] == "pb") or \
                    (unita in ("pb", "punti base") and m["tipo"] == "spread") or (not unita and s == "EUR/USD" and _dec(cifra) >= 3)
                chiude = bool(CHIUSURA.search(fl[a.end():n.start()]))
                if livello_unita and fuori_seduta(frase_mercato, m["data"], chiude):
                    continue                    # "da 4,98% a 5,10% in una settimana": livelli di altri giorni
                if livello_unita and not segno and (LIVELLO.search(testa) or PRIMA.search(testa)):
                    rif = m["v1"] if PRIMA.search(testa) else m["v0"]
                    if CIRCA.search(testa) or QUASI.search(testa) or OLTRE.search(testa):
                        tol = abs(rif) * 0.015       # "vicino a 52.000 punti"
                    if abs(x - rif) > tol and not (s == "VIX" and unita == "punti"):
                        lettura = f"livello {cifra}{(' ' + unita) if unita else ''}, in dati.json {rif:g}"
                    legati.add(a.start())
                elif livello_unita and not segno and (SOGLIA_SOTTO.search(testa) or SOGLIA_SOPRA.search(testa)):
                    if SOGLIA_SOTTO.search(testa) and not m["v0"] < x or SOGLIA_SOPRA.search(testa) and not m["v0"] > x:
                        lettura = f"\"{testa.strip()} {cifra}\", ma il livello in dati.json è {m['v0']:g}"
                    legati.add(a.start())
                elif unita in ("%", "per cento", "pb", "punti base", "punti") or segno:
                    if unita in ("%", "per cento") and m["tipo"] in ("pb", "spread"):
                        continue                # un rendimento in % senza "a/al" non è una variazione
                    if unita in ("pb", "punti base") and m["tipo"] not in ("pb", "spread"):
                        continue
                    if unita == "punti" and m["tipo"] != "punti":
                        continue                # "ai 5.000 punti": un livello in una forma che non si confronta
                    testa_frase = fl[:n.end()] + dopo
                    if fuori_seduta(frase_mercato, m["data"], chiude):
                        orizzonti = ["s", "s2"] if SETT.search(frase_mercato) else ["a"] if ANNO.search(frase_mercato) else []
                    elif fuori_seduta(testa_frase, m["data"], chiude):     # un periodo detto prima, nella stessa frase: vale anche la seduta
                        orizzonti = ["g"] + (["s", "s2"] if SETT.search(testa_frase) else ["a"] if ANNO.search(testa_frase) else [])
                        if len(orizzonti) == 1:
                            continue
                    else:
                        orizzonti = ["g"]
                    valori = [(o, m["pct_g"] if s == "VIX" and unita in ("%", "per cento") and o == "g" else _attese(m, o))
                              for o in orizzonti]
                    valori = [(o, v) for o, v in valori if v is not None]
                    if not valori:
                        continue
                    con_verso = bool(segno or GIU.search(finestra) or SU.search(finestra))
                    if con_verso:
                        verso = -1 if (segno in ("-", "−") or (not segno and GIU.search(finestra) and not SU.search(finestra))) \
                            else 1
                        if s == "EUR/USD" and genere == "inverso":
                            verso = -verso
                        x = x * verso

                    def torna(att, o):
                        # la settimana e l'anno si contano da un giorno che chi scrive può scegliere diverso: margine largo
                        tol_o = tol if o == "g" else max(tol, 0.3, abs(att) * 0.1)
                        if not con_verso:
                            att = abs(att)
                        if OLTRE.search(testa):
                            return abs(x) - tol <= abs(att) <= abs(x) * 1.25 + 0.3 and (x * att > 0 or x == 0)
                        if QUASI.search(testa):
                            return abs(x) * 0.8 - 0.1 <= abs(att) <= abs(x) + tol and (x * att >= 0)
                        if CIRCA.search(testa):
                            return abs(abs(att) - abs(x)) <= abs(x) * 0.15 + 0.1 and (x * att >= 0)
                        return abs(x - att) <= tol_o
                    if not any(torna(v, o) for o, v in valori):
                        orizzonte, att = valori[-1]
                        per = {"g": "nella seduta", "s": "nella settimana", "s2": "nella settimana chiusa ieri",
                               "a": "da inizio anno"}[orizzonte]
                        lettura = f"\"{f[a.start():n.end()].strip()}\": {s} {per} {_fmt(att, 2)}" + \
                                  ("%" if m["tipo"] not in ("pb", "spread") or unita in ("%", "per cento") else " pb")
                    legati.add(a.start())
                if a.start() in legati:
                    gia.add(s); CONTA["cifre"] += 1
                if lettura:
                    err.append(f"cifre: {dove}: {lettura}. La cifra va su chi l'ha fatta: se è di un altro listino o di un "
                               "titolo, il soggetto è quello; se è del mercato, vale quella di dati.json")
            # direzioni senza cifra: "il dollaro sale", "il Brent resta fermo"
            if COND.search(f):
                continue
            for a in als:
                if a.start() in legati or _tra_parentesi(fl, a):
                    continue
                rx, serie, genere = _alias(a)
                s = next((x for x in serie if x in M), None)
                prima = fl[:a.start()]
                if not s or _governato(prima) or (genere == "luogo" and _locativo(prima)):
                    continue
                dopo = fl[a.end():]
                st = STACCO.search(dopo)
                dopo = dopo[:st.start()] if st else dopo
                inizio = max([x.end() for x in STACCO.finditer(prima)] or [0])
                fine = FINE.search(dopo)
                if fuori_seduta(prima[inizio:] + fl[a.start():a.end()] + (dopo[:fine.start()] if fine else dopo), M[s]["data"],
                                bool(CHIUSURA.search(dopo[:fine.start()] if fine else dopo))):
                    continue                    # la proposizione del mercato parla di un altro periodo o momento
                dopo = " ".join(dopo.split()[:5])
                if ALIAS.search(dopo):
                    continue
                m, d = M[s], M[s]["g"]
                if SU.search(dopo) or GIU.search(dopo) or FERMO.search(dopo):
                    CONTA["direzioni"] += 1
                if genere == "inverso":
                    d = -d
                minimo = 1 if m["tipo"] in ("pb", "spread") else 0.05
                fermo_max = 3 if m["tipo"] in ("pb", "spread") else (0.2 if s == "EUR/USD" else 0.3)
                verbo = None
                if FERMO.search(dopo) and abs(d) > fermo_max:
                    verbo = "fermo"
                elif SU.search(dopo) and not GIU.search(dopo) and not FERMO.search(dopo) and not d >= minimo:
                    verbo = "su"
                elif GIU.search(dopo) and not SU.search(dopo) and not FERMO.search(dopo) and not d <= -minimo:
                    verbo = "giù"
                if verbo:
                    u = " pb" if m["tipo"] in ("pb", "spread") else "%"
                    err.append(f"direzioni: {dove}: \"{f[a.start():a.end() + len(dopo) + 1].strip()}\" dice {verbo}, ma "
                               f"nella seduta {s} fa {_fmt(m['g'], 2)}{u}" + (" (il dollaro va al contrario)" if genere == "inverso" else ""))
    return err


# ------------------------------------------------------------------ 1b. rimandi
VUOTE = set("""della delle dello degli dalla dalle dallo dagli nella nelle nello negli sulla sulle sullo sugli alla alle allo
agli come anche però perché quando mentre dopo prima ancora sempre sono essere stato stata hanno questo questa quello quella
più meno molto tutto tutti ogni altro altri altre dove oggi ieri domani venerdì giovedì mercoledì martedì lunedì mercati mercato
borsa borse prezzi prezzo titoli titolo settimana seduta pagina perde perdono scende scendono salgono chiude chiudono quasi
circa livello livelli punti minimi massimi calo rialzo ribasso vendite vendono""".split())


def _radici(t):
    return {w[:6] for w in re.findall(r"[a-zà-ù]{5,}", t.lower()) if w not in VUOTE}


def _testate():
    try:
        import controlli_testo as CT
        return {re.sub(r"[^a-z]", "", str(x).lower()) for x in CT.NOMI_BASE}
    except Exception:  # noqa: BLE001
        return set()


GENERICI = {"fed", "usa"}       # troppo comuni per dire di che cosa parla un testo ("Philadelphia Fed" non è la Fed)


def _nomi(t):
    """I nomi propri della frase, senza le testate: "Reuters" in comune non dice che due testi parlano della stessa cosa."""
    nomi = {w.lower() for w in re.findall(r"(?<![.!?] )(?<!^)\b[A-Z][A-Za-z&]{2,}", t)} | \
        {w.lower() for w in re.findall(r"\b[A-Z]{2,}[a-z]*\b", t)}
    return {w for w in nomi if re.sub(r"[^a-z]", "", w) not in _testate()} - GENERICI


def _nomi_e_mercati(t, chiave):
    """I nomi che dicono di che cosa parla un testo: i nomi propri, i mercati di MERCATI (anche se scritti in minuscolo:
    "l'oro", "il petrolio") e la chiave del pezzo, quando il testo la nomina ("→ [[oro]]" da una frase sull'oro)."""
    tl = t.lower()
    out = _nomi(t) | {MERCATI[int(next(k for k, v in a.groupdict().items() if v)[1:])][1][0] for a in ALIAS.finditer(tl)}
    if len(chiave) >= 3 and chiave.lower() not in GENERICI and re.search(rf"\b{re.escape(chiave.lower())}\b", tl):
        out.add(chiave.lower())
    return out


# Le famiglie dei dati del calendario: "Prezzi al consumo USA" e un pezzo sull'inflazione parlano della stessa cosa anche
# senza parole in comune. Elenco chiuso e generale: che cosa misurano i dati macro, non i fatti di un giorno.
FAMIGLIE = {
    "inflazione": r"prezz|inflazion|\bcpi\b|\bpce\b|\bppi\b|deflator",
    "lavoro": r"sussid|disoccupa|occupa|buste paga|payroll|lavor|salar",
    "attività": r"\bpmi\b|\bism\b|indice manifatturiero|produzione industriale|manifattur|ordini|attività delle imprese|fiducia",
    "crescita": r"\bpil\b|crescita|recession",
    "consumi": r"vendite al dettaglio|consum|spesa delle famiglie",
    "banche centrali": r"\bfed\b|\bbce\b|\bboj\b|banca centrale|banca del giappone|riunione|verbal|tassi d'interesse",
    "casa": r"\bcase\b|immobiliar|mutu|cantier",
}


def _famiglie(t):
    t = re.sub(r"(?:philadelphia|richmond|dallas|kansas city|chicago|new york|empire)(?: state)? fed",
               "indice manifatturiero", t.lower())
    return {k for k, rx in FAMIGLIE.items() if re.search(rx, t)}


def rimandi(C):
    err = []
    pezzi = {m.get("chiave"): m for m in C.get("moduli") or [] if m.get("chiave")}
    def testo_pezzo(m):
        return " ".join(_pulisci(x) for x in [m.get("titolo"), m.get("tema"), m.get("breve"), m.get("perche"), m.get("quindi"),
                                              m.get("guardare"), *(m.get("testo") or []), *(m.get("punti") or []),
                                              json.dumps(m.get("righe") or [], ensure_ascii=False)] if x)
    voci = []
    for i, n in enumerate(C.get("notizie") or []):
        if isinstance(n, dict) and n.get("rimando"):
            voci.append((f"notizie.{i}", f"{n.get('titolo', '')}. {n.get('testo', '')}", n["rimando"]))
    for i, x in enumerate(C.get("in30") or []):
        for k in re.findall(r"\[\[(\w+)\]\]", str(x)):
            voci.append((f"in30.{i}", str(x), k))
    for chi in ("ieri", "agenda"):
        for i, a in enumerate(C.get(chi) or []):
            for k in re.findall(r"\[\[(\w+)\]\]", " ".join(str(c) for c in a)):
                voci.append((f"{chi}.{i}", " ".join(str(c) for c in a if "[[" not in str(c)), k))
    t = C.get("top") or {}
    for k in re.findall(r"\[\[(\w+)\]\]", f"{t.get('dek', '')} {C.get('quadro', '')}"):
        voci.append(("top", f"{t.get('titolo', '')}. {t.get('dek', '')}", k))
    for dove, frase, k in voci:
        if k not in pezzi:
            continue                            # mercati, agenda, scommessa: pagine fisse
        CONTA["rimandi"] += 1
        tp = testo_pezzo(pezzi[k])
        nomi = _nomi_e_mercati(_pulisci(frase), k) & (_nomi_e_mercati(tp, k) | {k.lower()} - GENERICI)
        radici = _radici(_pulisci(frase)) & _radici(tp)
        famiglie = _famiglie(_pulisci(frase)) & _famiglie(tp) if dove.startswith(("ieri", "agenda")) else set()
        if not nomi and len(radici) < 2 and not famiglie:
            err.append(f"rimandi: {dove} rimanda a \"{pezzi[k].get('titolo', k)[:60]}\", che non ne parla (nessun nome e "
                       "meno di due parole in comune): il rimando va al pezzo che racconta quel fatto, o si toglie")
    return err


# ------------------------------------------------------------------ 1c. titoli
IPOTESI = re.compile(r"\b(?:forse|probabilmente|potrebbe|potrebbero|sembra|sembrano|pare|parrebbe|ipotesi|chissà|magari)\b", re.I)


def titoli(C):
    err = []
    t = C.get("top") or {}
    tt = [("top.titolo", t.get("titolo"))] + [(f"notizie.{i}.titolo", n.get("titolo")) for i, n in
                                              enumerate(C.get("notizie") or []) if isinstance(n, dict)]
    for m in C.get("moduli") or []:
        tt += [(f"moduli.{m.get('chiave')}.titolo", m.get("titolo")), (f"moduli.{m.get('chiave')}.breve", m.get("breve"))]
    for dove, x in tt:
        if x and IPOTESI.search(_pulisci(x)):
            err.append(f"titoli: {dove}: \"{_pulisci(x)[:70]}\" mette un'ipotesi nel titolo. Il titolo dice il fatto e, se "
                       "c'è, la causa verificata; un'ipotesi resta nel testo, dichiarata come nostra lettura")
    return err


# ------------------------------------------------------------------ 2. il ragionamento, per il revisore
CAUSA = re.compile(r"\bperch[ée]\b|per via d|a causa d|\bpes(?:a|ano|ato)\b|spinge|spingono|trascina|frena|complice|dovut[oa]|"
                   r"grazie a|la ragione|il motivo|a nostro avviso|per noi|leggiamo|secondo (?!giorno|trimestre|semestre|anno|mandato|posto)|effetto d|sotto la pressione|"
                   r"alimenta|sostiene|sostengono|sulla scia|dietro (?:il|la|l')|colpa", re.I)
EVENTO = re.compile(r"\b(?:indagine|inchiesta|accordo|intesa|dazi|dazio|sanzion\w+|causa legale|esposto|offerta|opa|ops|"
                    r"ricorso|multa|divieto|strett[ae]|giro di vite|embargo|riforma|pacchetto|piano di)\b", re.I)


def frasi_da_ragionare(C, campi, massimo=24):
    """Le frasi che il revisore giudica contro i prezzi e le schede, in ordine di importanza."""
    scelte, viste, eventi = [], set(), set()

    def metti(dove, f, perche):
        f = _pulisci(f)
        if f and not any(f in v for v in viste):        # una frase già dentro un Perché scelto non si ripete
            viste.add(f); scelte.append({"dove": dove, "frase": f, "perche_qui": perche})
    t = C.get("top") or {}
    metti("top.titolo", t.get("titolo", ""), "titolo")
    for m in C.get("moduli") or []:
        metti(f"moduli.{m.get('chiave')}.titolo", m.get("titolo", ""), "titolo")
        if m.get("perche"):
            metti(f"moduli.{m.get('chiave')}.perche", m["perche"], "causa")
    for dove, testo in campi.items():
        if dove.startswith("agenda") or dove.endswith((".numero", ".guardare")):
            continue
        for f in frasi(testo):
            for e in EVENTO.findall(f.lower()):
                if e[:5] not in eventi:
                    eventi.add(e[:5]); metti(dove, f, "primo fatto")
            if CAUSA.search(f):
                metti(dove, f, "causa")
    for i, n in enumerate(C.get("notizie") or []):
        if isinstance(n, dict) and CAUSA.search(str(n.get("titolo", ""))):
            metti(f"notizie.{i}.titolo", n["titolo"], "titolo")
    ordine = {"titolo": 0, "primo fatto": 1, "causa": 2}
    scelte = sorted(scelte, key=lambda x: (ordine[x["perche_qui"]], not x["dove"].endswith(".perche")))[:massimo]
    for i, x in enumerate(scelte, 1):
        x["id"] = f"R{i:02d}"
    return scelte


ISTRUZIONI_REVISORE = (
    "Senza aprire pagine. Per ogni frase rispondi in coerenza.json: [{\"id\", \"esito\": \"regge\" | \"non_regge\", \"nota\", "
    "\"rimedio\"}]. Non regge se: (1) dà una causa a un movimento e la causa non si è mossa nello stesso periodo nel verso "
    "giusto secondo i prezzi qui sotto (per esempio il dollaro forte con EUR/USD fermo nella seduta, i tassi in salita con il "
    "10 anni giù), o la stessa edizione dice il contrario altrove; (2) nomina un fatto che muove la storia (un'indagine, un "
    "accordo, un dazio) senza dire chi fa che cosa e su che cosa, o lo dice in modo diverso dal fatto delle schede che hai; "
    "(3) è un titolo con un'ipotesi o con una causa che non regge. La nota dice che cosa non torna con i numeri, in una frase. "
    "Il rimedio è uno di: \"chi la dà\" (la spiegazione di chi la dà, con la sua scheda), \"lettura con i prezzi\" (la nostra "
    "lettura con i prezzi che la sostengono), \"solo il fatto\" (via la causa), \"spiegare il fatto\" (chi, che cosa, su che "
    "cosa), \"titolo col fatto\". Nel dubbio regge: si ferma solo ciò che i numeri smentiscono o lasciano vuoto.")


def scrivi_incarico(C, campi, M, cartella):
    inc = {"istruzioni": ISTRUZIONI_REVISORE, "prezzi": scheda_prezzi(M), "frasi": frasi_da_ragionare(C, campi)}
    json.dump(inc, open(os.path.join(cartella, INCARICO), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return inc


def verdetti(campi, cartella):
    """Al giro finale: ogni frase dell'incarico ha l'esito; una "non_regge" ancora nel testo ferma."""
    err, avv = [], []
    pi, pr = os.path.join(cartella, INCARICO), os.path.join(cartella, RISPOSTA)
    if not os.path.exists(pi):
        return ["ragionamento: manca coerenza_incarico.json: lo scrive controlli_tutti.sh --prima-della-revisione"], avv
    inc = json.load(open(pi, encoding="utf-8"))
    if not os.path.exists(pr):
        return [f"ragionamento: manca coerenza.json: il revisore giudica le {len(inc.get('frasi') or [])} frasi di "
                "coerenza_incarico.json contro i prezzi (ISTRUZIONI §4.7)"], avv
    try:
        ris = {str(e.get("id")): e for e in json.load(open(pr, encoding="utf-8")) if isinstance(e, dict)}
    except (ValueError, AttributeError):
        return ["ragionamento: coerenza.json non è una lista di esiti [{\"id\", \"esito\", \"nota\", \"rimedio\"}]"], avv
    testo = " ".join(_pulisci(v) for v in campi.values())
    for x in inc.get("frasi") or []:
        e = ris.get(x["id"])
        if not e or e.get("esito") not in ("regge", "non_regge"):
            err.append(f"ragionamento: {x['id']} ({x['dove']}) senza esito \"regge\" o \"non_regge\" in coerenza.json")
        elif e["esito"] == "non_regge" and x["frase"] in testo:
            rim = e.get("rimedio") if e.get("rimedio") in RIMEDI else "chi la dà, lettura con i prezzi o solo il fatto"
            err.append(f"ragionamento: {x['dove']}, rimedio \"{rim}\": \"{x['frase'][:70]}...\" non regge: "
                       f"{str(e.get('nota', ''))[:150]}")
    return err, avv


# ------------------------------------------------------------------
def main():
    a = sys.argv[1:]
    ed = os.path.abspath(a[0])
    dati = os.path.abspath(a[a.index("--dati") + 1]) if "--dati" in a else os.path.join(os.path.dirname(ed), "dati.json")
    prima = "--prima-della-revisione" in a
    cartella = os.path.dirname(ed)
    os.chdir(cartella)              # l'edizione legge i suoi file (serie dei grafici, dati.json) dalla cartella di lavoro
    import controlli_testo as CT
    import desk
    C = CT.edizione(ed)
    campi = {k: _pulisci(v) for k, v in desk.campi(C).items()}
    D = json.load(open(dati, encoding="utf-8")) if os.path.exists(dati) else {}
    M = mercati_del_giorno(D) if D else {}
    err = (cifre_e_direzioni(campi, M) if M else []) + rimandi(C) + titoli(C)
    avv = [] if M else ["cifre e direzioni non confrontate: manca dati.json"]
    if prima:
        inc = scrivi_incarico(C, campi, M, cartella)
        avv.append(f"incarico del revisore: {INCARICO}, {len(inc['frasi'])} frasi; risposta in {RISPOSTA}")
    elif os.environ.get("GTD_SENZA_RAGIONAMENTO") == "1":
        # un'edizione già uscita, scritta prima di G-45: nessun incarico archiviato, il ragionamento non si giudica
        avv.append("ragionamento non giudicato: edizione scritta senza coerenza_incarico.json (prima di G-45)")
    else:
        e2, a2 = verdetti(campi, cartella)
        err += e2; avv += a2
    print(f"Coerenza (testo contro dati e schede): {CONTA['cifre']} cifre, {CONTA['direzioni']} direzioni e "
          f"{CONTA['rimandi']} rimandi confrontati | errori: {len(err)}")
    for e in err:
        print("ERRORE: " + e[:300])
    for x in avv:
        print("AVVISO: " + x[:200])
    sys.exit(1 if err else 0)


if __name__ == "__main__":
    main()
