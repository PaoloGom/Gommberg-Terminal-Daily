// La Gommunity (G-13): il sentiment Toro/Orso, i commenti, le risposte, i like e le segnalazioni di gommberg.com.
// È, con orologio.js (l'orologio dei controlli, G-58: il cron del Worker e /api/orologio), l'unico codice che gira sul
// sito: Cloudflare lo chiama solo per gli indirizzi /api/* (run_worker_first in wrangler.jsonc) e per il cron; tutto il
// resto sono file statici e non passa di qui. Se questo codice si ferma, homepage ed
// edizioni escono lo stesso: la sezione La Gommunity (assets/lettori.js) dice soltanto che la discussione non si carica.
//
// Dati in D1 (binding DB). Le tabelle le crea il codice al primo uso (SCHEMA): nessuna migrazione, nessun permesso in
// più sul token di GitHub. Gli indirizzi di anteprima (workers.dev, locale) scrivono con sito = "prova": nel database
// condiviso non si mescolano mai con quelli di gommberg.com.
//
// Difese che il lettore non vede (Paolo 22/11): gettone firmato dal server (niente invii da programmi che non hanno
// aperto la pagina, né prima di 3 secondi), campo trappola, origine della richiesta, limiti di frequenza per
// impronta dell'indirizzo IP, nomi riservati alla redazione, nomi unici (un nome resta di chi l'ha usato per primo),
// al massimo due link (che il sito non rende cliccabili), Segnala che nasconde un commento dopo 3 segnalazioni da
// indirizzi diversi. Le segnalazioni aperte escono, senza testi, da /api/lettori/segnalazioni: le legge ogni tre ore
// .github/workflows/segnalazioni.yml (lanciato dall'orologio), che avvisa Paolo.
// La redazione (G-51, redazione.js) toglie, rimette, fissa e blocca dalla scheda Gommunity di gommberg.com/redazione/,
// e scrive come "Gommberg" con il badge Redazione: nascosto = 2 è tolto dalla redazione, 1 nascosto dalle segnalazioni.
// Regole e procedura: redazione/sito/LETTORI.md.

import { giro, stato } from "./orologio.js";
import { area, SCHEMA_AREA, bloccato, chiusa, puliziaArea } from "./redazione.js";

export const LIMITI = {
  nome: [2, 24], testo: 600, link: 2,
  commenti_10min: 6, commenti_giorno: 40,          // per lettore e per impronta IP
  commenti_ip_10min: 12,                           // un ufficio dietro lo stesso indirizzo: più largo
  like_ora: 200, segnala_giorno: 5, voti_ip_ed: 30,  // 5 segnalazioni al giorno per rete: ognuna diventa un avviso a Paolo
  grezzo: [200, 5000],                             // nome e testo più lunghi di così non si guardano nemmeno
  segnalazioni_per_nascondere: 3,
  gettone_min_s: 3, gettone_max_s: 12 * 3600,
  ip_giorni: 30,                                   // dopo, l'impronta IP si cancella
  nomi_per_lettore: 3,                             // nomi che un lettore tiene per sé
  nome_cambio_giorni: 30,                          // per prenderne un quarto, uno dei tre deve essere fermo da un mese
  nome_giorni: 180,                                // un nome non più usato torna libero
  segnalazioni_giorni: 14,                         // per quanto una segnalazione resta nell'elenco degli avvisi
};
// Nomi unici (Paolo 22/11): un nome resta di chi l'ha usato per primo, riconosciuto dal codice anonimo del suo browser.
// Nessuno può firmarsi con il nome di un altro, nemmeno cambiando maiuscole, accenti, spazi o punteggiatura.
// false = spento: ognuno firma come vuole, come prima.
export const NOMI_UNICI = true;
export const RISERVATI = /redazion|redatt|gommberg|gommellini|amministra|admin|moderat|staff|direttore|direzion/i;

const SCHEMA = [
  `CREATE TABLE IF NOT EXISTS commenti (id INTEGER PRIMARY KEY AUTOINCREMENT, sito TEXT NOT NULL, ed INTEGER NOT NULL,
     padre INTEGER, nome TEXT NOT NULL, testo TEXT NOT NULL, creato TEXT NOT NULL, autore TEXT NOT NULL, ip TEXT,
     piace INTEGER NOT NULL DEFAULT 0, segnalazioni INTEGER NOT NULL DEFAULT 0, nascosto INTEGER NOT NULL DEFAULT 0,
     redazione INTEGER NOT NULL DEFAULT 0, fissato TEXT, modificato TEXT, deciso TEXT, attesa INTEGER)`,
  `CREATE INDEX IF NOT EXISTS commenti_ed ON commenti (sito, ed)`,
  `CREATE INDEX IF NOT EXISTS commenti_ip ON commenti (ip, creato)`,
  `CREATE TABLE IF NOT EXISTS piaciuti (commento INTEGER NOT NULL, autore TEXT NOT NULL, ip TEXT, creato TEXT NOT NULL,
     PRIMARY KEY (commento, autore))`,
  `CREATE TABLE IF NOT EXISTS segnalazioni (commento INTEGER NOT NULL, autore TEXT NOT NULL, ip TEXT, creato TEXT NOT NULL,
     PRIMARY KEY (commento, autore))`,
  `CREATE TABLE IF NOT EXISTS voti (sito TEXT NOT NULL, ed INTEGER NOT NULL, autore TEXT NOT NULL, voto TEXT NOT NULL,
     ip TEXT, creato TEXT NOT NULL, PRIMARY KEY (sito, ed, autore))`,
  `CREATE TABLE IF NOT EXISTS config (k TEXT PRIMARY KEY, v TEXT NOT NULL)`,
  `CREATE TABLE IF NOT EXISTS nomi (sito TEXT NOT NULL, chiave TEXT NOT NULL, nome TEXT NOT NULL, autore TEXT NOT NULL,
     creato TEXT NOT NULL, usato TEXT NOT NULL, PRIMARY KEY (sito, chiave))`,
  `CREATE INDEX IF NOT EXISTS nomi_autore ON nomi (sito, autore, usato)`,
  ...SCHEMA_AREA,
];
// Le colonne aggiunte dopo la nascita della tabella (G-51): sul database già in linea si aggiungono una volta sola
// (versione 2 dello schema in config). Su un database nuovo ci sono già: l'errore "duplicate column" non conta.
const COLONNE_2 = ["redazione INTEGER NOT NULL DEFAULT 0", "fissato TEXT", "modificato TEXT", "deciso TEXT", "attesa INTEGER"];

const JSON_H = { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", "x-content-type-options": "nosniff" };
const risposta = (dati, stato = 200) => new Response(JSON.stringify(dati), { status: stato, headers: JSON_H });
const errore = (msg, stato = 400) => risposta({ errore: msg }, stato);
const ora = () => new Date(Date.now());
export const iso = (d) => d.toISOString().replace(/\.\d{3}Z$/, "Z");
export const prima = (secondi) => iso(new Date(Date.now() - secondi * 1000));

let pronto = null;                                  // schema e segreto, una volta per istanza
export const nuovaIstanza = () => { pronto = null; };   // solo per il collaudo: come un'istanza appena nata, schema da preparare
export async function prepara(env) {
  if (!pronto) pronto = (async () => {
    await env.DB.batch(SCHEMA.map((s) => env.DB.prepare(s)));
    const v = await env.DB.prepare("SELECT v FROM config WHERE k = 'schema'").first();
    if (!v || +v.v < 2) {
      for (const col of COLONNE_2) {
        try { await env.DB.prepare("ALTER TABLE commenti ADD COLUMN " + col).run(); }
        catch (e) { if (!/duplicate column/i.test(String((e && e.message) || e))) throw e; }
      }
      await env.DB.prepare("INSERT INTO config (k, v) VALUES ('schema', '2') ON CONFLICT (k) DO UPDATE SET v = '2'").run();
    }
    let r = await env.DB.prepare("SELECT v FROM config WHERE k = 'segreto'").first();
    if (!r) {
      const b = new Uint8Array(32); crypto.getRandomValues(b);
      await env.DB.prepare("INSERT OR IGNORE INTO config (k, v) VALUES ('segreto', ?)").bind(esa(b)).run();
      r = await env.DB.prepare("SELECT v FROM config WHERE k = 'segreto'").first();
    }
    return { segreto: r.v };
  })().catch((e) => { pronto = null; throw e; });
  return pronto;
}

const esa = (buf) => [...new Uint8Array(buf)].map((x) => x.toString(16).padStart(2, "0")).join("");
export async function firma(segreto, testo) {
  const k = await crypto.subtle.importKey("raw", new TextEncoder().encode(segreto), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return esa(await crypto.subtle.sign("HMAC", k, new TextEncoder().encode(testo)));
}
export const impronta = async (segreto, tipo, valore) => (await firma(segreto, tipo + ":" + valore)).slice(0, 32);

// La rete di chi scrive (G-51): l'IPv4 intero, o i primi 64 bit dell'IPv6. Con IPv6 una casa o un telefono hanno 2^64
// indirizzi nella stessa /64: contare l'indirizzo intero lascerebbe aggirare limiti, attese e blocchi cambiandolo.
// La usano i limiti dei lettori (qui) e l'area riservata (redazione.js). Le impronte già in D1 di indirizzi IPv6 interi
// non coincidono più: i limiti guardano al massimo 24 ore indietro e i blocchi di rete scadono da soli entro 30 giorni.
export function chiaveRete(ip) {
  ip = String(ip == null ? "" : ip).trim().toLowerCase().replace(/%.*$/, "");
  const v4 = /^(?:::ffff:)?(\d{1,3}(?:\.\d{1,3}){3})$/.exec(ip);
  if (v4) return v4[1];
  if (!ip.includes(":")) return ip || "locale";
  const parti = ip.split("::");
  if (parti.length > 2) return ip;
  const a = parti[0] ? parti[0].split(":") : [], b = parti.length === 2 && parti[1] ? parti[1].split(":") : [];
  const gruppi = parti.length === 2 ? [...a, ...Array(Math.max(0, 8 - a.length - b.length)).fill("0"), ...b] : a;
  return gruppi.slice(0, 4).map((g) => (parseInt(g, 16) || 0).toString(16)).join(":") + "::/64";
}

// il sito che scrive: gommberg.com, oppure "prova" per anteprime e prove in locale
export const sitoDi = (url) => /^(www\.)?gommberg\.com\.?$/.test(url.hostname) ? "gommberg" : "prova";

// L'edizione: il server non si fida del browser, controlla che esista la scheda pubblica e/NNN.json
const edizioni = new Map();
export async function edizione(env, url, n) {
  const k = url.host + "/" + n, c = edizioni.get(k);
  if (c && c.t > Date.now() - 300000) return c.ed;
  let ed = null;
  try {
    const r = await env.ASSETS.fetch(new Request(new URL("/e/" + String(n).padStart(3, "0") + ".json", url)));
    if (r.ok) { const j = await r.json(); if (j && j.numero === n && /^\d{4}-\d{2}-\d{2}$/.test(j.data || "")) ed = j; }
  } catch (e) { ed = null; }
  edizioni.set(k, { t: Date.now(), ed });
  return ed;
}

// Il sentiment (Toro/Orso) è quello di oggi: si vota sull'edizione più recente, tutto il giorno, e si può cambiare finché
// non esce l'edizione dopo. Le edizioni precedenti mostrano il loro risultato, senza voto. Nelle anteprime è sempre aperto.
let recente = { t: 0, n: 0 };
export async function ultima(env, url) {
  if (recente.t > Date.now() - 300000) return recente.n;
  try {
    const r = await env.ASSETS.fetch(new Request(new URL("/dati/recenti.json", url)));
    const j = r.ok ? await r.json() : null;
    const n = Math.max(0, ...((j && j.edizioni) || []).map((e) => +e.numero || 0));
    if (n) recente = { t: Date.now(), n };
  } catch (e) { /* resta l'ultimo valore letto */ }
  return recente.n;
}
const aperto = async (c, n) => c.sito === "prova" || n === (await ultima(c.env, c.url));

// ------------------------------------------------------------------ testo dei lettori
export function pulisciNome(s) {
  return String(s == null ? "" : s).normalize("NFC").replace(/[\p{Cc}\p{Cf}\p{Co}\p{Cn}\uFE00-\uFE0F]/gu, "").replace(/\s+/g, " ").trim();
}
export function pulisciTesto(s) {
  return String(s == null ? "" : s).normalize("NFC").replace(/\r\n?/g, "\n")
    .replace(/[\u0000-\u0009\u000b-\u001f\u007f-\u009f\u200b-\u200f\u202a-\u202e\u2066-\u2069]/g, "")
    .replace(/[ \t]*\n/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
}
// Il nome si scrive con lettere (anche accentate), numeri, spazi e poca punteggiatura: niente simboli, emoji o lettere
// di altri alfabeti, che servirebbero solo a scrivere un nome uguale a quello di un altro ("Gıulia" con la i senza punto).
const AMMESSI = /^[A-Za-z0-9 .,'’&?!:+_-]+$/;
const senzaSegni = (s) => String(s).normalize("NFKD").replace(/\p{M}/gu, "");
// La chiave di un nome: ciò che due nomi devono avere di diverso per essere due nomi. Hanno la stessa chiave "Luca R.",
// "luca r", "LÙCA_R" e "Luca  R", e i nomi che all'occhio sono uguali: i, I, elle, uno e ! sono la stessa lettera, lo
// zero è una o, "rn" è una m e "vv" una w ("GiuIia", "Giu1ia", "Marnmola", "VValter").
export function chiaveNome(nome) {
  return senzaSegni(nome).toLowerCase().replace(/ß/g, "ss").replace(/rn/g, "m").replace(/vv/g, "w").replace(/[i1!|]/g, "l").replace(/0/g, "o").replace(/[^a-z0-9]/g, "");
}
const CHIAVI_RISERVATE = RISERVATI.source.split("|").map(chiaveNome);
export function controllaNome(nome) {
  if (nome.length < LIMITI.nome[0] || nome.length > LIMITI.nome[1]) return "Il nome va da " + LIMITI.nome[0] + " a " + LIMITI.nome[1] + " caratteri.";
  if (/\p{M}/u.test(nome) || !AMMESSI.test(senzaSegni(nome))) return "Nel nome usa lettere, numeri e punteggiatura semplice: niente simboli o emoji.";
  const chiave = chiaveNome(nome);
  if (chiave.length < 2) return "Nel nome servono almeno due lettere o numeri.";
  if (RISERVATI.test(nome.replace(/[\s._-]/g, "")) || CHIAVI_RISERVATE.some((r) => chiave.includes(r))) return "Questo nome è riservato alla redazione: scegline un altro.";
  return "";
}
export function controllaTesto(testo) {
  if (!testo) return "Scrivi qualcosa prima di pubblicare.";
  if (testo.length > LIMITI.testo) return "Al massimo " + LIMITI.testo + " caratteri.";
  const link = (testo.match(/\b(?:https?:\/\/|www\.)\S+|\b[a-z0-9-]+\.(?:com|it|eu|net|org|io|ly|me|co|gg|tv|cc|do|dev|app|xyz|ru|info|biz|link|site|online|shop|top|club)\b(?:\/\S*)?/gi) || []).length;
  if (link > LIMITI.link) return "Al massimo " + LIMITI.link + " link per commento.";
  return "";
}

// ------------------------------------------------------------------ richieste
export const OROLOGIO_CACHE_MS = 60000;
let oroCache = { t: 0, dati: null };
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    // l'area riservata (G-51): la pagina /redazione/, i dati del pannello e le azioni della redazione
    if (/^\/redazione(\/|$)|^\/api\/redazione(\/|$)/.test(url.pathname)) return area(request, env, url);
    if (!url.pathname.startsWith("/api/")) return env.ASSETS.fetch(request);
    if (url.pathname.replace(/\/+$/, "") === "/api/orologio") {
      if (request.method !== "GET") return errore("Metodo non ammesso.", 405);
      // non lancia mai: un guasto diventa "sano": false con il motivo. Una lettura di D1 al minuto per istanza al
      // massimo: chi chiamasse di continuo non consuma le letture gratuite che servono ai commenti
      if (!oroCache.dati || Date.now() - oroCache.t > OROLOGIO_CACHE_MS) oroCache = { t: Date.now(), dati: await stato(env) };
      return risposta(oroCache.dati);
    }
    try {
      try { await prepara(env); } catch (e) { await prepara(env); }   // un intoppo del database alla prima richiesta: si riprova una volta
      return await instrada(request, env, url);
    } catch (e) {
      console.log("lettori: errore", e && e.stack || e);
      return errore("Servizio non disponibile, riprova tra poco.", 503);
    }
  },
  // l'orologio dei controlli (G-58): il cron di wrangler.jsonc, ogni quarto d'ora
  async scheduled(controller, env, ctx) {
    ctx.waitUntil(giro(env, controller.scheduledTime));
  },
};

async function instrada(request, env, url) {
  const p = url.pathname.replace(/\/+$/, "").split("/").slice(2);   // ["lettori", ...]
  if (p[0] !== "lettori") return errore("Indirizzo sconosciuto.", 404);
  const metodo = request.method;
  if (metodo !== "GET" && metodo !== "POST") return errore("Metodo non ammesso.", 405);
  const cfg = await prepara(env);
  const sito = sitoDi(url);
  const lettore = String(request.headers.get("x-lettore") || "");
  const autore = /^[a-z0-9-]{16,64}$/i.test(lettore) ? await impronta(cfg.segreto, "lettore", lettore) : "";
  const ip = await impronta(cfg.segreto, "ip", chiaveRete(request.headers.get("cf-connecting-ip") || "locale"));
  const c = { env, url, sito, autore, ip, cfg, db: env.DB };
  await pulizia(c);

  if (metodo === "GET") {
    if (/^\d{1,4}$/.test(p[1] || "") && p.length === 2) return leggi(c, +p[1]);
    if (p[1] === "nome" && p.length === 2) { const nn = url.searchParams.getAll("n"); return nn.length > 1 ? nomiLiberi(c, nn) : nomeLibero(c, nn[0]); }
    if (p[1] === "segnalazioni" && p.length === 2) return segnalazioni(c);
    return errore("Indirizzo sconosciuto.", 404);
  }
  // scritture: dalla pagina del sito stesso, con un lettore riconoscibile e un gettone valido
  let origine = "";
  try { origine = new URL(request.headers.get("origin") || "").origin; } catch (e) { origine = ""; }
  if (!origine || origine !== url.origin) return errore("Richiesta non ammessa.", 403);   // l'origine intera, schema compreso
  if (!autore) return errore("Ricarica la pagina e riprova.", 400);
  let corpo = {};
  try { corpo = await request.json(); } catch (e) { return errore("Richiesta non valida.", 400); }
  if (!corpo || typeof corpo !== "object" || Array.isArray(corpo)) return errore("Richiesta non valida.", 400);
  if (!(await gettoneValido(cfg.segreto, corpo.gettone))) return errore("Ricarica la pagina e riprova.", 400);
  if (corpo.sito) return risposta({ ok: true });                    // campo trappola riempito: un programma, non una persona
  if (await bloccato(c)) return errore("Da qui non si può più partecipare alla Gommunity.", 403);   // bloccato dalla redazione (G-51)

  if (/^\d{1,4}$/.test(p[1] || "") && p[2] === "commenti" && p.length === 3) return scrivi(c, +p[1], corpo);
  if (/^\d{1,4}$/.test(p[1] || "") && p[2] === "voto" && p.length === 3) return vota(c, +p[1], corpo);
  if (p[1] === "commenti" && /^\d{1,9}$/.test(p[2] || "") && p[3] === "piace" && p.length === 4) return piace(c, +p[2]);
  if (p[1] === "commenti" && /^\d{1,9}$/.test(p[2] || "") && p[3] === "segnala" && p.length === 4) return segnala(c, +p[2]);
  return errore("Indirizzo sconosciuto.", 404);
}

async function gettone(segreto) {
  const t = String(Math.floor(Date.now() / 1000));
  return t + "." + (await firma(segreto, "gettone:" + t)).slice(0, 24);
}
async function gettoneValido(segreto, g) {
  const m = /^(\d{10})\.([0-9a-f]{24})$/.exec(String(g || ""));
  if (!m) return false;
  const eta = Date.now() / 1000 - +m[1];
  if (eta < LIMITI.gettone_min_s || eta > LIMITI.gettone_max_s) return false;
  return (await firma(segreto, "gettone:" + m[1])).slice(0, 24) === m[2];
}

async function conteggio(db, sql, ...arg) { const r = await db.prepare(sql).bind(...arg).first(); return r ? Object.values(r)[0] : 0; }

// Le edizioni di test (PROVA.md, parte B) si pubblicano prima del loro giorno e poi si tolgono: ciò che è stato votato e
// scritto lì non deve ricomparire sotto l'edizione vera, che ha lo stesso numero. Dal giorno dell'edizione in poi, tutto
// ciò che su quel numero porta una data precedente si cancella da solo, alla prima lettura. Finché quel giorno non è
// arrivato non si tocca nulla: chi sta provando vede i suoi commenti. Solo sul sito vero; se non riesce, si legge lo stesso.
const ripulite = new Map();
async function toglieProve(c, n, ed) {
  if (c.sito !== "gommberg" || iso(ora()) < ed.data) return;
  const k = n + "/" + ed.data;
  if (ripulite.get(k) > Date.now() - 300000) return;
  ripulite.set(k, Date.now());
  const vecchi = "SELECT id FROM commenti WHERE sito = ?1 AND ed = ?2 AND creato < ?3";
  try {
    await c.db.batch([
      c.db.prepare(`DELETE FROM piaciuti WHERE commento IN (${vecchi})`).bind(c.sito, n, ed.data),
      c.db.prepare(`DELETE FROM segnalazioni WHERE commento IN (${vecchi})`).bind(c.sito, n, ed.data),
      c.db.prepare("DELETE FROM commenti WHERE sito = ?1 AND ed = ?2 AND creato < ?3").bind(c.sito, n, ed.data),
      c.db.prepare("DELETE FROM voti WHERE sito = ?1 AND ed = ?2 AND creato < ?3").bind(c.sito, n, ed.data),
    ]);
  } catch (e) { ripulite.delete(k); }
}

// ------------------------------------------------------------------ lettura: sentiment e discussione di un'edizione
async function leggi(c, n) {
  const ed = await edizione(c.env, c.url, n);
  if (!ed) return errore("Edizione non trovata.", 404);
  await toglieProve(c, n, ed);
  const out = { n, gettone: await gettone(c.cfg.segreto), voto: await statoVoto(c, n), chiusa: await chiusa(c, n) };
  // "23 lettori oggi": chi ha votato o scritto su questa edizione, contato una volta
  out.lettori = await conteggio(c.db, "SELECT COUNT(*) FROM (SELECT autore FROM voti WHERE sito = ?1 AND ed = ?2 UNION SELECT autore FROM commenti WHERE sito = ?1 AND ed = ?2)", c.sito, n);
  const righe = await c.db.prepare(
    `SELECT c.id, c.padre, c.nome, c.testo, c.creato, c.piace, c.autore = ?2 AS mio, c.redazione, c.fissato, c.modificato,
            EXISTS (SELECT 1 FROM piaciuti p WHERE p.commento = c.id AND p.autore = ?2) AS piaciuto,
            EXISTS (SELECT 1 FROM segnalazioni s WHERE s.commento = c.id AND s.autore = ?2) AS segnalato,
            (SELECT v.voto FROM voti v WHERE v.sito = c.sito AND v.ed = c.ed AND v.autore = c.autore) AS voto
       FROM commenti c WHERE c.sito = ?1 AND c.ed = ?3 AND c.nascosto = 0
        AND (c.padre IS NULL OR EXISTS (SELECT 1 FROM commenti r WHERE r.id = c.padre AND r.nascosto = 0)) ORDER BY c.id LIMIT 1000`)
    .bind(c.sito, c.autore || "-", n).all();
  out.commenti = (righe.results || []).map(pubblico);
  return risposta(out);
}
// redazione: il commento è della redazione (firma "Gommberg" con il badge): lo dice solo il server, nessun lettore lo imita
const pubblico = (r) => ({ id: r.id, padre: r.padre || null, nome: r.nome, testo: r.testo, quando: r.creato, piace: r.piace,
  mio: !!r.mio, piaciuto: !!r.piaciuto, segnalato: !!r.segnalato, voto: r.voto || null,
  redazione: !!r.redazione, fissato: r.fissato || null, modificato: r.modificato || null });

async function totali(c, n) {
  const r = await c.db.prepare("SELECT SUM(voto = 'toro') AS toro, SUM(voto = 'orso') AS orso FROM voti WHERE sito = ? AND ed = ?").bind(c.sito, n).first();
  return { toro: (r && r.toro) || 0, orso: (r && r.orso) || 0 };
}
async function statoVoto(c, n) {
  const t = await totali(c, n);
  const mio = c.autore ? await c.db.prepare("SELECT voto FROM voti WHERE sito = ? AND ed = ? AND autore = ?").bind(c.sito, n, c.autore).first() : null;
  return { ...t, mio: mio ? mio.voto : null, aperto: await aperto(c, n) };
}

// ------------------------------------------------------------------ scrittura
async function limiti(c, condizioni) {
  for (const [sql, arg, max, msg] of condizioni) if ((await conteggio(c.db, sql, ...arg)) >= max) return msg;
  return "";
}
// Una volta al giorno, alla prima richiesta: le impronte IP oltre i 30 giorni si cancellano (lo promette la privacy) e i
// nomi fermi da LIMITI.nome_giorni si tolgono. Il giorno dell'ultima pulizia sta in config: la fa una sola richiesta.
let pulito = "";
async function pulizia(c) {
  const oggi = iso(ora()).slice(0, 10);
  if (pulito === oggi) return;
  const r = await c.db.prepare("SELECT v FROM config WHERE k = 'pulizia'").first();
  if (!r || r.v !== oggi) {
    const lim = prima(LIMITI.ip_giorni * 86400);
    await c.db.batch([
      c.db.prepare("INSERT INTO config (k, v) VALUES ('pulizia', ?1) ON CONFLICT (k) DO UPDATE SET v = ?1").bind(oggi),
      ...["commenti", "piaciuti", "segnalazioni", "voti"].map((t) => c.db.prepare(`UPDATE ${t} SET ip = NULL WHERE ip IS NOT NULL AND creato < ?`).bind(lim)),
      c.db.prepare("DELETE FROM nomi WHERE usato < ?").bind(prima(LIMITI.nome_giorni * 86400)),
      ...puliziaArea(c.db),
    ]);
  }
  pulito = oggi;
}

async function scrivi(c, n, corpo) {
  const ed = await edizione(c.env, c.url, n);
  if (!ed) return errore("Edizione non trovata.", 404);
  if (await chiusa(c, n)) return errore("La discussione di questa edizione è chiusa.", 409);
  if (String(corpo.nome == null ? "" : corpo.nome).length > LIMITI.grezzo[0] || String(corpo.testo == null ? "" : corpo.testo).length > LIMITI.grezzo[1])
    return errore("Al massimo " + LIMITI.testo + " caratteri.");
  const nome = pulisciNome(corpo.nome), testo = pulisciTesto(corpo.testo);
  const sbaglio = controllaNome(nome) || controllaTesto(testo);
  if (sbaglio) return errore(sbaglio);
  let padre = null;
  if (corpo.padre != null) {                         // risposte a un livello: si risponde sempre al commento principale
    const p = await c.db.prepare("SELECT id, padre FROM commenti WHERE id = ? AND sito = ? AND ed = ? AND nascosto = 0").bind(+corpo.padre, c.sito, n).first();
    if (!p) return errore("Il commento a cui rispondi non c'è più.", 404);
    padre = p.padre || p.id;
    if (p.padre && !(await c.db.prepare("SELECT 1 AS x FROM commenti WHERE id = ? AND nascosto = 0").bind(padre).first())) return errore("Il commento a cui rispondi non c'è più.", 404);
  }
  const troppi = "Stai scrivendo molto in fretta: riprova tra qualche minuto.";
  const msg = await limiti(c, [
    ["SELECT COUNT(*) FROM commenti WHERE autore = ? AND creato > ?", [c.autore, prima(600)], LIMITI.commenti_10min, troppi],
    ["SELECT COUNT(*) FROM commenti WHERE ip = ? AND creato > ?", [c.ip, prima(600)], LIMITI.commenti_ip_10min, troppi],
    ["SELECT COUNT(*) FROM commenti WHERE (autore = ? OR ip = ?) AND creato > ?", [c.autore, c.ip, prima(86400)], LIMITI.commenti_giorno, "Per oggi hai scritto tanto: ci rileggiamo domani."],
    ["SELECT COUNT(*) FROM commenti WHERE autore = ? AND testo = ? AND creato > ?", [c.autore, testo, prima(86400)], 1, "Hai già pubblicato questo commento."],
  ]);
  if (msg) return errore(msg, 429);
  if (NOMI_UNICI) { const no = await prendiNome(c, nome); if (no) return errore(no, 409); }
  const quando = iso(ora());
  // i due limiti che contano si ricontrollano dentro l'inserimento: dieci invii nello stesso istante non passano insieme
  const r = await c.db.prepare(
    `INSERT INTO commenti (sito, ed, padre, nome, testo, creato, autore, ip) SELECT ?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8
      WHERE (SELECT COUNT(*) FROM commenti WHERE autore = ?7 AND creato > ?9) < ?10
        AND (SELECT COUNT(*) FROM commenti WHERE autore = ?7 AND testo = ?5 AND creato > ?11) < 1 RETURNING id`)
    .bind(c.sito, n, padre, nome, testo, quando, c.autore, c.ip, prima(600), LIMITI.commenti_10min, prima(86400)).first();
  if (!r) return errore(troppi, 429);
  const voto = await c.db.prepare("SELECT voto FROM voti WHERE sito = ? AND ed = ? AND autore = ?").bind(c.sito, n, c.autore).first();
  return risposta({ commento: { id: r.id, padre, nome, testo, quando, piace: 0, mio: true, piaciuto: false, segnalato: false, voto: voto ? voto.voto : null } }, 201);
}

// ------------------------------------------------------------------ nomi unici
const NOME_PRESO = "Questo nome è già di un altro lettore: scegline un altro, o generane uno con il dado.";
// Di chi è la chiave: un nome che il suo lettore non usa da LIMITI.nome_giorni è di nuovo libero
async function padrone(c, chiave) {
  const r = await c.db.prepare("SELECT autore FROM nomi WHERE sito = ? AND chiave = ? AND usato >= ?").bind(c.sito, chiave, prima(LIMITI.nome_giorni * 86400)).first();
  return r ? r.autore : null;
}
// Prima di pubblicare: il nome diventa (o resta) di chi scrive. Restituisce "" se va bene, altrimenti il messaggio.
async function prendiNome(c, nome) {
  const chiave = chiaveNome(nome), adesso = iso(ora());
  const mio = await c.db.prepare("SELECT 1 AS x FROM nomi WHERE sito = ? AND chiave = ? AND autore = ?").bind(c.sito, chiave, c.autore).first();
  if (!mio) {
    // Un lettore tiene per sé pochi nomi. Per prenderne un altro, uno dei suoi deve essere fermo da un mese: così un
    // nome non passa a un altro lettore mentre nella discussione ci sono ancora i commenti firmati dal primo.
    const miei = (await c.db.prepare("SELECT chiave, nome, usato FROM nomi WHERE sito = ? AND autore = ? ORDER BY usato, creato").bind(c.sito, c.autore).all()).results || [];
    if (miei.length >= LIMITI.nomi_per_lettore) {
      if (miei[0].usato >= prima(LIMITI.nome_cambio_giorni * 86400)) return "Hai già " + miei.length + " nomi: firma con uno di quelli (" + miei.map((m) => m.nome).join(", ") + ").";
      await c.db.prepare("DELETE FROM nomi WHERE sito = ? AND chiave = ? AND autore = ?").bind(c.sito, miei[0].chiave, c.autore).run();
    }
  }
  // Chi arriva per primo lo prende. L'ordine conta quando due lettori lo chiedono nello stesso istante: si toglie il
  // nome scaduto di un altro, si prova a inserire, si rinnova solo se è già proprio, e alla fine si legge di chi è.
  await c.db.batch([
    c.db.prepare("DELETE FROM nomi WHERE sito = ? AND chiave = ? AND autore != ? AND usato < ?").bind(c.sito, chiave, c.autore, prima(LIMITI.nome_giorni * 86400)),
    c.db.prepare("INSERT OR IGNORE INTO nomi (sito, chiave, nome, autore, creato, usato) VALUES (?, ?, ?, ?, ?, ?)").bind(c.sito, chiave, nome, c.autore, adesso, adesso),
    c.db.prepare("UPDATE nomi SET nome = ?, usato = ? WHERE sito = ? AND chiave = ? AND autore = ?").bind(nome, adesso, c.sito, chiave, c.autore),
  ]);
  const r = await c.db.prepare("SELECT autore FROM nomi WHERE sito = ? AND chiave = ?").bind(c.sito, chiave).first();
  return r && r.autore === c.autore ? "" : NOME_PRESO;
}
// La sezione lo chiede mentre il lettore sceglie il nome (o tira il dado), per dirglielo prima che scriva il commento
async function nomeLibero(c, grezzo) {
  if (String(grezzo == null ? "" : grezzo).length > LIMITI.grezzo[0]) return risposta({ libero: false, tuo: false, messaggio: "Il nome va da " + LIMITI.nome[0] + " a " + LIMITI.nome[1] + " caratteri." });
  const nome = pulisciNome(grezzo), sbaglio = controllaNome(nome);
  if (sbaglio) return risposta({ libero: false, tuo: false, messaggio: sbaglio });
  const di = NOMI_UNICI ? await padrone(c, chiaveNome(nome)) : null;
  const tuo = !!di && !!c.autore && di === c.autore;
  return risposta({ libero: !di || tuo, tuo, messaggio: !di || tuo ? "" : NOME_PRESO });
}

// Il dado ne chiede fino a dodici per volta (?n=...&n=...) e riceve quelli che può proporre: validi e non di altri lettori
async function nomiLiberi(c, grezzi) {
  const visti = new Set(), nomi = [];
  for (const g of grezzi.slice(0, 12)) {
    if (String(g).length > LIMITI.grezzo[0]) continue;
    const n = pulisciNome(g), k = chiaveNome(n);
    if (!controllaNome(n) && !visti.has(k)) { visti.add(k); nomi.push(n); }
  }
  if (!nomi.length || !NOMI_UNICI) return risposta({ liberi: nomi });
  const chiavi = nomi.map(chiaveNome);
  const righe = await c.db.prepare(`SELECT chiave FROM nomi WHERE sito = ? AND usato >= ? AND autore != ? AND chiave IN (${chiavi.map(() => "?").join(", ")})`)
    .bind(c.sito, prima(LIMITI.nome_giorni * 86400), c.autore || "-", ...chiavi).all();
  const presi = new Set((righe.results || []).map((r) => r.chiave));
  return risposta({ liberi: nomi.filter((n, i) => !presi.has(chiavi[i])) });
}

async function vota(c, n, corpo) {
  const ed = await edizione(c.env, c.url, n);
  if (!ed) return errore("Edizione non trovata.", 404);
  if (!(await aperto(c, n))) return errore("Il sentiment si vota sull'edizione di oggi.", 409);
  const v = corpo.voto;
  if (v !== "toro" && v !== "orso" && v !== null) return errore("Voto non valido.");
  if (v === null) {
    await c.db.prepare("DELETE FROM voti WHERE sito = ? AND ed = ? AND autore = ?").bind(c.sito, n, c.autore).run();
  } else {
    const gia = await c.db.prepare("SELECT 1 AS x FROM voti WHERE sito = ? AND ed = ? AND autore = ?").bind(c.sito, n, c.autore).first();
    if (!gia && (await conteggio(c.db, "SELECT COUNT(*) FROM voti WHERE sito = ? AND ed = ? AND ip = ?", c.sito, n, c.ip)) >= LIMITI.voti_ip_ed)
      return errore("Da questa rete sono già arrivati molti voti.", 429);
    await c.db.prepare(`INSERT INTO voti (sito, ed, autore, voto, ip, creato) VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT (sito, ed, autore) DO UPDATE SET voto = excluded.voto`).bind(c.sito, n, c.autore, v, c.ip, iso(ora())).run();
  }
  return risposta({ voto: await statoVoto(c, n) });
}

async function commento(c, id) {
  return c.db.prepare("SELECT id, ed, piace, segnalazioni, autore, redazione FROM commenti WHERE id = ? AND sito = ? AND nascosto = 0").bind(id, c.sito).first();
}

async function piace(c, id) {
  const cm = await commento(c, id);
  if (!cm) return errore("Il commento non c'è più.", 404);
  const gia = await c.db.prepare("SELECT 1 AS x FROM piaciuti WHERE commento = ? AND autore = ?").bind(id, c.autore).first();
  // il conto è sempre quello delle righe vere: due tocchi nello stesso istante non lo sballano e non danno errore
  const conta = c.db.prepare("UPDATE commenti SET piace = (SELECT COUNT(*) FROM piaciuti WHERE commento = ?1) WHERE id = ?1").bind(id);
  if (gia) {
    await c.db.batch([c.db.prepare("DELETE FROM piaciuti WHERE commento = ? AND autore = ?").bind(id, c.autore), conta]);
  } else {
    if ((await conteggio(c.db, "SELECT COUNT(*) FROM piaciuti WHERE ip = ? AND creato > ?", c.ip, prima(3600))) >= LIMITI.like_ora)
      return errore("Troppi like in poco tempo: riprova più tardi.", 429);
    await c.db.batch([c.db.prepare("INSERT OR IGNORE INTO piaciuti (commento, autore, ip, creato) VALUES (?, ?, ?, ?)").bind(id, c.autore, c.ip, iso(ora())), conta]);
  }
  const r = await c.db.prepare("SELECT piace FROM commenti WHERE id = ?").bind(id).first();
  return risposta({ piace: r.piace, piaciuto: !gia });
}

async function segnala(c, id) {
  const cm = await commento(c, id);
  if (!cm) return risposta({ ok: true, nascosto: true });
  if (cm.autore === c.autore) return errore("Non puoi segnalare un tuo commento.");
  if (cm.redazione) return risposta({ ok: true, nascosto: false });   // i commenti della redazione non si nascondono con le segnalazioni
  if ((await conteggio(c.db, "SELECT COUNT(*) FROM segnalazioni WHERE ip = ? AND creato > ?", c.ip, prima(86400))) >= LIMITI.segnala_giorno)
    return errore("Hai già segnalato molti commenti oggi.", 429);
  await c.db.prepare("INSERT OR IGNORE INTO segnalazioni (commento, autore, ip, creato) VALUES (?, ?, ?, ?)").bind(id, c.autore, c.ip, iso(ora())).run();
  // si nasconde quando lo segnalano 3 reti diverse: tre lettori dello stesso ufficio contano una volta sola
  const reti = await conteggio(c.db, "SELECT COUNT(DISTINCT COALESCE(ip, autore)) FROM segnalazioni WHERE commento = ?", id);
  const nascosto = reti >= LIMITI.segnalazioni_per_nascondere;
  await c.db.prepare("UPDATE commenti SET segnalazioni = ?, nascosto = CASE WHEN ? THEN MAX(nascosto, 1) ELSE nascosto END WHERE id = ?").bind(reti, nascosto ? 1 : 0, id).run();
  return risposta({ ok: true, nascosto });
}

// ------------------------------------------------------------------ avviso alla redazione
// I commenti segnalati negli ultimi LIMITI.segnalazioni_giorni che la redazione non ha ancora tolto: numero, edizione,
// quante reti l'hanno segnalato e se è già nascosto; prima i nascosti, poi dalla segnalazione più recente. Mai il testo, il nome o chi ha segnalato: l'elenco è pubblico e
// finisce in una segnalazione di GitHub (segnalazioni.yml), dove un commento da togliere non deve essere copiato.
async function segnalazioni(c) {
  const righe = await c.db.prepare(
    `SELECT c.id, c.ed, c.segnalazioni AS reti, c.nascosto, MAX(s.creato) AS ultima
       FROM commenti c JOIN segnalazioni s ON s.commento = c.id
      WHERE c.sito = ? AND c.nascosto < 2 AND s.creato > ? GROUP BY c.id ORDER BY c.nascosto DESC, ultima DESC LIMIT 100`)
    .bind(c.sito, prima(LIMITI.segnalazioni_giorni * 86400)).all();
  return risposta({ sito: c.sito, segnalati: (righe.results || []).map((r) => ({ id: r.id, ed: r.ed, reti: r.reti, nascosto: r.nascosto === 1, ultima: r.ultima })) });
}
