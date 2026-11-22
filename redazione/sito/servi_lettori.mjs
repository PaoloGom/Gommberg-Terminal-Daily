// Il sito in locale con il servizio dei lettori vero: i file statici di una cartella (quella che prepara costruisci.py)
// e, per /api/*, lo stesso lettori.js che gira su Cloudflare, con il database finto di d1_finto.mjs.
// Serve a provare e fotografare La Gommunity senza pubblicare nulla:
//   python3 redazione/sito/costruisci.py /tmp/_sito --anteprima
//   node --no-warnings redazione/sito/servi_lettori.mjs /tmp/_sito [porta] [file.sqlite]
// Senza il file il database sta in memoria e si svuota alla chiusura. Scrive come sito = "prova", come le anteprime.
import http from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { d1 } from "./d1_finto.mjs";
import worker from "./lettori.js";

const [cartella, porta = "8787", file = ":memory:"] = process.argv.slice(2);
if (!cartella) { console.log("Uso: node servi_lettori.mjs <cartella del sito> [porta] [file.sqlite]"); process.exit(2); }
const radice = path.resolve(cartella);
const TIPI = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8",
               ".svg": "image/svg+xml", ".png": "image/png", ".pdf": "application/pdf", ".xml": "application/xml; charset=utf-8", ".txt": "text/plain; charset=utf-8" };

async function statico(url) {
  let p = decodeURIComponent(url.pathname); if (p.endsWith("/")) p += "index.html";
  const f = path.join(radice, p);
  if (!f.startsWith(radice + path.sep)) return new Response("fuori dalla cartella", { status: 403 });
  try { return new Response(await readFile(f), { headers: { "content-type": TIPI[path.extname(f)] || "application/octet-stream" } }); }
  catch (e) { return new Response("non trovata", { status: 404 }); }
}
const env = { DB: d1(file), ASSETS: { fetch: (req) => statico(new URL(req.url)) } };

http.createServer(async (req, res) => {
  const pezzi = []; for await (const c of req) pezzi.push(c);
  const corpo = Buffer.concat(pezzi), h = new Headers();
  for (const [k, v] of Object.entries(req.headers)) if (typeof v === "string") h.set(k, v);
  const r = await worker.fetch(new Request("http://" + req.headers.host + req.url, { method: req.method, headers: h, body: corpo.length ? corpo : undefined }), env);
  res.writeHead(r.status, Object.fromEntries(r.headers)); res.end(Buffer.from(await r.arrayBuffer()));
}).listen(+porta, "127.0.0.1", () => console.log("Sito con il servizio dei lettori su http://127.0.0.1:" + porta + "/"));
