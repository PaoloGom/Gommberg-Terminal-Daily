# Stato del Gommberg

Aggiornato: 28/11/2026 ore 15:00 (**chat di anticipo: la prova di sabato non è approvata né salvata, il ramo della prova NON va in linea; lunedì esce la linea di oggi**). Una pagina, che deve bastare da sola a una chat nuova: lo storico sta in `PROGETTO.md`, le cose da fare nel **Registro dei lavori** (artifact `97f08bbc-950b-4b6e-83eb-4b8d032a3783`, https://claude.ai/artifact/KmCtJUZFx2WKVCRaDiHPtE; una voce si legge per codice, `db_query` su `tasks` con `codice` = "G-xx"). Le decisioni di una voce stanno solo nella sua scheda: qui si citano i codici.

## Come si lavora (dal 27/11)
- **Paolo** dirige dal Registro: Tocca a te (ogni richiesta in tre righe: cosa, cosa cambia per il lettore, cosa ti chiedo), Togli e Via sul piano della settimana, Ok, approvo / Non ancora sulle voci da vedere, appunti, Usa il margine. La pagina scrive solo clic e appunti.
- **Il capo sviluppo** è l'attività "Gommberg: capo sviluppo" (Opus, approvazione automatica, id in `meta/capo.attivita`): parte al clic (la pagina la chiama con `fire_trigger`) e ogni giorno alle 19:27. Costruisce sui rami `g<NN>`, fa collaudare da un agente indipendente, prepara fino a Pronta e chiede l'Ok. **Non rilascia mai**. Testo: `registro/CAPO.md`; dati: `registro/CONTRATTO.md`; procedura: `ARCHITETTURA.md` §5. Il venerdì propone il piano della settimana dopo.
- **La chat del rilascio**, aperta da Paolo: unisce il commit approvato (`ok.commit`), lancia l'edizione di prova, annulla, manda le mail. `rilascia.sh`: `avvia [con-prova]`, `collauda`, `unisci <commit provato>`, `pubblica --commit <ok.commit> [--dopo-la-prova]`, `annulla`; `prova.sh avvio|esito|chiudi`. Tre finestre: ogni giorno (mai tra le 8:30 e le 10:30), con prova, con Paolo.
- **I cancelli sono negli script dal 28/11 (G-66)**: `pubblica` unisce solo il commit con l'Ok, lo rifiuta se non si unisce a main senza conflitti (allora si riallinea il ramo della voce e si chiede un Ok nuovo), e il collaudo di GitHub parte solo dal ramo `cancello`. Da allineare a mano il testo dell'attività del capo sviluppo nell'app a `registro/CAPO.md`.

## In linea
- **28/11 ore 9:27, G-19**: la carta è approvata da Paolo (merge `6621ce6` e `af07344`): l'edizione gira solo su Sonnet, le altre attività usano il modello adatto.
- **28/11 ore 2:06, G-66** (merge `805005d`): cancelli negli script di rilascio, `catena.txt`, `prova.sh` nuovo, collaudo di GitHub solo dal ramo `cancello`. **Ore 1:50, G-64** (merge `2712ebb`): 46 pagine di analisi `e/NNN/<chiave>.html`.
- **27/11 ore 19:41, G-58 passo 1 con le leve 1 e 3 di G-12** (merge `1365faa`): Worker con il cron `*/15`; l'orologio resta fermo finché Paolo non crea il token (`GITHUB_ACTIONS_TOKEN`). Passo 2 = `f46cfbd` dopo una settimana sana (il cherry-pick oggi dà conflitti: va rifatto a mano). **Ore 19:21, G-60**; **19:14, G-69**; **16:24, G-63**; **14:40, G-65**; **10:47, G-67**.
- Da questa sessione gommberg.com non si raggiunge: per ogni rilascio fa fede la verifica dal vivo di `sito.yml`.

## In attesa
- **Attenzione (28/11 sera)**: il limite del modello Fable è finito fino al 4/12. Lavoratori e collaudatori vanno su **Opus o Sonnet**, uno alla volta. Tre agenti si sono fermati a metà: il loro lavoro è salvato sui rami indicati sotto, NON collaudato.
- **Ramo `con-prova`** (punta `5fdb1c8`: G-45, G-54, G-41, G-50, caratteri della newsletter, istruzioni di G-67): la **prova del 28/11** (edizione 036 di prova) **non è approvata e non è salvata**. Paolo: grafici di pag. 2 sbagliati (dati di anni diversi sugli stessi giorni), fonti deboli, pag. 2 ripetitiva. Ordine: G-71 in linea (Ok di Paolo), G-72 dentro con-prova, prova rifatta, PDF letto da un agente indipendente, ok di Paolo, poi `unisci` + `pubblica --commit <prova.commit> --dopo-la-prova`. **Finché con-prova non è in linea, niente altri rilasci che tocchino collaudo.py o ARCHITETTURA.md**.
- **G-71** (`g71` `1e393ff`, sopra main, si unisce pulito con main, con-prova e g12; collaudo del costruttore verde): `prova.sh` trova il repository dal proprio percorso; `chiudi` che non salva stampa `PROVA NON SALVATA` e esce 1; chiusi due buchi vecchi (PDF mancante dava "salvata"; push rifiutato usciva 0); nuovo `chiudi --non-riuscita`; `esito` senza `--depth=5`. **Collaudo indipendente interrotto dal limite: da rifare**, poi Ok di Paolo, poi `pubblica --commit 1e393ff...`. La prova ferma sul ramo `prova` (esito in-corso) non blocca: il prossimo `avvio` la sostituisce.
- **G-72** (`g72` `85ec68e`, da con-prova): controllo generale delle serie dei grafici a linea (`controlli_grafici.py`, motore, attesi della rete). **Lavoro a metà, non collaudato**: da finire (date crescenti, periodo come nel titolo, ultimo valore = chiusura in dati.json, frase nelle istruzioni, misura sulle edizioni archiviate), collaudo indipendente, poi dentro con-prova.
- **G-43** (`g43` `607eb246`: punta della prova dal vivo; collaudo indipendente: "PROVA-INVIO: SI PUÒ LANCIARE"). Fatti misurati: Kit aggiorna gli elenchi di un'etichetta con 2-3 minuti di ritardo (letture per id subito giuste). Bozza di prova `27337643` (etichetta `gommberg-benvenuto-prova-2026-11-28-1510`) creata il 28/11 15:13, filtro sul solo gruppo di prova. Passi: Paolo guarda in Kit che i destinatari siano 1, poi `prova-invio` (finestre 08:00-08:19 e 10:30-20:49), mail a Paolo 10 minuti dopo, `prova-pulizia` SOLO dopo che la mail è arrivata. Correzioni E1-E7 (doppia mail possibile con due giri ravvicinati, giro in due tempi per il ritardo di Kit, id della bozza come input) sul ramo **`g43-lavoro` `13a08b2`, a metà e non collaudate**: da finire, collaudo indipendente, Ok di Paolo, rilascio dopo con-prova.
- **G-12, rilascio piccolo sui minuti** (`g12` `9379702`, collaudo indipendente: pubblicare sì): aspetta l'Ok di Paolo sulla versione costruita e va in linea dopo con-prova. Studio in `redazione/collaudi/2026-11-28/g12/piano.md` (da privato circa 350 minuti al mese su 2.000, 690 nel mese pesante). Paolo non ha altri repository privati. Passaggio a privato: martedì 1/12 sera.
- **G-51** (`g51` `26b5234`, Ok di Paolo il 28/11): tre collaudi da attaccante, nessun varco. In linea dopo G-12; quel giorno Paolo mette due segreti su Cloudflare (mai in chat).
- **G-46** (`g46` `6e47697`, pronta per una prova) e **G-42** (`g42` `28ad7da`): prova del 5-6/12; unire i due rami in con-prova risolvendo una riga di ARCHITETTURA.md (già provato: collaudo verde).

## Prossimo passo
1. G-71: collaudo indipendente, Ok di Paolo, in linea. G-72: finire, collaudo, dentro con-prova. Rifare la prova (domenica 29/11 o la sera di un feriale), PDF letto da un agente indipendente prima di Paolo.
2. G-43: prova dal vivo con Paolo che guarda Kit; poi E1-E7 da `g43-lavoro`.
3. Lunedì 30/11 esce la linea attuale (Sonnet, non toccata dal limite di Fable): prima corsa con il testo nuovo del mattino (G-67), prima newsletter dopo G-63 e G-69, prime analisi dal mattino (G-64), prima riga dei minuti alle 10:15.
4. Martedì 1/12 sera: G-12, repository privato con Paolo (circa 45 minuti); subito dopo `sito.yml` a mano. Poi G-51.
5. Dopo il token di Paolo (G-58): `/api/orologio` e i giri `workflow_dispatch`.
6. Allineare il testo dell'attività del capo sviluppo nell'app a `registro/CAPO.md`.

## Cose da fare per Paolo (piccole)
1. Kit: bozza `gommberg-benvenuto-prova-2026-11-28-1510`, destinatari = 1? (serve alla prova di G-43).
2. Ok sul rilascio piccolo di G-12 (`9379702`), e poi su G-71 dopo il collaudo.
3. G-58: token di GitHub in Cloudflare come "Secret" (lo crea e lo inserisce lui).
4. Il giorno di G-51: utente e password dell'area riservata in Cloudflare come "Secret" (password di almeno 16 caratteri, mai scritta in chat).
5. GitHub: avvisi di spesa al 90% e 100%.
6. Martedì 1/12 sera: repository privato insieme.

## Decisioni di Paolo aperte
Ok su G-71 (quando pronta) e sul rilascio piccolo di G-12 (versione costruita); G-58 (token, tipo Secret); G-43 (guardare in Kit i destinatari della bozza di prova, poi Ok sul commit); avvisi di GitHub al 90% e 100% (Settings, Billing); elenco delle grandi testate di G-46; G-16; G-61 dopo le tre prove alle 7:00; G-49 intorno al 7/12; l'ok all'edizione di prova rifatta. Deciso il 28/11: carta approvata; G-51 approvata e rischio delle quote gratuite accettato; G-12 niente carta di credito; G-46 sì ai perché della scommessa (se migliora l'esperienza del lettore) e alla fonte riconoscibile sotto gli approfondimenti; la prova del 28/11 non va in linea così. Le altre richieste stanno in Tocca a te.

## Regole del ritmo
- Modello: Sonnet per controlli, stato e piccole correzioni; Opus per dati, motore, decisioni, sito; Fable solo per revisioni grandi e rare.
- Una chat per tema; se si allunga, si salva qui e nel Registro e si riparte da una nuova.
- Questo file resta di una pagina: ciò che non serve a una chat nuova va in `PROGETTO.md`.

Ultima revisione del patto (skill "gommberg"): 27/11/2026 (due ruoli, rami `g<NN>`, `rilascio` e `con-prova`: salvata da Paolo, G-39 chiusa).
