# Mail straordinarie (DEM)

Tutto ciò che parte agli iscritti fuori dall'edizione del mattino: auguri, avvisi sulle pause, sondaggi. Una mail = un file in questa cartella. Il file è la verità, Kit è solo l'esecutore. Script: `redazione/dem.py`. Postino: `.github/workflows/dem.yml`. Vista: pannello, pagina **Invii** (`gommberg.com/pannello/#invii`).

## Il percorso di una mail

1. **Bozza.** Claude scrive il file con `stato: bozza`, lancia `python3 redazione/dem.py salva` e fa il commit su main. Il postino la mette in Kit come bozza senza data: da Kit si può mandare una mail di prova a sé stessi. Claude manda a Paolo l'anteprima (`dem.py anteprima NOME`).
2. **Ok di Paolo.** Claude mette `stato: approvata` e `ok: Paolo AAAA-MM-GG`, poi `salva` e commit. Il postino la programma in Kit per la data di invio. Da lì parte da sola.
3. **Cambi.** Si cambia il file, sempre con `salva` e commit: il postino aggiorna Kit. Una mail che deve partire entro 15 minuti non si tocca più.
4. **Annullare.** `stato: annullata` (resta nello storico) oppure si cancella il file: in tutti e due i casi il postino toglie l'invio da Kit, se non è ancora partito.

Ogni sera alle 19:30 il postino riallinea Kit ai file. Se qualcosa va guardato apre una segnalazione a Paolo, e GitHub gli manda l'email: una bozza a meno di 10 giorni dalla data senza ok, una mail approvata che non è partita, un'operazione che Kit ha rifiutato. Se va tutto bene non scrive a nessuno.

I file di questa cartella e `pannello/invii.json` si aggiornano su main in qualunque giorno: non toccano l'edizione né le pagine dei lettori. Lo script e il workflow invece passano dal rilascio, come il resto della macchina.

## Il formato

Nome: `AAAA-MM-GG-nome.md`, con la data di invio (così in ordine decrescente la più recente viene per prima).

```
---
invio: 2026-12-19 10:00
stato: bozza
oggetto: Buone feste dal Gommberg
anteprima: La riga che il programma di posta mostra accanto all'oggetto.
titolo: Buone feste
firma: Paolo Gommellini | Direttore
pulsante: Leggi l'ultima edizione | https://gommberg.com/
ok:
---
Testo della mail.
```

- `invio`: data e ora di Roma. `stato`: bozza, approvata, annullata. `ok`: obbligatorio per approvata (`Paolo AAAA-MM-GG`).
- Facoltativi: `titolo` (grande, in apertura), `firma` (nome | ruolo; senza firma "La redazione del Gommberg"), `pulsante` (testo | indirizzo), `nota` (postilla piccola dopo la firma, per gli avvisi di servizio).
- Nel testo, blocchi separati da una riga vuota: paragrafo; `## Titoletto`; elenco con righe `- `; riquadro con righe `> `; `**grassetto**`; `[link](https://...)`.
- **Sondaggio** (uno per mail): una riga `?? Domanda`, poi da 2 a 5 risposte con `- `. Ogni risposta è un link verso `gommberg.com/grazie.html`: Kit conta i clic di ogni link (nel report dell'invio, sezione dei link) e la pagina ringrazia. Il perché delle risposte arriva rispondendo alla mail.

Testata, caratteri e piè di pagina (riga sull'AI, Chi siamo, Privacy, annulla l'iscrizione, indirizzo) sono quelli dell'email del mattino: modello "Gommberg cornice" in Kit.

## Le regole (in `dem.py`, controllate a ogni commit e nel collaudo)

- Al massimo una mail ogni 21 giorni; le annullate non contano.
- Invio tra le 8:00 e le 20:59. Nei giorni di uscita mai tra le 7:00 e le 10:59: c'è l'edizione. Meglio il sabato mattina.
- Oggetto da 8 a 78 caratteri, mai tutto maiuscolo né con punti esclamativi ripetuti; anteprima da 20 a 140.
- Testo fino a 400 parole (avviso sopra 250); solo link https; solo il trattino corto.
- Il testo si scrive 2-3 settimane prima dell'invio: la data si può fissare anche mesi prima.
- Le finalità dichiarate in `privacy.html` coprono edizione e comunicazioni della redazione al massimo una volta al mese. Un uso diverso (per esempio pubblicità o mail a una parte degli iscritti in base al loro comportamento) richiede prima di aggiornare la privacy.
