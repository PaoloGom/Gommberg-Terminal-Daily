"""Le serie dei grafici a linea reggono (G-72, 28/11/2026). Uso (cartella di lavoro):
  python3 controlli_grafici.py <edizione.py> [--dati dati.json]

Nato dalla prova del 28/11 (#036, pag. 2): due grafici con tre tratti sovrapposti su due settimane. La serie era un anno
di chiusure ridotto a "mese-giorno" e filtrato "dal 6 ottobre": passavano anche novembre e dicembre dell'anno prima,
disegnati sui giorni di quest'anno. Il motore disegna ciò che riceve, e nessun controllo guardava le serie: i numeri si
confrontavano con dati.json solo nel testo e nelle tabelle, e l'anteprima a 45 dpi non mostra una linea doppia.

Qui si guarda la serie di OGNI grafico a linea dell'edizione (C["moduli"], "grafico" e "grafico2"), prima che esca:
 tempo     le x sono date vere, strettamente crescenti, senza doppioni, non future; ogni serie ha un valore per data;
           nessun buco di mesi; una serie con il nome di un mercato di dati.json non ha punti di sabato o domenica.
           Le x che non sono date (scadenze della curva, nomi) sono categorie: si conta solo un valore per categoria.
 periodo   il sottotitolo dice misura e periodo: "dal <giorno>" è la prima data, "dal <giorno> al <giorno>" anche
           l'ultima, "<giorno> = 100" è la base, "ultimo mese", "ultime N sedute", "da inizio anno" sono la durata. Una
           data di partenza nel titolo ("dal <giorno>", "dal massimo del <giorno>") sta dentro il periodo disegnato.
 chiusure  una serie che ha il nome di un mercato di dati.json porta le sue chiusure: l'ultimo punto è l'ultima chiusura
           (mezza unità dell'ultima cifra stampata, come controlli_numeri.py), non una data successiva né una seduta
           prima; gli altri punti coincidono con l'archivio delle chiusure dove l'archivio li conosce (da tre punti
           diversi in su è un errore, uno o due un AVVISO: può essere l'archivio). A base 100 si confronta il rapporto
           con la chiusura del giorno base. Serie trasformate (variazioni, differenze, medie, spot) non si confrontano.
 segni     note (data, valore, etichetta) sulla linea, eventi dentro il periodo, soglie con l'etichetta uguale al valore.
 titolo    "da A a B" passa per A e poi per B nella serie; "X% dal massimo del <giorno>" torna con i valori; "sale a N"
           è l'ultimo valore. Cifre tonde valgono come tali: "60.000" è un ordine di grandezza, "59.662" no.

Esito: righe ERRORE e uscita 1, con il rimedio sotto il primo errore. Chi scrive corregge la serie; se non ci riesce
toglie il grafico e il modulo esce senza (regola dei grafici nel modello, APP_ERRORI.md §4): l'edizione esce comunque.
controlla_grafico() non dipende dal motore: la usano anche il collaudo e le misure sulle edizioni uscite."""
import datetime as dt
import json
import math
import os
import re
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)

MESI = "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split()
_MESE = "|".join(MESI)
# un giorno scritto in un titolo: "6 ottobre", "1° novembre", "16/11", "16/11/2026"
GIORNO = rf"(\d{{1,2}})[°º]?(?:\s(?:di\s)?({_MESE})(?:\s(20\d\d))?|/(\d{{1,2}})(?:/(\d{{2,4}}))?)"
DAL_AL = re.compile(rf"\bdal(?:l')?\s?(\d{{1,2}})[°º]?(?:\s({_MESE})|/(\d{{1,2}}))?\s+al(?:l')?\s?{GIORNO}", re.I)
DAL = re.compile(rf"\bdal(?:l')?\s?{GIORNO}", re.I)
DAL_ESTREMO = re.compile(rf"\bdal?(?:l[ae']|i)?\s?(?:massim[oi]|minim[oi]|picc[oh]i?)\b[^.;:,]{{0,30}}?\b(?:del(?:l')?|di|il)\s?{GIORNO}", re.I)
BASE = re.compile(rf"{GIORNO}\s?=\s?100\b", re.I)
# "il minimo dal 3 marzo", "il calo più forte dal 2 aprile": la data misura una rarità, non l'inizio del grafico
RARITA = re.compile(r"(?:minim|massim|record|peggior|miglior|più (?:alt|bass|fort|ampi|grand|lung)|mai così|prima volta)"
                    r"[^.;:]{0,40}$", re.I)
_N = {"un": 1, "una": 1, "due": 2, "tre": 3, "quattro": 4, "cinque": 5, "sei": 6, "sette": 7, "otto": 8, "nove": 9,
      "dieci": 10, "dodici": 12}
_QUANTI = r"(\d{1,3}|" + "|".join(_N) + ")"
DURATA = re.compile(rf"\bultim[oaie]\s(?:{_QUANTI}\s)?(mes[ei]|settiman[ae]|ann[oi]|trimestr[ei]|semestr[ei]|sedut[ae]|giorn[oi])\b", re.I)
INIZIO = re.compile(rf"\bda(?:ll')?\s?inizio\s(?:dell')?(anno|mese|{_MESE})\b", re.I)
GIORNI_DI = {"mes": 30, "settiman": 7, "ann": 365, "trimestr": 91, "semestr": 182, "giorn": 1}
NUM = r"(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?)"
QUAL = r"(oltre|più di|poco più di|sopra|quasi|circa|intorno a|meno di|poco meno di|sotto)?\s?(?:i\s|il\s|gli\s|l')?"
NON_LIVELLO = rf"(?!\s?(?:ann[oi]|mes[ei]|giorn[oi]|sedut[ae]|settiman[ae]|ore\b|volte|punti percentuali|{_MESE}|/\d))"
DA_A = re.compile(rf"\bda(?:i|gli|l|ll')?\s?{QUAL}{NUM}(?!\d)\s?(?:%|\$|punti base|punti|pb|dollari|euro)?\s(?:a|ai|al|agli|all')\s?{QUAL}{NUM}(?!\d){NON_LIVELLO}", re.I)
PCT_DAL = re.compile(rf"{QUAL}[+\-−]?{NUM}\s?%[^.;:]{{0,40}}?\bdal?(?:l[ae']|i)?\s?(?:massim[oi]|minim[oi]|picc[oh]i?)\b[^.;:,]{{0,30}}?\b(?:del(?:l')?|di|il)\s?{GIORNO}", re.I)
ARRIVA_A = re.compile(rf"\b(?:sale|risale|scende|ridiscende|torna|ritorna|arriva|cala|chiude|si ferma)\s(?:fino\s)?(?:a|ai|al|agli|all')\s?{QUAL}{NUM}(?!\d)(\s?%)?{NON_LIVELLO}", re.I)
DISTANZA = re.compile(r"\s?(?:%|\$|punti base|punti|pb|dollari|euro)?\s(?:da|dal|dall[ao']|dai|sotto|sopra|in più|in meno)\b", re.I)
# serie che non sono il livello di chiusura del mercato di cui portano il nome
TRASFORMATA = re.compile(r"=\s?100\b|base 100|variazion|\bvar\.|differenz|\bmeno\b|rapporto|\bmedia\b|scart|spot|"
                         r"in euro|\breal[ei]\b|intraday|in seduta|stamattina|future sull|cumulat|rendimento totale", re.I)
ALTRA_SCALA = re.compile(r"=\s?100\b|base 100|variazion|\bvar\.|rapporto|cumulat", re.I)   # il titolo può dare i livelli
# come un grafico chiama i mercati di dati.json (il nome intero della serie, non una parola dentro)
NOMI = [(r"s&p(?: ?500)?", ("S&P 500",)), (r"nasdaq(?: comp\.?| composite)?", ("Nasdaq",)),
        (r"russell(?: 2000)?", ("Russell 2000",)), (r"euro ?stoxx(?: 50)?", ("Euro Stoxx 50",)),
        (r"ftse ?mib", ("FTSE MIB",)), (r"nikkei(?: 225)?", ("Nikkei 225",)), (r"hang seng", ("Hang Seng",)),
        (r"kospi", ("Kospi",)), (r"vix", ("VIX",)), (r"(?:msci )?acwi", ("ACWI",)),
        (r"brent(?: future)?", ("Brent future",)), (r"oro(?: future)?", ("Oro future", "Oro")),
        (r"eur/usd|euro[-/]dollaro", ("EUR/USD",)), (r"spread(?: italia| btp-bund| tra btp e bund)?", ("Spread Italia",)),
        (r"(?:(?:rendimento )?(?:del )?treasury (?:a )?)?10 anni", ("Treasury 10 anni",)),
        (r"(?:(?:rendimento )?(?:del )?treasury (?:a )?)?2 anni", ("Treasury 2 anni",))]
SOLO_CON = {"Treasury 10 anni": "treasury", "Treasury 2 anni": "treasury"}   # "10 anni" da solo può essere un Bund


def _testo(t):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", str(t or "")).replace("&amp;", "&")).strip()


def _num(s):
    return float(s.replace(".", "").replace(",", "."))


def _passo(s, tonda=True):
    """Mezza unità dell'ultima cifra che conta: "35,9" 0,05; "7.297" 0,5; "60.000" 5.000 (una cifra tonda in un titolo
    è un ordine di grandezza; tonda=False per le etichette, che dicono un livello esatto)."""
    if "," in s:
        return 0.5 * 10 ** -len(s.split(",")[1])
    cifre = s.replace(".", "")
    zeri = len(cifre) - len(cifre.rstrip("0")) if tonda else 0
    return 0.5 * 10 ** min(zeri, len(cifre) - 1)


def _vale(v, s, qual=""):
    """Il valore v è quello scritto come s? Con "oltre", "quasi", "circa" vale come tale."""
    n, q = _num(s), (qual or "").lower()
    largo = max(0.05 * abs(n), 2 * _passo(s))
    if q in ("oltre", "più di", "poco più di", "sopra"):
        return n - _passo(s) <= v <= n + largo
    if q in ("quasi", "meno di", "poco meno di", "sotto"):
        return n - largo <= v <= n + _passo(s)
    if q in ("circa", "intorno a"):
        return abs(v - n) <= largo
    return abs(v - n) <= _passo(s) + 1e-9


def _gm(d):
    return f"{d.day}/{d.month}/{d.year}"


def _it(v):
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s.rstrip("0").rstrip(",") if "," in s else s


def _giorno(m, i, fine, anno=None):
    """La data scritta nei gruppi i..i+4 di GIORNO: l'anno, se manca, è l'ultimo che non la porta dopo `fine`."""
    g, mese, a1, m2, a2 = (m.group(k) for k in range(i, i + 5))
    mm = MESI.index(mese.lower()) + 1 if mese else int(m2)
    a = a1 or a2 or anno
    try:
        if a:
            return dt.date(int(a) + (2000 if int(a) < 100 else 0), mm, int(g))
        d = dt.date(fine.year, mm, int(g))
        return d if d <= fine + dt.timedelta(days=7) else dt.date(fine.year - 1, mm, int(g))
    except ValueError:
        return None


def _sembra_data(s):
    return bool(re.fullmatch(r"\s*(?:\d{1,2}[/.\-]\d{1,2}(?:[/.\-]\d{2,4})?|20\d\d-\d{1,2}(?:-\d{1,2})?)\s*", str(s)))


def _decimali(g, valori):
    """I decimali con cui il motore stampa l'ultimo valore (gommberg_engine.linee)."""
    if g.get("dec") is not None:
        return int(g["dec"])
    r = max(valori) - min(valori)
    return 0 if r >= 50 else 1 if r >= 5 else 2


def mercato(nome, contesto, serie_dati):
    """La serie di dati.json di cui la serie del grafico porta il nome, o None."""
    n = re.sub(r"\(.*?\)", "", _testo(nome)).strip().lower()
    for rx, candidati in NOMI:
        if re.fullmatch(rx, n):
            k = next((c for c in candidati if c in serie_dati), None)
            if k and SOLO_CON.get(k, "") in contesto.lower():
                return k
    return None


def _storie(D):
    """{serie di dati.json: {data: chiusura}} dall'archivio e da dati.json (numeri.storia); la seduta in corso resta fuori."""
    if not D:
        return {}, {}
    import numeri as N
    oggi = str(D.get("oggi", ""))[:10]
    st, ultima = {}, {}
    for nome, s in (D.get("serie") or {}).items():
        h = dict(N.storia(nome, s))
        if s.get("tipo") == "intraday" and oggi:
            h.pop(oggi, None)                      # il livello di stamattina non è una chiusura
        if h:
            st[nome] = h
            u = [str(r[0])[:10] for r in s.get("ultimi") or [] if len(r) >= 2 and isinstance(r[1], (int, float))]
            u = [d for d in u if d in h]
            if u:
                ultima[nome] = max(u)
    return st, ultima


def controlla_grafico(g, oggi=None, storie=None, ultime=None, conta=None, avvisi=None):
    """Gli errori di un grafico a linea (dict come lo vuole il motore). oggi = data dell'edizione; storie e ultime da
    _storie(dati.json); in avvisi (una lista) finisce ciò che non ferma. Torna [] se la serie regge."""
    err, avvisi = [], avvisi if avvisi is not None else []
    storie, ultime, conta = storie or {}, ultime or {}, conta if conta is not None else {}
    visto = lambda k, n=1: conta.__setitem__(k, conta.get(k, 0) + n)
    tit, sub = _testo(g.get("titolo")), _testo(g.get("sottotitolo"))
    x = list(g.get("x") or [])
    serie = []
    for s in g.get("serie") or []:
        if not isinstance(s, (list, tuple)) or len(s) != 3 or not isinstance(s[1], (list, tuple)):
            return [f"una serie non è scritta come (nome, [valori], colore): {str(s)[:60]}"]
        nome, v = _testo(s[0]), list(s[1])
        xs, ys = ([a for a, _ in v], [b for _, b in v]) if v and isinstance(v[0], tuple) else (x, v)
        serie.append((nome, list(xs), list(ys)))
    if not serie:
        return ["nessuna serie"]
    for nome, xs, ys in serie:
        if len(xs) != len(ys):
            err.append(f"serie {nome}: {len(ys)} valori per {len(xs)} date: un valore per ogni data")
        rotti = [y for y in ys if isinstance(y, bool) or not isinstance(y, (int, float)) or not math.isfinite(y)]
        if rotti:
            err.append(f"serie {nome}: {len(rotti)} valori non numerici ({str(rotti[0])[:20]})")
        if len(xs) < 2:
            err.append(f"serie {nome}: {len(xs)} punti: una linea ne vuole almeno due (meglio una frase)")
    if err:
        return err
    tutte = [a for _, xs, _ in serie for a in xs]
    quante_date = sum(isinstance(a, dt.date) for a in tutte)
    if quante_date == 0:
        if any(_sembra_data(a) for a in tutte):
            err.append(f"le x sono testi che sembrano date ({str(tutte[0])[:12]}): servono date vere, con l'anno")
        return err                                  # categorie (scadenze, nomi): non è una serie nel tempo
    if quante_date < len(tutte):
        return ["le x mescolano date e altri valori"]
    # ---- tempo
    for i, (nome, xs, ys) in enumerate(serie):
        serie[i] = (nome, [a.date() if isinstance(a, dt.datetime) else a for a in xs], ys)
    for nome, xs, ys in serie:
        j = next((i for i in range(1, len(xs)) if xs[i] <= xs[i - 1]), None)
        if j is not None:
            doppie = len(xs) - len(set(xs))
            if all(b < a for a, b in zip(xs, xs[1:])):
                err.append(f"serie {nome}: le date vanno dalla più recente ({_gm(xs[0])}) alla più vecchia ({_gm(xs[-1])}): "
                           "vanno in ordine di data, l'ultima seduta per ultima")
                continue
            come = f"{doppie} date ripetute" if doppie else "date non in ordine"
            err.append(f"serie {nome}: {come} ({_gm(xs[j])} dopo {_gm(xs[j - 1])}, punto {j + 1} di {len(xs)}): la serie "
                       "mescola due periodi, due anni o due mercati")
    if err:
        return err                                  # il resto non si giudica su una serie che non è una serie
    x0, x1 = min(xs[0] for _, xs, _ in serie), max(xs[-1] for _, xs, _ in serie)
    if oggi and x1 > oggi:
        err.append(f"l'ultima data ({_gm(x1)}) è dopo il giorno dell'edizione ({_gm(oggi)})")
    for nome, xs, ys in serie:
        passi = sorted((b - a).days for a, b in zip(xs, xs[1:]))
        tipico = passi[len(passi) // 2]
        j = next((i for i in range(1, len(xs)) if (xs[i] - xs[i - 1]).days >= max(45, 5 * tipico)), None)
        if j is not None:
            err.append(f"serie {nome}: buco di {(xs[j] - xs[j - 1]).days} giorni tra {_gm(xs[j - 1])} e {_gm(xs[j])} in "
                       f"una serie che ha un punto ogni {tipico}: due periodi diversi nella stessa serie?")
    contesto = tit + " " + sub + " " + " ".join(n for n, _, _ in serie)
    rif = oggi or x1                                # un giorno scritto senza anno è l'ultimo prima dell'edizione
    # ---- periodo: il sottotitolo lo dichiara
    m = DAL_AL.search(sub)
    if m:
        visto("periodo")
        b = _giorno(m, 4, rif)
        a = b and _giorno(re.match(GIORNO, f"{m.group(1)} {m.group(2)}" if m.group(2) else
                                   f"{m.group(1)}/{m.group(3) or b.month}"), 1, b)
        if a and b and not (a <= x0 <= a + dt.timedelta(days=4) and b - dt.timedelta(days=4) <= x1 <= b):
            err.append(f"il sottotitolo dice \"{m.group(0)}\" ma la serie va dal {_gm(x0)} al {_gm(x1)}")
    else:
        m = DAL.search(sub)
        m = None if m and RARITA.search(sub[:m.start()]) else m
        a = m and _giorno(m, 1, rif)
        visto("periodo", bool(a))
        if a and not a <= x0 <= a + dt.timedelta(days=4):
            err.append(f"il sottotitolo dice \"{m.group(0)}\" ma la serie comincia il {_gm(x0)} e finisce il {_gm(x1)}: "
                       "la prima data è quella del sottotitolo")
    m = BASE.search(sub)
    if m:
        a = _giorno(m, 1, rif); visto("periodo")
        for nome, xs, ys in serie:
            if a and (a not in xs or abs(ys[xs.index(a)] - 100) > 0.05):
                err.append(f"serie {nome}: \"{m.group(0)}\" ma il {_gm(a)} " +
                           (f"vale {_it(ys[xs.index(a)])}" if a in xs else "non è nella serie"))
    giorni = (x1 - x0).days
    m = DURATA.search(sub)
    if m:
        visto("periodo")
        n = int(m.group(1)) if (m.group(1) or "").isdigit() else _N.get((m.group(1) or "un").lower(), 1)
        u = m.group(2).lower()
        if u.startswith("sedut"):
            punti = max(len(xs) for _, xs, _ in serie)
            if abs(punti - n) > 1:
                err.append(f"il sottotitolo dice \"{m.group(0)}\" ma i punti sono {punti}")
        else:
            attesi = n * next(v for k, v in GIORNI_DI.items() if u.startswith(k))
            if not 0.55 * attesi <= giorni <= 1.5 * attesi + 3:
                err.append(f"il sottotitolo dice \"{m.group(0)}\" (circa {attesi} giorni) ma la serie copre {giorni} giorni, "
                           f"dal {_gm(x0)} al {_gm(x1)}")
    m = INIZIO.search(sub)
    if m:
        visto("periodo")
        u = m.group(1).lower()
        primo = dt.date(rif.year, 1 if u == "anno" else rif.month if u == "mese" else MESI.index(u) + 1, 1)
        if primo > rif:
            primo = primo.replace(year=primo.year - 1)
        if not primo - dt.timedelta(days=5) <= x0 <= primo + dt.timedelta(days=6):
            err.append(f"il sottotitolo dice \"{m.group(0)}\" ma la serie comincia il {_gm(x0)}")
    # ---- una data di partenza nel titolo sta nel periodo disegnato
    for rx in (DAL_ESTREMO, DAL):
        for m in rx.finditer(tit):
            a = _giorno(m, 1, rif)
            if rx is DAL and RARITA.search(tit[:m.start()]):
                continue
            visto("periodo")
            # il giorno di un massimo è una seduta e si deve vedere; "dal 1° del mese" può cadere di festa
            if a and not x0 - dt.timedelta(days=0 if rx is DAL_ESTREMO else 4) <= a <= x1:
                err.append(f"il titolo parte da \"{m.group(0)}\" ma il grafico va dal {_gm(x0)} al {_gm(x1)}: quel giorno non si vede")
    # ---- chiusure: la serie che porta il nome di un mercato di dati.json
    misura = sub + " " + " ".join(n for n, _, _ in serie)
    base = BASE.search(sub)
    base = base and _giorno(base, 1, rif)
    trasformata = bool(TRASFORMATA.search(BASE.sub("", misura) if base else misura))
    for nome, xs, ys in serie:
        k = None if trasformata else mercato(nome, contesto, storie)
        if not k:
            continue
        h = storie[k]
        visto("serie")
        fine = [a for a in xs if a.weekday() > 4]
        if fine:
            err.append(f"serie {nome}: {len(fine)} punti di sabato o domenica ({_gm(fine[0])}): non sono sedute")
        u = ultime.get(k) and dt.date.fromisoformat(ultime[k])
        passi = sorted((b - a).days for a, b in zip(xs, xs[1:]))
        tipico = passi[len(passi) // 2]
        if u and xs[-1] > u:
            err.append(f"serie {nome}: l'ultimo punto è del {_gm(xs[-1])}, dopo l'ultima chiusura di dati.json "
                       f"({_gm(u)}): un valore in corso di seduta non è una chiusura")
        elif u and tipico <= (u - xs[-1]).days <= max(10, 2 * tipico):   # più indietro è un grafico storico, voluto
            err.append(f"serie {nome}: si ferma al {_gm(xs[-1])} ma l'ultima chiusura di {k} in dati.json è del {_gm(u)} "
                       f"({_it(h[u.isoformat()])}): manca l'ultima seduta")
        if base:                                    # base 100: ogni punto è la chiusura divisa per quella del giorno base
            h0 = h.get(base.isoformat())
            cifre = max(len(repr(float(y)).split(".")[1]) if float(y) != int(y) else 0 for y in ys)
            tol = 2 * 10 ** -min(cifre, 4) + 1e-9   # chi scrive arrotonda: due unità dell'ultima cifra scritta
            h = {d: 100 * v / h0 for d, v in h.items()} if h0 else {}
        else:
            tol = 0.5 * 10 ** -_decimali(g, [y for _, _, yy in serie for y in yy]) + 1e-9
        diversi = [(a, y, h[a.isoformat()]) for a, y in zip(xs, ys) if a.isoformat() in h and abs(y - h[a.isoformat()]) > tol]
        visto("punti", sum(a.isoformat() in h for a in xs))
        if diversi:
            # l'ultimo valore è quello stampato: si ferma sempre. Prima dell'ultimo, uno o due punti diversi possono
            # essere una chiusura rivista o un errore dell'archivio (avviso); da tre in su la serie non è quel mercato
            ultimo = diversi[-1][0] == xs[-1]
            a, y, c = diversi[-1] if ultimo else diversi[0]
            dove = "l'ultimo valore" if ultimo else f"{len(diversi)} punti su {len(xs)} diversi dalle chiusure: il {_gm(a)}"
            (err if ultimo or len(diversi) >= 3 else avvisi).append(
                f"serie {nome}: {dove} è {_it(y)}, " + (f"con {k} a base 100 il {_gm(base)} il {_gm(a)} fa {_it(c)}"
                                                        if base else f"la chiusura di {k} del {_gm(a)} è {_it(c)}"))
    # ---- segni: note, eventi, soglie
    ymin, ymax = min(y for _, _, ys in serie for y in ys), max(y for _, _, ys in serie for y in ys)
    sulla = lambda v, y: abs(v - y) <= max(0.01 * (ymax - ymin), 1e-9)
    for nota in g.get("note") or ():
        try:
            nx, ny, nt = nota
        except (TypeError, ValueError):
            err.append(f"nota scritta male: {str(nota)[:50]} (data, valore, etichetta)"); continue
        nx = nx.date() if isinstance(nx, dt.datetime) else nx
        visto("segni")
        qui = [ys[xs.index(nx)] for _, xs, ys in serie if nx in xs]
        if not qui:
            err.append(f"nota \"{_testo(nt)}\": il {_gm(nx) if isinstance(nx, dt.date) else nx} non è una data della serie")
        elif not any(sulla(ny, y) for y in qui):
            err.append(f"nota \"{_testo(nt)}\" del {_gm(nx)}: vale {_it(ny)} ma la serie quel giorno è a {_it(qui[0])}: "
                       "il punto non sta sulla linea")
        m = re.fullmatch(GIORNO, _testo(nt))
        if m and isinstance(nx, dt.date) and _giorno(m, 1, rif, nx.year) != nx:
            err.append(f"nota \"{_testo(nt)}\": l'etichetta è un giorno diverso dalla data del punto ({_gm(nx)})")
    for ev in g.get("eventi") or ():
        ex = ev[0].date() if isinstance(ev[0], dt.datetime) else ev[0]
        visto("segni")
        if not isinstance(ex, dt.date) or not x0 <= ex <= x1:
            err.append(f"evento \"{_testo(ev[1])}\": il {_gm(ex) if isinstance(ex, dt.date) else ex} è fuori dal periodo "
                       f"del grafico ({_gm(x0)}-{_gm(x1)})")
    for sv, st in g.get("soglie") or ():
        t = _testo(st)
        m = re.fullmatch(GIORNO, t)
        visto("segni")
        if m:
            a = _giorno(m, 1, rif)
            qui = [ys[xs.index(a)] for _, xs, ys in serie if a in xs]
            if qui and not any(sulla(sv, y) for y in qui):
                err.append(f"soglia \"{t}\": vale {_it(sv)} ma la serie il {_gm(a)} è a {_it(qui[0])}")
            continue
        nn = re.findall(NUM, t)
        if len(nn) == 1 and not re.search(r"[a-zà-ù]{3}", t.lower()) and abs(_num(nn[0]) - abs(sv)) > _passo(nn[0], False) + 1e-9:
            err.append(f"soglia \"{t}\": l'etichetta dice {nn[0]} ma la linea è a {_it(sv)}")
    # ---- le cifre del titolo tornano con la serie (non per le serie trasformate: il titolo può dare i livelli)
    if not ALTRA_SCALA.search(misura):
        for m in DA_A.finditer(tit + ". " + sub):
            qa, a, qb, b = m.groups(); visto("cifre")
            ok = any(_vale(ys[i], a, qa) and any(_vale(y, b, qb) for y in ys[i + 1:])
                     for _, _, ys in serie for i in range(len(ys)))
            if not ok:
                err.append(f"il titolo dice \"{m.group(0)}\" ma nessuna serie passa da {a} e poi da {b} "
                           f"(va da {_it(serie[0][2][0])} a {_it(serie[0][2][-1])}, tra {_it(ymin)} e {_it(ymax)})")
        for m in PCT_DAL.finditer(tit):
            q, p = m.group(1), m.group(2)
            a = _giorno(m, 3, rif); visto("cifre")
            qui = [(ys[xs.index(a)], ys[xs.index(a) + 1:]) for _, xs, ys in serie if a in xs]
            if a and qui and not any(_vale(abs(y / base - 1) * 100, p, q) for base, dopo in qui if base for y in dopo):
                base, dopo = qui[0]
                err.append(f"il titolo dice \"{m.group(0)}\" ma dal {_gm(a)} ({_it(base)}) all'ultimo valore "
                           f"({_it(dopo[-1]) if dopo else '-'}) fa {_it(abs(dopo[-1] / base - 1) * 100) if dopo and base else '-'}%")
        for m in ARRIVA_A.finditer(tit):
            q, n, pct = m.groups()
            if (pct and "%" not in sub) or DISTANZA.match(tit[m.end(2):]):
                continue                            # una variazione o una distanza ("a 200 punti dal massimo"), non un livello
            visto("cifre")
            if not any(_vale(ys[-1], n, q) for _, _, ys in serie):
                err.append(f"il titolo dice \"{m.group(0)}\" ma l'ultimo valore è {_it(serie[0][2][-1])}")
    return err


def grafici(C):
    """[(chiave del modulo, file, spec)] dei grafici a linea dell'edizione."""
    out = []
    for m in C.get("moduli") or []:
        for campo in ("grafico", "grafico2"):
            g = m.get(campo)
            if isinstance(g, dict) and g.get("tipo") == "linee":
                out.append((str(m.get("chiave") or _testo(m.get("titolo"))[:20]), str(g.get("file", campo)), g))
    return out


def controlla(C, D=None):
    """(errori, grafici a linea, conta) per tutta l'edizione."""
    storie, ultime = _storie(D)
    oggi = C.get("data") if isinstance(C.get("data"), dt.date) else None
    err, conta, gg = [], {}, grafici(C)
    conta["avvisi"] = []
    for chiave, f, g in gg:
        aa = []
        try:
            ee = controlla_grafico(g, oggi, storie, ultime, conta, aa)
        except Exception as e:  # noqa: BLE001  una serie scritta in un modo non previsto è un errore da leggere, non una traceback
            ee = [f"serie non leggibile ({type(e).__name__}: {str(e)[:80]})"]
        err += [f"{chiave}, {f}: {e}" for e in ee]
        conta["avvisi"] += [f"{chiave}, {f}: {a}" for a in aa]
    return err, len(gg), conta


RIMEDIO = ("correggi la serie (una riga per seduta: data con l'anno e valore, un solo mercato, in ordine di data, fino "
           "all'ultima chiusura); se non torna togli il grafico: il modulo esce senza")


def main():
    a = sys.argv[1:]
    ed = os.path.abspath(a[0])
    dati = os.path.abspath(a[a.index("--dati") + 1]) if "--dati" in a else os.path.join(os.path.dirname(ed), "dati.json")
    os.chdir(os.path.dirname(ed))   # l'edizione legge i suoi file dalla cartella di lavoro
    import contextlib
    import io
    import controlli_testo as CT
    # l'edizione, caricandosi, stampa le sue note (desk, tabelle di pag. 5): non sono di questo controllo
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        C = CT.edizione(ed)
    D = json.load(open(dati, encoding="utf-8")) if os.path.exists(dati) else None
    err, n, conta = controlla(C, D)
    c = lambda k: conta.get(k, 0)
    print(f"Grafici a linea: {n} | chiusure confrontate: {c('punti')} punti di {c('serie')} serie | periodi {c('periodo')}, "
          f"note e soglie {c('segni')}, cifre del titolo {c('cifre')} | errori: {len(err)}")
    for i, e in enumerate(err):
        print("ERRORE: " + e[:300])
        if i == 0:
            print("- " + RIMEDIO)
    for a in conta.get("avvisi", []):
        print("AVVISO: " + a[:300])
    if D is None:
        print("AVVISO: chiusure non confrontate: manca dati.json")
    sys.exit(1 if err else 0)


if __name__ == "__main__":
    main()
