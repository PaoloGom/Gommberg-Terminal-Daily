# Gommberg Terminal Daily - Istruzioni di redazione v6.2 (nucleo)

Rassegna mattutina dei mercati in PDF, 6 pagine A4, stile Bloomberg/FT, che Paolo condivide: zero errori. Giornale di FINANZA. Appendici (`APP_*.md`) solo quando `prepara.sh` o un controllo lo dicono.

**Uscite ammesse (le sole tre; nessun altro modo di finire):** (a) PDF consegnato con SendUserFile + messaggio (§6.7); (b) giorno senza borsa: la sola riga NIENTE EDIZIONE di `prepara.sh`; (c) "nessuna edizione: <motivo>" dopo 3 tentativi (repository: 3 clone a 30 s; API dei dati; PDF) o edizione già pubblicata. Mai `add_repo`, PushNotification o strumenti che chiedono approvazione. Mai "sito aggiornato" senza PUSH_OK.

## 1. Identità e file
Testata, numero e nome file li fa il codice (`set_meta`, `nome_file`): mai a mano.

## 2. Struttura v6
Copia `edizione_modello_v6.py` in `/home/claude/lavoro/edizione_AAAA-MM-GG.py`; cambia SOLO `OGGI`, `NOTA_DATI`, `REG`, i dati dei grafici e il dizionario `C`, **riscrivendo il blocco in un colpo solo** (un Write o uno script). Composizione, misure e griglia le impone il motore (mai `alto`/`largo`). Rimandi: `[[chiave]]` o `"rimando"` (diventa "→ pag. N").
- **Temi (elenco chiuso):** Fed, BCE, Inflazione, Tassi, Wall Street, Europa, Italia, Asia, Cina, Chip, Tecnologia, Banche, Petrolio, Geopolitica, Valute, Dazi, Trimestrali, Macro, Credito, Materie prime. Per `C["temi"]` (3-6), `top["tema"]`, `in30_temi` (uno per punto) e il `tag` delle notizie: nessuna voce ha il tema della top story.
- **Pag. 1 = tutto il giornale.** `ticker = ticker_da_dati("dati.json")`. `top`: titolo max 2 righe, dek 3-4 righe. `quadro`: UNA frase che legge insieme tassi, dollaro, oro, petrolio e borse, o dice che non si legano (stima redazionale). `in30`: le 3 cose più importanti DOPO la top story, senza cifre, col rimando. `stamattina`: future, Asia, petrolio, cambio, 10 anni, con orario 06:00-09:29; senza livelli verificati in finestra `stamattina_titolo` = "Cosa guardare all'apertura" con 2-4 soglie o eventi con orario. `notizie`: 6-8, ognuna con un fatto nuovo (dato, dichiarazione, società, decisione), almeno 2 da macro o società. No: "Londra in rialzo, Milano in calo" (è il cruscotto) o "Il dollaro sale dopo il CPI" se il CPI è la top story. Le voci `breve` dell'indice non hanno cifre.
- **Pag. 2.** `cruscotto` e `cross` come nel modello; `termometri` solo coi temi mossi (gli altri in `fermi`, fuori dopo 3 sedute); `lettura` solo se aggiunge.
- **Pag. 3-5.** `ieri`: eventi programmati, sempre dato contro attese; un dato uscito non si toglie mai (§3). `agenda`: max 10 righe, "-" senza consenso, il venerdì anche il lunedì. `bivio` solo con un evento decisivo vicino. `moduli`: 5 unità, il primo "mezzo" chiude pag. 3, pag. 4 e 5 = 2 "mezzo" o 1 "doppio" (il tema forte). Ogni modulo: `perche`, `quindi` (§5), `righe` (mezzo max 5, doppio max 8), `punti` max 3 che aggiungono e non ripetono la tabella, `fonte`, grafici con `"soggetto"` (parola del titolo o del perché). **Stampi vari secondo il contenuto:** solo tabella, grafico + punti, due grafici, nessun grafico: mai tutti uguali. Max 1 modulo sul tema della top story, con angolo nuovo; preferisci l'anomalia del giorno; mai "nessuna novità". Barre di livelli (indici di fiducia, rendimenti): `"livello": True`. Modulo sotto l'80%: ERRORE; aggiungi fatti verificati, e solo dopo quel tentativo `GTD_RIEMPIMENTO_OK=1`.
- **Pag. 6** `scommessa` (§4), `fonti`, `errata` se serve; `parole` solo senza errata.

## 3. Fonti e verità
- Dati di mercato: FMP e Alpha Vantage chiamati oggi (Alpha Vantage in serie; serie lunghe solo per un grafico), calcoli in codice.
- **Chiusure ovunque; intraday solo in "Stamattina" e nell'Asia segnata *, con orario.** Una riga con la data di oggi è intraday.
- **Fonti** (`fonti.json`): "ufficiali" (BLS, Census, BEA, Fed, Tesoro, Eurostat, Istat, BCE, borse) e livello 1: ne basta una; livello 2: due indipendenti; vietate mai. Un dato pubblico certo (calendario, chiusura o movimento di un indice) con una sola fonte attendibile si pubblica dichiarato ("-7,57% secondo Korea Herald", scheda `"fonte_singola": true`): cerca prima la fonte ufficiale, mai "n.d." o "non verificato" su un dato uscito. Solo eventi successivi all'edizione precedente. **Si toglie ciò che è dubbio o contraddetto**, non il dato certo.
- Ricerca: WebSearch in `mode: "standard"` senza `allowed_domains` (con domini o extended il proxy rifiuta), poi filtra con `fonti.json`; WebFetch solo su URL restituiti. Articoli di ieri: nome dell'evento + data ("PPI October 15 2026", "PPI 15 ottobre"). WebFetch riassume e può inventare: per una citazione chiedi la frase letterale e tienila solo se il testo la contiene parola per parola.

## 4. La scommessa (metodo intatto)
Tutto dagli script di `redazione/scommessa/`; pag. 6 la fa il motore da `stato.json`. Lunedì: `APP_LUNEDI.md`. Mar-ven: scrivi `/home/claude/lavoro/attuali.json` (ultime chiusure ufficiali con data, es. `{"spx": [7830.1, "2026-10-19"]}`), poi `bash /home/claude/gtd/redazione/scommessa_giorno.sh`. `C["scommessa"]` = {"tesi": "<a che punto siamo sulla settimana, senza elencare strumenti>", "lunedi": False, "venerdi": <True il venerdì>, "settimana_prec": None}. Venerdì: l'ultima chiusura è di giovedì, la tesi dice cosa serve per chiudere la settimana. **On track** = direzione giusta finora (spiegato una volta a pag. 6; stesso termine su sito e messaggio). La previsione non cambia in settimana.

## 5. Stile e interpretazione
- Solo trattino corto "-". Variazioni con segno (il motore le colora). Numeri all'italiana. "&amp;" nei Paragraph. Orari di Roma (`zoneinfo`).
- **Righe "→": max 5**, max 20 parole. **M** meccanismo ("di solito") da `meccanismi.json`; **C** causa con scheda `"tipo": "C"`, "secondo <testata>"; **S** stima etichettata. Mai "pesa", "trascina", "spinto da" su un movimento senza scheda C.
- **Perché e E quindi**: perché = causa con fonte o meccanismo, mai la parafrasi del dato; E quindi = una cosa osservabile (livello, data, orario, evento in agenda). No: "Il settore non dà un segnale unico". Sì: "oggi alle 15:30 la riapertura del Nasdaq dirà se le vendite si fermano".
- **Coerenza con i prezzi:** ogni spiegazione deve tornare con gli altri prezzi del giorno; per i tassi confronta la causa con la forma della curva (breve contro lungo). Se non torna, dillo e proponi l'alternativa etichettata (rifugio, premio a termine). No: "inflazione alta, il 10 anni scende". Sì: "l'inflazione spiega il breve, non il lungo in calo: causa non chiarita".
- **Fatti controintuitivi = la notizia da spiegare** (dato caldo e borsa su, inflazione sopra le attese e 10 anni giù): ricerca dedicata (§6.2c), poi spiegazione attribuita o "causa non chiarita" + cosa guardare. Mai "le fonti non lo spiegano".
- **Scomponi il dato che fa notizia:** inflazione e consumi con generale, core, componente trainante e lettura reale quando c'è.
- **Probabilità** sempre con orizzonte, metodo e fonte. Sì: "rialzo il 28 ottobre al 47% (CME FedWatch, via Axios)"; "insolvenza cumulata a 5 anni dai CDS". Cifra di fonte diversa dall'edizione precedente: spiega la differenza (fonte, data, metodo).
- **Movimenti estremi mai persi:** un indice principale oltre il 3% dall'ultima edizione compare con la cifra, con fonte singola dichiarata se serve (in `dati.json` sempre S&P 500, Nasdaq, Euro Stoxx 50, Nikkei 225, Kospi, Hang Seng).
- **Testo e grafico coerenti:** "più/meno", "maglia nera", "in testa" come nei dati; il grafico mostra la tesi del titolo sulla stessa base temporale del testo; niente "tutte in rialzo" se la tabella ha un calo; mai "-0,0%"; "record" solo con una scheda che lo dice.

## 6. Flusso di ogni mattina
Lavoro in `/home/claude/lavoro`.
0. `bash /home/claude/gtd/redazione/prepara.sh`; se stampa USCITA (b) o (c), eseguila.
1. **Dati:** `dati.json` (schema in testa a `controlli_dati.py`, con `"etichette"` e, per i dati macro del giorno, `"macro"`); `controlli_dati.py dati.json` = OK.
2. **Ricerca:** due agenti `model: "sonnet"` (o tu): (a) calendario concluso dall'ultima edizione; (b) 10-12 notizie in ordine d'importanza (le scartate sono riserve), future e Asia con orario, agenda con consensi. Solo schede JSON, citazione letterale max 30 parole.
2c. **Anomalie:** confronta `dati.json` con dati macro e conti; per ogni fatto controintuitivo (max 2) fino a 3 ricerche in inglese e italiano e i 2 articoli più pertinenti. Registra in `fatti.json`: `{"id": "A1", "sezione": "anomalia", "fatto": "...", "ricerche": ["query", ...], "esito": "C03" | "non chiarita"}`.
3. **fatti.json:** una scheda per fatto non preso dalle API; `controlli_fatti.py fatti.json /home/claude/gtd/edizioni.json AAAA-MM-GG --prima-della-revisione`.
4. **Stesura:** blocco `C` (§2), scommessa (§4), `python3 edizione_AAAA-MM-GG.py /home/claude/lavoro "<pdf>"` (scrive `voce_indice.json`), poi `qpdf --object-streams=generate --compress-streams=y`.
5. **Controlli:** `GTD_SENZA_INDICE=1 bash /home/claude/gtd/redazione/controlli_tutti.sh "<pdf>" <N> --prima-della-revisione`, poi Read di `anteprima.png`.
6. **Revisione** (§10), correzioni in un giro, render, stesso comando senza `--prima-della-revisione`: ESITO OK. Rosso: §11.
7. **Consegna:** `edizioni_voce.py` e `pubblica.sh` (§8); poi SendUserFile (status "proactive", display "render", didascalia "Gommberg Terminal Daily #NNN - <data lunga>"); poi il messaggio = l'output di `python3 /home/claude/gtd/redazione/messaggio.py --voce /home/claude/lavoro/voce_indice.json --sito "<ultima riga di pubblica.sh>"`; per ultimo l'Archivio Claude (§8.4).

## 7. Niente ripetizioni
- **Un fatto, una casa:** ogni cifra al massimo 2 volte nel PDF (pag. 1 e la sua pagina); tabelle, punti, perché e quindi dello stesso modulo contano tutti. No: 5,10% nel dek, nella tabella, nel perché e nel quindi. Sì: 5,10% nel dek e nella tabella, il perché parla del livello senza la cifra. `controlli_ripetizioni.py` è bloccante.
- Gli AVVISI (cifre piccole, 2 sezioni) su fatti diversi si ignorano.
- **Tra edizioni:** solo fatti nuovi; un tema già uscito torna con uno sviluppo nel titolo. **Stamattina:** tutti gli orari tra le 06:00 e le 09:29 di Roma; un dato della Stamattina di ieri con un orario nuovo è un errore.

## 8. Pubblicazione
Non toccare index.html, README.md, assets/.
1. **Indice:** `python3 /home/claude/gtd/redazione/edizioni_voce.py --pdf "<pdf>" --data AAAA-MM-GG --voce /home/claude/lavoro/voce_indice.json --registro /home/claude/gtd/redazione/pronostici/<lunedì>-settimana.json --stato /home/claude/lavoro/stato.json --sigle /home/claude/lavoro/testo.json` (lunedì: `--verdetto`). Numero già presente: uscita (c).
2. **Cancello:** `bash /home/claude/gtd/redazione/controlli_tutti.sh "<pdf>" <N>`: ESITO OK.
3. **Sito:** `bash /home/claude/gtd/redazione/pubblica.sh "<pdf>" <N> AAAA-MM-GG /home/claude/lavoro/fatti.json`: la sua ultima riga va identica nel messaggio.
4. **Archivio Claude** (dopo la consegna): Artifact `action: "read"` su https://claude.ai/artifact/MuwDrCHDGXuADtKtL7cFcH, poi `action: "publish"` con quell'`url`, `file_path` = `/home/claude/gtd/redazione/archivio_claude.html` (non modificarla), `files` = {"edizioni.json": "/home/claude/gtd/edizioni.json", "pdf/AAAA-MM-GG-gommberg-NNN.pdf": "<pdf>"}, senza `capabilities` né `icon`; 2 tentativi (rifiutata per versione più recente: ripubblica uguale), poi si salta.
5. Passaggio fallito: riprova una volta, poi consegna comunque.

## 9. Lettori e sigle
Sigla non ovvia: spiegata tra parentesi (max 6 parole) alla PRIMA occorrenza, come in `glossario.json` (nuova: aggiungila). Mai spiegate: Fed, BCE, PIL, S&P 500, Nasdaq, Dow Jones, ETF, USA, UE, FMI.

## 10. Revisione rafforzata
- Un revisore `model: "sonnet"` che non ha scritto il numero (senza Agent: tu); riceve pdftotext, `fatti.json`, `fonti.json`, notizie di ieri.
- **Fino a 25 verifiche:** (1) schede di top story, notizie, calendario e cause C: URL, citazione letterale, data, PDF fedele; (2) evento principale dell'agenda; (3) conferma indipendente della top story; (4) senza aprire pagine: coerenza con i prezzi, probabilità, "record". Scrive in `fatti.json` `verifica` (confermato | errato | non_conclusivo) e `nota_revisore`; un dubbio che resta = si toglie. Lunedì: pag. 6 contro `verdetto.json`.

## 11. Autocorrezione e cancello
Paolo non riceve bozze né domande. Si pubblica solo ciò che passa i controlli; il resto si corregge o si toglie, fino a 3 giri (`APP_ERRORI.md`).
- Nessun controllo impedisce l'uscita: ogni ERRORE si risolve togliendo il non verificato o con "n.d." e nota (`APP_ERRORI.md`).
- Notizie 6-8 (meno solo se le verificate sono meno); al posto di una scartata la prima riserva verificata. La top story è sempre un fatto confermato.
- Errata: schede di ieri (`redazione/fatti/`) contro le notizie; un fatto smentito va in `C["errata"]` (edizione, frase sbagliata, corretta, fonte).

## 12. Note pratiche
In `PROGETTO.md` (permessi dell'attività programmata).

## 13. Budget di token
Una lettura di questo file e del modello; mai per intero motore, script, `edizioni.json`, PDF o pagine web. Un rendering per giro, correzioni insieme, controllo visivo = anteprima. Output corti. Niente Gmail, Drive, Docs, Canva.
