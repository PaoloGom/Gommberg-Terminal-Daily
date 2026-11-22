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

Un nome resta di chi l'ha usato per primo (Paolo, 22/11): dal primo commento è legato al codice anonimo del browser (tabella `nomi`), e nessun altro può firmarsi così, nemmeno cambiando maiuscole, accenti, spazi, punteggiatura, o mettendo lo zero al posto della o (`chiaveNome` in `lettori.js`). Mentre il lettore sceglie il nome la sezione chiede al servizio se è libero (`/api/lettori/nome?n=`), e il dado propone solo nomi liberi: un centinaio di nomi di finanza, italiani e ironici, scritti a mano in `assets/lettori.js` (Paolo, 22/11; la lista si allunga aggiungendo righe, il collaudo controlla che il servizio li accetti). Se quelli pescati sono già presi, il dado ne numera uno ("Toro seduto 7").

Limiti scelti, in `LIMITI`: un lettore tiene per sé 3 nomi (il quarto libera quello che usa da più tempo) e un nome non usato per 180 giorni torna libero. Il limite vero: il nome non segue il lettore su un altro dispositivo o dopo che ha cancellato i dati del browser, lì ne serve un altro; lo risolve solo un accesso vero (G-51 per la redazione). Per spegnere i nomi unici: `NOMI_UNICI = false` in `lettori.js`.

Per liberare a mano un nome (qualcuno ha preso quello di un altro lettore noto): `DELETE FROM nomi WHERE sito = 'gommberg' AND nome = 'Il Nome';`

## Difese (il lettore non le vede)

Gettone firmato dal servizio (niente invii da programmi che non hanno aperto la pagina, né prima di 3 secondi), campo trappola, richieste solo dalla pagina del sito, limiti di frequenza per lettore e per impronta dell'indirizzo IP (i numeri in `LIMITI`, in testa a `lettori.js`), nomi riservati alla redazione (la stessa regola in `lettori.js` e `assets/lettori.js`: il collaudo lo verifica), al massimo due link per commento e mai cliccabili, Segnala che nasconde un commento quando lo segnalano 3 reti diverse. Le impronte IP si cancellano dopo 30 giorni.

## Segnalazioni: come lo viene a sapere Paolo

Quando un lettore tocca Segnala, entro un'ora GitHub manda a Paolo un'email: `segnalazioni.yml` legge `/api/lettori/segnalazioni` (numero del commento, edizione, quante reti, se è già nascosto; mai il testo) e `segnalazioni.py` apre una segnalazione assegnata a lui, una sola per commento. Dentro ci sono i tre comandi pronti: leggere il commento, toglierlo, oppure lasciarlo azzerando le segnalazioni. Il testo non è mai nella segnalazione perché il repository è pubblico. Nessun segreto: basta il token del giro. Un commento resta nell'elenco per 14 giorni dall'ultima segnalazione, finché la redazione non lo toglie o non azzera le segnalazioni.

Il flusso gira solo dal ramo principale. Per provarlo a mano: Actions, Segnalazioni della Gommunity, Run workflow. In locale: `python3 redazione/sito/segnalazioni.py --prova` (stampa senza toccare GitHub).

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
