# Registro dei lavori: contratto dei dati

La pagina (`redazione/registro/index.html`) legge tutto e scrive solo due cose: un documento `clic` per ogni tocco di Paolo (più il campo `lancio` di quel clic) e gli `appunti` nuovi. Tutto il resto, `tasks`, `meta/piano`, `meta/capo` e `meta/tocca` compresi, lo scrive il capo sviluppo (istruzioni in `CAPO.md`, il come in `ARCHITETTURA.md` §5): ogni dato ha un solo scrittore, salvo l'esito della prova (sotto). Dove questo file e `CAPO.md` dicessero cose diverse, vale `CAPO.md`.

## Messa in linea, in quest'ordine

1. Accendere l'attività "Gommberg: capo sviluppo" (testo in `CAPO.md`, una sola: parte ai clic e ogni giorno alle 19:27) e, nello stesso momento, spegnere "Gommberg: giro della sera"; scrivere `meta/capo` = {`attivita`: id dell'attività, `giro`: "19:27"}.
2. Se allo scambio la serata `2026-11-25-2` è ancora aperta, riportare la sua prova sulle voci G-45, G-54 e G-50: `prova` = {`giorno`: quello che decide la chat della prova, `esito`: "da-fare"}. Dopo, la pagina non guarda più le serate per lo stato.
3. Dichiarare le capacità della pagina: `db`, `user` e `mcp` con il connettore "Claude Code Remote" (nome verificato dal vivo il 26/11/2026), strumento `fire_trigger`.
4. Pubblicare la pagina.

Senza `meta/capo.attivita` la pagina non mostra i tasti che lanciano lavoro (Via al piano, Ok, Non ancora, Usa il margine, Torna indietro) e dice "Il capo sviluppo non è ancora collegato"; Togli e Aggiungi restano, perché scrivono soltanto.

## Raccolte

| Dove | Chi scrive | Stato |
|---|---|---|
| `tasks/<id>` | capo sviluppo (`prova.esito`, `prova.nota`, `prova.commit`: la chat che legge la prova) | esisteva |
| `serate/<id>` | nessuno: solo storico in Dietro le quinte (letti `stato`, `ramo`, `dopo.righe` o `prima.righe` con `codice` e `cosa`, `fine.testo`, `nota`, `ferma.nota`) | esisteva |
| `appunti/<id>` = {`testo`, `creato`, `stato` (`nuovo`, `assorbito`), `voce`} | pagina (nuovi), capo sviluppo (assorbiti) | esisteva |
| `rilasci/<id>` | nessuno: storico (letti `nome`, `aggiornato`, `stato`, `sintesi`) | esisteva |
| `meta/salute` = {`verificato`, `righe`: [{`nome`, `stato`, `testo`, `causa`, `rimedio`}], `rilasci`: [{`nome`, `quando`, `esito` (`ok`, `ko`, `annullato`), `testo`, `lettore`, `verificato`}]} | capo sviluppo | esisteva; la riga `nome: "Edizione"` dà la pillola in alto; `rilasci` è ordinato dal più recente; nuovi `lettore`, `verificato` ed esito `annullato` |
| `meta/stato` = {`lettori`, `edizioni`, `prossimo`} | capo sviluppo | esisteva; mostrato in Dietro le quinte |
| `meta/piano` = {`settimana` (il lunedì, AAAA-MM-GG), `titolo`, `voci` (codici), `tolte` (codici), `via` ({`quando`, `clic`} o null)} | capo sviluppo | nuovo |
| `meta/capo` = {`attivita`, `giro` ("19:27"), `lavora`: {`quando`, `aggiornato`, `che`} o assente} | capo sviluppo | nuovo |
| `meta/tocca` = {`conto`, `codici`, `aggiornato`, `detto`: {`quando`, `codici`}} | solo capo sviluppo; la pagina non lo legge | nuovo |
| `clic/<id>` | pagina; il capo sviluppo `esito`, `nota`, `chiuso`, `preso`, `non_prima` | nuova |

`meta/giro` non serve più. Un piano mai avviato la cui settimana è passata (sette giorni dopo `settimana`) non compare in Oggi: Dietro le quinte lo segnala come "piano scaduto".

## Campi delle voci (`tasks`)

Letti come prima: `codice`, `titolo`, `stato`, `priorita`, `ordine`, `giorno`, `chiusa`, `scadenza`, `chi`, `input`, `obiettivo` (mostrato come "Perché"), `decisioni`, `domanda`, `modello` (assente = "Da decidere"), `sforzo`, `finestra`.
Nuovi, tutti facoltativi:
- `livello`: `sola` (Da sola), `via` (Con il tuo via), `visto` (Via + Visto). Assente = `visto`. In questa prima versione `sola` e `via` si comportano uguale: partono con il via e vanno in linea da sole se non toccano il motore.
- `cosa`, `lettore`: una riga ciascuno. Assenti = `titolo` e "Da scrivere".
- `riserva`: `true` se la voce è nella riserva del margine.
- `ferma`: la causa in una frase, se il lavoro è fermo.
- `anteprima`: link `https://` a ciò che Paolo deve vedere (la pagina del file su GitHub).
- `visto_commit`: il commit esatto mostrato a Paolo. Lo scrive il capo sviluppo insieme a `domanda` e `anteprima`, lo toglie dopo il rilascio o dopo un "Non ancora"; al clic Ok si unisce solo quello.
- `prova`: {`giorno`, `esito` (`da-fare`, `ok`, `ko`), `nota`, `commit` (il commit di `con-prova` provato)}. Il capo sviluppo scrive `giorno` ed `esito: "da-fare"` e si ferma; l'edizione di prova la lancia e la legge una chat, che scrive `esito`, `nota` e `commit`. La sessione senza nessuno non lancia la prova.

Priorità: `max`, `high`, `medium`, `low`, `tbd` (mostrata come Idea); i vecchi numeri 1, 2, 3 valgono high, medium, low; `stato: "idea"` vale tbd. A parità di priorità viene prima la `scadenza` più vicina ("entro il 24/12").

## Chi aspetta Paolo (regola unica, `aspettaPaolo`)

Una voce non fatta sta in "Tocca a te" se ha una `domanda`, oppure `chi` è `Paolo`, oppure `input` è `decisione` (con `chi` diverso da Claude), come nella pagina di oggi (`chi: "Paolo"` vale `input: "azione"`; con `chi: "Claude"` l'`input` non conta; `approvazione` conta solo con una `domanda`). La richiesta resta anche se la voce è Ferma o aspetta la prova, con lo stato accanto. Con `stato: "pronta"`, una `domanda` e nessuna prova da fare è una voce *Da vedere* (Ok / Non ancora). Le altre richieste sono righe: prima le scadenze entro 14 giorni, poi priorità, poi `ordine`.

## Stati detti a Paolo (funzione `statoVoce`, il primo che vale)

1. `stato` `fatta` → **Fatta**
2. `ferma` non vuoto, o `prova.esito` `ko` → **Ferma** (con la causa)
3. `prova.esito` `da-fare` → **Aspetta la prova** (con il giorno); con `ok` la voce torna allo stato che le spetta
4. aspetta Paolo → **Tocca a te**
5. `stato` `in-corso`, o un clic Ok / Non ancora `in-lavoro` → **Al lavoro**
6. `stato` `pronta`, o un clic Ok / Non ancora `da-eseguire` → **In coda**
7. in `meta/piano.voci`, non in `tolte` e senza un clic `togli` aperto dato per la stessa settimana (`piano`) → **In piano**; **In coda** se il piano è avviato o c'è un clic `via-piano` aperto
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
  preso: { quando, aggiornato }  (ISO 8601 con Z),  non_prima: ISO 8601,
  lancio: { esito: "partito" | "coda" | "incerto" | "bloccato", quando, errore, connettore } }
```
La pagina scrive il clic, poi chiama `fire_trigger` sull'attività di `meta/capo.attivita` con `text: "clic/<id>"` (nient'altro), poi aggiunge `lancio`. `togli` e `appunto` non lanciano nulla. Che cosa dice la pagina (fresco = segnale di meno di 180 minuti):
- `partito`: "Partito"; dopo 15 minuti ancora `da-eseguire`: "Non ancora preso in carico" con Riprova.
- `coda`: "In coda: parte al giro delle <giro>". `incerto`: "Non so se è partito", con Riprova, mai ritentato da solo. `bloccato` (connettore da ricollegare, permesso da dare, connettore da scegliere, vietato dalle impostazioni): la frase e il tasto per rilanciare.
- `non_prima` nel futuro: "Riparte dopo le <ora>", senza la scadenza dei 15 minuti.
- `da-eseguire` mentre un altro clic è `in-lavoro` con segnale fresco, o c'è un `meta/capo.lavora` fresco: "In coda: parte appena finisce il lavoro in corso", senza la scadenza dei 15 minuti.
- `in-lavoro`: "Al lavoro"; con `preso.aggiornato` più vecchio di 180 minuti: "Fermo da <tempo>: nessun segnale" con Riprova.
- `eseguito` o `scartato`: una riga in Oggi con l'esito e la `nota`, per 24 ore da `chiuso` o finché Paolo non la chiude.
Riprova rilancia lo stesso clic: non ne scrive un altro. In "In linea" un rilascio `annullato` si legge "Annullato"; Torna indietro c'è solo sul primo rilascio con esito `ok` e mai se il più recente è `annullato`.

## Che cosa fa il capo sviluppo

Lanciato da un clic (`text` = `clic/<id>`) o dal giro delle 19:27. Nessuna sessione prende un clic prima del suo `non_prima`. Un solo capo sviluppo al lavoro, in quest'ordine:
a. All'avvio cerca clic `in-lavoro` con `preso.aggiornato` fresco e `meta/capo.lavora` con `aggiornato` fresco: se c'è uno dei due, esce senza prendere nulla (il suo clic resta `da-eseguire`: lo farà chi lavora).
b. Altrimenti prende il clic più vecchio fra i `da-eseguire` (senza `non_prima` futuro) e gli `in-lavoro` muti da più di 180 minuti: scrive `esito: "in-lavoro"` e `preso` = {`quando`, `aggiornato`} con `ifVersion` sulla versione letta. Se `ifVersion` fallisce, rilegge il clic: passa oltre solo se l'esito non è più quello letto (o il segnale è tornato fresco), altrimenti riprova la presa con la versione nuova. Chi lavora senza un clic (il giro che propone il piano o lavora le voci del giorno) prende allo stesso modo `meta/capo.lavora` = {`quando`, `aggiornato`, `che`} e lo toglie alla fine.
c. Subito dopo rilegge i clic `in-lavoro`: se ne trova un altro fresco, cede chi ha `preso.quando` più recente (a parità, l'id maggiore), rimettendo il proprio a `da-eseguire` con `ifVersion`, ed esce.
d. Aggiorna il segnale (`preso.aggiornato` o `meta/capo.lavora.aggiornato`) prima e dopo ogni lavoratore e ogni attesa lunga. Finito un clic, rilegge i `da-eseguire` in ordine di tempo e prosegue finché la coda è vuota.
Per tipo di clic:
- `via-piano`: scrive `meta/piano.via` = {`quando`, `clic`}; ogni voce del piano meno `tolte` si lavora nel suo `giorno` (subito quelle il cui giorno è arrivato, le altre al giro di quel giorno). Senza via non parte nulla del piano, nemmeno le `sola`.
- `ok`: unisce esattamente il `visto_commit` della voce e la manda in linea; se il ramo è andato oltre, niente linea e una domanda nuova. Poi toglie `domanda`, `anteprima`, `visto_commit`. Su una voce con prova va in linea solo quando tutte le voci del commit provato hanno avuto l'Ok; fino ad allora il clic si chiude con la nota "in linea quando dai l'ok anche a G-xx".
- `non-ancora`: niente in linea, la voce resta sul suo ramo; legge `testo`, la riprende e riscrive `domanda` e `visto_commit` quando la ripropone.
- `togli`: aggiunge il codice a `meta/piano.tolte` se il piano è ancora quello di `piano` e non è avviato; altrimenti scarta.
- `margine`: senza percentuale una voce della riserva; con la percentuale P, (P - 10) / 5 voci, al più quattro (10% o meno: nessuna). Le voci si costruiscono e collaudano, poi aspettano un Ok: il clic margine non manda in linea nulla.
- `appunto`: se `appunti/<rif>` manca lo crea dal `testo`; lo porta nel piano successivo e lo segna `assorbito`.
- `indietro`: si scarta se il rilascio nominato in `voce` non è il primo di `meta/salute.rilasci` (dal più recente) con esito `ok`; se il più recente è `annullato`, un secondo annullamento di fila non c'è (Ferma e chat). Altrimenti annulla, verifica dal vivo e scrive su quel rilascio `esito: "annullato"`. Mai tra le 8:30 e le 10:30 dei giorni di edizione: in quel caso il clic torna `da-eseguire` con `non_prima` = le 10:30.
Alla fine di ogni clic scrive `esito: "eseguito"` oppure `"scartato"`, `nota` (una frase) e `chiuso`. Ogni volta che scrive o toglie una `domanda` aggiorna `meta/tocca`. Il giro segue gli stessi passi a-d (quindi riprende anche i clic `in-lavoro` muti da più di 180 minuti), poi i suoi compiti. Tutte le scritture del capo sviluppo: con `db_write` e `ifVersion`, solo sui campi che cambia.

## Limite noto: gli orologi

Lo snapshot del database della pagina non dà l'orario del server per un documento (né `updatedAt` né altro): i tempi trascorsi (15 minuti, 180 minuti, 24 ore, "Partito adesso") si calcolano con l'orologio del dispositivo di chi guarda, contro le ore scritte nei documenti. Un dispositivo con l'orologio sbagliato vede soglie spostate.
