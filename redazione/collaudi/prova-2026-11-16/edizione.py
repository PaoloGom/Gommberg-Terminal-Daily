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
from numeri import fmt as _f, var as _v  # noqa: E402
OGGI = dt.date(2026, 11, 16)
NOTA_DATI = "Chiusure al 13 novembre; i mercati asiatici e i future non hanno ancora aperto"
REG = "2026-11-16-settimana.json"
_D = json.load(open("dati.json", encoding="utf-8"))["serie"]
def _u(n):
    return [x[1] for x in _D[n]["ultimi"]]
def _riga(nome, etichetta, dec, sett_idx, base_ytd, data="13/11", ytd=True):
    u = _u(nome)
    return [etichetta, _f(u[0], dec), data, _v(u[0], u[1]), _v(u[0], u[sett_idx]), (_v(u[0], base_ytd) if base_ytd else "n.d.")]

# ============================ DATI DEI GRAFICI (verificati) ============================
d = lambda s: dt.date(2026, int(s[:2]), int(s[3:]))
UST_6 = {"1M": 4.02, "3M": 4.19, "6M": 4.23, "1A": 4.33, "2A": 4.51, "3A": 4.59, "5A": 4.64, "7A": 4.74, "10A": 4.86, "20A": 5.29, "30A": 5.26}
UST_13 = {"1M": 4.10, "3M": 4.32, "6M": 4.42, "1A": 4.65, "2A": 4.88, "3A": 4.92, "5A": 4.98, "7A": 5.05, "10A": 5.15, "20A": 5.52, "30A": 5.47}
# 2 anni (FMP, curva par del Tesoro) meno il limite alto dei tassi Fed (4,00%, dal rialzo di settembre), in pb
DUE_ANNI = [("10-14", 4.82), ("10-15", 4.77), ("10-16", 4.74), ("10-19", 4.77), ("10-20", 4.79), ("10-21", 4.81), ("10-22", 4.65),
            ("10-23", 4.69), ("10-26", 4.68), ("10-27", 4.70), ("10-28", 4.67), ("10-29", 4.61), ("10-30", 4.56), ("11-02", 4.59),
            ("11-03", 4.61), ("11-04", 4.58), ("11-05", 4.46), ("11-06", 4.51), ("11-09", 4.56), ("11-10", 4.73), ("11-12", 4.86),
            ("11-13", 4.88)]
ORO = [("10-14", 4107.9), ("10-15", 4170.1), ("10-16", 4181.1), ("10-19", 4160.1), ("10-20", 4142.6), ("10-21", 4150.0),
       ("10-22", 4060.4), ("10-23", 4007.9), ("10-26", 4038.4), ("10-27", 4074.6), ("10-28", 4051.6), ("10-29", 4031.4),
       ("10-30", 3898.9), ("11-02", 3969.6), ("11-03", 3940.4), ("11-04", 4073.0), ("11-05", 4113.5), ("11-06", 4074.9),
       ("11-09", 4114.5), ("11-10", 4030.2), ("11-11", 4000.5), ("11-12", 3885.3), ("11-13", 3886.3)]
BRENT = [("10-14", 106.06), ("10-15", 105.92), ("10-16", 109.86), ("10-19", 109.55), ("10-20", 108.79), ("10-21", 108.82),
         ("10-22", 113.17), ("10-23", 116.72), ("10-26", 115.81), ("10-27", 113.88), ("10-28", 115.32), ("10-29", 110.80),
         ("10-30", 113.43), ("11-02", 104.77), ("11-03", 103.60), ("11-04", 94.62), ("11-05", 98.29), ("11-06", 98.32),
         ("11-09", 92.57), ("11-10", 91.49), ("11-11", 92.76), ("11-12", 95.82), ("11-13", 95.84)]
SETTORI = [("Tecnologia", -2.15), ("Industria", -1.26), ("Materiali", -0.82), ("Immobiliare", -0.62), ("Energia", -0.05),
           ("Finanza", 0.22), ("Servizi pubblici", 0.30), ("Consumo ciclico", 0.35), ("Consumo di base", 0.42),
           ("Sanità", 0.53), ("Comunicazioni", 0.96)]

C = {
    "data": OGGI,
    "temi": ["Chip", "Fed", "Tassi", "Materie prime", "Petrolio", "Geopolitica"],
    "glossario": ["CPI", "core", "TIPS", "ACWI", "VIX", "EIA"],
    "meccanismi": ["M15", "M16", "M26", "M02", "M05", "M20", "M23", "M10", "M11"],
    "ticker": ticker_da_dati("dati.json"),

    "top": {
        "tema": "Chip",
        "titolo": "Nvidia presenta martedì i primi conti senza Huang, e il mercato è già nervoso",
        "dek": "Il titolo ha perso il 13% in cinque sedute, la sesta settimana in calo, e venerdì la vendita si è allargata ai "
               "concorrenti: AMD -9%, Broadcom e Marvell quasi -5%. Gli analisti si aspettano ricavi di 109,5 mld $, appena sopra "
               "i 108 che l'azienda aveva indicato. Le opzioni a scadenza settimanale prezzano un movimento di circa il 9% in un senso o nell'altro "
               "(Investopedia). A guidare il titolo sarà la previsione dei prossimi tre mesi, che presenta Colette Kress, "
               "amministratore delegato ad interim. [[nvidia]]",
        "freccia": "Per MarketPulse conterà più la previsione del trimestre in arrivo che i conti di quello chiuso.",
    },
    "quadro": "Venerdì i prezzi hanno detto una cosa sola con voci diverse. Per noi il mercato non teme la guerra né i conti: "
              "teme il costo del denaro. I rendimenti salgono (10 anni al 5,15%, 2 anni al 4,88%) e l'oro cade, come quando si "
              "scommette su una Fed più dura. Il petrolio resta sotto i massimi di ottobre e l'Europa chiude la settimana in "
              "rialzo. A pagare sono soprattutto i titoli tecnologici, che valgono di più quando i tassi sono bassi.",
    "in30": [
        "I verbali della Fed di mercoledì dicono quanto era vicino il rialzo. [[tassi]]",
        "L'oro scende ai minimi da oltre un anno e la guerra in Iran non lo difende. [[oro]]",
        "Trump chiude all'accordo con l'Iran, ma il petrolio aveva già scontato la fine della guerra. [[petrolio]]",
    ],
    "in30_temi": ["Fed", "Materie prime", "Petrolio"],
    "stamattina_titolo": "Cosa guardare all'apertura",
    "stamattina": [
        "Tokyo apre alle 01:00: venerdì Nikkei +0,53%, Hang Seng -1,55%",
        "14:30 Empire State; 18:00 parla Warsh, presidente della Fed",
        "Euro Stoxx 50: venerdì 6.386,86, a un passo da quota 6.400 (dpa-AFX)",
        "Brent: venerdì 95,84 $; il minimo di martedì è 91,49 $",
    ],
    "notizie": [
        {"tag": "Inflazione", "titolo": "Prezzi alla produzione USA: +0,3% a ottobre, ma +0,5% senza le voci volatili",
         "testo": "Il dato generale è sotto le attese; senza alimentari, energia e servizi commerciali l'indice corre "
                  "invece del 4,9% in un anno (BLS).", "rimando": "tassi"},
        {"tag": "Trimestrali", "titolo": "Cisco e Applied Materials calano nonostante i conti sopra le attese",
         "testo": "Cisco cede il 6% e Applied Materials il 3% dopo i risultati; Dell perde il 7% (Yahoo Finance)."},
        {"tag": "Geopolitica", "titolo": "Trump potrebbe non attaccare l'Iran se Teheran non lo provoca",
         "testo": "Lo ha detto ai consiglieri, secondo Reuters, dopo aver scritto «We don't need a deal with Iran».",
         "rimando": "petrolio"},
        {"tag": "Geopolitica", "titolo": "L'Iran dice che tre petroliere hanno urtato mine a Hormuz, gli USA smentiscono",
         "testo": "Sabato la marina iraniana parla di rotte non autorizzate; l'esercito americano dice che quelle "
                  "principali sono libere e nessuna nave è stata nominata.",
         "rimando": "petrolio"},
        {"tag": "Europa", "titolo": "Per Merck Finck l'Europa batte Wall Street se l'intelligenza artificiale cede",
         "testo": "Per Robert Greil di Merck Finck, se l'intelligenza artificiale cede le borse europee vanno meglio "
                  "di quelle americane e asiatiche (dpa-AFX)."},
        {"tag": "Tecnologia", "titolo": "Il bitcoin scende vicino a 68 mila dollari e Strategy perde quasi il 5%",
         "testo": "È circa il 30% sotto il massimo di gennaio; Strategy cede dopo la notizia di un'esclusione da alcuni indici "
                  "(Yahoo Finance)."},
    ],

    "mercati_titolo": "Numeri, temi aperti e calendario",
    "cruscotto": [
        ("Mondo e Stati Uniti", [_riga("ACWI", "MSCI ACWI (ETF, $)", 2, 2, None),
                                 _riga("S&P 500", "S&amp;P 500", 2, 5, 6845.49),
                                 _riga("Nasdaq", "Nasdaq Comp.", 2, 5, 23241.99),
                                 _riga("Russell 2000", "Russell 2000", 2, 5, 2481.91)]),
        ("Europa", [_riga("Euro Stoxx 50", "Euro Stoxx 50", 2, 5, 5796.22),
                    ["FTSE MIB", "51.858", "13/11", "+0,1%", "n.d.", "n.d."]]),
        ("Asia (chiusure del 13/11)", [_riga("Nikkei 225", "Nikkei 225", 2, 5, 50339.48),
                                       _riga("Hang Seng", "Hang Seng", 2, 5, 25630.55),
                                       ["Kospi", "5.290,53", "13/11", _v(5290.53, 5342.73), "n.d.", "n.d."]]),
    ],
    "cruscotto_nota": "1 g = chiusura su chiusura; 1 sett. = su venerdì 6/11; da inizio anno = su chiusura 2025.",
    "cross_data": "Livello 13/11",
    "cross": [
        ("Tassi", [["Treasury 2 anni", "4,88%", "+2 pb", "+37 pb", "+9 pb", "Sale con le attese sulla Fed [[tassi]]"],
                   ["Treasury 10 anni", "5,15%", "+5 pb", "+29 pb", "-6 pb", "-"]]),
        ("Cambi", [["EUR/USD", "1,1021", _v(1.1021, 1.1053), _v(1.1021, 1.1143), _v(1.1021, 1.1198), "-"]]),
        ("Materie prime", [["Brent future", "95,84 $", _v(95.84, 95.82), _v(95.84, 98.32), _v(95.84, 105.69), "-"],
                           ["Oro (future, $/oncia)", "3.886,30", _v(3886.3, 3885.3), _v(3886.3, 4074.9), _v(3886.3, 4177.3),
                            "Minimo di 13 mesi giovedì [[oro]]"]]),
        ("Volatilità", [["VIX (volatilità attesa)", "19,30", "+0,60", "-6,34", "+4,03", "-"]]),
    ],
    "cross_nota": "1 mese = sul 13/10. VIX = volatilità attesa sull'S&amp;P 500.",
    "termometri": [
        ("Fed e tassi", "Riunione dell'8-9 dicembre", "Verbali di ottobre mercoledì", "su: Rendimento del 2 anni", "Verbali e Warsh"),
        ("AI e chip", "Conti Nvidia martedì", "Vendita di venerdì estesa ai concorrenti", "giu: Titoli dei chip", "Conti Nvidia"),
        ("Iran e petrolio", "Hormuz: accuse sulle mine", "Trump chiude all'accordo", "fermo: Brent, senza direzione", "Scorte USA di mercoledì"),
        ("Oro", "Minimo di 13 mesi", "Venduto con i rendimenti in salita", "giu: Prezzo dell'oro", "Verbali Fed"),
    ],
    "fermi": "Trump in Cina: il viaggio al vertice Apec di Shenzhen del 18-19 novembre non è cambiato (investingLive).",
    "lettura": "Due cose che le tabelle dicono e la prima pagina no. Le piccole società americane (Russell 2000) guadagnano nella "
               "settimana circa la metà dell'S&amp;P 500: di solito chi ha più debiti soffre di più con tassi che salgono. E l'Asia "
               "si divide: Tokyo sale di oltre il 6%, Hong Kong cede il 3,5%. Il VIX (indice della volatilità attesa a Wall Street) scende a 19,30 dal 25,64 di una settimana fa ma resta sopra il 15,27 di un mese fa: la paura cala meno di quanto era salita.",
    "ieri": [
        ("Mar 10, 14:30", "Prezzi al consumo USA (ottobre)", "+0,4% sul mese; core +0,3% (atteso +0,2%)", "+", "[[tassi]]"),
        ("Ven 13, 14:30", "Prezzi alla produzione USA (ottobre)", "+0,3% sul mese (atteso +0,4%); core +0,5%", "-", "[[tassi]]"),
    ],
    "agenda": [
        ("Lun 16, 14:30", "Indice Empire State (manifattura di New York)", "prima 25,5",
         "Primo dato del mese sull'industria",
         "<b>Sopra:</b> di solito salgono rendimenti e dollaro.<br/><b>Sotto:</b> frenata che pesa sui titoli ciclici."),
        ("Lun 16, 18:00", "Parla Kevin Warsh, presidente della Fed", "-", "La prima voce della Fed dopo i prezzi",
         "<b>Ascolta:</b> se apre al mezzo punto a dicembre, di solito salgono dollaro e rendimenti; se resta sui dati, il mercato respira."),
        ("Mar 17, 14:30", "Vendite al dettaglio USA (ottobre)", "-", "Consumi dopo prezzi più alti",
         "<b>Sopra:</b> consumi forti lasciano spazio alla Fed e spingono i rendimenti.<br/><b>Sotto:</b> il rialzo di dicembre perde forza."),
        ("<b>Mar 17, 23:00</b>", "<b>Conti di Nvidia (terzo trimestre)</b>", "<b>Ricavi 109,5 mld $, utile per azione 2,47 $</b>",
         "<b>Evento n.1:</b> i primi conti senza Huang",
         "<b>Sopra:</b> ricavi e previsione sopra le attese: di solito ripartono i chip.<br/><b>Sotto:</b> la vendita di questa settimana può proseguire."),
        ("Mer 18, 20:00", "Verbali della riunione Fed del 27-28 ottobre", "voti contrari: 2 (Cook, Hammack)", "Quanto era vicino il rialzo",
         "<b>Ascolta:</b> se molti volevano alzare, di solito sale il 2 anni; se parlano di attesa, scende."),
    ],
    "moduli": [
        {"chiave": "nvidia", "tema": "Chip", "breve": "i conti senza Huang",
         "titolo": "Per Nvidia conta più la previsione che i conti già quasi noti",
         "misura": "doppio",
         "grafico": {"tipo": "barre", "file": "c_nvidia_mosse.png",
                     "dati": [("Distanza tra consenso e guida", 1.4), ("Media dei movimenti dopo i conti", 7.8),
                              ("Movimento prezzato dalle opzioni", 9.0)],
                     "titolo": "Le opzioni prezzano una mossa sei volte più grande dello scarto sui ricavi",
                     "sottotitolo": "% (scarto consenso-guida; media di dieci anni; mossa implicita)", "unita": "%", "dec": 1,
                     "ordina": False, "soggetto": "conti", "ruolo": "quanto"},
         "grafico2": {"tipo": "barre", "file": "c_settori.png", "dati": SETTORI,
                      "titolo": "Venerdì la vendita ha colpito la tecnologia e l'industria, non tutta la borsa",
                      "sottotitolo": "Variazione media dei titoli USA quotati al NYSE, 13/11 (%)", "unita": "%", "dec": 1,
                      "ordina": False, "soggetto": "Nvidia", "ruolo": "chi"},
         "righe": [["Terzo trimestre", "Guida Nvidia", "Consenso"],
                   ["Ricavi (mld $)", "108, più o meno 2%", "109,5"],
                   ["Utile per azione ($)", "-", "2,47"],
                   ["Ricavi da data center in Cina", "esclusi", "-"]],
         "larghezze": [60, 60, 40], "ruolo_righe": "perche",
         "perche": "Un conto già quasi noto non basta a muovere un titolo che ha perso il 13% in una settimana: per MarketPulse conta più la previsione del quarto trimestre. In più c'è l'incognita di chi guida: il consiglio ha aperto un'indagine sulle accuse a Huang e la società ha un amministratore delegato ad interim (Yahoo Finance).",
         "numero": "+1,4%: di tanto i ricavi attesi superano la guida. Il tetto della forchetta dell'azienda è 110,2 mld $: oltre, Nvidia batte anche l'obiettivo più alto che si era data.",
         "quindi": "Martedì alle 23:00, ora di Roma, la previsione del trimestre dice se questi ricavi sono un punto di arrivo o di partenza.",
         "punti": ["<b>I concorrenti.</b> Venerdì AMD ha perso il 9%, Broadcom e Marvell quasi il 5% e l'ETF dei semiconduttori quasi il 4%: la vendita non riguarda solo Nvidia (Yahoo Finance)."],
         "testo": ["Perché un trimestre quasi noto sposta tanto un titolo? Chi compra Nvidia paga oggi gli utili dei prossimi anni, non quelli già incassati. I conti del terzo trimestre fotografano il passato. L'azienda aveva già detto più o meno cosa aspettarsi. La previsione per il trimestre dopo invece cambia i conti di chi guarda avanti, ed è quella, di solito, a muovere il prezzo il giorno dopo.",
                   "Il peso di Nvidia amplifica la reazione. S&P 500 e Nasdaq sono pesati per capitalizzazione: quando uno dei titoli più grandi cala molto, di solito trascina l'indice anche se molti altri salgono. Venerdì i titoli tecnologici hanno ceduto in media più del 2% mentre sanità e comunicazioni salivano: l'S&amp;P 500 ha perso solo lo 0,4%.",
                   "Martedì parla per la prima volta chi ha sostituito Huang, la direttrice finanziaria Colette Kress. La guida esclude i ricavi da data center in Cina: per noi un dollaro in più da quel mercato sarebbe una sorpresa."],
         "fonte": "Fonti: Investopedia, Yahoo Finance, MarketPulse, comunicato Nvidia, deposito SEC (autorità di Borsa USA); dati settoriali FMP.",
         "guardare": "Se la previsione supera ciò che gli analisti attendono per il trimestre in arrivo, la vendita della settimana scorsa era un eccesso; se è sotto, il calo era solo l'inizio."},
        {"chiave": "tassi", "tema": "Fed e tassi", "breve": "il 2 anni sopra la Fed",
         "titolo": "Il 2 anni sta sopra i tassi Fed: il mercato attende più rialzi",
         "misura": "doppio",
         "grafico": {"tipo": "barre", "file": "c_curva_sett.png",
                     "dati": [(k, round((UST_13[k] - UST_6[k]) * 100)) for k in UST_13],
                     "titolo": "In una settimana salgono tutte le scadenze, di più quelle brevi",
                     "sottotitolo": "Curva Treasury, variazione 6-13/11 (pb)", "unita": " pb", "dec": 0, "ordina": False,
                     "soggetto": "tassi", "ruolo": "quanto"},
         "grafico2": {"tipo": "linee", "file": "c_due_anni.png", "x": [d(a) for a, _ in DUE_ANNI], "soggetto": "Fed",
                      "titolo": "Il 2 anni torna al massimo del mese rispetto ai tassi della Fed",
                      "sottotitolo": "Rendimento a 2 anni meno il limite alto dei tassi Fed, ultimo mese (pb)", "ruolo": "storia",
                      "serie": [("2 anni meno tetto Fed", [round((b - 4.00) * 100) for _, b in DUE_ANNI], "#F26B1D")],
                      "eventi": [(d("11-10"), "CPI")],
                      "note": [(d("11-05"), 46, "5/11"), (d("11-13"), 88, "13/11")]},
         "numero": "+42 pb: di tanto il divario cresce in cinque sedute, dal minimo del 5 novembre. Il giorno dei prezzi al consumo ne ha dati 17.",
         "perche": "Il CPI (prezzi al consumo) core (senza cibo ed energia) di ottobre è risultato a +0,3% contro +0,2% atteso. Waller ha detto che, a quel livello, un rialzo da mezzo punto andrebbe considerato (investingLive). Venerdì i prezzi alla produzione hanno confermato la direzione: +0,5% sul mese senza le voci più volatili, +4,9% su un anno (BLS).",
         "quindi": "Mercoledì alle 20:00 i verbali dicono quanti erano pronti ad alzare già a ottobre: due lo hanno chiesto, Cook e Hammack (Fed).",
         "testo": ["Perché guardare il 2 anni e non il 10? Chi presta al governo americano per due anni si chiede soprattutto dove saranno i tassi della Fed in quel periodo: se li aspetta più alti, pretende subito un interesse più alto. Per questo di solito il 2 anni segue la banca centrale più da vicino del 10 anni, che dipende anche da crescita e inflazione di lungo periodo. I tassi della Fed oggi stanno tra 3,75% e 4,00%: un 2 anni sopra il limite alto vuol dire che il mercato conta su altri rialzi, e per noi non solo su quello di dicembre.",
                   "Il CPI ha cambiato la scala delle scommesse. Quando un dato di inflazione esce sopra le attese, di solito salgono le probabilità di un rialzo e i rendimenti a breve. Il 10 novembre quelle su un rialzo da mezzo punto a dicembre erano tra il 10% e il 15% (Finimize). Giovedì, dopo un 2 anni salito di 14 punti base, Libella scrive che gli operatori propendono per il mezzo punto.",
                   "La Fed ha già alzato di un quarto di punto a settembre e ha lasciato fermi i tassi a ottobre con due voti contrari, favorevoli a un nuovo rialzo. Dalla riunione dell'8-9 dicembre si aspettano un'altra decisione, e fino ad allora ogni dato, dal lavoro ai consumi, sposta il prezzo.",
                   "Per l'Europa conta il dollaro: tassi americani più alti di solito lo sostengono, e l'euro ha perso l'1,1% in una settimana. Conta anche per le famiglie americane. I mutui di solito seguono il 10 anni più dei tassi della Fed, e il 10 anni è salito anche lui: comprare casa costa di più già prima di dicembre."],
         "guardare": "Se i verbali descrivono un comitato pronto a rialzare, il 2 anni resta vicino al massimo del mese; se parlano di cautela, il divario si restringe in fretta."},
        {"chiave": "oro", "tema": "Materie prime", "breve": "oro ai minimi da 13 mesi",
         "titolo": "L'oro cade con i tassi in salita e la guerra in Iran non lo difende",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_oro.png", "x": [d(a) for a, _ in ORO], "soggetto": "oro",
                     "serie": [("Oro future", [v for _, v in ORO], "#F26B1D")], "ruolo": "storia",
                     "titolo": "L'oro chiude la settimana al minimo da 13 mesi",
                     "sottotitolo": "Oro future, chiusure ($ l'oncia)", "soglie": [(4000, "4.000 $")],
                     "note": [(d("10-16"), 4181.1, "16/10"), (d("11-13"), 3886.3, "13/11")]},
         "numero": "+27 pb: di tanto sale il rendimento a 10 anni nelle quattro sedute in cui l'oro perde il 5,5%.",
         "perche": "Con una Fed più dura il rendimento reale, quello che resta dopo l'inflazione, di solito sale. Il Treasury a 10 anni protetto dall'inflazione (TIPS) rendeva il 2,66% il 9 novembre contro l'1,84% di un anno prima (24/7 Wall St.). L'oro, che non paga interessi, perde quindi attrattiva. Martedì, dopo le parole di Waller, ha ceduto con rendimenti e dollaro in rialzo (investingLive).",
         "quindi": "Mercoledì alle 20:00 i verbali Fed: se confermano un comitato pronto ad alzare, di solito l'oro resta sotto pressione.",
         "testo": ["L'oro è un bene senza cedola: chi lo compra non incassa nulla mentre aspetta. Quando i rendimenti dei titoli di Stato, depurati dall'inflazione, salgono, tenerlo costa di più rispetto a prestare soldi al Tesoro, e di solito il prezzo scende. Il contrario accade quando i rendimenti reali calano.",
                   "L'oro è anche il bene che si compra quando cresce la paura, e questa settimana di paura ce n'era, tra l'Iran e i chip. Per noi i due motivi spingono in direzioni opposte e per ora vince quello dei tassi: da lunedì il prezzo cede il 5,5% mentre la borsa sale nella settimana."],
         "fonte": "Fonti: investingLive, 24/7 Wall St., Yahoo Finance; prezzi del future (FMP).",
         "guardare": "Un rimbalzo dell'oro con i rendimenti ancora alti direbbe che torna a pesare il rifugio. Un'altra seduta sotto i 3.900 $ con il 10 anni oltre il 5,10% confermerebbe la lettura dei tassi."},
        {"chiave": "petrolio", "tema": "Petrolio", "breve": "il greggio ha già scontato la pace",
         "titolo": "Il petrolio aveva già incassato la fine della guerra: Trump ne restituisce solo una parte",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_brent.png", "x": [d(a) for a, _ in BRENT], "soggetto": "petrolio",
                     "serie": [("Brent", [v for _, v in BRENT], "#F26B1D")], "ruolo": "storia",
                     "titolo": "Il Brent ha perso il 18% in tre settimane",
                     "sottotitolo": "Brent future, chiusure ($)", "soglie": [(100, "100 $")],
                     "note": [(d("10-23"), 116.72, "23/10"), (d("11-04"), 94.62, "4/11"), (d("11-13"), 95.84, "13/11")]},
         "numero": "+4,8%: il recupero del Brent dal minimo di martedì 10 novembre; nella settimana resta in calo del 2,5%.",
         "perche": "Secondo OilPrice.com la discesa è partita il 4 novembre. Dopo le elezioni di metà mandato la Casa Bianca ha legato la sconfitta alla guerra e il mercato ha puntato sulla sua fine. In un giorno il Brent ha perso l'8,6%.",
         "quindi": "Mercoledì il rapporto settimanale dell'EIA (agenzia americana dell'energia) sulle scorte USA è il primo dato fisico dopo le accuse iraniane sulle mine.",
         "testo": ["Perché il Brent non risale se Trump dice che l'accordo non serve? Il prezzo guarda a quanto greggio arriva davvero sul mercato, non alle parole. Finché Hormuz è attraversato e il blocco americano riguarda solo i barili iraniani, un'altra frase non toglie barili. Giovedì il Brent è salito del 3,3% (Libella) ma resta sotto la media delle ultime 50 sedute, 103,89 $.",
                   "Un barile che passa da 116 a 96 dollari toglie benzina all'inflazione dei prossimi mesi. Di solito il greggio arriva nei prezzi dei carburanti in poche settimane, ed è il canale più veloce verso l'inflazione complessiva."],
         "fonte": "Fonti: OilPrice.com, NBC News, Libella, FinanceFeeds; prezzi del future e media a 50 giorni (FMP).",
         "guardare": "Danni confermati alle navi riporterebbero il Brent verso i 98 $ (FinanceFeeds); nessuna conferma e un'altra settimana di offerta abbondante lo riporterebbero verso i 91 $."},
    ],
    "scommessa": {"tesi": "Con noi: tassi e dollaro restano forti, la borsa regge se Nvidia non delude. Contro: un dato sui consumi molto sotto le attese. Da qui a venerdì: i conti di Nvidia martedì, i verbali della Fed mercoledì.",
                  "lunedi": True, "venerdi": False, "settimana_prec": "9-13 novembre",
                  "com_e_andata": "La direzione è stata quella giusta quasi ovunque, ma il Treasury ha deluso: i rendimenti sono saliti dopo i prezzi al consumo, mentre noi ne aspettavamo il calo."},
    "parole": [("Rendimento a 2 anni", "L'interesse che chiede chi presta al governo americano per due anni: di solito segue le attese sui tassi della Fed."),
               ("Previsione dell'azienda", "Ciò che una società dice di aspettarsi per i prossimi trimestri: di solito muove il titolo più dei conti passati."),
               ("Tasso reale", "Il rendimento di un titolo di Stato dopo aver tolto l'inflazione: quando sale, l'oro perde attrattiva."),
               ("Consenso", "La media delle stime degli analisti: i mercati reagiscono alla distanza tra dato e consenso."),
               ("Opzioni", "Contratti che permettono di comprare o vendere a un prezzo fissato: dai loro prezzi si ricava il movimento atteso."),
               ("Verbali della Fed", "Il resoconto della riunione del comitato che decide i tassi: mostra chi voleva cosa.")],
    "fonti": [
        ("Dati di mercato", "Financial Modeling Prep (indici USA e Asia, VIX, Brent e oro future, curva par del Tesoro USA, settori); "
                            "Alpha Vantage (EUR/USD, ACWI); dpa-AFX (Euro Stoxx 50); ANSA (FTSE MIB); Euronews (Asia)."),
        ("Prima pagina e mercati", "Yahoo Finance (Investopedia), Euronews, HNGN (Reuters), FinanceFeeds, Libella, dpa-AFX, BLS, "
                                   "Federal Reserve, investingLive."),
        ("Calendario e agenda", "Kiplinger, BNN Bloomberg, New York Fed, comunicato Nvidia."),
        ("Approfondimenti", "Nvidia: Yahoo Finance (Investopedia), MarketPulse, SEC. Tassi: BLS, Federal Reserve, Finimize, investingLive, "
                            "curva par del Tesoro via FMP. Oro: investingLive, 24/7 Wall St., Yahoo Finance. Petrolio: OilPrice.com, "
                            "NBC News, Libella, FinanceFeeds."),
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
