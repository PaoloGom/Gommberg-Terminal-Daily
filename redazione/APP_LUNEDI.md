# Appendice - La scommessa del lunedì (o primo giorno di borsa della settimana)

Tutto si lancia da `cd /home/claude/gtd/redazione/scommessa` (perché `dati/`, `registro.csv`, `PAGELLA.md`, `pagella.json` e `../pronostici/` vanno committati). Grafici e PDF in `/home/claude/lavoro`. Registro della settimana: `redazione/pronostici/<data del lunedì>-settimana.json`. Chiavi: `acwi spx sx5e ust10 ust2 brent eurusd` (più `vix` solo in `nuovi.json`). Numeri, tabelle e pagella li fanno gli script: niente a mano.

## 1. Aggiorna la storia
Scrivi `/home/claude/lavoro/nuovi.json` con le chiusure ufficiali dei giorni dopo l'ultima data di ogni file in `dati/`, fino a venerdì compreso. Formato: `{"spx": [["2026-10-16", 7850.12], ...], ...}`.
- `spx`, `sx5e`, `vix`: FMP `indexes` endpoint `index-historical-price-eod-light` (^GSPC, ^STOXX50E, ^VIX) con from/to;
- `brent`: FMP `commodity` endpoint `commodities-historical-price-eod-light`, simbolo BZUSD;
- `ust10`, `ust2`: FMP `economics` endpoint `treasury-rates`, colonne year10 e year2;
- `eurusd`: Alpha Vantage `FX_DAILY`, colonna close (non FMP forex, che ha righe del weekend);
- `acwi`: Alpha Vantage `TIME_SERIES_DAILY`.
- **Mai la riga con la data di oggi:** è un valore intraday. Lo script la rifiuta.
- Poi: `python3 aggiorna_dati.py /home/claude/lavoro/nuovi.json` (valida tutto prima di scrivere).

## 2. Verdetto della settimana chiusa
`python3 valuta.py --settimana ../pronostici/<lunedì scorso>-settimana.json --verdetto --json /home/claude/lavoro/verdetto.json`
- Venerdì un mercato era chiuso: aggiungi `--festivo <chiavi separate da virgole>` (es. `--festivo ust10,ust2`) o `--festivo tutti`.
- Lo script aggiorna `registro.csv`, `PAGELLA.md` e `pagella.json`. Se si ferma per dati mancanti, aggiorna i dati: non aggirarlo.
- Il primo verdetto del metodo 1.0 (19/10/2026) riguarda `2026-10-12-settimana.json`.

## 3. Pronostico nuovo
- `python3 pronostico.py --origine <venerdì scorso> --prova`: stampa sigma e i livelli a +-0,1, 0,3 e 0,5 sigma.
- Scrivi `/home/claude/lavoro/redazione.json`: per ognuno dei 7 strumenti una previsione dentro quei limiti e un motivo di una riga, es. `{"spx": {"previsione": 7845, "motivo": "Banche solide e CPI in linea"}, ...}`. Nel motivo niente segni +/- davanti ai numeri. La direzione è obbligatoria ed è la vera scommessa: sceglila guardando agenda, notizie e scenari, non per abitudine.
- `python3 pronostico.py --origine <venerdì scorso> --redazione /home/claude/lavoro/redazione.json`: scrive `../pronostici/<lunedì>-settimana.json`. Non sovrascrive mai un registro esistente; `--forza` solo per correggere un errore della stessa mattina, prima della pubblicazione. Una previsione "AGGIUSTATA": vale il livello del registro e il motivo deve restare vero.

## 4. Grafico e pag. 6
- `python3 grafico.py ../pronostici/<lunedì>-settimana.json /home/claude/lavoro/c_forecast.png` (PNG e SVG).
- Nel modello dell'edizione: `REG = "<lunedì>-settimana.json"` (il registro NUOVO) e
  `C["scommessa"] = {"tesi": "<la tesi della settimana in una frase>", "lunedi": True, "venerdi": False, "settimana_prec": "<es. 12-16 ottobre>"}`.
  Il motore costruisce pag. 6 del lunedì (box "Le regole del gioco" completo) da `verdetto.json` in `/home/claude/lavoro` e da `redazione/scommessa/pagella.json`; senza settimana precedente il verdetto manca e la pagella lo dice. Render: `cd /home/claude/lavoro && python3 edizione_AAAA-MM-GG.py /home/claude/lavoro "<pdf>"`.
- In `edizioni_voce.py` usa `--verdetto /home/claude/lavoro/verdetto.json` e il registro NUOVO: strada e range della settimana nuova restano null.
- Il revisore controlla che tabella e pagella di pag. 6 riportino esattamente `verdetto.json` e il registro.
- Pag. 1: "La settimana scorsa" al posto di "Ieri in calendario" (max 5 righe); 1 sett. del cruscotto = settimana intera.

## 5. Collaudi e revisione del metodo
- Collaudi: `--prova` per il verdetto (non scrive registro né pagella); pronostico in una cartella fuori dal repository con `--uscita`.
- Ogni 26 settimane (la prima ad aprile 2027), o se la copertura dal vivo in `PAGELLA.md` esce da 55-80% dopo almeno 20 settimane: si rilancia `backtest.py`, si applica la regola di adozione di `metodo.json`, si aggiorna `METODO.md`. Lo fa Claude su richiesta di Paolo, mai l'edizione quotidiana: nel messaggio finale basta una riga che la revisione è dovuta.
