# G-64 - Il testo delle analisi sul sito: verifica, mockup e raccomandazione

27/11/2026, ramo `g64`. Solo verifica e mockup: `pagine.py`, le pagine vere, il motore e il PDF non sono toccati.
Legenda: **[V]** verificato (nel repository o sulla pagina ufficiale indicata, con la data di aggiornamento che la pagina riporta); **[S]** supposto.

## 1. Che cosa legge oggi un motore

- **`e/035.html`** **[V]**: 728 parole visibili. Ci sono titolo, dek, "Cosa significa", "In 30 secondi", i 6 titoli delle notizie, i **soli titoli** delle 4 analisi (con il link al PDF, pag. 2-4), l'agenda, le sigle, dati strutturati `NewsArticle` della pagina. Il corpo delle analisi, i riquadri, i grafici e le righe Fonti non ci sono. La pagina vera su gommberg.com non si apre da qui (il proxy blocca il dominio): ho confrontato il file del repository, che il collaudo dichiara identico al generato.
- **`feed.xml`** **[V]**: 30 voci, ognuna con il dek come `description` e il PDF come `enclosure`. Niente testo completo.
- **Il PDF** **[V]**: ha uno strato di testo vero (`pdftotext` ne tira fuori 3.501 parole per il n. 035) e i grafici sono vettoriali (nessuna immagine dentro). Google indicizza i PDF (developers.google.com/search/docs/crawling-indexing/indexable-file-types, agg. 03/02/2026). Quindi il testo non è invisibile: è chiuso in un unico file di 6 pagine, con 4-5 temi mescolati, senza titolo per tema, senza dati strutturati, senza indirizzo per singola analisi. Se e quanto Google mostri oggi i nostri PDF non l'ho potuto vedere (serve Search Console) **[S]**.

## 2. Che cosa c'è nei sorgenti archiviati

- `redazione/sorgenti/AAAA-MM-GG/edizione.py` contiene il dizionario `C` con, per ogni analisi (`C["moduli"]`): `tema`, `titolo`, `perche`, `quindi`, `numero` (43 su 46), `testo` (2-5 paragrafi), `guardare`, `fonte` e i grafici come **dati** (`tipo`, serie, titolo, sottotitolo, soglie) **[V]**. Il catenaccio come campo **non esiste**: nel mockup fa da catenaccio il "Perché" (1-2 frasi). Tabelle (`righe`) e `punti` ci sono in alcune analisi (correzione del 27/11 sera: la prima lettura li aveva mancati); le pagine costruite li riportano.
- Le riscritture del desk stanno in `desk_ok.json` accanto: si applicano con `desk.applica(C)`, come fa il motore. Fatto questo, i 46 titoli ricavati coincidono tutti con quelli di `edizioni.json` **[V]**.
- **Tutto si genera a zero token** **[V]**: `estrai.py` (in questa cartella) carica `edizione.py` senza impaginare, applica il desk e ridisegna i grafici con le stesse funzioni del motore (`linee`, `barre`, che salvano già un gemello SVG). Testo medio: 253 parole per analisi.
- **Edizioni recuperabili: 10 su 35** (n. 026-035, dal 16/11), 46 analisi, 50 grafici, tutte rifatte qui senza errori **[V]**. Le n. 001-025 hanno solo il PDF: se ne può estrarre il testo con `pdftotext`, ma senza struttura (titoli, riquadri, fonti da separare a mano) e senza i dati dei grafici. Consiglio: lasciarle solo PDF.
- Peso: i grafici in SVG (due misure, PC e telefono) fanno circa 290 KB per edizione, il doppio del PDF medio (146 KB) **[V]**; con il testo dei grafici salvato come testo e non come tracciati (`svg.fonttype` `none`) scenderebbero **[S]**.

## 3. Rischi SEO, pesati sulle pagine di Google Search Central

- **Contenuto duplicato PDF/HTML.** Per i file non HTML Google accetta un'intestazione HTTP `Link: <...>; rel="canonical"` che indica la versione principale, ed è "a strong signal", non un obbligo; vale per i doppioni "duplicate or very similar" (consolidate-duplicate-urls, agg. 10/07/2026) **[V]**. La pagina non parla di penalità per i doppioni **[V]**. Da noi si può fare a zero costi con il file `_headers` che `costruisci.py` già scrive **[V]** (che Cloudflare lo applichi ai PDF **[S]**, da provare). Con A il canonico PDF -> `e/NNN.html` è pulito (stessa edizione, stesso testo). Con B il PDF contiene 4-5 pagine diverse: il canonico verso una di esse non regge; resta verso `e/NNN.html`, meno simile, che Google può ignorare **[S]**.
- **Dati strutturati.** Per `Article`/`NewsArticle` "There are no required properties"; consigliati `author` (con `url`), `datePublished`, `dateModified` con fuso, `headline`, `image` in 16x9, 4x3 e 1x1 con almeno 50.000 pixel (article, agg. 08/09/2026) **[V]**. Oggi diamo una sola immagine 1200x630: per B servirebbe un'immagine per analisi o la copertina dell'edizione **[S]**.
- **Testi generati con l'AI.** Google chiede di spiegare come è stata usata l'automazione, di verificare i fatti prima di pubblicare, e mette tra lo spam "generate many pages without adding value" (using-gen-ai-content, agg. 01/10/2026; spam-policies, "scaled content abuse", agg. 23/11/2026) **[V]**. Nessuna etichetta tecnica obbligatoria per il testo (l'IPTC vale per le immagini su Merchant Center) **[V]**. La nostra riga AI e la gerenza bastano; il rischio "scaled" pesa un po' di più su B (5 pagine nuove al giorno, 250 parole l'una) che su A **[S]**.
- **Sitemap.** `lastmod` solo se esatto, `priority` e `changefreq` ignorati, 50.000 indirizzi per file, solo indirizzi canonici (build-sitemap, agg. 08/07/2026) **[V]**. Con B si arriva a circa 1.500 indirizzi in un anno: nessun limite vicino. La sitemap per Google News è facoltativa e tiene solo gli ultimi 2 giorni (news-sitemap, agg. 10/12/2025) **[V]**.

## 4. I mockup (testo e grafici veri del n. 035, CSS e caratteri del sito)

Pagine in `mockup/`, rigenerabili con `estrai.py` e `mockup.py`. Immagini: `A-pc.png`, `A-telefono.png`, `A-telefono-scuro.png`, `B-pc.png`, `B-telefono.png`, `B-pc-scuro.png`, `confronto.png`. Il sito ha i temi chiaro e scuro: i grafici restano su fondo bianco, come un ritaglio del giornale.
- **A** (`A-edizione-035.html`): sotto le notizie, "Analisi e storie" diventa un indice cliccabile più le 4 analisi intere (tema, pagina del giornale, titolo, Perché come catenaccio, grafici, Il numero, E quindi e Da guardare in riquadri, Fonti, "Leggila impaginata nel giornale, pag. N"), poi il riquadro scuro con la copertina e "Leggi l'edizione". La Gommunity resta dov'è, più su. La pagina passa da 3.748 a 10.834 px su PC e da 4.521 a 13.073 px sul telefono: agenda e sigle finiscono in fondo, il testo comincia a 1.800 px (PC) e 2.200 px (telefono).
- **B** (`B-analisi-035-corea.html`, indirizzo proposto `e/035/corea.html`): titolo proprio in H1, catenaccio, "Leggi il giornale" in testa, a destra su PC la copertina con "Leggi l'edizione" e le altre analisi del giorno; sul telefono una striscia "Leggi il giornale" sotto la testata e gli stessi blocchi in fondo, più l'invito alla Gommunity dell'edizione. Pagina di 3.054 px (PC). `B-edizione-035.html` mostra la pagina dell'edizione invariata, con le analisi che portano alla loro pagina; homepage "Da leggere" e archivio avrebbero lo stesso link (non disegnati).

## 5. Raccomandazione: B

- **Lettore:** chi arriva da Google trova la risposta in alto, con un titolo che è la sua ricerca, e a un clic il giornale; la pagina dell'edizione resta corta e uguale a oggi, quindi chi viene per il giornale non scorre 7.000 px di testo per arrivare all'agenda. A rovescia la pagina: il testo diventa la lettura principale e il PDF un rimando in fondo.
- **Google e motori AI:** un indirizzo, un titolo, una descrizione e un `NewsArticle` per tema sono ciò che un motore abbina a una ricerca ("fondo di stabilizzazione Kospi"); con A ogni pagina parla di 4-5 temi sotto un solo titolo. Il prezzo di B è il canonico del PDF meno pulito (sopra) e più pagine brevi da tenere di qualità.
- **Tra un anno (300 edizioni):** B dà circa 1.300-1.500 pagine piccole, tutte dallo stesso modello, e un archivio per tema possibile (G-35); A dà 300 pagine lunghe 3 volte quelle di oggi. Manutenzione simile: un solo generatore in entrambi i casi.
- **Rischio per il PDF:** più basso con B, perché la pagina dell'edizione e il visore restano il percorso di chi legge il giornale; il testo sul sito serve chi arriva da fuori.

**Che cosa costa costruire B** (dopo l'ok di Paolo): un modulo nuovo (per esempio `redazione/analisi_sito.py`, la logica di `estrai.py`) chiamato da `pagine.py`, che legge `redazione/sorgenti/<data>/` (già archiviati da `pubblica.sh` prima di `pagine.py`) e scrive `e/NNN/<chiave>.html` e i grafici; se qualcosa manca o fallisce salta l'analisi e l'edizione esce comunque. Tocca `pagine.py` (link dalle schede delle analisi, sitemap, feed se si vuole il testo), `index.html` e `archivio.html` (un link per analisi), `costruisci.py` solo per il canonico dei PDF in `_headers`, `collaudo_sito.py` e `collaudo.py` (pagine generate identiche, mappa), `ARCHITETTURA.md`. È catena: ramo `rilascio`, finestra con Paolo; non cambia il PDF né ciò che scrive il mattino, quindi niente edizione di prova **[S]** (decide la chat del rilascio). Edizioni passate: le 10 con sorgenti (n. 026-035, 46 pagine) in un solo giro, le 25 più vecchie restano solo PDF. Lavoro stimato: una sessione Opus di sviluppo più il collaudo **[S]**; poi prima lettura in Search Console dopo due settimane.

## Che cosa non ho potuto verificare

- La pagina vera su gommberg.com e le intestazioni HTTP dei PDF (dominio bloccato dal proxy di questa sessione).
- Se Google oggi indicizza e mostra i nostri PDF, e con quali ricerche (serve Search Console).
- Che Cloudflare applichi `_headers` con `Link: rel="canonical"` ai PDF serviti dagli asset statici.
- Negli screenshot i caratteri sono Archivo e IBM Plex scaricati dal repository di Google Fonts su GitHub (fonts.googleapis.com bloccato qui): stessi caratteri, ma non la stessa copia che serve il sito.

## 6. Costruita (27/11 sera, dopo l'ok di Paolo su B)

- `redazione/analisi_sito.py`, chiamato da `pagine.py`. Due tempi: estrazione una volta per edizione (processo a parte, `edizione.py` + desk -> `redazione/sorgenti/<data>/analisi.json` e grafici SVG in `e/NNN/`), poi le pagine `e/NNN/<chiave>.html` a ogni pubblicazione. Non blocca mai: sorgente rotto = `analisi.json` con `"errore"`, un avviso, nessuna pagina; titolo diverso da `edizioni.json` = quella pagina non nasce.
- Indirizzi `e/NNN/<chiave>.html` (es. `e/035/corea.html`): la chiave del modulo, non il titolo.
- PDF: nessuna intestazione `Link: rel="canonical"`. Google la prevede per pagine "duplicate or very similar" (consolidate-duplicate-urls, agg. 10/07/2026); un PDF contiene 4-5 analisi più mercati, agenda e scommessa, non è il doppione di nessuna pagina.
- 46 pagine da 10 edizioni (n. 026-035); le n. 001-025 senza pagine. Testo identico al PDF: 562 testi su 562 (titoli, perché, e quindi, numero, testo, da guardare, fonti, punti e celle delle tabelle; pdftotext), verificato dal collaudo a ogni giro.
- Immagini in `costruita/`.
