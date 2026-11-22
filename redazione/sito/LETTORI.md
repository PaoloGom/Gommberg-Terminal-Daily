# La Community (G-13)

La colonna accanto all'edizione (homepage) e la sezione nelle pagine `e/NNN.html`: il sentiment di oggi (Toro o Orso, le percentuali compaiono quando voti), i commenti con la targhetta del sentiment, le risposte a un livello, i like e Segnala. Nessuna iscrizione, nessuna email, nessuna approvazione prima della pubblicazione (Paolo, 22/11).

## Le parti

| Parte | File | Che cosa fa |
|---|---|---|
| Servizio | `redazione/sito/lettori.js` | L'unico codice che gira sul sito: Cloudflare lo chiama solo per `/api/*`. Legge e scrive nel database D1, applica le difese |
| Database | D1 `gommberg-lettori` (Cloudflare) | Tabelle `commenti`, `piaciuti`, `segnalazioni`, `voti`, `config` (il segreto delle firme). Le crea il servizio al primo uso |
| Sezione | `assets/lettori.js`, `assets/lettori.css` | La stessa in homepage e nelle edizioni: `LETTORI.monta(elemento, edizione)` |
| Collaudo | `redazione/sito/prova_lettori.mjs`, `collaudo.py` (`passo_lettori`) | Il servizio vero contro un D1 finto, la sintassi e la configurazione |

## Il sentiment

Nessuna domanda (Paolo, 22/11): solo Toro o Orso, per dire come ci si sente sui mercati. Si vota sull'edizione più recente, tutto il giorno, e si cambia finché non esce l'edizione dopo; le edizioni precedenti mostrano il loro risultato senza voto (nelle anteprime il voto è sempre aperto). Il voto accompagna i commenti di chi l'ha dato, come targhetta accanto al nome.

## Difese (il lettore non le vede)

Gettone firmato dal servizio (niente invii da programmi che non hanno aperto la pagina, né prima di 3 secondi), campo trappola, richieste solo dalla pagina del sito, limiti di frequenza per lettore e per impronta dell'indirizzo IP (i numeri in `LIMITI`, in testa a `lettori.js`), nomi riservati alla redazione (la stessa regola in `lettori.js` e `assets/lettori.js`: il collaudo lo verifica), al massimo due link per commento e mai cliccabili, Segnala che nasconde un commento quando lo segnalano 3 reti diverse. Le impronte IP si cancellano dopo 30 giorni.

## Togliere un commento (finché non c'è G-51)

Per l'ordinanza 22999/2026 della Cassazione il gestore risponde se, saputo di un commento diffamatorio, non lo rimuove in fretta: quando arriva una segnalazione a redazione@gommberg.com, si toglie subito.

1. Cloudflare, Storage e database, D1, `gommberg-lettori`, Console.
2. Trovare il commento: `SELECT id, ed, nome, testo, creato FROM commenti WHERE sito = 'gommberg' AND testo LIKE '%parola%';`
3. Toglierlo: `UPDATE commenti SET nascosto = 2 WHERE id = <numero>;` (2 = tolto dalla redazione; 1 = nascosto dalle segnalazioni; 0 = visibile). Per rimetterlo: `nascosto = 0`.

I commenti delle anteprime hanno `sito = 'prova'` e non compaiono mai su gommberg.com; si possono cancellare con `DELETE FROM commenti WHERE sito = 'prova';` (e lo stesso per `voti`).

## Il database

Creato il 22/11/2026 (ID in `wrangler.jsonc`). Se un giorno andasse ricreato: Cloudflare, account del Gommberg, Storage e database, D1, Crea, nome `gommberg-lettori`, posizione automatica (Europa); il nuovo ID va in `redazione/sito/wrangler.jsonc`. Con `DA-CREARE` al posto dell'ID, `sito.yml` pubblica i soli file statici e il riquadro dice che la discussione non si carica. Il token di GitHub non ha bisogno di permessi su D1: basta quello che pubblica il Worker.

## Se il servizio si ferma

Homepage ed edizioni sono file statici e non passano dal servizio: escono sempre. La sezione mostra "La discussione non si carica" e si riprova da solo ogni 90 secondi. Se la pubblicazione con il servizio fallisce, `sito.yml` ripubblica i soli file statici (avviso nel riepilogo dell'azione). Gli errori del servizio si leggono da Cloudflare, Workers, gommberg, Observability.
