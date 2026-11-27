// L'orologio dei controlli (G-58): le Cron Triggers del Worker di gommberg.com fanno partire i flussi di GitHub che
// devono girare a un'ora precisa, con la chiamata workflow_dispatch. Sostituisce le sveglie "schedule" di GitHub, che
// saltano o arrivano ore dopo (23/11: il controllo del mattino non è mai partito da solo).
//
// Un solo cron in wrangler.jsonc ("*/15 * * * *", in UTC): a ogni quarto d'ora questo codice guarda l'ora di ROMA e
// decide lui che cosa è dovuto (SVEGLIE, qui sotto). Così l'ora legale non serve conoscerla nel cron, e i giorni della
// settimana non dipendono da come Cloudflare li numera.
//
// Che cosa serve, tutto fuori dal codice:
//   - il segreto GITHUB_ACTIONS_TOKEN del Worker (Cloudflare, Workers, gommberg, Settings, Variables and Secrets): un
//     token fine-grained di GitHub con il solo permesso Actions "Read and write" su questo repository. Lo mette Paolo,
//     nessuno lo vede; i deploy non lo cancellano mai. Questo codice non lo stampa e non lo scrive da nessuna parte.
//   - la variabile GITHUB_REPOSITORY ("proprietario/nome"): la passa sito.yml a ogni pubblicazione da main con
//     --var GITHUB_REPOSITORY:${{ github.repository }}. È l'unico posto del nome: se il repository cambia nome (G-12),
//     la prima pubblicazione dopo il cambio lo aggiorna da sola.
//
// Niente doppie partenze: ogni partenza dovuta ha una riga nella tabella orologio di D1 (chiave = flusso@ora di Roma),
// presa con INSERT OR IGNORE prima di chiamare GitHub. Se GitHub rifiuta o non risponde, la riga resta "errore" e i
// quarti d'ora seguenti riprovano, fino a 3 tentativi entro 45 minuti. I flussi lanciati reggono comunque una partenza
// doppia (concurrency e segnalazioni cercate per titolo): una chiamata scaduta che GitHub aveva in realtà accettato
// non crea doppie segnalazioni né doppie mail.
//
// Il guasto si vede: /api/orologio dice, senza rivelare nulla, se il segreto c'è e com'è andata l'ultima partenza dovuta
// di ogni flusso ("sano"). Lo leggono il controllo del mattino (mattino.py, con redazione/sito/orologio.py) e il pannello.

// I giorni sono quelli di Date.getUTCDay() sull'ora di Roma: 0 domenica ... 6 sabato.
const TUTTI = [0, 1, 2, 3, 4, 5, 6];
export const SVEGLIE = [
  { flusso: "mattino.yml", giorni: [1, 2, 3, 4, 5], ore: [10], minuto: 15, inputs: { orologio: "cloudflare" },
    cosa: "controllo del mattino (edizione non uscita) e GOMM" },
  { flusso: "segnalazioni.yml", giorni: TUTTI, ore: [8, 11, 14, 17, 20, 23], minuto: 15, inputs: { orologio: "cloudflare" },
    cosa: "segnalazioni della Gommunity" },
  { flusso: "dem.yml", giorni: TUTTI, ore: [19], minuto: 30, inputs: { modo: "sincronizza", orologio: "cloudflare" },
    cosa: "mail straordinarie (allineamento con Kit)" },
];
export const QUARTO = 15 * 60000;
export const RECUPERO = 3;                   // quarti d'ora dopo l'ora dovuta in cui si riprova (45 minuti)
export const TENTATIVI = 3;
export const TOLLERANZA = 20 * 60000;        // una partenza si giudica 20 minuti dopo la sua ora
const TIMEOUT = 15000;                       // GitHub che non risponde entro 15 secondi: errore, si riprova

// ------------------------------------------------------------------ l'ora di Roma, senza tabelle dei fusi
// Regola europea: ora legale dall'ultima domenica di marzo all'ultima di ottobre, cambio alle 01:00 UTC.
// Il collaudo la confronta con il fuso Europe/Rome per due anni interi, quarto d'ora per quarto d'ora.
function ultimaDomenica(anno, mese) {        // mese 0-11; l'istante UTC del cambio
  const d = new Date(Date.UTC(anno, mese + 1, 0));
  return Date.UTC(anno, mese, d.getUTCDate() - d.getUTCDay(), 1);
}
export function scartoRoma(ms) {
  const a = new Date(ms).getUTCFullYear();
  return ms >= ultimaDomenica(a, 2) && ms < ultimaDomenica(a, 9) ? 2 : 1;
}
export function aRoma(ms) {
  const d = new Date(ms + scartoRoma(ms) * 3600000);
  return { anno: d.getUTCFullYear(), mese: d.getUTCMonth() + 1, giorno: d.getUTCDate(), ora: d.getUTCHours(), minuto: d.getUTCMinutes(), dow: d.getUTCDay() };
}
export function daRoma(anno, mese, giorno, ora, minuto) {   // ora di Roma -> istante; le sveglie stanno tra le 8 e le 23, mai nell'ora del cambio
  const base = Date.UTC(anno, mese - 1, giorno, ora, minuto);
  for (const s of [2, 1]) if (scartoRoma(base - s * 3600000) === s) return base - s * 3600000;
  return base - 3600000;
}
const due = (n) => String(n).padStart(2, "0");
export const etichetta = (r) => `${r.anno}-${due(r.mese)}-${due(r.giorno)}T${due(r.ora)}:${due(r.minuto)}`;
const iso = (ms) => new Date(ms).toISOString().replace(/\.\d{3}Z$/, "Z");
const tocca = (s, r) => s.giorni.includes(r.dow) && s.ore.includes(r.ora) && s.minuto === r.minuto;

// Le partenze dovute a questo giro: l'ora esatta e le RECUPERO precedenti (per riprovare quelle andate male).
export function dovute(ms) {
  const q = Math.floor(ms / QUARTO) * QUARTO, out = [];
  for (let k = 0; k <= RECUPERO; k++) {
    const r = aRoma(q - k * QUARTO);
    for (const s of SVEGLIE) if (tocca(s, r)) out.push({ sveglia: s, slot: etichetta(r), t: q - k * QUARTO, ritardo: k });
  }
  return out;
}
// L'ultima partenza dovuta di una sveglia prima di un istante (fino a 8 giorni indietro), o null.
export function ultimaDovuta(s, ms) {
  const r = aRoma(ms);
  for (let g = 0; g <= 8; g++) {
    const d = new Date(Date.UTC(r.anno, r.mese - 1, r.giorno - g));
    if (!s.giorni.includes(d.getUTCDay())) continue;
    for (const o of [...s.ore].sort((a, b) => b - a)) {
      const t = daRoma(d.getUTCFullYear(), d.getUTCMonth() + 1, d.getUTCDate(), o, s.minuto);
      if (t <= ms) return { slot: etichetta(aRoma(t)), t };
    }
  }
  return null;
}

// ------------------------------------------------------------------ dati in D1
const SCHEMA = `CREATE TABLE IF NOT EXISTS orologio (chiave TEXT PRIMARY KEY, flusso TEXT, slot TEXT, stato TEXT NOT NULL,
  tentativi INTEGER NOT NULL DEFAULT 0, quando TEXT NOT NULL, dettaglio TEXT NOT NULL DEFAULT '')`;
const pronti = new WeakSet();                // la tabella si crea una volta per istanza e per database
async function schema(db) {
  if (!pronti.has(db)) { await db.prepare(SCHEMA).run(); pronti.add(db); }
}
const cambiate = (r) => Number((r && r.meta && r.meta.changes) || 0);
const haSegreto = (env) => typeof env.GITHUB_ACTIONS_TOKEN === "string" && env.GITHUB_ACTIONS_TOKEN.trim().length > 0;
const repoValido = (env) => /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(env.GITHUB_REPOSITORY || "");

// Prende la partenza (una sola istanza la fa): nuova, oppure da riprovare dopo un errore o un giro rimasto a metà.
async function prendi(db, d, adesso) {
  const chiave = d.sveglia.flusso + "@" + d.slot;
  const r = await db.prepare("INSERT OR IGNORE INTO orologio (chiave, flusso, slot, stato, tentativi, quando, dettaglio) VALUES (?1, ?2, ?3, 'in corso', 1, ?4, '')")
    .bind(chiave, d.sveglia.flusso, d.slot, iso(adesso)).run();
  if (cambiate(r)) return chiave;
  const u = await db.prepare(`UPDATE orologio SET stato = 'in corso', tentativi = tentativi + 1, quando = ?2
    WHERE chiave = ?1 AND tentativi < ?3 AND (stato IN ('errore', 'senza-segreto') OR (stato = 'in corso' AND quando < ?4))`)
    .bind(chiave, iso(adesso), TENTATIVI, iso(adesso - 10 * 60000)).run();
  return cambiate(u) ? chiave : null;
}

// La chiamata a GitHub. Il token va solo nell'intestazione Authorization; nessun log lo contiene.
export async function lancia(env, s, chiama = fetch) {
  if (!haSegreto(env)) return { stato: "senza-segreto", dettaglio: "manca il segreto GITHUB_ACTIONS_TOKEN del Worker" };
  if (!repoValido(env)) return { stato: "errore", dettaglio: "manca la variabile GITHUB_REPOSITORY (la passa sito.yml alla pubblicazione)" };
  try {
    const r = await chiama(`https://api.github.com/repos/${env.GITHUB_REPOSITORY}/actions/workflows/${s.flusso}/dispatches`, {
      method: "POST",
      headers: { authorization: "Bearer " + env.GITHUB_ACTIONS_TOKEN.trim(), accept: "application/vnd.github+json",
                 "x-github-api-version": "2022-11-28", "user-agent": "gommberg-orologio", "content-type": "application/json" },
      body: JSON.stringify({ ref: "main", inputs: s.inputs }),
      signal: AbortSignal.timeout(TIMEOUT),
    });
    if (r.status >= 200 && r.status < 300) return { stato: "ok", dettaglio: "GitHub " + r.status };
    let msg = "";
    try { msg = String((await r.json()).message || ""); } catch (e) { msg = ""; }
    return { stato: "errore", dettaglio: ("GitHub risponde " + r.status + (msg ? ": " + msg : "")).slice(0, 200) };
  } catch (e) {
    return { stato: "errore", dettaglio: "GitHub non risponde (" + ((e && e.name) || "errore") + ")" };
  }
}

// Un giro dell'orologio (il cron, ogni quarto d'ora). Non lancia mai eccezioni: un errore resta scritto nella tabella.
export async function giro(env, ms, chiama = fetch) {
  const fatti = [];
  try {
    const db = env.DB, adesso = Date.now();
    await schema(db);
    if (haSegreto(env)) {
      await db.prepare("INSERT OR IGNORE INTO orologio (chiave, stato, quando) VALUES ('avvio', 'ok', ?1)").bind(iso(adesso)).run();
    }
    await db.prepare("INSERT INTO orologio (chiave, stato, quando) VALUES ('battito', 'ok', ?1) ON CONFLICT (chiave) DO UPDATE SET quando = ?1").bind(iso(adesso)).run();
    const lista = dovute(ms);
    for (const d of lista) {
      const chiave = await prendi(db, d, adesso);
      if (!chiave) continue;
      const e = await lancia(env, d.sveglia, chiama);
      await db.prepare("UPDATE orologio SET stato = ?2, dettaglio = ?3, quando = ?4 WHERE chiave = ?1").bind(chiave, e.stato, e.dettaglio, iso(Date.now())).run();
      fatti.push({ chiave, ...e });
      if (e.stato !== "ok") console.log("orologio: " + chiave + " " + e.stato + " - " + e.dettaglio);
    }
    if (lista.length) await db.prepare("DELETE FROM orologio WHERE slot IS NOT NULL AND quando < ?1").bind(iso(adesso - 14 * 86400000)).run();
  } catch (e) {
    console.log("orologio: giro non riuscito", (e && e.stack) || e);
    fatti.push({ chiave: "giro", stato: "errore", dettaglio: String((e && e.message) || e).slice(0, 200) });
  }
  return fatti;
}

// Lo stato per /api/orologio: niente segreti, niente nomi; "sano" se il segreto c'è, almeno una partenza è riuscita e
// l'ultima partenza dovuta di ogni flusso (dopo l'avvio, cioè il primo giro con il segreto) è andata bene.
export async function stato(env, ms = Date.now()) {
  const out = { sano: false, segreto: haSegreto(env), repository: repoValido(env), provato: false, avvio: null, battito: null, adesso: iso(ms), sveglie: [] };
  try {
    const db = env.DB;
    await schema(db);
    const righe = (await db.prepare("SELECT chiave, flusso, slot, stato, tentativi, quando, dettaglio FROM orologio WHERE slot IS NULL OR quando >= ?1")
      .bind(iso(ms - 9 * 86400000)).all()).results || [];
    const per = new Map(righe.map((x) => [x.chiave, x]));
    out.avvio = per.has("avvio") ? per.get("avvio").quando : null;
    out.battito = per.has("battito") ? per.get("battito").quando : null;
    const avvio = out.avvio ? Date.parse(out.avvio) : null;
    let tutte = true;
    for (const s of SVEGLIE) {
      const u = ultimaDovuta(s, ms - TOLLERANZA);
      const riga = u ? per.get(s.flusso + "@" + u.slot) : null;
      const daGiudicare = u && avvio !== null && u.t >= avvio;
      const ok = !daGiudicare || (riga && riga.stato === "ok");
      if (!ok) tutte = false;
      out.sveglie.push({ flusso: s.flusso, cosa: s.cosa, orari: orari(s), dovuta: u ? u.slot : null, ok: !!ok,
                         esito: riga ? { stato: riga.stato, tentativi: riga.tentativi, quando: riga.quando, dettaglio: riga.dettaglio }
                                     : (daGiudicare ? { stato: "mai partita", tentativi: 0, quando: null, dettaglio: "nessun giro dell'orologio a quell'ora" } : null) });
    }
    // e almeno una partenza riuscita dopo l'avvio: un orologio appena acceso non è ancora provato
    out.provato = righe.some((x) => x.slot && x.stato === "ok" && avvio !== null && Date.parse(x.quando) >= avvio);
    out.sano = out.segreto && out.repository && avvio !== null && tutte && out.provato;
  } catch (e) {
    out.errore = "stato non leggibile: " + String((e && e.message) || e).slice(0, 120);
  }
  return out;
}
function orari(s) {
  const g = s.giorni.length === 7 ? "ogni giorno" : s.giorni.join(",") === "1,2,3,4,5" ? "dal lunedì al venerdì" : "giorni " + s.giorni.join(",");
  return g + " alle " + s.ore.map((o) => o + ":" + due(s.minuto)).join(", ") + " di Roma";
}
