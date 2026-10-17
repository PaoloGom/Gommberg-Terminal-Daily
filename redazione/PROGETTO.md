# Gommberg Terminal Daily - scheda di progetto

Documento di riferimento del progetto: cosa esiste, come funziona, cosa viene dopo. Si aggiorna a ogni modifica.

## Cosa è
Rassegna quotidiana dei mercati globali in PDF di 6 pagine, stile Bloomberg, in italiano. Esce dal lunedì al venerdì verso le 9:45 (ora di Roma). Editore: Paolo. Redazione: Claude, in automatico.

## Dove si trova
| Cosa | Dove |
|---|---|
| Sito pubblico (link da condividere) | https://paologom.github.io/Gommberg-Terminal-Daily/ |
| Archivio su Claude (copia) | https://claude.ai/artifact/MuwDrCHDGXuADtKtL7cFcH |
| Kit della redazione | `redazione/` in questo repository |
| Registro della scommessa | `redazione/pronostici/` |
| Laboratorio della scommessa (metodo, backtest, pagella) | `redazione/scommessa/` (leggere `METODO.md`) |
| Edizioni PDF | `pdf/` |
| Indice delle edizioni | `edizioni.json` |

## Come funziona ogni mattina
1. Alle 8:58 parte l'attività programmata "Gommberg Terminal Daily" nel cloud di Anthropic (nessun PC acceso serve).
2. Clona questo repository e legge `redazione/ISTRUZIONI.md`.
3. Scarica i dati (FMP, Alpha Vantage), calcola il contesto dei movimenti (`contesto.py`), cerca notizie e agenda (agenti di ricerca), scrive il numero.
4. Controlli automatici (`controlli_tutti.sh`), controllo visivo, revisione rafforzata (fino a 25 verifiche, Sonnet).
5. Pubblica il PDF qui (sito) e nell'archivio su Claude, poi lo invia a Paolo in chat con 4 righe di sintesi (`messaggio.py`).

## Come chiedere modifiche (anche da cellulare)
Scrivere a Claude, dall'app, in questa conversazione o in una nuova: "Gommberg: ..." con la modifica. Claude aggiorna il kit in questo repository; la mattina dopo l'edizione la usa. Esempi: cambiare una sezione, aggiungere un indice, spostare l'orario, uscire anche il sabato.

## Stato
- 2026-10-12: edizione #001 pubblicata. Sito GitHub attivo. Automazione lun-ven (oggi alle 8:58, modello Sonnet).
- 2026-10-17: v7.0 (vedi Decisioni). Punto di ritorno prima dell'upgrade: ramo `salvastato-2026-10-16`.

## Note pratiche (ex paragrafo 12 delle istruzioni)
- Il permesso di push viene dalla sessione che crea l'attività programmata: se va ricreata, da una sessione col repository in scrittura.
- Il prompt fisso dell'attività cita ISTRUZIONI.md per paragrafi (§1-§13): la numerazione resta stabile.

## Prossimi passi (programma concordato con Paolo il 17/10, in quest'ordine; un cambiamento alla volta, misurato)
- [x] Collaudo end-to-end dal cloud superato il 12/10.
- [x] v7.0-7.2 (17/10): contesto.py, lettura e spiegazione, il perché in due fasi, prima pagina con le aperture delle altre testate, pagina del sito sulla scommessa.
- [ ] Notte del 17/10: prova generale end to end (simula lunedì 19/10, ramo `prova-2026-10-19`), anteprima sul sito solo con `?demo=1` (`edizioni_demo.json`, mai `edizioni.json`).
- [ ] 1. Lunedì 19/10: rivedere la #006, prima edizione v7.2, e il primo verdetto della scommessa (tempi, regole nuove, inceppi); correggere.
- [ ] 1b. Scommessa, metodo 1.1: sostituire il Treasury a 2 anni con la pendenza della curva (10 anni meno 2 anni). Motivo: nell'ultimo anno 2 e 10 anni sono andati nella stessa direzione il 77% delle settimane (correlazione 0,83), mentre la pendenza è quasi indipendente dal 10 anni (0,19). Collaudo sugli stessi 12 anni, registro della versione in METODO.md, aggiornare scommessa.html. Mai a ridosso di un lunedì.
- [ ] 2. Approfondimenti: un approfondimento = una tesi (il titolo dice cosa significa; la tabella a supporto).
- [ ] 3. Fonti primarie per i dati ufficiali (comunicato BLS, BEA, Eurostat...), l'agenzia solo d'appoggio.
- [ ] 4. Un ritorno dai lettori (una domanda sul sito o 3 lettori fidati sentiti il venerdì).
- [ ] 5. Landing page "più profonda, non più grande", per PC (oggi 4 lettori su 5) e telefono: prima pagina in testo, pagina per edizione con anteprima su WhatsApp, link fisso e feed RSS, fiducia in vista (metodo, errata, pagella). Decisione aperta di Paolo: statistiche dei lettori (GoatCounter, senza cookie) sì o no.
- [ ] 6. Alla prossima revisione: comprimere ISTRUZIONI.md (da 17 KB sotto i 15) senza togliere regole con un motivo scritto.

## La Scommessa (sotto-progetto)
- Obiettivo: range calibrati (la chiusura del venerdì cade nel range circa 2 settimane su 3) e una misura onesta delle scelte della redazione contro un modello senza opinioni.
- Metodo 1.0 dal 19/10/2026: volatilità delle ultime 20 sedute, distribuzione normale, range = base +- 1 sigma, uguale per tutti gli strumenti; direzione della redazione obbligatoria, tra 0,1 e 0,5 sigma.
- Backtest 2014-2026 (12/10/2026): nessun segnale di direzione batte la passeggiata casuale; il range in vigore è calibrato (68-72%); il VIX dava range troppo larghi sull'S&P 500 (82%) ed è stato tolto; il candidato "miscela + Student-t" è in osservazione (non supera ancora la soglia statistica). Audit indipendente superato dopo una correzione.
- Misure dal vivo in `scommessa/PAGELLA.md` (generata ogni lunedì). Prima revisione del metodo: aprile 2027 (26 settimane).
- Pag. 6 costruita da `scommessa/pagina6.py`: tabelle, grafico e pagella vengono dai file, nessun numero a mano. Collaudo del laboratorio dal cloud superato il 12/10 (rapporto in `collaudi/`).

## Idee per il futuro
- **Articoli ad hoc**: sezione separata del sito per approfondimenti fuori dal quotidiano (es. "Perché il 10 anni USA è al 5%"). Proposta: cartella `articoli/`, una pagina per articolo, elenco nel sito sotto le edizioni. Si scrivono su richiesta.
- Riepilogo settimanale del venerdì (una pagina).
- Iscrizione via email per i lettori.

## Decisioni prese
Ogni regola nuova o tolta si registra qui con data e motivo: è il registro che evita la stratificazione (una regola senza motivo scritto è candidata a uscire, una scelta di Paolo non si toglie senza chiederglielo).
- 2026-10-12: nome "Gommberg Terminal Daily"; solo trattino corto "-"; variazioni colorate per segno; struttura fissa di 6 pagine; scommessa del venerdì in chiusura.
- 2026-10-12: tolto il focus VWCE.
- 2026-10-12: pubblicazione su GitHub Pages perché la rete aziendale blocca claude.ai; kit e registro spostati da Google Drive al repository (lettura esatta dei file, niente trascrizioni).
- 2026-10-12: revisione mirata con modello più economico al posto della verifica completa (vedi ISTRUZIONI, paragrafo 10).
- 2026-10-12 sera: Scommessa rifondata come laboratorio (`redazione/scommessa/`): backtest su circa 12 anni, regola di adozione con soglia statistica fissata in anticipo, pagella con punteggi proper, controlli bloccanti su dati e date; festivi esclusi dalla numerazione; orari con zoneinfo; agenda con un evento per riga; fonti di opinione spostate tra le vietate; controllo automatico di numero e data in testata.
- 2026-10-12, dopo il collaudo: affidabilità prima di tutto. Fonti a livelli (`fonti.json`), una scheda con fonte, data e citazione per ogni fatto (`fatti.json`, archiviata in `redazione/fatti/`), controlli automatici su fonti, freschezza e dati (`controlli_fatti.py`, `controlli_dati.py`), revisione rafforzata (Sonnet, fino a 40 verifiche su tutte le schede principali), pubblicazione solo di ciò che supera i controlli; errata corrige nell'edizione successiva.
- 2026-10-12: tutto automatico, nessun messaggio di revisione o blocco a Paolo. Ciò che non supera i controlli si corregge o si toglie da solo (fino a 3 giri, notizie di riserva, minimo 6 top news); l'edizione salta solo se mancano repository, dati o PDF. Orario confermato: avvio alle 9:00, uscita verso le 9:45.
- 2026-10-16, v6.2 (dopo la prova E2E e tre revisioni): tre sole uscite ammesse; temi strutturati da elenco chiuso; ogni cifra al massimo 2 volte; movimenti oltre il 3% sempre citati; perché con causa o "causa non chiarita", quindi osservabile; probabilità con orizzonte, metodo e fonte; registro delle anomalie in fatti.json; frase di quadro trasversale; Stamattina solo prima delle 9:30; consegna prima dell'Archivio Claude; messaggio composto da messaggio.py; v5 in redazione/archivio/; "On track" uniforme.
- 2026-10-17, v7.0 (lettura più profonda, non più lunga): mappa delle regole con l'origine di ognuna, nessuna regola tolta; tolti 4 file mai usati (charts.py, charts2.py, data.py con il vecchio VWCE, schema/schema_flusso.py); `contesto.py` mette ogni movimento nel contesto dell'ultimo anno ("il calo più forte dal..."), dice chi muove la curva, scompone il 10 anni in reale e inflazione attesa e misura la reazione del 2 anni ai dati macro, senza chiamate API in più; §9 diventa "lettura e spiegazione" per il lettore medio; meccanismo M27; pagina del sito sulla scommessa con metodo e pagella. Motivo: Paolo vuole più comprensione del perché, non più contenuti.
- 2026-10-17, v7.1 (il perché si cerca sempre): due fasi per ogni fatto controintuitivo o movimento raro: prima la spiegazione delle testate di livello 1 (ricerche mirate per fatto e data, resoconti di fine seduta), poi la prova dei prezzi, che vale anche per la spiegazione trovata. Se nessuna fonte spiega, si pubblica la "lettura della redazione" con l'ipotesi che regge e i prezzi che la sostengono; "causa non chiarita" solo se ogni ipotesi registrata fallisce. "Le fonti non spiegano" vietato in tutto il PDF (controlli_contenuti.py). Motivo: nell'edizione #005 la domanda del giorno (Treasury giù dopo un PPI caldo) era rimasta senza risposta, e Paolo non vuole la "causa non chiarita" come via d'uscita.
- 2026-10-17, v7.2 (la prima pagina con il resto del mondo): la top story si sceglie confrontando le aperture di almeno 3 testate di riferimento con i movimenti rari di contesto.py; se non concorda con la maggioranza serve un motivo scritto (registro "prime_pagine" in fatti.json). Gli indici oltre il 3% e il movimento più raro del giorno vanno in prima pagina, non solo nel cruscotto. Le aperture pesano le notizie, non sono fonti dei fatti. Motivo: nell'edizione #005 il Nikkei a -4,9% era solo nel cruscotto.
- 2026-10-17: la rubrica si chiama "La scommessa della settimana" ovunque (PDF, sito, archivio Claude): la previsione si fa il lunedì e copre la settimana. Decisione di Paolo.
