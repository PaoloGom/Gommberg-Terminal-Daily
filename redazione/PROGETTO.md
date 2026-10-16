# Gommberg Terminal Daily - scheda di progetto

Documento di riferimento del progetto: cosa esiste, come funziona, cosa viene dopo. Si aggiorna a ogni modifica.

## Cosa è
Rassegna quotidiana dei mercati globali in PDF di 6 pagine, stile Bloomberg, in italiano. Esce dal lunedì al venerdì verso le 9:45-10:00 (ora di Roma). Editore: Paolo. Redazione: Claude, in automatico.

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
1. Alle 9:00 parte l'attività programmata "Gommberg Terminal Daily" nel cloud di Anthropic (nessun PC acceso serve).
2. Clona questo repository e legge `redazione/ISTRUZIONI.md`.
3. Scarica i dati (FMP, Alpha Vantage), cerca notizie e agenda (agenti di ricerca), scrive il numero.
4. Controlli automatici (`controlli.py`), controllo visivo, revisione mirata.
5. Pubblica il PDF qui (sito) e nell'archivio su Claude, poi lo invia a Paolo in chat con 3 righe di sintesi.

## Come chiedere modifiche (anche da cellulare)
Scrivere a Claude, dall'app, in questa conversazione o in una nuova: "Gommberg: ..." con la modifica. Claude aggiorna il kit in questo repository; la mattina dopo l'edizione la usa. Esempi: cambiare una sezione, aggiungere un indice, spostare l'orario, uscire anche il sabato.

## Stato
- 2026-10-12: edizione #001 pubblicata. Sito GitHub attivo. Automazione lun-ven alle 9:00.

## Note pratiche (ex paragrafo 12 delle istruzioni)
- Il permesso di push viene dalla sessione che crea l'attività programmata: se va ricreata, da una sessione col repository in scrittura.
- Il prompt fisso dell'attività cita ISTRUZIONI.md per paragrafi (§1-§13): la numerazione resta stabile.

## Prossimi passi
- [x] Collaudo end-to-end dal cloud superato il 12/10 (lezioni nel paragrafo 11 delle istruzioni; file di prova rimossi).
- [ ] Prima settimana: verificare ogni mattina esito, tempi e qualità; correggere il kit.
- [ ] Lunedì 19/10: primo verdetto della scommessa.

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
- 2026-10-12: nome "Gommberg Terminal Daily"; solo trattino corto "-"; variazioni colorate per segno; struttura fissa di 6 pagine; scommessa del venerdì in chiusura.
- 2026-10-12: tolto il focus VWCE.
- 2026-10-12: pubblicazione su GitHub Pages perché la rete aziendale blocca claude.ai; kit e registro spostati da Google Drive al repository (lettura esatta dei file, niente trascrizioni).
- 2026-10-12: revisione mirata con modello più economico al posto della verifica completa (vedi ISTRUZIONI, paragrafo 10).
- 2026-10-12 sera: Scommessa rifondata come laboratorio (`redazione/scommessa/`): backtest su circa 12 anni, regola di adozione con soglia statistica fissata in anticipo, pagella con punteggi proper, controlli bloccanti su dati e date; festivi esclusi dalla numerazione; orari con zoneinfo; agenda con un evento per riga; fonti di opinione spostate tra le vietate; controllo automatico di numero e data in testata.
- 2026-10-12, dopo il collaudo: affidabilità prima di tutto. Fonti a livelli (`fonti.json`), una scheda con fonte, data e citazione per ogni fatto (`fatti.json`, archiviata in `redazione/fatti/`), controlli automatici su fonti, freschezza e dati (`controlli_fatti.py`, `controlli_dati.py`), revisione rafforzata (Sonnet, fino a 40 verifiche su tutte le schede principali), pubblicazione solo di ciò che supera i controlli; errata corrige nell'edizione successiva.
- 2026-10-12: tutto automatico, nessun messaggio di revisione o blocco a Paolo. Ciò che non supera i controlli si corregge o si toglie da solo (fino a 3 giri, notizie di riserva, minimo 6 top news); l'edizione salta solo se mancano repository, dati o PDF. Orario confermato: avvio alle 9:00, uscita verso le 9:45.
- 2026-10-16, v6.2 (dopo la prova E2E e tre revisioni): tre sole uscite ammesse; temi strutturati da elenco chiuso; ogni cifra al massimo 2 volte; movimenti oltre il 3% sempre citati; perché con causa o "causa non chiarita", quindi osservabile; probabilità con orizzonte, metodo e fonte; registro delle anomalie in fatti.json; frase di quadro trasversale; Stamattina solo prima delle 9:30; consegna prima dell'Archivio Claude; messaggio composto da messaggio.py; v5 in redazione/archivio/; "On track" uniforme.
