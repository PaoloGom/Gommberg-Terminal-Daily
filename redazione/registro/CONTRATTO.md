# Registro dei lavori: contratto dei dati

La pagina (`redazione/registro/index.html`) legge tutto e scrive solo due cose: un documento `clic` per ogni tocco di Paolo (più il campo `lancio` di quel clic) e gli `appunti` nuovi. Tutto il resto, `tasks` e `meta/piano` compresi, lo scrive solo il capo sviluppo: ogni dato ha un solo scrittore.

## Messa in linea, in quest'ordine

1. Creare l'attività programmata del capo sviluppo (una sola, lanciata dai clic e da un giro fisso ogni sera) e scrivere `meta/capo` = {`attivita`: id dell'attività, `giro`: orario del giro in parole, es. "19:47"}.
2. Il capo sviluppo riporta la prova della serata aperta `2026-11-25-2` sulle voci G-45, G-54 e G-50 (`prova` = {`giorno`: "2026-11-27", `esito`: "da-fare"}): dopo, la pagina non guarda più le serate per decidere lo stato.
3. Dichiarare le capacità della pagina: `db`, `user` e `mcp` con il connettore "Claude Code Remote" (e "Claude_Code_Remote"), strumento `fire_trigger`.
4. Pubblicare la pagina.

Senza `meta/capo.attivita` la pagina non mostra i tasti che lanciano lavoro (Via al piano, Ok, Non ancora, Usa il margine, Torna indietro) e dice "Il capo sviluppo non è ancora collegato"; Togli e Aggiungi restano, perché scrivono soltanto.

## Raccolte

| Dove | Chi scrive | Stato |
|---|---|---|
| `tasks/<id>` | capo sviluppo | esisteva |
| `serate/<id>` | nessuno: solo storico in Dietro le quinte (letti `stato`, `ramo`, `dopo.righe` o `prima.righe` con `codice` e `cosa`, `fine.testo`, `nota`, `ferma.nota`) | esisteva |
| `appunti/<id>` = {`testo`, `creato`, `stato` (`nuovo`, `assorbito`), `voce`} | pagina (nuovi), capo sviluppo (assorbiti) | esisteva |
| `rilasci/<id>` | nessuno: storico (letti `nome`, `aggiornato`, `stato`, `sintesi`) | esisteva |
| `meta/salute` = {`verificato`, `righe`: [{`nome`, `stato`, `testo`, `causa`, `rimedio`}], `rilasci`: [{`nome`, `quando`, `esito`, `testo`}]} | capo sviluppo | esisteva; la riga con `nome: "Edizione"` dà la pillola in alto; `rilasci` è ordinato dal più recente; facoltativi nuovi in `rilasci[]`: `lettore` (una riga), `verificato` (vero o falso) |
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
- `prova`: {`giorno`, `esito` (`da-fare`, `ok`, `ko`), `nota` facoltativa} per il lavoro che aspetta l'edizione di prova. È l'unico posto della prova: lo scrive il capo sviluppo.

Priorità: `max`, `high`, `medium`, `low`, `tbd` (mostrata come Idea); i vecchi numeri 1, 2, 3 valgono high, medium, low; `stato: "idea"` vale tbd. A parità di priorità viene prima la `scadenza` più vicina; la scadenza si vede come "entro il 24/12".

## Chi aspetta Paolo (regola unica, `aspettaPaolo`)

Una voce non fatta sta in "Tocca a te" se ha una `domanda`, oppure `chi` è `Paolo`, oppure `input` è `decisione` (con `chi` diverso da Claude), come nella pagina di oggi (`chi: "Paolo"` vale `input: "azione"`; con `chi: "Claude"` l'`input` non conta; `approvazione` conta solo con una `domanda`). La richiesta resta in Tocca a te anche se la voce è Ferma o aspetta la prova, con lo stato scritto accanto. Senza `domanda` la voce dice "Azione tua" e apre la scheda. Con `stato: "pronta"` e una `domanda`, e nessuna prova da fare, è una voce *Da vedere* con Ok e Non ancora. Chiusa la domanda, il capo sviluppo la toglie.

## Stati detti a Paolo (funzione `statoVoce`, il primo che vale)

1. `stato` `fatta` → **Fatta**
2. `ferma` non vuoto, o `prova.esito` `ko` → **Ferma** (con la causa)
3. `prova.esito` `da-fare` → **Aspetta la prova** (con il giorno); con `ok` la voce torna allo stato che le spetta
4. aspetta Paolo → **Tocca a te**
5. `stato` `in-corso`, o un clic Ok / Non ancora `in-lavoro` → **Al lavoro**
6. `stato` `pronta`, o un clic Ok / Non ancora `da-eseguire` → **In coda**
7. in `meta/piano.voci`, non in `tolte` e senza un clic `togli` aperto dato per quella stessa settimana (`piano`) → **In piano**; **In coda** se il piano è avviato o c'è un clic `via-piano` aperto
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
  preso: { quando, aggiornato }   (ISO 8601 con Z, scritti dal capo sviluppo),
  lancio: { esito: "partito" | "coda" | "incerto" | "bloccato", quando, errore, connettore } }
```
La pagina scrive il clic, poi chiama `fire_trigger` sull'attività di `meta/capo.attivita` con `text: "clic/<id>"` (nient'altro), poi aggiunge `lancio`. `togli` e `appunto` non lanciano nulla. Che cosa dice la pagina:
- `partito`: "Partito"; se dopo 15 minuti l'esito è ancora `da-eseguire`, "Non ancora preso in carico" con Riprova.
- `coda` (nessun connettore, errore del lancio): "In coda: parte al giro delle <giro>".
- `incerto` (`server_unavailable`, `upstream_error`): "Non so se è partito", con Riprova; mai ritentato da solo.
- `bloccato` (`needs_reauth`, `server_not_connected`: ricollegare il connettore; `approval_required`, `consent_required`, `not_in_manifest`: dare il permesso; `selection_required`, `blocked_by_policy`): la frase e il tasto per rilanciare.
- `in-lavoro`: "Al lavoro"; se `preso.aggiornato` ha più di 60 minuti, "Fermo da <tempo>: nessun segnale" con Riprova.
- `da-eseguire` mentre un altro clic è `in-lavoro` con segnale fresco: "In coda: parte appena finisce il lavoro in corso", senza la scadenza dei 15 minuti. `eseguito` o `scartato`: una riga in Oggi con l'esito e la `nota`, per 24 ore da `chiuso` o finché Paolo non la chiude.
Riprova rilancia lo stesso clic: non ne scrive un altro.

## Che cosa fa il capo sviluppo

Lanciato da un clic (`text` = `clic/<id>`) o dal giro della sera. Un solo capo sviluppo al lavoro, in quest'ordine:
a. All'avvio cerca clic `in-lavoro` con segnale fresco (`preso.aggiornato` di meno di 60 minuti): se ce n'è uno, esce senza prendere nulla (il suo clic resta `da-eseguire`: lo farà chi lavora).
b. Altrimenti prende il clic più vecchio fra i `da-eseguire` e fra gli `in-lavoro` senza segnale da più di 60 minuti: scrive `esito: "in-lavoro"` e `preso` = {`quando`, `aggiornato`} con `ifVersion` sulla versione letta. Se `ifVersion` fallisce, RILEGGE il clic: passa oltre solo se l'esito non è più quello letto (o il segnale è tornato fresco), altrimenti riprova la presa con la versione nuova.
c. Subito dopo rilegge i clic `in-lavoro`: se ne trova un altro con segnale fresco, cede chi ha `preso.quando` più recente (a parità, l'id maggiore), rimettendo il proprio a `da-eseguire` (con `ifVersion`), ed esce.
d. Durante il lavoro aggiorna `preso.aggiornato` almeno ogni 30 minuti (tra una voce e l'altra e prima dei passi lunghi). Finito un clic, rilegge i `da-eseguire` in ordine di tempo e prosegue finché la coda è vuota.
Che cosa fa per tipo di clic:
- `via-piano`: scrive `meta/piano.via` = {`quando`, `clic`} e lavora le voci del piano meno `tolte`, secondo il livello.
- `ok`: manda in linea la voce (il consenso è questo clic), poi toglie `domanda`.
- `non-ancora`: non va in linea; legge `testo`, riprende la voce, riscrive `domanda` quando la ripropone.
- `togli`: aggiunge il codice a `meta/piano.tolte` se il piano è ancora quello di `piano` e non è avviato; altrimenti scarta.
- `margine`: lavora la riserva in ordine, fermandosi prima della percentuale indicata (vuota = prudenza); edizioni e prova vengono prima.
- `appunto`: se `appunti/<rif>` manca lo crea dal `testo`; lo porta nel piano successivo e lo segna `assorbito`.
- `indietro`: si scarta se `voce` non è più l'ultimo rilascio con esito `ok` in `meta/salute.rilasci` (ordinato dal più recente); altrimenti annulla il rilascio, verifica dal vivo, aggiorna `meta/salute`.
Alla fine scrive `esito: "eseguito"` oppure `"scartato"`, `nota` (una frase) e `chiuso`. Il giro della sera segue gli stessi passi a-d, quindi riprende anche i clic `in-lavoro` senza segnale da più di 60 minuti, poi fa le sue verifiche. Tutte le scritture del capo sviluppo: con `db_write` e `ifVersion`, solo sui campi che cambia.

## Limite noto: gli orologi

Lo snapshot del database della pagina non dà l'orario del server per un documento (né `updatedAt` né altro): i tempi trascorsi (15 minuti, 60 minuti, 24 ore, "Partito adesso") si calcolano con l'orologio del dispositivo di chi guarda, contro le ore scritte nei documenti. Un dispositivo con l'orologio sbagliato vede soglie spostate.
