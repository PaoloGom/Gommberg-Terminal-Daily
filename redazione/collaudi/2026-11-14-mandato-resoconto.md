# Mandato del 14/11/2026 - resoconto

Ramo di lavoro: `mandato-2026-11-14`, nato dal ramo `v8` (v8.6, commit af3e0ba). Il ramo principale, il sito e l'attività del mattino non sono stati toccati. Nulla è stato pubblicato.

## 1. Diagnosi: cosa ho trovato
**Il prodotto è già di livello alto.** PDF curato, sito solido su PC e telefono (11 pagine provate a 1366 e 390 px con i caratteri veri: nessun errore, nessuna pagina che esce dallo schermo), scommessa con metodo e collaudo storico, schede dei fatti con fonte e citazione. Controllo a campione sull'apertura della #025: dimissioni di Huang, Kress alla guida ad interim, Jones primo presidente, conti il 17/11 e titolo a -4,3% coincidono con il comunicato depositato alla SEC e con il resoconto Reuters.

**Il collo di bottiglia non sono le regole, è il modo di provarle.** In 33 giorni il kit ha avuto circa 150 modifiche (9 tra la sera del 13/11 e la mezzanotte), su 24 rami. Ogni modifica si verificava solo con una prova dell'attività vera, che costa 4-6 punti del limite settimanale, gira a ore diverse dall'edizione e si giudica a occhio. Risultato: non si sa quale modifica abbia aiutato, e due difetti sono entrati nella v8 senza che nessuno li vedesse.
- **La v8.4 ha svuotato la pagina di riferimento.** Applicando "un'idea, un posto" ha tolto testi senza rimetterne: 5 moduli tra il 63% e l'86% di riempimento, pag. 2 con 17 mm vuoti. È la stessa causa dell'edizione #021 "sottile" del 9/11. Sonnet imita il modello: un modello mezzo vuoto produce edizioni che falliscono il riempimento e si riempiono in fretta nei giri di correzione.
- **Il controllo bloccante della v8.5 dava falsi errori.** "Frase oltre 30 parole" si misurava sul testo estratto dal PDF, dove titolo e sommario, i punti di un elenco o una tabella intera diventano una "frase": 5-6 errori in ognuna delle edizioni #022-#025, nella prova del 13/11 e nel modello stesso. In linea avrebbe consumato i giri di correzione ogni mattina su errori che non si possono correggere scrivendo meglio.
- **I dati intermedi si buttavano.** Del lavoro di una mattina restavano PDF e schede; il testo scritto, i dati di mercato e gli esiti di revisione sparivano. Quindi nessuna edizione si poteva rifare e nessun confronto "stessi dati, regole diverse" era possibile.

**Sul lettore senza studi di finanza il divario è reale.** L'approfondimento sui tassi della prova del 13/11 dà per noti rendimento, curva, punti base, future sui tassi e non dice mai perché un dato debole sul lavoro "dovrebbe" far scendere i rendimenti. La libreria che serviva c'era già (27 meccanismi verificati in `meccanismi.json`), ma le istruzioni v8 non la citavano più: usata in 8 edizioni su 10 a ottobre, in 3 delle ultime 10.

**Dove una tua richiesta e il mandato tirano in direzioni opposte.** Il 9/11 hai detto che il giornale "spiega fin troppo" (pb, parentesi); il mandato chiede di spiegare a chi parte da zero. Non sono in contraddizione se si distingue: le definizioni delle parole annoiano chi sa e non bastano a chi non sa; ciò che manca è il passaggio, cioè perché il fatto muove il prezzo. Ho lavorato solo su quello.

## 2. Direzione scelta
Prima il metro, poi le regole. Un cambiamento editoriale solo, misurabile, nel punto dove il lavoro passa già; nessun agente, passo o servizio nuovo nell'edizione del mattino.

## 3. Decisioni e alternative scartate
- **Partire dalla v8, non dal ramo principale**: è la direzione che hai già approvato e contiene memoria, sensori, fonti per autore. Rifarla da capo sarebbe stato stratificare.
- **Collaudo in codice invece di più prove con l'attività**: 15 secondi e zero token contro 20 minuti e 4-6 punti. Le prove vere restano, ma per giudicare il giornale, non per scoprire un apostrofo rotto.
- **Niente sezioni per principianti, niente definizioni in più**: scartate perché ripetono l'errore del 9/11. Scelto il passaggio dentro il racconto.
- **Meccanismi offerti, non imposti**: la prima versione li dava per obbligatori e il confronto ha mostrato il danno (punto 6). Corretto.
- **Niente modello più forte, niente passaggi in più**: l'edizione resta su Sonnet con gli stessi passi.
- **Non ho toccato la scrittura decisa la sera del 13/11** (v8.4-v8.6): ho corretto solo come viene misurata.

## 4. Lavoro realizzato (tutto in `redazione/`)
| Cosa | File | A cosa serve |
|---|---|---|
| Collaudo a secco | `collaudo.py` (nuovo) | Sintassi, avvio, modello impaginato e controllato, ultima edizione vera rifatta, sito e link, pubblicazione in prova |
| Misure | `misure.py` (nuovo) | Lo stesso metro per tutte le edizioni e per le prove |
| Sorgenti dell'edizione | `pubblica.sh`, `prova_v8.sh` | Testo scritto, dati, scommessa, revisione e desk archiviati in `sorgenti/AAAA-MM-GG/` |
| Ritmo delle frasi | `controlli_testo.py`, `controlli_tutti.sh` | Misura esatta sui campi, con le riscritture del desk; dal PDF solo avviso |
| Il passaggio | `ISTRUZIONI.md` (v8.7), `memoria.py` | Lettore anche senza studi; al massimo 2 meccanismi offerti per tesi |
| Pagina di riferimento | `edizione_modello_v6.py` | Di nuovo piena; mostra passaggi, lettura di pag. 2, numero che fa un conto |
| Calendario | `gommberg_engine.py`, modello | "Sopra/sotto le attese" con una regola sola e senza verde e rosso |
| Documenti | `PROGETTO.md`, `ATTIVITA.md` (nuovo) | Decisioni registrate; copia del testo delle attività programmate |

## 5. Verifiche
- **Collaudo**: rosso sulla v8.6 di partenza (riempimento e scrittura), verde sulla v8.7. 14 secondi.
- **Modello**: 6 pagine, pagine 1-5 e tutti i moduli pieni, controlli di scrittura, numeri, temi e ripetizioni verdi; anteprima guardata pagina per pagina. Pag. 6 non è giudicata nel collaudo: dipende dal registro della scommessa di quella settimana.
- **Controllo del ritmo**: sul modello 0 errori; sulle edizioni #022-#025 e sulla prova i falsi errori non compaiono più come errori.
- **Sito**: nessun difetto bloccante. Una falsa pista scartata: nel mio ambiente la testata sembrava tagliata sul telefono, ma era il carattere di riserva; con i caratteri veri sta nello schermo.
- **Limite**: non ho potuto lanciare l'attività vera. Tutto ciò che riguarda come Sonnet scrive un'edizione intera con le regole nuove resta da provare.

## 6. Confronto con la base
Misure delle ultime 10 edizioni pubblicate (v7.8) e della prova v8.3 del 13/11. Colonne spiegate in testa a `misure.py`.

| nome | ora | parole | fr | >30 | cifre | gergo | () | not | ag | ag+ | sch | dd | prim | l1 | mecc | par |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| #016 11-02 | 09:19 | 3114 | 19.8 | 17 | 3.3 | 17.4 | 13 | 6 | 6 | 0 | 18 | 0 | 0 | 22 | 0 | 3 |
| #017 11-03 | 09:20 | 2891 | 20.5 | 17 | 6.4 | 12.2 | 13 | 6 | 6 | 1 | 28 | 0 | 4 | 14 | 0 | 3 |
| #018 11-04 | 12:45 | 2954 | 20.4 | 18 | 6.8 | 11.4 | 30 | 6 | 7 | 0 | 16 | 1 | 6 | 75 | 2 | 3 |
| #019 11-05 | 09:19 | 2877 | 23.4 | 34 | 6.5 | 17.8 | 12 | 5 | 2 | 2 | 17 | 0 | 12 | 29 | 0 | 3 |
| #020 11-06 | 09:33 | 3338 | 21.0 | 11 | 6.4 | 6.0 | 11 | 5 | 2 | 1 | 27 | 15 | 7 | 22 | 1 | 3 |
| #021 11-09 | 09:17 | 3499 | 21.7 | 22 | 5.3 | 5.9 | 27 | 6 | 7 | 5 | 36 | 13 | 53 | 69 | 0 | 6 |
| #022 11-10 | 09:25 | 3394 | 18.2 | 10 | 6.9 | 13.9 | 16 | 5 | 2 | 2 | 28 | 10 | 7 | 57 | 0 | 6 |
| #023 11-11 | 09:17 | 3320 | 20.0 | 17 | 7.1 | 10.6 | 7 | 6 | 8 | 4 | 30 | 8 | 10 | 30 | 1 | 6 |
| #024 11-12 | 12:44 | 3391 | 18.3 | 12 | 4.6 | 7.2 | 16 | 6 | 5 | 2 | 27 | 12 | 7 | 63 | 0 | 6 |
| #025 11-13 | 09:14 | 3376 | 18.4 | 14 | 5.6 | 10.7 | 20 | 6 | 3 | 2 | 24 | 8 | 25 | 71 | 0 | 6 |
| media |  | 3215.4 | 20.2 | 17.2 | 5.9 | 11.3 | 16.5 | 5.7 | 4.8 | 1.9 | 25.1 | 6.7 | 13.1 | 45.2 | 0.4 | 4.5 |
| prova v8.3 13/11 |  | 3336 | 17.1 | 5 | 7.2 | 20.0 | 18 | 5 | 5 | 4 | 30 | 12 | 57 | 93 | 3 | 6 |

- La v8 migliora nettamente le fonti (schede con fonte primaria dal 13% al 57%, con fonte primaria o d'agenzia dal 45% al 93%; attenzione: nella v8 "primaria" è un campo dichiarato da chi scrive la scheda) e accorcia le frasi lunghe (dal 17% al 5%).
- La v8 è però più fitta di termini da addetti: 20 ogni mille parole contro 10,7 dell'edizione dello stesso giorno. È una coppia sola, ma va nella direzione opposta a quella del mandato.
- Puntualità: 6 edizioni su 24 oltre le 10:00; nelle ultime 10, due con circa tre ore di ritardo (4/11 e 12/11). Agenda: in media 1,9 righe con le attese su 4,8. Notizie: 4 edizioni sotto le 6 richieste.

**Confronto controllato sul passaggio** (`2026-11-14-confronto-passaggio/`): stesso approfondimento, stesse schede della prova del 13/11, stesura di Sonnet con regole v8.6 e v8.7, giudice esterno che non sapeva quale fosse quale.
- Tassi: il giudice pubblicherebbe la v8.7 e la trova più chiara per il neofita (termini da addetti da 15,5 a 9,3 ogni mille parole, cifre da 4,9 a 3,7 ogni cento); per l'esperto preferisce la v8.6, che ha più livelli e un paragrafo sull'Europa.
- Petrolio: il giudice ha preferito la v8.6. La v8.7 aveva incollato un meccanismo generale che contraddiceva la tesi. Ho corretto la causa (meccanismi offerti e non imposti, due al massimo, con l'uso previsto) e rifatto la stesura: il difetto non c'è più, ma questa seconda stesura non è stata rigiudicata alla cieca.
- Conclusione onesta: la direzione regge in un caso su due al primo colpo, ha un costo per il lettore esperto a parità di spazio, e due casi non sono una prova.

## 7. Costi e operatività
- **Misurato**: collaudo 14 secondi, nessun token. Confronto controllato: 6 agenti Sonnet, circa 85-90 mila token l'uno (quasi tutto contesto di avvio dell'agente).
- **Stimato**: sull'edizione del mattino la v8.7 aggiunge circa 0,6 KB di istruzioni e poche righe nell'uscita di `memoria.py tema`; nessun passo, nessun agente. Toglie i giri di correzione causati dai falsi errori sul ritmo. I sorgenti aggiungono al repository circa 50-80 KB per edizione.
- **Non noto**: durata e consumo di un'edizione intera con la v8.7; quanto questa sessione ha pesato sul tuo limite settimanale (non posso leggerlo).
- Nota: la misura settimanale della lettura gira su Opus; alle due attività sono ancora collegati Gmail, Drive, Calendar e Docs (e Canva a quella del mattino).

## 8. Rischi e questioni aperte
1. **Il ramo esiste solo nella sessione di lavoro**: a questa sessione è stato negato l'accesso in scrittura al repository. Serve il tuo sì per portarlo su GitHub (solo il ramo `mandato-2026-11-14`, mai il principale). In allegato alla consegna c'è la copia del ramo.
2. **La v8.7 non è provata con l'attività vera.** Va fatto prima di qualsiasi unione.
3. **Euro Stoxx 50**: la regola provvisoria del ramo principale scade il 20/11; la soluzione stabile sta nella v8. Se la v8 non entra entro quella data, va prorogata.
4. **Lettore esperto**: il passaggio occupa righe. Nella prova vera va guardato se toglie sostanza.
5. **Colonna "Sorpresa" senza verde e rosso**: è una scelta visibile nel PDF; se preferisci i colori si ripristina in una riga, la regola aritmetica resta.
6. Minori: causa del ritardo del 12/11 mai cercata; 4 pagine del sito senza titolo h1; `controlli_tutti.sh` può spezzare una lettera accentata quando taglia le righe; `ultima/` scarica ancora tutto `edizioni.json`; il testo dell'attività del mattino cita paragrafi che nella v8 non esistono più.

## 9. Stato del repository
- Ramo `mandato-2026-11-14`, 3 commit sopra `v8` (af3e0ba). Albero pulito. Ramo principale e ramo `v8` invariati.
- Per rivedere: `git diff v8..mandato-2026-11-14 --stat`, poi `python3 redazione/collaudo.py` (deve dire COLLAUDO: OK) e `python3 redazione/misure.py --ultime 10`.

## 10. Prossimo passo consigliato
Una prova con l'attività vera su questo ramo, di mattina, subito dopo l'edizione del giorno: è il solo modo di sapere se un'edizione intera scritta con la v8.7 batte quella uscita. Si confronta con `misure.py` e con la tua lettura; si unisce solo se è migliore.
