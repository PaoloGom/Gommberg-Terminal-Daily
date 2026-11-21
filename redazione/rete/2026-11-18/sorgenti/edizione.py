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
OGGI = dt.date(2026, 11, 18)
NOTA_DATI = "Chiusure al 17 novembre; mattina del 18 novembre dove indicato"
REG = "2026-11-16-settimana.json"          # registro della scommessa (redazione/pronostici/)

# ============================ DATI DEI GRAFICI (verificati) ============================
d = lambda s: dt.date(2026, int(s[:2]), int(s[3:]))   # "MM-GG" -> data
UST = [  # data, 2 anni, 10 anni (curva par del Tesoro, FMP)
    ("10-19", 4.77, 5.15), ("10-20", 4.79, 5.12), ("10-21", 4.81, 5.13), ("10-22", 4.65, 4.96), ("10-23", 4.69, 5.00),
    ("10-26", 4.68, 5.00), ("10-27", 4.70, 4.99), ("10-28", 4.67, 5.05), ("10-29", 4.61, 4.98), ("10-30", 4.56, 4.94),
    ("11-02", 4.59, 4.91), ("11-03", 4.61, 4.95), ("11-04", 4.58, 4.90), ("11-05", 4.46, 4.84), ("11-06", 4.51, 4.86),
    ("11-09", 4.56, 4.88), ("11-10", 4.73, 4.98), ("11-12", 4.86, 5.10), ("11-13", 4.88, 5.15), ("11-16", 4.83, 5.12),
    ("11-17", 4.80, 5.10)]
NASDAQ = [("11-05", 24315.00), ("11-06", 24579.42), ("11-09", 25253.14), ("11-10", 25065.87), ("11-11", 25466.19),
          ("11-12", 25366.09), ("11-13", 25136.27), ("11-16", 24509.76), ("11-17", 24328.38)]
BRENT = [("10-19", 109.55), ("10-20", 108.79), ("10-21", 108.82), ("10-22", 113.17), ("10-23", 116.72), ("10-26", 115.81),
         ("10-27", 113.88), ("10-28", 115.32), ("10-29", 110.80), ("10-30", 113.43), ("11-02", 104.77), ("11-03", 103.60),
         ("11-04", 94.62), ("11-05", 98.29), ("11-06", 98.32), ("11-09", 92.57), ("11-10", 91.49), ("11-11", 92.76),
         ("11-12", 95.82), ("11-13", 95.84), ("11-16", 92.44), ("11-17", 93.14)]
BRENT_VAR = [("09/11", -5.8), ("10/11", -1.2), ("11/11", +1.4), ("12/11", +3.3), ("13/11", 0.0), ("16/11", -3.6), ("17/11", +0.8)]
SETTORI = [("Tecnologia", -2.83), ("Energia", -1.01), ("Comunicazioni", -0.96), ("Servizi di pubblica utilità", -0.63),
           ("Immobiliare", -0.48), ("Finanza", -0.47), ("Materiali di base", -0.38), ("Industria", -0.32)]
EUROPA = [("ASML", -5.3), ("Tecnologia Europa", -3.9), ("STMicroelectronics", -3.1), ("Euro Stoxx 50", -2.15),
          ("FTSE MIB", -1.31), ("S&P 500", -1.03), ("Petrolio e gas Europa", -0.8), ("Nasdaq", -0.74)]

C = {
    "data": OGGI,
    "temi": ["Chip", "Fed", "Tassi", "Europa", "Petrolio", "Geopolitica"],
    "glossario": ["VIX", "CME FedWatch", "IPO", "pb", "ACWI", "SEC", "FOMC", "Brent", "guidance"],
    "meccanismi": ["M15", "M16", "M26", "M07", "M10", "M11"],
    "ticker": ticker_da_dati("dati.json"),

    "top": {
        "tema": "Chip",
        "titolo": "Nvidia supera le stime e alza la guidance, poi il titolo azzera il rialzo",
        "dek": "Il gruppo chiude il trimestre con ricavi sopra le attese di circa il 6% e per il prossimo ne annuncia 130 "
               "miliardi di dollari, più dei 125 previsti dagli analisti. Nel dopo-chiusura il titolo sale e poi perde il "
               "guadagno: Reuters lo dà in calo dello 0,3%. Il consiglio esclude il ritorno di Huang, e secondo il Wall Street "
               "Journal la SEC (autorità di vigilanza della borsa americana) verifica le comunicazioni della società. [[chip]]",
    },
    "quadro": "Per noi stamattina la paura per l'AI pesa meno della Fed. Wall Street è giù di circa l'1% e l'Euro Stoxx 50 cede il 2,1%, il peggiore dal 3 marzo. Il 2 anni e il "
              "10 anni scendono di pochi punti base: i Treasury fanno da rifugio meno di lunedì. L'oro perde un altro "
              "2,4% e il petrolio cala con le scorte americane.",
    "in30": [
        "Stasera i verbali della Fed dicono quanto era largo il consenso al rialzo. [[agenda]]",
        "Xi e Putin si vedono a Shenzhen e giovedì arriva Trump. [[mercati]]",
        "Anthropic punta a un prezzo in cima alla forchetta, secondo Bloomberg. [[anthropic]]",
    ],
    "in30_temi": ["Fed", "Geopolitica", "Tecnologia"],
    "stamattina": [
        "Nikkei alle 07:25: 59.024,28 (+0,3%)",
        "Hang Seng alle 08:59: 23.274,00 (-1,0%)",
        "Oro future alle 09:03: 3.772,70 $ (-2,4%)",
        "Brent future alle 09:06: 91,76 $ (-1,5%)",
        "EUR/USD alle 09:06: 1,0980",
    ],
    "notizie": [
        {"tag": "Geopolitica", "titolo": "L'Iran colpisce un radar americano in Bahrain, gli USA rispondono a Qeshm",
         "testo": "Droni iraniani hanno preso di mira un radar degli Stati Uniti. Gli americani hanno colpito un sito di lancio di missili "
                  "sull'isola di Qeshm, mentre l'Oman e il Qatar continuano a mediare (Reuters).", "rimando": "petrolio"},
        {"tag": "Trimestrali", "titolo": "Home Depot cede nonostante l'utile sopra le attese",
         "testo": "Pesano i mutui americani, più cari con i rendimenti in rialzo: il titolo perde l'1,8% (AP)."},
        {"tag": "Banche", "titolo": "Il guasto di Zelle pesa sulle grandi banche americane",
         "testo": "Un problema tecnico di JPMorgan ha rallentato i pagamenti lunedì e le banche principali scendono (AP)."},
        {"tag": "Italia", "titolo": "Pirelli perde il 3,8% dopo la vendita di un pacchetto da Sinochem",
         "testo": "Il socio cinese ha ceduto azioni per 455 milioni di euro sotto la chiusura del giorno prima (dpa-AFX)."},
        {"tag": "Petrolio", "titolo": "Le scorte americane di greggio salgono di 5,3 milioni di barili",
         "testo": "Nella settimana al 13 novembre l'aumento è di 5,28 milioni di barili, mentre il rischio Hormuz frena il calo del prezzo (Reuters).", "rimando": "petrolio"},
        {"tag": "Materie prime", "titolo": "Kepler Cheuvreux alza TotalEnergies, Eni e BP a buy",
         "testo": "Il comparto petrolifero è il migliore dell'Europa in una seduta in forte calo (dpa-AFX)."},
    ],

    # ---------- Pag. 5: mercati e agenda ----------
    "mercati_titolo": "Numeri, temi aperti e calendario",
    "cruscotto": [
        ("Mondo e Stati Uniti", [["MSCI ACWI (ETF, $)", "151,34", "17/11", "-1,1%", "-", "-"],
                                 ["S&amp;P 500", "7.340,53", "17/11", "-1,0%", "-2,4%", "+7,2%"],
                                 ["Nasdaq Comp.", "24.328,38", "17/11", "-0,7%", "-2,9%", "+4,7%"]]),
        ("Europa", [["Euro Stoxx 50", "6.212,11", "17/11", "-2,1%", "-1,8%", "+7,2%"],
                    ["FTSE MIB", "50.845", "17/11", "-1,3%", "-", "-"]]),
        ("Asia (18/11 intraday*)", [["Nikkei 225*", "59.024,28", "18/11", "+0,3%", "-3,6%", "+17,3%"],
                                    ["Hang Seng*", "23.274,00", "18/11", "-1,0%", "-4,3%", "-9,2%"],
                                    ["Kospi*", "n.d.", "18/11", "0,0%", "-", "-"]]),
    ],
    "cruscotto_nota": "1 g = chiusura su chiusura; 1 sett. = su martedì 10/11 (Asia su mercoledì 11/11); da inizio anno = su chiusura "
                      "2025. * Asia: dato di stamattina (Nikkei alle 07:25, Hang Seng alle 08:59, Kospi alle 04:31).",
    "cross_data": "Livello 17/11",
    "cross": [
        ("Tassi", [["Treasury 2 anni", "4,80%", "-3 pb", "+7 pb", "+3 pb", "-"],
                   ["Treasury 10 anni", "5,10%", "-2 pb", "+12 pb", "-5 pb", "-"],
                   ["Spread Italia", "105 pb", "-", "-", "-", "Chiusura in lieve calo (ANSA)"]]),
        ("Cambi", [["EUR/USD", "1,0997", "0,0%", "-1,5%", "-1,9%", "-"]]),
        ("Materie prime", [["Brent future", "93,14 $", "+0,8%", "+1,8%", "-15,0%", "-"],
                           ["Oro (future, $/oncia)", "3.864,20", "+0,3%", "-4,1%", "-7,1%", "-"]]),
        ("Volatilità", [["VIX (volatilità attesa)", "25,46", "+2,55", "+6,00", "+7,02", "Il più alto dal 6/11"]]),
    ],
    "cross_nota": "1 mese = sul 19/10. VIX = volatilità attesa sull'S&amp;P 500.",
    "termometri": [
        ("AI e chip", "Conti Nvidia usciti", "Battuti i conti, poi il rialzo svanisce", "giu: Titolo Nvidia nel dopo-chiusura", "Apertura di Wall Street alle 15:30"),
        ("Fed e tassi", "Verbali stasera", "Rialzo di dicembre già nei prezzi", "fermo: Rendimenti a 2 e 10 anni", "Verbali, mer 18 alle 20:00"),
        ("Dollaro e oro", "Euro a 1,0997 in chiusura", "Oro in calo anche con la paura", "giu: Oro future", "Verbali Fed"),
        ("Petrolio", "Scorte USA in aumento", "Il Brent cala con le scorte", "giu: Brent", "Flussi da Hormuz"),
    ],
    "fermi": "Cina (nessuna novità verificata dal 16/11).",
    "lettura": "L'Euro Stoxx 50 perde il doppio dell'S&amp;P 500, e il Nikkei sale mentre l'Hang Seng scende: le vendite sui chip non hanno colpito allo stesso modo tutte le borse.",

    "ieri": [
        ("Mar 17, 14:30", "Vendite al dettaglio USA (ottobre)", "+0,2% sul mese (atteso +0,2%; prima +0,8%)", "=", "[[tassi]]"),
        ("Mar 17, 23:00", "Conti Nvidia (terzo trimestre fiscale)", "Ricavi 115,8 mld $ (attesi 109,15 mld $)", "+", "[[chip]]"),
    ],
    "agenda": [
        ("Mer 18, 14:30", "Cantieri avviati USA (ottobre)", "1,23 milioni annualizzati; prima 1,221 milioni",
         "Quanto reggono i mutui cari",
         "<b>Sopra:</b> l'edilizia tiene anche con i tassi alti.<br/><b>Sotto:</b> pesa sui titoli delle costruzioni."),
        ("<b>Mer 18, 20:00</b>", "<b>Verbali della riunione Fed di ottobre</b>",
         "<b>Il 28/10 tassi fermi al 3,75-4,00%, con due voti per il rialzo</b>",
         "<b>Evento n.1:</b> quanto era largo il consenso al rialzo",
         "<b>Sopra:</b> verbali più duri del previsto: di solito salgono rendimenti a breve e dollaro.<br/>"
         "<b>Sotto:</b> verbali più morbidi: il 2 anni tende a scendere."),
        ("Mer 18, 22:30", "Conti Palo Alto Networks", "Primo trimestre fiscale; ricavi e utile contro le stime",
         "Conti USA dopo la chiusura",
         "<b>Sopra:</b> di solito il titolo sale se la guidance batte le attese.<br/><b>Sotto:</b> una guidance debole pesa più di un buon trimestre."),
        ("Gio 19, 01:30", "Occupazione in Australia (ottobre)", "Disoccupazione: prima 4,7%",
         "Dato di apertura per l'Asia",
         "<b>Sopra:</b> più disoccupati, di solito dollaro australiano giù.<br/><b>Sotto:</b> mercato del lavoro solido, Banca centrale più libera."),
    ],

    "moduli": [
        {"chiave": "chip", "tema": "Chip", "breve": "i conti non bastano a Nvidia",
         "titolo": "Per Nvidia la sorpresa sui conti non basta: pesano vertice e indagine",
         "misura": "doppio",
         "grafico": {"tipo": "barre", "file": "c_settori.png", "dati": SETTORI, "ordina": False, "dec": 1, "unita": "%",
                     "soggetto": "tecnologia", "ruolo": "quanto",
                     "titolo": "In media i titoli tecnologici perdono il 2,8%, gli altri settori meno",
                     "sottotitolo": "Variazione media dei titoli quotati al Nyse, 17/11 (%)"},
         "grafico2": {"tipo": "linee", "file": "c_nasdaq.png", "x": [d(x) for x, _ in NASDAQ],
                      "serie": [("Nasdaq", [v for _, v in NASDAQ], "#111111")], "soggetto": "Nasdaq", "ruolo": "storia",
                      "titolo": "Il Nasdaq perde il 4,5% dal massimo dell'11 novembre",
                      "sottotitolo": "Nasdaq Composite, chiusure (punti)", "eventi": [(d("11-12"), "Dimissioni di Huang")],
                      "note": [(d("11-11"), 25466.19, "11/11"), (d("11-17"), 24328.38, "17/11")]},
         "righe": [["Nvidia, terzo trimestre fiscale", "Risultato", "Attese"],
                   ["Ricavi (mld di dollari)", "115,8", "109,15"],
                   ["Utile per azione (dollari)", "2,68", "2,47"],
                   ["Ricavi da data center (mld di dollari)", "107,6", "101,85"]],
         "larghezze": [78, 40, 40], "ruolo_righe": "perche",
         "perche": "Gli investitori avevano già messo nel prezzo conti ottimi: Nvidia ha battuto le attese di ricavi per 17 trimestri di fila. Non c'era nel prezzo il rischio su chi la guida e sulle verifiche in corso. Il consiglio ha escluso il ritorno di Huang e il Wall Street Journal riferisce un'indagine della SEC sulle comunicazioni (Reuters). Ieri le vendite hanno colpito soprattutto la tecnologia, e il Nasdaq arretra da giorni.",
         "numero": "-17%: il calo di Nvidia da inizio anno a fine martedì (Reuters).",
         "quindi": "Alle 15:30 si vede se Nvidia apre sopra i 155,46 $ di ieri: se sì, il calo del dopo-chiusura è riassorbito.",
         "punti": ["<b>La guidance.</b> Nvidia indica 130 miliardi di ricavi per il trimestre in corso, contro i 125,25 attesi dagli "
                   "analisti, e non conta alcuna vendita di chip per data center in Cina (Reuters).",
                   "<b>Il vertice.</b> Colette Kress guida Nvidia ad interim: il consiglio valuta candidati interni ed esterni.",
                   "<b>Chi scommette contro.</b> Muddy Waters Research è ribassista sul titolo."],
         "testo": ["Come può scendere un'azienda che batte tutte le stime? Il prezzo di un titolo non misura quanto è andata bene "
                   "l'ultima trimestrale, ma quanto gli investitori si aspettano dai prossimi anni. Se tutti aspettavano conti "
                   "ottimi, i conti ottimi non cambiano nulla: muove il prezzo solo ciò che nessuno aveva messo nel conto. "
                   "Per Nvidia, ieri sera, erano il vertice dell'azienda e le verifiche in corso (Reuters).",
                   "Il caso pesa più di quello di una società qualsiasi perché Nvidia vale circa 3.800 miliardi di dollari "
                   "(Reuters). In indici come il Nasdaq e l'S&amp;P 500, che pesano le società per dimensione, di solito pochi "
                   "titoli grandi muovono molto l'indice. Per questo il destino di Nvidia conta anche per chi non la possiede.",
                   "La settimana è stata una sequenza: dimissioni di Huang il 12 novembre, vendite sui chip lunedì, conti "
                   "martedì sera. Ieri le vendite hanno colpito la tecnologia più degli altri settori: in media i titoli "
                   "tecnologici del Nyse perdono il 2,8%, mentre nessun altro settore supera il 2%."],
         "fonte": "Fonti: Reuters, Yahoo Finance; dati FMP (Nasdaq e settori).",
         "guardare": "Se Nvidia apre sopra i 155 $ e i fornitori europei recuperano, le vendite di ieri erano eccessive. Se le "
                     "notizie sulla SEC pesano più dei conti, i chip restano sotto pressione anche con una guidance sopra le attese."},
        {"chiave": "tassi", "tema": "Tassi USA", "breve": "i Treasury aspettano la Fed",
         "titolo": "Con Wall Street giù i Treasury si fermano: il mercato aspetta la Fed",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_ust.png", "x": [d(r[0]) for r in UST], "soggetto": "Treasury",
                     "serie": [("10 anni", [r[2] for r in UST], "#F26B1D"), ("2 anni", [r[1] for r in UST], "#111111")],
                     "ruolo": "storia", "titolo": "I rendimenti salgono da inizio novembre e restano alti",
                     "sottotitolo": "Treasury 2 e 10 anni, chiusure (%)", "livello": True},
         "perche": "Il 2 anni segue le attese sulla Fed. Per la riunione dell'8-9 dicembre il mercato prezza un rialzo quasi certo. Un rialzo da 50 pb a dicembre ha circa il 9% di probabilità, secondo i future (CME FedWatch, Reuters): c'è poco da scontare ancora. Per questo ieri il rifugio si è fermato a metà, con il 2 anni a -3 pb contro i -5 di lunedì.",
         "numero": "+12 pb: la salita del 10 anni in una settimana, da 4,98% a 5,10%. Due sedute di rifugio non hanno cancellato il rialzo di novembre.",
         "quindi": "Stasera alle 20:00 i verbali: se mostrano molti membri pronti a un rialzo da 50 pb, di solito il 2 anni sale anche con Wall Street in calo.",
         "testo": ["Quando la borsa cala molti comprano titoli di Stato per proteggersi: il loro prezzo sale e il rendimento, che si "
                   "muove al contrario, scende. Il rendimento a 2 anni però segue soprattutto le attese sulla Fed, e se il rialzo è "
                   "già nel prezzo la paura da sola lo muove poco.",
                   "Non è detto che il rifugio sia finito. Di solito i titoli di Stato fanno da riparo quando la paura riguarda "
                   "la crescita. Lo fanno meno quando l'inflazione tiene alta la banca centrale: ieri il petrolio è calato, ma i "
                   "rendimenti restano ai livelli più alti di novembre. Per chi ha un mutuo o compra casa il segnale conta: i tassi a lunga scadenza, non quelli della Fed, guidano il costo dei finanziamenti."],
         "fonte": "Fonti: curva par del Tesoro via FMP; Reuters."},
        {"chiave": "europa", "tema": "Europa", "breve": "l'Europa cade più di New York",
         "titolo": "L'Europa perde il doppio di Wall Street: il calo viene dai titoli tecnologici",
         "misura": "mezzo",
         "grafico": {"tipo": "barre", "file": "c_europa.png", "dati": EUROPA, "ordina": False, "dec": 1, "unita": "%",
                     "soggetto": "Europa", "ruolo": "quanto", "titolo": "Il calo è più forte dove sono i chip",
                     "sottotitolo": "Variazioni del 17/11 (%)"},
         "perche": "Per noi il calo parte dal settore tecnologico: l'indice europeo dei titoli tecnologici perde il 3,9% (dpa-AFX), con ASML tra i peggiori. Quando New York vende i chip i fornitori europei seguono, e pesano molto nell'indice, mentre petrolio e gas tengono meglio (dpa-AFX).",
         "quindi": "Alle 15:30 si vede se Wall Street apre sopra la chiusura di ieri: se il Nasdaq recupera, i fornitori europei di chip possono seguirlo.",
         "numero": "1 su 28: la frequenza con cui l'Euro Stoxx 50 perde più del 2,1% in una seduta, sulla nostra serie storica. Il calo di ieri è il più forte dal 3 marzo.",
         "testo": ["Un indice pesa le società per la loro dimensione: se poche grandi aziende cadono molto, trascinano tutto. "
                   "Quando New York vende i chip, di solito i fornitori europei del settore seguono, e il loro peso nell'indice fa "
                   "il resto (dpa-AFX).",
                   "Milano segue con il Ftse Mib a -1,31%. Lo spread tra Btp e Bund chiude in lieve calo a 105 punti (ANSA). Per noi il rischio sull'Italia "
                   "non sale, a differenza dei titoli."],
         "fonte": "Fonti: dpa-AFX (Euro Stoxx 50 e tecnologici), ANSA (Milano e spread); chiusure FMP."},
        {"chiave": "petrolio", "tema": "Petrolio", "breve": "scorte USA contro Hormuz",
         "titolo": "Il Brent scende con le scorte USA, ma il rischio Hormuz lo sostiene",
         "misura": "mezzo",
         "grafico": {"tipo": "barre", "file": "c_brent_var.png", "dati": BRENT_VAR, "ordina": False, "dec": 1, "unita": "%",
                     "soggetto": "Brent", "ruolo": "storia",
                     "titolo": "Il Brent si muove di oltre il 3% in tre sedute su sette, senza direzione",
                     "sottotitolo": "Brent future, variazione giornaliera, dal 9 al 17 novembre (%)"},
         "perche": "A pesare sono le scorte americane: nella settimana al 13 novembre c'è stato un aumento di 5,28 milioni di barili di greggio (Reuters). A sostenere il prezzo restano i rischi sul Golfo: per LSEG la normalizzazione dei flussi da Hormuz non è ancora possibile.",
         "quindi": "Se un attacco ferma l'oleodotto saudita che porta il greggio al Mar Rosso evitando Hormuz, di solito il Brent torna sopra i 100 $. Se invece Hormuz riapre e le scorte salgono ancora, il prezzo tende a scendere verso il minimo del 10 novembre, a 91,49 $.",
         "testo": ["Il prezzo del petrolio dice quanto ne serve e quanto ce n'è. Se le scorte americane crescono, ce n'è più del "
                   "necessario e il prezzo tende a scendere; se le navi non passano da Hormuz, ce n'è meno e tende a salire. Le due "
                   "spinte si contrastano da giorni.",
                   "Per l'Europa è la combinazione migliore: di solito soffre quando il greggio sale per carenza di offerta. Dal "
                   "petrolio all'inflazione, inoltre, il passaggio è corto, perché il greggio diventa benzina e gasolio in poche "
                   "settimane. Un Brent sceso del 15% in un mese toglie quindi un po' di pressione sui prezzi che la Fed guarda con più attenzione."],
         "fonte": "Fonti: Reuters; chiusure FMP del Brent future."},
        {"chiave": "anthropic", "tema": "Tecnologia", "breve": "Anthropic prima del debutto",
         "titolo": "Il debutto di Anthropic mette alla prova la liquidità del Nasdaq",
         "misura": "mezzo",
         "righe": [["IPO di Anthropic", "Dato"],
                   ["Forchetta di prezzo", "70-78 $ per azione"],
                   ["Azioni offerte", "825 milioni (801,35 dalla società, 23,65 da azionisti)"],
                   ["Opzione dei collocatori", "fino a 123,75 milioni di azioni in più"],
                   ["Valutazione indicata", "fino a 1.400 miliardi di dollari"],
                   ["Quotazione", "Nasdaq, simbolo ANT"]],
         "larghezze": [50, 130], "ruolo_righe": "quanto",
         "perche": "Secondo Bloomberg, riportato da Reuters, il prezzo sarebbe in cima alla forchetta o sopra, con una valutazione fino a 1.400 miliardi di dollari. La domanda dunque c'è: resta da vedere se basta mentre l'Euro Stoxx 50 perde per il terzo giorno di fila.",
         "quindi": "Al debutto, se il titolo apre sotto il prezzo di collocamento il test di liquidità è fallito; sopra i 78 $ la domanda regge.",
         "numero": "64 mld $: l'incasso massimo se tutte le 825 milioni di azioni si vendono a 78 $ (calcolo su dati RTTNews).",
         "testo": ["Venderne 825 milioni in una volta chiede soldi freschi al mercato. Per noi un'IPO così grande, in una settimana di "
                   "vendite sulla tecnologia, si legge prima come test di liquidità e poi come voto sull'AI.",
                   "Non c'è una regola sul primo giorno: un titolo può salire in un mercato debole e scendere in uno forte. "
                   "Conta il confronto con il prezzo di collocamento, quello a cui hanno comprato i primi investitori."],
         "fonte": "Fonti: Reuters, RTTNews."},
    ],

    "scommessa": {"tesi": "Con noi: oro ed euro vanno dove li avevamo previsti. Contro: le borse cadono molto più della "
                          "nostra previsione, per le vendite sui chip. Da qui a venerdì: i verbali della Fed di stasera.",
                  "lunedi": False, "venerdi": False, "settimana_prec": None},
    "parole": [("Guidance", "Le previsioni che l'azienda dà sui propri ricavi futuri: spesso muovono il titolo più dei risultati passati."),
               ("Acquisti rifugio", "Vendite di azioni e acquisti di titoli considerati sicuri, come Treasury e oro, "
                                    "quando cresce la paura."),
               ("Verbali della Fed", "Il resoconto della riunione della banca centrale americana, pubblicato settimane dopo: "
                                     "mostra quanto erano divisi i suoi membri."),
               ("Offerta pubblica iniziale (IPO)", "Il momento in cui una società vende azioni al pubblico per la prima volta."),
               ("Scorte di greggio", "Il petrolio già estratto e non ancora usato: se crescono, di solito il prezzo scende."),
               ("Indice pesato per dimensione", "Un indice in cui le società più grandi contano di più: pochi titoli possono "
                                                "muoverlo da soli.")],
    "fonti": [
        ("Dati di mercato", "Financial Modeling Prep (indici USA e Asia, VIX, Brent e oro future, curva par del Tesoro USA); "
                            "Alpha Vantage (EUR/USD, ACWI); dpa-AFX (Euro Stoxx 50); ANSA (FTSE MIB, spread con la Germania); "
                            "Newsquawk (Kospi alle 04:31)."),
        ("Prima pagina e mercati", "Reuters, AP, Yahoo Finance, dpa-AFX, ANSA, Newsquawk."),
        ("Calendario e agenda", "Census Bureau, Finance Calendar, Australian Bureau of Statistics, Palo Alto Networks, Federal Reserve."),
        ("Approfondimenti", "Chip: Reuters, Yahoo Finance. Tassi: curva par del Tesoro via FMP, Reuters. Europa: dpa-AFX, ANSA. "
                            "Petrolio: Reuters. Anthropic: Reuters, RTTNews."),
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
