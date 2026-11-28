# G-46, punto 6 - I perché della scommessa del lunedì

Decisione di Paolo del 28/11: "ok solo se migliora l'esperienza del lettore ed ha senso". Qui: la misura di partenza, la regola, il controllo, e un prima e dopo su due scommesse uscite.

## 1. Misura di partenza

Fonte: i registri `redazione/pronostici/<lunedì>-settimana.json` (campo `motivo_redazione`, è la colonna "Il perché" di pag. 6 del lunedì), dal 19/10 al 23/11. Il 12/10 non ha perché. Lo scenario ("La nostra tesi", con "Ci smentirebbe") esiste dal 16/11: il contrario della tesi si misura solo da lì.

Categorie: **motivo** = causa -> effetto su quel mercato in quella direzione; **attesa** = il mercato "aspetta" qualcosa; **già fatto** = descrive ciò che è già successo (rimbalzo, tendenza, il mattino senza la sua causa); **ripete** = la stessa causa già data a un'altra riga; **contro la tesi** = poggia sul ramo che smentirebbe lo scenario.

| Lunedì | Mercato | Perché uscito | Giudizio |
|---|---|---|---|
| 19/10 | ACWI | Rimbalzo tecnico dopo la peggior settimana da giugno | già fatto |
| 19/10 | S&P 500 | Future in rialzo e trimestrali in arrivo | già fatto (e un evento senza verso) |
| 19/10 | Euro Stoxx 50 | Venerdì incerto e future in calo: prevale la prudenza | già fatto |
| 19/10 | Treasury 10 anni | Rendimenti in calo anche lunedì (Reuters) | già fatto |
| 19/10 | Brent | Sanzioni russe sospese (AP): il greggio perde premio | motivo |
| 19/10 | EUR/USD | Euro poco mosso, dollaro sostenuto dal rifugio | motivo |
| 19/10 | Oro | Rendimenti in calo e stress sul credito sostengono l'oro | motivo |
| 26/10 | ACWI | Future in rialzo e conti di Microsoft e Alphabet mercoledì | già fatto (e un evento senza verso) |
| 26/10 | S&P 500 | Future in rialzo, Fed attesa in pausa e grandi tecnologici in arrivo | motivo |
| 26/10 | Euro Stoxx 50 | Future in rialzo lunedì e Francia confermata da Moody's | motivo |
| 26/10 | Treasury 10 anni | Rendimento in calo lunedì mattina e Fed attesa in pausa | ripete (Fed in pausa) |
| 26/10 | Brent | Trump parla di accordo o fine del conflitto con l'Iran: il greggio perde premio | motivo |
| 26/10 | EUR/USD | Fed in pausa e dollaro senza spinta lunedì mattina | ripete (Fed in pausa, terza volta) |
| 26/10 | Nikkei 225 | Terzo calo di fila lunedì: tendenza debole fino ai conti di SK Hynix | già fatto |
| 2/11 | ACWI | Seul già in rimbalzo dopo i chip | già fatto |
| 2/11 | S&P 500 | Rimbalzo tecnico dopo il calo di venerdì | già fatto |
| 2/11 | Euro Stoxx 50 | ASML e Infineon in calo dopo Intel | motivo |
| 2/11 | Treasury 10 anni | Rifugio nei Treasury se i chip calano | motivo |
| 2/11 | Brent | Piano del Qatar su Hormuz: premio di rischio giù | motivo |
| 2/11 | EUR/USD | Dollaro sostenuto da Fed e rifugio | motivo |
| 2/11 | Oro | Dopo la vendita forzata, rimbalzo sopra 3.900 | già fatto |
| 9/11 | S&P 500 | Rimbalzo dei chip dopo il crollo, ma il CPI di martedì può cambiare tutto | già fatto (e un'attesa) |
| 9/11 | Euro Stoxx 50 | Petrolio più basso e banche italiane in ripresa aiutano l'Europa | motivo |
| 9/11 | Treasury 10 anni | Il petrolio che scende frena le attese di inflazione prima del CPI | motivo |
| 9/11 | EUR/USD | Un rialzo Fed a dicembre sempre più probabile sostiene il dollaro | motivo |
| 9/11 | Brent | Colloqui USA-Iran e offerta in eccesso stimata da JPMorgan | motivo |
| 9/11 | Oro | Un rialzo Fed a dicembre sempre più probabile pesa sull'oro | ripete (stessa frase dell'EUR/USD) |
| 16/11 | S&P 500 | I future perdono terreno dopo il crollo dei chip asiatici | motivo |
| 16/11 | Euro Stoxx 50 | L'Europa aspetta i conti di Nvidia dopo una settimana forte | attesa |
| 16/11 | Treasury 10 anni | La Fed parla oggi e mercoledì: un tono duro tiene alti i rendimenti | contro la tesi (lo scenario vuole verbali senza toni più duri) |
| 16/11 | EUR/USD | Con rialzi Fed attesi il dollaro resta il rifugio contro l'euro | contro la tesi (stesso ramo duro della Fed, ripetuto) |
| 16/11 | Brent | Gli attacchi nel Golfo e nel Mar Rosso tengono il rischio sulle forniture | motivo (ma gli attacchi non stanno nelle schede del giorno) |
| 16/11 | Oro | Il dollaro forte e i tassi alti pesano sull'oro | motivo |
| 23/11 | S&P 500 | I future salgono di oltre il 2% dopo il crollo di venerdì | già fatto (il mattino senza la sua causa) |
| 23/11 | Euro Stoxx 50 | Dopo il minimo da maggio aspetta di capire se Wall Street tiene | attesa |
| 23/11 | Treasury 10 anni | Se la paura cala i Treasury smettono di fare da rifugio e il rendimento risale | motivo |
| 23/11 | EUR/USD | L'euro recupera un po' dopo una settimana di dollaro forte | già fatto |
| 23/11 | Brent | Con meno fiducia nella crescita e più offerta il greggio ha poca spinta | contro la tesi ("meno fiducia nella crescita" contro un rimbalzo delle borse) |
| 23/11 | Oro | Rimbalza dopo la caduta di venerdì, la peggiore da mesi | già fatto |

**Totale: 18 motivi veri su 39** (19/10: 3 su 7; 26/10: 3 su 7; 2/11: 4 su 7; 9/11: 4 su 6; 16/11: 3 su 6; 23/11: 1 su 6). Gli altri 21: già fatto 13, ripete 3, contro la tesi 3, attesa 2. La settimana vera del 23/11 è la peggiore.

## 2. La regola (APP_LUNEDI §3, per sostituzione)

Prima (403 caratteri):
> Il motivo è una riga per il lettore, senza segni +/- davanti ai numeri: per `mattino` dice che cosa ha mosso il mercato; per `fondo` dice che cosa aspetta quel mercato in settimana (la tendenza di lungo periodo è la regola, non il motivo da ripetere); per `scenario` e `catalizzatore` dice il legame tra lo scenario, o l'evento, e quel mercato. Mai lo stesso motivo su due mercati: lo script lo rifiuta.

Dopo (454 caratteri):
> Il motivo è una riga per il lettore, senza segni +/- davanti ai numeri: il meccanismo che questa settimana spinge quel mercato nella direzione scelta (per `mattino` che cosa l'ha mosso, per gli altri tipi in che verso lo spinge lo scenario o l'evento). Non è un motivo: un'attesa, un evento senza il verso in cui spinge, ciò che il mercato ha già fatto (un rimbalzo, una tendenza), una causa già data a un'altra riga, il ramo che smentirebbe lo scenario.

La frase si allunga di 51 caratteri, ma la sezione si accorcia di 140: escono i due perché d'esempio nel modello di `redazione.json` (erano esempi concreti, con nomi veri: ora "..."), ed esce dalla "Una settimana sola" la frase sulla causa ripetuta, che ora sta nella regola. L'incarico del revisore (§4) chiede di segnalare "una riga che non è un motivo (§3)" al posto di "una causa già scritta". Il messaggio di `pronostico.py` non dice più "che cosa aspetta". L'istruzione `fondo` che chiedeva proprio l'attesa era la causa delle due righe "aspetta".

## 3. Il controllo: un avviso per il revisore (controlli_testo.py, passo Scrittura del lunedì)

Dopo il collaudo indipendente (8 falsi allarmi su 35 perché buoni del suo banco quando era un errore), il controllo è un
AVVISO per il revisore, che già rilegge i perché (APP_LUNEDI §4): distinguere un meccanismo da un'attesa è un giudizio di
lettura. Legge i sei perché dal registro della settimana e segnala, con la domanda da farsi:
- un perché senza un verbo di causa coniugato con il suo oggetto (la forma causa -> effetto, o un "se ...") che somiglia a
  un'attesa ("aspetta", "guarda al", "in vista di", "occhi puntati", "dipende da") o a ciò che il mercato ha già fatto
  ("rimbalza", "recupera", "riparte", "prosegue", "consolida", "torna a", "di fila", "consecutive", "sulla scia", "fiato");
- la stessa causa in due righe (quattro parole uguali di fila);
- più di due righe su sei che dichiarano la direzione debole ("la scommessa sembra fatta a caso"). La dichiarazione esce
  dal giudizio, il resto della frase no.
Le correzioni del revisore si fanno con `pronostico.py --solo-parole`, che riscrive nel registro solo scenario e perché:
direzioni, livelli e forchette non si toccano per costruzione (prima il rimando era a `--forza`, che riscrive tutto).

Misure (`banco_perche.py`): sui 39 perché usciti 12 avvisi, tutti su non motivi, 0 sui 18 motivi veri; banco con le frasi
del collaudatore, 15 perché buoni e 16 vuoti: 0 avvisi sui buoni, 0 mancati; sei righe "Direzione debole: poggia solo sul
mattino": un avviso. Restano senza avviso, e alla sola rilettura: il mattino descritto senza la causa, la causa ripetuta
con altre parole, il perché contro la tesi.

## 4. Prima e dopo su due scommesse uscite

Riscritti a mano solo con i fatti delle schede di quel giorno (`redazione/fatti/<data>.json`, id tra parentesi). Le direzioni restano quelle pubblicate.

### Lunedì 23/11 - tesi: rimbalzo fragile delle borse, prova il PCE; ci smentirebbe un PCE caldo

| Mercato | Prima | Dopo |
|---|---|---|
| S&P 500 su | I future salgono di oltre il 2% dopo il crollo di venerdì | **Nessun motivo nelle schede.** I future rimbalzano (T01) ma nessuna scheda dice perché. La regola costringe a cercarlo o a dichiarare che la direzione poggia solo sul mattino. |
| Euro Stoxx 50 su | Dopo il minimo da maggio aspetta di capire se Wall Street tiene | **Nessun motivo nelle schede per l'indice.** Le schede parlano di due titoli di Milano (N05) e del livello dell'indice (N06), non di che cosa lo spinge su. Direzione debole. |
| Treasury 10 anni su | Se la paura cala i Treasury smettono di fare da rifugio e il rendimento risale | invariato: è già un motivo (D01) |
| EUR/USD su | L'euro recupera un po' dopo una settimana di dollaro forte | **Nessun motivo nelle schede.** Le schede spiegano solo il dollaro forte (Waller, MEM-1120-MEM-1119-N12), che spinge nel verso opposto. Direzione debole: va detto o cercato. |
| Brent giù | Con meno fiducia nella crescita e più offerta il greggio ha poca spinta | Le scorte americane salite di oltre 5 milioni di barili tengono basso il greggio (MEM-1118-D05) |
| Oro su | Rimbalza dopo la caduta di venerdì, la peggiore da mesi | **Nessun motivo nelle schede.** Le schede dicono perché l'oro è sceso (dollaro forte e attese di una stretta Fed, MEM-1120-N10), non perché dovrebbe salire. Direzione debole. |

### Lunedì 16/11 - tesi: decidono i conti di Nvidia e i verbali Fed; se la spesa in AI regge e i verbali non aggiungono toni più duri, le borse recuperano

| Mercato | Prima | Dopo |
|---|---|---|
| S&P 500 giù | I future perdono terreno dopo il crollo dei chip asiatici | invariato: è già un motivo (T01, D02) |
| Euro Stoxx 50 su | L'Europa aspetta i conti di Nvidia dopo una settimana forte | Per un analista di Bankhaus Merck Finck, se l'intelligenza artificiale si indebolisce le borse europee vanno meglio di quelle americane (D08) |
| Treasury 10 anni su | La Fed parla oggi e mercoledì: un tono duro tiene alti i rendimenti | Waller e Logan chiedono già rialzi a dicembre: il rendimento resta spinto in su anche senza toni nuovi (MEM-1113-D04) |
| EUR/USD giù | Con rialzi Fed attesi il dollaro resta il rifugio contro l'euro | **Nessun motivo che non sia la Fed già data al Treasury.** Le schede dicono solo "dollaro in rafforzamento" (N12). Direzione debole. |
| Brent su | Gli attacchi nel Golfo e nel Mar Rosso tengono il rischio sulle forniture | Lo stretto di Hormuz resta chiuso: il rischio sulle forniture tiene alto il prezzo (D11, N07) |
| Oro giù | Il dollaro forte e i tassi alti pesano sull'oro | invariato: è già un motivo (N12) |

Che cosa vede il lettore: nelle due settimane si passa da 4 motivi veri su 12 a 7 su 12. Per gli altri 5 le schede del giorno non avevano un motivo: la regola non lo inventa, obbliga a cercarlo al passo delle prove. Se la ricerca non lo trova, la regola chiede di dire che la direzione è debole e su che cosa poggia (al più due righe su sei senza avviso).

## Non verificato

Come scriverà davvero il modello del mattino con la regola nuova si vede solo nella prova del 5-6/12. Non verificato nemmeno se la redazione, davanti all'errore, cercherà un motivo vero o ripiegherà su una formula che il controllo non vede (per esempio un mattino descritto senza causa): quella forma resta alla rilettura del revisore.
