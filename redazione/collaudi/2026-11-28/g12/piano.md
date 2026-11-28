# G-12 - I minuti di GitHub da privato: piano con i numeri (28/11/2026)

Con le tre leve già in linea: circa **350 minuti su 2.000 in un mese normale (17%), 690 in uno pesante (35%)**. Con cinque passi piccoli: **170 e 370 (8% e 19%)**, sotto il 25% anche tra tre anni. **[M]** misurato, **[S]** stimato, **[V]** da verificare. Minuti Linux standard equivalenti (ubuntu-slim un terzo, ogni job arrotondato in su: [prezzi](https://docs.github.com/en/billing/reference/actions-runner-pricing)). Conti interi: `misura.md` e gli script di questa cartella.

## 1. La misura [M]: 484 giri, 1.018 job, 14/10-28/11 (i flussi esistono dal 15-22/11)

| classe | 45 giorni, com'era | 21-28/11, com'era | 21-28/11 con le leve di oggi |
|---|---:|---:|---:|
| a) edizioni: sito.yml, newsletter, mattino dopo la pubblicazione | 21 | 16 | 9 |
| b) sviluppo: collaudo.yml 634, sito.yml 51, dem.yml da push 24, a mano 20 | 729 | 695 | 136 |
| c) a orario: mattino 19, segnalazioni 12, dem 10, sito.yml dal GOMM 6 | 47 | 47 | 20 |
| d) GitHub Pages | 613 | 0 | 0 |
| totale | 1.410 | 758 | 166 |

- **Il costo era il collaudo a ogni push**: 135 giri per 17 rilasci, 634 minuti in 8 giorni (ritmo di 2.400 al mese, oltre la quota). Giorni peggiori: 22/11 229 minuti (58 con le leve), 27/11 6 rilasci e 131 minuti (44).
- **Pages non conta**: finito il 20/11 e comunque gratuito ([GitHub](https://docs.github.com/en/billing/concepts/product-billing/github-actions)); 384 dei minuti di novembre in `pannello/minuti.json` sono falsi.
- **dem.yml dai rami di lavoro**: 26 giri dal 22 al 27/11, 21 minuti (9 a prezzo slim), quando un push porta file delle mail, anche solo unendo main. Non serve: lì fa solo il controllo che `collaudo.py` fa già.
- **Il filtro di sito.yml funziona**: 79 commit su main, 56 fermati, 17 giri di cui 3 a vuoto. **Le sveglie di GitHub no**: delle segnalazioni orarie ne parte una su dieci, quella delle 10:15 arriva alle 19-21; l'orologio di Cloudflare aspetta il token.

## 2. La proiezione da privato [S su basi M] - 22 edizioni; normale 12 rilasci, pesante 40 (quattro weekend come il 27-28/11)

| flusso, oggi | normale | pesante | | dopo il passo | normale | pesante |
|---|---:|---:|---|---|---:|---:|
| a) edizioni | 37 | 37 | | oggi | 350 | 691 |
| c) segnalazioni, 6 al giorno | 60 | 60 | | 1. dem.yml solo da main | 345 | 664 |
| c) mattino 10:15, sito dal GOMM, dem della sera | 47 | 47 | | 2. G-58 passo 2 | 282 | 601 |
| c) sveglie di riserva (40-99) | 63 | 63 | | 3. segnalazioni a evento | 234 | 553 |
| b) collaudo dal cancello, 8 min x 1,25 (kit 156 s, browser 154 s) | 120 | 400 | | 4. sito.yml su ubuntu-slim | 214 | 523 |
| b) sito dopo rilasci e prove, dem dai rami, a mano | 24 | 85 | | 5. collaudo in un job con cache | **169** | **373** |

Il collaudo dal cancello misura 6 minuti; ne conto 8 perché da privato le macchine hanno 2 CPU, non 4 ([GitHub](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)) [V al primo rilascio]. **Tra uno e tre anni** cresce solo l'archivio: `pagine.py` rifà tutto a ogni giro e il collaudo lo lancia 5 volte, +97 s l'anno [M in locale]. Senza fare nulla 380/791 tra un anno e 485/1.033 tra tre; con il piano e `pagine.py` che rifà solo il nuovo 169/373 e 209/434. **Un muro fuori dai minuti**: Cloudflare gratuito tiene 20.000 file per sito ([limiti](https://developers.cloudflare.com/workers/platform/limits/)); oggi 446, +20 a edizione [M]: pieno nell'autunno 2030.

## 3. Le leve senza spendere (minuti al mese risparmiati, normale / pesante)

| leva | risparmio | rischio | lavoro |
|---|---:|---|---|
| 1. dem.yml solo da main | 5 / 27 | nessuno | una riga |
| 2. G-58 passo 2, via le sveglie di riserva | 63 / 63 | quello già scritto in ARCHITETTURA | pronto (`f46cfbd`) |
| 3. segnalazioni a evento: l'orologio lancia il flusso solo se nel suo database c'è un commento segnalato | 48 / 48 | basso; avviso in 15 minuti, non 3 ore | mezza giornata |
| 4. sito.yml su ubuntu-slim (1 CPU, contenitore, 15 minuti al massimo: [GitHub](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)) | 20 / 30 | [V] un giro sul ramo prova | una riga |
| 5. collaudo.yml in un job con cache di pip, apt, Playwright (10 GB gratis: [GitHub](https://docs.github.com/en/actions/reference/limits)) | 45 / 150 | cache vecchia; attesa da 2,5 a 4 minuti | mezza giornata |
| tempi massimi corti (kit 8, browser 10, pubblica 8) | tetto ai danni | un job lento vero fallisce | tre righe |
| su GitHub solo il browser, kit solo in locale | 45 / 150 | si perde la macchina pulita, che ha trovato guasti | solo come freno al 75% |
| 6. sito pubblicato da Cloudflare (Workers Builds, 3.000 minuti gratis: [Cloudflare](https://developers.cloudflare.com/workers/ci-cd/builds/limits-and-pricing/)) | 40 / 62 | cambia la catena del mattino | 1-2 giorni e una prova |
| runner proprio | tutti | **sconsigliato**: l'edizione dipende da un PC di Paolo acceso; il runner vede i segreti e non riparte pulito ([GitHub](https://docs.github.com/en/actions/reference/security/secure-use)); tariffa anche per i runner propri annunciata e solo rinviata ([GitHub](https://github.com/resources/insights/2026-pricing-changes-for-github-actions)) | alto |
| repository pubblico che esegue i flussi del privato | tutti | **no**: le condizioni escludono attività estranee al progetto del repository dove Actions gira ([GitHub](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features)); log pubblici; token del privato in un repository pubblico. Con il solo sito pubblico è lecito, ma il passo 6 dà lo stesso con un repository | - |
| tornare pubblici | tutti | il motore torna visibile | un clic: uscita d'emergenza |

Tutte reversibili.

## 4. La rete di sicurezza senza carta

- **Quota finita**: senza metodo di pagamento l'uso si blocca ([GitHub](https://docs.github.com/en/billing/concepts/product-billing/github-actions)) e torna alle 00:00 UTC del primo del mese ([cicli](https://docs.github.com/en/billing/concepts/billing-cycles)). Coda o fallimento: la documentazione non lo dice [V]; di norma i giri falliscono e non ripartono da soli. Si fermano sito.yml, newsletter e il controllo del mattino: **anche l'allarme**. GitHub avvisa da sé al 90% e al 100% ([avvisi](https://docs.github.com/en/billing/how-tos/set-up-budgets)) [V che sia acceso].
- **Riserva del sito, zero minuti**: Workers Builds collegato al repository sul solo ramo `riserva` ([rami](https://developers.cloudflare.com/workers/ci-cd/builds/build-branches/), [Python e Node ci sono](https://developers.cloudflare.com/workers/ci-cd/builds/build-image/)): `git push origin main:riserva` pubblica senza GitHub Actions e senza segreti nella sessione; oppure un [Deploy Hook](https://developers.cloudflare.com/workers/ci-cd/builds/deploy-hooks) [V: repository privato, un giro di prova]. Wrangler dalla sessione del mattino no: da una sessione Cloudflare non si raggiunge [M].
- **Soglie** sulla stima di `minuti.py` (rifatta anche a ogni `pubblica`), applicate in `orologio.js` e `rilascia.sh`, dove dire di no costa zero; la newsletter non ha riserva, quindi si spegne prima il resto. **50%** nota. **75%** fermi battito delle segnalazioni, sito rilanciato dal GOMM, dem della sera senza mail vicine; al cancello solo il browser. **90%** `pubblica` solo con `--guasto`: restano edizione, newsletter e controllo, 2,4 minuti al giorno (il 10% basta per 80 giorni). **100%** ramo `riserva`; Paolo sceglie se aspettare il primo del mese o tornare pubblici.

## 5. Raccomandazione

- **Prima del 1/12** (un rilascio con Ok, senza edizione di prova): passo 1, tempi massimi corti, `collaudo.yml` e `sito.yml` dichiarano i minuti, `minuti.py` senza Pages -> 345 / 664. Paolo: avvisi di GitHub accesi; altri repository privati con Actions? (la quota è dell'account).
- **Dopo**: 2 (prima il token dell'orologio) -> 282 / 601; 3 -> 234 / 553; 4 -> 214 / 523; 5 -> 169 / 373; soglie e ramo `riserva`; poi `pagine.py` e, se si vuole, il 6 (129 / 311).
- **La regola**: ogni flusso ha in testa `# Minuti di GitHub: <normale>/<pesante> al mese`. `collaudo.py` ferma il rilascio se manca, se la somma supera 1.000, se un flusso parte da push senza `branches`, ha una `schedule` (dopo il passo 2) o un job senza tempo massimo. `minuti.py` confronta ogni giorno ogni flusso con il dichiarato: oltre il 150% è una riga rossa del mattino. Una regressione si vede in un giorno, non al 75%.
- **Per sempre?** I minuti crescono con i rilasci, non con lettori o edizioni: con il piano ne servono circa 280 in un mese (9 al giorno) per arrivare a 2.000. Restano quattro casi: (1) torna un flusso a ogni push (quota in 9 giorni) - lo ferma la regola; (2) altri repository privati dell'account [V]; (3) GitHub cambia il piano gratuito; (4) un job bloccato o che si rilancia - tempi massimi. In ogni caso: soglie, ramo `riserva`, tornare pubblici con un clic.
