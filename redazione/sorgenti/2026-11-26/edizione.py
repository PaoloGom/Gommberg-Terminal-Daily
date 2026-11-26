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
OGGI = dt.date(2026, 11, 26)
NOTA_DATI = "Chiusure al 25/11; Nikkei e Kospi al 26/11; Hang Seng alle 08:48."
REG = "2026-11-23-settimana.json"

d = lambda s: dt.date(2026, int(s[:2]), int(s[3:]))
VIX = [("11-11", 17.49), ("11-12", 18.70), ("11-13", 19.30), ("11-16", 22.91), ("11-17", 25.46), ("11-18", 24.56),
       ("11-19", 28.44), ("11-20", 35.89), ("11-23", 26.62), ("11-24", 26.36), ("11-25", 28.29)]
UST10 = [("11-16", 5.12), ("11-17", 5.10), ("11-18", 5.07), ("11-19", 5.04), ("11-20", 4.92), ("11-23", 4.92), ("11-24", 4.91), ("11-25", 4.85)]
UST2 = [("11-16", 4.83), ("11-17", 4.80), ("11-18", 4.80), ("11-19", 4.76), ("11-20", 4.63), ("11-23", 4.63), ("11-24", 4.63), ("11-25", 4.61)]
KOSPI = [("11-10", 5239.13), ("11-11", 5375.36), ("11-12", 5342.73), ("11-13", 5290.53), ("11-16", 5100.50), ("11-17", 4968.48),
         ("11-18", 5067.44), ("11-19", 5137.89), ("11-20", 4869.96), ("11-23", 4708.54), ("11-24", 5006.03), ("11-25", 4697.51),
         ("11-26", 4711.21)]
BRENT = [("11-18", 91.95), ("11-19", 91.98), ("11-20", 92.57), ("11-23", 89.37), ("11-24", 91.40), ("11-25", 94.61)]
BORSE_25 = [("Euro Stoxx 50", -1.82), ("FTSE MIB", -1.81), ("DAX", -1.26), ("Nasdaq", -0.62), ("S&P 500", -0.25)]

TAB = tabelle_da_dati("dati.json")
C = {
    "data": OGGI,
    "temi": ["Wall Street", "Tassi", "Dazi", "Asia", "Petrolio", "Credito"],
    "glossario": ["PCE", "core", "VIX", "CDS", "CME FedWatch", "pb", "EIA", "Kospi", "Nikkei", "Hang Seng", "DAX", "BTP"],
    "meccanismi": ["M14", "M26", "M05", "M01", "M23", "M24", "M17", "M11", "M10", "M16"],
    "ticker": ticker_da_dati("dati.json"),

    "top": {
        "tema": "Wall Street",
        "titolo": "Wall Street recupera quasi tutto il crollo e chiude appena in calo",
        "dek": "Mercoledì il Nasdaq è arrivato a perdere il 4,6% e l'S&P 500 il 3,2%, poi gli acquisti di fine seduta hanno riportato gli indici quasi in parità. Pesavano inflazione, nuovi dazi e dubbi sull'intelligenza artificiale. Oggi Wall Street è chiusa per il Ringraziamento. [[wall]]",
        "freccia": "Per l'AP i dubbi sul ritmo degli investimenti in intelligenza artificiale, dopo le elezioni di midterm, hanno pesato sui titoli.",
    },
    "quadro": "A nostro avviso i prezzi di stamattina raccontano due storie. Le azioni hanno quasi cancellato il crollo, ma l'indice della paura (VIX) è salito ancora del 7,3%. Il 10 anni cala nonostante l'inflazione, e il Brent sale su voci non confermate. Il rimbalzo è una pausa, non la fine dell'allarme.",
    "in30": [
        "I rendimenti dei titoli di Stato americani scendono malgrado un'inflazione più alta del previsto. [[tassi]]",
        "La banca centrale coreana alza i tassi il giorno dopo il crollo della borsa di Seul. [[corea]]",
        "I dazi proposti da Washington pesano sull'Europa prima ancora di entrare in vigore. [[dazi]]",
    ],
    "in30_temi": ["Tassi", "Asia", "Dazi"],
    "stamattina": [
        "Asia alle 08:48: Hang Seng +1,6%; Nikkei +0,86% e Kospi +0,29% a fine seduta",
        "EUR/USD alle 06:21: 1,0961, secondo l'AP",
        "Dollaro-yen alle 06:21: 159,12, secondo l'AP",
    ],
    "notizie": [
        {"tag": "Credito", "titolo": "S&P Global mette il rating AA di Nvidia sotto osservazione",
         "testo": "Il rischio di un taglio nasce dalla governance e non dai conti: l'agenzia cita la dipendenza da Jensen Huang, "
                  "dimesso il 12 novembre e rientrato lunedì. Decisione attesa entro circa 90 giorni.", "rimando": "wall"},
        {"tag": "Dazi", "titolo": "Washington propone nuovi dazi su 14 economie, non prima di gennaio",
         "testo": "La Cina rischia 20 punti in più sopra l'aliquota esistente, mentre per Unione europea, Giappone, Corea e "
                  "Taiwan l'aliquota resta nel tetto del 15% degli accordi.", "rimando": "dazi"},
        {"tag": "Petrolio", "titolo": "Voci di mine a Hormuz spingono il Brent al rialzo",
         "testo": "Sono report di media iraniani su petroliere finite su mine, senza conferma indipendente, ha scritto "
                  "Bloomberg.", "rimando": "petrolio"},
        {"tag": "Asia", "titolo": "La Corea del Sud alza i tassi al 3,25%",
         "testo": "La Bank of Korea cita inflazione persistente e una crescita più forte del previsto, trainata dall'export "
                  "di chip.", "rimando": "corea"},
        {"tag": "Chip", "titolo": "Infineon cede il 6,5% e guida il calo dei chip europei",
         "testo": "ASML perde il 5,8% e STMicroelectronics il 4,7%, nella giornata in cui l'Euro Stoxx 50 scende ai minimi da "
                  "maggio."},
        {"tag": "BCE", "titolo": "La BCE discute il raddoppio della riserva minima delle banche",
         "testo": "Secondo Reuters i vertici ne avrebbero parlato il 25 novembre; un resoconto anonimo dà la decisione a "
                  "dicembre o più tardi."},
    ],

    "mercati_titolo": "Numeri, temi aperti e calendario",
    "cruscotto": TAB["cruscotto"], "cruscotto_nota": TAB["cruscotto_nota"],
    "cross_data": TAB["cross_data"], "cross": TAB["cross"], "cross_nota": TAB["cross_nota"],
    "termometri": [
        ("Fed e tassi", "Riunione 8-9 dicembre", "Dati sopra le attese, rendimento in calo", "giu: Rendimento del 10 anni", "Riunione Fed dell'8-9 dicembre"),
        ("AI e chip", "Rimbalzo in Asia", "Rating di Nvidia sotto osservazione", "su: Chip e borse asiatiche stamattina", "Costo dell'assicurazione sul debito di CoreWeave"),
        ("Dazi", "Proposta su 14 economie", "Entrata in vigore non prima di gennaio", "giu: Borse europee", "Reazione dell'Unione europea"),
        ("Petrolio", "Brent a 94,61 $", "Voci di mine a Hormuz", "su: Brent in rialzo da lunedì", "Riunione OPEC+ del 29/11"),
    ],
    "fermi": "BCE e riserva minima delle banche (decisione rinviata, nessuna data verificata).",
    "lettura": "Il Russell 2000, l'indice delle società piccole, sale dello 0,7% mentre l'S&P 500 scende. Gli indici più "
               "seguiti pesano le società per il loro valore di borsa, e pochi giganti della tecnologia ne fanno gran parte: "
               "mercoledì sono loro ad aver trascinato giù l'S&P 500 e il Nasdaq, e a lasciar quasi indenni i piccoli titoli.",
    "ieri": [
        ("Mer 25, 14:30", "PCE USA di ottobre", "Core 3,3% (atteso 3,2%); totale 3,8%, in linea", "+", "[[tassi]]"),
        ("Gio 26", "Decisione della Bank of Korea", "Tasso al 3,25% da 3,00%", "", "[[corea]]"),
    ],
    "agenda": [
        ("Gio 26", "Wall Street e Treasury chiusi per il Ringraziamento", "Nessun dato USA in agenda", "Mercati senza il motore americano",
         "<b>Sopra:</b> non c'è un dato da leggere.<br/><b>Sotto:</b> con pochi scambi bastano poche operazioni per muovere i prezzi."),
        ("<b>Ven 27, 19:00</b>", "<b>Chiusura anticipata di Wall Street</b>", "<b>Seduta di mezza giornata, fino alle 13:00 a New York</b>",
         "<b>Evento n.1:</b> primo test dopo il rimbalzo",
         "<b>Sopra:</b> il VIX scende e il rimbalzo regge.<br/><b>Sotto:</b> il VIX resta alto e la calma era solo apparente."),
        ("Dom 29", "Riunione OPEC+", "Nessun consenso verificato", "Offerta di petrolio, con Hormuz sullo sfondo",
         "<b>Sopra:</b> più offerta frena il Brent.<br/><b>Sotto:</b> un taglio dell'offerta lo sostiene."),
        ("Mar 8, dicembre", "Riunione della Fed", "Rialzo di 25 pb scontato dai mercati", "Conferma o smentita del rialzo",
         "<b>Sopra:</b> un rialzo più forte alza il 2 anni.<br/><b>Sotto:</b> una pausa lo farebbe scendere."),
    ],
    "agenda_nota": "Giovedì Wall Street è chiusa e venerdì chiude alle 13:00 a New York: con la liquidità ridotta del Ringraziamento, i movimenti di questi due giorni vanno letti con cautela, perché poche operazioni bastano a spostare i prezzi. Il test vero della settimana per il rimbalzo è la seduta di venerdì, mentre la riunione della Fed dell'8-9 dicembre resta il prossimo evento che può cambiare i tassi.",
    "moduli": [
        {"chiave": "wall", "tema": "Wall Street", "breve": "il recupero non calma la paura",
         "titolo": "Wall Street recupera i prezzi ma non la calma: la paura sale ancora",
         "misura": "doppio",
         "grafico": {"tipo": "barre", "file": "c_wall.png",
                     "dati": [("S&P 500, minimo", -3.2), ("S&P 500, chiusura", -0.25), ("Nasdaq, minimo", -4.6), ("Nasdaq, chiusura", -0.62)],
                     "ordina": False, "dec": 2, "unita": "%", "soggetto": "azioni", "ruolo": "quanto",
                     "titolo": "A fine seduta il recupero ha cancellato quasi tutta la perdita",
                     "sottotitolo": "variazioni % del 25/11: minimo di giornata e chiusura"},
         "grafico2": {"tipo": "linee", "file": "c_vix.png", "x": [d(x) for x, _ in VIX],
                      "serie": [("VIX", [v for _, v in VIX], "#111111")], "soggetto": "VIX", "ruolo": "storia",
                      "titolo": "Il VIX non scende sotto 26 da cinque sedute", "sottotitolo": "VIX, chiusure",
                      "note": [(d("11-20"), 35.89, "20/11"), (d("11-25"), 28.29, "25/11")]},
         "numero": "15,34%: il costo annuo dell'assicurazione sul debito a 5 anni di CoreWeave.",
         "perche": "Le azioni sono risalite e il VIX è salito lo stesso: per l'AP i dubbi riguardano il ritmo degli investimenti in intelligenza artificiale, per Yahoo Finance i costi di finanziamento. A nostro avviso la paura è passata dalle azioni al debito.",
         "quindi": "Venerdì: VIX sotto 25, il recupero regge; sopra 28, era calma apparente.",
         "testo": ["Un Nasdaq che perde lo 0,6% sembra una giornata qualsiasi, ma in mezzo c'è stato un crollo del 4,6%, poi riassorbito dagli acquisti. Dice quanto gli investitori siano pronti a cambiare idea in poche ore. Un mercato che oscilla tanto in un giorno è un mercato in cui chi compra e chi vende non si fidano l'uno dell'altro.",
                   "Lo si vede nel VIX, che misura quanto gli operatori si aspettano che l'S&P 500 si muova nel prossimo mese, ricavandolo dal prezzo delle polizze di protezione. Ieri è salito del 7% con la borsa quasi ferma: chi si protegge paga caro anche dopo il rimbalzo.",
                   "Un secondo termometro è il costo di assicurarsi contro il fallimento di un'azienda, i cosiddetti CDS. Per i debiti a cinque anni di CoreWeave è arrivato, secondo Bloomberg, al 15,34% annuo. Record analoghi hanno toccato i contratti su Nvidia, Alphabet e Oracle. Chi presta soldi a queste società chiede di più per il rischio. A nostro avviso il nodo di mercoledì non è il prezzo dei titoli. È la capacità di queste imprese di finanziare, a tassi sostenibili, i data center che hanno promesso di costruire.",
                   "Nvidia ha poi un problema suo: S&P Global Ratings ha messo sotto osservazione il rating AA per questioni di governance e non di conti. L'agenzia indica l'indipendenza del consiglio, la dipendenza da Jensen Huang, dimesso il 12 novembre e rientrato lunedì, e l'esposizione alla Cina. Un taglio del rating alzerebbe il costo con cui Nvidia si indebita. In un momento in cui il mercato dubita già del debito dell'intelligenza artificiale, darebbe un segnale a tutto il settore."],
         "guardare": "Da seguire il costo di quelle assicurazioni: se resta ai massimi mentre le azioni risalgono, il rimbalzo ha le gambe corte. Per Nvidia la decisione di S&P arriva entro circa 90 giorni. Venerdì, con la seduta ridotta, è il primo banco di prova. Se i prezzi tengono anche con pochi scambi, il rimbalzo regge meglio di quanto sembri.",
         "fonte": "Fonti: AP, Yahoo Finance, Bloomberg, S&P Global Ratings tramite StockAnalysis.com; livelli del VIX da FMP."},
        {"chiave": "tassi", "tema": "Tassi USA", "breve": "rendimenti giù malgrado l'inflazione",
         "titolo": "Inflazione sopra le attese, ma il mercato guarda alla crescita",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_ust.png", "x": [d(x) for x, _ in UST10],
                     "serie": [("10 anni", [v for _, v in UST10], "#F26B1D"), ("2 anni", [v for _, v in UST2], "#111111")],
                     "soggetto": "rendimenti", "ruolo": "storia",
                     "titolo": "Rendimenti in flessione da una settimana, anche dopo il dato",
                     "sottotitolo": "Treasury 10 e 2 anni, chiusure (%)"},
         "righe": [["Dato di ottobre/Q3", "Uscito", "Atteso"],
                   ["Prezzi di fondo (core PCE), annuo", "3,3%", "3,2%"],
                   ["Prezzi dei consumi (PCE), annuo", "3,8%", "in linea"]],
         "larghezze": [60, 30, 30], "ruolo_righe": "quanto",
         "perche": "A nostro avviso il mercato ha pesato più il rischio per la crescita che l'inflazione. L'indice dei prezzi dei consumi al netto di energia e alimentari (core PCE) sale al 3,3%, un decimo sopra le attese. Di solito un dato così alza i rendimenti a breve. Ieri il 2 anni è sceso comunque, e il 10 anni di 6 pb. I titoli di Stato facevano da rifugio dai rischi di dazi e calo dei titoli dell'intelligenza artificiale.",
         "quindi": "Un 10 anni che torna sopra il 4,92% di lunedì e martedì direbbe che l'inflazione è tornata a contare più della paura. Oggi i mercati americani sono chiusi: nessun nuovo dato. Ne darebbe un primo segnale la seduta di venerdì, a Wall Street, che chiude alle 13:00 di New York.",
         "testo": ["Perché un dato che alza le attese sulla Fed ha fatto scendere il rendimento a 10 anni? Perché il 10 anni non "
                   "guarda solo alla Fed. Segue anche la crescita e i prezzi dei prossimi anni, mentre il 2 anni è più legato "
                   "alle mosse immediate della banca centrale. Così un'inflazione alta spinge su il breve, e il lungo può "
                   "scendere se si teme che dazi e borse in calo frenino l'economia. Quando si comprano titoli di Stato per "
                   "metterli al riparo il prezzo sale, e il rendimento, che si muove al contrario, scende.",
                   "Il rialzo di dicembre, intanto, è già scontato dai mercati. Secondo Reuters, il CME FedWatch, che ricava le probabilità dai future sui tassi, prezza 25 pb alla riunione dell'8-9 "
                   "dicembre, con il tasso ufficiale tra 3,75% e 4,00%."],
         "fonte": "Fonti: Reuters, Yahoo Finance, Longbridge; curva dei Treasury da FMP."},
        {"chiave": "dazi", "tema": "Dazi", "breve": "dazi in arrivo, borse già giù",
         "titolo": "I dazi sono ancora una proposta, ma l'Europa li ha già messi nei prezzi",
         "misura": "mezzo",
         "grafico": {"tipo": "barre", "file": "c_dazi.png", "dati": BORSE_25, "ordina": False, "dec": 2, "unita": "%",
                     "soggetto": "dazi", "ruolo": "quanto",
                     "titolo": "Le borse europee perdono più di quelle americane",
                     "sottotitolo": "variazioni % del 25/11"},
         "perche": "Washington ha proposto nuovi dazi su 14 economie, ma per ABC News e Yahoo Finance non entreranno in vigore "
                   "prima di gennaio. Per l'Europa le aliquote proposte restano nel tetto degli accordi. A nostro avviso il mercato non aspetta: chi vende ora paga in anticipo l'incertezza su "
                   "quanto toccherà, nei prossimi mesi, alle imprese che esportano negli Stati Uniti.",
         "quindi": "Gli indici europei di oggi mostrano se l'ondata di vendite è finita. L'Euro Stoxx 50 riparte dal livello più basso da maggio. Un nuovo calo direbbe che il mercato sta ancora prezzando i dazi. Conta anche se arrivano risposte dall'Unione europea.",
         "testo": ["I dazi del 25 novembre sono una proposta, non una decisione. Per la Cina il rialzo è di 20 punti sopra il circa 25% già in vigore. Per "
                   " Unione europea, Giappone, Corea e Taiwan le aliquote restano coerenti "
                   "con il tetto del 15% degli accordi.",
                   "Perché le borse reagiscono a una norma che non c'è? Un dazio è un costo in più sui beni importati. Il "
                   "peso si divide tra chi compra, chi importa e chi esporta. Le proporzioni cambiano da settore a settore. "
                   "Le imprese europee non sanno ancora quale parte toccherà a loro. Per dpa-AFX sul calo di mercoledì "
                   "hanno pesato insieme la fuga dai titoli dell'intelligenza artificiale, i nuovi dazi e le perdite delle "
                   "banche europee. Per questo oggi conta capire se l'ondata di vendite è finita o se i listini cercano ancora un prezzo."],
         "fonte": "Fonti: ABC News, Yahoo Finance, AP, Al Jazeera, RTE (AFP e Reuters), dpa-AFX, ANSA; livelli di FMP ed EODHD."},
        {"chiave": "corea", "tema": "Asia", "breve": "Seul alza i tassi dopo il crollo",
         "titolo": "La Corea alza i tassi il giorno dopo il crollo della borsa",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_kospi.png", "x": [d(x) for x, _ in KOSPI],
                     "serie": [("Kospi", [v for _, v in KOSPI], "#111111")], "soggetto": "Kospi", "ruolo": "storia",
                     "titolo": "Il Kospi ha perso quasi il 13% dal massimo dell'11 novembre",
                     "sottotitolo": "Kospi, chiusure (punti)",
                     "note": [(d("11-11"), 5375.36, "11/11"), (d("11-25"), 4697.51, "25/11")]},
         "perche": "La Bank of Korea ha alzato il tasso per un'inflazione persistente e una crescita più forte del previsto, "
                   "scrive il Korea Times. A nostro avviso guarda all'economia e non al Kospi. L'export di chip sostiene la crescita anche mentre i prezzi dei titoli crollano. Una banca centrale che guarda ai prezzi al consumo non può aspettare che la borsa si calmi.",
         "quindi": "Il livello da guardare è 4.697,51, la chiusura più bassa di mercoledì. Sotto, il rimbalzo di giovedì sarebbe cancellato. Il rialzo dei tassi peserebbe di più sulle banche e sugli investitori che comprano a credito, con effetti anche sui fondi esteri. Conta anche se gli stranieri tornano a comprare dopo le vendite di giovedì.",
         "testo": ["Una banca centrale che stringe mentre la borsa perde il 6% sembra un controsenso. A nostro avviso non lo è: l'inflazione resta il mandato della banca centrale, e l'export di chip continua a sostenere l'economia.",
                   "Il Kospi e la borsa di Taiwan pesano molto sui semiconduttori, perciò di solito seguono i chip americani della sera prima. Mercoledì il calo del 6,16% è arrivato dopo la vendita a Wall Street e, per il Korea Daily, con i timori sui dazi. Giovedì l'indice ha guadagnato oltre il 2% in seduta ma ha chiuso a +0,29%. Gli istituzionali hanno comprato per 750,9 miliardi di won e il retail ne ha venduti per 1.040. Gli stranieri hanno venduto per 113,6 miliardi: a comprare, nel giorno del rimbalzo, sono stati soprattutto i fondi coreani."],
         "fonte": "Fonti: Korea Times, Seoul Economic Daily, Korea Daily, Al Jazeera; chiusure di FMP."},
        {"chiave": "petrolio", "tema": "Petrolio", "breve": "Hormuz muove il greggio",
         "titolo": "Il Brent sale su voci di mine a Hormuz che nessuno conferma",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_brent.png", "x": [d(x) for x, _ in BRENT],
                     "serie": [("Brent", [v for _, v in BRENT], "#F26B1D")], "soggetto": "Brent", "ruolo": "storia",
                     "titolo": "Il Brent riparte dal minimo di lunedì", "sottotitolo": "Brent future, chiusure ($)",
                     "note": [(d("11-23"), 89.37, "23/11"), (d("11-25"), 94.61, "25/11")]},
         "numero": "+1,1 milioni di barili: l'aumento delle scorte USA di greggio, contro i +1,5 milioni attesi.",
         "perche": "Per Bloomberg il rialzo nasce dall'escalation in Medio Oriente e dai report iraniani di petroliere finite su "
                   "mine nello Stretto di Hormuz, notizie senza conferma indipendente.",
         "quindi": "Il livello da guardare è 94,61 dollari, la chiusura di mercoledì: sopra, il rialzo regge; sotto, rientra. Domenica 29 si riunisce l'OPEC+.",
         "testo": ["Il petrolio sale per una notizia che nessuno ha verificato. Le mine a Hormuz sono un'affermazione dei media "
                   "iraniani, e Bloomberg scrive di non avere conferme indipendenti. Eppure il Brent ha chiuso a 94,61 dollari, "
                   "in scambi sottili per la pausa americana del Ringraziamento.",
                   "Un rialzo che nasce da un rischio sulle forniture, e non da una domanda forte, di solito pesa sulla crescita. "
                   "Pesa anche sulle borse dei paesi che importano, come Europa e Giappone. Arriva poi presto alla benzina e al gasolio, "
                   "quindi all'inflazione complessiva, mentre sui prezzi di fondo ci mette più tempo."],
         "fonte": "Fonti: Bloomberg tramite Rigzone, OilPrice.com, Reuters; chiusure del Brent future da FMP."},
    ],
    "scommessa": {"tesi": "Con noi: Wall Street e oro hanno tenuto malgrado la paura. Contro: Europa, petrolio e rendimenti "
                          "americani vanno contro la previsione, perché dazi e Hormuz pesano più dei dati. Da qui a venerdì: "
                          "la seduta corta di Wall Street dice se il rimbalzo è vero.",
                  "lunedi": False, "venerdi": False, "settimana_prec": None},
    "parole": [("Costo dell'assicurazione sul debito", "Quanto si paga ogni anno per assicurarsi contro il mancato rimborso di "
                                                      "un prestito: sale quando cresce il rischio che l'azienda non paghi."),
               ("Indice della paura", "Misura quanto gli operatori si aspettano che l'S&P 500 si muova nel prossimo mese."),
               ("Inflazione di fondo", "I prezzi senza energia e alimentari, le voci più volatili: mostrano la tendenza "
                                       "di fondo."),
               ("Rating in osservazione", "L'agenzia avvisa che potrebbe cambiare il giudizio sul debito di una società, di "
                                          "solito entro alcuni mesi."),
               ("Scambi sottili", "Giornate con pochi scambi: poche operazioni bastano a muovere i prezzi."),
               ("Riserva minima delle banche", "La quota di depositi che le banche devono tenere presso la banca centrale.")],
    "fonti": [
        ("Dati di mercato", "Financial Modeling Prep (S&P 500, Nasdaq, Russell 2000, VIX, Nikkei 225, Brent e oro future, curva dei Treasury); "
                            "EODHD e dpa-AFX (Euro Stoxx 50, ACWI); Alpha Vantage (EUR/USD); ANSA (FTSE MIB); Seoul Economic Daily, "
                            "Korea Times (Kospi); Share Talk (Hang Seng, Nikkei)."),
        ("Prima pagina e mercati", "AP, Yahoo Finance, Reuters, Bloomberg, Il Sole 24 Ore, Milano Finanza, ANSA, QuiFinanza, "
                                   "Teleborsa, Korea Herald, Korea Times, Korea Daily, Al Jazeera."),
        ("Calendario e agenda", "Investrade, LiteFinance, Reuters."),
        ("Approfondimenti", "Wall Street: AP, Yahoo Finance, Bloomberg, StockAnalysis.com. Tassi: Reuters, Yahoo Finance, "
                            "BullionVault. Dazi: ABC News, Yahoo Finance, dpa-AFX. Asia: Korea Times, Seoul Economic Daily. "
                            "Petrolio: Bloomberg, OilPrice.com, Reuters."),
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
