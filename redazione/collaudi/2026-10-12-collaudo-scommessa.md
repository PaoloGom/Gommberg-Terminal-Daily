# Collaudo tecnico della Scommessa - 12/10/2026

Simulazione di un lunedì seguendo ISTRUZIONI.md paragrafo 4. Settimana chiusa: 5-9 ottobre 2026 (registro di prova `collaudi/test-2026-10-05-settimana.json`). Nuovo pronostico: origine 9/10, settimana 12-16 ottobre. Lavoro su copie: `/home/claude/collaudo` (copia di `scommessa/`) e `/home/claude/pronostici_copia` (copia di `pronostici/`). Repository non toccato, salvo questo file e il PDF di prova.

Esito complessivo: **il flusso funziona dall'inizio alla fine**, senza errori bloccanti negli script. Ci sono però 4 punti da correggere prima del 19/10 (sezione "Da correggere prima del 19/10") e diverse ambiguità delle istruzioni.

## Tempi (orologio del sandbox, UTC)
- Clone: 19:35, pochi secondi.
- Lettura istruzioni e script: circa 2 minuti.
- Download dei dati: 10 chiamate, circa 1 minuto. FMP: 4 serie + treasury-rates + forex. Alpha Vantage: ACWI, FX_DAILY, CURRENCY_EXCHANGE_RATE, GLOBAL_QUOTE.
- Script: circa 2 secondi ciascuno.
  - `aggiorna_dati` 0,5 s;
  - `valuta` 2,1 s;
  - `pronostico` 1,8 s;
  - `grafico` 1,0 s.
- Ricerche web per la direzione: 4 ricerche e 3 letture.
- Installazione di svglib (mancava): 22 s.
- Pagina 6: 2 render.
- Totale fino al PDF: circa 5-10 minuti.

## Passo 1 - Aggiorna la storia
**Dati in partenza.** Tutti gli 8 file in `dati/` arrivavano già al 9/10/2026.
- 260 righe ciascuno, solo `acwi.csv` ne ha 100.
- Ho riscaricato 1-9 ottobre da FMP e Alpha Vantage e confrontato in codice con `dati/`: **0 differenze** su 8 serie.

**Dopo il 9/10 (lunedì 12/10, ore 21:35 Roma) non c'è nessuna chiusura ufficiale affidabile:**
- **Treasury:** nessuna riga del 12/10 in FMP treasury-rates, mercato obbligazionario chiuso per il Columbus Day. Comportamento atteso.
- **Alpha Vantage (ACWI, FX_DAILY EUR/USD):** ultima riga il 9/10.
- **FMP S&P 500 (7.799,51), VIX (15,30), BZUSD (106,50), EURUSD (1,11571):** l'endpoint `eod-light` restituisce già una riga datata 12/10 a mercato USA aperto (15:35 ET). Sono **valori intraday con la data di oggi**, indistinguibili da una chiusura se non si guarda l'ora o il volume (S&P 500: 1,47 miliardi di pezzi contro 5-6 di una seduta piena).
- **FMP Euro Stoxx 50 del 12/10 (6.192,9):** dubbio. Il volume è 911 mila contro i soliti 20 milioni circa, e close = low esatto. Escluso.

**Esecuzione.** `nuovi.json` = `{}`, poi `python3 aggiorna_dati.py nuovi.json`: exit 0, **nessun output**. Lo script non dice "niente da aggiungere".

**Prove su una cartella temporanea (`GOMMBERG_DATI`):**
- Riga di domenica (FMP forex ha righe del 4/10 e dell'11/10): respinta correttamente.
- Valore stringa: respinto.
- **Chiave `brent` invece di `brent_future`:** respinta, MA solo dopo aver già scritto `spx.csv`. La scrittura non è atomica: un file mezzo aggiornato.
- **Valore intraday dell'S&P 500 datato 12/10:** accettato senza obiezioni.

## Passo 2 - Verdetto (registro di prova)
**Comando:** `python3 valuta.py --settimana /home/claude/gtd/redazione/collaudi/test-2026-10-05-settimana.json --verdetto --json verdetto.json`

**Output:** `Verdetto 2026-10-05/2026-10-09: 11 punti su 14 (direzione 4, range 7; par 8.5)`.
- Controllo a mano coerente: direzione giusta su ACWI, S&P 500, Euro Stoxx 50 e UST 10; sbagliata su UST 2, Brent ed EUR/USD; 7 chiusure su 7 nel range.
- Il par 8,5 si ricostruisce così: 7 x 0,68 + 0,57 + 0,58 + 0,55 + 4 x 0,5.
- Note vuote: z del Brent 0,31, nessun cambio di contratto.
- `registro.csv` e `PAGELLA.md` vengono scritti in `/home/claude/collaudo`.

**Prova del blocco.** Senza le righe del 9/10 lo script si ferma con un messaggio chiaro ("manca la chiusura di venerdì... --festivo") e non scrive il registro. Bene.

## Passo 3 - Pronostico
**`redazione.json`.** Direzioni scelte sull'agenda del 12-16/10, cioè banche martedì, CPI mercoledì (consenso 3,6% a/a da 3,4%), PPI e vendite al dettaglio giovedì. Notizie di lunedì: attacchi Houthi su Riad, petroliere attaccate vicino a Hormuz, Brent +1,2% al mattino. Fonti: Reuters via Kitco, investingLive, TheStreet.
- ACWI su;
- S&P 500 su;
- Euro Stoxx 50 giù;
- UST 10 su;
- UST 2 su;
- Brent su;
- EUR/USD giù.

**Comando:** `python3 pronostico.py --origine 2026-10-09 --redazione redazione.json --uscita /home/claude/pronostici_copia`

**Output:**
```
MSCI ACWI (ETF)    base 160.9 range 158.2-163.6 redazione 161.6 (scarto +0.26 sigma) p_rialzo 60%
S&P 500            base 7812 range 7704-7921 redazione 7845 (scarto +0.31 sigma) p_rialzo 62%
Euro Stoxx 50      base 6197 range 6089-6308 redazione 6165 (scarto -0.29 sigma) p_rialzo 38%
Treasury 10 anni   base 5.24 range 5.122-5.358 redazione 5.28 (scarto +0.34 sigma) p_rialzo 63%
Treasury 2 anni    base 4.8 range 4.66-4.94 redazione 4.85 (scarto +0.36 sigma) p_rialzo 64%
Brent future       base 104.7 range 97.67-112.3 redazione 108.5 (scarto +0.50 sigma, AGGIUSTATA) p_rialzo 69%
EUR/USD            base 1.12 range 1.113-1.128 redazione 1.119 (scarto -0.10 sigma, AGGIUSTATA) p_rialzo 46%
```
- I due limiti funzionano. Brent 110 è stato portato a 108,46 (0,5 sigma); EUR/USD 1,1195 portato a 1,1193 (0,1 sigma).
- Con la cartella di default `../pronostici` (che da `/home/claude/collaudo` è `/home/claude/pronostici`) lo script avrebbe creato una cartella nuova fuori posto: per questo `--uscita` esplicito.
- **Il file scritto è `2026-10-12-settimana.json` e ha sovrascritto senza avviso** il registro storico della versione 0 con lo stesso nome (nella copia). Vedi sotto.

## Passo 4 - Grafico
**Comando letterale:** `python3 grafico.py ../pronostici/<lunedì>-settimana.json /home/claude/lavoro/c_forecast.png`. Va in errore con `FileNotFoundError`, perché `/home/claude/lavoro` non esiste e lo script non crea la cartella. Con una cartella esistente: PNG e SVG corretti. Etichette leggibili e senza sovrapposizioni, rombi verdi e rossi coerenti con la direzione.

## Martedì-venerdì (stato)
**`attuali.json`.** Livelli più recenti disponibili alle 21:35 Roma del 12/10:
- S&P 500 7.799,51 e Brent 106,50 (intraday FMP);
- Euro Stoxx 50 6.192,9 (FMP 12/10);
- UST 10 e UST 2 al 9/10 (mercato chiuso);
- EUR/USD 1,1159 (Alpha Vantage, 19:35 UTC);
- ACWI omesso: GLOBAL_QUOTE dà ancora il 9/10, e la variante "delayed" è rifiutata dal piano.

**Comando:** `valuta.py --attuali attuali.json --json stato.json`. Exit 0; registro e pagella non toccati (md5 invariato). Poi `grafico.py ... stato.json`: ok, cerchi arancioni e valori corretti.

**Problemi trovati:**
- Uno strumento invariato (variazione 0, es. Treasury chiusi o ACWI senza dato nuovo) risulta `strada_giusta: False`. In pagina diventerebbe "No" quando la risposta onesta è "invariato" o "n.d.".
- Le chiavi sconosciute in `attuali.json` (es. `brent_future`, che è il nome giusto in `nuovi.json`, o `SPX`) vengono ignorate in silenzio. Lo script ripiega sull'ultima riga di `dati/`, cioè la base di venerdì, e mostra "var 0,00%" come se fosse un dato vero.
- Nel grafico con lo stato le etichette arancioni dei valori (es. "6.193", "5,24%") toccano la tacca nera e la barra della riga sopra: leggibili, ma da rifinire.

## Pagina 6 (lunedì)
Script `pag6_lunedi.py` con `gommberg_engine.py`: tutti i numeri sono letti da `2026-10-12-settimana.json`, `verdetto.json` e `PAGELLA.md`, nessuno scritto a mano. Contiene:
- titolo;
- tesi;
- grafico;
- tabella a 6 colonne del paragrafo 4;
- nota *;
- box "Le regole del gioco" e "La pagella", con Glossario e Fonti.

Il PDF sta in **una pagina** con circa 4 cm liberi in fondo.

**Correzioni fatte dopo il controllo visivo (pdftoppm -r 70):**
1. Nel motivo dell'ACWI "+30%" veniva colorato in verde: il motore colora ogni "+numero" negli stili cell. Riscritto "di oltre il 30%".
2. La colonna Prob. andava a capo con "(rend.)": allargata.

Risultato in `2026-10-12-pag6-collaudo.pdf`. Il piè di pagina dice "pag. 1" perché è un PDF di una pagina sola.

## Da correggere prima del 19/10 (problemi degli script)
1. **`pronostico.py` sovrascrive senza avviso** `pronostici/<lunedì>-settimana.json`. Il 12/10 esiste già il registro della versione 0: rilanciare il flusso su quella data lo cancellerebbe. Serve un `--forza`, o il rifiuto se il file esiste.
2. **`aggiorna_dati.py` non è atomico.** Valida e scrive una serie alla volta, quindi un errore sulla terza chiave lascia le prime due già scritte. Conviene validare tutto e poi scrivere. Non segnala nemmeno valori intraday: si potrebbe rifiutare una data uguale a oggi prima delle 22:30 Roma, o chiedere un campo "tipo".
3. **`valuta.py` in modalità stato:**
   - rifiutare chiavi sconosciute;
   - segnalare quando ripiega su `dati/`;
   - restituire `strada_giusta: null` se l'ultimo valore è uguale alla base.
4. **Nomi incoerenti:** `brent_future` in `nuovi.json` e `dati/`, `brent` in `redazione.json`, `attuali.json` e registri. È la trappola più probabile del martedì (vedi il punto 3).

Minori:
- `grafico.py` non crea la cartella di uscita.
- La tabella di controllo di `pronostico.py` usa `%.4g`: mostra 7812 al posto di 7.811,54 e 1.12 per EUR/USD, inutile per una verifica.
- `aggiorna_dati.py` non stampa nulla con un file vuoto.
- `PAGELLA.md` usa i decimali inglesi ("8.5", "+0.8%"): chi la copia in pagina deve convertirli. Il formato poi va letto con regex, fragile: meglio un `pagella.json`.

## Istruzioni e METODO.md: punti ambigui, sbagliati o impossibili
1. **Percorsi.** Il paragrafo 4 dice di eseguire tutto da `/home/claude/gtd/redazione/scommessa` (cioè nel repository) e di scrivere il grafico in `/home/claude/lavoro`, che nessun passo crea. Il paragrafo 6.1 invece dice di lavorare in una cartella separata copiando i .py. Per la scommessa va detto esplicitamente:
   - che si lavora nel repository (`registro.csv`, `PAGELLA.md` e `dati/` vanno committati);
   - di fare `mkdir -p /home/claude/lavoro`.
2. **Passo 1, "chiusure dei giorni mancanti".**
   - Il lunedì mattina mancano le chiusure da lunedì a venerdì della settimana prima.
   - Non dice di evitare la riga del giorno stesso che FMP `eod-light` restituisce già intraday con la data di oggi: va scritto, perché i dati sembrano chiusure.
   - Non dice quale fonte usare per EUR/USD se Alpha Vantage è indietro: FMP forex ha anche righe del sabato e della domenica.
3. **Contraddizione sui Treasury.** METODO.md paragrafo 6 dice che le chiusure Alpha Vantage dei Treasury arrivano in ritardo e che "valgono quelle FMP"; il paragrafo 4 delle istruzioni usa solo FMP. Coerente, ma METODO.md paragrafo 3 elenca Alpha Vantage `TREASURY_YIELD` come fonte del backtest: va precisato che il backtest usa una fonte diversa da quella dal vivo.
4. **Festivi parziali.** `--festivo` vale per tutti gli strumenti insieme. Per un venerdì con i soli Treasury chiusi (es. Veterans Day) o la sola Europa chiusa, il flag lascerebbe passare dati vecchi anche sugli altri strumenti. Le istruzioni dicono "se venerdì le borse erano chiuse", senza coprire il caso misto.
5. **Colonna "rialzo del rendimento".** "Per i Treasury la colonna si chiama 'rialzo del rendimento'", ma la tabella è una sola con una sola intestazione. Nel collaudo: "63% (rend.)" e spiegazione nella nota *. Va deciso il formato.
6. **Modello contro paragrafo 4.** L'edizione modello (che il paragrafo 2 dice di copiare) ha a pagina 6 7 colonne, tra cui "Var. prevista", e un box regole diverso. Il paragrafo 4 ne vuole 6. Il modello andrebbe aggiornato al metodo 1.0, altrimenti chi lo copia sbaglia.
7. **Colori nel "perché".** Il motore colora i "+numero" anche nei testi delle celle: le istruzioni dovrebbero vietare segni nei motivi, oppure la colonna "Il perché" dovrebbe usare "celln".
8. **Direzione da scegliere senza sigma.** Il paragrafo 4.3 chiede una previsione in livello, ma la sigma (necessaria per stare tra 0,1 e 0,5) si vede solo dopo aver lanciato lo script. Funziona grazie ai limiti automatici, ma la motivazione può non corrispondere più al numero pubblicato: nel collaudo il Brent "110" è diventato 108,46. Un `--prova` che stampi sigma e livelli a +-0,1/0,3/0,5 aiuterebbe.
9. **Pagella "dalla PAGELLA.md".** Con il registro di prova la "stagione" contiene una settimana fittizia. Le istruzioni non dicono che `registro.csv` del repository non deve mai ricevere settimane di collaudo. Va detto, e conviene un flag `--prova` in `valuta.py` che non scriva il registro.
10. **Metodo in vigore.** `metodo.json` dice "in vigore dal 2026-10-19", ma gli script lo applicano a qualsiasi data senza controllo: un pronostico del 12/10 esce marcato versione 1.0.
11. **Stato martedì-venerdì.** `attuali.json` chiede "la data", le istruzioni chiedono anche "l'ora" per future e cambi: il formato non lo prevede. Nel collaudo l'ho messa nella stringa della data, e lo script la accetta.
12. **Simulazione di sera.** Le direzioni sono state scelte lunedì sera, con il movimento di lunedì già noto (Brent su, EUR/USD giù). In un lunedì vero, alle 8, questa informazione non c'è: i punteggi di un collaudo serale non misurano l'abilità.

## Prova di fine collaudo
- `git status` del repository pulito prima del commit: solo questi due file aggiunti.
- `pdf/`, `edizioni.json`, `redazione/pronostici` e `redazione/scommessa` non toccati.
