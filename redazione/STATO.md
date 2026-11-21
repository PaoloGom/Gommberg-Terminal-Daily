# Stato del Gommberg

Aggiornato: 21/11/2026 mattina (Registro come ordine di lavoro, G-18). Deve bastare da solo a una chat nuova. Lo riscrive Claude in corsa, a ogni decisione, insieme al Registro.

Lista delle cose da fare: il **Registro dei lavori** (artifact `97f08bbc-950b-4b6e-83eb-4b8d032a3783`, https://claude.ai/artifact/KmCtJUZFx2WKVCRaDiHPtE). Una voce si legge per codice (`db_query` su `tasks`, `codice` = "G-xx"). Dal 21/11 ogni voce è un ordine di lavoro: priorità (Max, High, Medium, Low, TBD = idee), ownership (Claude, Insieme, Paolo), targhetta modello e sforzo, scheda con obiettivo, fatto quando, come, decisioni e vincoli, dipendenze ("dopo"). Le decisioni di una voce stanno solo nella sua scheda: qui si citano i codici.

## In linea
- Istruzioni v9.0 (struttura nuova delle 6 pagine), scommessa metodo 1.3 dal 16/11, 30 edizioni (ultima #030 del 20/11).
- **Sito su https://gommberg.com/ dal 20/11 sera (G-11)**: Cloudflare Workers con soli file statici, pubblicato da `.github/workflows/sito.yml` a ogni push su main (solo la parte pubblica, `redazione/sito/costruisci.py`), verifica dal vivo dopo ogni pubblicazione; ramo `prova` = anteprima su workers.dev. Il vecchio indirizzo paologom.github.io/Gommberg-Terminal-Daily reindirizza alla stessa pagina dal ramo `vecchio-indirizzo` (GitHub Pages). www porta alla radice. Kit (modulo e modelli) e Search Console (proprietà Dominio gommberg.com, sitemap) aggiornati.
- Sito con homepage B, riquadri dei mercati per il neofita, pagina Impara.
- Newsletter con Kit da redazione@gommberg.com (SPF/DKIM/DMARC ok), un solo pulsante verso il sito dal 17/11.
- #028 corretta il 19/11 notte nel lessico (guidance, buy, le vendite): PDF e sito rifatti, newsletter non ripartita. Causa delle traduzioni in `glossario.json` (lessico "previsioni" al posto di guidance): si toglie in G-07.
- Edizioni #027 e #028 controllate (G-01, 18/11): avvio 8:59, uscita 9:28; nessuna pagina negata. Il file dei permessi (`.claude/settings.json`) non fa da filtro: l'attività gira con approvazione automatica e apre anche siti fuori elenco.

## Cantiere attivo
**Affidabilità della macchina** (pilastro 5), rilascio del weekend 21-22/11. Ordine, con dettagli e decisioni nelle schede del Registro:
- G-38 prima (merge del pannello nuovo, prerequisito di G-02; serve l'ok di Paolo sulle schermate);
- pacchetto "Affidabilità delle fonti": G-34 (regola dei fatti nel controllo) e G-02 (la misura nel pannello), nella stessa chat;
- G-03 (Euro Stoxx 50 con seconda fonte da EODHD), in una chat sua.
Il resto del weekend è nel Registro in ordine di lavoro; la barra della capienza (12 punti, da ritarare) dice cosa non ci sta.

## Prossimo passo
Weekend 21-22/11: il rilascio del motore del pacchetto "La macchina" (cantiere attivo), da fare dopo un controllo veloce che `sito.yml` sia verde. Edizioni di prova solo con la procedura B di `PROVA.md` (data simulata: la newsletter non parte); ora ogni push su main ripubblica anche gommberg.com. Lunedì 23/11: prima edizione vera sul nuovo dominio, da controllare (pubblicazione e verifica verdi, link della newsletter su gommberg.com). Poi G-12 (repository privato), che sposta il ramo `vecchio-indirizzo` in un repository pubblico con il vecchio nome.

## Regole del ritmo
- Lun-ven il ramo principale non si tocca, salvo guasti e i file di stato della redazione; bozze sul ramo `prova`. Un rilascio nel weekend, tutto pulito entro domenica sera.
- Modello: Sonnet per controlli e piccole correzioni; Opus per dati, motore, decisioni, sito; Fable solo per revisioni grandi e rare.
- Una chat per tema; se si allunga, si chiude salvando qui e nel Registro e si riparte da una nuova.

Ultima revisione del patto (skill "gommberg"): 18/11/2026 (lettura del Registro per codice).
