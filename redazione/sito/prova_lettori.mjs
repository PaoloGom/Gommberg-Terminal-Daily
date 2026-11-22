// Collaudo del servizio dei lettori (redazione/sito/lettori.js) senza Cloudflare e senza rete: il codice vero, con un
// database D1 finto sopra SQLite di Node (node:sqlite, Node 22.5 o più) e un'edizione finta al posto dei file statici.
// Lo lancia redazione/collaudo.py; da solo: node redazione/sito/prova_lettori.mjs. Esce con 1 al primo errore.
import { DatabaseSync } from "node:sqlite";
import worker, { controllaTesto, pulisciTesto, LIMITI } from "./lettori.js";

// ------------------------------------------------------------- D1 finto: prepare/bind/first/all/run/batch
function d1() {
  const db = new DatabaseSync(":memory:");
  const stmt = (sql, arg = []) => ({
    bind: (...a) => stmt(sql, a),
    _esegui() { const s = db.prepare(sql); return /^\s*(select|with)|returning/i.test(sql) ? { rows: s.all(...arg) } : { info: s.run(...arg) }; },
    async first() { const r = this._esegui().rows; return r && r.length ? { ...r[0] } : null; },
    async all() { return { results: (this._esegui().rows || []).map((r) => ({ ...r })) }; },
    async run() { this._esegui(); return { success: true }; },
  });
  return { prepare: (sql) => stmt(sql), batch: async (lista) => { db.exec("BEGIN"); try { const r = lista.map((s) => s._esegui()); db.exec("COMMIT"); return r; } catch (e) { db.exec("ROLLBACK"); throw e; } }, _db: db };
}

// ------------------------------------------------------------- orologio finto, edizioni finte
let adesso = Date.parse("2026-11-23T09:00:00Z");
Date.now = () => adesso;
const avanti = (s) => { adesso += s * 1000; };
const EDIZIONI = {
  30: { numero: 30, data: "2026-11-20" },
  31: { numero: 31, data: "2026-11-23" },   // la più recente: il sentiment si vota qui
};
const env = {
  DB: d1(),
  ASSETS: { fetch: async (req) => {
    const u = new URL(req.url), m = /^\/e\/(\d{3})\.json$/.exec(u.pathname);
    if (m && EDIZIONI[+m[1]]) return new Response(JSON.stringify(EDIZIONI[+m[1]]), { headers: { "content-type": "application/json" } });
    if (u.pathname === "/dati/recenti.json") return new Response(JSON.stringify({ totale: 31, edizioni: [{ numero: 31 }, { numero: 30 }] }));
    return new Response(m ? "non trovata" : "statico", { status: m ? 404 : 200 });
  } },
};

let ok = 0, ko = 0;
function verifica(nome, cond, dettaglio) {
  if (cond) { ok++; return; }
  ko++; console.log("NO  " + nome + (dettaglio !== undefined ? ": " + JSON.stringify(dettaglio) : ""));
}
const BASE = "https://gommberg.com";
async function chiama(metodo, percorso, { corpo, lettore = "lettore-aaaaaaaaaaaaaaaa", ip = "1.1.1.1", origine = BASE, base = BASE } = {}) {
  const h = { "x-lettore": lettore, "cf-connecting-ip": ip };
  if (origine) h.origin = origine;
  if (corpo) h["content-type"] = "application/json";
  const r = await worker.fetch(new Request(base + percorso, { method: metodo, headers: h, body: corpo ? JSON.stringify(corpo) : undefined }), env);
  let j = null; try { j = await r.clone().json(); } catch (e) { j = await r.text(); }
  return { s: r.status, j };
}

// ------------------------------------------------------------- 1. lettura e file statici
let r = await chiama("GET", "/index.html");
verifica("le pagine non /api/ vanno ai file statici", r.s === 200 && r.j === "statico", r);
r = await chiama("GET", "/api/lettori/030");
verifica("lettura dell'edizione", r.s === 200 && Array.isArray(r.j.commenti) && /^\d{10}\.[0-9a-f]{24}$/.test(r.j.gettone), r);
verifica("sentiment chiuso su un'edizione passata", r.j.voto && r.j.voto.aperto === false, r.j.voto);
const g0 = r.j.gettone;
r = await chiama("GET", "/api/lettori/099");
verifica("edizione inesistente: 404", r.s === 404, r);
r = await chiama("GET", "/api/altro");
verifica("indirizzo sconosciuto: 404", r.s === 404, r);

// ------------------------------------------------------------- 2. difese
const testo = (x) => ({ nome: "Giulia T.", testo: x, gettone: g0 });
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: testo("Troppo presto") });
verifica("gettone di meno di 3 secondi: rifiutato", r.s === 400, r);
avanti(5);
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: testo("Senza origine"), origine: null });
verifica("senza origine: rifiutato", r.s === 403, r);
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: testo("Da un altro sito"), origine: "https://altro.example" });
verifica("da un altro sito: rifiutato", r.s === 403, r);
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: testo("Lettore finto"), lettore: "x" });
verifica("lettore non riconoscibile: rifiutato", r.s === 400, r);
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: { ...testo("Gettone falso"), gettone: "1795000000.000000000000000000000000" } });
verifica("gettone falso: rifiutato", r.s === 400, r);
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: { ...testo("Sono un programma"), sito: "https://spam.example" } });
verifica("campo trappola: risposta finta, nulla salvato", r.s === 200 && r.j.ok === true, r);
for (const [nome, atteso] of [["Redazione", "riservato"], ["Gommberg fan", "riservato"], ["P.Gommellini", "riservato"], ["G", "caratteri"], ["x".repeat(25), "caratteri"]]) {
  r = await chiama("POST", "/api/lettori/031/commenti", { corpo: { nome, testo: "Ciao", gettone: g0 } });
  verifica("nome " + JSON.stringify(nome) + " rifiutato", r.s === 400 && r.j.errore.includes(atteso), r);
}
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: testo("   \n  ") });
verifica("testo vuoto: rifiutato", r.s === 400, r);
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: testo("a".repeat(LIMITI.testo + 1)) });
verifica("testo troppo lungo: rifiutato", r.s === 400, r);
verifica("tre link: rifiutato", !!controllaTesto("vedi https://a.it e www.b.com e c.net/x"), null);
verifica("due link: ammesso", !controllaTesto("vedi https://a.it e www.b.com"), null);
verifica("testo ripulito", pulisciTesto(" a​\r\n\n\n\nb \u0007 ") === "a\n\nb", pulisciTesto(" a​\r\n\n\n\nb \u0007 "));
r = await chiama("GET", "/api/lettori/031");
verifica("nessun commento salvato dai tentativi rifiutati", r.j.commenti.length === 0, r.j.commenti);

// ------------------------------------------------------------- 3. commenti e risposte
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: testo("Sei sedute in rosso: oggi scende.\n\n\n\nSecondo me.") });
verifica("commento pubblicato subito", r.s === 201 && r.j.commento.id && r.j.commento.mio === true && r.j.commento.testo === "Sei sedute in rosso: oggi scende.\n\nSecondo me.", r);
const c1 = r.j.commento.id;
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: testo("Sei sedute in rosso: oggi scende.\n\nSecondo me.") });
verifica("stesso commento due volte: rifiutato", r.s === 429, r);
const B = { lettore: "lettore-bbbbbbbbbbbbbbbb", ip: "2.2.2.2" };
r = await chiama("POST", "/api/lettori/031/commenti", { ...B, corpo: { nome: "Luca R.", testo: "Non sono d'accordo", padre: c1, gettone: g0 } });
verifica("risposta", r.s === 201 && r.j.commento.padre === c1, r);
const c2 = r.j.commento.id;
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: { ...testo("@Luca R. perché?"), padre: c2 } });
verifica("risposta a una risposta: va sotto il commento principale (un livello)", r.s === 201 && r.j.commento.padre === c1, r);
r = await chiama("POST", "/api/lettori/030/commenti", { corpo: { ...testo("Altra edizione"), padre: c1 } });
verifica("risposta a un commento di un'altra edizione: rifiutata", r.s === 404, r);
r = await chiama("GET", "/api/lettori/031", B);
verifica("lettura: tre commenti, il mio riconosciuto", r.j.commenti.length === 3 && r.j.commenti.filter((x) => x.mio).length === 1 && r.j.commenti[1].mio, r.j.commenti);
verifica("lettura: nessun dato tecnico esce", !JSON.stringify(r.j).match(/"(ip|autore|segnalazioni)"/), r.j);

// ------------------------------------------------------------- 4. like
r = await chiama("POST", "/api/lettori/commenti/" + c1 + "/piace", { ...B, corpo: { gettone: g0 } });
verifica("like", r.s === 200 && r.j.piace === 1 && r.j.piaciuto === true, r);
r = await chiama("POST", "/api/lettori/commenti/" + c1 + "/piace", { ...B, corpo: { gettone: g0 } });
verifica("like tolto con il secondo tocco", r.j.piace === 0 && r.j.piaciuto === false, r);
await chiama("POST", "/api/lettori/commenti/" + c1 + "/piace", { ...B, corpo: { gettone: g0 } });
r = await chiama("GET", "/api/lettori/031", B);
verifica("like ricordato al lettore", r.j.commenti.find((x) => x.id === c1).piaciuto === true && r.j.commenti.find((x) => x.id === c1).piace === 1, r.j.commenti);

// ------------------------------------------------------------- 5. sentiment Toro/Orso (si vota sull'edizione più recente, tutto il giorno)
r = await chiama("POST", "/api/lettori/031/voto", { corpo: { voto: "toro", gettone: g0 } });
verifica("voto Toro", r.s === 200 && r.j.voto.toro === 1 && r.j.voto.mio === "toro" && r.j.voto.aperto, r);
r = await chiama("POST", "/api/lettori/031/voto", { corpo: { voto: "orso", gettone: g0 } });
verifica("cambio voto: Orso, un voto solo", r.j.voto.toro === 0 && r.j.voto.orso === 1 && r.j.voto.mio === "orso", r);
await chiama("POST", "/api/lettori/031/voto", { ...B, corpo: { voto: "toro", gettone: g0 } });
r = await chiama("GET", "/api/lettori/031");
verifica("targhetta del sentiment accanto al nome", r.j.commenti.find((x) => x.id === c1).voto === "orso" && r.j.commenti.find((x) => x.id === c2).voto === "toro", r.j.commenti);
verifica("lettori di oggi: chi ha votato o scritto, una volta sola", r.j.lettori === 2, r.j.lettori);
r = await chiama("POST", "/api/lettori/031/voto", { corpo: { voto: "lupo", gettone: g0 } });
verifica("voto non valido", r.s === 400, r);
r = await chiama("POST", "/api/lettori/030/voto", { corpo: { voto: "toro", gettone: g0 } });
verifica("edizione passata: niente voto", r.s === 409, r);
adesso = Date.parse("2026-11-23T22:31:00Z");
const g1 = (await chiama("GET", "/api/lettori/031")).j.gettone; avanti(5);
r = await chiama("POST", "/api/lettori/031/voto", { corpo: { voto: "orso", gettone: g1 } });
verifica("la sera il sentiment è ancora aperto", r.s === 200 && r.j.voto.aperto, r);
r = await chiama("GET", "/api/lettori/031");
verifica("i risultati restano", r.j.voto.toro === 1 && r.j.voto.orso === 1, r.j.voto);

// ------------------------------------------------------------- 6. segnalazioni
r = await chiama("POST", "/api/lettori/commenti/" + c1 + "/segnala", { corpo: { gettone: g1 } });
verifica("non si segnala un proprio commento", r.s === 400, r);
for (const [i, ip] of [["c", "3.3.3.3"], ["d", "3.3.3.3"], ["e", "4.4.4.4"]]) {
  r = await chiama("POST", "/api/lettori/commenti/" + c2 + "/segnala", { lettore: "lettore-" + i.repeat(16), ip, corpo: { gettone: g1 } });
}
r = await chiama("GET", "/api/lettori/031");
verifica("tre segnalazioni da due reti: il commento resta", r.j.commenti.some((x) => x.id === c2), r.j.commenti);
r = await chiama("POST", "/api/lettori/commenti/" + c2 + "/segnala", { lettore: "lettore-ffffffffffffffff", ip: "5.5.5.5", corpo: { gettone: g1 } });
verifica("terza rete: nascosto", r.j.nascosto === true, r);
r = await chiama("GET", "/api/lettori/031");
verifica("il commento nascosto non esce più", !r.j.commenti.some((x) => x.id === c2), r.j.commenti);

// ------------------------------------------------------------- 7. anteprime separate
r = await chiama("GET", "/api/lettori/031", { base: "https://anteprima-g13-gommberg.esempio.workers.dev", origine: null });
verifica("l'anteprima non vede i commenti di gommberg.com", r.s === 200 && r.j.commenti.length === 0, r.j);
r = await chiama("GET", "/api/lettori/030", { base: "https://anteprima-g13-gommberg.esempio.workers.dev", origine: null });
verifica("nell'anteprima il sentiment si vota anche sulle edizioni passate", r.j.voto && r.j.voto.aperto === true, r.j.voto);

// ------------------------------------------------------------- 8. limiti di frequenza
const C = { lettore: "lettore-gggggggggggggggg", ip: "6.6.6.6" };
let ultimo = 0;
for (let i = 0; i < LIMITI.commenti_10min + 1; i++) ultimo = (await chiama("POST", "/api/lettori/031/commenti", { ...C, corpo: { nome: "Veloce", testo: "Commento " + i, gettone: g1 } })).s;
verifica("troppi commenti in 10 minuti: fermato", ultimo === 429, ultimo);
avanti(601);
r = await chiama("POST", "/api/lettori/031/commenti", { ...C, corpo: { nome: "Veloce", testo: "Dopo la pausa", gettone: g1 } });
verifica("dopo 10 minuti si riscrive", r.s === 201, r);

// ------------------------------------------------------------- 9. impronte IP cancellate dopo 30 giorni
env.DB._db.exec("UPDATE commenti SET creato = '2026-10-01T00:00:00Z'");
const vecchio = Math.random; Math.random = () => 0;
await chiama("POST", "/api/lettori/031/commenti", { ...C, corpo: { nome: "Veloce", testo: "Per la pulizia", gettone: g1 } });
Math.random = vecchio;
const restano = env.DB._db.prepare("SELECT COUNT(*) AS n FROM commenti WHERE ip IS NOT NULL AND creato < '2026-10-24'").get().n;
verifica("impronte IP oltre i 30 giorni cancellate", restano === 0, restano);

console.log(ko ? `Lettori: ${ko} NO su ${ok + ko} prove` : `Lettori: ${ok} prove superate`);
process.exit(ko ? 1 : 0);
