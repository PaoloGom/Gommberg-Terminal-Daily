# Stato del Gommberg

Aggiornato: 27/11/2026 ore 20:30 (**chat di anticipo: tre rilasci in linea, G-66 aspetta un Ok nuovo, prova sabato 28/11**). Una pagina, che deve bastare da sola a una chat nuova: lo storico sta in `PROGETTO.md`, le cose da fare nel **Registro dei lavori** (artifact `97f08bbc-950b-4b6e-83eb-4b8d032a3783`, https://claude.ai/artifact/KmCtJUZFx2WKVCRaDiHPtE; una voce si legge per codice, `db_query` su `tasks` con `codice` = "G-xx"). Le decisioni di una voce stanno solo nella sua scheda: qui si citano i codici.

## Come si lavora (dal 27/11)
- **Paolo** dirige dal Registro: Tocca a te (ogni richiesta in tre righe: cosa, cosa cambia per il lettore, cosa ti chiedo), Togli e Via sul piano della settimana, Ok, approvo / Non ancora sulle voci da vedere, appunti, Usa il margine. La pagina scrive solo clic e appunti.
- **Il capo sviluppo** è l'attività "Gommberg: capo sviluppo" (Opus, approvazione automatica, id in `meta/capo.attivita`): parte al clic (la pagina la chiama con `fire_trigger`) e ogni giorno alle 19:27. Costruisce sui rami `g<NN>`, fa collaudare da un agente indipendente, prepara fino a Pronta e chiede l'Ok. **Non rilascia mai**. Testo: `registro/CAPO.md`; dati: `registro/CONTRATTO.md`; procedura: `ARCHITETTURA.md` §5. Il venerdì propone il piano della settimana dopo.
- **La chat del rilascio**, aperta da Paolo: unisce il commit approvato (`ok.commit`), lancia l'edizione di prova, annulla, manda le mail. `rilascia.sh`: `avvia [con-prova]`, `collauda`, `unisci <commit provato>`, `pubblica`, `annulla`. Tre finestre: ogni giorno (mai tra le 8:30 e le 10:30), con prova, con Paolo.
- Il clic unico fino alla linea arriva con **G-66** (i cancelli negli script). Spento il 27/11 "Gommberg: giro della sera".

## In linea
- **27/11 ore 19:41, G-58 passo 1 con le leve 1 e 3 di G-12** (merge `1365faa`; approvata `e9b24a0` più il commit `099327d` con `pannello/minuti.json`, l'uscita vera di `minuti.py`: senza, il collaudo nel browser di GitHub si fermava su un 404). Il Worker è pubblicato con il cron `*/15`; l'orologio resta fermo finché Paolo non crea il token (segreto `GITHUB_ACTIONS_TOKEN`), intanto lavorano le sveglie di GitHub. Non visto dal vivo: `/api/orologio`. Passo 2 = `f46cfbd` dopo una settimana sana.
- **27/11 ore 19:21, G-60** (merge `d9ea8a6`, approvata `0ef228d`): nel pannello la scheda dei piani. **Ore 19:14, G-69** (merge `7c317ce`, approvata `f5e1378`): l'email del mattino una volta sola anche con più di 100 invii; diagnosi dal vivo su Kit verde.
- **27/11 ore 16:24, G-63** (merge `2ff757a`): l'elenco degli invii di Kit si rilegge su guasto momentaneo; prima prova vera la newsletter di lunedì 30/11. **Ore 14:40, G-65** (merge `6248cd4`): pagina nuova del Registro, contratto, capo sviluppo. **Ore 10:47, G-67** (merge `de502a9`): rinuncia all'edizione da `messaggio.py --nessuna`.

## In attesa
- **Ramo `con-prova`** (punta `3e992b7`, riallineato al main del 27/11 sera con due conflitti risolti tenendo le due parti, collaudo del ramo verde): G-45, G-54, G-41, G-50, i caratteri della newsletter, le istruzioni di G-67. Edizione di prova sabato 28/11 con la data di lunedì 30/11 (procedura A; la lancia la chat di anticipo alle 9:00, l'ha chiesto Paolo); poi l'ok di Paolo e `unisci` + `pubblica --dopo-la-prova` entro domenica sera. G-42 (`g42` `28ad7da`) e G-46 entrano nella prova successiva (5-6/12).
- **G-66, aspetta un Ok NUOVO** (`g66` `203ce08` = l'approvata `fd67180` più il main del 27/11 sera): `pubblica --commit fd67180` si è fermato da sé perché il commit approvato non si univa più senza conflitti. Terzo collaudo indipendente verde sull'albero riallineato. Primo rilascio con la sequenza in fondo a §5 (mai il vecchio `--ok-di-paolo`). **Ordine con la prova**: una prova avviata con il `prova.sh` vecchio non passa il `pubblica --dopo-la-prova` nuovo, quindi G-66 va in linea o prima della prova (e poi si riallinea `con-prova`) o dopo il rilascio di domenica, mai in mezzo.
- **Pronte, aspettano Paolo**: G-64 strada B (`g64` `369f9dc`, immagini mandate: manca l'Ok sulla versione costruita); G-43 (`g43` `79a457a`: prima del merge serve l'indirizzo iscritto di Paolo e la prova dal vivo su Kit, perché il merge accende l'invio della sera).
- **In collaudo indipendente**: G-51 costruita (`g51` `0d332e2`, area riservata con accesso; collaudo da attaccante in corso; va in linea dopo G-58 e G-12); G-46, cinque ritocchi ai controlli (`g46` `1c7ecff`, terzo passaggio). I due seguiti di G-46 che cambiano ciò che il lettore legge NON sono costruiti: aspettano il sì o no di Paolo.

## Prossimo passo
1. Sabato 28/11 ore 9:00: edizione di prova del ramo `con-prova` (se G-66 ha l'Ok nuovo: prima G-66 in linea, poi `con-prova` riallineato, poi la prova con il `prova.sh` nuovo); lettura indipendente del PDF, `prova` sulle voci, PDF a Paolo, il suo ok e il rilascio entro domenica sera.
2. Dopo il token di Paolo (G-58): guardare `/api/orologio` (segreto=true, battito ogni 15 minuti) e i giri `workflow_dispatch`; una settimana dopo il passo 2.
3. Lunedì 30/11: prima corsa a orario con il testo nuovo dell'attività del mattino (G-67); prima newsletter dopo G-63 e G-69; alle 10:15 il primo controllo del mattino con la riga dell'orologio e dei minuti. Settimana del 30/11: le tre prove alle 7:00 di G-61.
4. Martedì 1/12 sera: G-12, repository privato; subito dopo il cambio di nome lanciare `sito.yml` a mano. Poi G-51.
5. Da verificare ancora sul capo sviluppo (G-65): che la sessione abbia agenti, `gh` e Chrome; quanto costa un giro senza lavoro. Dopo G-66: allineare il testo dell'attività nell'app a `CAPO.md`.

## Decisioni di Paolo aperte
G-66 (Ok nuovo sulla versione riallineata), G-64 (Ok sulla versione costruita), G-58 (token, tipo Secret), G-43 (il suo indirizzo iscritto per la prova dal vivo), G-46 (sì o no ai perché della scommessa e alla fonte grande sotto gli approfondimenti: il 27/11 ha scritto che la voce non gli è chiara, domanda riscritta), G-19 (la carta dice ancora "attività automatica solo su Sonnet"; testo proposto: "L'edizione gira solo su Sonnet; le altre attività usano il modello adatto al lavoro"), G-12 (carta su GitHub con tetto a 5 dollari), G-16, G-61 dopo le tre prove alle 7:00, G-49 intorno al 7/12. Deciso il 27/11: G-64 strada B; G-51 ok al disegno; nessuna correzione dei PDF usciti per gli errori trovati dalla rilettura (#032-#035). Le altre richieste stanno in Tocca a te.

## Regole del ritmo
- Modello: Sonnet per controlli, stato e piccole correzioni; Opus per dati, motore, decisioni, sito; Fable solo per revisioni grandi e rare.
- Una chat per tema; se si allunga, si salva qui e nel Registro e si riparte da una nuova.
- Questo file resta di una pagina: ciò che non serve a una chat nuova va in `PROGETTO.md`.

Ultima revisione del patto (skill "gommberg"): 27/11/2026 (due ruoli, rami `g<NN>`, `rilascio` e `con-prova`: salvata da Paolo, G-39 chiusa).
