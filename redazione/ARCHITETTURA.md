# Architettura del Gommberg

La mappa del sistema: quali parti ci sono, chi legge che cosa, e che cosa si rompe lontano se tocchi qui. Serve a chi sviluppa (per sapere dove guardare prima di cambiare) e al capo sviluppo del rilascio (per ordinare le voci e vedere i conflitti). Non contiene storia né cose da fare: la storia sta in `PROGETTO.md`, lo stato in `STATO.md`, le cose da fare nel Registro dei lavori.

**Regola di manutenzione.** Chi cambia un contratto (un file letto da un'altra parte, un campo di `edizioni.json`, un comando del mattino) aggiorna questa pagina e la rete del collaudo nello stesso commit. Scritta il 21/11/2026 (G-39), verificata sul codice di quel giorno.

## 1. Il viaggio di un'edizione

```
8:58 attività programmata (Sonnet, app di Claude; testo in ATTIVITA.md)
  │  legge ISTRUZIONI.md + appendici APP_*.md, parte da prepara.sh
  │  connettori dei dati: FMP, Alpha Vantage, EODHD (Euro Stoxx 50; regole in APP_DATI.md)
  ▼
cartella di lavoro /home/claude/lavoro  (fuori dal repository)
  dati.json ─ contesto.json ─ fatti.json ─ edizione_AAAA-MM-GG.py ─ stato.json | verdetto.json
  │  gommberg_engine.py (+ scommessa/pagina6.py)  →  PDF di 6 pagine, voce_indice.json, riempimento.json
  │  controlli_tutti.sh (tutti i controlli)       →  testo.json (sigle), ripetizioni.json, anteprima.png, coerenza_incarico.json
  │  revisione (agente) → desk (desk.py)          →  revisione.json, coerenza.json (il ragionamento), desk_ok.json
  │  edizioni_voce.py                             →  la voce in edizioni.json
  ▼
pubblica.sh  →  un commit "Edizione #NNN - data" sul ramo principale (main)
  pdf/  edizioni.json  redazione/fatti/  redazione/sorgenti/  dati/uscite.json
  pannello/registro.json (pannello.py)   e/  dati/  feed.xml  sitemap.xml  ultima/ (pagine.py)
  ▼
GitHub, a ogni push su main (zero token)
  sito.yml        costruisci.py → Cloudflare Workers → gommberg.com (file statici + servizio dei lettori su /api/*; se
                  il servizio non si pubblica, soli file statici), poi verifica dal vivo (collaudo_sito.py --veloce)
  newsletter.yml  (solo se cambia edizioni.json) newsletter.py → Kit → email agli iscritti
  mattino.yml     appena sito.yml finisce per il commit dell'edizione: mattino.py controlla uscita, sito, pubblicazione, newsletter, pannello; poi job gomm: gomm.py aggiunge le visite di ieri a dati/gomm.json, commit su main e sito ripubblicato. Le sveglie delle 10:15 lun-ven restano per l'edizione non uscita
  segnalazioni.yml  ogni ora: sito/segnalazioni.py legge i commenti segnalati della Gommunity e apre una segnalazione a Paolo
```

Fuori dal viaggio dell'edizione, le **mail straordinarie** (auguri, avvisi, sondaggi): un file per mail in `redazione/dem/`, `dem.yml` (a ogni cambiamento su main e ogni sera) le allinea in Kit con `dem.py sincronizza`. Formato e regole: `redazione/dem/LEGGIMI.md`.

## 2. Le parti

| Parte | Dove sta | Che cosa fa |
|---|---|---|
| Regole della redazione | `ISTRUZIONI.md`, `APP_*.md`, `NOTA_DEL_GIORNO.md`, `edizione_modello_v6.py` | Ciò che Sonnet legge ogni mattina: decide che cosa viene scritto |
| Lessico e fonti | `glossario.json`, `meccanismi.json`, `fonti.json`, `autori.py` | Sigle, meccanismi, livelli delle fonti; `autori.py` è l'unica definizione di autore, fonte primaria, fatto confermato e dato ufficiale: la usano il controllo e le misure |
| Dati di mercato | `controlli_dati.py`, `numeri.py`, `contesto.py`, `scommessa/dati/*.csv`, `chiusure.csv` | Schema di `dati.json`, nastro e tabelle di pag. 5 calcolati dal codice, archivio delle chiusure, contesto dei movimenti |
| Motore | `gommberg_engine.py`, `extra_voce.py`, `giorni.py` | Impagina il PDF, scrive `voce_indice.json`; calendario delle uscite e numero dell'edizione |
| Scommessa | `scommessa/` (`pagina6.py`, `valuta.py`, `pronostico.py`, `metodo.json`, `pagella.json`), `pronostici/` | Pag. 6, registro della settimana, punteggi |
| Controlli | `controlli_tutti.sh` e i `controlli_*.py`, `anteprima.py` | Il cancello del mattino: ciò che non passa si corregge o si toglie |
| Revisione e desk | `desk.py`, `memoria.py`, `ricerche.py` | Riscritture del desk, memoria dei fatti già verificati |
| Indice | `edizioni_voce.py` → `edizioni.json` | Una voce per edizione: è il contratto centrale (vedi 3) |
| Pubblicazione | `pubblica.sh`, `messaggio.py` | Copia, archivia i sorgenti, rigenera le pagine, commit e push |
| Sito | pagine fisse in radice (`index.html`, `archivio.html`...), `assets/`, `pagine.py`, `sito/costruisci.py`, `sito/statico.py`, `robots.txt` | Pagine scritte a mano che si riempiono via JavaScript dai file di dati; pagine per edizione generate. `statico.py` (lo chiama `costruisci.py`, scrive solo nel sito pubblicato, mai nel repository) aggiunge per i motori di ricerca le pagine `impara/<parola>.html`, il contenuto di riserva di home, Impara e Archivio e le pagine di Impara nella sitemap (G-35) |
| Newsletter | `newsletter.py` (compone anche testata e fascia dei mercati), `newsletter_cornice.html` e `newsletter_modello.html` (copiati a mano in Kit: "Gommberg cornice" per le edizioni, "Gommberg" predefinito) | L'email del mattino dalla scheda `e/NNN.json` |
| Pannello | `pannello.py`, `misure.py`, `gancio_token.py`, `pannello/` | Una riga per edizione: orari, lavoro, qualità, consumo; pagina Invii per le mail straordinarie |
| La Gommunity | `sito/lettori.js` (il servizio, l'unico codice che gira sul sito), `assets/lettori.js` e `lettori.css` (la sezione), `regole.html`, database D1 `gommberg-lettori`; `sito/segnalazioni.py` con `segnalazioni.yml` (ogni ora: avviso a Paolo per ogni commento segnalato); `sito/servi_lettori.mjs` (il sito in locale con il servizio vero); regole e procedura in `sito/LETTORI.md` | Sentiment Toro/Orso, commenti con nomi unici, risposte, like e Segnala accanto all'edizione (G-13) |
| Mail straordinarie | `dem.py`, `dem/` (un file per mail), `.github/workflows/dem.yml`, `grazie.html` (risposta ai sondaggi) | Il file è la verità, Kit l'esecutore: regole, vista del pannello, allineamento con Kit, segnalazione a Paolo |
| Collaudo e rilascio | `collaudo.py`, `rete/`, `rilascia.sh`, `sito/collaudo_sito.py`, `mattino.py`, `.github/workflows/`; fuori dal repository il Registro dei lavori e il giro della sera (attività programmata, testo in `ATTIVITA.md`) | Vedi 4 e 5 |
| Prove | `PROVA.md`, `prova.sh` | Edizioni di prova con l'attività vera |
| Gestione | `CARTA.md`, `STATO.md`, `AZIONI.md`, `PROGETTO.md`, `ATTIVITA.md` | Visione, stato, lezioni, storia, testo delle attività |

## 3. Chi legge che cosa (i contratti)

Un file della colonna di sinistra è un contratto: cambiarne forma o significato tocca tutti quelli a destra.

| File | Lo scrive | Lo leggono |
|---|---|---|
| `edizioni.json` (una voce per edizione) | `edizioni_voce.py` | `pagine.py` (tutto il sito), `controlli.py`, `controlli_fatti.py`, `controlli_contenuti.py` (edizioni precedenti: temi, grafici, Stamattina), `memoria.py`, `misure.py`, `pannello.py`, `newsletter.py`, `mattino.py`, `ultima/index.html` |
| `e/NNN.json`, `e/NNN.html`, `e/NNN.png`, `e/pagine.json` | `pagine.py` | `index.html`, `glossario.html`, `newsletter.py` (la scheda `e/NNN.json`), anteprime di WhatsApp; il servizio `sito/lettori.js` controlla da `e/NNN.json` che l'edizione esista e da `dati/recenti.json` qual è la più recente (il sentiment si vota lì) |
| `dati/recenti.json`, `indice.json`, `cerca.json`, `storico.json`, `redazione.json` | `pagine.py` | `index.html`, `scommessa.html` (recenti); `archivio.html` (indice, cerca); `glossario.html`, `numeri.html` (storico); `progetto.html`, `numeri.html` (redazione); `mattino.py`, `collaudo_sito.py` |
| `dati/uscite.json` | `pubblica.sh` | `numeri.html` (puntualità) |
| `dati/gomm.json` (visite dei giorni completi dal 17/10) | `gomm.py`, nel job gomm di `mattino.yml` | `assets/gomm.js` (il GOMM: un solo calcolo), letto da `numeri.html`, dal nastro di `index.html` e dal blocco in fondo alle pagine `e/` |
| `redazione/fatti/AAAA-MM-GG.json` | `pubblica.sh` (dalle schede del mattino) | `memoria.py`, `misure.py`, `pannello.py`, `collaudo.py` |
| `redazione/sorgenti/AAAA-MM-GG/` | `pubblica.sh` | `collaudo.py` (rifare un'edizione, congelare un campione) |
| `redazione/glossario.json`, `glossario_sito.json`, `meccanismi.json` | a mano (e la redazione, per glossario e meccanismi) | `controlli_testo.py`, `edizioni_voce.py`, e **il sito**: `glossario.html` |
| `redazione/scommessa/pagella.json` | `valuta.py`, con il verdetto della settimana | pag. 6 del PDF, e **il sito**: `scommessa.html`, `numeri.html` |
| `redazione/scommessa/metodo.json`, `pronostici/*.json` | a mano / `pronostico.py` | `pagina6.py`, `valuta.py`, `edizioni_voce.py` |
| `redazione/chiusure.csv` (chiusure delle serie senza archivio nella scommessa) | `pubblica.sh` (`numeri.py --archivia`, dal `dati.json` del giorno) | `numeri.py` (`tabelle_da_dati`: le tabelle di pag. 5 e le loro note, calcolate e mai scritte a mano, con la data di ogni riga anche quando un mercato è chiuso), `controlli_dati.py`, `controlli_numeri.py` |
| `FESTIVI` in `gommberg_engine.py` (i giorni senza edizione) | a mano, ogni dicembre (`APP_FESTIVI.md` §4) | il motore stesso e `giorni.py`, e tramite lui `prepara.sh`, `controlli_tutti.sh`, `edizioni_voce.py`, `controlli_contenuti.py`, `mattino.py`, `scommessa_giorno.sh` (uscite e numero dell'edizione) e `controlli_dati.py` (età di un dato, contata in giorni di uscita) |
| `redazione/fonti.json` | a mano | `autori.py` (e, tramite lui, `controlli_fatti.py`, `misure.py`, `pannello.py`), `controlli_testo.py`, `controlli_contenuti.py`, `controlli_ripetizioni.py` |
| `pannello/registro.json`, `taratura.json` | `pannello.py` | `pannello/index.html`, `mattino.py` |
| `redazione/dem/AAAA-MM-GG-nome.md` (una mail straordinaria) | a mano (Claude, con l'ok di Paolo) | `dem.py` → `pannello/invii.json` (`dem.py salva`; il collaudo pretende che sia allineato) e Kit (`dem.yml`); usa `newsletter.py` (colori, cornice, chiamate a Kit) e `giorni.py` (giorni di uscita) |
| `/tmp/gtd_token.json` (token e, in `web`, ricerche e pagine non raggiunte) e la trascrizione della sessione a cui punta | `gancio_token.py` (`.claude/settings.json`) | `pannello.py --indici`; `controlli_fatti.py` (riscontra le ricerche dichiarate in `"conferma_cercata"` con quelle fatte davvero; senza gancio non conclude nulla) |
| `voce_indice.json`, `testo.json` (cartella di lavoro) | motore; `controlli_testo.py` | `controlli_temi.py`, `controlli_contenuti.py`, `edizioni_voce.py`, `messaggio.py` |

Tre cose da ricordare:
- **Quattro file della redazione sono pubblici**: `glossario.json`, `glossario_sito.json`, `meccanismi.json`, `scommessa/pagella.json` (elenco `LETTI` in `costruisci.py`). Tutto il resto di `redazione/` non arriva mai su gommberg.com.
- **Le pagine in `e/`, `dati/`, `ultima/`, `feed.xml` e `sitemap.xml` sono generate**: non si toccano a mano. Chi cambia `pagine.py` rigenera (`python3 redazione/pagine.py`) e committa le pagine nello stesso commit: il collaudo lo pretende.
- **`.claude/settings.json` non filtra i siti**: contiene il gancio e il permesso a WebSearch. Quali fonti valgono lo decide solo `fonti.json`; le pagine che non si aprono le annota il gancio e le mostra il pannello (`fallite`).
- **Fuori dal repository**: il testo delle attività programmate (app di Claude, copia in `ATTIVITA.md`: l'edizione, la misura della lettura, il giro della sera), la pagina e i dati del Registro dei lavori, i due modelli di email e il modulo di iscrizione (Kit), DNS, Worker e database D1 dei lettori (Cloudflare; i commenti si tolgono da lì finché non c'è G-51, `sito/LETTORI.md`), i segreti di GitHub (`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `KIT_API_KEY`), GoatCounter, Search Console. Un cambiamento che li riguarda non lo vede nessun collaudo: va scritto nel piano del rilascio e provato a mano.

## 4. La rete di non regressione

Un solo comando, `python3 redazione/collaudo.py` (meno di un minuto, senza rete e senza modelli), dopo ogni modifica:

1. sintassi di tutti i `.py` e `.sh`; 2. avvio (`prepara.sh` in tre giorni tipo); 3. pagina modello impaginata e controllata, e la regola dei fatti e il gancio su casi costruiti apposta;
4. **rete**: le edizioni campione di `redazione/rete/` rifatte dai loro sorgenti con il kit di oggi lungo la catena del mattino, e confrontate con l'atteso (`atteso/`): testo del PDF, esito dei controlli, voce di `edizioni.json`, email, numeri del pannello;
5. sito: file validi, link interni, **pagine generate identiche a quelle nel repository**, `costruisci.py` senza avvisi; 6. lettori: il servizio vero contro un database finto (`sito/prova_lettori.mjs`, serve Node 22.5 o più), la sintassi del codice del browser, la configurazione e l'avviso sulle segnalazioni (`sito/segnalazioni.py` a secco); 7. pubblicazione a secco.

Ogni differenza ferma. Se è un guasto si corregge; se è voluta si rilancia con `--atteso`, che riscrive l'atteso e stampa che cosa è cambiato: quel cambiamento è nel commit e nel resoconto del rilascio, dove lo vede anche Paolo. `--campione AAAA-MM-GG` congela un'edizione nuova (accettata solo se, rifatta, è identica a quella pubblicata).

Come cresce: un guasto arrivato ai lettori diventa un campione o un controllo in più, nello stesso rilascio che lo corregge. I campioni coprono oggi un lunedì con il verdetto (16/11), un giorno qualsiasi (18/11) e un venerdì passato dal desk (20/11).

Che cosa la rete **non** vede: ciò che Sonnet scriverà con regole nuove (serve un'edizione di prova, `PROVA.md`), l'aspetto grafico (colori, immagini: si guarda l'anteprima), i servizi esterni (Kit, Cloudflare), le pagine nel browser (le apre `collaudo_sito.py`, su GitHub a ogni push sul ramo di rilascio).

## 5. Il rilascio e la serata

Il ramo principale è ciò che i lettori vedono: ogni push lo ripubblica. Per questo il lavoro si fa sul ramo `rilascio` e main riceve un merge alla volta, solo a collaudo verde (G-39). Dal 23/11 il lavoro si fa in **serate** (G-57): Paolo preme un pulsante, il capo sviluppo fa il resto, Paolo approva due volte (partenza e rilascio). Dal 24/11 vale una regola sola: **un tasto c'è solo se quel clic basta**, e il Registro dice sempre la verità su che cosa sta succedendo.

```
bash redazione/rilascia.sh avvia      all'inizio della serata: la sessione va sul ramo rilascio, allineato a main
   ... una voce alla volta: modifica, collaudo.py, commit, git push origin rilascio ...
bash redazione/rilascia.sh collauda   quando si vuole: collaudo e resoconto (con la finestra), main non si tocca
bash redazione/rilascia.sh pubblica   dopo il Rilascia di Paolo: l'orario, i cinque cancelli, poi un solo merge su main
bash redazione/rilascia.sh annulla    "torna indietro": toglie da main l'ultimo rilascio
```

I cinque cancelli di `pubblica`: niente modifiche non salvate; il ramo contiene l'ultimo main; collaudo verde; **ok di Paolo** se cambia ciò che il lettore vede (file pubblici del sito, testo del PDF o email dei campioni, modello della newsletter); collaudo di GitHub verde sullo stesso commit (`collaudo.yml`: stesso collaudo su un'altra macchina, più il sito aperto in un browser e confrontato con gommberg.com). Prima dei cancelli l'orario: dal lunedì al venerdì tra le 8:30 e le 10:30 main non si tocca (`--guasto` solo per un guasto che blocca l'uscita).

**Le tre finestre.** Ogni voce ha nel Registro un `giorno` e una `finestra`, scritti dal capo sviluppo; la finestra vera la dice il resoconto di `rilascia.sh` (riga "Finestra"), non la chat. Un Rilascia manda in linea **tutto il ramo**: la finestra della serata è quella del resoconto sul ramo intero, e se sul ramo c'è già lavoro con prova anche il lavoro nuovo aspetta la prova (il PRIMA lo dice nel "quando").
- **Ogni giorno**: le edizioni campione escono identiche e non cambiano le regole di scrittura. In linea la sera stessa del Rilascia.
- **Con prova**: cambiano le regole di scrittura o un campione esce diverso. Si sviluppa ogni giorno fino a Pronta; una sola edizione di prova il venerdì dopo l'edizione vera, per tutto il ramo (procedura A di `PROVA.md`), lanciata dal capo sviluppo. Fino alla prova la serata è `con-prova` e **non ha il tasto**: il Registro dice il giorno della prova. Dopo la prova il capo sviluppo riscrive il DOPO con l'esito: se è andata bene la serata torna `pronta`, Paolo vede il tasto e il Rilascia va in linea quella sera.
- **Con Paolo**: ciò che il lettore vede (l'ok va nel riassunto DOPO), soldi, terzi, irreversibile. Le ultime tre lo script non le vede: le dichiara il capo sviluppo.

**La serata.** Un pulsante nel Registro ("Avvia la serata") apre la chat del capo sviluppo: Claude non parte mai da solo. In questo primo periodo Paolo approva partenza e rilascio (scala dell'autonomia, gradino 2). Il capo sviluppo, nell'ordine: rilegge `STATO.md` su main, le voci della settimana e gli appunti nuovi (gli appunti diventano voci con giorno e finestra, o entrano nella scheda giusta); aggiorna Salute; scrive il PRIMA; al Parti lavora una voce alla volta, mai in parallelo (le voci sulla stessa pagina o sullo stesso file si fanno insieme, sull'ultima versione); fa collaudare a un agente che non ha visto il lavoro; scrive il DOPO; al Rilascia mette in linea; verifica dal vivo; scrive ALLA FINE e Salute. Le edizioni vengono prima: se i token non bastano la serata si ferma e lascia in fila ciò che non entra. Le stanze di disegno aperte da Paolo restano possibili: la voce si segna occupata (`occupata` nella scheda) e si consegna al capo sviluppo, che integra.

**Chi esegue Parti e Rilascia.** Paolo li dà dove vuole, e in tutti e due i casi il suo clic basta:
- **nella chat della serata**: la chat scrive il consenso (`da: "chat"`) e lo esegue subito;
- **dal Registro**: il tasto scrive il consenso e lo esegue il **giro della sera**, un'attività programmata ("Gommberg: giro della sera") che passa agli orari scritti in `meta/giro` (oggi 19:47, 21:47, 23:47 e 01:47, tutti i giorni). Il tasto c'è solo se un giro passerà ancora in quella sera (la sera di un giorno va dalle 6:00 all'ultimo giro, anche dopo mezzanotte): dopo l'ultimo giro il Registro lo dice e il tasto torna alle 6:00.
Chi prende il lavoro (giro o chat) lo segna prima di cominciare con una scrittura condizionata alla versione (`ifVersion`): se la serata è già presa, si ferma. Così due esecutori non lavorano mai sulla stessa serata.

**Un solo lavoro sul ramo.** Il ramo `rilascio` è uno e un Rilascia manda in linea tutto ciò che c'è sopra. Quindi: non si prende un Rilascia se un'altra serata è `partita` o `in-rilascio`, né un Parti se un'altra è `partita`, `in-rilascio` o `pronta` con un Rilascia in coda; chi trova il ramo occupato lascia la serata com'è e lo scrive nel messaggio. Il DOPO di uno sviluppo descrive tutto il ramo (e chiude le serate che assorbe); se sul ramo c'è lavoro con prova ancora da provare, la serata è `con-prova`, qualunque sia la finestra delle voci nuove. La pagina applica le stesse regole: senza ramo libero o con una prova da fare non mostra il tasto e dice perché.

**La prova del venerdì.** Il giorno della prova la serata `con-prova` chiede a Paolo di aprire la chat (messaggio pronto): il capo sviluppo, dopo l'edizione e il controllo del mattino, lancia la procedura A di `PROVA.md` dal ramo `rilascio`, legge l'edizione di prova e scrive `dopo.prova` = {`giorno`, `esito` `ok` o `ko`, `nota` (che cosa ha mostrato, una frase)}. Se è `ok`: la serata torna `pronta` e il DOPO dice l'esito, quindi Paolo vede il tasto. Se è `ko`, o se il giorno passa senza esito, il Registro mostra Fermo.

**Il giro della sera, passo per passo.** Il testo dell'attività rimanda qui; vale anche per la chat che esegue un Parti o un Rilascia.
1. Cerca nelle `serate` un Rilascia da eseguire (`stato` `pronta` con `rilascio.esito` approvato o corretto, senza `ferma`) o un Parti (`stato` `preparata` con `partenza` approvata o corretta, senza `ferma`). Se non c'è nulla scrive `meta/giro.ultimo` = {`quando` (ora di inizio), `esito`: `niente`, `testo`: "Niente da fare"} e finisce, senza aprire il repository.
2. Controlla che il ramo sia libero (paragrafo "Un solo lavoro sul ramo") e prende la serata: `stato` `in-rilascio` o `partita`, `preso` = {`da` (con l'articolo: "il giro delle 21:47", "la chat della serata"), `quando`, `aggiornato`}, con `ifVersion`. Subito dopo scrive `meta/giro.ultimo` = {`quando` (ora di inizio), `esito`: `al-lavoro`, `testo` ("preso il Rilascia della serata del 24/11")}: un lavoro lungo non deve sembrare un giro saltato.
3. **Rilascio**: rilegge `STATO.md` su main; `bash redazione/rilascia.sh avvia`, poi `bash redazione/rilascia.sh pubblica`, con `--ok-di-paolo` solo se una riga del DOPO ha `lettore` non vuoto (è ciò che Paolo ha visto prima di cliccare; se il resoconto chiede l'ok e nessuna riga lo dice, ci si ferma). Prima della pubblicazione tre controlli: la serata non ha `ferma` (si rilegge); le voci dei commit sul ramo (riga "voci" del resoconto) devono stare tutte nel consenso; se la riga "Finestra" dice CON PROVA, `dopo.prova.esito` deve essere `ok`. Se un controllo o un cancello ferma, nulla va in linea e si passa al punto 5. Se pubblica: aspetta `sito.yml` verde (verifica dal vivo), poi scrive `fine` e `stato` `in-linea` (sempre: se nel frattempo è arrivato un Ferma, la serata è comunque in linea e `fine.testo` lo dice; si toglie con Torna indietro), segna Fatta le voci Pronte del rilascio con data ed esito, aggiunge il rilascio in `meta/salute.rilasci`, aggiorna `STATO.md` e una riga di `PROGETTO.md` su main.
4. **Sviluppo**: lavora come capo sviluppo (paragrafo "La serata"), una voce alla volta tra quelle del consenso; dopo ogni voce aggiorna `preso.aggiornato` e rilegge la serata: se c'è `ferma`, salva sul ramo e scrive `stato` `ferma`. Alla fine lancia `bash redazione/rilascia.sh collauda` sul ramo intero, scrive il DOPO (tutto il ramo, chiudendo le serate che assorbe) e `stato` `pronta` se la riga "Finestra" non dice CON PROVA, altrimenti `con-prova` con `dopo.prova` = {`giorno`: il venerdì della prova, `esito`: `da-fare`}. Non rilascia mai nello stesso giro: serve il Rilascia di Paolo.
5. **Se si ferma** (cancello rosso, conflitto, permesso negato, qualsiasi cosa che non sa risolvere da solo): `stato` `ferma`, `ferma` = {`quando`, `da`, `nota` (la causa in parole semplici, una frase), `serve_chat`: true}, e una riga in Salute con causa e rimedio. Il Registro mostra "Fermo" e il pulsante "Apri la chat" con il messaggio già pronto.
6. Sempre, alla fine: `meta/giro.ultimo` = {`quando` (ora di inizio), `esito` (`niente`, `fatto`, `ferma`), `testo` (una frase)}, ma solo se l'`ultimo` scritto non è di un giro partito dopo (la traccia non torna mai indietro nel tempo); poi un messaggio a Paolo di al massimo quattro righe.

**Che cosa vede Paolo.** Il Registro calcola lo stato da questi dati e non scrive mai "aspetta" quando nessuno lavora: **Tocca a te** (c'è un tasto, o la chat se è notte), **In coda** (ok scritto, con l'ora del giro che lo eseguirà), **Al lavoro** o **In corso** (qualcuno l'ha preso, con chi e da che ora), **Aspetta la prova** (con il giorno; il giorno stesso diventa Tocca a te, con "Apri la chat" per lanciarla) o **Aspetta** (il ramo è occupato da un'altra serata, e dice quale), **In linea** (da che ora, verificato dal vivo o no), **Fermo** (con la causa e "Apri la chat"), **Fermata** (da Paolo, nulla in linea). Diventa Fermo da sola anche quando la macchina tace o una prova manca: un giro passato senza prendere un ok in coda, un giro che non ha lasciato traccia entro 40 minuti dal suo orario, uno sviluppo senza aggiornamenti da 3 ore, una messa in linea senza esito da 90 minuti, una prova andata male o il cui giorno è passato senza esito. In Salute la riga "Giro della sera" dice l'ultimo passaggio e il prossimo, e diventa rossa se un passaggio è saltato. Il verde, nelle righe delle serate, è solo per ciò che è in linea.

**I tre riassunti, formato fisso.** Asciutti, per il superiore e non per il tecnico: niente nomi di file, rami o commit se non servono a decidere. Lo stesso testo va in chat e nel Registro.
- **PRIMA** (per partire): una riga per sviluppo, con che cosa cambia e per chi, perché, rischio (basso, medio, alto) e quando andrà in linea. Paolo dice Parti, per tutto o per una parte.
- **DOPO** (per rilasciare): che cosa è pronto, cioè **tutto ciò che è sul ramo** e che il Rilascia manderà in linea (le serate precedenti ancora aperte si chiudono con `stato` `chiusa` e la nota "unita alla serata ..."); che cosa cambia per il lettore, con le immagini prima e dopo (in chat); l'esito dei controlli in una riga e quello del collaudo indipendente; che cosa non ho potuto verificare; per la finestra con prova, il giorno della prova. Paolo dice Rilascia.
- **ALLA FINE** (in linea): che cosa è in linea e da che ora, verificato dal vivo sì o no, come si torna indietro. Lo firma il capo sviluppo.

**Chi risponde.** Il capo sviluppo risponde del risultato dall'inizio alla fine, non del solo merge: tiene Salute (edizione, sito, newsletter, controlli partiti davvero, giri della sera, ultimi rilasci) e, quando qualcosa non va, lo scrive lì con causa e rimedio e lo dice a Paolo senza aspettare che lo scopra.

**Dove sta la serata nel Registro** (artifact `97f08bbc-950b-4b6e-83eb-4b8d032a3783`; si scrive con `db_write`, si legge con `db_get`). Date e ore sempre in ISO 8601 con il fuso (`2026-11-23T19:32:00+01:00`), giorni come `AAAA-MM-GG`; un valore fuori da quelli elencati la pagina lo mostra come "da decidere" o lo ignora.
- Nelle voci (`tasks/<id>`): `giorno` (`AAAA-MM-GG`), `finestra` (`ogni-giorno`, `con-prova`, `con-paolo`), `occupata` (testo: chi la tiene e fino a quando; vuoto o assente = libera). La pagina salva solo i campi che Paolo cambia.
- `serate/AAAA-MM-GG` (una seconda serata nello stesso giorno: `AAAA-MM-GG-2`): `stato` (`preparata`, `partita`, `pronta`, `con-prova`, `in-rilascio`, `in-linea`, `ferma`, `chiusa`), `responsabile`; `prima` = {`scritto`, `righe`: [{`codice`, `cosa`, `perche`, `rischio` (`basso`, `medio`, `alto`), `quando` (testo: "stasera", "sabato, dopo la prova"), `finestra`}]} (una riga senza codice, per esempio un appunto non ancora voce, nel consenso si nomina con l'inizio di `cosa`; se il PRIMA si riscrive, le spunte di Paolo ripartono tutte accese); `partenza` = {`quando`, `esito` (`approvata`, `corretta`, `fermata`), `voci`, `da` (`Registro` o `chat`)}; `preso` = {`da`, `quando`, `aggiornato`}; `dopo` = {`scritto`, `righe`: [{`codice`, `cosa`, `lettore`, `finestra`}], `controlli`, `collaudo`, `non_verificato`, `immagini` (dove sono, se non in chat), `prova` = {`giorno`, `esito` (`da-fare`, `ok`, `ko`), `nota`}}; `rilascio` = {`quando`, `esito` (`approvato`, `corretto`, `fermato`), `voci`, `da`}; `fine` = {`scritto`, `in_linea_da` (ora come testo, `21:10`), `verificato` (true/false), `testo`, `righe` (facoltative, come quelle del DOPO), `indietro`}; `ferma` = {`quando`, `da`, `nota`, `serve_chat` (true: si è fermata la macchina e serve Paolo in chat; false: l'ha fermata Paolo)}. Ferma dal Registro: se nessuno lavora la serata diventa subito `ferma`; se è `partita`, chi lavora la porta a `ferma` alla fine della voce in corso. Una serata `con-prova` non impedisce di avviarne una nuova; una `ferma` con `serve_chat` resta in vista finché la chat non la risolve. `voci` sono sempre liste di codici, senza doppioni. Il consenso dato in chat lo scrive il capo sviluppo, con `da: "chat"`: le serate sono il **registro dei consensi**, il dato su cui Paolo decide se salire di gradino.
- `meta/giro` = {`orari` (lista di `HH:MM`, gli stessi dell'attività programmata: si cambiano insieme), `creato`, `ultimo` = {`quando`, `esito` (`niente`, `al-lavoro`, `fatto`, `ferma`), `testo`}}.
- `meta/salute` = {`verificato`, `da`, `righe`: [{`nome`, `stato` (`ok`, `ko`, `attesa`), `testo`, `causa`, `rimedio`}], `rilasci`: [{`nome`, `quando`, `esito` (`ok`, `ko`), `testo`}], dal più recente}. "Torna indietro" nomina il rilascio più recente e apre la chat: è un'emergenza, non aspetta un giro. La pagina avvisa se la verifica ha più di 26 ore o una data illeggibile.
- `appunti/<id>` = {`testo`, `creato`, `stato` (`nuovo`, `assorbito`), `voce`}: alla serata il capo sviluppo li porta nelle voci e li segna `assorbito` con il codice.

Durante il lavoro i file di stato (`STATO.md`, `PROGETTO.md`, `AZIONI.md`) si aggiornano sul ramo principale (non ripubblicano il sito); tutto il resto sta sul ramo `rilascio`. Lo stesso vale, in qualunque giorno, per le mail straordinarie: i file di `redazione/dem/` e `pannello/invii.json` (sempre insieme, dopo `dem.py salva`) vanno su main direttamente, perché non toccano l'edizione né le pagine dei lettori; `dem.py`, `dem.yml` e la vista passano dal rilascio.

Dopo il merge: `sito.yml` pubblica e verifica dal vivo; la mattina dopo `mattino.yml` controlla l'edizione appena è pubblicata. Le prove con l'attività vera si fanno prima del merge dal ramo `rilascio` (procedura A di `PROVA.md`) e, per provare anche la pubblicazione, dopo il merge con una data simulata (procedura B).

Un guasto che blocca l'edizione passa davanti a tutto e segue la stessa strada in piccolo: `avvia`, correzione, `pubblica` (con `--guasto` se è la fascia dell'uscita).
