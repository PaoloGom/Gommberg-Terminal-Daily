# G-62 - Portare i testi del Gommberg su Medium e piattaforme simili?

Valutazione del 25/11/2026. Solo lettura: nessun account, nessuna pubblicazione, repository non toccato.
Legenda: **[V]** = verificato sulla pagina ufficiale indicata (data della regola tra parentesi, se la pagina la riporta); **[S]** = supposto, non verificato.

## In breve

Non farlo su Medium, né come prova né come flusso. Il motivo decisivo non è la riga AI ma la lingua: Medium oggi rivede solo storie in inglese, quindi un pezzo in italiano resta visibile solo ai follower dell'account, che per un account nuovo sono zero. Prima di qualsiasi piattaforma esterna c'è un lavoro più utile sul nostro sito: oggi i testi delle Analisi e storie esistono solo nel PDF, non in pagine HTML del sito, quindi né Google né nessun aggregatore li può leggere, e una copia esterna sarebbe l'unica versione leggibile del testo (cioè la concorrenza peggiore possibile per il sito).

## Che cosa ho trovato nel repository (fatto, non supposto)

- `e/033.html` contiene titolo, sommario, "Cosa significa", "In 30 secondi", titoli delle notizie, titoli delle analisi con il rimando alla pagina del PDF, agenda. Il corpo delle 5 analisi non c'è: sta solo in `pdf/2026-11-25-gommberg-033.pdf`.
- `feed.xml`: 30 voci, ognuna con il sommario (non il testo completo) e il PDF allegato.
- `sitemap.xml`: 42 indirizzi; `robots.txt` apre tutto il sito.
- Ogni pagina porta la riga AI ("Testi generati con l'intelligenza artificiale...") e GoatCounter con eventi sui clic di iscrizione.

Conseguenze: lo strumento di importazione di Medium e il link canonico presuppongono una pagina del sito con lo stesso testo; per le analisi quella pagina non esiste. Lo stesso vale per Flipboard (vuole un feed con il testo completo).

## Tabella delle piattaforme

| Piattaforma | Regole verificate (fonte, data) | Lingua / pubblico italiano | Porta al sito? | Misura |
|---|---|---|---|---|
| **Medium** | **[V]** Testo generato con AI: va dichiarato; testo assistito: dichiarazione nei primi due paragrafi; mai dietro paywall del Partner Program; se dichiarato è "eligible for General Distribution" ma non per Boost; se non dichiarato solo Network; violazioni: restrizioni dell'account o sospensione dei contenuti (help.medium.com/hc/en-us/articles/22576852947223, nessuna data in pagina). **[V]** Linee guida di distribuzione: "AI-generated content" tra i contenuti a basso valore esclusi dalla General Distribution; per Boost la storia deve essere "human-created"; esclusi i pezzi il cui scopo principale è "gathering signups/traffic" (help.medium.com/hc/en-us/articles/360006362473, aggiornata 14/08/2024). Le due pagine si contraddicono sulla General Distribution dei testi AI dichiarati. **[V]** Link canonico impostabile a mano; lo strumento di importazione lo imposta da solo verso la fonte e retrodata il pezzo (articles/360033930293 e 214550207, senza data). **[V]** Regole: promozione del proprio sito e mailing list ammessa; vietato pubblicare "primarily to drive traffic to... an external site"; vietati i duplicati su Medium; ammesso il cross-post dal proprio blog se si hanno i diritti (policy.medium.com/medium-rules-30e5502c4eb4, "Updated June 2023"). **[V parziale]** Diritti: l'autore resta proprietario, licenza non esclusiva a Medium; cancellando, copie di backup fino a 14 giorni (help.medium.com/hc/en-us/articles/360053078253, versione "Effective March 7, 2016": è l'archivio dei termini; la pagina dei termini in vigore su policy.medium.com non si è aperta). | **[V]** "We can only review stories written in English at this time": senza revisione niente Boost né General Distribution (articles/360006362473, 14/08/2024). Pubblico italiano su Medium: **[S]** scarso. | Sì, con link nel testo, ma con distribuzione solo ai follower il traffico atteso è vicino a zero. | Clic in arrivo con `utm_source=medium` su GoatCounter **[V]**; statistiche di lettura di Medium **[S]**. |
| **Substack** | **[V]** Linee guida dei contenuti (substack.com/content, aggiornate 29/09/2026): nessuna regola generale sui testi AI; vietate le pubblicazioni il cui scopo principale è "drive traffic to third party sites"; plagio vietato; brand e organizzazioni commerciali possono avere verifiche in più. Link canonico verso un sito esterno: **[S]** non disponibile. | **[S]** Esistono newsletter italiane di finanza personale, pubblico in crescita ma di nicchia. | No: è una seconda newsletter con i suoi iscritti, in concorrenza con Kit e con il sito. Un flusso usato per spingere al sito va contro la regola sopra. | Iscritti Substack, non nostri. Clic al sito con UTM **[V]**. |
| **LinkedIn** (articoli, newsletter di Pagina) | Le pagine di aiuto LinkedIn non si aprono allo strumento di lettura (bloccate da robots): **non verificato**. Unica fonte aperta, un PDF ufficiale di LinkedIn senza data (dal nome del file, novembre 2023): newsletter con modalità Creator, più di 150 follower e collegamenti, un contenuto originale negli ultimi 90 giorni; a ogni numero gli iscritti ricevono notifica e email; chi si iscrive diventa follower (members.linkedin.com/.../li4c-newsletters-microsite-doc-231129.pdf). Probabilmente superato **[S]**. Regole su AI e portata dei link esterni: **[S]**. | Sì, ed è già il canale dove stanno i lettori di oggi. | In parte: l'articolo o la newsletter tengono il lettore su LinkedIn; un post breve con link porta al sito. | Clic al sito con UTM **[V]**; numeri di LinkedIn **[S]**. |
| **Google News** | **[V]** Dal 2025 l'inclusione è automatica: niente più feed o indirizzi inviati dal Publisher Center; i contenuti conformi sono idonei da soli; logo = favicon, nome = nome del sito (support.google.com/news/publisher-center/answer/15898024, aggiornata 20/03/2025). **[V]** Requisiti: date e firme chiare, informazioni su autori, testata, editore e proprietà, contatti; rispetto delle regole antispam di Search (answer/6204050, nessuna data in pagina; cita la regola sull'abuso di reputazione del 05/05/2024). Nessuna regola specifica sui testi AI in quella pagina. **[V]** Per le copie ripubblicate altrove Google News sconsiglia il canonico e chiede `noindex` sul sito che ripubblica (answer/9606800, senza data). | Sì, è dove si cercano le notizie in italiano. | Sì: i lettori arrivano sul nostro sito. | Referrer Google su GoatCounter **[V]** (sorgente rilevata dal referrer se manca l'UTM). |
| **Flipboard** | **[V]** Per portare un feed RSS: testo completo (non estratti), un'immagine di almeno 400 px, almeno 30 voci (about.flipboard.com/inside-flipboard/rss-feed-on-flipboard/, aggiornata 19/09/2023). Il nostro feed ha 30 voci ma solo sommari: oggi non è idoneo. | **[S]** Pubblico italiano modesto. | **[S]** Apre l'articolo dentro l'app o rimanda al sito, a seconda dei casi. | Referrer **[S]**. |
| **Telegram / WhatsApp Channels** | Non verificato sulle pagine ufficiali. **[S]** Canali gratuiti, messaggi con link; Telegram pubblicabile in automatico con un bot gratuito, WhatsApp Channels no. | **[S]** Molto usati in Italia, anche per finanza. | Sì: un messaggio al giorno con il link all'edizione. | Clic con UTM **[V]**; iscritti al canale **[S]**. |
| **Reddit** (es. r/ItaliaPersonalFinance) | Pagina delle regole bloccata: **non verificato**. **[S]** Autopromozione di norma vietata o molto limitata. | **[S]** Sì, ma ostile ai link promozionali e ai testi AI. | Sì se tollerato, ma rischio ban. | UTM **[V]**. |
| **MSN / aggregatori italiani** | Non verificato. **[S]** MSN accetta solo editori partner selezionati; aggregatori come Google News sono già coperti dall'inclusione automatica. | - | - | - |

## Che cosa si potrebbe pubblicare e che cosa no

Ammissibile (su qualsiasi piattaforma, solo dopo che il testo esiste sul nostro sito):
- Un post breve di 3-5 righe scritto apposta (non copiato) con il link all'analisi sul sito: nessun duplicato, nessun conflitto con Google.
- Un estratto (attacco e un grafico) con "continua sul Gommberg" e il link: duplicato parziale, rischio basso.

Da non fare:
- L'analisi intera fuori dal sito finché sul sito c'è solo il PDF: la copia esterna sarebbe l'unico testo leggibile dai motori, e il canonico non aiuterebbe (Google lo sconsiglia per le copie su altri domini, **[V]** answer/9606800).
- L'edizione a testo completa ogni giorno: è un secondo giornale, fuori dal nostro controllo, che si corregge solo a mano.
- Qualsiasi pezzo senza la riga AI: su Medium la dichiarazione è obbligatoria **[V]**, e per la testata vale sempre.

## Tre opzioni a confronto

| | Niente | Prova su un solo pezzo (Medium) | Flusso regolare (Medium o simili) |
|---|---|---|---|
| Token | 0 | Una sessione per adattare un pezzo **[S]** poche decine di migliaia di token, una volta | Ogni giorno: adattamento + pubblicazione. API di Medium **[S]** non più aperta ai nuovi token: resterebbe il lavoro a mano o un'automazione a token. Contro il vincolo "zero token al giorno". |
| Lavoro di Paolo | 0 | Account sulla casella del Gommberg, controllo, pubblicazione: circa 30-45 minuti **[S]** | Pubblicazione quotidiana a mano o approvazione di un flusso nuovo da scrivere nella mappa. |
| Rischio per la testata | Nessuno | Basso ma non nullo: un errore pubblicato su Medium resta in copia anche dopo la correzione sul sito; cancellando restano backup 14 giorni **[V]**, più copie e cache altrui **[S]**. | Alto: ogni errore si moltiplica fuori dal sito; la regola "mai errata corrige" non si applica a copie che non controlliamo; un account sospeso per i testi AI **[V]** è un danno di immagine. |
| Effetto su Google | Neutro | Lieve rischio: Medium ha più autorità del nostro dominio, e il canonico è solo un suggerimento. | Rischio concreto di concorrenza con le nostre pagine, aggravato dal fatto che le analisi non stanno in HTML sul sito. |
| Lettori attesi | 0 | Vicino a 0: storia in italiano = solo ai follower **[V]**, account nuovo = 0 follower. | Vicino a 0 per lo stesso motivo; poche decine nel caso migliore **[S]**. |

## Raccomandazione

**Non fare Medium, né la prova né il flusso.** Una prova su un pezzo in italiano misurerebbe solo la regola sulla lingua, che è già verificata: costerebbe lavoro a Paolo senza dare informazioni. Substack ha lo stesso difetto in un'altra forma (tiene i lettori su una newsletter non nostra).

**Meglio prima un altro canale, nell'ordine:**
1. **Il sito stesso**: mettere il testo delle Analisi e storie in pagine HTML del sito (una per analisi o dentro la pagina dell'edizione), con data, firma della testata e riga AI. Costo in token quasi nullo se il testo esce già dal JSON dell'edizione **[S]**, nessun lavoro quotidiano di Paolo. Apre Google, Google News (automatico, **[V]**) e un feed completo per Flipboard. È un flusso nuovo: va scritto nella mappa e deciso da Paolo, perché cambia ciò che il lettore vede.
2. **LinkedIn con un post breve e il link** alla singola analisi (non l'articolo intero): è il canale dove ci sono già i lettori.
3. **Telegram** (o WhatsApp Channel) con il link quotidiano, solo se il punto 1 è fatto: un messaggio automatico senza token **[S]**.

Medium e Substack si possono rivalutare solo se un giorno il Gommberg avrà un'edizione in inglese.

## Come si misura una prova di due settimane (per il canale scelto, non per Medium)

- Link sempre con `?utm_source=<canale>&utm_campaign=g62-<aaaa-mm-gg>`: GoatCounter crea la campagna da solo e la mostra nel riquadro "Campaigns" **[V]** (goatcounter.com/help/campaigns).
- Metriche: visite per sorgente; clic su "Iscriviti" (eventi già presenti, `invito-iscrizione`, `invito-primo-schermo`) nelle stesse giornate; nuovi iscritti Kit nelle due settimane rispetto alle due precedenti. Limite: GoatCounter non lega la visita da una campagna al clic di iscrizione successivo **[S]**, quindi l'attribuzione delle iscrizioni è per periodo, non per lettore.
- Soglia decisa prima: per esempio almeno 50 visite e 3 iscrizioni dal canale in 10 edizioni; sotto, si chiude. Lavoro di Paolo: meno di 10 minuti al giorno, altrimenti la prova è già fallita sul criterio di sostenibilità.

## Che cosa non ho potuto verificare

- Termini di servizio di Medium in vigore (pagina non aperta: ho letto solo la versione d'archivio del 2016).
- Tutte le pagine di aiuto LinkedIn (bloccate da robots).
- Regole di Reddit (sito bloccato), WhatsApp e Telegram Channels, MSN.
- Statistiche e pubblico italiano reale di ogni piattaforma.
