# Stato del Gommberg

Aggiornato: 22/11/2026 ore 01:45 (rilascio del weekend pubblicato su main alle 00:33 con l'ok di Paolo: merge `4138a2a`, 32 commit, 16 voci; all'1:30 modelli di Kit aggiornati e `mattino.yml` provato).

Lista delle cose da fare: il **Registro dei lavori** (artifact `97f08bbc-950b-4b6e-83eb-4b8d032a3783`, https://claude.ai/artifact/KmCtJUZFx2WKVCRaDiHPtE). Una voce si legge per codice (`db_query` su `tasks`, `codice` = "G-xx"). Dal 21/11 ogni voce è un ordine di lavoro: priorità (Max, High, Medium, Low, TBD = idee), ownership (Claude, Insieme, Paolo), targhetta modello e sforzo, scheda con obiettivo, fatto quando, come, decisioni e vincoli, dipendenze ("dopo"). Le decisioni di una voce stanno solo nella sua scheda: qui si citano i codici.

## In linea
- **Rilascio del 22/11** (merge `4138a2a` su main; collaudo verde in locale e su GitHub, prima sul commit `be25f22` del ramo e poi su main; gommberg.com ripubblicato e verificato dal vivo da `sito.yml`). Per tornare indietro: `bash redazione/rilascia.sh annulla`. Dentro, voce per voce (che cosa fa e perché: nella scheda, per codice):
  - La macchina: G-39 (rete di non regressione in `collaudo.py`, `rilascia.sh`, `collaudo.yml`, `mattino.yml`, mappa in `ARCHITETTURA.md`), G-34 + G-02 (un fatto vuole la fonte primaria o due autori; misure nel pannello), G-03 (Euro Stoxx 50 con EODHD), G-38 (pannello nuovo).
  - Il giornale: G-07 (lessico di casa), G-06 (comunicato per i dati ufficiali di pag. 1), G-04 (agenda del lunedì fino a venerdì), G-05 (tabelle di pag. 5 calcolate dal codice), G-36 e G-47 (scrittura: la voce della #030, nessuna testata tra parentesi, sigle dette in parole, tabelle degli approfondimenti larghe quanto il testo).
  - La scommessa: G-09 (registro), G-08 (il lunedì "La nostra tesi" è lo scenario del registro).
  - Sito e lettori: G-37 (grafico de I numeri), G-40 (riga AI senza nome, gerenza in Chi siamo), G-15 (email del mattino come indice dell'edizione).
- Istruzioni v9.1, scommessa metodo 1.3 dal 16/11, 30 edizioni (ultima #030 del 20/11). **Lunedì 23/11 esce la prima edizione con il motore nuovo.**
- Sito su https://gommberg.com/ dal 20/11 (G-11): Cloudflare Workers con soli file statici, pubblicato da `.github/workflows/sito.yml` a ogni push su main, verifica dal vivo dopo ogni pubblicazione; ramo `prova` = anteprima su workers.dev. Il vecchio indirizzo github.io reindirizza dal ramo `vecchio-indirizzo`.
- Newsletter con Kit da redazione@gommberg.com (SPF/DKIM/DMARC ok). Modelli in Kit allineati al repository il 22/11 (verificati con l'impronta SHA-256 del file): "Gommberg cornice" (nuovo, n. 5716428, lo usa lo script per le edizioni), "Gommberg" (predefinito, con il margine) e "Gommberg edizione" (il ripiego, da togliere dopo la prima email uscita con la cornice) con la riga AI nuova. Si aggiornano da Kit, Broadcasts, Templates.
- Il file dei permessi (`.claude/settings.json`) non fa da filtro: l'attività gira con approvazione automatica.

## Cantiere attivo
**Affidabilità della macchina** (pilastro 5). Il rilascio del 21-22/11 è in linea; restano la sua coda e la prima settimana vera.

- **G-39 in corso**: restano la prova pubblicata e tolta (procedura B di `PROVA.md`), il pulsante "Avvia il rilascio" e la vista del piano nel Registro, i due ruoli nella skill (un solo salvataggio, con "Pronta prima di Fatta" e "voce In corso all'apertura"). Slittano al rilascio del 28/11.
- **G-40 fatta, G-15 in corso**: in linea nel repository e in Kit; invio di prova dalla bozza della #030 con la cornice (n. 27208167) visto da Paolo il 22/11, tutto bene. A G-15 resta la prima email vera di lunedì.
- **G-44** (pag. 5 nei giorni con un mercato chiuso, scade giovedì 26/11, Wall Street chiusa): non è entrata nel rilascio. Va con un rilascio piccolo, stessa strada (`rilascia.sh avvia`, correzione, collaudo, `pubblica`), domenica o al più tardi entro mercoledì 25/11.
- In fila: **G-45** (tre errori della prova che i controlli non vedono), **G-46** (seguiti della prova dopo una settimana vera, più da G-47: il calco "la vendita" nelle forme che il controllo non vede, la ricerca più stretta della seconda prova, il tempo), G-42 (desk che vede le edizioni precedenti, 28/11), G-41, G-43, G-10.

Come si lavora in ogni chat che tocca il motore o il sito: `bash redazione/rilascia.sh avvia`, una voce alla volta, `python3 redazione/collaudo.py` dopo ogni modifica (`--atteso` se la differenza è voluta), commit e `git push origin rilascio`. Voce finita e collaudata sul ramo = **Pronta**; dopo il merge il capo sviluppo la segna Fatta. Il merge lo fa solo il capo sviluppo, con `rilascia.sh pubblica` (`--ok-di-paolo` solo dopo il sì di Paolo al resoconto, quando cambia ciò che il lettore vede).

## Prossimo passo
**Domenica 22/11, prima dell'email di lunedì:**
1. **Paolo**: aggiungere il connettore EODHD all'attività del mattino prima delle 8:58 di lunedì. Senza, G-03 lavora con il ripiego su due fonti web.
2. **G-44** in una chat sua (Opus), con un rilascio piccolo: così era già scritto nella sua scheda.
3. A occhio su PC e telefono: il pannello (anche i vecchi indirizzi #operativita #versioni #metodo) e `numeri.html` nelle tre viste. `sito.yml` ha già verificato che i file in linea sono quelli collaudati.
4. Ramo `prova-2026-11-23-prima`: **resta** finché G-45 e G-46 non sono chiuse (unica copia della prima edizione di prova). `g36-modello` e `pannello` cancellati da Paolo il 22/11.

Fatti il 22/11 dopo il merge: modelli in Kit (G-40, G-15); `mattino.yml` lanciato a mano, verde con "borse chiuse, oggi niente edizione"; `newsletter.yml` in modo prova, verde.

**Lunedì 23/11, sulla prima edizione vera** (alle 10:15 la controlla `mattino.yml`; se esce dopo le 9:40 l'avvio passa alle 8:50, Paolo 19/11; la seconda prova ha chiesto 30 minuti, la prima 39):
- G-47: i tre controlli aggiunti dopo la seconda prova e mai provati su un'edizione (al massimo due aperture con la domanda, testate nominate anche nella riga Fonti, un bene non "vende"), e i minuti.
- G-34 + G-02: quante schede escono con CERCA e quanto costano; nel pannello fonte singola, ricerche, autori per analisi, pagine non raggiunte (lunedì e martedì). Poi congelare l'edizione come campione (`collaudo.py --campione`): i tre di oggi hanno Fatti e Scrittura in rosso per costruzione.
- G-05 e G-03: FTSE MIB e Spread Italia come serie in `dati.json`, `TAB` nel file dell'edizione, nessuna "n.d."; `chiusure.csv` allungato nel commit dell'edizione; chiusura dell'Euro Stoxx 50 di venerdì 20/11 = 5.941,95.
- G-04: "In arrivo" fino a venerdì 27 (giovedì 26 Wall Street chiusa, venerdì seduta corta).
- G-08 e G-09: registro con schema 3, riquadro "La nostra tesi" = scenario con "Ci smentirebbe:", sei perché coerenti; poi congelare il lunedì come campione.
- G-15 e G-40: l'email arrivata, con quale modello.
- G-11: prima edizione vera sul nuovo dominio (link della newsletter su gommberg.com).

Se lunedì qualcosa di grave non regge: `rilascia.sh annulla` riporta main a prima del rilascio, il lavoro resta sul ramo `rilascio`.

## Regole del ritmo
- Lun-ven il ramo principale non si tocca, salvo guasti e i file di stato della redazione; bozze sul ramo `prova`. Un rilascio nel weekend, sul ramo `rilascio`, con un solo merge su main a collaudo verde entro domenica sera (G-39). Un guasto in settimana segue la stessa strada in piccolo (`rilascia.sh avvia`, correzione, `pubblica`). I file di stato (`STATO.md`, `PROGETTO.md`, `AZIONI.md`) si aggiornano su main anche durante il rilascio: non ripubblicano il sito.
- Modello: Sonnet per controlli e piccole correzioni; Opus per dati, motore, decisioni, sito; Fable solo per revisioni grandi e rare.
- Una chat per tema; se si allunga, si chiude salvando qui e nel Registro e si riparte da una nuova.

Ultima revisione del patto (skill "gommberg"): 21/11/2026 (scheda delle voci come ordine di lavoro, G-18). Prossimo ritocco in G-39, in un solo salvataggio: due ruoli, Pronta prima di Fatta, voce In corso all'apertura.
