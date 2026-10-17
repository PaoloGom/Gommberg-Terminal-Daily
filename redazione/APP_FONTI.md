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

## 3. Fiducia e citazioni
- Ufficiali e livello 1: ne basta una. Livello 2, e ogni fonte seria non in elenco: due indipendenti che danno lo stesso numero. Vietate: mai.
- Un dato pubblico certo (calendario, chiusura o movimento di un indice) con una sola fonte attendibile: si pubblica dichiarato, "-7,57% (Korea Herald)", scheda `"fonte_singola": true`.
- WebFetch riassume e può inventare: per una citazione chiedi la frase letterale e tienila solo se il testo la contiene parola per parola.

## 4. Registri in `fatti.json` (li controlla `controlli_contenuti.py`)
- Prime pagine (§2): `{"id": "P1", "sezione": "prime_pagine", "testate": [{"testata": "...", "apertura": "..."}], "concorda": true | false, "motivo": "..."}`.
- Il perché (§6.2c): `{"id": "A1", "sezione": "anomalia", "fatto": "...", "ricerche": ["query", ...], "ipotesi": [{"causa": "...", "fonte": "C03" | null, "prevede": "...", "prezzi": "torna" | "in parte" | "non torna"}], "esito": "C03" | "ipotesi" | "non chiarita"}`.
- Ricerche (§1 qui sopra): `{"id": "R1", "sezione": "ricerca", ...}`.
