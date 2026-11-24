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
NOTA_DATI = "Chiusure al 20 novembre; nel fine settimana le borse sono chiuse"
REG = "2026-11-23-settimana.json"

# ============================ DATI DEI GRAFICI (verificati) ============================
d = lambda s: dt.date(2026, int(s[:2]), int(s[3:]))   # "MM-GG" -> data
NASDAQ = [("11-10", 25065.87), ("11-11", 25466.19), ("11-12", 25366.09), ("11-13", 25136.27), ("11-16", 24509.76),
          ("11-17", 24328.38), ("11-18", 24429.88), ("11-19", 23879.20), ("11-20", 22617.73)]
SETTIMANA = [("S&P 500", round((6910.39 / 7561.67 - 1) * 100, 1)), ("Russell 2000", round((2581.79 / 2790.49 - 1) * 100, 1)),
             ("Nasdaq", round((22617.73 / 25136.27 - 1) * 100, 1))]
UST_19 = {"1M": 4.20, "2M": 4.29, "3M": 4.34, "6M": 4.42, "1A": 4.62, "2A": 4.76, "3A": 4.81, "5A": 4.86, "7A": 4.94,
          "10A": 5.04, "20A": 5.43, "30A": 5.40}
UST_20 = {"1M": 4.19, "2M": 4.28, "3M": 4.32, "6M": 4.38, "1A": 4.51, "2A": 4.63, "3A": 4.65, "5A": 4.71, "7A": 4.80,
          "10A": 4.92, "20A": 5.34, "30A": 5.31}
ORO = [("11-10", 4030.2), ("11-11", 4000.5), ("11-12", 3885.3), ("11-13", 3886.3), ("11-16", 3853.0), ("11-17", 3864.2),
       ("11-18", 3741.9), ("11-19", 3685.5), ("11-20", 3515.4)]
SX5E = [("11-10", 6327.87), ("11-11", 6393.39), ("11-12", 6398.98), ("11-13", 6386.86), ("11-16", 6348.35),
        ("11-17", 6212.11), ("11-18", 6154.39), ("11-19", 6113.86), ("11-20", 5941.95)]

TAB = tabelle_da_dati("dati.json")
C = {
    "data": OGGI,
    "temi": ["Tecnologia", "Chip", "Fed", "Tassi", "Europa", "Materie prime"],
    "glossario": ["PCE", "VIX", "pb", "core"],
    "meccanismi": ["M01", "M26", "M23", "M16", "M14", "M09", "M04"],
    "ticker": ticker_da_dati("dati.json"),
    "top": {
        "tema": "Tecnologia",
        "titolo": "Nvidia crolla per l'indagine sui conti e Wall Street entra in correzione",
        "dek": "Venerdì Nvidia perde circa il 14% dopo la notizia, data da Reuters, che gli investigatori dell'autorità "
               "americana di Borsa esaminano la sua contabilità. L'S&amp;P 500 chiude a 6.910,39 (-3,70%), più del 10% sotto il "
               "massimo del 6 ottobre, e il Nasdaq cede il 5,28%. Per l'indice è la settimana peggiore da più di 18 mesi. [[nvidia]]",
        "freccia": "Non è chiaro quando l'indagine sia partita; l'autorità non commenta e Nvidia non ha risposto.",
    },
    "quadro": "Venerdì borse e oro hanno venduto insieme e i titoli di Stato hanno fatto da rifugio. Il 10 anni scende "
              "al 4,92%. Leggiamo vendite forzate, di chi cede ciò che si vende in fretta per coprire le "
              "perdite sulle azioni. L'oro perde il 4,6% e il dollaro non si muove. Il VIX, l'indice che "
              "misura la paura a Wall Street, sale del 26,2% a 35,89. Il petrolio resta in disparte (Brent 92,57 $). [[rifugio]]",
    "in30": [
        "L'Europa cede e ASML e STMicroelectronics sono tra i titoli più colpiti: finora aveva perso meno di Wall Street. [[europa]]",
        "Treasury e oro prendono strade opposte: i titoli di Stato salgono, il metallo scende più dell'S&amp;P 500. [[rifugio]]",
        "Mercoledì il PCE, l'indice dei prezzi che la Fed guarda di più, mette alla prova il rialzo di dicembre. [[agenda]]",
    ],
    "in30_temi": ["Europa", "Materie prime", "Fed"],
    "stamattina_titolo": "Cosa guardare all'apertura",
    "stamattina": [
        "Alle 15:30 apre Wall Street: la prima seduta dopo la settimana peggiore da più di 18 mesi",
        "Treasury a 10 anni: venerdì ha chiuso sotto il 5%",
        "Oro: venerdì ha chiuso a 3.515 $, il livello da cui si vede se il calo continua",
    ],
    "notizie": [
        {"tag": "Fed", "titolo": "Cook avverte: aspettare ancora per alzare i tassi è un rischio",
         "testo": "La governatrice della Fed lo dice a Santiago del Cile: se la banca centrale aspetta, potrebbero servire rialzi "
                  "più grandi dopo. Giudica la crescita forte e il lavoro solido.", "rimando": "fed"},
        {"tag": "Wall Street", "titolo": "GTCR valuta un'offerta da 50 miliardi per Global Payments",
         "testo": "Secondo Bloomberg il fondo di private equity esplora l'acquisto della società dei pagamenti, che sale "
                  "in forte rialzo sulla notizia. Non c'è un'offerta annunciata."},
        {"tag": "Wall Street", "titolo": "CrowdStrike tratta per comprare Zscaler",
         "testo": "Lo scrive Reuters citando due persone informate: nessun accordo è garantito e le trattative potrebbero "
                  "finire senza intesa."},
        {"tag": "Chip", "titolo": "STMicroelectronics e ASML tra i più colpiti in Europa: oltre il 9%",
         "testo": "Sono i titoli più colpiti dalla vendita dei chip, che venerdì ha fatto perdere al comparto "
                  "tecnologico il 5,4%. A Milano lo spread tra BTP e Bund è a 110 punti base.", "rimando": "europa"},
        {"tag": "Asia", "titolo": "Advantest cede un decimo e Samsung il 7% nel crollo dei chip asiatici",
         "testo": "Il Nikkei perde il 5,06% e il Kospi il 5,21%; l'ETF ACWI sull'azionario mondiale cede il 3,49%."},
        {"tag": "Wall Street", "titolo": "Anthropic sfiora il prezzo dell'IPO nel secondo giorno di scambi",
         "testo": "Venerdì il titolo è sceso fino a 83,05 $, cinque centesimi sopra i 83 $ del collocamento, prima di "
                  "risalire."},
    ],
    "mercati_titolo": "Numeri, temi aperti e calendario",
    "cruscotto": TAB["cruscotto"], "cruscotto_nota": TAB["cruscotto_nota"],
    "cross_data": TAB["cross_data"], "cross": TAB["cross"], "cross_nota": TAB["cross_nota"],
    "termometri": [
        ("Fed e tassi", "Riunione 8-9 dicembre", "Cook: aspettare rischia di restare indietro", "su: Attese di un rialzo a dicembre", "PCE di mercoledì"),
        ("AI e borsa", "S&amp;P 500 in correzione", "Indagine sui conti di Nvidia", "giu: Titoli dei chip", "Wall Street alle 15:30"),
        ("Oro e dollaro", "Oro a 3.515 $ in chiusura", "Cala più delle azioni", "giu: Oro", "Dollaro e rendimenti USA"),
        ("Petrolio", "Brent a 92,57 $", "In rialzo con le borse a picco", "fermo: Brent, senza direzione", "Scorte USA e Hormuz"),
    ],
    "fermi": "Iran e Hormuz (nessuna novità verificata nel fine settimana), Tassi della Bce (prossima riunione il 17 dicembre).",
    "lettura": "Il Russell 2000, che raccoglie le società più piccole, perde meno dell'S&amp;P 500, mentre il Nasdaq perde un po' di "
               "più. Leggiamo che le vendite hanno colpito i grandi titoli tecnologici, che pesano di più negli indici più "
               "concentrati, e meno le piccole società.",
    "ieri": [
        ("Mar 17", "Conti Nvidia (terzo trimestre)", "Ricavi 115,8 mld $ (attesi 109,15); utile per azione 2,68 $ (2,47)", "+", "[[nvidia]]"),
        ("Gio 19", "Conti Gap (terzo trimestre)", "Vendite nette 4,0 mld $, +2% sull'anno", "+", ""),
        ("Mer 18", "Verbali della Fed (riunione di ottobre)", "Nuovi rialzi giudicati probabili", "", "[[fed]]"),
    ],
    "agenda": [
        ("<b>Mer 25, 14:30</b>", "<b>PCE USA (ottobre)</b>", "<b>Core +0,3% sul mese, +3,2% su un anno; prima +3,1%</b>",
         "<b>Evento n.1:</b> i prezzi che la Fed guarda di più, prima della riunione dell'8-9 dicembre",
         "<b>Sopra:</b> salgono i rendimenti a 2 anni e le attese di rialzo.<br/><b>Sotto:</b> il rialzo di dicembre perde forza."),
        ("Mer 25, 14:30", "PIL USA (terzo trimestre, seconda stima)", "+3,4% annualizzato", "Tenuta della crescita",
         "<b>Sopra:</b> l'economia regge i tassi alti.<br/><b>Sotto:</b> cresce il timore di una frenata."),
        ("Gio 26", "Mercati USA chiusi per il Ringraziamento", "Wall Street e titoli di Stato fermi", "Scambi più sottili in Europa",
         "Senza Wall Street gli scambi europei tendono a calare."),
        ("Ven 27, in serata", "Wall Street chiude in anticipo", "Seduta ridotta", "Volumi più bassi",
         "Nelle sedute brevi di solito i volumi calano."),
    ],
    "moduli": [
        {"chiave": "nvidia", "tema": "Chip", "breve": "Nvidia batte le stime e crolla",
         "titolo": "Nvidia batte le stime ma crolla: ora il mercato dubita dei suoi conti",
         "misura": "doppio",
         "grafico": {"tipo": "barre", "file": "c_settimana.png", "dati": SETTIMANA, "ordina": False, "dec": 1, "unita": "%",
                     "soggetto": "Nvidia", "ruolo": "quanto",
                     "titolo": "In una settimana il Nasdaq perde più delle piccole società",
                     "sottotitolo": "variazione % dal 13 al 20 novembre"},
         "grafico2": {"tipo": "linee", "file": "c_nasdaq.png", "x": [d(x) for x, _ in NASDAQ],
                      "serie": [("Nasdaq", [v for _, v in NASDAQ], "#111111")], "soggetto": "Nvidia", "ruolo": "storia",
                      "titolo": "Il Nasdaq cede il 3% dopo i conti di Nvidia e il 5% dopo la notizia dell'indagine",
                      "sottotitolo": "Nasdaq Composite, chiusure in punti",
                      "eventi": [(d("11-17"), "conti"), (d("11-20"), "indagine")]},
         "righe": [["Nvidia, terzo trimestre", "Risultato", "Attese"],
                   ["Ricavi (mld $)", "115,8", "109,15"],
                   ["Utile per azione ($)", "2,68", "2,47"],
                   ["Ricavi del data center (mld $)", "107,6", "101,85"],
                   ["Guidance per il trimestre in corso (mld $)", "130", "125,25"]],
         "larghezze": [70, 30, 30], "ruolo_righe": "chi",
         "perche": "Per Reuters, che cita due persone informate, gli investigatori della SEC esaminano possibili problemi "
                   "contabili di Nvidia. A nostro avviso il mercato non discute più quanto valgano i chip, ma se i conti di chi li "
                   "vende siano affidabili.",
         "numero": "+6,1%: di tanto i ricavi del trimestre superano le stime degli analisti. Un'ottima notizia, e il titolo "
                   "perde comunque in una sola seduta.",
         "quindi": "Alle 15:30 riapre Wall Street: se l'S&amp;P 500 riparte sotto i 6.910 punti della chiusura di venerdì, le vendite continuano.",
         "testo": ["Perché un'azienda che batte le stime perde circa il 14% in un giorno? Perché chi compra un'azione paga gli "
                   "utili dei prossimi anni, e può farlo solo se si fida dei numeri che riceve. Martedì i conti di Nvidia erano "
                   "sopra le attese su ricavi, utili e previsioni. Venerdì Reuters ha scritto che gli investigatori "
                   "dell'autorità americana di Borsa guardano la sua contabilità, e la fiducia si è incrinata.",
                   "Il dubbio colpisce un titolo che pesa moltissimo. Nvidia è tra i titoli più grandi del mondo. In un indice "
                   "come l'S&amp;P 500 ogni titolo conta in proporzione al suo valore di Borsa, e una caduta così tende a "
                   "trascinare l'intero indice.",
                   "C'è poi chi la guida. Il direttore finanziario Colette Kress è amministratore delegato ad interim, come "
                   "mostra il documento depositato il 17 novembre con i conti. Per chi deve fidarsi dei numeri, è "
                   "un'incertezza in più.",
                   "Con questa chiusura l'S&amp;P 500 entra in ciò che gli operatori chiamano correzione, un calo di oltre il "
                   "10% dal massimo, qui quello del 6 ottobre. Il VIX, che ricava dai prezzi delle opzioni quanto movimento si "
                   "aspettano gli operatori nei prossimi trenta giorni, sale a 35,89: più del doppio del 17,49 dell'11 novembre."],
         "fonte": "Fonti: AP, Reuters, documento Nvidia depositato il 17/11, FMP; contesto dall'archivio della redazione.",
         "guardare": "Conta se si chiarisce l'oggetto dell'indagine e se i chip americani recuperano. Un chiarimento che "
                     "escluda problemi contabili darebbe ragione a chi vede un eccesso nelle vendite; nuove notizie "
                     "allargherebbero la sfiducia agli altri produttori di chip."},
        {"chiave": "rifugio", "tema": "Materie prime", "breve": "Treasury sì, oro no",
         "titolo": "Con le borse a picco i Treasury fanno da rifugio, l'oro vende",
         "misura": "doppio",
         "grafico": {"tipo": "barre", "file": "c_curva.png",
                     "dati": [(k, round((UST_20[k] - UST_19[k]) * 100)) for k in UST_20],
                     "titolo": "I rendimenti calano lungo tutta la curva, di più tra 1 e 7 anni",
                     "sottotitolo": "Curva Treasury, variazione del 20/11 (pb)", "unita": " pb", "dec": 0, "ordina": False,
                     "soggetto": "Treasury", "ruolo": "quanto"},
         "grafico2": {"tipo": "linee", "file": "c_oro.png", "x": [d(x) for x, _ in ORO],
                      "serie": [("Oro future", [v for _, v in ORO], "#F26B1D")], "soggetto": "oro", "ruolo": "storia",
                      "titolo": "Dal 10 novembre l'oro perde più di 500 dollari l'oncia",
                      "sottotitolo": "Oro future, chiusure ($)",
                      "note": [(d("11-10"), 4030.2, "10/11"), (d("11-20"), 3515.4, "20/11")]},
         "numero": "-4,6%: il calo dell'oro in un giorno, più di quello dell'S&amp;P 500 (-3,7%). Nel giorno della paura il "
                   "metallo ha ceduto più dell'S&amp;P 500.",
         "perche": "A nostro avviso chi perdeva sulle azioni ha venduto ciò che si vende in fretta, oro compreso. Già il 30 "
                   "ottobre, per Kitco, le vendite forzate dopo un calo delle azioni avevano prevalso sul ruolo di rifugio. Per Milano "
                   "Finanza pesano anche il dollaro forte e le attese di una stretta della Fed.",
         "quindi": "Un oro che chiude sotto i 3.500 $ dice che le vendite non sono finite; sopra i 3.685 $ di giovedì direbbe che la vendita forzata è finita.",
         "testo": ["Perché i titoli di Stato salgono e l'oro scende, se entrambi passano per un riparo? Perché chi cerca "
                   "sicurezza compra ciò che promette di restituire i soldi con gli interessi. Quando tutti comprano un "
                   "titolo del Tesoro il suo prezzo sale, e il rendimento, che si muove al contrario, scende. Venerdì il "
                   "10 anni è sceso al 4,92%: chi cercava protezione nei titoli di Stato l'ha trovata, chi la cercava nell'oro no.",
                   "L'oro non paga nulla, e con rendimenti alti pesa, come nelle ultime settimane, il costo di non incassare "
                   "interessi. In più, di solito, quando le perdite su un mercato obbligano a vendere, si cede ciò che si "
                   "riesce a vendere in fretta, non ciò che si vorrebbe.",
                   "Il dollaro, che nei giorni di paura vera tende a salire, è rimasto fermo. Era già forte: l'euro era "
                   "già in difficoltà prima della vendita, e con la Fed pronta a rialzare non aveva spazio "
                   "per salire ancora.",
                   "Giovedì il metallo aveva chiuso a 3.685 $: in una sola seduta lascia oltre 170 $ l'oncia e chiude a 3.515 $, in una settimana in cui perde più del 9%. Chi guardava il metallo come rifugio, venerdì, ha visto il contrario.",
                   "Nei titoli di Stato la corsa è lunga: il 10 anni chiude sotto il 5%, in calo sulla settimana. Con un rendimento più basso il prezzo dei titoli già in circolazione sale: chi li "
                   "aveva comprati prima ci guadagna. Vale anche il contrario: se il rendimento risalisse sopra il 5%, quei titoli perderebbero valore e il rifugio tornerebbe a costare."],
         "fonte": "Fonti: Kitco (archivio della redazione), curva del Tesoro e oro future via FMP.",
         "guardare": "Un 10 anni che torna sopra il 5% direbbe che la paura è passata e conta di nuovo la Fed. Un oro che non "
                     "rimbalza con il dollaro fermo indicherebbe che le vendite forzate continuano. Giovedì Wall Street è chiusa per il Ringraziamento."},
        {"chiave": "europa", "tema": "Europa", "breve": "L'Europa non regge più",
         "titolo": "L'Europa, che reggeva meglio di Wall Street, cede il 2,8% con i chip",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_sx5e.png", "x": [d(x) for x, _ in SX5E],
                     "serie": [("Euro Stoxx 50", [v for _, v in SX5E], "#111111")], "soggetto": "Europa", "ruolo": "storia",
                     "titolo": "L'Euro Stoxx 50 perde il 7,1% dal 12 novembre",
                     "sottotitolo": "Euro Stoxx 50, chiusure in punti",
                     "note": [(d("11-12"), 6398.98, "12/11"), (d("11-20"), 5941.95, "20/11")]},
         "perche": "Per Reuters gli investitori scaricano le scommesse sull'AI dopo l'IPO di Anthropic, che non ha rilanciato "
                   "la fiducia nel settore. A nostro avviso l'Europa non vende i suoi titoli AI, che sono pochi, ma i fornitori "
                   "dell'industria dei chip. Il calo non resta nei chip: banche, difesa e lusso, i titoli più legati alla crescita, "
                   "perdono più del 2,5%.",
         "quindi": "Alle 15:30 riapre Wall Street e si vede se l'Europa recupera il calo di venerdì: ASML e STMicroelectronics, "
                   "che hanno perso di più, mostrano se la vendita sta finendo. Un lunedì in calo darebbe allo STOXX 600 la sesta seduta negativa di fila.",
         "testo": ["Fino a giovedì l'Europa aveva perso meno di Wall Street: dal 12 al 19 novembre l'Euro Stoxx 50 cede il "
                   "4,5%, l'S&amp;P 500 il 5,5%. Perché venerdì il copione cambia? Perché il calo ha colpito i fornitori dei "
                   "chip, che l'Europa ha. ASML e STMicroelectronics perdono oltre il 9%, Infineon il 7,6%.",
                   "Milano chiude a 48.703 punti (-2,48%) con STMicroelectronics tra i titoli peggiori, e lo spread tra BTP e Bund "
                   "sale a 110 punti base.",
                   "Per Reuters è la quinta seduta di ribasso di fila dello STOXX 600, che chiude a 625,65. La perdita "
                   "della settimana supera il 5,7%, la peggiore da più di un anno.",
                   "Non è solo l'AI. Per dpa pesano anche i timori su inflazione e su una stretta della Fed. Tra i titoli colpiti: Siemens Energy perde il 6,5% e Scout24 circa il 7%."],
         "fonte": "Fonti: Reuters, dpa, ANSA, QuiFinanza, SoldiOnline; Euro Stoxx 50 via EODHD."},
        {"chiave": "fed", "tema": "Fed", "breve": "Cook e il PCE di mercoledì",
         "titolo": "Cook insiste sui rialzi mentre le borse scendono: il PCE decide",
         "misura": "mezzo",
         "righe": [["Chi", "Che cosa dice", "Quando"],
                   ["Waller", "Possibile rialzo da mezzo punto a dicembre", "novembre"],
                   ["Verbali Fed", "Nuovi rialzi probabili; alcuni più grandi di un quarto di punto", "18/11"],
                   ["Cook", "Aspettare rischia di restare indietro", "20/11"]],
         "larghezze": [20, 70, 18], "ruolo_righe": "chi",
         "perche": "Per Cook la crescita è forte e in accelerazione, il lavoro solido e l'inflazione ben sopra il 2% da 67 mesi. "
                   "Perciò aspettare rischia di costringere a rialzi più grandi dopo. A nostro avviso la caduta delle borse "
                   "per ora pesa meno di questi dati.",
         "quindi": "Mercoledì alle 14:30 il PCE: un dato di fondo, senza energia e alimentari, sopra il 3,2% atteso renderebbe più probabile il rialzo dell'8-9 dicembre.",
         "testo": ["Con le borse in correzione e i rendimenti in calo la Fed non dovrebbe frenare? Dipende da ciò che guarda. "
                   "Decide sui prezzi e sul lavoro, non sul listino, e per Cook l'inflazione non scende: «Waiting longer to "
                   "implement rate increases risks getting behind the curve».",
                   "I rendimenti, che seguono da vicino le attese sulla Fed, sono scesi. Ci leggiamo "
                   "una scommessa del mercato su una Fed meno dura dopo la caduta delle borse. È la lettura opposta a quella "
                   "di Cook, e il PCE di mercoledì decide chi ha ragione.",
                   "Conta la sorpresa più del livello: un dato di fondo al 3,2%, senza energia e alimentari, è già nei prezzi, e il mercato reagisce alla distanza "
                   "da quel numero."],
         "fonte": "Fonti: discorso di Cook (Federal Reserve), Reuters, verbali Fed e Waller dall'archivio della redazione."},
    ],
    "scommessa": {"lunedi": True, "venerdi": False, "settimana_prec": "16-20 novembre",
                  "com_e_andata": "Il crollo di Wall Street ha deciso la settimana: i Treasury hanno fatto da rifugio, l'oro no."},
    "parole": [("Correzione", "Un calo di oltre il 10% di un indice dal suo ultimo massimo."),
               ("Vendite forzate", "Vendite che chi investe con soldi presi in prestito deve fare, di solito, quando i prezzi scendono."),
               ("Rifugio", "Titolo o bene che si compra quando si ha paura, per mettere i soldi al riparo."),
               ("Rendimento", "L'interesse che un titolo di Stato rende: scende quando il prezzo sale."),
               ("Core", "L'inflazione senza energia e alimentari, le voci più instabili."),
               ("Guidance", "La previsione dell'azienda sul trimestre che comincia.")],
    "fonti": [
        ("Dati di mercato", "Financial Modeling Prep (indici USA e Asia, VIX, Brent e oro future, curva del Tesoro USA); EODHD "
                            "(Euro Stoxx 50, ACWI); Alpha Vantage (EUR/USD); ANSA (FTSE MIB); QuiFinanza e SoldiOnline (spread con la "
                            "Germania); COINOTAG (Kospi)."),
        ("Prima pagina e mercati", "AP, Reuters, Bloomberg, Fortune, 24/7 Wall St., Federal Reserve, QuiFinanza."),
        ("Calendario e agenda", "BEA, NYSE, archivio della redazione."),
        ("Approfondimenti", "Chip: AP, Reuters, documento Nvidia depositato il 17/11. Rifugio: Kitco (archivio), FMP. Europa: "
                            "Reuters, dpa, ANSA. Fed: Federal Reserve, Reuters."),
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
