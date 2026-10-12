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

## Prossimi passi
- [x] Collaudo end-to-end dal cloud superato il 12/10 (lezioni nel paragrafo 11 delle istruzioni; file di prova rimossi).
- [ ] Prima settimana: verificare ogni mattina esito, tempi e qualità; correggere il kit.
- [ ] Lunedì 19/10: primo verdetto della scommessa.

## Idee per il futuro
- **Articoli ad hoc**: sezione separata del sito per approfondimenti fuori dal quotidiano (es. "Perché il 10 anni USA è al 5%"). Proposta: cartella `articoli/`, una pagina per articolo, elenco nel sito sotto le edizioni. Si scrivono su richiesta.
- Riepilogo settimanale del venerdì (una pagina).
- Iscrizione via email per i lettori.

## Decisioni prese
- 2026-10-12: nome "Gommberg Terminal Daily"; solo trattino corto "-"; variazioni colorate per segno; struttura fissa di 6 pagine; scommessa del venerdì in chiusura.
- 2026-10-12: tolto il focus VWCE.
- 2026-10-12: pubblicazione su GitHub Pages perché la rete aziendale blocca claude.ai; kit e registro spostati da Google Drive al repository (lettura esatta dei file, niente trascrizioni).
- 2026-10-12: revisione mirata con modello più economico al posto della verifica completa (vedi ISTRUZIONI, paragrafo 10).
