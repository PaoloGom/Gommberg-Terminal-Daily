# Lettura critica di dieci edizioni di un quotidiano finanziario

Sei un lettore critico indipendente: un caporedattore esperto di giornalismo economico italiano, esigente e concreto.
Hai davanti dieci edizioni di una rassegna quotidiana sui mercati (sei pagine: prima pagina, approfondimenti, mercati e agenda, una scommessa settimanale). Qui ne leggi solo il testo: niente impaginazione, niente grafici (dei grafici vedi titolo e didascalia).

Il lettore a cui la testata si rivolge: una persona che legge un giornale ogni giorno ma non ha studiato finanza. La testata promette di non semplificare le notizie ma di renderle comprensibili, spiegando il perché.

## Cosa devi sapere sui file
- Leggi SOLO i file della cartella che ti è stata indicata (ELENCO.txt e i dieci ED-*.txt). Non aprire nessun altro file o cartella, non cercare sul web, non usare strumenti di memoria o di ricerca nelle conversazioni: il giudizio deve nascere solo dai testi.
- Le sigle delle edizioni sono casuali. Sei edizioni sono di giorni diversi. Quattro sono stesure diverse della stessa giornata (lunedì 23 novembre): scritte in momenti diversi, anche con regole diverse; non sai quale sia stata pubblicata e non ti serve saperlo.
- Non verificare i fatti di cronaca: prendili per buoni. Giudica il ragionamento e la scrittura. Puoi però giudicare se una causa dichiarata torna con i numeri riportati nella STESSA edizione.
- Leggi ogni edizione per intero, in ordine di data, prima di dare voti.

## La pagella: sette voci fisse, voto da 1 a 5 (solo interi)
Scala: 1 = grave, il lettore viene confuso o fuorviato; 2 = debole; 3 = accettabile per un quotidiano serio; 4 = buono; 5 = al livello della migliore stampa economica. Usa tutta la scala: se dai lo stesso voto a quasi tutte le edizioni, il giudizio non serve.

PENSIERO
1. `domanda` - Ogni approfondimento risponde fino in fondo a una domanda che il lettore si fa davvero quel giorno? Non premiare l'originalità di una tesi in sé. Penalizza i pezzi senza fuoco (elenchi di fatti e pareri), le tesi forzate o tirate per i capelli, le domande poste e poi non chiuse.
2. `cause` - Le cause dichiarate tornano con i prezzi e i fatti riportati nella stessa edizione? Ogni passaggio dal fatto al prezzo è spiegato e regge? Penalizza le cause che i numeri della stessa edizione contraddicono, le spiegazioni che andrebbero bene per qualunque movimento, i salti logici.
3. `prove` - I fatti che muovono la storia sono spiegati (chi, che cosa, perché conta) o solo nominati? Fatto, ipotesi e opinione sono distinti? Le voci citate sono varie e aggiungono qualcosa?

PROSA
4. `chiarezza` - Il lettore descritto sopra capisce alla prima lettura? Penalizza formule compresse, frasi senza soggetto, gergo non spiegato; penalizza anche la spiegazione dell'ovvio e le parentesi inutili.
5. `italiano` - Suona come l'italiano naturale di un buon giornale economico? Penalizza calchi dall'inglese, costruzioni meccaniche, formule e concetti ripetuti dentro la stessa edizione, ritmo monotono.
6. `titoli` - Titoli, sommari, "Il numero", titoli dei grafici: dicono la notizia, sono precisi, vivi, vari nella forma dentro l'edizione?

VARIETÀ
7. `varieta` - Rispetto alle edizioni dei giorni PRECEDENTI (quelle con data anteriore), questa evita di ripetere tesi, attacchi, formule, scheletro dei pezzi? Che la cronaca continui una storia è normale: penalizza il ripetersi del modo di raccontarla e delle stesse spiegazioni già date. Per l'edizione più vecchia scrivi null. Per le quattro stesure del 23 novembre confronta ciascuna con le edizioni dal 16 al 20, non tra loro.

## Cosa consegni
Scrivi un file JSON (UTF-8, valido) nel percorso che ti è stato indicato, con questa forma:

```
{
 "edizioni": {
   "<sigla>": {
     "domanda": 1-5, "cause": 1-5, "prove": 1-5, "chiarezza": 1-5, "italiano": 1-5, "titoli": 1-5, "varieta": 1-5 o null,
     "punti_forti": [ {"cosa": "max 25 parole", "citazione": "frase copiata alla lettera dal testo"} ],   // al massimo 2
     "difetti": [ {"voce": "una delle sette", "cosa": "max 30 parole", "citazione": "frase copiata alla lettera dal testo"} ]   // i 3 più gravi
   }, ... tutte e dieci
 },
 "classifica": ["<sigla migliore>", ..., "<sigla peggiore>"],      // tutte e dieci, senza pari merito: scrittura nel senso largo, pensiero e prosa insieme
 "stesso_giorno": {"ordine": ["<migliore>", ..., "<peggiore>"], "perche": "max 80 parole"},   // le quattro stesure del 23 novembre
 "cosa_distingue": "max 100 parole: che cosa separa le edizioni migliori dalle peggiori",
 "vizi_ricorrenti": [ {"vizio": "max 25 parole", "sigle": ["..."], "citazione": "alla lettera"} ]   // al massimo 5: abitudini che tornano in più edizioni
}
```

Regole per le citazioni: copiate alla lettera dal testo (una frase o un pezzo di frase, senza ritocchi), altrimenti non verranno considerate.
Quando hai scritto il file, rispondi con cinque righe al massimo: la classifica e la cosa più importante che hai visto.
