# Appendice - Festività e chiusure di borsa

## 1. Niente edizione
Se la data è in `FESTIVI` di `gommberg_engine.py` (borse USA ed europee chiuse insieme: Natale, Capodanno, Venerdì Santo), `prepara.sh` dice NIENTE EDIZIONE: uscita (b): manda a Paolo solo la riga "Oggi borse chiuse: niente Gommberg, ci rivediamo al prossimo giorno di borsa". Questi giorni non contano nella numerazione.

## 2. Chiusure parziali (l'edizione esce)
- **In `dati.json`** la serie di un mercato chiuso porta la sua ultima chiusura vera, con la data vera, e la chiusura prima: `"tipo": "chiusura"`. Mai una riga con la data del giorno di chiusura, mai una variazione a zero. Lo stesso per i rendimenti quando è chiuso solo il mercato dei Treasury e le borse sono aperte.
- **Le tabelle di pag. 5 le scrive il codice anche in questi giorni** (`numeri.py`). Per un mercato chiuso la variazione di un giorno è quella della sua ultima seduta; la data di ogni livello e la chiusura usata per ogni riferimento escono da sole, nell'intestazione, nel titolo del gruppo o nella nota. Nel file dell'edizione non si scrive nessuna cella e nessuna nota: mai "chiuso", mai "n.d.".
- **Che un mercato era chiuso lo dice la redazione, a parole**: in `NOTA_DATI` (la riga della testata: a che data sono le chiusure, e a quale è fermo il mercato rimasto indietro) e dove il testo parla di quel mercato (la lettura di pag. 5, Stamattina, il pezzo che lo riguarda). L'ultima seduta di un mercato chiuso ieri non si racconta come se fosse di ieri.
- `controlli_dati.py` conta i giorni di uscita passati dall'ultimo dato (un giorno senza edizione non conta). A 2 dà un avviso: è il caso normale del giorno dopo una chiusura. Oltre si ferma, perché di solito è un dato vecchio. Chiusure così lunghe le hanno solo le borse asiatiche: se l'indice è davvero fermo da più giorni di uscita (calendario ufficiale), la sua serie si scrive `{"mercato": "..", "nd": "<motivo>", "ultimi": []}`, la riga esce dalla tabella e lo spazio si riempie come dice `APP_ERRORI.md` §2. Se un indice asiatico ha già chiuso stamattina e il suo ultimo dato è di ieri, il controllo lo segnala: o manca la chiusura di oggi, o oggi quella borsa era chiusa.
- Calendario e agenda: il giorno dopo una chiusura il calendario copre tutte le sedute dall'ultima edizione.
- Scommessa: venerdì chiuso per un mercato -> il lunedì `valuta.py --verdetto --festivo <chiavi>` (vedi `APP_LUNEDI.md`). Lunedì festivo per la redazione -> il primo giorno di uscita della settimana fa il lavoro del lunedì (`prepara.sh` lo indica).
- Chiusure anticipate (vigilie, giorno dopo Thanksgiving): la chiusura è valida ma i volumi sono bassi; nessuna lettura forte sui movimenti.

## 3. Elenco indicativo (verifica sempre sul calendario ufficiale di NYSE, Borsa Italiana, Eurex/Xetra, LSE, Tokyo)
`prepara.sh` contiene le chiusure parziali note fino a settembre 2027 (Thanksgiving, MLK, Presidents' Day, Lunedì dell'Angelo, Memorial Day, Juneteenth, Independence Day, Labor Day, vigilie). Le borse asiatiche hanno festività proprie (Golden Week in Giappone e Cina, Capodanno lunare) che `prepara.sh` non elenca: quando un indice asiatico è fermo lo segnala `controlli_dati.py` e vale il §2.

## 4. Ogni dicembre
Aggiungi a `FESTIVI` in `gommberg_engine.py` le date dell'anno dopo in cui USA ed Europa sono chiuse insieme (Natale, Capodanno, Venerdì Santo; Santo Stefano solo se anche NYSE è chiusa), aggiorna le chiusure parziali in `prepara.sh` e segnalalo nel messaggio finale. Il numero di edizione si ricalcola da solo (`giorni.py` legge `FESTIVI` dal motore).
