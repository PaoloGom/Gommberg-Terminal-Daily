// L'area riservata della redazione (G-51): gommberg.com/redazione/. Accesso con nome utente e password, sessioni sul
// server (D1), il pannello di controllo e i suoi dati solo dopo l'accesso, la moderazione della Gommunity, la firma
// "Gommberg" con il badge Redazione e la scheda Sicurezza. Gira nello stesso Worker dei lettori: lettori.js gli passa
// le richieste di /redazione e /api/redazione/*. Regole, segreti e procedura: redazione/sito/LETTORI.md (parte "L'area
// riservata").
//
// Credenziali. Le sceglie Paolo e le mette lui tra i segreti del Worker su Cloudflare: REDAZIONE_UTENTE e
// REDAZIONE_PASSWORD (almeno 16 caratteri). Il codice non le scrive mai da nessuna parte. Dalla scheda Sicurezza la
// password si cambia: in D1 resta solo l'impronta della nuova (PBKDF2-SHA256 con sale), mai la password. Chi vince:
// l'ultima cambiata. L'impronta salvata vale finché il segreto REDAZIONE_PASSWORD resta quello di quando è stata
// salvata (lo riconosce da una sua firma); se Paolo cambia il segreto su Cloudflare, vince il segreto e l'impronta si
// cancella. È anche il modo di recuperare una password dimenticata.
//
// Sessioni. Un gettone casuale di 32 byte nel cookie __Host-gtd_sessione (HttpOnly, Secure, SameSite=Strict, Path=/:
// gli script non lo leggono, gli altri siti non lo mandano); in D1 sta solo la sua impronta SHA-256. Con "Resta
// collegato" il cookie dura 90 giorni e la sessione scade dopo 90 giorni senza uso; senza, il cookie sparisce alla
// chiusura del browser e la sessione dopo 12 ore senza uso. Cambiare password, o cambiare il segreto, chiude le altre
// sessioni. Ogni azione che cambia qualcosa vuole lo stesso sito d'origine e il gettone anti-CSRF della sessione.
// Accanto c'è il cookie gtd_red=1, leggibile dagli script e senza segreti: dice solo alle pagine del sito che vale la
// pena chiedere se c'è una sessione (così i lettori non fanno mai quella richiesta).
//
// Tentativi. Per rete (impronta della rete: l'IPv4 intero o i primi 64 bit dell'IPv6, chiaveRete in lettori.js): 5 errori in 24 ore liberi, poi un'attesa che raddoppia a ogni errore (1, 2,
// 4... minuti, al massimo 60). Ogni tentativo si prenota prima di provare la password (una riga "errore" inserita solo se
// nessun altro tentativo della stessa rete è passato nel frattempo): cento richieste insieme non ne provano più di una.
// Nessun blocco per tutto il sito (chiunque lo farebbe scattare chiudendo fuori Paolo): con una password di almeno 16
// caratteri non serve; i tentativi falliti delle ultime 24 ore si vedono nell'area. Utente inesistente e password
// sbagliata danno la stessa risposta, e lo stesso lavoro.
import { prepara, firma, impronta, chiaveRete, sitoDi, pulisciTesto, controllaTesto, chiaveNome, edizione, ultima, iso, prima, LIMITI } from "./lettori.js";

export const AREA = {
  iterazioni: 50000,           // PBKDF2-SHA256: ~6 ms di CPU (piano gratuito: 10 ms per richiesta; il massimo dei Workers è 100.000)
  password_min: 16, password_max: 200, utente_max: 100,
  resta_giorni: 90, breve_ore: 12, rinnovo_min: 60,
  errori_liberi: 5, attesa_max_min: 60,
  accessi_giorni: 30, blocco_rete_giorni: 30,   // 30 giorni: privacy.html promette l'impronta della rete cancellata dopo 30 giorni
  pagina: 50,
};
export const COOKIE = "__Host-gtd_sessione";
export const SPIA = "gtd_red";
export const GOMMBERG = "Gommberg";
const AUTORE_RED = "redazione";              // le impronte dei lettori sono 32 cifre esadecimali: non possono mai coincidere

export const SCHEMA_AREA = [
  `CREATE TABLE IF NOT EXISTS sessioni (id TEXT PRIMARY KEY, csrf TEXT NOT NULL, cred TEXT NOT NULL, creata TEXT NOT NULL,
     usata TEXT NOT NULL, resta INTEGER NOT NULL, dispositivo TEXT, luogo TEXT, ip TEXT)`,
  `CREATE TABLE IF NOT EXISTS accessi (id INTEGER PRIMARY KEY AUTOINCREMENT, quando TEXT NOT NULL, esito TEXT NOT NULL,
     dispositivo TEXT, luogo TEXT, ip TEXT)`,
  `CREATE INDEX IF NOT EXISTS accessi_ip ON accessi (ip, esito, quando)`,
  `CREATE INDEX IF NOT EXISTS accessi_quando ON accessi (esito, quando)`,
  `CREATE TABLE IF NOT EXISTS bloccati (sito TEXT NOT NULL, tipo TEXT NOT NULL, valore TEXT NOT NULL, creato TEXT NOT NULL,
     scade TEXT, commento INTEGER, PRIMARY KEY (sito, tipo, valore))`,
  `CREATE TABLE IF NOT EXISTS discussioni (sito TEXT NOT NULL, ed INTEGER NOT NULL, chiusa TEXT NOT NULL, PRIMARY KEY (sito, ed))`,
];

// ------------------------------------------------------------------ risposte
const SICUREZZA = {
  "cache-control": "no-store, private", "x-content-type-options": "nosniff", "x-frame-options": "DENY",
  "referrer-policy": "no-referrer", "cross-origin-opener-policy": "same-origin", "cross-origin-resource-policy": "same-origin",
  "permissions-policy": "camera=(), microphone=(), geolocation=(), payment=()",
};
function intestazioni(url, extra) {
  const h = new Headers({ ...SICUREZZA, ...extra });
  if (sitoDi(url) === "gommberg") h.set("strict-transport-security", "max-age=31536000");
  return h;
}
const json = (url, dati, stato = 200, extra = {}) => {
  const h = intestazioni(url, { "content-type": "application/json; charset=utf-8" });
  for (const [k, v] of Object.entries(extra)) for (const x of [].concat(v)) h.append(k, x);
  return new Response(JSON.stringify(dati), { status: stato, headers: h });
};
const no = (url, msg, stato = 400) => json(url, { errore: msg }, stato);

// ------------------------------------------------------------------ piccoli strumenti
const enc = (s) => new TextEncoder().encode(s);
const b64u = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const daB64u = (s) => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/")), (ch) => ch.charCodeAt(0));
const esa = (buf) => [...new Uint8Array(buf)].map((x) => x.toString(16).padStart(2, "0")).join("");
const casuale = (n) => { const b = new Uint8Array(n); crypto.getRandomValues(b); return b; };
const sha256 = async (s) => esa(await crypto.subtle.digest("SHA-256", enc(s)));
// confronto a tempo costante tra due stringhe della stessa lunghezza (impronte); lunghezze diverse: falso, senza scorciatoie
export function uguali(a, b) {
  a = String(a); b = String(b);
  let d = a.length ^ b.length;
  for (let i = 0, n = Math.max(a.length, b.length); i < n; i++) d |= (a.charCodeAt(i) | 0) ^ (b.charCodeAt(i) | 0);
  return d === 0;
}
export async function deriva(password, sale, iterazioni) {
  const k = await crypto.subtle.importKey("raw", enc(password), "PBKDF2", false, ["deriveBits"]);
  return new Uint8Array(await crypto.subtle.deriveBits({ name: "PBKDF2", hash: "SHA-256", salt: sale, iterations: iterazioni }, k, 256));
}
export async function improntaPassword(password, iterazioni = AREA.iterazioni) {
  const sale = casuale(16);
  return "pbkdf2-sha256$" + iterazioni + "$" + b64u(sale) + "$" + b64u(await deriva(password, sale, iterazioni));
}
export async function verificaImpronta(password, h) {
  const m = /^pbkdf2-sha256\$(\d{4,6})\$([A-Za-z0-9_-]{16,64})\$([A-Za-z0-9_-]{43})$/.exec(String(h || ""));
  if (!m || +m[1] > 100000) return false;
  return uguali(b64u(await deriva(password, daB64u(m[2]), +m[1])), m[3]);
}
function cookie(request, nome) {
  for (const p of String(request.headers.get("cookie") || "").split(";")) {
    const i = p.indexOf("=");
    if (i > 0 && p.slice(0, i).trim() === nome) return p.slice(i + 1).trim();
  }
  return "";
}
// il dispositivo, in parole: "Chrome su Windows", "Safari su iPhone". Solo per la scheda Sicurezza
export function dispositivo(ua) {
  ua = String(ua || "");
  const os = /iPhone/.test(ua) ? "iPhone" : /iPad/.test(ua) ? "iPad" : /Android/.test(ua) ? "Android" : /Windows/.test(ua) ? "Windows"
    : /Mac OS X|Macintosh/.test(ua) ? "Mac" : /CrOS/.test(ua) ? "ChromeOS" : /Linux/.test(ua) ? "Linux" : "";
  const br = /Edg\//.test(ua) ? "Edge" : /SamsungBrowser/.test(ua) ? "Samsung Internet" : /Firefox\/|FxiOS/.test(ua) ? "Firefox"
    : /OPR\//.test(ua) ? "Opera" : /Chrome\/|CriOS/.test(ua) ? "Chrome" : /Safari\//.test(ua) ? "Safari" : "";
  const tipo = /iPhone|Android.*Mobile|Mobile.*Safari/.test(ua) ? "telefono" : /iPad|Android/.test(ua) ? "tablet" : "pc";
  return { testo: (br || "Programma sconosciuto") + (os ? " su " + os : ""), tipo: br ? tipo : "altro" };
}
const luogo = (request) => { const cf = request.cf || {}; return [cf.city, cf.country].filter(Boolean).join(", ").slice(0, 60) || null; };
const testoBreve = (s, n) => String(s == null ? "" : s).slice(0, n);

// ------------------------------------------------------------------ le credenziali
// La credenziale attiva: l'impronta salvata dall'area, se il segreto è ancora quello di quando è stata salvata;
// altrimenti il segreto. Senza i due segreti (o con una password troppo corta) l'accesso è spento.
async function credenziale(c) {
  const utente = String(c.env.REDAZIONE_UTENTE || ""), segreto = String(c.env.REDAZIONE_PASSWORD || "");
  if (!utente || segreto.length < AREA.password_min) return null;
  const firmaSegreto = await firma(c.cfg.segreto, "segreto:" + utente + "\n" + segreto);
  let rec = null;
  const r = await c.db.prepare("SELECT v FROM config WHERE k = 'password'").first();
  if (r) {
    try { rec = JSON.parse(r.v); } catch (e) { rec = null; }
    if (!rec || !uguali(rec.s || "", firmaSegreto)) {   // il segreto è cambiato dopo: vince lui, l'impronta si cancella
      // e con lei le sessioni di prima (non valgono più: non devono restare in D1 né nei Dispositivi collegati)
      await c.db.batch([c.db.prepare("DELETE FROM config WHERE k = 'password'"), c.db.prepare("DELETE FROM sessioni")]);
      rec = null;
    }
  }
  const versione = (await firma(c.cfg.segreto, "cred:" + (rec ? rec.h : firmaSegreto))).slice(0, 24);
  return { utente, segreto, rec, firmaSegreto, versione };
}
// Nome utente e password: stesso lavoro e stessa risposta se sbaglia il nome, la password o entrambi
async function controllaCredenziali(c, cred, utente, password) {
  const k = c.cfg.segreto;
  const okU = uguali(await firma(k, "u:" + utente), await firma(k, "u:" + cred.utente));
  const okP = cred.rec ? await verificaImpronta(password, cred.rec.h)
    : uguali(await firma(k, "p:" + password), await firma(k, "p:" + cred.segreto));
  return okU && okP;
}

// ------------------------------------------------------------------ sessioni
async function sessione(c) {
  const t = cookie(c.request, COOKIE);
  if (!/^[A-Za-z0-9_-]{43}$/.test(t)) return null;
  const cred = await credenziale(c);
  if (!cred) return null;
  const id = await sha256("sessione:" + t);
  const s = await c.db.prepare("SELECT id, cred, creata, usata, resta, dispositivo, luogo FROM sessioni WHERE id = ?").bind(id).first();
  if (!s) return null;
  // scade dopo la durata senza uso, e comunque dopo la stessa durata dall'accesso (12 ore, o 90 giorni con Resta collegato)
  const durata = s.resta ? AREA.resta_giorni * 86400 : AREA.breve_ore * 3600;
  if (s.usata < prima(durata) || s.creata < prima(durata) || !uguali(s.cred, cred.versione)) {
    await c.db.prepare("DELETE FROM sessioni WHERE id = ?").bind(id).run();
    return null;
  }
  s.rinnova = s.usata < prima(AREA.rinnovo_min * 60);
  if (s.rinnova) await c.db.prepare("UPDATE sessioni SET usata = ? WHERE id = ?").bind(iso(new Date(Date.now())), id).run();
  s.token = t; s.credenziale = cred;
  s.csrf = await gettoneCsrf(c, t);
  return s;
}
// il gettone anti-CSRF si ricava dal gettone di sessione: in D1 non c'è (come il gettone di sessione, di cui c'è solo l'impronta)
const gettoneCsrf = async (c, t) => (await firma(c.cfg.segreto, "csrf:" + t)).slice(0, 32);
function cookieSessione(t, resta, url) {
  const durata = resta ? "; Max-Age=" + AREA.resta_giorni * 86400 : "";
  return [`${COOKIE}=${t}; Path=/; HttpOnly; Secure; SameSite=Strict${durata}`, `${SPIA}=1; Path=/; Secure; SameSite=Strict${durata}`];
}
const cookieVia = () => [`${COOKIE}=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0`, `${SPIA}=; Path=/; Secure; SameSite=Strict; Max-Age=0`];
async function registra(c, esito) {
  const d = dispositivo(c.request.headers.get("user-agent"));
  await c.db.prepare("INSERT INTO accessi (quando, esito, dispositivo, luogo, ip) VALUES (?, ?, ?, ?, ?)")
    .bind(iso(new Date(Date.now())), esito, d.testo + "|" + d.tipo, luogo(c.request), c.ip).run();
}
// Le scritture dell'area: dal sito stesso, con una sessione valida e il suo gettone anti-CSRF
function stessoSito(c) {
  let o = "";
  try { o = new URL(c.request.headers.get("origin") || "").origin; } catch (e) { o = ""; }
  return !!o && o !== "null" && o === c.url.origin;      // l'origine intera: schema, nome e porta
}
// Il corpo di una richiesta, al massimo max byte: si rifiuta prima di leggerlo se la lunghezza dichiarata è troppa, e si
// smette di leggerlo appena supera il limite se non è dichiarata. null = troppo grande.
async function leggiCorpo(request, max) {
  const cl = request.headers.get("content-length");
  if (cl !== null && (!/^\d{1,12}$/.test(cl) || +cl > max)) return null;
  if (!request.body) return "";
  const r = request.body.getReader(), pezzi = [];
  let n = 0;
  for (;;) {
    const { done, value } = await r.read();
    if (done) break;
    n += value.byteLength;
    if (n > max) { try { await r.cancel(); } catch (e) { /* già chiuso */ } return null; }
    pezzi.push(value);
  }
  const tutto = new Uint8Array(n); let i = 0;
  for (const p of pezzi) { tutto.set(p, i); i += p.byteLength; }
  return new TextDecoder().decode(tutto);
}

// ------------------------------------------------------------------ ingresso
// _privato/pannello.js (costruisci.py): i file di pannello/ e PUBBLICI, i file pubblici sotto i percorsi del Worker
let privatoProva = null;
export const usaPrivato = (file, pubblici = []) => { privatoProva = { file, pubblici }; };   // solo per il collaudo: file finti
async function privato() {
  if (privatoProva) return privatoProva;
  try { const m = await import("../../_privato/pannello.js"); return { file: m.default, pubblici: m.PUBBLICI || [] }; } catch (e) { return { file: null, pubblici: [] }; }
}
const NOME_DATI = /^[a-z0-9_-]+\.json$/;

export async function area(request, env, url) {
  try {
    // Prima di aprire il database: ciò che non è dell'area va ai file statici. I file pubblici sotto /redazione/
    // (PUBBLICI) di norma non arrivano nemmeno qui (wrangler.pubblica.json li esclude), ma se arrivassero non devono
    // dipendere da D1. Sulle anteprime e sugli altri indirizzi l'area non c'è.
    const fuori = sitoDi(url) !== "gommberg" && env.AREA_LOCALE !== "si";
    if (!url.pathname.startsWith("/api/")) {
      const nome = url.pathname.slice("/redazione/".length) || "index.html", m = await privato();
      const candidato = url.pathname === "/redazione" || nome === "index.html" || nome === "accesso.html" || NOME_DATI.test(nome);
      if (fuori || m.pubblici.includes(url.pathname) || !candidato || (request.method !== "GET" && request.method !== "HEAD")) return env.ASSETS.fetch(request);
    } else if (fuori) return no(url, "Indirizzo sconosciuto.", 404);
    let cfg;
    try { cfg = await prepara(env); } catch (e) { cfg = await prepara(env); }
    const ip = await impronta(cfg.segreto, "ip", chiaveRete(request.headers.get("cf-connecting-ip") || "locale"));
    const c = { request, env, url, cfg, ip, db: env.DB, sito: sitoDi(url) };
    if (url.pathname.startsWith("/api/")) return await api(c);
    return await pagina(c);
  } catch (e) {
    console.log("redazione: errore", (e && e.stack) || e);
    return no(url, "Servizio non disponibile, riprova tra poco.", 503);
  }
}

// /redazione/: l'area se c'è una sessione, la schermata di accesso se no; /redazione/<file>.json: i dati del pannello
async function pagina(c) {
  const { url, request } = c;
  if (url.pathname === "/redazione") return new Response(null, { status: 301, headers: intestazioni(url, { location: "/redazione/" + url.search }) });
  const nome = url.pathname.slice("/redazione/".length) || "index.html";
  const P = (await privato()).file;
  if (!P) return no(url, "L'area non è disponibile in questa pubblicazione.", 503);
  // stesso lavoro per ogni nome che potrebbe essere un file del pannello: la sessione si controlla sempre, poi un file
  // che c'è ma senza sessione risponde come uno che non c'è (i nomi non si scoprono, nemmeno dai tempi)
  const s = await sessione(c);
  if (nome === "index.html" || nome === "accesso.html") {
    const file = s ? "index.html" : "accesso.html";
    if (!P[file]) return no(url, "Pagina non trovata.", 404);
    const nonce = b64u(casuale(16));
    const corpo = P[file].replace(/<script(?=[\s>])/g, `<script nonce="${nonce}"`);
    const h = intestazioni(url, {
      "content-type": "text/html; charset=utf-8",
      "content-security-policy": `default-src 'none'; script-src 'nonce-${nonce}'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; ` +
        "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; manifest-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
    });
    if (s && s.rinnova) for (const x of cookieSessione(s.token, s.resta, url)) h.append("set-cookie", x);
    return new Response(request.method === "HEAD" ? null : corpo, { status: 200, headers: h });
  }
  if (!s || !Object.prototype.hasOwnProperty.call(P, nome)) return c.env.ASSETS.fetch(request);
  return new Response(request.method === "HEAD" ? null : P[nome], { status: 200, headers: intestazioni(url, { "content-type": "application/json; charset=utf-8" }) });
}

async function api(c) {
  const { request, url } = c;
  const p = url.pathname.replace(/\/+$/, "").split("/").slice(3);      // /api/redazione/<...>
  const metodo = request.method;
  if (metodo !== "GET" && metodo !== "POST") return no(url, "Metodo non ammesso.", 405);
  let corpo = {};
  if (metodo === "POST") {
    if (!stessoSito(c)) return no(url, "Richiesta non ammessa.", 403);
    const testo = await leggiCorpo(request, 8000);
    if (testo === null) return no(url, "Richiesta troppo grande.", 413);
    try { corpo = testo ? JSON.parse(testo) : {}; } catch (e) { return no(url, "Richiesta non valida.", 400); }
    if (!corpo || typeof corpo !== "object" || Array.isArray(corpo)) return no(url, "Richiesta non valida.", 400);
  }
  if (metodo === "POST" && p[0] === "accesso" && p.length === 1) return accesso(c, corpo);
  const s = await sessione(c);
  if (!s) return json(url, { errore: "Accesso richiesto." }, 401, metodo === "POST" && p[0] === "esci" ? { "set-cookie": cookieVia() } : {});
  if (metodo === "POST" && !uguali(String(request.headers.get("x-csrf") || ""), s.csrf)) return no(url, "Richiesta non ammessa: ricarica la pagina.", 403);
  c.s = s;
  const id = /^\d{1,9}$/.test(p[1] || "") ? +p[1] : null;
  if (metodo === "GET") {
    if (p[0] === "sessione" && p.length === 1) return json(url, { utente: GOMMBERG, csrf: s.csrf, resta: !!s.resta }, 200, s.rinnova ? { "set-cookie": cookieSessione(s.token, s.resta, url) } : {});
    if (p[0] === "riepilogo" && p.length === 1) return riepilogo(c);
    if (p[0] === "commenti" && p.length === 1) return elenco(c);
    if (p[0] === "lettore" && p.length === 1) return lettore(c);
    if (p[0] === "discussioni" && p.length === 1) return discussioni(c);
    if (p[0] === "sicurezza" && p.length === 1) return sicurezza(c);
    return no(url, "Indirizzo sconosciuto.", 404);
  }
  if (p[0] === "esci" && p.length === 1) return esci(c, false);
  if (p[0] === "esci-tutti" && p.length === 1) return esci(c, true);
  if (p[0] === "sessioni" && p.length === 3 && /^[0-9a-f]{12}$/.test(p[1]) && p[2] === "esci") return chiudiSessione(c, p[1]);
  if (p[0] === "password" && p[1] === "verifica" && p.length === 2) return verificaPassword(c, corpo);
  if (p[0] === "password" && p.length === 1) return cambiaPassword(c, corpo);
  if (p[0] === "commenti" && p.length === 1) return scriviRedazione(c, corpo);
  if (p[0] === "commenti" && id && p.length === 3) return azione(c, id, p[2], corpo);
  if (p[0] === "lettori" && (p[1] === "blocca" || p[1] === "sblocca") && p.length === 2) return blocca(c, corpo, p[1] === "blocca");
  if (p[0] === "nomi" && p[1] === "libera" && p.length === 2) return liberaNome(c, corpo);
  if (p[0] === "edizioni" && id && (p[2] === "chiudi" || p[2] === "riapri") && p.length === 3) return discussione(c, id, p[2] === "chiudi");
  return no(url, "Indirizzo sconosciuto.", 404);
}

// ------------------------------------------------------------------ accesso, uscita, password
async function accesso(c, corpo) {
  const { url } = c;
  const cred = await credenziale(c);
  if (!cred) return no(url, "L'accesso non è ancora configurato.", 503);
  const utente = typeof corpo.utente === "string" ? corpo.utente : "", password = typeof corpo.password === "string" ? corpo.password : "";
  if (!utente || !password || utente.length > AREA.utente_max || password.length > AREA.password_max) return no(url, "Nome utente o password non corretti.", 401);
  // i tentativi, prima di ogni calcolo: chi aspetta non costa CPU
  const errori = (await c.db.prepare("SELECT quando FROM accessi WHERE ip = ? AND esito = 'errore' AND quando > ? ORDER BY quando DESC LIMIT 60")
    .bind(c.ip, prima(86400)).all()).results || [];
  if (errori.length >= AREA.errori_liberi) {
    const attesa = Math.min(2 ** (errori.length - AREA.errori_liberi), AREA.attesa_max_min) * 60000;
    const resta = Date.parse(errori[0].quando) + attesa - Date.now();
    if (resta > 0) return json(url, { errore: "Troppi tentativi da questa rete: riprova tra " + Math.ceil(resta / 60000) + " " + (Math.ceil(resta / 60000) === 1 ? "minuto" : "minuti") + ".", attesa: Math.ceil(resta / 1000) }, 429);
  }
  // la prenotazione: il conteggio sta dentro l'inserimento, come per i commenti dei lettori (lettori.js)
  const t = b64u(casuale(32)), adesso = iso(new Date(Date.now())), d = dispositivo(c.request.headers.get("user-agent"));
  const pren = await c.db.prepare(`INSERT INTO accessi (quando, esito, dispositivo, luogo, ip) SELECT ?1, 'errore', ?2, ?3, ?4
      WHERE (SELECT COUNT(*) FROM accessi WHERE ip = ?4 AND esito = 'errore' AND quando > ?5) = ?6 RETURNING id`)
    .bind(adesso, d.testo + "|" + d.tipo, luogo(c.request), c.ip, prima(86400), errori.length).first();
  if (!pren) return json(url, { errore: "Un tentativo alla volta: riprova tra qualche secondo.", attesa: 5 }, 429);
  if (!(await controllaCredenziali(c, cred, utente.trim(), password))) return no(url, "Nome utente o password non corretti.", 401);
  await c.db.batch([
    c.db.prepare("DELETE FROM accessi WHERE ip = ? AND esito = 'errore'").bind(c.ip),
    c.db.prepare("INSERT INTO sessioni (id, csrf, cred, creata, usata, resta, dispositivo, luogo, ip) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)")
      .bind(await sha256("sessione:" + t), "-", cred.versione, adesso, adesso, corpo.resta === true ? 1 : 0, d.testo + "|" + d.tipo, luogo(c.request), c.ip),
  ]);
  await registra(c, "ok");
  return json(url, { ok: true }, 200, { "set-cookie": cookieSessione(t, corpo.resta === true, url) });
}

async function esci(c, tutti) {
  if (tutti) await c.db.prepare("DELETE FROM sessioni").run();
  else await c.db.prepare("DELETE FROM sessioni WHERE id = ?").bind(c.s.id).run();
  await registra(c, tutti ? "esci-tutti" : "uscita");
  return json(c.url, { ok: true }, 200, { "set-cookie": cookieVia() });
}
async function chiudiSessione(c, corto) {
  const r = await c.db.prepare("DELETE FROM sessioni WHERE substr(id, 1, 12) = ?").bind(corto).run();
  if (corto === c.s.id.slice(0, 12)) return json(c.url, { ok: true, questa: true }, 200, { "set-cookie": cookieVia() });
  return json(c.url, { ok: true, chiuse: r.meta ? r.meta.changes : 0 });
}

// Il cambio password in due richieste, perché ogni richiesta faccia al massimo una derivazione PBKDF2 (piano gratuito:
// 10 ms di CPU). 1) /password/verifica controlla la password attuale e dà una prova firmata, valida 5 minuti, legata a
// questa sessione, alla credenziale di adesso e alla nuova password (che lì si controlla: lunghezza, diversa dall'attuale).
// 2) /password con la prova scrive l'impronta della nuova; impronta,
// sessioni chiuse e riga degli accessi stanno nello stesso batch di D1: o tutto o niente.
const PROVA_S = 300;
async function prova(c, ts, nuova) { return ts + "." + (await firma(c.cfg.segreto, "password:" + c.s.id + ":" + c.s.credenziale.versione + ":" + ts + ":" + (await sha256("nuova:" + nuova)))).slice(0, 32); }
function regoleNuova(nuova, conferma) {
  if (nuova.length < AREA.password_min) return "La nuova password deve avere almeno " + AREA.password_min + " caratteri.";
  if (nuova.length > AREA.password_max) return "La nuova password è troppo lunga.";
  if (/^\s*$/.test(nuova) || /^(.)\1*$/su.test(nuova)) return "La nuova password non può essere fatta di soli spazi o di un solo carattere ripetuto.";
  if (conferma !== undefined && conferma !== nuova) return "Le due nuove password non sono uguali.";
  return "";
}
async function verificaPassword(c, corpo) {
  const { url } = c, cred = c.s.credenziale;
  const attuale = typeof corpo.attuale === "string" ? corpo.attuale.slice(0, AREA.password_max) : "", nuova = typeof corpo.nuova === "string" ? corpo.nuova : "";
  const sbaglio = regoleNuova(nuova, corpo.conferma);
  if (sbaglio) return no(url, sbaglio);
  if (nuova === attuale) return no(url, "La nuova password deve essere diversa da quella attuale.");
  // anche qui i tentativi contano: chi ha rubato una sessione non prova le password all'infinito
  const errori = await c.db.prepare("SELECT COUNT(*) AS n FROM accessi WHERE ip = ? AND esito = 'errore' AND quando > ?").bind(c.ip, prima(86400)).first();
  if (errori && errori.n >= AREA.errori_liberi) return no(url, "Troppi tentativi sbagliati: riprova più tardi.", 429);
  if (!attuale || !(await controllaCredenziali(c, cred, cred.utente, attuale))) { await registra(c, "errore"); return no(url, "La password attuale non è corretta.", 403); }
  return json(url, { prova: await prova(c, Math.floor(Date.now() / 1000), nuova) });
}
async function cambiaPassword(c, corpo) {
  const { url } = c, cred = c.s.credenziale;
  const nuova = typeof corpo.nuova === "string" ? corpo.nuova : "";
  const sbaglio = regoleNuova(nuova, corpo.conferma);
  if (sbaglio) return no(url, sbaglio);
  const m = /^(\d{10})\.[0-9a-f]{32}$/.exec(String(corpo.prova || ""));
  if (!m || Date.now() / 1000 - +m[1] > PROVA_S || Date.now() / 1000 < +m[1] - 5 || !uguali(await prova(c, +m[1], nuova), corpo.prova))
    return no(url, "Prima conferma la password attuale (o rifallo: sono passati più di 5 minuti).", 403);
  const h = await improntaPassword(nuova);
  const versione = (await firma(c.cfg.segreto, "cred:" + h)).slice(0, 24), d = dispositivo(c.request.headers.get("user-agent"));
  await c.db.batch([
    c.db.prepare("INSERT INTO config (k, v) VALUES ('password', ?1) ON CONFLICT (k) DO UPDATE SET v = ?1").bind(JSON.stringify({ h, s: cred.firmaSegreto, quando: iso(new Date(Date.now())) })),
    c.db.prepare("DELETE FROM sessioni WHERE id != ?").bind(c.s.id),
    c.db.prepare("UPDATE sessioni SET cred = ? WHERE id = ?").bind(versione, c.s.id),
    c.db.prepare("INSERT INTO accessi (quando, esito, dispositivo, luogo, ip) VALUES (?, 'password', ?, ?, ?)").bind(iso(new Date(Date.now())), d.testo + "|" + d.tipo, luogo(c.request), c.ip),
  ]);
  return json(url, { ok: true });
}

// ------------------------------------------------------------------ scheda Sicurezza
async function sicurezza(c) {
  // gli accessi riusciti e le uscite sempre visibili; gli errori raggruppati per rete (50 errori non nascondono nulla)
  const acc = (await c.db.prepare("SELECT quando, esito, dispositivo, luogo, ip FROM accessi WHERE esito != 'errore' AND quando > ? ORDER BY id DESC LIMIT 30")
    .bind(prima(30 * 86400)).all()).results || [];
  const err = (await c.db.prepare(`SELECT ip, COUNT(*) AS n, MIN(quando) AS primo, MAX(quando) AS ultimo, MAX(dispositivo) AS dispositivo, MAX(luogo) AS luogo
      FROM accessi WHERE esito = 'errore' AND quando > ? GROUP BY ip ORDER BY ultimo DESC, MAX(id) DESC LIMIT 20`).bind(prima(30 * 86400)).all()).results || [];
  const ses = (await c.db.prepare("SELECT id, creata, usata, resta, dispositivo, luogo FROM sessioni ORDER BY usata DESC LIMIT 20").all()).results || [];
  const pw = await c.db.prepare("SELECT v FROM config WHERE k = 'password'").first();
  let cambiata = null; try { cambiata = pw ? JSON.parse(pw.v).quando : null; } catch (e) { cambiata = null; }
  const dv = (x) => { const [testo, tipo] = String(x || "|").split("|"); return { testo: testo || "Sconosciuto", tipo: tipo || "altro" }; };
  return json(c.url, {
    accessi: acc.map((a) => ({ quando: a.quando, esito: a.esito, dispositivo: dv(a.dispositivo), luogo: a.luogo, questa_rete: a.ip === c.ip })),
    errori: err.map((e) => ({ n: e.n, primo: e.primo, ultimo: e.ultimo, dispositivo: dv(e.dispositivo), luogo: e.luogo, questa_rete: e.ip === c.ip })),
    tentativi: await tentativi(c),
    sessioni: ses.map((s) => ({ id: s.id.slice(0, 12), questa: s.id === c.s.id, creata: s.creata, usata: s.usata, resta: !!s.resta,
      scade: iso(new Date(Date.parse(s.usata) + (s.resta ? AREA.resta_giorni * 86400000 : AREA.breve_ore * 3600000))), dispositivo: dv(s.dispositivo), luogo: s.luogo })),
    password: { origine: c.s.credenziale.rec ? "area" : "segreto", cambiata, minimo: AREA.password_min },
    regole: { errori_liberi: AREA.errori_liberi, attesa_max_min: AREA.attesa_max_min,
      resta_giorni: AREA.resta_giorni, breve_ore: AREA.breve_ore, iterazioni: AREA.iterazioni },
  });
}

// i tentativi di accesso falliti delle ultime 24 ore, e da quante reti: l'avviso nella Panoramica e in Sicurezza
async function tentativi(c) {
  const r = await c.db.prepare("SELECT COUNT(*) AS n, COUNT(DISTINCT ip) AS reti FROM accessi WHERE esito = 'errore' AND quando > ?").bind(prima(86400)).first() || {};
  return { n: r.n || 0, reti: r.reti || 0 };
}

// ------------------------------------------------------------------ Gommunity: lettura
const DA_GUARDARE = "(c.nascosto < 2 AND c.segnalazioni > 0)";
async function riepilogo(c) {
  const t0 = Date.now();
  const n = await ultima(c.env, c.url);
  const r = await c.db.prepare(`SELECT SUM(${DA_GUARDARE}) AS guardare, SUM(c.nascosto = 1) AS auto,
      SUM(c.ed = ?2) AS oggi FROM commenti c WHERE c.sito = ?1`).bind(c.sito, n).first() || {};
  const v = await c.db.prepare("SELECT SUM(voto = 'toro') AS toro, SUM(voto = 'orso') AS orso FROM voti WHERE sito = ? AND ed = ?").bind(c.sito, n).first() || {};
  const ch = await c.db.prepare("SELECT 1 AS x FROM discussioni WHERE sito = ? AND ed = ?").bind(c.sito, n).first();
  const ms = Date.now() - t0;
  const u = (await c.db.prepare(`SELECT c.nome, c.testo, c.creato, c.redazione, (SELECT v.voto FROM voti v WHERE v.sito = c.sito AND v.ed = c.ed AND v.autore = c.autore) AS voto
      FROM commenti c WHERE c.sito = ? AND c.ed = ? AND c.nascosto = 0 ORDER BY c.id DESC LIMIT 3`).bind(c.sito, n).all()).results || [];
  return json(c.url, { edizione: n, guardare: r.guardare || 0, auto: r.auto || 0, commenti_oggi: r.oggi || 0, voti_oggi: (v.toro || 0) + (v.orso || 0),
    toro: v.toro || 0, orso: v.orso || 0, chiusa: !!ch, database_ms: ms, tentativi: await tentativi(c),
    ultimi: u.map((x) => ({ nome: x.nome, testo: x.testo, quando: x.creato, redazione: !!x.redazione, voto: x.voto || null })) });
}

function filtri(c) {
  const q = c.url.searchParams, dove = ["c.sito = ?"], arg = [c.sito];
  const f = q.get("filtro") || "tutti";
  if (f === "guardare") dove.push(DA_GUARDARE);
  else if (f === "nascosti") dove.push("c.nascosto > 0");
  else if (f === "redazione") dove.push("c.redazione = 1");
  else if (f !== "tutti") return null;
  const ed = q.get("ed");
  if (ed) { if (!/^\d{1,4}$/.test(ed)) return null; dove.push("c.ed = ?"); arg.push(+ed); }
  const testo = String(q.get("q") || "").trim();
  if (testo) {
    if (testo.length > 60) return null;
    const like = "%" + testo.replace(/[\\%_]/g, (x) => "\\" + x) + "%";
    dove.push("(c.nome LIKE ? ESCAPE '\\' OR c.testo LIKE ? ESCAPE '\\')"); arg.push(like, like);
  }
  const id = q.get("id");
  if (id) { if (!/^\d{1,9}$/.test(id)) return null; dove.push("c.id = ?"); arg.push(+id); }
  const da = q.get("da") || "0";
  if (!/^\d{1,6}$/.test(da)) return null;
  return { dove: dove.join(" AND "), arg, da: +da, filtro: f };
}
async function elenco(c) {
  const f = filtri(c);
  if (!f) return no(c.url, "Filtro non valido.");
  const righe = (await c.db.prepare(
    `SELECT c.id, c.ed, c.padre, c.nome, c.testo, c.creato, c.piace, c.segnalazioni, c.nascosto, c.redazione, c.fissato, c.modificato, c.deciso,
            (SELECT v.voto FROM voti v WHERE v.sito = c.sito AND v.ed = c.ed AND v.autore = c.autore) AS voto,
            (SELECT p.nome FROM commenti p WHERE p.id = c.padre) AS padre_nome,
            EXISTS (SELECT 1 FROM bloccati b WHERE b.sito = c.sito AND b.tipo = 'lettore' AND b.valore = c.autore) AS bloccato
       FROM commenti c WHERE ${f.dove} ORDER BY ${DA_GUARDARE} DESC, c.id DESC LIMIT ${AREA.pagina + 1} OFFSET ${f.da}`).bind(...f.arg).all()).results || [];
  const conti = await c.db.prepare(`SELECT COUNT(*) AS tutti, SUM(${DA_GUARDARE}) AS guardare, SUM(c.nascosto > 0) AS nascosti, SUM(c.redazione = 1) AS redazione,
      COUNT(DISTINCT c.ed) AS edizioni FROM commenti c WHERE c.sito = ?`).bind(c.sito).first() || {};
  const ora7 = prima(7 * 86400), ora14 = prima(14 * 86400);
  const k = await c.db.prepare(`SELECT SUM(creato > ?2) AS c7, SUM(creato <= ?2 AND creato > ?3) AS c14,
      COUNT(DISTINCT CASE WHEN creato > ?2 AND redazione = 0 THEN autore END) AS l7,
      COUNT(DISTINCT CASE WHEN creato <= ?2 AND creato > ?3 AND redazione = 0 THEN autore END) AS l14,
      SUM(nascosto = 1) AS auto FROM commenti WHERE sito = ?1`).bind(c.sito, ora7, ora14).first() || {};
  const attese = ((await c.db.prepare("SELECT attesa FROM commenti WHERE sito = ? AND deciso > ? AND attesa IS NOT NULL ORDER BY attesa")
    .bind(c.sito, prima(30 * 86400)).all()).results || []).map((x) => x.attesa);
  const mediana = attese.length ? (attese.length % 2 ? attese[attese.length >> 1] : (attese[attese.length / 2 - 1] + attese[attese.length / 2]) / 2) : null;
  return json(c.url, {
    commenti: righe.slice(0, AREA.pagina).map((r) => ({ id: r.id, ed: r.ed, padre: r.padre || null, padre_nome: r.padre_nome || null, nome: r.nome, testo: r.testo,
      quando: r.creato, piace: r.piace, segnalazioni: r.segnalazioni, stato: r.nascosto === 2 ? "tolto" : r.nascosto === 1 ? "nascosto" : r.segnalazioni > 0 ? "segnalato" : "visibile",
      redazione: !!r.redazione, fissato: r.fissato || null, modificato: r.modificato || null, deciso: r.deciso || null, voto: r.voto || null, bloccato: !!r.bloccato })),
    altri: righe.length > AREA.pagina,
    conti: { tutti: conti.tutti || 0, guardare: conti.guardare || 0, nascosti: conti.nascosti || 0, redazione: conti.redazione || 0, edizioni: conti.edizioni || 0 },
    misure: { commenti_7: k.c7 || 0, commenti_7_prima: k.c14 || 0, lettori_7: k.l7 || 0, lettori_7_prima: k.l14 || 0, auto: k.auto || 0,
      decisione_s: mediana, decisioni: attese.length },
  });
}
async function trovaCommento(c, id) {
  return c.db.prepare("SELECT id, ed, padre, autore, ip, nome, creato, nascosto, segnalazioni, redazione FROM commenti WHERE id = ? AND sito = ?").bind(id, c.sito).first();
}
async function lettore(c) {
  const id = c.url.searchParams.get("commento");
  if (!/^\d{1,9}$/.test(id || "")) return no(c.url, "Commento non valido.");
  const cm = await trovaCommento(c, +id);
  if (!cm) return no(c.url, "Commento non trovato.", 404);
  if (cm.redazione) return json(c.url, { redazione: true, nome: GOMMBERG });
  const r = await c.db.prepare(`SELECT COUNT(*) AS commenti, SUM(segnalazioni > 0) AS segnalati, SUM(nascosto = 2) AS tolti, SUM(piace) AS like,
      MIN(creato) AS primo FROM commenti WHERE sito = ? AND autore = ?`).bind(c.sito, cm.autore).first() || {};
  const nomi = ((await c.db.prepare("SELECT nome, usato FROM nomi WHERE sito = ? AND autore = ? ORDER BY usato DESC").bind(c.sito, cm.autore).all()).results || []);
  const b = await c.db.prepare("SELECT tipo, creato, scade FROM bloccati WHERE sito = ? AND ((tipo = 'lettore' AND valore = ?) OR (tipo = 'ip' AND valore = ?))")
    .bind(c.sito, cm.autore, cm.ip || "-").all();
  return json(c.url, { redazione: false, nome: cm.nome, commenti: r.commenti || 0, segnalati: r.segnalati || 0, tolti: r.tolti || 0, like: r.like || 0,
    primo: r.primo, nomi: nomi.map((x) => ({ nome: x.nome, usato: x.usato })), rete_nota: !!cm.ip,
    bloccato: ((b && b.results) || []).map((x) => ({ tipo: x.tipo, creato: x.creato, scade: x.scade })) });
}
async function discussioni(c) {
  const righe = (await c.db.prepare(`SELECT c.ed, COUNT(*) AS commenti, SUM(c.nascosto > 0) AS nascosti, MAX(c.creato) AS ultimo,
      (SELECT d.chiusa FROM discussioni d WHERE d.sito = c.sito AND d.ed = c.ed) AS chiusa
      FROM commenti c WHERE c.sito = ? GROUP BY c.ed ORDER BY c.ed DESC LIMIT 60`).bind(c.sito).all()).results || [];
  const n = await ultima(c.env, c.url);
  const ch = await c.db.prepare("SELECT ed, chiusa FROM discussioni WHERE sito = ?").bind(c.sito).all();
  const chiuse = new Map(((ch && ch.results) || []).map((x) => [x.ed, x.chiusa]));
  const per = new Map(righe.map((r) => [r.ed, r]));
  if (n && !per.has(n)) righe.unshift({ ed: n, commenti: 0, nascosti: 0, ultimo: null, chiusa: chiuse.get(n) || null });
  const vv = (await c.db.prepare("SELECT ed, SUM(voto = 'toro') AS toro, SUM(voto = 'orso') AS orso FROM voti WHERE sito = ? GROUP BY ed ORDER BY ed DESC LIMIT 60").bind(c.sito).all()).results || [];
  const voti = new Map(vv.map((x) => [x.ed, x]));
  return json(c.url, { ultima: n, edizioni: righe.map((r) => ({ ed: r.ed, commenti: r.commenti, nascosti: r.nascosti || 0, ultimo: r.ultimo, chiusa: r.chiusa || null,
    toro: (voti.get(r.ed) || {}).toro || 0, orso: (voti.get(r.ed) || {}).orso || 0 })) });
}

// ------------------------------------------------------------------ Gommunity: azioni
async function azione(c, id, cosa, corpo) {
  const { url } = c;
  const cm = await trovaCommento(c, id);
  if (!cm) return no(url, "Commento non trovato.", 404);
  const adesso = iso(new Date(Date.now()));
  // da quando aspetta una decisione: la prima segnalazione ancora aperta (per il "tempo di decisione" della scheda)
  const attesa = async () => {
    const r = await c.db.prepare("SELECT MIN(creato) AS t FROM segnalazioni WHERE commento = ?").bind(id).first();
    return r && r.t ? Math.max(0, Math.round((Date.now() - Date.parse(r.t)) / 1000)) : null;
  };
  if (cosa === "togli") {
    const a = await attesa();
    await c.db.prepare("UPDATE commenti SET nascosto = 2, deciso = ?, attesa = COALESCE(?, attesa) WHERE id = ?").bind(adesso, a, id).run();
  } else if (cosa === "rimetti" || cosa === "azzera") {
    // rimettere un commento vuol dire che può restare: le segnalazioni si azzerano, se no alla prossima si nasconderebbe di nuovo
    if (cosa === "rimetti" && cm.nascosto === 0) return no(url, "Il commento è già visibile.", 409);
    const a = await attesa();
    await c.db.batch([
      c.db.prepare("DELETE FROM segnalazioni WHERE commento = ?").bind(id),
      c.db.prepare(`UPDATE commenti SET segnalazioni = 0, nascosto = ${cosa === "rimetti" ? "0" : "CASE WHEN nascosto = 1 THEN 0 ELSE nascosto END"},
                    deciso = ?, attesa = COALESCE(?, attesa) WHERE id = ?`).bind(adesso, a, id),
    ]);
  } else if (cosa === "fissa") {
    if (cm.padre) return no(url, "Si fissano in alto solo i commenti principali, non le risposte.");
    if (cm.nascosto) return no(url, "Un commento nascosto non si fissa in alto.");
    await c.db.prepare("UPDATE commenti SET fissato = ? WHERE id = ?").bind(adesso, id).run();
  } else if (cosa === "sgancia") {
    await c.db.prepare("UPDATE commenti SET fissato = NULL WHERE id = ?").bind(id).run();
  } else if (cosa === "modifica") {
    if (!cm.redazione) return no(url, "I commenti dei lettori si tolgono, non si modificano.", 403);
    const testo = pulisciTesto(testoBreve(corpo.testo, LIMITI.grezzo[1]));
    const sbaglio = controllaTesto(testo);
    if (sbaglio) return no(url, sbaglio);
    await c.db.prepare("UPDATE commenti SET testo = ?, modificato = ? WHERE id = ?").bind(testo, adesso, id).run();
  } else return no(url, "Azione sconosciuta.", 404);
  const r = await c.db.prepare("SELECT nascosto, segnalazioni, fissato, testo, modificato FROM commenti WHERE id = ?").bind(id).first();
  return json(url, { ok: true, id, stato: r.nascosto === 2 ? "tolto" : r.nascosto === 1 ? "nascosto" : r.segnalazioni > 0 ? "segnalato" : "visibile",
    fissato: r.fissato || null, testo: r.testo, modificato: r.modificato || null });
}

// La firma della redazione: sempre "Gommberg", con il badge; nessun nome scelto, nessun gettone (vale la sessione)
async function scriviRedazione(c, corpo) {
  const { url } = c;
  const n = Number.isInteger(corpo.ed) ? corpo.ed : NaN;
  if (!(n >= 1 && n <= 9999)) return no(url, "Edizione non valida.");
  if (!(await edizione(c.env, url, n))) return no(url, "Edizione non trovata.", 404);
  const testo = pulisciTesto(testoBreve(corpo.testo, LIMITI.grezzo[1]));
  const sbaglio = controllaTesto(testo);
  if (sbaglio) return no(url, sbaglio);
  let padre = null;
  if (corpo.padre != null) {
    const p = await c.db.prepare("SELECT id, padre FROM commenti WHERE id = ? AND sito = ? AND ed = ? AND nascosto = 0").bind(+corpo.padre || 0, c.sito, n).first();
    if (!p) return no(url, "Il commento a cui rispondi non c'è più.", 404);
    padre = p.padre || p.id;
  }
  const quando = iso(new Date(Date.now()));
  const r = await c.db.prepare(`INSERT INTO commenti (sito, ed, padre, nome, testo, creato, autore, ip, redazione) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, 1) RETURNING id`)
    .bind(c.sito, n, padre, GOMMBERG, testo, quando, AUTORE_RED).first();
  return json(url, { commento: { id: r.id, padre, nome: GOMMBERG, testo, quando, piace: 0, mio: true, piaciuto: false, segnalato: false, voto: null,
    redazione: true, fissato: null, modificato: null } }, 201);
}

// Bloccare un lettore: il codice del suo browser per sempre (finché non lo si sblocca) e la sua rete fino a 30 giorni dal commento
// (le reti cambiano mano: un blocco per sempre fermerebbe anche chi viene dopo). I commenti già scritti restano.
async function blocca(c, corpo, si) {
  const { url } = c;
  const cm = Number.isInteger(corpo.commento) ? await trovaCommento(c, corpo.commento) : null;
  if (!cm) return no(url, "Commento non trovato.", 404);
  if (cm.redazione) return no(url, "La redazione non si blocca.");
  const adesso = iso(new Date(Date.now()));
  if (si) {
    const q = [c.db.prepare("INSERT OR REPLACE INTO bloccati (sito, tipo, valore, creato, scade, commento) VALUES (?, 'lettore', ?, ?, NULL, ?)").bind(c.sito, cm.autore, adesso, cm.id)];
    // la rete scade 30 giorni dopo il commento: l'impronta della rete non resta oltre i 30 giorni promessi da privacy.html
    const scade = Date.parse(cm.creato) + AREA.blocco_rete_giorni * 86400000;
    if (cm.ip && scade > Date.now()) q.push(c.db.prepare("INSERT OR REPLACE INTO bloccati (sito, tipo, valore, creato, scade, commento) VALUES (?, 'ip', ?, ?, ?, ?)")
      .bind(c.sito, cm.ip, adesso, iso(new Date(scade)), cm.id));
    await c.db.batch(q);
  } else {
    await c.db.prepare("DELETE FROM bloccati WHERE sito = ? AND ((tipo = 'lettore' AND valore = ?) OR (tipo = 'ip' AND valore = ?))").bind(c.sito, cm.autore, cm.ip || "-").run();
  }
  return json(url, { ok: true, bloccato: si, rete: si && !!cm.ip && Date.parse(cm.creato) + AREA.blocco_rete_giorni * 86400000 > Date.now() });
}
// Liberare un nome: torna disponibile per tutti (per esempio dopo aver tolto i commenti di chi lo usava)
async function liberaNome(c, corpo) {
  const { url } = c;
  const cm = Number.isInteger(corpo.commento) ? await trovaCommento(c, corpo.commento) : null;
  if (!cm || cm.redazione) return no(url, "Commento non trovato.", 404);
  const nome = typeof corpo.nome === "string" ? corpo.nome.slice(0, 200) : "";
  const r = nome
    ? await c.db.prepare("DELETE FROM nomi WHERE sito = ? AND autore = ? AND chiave = ?").bind(c.sito, cm.autore, chiaveNome(nome)).run()
    : await c.db.prepare("DELETE FROM nomi WHERE sito = ? AND autore = ?").bind(c.sito, cm.autore).run();
  return json(url, { ok: true, liberati: r.meta ? r.meta.changes : 0 });
}
async function discussione(c, n, chiudi) {
  if (chiudi) await c.db.prepare("INSERT OR IGNORE INTO discussioni (sito, ed, chiusa) VALUES (?, ?, ?)").bind(c.sito, n, iso(new Date(Date.now()))).run();
  else await c.db.prepare("DELETE FROM discussioni WHERE sito = ? AND ed = ?").bind(c.sito, n).run();
  return json(c.url, { ok: true, ed: n, chiusa: chiudi });
}

// ------------------------------------------------------------------ per i lettori (lettori.js)
export async function bloccato(c) {
  const r = await c.db.prepare(`SELECT 1 AS x FROM bloccati WHERE sito = ?1 AND ((tipo = 'lettore' AND valore = ?2) OR (tipo = 'ip' AND valore = ?3 AND (scade IS NULL OR scade > ?4))) LIMIT 1`)
    .bind(c.sito, c.autore || "-", c.ip, iso(new Date(Date.now()))).first();
  return !!r;
}
export async function chiusa(c, n) {
  return !!(await c.db.prepare("SELECT 1 AS x FROM discussioni WHERE sito = ? AND ed = ?").bind(c.sito, n).first());
}
// la pulizia di ogni giorno (in lettori.js): accessi oltre i 90 giorni, sessioni scadute, blocchi di rete finiti
export function puliziaArea(db) {
  return [
    db.prepare("DELETE FROM accessi WHERE quando < ?").bind(prima(AREA.accessi_giorni * 86400)),
    db.prepare("DELETE FROM sessioni WHERE usata < ?").bind(prima(AREA.resta_giorni * 86400)),
    db.prepare("DELETE FROM bloccati WHERE scade IS NOT NULL AND scade < ?").bind(iso(new Date(Date.now()))),
  ];
}
