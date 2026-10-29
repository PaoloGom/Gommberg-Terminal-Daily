# Gommberg Terminal Daily - protocollo di manutenzione del kit

Questo file vale per ogni sessione che **cambia il kit** (regole, controlli, modello, motore, sito). Obiettivo: migliorare il giornale senza stratificarlo, a qualità uguale o migliore.

## Principi
1. **Una regola, una casa.** Ogni regola sta in un solo punto delle istruzioni (`ISTRUZIONI.md` o un'appendice) e, se ha un controllo, in un solo script (es. la regola delle fonti nel testo vive in `citazioni.py`). Regola, controllo, esempio nel modello (`edizione_modello_v6.py`) e messaggio d'errore dicono la stessa cosa: se ne cambi uno, cambi tutti e quattro. Prima di toccare una regola: `grep` della parola chiave in `redazione/`.
2. **Gli esempi pesano più delle regole.** Il modello è la cosa che la redazione copia: un esempio contrario alla regola vince sempre sulla regola.
3. **Sostituire, non aggiungere.** Ogni cambiamento risolve la causa con una regola generale e toglie ciò che diventa superfluo. Niente casi singoli, niente pezze. Tetti: `ISTRUZIONI.md` 16 KB, appendici 30 KB (li controlla il banco).
4. **I controlli bloccanti valgono quanto le regole.** Un controllo che chiede più della regola produce un giornale diverso da quello scritto nelle istruzioni (caso del 26-29/10: regola sulle fonti cambiata, controlli no, parentesi raddoppiate).
5. **Un cambiamento alla volta, misurato.** Ogni voce della coda ha una misura di successo e si verifica sull'edizione del giorno dopo.
6. **La redazione del mattino non cambia il kit.** Pubblica, e annota gli inceppi in `fatti.json` (sezione "inceppo"): sono l'ingresso della manutenzione.

## Procedura di ogni modifica
1. Leggi in `redazione/PROGETTO.md` la **Coda** e le **Decisioni** (le scelte di Paolo non si ribaltano senza di lui). Leggi gli inceppi recenti: `grep -l inceppo redazione/fatti/*.json`.
2. **Diagnosi:** la causa sta nella regola, nel controllo, nel modello o nel motore? Correggi lì, nei quattro punti coerenti.
3. **Banco di prova:** `bash redazione/banco/banco.sh` (tetti e confronto dei controlli sulle edizioni pubblicate). Ogni controllo che cambia esito va spiegato: stretta voluta o falso positivo da correggere.
4. Se cambia il contenuto del giornale: una demo con `pubblica.sh --prova`, giudicata da un agente che non ha scritto la modifica, contro l'ultima edizione vera.
5. Registra in `PROGETTO.md` (Decisioni: data, cosa, perché, misura attesa) e aggiorna la Coda.
6. **Quando pubblicare su main:** mai tra le 8:30 e le 10:45 dei giorni di uscita (la redazione lavora sul repository), mai il venerdì (verdetto della scommessa), mai due voci della coda nello stesso giorno.
7. Il giorno dopo: `banco.sh` e lettura dell'edizione contro la misura attesa. Se peggiora, si torna indietro con un `git revert`.

## Lingua e stile
Testi in italiano, trattino corto "-" (mai lunghi), file d'archivio con la data AAAA-MM-GG all'inizio.
