# Prova generale (testo da passare all'attività vera, lanciata a mano fuori orario)

Si lancia l'attività del mattino aggiungendo questo testo come messaggio in coda, con `<ramo>` e `<data>` al loro posto. La data serve solo quando la prova non vale per oggi (per esempio nel fine settimana, per provare l'edizione del lunedì).

QUESTA NON È L'EDIZIONE VERA: è una prova generale chiesta da Paolo. Niente di ciò che fai va sul sito e il ramo principale non si tocca.

1. Al posto del passo 2 del tuo incarico: dalla cartella di partenza (il clone del repository) esegui
   `git fetch --depth=60 origin <ramo> main && git checkout -B <ramo> origin/<ramo> && bash redazione/prova.sh avvio <data>`.
   Se stampa PROVA NON POSSIBILE, chiudi con "Prova non riuscita: <motivo>".
2. Leggi `redazione/ISTRUZIONI.md` di questo ramo (§1-§7; il tuo incarico cita paragrafi vecchi, vale questo file) e seguilo come ogni mattina, da `prepara.sh`: stampa PROVA GENERALE e la data dell'edizione. Le chiusure sono le ultime ufficiali; la finestra di "Stamattina" resta 06:00-09:29: se un livello del mattino non è verificabile a quest'ora, usa "Cosa guardare all'apertura".
3. Pubblicazione: `GTD_PROVA=1 bash /home/claude/gtd/redazione/pubblica.sh ...` (stampa i comandi, non li esegue). Mai `git push origin main`. Niente Archivio Claude.
4. Alla fine: `bash /home/claude/gtd/redazione/prova.sh chiudi "<pdf>"`, poi SendUserFile del PDF con didascalia "PROVA - <data lunga> (non pubblicata)" e un messaggio di 6 righe: titolo di pag. 1; minuti impiegati; controlli rossi al primo giro e giri serviti; cosa nelle istruzioni era ambiguo o ti ha fatto perdere tempo; quante riscritture del desk accettate e respinte; la riga stampata da `prova.sh chiudi`.
