// Anteprima del Registro: la pagina vera con un'istantanea dei dati e un database finto in memoria.
// Serve a mostrare a Paolo una modifica della pagina prima di pubblicarla. Nessun tasto fa partire nulla.
// Uso: node redazione/registro/anteprima.mjs <istantanea.json> <uscita.html> ["testo della fascia in alto"]
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const [, , fileDati, fileUscita, fascia = "Anteprima: i tasti non fanno partire nulla."] = process.argv;
if (!fileDati || !fileUscita) { console.error("Uso: node anteprima.mjs <istantanea.json> <uscita.html> [fascia]"); process.exit(2); }
const qui = dirname(fileURLToPath(import.meta.url));
let html = readFileSync(join(qui, "index.html"), "utf8");
const ist = JSON.parse(readFileSync(fileDati, "utf8"));
const dati = {};
for (const [raccolta, docs] of Object.entries(ist)) for (const [id, d] of Object.entries(docs || {})) dati[raccolta + "/" + id] = d;

const GANCIO = "window.claude && window.claude.use ? await window.claude.use(n) : null";
if (html.split(GANCIO).length !== 2) { console.error("Non trovo il punto in cui la pagina prende le capacità: la pagina è cambiata, aggiorna GANCIO."); process.exit(1); }
html = html.replace(GANCIO, "await window.__finto(n)");

const finto = `
(() => {
  const D = JSON.parse(document.getElementById("istantanea").textContent);
  const iscritti = [];
  const avvisa = () => setTimeout(() => iscritti.forEach(f => f()), 0);
  const copia = x => JSON.parse(JSON.stringify(x));
  const istRaccolta = nome => ({ metadata: { fromCache: false }, docs: Object.keys(D).filter(p => p.split("/")[0] === nome).map(p => ({ id: p.split("/")[1], exists: true, data: () => D[p] })) });
  const doc = path => ({
    async get() { const d = D[path]; return { exists: !!d, data: () => d && copia(d) }; },
    async set(d) { D[path] = copia(d); avvisa(); },
    async update(d) { if (!D[path]) throw { code: "invalid_argument" }; Object.assign(D[path], copia(d)); avvisa(); },
    onSnapshot(next) { const f = () => { const d = D[path]; next({ exists: !!d, data: () => d }); }; iscritti.push(f); setTimeout(f, 0); return () => {}; }
  });
  const db = { doc, collection: nome => ({ onSnapshot(next) { const f = () => next(istRaccolta(nome)); iscritti.push(f); setTimeout(f, 0); return () => {}; } }) };
  // Un capo sviluppo finto: prende il clic e lo chiude, senza fare nulla.
  const mcp = { async callTool(_s, _t, input) {
    const path = input && input.text;
    setTimeout(() => { const c = D[path]; if (!c) return; const ora = new Date().toISOString(); c.esito = "in-lavoro"; c.preso = { quando: ora, aggiornato: ora };
      if (c.tipo === "via-piano" && D["meta/piano"]) D["meta/piano"].via = { quando: ora, clic: path }; avvisa(); }, 1500);
    setTimeout(() => { const c = D[path]; if (!c) return; c.esito = "eseguito"; c.nota = "Anteprima: non è partito nulla davvero."; c.chiuso = new Date().toISOString(); avvisa(); }, 7000);
    return {};
  } };
  window.__finto = async n => (n === "db" ? db : n === "mcp" ? mcp : n === "user" ? { can: async () => true } : null);
})();`;

const sicuro = JSON.stringify(dati).replace(/</g, "\\u003c");
const testa = `<div style="position:sticky;top:0;z-index:50;background:#1A1A1A;color:#FFFFFF;font:600 14px/1.4 system-ui,sans-serif;padding:10px 16px;text-align:center" id="fascia-anteprima"></div>
<script type="application/json" id="istantanea">${sicuro}</script>
<script>document.getElementById("fascia-anteprima").textContent = ${JSON.stringify(fascia).replace(/</g, "\\u003c")};${finto}</script>`;
if (html.split("<body>").length !== 2) { console.error("Non trovo <body>."); process.exit(1); }
html = html.replace("<body>", "<body>\n" + testa);
html = html.replace(/<title>[^<]*<\/title>/, "<title>Registro dei lavori - anteprima</title>");
writeFileSync(fileUscita, html);
console.log("Anteprima scritta: " + fileUscita + " (" + html.length + " caratteri, " + Object.keys(dati).length + " documenti)");
