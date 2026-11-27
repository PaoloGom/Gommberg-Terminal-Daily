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
OGGI = dt.date(2026, 11, 27)
NOTA_DATI = "Chiusure al 26 novembre per Europa e Asia di ieri, al 27 novembre per Tokyo, Hong Kong e Seul; Stati Uniti fermi al 25 novembre (Ringraziamento)"
REG = "2026-11-23-settimana.json"
d = lambda s: dt.date(2026, int(s[:2]), int(s[3:]))
KOSPI = [("23/11", -3.31), ("24/11", 6.32), ("25/11", -6.16), ("26/11", 0.29), ("27/11", 4.34)]
_X = ["11-16", "11-17", "11-18", "11-19", "11-20", "11-24", "11-25", "11-26", "11-27"]
_NK = [59662.02, 58860.43, 59024.28, 59444.21, 56436.65, 58644.63, 57011.62, 57499.16, 58711.11]
_HS = [23753.85, 23508.18, 23294.76, 22841.63, 22410.81, 22219.66, 21966.02, 22226.89, 22694.77]
_E = ["11-20", "11-23", "11-24", "11-25", "11-26"]
_ES = [5941.95, 6074.47, 6003.76, 5894.46, 6014.74]
_FM = [48703.72, 49021.0, 48121.19, 47249.0, 48362.0]
TITOLI = [("Stellantis", 8.82), ("Prysmian", 6.57), ("STMicroelectronics", 4.58), ("Technoprobe", 4.31), ("Banco BPM", 2.81), ("Intesa Sanpaolo", 2.46), ("UniCredit", 0.87)]
_GX = ["11-16", "11-17", "11-18", "11-19", "11-20", "11-23", "11-24", "11-25", "11-26"]
_GV = [3853.0, 3864.2, 3741.9, 3685.5, 3515.4, 3651.4, 3561.9, 3535.8, 3687.4]
_BX = ["11-09", "11-10", "11-11", "11-12", "11-13", "11-16", "11-17", "11-18", "11-19", "11-20", "11-23", "11-24", "11-25"]
_BV = [92.57, 91.49, 92.76, 95.82, 95.84, 92.44, 93.14, 91.95, 91.98, 92.57, 89.37, 91.40, 94.61]
b100 = lambda v: [round(x / v[0] * 100, 1) for x in v]
TAB = tabelle_da_dati("dati.json")
C = {
    "data": OGGI,
    "temi": ["Asia", "Europa", "Italia", "Materie prime", "Petrolio", "Fed"],
    "glossario": ["VIX", "pb", "BTP", "Bund", "CME FedWatch", "GPU"],
    "meccanismi": ["M23", "M11"],
    "ticker": ticker_da_dati("dati.json"),
    "top": {
        "tema": "Asia",
        "titolo": "L'Asia risale e Seul guadagna il 4,3% sperando in un fondo pubblico",
        "dek": "Il Kospi chiude a 4.915,68 punti, due sedute dopo aver perso il 6,2%. Secondo la stampa coreana pesano gli acquisti dopo il crollo, i future americani in rialzo e l'attesa che le autorità attivino o ampliino il fondo di stabilizzazione del mercato. Anche il Nikkei guadagna oltre il 2%. Ieri l'Europa aveva già recuperato con Wall Street chiusa, e oggi New York riapre per una mezza seduta. [[corea]]",
    },
    "quadro": "I prezzi dicono rimbalzo, non svolta. Le borse risalgono a Seul, a Tokyo e in Europa, l'oro recupera una parte della caduta e il dollaro resta fermo contro l'euro. A nostro avviso è un recupero fatto in giorni di scambi rarefatti: ieri New York era chiusa e le borse europee hanno mosso molto con pochi ordini. La prova arriva oggi dalla riapertura di Wall Street, e poi dal rialzo della Fed che i future danno quasi per certo a dicembre. Intanto lo spread tra BTP e Bund è sceso del 3,6%, a 107 punti.",
    "in30": [
        "L'Europa ha rimbalzato con New York chiusa, ma su pochi scambi. [[europa]]",
        "L'oro ha già riconquistato metà della caduta di questa settimana. [[oro]]",
        "Oggi Wall Street riapre per una mezza seduta: è la prima prova del rimbalzo. [[agenda]]",
    ],
    "in30_temi": ["Europa", "Materie prime", "Wall Street"],
    "stamattina_titolo": "Cosa guardare all'apertura",
    "stamattina": [
        "15:30 apre Wall Street, seduta corta fino alle 19:00",
        "Il Kospi guarda ai 5.000 punti: oggi ha chiuso a 4.915,68",
        "20:00 chiude il mercato USA dei titoli di Stato",
    ],
    "notizie": [
        {"tag": "Europa", "titolo": "Stellantis guadagna l'8,8% dopo uno studio di JPMorgan sulle auto",
         "testo": "Il titolo guida la Borsa di Milano, che ieri ha chiuso in forte rialzo mentre Wall Street era chiusa.", "rimando": "europa"},
        {"tag": "Italia", "titolo": "Prysmian sale del 6,6% dopo il sì della Grecia al cavo sottomarino",
         "testo": "Atene ha dato il via libera all'elettrodotto tra la terraferma e il Dodecaneso, un giorno prima del rialzo del titolo.", "rimando": "europa"},
        {"tag": "Chip", "titolo": "Nvidia e Kioxia mostrano una nuova memoria per le schede grafiche",
         "testo": "La tecnologia usa dischi a stato solido per allargare la memoria delle GPU e ha aiutato i titoli dei chip di memoria a Seul.", "rimando": "corea"},
        {"tag": "Italia", "titolo": "Banco BPM e Mediobanca salgono del 2,8% e Intesa del 2,5% a Milano",
         "testo": "Le banche hanno accompagnato il rialzo di Stellantis e Prysmian nella seduta di ieri.", "rimando": "europa"},
        {"tag": "Chip", "titolo": "STMicroelectronics e Technoprobe guadagnano oltre il 4% a Milano",
         "testo": "Per ANSA il rialzo viene dalla fiducia ritrovata sull'intelligenza artificiale.", "rimando": "europa"},
        {"tag": "Fed", "titolo": "I future danno il 63% a un secondo rialzo Fed a gennaio",
         "testo": "Per dicembre la probabilità di un rialzo di 25 punti base è tra il 97% e il 98%, secondo i future sui tassi. La decisione è attesa mercoledì 9 dicembre in serata."},
    ],
    "mercati_titolo": "Numeri, temi aperti e calendario",
    "cruscotto": TAB["cruscotto"], "cruscotto_nota": TAB["cruscotto_nota"],
    "cross_data": TAB["cross_data"], "cross": TAB["cross"], "cross_nota": TAB["cross_nota"],
    "termometri": [
        ("Fed e tassi", "Riunione 8-9 dicembre", "Rialzo di dicembre quasi scontato", "fermo: Probabilità di rialzo a dicembre", "Riunione Fed dell'8-9 dicembre"),
        ("AI e chip", "Rimbalzo in Asia", "Memoria per GPU di Nvidia e Kioxia", "su: Samsung e SK Hynix", "Kospi sopra i 5.000 punti"),
        ("Oro", "Rimbalzo dopo il -9% della settimana", "Ieri ha ripreso metà della caduta", "su: Oro future", "Livello 3.864 $ del 17/11"),
        ("Petrolio", "Brent a 94,61 $ mercoledì", "Attacchi nel Golfo secondo Bloomberg", "fermo: Brent tra 89 e 96 $", "Prime chiusure della settimana"),
    ],
    "fermi": "Dazi USA su 14 economie e BCE sulla riserva minima delle banche (nessuna novità verificata dal 26/11).",
    "lettura": "Le colonne non raccontano la stessa giornata: Asia ed Europa mostrano il rimbalzo di oggi e di ieri, mentre S&amp;P 500, Nasdaq e rendimenti dei Treasury sono fermi alla chiusura di mercoledì. Il VIX, a 28,29, è l'unico dato americano che dice quanta paura c'era prima del rimbalzo. Le due tabelle indicano per ogni riga la data della chiusura: per Treasury e indici USA è quella di mercoledì, e vanno lette con la mezza seduta di oggi in mente. Tra i mercati asiatici Hong Kong, a 22.694,77 punti, è quello più indietro nel recupero dal 16/11, mentre il cambio tra euro e dollaro, a 1,0967, resta la riga più ferma.",
    "ieri": [],
    "agenda": [
        ("<b>Ven 27, 15:30</b>", "<b>Riapre Wall Street, seduta corta</b>", "<b>Chiude alle 19:00; S&amp;P 500 a 7.182,78 mercoledì</b>",
         "<b>Evento n.1:</b> prima prova del rimbalzo dopo il Ringraziamento",
         "<b>Sopra:</b> se tengono i guadagni di Asia ed Europa, il rimbalzo si conferma.<br/><b>Sotto:</b> se New York restituisce i rialzi, erano scambi sottili."),
        ("Ven 27, 20:00", "Chiude il mercato USA dei titoli di Stato", "Orario ridotto: le 14:00 a New York", "Pochi scambi sui Treasury",
         "<b>Sopra:</b> rendimenti in rialzo, di solito pesano su oro e azioni di crescita.<br/><b>Sotto:</b> rendimenti in calo, di solito sostengono l'oro."),
        ("Mer 9 dic, in serata", "Decisione della Fed sui tassi", "Rialzo di 25 pb: probabilità del 97-98%", "Conferma o smentita del rialzo scontato",
         "<b>Sopra:</b> un rialzo più ampio o toni più duri, di solito sostengono dollaro e rendimenti.<br/><b>Sotto:</b> una pausa sorprenderebbe i mercati e di solito sostiene azioni e oro."),
        ("Lun 30, 15:30", "Wall Street torna agli orari normali", "Seduta piena, 9:30-16:00 a New York", "Torna il volume normale",
         "<b>Sopra:</b> scambi più alti, il rimbalzo si misura meglio.<br/><b>Sotto:</b> volumi bassi, ogni movimento pesa meno."),
    ],
    "moduli": [
        {"chiave": "corea", "tema": "Chip e Asia", "breve": "Seul in attesa del fondo",
         "titolo": "Il rimbalzo di Seul poggia su un fondo pubblico che ancora non c'è",
         "misura": "doppio",
         "grafico": {"tipo": "barre", "file": "c_kospi.png", "dati": KOSPI, "ordina": False, "dec": 1, "unita": "%",
                     "soggetto": "Kospi", "ruolo": "quanto",
                     "titolo": "In cinque sedute il Kospi ha dato e ripreso più del 6%",
                     "sottotitolo": "Kospi, variazione giornaliera (%)"},
         "grafico2": {"tipo": "linee", "file": "c_asia.png", "x": [d(x) for x in _X], "soggetto": "Tokyo", "ruolo": "storia",
                      "titolo": "Tokyo e Hong Kong sono ancora sotto il livello del 16/11",
                      "sottotitolo": "Nikkei 225 e Hang Seng, 16/11 = 100",
                      "serie": [("Nikkei 225", b100(_NK), "#111111"), ("Hang Seng", b100(_HS), "#F26B1D")]},
         "numero": "-1,8%: quanto manca al Kospi per tornare ai 5.006 punti del 24/11, il massimo di questa settimana.",
         "perche": "Per la stampa coreana pesano acquisti dopo il crollo, future americani e attesa del fondo. A nostro avviso conta soprattutto l'ultima: il 24/11 il Kospi era salito del 6,3% e il giorno dopo aveva restituito quasi tutto, un rimbalzo spento in fretta. A Tokyo e a Hong Kong il recupero è più lento.",
         "quindi": "Sopra i 5.006 punti del 24/11 il rimbalzo avrebbe un primo segnale di forza; sotto i 4.697,51 del 25/11 il fondo avrebbe fallito la prova.",
         "testo": ["Il Kospi risale due sedute dopo il crollo: la caduta è finita? Per ora è un rimbalzo, e la stampa coreana lo lega a un fondo con cui lo Stato interviene per frenare una vendita prolungata. Bastano le attese: se chi vende pensa che arriverà un compratore pubblico, ha meno fretta di vendere a qualunque prezzo.",
                   "Oggi i compratori sono gli stranieri e le istituzioni, mentre i piccoli risparmiatori hanno venduto per 1,77 mila miliardi di won. Il won si è rafforzato a 1.338,60 per dollaro.",
                   "Per un'analista di Kiwoom Securities, finché non arriva la domanda del fondo lo slancio del rimbalzo può restare limitato, anche se non c'è motivo di vedere tutto nero.",
                   "Sui chip pesa una notizia di stamattina. Nvidia e Kioxia hanno mostrato una tecnologia che usa dischi a stato solido per allargare la memoria delle schede grafiche. Samsung Electronics e SK Hynix chiudono in rialzo del 4,5% e del 5,4%. Il Kosdaq, il listino dei titoli più piccoli, sale di circa l'8,1%. Per KED Global il Kospi si avvicina ai 5.000 punti sulla speranza di un fondo di salvataggio più grande.",
                   "Fuori dalla Corea il recupero è più lento. Dal 16/11 il Nikkei è ancora sotto dell'1,6% e Hong Kong del 4,5%: il rimbalzo di oggi riempie una parte della buca, non tutta."],
         "fonte": "Fonti: Seoul Economic Daily, Digitaltoday, KED Global (Yonhap); chiusure di Nikkei e Hang Seng da FMP.",
         "guardare": "Conta se Seul annuncia l'ampliamento del fondo, oggi attorno a 10,8 mila miliardi di won, e se gli stranieri continuano a comprare. Un nuovo calo a fondo già attivo smentirebbe la lettura."},
        {"chiave": "europa", "tema": "Europa e Italia", "breve": "Europa su pochi scambi",
         "titolo": "L'Europa rimbalza con Wall Street chiusa, ma su pochi scambi",
         "misura": "doppio",
         "grafico": {"tipo": "linee", "file": "c_europa.png", "x": [d(x) for x in _E], "soggetto": "Europa", "ruolo": "storia",
                     "titolo": "Euro Stoxx 50 e FTSE MIB sono ancora sotto il livello del 23/11",
                     "sottotitolo": "Chiusure, 20/11 = 100",
                     "serie": [("Euro Stoxx 50", b100(_ES), "#111111"), ("FTSE MIB", b100(_FM), "#F26B1D")]},
         "grafico2": {"tipo": "barre", "file": "c_titoli.png", "dati": TITOLI, "ordina": False, "dec": 1, "unita": "%",
                      "soggetto": "titoli", "ruolo": "chi",
                      "titolo": "A guidare il rialzo di Milano sono auto, cavi, chip e banche",
                      "sottotitolo": "Variazioni del 26/11, titoli del FTSE MIB (%)"},
         "numero": "-35,7%: il calo dei pezzi scambiati ieri sull'Euro Stoxx 50 rispetto a mercoledì, da 24,8 a 15,9 milioni. Il rialzo del 2,0% si è fatto con un terzo di scambi in meno.",
         "perche": "Per ANSA gli scambi erano scarsi per la chiusura dei mercati USA; sui titoli, JPMorgan spiega Stellantis. A nostro avviso un rialzo così largo su volumi scesi di oltre un terzo dice più sul bisogno di recuperare che su un cambio di giudizio.",
         "quindi": "Sopra i 6.074,47 punti del 23/11 con New York aperta il rimbalzo si conferma; sotto i 5.941,95 del 20/11 si riapre la caduta.",
         "testo": ["Una borsa che sale del 2% fa pensare che la paura sia passata. Il dato dice altro: ieri Wall Street era chiusa e l'Euro Stoxx 50 ha scambiato 15,9 milioni di pezzi contro 24,8 il giorno prima. Per noi, quando i compratori sono pochi anche ordini piccoli spostano molto i prezzi, e un movimento forte pesa meno di quanto sembri.",
                   "Il rimbalzo ha avuto protagonisti precisi e concentrati in pochi settori. Stellantis ha guadagnato l'8,8% dopo uno studio di JPMorgan sul settore. Prysmian il 6,6% dopo il via libera della Grecia all'elettrodotto sottomarino per il Dodecaneso, un giorno prima del rialzo del titolo. STMicroelectronics e Technoprobe oltre il 4% per la fiducia ritrovata sull'intelligenza artificiale.",
                   "Milano ha fatto meglio dell'Europa ma ha ancora strada. Con 48.362 punti il FTSE MIB resta sotto i 48.703 del 20/11, dopo aver toccato mercoledì i minimi da aprile. Il recupero di ieri non ha ancora cancellato la caduta della settimana.",
                   "Sul fronte dei titoli di Stato, lo spread tra BTP e Bund è sceso a 107 punti. L'Italia paga meno rispetto alla Germania, con il BTP al 4,32% e il Bund al 3,25%.",
                   "Oggi il test: Wall Street riapre fino alle 19:00 e dice se i prezzi di ieri reggono con scambi più normali. Per questo conta il volume, non solo il prezzo."],
         "fonte": "Fonti: ANSA, SoldiOnline; volumi e chiusure dell'Euro Stoxx 50 da EODHD.",
         "guardare": "La prova è il volume. Se oggi, con Wall Street aperta, gli scambi salgono e i prezzi tengono, ieri era un ritorno vero dei compratori; se i prezzi cedono, era un rimbalzo di mercato sottile."},
        {"chiave": "oro", "tema": "Materie prime", "breve": "oro, metà del crollo",
         "titolo": "L'oro recupera metà della caduta dal 17/11 ma resta lontano dai massimi",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_oro.png", "x": [d(x) for x in _GX], "soggetto": "oro", "ruolo": "storia",
                     "titolo": "Dopo il crollo del 20/11 l'oro ha ripreso metà del terreno perso",
                     "sottotitolo": "Oro future, chiusure ($)", "soglie": [(3864.2, "17/11"), (3515.4, "20/11")],
                     "serie": [("Oro future", _GV, "#F26B1D")]},
         "numero": "+4,3%: il rialzo dell'oro future ieri, il maggiore dal 3 febbraio. Cade su una settimana in cui il metallo aveva perso il 9,0% fino al 20/11.",
         "perche": "A nostro avviso il rimbalzo è soprattutto tecnico. Dopo la caduta del 9,0% fino al 20/11 l'oro ha ripreso metà del terreno perso, mentre l'inflazione USA più alta del previsto resta un freno.",
         "quindi": "Sopra i 3.864 dollari del 17/11 l'oro cancellerebbe la caduta; sotto i 3.515 del 20/11 la riaprirebbe.",
         "testo": ["Un oro che sale mentre il mercato scommette quasi al 100% su un rialzo Fed sembra una contraddizione. Di solito i tassi alti lo frenano: chi tiene oro non incassa interessi, e un titolo di Stato che li paga diventa più attraente. Ieri è successo il contrario del solito. A nostro avviso pesa di più il rimbalzo dopo la caduta che un cambio di giudizio sui tassi.",
                   "La salita viene dopo una caduta. Tra il 17 e il 20/11 il future era passato da 3.864 a 3.515 dollari, e nelle sedute successive ne ha ripresi 172. Se i rendimenti tornano a salire, il rimbalzo rischia di esaurirsi."],
         "fonte": "Fonti: The Company Chronicle; chiusure dell'oro future da FMP.",
         "guardare": "Contano i rendimenti dei Treasury alla riapertura di oggi: se salgono e l'oro tiene, il rimbalzo avrebbe un'altra ragione; se l'oro ricade, resta una correzione."},
        {"chiave": "petrolio", "tema": "Petrolio", "breve": "Brent nel corridoio",
         "titolo": "Il Brent resta tra 89 e 96 dollari nonostante gli attacchi nel Golfo",
         "misura": "mezzo",
         "grafico": {"tipo": "linee", "file": "c_brent.png", "x": [d(x) for x in _BX], "soggetto": "Brent", "ruolo": "storia",
                     "titolo": "Dal 9/11 il Brent chiude sempre dentro uno stesso corridoio",
                     "sottotitolo": "Brent future, chiusure ($)", "soglie": [(95.84, "13/11"), (89.37, "23/11")],
                     "serie": [("Brent", _BV, "#111111")]},
         "numero": "6,47 $: l'ampiezza del corridoio delle chiusure dal 9/11, tra 89,37 e 95,84 dollari.",
         "perche": "Per Bloomberg il rialzo del 25/11 (+3,5% a 94,61 dollari) viene dall'escalation di attacchi in Medio Oriente. Il calo del 23/11 era dovuto agli investitori che chiudevano le coperture dopo che Trump aveva lasciato più tempo ai colloqui con l'Iran.",
         "quindi": "Una chiusura sopra i 95,84 dollari del 13/11 direbbe che il mercato ha cambiato idea sul rischio forniture; sotto gli 89,37 del 23/11 tornerebbe a prevalere la speranza nei colloqui.",
         "testo": ["Gli attacchi si ripetono e il prezzo no. Di solito conta quanto una notizia cambia le forniture reali. Un attacco che ferma poco e per poco sposta il prezzo di una seduta; uno che blocca le consegne lo sposta per settimane. Da due settimane il mercato continua a trattare le notizie del Golfo come rumore di breve durata.",
                   "Per i paesi importatori conta anche il motivo del rincaro. Un petrolio che sale per carenza di offerta è di norma un costo secco per i paesi che lo importano. Uno che sale per domanda forte può accompagnarsi a borse in rialzo."],
         "fonte": "Fonti: Rigzone (Bloomberg); chiusure del Brent future da FMP.",
         "guardare": "Contano la prossima chiusura sopra o sotto i bordi del corridoio."},
    ],
    "scommessa": {"tesi": "Con noi: le borse sono rimbalzate dopo il crollo di venerdì scorso, in Asia, in Europa e a Wall Street. Contro: l'inflazione è uscita più calda del previsto e il rialzo della Fed di dicembre è quasi certo. Da qui a lunedì: la seduta corta di oggi a Wall Street.",
                  "lunedi": False, "venerdi": True, "settimana_prec": None},
    "parole": [("Fondo di stabilizzazione", "Una riserva pubblica con cui lo Stato compra azioni per frenare una caduta troppo rapida."),
               ("Freno automatico (sidecar)", "Sospende per qualche minuto gli acquisti o le vendite dei programmi di borsa quando il mercato si muove troppo in fretta."),
               ("Volumi", "Il numero di pezzi scambiati in una seduta: con pochi volumi anche ordini piccoli spostano i prezzi."),
               ("Rimbalzo tecnico", "Una risalita dopo una forte discesa, che non dice ancora che il motivo della caduta sia finito."),
               ("Corridoio di prezzo", "L'intervallo tra il minimo e il massimo in cui un prezzo resta per un po' di sedute."),
               ("Memoria per GPU", "La memoria veloce delle schede grafiche, che serve ai programmi di intelligenza artificiale.")],
    "fonti": [
        ("Dati di mercato", "Financial Modeling Prep (indici USA, Nikkei, Hang Seng, VIX, Brent e oro future, curva del Tesoro USA); Alpha Vantage (EUR/USD, ACWI); EODHD (Euro Stoxx 50); ANSA (FTSE MIB e spread con la Germania); stampa coreana per il Kospi."),
        ("Prima pagina e mercati", "Stampa coreana, ANSA, SoldiOnline, Al Jazeera, The Company Chronicle, political.org."),
        ("Calendario e agenda", "BigGo Finance, political.org."),
        ("Approfondimenti", "Europa e Italia: ANSA, SoldiOnline, EODHD. Materie prime: The Company Chronicle. Petrolio: Rigzone (Bloomberg)."),
        ("La scommessa", "Chiusure di FMP, Alpha Vantage ed EODHD; forchette calcolate dalla volatilità delle ultime 20 sedute."),
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
