# Registro dei lavori: contratto dei dati

La pagina (`redazione/registro/index.html`) legge tutto e scrive solo due cose: un documento `clic` per ogni tocco di Paolo (più il campo `lancio` di quel clic) e gli `appunti` nuovi. Tutto il resto, `tasks` e `meta/piano` compresi, lo scrive solo il capo sviluppo: ogni dato ha un solo scrittore.

## Messa in linea, in quest'ordine

1. Creare l'attività programmata del capo sviluppo (una sola, lanciata dai clic e da un giro fisso ogni sera) e scrivere `meta/capo` = {`attivita`: id dell'attività, `giro`: orario del giro in parole, es. "19:47"}.
2. Dichiarare le capacità della pagina: `db`, `user` e `mcp` con il connettore "Claude Code Remote" (e "Claude_Code_Remote"), strumento `fire_trigger`.
3. Pubblicare la pagina.

Senza `meta/capo.attivita` la pagina non mostra i tasti che lanciano lavoro (Via al piano, Ok, Non ancora, Usa il margine, Torna indietro) e dice "Il capo sviluppo non è ancora collegato"; Togli e Aggiungi restano, perché scrivono soltanto.

## Raccolte

| Dove | Chi scrive | Stato |
|---|---|---|
| `tasks/<id>` | capo sviluppo | esisteva |
| `serate/<id>` | nessuno (storico in sola lettura) | esisteva |
| `appunti/<id>` = {`testo`, `creato`, `stato` (`nuovo`, `assorbito`), `voce`} | pagina (nuovi), capo sviluppo (assorbiti) | esisteva |
| `rilasci/<id>` | nessuno (storico) | esisteva |
| `meta/salute` = {`verificato`, `righe`, `rilasci`} | capo sviluppo | esisteva; facoltativi nuovi in `rilasci[]`: `lettore` (una riga), `verificato` (vero o falso) |
| `meta/stato` = {`lettori`, `edizioni`, `prossimo`} | capo sviluppo | esisteva; mostrato in Dietro le quinte |
| `meta/piano` = {`settimana` (AAAA-MM-GG, il primo giorno), `titolo`, `voci` (codici), `tolte` (codici), `via` ({`quando`, `clic`} o null)} | solo capo sviluppo | nuovo |
| `meta/capo` = {`attivita`, `giro`} | capo sviluppo | nuovo |
| `clic/<id>` | pagina; il capo sviluppo `esito`, `nota`, `chiuso` | nuova |

`meta/giro` la pagina non lo legge più. Un piano mai avviato la cui settimana è passata (sette giorni dopo `settimana`) non compare in Oggi: Dietro le quinte lo segnala come "piano scaduto".

## Campi delle voci (`tasks`)

Letti come prima: `codice`, `titolo`, `stato`, `priorita`, `ordine`, `giorno`, `chiusa`, `scadenza`, `chi`, `input`, `obiettivo` (mostrato come "Perché"), `decisioni`, `domanda`, `modello` (assente = "Da decidere"), `sforzo`, `finestra`.
Nuovi, tutti facoltativi:
- `livello`: `sola` (Da sola), `via` (Con il tuo via), `visto` (Via + Visto). Assente = `visto`.
- `cosa`: una riga. Assente = `titolo`.
- `lettore`: che cosa cambia per il lettore, una riga. Assente = "Da scrivere".
- `riserva`: `true` se la voce è nella riserva del margine.
- `ferma`: la causa in una frase, se il lavoro è fermo.
- `anteprima`: link `https://` a ciò che Paolo deve vedere.

Priorità: `max`, `high`, `medium`, `low`, `tbd` (mostrata come Idea); i vecchi numeri 1, 2, 3 valgono high, medium, low; `stato: "idea"` vale tbd. A parità di priorità viene prima la `scadenza` più vicina; la scadenza si vede come "entro il 24/12".

## Chi aspetta Paolo (regola unica, `aspettaPaolo`)

Una voce non fatta sta in "Tocca a te" se ha una `domanda`, oppure `chi` è `Paolo`, oppure `input` è `decisione` (con `chi` diverso da Claude), come nella pagina di oggi (`chi: "Paolo"` vale `input: "azione"`; con `chi: "Claude"` l'`input` non conta; `approvazione` conta solo con una `domanda`). La richiesta resta in Tocca a te anche se la voce è Ferma o aspetta la prova, con lo stato scritto accanto. Senza `domanda` la voce dice "Azione tua" e apre la scheda. Con `stato: "pronta"` e una `domanda`, e nessuna prova da fare, è una voce *Da vedere* con Ok e Non ancora. Chiusa la domanda, il capo sviluppo la toglie.

## Stati detti a Paolo (funzione `statoVoce`, il primo che vale)

1. `stato` `fatta` → **Fatta**
2. `ferma` non vuoto, o prova della serata `con-prova` con esito `ko` → **Ferma** (con la causa)
3. codice nelle righe di una serata `con-prova` con prova non ancora `ok` → **Aspetta la prova** (con il giorno)
4. aspetta Paolo → **Tocca a te**
5. `stato` `in-corso`, o un clic Ok / Non ancora `in-lavoro` → **Al lavoro**
6. `stato` `pronta`, o un clic Ok / Non ancora `da-eseguire` → **In coda**
7. in `meta/piano.voci`, non in `tolte` e senza un clic `togli` aperto → **In piano**; **In coda** se il piano è avviato o c'è un clic `via-piano` aperto
8. `riserva` con un clic `margine` aperto → **In coda**
9. priorità `tbd` → **Idea**
10. altrimenti → **Più avanti**

## Un documento `clic`

```
{ chi: "Paolo", da: "Registro", quando: ISO 8601,
  tipo: "via-piano" | "ok" | "non-ancora" | "togli" | "margine" | "appunto" | "indietro",
  voce: codice, o nome del rilascio per indietro, o "",  piano: settimana o "",
  testo: nota di Paolo, percentuale del margine ("30%") o testo dell'appunto, oppure "",
  rif: "appunti/<id>" per un appunto, altrimenti "",
  esito: "da-eseguire" | "in-lavoro" | "eseguito" | "scartato",  nota, chiuso: ISO 8601,
  lancio: { esito: "partito" | "coda" | "incerto" | "bloccato", quando, errore, connettore } }
```
La pagina scrive il clic, poi chiama `fire_trigger` sull'attività di `meta/capo.attivita` con `text: "clic/<id>"` (nient'altro), poi aggiunge `lancio`. `togli` e `appunto` non lanciano nulla. Che cosa dice la pagina:
- `partito`: "Partito"; se dopo 15 minuti l'esito è ancora `da-eseguire`, "Non ancora preso in carico" con Riprova.
- `coda` (nessun connettore, errore del lancio): "In coda: parte al giro delle <giro>".
- `incerto` (`server_unavailable`, `upstream_error`): "Non so se è partito", con Riprova; mai ritentato da solo.
- `bloccato` (`needs_reauth`, `server_not_connected`: ricollegare il connettore; `approval_required`, `consent_required`, `not_in_manifest`: dare il permesso; `selection_required`, `blocked_by_policy`): la frase e il tasto per rilanciare.
- `in-lavoro`: "Al lavoro". `eseguito` o `scartato`: una riga in Oggi con l'esito e la `nota`, per 24 ore da `chiuso` o finché Paolo non la chiude.
Riprova rilancia lo stesso clic: non ne scrive un altro.

## Che cosa fa il capo sviluppo

Lanciato da un clic (`text` = `clic/<id>`) o dal giro della sera, legge tutti i `clic` con `esito: "da-eseguire"`, dal più vecchio, uno alla volta. Per ognuno, come PRIMA cosa, lo prende scrivendo `esito: "in-lavoro"` con `ifVersion` sulla versione letta: se la versione è cambiata o l'esito non è più `da-eseguire`, passa oltre senza fare nulla (così un clic lanciato due volte, dal tasto e dal giro, o con Riprova, si esegue una volta sola). Poi:
- `via-piano`: scrive `meta/piano.via` = {`quando`, `clic`} e lavora le voci del piano meno `tolte`, secondo il livello.
- `ok`: manda in linea la voce (il consenso è questo clic), poi toglie `domanda`.
- `non-ancora`: non va in linea; legge `testo`, riprende la voce, riscrive `domanda` quando la ripropone.
- `togli`: aggiunge il codice a `meta/piano.tolte` se il piano è ancora quello di `piano` e non è avviato; altrimenti scarta.
- `margine`: lavora la riserva in ordine, fermandosi prima della percentuale indicata (vuota = prudenza); edizioni e prova vengono prima.
- `appunto`: se `appunti/<rif>` manca lo crea dal `testo`; lo porta nel piano successivo e lo segna `assorbito`.
- `indietro`: si scarta se `voce` non è più l'ultimo rilascio in `meta/salute.rilasci`; altrimenti annulla il rilascio, verifica dal vivo, aggiorna `meta/salute`.
Alla fine scrive `esito: "eseguito"` oppure `"scartato"`, `nota` (una frase) e `chiuso`. Il giro della sera fa la stessa cosa sui clic rimasti `da-eseguire` (quelli in coda o non presi), poi le sue verifiche. Tutte le scritture del capo sviluppo: con `db_write` e `ifVersion`, solo sui campi che cambia.
