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
OGGI = dt.date(2026, 11, 16)
NOTA_DATI = "Chiusure al 13 novembre per Stati Uniti ed Europa; Asia chiusa il 16 novembre"
REG = "2026-11-16-settimana.json"          # registro della scommessa (redazione/pronostici/)

# ============================ DATI DEI GRAFICI (verificati) ============================
_D = json.load(open("dati.json", encoding="utf-8"))["serie"]


def _v(nome, data):
    return next(r[1] for r in _D[nome]["ultimi"] if r[0] == data)


def _pc(a, b):
    return (a / b - 1) * 100


def _riga(nome, serie, data, base=None, dec=2, etichetta=None):
    u = _D[serie]["ultimi"]
    v0, v1 = u[0][1], u[1][1]
    wk = next((r[1] for r in u if r[0] == "2026-11-06"), None)
    f = lambda x, d=1: ("+" if round(x, d) > 0 else "") + f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".") + "%"
    lv = f"{v0:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return [etichetta or nome, lv, data, f(_pc(v0, v1)), f(_pc(v0, wk)) if wk else "n.d.", f(_pc(v0, base)) if base else "n.d."]


def _tasso(nome, serie, mese):
    u = _D[serie]["ultimi"]
    wk = next(r[1] for r in u if r[0] == "2026-11-06")
    p = lambda x: ("+" if round(x) > 0 else "") + f"{round(x):d} pb"
    return [nome, f"{u[0][1]:.2f}%".replace(".", ","), p((u[0][1] - u[1][1]) * 100), p((u[0][1] - wk) * 100), p((u[0][1] - mese) * 100)]


CURVA_6 = {"1M": 4.02, "3M": 4.19, "6M": 4.23, "1A": 4.33, "2A": 4.51, "3A": 4.59, "5A": 4.64, "7A": 4.74, "10A": 4.86, "20A": 5.29, "30A": 5.26}
CURVA_13 = {"1M": 4.10, "3M": 4.32, "6M": 4.42, "1A": 4.65, "2A": 4.88, "3A": 4.92, "5A": 4.98, "7A": 5.05, "10A": 5.15, "20A": 5.52, "30A": 5.47}
UST_G = [("11-02", 4.59, 4.91), ("11-03", 4.61, 4.95), ("11-04", 4.58, 4.90), ("11-05", 4.46, 4.84), ("11-06", 4.51, 4.86),
         ("11-09", 4.56, 4.88), ("11-10", 4.73, 4.98), ("11-12", 4.86, 5.10), ("11-13", 4.88, 5.15)]
NIKKEI = [("11-02", 63081.86), ("11-04", 62188.63), ("11-05", 61077.90), ("11-06", 57434.77), ("11-09", 58775.50),
          ("11-10", 60459.58), ("11-11", 61248.59), ("11-12", 60819.36), ("11-13", 61142.35), ("11-16", 59662.02)]
BRENT = [("11-02", 104.77), ("11-03", 103.60), ("11-04", 94.62), ("11-05", 98.29), ("11-06", 98.32), ("11-09", 92.57),
         ("11-10", 91.49), ("11-11", 92.76), ("11-12", 95.82), ("11-13", 95.84)]
ASIA = [("Taiwan (Taiex)", -6.0), ("Corea (Kospi)", -3.6), ("Giappone (Nikkei)", -2.4), ("Cina (Shanghai)", -0.9),
        ("Hong Kong (Hang Seng)", 0.5)]
SETTIMANA = [("Ftse Mib", 3.61), ("Euro Stoxx 50", 3.51), ("S&P 500", 2.51), ("Nasdaq", 2.27), ("Russell 2000", 1.32)]
ORO = [("11-02", 3969.6), ("11-03", 3940.4), ("11-04", 4073.0), ("11-05", 4113.5), ("11-06", 4074.9),
       ("11-09", 4114.5), ("11-10", 4030.2), ("11-11", 4000.5), ("11-12", 3885.3), ("11-13", 3886.3)]
d = lambda s: dt.date(2026, int(s[:2]), int(s[3:]))   # "MM-GG" -> data

C = {
    "data": OGGI,
    "temi": ["Chip", "Fed", "Tassi", "Asia", "Petrolio", "Europa"],
    "glossario": ["VIX", "ACWI"],
    "meccanismi": ["M17", "M23", "M11"],

    "ticker": ticker_da_dati("dati.json"),

    "top": {
        "tema": "Chip",
        "titolo": "I chip asiatici crollano dopo Nvidia: Taiwan perde il 6%, Seul il 3,6%",
        "dek": "Le borse asiatiche aprono la settimana con i chip sotto pressione: oltre a Taipei e Seul perde il 2,4% "
               "Tokyo, mentre Hong Kong sale dello 0,5%. Il dubbio è che la spesa in intelligenza artificiale rallenti, con "
               "l'addio di Jensen Huang a Nvidia e la notizia che potrebbe tornare. Martedì sera i conti di Nvidia diranno "
               "se il timore è fondato, e giovedì debutta in borsa Anthropic. [[chip]]",
        "freccia": "Secondo il Financial Times, un alleato di Huang prepara una «war room» di dirigenti per riportarlo al comando.",
    },
    "quadro": "Per noi la giornata dice due cose che non si contraddicono. In Asia la paura riguarda i chip e non l'economia in "
              "generale: Hong Kong sale mentre Taipei crolla. Intanto i rifugi, di solito cercati con la paura, non funzionano: "
              "i titoli di Stato e l'oro hanno perso e il dollaro è più forte. Per noi pesa di più la "
              "Fed delle borse. Il Brent, a 95,84 $, resta senza direzione.",
    "in30": [
        "La Fed parla oggi e mercoledì: dai verbali si capisce quanto è vicino il rialzo di dicembre. [[rifugi]]",
        "Giovedì a Shenzhen il primo vertice a tre tra Trump, Xi e Putin. [[agenda]]",
        "Europa e Milano chiudono la settimana migliore da aprile, mentre l'AI vacilla. [[europa]]",
    ],
    "in30_temi": ["Fed", "Geopolitica", "Europa"],
    "stamattina_titolo": "Cosa guardare all'apertura",
    "stamattina": [
        "Alle 14:30 l'indice Empire State sull'industria di New York",
        "Alle 18:00 parla Kevin Warsh, presidente della Fed",
        "Treasury a 10 anni: venerdì ha chiuso al 5,15%, sopra il 5% da mercoledì",
        "Nikkei: ha chiuso sotto i 60.000 punti, a 59.662,02",
    ],
    "notizie": [
        {"tag": "Cina", "titolo": "La Cina delude: vendite al dettaglio a +0,4% contro il +0,8% atteso",
         "testo": "Anche la produzione industriale cresce del 4,8%, sotto il 5,3% previsto, e gli investimenti fissi calano "
                  "dell'8,1% nei primi dieci mesi. Regge solo l'export, trainato dalla domanda di tecnologia per l'AI (Reuters)."},
        {"tag": "Asia", "titolo": "Il Giappone si ferma: Pil a -0,1%, primo calo in un anno",
         "testo": "I consumi privati scendono dell'1,1% annualizzato, tra maltempo e prezzi più alti, mentre gli "
                  "investimenti delle imprese crescono del 6,8% (AP).", "rimando": "petrolio"},
        {"tag": "Tecnologia", "titolo": "Anthropic fissa il prezzo tra 70 e 78 dollari e debutta giovedì al Nasdaq",
         "testo": "Può raccogliere fino a 64,4 miliardi di dollari, con un valore fino a circa 1.400 miliardi su base "
                  "diluita; il prezzo definitivo è atteso il 18 novembre."},
        {"tag": "Geopolitica", "titolo": "Trump, Xi e Putin si incontrano a Shenzhen per la prima volta",
         "testo": "La Casa Bianca ha confermato il vertice ai margini dell'Apec: sul tavolo dazi, chip e Iran, mentre "
                  "l'Ucraina, dice un funzionario USA, non sarà discussa."},
        {"tag": "Italia", "titolo": "Fincantieri cede oltre il 4% dopo i conti, Eni sale dell'1,98%",
         "testo": "Il Ftse Mib finisce venerdì a 51.859 punti (+0,1%). Eni sale dell'1,98% e Fincantieri cala di "
                  "oltre il 4%; lo spread tra Btp e Bund oscilla tra 100 e 105 punti (SoldiOnline)."},
        {"tag": "Petrolio", "titolo": "Hormuz resta chiuso e il Brent sta intorno ai 96 dollari",
         "testo": "Il petrolio è ancora molto più caro dei circa 72 $ di fine febbraio, prima della guerra in Iran. Le "
                  "ostilità su larga scala sono finite, ma il conflitto è in stallo (AP).", "rimando": "petrolio"},
    ],

    "mercati_titolo": "Numeri, temi aperti e calendario",
    "cruscotto": [
        ("Mondo e Stati Uniti", [_riga("ACWI", "ACWI", "13/11", None, 2, "MSCI ACWI (ETF, $)"),
                                 _riga("S&P 500", "S&P 500", "13/11", 6845.49, 2, "S&amp;P 500"),
                                 _riga("Nasdaq", "Nasdaq", "13/11", 23241.99, 2, "Nasdaq Comp."),
                                 _riga("Russell 2000", "Russell 2000", "13/11", 2481.91, 2)]),
        ("Europa", [_riga("Euro Stoxx 50", "Euro Stoxx 50", "13/11", 5796.22, 2),
                    _riga("FTSE MIB", "FTSE MIB", "13/11", 44944.0, 0)]),
        ("Asia (chiusure del 16/11)", [_riga("Nikkei 225", "Nikkei 225", "16/11", 50339.48, 2),
                                       _riga("Hang Seng", "Hang Seng", "16/11", 25630.55, 2),
                                       ["Kospi", "5.100,50", "16/11", "-3,6%", "+0,8%", "+21,0%"]]),
    ],
    "cruscotto_nota": "1 g = chiusura su chiusura; 1 sett. = su venerdì 6/11; da inizio anno = su chiusura 2025. "
                      "Kospi: variazione dalla chiusura di Seul del 16/11 (JoongAng Daily e AFP).",
    "cross_data": "Livello 13/11",
    "cross": [
        ("Tassi", [_tasso("Treasury 2 anni", "Treasury 2 anni", 4.79) + ["Sale con le attese sulla Fed [[rifugi]]"],
                   _tasso("Treasury 10 anni", "Treasury 10 anni", 5.21) + ["-"]]),
        ("Cambi", [["EUR/USD", "1,1021", "-0,3%", "-1,1%", "-1,6%", "-"]]),
        ("Materie prime", [["Brent future", "95,84 $", "0,0%", "-2,5%", "-9,3%", "-"],
                           ["Oro (future, $/oncia)", "3.886,30", "0,0%", "-4,6%", "-7,0%", "-"]]),
        ("Volatilità", [["VIX (volatilità attesa)", "19,30", "+0,60", "-6,34", "+4,03", "-"]]),
    ],
    "cross_nota": "1 mese = sul 13/10. VIX = volatilità attesa sull'S&amp;P 500.",
    "termometri": [
        ("AI e chip", "Conti Nvidia martedì", "Taiwan -6% alla prima seduta", "giu: Titoli dei chip asiatici", "Conti Nvidia, mar 17 alle 23:00"),
        ("Fed e tassi", "Verbali mercoledì", "Rialzo di dicembre quasi certo", "su: Rendimenti a 2 e 10 anni", "Verbali, mer 18 alle 20:00"),
        ("Dollaro e oro", "Dollaro forte, oro in calo", "Oro -4,6% in una settimana", "giu: Oro", "Tono della Fed oggi e mercoledì"),
        ("Petrolio", "Hormuz chiuso", "Brent senza direzione", "fermo: Brent intorno a 96 $", "Vertice a Shenzhen, giovedì"),
    ],
    "fermi": "",
    "lettura": "Una cosa che le tabelle dicono e la prima pagina no. Nella settimana scorsa il Russell 2000, l'indice delle "
               "piccole società americane, è salito meno degli altri (+1,3% contro +2,5% dell'S&amp;P 500): di solito "
               "chi ha più debiti sconta di più rendimenti che salgono. Il VIX (volatilità attesa sull'S&amp;P 500) "
               "è sceso da 25,64 a 19,30 nella stessa settimana: la paura di borsa si era già calmata prima della vendita "
               "asiatica di oggi. Per noi sono due letture della stessa settimana: i titoli piccoli risentono dei tassi, i "
               "grandi del dubbio sull'AI.",

    "ieri": [
        ("Lun 16, 03:00", "Cina: vendite al dettaglio e produzione industriale (ottobre)", "Vendite +0,4% annuo (atteso +0,8%); produzione +4,8% (+5,3%)", "-", ""),
        ("Lun 16, 00:50", "Giappone: Pil del terzo trimestre", "-0,1% annualizzato; attesa di crescita", "-", "[[petrolio]]"),
    ],
    "agenda": [
        ("Lun 16, 18:00", "Intervento di Kevin Warsh (Fed)", "Nessun dato: si ascolta il tono sul rialzo di dicembre",
         "Il tono del presidente, dopo Williams alle 15:05",
         "<b>Sopra:</b> un tono più duro del previsto di solito alza rendimenti e dollaro.<br/><b>Sotto:</b> un tono più cauto di solito aiuta azioni e oro."),
        ("Mar 17, 14:30", "Vendite al dettaglio USA (ottobre)", "+0,2% sul mese (core +0,4%); prima +0,8% (+0,9%)",
         "Primi consumi dopo i prezzi alti",
         "<b>Sopra:</b> di solito salgono dollaro e rendimenti a breve.<br/><b>Sotto:</b> il rialzo di dicembre perde un po' di forza."),
        ("<b>Mar 17, 23:00</b>", "<b>Conti di Nvidia</b>", "<b>Utile per azione 2,47 $; ricavi circa 108,8 mld $</b>",
         "<b>Evento n.1:</b> primi conti dopo l'addio di Huang",
         "<b>Sopra:</b> di solito i fornitori asiatici di chip recuperano in apertura.<br/><b>Sotto:</b> il timore sull'AI si allarga oltre l'Asia."),
        ("Mer 18, 20:00", "Verbali della Fed (riunione di ottobre)", "Nessun dato: si cerca quanti membri vogliono più rialzi",
         "Quanto è condiviso il rialzo di dicembre",
         "<b>Sopra:</b> più rialzi nei verbali di solito spingono su i rendimenti brevi.<br/><b>Sotto:</b> toni più cauti di solito li fanno scendere."),
    ],

    "moduli": [
        {"chiave": "chip", "tema": "Chip e Asia", "breve": "i chip asiatici cedono",
         "titolo": "Per noi Taipei e Seul cadono di più: nell'indice pesano i chip",
         "misura": "doppio",
         "grafico": {"tipo": "barre", "file": "c_asia.png", "dati": ASIA, "ordina": False, "dec": 1, "unita": "%",
                     "soggetto": "chip", "ruolo": "quanto",
                     "titolo": "La vendita colpisce Taipei e Seul e risparmia Hong Kong",
                     "sottotitolo": "variazione % delle chiusure del 16/11"},
         "grafico2": {"tipo": "linee", "file": "c_nikkei.png", "x": [d(x) for x, _ in NIKKEI],
                      "serie": [("Nikkei", [v for _, v in NIKKEI], "#111111")], "soggetto": "asiatici", "ruolo": "storia",
                      "titolo": "Il Nikkei torna sotto 60.000 dopo una risalita da 57.435",
                      "sottotitolo": "Nikkei 225, chiusure (punti)", "soglie": [(60000, "60.000")],
                      "note": [(d("11-06"), 57434.77, "6/11"), (d("11-16"), 59662.02, "16/11")]},
         "righe": [["Titolo asiatico", "16/11"],
                   ["Kioxia", "-8,0%"], ["SK Hynix", "-7,9%"], ["Tokyo Electron", "-7,1%"], ["TSMC", "-5,7%"],
                   ["Samsung Electronics", "-4,5%"], ["SoftBank", "-3,7%"]],
         "larghezze": [110, 60], "ruolo_righe": "chi",
         "perche": "I dubbi sulla spesa in intelligenza artificiale c'erano già prima del caso Huang, per gli analisti. Venerdì "
                   "hanno colpito Wall Street (AMD -8,8%, Broadcom -4,8%) e oggi arrivano ai fornitori asiatici (AP).",
         "numero": "1.384 miliardi di won: le vendite nette degli stranieri a Seul. I piccoli investitori coreani ne hanno "
                   "comprati 1.348: per noi chi è dentro da poco e chi è dentro da tempo leggono il caso in modo opposto "
                   "(Seoul Economic Daily).",
         "quindi": "Martedì sera, a Wall Street chiusa, i conti di Nvidia: il primo test è l'apertura di Taipei di mercoledì.",
         "testo": ["Come fa una notizia su un'azienda americana a far cadere una borsa asiatica? Per noi la risposta è che Taiwan e Corea hanno nei "
                   "chip una parte molto larga dell'indice. Quando i titoli dei semiconduttori americani si muovono, di solito "
                   "le loro borse li seguono, e con più forza. Il Taiex e il Kospi sono quindi i primi a pagare il dubbio che "
                   "gli ordini di Nvidia possano rallentare (AP).",
                   "Dove i chip pesano meno la vendita si ferma. Hong Kong sale e Shanghai cede lo 0,9%, ma lì a pesare sono "
                   "stati i dati di ottobre, con vendite e produzione sotto le attese (Reuters), più che la paura sull'AI.",
                   "Si aggiunge una domanda di guida. Il Financial Times scrive che Huang valuta di tornare. Un suo "
                   "alleato prepara una «war room» per convincere il consiglio, che secondo lo stesso giornale aveva già sondato "
                   "Rene Haas, capo di Arm, come successore. Per noi l'incertezza su chi guida il principale fornitore di chip "
                   "per l'AI pesa quanto i numeri.",
                   "Giovedì debutta Anthropic, che chiede fino a 64,4 miliardi di dollari e secondo Investing.com ha attirato "
                   "più interesse degli investitori istituzionali di SpaceX. Per chi investe nell'AI è un'altra occasione "
                   "dove mettere i soldi, e per noi una ragione in più per vendere i fornitori più cari."],
         "fonte": "Fonti: AP, AFP, Seoul Economic Daily, Reuters, Financial Times, Investing.com.",
         "guardare": "Se martedì sera Nvidia conferma ricavi vicini a 108,8 miliardi e previsioni in crescita, la vendita "
                     "asiatica può restare un episodio. Se le previsioni deludono, la paura sull'AI si allarga oltre l'Asia."},
        {"chiave": "rifugi", "tema": "Tassi USA", "breve": "oro e Treasury non proteggono",
         "titolo": "Borse su e rifugi giù: per noi la Fed pesa più della paura",
         "misura": "doppio",
         "grafico": {"tipo": "linee", "file": "c_ust_sett.png", "x": [d(r[0]) for r in UST_G], "soggetto": "Fed",
                     "titolo": "Il 2 anni sale più del 10 anni: la distanza scende a 27 punti base",
                     "sottotitolo": "10 anni meno 2 anni, chiusure (punti base)", "ruolo": "storia",
                     "serie": [("10 anni meno 2 anni", [round((r[2]-r[1])*100) for r in UST_G], "#111111")]},
         "grafico2": {"tipo": "linee", "file": "c_oro.png", "x": [d(x) for x, _ in ORO], "soggetto": "rifugi",
                      "serie": [("Oro future", [v for _, v in ORO], "#B8860B")], "ruolo": "quanto",
                      "titolo": "L'oro scende sotto 3.900 dollari dal massimo del 9 novembre",
                      "sottotitolo": "Oro future, chiusure ($ l'oncia)",
                      "note": [(d("11-09"), 4114.5, "9/11"), (d("11-13"), 3886.3, "13/11")]},
         "numero": "-4,6%: l'oro in una settimana, da 4.074,90 a 3.886,30 $. Il Treasury a 10 anni ha chiuso la settimana "
                   "a 5,15%: oro e titoli di Stato, i rifugi di solito cercati con la paura, hanno perso insieme.",
         "perche": "Dopo i prezzi di ottobre i future danno l'87,1% di probabilità a un rialzo Fed da un quarto di "
                   "punto a dicembre, il 12,9% a uno da mezzo punto (Kitco). Per noi la scommessa sui tassi pesa più della paura sui chip.",
         "quindi": "Se i verbali di mercoledì sono più duri del previsto, il 2 anni resta sopra il 4,88% di venerdì. Se sono "
                   "più cauti, di solito sono i rendimenti brevi a scendere per primi.",
         "testo": ["Perché la Fed muove titoli di Stato e oro in direzione opposta alla paura? Chi presta soldi allo Stato "
                   "americano per due anni guarda ai tassi della Fed: se li aspetta più alti, chiede un rendimento più alto e "
                   "il prezzo del titolo scende. L'oro non paga interessi, e quando un deposito rende di più tenerlo costa di "
                   "più, così di solito molti lo vendono.",
                   "Il segno della Fed si legge nella forma della curva. In una settimana il 2 anni è salito di 37 punti base "
                   "e il 10 anni di 29. Il breve si muove di più, per noi perché è lì che si scommette sul rialzo. Venerdì, con il "
                   "Nasdaq in calo dello 0,9%, il 10 anni è salito di altri 5. La paura sui chip non ha portato acquisti di "
                   "titoli di Stato, che di solito fanno da rifugio.",
                   "A fare il rifugio è stato il dollaro. L'euro vale 1,1021 dollari contro 1,1143 di una settimana prima, e "
                   "mercoledì l'indice del dollaro era già vicino al massimo da aprile 2025 (Kitco).",
                   "Il prossimo esame sono i verbali di mercoledì, preceduti oggi da Williams e Warsh. Waller aveva aperto a un "
                   "rialzo da mezzo punto e Logan a due da un quarto di punto (CNBC): i verbali dicono quanto questa linea sia "
                   "condivisa.",
                   "Martedì conta anche un dato sui consumi: le vendite al dettaglio USA sono attese a +0,2% sul mese, "
                   "dopo il +0,8% di settembre (FXEmpire). Per noi consumi più deboli darebbero alla Fed un motivo per "
                   "frenare, e di solito farebbero scendere prima i rendimenti brevi."],
         "fonte": "Fonti: Kitco, CNBC, curva par del Tesoro USA via FMP, FXEmpire.",
         "guardare": "Se i verbali parlano di più rialzi, il 2 anni resta alto e l'oro fatica a recuperare. Se molti "
                     "membri frenano, il mercato taglierà in fretta la scommessa sul mezzo punto e i rendimenti brevi "
                     "scenderanno per primi."},
        {"chiave": "europa", "tema": "Europa", "breve": "Europa e Milano battono Wall Street",
         "titolo": "La settimana più forte da aprile per l'Europa arriva mentre l'AI vacilla",
         "misura": "mezzo",
         "grafico": {"tipo": "barre", "file": "c_settimana.png", "dati": SETTIMANA, "ordina": False, "dec": 1, "unita": "%",
                     "soggetto": "Europa", "ruolo": "quanto",
                     "titolo": "Europa e Milano battono Wall Street nella settimana",
                     "sottotitolo": "variazione % del 6-13/11"},
         "numero": "1,3 punti: il vantaggio del Ftse Mib sul Nasdaq in cinque sedute, un margine che per noi dice "
                   "poco su un'intera stagione ma molto su questa settimana.",
         "perche": "Secondo l'analista Robert Greil (Merck Finck), le borse europee vanno meglio quando il settore dell'AI è debole. Venerdì il Ftse Mib ha chiuso a +0,1%, "
                   "l'Euro Stoxx 50 ha ceduto lo 0,19% e il Nasdaq ha perso lo 0,9%.",
         "quindi": "Oggi l'apertura mostra se la vendita asiatica pesa su Milano: giovedì 12 Technoprobe aveva perso il 4,73% con "
                   "il calo di Nvidia (ANSA).",
         "testo": ["In una settimana in cui Nvidia ha perso terreno quasi ogni giorno, le borse europee sono salite più di "
                   "quelle americane. A Milano il Ftse Mib ha chiuso vicino a 52.000 punti e l'Euro Stoxx 50 ha toccato "
                   "giovedì il massimo da fine agosto (dpa-AFX).",
                   "Non è una regola. I titoli italiani legati ai chip seguono Nvidia, come Technoprobe giovedì scorso; "
                   "venerdì Fincantieri e Generali hanno ceduto per i loro conti, non per la tecnologia (SoldiOnline).",
                   "La seduta di venerdì è stata «senza direzione» e gli scambi sono scesi a 2,66 miliardi di euro dai 3,62 "
                   "del venerdì precedente (SoldiOnline). Pochi acquisti nuovi: per noi il segno di una settimana che "
                   "aspetta i conti di Nvidia prima di scegliere."],
         "fonte": "Fonti: dpa-AFX, AWP, SoldiOnline, ANSA."},
        {"chiave": "petrolio", "tema": "Petrolio", "breve": "il petrolio caro frena il Giappone",
         "titolo": "Con Hormuz chiuso, il petrolio caro frena chi lo importa: il Giappone",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_brent.png", "x": [d(x) for x, _ in BRENT], "soggetto": "petrolio",
                     "serie": [("Brent", [v for _, v in BRENT], "#F26B1D")], "ruolo": "storia",
                     "titolo": "Il Brent risale a 96 dollari dopo il minimo del 10 novembre",
                     "sottotitolo": "Brent future, chiusure ($)", "soglie": [(100, "100 $")],
                     "note": [(d("11-10"), 91.49, "10/11"), (d("11-13"), 95.84, "13/11")]},
         "numero": "Un terzo in più: di tanto il Brent è più caro di fine febbraio, quando costava circa 72 $ prima della "
                   "guerra in Iran (AP).",
         "perche": "Il Giappone importa quasi tutto il suo petrolio e lo stretto di Hormuz, la rotta principale, è di fatto "
                   "bloccato (AP).",
         "quindi": "Con il dollaro vicino a 160 yen torna il tema dell'intervento di Tokyo, che un funzionario giapponese ha "
                   "ricordato venerdì (AP).",
         "testo": ["Quando il petrolio sale perché manca l'offerta, di solito soffrono i paesi che lo comprano: pagano di più "
                   "senza vendere di più. Europa e Giappone sono i casi più chiari. A Tokyo i consumi privati sono scesi "
                   "nel trimestre, tra maltempo e prezzi più alti, e il Pil è calato per la prima volta in un anno (AP).",
                   "Il conflitto in Iran è in stallo. Le ostilità su larga scala sono finite, ma Hormuz resta chiuso, e la Cina "
                   "riceveva circa un terzo del suo greggio da quella rotta (Al Jazeera)."],
         "fonte": "Fonti: AP, Al Jazeera, chiusure del Brent future."},
    ],

    "scommessa": {"tesi": "Con noi: i conti di Nvidia e i verbali della Fed decidono la settimana. Contro: i chip asiatici in "
                          "calo e l'oro sotto pressione. Da qui a venerdì: Nvidia martedì sera, Fed mercoledì.",
                  "lunedi": True, "venerdi": False, "settimana_prec": "9-13 novembre",
                  "com_e_andata": "I rendimenti sono saliti più del previsto e hanno portato fuori forchetta Treasury, "
                                  "euro-dollaro e oro, mentre l'Euro Stoxx ha corso più del previsto."},
    "parole": [("Chip", "I microprocessori e le memorie dentro computer e server: se ne parla tanto per l'AI."),
               ("Acquisti rifugio", "Acquisti di titoli considerati sicuri, come Treasury e oro, quando cresce la paura."),
               ("Verbali della Fed", "Il resoconto della riunione, pubblicato tre settimane dopo: dice quanto i membri "
                                     "erano divisi sui tassi."),
               ("Curva dei rendimenti", "I rendimenti messi in fila dal titolo più breve al più lungo."),
               ("Importatore di petrolio", "Un paese che compra più energia di quanta ne produce: soffre un greggio caro."),
               ("Quotazione in borsa", "Il debutto di una società sul mercato: le sue azioni cominciano a essere scambiate.")],
    "fonti": [
        ("Dati di mercato", "Financial Modeling Prep (indici USA e Asia, Brent e oro future, curva par del Tesoro USA); "
                            "Alpha Vantage (EUR/USD, ACWI); dpa-AFX (Euro Stoxx 50); JoongAng Daily e AFP (Kospi); "
                            "SoldiOnline e Money.it (Ftse Mib)."),
        ("Prima pagina e mercati", "AP, AFP, Reuters, Financial Times, Bloomberg, Investing.com, Al Jazeera, SoldiOnline."),
        ("Calendario e agenda", "FXEmpire, Thrive in Markets, SEC (conti Nvidia)."),
        ("Approfondimenti", "Chip: AP, AFP, Seoul Economic Daily, Reuters. Tassi: Kitco, CNBC, FXEmpire. Europa: dpa-AFX, "
                            "SoldiOnline, ANSA. Petrolio: AP, Al Jazeera."),
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
