# Prove con l'attività vera (testo da aggiungere in coda quando la si lancia a mano)

## A. Prova generale su un ramo, senza pubblicare

Si lancia l'attività del mattino aggiungendo questo testo come messaggio in coda, con `<ramo>` e `<data>` al loro posto. La data serve solo quando la prova non vale per oggi (per esempio nel fine settimana, per provare l'edizione del lunedì).

QUESTA NON È L'EDIZIONE VERA: è una prova generale chiesta da Paolo. Niente di ciò che fai va sul sito e il ramo principale non si tocca.

1. Al posto del passo 2 del tuo incarico: dalla cartella di partenza (il clone del repository) esegui
   `git fetch --depth=60 origin <ramo> main && git checkout -B <ramo> origin/<ramo> && bash redazione/prova.sh avvio <data>`.
   Se stampa PROVA NON POSSIBILE, chiudi con "Prova non riuscita: <motivo>".
2. Leggi `redazione/ISTRUZIONI.md` di questo ramo (§1-§7; il tuo incarico cita paragrafi vecchi, vale questo file) e seguilo come ogni mattina, da `prepara.sh`: stampa PROVA GENERALE e la data dell'edizione. Le chiusure sono le ultime ufficiali; la finestra di "Stamattina" resta 06:00-09:29: se un livello del mattino non è verificabile a quest'ora, usa "Cosa guardare all'apertura".
3. Pubblicazione: `GTD_PROVA=1 bash /home/claude/gtd/redazione/pubblica.sh ...` (stampa i comandi, non li esegue). Mai `git push origin main`. Niente Archivio Claude.
4. Alla fine: `bash /home/claude/gtd/redazione/prova.sh chiudi "<pdf>"`, poi SendUserFile del PDF con didascalia "PROVA - <data lunga> (non pubblicata)" e un messaggio di 6 righe: titolo di pag. 1; minuti impiegati; controlli rossi al primo giro e giri serviti; cosa nelle istruzioni era ambiguo o ti ha fatto perdere tempo; quante riscritture del desk accettate e respinte; la riga stampata da `prova.sh chiudi`.

## B. Edizione di test pubblicata davvero dal ramo principale
Serve a provare anche la pubblicazione (commit, push, sito). Si fa solo quando Paolo lo chiede e i lettori non ci sono (fine settimana); poi l'edizione si toglie con `git revert` del suo commit, prima del giorno di borsa successivo. `<data>` è il giorno di borsa da simulare.

QUESTA È UN'EDIZIONE DI TEST chiesta da Paolo: si pubblica davvero sul sito e verrà tolta entro stasera. Segui il tuo incarico così com'è, con due sole differenze.
1. Dopo il passo 2 (repository aggiornato e collegamento /home/claude/gtd) e prima di `prepara.sh`: `echo <data> > /home/claude/gtd/redazione/PROVA_DATA`. `prepara.sh` stamperà PROVA GENERALE con quella data: è l'edizione da scrivere. I livelli del mattino di quel giorno non esistono ancora: usa "Cosa guardare all'apertura".
2. Alla pubblicazione: `GTD_PUBBLICA_PROVA=1 bash /home/claude/gtd/redazione/pubblica.sh ...` (pubblica davvero: verifica PUSH_OK). Tutto il resto, consegna compresa, come ogni mattina.
