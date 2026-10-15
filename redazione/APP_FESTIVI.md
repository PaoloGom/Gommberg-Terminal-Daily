# Appendice - Festività e chiusure di borsa

## 1. Niente edizione
Se la data è in `FESTIVI` di `gommberg_engine.py` (borse USA ed europee chiuse insieme: Natale, Capodanno, Venerdì Santo), `prepara.sh` dice NIENTE EDIZIONE: manda a Paolo una riga ("Oggi borse chiuse: niente Gommberg, ci rivediamo al prossimo giorno di borsa") e fermati. Questi giorni non contano nella numerazione.

## 2. Chiusure parziali (l'edizione esce)
- Un mercato chiuso si scrive "chiuso" (o "n.d." con la data dell'ultima chiusura), mai "0,0%".
- La variazione 1g usa l'ultima chiusura disponibile; dichiaralo nella nota del cruscotto ("Wall Street chiusa il 26/11: variazioni sul 25/11").
- `controlli_dati.py` dà un avviso a 2 giorni lavorativi e un errore oltre: per un festivo verificato dichiaralo nel PDF e, se serve, nella serie metti `"tipo": "chiusura"` con la data giusta.
- Mercato dei Treasury chiuso (es. Veterans Day, Columbus Day) con borse aperte: rendimenti fermi, scrivilo in cross-asset.
- Calendario e agenda: il giorno dopo una chiusura il calendario copre tutte le sedute dall'ultima edizione.
- Scommessa: venerdì chiuso per un mercato -> il lunedì `valuta.py --verdetto --festivo <chiavi>` (vedi `APP_LUNEDI.md`). Lunedì festivo per la redazione -> il primo giorno di uscita della settimana fa il lavoro del lunedì (`prepara.sh` lo indica).
- Chiusure anticipate (vigilie, giorno dopo Thanksgiving): la chiusura è valida ma i volumi sono bassi; nessuna lettura forte sui movimenti.

## 3. Elenco indicativo (verifica sempre sul calendario ufficiale di NYSE, Borsa Italiana, Eurex/Xetra, LSE, Tokyo)
`prepara.sh` contiene le chiusure parziali note fino a settembre 2027 (Thanksgiving, MLK, Presidents' Day, Lunedì dell'Angelo, Memorial Day, Juneteenth, Independence Day, Labor Day, vigilie). Le borse asiatiche hanno festività proprie (Golden Week in Giappone e Cina, Capodanno lunare): in quei giorni la riga Asia del cruscotto indica "chiuso".

## 4. Ogni dicembre
Aggiungi a `FESTIVI` in `gommberg_engine.py` le date dell'anno dopo in cui USA ed Europa sono chiuse insieme (Natale, Capodanno, Venerdì Santo; Santo Stefano solo se anche NYSE è chiusa), aggiorna le chiusure parziali in `prepara.sh` e segnalalo nel messaggio finale. Il numero di edizione si ricalcola da solo (`giorni.py` legge `FESTIVI` dal motore).
