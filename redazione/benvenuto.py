#!/usr/bin/env python3
"""La mail di benvenuto ai nuovi iscritti (G-43): la guida "Come si legge il Gommberg", una volta sola per iscritto.

Perché qui e non in Kit: il piano gratuito di Kit non ha automazioni né sequenze (verificato il 25/11/2026,
redazione/collaudi/2026-11-25/g43/ricerca.md). Allora la fa la macchina, a zero token: ogni sera, nel giro di
.github/workflows/dem.yml (passo "Benvenuto", dopo le mail straordinarie), questo script
  1. legge da Kit gli iscritti ATTIVI (cioè confermati) arrivati nelle ultime 48 ore;
  2. toglie chi ha già l'etichetta (tag) "gommberg-benvenuto": è il segno "benvenuto già fatto", e per questo nessuno
     riceve la guida due volte, anche con due giri nello stesso giorno;
  3. dà ai rimasti l'etichetta del gruppo di stasera ("gommberg-benvenuto-AAAA-MM-GG-HHMM") e poi quella permanente;
  4. controlla che il gruppo in Kit abbia esattamente quegli iscritti;
  5. crea l'invio in BOZZA solo per il gruppo (subscriber_filter sull'etichetta del gruppo, modello "Gommberg cornice"),
     controlla che Kit abbia registrato quel filtro, poi lo programma tra ATTESA_MINUTI minuti e ricontrolla.
Testo: redazione/benvenuto_mail.html (approvato da Paolo il 25/11/2026). Chiamate a Kit: newsletter.kit, una sola logica.

L'ordine, e perché (mai due mail allo stesso iscritto):
  - le etichette PRIMA dell'invio, e per ogni iscritto prima il gruppo e poi quella permanente. Un giro interrotto
    dopo il gruppo e prima della permanente: l'invio non esiste ancora, l'iscritto torna candidato al giro dopo, in un
    gruppo nuovo, e riceve la guida una volta. Un giro interrotto dopo le etichette e prima dell'invio: chi è stato
    segnato perde la guida (riceve comunque l'edizione e la pagina benvenuto.html gli ha già detto tutto), ma nessuno la
    riceve due volte. L'inverso (invio creato ed etichetta non data) non può succedere: l'invio nasce per ultimo.
  - la creazione dell'invio non si ritenta mai; un invio nasce in bozza (una bozza non parte) e si programma solo
    dopo aver visto che Kit ha registrato il filtro sul gruppo. Se Kit risponde in modo diverso dall'atteso, la bozza
    si toglie e lo script esce con errore: mai un ripiego su un invio a tutti gli iscritti (che è ciò che Kit fa con un
    filtro vuoto).
  - nel dubbio non si invia: risposta fuori forma, filtro per data ignorato, troppi nuovi (oltre MAX_NUOVI), elenco
    non letto per intero, tempo del giro quasi finito: errore, nessun invio.
  - orari: si spedisce tra le 8:00 e le 20:59 (regole di dem.py) e mai nella fascia dell'edizione (da 75 minuti prima a
    45 minuti dopo giorni.ORA_USCITA: 8:30-10:30 con l'uscita alle 9:45). Fuori orario il giro non fa nulla: con la
    finestra di 48 ore ci pensa il giro della sera dopo.

Uso:   python3 redazione/benvenuto.py controlla        il testo e la mail composta, senza rete (lo fa il collaudo)
       python3 redazione/benvenuto.py anteprima        scrive _benvenuto/benvenuto.html, la mail come la vedrà il lettore
       python3 redazione/benvenuto.py piano            legge Kit e dice a quanti iscritti partirebbe, senza scrivere nulla
       python3 redazione/benvenuto.py invia            il giro vero (lo fa dem.yml, solo da main)
       python3 redazione/benvenuto.py prova INDIRIZZO  la prova dal vivo su UN indirizzo di casa già iscritto e confermato:
                                                       stessa strada (gruppo, bozza, filtro, programmazione), senza
                                                       l'etichetta permanente; mai indirizzi nel registro
Esce con 1 quando qualcosa va guardato: dem.yml apre allora la segnalazione a Paolo. La chiave è KIT_API_KEY, mai stampata.
"""
import html
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

QUI = Path(__file__).resolve().parent
sys.path.insert(0, str(QUI))
import dem  # noqa: E402  regole degli orari delle mail fuori dall'edizione (ORA_DA, ORA_A)
import giorni  # noqa: E402  ora di uscita (ORA_USCITA): un posto solo
import newsletter as nl  # noqa: E402  chiamate a Kit, cornice, anteprima locale: una sola definizione

REPO = QUI.parent
TESTO = QUI / "benvenuto_mail.html"
ANTEPRIME = REPO / "_benvenuto"
ROMA = ZoneInfo("Europe/Rome")
UTC = timezone.utc

FATTO = "gommberg-benvenuto"       # etichetta permanente: benvenuto già fatto (o iscritto segnato senza mail)
FINESTRA_ORE = 48                  # iscritti arrivati nelle ultime 48 ore: due giri serali per ciascuno
MAX_NUOVI = 100                    # oltre, qualcosa non va (un filtro ignorato da Kit?): nessun invio
ATTESA_MINUTI = 10                 # l'invio parte dopo: il tempo di toglierlo se Kit lo registra male
ATTESA_PROVA = 2
FASCIA = (75, 45)                  # minuti prima e dopo l'uscita in cui non si spedisce
LETTURE = 3                        # tentativi per ogni lettura su un guasto momentaneo (429, 5xx, rete)
ATTESA_LETTURE = 10                # secondi tra un tentativo e l'altro (il collaudo la azzera)
SCADENZA = 150                     # secondi per tutto il giro (il job di dem.yml ha 5 minuti in tutto)
MARGINE = 35                       # sotto questi secondi rimasti non si scrive più nulla in Kit
MAX_PAGINE = 20
PER_PAGINA = 500
TRATTINI_LUNGHI = re.compile("[–—]")
orologio = time.monotonic          # il collaudo lo sostituisce
_scadenza = None


class Fermo(Exception):
    """Il giro si ferma senza inviare nulla. Il messaggio dice perché e che cosa è già stato fatto."""


# ------------------------------------------------------------------ orari
def fascia_edizione(giorno):
    h, m = giorni.ora_uscita()
    uscita = datetime(giorno.year, giorno.month, giorno.day, h, m, tzinfo=ROMA)
    return uscita - timedelta(minutes=FASCIA[0]), uscita + timedelta(minutes=FASCIA[1])


def orario_ammesso(t):
    """True se a t (ora di Roma) una mail del Gommberg fuori dall'edizione può partire."""
    t = t.astimezone(ROMA)
    if not dem.ORA_DA <= t.hour < dem.ORA_A:
        return False
    da, a = fascia_edizione(t.date())
    return not da <= t < a


# ------------------------------------------------------------------ la mail
def componi():
    """Oggetto, anteprima e contenuto HTML (solo il contenuto: la cornice è il modello di Kit)."""
    testo = TESTO.read_text(encoding="utf-8")
    testa = re.match(r"\s*<!--(.*?)-->\s*", testo, re.S)
    if not testa:
        raise Fermo(f"{TESTO.name}: manca l'intestazione con oggetto e anteprima")
    campi = dict(re.findall(r"^(oggetto|anteprima):\s*(.+?)\s*$", testa.group(1), re.M))
    corpo = testo[testa.end():].replace("[[ORA_USCITA]]", giorni.ORA_USCITA).strip()
    return campi.get("oggetto", ""), campi.get("anteprima", ""), corpo


def problemi_testo():
    """Le regole del testo: le stesse delle mail straordinarie dove valgono. Lista vuota = va bene."""
    try:
        oggetto, anteprima, corpo = componi()
    except (OSError, Fermo) as e:
        return [str(e)]
    male = []
    if not 8 <= len(oggetto) <= 78:
        male.append(f"oggetto di {len(oggetto)} caratteri (da 8 a 78)")
    if not 20 <= len(anteprima) <= 140:
        male.append(f"anteprima di {len(anteprima)} caratteri (da 20 a 140)")
    if TRATTINI_LUNGHI.search(oggetto + anteprima + corpo):
        male.append("trattini lunghi: si usa solo il trattino corto -")
    if "[[" in corpo or "{{" in corpo or "{%" in corpo:
        male.append("segnaposto rimasti nel testo ([[...]] o codice di Kit)")
    if not corpo.startswith("<table") or not corpo.endswith("</table>"):
        male.append("il contenuto deve essere una tabella sola, come nelle altre email")
    for url in re.findall(r'href="([^"]+)"', corpo):
        if not url.startswith("https://gommberg.com/"):
            male.append(f"link fuori dal sito o non https: {url[:60]}")
    if "La redazione del Gommberg" not in corpo:
        male.append("manca la firma 'La redazione del Gommberg'")
    if f"alle {giorni.ORA_USCITA}" not in corpo:
        male.append("l'ora di uscita non è quella di giorni.ORA_USCITA")
    parole = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", html.unescape(corpo))))
    if parole > dem.PAROLE_MAX:
        male.append(f"{parole} parole: al massimo {dem.PAROLE_MAX}")
    return male


# ------------------------------------------------------------------ Kit
def avvia_scadenza():
    global _scadenza
    _scadenza = orologio() + SCADENZA


def rimasto():
    return float("inf") if _scadenza is None else _scadenza - orologio()


def chiama(metodo, percorso, dati=None):
    if rimasto() <= 0:
        raise Fermo("tempo del giro scaduto prima di finire: nessun invio creato")
    return nl.kit(metodo, percorso, dati)


def leggi(percorso):
    """Una lettura di Kit: su un guasto momentaneo (rete, 429, 5xx) si riprova, LETTURE volte. Torna il corpo (dict)."""
    for tentativo in range(1, LETTURE + 1):
        stato, corpo = chiama("GET", percorso)
        if stato == 200 and isinstance(corpo, dict):
            return corpo
        if stato == 200:
            raise Fermo(f"risposta di Kit fuori forma a GET {percorso.split('?')[0]}")
        if not (stato == 0 or stato == 429 or stato >= 500) or tentativo == LETTURE:
            raise Fermo(f"Kit non ha risposto a GET {percorso.split('?')[0]} (HTTP {stato}, {tentativo} tentativ"
                        f"{'o' if tentativo == 1 else 'i'})")
        time.sleep(max(0, min(ATTESA_LETTURE, rimasto())))


def leggi_tutto(percorso, chiave):
    """Tutte le pagine di un elenco di Kit (cursore after). Ogni pagina deve avere la lista e la paginazione: un
    elenco parziale non vale mai per completo."""
    out, dopo = [], None
    for _ in range(MAX_PAGINE):
        corpo = leggi(percorso + (f"&after={dopo}" if dopo else ""))
        lista, pg = corpo.get(chiave), corpo.get("pagination")
        if not isinstance(lista, list) or not isinstance(pg, dict) or not isinstance(pg.get("has_next_page"), bool):
            raise Fermo(f"risposta di Kit fuori forma a GET {percorso.split('?')[0]} (manca '{chiave}' o la paginazione)")
        if any(not isinstance(x, dict) for x in lista):
            raise Fermo(f"risposta di Kit fuori forma a GET {percorso.split('?')[0]} (voci non leggibili)")
        out += lista
        if not pg["has_next_page"]:
            return out
        dopo = pg.get("end_cursor")
        if not dopo:
            raise Fermo(f"risposta di Kit fuori forma a GET {percorso.split('?')[0]} (pagina dopo senza cursore)")
    raise Fermo(f"elenco di Kit troppo lungo (oltre {MAX_PAGINE} pagine): fermo per prudenza")


def quando(s):
    try:
        t = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=UTC)


def intero(x):
    return x if isinstance(x, int) and not isinstance(x, bool) else None


def modello_cornice():
    corpo = leggi("/email_templates")
    lista = corpo.get("email_templates")
    if not isinstance(lista, list):
        raise Fermo("risposta di Kit fuori forma a GET /email_templates")
    for t in lista:
        if isinstance(t, dict) and str(t.get("name") or "").strip().lower() == nl.CORNICE.lower() and intero(t.get("id")):
            return t["id"]
    raise Fermo(f'in Kit manca il modello "{nl.CORNICE}": nessun invio (su nessun altro modello)')


def etichetta(nome, crea=False):
    """L'id dell'etichetta con quel nome (Kit li confronta senza maiuscole), o None. Con crea=True la crea se manca."""
    for t in leggi_tutto(f"/tags?per_page={PER_PAGINA}", "tags"):
        if str(t.get("name") or "").strip().lower() == nome.lower():
            if not intero(t.get("id")):
                raise Fermo("risposta di Kit fuori forma a GET /tags (etichetta senza id)")
            return t["id"]
    if not crea:
        return None
    stato, corpo = chiama("POST", "/tags", {"name": nome})
    t = (corpo or {}).get("tag") if isinstance(corpo, dict) else None
    if stato not in (200, 201) or not isinstance(t, dict) or not intero(t.get("id")) or str(t.get("name", "")).lower() != nome.lower():
        raise Fermo(f"Kit non ha creato l'etichetta {nome} (HTTP {stato}): nessun invio")
    return t["id"]


def nuovi_iscritti(adesso):
    """Gli iscritti attivi (confermati) arrivati nelle ultime FINESTRA_ORE ore, con le loro etichette. Kit filtra per
    data (created_after, giorno); qui si ricontrolla ogni data: se Kit ha ignorato il filtro ci si ferma."""
    inizio = adesso.astimezone(UTC) - timedelta(hours=FINESTRA_ORE)
    giorno = inizio.date().isoformat()
    lista = leggi_tutto(f"/subscribers?status=active&created_after={giorno}&include=tags&per_page={PER_PAGINA}", "subscribers")
    out = []
    for s in lista:
        t, i = quando(s.get("created_at")), intero(s.get("id"))
        if not i or not t or s.get("state") != "active" or not isinstance(s.get("tags"), list):
            raise Fermo("risposta di Kit fuori forma a GET /subscribers (iscritto senza id, data, stato attivo o etichette)")
        if t < inizio - timedelta(days=1):       # più vecchio del giorno chiesto (con un giorno di tolleranza sul fuso)
            raise Fermo("Kit ha restituito iscritti più vecchi del filtro per data: nessun invio")
        if t >= inizio:
            out.append({"id": i, "creato": t, "etichette": {str((x or {}).get("name", "")).lower() for x in s["tags"] if isinstance(x, dict)}})
    return out


def iscritti_con(tag_id, dal=None):
    """Gli id degli iscritti (di ogni stato) che hanno l'etichetta, letti dalla parte dell'etichetta."""
    filtro = f"&created_after={dal}" if dal else ""
    lista = leggi_tutto(f"/tags/{tag_id}/subscribers?status=all&per_page={PER_PAGINA}{filtro}", "subscribers")
    ids = {intero(s.get("id")) for s in lista}
    if None in ids:
        raise Fermo(f"risposta di Kit fuori forma a GET /tags/{tag_id}/subscribers (iscritto senza id)")
    return ids


def metti(tag_id, iscritto):
    """Etichetta a un iscritto: True se data ora. Kit risponde 201 se la dà, 200 se l'iscritto l'aveva già. Si ritenta
    solo un guasto momentaneo (dare un'etichetta due volte non fa danni); dopo un tentativo senza risposta anche 200
    va bene (l'aveva data il tentativo di prima). Un 200 al primo colpo vuol dire che l'etichetta c'era già: False."""
    for tentativo in range(1, LETTURE + 1):
        stato, _ = chiama("POST", f"/tags/{tag_id}/subscribers/{iscritto}", {})
        if stato == 201 or (stato == 200 and tentativo > 1):
            return True
        if not (stato == 0 or stato == 429 or stato >= 500) or tentativo == LETTURE:
            return False
        time.sleep(max(0, min(ATTESA_LETTURE, rimasto())))


def filtro_giusto(filtro, gruppo):
    """Il filtro registrato da Kit è esattamente "tutti quelli con l'etichetta del gruppo"? Ogni altra forma (vuoto,
    all_subscribers, un segmento, un'altra etichetta, più gruppi) è no."""
    if not isinstance(filtro, list) or len(filtro) != 1 or not isinstance(filtro[0], dict):
        return False
    f = filtro[0]
    if set(f) - {"all", "any", "none"} or any(f.get(k) for k in ("any", "none")):
        return False
    voci = f.get("all")
    if not isinstance(voci, list) or len(voci) != 1 or not isinstance(voci[0], dict):
        return False
    v = voci[0]
    return v.get("type") == "tag" and isinstance(v.get("ids"), list) and [intero(x) for x in v["ids"]] == [gruppo]


def togli(bid):
    for _ in range(LETTURE):
        stato, _ = nl.kit("DELETE", f"/broadcasts/{bid}")        # anche a tempo scaduto: togliere è sempre giusto
        if stato in (200, 204, 404):
            return True
        if not (stato == 0 or stato == 429 or stato >= 500):
            return False
    return False


def spedisci(gruppo_id, nome_gruppo, modello, invio, attesi):
    """Bozza per il gruppo, controllo del filtro, programmazione, controllo. Mai una seconda creazione."""
    oggetto, anteprima, corpo = componi()
    dati = {"subject": oggetto, "preview_text": anteprima, "content": corpo, "description": nome_gruppo, "public": False,
            "published_at": datetime.now(UTC).isoformat(timespec="seconds"), "send_at": None,
            "email_template_id": modello, "subscriber_filter": [{"all": [{"type": "tag", "ids": [gruppo_id]}]}]}
    # ultimo controllo prima di creare: nel gruppo ci sono esattamente gli iscritti voluti
    nel_gruppo = iscritti_con(gruppo_id)
    if nel_gruppo != set(attesi):
        raise Fermo(f"l'etichetta {nome_gruppo} in Kit ha {len(nel_gruppo)} iscritti invece di {len(attesi)}: nessun invio "
                    f"({len(attesi)} iscritti segnati senza mail)")
    if rimasto() < MARGINE:
        raise Fermo(f"tempo del giro quasi finito: nessun invio creato ({len(attesi)} iscritti segnati senza mail)")
    stato, risposta = chiama("POST", "/broadcasts", dati)      # MAI ritentata
    b = (risposta or {}).get("broadcast") if isinstance(risposta, dict) else None
    if stato == 0:
        raise Fermo("esito incerto: Kit non ha risposto alla creazione della bozza. Una bozza non parte da sola: guarda in "
                    f"Kit (Broadcasts, {nome_gruppo}) e toglila; {len(attesi)} iscritti segnati senza mail")
    if stato not in (200, 201) or not isinstance(b, dict) or not intero(b.get("id")):
        raise Fermo(f"Kit non ha accettato la bozza (HTTP {stato}): nessun invio, {len(attesi)} iscritti segnati senza mail")
    bid = b["id"]
    modello_kit = intero((b.get("email_template") or {}).get("id")) if isinstance(b.get("email_template"), dict) else None
    if not filtro_giusto(b.get("subscriber_filter"), gruppo_id) or b.get("send_at") or (modello_kit and modello_kit != modello):
        tolta = togli(bid)
        raise Fermo("Kit ha registrato la bozza in modo diverso dall'atteso (filtro sugli iscritti, data o modello): "
                    + ("bozza tolta" if tolta else f"bozza {bid} NON tolta, da togliere a mano in Kit") + ", nessun invio")
    # programmazione: lo stesso invio, con la data. Se non torna giusto, si toglie
    dati["send_at"] = invio.astimezone(UTC).isoformat(timespec="seconds")
    stato, risposta = chiama("PUT", f"/broadcasts/{bid}", dati)
    b = (risposta or {}).get("broadcast") if isinstance(risposta, dict) else None
    if stato == 0:
        raise Fermo(f"esito incerto: Kit non ha risposto alla programmazione della bozza {bid}: guarda in Kit prima delle "
                    f"{invio.astimezone(ROMA):%H:%M} (se è programmata con il filtro sul gruppo va bene, se no toglila)")
    t = quando((b or {}).get("send_at")) if isinstance(b, dict) else None
    giusto = (stato == 200 and isinstance(b, dict) and filtro_giusto(b.get("subscriber_filter"), gruppo_id)
              and t is not None and abs((t - invio).total_seconds()) < 60)
    if not giusto:
        tolta = togli(bid)
        raise Fermo(f"Kit non ha programmato l'invio come voluto (HTTP {stato}): "
                    + ("invio tolto" if tolta else f"invio {bid} NON tolto: FERMALO A MANO in Kit prima delle {invio.astimezone(ROMA):%H:%M}")
                    + f", {len(attesi)} iscritti segnati senza mail")
    return bid


# ------------------------------------------------------------------ i giri
def giro(esegui=True, adesso=None):
    """Il giro della sera. Torna 0 (fatto o niente da fare) o solleva Fermo."""
    adesso = (adesso or datetime.now(ROMA)).astimezone(ROMA)
    invio = adesso + timedelta(minutes=ATTESA_MINUTI)
    if esegui and not (orario_ammesso(adesso) and orario_ammesso(invio)):
        print(f"Benvenuto: niente da fare alle {adesso:%H:%M} (si spedisce tra le {dem.ORA_DA}:00 e le {dem.ORA_A - 1}:59, "
              "mai nella fascia dell'edizione): ci pensa il prossimo giro")
        return 0
    male = problemi_testo()
    if male:
        raise Fermo("testo della mail: " + "; ".join(male))
    modello = modello_cornice()
    fatto = etichetta(FATTO)
    candidati = nuovi_iscritti(adesso)
    gia = set()
    if fatto:
        gia = iscritti_con(fatto, dal=(adesso.astimezone(UTC) - timedelta(hours=FINESTRA_ORE + 24)).date().isoformat())
    nuovi = [s for s in candidati if s["id"] not in gia and FATTO not in s["etichette"]]
    print(f"Benvenuto: {len(candidati)} iscritti confermati nelle ultime {FINESTRA_ORE} ore, {len(candidati) - len(nuovi)} "
          f"già salutati, {len(nuovi)} da salutare")
    if not nuovi:
        return 0
    if len(nuovi) > MAX_NUOVI:
        raise Fermo(f"{len(nuovi)} iscritti nuovi in {FINESTRA_ORE} ore (oltre {MAX_NUOVI}): troppi per essere veri, nessun invio")
    if not esegui:
        print(f"Piano: etichetta del gruppo e invio alle {invio:%H:%M} per {len(nuovi)} iscritt{'o' if len(nuovi) == 1 else 'i'}")
        return 0
    if rimasto() < MARGINE * 2:
        raise Fermo("tempo del giro quasi finito prima delle etichette: nessuna etichetta data, nessun invio")
    nome = f"{FATTO}-{adesso:%Y-%m-%d-%H%M}"
    return saluta(nuovi, nome, fatto or etichetta(FATTO, crea=True), modello, invio)


def saluta(nuovi, nome, fatto, modello, invio):
    """Etichette (prima il gruppo, poi la permanente, iscritto per iscritto), poi l'invio."""
    if rimasto() < MARGINE * 2:
        raise Fermo("tempo del giro quasi finito prima delle etichette: nessuna etichetta data, nessun invio")
    stato, corpo = chiama("POST", "/tags", {"name": nome})
    t = (corpo or {}).get("tag") if isinstance(corpo, dict) else None
    if stato != 201 or not isinstance(t, dict) or not intero(t.get("id")):
        raise Fermo(f"etichetta del gruppo {nome} non creata come nuova (HTTP {stato}; 200 = esisteva già): nessun invio")
    gruppo = t["id"]
    segnati = 0
    for s in nuovi:
        if not metti(gruppo, s["id"]):
            raise Fermo("etichetta del gruppo non data a un iscritto: nessun invio creato; "
                        f"{segnati} iscritti segnati senza mail, gli altri riprovano al prossimo giro")
        if fatto:
            if not metti(fatto, s["id"]):   # anche "l'aveva già": salutato da un altro giro, e ora è nel gruppo. Fermo
                raise Fermo("etichetta permanente non data a un iscritto (o l'aveva già): nessun invio creato; "
                            f"{segnati} iscritti segnati senza mail, gli altri riprovano al prossimo giro")
        segnati += 1
    bid = spedisci(gruppo, nome, modello, invio, [s["id"] for s in nuovi])
    print(f"OK: benvenuto programmato (invio {bid}) alle {invio.astimezone(ROMA):%H:%M} per {len(nuovi)} "
          f"iscritt{'o' if len(nuovi) == 1 else 'i'}, gruppo {nome}")
    return 0


def prova(indirizzo, adesso=None):
    """La prova dal vivo su un indirizzo di casa: un gruppo di prova con dentro solo lui, stessa strada dell'invio vero,
    senza l'etichetta permanente. Mai indirizzi nel registro: si stampano solo i conteggi."""
    adesso = (adesso or datetime.now(ROMA)).astimezone(ROMA)
    invio = adesso + timedelta(minutes=ATTESA_PROVA)
    if not (orario_ammesso(adesso) and orario_ammesso(invio)):
        raise Fermo(f"fuori orario ({adesso:%H:%M}): si prova tra le {dem.ORA_DA}:00 e le {dem.ORA_A - 1}:59, fuori dalla fascia dell'edizione")
    male = problemi_testo()
    if male:
        raise Fermo("testo della mail: " + "; ".join(male))
    from urllib.parse import quote
    modello = modello_cornice()
    trovati = leggi_tutto(f"/subscribers?status=active&email_address={quote(indirizzo.strip())}&per_page=10", "subscribers")
    if len(trovati) != 1 or not intero(trovati[0].get("id")) or str(trovati[0].get("email_address", "")).lower() != indirizzo.strip().lower():
        raise Fermo(f"l'indirizzo di prova non è un iscritto attivo (trovati {len(trovati)}): iscriviti e conferma prima")
    nome = f"{FATTO}-prova-{adesso:%Y-%m-%d-%H%M}"
    bid = saluta([{"id": trovati[0]["id"]}], nome, None, modello, invio)
    return bid


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else "controlla"
    if modo == "controlla":
        male = problemi_testo()
        oggetto, anteprima, _ = componi() if not male else ("", "", "")
        print(f"Benvenuto: {'OK' if not male else 'ERRORI'} - oggetto: {oggetto} | anteprima: {anteprima}")
        for x in male:
            print(f"  ERRORE  {x}")
        sys.exit(1 if male else 0)
    if modo == "anteprima":
        oggetto, anteprima, corpo = componi()
        ANTEPRIME.mkdir(exist_ok=True)
        (ANTEPRIME / "benvenuto.html").write_text(nl.anteprima_locale(corpo), encoding="utf-8")
        print(f"Anteprima: _benvenuto/benvenuto.html - {oggetto} | {anteprima}")
        return
    if modo not in ("piano", "invia", "prova") or (modo == "prova" and len(sys.argv) < 3):
        sys.exit(__doc__)
    avvia_scadenza()
    try:
        if modo == "prova":
            prova(sys.argv[2])
        else:
            giro(esegui=modo == "invia")
    except Fermo as e:
        print(f"DA GUARDARE: benvenuto - {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
