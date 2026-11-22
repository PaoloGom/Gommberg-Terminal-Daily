# La Gommunity (G-13)

La colonna accanto all'edizione (homepage) e la sezione nelle pagine `e/NNN.html`: il sentiment di oggi (Toro o Orso, le percentuali compaiono quando voti), i commenti con la targhetta del sentiment, le risposte a un livello, i like e Segnala. Nessuna iscrizione, nessuna email, nessuna approvazione prima della pubblicazione (Paolo, 22/11).

## Le parti

| Parte | File | Che cosa fa |
|---|---|---|
| Servizio | `redazione/sito/lettori.js` | L'unico codice che gira sul sito: Cloudflare lo chiama solo per `/api/*`. Legge e scrive nel database D1, applica le difese |
| Database | D1 `gommberg-lettori` (Cloudflare) | Tabelle `commenti`, `piaciuti`, `segnalazioni`, `voti`, `nomi`, `config` (il segreto delle firme). Le crea il servizio al primo uso |
| Sezione | `assets/lettori.js`, `assets/lettori.css` | La stessa in homepage e nelle edizioni: `LETTORI.monta(elemento, edizione)` |
| Regole | `regole.html` | La pagina che la sezione collega accanto a Privacy: come funziona, il nome, che cosa si scrive, le segnalazioni |
| Avviso | `redazione/sito/segnalazioni.py`, `.github/workflows/segnalazioni.yml` | Ogni ora legge i commenti segnalati e apre una segnalazione di GitHub assegnata a Paolo |
| Collaudo | `redazione/sito/prova_lettori.mjs`, `d1_finto.mjs`, `collaudo.py` (`passo_lettori`) | Il servizio vero contro un D1 finto, la sintassi, la configurazione e l'avviso |
| Prova in locale | `redazione/sito/servi_lettori.mjs` | Il sito in locale con il servizio vero e il D1 finto, per provare e fotografare la sezione senza pubblicare |

## Il sentiment

Nessuna domanda (Paolo, 22/11): solo Toro o Orso, per dire come ci si sente sui mercati. Si vota sull'edizione più recente, tutto il giorno, e si cambia finché non esce l'edizione dopo; le edizioni precedenti mostrano il loro risultato senza voto (nelle anteprime il voto è sempre aperto). Il voto accompagna i commenti di chi l'ha dato, come targhetta accanto al nome.

## Il nome

Un nome resta di chi l'ha usato per primo (Paolo, 22/11): dal primo commento è legato al codice anonimo del browser (tabella `nomi`), senza iscrizione. Il browser lo ricorda e lo ripropone in "Firmi come" a ogni visita, su ogni edizione.

- **Nomi uguali all'occhio sono lo stesso nome** (`chiaveNome` in `lettori.js`): maiuscole, accenti, spazi e punteggiatura non contano; i, I, elle, uno e ! sono la stessa lettera, lo zero è una o, "rn" è una m, "vv" una w. Il prezzo: due nomi veri che differiscono solo per i ed elle ("Elia" ed "Ella") non possono convivere, il secondo ne sceglie un altro.
- **Caratteri ammessi** (`AMMESSI`): lettere anche accentate, numeri, spazi e `. , ' & ? ! : + _ -`. Niente simboli, emoji o lettere di altri alfabeti: servirebbero solo a scrivere un nome uguale a quello di un altro, o a imitare la targhetta "▲ Toro".
- **Nomi riservati** alla redazione: `RISERVATI`, controllato anche sulla chiave ("Redaz1one", "Gornmberg").
- **Tre nomi per lettore** (`LIMITI.nomi_per_lettore`). Per prenderne un quarto, uno dei tre deve essere fermo da 30 giorni (`nome_cambio_giorni`): così un nome non passa a un altro lettore mentre nella discussione ci sono ancora i commenti firmati dal primo. Chi ci prova prima legge l'elenco dei suoi nomi.
- **Un nome non usato per 180 giorni torna libero** (`nome_giorni`) e la sua riga si cancella con la pulizia di ogni giorno.
- Mentre il lettore sceglie il nome la sezione chiede al servizio se è libero (`/api/lettori/nome?n=`).
- **Il dado** propone sempre un "Nome Cognome" di finanza (Paolo, 22/11) e non va mai toccato, perché ha tre livelli che si attivano da soli (`assets/lettori.js`): 1) il mazzo di 123 giochi di parole scritti a mano ("Massimo Rischio", "Tito Lare"), in ordine casuale e senza ripetizioni; 2) un nome vero più un cognome finanziario ("Wanda Plusvalenza"), 5.040 combinazioni; 3) quando una decina intera di combinati risulta presa, il numero romano ("Gino Spread II", poi III...), senza fine. Il dado chiede al servizio dieci nomi per volta (`/api/lettori/nome?n=...&n=...`) e propone solo quelli liberi; tiene una piccola coda, così il clic risponde subito. Le liste si possono allungare aggiungendo parole (il collaudo controlla che il servizio le accetti tutte), ma non serve.

I limiti veri: il nome non segue il lettore su un altro dispositivo o dopo che ha cancellato i dati del browser, lì ne serve un altro (lo risolve solo un accesso vero: G-51 per la redazione); e una rete sola, cambiando codice a ogni commento, può occupare fino a 40 nomi al giorno (il tetto dei commenti per rete). Per spegnere i nomi unici: `NOMI_UNICI = false` in `lettori.js`.

Per liberare i nomi di chi ha scritto un commento (per esempio dopo averlo tolto): `DELETE FROM nomi WHERE sito = 'gommberg' AND autore = (SELECT autore FROM commenti WHERE id = <numero>);`

## Edizioni di test

Un'edizione di test (`PROVA.md`, parte B) si pubblica prima del suo giorno e poi si toglie, ma voti e commenti restano nel database sotto lo stesso numero che avrà l'edizione vera. Si cancellano da soli (`toglieProve` in `lettori.js`): dal giorno dell'edizione in poi, alla prima lettura, sparisce tutto ciò che su quel numero porta una data precedente, con i suoi like e le sue segnalazioni. Finché quel giorno non arriva non si tocca nulla, così chi prova vede i suoi commenti. Vale solo sul sito vero; i nomi scelti durante la prova restano di chi li ha scelti.

## Difese (il lettore non le vede)

Gettone firmato dal servizio (niente invii da programmi che non hanno aperto la pagina, né prima di 3 secondi), campo trappola, richieste solo dalla pagina del sito, limiti di frequenza per lettore e per impronta dell'indirizzo IP (i numeri in `LIMITI`, in testa a `lettori.js`), nomi riservati alla redazione (la stessa regola in `lettori.js` e `assets/lettori.js`: il collaudo lo verifica), al massimo due link per commento e mai cliccabili, Segnala che nasconde un commento quando lo segnalano 3 reti diverse (tre colleghi dallo stesso ufficio contano una volta: per questo ai lettori diciamo "più lettori"). Le impronte IP si cancellano dopo 30 giorni: la pulizia la fa la prima richiesta di ogni giorno (`pulizia` in `lettori.js`). I limiti di frequenza che contano sono ricontrollati dentro l'inserimento, così reggono anche a molte richieste nello stesso istante. Non c'è un limite alle sole letture: sul piano gratuito di Cloudflare (100.000 richieste al giorno) chi volesse potrebbe esaurirle e spegnere la sezione fino al giorno dopo; l'edizione resterebbe in linea. Se succede, il rimedio è Turnstile o una cache sulle letture.

## Segnalazioni: come lo viene a sapere Paolo

Quando un lettore tocca Segnala, entro un'ora GitHub manda a Paolo un'email: `segnalazioni.yml` legge `/api/lettori/segnalazioni` (numero del commento, edizione, quante reti, se è già nascosto; mai il testo) e `segnalazioni.py` tiene una segnalazione di GitHub per commento, assegnata a lui, con l'etichetta `gommunity`. Dentro ci sono i tre comandi pronti: leggere il commento, toglierlo, oppure lasciarlo azzerando le segnalazioni. Il testo non è mai nella segnalazione perché il repository è pubblico. Nessun segreto: basta il token del giro.

- Un commento resta nell'elenco per 14 giorni dall'ultima segnalazione, finché la redazione non lo toglie o non azzera le segnalazioni. L'elenco mette prima i commenti già nascosti, poi dalla segnalazione più recente.
- Se dopo l'avviso altri lettori lo segnalano e si nasconde, la segnalazione di GitHub riceve una riga e il titolo finisce con "- nascosto". Se Paolo l'aveva chiusa e il commento viene segnalato di nuovo, si riapre.
- Contro le raffiche: una rete manda al massimo 5 segnalazioni al giorno (`segnala_giorno`) e un giro apre al massimo 5 segnalazioni nuove; le altre al giro dopo.
- Se l'avviso stesso non funziona (il sito non dà l'elenco, GitHub rifiuta), lo scrive nel riepilogo del giro e riprova; il giro fallisce, e GitHub scrive a Paolo, solo una volta al giorno (il giro delle 10 di Roma) o se è lanciato a mano.

Il flusso gira solo dal ramo principale. **Alla prima messa in linea va provato a mano**: Actions, Segnalazioni della Gommunity, Run workflow (verde con "Nessun commento segnalato"); poi una segnalazione vera su un commento di prova, per vedere arrivare l'email. In locale: `python3 redazione/sito/segnalazioni.py --prova` (stampa senza toccare GitHub).

## Togliere un commento (finché non c'è G-51)

Per l'ordinanza 22999/2026 della Cassazione il gestore risponde se, saputo di un commento diffamatorio, non lo rimuove in fretta: quando arriva l'avviso di una segnalazione, o un'email a redazione@gommberg.com, si guarda e se serve si toglie subito.

1. Cloudflare, Storage e database, D1, `gommberg-lettori`, Console.
2. Trovare il commento: `SELECT id, ed, nome, testo, creato FROM commenti WHERE sito = 'gommberg' AND testo LIKE '%parola%';`
3. Toglierlo: `UPDATE commenti SET nascosto = 2 WHERE id = <numero>;` (2 = tolto dalla redazione; 1 = nascosto dalle segnalazioni; 0 = visibile).
4. Se invece può restare: `DELETE FROM segnalazioni WHERE commento = <numero>;` e `UPDATE commenti SET nascosto = 0, segnalazioni = 0 WHERE id = <numero>;` (senza azzerare le segnalazioni, alla prossima si nasconderebbe di nuovo).

I commenti delle anteprime hanno `sito = 'prova'` e non compaiono mai su gommberg.com; si possono cancellare con `DELETE FROM commenti WHERE sito = 'prova';` (e lo stesso per `voti` e `nomi`).

## Il database

Creato il 22/11/2026 (ID in `wrangler.jsonc`). Se un giorno andasse ricreato: Cloudflare, account del Gommberg, Storage e database, D1, Crea, nome `gommberg-lettori`, posizione automatica (Europa); il nuovo ID va in `redazione/sito/wrangler.jsonc`. Con `DA-CREARE` al posto dell'ID, `sito.yml` pubblica i soli file statici e il riquadro dice che la discussione non si carica. Il token di GitHub non ha bisogno di permessi su D1: basta quello che pubblica il Worker.

## Se il servizio si ferma

Homepage ed edizioni sono file statici e non passano dal servizio: escono sempre. La sezione mostra "La discussione si sta caricando" e riprova da sola (dopo 2, 5, 15 secondi, poi ogni minuto). Nei giorni di uscita il controllo del mattino (`mattino.py`) guarda che il servizio risponda e, se no, avvisa Paolo. Se la pubblicazione con il servizio fallisce, `sito.yml` ripubblica i soli file statici (avviso nel riepilogo dell'azione). Gli errori del servizio si leggono da Cloudflare, Workers, gommberg, Observability.
