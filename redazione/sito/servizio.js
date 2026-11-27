// Il punto d'ingresso del Worker di gommberg.com ("main" in wrangler.jsonc). Esporta solo il gestore: Cloudflare tratta
// ogni export del modulo principale come un punto d'ingresso e rifiuta lo script se uno è una costante (provato con
// wrangler dev 4.165.0: "Incorrect type for map entry 'NOMI_UNICI'"). Le costanti e le funzioni che il collaudo prova
// restano esportate da lettori.js (i lettori, G-13), redazione.js (l'area riservata, G-51) e orologio.js (G-58).
import servizio from "./lettori.js";

export default servizio;
