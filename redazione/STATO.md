# Stato del Gommberg

Aggiornato: 27/11/2026 ore 16:30 (**G-63 in linea: primo rilascio col giro nuovo, Ok dal Registro e chat del rilascio**). Una pagina, che deve bastare da sola a una chat nuova: lo storico sta in `PROGETTO.md`, le cose da fare nel **Registro dei lavori** (artifact `97f08bbc-950b-4b6e-83eb-4b8d032a3783`, https://claude.ai/artifact/KmCtJUZFx2WKVCRaDiHPtE; una voce si legge per codice, `db_query` su `tasks` con `codice` = "G-xx"). Le decisioni di una voce stanno solo nella sua scheda: qui si citano i codici.

## Come si lavora (dal 27/11)
- **Paolo** dirige dal Registro: Tocca a te (ogni richiesta in tre righe: cosa, cosa cambia per il lettore, cosa ti chiedo), Togli e Via sul piano della settimana, Ok, approvo / Non ancora sulle voci da vedere, appunti, Usa il margine. La pagina scrive solo clic e appunti.
- **Il capo sviluppo** è l'attività "Gommberg: capo sviluppo" (Opus, approvazione automatica, id in `meta/capo.attivita`): parte al clic (la pagina la chiama con `fire_trigger`) e ogni giorno alle 19:27. Costruisce sui rami `g<NN>`, fa collaudare da un agente indipendente, prepara fino a Pronta e chiede l'Ok. **Non rilascia mai**. Testo: `registro/CAPO.md`; dati: `registro/CONTRATTO.md`; procedura: `ARCHITETTURA.md` §5. Il venerdì propone il piano della settimana dopo.
- **La chat del rilascio**, aperta da Paolo: unisce il commit approvato (`ok.commit`), lancia l'edizione di prova, annulla, manda le mail. `rilascia.sh`: `avvia [con-prova]`, `collauda`, `unisci <commit provato>`, `pubblica`, `annulla`. Tre finestre: ogni giorno (mai tra le 8:30 e le 10:30), con prova, con Paolo.
- Il clic unico fino alla linea arriva con **G-66** (i cancelli negli script). Spento il 27/11 "Gommberg: giro della sera".

## In linea
- **27/11 ore 16:24, G-63** (merge `2ff757a`, esattamente il commit approvato `20ab01e`; collaudo verde qui e su GitHub): l'elenco degli invii di Kit si rilegge su guasto momentaneo. Niente per i lettori, il sito non si ripubblica; prima prova vera la newsletter di lunedì 30/11. I due spunti del collaudo indipendente (tempo di `newsletter.yml`, elenco degli invii oltre i 100) sono **G-69**.
- **27/11 ore 14:40, G-65** (merge `6248cd4`, collaudo verde qui e su GitHub; tre collaudi indipendenti sul ramo `g65` il 26/11): pagina nuova del Registro, contratto, istruzioni del capo sviluppo, §5. Niente per i lettori. Per tornare indietro: `rilascia.sh annulla`; la pagina di prima è la versione `1795621755-04b8` dell'artifact.
- **27/11 ore 10:47, G-67** (merge `de502a9`): la rinuncia all'edizione passa da `messaggio.py --nessuna` (cinque casi), `pubblica.sh` pubblica anche da una sessione senza ramo. La #035 è uscita alle 10:30.
- **25/11 ore 18:48** (merge `4d9c4df`): due rami di lavoro (G-57), pannello sul piano in vigore (G-60), newsletter senza ripiego (G-15), campione #031 nella rete.

## In attesa
- **Ramo `con-prova`** (fino a `538a162`): G-45, G-54, G-50, i caratteri della newsletter, le istruzioni allineate di G-67. Collaudo del ramo rosso su Coerenza (G-45, già rosso prima). Edizione di prova nel fine settimana con la data di lunedì 30/11, lanciata da una chat; poi l'ok di Paolo e `unisci` + `pubblica --dopo-la-prova`. Sulle voci: `prova` = da fare, sabato 28/11.
- **Piano di prova** (`meta/piano`, settimana del 23/11): G-63 (fatta: il giro Via → capo sviluppo → Ok → chat del rilascio ha funzionato) e G-68.

## Prossimo passo
1. Oggi, prova dal vivo di Paolo. Da verificare sul primo giro vero: che il clic parta e che il capo sviluppo scriva davvero nel Registro (l'attività di prova del 26/11 non aveva scritto la sua riga); che la sessione abbia agenti, `gh` e Chrome; che i lavoratori rispettino i divieti; quanto dura un lavoratore rispetto ai 180 minuti; quanto costa un giro senza lavoro.
2. Stasera alle 19:27 il primo giro a orario: propone il piano della settimana del 30/11.
3. Fine settimana: prova del ramo `con-prova`; G-58 (serve il token di Paolo) con le leve di G-12; G-64 e G-43 con i mockup per Paolo.
4. Martedì 1/12 sera: G-12, repository privato. Lunedì 30/11: prima corsa a orario con il testo nuovo dell'attività del mattino (G-67).

## Decisioni di Paolo aperte
G-19 (la carta: dice ancora "attività automatica solo su Sonnet", mentre il capo sviluppo gira su Opus per sua scelta del 27/11; testo proposto: "L'edizione gira solo su Sonnet; le altre attività usano il modello adatto al lavoro"), G-12 (carta su GitHub con tetto a 5 dollari), G-58 (token), G-16, G-61 dopo le tre prove alle 7:00. Le altre richieste stanno in Tocca a te.

## Regole del ritmo
- Modello: Sonnet per controlli, stato e piccole correzioni; Opus per dati, motore, decisioni, sito; Fable solo per revisioni grandi e rare.
- Una chat per tema; se si allunga, si salva qui e nel Registro e si riparte da una nuova.
- Questo file resta di una pagina: ciò che non serve a una chat nuova va in `PROGETTO.md`.

Ultima revisione del patto (skill "gommberg"): 21/11/2026. Proposta di ritocco del 27/11 (G-39 e G-65): due ruoli come sopra, rami `g<NN>`, `rilascio` e `con-prova`; la salva Paolo.
