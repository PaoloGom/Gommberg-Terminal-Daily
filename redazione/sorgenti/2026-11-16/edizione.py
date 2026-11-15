"""EDIZIONE #026 (prova generale 16/11/2026) su modello v6 - ex #004 del 15/10/2026 rifatta nella struttura v6 (SPEC v6).
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
NOTA_DATI = "Chiusure al 13 novembre; lunedì 16 le borse asiatiche non hanno ancora aperto al momento dell'uscita"
REG = "2026-11-16-settimana.json"

D = json.load(open("dati.json", encoding="utf-8"))["serie"]
def ult(nome, giorno):
    return next(v for g, v, *_ in D[nome]["ultimi"] if g == giorno)
def riga(nome, et, dec, base_anno, giorno="2026-11-13", sett="2026-11-06", unita=""):
    u = D[nome]["ultimi"]
    v0, v1 = u[0][1], u[1][1]
    vs = ult(nome, sett)
    ytd = "n.d." if base_anno is None else var(v0, base_anno, "pct", 1)
    return [et, fmt(v0, dec) + unita, "13/11", var(v0, v1, "pct", 1), var(v0, vs, "pct", 1), ytd]
d = lambda s: dt.date(2026, int(s[:2]), int(s[3:]))

NVDA = [("11-06", 186.64), ("11-09", 178.67), ("11-10", 168.89), ("11-11", 173.73), ("11-12", 166.19),
        ("11-13", 162.85)]
CURVA_6 = {"3M": 4.19, "6M": 4.23, "1A": 4.33, "2A": 4.51, "3A": 4.59, "5A": 4.64, "7A": 4.74, "10A": 4.86, "20A": 5.29}
CURVA_13 = {"3M": 4.32, "6M": 4.42, "1A": 4.65, "2A": 4.88, "3A": 4.92, "5A": 4.98, "7A": 5.05, "10A": 5.15, "20A": 5.52}
UST2 = [("10-13", 4.79), ("10-14", 4.82), ("10-15", 4.77), ("10-16", 4.74), ("10-19", 4.77), ("10-20", 4.79), ("10-21", 4.81), ("10-22", 4.65),
        ("10-23", 4.69), ("10-26", 4.68), ("10-27", 4.70), ("10-28", 4.67), ("10-29", 4.61), ("10-30", 4.56), ("11-02", 4.59), ("11-03", 4.61),
        ("11-04", 4.58), ("11-05", 4.46), ("11-06", 4.51), ("11-09", 4.56), ("11-10", 4.73), ("11-12", 4.86), ("11-13", 4.88)]
BRENT = [("10-12", 106.65), ("10-13", 105.69), ("10-14", 106.06), ("10-15", 105.92), ("10-16", 109.86), ("10-19", 109.55), ("10-20", 108.79),
         ("10-21", 108.82), ("10-22", 113.17), ("10-23", 116.72), ("10-26", 115.81), ("10-27", 113.88), ("10-28", 115.32), ("10-29", 110.80),
         ("10-30", 113.43), ("11-02", 104.77), ("11-03", 103.60), ("11-04", 94.62), ("11-05", 98.29), ("11-06", 98.32), ("11-09", 92.57),
         ("11-10", 91.49), ("11-11", 92.76), ("11-12", 95.82), ("11-13", 95.84)]
DAL_4 = [("Euro Stoxx 50", 6386.86 / 6271.90 - 1), ("Hang Seng", 23637.60 / 23919.50 - 1), ("Nikkei 225", 61142.35 / 62188.63 - 1),
         ("S&amp;P 500", 7561.67 / 7688.62 - 1), ("Nasdaq", 25136.27 / 25736.51 - 1), ("Russell 2000", 2790.49 / 2856.95 - 1)]

C = {
    "data": OGGI,
    "temi": ["Chip", "Fed", "Tassi", "Petrolio", "Europa", "Geopolitica"],
    "glossario": ["PPI", "CME FedWatch", "VIX", "HBM", "EIA", "FOMC", "BLS"],
    "meccanismi": ["M26", "M02", "M01", "M15", "M17", "M16", "M10", "M11", "M14"],
    "ticker": ticker_da_dati("dati.json"),

    "top": {
        "tema": "Chip",
        "titolo": "Nvidia presenta i conti martedì: sarà il primo esame senza Huang",
        "dek": "Il titolo ha perso un quarto del valore dal 27 ottobre e venerdì ha chiuso a 162,85 $, dopo l'addio del "
               "fondatore. Martedì parlerà per la prima volta da amministratrice delegata ad interim la direttrice finanziaria "
               "Colette Kress, che dovrà dire che cosa vale Nvidia senza Huang. Per noi il trimestre conta meno della "
               "prospettiva: il mercato vuole capire che cosa può vendere la società, e con quale guida. [[chip]]",
        "freccia": "Nella sua guida per il trimestre Nvidia non conta alcun ricavo dalla Cina (comunicato Nvidia).",
    },
    "quadro": "La settimana ha messo i tassi sopra ogni altra cosa. Il 2 anni sale di 37 pb e arriva al 4,88%, il dollaro "
              "si rafforza sull'euro e l'oro perde il 4,6%. Di solito accade quando una Fed più dura rende meno "
              "conveniente tenere un metallo che non paga interessi. Il petrolio non segue (il Brent cala del 2,5%) e le "
              "borse si dividono: l'Europa guadagna il 3,5%, Wall Street resta sotto i livelli del 4 novembre.",
    "in30": [
        "Fed: oggi parla Warsh, mercoledì escono i verbali e il rialzo di dicembre è già nei prezzi. [[fed]]",
        "Petrolio: scende perché le scorte americane crescono, anche con le tensioni nel Golfo. [[petrolio]]",
        "Europa: le borse hanno già recuperato il crollo del 5 novembre, Wall Street no. [[europa]]",
    ],
    "in30_temi": ["Fed", "Petrolio", "Europa"],
    "stamattina_titolo": "Cosa guardare all'apertura",
    "stamattina": [
        "Alle 03:00 i dati cinesi di ottobre: produzione industriale attesa al 5,3% su un anno, vendite al dettaglio allo 0,8% (Radiocor)",
        "Alle 18:00 parla Warsh, il presidente della Fed",
        "Alle 23:00 di martedì i conti di Nvidia: il primo test per i chip, a Seul e a Milano",
    ],
    "notizie": [
        {"tag": "Inflazione", "titolo": "I prezzi alla produzione USA salgono meno del previsto, ma restano a +6,5%",
         "testo": "A ottobre l'aumento è dello 0,3% sul mese, un decimo sotto le attese. Su un anno il rialzo è il più forte da "
                  "novembre 2022 (Cointelegraph).", "rimando": "fed"},
        {"tag": "Geopolitica", "titolo": "L'Iran dice che quattro petroliere sono state colpite a Hormuz",
         "testo": "Reuters non ha potuto verificare l'esplosione. Trump scrive che per chiudere la guerra non serve un accordo "
                  "e il blocco navale americano resta.", "rimando": "petrolio"},
        {"tag": "Cina", "titolo": "Trump vola a Shenzhen e cerca un incontro a tre con Xi e Putin",
         "testo": "Prima passa dalle Filippine. Pechino dice solo che si valutano contatti, e la presenza di Putin non è "
                  "confermata (AP)."},
        {"tag": "Dazi", "titolo": "Il Congresso prepara quattro leggi per frenare i chip verso la Cina",
         "testo": "Lo scrive Reuters: Huang dovrebbe testimoniare entro il 26 novembre. Venerdì le azioni cinesi dell'IA "
                  "cadono, Z.AI del 12% e MiniMax dell'8,4%.", "rimando": "chip"},
        {"tag": "Asia", "titolo": "Gli stranieri vendono 550 miliardi di won a Seul e il Kospi cede l'1%",
         "testo": "L'indice resta comunque in rialzo del 4,6% sulla settimana (Korea JoongAng Daily).", "rimando": "chip"},
        {"tag": "Italia", "titolo": "Cucinelli e Banca Generali guidano il Ftse Mib, Technoprobe cede il 2,7%",
         "testo": "L'indice chiude a 51.858,51 punti, in rialzo dello 0,1%; Technoprobe è legata ai chip (Teleborsa)."},
    ],

    "mercati_titolo": "Numeri, temi aperti e calendario",
    "cruscotto": [
        ("Mondo e Stati Uniti", [riga("ACWI", "MSCI ACWI (ETF, $)", 2, None),
                                 riga("S&P 500", "S&amp;P 500", 2, 6845.49), riga("Nasdaq", "Nasdaq Comp.", 2, 23241.99),
                                 riga("Russell 2000", "Russell 2000", 2, 2481.91)]),
        ("Europa", [riga("Euro Stoxx 50", "Euro Stoxx 50", 2, 5796.22),
                    ["FTSE MIB", "51.858,51", "13/11", "+0,1%", "+3,6%", "+15,4%"]]),
        ("Asia (chiusure del 13/11)", [riga("Nikkei 225", "Nikkei 225", 2, 50339.48), riga("Hang Seng", "Hang Seng", 2, 25630.55),
                                       ["Kospi", "5.290,53", "13/11", "-1,0%", "+4,6%", "n.d."]]),
    ],
    "cruscotto_nota": "1 g = chiusura su chiusura; 1 sett. = su venerdì 6/11; da inizio anno = su chiusura 2025. "
                      "Asia: chiusure di venerdì, il lunedì le borse non hanno ancora aperto.",
    "cross_data": "Livello 13/11",
    "cross": [
        ("Tassi", [["Treasury 2 anni", "4,88%", "+2 pb", "+37 pb", "+9 pb", "Segue le attese sulla Fed [[fed]]"],
                   ["Treasury 10 anni", "5,15%", "+5 pb", "+29 pb", "-6 pb", "-"],
                   ["Spread Italia", "104 pb", "n.d.", "n.d.", "n.d.", "10 anni italiano al 4,42% (Teleborsa)"]]),
        ("Cambi", [["EUR/USD", "1,1021", "-0,3%", "-1,1%", "-1,6%", "-"]]),
        ("Materie prime", [["Brent future", "95,84 $", "0,0%", "-2,5%", "-9,3%", "-"],
                           ["Oro (future, $/oncia)", "3.886", "0,0%", "-4,6%", "-7,0%", "-"]]),
        ("Volatilità", [["VIX (volatilità attesa)", "19,30", "+0,60", "-6,34", "+4,03", "Massimo di giornata a 20,92"]]),
    ],
    "cross_nota": "1 mese = sul 13/10. VIX = volatilità attesa sull'S&amp;P 500.",
    "termometri": [
        ("Nvidia e chip", "Conti martedì 17/11", "Il Congresso valuta limiti all'export verso la Cina", "su: Rischio di nuove regole sull'export", "Conti e guida di martedì"),
        ("Fed", "Rialzo di dicembre atteso", "Warsh parla alle 18:00, verbali mercoledì", "su: Probabilità del rialzo di dicembre", "Vendite al dettaglio USA"),
        ("Iran e Hormuz", "Blocco navale USA in vigore", "Teheran dice che quattro petroliere sono state colpite", "fermo: Brent, senza direzione", "Conferme indipendenti"),
        ("Dollaro", "EUR/USD 1,1021 in chiusura", "Euro in calo per la quinta seduta", "su: Dollaro contro euro", "Treasury a 2 anni"),
    ],
    "fermi": "Yen vicino a 160 per dollaro (ultima novità verificata il 13/11).",
    "lettura": "Due cose che le tabelle dicono e la prima pagina no. Il Russell 2000, l'indice delle società più piccole, "
               "recupera nella settimana poco più della metà dell'S&amp;P 500 (+1,3% contro +2,5%): di solito chi ha più "
               "debiti soffre di più quando i tassi salgono. E il VIX (la volatilità attesa a Wall Street) scende di oltre "
               "6 punti ma resta a 19,30, sopra i 15,27 di un mese fa: la paura è calata, non è sparita.",

    "ieri": [
        ("Mar 10, 14:30", "Prezzi al consumo USA (ottobre)", "+0,4% sul mese (atteso +0,3%); senza energia e alimentari +0,3% (+0,2%)", "+", "[[fed]]"),
        ("Ven 13, 14:30", "Prezzi alla produzione USA (ottobre)", "+0,3% sul mese (atteso +0,4%); +6,5% su un anno", "-", "[[fed]]"),
    ],
    "agenda": [
        ("Lun 16, 18:00", "Discorso di Warsh (Fed)", "Nessun numero: si ascolta il tono",
         "Dopo i dati sui prezzi, ogni parola sui rialzi conta",
         "<b>Più duro:</b> se non esclude rialzi dopo dicembre, di solito salgono i rendimenti a breve.<br/><b>Più cauto:</b> se resta sulla produttività, l'effetto di solito è piccolo."),
        ("Mar 17, 14:30", "Vendite al dettaglio USA (ottobre)", "0,0% sul mese; prima +0,8%",
         "Dice se i consumi reggono dopo i rincari",
         "<b>Sopra:</b> di solito salgono dollaro e rendimenti a breve: consumi forti lasciano spazio alla Fed.<br/><b>Sotto:</b> il rialzo di dicembre perde un po' di forza."),
        ("<b>Mar 17, 23:00</b>", "<b>Conti trimestrali di Nvidia</b>", "<b>Guida della società: ricavi 108 mld $ (±2%); prima 96,2 mld $</b>",
         "<b>Evento n.1:</b> primo esame senza Huang",
         "<b>Sopra:</b> di solito un trimestre sopra la guida aiuta anche AMD e i chip asiatici.<br/><b>Sotto:</b> la vendita sul settore può ripartire."),
        ("Mer 18, 20:00", "Verbali del FOMC (riunione di ottobre)", "Nessun numero: mostrano chi voleva rialzare",
         "A ottobre due membri avevano votato per un rialzo",
         "<b>Più duro:</b> molti favorevoli al rialzo: di solito sale il 2 anni.<br/><b>Più cauto:</b> pochi favorevoli: di solito scende."),
    ],

    "moduli": [
        {"chiave": "chip", "tema": "Chip", "breve": "Nvidia cala in due tempi",
         "titolo": "Nvidia cala in due tempi: prima con i chip, poi da sola",
         "misura": "doppio",
         "grafico": {"tipo": "linee", "file": "c_nvda.png", "x": [d(x) for x, _ in NVDA], "soggetto": "Nvidia",
                     "serie": [("Nvidia", [v for _, v in NVDA], "#F26B1D")], "ruolo": "storia",
                     "titolo": "Dal 6 novembre Nvidia ha perso oltre un ottavo",
                     "sottotitolo": "Nvidia, chiusure giornaliere ($)",
                     "eventi": [(d("11-12"), "Addio di Huang")],
                     "note": [(d("11-06"), 186.64, "6/11"), (d("11-13"), 162.85, "13/11")]},
         "grafico2": {"tipo": "barre", "file": "c_chip_giorni.png", "ordina": False, "dec": 1, "unita": "%", "soggetto": "chip", "ruolo": "chi",
                      "dati": [("Nvidia 5/11", -9.3), ("AMD 5/11", -17.3), ("Nvidia 12/11", -4.3), ("AMD 12/11", 5.9)],
                      "titolo": "Il 5 novembre scende tutto il settore, il 12 solo Nvidia",
                      "sottotitolo": "Variazione giornaliera (%)"},
         "numero": "0: i ricavi dalla Cina contati nella guida da 108 mld $. Un limite del Congresso all'export toglie poco a quella guida, "
                   "un'apertura della Cina aggiungerebbe.",
         "perche": "Il 5 novembre è caduto tutto il settore: l'AP lo lega ai timori sui data center dell'intelligenza "
                   "artificiale, al costo del denaro e alle elezioni di metà mandato (AP). Il 12 novembre è un'altra storia: "
                   "AMD sale del 5,9% mentre Nvidia perde il 4,3%, e per noi un'ondata di vendite su tutto il settore non "
                   "produce questa divergenza.",
         "quindi": "Mercoledì guarda AMD e i chip asiatici: se seguono Nvidia dopo i conti, la seconda fase non era solo sua.",
         "punti": ["<b>Seul.</b> Hana Securities vede un impatto limitato sulla domanda di chip; per Mirae Asset gli ordini "
                   "potrebbero spostarsi su AMD o su chip su misura.",
                   "<b>SK hynix.</b> È più esposta di Samsung, perché gran parte delle sue memorie HBM (veloci, usate con i chip per l'IA) va a Nvidia."],
         "testo": ["Che cosa cambia quando se ne va una persona sola? Chi compra Nvidia non compra i ricavi "
                   "di oggi, ma ciò che la società venderà nei prossimi anni. Huang decideva dove mettere i soldi, con chi "
                   "firmare i contratti e come trattare con Washington. Quando se ne va, i conti dell'ultimo trimestre non "
                   "cambiano: cambia la fiducia su quelli futuri.",
                   "La prima discesa con lui non c'entra. Il 5 novembre l'S&P 500 ha perso il 4,4% e il Nasdaq il 5,5%. "
                   "Nvidia ha ceduto il 9,3% e AMD il 17,3%. Da allora il rendimento del Treasury a 10 anni è salito dal 4,84% al 5,15%. "
                   "I data center costano di più da finanziare quando i tassi salgono, ed è il bersaglio che l'AP "
                   "indica. Fino al 6 novembre Nvidia aveva perso il 14,4% rispetto al 27 ottobre.",
                   "La seconda discesa è solo sua. Dal 6 al 13 novembre il titolo ha perso il 12,7%, e il giorno dell'addio "
                   "AMD ha guadagnato mentre Nvidia scendeva.",
                   "Martedì il trimestre conta meno di quanto sembri. La società aveva indicato 108 mld $ di ricavi, senza "
                   "contare la Cina, dopo i 96,2 mld $ del trimestre precedente (+106% su un anno). Di solito un titolo reagisce "
                   "più alla prospettiva che l'azienda dà per il periodo dopo che al confronto con le stime. Qui la dà "
                   "Colette Kress, alla sua prima volta da amministratrice delegata ad interim.",
                   "Il canale verso l'Asia è diretto: Kospi e borsa di Taiwan pesano molto nei semiconduttori e di solito si "
                   "muovono con i chip americani. Venerdì Seul ha perso lo 0,98% e SK hynix il 3,03%. In Italia a pagare è "
                   "Technoprobe: giovedì -4,73%, un calo che l'ANSA lega al tonfo di Nvidia, e venerdì -2,66%."],
         "fonte": "Fonti: Nvidia (comunicato), AP, Seoul Economic Daily, Korea JoongAng Daily, ANSA, Teleborsa; chiusure da FMP.",
         "guardare": "Se mercoledì AMD e i chip asiatici si muovono con Nvidia, la seconda fase è finita; se vanno in senso "
                     "opposto, il caso Huang pesa solo su di lei. Un nuovo limite all'export cambierebbe poco la guida, che la "
                     "Cina non la conta già."},
        {"chiave": "fed", "tema": "Tassi USA", "breve": "i rialzi sono già nei prezzi",
         "titolo": "Il 2 anni è un punto sopra la Fed: i rialzi sono nei prezzi",
         "misura": "doppio",
         "grafico": {"tipo": "barre", "file": "c_curva_sett.png", "ordina": False, "dec": 0, "unita": " pb", "soggetto": "2 anni", "ruolo": "quanto",
                     "dati": [(k, round((CURVA_13[k] - CURVA_6[k]) * 100)) for k in CURVA_13],
                     "titolo": "La salita è massima sulle scadenze intermedie",
                     "sottotitolo": "Curva Treasury, variazione dal 6 al 13/11 (pb)"},
         "grafico2": {"tipo": "linee", "file": "c_ust2.png", "x": [d(x) for x, _ in UST2], "soggetto": "2 anni", "ruolo": "storia",
                      "serie": [("Treasury a 2 anni", [v for _, v in UST2], "#F26B1D")],
                      "titolo": "Il 2 anni si allontana dalla forchetta dei tassi Fed",
                      "sottotitolo": "Rendimento a 2 anni, chiusure (%)",
                      "soglie": [(3.75, "minimo tasso Fed"), (4.00, "massimo tasso Fed")],
                      "note": [(d("10-13"), 4.79, "13/10"), (d("11-13"), 4.88, "13/11")]},
         "numero": "89,7%: la probabilità di un rialzo da un quarto di punto a dicembre dopo i prezzi alla produzione, contro "
                   "l'85,4% del giorno prima (CME FedWatch).",
         "perche": "Il mercato ha incassato prima i prezzi al consumo di ottobre sopra le attese e poi le parole di due "
                   "governatori. Waller vede possibile un rialzo di mezzo punto, Logan ne vuole almeno due (CNBC).",
         "quindi": "Mercoledì alle 20:00 i verbali dicono se, oltre a Cook e Hammack, altri volevano già rialzare a ottobre.",
         "testo": ["Il 2 anni è il rendimento che chiede chi presta soldi al governo americano per due anni. Di solito "
                   "segue le attese sulla Fed più da vicino di ogni altra scadenza. La Fed tiene i tassi tra 3,75% e 4%. "
                   "Il 2 anni è al 4,88%: chi presta chiede quasi un punto in più perché si aspetta che i tassi "
                   "salgano ancora. È come dire che il mercato i rialzi li ha già comprati.",
                   "Per questo la settimana ha contato più della riunione di dicembre. In cinque sedute il 2 anni ha "
                   "guadagnato 37 pb e il 10 anni 29 pb. Quando i rendimenti salgono i prezzi dei titoli scendono: chi li "
                   "teneva ha perso.",
                   "I dati hanno detto due cose diverse. Il 10 novembre i prezzi al consumo sono saliti più delle attese, "
                   "anche nel dato di fondo: +0,3% contro +0,2%. Venerdì quelli alla produzione, +0,3% contro +0,4%, sono "
                   "usciti un decimo sotto, pur restando in rialzo del 6,5% su un anno. Il dato annuale dei prezzi al "
                   "consumo non esiste: il BLS non raccolse i prezzi di ottobre 2025 e non può calcolarlo.",
                   "Dentro la Fed la spinta c'è già. Il 28 ottobre Cook e Hammack hanno votato contro la scelta di lasciare i "
                   "tassi fermi, perché volevano alzarli di un quarto di punto. La decisione è passata con dieci voti a due.",
                   "Oggi alle 18:00 parla Warsh, ma l'appuntamento che pesa di più è mercoledì. Domani alle 14:30 le "
                   "vendite al dettaglio, attese ferme, dicono se i consumi reggono: di solito un dato forte lascia più "
                   "spazio alla Fed e fa salire il breve."],
         "fonte": "Fonti: Federal Reserve, BLS, CNBC, CME FedWatch, Cointelegraph, curva par del Tesoro USA da FMP.",
         "guardare": "Se i verbali mostrano molti favorevoli al rialzo già a ottobre, il 2 anni ha ragione e può salire ancora. "
                     "Se i voti contro restano due, il rialzo di dicembre dipenderà soprattutto dai prossimi prezzi."},
        {"chiave": "petrolio", "tema": "Petrolio", "breve": "il barile scende lo stesso",
         "titolo": "Il petrolio scende perché le scorte crescono, non perché Hormuz si calma",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_brent.png", "x": [d(x) for x, _ in BRENT], "soggetto": "petrolio", "ruolo": "storia",
                     "serie": [("Brent", [v for _, v in BRENT], "#F26B1D")],
                     "titolo": "Dal massimo del 23 ottobre il Brent ha perso il 18%",
                     "sottotitolo": "Brent future, chiusure ($)",
                     "note": [(d("10-23"), 116.72, "23/10"), (d("11-13"), 95.84, "13/11")]},
         "numero": "116,72 $ contro 95,84 $: dal massimo del 23 ottobre alla chiusura di venerdì, con Hormuz ancora in tensione.",
         "perche": "Le scorte americane di greggio sono salite di 4,7 milioni di barili nella settimana al 6 novembre, mentre "
                   "gli analisti ne aspettavano un calo di 1,1 milioni (Reuters).",
         "quindi": "Mercoledì l'EIA (l'agenzia americana dell'energia) pubblica le scorte al 13 novembre: se salgono ancora, il calo del Brent trova conferma.",
         "testo": ["Chi compra petrolio ha in testa due prezzi. Uno è il rischio: un attacco a un impianto o a una nave fa "
                   "temere che domani manchino barili. L'altro è la scorta: se nei serbatoi americani i barili aumentano, oggi "
                   "ce ne sono più del necessario. Questa settimana ha vinto il secondo.",
                   "Il rischio, intanto, è già nel prezzo: dal massimo del 23 ottobre il Brent ha perso il 18% con Hormuz "
                   "ancora in tensione. Quando un petrolio caro non basta a far temere nuove carenze, di solito basta una "
                   "scorta in più per farlo scendere.",
                   "Il calo conta anche lontano dal Golfo. Per l'Europa e il Giappone, che il greggio lo comprano, alleggerisce "
                   "il conto dell'energia; per la Fed alleggerisce l'inflazione, perché i carburanti entrano presto nei "
                   "prezzi complessivi.",
                   "Che cosa smentirebbe questa lettura? Una nuova scorta in calo o un attacco confermato a una petroliera. "
                   "In quel caso tornerebbe a contare il rischio, e il Brent potrebbe risalire in fretta dai 95,84 $ di venerdì."],
         "fonte": "Fonti: Reuters, AP; chiusure del Brent future (FMP)."},
        {"chiave": "europa", "tema": "Europa", "breve": "Europa già oltre il crollo",
         "titolo": "L'Europa ha già recuperato il crollo del 5 novembre, Wall Street no",
         "misura": "mezzo",
         "grafico": {"tipo": "barre", "file": "c_dal4.png", "ordina": False, "dec": 1, "unita": "%", "soggetto": "Europa", "ruolo": "quanto",
                     "dati": [(n, round(v * 100, 1)) for n, v in DAL_4],
                     "titolo": "Solo l'Euro Stoxx 50 è sopra il livello del 4 novembre",
                     "sottotitolo": "Variazione dal 4 al 13 novembre (%)"},
         "numero": "+1,8%: quanto l'Euro Stoxx 50 sta sopra il livello del 4 novembre; l'S&amp;P 500 è ancora sotto dell'1,7%.",
         "perche": "Secondo Merck Finck gli investitori passano dai titoli di crescita a quelli più solidi, e questo spiega "
                   "perché l'Europa batte Wall Street e l'Asia mentre l'intelligenza artificiale si indebolisce (dpa-AFX).",
         "quindi": "Il Nasdaq deve salire di circa il 2,4% per tornare ai 25.736 punti del 4 novembre.",
         "testo": ["Il 5 novembre è stato il giorno del crollo: S&amp;P 500 -4,4%, Nasdaq -5,5%. In otto sedute l'Euro "
                   "Stoxx 50 ha ripreso quel livello e lo ha superato dell'1,8%, mentre l'S&amp;P 500 è ancora sotto dell'1,7%.",
                   "Il motivo sta nei pesi. S&amp;P 500 e Nasdaq contano ogni titolo per il suo valore in borsa. Pochi "
                   "grandi nomi come Nvidia guidano gran parte del movimento. Un indice europeo pesa meno i chip, e di solito "
                   "un'ondata di vendite sull'IA lo scalfisce meno.",
                   "Milano fa meglio ancora: il Ftse Mib guadagna il 3,61% in settimana e chiude a 51.858,51. Lo spread tra "
                   "Btp e Bund è a 104 punti e il rendimento del Btp a 10 anni al 4,42% (Teleborsa).",
                   "Il confronto va letto con prudenza: dal 5 novembre l'Europa ha anche beneficiato di un punto di partenza più "
                   "basso, perché Wall Street ha ceduto di più. La prova vera arriva se martedì i conti di Nvidia riaccendono "
                   "i titoli tecnologici: allora il vantaggio europeo può ridursi, perché lì i grandi nomi pesano di meno."],
         "fonte": "Fonti: dpa-AFX, Teleborsa, Money.it, AP; chiusure da FMP."},
    ],

    "scommessa": {"tesi": "Con noi: i conti di Nvidia possono dare respiro a Wall Street e il petrolio ha le scorte in aumento. "
                          "Contro: dollaro e rendimenti salgono con una Fed pronta a stringere. Da qui a venerdì: Nvidia martedì, "
                          "verbali della Fed mercoledì.",
                  "lunedi": True, "venerdi": False, "settimana_prec": "9-13 novembre",
                  "com_e_andata": "Hanno funzionato le direzioni su azioni, euro, petrolio e oro. Ha sbagliato quella del Treasury a 10 anni: i prezzi al consumo e i governatori della Fed hanno spinto i rendimenti in alto."},
    "parole": [("Guida dei ricavi", "La previsione che un'azienda dà per il trimestre successivo: il mercato la guarda più dei conti già chiusi."),
               ("Rendimento a 2 anni", "Il tasso che chiede chi presta al governo americano per due anni: segue le attese sulla Fed."),
               ("Verbali della Fed", "Il resoconto della discussione di una riunione, pubblicato tre settimane dopo: mostra chi voleva che cosa."),
               ("Dato di fondo", "L'inflazione senza energia e alimentari, le voci più volatili: mostra la tendenza dei prezzi."),
               ("Scorte di greggio", "I barili che restano nei serbatoi americani: se salgono, di solito il petrolio costa meno."),
               ("Memorie HBM", "Chip di memoria veloce, usati insieme ai processori per l'IA.")],
    "fonti": [
        ("Dati di mercato", "FMP (indici USA e Asia, VIX, Brent, oro, Treasury, Nvidia); Alpha Vantage (EUR/USD, ACWI); dpa-AFX (Euro Stoxx 50); Teleborsa e Money.it (Ftse Mib, spread); Korea JoongAng Daily (Kospi)."),
        ("Notizie e approfondimenti", "Reuters, AP, CNBC, Cointelegraph, ANSA, Teleborsa, dpa-AFX, Seoul Economic Daily, comunicato Nvidia, Federal Reserve, BLS, CME FedWatch."),
        ("La scommessa", "Chiusure di FMP e Alpha Vantage; forchette dalla volatilità delle ultime 20 sedute."),
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
