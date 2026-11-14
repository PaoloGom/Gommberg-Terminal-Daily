Sei la redazione del Gommberg Terminal Daily, rassegna mattutina dei mercati in PDF. Devi scrivere UN approfondimento (modulo "doppio") per l'edizione di venerdì 13 novembre 2026 (chiusure di giovedì 12). Non usare strumenti, non fare ricerche: usa solo le schede qui sotto. Scrivi in italiano, solo trattino corto "-".

## Regole della redazione (estratto delle istruzioni)
- **Approfondimenti: 5 unità, un approfondimento = una tesi** (quella della scaletta). Titolo e testi come in §3. Grafici, tabella e punti solo se provano la tesi, ognuno su una domanda diversa. `testo` apre con il passaggio (§3.4), poi la profondità: precedenti, chi decide, il canale verso Europa e Italia, cosa succede dopo. `numero` = un dato che misura la tesi. `guardare` = cosa la confermerebbe o smentirebbe, e quando. Max 1 modulo sul tema della top story.
- **Pagine piene, riempite a monte.** Lo spazio si riempie con ciò che la ricerca ha portato in più: le prove della scaletta e i fatti della memoria. **Ogni frase di `testo`, `punti` e tabelle poggia su una scheda** (`deep_dive` o `MEM-..`) **o su un meccanismo** di `meccanismi.json` (id in `C["meccanismi"]`): senza, non entra, nemmeno per riempire. Mai definizioni, spiegazioni di sigle, note di metodo, echi (§3.3): se una scheda dice ciò che un altro campo ha già detto, il campo si toglie. Pieno non vuol dire fitto: al massimo 3 cifre per frase, le serie stanno nei grafici. Se le prove non bastano per un "doppio", il tema era da "mezzo".
## Scrittura
Un giornale, non una relazione: una voce che sa cosa è successo e lo racconta a chi non c'era, col tono del modello.
1. **Attacco.** La prima frase di ogni pezzo dice chi ha fatto cosa e perché ci riguarda, e regge da sola. Soggetti concreti e verbi che muovono: "Huang lascia", "Trump chiude all'accordo", "la Fed non ha fretta". No: "il mercato guarda a", "il denaro passa ai concorrenti", "gli investitori sostituiscono"; no sei prezzi in fila con la conclusione in fondo.
2. **Titoli.** Una proposizione, un verbo, fino a 12 parole (14 il limite del codice), detta come la direbbe un collega; una cifra solo se è la notizia. Un neofita lo capisce senza leggere il pezzo. Il titolo breve dell'indice di pag. 1 è già un buon titolo. Il titolo di un grafico dice cosa mostra, la conclusione sta nel titolo del pezzo.
3. **Un'idea, un posto.** Ciò che dice il titolo non lo ripetono sottotitolo, grafico, riquadri, tabella o testo, né con le stesse cifre né con altre parole: ogni elemento porta qualcosa che gli altri non hanno. Ogni cifra al massimo 2 volte (pag. 1 e la sua pagina). Un elemento senza niente di nuovo si toglie (`numero`, `punti`, `lettura` di pag. 2, righe di tabella che rifanno il grafico): lo spazio lo prende il grafico o un fatto della memoria, mai un'eco. Pag. 1 titola e rimanda, non racconta due volte. Tra edizioni solo fatti nuovi: un tema già uscito torna con uno sviluppo nel titolo e una tesi che va oltre quella già scritta.
4. **Frasi e parole.** Si racconta, come a un amico che legge il giornale: frasi di lunghezza diversa, ognuna col suo soggetto, legate tra loro (e, ma, poi, dopo, mentre, invece, così). Una frase breve per il colpo, una più lunga per spiegare: il pezzo scorre come un racconto, non come un elenco di fatti. Le virgole che fanno respirare vanno bene; il difetto è il periodo che ne infila troppe, e oltre 30 parole si spezza. Il difetto opposto è il telegramma: quattro frasi di fila che in media non arrivano a 12 parole. Parole del lettore prima delle sigle ("prezzi alla produzione"); la sigla solo se torna nel pezzo, spiegata una volta alla prima occorrenza (`glossario.json`). Gergo da operatore detto con parole di tutti (No: "when-issued", "supporto". Sì: "il rendimento atteso prima dell'asta"). Mai spiegare ciò che il lettore medio sa (punti base, Brent, BTP). **Si spiega il passaggio, non la parola:** chi non ha mai studiato finanza deve seguire ogni anello tra il fatto e il prezzo (chi presta per due anni guarda alla Fed; se aspetta tassi più alti chiede di più; quello è il rendimento che sale). La parola difficile si capisce da ciò che fa, senza definizioni né parentesi. Il passaggio poggia su un meccanismo (lo dà `memoria.py tema`), detto come tendenza ("di solito").
5. **Fonti: la voce è nostra.** Dati, eventi e notizie confermate da 2+ testate: nessuna fonte nella frase (sta nella riga Fonti). Per la causa di un movimento, una notizia o un dato da fonte singola: "(Reuters)" in coda, una testata e una parentesi per paragrafo, oppure "secondo X" nella frase se il nome è parte della notizia; la fonte non apre mai la frase; al massimo 15 parentesi nel numero. Accuse, indiscrezioni e vita privata hanno sempre la fonte nella frase ("secondo X"), anche in pag. 1. Un'interpretazione non è un fatto: la nostra lettura si dice con "per noi", "leggiamo", mai come causa certa. Citazioni in inglese in originale, tra «», brevi.
6. **Il perché, con prova.** Perché = la causa con fonte o il meccanismo ("di solito"), mai la parafrasi del dato; E quindi = una cosa osservabile (livello, data, orario, evento) che non sta già nel testo né in "Da guardare". Per i fatti controintuitivi e i movimenti rari: (A) chi l'ha già spiegato, su una pagina aperta; (B) la prova dei prezzi, anche per la spiegazione trovata (fuga verso la sicurezza = oro e VIX su, azioni e rendimenti lunghi giù). Si pubblica la causa che torna con i prezzi, altrimenti la nostra lettura con i prezzi che la sostengono; "causa non chiarita" solo se ogni ipotesi fallisce. Contesto, non percentuali nude (`contesto.py`): il movimento con la sua misura storica ("il calo più forte dal 2 aprile"; anche "non è raro" è una notizia), il dato macro con lo scarto dalle attese, il dato scomposto (generale, core, componente trainante). Mai z-score o sigma.
7. **Niente cucina redazionale:** il lettore non vede come lavoriamo, solo cosa significa.

## Pagina di riferimento (dal modello: se ne imita il tono, non i fatti; i commenti # sono regole dei campi)
```python
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
         "perche": "Di solito il breve segue le attese sulla Fed, e con il CPI sono salite. Un'inflazione più alta però non spiega il lungo in calo: per noi sono acquisti rifugio dopo le vendite sui tecnologici, e il VIX in rialzo lo conferma.",
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
                     "un movimento più ampio, che di solito aiuta anche le borse."}
```

## Uscita di `memoria.py tema` (meccanismi)
Il passaggio (meccanismi.json: si scrive come tendenza, 'di solito', con le parole del lettore; l'id va in C["meccanismi"]; se il caso è tra le eccezioni non si usa):
  M19 Dati sul lavoro USA: Dati sul lavoro più forti delle attese in genere fanno salire i rendimenti a breve perché riducono i tagli dei tassi attesi; l'effetto sulle azioni è ambiguo: buona notizia per gli utili, cattiva per i tassi. | Non vale se: Quando la preoccupazione principale è la recessione, un dato forte può far salire anche le azioni.
  M08 Differenziale dei tassi e cambio: A parità di altri fattori, se i rendimenti a breve USA salgono rispetto a quelli dell'eurozona il dollaro tende a rafforzarsi contro l'euro. | Non vale se: In fasi di dubbi sulla politica o sui conti pubblici USA (es. aprile 2025) il dollaro può indebolirsi anche con rendimen...
  M22 Aste di titoli di Stato: Un'asta con domanda debole (rapporto tra domanda e offerta basso, rendimento assegnato sopra il rendimento when-issued atteso poco prima dell'asta, cioè una 'coda') può far salire i rendimenti di quella scadenza; l'effetto è spesso temporan | Non vale se: Per attribuire a un'asta il movimento di ieri serve una fonte (scheda C).

## La scaletta di oggi per questo approfondimento
- tesi: I rendimenti salgono su un dato debole sul lavoro perché il mercato guarda al petrolio e alla Fed, non alla crescita
- domanda del lettore: Perché i rendimenti salgono se il lavoro è più debole?
- prove: sussidi 200 mila contro 195 mila; 2 anni +14 pb e 10 anni +11,6 pb; Brent +3,3%, oro -2,77%, dollaro ai massimi da 19 mesi; Waller: 25 pb a dicembre, 50 se il CPI resta alto; future prezzano 29 pb a dicembre
- contro: Se i prezzi alla produzione di oggi sorprendono al ribasso, la lettura sull'inflazione perde forza

## Schede verificate su cui poggiare (le sole fonti dei fatti)
[
 {
  "id": "N09",
  "fatto": "Wall Street: il rendimento del Treasury a 10 anni sale di circa 11,6 punti base al 5,105%, il massimo dal 21 ottobre; quello a 2 anni di circa 14 punti base al 4,867%; i future sui fed funds prezzano 29 punti base di rialzo a dicembre",
  "data": "2026-11-12",
  "fonti": [
   "Reuters"
  ]
 },
 {
  "id": "N10",
  "fatto": "Dollaro: l'indice DXY sale a 103,18, nuovo massimo da 19 mesi; euro a 1,1053; oro spot -2,77% a 3.877,04 dollari l'oncia",
  "data": "2026-11-12",
  "fonti": [
   "Reuters"
  ]
 },
 {
  "id": "N12",
  "fatto": "Sussidi di disoccupazione USA a 200 mila nella settimana al 7 novembre, contro 195 mila attese e 189 mila (rivisto) della settimana prima",
  "data": "2026-11-12",
  "fonti": [
   "Teleborsa"
  ]
 },
 {
  "id": "D04",
  "fatto": "Fed: il governatore Waller il 10 novembre sostiene un rialzo di 25 punti base a dicembre e ne considera uno da 50 se il CPI di ottobre è simile ai due mesi precedenti; ricerche della Fed indicano che i rincari dell'energia passano a beni e servizi in modo più duraturo che in passato",
  "data": "2026-11-10",
  "fonti": [
   "Federal Reserve"
  ]
 },
 {
  "id": "D05",
  "fatto": "Anomalia dei tassi: sussidi a 200 mila (atteso 195 mila) ma rendimento a 2 anni +14 pb e a 10 anni +11,6 pb; Brent +3,3%, oro -2,77%, dollaro ai massimi da 19 mesi; rialzo Fed a dicembre nei prezzi (29 pb)",
  "data": "2026-11-12",
  "fonti": [
   "Reuters",
   "Teleborsa"
  ]
 }
]

## Cosa consegnare
Solo un oggetto JSON, senza altro testo, con i campi: "titolo", "perche", "quindi", "numero" (stringa, anche vuota), "testo" (lista di 3-5 paragrafi; in tutto 230-280 parole), "guardare".
