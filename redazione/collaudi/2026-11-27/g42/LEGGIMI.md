# G-42 - La memoria delle ultime edizioni, prove sulle edizioni vere (27/11/2026)

Che cosa avrebbe visto chi scriveva, ogni mattina dal 16 al 27/11, se la memoria ci fosse già stata. Tutto rifatto dal codice
con `python3 redazione/collaudi/2026-11-27/g42/prove.py`: zero token, nessun modello.

- `memoria_AAAA-MM-GG.txt`: la memoria che `prepara.sh` scrive in `memoria_edizioni.txt` quella mattina (le 5 edizioni prima).
- `desk_AAAA-MM-GG.txt`: che cosa il desk avrebbe visto segnalato sui pezzi usciti quel giorno (in fondo a `desk_incarico.json`).

## Quanto pesa
| Giorno | Caratteri della memoria | Pezzi in memoria | Pezzi del giorno segnalati al desk |
|---|---|---|---|
| 16/11 | 91 (nessun sorgente prima) | 0 | 0 su 4 |
| 17/11 | 1.526 | 4 | 3 su 5 |
| 18/11 | 3.546 | 9 | 4 su 5 |
| 19/11 | 5.876 | 14 | 4 su 4 |
| 20/11 | 5.551 | 18 | 3 su 5 |
| 23/11 | 5.829 | 23 | 4 su 4 |
| 24/11 | 5.731 | 23 | 5 su 5 |
| 25/11 | 5.997 | 23 | 5 su 5 |
| 26/11 | 6.271 | 23 | 4 su 5 |
| 27/11 | 5.088 | 24 | 3 su 4 |

Tetto di 6.500 caratteri dentro `testo_memoria` (TETTO): sopra, le edizioni più vecchie passano "in breve" (prima
pagina, titoli e meccanismi, senza tesi né attacco), e se non basta esce la più vecchia. A regime le 5 edizioni ci
stanno con le 2 più recenti intere. Il 30/11: 6.089 caratteri. Per ogni edizione anche la prima pagina, l'apertura di
pag. 5 e i titoli d'indice.

## Dopo il collaudo indipendente (27/11, secondo giro)
- Tesi: presa intera dalla scaletta archiviata (`redazione/fatti/AAAA-MM-GG.json`, registro "scaletta"), dove c'è per
  tutte le edizioni dal 16/11; senza scaletta, la frase che dichiara la lettura nel Perché o nel testo, con la frase
  prima se comincia con un rimando. Sulle 12 controllate (24/11, 25/11, Seul e oro del 27/11): 12 giuste; nessun pezzo
  senza tesi dal 16/11.
- Titolo vicino: contano solo parole che non sono il soggetto del tema, un verbo di movimento o un'unità; due parole in
  comune, o una nella stessa famiglia di tema. Sulle edizioni 20-27/11: 8 segnalazioni con i titoli usciti (6 giuste,
  sbagliate 26/11 crescita e 27/11 pochi scambi); 9 con i titoli prima del desk (3 sbagliate).
- Temi in famiglie dal codice (Oro, Petrolio, Dazi, Tassi e Fed, Europa e Italia, Corea e Asia, Chip e AI).
- Meccanismi: la glossa del VIX e lo spread dato come cifra non contano più; ritrovati Seul pesata sui chip (M17) e il
  dato d'inflazione che muove il breve (M05). Resta: "il 2 anni segue la banca centrale" detto di passaggio conta come
  spiegato (M26), perché a parole non si distingue da una spiegazione breve.

## I casi della misura del 25/11
**L'oro che non fa da rifugio (7 edizioni su 8).** Il 23/11 la memoria mostrava l'oro già uscito il 17 ("Con il dollaro forte
l'oro non fa da rifugio", tesi "pesano tassi alti e dollaro forte: di solito un metallo che non paga interessi..."), il 19
("Neanche le tensioni nel Golfo fermano l'oro: pesa il dollaro") e il 20/11, con "M23 Oro e tassi reali (16, 17, 19, 20/11)"
tra i meccanismi spiegati più volte, e due attacchi del 17 e del 19 che aprono con "L'oro non paga interessi". Il pezzo uscito
il 23/11 ("L'oro non ripara dal panico perché dollaro e tassi pesano più della paura") era la stessa tesi senza un fatto nuovo
che la cambiasse: con la regola di §3.3 cambiava angolo o usciva. Il desk lo avrebbe visto segnalato: M23 già spiegato il 16,
17, 19, 20/11; titolo vicino al 17, 19 e 20/11; attacco sull'oro come il 17 e il 19/11. Il 24/11 l'oro torna ancora
e la memoria lo mostra il 17, 19, 20 e 23/11.

**Il petrolio che guarda al surplus (6 su 8).** Il 24/11 ("Il petrolio scende guardando al surplus, non alla guerra") la memoria
aveva il petrolio il 17, 18 e 20/11 con M11 Shock d'offerta o di domanda; il desk avrebbe visto "M11 già spiegato il 17, 18,
20/11" e titoli vicini al 17, 18 e 20/11. Il 25/11 ("Il petrolio perde un quinto in un mese...") di nuovo: M11 il 18, 20, 24/11 e
titolo vicino al 20 e al 24/11.

**"Il prezzo sale e il rendimento scende" (M01, rispiegato quattro volte).** Riconosciuto nel testo il 17, 18, 23 e 24/11 anche
dove non era dichiarato in `C["meccanismi"]` (17 e 18/11). Il 23/11 il pezzo sui Treasury lo avrebbe visto segnalato "già
spiegato il 17/11, 18/11", il 24/11 "il 17, 18, 23/11", il 26/11 "il 23, 24/11": tre occasioni per richiamarlo in mezza frase.

**L'Europa che si muove per la composizione dell'indice (7 su 8).** M16 Concentrazione degli indici è tra i meccanismi spiegati più
volte ogni giorno dal 20/11; i pezzi europei del 23, 24, 25 e 27/11 hanno titolo vicino a 3-4 pezzi della memoria.

## Limiti da guardare
- I meccanismi si riconoscono con combinazioni di parole (`SEGNI` in `memoria.py`), tarate su queste dieci edizioni: un
  passaggio spiegato con parole nuove può sfuggire, e un meccanismo citato di passaggio può contare come spiegato.
- La tesi è la frase del Perché che dichiara la nostra lettura; nei pezzi che riportano la lettura di altri la tesi è il
  titolo (nella memoria "-"). Una frase dichiarata che rimanda alla precedente ("hanno prevalso le seconde") si legge male da sola.
- I "titoli vicini" contano parole in comune: un tema seguito per giorni (la stessa storia che va avanti) viene segnalato
  anche quando è giusto riprenderlo. Le segnalazioni non bloccano nulla: decide chi legge, con il fatto nuovo.

## Terzo giro (27/11): forma breve con la tesi
- Tetto 8.000 caratteri. Ordine dei tagli: prima le edizioni più vecchie perdono attacco, titolo d'indice e pag. 5 (la
  più recente li tiene), poi la tesi si taglia a parola intera intorno ai 100 caratteri, infine esce la più vecchia.
- Caratteri e forma, dal 23 al 30/11: 23/11 7.732 (5 edizioni con tesi intera, 3 con attacco); 24/11 7.909 (5, 3);
  25/11 7.686 (5, 2); 26/11 7.717 (5, 2); 27/11 7.599 (5, 1); 30/11 7.366 (5, 1). Senza tetto 8.900-9.900.
- Tesi: vale la lettura che il Perché del pezzo uscito dichiara (con la frase prima se comincia con un rimando, anche
  "quel"); la scaletta è il ripiego. Dalla scaletta restano i pezzi senza lettura dichiarata nel Perché, tra cui l'Europa
  del 25/11, dove la scaletta diverge dalla stampa: dichiarato.
- Un pezzo con il titolo non scritto come testo nel sorgente non sparisce in silenzio: la memoria lo dice in una riga.
- Titolo vicino: ritrovato il Treasury del 23/11 contro il 17/11 ("rifugio" non conta più come soggetto del tema).
  Sulle edizioni 20-27/11: 9 segnalazioni con i titoli usciti, 10 con quelli letti dal desk; sbagliate 2-3.
