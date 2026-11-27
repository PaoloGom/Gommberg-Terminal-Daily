# La Gommunity (G-13)

La colonna accanto all'edizione (homepage) e la sezione nelle pagine `e/NNN.html`: il sentiment di oggi (Toro o Orso, le percentuali compaiono quando voti), i commenti con la targhetta del sentiment, le risposte a un livello, i like e Segnala. Nessuna iscrizione, nessuna email, nessuna approvazione prima della pubblicazione (Paolo, 22/11).

## Le parti

| Parte | File | Che cosa fa |
|---|---|---|
| Servizio | `redazione/sito/lettori.js` | L'unico codice che gira sul sito: Cloudflare lo chiama solo per `/api/*`. Legge e scrive nel database D1, applica le difese |
| Database | D1 `gommberg-lettori` (Cloudflare) | Tabelle `commenti`, `piaciuti`, `segnalazioni`, `voti`, `nomi`, `config` (il segreto delle firme). Le crea il servizio al primo uso |
| Sezione | `assets/lettori.js`, `assets/lettori.css` | La stessa in homepage e nelle edizioni: `LETTORI.monta(elemento, edizione)` |
| Regole | `regole.html` | La pagina che la sezione collega accanto a Privacy: come funziona, il nome, che cosa si scrive, le segnalazioni |
| Avviso | `redazione/sito/segnalazioni.py`, `.github/workflows/segnalazioni.yml` | Ogni 3 ore tra le 8 e le 23 (sveglia dell'orologio dei controlli, `orologio.js`, G-58) legge i commenti segnalati e apre una segnalazione di GitHub assegnata a Paolo |
| Orologio | `redazione/sito/orologio.js` (nello stesso Worker), `orologio.py`, `prova_orologio.mjs` | Il cron del Worker lancia i controlli a orario; lo stato è su `/api/orologio`. Mappa e passaggio: `ARCHITETTURA.md` §1 |
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

I limiti veri: il nome non segue il lettore su un altro dispositivo o dopo che ha cancellato i dati del browser, lì ne serve un altro (per la redazione c'è l'accesso vero dell'area riservata, G-51); e una rete sola, cambiando codice a ogni commento, può occupare fino a 40 nomi al giorno (il tetto dei commenti per rete). Per spegnere i nomi unici: `NOMI_UNICI = false` in `lettori.js`.

Per liberare i nomi di chi ha scritto un commento (per esempio dopo averlo tolto): `DELETE FROM nomi WHERE sito = 'gommberg' AND autore = (SELECT autore FROM commenti WHERE id = <numero>);`

## Edizioni di test

Un'edizione di test (`PROVA.md`, parte B) si pubblica prima del suo giorno e poi si toglie, ma voti e commenti restano nel database sotto lo stesso numero che avrà l'edizione vera. Si cancellano da soli (`toglieProve` in `lettori.js`): dal giorno dell'edizione in poi, alla prima lettura, sparisce tutto ciò che su quel numero porta una data precedente, con i suoi like e le sue segnalazioni. Finché quel giorno non arriva non si tocca nulla, così chi prova vede i suoi commenti. Vale solo sul sito vero; i nomi scelti durante la prova restano di chi li ha scelti.

## Difese (il lettore non le vede)

Gettone firmato dal servizio (niente invii da programmi che non hanno aperto la pagina, né prima di 3 secondi), campo trappola, richieste solo dalla pagina del sito, limiti di frequenza per lettore e per impronta dell'indirizzo IP (i numeri in `LIMITI`, in testa a `lettori.js`), nomi riservati alla redazione (la stessa regola in `lettori.js` e `assets/lettori.js`: il collaudo lo verifica), al massimo due link per commento e mai cliccabili, Segnala che nasconde un commento quando lo segnalano 3 reti diverse (tre colleghi dallo stesso ufficio contano una volta: per questo ai lettori diciamo "più lettori"). Le impronte IP si cancellano dopo 30 giorni: la pulizia la fa la prima richiesta di ogni giorno (`pulizia` in `lettori.js`). I limiti di frequenza che contano sono ricontrollati dentro l'inserimento, così reggono anche a molte richieste nello stesso istante. Non c'è un limite alle sole letture: sul piano gratuito di Cloudflare (100.000 richieste al giorno) chi volesse potrebbe esaurirle e spegnere la sezione fino al giorno dopo; l'edizione resterebbe in linea. Se succede, il rimedio è Turnstile o una cache sulle letture.

## Segnalazioni: come lo viene a sapere Paolo

Quando un lettore tocca Segnala, al giro successivo (ogni 3 ore tra le 8 e le 23 di Roma: 8:15, 11:15, 14:15, 17:15, 20:15, 23:15; una segnalazione fatta di notte arriva alle 8:15) GitHub manda a Paolo un'email: `segnalazioni.yml` legge `/api/lettori/segnalazioni` (numero del commento, edizione, quante reti, se è già nascosto; mai il testo) e `segnalazioni.py` tiene una segnalazione di GitHub per commento, assegnata a lui, con l'etichetta `gommunity`. Dentro c'è il link alla scheda Gommunity dell'area riservata, aperta su quel commento (G-51). Il testo non è mai nella segnalazione perché il repository è pubblico. Nessun segreto: basta il token del giro.

- Un commento resta nell'elenco per 14 giorni dall'ultima segnalazione, finché la redazione non lo toglie o non azzera le segnalazioni. L'elenco mette prima i commenti già nascosti, poi dalla segnalazione più recente.
- Se dopo l'avviso altri lettori lo segnalano e si nasconde, la segnalazione di GitHub riceve una riga e il titolo finisce con "- nascosto". Se Paolo l'aveva chiusa e il commento viene segnalato di nuovo, si riapre.
- Contro le raffiche: una rete manda al massimo 5 segnalazioni al giorno (`segnala_giorno`) e un giro apre al massimo 5 segnalazioni nuove; le altre al giro dopo.
- Se l'avviso stesso non funziona (il sito non dà l'elenco, GitHub rifiuta), lo scrive nel riepilogo del giro e riprova; il giro fallisce, e GitHub scrive a Paolo, solo una volta al giorno (il giro tra le 11 e le 14 di Roma: alle 11:15 con l'orologio, alle 12:15 con la riserva di GitHub d'estate) o se è lanciato a mano.
- Se è l'orologio a fermarsi (segreto mancante o scaduto, GitHub che rifiuta), lo dicono il controllo del mattino e il pannello (`/api/orologio`).

Il flusso gira solo dal ramo principale. **Alla prima messa in linea va provato a mano**: Actions, Segnalazioni della Gommunity, Run workflow (verde con "Nessun commento segnalato"); poi una segnalazione vera su un commento di prova, per vedere arrivare l'email. In locale: `python3 redazione/sito/segnalazioni.py --prova` (stampa senza toccare GitHub).

## Togliere un commento: la scheda Gommunity

Per l'ordinanza 22999/2026 della Cassazione il gestore risponde se, saputo di un commento diffamatorio, non lo rimuove in fretta: quando arriva l'avviso di una segnalazione, o un'email a redazione@gommberg.com, si guarda e se serve si toglie subito. Dal 5/12 (G-51) si fa dalla scheda Gommunity dell'area riservata (gommberg.com/redazione/, vedi sotto): l'avviso di GitHub porta dritto al commento. Lì: **Togli** (nascosto = 2), **Rimetti** (torna visibile e azzera le segnalazioni, se no alla prossima si nasconderebbe di nuovo), **Azzera** (le segnalazioni di un commento ancora visibile), **Fissa in alto**, **Blocca il lettore** (il codice del browser per sempre, la rete per 30 giorni: non scrive, non vota, non segnala), **Libera il nome**, **Chiudi o riapri la discussione** di un'edizione (i lettori leggono ma non scrivono; la redazione sì). Togli e Rimetti si annullano per 10 secondi. Da collegato, sul sito c'è anche "Togli" sotto ogni commento.

Solo se l'area non risponde, dalla console di D1 (Cloudflare, Storage e database, D1, `gommberg-lettori`, Console): `UPDATE commenti SET nascosto = 2 WHERE id = <numero>;` per toglierlo; `DELETE FROM segnalazioni WHERE commento = <numero>;` e `UPDATE commenti SET nascosto = 0, segnalazioni = 0 WHERE id = <numero>;` per rimetterlo.

I commenti delle anteprime hanno `sito = 'prova'` e non compaiono mai su gommberg.com; si possono cancellare con `DELETE FROM commenti WHERE sito = 'prova';` (e lo stesso per `voti` e `nomi`).

## L'area riservata della redazione (G-51)

Un solo posto per Paolo: **gommberg.com/redazione/**, non collegato da nessuna pagina. Il codice è `redazione.js` (nel Worker, con `lettori.js`); le pagine sono `pannello/accesso.html` (l'accesso) e `pannello/index.html` (l'area: il pannello di controllo con la striscia di oggi in Panoramica, più le schede Gommunity e Sicurezza). La cartella `pannello/` non è mai tra i file pubblici: `costruisci.py` la mette in `_privato/pannello.js`, che entra nel codice del Worker, e il Worker la serve solo dopo l'accesso. I vecchi indirizzi `/pannello/` e `/consumi/` danno 404.

**Le credenziali** le sceglie Paolo e le mette lui, una volta, tra i segreti del Worker: Cloudflare, Workers e Pages, `gommberg`, Impostazioni, Variabili e segreti, Aggiungi, tipo **Segreto**: `REDAZIONE_UTENTE` (il nome utente) e `REDAZIONE_PASSWORD` (almeno 16 caratteri: meglio una frase di quattro o cinque parole). Nessun deploy li cancella e nessuno li rilegge. Senza, la schermata di accesso dice "non ancora configurato". Claude non li vede mai.

**Il cambio password** dalla scheda Sicurezza salva in D1 solo l'impronta della nuova (PBKDF2-SHA256, 50.000 passaggi, sale casuale) e chiude le altre sessioni. **Chi vince**: l'ultima cambiata. L'impronta salvata vale finché il segreto `REDAZIONE_PASSWORD` resta quello di quando è stata salvata; se Paolo cambia il segreto su Cloudflare, vince il segreto, l'impronta si cancella e tutte le sessioni si chiudono. **Password dimenticata**: si cambia il segreto `REDAZIONE_PASSWORD` su Cloudflare (anche dal telefono) e si entra con quello.

**Sessioni**: cookie `__Host-gtd_sessione` (HttpOnly, Secure, SameSite=Strict), in D1 solo la sua impronta. "Resta collegato" (acceso di base, da spegnere sui PC condivisi): 90 giorni senza uso; senza, fino alla chiusura del browser e al massimo 12 ore senza uso. Esci chiude la sessione sul server; "Esci da tutti i dispositivi" e l'Esci di ogni dispositivo stanno nella scheda Sicurezza, con gli ultimi accessi (anche quelli sbagliati) degli ultimi 30 giorni. Il cookie `gtd_red=1`, leggibile dalle pagine e senza segreti, serve solo a dire alle pagine del sito che vale la pena chiedere la sessione: così la barra Redazione (`assets/redazione.js`, in ogni pagina) e la firma della redazione nella Gommunity non costano nulla ai lettori.

**Tentativi**: per rete, 5 errori in 24 ore liberi, poi un'attesa che raddoppia a ogni errore (1, 2, 4... minuti, al massimo 60); per tutto il sito, oltre 50 errori in 15 minuti l'accesso si sospende finché non scendono (vale anche per Paolo: è il prezzo contro un attacco da molte reti). Nome utente sbagliato e password sbagliata danno la stessa risposta. Ogni azione che cambia qualcosa vuole lo stesso sito d'origine e il gettone anti-CSRF della sessione; le pagine dell'area hanno una CSP con nonce, niente cache e niente cornici.

**La firma "Gommberg"**: i commenti della redazione hanno `redazione = 1` (autore `redazione`, mai un'impronta di lettore) ed escono con il logo e il badge Redazione; il nome è riservato (`RISERVATI`), quindi nessun lettore può firmarsi così, e il badge lo decide solo il servizio. I commenti della redazione si modificano (con "modificato"), non si nascondono con le segnalazioni, e si scrivono anche a discussione chiusa; quelli dei lettori si tolgono, mai si modificano.

**Costi sul piano gratuito**: la derivazione della password (circa 6 ms di CPU, misurati) si fa solo quando c'è un'impronta salvata, una volta per accesso; il cambio password ne fa due (raro: Cloudflare tollera i superamenti occasionali dei 10 ms). Ogni pagina dell'area legge la sessione in D1 e la rinnova al massimo una volta l'ora.

**Primo accesso** (Paolo, dopo il rilascio): 1) i due segreti su Cloudflare; 2) gommberg.com/redazione/ dal PC, "Resta collegato" acceso, e il preferito; 3) dal telefono, stesso indirizzo, poi Condividi, Aggiungi alla schermata Home (l'icona si chiama "Redazione"); 4) Esci e rientro per provare.

## Il database

Creato il 22/11/2026 (ID in `wrangler.jsonc`). Se un giorno andasse ricreato: Cloudflare, account del Gommberg, Storage e database, D1, Crea, nome `gommberg-lettori`, posizione automatica (Europa); il nuovo ID va in `redazione/sito/wrangler.jsonc`. Con `DA-CREARE` al posto dell'ID, `sito.yml` pubblica i soli file statici e il riquadro dice che la discussione non si carica. Il token di GitHub non ha bisogno di permessi su D1: basta quello che pubblica il Worker.

## Se il servizio si ferma

Homepage ed edizioni sono file statici e non passano dal servizio: escono sempre. La sezione mostra "La discussione si sta caricando" e riprova da sola (dopo 2, 5, 15 secondi, poi ogni minuto). Nei giorni di uscita il controllo del mattino (`mattino.py`) guarda che il servizio risponda e, se no, avvisa Paolo. Se la pubblicazione con il servizio fallisce, `sito.yml` ripubblica i soli file statici (avviso nel riepilogo dell'azione). Gli errori del servizio si leggono da Cloudflare, Workers, gommberg, Observability.
