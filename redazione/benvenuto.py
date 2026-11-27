#!/usr/bin/env python3
"""La mail di benvenuto ai nuovi iscritti (G-43): la guida "Come si legge il Gommberg", una volta sola per iscritto.

Perché qui e non in Kit: il piano gratuito di Kit non ha automazioni né sequenze (verificato il 25/11/2026,
redazione/collaudi/2026-11-25/g43/ricerca.md). Allora la fa la macchina, a zero token: ogni sera, nel giro di
.github/workflows/dem.yml (passo "Benvenuto", dopo le mail straordinarie), questo script
  1. legge da Kit gli iscritti ATTIVI (cioè confermati) arrivati negli ultimi FINESTRA_GIORNI giorni e non prima di
     ACCESO_DAL (vedi sotto);
  2. toglie chi ha già l'etichetta (tag) "gommberg-benvenuto": è il segno "benvenuto già fatto", e per questo nessuno
     riceve la guida due volte, anche con due giri nello stesso giorno;
  3. dà ai rimasti l'etichetta del gruppo di stasera ("gommberg-benvenuto-AAAA-MM-GG-HHMM") e poi quella permanente;
  4. controlla che il gruppo in Kit abbia esattamente quegli iscritti;
  5. crea l'invio in BOZZA solo per il gruppo (subscriber_filter sull'etichetta del gruppo, modello "Gommberg cornice"),
     lo RILEGGE da Kit (GET, indipendente dalla risposta alla creazione) e solo se filtro e stato tornano lo programma
     tra ATTESA_MINUTI minuti; poi lo rilegge di nuovo. Se qualcosa non torna l'invio si toglie; se non si riesce a
     toglierlo si riporta in bozza (send_at null); se non riesce nemmeno quello, il messaggio dice URGENTE e dem.yml
     apre una segnalazione apposta.
Testo: redazione/benvenuto_mail.html (approvato da Paolo il 25/11/2026). Chiamate a Kit: newsletter.kit, una sola logica
(qui sopra c'è solo uno strato che trasforma ogni risposta illeggibile in "esito incerto").

L'accensione (ACCESO_DAL, un posto solo): ricevono il benvenuto solo gli iscritti arrivati da quel giorno in poi. I
lettori di prima (iscritti da settimane) e chi si è iscritto nei giorni prima del rilascio NON lo ricevono al primo
giro. La finestra di FINESTRA_GIORNI (7) giorni serve a chi conferma giorni dopo l'iscrizione (Kit dà la data di
iscrizione, non di conferma) e a chi perde qualche giro: i doppioni li impedisce l'etichetta permanente.

L'ordine, e perché (mai due mail allo stesso iscritto):
  - le etichette PRIMA dell'invio, e per ogni iscritto prima il gruppo e poi quella permanente. Un giro interrotto
    dopo il gruppo e prima della permanente: l'invio non esiste ancora, l'iscritto torna candidato al giro dopo, in un
    gruppo nuovo, e riceve la guida una volta. Un giro interrotto dopo le etichette e prima dell'invio: chi è stato
    segnato perde la guida (riceve comunque l'edizione e la pagina benvenuto.html gli ha già detto tutto), ma nessuno la
    riceve due volte. L'inverso (invio creato ed etichetta non data) non può succedere: l'invio nasce per ultimo.
  - la creazione dell'invio non si ritenta mai. Ogni esito incerto (nessuna risposta, risposta illeggibile o fuori
    forma) si chiarisce rileggendo da Kit: l'invio si cerca per id o per etichetta (description) e, se non è
    esattamente come voluto, si toglie. Mai un ripiego su un invio a tutti gli iscritti (che è ciò che Kit fa con un
    filtro vuoto).
  - nel dubbio non si invia: risposta fuori forma, filtro per data ignorato, troppi nuovi (oltre MAX_NUOVI), elenco
    non letto per intero, tempo del giro quasi finito: errore, nessun invio.
  - orari: si spedisce tra le 8:00 e le 20:59 (regole di dem.py) e mai nella fascia dell'edizione (da 75 minuti prima a
    45 minuti dopo giorni.ORA_USCITA: 8:30-10:30 con l'uscita alle 9:45). Fuori orario il giro lo scrive nel registro
    del giro e non spedisce: ci pensa il giro dopo (con la finestra di 7 giorni una sera saltata non fa perdere nessuno).
    Se un iscritto confermato riceve il benvenuto più di ATTESA_AVVISO (3) giorni dopo l'iscrizione, il giro spedisce
    e poi esce con 1 (Avviso): dem.yml apre la segnalazione, perché vuol dire giri saltati (o una conferma tardiva).
  - tempo: la programmazione parte solo se nel passo di dem.yml restano RISERVA secondi, il tempo di rileggere e, se
    serve, togliere l'invio: la pulizia di un invio sbagliato viene prima della scadenza del passo.

Uso:   python3 redazione/benvenuto.py controlla        il testo e la mail composta, senza rete (lo fa il collaudo)
       python3 redazione/benvenuto.py anteprima        scrive _benvenuto/benvenuto.html, la mail come la vedrà il lettore
       python3 redazione/benvenuto.py piano            legge Kit e dice a quanti iscritti partirebbe, senza scrivere nulla
       python3 redazione/benvenuto.py invia            il giro vero (lo fa dem.yml, solo da main)
       python3 redazione/benvenuto.py bozza INDIRIZZO  prova dal vivo, passo 2: SOLO una bozza per un gruppo con dentro
                                                       quel solo indirizzo (iscritto e confermato); la rilegge, stampa
                                                       filtro e stato e si ferma. Non spedisce nulla
       python3 redazione/benvenuto.py prova INDIRIZZO  prova dal vivo, passo 3: programma tra ATTESA_PROVA minuti l'ultima
                                                       bozza di prova di quell'indirizzo, solo se la rilettura conferma
                                                       il filtro sul gruppo con dentro lui solo

LA PROVA DAL VIVO, prima di accendere (dal PC, con KIT_API_KEY nell'ambiente; mai indirizzi nel registro):
  1. python3 redazione/benvenuto.py piano            sole letture: quanti iscritti riceverebbero il benvenuto stasera
  2. python3 redazione/benvenuto.py bozza CASA       poi in Kit, Broadcasts, la bozza gommberg-benvenuto-prova-...:
                                                     i destinatari stimati devono essere 1. Se non è 1: togli la bozza
                                                     a mano e fermati
  3. python3 redazione/benvenuto.py prova CASA       tra le 10:30 e le 20:45; la mail arriva solo a CASA dopo 2 minuti
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
PROVA = FATTO + "-prova-"          # gruppi e invii della prova dal vivo
ACCESO_DAL = "2026-11-28"          # accensione (ora di Roma, dalla mezzanotte): solo chi si iscrive da qui riceve il benvenuto
FINESTRA_GIORNI = 7                # iscritti arrivati negli ultimi 7 giorni (chi conferma tardi, giri persi)
ATTESA_AVVISO = 3                  # chi riceve il benvenuto oltre 3 giorni dopo l'iscrizione: avviso (giri saltati?)
MAX_NUOVI = 100                    # oltre, qualcosa non va (un filtro ignorato da Kit?): nessun invio
ATTESA_MINUTI = 10                 # l'invio parte dopo: il tempo di toglierlo se Kit lo registra male
ATTESA_PROVA = 2
FASCIA = (75, 45)                  # minuti prima e dopo l'uscita in cui non si spedisce
LETTURE = 3                        # tentativi per ogni lettura su un guasto momentaneo (429, 5xx, rete)
ATTESA_LETTURE = 10                # secondi tra un tentativo e l'altro (il collaudo la azzera)
SCADENZA = 80                      # secondi per il lavoro normale del giro (letture, etichette, bozza)
PASSO = 230                        # secondi del passo "Benvenuto" di dem.yml (timeout-minutes: 4), contati dall'avvio
TEMPO_CHIAMATA = 30                # tetto di una chiamata a Kit (il timeout di newsletter.kit)
RISERVA = 7 * TEMPO_CHIAMATA       # programmazione + 2 riletture + pulizia (2 DELETE, 1 PUT in bozza, 1 rilettura):
                                   # la PUT parte solo se nel passo restano questi secondi, così la pulizia di un
                                   # invio sbagliato finisce sempre prima della scadenza del passo
MARGINE = 35                       # sotto questi secondi rimasti non si scrive più nulla in Kit
MAX_PAGINE = 20
PER_PAGINA = 500
TRATTINI_LUNGHI = re.compile("[–—]")
orologio = time.monotonic          # il collaudo lo sostituisce
_scadenza = None
_avvio = None


class Fermo(Exception):
    """Il giro si ferma senza inviare nulla. Il messaggio dice perché e che cosa è già stato fatto."""


class Avviso(Exception):
    """Il giro ha fatto il suo lavoro, ma c'è qualcosa da guardare (esce con 1: segnalazione)."""


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
    global _scadenza, _avvio
    _avvio = orologio()
    _scadenza = _avvio + SCADENZA


def resta_nel_passo():
    return float("inf") if _avvio is None else PASSO - (orologio() - _avvio)


def rimasto():
    return float("inf") if _scadenza is None else _scadenza - orologio()


def kit_sicuro(metodo, percorso, dati=None):
    """newsletter.kit, con una sola aggiunta: una risposta che non si legge (200 con un corpo non JSON, connessione
    rotta a metà, qualsiasi eccezione) diventa (0, ...), cioè "esito incerto", come la rete muta. Mai un traceback."""
    try:
        stato, corpo = nl.kit(metodo, percorso, dati)
    except Exception as e:  # noqa: BLE001
        return 0, {"errore": f"risposta di Kit non leggibile ({type(e).__name__})"}
    return stato, corpo


def chiama(metodo, percorso, dati=None):
    if rimasto() <= 0:
        raise Fermo("tempo del giro scaduto prima di finire: nessun invio creato")
    return kit_sicuro(metodo, percorso, dati)


def leggi(percorso, pulizia=False):
    """Una lettura di Kit: su un guasto momentaneo (rete, risposta illeggibile, 429, 5xx) si riprova, LETTURE volte.
    Torna il corpo (dict). pulizia=True: lettura per controllare o togliere un invio, anche a tempo scaduto."""
    for tentativo in range(1, LETTURE + 1):
        stato, corpo = (kit_sicuro if pulizia else chiama)("GET", percorso)
        if stato == 200 and isinstance(corpo, dict):
            return corpo
        if stato == 200:
            raise Fermo(f"risposta di Kit fuori forma a GET {percorso.split('?')[0]}")
        if not (stato == 0 or stato == 429 or stato >= 500) or tentativo == LETTURE:
            raise Fermo(f"Kit non ha risposto a GET {percorso.split('?')[0]} (HTTP {stato}, {tentativo} tentativ"
                        f"{'o' if tentativo == 1 else 'i'})")
        time.sleep(max(0, min(ATTESA_LETTURE, rimasto())) if not pulizia else min(ATTESA_LETTURE, 2))


def leggi_tutto(percorso, chiave, pulizia=False):
    """Tutte le pagine di un elenco di Kit (cursore after). Ogni pagina deve avere la lista e la paginazione: un
    elenco parziale non vale mai per completo."""
    out, dopo = [], None
    for _ in range(MAX_PAGINE):
        corpo = leggi(percorso + (f"&after={dopo}" if dopo else ""), pulizia)
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


def acceso_dal():
    a = datetime.fromisoformat(ACCESO_DAL)
    return a if a.tzinfo else a.replace(tzinfo=ROMA)


def nuovi_iscritti(adesso):
    """Gli iscritti attivi (confermati) arrivati negli ultimi FINESTRA_GIORNI giorni e non prima di ACCESO_DAL, con le
    loro etichette. Kit filtra per data (created_after, giorno); qui si ricontrolla ogni data: se Kit ha ignorato il
    filtro ci si ferma."""
    inizio = max(adesso.astimezone(UTC) - timedelta(days=FINESTRA_GIORNI), acceso_dal().astimezone(UTC))
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


def iscritti_con(tag_id, dal=None, pulizia=False):
    """Gli id degli iscritti (di ogni stato) che hanno l'etichetta, letti dalla parte dell'etichetta."""
    filtro = f"&created_after={dal}" if dal else ""
    lista = leggi_tutto(f"/tags/{tag_id}/subscribers?status=all&per_page={PER_PAGINA}{filtro}", "subscribers", pulizia)
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


def broadcast_di(risposta):
    b = risposta.get("broadcast") if isinstance(risposta, dict) else None
    return b if isinstance(b, dict) else None


def rileggi(bid, tentativi=2):
    """L'invio come lo vede Kit ora (GET /broadcasts/{id}), o None se non si legge. Lettura di pulizia: anche a tempo
    scaduto, al massimo `tentativi` chiamate (il tempo della pulizia è contato in RISERVA)."""
    for _ in range(tentativi):
        stato, corpo = kit_sicuro("GET", f"/broadcasts/{bid}")
        if stato == 200:
            return broadcast_di(corpo)
        if not (stato == 0 or stato == 429 or stato >= 500):
            return None
    return None


def com_e(b, gruppo, invio):
    """True se l'invio b è esattamente quello voluto: filtro sul solo gruppo, e send_at assente (bozza, invio=None) o
    entro un minuto dall'ora voluta."""
    if not isinstance(b, dict) or not filtro_giusto(b.get("subscriber_filter"), gruppo):
        return False
    t = quando(b.get("send_at")) if b.get("send_at") else None
    if invio is None:
        return t is None and str(b.get("status") or "draft").lower() in ("draft", "")
    return t is not None and abs((t - invio).total_seconds()) < 60


def togli(bid, dati=None):
    """Toglie l'invio. Se Kit non lo toglie, ripiego: lo riporta in bozza (PUT con send_at null) e verifica rileggendo.
    Torna "tolto", "in bozza" o "" (né l'uno né l'altro: URGENTE). Lavora anche a tempo scaduto."""
    for _ in range(2):
        stato, _ = kit_sicuro("DELETE", f"/broadcasts/{bid}")
        if stato in (200, 204, 404):
            return "tolto"
        if not (stato == 0 or stato == 429 or stato >= 500):
            break
    if dati is not None:
        kit_sicuro("PUT", f"/broadcasts/{bid}", dict(dati, send_at=None))
        b = rileggi(bid, tentativi=1)
        if b is not None and not b.get("send_at"):
            return "in bozza"
    return ""


def esito_tolto(bid, dati, invio=None):
    """Toglie (o riporta in bozza) e dice come è andata, in parole per il registro e la segnalazione."""
    come = togli(bid, dati)
    if come == "tolto":
        return f"invio {bid} tolto"
    if come == "in bozza":
        return f"invio {bid} NON tolto ma riportato in bozza (non parte): toglilo a mano in Kit"
    ora = f" prima delle {invio.astimezone(ROMA):%H:%M}" if invio else ""
    return f"URGENTE: invio {bid} né tolto né riportato in bozza, può partire con destinatari sbagliati: FERMALO A MANO in Kit{ora}"


def invii_con(descrizione):
    """Gli id degli invii in Kit con quella description (per chiarire una creazione dall'esito incerto)."""
    return [b["id"] for b in leggi_tutto(f"/broadcasts?per_page={PER_PAGINA}", "broadcasts", pulizia=True)
            if str(b.get("description") or "") == descrizione and intero(b.get("id"))]


def dati_invio(gruppo_id, descrizione, modello):
    oggetto, anteprima, corpo = componi()
    return {"subject": oggetto, "preview_text": anteprima, "content": corpo, "description": descrizione, "public": False,
            "published_at": datetime.now(UTC).isoformat(timespec="seconds"), "send_at": None, "email_template_id": modello,
            "subscriber_filter": [{"all": [{"type": "tag", "ids": [gruppo_id]}], "any": None, "none": None}]}


def crea_bozza(gruppo_id, nome_gruppo, modello, attesi):
    """Crea la bozza per il gruppo (mai ritentata) e la rilegge. Torna (id, dati) solo se Kit, riletto, ha la bozza con
    il filtro sul solo gruppo; altrimenti la toglie e si ferma."""
    dati = dati_invio(gruppo_id, nome_gruppo, modello)
    senza = f"{len(attesi)} iscritti segnati senza mail" if attesi is not None else "nessun iscritto segnato"
    nel_gruppo = iscritti_con(gruppo_id)                         # ultimo controllo: nel gruppo i soli voluti
    if attesi is not None and nel_gruppo != set(attesi):
        raise Fermo(f"l'etichetta {nome_gruppo} in Kit ha {len(nel_gruppo)} iscritti invece di {len(attesi)}: nessun invio ({senza})")
    if rimasto() < MARGINE:
        raise Fermo(f"tempo del giro quasi finito: nessun invio creato ({senza})")
    stato, risposta = chiama("POST", "/broadcasts", dati)      # MAI ritentata
    b = broadcast_di(risposta)
    bid = intero((b or {}).get("id"))
    if stato not in (200, 201) or not bid:
        # esito incerto o rifiuto: se la bozza è nata lo stesso la si trova per etichetta e si toglie
        try:
            trovati = invii_con(nome_gruppo)
        except Fermo:
            raise Fermo(f"esito incerto alla creazione (HTTP {stato}) e elenco degli invii non leggibile: guarda in Kit "
                        f"(Broadcasts, {nome_gruppo}) e togli la bozza se c'è; nessun invio, {senza}")
        esiti = [esito_tolto(i, dati) for i in trovati]
        raise Fermo(f"Kit non ha confermato la creazione della bozza (HTTP {stato}): "
                    + ("; ".join(esiti) if esiti else "nessuna bozza trovata in Kit") + f"; nessun invio, {senza}")
    modello_kit = intero((b.get("email_template") or {}).get("id")) if isinstance(b.get("email_template"), dict) else None
    riletta = rileggi(bid)
    if not com_e(b, gruppo_id, None) or not com_e(riletta, gruppo_id, None) or (modello_kit and modello_kit != modello):
        raise Fermo("Kit ha registrato la bozza in modo diverso dall'atteso (filtro sugli iscritti, data o modello), "
                    f"o la rilettura non torna: {esito_tolto(bid, dati)}; nessun invio, {senza}")
    return bid, dati


def programma(bid, gruppo_id, dati, invio, senza):
    """Programma la bozza (già verificata) e la rilegge: qualunque risposta alla PUT (anche nessuna) si chiarisce con
    la rilettura. Se non è esattamente come voluta, si toglie (o si riporta in bozza)."""
    voluti = dict(dati, send_at=invio.astimezone(UTC).isoformat(timespec="seconds"))
    if resta_nel_passo() < RISERVA:      # non c'è più il tempo per rimediare a una programmazione sbagliata
        raise Fermo(f"tempo del passo insufficiente per programmare in sicurezza: {esito_tolto(bid, dati)}, nessun invio, {senza}")
    stato, risposta = kit_sicuro("PUT", f"/broadcasts/{bid}", voluti)      # anche a tempo scaduto: poi si rilegge
    riletta = rileggi(bid)
    risposta_b = broadcast_di(risposta)
    # la risposta conta solo se si legge: una risposta illeggibile (0, o 200 senza l'invio) la chiarisce la rilettura;
    # un rifiuto (4xx, 5xx) o una risposta leggibile diversa dal voluto bastano per togliere
    risposta_ok = stato == 0 or (stato == 200 and (risposta_b is None or com_e(risposta_b, gruppo_id, invio)))
    if com_e(riletta, gruppo_id, invio) and risposta_ok:
        return
    raise Fermo(f"Kit non ha programmato l'invio come voluto (HTTP {stato}, rilettura "
                f"{'non leggibile' if riletta is None else 'diversa'}): {esito_tolto(bid, voluti, invio)}, {senza}")


# ------------------------------------------------------------------ i giri
def salto(adesso):
    """Il giro salta per l'orario: lo scrive nel registro del giro e basta. Con la finestra di 7 giorni una sera saltata
    non fa perdere nessuno; chi aspetta da più di ATTESA_AVVISO giorni lo dice il giro dopo (Avviso)."""
    print(f"Benvenuto: giro saltato per l'orario alle {adesso:%H:%M} (si spedisce tra le {dem.ORA_DA}:00 e le "
          f"{dem.ORA_A - 1}:59, mai nella fascia dell'edizione): ci pensa il prossimo giro")
    return 0


def giro(esegui=True, adesso=None):
    """Il giro della sera. Torna 0 (fatto o niente da fare) o solleva Fermo."""
    adesso = (adesso or datetime.now(ROMA)).astimezone(ROMA)
    invio = adesso + timedelta(minutes=ATTESA_MINUTI)
    if esegui and not (orario_ammesso(adesso) and orario_ammesso(invio)):
        return salto(adesso)
    male = problemi_testo()
    if male:
        raise Fermo("testo della mail: " + "; ".join(male))
    modello = modello_cornice()
    fatto = etichetta(FATTO)
    candidati = nuovi_iscritti(adesso)
    gia = set()
    if fatto:
        gia = iscritti_con(fatto, dal=(adesso.astimezone(UTC) - timedelta(days=FINESTRA_GIORNI + 1)).date().isoformat())
    nuovi = [s for s in candidati if s["id"] not in gia and FATTO not in s["etichette"]]
    print(f"Benvenuto: {len(candidati)} iscritti confermati arrivati negli ultimi {FINESTRA_GIORNI} giorni (dal {ACCESO_DAL}), "
          f"{len(candidati) - len(nuovi)} già salutati, {len(nuovi)} da salutare")
    soglia = adesso.astimezone(UTC) - timedelta(days=ATTESA_AVVISO)
    in_attesa = [s for s in nuovi if s["creato"] < soglia]
    tardi = (f"{len(in_attesa)} iscritt{'o' if len(in_attesa) == 1 else 'i'} confermat{'o' if len(in_attesa) == 1 else 'i'} "
             f"aspettava{'' if len(in_attesa) == 1 else 'no'} il benvenuto da più di {ATTESA_AVVISO} giorni dall'iscrizione "
             "(giri saltati, o conferma arrivata tardi): guarda che dem.yml parta ogni sera") if in_attesa else ""
    if tardi:
        print(f"AVVISO: {tardi}")
    if not nuovi:
        return 0
    if len(nuovi) > MAX_NUOVI:
        raise Fermo(f"{len(nuovi)} iscritti nuovi in {FINESTRA_GIORNI} giorni (oltre {MAX_NUOVI}): troppi per essere veri, nessun invio")
    if not esegui:
        print(f"Piano: etichetta del gruppo e invio alle {invio:%H:%M} per {len(nuovi)} iscritt{'o' if len(nuovi) == 1 else 'i'}")
        return 0
    if rimasto() < MARGINE * 2:
        raise Fermo("tempo del giro quasi finito prima delle etichette: nessuna etichetta data, nessun invio")
    nome = f"{FATTO}-{adesso:%Y-%m-%d-%H%M}"
    fatto = fatto or etichetta(FATTO, crea=True)
    gruppo = nuovo_gruppo(nome)
    segnati = 0
    for s in nuovi:
        if not metti(gruppo, s["id"]):
            raise Fermo("etichetta del gruppo non data a un iscritto: nessun invio creato; "
                        f"{segnati} iscritti segnati senza mail, gli altri riprovano al prossimo giro")
        if not metti(fatto, s["id"]):   # anche "l'aveva già": salutato da un altro giro, e ora è nel gruppo. Fermo
            raise Fermo("etichetta permanente non data a un iscritto (o l'aveva già): nessun invio creato; "
                        f"{segnati} iscritti segnati senza mail, gli altri riprovano al prossimo giro")
        segnati += 1
    attesi = [s["id"] for s in nuovi]
    bid, dati = crea_bozza(gruppo, nome, modello, attesi)
    programma(bid, gruppo, dati, invio, f"{len(attesi)} iscritti segnati senza mail")
    print(f"OK: benvenuto programmato (invio {bid}) alle {invio.astimezone(ROMA):%H:%M} per {len(attesi)} "
          f"iscritt{'o' if len(attesi) == 1 else 'i'}, gruppo {nome}")
    if tardi:
        raise Avviso(tardi)
    return 0


def nuovo_gruppo(nome):
    if rimasto() < MARGINE * 2:
        raise Fermo("tempo del giro quasi finito prima delle etichette: nessuna etichetta data, nessun invio")
    stato, corpo = chiama("POST", "/tags", {"name": nome})
    t = (corpo or {}).get("tag") if isinstance(corpo, dict) else None
    if stato != 201 or not isinstance(t, dict) or not intero(t.get("id")):
        raise Fermo(f"etichetta del gruppo {nome} non creata come nuova (HTTP {stato}; 200 = esisteva già): nessun invio")
    return t["id"]


def iscritto_di_prova(indirizzo):
    from urllib.parse import quote
    trovati = leggi_tutto(f"/subscribers?status=active&email_address={quote(indirizzo.strip())}&per_page=10", "subscribers")
    if len(trovati) != 1 or not intero(trovati[0].get("id")) or str(trovati[0].get("email_address", "")).lower() != indirizzo.strip().lower():
        raise Fermo(f"l'indirizzo di prova non è un iscritto attivo (trovati {len(trovati)}): iscriviti e conferma prima")
    return trovati[0]["id"]


def bozza(indirizzo, adesso=None):
    """Prova dal vivo, passo 2: la sola bozza per un gruppo con dentro solo l'indirizzo di casa, riletta. Non spedisce."""
    adesso = (adesso or datetime.now(ROMA)).astimezone(ROMA)
    male = problemi_testo()
    if male:
        raise Fermo("testo della mail: " + "; ".join(male))
    modello = modello_cornice()
    chi = iscritto_di_prova(indirizzo)
    nome = f"{PROVA}{adesso:%Y-%m-%d-%H%M}"
    gruppo = nuovo_gruppo(nome)
    if not metti(gruppo, chi):
        raise Fermo("etichetta di prova non data all'indirizzo: nessuna bozza")
    bid, _ = crea_bozza(gruppo, nome, modello, [chi])
    b = rileggi(bid) or {}
    print(f"Bozza di prova {bid} ({nome}): filtro {json.dumps(b.get('subscriber_filter'))}, stato {b.get('status')}, "
          f"send_at {b.get('send_at')}. Guarda in Kit (Broadcasts): i destinatari stimati devono essere 1. Poi: prova INDIRIZZO")
    return bid


def prova(indirizzo, adesso=None):
    """Prova dal vivo, passo 3: programma l'ultima bozza di prova, solo se riletta è ancora per il gruppo dell'indirizzo
    e il gruppo ha dentro lui solo."""
    adesso = (adesso or datetime.now(ROMA)).astimezone(ROMA)
    invio = adesso + timedelta(minutes=ATTESA_PROVA)
    if not (orario_ammesso(adesso) and orario_ammesso(invio)):
        raise Fermo(f"fuori orario ({adesso:%H:%M}): si prova tra le {dem.ORA_DA}:00 e le {dem.ORA_A - 1}:59, fuori dalla fascia dell'edizione")
    modello = modello_cornice()
    chi = iscritto_di_prova(indirizzo)
    bozze = [b for b in leggi_tutto(f"/broadcasts?per_page={PER_PAGINA}", "broadcasts")
             if str(b.get("description") or "").startswith(PROVA) and intero(b.get("id")) and not b.get("send_at")]
    if not bozze:
        raise Fermo("nessuna bozza di prova in Kit: lancia prima 'bozza INDIRIZZO'")
    b = rileggi(max(x["id"] for x in bozze))
    try:
        gruppo = intero(b["subscriber_filter"][0]["all"][0]["ids"][0])
    except (TypeError, KeyError, IndexError):
        gruppo = None
    if not b or not gruppo or not com_e(b, gruppo, None):
        raise Fermo("l'ultima bozza di prova, riletta, non è una bozza con il filtro su un solo gruppo: non si programma")
    if iscritti_con(gruppo) != {chi}:
        raise Fermo("il gruppo della bozza di prova non contiene solo l'indirizzo dato: non si programma")
    dati = dati_invio(gruppo, str(b.get("description")), modello)
    programma(b["id"], gruppo, dati, invio, "nessun iscritto segnato")
    print(f"OK: prova programmata (invio {b['id']}) alle {invio:%H:%M}, al solo indirizzo dato")
    return b["id"]


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
    if modo not in ("piano", "invia", "bozza", "prova") or (modo in ("bozza", "prova") and len(sys.argv) < 3):
        sys.exit(__doc__)
    avvia_scadenza()
    try:
        if modo == "bozza":
            bozza(sys.argv[2])
        elif modo == "prova":
            prova(sys.argv[2])
        else:
            giro(esegui=modo == "invia")
    except (Fermo, Avviso) as e:
        print(f"DA GUARDARE: benvenuto - {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
