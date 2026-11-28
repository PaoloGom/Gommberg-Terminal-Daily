# Stato del Gommberg

Aggiornato: 28/11/2026 ore 2:20 (**chat di anticipo: cinque rilasci in linea tra venerdì sera e la notte, cancelli nuovi accesi, prova sabato mattina**). Una pagina, che deve bastare da sola a una chat nuova: lo storico sta in `PROGETTO.md`, le cose da fare nel **Registro dei lavori** (artifact `97f08bbc-950b-4b6e-83eb-4b8d032a3783`, https://claude.ai/artifact/KmCtJUZFx2WKVCRaDiHPtE; una voce si legge per codice, `db_query` su `tasks` con `codice` = "G-xx"). Le decisioni di una voce stanno solo nella sua scheda: qui si citano i codici.

## Come si lavora (dal 27/11)
- **Paolo** dirige dal Registro: Tocca a te (ogni richiesta in tre righe: cosa, cosa cambia per il lettore, cosa ti chiedo), Togli e Via sul piano della settimana, Ok, approvo / Non ancora sulle voci da vedere, appunti, Usa il margine. La pagina scrive solo clic e appunti.
- **Il capo sviluppo** è l'attività "Gommberg: capo sviluppo" (Opus, approvazione automatica, id in `meta/capo.attivita`): parte al clic (la pagina la chiama con `fire_trigger`) e ogni giorno alle 19:27. Costruisce sui rami `g<NN>`, fa collaudare da un agente indipendente, prepara fino a Pronta e chiede l'Ok. **Non rilascia mai**. Testo: `registro/CAPO.md`; dati: `registro/CONTRATTO.md`; procedura: `ARCHITETTURA.md` §5. Il venerdì propone il piano della settimana dopo.
- **La chat del rilascio**, aperta da Paolo: unisce il commit approvato (`ok.commit`), lancia l'edizione di prova, annulla, manda le mail. `rilascia.sh`: `avvia [con-prova]`, `collauda`, `unisci <commit provato>`, `pubblica --commit <ok.commit> [--dopo-la-prova]`, `annulla`; `prova.sh avvio|esito|chiudi`. Tre finestre: ogni giorno (mai tra le 8:30 e le 10:30), con prova, con Paolo.
- **I cancelli sono negli script dal 28/11 (G-66)**: `pubblica` unisce solo il commit con l'Ok, lo rifiuta se non si unisce a main senza conflitti (allora si riallinea il ramo della voce e si chiede un Ok nuovo), e il collaudo di GitHub parte solo dal ramo `cancello`. Da allineare a mano il testo dell'attività del capo sviluppo nell'app a `registro/CAPO.md`.

## In linea
- **28/11 ore 2:06, G-66** (merge `805005d`, esattamente l'approvata `203ce08`): cancelli negli script di rilascio, `catena.txt`, `prova.sh` nuovo, collaudo di GitHub solo dal ramo `cancello` (visto partire e verde). **Ore 1:50, G-64** (merge `2712ebb`): 46 pagine di analisi `e/NNN/<chiave>.html` per le edizioni #026-#035, byte per byte quelle approvate; il controllo dei grafici ora confronta ciò che mostrano e non i byte.
- **27/11 ore 19:41, G-58 passo 1 con le leve 1 e 3 di G-12** (merge `1365faa`): Worker pubblicato con il cron `*/15`; l'orologio resta fermo finché Paolo non crea il token (segreto `GITHUB_ACTIONS_TOKEN`), intanto lavorano le sveglie di GitHub. Non visto dal vivo: `/api/orologio`. Passo 2 = `f46cfbd` dopo una settimana sana. **Ore 19:21, G-60** (merge `d9ea8a6`). **Ore 19:14, G-69** (merge `7c317ce`). **Ore 16:24, G-63**; **14:40, G-65**; **10:47, G-67**.
- Da questa sessione gommberg.com non si raggiunge: per ogni rilascio fa fede la verifica dal vivo di `sito.yml` (verde su tutti).

## In attesa
- **Ramo `con-prova`** (punta `71f4143`, riallineato a main con G-64 e G-66 dentro, conflitti risolti tenendo le due parti, collaudo del ramo verde): G-45, G-54, G-41, G-50, i caratteri della newsletter, le istruzioni di G-67. Edizione di prova sabato 28/11 con la data di lunedì 30/11 (procedura A, `prova.sh` nuovo; la lancia la chat di anticipo alle 9:00, l'ha chiesto Paolo); poi l'ok di Paolo e `avvia`, `unisci <prova.commit>`, `pubblica --commit <prova.commit> --dopo-la-prova` entro domenica sera. G-42 (`g42` `28ad7da`) e G-46 entrano nella prova successiva (5-6/12).
- **G-43** (`g43` `79a457a`, Ok di Paolo nel Registro): prima del merge la prova dal vivo su Kit, sabato dopo le 10:30, su paolo.gommellini@gmail.com; il ramo va riallineato a main (conflitto atteso in `pagine.py`) e, per il cancello, serve poi l'Ok sul commit riallineato.
- **G-51** (`g51` `b0ac36d`): due collaudi da attaccante, nessun varco; chiusi 2 bloccanti e 5 seri in tre giri di correzioni. Manca: merge di main (conflitti additivi in `collaudo.py`, `mattino.py`, `ARCHITETTURA.md`), terzo collaudo indipendente, immagini e Ok. Paolo ha accettato il rischio delle quote gratuite di Cloudflare. In linea dopo G-12.
- **G-46** (`g46` `ac65905`): cinque ritocchi ai controlli pronti per una prova (prima va unito l'ultimo `con-prova`). Da costruire: i "perché" della scommessa (Paolo: sì solo se migliora l'esperienza del lettore; si giudica nella prova). Non costruire: la fonte grande sotto gli approfondimenti, finché Paolo non risponde alla domanda chiarita.
- **G-19**: Paolo ha approvato la riga sul modello (riga 32 di `CARTA.md`); va portata con un rilascio (la carta è nella catena) e gli va chiesto se la bozza è approvata tutta.

## Prossimo passo
1. Sabato 28/11 ore 9:00: edizione di prova dal ramo `con-prova`; lettura indipendente del PDF, `prova` sulle voci, PDF a Paolo, il suo ok e il rilascio entro domenica sera.
2. Sabato mattina: studio di G-12 chiesto da Paolo (niente carta di credito: come stare sotto il limite dei minuti per sempre con il repository privato, piano con i numeri); dopo le 10:30 la prova dal vivo di G-43; G-19; terzo collaudo di G-51; i "perché" della scommessa su `g46`.
3. Dopo il token di Paolo (G-58): guardare `/api/orologio` (segreto=true, battito ogni 15 minuti) e i giri `workflow_dispatch`; una settimana dopo il passo 2.
4. Lunedì 30/11: prima corsa a orario con il testo nuovo dell'attività del mattino (G-67), prima newsletter dopo G-63 e G-69, prime pagine delle analisi generate dal mattino (G-64: il controllo delle 10:15 dice se sono nate), prima riga dell'orologio e dei minuti. Settimana del 30/11: le tre prove alle 7:00 di G-61.
5. Martedì 1/12 sera: G-12, repository privato, secondo il piano che esce dallo studio; subito dopo il cambio di nome lanciare `sito.yml` a mano. Poi G-51.

## Decisioni di Paolo aperte
G-58 (token, tipo Secret), G-46 (sì o no alla fonte grande sotto gli approfondimenti, domanda chiarita il 28/11), G-19 (la bozza della carta è approvata tutta?), G-16, G-61 dopo le tre prove alle 7:00, G-49 intorno al 7/12, l'ok al rilascio dopo la prova di sabato. Deciso il 27-28/11: G-64 strada B e in linea; G-66 in linea; G-12 niente carta di credito su GitHub, si studia come non arrivare mai al limite; G-51 ok al disegno e rischio delle quote gratuite accettato; G-46 "perché" della scommessa sì se migliora l'esperienza del lettore; nessuna correzione dei PDF usciti (#032-#035). Le altre richieste stanno in Tocca a te.

## Regole del ritmo
- Modello: Sonnet per controlli, stato e piccole correzioni; Opus per dati, motore, decisioni, sito; Fable solo per revisioni grandi e rare.
- Una chat per tema; se si allunga, si salva qui e nel Registro e si riparte da una nuova.
- Questo file resta di una pagina: ciò che non serve a una chat nuova va in `PROGETTO.md`.

Ultima revisione del patto (skill "gommberg"): 27/11/2026 (due ruoli, rami `g<NN>`, `rilascio` e `con-prova`: salvata da Paolo, G-39 chiusa).
