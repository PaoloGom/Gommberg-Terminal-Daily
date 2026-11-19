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
OGGI = dt.date(2026, 11, 19)
NOTA_DATI = "Chiusure al 18 novembre; mattina del 19 novembre dove indicato"
REG = "2026-11-16-settimana.json"

# ---- dati dei grafici (FMP, verificati il 19/11/2026) ----
SPX = [("10-19", 7690.73), ("10-20", 7712.57), ("10-21", 7757.17), ("10-22", 7663.43), ("10-23", 7623.68), ("10-26", 7676.77),
       ("10-27", 7722.60), ("10-28", 7743.98), ("10-29", 7720.39), ("10-30", 7580.07), ("11-02", 7541.40), ("11-03", 7568.92),
       ("11-04", 7688.62), ("11-05", 7353.73), ("11-06", 7376.86), ("11-09", 7549.94), ("11-10", 7520.93), ("11-11", 7619.38),
       ("11-12", 7592.40), ("11-13", 7561.67), ("11-16", 7416.59), ("11-17", 7340.53), ("11-18", 7323.63)]
ORO = [("10-19", 4160.1), ("10-20", 4142.6), ("10-21", 4150.0), ("10-22", 4060.4), ("10-23", 4007.9), ("10-26", 4038.4),
       ("10-27", 4074.6), ("10-28", 4051.6), ("10-29", 4031.4), ("10-30", 3898.9), ("11-02", 3969.6), ("11-03", 3940.4),
       ("11-04", 4073.0), ("11-05", 4113.5), ("11-06", 4074.9), ("11-09", 4114.5), ("11-10", 4030.2), ("11-11", 4000.5),
       ("11-12", 3885.3), ("11-13", 3886.3), ("11-16", 3853.0), ("11-17", 3864.2), ("11-18", 3741.9)]
# data, 2 anni, 10 anni, 30 anni (curva par del Tesoro via FMP)
UST = [("10-19", 4.77, 5.15, 5.48), ("10-20", 4.79, 5.12, 5.42), ("10-21", 4.81, 5.13, 5.42), ("10-22", 4.65, 4.96, 5.29),
       ("10-23", 4.69, 5.00, 5.33), ("10-26", 4.68, 5.00, 5.31), ("10-27", 4.70, 4.99, 5.30), ("10-28", 4.67, 5.05, 5.37),
       ("10-29", 4.61, 4.98, 5.32), ("10-30", 4.56, 4.94, 5.31), ("11-02", 4.59, 4.91, 5.28), ("11-03", 4.61, 4.95, 5.32),
       ("11-04", 4.58, 4.90, 5.28), ("11-05", 4.46, 4.84, 5.25), ("11-06", 4.51, 4.86, 5.26), ("11-09", 4.56, 4.88, 5.26),
       ("11-10", 4.73, 4.98, 5.35), ("11-12", 4.86, 5.10, 5.43), ("11-13", 4.88, 5.15, 5.47), ("11-16", 4.83, 5.12, 5.46),
       ("11-17", 4.80, 5.10, 5.46), ("11-18", 4.80, 5.07, 5.41)]
C17 = {"3M": 4.33, "6M": 4.41, "1A": 4.60, "2A": 4.80, "3A": 4.84, "5A": 4.90, "7A": 4.99, "10A": 5.10, "20A": 5.50, "30A": 5.46}
C18 = {"3M": 4.34, "6M": 4.43, "1A": 4.62, "2A": 4.80, "3A": 4.84, "5A": 4.89, "7A": 4.96, "10A": 5.07, "20A": 5.44, "30A": 5.41}
d = lambda s: dt.date(2026, int(s[:2]), int(s[3:]))   # "MM-GG" -> data

C = {
    "data": OGGI,
    "temi": ["Tecnologia", "Fed", "Valute", "Materie prime", "Asia", "Banche"],
    "glossario": ["IPO", "pb", "CMS", "VIX", "Ires", "BCE"],
    "meccanismi": ["M26", "M02", "M20", "M22", "M08", "M23", "M09", "M06", "M16", "M17", "M10"],
    "ticker": ticker_da_dati("dati.json"),

    "top": {
        "tema": "Tecnologia",
        "titolo": "Anthropic debutta oggi al Nasdaq con la maggiore quotazione di sempre",
        "dek": "Il prezzo dell'offerta è fissato a 83 dollari, sopra la forchetta prevista, e la società raccoglie circa "
               "81 miliardi di dollari: più di ogni altra offerta pubblica iniziale (Reuters). Il titolo, con il simbolo ANT, "
               "comincia a trattare alle 15:30 di Roma. Arriva dopo una settimana di vendite a Wall Street, e per noi il "
               "primo prezzo dirà quanto il mercato accetta ancora di pagare per l'intelligenza artificiale. [[anthropic]]",
    },
    "quadro": "Per noi a muovere i prezzi è la Fed più della quotazione. I future sui tassi danno quasi per certo un rialzo "
              "a dicembre. Il dollaro sale ai massimi da 19 mesi e l'oro cede il 3,2% anche con le tensioni nel Golfo. Il "
              "rendimento a 30 anni scende, quello a 2 anni no: di solito significa tassi alti oggi e crescita più debole "
              "domani. In borsa si vende da una settimana, e il debutto di Anthropic mette alla prova chi compra ancora.",
    "in30": [
        "I verbali della Fed vedono altri rialzi dei tassi: il dubbio è quanto grandi. [[fed]]",
        "L'oro scende ai minimi da 14 mesi, anche con le tensioni nel Golfo. [[dollaro]]",
        "UnitedHealth crolla per una proposta del governo sui rimborsi. [[sanita]]",
    ],
    "in30_temi": ["Fed", "Materie prime", "Macro"],
    "stamattina": [
        "Asia alle 08:37: Hong Kong -1,98%, Seul +1,02%, Tokyo con il Nikkei a 59.444,21 punti",
    ],
    "notizie": [
        {"tag": "Banche", "titolo": "Le banche italiane frenate da Ires più alta e voci su una stretta della Bce",
         "testo": "Un emendamento della Lega alza di tre punti l'Ires per le banche, e la Bce studia più riserva obbligatoria: "
                  "se ne discute al Consiglio direttivo del 25 novembre."},
        {"tag": "Trimestrali", "titolo": "TJX alza le previsioni per l'anno e sale in borsa",
         "testo": "Vendite a parità di negozi attese in crescita del 4% e utile per azione rettificato tra 5,17 e 5,20 $: "
                  "il titolo guadagna circa il 10% in mattinata."},
        {"tag": "Inflazione", "titolo": "Nel Regno Unito l'inflazione sale al 3,6% e il diesel segna un record",
         "testo": "A ottobre i prezzi crescono del 3,6% su un anno, dal 3,5%. Il diesel costa 7 pence al litro in più "
                  "in un mese, il prezzo più alto dall'inizio della serie nel 1996 (ONS)."},
        {"tag": "Geopolitica", "titolo": "Trump arriva in Cina mentre Xi e Putin attaccano il protezionismo",
         "testo": "Il vertice a tre con l'Iran in agenda è atteso oggi a Shenzhen; Xi e Putin criticano il "
                  "«protezionismo» occidentale e le sanzioni."},
        {"tag": "Petrolio", "titolo": "Le previsioni di offerta in eccesso pesano sul Brent",
         "testo": "Il barile vale circa 92 $: pesa la prospettiva di un'offerta in eccesso (Reuters)."},
        {"tag": "Europa", "titolo": "Prosus cade ai minimi dal 2024 dopo i conti deboli di Tencent",
         "testo": "Ad Amsterdam il titolo perde il 5,05%, ai minimi da settembre 2024: Prosus detiene una quota "
                  "importante di Tencent (dpa-AFX)."},
        {"tag": "Italia", "titolo": "Leonardo e Tenaris trascinano giù Milano, Ferrari controcorrente",
         "testo": "Leonardo cede il 4,08% e Tenaris il 3,13%, mentre Ferrari sale del 2,97%."},
    ],

    "mercati_titolo": "Numeri, temi aperti e calendario",
    "cruscotto": [
        ("Mondo e Stati Uniti", [["MSCI ACWI (ETF, $)", "150,68", "18/11", "-0,4%", "n.d.", "+6,5%"],
                         ["S&amp;P 500", "7.323,63", "18/11", "-0,2%", "-3,1%", "+7,0%"],
                         ["Nasdaq Comp.", "24.429,88", "18/11", "+0,4%", "-2,8%", "+5,1%"],
                         ["Russell 2000", "2.714,31", "18/11", "+0,5%", "-2,7%", "+9,4%"]]),
        ("Europa", [["Euro Stoxx 50", "6.154,39", "18/11", "-0,9%", "-3,6%", "+6,2%"],
                    ["FTSE MIB", "50.173", "18/11", "-1,3%", "n.d.", "+11,6%"]]),
        ("Asia (19/11 intraday*)", [["Nikkei 225*", "59.444,21", "19/11", "+0,7%", "-2,8%", "+18,1%"],
                                    ["Hang Seng*", "n.d.", "19/11", "-2,0%", "n.d.", "n.d."],
                                    ["Kospi*", "n.d.", "19/11", "+1,0%", "n.d.", "n.d."]]),
    ],
    "cruscotto_nota": "1 g = chiusura su chiusura; 1 sett. = su venerdì 13/11; da inizio anno = su chiusura 2025. "
                      "* Asia: dato di stamattina alle 08:37.",
    "cross_data": "Livello 18/11",
    "cross": [
        ("Tassi", [["Treasury 10 anni", "5,07%", "-3 pb", "-8 pb", "-8 pb", "Sotto il 5,15% di venerdì 13/11"],
                   ["Treasury 30 anni", "5,41%", "-5 pb", "-6 pb", "-7 pb", "Scende più del 10 anni [[fed]]"]]),
        ("Cambi", [["EUR/USD", "1,0973", "-0,2%", "-0,4%", "-2,1%", "Vicino ai minimi da aprile 2025"]]),
        ("Materie prime", [["Brent future", "91,95 $", "-1,3%", "-4,1%", "-16,1%", "-"],
                           ["Oro (future, $/oncia)", "3.741,90", "-3,2%", "-3,7%", "-10,0%", "Minimo da 14 mesi [[dollaro]]"]]),
        ("Volatilità", [["VIX (volatilità attesa)", "24,56", "-0,90", "+5,26", "+6,12", "Massimo di giornata 25,46 il 17/11"]]),
    ],
    "cross_nota": "1 mese = sul 19/10. VIX = volatilità attesa sull'S&amp;P 500. EUR/USD e variazioni a un mese: FMP.",
    "termometri": [
        ("Fed e tassi", "Decisione il 9 dicembre", "Verbali: più rialzi probabili", "su: Probabilità di rialzo a dicembre", "Dati sui prezzi"),
        ("AI e borsa", "Debutto di Anthropic oggi", "Prezzo sopra la forchetta", "giu: Titoli AI, Nvidia in testa", "Primo prezzo di ANT"),
        ("Oro e dollaro", "Oro ai minimi da 14 mesi", "Dollaro ai massimi da 19 mesi", "giu: Oro e argento", "Rendimento a 30 anni"),
        ("Sanità USA", "Proposta CMS aperta ai commenti", "UnitedHealth in forte calo", "giu: UnitedHealth", "Commenti fino al 19 gennaio"),
    ],
    "fermi": "Tassi della Bce (depositi al 2,50%, prossima riunione il 17 dicembre).",
    "lettura": "Due cose che le tabelle dicono e la prima pagina no. In una settimana l'Euro Stoxx 50 perde più di Wall "
               "Street: da inizio anno però la distanza resta piccola, +6,2% contro +7,0%. E il Brent perde il 16% in un mese: di solito un petrolio che scende allenta i prezzi, "
               "ma il VIX (la volatilità attesa a Wall Street) è a 24,56: per noi oggi la paura pesa più dell'inflazione.",

    "ieri": [
        ("Mer 18, sera", "Verbali Fed (riunione 27-28 ottobre)", "I funzionari vedono probabili altri rialzi; alcuni più di un quarto di punto", "", "[[fed]]"),
        ("Mer 18, mattina", "Inflazione Regno Unito (ottobre)", "3,6% su un anno (prima 3,5%); senza energia e alimentari 2,8%", "", "Notizie"),
    ],
    "agenda": [
        ("Gio 19, 14:00", "Walmart: conti del terzo trimestre fiscale", "Conference call alle 14:00",
         "Termometro dei consumi americani",
         "<b>Sopra:</b> di solito il titolo sale se le previsioni vengono alzate.<br/><b>Sotto:</b> pesa su tutti i titoli dei consumi."),
        ("<b>Gio 19, 14:30</b>", "<b>Sussidi di disoccupazione USA</b>", "<b>198 mila; prima 200 mila (Investing.com)</b>",
         "<b>Evento n.1:</b> tenuta del lavoro con tassi in salita",
         "<b>Sopra</b> (più sussidi): lavoro più debole, di solito rendimenti giù.<br/><b>Sotto:</b> lavoro solido, di solito rialzo di dicembre più certo."),
        ("Gio 19, 14:30", "Indice Philadelphia Fed (novembre)", "20,6; prima 20,9 (Investing.com)", "Stato dell'industria",
         "<b>Sopra:</b> industria in salute, di solito dollaro e rendimenti su.<br/><b>Sotto:</b> torna il timore di una frenata."),
        ("Gio 19, 15:30", "Anthropic debutta al Nasdaq (ANT)", "Apertura delle contrattazioni",
         "Primo prezzo dopo l'offerta a 83 $",
         "<b>Sopra:</b> di solito aiuta i titoli dell'AI.<br/><b>Sotto:</b> pesa su Nvidia e sul Nasdaq."),
    ],
    "moduli": [
        {"chiave": "anthropic", "tema": "Tecnologia", "breve": "il test di ANT",
         "titolo": "Anthropic quota sopra la forchetta e mette alla prova un mercato che vende AI",
         "misura": "doppio",
         "grafico": {"tipo": "linee", "file": "c_spx_mese.png", "x": [d(x) for x, _ in SPX], "soggetto": "Wall Street",
                     "serie": [("S&P 500", [v for _, v in SPX], "#111111")], "ruolo": "storia",
                     "titolo": "Wall Street arriva al debutto dopo una settimana di vendite",
                     "sottotitolo": "S&P 500, chiusure (punti)",
                     "note": [(d("11-11"), 7619.38, "11/11"), (d("11-18"), 7323.63, "18/11")]},
         "righe": [["Anthropic (ANT)", "Valore", "Nota"],
                   ["Prezzo dell'offerta", "83 $", "Sopra la forchetta indicata"],
                   ["Raccolta", "circa 81 mld $", "Maggiore offerta di sempre"],
                   ["Valore atteso al debutto", "fino a 1.500 mld $", "Stima massima"],
                   ["Ricavi del terzo trimestre", "quasi 17 mld $", "+45% sul secondo"],
                   ["Valore diviso ricavi annualizzati", "circa 22 volte", "Calcolo nostro: 17 mld x 4 = 68 mld"]],
         "larghezze": [62, 48, 78], "ruolo_righe": "quanto",
         "perche": "Per noi il debutto misura quanto si paga ancora l'AI proprio mentre Wall Street la vende. Anthropic ha chiuso l'offerta sopra la forchetta (Reuters), e Nvidia ha perso il 13% in cinque sedute.",
         "quindi": "Oggi alle 15:30 si vede il primo prezzo di ANT. Se chiude ben oltre i 100 $ e insieme salgono Nvidia e Nasdaq, la nostra lettura cade.",
         "punti": ["<b>Chi compra.</b> Per Vanda Research i piccoli investitori hanno comprato 3 mld $ netti di Nvidia in dieci "
                   "sedute. Su Anthropic la stima di acquisti netti è di 250 milioni, e per Vanda è prudente.",
                   "<b>I conti.</b> La società non è ancora in utile e ha 6,2 mld $ di debito (CBS News).",
                   "<b>Il record.</b> È la maggiore quotazione mai fatta in borsa (Reuters)."],
         "testo": ["Perché un prezzo sopra la forchetta conta? Prima dell'offerta gli analisti fissano un intervallo, e "
                   "chi compra dice quanto è disposto a pagare. Un prezzo sopra l'intervallo vuol dire che la domanda "
                   "superava l'offerta, ed è il segnale che i grandi investitori credono ancora alla storia.",
                   "C'è un secondo effetto, meno visibile. Quando una sola società raccoglie 81 miliardi, chi compra "
                   "deve trovare quei soldi altrove: di solito vende altri titoli, e per primi quelli che si scambiano "
                   "di più, come Nvidia. Delle 980 milioni di azioni offerte, 956,35 milioni sono vendute dalla società "
                   "(CBS News): quasi tutto il ricavato va quindi ad Anthropic. È una lettura nostra, non un fatto dichiarato: per questo conta guardare se "
                   "oggi i titoli dell'AI salgono o scendono insieme ad Anthropic.",
                   "Ieri il quadro era diviso: il Dow Jones ha perso l'1,11% mentre il Nasdaq Composite saliva dello 0,42%. Di solito indici ponderati per capitalizzazione possono divergere, perché pochi grandi titoli "
                   "ne decidono il movimento.",
                   "A Taipei l'effetto si sente di più: la borsa di Taiwan perde il 4,4% stamattina (Reuters). Di solito "
                   "i suoi indici seguono i chip americani della sera prima, perché i produttori di semiconduttori "
                   "pesano molto sull'indice."],
         "fonte": "Fonti: CBS News, Reuters (MarketScreener), ANSA.",
         "guardare": "Il primo prezzo e la chiusura di ANT, e Nvidia: se tiene, la vendita è finita. Per noi un titolo che perde subito terreno sul prezzo dell'offerta dice che la domanda era già stata servita."},
        {"chiave": "fed", "tema": "Fed", "breve": "i verbali e la curva piatta",
         "titolo": "I verbali vedono altri rialzi e la curva dei Treasury si appiattisce",
         "misura": "doppio",
         "grafico2": {"tipo": "barre", "file": "c_curva_1g.png",
                    "dati": [(k, round((C18[k] - C17[k]) * 100)) for k in C18],
                    "titolo": "Salgono le scadenze brevi, scendono le lunghe",
                    "sottotitolo": "Curva Treasury, variazione del 18/11 (pb)", "unita": " pb", "dec": 0, "ordina": False,
                    "soggetto": "curva", "ruolo": "quanto"},
         "grafico": {"tipo": "linee", "file": "c_ust_mese.png", "x": [d(r[0]) for r in UST], "soggetto": "curva",
                       "titolo": "La distanza tra 30 e 2 anni scende da 71 a 61 punti base in un mese",
                       "sottotitolo": "30 anni meno 2 anni (pb)", "ruolo": "storia",
                       "serie": [("30 anni meno 2 anni", [round((r[3] - r[1]) * 100) for r in UST], "#F26B1D")]},
         "numero": "90-95%: probabilità di un rialzo il 9 dicembre secondo i future sui tassi.",
         "perche": "Di solito il rendimento a 2 anni segue le attese sulla Fed, e i verbali le hanno confermate: i funzionari della Fed vedono probabili nuovi rialzi. Il lungo scende e il breve resta fermo: per noi il mercato teme più la crescita che i prezzi oltre dicembre.",
         "quindi": "Se il 30 anni risale sopra il 5,50% e il 10 anni sopra il 5,15%, la curva torna a dire inflazione.",
         "punti": ["<b>Il voto.</b> A ottobre Cook e Hammack volevano già un rialzo di un quarto di punto (voto 10-2).",
                   "<b>La misura.</b> Per diversi membri dicembre è una «close call»; alcuni valutano più di un quarto di punto se l'inflazione peggiora.",
                   "<b>Il 30 anni.</b> Scende di 5 pb mentre il 2 anni resta fermo.",
                   "<b>L'AI.</b> I verbali citano la spesa in intelligenza artificiale tra ciò che alimenta i prezzi."],
         "testo": ["Il verbale è il resoconto di cosa si sono detti i membri della Fed all'ultima riunione. Il 28 ottobre i tassi erano stati lasciati al 3,75-4,00% "
                   "(federalreserve.gov), e un rialzo a dicembre li porterebbe al 4,00-4,25%. Il verbale non cambia "
                   "la decisione, che il mercato già dava per fatta: sposta la domanda su quanto sarà grande "
                   "il rialzo. Quando i membri discutono di muoversi più di un quarto di punto, i prezzi se ne accorgono "
                   "prima che arrivi la decisione.",
                   "L'inflazione è sopra l'obiettivo della Fed da quasi sei anni (CBS News). Un rialzo di dicembre non "
                   "sorprende nessuno: a dividere è la dimensione.",
                   "Il rendimento a 2 anni, di solito, segue da vicino le attese sulla Fed. Quello a 30 dipende anche "
                   "da crescita e inflazione di molti anni. Se il breve tiene e il lungo scende la curva si fa piatta: "
                   "non è una previsione, ma di solito vuol dire tassi alti oggi e un'economia più fragile domani.",
                   "All'asta dei titoli a 20 anni la domanda diretta è stata forte e quella indiretta debole. "
                   "Un'asta con poca domanda di solito spinge i rendimenti in su: ieri non è accaduto, e il lungo ha continuato a scendere."],
         "guardare": "Il prossimo dato sui prezzi. Se l'inflazione dei servizi resta alta il rialzo di dicembre non basta, "
                     "e si torna a parlare di mezzo punto. Se rallenta, il calo del lungo può essere l'inizio di un movimento più ampio, "
                     "e di solito ne beneficiano anche le borse."},
        {"chiave": "dollaro", "tema": "Valute", "breve": "oro giù con il dollaro",
         "titolo": "Neanche le tensioni nel Golfo fermano l'oro: pesa il dollaro",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_oro_mese.png", "x": [d(x) for x, _ in ORO], "soggetto": "oro",
                     "serie": [("Oro future", [v for _, v in ORO], "#F26B1D")], "ruolo": "storia",
                     "titolo": "L'oro tocca il minimo da 14 mesi dopo un mese quasi sempre in calo",
                     "sottotitolo": "Oro future, chiusure ($)",
                     "note": [(d("10-19"), 4160.1, "19/10"), (d("11-18"), 3741.9, "18/11")]},
         "perche": "Per noi il dollaro attira più dei rifugi. L'indice del dollaro è a 103,92, massimo da 19 mesi, e i future danno oltre il 90% al rialzo Fed di dicembre. Per Kitco le tensioni nel Golfo non sostengono il metallo.",
         "numero": "3.735 $: il minimo toccato dall'oro a pronti, il più basso da settembre 2025 (Reuters). Per l'oro in dollari conta anche il cambio: se il dollaro sale, di solito il prezzo in altre valute sale ancora meno.",
         "punti": ["<b>L'argento.</b> Perde il 3,4%, più dell'oro.",
                   "<b>Lo spot.</b> Il metallo a pronti scende sotto 3.800 $, ai minimi dal 2025."],
         "quindi": "Se l'oro risale sopra i 3.864 $ della chiusura del 17/11 mentre il dollaro resta forte, la sola Fed non basta a spiegarlo.",
         "testo": ["L'oro non paga interessi: di solito soffre quando i tassi alti rendono più convenienti titoli che "
                   "li pagano. Quando il dollaro sale, inoltre, diventa più caro per chi compra in altre valute. Nei momenti di "
                   "paura molti comprano oro come rifugio, ma stavolta la spinta del dollaro è stata più forte.",
                   "L'indice del dollaro è salito a 103,92 dopo le parole di Waller, membro della Fed, su un'azione aggressiva "
                   "contro l'inflazione.",
                   "Nelle fasi di forte paura, di solito, è il dollaro stesso a fare da rifugio: chi cerca liquidità compra "
                   "dollari prima ancora dell'oro. È una seconda lettura possibile, e in quel caso oro e "
                   "dollaro non salirebbero insieme.",
                   "In un mese l'oro ha perso più di 400 $: la discesa di ieri è l'ultimo gradino di un calo già lungo. "
                   "Se i tassi americani restano alti, di solito il suo prezzo resta sotto pressione.",
                   "Lo stesso vale per l'euro: vicino ai minimi da aprile 2025, a 1,0973, perché di solito i tassi "
                   "americani più alti rafforzano il dollaro sul cambio con la moneta europea."],
         "fonte": "Fonti: Kitco, Bloomberg, Reuters."},
        {"chiave": "sanita", "tema": "Macro", "breve": "UnitedHealth crolla su una proposta",
         "titolo": "I titoli sanitari scontano come legge una proposta che può ancora cambiare",
         "misura": "mezzo",
         "righe": [["Il punto", "Dato"],
                   ["UnitedHealth, 18/11", "-10,2%, a circa 349,9 $"],
                   ["Cosa propone il CMS", "Estendere a più pagamenti l'esito dei controlli a campione"],
                   ["Da quale anno", "Dal 2018 di pagamento"],
                   ["Recuperi stimati", "Circa 9 mld $ per anno di pagamento"]],
         "larghezze": [62, 118],
         "perche": "Per noi il mercato prezza il caso peggiore. La proposta del CMS, l'ente che gestisce Medicare, estenderebbe a una platea più ampia di pagamenti l'esito dei controlli a campione, senza correzione per la spesa a pagamento (finchannel).",
         "quindi": "I commenti pubblici restano aperti fino al 19 gennaio 2027 e non è una regola finale: finché il testo può cambiare, il prezzo scommette sul peggio.",
         "punti": ["<b>Il metodo.</b> L'estrapolazione applicherebbe l'esito dei controlli su un campione a una platea più ampia di pagamenti.",
                   "<b>Chi è esposto.</b> Per Mizuho più controlli sono un fattore negativo per i margini, e le più esposte sono UnitedHealth e Humana."],
         "testo": ["Perché un titolo cade di un decimo per una proposta? Il prezzo di un'azione sconta ogni giorno gli utili futuri "
                   "attesi. Se il testo diventasse regola, i recuperi chiesti agli assicuratori ridurrebbero quegli utili. "
                   "Chi vende non aspetta la versione finale.",
                   "Una regola finale più morbida di solito fa recuperare il titolo. Un testo ancora in consultazione "
                   "può cambiare, e finché non cambia il prezzo incorpora la versione più dura."],
         "fonte": "Fonte: FINANCIAL (finchannel)."},
    ],

    "scommessa": {"tesi": "Con noi: Treasury a 10 anni, euro e Brent restano dentro la forchetta. Contro: S&P 500, Euro "
                          "Stoxx 50 e oro sono fuori dopo il calo di inizio settimana. Da qui a venerdì: Anthropic e i dati americani.",
                  "lunedi": False, "venerdi": False, "settimana_prec": None},
    "parole": [("Offerta pubblica iniziale (IPO)", "Il momento in cui una società vende per la prima volta azioni al pubblico e comincia a essere quotata."),
               ("Verbali della Fed", "Il resoconto, pubblicato tre settimane dopo, di ciò che i membri hanno detto alla riunione sui tassi."),
               ("Appiattimento della curva", "La distanza tra i rendimenti a lunga e a breve scadenza si riduce."),
               ("Close call", "Una decisione in bilico: chi deve prendere una decisione la giudica incerta tra due scelte vicine."),
               ("Medicare Advantage", "Piani sanitari privati per anziani americani, pagati in gran parte dal governo."),
               ("Indice del dollaro", "Il valore del dollaro contro un paniere di altre valute, tra cui euro, yen e sterlina.")],
    "fonti": [
        ("Dati di mercato", "Financial Modeling Prep (indici USA, VIX, Nikkei, Brent e oro future, curva par del Tesoro USA); "
                            "Alpha Vantage (EUR/USD, ACWI); dpa-AFX (Euro Stoxx 50); ANSA (FTSE MIB, Asia delle 08:37)."),
        ("Prima pagina e mercati", "Reuters, ANSA, ONS, Kitco, Yahoo Finance, dpa-AFX."),
        ("Calendario e agenda", "Investing.com, Walmart, calendari economici."),
        ("Approfondimenti", "Anthropic: CBS News, Reuters. Fed: Yahoo Finance, Reuters, curva via FMP. "
                            "Oro: Kitco, Bloomberg. Sanità: finchannel."),
        ("La scommessa", "Chiusure di FMP e Alpha Vantage; forchette calcolate dalla volatilità delle ultime 20 sedute."),
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
