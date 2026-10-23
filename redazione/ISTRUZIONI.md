# Gommberg Terminal Daily - Istruzioni di redazione v7.3 (nucleo)

Rassegna mattutina dei mercati, PDF di 6 pagine A4 stile Bloomberg/FT che Paolo condivide: zero errori. Giornale di FINANZA. Appendici (`APP_*.md`) solo quando `prepara.sh`, un controllo o questo file lo dicono.

**Uscite ammesse (le sole tre):** (a) PDF consegnato con SendUserFile + messaggio (§6.7); (b) giorno senza borsa: la sola riga NIENTE EDIZIONE di `prepara.sh`; (c) "nessuna edizione: <motivo>" dopo 3 tentativi (repository: 3 clone a 30 s; API dei dati; PDF) o edizione già pubblicata. Mai `add_repo`, PushNotification o strumenti che chiedono approvazione. Mai "sito aggiornato" senza PUSH_OK.

## 1. Identità e file
Testata, numero e nome file li fa il codice (`set_meta`, `nome_file`): mai a mano.

## 2. Struttura v6
Copia `edizione_modello_v6.py` in `/home/claude/lavoro/edizione_AAAA-MM-GG.py`; cambia SOLO `OGGI`, `NOTA_DATI`, `REG`, i dati dei grafici e `C`, **riscrivendo il blocco in un colpo solo**. Misure e griglia le impone il motore (mai `alto`/`largo`). Rimandi: `[[chiave]]` o `"rimando"` (→ pag. N).
- **Temi (elenco chiuso):** Fed, BCE, Inflazione, Tassi, Wall Street, Europa, Italia, Asia, Cina, Chip, Tecnologia, Banche, Petrolio, Geopolitica, Valute, Dazi, Trimestrali, Macro, Credito, Materie prime. Per `C["temi"]` (3-6), `top["tema"]`, `in30_temi` e il `tag` delle notizie: nessuna voce col tema della top story.
- **Gerarchia: noi più il resto del mondo.** Top story = aperture di almeno 3 testate di riferimento (Reuters, FT o Bloomberg dai titoli, Sole 24 Ore; Nikkei Asia se si muove l'Asia) confrontate con i movimenti rari di `contesto.py`. Le aperture pesano le notizie, non sono fonti. Se la maggioranza apre altrove, motivo scritto. Indice oltre il 3% e movimento più raro del giorno in prima pagina. Registro "prime_pagine" in `fatti.json` (schema in `APP_FONTI.md` §4).
- **Pag. 1 = tutto il giornale.** `ticker = ticker_da_dati("dati.json")`. `top`: titolo max 2 righe, dek 3-4. `quadro`: UNA frase che legge insieme tassi, dollaro, oro, petrolio e borse, o dice che non si legano (stima redazionale). `in30`: le 3 cose più importanti DOPO la top story, senza cifre, col rimando. `stamattina`: future, Asia, petrolio, cambio, 10 anni, orario 06:00-09:29; senza livelli verificati `stamattina_titolo` = "Cosa guardare all'apertura" con 2-4 soglie o eventi con orario. `notizie`: 6-8, ognuna con un fatto nuovo, almeno 2 da macro o società; no cruscotto ("Londra in rialzo") né eco della top story. Voci `breve` dell'indice senza cifre.
- **Pag. 2.** `cruscotto` e `cross` come nel modello; `termometri` solo coi temi mossi (gli altri in `fermi`, fuori dopo 3 sedute); `lettura` solo se aggiunge.
- **Pag. 3-5.** `ieri`: eventi programmati, sempre dato contro attese; un dato uscito non si toglie mai. `agenda`: max 10 righe, "-" senza consenso, il venerdì anche il lunedì. `bivio` solo con un evento decisivo vicino. `moduli`: 5 unità, il primo "mezzo" chiude pag. 3, pag. 4 e 5 = 2 "mezzo" o 1 "doppio". Ogni modulo: `perche`, `quindi` (§5), `righe` (mezzo max 5, doppio max 8), `punti` max 3 non ripetuti, `fonte`, grafici con `"soggetto"`; stampi vari, mai tutti uguali. Max 1 modulo sul tema della top story, con angolo nuovo; preferisci l'anomalia del giorno. Barre di livelli: `"livello": True`.
- **Un approfondimento = una tesi:** il `titolo` dice cosa significa, non cosa è successo (No: "Il Brent torna sopra i livelli di settembre". Sì: "Il petrolio rimette l'inflazione sul tavolo della Fed"); grafici, tabella e punti solo se la provano, **ognuno su una domanda diversa della tesi** (`ruolo`: quanto, perche, storia, conseguenza, chi; mai due volte la stessa grandezza sullo stesso periodo né una tabella che ripete un grafico: il motore lo blocca, No: 2-10-30 anni in linea + le stesse scadenze in barre + la stessa variazione in tabella; gli elementi si scelgono ogni giorno dalla tesi, mai uno schema fisso); `testo` (1-3 paragrafi) dà il contesto che i grafici non dicono; `numero` = UN dato che misura la tesi e dice ciò che il resto non dice (Sì: "Meno di 1 seduta su 5: quante volte nell'ultimo anno il VIX ha chiuso sopra 20"); `guardare` (obbligatorio nel doppio) = cosa confermerebbe o smentirebbe la tesi, e quando.
- **Riempimento (ogni pagina, ogni riquadro):** lo spazio porta contenuto verificato che aggiunge (racconto, contesto, il numero, un'altra notizia, una riga), mai spazi, a capo o grafici allungati, mai ripetizioni (§7). Ciò che varia ogni giorno rientra negli stessi spazi e nella stessa struttura. Il motore misura pagine e riquadri: sotto il 90% ERRORE; prima ricerche mirate per avere altro da dire, solo dopo `GTD_RIEMPIMENTO_OK=1`.
- **Pag. 6** `scommessa` (§4), `fonti`, `parole`.

## 3. Fonti e verità
- Dati di mercato: FMP e Alpha Vantage chiamati oggi (Alpha Vantage in serie; serie lunghe solo per un grafico), calcoli in codice. **Chiusure ovunque; intraday solo in "Stamattina" e nell'Asia segnata *, con orario.** Una riga con la data di oggi è intraday.
- **Fonti** (`fonti.json`): ufficiali e livello 1 bastano da sole; livello 2 e fonti serie non in elenco: due indipendenti; vietate mai. Dato pubblico certo con una sola fonte attendibile: dichiarato, "-7,57% (Korea Herald)", `"fonte_singola": true`. Solo eventi successivi all'edizione precedente. **Si toglie ciò che è dubbio o contraddetto**, non il dato certo.
- **Dati ufficiali dal comunicato** (scheda `"tipo": "U"` e calendario; agenzia d'appoggio; CERCA in `controlli_fatti.py`). **Trovare qualsiasi dato:** chi lo produce, agenzia nazionale, stampa locale; max 5 ricerche con la extended; registro "ricerca"; "n.d." solo dopo 4 ricerche registrate. Metodo in `APP_FONTI.md`: leggilo quando un dato non esce al primo tentativo.
- **WebFetch SOLO su un URL comparso in un risultato di WebSearch o di un WebFetch precedente, copiato identico.** Un URL scritto a mano o preso da un file chiede un permesso che nessuno può dare e **la sessione programmata muore** (16/10). Al sito ufficiale si arriva via ricerca. Una citazione si tiene solo se il testo la contiene parola per parola.

## 4. La scommessa
Script in `redazione/scommessa/`; pag. 6 la fa il motore da `stato.json`. Sei mercati fissi (metodo 1.1) più **lo strumento della settimana**, sul tema del momento, mai un doppione e mai ripetitivo rispetto al resto del giornale (`APP_LUNEDI.md` §3b): ogni suo dato si verifica come un fatto. Lunedì: `APP_LUNEDI.md`. Mar-ven: `/home/claude/lavoro/attuali.json` (ultime chiusure ufficiali con data, anche dello strumento della settimana: `{"spx": [7830.1, "2026-10-19"]}`), poi `bash /home/claude/gtd/redazione/scommessa_giorno.sh`. `C["scommessa"]` = {"tesi": "<a che punto siamo, senza elencare strumenti>", "lunedi": False, "venerdi": <True il venerdì>, "settimana_prec": None}. Venerdì l'ultima chiusura è di giovedì: la tesi dice cosa serve per chiudere la settimana. **On track** = direzione giusta finora (stesso termine su sito e messaggio). La previsione non cambia in settimana.

## 5. Stile e interpretazione
- Solo trattino corto "-". Variazioni con segno (il motore le colora). Numeri all'italiana. "&amp;" nei Paragraph. Orari di Roma.
- **Righe "→": max 5**, max 20 parole: **M** meccanismo ("di solito", `meccanismi.json`), **C** causa con scheda `"tipo": "C"` e fonte in coda, **S** stima etichettata. Mai "pesa", "trascina", "spinto da" su un movimento senza scheda C.
- **Come si cita: la voce è nostra, la fonte firma.** Dati e fatti certi: nessuna fonte nella frase, va nella riga "Fonti" della pagina. Notizie e cause riprese: fonte tra parentesi in coda ("Pesano gli attacchi dell'Iran nello Stretto di Hormuz (Yahoo Finance)."). "Secondo X" solo quando il nome è parte della notizia (stime, opinioni, indiscrezioni, citazioni), mai in apertura per un fatto. La lettura della redazione non ha fonte.
- **Perché e E quindi:** perché = causa con fonte o meccanismo, mai la parafrasi del dato; E quindi = una cosa osservabile (livello, data, orario, evento). Sì: "oggi alle 15:30 la riapertura del Nasdaq dirà se le vendite si fermano".
- **Coerenza con i prezzi:** ogni spiegazione, anche di una grande testata, torna con gli altri prezzi (per i tassi, con la forma della curva).
- **Contesto, non percentuali nude** (`contesto.py`; tassi reali `APP_DATI.md` §3): un movimento notevole con la sua misura storica ("il calo più forte dal 2 aprile", "capita una seduta su 20"), chi muove la curva, rendimento reale o inflazione attesa; un dato macro con lo scarto dalle attese e la reazione del 2 anni. Mai z-score o sigma; le frasi dello script si riscrivono.
- **Il perché si cerca sempre, in due fasi** (fatti controintuitivi, ANOMALIE e movimenti rari): (A) chi l'ha già spiegato, fonti di livello 1; (B) la prova dei prezzi, anche per la spiegazione trovata (fuga verso la sicurezza = oro e VIX su, azioni e rendimenti lunghi giù). Si pubblica la causa attribuita che torna; altrimenti (dirlo) la **lettura della redazione** con l'ipotesi che regge e i prezzi che la sostengono. "Causa non chiarita" solo se ogni ipotesi fallisce, dicendo quali. Mai "le fonti non spiegano".
- **Scomponi il dato che fa notizia:** generale, core, componente trainante, lettura reale.
- **Probabilità** con orizzonte, metodo e fonte ("rialzo il 28 ottobre al 47% (CME FedWatch)"); se cambia dall'edizione precedente, perché.
- **Movimenti estremi mai persi:** un indice principale oltre il 3% compare con la cifra (in `dati.json` sempre S&P 500, Nasdaq, Euro Stoxx 50, Nikkei 225, Kospi, Hang Seng).
- **Testo e grafico coerenti:** confronti come nei dati, stessa base temporale; mai "-0,0%"; "record" solo con una scheda.

## 6. Flusso di ogni mattina
Lavoro in `/home/claude/lavoro`, orari di Roma (`zoneinfo`).
0. `bash /home/claude/gtd/redazione/prepara.sh`; se stampa USCITA (b) o (c), eseguila. Le righe "Ricerche" dicono dove sono stati trovati i dati difficili.
1. **Dati:** `dati.json` (schema in `controlli_dati.py`, con `"etichette"` e i `"macro"` del giorno); `controlli_dati.py dati.json` = OK; poi `python3 /home/claude/gtd/redazione/contesto.py dati.json --json contesto.json`: materiale per top story, quadro e moduli.
2. **Ricerca:** due agenti `model: "sonnet"` (o tu): (a) calendario concluso dall'ultima edizione; (b) aperture delle testate di riferimento, 10-12 notizie in ordine d'importanza (le scartate sono riserve), future e Asia con orario, agenda con consensi. Schede JSON, citazione letterale max 30 parole.
2c. **Il perché** (max 2 casi): (A) fino a 4 ricerche mirate col fatto e la data e sui resoconti di fine seduta (Reuters, AP, CNBC, Radiocor); i titoli di Bloomberg, FT, WSJ orientano, la causa si conferma su un articolo aperto; (B) 2-3 ipotesi, ognuna con cosa prevede sui prezzi, confrontate con `dati.json` e `contesto.py`. Registro "anomalia" in `fatti.json` (schema in `APP_FONTI.md` §4).
3. **fatti.json:** una scheda per fatto non preso dalle API; `controlli_fatti.py fatti.json /home/claude/gtd/edizioni.json AAAA-MM-GG --prima-della-revisione`.
4. **Stesura:** blocco `C` (§2), scommessa (§4), `python3 edizione_AAAA-MM-GG.py /home/claude/lavoro "<pdf>"` (scrive `voce_indice.json`), poi `qpdf --object-streams=generate --compress-streams=y`.
5. **Controlli:** `GTD_SENZA_INDICE=1 bash /home/claude/gtd/redazione/controlli_tutti.sh "<pdf>" <N> --prima-della-revisione`, poi Read di `anteprima.png`.
6. **Revisione** (§10), correzioni in un giro, render, stesso comando senza `--prima-della-revisione`: ESITO OK. Rosso: §11.
7. **Consegna:** `edizioni_voce.py` e `pubblica.sh` (§8); SendUserFile (status "proactive", display "render", didascalia "Gommberg Terminal Daily #NNN - <data lunga>"); il messaggio = output di `python3 /home/claude/gtd/redazione/messaggio.py --voce /home/claude/lavoro/voce_indice.json --sito "<ultima riga di pubblica.sh>"`; per ultimo l'Archivio Claude (§8.4).

## 7. Niente ripetizioni
- **Un fatto, una casa:** ogni cifra al massimo 2 volte nel PDF (pag. 1 e la sua pagina); tabelle, punti, perché e quindi dello stesso modulo contano tutti. `controlli_ripetizioni.py` è bloccante; gli AVVISI su fatti diversi si ignorano.
- **Tra edizioni:** solo fatti nuovi; un tema già uscito torna con uno sviluppo nel titolo. **Stamattina:** orari tra le 06:00 e le 09:29 di Roma; un dato della Stamattina di ieri con un orario nuovo è un errore.

## 8. Pubblicazione
Non toccare index.html, README.md, assets/.
1. **Indice:** `python3 /home/claude/gtd/redazione/edizioni_voce.py --pdf "<pdf>" --data AAAA-MM-GG --voce /home/claude/lavoro/voce_indice.json --registro /home/claude/gtd/redazione/pronostici/<lunedì>-settimana.json --stato /home/claude/lavoro/stato.json --sigle /home/claude/lavoro/testo.json` (lunedì: `--verdetto`). Numero già presente: uscita (c).
2. **Cancello:** `bash /home/claude/gtd/redazione/controlli_tutti.sh "<pdf>" <N>`: ESITO OK.
3. **Sito:** `bash /home/claude/gtd/redazione/pubblica.sh "<pdf>" <N> AAAA-MM-GG /home/claude/lavoro/fatti.json` (genera anche pagine per edizione, feed e link fisso): la sua ultima riga va identica nel messaggio.
4. **Archivio Claude** (dopo la consegna): Artifact `action: "read"` su https://claude.ai/artifact/MuwDrCHDGXuADtKtL7cFcH, poi `action: "publish"` con quell'`url`, `file_path` = `/home/claude/gtd/redazione/archivio_claude.html` (non modificarla), `files` = {"edizioni.json": "/home/claude/gtd/edizioni.json", "pdf/AAAA-MM-GG-gommberg-NNN.pdf": "<pdf>"}, senza `capabilities` né `icon`; 2 tentativi (rifiutata per versione più recente: ripubblica uguale), poi si salta.
5. Passaggio fallito: riprova una volta, poi consegna comunque.

## 9. Lettori: lettura e spiegazione
Lettori per lo più di media competenza. Ogni pezzo dà il fatto (con il numero) e la lettura (cosa significa, quanto era atteso); un concetto (curva, premio a termine, carry trade...) si spiega in una frase alla prima comparsa (`meccanismi.json`). Test: il lettore medio capisce senza cercare, l'esperto non si annoia.
Sigla non ovvia: spiegata tra parentesi (max 6 parole) alla PRIMA occorrenza, come in `glossario.json` (nuova: aggiungila). Mai spiegate: Fed, BCE, PIL, S&P 500, Nasdaq, Dow Jones, ETF, USA, UE, FMI.

## 10. Revisione rafforzata
Un revisore `model: "sonnet"` che non ha scritto il numero (senza Agent: tu) riceve pdftotext, `fatti.json`, `fonti.json`, notizie di ieri. **Fino a 25 verifiche:** (1) schede di top story, notizie, calendario e cause C: URL, citazione letterale, data, PDF fedele; (2) evento principale dell'agenda; (3) conferma indipendente della top story; (4) senza aprire pagine: coerenza con i prezzi, probabilità, "record". Scrive `verifica` (confermato | errato | non_conclusivo) e `nota_revisore`; un dubbio che resta si toglie. Lunedì anche pag. 6 contro `verdetto.json`.

## 11. Autocorrezione e cancello
Paolo non riceve bozze né domande. Si pubblica solo ciò che passa i controlli: ogni ERRORE si corregge o si risolve togliendo il non verificato, fino a 3 giri (`APP_ERRORI.md`).
- Notizie 6-8 (meno solo se le verificate sono meno); al posto di una scartata la prima riserva verificata. La top story è sempre un fatto confermato.
- Correzioni: schede di ieri (`redazione/fatti/`) contro le notizie; mai errata corrige; errore piccolo: nessuna menzione; sostanziale: il fatto giusto in una frase, senza rimandi a ieri (`APP_ERRORI.md` §6).

## 12. Note pratiche
In `PROGETTO.md` (permessi dell'attività programmata).

## 13. Budget di token
Una lettura di questo file e del modello; mai per intero motore, script, `edizioni.json`, PDF o pagine web. Un rendering per giro, correzioni insieme, controllo visivo = anteprima. Output corti. Niente Gmail, Drive, Docs, Canva.
