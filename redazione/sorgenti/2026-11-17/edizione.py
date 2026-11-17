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
- Lunedì: "ieri" = la settimana scorsa, in 3 righe al massimo; 1 sett. del cruscotto = settimana intera.
- parole: 6 concetti (non sigle) del numero, in ordine di importanza: il motore ne mostra 3 o 6."""
import datetime as dt
import json
import os
import sys

REPO = os.path.join(os.environ.get("GTD_REPO", "/home/claude/gtd"), "redazione")   # kit e registri (mai la copia)
sys.path.insert(0, REPO)
from gommberg_engine import *  # noqa: E402,F403
from numeri import ticker_da_dati  # noqa: E402

LAVORO = sys.argv[1] if len(sys.argv) > 1 else "."
USCITA = sys.argv[2] if len(sys.argv) > 2 else None
os.chdir(LAVORO)   # grafici e c_forecast.png stanno qui

# =============================== CONTENUTI DEL GIORNO ===============================
from numeri import fmt, var as VAR   # noqa: E402
OGGI = dt.date(2026, 11, 17)
NOTA_DATI = "Chiusure al 16 novembre; mattina del 17 novembre dove indicato"
REG = "2026-11-16-settimana.json"
d = lambda s: dt.date(2026, int(s[:2]), int(s[3:]))

NASDAQ = [("10-14", 26692.87), ("10-15", 26713.03), ("10-16", 26140.03), ("10-19", 26430.89), ("10-20", 26424.82), ("10-21", 26702.86),
          ("10-22", 26008.86), ("10-23", 25955.34), ("10-26", 26169.38), ("10-27", 26477.81), ("10-28", 26549.85), ("10-29", 26184.72),
          ("10-30", 25437.0), ("11-02", 25164.32), ("11-03", 25372.01), ("11-04", 25736.51), ("11-05", 24315.0), ("11-06", 24579.42),
          ("11-09", 25253.14), ("11-10", 25065.87), ("11-11", 25466.19), ("11-12", 25366.09), ("11-13", 25136.27), ("11-16", 24509.76)]
BRENT = [("10-14", 106.06), ("10-15", 105.92), ("10-16", 109.86), ("10-19", 109.55), ("10-20", 108.79), ("10-21", 108.82), ("10-22", 113.17),
         ("10-23", 116.72), ("10-26", 115.81), ("10-27", 113.88), ("10-28", 115.32), ("10-29", 110.8), ("10-30", 113.43), ("11-02", 104.77),
         ("11-03", 103.6), ("11-04", 94.62), ("11-05", 98.29), ("11-06", 98.32), ("11-09", 92.57), ("11-10", 91.49), ("11-11", 92.76),
         ("11-12", 95.82), ("11-13", 95.84), ("11-16", 92.44)]
ORO = [("10-14", 4107.9), ("10-15", 4170.1), ("10-16", 4181.1), ("10-19", 4160.1), ("10-20", 4142.6), ("10-21", 4150.0), ("10-22", 4060.4),
       ("10-23", 4007.9), ("10-26", 4038.4), ("10-27", 4074.6), ("10-28", 4051.6), ("10-29", 4031.4), ("10-30", 3898.9), ("11-02", 3969.6),
       ("11-03", 3940.4), ("11-04", 4073.0), ("11-05", 4113.5), ("11-06", 4074.9), ("11-09", 4114.5), ("11-10", 4030.2), ("11-11", 4000.5),
       ("11-12", 3885.3), ("11-13", 3886.3), ("11-16", 3853.0)]
CURVA_13 = {"1M": 4.10, "2M": 4.26, "3M": 4.32, "6M": 4.42, "1A": 4.65, "2A": 4.88, "3A": 4.92, "5A": 4.98, "7A": 5.05, "10A": 5.15, "20A": 5.52, "30A": 5.47}
CURVA_16 = {"1M": 4.10, "2M": 4.27, "3M": 4.34, "6M": 4.42, "1A": 4.62, "2A": 4.83, "3A": 4.87, "5A": 4.93, "7A": 5.01, "10A": 5.12, "20A": 5.51, "30A": 5.46}

C = {
    "data": OGGI,
    "temi": ["Chip", "Fed", "Tassi", "Valute", "Petrolio", "Europa"],
    "glossario": ["VIX", "CME FedWatch", "IPO", "Kospi", "pb"],
    "meccanismi": ["M15", "M16", "M17", "M20", "M26", "M23", "M09", "M10", "M11"],
    "ticker": ticker_da_dati("dati.json"),

    "top": {
        "tema": "Chip",
        "titolo": "La paura per l'AI colpisce Wall Street, stasera tocca ai conti Nvidia",
        "dek": "Il Nasdaq perde il 2,5% e l'S&amp;P 500 l'1,9%, con Nvidia in calo del 4,1% dopo le dimissioni di Jensen Huang "
               "da amministratore delegato. Pesano anche le nuove regole USA che limitano l'accesso della Cina ai chip avanzati (Reuters), "
               "e stamattina Seul chiude sotto quota 5.000, ai minimi da nove mesi. Stasera a mercati chiusi i conti di "
               "Nvidia, i primi senza Huang. [[chip]]",
        "freccia": "Il ministro del Tesoro Bessent chiede al consiglio di Nvidia «un cambiamento radicale» al vertice (Radiocor).",
    },
    "quadro": "Lunedì i prezzi parlano di paura più che di inflazione. Per noi i Treasury tornano rifugio: il 2 anni scende di 5 pb "
              "anche con il rialzo Fed di dicembre quasi scontato. Il VIX (volatilità attesa sull'S&amp;P 500) sale a 22,91, il "
              "livello più alto dal 6 novembre. L'oro cede e il dollaro sale, come spesso accade quando i tassi restano alti.",
    "in30": [
        "Il petrolio cade: il mercato guarda all'offerta in eccesso più che agli attacchi alle navi. [[petrolio]]",
        "Mercoledì i verbali della Fed: il rialzo di dicembre è già nei prezzi. [[tassi]]",
        "A Milano Igd sale con l'offerta di Carmila, mentre Stellantis perde. [[europa]]",
    ],
    "in30_temi": ["Petrolio", "Fed", "Italia"],
    "stamattina": [
        "Seul alla chiusura (07:30): Kospi 4.968,48, -2,59%",
        "Future sull'Euro Stoxx 50 alle 07:30: -0,7% (Milano Finanza)",
        "EUR/USD alle 09:04: 1,0998",
    ],
    "notizie": [
        {"tag": "Petrolio", "titolo": "L'Agenzia internazionale dell'energia passa dal deficit all'eccesso di offerta",
         "testo": "Per il quarto trimestre prima si stimava che il petrolio sarebbe mancato; ora il mercato ne avrebbe più della domanda (Reuters).",
         "rimando": "petrolio"},
        {"tag": "Geopolitica", "titolo": "Le Guardie della Rivoluzione dicono che due petroliere hanno colpito mine a Hormuz",
         "testo": "Secondo i pasdaran sei navi hanno preso fuoco tra domenica e lunedì; Reuters non ha potuto verificare.",
         "rimando": "petrolio"},
        {"tag": "Cina", "titolo": "Trump comincia il viaggio in Cina per incontrare Xi Jinping",
         "testo": "Parte nelle ore in cui Washington stringe l'accesso cinese ai chip avanzati (Reuters)."},
        {"tag": "Italia", "titolo": "Igd sale con l'offerta di Carmila, Stellantis e Technoprobe perdono",
         "testo": "L'offerta pubblica di scambio di Carmila spinge Igd, mentre Technoprobe cede per il pessimismo sull'AI (Teleborsa).",
         "rimando": "europa"},
        {"tag": "Europa", "titolo": "Zurigo tocca un record e chiude in rialzo mentre l'Europa cede",
         "testo": "L'indice svizzero SMI finisce in rialzo dopo il record, mentre l'Euro Stoxx 50 perde (dpa-AFX).",
         "rimando": "europa"},
        {"tag": "Tecnologia", "titolo": "Anthropic debutta al Nasdaq giovedì, e c'è chi frena",
         "testo": "Gli analisti di Acatis si chiedono perché abbia bisogno di capitale e la paragonano a «fare scorta di "
                  "provviste in tutta fretta» (Radiocor).", "rimando": "chip"},
    ],

    "mercati_titolo": "Numeri, temi aperti e calendario",
    "cruscotto": [
        ("Mondo e Stati Uniti", [["MSCI ACWI (ETF, $)", "153,00", "16/11", "-2,0%", "-", "-"],
                                 ["S&amp;P 500", "7.416,59", "16/11", "-1,9%", "-1,8%", "+8,3%"],
                                 ["Nasdaq Comp.", "24.509,76", "16/11", "-2,5%", "-2,9%", "+5,5%"],
                                 ["Russell 2000", "2.742,94", "16/11", "-1,7%", "-3,4%", "+10,5%"]]),
        ("Europa", [["Euro Stoxx 50", "6.348,35", "16/11", "-0,6%", "+0,9%", "+9,5%"],
                    ["FTSE MIB", "51.521", "16/11", "-0,6%", "-", "-"]]),
        ("Asia (17/11)", [["Nikkei 225", "n.d.", "17/11", "-", "-", "-"],
                          ["Hang Seng", "n.d.", "17/11", "-", "-", "-"],
                          ["Kospi", "4.968,48", "17/11", "-2,6%", "-", "-"]]),
    ],
    "cruscotto_nota": "1 g = chiusura su chiusura; 1 sett. = su lunedì 9/11; da inizio anno = su chiusura 2025. "
                      "- = dato non disponibile oggi. Tokyo e Hong Kong: fonti discordanti sull'orario della seduta.",
    "cross_data": "Livello 16/11",
    "cross": [
        ("Tassi", [["Treasury 2 anni", "4,83%", "-5 pb", "+27 pb", "+9 pb", "-"],
                   ["Treasury 10 anni", "5,12%", "-3 pb", "+24 pb", "+3 pb", "-"],
                   ["Spread Italia", "105 pb", "0 pb", "-", "-", "10 anni italiano al 4,43% (Teleborsa)"]]),
        ("Cambi", [["EUR/USD", "1,0996", "-0,2%", "-2,0%", "-2,2%", "Minimo da quattro mesi e mezzo [[oro]]"]]),
        ("Materie prime", [["Brent future", "92,44 $", "-3,5%", "-0,1%", "-15,9%", "-"],
                           ["Oro (future, $/oncia)", "3.853,00", "-0,9%", "-6,4%", "-7,8%", "-"]]),
        ("Volatilità", [["VIX (volatilità attesa)", "22,91", "+3,61", "+2,99", "+2,92", "Massimo dal 6/11"]]),
    ],
    "cross_nota": "1 mese = sul 16/10. VIX = volatilità attesa sull'S&amp;P 500.",
    "termometri": [
        ("AI e chip", "Conti Nvidia stasera", "La vendita arriva a Wall Street", "giu: Titoli dell'AI, da Seul a New York", "Conti alle 23:00"),
        ("Fed e tassi", "Verbali mercoledì", "Rialzo di dicembre già nei prezzi", "giu: Rendimenti a 2 e 10 anni, per la paura", "Verbali, mer 18 alle 20:00"),
        ("Dollaro e oro", "Euro ai minimi da mesi", "Oro in calo con il dollaro forte", "giu: Oro e euro", "Verbali Fed"),
        ("Petrolio", "Eccesso di offerta", "Il Brent scende sotto 93 $", "giu: Brent", "Flussi da Hormuz"),
    ],
    "fermi": "Cina (dati d'ottobre usciti lunedì, nessuna novità verificata oggi); Iran e Hormuz (nuovi attacchi alle navi dichiarati dai pasdaran, non verificati da Reuters).",
    "lettura": "Su una settimana le tabelle dicono qualcosa che ieri non si vedeva. Il Treasury a 2 anni resta 27 pb più alto di "
               "lunedì scorso, quindi il rifugio di ieri ha cancellato solo una piccola parte del rialzo dei tassi. Il Nasdaq "
               "perde più dell'S&amp;P 500, segno che a soffrire sono i titoli dell'AI più dell'intero mercato. E il Russell "
               "2000, l'indice delle società più piccole, cede ieri meno dell'S&amp;P 500 ma in sette giorni quasi il doppio: la "
               "settimana non è stata solo una questione di chip.",

    "ieri": [
        ("Lun 16", "Discorso del presidente Fed Warsh", "Parla di AI, nessun commento sui tassi (Newsquawk)", "", "[[tassi]]"),
    ],
    "agenda": [
        ("<b>Mar 17, 14:30</b>", "<b>Vendite al dettaglio USA (ottobre)</b>", "<b>+0,2% sul mese; prima +0,8%</b>",
         "<b>Evento n.1:</b> consumi con prezzi alti e Fed che alza",
         "<b>Sopra:</b> di solito salgono dollaro e rendimenti a breve: consumi forti lasciano spazio alla Fed.<br/>"
         "<b>Sotto:</b> il rialzo di dicembre perde un po' di forza e i rendimenti tendono a scendere."),
        ("Mar 17, 23:00", "Conti Nvidia (terzo trimestre fiscale)", "Utile e ricavi contro le stime; primi senza Huang",
         "Primi conti e prime previsioni dopo l'addio di Huang",
         "<b>Sopra:</b> di solito il titolo recupera, ma contano più le previsioni dell'azienda per i prossimi mesi.<br/>"
         "<b>Sotto:</b> la vendita sui chip può allargarsi."),
        ("Mer 18, 20:00", "Verbali della Fed (riunione 27-28 ottobre)", "Tassi lasciati al 3,75-4,00%; rialzo di dicembre atteso",
         "Quanto la Fed è vicina al rialzo",
         "<b>Più duri:</b> di solito salgono rendimenti a breve e dollaro.<br/><b>Più cauti:</b> i rendimenti tendono a scendere."),
        ("Gio 19", "Debutto di Anthropic al Nasdaq", "Primo giorno di scambi",
         "Secondo test per l'AI dopo Nvidia",
         "<b>Forte:</b> di solito rilancia i titoli dell'AI.<br/><b>Debole:</b> rafforza i dubbi sul valore del settore."),
    ],

    "moduli": [
        {"chiave": "chip", "tema": "Chip e AI", "breve": "la vendita arriva a Wall Street",
         "titolo": "La vendita sull'AI si allarga e a Wall Street perdono i settori in blocco",
         "misura": "doppio",
         "grafico": {"tipo": "barre", "file": "c_chip.png", "dec": 1, "ordina": False, "unita": "%", "soggetto": "AI", "ruolo": "quanto",
                     "dati": [("Industriali", -1.5), ("Materiali", -1.4), ("Tecnologia", -1.4), ("Energia", -1.3), ("Sanità", -1.2),
                              ("Consumi ciclici", -1.0), ("Comunicazioni", -0.9), ("Immobiliare", -0.7), ("Consumi difensivi", -0.6),
                              ("Finanza", -0.1), ("Utility", -0.1)],
                     "titolo": "La vendita sull'AI è larga: in media perdono i titoli di ogni settore",
                     "sottotitolo": "variazione media dei titoli del Nyse per settore, chiusura del 16/11 (%)"},
         "grafico2": {"tipo": "linee", "file": "c_nasdaq.png", "x": [d(x) for x, _ in NASDAQ],
                      "serie": [("Nasdaq", [v for _, v in NASDAQ], "#111111")], "soggetto": "Nvidia", "ruolo": "storia",
                      "titolo": "Il Nasdaq perde il 7,7% dal massimo del 28 ottobre", "sottotitolo": "Nasdaq Composite, punti",
                      "note": [(d("10-28"), 26549.85, "28/10"), (d("11-16"), 24509.76, "16/11")]},
         "perche": "Pesano insieme due dubbi: chi guiderà Nvidia dopo Huang e se la spesa in AI renderà abbastanza (Reuters). "
                   "Nvidia ha la serie settimanale di perdite più lunga dall'ottobre 2012, e ieri sono arrivate anche le regole USA "
                   "sull'accesso cinese ai chip.",
         "numero": "-735 miliardi di dollari: il valore che Nvidia ha perso dalle rivelazioni su Huang (AP). Per noi è il conto "
                   "della fiducia, più che dei conti trimestrali.",
         "quindi": "Alle 23:00 di stasera la conference call di Nvidia dice se la domanda di chip regge; giovedì il debutto di "
                   "Anthropic al Nasdaq è il secondo test.",
         "punti": ["<b>Il fornitore.</b> A Seul gli stranieri vendono 1.440 miliardi di won netti, mentre istituzionali e privati "
                   "comprano.",
                   "<b>La regia.</b> Il Financial Times scrive che Huang lavora per rientrare, e Trump non si opporrebbe a un suo "
                   "ritorno (Reuters)."],
         "testo": ["Un titolo guarda avanti: chi compra Nvidia paga oggi gli utili che si aspetta tra qualche anno. Se cambia "
                   "l'incertezza su chi la guida, o su quanto i clienti continueranno a spendere, il prezzo si rifà da capo, "
                   "anche prima dei conti. Per questo la vendita non si ferma a Nvidia: chi fa memorie, server e servizi cloud "
                   "per l'AI vive della stessa spesa, e il dubbio riguarda tutti.",
                   "In Asia l'effetto è più forte dove i chip pesano di più sull'indice. A Seul Samsung perde il 3,3% e SK hynix "
                   "il 2%: pochi titoli muovono molto il Kospi, che chiude sotto 5.000, ai minimi da nove mesi.",
                   "A Wall Street la vendita è larga: in media i titoli del Nyse perdono in quasi tutti i settori. Più degli "
                   "altri calano industriali e materiali, meno la finanza e le utility. Non è più solo una questione di chip: "
                   "quando una spesa così grande viene messa in dubbio, il dubbio arriva anche a chi la sostiene. E finché non è chiaro chi guida Nvidia, per i mercati ogni notizia sul "
                   "vertice pesa quanto un dato sui conti."],
         "fonte": "Fonti: Reuters, AP, Korea Herald, Radiocor.",
         "guardare": "Se i conti battono le attese ma il titolo cade lo stesso, la vendita non riguarda più i risultati. Se "
                     "Nvidia recupera e i chip americani la seguono, quella di ieri può restare una tappa. Domattina l'Asia dice "
                     "quale delle due."},
        {"chiave": "tassi", "tema": "Tassi USA", "breve": "rifugio con la Fed che alza",
         "titolo": "Con la paura i Treasury tornano rifugio, anche con la Fed pronta ad alzare",
         "misura": "mezzo",
         "grafico": {"tipo": "barre", "file": "c_curva.png", "dati": [(k, round((CURVA_16[k] - CURVA_13[k]) * 100)) for k in CURVA_16],
                     "titolo": "Il breve scende più del lungo", "sottotitolo": "Curva Treasury, variazione del 16/11 (pb)",
                     "unita": " pb", "dec": 0, "ordina": False, "soggetto": "Treasury", "ruolo": "quanto"},
         "perche": "Di solito chi ha paura compra Treasury: il loro prezzo sale e il rendimento scende. Lunedì è successo mentre i "
                   "future sui tassi davano per fatto il rialzo di dicembre (Reuters), e per noi il rifugio pesa più della Fed.",
         "numero": "+27 pb: di quanto il 2 anni è più alto di lunedì scorso, da 4,56% a 4,83%. Il rifugio di ieri ne ha cancellati solo 5.",
         "quindi": "Mercoledì alle 20:00 i verbali dicono quanto la Fed è vicina al rialzo: se sono duri, il 2 anni può tornare "
                   "sopra il 4,88% di venerdì.",
         "testo": ["Il 2 anni segue le attese sui tassi della Fed, il 10 anni guarda anche a crescita e prezzi. Lunedì il breve ha perso 5 pb "
                   "e il lungo 3. Scende di più chi guarda alla Fed: è la mossa tipica di chi si mette al riparo e non di chi si "
                   "aspetta tassi più bassi.",
                   "Il rialzo di dicembre è già nei prezzi: per i future sui tassi (CME FedWatch) è quasi certo. La "
                   "probabilità di uno da 50 pb è circa il 9%. Quando una mossa è scontata, a muovere i rendimenti è ciò che la "
                   "Fed dice sul dopo, non la mossa in sé.",
                   "In una settimana il rendimento a 10 anni è salito di 24 pb, da 4,88% a 5,12%, e il passo indietro di lunedì "
                   "ne ha restituiti solo 3. Chi presta al governo americano per due anni chiede ancora molto di più di una "
                   "settimana fa. È il segno che la Fed resta il tema di fondo anche nei giorni di paura."],
         "fonte": "Fonti: curva par del Tesoro USA (FMP), Reuters.",
         "guardare": "Se i verbali parlano di inflazione più larga, il rifugio può non bastare: rendimenti su anche con la borsa "
                     "giù. Se parlano di rischi per la crescita, il 2 anni può scendere ancora."},
        {"chiave": "oro", "tema": "Dollaro e oro", "breve": "l'oro non fa da rifugio",
         "titolo": "Con il dollaro forte l'oro non fa da rifugio",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_oro.png", "x": [d(x) for x, _ in ORO], "soggetto": "oro", "ruolo": "storia",
                     "serie": [("Oro", [v for _, v in ORO], "#F26B1D")],
                     "titolo": "L'oro perde il 6,4% in una settimana", "sottotitolo": "Oro future, chiusure ($)",
                     "note": [(d("11-09"), 4114.5, "9/11"), (d("11-16"), 3853.0, "16/11")]},
         "perche": "Per noi pesano tassi alti e dollaro forte: di solito un metallo che non paga interessi perde appeal quando i rendimenti "
                   "salgono. Ieri l'euro è sceso a 1,0996, il livello più basso da almeno quattro mesi e mezzo. Quando la paura sale "
                   "molti comprano prima dollari che oro: è la moneta in cui si tengono i titoli di Stato più sicuri, e ieri a "
                   "guadagnare è stato lui.",
         "quindi": "Se mercoledì i verbali Fed spingono ancora il dollaro, la soglia da guardare è il minimo di ieri sera, 3.853 $, la chiusura più bassa delle ultime cinque settimane.",
         "testo": ["L'oro non paga interessi: se un titolo di Stato americano rende il 5,12% senza rischi, tenere un metallo che "
                   "non dà niente costa di più. Per questo l'oro tende a soffrire quando i rendimenti salgono e il dollaro si "
                   "rafforza, anche nei giorni di paura. Ieri è successo di nuovo: la borsa scendeva e l'oro ha perso lo 0,9%.",
                   "In poche settimane il percorso si è rovesciato: il 16 ottobre l'oro valeva 4.181 dollari, ieri 3.853, il 7,8% "
                   "in meno. Intanto il dollaro ha guadagnato sull'euro: in un mese l'EUR/USD è passato da 1,1239 a 1,0996, "
                   "il 2,2% in meno. Un dollaro più caro rende l'oro più costoso per chi compra con altre valute, e di solito ne frena la "
                   "domanda. È uno dei motivi per cui il metallo non ha tenuto il passo della paura."],
         "fonte": "Fonti: FMP (oro future), Alpha Vantage (EUR/USD).",
         "guardare": "Un oro in recupero con il dollaro fermo direbbe che il rifugio è tornato. Un oro ancora in calo con la "
                     "borsa che scende confermerebbe che a comandare sono i tassi."},
        {"chiave": "europa", "tema": "Europa", "breve": "perde meno di Wall Street",
         "titolo": "Con meno AI nell'indice l'Europa perde meno di Wall Street",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_europa.png", "soggetto": "Europa", "ruolo": "quanto",
                     "x": [d(x) for x in ("11-06", "11-09", "11-10", "11-11", "11-12", "11-13", "11-16")],
                     "serie": [("S&amp;P 500", [100.0, 102.34, 101.96, 103.28, 102.92, 102.51, 100.54], "#111111"),
                               ("Euro Stoxx 50", [100.0, 101.94, 102.55, 103.61, 103.70, 103.51, 102.88], "#F26B1D")],
                     "titolo": "L'Europa tiene mentre Wall Street scende dal massimo dell'11 novembre",
                     "sottotitolo": "S&amp;P 500 e Euro Stoxx 50, chiusure, 6 novembre = 100"},
         "perche": "Per noi conta la composizione: gli indici americani sono più concentrati sulle grandi società tecnologiche, quindi "
                   "un calo dell'AI li colpisce più di quelli europei. Alla chiusura europea il Nasdaq 100 perdeva l'1,5% e l'indice "
                   "europeo dei titoli tecnologici l'1,3% (dpa-AFX). Per noi il banco di prova resta la serata di Nvidia, che dà il tono alla riapertura.",
         "quindi": "Oggi il test è la riapertura di Wall Street alle 15:30. Se il Nasdaq continua a scendere, l'Europa "
                   "difficilmente resta indietro, mentre la difesa che ieri ha sostenuto Milano è la prima cosa da controllare.",
         "testo": ["A Milano a pesare sono Stellantis, in calo del 3,9%, e Technoprobe, che perde il 4,2% per il pessimismo "
                   "sull'AI; la difesa tiene, con Leonardo in rialzo dello 0,9%."],
         "fonte": "Fonti: dpa-AFX, Radiocor, Teleborsa.",
         "guardare": "Se Wall Street recupera dopo i conti Nvidia l'Europa dovrebbe seguire; se il Nasdaq continua a scendere, il "
                     "vantaggio di ieri si riduce."},
        {"chiave": "petrolio", "tema": "Petrolio", "breve": "il Brent perde un quinto in tre settimane",
         "titolo": "Il petrolio cade: il mercato guarda all'eccesso di offerta",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_brent.png", "x": [d(x) for x, _ in BRENT], "soggetto": "petrolio", "ruolo": "storia",
                     "serie": [("Brent", [v for _, v in BRENT], "#F26B1D")],
                     "titolo": "Dal 23 ottobre il Brent ha perso più di un quinto", "sottotitolo": "Brent future, chiusure ($)",
                     "soglie": [(100, "100 $")], "note": [(d("10-23"), 116.72, "23/10"), (d("11-16"), 92.44, "16/11")]},
         "perche": "Segnali di recupero dei flussi da Hormuz rafforzano l'idea di un eccesso di offerta. L'Agenzia internazionale dell'energia ora prevede per il "
                   "quarto trimestre 1,7 milioni di barili al giorno di offerta in più della domanda (Reuters).",
         "quindi": "Il minimo recente è 91,49 $ del 10/11: da lì il Brent è rimbalzato a 95,82 $ in due giorni, e ieri ci è tornato vicino.",
         "numero": "-20,8%: il calo del Brent dal 23 ottobre a ieri sera. Il giorno più pesante è stato il 4 novembre, -8,7%.",
         "testo": ["Meno petrolio vuol dire meno inflazione, di solito con un po' di ritardo: i carburanti costano meno subito, i "
                   "prezzi di trasporti e beni ci mettono più tempo. Per la Fed che deve decidere a dicembre un Brent più basso "
                   "è un sollievo, anche se da solo non basta.",
                   "Intanto cambia anche la domanda: la lavorazione di greggio nelle raffinerie cinesi scende dell'8,1% su un anno e "
                   "implica scorte in aumento di circa 492 mila barili al giorno. Goldman Sachs vede il Brent a 88 "
                   "dollari in media il prossimo anno, ma avverte che gli attacchi alle navi tengono aperto il rischio di "
                   "rialzo nel breve."],
         "fonte": "Fonti: Reuters, Radiocor; chiusure del Brent future (FMP).",
         "guardare": "Un nuovo attacco che blocchi davvero i flussi smentirebbe la tesi; più petroliere che passano da Hormuz la "
                     "rafforzano."},
    ],

    "scommessa": {"tesi": "Con noi: la paura per l'AI spinge giù le borse americane, come previsto. Contro: petrolio e rendimenti "
                          "scendono invece di salire. Da qui a venerdì: conti di Nvidia e verbali della Fed.",
                  "lunedi": False, "venerdi": False, "settimana_prec": None},
    "parole": [("Acquisti rifugio", "Vendite di azioni e acquisti di titoli considerati sicuri, come Treasury e oro, quando "
                                    "cresce la paura."),
               ("Previsioni aziendali", "Ciò che un'azienda si aspetta per i prossimi trimestri: spesso contano più dei conti appena usciti."),
               ("Eccesso di offerta", "Quando si produce più petrolio di quanto se ne consuma: di solito i prezzi scendono."),
               ("VIX", "L'indice della volatilità attesa a Wall Street: sale quando gli investitori temono grandi oscillazioni."),
               ("Quotazione in borsa (IPO)", "Il debutto di un'azienda in borsa, con la vendita delle prime azioni al pubblico."),
               ("Curva dei rendimenti", "I rendimenti dei titoli di Stato messi in fila dal più breve al più lungo.")],
    "fonti": [
        ("Dati di mercato", "Financial Modeling Prep (indici USA, VIX, Brent e oro future, curva par del Tesoro USA); Alpha Vantage "
                            "(EUR/USD, ACWI); dpa-AFX (Euro Stoxx 50); Teleborsa (Ftse Mib, spread Btp-Bund); Korea Herald (Kospi)."),
        ("Prima pagina e mercati", "Reuters, MarketScreener, AP, Radiocor, Teleborsa, dpa-AFX, Korea Herald, Milano Finanza."),
        ("Calendario e agenda", "Newsquawk, Federal Reserve, documenti di Nvidia alla Securities and Exchange Commission."),
        ("Approfondimenti", "Chip e AI: Reuters, AP, Korea Herald. Tassi: curva par del Tesoro via FMP, Reuters. Oro: FMP, Alpha "
                            "Vantage. Europa: dpa-AFX, Radiocor, Teleborsa. Petrolio: Reuters, FMP."),
        ("La scommessa", "Chiusure di FMP, Alpha Vantage e dpa-AFX; forchette calcolate dalla volatilità delle ultime 20 sedute."),
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
