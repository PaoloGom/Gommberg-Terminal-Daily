# G-49 - note sulla bozza degli auguri (proposta, non approvata)

## Che cosa ho cambiato e perché
- Apertura più corta e diretta: via "in queste prime settimane" e "senza semplificare" (frase fatta, in tensione con "spieghiamo"); detto subito che è la prima mail fuori dall'edizione e che cosa chiediamo.
- Uscite: la bozza diceva solo 25/12 e 1/1. Aggiunte le sedute con borse chiuse in parte (24/12 e 31/12), che il codice prevede e la bozza ignorava.
- Sondaggio: stessa domanda; risposte aggiornate a ciò che esiste oggi. "Guide passo passo" ora si sovrapponeva a Impara (tolta come voce autonoma, diventa "oltre a quelle di Impara"); aggiunta "Più dati e grafici, come in I numeri". Cinque risposte (massimo consentito).
- Chiusura: via "A nome della redazione ... sereno 2027" (formula), ora "Buone feste e buon 2027, dalla redazione."
- Anteprima rifatta (quasi uguale, 98 caratteri). Oggetto, firma, pulsante, nota (postilla privacy), stato e riga ok invariati.

## Date verificate
- 25/12/2026 (ven) e 01/01/2027 (ven): niente edizione. `FESTIVI` in redazione/gommberg_engine.py riga 115. Calendario controllato: sono due venerdì.
- 24/12/2026 (gio): edizione regolare, "Italia e Germania chiuse, USA chiusura anticipata"; 31/12/2026 (gio): "Italia e Germania chiuse". Da `PARZIALI` in redazione/prepara.sh (righe 72-76) e dalla regola "l'edizione esce" di redazione/APP_FESTIVI.md §2.
- 28/12 (lun): Londra chiusa (Boxing Day), nel codice ma NON citata nella mail: irrilevante per il lettore.
- 21-23/12, 28-30/12, 04-06/01: giorni di uscita normali (lun-ven non in FESTIVI). 6/1 non è in nessun elenco.
- Orario 9:45: da iscriviti.html e index.html.
- Nomi sito: "Impara" (glossario.html), "I numeri" (numeri.html), "Chi siamo", "La Gommunity", "GOMM" da index.html e STATO.md.

## Sondaggio
Domanda: "Che cosa vorresti trovare in più nel Gommberg nel 2027?"
Risposte: Più analisi su aziende e settori / Più spiegazioni sui meccanismi dei mercati, oltre a quelle di Impara / Un riepilogo della settimana il sabato / Più dati e grafici, come in I numeri / Va bene così com'è.
Ogni risposta è un link verso grazie.html (pagina "Grazie, risposta ricevuta", coerente: invita a rispondere alla mail per il perché).

## Controlli
- `dem.py salva` sulla copia: "DEM: OK" (nessun errore di formato, trattini, parole, orario di invio). Anteprima: anteprima.html, immagini anteprima-1280.png e anteprima-390.png, guardate: nulla di rotto. "[indirizzo postale]" nel piè è un segnaposto dell'anteprima locale.

## Dubbi per Paolo
1. 24/12 e 31/12: dico "Milano e Francoforte chiuse" seguendo il codice (Italia e Germania); il calendario ufficiale va riverificato a dicembre (APP_FESTIVI §3).
2. Il sabato e la riga "un riepilogo il sabato": scelta tua se tenerla (la mail stessa esce di sabato).
3. La mail dice "prima mail fuori dall'edizione": vera solo se non parte altro prima del 19/12.
4. STATO.md dice che la #033 è uscita alle 9:30, mentre sito e mail promettono le 9:45: ho tenuto 9:45 (promessa pubblica).
