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
- termometri: solo i temi mossi; gli altri in "fermi", fuori dopo 3 sedute. "lettura" (pag. 2) = ciò che le tabelle della
  pagina mostrano e la prima pagina non dice, mai il quadro con altre parole.
- moduli: 6 unità (mezzo = 1, doppio = 2) sulle pag. 2-4, in ordine d'importanza; un "doppio" comincia in cima a una pagina. Ogni modulo: perche, quindi, fonte; righe (mezzo max 5,
  doppio max 8); punti max 3; "guardare" obbligatorio nel doppio; niente "lettura". "numero", "punti" e "righe" solo se
  portano ciò che grafico e testo non dicono: qui sotto li usa solo chi li merita (§3.3). Due "mezzo" sulla stessa pagina si dividono
  lo spazio secondo il contenuto: non serve che siano lunghi uguali.
- grafici: "titolo" = cosa mostra, "sottotitolo" = misura e periodo, "soggetto" = parola del titolo o del perche, "ruolo" diverso
  per ogni elemento del modulo (quanto, perche, storia, conseguenza, chi); barre sempre con "unita", livelli con "livello": True;
  segna con "eventi" e "soglie" ciò che usano E quindi e Da guardare; sotto 5 valori meglio una frase. Mai "alto"/"largo".
- "&" si scrive com'è (S&P 500): lo sistema il motore. Solo trattino corto. Variazioni col segno. Numeri all'italiana.
- Lunedì: "ieri_titolo": "La settimana scorsa" (max 5 righe); 1 sett. del cruscotto = settimana intera.
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


BRENT = [("09-14", 105.68), ("09-15", 108.75), ("09-16", 105.83), ("09-17", 104.82), ("09-18", 103.87), ("09-21", 100.34),
         ("09-22", 99.25), ("09-23", 103.08), ("09-24", 106.60), ("09-25", 104.32), ("09-28", 105.28), ("09-29", 96.16),
         ("09-30", 98.03), ("10-01", 102.31), ("10-02", 102.25), ("10-05", 100.32), ("10-06", 100.58), ("10-07", 100.20),
         ("10-08", 104.28), ("10-09", 104.72), ("10-12", 106.65), ("10-13", 105.69), ("10-14", 106.06)]
d = lambda s: dt.date(2026, int(s[:2]), int(s[3:]))   # "MM-GG" -> data

C = {
    "data": OGGI,
    "temi": ["Inflazione", "Fed", "Tassi", "Chip", "Asia", "Trimestrali"],
    "glossario": ["CPI", "pb", "AI", "DRAM", "CXMT", "EPS", "ROTCE", "BTP", "Bund", "VIX", "CME FedWatch", "WTI"],
    "meccanismi": ["M26", "M01", "M04", "M21", "M28", "M10", "M11"],   # id di redazione/meccanismi.json su cui poggiano i passaggi spiegati

    "ticker": ticker_da_dati("dati.json"),   # dal dati.json del giorno (numeri.py): mai a mano

    "top": {
        "tema": "Inflazione",   # elenco chiuso (in testa al file): nessuna voce di pag. 1 ripete questo tema
        "titolo": "L'inflazione sorprende e la Fed torna a pensare a un rialzo",
        # PAGINA DI RIFERIMENTO (v8.6): i testi di questo file sono scritti come vogliamo ogni mattina. Si imita il tono,
        # non i fatti. Il fatto apre la frase, la fonte non la apre mai; parole di tutti; una cifra dove serve, non sei.
        # Il dek racconta ciò che il titolo non dice, in frasi di lunghezza diversa legate tra loro (§3.4).
        "dek": "A settembre i prezzi al consumo (CPI) salgono del 3,7% in un anno, un decimo sopra le attese, e anche "
               "senza energia e alimentari corrono più del previsto. Così i future sui tassi (CME FedWatch) danno ora al "
               "rialzo del 27-28 ottobre il 47% di probabilità, più del doppio del giorno prima. Wall Street cede "
               "(S&amp;P 500 -1,11%) trascinata dai tecnologici, e stamattina vendono anche Tokyo e Seul. [[chip]]",
        "freccia": "L'energia più cara comincia a farsi sentire nei prezzi dei servizi, scrive Axios.",  # tipo C, scheda T01 (Axios, liv. 1)
    },
    # 2-3 frasi legate tra loro: prima la lettura (cosa dicono insieme tassi, dollaro, oro, petrolio e borse, o che non si legano),
    # poi i prezzi che la provano
    "quadro": "Lo stesso dato si legge in due modi. Per noi il 2 anni (+3 pb) e il dollaro salgono perché si scommette su "
              "una Fed più dura, mentre il 10 anni scende, come quando si cerca riparo. In borsa si vendono i tecnologici e si "
              "comprano i difensivi, e intanto petrolio e oro restano fermi.",
    "in30": [
        # le 3 cose più importanti DOPO la top story: mai la top story né le sue reazioni di mercato (controlli_temi.py)
        "Banche USA divise: BofA paga l'accordo con il Tesoro, Morgan Stanley guadagna con il trading. [[banche]]",
        "TSMC batte le stime, ma i conti non fermano le vendite sui chip. [[chip]]",
        "Oggi alle 14:30 le vendite al dettaglio USA: il primo dato sui consumi di settembre. [[agenda]]",
    ],
    "in30_temi": ["Banche", "Chip", "Macro"],   # uno per punto, mai il tema della top story
    "stamattina": [
        "Asia alle 08:11: Kospi -8,68%, Nikkei -4,89%, Hang Seng -1,32%",
        "Brent future (petrolio europeo) alle 08:29: 104,39 $ (-1,6%)",
        "EUR/USD alle 09:12: 1,1216",
        "Treasury 10 anni in mattinata: 5,10% (Investing.com)",
    ],
    "notizie": [   # 6-8; "tag" = tema dell'elenco chiuso, mai quello della top story né una sua reazione di mercato
        # No: "Treasury: dopo il CPI sale il breve" o "Il dollaro si rafforza dopo il dato" (reazioni alla top story:
        # vanno nel quadro o in un modulo). Sì: fatti con una causa propria. "rimando" = chiave interna, "freccia" = riga →
        # ogni notizia porta un fatto nuovo (dato, dichiarazione, società, decisione): mai il cruscotto in parole
        # (No: "Londra in rialzo, Milano ed Euro Stoxx in calo"); almeno 2 su 6 da macro o società
        # il soggetto del titolo è il fatto (chi, cosa), mai il mercato: No "Il greggio sale", Sì "Gli Houthi colpiscono..."
        {"tag": "Chip", "titolo": "TSMC batte le stime, ma l'Asia vende lo stesso i chip",
         "testo": "Utile e ricavi del terzo trimestre crescono di oltre metà in un anno. A Taipei e a Seul, però, conta di "
                  "più la paura dei concorrenti cinesi.", "rimando": "chip"},
        {"tag": "Asia", "titolo": "SoftBank cede quasi il 10% all'apertura di Tokyo",
         "testo": "Con lei Kioxia e Advantest perdono circa l'11%: la vendita dei titoli legati all'intelligenza "
                  "artificiale è arrivata in Asia.", "rimando": "chip"},
        {"tag": "Cina", "titolo": "La cinese CXMT presenta nuove memorie e spaventa i concorrenti",
         "testo": "Per un analista di BNP Paribas AM è l'annuncio sulle memorie di nuova generazione a pesare sui titoli "
                  "(Milano Finanza).", "rimando": "chip"},
        {"tag": "Banche", "titolo": "BofA paga l'accordo con il Tesoro, Morgan Stanley incassa dal trading",
         "testo": "Nella seconda giornata di conti delle grandi banche americane l'accordo costa a BofA 1,2 mld $, mentre "
                  "il trading azionario di Morgan Stanley cresce del 41%.", "rimando": "banche"},
        {"tag": "Petrolio", "titolo": "Gli Houthi colpiscono gli uffici Aramco e il greggio sale",
         "testo": "Dopo l'attacco a Dhahran il greggio americano (WTI) arriva in seduta a circa 95 $, mentre il Brent "
                  "chiude appena sopra la vigilia (investingLive)."},
        {"tag": "Trimestrali", "titolo": "BlackRock aumenta l'utile del 25%",
         "testo": "Il gestore chiude il terzo trimestre con 1,66 mld $ di utile, nella giornata delle grandi banche "
                  "USA.", "rimando": "banche"},
    ],

    # ---------- Pag. 5: mercati e agenda (i campi restano quelli di prima: li impagina il motore) ----------
    "mercati_titolo": "Numeri, temi aperti e calendario",
    "cruscotto": [   # [nome, ultimo, data, 1 g, 1 sett. (vs venerdì), da inizio anno]
        ("Mondo e Stati Uniti", [["MSCI ACWI (ETF, $)", "158,75", "14/10", "-1,2%", "-1,3%", "n.d."],
                         ["S&amp;P 500", "7.718,94", "14/10", "-1,1%", "-1,2%", "+12,8%"],
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
    # note di pag. 5: solo come leggere le colonne. Le fonti dei dati stanno nella tabella Fonti di pag. 6.
    "cruscotto_nota": "1 g = chiusura su chiusura; 1 sett. = su venerdì 9/10; da inizio anno = su chiusura 2025. "
                      "* Asia: dato di stamattina (Kospi alle 08:11).",
    "cross_data": "Livello 14/10",
    "cross": [       # [strumento, livello, 1 g, 1 sett., 1 mese, lettura breve o "-"]
        ("Tassi", [["Treasury 2 anni", "4,82%", "+3 pb", "+2 pb", "+17 pb", "Sale con le attese sulla Fed [[treasury]]"],
                   ["Treasury 10 anni", "5,19%", "-2 pb", "-5 pb", "+22 pb", "-"],
                   ["Treasury 30 anni", "5,52%", "-4 pb", "-8 pb", "+18 pb", "-"],
                   ["Spread Italia", "110 pb", "+2 pb", "n.d.", "n.d.", "10 anni italiano al 4,57% (Teleborsa)"]]),
        ("Cambi", [["EUR/USD", "1,1156", "-0,4%", "-0,4%", "-3,4%", "-"]]),
        ("Materie prime", [["Brent future", "106,06 $", "+0,4%", "+1,3%", "+0,4%", "-"],
                           ["Oro (spot, $/oncia)", "4.162,84", "0,0%", "+0,4%", "-4,2%", "-"]]),
        ("Volatilità", [["VIX (volatilità attesa)", "16,87", "+1,60", "+2,03", "-0,23", "Massimo dal 16/9"]]),
    ],
    "cross_nota": "1 mese = sul 14/9. VIX = volatilità attesa sull'S&amp;P 500.",
    "termometri": [  # (tema, a che punto, ultima novità, cosa si muove, cosa guardare). Al massimo 4.
        # cosa si muove = "su: ...", "giu: ..." o "fermo: ...", e dopo i due punti CHE COSA sale o scende
        ("Fed e tassi", "Riunione 27-28 ottobre", "Rialzo di ottobre di nuovo in gioco", "su: Probabilità di un rialzo", "Dati USA delle 14:30"),
        ("AI e chip", "Rally concentrato", "Vendite da Wall Street all'Asia", "giu: Titoli dei chip", "Nasdaq e Kospi"),
        ("Dollaro", "EUR/USD 1,1156 in chiusura", "Più forte dopo il CPI", "su: Dollaro contro euro", "Treasury a 2 anni"),
        ("Petrolio", "Brent sopra 104 $", "WTI verso 95 $ in seduta", "fermo: Brent, senza direzione", "Prezzi della benzina"),
    ],
    "fermi": "Iran e Hormuz (nessuna novità verificata dal 13/10), Francia e debito europeo (dal 12/10).",
    # lettura (pag. 2): MAI il quadro di pag. 1 con altre parole (§3.3). Dice ciò che le tabelle di questa pagina mostrano
    # e la prima pagina no, e spiega il passaggio a chi le tabelle non le sa leggere.
    "lettura": "Due cose che le tabelle dicono e la prima pagina no. Il Russell 2000, l'indice delle società più piccole, "
               "perde quasi il doppio dell'S&amp;P 500: di solito chi ha più debiti soffre di più i tassi alti. Il Dow "
               "Jones, dove la tecnologia pesa poco, è quasi fermo: la vendita riguarda un settore, non tutta la borsa.",

    # ---------- Pag. 3-5 ----------
    "ieri": [        # (quando, evento, dato contro attese, sorpresa +/-/=, → max 8 parole). Casa delle cifre solo per i dati NON raccontati altrove
        # sorpresa: "+" se il NUMERO è più alto delle attese, "-" se è più basso, "=" se uguale. È aritmetica, non un
        # giudizio: sussidi di disoccupazione a 200 mila contro 195 mila attesi sono "+", anche se è un dato peggiore.
        ("Mer 14, 14:30", "Prezzi al consumo USA (settembre)", "3,7% su un anno (atteso 3,6%); senza energia e alimentari 2,6% (2,5%)", "+", "[[treasury]]"),
        ("Mer 14", "Trimestrali BofA, Morgan Stanley, BlackRock", "Esiti divergenti", "", "[[banche]]"),
    ],
    # Misura di pag. 5: temi aperti al massimo 4; righe uscite ("ieri") più righe in arrivo ("agenda") al massimo 7.
    # agenda: 5-6 righe, (quando Roma, evento, attese, perché conta, come può muovere i mercati) - <b> sull'evento chiave.
    # L'ultima colonna insegna a leggere il dato PRIMA che esca: cosa succede di solito se esce sopra le attese e cosa
    # se esce sotto, con parole di tutti, sempre nella forma "<b>Sopra:</b> ... <br/><b>Sotto:</b> ..." (una riga ciascuno).
    # Sempre come tendenza ("di solito"), mai come previsione; se un evento non ha un numero atteso, dice cosa ascoltare. Il giorno dopo la riga torna in "ieri" con l'esito.
    "agenda": [
        ("Gio 15, 11:00", "Produzione industriale area euro (agosto)", "0,0% sul mese; prima -0,1%",
         "Tenuta dell'industria europea",
         "<b>Sopra:</b> un po' di sostegno all'euro.<br/><b>Sotto:</b> pesa sui titoli industriali europei."),
        ("<b>Gio 15, 14:30</b>", "<b>Vendite al dettaglio USA (settembre)</b>", "<b>+0,3% sul mese; prima +1,2%</b>",
         "<b>Evento n.1:</b> primi consumi dopo il CPI",
         "<b>Sopra:</b> di solito salgono dollaro e rendimenti a breve: consumi forti lasciano spazio alla Fed."
         "<br/><b>Sotto:</b> il rialzo di ottobre perde forza."),
        ("Gio 15, 14:30", "Prezzi alla produzione USA (PPI, settembre)", "+0,6% sul mese; prima +0,4%",
         "Se l'energia passa a monte della filiera",
         "<b>Sopra:</b> conferma il dato di ieri, di solito pesa sui titoli di Stato.<br/><b>Sotto:</b> l'inflazione sembra meno diffusa."),
        ("Gio 15, 14:30", "Sussidi di disoccupazione settimanali", "199 mila; prima 197 mila", "Tenuta del lavoro",
         "<b>Sopra</b> (più sussidi): lavoro più debole, di solito rendimenti giù.<br/><b>Sotto:</b> lavoro solido, Fed più libera."),
        ("Ven 16, 15:15", "Produzione industriale USA (settembre)", "+0,4% sul mese; prima 0,0%", "Attività reale",
         "<b>Sopra:</b> l'economia regge anche con tassi alti.<br/><b>Sotto:</b> torna il timore di una frenata."),
    ],
    # niente nota sotto l'agenda: le fonti stanno nella tabella Fonti di pag. 6, l'ora di Roma e "di solito" nell'intestazione
    # ---------- Pag. 2-4: analisi e storie. 6 unità (mezzo = 1, doppio = 2) su tre pagine, da 3 a 6 storie, in ordine
    # d'importanza: la prima spiega la top story. Una pagina intera ("doppio") solo alla storia che la regge. ----------
    "moduli": [   # 6 unità su pag. 2-4: ogni pagina 1 "doppio" o 2 "mezzo". "breve" = voce dell'indice di pag. 1
        {"chiave": "treasury", "tema": "Tassi USA", "breve": "curva al minimo dal 28/9",
         "titolo": "Con la Fed più dura la curva dei Treasury si appiattisce",
         "misura": "doppio",
         "grafico2": {"tipo": "barre", "file": "c_curva_1g.png",
                    "dati": [(k, round((UST_14[k] - UST_13[k]) * 100)) for k in UST_14],
                    "titolo": "Salgono le scadenze brevi, scendono le lunghe",
                    "sottotitolo": "Curva Treasury, variazione del 14/10 (pb)", "unita": " pb", "dec": 0, "ordina": False,
                    "soggetto": "curva", "ruolo": "quanto"},   # misure dal motore: mai "alto"/"largo"
         # ruolo: ogni elemento risponde a una domanda DIVERSA della tesi e non ripete i numeri di un altro (ridondanza()).
         # Qui una delle tante scelte possibili, valida per QUESTA tesi: barre = quanto oggi, linea = la storia del mese.
         # Non è uno schema da copiare: ogni giorno gli elementi si scelgono dalla tesi del giorno e cambiano.
         "grafico": {"tipo": "linee", "file": "c_ust_mese.png", "x": [d(r[0]) for r in UST_MESE], "soggetto": "curva",
                       "titolo": "La distanza tra 10 e 2 anni torna ai livelli di fine settembre",
                       "sottotitolo": "10 anni meno 2 anni, ultimo mese (pb)", "ruolo": "storia",
                       "serie": [("10 anni meno 2 anni", [round((r[2] - r[1]) * 100) for r in UST_MESE], "#F26B1D")]},
         # niente "punti": le variazioni per scadenza sono già nelle barre (§3.3). Il "numero" c'è perché dice una cosa che
         # grafici e testo non dicono: quanto era stata più forte la prima reazione
         "numero": "+12 pb: il salto del 2 anni nei minuti dopo il dato (Axios). Ha chiuso a +3: la prima reazione "
                   "era stata quattro volte più forte di quella rimasta a fine seduta.",
         # B1: la causa si confronta con la forma della curva. Un'inflazione più alta spiega il breve, non il lungo in calo:
         # dirlo e dare la lettura della redazione che regge alla prova dei prezzi (registro "anomalia" in fatti.json, §6.2c)
         "perche": "Di solito il breve segue le attese sulla Fed, e con il CPI sono salite. Un'inflazione più alta però non spiega il lungo in calo. Per noi sono acquisti rifugio dopo le vendite sui tecnologici, e lo conferma il rialzo del VIX (la volatilità attesa a Wall Street).",
         "quindi": "Se il 10 anni torna verso il 5,30-5,35% toccato in serata, torna a contare l'inflazione. Sotto il 5,10% di stamattina, invece, prevale la paura sulla borsa.",
         # testo: IL PASSAGGIO PRIMA DI TUTTO (§3.4). Il primo paragrafo fa capire a chi non ha mai studiato finanza perché
         # il fatto muove il prezzo, un anello alla volta, con parole di tutti i giorni e senza definizioni da dizionario:
         # la parola difficile si capisce da ciò che fa ("pretende un interesse più alto, ed è questo il rendimento").
         # Poggia su un meccanismo di meccanismi.json (qui M26 e M01), non su una scheda. Poi il racconto che i grafici
         # non fanno (storia del mese, mutui, asta), senza riscrivere le cifre. Chi i mercati li conosce non perde nulla.
         "testo": ["Dietro i due movimenti ci sono due domande diverse. Chi presta soldi al governo americano per due "
                   "anni si chiede dove saranno i tassi della Fed. Se li aspetta più alti pretende un interesse più "
                   "alto, ed è questo il rendimento che sale. Chi presta per dieci anni guarda più lontano, alla "
                   "crescita e ai prezzi dei prossimi anni. E quando la borsa spaventa, molti comprano proprio questi "
                   "titoli per mettere i soldi al riparo: il loro prezzo sale e il rendimento, che si muove al "
                   "contrario, scende.",
                   "Messi in fila dal più breve al più lungo, i rendimenti disegnano una curva. Di solito sale, perché "
                   "chi presta per molti anni chiede di più: in dieci anni può succedere di tutto. Quando il breve "
                   "sale e il lungo scende la curva si fa piatta, e il messaggio è che il mercato vede tassi alti "
                   "oggi e un'economia più debole domani. È un segnale che si guarda con attenzione, "
                   "non una previsione.",
                   "Il mese ha avuto due fasi. Fino al 21 settembre la distanza tra 10 e 2 anni si è quasi dimezzata; "
                   "poi il lungo ha corso più del breve, fino al massimo del 7 ottobre. In una settimana quel movimento "
                   "si è quasi tutto riassorbito.",
                   "Conta anche fuori dalla finanza. I mutui americani seguono il 10 anni più dei tassi della Fed: se il "
                   "lungo scende, comprare casa costa meno anche con una banca centrale più dura.",
                   "Il prossimo esame è l'asta dei titoli a 20 anni di mercoledì. Una domanda debole rilancerebbe il "
                   "lungo e smentirebbe la lettura del rifugio. Le ultime aste lunghe hanno avuto una domanda nella "
                   "media: è il metro per giudicare questa."],
         # guardare (obbligatorio nel doppio): ciò che darebbe ragione al breve o al lungo, e quando; non ripete il quindi
         "guardare": "Lo diranno i prossimi dati sui prezzi. Se l'inflazione dei servizi resta alta, il breve ha visto "
                     "giusto e il rialzo resta sul tavolo. Se invece rallenta, il calo del lungo può essere l'inizio di "
                     "un movimento più ampio, che di solito aiuta anche le borse."},
        {"chiave": "chip", "tema": "Chip e Asia", "breve": "TSMC batte le stime, l'Asia vende",
         "titolo": "TSMC batte le stime, ma i chip cadono per paura dei concorrenti",
         "misura": "doppio",
         "grafico": {"tipo": "barre", "file": "c_contagio.png", "dati": CONTAGIO, "ordina": False, "dec": 1,
                       "soggetto": "chip", "ruolo": "quanto",
                       "unita": "%",
                       # titolo = cosa mostra il grafico; sottotitolo = misura e periodo (v7.8)
                       "titolo": "La vendita parte dalla tecnologia USA e arriva ai chip asiatici",
                       "sottotitolo": "variazioni % del 14/10 e di stamattina"},
         "grafico2": {"tipo": "linee", "file": "c_nasdaq.png", "x": [d(x) for x, _ in NASDAQ],
                    "serie": [("Nasdaq", [v for _, v in NASDAQ], "#111111")], "soggetto": "Nasdaq", "ruolo": "storia",
                    "titolo": "Il Nasdaq perde il 3,3% dal massimo del 6 ottobre", "sottotitolo": "Nasdaq Composite, punti",
                    "eventi": [(d("10-14"), "CPI")],   # segna l'evento di cui parla il testo (v7.8); soglie = [(livello, "testo")]
                    "note": [(d("10-06"), 27599.79, "6/10"), (d("10-14"), 26692.87, "14/10")]},
         "righe": [["TSMC, terzo trimestre", "Valore", "Variazione annua", "Contro le attese"],
                   ["Ricavi (mld di dollari taiwanesi)", "1.494,24", "+50,9%", "-"],
                   ["Utile netto (mld di dollari taiwanesi)", "763,06", "+68,7%", "Stima LSEG 746,3"],
                   ["Quota dei ricavi da wafer a 2 nanometri", "8%", "-", "-"],
                   ["Quota dei ricavi da wafer a 3 nanometri", "33%", "-", "-"]],
         "larghezze": [70, 30, 36, 46], "ruolo_righe": "perche",   # i conti solidi: la tesi è che non bastano
         "perche": "La vendita partita dai titoli dell'intelligenza artificiale del Nasdaq si allarga a tutta l'Asia (ANSA). Le borse asiatiche aprono quando New York ha già chiuso, e di solito ne ereditano l'umore. Chi ha venduto a Wall Street ritrova a Seul e a Taipei gli stessi titoli, o i loro fornitori.",
         # numero: un conto che il lettore non trova già fatto (qui lo scarto tra utile e stima), e misura la tesi
         "numero": "+2,2%: di tanto l'utile di TSMC supera la stima degli analisti. Un margine piccolo: per noi la buona notizia era già in gran parte nei prezzi.",
         "quindi": "Oggi alle 15:30 riapre il Nasdaq, il primo test per l'Europa.",
         "punti": ["<b>Tokyo.</b> Cede anche Tokyo Electron, circa il 6,5% in apertura: la vendita tocca i produttori "
                   "di macchinari per chip.",
                   "<b>Il timore.</b> Un analista di BNP Paribas AM indica l'annuncio di CXMT, produttore cinese, sulle "
                   "memorie di nuova generazione."],
         "testo": ["Perché conti migliori delle stime non bastano? In borsa un prezzo guarda avanti: chi compra un "
                   "produttore di chip paga oggi gli utili che si aspetta nei prossimi anni. Un trimestre migliore "
                   "del previsto racconta il passato. Un concorrente che promette memorie nuove mette invece in dubbio i prezzi di "
                   "domani, e di solito sono quelli a muovere il titolo.",
                   "Il calo è più forte dove i chip pesano di più. A Taipei e a Seul pochi produttori di semiconduttori "
                   "fanno una parte larga dell'indice: se vendono loro, vende tutta la borsa. A Tokyo il peso è minore, e "
                   "infatti il Nikkei cede meno, nonostante SoftBank e i produttori di macchinari per chip."],
         "fonte": "Notizie e conti TSMC: ANSA, Milano Finanza, Teleborsa.",
         "guardare": "Se i chip americani recuperano, la vendita resta asiatica; se scendono ancora, il timore sulle "
                     "memorie diventa un tema globale."},
        {"chiave": "banche", "tema": "Trimestrali", "breve": "BofA contro Morgan Stanley",
         # titolo = la TESI in una proposizione (§3.2); la tabella dà i conti, il testo il meccanismo, nessuno ripete l'altro
         "titolo": "I mercati nervosi premiano le banche d'affari più di quelle che prestano",
         "misura": "mezzo",
         "righe": [["Società", "Risultato del terzo trimestre", "Il punto"],
                   ["Bank of America", "Utile netto 6,9 mld $", "Onere straordinario di 1,2 mld $ per l'accordo con il "
                    "Tesoro USA; titolo in calo (TheStreet)"],
                   ["Morgan Stanley", "Utile per azione (EPS) 3,03 $, ricavi 20,33 mld $", "Trading azionario +41% a "
                    "5,79 mld $; rendimento sul capitale tangibile (ROTCE) 22,6%"],
                   ["BlackRock", "Utile 1,66 mld $ (+25%)", "Utile in crescita (FIRSTonline)"]],
         "larghezze": [30, 58, 94],
         # perche = la causa con fonte, non la parafrasi della tabella; quindi = una cosa osservabile che il testo non dice
         "perche": "BofA paga un onere straordinario per l'accordo con il Tesoro, mentre Morgan Stanley incassa da consulenza e trading, che crescono quando i mercati si agitano (FIRSTonline).",
         "quindi": "Il trading di Morgan Stanley, 5,79 mld $ nel trimestre, è il metro per Goldman Sachs e Citigroup, che pubblicano nei prossimi giorni.",
         # niente "lettura": la tesi sta nel titolo e si dice una volta (§3.3; il motore rifiuta il campo).
         # testo = il meccanismo che il lettore non vede nei numeri: spiega, non ripete tabella e perché
         "testo": ["La differenza sta in come si guadagna. Le banche d'affari vivono di scambi e commissioni, che salgono "
                   "quando i mercati si agitano. Quelle commerciali, come BofA, vivono del margine tra gli interessi sui "
                   "prestiti e sui depositi: se i tassi scendono il margine si stringe, e un trimestre nervoso non le aiuta. "
                   "Per questo in una stagione di conti le banche non vanno lette tutte insieme: lo stesso trimestre "
                   "può essere ottimo per chi fa da intermediario e mediocre per chi presta. BlackRock sta ancora "
                   "altrove: gestisce i risparmi degli altri e non presta, e di solito guadagna di più quando i mercati "
                   "salgono e i clienti investono. Tre mestieri diversi sotto la stessa parola, banca.",
                   "Il nervosismo premia chi intermedia per un motivo semplice. Ogni compravendita passa da un intermediario, "
                   "che trattiene una piccola differenza tra il prezzo a cui compra e quello a cui vende. Quando i "
                   "prezzi si muovono molto i clienti scambiano di più, per proteggersi o per approfittarne, e di "
                   "solito quella differenza si allarga. È un guadagno che dipende da quanto il mercato si muove, non "
                   "dalla direzione in cui va."],
         "fonte": "Fonti: comunicato Morgan Stanley (SEC), Milano Finanza, FIRSTonline, TheStreet."},
        {"chiave": "petrolio", "tema": "Petrolio", "breve": "il barile dietro l'inflazione",
         "titolo": "Il petrolio resta sopra i 100 dollari e tiene alta l'inflazione americana",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_brent.png", "x": [d(x) for x, _ in BRENT], "soggetto": "petrolio",
                     "serie": [("Brent", [v for _, v in BRENT], "#F26B1D")], "ruolo": "storia",
                     "titolo": "Dal primo ottobre il Brent non è più sceso sotto i 100 dollari",
                     "sottotitolo": "Brent future, chiusure ($)", "soglie": [(100, "100 $")],
                     "note": [(d("09-29"), 96.16, "29/9"), (d("10-14"), 106.06, "14/10")]},
         "perche": "Sono i prezzi dell'energia, legati alla guerra in Iran, ad aver spinto l'inflazione di settembre (TheStreet). L'attacco degli Houthi agli uffici Aramco di Dhahran ha aggiunto il timore per le forniture.",
         "quindi": "Oggi alle 14:30 i prezzi alla produzione dicono se il rincaro dell'energia è già arrivato alle imprese.",
         "numero": "+10,3%: quanto ha recuperato il Brent dal minimo del 29 settembre. In due settimane ha ripreso tutto il calo di fine mese.",
         # testo = il passaggio (M10, M11): dal barile ai prezzi, un anello alla volta, senza una sigla
         "testo": ["Dal barile ai prezzi il passaggio è corto. Il greggio diventa benzina e gasolio in poche settimane, e "
                   "di solito i carburanti entrano subito nell'inflazione complessiva. Più lento è il secondo giro: "
                   "trasporti e imballaggi più cari finiscono poco alla volta nei prezzi di beni e servizi, quelli che "
                   "la Fed guarda di più. Per questo un petrolio che resta caro pesa sui tassi anche nei giorni in cui "
                   "si muove poco.",
                   "C'è poi una differenza che conta per l'Europa. Quando il petrolio sale perché si teme per le "
                   "forniture, come dopo un attacco a un impianto, di solito soffrono i paesi che il greggio lo "
                   "comprano. Europa e Giappone pagano di più senza vendere di più. Diverso è il caso di "
                   "un'economia che corre e consuma più energia: lì di solito salgono insieme petrolio e borse."],
         "fonte": "Fonti: TheStreet, investingLive; chiusure del Brent future."},
    ],

    # ---------- Pag. 6 ----------
    "scommessa": {"tesi": "Con noi: per ora quasi nulla. Contro: il dato sui prezzi e le vendite sui tecnologici "
                          "spingono giù le borse. Da qui a venerdì: prezzi alla produzione e vendite al dettaglio.",
                  "lunedi": False,     # True il primo giorno di borsa della settimana (pagina6_lunedi + verdetto.json)
                  "venerdi": False, "settimana_prec": None},   # settimana_prec solo il lunedì, es. "12-16 ottobre"
    "parole": [("Appiattimento della curva", "La distanza tra i rendimenti a lunga e a breve scadenza si riduce: "
                                             "il breve sale più del lungo, o il lungo scende di più."),
               ("Inflazione core", "L'inflazione senza energia e alimentari, le voci più volatili: mostra la tendenza "
                                   "di fondo dei prezzi."),
               ("Titoli difensivi", "Settori come sanità e beni di consumo base, i cui utili dipendono poco dal ciclo "
                                    "economico."),
               # fino a 6 voci, in ordine di importanza: le prime 3 escono sempre, le altre se pag. 6 ha spazio
               ("Acquisti rifugio", "Vendite di azioni e acquisti di titoli considerati sicuri, come Treasury e oro, "
                                    "quando cresce la paura."),
               ("Utile per azione", "L'utile diviso per il numero di azioni: il dato che gli analisti confrontano "
                                    "con le stime."),
               ("Memorie DRAM", "I chip di memoria di lavoro di computer e server: il loro prezzo segue il ciclo "
                                "della domanda.")],
    "fonti": [
        ("Dati di mercato", "Financial Modeling Prep (indici USA e Asia, VIX, Brent future, curva par del Tesoro USA); "
                            "Alpha Vantage (EUR/USD, ACWI, oro spot); ANSA (FTSE MIB); Teleborsa (titoli di Stato italiani, spread con la Germania, "
                            "Asia delle 08:11)."),
        ("Prima pagina e mercati", "TheStreet, Axios, Milano Finanza, investingLive, FXStreet, Investing.com, ANSA, "
                       "Teleborsa."),
        ("Calendario e agenda", "Teleborsa, Admiral Markets, Banca d'Italia, Federal Reserve."),
        ("Approfondimenti", "Banche: comunicato Morgan Stanley (SEC), Milano Finanza, FIRSTonline, TheStreet. Treasury: "
                            "curva par del Tesoro via FMP, Axios, Investing.com. Chip e Asia: ANSA, Milano Finanza, "
                            "Teleborsa (TSMC). Petrolio: TheStreet, investingLive."),
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
