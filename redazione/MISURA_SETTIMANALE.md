# Misura settimanale della lettura (v8.3, dal 13/11/2026)

Il Gommberg misura da sempre il processo (schede, fonti, controlli). Questa misura guarda il lettore: dopo la prima pagina, un lettore di media competenza sa dire cosa è successo, perché e cosa guardare oggi? Si fa una volta a settimana, fuori dall'edizione del mattino (nessun costo sull'edizione), con l'attività programmata "Gommberg: misura della lettura".

## Come si fa
1. Le edizioni della settimana: i PDF in `pdf/` del ramo principale con data da lunedì a venerdì.
2. Per ognuna si legge SOLO la prima pagina (`pdftotext -f 1 -l 1`). Chi misura si mette nei panni di un lettore che conosce i mercati per sentito dire: niente ricerche, niente altre pagine.
3. Risponde in una o due frasi a tre domande, solo con ciò che la pagina dice:
   - **Cosa è successo?** (il fatto principale)
   - **Perché?** (la causa, o la lettura che la pagina ne dà)
   - **Cosa guardo oggi?** (un evento o un livello, con l'ora)
4. Poi confronta con le pagine interne dell'edizione e dà a ogni risposta un voto: 2 = giusta e completa, 1 = parziale, 0 = sbagliata o impossibile da dare. Massimo 6 per edizione.
5. Annota per ogni edizione le parole o le frasi su cui il lettore si è fermato (sigle, gergo, frasi da rileggere, titoli ambigui), con la riga esatta.

## Cosa esce
Una riga per edizione in `redazione/collaudi/lettura.md` sul ramo `misure` (mai sul ramo principale):
`| AAAA-MM-GG | n. | cosa 0-2 | perché 0-2 | oggi 0-2 | totale /6 | dove ci si ferma |`
e un messaggio a Paolo di massimo 6 righe: media della settimana contro la precedente, l'edizione migliore e la peggiore, i 3 inciampi più frequenti. Nessuna modifica alle istruzioni: le correzioni si decidono con Paolo nella chat di progetto.

## Come si legge
- Sotto 5 di media: la prima pagina non regge da sola; si guarda prima il quadro e "In 30 secondi".
- "Perché" a 0-1 più volte: la causa resta nelle pagine interne o è scritta in gergo.
- Gli stessi inciampi per due settimane: vanno al desk (`ISTRUZIONI.md` §4.8) come esempio, non come regola nuova.
