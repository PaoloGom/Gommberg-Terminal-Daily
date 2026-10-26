# Appendice - Trovare i dati e citarli (da leggere quando un dato non esce al primo tentativo, o per una fonte ufficiale)

## 1. Trovare qualsiasi dato: metodo, non elenchi
- Prima chiediti **chi produce il dato** (la borsa per un indice, l'istituto di statistica, la società, la banca centrale) e cerca in quest'ordine: il produttore; l'agenzia di stampa nazionale del paese (Yonhap, Kyodo, ANSA, Xinhua...); la stampa finanziaria locale, in inglese e nella lingua del paese.
- **Scala prima di arrenderti (max 5 ricerche per dato):** (1) due formulazioni nelle parole delle agenzie ("Kospi closes" + data in più formati; "chiude"); (2) WebSearch `mode: "extended"` (se il proxy la rifiuta, vai avanti); (3) le pagine elenco delle testate uscite; (4) WebFetch dell'articolo e cifra letterale.
- WebSearch sempre senza `allowed_domains`, poi filtra con `fonti.json`. Notizie del giorno: la ricerca indicizza male le ultime ore; funzionano le pagine elenco di borsaitaliana.it (Radiocor) e investinglive.com trovate via ricerca. Articoli di ieri: nome dell'evento + data ("PPI October 15 2026", "PPI 15 ottobre").
- **Registro delle ricerche:** ogni dato che ha richiesto più di una ricerca, o che manca, lascia in `fatti.json` `{"id": "R1", "sezione": "ricerca", "dato": "...", "ricerche": [...], "esito": "trovato" | "mancante", "fonte": {"testata", "url"}}`. `prepara.sh` lo rilegge la mattina dopo (`ricerche.py`: dove li abbiamo trovati). "n.d." o "non verificato" nel PDF solo con la scheda "mancante" e almeno 4 ricerche (`controlli_contenuti.py`).
- Esempio che ha fatto nascere la regola: la chiusura del Kospi del 16/10/2026 (5.668,05, +2,05%) era su Seoul Economic Daily dalle 15:38 di Seul; FMP gratuito non copre il Kospi e la ricerca standard trovava solo gli articoli del mattino.

## 2. Fonti ufficiali (scheda `"tipo": "U"` e ogni riga del calendario)
- Un dato macro, una decisione di banca centrale, un'asta o un comunicato si prende dal comunicato ufficiale (`fonti.json` "ufficiali"); l'agenzia serve solo d'appoggio (contesto, attese, reazioni).
- Si arriva al sito ufficiale **solo via ricerca**: WebSearch con nome della fonte + dato + data ("BLS CPI September 2026 news release", "Istat inflazione settembre 2026 comunicato"), poi WebFetch del link restituito. Il comunicato BLS esce spesso come PDF su dol.gov (ufficiale). Scarta gli aggregatori vietati.
- Se dopo 2 ricerche vere il comunicato non esce: `"ufficiale_cercato": [le ricerche]` e il dato esce attribuito "(Reuters)". `controlli_fatti.py` blocca con CERCA e non toglie mai il dato.

## 2b. Agenda: ogni riga con un orario (regola del 26/10/2026)
- **Un evento per riga**, con giorno e ora di Roma ("Ven 30, 11:30: ..."). Due eventi nella stessa riga (come "Gio 29, 13:30: PCE; ven 30: Exxon e Chevron") rompono l'omogeneità della sezione: si dividono.
- **L'ora viene da una fonte che la dice**: calendario dell'ente o area investitori dell'azienda (es. ExxonMobil: comunicato 5:30 CT = 11:30 a Roma; call 8:30 CT = 14:30). Conversione in codice o con `TZ=Europe/Rome`, ricordando che USA e Europa cambiano ora in date diverse (nel 2026 l'Europa il 25/10, gli USA l'1/11: fino al 31/10 la differenza con New York è di 5 ore, poi 6).
- **Se nessuna fonte seria dà l'ora**, la riga non salta e non inventa: scrive la fascia "prima dell'apertura USA", "dopo la chiusura USA" o "in giornata" seguita da "(ora da confermare)", e tenta una seconda ricerca sul sito dell'azienda. Mai un'ora presa da articoli automatici (ad-hoc-news, finanzen, aggregatori con "AI" nel nome).
- Le righe di una stessa azienda con più eventi (comunicato e call) si scrivono come una riga sola con le due ore: "Ven 30, 11:30 comunicato e 14:30 call: Exxon Mobil".
- Il revisore controlla che nessuna riga dell'agenda sia senza ora o fascia.

## 3. Fiducia e citazioni
- Ufficiali e livello 1: ne basta una. Livello 2, e ogni fonte seria non in elenco: due indipendenti che danno lo stesso numero. Vietate: mai.
- Un dato pubblico certo (calendario, chiusura o movimento di un indice) con una sola fonte attendibile: si pubblica dichiarato, "-7,57% (Korea Herald)", scheda `"fonte_singola": true`.
- WebFetch riassume e può inventare: per una citazione chiedi la frase letterale e tienila solo se il testo la contiene parola per parola.

## 4. Registri in `fatti.json` (li controlla `controlli_contenuti.py`)
- Prime pagine (§2): `{"id": "P1", "sezione": "prime_pagine", "testate": [{"testata": "...", "apertura": "..."}], "concorda": true | false, "motivo": "..."}`.
- Il perché (§6.2c): `{"id": "A1", "sezione": "anomalia", "fatto": "...", "ricerche": ["query", ...], "ipotesi": [{"causa": "...", "fonte": "C03" | null, "prevede": "...", "prezzi": "torna" | "in parte" | "non torna"}], "esito": "C03" | "ipotesi" | "non chiarita"}`.
- Ricerche (§1 qui sopra): `{"id": "R1", "sezione": "ricerca", ...}`.
