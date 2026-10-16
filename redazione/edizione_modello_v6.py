"""MODELLO v6 - Edizione #004 del 15/10/2026 rifatta nella struttura v6 (SPEC v6).
Ogni giorno: copia questo file nella cartella di lavoro, sostituisci SOLO i blocchi "CONTENUTI" e "DATI DEI GRAFICI"
(il dizionario C: nessun codice da scrivere), poi lancia
`python3 edizione_modello_v6.py <cartella di lavoro> <pdf di uscita>`: il motore impagina, riempie le 6 pagine
allungando i grafici scritti come dict, risolve i rimandi e scrive voce_indice.json per edizioni.json.
Prima: valuta.py (stato.json) e grafico.py (c_forecast.png) nella cartella di lavoro, come da ISTRUZIONI par. 4.
Regole rapide: un fatto ha una casa sola; in pag. 1 si titola e si rimanda con [[chiave]] (diventa "→ pag. N");
righe "→" (freccia=...) max 5 in tutto; solo trattino corto; variazioni con segno (il motore le colora).
Chiavi di rimando disponibili: mercati, agenda, scommessa + la "chiave" di ogni approfondimento."""
import datetime as dt
import json
import os
import sys

REPO = os.path.join(os.environ.get("GTD_REPO", "/home/claude/gtd"), "redazione")   # kit e registri (mai la copia)
sys.path.insert(0, REPO)
from gommberg_engine import *  # noqa: E402,F403

LAVORO = sys.argv[1] if len(sys.argv) > 1 else "."
USCITA = sys.argv[2] if len(sys.argv) > 2 else None
os.chdir(LAVORO)   # grafici e c_forecast.png stanno qui

# =============================== CONTENUTI DEL GIORNO ===============================
OGGI = dt.date(2026, 10, 15)
NOTA_DATI = "Chiusure al 14 ottobre; mattina del 15 ottobre dove indicato"
REG = "2026-10-12-settimana.json"          # registro della scommessa (redazione/pronostici/)

# ============================ DATI DEI GRAFICI (verificati) ============================
UST_13 = {"1M": 4.10, "3M": 4.26, "6M": 4.34, "1A": 4.48, "2A": 4.79, "3A": 4.90, "5A": 5.00, "7A": 5.11, "10A": 5.21,
          "20A": 5.60, "30A": 5.56}
UST_14 = {"1M": 4.11, "3M": 4.28, "6M": 4.37, "1A": 4.53, "2A": 4.82, "3A": 4.92, "5A": 5.00, "7A": 5.09, "10A": 5.19,
          "20A": 5.57, "30A": 5.52}
SP_2_10 = [("09-10", 39), ("09-11", 33), ("09-14", 32), ("09-15", 33), ("09-16", 27), ("09-17", 27), ("09-18", 25),
           ("09-21", 20), ("09-22", 25), ("09-23", 26), ("09-24", 31), ("09-25", 36), ("09-28", 32), ("09-29", 37),
           ("09-30", 41), ("10-01", 46), ("10-02", 45), ("10-05", 47), ("10-06", 48), ("10-07", 51), ("10-08", 47),
           ("10-09", 44), ("10-13", 42), ("10-14", 37)]
NASDAQ = [("09-11", 26333.04), ("09-14", 26186.41), ("09-15", 25981.57), ("09-16", 25978.42), ("09-17", 26418.30),
          ("09-18", 26522.55), ("09-21", 27122.09), ("09-22", 27244.28), ("09-23", 26936.04), ("09-24", 26939.37),
          ("09-25", 27068.72), ("09-28", 26820.38), ("09-29", 26797.54), ("09-30", 26861.06), ("10-01", 26871.60),
          ("10-02", 27190.86), ("10-05", 27477.31), ("10-06", 27599.79), ("10-07", 27538.69), ("10-08", 27193.34),
          ("10-09", 27366.17), ("10-12", 27245.90), ("10-13", 27204.38), ("10-14", 26692.87)]


UST_MESE = [  # data, 2 anni, 10 anni, 30 anni (curva par del Tesoro, FMP)
    ("09-10", 4.56, 4.95, 5.37), ("09-11", 4.63, 4.96, 5.35), ("09-14", 4.65, 4.97, 5.34), ("09-15", 4.67, 5.00, 5.36),
    ("09-16", 4.74, 5.01, 5.35), ("09-17", 4.67, 4.94, 5.29), ("09-18", 4.76, 5.01, 5.34), ("09-21", 4.76, 4.96, 5.29),
    ("09-22", 4.71, 4.96, 5.29), ("09-23", 4.85, 5.11, 5.40), ("09-24", 4.87, 5.18, 5.47), ("09-25", 4.81, 5.17, 5.49),
    ("09-28", 4.92, 5.24, 5.56), ("09-29", 4.89, 5.26, 5.59), ("09-30", 4.88, 5.29, 5.64), ("10-01", 4.78, 5.24, 5.61),
    ("10-02", 4.83, 5.28, 5.63), ("10-05", 4.84, 5.31, 5.66), ("10-06", 4.79, 5.27, 5.64), ("10-07", 4.77, 5.28, 5.67),
    ("10-08", 4.75, 5.22, 5.60), ("10-09", 4.80, 5.24, 5.60), ("10-13", 4.79, 5.21, 5.56), ("10-14", 4.82, 5.19, 5.52)]
CONTAGIO = [  # (etichetta, var %): Wall Street 14/10 (TheStreet), Asia 15/10 (Teleborsa 08:11, ANSA, Milano Finanza)
    ("Tecnologia S&P 500 (14/10)", -3.00), ("Nasdaq (14/10)", -1.88), ("Hang Seng (08:11)", -1.32),
    ("Nikkei 225 (08:11)", -4.89), ("Kospi (08:11)", -8.68)]   # nei grafici solo valori esatti: i "circa" restano nel testo
NIKKEI = [("07-01", 70474.96), ("07-15", 68751.51), ("07-17", 64141.12), ("07-23", 66422.60), ("07-29", 61434.19),
          ("07-31", 64362.02), ("08-05", 66300.44), ("08-13", 68308.59), ("08-17", 69220.25), ("08-19", 65326.42),
          ("08-27", 66131.98), ("09-02", 64325.64), ("09-07", 66399.84), ("09-15", 63484.10), ("09-18", 65018.95),
          ("09-25", 66364.20), ("09-29", 65481.27), ("10-01", 68956.72), ("10-06", 70683.98), ("10-08", 69042.11),
          ("10-09", 69030.92), ("10-13", 67777.52), ("10-14", 67744.29), ("10-15", 64425.95)]


d = lambda s: dt.date(2026, int(s[:2]), int(s[3:]))   # "MM-GG" -> data

C = {
    "data": OGGI,
    "temi": ["Inflazione", "Fed", "Tassi", "Chip", "Asia", "Trimestrali"],
    "glossario": ["CPI", "pb", "AI", "DRAM", "CXMT", "EPS", "ROTCE", "BTP", "Bund", "VIX", "CME FedWatch", "WTI"],
    "meccanismi": ["M26"],    # id di redazione/meccanismi.json usati nelle righe M

    "ticker": [("MSCI ACWI (ETF)", "158,75 $", "-1,2% g"), ("S&amp;P 500", "7.718,94", "-1,1% g"),
               ("EURO STOXX 50", "6.162,90", "-0,3% g"), ("UST 10 ANNI", "5,19%", "-2 pb g"),
               ("BRENT FUTURE", "106,06 $", "+0,4% g"), ("EUR/USD", "1,1156", "-0,4% g"), ("VIX", "16,87", "+1,60 g")],

    "top": {
        "titolo": "Inflazione USA sopra le attese: torna in gioco il rialzo Fed di ottobre",
        "dek": "A settembre l'indice dei prezzi al consumo (CPI) sale del 3,7% annuo contro il 3,6% atteso; il core "
               "(senza energia e alimentari) del 2,6% contro il 2,5%. La probabilità di un rialzo dei tassi Fed il 27-28 "
               "ottobre sale al 47% secondo Axios, dal 22% del giorno prima (CME FedWatch, la stima ricavata dai "
               "future). Wall Street chiude in calo e stamattina le vendite si estendono all'Asia.",
        "freccia": "Secondo Axios i rincari dell'energia cominciano a passare ai prezzi dei servizi.",  # tipo C, scheda T01 (Axios, liv. 1)
    },
    "in30": [
        "Wall Street cede: S&amp;P 500 -1,11%, Nasdaq -1,88%, con il settore tecnologico in testa ai ribassi.",
        "Asia in forte calo stamattina: a Tokyo e Seul guidano le vendite i titoli legati all'intelligenza "
        "artificiale (AI), secondo Teleborsa. [[chip]]",
        "Oggi alle 14:30 vendite al dettaglio e prezzi alla produzione USA: il primo test dopo il CPI. [[agenda]]",
    ],
    "stamattina": [
        "Asia alle 08:11: Kospi -8,68%, Nikkei -4,89%, Hang Seng -1,32%",
        "Brent future (petrolio europeo) alle 08:29: 104,39 $ (-1,6%)",
        "EUR/USD alle 09:12: 1,1216",
        "Treasury 10 anni in mattinata: 5,10% (Investing.com)",
    ],
    "notizie": [   # 6-8; "rimando" = chiave di un pezzo interno, "freccia" = riga → (conta nelle 5)
        {"tag": "Tassi", "titolo": "Treasury: dopo il CPI sale il breve, scende il lungo",
         "testo": "Il 2 anni chiude in rialzo, 10 e 30 anni in calo dopo il picco serale. Cosa dice la forma della "
                  "curva.",
         "rimando": "treasury"},
        {"tag": "Fed", "titolo": "Mercato diviso sul rialzo di ottobre",
         "testo": "Per una strategist citata da Milano Finanza il dato non basta a rilanciare davvero l'ipotesi di "
                  "ottobre; secondo Axios i future la vedono invece più probabile di ieri."},
        {"tag": "Wall Street", "titolo": "Tecnologia -3,00%, difensivi in rialzo",
         "testo": "In rialzo sanità (+2,44%) e beni di consumo base (+2,21%). Russell 2000 -1,93%, Dow Jones -0,09%. "
                  "Milano Finanza parla di vendite sull'AI.", "rimando": "mercati"},
        {"tag": "Chip", "titolo": "TSMC: utile +68,7% nel terzo trimestre, sopra le stime",
         "testo": "L'utile netto batte la stima degli analisti raccolta da LSEG (Teleborsa). I conti, usciti stamattina, non fermano le vendite "
                  "sui chip in Asia.", "rimando": "chip"},
        {"tag": "Banche", "titolo": "BofA delude, Morgan Stanley corre nel trading",
         "testo": "Sintesi di Milano Finanza sulla seconda giornata di trimestrali bancarie; BofA sconta l'onere per "
                  "la sanzione del Tesoro USA.", "rimando": "banche"},
        {"tag": "Valute", "titolo": "Il dollaro si rafforza su tutta la linea",
         "testo": "L'euro scende subito dopo il dato (investingLive) e chiude in calo; stamattina recupera."},
        {"tag": "Petrolio", "titolo": "Petrolio USA (WTI) ai massimi da tre settimane",
         "testo": "In seduta il WTI sale a circa 95 $; il Brent future chiude in "
                  "lieve rialzo e stamattina scende."},
        {"tag": "Europa", "titolo": "Londra in rialzo, Milano ed Euro Stoxx in calo",
         "testo": "Piazza Affari chiude in calo (ANSA), Londra sale. Lo spread tra BTP e Bund (titoli di Stato italiani e tedeschi) si allarga di "
                  "2 punti base (pb) secondo Teleborsa.", "rimando": "mercati"},
    ],

    # ---------- Pag. 2 ----------
    "mercati_titolo": "Cruscotto, tassi e temi aperti",
    "grafico_sett": "Indici: variazione dal 9 ottobre",
    "cruscotto": [   # [nome, ultimo, data, 1 g, 1 sett. (vs venerdì), da inizio anno]
        ("Globale", [["MSCI ACWI (ETF, $)", "158,75", "14/10", "-1,2%", "-1,3%", "n.d."]]),
        ("Stati Uniti", [["S&amp;P 500", "7.718,94", "14/10", "-1,1%", "-1,2%", "+12,8%"],
                         ["Nasdaq Comp.", "26.692,87", "14/10", "-1,9%", "-2,5%", "+14,8%"],
                         ["Dow Jones", "51.621,48", "14/10", "-0,1%", "-0,1%", "+7,4%"],
                         ["Russell 2000", "2.729,53", "14/10", "-1,9%", "-2,8%", "+10,0%"]]),
        ("Europa", [["Euro Stoxx 50", "6.162,90", "14/10", "-0,3%", "-0,6%", "+6,3%"],
                    ["FTSE MIB", "49.753", "14/10", "-0,6%", "0,0%", "n.d."],
                    ["FTSE 100", "10.724,86", "14/10", "+0,7%", "+1,6%", "+8,0%"]]),
        ("Asia (15/10 intraday*)", [["Nikkei 225*", "64.425,95", "15/10", "-4,9%", "-6,7%", "+28,0%"],
                                    ["Hang Seng*", "24.010,00", "15/10", "-1,3%", "-0,8%", "-6,3%"],
                                    ["Kospi*", "n.d.", "15/10", "-8,7%", "n.d.", "n.d."]]),
    ],
    "cruscotto_nota": "Fonte: FMP, Alpha Vantage, ANSA (FTSE MIB), Teleborsa (Kospi, 08:11). 1 g = chiusura su chiusura; "
                      "1 sett. = su venerdì 9/10; da inizio anno = su chiusura 2025. * Asia: dato di stamattina.",
    "cross_data": "Livello 14/10",
    "cross": [       # [strumento, livello, 1 g, 1 sett., 1 mese, lettura breve o "-"]
        ("Tassi", [["Treasury 2 anni", "4,82%", "+3 pb", "+2 pb", "+17 pb", "Sale con le attese sulla Fed [[treasury]]"],
                   ["Treasury 10 anni", "5,19%", "-2 pb", "-5 pb", "+22 pb", "-"],
                   ["Treasury 30 anni", "5,52%", "-4 pb", "-8 pb", "+18 pb", "-"],
                   ["Spread BTP-Bund", "110 pb", "+2 pb", "n.d.", "n.d.", "BTP 10 anni al 4,57% (Teleborsa)"]]),
        ("Cambi", [["EUR/USD", "1,1156", "-0,4%", "-0,4%", "-3,4%", "-"]]),
        ("Materie prime", [["Brent future", "106,06 $", "+0,4%", "+1,3%", "+0,4%", "-"],
                           ["Oro (spot, $/oncia)", "4.162,84", "0,0%", "+0,4%", "-4,2%", "-"]]),
        ("Volatilità", [["VIX (volatilità attesa)", "16,87", "+1,60", "+2,03", "-0,23", "Massimo dal 16/9"]]),
    ],
    "cross_nota": "Fonte: FMP, Alpha Vantage (EUR/USD, oro), Teleborsa (BTP, spread). 1 mese = sul 14/9. VIX = volatilità "
                  "attesa sull'S&amp;P 500.",
    "termometri": [  # (tema, a che punto, ultima novità, tendenza su/giu/fermo o testo, cosa guardare)
        ("Fed e tassi", "Riunione 27-28 ottobre", "Rialzo di ottobre di nuovo in gioco", "su", "Dati USA delle 14:30"),
        ("Inflazione USA", "In accelerazione", "Energia nei servizi (Axios)", "su", "Prezzi alla produzione (PPI)"),
        ("AI e chip", "Rally concentrato", "Vendite da Wall Street all'Asia", "giu", "Nasdaq e Kospi"),
        ("Dollaro", "EUR/USD sotto 1,12", "Più forte dopo il CPI", "su", "Treasury a 2 anni"),
        ("Petrolio", "Brent sopra 104 $", "WTI ai massimi da 3 settimane", "mista", "Prezzi della benzina"),
    ],
    "fermi": "Iran e Hormuz (nessuna novità verificata dal 13/10), Francia e debito europeo (dal 12/10).",
    "lettura": "Lo stesso dato letto in due modi: i future sui tassi alzano le probabilità di un rialzo a ottobre, i "
               "titoli di Stato a lunga chiudono con rendimenti più bassi; in borsa cedono i tecnologici e salgono i "
               "difensivi. Stima redazionale: senza conferme da PPI e vendite il mercato resta diviso.",

    # ---------- Pag. 3-5 ----------
    "agenda_titolo": "Ieri in calendario e in arrivo",
    "ieri": [        # (quando, evento, dato contro attese, sorpresa +/-/=, → max 8 parole)
        ("Mer 14, 14:30", "CPI USA settembre, indice generale", "+0,6% m/m (sul mese prima), atteso +0,6%", "=", "-"),
        ("Mer 14, 14:30", "CPI USA settembre, indice generale", "+3,7% a/a (sull'anno prima), atteso 3,6%; agosto 3,4%",
         "+", "-"),
        ("Mer 14, 14:30", "CPI USA settembre, core", "+0,3% m/m, atteso +0,2%; +2,6% a/a, atteso 2,5%", "+",
         "Energia nei servizi, secondo Axios"),
        ("Mer 14", "Trimestrali BofA, Morgan Stanley, BlackRock", "Esiti divergenti", "", "[[banche]]"),
    ],
    "agenda": [      # (quando Roma, evento, attese, perché conta) - <b> sull'evento chiave
        ("Gio 15, 11:00", "Produzione industriale area euro (agosto)", "0,0% m/m; prec. -0,1%",
         "Tenuta dell'industria europea"),
        ("<b>Gio 15, 14:30</b>", "<b>Vendite al dettaglio USA (settembre)</b>", "<b>+0,3% m/m; prec. +1,2%</b>",
         "<b>Evento n.1:</b> primi consumi dopo il CPI"),
        ("Gio 15, 14:30", "Prezzi alla produzione USA (PPI, settembre)", "+0,6% m/m (Teleborsa); prec. +0,4%",
         "Se l'energia passa a monte della filiera"),
        ("Gio 15, 14:30", "Sussidi di disoccupazione settimanali", "199 mila; prec. 197 mila", "Tenuta del lavoro"),
        ("Gio 15, 14:30", "Indice Philadelphia Fed (ottobre)", "27,8 (Teleborsa) o 26,5 (Admiral); prec. 37,8",
         "Industria manifatturiera USA"),
        ("Gio 15", "Assemblee FMI-Banca Mondiale, G7 e G20 (Bangkok, fino al 17)", "-",
         "Messaggi su debito, inflazione, energia"),
        ("Ven 16, 15:15", "Produzione industriale USA (settembre)", "+0,4% m/m; prec. 0,0%", "Attività reale"),
    ],
    "agenda_nota": "Fonti: Teleborsa, Admiral Markets, Banca d'Italia. Orari in ora di Roma.",
    "bivio": {
        "titolo": "Il bivio: la Fed del 27-28 ottobre dopo il CPI",
        "righe": [["Scenario", "Prob.*", "Treasury", "Azionario", "Dollaro (EUR/USD)"],
                  ["Pausa e tono morbido", "30%", "Rendimenti in calo su tutta la curva", "Rimbalzo, tecnologici in testa",
                   "Dollaro più debole"],
                  ["Pausa e tono duro", "30%", "2 anni stabile, 10 anni intorno a 5,1-5,3%", "Laterale, rotazione verso "
                   "difensivi", "Stabile"],
                  ["Rialzo a ottobre (25 pb)", "40%", "2 anni in salita, curva piatta", "Pressione su tecnologici e "
                   "small cap", "Dollaro più forte, sotto 1,11"]],
        "larghezze": [38, 14, 50, 46, 34],
        "nota": "* Stime redazionali soggettive. Oggi vendite al dettaglio e PPI possono spostarle.",
    },
    "approfondimenti": [   # 2-3; formato "grafico" | "tabella" | "due_grafici"; "breve" = titolo per l'indice di pag. 1
        {"chiave": "banche", "tema": "Trimestrali", "breve": "BofA contro Morgan Stanley",
         "titolo": "Banche USA: BofA sconta la sanzione, Morgan Stanley corre nel trading",
         "formato": "tabella",
         "righe": [["Società", "Risultato del terzo trimestre", "Il punto"],
                   ["Bank of America", "Utile netto 6,9 mld $", "Onere straordinario di 1,2 mld $ per l'accordo con il "
                    "Tesoro USA; titolo in calo (TheStreet)"],
                   ["Morgan Stanley", "Utile per azione (EPS) 3,03 $, ricavi 20,33 mld $", "Trading azionario +41% a "
                    "5,79 mld $; rendimento sul capitale tangibile (ROTCE) 22,6%"],
                   ["BlackRock", "Utile 1,66 mld $ (+25%)", "Patrimonio gestito a livello record (FIRSTonline)"]],
         "larghezze": [30, 58, 94],
         "lettura": "La seconda giornata di trimestrali divide le grandi banche: il risultato di BofA è segnato da una "
                    "voce straordinaria, quello di Morgan Stanley dall'attività sui mercati.",
         "fonte": "Fonti: comunicato Morgan Stanley (SEC), Milano Finanza, FIRSTonline, TheStreet."},
        {"chiave": "treasury", "tema": "Tassi USA", "breve": "breve su, lungo giù dopo il CPI",
         "titolo": "Dopo il CPI il 2 anni sale e il 10 anni scende: la curva si appiattisce",
         "formato": "due_grafici",
         "img_sx": {"tipo": "barre", "file": "c_curva_1g.png",
                    "dati": [(k, round((UST_14[k] - UST_13[k]) * 100)) for k in UST_14],
                    "titolo": "Curva Treasury: variazione del 14/10 (pb)", "unita": " pb", "dec": 0, "ordina": False,
                    "alto": 2.5},
         "img_dx": {"tipo": "linee", "file": "c_2_10.png", "x": [d(x) for x, _ in SP_2_10],
                    "serie": [("10 anni meno 2 anni", [v for _, v in SP_2_10], "#1F5FA8")],
                    "titolo": "Distanza 10 anni - 2 anni (pb)", "alto": 2.5,
                    "note": [(d("10-07"), 51, "51"), (d("10-14"), 37, "37")]},
         "img_sopra": {"tipo": "linee", "file": "c_ust_mese.png", "x": [d(r[0]) for r in UST_MESE], "largo": 7.3,
                       "alto": 2.2, "titolo": "Treasury 2, 10 e 30 anni nell'ultimo mese (%)",
                       "serie": [(n, [r[i] for r in UST_MESE], c) for i, n, c in
                                 ((1, "2 anni", "#1F5FA8"), (2, "10 anni", "#F26B1D"), (3, "30 anni", "#111111"))]},
         "fonte_sx": "Fonte: curva par del Tesoro USA via FMP, 13/10 e 14/10.",
         "fonte_dx": "Fonte: idem, chiusure 10/9 - 14/10.",
         "punti": ["<b>Il breve.</b> Fino a 3 anni i rendimenti chiudono in rialzo; il 2 anni era salito di circa "
                   "12 pb subito dopo il dato (Axios).",
                   "<b>Il lungo.</b> Dal 7 anni in su chiudono in calo, dopo il picco serale del 10 anni al 5,33% "
                   "(Investing.com).",
                   "<b>La curva.</b> La distanza tra 10 e 2 anni torna ai livelli di fine settembre: la curva si "
                   "appiattisce."],
         "righe": [["Scadenza", "7 ottobre", "13 ottobre", "14 ottobre", "Var. dal 7/10", "Var. 14/10"],
                   ["3 mesi", "4,22%", "4,26%", "4,28%", "+6 pb", "+2 pb"],
                   ["1 anno", "4,42%", "4,48%", "4,53%", "+11 pb", "+5 pb"],
                   ["5 anni", "5,03%", "5,00%", "5,00%", "-3 pb", "0 pb"],
                   ["20 anni", "5,71%", "5,60%", "5,57%", "-14 pb", "-3 pb"],
                   ["10 anni meno 2 anni", "51 pb", "42 pb", "37 pb", "-14 pb", "-5 pb"]],
         "larghezze": [40, 26, 26, 26, 32, 32],
         "lettura": "Per il rialzo del breve e il calo del lungo le fonti di oggi non danno una spiegazione "
                    "verificata. Il 10 anni chiude sotto i livelli di fine "
                    "settembre e cala ancora stamattina. <b>Soglia:</b> 5,30-5,35%, toccata ma mai tenuta a fine seduta.",
         "freccia": "Di solito il 2 anni segue la Fed più del 10 anni: ieri è salito, il 10 anni è sceso."},
        # ↑ riga M: id "M26" di redazione/meccanismi.json
        {"chiave": "chip", "tema": "Chip e Asia", "breve": "TSMC batte le stime, l'Asia vende",
         "titolo": "TSMC batte le stime, ma l'Asia vende i chip",
         "formato": "due_grafici",
         "img_sopra": {"tipo": "barre", "file": "c_contagio.png", "dati": CONTAGIO, "ordina": False, "dec": 1,
                       "largo": 7.3, "alto": 2.2,
                       "titolo": "Dalla tecnologia USA ai chip asiatici: variazioni % (14/10 e stamattina)"},
         "img_sx": {"tipo": "linee", "file": "c_nasdaq.png", "x": [d(x) for x, _ in NASDAQ],
                    "serie": [("Nasdaq", [v for _, v in NASDAQ], "#111111")], "alto": 2.4,
                    "titolo": "Nasdaq Composite: -3,3% dal 6 ottobre",
                    "note": [(d("10-06"), 27599.79, "6/10"), (d("10-14"), 26692.87, "14/10")]},
         "img_dx": {"tipo": "linee", "file": "c_nikkei.png", "x": [d(x) for x, _ in NIKKEI],
                    "serie": [("Nikkei", [v for _, v in NIKKEI], "#111111")], "alto": 2.4,
                    "titolo": "Nikkei 225 da luglio", "note": [(d("10-15"), 64425.95, "15/10*")]},
         "fonte_sx": "Fonte: FMP, chiusure giornaliere.", "fonte_dx": "Fonte: FMP; 15/10 = livello di stamattina.",
         "righe": [["TSMC, terzo trimestre", "Valore", "Variazione annua", "Contro le attese"],
                   ["Ricavi (mld di dollari taiwanesi)", "1.494,24", "+50,9%", "-"],
                   ["Utile netto (mld di dollari taiwanesi)", "763,06", "+68,7%", "Stima LSEG 746,3"],
                   ["Quota dei ricavi da wafer a 2 nanometri", "8%", "-", "-"],
                   ["Quota dei ricavi da wafer a 3 nanometri", "33%", "-", "-"]],
         "larghezze": [70, 30, 36, 46],
         "lettura": "Le vendite partite ieri dal settore tecnologico di Wall Street si sono estese stamattina all'Asia, "
                    "con i cali più forti sui titoli dei semiconduttori e sulle borse dove i chip contano di più: Seul e Tokyo.",
         "punti": ["<b>Tokyo.</b> SoftBank perde quasi il 10%, Kioxia e Advantest circa l'11%; Tokyo Electron circa il "
                   "6,5% in apertura (ANSA, Milano Finanza).",
                   "<b>Il timore.</b> Un analista di BNP Paribas AM cita l'annuncio di CXMT (produttore cinese di "
                   "memorie) sulle DRAM, le memorie di lavoro, di nuova generazione.",
                   "<b>Il clima.</b> \"In questo momento gli investitori stanno entrando nel panico\" (Milano Finanza). I "
                   "conti di TSMC, usciti stamattina, non hanno fermato le vendite."],
         "fonte": "Notizie e conti TSMC: ANSA, Milano Finanza, Teleborsa."},
    ],

    # ---------- Pag. 6 ----------
    "scommessa": {"tesi": "il CPI e i tecnologici mettono sotto pressione le borse: tutti e 7 i mercati sono ancora "
                          "dentro il range, ma solo Treasury 10 anni e Brent vanno nella direzione prevista.",
                  "lunedi": False,     # True il primo giorno di borsa della settimana (pagina6_lunedi + verdetto.json)
                  "venerdi": False, "settimana_prec": None},   # settimana_prec solo il lunedì, es. "12-16 ottobre"
    "parole": [("Appiattimento della curva", "La distanza tra i rendimenti a lunga e a breve scadenza si riduce: "
                                             "il breve sale più del lungo, o il lungo scende di più."),
               ("Inflazione core", "L'inflazione senza energia e alimentari, le voci più volatili: mostra la tendenza "
                                   "di fondo dei prezzi."),
               ("Titoli difensivi", "Settori come sanità e beni di consumo base, i cui utili dipendono poco dal ciclo "
                                    "economico.")],
    "fonti": [
        ("Dati di mercato", "Financial Modeling Prep (indici USA e Asia, VIX, Brent future, curva par del Tesoro USA); "
                            "Alpha Vantage (EUR/USD, ACWI, oro spot); ANSA (FTSE MIB); Teleborsa (BTP, spread BTP-Bund, "
                            "Asia delle 08:11)."),
        ("Pag. 1 e 2", "TheStreet, Axios, Milano Finanza, investingLive, FXStreet, Investing.com, ANSA, "
                       "Teleborsa."),
        ("Calendario e agenda", "Teleborsa, Admiral Markets, Banca d'Italia, Federal Reserve."),
        ("Approfondimenti", "Banche: comunicato Morgan Stanley (SEC), Milano Finanza, FIRSTonline, TheStreet. Treasury: "
                            "curva par del Tesoro via FMP, Axios, Investing.com. Chip e Asia: ANSA, Milano Finanza, "
                            "Teleborsa (TSMC)."),
        ("La scommessa", "Registro della settimana 12-16 ottobre e script del laboratorio (valuta.py, grafico.py)."),
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
    render_v6(out, lambda: edizione_v6(C, stato=stato, reg=reg, verdetto=verdetto, pagella=pagella))
    json.dump(voce_indice(C, stato, reg), open("voce_indice.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(out)
