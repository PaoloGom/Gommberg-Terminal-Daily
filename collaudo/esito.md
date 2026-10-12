# Esito collaudo end-to-end - 12/10/2026 pomeriggio

Esecuzione di collaudo (edizione n. 0), lanciata alle 17:09 ora di Roma. PDF: `pdf/2026-10-12-gommberg-collaudo.pdf`. Controllo automatico: `controlli.py ... 0` -> OK (6 pagine, 8 "n.d.").

## Tempi (ora di Roma, paragrafo 6)
| Passo | Inizio | Fine |
|---|---|---|
| Ora corrente + clone del repository | 17:09:40 | 17:09:45 |
| 1. Kit (lettura ISTRUZIONI, modello, motore, copia in /home/claude/lavoro, install svglib) | 17:09:45 | 17:17:36 |
| 2. Cosa è già uscito (edizioni.json) | 17:10:00 | 17:10:30 |
| 3. Dati e ricerca (2 agenti in parallelo + FMP/Alpha Vantage) | 17:10:30 | 17:18:00 |
| 4. Stesura (script, grafici, primo render) | 17:18:00 | 17:22:18 |
| 5. Controlli automatici e visivi | 17:22:18 | 17:27:40 |
| 6. Revisione mirata (revisore + correzioni + nuovo render) | 17:23:00 | 17:27:30 |
| 7. Pubblicazione (commit/push, archivio Artifact) e consegna | 17:28:00 | dopo questo commit (esito nel messaggio finale) |

Nota: i passi 1-3 si sovrappongono perché gli agenti di ricerca lavorano mentre si leggono kit e dati.

## Strumenti usati
Bash (git, python3, reportlab, matplotlib, svglib, qpdf, pdftotext, pdftoppm, pdfinfo), Read/Write, FMP (`indexes` eod-light, `economics` treasury-rates, `commodity` BZUSD), Alpha Vantage (TIME_SERIES_DAILY ACWI, FX_DAILY, CURRENCY_EXCHANGE_RATE, BRENT daily), WebSearch/WebFetch (verifica TheStreet), Agent, Artifact, SendUserFile.

## Agenti
- Ricerca (a) catalizzatori conclusi: general-purpose, model sonnet (7 min).
- Ricerca (b) notizie, mercati ora, agenda: general-purpose, model sonnet (1,7 min).
- Revisore: general-purpose, model sonnet (2,4 min).

## Revisione
- Affermazioni verificate dal revisore: 17 (limite 20).
- Errori bloccanti segnalati: 9 gruppi, tutti gestiti: dato OPEC (400.000 bpd "da 1,4 milioni") risultato del rapporto di settembre -> tolto da titolo, notizie, catalizzatori e deep dive; Microsoft Maia 300 "lancia" -> riformulato come obiettivo (TheStreet); sei senatori -> mantenuto con attribuzione a TheStreet, che li descrive bipartisan (verificato con WebFetch); Tata/Iveco 28,4% e Unipol-Bper (notizie del 7 e 9/10) -> tolte; FAA -> tolta, Delta confermato da TheStreet; attribuzioni di causa -> tolte o attribuite (ANSA); CdA MPS "alle 18:00" -> "nel tardo pomeriggio, a Borsa chiusa" (ANSA).

## Errori e ripieghi
- FMP `commodity` CLUSD (WTI) e `indexes` intraday: negati dal piano -> WTI da TheStreet (13:19); orario del dato intraday indicato come "17:15 circa".
- Alpha Vantage BRENT: primo tentativo bloccato da limite 1 chiamata/secondo, riuscito al secondo; serie EIA ferma al 6/10 (nessun dato nuovo).
- FMP ^STOXX50E del 12/10 fermo a 6.201,90 (volume 100) anche dopo le 17:27: usato come intraday con asterisco, non come chiusura.
- ACWI: Alpha Vantage non ha ancora il 12/10 -> dato del 9/10.
- Kospi: dato del 12/10 ripreso dall'edizione 1 (nessuna fonte nuova).
- svglib mancante: installato.

## Punti ambigui o impossibili da seguire
1. Struttura "edizione del mattino" in un'esecuzione pomeridiana: il box "Stamattina" è stato rinominato "Nel pomeriggio"; la sezione catalizzatori ("La settimana scorsa | Ieri") è diventata "Oggi: cosa ha mosso i mercati", perché "ieri" (domenica) non ha sedute.
2. Numero 0: `set_meta` calcola il numero dalla data (darebbe 1); forzato `META["edizione"] = 0` nello script, senza toccare il motore. La testata mostra "Edizione n. 000".
3. Nome file: le istruzioni prevedono `nome_file()` con "#NNN"; sostituito dal nome di collaudo.
4. Lunedì con regole martedì-venerdì (scommessa "a che punto siamo", glossario solo sigle nuove): applicate come richiesto; nessun file in `redazione/pronostici` creato o modificato.
5. Chiusure europee: alle 17:30 non ancora disponibili da FMP; le istruzioni non dicono se attendere.
6. Paragrafo 8.3 indica `git add pdf edizioni.json redazione/pronostici`: aggiunto anche `collaudo/esito.md` come da regole di collaudo.
7. Lo strumento "ora corrente" non esiste come tool dedicato: usato `date` con TZ=Europe/Rome.
8. Agenda: i consensi EPS delle banche divergono tra fonti (es. Goldman 13,04 contro 14,84) -> non riportati; ZEW e aste Treasury non confermati -> non inseriti.
9. Il paragrafo 10 vieta di rivedere i numeri di mercato a mano, ma alcuni dati intraday vengono da fonti web (TheStreet, Milano Finanza), non da API.
