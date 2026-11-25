# G-43 - Il percorso di benvenuto: ricerca, scelte, messa in linea

Mockup, niente in linea e niente in Kit. Data: 25/11/2026.

## 1. Che cosa ho trovato

### Come fanno gli altri
- **Tre momenti, un compito per ciascuno.** Le guide di settore descrivono la stessa sequenza: pagina di conferma subito, poi una mail di benvenuto che dice quando arriva la prossima, chiede di salvare il mittente o spostarlo in Principale e invita a rispondere ([The Newsletter Newsletter, guida alla welcome email](https://thenewsletternewsletter.substack.com/p/the-newsletter-welcome-email-guide)). Lo stesso articolo cita come errore Robinhood Snacks: conferma dell'iscrizione e poi nessuna mail di benvenuto, solo l'edizione del giorno dopo. È esattamente il Gommberg di oggi.
- **Morning Brew** fa una rampa corta: conferma, dice quando aspettarla ("every morning") e propone altre cose da leggere; il tono è da amico, non da venditore ([swipefile.com](https://swipefile.com/morning-brews-welcome-email)). **1440** manda una nota breve del cofondatore, invita a leggere subito l'ultimo numero e dà due passi per arrivare in posta principale ([swipefile.com](https://swipefile.com/1440-thank-you-for-subscribing-email)). **The Daily Upside** (finanza): pagina di grazie corta, tre paragrafi, dice orario e giorni e rimanda alle sezioni ([thedailyupside.com/thankyou](https://www.thedailyupside.com/thankyou)).
- **FT**: la prima mail della serie di benvenuto è "nuts and bolts", pratica: come si usa e in quali modi si legge; le successive vendono ([Subscription Insider](https://www.subscriptioninsider.com/article-type/subscriber-only/ft-com-welcomes-registered-users-with-5-part-email-series), letto solo l'estratto pubblico).
- **Editori di notizie**: l'onboarding serve a creare l'abitudine, mostrare che cosa c'è e dare il tono; i casi buoni non chiedono nulla di commerciale nelle prime mail ([American Press Institute](https://americanpressinstitute.org/how-to-win-the-loyalty-of-new-subscribers-through-great-onboarding/)). Mostrare qualche pezzo che faccia capire che cosa aspettarsi, e non riempire di mail chi è appena arrivato ([Indiegraf](https://indiegraf.com/blog/welcome-email-best-practices-news-publishers)).
- **Che cosa non fanno i migliori**: non ripetono nella mail ciò che la pagina ha già detto, non mettono cinque inviti all'azione, non chiedono soldi, non si presentano con frasi su chi sono ("siamo una testata che..."). Molte guide "da creator" spingono invece offerte e prodotti nella prima mail ([emailbreakdown](https://emailbreakdown.beehiiv.com/p/is-your-first-email-failing)): scartato, non è il Gommberg.
- **Italiane**: per Il Post, Good Morning Italia e le newsletter italiane di finanza non ho trovato pubblicato il testo delle loro mail o pagine di benvenuto (servirebbe iscriversi). Il pezzo di Charlie sul passaggio agli abbonati ([ilpost.it](https://www.ilpost.it/charlie/benvenuti-benvenute-ben-rimasti-e-ben-rimaste/)) conferma solo il registro: sobrio, grato, nessuna vendita. Lo segnalo come limite della ricerca.
- Le misure di apertura delle mail di benvenuto (più alte della media) esistono, ma sono di piattaforme di invio e falsate dalla privacy di Apple Mail: non le uso come argomento.

### Che cosa permette Kit gratuito OGGI (verificato sulle pagine ufficiali, 25/11/2026)
- [kit.com/pricing](https://kit.com/pricing): piano Free fino a 10.000 iscritti. **Visual automations: No. Automated email sequences: No.** Sì a tagging, segmentazione, documentazione API, "Deliver opt-in incentives", moduli illimitati, 1 utente.
- [Kit Help, The Kit free plan](https://intercom.help/convertkit/en/articles/16627071-the-kit-free-plan) (pagina datata 23/09/2026): automazioni visuali e sequenze solo sui piani a pagamento.
- [Kit Help, The incentive email](https://help.kit.com/en/articles/2502655-the-incentive-email): l'"incentive email" è la mail di conferma; si cambiano mittente, oggetto e contenuto (i campi personalizzati non funzionano nell'oggetto); dopo la conferma si può mandare a un indirizzo a scelta; usa il modello predefinito dell'account. Kit consiglia di tenerla semplice, con l'attenzione sul pulsante.
- [Kit API, Create a broadcast](https://developers.kit.com/api-reference/broadcasts/create-a-broadcast.md): un invio può andare solo agli iscritti con un tag o in un segmento (`subscriber_filter`), con data e modello a scelta. La pagina non parla di limiti per piano; che l'API crei e programmi invii sul piano gratuito lo prova già `newsletter.py` ogni mattina. **Non provato**: un invio filtrato per tag sul nostro account. È il primo test da fare.

**Conclusione:** una mail che parte da sola subito dopo la conferma, con gli strumenti di Kit, sul piano gratuito non si può fare. Non ho trovato una mail di benvenuto separata nelle impostazioni del modulo.

## 2. Il percorso progettato

| Passo | Quando | Un solo compito | Che cosa NON fa |
|---|---|---|---|
| 1. Mail di conferma (`conferma-mail.txt`) | subito, da Kit | far cliccare "Confermo l'iscrizione" | niente sezioni, niente link al sito |
| 2. Pagina `benvenuto.html` (`benvenuto-pagina.html`) | al clic di conferma | dire **quando** arriva la prima edizione (giorno e ora veri), farla arrivare in Principale, far leggere **subito** l'ultima edizione | non spiega le sezioni del sito |
| 3. Mail di benvenuto (`benvenuto-mail.html`) | la sera stessa (vedi sotto), prima della prima edizione per chi si iscrive di giorno | far capire **che cosa ha in mano**: le 6 pagine, sempre nello stesso ordine; che cosa c'è sul sito accanto all'edizione; una domanda a cui rispondere | non ripete l'invito a leggere l'ultima edizione né i consigli sulla posta |

Il motivo per aprire l'edizione di domani sta in due punti: la pagina dice il giorno esatto ("Ci vediamo domani alle 9:45 - giovedì 26 novembre"), la mail spiega la scommessa come una storia a puntate (il lunedì la previsione, il venerdì la chiusura, il lunedì dopo il verdetto con la pagella pubblica).

### Scelte, e perché
- **Mail di benvenuto come guida, non come "grazie".** È la prima mail "nuts and bolts" dell'FT: con l'indice della mattina che arriva poco dopo, chi sa già che pag. 2-4 sono le analisi e pag. 6 la scommessa riconosce l'indice e sa dove cliccare. Stessa testata e stessa grafica a righe "PAG. N" dell'email del mattino, così la mail di domani si riconosce. Circa 260 parole (testata compresa), nessun pulsante: le tre righe del sito sono link.
- **Una sola richiesta: rispondere.** Diversa da "Chiedi al Gommberg" (che è in ogni edizione): qui si chiede che cosa ha portato il lettore e che cosa vuole capire. Due vantaggi: materiale per la redazione, e una risposta insegna a Gmail che il mittente è voluto, così le edizioni arrivano meglio.
- **La pagina fa ciò che conta subito**: il clic di conferma è il momento di massima attenzione e il lettore è già sul sito. Per questo la pagina mostra la copertina dell'ultima edizione (letta da `edizioni.json`, la stessa scheda della homepage) con "Leggi le 6 pagine". Tolto il link secondario "parti dal glossario": Impara passa nella mail.
- **Data vera**: la pagina calcola il giorno della prima edizione (ora di Roma, lun-ven, salta i FESTIVI del motore; prima delle 9:30 di un giorno di uscita dice "stamattina"). Provato: mer 16:00 "domani", gio 8:10 "stamattina", ven 18:00 e sab "lunedì", 24/12 "lunedì 28 dicembre", 31/12 "lunedì 4 gennaio".
- **Conferma ridotta all'osso**, come consiglia Kit; frase finale neutra ("Se l'iscrizione non è tua...").
- **Iscriviti riallineata** all'email "L'indice": la notizia leggibile senza cliccare con i mercati, una riga per pagina con il clic per le 6 pagine, "Chiedi al Gommberg". Cambiano anche la riga sotto il titolo e le due description, che parlavano ancora della "prima pagina".
- Testi dalla homepage ("Come funziona il Gommberg") per le descrizioni delle pagine: nessun dato nuovo, nessun numero inventato.

### Come si realizza con Kit gratuito
Senza automazioni, la soluzione più semplice che regge è **un invio a gruppi, fatto dalla macchina con l'API, a zero token**:
1. Nuovo `redazione/benvenuto.py` (stesso stile di `newsletter.py`/`dem.py`, funzione `kit()` comune): legge da Kit gli iscritti **attivi** (cioè confermati) arrivati nelle ultime 48 ore; toglie chi ha già il tag `benvenuto`; ai rimasti mette il tag del gruppo (`benvenuto-AAAA-MM-GG`) e il tag `benvenuto`; crea un invio con `subscriber_filter` sul tag del gruppo, modello "Gommberg cornice", contenuto = il blocco tra `CONTENUTO` e `FINE CONTENUTO` di `benvenuto-mail.html` (salvato come `redazione/benvenuto_mail.html`), etichetta `gommberg-benvenuto-AAAA-MM-GG`, partenza dopo pochi minuti. Se nessuno è nuovo non fa nulla. Il tag `benvenuto` rende ogni passo ripetibile senza doppioni.
2. **Quando**: una volta al giorno alle 19:30, nello stesso giro serale di `dem.yml` (nessun workflow nuovo, pochi secondi di GitHub: conta per G-12). Chi conferma di giorno riceve la guida la sera, prima della prima edizione; chi conferma dopo le 19:30 riceve prima l'edizione e la guida la sera dopo. La pagina ha già fatto il necessario. Per questo il testo della mail non dice mai "domani" ("Alla prossima edizione").
3. **Gli iscritti di oggi** (una decina, leggono da settimane) al primo giro ricevono solo il tag `benvenuto`, senza mail.
4. Le regole delle mail straordinarie (una al mese) non valgono qui: è un'altra etichetta, e il postino di `dem.py` non deve toccare gli invii `gommberg-benvenuto-*` (da verificare nel codice: oggi cerca le copie con la stessa etichetta). Il pannello, pagina Invii, può mostrarle come riga a parte.
5. Alternative scartate: **conferma singola con incentive email** (togliere la doppia conferma peggiora la consegna e la pulizia della lista; il comportamento non è nemmeno documentato); **benvenuto dentro la mail di conferma** (due compiti in una mail, il pulsante si perde); **piano Creator** a pagamento per l'automazione (spesa non approvata, e la soluzione con l'API fa lo stesso lavoro).

## 3. Da decidere a Paolo
1. **Firma della mail di benvenuto**: "La redazione del Gommberg" (proposta, coerente con la testata e con la riga AI senza nome) oppure "Paolo Gommellini, direttore" (più personale; è un testo fisso, scritto una volta e approvato da te)?

## 4. Per metterlo in linea
**Nel repository (ramo di rilascio, con collaudo):**
- `iscriviti.html`: lede, sezione "Cosa ricevi", meta e og description (testi in `iscriviti-cosa-ricevi.html`).
- `benvenuto.html`: struttura e stili propri di `benvenuto-pagina.html` (resta il link a `assets/sito.css`; nel file di prova gli stili sono copiati). FESTIVI e ora scritti da `pagine.py` leggendo `gommberg_engine.py`, non a mano. Senza JavaScript la scheda dell'ultima edizione deve restare generica (link a `./` e `assets/copertina.png`), non fissata su un numero.
- `redazione/benvenuto.py` + `redazione/benvenuto_mail.html` (il solo contenuto), passo in `.github/workflows/dem.yml` alle 19:30; controlli nel collaudo (testo solo con trattino corto, nessun invio se l'API risponde male, mai due invii per lo stesso iscritto).
- `privacy.html`: aggiungere tra le finalità "un'email di benvenuto dopo la conferma" (oggi dice edizione e al massimo una comunicazione al mese).
- Se G-61 sposta l'uscita: "9:45" sta in conferma, `benvenuto.html`, mail di benvenuto, `iscriviti.html` (e nella fascia della homepage).

**In Kit, a mano (dal browser):**
- Modulo 10193457 > Settings > Incentive: oggetto e testo di `conferma-mail.txt`, scritta del pulsante; redirect invariato su `https://gommberg.com/benvenuto.html`.
- Prima prova: invio di prova del benvenuto con filtro per tag su un indirizzo di casa (verifica che il filtro funzioni sul piano gratuito), poi tag `benvenuto` agli iscritti attuali.
- Nessun modello nuovo: la mail usa "Gommberg cornice", la conferma "Gommberg".

## File
- `benvenuto-mail.html` (+ `-pc.png`, `-telefono.png`)
- `conferma-mail.txt`
- `benvenuto-pagina.html` (+ `-pc.png`, `-telefono.png`; `e/033.png` serve solo al mockup)
- `iscriviti-cosa-ricevi.html` (+ `-pc.png`, `-telefono.png`)

Nota sulle immagini: qui i caratteri di Google sono bloccati; per le foto il titolo in Archivio stretto è reso con Liberation Sans Narrow e Plex Sans con un carattere simile. Sul sito vero valgono i caratteri del sito.
