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
  pannello/registro.json (pannello.py)   e/  dati/  feed.xml  sitemap.xml  ultima/ (pagine.py; dati/parole.json con impara.py)
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
| Sito | pagine fisse in radice (`index.html`, `archivio.html`...), `assets/`, `pagine.py`, `impara.py`, `parole_giornale.json`, `sito/costruisci.py`, `sito/statico.py`, `robots.txt` | Pagine scritte a mano che si riempiono via JavaScript dai file di dati; pagine per edizione generate. `impara.py` (lo chiama `pagine.py`) fa crescere Impara con le parole che le edizioni spiegano (G-54): da solo collega le parole alle schede scritte a mano e prepara le proposte (`impara.py --proposte`, con i possibili doppioni); una scheda nuova entra solo con la definizione confermata a mano in `parole_giornale.json`. Se un ingresso manca o non si legge si ferma senza scrivere: `dati/parole.json` resta com'era e la pubblicazione va avanti. `statico.py` (lo chiama `costruisci.py`, scrive solo nel sito pubblicato, mai nel repository) aggiunge per i motori di ricerca le pagine `impara/<parola>.html`, il contenuto di riserva di home, Impara e Archivio e le pagine di Impara nella sitemap (G-35) |
| Newsletter | `newsletter.py` (compone anche testata e fascia dei mercati), `newsletter_cornice.html` e `newsletter_modello.html` (copiati a mano in Kit: "Gommberg cornice" per le edizioni, "Gommberg" predefinito; se la cornice manca l'invio fallisce e il controllo del mattino lo segnala, nessun ripiego su un altro modello; se Kit non risponde all'elenco dei modelli, 4 tentativi a 15 secondi e poi errore "Kit non risponde"; la creazione dell'invio non si ritenta mai) | L'email del mattino dalla scheda `e/NNN.json` |
| Pannello | `pannello.py`, `misure.py`, `gancio_token.py`, `pannello/` | Una riga per edizione: orari, lavoro, qualità, consumo; pagina Invii per le mail straordinarie |
| La Gommunity | `sito/lettori.js` (il servizio, l'unico codice che gira sul sito), `assets/lettori.js` e `lettori.css` (la sezione), `regole.html`, database D1 `gommberg-lettori`; `sito/segnalazioni.py` con `segnalazioni.yml` (ogni ora: avviso a Paolo per ogni commento segnalato); `sito/servi_lettori.mjs` (il sito in locale con il servizio vero); regole e procedura in `sito/LETTORI.md` | Sentiment Toro/Orso, commenti con nomi unici, risposte, like e Segnala accanto all'edizione (G-13) |
| Mail straordinarie | `dem.py`, `dem/` (un file per mail), `.github/workflows/dem.yml`, `grazie.html` (risposta ai sondaggi) | Il file è la verità, Kit l'esecutore: regole, vista del pannello, allineamento con Kit, segnalazione a Paolo |
| Collaudo e rilascio | `collaudo.py`, `rete/`, `rilascia.sh`, `sito/collaudo_sito.py`, `mattino.py`, `.github/workflows/`; fuori dal repository il Registro dei lavori (pagina in `registro/`) e il capo sviluppo (attività programmata, testo in `registro/CAPO.md`) | Vedi 4 e 5 |
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
| `redazione/sorgenti/AAAA-MM-GG/` (anche `coerenza_incarico.json` e `coerenza.json`) | `pubblica.sh` | `collaudo.py` (rifare un'edizione, congelare un campione), `impara.py` (il campo `parole` di `edizione.py`, letto senza eseguirlo) |
| `dati/parole.json` (le parole spiegate dalle edizioni che entrano in Impara: `voci` con `sigla`, `breve`, `spiega`, `varianti`, `da`; `alias` = parola di un'edizione → voce di Impara, anche scritta a mano; `tipo`) | `impara.py`, chiamato da `pagine.py` (generato: si committa con le pagine) | `glossario.html` (schede "Dalle edizioni", "Nell'ultima edizione", "dove l'abbiamo usata"), `numeri.html` (scheda "Parole e meccanismi spiegati"), `sito/statico.py` (pagine `impara/<parola>.html`) |
| `redazione/parole_giornale.json` (`stesse`: sinonimi; `fuori`: parole (per qualunque nome) o spiegazioni tolte a mano, con il perché; `confermate`: le schede nuove con la definizione rivista a mano, l'unica strada per entrare in Impara e per correggerle; `archivio`: le spiegazioni delle edizioni prima del 16/11/2026, dai PDF) | a mano, nel ramo di sviluppo | `impara.py` |
| `redazione/glossario.json`, `glossario_sito.json`, `meccanismi.json` | a mano (e la redazione, per glossario e meccanismi) | `controlli_testo.py`, `edizioni_voce.py`, `impara.py` (le schede scritte a mano vincono), e **il sito**: `glossario.html` |
| `redazione/scommessa/pagella.json` | `valuta.py`, con il verdetto della settimana | pag. 6 del PDF, e **il sito**: `scommessa.html`, `numeri.html` |
| `redazione/scommessa/metodo.json`, `pronostici/*.json` | a mano / `pronostico.py` | `pagina6.py`, `valuta.py`, `edizioni_voce.py` |
| `redazione/chiusure.csv` (chiusure delle serie senza archivio nella scommessa) | `pubblica.sh` (`numeri.py --archivia`, dal `dati.json` del giorno) | `numeri.py` (`tabelle_da_dati`: le tabelle di pag. 5 e le loro note, calcolate e mai scritte a mano, con la data di ogni riga anche quando un mercato è chiuso), `controlli_dati.py`, `controlli_numeri.py` |
| `FESTIVI` in `gommberg_engine.py` (i giorni senza edizione) | a mano, ogni dicembre (`APP_FESTIVI.md` §4) | il motore stesso e `giorni.py`, e tramite lui `prepara.sh`, `controlli_tutti.sh`, `edizioni_voce.py`, `controlli_contenuti.py`, `mattino.py`, `scommessa_giorno.sh` (uscite e numero dell'edizione) e `controlli_dati.py` (età di un dato, contata in giorni di uscita) |
| `redazione/fonti.json` | a mano | `autori.py` (e, tramite lui, `controlli_fatti.py`, `misure.py`, `pannello.py`), `controlli_testo.py`, `controlli_contenuti.py`, `controlli_ripetizioni.py` |
| `pannello/registro.json`, `taratura.json` | `pannello.py` | `pannello/index.html`, `mattino.py` |
| `pannello/piani.json` (i piani di Claude: nome, inizio, giorno e ora dell'azzeramento) | a mano, una riga per cambio di piano | `pannello/index.html` (rapporta ogni edizione al piano in vigore alla sua uscita); `pannello.py --taratura` rifiuta un piano che qui non c'è; il collaudo ferma il rilascio se il file è rotto, ha un "dal" senza fuso, fuori ordine, o se `taratura.json` ha letture di un piano sconosciuto (salvo quelle con "escluso") |
| `redazione/dem/AAAA-MM-GG-nome.md` (una mail straordinaria) | a mano (Claude, con l'ok di Paolo) | `dem.py` → `pannello/invii.json` (`dem.py salva`; il collaudo pretende che sia allineato) e Kit (`dem.yml`); usa `newsletter.py` (colori, cornice, chiamate a Kit) e `giorni.py` (giorni di uscita) |
| `/tmp/gtd_token.json` (token e, in `web`, ricerche e pagine non raggiunte) e la trascrizione della sessione a cui punta | `gancio_token.py` (`.claude/settings.json`) | `pannello.py --indici`; `controlli_fatti.py` (riscontra le ricerche dichiarate in `"conferma_cercata"` con quelle fatte davvero; senza gancio non conclude nulla) |
| `voce_indice.json`, `testo.json` (cartella di lavoro) | motore; `controlli_testo.py` | `controlli_temi.py`, `controlli_contenuti.py`, `edizioni_voce.py`, `messaggio.py` |

Tre cose da ricordare:
- **Quattro file della redazione sono pubblici**: `glossario.json`, `glossario_sito.json`, `meccanismi.json`, `scommessa/pagella.json` (elenco `LETTI` in `costruisci.py`). Tutto il resto di `redazione/` non arriva mai su gommberg.com.
- **Le pagine in `e/`, `dati/`, `ultima/`, `feed.xml` e `sitemap.xml` sono generate**: non si toccano a mano. Chi cambia `pagine.py` rigenera (`python3 redazione/pagine.py`) e committa le pagine nello stesso commit: il collaudo lo pretende.
- **`.claude/settings.json` non filtra i siti**: contiene il gancio e il permesso a WebSearch. Quali fonti valgono lo decide solo `fonti.json`; le pagine che non si aprono le annota il gancio e le mostra il pannello (`fallite`).
- **Fuori dal repository**: il testo delle attività programmate (app di Claude, copia in `ATTIVITA.md`: l'edizione, la misura della lettura, il capo sviluppo, il cui testo sta in `registro/CAPO.md`), la pagina e i dati del Registro dei lavori, i due modelli di email e il modulo di iscrizione (Kit), DNS, Worker e database D1 dei lettori (Cloudflare; i commenti si tolgono da lì finché non c'è G-51, `sito/LETTORI.md`), i segreti di GitHub (`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `KIT_API_KEY`), GoatCounter, Search Console. Un cambiamento che li riguarda non lo vede nessun collaudo: va scritto nel piano del rilascio e provato a mano.

## 4. La rete di non regressione

Un solo comando, `python3 redazione/collaudo.py` (meno di un minuto, senza rete e senza modelli), dopo ogni modifica:

1. sintassi di tutti i `.py` e `.sh`; 2. avvio (`prepara.sh` in tre giorni tipo); 3. pagina modello impaginata e controllata, e la regola dei fatti e il gancio su casi costruiti apposta;
4. **rete**: le edizioni campione di `redazione/rete/` rifatte dai loro sorgenti con il kit di oggi lungo la catena del mattino, e confrontate con l'atteso (`atteso/`): testo del PDF, esito dei controlli, voce di `edizioni.json`, email, numeri del pannello;
5. sito: file validi, link interni, **pagine generate identiche a quelle nel repository**, `costruisci.py` senza avvisi, il filtro di Impara su casi costruiti e un suo guasto che non ferma `pagine.py`; 6. lettori: il servizio vero contro un database finto (`sito/prova_lettori.mjs`, serve Node 22.5 o più), la sintassi del codice del browser, la configurazione e l'avviso sulle segnalazioni (`sito/segnalazioni.py` a secco); 7. pubblicazione a secco.

Ogni differenza ferma. Se è un guasto si corregge; se è voluta si rilancia con `--atteso`, che riscrive l'atteso e stampa che cosa è cambiato: quel cambiamento è nel commit e nel resoconto del rilascio, dove lo vede anche Paolo. `--campione AAAA-MM-GG` congela un'edizione nuova (accettata solo se, rifatta, è identica a quella pubblicata).

Come cresce: un guasto arrivato ai lettori diventa un campione o un controllo in più, nello stesso rilascio che lo corregge. I campioni coprono oggi un lunedì con il verdetto (16/11), un giorno qualsiasi (18/11), un venerdì passato dal desk (20/11) e la prima edizione con le regole di scrittura del 22/11 (23/11, con Tokyo chiusa).

Che cosa la rete **non** vede: ciò che Sonnet scriverà con regole nuove (serve un'edizione di prova, `PROVA.md`), l'aspetto grafico (colori, immagini: si guarda l'anteprima), i servizi esterni (Kit, Cloudflare), le pagine nel browser (le apre `collaudo_sito.py`, su GitHub a ogni push sul ramo di rilascio).

## 5. Il rilascio e il capo sviluppo

Il ramo principale è ciò che i lettori vedono: ogni push lo ripubblica. Per questo main riceve un merge alla volta, dal ramo `rilascio`, solo a collaudo verde (G-39). Dal 28/11 (G-65) questo paragrafo parla a due lettori:
- **il capo sviluppo** (sessione senza nessuno, attività "Gommberg: capo sviluppo", testo in `registro/CAPO.md`; parte al clic di Paolo nel Registro e ogni sera alle 19:27): costruisce, collauda, prepara, **non rilascia**. Scrive solo i rami `g<NN>` delle voci e il database del Registro; mai main, `rilascio`, `con-prova`, `prova` o `anteprima-*`.
- **la chat del rilascio** (aperta da Paolo): rilascia con `rilascia.sh`, e lei sola tocca main, i rami condivisi, i file di stato e le mail straordinarie.
I dati (voci, clic, piano, presa in carico) sono in `registro/CONTRATTO.md`. Le serate di G-57 restano solo come storico; `meta/giro` non serve più.

**I livelli** (`livello` sulla voce: `sola`, `via`, `visto`; assente = `visto`) sono l'obiettivo: `sola` andrà in linea da sola, `via` dopo il via sul piano, `visto` dopo l'Ok. In questa versione valgono solo come informazione: ogni voce si ferma a "pronta" e ogni rilascio passa da un Ok di Paolo e da una chat. Il gradino dopo vuole prima i cancelli negli script (lista in fondo a `CAPO.md`).

**La catena** (regola per la chat del rilascio): tutto `redazione/` tranne `STATO.md`, `PROGETTO.md`, `AZIONI.md` e `collaudi/`; più `.github/workflows/`, `.claude/settings.json`, `edizioni.json`, `dati/`, `pannello/`. Dentro ci sono ciò che l'attività del mattino legge o esegue (§1, §2), i cancelli (`collaudo.py`, `rilascia.sh`, `prova.sh`, `rete/`, workflow) e i file che comandano le attività (`ATTIVITA.md`, `registro/`). Una voce che tocca la catena va in linea solo con l'Ok sul commit esatto (le mail di `redazione/dem/` hanno la loro regola, in fondo a questo paragrafo); se cambia ciò che il mattino scrive (regole, lessico, kit, controlli, campioni) va con l'edizione di prova anche se il resoconto dice OGNI GIORNO.

**Il piano e il via.** Il venerdì (se manca, il sabato o la domenica) il capo sviluppo propone il piano della settimana dopo in `meta/piano`: `settimana` = il lunedì, `via` null, `voci`, `giorni` = {codice: giorno}; le voci in ordine di priorità e scadenza, ciascuna con `giorno`, `finestra`, `livello`, `cosa`, `lettore`; lo sviluppo che non cambia la scrittura da lunedì a venerdì, il motore di scrittura e i campioni nel weekend; gli appunti nuovi entrano qui, formulati, e si segnano `assorbito`. Paolo toglie (Togli) e dà un solo via (Via al piano): ogni voce si lavora nel suo giorno, subito quelle il cui giorno è già arrivato. Senza via non parte nulla.

**Un solo lavoratore.** Passi a-d del contratto, con 180 minuti di silenzio come soglia. Qualunque lavoro senza un clic preso (compiti del giro compresi, anche in una sessione nata da un clic) vuole prima il lucchetto `meta/capo.lavora` = {`quando`, `aggiornato`, `che`}, preso con `ifVersion` e tolto alla fine; un `lavora` più vecchio di 180 minuti lo toglie la prima sessione che lo trova, e prosegue. Il segnale si aggiorna prima e dopo ogni lavoratore e ogni attesa lunga; un lavoratore oltre 150 minuti è un difetto da scrivere in `meta/salute`. Finiti i compiti, ogni sessione rilegge la coda dei clic prima di uscire. Una voce `occupata` (una chat di disegno aperta da Paolo) non si prende.

**Il capo sviluppo, una voce fino a "pronta".**
1. Un lavoratore con il modello della scheda (`modello`, `sforzo`) e il contesto pulito costruisce sul ramo `g<NN>` nato da `origin/main`; il suo compito, come quello dell'agente del collaudo, comincia con i divieti scritti in `registro/CAPO.md` punto 3 (solo il ramo della voce, di `rilascia.sh` solo `collauda`, niente main, `redazione/dem/`, Kit o flussi di GitHub): commit "G-NN: ...", `python3 redazione/collaudo.py` dopo ogni modifica, push di `g<NN>`.
2. In locale, senza push: `git fetch origin main g<NN> && git checkout -B rilascio origin/main && git merge --no-ff --no-edit origin/g<NN> && bash redazione/rilascia.sh collauda`. Su questo albero (main più la voce) un agente che non ha visto il lavoro fa il collaudo indipendente: diff, resoconto, ciò che la voce promette; rosso: la voce torna al lavoratore una volta, poi Ferma. Il `rilascio` locale poi si butta (`git checkout g<NN>`); non si spinge mai.
3. Se cambia qualcosa che si vede: l'anteprima si fa in locale con Chrome dalla stessa versione del codice (immagine o PDF), si salva in `redazione/collaudi/AAAA-MM-GG/g<NN>/` sul ramo della voce, e il link è la pagina del file su GitHub al commit (`https://github.com/PaoloGom/gommberg-terminal-daily/blob/<commit>/...`).
4. Sulla voce: `stato` `pronta`, `visto_commit` (il commit esatto, anteprima compresa), `anteprima`, `domanda` in tre righe (cosa, cosa cambia per il lettore, cosa ti chiedo) che dice anche come andrà in linea secondo il resoconto: "la sera stessa" (OGNI GIORNO e niente scrittura toccata) oppure "con l'edizione di prova". Qui si ferma, sempre.
Clic `ok`: sulla voce `ok` = {`quando`, `clic`, `commit`: il `visto_commit` approvato} e `domanda` "Approvata: apri la chat del rilascio"; non rilascia. Clic `non-ancora`: legge la nota, riprende la voce sullo stesso ramo, ripropone con un `visto_commit` nuovo. Clic `ok` su una voce senza `visto_commit`: si scarta e la voce si riprepara. Clic `indietro`: non annulla nulla e non scrive su nessuna voce; chiude il clic con la nota "Apri la chat per annullare il rilascio <nome>", che la pagina mostra come richiesta. Clic `margine`: le voci della riserva in ordine fino a "pronta", mai oltre; con la percentuale P al più (P - 10) / 5 voci e mai più di quattro, senza percentuale una.

**Il giro e il ramo veloce.** Il giro delle 19:27 legge solo i `clic` aperti, `meta/capo`, `meta/piano` (con `giorni`), `meta/tocca` e `meta/salute`, e ricalcola le richieste di Paolo con tre ricerche filtrate (voci non fatte con `domanda`, con `chi` Paolo, con `input` decisione). Se `meta/salute` ha più di 20 ore la aggiorna con `gh run list` (se `gh` manca lo scrive nella riga e prosegue). Lavora solo se c'è un clic, una voce del piano avviato con giorno oggi o già passato e non ancora pronta, il piano della settimana dopo da proporre (venerdì-domenica), o il promemoria del margine (giovedì, se la riserva non è vuota). Onestamente: poiché la salute si aggiorna ogni 24 ore, quasi ogni giro chiama `gh`; il ramo veloce evita git, contratto, §5 e la lettura di tutte le voci, non ogni lettura.

**L'avviso della sera.** `meta/tocca` = {`conto`, `codici`, `aggiornato`, `detto`} il capo sviluppo lo ricalcola dalle voci ogni volta che le ha lette (regola `aspettaPaolo` del contratto, più "piano:<settimana>" finché il piano non ha il via e "ferma:<codice>" per ogni voce ferma): così ci entrano anche le domande scritte dalle chat e le "Azione tua". A ogni giro, anche nel ramo veloce, confronta `codici` e i rilasci di `meta/salute.rilasci` più recenti di `detto.quando` con `detto` = {`quando`, `codici`}: se c'è qualcosa di non ancora detto scrive a Paolo, poi aggiorna `detto`. Mai ogni sera le stesse cose.

**Ferma.** Se un comando, un permesso o uno strumento manca o fallisce (agenti, Chrome, `gh` dove serve), non si aggira: sulla voce `ferma` = la causa in una frase e una `domanda` per la chat; il lavoro resta su `g<NN>`; il clic si chiude con la nota; una riga in `meta/salute`.

**I rami.** `g<NN>`: uno per voce, del capo sviluppo. `rilascio`: della chat; uguale a main quando nessuno rilascia. `con-prova`: della chat; raccoglie, con merge `--no-ff`, il lavoro che aspetta l'edizione di prova. `prova`: lo scrive solo `prova.sh`.

**I comandi** (solo la chat del rilascio; ogni azione che non può procedere stampa "RILASCIO: FERMO - <causa>"):
```
bash redazione/rilascia.sh avvia [con-prova]   la sessione va sul ramo rilascio (o con-prova), allineato all'ultimo main, e lo spinge
bash redazione/rilascia.sh collauda            sul ramo dove si è: collaudo e resoconto (righe Finestra e Ok di Paolo), main non si tocca
bash redazione/rilascia.sh unisci <commit>     dopo la prova andata bene: porta in rilascio il lavoro di con-prova fino al commit provato
bash redazione/rilascia.sh pubblica [--ok-di-paolo] [--dopo-la-prova] [--guasto]   l'orario, i cancelli, un solo merge su main
bash redazione/rilascia.sh annulla             toglie da main l'ultimo merge "Rilascio" (revert)
```
I cancelli di `pubblica`: niente modifiche non salvate; il ramo contiene l'ultimo main; collaudo verde; **la prova** se cambiano le regole di scrittura o un campione (`--dopo-la-prova`, solo con `prova.esito` `ok`); **l'ok di Paolo** se cambia ciò che il lettore vede (`--ok-di-paolo`, solo con `ok.commit` sulla voce); collaudo di GitHub verde sullo stesso commit (`collaudo.yml`; mai `--senza-github` senza Paolo). Prima dei cancelli l'orario: dal lunedì al venerdì tra le 8:30 e le 10:30 main non si tocca (`--guasto` solo per un guasto che blocca l'uscita). Le tre finestre le dice la riga "Finestra" del resoconto: OGNI GIORNO (in linea la sera stessa), CON PROVA (dopo l'edizione di prova), CON PAOLO (ciò che il lettore vede; più soldi, terzi e irreversibile, che lo script non vede).

**La chat del rilascio, una voce** (una alla volta: unisci, collauda, pubblica, verifica dal vivo, poi la successiva):
1. `avvia`; POI `git rev-list --no-merges origin/main..origin/rilascio` deve essere vuoto: se no, `rilascio` porta lavoro non in linea e si ripulisce prima (senza push forzati).
2. `git merge --no-ff --no-edit <ok.commit>`: esattamente il commit approvato, non la punta di `g<NN>`. `collauda` di nuovo; se main è cambiato dopo il collaudo del capo sviluppo, uno sguardo indipendente all'albero nuovo.
3. `pubblica --ok-di-paolo` (l'Ok è sul commit). Se si ferma dopo aver spinto `rilascio`, nessun'altra voce finché `rilascio` non torna pulito.
4. Verifica dal vivo: `sito.yml` verde su main (`gh run list --workflow sito.yml -L 1`) e la cosa promessa vista su gommberg.com.
5. Sulla voce `stato` `fatta`, `chiusa`, `esito`; via `domanda`, `anteprima`, `visto_commit`, `ok`; in cima a `meta/salute.rilasci` {`nome`: la prima riga del merge, `quando`, `esito` `ok`, `testo`, `lettore`, `verificato`}; `STATO.md` e una riga di `PROGETTO.md` su main.

**L'edizione di prova** (la chat; procedura A di `PROVA.md`). Le voci con prova entrano in `con-prova` con merge `--no-ff` del loro `ok.commit` (`avvia con-prova`, merge, push). Si prova nel fine settimana, con la data del lunedì che viene: `prova.sh avvio <lunedì>` porta dentro l'archivio fino al giorno prima, e il lunedì non ha ancora un'edizione. Il commit provato è la punta di `origin/con-prova` subito prima di lanciare l'attività del mattino con il testo della procedura A. Si legge il PDF in `redazione/collaudi/prova-<data>/` del ramo `prova`, e su ogni voce del commit provato si scrive `prova` = {`esito` `ok` o `ko`, `nota`, `commit`}. Con `ok`: `avvia`, controllo del punto 1, `unisci <prova.commit>`, `pubblica --dopo-la-prova` (con `--ok-di-paolo`), entro domenica sera. "Non ancora" PRIMA della prova: la voce esce da `con-prova` con `git revert -m 1` del suo merge; per farla rientrare serve il revert di quel revert. "Non ancora" DOPO la prova: il commit provato non si cambia, e nulla di quel commit va in linea finché una chat non rifà la prova senza quella voce. `ko`: Ferma. Ciò che entra in `con-prova` dopo il commit provato aspetta la prova successiva.

**Torna indietro** (la chat). Mai tra le 8:30 e le 10:30 dei giorni di edizione (`annulla` non lo controlla). Prima si confronta l'oggetto dell'ultimo merge "Rilascio" (`git log origin/main --merges --grep='^Rilascio ' -1 --format=%s`) con il rilascio nominato, che deve essere il primo con esito `ok` in `meta/salute.rilasci`; se non coincidono, non si annulla. `annulla`, verifica dal vivo, `esito` `annullato` su quel rilascio, sulla voce `stato` non più `fatta` e `ferma` "tolta dalla linea: <perché>". Per farla rientrare: `avvia`, `git revert <commit dell'annullamento>` su `rilascio` (il revert del revert, come stampa `annulla`), correzione, `pubblica`.

**Il ritmo.** In settimana va in linea la sera stessa, dopo l'Ok e la chat, ciò che non cambia la scrittura; ciò che la cambia, o cambia un campione, si costruisce nel weekend e va in linea dopo l'edizione di prova, entro domenica sera.

**Chi risponde.** Il capo sviluppo tiene `meta/salute` (edizione, sito, newsletter, controlli partiti davvero, ultimi rilasci) e, quando qualcosa non va, lo scrive lì con causa e rimedio e lo dice a Paolo senza aspettare che lo scopra. La chat del rilascio risponde di ciò che manda in linea, fino alla verifica dal vivo.

Solo la chat aggiorna i file di stato (`STATO.md`, `PROGETTO.md`, `AZIONI.md`) sul ramo principale (non ripubblicano il sito) e tocca le mail straordinarie: i file di `redazione/dem/` e `pannello/invii.json` (sempre insieme, dopo `dem.py salva`) vanno su main direttamente, e ogni loro push può far partire una mail ai lettori; `dem.py`, `dem.yml` e la vista passano dal rilascio.

Dopo il merge: `sito.yml` pubblica e verifica dal vivo; la mattina dopo `mattino.yml` controlla l'edizione appena è pubblicata. La procedura B di `PROVA.md` (edizione di test pubblicata davvero) si fa solo su richiesta di Paolo.

Un guasto che blocca l'edizione passa davanti a tutto e segue la stessa strada in piccolo, in una chat con Paolo: `avvia`, correzione, `pubblica` (con `--guasto` se è la fascia dell'uscita).
