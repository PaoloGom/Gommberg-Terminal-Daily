# G-42 - Il giornale si ripete da un giorno all'altro? Misura del 25/11/2026

Edizioni misurate: tutte quelle con i sorgenti, #026-#033.
- **Prima** delle tre correzioni (G-07, G-36, G-47 entrate il 22/11): #026 (16/11), #027 (17/11), #028 (18/11), #029 (19/11), #030 (20/11) - 9.191 parole di prosa.
- **Dopo**: #031 (23/11), #032 (24/11), #033 (25/11) - 5.667 parole di prosa.

Il testo misurato è quello che il lettore legge: il dizionario C di ogni `edizione.py` con le correzioni del desk applicate come le applica il modello (solo sui campi rimasti come il desk li ha letti), senza tabelle, agenda, fonti, etichette, parole del glossario e riga AI. Nessuna modifica al repository.

Avvertenza sul campione: tre edizioni dopo il 22/11 sono poche. Le differenze sotto il 30% tra prima e dopo vanno lette come "nessun cambiamento", non come peggioramento o miglioramento.

## In breve

**Conclusione: (c).** Il problema non sta nelle sequenze di parole ma nei temi e nelle tesi, e va curato a monte, nella scaletta. Le tre correzioni hanno colpito esattamente le forme che nominavano. Il vizio però si è spostato sulla forma vicina, e le tesi e le spiegazioni continuano a tornare come prima. Le sequenze copiate alla lettera dalle edizioni precedenti sono poche (circa il 4% della prosa) e restano stabili. Più della metà sono fatti ancora in corso, che è giusto ripetere.

| Misura | Prima (#026-#030) | Dopo (#031-#033) | Tipo di numero |
|---|---|---|---|
| 1. Parole in sequenze riprese dalla pagina modello in vigore, ogni 1.000 | 26,1 | 15,9 | esatto |
| 2. Parole in sequenze riprese dalle 5 edizioni precedenti, ogni 1.000 | 36,4 | 41,5 | esatto (soglia da 5 parole) |
| 2b. Parole in sequenze riprese dalla vigilia, ogni 1.000 | 16,1 | 15,0 | esatto |
| 3. Titoli nella forma "A pesa più di B" o "A, non B" | 2 su 28 | 4 su 17 | esatto (conteggio a mano) |
| 4a. Testi aperti da una domanda | 10 su 23 (43%) | 5 su 14 (36%) | esatto |
| 4b. Testi aperti da un paradosso (domanda o affermazione: "succede X, eppure Y") | 8 su 23 (35%) | 11 su 14 (79%) | indicativo (lettura mia) |
| 5. Approfondimenti che riprendono una tesi già sostenuta nelle 5 edizioni prima | 11 su 19 (58%, #027-#030) | 9 su 14 (64%) | indicativo (lettura mia) |
| 6. "per noi" ogni 1.000 parole | 4,57 | 0,35 | esatto |
| 6. "a nostro avviso" ogni 1.000 parole | 0,00 | 2,47 | esatto |

## Come è stato verificato il lavoro dell'agente precedente

- `estrai.py` e `carica.py` (legge il dizionario C senza eseguirlo e applica `desk_ok.json`): verificati. Per #033 entrano 26 correzioni del desk su 31. Le 5 escluse riguardano campi che chi scrive ha cambiato dopo la lettura del desk (per esempio `top.dek`), e il PDF uscito lo conferma. Lo stesso comportamento del modello.
- `modello_vecchio.py` è il modello al commit ab8f03e (in vigore dal 14 al 21/11). `modello_nuovo.py` è identico a `redazione/edizione_modello_v6.py` di oggi (in vigore dal 22/11). Verificato con git.
- `pdftxt/`: rigenerato da `pdf/*.pdf` con pdftotext, identico byte per byte.
- `misura.py`: rilanciato. Le misure 1, 3, 4 e 6 sono riprese da qui. La sua misura 2 aveva un difetto: per #026-#030 la finestra delle 5 edizioni precedenti era tronca, perché i sorgenti partono da #026. L'ho sostituita con `misura2.py` (sotto).
- `pdf5.py`: rilanciato e scartato come misura principale. Sul PDF contano anche formule fisse nate da poco (la riga AI, le regole della scommessa, le note dei grafici), che fanno salire il conteggio delle ultime edizioni senza che sia una ripetizione vera (per #033 dà 68 sequenze in comune con la vigilia, quasi tutte di questo tipo).
- `meccanismi.py`: rilanciato. È la base della misura 5, che poi ho letto e completato a mano.

Script di questa misura, tutti in `/home/claude/out/g42/`: `misura.py` (1, 3, 4, 6, scrive `risultati.json`), `misura2.py` (2, scrive `risultati_m2.json`; con l'argomento `tutti` elenca ogni tratto ripreso), `meccanismi.py` (5).

## 1. Sequenze di 5 parole condivise con la pagina modello

Si conta un gruppo di 5 parole consecutive che contiene almeno 2 parole piene. Ogni edizione si confronta con il modello in vigore il giorno in cui è uscita.

| Ed. | Data | Gruppi propri | Con il modello in vigore | Tratti | Parole nei tratti |
|---|---|---|---|---|---|
| #026 | 16/11 | 1.458 | 20 | 8 | 54 |
| #027 | 17/11 | 1.534 | 19 | 6 | 43 |
| #028 | 18/11 | 1.384 | 18 | 6 | 43 |
| #029 | 19/11 | 1.483 | 39 | 10 | 79 |
| #030 | 20/11 | 1.472 | 9 | 3 | 21 |
| #031 | 23/11 | 1.473 | 7 | 4 | 23 |
| #032 | 24/11 | 1.602 | 19 | 5 | 40 |
| #033 | 25/11 | 1.391 | 11 | 4 | 27 |

Media per edizione: 21 gruppi prima, 12,3 dopo. Per ogni 1.000 parole: 26,1 prima, 15,9 dopo. Numeri esatti. Il calo è reale ma in parte meccanico, perché il 21/11 il modello è stato riscritto.

Quello che resta è significativo. Dal modello arrivano le **glosse fisse**, che chi scrive copia e che quindi tornano ogni giorno:
- 24/11, #032, Treasury: "il prezzo sale e il rendimento, che si muove al contrario, scende" (10 parole, dal modello nuovo; la stessa frase c'era già il 18/11 nella #028, dal modello vecchio).
- 24/11, #032, oro: "il VIX, l'indice che misura la paura a Wall Street" (9 parole).
- 25/11, #033, petrolio: "il greggio diventa benzina e gasolio in poche settimane" (9 parole; c'era già il 18/11 nella #028).
- "il Russell 2000, l'indice delle società più piccole": nella lettura di pag. 5 in 6 edizioni su 8 (16, 17, 20, 23, 24 e 25/11). È così frequente che il filtro automatico dei falsi echi lo scambia per una formula d'impaginazione: va invece contato come ripetizione vera.

## 2. Sequenze di 5 parole condivise con le 5 edizioni precedenti

Da una parte la prosa dell'edizione dal sorgente. Dall'altra, per ognuna delle 5 edizioni precedenti, il testo intero del suo PDF, perché #021-#025 non hanno sorgenti. Sono esclusi i falsi echi: le formule presenti in almeno 6 edizioni su 8 ("Numeri, temi aperti e calendario"; la glossa del Russell, che conto però a parte al punto 1) e le sequenze che vengono dal modello (già contate al punto 1). Le righe di tabelle, agenda, indice e la riga AI non entrano dal lato dell'edizione misurata.

| Ed. | Periodo | Vigilia | 2 ed. prima | 3 ed. prima | 4 ed. prima | 5 ed. prima | Unione delle 5 | Parole nei tratti | Ogni 1.000 | Con la sola vigilia, ogni 1.000 |
|---|---|---|---|---|---|---|---|---|---|---|
| #026 | prima | 5 | 4 | 7 | 2 | 1 | 14 | 55 | 30,6 | 16,7 |
| #027 | prima | 8 | 3 | 10 | 7 | 3 | 19 | 76 | 39,4 | 14,5 |
| #028 | prima | 4 | 3 | 2 | 3 | 2 | 13 | 58 | 33,6 | 9,3 |
| #029 | prima | 9 | 4 | 3 | 2 | 2 | 11 | 42 | 22,2 | 16,9 |
| #030 | prima | 9 | 0 | 9 | 1 | 6 | 24 | 104 | 56,2 | 22,7 |
| #031 | dopo | 0 | 5 | 13 | 11 | 2 | 26 | 78 | 41,0 | 0,0 |
| #032 | dopo | 4 | 1 | 0 | 1 | 5 | 8 | 41 | 20,6 | 8,0 |
| #033 | dopo | 27 | 7 | 1 | 2 | 3 | 39 | 116 | 65,5 | 39,0 |

Totale per ogni 1.000 parole: **36,4 prima, 41,5 dopo**. Con la sola vigilia: 16,1 prima, 15,0 dopo. Numeri esatti alla soglia di 5 parole. Le correzioni non hanno cambiato nulla, ma il fenomeno è piccolo: circa 4 parole su 100.

Letti uno per uno (elenco completo con `python3 misura2.py tutti`), i tratti ripresi sono di tre tipi. Questa ripartizione è indicativa:
- **Fatti ancora in corso**, giusto ripeterli. Dopo il 22/11 sono circa 145 parole su 235. Per esempio il 25/11: "fondo di stabilizzazione del governo di Seul, nessuna novità verificata dal 23/11" (riquadro Fermi, 13 parole, uguale al 24/11); "la probabilità di un rialzo a dicembre"; "l'offerta di Intesa Sanpaolo su Mps".
- **Spiegazioni rifatte con le stesse parole**: circa 67 parole dopo (11,8 ogni 1.000) contro 69 prima (7,5 ogni 1.000). Per esempio il 23/11, #031: "i Treasury: il loro prezzo sale e il rendimento scende" (già il 17 e il 18/11); il 23/11: "il rendimento a 2 anni segue le attese sui tassi" (già il 17, il 18 e il 19/11); il 25/11: "un surplus di circa 2 milioni di barili al giorno" (uguale al 24/11).
- **Formule**: per esempio "i chip americani della sera prima" e "da qui a venerdì".

Questa misura guarda solo le parole identiche. La ripetizione più grande, quella delle tesi riscritte ogni giorno con parole diverse, le sfugge quasi tutta (punto 5).

## 3. Titoli, titoli d'indice e catenacci

Titoli uguali alla lettera: solo il titolo d'indice "perde meno di Wall Street", il 17/11 (#027) e il 20/11 (#030), già segnalato nella G-36. Dopo il 22/11 nessun titolo uguale (esatto). Su lessico (parole portanti in comune) le coppie simili sono 18, quasi tutte la stessa notizia seguita per più giorni (Anthropic, Trump in Cina), cosa giusta.

Il problema vero è lo **schema del titolo** (conteggio a mano su titoli di apertura e degli approfondimenti):
- **"A pesa più di B" / "A, non B"**: 16/11 "Borse su e rifugi giù: per noi la Fed pesa più della paura"; 20/11 "Per il petrolio i barili in arrivo pesano più dei rischi a Riyadh"; 23/11 "L'oro non ripara dal panico perché dollaro e tassi pesano più della paura"; 24/11, nella stessa edizione, "Il rimbalzo di Nvidia: si vendeva per sfiducia, non per i conti", "Il petrolio scende guardando al surplus, non alla guerra" e "L'oro è sceso e risalito con le borse, non contro di loro". Sono 2 titoli su 28 prima e 4 su 17 dopo; la #032 ne ha 3 su 6.
- **Stessa tesi, quasi la stessa frase**: 17/11 "Con la paura i Treasury tornano rifugio, anche con la Fed pronta ad alzare" e 23/11 "Con la Fed in rialzo i Treasury restano un rifugio e i rendimenti scendono".
- **Stesso verbo, stesso soggetto, a due giorni**: 23/11 "A Milano pesano chip e banche, e l'Europa tocca il minimo da maggio" e 25/11 "Le vendite sui chip pesano su Milano, che perde quasi il 2%".
- **Notizia uguale due giorni di fila**: 24/11 "Gli operatori scommettono ancora sul rialzo Fed di dicembre" e 25/11 "Il mercato dà quasi per certo il rialzo della Fed a dicembre".
- **Stessa cifra-titolo**: 17/11 indice "il Brent perde un quinto in tre settimane", 20/11 grafico "il Brent perde un quinto", 25/11 titolo "Il petrolio perde un quinto in un mese" con indice "il barile perde un quinto".
- **Il verbo "pesare" nei titoli**: 7 volte in 5 edizioni prima, 5 volte in 3 edizioni dopo.

## 4. Come aprono i testi (prima frase degli approfondimenti)

| | #026 | #027 | #028 | #029 | #030 | #031 | #032 | #033 |
|---|---|---|---|---|---|---|---|---|
| Approfondimenti | 4 | 5 | 5 | 4 | 5 | 4 | 5 | 5 |
| Aperti da una domanda (esatto) | 2 | 0 | 1 | 2 | 5 | 1 | 2 | 2 |
| Aperti da un paradosso, domanda o affermazione (indicativo) | 3 | 0 | 1 | 1 | 3 | 3 | 5 | 3 |
| Stessa apertura della vigilia nello stesso tema (indicativo) | - | 0 | 0 | 0 | 1 | 1 | 1 | 1 |

La regola G-47 ("al massimo due aperture con la domanda") è rispettata: le domande scendono da 10 su 23 a 5 su 14. Ma la stessa mossa è passata alla forma affermativa: l'apertura a paradosso ("succede X, eppure Y") sale da 8 su 23 a 11 su 14, e la #032 apre così tutti e 5 gli approfondimenti. Esempi veri:
- 20/11, #030: "Come mai l'oro, il bene rifugio per eccellenza, scende in un giorno di paura?" e il 24/11, #032: "L'oro, il rifugio per eccellenza, è caduto proprio nella settimana della paura." È la stessa frase, senza il punto di domanda.
- 23/11, #031: "L'oro cade anche quando c'è paura, e la ragione è che non è solo un rifugio..." Il tema oro apre con "L'oro..." il 17, il 19, il 23 e il 24/11.
- 24/11, #032: "Le petroliere continuano a essere colpite e il greggio scende lo stesso." e il 25/11, #033: "Perché il petrolio scende mentre le borse hanno paura?" (già il 20/11: "Perché i missili non bastano?").
- 24/11, #032, stesso giorno: "Se i conti di Nvidia non sono cambiati in undici giorni, perché il titolo ha perso circa un quarto...?" e "Se la paura cala, perché il 10 anni non sale?"

Le aperture fisse di pag. 5: la lettura comincia con "Il Russell 2000, l'indice delle società più piccole" il 20, il 24 e il 25/11 (esatto).

## 5. Tesi e spiegazioni che tornano (lettura, con data e frase)

**Tesi che tornano su più giorni**
- **"L'oro non fa da rifugio perché pesano Fed e dollaro"**: in 7 edizioni su 8 (tutte tranne la #028). Ha un approfondimento dedicato in 6: 16/11 "oro e Treasury non proteggono"; 17/11 "Con il dollaro forte l'oro non fa da rifugio"; 19/11 "Neanche le tensioni nel Golfo fermano l'oro: pesa il dollaro"; 20/11 "Come mai l'oro, il bene rifugio per eccellenza, scende in un giorno di paura?"; **23/11** "L'oro non ripara dal panico perché dollaro e tassi pesano più della paura"; **24/11** "L'oro, il rifugio per eccellenza, è caduto proprio nella settimana della paura". Torna ancora il 25/11 nella lettura: "il greggio scende per ragioni sue e non perché il mondo cerchi rifugio". È il caso più chiaro, e continua dopo le correzioni.
- **"Il petrolio guarda all'offerta in eccesso, non alla guerra"**: in 6 edizioni su 8. 17/11 "il mercato guarda all'offerta in eccesso più che agli attacchi alle navi"; 19/11 "Le previsioni di offerta in eccesso pesano sul Brent"; 20/11 "Missili su Riyadh e mine a Hormuz, ma il petrolio guarda all'eccesso di offerta"; **24/11** "il greggio scende perché il mercato guarda al surplus, non alla guerra"; **25/11** "un surplus di circa 2 milioni di barili al giorno" (stessa cifra e stessa fonte del 24/11).
- **"L'Europa si muove diversamente da Wall Street perché ha meno AI nell'indice"**: 16/11 "Europa e Milano battono Wall Street"; 17/11 "Con meno AI nell'indice l'Europa perde meno di Wall Street"; 18/11 "L'Europa perde il doppio di Wall Street"; 20/11 "L'Europa regge perché ha pochi titoli AI". Dopo il 22/11 la tesi si sposta su Milano ma la spiegazione è la stessa: 23/11 "il motivo sta nella composizione"; 25/11 "Le vendite sui chip pesano su Milano".
- **"La Fed pesa più della paura"**: 16/11 nel titolo; 20/11 nel catenaccio "per noi pesa più la Fed... che il giudizio sulle singole società"; **24/11** "Le borse rimbalzano ma il 10 anni resta fermo: pesa la Fed".
- **"Nvidia si vende per sfiducia, non per i conti"**: **23/11** "Le vendite sui chip passano dai prezzi alla fiducia" e **24/11** "si vendeva per sfiducia, non per i conti".

**Meccanismi rispiegati per intero in edizioni vicine** (ricerca con `meccanismi.py`, poi lettura)

| Meccanismo | Edizioni in cui è rispiegato | Esempio dopo il 22/11 |
|---|---|---|
| Sale il prezzo del titolo di Stato, scende il rendimento | 17, 18, 23 (due volte), 24/11 | 24/11: "Chi ha paura compra titoli di Stato americani per mettere i soldi al sicuro: il prezzo sale e il rendimento, che si muove al contrario, scende." |
| L'oro non paga interessi | 16, 17, 19, 20, 23/11 | 23/11: "tenere un metallo che non rende interessi costa di più" |
| Un'azione vale gli utili futuri | 17, 18, 19, 20 (quattro volte), 25/11 (tre volte) | 25/11: "il prezzo di un titolo sconta oggi i margini di domani" |
| Un indice pesa le società per dimensione / composizione | 16, 17, 18, 20, 23, 24, 25/11 | 25/11: "Un indice è una media dei titoli..." |
| Il 2 anni segue le attese sulla Fed | 17, 18, 19, 23/11 | 23/11: "Il rendimento a 2 anni segue di più le attese sui tassi della banca centrale..." |
| Russell 2000 e chi ha più debiti | 16, 20, 24/11 (glossa dell'indice in 6 edizioni su 8) | 24/11: "di solito chi ha più debiti recupera più piano quando i tassi restano alti" |

**Quanto è grande.** Approfondimenti che riprendono una tesi già sostenuta in una delle 5 edizioni precedenti (lettura mia, indicativa): #027 3 su 5, #028 3 su 5, #029 2 su 4, #030 3 su 5 (prima: 11 su 19, 58%); #031 3 su 4, #032 4 su 5, #033 2 su 5 (dopo: 9 su 14, 64%). La #026 non è contata perché non ho letto i PDF #021-#025 a livello di tesi. In pratica più di metà delle pagine 2-4 ridice una tesi della settimana, e le correzioni non l'hanno toccato.

## 6. Parole e formule ricorrenti (conteggio esatto, per edizione e ogni 1.000 parole)

| Formula | #026 | #027 | #028 | #029 | #030 | #031 | #032 | #033 | Prima, ogni 1.000 | Dopo, ogni 1.000 |
|---|---|---|---|---|---|---|---|---|---|---|
| per noi | 14 | 6 | 4 | 8 | 10 | 0 | 1 | 1 | 4,57 | 0,35 |
| a nostro avviso | 0 | 0 | 0 | 0 | 0 | 6 | 5 | 3 | 0,00 | 2,47 |
| di solito | 8 | 4 | 6 | 16 | 10 | 5 | 4 | 4 | 4,79 | 2,29 |
| tende / tendono a | 0 | 1 | 3 | 0 | 0 | 6 | 3 | 2 | 0,44 | 1,94 |
| pesa / pesano / pesare | 8 | 7 | 10 | 5 | 8 | 11 | 7 | 5 | 4,13 | 4,06 |
| paura | 9 | 9 | 3 | 3 | 5 | 13 | 8 | 2 | 3,16 | 4,06 |
| rifugio / riparo | 4 | 11 | 5 | 3 | 2 | 8 | 3 | 1 | 2,72 | 2,12 |
| "A, non B" / "non per..., ma" | 1 | 0 | 0 | 0 | 0 | 0 | 6 | 0 | 0,11 | 1,06 |
| anche quando / proprio / lo stesso / eppure | 1 | 1 | 0 | 1 | 2 | 2 | 3 | 1 | 0,54 | 1,06 |
| frasi con "?" | 2 | 0 | 1 | 2 | 5 | 1 | 2 | 2 | 1,09 | 0,88 |

È lo stesso andamento del punto 4. La formula vietata sparisce ("per noi" da 4,57 a 0,35) e al suo posto arriva la gemella ("a nostro avviso" da 0 a 2,47): la voce in prima persona plurale si ferma intorno ai 3 casi ogni 1.000 parole. Allo stesso modo "di solito" cede il posto a "tende a" (il totale dei due passa da 5,2 a 4,2). "Pesa", la parola che un lettore quotidiano nota di più, non è cambiata (4,1 ogni 1.000, circa 7-8 volte per edizione). "Paura" sale (4,1 ogni 1.000) perché accompagna le tesi ripetute su oro, Treasury e petrolio.

## Conclusione

**(c) Il problema non è di sequenze ma di temi e tesi, e si cura a monte, nella scaletta.**

1. Le tre correzioni funzionano sul bersaglio preciso: "per noi" -92%, domande in apertura da 43% a 36%, sequenze dal modello -40%. Ma ogni regola sulla forma ha fatto nascere la forma gemella: "a nostro avviso", "tende a", le aperture a paradosso senza punto di domanda (79%), i titoli "A, non B". È la prova che le regole sulla singola forma non bastano e non vanno moltiplicate.
2. Le parole copiate alla lettera dalle 5 edizioni precedenti sono circa il 4% della prosa, invariate dopo il 22/11 (da 36 a 42 ogni 1.000), e più della metà sono fatti in corso. Un controllo degli echi a 5 parole sulle ultime 5 edizioni prenderebbe poche frasi, molte delle quali da non toccare.
3. Quello che il direttore sente come ripetizione è la tesi: l'oro che non fa da rifugio in 7 edizioni su 8 (6 con un approfondimento dedicato, anche il 23 e il 24/11), il petrolio che guarda al surplus e non alla guerra in 6 su 8, l'indice composto diversamente in 7 su 8, cinque meccanismi rispiegati da capo ogni due o tre giorni. Più di metà degli approfondimenti riprende una tesi della settimana, prima come dopo. Il desk di oggi non lo può vedere perché legge una sola edizione, e un controllo a sequenze non lo vedrebbe comunque, perché le parole cambiano ogni giorno.

**Che cosa serve, a monte e non come controllo degli echi.** Chi fa la scaletta (e poi il desk) deve ricevere una memoria breve delle ultime 5 edizioni, scritta per temi e non per testo:
- per ogni approfondimento: data, tema (chiave), titolo, tesi in una riga, meccanismo spiegato, prima frase;
- le glosse già date (che cos'è il Russell 2000, che cos'è il VIX, perché prezzo e rendimento vanno al contrario...).

Con una regola sola, che vale anche per il prossimo vizio: **una tesi o un meccanismo già usati nelle ultime 5 edizioni tornano solo se c'è un fatto nuovo che li cambia. In quel caso si richiamano in una riga ("come scritto lunedì") e non si rispiegano. Se il fatto nuovo non c'è, il tema esce dalla scaletta o cambia angolo.** Il desk verifica questa regola sulla memoria, non sulle sequenze.

La pagina modello non deve per forza vedersi intera: le sue glosse vanno nella memoria come "già spiegate", così smettono di essere copiate ogni giorno.

Ordine di grandezza del beneficio atteso (indicativo): fino a 2 o 3 approfondimenti su 5 al giorno cambierebbero angolo o si accorcerebbero, contro le circa 20 parole al giorno che toglierebbe un controllo degli echi.

## Che cosa è esatto e che cosa è indicativo

- **Esatti** (contati dagli script su tutte le 8 edizioni): misure 1, 2 e 6, le domande in apertura (4a), i titoli uguali alla lettera.
- **Indicativi** (mia lettura): le aperture a paradosso (4b), la stessa apertura della vigilia, la ripartizione dei tratti ripresi in fatti, spiegazioni e formule, gli approfondimenti con una tesi già sostenuta (5), lo schema dei titoli (3).
- **Limiti**: solo 3 edizioni dopo il 22/11; per #021-#025 c'è solo il PDF, quindi la misura 2 su quelle edizioni usa il testo del PDF e i gruppi spezzati dall'impaginazione si perdono; la soglia di 5 parole non vede le riformulazioni.
