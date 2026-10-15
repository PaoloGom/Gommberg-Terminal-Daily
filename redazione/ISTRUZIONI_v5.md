# Gommberg Terminal Daily - Istruzioni di redazione v5 (ARCHIVIO: via di ritorno. In vigore: ISTRUZIONI.md v6)

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
9. `section("Questa settimana: agenda e catalizzatori in arrivo", "Week ahead | <date>")`: tabella Quando (Roma) | Evento | Attese | Perché conta, dai giorni rimanenti della settimana (il venerdì aggiungi il lunedì successivo). La colonna Attese usa lo stile "celln" (non colorato). Evento principale in grassetto. Un solo evento per riga (al massimo 10 righe): mai più eventi nella stessa riga, perché le colonne Attese e Perché conta devono riferirsi a quell'evento; "-" dove non c'è un consenso.

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
- Basi da inizio anno: ultima chiusura dell'anno precedente, presa in codice dalla serie storica (FMP `index-historical-price-eod-light` con from/to sull'ultima settimana di dicembre). Per il 2026: Euro Stoxx 50 5.796,22 (30/12/2025), FTSE 100 9.931,38, Nikkei 50.339,48 (30/12/2025), Hang Seng 25.630,55. Dal primo giorno di borsa di gennaio si usa l'anno nuovo: mai le basi dell'anno prima.
- Notizie, agenda, consensi: ricerche separate per argomento su Reuters, AP, Bloomberg, CNBC, WSJ, FT, investingLive, Trading Economics, ANSA, Teleborsa, Sole 24 Ore, siti ufficiali (Fed, BLS, società). Orari sempre in ora di Roma, convertiti in codice con `zoneinfo` (America/New_York, Asia/Tokyo, ecc. -> Europe/Rome) per la data dell'evento: la differenza con New York cambia due volte l'anno per alcune settimane (fine marzo e fine ottobre), e non va mai calcolata a mente. Per eventi in Asia o in città diverse dal solito (es. riunioni del FMI) scrivi anche dove si tengono.
- **Fonti ammesse:** `redazione/fonti.json`. Livello 1 (Reuters, AP, Bloomberg, FT, WSJ, CNBC, ANSA, Sole 24 Ore, siti ufficiali): basta una fonte. Livello 2 (TheStreet, Milano Finanza, investingLive, Trading Economics...): servono due testate indipendenti. Fonti vietate (aggregatori, blog, siti che ripubblicano altri) e domini non in elenco: mai da soli. Se una fonte nuova sembra seria ma non è in elenco, non usarla: annotala nel registro del giorno (`redazione/fatti/AAAA-MM-GG.json`, voce `fonti_da_valutare`), senza dirlo a Paolo.
- **Freschezza:** in top story, top news e catalizzatori vanno solo eventi accaduti dopo l'edizione precedente. La data che conta è quella dell'evento, non dell'articolo: un articolo di oggi che riprende un fatto di giorni fa non è una notizia di oggi (collaudo: dato OPEC di settembre presentato come nuovo). L'orario di un live blog è l'ora di pubblicazione, non dell'evento.
- **Nel dubbio si toglie:** meglio una notizia in meno che una sbagliata. Un fatto non confermato non si scrive, nemmeno con il condizionale.
- Regole di verità: ogni numero viene da una fonte recuperata oggi o da un calcolo in codice. Fonti in disaccordo: indica la fonte o ometti. Consensi divergenti (es. EPS delle banche): non riportarli se non confermati da due fonti. Non attribuire cause a un movimento di mercato senza una fonte che le indichi. Distingui piani e proposte da decisioni prese.

## 4. La scommessa della settimana (la parte che i lettori aspettano)
È un laboratorio a sé: `redazione/scommessa/`. Prima di toccarlo leggi:
- `scommessa/METODO.md`: metodo, backtest, regole;
- `scommessa/metodo.json`: la configurazione in vigore.

**Regole generali:**
- Tutti i numeri della scommessa (range, sigma, probabilità, verdetto, pagella) li producono gli script, e pag. 6 la costruisce `pagina6.py`: niente calcoli o tabelle a mano.
- Per pag. 6 vale questo paragrafo, non la pag. 6 dell'edizione modello.
- Gli script si lanciano dentro il repository (`cd /home/claude/gtd/redazione/scommessa`), perché `dati/`, `registro.csv`, `PAGELLA.md`, `pagella.json` e `../pronostici/` vanno committati.
- Grafici e PDF vanno nella cartella di lavoro (`mkdir -p /home/claude/lavoro`).
- Registro delle settimane: `redazione/pronostici/AAAA-MM-GG-settimana.json`, con la data del lunedì.
- Chiavi uguali ovunque: `acwi`, `spx`, `sx5e`, `ust10`, `ust2`, `brent`, `eurusd` (più `vix` solo in `nuovi.json`).

**Lunedì (o primo giorno di borsa della settimana):**
1. **Aggiorna la storia.** Scrivi `nuovi.json` con le chiusure ufficiali dei giorni dopo l'ultima data di ogni file in `dati/`, fino a venerdì compreso. Formato: `{"spx": [["2026-10-16", 7850.12], ...], ...}`.
   - **Fonti:**
     - `spx`, `sx5e`, `vix`: FMP `index-historical-price-eod-light` con from/to;
     - `brent`: FMP `commodities-historical-price-eod-light`, simbolo BZUSD;
     - `ust10`, `ust2`: FMP `treasury-rates`, colonne year10 e year2;
     - `eurusd`: Alpha Vantage `FX_DAILY`, colonna close. Non FMP forex, che ha anche righe del weekend;
     - `acwi`: Alpha Vantage `TIME_SERIES_DAILY`.
   - **Mai la riga con la data di oggi:** FMP la restituisce già, ma è un valore intraday. Lo script la rifiuta.
   - **Poi:** `python3 aggiorna_dati.py nuovi.json`. Valida tutto prima di scrivere.
2. **Verdetto della settimana chiusa.** `python3 valuta.py --settimana ../pronostici/<lunedì scorso>-settimana.json --verdetto --json /home/claude/lavoro/verdetto.json`.
   - Se venerdì un mercato era chiuso, aggiungi `--festivo <chiavi separate da virgole>` (per esempio `--festivo ust10,ust2`), oppure `--festivo tutti`.
   - Lo script aggiorna `registro.csv`, `PAGELLA.md` e `pagella.json`.
   - Se si ferma per dati mancanti, aggiorna i dati: non aggirarlo.
   - Il primo lunedì del metodo (19/10/2026) il verdetto riguarda il file `2026-10-12-settimana.json`.
3. **Pronostico nuovo.**
   - **Livelli possibili:** `python3 pronostico.py --origine <venerdì scorso> --prova` stampa sigma e i livelli a +-0,1, 0,3 e 0,5 sigma.
   - **`redazione.json`:** una previsione dentro quei limiti per ciascuno dei 7 strumenti, con un motivo di una riga, per esempio `{"spx": {"previsione": 7845, "motivo": "Banche solide e CPI in linea"}, ...}`.
     - Nel motivo niente segni +/- davanti ai numeri.
     - La direzione è obbligatoria, ed è la vera scommessa: sceglila guardando agenda, notizie e scenari, non per abitudine.
   - **Poi:** `python3 pronostico.py --origine <venerdì scorso> --redazione redazione.json`.
     - Scrive `../pronostici/<lunedì>-settimana.json`.
     - Non sovrascrive mai un registro esistente: `--forza` si usa solo per correggere un errore della stessa mattina, prima della pubblicazione.
     - Se una previsione esce "AGGIUSTATA", il livello pubblicato è quello del registro: il motivo deve restare vero.
4. **Grafico:** `python3 grafico.py ../pronostici/<lunedì>-settimana.json /home/claude/lavoro/c_forecast.png`. Scrive PNG e SVG.
5. **Pag. 6.** Nello script dell'edizione:
   ```python
   import sys, json; sys.path.insert(0, "/home/claude/gtd/redazione/scommessa")
   from pagina6 import pagina6_lunedi
   story += pagina6_lunedi(reg, verdetto, pagella, tesi="<una frase con la tesi della settimana>",
                           grafico="c_forecast.png", settimana_prec="<es. 12-16 ottobre>")
   ```
   - `reg`, `verdetto`, `pagella` sono i JSON caricati: registro nuovo, `verdetto.json`, `pagella.json`.
   - `verdetto` è None se non c'è una settimana precedente.
   - Poi Glossario e Fonti come sempre.

**Martedì-venerdì:**
1. **`attuali.json`:** l'ultimo valore di ogni strumento con data, e ora se è un livello di stamattina. Per esempio `{"spx": [7830.1, "2026-10-19"], "brent": [104.2, "2026-10-20", "08:15"], ...}`.
   - Uno strumento senza valore nuovo si omette: lo script usa la base e lo segna come fermo.
   - Le chiavi sbagliate fanno fermare lo script.
2. **Poi lancia:**
   - `python3 valuta.py --settimana ../pronostici/<lunedì>-settimana.json --attuali attuali.json --json /home/claude/lavoro/stato.json`;
   - `python3 grafico.py ../pronostici/<lunedì>-settimana.json /home/claude/lavoro/c_forecast.png /home/claude/lavoro/stato.json`.
3. **Pag. 6:** `from pagina6 import pagina6_settimana`, poi `story += pagina6_settimana(reg, stato, tesi="<una frase: a che punto siamo>", grafico="c_forecast.png", venerdi=<True il venerdì>)`.
   - La previsione non cambia mai durante la settimana.
   - Il venerdì il box ricorda il verdetto di lunedì. Nella tesi è ammessa una frase autoironica se stiamo sbagliando.
- In prima pagina, nel box "In 30 secondi", il terzo punto può ricordare dove siamo sulla scommessa quando è rilevante.

**Collaudi e prove:** non scrivono mai nel registro vero.
- Per il verdetto si usa `--prova`, che calcola senza scrivere `registro.csv` né `PAGELLA.md`.
- Il pronostico va in una cartella fuori dal repository, con `--uscita`.

**Revisione periodica.** Il lavoro più dettagliato lo fa Claude su richiesta di Paolo. Ogni 26 settimane (la prima ad aprile 2027), o se la copertura dal vivo in `PAGELLA.md` esce da 55-80% dopo almeno 20 settimane:
- si rilancia `backtest.py` sullo storico completo (vedi METODO.md);
- si applica la regola di adozione di `metodo.json`;
- si aggiorna `METODO.md`.

L'edizione quotidiana non cambia mai il metodo da sola.

## 5. Stile (obbligatorio)
- Solo trattino corto "-", mai trattini lunghi.
- Variazioni con segno esplicito: il motore le colora da solo (verde positivo, rosso negativo, grigio zero) negli stili cell, cellb, tk_c e nei box. Non mettere + o - davanti a cose che non sono variazioni. Per livelli attesi in agenda usa lo stile "celln".
- Numeri all'italiana (7.811,54; 5,24%). Escape "&" come "&amp;" nei Paragraph.
- Tono: Bloomberg, frasi brevi, numero e "perché conta". Probabilità soggettive sempre dichiarate "stime redazionali soggettive".
- Grafici: font DejaVu Sans, palette del modello (arancione #F26B1D, nero #111111, blu #1F5FA8, verde #1E7B3A, rosso #C62828), titoli brevi che stanno nella larghezza, etichette che non si sovrappongono.

## 6. Flusso di lavoro di ogni mattina
Tutto avviene nella copia clonata del repository PaoloGom/Gommberg-Terminal-Daily (cartella di lavoro `/home/claude/gtd`, kit in `/home/claude/gtd/redazione`). Google Drive non serve più.
0. **Giorno di uscita?** Se la data di oggi è in `FESTIVI` di `gommberg_engine.py` (borse USA ed europee chiuse insieme), non si fa l'edizione: manda a Paolo una riga ("Oggi borse chiuse: niente Gommberg, ci rivediamo al prossimo giorno di borsa") e fermati. Negli altri festivi parziali (es. Lunedì dell'Angelo, Thanksgiving) l'edizione esce e i mercati chiusi si scrivono "chiuso", mai "0,0%". A dicembre di ogni anno aggiungi a `FESTIVI` le date dell'anno dopo e segnalalo nel messaggio finale.
1. **Kit.** Il kit è già su disco dopo il clone: `redazione/` contiene questo file, `gommberg_engine.py`, `charts.py`, `charts2.py`, `data.py` (dati del modello, da rigenerare ogni giorno), `edizione_modello_2026-10-12.py`, `scommessa/` (laboratorio della scommessa), `controlli.py`, `controlli_dati.py`, `controlli_fatti.py`, `fonti.json`, `pronostici/` e `fatti/` (registro delle fonti). Lavora dentro una cartella di lavoro separata (es. `/home/claude/lavoro`) copiando lì i .py, così il repository riceve solo i file finali. Installa reportlab, matplotlib e svglib se mancano (pip install --break-system-packages reportlab matplotlib svglib). I grafici si salvano in PNG e SVG con lo stesso nome: il motore usa l'SVG vettoriale. Dopo il render comprimi con `qpdf --object-streams=generate --compress-streams=y in.pdf out.pdf`.
2. **Cosa è già uscito.** Leggi `edizioni.json` del repository (paragrafo 7): notizie, tesi e glossario delle edizioni precedenti.
3. **Dati e ricerca.** Raccogli i dati (paragrafo 3) chiamando direttamente gli strumenti FMP e Alpha Vantage. Se lo strumento Agent è disponibile, lancia in parallelo due agenti di ricerca con `model: "sonnet"`: (a) catalizzatori conclusi dall'ultima edizione con esiti e reazioni, (b) notizie della notte e di stamattina, future e borse con orario, agenda dei giorni rimanenti con orari e consensi. Passa a entrambi l'elenco delle notizie di ieri da non ripetere, la data dell'edizione precedente e l'elenco delle fonti di `fonti.json`. L'agente (b) porta 10-12 notizie candidate (non di più), ordinate per importanza, così le scartate si sostituiscono con le riserve senza nuove ricerche. Ogni agente restituisce SOLO schede in formato JSON (schema in testa a `controlli_fatti.py`): per ogni fatto data dell'evento, testata, URL, data di pubblicazione e la frase originale copiata dall'articolo (al massimo 30 parole). Niente riassunti, commenti o testo fuori dal JSON. Niente fatti senza scheda, nessun dato inventato. Se Agent non c'è, fai le ricerche tu con lo stesso formato.
   Dopo il download dei dati scrivi `dati.json` (schema in testa a `controlli_dati.py`) con le ultime osservazioni di ogni serie, il tipo (chiusura o intraday) e, dove esiste, il valore di una seconda fonte (es. EUR/USD da FMP e da Alpha Vantage). `python3 /home/claude/gtd/redazione/controlli_dati.py dati.json` deve dire OK: un dato fermo, vecchio o intraday segnato come chiusura si corregge prima di scrivere.
4. **Stesura.** Raccogli le schede in `fatti.json` (una scheda per ogni fatto non preso dalle API che finisce nel PDF: top story, top news, catalizzatori, agenda, cifre di macro e deep dive) e lancia `python3 /home/claude/gtd/redazione/controlli_fatti.py fatti.json /home/claude/gtd/edizioni.json AAAA-MM-GG --prima-della-revisione`: ogni fatto che non passa si toglie o si rifonda con fonti adeguate. Poi scrivi `edizione_AAAA-MM-GG.py` partendo dal modello, usando solo fatti con scheda, aggiorna `data.py` e i grafici, genera il PDF. Tutte le variazioni e i livelli nelle tabelle vengono da calcoli in codice sui dati scaricati, mai ricopiati a mano.
5. **Controlli automatici.** Aggiorna edizioni.json (paragrafo 8, punto 2), poi `python3 /home/claude/gtd/redazione/controlli.py "<pdf>" /home/claude/gtd/edizioni.json <N>` deve dire OK. Poi `python3 /home/claude/gtd/redazione/anteprima.py "<pdf>" /home/claude/lavoro/anteprima.png` e guarda con Read quell'unica immagine (le 6 pagine in griglia): niente sovrapposizioni, niente pagine semivuote (salvo l'ultima), colori coerenti col segno. Solo se nell'anteprima una pagina sembra avere un problema, rendi quella pagina a `-r 70` (`pdftoppm -f N -l N`) e guardala: mai tutte e sei.
6. **Revisione rafforzata** (paragrafo 10). Correggi, rigenera, ripeti i controlli del punto 5 e `controlli_fatti.py` senza `--prima-della-revisione`: deve dire OK.
6b. **Autocorrezione e cancello** (paragrafo 11): si pubblica solo ciò che supera tutti i controlli. Ciò che non li supera si corregge o si toglie in automatico, senza coinvolgere Paolo.
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
3. Commit e push: `git -C /home/claude/gtd config user.name "PaoloGom"`, `git -C /home/claude/gtd config user.email "PaoloGom@users.noreply.github.com"` (mai l'email personale), copia `fatti.json` in `redazione/fatti/AAAA-MM-GG.json` (registro delle fonti di ogni edizione, serve per gli errata), `git -C /home/claude/gtd add pdf edizioni.json redazione/pronostici redazione/fatti redazione/scommessa` (mai `redazione/collaudi` con dati di prova nel registro), commit "Edizione #NNN - AAAA-MM-GG", `git -C /home/claude/gtd push origin main`. Se il push è rifiutato perché il remoto è avanti: `git pull --rebase origin main` e ripeti una volta. **Verifica obbligatoria del push (il 13/10 l'edizione è finita nell'archivio Claude ma non sul sito):** `test "$(git -C /home/claude/gtd ls-remote origin refs/heads/main | cut -f1)" = "$(git -C /home/claude/gtd rev-parse HEAD)" && echo PUSH_OK`. Se non stampa PUSH_OK: leggi l'errore di `git push`, `git pull --rebase origin main`, ripeti il push e la verifica (fino a 3 tentativi in tutto). Il passo 4 (archivio Claude) si fa solo dopo PUSH_OK o dopo il terzo tentativo fallito. Il sito si aggiorna da solo in 1-2 minuti.
4. Archivio online: strumento Artifact `action: "read"` con `url` dell'archivio (serve a registrare la lettura, senza la quale la pubblicazione viene rifiutata), poi `action: "publish"` con `url`, `file_path` = `/home/claude/gtd/redazione/archivio_claude.html` (la pagina dell'archivio, da non modificare), `files` = {"edizioni.json": "/home/claude/gtd/edizioni.json", "pdf/AAAA-MM-GG-gommberg-NNN.pdf": "<percorso del pdf>"}. Non passare `capabilities` né `icon`. Se la pubblicazione viene rifiutata perché esiste una versione più recente, la pagina non è cambiata: ripubblica con gli stessi parametri (fino a due volte). Verifica con `action: "list"`, `scope: "files"`: devono esserci il nuovo PDF e il nuovo edizioni.json.
5. Se un passaggio fallisce, riprova una volta; se fallisce ancora consegna comunque il PDF in chat e scrivi nel messaggio finale cosa non è stato aggiornato.
6. Il messaggio finale contiene sempre la riga `Sito: aggiornato (commit <hash breve>)` oppure `Sito: NON aggiornato - <errore>`, e la riga `Archivio Claude: aggiornato` oppure `NON aggiornato`. Mai scrivere che il sito è aggiornato senza PUSH_OK.
## 10. Revisione rafforzata
I numeri presi dalle API (FMP, Alpha Vantage) non si rivedono a mano: vengono da calcoli in codice e li controllano `controlli_dati.py` e `controlli.py`. La revisione copre tutto il resto: fatti di cronaca, date, orari, consensi, attribuzioni di causa, ripetizioni, numeri presi da fonti web.
- Un solo agente revisore con `model: "sonnet"`, che non ha scritto il numero. Riceve il testo del PDF (pdftotext), `fatti.json`, `fonti.json`, la data e le notizie dell'edizione precedente.
- Compito, fino a 25 verifiche, in quest'ordine di priorità: (1) per OGNI scheda di top story, top news e catalizzatori aprire l'URL indicato e controllare che la citazione ci sia, che la data dell'evento sia giusta e che il testo del PDF dica la stessa cosa (stesse cifre, stesse date, niente cause aggiunte); (2) nell'agenda solo l'evento principale (orario e consenso); (3) conferma indipendente sul web solo per la top story; (4) segnalare ripetizioni senza novità rispetto all'edizione precedente e frasi del PDF senza scheda (questi due senza aprire pagine web). Le cifre su Iran, petrolio e consensi non coperte entro le 25 verifiche restano solo se la loro scheda viene da una fonte di livello 1; altrimenti si tolgono.
- Il revisore scrive l'esito in `fatti.json`: per ogni scheda `verifica` = "confermato", "errato" o "non_conclusivo" e `nota_revisore` con la fonte. Restituisce solo l'elenco degli errori, niente riscritture di stile. Attenzione: anche il revisore sbaglia (collaudo: contestò un fatto che la fonte confermava). Se contesta un fatto, ricontrolla tu la fonte originale prima di decidere; se resta il dubbio, il fatto si toglie.
- Il lunedì il revisore controlla che la tabella e la pagella di pag. 6 riportino esattamente i valori di `verdetto.json` e del registro della settimana (i calcoli li fanno gli script).
- Senza Agent: fai tu la stessa verifica, con lo stesso limite di 25.
- "errato": si corregge con la fonte giusta o si toglie. "non_conclusivo": si toglie dal PDF (o si attribuisce alla fonte e si rifà la verifica). Le correzioni seguono il paragrafo 11.

## 11. Autocorrezione, cancello ed errata (tutto automatico)
Paolo non riceve messaggi di revisione, bozze o richieste di decisione: la redazione si corregge da sola e pubblica solo ciò che è verificato. Non usare PushNotification in nessun caso; l'unico messaggio è la consegna finale del paragrafo 6.
- **Ciclo di autocorrezione (fino a 3 giri):** dopo ogni controllo che fallisce, `controlli_fatti.py` stampa la riga `DA_TOGLIERE:` con gli id delle schede respinte. Per ognuna, in quest'ordine: (1) se il revisore ha indicato una fonte di livello 1 che corregge il fatto, aggiorna scheda e testo; (2) altrimenti togli il fatto e, se era una top news, mettici la prima riserva verificata; (3) se era un catalizzatore, una riga d'agenda o una cifra di un deep dive, togli la riga o la frase. Poi rigenera il PDF e ripeti i controlli; il revisore ricontrolla solo le schede nuove.
- **Minimi:** top news da 8 a 6 (la griglia regge anche 6); se le notizie verificate sono meno di 6, la sezione esce con quelle che ci sono. Agenda e catalizzatori: almeno le righe verificate. Un deep dive senza fatti verificati diventa "Nessuna novità rilevante: quadro invariato rispetto a ieri" con tabelle e grafici aggiornati. La top story deve essere sempre un fatto confermato: se cade, diventa top story la notizia confermata più importante.
- **Dati di mercato:** un dato respinto da `controlli_dati.py` si sostituisce con la chiusura precedente indicando la data, o con "n.d." (massimo 8 in tutto il PDF); mai un dato dubbio.
- **Layout:** se `controlli.py` o il controllo visivo falliscono (pagine diverse da 6, sovrapposizioni), accorcia i testi o riduci le righe e rigenera.
- **Dopo 3 giri:** togli tutto ciò che è ancora rosso e pubblica il resto. Non si pubblica solo se manca il minimo vitale (repository o API dei dati irraggiungibili, PDF impossibile da generare): in quel caso nessuna edizione oggi, e il messaggio finale lo dice in una riga.
- **Registro:** le schede con l'esito di ogni verifica (anche quelle scartate, con `"scartata": true`) vanno in `redazione/fatti/AAAA-MM-GG.json`: è la traccia per controlli futuri, non va mostrata a Paolo.
- **Errata, in automatico:** ogni mattina, prima di scrivere, rileggi `redazione/fatti/` dell'edizione precedente e confronta i fatti pubblicati con le notizie di oggi; se uno si è rivelato sbagliato (smentita, dato rivisto, fonte che corregge), la correzione esce a pagina 6, sotto le Fonti, nel paragrafo "Errata corrige" (edizione, frase sbagliata, frase corretta, fonte), e in `edizioni.json` nel campo `"errata"`. I PDF già pubblicati non si modificano.

## 12. Note pratiche dal collaudo del 12/10
- Ora corrente: se non c'è uno strumento dedicato, usa `TZ=Europe/Rome date`.
- Il numero di edizione lo calcola `set_meta`; non forzarlo mai a mano.
- FMP non dà il WTI (CLUSD) né gli indici intraday: prendili da fonti web con l'orario (es. Reuters, TheStreet, CNBC) e falli rientrare nella revisione.
- Alpha Vantage: una chiamata al secondo, chiamale una dopo l'altra; la serie BRENT EIA si aggiorna con qualche giorno di ritardo, normale.
- Le chiusure europee di oggi non esistono la mattina: nel ticker e nel cruscotto usa le chiusure della seduta precedente e i dati di stamattina con l'ora.
- Consensi divergenti tra fonti (es. EPS delle banche): non riportarli.
- Accesso in scrittura (lezione del 13-14/10): l'attività programmata eredita il permesso di push dalla sessione che la crea. Se va ricreata, crearla da una sessione con il repository agganciato in scrittura. Nel run mai add_repo né altri strumenti che chiedono approvazioni: senza nessuno davanti la sessione si ferma (14/10, run chiuso dopo 25 secondi, edizione recuperata alle 10:15).
- Tempi del collaudo: circa 20 minuti dall'avvio alla pubblicazione, revisore compreso (17 affermazioni verificate, 9 errori bloccanti trovati e corretti).

## 13. Budget di token (la redazione ha un tetto settimanale)
Ogni edizione deve costare il meno possibile senza toccare l'accuratezza. Regole:
- **Leggi una volta sola** questo file e il modello: non rileggere file già letti nella sessione, e non aprire per intero file lunghi (motore, script della scommessa, `edizioni.json`) se basta `grep`, `head` o `python3 -c` per il pezzo che serve. Di `edizioni.json` serve solo l'ultima voce.
- **Niente ricerche doppie:** le notizie le cercano gli agenti; tu non rifai le stesse ricerche e non apri gli articoli già coperti da una scheda, salvo i fatti contestati dal revisore.
- **Script dell'edizione:** copia il modello e modifica solo i contenuti con Edit; non riscriverlo da zero e non stamparlo intero più volte.
- **Un rendering per giro:** genera il PDF, poi tutti i controlli; correggi tutto quello che è emerso in una volta e rigenera. Il controllo visivo è l'anteprima unica (paragrafo 6, punto 5).
- **Output dei comandi corti:** usa `-q`, `| tail`, `| head`; mai stampare PDF, JSON lunghi o pagine web intere.
- **Strumenti esterni:** usa solo FMP, Alpha Vantage, ricerca web, git, Artifact e SendUserFile. Non caricare né usare Gmail, Calendar, Drive, Docs o Canva.
