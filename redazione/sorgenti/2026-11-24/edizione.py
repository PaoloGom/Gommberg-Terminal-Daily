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
OGGI = dt.date(2026, 11, 24)
NOTA_DATI = "Chiusure al 23 novembre; Asia di martedì 24 novembre (Kospi in chiusura, Nikkei e Hang Seng al mattino)"
REG = "2026-11-23-settimana.json"

d = lambda s: dt.date(2026, int(s[:2]), int(s[3:]))
SP = [("10-26", 7676.77), ("10-27", 7722.60), ("10-28", 7743.98), ("10-29", 7720.39), ("10-30", 7580.07), ("11-02", 7541.40),
      ("11-03", 7568.92), ("11-04", 7688.62), ("11-05", 7353.73), ("11-06", 7376.86), ("11-09", 7549.94), ("11-10", 7520.93),
      ("11-11", 7619.38), ("11-12", 7592.40), ("11-13", 7561.67), ("11-16", 7416.59), ("11-17", 7340.53), ("11-18", 7323.63),
      ("11-19", 7175.83), ("11-20", 6910.39), ("11-23", 7237.17)]
UST = [("10-26", 4.68, 5.00), ("10-27", 4.70, 4.99), ("10-28", 4.67, 5.05), ("10-29", 4.61, 4.98), ("10-30", 4.56, 4.94),
       ("11-02", 4.59, 4.91), ("11-03", 4.61, 4.95), ("11-04", 4.58, 4.90), ("11-05", 4.46, 4.84), ("11-06", 4.51, 4.86),
       ("11-09", 4.56, 4.88), ("11-10", 4.73, 4.98), ("11-12", 4.86, 5.10), ("11-13", 4.88, 5.15), ("11-16", 4.83, 5.12),
       ("11-17", 4.80, 5.10), ("11-18", 4.80, 5.07), ("11-19", 4.76, 5.04), ("11-20", 4.63, 4.92), ("11-23", 4.63, 4.92)]
BRENT = [("10-26", 115.81), ("10-27", 113.88), ("10-28", 115.32), ("10-29", 110.80), ("10-30", 113.43), ("11-02", 104.77),
         ("11-03", 103.60), ("11-04", 94.62), ("11-05", 98.29), ("11-06", 98.32), ("11-09", 92.57), ("11-10", 91.49),
         ("11-11", 92.76), ("11-12", 95.82), ("11-13", 95.84), ("11-16", 92.44), ("11-17", 93.14), ("11-18", 91.95),
         ("11-19", 91.98), ("11-20", 92.57), ("11-23", 89.37)]
ORO = [("10-26", 4038.4), ("10-27", 4074.6), ("10-28", 4051.6), ("10-29", 4031.4), ("10-30", 3898.9), ("11-02", 3969.6),
       ("11-03", 3940.4), ("11-04", 4073.0), ("11-05", 4113.5), ("11-06", 4074.9), ("11-09", 4114.5), ("11-10", 4030.2),
       ("11-11", 4000.5), ("11-12", 3885.3), ("11-13", 3886.3), ("11-16", 3853.0), ("11-17", 3864.2), ("11-18", 3741.9),
       ("11-19", 3685.5), ("11-20", 3515.4), ("11-23", 3651.4)]
RIMBALZO = [("Nvidia", 31.48), ("Micron", 19.04), ("Intel", 16.3), ("Nasdaq 100", 6.9), ("Nasdaq", 6.51),
            ("Kospi (24/11)", 6.32), ("S&P 500", 4.73), ("Dow Jones", 3.01)]

TAB = tabelle_da_dati("dati.json")
C = {
    "data": OGGI,
    "temi": ["Chip", "Fed", "Tassi", "Petrolio", "Materie prime", "Europa"],
    "glossario": ["PMI", "PCE", "VIX", "CME FedWatch", "core", "WTI"],
    "meccanismi": ["M01", "M10", "M27", "M26", "M20", "M23", "M16", "M17", "M11"],
    "ticker": ticker_da_dati("dati.json"),

    "top": {
        "tema": "Chip",
        "titolo": "Huang torna alla guida di Nvidia e Wall Street rimbalza",
        "dek": "Il consiglio di Nvidia ha reintegrato Jensen Huang, dimessosi il 12 novembre, e il titolo "
               "guadagna oltre il 31%. L'S&amp;P 500 sale del 4,7%, il rialzo più forte da almeno un anno, e il Nasdaq del "
               "6,5%. Stamattina Seul chiude a +6,3% e ieri l'Euro Stoxx 50 aveva già guadagnato il 2,2%. [[chip]]",
        "freccia": "",
    },
    "quadro": "Una giornata di sollievo, non un cambio di scenario. Le azioni salgono ovunque (azionario mondiale +4,5%, "
              "piccole società del Russell 2000 +3,4%) e il VIX, l'indice della paura, crolla del 25,8% da 35,89 a 26,62. "
              "Ci leggiamo anche il rimbalzo dell'oro (+3,9%): finiscono le vendite per far cassa. Ma il 10 anni resta al "
              "4,92% e il rialzo Fed di dicembre è ancora quasi scontato: meno rischio, non meno tassi.",
    "in30": [
        "Europa: la tecnologia trascina le borse, ma Germania e Francia crescono a ritmi opposti. [[europa]]",
        "Petrolio: per noi il greggio scende perché il mercato guarda al surplus, non alla guerra. [[petrolio]]",
        "Mercoledì i prezzi PCE: il test che può confermare o far saltare il rialzo Fed di dicembre. [[agenda]]",
    ],
    "in30_temi": ["Europa", "Petrolio", "Macro"],
    "stamattina": [
        "Kospi alla chiusura di Seul: 5.006,03 (+6,32%)",
        "Nikkei 225 alle 09:03: 58.644,63 (+3,9%)",
        "Hang Seng alle 09:03: 22.194,50 (-0,8%)",
    ],
    "notizie": [
        {"tag": "Tecnologia", "titolo": "CrowdStrike compra Zscaler per 44 miliardi di dollari, tutto in azioni",
         "testo": "L'accordo è stato annunciato ieri. In Borsa Zscaler sale del 18% e CrowdStrike perde circa il 9%."},
        {"tag": "Tecnologia", "titolo": "Micron firma nuovi accordi pluriennali di fornitura di memorie",
         "testo": "Le intese con i clienti fanno salire il titolo del 19% e arrivano nella giornata in cui il mercato "
                  "torna a comprare i chip.", "rimando": "chip"},
        {"tag": "Europa", "titolo": "ABB compra il tedesco Ziehl-Abegg e sale del 4,6%",
         "testo": "L'acquisizione dei ventilatori e motori per il condizionamento industriale vale 2,65 miliardi di "
                  "dollari e fa dell'azienda svizzera la migliore di Zurigo."},
        {"tag": "Macro", "titolo": "La Francia si contrae di più mentre la Germania accelera",
         "testo": "L'indice dell'attività delle imprese resta a 51,7 per l'area euro, sotto il 51,9 atteso: la media "
                  "nasconde due paesi che vanno in direzioni opposte.", "rimando": "europa"},
        {"tag": "Italia", "titolo": "Intesa Sanpaolo e UniCredit guidano Milano malgrado lo stacco di undici dividendi",
         "testo": "Il FTSE MIB chiude a +0,65% dopo aver perso quasi l'1% in mattinata, con Intesa Sanpaolo a +2,8% e UniCredit a +2%.", "rimando": "europa"},
        {"tag": "Fed", "titolo": "Gli operatori scommettono ancora sul rialzo Fed di dicembre",
         "testo": "Secondo il CME FedWatch, che ricava la probabilità dai future sui tassi, un rialzo a dicembre vale circa il 94%: il sollievo in borsa non l'ha toccata.", "rimando": "treasury"},
    ],
    "mercati_titolo": "Numeri, temi aperti e calendario",
    "cruscotto": TAB["cruscotto"], "cruscotto_nota": TAB["cruscotto_nota"],
    "cross_data": TAB["cross_data"], "cross": TAB["cross"], "cross_nota": TAB["cross_nota"],
    "termometri": [
        ("Fed e tassi", "Rialzo di dicembre scontato", "Rimbalzo senza effetti sul 10 anni", "fermo: Rendimento del 10 anni", "PCE di mercoledì"),
        ("AI e chip", "Rimbalzo dopo il reintegro di Huang", "Nvidia a +31% in un giorno", "su: Titoli dei chip", "Apertura del Nasdaq"),
        ("Oro", "Rimbalzo dal minimo di 14 mesi", "Risale con le borse", "su: Oro future", "Rendimenti dei Treasury"),
        ("Petrolio", "Brent sotto 90 $", "Colloqui con l'Iran e surplus", "giu: Brent e WTI", "Hormuz e scorte"),
    ],
    "fermi": "Fondo di stabilizzazione del governo di Seul (nessuna novità verificata dal 23/11).",
    "lettura": "Il Russell 2000, l'indice delle società più piccole, sale meno dell'S&amp;P 500: di solito chi ha più "
               "debiti recupera più piano quando i tassi restano alti. E stamattina l'Hang Seng cede mentre Tokyo e Seul "
               "volano: a Hong Kong i produttori di chip tendono a pesare meno nell'indice.",
    "ieri": [
        ("Lun 23, 10:00", "PMI flash area euro (novembre)", "Composito 51,7 (atteso 51,9); servizi 51,2 (51,8)", "-", "[[europa]]"),
    ],
    "agenda": [
        ("Mar 24, 16:00", "Fiducia dei consumatori Conference Board (novembre)", "Prima 91,7",
         "Quanto pesano prezzi e borsa sulle famiglie",
         "<b>Sopra:</b> consumi più saldi, un po' di sostegno ai rendimenti.<br/><b>Sotto:</b> più spazio per chi scommette su una Fed meno dura."),
        ("<b>Mer 25, 14:30</b>", "<b>Prezzi PCE (ottobre)</b>", "<b>Senza energia e alimentari: +0,3% sul mese, +3,2% su un anno (prima +3,1%)</b>",
         "<b>Evento n.1:</b> la misura di inflazione che la Fed segue di più, prima della riunione di dicembre",
         "<b>Sopra:</b> sale la probabilità del rialzo, salgono dollaro e rendimenti.<br/><b>Sotto:</b> il rialzo perde forza e le borse respirano."),
        ("Mer 25, 14:30", "PIL USA del terzo trimestre (seconda stima)", "+3,4% annualizzato",
         "Tenuta dell'economia con tassi alti",
         "<b>Sopra:</b> l'economia regge e lascia spazio alla Fed.<br/><b>Sotto:</b> torna il timore di una frenata."),
        ("Ven 27, 19:00", "Chiusura anticipata di Wall Street", "Borse USA chiuse giovedì per il Ringraziamento",
         "Pochi scambi: un movimento si amplifica facilmente",
         "<b>Sopra e sotto:</b> con volumi bassi un dato o una notizia muovono i prezzi più del solito."),
    ],
    "moduli": [
        {"chiave": "chip", "tema": "Chip e Asia", "breve": "il rimbalzo dopo Huang",
         "titolo": "Il rimbalzo di Nvidia mostra che le vendite erano di fiducia, non di conti",
         "misura": "doppio",
         "grafico": {"tipo": "barre", "file": "c_rimbalzo.png", "dati": RIMBALZO, "ordina": False, "dec": 1, "unita": "%",
                     "soggetto": "rimbalzo", "ruolo": "quanto",
                     "titolo": "Il rialzo è più forte dove pesano di più i chip",
                     "sottotitolo": "variazioni % del 23/11 (Kospi: 24/11)"},
         "grafico2": {"tipo": "linee", "file": "c_sp500.png", "x": [d(x) for x, _ in SP], "soggetto": "calo", "ruolo": "storia",
                      "serie": [("S&P 500", [v for _, v in SP], "#111111")],
                      "titolo": "In sei sedute l'S&P 500 aveva perso quasi il 9% e ne ha ripreso metà",
                      "sottotitolo": "S&P 500, chiusure (punti)", "soglie": [(7000, "7.000")], "eventi": [(d("11-12"), "dimissioni di Huang")],
                      "note": [(d("11-12"), 7592.40, "12/11"), (d("11-20"), 6910.39, "20/11"), (d("11-23"), 7237.17, "23/11")]},
         "numero": "25%: il calo circa di Nvidia tra le dimissioni di Huang del 12 novembre e venerdì, secondo Aju Press.",
         "perche": "A nostro avviso la vendita era una perdita di fiducia in Nvidia e non di utili, e il rimbalzo di ieri lo conferma. Quando il consiglio ha riportato Huang, un solo "
                   "comunicato ha ricomprato gran parte di un calo durato undici giorni.",
         "quindi": "Il primo test è l'apertura di Wall Street oggi alle 15:30: se i chip americani rivendono, il rimbalzo "
                   "di ieri è stato uno sfogo di un giorno.",
         "testo": ["Se i conti di Nvidia non sono cambiati in undici giorni, perché il titolo ha perso circa un quarto e "
                   "ieri ne ha ripreso gran parte in una seduta? Perché a muovere il prezzo non erano i conti ma la "
                   "persona che guida l'azienda. Chi compra Nvidia compra la storia dell'intelligenza artificiale, e quella "
                   "storia aveva un protagonista. Dopo le dimissioni di Huang sono arrivate notizie secondo cui sarebbe stato nel mirino di un'operazione di intelligence straniera. Il mercato ha cominciato a chiedersi chi avrebbe deciso e se l'azienda poteva ancora vendere le sue macchine.",
                   "Un solo titolo può muovere un intero indice quando pesa tanto. Gli indici contano ogni società per il "
                   "suo valore in borsa, e quando le più grandi di un settore cadono insieme l'indice perde molto più "
                   "della media dei titoli. Per questo il Nasdaq ha perso il 10% in una settimana e ne ha guadagnato "
                   "il 6,5% in un giorno.",
                   "Il rimbalzo non ha riguardato solo Nvidia. Intel sale del 16,3% e il Nasdaq 100 del 6,9%, il maggior rialzo giornaliero dall'aprile 2025. Sono titoli che di solito dipendono dalla stessa "
                   "domanda di chip per i centri di calcolo: quando il timore passa, i compratori tornano su tutta la "
                   "filiera.",
                   "Stamattina l'Asia ha seguito Wall Street. Il Kospi di Seul chiude a 5.006,03. In mattinata la borsa coreana ha sospeso per cinque minuti gli ordini d'acquisto automatici, una misura che scatta quando i future "
                   "salgono troppo in fretta. Seul tende a salire più di Tokyo quando i chip rimbalzano, perché due soli produttori, Samsung Electronics e "
                   "SK hynix, valgono circa metà dell'indice.",
                   "Non tutti sono convinti. A Seul i piccoli risparmiatori vendono per circa 2.000 miliardi di won mentre "
                   "stranieri e istituzioni comprano, e un professore giudica il rimbalzo temporaneo. Anche per Nvidia il rischio resta aperto."],
         "guardare": "Contano i chip americani all'apertura di oggi: un nuovo calo farebbe del rimbalzo uno sfogo, una seduta "
                     "in rialzo darebbe ragione a chi compra.",
         "fonte": "Fonti: comunicato Nvidia (SEC), Aju Press, JKN, Korea Herald, City AM."},
        {"chiave": "treasury", "tema": "Tassi USA", "breve": "10 anni fermo malgrado il rimbalzo",
         "titolo": "Le borse rimbalzano ma il 10 anni resta fermo: pesa la Fed",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_ust.png", "x": [d(r[0]) for r in UST], "soggetto": "10 anni", "ruolo": "storia",
                     "titolo": "In dieci giorni il 10 anni è sceso di oltre 20 punti base",
                     "sottotitolo": "Rendimenti dei Treasury, chiusure (%)",
                     "serie": [("10 anni", [r[2] for r in UST], "#F26B1D"), ("2 anni", [r[1] for r in UST], "#111111")]},
         "perche": "Meno paura dovrebbe far salire i rendimenti, perché si comprano meno titoli di Stato come rifugio. Ma "
                   "il petrolio in calo e le attese di inflazione più basse spingono nel verso opposto, e a nostro avviso "
                   "le due forze si annullano.",
         "numero": "29 pb: di quanto il 10 anni, al 4,92%, rende più del 2 anni, al 4,63%. A nostro avviso non è il "
                   "segno di un mercato che scommette su una recessione vicina.",
         "quindi": "Mercoledì alle 14:30 escono i prezzi PCE: un dato di fondo, senza energia e alimentari, sopra il +0,3% atteso sul mese toglierebbe "
                   "ogni dubbio al rialzo di dicembre.",
         "testo": ["Se la paura cala, perché il 10 anni non sale? Perché oggi due cose lo spingono in direzioni opposte. "
                   "Chi ha paura compra titoli di Stato americani per mettere i soldi al sicuro: il prezzo sale e il "
                   "rendimento, che si muove al contrario, scende. Quando la paura passa quella domanda si ferma e il "
                   "rendimento tende a risalire. Ma con la paura è calato anche il petrolio. Un greggio più basso di solito abbassa l'inflazione che gli investitori si aspettano, cioè il rendimento che pretendono per "
                   "prestare a dieci anni.",
                   "Lo scenario Fed non è cambiato. Secondo il CME FedWatch i future danno circa il 94% di probabilità a un rialzo di 25 punti base a dicembre. Secondo Kitco una parte degli operatori l'ha ridotta dopo indicatori più deboli. Il 2 anni, che segue la banca centrale più da vicino, resta a 4,63% come venerdì. "
                   "Per questo il dato di mercoledì conta più del rimbalzo.",
                   "Il petrolio spiega anche la discesa dei dieci giorni scorsi. Dal 13 novembre, quando il 10 anni era al 5,15%, il Brent è passato da 95,84 a meno di 90 $. Con lui, secondo Kitco, sono scese le attese di inflazione. Un rendimento che si sposta con il barile dice che il mercato lo legge come un "
                   "termometro dei prezzi futuri."],
         "fonte": "Fonti: Kitco, Fox Business, Milano Finanza, CME; curva par del Tesoro USA via FMP."},
        {"chiave": "petrolio", "tema": "Petrolio", "breve": "surplus più forte della guerra",
         "titolo": "Il petrolio scende guardando al surplus, non alla guerra",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_brent.png", "x": [d(x) for x, _ in BRENT], "soggetto": "petrolio", "ruolo": "storia",
                     "serie": [("Brent", [v for _, v in BRENT], "#F26B1D")],
                     "titolo": "In un mese il Brent è sceso da oltre 115 a meno di 90 dollari",
                     "sottotitolo": "Brent future, chiusure ($)", "soglie": [(100, "100 $")],
                     "note": [(d("10-26"), 115.81, "26/10"), (d("11-23"), 89.37, "23/11")]},
         "perche": "Per Bloomberg gli investitori chiudono le coperture contro un'escalation, perché Trump ha lasciato più "
                   "tempo ai colloqui con l'Iran. Dietro c'è un mercato che, secondo l'Aie, avrà un surplus di circa 2 "
                   "milioni di barili al giorno in questo trimestre.",
         "quindi": "Un nuovo attacco alle petroliere nello Stretto di Hormuz, o il fallimento dei colloqui, è ciò che può "
                   "riportare il Brent sopra i 100 $.",
         "numero": "-23%: il calo del Brent dal 26 ottobre, da 115,81 a 89,37 $.",
         "testo": ["Le petroliere continuano a essere colpite e il greggio scende lo stesso. Il prezzo di un barile "
                   "dipende da quanti ne arrivano e da quanti ne servono, non dal numero delle notizie di guerra. I flussi dal Golfo, scrive Bloomberg, sembrano continuare. Le previsioni dicono che ne arriveranno più del necessario: Bernstein vede un surplus per tre anni e Goldman Sachs segnala il rischio di troppa offerta l'anno prossimo.",
                   "Per l'inflazione la differenza conta. Un petrolio che sale per timore sulle forniture è di solito un "
                   "costo secco per Europa e Giappone, che lo importano. Uno che scende per l'abbondanza alleggerisce i costi di trasporti e carburanti. Secondo Saxo Bank il calo del diesel può attenuare i timori sui prezzi e su ulteriori rialzi dei tassi."],
         "fonte": "Fonti: Bloomberg (Rigzone), Kitco; chiusure del Brent future."},
        {"chiave": "oro", "tema": "Materie prime", "breve": "l'oro risale con le borse",
         "titolo": "L'oro è sceso e risalito con le borse, non contro di loro",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_oro.png", "x": [d(x) for x, _ in ORO], "soggetto": "oro", "ruolo": "storia",
                     "serie": [("Oro future", [v for _, v in ORO], "#F26B1D")],
                     "titolo": "L'oro ha perso quasi un decimo in una settimana e ne ha recuperato più di un terzo",
                     "sottotitolo": "Oro future, chiusure ($ l'oncia)", "soglie": [(3500, "3.500 $")],
                     "note": [(d("11-09"), 4114.5, "9/11"), (d("11-20"), 3515.4, "20/11")]},
         "perche": "Secondo Kitco nel ribasso di venerdì l'oro ha avuto spinte contrastanti: la domanda da rifugio da un lato, "
                   "le vendite per raccogliere liquidità e coprire i margini dall'altro. A nostro avviso hanno prevalso le "
                   "seconde, e il rimbalzo di ieri insieme alle azioni lo suggerisce.",
         "quindi": "Una ricaduta sotto i 3.500 $, il minimo di venerdì, segnerebbe il fallimento del rimbalzo.",
         "numero": "-9,5%: il calo dell'oro future dal 13 al 20 novembre, da 3.886,30 a 3.515,40 $.",
         "testo": ["L'oro, il rifugio per eccellenza, è caduto proprio nella settimana della paura. In una giornata di panico chi ha perdite su azioni o su titoli comprati a debito deve rimettere soldi sul conto. Vende allora ciò che si vende bene, oro compreso. Sono vendite forzate. Non dicono nulla sul valore dell'oro.",
                   "Quando le azioni risalgono, quella pressione si allenta e l'oro recupera, mentre il VIX, l'indice che misura la paura a Wall Street, scende da 35,89 a 26,62. Natixis avverte che il "
                   "rimbalzo può durare poco e vede il rischio di un ritorno verso i 3.340 $. Pesano anche i "
                   "rendimenti, ancora vicini al 5%: più sono alti, più costa tenere un oro che non rende."],
         "fonte": "Fonti: Kitco, Nation Thailand; chiusure dell'oro future."},
        {"chiave": "europa", "tema": "Europa e Italia", "breve": "rimbalzo dei chip, Francia in frenata",
         "titolo": "L'Europa sale con i chip americani, mentre Germania e Francia divergono",
         "misura": "mezzo",
         "righe": [["Clima d'affari area euro, novembre", "Dato", "Atteso"],
                   ["Composito", "51,7", "51,9"],
                   ["Servizi", "51,2", "51,8"],
                   ["Manifattura", "52,9", "52,8"]],
         "larghezze": [60, 30, 30], "ruolo_righe": "perche",
         "perche": "Per l'agenzia dpa-AFX la tecnologia è di gran lunga il settore migliore e porta l'Euro Stoxx 50 a +2,2%, con ASML a +8,9% e Infineon a "
                   "+6,6%. Per Salah-Eddine Bouhmidi di IG Markets la fiducia torna ben oltre Nvidia e il settore "
                   "dell'intelligenza artificiale.",
         "quindi": "Oggi parte il periodo di adesione all'offerta di Intesa Sanpaolo su Mps: per le banche che ieri hanno "
                   "guidato Milano è il primo test.",
         "testo": ["I chip sono americani, eppure l'Europa sale. L'Euro Stoxx 50 ha dentro ASML e Infineon, che "
                   "vendono macchine e componenti agli stessi centri di calcolo. Quando Wall Street compra i chip, di "
                   "riflesso compra chi li rende possibili. Per l'economia europea nel suo insieme conta però altro.",
                   "Lo mostrano i PMI, gli indici mensili sul clima d'affari delle imprese: l'area euro cresce come prima, ma la media nasconde due economie. Per Chris Williamson di S&amp;P Global la Germania accelera al ritmo più rapido in quattro anni e mezzo. La Francia si contrae più che negli ultimi sei mesi e il divario tra i due è il più ampio in sei anni.",
                   "A Milano lo stacco dei dividendi di undici titoli, secondo ANSA, pesava circa l'1,4% sull'indice, e in mattinata il "
                   "FTSE MIB perdeva quasi l'1%. A nostro avviso è stata l'apertura di Wall Street nel pomeriggio a ribaltare la seduta, "
                   "con le banche in testa: Intesa Sanpaolo +2,8%, Banco BPM +2,5% e UniCredit +2%."],
         "fonte": "Fonti: dpa-AFX, Reuters, investingLive, ANSA, Milano Finanza, Teleborsa."},
    ],
    "scommessa": {"tesi": "Con noi: il rimbalzo c'è e va nella nostra direzione su borse, petrolio e oro. Contro: l'euro, che "
                          "si indebolisce invece di recuperare. Da qui a venerdì: il PCE di mercoledì decide se il rimbalzo regge.",
                  "lunedi": False, "venerdi": False, "settimana_prec": None},
    "parole": [("Vendite forzate", "Vendite fatte per rimettere soldi sul conto e coprire perdite altrove, chi vende lo fa per "
                                   "necessità, senza un giudizio sul titolo."),
               ("Capitalizzazione", "Il valore di una società in borsa: più è grande, più la società pesa negli indici."),
               ("Inflazione attesa", "Quella che gli investitori si aspettano nei prossimi anni: pesa sul rendimento che "
                                     "chiedono per prestare."),
               ("Surplus di petrolio", "Più barili offerti di quanti ne servano: spinge i prezzi in giù."),
               ("Sidecar", "Freno automatico della borsa coreana agli acquisti dei programmi quando i future salgono troppo in fretta."),
               ("Stacco del dividendo", "Il giorno in cui il titolo scende dell'importo della cedola pagata: pesa "
                                        "sull'indice se riguarda molte società.")],
    "fonti": [
        ("Dati di mercato", "Financial Modeling Prep (indici USA e Asia, VIX, Brent e oro future, curva par del Tesoro USA); "
                            "Alpha Vantage (EUR/USD, ACWI); EODHD e dpa-AFX (Euro Stoxx 50); ANSA e Milano Finanza (FTSE MIB, spread); "
                            "JKN e Aju Press (Kospi)."),
        ("Prima pagina e mercati", "Fox Business, ABC News, dpa-AFX, ANSA, Milano Finanza, Kitco, "
                                   "Bloomberg (Rigzone), Reuters (RTÉ), investingLive, comunicato CrowdStrike e Zscaler (SEC)."),
        ("Calendario e agenda", "FinancialJuice, Investrade, HyperStocks, LiteFinance, Teleborsa."),
        ("Approfondimenti", "Chip: comunicato Nvidia (SEC), Aju Press, JKN, City AM. Treasury: Kitco, "
                            "Fox Business, curva par del Tesoro via FMP. Petrolio: Bloomberg (Rigzone), Kitco. Oro: Kitco, "
                            "Nation Thailand. Europa: dpa-AFX, Reuters, ANSA, Milano Finanza."),
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
