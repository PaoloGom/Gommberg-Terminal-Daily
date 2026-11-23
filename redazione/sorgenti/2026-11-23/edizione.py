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
NOTA_DATI = "Chiusure al 20 novembre; Kospi al 23 novembre; Tokyo chiusa per festa"
REG = "2026-11-23-settimana.json"

_D = json.load(open("dati.json", encoding="utf-8"))["serie"]
def _var(n):
    u = _D[n]["ultimi"]
    return round((u[0][1] / u[1][1] - 1) * 100, 1)
IND = [("Nasdaq", _var("Nasdaq")), ("S&P 500", _var("S&P 500")), ("Russell 2000", _var("Russell 2000")),
       ("Euro Stoxx 50", _var("Euro Stoxx 50")), ("FTSE MIB", _var("FTSE MIB")), ("Hang Seng", _var("Hang Seng")),
       ("Kospi (23/11)", _var("Kospi"))]
VIX = [("11-16", 22.91), ("11-17", 25.46), ("11-18", 24.56), ("11-19", 28.44), ("11-20", 35.89)]
UST2 = [("11-16", 4.83), ("11-17", 4.80), ("11-18", 4.80), ("11-19", 4.76), ("11-20", 4.63)]
d = lambda s: dt.date(2026, int(s[:2]), int(s[3:]))
TAB = tabelle_da_dati("dati.json")
C = {
    "data": OGGI,
    "temi": ["Wall Street", "Chip", "Fed", "Asia", "Tassi", "Materie prime"],
    "glossario": ["VIX", "CME FedWatch", "pb", "Sidecar", "BTP", "Bund"],
    "meccanismi": ["M01", "M04", "M10"],
    "ticker": ticker_da_dati("dati.json"),
    "top": {
        "tema": "Wall Street",
        "titolo": "Wall Street entra in correzione sui timori per l'intelligenza artificiale e Seul cade ancora",
        "dek": "Venerdì l'S&amp;P 500 ha perso il 3,70% e il Nasdaq il 5,28%, l'indice globale ACWI il 3,49% e il Nikkei il 5,06%. "
               "L'indice della paura (VIX) è salito del 26,2% a 35,89. Stanotte i future sono rimbalzati di oltre il 2%, ma il Kospi "
               "sudcoreano è di nuovo in forte calo. Il bersaglio resta Nvidia, dopo l'indagine SEC riportata dalla stampa americana. [[chip]]",
        "freccia": "Per Schwab pesano i dubbi sul finanziamento dell'intelligenza artificiale e l'uscita di Huang.",
    },
    "quadro": "La paura ha battuto la politica monetaria: i Treasury hanno fatto da rifugio e i rendimenti sono scesi, "
              "anche con un rialzo della Fed a dicembre quasi scontato. L'oro, che di solito ripara, è invece caduto insieme "
              "alle azioni, e a nostro avviso pesa il dollaro forte. Il petrolio e il cambio euro-dollaro sono rimasti quasi fermi.",
    "in30": [
        "L'indagine sui conti di Nvidia mette in dubbio la storia che ha sostenuto i chip. [[chip]]",
        "Nonostante la paura i rendimenti dei Treasury scendono, mentre la Fed guarda a un rialzo. [[treasury]]",
        "Mercoledì il dato sui prezzi PCE è la prova per i rimbalzi della settimana. [[agenda]]",
    ],
    "in30_temi": ["Chip", "Tassi", "Inflazione"],
    "stamattina_titolo": "Cosa guardare all'apertura",
    "stamattina": [
        "Kospi: minimo di giornata a 4.586,80 e chiusura di venerdì a 4.869,96, i due livelli da cui si legge se il rimbalzo tiene",
        "Alle 15:30 apre Wall Street: si vede se il rimbalzo dei future regge dopo il crollo di venerdì",
        "Fondo di stabilizzazione coreano: per il ministero delle Finanze si può usare subito se i ribassi continuano",
    ],
    "notizie": [
        {"tag": "Chip", "titolo": "La SEC indaga sui conti di Nvidia, riferisce la stampa americana",
         "testo": "L'inchiesta è agli inizi e può chiudersi senza accuse. Il titolo ha perso il 14% venerdì e più del 20% in settimana.",
         "rimando": "chip"},
        {"tag": "Tecnologia", "titolo": "Anthropic perde l'8,5% al secondo giorno di quotazione",
         "testo": "Chiude a 88,91 $, ancora sopra il prezzo di collocamento di 83 $, dopo il +17,1% del debutto."},
        {"tag": "Asia", "titolo": "Il governo di Seul prepara il fondo di stabilizzazione per il mercato",
         "testo": "Stamattina il Kospi ha ceduto il 3,3%. Il ministero delle Finanze dice che può usarlo subito se i ribassi continuano; a Taiwan il regolatore ha ordinato una stretta sulle vendite allo scoperto.",
         "rimando": "chip"},
        {"tag": "Banche", "titolo": "Le banche italiane perdono tra il 2% e il 3% in una giornata nera a Milano",
         "testo": "Per ANSA pesano la possibile stretta della Bce sui requisiti patrimoniali e l'emendamento della Lega che alza di tre punti l'Ires.",
         "rimando": "europa"},
        {"tag": "Fed", "titolo": "Waller (Fed): «Non possiamo aspettare»",
         "testo": "Per il governatore l'inflazione va nella direzione sbagliata.", "rimando": "treasury"},
        {"tag": "Macro", "titolo": "La fiducia dei consumatori del Michigan sale a 51,5",
         "testo": "Il dato finale di novembre supera la stima preliminare di 51,0; le attese di inflazione a un anno sono al 3,7%."},
    ],
    "mercati_titolo": "Numeri, temi aperti e calendario",
    "cruscotto": TAB["cruscotto"], "cruscotto_nota": TAB["cruscotto_nota"],
    "cross_data": TAB["cross_data"], "cross": TAB["cross"], "cross_nota": TAB["cross_nota"],
    "termometri": [
        ("Fed e tassi", "Rialzo di dicembre quasi scontato", "Waller e verbali di ottobre", "su: Probabilità di un rialzo", "PCE di mercoledì"),
        ("AI e chip", "In correzione", "Indagine SEC su Nvidia", "giu: Titoli dei chip", "Future e Kospi"),
        ("Asia", "Seul cede ancora", "Interventi dei governi", "giu: Kospi e Kosdaq", "Fondo di stabilizzazione"),
        ("Oro", "In calo da una settimana", "Venerdì sotto i 3.600 $", "giu: Oro future", "Dollaro e Treasury"),
    ],
    "fermi": "Petrolio e cambio euro-dollaro: venerdì poco mossi, con il Brent a 92,57 $ e l'EUR/USD a 1,0967.",
    "lettura": "Il Nasdaq perde più dell'S&amp;P 500, e il Russell 2000, l'indice delle società piccole, meno: a nostro avviso "
               "pesa il peso dei grandi tecnologici, che nel Nasdaq è molto più alto. E in Asia Seul cade più di Hong Kong, "
               "dove i produttori di chip contano meno nell'indice.",
    "ieri": [
        ("Mer 18", "Verbali della Fed (riunione di ottobre)", "Per un paio di partecipanti un rialzo oltre 25 pb \"potrebbe essere considerato\" a dicembre", "", "[[treasury]]"),
        ("Ven 20", "Fiducia consumatori Michigan (novembre, finale)", "51,5 (atteso 51,5); stima preliminare 51,0", "=", ""),
    ],
    "agenda": [
        ("Mar 24, 16:00", "Fiducia consumatori Conference Board (novembre)", "Prima 91,7", "Quanto la paura entra nei consumi",
         "<b>Sopra:</b> consumi solidi, rendimenti su.<br/><b>Sotto:</b> più timore sulla crescita, rendimenti giù."),
        ("<b>Mer 25, 14:30</b>", "<b>Prezzi PCE USA (ottobre)</b>", "<b>Prima +0,5% sul mese, +3,6% in un anno; senza energia e alimentari +0,3% e +3,1%</b>",
         "<b>Evento n.1:</b> la misura di inflazione che la Fed guarda di più",
         "<b>Sopra:</b> rialzo di dicembre più vicino, Treasury giù.<br/><b>Sotto:</b> la Fed ha meno fretta."),
        ("Mer 25, 14:30", "PIL USA terzo trimestre (seconda stima)", "Prima stima +3,4% annualizzato", "Tenuta dell'economia",
         "<b>Sopra:</b> l'economia regge, rendimenti su.<br/><b>Sotto:</b> cresce il timore di una frenata."),
        ("Gio 26", "Wall Street e Treasury chiusi per il Ringraziamento", "Venerdì le azioni chiudono alle 19:00 a Roma", "Pochi scambi",
         "Con volumi bassi anche movimenti piccoli possono pesare di più."),
    ],
    "moduli": [
        {"chiave": "chip", "tema": "Chip e Asia", "breve": "Nvidia e i chip sotto accusa",
         "titolo": "Le vendite sui chip passano dai prezzi alla fiducia dopo l'inchiesta su Nvidia",
         "misura": "doppio",
         "grafico": {"tipo": "barre", "file": "c_indici.png", "dati": IND, "ordina": False, "dec": 1, "unita": "%",
                     "soggetto": "chip", "ruolo": "quanto",
                     "titolo": "Le vendite colpiscono di più i listini con più tecnologia",
                     "sottotitolo": "variazioni % del 20/11 (Kospi: 23/11)"},
         "grafico2": {"tipo": "linee", "file": "c_vix.png", "x": [d(x) for x, _ in VIX], "soggetto": "VIX", "ruolo": "storia",
                      "serie": [("VIX", [v for _, v in VIX], "#F26B1D")],
                      "titolo": "L'indice della paura accelera nella seconda metà della settimana",
                      "sottotitolo": "VIX, chiusure",
                      "note": [(d("11-16"), 22.91, "16/11"), (d("11-20"), 35.89, "20/11")]},
         "perche": "L'indagine della SEC, riportata dalla stampa americana, tocca il titolo che di solito garantisce la storia dell'intelligenza artificiale, dopo l'uscita di Huang e i conti del 17/11. A nostro avviso il mercato non prezza più solo gli utili, ma anche il rischio di scoprire che i conti non reggono, e il VIX, l'indice della paura, lo mostra.",
         "numero": "-14%: il calo di Nvidia in una sola seduta, più del 20% in settimana.",
         "quindi": "Se i future di stanotte reggono all'apertura di Wall Street, il ribasso di venerdì era in parte un eccesso.",
         "punti": ["<b>Huang.</b> Si è dimesso il 12 novembre da amministratore delegato, President e consigliere; Colette Kress è amministratore delegato ad interim.",
                   "<b>Taiwan.</b> La Borsa perde il 17% in settimana, il calo settimanale più forte dal 1990.",
                   "<b>Seul.</b> Il Kospi chiude a 4.708,54 (-3,31%), il minimo dal 13 gennaio, con stranieri venditori netti per la settima seduta."],
         "testo": ["Perché un'inchiesta su un solo titolo fa cadere un intero settore? Perché Nvidia è il titolo su cui poggia la storia dell'intelligenza artificiale: i suoi conti dicono quanto spendono gli altri per i chip. Se i conti vengono messi in dubbio, tende a perdere fiducia tutta la filiera, dai produttori di memorie a chi quest'anno ha guadagnato di più.",
                   "A Seul pesa anche la struttura dell'indice. Pochi grandi produttori di chip, come Samsung e SK Hynix, fanno una parte larga del Kospi, e per questo la borsa coreana cade più di quella di Hong Kong. Il governo ha avviato i preparativi per attivare un fondo di stabilizzazione, e il ministero delle Finanze dice che può usarlo subito se i ribassi continuano.",
                   "Il mercato ha anche già bloccato gli scambi. Al secondo giorno di sidecar, il meccanismo che sospende per qualche minuto le vendite automatiche, il Kospi ha toccato un minimo di giornata a 4.586,80. È un segnale di panico più che di notizie nuove."],
         "fonte": "Fonti: AFP, InvestmentNews, comunicato Nvidia (SEC), The Korea Times, JKN, Al Jazeera, Schwab.",
         "guardare": "Decide l'apertura di Wall Street: se i chip rimbalzano con i future il ribasso era un eccesso, se ricadono il timore sui conti diventa un tema globale."},
        {"chiave": "treasury", "tema": "Tassi USA", "breve": "rendimenti giù con la Fed in rialzo",
         "titolo": "Con la Fed in rialzo i Treasury restano un rifugio e i rendimenti scendono",
         "misura": "doppio",
         "grafico": {"tipo": "linee", "file": "c_ust2.png", "x": [d(x) for x, _ in UST2], "soggetto": "Treasury",
                     "serie": [("2 anni", [v for _, v in UST2], "#111111")], "ruolo": "storia",
                     "titolo": "Il 2 anni chiude la settimana ai minimi del periodo",
                     "sottotitolo": "Treasury a 2 anni, chiusure (%)",
                     "note": [(d("11-16"), 4.83, "16/11"), (d("11-20"), 4.63, "20/11")]},
         "perche": "Venerdì il 10 anni è sceso dal 5,04% al 4,92% e il 2 anni di 13 pb. Eppure i future sui tassi danno il rialzo di dicembre tra il 92% e il 99%. A nostro avviso ha prevalso la paura: quando si vende la borsa, si comprano Treasury, il loro prezzo sale e il rendimento scende.",
         "quindi": "Se il 10 anni torna sopra il 5,04% la paura non basta più e torna a contare la Fed.",
         "numero": "92-99%: la probabilità di un rialzo a dicembre secondo i future sui tassi, a seconda della stima.",
         "testo": ["Rendimenti in calo con una Fed pronta a rialzare: venerdì il mercato ha guardato più alla paura che alla banca centrale. Chi vende azioni cerca un luogo sicuro. Di solito lo trova nei titoli di Stato americani, dove più compratori fanno salire il prezzo e scendere il rendimento, che si muove al contrario.",
                   "La Fed intanto non ha cambiato linea. Waller ha detto il 18 novembre che non si può aspettare e che a dicembre può servire un rialzo da 50 punti base. Nei verbali di ottobre un paio di partecipanti indicano che un aumento superiore a 25 punti base potrebbe essere considerato alla prossima riunione, a seconda dei dati sull'inflazione.",
                   "Le due cose possono convivere per qualche giorno, ma non a lungo. Se la paura cala, tende a tornare il peso della Fed, e il rendimento sale di nuovo. Il segnale da seguire è se rendimenti e borsa tornano a muoversi nella stessa direzione, come accade quando prevale il timore sui tassi.",
                   "Per capire la differenza conta la scadenza. Il rendimento a 2 anni segue di più le attese sui tassi della banca centrale nei prossimi mesi, quello a 10 anni anche crescita e inflazione di lungo periodo. Per questo venerdì il 2 anni è sceso di 13 pb, e di 12 il 10 anni: il mercato ha comprato titoli di tutte le scadenze, senza scegliere. Un rialzo da 50 pb a dicembre, se arrivasse, spingerebbe di solito su soprattutto il 2 anni. È il titolo più legato alle mosse immediate della banca centrale. Per questo, nei giorni di attesa di una riunione, il suo rendimento tende a muoversi più di quello a 10 anni.",
                   "Venerdì il 2 anni ha chiuso al 4,63% e il 10 anni al 4,92%, dopo un 2 anni a 4,83% lunedì scorso. Anche la fiducia dei consumatori dà un'indicazione: secondo l'Università del Michigan le famiglie si aspettano un'inflazione del 3,7% a un anno. È proprio il tipo di dato che la Fed guarda per capire se le attese di prezzo si stanno radicando."],
         "punti": ["<b>Verbali.</b> Nella riunione di ottobre un paio di partecipanti vedono possibile un aumento oltre i 25 pb alla prossima; quasi tutti ritengono probabile un altro rialzo.",
                   "<b>Attese.</b> Le attese di inflazione delle famiglie, rilevate dal Michigan, sono tra i dati che la Fed guarda con più attenzione."],
         "fonte": "Fonti: Stock Titan, Schwab, Investrade, Reuters (Business Day), Newsquawk.",
         "guardare": "Mercoledì il PCE di ottobre: un dato sopra il previsto rafforzerebbe la Fed e riporterebbe su i rendimenti, uno sotto lascerebbe spazio al rifugio."},
        {"chiave": "europa", "tema": "Europa e Italia", "breve": "Milano pesa STM e banche",
         "titolo": "A Milano pesano chip e banche, e l'Europa tocca il minimo da maggio",
         "misura": "mezzo",
         "righe": [["Venerdì 20 novembre", "Variazione", "Il punto"],
                   ["FTSE MIB", "-2,48%", "33 titoli su 40 in ribasso; -6,08% da inizio settimana"],
                   ["Euro Stoxx 50", "-2,81%", "Chiude a 5.941,95, il livello più basso da maggio"],
                   ["STMicroelectronics", "-10,78%", "A 36,72 euro"],
                   ["Banco Bpm, Unicredit, Intesa", "-3,02%, -2,54%, -2,41%", "Ipotesi di stretta Bce e Ires più alta"]],
         "larghezze": [30, 22, 70],
         "perche": "Secondo ANSA a Milano pesano i chip e le banche. Le banche, per ANSA, pagano la possibile stretta della Bce sui requisiti patrimoniali e l'emendamento della Lega che alza di tre punti l'Ires.",
         "quindi": "Alle 10:00 i PMI flash dell'area euro dicono se l'attività regge: da lì si vede se Milano rimbalza, anche perché STMicroelectronics, a 36,72 euro venerdì, segue i chip americani.",
         "testo": ["Milano perde quasi quanto l'Europa, e il motivo sta nella composizione: il listino italiano ha pochi grandi tecnologici ma molte banche, e venerdì sono caduti entrambi. Le banche tendono a soffrire quando si teme di dover accantonare più capitale. Soffrono anche per una tassa più alta sui loro utili, e per questo hanno perso tra il 2% e il 3%.",
                   "L'Euro Stoxx 50 ha perso circa il 7% in una settimana e chiude venerdì al livello più basso da maggio. Pesa il legame con Wall Street: quando i chip americani cadono, tendono a seguire i loro fornitori europei, e in Italia lo si vede su STMicroelectronics. Moncler e Stellantis hanno segnato il minimo a 52 settimane. Lo spread tra BTP e Bund chiude a 109,9 punti base, da 106 il giorno prima: i titoli di Stato italiani rendono un po' di più rispetto a quelli tedeschi."],
         "fonte": "Fonti: ANSA, Money.it, dpa-AFX."},
        {"chiave": "oro", "tema": "Materie prime", "breve": "l'oro cade con le azioni",
         "titolo": "L'oro non ripara dal panico perché dollaro e tassi pesano più della paura",
         "misura": "mezzo",
         "righe": [["Oro future", "Valore", "Variazione"],
                   ["Chiusura del 20/11", "3.515,40 $", "-4,6%"],
                   ["Chiusura del 19/11", "3.685,50 $", "-"],
                   ["Nella settimana", "-", "oltre -9%"]],
         "larghezze": [50, 40, 40],
         "perche": "Di solito l'oro sale quando c'è paura, ma venerdì è sceso insieme alle azioni. A nostro avviso pesa il dollaro forte: con una Fed pronta a rialzare i tassi, tenere un metallo che non rende interessi costa di più.",
         "quindi": "Mercoledì alle 14:30 il PCE: un dato più morbido darebbe fiato all'oro, uno più caldo lo terrebbe sotto i 3.600 $.",
         "testo": ["L'oro cade anche quando c'è paura, e la ragione è che non è solo un rifugio: è anche un'alternativa ai titoli che pagano interessi. Quando i tassi salgono o si attendono più alti, chi lo detiene rinuncia a un guadagno maggiore, e il metallo tende a perdere appeal. Il calo di venerdì non lo spiega una notizia sola: a nostro avviso è la somma di dollaro forte, tassi e vendite per coprire perdite altrove.",
                   "La settimana ha perso più del 9%: un calo di questa ampiezza in una settimana è raro per un metallo che molti considerano un porto sicuro. Se il rialzo della Fed a dicembre venisse confermato dal PCE di mercoledì, la pressione dei rendimenti tenderebbe a restare. Se il dato fosse più morbido, il metallo potrebbe recuperare almeno una parte del calo. Giovedì i mercati americani sono chiusi per il Ringraziamento e venerdì le azioni chiudono alle 19:00 a Roma. Con pochi scambi anche pochi ordini possono muovere il prezzo più del solito.",
                   "Per chi guarda i mercati, la lezione è che un rifugio non lo è sempre: dipende da cosa spaventa. Con la paura di una bolla sull'intelligenza artificiale i Treasury hanno funzionato da riparo, l'oro no. Per questo conviene chiedersi ogni giorno se a guidare i prezzi sono i tassi o la borsa."],
         "fonte": "Fonti: Investrade, Schwab."},
    ],
    "scommessa": {"tesi": "", "lunedi": True, "venerdi": False, "settimana_prec": "16-20 novembre",
                  "com_e_andata": "Il crollo di venerdì ha sorpreso anche noi: abbiamo preso la direzione giusta su tre mercati, ma i listini sono caduti ben oltre le forchette."},
    "parole": [("Correzione", "Un calo di almeno il 10% dall'ultimo massimo: segnala che la fiducia è cambiata, ma non decide da sola se la caduta continua."),
               ("Sidecar", "Una pausa di pochi minuti negli scambi automatici quando un indice scende troppo e in fretta."),
               ("VIX", "L'indice che misura quanto il mercato paga per proteggersi da cali dell'S&amp;P 500: sale quando cresce la paura."),
               ("Rifugio", "Un titolo, come i Treasury, che gli investitori comprano quando hanno paura."),
               ("Punto base", "Un centesimo di punto percentuale: 13 pb sono 0,13%."),
               ("Vendite allo scoperto", "Si vende un titolo preso in prestito sperando di ricomprarlo a meno: i regolatori le limitano nei giorni di panico.")],
    "fonti": [
        ("Dati di mercato", "Financial Modeling Prep, EODHD, Alpha Vantage; Euro Stoxx 50 con dpa-AFX; Kospi con Korea Times e JKN."),
        ("Prima pagina e mercati", "Schwab, Stock Market Watch, Investrade, Stock Titan, Al Jazeera, Fortune, Reuters, AFP."),
        ("Calendario e agenda", "Investrade, FinancialJuice, LiteFinance."),
        ("Approfondimenti", "Chip: AFP, InvestmentNews, Nvidia (SEC), Korea Times, JKN. Tassi: Reuters (Business Day), Newsquawk. Milano: ANSA, Money.it, dpa-AFX. Oro: Investrade, Schwab."),
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
