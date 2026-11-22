// La parola ai lettori (G-13): commenti, risposte, like, segnalazioni e la domanda del giorno di gommberg.com.
// È l'unico codice che gira sul sito: Cloudflare lo chiama solo per gli indirizzi /api/* (run_worker_first in
// wrangler.jsonc); tutto il resto sono file statici e non passa di qui. Se questo codice si ferma, homepage ed
// edizioni escono lo stesso: la colonna dei lettori (assets/lettori.js) dice soltanto che la discussione non si carica.
//
// Dati in D1 (binding DB). Le tabelle le crea il codice al primo uso (SCHEMA): nessuna migrazione, nessun permesso in
// più sul token di GitHub. Gli indirizzi di anteprima (workers.dev, locale) scrivono con sito = "prova": nel database
// condiviso non si mescolano mai con quelli di gommberg.com.
//
// Difese che il lettore non vede (Paolo 22/11): gettone firmato dal server (niente invii da programmi che non hanno
// aperto la pagina, né prima di 3 secondi), campo trappola, origine della richiesta, limiti di frequenza per
// impronta dell'indirizzo IP, nomi riservati alla redazione, al massimo due link (che il sito non rende cliccabili),
// Segnala che nasconde un commento dopo 3 segnalazioni da indirizzi diversi.
// Togliere un commento (finché non c'è G-51): da Cloudflare, D1, gommberg-lettori, Console:
//   UPDATE commenti SET nascosto = 2 WHERE id = <numero>;      (2 = tolto dalla redazione, 1 = nascosto dalle segnalazioni)
// Regole e procedura: redazione/sito/LETTORI.md.

export const LIMITI = {
  nome: [2, 24], testo: 600, link: 2,
  commenti_10min: 6, commenti_giorno: 40,          // per lettore e per impronta IP
  commenti_ip_10min: 12,                           // un ufficio dietro lo stesso indirizzo: più largo
  like_ora: 200, segnala_giorno: 30, voti_ip_ed: 30,
  segnalazioni_per_nascondere: 3,
  gettone_min_s: 3, gettone_max_s: 12 * 3600,
  ip_giorni: 30,                                   // dopo, l'impronta IP si cancella
};
export const RISERVATI = /redazion|gommberg|gommellini|amministra|admin|moderat|staff|direttore/i;

const SCHEMA = [
  `CREATE TABLE IF NOT EXISTS commenti (id INTEGER PRIMARY KEY AUTOINCREMENT, sito TEXT NOT NULL, ed INTEGER NOT NULL,
     padre INTEGER, nome TEXT NOT NULL, testo TEXT NOT NULL, creato TEXT NOT NULL, autore TEXT NOT NULL, ip TEXT,
     piace INTEGER NOT NULL DEFAULT 0, segnalazioni INTEGER NOT NULL DEFAULT 0, nascosto INTEGER NOT NULL DEFAULT 0)`,
  `CREATE INDEX IF NOT EXISTS commenti_ed ON commenti (sito, ed)`,
  `CREATE INDEX IF NOT EXISTS commenti_ip ON commenti (ip, creato)`,
  `CREATE TABLE IF NOT EXISTS piaciuti (commento INTEGER NOT NULL, autore TEXT NOT NULL, ip TEXT, creato TEXT NOT NULL,
     PRIMARY KEY (commento, autore))`,
  `CREATE TABLE IF NOT EXISTS segnalazioni (commento INTEGER NOT NULL, autore TEXT NOT NULL, ip TEXT, creato TEXT NOT NULL,
     PRIMARY KEY (commento, autore))`,
  `CREATE TABLE IF NOT EXISTS voti (sito TEXT NOT NULL, ed INTEGER NOT NULL, autore TEXT NOT NULL, voto TEXT NOT NULL,
     ip TEXT, creato TEXT NOT NULL, PRIMARY KEY (sito, ed, autore))`,
  `CREATE TABLE IF NOT EXISTS config (k TEXT PRIMARY KEY, v TEXT NOT NULL)`,
];

const JSON_H = { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", "x-content-type-options": "nosniff" };
const risposta = (dati, stato = 200) => new Response(JSON.stringify(dati), { status: stato, headers: JSON_H });
const errore = (msg, stato = 400) => risposta({ errore: msg }, stato);
const ora = () => new Date(Date.now());
const iso = (d) => d.toISOString().replace(/\.\d{3}Z$/, "Z");
const prima = (secondi) => iso(new Date(Date.now() - secondi * 1000));

let pronto = null;                                  // schema e segreto, una volta per istanza
async function prepara(env) {
  if (!pronto) pronto = (async () => {
    await env.DB.batch(SCHEMA.map((s) => env.DB.prepare(s)));
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
async function firma(segreto, testo) {
  const k = await crypto.subtle.importKey("raw", new TextEncoder().encode(segreto), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return esa(await crypto.subtle.sign("HMAC", k, new TextEncoder().encode(testo)));
}
const impronta = async (segreto, tipo, valore) => (await firma(segreto, tipo + ":" + valore)).slice(0, 32);

// il sito che scrive: gommberg.com, oppure "prova" per anteprime e prove in locale
export const sitoDi = (url) => (url.hostname === "gommberg.com" || url.hostname === "www.gommberg.com") ? "gommberg" : "prova";

// L'edizione: il server non si fida del browser, legge la scheda pubblica e/NNN.json (data e domanda del giorno)
const edizioni = new Map();
async function edizione(env, url, n) {
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

// Il voto si chiude all'apertura di Wall Street (9:30 a New York) del giorno dell'edizione: dopo si vede già la direzione.
// Nelle anteprime resta aperto, così il voto si prova su qualunque edizione.
const aperto = (c, ed) => c.sito === "prova" || ora() < chiusuraVoto(ed.data);
export function chiusuraVoto(data) {
  for (const h of [13, 14]) {                        // 9:30 a New York = 13:30 UTC con l'ora legale, 14:30 senza
    const t = new Date(data + "T" + h + ":30:00Z");
    const p = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", hour: "numeric", minute: "numeric", hourCycle: "h23" }).formatToParts(t);
    const hh = +p.find((x) => x.type === "hour").value, mm = +p.find((x) => x.type === "minute").value;
    if (hh === 9 && mm === 30) return t;
  }
  return new Date(data + "T14:30:00Z");
}

// ------------------------------------------------------------------ testo dei lettori
export function pulisciNome(s) {
  return String(s == null ? "" : s).normalize("NFC").replace(/[\u0000-\u001f\u007f-\u009f​-‏‪-‮⁦-⁩]/g, "").replace(/\s+/g, " ").trim();
}
export function pulisciTesto(s) {
  return String(s == null ? "" : s).normalize("NFC").replace(/\r\n?/g, "\n")
    .replace(/[\u0000-\u0009\u000b-\u001f\u007f-\u009f​-‏‪-‮⁦-⁩]/g, "")
    .replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
}
export function controllaNome(nome) {
  if (nome.length < LIMITI.nome[0] || nome.length > LIMITI.nome[1]) return "Il nome va da " + LIMITI.nome[0] + " a " + LIMITI.nome[1] + " caratteri.";
  if (RISERVATI.test(nome.replace(/[\s._-]/g, ""))) return "Questo nome è riservato alla redazione: scegline un altro.";
  return "";
}
export function controllaTesto(testo) {
  if (!testo) return "Scrivi qualcosa prima di pubblicare.";
  if (testo.length > LIMITI.testo) return "Al massimo " + LIMITI.testo + " caratteri.";
  const link = (testo.match(/\b(?:https?:\/\/|www\.)\S+|\b[a-z0-9-]+\.(?:com|it|net|org|io|ly|me|xyz|ru|info|biz)\b(?:\/\S*)?/gi) || []).length;
  if (link > LIMITI.link) return "Al massimo " + LIMITI.link + " link per commento.";
  return "";
}

// ------------------------------------------------------------------ richieste
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!url.pathname.startsWith("/api/")) return env.ASSETS.fetch(request);
    try {
      return await instrada(request, env, url);
    } catch (e) {
      console.log("lettori: errore", e && e.stack || e);
      return errore("Servizio non disponibile, riprova tra poco.", 503);
    }
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
  const ip = await impronta(cfg.segreto, "ip", request.headers.get("cf-connecting-ip") || "locale");
  const c = { env, url, sito, autore, ip, cfg, db: env.DB };

  if (metodo === "GET") {
    if (/^\d{1,4}$/.test(p[1] || "") && p.length === 2) return leggi(c, +p[1]);
    return errore("Indirizzo sconosciuto.", 404);
  }
  // scritture: dalla pagina del sito stesso, con un lettore riconoscibile e un gettone valido
  const origine = request.headers.get("origin");
  if (!origine || new URL(origine).host !== url.host) return errore("Richiesta non ammessa.", 403);
  if (!autore) return errore("Ricarica la pagina e riprova.", 400);
  let corpo = {};
  try { corpo = await request.json(); } catch (e) { return errore("Richiesta non valida.", 400); }
  if (!(await gettoneValido(cfg.segreto, corpo.gettone))) return errore("Ricarica la pagina e riprova.", 400);
  if (corpo.sito) return risposta({ ok: true });                    // campo trappola riempito: un programma, non una persona

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

// ------------------------------------------------------------------ lettura: domanda, voti e discussione di un'edizione
async function leggi(c, n) {
  const ed = await edizione(c.env, c.url, n);
  if (!ed) return errore("Edizione non trovata.", 404);
  const out = { n, gettone: await gettone(c.cfg.segreto) };
  const q = ed.lettori && ed.lettori.domanda;
  if (q) out.voto = await statoVoto(c, n, ed);
  // il voto dell'edizione precedente, per la verifica sulla chiusura ("Ieri ha vinto il Toro: lo aveva detto il 63%")
  const pr = ed.lettori && ed.lettori.ieri && ed.lettori.ieri.n;
  if (pr) out.ieri = await totali(c, pr);
  const righe = await c.db.prepare(
    `SELECT c.id, c.padre, c.nome, c.testo, c.creato, c.piace, c.autore = ?2 AS mio,
            EXISTS (SELECT 1 FROM piaciuti p WHERE p.commento = c.id AND p.autore = ?2) AS piaciuto,
            EXISTS (SELECT 1 FROM segnalazioni s WHERE s.commento = c.id AND s.autore = ?2) AS segnalato,
            (SELECT v.voto FROM voti v WHERE v.sito = c.sito AND v.ed = c.ed AND v.autore = c.autore) AS voto
       FROM commenti c WHERE c.sito = ?1 AND c.ed = ?3 AND c.nascosto = 0 ORDER BY c.id LIMIT 1000`)
    .bind(c.sito, c.autore || "-", n).all();
  out.commenti = (righe.results || []).map(pubblico);
  return risposta(out);
}
const pubblico = (r) => ({ id: r.id, padre: r.padre || null, nome: r.nome, testo: r.testo, quando: r.creato, piace: r.piace,
  mio: !!r.mio, piaciuto: !!r.piaciuto, segnalato: !!r.segnalato, voto: r.voto || null });

async function totali(c, n) {
  const r = await c.db.prepare("SELECT SUM(voto = 'toro') AS toro, SUM(voto = 'orso') AS orso FROM voti WHERE sito = ? AND ed = ?").bind(c.sito, n).first();
  return { toro: (r && r.toro) || 0, orso: (r && r.orso) || 0 };
}
async function statoVoto(c, n, ed) {
  const t = await totali(c, n);
  const mio = c.autore ? await c.db.prepare("SELECT voto FROM voti WHERE sito = ? AND ed = ? AND autore = ?").bind(c.sito, n, c.autore).first() : null;
  return { ...t, mio: mio ? mio.voto : null, aperto: aperto(c, ed), chiude: iso(chiusuraVoto(ed.data)) };
}

// ------------------------------------------------------------------ scrittura
async function limiti(c, condizioni) {
  for (const [sql, arg, max, msg] of condizioni) if ((await conteggio(c.db, sql, ...arg)) >= max) return msg;
  return "";
}
async function pulizia(c) {                          // ogni tanto: le impronte IP oltre i 30 giorni si cancellano
  if (Math.random() > 0.05) return;
  const lim = prima(LIMITI.ip_giorni * 86400);
  await c.db.batch(["commenti", "piaciuti", "segnalazioni", "voti"].map((t) => c.db.prepare(`UPDATE ${t} SET ip = NULL WHERE ip IS NOT NULL AND creato < ?`).bind(lim)));
}

async function scrivi(c, n, corpo) {
  const ed = await edizione(c.env, c.url, n);
  if (!ed) return errore("Edizione non trovata.", 404);
  const nome = pulisciNome(corpo.nome), testo = pulisciTesto(corpo.testo);
  const sbaglio = controllaNome(nome) || controllaTesto(testo);
  if (sbaglio) return errore(sbaglio);
  let padre = null;
  if (corpo.padre != null) {                         // risposte a un livello: si risponde sempre al commento principale
    const p = await c.db.prepare("SELECT id, padre FROM commenti WHERE id = ? AND sito = ? AND ed = ? AND nascosto = 0").bind(+corpo.padre, c.sito, n).first();
    if (!p) return errore("Il commento a cui rispondi non c'è più.", 404);
    padre = p.padre || p.id;
  }
  const troppi = "Stai scrivendo molto in fretta: riprova tra qualche minuto.";
  const msg = await limiti(c, [
    ["SELECT COUNT(*) FROM commenti WHERE autore = ? AND creato > ?", [c.autore, prima(600)], LIMITI.commenti_10min, troppi],
    ["SELECT COUNT(*) FROM commenti WHERE ip = ? AND creato > ?", [c.ip, prima(600)], LIMITI.commenti_ip_10min, troppi],
    ["SELECT COUNT(*) FROM commenti WHERE (autore = ? OR ip = ?) AND creato > ?", [c.autore, c.ip, prima(86400)], LIMITI.commenti_giorno, "Per oggi hai scritto tanto: ci rileggiamo domani."],
    ["SELECT COUNT(*) FROM commenti WHERE autore = ? AND testo = ? AND creato > ?", [c.autore, testo, prima(86400)], 1, "Hai già pubblicato questo commento."],
  ]);
  if (msg) return errore(msg, 429);
  const quando = iso(ora());
  const r = await c.db.prepare("INSERT INTO commenti (sito, ed, padre, nome, testo, creato, autore, ip) VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id")
    .bind(c.sito, n, padre, nome, testo, quando, c.autore, c.ip).first();
  await pulizia(c);
  const voto = await c.db.prepare("SELECT voto FROM voti WHERE sito = ? AND ed = ? AND autore = ?").bind(c.sito, n, c.autore).first();
  return risposta({ commento: { id: r.id, padre, nome, testo, quando, piace: 0, mio: true, piaciuto: false, segnalato: false, voto: voto ? voto.voto : null } }, 201);
}

async function vota(c, n, corpo) {
  const ed = await edizione(c.env, c.url, n);
  if (!ed || !(ed.lettori && ed.lettori.domanda)) return errore("Per questa edizione non c'è la domanda.", 404);
  if (!aperto(c, ed)) return errore("Il voto si è chiuso all'apertura di Wall Street.", 409);
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
  return risposta({ voto: await statoVoto(c, n, ed) });
}

async function commento(c, id) {
  return c.db.prepare("SELECT id, ed, piace, segnalazioni, autore FROM commenti WHERE id = ? AND sito = ? AND nascosto = 0").bind(id, c.sito).first();
}

async function piace(c, id) {
  const cm = await commento(c, id);
  if (!cm) return errore("Il commento non c'è più.", 404);
  const gia = await c.db.prepare("SELECT 1 AS x FROM piaciuti WHERE commento = ? AND autore = ?").bind(id, c.autore).first();
  if (gia) {
    await c.db.batch([c.db.prepare("DELETE FROM piaciuti WHERE commento = ? AND autore = ?").bind(id, c.autore),
                      c.db.prepare("UPDATE commenti SET piace = MAX(piace - 1, 0) WHERE id = ?").bind(id)]);
  } else {
    if ((await conteggio(c.db, "SELECT COUNT(*) FROM piaciuti WHERE ip = ? AND creato > ?", c.ip, prima(3600))) >= LIMITI.like_ora)
      return errore("Troppi like in poco tempo: riprova più tardi.", 429);
    await c.db.batch([c.db.prepare("INSERT INTO piaciuti (commento, autore, ip, creato) VALUES (?, ?, ?, ?)").bind(id, c.autore, c.ip, iso(ora())),
                      c.db.prepare("UPDATE commenti SET piace = piace + 1 WHERE id = ?").bind(id)]);
  }
  const r = await c.db.prepare("SELECT piace FROM commenti WHERE id = ?").bind(id).first();
  return risposta({ piace: r.piace, piaciuto: !gia });
}

async function segnala(c, id) {
  const cm = await commento(c, id);
  if (!cm) return risposta({ ok: true, nascosto: true });
  if (cm.autore === c.autore) return errore("Non puoi segnalare un tuo commento.");
  if ((await conteggio(c.db, "SELECT COUNT(*) FROM segnalazioni WHERE ip = ? AND creato > ?", c.ip, prima(86400))) >= LIMITI.segnala_giorno)
    return errore("Hai già segnalato molti commenti oggi.", 429);
  await c.db.prepare("INSERT OR IGNORE INTO segnalazioni (commento, autore, ip, creato) VALUES (?, ?, ?, ?)").bind(id, c.autore, c.ip, iso(ora())).run();
  // si nasconde quando lo segnalano 3 reti diverse: tre lettori dello stesso ufficio contano una volta sola
  const reti = await conteggio(c.db, "SELECT COUNT(DISTINCT COALESCE(ip, autore)) FROM segnalazioni WHERE commento = ?", id);
  const nascosto = reti >= LIMITI.segnalazioni_per_nascondere;
  await c.db.prepare("UPDATE commenti SET segnalazioni = ?, nascosto = CASE WHEN ? THEN MAX(nascosto, 1) ELSE nascosto END WHERE id = ?").bind(reti, nascosto ? 1 : 0, id).run();
  return risposta({ ok: true, nascosto });
}
