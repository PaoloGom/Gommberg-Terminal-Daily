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
OGGI = dt.date(2026, 11, 20)
NOTA_DATI = "Chiusure al 19 novembre; Asia e mercati europei di stamattina dove indicato"
REG = "2026-11-16-settimana.json"          # registro della scommessa (redazione/pronostici/)

from numeri import fmt, var  # noqa: E402

# ============================ DATI DEI GRAFICI (verificati) ============================
BRENT = [("10-20", 108.79), ("10-21", 108.82), ("10-22", 113.17), ("10-23", 116.72), ("10-26", 115.81), ("10-27", 113.88),
         ("10-28", 115.32), ("10-29", 110.80), ("10-30", 113.43), ("11-02", 104.77), ("11-03", 103.60), ("11-04", 94.62),
         ("11-05", 98.29), ("11-06", 98.32), ("11-09", 92.57), ("11-10", 91.49), ("11-11", 92.76), ("11-12", 95.82),
         ("11-13", 95.84), ("11-16", 92.44), ("11-17", 93.14), ("11-18", 91.95), ("11-19", 91.98)]
ORO = [("10-20", 4142.6), ("10-21", 4150.0), ("10-22", 4060.4), ("10-23", 4007.9), ("10-26", 4038.4), ("10-27", 4074.6),
       ("10-28", 4051.6), ("10-29", 4031.4), ("10-30", 3898.9), ("11-02", 3969.6), ("11-03", 3940.4), ("11-04", 4073.0),
       ("11-05", 4113.5), ("11-06", 4074.9), ("11-09", 4114.5), ("11-10", 4030.2), ("11-11", 4000.5), ("11-12", 3885.3),
       ("11-13", 3886.3), ("11-16", 3853.0), ("11-17", 3864.2), ("11-18", 3741.9), ("11-19", 3685.5)]
SP = [("11-06", 7376.86), ("11-09", 7549.94), ("11-10", 7520.93), ("11-11", 7619.38), ("11-12", 7592.40), ("11-13", 7561.67),
      ("11-16", 7416.59), ("11-17", 7340.53), ("11-18", 7323.63), ("11-19", 7175.83)]
MOSSE = [("Dow Jones", -2.19), ("S&P 500", -2.02), ("Nasdaq Comp.", -2.25), ("Euro Stoxx 50", -0.55),
         ("Hong Kong*", -2.1), ("Nikkei 225", -5.06), ("Kospi*", -5.2)]
d = lambda s: dt.date(2026, int(s[:2]), int(s[3:]))   # "MM-GG" -> data

C = {
    "data": OGGI,
    "temi": ["Tecnologia", "Fed", "Petrolio", "Europa", "Materie prime", "Asia"],
    "glossario": ["VIX", "ACWI", "PCE", "IPO", "AIE"],
    "meccanismi": ["M17", "M20", "M23", "M10"],

    "ticker": ticker_da_dati("dati.json"),

    "top": {
        "tema": "Tecnologia",
        "titolo": "Il debutto record di Anthropic non ferma la vendita dell'AI: Asia a picco",
        "dek": "Anthropic chiude il primo giorno in rialzo del 17%, ma il Nasdaq perde il 2,25% e l'S&amp;P 500 il 2,0%, "
               "la sesta perdita di fila. Stamattina il conto arriva in Asia: il Nikkei cede il 5,1% e il Kospi il 5,2%, "
               "con i produttori di chip in testa. Per noi pesa più la Fed, che si prepara ad alzare i tassi, che il "
               "giudizio sulle singole società: gli utili lontani valgono meno quando il denaro costa di più. [[ai]]",
        "freccia": "Per gli operatori sentiti dal Sole 24 Ore, l'offerta da record ha sottratto liquidità agli altri titoli del settore.",
    },
    "quadro": "Per noi si vende ciò che vive di utili lontani o non paga interessi. L'AI e l'oro scendono insieme e il dollaro "
              "resta vicino ai massimi da 19 mesi. Il rendimento del Treasury a 10 anni (5,04%) cala poco: per noi, perché la Fed "
              "si prepara ad alzare. Il petrolio non fa da rifugio: il Brent (91,98 $) guarda all'eccesso di offerta.",
    "in30": [
        "La Fed ha meno spazio per fermarsi: i dati di ieri frenano l'attività e spingono i prezzi. [[fed]]",
        "Missili su Riyadh e mine a Hormuz, ma il petrolio guarda all'eccesso di offerta. [[petrolio]]",
        "L'Europa perde meno di Wall Street: ha pochi titoli AI, ma i difensivi cedono. [[europa]]",
    ],
    "in30_temi": ["Fed", "Petrolio", "Europa"],
    "stamattina": [
        "Kospi -5,2% e Hong Kong -2,1% alle 08:13; Tokyo ha chiuso a -5,06%",
        "Treasury 10 anni in Asia alle 07:40: 5,0%",
        "EUR/USD alle 09:02: 1,0986",
        "Future Euro Stoxx 50 alle 08:47: -1,43% (Borsa&amp;Finanza)",
    ],
    "notizie": [
        {"tag": "Trimestrali", "titolo": "Saipem sale del 4,7% dopo i conti dei nove mesi",
         "testo": "Ricavi e margini crescono e le previsioni di fine anno sono confermate: è il titolo migliore del FTSE MIB, "
                  "mentre Nexi cede il 3,2%.", "rimando": "europa"},
        {"tag": "Europa", "titolo": "Novartis cede il 3,2% sugli obiettivi di vendita, Sanofi il 2,9%",
         "testo": "Per Novartis pesa un obiettivo di vendite a medio termine nella parte bassa della forchetta (Reuters). Sanofi "
                  "paga il presunto interesse verso la biotech americana Insmed, secondo Bloomberg.", "rimando": "europa"},
        {"tag": "Banche", "titolo": "UniCredit e il governo tedesco si accordano sui nodi dell'offerta per Commerzbank",
         "testo": "Commerzbank cede l'1,2% in borsa (Reuters)."},
        {"tag": "Geopolitica", "titolo": "Trump, Xi e Putin firmano a Shenzhen una dichiarazione senza impegni",
         "testo": "Ribadisce che una guerra nucleare non va combattuta, ma non cita né l'Ucraina né l'Iran e non fissa "
                  "scadenze (Reuters)."},
        {"tag": "Macro", "titolo": "Il Philly Fed cala a 6,3 e le imprese pagano di più",
         "testo": "L'indice della manifattura di Filadelfia scende da 20,9 a 6,3, mentre i prezzi pagati salgono a 58,2 da "
                  "43,2 (investingLive). I sussidi di disoccupazione salgono a 203 mila, sopra i 197 mila attesi.", "rimando": "fed"},
        {"tag": "Chip", "titolo": "AMD perde il 7,7% dopo un rapporto ribassista sulla Cina",
         "testo": "Il rapporto di Hunterbrook Capital punta sulla dipendenza della società dal mercato cinese; il titolo "
                  "chiude a 489,19 $ (Milano Finanza).", "rimando": "ai"},
    ],

    # ---------- Pag. 5: mercati e agenda ----------
    "mercati_titolo": "Numeri, temi aperti e calendario",
    "cruscotto": [
        ("Mondo e Stati Uniti", [["MSCI ACWI (ETF, $)", "147,74", "19/11", "-2,0%", "-", "-"],
                                 ["S&amp;P 500", "7.175,83", "19/11", "-2,0%", "-5,1%", "+4,8%"],
                                 ["Nasdaq Comp.", "23.879,20", "19/11", "-2,3%", "-5,0%", "+2,7%"],
                                 ["Russell 2000", "2.655,11", "19/11", "-2,2%", "-4,9%", "+7,0%"]]),
        ("Europa", [["Euro Stoxx 50", "6.120,30", "19/11", "-0,6%", "-4,2%", "-"],
                    ["FTSE MIB", "49.941", "19/11", "-0,5%", "-3,6%", "+11,1%"]]),
        ("Asia (20/11)", [["Nikkei 225", "56.436,65", "20/11", "-5,1%", "-7,7%", "+12,1%"],
                          ["Hang Seng*", "-", "20/11", "-2,1%", "-", "-"],
                          ["Kospi*", "-", "20/11", "-5,2%", "-", "-"]]),
    ],
    "cruscotto_nota": "1 g = chiusura su chiusura; 1 sett. = su venerdì 13/11; da inizio anno = su chiusura 2025. "
                      "* Asia: dato di stamattina (Hong Kong e Seul alle 08:13). - = non disponibile.",
    "cross_data": "Livello 19/11",
    "cross": [
        ("Tassi", [["Treasury 2 anni", "4,76%", "-4 pb", "-12 pb", "-3 pb", "-"],
                   ["Treasury 10 anni", "5,04%", "-3 pb", "-11 pb", "-8 pb", "-"],
                   ["Spread Italia", "106 pb", "0 pb", "-", "-", "10 anni italiano al 4,47% (Teleborsa)"]]),
        ("Cambi", [["EUR/USD", "1,0966", "-0,1%", "-0,5%", "-2,4%", "-"]]),
        ("Materie prime", [["Brent future", "91,98 $", "0,0%", "-4,0%", "-15,5%", "-"],
                           ["Oro (future, $/oncia)", "3.685,50", "-1,5%", "-5,2%", "-11,0%", "-"]]),
        ("Volatilità", [["VIX (volatilità attesa)", "28,44", "+3,88", "+9,14", "-", "Il più alto delle ultime due settimane"]]),
    ],
    "cross_nota": "1 mese = sul 20/10. VIX = volatilità attesa sull'S&amp;P 500.",
    "termometri": [
        ("Fed e tassi", "Decisione a dicembre", "Waller apre al rialzo da mezzo punto", "fermo: Treasury a 10 anni, sopra il 5%", "Dati sui prezzi di mercoledì"),
        ("AI e borsa", "Anthropic ha debuttato ieri", "ANT sale del 17% ma poi cede dopo la chiusura", "giu: Titoli AI e chip, Asia in testa", "Apertura di Wall Street alle 15:30"),
        ("Oro e dollaro", "Oro verso i 3.500 $", "In calo da oltre una settimana", "giu: Oro", "Dollaro e rendimenti USA"),
        ("Petrolio", "Brent sotto i 92 $", "Houthi su Riyadh, il prezzo non sale", "fermo: Brent, senza direzione", "Scorte USA e Hormuz"),
    ],
    "fermi": "Sanità USA (proposta CMS aperta ai commenti, nessuna novità verificata oggi), Tassi della Bce (prossima riunione il 17 dicembre).",
    "lettura": "Il Russell 2000, l'indice delle società più piccole, perde quanto l'S&amp;P 500: non è la solita vendita che "
               "colpisce di più chi ha più debiti e soffre i tassi alti, ma una vendita che riguarda tutti. Il VIX (la volatilità "
               "attesa a Wall Street) sale di quasi 4 punti in un giorno.",

    "ieri": [
        ("Gio 19, 14:30", "Philly Fed e sussidi di disoccupazione USA", "Philly Fed 6,3 (prima 20,9); sussidi 203 mila (attesi 197 mila)", "+", "[[fed]]"),
        ("Gio 19", "Debutto di Anthropic al Nasdaq", "ANT chiude a 97,17 $, +17,1% sul prezzo di collocamento (83 $)", "", "[[ai]]"),
    ],
    "agenda": [
        ("<b>Ven 20, 16:00</b>", "<b>Fiducia dei consumatori Michigan (finale di novembre)</b>", "<b>Prima 51,0 (stima preliminare)</b>",
         "<b>Evento n.1:</b> dice se le attese d'inflazione restano alte",
         "<b>Sopra:</b> consumatori più fiduciosi, di solito rendimenti su.<br/><b>Sotto:</b> più cautela, la Fed ha meno spinta a rialzare."),
        ("Mer 25, 14:30", "PCE core USA (ottobre, la misura d'inflazione preferita dalla Fed)", "+0,3% sul mese, +3,2% su un anno; prima +3,1%",
         "Prezzi che la Fed guarda di più",
         "<b>Sopra:</b> di solito più peso a un rialzo da mezzo punto.<br/><b>Sotto:</b> il rialzo da un quarto di punto resta il caso base."),
        ("Mer 25, 14:30", "Pil USA del terzo trimestre (seconda stima)", "+3,4% annualizzato", "Crescita dell'economia",
         "<b>Sopra:</b> economia forte, spazio per tassi alti.<br/><b>Sotto:</b> torna il timore di una frenata."),
        ("Gio 26", "Festa del Ringraziamento: borse USA chiuse", "-", "Volumi più bassi sui mercati",
         "Di solito meno scambi e prezzi più mossi su dollaro e petrolio."),
    ],

    # ---------- Pag. 2-4 ----------
    "moduli": [
        {"chiave": "ai", "tema": "Tecnologia", "breve": "Anthropic sale, l'AI scende",
         "titolo": "Anthropic guadagna il 17%, ma il resto dell'AI paga il conto",
         "misura": "doppio",
         "grafico": {"tipo": "barre", "file": "c_mosse.png", "dati": MOSSE, "ordina": False, "dec": 1,
                     "soggetto": "AI", "ruolo": "quanto", "unita": "%",
                     "titolo": "La vendita pesa di più dove i chip contano di più",
                     "sottotitolo": "variazioni %: Stati Uniti ed Europa il 19/11, Asia stamattina*"},
         "grafico2": {"tipo": "linee", "file": "c_sp.png", "x": [d(x) for x, _ in SP],
                      "serie": [("S&P 500", [v for _, v in SP], "#111111")], "soggetto": "AI", "ruolo": "storia",
                      "titolo": "Sei sedute di calo cancellano il 5,8% dal massimo dell'11 novembre",
                      "sottotitolo": "S&amp;P 500, chiusure (punti)",
                      "note": [(d("11-11"), 7619.38, "11/11"), (d("11-19"), 7175.83, "19/11")]},
         "righe": [["Titolo", "Giovedì 19", "Cosa pesa"],
                   ["Anthropic (ANT)", "+17,1% a 97,17 $", "Aperta a 111,50 $, ha poi ceduto circa il 5% dopo la chiusura (Il Sole 24 Ore)"],
                   ["AMD", "-7,7% a 489,19 $", "Rapporto ribassista di Hunterbrook sulla dipendenza dalla Cina"],
                   ["Nvidia", "Conti del 17/11 oltre le stime", "Ricavi 115,8 mld $ (+103%); Huang lascia"],
                   ["Mercato USA", "Oltre il 90% dei titoli in calo", "Sesta seduta negativa di fila"]],
         "larghezze": [34, 38, 100], "ruolo_righe": "chi",
         "perche": "Per noi il costo del denaro conta più del successo della singola società. Con la Fed pronta ad alzare i "
                   "tassi, chi paga oggi utili attesi tra molti anni li sconta di più. A questo si somma un fatto tecnico: per "
                   "gli operatori sentiti dal Sole 24 Ore l'offerta da 81 miliardi ha sottratto liquidità agli altri titoli del "
                   "settore.",
         "quindi": "Alle 15:30 apre Wall Street: i future del Nasdaq perdono oltre l'1% (Milano Finanza, 07:40), segno che la "
                   "vendita non è finita.",
         "numero": "111,50 $: il prezzo a cui ANT ha aperto, il 34% sopra il collocamento. Ha chiuso a 97,17 $: in giornata "
                   "ha restituito metà del guadagno.",
         "testo": ["Perché un debutto riuscito non aiuta? Un'azione vale oggi gli utili che si spera di incassare in futuro. "
                   "Se i tassi salgono, quegli utili lontani valgono meno, e chi compra deve pagare meno: è come un mutuo più "
                   "caro, che riduce la casa che ci si può permettere. Le azioni dell'AI sono di solito le più esposte, perché gran "
                   "parte del loro valore sta negli anni a venire. Il rialzo che la Fed prepara per dicembre colpisce "
                   "proprio loro.",
                   "Il secondo anello è la liquidità. Una società che raccoglie 81,3 miliardi di dollari in un colpo costringe i fondi a trovare quei soldi: di solito li prendono vendendo altri titoli già in portafoglio. Per gli operatori sentiti dal Sole 24 Ore è quello che è successo, ma è una "
                   "lettura da verificare: la pressione dovrebbe calare una volta chiusa la fase di collocamento.",
                   "Le cause singole non mancano. AMD paga un rapporto ribassista e Nvidia l'uscita di Jensen Huang (Milano "
                   "Finanza). Le borse globali vanno verso la più lunga serie negativa degli ultimi tre anni.",
                   "L'Asia ha ereditato tutto con un effetto amplificato. A Tokyo, Seul e Taipei pochi produttori di chip "
                   "pesano molto sull'indice, e di solito ne seguono la sera prima. Advantest cede il 10%, Tokyo Electron e "
                   "Samsung Electronics il 7% (Il Sole 24 Ore): per questo Nikkei e Kospi perdono più del doppio del Nasdaq."],
         "fonte": "Fonti: AP, investingLive, Il Sole 24 Ore, Milano Finanza.",
         "guardare": "Lo dirà l'apertura di Wall Street: se i chip americani recuperano mentre l'Asia è ancora in calo, la "
                     "vendita era un eccesso dettato dall'orario. Se scendono ancora, perde peso l'idea che sia solo "
                     "liquidità e prevale quella dei tassi."},
        {"chiave": "fed", "tema": "Fed", "breve": "meno crescita, più prezzi",
         "titolo": "I dati di ieri danno alla Fed meno crescita e più prezzi",
         "misura": "mezzo",
         "righe": [["Dato di giovedì 19", "Uscito", "Confronto"],
                   ["Philly Fed (manifattura)", "6,3", "prima 20,9"],
                   ["Prezzi pagati dalle imprese", "58,2", "prima 43,2"],
                   ["Sussidi di disoccupazione", "203 mila", "attesi 197 mila"]],
         "larghezze": [70, 40, 50], "ruolo_righe": "quanto",
         "perche": "I prezzi pagati dalle imprese di Filadelfia salgono mentre l'indice generale crolla: per noi i costi aumentano anche se l'attività frena.",
         "quindi": "Mercoledì 25 esce l'indice dei prezzi che la Fed preferisce (PCE): un dato sopra le attese darebbe forza "
                   "al rialzo da mezzo punto di cui parla Waller.",
         "testo": ["Perché i prezzi pagati contano? Sono il primo anello della catena: se le imprese pagano di più materie e "
                   "servizi, di solito prima o poi lo scaricano sui prezzi al consumo. A Filadelfia il costo sale mentre l'attività delle fabbriche cala: una combinazione scomoda. La Fed vuole frenare l'inflazione con tassi più "
                   "alti, ma tassi più alti pesano su un'economia che già rallenta.",
                   "Per questo il mercato ascolta Waller, che dopo i verbali ha indicato la possibilità di un rialzo da mezzo "
                   "punto a dicembre (Milano Finanza). Il rendimento del Treasury a 10 anni, intanto, non sale: per noi si "
                   "comprano titoli di Stato perché la borsa fa più paura dell'inflazione.",
                   "I sussidi di disoccupazione salgono a 203 mila, appena sopra i 197 mila attesi, non cambiano il quadro. Per noi il lavoro resta il lato dell'economia che tiene. La Fed può quindi guardare soprattutto ai prezzi."],
         "fonte": "Fonti: investingLive, Milano Finanza."},
        {"chiave": "petrolio", "tema": "Petrolio", "breve": "Houthi su Riyadh, Brent fermo",
         "titolo": "Houthi su Riyadh e mine a Hormuz, ma il petrolio guarda all'eccesso di offerta",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_brent.png", "x": [d(x) for x, _ in BRENT], "soggetto": "petrolio",
                     "serie": [("Brent", [v for _, v in BRENT], "#F26B1D")], "ruolo": "storia",
                     "titolo": "Il Brent perde un quinto dal massimo del 23 ottobre",
                     "sottotitolo": "Brent future, chiusure ($)", "soglie": [(100, "100 $")],
                     "note": [(d("10-23"), 116.72, "23/10"), (d("11-19"), 91.98, "19/11")]},
         "perche": "Il mercato pesa più i barili in arrivo di quelli a rischio. Le scorte USA salgono e si attende un eccesso di offerta globale (investingLive). Per l'Agenzia internazionale dell'energia (AIE) l'offerta del quarto trimestre supera la domanda di 1,7 milioni "
                   "di barili al giorno (Reuters).",
         "quindi": "Una chiusura sopra i 100 $, livello che il Brent non vede dal 3 novembre, direbbe che il rischio Hormuz ha battuto l'eccesso di offerta.",
         "numero": "3 novembre: l'ultima chiusura del Brent sopra i 100 dollari (103,60). Da allora ha perso l'11%.",
         "testo": ["Perché i missili non bastano? Il prezzo del petrolio somma due forze: la paura che manchi, che lo spinge "
                   "su, e la certezza che ce ne sia troppo, che lo spinge giù. Dopo un attacco di solito il prezzo sale per "
                   "qualche ora o qualche giorno. Poi torna dove lo porta il bilancio tra produzione e consumi, a meno che i "
                   "barili non spariscano davvero.",
                   "Sul campo i segnali sono contrastanti. Le Guardie della Rivoluzione iraniane hanno detto il 16 novembre "
                   "che due petroliere sono finite su mine a Hormuz, ma Reuters non ha potuto verificarlo. Ieri gli Houthi "
                   "hanno colpito Riyadh.",
                   "C'è poi l'effetto sull'inflazione. Un barile più caro passa in fretta ai carburanti e quindi ai prezzi al "
                   "consumo, ed è per questo che la Fed guarda al greggio con attenzione. Il calo dalle punte di fine ottobre "
                   "di solito toglie pressione ai prossimi dati sui prezzi, e dà alla banca centrale una ragione in meno per "
                   "alzare più del previsto.",
                   "Per l'Europa il conto è doppio. Il greggio si paga in dollari e, con un dollaro vicino ai massimi da 19 "
                   "mesi ogni barile costa di più, anche quando il prezzo in dollari scende. L'inflazione dell'area euro è già "
                   "al 4%, con l'energia a +20,8% (BCE)."],
         "fonte": "Fonti: Reuters, investingLive; chiusure del Brent future (FMP)."},
        {"chiave": "europa", "tema": "Europa", "breve": "perde meno di Wall Street",
         "titolo": "L'Europa regge perché ha pochi titoli AI, ma i difensivi cedono",
         "misura": "mezzo",
         "righe": [["Indice, 19/11", "Chiusura", "Variazione"],
                   ["Euro Stoxx 50", "6.120,30", "-0,55%"],
                   ["STOXX 600", "638,41", "-0,88%"],
                   ["DAX", "25.464", "-1,06%"],
                   ["FTSE 100", "10.452,68", "-0,93%"]],
         "larghezze": [70, 45, 45], "ruolo_righe": "quanto",
         "perche": "Il calo europeo è guidato dai settori tranquilli, non dalla tecnologia: alimentari e bevande perdono il 2,1% "
                   "e la sanità l'1,8%, mentre ASML sale del 2,2% (Reuters).",
         "quindi": "L'apertura dirà se l'Europa recupera il ritardo: i future sull'Euro Stoxx 50 segnano -1,43% (Borsa&amp;Finanza, 08:47).",
         "testo": ["Perché l'Europa cade meno? Gli indici europei hanno pochi titoli dell'intelligenza artificiale, e la "
                   "vendita di giovedì colpiva soprattutto quelli. ASML, che fa le macchine con cui si producono i chip, ha "
                   "chiuso in rialzo.",
                   "Di solito in una giornata di paura i difensivi, come alimentari e sanità, tengono meglio degli altri "
                   "settori. Giovedì hanno perso più del mercato: per noi chi doveva fare cassa ha venduto ciò che si vende "
                   "più facilmente, non ciò che costava meno. È una lettura nostra, non confermata.",
                   "Anche su base settimanale il quadro è lo stesso: il FTSE MIB perde il 3,6% e l'Euro Stoxx 50 il 4,2%, "
                   "contro il 5,1% dell'S&amp;P 500. L'Europa soffre, ma meno, e senza il peso dei titoli dell'intelligenza "
                   "artificiale."],
         "fonte": "Fonti: Reuters, dpa-AFX, Teleborsa, ANSA, Borsa&amp;Finanza."},
        {"chiave": "oro", "tema": "Materie prime", "breve": "oro ai minimi da settembre",
         "titolo": "L'oro perde oltre 400 dollari dal 9 novembre e la Fed non aiuta",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_oro.png", "x": [d(x) for x, _ in ORO], "soggetto": "oro",
                     "serie": [("Oro", [v for _, v in ORO], "#B8860B")], "ruolo": "storia",
                     "titolo": "L'oro cade di oltre 400 dollari dal 9 novembre",
                     "sottotitolo": "Oro future, chiusure ($ l'oncia)",
                     "note": [(d("11-09"), 4114.5, "9/11"), (d("11-19"), 3685.5, "19/11")]},
         "perche": "L'oro non paga interessi. Con la Fed pronta ad alzare e il dollaro vicino ai massimi, chi lo tiene rinuncia a un rendimento più alto altrove (Milano Finanza).",
         "quindi": "Venerdì decidono dollaro e Treasury: un 10 anni sopra il 5% di solito tiene l'oro sotto pressione.",
         "numero": "3.500 $: dove l'oro è sceso stamattina, il livello più basso da settembre 2025.",
         "testo": ["Come mai l'oro, il bene rifugio per eccellenza, scende in un giorno di paura? Per noi oggi la paura è sui tassi, non sull'inflazione fuori controllo. L'oro serve a proteggersi da un denaro che perde valore. Ma se la banca centrale alza i tassi per fermare l'inflazione, il dollaro rende di più e l'oro, che non rende "
                   "nulla, diventa meno interessante.",
                   "C'è poi la vendita forzata: chi perde su un mercato di solito vende ciò che si vende subito per coprire "
                   "le perdite. Per Milano Finanza è una delle cause del calo, insieme a dollaro più forte e attese di una "
                   "stretta della Fed.",
                   "Mercoledì l'argento è sceso del 3,4% (Kitco). I metalli preziosi si muovono insieme, segno che pesa una spinta comune e non una notizia sul solo oro.",
                   "Per chi compra in euro il colpo è un po' più leggero. Dal 9 novembre l'oro perde il 10% in dollari ma l'8% in euro: per noi, perché nel frattempo l'euro è sceso contro il dollaro. Di solito un dollaro forte fa scendere l'oro in dollari più di quanto lo faccia scendere in altre valute."],
         "fonte": "Fonti: Milano Finanza, Kitco, investingLive; chiusure dell'oro future (FMP)."},
    ],

    # ---------- Pag. 6 ----------
    "scommessa": {"tesi": "Con noi: la borsa americana, l'oro e il dollaro vanno nella direzione prevista, e con più forza. "
                          "Contro: l'Europa, i Treasury e il petrolio vanno dall'altra parte. "
                          "Da qui alla chiusura: l'apertura di Wall Street.",
                  "lunedi": False, "venerdi": True, "settimana_prec": None},
    "parole": [("Liquidità", "Quanti soldi ci sono a disposizione per comprare titoli: quando una grande offerta li assorbe, "
                             "gli altri titoli di solito ne ricevono meno."),
               ("Prezzi pagati", "La quota di imprese che dice di pagare di più materie e servizi: è un'anticipazione "
                                 "dell'inflazione."),
               ("Vendita forzata", "Vendere titoli non perché si è cambiata idea, ma per coprire perdite altrove."),
               ("Titoli difensivi", "Settori come sanità e alimentari, i cui utili dipendono poco dal ciclo economico."),
               ("Eccesso di offerta", "Più barili prodotti di quanti se ne consumino: di solito spinge il prezzo giù."),
               ("Collocamento", "Il prezzo a cui una società vende le sue azioni al pubblico la prima volta.")],
    "fonti": [
        ("Dati di mercato", "Financial Modeling Prep (indici USA, Nikkei, VIX, Brent e oro future, curva par del Tesoro USA); "
                            "Alpha Vantage (EUR/USD, ACWI); finanzen.at e dpa-AFX (Euro Stoxx 50); ANSA e Teleborsa (FTSE MIB, "
                            "titoli di Stato italiani); Il Sole 24 Ore e Milano Finanza (Asia di stamattina)."),
        ("Prima pagina e mercati", "AP, Reuters, investingLive, Il Sole 24 Ore, Milano Finanza, Borsa&amp;Finanza, ANSA, Teleborsa."),
        ("Calendario e agenda", "ThriveInMarkets, HyperStocks, LiteFinance, stockanalysis.com."),
        ("Approfondimenti", "AI: AP, investingLive, Il Sole 24 Ore, Milano Finanza. Fed: investingLive, Milano Finanza. "
                            "Petrolio: Reuters, investingLive. Europa: Reuters, dpa-AFX, Teleborsa. Oro: Milano Finanza, Kitco."),
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
