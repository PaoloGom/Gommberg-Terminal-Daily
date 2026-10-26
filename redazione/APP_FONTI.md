# Appendice - Trovare i dati e citarli (da leggere quando un dato non esce al primo tentativo, o per una fonte ufficiale)

## 1. Trovare qualsiasi dato: metodo, non elenchi
- Prima chiediti **chi produce il dato** (la borsa per un indice, l'istituto di statistica, la società, la banca centrale) e cerca in quest'ordine: il produttore; l'agenzia di stampa nazionale del paese (Yonhap, Kyodo, ANSA, Xinhua...); la stampa finanziaria locale, in inglese e nella lingua del paese.
- **Scala prima di arrenderti (max 5 ricerche per dato):** (1) due formulazioni nelle parole delle agenzie ("Kospi closes" + data in più formati; "chiude"); (2) WebSearch `mode: "extended"` (se il proxy la rifiuta, vai avanti); (3) le pagine elenco delle testate uscite; (4) WebFetch dell'articolo e cifra letterale.
- **Il flusso della notte** (prima lettura delle notizie, §2): WebSearch "investingLive" + data ("investingLive October 26 2026") e apri la pagina elenco restituita; poi una ricerca sulle agenzie ("Reuters markets overnight", "Asia open") per le storie non di mercato che muovono i mercati (voti, decisioni politiche, attacchi, annunci). Si legge da ieri sera all'ora della ricerca, segnando ora e fonte dei titoli più forti. È il sensore più rapido che abbiamo: il 26/10/2026 il risultato del ballottaggio in Brasile e il -15% dell'ETF a Tokyo erano lì alle 4:14, a 5 ore dall'uscita.
- WebSearch sempre senza `allowed_domains`, poi filtra con `fonti.json`. Notizie del giorno: la ricerca indicizza male le ultime ore; funzionano le pagine elenco di borsaitaliana.it (Radiocor) e investinglive.com trovate via ricerca. Articoli di ieri: nome dell'evento + data ("PPI October 15 2026", "PPI 15 ottobre").
- **Registro delle ricerche:** ogni dato che ha richiesto più di una ricerca, o che manca, lascia in `fatti.json` `{"id": "R1", "sezione": "ricerca", "dato": "...", "ricerche": [...], "esito": "trovato" | "mancante", "fonte": {"testata", "url"}}`. `prepara.sh` lo rilegge la mattina dopo (`ricerche.py`: dove li abbiamo trovati). "n.d." o "non verificato" nel PDF solo con la scheda "mancante" e almeno 4 ricerche (`controlli_contenuti.py`).
- Esempio che ha fatto nascere la regola: la chiusura del Kospi del 16/10/2026 (5.668,05, +2,05%) era su Seoul Economic Daily dalle 15:38 di Seul; FMP gratuito non copre il Kospi e la ricerca standard trovava solo gli articoli del mattino.

## 2. Fonti ufficiali (scheda `"tipo": "U"` e ogni riga del calendario)
- Un dato macro, una decisione di banca centrale, un'asta o un comunicato si prende dal comunicato ufficiale (`fonti.json` "ufficiali"); l'agenzia serve solo d'appoggio (contesto, attese, reazioni).
- Si arriva al sito ufficiale **solo via ricerca**: WebSearch con nome della fonte + dato + data ("BLS CPI September 2026 news release", "Istat inflazione settembre 2026 comunicato"), poi WebFetch del link restituito. Il comunicato BLS esce spesso come PDF su dol.gov (ufficiale). Scarta gli aggregatori vietati.
- Se dopo 2 ricerche vere il comunicato non esce: `"ufficiale_cercato": [le ricerche]` e il dato esce attribuito "(Reuters)". `controlli_fatti.py` blocca con CERCA e non toglie mai il dato.

## 2b. Agenda: ogni riga con un orario in ora italiana (regola del 26/10/2026)
**Formato identico per ogni riga:** `quando` = giorno + UN solo orario di Roma ("Ven 30, 14:30"); `evento` = solo il nome, breve, senza parentesi, senza ";" e senza orari ("Conti di Exxon Mobil"); un dettaglio utile va in `perche`. Un evento per riga: due eventi insieme si dividono. Sempre ora di Roma, mai ET, CT, UTC, EDT, PT nel testo.

**Scala dell'orario, in quest'ordine (si ferma al primo gradino che funziona):**
1. **Ora esatta da fonte che la dice** (calendario dell'ente, comunicato o avviso dell'azienda, non aggregatori), convertita in ora di Roma con `TZ=Europe/Rome` o in codice. Per le trimestrali si scrive l'ora della conference call, uguale per tutte (ExxonMobil 8:30 CT, Chevron 11:00 ET). USA e Europa cambiano ora in date diverse (nel 2026 l'Europa il 25/10, gli USA l'1/11): fino al 31/10 New York è 5 ore indietro, dopo 6 (dal 29/3 al 4/4 e dal 25/10 all'1/11 le sedute USA aprono alle 14:30 e chiudono alle 21:00; nel resto dell'anno 15:30 e 22:00).
2. **Seconda ricerca** (una sola) sul sito dell'azienda o dell'ente: area investitori, "events", calendario ufficiale. Mai un'ora ricavata da articoli automatici (ad-hoc-news, finanzen, aggregatori con "AI" nel nome).
3. **Fascia, solo da questa lista chiusa**, scritta nel campo `quando` dopo il giorno: "prima dell'apertura USA", "dopo la chiusura USA", "in mattinata", "nel pomeriggio", "in serata". Si usa solo se la fonte dice almeno se è prima o dopo la seduta; mai "ora da confermare" né altre formule.
4. **Nessuna fonte nemmeno sulla fascia:** la riga non entra in agenda (meglio una riga in meno che un orario inventato) e va in una nota del revisore.

Controlli: `edizioni_voce.py` segnala come AVVISO ogni riga con orario non in lista, parentesi, ";" o fusi orari stranieri (dopo 5 edizioni senza falsi positivi diventa ERRORE). Il revisore verifica che nessuna riga sia senza orario o fascia.

## 3. Fiducia e citazioni
- Ufficiali e livello 1: ne basta una. Livello 2, e ogni fonte seria non in elenco: due indipendenti che danno lo stesso numero. Vietate: mai.
- Un dato pubblico certo (calendario, chiusura o movimento di un indice) con una sola fonte attendibile: si pubblica dichiarato, "-7,57% (Korea Herald)", scheda `"fonte_singola": true`.
- WebFetch riassume e può inventare: per una citazione chiedi la frase letterale e tienila solo se il testo la contiene parola per parola.

## 4. Registri in `fatti.json` (li controlla `controlli_contenuti.py`)
- Prime pagine (§2): `{"id": "P1", "sezione": "prime_pagine", "flusso": ["titolo (fonte, ora di Roma)", ...3-5], "testate": [{"testata": "...", "storie": ["...", ...3-5, la prima è l'apertura]}, ...almeno 3], "fuori": [{"storia": "...", "motivo": "..."}], "concorda": true | false, "motivo": "..."}`. `flusso` = i titoli più forti della notte (§1, "Il flusso della notte"); `fuori` = ogni storia forte in almeno due letture (flusso o testate) che non copriamo, col perché ("troppo piccola", "senza dati di mercato prima dell'uscita: la prova è l'apertura di X alle HH:MM", "in agenda"); `[]` se non ce ne sono. Le schede vecchie con `"apertura"` restano valide.
- Il perché (§6.2c): `{"id": "A1", "sezione": "anomalia", "fatto": "...", "ricerche": ["query", ...], "ipotesi": [{"causa": "...", "fonte": "C03" | null, "prevede": "...", "prezzi": "torna" | "in parte" | "non torna"}], "esito": "C03" | "ipotesi" | "non chiarita"}`.
- Ricerche (§1 qui sopra): `{"id": "R1", "sezione": "ricerca", ...}`.
