# La parola ai lettori (G-13)

La colonna accanto all'edizione (homepage) e il riquadro nelle pagine `e/NNN.html`: la domanda del giorno con il voto Toro/Orso, i commenti con risposte a un livello, i like e Segnala. Nessuna iscrizione, nessuna email, nessuna approvazione prima della pubblicazione (Paolo, 22/11).

## Le parti

| Parte | File | Che cosa fa |
|---|---|---|
| Servizio | `redazione/sito/lettori.js` | L'unico codice che gira sul sito: Cloudflare lo chiama solo per `/api/*`. Legge e scrive nel database D1, applica le difese |
| Database | D1 `gommberg-lettori` (Cloudflare) | Tabelle `commenti`, `piaciuti`, `segnalazioni`, `voti`, `config` (il segreto delle firme). Le crea il servizio al primo uso |
| Riquadro | `assets/lettori.js`, `assets/lettori.css` | Lo stesso in homepage e nelle edizioni: `LETTORI.monta(elemento, edizione)` |
| Domanda | `pagine.py` (`domande`) | Scrive nel campo `lettori` di ogni edizione (`e/NNN.json`, `dati/recenti.json`) la domanda, le etichette, la verifica del giorno prima e l'esito |
| Collaudo | `redazione/sito/prova_lettori.mjs`, `collaudo.py` (`passo_lettori`) | Il servizio vero contro un D1 finto, la domanda su casi costruiti, la configurazione |

## La domanda del giorno

Sempre "oggi l'S&P 500 sale o scende?" (sale = Toro, scende = Orso), calcolata dalle chiusure di `scommessa/dati/spx.csv`: con tre o più sedute nella stessa direzione "Dopo N cali (rialzi) di fila, ...", con un movimento di almeno l'1% e senza verifica di ieri "Dopo il -2,0% di ieri, ...". Il giorno dopo, in testa alla domanda, la verifica: "Ieri l'S&P 500 ha chiuso a +0,8%: ha vinto il Toro. Lo aveva detto il 63% dei lettori" (solo se quel giorno qualcuno aveva votato). Il voto si chiude all'apertura di Wall Street (9:30 a New York); nei giorni con Wall Street chiusa (`PARZIALI` di `prepara.sh`, letto da `giorni.py`) la domanda non esce e restano i commenti. Il motore non scrive nulla: la domanda scritta dalla redazione è un passo successivo.

## Difese (il lettore non le vede)

Gettone firmato dal servizio (niente invii da programmi che non hanno aperto la pagina, né prima di 3 secondi), campo trappola, richieste solo dalla pagina del sito, limiti di frequenza per lettore e per impronta dell'indirizzo IP (i numeri in `LIMITI`, in testa a `lettori.js`), nomi riservati alla redazione (la stessa regola in `lettori.js` e `assets/lettori.js`: il collaudo lo verifica), al massimo due link per commento e mai cliccabili, Segnala che nasconde un commento quando lo segnalano 3 reti diverse. Le impronte IP si cancellano dopo 30 giorni.

## Togliere un commento (finché non c'è G-51)

Per l'ordinanza 22999/2026 della Cassazione il gestore risponde se, saputo di un commento diffamatorio, non lo rimuove in fretta: quando arriva una segnalazione a redazione@gommberg.com, si toglie subito.

1. Cloudflare, Storage e database, D1, `gommberg-lettori`, Console.
2. Trovare il commento: `SELECT id, ed, nome, testo, creato FROM commenti WHERE sito = 'gommberg' AND testo LIKE '%parola%';`
3. Toglierlo: `UPDATE commenti SET nascosto = 2 WHERE id = <numero>;` (2 = tolto dalla redazione; 1 = nascosto dalle segnalazioni; 0 = visibile). Per rimetterlo: `nascosto = 0`.

I commenti delle anteprime hanno `sito = 'prova'` e non compaiono mai su gommberg.com; si possono cancellare con `DELETE FROM commenti WHERE sito = 'prova';` (e lo stesso per `voti`).

## Il database

Creato il 22/11/2026 (ID in `wrangler.jsonc`). Se un giorno andasse ricreato: Cloudflare, account del Gommberg, Storage e database, D1, Crea, nome `gommberg-lettori`, posizione Europa occidentale. il nuovo ID va in `redazione/sito/wrangler.jsonc`. Con `DA-CREARE` al posto dell'ID `sito.yml` pubblica i soli file statici e il riquadro dice che la discussione non si carica. Il token di GitHub non ha bisogno di permessi su D1: basta quello che pubblica il Worker.

## Se il servizio si ferma

Homepage ed edizioni sono file statici e non passano dal servizio: escono sempre. Il riquadro mostra "La discussione non si carica" e si riprova da solo ogni 90 secondi. Se la pubblicazione con il servizio fallisce, `sito.yml` ripubblica i soli file statici (avviso nel riepilogo dell'azione). Gli errori del servizio si leggono da Cloudflare, Workers, gommberg, Observability.
