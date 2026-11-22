"""MODELLO v6 - Edizione #004 del 15/10/2026 rifatta nella struttura v6 (SPEC v6).
Ogni giorno: copia questo file nella cartella di lavoro, sostituisci SOLO i blocchi "CONTENUTI" e "DATI DEI GRAFICI"
(il dizionario C: nessun codice da scrivere), poi lancia
`python3 edizione_modello_v6.py <cartella di lavoro> <pdf di uscita>`: il motore impagina, riempie le 6 pagine
allungando i grafici scritti come dict, risolve i rimandi e scrive voce_indice.json per edizioni.json.
Prima: valuta.py (stato.json) e grafico.py (c_forecast.png) nella cartella di lavoro, come da ISTRUZIONI §5.
Regole rapide: un'idea ha un posto solo (ISTRUZIONI §3.3: non solo le cifre, anche le parole); in pag. 1 si titola e
si rimanda con [[chiave]] (diventa "→ pag. N"); righe "→" (freccia=...) max 5 in tutto; solo trattino corto; variazioni
con segno (il motore le colora). Temi (top "tema", "in30_temi", "tag" delle notizie) dall'elenco chiuso qui sotto.
Il contenuto si compila riscrivendo in un colpo solo il blocco C (uno script o un Write), non con decine di Edit.
Chiavi di rimando disponibili: mercati, agenda, scommessa + la "chiave" di ogni approfondimento.

REGOLE DEI CAMPI (v8.1: stanno qui, accanto ai campi; ISTRUZIONI.md tiene solo ciò che richiede giudizio).
- Temi, elenco chiuso (C["temi"] 3-6, top["tema"], in30_temi, "tag" delle notizie): Fed, BCE, Inflazione, Tassi, Wall Street,
  Europa, Italia, Asia, Cina, Chip, Tecnologia, Banche, Petrolio, Geopolitica, Valute, Dazi, Trimestrali, Macro, Credito,
  Materie prime.
- top: titolo max 2 righe, dek 3-4. in30: 3 punti senza cifre, col rimando. Voci "breve" dell'indice senza cifre.
- stamattina: future, Asia, petrolio, cambio, 10 anni con orario 06:00-09:29; senza livelli verificati
  "stamattina_titolo": "Cosa guardare all'apertura" con 2-4 soglie o eventi con orario.
- termometri: solo i temi mossi; gli altri in "fermi", fuori dopo 3 sedute. "lettura" (pag. 5) = ciò che le tabelle della
  pagina mostrano e la prima pagina non dice, mai il quadro con altre parole.
- moduli: 6 unità (mezzo = 1, doppio = 2) sulle pag. 2-4, in ordine d'importanza; un "doppio" comincia in cima a una pagina. Ogni modulo: perche, quindi, fonte; righe (mezzo max 5,
  doppio max 8); punti max 3; "guardare" obbligatorio nel doppio; niente "lettura". "numero", "punti" e "righe" solo se
  portano ciò che grafico e testo non dicono: qui sotto li usa solo chi li merita (§3.3). Due "mezzo" sulla stessa pagina si dividono
  lo spazio secondo il contenuto: non serve che siano lunghi uguali.
- grafici: "titolo" = cosa mostra, "sottotitolo" = misura e periodo, "soggetto" = parola del titolo o del perche, "ruolo" diverso
  per ogni elemento del modulo (quanto, perche, storia, conseguenza, chi); barre sempre con "unita", livelli con "livello": True;
  segna con "eventi" e "soglie" ciò che usano E quindi e Da guardare; sotto 5 valori meglio una frase. Mai "alto"/"largo".
- "&" si scrive com'è (S&P 500): lo sistema il motore. Solo trattino corto. Variazioni col segno. Numeri all'italiana.
- Lunedì: "ieri" = la settimana scorsa, in 3 righe al massimo; "agenda" = tutta la settimana fino a venerdì; 1 sett. del
  cruscotto = settimana intera.
- parole: 6 concetti (non sigle) del numero, in ordine di importanza: il motore ne mostra 3 o 6."""
import datetime as dt
import json
import os
import sys

REPO = os.path.join(os.environ.get("GTD_REPO", "/home/claude/gtd"), "redazione")   # kit e registri (mai la copia)
sys.path.insert(0, REPO)
from gommberg_engine import *  # noqa: E402,F403
from numeri import tabelle_da_dati, ticker_da_dati  # noqa: E402

LAVORO = sys.argv[1] if len(sys.argv) > 1 else "."
USCITA = sys.argv[2] if len(sys.argv) > 2 else None
os.chdir(LAVORO)   # grafici e c_forecast.png stanno qui

# =============================== CONTENUTI DEL GIORNO ===============================
OGGI = dt.date(2026, 11, 23)
NOTA_DATI = "Chiusure al 20 novembre; nessun livello di lunedì 23 verificato"
REG = "2026-11-23-settimana.json"
d = lambda s: dt.date(2026, int(s[:2]), int(s[3:]))
NASDAQ = [("11-09", 25253.14), ("11-10", 25065.87), ("11-11", 25466.19), ("11-12", 25366.09), ("11-13", 25136.27),
          ("11-16", 24509.76), ("11-17", 24328.38), ("11-18", 24429.88), ("11-19", 23879.20), ("11-20", 22617.73)]
ORO = [("11-09", 4114.5), ("11-10", 4030.2), ("11-11", 4000.5), ("11-12", 3885.3), ("11-13", 3886.3), ("11-16", 3853.0),
       ("11-17", 3864.2), ("11-18", 3741.9), ("11-19", 3685.5), ("11-20", 3515.4)]
UST2 = [("11-09", 4.56), ("11-10", 4.73), ("11-12", 4.86), ("11-13", 4.88), ("11-16", 4.83), ("11-17", 4.80),
        ("11-18", 4.80), ("11-19", 4.76), ("11-20", 4.63)]
CHIP = [("Micron", -13.9), ("Nvidia", -13.8), ("AMD", -13.3), ("Broadcom", -12.1), ("Indice dei chip", -10.7)]
BORSE = [("Taiwan", -6.63), ("Seul", -5.21), ("Tokyo", -5.06), ("Euro Stoxx 50", -2.81), ("Milano", -2.48), ("Parigi", -1.89),
         ("Londra", -1.02)]
TAB = tabelle_da_dati("dati.json")
C = {
    "data": OGGI,
    "temi": ["Wall Street", "Chip", "Asia", "Materie prime", "Fed", "Tecnologia"],
    "glossario": ["PCE", "core", "VIX", "pb", "AI", "Kospi", "Nasdaq", "Fed"],
    "meccanismi": ["M16", "M17", "M09", "M23", "M20", "M05", "M14"],
    "ticker": ticker_da_dati("dati.json"),
    "top": {
        "tema": "Wall Street",
        "titolo": "Wall Street entra in correzione e il Nasdaq perde il 5,3% con i chip",
        "dek": "L'S&P 500 perde il 3,7% e chiude oltre il 10% sotto il massimo di ottobre dopo sette perdite di fila, e il Nasdaq torna "
               "in rosso da inizio anno. La vendita parte dai chip: Nvidia lascia il 13,8% mentre il titolo paga la caduta del "
               "fondatore Jensen Huang, e AMD e Micron cedono più del 13%. Le borse asiatiche avevano già venduto, l'Europa ha "
               "chiuso in forte calo. Lunedì si capisce se la paura passa o continua. [[fiducia]]",
    },
    "quadro": "Il crollo ci sembra di fiducia più che di tassi. Il rendimento a 10 anni scende, come quando si cerca riparo. "
              "L'oro però cala del 4,6% invece di salire, e a nostro avviso si vende ciò che si vende bene per coprire le perdite "
              "sulle azioni. Il mondo azionario (ACWI) perde il 3,5%, con Tokyo a -5,06% e Seul a -5,21%. Il VIX, l'indice della paura, sale di 7 punti e chiude a 35,89; il dollaro e il Brent restano quasi fermi.",
    "in30": [
        "I chip cadono insieme per il dubbio sui conti dell'IA, non per i tassi. [[fiducia]]",
        "Per noi Taiwan e Corea cedono più di Londra perché i chip contano di più nell'indice. [[asia]]",
        "Mercoledì il dato sui prezzi dice se la Fed ha ancora fretta di alzare i tassi. [[pce]]",
    ],
    "in30_temi": ["Chip", "Asia", "Macro"],
    "stamattina_titolo": "Cosa guardare all'apertura",
    "stamattina": [
        "Alle 01:00 di Roma riaprono Tokyo e Seul dopo il crollo di venerdì",
        "Alle 15:30 riapre Wall Street; l'S&P 500 ha chiuso venerdì a 6.910,39",
        "Nello scenario peggiore dei broker coreani Hana e BNK il Kospi scende tra 4.300 e 4.500 punti",
    ],
    "notizie": [
        {"tag": "Chip", "titolo": "Broadcom perde il 12,1% e i chip americani cadono in blocco",
         "testo": "Con AMD e Micron oltre il 13%, l'indice dei semiconduttori di Philadelphia lascia sul terreno il 10,7%.",
         "rimando": "fiducia"},
        {"tag": "Chip", "titolo": "Nvidia chiude la nona seduta in calo su dieci",
         "testo": "Dalla caduta di Huang il titolo ha lasciato più del 25%, e la SEC avrebbe aperto un'indagine, scrive il Wall Street Journal.",
         "rimando": "fiducia"},
        {"tag": "Tecnologia", "titolo": "Anthropic cede il 9,1% nella seconda seduta da quotata",
         "testo": "Chi è entrato nel collocamento ha ancora un guadagno, chi ha comprato all'apertura del debutto ha perso più di un quinto.",
         "rimando": "anthropic"},
        {"tag": "Asia", "titolo": "Seul attiva i sidecar dopo il crollo di Samsung Electronics e SK hynix",
         "testo": "La pausa agli ordini automatici scatta con il Kospi sotto 4.900 punti per la prima volta in dieci mesi; Samsung cede il 7,01% e SK hynix il 5,92%.",
         "rimando": "asia"},
        {"tag": "Italia", "titolo": "Stm e Technoprobe perdono oltre il 9% mentre Piazza Affari cede il 2,48%",
         "testo": "Il Ftse Mib chiude il quinto ribasso di fila e lo spread BTP-Bund sale di 5 punti base a 111 (+4,7%).", "rimando": "asia"},
        {"tag": "Tecnologia", "titolo": "Corning e Bloom Energy perdono il 10,9% e il 15,3%",
         "testo": "Due fornitori delle infrastrutture dell'IA perdono più di un decimo del loro valore in una seduta.",
         "rimando": "fiducia"},
    ],
    "mercati_titolo": "Numeri, temi aperti e calendario",
    "cruscotto": TAB["cruscotto"], "cruscotto_nota": TAB["cruscotto_nota"],
    "cross_data": TAB["cross_data"], "cross": TAB["cross"], "cross_nota": TAB["cross_nota"],
    "termometri": [
        ("Fed e tassi", "Decisione a dicembre", "Il 10 anni scende sotto il 5%", "giu: Rendimento a 10 anni", "Dato sui prezzi di mercoledì"),
        ("AI e borsa", "Venerdì nero sui chip", "Nvidia dopo l'uscita di Huang", "giu: Titoli dei chip", "Apertura di Wall Street alle 15:30"),
        ("Oro e dollaro", "Oro a 3.515 $", "Il calo più forte dal 22 marzo", "giu: Oro, anche con i Treasury in rialzo", "Dollaro e rendimenti USA"),
        ("Petrolio", "Brent a 92,57 $", "Hormuz e guerra USA-Iran sostengono il prezzo", "fermo: Brent, senza direzione", "Notizie da Hormuz"),
    ],
    "fermi": "Sanità USA (nessuna novità verificata) e tassi della Bce (prossima riunione il 17 dicembre).",
    "lettura": "Il Russell 2000, l'indice delle società piccole, perde il 2,8%, meno dell'S&amp;P 500 e quasi la metà del Nasdaq: "
               "a nostro avviso perché nell'indice contano poco i colossi dell'IA, che sono quelli venduti. Nel mondo l'ACWI, il "
               "fondo che replica le borse globali, perde il 3,5%, e l'Europa cede meno degli Stati Uniti perché ha meno "
               "tecnologia in indice. A nostro avviso la differenza conta per chi guarda il portafoglio: una correzione concentrata "
               "sui titoli dei chip colpisce di più chi ha molta tecnologia americana e meno chi è diversificato tra settori e aree. "
               "Lunedì conterà vedere se i titoli difensivi, come sanità ed energia, reggono mentre i chip cercano un livello da cui ripartire. "
               "Per noi il segnale più utile non è la discesa in sé, ma quanto in fretta si ricompone la fiducia nei bilanci: "
               "se le prossime trimestrali di settore confermano gli ordini, il calo resta una correzione; se li smentiscono, "
               "il discorso cambia e gli investitori dovranno rivedere le attese sugli utili dell'intero comparto tecnologico.",
    "ieri": [],
    "agenda": [
        ("<b>Mer 25, 14:30</b>", "<b>PCE core (ottobre)</b>", "<b>+0,3% sul mese; +3,2% su un anno; prima +3,1%</b>",
         "<b>Evento n.1:</b> i prezzi che la Fed guarda di più",
         "<b>Sopra:</b> la Fed ha più motivi per alzare i tassi e i rendimenti brevi salgono.<br/>"
         "<b>Sotto:</b> la Fed ha meno fretta e le borse possono respirare."),
        ("Mer 25, 14:30", "PIL USA terzo trimestre (seconda stima)", "+3,4% annualizzato", "Tenuta della crescita",
         "<b>Sopra:</b> l'economia regge e i rendimenti non scendono.<br/><b>Sotto:</b> torna il timore di una frenata."),
        ("Gio 26, 15:30", "Borse USA chiuse per il Ringraziamento", "Chiusura della borsa", "Meno scambi in giro per il mondo",
         "<b>Sopra:</b> nessun dato da leggere.<br/><b>Sotto:</b> in Europa i movimenti pesano meno, con pochi scambi."),
        ("Ven 27, 19:00", "Wall Street chiude in anticipo", "Chiusura alle 13:00 a New York", "Seduta breve dopo la festa",
         "<b>Sopra:</b> nessun dato da leggere.<br/><b>Sotto:</b> con pochi scambi un movimento forte dice meno."),
    ],
    "moduli": [
        {"chiave": "fiducia", "tema": "Chip e IA", "breve": "i chip cadono insieme",
         "titolo": "Il dubbio sui conti dell'IA, non i tassi, fa cadere tutti i chip",
         "misura": "doppio",
         "grafico": {"tipo": "barre", "file": "c_chip.png", "dati": CHIP, "ordina": False, "dec": 1, "unita": "%",
                     "soggetto": "chip", "ruolo": "quanto",
                     "titolo": "Nessun grande titolo dei chip si è salvato",
                     "sottotitolo": "variazioni % del 20/11"},
         "grafico2": {"tipo": "linee", "file": "c_nasdaq.png", "x": [d(x) for x, _ in NASDAQ],
                      "serie": [("Nasdaq", [v for _, v in NASDAQ], "#111111")], "soggetto": "Nasdaq", "ruolo": "storia",
                      "titolo": "Dal massimo dell'11 novembre il Nasdaq perde l'11%", "sottotitolo": "Nasdaq Composite, chiusure",
                      "soglie": [(23000, "23.000")], "note": [(d("11-11"), 25466.19, "11/11"), (d("11-20"), 22617.73, "20/11")]},
         "perche": "Per AP la vendita che affonda il Nasdaq nasce dai timori su valutazioni e spese per l'IA. Pesa anche l'esito delle "
                   "elezioni di metà mandato, con candidati favorevoli a rallentare i data center. A nostro avviso non sono i tassi: una vendita guidata dai "
                   "tassi li avrebbe fatti salire, mentre il rendimento a 10 anni è sceso di 12 pb.",
         "quindi": "Se alle 15:30 i chip americani rimbalzano, le vendite di venerdì erano in parte panico. Un altro calo del Nasdaq "
                   "farebbe del dubbio sui conti dell'IA il tema della settimana.",
         "testo": ["Un giorno così brutto per Nvidia non nasce da un dato ma da una questione di fiducia. Jensen Huang "
                   "ha lasciato la guida dell'azienda e, secondo il Wall Street Journal, la SEC ha aperto un'indagine. Nvidia "
                   "è il titolo su cui poggia buona parte della corsa dei chip. Quando il suo fondatore se ne va e arriva "
                   "un'indagine, chi aveva comprato il settore tende a vendere tutto insieme.",
                   "Perché il Nasdaq perde così tanto? Un indice come questo conta i titoli in proporzione al loro valore in "
                   "borsa, quindi pochi colossi ne decidono la direzione. Quando cadono i grandi dei chip l'indice cede molto, "
                   "anche se gli altri titoli reggono. Per questo il Nasdaq perde il 5,3% mentre il Dow Jones, che ha meno tecnologia, cede l'1,9%, e lo stesso meccanismo vale in salita.",
                   "La vendita passa poi dalle società che vivono delle spese per l'IA. Corning perde il 10,9% e Bloom Energy il "
                   "15,3%, ma anche Anthropic, appena quotata, lascia il 9,1%. A nostro avviso il mercato non paga più la promessa: "
                   "vuole vedere chi incassa.",
                   "Per misurare la giornata serve un confronto. L'S&P 500 chiude la settimana peggiore da aprile 2025 e la serie di "
                   "sette perdite consecutive è la più lunga dal 2020. Non è una conclusione ma un metro. In giorni così le "
                   "borse cadono insieme, e per capire se è un fondo conta più la reazione del giorno dopo."],
         "numero": "35,89: il VIX, l'indice della paura, chiude al livello più alto da aprile 2025, per Fox Business.",
         "fonte": "Fonti: AP, Reuters, Fox Business, Wall Street Journal (ripreso da Reuters), Seoul Economic Daily; chiusure di FMP.",
         "guardare": "Conta l'apertura dei chip americani alle 15:30. Se Nvidia risale dal minimo di venerdì, la vendita era "
                     "panico. Un'altra seduta così direbbe che il mercato dubita dei bilanci di tutto il settore, non solo di Nvidia e dei suoi fornitori."},
        {"chiave": "asia", "tema": "Asia e Europa", "breve": "Seul e Taipei cadono più di Londra",
         "titolo": "Più i chip pesano nell'indice, più la borsa cade",
         "misura": "mezzo",
         "grafico": {"tipo": "barre", "file": "c_borse.png", "dati": BORSE, "ordina": True, "dec": 1, "unita": "%",
                     "soggetto": "borsa", "ruolo": "quanto",
                     "titolo": "Dove i chip contano di più la borsa cade di più",
                     "sottotitolo": "variazioni % del 20/11"},
         "perche": "A nostro avviso Taiwan e Corea cedono di più perché i loro indici poggiano su pochi produttori di chip. "
                   "Londra ha un'economia più varia, e di solito un indice cade di più dove pesano i titoli colpiti.",
         "quindi": "Il test è la riapertura di Seul alle 01:00: nello scenario più duro dei broker coreani il Kospi scende a "
                   "4.300-4.500 punti, fino al 12% sotto la chiusura.",
         "testo": ["Taiwan perde quasi sette punti percentuali, Seul oltre cinque e Londra uno: è lo stesso giorno, ma non lo stesso mercato. Gli "
                   "indici di Taiwan e della Corea ruotano attorno a pochi produttori di chip, e quando il settore cade "
                   "l'indice li segue. A Londra i titoli sono più vari e la caduta è più contenuta.",
                   "Seul scende sotto 4.900 punti per la prima volta in dieci mesi. "
                   "Samsung Electronics cede il 7,01%, e per frenare le vendite la borsa ha attivato i sidecar, una pausa "
                   "imposta agli ordini automatici. In Europa il colpo arriva smorzato: l'Euro Stoxx 50 perde il 2,81%, "
                   "Milano il 2,48% con Stm e Technoprobe in testa alle perdite.",
                   "Il segnale è la distanza tra i mercati: il Ftse 100 di Londra perde l'1,02%, meno della metà dell'Euro Stoxx 50. "
                   "Chi ha in portafoglio titoli diversificati ha sentito il colpo in modo diverso da chi ha comprato i chip."],
         "numero": "47-48%: la perdita del Kospi dal massimo di giugno, secondo le stime di Seoul Economic Daily e Aju Press, prima di toccare i 4.869,96 di venerdì.",
         "fonte": "Fonti: Aju Press, Seoul Economic Daily, dpa-AFX, Teleborsa, askanews; chiusure di FMP ed EODHD.",
         "guardare": "Contano Tokyo e Seul all'apertura delle 01:00: se reggono, la vendita ha già fatto il suo corso."},
        {"chiave": "oro", "tema": "Oro e Treasury", "breve": "oro in calo con i Treasury su",
         "titolo": "L'oro cade nel giorno della paura: forse si vende per fare cassa",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_oro.png", "x": [d(x) for x, _ in ORO], "soggetto": "oro", "ruolo": "storia",
                     "serie": [("Oro future", [v for _, v in ORO], "#F26B1D")],
                     "titolo": "L'oro perde il 14,6% in due settimane", "sottotitolo": "Oro future, chiusure ($)",
                     "soglie": [(3500, "3.500 $")],
                     "note": [(d("11-09"), 4114.5, "9/11"), (d("11-20"), 3515.4, "20/11")]},
         "perche": "Di solito nei giorni di paura salgono sia i titoli di Stato sia l'oro. Venerdì i Treasury sono saliti e il "
                   "rendimento a 10 anni è sceso di 12 pb, mentre l'oro ha ceduto il 4,6%. A nostro avviso molti hanno venduto "
                   "l'oro, che si vende in fretta e con guadagno, per coprire le perdite sulle azioni.",
         "quindi": "Una chiusura sotto 3.500 $ dice che le vendite continuano; l'oro che sale con le borse che rimbalzano "
                   "smentisce la lettura.",
         "testo": ["Due rifugi hanno detto cose opposte nello stesso giorno. I titoli di Stato americani sono saliti di prezzo, "
                   "e il rendimento, che si muove al contrario, è sceso. L'oro invece ha perso una parte rilevante del suo valore "
                   "in una seduta.",
                   "Chi perde sulle azioni deve spesso trovare contanti, e vende ciò che ha in portafoglio e si vende senza "
                   "difficoltà, anche se non c'entra con il problema. L'oro è uno di questi beni. Con i tassi in discesa "
                   "l'oro, che non paga interessi, di solito ne trae vantaggio: venerdì non è stato così."],
         "numero": "599 $: la distanza tra la chiusura del 9 novembre e quella di venerdì, 3.515,40 $: il calo più forte da marzo.",
         "fonte": "Fonti: FMP (oro e Treasury), AP.",
         "guardare": "Conta la chiusura di lunedì: se l'oro non risale con le borse, le vendite per fare cassa non sono finite."},
        {"chiave": "pce", "tema": "Fed e tassi", "breve": "i prezzi di mercoledì decidono",
         "titolo": "Il dato sui prezzi di mercoledì dice se la Fed può rallentare",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_ust2.png", "x": [d(x) for x, _ in UST2], "soggetto": "Fed", "ruolo": "storia",
                     "serie": [("Treasury 2 anni", [v for _, v in UST2], "#111111")],
                     "titolo": "Il rendimento a 2 anni scende di 25 pb in cinque sedute", "sottotitolo": "Treasury 2 anni, chiusure (%)",
                     "note": [(d("11-13"), 4.88, "13/11"), (d("11-20"), 4.63, "20/11")]},
         "perche": "Il PCE è l'indice dei prezzi che la Fed guarda di più. A nostro avviso il core, cioè i prezzi senza energia e alimentari, darebbe alla Fed più motivi per "
                   "alzare i tassi a dicembre se uscisse sopra il 3,2% atteso. Un dato in linea lascerebbe più peso alla paura "
                   "delle borse.",
         "quindi": "Se mercoledì alle 14:30 il rendimento a 2 anni torna verso 4,80%, il mercato ha ripreso a temere la Fed.",
         "testo": ["Il rendimento a 2 anni segue le attese sui tassi della Fed, e in cinque sedute è sceso di 25 pb. Chi presta "
                   "per due anni al governo americano si aspetta meno rialzi di prima, perché con le borse in difficoltà "
                   "una banca centrale tende a frenare.",
                   "Il dato di mercoledì può cambiare la lettura. Se i prezzi corrono più del previsto, la Fed ha meno margine "
                   "per ascoltare la paura delle borse; se sono in linea, il calo dei rendimenti ha più senso.",
                   "Lo stesso giorno esce il PIL americano del terzo trimestre, atteso a +3,4% annualizzato. Una crescita forte dà "
                   "alla Fed più spazio per restare dura, una più debole le dà un motivo in più per aspettare: i due dati si "
                   "leggono insieme."],
         "numero": "Un decimo: lo scarto tra il core atteso e quello di prima. Basta così poco per muovere i rendimenti, perché il mercato ha già in testa il dato di prima.",
         "fonte": "Fonti: FMP (curva del Tesoro USA), calendario HyperStocks e LiteFinance.",
         "guardare": "Mercoledì alle 14:30, insieme al PIL: un core sopra il 3,2% riporta in primo piano i tassi."},
        {"chiave": "anthropic", "tema": "Tecnologia", "breve": "Anthropic vicina al prezzo IPO",
         "titolo": "Anthropic perde il 23% dal massimo ma resta sopra il prezzo di collocamento",
         "misura": "mezzo",
         "righe": [["Momento", "Prezzo in dollari"],
                   ["Collocamento del 19/11", "83,00"],
                   ["Apertura del 19/11", "111,50"],
                   ["Massimo del 19/11", "115,10"],
                   ["Chiusura del 19/11", "97,17"],
                   ["Chiusura del 20/11", "88,30"]],
         "larghezze": [60, 40], "ruolo_righe": "quanto",
         "perche": "A nostro avviso il prezzo del collocamento è il punto che guardano gli investitori entrati per primi. "
                   "I titoli appena quotati tendono a seguire il settore, e il settore oggi vende.",
         "quindi": "Alla riapertura di Wall Street alle 15:30, una chiusura sotto il prezzo di collocamento dice che il guadagno del debutto è svanito.",
         "testo": ["Chi ha comprato nel collocamento a 83 $ ha ancora un guadagno del 6%, chi ha comprato all'apertura a "
                   "111,50 $ ha già perso più di un quinto. Il debutto, la più grande quotazione di sempre, ha mostrato "
                   "quanto sia facile passare dall'entusiasmo alla vendita.",
                   "Un titolo nuovo non ha ancora una storia di conti: i prezzi li fanno la fiducia e i flussi. Per questo "
                   "segue il settore più di altri, e venerdì il settore ha venduto."],
         "fonte": "Fonti: AP, Aju Press.",
         "guardare": "Conta il prezzo di collocamento: sopra, il debutto ha ancora un guadagno; sotto, non resta nulla."},
    ],
    "scommessa": {"tesi": "", "lunedi": True, "venerdi": False, "settimana_prec": "16-20 novembre",
                  "com_e_andata": "Il crollo della tecnologia di venerdì ha deciso la settimana: azioni e oro hanno ceduto, mentre i rendimenti sono scesi."},
    "parole": [("Correzione", "Un calo di oltre il 10% di un indice dal suo massimo recente."),
               ("Sidecar", "Pausa che la borsa coreana impone agli ordini automatici quando l'indice cade troppo in fretta."),
               ("Capitalizzazione", "Il valore in borsa di una società: più è alto, più pesa nell'indice."),
               ("Prezzo di collocamento", "Il prezzo a cui una società vende le sue azioni al pubblico il primo giorno."),
               ("Vendite forzate", "Vendite fatte per coprire perdite altrove, non per scelta."),
               ("Semiconduttori", "I chip: i componenti dei computer e dei server su cui si basa l'IA.")],
    "fonti": [
        ("Dati di mercato", "Financial Modeling Prep (indici USA e Asia, VIX, Brent e oro future, curva del Tesoro USA); EODHD (Euro Stoxx 50, ACWI); "
                            "Alpha Vantage (EUR/USD); Teleborsa e askanews (Ftse Mib, spread); Aju Press e Korea Times (Kospi)."),
        ("Prima pagina e mercati", "AP, Fox Business, Reuters, Teleborsa, askanews."),
        ("Calendario e agenda", "HyperStocks, LiteFinance, NYSE."),
        ("Approfondimenti", "Come nella riga Fonti di ogni pezzo; oro, Treasury e Fed da FMP."),
        ("La scommessa", "Chiusure di FMP, EODHD e Alpha Vantage; forchette calcolate dalla volatilità delle ultime 20 sedute."),
    ],
}

# ================================ COMPOSIZIONE (non toccare) ================================
if __name__ == "__main__":
    set_meta(OGGI, NOTA_DATI)
    reg = json.load(open(os.path.join(REPO, "pronostici", REG), encoding="utf-8"))
    stato = json.load(open("stato.json", encoding="utf-8")) if os.path.exists("stato.json") else None
    verdetto = json.load(open("verdetto.json", encoding="utf-8")) if os.path.exists("verdetto.json") else None
    pagella_p = os.path.join(REPO, "scommessa", "pagella.json")
    pagella = json.load(open(pagella_p, encoding="utf-8")) if os.path.exists(pagella_p) else None
    out = USCITA or nome_file(OGGI)
    try:   # riscritture del desk accettate da desk.py verifica (solo sui campi rimasti come il desk li ha letti)
        import desk
        desk.applica(C)
    except Exception as e:  # noqa: BLE001
        print("AVVISO desk:", e)
    render_v6(out, lambda: edizione_v6(C, stato=stato, reg=reg, verdetto=verdetto, pagella=pagella))
    voce = voce_indice(C, stato, reg)
    try:   # campi per controlli_temi.py e controlli_contenuti.py (non sovrascrive quelli del motore)
        import extra_voce
        voce.update(extra_voce.campi(C, voce))
    except Exception as e:  # noqa: BLE001
        print("AVVISO extra_voce:", e)
    json.dump(voce, open("voce_indice.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(out)
