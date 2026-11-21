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
NOTA_DATI = "Chiusure al 20 novembre; nessun livello verificato per la mattina del 23 novembre"
REG = "2026-11-23-settimana.json"          # registro della scommessa (redazione/pronostici/)

# ============================ DATI DEI GRAFICI (verificati) ============================
d = lambda s: dt.date(2026, int(s[:2]), int(s[3:]))   # "MM-GG" -> data
_S = json.load(open("serie.json"))
NASDAQ = [tuple(x) for x in _S["nas"]]
UST2 = _S["u2"]; UST10 = _S["u10"]
UST_X = sorted(UST2.keys())
ORO = [tuple(x) for x in _S["oro"]]
SETTORI = [("Tecnologia", -5.34), ("Immobiliare", -3.94), ("Consumi ciclici", -3.61), ("Comunicazione", -3.44),
           ("Industria", -2.93), ("Servizi pubblici", -2.80), ("Finanza", -2.35), ("Materiali", -1.97),
           ("Energia", -1.93), ("Sanità", -1.84), ("Consumi di base", 0.08)]
TAB = tabelle_da_dati("dati.json")
C = {
    "data": OGGI,
    "temi": ["Wall Street", "Chip", "Fed", "Europa", "Materie prime", "Asia"],
    "glossario": ["SEC", "VIX", "PCE", "core", "PMI", "FOMC", "CME FedWatch", "BoJ"],
    "meccanismi": ["M26", "M23", "M16", "M09"],
    "ticker": ticker_da_dati("dati.json"),
    "top": {
        "tema": "Wall Street",
        "titolo": "Wall Street crolla e il Nasdaq cancella tutto il rialzo del 2026",
        "dek": "L'S&P 500 perde il 3,7% e chiude in correzione, cioè oltre il 10% sotto il massimo di ottobre; il Nasdaq "
               "cede il 5,3% e finisce l'anno in negativo. A pesare sono i chip: Nvidia lascia il 14% dopo che, secondo "
               "Reuters, la SEC (l'autorità di Borsa americana) esamina possibili problemi nei suoi conti. Nemmeno "
               "Anthropic, scesa dell'8,5% nella seconda seduta ma ancora sopra il prezzo di collocamento, ha frenato "
               "le vendite. [[chip]]",
    },
    "quadro": "La paura ha preso il posto dell'inflazione, ma con una crepa. Il Treasury a 10 anni scende al 4,92% e il 2 anni "
              "al 4,63%, come quando si cerca riparo nei titoli di Stato. L'oro cede più del 2% e il dollaro quasi non si muove (EUR/USD 1,0967). A nostro avviso si vende ciò che si può vendere per far cassa. "
              "L'indice azionario mondiale ACWI (indice azionario mondiale MSCI) perde il 3,5%, il VIX (volatilità attesa sull'S&P 500) sale del 26,2% e il Brent, 92,57 $, resta quasi fermo.",
    "in30": [
        "La Fed non ha margine per soccorrere la borsa: pesa l'inflazione. [[fed]]",
        "L'Europa cade con Wall Street: a Milano cedono chip e banche. [[europa]]",
        "Mercoledì il dato sui prezzi che la Fed guarda di più, giovedì Wall Street è chiusa. [[agenda]]",
    ],
    "in30_temi": ["Fed", "Europa", "Macro"],
    "stamattina_titolo": "Cosa guardare all'apertura",
    "stamattina": [
        "Alle 10:00 il PMI flash (sondaggio sui direttori acquisti) dell'area euro, sull'attività di novembre",
        "Alle 15:30 apre Wall Street: si vede se le vendite di venerdì continuano",
        "Alle 15:45 il PMI flash degli Stati Uniti, atteso a 55,6 contro il 55,9 precedente",
        "Brent: chiuso venerdì sotto i 93 $, si guardano le notizie da Hormuz",
    ],
    "notizie": [
        {"tag": "Asia", "titolo": "SoftBank perde il 14% a Tokyo e il Nikkei scende ai minimi da aprile",
         "testo": "Il Nikkei chiude a 56.436,65 punti (-5,06%), il livello più basso dal 13 aprile. Con SoftBank, in forte calo, cede anche Advantest, tra i titoli che perdono di più (Reuters).",
         "rimando": "chip"},
        {"tag": "Macro", "titolo": "In Giappone l'inflazione sale al 2,3% e alimenta le attese di rialzo dei tassi",
         "testo": "Il dato di ottobre rafforza le attese su una mossa della Banca del Giappone (BoJ, la banca centrale "
                  "giapponese), proprio mentre il Nikkei vende (Reuters)."},
        {"tag": "Cina", "titolo": "Nuove strette USA sulla tecnologia per la Cina fanno scendere il listino tecnologico di Hong Kong (-3,8%)",
         "testo": "L'Hang Seng chiude a 22.410,80 punti. Tra le cause le strette "
                  "americane sulla tecnologia diretta alla Cina (RTHK)."},
        {"tag": "Chip", "titolo": "Samsung perde il 7% a Seul e SK hynix quasi il 6%",
         "testo": "Il Kospi chiude a 4.869,96 punti, il 5,2% in meno, mentre gli investitori esteri vendono i titoli "
                  "dei semiconduttori (IANS).", "rimando": "chip"},
        {"tag": "Banche", "titolo": "Il cda di Mps giudica congruo il prezzo di Intesa e Passera si dimette",
         "testo": "L'offerta vale 1,250 euro in contanti più 1,664 azioni Intesa per ogni azione Mps; "
                  "Corrado Passera lascia durante la riunione, parlando di «profondo dissenso». Le adesioni partono "
                  "il 24 novembre."},
        {"tag": "Petrolio", "titolo": "Gli incidenti alle petroliere a Hormuz fanno rimbalzare il Brent, ma è la terza settimana di calo",
         "testo": "Pesano i timori per l'Iran e gli incidenti alle petroliere nello Stretto di Hormuz; i flussi sono "
                  "però tornati vicino ai livelli di prima della guerra (Reuters)."},
    ],
    "mercati_titolo": "Numeri, temi aperti e calendario",
    "cruscotto": TAB["cruscotto"], "cruscotto_nota": TAB["cruscotto_nota"],
    "cross_data": TAB["cross_data"], "cross": TAB["cross"], "cross_nota": TAB["cross_nota"],
    "termometri": [
        ("Fed e tassi", "Riunione 8-9 dicembre", "Waller: mossa decisa a dicembre", "fermo: Rialzo di dicembre, dato per probabile", "PCE di mercoledì"),
        ("AI e chip", "Anthropic, seconda seduta", "Chiude a 88,91 $, sopra il collocamento", "giu: Titoli dei chip e Nasdaq", "Apertura di Wall Street alle 15:30"),
        ("Oro", "Future sotto 3.520 $", "Vende anche chi ha paura", "giu: Oro future", "Treasury a 10 anni"),
        ("Petrolio", "Brent poco sopra 92 $", "Petroliera colpita a Hormuz sabato", "fermo: Brent, senza direzione", "Notizie dal Golfo"),
    ],
    "fermi": "Tassi della Bce, UniCredit e Commerzbank (accordo del 19/11).",
    "lettura": "Il Russell 2000, l'indice delle imprese più piccole, perde meno dell'S&P 500: la vendita ha colpito i "
               "grandi nomi della tecnologia, non tutta l'economia americana. Lo conferma il Treasury a 2 anni, che "
               "scende più di quello a 10: chi compra titoli di Stato guarda ai tassi della Fed, non a una crisi dei conti. "
               "Il cambio euro-dollaro quasi non si muove: quando lo shock nasce a Wall Street il dollaro tende a non fare da "
               "rifugio. E lo spread tra BTP e Bund sale di soli quattro punti base, poco rispetto al calo delle borse.",
    "ieri": [
        ("Gio 19, 14:30", "Sussidi di disoccupazione USA", "203 mila (atteso 197 mila)", "+", "[[fed]]"),
        ("Gio 19, 14:30", "Indice Philadelphia Fed (novembre)", "6,3 (atteso 20,0)", "-", "[[fed]]"),
    ],
    "agenda": [
        ("Lun 23, 15:45", "PMI flash USA (novembre)", "Composito 55,6; prima 55,9", "Attività delle imprese americane",
         "<b>Sopra:</b> l'economia regge e i rendimenti salgono.<br/><b>Sotto:</b> si parla di frenata."),
        ("<b>Mer 25, 14:30</b>", "<b>PCE di ottobre (prezzi dei consumi)</b>", "<b>Core +0,3% sul mese, +3,2% su un anno; prima +3,1%</b>",
         "<b>Evento n.1:</b> il dato sui prezzi che la Fed guarda di più",
         "<b>Sopra:</b> più forza ai rialzi e di solito rendimenti su.<br/><b>Sotto:</b> la Fed può rallentare."),
        ("Mer 25, 14:30", "Pil USA del terzo trimestre (seconda stima)", "Prima stima +3,4% annualizzato", "Tenuta dell'economia",
         "<b>Sopra:</b> spazio per i rialzi.<br/><b>Sotto:</b> più timori sulla crescita."),
        ("Gio 26", "Borse e Treasury USA chiusi per il Ringraziamento", "Nessun dato", "Liquidità ridotta",
         "Gli scambi si spostano in Europa e i movimenti possono essere più bruschi."),
    ],
    "moduli": [
        {"chiave": "chip", "tema": "Chip", "breve": "i chip perdono la fiducia",
         "titolo": "Per Nvidia i conti non bastano più: a pesare sono la SEC e Huang",
         "misura": "doppio",
         "grafico": {"tipo": "barre", "file": "c_settori.png", "dati": SETTORI, "ordina": False, "dec": 1,
                     "soggetto": "Nvidia", "ruolo": "quanto", "unita": "%",
                     "titolo": "Reggono solo i consumi di base: la tecnologia perde il 5,3%",
                     "sottotitolo": "Variazione media dei titoli quotati al Nasdaq, per settore, 20/11"},
         "grafico2": {"tipo": "linee", "file": "c_nasdaq.png", "x": [d(x) for x, _ in NASDAQ[3:]],
                      "serie": [("Nasdaq", [v for _, v in NASDAQ[3:]], "#111111")], "soggetto": "Nvidia", "ruolo": "storia",
                      "titolo": "Il Nasdaq perde il 10% in cinque sedute",
                      "sottotitolo": "Nasdaq Composite, chiusure, punti",
                      "eventi": [(d("11-19"), "Debutto di Anthropic")]},
         "righe": [["Anthropic (ANT)", "Dollari", "Dove si colloca"],
                   ["Prezzo di collocamento", "83,00", "Base di partenza"],
                   ["Apertura di giovedì", "111,50", "+34% sul collocamento"],
                   ["Chiusura di giovedì", "97,17", "Sale del 17%"],
                   ["Chiusura di venerdì", "88,91", "-8,5%, ancora sopra 83"]],
         "larghezze": [50, 30, 66], "ruolo_righe": "chi",
         "perche": "Le vendite di venerdì seguono la notizia che, secondo Reuters, lo staff della SEC che controlla il rispetto delle regole esamina possibili problemi contabili di Nvidia: il titolo è crollato. Il dubbio non riguarda la domanda di chip, ma l'affidabilità dei conti che la raccontano. Per questo anche un buon trimestre non basta a rassicurare chi ha comprato il titolo vicino ai massimi, e le vendite si estendono ai fornitori e alle società collegate.",
         "numero": "17: i trimestri di fila in cui Nvidia ha battuto le stime di ricavi, anche nell'ultimo conto. Non è bastato a fermare il titolo.",
         "quindi": "Alle 15:30 si vede se Anthropic resta sopra gli 83 $ del collocamento: sotto, chi ha comprato all'offerta è in perdita.",
         "testo": ["Il debutto che doveva dire se la domanda di intelligenza artificiale regge non ha fermato nulla. "
                   "Anthropic ha aperto giovedì a 111,50 $ e venerdì ha chiuso a 88,91, sopra gli 83 del collocamento ma "
                   "lontana dai massimi, mentre Nvidia crollava (Yahoo Finance).",
                   "Per Nvidia il problema non sono più i numeri. L'ultima trimestrale ha battuto ancora le stime di ricavi, "
                   "eppure il titolo è sceso. Pesano l'uscita di Jensen Huang e l'indagine della SEC, riferita martedì dal Wall Street Journal. Venerdì Reuters ha scritto che l'esame, in mano allo staff che controlla l'applicazione delle regole, riguarda possibili problemi contabili. A nostro avviso il mercato non sconta più una cattiva notizia sulla "
                   "domanda, ma un dubbio sull'affidabilità di chi la racconta.",
                   "I listini di Seul e Tokyo, dove poche società di chip pesano molto negli indici, avevano già "
                   "venduto in mattinata. Il contagio ha poi superato i semiconduttori: il bitcoin è sceso sotto i 59.000 "
                   "dollari e le società che lo estraggono hanno perso fino al 18,6% (CoinDesk).",
                   "Il calo ha toccato quasi tutto il listino tecnologico: nel Nasdaq la tecnologia è il settore che perde di più. Reggono solo i consumi di base, il settore meno legato ai chip e alla corsa dell'intelligenza artificiale."],
         "fonte": "Fonti: Yahoo Finance, CoinDesk, Reuters, Investing.com, comunicati e serie di mercato.",
         "guardare": "Decidono le notizie sull'indagine. Un chiarimento della SEC, o un rimbalzo dei chip senza novità "
                     "sui conti, direbbe che il timore era soprattutto di mercato; altre rivelazioni sui bilanci "
                     "confermerebbero un problema di fiducia."},
        {"chiave": "fed", "tema": "Fed", "breve": "la Fed non soccorre la borsa",
         "titolo": "La Fed ha l'inflazione contro e non può soccorrere la borsa",
         "misura": "doppio",
         "grafico": {"tipo": "linee", "file": "c_ust.png", "x": [d(x) for x in UST_X], "soggetto": "Fed", "ruolo": "storia",
                     "serie": [("Treasury a 10 anni", [UST10[x] for x in UST_X], "#F26B1D"),
                               ("Treasury a 2 anni", [UST2[x] for x in UST_X], "#111111")],
                     "titolo": "Il crollo abbassa i rendimenti, ma il 2 anni resta sopra il 4,5%",
                     "sottotitolo": "Rendimenti dei Treasury, chiusure (%)",
                     "eventi": [(d("11-18"), "Verbali Fed")]},
         "righe": [["Chi", "Cosa ha detto", "Quando"],
                   ["Christopher Waller, governatore", "A dicembre serve un rialzo da mezzo punto o un segnale chiaro di rialzi più rapidi", "Mer 18"],
                   ["Verbali della riunione del 27-28 ottobre", "Quasi tutti giudicano probabili altri rialzi (Newsquawk)", "Mer 18"],
                   ["Prossima riunione (FOMC, comitato Fed che decide i tassi)", "L'8 e 9 dicembre, con le nuove proiezioni", "Dic"]],
         "larghezze": [44, 100, 20], "ruolo_righe": "chi",
         "perche": "Waller, in un'intervista alla CNBC, chiede per dicembre una mossa decisa (Reuters). Il rendimento a 2 anni, sceso ma ancora sopra i tassi attuali, indica che il mercato non esclude altri rialzi.",
         "numero": "",
         "quindi": "Mercoledì alle 14:30 il PCE (inflazione dei consumi, misura Fed): il core (esclusi energia e alimentari) sopra il 3,2% atteso rafforza chi vuole mezzo punto.",
         "testo": ["Nel giorno del crollo il rendimento del Treasury a 2 anni è sceso di 13 punti base. Quel titolo "
                   "tende a seguire le attese sulla Fed: se scende, chi lo compra pensa che i rialzi si fermeranno prima "
                   "o saranno più piccoli. Non dice però che la Fed abbia smesso di volerli. A 4,63% resta sopra la fascia dei tassi "
                   "Fed, tra il 3,75% e il 4%. A nostro avviso il mercato continua a mettere in conto altri rialzi, "
                   "anche dopo il crollo.",
                   "Per la banca centrale è una posizione scomoda. Fermarsi per sostenere la borsa sembrerebbe "
                   "un cedimento davanti a prezzi che salgono ancora, ed è un rischio che la Fed conosce. Chi voleva "
                   "già un rialzo a ottobre, quando i tassi sono rimasti fermi, ha ora argomenti in più (Newsquawk).",
                   "La scelta di dicembre è tra due strade, e Waller le ha dette chiaramente: o mezzo punto subito, o una "
                   "comunicazione che renda credibili rialzi più rapidi. Senza uno dei due segnali, ha spiegato, "
                   "bisognerebbe fare mezzo punto (Reuters).",
                   "Il quadro di partenza è quello dei verbali. Il 27-28 ottobre la Fed ha lasciato i tassi fermi tra "
                   "il 3,75% e il 4%. Alcuni membri volevano già un rialzo da un quarto di punto, e un paio ha detto "
                   "che a dicembre potrebbe servire di più se i dati sui prezzi deludono (Newsquawk).",
                   "Prima dell'8-9 dicembre, quando la Fed pubblicherà anche le nuove proiezioni, c'è un solo dato che "
                   "può cambiare i conti: il PCE di mercoledì, atteso a +0,3% sul mese. Lo stesso giorno il Pil del "
                   "terzo trimestre, con una prima stima a +3,4%, aggiunge una seconda lettura sulla tenuta dell'economia, e su quanto la Fed possa permettersi di aspettare."],
         "fonte": "Fonti: Federal Reserve (calendario), Reuters, Newsquawk, serie del Tesoro USA via FMP.",
         "guardare": "Contano il PCE di mercoledì e le parole della Fed prima dell'8-9 dicembre. Un dato sotto le attese "
                     "darebbe ragione a chi spera in rialzi più piccoli; uno sopra rafforza i toni duri. A nostro avviso conta anche se altri governatori si schiereranno con Waller, perché una linea condivisa pesa più di una voce sola nel comitato che decide."},
        {"chiave": "oro", "tema": "Materie prime", "breve": "l'oro non fa da rifugio",
         "titolo": "L'oro non fa da rifugio: scende mentre i Treasury salgono",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_oro.png", "x": [d(x) for x, _ in ORO], "soggetto": "oro", "ruolo": "storia",
                     "serie": [("Oro future", [v for _, v in ORO], "#F26B1D")],
                     "titolo": "Dal 10 novembre l'oro future ha perso più di 500 dollari",
                     "sottotitolo": "Oro future, chiusure ($)"},
         "numero": "3,8%: quanto ha perso l'argento spot nella stessa seduta (Kitco), più dell'oro.",
         "perche": "A nostro avviso il calo viene da vendite per far cassa e dall'attesa di altri rialzi Fed. Non è una fuga verso la sicurezza: quella ha premiato i titoli di Stato (Kitco).",
         "quindi": "Se lunedì l'oro risale mentre le borse restano giù, la lettura delle vendite per far cassa perde forza e torna in primo piano la paura.",
         "testo": ["Un rifugio dovrebbe salire quando si ha paura, e invece l'oro ha seguito le azioni, e il future ha chiuso a 3.515,4 dollari contro i 3.685,5 di giovedì. Nella stessa "
                   "seduta i Treasury hanno guadagnato: il 10 anni è sceso al 4,92%, il segnale che chi cerca riparo "
                   "sceglie i titoli di Stato.",
                   "L'oro non paga interessi, e con rialzi Fed più probabili costa di più tenerlo. In un crollo rapido, "
                   "poi, chi ha perdite altrove tende a vendere ciò che si vende bene per coprirle, e l'oro è tra i "
                   "mercati più liquidi.",
                   "Il movimento di venerdì chiude una settimana già pesante. L'oro era già sceso di circa il 9% nella settimana, ai minimi da settembre 2025 (Milano Finanza), e venerdì ha cambiato poco che a Wall Street cadessero "
                   "insieme le azioni. Anche il bitcoin, che non rende interessi, è sceso sotto i 59.000 dollari (CoinDesk).",
                   "La differenza con le crisi in cui l'oro sale sta nell'origine della paura. Qui il timore viene da "
                   "prezzi alti e rialzi Fed più probabili. Un oro che non rende interessi ne soffre; a nostro avviso "
                   "è per questo che il rifugio, stavolta, è stato il titolo di Stato."],
         "fonte": "Fonti: Kitco, Investing.com, serie FMP."},
        {"chiave": "europa", "tema": "Europa", "breve": "l'Europa non fa da rifugio",
         "titolo": "L'Europa non fa da rifugio: perde il 7% in cinque sedute",
         "misura": "mezzo",
         "righe": [["Titolo", "Seduta del 20/11", "Settore"],
                   ["STMicroelectronics", "-10,78%", "Chip"],
                   ["Technoprobe", "-9,31%", "Chip"],
                   ["Prysmian", "-6,29%", "Cavi"],
                   ["Intesa Sanpaolo", "-2,41%", "Banche"],
                   ["Italgas", "+1,08%", "Gas"]],
         "larghezze": [50, 40, 30], "ruolo_righe": "quanto",
         "perche": "In Europa cadono per primi i produttori di chip, e a Milano anche le banche, che cedono tra il 2,2% e il 3% (Teleborsa).",
         "quindi": "Alle 10:00 il PMI flash dell'area euro dice quanto l'attività regge dopo il crollo.",
         "testo": ["L'Euro Stoxx 50 chiude ai minimi da maggio, in calo di circa il 7% nella settimana. "
                   "ASML cede il 9,3% (dpa-AFX). A Milano il FTSE MIB scende sotto quota 49mila: 33 titoli su 40 perdono e solo pochi difensivi, "
                   "come Italgas e Saipem, resistono.",
                   "Il paradosso è che l'Europa ha pochi titoli di intelligenza artificiale. Ciò non è bastato a proteggerla: quando il prezzo dei chip crolla, cadono anche i fornitori e le società che li usano.",
                   "Francoforte cede il 2,6%, Parigi l'1,9% e Londra l'1,0%: il listino britannico, con meno tecnologia, "
                   "tiene meglio. Lo spread tra BTP e Bund chiude a 109,9 punti base, da 103 in apertura, e il rendimento "
                   "italiano è intorno al 4,4% (ANSA)."],
         "fonte": "Fonti: ANSA, Teleborsa, dpa-AFX, Money.it."},
    ],
    "scommessa": {"tesi": "", "lunedi": True, "venerdi": False, "settimana_prec": "16-20 novembre",
                  "com_e_andata": "Il crollo di venerdì ha rovesciato la settimana: i conti di Nvidia e i verbali non hanno ridato fiducia alle borse."},
    "parole": [("Correzione", "Un calo di oltre il 10% da un massimo recente: un'indicazione di nervosismo, non ancora di crisi."),
               ("VIX", "L'indice della volatilità attesa a Wall Street: sale quando si teme che i prezzi si muovano molto."),
               ("PCE", "L'indice dei prezzi dei consumi americani: è quello che la Fed guarda di più."),
               ("Vendite forzate", "Vendite fatte non perché si vuole, ma per coprire perdite o richieste di denaro altrove."),
               ("Collocamento", "Il prezzo a cui una società vende le azioni agli investitori al debutto in Borsa."),
               ("Rendimento a 2 anni", "Il tasso dei titoli di Stato a breve scadenza: segue le attese sulla Fed.")],
    "fonti": [
        ("Dati di mercato", "Financial Modeling Prep (indici USA e Asia, VIX, Brent e oro future, curva del Tesoro USA); "
                            "Alpha Vantage (EUR/USD, ACWI); EODHD e dpa-AFX (Euro Stoxx 50); ANSA e Teleborsa (FTSE MIB, spread BTP-Bund); Yonhap (Kospi)."),
        ("Prima pagina e mercati", "Yahoo Finance, CoinDesk, Reuters, Investing.com, ANSA, Teleborsa, RTHK, IANS."),
        ("Calendario e agenda", "Federal Reserve, Newsquawk, MUFG Research, LiteFinance, FinancialJuice."),
        ("Approfondimenti", "Chip: Yahoo Finance, CoinDesk, Reuters. Fed: Federal Reserve, Reuters, Newsquawk. "
                            "Oro: Kitco, Investing.com. Europa: ANSA, Teleborsa, dpa-AFX."),
        ("La scommessa", "Chiusure di FMP, Alpha Vantage ed EODHD; forchette calcolate dalla volatilità delle ultime 20 sedute."),
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
