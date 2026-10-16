# Gommberg Terminal Daily - Istruzioni di redazione v6 (nucleo)

Rassegna mattutina dei mercati in PDF, 6 pagine A4, stile Bloomberg/FT. Paolo la condivide: zero errori. Giornale di FINANZA: macro solo se serve a capire l'attualità. Appendici solo quando `prepara.sh` o un controllo lo dicono: `APP_LUNEDI.md` (scommessa del lunedì), `APP_ERRORI.md` (controllo rosso, errata), `APP_FESTIVI.md`, `APP_DATI.md` (endpoint, simboli, basi). `ISTRUZIONI_v5.md`: archivio.

**Due lezioni:** (1) mai scrivere "sito aggiornato" senza PUSH_OK (13/10); (2) mai `add_repo` né strumenti che chiedono approvazione: senza nessuno davanti la sessione si ferma (14/10).

## 1. Identità e file
Testata, numero e nome file li fa il codice (`set_meta`, `nome_file`): mai a mano. Nota di `set_meta`: "Chiusure al 14 ottobre; mattina del 15 ottobre dove indicato".

## 2. Struttura v6
Copia `edizione_modello_v6.py` e sostituisci solo i contenuti (componenti, ordine, titoli fissi). Il prompt dell'attività cita `edizione_modello_2026-10-12.py`: dalla v6 quel file rimanda qui; il modello v5 è `edizione_modello_v5.py`.
- **Pag. 1 = tutto il giornale.** `ticker()` 7 caselle (chiusure). TOP STORY: h1 max 2 righe, dek 3-4 righe col fatto completo, al massimo una `arrow()`. "In 30 secondi" (le 3 cose più importanti DOPO la top story) | "Stamattina" (future, Asia, petrolio, cambio, 10 anni, ogni dato con orario). "Le notizie del giorno": 6-8 notizie per importanza, `rimando="pag. N"` se approfondite dentro. `indice_interno()` in fondo.
- **Pag. 2 Mercati.** Cruscotto con nota delle basi, cross-asset (Treasury 2/10/30, BTP e spread BTP-Bund, EUR/USD, Brent, WTI, oro, VIX; "Lettura" breve o "-"), `termometri`: per esteso solo i temi con novità dall'ultima edizione, gli altri in "Fermi: ..."; un tema esce dopo 3 sedute ferme. `lettura()` solo se aggiunge qualcosa.
- **Pag. 3-5 flusso continuo.** "Ieri in calendario" (lunedì "La settimana scorsa"): solo eventi programmati, dato contro attese, niente righe di mercato. "In arrivo": max 10 righe, un evento per riga, Attese in "celln", "-" senza consenso; il venerdì anche il lunedì dopo. "Il bivio" solo con un evento decisivo vicino. 2-3 `approfondimento()` (grafico | tabella | due_grafici): almeno 1 su un tema diverso dalla top story, al massimo 1 sul suo tema e con angolo nuovo; temi di lungo corso (Treasury, Iran, petrolio, EUR/USD) solo con novità o soglia superata; preferisci l'anomalia del giorno. Mai "nessuna novità": cambia tema. Numero e lunghezza degli approfondimenti si regolano per 6 pagine piene.
- **Pag. 6** scommessa (§4), `parole()` facoltativo, Fonti, Errata se serve.

## 3. Fonti e verità
- Dati di mercato: FMP e Alpha Vantage chiamati oggi, calcoli in codice, mai a memoria o a mano.
- **Chiusure ovunque; intraday solo in "Stamattina" e nell'Asia segnata *, sempre con orario.** Una riga con la data di oggi (FMP o Alpha Vantage) è intraday.
- **Fonti ammesse:** `fonti.json`. Livello 1 (Reuters, AP, Bloomberg, FT, WSJ, CNBC, ANSA, Sole 24 Ore, siti ufficiali): ne basta una. Livello 2: due testate indipendenti. Vietate e domini fuori elenco: mai da soli; una fonte seria fuori elenco si annota in `fatti.json` (`fonti_da_valutare`) e non si usa.
- **Freschezza:** notizie, top story e calendario solo con eventi successivi all'edizione precedente; conta la data dell'evento, non dell'articolo; l'orario di un live blog è quello di pubblicazione.
- Fonti in disaccordo: cita la fonte o ometti. Consensi divergenti: mai senza due fonti concordi. Piani non sono decisioni. **Nel dubbio si toglie**, anche col condizionale.
- Orari in ora di Roma, convertiti con `zoneinfo` per la data dell'evento; per eventi fuori sede indica dove.

## 4. La scommessa (metodo intatto)
Numeri, range, verdetto e pagella li fanno gli script di `redazione/scommessa/` (lanciati da lì); pag. 6 la fa `pagina6.py`; il metodo non si tocca (`METODO.md`). Chiavi: `acwi spx sx5e ust10 ust2 brent eurusd`. Lunedì: `APP_LUNEDI.md`.
**Mar-ven:** `/home/claude/lavoro/attuali.json` con l'ultima **chiusura ufficiale** e la sua data, es. `{"spx": [7830.1, "2026-10-19"]}`; senza chiusura nuova lo strumento si omette. Da `redazione/scommessa`: `python3 valuta.py --settimana ../pronostici/<lunedì>-settimana.json --attuali /home/claude/lavoro/attuali.json --json /home/claude/lavoro/stato.json` e `python3 grafico.py ../pronostici/<lunedì>-settimana.json /home/claude/lavoro/c_forecast.png /home/claude/lavoro/stato.json`. Pag. 6: `pagina6_settimana(reg, stato, tesi="<a che punto siamo>", grafico="c_forecast.png", venerdi=<True il venerdì>)`. La previsione non cambia in settimana (il venerdì è ammessa una frase autoironica). Prove mai nel registro vero.

## 5. Stile e interpretazione
- Solo trattino corto "-". Variazioni con segno esplicito: il motore le colora (verde +, rosso -); niente segni su ciò che non varia; livelli attesi in "celln". Numeri all'italiana (7.811,54). "&amp;" nei Paragraph. Frasi brevi, numero e perché conta. Probabilità: "stime redazionali soggettive". Grafici PNG + SVG con lo stesso nome, etichette senza sovrapposizioni.
- **Righe "→": massimo 5 nel PDF**, max 20 parole, solo dove il perché non è ovvio. Tipi: **M** meccanismo ("di solito", "in genere") solo se è in `meccanismi.json`, rispettandone le eccezioni; **C** causa di un movimento: solo con scheda `"tipo": "C"` la cui citazione contiene il nesso, scritta "secondo <testata>"; **S** stima redazionale, etichettata.
- Una M non sta nella frase di una variazione di ieri, salvo come contrasto ("di solito X; ieri no"). Mai "perché", "a causa di", "spinto da", "pesa", "trascina", "sulla scia di", "complice" su un movimento di ieri senza scheda C.

## 6. Flusso di ogni mattina
Repository `/home/claude/gtd`; file del giorno in `/home/claude/lavoro`, comandi lanciati da lì. Strumenti: FMP, Alpha Vantage, ricerca web, Agent, git, Artifact, SendUserFile.
0. `bash /home/claude/gtd/redazione/prepara.sh`: ora, giorno di uscita, numero, appendici, riepilogo dell'ultima edizione. NIENTE EDIZIONE: manda la riga indicata e fermati. Numero già esistente: fermati e segnalalo.
1. **Dati:** scarica, scrivi `dati.json` (schema in testa a `controlli_dati.py`), `python3 /home/claude/gtd/redazione/controlli_dati.py dati.json` deve dire OK.
2. **Ricerca:** due agenti `model: "sonnet"`: (a) eventi in calendario conclusi dall'ultima edizione; (b) notizie della notte (10-12 candidate in ordine d'importanza: le scartate fanno da riserva), future e Asia con orario, agenda con orari e consensi. Passa data e notizie dell'ultima edizione e `fonti.json`. Restituiscono SOLO schede JSON (schema in `controlli_fatti.py`), citazione originale max 30 parole. Senza Agent: stesse ricerche, stesso formato.
3. **fatti.json:** una scheda per ogni fatto non preso dalle API; `python3 /home/claude/gtd/redazione/controlli_fatti.py fatti.json /home/claude/gtd/edizioni.json AAAA-MM-GG --prima-della-revisione`; ciò che non passa si toglie o si rifonda.
4. **Stesura:** copia il modello in `edizione_AAAA-MM-GG.py`, modifica con Edit, scommessa, grafici, render, `qpdf --object-streams=generate --compress-streams=y in.pdf out.pdf`.
5. **Controlli:** `GTD_SENZA_INDICE=1 bash /home/claude/gtd/redazione/controlli_tutti.sh "<pdf>" <N> --prima-della-revisione`, poi Read della sola `anteprima.png` (sovrapposizioni, pagine piene). Pagina dubbia: `pdftoppm -r 70 -f N -l N`.
6. **Revisione** (§10), correzioni in un giro, render, stesso comando senza `--prima-della-revisione`: ESITO OK. Rosso: §11.
7. **Pubblicazione** (§8), poi SendUserFile (status "proactive", display "render"), didascalia "Gommberg Terminal Daily #NNN - <data lunga>", 3 righe (notizia del giorno, evento di oggi, scommessa) più le righe Sito e Archivio Claude.

## 7. Niente ripetizioni
- **Nell'edizione:** un fatto ha UNA casa. Pag. 1 titola e riassume in 1-2 righe col rimando; dentro si approfondisce senza rifare il riassunto né ripetere le cifre (salvo confronto).
- **Tra edizioni:** solo fatti nuovi; un tema già uscito torna con uno sviluppo che il titolo nomina; mai numeri invariati ripetuti. Calendario: solo la seduta precedente. Agenda: "perché conta" riscritto solo se cambia. "In 30 secondi": tre punti nuovi.

## 8. Pubblicazione
Sito: https://paologom.github.io/Gommberg-Terminal-Daily/ (ramo main). Non toccare index.html, README.md, assets/.
1. **Indice:** `voce.json` (titolo, sommario = i 3 punti di In 30 secondi, notizie, temi da elenco chiuso, approfondimenti {tema, titolo, formato}, meccanismi, parole, termometri, errata), poi `python3 /home/claude/gtd/redazione/edizioni_voce.py --pdf "<pdf>" --data AAAA-MM-GG --voce voce.json --registro /home/claude/gtd/redazione/pronostici/<lunedì>-settimana.json --stato /home/claude/lavoro/stato.json --sigle /home/claude/lavoro/testo.json` (lunedì: `--verdetto`). Calcola numero, ticker, scommessa, glossario; rifiuta numeri esistenti (fermati e segnalalo).
2. **Cancello:** `bash /home/claude/gtd/redazione/controlli_tutti.sh "<pdf>" <N>`: ESITO OK.
3. **Sito:** `bash /home/claude/gtd/redazione/pubblica.sh "<pdf>" <N> AAAA-MM-GG /home/claude/lavoro/fatti.json` (commit, push, verifica PUSH_OK fino a 3 tentativi). La sua ultima riga ("Sito: aggiornato (commit X)" o "Sito: NON aggiornato - <errore>") va identica nel messaggio finale.
4. **Archivio Claude** (dopo PUSH_OK o il terzo tentativo fallito): Artifact `action: "read"` su https://claude.ai/artifact/MuwDrCHDGXuADtKtL7cFcH, poi `action: "publish"` con quell'`url`, `file_path` = `/home/claude/gtd/redazione/archivio_claude.html` (non modificarla), `files` = {"edizioni.json": "/home/claude/gtd/edizioni.json", "pdf/AAAA-MM-GG-gommberg-NNN.pdf": "<pdf>"}, senza `capabilities` né `icon`. Rifiutata per versione più recente: ripubblica uguale (max 2 volte). Verifica con `action: "list"`, `scope: "files"`. Riga finale: "Archivio Claude: aggiornato" o "NON aggiornato".
5. Passaggio fallito: riprova una volta, poi consegna il PDF e di' cosa non è aggiornato.

## 9. Lettori e sigle
Ogni sigla non ovvia si spiega tra parentesi (max 6 parole) alla PRIMA occorrenza dell'edizione, una volta sola, con la forma di `glossario.json` (sigla nuova: aggiungila). Mai spiegate: Fed, BCE, PIL, S&P 500, Nasdaq, Dow Jones, ETF, USA, UE, FMI.

## 10. Revisione rafforzata
I numeri delle API li controllano gli script; la revisione copre il resto.
- Un revisore `model: "sonnet"` che non ha scritto il numero; riceve pdftotext, `fatti.json`, `fonti.json`, notizie dell'edizione precedente.
- **Fino a 25 verifiche**, in ordine: (1) OGNI scheda di top story, notizie, calendario e cause C: aprire l'URL, citazione presente, data giusta, PDF fedele (cifre, date, niente cause aggiunte); (2) agenda: solo l'evento principale; (3) conferma indipendente della top story; (4) senza aprire pagine: ripetizioni, frasi senza scheda, righe → fuori regola. Cifre non coperte entro le 25 restano solo con scheda di livello 1.
- Scrive in `fatti.json` `verifica` = confermato | errato | non_conclusivo e `nota_revisore`; restituisce solo gli errori. Se contesta un fatto, ricontrolla tu la fonte; se il dubbio resta, si toglie. Il lunedì verifica pag. 6 contro `verdetto.json` e registro. Senza Agent: stessa verifica, stesso limite.

## 11. Autocorrezione e cancello
Paolo non riceve bozze, domande né notifiche (mai PushNotification): l'unico messaggio è la consegna. Si pubblica solo ciò che passa i controlli; il resto si corregge o si toglie, fino a 3 giri (`APP_ERRORI.md`). Ogni mattina confronta le schede di ieri (`redazione/fatti/`) con le notizie: un fatto smentito va in Errata corrige. Nessuna edizione solo senza il minimo vitale (repository o API irraggiungibili, PDF impossibile): una riga nel messaggio.

## 12. Note pratiche
Il permesso di push viene dalla sessione che crea l'attività: se va ricreata, da una sessione col repository in scrittura.

## 13. Budget di token
- Una lettura di questo file e del modello. Mai aprire per intero motore, script, `edizioni.json`, PDF o pagine web.
- Niente ricerche doppie: apri articoli solo per i fatti contestati.
- Script dell'edizione modificato con Edit, mai riscritto né stampato. Un rendering per giro, correzioni tutte insieme, controllo visivo = anteprima.
- Output corti (`-q`, `| tail`). Niente Gmail, Drive, Docs, Canva.
