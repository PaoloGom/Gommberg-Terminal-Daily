# Appendice - La scommessa del lunedì (o primo giorno di borsa della settimana)

Tutto si lancia da `cd /home/claude/gtd/redazione/scommessa` (perché `dati/`, `registro.csv`, `PAGELLA.md`, `pagella.json` e `../pronostici/` vanno committati). Grafici e PDF in `/home/claude/lavoro`. Registro della settimana: `redazione/pronostici/<data del lunedì>-settimana.json`. Chiavi della scommessa (metodo 1.2, in quest'ordine): `spx sx5e ust10 eurusd brent oro`; in `nuovi.json` anche `vix` e `ust2` (storia); `acwi` solo il 9/11/2026, per il verdetto della settimana 2-6/11 (poi non serve più alla scommessa: il nastro del PDF prende il Mondo da `dati.json`). Numeri, tabelle e pagella li fanno gli script: niente a mano.

## 1. Aggiorna la storia
Scrivi `/home/claude/lavoro/nuovi.json` con le chiusure ufficiali dei giorni dopo l'ultima data di ogni file in `dati/`, fino a venerdì compreso. Formato: `{"spx": [["2026-10-16", 7850.12], ...], ...}`.
- **Temporanea, valida fino al 30/10/2026 (poi togliere):** `dati/sx5e.csv` è già verificato fino al 23/10 (due fonti). Non mettere `sx5e` in `nuovi.json`: FMP `^STOXX50E` non dà la chiusura (livelli sbagliati quasi ogni giorno, anche di segno; ad esempio il 16/10 dà 6.161,9 contro 6.204,23). Il revisore controlla che in pag. 6 l'Euro Stoxx 50 finisca a 6.068,22 (23/10). Venerdì 30/10 la chiusura dell'Euro Stoxx si prende da dpa-AFX "Aktien Europa Schluss" più Investing.com o stoxx.com, concordi entro lo 0,05%.
- `spx`, `sx5e`, `vix`: FMP `indexes` endpoint `index-historical-price-eod-light` (^GSPC, ^STOXX50E, ^VIX) con from/to;
- `brent`: FMP `commodity` endpoint `commodities-historical-price-eod-light`, simbolo BZUSD;
- `ust10`, `ust2`: FMP `economics` endpoint `treasury-rates`, colonne year10 e year2;
- `eurusd`: Alpha Vantage `FX_DAILY`, colonna close (non FMP forex, che ha righe del weekend);
- `oro`: FMP `commodity` endpoint `commodities-historical-price-eod-light`, simbolo GCUSD (seconda fonte: Alpha Vantage `GOLD_SILVER_SPOT`). La chiave vecchia `var_oro` (strumento della settimana 2-6/11) è accettata e finisce nella stessa serie `dati/oro.csv`;
- `acwi`: Alpha Vantage `TIME_SERIES_DAILY`.
- **Mai la riga con la data di oggi:** è un valore intraday. Lo script la rifiuta.
- **Solo chiusure che hanno passato `controlli_dati.py`:** una chiusura del venerdì con volume anomalo (controllo dei volumi) non entra in `nuovi.json` finché una seconda fonte non conferma il livello (il 16/10/2026 FMP ha registrato per l'Euro Stoxx 50 un -0,47% con volume al 7%, mentre l'Europa chiudeva in rialzo).
- Poi: `python3 aggiorna_dati.py /home/claude/lavoro/nuovi.json` (valida tutto prima di scrivere).

## 2. Verdetto della settimana chiusa
`python3 valuta.py --settimana ../pronostici/<lunedì scorso>-settimana.json --verdetto --json /home/claude/lavoro/verdetto.json`
- Venerdì un mercato era chiuso: aggiungi `--festivo <chiavi separate da virgole>` (es. `--festivo ust10,ust2`) o `--festivo tutti`.
- Lo script aggiorna `registro.csv`, `PAGELLA.md` e `pagella.json`. Se si ferma per dati mancanti, aggiorna i dati: non aggirarlo.
- Il verdetto del 9/11/2026 riguarda `2026-11-02-settimana.json`, ancora con il metodo 1.1: servono le chiusure di venerdì 6/11 anche di `acwi` e dell'oro (chiave `oro` o `var_oro`, stessa serie), che quella settimana era lo strumento della settimana. Dal pronostico del 9/11 i fissi sono quelli del metodo 1.2 e l'oro non può più essere lo strumento della settimana.
- Lo strumento della settimana scorsa (se c'era) è nel registro: serve la sua chiusura di venerdì in `nuovi.json` (chiave `var_<chiave>`); il verdetto lo conta a parte.

## 3. Pronostico nuovo
- `python3 pronostico.py --origine <venerdì scorso> --prova`: stampa sigma e i livelli a +-0,1, 0,2 e 0,3 sigma.
- Scrivi `/home/claude/lavoro/redazione.json`: per ognuno dei 6 strumenti di `metodo.json` una previsione e un motivo di una riga. **Spostamento: 0,1 sigma di norma**; fino a 0,3 solo con un catalizzatore datato nella settimana (un dato, una decisione, dei conti) scritto nel motivo; più di 0,3 lo script lo limita. Senza abilità dimostrata, spostarsi di più peggiora la pagella (METODO.md §2); es. `{"spx": {"previsione": 7845, "motivo": "Banche solide e CPI in linea"}, ...}`. Nel motivo niente segni +/- davanti ai numeri. La direzione è obbligatoria ed è la vera scommessa: sceglila guardando agenda, notizie e scenari, non per abitudine.
- `python3 pronostico.py --origine <venerdì scorso> --redazione /home/claude/lavoro/redazione.json`: scrive `../pronostici/<lunedì>-settimana.json`. Non sovrascrive mai un registro esistente; `--forza` solo per correggere un errore della stessa mattina, prima della pubblicazione. Una previsione "AGGIUSTATA": vale il livello del registro e il motivo deve restare vero.

## 3b. Lo strumento della settimana
- Sceglilo sul tema del momento (la top story, il catalizzatore della settimana): un mercato che racconta qualcosa che i 6 fissi e il resto del giornale non dicono. Non un doppione dei fissi né una scommessa doppia sulla stessa notizia.
- Prendi circa un anno di chiusure giornaliere dai nostri dati (FMP `chart`/`commodity`/`indexes`, Alpha Vantage `TIME_SERIES_DAILY`, `FX_DAILY`, `DIGITAL_CURRENCY_DAILY`), mai la riga di oggi, in `/home/claude/lavoro/serie_<chiave>.json` (`[["AAAA-MM-GG", valore], ...]`).
- `python3 variabile.py --chiave <chiave> --nome "<nome per il lettore>" --tipo prezzo --unita "$" --serie /home/claude/lavoro/serie_<chiave>.json --motivo "<perché questa settimana>"`: rifiuta doppioni (correlazione >= 0,7 con un fisso), storia corta e singole azioni nella settimana dei conti (`--conti-in-settimana`). Se rifiuta, scegli un altro mercato.
- Poi il pronostico con `--variabile var_<chiave>` (anche in `--prova`) e in `redazione.json` anche la riga `var_<chiave>`. Mar-ven la sua ultima chiusura va in `attuali.json` con la chiave `var_<chiave>`; il venerdì sera la chiusura entra in `dati/var_<chiave>.csv` con `aggiorna_dati.py` prima del verdetto.

## 4. Grafico e pag. 6
- `python3 grafico.py ../pronostici/<lunedì>-settimana.json /home/claude/lavoro/c_forecast.png` (PNG e SVG).
- Nel modello dell'edizione: `REG = "<lunedì>-settimana.json"` (il registro NUOVO) e
  `C["scommessa"] = {"tesi": "<perché scommettiamo così, 1-2 frasi semplici>", "lunedi": True, "venerdi": False, "settimana_prec": "<es. 2-6 novembre>", "com_e_andata": "<cosa ha deciso la settimana chiusa, una frase semplice, es. La tregua sul petrolio ha portato le borse dove pensavamo; il dollaro no.>"}`. `com_e_andata` è facoltativo ma va scritto quando c'è il verdetto: niente numeri (sono nel riquadro), solo il perché.
  Il motore costruisce pag. 6 del lunedì da registro, `verdetto.json` in `/home/claude/lavoro` e `metodo.json`: tabellone (mercato e la sua domanda, partenza, freccia, forchetta disegnata, il perché), riquadri "Come si gioca" e "Il verdetto" (solo i numeri della settimana chiusa: la stagione è sul sito); senza settimana precedente il riquadro lo dice. Le domande dei fissi sono scritte in `pagina6.py`; quella dello strumento della settimana è il suo `motivo_scelta`: una domanda di **massimo 40 caratteri** (es. "La paura sull'AI è globale?"), altrimenti va a capo. Render: `cd /home/claude/lavoro && python3 edizione_AAAA-MM-GG.py /home/claude/lavoro "<pdf>"`.
- In `edizioni_voce.py` usa `--verdetto /home/claude/lavoro/verdetto.json` e il registro NUOVO: strada e range della settimana nuova restano null.
- Il revisore controlla che tabellone e riquadro "Il verdetto" di pag. 6 riportino esattamente il registro e `verdetto.json`.
- Pag. 1: "La settimana scorsa" al posto di "Ieri in calendario" (max 5 righe); 1 sett. del cruscotto = settimana intera.

## 5. Collaudi e revisione del metodo
- Collaudi: `--prova` per il verdetto (non scrive registro né pagella); pronostico in una cartella fuori dal repository con `--uscita`.
- Ogni 26 settimane (la prima ad aprile 2027), o se la copertura dal vivo in `PAGELLA.md` esce da 55-80% dopo almeno 20 settimane: si rilancia `backtest.py`, si applica la regola di adozione di `metodo.json`, si aggiorna `METODO.md`. Lo fa Claude su richiesta di Paolo, mai l'edizione quotidiana: nel messaggio finale basta una riga che la revisione è dovuta.
