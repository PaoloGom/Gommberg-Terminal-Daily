# Appendice - La scommessa del lunedì (o primo giorno di borsa della settimana)

Tutto si lancia da `cd /home/claude/gtd/redazione/scommessa` (perché `dati/`, `registro.csv`, `PAGELLA.md`, `pagella.json` e `../pronostici/` vanno committati). Grafici e PDF in `/home/claude/lavoro`. Registro della settimana: `redazione/pronostici/<data del lunedì>-settimana.json`. Chiavi della scommessa (metodo 1.2, in quest'ordine): `spx sx5e ust10 eurusd brent oro`; in `nuovi.json` anche `vix` e `ust2` (storia); `acwi` solo il 9/11/2026, per il verdetto della settimana 2-6/11 (poi non serve più alla scommessa: il nastro del PDF prende il Mondo da `dati.json`). Numeri, tabelle e pagella li fanno gli script: niente a mano.

## 1. Aggiorna la storia
Scrivi `/home/claude/lavoro/nuovi.json` con le chiusure ufficiali dei giorni dopo l'ultima data di ogni file in `dati/`, fino a venerdì compreso. Formato: `{"spx": [["2026-10-16", 7850.12], ...], ...}`.
- `sx5e`: mai da FMP (`APP_DATI.md` §6). Le sedute da martedì a giovedì sono già in `dati/sx5e.csv` (le scrive `scommessa_giorno.sh`); in `nuovi.json` va la chiusura di venerdì, da EODHD con una fonte web (`APP_DATI.md` §6).
- `spx`, `vix`: FMP `indexes` endpoint `index-historical-price-eod-light` (^GSPC, ^VIX) con from/to;
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

## 3. Pronostico nuovo (metodo 1.3: prima il mercato, poi la tesi)
- `python3 pronostico.py --origine <venerdì scorso> --prova`: stampa sigma, i livelli a +-0,1, 0,2 e 0,3 sigma e, per ogni mercato, da quale variazione il mattino conta.
- **Il mattino.** Per ognuno dei 6 mercati annota di quanto si è mosso da venerdì sera a stamattina, in `mattino_var` (% per i prezzi, punti base per il Treasury): sono i livelli di "Stamattina" che raccogli comunque (per S&P 500 ed Euro Stoxx 50 il future, per gli altri la quotazione). È un dato indicativo che serve solo a scegliere la direzione: non si stampa come chiusura. Se non è verificabile, ometti il campo.
- **Lo scenario.** In `_scenario` la nostra lettura della settimana, scritta per il lettore: il motore la stampa così com'è nel riquadro "La nostra tesi" di pag. 6. Prima che cosa ci aspettiamo e da quale evento datato dipende, poi `Ci smentirebbe:` e il fatto che ci darebbe torto. È una posizione, non un bivio: sceglie un lato. Si scrive dopo aver guardato il mattino e non si aspetta il contrario di ciò che un mercato ha già fatto. Massimo 200 caratteri, parole di tutti i giorni; lo script rifiuta la forma sbagliata. Le direzioni che scegli tu discendono da lì.
- **La direzione,** mercato per mercato, con il suo `tipo`:
  - `mattino`: il mercato si è già mosso oltre la soglia stampata. La direzione è quella e la previsione la calcola lo script. È la scelta predefinita.
  - `fondo`: mattino fermo, solo su S&P 500, Euro Stoxx 50 e oro: su (salgono in 55-58 settimane su 100). La previsione la calcola lo script.
  - `scenario`: mattino fermo: la direzione che discende dallo scenario, con `previsione` a 0,1 sigma.
  - `catalizzatore`: un evento datato nella settimana (un dato, una decisione, dei conti) scritto nel motivo. È l'unico tipo che può andare contro il mattino, con `previsione` fino a 0,3 sigma. Di norma non più di 2 su 6.
  - Non sono motivi: il rimbalzo dopo un calo e la tendenza delle ultime settimane (bocciati dal backtest, `METODO.md` §3).
- Scrivi `/home/claude/lavoro/redazione.json`, es. `{"_scenario": "...", "spx": {"mattino_var": 0.6, "tipo": "mattino", "motivo": "..."}, "ust10": {"mattino_var": -0.5, "tipo": "scenario", "previsione": 4.85, "motivo": "..."}, ...}`. Il motivo è una riga per il lettore, senza segni +/- davanti ai numeri: il meccanismo che questa settimana spinge quel mercato nella direzione scelta (per `mattino` che cosa l'ha mosso, per gli altri tipi in che verso lo spinge lo scenario o l'evento). Non è un motivo: un'attesa, un evento senza il verso in cui spinge, ciò che il mercato ha già fatto (un rimbalzo, una tendenza), una causa già data a un'altra riga, il ramo che smentirebbe lo scenario.
- **Una settimana sola.** In pag. 6 il lettore legge di fila i sei motivi e, sotto, lo scenario: prima di lanciare lo script rileggili così. Nessuna riga dà per vero il contrario dello scenario o di un'altra riga. Un mercato che lo scenario non tocca ha il suo motivo. Se due mercati che di solito si muovono insieme qui si separano, una delle due righe dice perché.
- `python3 pronostico.py --origine <venerdì scorso> --redazione /home/claude/lavoro/redazione.json`: scrive `../pronostici/<lunedì>-settimana.json`. Se rifiuta un tipo dice perché: correggi `redazione.json`, non aggirarlo. Non sovrascrive mai un registro esistente; `--forza` solo per correggere un errore della stessa mattina, prima della pubblicazione. Una previsione "AGGIUSTATA": vale il livello del registro e il motivo deve restare vero.

## 3b. Lo strumento della settimana
**SOSPESO dal 14/11/2026 (decisione di Paolo): salta questo paragrafo, la scommessa esce con i sei mercati fissi.** In questa fase conta la linearità della lettura, settimana dopo settimana; `pronostico.py` rifiuta `--variabile`. Il paragrafo resta per quando si riprenderà.
- **Non è obbligatorio.** Entra solo se un tema domina la settimana e i sei fissi non lo raccontano; altrimenti la scommessa esce con i sei (il motore impagina da solo). Quando entra: sceglilo sul tema del momento (la top story, il catalizzatore della settimana): un mercato che racconta qualcosa che i 6 fissi e il resto del giornale non dicono. Non un doppione dei fissi né una scommessa doppia sulla stessa notizia.
- Prendi circa un anno di chiusure giornaliere dai nostri dati (FMP `chart`/`commodity`/`indexes`, Alpha Vantage `TIME_SERIES_DAILY`, `FX_DAILY`, `DIGITAL_CURRENCY_DAILY`), mai la riga di oggi, in `/home/claude/lavoro/serie_<chiave>.json` (`[["AAAA-MM-GG", valore], ...]`).
- `python3 variabile.py --chiave <chiave> --nome "<nome per il lettore>" --tipo prezzo --unita "$" --serie /home/claude/lavoro/serie_<chiave>.json --motivo "<perché questa settimana>"`: rifiuta doppioni (correlazione >= 0,7 con un fisso), storia corta e singole azioni nella settimana dei conti (`--conti-in-settimana`). Se rifiuta, scegli un altro mercato.
- Poi il pronostico con `--variabile var_<chiave>` (anche in `--prova`) e in `redazione.json` anche la riga `var_<chiave>`. Mar-ven la sua ultima chiusura va in `attuali.json` con la chiave `var_<chiave>`; il venerdì sera la chiusura entra in `dati/var_<chiave>.csv` con `aggiorna_dati.py` prima del verdetto.

## 4. Grafico e pag. 6
- `python3 grafico.py ../pronostici/<lunedì>-settimana.json /home/claude/lavoro/c_forecast.png` (PNG e SVG).
- Nel modello dell'edizione: `REG = "<lunedì>-settimana.json"` (il registro NUOVO) e
  `C["scommessa"] = {"lunedi": True, "venerdi": False, "settimana_prec": "<es. 2-6 novembre>", "com_e_andata": "<cosa ha deciso la settimana chiusa, una frase semplice, es. La tregua sul petrolio ha portato le borse dove pensavamo; il dollaro no.>"}`. `com_e_andata` è facoltativo ma va scritto quando c'è il verdetto: niente numeri (sono nel riquadro), solo il perché. `tesi` il lunedì non si scrive: il riquadro "La nostra tesi" è lo scenario del registro.
  Il motore costruisce pag. 6 del lunedì da registro, `verdetto.json` in `/home/claude/lavoro` e `metodo.json`: tabellone (mercato e la sua domanda, partenza, freccia, forchetta disegnata, il perché), riquadri "Come si gioca" e "Il verdetto" (solo i numeri della settimana chiusa: la stagione è sul sito); senza settimana precedente il riquadro lo dice. Le domande dei fissi sono scritte in `pagina6.py`; quella dello strumento della settimana è il suo `motivo_scelta`: una domanda di **massimo 40 caratteri** (es. "La paura sull'AI è globale?"), altrimenti va a capo. Render: `cd /home/claude/lavoro && python3 edizione_AAAA-MM-GG.py /home/claude/lavoro "<pdf>"`.
- In `edizioni_voce.py` usa `--verdetto /home/claude/lavoro/verdetto.json` e il registro NUOVO: strada e range della settimana nuova restano null.
- Il revisore controlla che tabellone e riquadro "Il verdetto" di pag. 6 riportino esattamente il registro e `verdetto.json`, e legge di fila i sei perché e "La nostra tesi" come un lettore: segnala una riga che non è un motivo (§3) o che contraddice la tesi o un'altra riga. In quel caso si correggono le parole in `redazione.json` e si rilancia `pronostico.py` con `--forza`: direzioni e numeri restano quelli.
- Pag. 5: `ieri` = la settimana scorsa, in 3 righe al massimo; `agenda` = la settimana che comincia, fino a venerdì: per ogni giorno l'evento che conta di più, in ordine di data, senza fermarsi ai primi giorni (un giorno senza nulla che muove i mercati si salta; un mercato chiuso o a orario ridotto è un evento). Il calendario dell'intera settimana si cerca al passo dei sensori (ISTRUZIONI §4.2). 1 sett. del cruscotto = settimana intera.

## 5. Collaudi e revisione del metodo
- Collaudi: `--prova` per il verdetto (non scrive registro né pagella); pronostico in una cartella fuori dal repository con `--uscita`.
- Ogni 26 settimane (la prima ad aprile 2027), o se la copertura dal vivo in `PAGELLA.md` esce da 55-80% dopo almeno 20 settimane: si rilancia `backtest.py`, si applica la regola di adozione di `metodo.json`, si aggiorna `METODO.md`. Lo fa Claude su richiesta di Paolo, mai l'edizione quotidiana: nel messaggio finale basta una riga che la revisione è dovuta.
