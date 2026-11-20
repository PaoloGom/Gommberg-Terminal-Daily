# Stato del Gommberg

Aggiornato: 20/11/2026 pomeriggio (G-11 in corso). Deve bastare da solo a una chat nuova. Lo riscrive Claude in corsa, a ogni decisione, insieme al Registro.

Lista delle cose da fare: il **Registro dei lavori** (artifact `97f08bbc-950b-4b6e-83eb-4b8d032a3783`, https://claude.ai/artifact/KmCtJUZFx2WKVCRaDiHPtE). Una voce si legge per codice (`db_query` su `tasks`, `codice` = "G-xx").

## In linea
- Istruzioni v9.0 (struttura nuova delle 6 pagine), scommessa metodo 1.3 dal 16/11, 28 edizioni (ultima #028 del 18/11).
- Sito con homepage B, riquadri dei mercati per il neofita, pagina Impara.
- Newsletter con Kit da redazione@gommberg.com (SPF/DKIM/DMARC ok), un solo pulsante verso il sito dal 17/11.
- #028 corretta il 19/11 notte nel lessico (guidance, buy, le vendite): PDF e sito rifatti, newsletter non ripartita. Causa delle traduzioni in `glossario.json` (lessico "previsioni" al posto di guidance): si toglie in G-07.
- Edizioni #027 e #028 controllate (G-01, 18/11): avvio 8:59, uscita 9:28; nessuna pagina negata. Il file dei permessi (`.claude/settings.json`) non fa da filtro: l'attività gira con approvazione automatica e apre anche siti fuori elenco.

## Cantiere attivo
**Affidabilità della macchina** (pilastro 5), rilascio del weekend 21-22/11, pacchetto "La macchina" del Registro:
Ordine: G-34 e G-02 insieme (uno corregge, l'altro misura), poi G-03. Decisioni del 18/11 notte, dettagli nelle voci:
- G-34 causa trovata: la regola v8 "vale chi ha scritto, non chi ospita" (in linea dal 14/11) fa valere livello 1 una copia d'agenzia da qualunque sito e per `controlli_fatti.py` una fonte di livello 1 basta: la redazione chiude la scheda alla prima copia e smette di cercare. Deciso (19/11): fatti con primaria per prima se esiste, altrimenti due autori diversi, come ultima scelta uno dichiarato "(Testata)" (unica regola rigida, nel controllo); letture di top story e analisi a carta bianca con il solo metodo delle quattro voci (nel fatto, chi racconta, chi interpreta, Europa e Italia), nessuna soglia; "contro" e stile invariati. Benchmark: fonti come la #025 (simulazione: 0 schede fuori regola, contro 12 nella #028), ricerche e letture come la #026 (25-30 ricerche, 3-4 autori per analisi). Prima di G-07;
- G-02: niente cancello vero, le fonti le governa `fonti.json`; dal file dei permessi esce l'elenco dei 196 siti. Il gancio dei token annota a costo zero ricerche e pagine fallite; il pannello mostra per edizione ricerche, pagine fallite e notizie a fonte singola (la misura di G-34);
- G-03 EODHD approvato, anche con un connettore gratuito. Chiave ricevuta da Paolo (mai nel repository). Piano gratuito: 20 chiamate al giorno più 500 di benvenuto; l'email elenca azioni, ETF, fondi, cambi e cripto ma non gli indici: la copertura dell'Euro Stoxx 50 va provata per prima (dalla chat non si raggiunge eodhd.com).
Gli altri lavori del weekend sono nel Registro, in ordine.

## Prossimo passo
G-11, sito anche su gommberg.com (Opus): il lavoro è pronto e provato sul ramo `dominio` (Cloudflare Workers con soli file statici, pubblicato da GitHub Actions; dettagli nella voce del Registro). Manca l'accesso a Cloudflare: venerdì 20/11 sera con Paolo al PC (token e Account ID come segreti GitHub, www, prima pubblicazione e collaudo dal vivo), poi `dominio` entra in main e parte il doppio binario. Proposta in attesa di ok: passaggio nel weekend 28-29/11, dopo una settimana di edizioni vere. Sabato 21/11 il rilascio del motore resta com'era.

## Regole del ritmo
- Lun-ven il ramo principale non si tocca, salvo guasti e i file di stato della redazione; bozze sul ramo `prova`. Un rilascio nel weekend, tutto pulito entro domenica sera.
- Modello: Sonnet per controlli e piccole correzioni; Opus per dati, motore, decisioni, sito; Fable solo per revisioni grandi e rare.
- Una chat per tema; se si allunga, si chiude salvando qui e nel Registro e si riparte da una nuova.

Ultima revisione del patto (skill "gommberg"): 18/11/2026 (lettura del Registro per codice).
