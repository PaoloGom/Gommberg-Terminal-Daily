# G-46 - Rilettura sulla settimana vera 23-27/11 (#031-#035)

Primo passo della voce G-46: misura, causa e verdetto per ogni riga del "fatto" (G-06, G-08, G-07, G-03, G-04, G-44) e per i tre temi delle note "confermati sulla settimana vera". Nessun codice del motore, nessuna istruzione o controllo toccati. La riga G-36 è passata a G-59 e la coerenza delle cause è G-45: fuori da qui.

Materiale: i cinque PDF (`pdftotext`), i sorgenti in `redazione/sorgenti/2026-11-2[3-7]/`, l'archivio `redazione/fatti/` (dal 16/11 per le prove a dieci giorni), i registri in `redazione/pronostici/`, le serie in `redazione/scommessa/dati/`. Script in questa cartella, tutti in sola lettura, ognuno con il suo campione verificato a mano (detto nella sezione):

- `g06_ufficiali.py` - quali schede `ufficiale_di_fatto` riconosce come dato ufficiale, oggi e con due varianti, su 10 giorni
- `g07_parentesi.py` - tutte le parentesi del testo dei cinque PDF e il conteggio del controllo
- `g04_agenda.py` - fin dove arriva "In arrivo" nelle edizioni del primo giorno della settimana
- `fonti_approfondimenti.py` - testate e livelli della riga Fonti di ogni approfondimento
- `indiscrezioni.py` - frasi con un soggetto generico ("la stampa americana", "notizie secondo cui", "indiscrezioni")
- `agenda_chiusure.py` - righe d'agenda su chiusure e sedute corte, con l'ultima colonna

## Sintesi

| Riga | Quante volte su 5 | Verdetto | Costo |
|---|---|---|---|
| G-06 dato ufficiale nella scheda di un'altra notizia | 1 su 5 (#032, PMI dell'area euro senza comunicato); gli altri 6 dati macro e di banca centrale di prima pagina erano dichiarati U | COSTRUIRE (`autori.py`, una condizione cambiata) | XS |
| G-08 i sei perché del lunedì | 23/11: 3 su 6 senza motivo, 1 debole; 16/11: 1 su 6. Mar-ven la pagina non li riporta | CHIEDERE A PAOLO (esempio pronto) | XS |
| G-07 parentesi di fonte | 0 su 5: nessuna testata tra parentesi in 90 parentesi lette a mano | NON COSTRUIRE (già risolta da §3.5 e dalle righe Fonti) | - |
| G-03 eodhd_nd con una fonte sola | 0 su 5 (0 su 10 dal 16/11); il buco esiste, provato | COSTRUIRE piccolo, ultimo in ordine | XS |
| G-04 agenda del lunedì fino a venerdì | 1 lunedì: fino a giovedì, ma la seduta corta di venerdì è detta nella riga | NON COSTRUIRE | - |
| G-44 pag. 5 nei giorni di chiusura | pag. 5 giusta riga per riga 2 su 2; testata sovrapposta allo slogan 1 su 5 (#035, su tutte e sei le pagine); nota +1 riga solo venerdì | COSTRUIRE (motore, testata); nota NON COSTRUIRE | S |
| Nota: fonti deboli o poche negli approfondimenti | 5 approfondimenti su 23 senza una fonte di livello 1, agenzia o primaria (4 edizioni su 5, l'oro 3 volte); 8 su 23 con una o due testate | CHIEDERE A PAOLO | M |
| Nota: indiscrezione o causa senza il nome della testata | 8 frasi in 4 edizioni su 5 (4 storie) | COSTRUIRE (`controlli_testo.py`, per sostituzione) | S |
| Nota: "Sopra: ... Sotto: ..." su una chiusura | 6 righe su 9 di chiusure e sedute, in 3 edizioni su 5 (2 senza senso) | COSTRUIRE (ISTRUZIONI §1, una frase sostituita) | XS |

Ordine di valore degli interventi da costruire: (1) indiscrezioni senza testata, (2) "Sopra/Sotto" sulle chiusure, (3) G-06, (4) testata di G-44, (5) G-03.

---

## G-06 - Il dato ufficiale di prima pagina e il suo comunicato

**Misura.** Dati ufficiali (numero o decisione di un ente, dato macro, banca centrale) nelle notizie di pag. 1 delle cinque edizioni, con la loro scheda:

- #031: fiducia del Michigan 51,5 (N08, U, comunicato cercato due volte); verbali Fed (U).
- #032: **PMI composito dell'area euro 51,7 contro 51,9 atteso** (notizia 04 e tabella di pag. 4): scheda N07 senza "tipo", fonti Reuters (RTÉ) e investingLive, nessun comunicato di S&P Global/HCOB e nessuna ricerca dichiarata. È l'unico passato senza che il controllo lo chiedesse.
- #033: nessun dato macro in pag. 1 (Moody's su Mps, vedi sotto).
- #034: PCE (A03, U), Bank of Korea (B08, U), scorte EIA (C03, U), PIL tedesco (C06, U con Destatis): tutti dichiarati.
- #035: nessun dato macro.

Gravità per il lettore: bassa (il PMI era giusto), ma è un dato ufficiale pubblicato con due testate al posto del comunicato, contro ISTRUZIONI §2.

**Causa (verificata).** `autori.ufficiale_di_fatto` riconosce il dato non dichiarato in tre modi; il caso (b), "numero uscito contro le attese", parte solo se la scheda ha una cifra con unità (`_CIFRA` vuole %, pb, punti, mld...). Un indice come PMI, fiducia, ISM si scrive senza unità ("51,7 (atteso 51,9)"): `mie` è vuoto e il caso (b) non scatta. Provato su N07 del 24/11: `ufficiale_di_fatto` torna "". Inoltre la funzione guarda solo top_story e top_news, mentre ISTRUZIONI §2 dice "ovunque compaia".

Il caso d'origine della prova (inflazione giapponese dentro la scheda del Nikkei, senza attese né riga di calendario) resta fuori anche con le varianti: riconoscerlo vorrebbe un elenco di argomenti, che la funzione per scelta non usa. Lo stesso vale per decisioni senza cifre (rating di Moody's su Mps nel #033, CreditWatch di S&P su Nvidia e proposta di dazi dell'USTR nel #034, tutte in schede deep_dive o senza attese): non si costruisce.

**Verdetto: COSTRUIRE.** In `autori.py`, `ufficiale_di_fatto`: esce `if mie and _ATTESE.search(...)`, entra `if _ATTESE.search(...)` (la regex vuole già una cifra prima del confronto), e la funzione vale per ogni sezione di fatti salvo agenda, calendario, registri, cause (C), dati già U e memoria. Nessuna regola nuova: allinea il codice a §2. Prova (`g06_ufficiali.py`, 10 giorni dal 16/11): oggi 2 schede riconosciute, con la modifica 5; le 3 in più (PMI del 24/11, dati cinesi D13 del 16/11, conti di Nvidia D01 del 18/11) sono tutte dati ufficiali veri, lette a mano: nessun falso allarme. L'edizione non si blocca: dopo due ricerche vere `ufficiale_cercato` fa scendere il CERCA ad avviso. Caso da aggiungere a `collaudo.py`: "51,7 (atteso 51,9)" senza tipo deve dare CERCA.

## G-08 - I sei perché della scommessa

**Misura.** La pagina riporta i perché solo il lunedì (mar-ven c'è "Il punto", che ha la sua forma e qui regge). Lunedì 23/11, dal registro `pronostici/2026-11-23-settimana.json`:

| Mercato | Tipo | Il perché stampato | Giudizio |
|---|---|---|---|
| S&P 500 | mattino | I future salgono di oltre il 2% dopo il crollo di venerdì | debole: dice il movimento, non che cosa l'ha mosso |
| Euro Stoxx 50 | fondo | Dopo il minimo da maggio aspetta di capire se Wall Street tiene | nessun motivo ("aspetta") |
| Treasury 10 anni | scenario | Se la paura cala i Treasury smettono di fare da rifugio e il rendimento risale | motivo |
| EUR/USD | mattino | L'euro recupera un po' dopo una settimana di dollaro forte | nessun motivo (rimbalzo dopo un calo) |
| Brent | scenario | Con meno fiducia nella crescita e più offerta il greggio ha poca spinta | motivo |
| Oro | mattino | Rimbalza dopo la caduta di venerdì, la peggiore da mesi | nessun motivo (rimbalzo dopo un calo) |

3 su 6 senza motivo, 1 debole: come nella prova (3 su 6). Sugli altri lunedì: 16/11 1 su 6 (Euro Stoxx, tipo fondo: "L'Europa aspetta i conti di Nvidia"); 9/11 0 su 6; 2/11 2 su 7 ("Rimbalzo tecnico dopo il calo di venerdì", "Dopo la vendita forzata, rimbalzo"); 19/10 1 su 7. Il difetto torna in due forme: "aspetta" su ogni riga di tipo fondo (2 su 2 dal metodo 1.3) e "rimbalza dopo il calo" sulle righe di tipo mattino quando il mattino non ha una notizia.

**Causa (verificata).** `APP_LUNEDI.md` §3: "per `fondo` dice che cosa aspetta quel mercato in settimana" (l'istruzione chiede proprio l'attesa), e il messaggio di `scommessa/pronostico.py` (riga 219) ripete "che cosa muove o che cosa aspetta QUEL mercato". "Non sono motivi: il rimbalzo dopo un calo" sta nella scelta della direzione, non nella scrittura del motivo, e `pronostico.py` controlla solo che il motivo ci sia e non sia doppio.

**Verdetto: CHIEDERE A PAOLO** (lo dice la scheda: tocca ciò che il lettore legge). Proposta per sostituzione: in `APP_LUNEDI.md` §3 la frase "per `mattino` dice che cosa ha mosso il mercato; per `fondo` dice che cosa aspetta quel mercato in settimana (...); per `scenario` e `catalizzatore` dice il legame..." diventa "dice perché quel mercato va nella direzione scelta: per `mattino` che cosa l'ha mosso, per `fondo` perché questa settimana la tendenza vale anche per lui, per `scenario` e `catalizzatore` il legame tra lo scenario, o l'evento, e quel mercato; un'attesa o un rimbalzo dopo un calo non sono un motivo". In `pronostico.py` il messaggio perde "o che cosa aspetta". Nessun controllo nuovo (una regex su "aspetta/rimbalza dopo" sarebbe una pezza di forma). Esempio per Paolo, solo con fatti dell'edizione #031:

- Euro Stoxx 50. Prima: "Dopo il minimo da maggio aspetta di capire se Wall Street tiene". Dopo: "I chip europei, i più colpiti venerdì, ripartono con i future americani".
- EUR/USD. Prima: "L'euro recupera un po' dopo una settimana di dollaro forte". Dopo: "Se la paura cala, il dollaro perde la domanda di rifugio che l'aveva spinto".
- Oro. Prima: "Rimbalza dopo la caduta di venerdì, la peggiore da mesi". Dopo: "Finite le vendite per coprire le perdite in borsa, torna a contare il rifugio".

## G-07 - Il conteggio delle parentesi di fonte

**Misura.** `g07_parentesi.py`: 90 parentesi nel testo dei cinque PDF (righe Fonti e tabella di pag. 6 escluse), lette tutte a mano: sono unità, date, orari, attese, definizioni ("(core PCE)"), etichette di tabella. **Nessuna testata tra parentesi**, nessun "(BoJ)"/"(Fed)" contato per errore ("Waller (Fed)" del #031 è una qualifica e il controllo non la conta). `controlli_testo.py` con i sorgenti di ogni giorno stampa 0 in tutte e cinque le edizioni.

**Causa.** Il difetto della prova (11 contate su circa 19) apparteneva alla regola di allora, una parentesi per paragrafo. Con ISTRUZIONI §3.5 (mai una testata tra parentesi) le parentesi sono a zero, e `fonti_tra_parentesi` riconosce oltre a fonti.json le testate scritte nelle righe Fonti dell'edizione (provato: Newsquawk, Kitco, CoinDesk, RTHK, IANS, dpa-AFX riconosciute con le righe Fonti; BoJ e Fed escluse). Resta fuori solo una testata tra parentesi che non sta né in fonti.json né in nessuna riga Fonti: in quel caso manca anche dalla riga Fonti, e quella è un'altra regola.

**Verdetto: NON COSTRUIRE.** Il difetto non si ripete.

## G-03 - Euro Stoxx 50 con EODHD giù

**Misura.** 0 su 5: tutte le edizioni hanno EODHD; quattro con dpa-AFX come seconda fonte concorde, la #035 con EODHD da solo (`fonte_singola`, ammesso). Nessun `eodhd_nd` nei sorgenti dal 16/11 (0 su 10).

**Causa (provata).** `controlli_dati.py`: con `eodhd_nd` salta la richiesta di EODHD, ma subito dopo `fonte_singola: true` basta al posto di `seconda_fonte`. Prova su una serie del 20/11 letta il 23/11: `{"fonte": "dpa-AFX", "fonte_singola": true, "eodhd_nd": "non risponde"}` passa; senza `eodhd_nd` è fermata. `collaudo.py` prova "EODHD giù, due fonti web" (passa) ma non "EODHD giù, una fonte".

**Verdetto: COSTRUIRE piccolo, ultimo in ordine.** Il difetto non è mai successo, e chiedere sempre due fonti web con EODHD giù rischia di lasciare l'edizione senza Euro Stoxx 50. Proposta coerente con ISTRUZIONI §2 (la fonte primaria basta da sola): in `controlli_dati.py` con `eodhd_nd` vale `fonte_singola` solo se la fonte è stoxx.com (il gestore dell'indice); altrimenti serve `seconda_fonte`. In `APP_DATI.md` §6 "Connettore EODHD che non risponde: `eodhd_nd` e le due fonti web" diventa "...: `eodhd_nd` e stoxx.com, oppure due fonti web". Prova: caso nuovo in `collaudo.py` ("EODHD giù, solo dpa-AFX" fermato; "EODHD giù, solo stoxx.com" passa), e i 10 `dati.json` archiviati restano tutti verdi (nessuno ha `eodhd_nd`).

## G-04 - L'agenda del lunedì

**Misura.** Nella settimana un solo lunedì: il 23/11 "In arrivo" si ferma a giovedì 26 (Wall Street chiusa), e la riga dice "Venerdì le azioni chiudono alle 19:00 a Roma": il lettore sa della seduta corta. Sui sei lunedì leggibili (`g04_agenda.py` e lettura del layout vecchio): venerdì presente il 2/11 e il 9/11; fino a giovedì il 19/10, 26/10 e 23/11; fino a mercoledì il 16/11 (prima del controllo).

**Causa.** `controlli_contenuti.py` (riga 352) ferma sotto giovedì e lo spiega: "un venerdì senza eventi che contano esiste". La regola in ISTRUZIONI §1 e APP_LUNEDI §4 dice già fino a venerdì.

**Verdetto: NON COSTRUIRE.** Il caso del 23/11 non ha tolto nulla al lettore, e alzare la soglia a venerdì farebbe aggiungere una riga di riempimento nei venerdì vuoti o festivi (falso allarme). Si riguarda solo se un lunedì perde un evento di venerdì che conta.

## G-44 - Pag. 5 con Tokyo chiusa (lun 23/11) e Wall Street chiusa (ven 27/11)

**Misura.**
- #031, pag. 5: testata "Chiusure al 20 novembre; Kospi al 23 novembre; Tokyo chiusa per festa" giusta; Nikkei 56.436,65 al 20/11 come il resto; "Livello 20/11"; nota con il Kospi del 23/11. Nota di 3 righe, come martedì-giovedì (3-4).
- #035, pag. 5: righe giuste riga per riga (verificate 1 g e 1 sett. di Nikkei, Hang Seng, Kospi, oro e Spread contro `dati.json` e le serie); gruppi segnati con la loro data ("EUROPA (26/11)", "ASIA (27/11)"), Brent al 25/11 detto in nota; chiusura di Wall Street detta in testata e nella Lettura. Nota di 4 righe (+1) e Lettura di 5 righe.
- **Difetto nuovo, visibile su tutte e sei le pagine della #035:** la testata dei dati (144 caratteri) si sovrappone allo slogan "I mercati globali spiegati, ogni mattina in 6 pagine" (pdftotext la legge "I mercati globaliChiusure spiegati,alogni..."; verificato sull'immagine di pag. 1). Misura con i font del motore su 10 edizioni dal 16/11: spazio a destra 348 pt, la #035 ne occupa 466; tutte le altre stanno sotto (la più lunga, il 24/11, 336 pt).
- Giri di correzione chiesti da pag. 5: i file archiviati non li registrano; la #035 è uscita alle 10:30 per il guasto di `pubblica.sh` (G-67), non per pag. 5. Non misurabile.

**Causa.** `gommberg_engine.page` disegna `META["nota_dati"]` con `drawRightString` senza misurarla; nessun controllo ne guarda la lunghezza, e nei giorni di chiusura la redazione deve dire più date.

**Verdetto: COSTRUIRE la testata, NON COSTRUIRE la nota.** Nel motore, per sostituzione: quando la nota dei dati non entra nello spazio a destra, quel giorno lo slogan lascia il posto alla nota, allineata a destra su tutta la riga (circa 520 pt, fino a circa 160 caratteri). Nessuna regola per chi scrive, nessun falso allarme: sulle 10 edizioni cambia solo la #035. Prova: rifare la #035 dai sorgenti archiviati e guardare l'anteprima. La nota più lunga di una riga non ha creato problemi di pagina: non si accorcia la forma delle eccezioni.

## Nota - Fonti deboli o poche negli approfondimenti

**Misura** (`fonti_approfondimenti.py`, 23 approfondimenti; livello da fonti.json sulle schede del giorno, agenzia o primaria = 1; verificati a mano i casi peggiori):

- senza nessuna fonte di livello 1, agenzia o primaria: 5 su 23 - #031 oro (Investrade, Schwab: entrambe fuori elenco), #032 Treasury (Kitco, Fox Business, Milano Finanza: tutte livello 2), #032 oro (Kitco, Nation Thailand), #033 Fed (solo Investing.com), #035 oro (solo The Company Chronicle, fuori elenco);
- con una o due testate: 8 su 23; testate fuori elenco: 19 su 79 citazioni (Schwab, Investrade, Stock Titan, Aju Press, JKN, City AM, Money.it, Digitaltoday, The Company Chronicle...);
- nelle righe Fonti di calendario e agenda di pag. 6: Investrade, FinancialJuice, LiteFinance, HyperStocks, BigGo Finance, political.org (il 27/11 solo BigGo Finance e political.org).

Gravità: il lettore vede nella riga Fonti un approfondimento sull'oro retto da un blog di broker o da un sito sconosciuto; contro le testate importanti chieste da Paolo il 19/11.

**Causa (verificata).** `controlli_fatti.py`/`autori.py` chiedono per ogni scheda la primaria o due autori diversi, ma un sito fuori elenco conta come autore (N10 del 23/11, Investrade più Schwab, passa); i minimi sono per edizione (almeno 6 schede di approfondimento), non per pezzo; ISTRUZIONI §4.4 chiede di guardare il fatto da più lati "non un numero da raggiungere". Nessuna regola vuole una testata grande sotto ogni approfondimento.

**Verdetto: CHIEDERE A PAOLO.** Proposta per sostituzione: in `controlli_fatti.py` il minimo "almeno 6 schede di approfondimento" per edizione esce, ed entra "ogni approfondimento poggia su almeno una scheda con fonte primaria, agenzia o livello 1" (le schede del modulo nel registro "scaletta"). Sulla settimana avrebbe chiesto un giro per 5 pezzi su 23, in 4 edizioni su 5; dopo 3 giri l'edizione esce com'è. Da chiedere: (1) se le "cinque testate importanti" sono l'elenco livello_1 di fonti.json (più largo: Korea Times, Teleborsa...) o un elenco stretto (Reuters, Bloomberg, FT, WSJ, una italiana); (2) se la regola vale anche per le righe Fonti di calendario e agenda. Esempio: oggi passa "Fonti: The Company Chronicle; chiusure dell'oro future da FMP" (#035, pag. 4); con la regola il pezzo sull'oro deve avere almeno una scheda Reuters, Bloomberg, AP, Kitco con agenzia o il dato CME, e The Company Chronicle resta solo come seconda voce.

## Nota - Indiscrezione o causa senza il nome della testata

**Misura** (`indiscrezioni.py` più lettura a mano di ogni frase trovata):

- #031: 3 frasi sullo scoop dell'indagine SEC su Nvidia - pag. 1 top story "riportata dalla stampa americana", titolo della notizia 01 "riferisce la stampa americana", pag. 2 perché "riportata dalla stampa americana" (le schede citano AFP, "- media", e InvestmentNews; la testata dello scoop non è mai detta);
- #032 pag. 2: "Dopo le dimissioni di Huang sono arrivate notizie secondo cui sarebbe stato nel mirino di un'operazione di intelligence straniera" - né testata né scheda del giorno (vedi anche gli errori di fatto);
- #033 pag. 1 top story: "le indiscrezioni su nuovi dazi americani" (a pag. 3 c'è "Secondo tre fonti citate da Reuters": il nome manca solo in prima pagina);
- #035: 3 frasi con la causa del rialzo di Seul data alla "stampa coreana" (pag. 1, pag. 2 perché e testo), mentre la scheda N02 nomina Seoul Economic Daily e Digitaltoday.

Totale 8 frasi in 4 edizioni su 5. Frasi trovate e giuste: #034 "Secondo Reuters ... un resoconto anonimo", #033 pag. 3 "le indiscrezioni dicono soltanto" (Reuters è nel pezzo). Gravità: alta per il #032 (una voce su una persona senza chi la dice), media per lo scoop del #031, bassa per il #035.

**Causa (verificata).** ISTRUZIONI §3.5 vuole il nome nella frase per un'indiscrezione o una spiegazione di qualcuno, ma `controlli_testo.py` accetta come chi dà la causa qualsiasi "secondo ..." (`ESENZIONI` contiene `secondo `) e non guarda le frasi senza connettivo causale ("riportata dalla stampa americana"). Con i sorgenti di ogni giorno il controllo è verde su tutte e cinque.

**Verdetto: COSTRUIRE**, per sostituzione in `controlli_testo.py`: in `ESENZIONI` esce `secondo ` generico ed entra "secondo" seguito da un nome riconosciuto (fonti.json e righe Fonti, come per le parentesi); in più un soggetto generico di notizia (stampa di un paese, media, "notizie secondo cui", indiscrezioni, fonti anonime) è un errore se il pezzo non nomina una testata. Sulla settimana: 8 frasi segnalate, tutte vere; le due giuste restano fuori perché il nome c'è nella frase o nel pezzo; nessun falso allarme. La regola esiste già (§3.5, G-47): niente da aggiungere alle istruzioni. Prova: il controllo su tutte le edizioni dal 16/11 prima del rilascio, e un caso in `collaudo.py`.

## Nota - "Sopra: ... Sotto: ..." su una chiusura di borsa

**Misura** (`agenda_chiusure.py`): 20 righe "In arrivo" nella settimana, 9 su chiusure, sedute corte o riaperture (quasi metà dell'agenda, settimana del Ringraziamento). Di queste 6 usano lo schema:

- #032 Ven 27 chiusura anticipata: "Sopra e sotto: con volumi bassi un dato o una notizia muovono i prezzi più del solito";
- #034 Gio 26 Wall Street chiusa: "Sopra: non c'è un dato da leggere. Sotto: con pochi scambi bastano poche operazioni..." (senza senso);
- #034 Ven 27 seduta corta: "Sopra: il VIX scende... Sotto: il VIX resta alto...";
- #035 Ven 27 riapertura, Ven 27 chiusura dei Treasury, Lun 30 "Wall Street torna agli orari normali" ("Sopra: scambi più alti... Sotto: volumi bassi...").

Le 3 righe senza schema (#031 Gio 26, #033 Gio 26 e Ven 27: "Si ascolta l'Asia di venerdì...") sono quelle giuste.

**Causa (verificata).** ISTRUZIONI §1: "L'ultima colonna insegna a leggere il dato prima che esca: "Sopra: ... Sotto: ..."", senza eccezione; l'eccezione ("Se un evento non ha un numero atteso, dice cosa ascoltare") sta solo nel commento del modello (`edizione_modello_v6.py`, riga 198), che la redazione legge dopo le istruzioni.

**Verdetto: COSTRUIRE**, una frase sostituita in ISTRUZIONI §1: "L'ultima colonna insegna a leggere il dato prima che esca: "Sopra: ... Sotto: ...", cosa succede di solito ai mercati se esce sopra o sotto le attese, mai una previsione" diventa "L'ultima colonna insegna a leggere l'evento prima che arrivi: per un dato con attese "Sopra: ... Sotto: ...", cosa succede di solito ai mercati se esce sopra o sotto; per un evento senza un numero atteso, in una frase cosa ascoltare; mai una previsione". Nessun esempio, nessun controllo (un controllo su "attese senza cifre" ne vedrebbe 2 su 6 e segnerebbe l'OPEC+ del #034, che regge: meglio niente). Prova: la prossima settimana con chiusure. Esempio per il lettore: prima "Sopra: non c'è un dato da leggere. Sotto: con pochi scambi bastano poche operazioni per muovere i prezzi"; dopo "Si ascolta l'Asia: con Wall Street ferma, pochi scambi bastano a muovere i prezzi".

---

## In coda 1 - Fatti non verificati delle note

- **"Taiwan -17% in settimana, il calo più forte dal 1990" (#031, pag. 2): GIUSTO.** Reuters (ripresa da Yahoo Finance, 22/11/2026): "Taiwan's stock market lost 17.5% in the week to November 20, its worst five days since 1990". Conferma da CriptoTendencia (21/11): TAIEX a 36.033,29 il 20/11 (-6,23%), -7.641,83 punti dal 13/11 (-17,5%). Il "-17%" è un arrotondamento per difetto di -17,5%.
- Verificati sulle serie archiviate, giusti: S&P 500 +4,7% "il rialzo più forte da almeno un anno" (#032; nessun +3% dal 13/11/2025); oro +4,3% "il maggiore dal 3 febbraio" (#035; +6,07% il 3/2, +4,35% il 28/1); oro da 3.864 a 3.515 tra 17 e 20/11 e 172 dollari ripresi (#035); Brent "dal 9/11 tra 89,37 e 95,84" e corridoio di 6,47 $ (#035); 89,37 minimo del mese (#033); 10 anni al 5,15% il 13/11 e Brent a 95,84 (#032); 2 anni a 4,83% il 16/11 (#031); S&P "quasi -9% in sei sedute, ne ha ripreso metà" (#032).

## In coda 2 - Errori di fatto trovati rileggendo

1. **#033, pag. 5, Lettura:** "il Brent a -21,7% in un mese contro il 7,8% in meno dell'oro". In un mese l'oro perde l'11,1% (stessa tabella, colonna 1 mese; `oro.csv`: 4.007,9 il 23/10, 3.561,9 il 24/11); -7,8% è la settimana (3.864,2 del 17/11). La Lettura confronta il mese del Brent con la settimana dell'oro.
2. **#034, pag. 3, Perché:** "ieri il 2 anni è sceso comunque, come il 10 anni, di 6 pb". Il 2 anni è sceso di 2 pb (4,63 il 24/11, 4,61 il 25/11: tabella di pag. 5 della stessa edizione e `dati.json` del 26/11); di 6 è sceso solo il 10 anni. In più "infatti" lega il calo a "un dato così alza i rendimenti a breve": la frase dice il contrario di ciò che vuole spiegare.
3. **#032, pag. 2:** "Dopo le dimissioni di Huang sono arrivate notizie secondo cui sarebbe stato nel mirino di un'operazione di intelligence straniera". Ordine sbagliato: il consiglio di Nvidia annuncia l'indagine su quelle notizie l'8/11 (comunicato del consiglio, schede D04 del 12/11 e D08 del 13/11), le dimissioni sono del 12/11. La frase non poggia su nessuna scheda del 24/11.
4. **#034, pag. 3, E quindi (minore):** "sopra il 4,92% di lunedì e martedì": martedì 24 il 10 anni era al 4,91% (`ust10.csv`, tabella del #033).
5. **#035, pag. 2, Il numero (minore):** "-1,8%: quanto manca al Kospi per tornare ai 5.006 punti": per tornarci serve +1,8% (4.915,68 contro 5.006,03); il segno è sbagliato.

Altri difetti incontrati, non di fatto, da affidare alle voci giuste:
- #035 pag. 5: agenda fuori ordine ("Mer 9 dic" prima di "Lun 30"): nessun controllo né il motore ordinano le righe per data.
- #033 pag. 5: mancano Treasury 2 anni e Spread Italia. Il 2 anni è uscito con `nd` "rendimento identico (4,63%) da tre sedute: il controllo lo segna come dato fermo", ma 4,63 il 20, 23 e 24/11 era vero (`dati.json` del 26/11): falso allarme del controllo sul dato fermo, che ha tolto una riga giusta.
- #034 pag. 6: la tabella Fonti dà per i Treasury "BullionVault", la riga Fonti del pezzo "Longbridge": le due righe non coincidono.
- #035 testata: "Chiusure al 26 novembre per Europa e Asia di ieri, al 27 novembre per Tokyo, Hong Kong e Seul" dice due date per l'Asia nella stessa frase (oltre alla sovrapposizione, sezione G-44).
