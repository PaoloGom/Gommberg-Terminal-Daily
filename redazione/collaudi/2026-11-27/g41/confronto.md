# G-41 - Chiusure di Kospi e Hang Seng: EODHD contro una seconda fonte (27/11/2026)

Regola di APP_DATI §2b: un nuovo uso di EODHD si prova prima con un confronto su almeno 20 sedute.

## Fonti

- **EODHD** (connettore del progetto, piano gratuito): `get_historical_stock_prices`, `KS11.INDX` e `HSI.INDX`, dal 13/10 al 27/11/2026, csv. Due chiamate in tutto, lette il 27/11 alle 16:55 circa (ora di Roma), a borse asiatiche chiuse.
- **Seconda fonte: Investing.com** (storico giornaliero, kr.investing.com per il Kospi e investing.com per l'Hang Seng), fornitore di dati indipendente da EODHD: il 26/10 per il Kospi scrive un valore diverso da EODHD (vedi sotto), quindi non ripubblica EODHD.
- **Terza fonte, solo per la seduta discorde:** Korea JoongAng Daily (26/10/2026, "close down 80.83 points, or 1.46 percent, at 5,469.47") e Money Today (mt.co.kr, 26/10/2026, "closed regular trading at 5,469.47, down 80.83 points (1.46%)").
- **Scartata come seconda fonte: FMP `^HSI`.** Ha gli stessi volumi di EODHD riga per riga (stesso flusso a monte): non è indipendente. FMP `^KS11` non è nel piano.
- Investing.com letto con WebFetch (pagina dello storico, due intervalli di date: 13/10-27/10 e 27/10-27/11, coincidenti sul 27/10).
- Non raggiungibili da qui: KRX (data.krx.co.kr chiede richieste POST), Naver Finance, MarketWatch, Stooq (bloccati). Hang Seng Indexes (hsi.com.hk) pubblica solo il dato corrente.

## Festività locali nel periodo

- Hong Kong chiusa lunedì 19/10 (Chung Yeung, festa il giorno dopo la domenica): EODHD non scrive la riga, Investing nemmeno. Nessuna riga a indice fermo nel periodo.
- Seul: nessuna chiusura nel periodo (Chuseok e Hangul Day sono prima del 13/10).
- Le righe EODHD del 27/11 sono la seduta di oggi, letta a borse chiuse (Hang Seng con volume 0: il volume non è ancora scritto, la chiusura coincide con Investing).
- I volumi EODHD del Kospi cambiano unità tra una seduta e l'altra (migliaia fino al 20/11, unità dal 23/11 al 26/11, di nuovo migliaia il 27/11): non vanno usati (la regola in APP_DATI §2b dice volume null).

## Kospi: 34 sedute (13/10 - 27/11/2026)

| Seduta | EODHD | Investing.com | Scarto |
|---|---:|---:|---:|
| 13/10 | 6.035,3501 | 6.035,35 | 0,0000% |
| 14/10 | 6.008,8101 | 6.008,81 | 0,0000% |
| 15/10 | 5.554,2202 | 5.554,22 | 0,0000% |
| 16/10 | 5.668,0498 | 5.668,05 | 0,0000% |
| 19/10 | 5.768,0098 | 5.768,01 | 0,0000% |
| 20/10 | 5.552,7402 | 5.552,74 | 0,0000% |
| 21/10 | 5.735,6602 | 5.735,66 | 0,0000% |
| 22/10 | 5.533,7700 | 5.533,77 | 0,0000% |
| 23/10 | 5.550,2998 | 5.550,30 | 0,0000% |
| 26/10 | 5.469,4702 | 5.460,52 | +0,1639% |
| 27/10 | 5.638,3398 | 5.638,34 | 0,0000% |
| 28/10 | 6.012,4399 | 6.012,44 | 0,0000% |
| 29/10 | 5.937,6602 | 5.937,66 | 0,0000% |
| 30/10 | 5.730,7402 | 5.730,74 | 0,0000% |
| 2/11 | 5.859,0801 | 5.859,08 | 0,0000% |
| 3/11 | 5.648,7900 | 5.648,79 | 0,0000% |
| 4/11 | 5.683,7998 | 5.683,80 | 0,0000% |
| 5/11 | 5.383,7998 | 5.383,80 | 0,0000% |
| 6/11 | 5.059,6899 | 5.059,69 | 0,0000% |
| 9/11 | 5.018,8501 | 5.018,85 | 0,0000% |
| 10/11 | 5.239,1299 | 5.239,13 | 0,0000% |
| 11/11 | 5.375,3599 | 5.375,36 | 0,0000% |
| 12/11 | 5.342,7300 | 5.342,73 | 0,0000% |
| 13/11 | 5.290,5298 | 5.290,53 | 0,0000% |
| 16/11 | 5.100,5000 | 5.100,50 | 0,0000% |
| 17/11 | 4.968,4800 | 4.968,48 | 0,0000% |
| 18/11 | 5.067,4399 | 5.067,44 | 0,0000% |
| 19/11 | 5.137,8901 | 5.137,89 | 0,0000% |
| 20/11 | 4.869,9600 | 4.869,96 | 0,0000% |
| 23/11 | 4.708,5400 | 4.708,54 | 0,0000% |
| 24/11 | 5.006,0300 | 5.006,03 | 0,0000% |
| 25/11 | 4.697,5100 | 4.697,51 | 0,0000% |
| 26/11 | 4.711,2100 | 4.711,21 | 0,0000% |
| 27/11 | 4.915,6800 | 4.915,68 | 0,0000% |

## Hang Seng: 33 sedute (13/10 - 27/11/2026)

| Seduta | EODHD | Investing.com | Scarto |
|---|---:|---:|---:|
| 13/10 | 24.345,2207 | 24.345,22 | 0,0000% |
| 14/10 | 24.314,1699 | 24.314,17 | 0,0000% |
| 15/10 | 24.062,7207 | 24.062,72 | 0,0000% |
| 16/10 | 24.186,8301 | 24.186,83 | 0,0000% |
| 20/10 | 23.867,7402 | 23.867,74 | 0,0000% |
| 21/10 | 23.651,8691 | 23.651,87 | 0,0000% |
| 22/10 | 22.934,6797 | 22.934,68 | 0,0000% |
| 23/10 | 23.093,3691 | 23.093,37 | 0,0000% |
| 26/10 | 23.211,8105 | 23.211,81 | 0,0000% |
| 27/10 | 23.041,3203 | 23.041,32 | 0,0000% |
| 28/10 | 23.094,8301 | 23.094,83 | 0,0000% |
| 29/10 | 22.958,6504 | 22.958,65 | 0,0000% |
| 30/10 | 23.294,4199 | 23.294,42 | 0,0000% |
| 2/11 | 23.393,3203 | 23.393,32 | 0,0000% |
| 3/11 | 23.525,9707 | 23.525,97 | 0,0000% |
| 4/11 | 23.919,5000 | 23.919,50 | 0,0000% |
| 5/11 | 24.796,9805 | 24.796,98 | 0,0000% |
| 6/11 | 24.481,8594 | 24.481,86 | 0,0000% |
| 9/11 | 24.448,9492 | 24.448,95 | 0,0000% |
| 10/11 | 24.557,0391 | 24.557,04 | 0,0000% |
| 11/11 | 24.315,9199 | 24.315,92 | 0,0000% |
| 12/11 | 24.008,5508 | 24.008,55 | 0,0000% |
| 13/11 | 23.637,5996 | 23.637,60 | 0,0000% |
| 16/11 | 23.753,8398 | 23.753,84 | 0,0000% |
| 17/11 | 23.508,1699 | 23.508,17 | 0,0000% |
| 18/11 | 23.294,7500 | 23.294,75 | 0,0000% |
| 19/11 | 22.841,6191 | 22.841,62 | 0,0000% |
| 20/11 | 22.410,8008 | 22.410,80 | 0,0000% |
| 23/11 | 22.383,7402 | 22.383,74 | 0,0000% |
| 24/11 | 22.219,6504 | 22.219,65 | 0,0000% |
| 25/11 | 21.966,0098 | 21.966,01 | 0,0000% |
| 26/11 | 22.226,8809 | 22.226,88 | 0,0000% |
| 27/11 | 22.694,7695 | 22.694,77 | 0,0000% |

## Esito

- **Kospi**: 34 sedute; sedute concordi entro lo 0,05%: 33, scarto massimo tra quelle 0,0000% (arrotondamento al centesimo). Scarto massimo assoluto 0,1639% (26/10, vedi sotto).
- **Hang Seng**: 33 sedute; sedute concordi entro lo 0,05%: 33, scarto massimo tra quelle 0,0000% (arrotondamento al centesimo). Scarto massimo assoluto 0,0000%.
- **Seduta discorde: Kospi 26/10.** EODHD 5.469,47, Investing 5.460,52 (+0,16%). Le due cronache di chiusura del giorno (JoongAng Daily, Money Today) danno 5.469,47: ha ragione EODHD; il valore di Investing è con ogni probabilità un dato di seduta in corso mai corretto.
- **Archivio** (`redazione/chiusure.csv`): le chiusure del Kospi dal 5/11 al 27/11 e quelle dell'Hang Seng del 20/10 e dal 5/11 al 27/11 (le sole che l'archivio ha nel periodo) coincidono con EODHD entro un centesimo.
- **Conclusione:** su 34 + 33 sedute EODHD dà la chiusura ufficiale, con la data giusta e senza righe nei giorni di festa locale del periodo. Il metodo dell'Euro Stoxx 50 (§2b) si può estendere a Kospi e Hang Seng.
