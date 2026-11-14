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
from numeri import ticker_da_dati, fmt, var  # noqa: E402

LAVORO = sys.argv[1] if len(sys.argv) > 1 else "."
USCITA = sys.argv[2] if len(sys.argv) > 2 else None
os.chdir(LAVORO)   # grafici e c_forecast.png stanno qui

# =============================== CONTENUTI DEL GIORNO ===============================
OGGI = dt.date(2026, 11, 16)
NOTA_DATI = "Chiusure al 13 novembre; le borse asiatiche di lunedì non hanno ancora aperto"
REG = "2026-11-16-settimana.json"          # registro della scommessa (redazione/pronostici/)

DJ = json.load(open("dati.json", encoding="utf-8"))["serie"]
YTD = {"S&P 500": 6845.49, "Nasdaq": 23241.99, "Russell 2000": 2481.91, "Euro Stoxx 50": 5796.22, "Nikkei 225": 50339.48,
       "Hang Seng": 25630.55, "FTSE MIB": 44944.0}


def riga(nome, serie, dec=2, ytd=True, sett=True, unita=""):
    s = DJ[serie]["ultimi"]
    v0, v1 = s[0][1], s[1][1]
    sw = next((x[1] for x in s if x[0] == "2026-11-06"), None)
    t = DJ[serie].get("tipo_var") or ("pb" if DJ[serie]["mercato"] == "UST" else "pct")
    return [nome, fmt(v0, dec) + unita, "13/11", var(v0, v1, t, 1), var(v0, sw, t, 1) if (sw and sett) else "n.d.",
            var(v0, YTD[serie], "pct", 1) if (ytd and serie in YTD) else "n.d."]


# ============================ DATI DEI GRAFICI (verificati) ============================
UST_6 = {"1M": 4.02, "3M": 4.19, "6M": 4.23, "1A": 4.33, "2A": 4.51, "3A": 4.59, "5A": 4.64, "7A": 4.74, "10A": 4.86,
         "20A": 5.29, "30A": 5.26}
UST_13 = {"1M": 4.10, "3M": 4.32, "6M": 4.42, "1A": 4.65, "2A": 4.88, "3A": 4.92, "5A": 4.98, "7A": 5.05, "10A": 5.15,
          "20A": 5.52, "30A": 5.47}
UST_MESE = [  # data, 2 anni, 10 anni (curva par del Tesoro, FMP); l'11/11 i Treasury erano chiusi (Veterans Day)
    ("10-13", 4.79, 5.21), ("10-14", 4.82, 5.19), ("10-15", 4.77, 5.10), ("10-16", 4.74, 5.09), ("10-19", 4.77, 5.15),
    ("10-20", 4.79, 5.12), ("10-21", 4.81, 5.13), ("10-22", 4.65, 4.96), ("10-23", 4.69, 5.00), ("10-26", 4.68, 5.00),
    ("10-27", 4.70, 4.99), ("10-28", 4.67, 5.05), ("10-29", 4.61, 4.98), ("10-30", 4.56, 4.94), ("11-02", 4.59, 4.91),
    ("11-03", 4.61, 4.95), ("11-04", 4.58, 4.90), ("11-05", 4.46, 4.84), ("11-06", 4.51, 4.86), ("11-09", 4.56, 4.88),
    ("11-10", 4.73, 4.98), ("11-12", 4.86, 5.10), ("11-13", 4.88, 5.15)]
NASDAQ = [("11-02", 25164.32), ("11-03", 25372.01), ("11-04", 25736.51), ("11-05", 24315.00), ("11-06", 24579.42),
          ("11-09", 25253.14), ("11-10", 25065.87), ("11-11", 25466.19), ("11-12", 25366.09), ("11-13", 25136.27)]
BRENT = [("10-12", 106.65), ("10-13", 105.69), ("10-14", 106.06), ("10-15", 105.92), ("10-16", 109.86), ("10-19", 109.55),
         ("10-20", 108.79), ("10-21", 108.82), ("10-22", 113.17), ("10-23", 116.72), ("10-26", 115.81), ("10-27", 113.88),
         ("10-28", 115.32), ("10-29", 110.80), ("10-30", 113.43), ("11-02", 104.77), ("11-03", 103.60), ("11-04", 94.62),
         ("11-05", 98.29), ("11-06", 98.32), ("11-09", 92.57), ("11-10", 91.49), ("11-11", 92.76), ("11-12", 95.82),
         ("11-13", 95.84)]
d = lambda s: dt.date(2026, int(s[:2]), int(s[3:]))   # "MM-GG" -> data

C = {
    "data": OGGI,
    "temi": ["Chip", "Fed", "Tassi", "Valute", "Petrolio", "Europa"],
    "glossario": ["CPI", "PPI", "pb", "CME FedWatch", "DXY", "VIX", "WTI"],
    "meccanismi": ["M16", "M26", "M05", "M06", "M08", "M10", "M11"],

    "ticker": ticker_da_dati("dati.json"),

    "top": {
        "tema": "Chip",
        "titolo": "I chip crollano, ma Wall Street chiude la settimana in rialzo",
        "dek": "Venerdì l'indice dei semiconduttori di Filadelfia perde il 3,4%, AMD l'8,8% e Nvidia un altro 2%. Il resto "
               "della borsa tiene: l'S&amp;P 500 sale del 2,5% sulla settimana e l'Euro Stoxx 50 del 3,5%, la migliore da aprile. "
               "A pagare sono pochi grandi titoli, non tutto il mercato. Intanto i tassi corrono più delle azioni, e la "
               "settimana che comincia ha il banco di prova nei conti di Nvidia. [[chip]]",
        "freccia": "Nvidia pubblica i conti martedì dopo la chiusura, senza più Huang amministratore delegato (Reuters).",
    },
    "quadro": "Per noi borse e tassi leggono l'inflazione in modo opposto. Fuori dai chip le azioni guardano agli utili e "
              "salgono. I Treasury scommettono invece su una Fed che alza i tassi a dicembre, e così il 2 anni sale a 4,88% "
              "e il dollaro tocca il massimo da aprile 2025. Il petrolio scende ancora, mentre l'oro perde oltre il 4% sulla "
              "settimana, come spesso accade quando dollaro e rendimenti salgono.",
    "in30": [
        "Il mercato dei tassi dà per molto probabile un rialzo della Fed a dicembre, e il breve paga il conto. [[treasury]]",
        "Il petrolio scende ancora: il mercato guarda ai colloqui con l'Iran più che agli attacchi. [[petrolio]]",
        "L'Europa chiude la migliore settimana da aprile, aiutata dai pochi chip in portafoglio. [[europa]]",
    ],
    "in30_temi": ["Fed", "Petrolio", "Europa"],
    "stamattina_titolo": "Cosa guardare all'apertura",
    "stamattina": [
        "Alle 11:00 a Milano parla Michael Barr, governatore della Fed, di intelligenza artificiale e stabilità finanziaria",
        "Tokyo, Seul e Hong Kong aprono dopo il calo dei chip americani: il primo test è il Kospi, che venerdì ha invertito la rotta dopo l'apertura in rialzo",
        "S&amp;P 500: la soglia è il minimo di venerdì, 7.499,40 punti",
        "Nasdaq: venerdì ha toccato 24.872,41 prima di risalire",
    ],
    "notizie": [
        {"tag": "Inflazione", "titolo": "I prezzi alla produzione USA salgono del 6,5% in un anno",
         "testo": "Ottobre porta +0,3% sul mese; senza cibo, energia e servizi commerciali il rialzo è dello 0,5%.",
         "rimando": "treasury"},
        {"tag": "Asia", "titolo": "Gli stranieri vendono azioni coreane e il Kospi inverte la rotta",
         "testo": "L'indice aveva aperto in rialzo del 2,05% e chiude in calo: gli investitori esteri hanno venduto 550,5 "
                  "miliardi di won netti (Korea Herald)."},
        {"tag": "Macro", "titolo": "La FAA ferma tutti i voli in partenza dagli Usa",
         "testo": "Il blocco nazionale arriva nel finale di seduta, dopo problemi di comunicazione con il controllo del "
                  "traffico aereo, e le compagnie aeree perdono l'1,4% (Reuters)."},
        {"tag": "Trimestrali", "titolo": "I conti dividono l'Europa: Aviva sale, Generali, Richemont e AMS-Osram scendono",
         "testo": "Quattro società, quattro esiti diversi nella giornata dei conti europei.", "rimando": "europa"},
        {"tag": "Italia", "titolo": "Fincantieri scivola dopo i conti, Milano chiude in lieve rialzo",
         "testo": "Il Ftse Mib sale dello 0,10% e lo spread tra Btp e Bund resta a 104 punti base (ANSA). Fincantieri cede il 4,2%, "
                  "secondo SoldiOnline.", "rimando": "europa"},
        {"tag": "Tecnologia", "titolo": "Il consiglio di Nvidia sonda il capo di Arm per la successione a Huang",
         "testo": "Lo scrive il Financial Times, riferisce Reuters: Rene Haas, amministratore delegato di Arm, è stato "
                  "contattato dal consiglio.", "rimando": "chip"},
    ],

    "mercati_titolo": "Numeri, temi aperti e calendario",
    "cruscotto": [
        ("Mondo e Stati Uniti", [riga("MSCI ACWI (ETF, $)", "ACWI", 2, ytd=False),
                                 riga("S&amp;P 500", "S&P 500"), riga("Nasdaq Comp.", "Nasdaq"),
                                 riga("Russell 2000", "Russell 2000")]),
        ("Europa", [riga("Euro Stoxx 50", "Euro Stoxx 50"), riga("FTSE MIB", "FTSE MIB", 0)]),
        ("Asia (chiusure del 13/11)", [riga("Nikkei 225", "Nikkei 225"), riga("Hang Seng", "Hang Seng"),
                                       riga("Kospi", "Kospi", sett=False, ytd=False)]),
    ],
    "cruscotto_nota": "1 g = chiusura su chiusura; 1 sett. = su venerdì 6/11; da inizio anno = su chiusura 2025. "
                      "Kospi: variazione del giorno dalla fonte (Korea Herald).",
    "cross_data": "Livello 13/11",
    "cross": [
        ("Tassi", [["Treasury 2 anni", "4,88%", "+2 pb", "+37 pb", "+9 pb", "Sale con le attese sulla Fed [[treasury]]"],
                   ["Treasury 10 anni", "5,15%", "+5 pb", "+29 pb", "-6 pb", "-"],
                   ["Spread Italia", "104 pb", "n.d.", "n.d.", "n.d.", "Chiusura del 13/11 (ANSA)"]]),
        ("Cambi", [["EUR/USD", "1,1021", "-0,3%", "-1,1%", "-1,6%", "-"]]),
        ("Materie prime", [["Brent future", "95,84 $", "0,0%", "-2,5%", "-9,3%", "-"],
                           ["Oro (future, $/oncia)", "3.886", "0,0%", "-4,6%", "-7,0%", "-"]]),
        ("Volatilità", [["VIX (volatilità attesa)", "19,30", "+0,60", "-6,34", "+4,03", "-"]]),
    ],
    "cross_nota": "1 mese = sul 13/10. VIX = volatilità attesa sull'S&amp;P 500.",
    "termometri": [
        ("Fed e tassi", "Riunione 8-9 dicembre", "Rialzo di dicembre molto probabile", "su: Probabilità di un rialzo da mezzo punto",
         "Verbali Fed di mercoledì"),
        ("AI e chip", "Conti Nvidia martedì", "Chip in calo, Nvidia senza Huang ceo", "giu: Titoli dei chip", "Nvidia dopo i conti"),
        ("Dollaro", "Indice a 103,40", "Massimo da aprile 2025", "su: Dollaro contro euro", "Treasury a 2 anni"),
        ("Petrolio e Iran", "Brent sotto 100 $", "Colloqui in corso", "giu: Brent nella settimana", "Notizie dai negoziati"),
    ],
    "fermi": "Yen e interventi di Tokyo (ultima notizia verificata il 13/11), Banco BPM e Crédit Agricole (12/11).",
    "lettura": "Due cose che le tabelle dicono e la prima pagina no. Il Russell 2000, l'indice delle società più piccole, "
               "perde meno del Nasdaq: di solito chi non vive di tecnologia soffre meno quando i chip vendono. E il VIX (volatilità attesa) "
               "chiude la settimana sotto i livelli del 6 novembre pur con un venerdì nervoso: la paura "
               "resta lontana dai massimi.",

    "ieri": [
        ("Mar 10, 14:30", "Prezzi al consumo USA (ottobre)", "+0,4% sul mese (atteso +0,3%); senza energia e alimentari "
                                                              "+0,3% (+0,2%)", "+", "[[treasury]]"),
        ("Ven 13, 14:30", "Prezzi alla produzione USA (ottobre)", "+0,3% sul mese; +6,5% su un anno", "", "[[treasury]]"),
    ],
    "agenda": [
        ("Lun 16, 18:00", "Discorso di Warsh, presidente della Fed", "Nessun numero atteso", "Primo intervento dopo i prezzi caldi",
         "<b>Più duro:</b> di solito salgono i rendimenti a breve.<br/><b>Più cauto:</b> di solito frenano dollaro e tassi."),
        ("<b>Mar 17, 14:30</b>", "<b>Vendite al dettaglio USA (ottobre)</b>", "<b>consenso non verificato; prima +0,8%</b>",
         "<b>Evento n.1:</b> i consumi dopo i prezzi caldi",
         "<b>Sopra:</b> di solito salgono dollaro e rendimenti a breve: consumi forti lasciano spazio alla Fed."
         "<br/><b>Sotto:</b> il rialzo di dicembre perde un po' di forza."),
        ("Mar 17, 15:10", "Discorso di Waller (Fed) sui pagamenti", "Nessun numero atteso", "Ha parlato di rialzo da mezzo punto",
         "<b>Più duro:</b> di solito salgono i rendimenti a breve.<br/><b>Più cauto:</b> di solito frenano dollaro e tassi."),
        ("Mar 17, 23:00", "Conti trimestrali di Nvidia", "Consenso non verificato", "Primo esame dei chip senza Huang",
         "<b>Sopra le attese:</b> di solito i chip rimbalzano.<br/><b>Sotto:</b> la vendita di venerdì può estendersi."),
        ("Mer 18, 20:00", "Verbali della riunione Fed del 27-28 ottobre", "Nessun numero atteso", "Quanti vogliono rialzi più forti",
         "<b>Toni duri:</b> di solito salgono i rendimenti.<br/><b>Toni cauti:</b> il rialzo di dicembre appare meno certo."),
    ],
    "moduli": [
        {"chiave": "chip", "tema": "Chip", "breve": "chip in calo, borse in rialzo",
         "titolo": "I chip pagano il conto, ma la borsa non crolla con loro",
         "misura": "doppio",
         "grafico": {"tipo": "barre", "file": "c_settori_nyse.png",
                     "dati": [("Tecnologia", -2.1), ("Industriali", -1.3), ("Materiali di base", -0.8), ("Immobiliare", -0.6),
                              ("Energia", -0.1), ("Finanziari", 0.2), ("Servizi di pubblica utilità", 0.3), ("Consumi ciclici", 0.4),
                              ("Consumi difensivi", 0.4), ("Salute", 0.5), ("Comunicazione", 1.0)],
                     "titolo": "A cadere è la tecnologia: sei settori su undici salgono",
                     "sottotitolo": "variazione media dei titoli quotati al NYSE, 13/11 (%)", "unita": "%", "dec": 1, "ordina": False,
                     "soggetto": "borsa", "ruolo": "quanto"},
         "grafico2": {"tipo": "linee", "file": "c_nasdaq.png", "x": [d(x) for x, _ in NASDAQ],
                      "serie": [("Nasdaq", [v for _, v in NASDAQ], "#111111")], "soggetto": "chip", "ruolo": "storia",
                      "titolo": "Il Nasdaq ha riconquistato poco più della metà del crollo del 5 novembre",
                      "sottotitolo": "Nasdaq Composite, chiusure (punti)",
                      "note": [(d("11-04"), 25736.51, "4/11"), (d("11-05"), 24315.00, "5/11"), (d("11-13"), 25136.27, "13/11")]},
         "righe": [["Titolo", "Cinque giorni", "Un mese"],
                   ["Nvidia", "-5,9%", "-26,4%"],
                   ["AMD", "+12,8%", "-6,4%"]],
         "larghezze": [60, 60, 60], "ruolo_righe": "chi",
         "perche": "La vendita di venerdì nasce dall'incertezza su Nvidia, che pubblica i conti martedì dopo la chiusura e Huang si è dimesso da amministratore delegato (Reuters). Quando il leader vacilla, di solito vendono anche i titoli che gli ruotano intorno.",
         "numero": "+149%: il guadagno di AMD da inizio anno. Più un titolo è salito, più c'è da restituire quando il mercato si spaventa.",
         "quindi": "Martedì alle 23:00, ora di Roma, la conference call di Nvidia: se il titolo non risale dopo i conti, il problema va oltre Huang.",
         "testo": ["Un crollo dei chip di solito non trascina tutta la borsa. Il motivo è semplice: S&amp;P 500 e Nasdaq contano "
                   "ogni società in proporzione al suo valore, e i chip sono tra le più grandi. Di solito, se cadono loro l'indice scende, "
                   "ma le altre migliaia di titoli pesano meno. Venerdì è andata così: il Dow Jones, che ha pochi chip, ha chiuso "
                   "in rialzo dello 0,10%, e nel grafico la tecnologia è l'unico settore con una perdita larga.",
                   "AMD è il caso che spiega di più. In cinque giorni, nonostante venerdì, è salita del 12,8% e da inizio anno aveva più che "
                   "raddoppiato il valore; venerdì cede più di quattro volte Nvidia. Per noi qui ha pesato più il realizzo che "
                   "il contagio: chi aveva guadagnato tanto ha incassato, proprio quando il leader del settore perdeva "
                   "terreno.",
                   "Nvidia, intanto, vale circa un quarto in meno di un mese fa. Eppure la domanda non è sparita: la settimana "
                   "scorsa Cisco ha dichiarato ricavi in crescita del 24% e Applied Materials del 53%. Per noi il mercato ha "
                   "smesso di trattare i chip come un blocco unico: premia chi sale e punisce chi dipende da un solo nome."],
         "fonte": "Fonti: Reuters; variazioni dei titoli e settori NYSE da Financial Modeling Prep.",
         "guardare": "Se Nvidia batte le attese martedì e il titolo non risale, il problema è più largo di Huang; se risale, "
                     "il realizzo di venerdì si rivela una pausa."},
        {"chiave": "treasury", "tema": "Tassi USA", "breve": "i tassi corrono più delle azioni",
         "titolo": "La borsa sale, ma i Treasury scommettono su una Fed che alza i tassi",
         "misura": "doppio",
         "grafico": {"tipo": "barre", "file": "c_curva_sett.png",
                     "dati": [(k, round((UST_13[k] - UST_6[k]) * 100)) for k in UST_13],
                     "titolo": "Il maggior rialzo settimanale è a 2 anni e si smorza sulle lunghe",
                     "sottotitolo": "Curva Treasury, variazione dal 6 al 13/11 (pb)", "unita": " pb", "dec": 0, "ordina": False,
                     "soggetto": "Treasury", "ruolo": "quanto"},
         "grafico2": {"tipo": "linee", "file": "c_ust_mese.png", "x": [d(r[0]) for r in UST_MESE], "soggetto": "Treasury",
                      "titolo": "La distanza tra 10 e 2 anni resta vicina ai minimi dell'ultimo mese",
                      "sottotitolo": "10 anni meno 2 anni, chiusure (pb)", "ruolo": "storia",
                      "serie": [("10 anni meno 2 anni", [round((r[2] - r[1]) * 100) for r in UST_MESE], "#F26B1D")]},
         "numero": "11%: probabilità di un rialzo da mezzo punto a dicembre (CME FedWatch). Il rialzo da un quarto di punto è l'ipotesi di base.",
         "perche": "Il dato sui prezzi alla produzione, un po' sotto le attese sul mese, non ha cancellato la pressione dei prezzi al consumo (CPI) di martedì. Il mercato ha smesso di chiedersi se la Fed alzerà i tassi a dicembre e si chiede di quanto (Reuters). Waller non esclude mezzo punto, Logan ne vuole almeno due da un quarto (CNBC).",
         "quindi": "Mercoledì alle 20:00 i verbali della Fed dicono se il rialzo da mezzo punto ha sostenitori oltre Waller e Logan.",
         "testo": ["Per noi i rendimenti salgono mentre la borsa sale perché guardano a cose diverse. Chi presta al governo "
                   "americano per due anni si chiede dove saranno i tassi della Fed. Se si aspetta un rialzo a dicembre pretende "
                   "un interesse più alto, ed è questo il rendimento che sale. Chi presta per dieci anni guarda più lontano, "
                   "e per questo il suo rendimento si è mosso meno. Venerdì il 10 anni ha chiuso al 5,15% e il 2 anni al 4,88%. Giovedì il 10 anni era già salito di 12 punti base, a 5,10%, e il "
                   "2 anni di 13, a 4,86%: venerdì ha aggiunto il resto.",
                   "Un'inflazione più alta di solito spinge la banca centrale ad alzare i tassi, e tassi più alti fanno valere "
                   "meno gli utili che le imprese incasseranno tra molti anni. Ecco perché la salita dei rendimenti pesa "
                   "soprattutto sui titoli tecnologici. Lo stesso movimento rende più interessante il dollaro, perché chi "
                   "investe in titoli americani a breve guadagna di più, e l'indice del dollaro è ai massimi da aprile 2025 "
                   "(Reuters).",
                   "I numeri dicono da dove viene l'allarme. A ottobre i prezzi alla produzione crescono del 6,5% in un anno; "
                   "senza cibo, energia e servizi commerciali il rialzo mensile è dello 0,5%. Il dato di martedì 10 era già "
                   "sopra le attese: +0,4% sul mese contro lo 0,3% previsto.",
                   "Per noi borsa e tassi stanno scommettendo su due scenari diversi. La prima su un'economia che regge anche "
                   "con tassi più alti, i secondi su una Fed costretta a stringere. Uno dei due ha torto, e i dati della "
                   "settimana dicono quale."],
         "fonte": "Fonti: BLS (CPI e prezzi alla produzione), Reuters, CNBC; curva par del Tesoro USA via FMP.",
         "guardare": "Martedì alle 14:30 le vendite al dettaglio: un dato forte darebbe ragione ai Treasury, uno debole alla "
                     "borsa. Poi i conti di Nvidia: se i chip non risalgono, la borsa dovrà fare i conti con i tassi da sola."},
        {"chiave": "petrolio", "tema": "Petrolio", "breve": "il Brent scommette sulla pace",
         "titolo": "Il Brent scende anche dopo gli attacchi: il mercato scommette sulla pace",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_brent.png", "x": [d(x) for x, _ in BRENT], "soggetto": "Brent",
                     "serie": [("Brent", [v for _, v in BRENT], "#F26B1D")], "ruolo": "storia",
                     "titolo": "Il Brent ha perso oltre il 15% in due settimane e resta sopra 90 dollari",
                     "sottotitolo": "Brent future, chiusure ($)", "soglie": [(100, "100 $")],
                     "note": [(d("10-30"), 113.43, "30/10"), (d("11-10"), 91.49, "10/11")]},
         "perche": "Il petrolio cala perché Washington allontana nuovi attacchi all'Iran e il mercato scommette su un accordo (Reuters). Giovedì gli attacchi degli Houthi a siti sauditi lo avevano riportato a 95,82 $ (+3,3%), ma venerdì è rimasto fermo.",
         "numero": "-16%: il calo del Brent nella settimana al 6 novembre (Reuters). Martedì 10 il prezzo è sceso sotto i 90 $ per la prima volta da agosto.",
         "quindi": "Un nuovo attacco o un colloquio che salta riporterebbe il Brent verso i 100 $, la soglia segnata nel grafico.",
         "testo": ["Il petrolio scende anche se la guerra non è finita, e per noi il motivo è questo: il prezzo guarda a quanto "
                   "greggio arriverà sul mercato nelle prossime settimane. Un attacco a un impianto toglie barili per qualche giorno; un accordo "
                   "che riapre lo Stretto di Hormuz può rimetterne in circolazione per mesi. Per noi il mercato sta già "
                   "contando quei barili, ed è per questo che l'attacco di giovedì ha avuto vita breve.",
                   "C'è poi un conto per le tasche di tutti: il greggio diventa benzina e gasolio in poche settimane, e di "
                   "solito i carburanti entrano subito nell'inflazione. Un petrolio più basso allenta questa spinta, ma i "
                   "prezzi alla produzione senza energia dicono che l'inflazione americana non dipende solo dal barile.",
                   "Sull'offerta il quadro è disteso: la produzione Opec+ di ottobre è salita, con più greggio saudita, e le "
                   "scorte americane sono cresciute di 9 milioni di barili secondo l'API. Gli analisti di ANZ avvertono però "
                   "che un premio per il rischio geopolitico resterà, perché il conflitto non ha una via d'uscita chiara (Milano Finanza)."],
         "fonte": "Fonti: Reuters, AP; chiusure del Brent future."},
        {"chiave": "europa", "tema": "Europa", "breve": "l'Europa batte Wall Street",
         "titolo": "L'Europa chiude la migliore settimana da aprile con pochi chip in portafoglio",
         "misura": "mezzo",
         "righe": [["Società", "13/11", "Il motivo"],
                   ["Aviva", "+3,4%", "Conti del terzo trimestre, obiettivi annuali confermati (RBC)"],
                   ["Generali", "oltre -1%", "Danni da catastrofi naturali per circa 1,5 mld € nei nove mesi"],
                   ["Richemont", "quasi -4%", "Gioielli sotto gli obiettivi nel secondo trimestre"],
                   ["AMS-Osram", "oltre -9%", "Previsioni sotto le stime (Vontobel)"]],
         "larghezze": [40, 30, 112],
         "perche": "Per noi l'Europa tiene perché ha pochi chip nell'indice. Lo dice anche Robert Greil di Bankhaus Merck Finck: se il settore dell'intelligenza artificiale è debole, le borse europee vanno meglio di quelle americane e asiatiche, secondo dpa-AFX.",
         "quindi": "Il test è martedì: se i conti di Nvidia rilanciano i chip, Wall Street rimonta e il vantaggio europeo si riduce.",
         "testo": ["Un calo dei chip di solito pesa meno in Europa, perché nell'indice europeo i semiconduttori contano meno che "
                   "nel Nasdaq: i grandi nomi del settore sono americani e asiatici. Un indice pesato per valore, come l'Euro "
                   "Stoxx 50, segue dunque più le banche, il lusso e l'industria.",
                   "Ha aiutato anche l'energia: il gas è sceso di circa un quinto nei giorni scorsi (dpa-AFX), un sollievo per "
                   "industrie e bollette europee. A Milano il Ftse Mib sale del 3,6% rispetto a venerdì scorso. La partita più seguita resta Crédit Agricole-Banco BPM: "
                   "la proposta di fusione amichevole, senza Opa, ha un premio del 20%. Lunedì scorso il titolo è salito del 10,6% (Milano Finanza)."],
         "fonte": "Fonti: dpa-AFX, ANSA, SoldiOnline."},
    ],

    "scommessa": {"tesi": "Con noi: tassi americani in salita e dollaro forte frenano euro, oro e Wall Street. Contro: i conti di "
                          "Nvidia possono rilanciare i chip e le borse. Da qui a venerdì: vendite al dettaglio, Nvidia e verbali della Fed.",
                  "lunedi": True, "venerdi": False, "settimana_prec": "9-13 novembre",
                  "com_e_andata": "Le borse sono salite più del previsto e dollaro, petrolio e oro sono andati dove pensavamo; "
                                  "ha sbagliato solo il Treasury a 10 anni, spinto in alto dai prezzi sopra le attese."},
    "parole": [("Prezzi alla produzione", "I prezzi che le imprese incassano per ciò che vendono, prima che arrivino al "
                                          "consumatore: di solito anticipano quelli nei negozi."),
               ("Realizzo", "La vendita di un titolo salito molto per incassare il guadagno, anche senza notizie negative."),
               ("Rendimento a 2 anni", "L'interesse che chiede chi presta al governo americano per due anni: segue le attese "
                                       "sui tassi della Fed."),
               ("Concentrazione dell'indice", "Quando pochi titoli molto grandi pesano molto sull'indice, il loro calo lo "
                                              "trascina anche se gli altri salgono."),
               ("Conference call", "L'incontro in cui i dirigenti commentano i conti e rispondono agli analisti."),
               ("Premio per il rischio", "Il prezzo in più che il mercato chiede per tenere un investimento incerto.")],
    "fonti": [
        ("Dati di mercato", "Financial Modeling Prep (indici USA e Asia, VIX, Brent e oro future, curva par del Tesoro USA, "
                            "variazioni dei titoli); Alpha Vantage (EUR/USD, ACWI); dpa-AFX (Euro Stoxx 50); ANSA e SoldiOnline "
                            "(Ftse Mib, spread); Korea Herald (Kospi)."),
        ("Prima pagina e mercati", "Reuters, dpa-AFX, ANSA, Korea Herald, BLS."),
        ("Calendario e agenda", "Census Bureau, Federal Reserve, Trading Economics, Securities and Exchange Commission (Nvidia)."),
        ("Approfondimenti", "Chip: Reuters, Financial Modeling Prep. Tassi: BLS, Reuters, CNBC. Petrolio: Reuters, AP. "
                            "Europa: dpa-AFX, ANSA."),
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
