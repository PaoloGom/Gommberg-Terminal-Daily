#!/usr/bin/env python3
"""La mail di benvenuto ai nuovi iscritti (G-43): la guida "Come si legge il Gommberg", una volta sola per iscritto.

Perché qui e non in Kit: il piano gratuito di Kit non ha automazioni né sequenze (verificato il 25/11/2026,
redazione/collaudi/2026-11-25/g43/ricerca.md). Allora la fa la macchina, a zero token: ogni sera, nel giro di
.github/workflows/dem.yml (passo "Benvenuto", dopo le mail straordinarie), questo script
  1. legge da Kit gli iscritti ATTIVI (cioè confermati) arrivati negli ultimi FINESTRA_GIORNI giorni e non prima di
     ACCESO_DAL (vedi sotto);
  2. toglie chi ha già l'etichetta (tag) "gommberg-benvenuto": è il segno "benvenuto già fatto", e per questo nessuno
     riceve la guida due volte, anche con due giri nello stesso giorno;
  3. se un giro di prima ha lasciato un gruppo in sospeso (etichetta data, invio non programmato) riprende quello;
     altrimenti prende in carico quanti iscritti stanno nel tempo del passo (vedi "tempo"), chi aspetta da più tempo per
     primo, e dà loro l'etichetta del gruppo di stasera ("gommberg-benvenuto-AAAA-MM-GG-HHMM"); gli altri non li tocca;
  4. aspetta che il gruppo in Kit abbia dentro esattamente quegli iscritti (vedi "il ritardo di Kit");
  5. crea l'invio in BOZZA solo per il gruppo (subscriber_filter sull'etichetta del gruppo, modello "Gommberg cornice")
     e lo RILEGGE da Kit (GET, indipendente dalla risposta alla creazione);
  6. solo ora dà a quegli iscritti l'etichetta permanente, e subito dopo programma l'invio tra ATTESA_MINUTI minuti;
     poi lo rilegge di nuovo. Se qualcosa non torna l'invio si toglie; se non si riesce a toglierlo si riporta in bozza
     (send_at null); se non riesce nemmeno quello, il messaggio dice URGENTE e dem.yml apre una segnalazione apposta.
     Quando l'invio di sicuro non parte, l'etichetta permanente si toglie a chi l'ha avuta da questo giro: torna
     candidato per il giro dopo.
Testo: redazione/benvenuto_mail.html (approvato da Paolo il 25/11/2026). Chiamate a Kit: newsletter.kit, una sola logica
(qui sopra c'è solo uno strato che trasforma ogni risposta illeggibile in "esito incerto" e tiene il registro delle
chiamate del giro); l'elenco degli invii è newsletter.leggi_invii, la lettura leggera a pagine delle edizioni.

L'accensione (ACCESO_DAL, un posto solo): ricevono il benvenuto solo gli iscritti arrivati da quel giorno in poi. I
lettori di prima (iscritti da settimane) e chi si è iscritto nei giorni prima del rilascio NON lo ricevono al primo
giro. La finestra di FINESTRA_GIORNI (7) giorni serve a chi conferma giorni dopo l'iscrizione (Kit dà la data di
iscrizione, non di conferma) e a chi perde qualche giro: i doppioni li impedisce l'etichetta permanente.

Il ritardo di Kit (dichiarato da Kit: developers.kit.com/api-reference/eventual-consistency). Gli elenchi (gli iscritti,
gli iscritti di un'etichetta, i filtri) sono aggiornati in ritardo rispetto alle scritture: di solito 30 secondi, fino a
5 minuti; misurato qui il 28/11/2026 sull'elenco di un'etichetta appena data: circa 150 secondi, e un'altra volta più
di 119. Le scritture e le letture per id no (verificato lo stesso giorno): la risposta di Kit a una scrittura fa fede.
Quindi:
  - che l'etichetta sia stata data lo dice la risposta alla scrittura (201 con lo stesso iscritto), non l'elenco;
  - MAI programmare prima che l'elenco del gruppo sia completo: Kit sceglie i destinatari di un invio dall'elenco
    dell'etichetta, e un invio programmato su un elenco che non ha ancora dentro tutti partirebbe senza qualcuno;
  - l'elenco del gruppo si rilegge ogni PAUSA_GRUPPO secondi finché il passo lascia tempo (con pochi iscritti più di
    quattro minuti; ATTESA_GRUPPO, 180 secondi, è il tempo che il giro tiene comunque da parte per questa attesa quando
    decide quanti iscritti servire): finché ha meno iscritti degli attesi è ritardo, e si aspetta; un iscritto che non
    è tra gli attesi non è ritardo, è un errore, e ferma subito. L'elenco si legge in due modi (con status=all e con lo
    stato predefinito, i soli attivi) e il gruppo è l'unione dei due; in più, per dire i fatti nel riepilogo, l'etichetta
    si legge per id dalla parte dell'iscritto (GET /subscribers/{id}/tags);
  - il giro in due tempi: se quando il tempo finisce l'elenco non è ancora completo, nessun invio, e il gruppo resta
    IN SOSPESO in Kit: l'etichetta del gruppo è data, nessuno ha l'etichetta permanente, nessun invio è programmato.
    Lo stato sta tutto in Kit. Il giro dopo (la sera dopo, o rilanciando dopo mezz'ora) lo riprende: stesse persone,
    nessun gruppo nuovo, e a quel punto l'elenco è completo. Chi si è iscritto nel frattempo va al giro ancora dopo.
    Vale per ogni giro fermato o interrotto prima della programmazione. Un gruppo in sospeso che non si può più
    riprendere (vuoto, o con dentro qualcuno che non è più da salutare, per esempio già segnato da un giro morto a
    metà) si toglie, e chi resta da salutare rientra in un gruppo nuovo. Il giro rimandato esce con 0 e lo scrive nel
    registro; se qualcuno aspetta da più di ATTESA_AVVISO giorni esce con 1. Nella prova dal vivo è un fermo;
  - mai due giri che scrivono a meno di ELENCHI_SICURI (30) minuti l'uno dall'altro: l'ora di nascita di un gruppo è
    nel suo nome, e finché un gruppo è più giovane gli elenchi di Kit possono non dire ancora che cosa ha fatto il suo
    giro. Il secondo giro non scrive nulla e lo dice;
  - l'invio parte ATTESA_MINUTI (10) minuti dopo l'avvio del giro: dopo la fine del passo.

L'ordine, e perché (mai due mail allo stesso iscritto, e nessuno segnato senza mail finché si può evitare):
  - l'etichetta permanente PRIMA della programmazione, ma DOPO la bozza riletta: è l'ultima cosa prima di programmare.
    Un giro interrotto o fermato in qualunque punto prima (etichette del gruppo, attesa del gruppo, bozza) non ha segnato
    nessuno: tutti tornano candidati al giro dopo, in un gruppo nuovo, e ricevono la guida una volta.
  - "mai due mail" non dipende da nulla che possa mancare: un invio parte solo dopo che Kit ha risposto 201 ("data
    adesso") all'etichetta permanente di ognuno dei suoi destinatari. Un 200 ("l'aveva già") non prova mai che l'abbia
    data questo giro, nemmeno dopo un tentativo senza risposta: può averla data un altro giro pochi minuti prima, che
    gli elenchi di Kit non mostrano ancora. Allora il giro si ritira: toglie la bozza e de-segna chi aveva segnato lui.
    (La documentazione di Kit non dice che cosa significhi la data dell'etichetta in una risposta 200, né che la
    lettura per id delle etichette di un iscritto sia subito coerente: non c'è un modo certo di distinguere, quindi
    non si distingue.) Per questo l'etichetta permanente resta prima della programmazione: darla dopo lascerebbe, se
    il giro muore in quei secondi, un invio che parte verso iscritti non segnati, cioè due mail la sera dopo.
  - "nessuno segnato senza mail": la programmazione si ritenta su un guasto momentaneo, ma solo se la rilettura per id
    mostra che l'invio non è programmato; e se alla fine l'invio non parte (tolto, o riportato in bozza), l'etichetta
    permanente si toglie a chi l'ha avuta da questo giro. Resta segnato senza mail solo: chi è stato segnato da un giro
    che muore (macchina spenta, passo chiuso) nei pochi secondi tra la prima etichetta permanente e la programmazione
    riletta; chi Kit non lascia de-segnare; e l'iscritto la cui etichetta è "dubbia" (Kit l'ha data ma la risposta si
    è persa). Riceve comunque l'edizione, e la pagina benvenuto.html gli ha già detto tutto.
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
  - tempo. Lo script si dà PASSO (510) secondi, 30 meno del passo di dem.yml (9 minuti), e ogni chiamata a Kit sta nel
    tempo rimasto: si arrende da sé, con il suo messaggio, prima che GitHub chiuda il passo (e a 525 secondi un allarme
    lo ferma comunque: se in quel momento un invio è programmato e non verificato, il messaggio è URGENTE). Gli ultimi
    RISERVA (210) secondi sono della programmazione: la PUT parte solo se restano, il tempo di rileggere e, se serve,
    togliere l'invio. I primi LAVORO (300) sono per tutto il resto. Il giro prende in carico solo gli iscritti che
    stanno in quel tempo: ogni iscritto costa due chiamate, e una chiamata è stimata il doppio della media misurata
    sulle letture dello stesso giro (mai meno di un secondo; misurato: un quarto di secondo); tolti i 180 secondi
    dell'attesa del gruppo e il margine, con Kit sotto il mezzo secondo a chiamata sono circa 40 iscritti a sera, con
    Kit a un secondo circa 18, a 2 secondi circa 7. Gli altri restano candidati per la sera dopo, senza nessuna
    etichetta. E l'etichetta permanente non si dà a nessuno se non resta il tempo per darla a tutti i presi in carico
    e programmare.
  - seconda difesa: è "già salutato" anche chi non ha l'etichetta permanente ma sta in un gruppo il cui invio risulta
    programmato o spedito.

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
       python3 redazione/benvenuto.py prova impronta:X bozza:N
                                                         prova dal vivo, passo 3: programma tra ATTESA_MINUTI minuti la
                                                         bozza di prova numero N (lo scrive "bozza"), letta per id: solo se
                                                         è una bozza con il filtro su un gruppo di prova con dentro lui
                                                         solo; poi rilegge l'invio e riconta il gruppo
       python3 redazione/benvenuto.py pulizia [bozza:N]  toglie da Kit ciò che le prove lasciano: le bozze di prova non
                                                         programmate e le etichette dei gruppi di prova più vecchie di 30
                                                         minuti. Mai un invio programmato o spedito, mai un'etichetta che
                                                         non sia di prova. bozza:N: guarda anche quell'invio, letto per id

L'iscritto di prova si indica SOLO con l'impronta, mai con l'indirizzo: il repository è pubblico e chiunque legge gli
input e i registri dei giri. Lo script legge da Kit gli iscritti attivi e sceglie quello la cui impronta coincide; zero o
più di uno: errore, e non fa nulla. Non stampa mai un indirizzo né un dato letto da Kit che non abbia prima controllato
(numeri, nomi di gruppi che ha creato lui): nemmeno negli errori, e mai un tracciato. L'impronta non è un segreto: chi
conosce o indovina l'indirizzo la può ricalcolare; serve a non scriverlo in chiaro.

Che cosa dice ogni giro, senza indirizzi: i passi fatti; a ogni rilettura del gruppo quanti elementi ha restituito Kit
e quanti di questi sono tra gli attesi, per l'elenco con status=all e per quello con lo stato predefinito; e, in fondo,
il registro delle chiamate a Kit con il codice HTTP di ognuna (metodo, percorso senza l'id dell'iscritto, e i nomi dei
parametri: il valore solo per stati, date e formati; 0 = nessuna risposta leggibile). La pulizia, prima di togliere,
dice per ogni etichetta di prova quanti iscritti Kit le attribuisce in quel momento.

LA PROVA DAL VIVO, prima di accendere. Si fa da GitHub, dove sta la chiave di Kit (il segreto KIT_API_KEY: non la legge
nessuna chat e nessun PC), lanciando a mano dem.yml dal ramo da provare. I modi "prova-" fanno girare solo questo
script, mai dem.py e mai "invia"; l'esito si legge nel riepilogo del giro.
  0. l'impronta, in una sessione (l'indirizzo non finisce in nessun file):
       X=$(printf '%s' 'INDIRIZZO' | python3 redazione/benvenuto.py impronta)
  1. gh workflow run dem.yml --ref RAMO -f modo=prova-piano
       sole letture: quanti iscritti riceverebbero il benvenuto stasera
  2. gh workflow run dem.yml --ref RAMO -f modo=prova-bozza -f impronta="$X"
       il riepilogo deve dire: gruppo di prova con 1 iscritto, bozza riletta con il filtro sul solo gruppo. Il giro può
       durare fino a quattro minuti: aspetta che Kit aggiorni l'elenco del gruppo. Poi in Kit, Broadcasts, la bozza
       gommberg-benvenuto-prova-...: i destinatari devono essere 1. Se non è 1: lancia prova-pulizia e fermati.
       L'ultima riga dice il numero della bozza (N)
  3. gh workflow run dem.yml --ref RAMO -f modo=prova-invio -f impronta="$X" -f bozza=N
       tra le 8:00 e le 8:20 o tra le 10:30 e le 20:49 (le stesse fasce del giro); la mail arriva al solo iscritto di
       prova dopo ATTESA_MINUTI minuti. L'attesa è la stessa del giro vero e supera la durata del passo: un invio
       registrato male si toglie sempre prima che parta
  4. gh workflow run dem.yml --ref RAMO -f modo=prova-pulizia [-f bozza=N]
       dopo che la mail è arrivata (o dopo una prova fermata): toglie le bozze di prova non programmate e le etichette
       dei gruppi di prova, e dice che cosa ha tolto. Finché l'invio di prova è programmato e non ancora partito non
       tocca né lui né la sua etichetta, e non tocca un'etichetta nata da meno di 30 minuti: si rilancia dopo
Che cosa resta in Kit dopo la prova, finché non si lancia prova-pulizia: l'etichetta del gruppo
gommberg-benvenuto-prova-AAAA-MM-GG-HHMM sull'iscritto di prova, una per ogni bozza tentata; l'invio di prova tra i
Broadcasts, spedito a 1 (quello resta nello storico anche dopo la pulizia), o ancora in bozza se ci si è fermati al
passo 2. La prova NON dà l'etichetta permanente "gommberg-benvenuto": l'iscritto di prova resta com'era. Se è un lettore
di prima dell'accensione il benvenuto vero non lo riceve mai (non è nella finestra); se invece si è iscritto da
ACCESO_DAL in poi e da meno di 7 giorni, il giro della sera gli manda anche quello vero.
Gli altri resti in Kit (non li tocca nessuno, si tolgono a mano se danno fastidio): le etichette dei gruppi della sera già
spediti, e quelle dei gruppi in sospeso più vecchi di 7 giorni.
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
BOZZA = re.compile(r"bozza:([0-9]{1,20})")                                  # come si indica la bozza di prova: il suo id in Kit
NOME_SERA = re.compile(re.escape(FATTO) + r"-\d{4}-\d{2}-\d{2}-\d{4}")       # il nome intero di un gruppo del giro della sera
ELENCHI_SICURI = 30                # minuti dopo i quali gli elenchi di Kit dicono di sicuro ciò che un giro ha fatto (Kit
                                   # dichiara un ritardo fino a 5). Prima: un altro giro non scrive nulla, e la pulizia non
                                   # tocca un'etichetta (l'ora di nascita di un gruppo è nel suo nome)
ACCESO_DAL = "2026-11-28"          # accensione (ora di Roma, dalla mezzanotte): solo chi si iscrive da qui riceve il benvenuto
FINESTRA_GIORNI = 7                # iscritti arrivati negli ultimi 7 giorni (chi conferma tardi, giri persi)
ATTESA_AVVISO = 3                  # chi riceve il benvenuto oltre 3 giorni dopo l'iscrizione: avviso (giri saltati?)
MAX_NUOVI = 100                    # oltre, qualcosa non va (un filtro ignorato da Kit?): nessun invio
ATTESA_MINUTI = 10                 # l'invio parte dopo: il tempo di toglierlo se Kit lo registra male (più di PASSO,
                                   # così la pulizia finisce sempre prima della partenza). Vale anche per la prova
FASCIA = (75, 45)                  # minuti prima e dopo l'uscita in cui non si spedisce
LETTURE = 3                        # tentativi per ogni lettura su un guasto momentaneo (429, 5xx, rete)
ATTESA_LETTURE = 10                # secondi tra un tentativo e l'altro (il collaudo la azzera)
PASSO = 510                        # secondi che lo script si dà, contati dall'avvio: 30 meno del passo di dem.yml
                                   # (timeout-minutes: 9), così si arrende da sé, con il suo messaggio, prima che GitHub lo chiuda
ALLARME = PASSO + 15               # limite netto (SIGALRM): una chiamata appesa oltre il suo tempo non porta il passo alla
                                   # chiusura di GitHub senza che lo script abbia detto com'è finita
TEMPO_CHIAMATA = 30                # tetto di una chiamata a Kit (il timeout di newsletter.kit, che si accorcia col tempo rimasto)
RISERVA = 7 * TEMPO_CHIAMATA       # programmazione + 2 riletture + pulizia (2 DELETE, 1 PUT in bozza, 1 rilettura):
                                   # la PUT parte solo se nel passo restano questi secondi, così la pulizia di un
                                   # invio sbagliato finisce sempre prima della scadenza del passo
RISERVA_GRUPPO = 6 * TEMPO_CHIAMATA  # prova: ricontare il gruppo dopo la programmazione (2 letture) + pulizia (4 chiamate)
LAVORO = PASSO - RISERVA           # secondi per tutto ciò che viene prima della programmazione (letture, etichette,
                                   # attesa del gruppo, bozza): 300
ATTESA_GRUPPO = 180                # Kit aggiorna gli elenchi con ritardo, e lo dichiara (di solito 30 secondi, fino a 5
                                   # minuti; misurato il 28/11/2026 su un'etichetta appena data: circa 150 secondi, e
                                   # un'altra volta più di 119). È il solo parametro dell'attesa: i secondi che il giro
                                   # tiene da parte per aspettare l'elenco del gruppo quando decide quanti iscritti
                                   # servire. Poi l'attesa vera dura finché il passo lascia tempo (con pochi iscritti,
                                   # più di quattro minuti); e se non basta il gruppo resta in sospeso per il giro dopo
PAUSA_GRUPPO = 5                   # secondi tra una rilettura del gruppo e l'altra
STIMA_MINIMA, STIMA_FATTORE = 1.0, 2   # il costo stimato di una chiamata: il doppio della media misurata in questo giro,
                                   # mai meno di un secondo. Serve a decidere quanti iscritti si riesce a servire
MARGINE = 35                       # sotto questi secondi di lavoro rimasti non si scrive più nulla in Kit
MAX_PAGINE = 20
PER_PAGINA = 500
TRATTINI_LUNGHI = re.compile("[–—]")
VIA_ISCRITTO = re.compile(r"(/subscribers/)\d+")
# i parametri di cui il registro delle chiamate scrive anche il valore (stati, date, formati); degli altri solo il nome
IN_CHIARO = ("status", "created_after", "created_before", "tagged_after", "tagged_before", "sent_after", "sent_before",
             "per_page", "slim", "include", "include_total_count")
orologio = time.monotonic          # il collaudo lo sostituisce
pausa = time.sleep                 # il collaudo la sostituisce
_avvio = None                      # istante dell'avvio (orologio), o None se nessuna scadenza è partita
_chiamate = []                     # le chiamate a Kit di questo giro: (metodo, percorso, codice HTTP, secondi)
_in_volo = None                    # (id, ora) di un invio programmato e non ancora verificato né tolto


class Fermo(Exception):
    """Il giro si ferma senza inviare nulla. Il messaggio dice perché e che cosa è già stato fatto."""


class Ritardo(Fermo):
    """L'elenco di un gruppo in Kit non è ancora quello atteso dopo ATTESA_GRUPPO secondi (Kit lo aggiorna con ritardo)."""


class NonParte(Fermo):
    """La programmazione non è riuscita e l'invio di sicuro non parte: tolto, o riportato in bozza, o mai programmato."""


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


def via_di(percorso):
    """Il percorso come va nel registro: senza l'id dell'iscritto, e dei parametri il nome; il valore solo per stati,
    date e formati (IN_CHIARO), mai per un parametro che può portare un dato personale o un cursore."""
    via, _, coda = str(percorso).partition("?")
    nomi = []
    for pezzo in coda.split("&") if coda else []:
        nome, _, valore = pezzo.partition("=")
        nomi.append(f"{nome}={valore}" if nome in IN_CHIARO and re.fullmatch(r"[A-Za-z0-9_,:.-]{1,40}", valore) else nome)
    return VIA_ISCRITTO.sub(r"\1*", via) + ("?" + "&".join(nomi) if nomi else "")


def annota(metodo, percorso, stato, t0):
    _chiamate.append((metodo, via_di(percorso), intero(stato) or 0, max(0.0, orologio() - t0)))


def stima_chiamata():
    """Il costo prudente di una chiamata a Kit, in secondi, misurato su quelle già fatte in questo giro."""
    media = sum(c[3] for c in _chiamate) / len(_chiamate) if _chiamate else 0.0
    return max(STIMA_MINIMA, STIMA_FATTORE * media)


def registro_kit():
    """Che cosa ha risposto Kit, in una riga: metodo, percorso con i suoi parametri, codice HTTP (0 = nessuna risposta
    leggibile). Le chiamate uguali sono contate una volta, nell'ordine in cui sono comparse. Mai un dato degli iscritti."""
    if not _chiamate:
        return "Kit: nessuna chiamata"
    conti, tot = {}, sum(c[3] for c in _chiamate)
    for metodo, via, stato, _ in _chiamate:
        conti[f"{metodo} {via} {stato}"] = conti.get(f"{metodo} {via} {stato}", 0) + 1
    voci = list(conti.items())
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


def iscritti_con(tag_id, dal=None, pulizia=False, tentativi=LETTURE, pagine=MAX_PAGINE, stato="all"):
    """Gli id degli iscritti che hanno l'etichetta, letti dalla parte dell'etichetta: di ogni stato (status=all) o, con
    stato=None, come li dà Kit senza dirgli nulla (lo stato predefinito: i soli attivi). `dal`: solo gli iscritti
    arrivati da quel giorno (lo usa il giro per l'etichetta permanente, mai il conto di un gruppo)."""
    parametri = (f"status={stato}&" if stato else "") + f"per_page={PER_PAGINA}" + (f"&created_after={dal}" if dal else "")
    lista = leggi_tutto(f"/tags/{tag_id}/subscribers?{parametri}", "subscribers", pulizia, tentativi, pagine)
    ids = {intero(s.get("id")) for s in lista}
    if None in ids:
        raise Fermo(f"risposta di Kit fuori forma a GET /tags/{tag_id}/subscribers (iscritto senza id)")
    return ids


def ha_etichetta(iscritto, tag_id):
    """L'iscritto ha l'etichetta? Letto per id dalla parte dell'iscritto (GET /subscribers/{id}/tags), che non passa
    dagli elenchi in ritardo. Torna "c'è", "non c'è" o "non si legge": serve a dire i fatti nel riepilogo, non decide."""
    try:
        tags = leggi_tutto(f"/subscribers/{iscritto}/tags?per_page={PER_PAGINA}", "tags", pulizia=True, tentativi=1, pagine=2)
    except Fermo:
        return "non si legge"
    return "c'è" if any(intero(t.get("id")) == tag_id for t in tags) else "non c'è"


def gruppo_in_kit(tag_id, attesi, nome, dopo=0.0):
    """Rilegge l'elenco del gruppo finché ha dentro esattamente gli attesi, e torna ciò che ha letto ogni volta. Kit
    aggiorna gli elenchi con ritardo (lo dichiara: di solito 30 secondi, fino a 5 minuti), quindi un elenco ancora corto
    si rilegge ogni PAUSA_GRUPPO secondi finché il passo lascia tempo (tolti il margine e `dopo`, i secondi che servono
    dopo l'attesa); poi Ritardo. L'elenco si legge in due modi, con status=all e con lo stato predefinito (i soli
    attivi), e il gruppo è l'unione: gli attesi devono esserci tutti, e in nessuno dei due deve esserci un iscritto che
    non è tra gli attesi (quello non è un ritardo: fermo subito)."""
    attesi, letture, t0 = set(attesi), [], orologio()
    while True:
        tutti, attivi = iscritti_con(tag_id), iscritti_con(tag_id, stato=None)
        letture.append((len(tutti), len(tutti & attesi), len(attivi), len(attivi & attesi)))
        visti = tutti | attivi
        if visti == attesi:
            return letture
        letti = conti_letti(letture)
        if visti - attesi:
            raise Fermo(f"l'etichetta {nome} in Kit ha {len(visti)} iscritti invece di {len(attesi)}, e {len(visti - attesi)} non "
                        f"glieli ho dati io ({letti}): nessun invio")
        resta = rimasto() - MARGINE - dopo
        if resta == float("inf"):          # nessuna scadenza partita: vale il solo tempo dichiarato
            resta = ATTESA_GRUPPO - (orologio() - t0)
        if resta < PAUSA_GRUPPO:
            per_id = ha_etichetta(min(attesi), tag_id) if attesi else "non si legge"
            raise Ritardo(f"l'etichetta {nome} in Kit ha {len(visti)} iscritti invece di {len(attesi)} dopo {len(letture)} riletture in "
                          f"{orologio() - t0:.0f} secondi ({letti}); letta per id dalla parte di un iscritto atteso, l'etichetta "
                          f"{per_id}. Kit dichiara che gli elenchi arrivano in ritardo, di solito 30 secondi e fino a 5 minuti; nessun invio")
        pausa(PAUSA_GRUPPO)


def conti_letti(letture):
    """Ciò che Kit ha restituito a ogni rilettura del gruppo, in breve e senza dati degli iscritti: per l'elenco con
    status=all e per quello con lo stato predefinito, quanti elementi e quanti di questi sono tra gli attesi."""
    voci = []
    for tutti, tutti_attesi, attivi, attivi_attesi in letture:
        voce = (f"con status=all {tutti} element{'o' if tutti == 1 else 'i'} di cui {tutti_attesi} tra gli attesi, "
                f"con lo stato predefinito {attivi} di cui {attivi_attesi} tra gli attesi")
        if voci and voci[-1][0] == voce:
            voci[-1][1] += 1
        else:
            voci.append([voce, 1])
    return "elenchi letti: " + "; poi ".join(v + (f" (x{n})" if n > 1 else "") for v, n in voci)


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


def segna(tag_id, iscritto):
    """L'etichetta permanente a un iscritto, e come è andata:
      "data"    Kit ha risposto 201 con lo stesso iscritto: l'ha data questo giro, ed è la sola risposta che lo prova;
      "c'era"   200 al primo colpo: l'aveva già, data da un altro giro (gli elenchi di Kit non la mostravano ancora);
      "dubbia"  200 dopo un tentativo senza risposta, o 201 che parla di un altro iscritto: l'etichetta c'è, ma non si
                può sapere se l'ha data questo giro o un altro. Non vale mai come data;
      "no"      Kit non l'ha data.
    Si ritenta solo un guasto momentaneo. Mai due mail: si spedisce solo a chi ha "data"."""
    for tentativo in range(1, LETTURE + 1):
        stato, corpo = chiama("POST", f"/tags/{tag_id}/subscribers/{iscritto}", {})
        if stato == 201:
            chi = corpo.get("subscriber") if isinstance(corpo, dict) else None
            return "data" if isinstance(chi, dict) and intero(chi.get("id")) == iscritto else "dubbia"
        if stato == 200:
            return "c'era" if tentativo == 1 else "dubbia"
        if not (stato == 0 or stato == 429 or stato >= 500) or tentativo == LETTURE:
            return "no"
        pausa(max(0, min(ATTESA_LETTURE, rimasto())))


def desegna(tag_id, iscritti):
    """Toglie l'etichetta permanente agli iscritti a cui l'ha data QUESTO giro (201), quando l'invio non parte: tornano
    candidati per il giro dopo invece di restare segnati senza mail. Lavora anche a tempo di lavoro scaduto, finché il
    passo lascia una chiamata. Torna quanti non è riuscito a togliere."""
    restano = 0
    for i in iscritti:
        tolta = False
        for _ in range(2):
            if resta_nel_passo() < TEMPO_CHIAMATA + 5:
                break
            stato, _ = kit_sicuro("DELETE", f"/tags/{tag_id}/subscribers/{i}")
            if stato in (200, 204):
                tolta = True
            if not (stato == 0 or stato == 429 or stato >= 500):
                break
        restano += 0 if tolta else 1
    return restano


def iscritti_n(n):
    return f"{n} iscritt{'o' if n == 1 else 'i'}"


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


def togli_e_di(bid, dati, invio=None):
    """Toglie (o riporta in bozza) e dice come è andata: ("tolto" | "in bozza" | "", parole per il registro). `invio` è
    l'ora per cui l'invio può essere stato programmato; None = è una bozza mai programmata, che non parte da sola: se Kit
    non la lascia togliere va tolta a mano, ma non è urgente."""
    come = togli(bid, dati)
    if come == "tolto":
        return come, f"invio {bid} tolto"
    if come == "in bozza":
        return come, f"invio {bid} NON tolto ma riportato in bozza (non parte): toglilo a mano in Kit"
    if invio is None:
        return come, f"bozza {bid} NON tolta (Kit non risponde): non è programmata e non parte da sola, toglila a mano in Kit"
    return come, (f"URGENTE: invio {bid} né tolto né riportato in bozza, può partire con destinatari sbagliati: FERMALO A MANO in Kit "
                  f"prima delle {invio.astimezone(ROMA):%H:%M}")


def esito_tolto(bid, dati, invio=None):
    return togli_e_di(bid, dati, invio)[1]


ELENCO_INVII = f"/broadcasts?per_page={nl.PER_PAGINA}&slim=true&after"      # come lo chiede newsletter.leggi_invii, pagina per pagina


def elenco_invii():
    """Tutti gli invii di Kit nella forma leggera (id, description, send_at, status: senza contenuto, filtro e modello).
    È newsletter.leggi_invii, la lettura a pagine che newsletter.py usa per le edizioni (G-69): una sola logica. Se
    l'elenco non si legge per intero: fermo ("non so" non diventa mai "non c'è")."""
    t0 = orologio()
    try:
        invii = nl.leggi_invii(LETTURE, ATTESA_LETTURE, rigoroso=True)
    except nl.ElencoNonLeggibile as e:
        annota("GET", ELENCO_INVII, e.stato, t0)
        raise Fermo(f"elenco degli invii di Kit non leggibile (HTTP {intero(e.stato) or 0}"
                    + (", troppo lungo" if e.troppo_lungo else "") + (f", {e.motivo}" if e.motivo else "") + ")")
    except Exception as e:  # noqa: BLE001
        annota("GET", ELENCO_INVII, 0, t0)
        raise Fermo(f"elenco degli invii di Kit non leggibile ({type(e).__name__})")
    annota("GET", ELENCO_INVII, 200, t0)
    return invii


def invii_con(descrizione):
    """Gli id degli invii in Kit con quella description (per chiarire una creazione dall'esito incerto)."""
    return [b["id"] for b in elenco_invii() if str(b.get("description") or "") == descrizione and intero(b.get("id"))]


def dati_invio(gruppo_id, descrizione, modello):
    oggetto, anteprima, corpo = componi()
    return {"subject": oggetto, "preview_text": anteprima, "content": corpo, "description": descrizione, "public": False,
            "published_at": datetime.now(UTC).isoformat(timespec="seconds"), "send_at": None, "email_template_id": modello,
            "subscriber_filter": [{"all": [{"type": "tag", "ids": [gruppo_id]}], "any": None, "none": None}]}


def crea_bozza(gruppo_id, nome_gruppo, modello, attesi, senza, dopo=0.0):
    """Crea la bozza per il gruppo (mai ritentata) e la rilegge. Torna (id, dati) solo se Kit, riletto, ha la bozza con
    il filtro sul solo gruppo; altrimenti la toglie e si ferma. Prima aspetta che l'elenco del gruppo in Kit abbia dentro
    esattamente gli attesi (gruppo_in_kit), finché restano i secondi che servono dopo (`dopo`). senza: che cosa è già
    stato fatto, per i messaggi. Torna anche ciò che ha letto degli elenchi."""
    dati = dati_invio(gruppo_id, nome_gruppo, modello)
    try:
        conti = gruppo_in_kit(gruppo_id, attesi, nome_gruppo, dopo)    # ultimo controllo: nel gruppo i soli voluti
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


def programma(bid, gruppo_id, dati, invio):
    """Programma la bozza (già verificata) e la rilegge per id: qualunque risposta alla PUT (anche nessuna) si chiarisce
    con la rilettura. Un guasto momentaneo (nessuna risposta, 429, 5xx) si ritenta, ma solo se la rilettura mostra che
    l'invio è ancora la bozza giusta e NON è programmato, e solo se nel passo resta la riserva. Se alla fine non è
    esattamente come voluto si toglie (o si riporta in bozza): NonParte se di sicuro non parte, altrimenti Fermo con
    URGENTE."""
    global _in_volo
    voluti = dict(dati, send_at=invio.astimezone(UTC).isoformat(timespec="seconds"))
    stato, riletta, tentativo = None, None, 0
    while True:
        if resta_nel_passo() < RISERVA:      # non c'è più il tempo per rimediare a una programmazione sbagliata
            come, testo = togli_e_di(bid, dati, invio if tentativo else None)
            raise (NonParte if come or not tentativo else Fermo)(f"tempo del passo insufficiente per programmare in sicurezza: {testo}, nessun invio")
        tentativo += 1
        _in_volo = (bid, invio)              # da qui l'invio può partire: se il passo scade prima della verifica, URGENTE
        stato, risposta = kit_sicuro("PUT", f"/broadcasts/{bid}", voluti)
        riletta = rileggi(bid)
        risposta_b = broadcast_di(risposta)
        # la risposta conta solo se si legge: una risposta illeggibile (0, o 200 senza l'invio) la chiarisce la rilettura;
        # un rifiuto (4xx, 5xx) o una risposta leggibile diversa dal voluto bastano per non fidarsi
        risposta_ok = stato == 0 or (stato == 200 and (risposta_b is None or com_e(risposta_b, gruppo_id, invio)))
        if com_e(riletta, gruppo_id, invio) and risposta_ok:
            _in_volo = None
            return tentativo
        if not ((stato == 0 or stato == 429 or stato >= 500) and com_e(riletta, gruppo_id, None) and tentativo < LETTURE):
            break
        pausa(max(0, min(ATTESA_LETTURE, resta_nel_passo() - RISERVA)))
    come, testo = togli_e_di(bid, voluti, invio)
    raise (NonParte if come else Fermo)(
        f"Kit non ha programmato l'invio come voluto (HTTP {stato}, rilettura {'non leggibile' if riletta is None else 'diversa'}, "
        f"{tentativo} tentativ{'o' if tentativo == 1 else 'i'}): {testo}")


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


def nato(nome, prefisso):
    """L'ora di nascita di un gruppo, scritta nel suo nome dopo il prefisso (ora di Roma), o None."""
    try:
        return datetime.strptime(nome[len(prefisso):], "%Y-%m-%d-%H%M").replace(tzinfo=ROMA)
    except ValueError:
        return None


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
    etichette = leggi_tutto(f"/tags?per_page={PER_PAGINA}", "tags")
    fatto = next((t["id"] for t in etichette if str(t.get("name") or "").strip().lower() == FATTO and intero(t.get("id"))), None)
    # i gruppi dei giri di prima, dalla finestra in qua: lo stato del lavoro sta in Kit, nelle etichette e negli invii
    gruppi = sorted((n, str(t["name"]), t["id"]) for t in etichette if NOME_SERA.fullmatch(str(t.get("name") or "")) and intero(t.get("id"))
                    for n in [nato(str(t["name"]), FATTO + "-")] if n and n > adesso - timedelta(days=FINESTRA_GIORNI))
    invii = elenco_invii() if gruppi else []
    chiusi = {str(b.get("description")) for b in invii if b.get("send_at")}        # gruppi con l'invio programmato o spedito
    sospesi = [g for g in gruppi if g[1] not in chiusi]
    recente = next((g for g in reversed(gruppi) if g[0] > adesso - timedelta(minutes=ELENCHI_SICURI)), None)
    candidati = nuovi_iscritti(adesso)
    gia = set()
    if fatto:
        gia = iscritti_con(fatto, dal=(adesso.astimezone(UTC) - timedelta(days=FINESTRA_GIORNI + 1)).date().isoformat())
    # già salutato: ha l'etichetta permanente, o è in un gruppo il cui invio è programmato o spedito (seconda difesa)
    nuovi = sorted((s for s in candidati if s["id"] not in gia and FATTO not in s["etichette"] and not s["etichette"] & chiusi),
                   key=lambda s: (s["creato"], s["id"]))
    print(f"Benvenuto: {len(candidati)} iscritti confermati arrivati negli ultimi {FINESTRA_GIORNI} giorni (dal {ACCESO_DAL}), "
          f"{len(candidati) - len(nuovi)} già salutati, {len(nuovi)} da salutare")
    soglia = adesso.astimezone(UTC) - timedelta(days=ATTESA_AVVISO)
    in_attesa = [s for s in nuovi if s["creato"] < soglia]
    tardi = (f"{len(in_attesa)} iscritt{'o' if len(in_attesa) == 1 else 'i'} confermat{'o' if len(in_attesa) == 1 else 'i'} "
             f"aspettava{'' if len(in_attesa) == 1 else 'no'} il benvenuto da più di {ATTESA_AVVISO} giorni dall'iscrizione "
             "(giri saltati o rimandati, o conferma arrivata tardi): guarda che dem.yml parta ogni sera") if in_attesa else ""
    if tardi:
        print(f"AVVISO: {tardi}")

    def rimanda(perche):
        if tardi:
            raise Avviso(f"{tardi}. E stasera: {perche}")
        raise Rimando(perche)
    if sospesi:
        print(f"Benvenuto: {len(sospesi)} grupp{'o' if len(sospesi) == 1 else 'i'} in sospeso da un giro di prima "
              f"({', '.join(g[1] for g in sospesi)}): etichetta data, invio non programmato")
    if not nuovi and not sospesi:
        return 0
    if len(nuovi) > MAX_NUOVI:
        raise Fermo(f"{len(nuovi)} iscritti nuovi in {FINESTRA_GIORNI} giorni (oltre {MAX_NUOVI}): troppi per essere veri, nessun invio")
    if not esegui:
        print("Piano: " + (f"riprendere il gruppo in sospeso {sospesi[0][1]}" if sospesi else "etichetta del gruppo") + f" e invio alle {invio:%H:%M}"
              + ("" if sospesi else f" per {iscritti_n(len(nuovi))}")
              + (f"; ma un giro ha lavorato alle {recente[0]:%H:%M}, meno di {ELENCHI_SICURI} minuti fa: adesso non scriverebbe nulla" if recente else ""))
        return 0
    if recente:        # gli elenchi di Kit possono non dire ancora che cosa ha fatto quel giro: mai due giri che scrivono vicini
        rimanda(f"un giro del benvenuto ha lavorato alle {recente[0]:%H:%M}, meno di {ELENCHI_SICURI} minuti fa, e gli elenchi di Kit "
                "possono non mostrare ancora che cosa ha fatto: questo giro non scrive nulla. Si può rilanciare dopo le "
                f"{recente[0] + timedelta(minutes=ELENCHI_SICURI):%H:%M}")
    da_salutare = {s["id"] for s in nuovi}
    for _, nome, gruppo in sospesi:        # dal più vecchio: uno si riprende, quelli che non si possono riprendere si tolgono
        membri = iscritti_con(gruppo) | iscritti_con(gruppo, stato=None)
        bozze = [b["id"] for b in invii if str(b.get("description") or "") == nome and intero(b.get("id"))]
        if membri and membri <= da_salutare:
            for b in bozze:                # la bozza di un giro interrotto non si riusa: si toglie e si rifà
                come, detto = togli_e_di(b, None)
                if come != "tolto":
                    raise Fermo(f"del gruppo in sospeso {nome} è rimasta una bozza che Kit non toglie ({detto}): nessun invio")
            print(f"Benvenuto: riprendo il gruppo in sospeso {nome}, {iscritti_n(len(membri))}"
                  + (f"; gli altri {len(da_salutare - membri)} da salutare restano per il prossimo giro" if da_salutare - membri else ""))
            fatto = fatto or etichetta(FATTO, crea=True)
            return servi(gruppo, nome, modello, fatto, sorted(membri), invio, rimanda, tardi)
        # vuoto, o con dentro qualcuno che non è più da salutare (già segnato, non più iscritto, fuori dalla finestra): non
        # si può spedire a quel gruppo così com'è. Si toglie (chi resta da salutare rientra nel gruppo nuovo, qui sotto)
        for b in bozze:
            togli(b)
        stato, _ = chiama("DELETE", f"/tags/{gruppo}")
        if stato not in (200, 204, 404):
            raise Fermo(f"il gruppo in sospeso {nome} non si può riprendere ({iscritti_n(len(membri))}, di cui {len(membri - da_salutare)} non più "
                        f"da salutare) e Kit non lascia togliere la sua etichetta (HTTP {stato}): nessun invio")
        print(f"Benvenuto: gruppo in sospeso {nome} tolto (" + ("vuoto" if not membri else
              f"{len(membri - da_salutare)} dei suoi {len(membri)} iscritti non sono più da salutare") + ")")
    if not nuovi:
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
    fatto = fatto or etichetta(FATTO, crea=True)
    gruppo = nuovo_gruppo(nome)
    for s in presi:
        if not metti(gruppo, s["id"]):
            raise Fermo("etichetta del gruppo non data a un iscritto: nessun invio creato, nessuna etichetta permanente data; il gruppo "
                        f"{nome} resta in sospeso e lo riprende il prossimo giro")
    return servi(gruppo, nome, modello, fatto, [s["id"] for s in presi], invio, rimanda, tardi)


def servi(gruppo, nome, modello, fatto, attesi, invio, rimanda, tardi):
    """La coda del giro, per un gruppo appena etichettato o ripreso: aspetta l'elenco del gruppo, crea e rilegge la
    bozza, dà le etichette permanenti e programma. MAI programmare prima che l'elenco del gruppo sia completo: Kit
    sceglie i destinatari dall'elenco, che arriva in ritardo. Se il giro si ferma prima della programmazione il gruppo
    resta in sospeso in Kit (etichetta data, nessun invio programmato) e lo riprende il giro dopo."""
    sospeso = f"nessuna etichetta permanente data; il gruppo {nome} resta in sospeso e lo riprende il prossimo giro"
    try:
        bid, dati, conti = crea_bozza(gruppo, nome, modello, attesi, sospeso, dopo=(3 + len(attesi)) * stima_chiamata())
    except Ritardo as e:                   # nessuno è segnato: non è un errore, è Kit che non ha ancora aggiornato l'elenco
        rimanda(str(e))
    print(f"Benvenuto: gruppo {nome} di {iscritti_n(len(attesi))}, {conti_letti(conti)}")
    # la bozza c'è ed è giusta: solo ora, e solo se resta il tempo per tutte e per programmare, le etichette permanenti.
    # Vale solo l'etichetta che Kit dice di aver dato adesso (201): miei = chi è stato segnato da QUESTO giro
    miei, altrui, dubbia, guasto = [], 0, False, ""
    if rimasto() < len(attesi) * stima_chiamata() + MARGINE:
        guasto = "non resta il tempo per segnare gli iscritti e programmare l'invio"
    else:
        try:
            for i in attesi:
                come = segna(fatto, i)
                if come == "data":
                    miei.append(i)
                    continue
                if come == "c'era":
                    altrui = 1
                elif come == "dubbia":
                    dubbia = True
                    guasto = ("l'etichetta permanente di un iscritto risulta data, ma dopo un tentativo senza risposta: non si può "
                              "sapere se l'ha data questo giro o un altro, quindi a lui non si spedisce (se l'aveva segnato un altro "
                              "giro ha già la sua guida; se era questo, resta segnato senza)")
                else:
                    guasto = "Kit non ha dato l'etichetta permanente a un iscritto"
                break
        except Fermo as e:
            guasto = str(e)
    if altrui or guasto:
        come, tolta = togli_e_di(bid, dati)
        restano = desegna(fatto, miei)
        # un iscritto del gruppo ha già l'etichetta permanente (di un altro giro, o dubbia): a questo gruppo non si potrà
        # mai spedire. Si toglie la sua etichetta, così chi resta da salutare rientra in un gruppo nuovo al prossimo giro
        if altrui or dubbia:
            stato, _ = kit_sicuro("DELETE", f"/tags/{gruppo}")
            gruppo_ora = (f"gruppo {nome} tolto" if stato in (200, 204, 404)
                          else f"l'etichetta del gruppo {nome} NON si è tolta (HTTP {stato}): toglila a mano in Kit")
        else:
            stato, gruppo_ora = 204, f"il gruppo {nome} resta in sospeso e lo riprende il prossimo giro"
        miei_ora = (f"nessuno resta segnato da questo giro ({iscritti_n(len(miei))} de-segnat{'o' if len(miei) == 1 else 'i'})" if miei and not restano
                    else "nessuno è stato segnato da questo giro" if not miei
                    else f"{iscritti_n(restano)} restano segnati senza mail (Kit non ha tolto l'etichetta)")
        if altrui and not guasto and come == "tolto" and not restano and stato in (200, 204, 404):
            rimanda("un iscritto ha già l'etichetta permanente, data da un altro giro (gli elenchi di Kit non la mostravano "
                    f"ancora): questo giro si ritira senza spedire, {tolta}, {gruppo_ora}, {miei_ora}; gli altri restano candidati "
                    "per il prossimo giro")
        raise Fermo((guasto or "un iscritto ha già l'etichetta permanente, data da un altro giro") + f": {tolta}, nessun invio; {miei_ora}; {gruppo_ora}")
    try:
        tentativi = programma(bid, gruppo, dati, invio)
    except NonParte as e:                  # l'invio di sicuro non parte: chi è stato segnato torna candidato
        restano = desegna(fatto, miei)
        raise Fermo(f"{e}; " + (f"{iscritti_n(len(miei))} de-segnat{'o' if len(miei) == 1 else 'i'}, tornano candidati: il gruppo {nome} resta in sospeso e lo riprende il prossimo giro"
                                if not restano else f"{iscritti_n(restano)} restano segnati senza mail (Kit non ha tolto l'etichetta)"))
    except Fermo as e:                     # URGENTE: l'invio può partire, quindi chi è segnato resta segnato
        raise Fermo(f"{e}; {iscritti_n(len(miei))} restano segnati: se l'invio parte hanno la loro guida, se lo fermi a mano no")
    print(f"OK: benvenuto programmato (invio {bid}) alle {invio.astimezone(ROMA):%H:%M} per {iscritti_n(len(attesi))}, gruppo {nome}"
          + (f" (programmazione riuscita al tentativo {tentativi})" if tentativi > 1 else ""))
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
    """True se in Kit il gruppo ha dentro il solo iscritto di prova, riletto ora nei due modi dell'elenco (status=all e
    stato predefinito). Lettura di pulizia: anche a tempo scaduto. Un elenco che non si legge vale come no."""
    try:
        return (iscritti_con(gruppo, pulizia=True, tentativi=tentativi, pagine=1)
                | iscritti_con(gruppo, pulizia=True, tentativi=tentativi, pagine=1, stato=None)) == {chi}
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
    print(f"- letta per id dalla parte dell'iscritto di prova, l'etichetta del gruppo {ha_etichetta(chi, gruppo)}")
    bid, dati, conti = crea_bozza(gruppo, nome, modello, [chi], "nessun iscritto segnato", dopo=4 * stima_chiamata())
    print(f"- gruppo riletto da Kit prima della bozza: iscritti nel gruppo 1 ({conti_letti(conti)})")
    print(f"- bozza {bid}: creata e riletta da Kit, filtro sul solo gruppo di prova, stato bozza, non programmata")
    if not solo_lui(gruppo, chi):
        raise Fermo(f"dopo la creazione il gruppo di prova {nome} non ha dentro il solo iscritto di prova (o non si rilegge): "
                    f"{esito_tolto(bid, dati)}")
    print("- gruppo riletto dopo la bozza: iscritti nel gruppo 1")
    print(f"- {RESTA}\n")
    print(f"OK: bozza di prova {bid} pronta. In Kit (Broadcasts, {nome}) i destinatari devono essere 1: se non è 1 lancia "
          f"prova-pulizia e fermati. Poi: prova-invio con bozza={bid}")
    return bid


def di_prova(invii):
    """Gli invii di prova (description = il nome intero di un gruppo di prova), dal più vecchio al più recente."""
    return sorted((b for b in invii if NOME_PROVA.fullmatch(str(b.get("description") or "")) and intero(b.get("id"))),
                  key=lambda b: b["id"])


def prova(chi, quale, adesso=None):
    """Prova dal vivo, passo 3: programma la bozza di prova indicata per id (bozza:<id>, l'id che scrive prova-bozza), letta
    per id e non cercata nell'elenco degli invii, che Kit aggiorna in ritardo. Solo se è ancora una bozza con il filtro
    su un gruppo di prova (l'etichetta che porta il suo stesso nome) e il gruppo ha dentro il solo iscritto di prova. Dopo
    la programmazione riconta il gruppo: se non torna, o non c'è il tempo per ricontare e rimediare, l'invio si toglie."""
    global _in_volo
    adesso = (adesso or datetime.now(ROMA)).astimezone(ROMA)
    invio = adesso + timedelta(minutes=ATTESA_MINUTI)
    print("Prova del benvenuto, invio al solo iscritto di prova:")
    m = BOZZA.fullmatch(str(quale).strip().lower())
    if not m:
        raise Fermo("la bozza da programmare si indica con bozza: seguito dal suo numero (lo scrive prova-bozza nell'ultima riga): "
                    "nulla di fatto")
    bid = int(m.group(1))
    if not (orario_ammesso(adesso) and orario_ammesso(invio)):
        raise Fermo(f"fuori orario ({adesso:%H:%M}, l'invio partirebbe alle {invio:%H:%M}): si spedisce tra le {dem.ORA_DA}:00 e le "
                    f"{dem.ORA_A - 1}:59, mai nella fascia dell'edizione. Nulla di fatto: la bozza resta in Kit")
    modello = modello_cornice()
    chi = iscritto_di_prova(chi)
    print("- iscritto di prova: trovato per impronta, 1 solo iscritto attivo corrisponde")
    b = rileggi(bid)
    if b is None:
        raise Fermo(f"la bozza {bid} non si legge in Kit (non c'è, o Kit non risponde): nulla di fatto")
    nome = str(b.get("description") or "")
    try:
        gruppo = intero(b["subscriber_filter"][0]["all"][0]["ids"][0])
    except (TypeError, KeyError, IndexError):
        gruppo = None
    if not NOME_PROVA.fullmatch(nome):
        raise Fermo(f"l'invio {bid} non è una bozza di prova (non porta il nome di un gruppo di prova): non si programma")
    if b.get("send_at") or str(b.get("status") or "draft").lower() not in ("draft", ""):
        raise Fermo(f"l'invio di prova {bid} è già programmato o spedito: non si programma nulla. Per un'altra prova lancia prima "
                    "prova-bozza")
    if not gruppo or not com_e(b, gruppo, None):
        raise Fermo(f"la bozza di prova {bid}, riletta, non ha il filtro su un solo gruppo di prova: non si programma")
    if etichetta(nome) != gruppo:       # il gruppo del filtro è l'etichetta di prova che porta il nome della bozza, non un'altra
        raise Fermo(f"il filtro della bozza di prova {bid} non è sull'etichetta {nome}: non si programma")
    print(f"- bozza {bid} ({nome}): riletta da Kit per id, filtro sul solo gruppo di prova, stato bozza")
    try:
        conti = gruppo_in_kit(gruppo, {chi}, nome)
    except Fermo as e:
        raise Fermo(f"il gruppo di prova non ha dentro il solo iscritto di questa impronta ({e}): non si programma")
    print(f"- gruppo di prova: iscritti nel gruppo 1, l'iscritto di prova ({conti_letti(conti)})")
    dati = dati_invio(gruppo, nome, modello)
    tentativi = programma(bid, gruppo, dati, invio)
    print(f"- invio {bid}: programmato per le {invio:%H:%M} (ora di Roma) e riletto da Kit, filtro sul solo gruppo di prova"
          + (f" (riuscito al tentativo {tentativi})" if tentativi > 1 else ""))
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


def iscritti_di(tag_id):
    """Quanti iscritti Kit attribuisce a un'etichetta in questo momento, letti in tre modi e detti in una frase: l'elenco
    con status=all, l'elenco con lo stato predefinito, e il totale che Kit dichiara (include_total_count). Solo conti."""
    def conto(stato):
        try:
            return str(len(iscritti_con(tag_id, stato=stato)))
        except Fermo:
            return "non letto"
    stato, corpo = chiama("GET", f"/tags/{tag_id}/subscribers?status=all&include_total_count=true&per_page=1")
    pg = corpo.get("pagination") if isinstance(corpo, dict) and isinstance(corpo.get("pagination"), dict) else {}
    totale = intero(pg.get("total_count")) if intero(pg.get("total_count")) is not None else intero(corpo.get("total_count")) if isinstance(corpo, dict) else None
    return (f"Kit le attribuisce {conto('all')} iscritti con status=all, {conto(None)} con lo stato predefinito, "
            f"totale dichiarato {totale if stato == 200 and totale is not None else 'non dato'}")


def pulisci(quale=None, adesso=None):
    """Toglie da Kit ciò che le prove dal vivo lasciano: le bozze di prova NON programmate e le etichette dei gruppi di
    prova. Di prova è solo ciò che porta il nome intero di un gruppo di prova (NOME_PROVA): mai l'etichetta permanente,
    mai un gruppo o un invio del giro della sera, mai una mail straordinaria. Un invio programmato o spedito non si tocca
    mai; e finché un invio di prova è in Kit senza essere stato spedito, la sua etichetta resta (è il suo filtro). Poiché
    l'elenco degli invii di Kit può arrivare in ritardo e non mostrare ancora un invio appena creato, un'etichetta più
    giovane di ELENCHI_SICURI minuti (l'ora è nel suo nome) non si tocca; e l'invio indicato con bozza:<id> si legge per id
    anche se l'elenco non lo mostra. Chi aveva un'etichetta tolta resta iscritto: perde solo quella."""
    adesso = (adesso or datetime.now(ROMA)).astimezone(ROMA)
    print("Prova del benvenuto, pulizia (solo bozze ed etichette di prova):")
    tolti, male, occupate = 0, [], set()
    etichette = [t for t in leggi_tutto(f"/tags?per_page={PER_PAGINA}", "tags") if NOME_PROVA.fullmatch(str(t.get("name") or ""))]
    for t in etichette:                # i fatti, prima di togliere qualcosa: quanti iscritti Kit attribuisce a ogni etichetta
        if intero(t.get("id")):
            print(f"- etichetta {t['name']}, prima di toccarla: {iscritti_di(t['id'])}")
    invii = {x["id"]: str(x["description"]) for x in di_prova(elenco_invii())}
    if quale is not None:              # l'invio indicato: letto per id, che l'elenco lo mostri o no
        m = BOZZA.fullmatch(str(quale).strip().lower())
        if not m:
            raise Fermo("l'invio da guardare si indica con bozza: seguito dal suo numero: nulla di fatto")
        b = rileggi(int(m.group(1)))
        if b is None:
            print(f"- invio {m.group(1)}, indicato: in Kit non si legge (già tolto?)")
        elif NOME_PROVA.fullmatch(str(b.get("description") or "")):
            invii.setdefault(int(m.group(1)), str(b["description"]))
        else:
            male.append(f"l'invio {m.group(1)}, indicato, non è di prova: non toccato")
    for bid, nome in sorted(invii.items()):
        b = rileggi(bid)                                  # per id, nella forma intera: fa fede questa
        stato = str((b or {}).get("status") or "").lower()
        if not b or str(b.get("description") or "") != nome:
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
    for t in etichette:
        nome = str(t.get("name") or "")
        try:
            nata = datetime.strptime(nome[len(PROVA):], "%Y-%m-%d-%H%M").replace(tzinfo=ROMA)
        except ValueError:
            nata = None
        if not intero(t.get("id")):
            male.append(f"etichetta {nome}: senza id nella risposta di Kit, non toccata")
        elif nome in occupate:
            print(f"- etichetta {nome}: resta (il suo invio è ancora in Kit e non è spedito)")
        elif nata is None or adesso - nata < timedelta(minutes=ELENCHI_SICURI):
            dopo = f" dopo le {nata + timedelta(minutes=ELENCHI_SICURI):%H:%M}" if nata else ""
            print(f"- etichetta {nome}: resta, ha meno di {ELENCHI_SICURI} minuti (l'elenco degli invii di Kit può non mostrare ancora "
                  f"il suo invio). Rilancia prova-pulizia{dopo}")
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
    if modo not in ("piano", "invia", "bozza", "prova", "pulizia") \
            or len(sys.argv) not in {"bozza": (3,), "prova": (4,), "pulizia": (2, 3)}.get(modo, (2,)):
        sys.exit(__doc__)
    a_capo, uscita = ("\n" if di_prova_ else ""), 1
    avvia_scadenza()
    try:
        try:
            if modo == "bozza":
                bozza(sys.argv[2])
            elif modo == "prova":
                prova(sys.argv[2], sys.argv[3])
            elif modo == "pulizia":
                pulisci(sys.argv[2] if len(sys.argv) > 2 else None)
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
