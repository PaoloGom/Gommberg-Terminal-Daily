#!/usr/bin/env python3
"""La mail di benvenuto ai nuovi iscritti (G-43): la guida "Come si legge il Gommberg", una volta sola per iscritto.

Perché qui e non in Kit: il piano gratuito di Kit non ha automazioni né sequenze (verificato il 25/11/2026,
redazione/collaudi/2026-11-25/g43/ricerca.md). Allora la fa la macchina, a zero token: ogni sera, nel giro di
.github/workflows/dem.yml (passo "Benvenuto", dopo le mail straordinarie), questo script
  1. legge da Kit gli iscritti ATTIVI (cioè confermati) arrivati negli ultimi FINESTRA_GIORNI giorni e non prima di
     ACCESO_DAL (vedi sotto);
  2. toglie chi ha già l'etichetta (tag) "gommberg-benvenuto": è il segno "benvenuto già fatto", e per questo nessuno
     riceve la guida due volte, anche con due giri nello stesso giorno;
  3. prende in carico quanti iscritti stanno nel tempo del passo (vedi "tempo"), chi aspetta da più tempo per primo, e
     dà loro l'etichetta del gruppo di stasera ("gommberg-benvenuto-AAAA-MM-GG-HHMM"); gli altri non li tocca;
  4. aspetta che il gruppo in Kit abbia dentro esattamente quegli iscritti (vedi "il ritardo di Kit");
  5. crea l'invio in BOZZA solo per il gruppo (subscriber_filter sull'etichetta del gruppo, modello "Gommberg cornice")
     e lo RILEGGE da Kit (GET, indipendente dalla risposta alla creazione);
  6. solo ora dà a quegli iscritti l'etichetta permanente, e subito dopo programma l'invio tra ATTESA_MINUTI minuti;
     poi lo rilegge di nuovo. Se qualcosa non torna l'invio si toglie; se non si riesce a toglierlo si riporta in bozza
     (send_at null); se non riesce nemmeno quello, il messaggio dice URGENTE e dem.yml apre una segnalazione apposta.
Testo: redazione/benvenuto_mail.html (approvato da Paolo il 25/11/2026). Chiamate a Kit: newsletter.kit, una sola logica
(qui sopra c'è solo uno strato che trasforma ogni risposta illeggibile in "esito incerto" e tiene il registro delle
chiamate del giro); l'elenco degli invii è newsletter.leggi_invii, la lettura leggera a pagine delle edizioni.

L'accensione (ACCESO_DAL, un posto solo): ricevono il benvenuto solo gli iscritti arrivati da quel giorno in poi. I
lettori di prima (iscritti da settimane) e chi si è iscritto nei giorni prima del rilascio NON lo ricevono al primo
giro. La finestra di FINESTRA_GIORNI (7) giorni serve a chi conferma giorni dopo l'iscrizione (Kit dà la data di
iscrizione, non di conferma) e a chi perde qualche giro: i doppioni li impedisce l'etichetta permanente.

Il ritardo di Kit (dichiarato da Kit: developers.kit.com/api-reference/eventual-consistency). Gli elenchi (gli iscritti,
gli iscritti di un'etichetta, i filtri) sono aggiornati in ritardo rispetto alle scritture: di solito 30 secondi, fino a
5 minuti. Le scritture e le letture per id no: la risposta di Kit a una scrittura fa fede. Quindi:
  - che l'etichetta sia stata data lo dice la risposta alla scrittura (201 con lo stesso iscritto), non l'elenco;
  - l'elenco del gruppo si rilegge ogni PAUSA_GRUPPO secondi per al massimo ATTESA_GRUPPO (120): finché ha meno iscritti
    degli attesi è ritardo, e si aspetta; un iscritto che non è tra gli attesi non è ritardo, è un errore, e ferma subito;
  - se dopo ATTESA_GRUPPO l'elenco non è ancora completo, nessun invio. Nel giro della sera nessuno è ancora segnato:
    il giro si rimanda da sé alla sera dopo (esce con 0, lo scrive nel registro); se qualcuno aspetta da più di
    ATTESA_AVVISO giorni esce con 1. Nella prova dal vivo è un fermo, e si rilancia;
  - l'invio parte ATTESA_MINUTI (10) minuti dopo: più del ritardo massimo dichiarato.

L'ordine, e perché (mai due mail allo stesso iscritto, e nessuno segnato senza mail finché si può evitare):
  - l'etichetta permanente PRIMA della programmazione, ma DOPO la bozza riletta: è l'ultima cosa prima di programmare.
    Un giro interrotto o fermato in qualunque punto prima (etichette del gruppo, attesa del gruppo, bozza) non ha segnato
    nessuno: tutti tornano candidati al giro dopo, in un gruppo nuovo, e ricevono la guida una volta. Un giro interrotto
    tra le etichette permanenti e la programmazione: chi è stato segnato perde la guida (riceve comunque l'edizione e la
    pagina benvenuto.html gli ha già detto tutto), ma nessuno la riceve due volte. L'inverso (invio programmato ed
    etichetta permanente non data) non può succedere: la programmazione viene per ultima.
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
  - tempo. Lo script si dà PASSO (450) secondi, 30 meno del passo di dem.yml (8 minuti), e ogni chiamata a Kit sta nel
    tempo rimasto: si arrende da sé, con il suo messaggio, prima che GitHub chiuda il passo (e a 465 secondi un allarme
    lo ferma comunque: se in quel momento un invio è programmato e non verificato, il messaggio è URGENTE). Gli ultimi
    RISERVA (210) secondi sono della programmazione: la PUT parte solo se restano, il tempo di rileggere e, se serve,
    togliere l'invio. I primi LAVORO (240) sono per tutto il resto. Il giro prende in carico solo gli iscritti che
    stanno in quel tempo: ogni iscritto costa due chiamate, e una chiamata è stimata il doppio della media misurata
    sulle letture dello stesso giro (mai meno di un secondo); tolti l'attesa del gruppo e il margine, con Kit a mezzo
    secondo a chiamata sono circa 40 iscritti a sera, con Kit a 2 secondi circa 7. Gli altri restano candidati per la
    sera dopo, senza nessuna etichetta. E l'etichetta permanente non si dà a nessuno se non resta il tempo per darla a
    tutti i presi in carico e programmare.

Uso:   python3 redazione/benvenuto.py controlla          il testo e la mail composta, senza rete (lo fa il collaudo)
       python3 redazione/benvenuto.py anteprima          scrive _benvenuto/benvenuto.html, la mail come la vedrà il lettore
       python3 redazione/benvenuto.py piano              legge Kit e dice a quanti iscritti partirebbe, senza scrivere nulla
       python3 redazione/benvenuto.py invia              il giro vero (lo fa dem.yml, solo da main)
       python3 redazione/benvenuto.py impronta           legge un indirizzo dallo standard input e ne stampa l'impronta: i
                                                         primi 16 caratteri esadecimali di SHA-256 dell'indirizzo in
                                                         minuscolo e senza spazi. Non scrive e non chiama nessuno
       python3 redazione/benvenuto.py bozza impronta:X   prova dal vivo, passo 2: SOLO una bozza per un gruppo nuovo con
                                                         dentro il solo iscritto attivo (confermato) che ha quell'impronta;
                                                         la rilegge, conta il gruppo prima e dopo e si ferma. Non spedisce
       python3 redazione/benvenuto.py prova impronta:X   prova dal vivo, passo 3: programma tra ATTESA_MINUTI minuti l'ULTIMO
                                                         invio di prova, solo se è una bozza con il filtro su un gruppo di
                                                         prova con dentro lui solo; poi rilegge l'invio e riconta il gruppo.
                                                         Le bozze di prova più vecchie non le programma mai: le dice
       python3 redazione/benvenuto.py pulizia            toglie da Kit ciò che le prove lasciano: le bozze di prova non
                                                         programmate e le etichette dei gruppi di prova. Mai un invio
                                                         programmato o spedito, mai un'etichetta che non sia di prova

L'iscritto di prova si indica SOLO con l'impronta, mai con l'indirizzo: il repository è pubblico e chiunque legge gli
input e i registri dei giri. Lo script legge da Kit gli iscritti attivi e sceglie quello la cui impronta coincide; zero o
più di uno: errore, e non fa nulla. Non stampa mai un indirizzo né un dato letto da Kit che non abbia prima controllato
(numeri, nomi di gruppi che ha creato lui): nemmeno negli errori, e mai un tracciato. L'impronta non è un segreto: chi
conosce o indovina l'indirizzo la può ricalcolare; serve a non scriverlo in chiaro.

Che cosa dice ogni giro, senza indirizzi: i passi fatti, i conti del gruppo letti in Kit uno dopo l'altro (per esempio
"0 x3, 1": tre letture a zero, poi uno) e, in fondo, il registro delle chiamate a Kit con il codice HTTP di ognuna
(metodo e percorso, senza parametri e senza l'id dell'iscritto; 0 = nessuna risposta leggibile).

LA PROVA DAL VIVO, prima di accendere. Si fa da GitHub, dove sta la chiave di Kit (il segreto KIT_API_KEY: non la legge
nessuna chat e nessun PC), lanciando a mano dem.yml dal ramo da provare. I modi "prova-" fanno girare solo questo
script, mai dem.py e mai "invia"; l'esito si legge nel riepilogo del giro.
  0. l'impronta, in una sessione (l'indirizzo non finisce in nessun file):
       X=$(printf '%s' 'INDIRIZZO' | python3 redazione/benvenuto.py impronta)
  1. gh workflow run dem.yml --ref RAMO -f modo=prova-piano
       sole letture: quanti iscritti riceverebbero il benvenuto stasera
  2. gh workflow run dem.yml --ref RAMO -f modo=prova-bozza -f impronta="$X"
       il riepilogo deve dire: gruppo di prova con 1 iscritto, bozza riletta con il filtro sul solo gruppo. Il giro può
       durare fino a un paio di minuti: aspetta che Kit aggiorni l'elenco del gruppo. Poi in Kit, Broadcasts, la bozza
       gommberg-benvenuto-prova-...: i destinatari devono essere 1. Se non è 1: lancia prova-pulizia e fermati
  3. gh workflow run dem.yml --ref RAMO -f modo=prova-invio -f impronta="$X"
       tra le 8:00 e le 8:20 o tra le 10:30 e le 20:49 (le stesse fasce del giro); la mail arriva al solo iscritto di
       prova dopo ATTESA_MINUTI minuti. L'attesa è la stessa del giro vero e supera la durata del passo: un invio
       registrato male si toglie sempre prima che parta
  4. gh workflow run dem.yml --ref RAMO -f modo=prova-pulizia
       dopo che la mail è arrivata (o dopo una prova fermata): toglie le bozze di prova non programmate e le etichette
       dei gruppi di prova, e dice che cosa ha tolto. Finché l'invio di prova è programmato e non ancora partito non
       tocca né lui né la sua etichetta: si rilancia dopo
Che cosa resta in Kit dopo la prova, finché non si lancia prova-pulizia: l'etichetta del gruppo
gommberg-benvenuto-prova-AAAA-MM-GG-HHMM sull'iscritto di prova, una per ogni bozza tentata; l'invio di prova tra i
Broadcasts, spedito a 1 (quello resta nello storico anche dopo la pulizia), o ancora in bozza se ci si è fermati al
passo 2. La prova NON dà l'etichetta permanente "gommberg-benvenuto": l'iscritto di prova resta com'era. Se è un lettore
di prima dell'accensione il benvenuto vero non lo riceve mai (non è nella finestra); se invece si è iscritto da
ACCESO_DAL in poi e da meno di 7 giorni, il giro della sera gli manda anche quello vero.
Esce con 1 quando qualcosa va guardato: dem.yml apre allora la segnalazione a Paolo. La chiave è KIT_API_KEY, mai stampata.
"""
import hashlib
import html
import re
import signal
import sys
import time
import traceback
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
NOME_PROVA = re.compile(re.escape(PROVA) + r"\d{4}-\d{2}-\d{2}-\d{4}")      # il nome intero di un gruppo di prova
IMPRONTA = re.compile(r"impronta:([0-9a-f]{16})")                           # come si indica l'iscritto di prova
ACCESO_DAL = "2026-11-28"          # accensione (ora di Roma, dalla mezzanotte): solo chi si iscrive da qui riceve il benvenuto
FINESTRA_GIORNI = 7                # iscritti arrivati negli ultimi 7 giorni (chi conferma tardi, giri persi)
ATTESA_AVVISO = 3                  # chi riceve il benvenuto oltre 3 giorni dopo l'iscrizione: avviso (giri saltati?)
MAX_NUOVI = 100                    # oltre, qualcosa non va (un filtro ignorato da Kit?): nessun invio
ATTESA_MINUTI = 10                 # l'invio parte dopo: il tempo di toglierlo se Kit lo registra male (più di PASSO,
                                   # così la pulizia finisce sempre prima della partenza). Vale anche per la prova
FASCIA = (75, 45)                  # minuti prima e dopo l'uscita in cui non si spedisce
LETTURE = 3                        # tentativi per ogni lettura su un guasto momentaneo (429, 5xx, rete)
ATTESA_LETTURE = 10                # secondi tra un tentativo e l'altro (il collaudo la azzera)
PASSO = 450                        # secondi che lo script si dà, contati dall'avvio: 30 meno del passo di dem.yml
                                   # (timeout-minutes: 8), così si arrende da sé, con il suo messaggio, prima che GitHub lo chiuda
ALLARME = PASSO + 15               # limite netto (SIGALRM): una chiamata appesa oltre il suo tempo non porta il passo alla
                                   # chiusura di GitHub senza che lo script abbia detto com'è finita
TEMPO_CHIAMATA = 30                # tetto di una chiamata a Kit (il timeout di newsletter.kit, che si accorcia col tempo rimasto)
RISERVA = 7 * TEMPO_CHIAMATA       # programmazione + 2 riletture + pulizia (2 DELETE, 1 PUT in bozza, 1 rilettura):
                                   # la PUT parte solo se nel passo restano questi secondi, così la pulizia di un
                                   # invio sbagliato finisce sempre prima della scadenza del passo
RISERVA_GRUPPO = 5 * TEMPO_CHIAMATA  # prova: ricontare il gruppo dopo la programmazione (1 lettura) + pulizia (4 chiamate)
LAVORO = PASSO - RISERVA           # secondi per tutto ciò che viene prima della programmazione (letture, etichette,
                                   # attesa del gruppo, bozza): 240
ATTESA_GRUPPO = 120                # Kit aggiorna gli elenchi con ritardo, e lo dichiara (di solito 30 secondi, fino a 5
                                   # minuti): l'elenco del gruppo si rilegge per al massimo questi secondi
PAUSA_GRUPPO = 5                   # secondi tra una rilettura del gruppo e l'altra (il collaudo la azzera)
LETTURE_GRUPPO = ATTESA_GRUPPO // PAUSA_GRUPPO
STIMA_MINIMA, STIMA_FATTORE = 1.0, 2   # il costo stimato di una chiamata: il doppio della media misurata in questo giro,
                                   # mai meno di un secondo. Serve a decidere quanti iscritti si riesce a servire
MARGINE = 35                       # sotto questi secondi di lavoro rimasti non si scrive più nulla in Kit
MAX_PAGINE = 20
PER_PAGINA = 500
TRATTINI_LUNGHI = re.compile("[–—]")
VIA_ISCRITTO = re.compile(r"(/subscribers/)\d+")
orologio = time.monotonic          # il collaudo lo sostituisce
pausa = time.sleep                 # il collaudo la sostituisce
_avvio = None                      # istante dell'avvio (orologio), o None se nessuna scadenza è partita
_chiamate = []                     # le chiamate a Kit di questo giro: (metodo, percorso, codice HTTP, secondi)
_in_volo = None                    # (id, ora) di un invio programmato e non ancora verificato né tolto


class Fermo(Exception):
    """Il giro si ferma senza inviare nulla. Il messaggio dice perché e che cosa è già stato fatto."""


class Ritardo(Fermo):
    """L'elenco di un gruppo in Kit non è ancora quello atteso dopo ATTESA_GRUPPO secondi (Kit lo aggiorna con ritardo)."""


class Rimando(Exception):
    """Il giro non ha potuto servire nessuno e nessuno è stato segnato: ci pensa il prossimo giro (esce con 0)."""


class Avviso(Exception):
    """Il giro ha fatto il suo lavoro, ma c'è qualcosa da guardare (esce con 1: segnalazione)."""


class Scaduto(BaseException):
    """Il limite netto del passo (ALLARME) è arrivato con una chiamata ancora appesa. Non è una Exception: nessuno
    strato la prende per una risposta di Kit."""


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
def _allarme(*_):
    raise Scaduto()


def avvia_scadenza():
    """Parte l'orologio del passo: da qui ogni chiamata a Kit sta nel tempo rimasto (newsletter.kit la accorcia e, a
    tempo finito, non chiama più), e ad ALLARME secondi lo script si ferma comunque, con il suo messaggio."""
    global _avvio
    ferma_scadenza()
    _avvio = orologio()
    nl._scadenza = nl.orologio() + PASSO
    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, _allarme)
        signal.alarm(ALLARME)


def spegni_allarme():
    if hasattr(signal, "SIGALRM"):
        signal.alarm(0)


def ferma_scadenza():
    global _avvio, _in_volo
    spegni_allarme()
    _avvio, _in_volo, nl._scadenza = None, None, None
    _chiamate.clear()


def resta_nel_passo():
    return float("inf") if _avvio is None else PASSO - (orologio() - _avvio)


def rimasto():
    """Secondi di lavoro rimasti prima che resti solo la riserva della programmazione."""
    return resta_nel_passo() - RISERVA


def kit_sicuro(metodo, percorso, dati=None):
    """newsletter.kit, con due aggiunte: una risposta che non si legge (200 con un corpo non JSON, connessione rotta a
    metà, qualsiasi eccezione) diventa (0, ...), cioè "esito incerto", come la rete muta, mai un tracciato; e ogni
    chiamata va nel registro del giro (metodo, percorso senza parametri e senza l'id dell'iscritto, codice, secondi)."""
    t0 = orologio()
    try:
        stato, corpo = nl.kit(metodo, percorso, dati)
    except Exception as e:  # noqa: BLE001
        stato, corpo = 0, {"errore": f"risposta di Kit non leggibile ({type(e).__name__})"}
    annota(metodo, percorso, stato, t0)
    return stato, corpo


def annota(metodo, percorso, stato, t0):
    _chiamate.append((metodo, VIA_ISCRITTO.sub(r"\1*", str(percorso).split("?")[0]), intero(stato) or 0, max(0.0, orologio() - t0)))


def stima_chiamata():
    """Il costo prudente di una chiamata a Kit, in secondi, misurato su quelle già fatte in questo giro."""
    media = sum(c[3] for c in _chiamate) / len(_chiamate) if _chiamate else 0.0
    return max(STIMA_MINIMA, STIMA_FATTORE * media)


def registro_kit():
    """Che cosa ha risposto Kit, chiamata per chiamata, in una riga: metodo, percorso, codice HTTP (0 = nessuna risposta
    leggibile). Le chiamate uguali di fila sono contate. Mai un dato degli iscritti."""
    if not _chiamate:
        return "Kit: nessuna chiamata"
    voci, tot = [], sum(c[3] for c in _chiamate)
    for metodo, via, stato, _ in _chiamate:
        voce = f"{metodo} {via} {stato}"
        if voci and voci[-1][0] == voce:
            voci[-1][1] += 1
        else:
            voci.append([voce, 1])
    tempi = f"{len(_chiamate)} chiamate in {tot:.1f} secondi (media {tot / len(_chiamate):.2f})".replace(".", ",")
    return f"Kit, {tempi}, con il codice HTTP di ognuna: " + "; ".join(v + (f" x{n}" if n > 1 else "") for v, n in voci)


def chiama(metodo, percorso, dati=None):
    if rimasto() <= 0:
        raise Fermo("tempo del giro scaduto prima di finire: nessun invio creato")
    return kit_sicuro(metodo, percorso, dati)


def leggi(percorso, pulizia=False, tentativi=LETTURE):
    """Una lettura di Kit: su un guasto momentaneo (rete, risposta illeggibile, 429, 5xx) si riprova, `tentativi` volte.
    Torna il corpo (dict). pulizia=True: lettura per controllare o togliere un invio, anche a tempo scaduto."""
    for tentativo in range(1, tentativi + 1):
        stato, corpo = (kit_sicuro if pulizia else chiama)("GET", percorso)
        if stato == 200 and isinstance(corpo, dict):
            return corpo
        if stato == 200:
            raise Fermo(f"risposta di Kit fuori forma a GET {percorso.split('?')[0]}")
        if not (stato == 0 or stato == 429 or stato >= 500) or tentativo == tentativi:
            raise Fermo(f"Kit non ha risposto a GET {percorso.split('?')[0]} (HTTP {stato}, {tentativo} tentativ"
                        f"{'o' if tentativo == 1 else 'i'})")
        pausa(max(0, min(ATTESA_LETTURE, rimasto())) if not pulizia else min(ATTESA_LETTURE, 2))


def leggi_tutto(percorso, chiave, pulizia=False, tentativi=LETTURE, pagine=MAX_PAGINE):
    """Tutte le pagine di un elenco di Kit (cursore after). Ogni pagina deve avere la lista e la paginazione: un
    elenco parziale non vale mai per completo."""
    out, dopo = [], None
    for _ in range(pagine):
        corpo = leggi(percorso + (f"&after={dopo}" if dopo else ""), pulizia, tentativi)
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
    raise Fermo(f"elenco di Kit troppo lungo (oltre {pagine} pagin{'a' if pagine == 1 else 'e'}): fermo per prudenza")


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


def iscritti_con(tag_id, dal=None, pulizia=False, tentativi=LETTURE, pagine=MAX_PAGINE):
    """Gli id degli iscritti (di ogni stato) che hanno l'etichetta, letti dalla parte dell'etichetta."""
    filtro = f"&created_after={dal}" if dal else ""
    lista = leggi_tutto(f"/tags/{tag_id}/subscribers?status=all&per_page={PER_PAGINA}{filtro}", "subscribers", pulizia,
                        tentativi, pagine)
    ids = {intero(s.get("id")) for s in lista}
    if None in ids:
        raise Fermo(f"risposta di Kit fuori forma a GET /tags/{tag_id}/subscribers (iscritto senza id)")
    return ids


def gruppo_in_kit(tag_id, attesi, nome):
    """Rilegge l'elenco del gruppo finché ha dentro esattamente gli attesi, e torna i conti letti. Kit aggiorna gli
    elenchi con ritardo (lo dichiara: di solito 30 secondi, fino a 5 minuti), quindi un elenco ancora corto si rilegge
    ogni PAUSA_GRUPPO secondi, per al massimo ATTESA_GRUPPO; poi Ritardo. Un iscritto che non è tra gli attesi non è un
    ritardo: fermo subito."""
    attesi, conti, t0 = set(attesi), [], orologio()
    while True:
        ids = iscritti_con(tag_id)
        conti.append(len(ids))
        if ids == attesi:
            return conti
        letti = conti_letti(conti)
        if ids - attesi:
            raise Fermo(f"l'etichetta {nome} in Kit ha {len(ids)} iscritti invece di {len(attesi)}, e {len(ids - attesi)} non "
                        f"glieli ho dati io (conti letti: {letti}): nessun invio")
        if len(conti) >= LETTURE_GRUPPO or orologio() - t0 + PAUSA_GRUPPO > ATTESA_GRUPPO or rimasto() < MARGINE + PAUSA_GRUPPO:
            raise Ritardo(f"l'etichetta {nome} in Kit ha {len(ids)} iscritti invece di {len(attesi)} dopo {len(conti)} letture in "
                          f"{orologio() - t0:.0f} secondi (conti letti: {letti}): Kit aggiorna gli elenchi con ritardo, di solito 30 "
                          "secondi e fino a 5 minuti; nessun invio")
        pausa(PAUSA_GRUPPO)


def conti_letti(conti):
    """I conti di un gruppo letti uno dopo l'altro, in breve: "0 x3, 1"."""
    voci = []
    for c in conti:
        if voci and voci[-1][0] == c:
            voci[-1][1] += 1
        else:
            voci.append([c, 1])
    return ", ".join(f"{c}" + (f" x{n}" if n > 1 else "") for c, n in voci)


def metti(tag_id, iscritto):
    """Etichetta a un iscritto: True se data ora. Kit risponde 201 se la dà, 200 se l'iscritto l'aveva già, e nella
    risposta ripete l'iscritto: fa fede quella (è la scrittura, non un elenco che arriva in ritardo), quindi deve dire
    lo stesso id. Si ritenta solo un guasto momentaneo (dare un'etichetta due volte non fa danni); dopo un tentativo
    senza risposta anche 200 va bene (l'aveva data il tentativo di prima). Un 200 al primo colpo vuol dire che
    l'etichetta c'era già: False."""
    for tentativo in range(1, LETTURE + 1):
        stato, corpo = chiama("POST", f"/tags/{tag_id}/subscribers/{iscritto}", {})
        if stato == 201 or (stato == 200 and tentativo > 1):
            chi = corpo.get("subscriber") if isinstance(corpo, dict) else None
            return isinstance(chi, dict) and intero(chi.get("id")) == iscritto
        if not (stato == 0 or stato == 429 or stato >= 500) or tentativo == LETTURE:
            return False
        pausa(max(0, min(ATTESA_LETTURE, rimasto())))


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
    Torna "tolto", "in bozza" o "" (né l'uno né l'altro: URGENTE). Lavora anche a tempo di lavoro scaduto."""
    global _in_volo
    for _ in range(2):
        stato, _ = kit_sicuro("DELETE", f"/broadcasts/{bid}")
        if stato in (200, 204, 404):
            _in_volo = None
            return "tolto"
        if not (stato == 0 or stato == 429 or stato >= 500):
            break
    if dati is not None:
        kit_sicuro("PUT", f"/broadcasts/{bid}", dict(dati, send_at=None))
        b = rileggi(bid, tentativi=1)
        if b is not None and not b.get("send_at"):
            _in_volo = None
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


def elenco_invii():
    """Tutti gli invii di Kit nella forma leggera (id, description, send_at, status: senza contenuto, filtro e modello).
    È newsletter.leggi_invii, la lettura a pagine che newsletter.py usa per le edizioni (G-69): una sola logica. Se
    l'elenco non si legge per intero: fermo ("non so" non diventa mai "non c'è")."""
    t0 = orologio()
    try:
        invii = nl.leggi_invii(LETTURE, ATTESA_LETTURE, rigoroso=True)
    except nl.ElencoNonLeggibile as e:
        annota("GET", "/broadcasts (elenco leggero)", e.stato, t0)
        raise Fermo(f"elenco degli invii di Kit non leggibile (HTTP {intero(e.stato) or 0}"
                    + (", troppo lungo" if e.troppo_lungo else "") + (f", {e.motivo}" if e.motivo else "") + ")")
    except Exception as e:  # noqa: BLE001
        annota("GET", "/broadcasts (elenco leggero)", 0, t0)
        raise Fermo(f"elenco degli invii di Kit non leggibile ({type(e).__name__})")
    annota("GET", "/broadcasts (elenco leggero)", 200, t0)
    return invii


def invii_con(descrizione):
    """Gli id degli invii in Kit con quella description (per chiarire una creazione dall'esito incerto)."""
    return [b["id"] for b in elenco_invii() if str(b.get("description") or "") == descrizione and intero(b.get("id"))]


def dati_invio(gruppo_id, descrizione, modello):
    oggetto, anteprima, corpo = componi()
    return {"subject": oggetto, "preview_text": anteprima, "content": corpo, "description": descrizione, "public": False,
            "published_at": datetime.now(UTC).isoformat(timespec="seconds"), "send_at": None, "email_template_id": modello,
            "subscriber_filter": [{"all": [{"type": "tag", "ids": [gruppo_id]}], "any": None, "none": None}]}


def crea_bozza(gruppo_id, nome_gruppo, modello, attesi, senza):
    """Crea la bozza per il gruppo (mai ritentata) e la rilegge. Torna (id, dati) solo se Kit, riletto, ha la bozza con
    il filtro sul solo gruppo; altrimenti la toglie e si ferma. Prima aspetta che l'elenco del gruppo in Kit abbia dentro
    esattamente gli attesi (gruppo_in_kit). senza: che cosa è già stato fatto, per i messaggi. Torna anche i conti letti."""
    dati = dati_invio(gruppo_id, nome_gruppo, modello)
    try:
        conti = gruppo_in_kit(gruppo_id, attesi, nome_gruppo)    # ultimo controllo: nel gruppo i soli voluti
    except Ritardo as e:
        raise Ritardo(f"{e} ({senza})")
    except Fermo as e:
        raise Fermo(f"{e} ({senza})")
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
    return bid, dati, conti


def programma(bid, gruppo_id, dati, invio, senza):
    """Programma la bozza (già verificata) e la rilegge: qualunque risposta alla PUT (anche nessuna) si chiarisce con
    la rilettura. Se non è esattamente come voluta, si toglie (o si riporta in bozza)."""
    global _in_volo
    voluti = dict(dati, send_at=invio.astimezone(UTC).isoformat(timespec="seconds"))
    if resta_nel_passo() < RISERVA:      # non c'è più il tempo per rimediare a una programmazione sbagliata
        raise Fermo(f"tempo del passo insufficiente per programmare in sicurezza: {esito_tolto(bid, dati)}, nessun invio, {senza}")
    _in_volo = (bid, invio)              # da qui l'invio può partire: se il passo scade prima della verifica, URGENTE
    stato, risposta = kit_sicuro("PUT", f"/broadcasts/{bid}", voluti)
    riletta = rileggi(bid)
    risposta_b = broadcast_di(risposta)
    # la risposta conta solo se si legge: una risposta illeggibile (0, o 200 senza l'invio) la chiarisce la rilettura;
    # un rifiuto (4xx, 5xx) o una risposta leggibile diversa dal voluto bastano per togliere
    risposta_ok = stato == 0 or (stato == 200 and (risposta_b is None or com_e(risposta_b, gruppo_id, invio)))
    if com_e(riletta, gruppo_id, invio) and risposta_ok:
        _in_volo = None
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


def posti(nuovi):
    """Quanti dei nuovi iscritti il giro riesce a servire nel tempo di lavoro rimasto. Ogni iscritto costa due chiamate
    (etichetta del gruppo, etichetta permanente); dopo le etichette servono l'attesa del gruppo (ATTESA_GRUPPO), la bozza
    con la sua rilettura e il margine. Il costo di una chiamata è stima_chiamata(), misurata sulle letture già fatte."""
    costo, tempo = stima_chiamata(), rimasto() - ATTESA_GRUPPO - MARGINE
    if tempo == float("inf"):              # nessuna scadenza partita (il giro chiamato senza il suo orologio)
        return len(nuovi)
    return max(0, min(len(nuovi), int((tempo - 4 * costo) // (2 * costo))))


def giro(esegui=True, adesso=None):
    """Il giro della sera. Torna 0 (fatto o niente da fare) o solleva Fermo, Rimando o Avviso."""
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
    nuovi = sorted((s for s in candidati if s["id"] not in gia and FATTO not in s["etichette"]), key=lambda s: (s["creato"], s["id"]))
    print(f"Benvenuto: {len(candidati)} iscritti confermati arrivati negli ultimi {FINESTRA_GIORNI} giorni (dal {ACCESO_DAL}), "
          f"{len(candidati) - len(nuovi)} già salutati, {len(nuovi)} da salutare")
    soglia = adesso.astimezone(UTC) - timedelta(days=ATTESA_AVVISO)
    in_attesa = [s for s in nuovi if s["creato"] < soglia]
    tardi = (f"{len(in_attesa)} iscritt{'o' if len(in_attesa) == 1 else 'i'} confermat{'o' if len(in_attesa) == 1 else 'i'} "
             f"aspettava{'' if len(in_attesa) == 1 else 'no'} il benvenuto da più di {ATTESA_AVVISO} giorni dall'iscrizione "
             "(giri saltati o rimandati, o conferma arrivata tardi): guarda che dem.yml parta ogni sera") if in_attesa else ""
    if tardi:
        print(f"AVVISO: {tardi}")
    if not nuovi:
        return 0
    if len(nuovi) > MAX_NUOVI:
        raise Fermo(f"{len(nuovi)} iscritti nuovi in {FINESTRA_GIORNI} giorni (oltre {MAX_NUOVI}): troppi per essere veri, nessun invio")
    if not esegui:
        print(f"Piano: etichetta del gruppo e invio alle {invio:%H:%M} per {len(nuovi)} iscritt{'o' if len(nuovi) == 1 else 'i'}")
        return 0
    quanti = posti(nuovi)
    if not quanti:
        raise Fermo(f"non resta il tempo per servire nemmeno un iscritto (Kit risponde in circa {stima_chiamata() / STIMA_FATTORE:.0f} secondi "
                    "a chiamata): nessuna etichetta data, nessun invio, tutti restano candidati per il prossimo giro")
    presi = nuovi[:quanti]                 # chi aspetta da più tempo per primo; gli altri non vengono toccati
    if quanti < len(nuovi):
        print(f"Benvenuto: in questo giro {quanti} iscritti su {len(nuovi)}, quanti ne stanno nel tempo del passo (stima di "
              f"{stima_chiamata():.0f} secondi a chiamata); gli altri {len(nuovi) - quanti} restano candidati per il prossimo giro")
    nome = f"{FATTO}-{adesso:%Y-%m-%d-%H%M}"
    nessuno = "nessuna etichetta permanente data, tutti restano candidati per il prossimo giro"
    fatto = fatto or etichetta(FATTO, crea=True)
    gruppo = nuovo_gruppo(nome)
    for s in presi:
        if not metti(gruppo, s["id"]):
            raise Fermo(f"etichetta del gruppo non data a un iscritto: nessun invio creato, {nessuno}")
    attesi = [s["id"] for s in presi]
    try:
        bid, dati, conti = crea_bozza(gruppo, nome, modello, attesi, nessuno)
    except Ritardo as e:                   # nessuno è segnato: non è un errore, è Kit che non ha ancora aggiornato l'elenco
        if tardi:
            raise Avviso(f"{tardi}. E stasera: {e}")
        raise Rimando(str(e))
    print(f"Benvenuto: gruppo {nome} di {len(attesi)} iscritt{'o' if len(attesi) == 1 else 'i'}, conti letti in Kit: {conti_letti(conti)}")
    # la bozza c'è ed è giusta: solo ora, e solo se resta il tempo per tutte e per programmare, le etichette permanenti
    segnati = 0
    try:
        if rimasto() < len(presi) * stima_chiamata() + MARGINE:
            raise Fermo("non resta il tempo per segnare gli iscritti e programmare l'invio")
        for s in presi:
            if not metti(fatto, s["id"]):  # anche "l'aveva già": salutato da un altro giro, e ora è nel gruppo. Fermo
                raise Fermo("etichetta permanente non data a un iscritto (o l'aveva già)")
            segnati += 1
    except Fermo as e:
        raise Fermo(f"{e}: {esito_tolto(bid, dati)}, nessun invio; "
                    + (f"{segnati} iscritti segnati senza mail, gli altri restano candidati per il prossimo giro" if segnati else nessuno))
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


# ------------------------------------------------------------------ la prova dal vivo
RESTA = ("Che cosa resta in Kit finché non lanci prova-pulizia: l'etichetta del gruppo di prova sull'iscritto di prova e "
         "l'invio di prova tra i Broadcasts (in bozza, poi spedito a 1). La prova non dà l'etichetta permanente "
         + FATTO + ": l'iscritto di prova resta com'era (un lettore di prima dell'accensione non riceve il benvenuto vero; chi "
         f"si è iscritto dal {ACCESO_DAL} in poi e da meno di {FINESTRA_GIORNI} giorni riceve anche quello vero dal giro della sera)")
RESTA_FERMO = ("Che cosa può essere rimasto in Kit: l'etichetta di un gruppo di prova (" + PROVA + "...) sull'iscritto di prova, "
               "e un invio di prova solo se il messaggio qui sopra dice che non è stato tolto. Li toglie prova-pulizia")


def impronta_di(indirizzo):
    """L'impronta di un indirizzo: i primi 16 caratteri esadecimali di SHA-256 dell'indirizzo in minuscolo e senza spazi."""
    return hashlib.sha256("".join(str(indirizzo).split()).lower().encode("utf-8")).hexdigest()[:16]


def iscritto_di_prova(chi):
    """L'id del solo iscritto attivo (confermato) con quell'impronta. Zero o più di uno: fermo. Mai un indirizzo in un
    messaggio: degli iscritti letti da Kit escono di qui solo un id e un conto."""
    m = IMPRONTA.fullmatch(str(chi).strip().lower())
    if not m:
        raise Fermo("l'iscritto di prova si indica con impronta: seguito da 16 caratteri esadecimali (benvenuto.py impronta), "
                    "mai con l'indirizzo: nulla di fatto")
    trovati = []
    for s in leggi_tutto(f"/subscribers?status=active&per_page={PER_PAGINA}", "subscribers"):
        posta = s.get("email_address")
        if not intero(s.get("id")) or s.get("state") != "active" or not isinstance(posta, str) or "@" not in posta:
            raise Fermo("risposta di Kit fuori forma a GET /subscribers (iscritto senza id, stato attivo o indirizzo): nulla di fatto")
        if impronta_di(posta) == m.group(1):
            trovati.append(s["id"])
    if len(trovati) != 1:
        raise Fermo(f"l'impronta corrisponde a {len(trovati)} iscritti attivi, ne serve esattamente 1"
                    + (" (l'indirizzo di prova deve essere iscritto e confermato, e l'impronta calcolata con benvenuto.py impronta)"
                       if not trovati else "") + ": nulla di fatto")
    return trovati[0]


def solo_lui(gruppo, chi, tentativi=LETTURE):
    """True se in Kit il gruppo ha dentro il solo iscritto di prova (di ogni stato), riletto ora. Lettura di pulizia:
    anche a tempo scaduto. Un elenco che non si legge vale come no."""
    try:
        return iscritti_con(gruppo, pulizia=True, tentativi=tentativi, pagine=1) == {chi}
    except Fermo:
        return False


def bozza(chi, adesso=None):
    """Prova dal vivo, passo 2: la sola bozza per un gruppo nuovo con dentro il solo iscritto di prova, riletta; il gruppo
    contato prima (aspettando che Kit aggiorni l'elenco) e dopo. Non spedisce."""
    adesso = (adesso or datetime.now(ROMA)).astimezone(ROMA)
    print("Prova del benvenuto, bozza (non spedisce nulla):")
    male = problemi_testo()
    if male:
        raise Fermo("testo della mail: " + "; ".join(male))
    modello = modello_cornice()
    chi = iscritto_di_prova(chi)
    print("- iscritto di prova: trovato per impronta, 1 solo iscritto attivo corrisponde")
    nome = f"{PROVA}{adesso:%Y-%m-%d-%H%M}"
    gruppo = nuovo_gruppo(nome)
    if not metti(gruppo, chi):
        raise Fermo(f"etichetta del gruppo di prova {nome} creata ma non data all'iscritto di prova: nessuna bozza")
    print(f"- gruppo di prova {nome}: creato nuovo, e Kit ha confermato l'etichetta all'iscritto di prova")
    bid, dati, conti = crea_bozza(gruppo, nome, modello, [chi], "nessun iscritto segnato")
    print(f"- gruppo riletto da Kit prima della bozza: iscritti nel gruppo 1 (conti letti: {conti_letti(conti)})")
    print(f"- bozza {bid}: creata e riletta da Kit, filtro sul solo gruppo di prova, stato bozza, non programmata")
    if not solo_lui(gruppo, chi):
        raise Fermo(f"dopo la creazione il gruppo di prova {nome} non ha dentro il solo iscritto di prova (o non si rilegge): "
                    f"{esito_tolto(bid, dati)}")
    print("- gruppo riletto dopo la bozza: iscritti nel gruppo 1")
    print(f"- {RESTA}\n")
    print(f"OK: bozza di prova {bid} pronta. In Kit (Broadcasts, {nome}) i destinatari devono essere 1: se non è 1 togli la "
          "bozza a mano e fermati. Poi: prova-invio")
    return bid


def di_prova(invii):
    """Gli invii di prova (description = il nome intero di un gruppo di prova), dal più vecchio al più recente."""
    return sorted((b for b in invii if NOME_PROVA.fullmatch(str(b.get("description") or "")) and intero(b.get("id"))),
                  key=lambda b: b["id"])


def prova(chi, adesso=None):
    """Prova dal vivo, passo 3: programma l'ULTIMO invio di prova, solo se riletto è ancora una bozza con il filtro su un
    gruppo di prova (l'etichetta che porta il suo stesso nome) e il gruppo ha dentro il solo iscritto di prova. Le bozze
    di prova più vecchie non si toccano mai: le dice. Dopo la programmazione riconta il gruppo: se non torna, o non c'è
    il tempo per ricontare e rimediare, l'invio si toglie."""
    global _in_volo
    adesso = (adesso or datetime.now(ROMA)).astimezone(ROMA)
    invio = adesso + timedelta(minutes=ATTESA_MINUTI)
    print("Prova del benvenuto, invio al solo iscritto di prova:")
    if not (orario_ammesso(adesso) and orario_ammesso(invio)):
        raise Fermo(f"fuori orario ({adesso:%H:%M}, l'invio partirebbe alle {invio:%H:%M}): si spedisce tra le {dem.ORA_DA}:00 e le "
                    f"{dem.ORA_A - 1}:59, mai nella fascia dell'edizione. Nulla di fatto: la bozza resta in Kit")
    modello = modello_cornice()
    chi = iscritto_di_prova(chi)
    print("- iscritto di prova: trovato per impronta, 1 solo iscritto attivo corrisponde")
    prove = di_prova(elenco_invii())
    if not prove:
        raise Fermo("nessuna bozza di prova in Kit: lancia prima prova-bozza. Nulla di fatto")
    bid = prove[-1]["id"]
    vecchie = [x["id"] for x in prove[:-1] if not x.get("send_at")]
    altre = (f" Le bozze di prova più vecchie ({', '.join(str(x) for x in vecchie)}) non si programmano mai: le toglie prova-pulizia"
             if vecchie else "")
    b = rileggi(bid)
    nome = str((b or {}).get("description") or "")
    try:
        gruppo = intero(b["subscriber_filter"][0]["all"][0]["ids"][0])
    except (TypeError, KeyError, IndexError):
        gruppo = None
    if b and (b.get("send_at") or str(b.get("status") or "draft").lower() not in ("draft", "")):
        raise Fermo(f"l'ultimo invio di prova ({bid}) è già programmato o spedito: non si programma nulla. Per un'altra prova "
                    f"lancia prima prova-bozza.{altre}")
    if not b or not gruppo or not com_e(b, gruppo, None) or not NOME_PROVA.fullmatch(nome):
        raise Fermo(f"l'ultima bozza di prova ({bid}), riletta, non è una bozza con il filtro su un solo gruppo di prova: non si "
                    f"programma.{altre}")
    if etichetta(nome) != gruppo:       # il gruppo del filtro è l'etichetta di prova che porta il nome della bozza, non un'altra
        raise Fermo(f"il filtro della bozza di prova {bid} non è sull'etichetta {nome}: non si programma.{altre}")
    print(f"- bozza {bid} ({nome}): riletta da Kit, filtro sul solo gruppo di prova, stato bozza")
    if vecchie:
        print(f"- altre bozze di prova più vecchie, non toccate: {', '.join(str(x) for x in vecchie)} (le toglie prova-pulizia)")
    try:
        conti = gruppo_in_kit(gruppo, {chi}, nome)
    except Fermo as e:
        raise Fermo(f"il gruppo di prova non ha dentro il solo iscritto di questa impronta ({e}): non si programma")
    print(f"- gruppo di prova: iscritti nel gruppo 1, l'iscritto di prova (conti letti: {conti_letti(conti)})")
    dati = dati_invio(gruppo, nome, modello)
    programma(bid, gruppo, dati, invio, "nessun iscritto segnato")
    print(f"- invio {bid}: programmato per le {invio:%H:%M} (ora di Roma) e riletto da Kit, filtro sul solo gruppo di prova")
    voluti = dict(dati, send_at=invio.astimezone(UTC).isoformat(timespec="seconds"))
    _in_volo = (bid, invio)             # fino al conto del gruppo: se il passo scade qui, URGENTE
    if resta_nel_passo() < RISERVA_GRUPPO:
        raise Fermo(f"non resta il tempo per ricontare il gruppo dopo la programmazione e rimediare: {esito_tolto(bid, voluti, invio)}")
    if not solo_lui(gruppo, chi, tentativi=1):
        raise Fermo(f"dopo la programmazione il gruppo di prova {nome} non ha dentro il solo iscritto di prova (o non si rilegge): "
                    f"{esito_tolto(bid, voluti, invio)}")
    _in_volo = None
    print("- gruppo riletto dopo la programmazione: iscritti nel gruppo 1")
    print(f"- {RESTA}\n")
    print(f"OK: prova programmata (invio {bid}) per le {invio:%H:%M}, al solo iscritto di prova")
    return bid


def pulisci():
    """Toglie da Kit ciò che le prove dal vivo lasciano: le bozze di prova NON programmate e le etichette dei gruppi di
    prova. Di prova è solo ciò che porta il nome intero di un gruppo di prova (NOME_PROVA): mai l'etichetta permanente,
    mai un gruppo o un invio del giro della sera, mai una mail straordinaria. Un invio programmato o spedito non si tocca
    mai; e finché un invio di prova è in Kit senza essere stato spedito, la sua etichetta resta (è il suo filtro). Chi
    aveva un'etichetta tolta resta iscritto: perde solo quella."""
    print("Prova del benvenuto, pulizia (solo bozze ed etichette di prova):")
    tolti, male, occupate = 0, [], set()
    for x in di_prova(elenco_invii()):
        bid, nome = x["id"], str(x["description"])
        b = rileggi(bid)                                  # per id, nella forma intera: fa fede questa
        stato = str((b or {}).get("status") or "").lower()
        if not b or not NOME_PROVA.fullmatch(str(b.get("description") or "")) or str(b.get("description")) != nome:
            occupate.add(nome)
            male.append(f"invio {bid} ({nome}) non riletto o cambiato: non toccato, e la sua etichetta resta")
        elif not b.get("send_at") and stato in ("draft", ""):
            if togli(bid) == "tolto":
                tolti += 1
                print(f"- bozza {bid} ({nome}): tolta")
            else:
                occupate.add(nome)
                male.append(f"bozza {bid} ({nome}): Kit non l'ha tolta, e la sua etichetta resta")
        elif stato == "completed":
            print(f"- invio {bid} ({nome}): spedito, resta nello storico di Kit")
        else:
            occupate.add(nome)
            detto = stato if re.fullmatch(r"[a-z_]{1,20}", stato) else "non detto"
            print(f"- invio {bid} ({nome}): " + ("programmato e non ancora spedito" if stato in ("scheduled", "sending") else "non risulta spedito")
                  + f" (stato {detto}): non si tocca, e la sua etichetta resta finché non è partito. Rilancia prova-pulizia dopo")
    for t in leggi_tutto(f"/tags?per_page={PER_PAGINA}", "tags"):
        nome = str(t.get("name") or "")
        if not NOME_PROVA.fullmatch(nome):
            continue
        if not intero(t.get("id")):
            male.append(f"etichetta {nome}: senza id nella risposta di Kit, non toccata")
        elif nome in occupate:
            print(f"- etichetta {nome}: resta (il suo invio è ancora in Kit e non è spedito)")
        else:
            stato, _ = chiama("DELETE", f"/tags/{t['id']}")
            if stato in (200, 204):
                tolti += 1
                print(f"- etichetta {nome}: tolta (chi l'aveva resta iscritto, perde solo questa etichetta)")
            else:
                male.append(f"etichetta {nome}: Kit non l'ha tolta (HTTP {stato})")
    if male:
        raise Fermo("; ".join(male))
    print(f"\nOK: pulizia fatta, {tolti} tra bozze ed etichette di prova tolt{'a' if tolti == 1 else 'e'}"
          + ("" if tolti else " (non c'era nulla da togliere)"))
    return tolti


def scaduto():
    """Che cosa dire quando arriva il limite netto del passo: se un invio è programmato e non verificato, URGENTE."""
    if _in_volo:
        bid, invio = _in_volo
        return (f"URGENTE: tempo del passo scaduto con l'invio {bid} programmato e non verificato né tolto: può partire con "
                f"destinatari sbagliati, FERMALO A MANO in Kit prima delle {invio.astimezone(ROMA):%H:%M}")
    return ("tempo del passo scaduto con una chiamata a Kit ancora in corso: nessun invio programmato; guarda in Kit (Broadcasts) "
            "se è rimasta una bozza del benvenuto da togliere")


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else "controlla"
    try:
        sys.stdout.reconfigure(line_buffering=True)      # ogni riga esce subito: se il passo viene chiuso, ciò che è stato fatto è scritto
    except AttributeError:
        pass
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
    if modo == "impronta":
        indirizzo = "".join(sys.stdin.readline().split())
        if indirizzo.count("@") != 1 or indirizzo.startswith("@") or indirizzo.endswith("@"):
            sys.exit("Impronta: sullo standard input serve un indirizzo (non lo ripeto qui)")
        print(impronta_di(indirizzo))
        return
    di_prova_ = modo in ("bozza", "prova", "pulizia")
    if modo not in ("piano", "invia", "bozza", "prova", "pulizia") or len(sys.argv) != (3 if modo in ("bozza", "prova") else 2):
        sys.exit(__doc__)
    a_capo, uscita = ("\n" if di_prova_ else ""), 1
    avvia_scadenza()
    try:
        try:
            if modo == "bozza":
                bozza(sys.argv[2])
            elif modo == "prova":
                prova(sys.argv[2])
            elif modo == "pulizia":
                pulisci()
            else:
                giro(esegui=modo == "invia")
            uscita = 0
        finally:
            spegni_allarme()
    except Rimando as e:
        uscita = 0
        print(f"Benvenuto: rimandato al prossimo giro, nessuno è stato segnato - {e}")
    except (Fermo, Avviso) as e:
        print(f"{a_capo}DA GUARDARE: benvenuto - {e}")
    except Scaduto:
        print(f"{a_capo}DA GUARDARE: benvenuto - {scaduto()}")
    except Exception as e:  # noqa: BLE001
        # mai un tracciato né il testo dell'errore: dentro può esserci una risposta di Kit, cioè indirizzi. Solo dove
        dove = traceback.extract_tb(e.__traceback__)[-1]
        print(f"{a_capo}DA GUARDARE: benvenuto - errore imprevisto ({type(e).__name__}, {Path(dove.filename).name} riga {dove.lineno}): "
              "il giro si è fermato a metà, guarda in Kit (Broadcasts) se è rimasto un invio del benvenuto da togliere")
    if uscita and modo in ("bozza", "prova"):
        print(f"\n{RESTA_FERMO}")
    print(f"{a_capo}{registro_kit()}")
    ferma_scadenza()
    sys.exit(uscita)


if __name__ == "__main__":
    main()
