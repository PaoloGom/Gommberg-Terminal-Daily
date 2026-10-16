# Appendice - Autocorrezione, cancello ed errata (tutto automatico)

Paolo non riceve messaggi di revisione, bozze o richieste di decisione: la redazione si corregge da sola e pubblica solo ciò che è verificato. Mai PushNotification; l'unico messaggio è la consegna finale.

## 1. Ciclo di autocorrezione (fino a 3 giri)
Dopo un controllo rosso, `controlli_fatti.py` (dentro `controlli_tutti.sh`) stampa `DA_TOGLIERE:` con gli id delle schede respinte. Per ognuna, in quest'ordine:
1. se il revisore ha indicato una fonte di livello 1 che corregge il fatto: aggiorna scheda e testo;
2. altrimenti togli il fatto; se era una notizia, mettici la prima riserva verificata;
3. se era una riga di calendario o d'agenda, una cifra di termometri o approfondimenti, o una causa C: togli la riga o la frase (una causa tolta lascia il fatto senza "perché").
Poi rigenera il PDF e ripeti `controlli_tutti.sh`; il revisore ricontrolla solo le schede nuove. Esiti del revisore: "errato" = si corregge con la fonte giusta o si toglie; "non_conclusivo" = si toglie (o si attribuisce alla fonte e si ripete la verifica).

## 2. Per tipo di controllo
- **Fatti** (`controlli_fatti.py`): vedi sopra. Un dato del calendario o una chiusura non si tolgono: fonte ufficiale (`fonti.json` "ufficiali") o `"fonte_singola": true` con "secondo <testata>" nel PDF.
- **Dati** (`controlli_dati.py`): un dato respinto si sostituisce con la chiusura precedente indicando la data, o con "n.d." (massimo 8 in tutto il PDF); mai un dato dubbio. Se una serie manca: `APP_DATI.md`.
- **PDF** (`controlli.py`): pagine diverse da 6, testata sbagliata, trattini lunghi, segnaposto. Meno di 6 pagine: allunga o aggiungi un approfondimento; più di 6: accorcia testi, togli righe d'agenda o un approfondimento. Mai PageBreak in mezzo a pag. 3-5.
- **Scrittura** (`controlli_testo.py`): più di 5 righe "→": tieni solo quelle dove il perché non è ovvio. Avvisi su connettivi causali: o c'è una scheda C con "secondo <testata>", o riscrivi la frase senza causa (un meccanismo M solo come tendenza, in una frase separata dalla variazione). Sigle non spiegate: aggiungi la parentesi alla prima occorrenza.
- **Ripetizioni** (`controlli_ripetizioni.py`, bloccante): una cifra distintiva oltre 2 volte va lasciata nella sua casa (pag. 1 e la sua pagina) e tolta altrove; gli AVVISI su cifre piccole si ignorano.
- **Temi** (`controlli_temi.py`, bloccante): una voce di pag. 1 con il tema della top story si sostituisce con la riserva su un altro tema; tema fuori elenco: scegli dall'elenco chiuso di ISTRUZIONI §2.
- **Contenuti** (`controlli_contenuti.py`, bloccante): estremi = aggiungi in prima pagina (top story, In 30 secondi o una notizia) la cifra del movimento oltre il 3%, con fonte singola dichiarata se serve (indice mancante: APP_DATI §6; "nd" solo se nessuna fonte dà il dato); notizie = sostituisci la notizia-cruscotto con una riserva che porta un fatto nuovo; indice = togli la cifra dalla voce "breve"; zero col segno = "0,0%"; generalizzazione smentita = nomina l'eccezione; perché = attribuisci la causa che torna con i prezzi, oppure la lettura della redazione con i prezzi che la sostengono, "causa non chiarita" solo se tutte le ipotesi del registro falliscono; quindi = aggiungi il livello, la data o l'evento da guardare; prob = aggiungi orizzonte, metodo e fonte; record = togli la parola se nessuna scheda la dice; anomalie = scrivi il registro (passo 2c); stamattina = togli il dato fuori finestra o ripreso da ieri; moduli = togli dai punti le cifre della tabella; quadro = scrivi `C["quadro"]`; rari = cita in prima pagina il movimento più raro con la sua misura storica ("il rialzo più forte dal..."); aperture = scrivi il registro delle aperture (§2) o il motivo se la top story non concorda con la maggioranza.
- **Riempimento** (render): un modulo sotto l'80% esce con ERRORE; aggiungi punti, righe o una lettura verificati (o cambia stampo, es. senza grafico); solo dopo quel tentativo, se non ci sono fatti verificati, rilancia con `GTD_RIEMPIMENTO_OK=1`.
- **Layout** (anteprima): sovrapposizioni o pagine semivuote: accorcia o riduci righe e rigenera.

## 3. Minimi
- Notizie 6-8 (la griglia regge 6); se le verificate sono meno di 6, la sezione esce con quelle che ci sono.
- Calendario e agenda: almeno le righe verificate.
- Un approfondimento senza fatti verificati si sostituisce con un altro tema (dati di mercato o anomalia del giorno, che non richiedono schede web), mai con "nessuna novità".
- La top story è sempre un fatto confermato: se cade, diventa top story la notizia confermata più importante.

## 4. Dopo 3 giri
Togli tutto ciò che è ancora rosso e pubblica il resto. Non si pubblica solo se manca il minimo vitale (repository o API dei dati irraggiungibili, PDF impossibile): nessuna edizione oggi, una riga nel messaggio finale.

## 5. Registro
Tutte le schede con l'esito della verifica (anche le scartate, con `"scartata": true`) restano in `/home/claude/lavoro/fatti.json`, che `pubblica.sh` copia in `redazione/fatti/AAAA-MM-GG.json`: è la traccia per gli errata, non si mostra a Paolo.

## 6. Errata corrige
Ogni mattina, prima di scrivere, confronta i fatti dell'edizione precedente (`redazione/fatti/<data>.json`, lo indica `prepara.sh`) con le notizie di oggi. Se uno si è rivelato sbagliato (smentita, dato rivisto, fonte che corregge): paragrafo "Errata corrige" a pag. 6 sotto le Fonti (edizione, frase sbagliata, frase corretta, fonte) e campo `errata` in `voce.json` (finisce in `edizioni.json`). I PDF già pubblicati non si modificano.
