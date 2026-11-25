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
OGGI = dt.date(2026, 11, 25)
NOTA_DATI = "Chiusure al 24 novembre; Nikkei 225 e Kospi al 25 novembre; Hang Seng al 24 novembre"
REG = "2026-11-23-settimana.json"          # registro della scommessa (redazione/pronostici/)

# ============================ DATI DEI GRAFICI (verificati) ============================
NASDAQ = [("10-20", 26424.82), ("10-21", 26702.86), ("10-22", 26008.86), ("10-23", 25955.34), ("10-26", 26169.38),
          ("10-27", 26477.81), ("10-28", 26549.85), ("10-29", 26184.72), ("10-30", 25437.00), ("11-02", 25164.32),
          ("11-03", 25372.01), ("11-04", 25736.51), ("11-05", 24315.00), ("11-06", 24579.42), ("11-09", 25253.14),
          ("11-10", 25065.87), ("11-11", 25466.19), ("11-12", 25366.09), ("11-13", 25136.27), ("11-16", 24509.76),
          ("11-17", 24328.38), ("11-18", 24429.88), ("11-19", 23879.20), ("11-20", 22617.73), ("11-23", 24089.56),
          ("11-24", 23733.54)]
UST = [  # data, 2 anni, 10 anni (curva par del Tesoro, FMP)
    ("10-26", 4.68, 5.00), ("10-27", 4.70, 4.99), ("10-28", 4.67, 5.05), ("10-29", 4.61, 4.98), ("10-30", 4.56, 4.94),
    ("11-02", 4.59, 4.91), ("11-03", 4.61, 4.95), ("11-04", 4.58, 4.90), ("11-05", 4.46, 4.84), ("11-06", 4.51, 4.86),
    ("11-09", 4.56, 4.88), ("11-10", 4.73, 4.98), ("11-12", 4.86, 5.10), ("11-13", 4.88, 5.15), ("11-16", 4.83, 5.12),
    ("11-17", 4.80, 5.10), ("11-18", 4.80, 5.07), ("11-19", 4.76, 5.04), ("11-20", 4.63, 4.92), ("11-23", 4.63, 4.92),
    ("11-24", 4.63, 4.91)]
BRENT = [("10-26", 115.81), ("10-27", 113.88), ("10-28", 115.32), ("10-29", 110.80), ("10-30", 113.43), ("11-02", 104.77),
         ("11-03", 103.60), ("11-04", 94.62), ("11-05", 98.29), ("11-06", 98.32), ("11-09", 92.57), ("11-10", 91.49),
         ("11-11", 92.76), ("11-12", 95.82), ("11-13", 95.84), ("11-16", 92.44), ("11-17", 93.14), ("11-18", 91.95),
         ("11-19", 91.98), ("11-20", 92.57), ("11-23", 89.37), ("11-24", 91.40)]
d = lambda s: dt.date(2026, int(s[:2]), int(s[3:]))   # "MM-GG" -> data

TAB = tabelle_da_dati("dati.json")
C = {
    "data": OGGI,
    "temi": ["Asia", "Chip", "Dazi", "Fed", "Europa", "Petrolio"],
    "glossario": ["DRAM", "NAND", "CXMT", "PCE", "CME FedWatch", "Kospi", "OPAS", "Nasdaq", "ACEA", "pb"],
    "meccanismi": ["M17", "M16", "M06", "M24", "M20", "M04", "M05", "M10", "M11"],

    "ticker": ticker_da_dati("dati.json"),

    "top": {
        "tema": "Asia",
        "titolo": "Seul perde il 6% e l'Asia vende i chip, mentre tornano i dazi",
        "dek": "Il Kospi chiude a 4.697,51 (-6,16%), il minimo dal 13 gennaio, con SK Hynix a -11,05% e Samsung "
               "Electronics a -9,87%. Tokyo segue: il Nikkei 225 cede il 2,8% e SoftBank più di ogni altro titolo. Pesano la Wall Street "
               "di martedì, dove Nvidia ha perso il 5,86% dopo il +31,5% del giorno prima, e le indiscrezioni su nuovi dazi "
               "americani contro 16 economie. [[chip]]",
    },
    "quadro": "Lo stesso giorno i prezzi dicono due cose. Nel Dow Jones in rialzo (+0,85%) mentre il Nasdaq perde, leggiamo "
              "una rotazione dai tecnologici verso i titoli meno legati al ciclo, non una fuga dal rischio. Il Treasury a 10 "
              "anni resta a 4,91%: con un rialzo della Fed quasi scontato, la paura sulle borse non basta a farlo scendere. "
              "L'euro guadagna lo 0,6% sul dollaro, il Brent risale a 91,40 dollari ma resta lontano dai livelli di "
              "ottobre, e l'oro cede il 2,5% dopo il rimbalzo di lunedì.",
    "in30": [
        "Gli Stati Uniti sarebbero pronti a pubblicare i risultati dell'indagine su 16 economie, e con loro nuovi dazi. [[dazi]]",
        "Alle 14:30 escono i prezzi PCE di ottobre e il Pil americano del terzo trimestre. [[agenda]]",
        "A Milano parte l'offerta di Intesa Sanpaolo su Mps, nel giorno in cui il Ftse Mib perde quasi il 2%. [[europa]]",
    ],
    "in30_temi": ["Dazi", "Macro", "Banche"],
    "stamattina_titolo": "Cosa guardare all'apertura",
    "stamattina": [
        "Alle 14:30 PCE di ottobre e Pil americano del terzo trimestre (seconda stima)",
        "Alle 15:30 apre Wall Street: si vede se Micron e i chip americani recuperano",
        "Giovedì 26 Wall Street è chiusa per il Ringraziamento; venerdì chiude alle 19:00 ora di Roma",
    ],
    "notizie": [
        {"tag": "Tecnologia", "titolo": "BNP Paribas taglia il giudizio su Micron e il titolo crolla",
         "testo": "La banca vede rischi sui piani di capacità del 2028 dei grandi operatori del cloud. Martedì il titolo ha "
                  "perso circa l'11% e ha trascinato i chip americani.",
         "rimando": "chip"},
        {"tag": "Italia", "titolo": "STMicroelectronics e Technoprobe perdono il 10% a Milano",
         "testo": "Prysmian cede l'8%. Le vendite arrivano dopo il rimbalzo di lunedì.", "rimando": "europa"},
        {"tag": "Europa", "titolo": "Stellantis perde quota in Europa e a ottobre immatricola il 7% di auto in meno",
         "testo": "Nell'Unione europea le immatricolazioni scendono a 129.902 e la quota di mercato passa dal 15,3% al 13,8%.",
         "rimando": "europa"},
        {"tag": "Fed", "titolo": "Il mercato dà quasi per certo il rialzo della Fed a dicembre",
         "testo": "Secondo CME FedWatch la probabilità di un rialzo a dicembre è al 99%, e al 64% quella di un altro a gennaio.", "rimando": "fed"},
        {"tag": "Petrolio", "titolo": "Surplus di offerta e colloqui con l'Iran tengono il petrolio sotto i 92 dollari",
         "testo": "Il Brent chiude a 91,40 dollari, ben sotto i 115,81 del 26 ottobre.", "rimando": "petrolio"},
        {"tag": "Credito", "titolo": "Moody's alza il rating di Mps e Mediobanca a Baa2",
         "testo": "Il giudizio sale da Baa3 per entrambe, nel giorno prima dell'avvio dell'offerta di Intesa Sanpaolo.",
         "rimando": "europa"},
    ],

    "mercati_titolo": "Numeri, temi aperti e calendario",
    "cruscotto": TAB["cruscotto"], "cruscotto_nota": TAB["cruscotto_nota"],
    "cross_data": TAB["cross_data"], "cross": TAB["cross"], "cross_nota": TAB["cross_nota"],
    "termometri": [
        ("Fed e tassi", "Rialzo di dicembre quasi certo", "Il 10 anni resta sotto il massimo di metà mese", "fermo: Rendimento del 10 anni", "PCE core delle 14:30"),
        ("AI e chip", "Seconda giornata di vendite", "Micron e SK Hynix cedono circa l'11%", "giu: Titoli delle memorie", "Apertura del Nasdaq alle 15:30"),
        ("Dazi", "Risultati dell'indagine attesi", "Tre fonti anonime parlano di 16 economie", "su: Timore di nuovi dazi", "Reazione dell'Unione europea"),
        ("Petrolio", "Brent a 91,40 $", "Risale dopo il minimo di lunedì", "su: Brent, in rimbalzo", "Colloqui con l'Iran"),
    ],
    "fermi": "Fondo di stabilizzazione del governo di Seul (nessuna novità verificata dal 23/11).",
    "lettura": "Il Russell 2000, l'indice delle società più piccole, sale (+0,6%) mentre l'S&amp;P 500 e il "
               "Nasdaq scendono: le vendite colpiscono i grandi nomi dell'intelligenza artificiale più "
               "di chi ne dipende poco. E il Brent a -21,7% in un mese contro il 7,8% in meno dell'oro dice, per noi, che il "
               "greggio scende per ragioni sue e non perché il mondo cerchi rifugio.",

    "ieri": [
        ("Mar 24", "Avvio dell'offerta di Intesa Sanpaolo su Mps", "1,25 euro e 1,664 azioni Intesa per ogni azione Mps", "", "[[europa]]"),
        ("Mar 24", "Immatricolazioni di auto in Europa (ottobre)", "Stellantis 129.902 auto, -7,0% su un anno", "", "[[europa]]"),
    ],
    "agenda": [
        ("<b>Mer 25, 14:30</b>", "<b>Prezzi PCE di ottobre</b>", "<b>Core +0,3% sul mese; prima +3,1% su un anno</b>",
         "<b>Evento n.1:</b> l'inflazione che decide quanto durano i tassi alti",
         "<b>Sopra:</b> salgono dollaro e rendimenti a breve, e il rialzo di gennaio diventa più probabile."
         "<br/><b>Sotto:</b> i rendimenti scendono e le borse respirano."),
        ("Mer 25, 14:30", "Pil USA del terzo trimestre (seconda stima)", "Prima stima +3,4% annualizzato",
         "Tenuta dell'economia con tassi alti",
         "<b>Sopra:</b> l'economia regge e la Fed ha meno ragioni di fermarsi.<br/><b>Sotto:</b> torna il timore di una frenata."),
        ("Gio 26, 15:30", "Wall Street chiusa per il Ringraziamento", "Niente seduta; anche i Treasury sono fermi",
         "Meno scambi, meno prezzi di riferimento", "Si ascolta l'Asia di venerdì: con Wall Street ferma, i chip asiatici non hanno un riferimento."),
        ("Ven 27, 19:00", "Chiusura anticipata di Wall Street", "Seduta più corta, a ridotta liquidità",
         "Pochi scambi amplificano i movimenti", "Si ascolta se i volumi restano bassi: con pochi scambi anche vendite modeste muovono i prezzi."),
    ],
    "moduli": [
        {"chiave": "chip", "tema": "Chip e Asia", "breve": "memorie e Asia in caduta",
         "titolo": "Le banche vedono calare le memorie nel 2028 e Seul perde il 6%",
         "misura": "doppio",
         "grafico": {"tipo": "barre", "file": "c_memorie.png",
                     "dati": [("Nvidia (24/11)", -5.86), ("Indice dei chip USA (24/11)", -7.88), ("Micron (24/11)", -10.97),
                              ("Kospi (25/11)", -6.16), ("Samsung (25/11)", -9.87), ("SK Hynix (25/11)", -11.05)],
                     "ordina": False, "dec": 2, "unita": "%", "soggetto": "memorie", "ruolo": "quanto",
                     "titolo": "Le memorie perdono più di Nvidia e dell'indice dei chip",
                     "sottotitolo": "variazioni % del 24/11 a Wall Street e del 25/11 a Seul"},
         "grafico2": {"tipo": "linee", "file": "c_nasdaq.png", "x": [d(x) for x, _ in NASDAQ],
                      "serie": [("Nasdaq", [v for _, v in NASDAQ], "#111111")], "soggetto": "Nasdaq", "ruolo": "storia",
                      "titolo": "Il Nasdaq è a -10,6% dal massimo del 28 ottobre", "sottotitolo": "Nasdaq Composite, punti",
                      "eventi": [(d("11-23"), "Huang torna")],
                      "note": [(d("10-28"), 26549.85, "28/10"), (d("11-24"), 23733.54, "24/11")]},
         "righe": [["Target di prezzo tagliati", "SK Hynix (won)", "Samsung Electronics (won)", "Data"],
                   ["Goldman Sachs", "da 3,5 mln a 2 mln", "da 500.000 a 350.000", "Domenica 22/11"],
                   ["Morgan Stanley", "da 2,6 mln a 1,6 mln", "da 381.000 a 309.000", "10/11"]],
         "larghezze": [40, 40, 46, 30], "ruolo_righe": "perche",
         "perche": "Secondo Goldman Sachs e Morgan Stanley, dal 2028 l'offerta di memorie dovrebbe raggiungere la domanda, "
                   "anche per l'espansione del produttore cinese CXMT. Per questo hanno tagliato i target su SK Hynix e Samsung. Morgan Stanley parla di un «profit cliff» del 2028, per la nuova capacità attesa dalla fine del 2027. A nostro avviso oggi il mercato sconta in anticipo quel calo di prezzi. Il Nasdaq, con i chip in testa, resta sotto i massimi di ottobre.",
         "numero": "Quasi l'11% in due giorni e in due Paesi: Micron a New York, SK Hynix a Seul. Per noi il calo segue le "
                   "ore di apertura delle borse.",
         "quindi": "Alle 15:30 riapre Wall Street: Micron è il primo titolo da guardare per capire se la caduta continua.",
         "testo": ["Come può un titolo perdere più di un decimo del suo valore in un giorno se vende chip che tutti vogliono? "
                   "Perché oggi non si giudica il trimestre ma il 2028. Per le banche d'affari tra due anni le memorie "
                   "saranno troppe e i prezzi scenderanno, e leggiamo la caduta di oggi come la messa in prezzo anticipata "
                   "di quel calo. Un titolo vale gli utili dei prossimi anni, quindi anche una previsione lontana tende a "
                   "pesare subito sul prezzo.",
                   "A perdere più di Nvidia sono le memorie perché, di solito, il prezzo di una memoria cambia con "
                   "l'equilibrio tra chi la produce e chi la compra. Goldman Sachs prevede che il divario tra offerta e "
                   "domanda di DRAM si stringa dal 5,1% del prossimo anno all'1,2% nel 2028. Sempre per Goldman Sachs, "
                   "DRAM e NAND perderanno ciascuna circa il 20% di prezzo.",
                   "BNP Paribas ha seguito la stessa logica con Micron: vede rischi sui piani di capacità del 2028 dei grandi "
                   "operatori del cloud. Il titolo ha ceduto "
                   "martedì, e il giorno dopo SK Hynix ha fatto lo stesso a Seul.",
                   "Seul pesa molto in questa storia perché Kospi e borsa di Taiwan hanno un peso alto nei semiconduttori, "
                   "e di solito si muovono con i chip americani della sera prima. Il Nikkei 225 ha perso meno della metà "
                   "del Kospi."],
         "guardare": "Decide l'apertura di Wall Street alle 15:30. Un recupero di Micron e dei produttori di chip direbbe "
                     "che il calo asiatico era eccessivo. Un'altra seduta in rosso farebbe dei prezzi delle memorie del "
                     "2028 il tema dei prossimi mesi.",
         "fonte": "Fonti: Korea Times, Seoul Economic Daily, AP, Reuters, Yahoo Finance; target delle due banche d'affari."},
        {"chiave": "dazi", "tema": "Dazi", "breve": "16 economie nel mirino",
         "titolo": "Gli Stati Uniti preparano nuovi dazi su 16 economie e l'Asia vende in anticipo",
         "misura": "mezzo",
         "perche": "Secondo tre fonti citate da Reuters, l'amministrazione Trump è pronta a pubblicare i risultati "
                   "dell'indagine sull'eccesso di capacità industriale in 16 economie. Tra queste ci sono Cina, Unione europea "
                   "e Corea del Sud, e il passo potrebbe aprire la strada a nuovi dazi.",
         "quindi": "Entro giovedì, quando Wall Street è chiusa per il Ringraziamento, si vede se i risultati escono. Conta "
                   "allora la risposta dell'Unione europea, che chiede di restare sotto il tetto dell'accordo di Turnberry e di non "
                   "superarlo con nuove aliquote.",
         "testo": ["Un dazio che non c'è ancora fa già vendere, perché il prezzo di un titolo sconta oggi i "
                   "margini di domani. Un dazio aumenta il costo dei beni importati. Il peso si divide tra chi importa, "
                   "chi compra e chi esporta. Le proporzioni dipendono dal settore, e finché non si sa quali le borse "
                   "tendono a prezzare il caso peggiore.",
                   "Nessuna aliquota è ufficiale: le indiscrezioni dicono soltanto che i risultati sono pronti. "
                   "L'Unione europea ha già chiesto che ogni nuovo dazio rispetti il tetto complessivo concordato "
                   "con gli Stati Uniti a Turnberry. Per questo la lettura resta prudente: l'effetto di un dazio su cambi e "
                   "borse non ha un verso fisso.",
                   "Chi paga alla fine? L'importatore può assorbire il costo nei margini o girarlo a chi compra, mentre "
                   "l'esportatore può abbassare il prezzo per restare competitivo. Per questo la stessa notizia pesa in "
                   "modo diverso su settori e paesi, e le borse reagiscono prima di sapere chi pagherà. I risultati "
                   "dell'indagine sono attesi tra il 24 e il 25 novembre: la loro pubblicazione è il passaggio che "
                   "trasforma un timore in aliquote."],
         "numero": "15%: il tetto complessivo dell'accordo di Turnberry, il metro con cui l'Unione europea chiede di misurare ogni nuova aliquota. Su quella soglia si leggeranno i risultati dell'indagine, appena usciranno.",
         "fonte": "Fonti: Reuters, The Private Banker, Political.org."},
        {"chiave": "fed", "tema": "Fed e tassi", "breve": "rialzo scontato, PCE alle 14:30",
         "titolo": "Con il rialzo di dicembre scontato, il PCE dice quanto dureranno i tassi alti",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_ust.png", "x": [d(r[0]) for r in UST], "soggetto": "tassi",
                     "titolo": "Il 10 anni torna sotto il 5% il 20 novembre e ci resta",
                     "sottotitolo": "rendimento Treasury a 10 anni, chiusure (%)", "ruolo": "storia", "soglie": [(5.0, "5%")],
                     "serie": [("10 anni", [r[2] for r in UST], "#F26B1D")]},
         "perche": "Il mercato dà il rialzo di dicembre per quasi certo. Di solito, quando una mossa è già nei prezzi, il dato di "
                   "oggi cambia la durata più che la direzione.",
         "numero": "-24 pb: il calo del 10 anni dal massimo del 13 novembre. Intanto la probabilità di un rialzo a "
                  "dicembre arriva al 99% secondo CME FedWatch, che la calcola sui future sui tassi.",
         "quindi": "Un PCE senza energia e alimentari sopra il +0,3% atteso sul mese riaprirebbe il rialzo anche a gennaio, già scontato al 64%.",
         "testo": ["Il rialzo è già nei prezzi, eppure il dato di oggi conta ancora. Le probabilità dei future "
                   "sui tassi sono scommesse del mercato e non previsioni ufficiali, e cambiano in fretta con i dati. Il "
                   "PCE misura i prezzi pagati dai consumatori americani, e la sua parte core esclude energia e alimentari.",
                   "Conta la sorpresa più del livello. Il consenso per il core di ottobre è +0,3% sul mese. Un numero "
                   "uguale vale poco, mentre un decimo in più o in meno sposta le attese sulla Fed e il rendimento a breve.",
                   "A nostro avviso il 10 anni resta fermo perché due spinte si compensano: una Fed più dura tende a "
                   "alzarlo, la paura sulle borse a abbassarlo.",
                   "Per le borse la durata dei tassi alti conta. I "
                   "titoli tecnologici valgono soprattutto per utili lontani, e a parità di utili attesi tassi più alti "
                   "riducono il valore di quegli utili oggi e li penalizzano più degli altri."],
         "fonte": "Fonti: Investing.com, CME FedWatch; curva del Tesoro USA, FMP."},
        {"chiave": "europa", "tema": "Europa e Italia", "breve": "Milano cede, offerta su Mps",
         "titolo": "Milano cede quasi il 2% perché STMicroelectronics e Technoprobe perdono il 10%",
         "misura": "mezzo",
         "grafico": {"tipo": "barre", "file": "c_milano.png",
                     "dati": [("Euro Stoxx 50", -1.16), ("FTSE MIB", -1.84), ("Prysmian", -8.04), ("Technoprobe", -10.09),
                              ("STMicroelectronics", -10.21)],
                     "ordina": False, "dec": 2, "unita": "%", "soggetto": "Milano", "ruolo": "quanto",
                     "titolo": "I titoli dei chip perdono cinque volte l'indice di Milano",
                     "sottotitolo": "variazioni % del 24/11"},
         "perche": "Secondo dpa-AFX le vendite arrivano tra prese di beneficio dopo il rimbalzo di lunedì, timori sul "
                   "rialzo della Fed e dubbi sull'intelligenza artificiale.",
         "numero": "31,4 miliardi di euro: il valore dell'offerta di Intesa Sanpaolo su Mps, aperta alle adesioni fino al 22 gennaio.",
         "quindi": "Il test è l'apertura di oggi: se STMicroelectronics e Technoprobe recuperano quanto perso ieri erano "
                   "prese di beneficio, se scendono ancora il tema è la tecnologia.",
         "testo": ["Il Ftse Mib scende dell'1,84% e l'Euro Stoxx 50 dell'1,16%. I chip in Europa perdono molto di più, "
                   "e a Milano tre titoli cedono circa un decimo del valore. Un indice è una media dei titoli, e quando tre di loro perdono tanto in un giorno il resto lo attutisce.",
                   "A Milano si gioca anche una partita che con la tecnologia non c'entra. È partita l'offerta di Intesa "
                   "Sanpaolo su Mps: 1,25 euro e 1,664 azioni Intesa per ogni azione, con adesioni fino al 22 gennaio. Il "
                   "giorno prima Moody's aveva alzato a Baa2 il rating di Mps e Mediobanca.",
                   "Fuori dalla Borsa, i dati dell'associazione dei costruttori europei mostrano che a ottobre Stellantis ha "
                   "perso quota sul mercato dell'Unione. Non dipende dall'intelligenza artificiale: a Milano la giornata "
                   "non è stata soltanto una questione di chip."],
         "fonte": "Fonti: ANSA, Money.it, dpa-AFX, ACEA, Teleborsa, Radiocor."},
        {"chiave": "petrolio", "tema": "Petrolio", "breve": "il barile perde un quinto",
         "titolo": "Il petrolio perde un quinto in un mese anche con le borse in rotta",
         "misura": "mezzo",
         "grafico": {"tipo": "barre", "file": "c_brent.png",
                     "dati": [("Settimana al 6/11", round((98.32 / 113.43 - 1) * 100, 1)),
                              ("Settimana al 13/11", round((95.84 / 98.32 - 1) * 100, 1)),
                              ("Settimana al 20/11", round((92.57 / 95.84 - 1) * 100, 1)),
                              ("23 e 24/11", round((91.40 / 92.57 - 1) * 100, 1))],
                     "ordina": False, "dec": 1, "unita": "%", "soggetto": "petrolio", "ruolo": "storia",
                     "titolo": "Il calo del petrolio si è concentrato nella prima settimana di novembre",
                     "sottotitolo": "variazione % del Brent future su chiusura precedente, per settimana"},
         "perche": "Il calo ha due cause che la domanda non spiega: i colloqui tra Stati Uniti e Iran e un surplus di circa "
                   "2 milioni di barili al giorno. La stima è dell'Agenzia internazionale dell'energia, riportata da Bloomberg.",
         "quindi": "Oggi pomeriggio PCE e Pil dicono se la domanda americana tiene: è il test per un barile che ha già perso "
                   "un quinto.",
         "numero": "89,37 $: il minimo del mese, toccato lunedì 23. Ieri il Brent ha recuperato il 2,3%.",
         "testo": ["Perché il petrolio scende mentre le borse hanno paura? Di solito un barile in calo accompagna una "
                   "domanda debole, ma qui il motivo è l'offerta: il surplus stimato dall'Agenzia internazionale dell'energia e le speranze di intesa con "
                   "l'Iran. Un petrolio che scende per eccesso di offerta tende ad aiutare i paesi che lo importano, come "
                   "l'Europa e il Giappone.",
                   "Il passaggio verso i prezzi è rapido: il greggio diventa benzina e gasolio in poche settimane. Un barile "
                   "più basso alleggerisce prima l'inflazione complessiva e solo dopo, e meno, quella core."],
         "fonte": "Fonti: Bloomberg via Rigzone; chiusure del Brent future (FMP)."},
    ],

    "scommessa": {"tesi": "Con noi: la ripresa di lunedì ha riportato le borse sopra la base e il petrolio più basso aiuta. "
                          "Contro: il rialzo della Fed quasi certo tiene fermi i rendimenti e l'euro. "
                          "Da qui a venerdì: i prezzi PCE di oggi e la seduta corta di venerdì.",
                  "lunedi": False, "venerdi": False, "settimana_prec": None},
    "parole": [("Memorie DRAM e NAND", "I chip che tengono i dati: la DRAM è la memoria di lavoro, la NAND quella dove i "
                                       "dati restano. Il loro prezzo segue l'equilibrio tra chi produce e chi compra."),
               ("Target di prezzo", "Il prezzo a cui un analista pensa che un titolo arriverà tra circa un anno: tagliarlo "
                                    "vuol dire ridurre le attese sugli utili."),
               ("Eccesso di capacità", "Quando un settore produce più di quanto il mercato compra: i prezzi calano e gli "
                                       "altri paesi accusano chi ha fabbriche in più di scaricare il surplus fuori."),
               ("Rotazione", "Il passaggio dei soldi da un gruppo di titoli a un altro, per esempio dai tecnologici ai "
                             "settori che dipendono meno dall'economia."),
               ("PCE core", "L'indice dei prezzi pagati dai consumatori americani senza energia e alimentari, le voci che "
                            "variano di più."),
               ("Probabilità dei future sui tassi", "La probabilità che il mercato assegna a una mossa della Fed, ricavata "
                                                    "dai prezzi dei future: non è una previsione ufficiale.")],
    "fonti": [
        ("Dati di mercato", "Financial Modeling Prep (indici USA, Nikkei 225, Hang Seng, VIX, Brent e oro future, curva "
                            "del Tesoro USA); Alpha Vantage (EUR/USD, ACWI); EODHD e dpa-AFX (Euro Stoxx 50); Money.it e "
                            "ANSA (FTSE MIB); le testate coreane (Kospi)."),
        ("Prima pagina e mercati", "Korea Times, Seoul Economic Daily, AP, Reuters, Yahoo Finance, Investing.com, ANSA, "
                                   "Money.it, dpa-AFX, Il Sole 24 Ore."),
        ("Calendario e agenda", "Investing.com, FinancialJuice, HyperStocks, Investrade, LiteFinance."),
        ("Approfondimenti", "Chip e Asia: AP, Reuters, Yahoo Finance, Korea Times. Dazi: Reuters, "
                            "The Private Banker, Political.org. Fed: Investing.com, CME FedWatch. Europa: ANSA, "
                            "Money.it, dpa-AFX, ACEA, Teleborsa, Radiocor. Petrolio: Bloomberg via Rigzone."),
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
