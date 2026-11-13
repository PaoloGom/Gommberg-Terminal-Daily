# Prova generale della v8 (testo da aggiungere all'attività vera, lanciata a mano dopo l'edizione del giorno)

QUESTA NON È L'EDIZIONE DI OGGI: è una prova generale della v8, chiesta da Paolo. L'edizione di oggi è già uscita e non si tocca. Niente di ciò che fai va sul sito.

1. Al posto del passo 2 del tuo incarico: dalla cartella di partenza (il clone del repository) esegui
   `git fetch --depth=60 origin v8 main && git checkout -B v8 origin/v8 && bash redazione/prova_v8.sh avvio`.
   Se stampa PROVA NON POSSIBILE, chiudi con "Prova v8 non riuscita: <motivo>".
2. Leggi `redazione/ISTRUZIONI.md` di questo ramo (§1-§7) e seguilo come ogni mattina, da `prepara.sh`. Le chiusure sono quelle di ieri, la finestra di "Stamattina" resta 06:00-09:29: se un livello del mattino non è verificabile a quest'ora, usa "Cosa guardare all'apertura".
3. Pubblicazione: `GTD_PROVA=1 bash /home/claude/gtd/redazione/pubblica.sh ...` (stampa i comandi, non li esegue). Mai `git push origin main`. Niente Archivio Claude.
4. Alla fine: `bash /home/claude/gtd/redazione/prova_v8.sh chiudi "<pdf>"`, poi SendUserFile del PDF con didascalia "PROVA v8 - <data lunga> (non pubblicata)" e un messaggio di 5 righe: titolo di pag. 1; minuti impiegati; controlli rossi al primo giro e giri serviti; cosa nelle istruzioni nuove era ambiguo o ti ha fatto perdere tempo; quante riscritture del desk accettate e respinte; la riga stampata da `prova_v8.sh chiudi`.
