# Pagella di scrittura - prima lettura (24/11/2026, G-59 passo 1)

Nessuna modifica al motore: qui stanno solo gli strumenti e i risultati della prima lettura, per il banco del 25/11.
Pagina per Paolo: https://claude.ai/artifact/TMpJPSjh716NxHyWyRRL51

## Che cosa c'è
- `estrai.py`, `rendi.py`: leggono il dizionario C di un `edizione.py` senza eseguirlo e lo rendono come testo che il lettore legge (nessun numero di edizione, nessun indizio su come è stata scritta).
- `testi/`: le dieci edizioni rese così. `e-2026-11-16` ... `e-2026-11-24` = #026 ... #032; `prova1` = ramo `prova-2026-11-23-prima`; `prova2` = seconda prova (commit 7d53799, salvata anche sul ramo `prova-2026-11-23-seconda`); `prova3` = ramo `prova` (terza prova del 22/11).
- `seconda-prova-edizione.py`: copia del sorgente della seconda prova, che prima stava solo in un commit senza ramo.
- `ISTRUZIONI_LETTORE.md`: la pagella (sette voci fisse, due metà più la varietà) e la forma del giudizio. È la versione 1.
- `sigle.json`: quale sigla aveva ogni edizione per ogni lettore. `giudizi/`: i quattro giudizi come consegnati (g1 e g2 Fable, g3 Opus, g4 Sonnet). `giudizi_decodificati.json`: gli stessi con i nomi veri.
- `conta.py`, `conteggi.json`: conteggi indicativi (formule, aperture, forme dei titoli, 5-grammi condivisi) sulle dieci edizioni.
- `aggrega.py`: classifiche, medie, verifica alla lettera delle citazioni.

Gli script hanno i percorsi della sessione in cui sono nati (`/home/claude/pagella`): chi li riusa li adatta.

## Che cosa è uscito
- Accordo con Paolo su quattro confronti su cinque: seconda prova meglio della prima (4 lettori su 4), #030 meglio della #026 (4 su 4), la causa sull'oro della #031 che va contro i prezzi (trovata da 4 su 4), i difetti della prima prova (stessa frase su ACWI citata da Paolo). Disaccordo sulla #032: per i lettori è seconda su dieci, per Paolo non è scritta bene.
- Posizione media (1 = migliore): seconda prova 1,8; #032 3,0; #028 3,5; #030 4,0; prima prova 5,5; terza prova 6,0; #029 6,2; #026 8,0; #027 8,2; #031 8,8.
- Le voci più basse sono cause e varietà, non la prosa.
- Rumore: correlazione tra le classifiche dei lettori da 0,37 a 0,76; reggono solo gli estremi. Un lettore solo non basta.
- Varianza: seconda prova, terza prova e #031 (stesso giorno, regole quasi uguali) stanno a 1,8, 6,0 e 8,8.
- Costo: circa 680 mila token per quattro lettori su dieci edizioni.

## Aggiunta delle 19:30: gli errori di frase
Paolo, 24/11 ore 19:05: la #032 era buona ma con errori grossolani ("vendere le sue macchine": Nvidia non vende macchine; "un solo comunicato ha ricomprato gran parte di un calo": non è italiano), più altri errori di grammatica; in generale lo disturba la ripetizione tra un'edizione e l'altra.
I lettori della pagella non pesano la frase sbagliata (uno aveva messo la frase del comunicato tra i punti forti). Seconda lettura da correttore di bozze, senza suggerimenti, su #031 (ED-Y) e #032 (ED-X): `bozze/B-fable.json` trova 8 e 12 frasi grossolane e tutte e due quelle di Paolo (le macchine classificate minori: la gravità va tarata sui suoi casi); `bozze/A-sonnet.json` ne trova 2 e 3. Le istruzioni del correttore: frase sbagliata = parola che nomina la cosa sbagliata, soggetto che non può fare il verbo, grammatica, calco, frase che non si capisce; niente gusti di stile.
Ne segue: la pagella ha due strumenti (voto dei lettori e conto delle frasi sbagliate, con un pavimento); variante per il banco: rilettura finale fatta da un modello più forte, al posto di quella di oggi (tocca il confine "solo Sonnet" della carta: decide Paolo dopo i numeri).
