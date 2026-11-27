# G-51 - mockup dell'area riservata (27/11/2026)

Solo disegno: nessun accesso, sessione o API. Da guardare per primo: `insieme.png`. Le pagine statiche sono in `mockup/` (`index.html` è la prima schermata, poi `gommunity.html`, `sicurezza.html`, `accesso.html`, `sito-con-barra.html`). Usano lo stile vero: `mockup/area.css` è il CSS di `pannello/index.html` più le aggiunte dell'area; accesso e barra usano `assets/sito.css` e `assets/lettori.css`. Dati presi da `pannello/registro.json`, `invii.json` ed `edizioni.json`; i lettori sono nomi del dado, i commenti sono inventati.

## Scelte di disegno

- **Una sola area, il pannello di oggi allargato**: stessa barra laterale nera, con tre gruppi (Pannello: Panoramica e le sue cinque pagine; Lettori: Gommunity; Account: Sicurezza). In fondo: Posta (apre Gmail), Torna al sito, Esci.
- **La Panoramica è la prima schermata**: in cima quattro riquadri con il loro semaforo (edizione di oggi e controlli, segnalazioni aperte, servizio dei commenti, prossima mail straordinaria), ognuno con il suo tasto. Sotto restano i numeri di oggi del pannello e la tabella delle edizioni, con due colonne nuove (commenti e sentiment) e il riquadro "Gommunity oggi". Niente elenco di cose da fare: quello resta nel Registro dei lavori.
- **Gommunity**: un elenco unico con il testo intero, prima i commenti da guardare. Le azioni frequenti sono tasti a vista (Togli, Rimetti, Azzera, Fissa); quelle rare stanno nel menu "···" (Blocca il lettore, Libera il nome, Chiudi la discussione). A destra chi ha scritto il commento selezionato (i suoi tre nomi, le segnalazioni) e l'interruttore Aperta/Chiusa per ogni edizione.
- **Accesso e barra nello stile del sito** (angoli vivi, nero e arancione, caratteri mono), l'area nello stile del pannello. La firma "Gommberg" ha il logo, il badge nero e arancione "Redazione" e un fondo arancione leggero quando il commento è fissato in alto; sul sito, accanto ai commenti dei lettori, Paolo vede anche "Togli".
- I colori delle variazioni dicono meglio o peggio, come nel pannello; verde e rosso di Toro e Orso restano quelli del sito.

## Su cosa deve decidere Paolo

1. **Il cambio della password dalla scheda Sicurezza.** La scheda dice "solo tra i segreti di Cloudflare", ma il servizio non può riscrivere un segreto. Le strade sono due: (a) il tasto c'è e salva sul server solo l'impronta cifrata della password nuova (il segreto serve per il primo accesso); (b) il tasto non c'è e la scheda spiega come cambiarla su Cloudflare. Il mockup mostra la (a).
2. **Approvare la mail straordinaria dall'area** (tasto "Approva" nella prima schermata) oppure lasciare l'approvazione in chat com'è oggi, con l'area che mostra solo data, stato e anteprima.
3. **Togliere un commento anche dal sito** (il link "Togli" sotto ogni commento quando sei collegato) oppure solo dalla scheda Gommunity, così sul sito vedi la pagina come la vede un lettore.
