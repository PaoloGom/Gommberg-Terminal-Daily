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

Il ramo principale è ciò che i lettori vedono: ogni push lo ripubblica. Per questo main riceve un merge alla volta, dal ramo `rilascio`, solo a collaudo verde (G-39). Dal 28/11 (G-65) il lavoro lo porta il **capo sviluppo**: un'attività programmata sola, "Gommberg: capo sviluppo" (testo in `registro/CAPO.md`), che parte al clic di Paolo nel Registro dei lavori e ogni sera alle 19:27 (il giro). I dati che legge e scrive (voci, clic, piano, presa in carico) sono in `registro/CONTRATTO.md`; qui sta il come. Le serate di G-57 restano solo come storico: non si scrivono più, e `meta/giro` non serve più.

**L'unità è la voce.** Paolo vede voci, non rami. Ogni voce ha un `livello` (assente = `visto`), deciso dal capo sviluppo:
- `sola`: parte e va in linea da sola, Paolo legge l'esito. Solo se il lettore non vede nulla (resoconto: finestra OGNI GIORNO, ok di Paolo "non serve"), non tocca la catena dell'edizione del mattino (i file che l'attività del mattino esegue o legge, §2: regole, motore, controlli, pubblicazione, indice) e si annulla con `annulla`. Se una delle tre non vale, quella volta la voce si tratta come `visto`. Se un rilascio `sola` va annullato, quel tipo di voce sale di un livello e lo si scrive nelle Lezioni di `AZIONI.md`.
- `via`: parte al via di Paolo sul piano, poi fa da sé fino in linea. Anche qui il lettore non vede nulla.
- `visto`: prima di andare in linea il capo sviluppo si ferma, scrive sulla voce `domanda` e `anteprima` e aspetta il clic Ok. Scrittura, sito, newsletter, soldi, terzi e irreversibile sono sempre `visto`, e solo dopo quel clic si aggiunge `--ok-di-paolo`.
L'`anteprima` è un link `https://` a qualcosa che esiste già fuori da claude.ai (una sessione senza nessuno non può pubblicare artefatti): l'anteprima del sito di un ramo `anteprima-g<NN>`, il PDF di prova o un file del repository visto da GitHub.

**Il piano e il via.** Il venerdì il giro propone il piano della settimana dopo in `meta/piano` (`settimana` = il lunedì, `via` null): le voci aperte in ordine di priorità e scadenza, ciascuna con `giorno`, `finestra`, `livello`, `cosa` e `lettore` scritti; lo sviluppo che non cambia la scrittura da lunedì a venerdì, il motore di scrittura e i campioni nel weekend; gli appunti nuovi entrano qui, formulati, e si segnano `assorbito`. Paolo toglie voci (Togli) e dà un solo via (Via al piano). Con il via ogni voce si lavora nel suo `giorno`: subito quelle il cui giorno è già arrivato, le altre al giro di quel giorno. Le voci `sola` del piano non aspettano il via. Fuori dal piano lavora solo ciò che Paolo lancia con un clic (Ok, Non ancora, Usa il margine, Torna indietro).

**Presa in carico.** Un solo capo sviluppo al lavoro, con i passi a-d del contratto: presa del clic con `ifVersion`, segnale `preso.aggiornato` almeno ogni 30 minuti, chi trova un altro al lavoro con segnale fresco esce. Una voce alla volta, mai in parallelo (quelle sullo stesso file si fanno insieme, sull'ultima versione). Una voce `occupata` (una chat di disegno aperta da Paolo) non si prende.

**Chi costruisce non si collauda.** Ogni voce va a un lavoratore con il modello della scheda (`modello`, `sforzo`) e il contesto pulito: la scheda, questo paragrafo, i file che servono. Prima di andare in linea la controlla un agente che non ha visto il lavoro (Opus): legge il diff, lancia il collaudo, prova ciò che la voce promette, dice verde o rosso e perché. Se la sessione non ha lo strumento per chiamare agenti, il capo sviluppo costruisce da sé ma non manda nulla in linea da solo: scrive sulla voce la `domanda` "Apri la chat sulla voce per il collaudo" e la voce va in Tocca a te.

**I rami.**
- `g<NN>` (es. `g45`): uno per voce, nato dall'ultimo main; il lavoratore ci fa i commit ("G-NN: ...") e `python3 redazione/collaudo.py` dopo ogni modifica.
- `rilascio`: porta solo ciò che va in linea adesso. Fuori da un rilascio in corso è uguale a main: se `avvia` lo trova avanti con lavoro non in linea, ci si ferma.
- `con-prova`: raccoglie le voci che cambiano le regole di scrittura o un campione, fino all'edizione di prova del sabato.
- `anteprima-g<NN>`: copia del ramo voce quando la voce cambia il sito; `sito.yml` la pubblica come anteprima (noindex, indirizzo nel resoconto della corsa).
- `prova`: lo scrive solo `prova.sh`.

**I comandi** (`rilascia.sh`; ogni azione che non può procedere stampa "RILASCIO: FERMO - <causa>"):
```
bash redazione/rilascia.sh avvia [con-prova]   la sessione va sul ramo rilascio (o con-prova), allineato all'ultimo main
bash redazione/rilascia.sh collauda            sul ramo dove si è: collaudo e resoconto (righe Finestra e Ok di Paolo), main non si tocca
bash redazione/rilascia.sh unisci <commit>     dopo la prova andata bene: porta in rilascio il lavoro di con-prova fino al commit provato
bash redazione/rilascia.sh pubblica [--ok-di-paolo] [--dopo-la-prova] [--guasto]   l'orario, i cancelli, un solo merge su main
bash redazione/rilascia.sh annulla             toglie da main l'ultimo rilascio
```
I cancelli di `pubblica`: niente modifiche non salvate; il ramo contiene l'ultimo main; collaudo verde; **la prova** se cambiano le regole di scrittura o un campione (`--dopo-la-prova`, solo con `prova.esito` `ok` sulle voci); **l'ok di Paolo** se cambia ciò che il lettore vede (file pubblici del sito, testo del PDF o email dei campioni, modello della newsletter: `--ok-di-paolo`, solo dopo il clic Ok); collaudo di GitHub verde sullo stesso commit (`collaudo.yml`: stesso collaudo su un'altra macchina, più il sito in un browser). Prima dei cancelli l'orario: dal lunedì al venerdì tra le 8:30 e le 10:30 main non si tocca (`--guasto` solo per un guasto che blocca l'uscita). Se l'orario ferma un rilascio non è una fermata: il clic torna `da-eseguire` e lo riprende il giro.

**Le tre finestre**, dette dalla riga "Finestra" del resoconto, mai dalla chat:
- **Ogni giorno**: campioni identici, scrittura intatta. In linea la sera stessa, anche in settimana.
- **Con prova**: cambiano le regole di scrittura o un campione esce diverso. Si lavora nel weekend su `con-prova`; in linea solo dopo la prova del sabato, entro domenica sera.
- **Con Paolo**: ciò che il lettore vede; più soldi, terzi e irreversibile, che lo script non vede e il capo sviluppo dichiara. Sempre `visto`.

**Una voce, passo per passo.**
1. Il lavoratore costruisce sul ramo `g<NN>` (da `origin/main`), con commit e push.
2. Collaudo indipendente. Rosso: la voce torna al lavoratore una volta; ancora rosso: Ferma.
3. `avvia`; `git merge --no-ff --no-edit origin/g<NN>`; `collauda` (senza push). Dal resoconto:
   - CON PROVA: si scarta il merge locale (`git reset --hard origin/rilascio`), `avvia con-prova`, merge di `g<NN>`, push; sulla voce `prova` = {`giorno`: il sabato, `esito`: `da-fare`}. Per ora finisce qui.
   - serve l'ok e non c'è un clic Ok: merge locale scartato; `anteprima`, `domanda` e `stato` `pronta` sulla voce. Per ora finisce qui.
   - altrimenti, o al clic Ok: `pubblica` (con `--ok-di-paolo` solo al clic Ok).
4. Verifica dal vivo: `sito.yml` verde su main (`gh run list --workflow sito.yml -L 1`) e, se la voce lo promette, la cosa vista su gommberg.com.
5. Scritture: sulla voce `stato` `fatta`, `chiusa`, `esito` (una riga), via `domanda` e `anteprima`; in cima a `meta/salute.rilasci` {`nome`: la prima riga del merge ("Rilascio AAAA-MM-GG: ..."), `quando`, `esito` `ok`, `testo`, `lettore`, `verificato`}; `STATO.md` e una riga di `PROGETTO.md` su main.
Ogni voce è un rilascio a sé: Torna indietro toglie solo quella.

**La prova del sabato.** Al giro del sabato, se `con-prova` è avanti a main e ha voci con `prova.esito` `da-fare`: `avvia con-prova` (porta dentro l'ultimo main), poi si lancia l'attività del mattino ("Gommberg Terminal Daily") con il testo della procedura A di `PROVA.md`, ramo `con-prova`, data l'ultima edizione uscita (di norma il venerdì): l'edizione si rifà e si confronta con quella vera. Il commit provato è `git merge-base origin/prova origin/con-prova`. Il giro della domenica legge la prova (commit "Prova ... non pubblicata" sul ramo `prova`, PDF in `redazione/collaudi/prova-<data>/` di quel ramo), la fa giudicare da un agente che non ha visto il lavoro e scrive su ogni voce di `con-prova` `prova.esito` `ok` o `ko` con la `nota`. Se `ok`: `domanda` e `anteprima` (il PDF di prova su GitHub) sulle voci `visto`; quando tra le voci di `con-prova` non resta nessuna domanda aperta, l'ultimo Ok manda in linea tutto: `avvia`, `unisci <commit provato>`, `pubblica --dopo-la-prova` (con `--ok-di-paolo`). Non ancora su una voce di `con-prova`: la voce esce dal ramo (`git revert` dei suoi commit) e il resto aspetta la prova del sabato dopo. `ko`, o nessun esito entro il giro della domenica: Ferma. Ciò che arriva su `con-prova` dopo il commit provato aspetta il sabato dopo. Se la sessione non può lanciare l'attività del mattino, la voce va in Tocca a te con la `domanda` "Serve l'edizione di prova: apri la chat sulla voce".

**Il ritmo.** In settimana va in linea la sera stessa ciò che non cambia la scrittura; ciò che la cambia, o cambia un campione, si lavora nel weekend, si prova il sabato e va in linea entro domenica sera. Le edizioni vengono prima: se i token non bastano il capo sviluppo si ferma e lascia in coda. Con il clic `margine` lavora la riserva in ordine e si ferma prima della percentuale indicata (senza percentuale: una voce sola).

**Il giro della sera** (19:27, ogni giorno): i passi a-d come per un clic, quindi riprende anche i clic fermi; le voci del piano che toccano oggi; il venerdì il piano; il sabato la prova, la domenica il suo esito; il giovedì il promemoria del margine; `meta/salute`; poi l'avviso a Paolo, solo se serve (`registro/CAPO.md`).

**Ferma.** Se un comando, un permesso, un cancello o un collaudo ferma il lavoro, non si aggira: sulla voce `ferma` = la causa in una frase; il lavoro resta salvato sul suo ramo; il clic si chiude con la nota; una riga in `meta/salute` con causa e rimedio; il messaggio della sera lo dice.

**Torna indietro.** Al clic `indietro` (o subito, se la verifica dal vivo va male): `annulla` toglie da main l'ultimo rilascio; verifica dal vivo; in `meta/salute.rilasci` quel rilascio passa a `esito` `ko` con "annullato il ..."; sulla voce `stato` non più `fatta` e `ferma` "tolta dalla linea: <perché>"; se era `sola`, sale di livello (Lezioni). Per riproporla vale quanto stampa `annulla`.

**Che cosa si scrive a Paolo.** È il superiore, non il tecnico: ogni cosa in tre righe (cosa, cosa cambia per il lettore, cosa ti chiedo), senza nomi di rami, file o commit se non servono a decidere. Lo stesso testo va nel Registro (`domanda`, `esito`, `nota`) e nel messaggio della sera.

**Chi risponde.** Il capo sviluppo risponde del risultato dall'inizio alla fine, non del solo merge: tiene `meta/salute` (edizione, sito, newsletter, controlli partiti davvero, ultimi rilasci) e, quando qualcosa non va, lo scrive lì con causa e rimedio e lo dice a Paolo senza aspettare che lo scopra.

Durante il lavoro i file di stato (`STATO.md`, `PROGETTO.md`, `AZIONI.md`) si aggiornano sul ramo principale (non ripubblicano il sito); tutto il resto passa dai rami. Lo stesso vale, in qualunque giorno, per le mail straordinarie: i file di `redazione/dem/` e `pannello/invii.json` (sempre insieme, dopo `dem.py salva`) vanno su main direttamente, perché non toccano l'edizione né le pagine dei lettori; `dem.py`, `dem.yml` e la vista passano dal rilascio.

Dopo il merge: `sito.yml` pubblica e verifica dal vivo; la mattina dopo `mattino.yml` controlla l'edizione appena è pubblicata. Le prove con l'attività vera si fanno prima del merge dal ramo `con-prova` (procedura A di `PROVA.md`) e, per provare anche la pubblicazione, dopo il merge con una data simulata (procedura B).

Un guasto che blocca l'edizione passa davanti a tutto e segue la stessa strada in piccolo: `avvia`, correzione, `pubblica` (con `--guasto` se è la fascia dell'uscita).
