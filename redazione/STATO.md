# Stato del Gommberg

Aggiornato: 27/11/2026 ore 19:00 (**chat di anticipo: quattro voci pronte per l'Ok, ramo della prova verde**). Una pagina, che deve bastare da sola a una chat nuova: lo storico sta in `PROGETTO.md`, le cose da fare nel **Registro dei lavori** (artifact `97f08bbc-950b-4b6e-83eb-4b8d032a3783`, https://claude.ai/artifact/KmCtJUZFx2WKVCRaDiHPtE; una voce si legge per codice, `db_query` su `tasks` con `codice` = "G-xx"). Le decisioni di una voce stanno solo nella sua scheda: qui si citano i codici.

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
- **Ramo `con-prova`** (punta `70c2147`, collaudo del ramo verde, con dentro l'ultimo main): G-45 (quarto giro), G-54 (secondo giro), G-41, G-50, i caratteri della newsletter, le istruzioni allineate di G-67. Edizione di prova nel fine settimana con la data di lunedì 30/11, lanciata da una chat; poi l'ok di Paolo e `unisci` + `pubblica --dopo-la-prova`. Sulle voci: `prova` = da fare, sabato 28/11. Una sola modifica alla scrittura per prova: G-42 e G-46 aspettano la prova successiva.
- **Pronte, aspettano l'Ok di Paolo nel Registro** (27/11, chat di anticipo: ogni voce sul suo ramo, costruita da un lavoratore e collaudata da un agente diverso): G-60 (`g60` `0ef228d`), G-69 (`g69` `f5e1378`), G-58 con le leve 1 e 3 di G-12 (`g58` `e9b24a0`; serve anche il token di Paolo, tipo Secret; passo 2 = `f46cfbd` dopo una settimana di orologio sano), G-66 con la leva 2 di G-12 (`g66` `fd67180`; primo rilascio con la sequenza in fondo a §5 del ramo, mai il vecchio `--ok-di-paolo`).
- **Costruite, in collaudo indipendente**: G-64 strada B scelta da Paolo il 27/11 (`g64` `ca9db8b`), G-43 (`g43` `5eedeca`), G-42 (`g42` `d9f77df`, parte dal ramo della prova). **In costruzione**: G-46, i cinque interventi decisi dalla rilettura (`g46`, dal ramo della prova).
- **Disegni per Paolo**: G-51, area riservata (`g51` `c3177a9`, solo immagini).

## Prossimo passo
1. Sabato 28/11: edizione di prova del ramo `con-prova` (procedura A di `PROVA.md`, data di lunedì 30/11); lettura del PDF, `prova` sulle voci, poi l'ok di Paolo e il rilascio entro domenica sera.
2. Dopo ogni Ok di Paolo: la chat del rilascio unisce il commit approvato, una voce alla volta. Ordine consigliato: G-69, G-60, G-58 (dopo il token), G-66 per ultima (cambia gli script di rilascio).
3. Lunedì 30/11: prima corsa a orario con il testo nuovo dell'attività del mattino (G-67); prima newsletter dopo G-63. Settimana del 30/11: le tre prove alle 7:00 di G-61.
4. Martedì 1/12 sera: G-12, repository privato; subito dopo il cambio di nome lanciare `sito.yml` a mano (orologio di G-58).
5. Da verificare ancora sul capo sviluppo (G-65): che la sessione abbia agenti, `gh` e Chrome; quanto costa un giro senza lavoro.

## Decisioni di Paolo aperte
G-19 (la carta: dice ancora "attività automatica solo su Sonnet", mentre il capo sviluppo gira su Opus per sua scelta del 27/11; testo proposto: "L'edizione gira solo su Sonnet; le altre attività usano il modello adatto al lavoro"), G-12 (carta su GitHub con tetto a 5 dollari), G-58 (token), G-16, G-46 (perché della scommessa e fonti degli approfondimenti), G-51 (disegno dell'area e tre scelte), G-61 dopo le tre prove alle 7:00. Errori di fatto trovati in edizioni uscite (#033 oro "-7,8% in un mese", #034 il 2 anni a -6 pb invece di -2): se correggere i PDF lo decide Paolo. Le altre richieste stanno in Tocca a te.

## Regole del ritmo
- Modello: Sonnet per controlli, stato e piccole correzioni; Opus per dati, motore, decisioni, sito; Fable solo per revisioni grandi e rare.
- Una chat per tema; se si allunga, si salva qui e nel Registro e si riparte da una nuova.
- Questo file resta di una pagina: ciò che non serve a una chat nuova va in `PROGETTO.md`.

Ultima revisione del patto (skill "gommberg"): 27/11/2026 (due ruoli, rami `g<NN>`, `rilascio` e `con-prova`: salvata da Paolo, G-39 chiusa).
