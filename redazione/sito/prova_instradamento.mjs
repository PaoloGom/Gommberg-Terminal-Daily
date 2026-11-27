// Ciò che passa dal Worker (run_worker_first in wrangler.jsonc) non deve rompere il sito pubblico (G-51): ogni file che
// costruisci.py pubblica sotto quei percorsi (per esempio redazione/glossario.json, che leggono Impara, Numeri e la
// Scommessa) deve rispondere 200, con lo stesso contenuto, passando dal Worker vero. E senza sessione un file del
// pannello risponde come un file che non esiste. Lo lancia redazione/collaudo.py dopo costruisci.py:
//   node redazione/sito/prova_instradamento.mjs <cartella del sito>      (serve _privato/pannello.js, scritto da costruisci.py)
import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import path from "node:path";
import { d1 } from "./d1_finto.mjs";
import servizio from "./servizio.js";

const radice = path.resolve(process.argv[2] || "");
if (!process.argv[2] || !existsSync(path.join(radice, "index.html"))) { console.log("Uso: node prova_instradamento.mjs <cartella del sito>"); process.exit(2); }
const qui = path.dirname(new URL(import.meta.url).pathname);
const cfg = JSON.parse(readFileSync(path.join(qui, "wrangler.jsonc"), "utf8").replace(/^\s*\/\/.*$/gm, ""));
const schemi = cfg.assets.run_worker_first.filter((x) => !x.startsWith("/api/"))
  .map((x) => new RegExp("^" + x.replace(/[.+?^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*") + "$"));
// i file statici come li serve Cloudflare: il file, o 404.html con stato 404
const ASSETS = { fetch: async (req) => {
  const u = new URL(req.url); let p = decodeURIComponent(u.pathname); if (p.endsWith("/")) p += "index.html";
  const f = path.join(radice, p);
  if (f.startsWith(radice + path.sep) && existsSync(f) && statSync(f).isFile()) return new Response(readFileSync(f), { status: 200 });
  return new Response(readFileSync(path.join(radice, "404.html")), { status: 404 });
} };
const env = { DB: d1(), ASSETS };
const tutti = [];
(function giro(d) { for (const x of readdirSync(d)) { const f = path.join(d, x); if (statSync(f).isDirectory()) giro(f); else tutti.push("/" + path.relative(radice, f).split(path.sep).join("/")); } })(radice);
const passano = tutti.filter((u) => schemi.some((r) => r.test(u)));
const male = [];
const chiedi = async (u) => { const r = await servizio.fetch(new Request("https://gommberg.com" + u, { headers: { "cf-connecting-ip": "8.8.8.8" } }), env); return { s: r.status, b: Buffer.from(await r.arrayBuffer()) }; };
for (const u of passano) {
  const r = await chiedi(u);
  if (r.s !== 200 || !r.b.equals(readFileSync(path.join(radice, u)))) male.push(`${u}: ${r.s}${r.s === 200 ? " (contenuto diverso)" : ""}`);
}
// senza sessione un file del pannello e un file inesistente sono indistinguibili
const finto = await chiedi("/redazione/non-esiste-" + Date.now() + ".json");
for (const u of ["/redazione/registro.json", "/redazione/invii.json", "/redazione/taratura.json"]) {
  const r = await chiedi(u);
  if (r.s !== finto.s || !r.b.equals(finto.b)) male.push(`${u} senza sessione: ${r.s}, diverso da un file che non esiste (${finto.s})`);
}
// e nessun file del pannello ha il nome di un file pubblico sotto /redazione/ (lo coprirebbe)
const privato = (await import(path.join(qui, "..", "..", "_privato", "pannello.js"))).default;
for (const n of Object.keys(privato)) if (passano.includes("/redazione/" + n)) male.push(`pannello/${n} ha lo stesso nome di un file pubblico sotto /redazione/`);
for (const x of male) console.log("NO  " + x);
console.log(male.length ? `Instradamento: ${male.length} problemi` : `Instradamento: ${passano.length} file pubblici sotto i percorsi del Worker rispondono 200 passando dal Worker; il pannello senza sessione è indistinguibile da un file che non esiste`);
process.exit(male.length ? 1 : 0);
