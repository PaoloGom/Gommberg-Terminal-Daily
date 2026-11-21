# Architettura del Gommberg

La mappa del sistema: quali parti ci sono, chi legge che cosa, e che cosa si rompe lontano se tocchi qui. Serve a chi sviluppa (per sapere dove guardare prima di cambiare) e al capo sviluppo del rilascio (per ordinare le voci e vedere i conflitti). Non contiene storia né cose da fare: la storia sta in `PROGETTO.md`, lo stato in `STATO.md`, le cose da fare nel Registro dei lavori.

**Regola di manutenzione.** Chi cambia un contratto (un file letto da un'altra parte, un campo di `edizioni.json`, un comando del mattino) aggiorna questa pagina e la rete del collaudo nello stesso commit. Scritta il 21/11/2026 (G-39), verificata sul codice di quel giorno.

## 1. Il viaggio di un'edizione

```
8:58 attività programmata (Sonnet, app di Claude; testo in ATTIVITA.md)
  │  legge ISTRUZIONI.md + appendici APP_*.md, parte da prepara.sh
  ▼
cartella di lavoro /home/claude/lavoro  (fuori dal repository)
  dati.json ─ contesto.json ─ fatti.json ─ edizione_AAAA-MM-GG.py ─ stato.json | verdetto.json
  │  gommberg_engine.py (+ scommessa/pagina6.py)  →  PDF di 6 pagine, voce_indice.json, riempimento.json
  │  controlli_tutti.sh (tutti i controlli)       →  testo.json (sigle), ripetizioni.json, anteprima.png
  │  revisione (agente) → desk (desk.py)          →  revisione.json, desk_ok.json
  │  edizioni_voce.py                             →  la voce in edizioni.json
  ▼
pubblica.sh  →  un commit "Edizione #NNN - data" sul ramo principale (main)
  pdf/  edizioni.json  redazione/fatti/  redazione/sorgenti/  dati/uscite.json
  pannello/registro.json (pannello.py)   e/  dati/  feed.xml  sitemap.xml  ultima/ (pagine.py)
  ▼
GitHub, a ogni push su main (zero token)
  sito.yml        costruisci.py → Cloudflare Workers → gommberg.com, poi verifica dal vivo (collaudo_sito.py --veloce)
  newsletter.yml  (solo se cambia edizioni.json) newsletter.py → Kit → email agli iscritti
  mattino.yml     alle 10:15 lun-ven: mattino.py controlla uscita, sito, pubblicazione, newsletter, pannello
```

## 2. Le parti

| Parte | Dove sta | Che cosa fa |
|---|---|---|
| Regole della redazione | `ISTRUZIONI.md`, `APP_*.md`, `NOTA_DEL_GIORNO.md`, `edizione_modello_v6.py` | Ciò che Sonnet legge ogni mattina: decide che cosa viene scritto |
| Lessico e fonti | `glossario.json`, `meccanismi.json`, `fonti.json`, `domini.txt` | Sigle, meccanismi, livelli delle fonti: li leggono regole, controlli e sito |
| Dati di mercato | `controlli_dati.py`, `numeri.py`, `contesto.py`, `scommessa/dati/*.csv` | Schema di `dati.json`, nastro, contesto dei movimenti |
| Motore | `gommberg_engine.py`, `extra_voce.py`, `giorni.py` | Impagina il PDF, scrive `voce_indice.json`; calendario delle uscite e numero dell'edizione |
| Scommessa | `scommessa/` (`pagina6.py`, `valuta.py`, `pronostico.py`, `metodo.json`, `pagella.json`), `pronostici/` | Pag. 6, registro della settimana, punteggi |
| Controlli | `controlli_tutti.sh` e i `controlli_*.py`, `anteprima.py` | Il cancello del mattino: ciò che non passa si corregge o si toglie |
| Revisione e desk | `desk.py`, `memoria.py`, `ricerche.py` | Riscritture del desk, memoria dei fatti già verificati |
| Indice | `edizioni_voce.py` → `edizioni.json` | Una voce per edizione: è il contratto centrale (vedi 3) |
| Pubblicazione | `pubblica.sh`, `messaggio.py` | Copia, archivia i sorgenti, rigenera le pagine, commit e push |
| Sito | pagine fisse in radice (`index.html`, `archivio.html`...), `assets/`, `pagine.py`, `sito/costruisci.py` | Pagine scritte a mano che si riempiono via JavaScript dai file di dati; pagine per edizione generate |
| Newsletter | `newsletter.py`, `newsletter_modello.html` (copiato a mano in Kit) | L'email del mattino dalla scheda `e/NNN.json` |
| Pannello | `pannello.py`, `misure.py`, `gancio_token.py`, `pannello/` | Una riga per edizione: orari, lavoro, qualità, consumo |
| Collaudo e rilascio | `collaudo.py`, `rete/`, `rilascia.sh`, `sito/collaudo_sito.py`, `mattino.py`, `.github/workflows/` | Vedi 4 e 5 |
| Prove | `PROVA.md`, `prova.sh` | Edizioni di prova con l'attività vera |
| Gestione | `CARTA.md`, `STATO.md`, `AZIONI.md`, `PROGETTO.md`, `ATTIVITA.md` | Visione, stato, lezioni, storia, testo delle attività |

## 3. Chi legge che cosa (i contratti)

Un file della colonna di sinistra è un contratto: cambiarne forma o significato tocca tutti quelli a destra.

| File | Lo scrive | Lo leggono |
|---|---|---|
| `edizioni.json` (una voce per edizione) | `edizioni_voce.py` | `pagine.py` (tutto il sito), `controlli.py`, `controlli_fatti.py`, `controlli_contenuti.py` (edizioni precedenti: temi, grafici, Stamattina), `memoria.py`, `misure.py`, `pannello.py`, `newsletter.py`, `mattino.py`, `ultima/index.html` |
| `e/NNN.json`, `e/NNN.html`, `e/NNN.png`, `e/pagine.json` | `pagine.py` | `index.html`, `glossario.html`, `newsletter.py` (la scheda `e/NNN.json`), anteprime di WhatsApp |
| `dati/recenti.json`, `indice.json`, `cerca.json`, `storico.json`, `redazione.json` | `pagine.py` | `index.html`, `scommessa.html` (recenti); `archivio.html` (indice, cerca); `glossario.html`, `numeri.html` (storico); `progetto.html` (redazione); `mattino.py`, `collaudo_sito.py` |
| `dati/uscite.json` | `pubblica.sh` | `numeri.html` (puntualità) |
| `redazione/fatti/AAAA-MM-GG.json` | `pubblica.sh` (dalle schede del mattino) | `memoria.py`, `misure.py`, `pannello.py`, `collaudo.py` |
| `redazione/sorgenti/AAAA-MM-GG/` | `pubblica.sh` | `collaudo.py` (rifare un'edizione, congelare un campione) |
| `redazione/glossario.json`, `glossario_sito.json`, `meccanismi.json` | a mano (e la redazione, per glossario e meccanismi) | `controlli_testo.py`, `edizioni_voce.py`, e **il sito**: `glossario.html` |
| `redazione/scommessa/pagella.json` | `valuta.py`, con il verdetto della settimana | pag. 6 del PDF, e **il sito**: `scommessa.html`, `numeri.html` |
| `redazione/scommessa/metodo.json`, `pronostici/*.json` | a mano / `pronostico.py` | `pagina6.py`, `valuta.py`, `edizioni_voce.py` |
| `redazione/fonti.json` | a mano | `controlli_fatti.py`, `controlli_testo.py`, `controlli_contenuti.py`, `controlli_ripetizioni.py`, `misure.py` |
| `pannello/registro.json`, `taratura.json` | `pannello.py` | `pannello/index.html`, `mattino.py` |
| `/tmp/gtd_token.json` | `gancio_token.py` (`.claude/settings.json`) | `pannello.py --indici` |
| `voce_indice.json`, `testo.json` (cartella di lavoro) | motore; `controlli_testo.py` | `controlli_temi.py`, `controlli_contenuti.py`, `edizioni_voce.py`, `messaggio.py` |

Tre cose da ricordare:
- **Quattro file della redazione sono pubblici**: `glossario.json`, `glossario_sito.json`, `meccanismi.json`, `scommessa/pagella.json` (elenco `LETTI` in `costruisci.py`). Tutto il resto di `redazione/` non arriva mai su gommberg.com.
- **Le pagine in `e/`, `dati/`, `ultima/`, `feed.xml` e `sitemap.xml` sono generate**: non si toccano a mano. Chi cambia `pagine.py` rigenera (`python3 redazione/pagine.py`) e committa le pagine nello stesso commit: il collaudo lo pretende.
- **Fuori dal repository**: il testo delle attività programmate (app di Claude, copia in `ATTIVITA.md`), i due modelli di email e il modulo di iscrizione (Kit), DNS e Worker (Cloudflare), i segreti di GitHub (`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `KIT_API_KEY`), GoatCounter, Search Console. Un cambiamento che li riguarda non lo vede nessun collaudo: va scritto nel piano del rilascio e provato a mano.

## 4. La rete di non regressione

Un solo comando, `python3 redazione/collaudo.py` (meno di un minuto, senza rete e senza modelli), dopo ogni modifica:

1. sintassi di tutti i `.py` e `.sh`; 2. avvio (`prepara.sh` in tre giorni tipo); 3. pagina modello impaginata e controllata;
4. **rete**: le edizioni campione di `redazione/rete/` rifatte dai loro sorgenti con il kit di oggi lungo la catena del mattino, e confrontate con l'atteso (`atteso/`): testo del PDF, esito dei controlli, voce di `edizioni.json`, email, numeri del pannello;
5. sito: file validi, link interni, **pagine generate identiche a quelle nel repository**, `costruisci.py` senza avvisi; 6. pubblicazione a secco.

Ogni differenza ferma. Se è un guasto si corregge; se è voluta si rilancia con `--atteso`, che riscrive l'atteso e stampa che cosa è cambiato: quel cambiamento è nel commit e nel resoconto del rilascio, dove lo vede anche Paolo. `--campione AAAA-MM-GG` congela un'edizione nuova (accettata solo se, rifatta, è identica a quella pubblicata).

Come cresce: un guasto arrivato ai lettori diventa un campione o un controllo in più, nello stesso rilascio che lo corregge. I campioni coprono oggi un lunedì con il verdetto (16/11), un giorno qualsiasi (18/11) e un venerdì passato dal desk (20/11).

Che cosa la rete **non** vede: ciò che Sonnet scriverà con regole nuove (serve un'edizione di prova, `PROVA.md`), l'aspetto grafico (colori, immagini: si guarda l'anteprima), i servizi esterni (Kit, Cloudflare), le pagine nel browser (le apre `collaudo_sito.py`, su GitHub a ogni push sul ramo di rilascio).

## 5. Il rilascio

Il ramo principale è ciò che i lettori vedono: ogni push lo ripubblica. Per questo il lavoro si fa sul ramo `rilascio` e main riceve un solo merge.

```
bash redazione/rilascia.sh avvia      sabato (o per un guasto): la sessione va sul ramo rilascio, allineato a main
   ... una voce alla volta: modifica, collaudo.py, commit, git push origin rilascio ...
bash redazione/rilascia.sh collauda   quando si vuole: collaudo e resoconto, main non si tocca
bash redazione/rilascia.sh pubblica   alla fine: i cinque cancelli, poi un solo merge su main
bash redazione/rilascia.sh annulla    se serve: toglie da main l'ultimo rilascio
```

I cinque cancelli di `pubblica`: niente modifiche non salvate; il ramo contiene l'ultimo main; collaudo verde; **ok di Paolo** se cambia ciò che il lettore vede (file pubblici del sito, testo del PDF o email dei campioni, modello della newsletter); collaudo di GitHub verde sullo stesso commit (`collaudo.yml`: stesso collaudo su un'altra macchina, più il sito aperto in un browser e confrontato con gommberg.com).

Due ruoli, due chat diverse:
- **Capo sviluppo** (apre e chiude il rilascio): legge questa mappa e le voci del weekend, scrive il piano nel Registro (ordine, file toccati, conflitti, chat e modello per ogni voce), integra, lancia `pubblica`.
- **Collaudo indipendente** (prima del merge): un agente che non ha visto il lavoro controlla il "Fatto quando" di ogni voce contro il ramo e legge il resoconto. Chi costruisce non si collauda da solo.

Durante il rilascio i file di stato (`STATO.md`, `PROGETTO.md`, `AZIONI.md`) si aggiornano sul ramo principale come in settimana (non ripubblicano il sito); tutto il resto sta sul ramo `rilascio`.

Dopo il merge: `sito.yml` pubblica e verifica dal vivo; il lunedì `mattino.yml` controlla la prima edizione. Le prove con l'attività vera si fanno prima del merge dal ramo `rilascio` (procedura A di `PROVA.md`) e, per provare anche la pubblicazione, dopo il merge con una data simulata (procedura B).

In settimana un guasto segue la stessa strada in piccolo: `avvia`, correzione, `pubblica`.
