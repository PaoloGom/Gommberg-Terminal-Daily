// Nessun valore che viene dal database arriva nell'HTML dell'area riservata senza escape (G-51). Esegue lo script vero di
// pannello/index.html in Node, con un documento finto che registra ogni innerHTML, e risponde a ogni chiamata
// /api/redazione/* e /api/orologio con dati avvelenati: ogni testo è un pezzo di HTML. Visita Panoramica, Gommunity (con
// il menu, la risposta e la modifica aperti) e Sicurezza: se l'HTML scritto contiene il pezzo intatto, un valore è
// passato senza esc(). Non guarda un campo alla volta: vale per tutti, anche per quelli che verranno.
// Lo lancia redazione/collaudo.py; da solo: node redazione/sito/prova_area_html.mjs
import { readFileSync } from "node:fs";
import path from "node:path";
import vm from "node:vm";

const qui = path.dirname(new URL(import.meta.url).pathname), repo = path.join(qui, "..", "..");
const VELENO = '<b id="veleno">X</b>"\'&';
const SEGNO = '<b id="veleno">';
const v = (x) => VELENO + (x || "");
const html = readFileSync(path.join(repo, "pannello", "index.html"), "utf8");
const script = (html.match(/<script>([\s\S]*?)<\/script>/) || [])[1];
if (!script) { console.log("NO  pannello/index.html: lo script dell'area non si trova"); process.exit(1); }

const commento = (o) => ({ id: 1, ed: 35, padre: null, padre_nome: v(), nome: v("nome"), testo: v("testo"), quando: v(), piace: 1, segnalazioni: 2, stato: v(),
  redazione: false, fissato: v(), modificato: v(), deciso: v(), voto: v(), bloccato: true, ...o });
const API = {
  sessione: { utente: v(), csrf: "c", resta: true },
  riepilogo: { edizione: 35, guardare: 2, auto: 1, commenti_oggi: 3, voti_oggi: 5, toro: 3, orso: 2, chiusa: true, database_ms: 5, tentativi: { n: 3, reti: 2 },
    ultimi: [{ nome: v(), testo: v(), quando: v(), redazione: false, voto: v() }, { nome: v(), testo: v(), quando: v(), redazione: true, voto: null }] },
  discussioni: { ultima: 35, edizioni: [{ ed: 35, commenti: 2, nascosti: 0, ultimo: v(), chiusa: v(), toro: 1, orso: 1 }, { ed: 34, commenti: 1, nascosti: 1, ultimo: v(), chiusa: null, toro: 0, orso: 0 }] },
  commenti: { commenti: [commento({ id: 1, padre: 9 }), commento({ id: 2, stato: "tolto" }), commento({ id: 3, stato: "nascosto" }), commento({ id: 4, stato: "segnalato" }),
    commento({ id: 5, stato: "visibile", redazione: true }), commento({ id: 6, stato: "visibile", bloccato: false })], altri: true,
    conti: { tutti: 6, guardare: 2, nascosti: 2, redazione: 1, edizioni: 2 }, misure: { commenti_7: 4, commenti_7_prima: 2, lettori_7: 3, lettori_7_prima: 1, auto: 1, decisione_s: 4000, decisioni: 2 } },
  lettore: { redazione: false, nome: v(), commenti: 2, segnalati: 1, tolti: 1, like: 3, primo: v(), nomi: [{ nome: v(), usato: v() }], rete_nota: true, bloccato: [{ tipo: v(), creato: v(), scade: v() }] },
  sicurezza: { accessi: [{ quando: v(), esito: v(), dispositivo: { testo: v(), tipo: v() }, luogo: v(), questa_rete: true }, { quando: v(), esito: "ok", dispositivo: { testo: v(), tipo: "pc" }, luogo: v(), questa_rete: false }],
    errori: [{ n: 4, primo: v(), ultimo: v(), dispositivo: { testo: v(), tipo: v() }, luogo: v(), questa_rete: false }], tentativi: { n: 4, reti: 1 },
    sessioni: [{ id: "abcdefabcdef", questa: true, creata: v(), usata: v(), resta: true, scade: v(), dispositivo: { testo: v(), tipo: v() }, luogo: v() }],
    password: { origine: v(), cambiata: v(), minimo: 16 }, regole: { errori_liberi: 5, attesa_max_min: 60, resta_giorni: 90, breve_ore: 12, iterazioni: 50000 } },
};
const OROLOGIO = { sano: false, segreto: true, errore: v(), sveglie: [{ flusso: "mattino.yml", cosa: v(), ok: false, dovuta: v(), esito: { stato: v(), dettaglio: v() } }] };

const scritto = [], uscite = [];
const ascoltatori = { document: {}, window: {} };
function elemento(id) {
  const t = { id, style: {}, dataset: {}, hidden: false, value: "", textContent: "", innerHTML: "",
    classList: { add() {}, remove() {}, contains() { return false; }, toggle() {} } };
  return new Proxy(t, {
    set(o, k, val) { if (k === "innerHTML") scritto.push(String(val)); o[k] = val; return true; },
    get(o, k) {
      if (k in o) return o[k];
      if (k === "querySelectorAll") return () => [];
      if (k === "getBoundingClientRect") return () => ({ width: 900, height: 300, left: 0, right: 900, top: 0 });
      if (["querySelector", "closest", "getAttribute"].includes(k)) return () => null;
      if (k === "contains") return () => false;
      return () => {};
    },
  });
}
const els = {};
const documento = {
  cookie: "", title: "", activeElement: null, body: elemento("body"), head: elemento("head"),
  getElementById: (id) => els[id] || (els[id] = elemento(id)),
  querySelector: () => null, querySelectorAll: () => [], createElement: () => elemento(""),
  addEventListener: (t, f) => { (ascoltatori.document[t] = ascoltatori.document[t] || []).push(f); },
};
const leggiFile = (p) => readFileSync(p, "utf8");
async function fetchFinta(u) {
  u = String(u);
  let corpo = null, stato = 200;
  const m = /\/api\/redazione\/([a-z-]+)/.exec(u);
  if (m) corpo = API[m[1]] || { ok: true };
  else if (u.includes("api/orologio")) corpo = OROLOGIO;
  else if (u.includes("edizioni.json")) corpo = JSON.parse(leggiFile(path.join(repo, "edizioni.json")));
  else { try { corpo = JSON.parse(leggiFile(path.join(repo, "pannello", u.replace(/^.*\//, "").replace(/\?.*$/, "")))); } catch (e) { stato = 404; corpo = {}; } }
  return { ok: stato === 200, status: stato, json: async () => JSON.parse(JSON.stringify(corpo)) };
}
const loc = { hash: "", search: "", pathname: "/redazione/", replace: (x) => uscite.push(x) };
const ctx = {
  document: documento, location: loc, history: { replaceState() {} }, innerWidth: 1440, innerHeight: 1000,
  addEventListener: (t, f) => { (ascoltatori.window[t] = ascoltatori.window[t] || []).push(f); },
  scrollTo() {}, setTimeout, clearTimeout, setInterval: () => 0, fetch: fetchFinta, confirm: () => true, console,
  MouseEvent: class { constructor(t) { this.type = t; } }, requestAnimationFrame: (f) => setTimeout(f, 0),
  matchMedia: () => ({ matches: false }), Date, Math, JSON, Promise, Intl, URL, Number, String, Array, Object, RegExp,
};
ctx.window = ctx; ctx.drawer = documento.getElementById("drawer"); ctx.scrim = documento.getElementById("scrim");
vm.createContext(ctx);
const attendi = () => new Promise((ok) => setTimeout(ok, 30));
async function giro(n = 6) { for (let i = 0; i < n; i++) await attendi(); }
function clic(attr, valori) {
  const bersaglio = { closest: (sel) => (sel === "[" + attr + "]" ? { disabled: false, getAttribute: (k) => (k in valori ? valori[k] : null) } : null) };
  for (const f of ascoltatori.document.click || []) { try { f({ target: bersaglio, preventDefault() {} }); } catch (e) { /* un ascoltatore che non c'entra */ } }
}
async function vai(h) { loc.hash = h; for (const f of ascoltatori.window.hashchange || []) f(); await giro(); }

vm.runInContext(script, ctx, { filename: "pannello/index.html" });
await giro(10);
await vai("#gommunity");
for (const [act, id] of [["menu", "1"], ["menu", "5"], ["rispondi-apri", "1"], ["modifica-apri", "5"]]) { clic("data-ga", { "data-ga": act, "data-id": id, "aria-expanded": "false" }); await giro(3); }
await vai("#sicurezza");
await vai("#panoramica");

const male = [];
const tutto = scritto.join("\n");
if (scritto.length < 10) male.push(`l'area ha scritto poco HTML (${scritto.length} volte): la prova non ha visitato le pagine`);
for (const [nome, chiave] of [["Panoramica", "Edizione di oggi"], ["Gommunity", 'class="cl"'], ["Sicurezza", "Ultimi accessi"], ["menu della Gommunity", 'class="menu"'], ["risposta o modifica", 'id="gtesto"']])
  if (!tutto.includes(chiave)) male.push(`la prova non ha disegnato ${nome}`);
// un testo senza spazi (300 caratteri) va a capo: le regole che lo permettono nel CSS dell'area
const css = (html.match(/<style>([\s\S]*?)<\/style>/) || [])[1] || "";
const regola = (sel) => css.split("}").some((r) => r.includes(sel) && /overflow-wrap:\s*anywhere/.test(r));
if (!regola(".cl .tx") || !regola(".cl .mt b") || !/\.cl>li>div[^{]*\{[^}]*min-width:0/.test(css)) male.push("CSS dell'area: il testo e il nome dei commenti non vanno a capo (overflow-wrap:anywhere e min-width:0)");
let i = tutto.indexOf(SEGNO);
while (i >= 0 && male.length < 6) { male.push("valore senza escape nell'HTML: …" + tutto.slice(Math.max(0, i - 120), i + 40).replace(/\s+/g, " ") + "…"); i = tutto.indexOf(SEGNO, i + 1); }
for (const x of male) console.log("NO  " + x);
console.log(male.length ? `Area: ${male.length} problemi di escape` : `Area: ${scritto.length} pezzi di HTML scritti con dati avvelenati in ogni campo, nessun valore senza escape`);
process.exit(male.length ? 1 : 0);
