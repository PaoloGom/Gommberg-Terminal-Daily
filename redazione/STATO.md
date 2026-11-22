# Stato del Gommberg

Aggiornato: 22/11/2026 ore 02:55 (rilascio del weekend pubblicato su main alle 00:33 con l'ok di Paolo: merge `4138a2a`, 32 commit, 16 voci; all'1:30 modelli di Kit aggiornati e `mattino.yml` provato; alle 02:45 rilascio piccolo di G-10, merge `e13e2bc`; alle 03:35 mockup di G-14 approvato; alle 11:45 G-17 pronta sul ramo `g17-dem`; alle 10:50 G-44 pronta sul ramo `rilascio`).

Lista delle cose da fare: il **Registro dei lavori** (artifact `97f08bbc-950b-4b6e-83eb-4b8d032a3783`, https://claude.ai/artifact/KmCtJUZFx2WKVCRaDiHPtE). Una voce si legge per codice (`db_query` su `tasks`, `codice` = "G-xx"). Dal 21/11 ogni voce è un ordine di lavoro: priorità (Max, High, Medium, Low, TBD = idee), ownership (Claude, Insieme, Paolo), targhetta modello e sforzo, scheda con obiettivo, fatto quando, come, decisioni e vincoli, dipendenze ("dopo"). Le decisioni di una voce stanno solo nella sua scheda: qui si citano i codici.

## In linea
- **Rilascio del 22/11** (merge `4138a2a` su main; collaudo verde in locale e su GitHub, prima sul commit `be25f22` del ramo e poi su main; gommberg.com ripubblicato e verificato dal vivo da `sito.yml`). Per tornare indietro: `bash redazione/rilascia.sh annulla`. Dentro, voce per voce (che cosa fa e perché: nella scheda, per codice):
  - La macchina: G-39 (rete di non regressione in `collaudo.py`, `rilascia.sh`, `collaudo.yml`, `mattino.yml`, mappa in `ARCHITETTURA.md`), G-34 + G-02 (un fatto vuole la fonte primaria o due autori; misure nel pannello), G-03 (Euro Stoxx 50 con EODHD), G-38 (pannello nuovo).
  - Il giornale: G-07 (lessico di casa), G-06 (comunicato per i dati ufficiali di pag. 1), G-04 (agenda del lunedì fino a venerdì), G-05 (tabelle di pag. 5 calcolate dal codice), G-36 e G-47 (scrittura: la voce della #030, nessuna testata tra parentesi, sigle dette in parole, tabelle degli approfondimenti larghe quanto il testo).
  - La scommessa: G-09 (registro), G-08 (il lunedì "La nostra tesi" è lo scenario del registro).
  - Sito e lettori: G-37 (grafico de I numeri), G-40 (riga AI senza nome, gerenza in Chi siamo), G-15 (email del mattino come indice dell'edizione).
- **Rilascio piccolo del 22/11** (merge `e13e2bc`, ok di Paolo): G-10, stesso marchio in favicon, icona per la Home di iPhone e copertina dei link; avatar email invariato. `sito.yml` verde, pagine dal vivo identiche.
- Istruzioni v9.1, scommessa metodo 1.3 dal 16/11, 30 edizioni (ultima #030 del 20/11). **Lunedì 23/11 esce la prima edizione con il motore nuovo.**
- Sito su https://gommberg.com/ dal 20/11 (G-11): Cloudflare Workers con soli file statici, pubblicato da `.github/workflows/sito.yml` a ogni push su main, verifica dal vivo dopo ogni pubblicazione; ramo `prova` = anteprima su workers.dev. Il vecchio indirizzo github.io reindirizza dal ramo `vecchio-indirizzo`.
- Newsletter con Kit da redazione@gommberg.com (SPF/DKIM/DMARC ok). Modelli in Kit allineati al repository il 22/11 (verificati con l'impronta SHA-256 del file): "Gommberg cornice" (nuovo, n. 5716428, lo usa lo script per le edizioni), "Gommberg" (predefinito, con il margine) e "Gommberg edizione" (il ripiego, da togliere dopo la prima email uscita con la cornice) con la riga AI nuova. Si aggiornano da Kit, Broadcasts, Templates.
- Il file dei permessi (`.claude/settings.json`) non fa da filtro: l'attività gira con approvazione automatica.

## Cantiere attivo
**Affidabilità della macchina** (pilastro 5). Il rilascio del 21-22/11 è in linea; restano la sua coda e la prima settimana vera.

- **G-39 in corso**: restano la prova pubblicata e tolta (procedura B di `PROVA.md`), il pulsante "Avvia il rilascio" e la vista del piano nel Registro, i due ruoli nella skill (un solo salvataggio, con "Pronta prima di Fatta" e "voce In corso all'apertura"). Slittano al rilascio del 28/11.
- **G-40 fatta, G-15 in corso**: in linea nel repository e in Kit; invio di prova dalla bozza della #030 con la cornice (n. 27208167) visto da Paolo il 22/11, tutto bene. A G-15 resta la prima email vera di lunedì.
- **G-44 Pronta sul ramo rilascio** (22/11, commit `6ac9b89` e `b81d893`, collaudo verde qui e su GitHub su `b81d893`, con dentro G-35 e G-14; collaudo indipendente fatto, riserve chiuse): le tabelle di pag. 5 scrivono intestazione, titoli dei gruppi e note dalla data vera di ogni riga, e `controlli_dati.py` conta l'età di un dato in giorni di uscita. Nessun file pubblico, campioni identici: per questa voce non serve l'ok di Paolo. Entra nel merge unico di stasera (chat di G-35). **Deve essere in linea prima dell'edizione di lunedì 23/11**: Tokyo è chiusa, e senza G-44 il titolo "Asia" e la nota escono con la data sbagliata. Il ramo `rilascio-g44` su GitHub è di servizio (nato quando il ramo `rilascio` ha ricevuto G-35 e G-14): non ha nulla che non sia in `rilascio`, lo cancella Paolo.
- **G-35 Pronta sul ramo rilascio** (22/11, commit 8effb5f, collaudo verde qui e su GitHub): pagine `impara/<parola>.html` e contenuto senza JavaScript generati da `sito/statico.py` solo nel sito pubblicato, robots.txt, freccia delle sigle corretta. Search Console ora gestita anche dall'account del Gommberg; Bing Webmaster Tools aperto. **Un solo merge stasera** con G-44 e G-14 quando sono Pronte, lo fa la chat di G-35 (Paolo 22/11: il suo sì vale per ciò che cambia per il lettore). Dopo il merge: sitemap reinviata, indicizzazione chiesta, robots.txt verificato dal vivo (Cloudflare ha il robots.txt gestito acceso).
- **G-17 pronta** (mail straordinarie programmabili: un file per mail in `redazione/dem/`, postino `dem.yml`, vista Invii nel pannello, privacy allargata) sul ramo `g17-dem`, commit `f72ea78`: collaudo verde, collaudo indipendente verde al terzo giro. Entra nel **rilascio del 28/11** con un merge nel ramo `rilascio` e serve l'ok di Paolo (cambiano privacy, modulo di iscrizione, `grazie.html`, pannello). Subito dopo il merge: `dem.yml` a mano in modo "piano" per vedere le risposte vere di Kit. Poi **G-49**: testo definitivo degli auguri del 19/12 e ok di Paolo entro il 9/12.
- In fila con una data: **G-41** (chiusure di Kospi e Hang Seng da EODHD, e il livello ricavato dalla variazione che parta dall'ultima seduta vera: entro il 24/12, perché lunedì 28/12 e lunedì 4/1 quelle righe uscirebbero dalla tabella) e **G-50** (giorni senza edizione del 2027 e promemoria di dicembre che oggi non scatterebbe, entro il 20/12). Tutte e due nate da G-44.
- In fila: **G-45** (tre errori della prova che i controlli non vedono), **G-46** (seguiti della prova dopo una settimana vera, più da G-47: il calco "la vendita" nelle forme che il controllo non vede, la ricerca più stretta della seconda prova, il tempo), G-42 (desk che vede le edizioni precedenti, 28/11), **G-14** (il GOMM: indice di lettura con candele e volume su I numeri, nel nastro della homepage e in fondo alle edizioni; mockup approvato il 22/11, rilascio del 28/11, tutto nella scheda), G-41, G-43, G-48.

Come si lavora in ogni chat che tocca il motore o il sito: `bash redazione/rilascia.sh avvia`, una voce alla volta, `python3 redazione/collaudo.py` dopo ogni modifica (`--atteso` se la differenza è voluta), commit e `git push origin rilascio`. Voce finita e collaudata sul ramo = **Pronta**; dopo il merge il capo sviluppo la segna Fatta. Il merge lo fa solo il capo sviluppo, con `rilascia.sh pubblica` (`--ok-di-paolo` solo dopo il sì di Paolo al resoconto, quando cambia ciò che il lettore vede).

## Prossimo passo
**Domenica 22/11, prima dell'email di lunedì:**
1. Connettore EODHD: verificato da Paolo il 22/11 nelle impostazioni dell'attività del mattino (Connettori: EODHD presente, modo Auto, Sonnet 5.5). Lunedì si vede se `dati.json` esce con fonte "EODHD + ...".
2. **G-44**: Pronta, entra nel merge unico di stasera (vedi Cantiere attivo).
3. A occhio su PC e telefono: il pannello (anche i vecchi indirizzi #operativita #versioni #metodo) e `numeri.html` nelle tre viste. `sito.yml` ha già verificato che i file in linea sono quelli collaudati.
4. Ramo `prova-2026-11-23-prima`: **resta** finché G-45 e G-46 non sono chiuse (unica copia della prima edizione di prova). `g36-modello` e `pannello` cancellati da Paolo il 22/11.

Fatti il 22/11 dopo il merge: modelli in Kit (G-40, G-15); `mattino.yml` lanciato a mano, verde con "borse chiuse, oggi niente edizione"; `newsletter.yml` in modo prova, verde.

**Lunedì 23/11, sulla prima edizione vera** (alle 10:15 la controlla `mattino.yml`; se esce dopo le 9:40 l'avvio passa alle 8:50, Paolo 19/11; la seconda prova ha chiesto 30 minuti, la prima 39):
- G-47: i tre controlli aggiunti dopo la seconda prova e mai provati su un'edizione (al massimo due aperture con la domanda, testate nominate anche nella riga Fonti, un bene non "vende"), e i minuti.
- G-34 + G-02: quante schede escono con CERCA e quanto costano; nel pannello fonte singola, ricerche, autori per analisi, pagine non raggiunte (lunedì e martedì). Poi congelare l'edizione come campione (`collaudo.py --campione`): i tre di oggi hanno Fatti e Scrittura in rosso per costruzione.
- G-05 e G-03: FTSE MIB e Spread Italia come serie in `dati.json`, `TAB` nel file dell'edizione, nessuna "n.d."; `chiusure.csv` allungato nel commit dell'edizione; chiusura dell'Euro Stoxx 50 di venerdì 20/11 = 5.941,95.
- G-44: pag. 5 con Tokyo chiusa: titolo "Asia (23/11)", nella nota "Nikkei 225: dato del 20/11", la chiusura detta in testata o nel testo. Venerdì 27/11 lo stesso con Wall Street ferma al 25 (riga in G-46: anche se la nota più lunga ha chiesto un giro di correzione).
- G-04: "In arrivo" fino a venerdì 27 (giovedì 26 Wall Street chiusa, venerdì seduta corta).
- G-08 e G-09: registro con schema 3, riquadro "La nostra tesi" = scenario con "Ci smentirebbe:", sei perché coerenti; poi congelare il lunedì come campione.
- G-15 e G-40: l'email arrivata, con quale modello.
- G-11: prima edizione vera sul nuovo dominio (link della newsletter su gommberg.com).

Se lunedì qualcosa di grave non regge: `rilascia.sh annulla` riporta main a prima del rilascio, il lavoro resta sul ramo `rilascio`.

## Regole del ritmo
- Lun-ven il ramo principale non si tocca, salvo guasti e i file di stato della redazione; bozze sul ramo `prova`. Un rilascio nel weekend, sul ramo `rilascio`, con un solo merge su main a collaudo verde entro domenica sera (G-39). Un guasto in settimana segue la stessa strada in piccolo (`rilascia.sh avvia`, correzione, `pubblica`). I file di stato (`STATO.md`, `PROGETTO.md`, `AZIONI.md`) si aggiornano su main anche durante il rilascio: non ripubblicano il sito. Dal merge di G-17, lo stesso vale in qualunque giorno per le mail straordinarie: i file di `redazione/dem/` e `pannello/invii.json`, sempre insieme dopo `dem.py salva` (`redazione/dem/LEGGIMI.md`).
- Modello: Sonnet per controlli e piccole correzioni; Opus per dati, motore, decisioni, sito; Fable solo per revisioni grandi e rare.
- Una chat per tema; se si allunga, si chiude salvando qui e nel Registro e si riparte da una nuova.

Ultima revisione del patto (skill "gommberg"): 21/11/2026 (scheda delle voci come ordine di lavoro, G-18). Prossimo ritocco in G-39, in un solo salvataggio: due ruoli, Pronta prima di Fatta, voce In corso all'apertura.
