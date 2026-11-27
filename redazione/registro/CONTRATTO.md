# Registro dei lavori: contratto dei dati

La pagina (`redazione/registro/index.html`) scrive solo due cose: un documento `clic` per ogni tocco di Paolo (più il campo `lancio` di quel clic) e gli `appunti` nuovi. **La pagina non scrive mai voci né piano.** Gli altri scrittori sono due: il capo sviluppo (sessione senza nessuno, istruzioni in `CAPO.md`) e la chat del rilascio (aperta da Paolo, il come in `ARCHITETTURA.md` §5). Dove questo file e `CAPO.md` dicessero cose diverse, vale `CAPO.md`.

In questa prima versione il capo sviluppo non rilascia mai: costruisce, fa collaudare, prepara l'anteprima, chiede l'Ok e lo registra. Rilasci, annullamenti, edizione di prova e mail li fa la chat.

## Chi scrive che cosa

- **Capo sviluppo:** le voci (fino a `stato` "pronta", con `domanda`, `anteprima`, `visto_commit`, `ok`, `ferma`), il piano (`meta/piano`), l'esito dei clic (`esito`, `nota`, `chiuso`, `preso`), `meta/capo`, `meta/tocca`, `meta/salute` (salvo i rilasci), `appunti` assorbiti.
- **Chat del rilascio:** sulla voce `stato` "fatta", `chiusa`, `esito` (una riga) e la pulizia dei campi dell'Ok (`ok`, `domanda`, `anteprima`, `visto_commit`); `prova` (`esito` "ok" o "ko", `nota`, `commit`); `meta/salute.rilasci` (`ok`, `ko`, `annullato`).
- **Pagina:** `clic` (e il loro `lancio`), `appunti` nuovi.

## In linea

Dal 27/11/2026: attività "Gommberg: capo sviluppo" accesa (id in `meta/capo.attivita`), "Gommberg: giro della sera" spenta, pagina pubblicata con le capacità `db`, `user` e `mcp` (connettore "Claude Code Remote", strumento `fire_trigger`). La pagina di prima resta nella storia dell'artifact (versione 1795621755-04b8).

Senza `meta/capo.attivita` la pagina non mostra i tasti che lanciano lavoro (Via al piano, Ok, Non ancora, Usa il margine, Torna indietro) e dice "Il capo sviluppo non è ancora collegato"; Togli e Aggiungi restano, perché scrivono soltanto.

## Raccolte

| Dove | Che cosa | Stato |
|---|---|---|
| `tasks/<id>` | le voci (campi sotto) | esisteva |
| `serate/<id>` | solo storico in Dietro le quinte (letti `stato`, `ramo`, `dopo.righe` o `prima.righe` con `codice` e `cosa`, `fine.testo`, `nota`, `ferma.nota`) | esisteva |
| `appunti/<id>` = {`testo`, `creato`, `stato` (`nuovo`, `assorbito`), `voce`} | | esisteva |
| `rilasci/<id>` | storico (letti `nome`, `aggiornato`, `stato`, `sintesi`) | esisteva |
| `meta/salute` = {`verificato`, `righe`: [{`nome`, `stato`, `testo`, `causa`, `rimedio`}], `rilasci`: [{`nome`, `quando`, `esito` (`ok`, `ko`, `annullato`), `testo`, `lettore`, `verificato`}]} | la riga `nome: "Edizione"` dà la pillola in alto; `rilasci` è ordinato dal più recente | esisteva; nuovi `lettore`, `verificato`, esito `annullato` |
| `meta/stato` = {`lettori`, `edizioni`, `prossimo`} | mostrato in Dietro le quinte | esisteva |
| `meta/piano` = {`settimana` (il lunedì, AAAA-MM-GG), `titolo`, `voci` (codici), `giorni` ({codice: giorno}, scritto con il piano), `tolte` (codici), `via` ({`quando`, `clic`} o null)} | | nuovo |
| `meta/capo` = {`attivita`, `giro` ("19:27"), `lavora`: {`quando`, `aggiornato`, `che`} o assente} | | nuovo |
| `meta/tocca` = {`conto`, `codici` (codici delle voci che aspettano Paolo, più "piano:<settimana>" finché il piano non ha il via e "ferma:<codice>" per ogni voce ferma), `aggiornato`, `detto`: {`quando`, `codici`}} | la pagina non lo legge | nuovo |
| `clic/<id>` | sotto | nuova |

Un piano mai avviato la cui settimana è passata (sette giorni dopo `settimana`) non compare in Oggi: Dietro le quinte lo segnala come "piano scaduto".

## Campi delle voci (`tasks`)

Letti come prima: `codice`, `titolo`, `stato`, `priorita`, `ordine`, `giorno`, `chiusa`, `scadenza`, `chi`, `input`, `obiettivo` (mostrato come "Perché"), `decisioni`, `domanda`, `modello` (assente = "Da decidere"), `sforzo`, `finestra`.
Nuovi, tutti facoltativi:
- `livello`: `sola`, `via`, `visto` (assente = `visto`). È l'obiettivo: `sola` andrà in linea da sola, `via` dopo il via sul piano, `visto` dopo l'Ok. In questa versione ogni voce si ferma a "pronta" e va in linea solo con un Ok e una chat.
- `cosa`, `lettore`: una riga ciascuno. Assenti = `titolo` e "Da scrivere".
- `riserva`: `true` se la voce è nella riserva del margine.
- `ferma`: la causa in una frase, se il lavoro è fermo.
- `anteprima`: link `https://` a ciò che Paolo deve vedere (la pagina del file su GitHub).
- `visto_commit`: il commit esatto mostrato a Paolo; lo scrive il capo sviluppo con `domanda` e `anteprima`.
- `ok` = {`quando`, `clic`, `commit`}: lo scrive il capo sviluppo al clic Ok; `commit` è il `visto_commit` approvato. La chat del rilascio unisce esattamente `ok.commit`, poi toglie `ok`, `domanda`, `anteprima`, `visto_commit`.
- `prova` = {`giorno`, `esito` (`da-fare`, `ok`, `ko`), `nota`, `commit` (il commit di `con-prova` provato)}: lo scrive solo la chat: "da-fare" quando la voce approvata entra nel ramo della prova, poi l'esito. Il capo sviluppo non scrive mai `prova`.

Priorità: `max`, `high`, `medium`, `low`, `tbd` (mostrata come Idea); i vecchi numeri 1, 2, 3 valgono high, medium, low; `stato: "idea"` vale tbd. A parità di priorità viene prima la `scadenza` più vicina ("entro il 24/12").

## Chi aspetta Paolo (regola unica, `aspettaPaolo`)

Una voce non fatta sta in "Tocca a te" se ha una `domanda`, oppure `chi` è `Paolo`, oppure `input` è `decisione` (con `chi` diverso da Claude), come nella pagina di oggi (`chi: "Paolo"` vale `input: "azione"`; con `chi: "Claude"` l'`input` non conta; `approvazione` conta solo con una `domanda`). La richiesta resta anche se la voce è Ferma o aspetta la prova, con lo stato accanto. In cima: il piano, le voci approvate (con `ok`: una scheda sola con il link alla chat del rilascio), le richieste di annullamento, le voci *Da vedere* (`stato` "pronta", una `domanda`, nessuna prova da fare: Ok, approvo / Non ancora); le altre richieste sono righe: prima le scadenze entro 14 giorni, poi priorità, poi `ordine`. Il capo sviluppo ricalcola `meta/tocca` dalle voci con questa regola, più "piano:<settimana>" finché il piano non ha il via.

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
  preso: { quando, aggiornato }  (ISO 8601 con Z),
  lancio: { esito: "partito" | "coda" | "incerto" | "bloccato", quando, errore, connettore } }
```
La pagina scrive il clic, poi chiama `fire_trigger` sull'attività di `meta/capo.attivita` con `text: "clic/<id>"` (nient'altro), poi aggiunge `lancio`. `togli` e `appunto` non lanciano nulla. Che cosa dice la pagina (fresco = segnale di meno di 180 minuti):
- `partito`: "Partito"; dopo 15 minuti ancora `da-eseguire`: "Non ancora preso in carico" con Riprova.
- `coda`: "In coda: parte al giro delle <giro>". `incerto`: "Non so se è partito", con Riprova, mai ritentato da solo. `bloccato` (connettore da ricollegare, permesso da dare, connettore da scegliere, vietato dalle impostazioni): la frase e il tasto per rilanciare.
- `da-eseguire` mentre un altro clic è `in-lavoro` con segnale fresco, o c'è un `meta/capo.lavora` fresco: "In coda: parte appena finisce il lavoro in corso", senza la scadenza dei 15 minuti.
- `in-lavoro`: "Al lavoro"; con `preso.aggiornato` più vecchio di 180 minuti: "Fermo da <tempo>: nessun segnale" con Riprova.
- `indietro` non ancora chiuso: "Chiesto: sto preparando l'annullamento". Chiuso `eseguito`: in Tocca a te la richiesta con il link "Apri la chat per annullare", finché quel rilascio non è `annullato`.
- `ok` chiuso `eseguito`: la voce, con `ok`, è "Approvata: apri la chat del rilascio".
- Gli altri clic chiusi: una riga in Oggi con l'esito e la `nota`, per 24 ore da `chiuso` o finché Paolo non la chiude.
Riprova rilancia lo stesso clic: non ne scrive un altro. In "In linea" un rilascio `annullato` si legge "Annullato"; Torna indietro c'è solo sul primo rilascio con esito `ok` e mai se il più recente è `annullato`.

## Che cosa fa il capo sviluppo

Lanciato da un clic (`text` = `clic/<id>`) o dal giro delle 19:27. Un solo capo sviluppo al lavoro, in quest'ordine:
a. All'avvio cerca clic `in-lavoro` con `preso.aggiornato` fresco e un `meta/capo.lavora` con `aggiornato` fresco: se c'è uno dei due, esce senza prendere nulla (il suo clic resta `da-eseguire`: lo farà chi lavora). Un `lavora` più vecchio di 180 minuti lo toglie la prima sessione che lo trova, e prosegue.
b. Altrimenti prende il clic più vecchio fra i `da-eseguire` e gli `in-lavoro` muti da più di 180 minuti: scrive `esito: "in-lavoro"` e `preso` = {`quando`, `aggiornato`} con `ifVersion` sulla versione letta. Se `ifVersion` fallisce, rilegge il clic: passa oltre solo se l'esito non è più quello letto (o il segnale è tornato fresco), altrimenti riprova la presa con la versione nuova. Qualunque lavoro senza un clic preso (compiti del giro compresi, anche in una sessione nata da un clic) vuole prima `meta/capo.lavora` = {`quando`, `aggiornato`, `che`}, preso con `ifVersion` e tolto alla fine.
c. Subito dopo rilegge i clic `in-lavoro`: se ne trova un altro fresco, cede chi ha `preso.quando` più recente (a parità, l'id maggiore), rimettendo il proprio a `da-eseguire` con `ifVersion`, ed esce.
d. Aggiorna il segnale (`preso.aggiornato` o `meta/capo.lavora.aggiornato`) prima e dopo ogni lavoratore e ogni attesa lunga. Finito un clic, rilegge i `da-eseguire` in ordine di tempo e prosegue finché la coda è vuota; finiti i compiti, rilegge la coda dei clic prima di uscire.
Per tipo di clic:
- `via-piano`: scrive `meta/piano.via` = {`quando`, `clic`}; ogni voce del piano meno `tolte` si lavora nel suo giorno (`meta/piano.giorni`; subito quelle il cui giorno è arrivato), fino a "pronta", mai oltre. Senza via non parte nulla del piano.
- `ok`: sulla voce `ok` = {`quando`, `clic`, `commit`: il `visto_commit`} e `domanda` "Approvata: apri la chat del rilascio". Non manda in linea.
- `non-ancora`: legge la nota, riprende la voce sullo stesso ramo, la ripropone con un `visto_commit` nuovo.
- `indietro`: non annulla nulla e non scrive su nessuna voce; chiude il clic con la nota "Apri la chat per annullare il rilascio <nome>": la pagina mostra la richiesta dal clic chiuso.
- `togli`: aggiunge il codice a `meta/piano.tolte` se il piano è ancora quello di `piano` e non ha il via; altrimenti scarta.
- `margine`: le voci della riserva in ordine fino a "pronta", mai oltre; senza percentuale una voce, con la percentuale P al più (P - 10) / 5 voci e mai più di quattro (10% o meno: nessuna).
- `appunto`: se `appunti/<rif>` manca lo crea dal `testo`; lo porta nel piano successivo e lo segna `assorbito`.
Alla fine di ogni clic scrive `esito` ("eseguito" o "scartato"), `nota` (una frase) e `chiuso`. Ogni volta che ha letto le voci ricalcola `meta/tocca`. Tutte le sue scritture: con `db_write` e `ifVersion`, solo sui campi che cambia.

## Limite noto: gli orologi

Lo snapshot del database della pagina non dà l'orario del server per un documento (né `updatedAt` né altro): i tempi trascorsi (15 minuti, 180 minuti, 24 ore, "Partito adesso") si calcolano con l'orologio del dispositivo di chi guarda, contro le ore scritte nei documenti. Un dispositivo con l'orologio sbagliato vede soglie spostate.
