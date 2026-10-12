# Gommberg Terminal Daily - Istruzioni di redazione (template v5)

Rassegna mattutina dei mercati globali in PDF, stile Bloomberg, in italiano. La legge Paolo e la condivide con altre persone: deve essere professionale e senza errori. Il riferimento visivo e di contenuto è l'edizione n. 001 (script `edizione_modello_2026-10-12.py`): ogni edizione ne copia struttura, componenti e tono, sostituendo i contenuti.

## 1. Identità e file
- Testata: GOMMBERG TERMINAL DAILY, sottotitolo "Mercati globali | Rassegna quotidiana" (nel motore, non toccare).
- Edizione: numero progressivo dei giorni lun-ven dal 12/10/2026 (funzione `numero_edizione`). Nome file: `AAAA-MM-GG Gommberg Terminal Daily #NNN.pdf` (funzione `nome_file`).
- `set_meta(oggi, nota)`: la nota dice a quando si riferiscono i dati, es. "Chiusure al 13 ottobre; mattina del 14 ottobre dove indicato".

## 2. Struttura fissa (6 pagine A4, ordine e titoli di sezione invariati)
Kicker (arancione, maiuscolo) e titolo di sezione sono fissi; dove c'è "<...>" cambia solo quella parte.

**Pag. 1 - Prima pagina**
1. `ticker()` con 7 caselle in quest'ordine: MSCI ACWI (ETF), S&P 500, EURO STOXX 50, UST 10 ANNI, BRENT FUTURE, EUR/USD, VIX. Valore di chiusura + variazione del giorno con segno ("+0,6% g", "+2 pb g", "-0,57 g").
2. Kicker "TOP STORY" + titolo h1 (massimo 2 righe, niente parole orfane) + "dek" di 2-3 righe.
3. `side_by_side`: a sinistra `box("In 30 secondi", 3 punti)`, a destra `box("Stamattina", 4-5 righe)` con future USA, Europa, Asia, petrolio, EUR/USD, ciascuna con l'orario del dato.
4. `section("Le notizie del giorno", "Top news")` + `news_grid` con 8 notizie (tag, titolo, 2-3 righe con numeri e perché conta). Ordine per importanza per i mercati.

**Pag. 2 - Mercati**
5. `section("Cruscotto: come stanno andando i mercati", "Mercati")`: `dash_table` con gruppi Globale (ACWI), Stati Uniti (S&P 500, Nasdaq Comp., Dow, Russell 2000), Europa (Euro Stoxx 50, FTSE 100), Asia (Nikkei 225, Hang Seng, Kospi, Shanghai). Colonne Ultimo | Data | 1 g | 1 sett. | Da inizio anno. A destra il grafico a barre della variazione settimanale (o da inizio settimana) degli indici.
6. `section("Tassi, cambi, materie prime e volatilità", "Cross-asset")`: Treasury 2/10/30 anni (in pb), EUR/USD, Brent, WTI, VIX con 1 g, 1 sett., 1 mese e una "Lettura" di poche parole.
7. `section("Quadro macro: <titolo>", "Il contesto")`: 4 paragrafi con attacco in grassetto (Utili, Fed, Energia, Europa o i temi del giorno).

**Pag. 3 - Catalizzatori**
8. `section("<La settimana scorsa | Ieri>: cosa ha mosso i mercati", "Catalizzatori conclusi | <periodo>")`: tabella Quando | Evento | Esito (dato contro attese) | Effetto sui mercati. Il lunedì copre la settimana precedente, gli altri giorni la seduta precedente. Chiude con `box("La settimana in una riga" o "La seduta in una riga", ...)`.
9. `section("Questa settimana: agenda e catalizzatori in arrivo", "Week ahead | <date>")`: tabella Quando (Roma) | Evento | Attese | Perché conta, dai giorni rimanenti della settimana (il venerdì aggiungi il lunedì successivo). La colonna Attese usa lo stile "celln" (non colorato). Evento principale in grassetto.

**Pag. 4 - Scenari, rischi, Treasury**
10. `section("Il bivio: scenari per <evento chiave>", "Scenari")`: Scenario | Prob.* | Fed | Treasury | Azionario | Dollaro (EUR/USD).
11. `section("Classifica dei rischi della settimana", "Risk map")`: 5 righe.
12. `section("Treasury: <titolo>", "Deep dive 1 | Tassi USA")`: `two()` con curva (oggi contro 2 settimane fa) e 2-10-30 anni nell'ultimo mese; tabella Scadenza | -1 mese | -2 sett. | ultimo | Var. 1 mese | Var. 2 sett. | Lettura; paragrafo "Lettura." con la soglia da guardare.

**Pag. 5 - Iran, petrolio, cambi**
13. `section("Iran: <titolo>", "Deep dive 2 | Geopolitica")`: 3 punti (Il quadro, La novità, Sul terreno) + tabella scenari (Prob.* | Petrolio | Borse).
14. `section("Petrolio: <titolo>", "Deep dive 3 | Energia")`: `chart_text` con Brent fisico EIA dal 2/2026 e linea del future; 3 punti (Future, Fisico, Spinte e freni).
15. `section("EUR/USD: <titolo>", "Deep dive 4 | Cambi")`: `chart_text` con EUR/USD ultimi ~5 mesi; 3 punti (Livello, Perché, Cosa può invertire il trend).

**Pag. 6 - Il gran finale**
16. `section(..., "Il gran finale | Forecast")`, vedi paragrafo 4.
17. `section("Glossario", "Per chi legge")`: 10 voci (tieni quelle del modello, aggiungi solo se nel numero compaiono sigle nuove).
18. `section("Fonti", "Note")`: un solo paragrafo "src" raggruppato per Dati di mercato / Notizie / Catalizzatori / Agenda.

Usa `PageBreak()` tra le pagine. Se un'appendice non ha novità: "Nessuna novità rilevante: quadro invariato rispetto a ieri" in una riga, ma aggiorna comunque dati e tabelle.

## 3. Dati: dove prenderli (verificati, mai a memoria)
- FMP `indexes` endpoint `index-historical-price-eod-light`: ^GSPC, ^IXIC, ^STOXX50E, ^FTSE, ^N225, ^HSI, ^VIX (funzionano). Non funzionano (piano): ^GDAXI, FTSEMIB.MI, ^FCHI, ^KS11, `quote`, `chart`.
- FMP `economics` endpoint `treasury-rates` (curva completa). FMP `commodity` endpoint `commodities-historical-price-eod-light` simbolo BZUSD (Brent future).
- Alpha Vantage (max 25 chiamate al giorno, 1 al secondo): TIME_SERIES_DAILY ACWI, FX_DAILY EUR/USD, CURRENCY_EXCHANGE_RATE EUR/USD (livello di stamattina), BRENT interval daily (= Brent fisico EIA spot FOB, non il future).
- Dow, Russell 2000 e da-inizio-anno USA: AP "How major US stock indexes fared" + data (es. via La Nación). Kospi, Shanghai e borse di stamattina: Reuters, Trading Economics, Newsquawk, investingLive.
- Basi da inizio anno: Euro Stoxx 50 5.796,22 (30/12/2025), FTSE 100 9.931,38, Nikkei 50.339,48 (30/12/2025), Hang Seng 25.630,55.
- Notizie, agenda, consensi: ricerche separate per argomento su Reuters, AP, Bloomberg, CNBC, WSJ, FT, investingLive, Trading Economics, ANSA, Teleborsa, Sole 24 Ore, siti ufficiali (Fed, BLS, società). Orari sempre in ora di Roma: Roma = ET+6, tranne dal 25 al 31 ottobre 2026 (Europa già all'ora solare, USA ancora no) quando è ET+5; dal 1° novembre torna ET+6.
- Regole di verità: ogni numero viene da una fonte recuperata oggi o da un calcolo in codice. Fonti in disaccordo: indica la fonte o ometti. Consensi divergenti (es. EPS delle banche): non riportarli se non confermati da due fonti. Non attribuire cause a un movimento di mercato senza una fonte che le indichi. Distingui piani e proposte da decisioni prese.

## 4. La scommessa della settimana (la parte che i lettori aspettano)
Registro nel repository: cartella `redazione/pronostici/`, un file JSON per settimana, nome `AAAA-MM-GG-settimana-<date>.json` (es. `2026-10-12-settimana-12-16-ottobre.json`). Si leggono e si scrivono come file normali nella copia clonata e si pubblicano con il commit del giorno (paragrafo 8). Un file per settimana: il verdetto della settimana precedente va nel file nuovo, i file vecchi non si modificano.

**Lunedì (o primo giorno lavorativo della settimana):**
1. Leggi il JSON della settimana precedente e calcola il verdetto con le chiusure del venerdì: per ogni strumento 1 punto se la direzione (segno rispetto alla base) è giusta, 1 punto se la chiusura è dentro il range. Aggiorna il punteggio stagionale.
2. Fai il nuovo pronostico per la chiusura di venerdì: per MSCI ACWI (ETF), S&P 500, Euro Stoxx 50, Treasury 10 e 2 anni, Brent future, EUR/USD. Range: S&P 500 = ±VIX/√52; gli altri = volatilità realizzata 20 sedute × √5 (calcolata in codice). Previsione puntuale e probabilità di rialzo sono giudizi redazionali motivati in una riga.
3. Salva il nuovo JSON in `redazione/pronostici/` (stesso schema del file del 12/10: edizione, data_pronostico, settimana, chiusura_riferimento, verdetto_previsto, previsioni[strumento, base, previsione, range, prob_rialzo, unita], regole_verdetto, punteggio_stagionale_prima_di_questa_settimana) e aggiungi il campo "verdetto_settimana_precedente" con i punti.
4. Pag. 6: titolo "La scommessa della settimana: dove chiudiamo venerdì <data>", sottotitolo "Il nostro pronostico: ..." (stile dek), grafico `c_forecast.png`, tabella delle previsioni, box "Le regole del gioco" e box "La pagella" con il verdetto della settimana precedente (es. "Settimana 12-16 ottobre: 9 punti su 14; direzione giusta 5 su 7") e il punteggio stagionale.

**Martedì-venerdì:**
- Leggi il JSON della settimana corrente. Pag. 6 diventa "La scommessa della settimana: a che punto siamo" con lo stesso grafico più un cerchio sul livello attuale e una tabella Strumento | Base | Previsione | Ultimo | Var. da base | Dentro il range? | Sulla strada giusta?. La previsione NON si cambia. Il venerdì aggiungi "Verdetto lunedì" e una frase autoironica se stiamo sbagliando.
- In prima pagina, nel box "In 30 secondi", il terzo punto può ricordare dove siamo sulla scommessa quando è rilevante.

## 5. Stile (obbligatorio)
- Solo trattino corto "-", mai trattini lunghi.
- Variazioni con segno esplicito: il motore le colora da solo (verde positivo, rosso negativo, grigio zero) negli stili cell, cellb, tk_c e nei box. Non mettere + o - davanti a cose che non sono variazioni. Per livelli attesi in agenda usa lo stile "celln".
- Numeri all'italiana (7.811,54; 5,24%). Escape "&" come "&amp;" nei Paragraph.
- Tono: Bloomberg, frasi brevi, numero e "perché conta". Probabilità soggettive sempre dichiarate "stime redazionali soggettive".
- Grafici: font DejaVu Sans, palette del modello (arancione #F26B1D, nero #111111, blu #1F5FA8, verde #1E7B3A, rosso #C62828), titoli brevi che stanno nella larghezza, etichette che non si sovrappongono.

## 6. Flusso di lavoro di ogni mattina
Tutto avviene nella copia clonata del repository PaoloGom/Gommberg-Terminal-Daily (cartella di lavoro `/home/claude/gtd`, kit in `/home/claude/gtd/redazione`). Google Drive non serve più.
1. **Kit.** Il kit è già su disco dopo il clone: `redazione/` contiene questo file, `gommberg_engine.py`, `charts.py`, `charts2.py`, `data.py` (dati del modello, da rigenerare ogni giorno), `edizione_modello_2026-10-12.py`, `controlli.py` e `pronostici/`. Lavora dentro una cartella di lavoro separata (es. `/home/claude/lavoro`) copiando lì i .py, così il repository riceve solo i file finali. Installa reportlab, matplotlib e svglib se mancano (pip install --break-system-packages reportlab matplotlib svglib). I grafici si salvano in PNG e SVG con lo stesso nome: il motore usa l'SVG vettoriale. Dopo il render comprimi con `qpdf --object-streams=generate --compress-streams=y in.pdf out.pdf`.
2. **Cosa è già uscito.** Leggi `edizioni.json` del repository (paragrafo 7): notizie, tesi e glossario delle edizioni precedenti.
3. **Dati e ricerca.** Raccogli i dati (paragrafo 3) chiamando direttamente gli strumenti FMP e Alpha Vantage. Se lo strumento Agent è disponibile, lancia in parallelo due agenti di ricerca con `model: "sonnet"`: (a) catalizzatori conclusi dall'ultima edizione con esiti e reazioni, (b) notizie della notte e di stamattina, future e borse con orario, agenda dei giorni rimanenti con orari e consensi. Passa a entrambi l'elenco delle notizie di ieri da non ripetere. Ogni fatto con fonte e URL, nessun dato inventato. Se Agent non c'è, fai le ricerche tu.
4. **Stesura.** Scrivi `edizione_AAAA-MM-GG.py` partendo dal modello, aggiorna `data.py` e i grafici, genera il PDF. Tutte le variazioni e i livelli nelle tabelle vengono da calcoli in codice sui dati scaricati, mai ricopiati a mano.
5. **Controlli automatici.** Aggiorna edizioni.json (paragrafo 8, punto 2), poi `python3 /home/claude/gtd/redazione/controlli.py "<pdf>" /home/claude/gtd/edizioni.json <N>` deve dire OK. Poi `pdftoppm -r 70` di tutte le pagine e guardale con Read: niente sovrapposizioni, niente pagine semivuote (salvo l'ultima), colori coerenti col segno.
6. **Revisione mirata** (paragrafo 10). Correggi, rigenera, ripeti i controlli del punto 5.
7. **Pubblicazione** (paragrafo 8), poi **consegna**: SendUserFile (status "proactive", display "render"), didascalia "Gommberg Terminal Daily #NNN - <data lunga>", poi 3 righe: notizia del giorno, evento da guardare oggi, stato della scommessa, più l'esito della pubblicazione ("Sito e archivio aggiornati" o il problema).
## 7. Niente ridondanze tra un'edizione e l'altra
Chi legge ogni giorno non deve ritrovare le stesse cose. Prima di scrivere, leggi `/home/claude/gtd/edizioni.json`: per ogni edizione passata contiene `notizie` (titoli delle 8 top news), `temi_deep_dive` (la tesi di ciascun approfondimento) e `glossario` (voci già spiegate). Poi:
- Top news: solo fatti nuovi dall'ultima edizione. Un tema già uscito torna solo con uno sviluppo nuovo, e il titolo dice qual è lo sviluppo ("Iran, Teheran apre sulle navi neutrali"), mai lo stesso titolo di ieri. Vietato ripetere numeri già dati se non sono cambiati.
- Catalizzatori conclusi: il martedì-venerdì solo la seduta precedente; ciò che era già nella tabella di ieri non si ripete.
- Agenda: eventi passati tolti; per gli eventi già presentati basta la riga aggiornata, il testo "perché conta" si riscrive solo se è cambiato qualcosa (consenso, orario, contesto).
- Quadro macro e deep dive (Treasury, Iran, Petrolio, EUR/USD): se la tesi è la stessa di ieri, aggiorna tabelle e grafici e scrivi una sola riga che dice cosa è cambiato rispetto a ieri (o "Nessuna novità rilevante: quadro invariato rispetto a ieri"); usa lo spazio liberato per l'argomento del giorno. Titoli di sezione: la parte variabile deve dire la novità, non ripetere quella di ieri.
- Scenari e Risk map: si aggiornano le probabilità e si scrive in una riga cosa le ha mosse; non si riscrive tutta la tabella se non cambia.
- Glossario: il lunedì le 10 voci standard; martedì-venerdì solo le sigle nuove comparse nel numero (se non ce ne sono, la sezione diventa una riga "Glossario completo nell'edizione del lunedì"). Lo spazio libero in pag. 6 va alla scommessa.
- Box "In 30 secondi": tre punti tutti nuovi rispetto a ieri.
- Il revisore (paragrafo 10) controlla anche questo: confronta il numero con le voci di `edizioni.json` dell'edizione precedente e segnala come errore bloccante ogni notizia o frase ripetuta senza novità.

## 8. Pubblicazione: sito pubblico e archivio online
**Sito pubblico (il link che Paolo condivide, si apre anche dal PC aziendale):** https://paologom.github.io/Gommberg-Terminal-Daily/ (maiuscole obbligatorie). Repository PaoloGom/Gommberg-Terminal-Daily, ramo main, pubblicato dalla radice. Il sito legge `edizioni.json` e i PDF in `pdf/`. Non modificare index.html, README.md né assets/.
**Archivio online su Claude (copia per Paolo):** https://claude.ai/artifact/MuwDrCHDGXuADtKtL7cFcH, stessa pagina e stesso edizioni.json.
1. Copia il PDF finale in `/home/claude/gtd/pdf/AAAA-MM-GG-gommberg-NNN.pdf` (nome senza spazi né "#").
2. Aggiungi a `/home/claude/gtd/edizioni.json` (array, una voce per edizione; non toccare le voci esistenti; se il numero esiste già, NON sovrascrivere: fermati e segnala l'anomalia nel messaggio finale, perché vuol dire che il numero di edizione è sbagliato) la voce:
   `{"numero": N, "data": "AAAA-MM-GG", "titolo": "<titolo h1>", "sommario": ["<3 punti del box In 30 secondi>"], "file": "pdf/AAAA-MM-GG-gommberg-NNN.pdf", "nome": "AAAA-MM-GG Gommberg Terminal Daily #NNN.pdf", "pagine": 6, "notizie": ["<8 titoli top news>"], "temi_deep_dive": {"treasury": "...", "iran": "...", "petrolio": "...", "eurusd": "..."}, "glossario": ["<voci spiegate in questo numero>"]}`. Testo semplice senza tag HTML (scrivi S&P, non &amp;).
3. Commit e push: `git -C /home/claude/gtd config user.name "PaoloGom"`, `git -C /home/claude/gtd config user.email "PaoloGom@users.noreply.github.com"` (mai l'email personale), `git -C /home/claude/gtd add pdf edizioni.json redazione/pronostici`, commit "Edizione #NNN - AAAA-MM-GG", `git -C /home/claude/gtd push origin main`. Se il push è rifiutato perché il remoto è avanti: `git pull --rebase origin main` e ripeti una volta. Verifica con `git -C /home/claude/gtd log origin/main -1`. Il sito si aggiorna da solo in 1-2 minuti.
4. Archivio online: strumento Artifact `action: "read"` con `url` dell'archivio (serve a registrare la lettura, senza la quale la pubblicazione viene rifiutata), poi `action: "publish"` con `url`, `file_path` = `/home/claude/gtd/redazione/archivio_claude.html` (la pagina dell'archivio, da non modificare), `files` = {"edizioni.json": "/home/claude/gtd/edizioni.json", "pdf/AAAA-MM-GG-gommberg-NNN.pdf": "<percorso del pdf>"}. Non passare `capabilities` né `icon`. Se la pubblicazione viene rifiutata perché esiste una versione più recente, la pagina non è cambiata: ripubblica con gli stessi parametri (fino a due volte). Verifica con `action: "list"`, `scope: "files"`: devono esserci il nuovo PDF e il nuovo edizioni.json.
5. Se un passaggio fallisce, riprova una volta; se fallisce ancora consegna comunque il PDF in chat e scrivi nel messaggio finale cosa non è stato aggiornato.
## 10. Revisione mirata (compromesso tra accuratezza e costo)
I numeri di mercato presi dalle API (FMP, Alpha Vantage) non si rivedono a mano: vengono da calcoli in codice; e `controlli.py` blocca gli errori meccanici. La revisione si concentra dove si sbaglia davvero: fatti di cronaca, date, orari, consensi, attribuzioni di causa, ripetizioni, e i numeri presi da fonti web (livelli intraday, cifre delle notizie).
- Se lo strumento Agent è disponibile: un solo agente revisore con `model: "sonnet"`, che non ha scritto il numero. Gli passi il testo del PDF (pdftotext) e l'elenco notizie dell'edizione precedente. Compito: verificare sul web al massimo 20 affermazioni, scelte tra quelle non prese dalle API (in priorità: top story, top news, orari e consensi dell'agenda, cifre su Iran e petrolio, catalizzatori conclusi), segnalare ripetizioni senza novità rispetto a ieri, e restituire SOLO gli errori bloccanti con fonte. Niente riscritture di stile.
- Il lunedì il revisore controlla in più il verdetto della scommessa e il nuovo pronostico (i calcoli si rifanno in codice).
- Senza Agent: controllo tu le stesse affermazioni, con lo stesso limite.
- Correggi tutto ciò che è bloccante; se una verifica non è conclusiva, togli il dettaglio o attribuiscilo alla fonte.
## 11. Note pratiche dal collaudo del 12/10
- Ora corrente: se non c'è uno strumento dedicato, usa `TZ=Europe/Rome date`.
- Il numero di edizione lo calcola `set_meta`; non forzarlo mai a mano.
- FMP non dà il WTI (CLUSD) né gli indici intraday: prendili da fonti web con l'orario (es. Reuters, TheStreet, CNBC) e falli rientrare nella revisione.
- Alpha Vantage: una chiamata al secondo, chiamale una dopo l'altra; la serie BRENT EIA si aggiorna con qualche giorno di ritardo, normale.
- Le chiusure europee di oggi non esistono la mattina: nel ticker e nel cruscotto usa le chiusure della seduta precedente e i dati di stamattina con l'ora.
- Consensi divergenti tra fonti (es. EPS delle banche): non riportarli.
- Tempi del collaudo: circa 20 minuti dall'avvio alla pubblicazione, revisore compreso (17 affermazioni verificate, 9 errori bloccanti trovati e corretti).
