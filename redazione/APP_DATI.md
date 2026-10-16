# Appendice - Dati: endpoint, simboli, basi, fonti

Da leggere se una chiamata dati fallisce o serve un dato nuovo. Ogni dato va in `dati.json` (con `tipo` chiusura|intraday e, dove esiste, `seconda_fonte`) e passa `controlli_dati.py`.

## 1. FMP (verificato il 15/10/2026 sul piano attuale)
- `indexes`, endpoint `index-historical-price-eod-light`, con from/to: **funzionano** ^GSPC (S&P 500), ^IXIC (Nasdaq), ^DJI (Dow), ^RUT (Russell 2000), ^STOXX50E, ^FTSE, ^N225, ^HSI, ^VIX.
- **Non funzionano** (piano): FTSEMIB.MI, ^KS11, 000001.SS (Shanghai), ^GDAXI, ^FCHI, endpoint `quote`, `chart` e intraday degli indici.
- `economics`, endpoint `treasury-rates`: curva completa (year2, year10, year30...). Chiusure del giorno: valgono per base e verdetto della scommessa.
- `commodity`, endpoint `commodities-historical-price-eod-light`: BZUSD (Brent future), GCUSD (oro future). **Non funziona** CLUSD (WTI).
- Attenzione: FMP restituisce già una riga con la data di oggi, con valore intraday (a volte volume 0): mai usarla come chiusura.

## 2. Alpha Vantage (max 25 chiamate al giorno, una al secondo, una dopo l'altra)
- `TIME_SERIES_DAILY` ACWI; `FX_DAILY` EUR/USD (chiusure); `CURRENCY_EXCHANGE_RATE` EUR/USD (livello di stamattina, con orario).
- `BRENT` e `WTI` interval daily = prezzi spot EIA (fisico), non future, con qualche giorno di ritardo: normale. Per il WTI future serve una fonte web.
- `GOLD_SILVER_SPOT` (oro spot, seconda fonte per l'oro), `TREASURY_YIELD` (chiusure con un giorno di ritardo: per la scommessa valgono quelle FMP).

## 3. Fonti web per i dati che le API non danno (vanno in `fatti.json` e in revisione)
- **FTSE MIB** (chiusura e da inizio anno): Borsa Italiana, Sole 24 Ore/Radiocor, Teleborsa, ANSA (livello 1).
- **BTP 10 anni e spread BTP-Bund** (in pb, chiusura): Sole 24 Ore, Teleborsa, ANSA, Borsa Italiana (livello 1); MTS indicato come fonte se citato.
- **Kospi, Shanghai** e borse asiatiche di stamattina: Reuters, Nikkei Asia, Korea Herald, SCMP (livello 1); Trading Economics, investingLive (livello 2, due testate). Sempre con orario, segnati * nel cruscotto.
- **WTI future**, future sugli indici di stamattina: Reuters, CNBC (livello 1) o TheStreet/investingLive (livello 2), con orario.
- Dow, Russell e da-inizio-anno USA in alternativa: AP "How major US stock indexes fared" + data.
- Consensi e calendario: siti ufficiali (Fed, BLS, BEA, BCE, Istat), Reuters, Trading Economics (livello 2).

## 4. Basi da inizio anno 2026 (ultima chiusura del 2025, verificate su FMP il 15/10/2026)
S&P 500 6.845,49 (31/12) | Nasdaq 23.241,99 (31/12) | Dow 48.063,28 (31/12) | Russell 2000 2.481,91 (31/12) | Euro Stoxx 50 5.796,22 (30/12) | FTSE 100 9.931,38 (31/12) | Nikkei 50.339,48 (30/12) | Hang Seng 25.630,55 (31/12). FTSE MIB e Kospi: da fonte web, una volta, poi annotala qui.
Meglio ancora: calcolale in codice dalla serie (from/to sull'ultima settimana di dicembre). Dal primo giorno di borsa di gennaio si usano le basi dell'anno appena chiuso: mai quelle dell'anno prima. Ogni gennaio aggiorna questa tabella.

## 5. Orari di chiusura (ora di Roma) e intraday
Prima dell'ora di chiusura il dato di oggi è intraday. `controlli_dati.py` converte con `zoneinfo` la chiusura locale (più un margine per l'asta) in ora di Roma per la data del giorno: in ottobre circa USA 22:15, Europa e Londra 17:45, Tokyo 08:45, Seul 08:45, Shanghai 09:15, Hong Kong 10:15 (i fusi cambiano in date diverse). Le chiusure europee di oggi la mattina non esistono: ticker e cruscotto usano la seduta precedente.

## 6. Regole v6.2 (16/10/2026)
- Alpha Vantage sempre in serie, una chiamata dopo l'altra (in parallelo dà rate limit). `TIME_SERIES_DAILY` compact = 100 giorni (circa 15k token): solo se la serie serve a un grafico; per la sola chiusura usa `GLOBAL_QUOTE` o FMP.
- Indici obbligatori in `dati.json`: S&P 500, Nasdaq, Euro Stoxx 50, Nikkei 225, Kospi, Hang Seng (chiusura dell'ultima seduta conclusa; un'Asia chiusa dopo l'edizione di ieri conta). Senza livello: `{"mercato": "KR", "tipo": "intraday", "var": -8.68, "ora": "08:11", "fonte": "Teleborsa", "ultimi": []}`.
- `"macro"` in `dati.json` per i dati del giorno: `[{"nome": "PPI USA a/a", "dato": 6.3, "atteso": 5.3, "caldo_se": "su"}]` ("giu" per sussidi e disoccupazione): serve al controllo delle anomalie.
