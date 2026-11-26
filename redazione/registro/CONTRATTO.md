# Registro dei lavori: contratto dei dati

La pagina (`redazione/registro/index.html`) legge tutto e scrive poco: un documento `clic` per ogni tocco di Paolo, gli `appunti` e il solo campo `tolte` di `meta/piano`. Le schede (`tasks`) le scrive solo il capo sviluppo. Database: artifact del Registro, stessa base di oggi.

## Raccolte

| Dove | Chi scrive | Stato |
|---|---|---|
| `tasks/<id>` | capo sviluppo | esisteva |
| `serate/<id>` | nessuno (storico in sola lettura) | esisteva |
| `appunti/<id>` = {`testo`, `creato`, `stato` (`nuovo`, `assorbito`), `voce`} | pagina (nuovi), capo sviluppo (assorbiti) | esisteva |
| `rilasci/<id>` | nessuno (storico) | esisteva |
| `meta/salute` = {`verificato`, `righe`, `rilasci`} | capo sviluppo | esisteva; facoltativi nuovi in `rilasci[]`: `lettore` (una riga), `verificato` (vero o falso) |
| `meta/piano` = {`settimana` (AAAA-MM-GG), `titolo`, `voci` (codici), `tolte` (codici), `via` ({`quando`, `clic`} o null)} | capo sviluppo; la pagina solo `tolte` | nuovo |
| `meta/capo` = {`attivita` (id dell'attività programmata del capo sviluppo)} | capo sviluppo | nuovo |
| `clic/<id>` | pagina; il capo sviluppo `esito` e `nota` | nuova |

`meta/stato` e `meta/giro` la pagina non li legge più.

## Campi delle voci (`tasks`)

Usati come prima: `codice`, `titolo`, `stato`, `priorita`, `ordine`, `giorno`, `chiusa`, `obiettivo` (mostrato come "Perché"), `decisioni`, `domanda`, `modello`, `sforzo`, `finestra`.
Nuovi, tutti facoltativi (la pagina funziona senza):
- `livello`: `sola` (Da sola), `via` (Con il tuo via), `visto` (Via + Visto). Assente = `visto`.
- `cosa`: una riga. Assente = `titolo`.
- `lettore`: che cosa cambia per il lettore, una riga. Assente = "Da scrivere".
- `riserva`: `true` se la voce è nella riserva del margine.
- `ferma`: la causa in una frase, se il lavoro è fermo. Vuoto = non fermo.
- `anteprima`: link `https://` a ciò che Paolo deve vedere.

Priorità: `max`, `high`, `medium`, `low`, `tbd` (mostrata come Idea); i vecchi numeri 1, 2, 3 valgono high, medium, low; `stato: "idea"` vale tbd.

## Stati detti a Paolo (funzione `statoVoce`, il primo che vale)

1. `stato` `fatta` → **Fatta**
2. `ferma` non vuoto, o prova della serata `con-prova` con esito `ko` → **Ferma** (con la causa)
3. codice nelle righe di una serata `stato: "con-prova"` → **Aspetta la prova** (con il giorno)
4. `domanda` non vuota → **Tocca a te**: con `stato` `pronta` è una voce *Da vedere* (Ok / Non ancora), altrimenti una domanda con "Rispondi nella chat"
5. `stato` `in-corso` → **Al lavoro**
6. `stato` `pronta`, o un clic Ok / Non ancora non ancora eseguito → **In coda**
7. in `meta/piano.voci` e non in `tolte` → **In piano**; **In coda** se il piano è avviato (`via`) o c'è un clic `via-piano` da eseguire
8. `riserva` con un clic `margine` da eseguire → **In coda**
9. priorità `tbd` → **Idea**
10. altrimenti → **Più avanti**

Il piano compare in Tocca a te solo se esiste e `via` è vuoto. Quindi: un'attività deve togliere `domanda` quando la domanda è chiusa, mettere `in-corso` solo quando qualcuno lavora davvero, e scrivere `ferma` quando si blocca.

## Un documento `clic`

```
{ chi: "Paolo", da: "Registro", quando: ISO 8601,
  tipo: "via-piano" | "ok" | "non-ancora" | "togli" | "margine" | "appunto" | "indietro",
  voce: codice o nome del rilascio (indietro) o "", piano: settimana o "",
  testo: nota di Paolo, percentuale del margine ("30%") o testo dell'appunto, oppure "",
  rif: "appunti/<id>" per un appunto, altrimenti "",
  esito: "da-eseguire",
  lancio: { esito: "partito" | "coda" | "incerto", quando, errore, connettore } }
```
La pagina scrive il clic prima di tutto, poi prova `fire_trigger` sull'attività di `meta/capo.attivita` con `text: "clic/<id>"` (nient'altro), poi aggiunge `lancio`. `togli` e `appunto` non lanciano nulla e non hanno `lancio`. Finché `esito` è `da-eseguire` il tasto non ricompare.

## Che cosa fa il capo sviluppo con i clic

All'avvio (lanciato da un clic o dal suo giro) legge tutti i `clic` con `esito: "da-eseguire"`, dal più vecchio, uno alla volta:
- `via-piano`: scrive `meta/piano.via` = {`quando`, `clic`} e lavora le voci del piano meno `tolte`, secondo il livello.
- `ok`: manda in linea la voce (il consenso è questo clic), poi toglie `domanda`.
- `non-ancora`: non va in linea; legge `testo`, riprende la voce, riscrive `domanda` quando la ripropone.
- `togli`: si assicura che il codice sia in `meta/piano.tolte` (la pagina può non esserci riuscita).
- `margine`: lavora la riserva in ordine, fermandosi prima della percentuale indicata (vuota = prudenza); edizioni e prova vengono prima.
- `appunto`: se `appunti/<rif>` manca lo crea dal `testo`; lo porta nel piano successivo e lo segna `assorbito`.
- `indietro`: annulla l'ultimo rilascio, verifica dal vivo, aggiorna `meta/salute`.
Poi scrive sul clic `esito: "eseguito"` oppure `"scartato"` con `nota` (una frase). Un clic con `lancio.esito: "partito"` può arrivare due volte (clic e giro): chi lo prende prima lo segna, chi arriva dopo trova `esito` cambiato e passa oltre.

Scritture del capo sviluppo: con `db_write` e `ifVersion`, solo sui campi che cambia. La pagina non può usare `ifVersion` (il suo database non lo offre): prima di scrivere `tolte` rilegge `meta/piano` e scrive solo se `settimana` è la stessa, `via` è vuoto e la voce c'è; altrimenti scarta il clic.
