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
  │  controlli_tutti.sh (tutti i controlli)       →  testo.json (sigle), ripetizioni.json, anteprima.png
  │  revisione (agente) → desk (desk.py)          →  revisione.json, desk_ok.json
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
| Newsletter | `newsletter.py` (compone anche testata e fascia dei mercati), `newsletter_cornice.html` e `newsletter_modello.html` (copiati a mano in Kit: "Gommberg cornice" per le edizioni, "Gommberg" predefinito; se la cornice manca l'invio fallisce e il controllo del mattino lo segnala, nessun ripiego su un altro modello; se Kit non risponde all'elenco dei modelli, 4 tentativi a 15 secondi e poi errore "Kit non risponde"; la creazione dell'invio non si ritenta mai) | L'email del mattino dalla scheda `e/NNN.json` |
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
| `pannello/piani.json` (i piani di Claude: nome, inizio, giorno e ora dell'azzeramento) | a mano, una riga per cambio di piano | `pannello/index.html` (rapporta ogni edizione al piano in vigore alla sua uscita); `pannello.py --taratura` rifiuta un piano che qui non c'è; il collaudo ferma il rilascio se il file è rotto, ha un "dal" senza fuso, fuori ordine, o se `taratura.json` ha letture di un piano sconosciuto (salvo quelle con "escluso") |
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

Come cresce: un guasto arrivato ai lettori diventa un campione o un controllo in più, nello stesso rilascio che lo corregge. I campioni coprono oggi un lunedì con il verdetto (16/11), un giorno qualsiasi (18/11), un venerdì passato dal desk (20/11) e la prima edizione con le regole di scrittura del 22/11 (23/11, con Tokyo chiusa).

Che cosa la rete **non** vede: ciò che Sonnet scriverà con regole nuove (serve un'edizione di prova, `PROVA.md`), l'aspetto grafico (colori, immagini: si guarda l'anteprima), i servizi esterni (Kit, Cloudflare), le pagine nel browser (le apre `collaudo_sito.py`, su GitHub a ogni push sul ramo di rilascio).

## 5. Il rilascio e il capo sviluppo

Il ramo principale è ciò che i lettori vedono: ogni push lo ripubblica. Per questo main riceve un merge alla volta, dal ramo `rilascio`, solo a collaudo verde (G-39). Dal 28/11 (G-65) il lavoro lo porta il **capo sviluppo**: un'attività programmata sola, "Gommberg: capo sviluppo" (testo in `registro/CAPO.md`), che parte al clic di Paolo nel Registro dei lavori e ogni sera alle 19:27 (il giro). I dati che legge e scrive sono in `registro/CONTRATTO.md`; qui sta il come. Questa prima versione automatizza solo ciò che `rilascia.sh`, `prova.sh` e `PROVA.md` reggono oggi. Le serate di G-57 restano solo come storico: non si scrivono più, e `meta/giro` non serve più.

**Nulla va su main senza un clic di Paolo che lo copre.** Il Via al piano copre le voci `sola` e `via` di quel piano; il clic Ok copre una voce `visto` (livello assente = `visto`). Il clic Usa il margine non copre la linea. In questa versione `sola` e `via` si comportano uguale: la differenza (`sola` partirà senza via) vale quando lo script avrà il cancello del livello.

**Il più severo vince.** Dopo il via una voce va in linea da sola SOLO se valgono tutte: il resoconto di `rilascia.sh collauda` dice "Finestra: OGNI GIORNO" e "Ok di Paolo: non serve"; nessun file toccato sta nella catena qui sotto; il collaudo indipendente è verde. Se un file toccato sta nella catena, la voce si tratta come `visto` e, se cambia la scrittura o un campione, come lavoro con prova, qualunque cosa dicano il campo `livello` o lo script. Scrittura, sito, newsletter, soldi, terzi e irreversibile sono sempre `visto`.

**La catena del mattino e dei cancelli** (ricavata da §1, §2, `prepara.sh`, `controlli_tutti.sh`, `pubblica.sh`, `scommessa_giorno.sh` e dai workflow):
- regole e lessico: `redazione/ISTRUZIONI.md`, `redazione/APP_*.md`, `redazione/NOTA_DEL_GIORNO.md`, `redazione/edizione_modello_*.py`, `redazione/glossario*.json`, `redazione/meccanismi.json`, `redazione/fonti.json`;
- il kit: tutti i `redazione/*.py` e `redazione/*.sh` (motore, controlli, desk, memoria, indice, pubblicazione, messaggio, pagine, pannello, newsletter, `collaudo.py`, `rilascia.sh`, `prova.sh`), `redazione/scommessa/`, `redazione/newsletter_*.html`, `.claude/settings.json`;
- i dati che il mattino legge o scrive: `redazione/chiusure.csv`, `redazione/fatti/`, `redazione/sorgenti/`, `redazione/pronostici/`, `edizioni.json`, `dati/`, `pannello/`;
- il sito e il servizio dei lettori: `redazione/sito/`;
- i cancelli: `.github/workflows/`, `redazione/rete/`.

**Il piano e il via.** Il venerdì (o, se manca, il sabato o la domenica) il giro propone il piano della settimana dopo in `meta/piano` (`settimana` = il lunedì, `via` null): le voci aperte in ordine di priorità e scadenza, ciascuna con `giorno`, `finestra`, `livello`, `cosa` e `lettore`; lo sviluppo che non cambia la scrittura da lunedì a venerdì, il motore di scrittura e i campioni nel weekend; gli appunti nuovi entrano qui, formulati, e si segnano `assorbito`. Paolo toglie voci (Togli) e dà un solo via (Via al piano). Con il via ogni voce si lavora nel suo `giorno`: subito quelle il cui giorno è già arrivato, le altre al giro di quel giorno. Senza via non parte nulla del piano.

**Un solo lavoratore.** Passi a-d del contratto, con la soglia di silenzio a 180 minuti. Chi lavora senza un clic (il giro che propone il piano o lavora le voci del giorno) prende prima `meta/capo.lavora` = {`quando`, `aggiornato`, `che`} con `ifVersion` e lo toglie alla fine; il passo a esce anche davanti a un `meta/capo.lavora` fresco. Il segnale (`preso.aggiornato` o `meta/capo.lavora.aggiornato`) si aggiorna prima e dopo ogni lavoratore e ogni attesa lunga; un lavoratore che dura più di 150 minuti è un difetto da segnalare in `meta/salute`, non da aggirare. Una voce alla volta, mai in parallelo. Una voce `occupata` (una chat di disegno aperta da Paolo) non si prende.

**Chi costruisce non si collauda.** Ogni voce va a un lavoratore con il modello della scheda (`modello`, `sforzo`) e il contesto pulito: la scheda, questo paragrafo, i file che servono. Prima della linea la controlla un agente che non ha visto il lavoro (Opus) sull'albero che va in linea, cioè main più la voce: legge il diff, guarda il resoconto di `collauda`, prova ciò che la voce promette, dice verde o rosso e perché. Senza lo strumento per chiamare agenti, o senza `gh`, la sessione non rilascia nulla: la voce diventa una richiesta a Paolo di aprire la chat. Mai `--senza-github` da una sessione senza nessuno.

**I rami.**
- `g<NN>` (es. `g45`): uno per voce, nato dall'ultimo main; ci stanno i commit ("G-NN: ...") e `python3 redazione/collaudo.py` dopo ogni modifica. Una voce resta qui finché non va in linea.
- `rilascio`: uguale a main quando nessuno sta rilasciando. Prima di ogni rilascio il capo sviluppo controlla `git diff --quiet origin/main origin/rilascio`: se non è uguale non rilascia nulla ed è Ferma. Rimetterlo a posto (senza push forzati) tocca a una chat con Paolo.
- `con-prova`: raccoglie il lavoro che cambia la scrittura o un campione, fino all'edizione di prova.
- `prova`: lo scrive solo `prova.sh`. Nessuna sessione senza nessuno spinge su `prova` o su `anteprima-*` (usano il servizio vero dei lettori).

**I comandi** (`rilascia.sh`; ogni azione che non può procedere stampa "RILASCIO: FERMO - <causa>"):
```
bash redazione/rilascia.sh avvia [con-prova]   la sessione va sul ramo rilascio (o con-prova), allineato all'ultimo main
bash redazione/rilascia.sh collauda            sul ramo dove si è: collaudo e resoconto (righe Finestra e Ok di Paolo), main non si tocca
bash redazione/rilascia.sh unisci <commit>     dopo la prova andata bene: porta in rilascio il lavoro di con-prova fino al commit provato
bash redazione/rilascia.sh pubblica [--ok-di-paolo] [--dopo-la-prova] [--guasto]   l'orario, i cancelli, un solo merge su main
bash redazione/rilascia.sh annulla             toglie da main l'ultimo rilascio
```
I cancelli di `pubblica`: niente modifiche non salvate; il ramo contiene l'ultimo main; collaudo verde; **la prova** se cambiano le regole di scrittura o un campione (`--dopo-la-prova`, solo con `prova.esito` `ok`); **l'ok di Paolo** se cambia ciò che il lettore vede (`--ok-di-paolo`, solo dopo il clic Ok); collaudo di GitHub verde sullo stesso commit (`collaudo.yml`). Prima dei cancelli l'orario: dal lunedì al venerdì tra le 8:30 e le 10:30 main non si tocca (`--guasto` solo per un guasto che blocca l'uscita). Se l'orario ferma un rilascio, il clic torna `da-eseguire` con `non_prima` = le 10:30 di oggi e la sessione esce; nessuna sessione riprende un clic prima del suo `non_prima`. Se `pubblica` si ferma dopo aver spinto `rilascio`, la voce è Ferma e non si lavora nessun'altra voce finché `rilascio` non torna uguale a main.

**Una voce, passo per passo** (finito un rilascio, la successiva):
1. Il lavoratore costruisce su `g<NN>` (da `origin/main`), commit e push.
2. Controllo di `rilascio` (sopra); `avvia`; `git merge --no-ff --no-edit origin/g<NN>`; `collauda`, senza push. Su questo albero il collaudo indipendente; rosso: la voce torna al lavoratore una volta, poi Ferma.
3. Se il resoconto dice CON PROVA, o un file sta nella catena e tocca la scrittura o i campioni: merge locale scartato (`git reset --hard origin/rilascio`, mai spinto) e lavoro con prova (sotto).
4. Se la voce è da trattare come `visto`: merge locale scartato; l'anteprima si fa in locale con Chrome dalla stessa versione del codice (immagine o PDF), si salva in `redazione/collaudi/AAAA-MM-GG/g<NN>/` sul ramo della voce, e il link è la pagina del file su GitHub al commit (`https://github.com/PaoloGom/gommberg-terminal-daily/blob/<commit>/...`). Sulla voce: `domanda` (tre righe: cosa, cosa cambia per il lettore, cosa ti chiedo), `anteprima`, `visto_commit` (il commit esatto mostrato, anteprima compresa), `stato` `pronta`. Per ora finisce qui.
5. Altrimenti, o al clic Ok: `pubblica` (con `--ok-di-paolo` solo al clic Ok). Al clic Ok si unisce ESATTAMENTE `visto_commit`: se `origin/g<NN>` è andato oltre, non va in linea e si scrive una domanda nuova; se main è cambiato dopo il collaudo, l'agente ricontrolla l'albero nuovo prima di `pubblica`.
6. Verifica dal vivo: `sito.yml` verde su main (`gh run list --workflow sito.yml -L 1`) e, se la voce lo promette, la cosa vista su gommberg.com.
7. Scritture: sulla voce `stato` `fatta`, `chiusa`, `esito` (una riga), via `domanda`, `anteprima`, `visto_commit`; in cima a `meta/salute.rilasci` {`nome`: la prima riga del merge ("Rilascio AAAA-MM-GG: ..."), `quando`, `esito` `ok`, `testo`, `lettore`, `verificato`}; `STATO.md` e una riga di `PROGETTO.md` su main.
Ogni voce è un rilascio a sé: Torna indietro toglie solo quella.

**"Non ancora".** La voce non va in linea e resta sul suo ramo `g<NN>`: non era stata unita, non c'è nulla da togliere. Il capo sviluppo legge `testo`, riprende la voce e riscrive `domanda` e `visto_commit` quando la ripropone.

**Il lavoro con prova** (cambia la scrittura o un campione). Il capo sviluppo costruisce su `g<NN>`, lo unisce a `con-prova` (`avvia con-prova`, merge, push), fa collaudare l'albero, poi si ferma: sulla voce `prova` = {`giorno`, `esito` `da-fare`} e una `domanda` che chiede a Paolo di aprire la chat per l'edizione di prova. La sessione senza nessuno non lancia la prova. Che cosa dicono `PROVA.md` e `rilascia.sh`, oggi: la prova la lancia a mano una chat, con l'attività del mattino e il testo della procedura A, dal ramo `con-prova` dopo `avvia con-prova`; senza data vale per oggi (in un giorno di edizione, dopo l'edizione vera), con una data vale per quel giorno di borsa (nel fine settimana, il lunedì che viene); `prova.sh avvio` porta dentro l'archivio fino al giorno prima e scrive sul ramo `prova`, `prova.sh chiudi` salva PDF e schede in `redazione/collaudi/prova-<data>/` di quel ramo. Chi legge la prova scrive su ogni voce di quel lavoro `prova.esito` `ok` o `ko`, la `nota` e `prova.commit` (il commit di `con-prova` provato). Poi ogni voce `visto` del commit provato riceve `domanda`, `anteprima` (il PDF di prova su GitHub) e `visto_commit` = il commit provato; va in linea quando TUTTE le voci di quel commit hanno avuto l'Ok: un Ok che trova altre domande aperte chiude il clic con "in linea quando dai l'ok anche a G-xx"; l'ultimo fa `avvia`, `unisci <prova.commit>`, `pubblica --dopo-la-prova --ok-di-paolo`. "Non ancora" PRIMA della prova: la voce esce da `con-prova` (`git revert -m 1` del suo merge) e la prova si fa senza di lei. "Non ancora" DOPO la prova: il commit provato non si cambia, e nulla di quel commit va in linea finché una chat non rifà la prova senza quella voce. `ko`: Ferma. Ciò che arriva su `con-prova` dopo il commit provato aspetta la prova successiva.

**Il ritmo.** In settimana va in linea la sera stessa (dopo il via) ciò che non cambia la scrittura; ciò che la cambia, o cambia un campione, si lavora nel weekend e va in linea dopo l'edizione di prova lanciata da una chat con Paolo. Le edizioni vengono prima: mai rilasci tra le 8:30 e le 10:30 dei giorni di edizione. Clic Usa il margine: con la percentuale dichiarata P, la riserva in ordine per al più (P - 10) / 5 voci, mai più di quattro (10% o meno: nessuna); senza percentuale una voce sola. Le voci del margine si costruiscono e collaudano, poi aspettano un Ok come le `visto`.

**Il giro della sera** (19:27, ogni giorno): i passi a-d come per un clic; poi le voci del piano che toccano oggi (con il via); se manca il piano della settimana dopo ed è venerdì, sabato o domenica, lo propone; il giovedì il promemoria del margine, se la riserva non è vuota; se `meta/salute` ha più di 20 ore, la aggiorna. Chi esce al passo a o c non fa i compiti del giro: li fa chi sta lavorando, alla fine della sua coda. Il ramo veloce legge solo `clic` (`da-eseguire` e `in-lavoro`), `meta/capo`, `meta/piano`, `meta/salute` e `meta/tocca`; contratto e voci si leggono solo quando c'è lavoro.

**Che cosa si scrive a Paolo.** È il superiore, non il tecnico: ogni cosa in tre righe (cosa, cosa cambia per il lettore, cosa ti chiedo), senza nomi di rami, file o commit se non servono a decidere. `meta/tocca` = {`conto`, `codici`, `aggiornato`, `detto`} conta le richieste aperte e il capo sviluppo lo aggiorna ogni volta che scrive o toglie una `domanda`; `detto` = {`quando`, `codici`} dice che cosa il messaggio della sera ha già detto. Il giro scrive a Paolo solo se dall'ultimo messaggio c'è stato un rilascio o una Ferma, c'è un piano nuovo da approvare, c'è una richiesta nuova rispetto a `detto`, o è giovedì con il promemoria: mai ogni sera le stesse cose.

**Ferma.** Se un comando, un permesso, un cancello o un collaudo ferma il lavoro, non si aggira: sulla voce `ferma` = la causa in una frase e una `domanda` che chiede la chat; il lavoro resta sul suo ramo; il clic si chiude con la nota; una riga in `meta/salute` con causa e rimedio.

**Torna indietro.** Al clic `indietro` il capo sviluppo: controlla l'orario da sé (mai tra le 8:30 e le 10:30 dei giorni di edizione: altrimenti `non_prima`, come sopra); esegue solo se il rilascio nominato è il primo di `meta/salute.rilasci` con `esito` `ok` (se il primo è `annullato`, un secondo annullamento di fila non è previsto: Ferma e chat; se il nominato non è il primo, scarta); `annulla`; verifica dal vivo; scrive su quel rilascio `esito` `annullato`, così un secondo clic si scarta; `avvia` (riallinea `rilascio` a main con un merge) e controlla che `rilascio` sia uguale a main, altrimenti Ferma; sulla voce `stato` non più `fatta` e `ferma` "tolta dalla linea: <perché>"; se era `sola` o `via`, quel tipo di voce sale di un livello e lo si scrive nelle Lezioni di `AZIONI.md`.

**Chi risponde.** Il capo sviluppo risponde del risultato dall'inizio alla fine, non del solo merge: tiene `meta/salute` (edizione, sito, newsletter, controlli partiti davvero, ultimi rilasci) e, quando qualcosa non va, lo scrive lì con causa e rimedio e lo dice a Paolo senza aspettare che lo scopra.

Durante il lavoro i file di stato (`STATO.md`, `PROGETTO.md`, `AZIONI.md`) si aggiornano sul ramo principale (non ripubblicano il sito); tutto il resto passa dai rami. Lo stesso vale, in qualunque giorno, per le mail straordinarie: i file di `redazione/dem/` e `pannello/invii.json` (sempre insieme, dopo `dem.py salva`) vanno su main direttamente, perché non toccano l'edizione né le pagine dei lettori; `dem.py`, `dem.yml` e la vista passano dal rilascio.

Dopo il merge: `sito.yml` pubblica e verifica dal vivo; la mattina dopo `mattino.yml` controlla l'edizione appena è pubblicata. Le prove con l'attività vera si fanno prima del merge dal ramo `con-prova` (procedura A di `PROVA.md`) e, per provare anche la pubblicazione, dopo il merge con una data simulata (procedura B, solo su richiesta di Paolo).

Un guasto che blocca l'edizione passa davanti a tutto e segue la stessa strada in piccolo, in una chat con Paolo: `avvia`, correzione, `pubblica` (con `--guasto` se è la fascia dell'uscita).
