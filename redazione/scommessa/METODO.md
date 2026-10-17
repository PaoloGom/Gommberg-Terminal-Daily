# La Scommessa della settimana - metodo (documento interno)

Versione del metodo: **1.1**, in vigore dal pronostico di lunedì 19/10/2026. Configurazione in `metodo.json`.

**Registro delle versioni.** 1.0 (12/10/2026): 7 strumenti. 1.1 (17/10/2026, prima del primo pronostico ufficiale): tolto il Treasury a 2 anni, che con il 10 anni andava nella stessa direzione il 77% delle settimane (correlazione 0,83): una scommessa doppia. Range invariato (stesso backtest); par da 8,5 su 14 a 7,3 su 12; soglia di direzione senza abilità invariata (53%). Il verdetto della settimana 12-16/10 resta sul registro a 7 strumenti. Aggiunto lo strumento della settimana (sezione 6), con conto a parte. Scartata l'idea di sostituire il 2 anni con la pendenza della curva: corretta statisticamente, ma un concetto da addetti ai lavori come scommessa per i lettori.

## 1. Cosa promettiamo e cosa no
La scommessa chiede, per 6 strumenti, dove sarà la chiusura del venerdì.

Le previsioni di direzione a una settimana hanno poco o nessun potere predittivo, ed è documentato. Lo conferma il nostro backtest (sezione 3). Il valore scientifico della scommessa sta in due cose:
1. **Un range calibrato:** la chiusura cade nel range 16-84% circa 2 settimane su 3. Né molto di più (range troppo larghi, inutili) né molto di meno (range troppo stretti, presuntuosi).
2. **Una misura onesta della redazione:** la direzione la sceglie la redazione e la misuriamo contro il modello senza opinioni. Se in 26 settimane non lo batte in modo significativo, lo diciamo.

## 2. Il modello
- **Orizzonte:** dalla chiusura del venerdì precedente (la "base") alla chiusura del venerdì. Prezzi in log-rendimenti, Treasury in punti base.
- **Previsione puntuale del modello:** la base stessa (passeggiata casuale). Nessun segnale testato la batte (sezione 3).
- **Incertezza, uguale per tutti gli strumenti:**
  - sigma settimanale = deviazione standard delle ultime 20 variazioni giornaliere x radice(5);
  - distribuzione normale;
  - range pubblicato = quantili 16% e 84%, cioè base +- 1 sigma, centrato sulla base.

  È il metodo dell'edizione n. 001, con una differenza: per l'S&P 500 non si usa più il VIX (vedi sotto).
- **Previsione della redazione:** la direzione è obbligatoria per ogni strumento (è una scommessa), con uno spostamento dalla base tra 0,1 e 0,5 sigma e un motivo scritto. Il range non si sposta.
  - **Perché il tetto di 0,5 sigma:** nessun segnale ha mostrato abilità, e uno spostamento più grande sarebbe una scommessa contro l'evidenza.
  - **Probabilità di rialzo pubblicata:** Phi(spostamento/sigma). Va da 54% a 69% se la redazione dice "su", da 31% a 46% se dice "giù".

## 3. Il backtest (`backtest.py`, ultima esecuzione il 12/10/2026, risultati in `backtest/`)
**Dati.** Chiusure giornaliere di circa 20 anni (nel repository pubblico `dati/` tiene solo l'ultimo anno; per rifare il backtest si riscarica lo storico: FMP `index-historical-price-eod-light` e `commodities-historical-price-eod-light` con from 2006-01-01, Alpha Vantage `TREASURY_YIELD` daily e `FX_DAILY` full, e si salvano nello stesso formato in una cartella locale):
- FMP: S&P 500, Euro Stoxx 50, VIX, Brent future;
- Alpha Vantage: Treasury 10 e 2 anni, EUR/USD (i valori coincidono con quelli FMP, verificato su ottobre 2026).

**Valutazione.** Ogni settimana dal 2014-2015 al 2026, 580-620 settimane per strumento.
- A ogni venerdì si usano solo i dati fino a quel giorno.
- Le previsioni puntuali sono stimate su finestra espansiva, con almeno 5 anni di storia.
- Un audit indipendente (12/10) ha rieseguito il codice: nessuna informazione dal futuro, numeri riprodotti.

**Previsione puntuale, contro la passeggiata casuale** (R2 fuori campione; t di Diebold-Mariano: positivo = meglio della passeggiata):

| | S&P 500 | Euro Stoxx 50 | UST 10 | UST 2 | Brent | EUR/USD |
|---|---|---|---|---|---|---|
| Deriva storica | +0,7% (t 1,0) | -0,1% (t -0,4) | -0,2% | +0,1% | -0,3% | -0,3% |
| Inversione dell'ultima settimana | +0,6% (t 0,4) | -0,6% | -0,2% | -0,7% | -0,6% | +0,1% |
| Momentum 12 settimane | +0,9% (t 0,5) | +0,3% | -0,4% | +0,3% | -1,5% | -0,5% |

Nessun |t| supera 1,6, quindi nessun segnale è adottato. Settimane in rialzo: S&P 500 58%, Euro Stoxx 50 55%, altri strumenti circa 50%.

**Range.** Misura: perdita quantile media su 19 livelli (approssima il CRPS), espressa in unità di sigma per poter sommare gli strumenti. Candidati provati:
- volatilità a 20 e 60 sedute;
- EWMA con lambda 0,94 e 0,97;
- miscela 70% EWMA + 30% volatilità di 3 anni;
- VIX (solo S&P 500);
- forme: normale, Student-t 5, empirica (quantili centrati).

Risultati:
- **Calibrazione del metodo in vigore.** Il range 16-84% contiene la chiusura nel 68-72% delle settimane su tutti gli strumenti: è calibrato. La banda 5-95% ne contiene l'87-88%, un po' meno del 90%: le code sono più spesse della normale. Per questo il grafico pubblica solo il 16-84%.
- **VIX per l'S&P 500, scartato.** Copre l'81,5% delle settimane (atteso 68%): range troppo larghi, perché il VIX incorpora il premio per il rischio di volatilità. Torna alla volatilità a 20 sedute come gli altri strumenti.
- **Miscela + Student-t 5, il migliore e "in osservazione".**
  - Migliora 6 strumenti su 6, di poco (0,3-1,0%), e porta la banda 5-95% al 90-92%.
  - Il test aggregato però non supera la soglia: t 1,6, e dal 2020 t 0,8. Con circa 15 combinazioni provate per strumento, un t intorno a 2 su un solo strumento è atteso anche per puro caso (un'adozione spuria su sei strumenti).
  - Quindi non si adotta.
- **Correzione dopo l'audit.** Una prima versione del backtest dava come vincente la forma "empirica" su S&P 500 ed Euro Stoxx 50. Il guadagno veniva dalla deriva reintrodotta di nascosto: i quantili delle sorprese non erano centrati. Centrandoli, il vantaggio sparisce (S&P da +2,6% a +0,1%).

## 4. Come si misura
- **Per i lettori:** 1 punto per la direzione giusta e 1 punto se la chiusura cade nel range, massimo 12 a settimana.
  - **Par**, cioè il punteggio atteso senza abilità: circa 7,3 su 12 (8,5 su 14 nella settimana 12-16/10, a 7 strumenti).
  - Il par tiene conto che sugli azionari "sempre su" indovina il 55-58% delle settimane (`par_direzione` in `metodo.json`).
- **Per noi** (`valuta.py`, che scrive `registro.csv` e `PAGELLA.md`):
  - copertura reale del range: obiettivo 68%;
  - sorprese oltre 2 sigma: circa 5% se la normale regge, di più se le code sono spesse;
  - direzione della redazione sugli azionari contro il riferimento "sempre su";
  - abilità della redazione sul modello: perdita quantile in unità di sigma della distribuzione spostata contro quella non spostata;
  - test di Diebold-Mariano dopo 26 settimane.
- **Verdetto sulla redazione:**
  - dopo 26 settimane, se t >= 2 gli spostamenti aggiungono valore;
  - se t <= -2 peggiorano la previsione: si riducono a 0,1 sigma (direzione sì, convinzione no) finché il record non cambia;
  - tra -2 e 2 nessuna conclusione, si continua.

## 5. Come migliora, senza aggiungere rumore
- **Regola di adozione,** fissata prima di guardare i dati nuovi. È in `metodo.json` e richiede, fuori campione, una di queste due condizioni:
  - **Specifica unica per tutti:** t di Diebold-Mariano aggregato >= 2 e positivo anche solo dal 2020.
  - **Eccezione per un singolo strumento:** t >= 2,9 (correzione di Bonferroni per circa 15 candidati) e miglioramento dal 2020.
- **Tra più candidati che passano:** vince il t più alto.
- **Difetti di calibrazione:** si correggono anche senza test di perdita (copertura del 68% fuori da 63-73% su almeno 300 settimane).
- **Candidati falliti:** restano scritti qui, per non riprovarli all'infinito.
- **Cadenza:**
  - ogni lunedì `aggiorna_dati.py` aggiunge le chiusure della settimana;
  - ogni 26 settimane (la prima ad aprile 2027) si rilancia `backtest.py` e si confronta la `PAGELLA.md` dal vivo con il backtest;
  - **allarme:** se la copertura dal vivo esce da 55-80% dopo almeno 20 settimane, si anticipa la revisione.
- **Da non fare.** Aggiungono parametri senza potere statistico:
  - ottimizzare lambda o i pesi per strumento;
  - stimare i gradi di libertà per strumento;
  - range speciali nelle settimane di banca centrale;
  - GARCH, salvo che superi la regola.

## 6. Limiti noti
- Il Brent è la serie continua del future: al cambio di contratto può esserci un salto che non è un movimento di mercato. Il verdetto lo segnala se la variazione supera 3 sigma, nel campo `nota`.
- La base è la chiusura di venerdì, ma il pronostico esce lunedì mattina: le notizie del weekend entrano solo tramite la scelta di direzione della redazione.
- Treasury: le chiusure Alpha Vantage arrivano con un giorno di ritardo; per la base e il verdetto valgono quelle FMP del giorno.
- Venerdì festivo (es. Venerdì Santo): il verdetto si lancia con `--festivo`, usa l'ultima chiusura della settimana e lo scrive nel campo `nota`. Senza `--festivo`, una chiusura mancante blocca il verdetto, per non scrivere mai un risultato con dati vecchi.

## 7. Registro delle versioni
- **0** (edizione n. 001, 12/10/2026):
  - range con la volatilità di 20 sedute (VIX per l'S&P 500) e distribuzione normale;
  - previsione della redazione senza limiti.

  Il suo file è `pronostici/2026-10-12-settimana.json`, con i quantili del modello 1.0 ricostruiti per confronto usando solo dati fino al 9/10. Il file storico originale è `2026-10-12-settimana-12-16-ottobre.json`.
- **1.0** (dal 19/10/2026):
  - stesso metodo per tutti (20 sedute, normale, +-1 sigma);
  - l'S&P 500 lascia il VIX;
  - previsione del modello = base;
  - direzione obbligatoria della redazione tra 0,1 e 0,5 sigma;
  - punteggi in unità di sigma e pagella;
  - controlli bloccanti su date e dati vecchi.

## 6. Lo strumento della settimana (dal 19/10/2026)
- **Cosa:** ogni lunedì, oltre ai 6 fissi, un settimo mercato scelto sul tema del momento (oro, Nikkei, Bitcoin, un'azione, il gas...), con lo stesso gioco: chiusura di partenza, previsione della redazione, forchetta del modello (rv20, normale), on track, verdetto. Conto e pagella a parte (`pagella.json` campo "variabile"), così la pagella dei fissi resta confrontabile.
- **Ammissione (`variabile.py`):** serie giornaliera dai nostri dati gratuiti (FMP o Alpha Vantage), almeno 60 sedute; nessun doppione: correlazione delle variazioni settimanali dell'ultimo anno sotto 0,7 in valore assoluto con ognuno dei fissi (il Nasdaq contro l'S&P 500, il VIX contro le borse e il 2 anni contro il 10 anni non passano: verificato il 17/10); niente singole azioni nella settimana dei loro conti (forchetta troppo stretta).
- **Scelta:** parla con il tema della settimana e dice qualcosa che i 6 fissi e il resto del giornale non dicono; il motivo della scelta è scritto nel registro (`motivo_scelta`).
- **Registro:** la riga dello strumento ha `"variabile": true` nel registro della settimana; `pronostico.py --variabile var_<chiave>`.
