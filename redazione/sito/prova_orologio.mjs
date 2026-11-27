// Collaudo dell'orologio dei controlli (redazione/sito/orologio.js, G-58) senza Cloudflare e senza rete: il codice vero,
// con il D1 finto (d1_finto.mjs, Node 22.5 o più) e un GitHub finto che risponde bene, rifiuta o non risponde.
// Lo lancia redazione/collaudo.py; da solo: node --no-warnings redazione/sito/prova_orologio.mjs. Esce con 1 al primo errore.
import { d1 } from "./d1_finto.mjs";
import worker from "./lettori.js";
import { SVEGLIE, aRoma, daRoma, scartoRoma, dovute, ultimaDovuta, giro, stato, etichetta } from "./orologio.js";

let ok = 0, ko = 0;
function verifica(nome, cond, dettaglio) {
  if (cond) { ok++; return; }
  ko++; process.stdout.write("NO  " + nome + (dettaglio !== undefined ? ": " + JSON.stringify(dettaglio) : "") + "\n");
}
const TOKEN = "github_pat_SEGRETO_DI_PROVA_123";
const log = [];
const logVero = console.log;
console.log = (...a) => log.push(a.join(" "));

// ------------------------------------------------------------- 1. l'ora di Roma, contro il fuso vero
const fmt = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/Rome", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23", weekday: "short" });
const GG = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };
let sbagli = 0, primo = null;
for (let t = Date.UTC(2026, 0, 1); t < Date.UTC(2028, 0, 1); t += 15 * 60000) {
  const p = Object.fromEntries(fmt.formatToParts(new Date(t)).map((x) => [x.type, x.value]));
  const r = aRoma(t);
  if (+p.year !== r.anno || +p.month !== r.mese || +p.day !== r.giorno || +p.hour !== r.ora || +p.minute !== r.minuto || GG[p.weekday] !== r.dow) {
    sbagli++; primo = primo || [new Date(t).toISOString(), p, r];
  }
}
verifica("ora di Roma uguale al fuso Europe/Rome per 2026 e 2027, ogni quarto d'ora", sbagli === 0, primo);
for (const [a, m, g] of [[2026, 11, 27], [2027, 7, 1], [2027, 3, 28], [2026, 10, 25]]) {
  for (const o of [8, 10, 19, 23]) {
    const t = daRoma(a, m, g, o, 15), r = aRoma(t);
    verifica(`daRoma ${a}-${m}-${g} ${o}:15 torna indietro uguale`, r.anno === a && r.mese === m && r.giorno === g && r.ora === o && r.minuto === 15, r);
  }
}
verifica("scarto d'inverno 1, d'estate 2", scartoRoma(Date.UTC(2026, 11, 7, 9)) === 1 && scartoRoma(Date.UTC(2027, 5, 7, 9)) === 2);

// ------------------------------------------------------------- 2. che cosa è dovuto, d'inverno e d'estate (cron in UTC)
const nomi = (ms, solo0 = true) => dovute(ms).filter((d) => !solo0 || d.ritardo === 0).map((d) => d.sveglia.flusso + "@" + d.slot).sort();
verifica("inverno, lunedì 7/12 09:15 UTC = 10:15 di Roma: il controllo del mattino", nomi(Date.UTC(2026, 11, 7, 9, 15)).join() === "mattino.yml@2026-12-07T10:15", nomi(Date.UTC(2026, 11, 7, 9, 15)));
verifica("inverno, 08:15 UTC = 9:15 di Roma: niente", nomi(Date.UTC(2026, 11, 7, 8, 15)).length === 0, nomi(Date.UTC(2026, 11, 7, 8, 15)));
verifica("estate, lunedì 7/6/2027 08:15 UTC = 10:15 di Roma: il controllo del mattino", nomi(Date.UTC(2027, 5, 7, 8, 15)).join() === "mattino.yml@2027-06-07T10:15", nomi(Date.UTC(2027, 5, 7, 8, 15)));
verifica("estate, 09:15 UTC = 11:15 di Roma: le segnalazioni, non il mattino", nomi(Date.UTC(2027, 5, 7, 9, 15)).join() === "segnalazioni.yml@2027-06-07T11:15", nomi(Date.UTC(2027, 5, 7, 9, 15)));
verifica("inverno, 18:30 UTC = 19:30 di Roma: le mail straordinarie", nomi(Date.UTC(2026, 11, 7, 18, 30)).join() === "dem.yml@2026-12-07T19:30");
verifica("estate, 17:30 UTC = 19:30 di Roma: le mail straordinarie", nomi(Date.UTC(2027, 5, 7, 17, 30)).join() === "dem.yml@2027-06-07T19:30");
verifica("sabato 10:15 di Roma: niente controllo del mattino", nomi(Date.UTC(2026, 11, 5, 9, 15)).length === 0);
const segn = (y, m, g) => { const out = []; for (let t = Date.UTC(y, m - 1, g) - 3 * 3600000; t < Date.UTC(y, m - 1, g) + 27 * 3600000; t += 15 * 60000) for (const d of dovute(t)) if (d.ritardo === 0 && d.sveglia.flusso === "segnalazioni.yml" && d.slot.startsWith(`${y}-${String(m).padStart(2, "0")}-${String(g).padStart(2, "0")}`)) out.push(d.slot.slice(11)); return out.join(","); };
for (const [y, m, g, cosa] of [[2026, 12, 7, "inverno"], [2027, 6, 7, "estate"], [2027, 3, 28, "giorno del passaggio all'ora legale"], [2026, 10, 25, "giorno del ritorno all'ora solare"]]) {
  verifica(`segnalazioni ogni 3 ore tra le 8 e le 23 di Roma (${cosa})`, segn(y, m, g) === "08:15,11:15,14:15,17:15,20:15,23:15", segn(y, m, g));
}
const u = ultimaDovuta(SVEGLIE[0], Date.UTC(2026, 11, 7, 7));   // lunedì mattina presto: l'ultima è venerdì 4/12
verifica("ultima partenza dovuta del mattino, lunedì alle 8: venerdì alle 10:15", u && u.slot === "2026-12-04T10:15", u);
verifica("cinque giri dopo l'ora dovuta: fuori dal recupero", !nomi(Date.UTC(2026, 11, 7, 10, 30), false).includes("mattino.yml@2026-12-07T10:15"));

// ------------------------------------------------------------- 3. GitHub finto
let chiamate = [], modo = "bene";
const github = async (url, init) => {
  chiamate.push({ url, init, corpo: JSON.parse(init.body) });
  if (modo === "bene") return new Response(JSON.stringify({ workflow_run_id: 1 }), { status: 200 });
  if (modo === "204") return new Response(null, { status: 204 });
  if (modo === "rifiuta") return new Response(JSON.stringify({ message: "Bad credentials" }), { status: 401 });
  if (modo === "422") return new Response(JSON.stringify({ message: "Unexpected inputs provided" }), { status: 422 });
  const e = new Error("scaduto"); e.name = "TimeoutError"; throw e;
};
const nuovo = (extra = {}) => ({ DB: d1(), GITHUB_REPOSITORY: "PaoloGom/gommberg-terminal-daily", GITHUB_ACTIONS_TOKEN: TOKEN, ...extra });
const ADESSO = { t: 0 };
Date.now = () => ADESSO.t;
const MATTINO = Date.UTC(2026, 11, 7, 9, 15);                   // lunedì 7/12, 10:15 di Roma

let env = nuovo();
ADESSO.t = MATTINO + 5000;
let f = await giro(env, MATTINO, github);
verifica("GitHub risponde bene: una partenza, stato ok", f.length === 1 && f[0].stato === "ok" && chiamate.length === 1, f);
const c0 = chiamate[0];
verifica("la chiamata è il workflow_dispatch giusto", c0 && c0.url === "https://api.github.com/repos/PaoloGom/gommberg-terminal-daily/actions/workflows/mattino.yml/dispatches"
  && c0.init.method === "POST" && c0.corpo.ref === "main" && c0.corpo.inputs.orologio === "cloudflare" && c0.init.headers.authorization === "Bearer " + TOKEN
  && c0.init.headers["user-agent"] && c0.init.headers.accept === "application/vnd.github+json", c0 && { url: c0.url, corpo: c0.corpo });
f = await giro(env, MATTINO, github);
verifica("lo stesso giro ripetuto (Cloudflare che riprova): nessuna seconda partenza", f.length === 0 && chiamate.length === 1, f);
ADESSO.t = MATTINO + 15 * 60000;
f = await giro(env, MATTINO + 15 * 60000, github);
verifica("il quarto d'ora dopo: nessuna seconda partenza", f.length === 0 && chiamate.length === 1, f);
// due istanze nello stesso istante, con un database lento: una sola parte
env = nuovo(); env.DB.latenza = 5; chiamate = [];
ADESSO.t = MATTINO + 1000;
await Promise.all([giro(env, MATTINO, github), giro(env, MATTINO, github), giro(env, MATTINO, github)]);
verifica("tre giri contemporanei: una sola partenza", chiamate.length === 1, chiamate.length);
env.DB.latenza = 0;
modo = "204"; chiamate = [];
f = await giro(nuovo(), Date.UTC(2026, 11, 7, 18, 30), github);
verifica("GitHub che risponde 204 (versione vecchia dell'API) è un ok; le mail straordinarie partono con modo sincronizza",
  f.length === 1 && f[0].stato === "ok" && chiamate[0].corpo.inputs.modo === "sincronizza" && /dem\.yml\/dispatches$/.test(chiamate[0].url), f);

// stato sano dopo le partenze
env = nuovo(); modo = "bene"; chiamate = [];
ADESSO.t = Date.UTC(2026, 11, 7, 7, 0);
await giro(env, Date.UTC(2026, 11, 7, 7, 0), github);                       // primo giro con il segreto: l'avvio
let s = await stato(env, Date.UTC(2026, 11, 7, 7, 5));
verifica("appena acceso, prima di ogni partenza: non ancora provato, non sano", s.sano === false && s.provato === false && s.avvio, s);
for (const t of [Date.UTC(2026, 11, 7, 7, 15), Date.UTC(2026, 11, 7, 9, 15)]) { ADESSO.t = t + 2000; await giro(env, t, github); }
s = await stato(env, Date.UTC(2026, 11, 7, 9, 50));
verifica("dopo le 8:15 e le 10:15 partite bene: sano", s.sano === true && s.segreto && s.sveglie.every((x) => x.ok), s);
verifica("lo stato non contiene né il token né il nome del repository", !JSON.stringify(s).includes(TOKEN) && !JSON.stringify(s).includes("PaoloGom"), s);
s = await stato(env, Date.UTC(2026, 11, 7, 10, 40));
verifica("le 11:15 non sono partite (il cron si è fermato): non sano, e dice quale", s.sano === false && s.sveglie.find((x) => x.flusso === "segnalazioni.yml").esito.stato === "mai partita", s.sveglie);

// GitHub che rifiuta: errore visibile, si riprova fino a 3 volte, poi basta
env = nuovo(); modo = "rifiuta"; chiamate = [];
ADESSO.t = MATTINO - 3600000; await giro(env, MATTINO - 3600000, github);   // avvio
for (let k = 0; k <= 4; k++) { const t = MATTINO + k * 15 * 60000; ADESSO.t = t + 1000; await giro(env, t, github); }
const cm = chiamate.filter((x) => /mattino\.yml/.test(x.url)).length;
verifica("GitHub rifiuta: 3 tentativi in 45 minuti, non di più", cm === 3, cm);
s = await stato(env, MATTINO + 3600000);
const sm = s.sveglie.find((x) => x.flusso === "mattino.yml");
verifica("GitHub rifiuta: non sano, con il motivo", s.sano === false && sm.esito.stato === "errore" && /401: Bad credentials/.test(sm.esito.dettaglio) && sm.esito.tentativi === 3, sm);
// GitHub che rifiuta e poi accetta: il secondo tentativo basta
env = nuovo(); chiamate = [];
ADESSO.t = MATTINO - 3600000; await giro(env, MATTINO - 3600000, github);
modo = "422"; ADESSO.t = MATTINO + 1000; await giro(env, MATTINO, github);
modo = "bene"; ADESSO.t = MATTINO + 15 * 60000 + 1000; await giro(env, MATTINO + 15 * 60000, github);
s = await stato(env, MATTINO + 40 * 60000);
verifica("rifiuto e poi successo al quarto d'ora dopo: sano", chiamate.length === 2 && s.sveglie.find((x) => x.flusso === "mattino.yml").ok, s.sveglie);
// GitHub che non risponde
env = nuovo(); modo = "muto"; chiamate = [];
ADESSO.t = MATTINO + 1000;
f = await giro(env, MATTINO, github);
verifica("GitHub non risponde: errore scritto, nessuna eccezione", f.length === 1 && f[0].stato === "errore" && /non risponde \(TimeoutError\)/.test(f[0].dettaglio), f);

// segreto assente: nessuna chiamata, non sano; poi Paolo lo mette e il quarto d'ora dopo parte
env = nuovo({ GITHUB_ACTIONS_TOKEN: undefined }); modo = "bene"; chiamate = [];
ADESSO.t = MATTINO + 1000;
f = await giro(env, MATTINO, github);
s = await stato(env, MATTINO + 30 * 60000);
verifica("segreto assente: nessuna chiamata a GitHub, stato senza-segreto, non sano", chiamate.length === 0 && f[0].stato === "senza-segreto" && s.segreto === false && s.sano === false && s.avvio === null, { f, s });
env.GITHUB_ACTIONS_TOKEN = TOKEN;
ADESSO.t = MATTINO + 15 * 60000 + 1000;
f = await giro(env, MATTINO + 15 * 60000, github);
s = await stato(env, MATTINO + 40 * 60000);
verifica("segreto messo: la partenza delle 10:15 recuperata alle 10:30, sano", chiamate.length === 1 && f[0].stato === "ok" && s.sano === true, { f, s });
// repository non passato da sito.yml
env = nuovo({ GITHUB_REPOSITORY: "" }); chiamate = [];
f = await giro(env, MATTINO, github);
verifica("senza GITHUB_REPOSITORY: errore che lo dice, nessuna chiamata", chiamate.length === 0 && /GITHUB_REPOSITORY/.test(f[0].dettaglio), f);
// database rotto: il giro non lancia eccezioni
f = await giro({ ...nuovo(), DB: { prepare: () => { throw new Error("D1 giù"); } } }, MATTINO, github);
verifica("database che non risponde: nessuna eccezione, errore scritto", f.length === 1 && f[0].stato === "errore", f);
s = await stato({ ...nuovo(), DB: { prepare: () => { throw new Error("D1 giù"); } } }, MATTINO);
verifica("database che non risponde: stato non sano con il motivo", s.sano === false && /D1 giù/.test(s.errore || ""), s);

// ------------------------------------------------------------- 4. dal Worker: /api/orologio e il cron
env = { ...nuovo(), ASSETS: { fetch: async () => new Response("statico") } };
let r = await worker.fetch(new Request("https://gommberg.com/api/orologio"), env);
let j = await r.json();
verifica("GET /api/orologio: risponde con lo stato, senza cache", r.status === 200 && typeof j.sano === "boolean" && j.segreto === true && r.headers.get("cache-control") === "no-store", j);
r = await worker.fetch(new Request("https://gommberg.com/api/orologio", { method: "POST" }), env);
verifica("POST /api/orologio: rifiutato", r.status === 405);
const attese = [];
const fetchVero = globalThis.fetch;
globalThis.fetch = github; chiamate = []; modo = "bene";
ADESSO.t = MATTINO + 1000;
await worker.scheduled({ scheduledTime: MATTINO, cron: "*/15 * * * *" }, env, { waitUntil: (p) => attese.push(p) });
await Promise.all(attese);
globalThis.fetch = fetchVero;
verifica("il cron del Worker lancia il controllo del mattino", chiamate.length === 1 && /mattino\.yml/.test(chiamate[0].url), chiamate.length);
verifica("ogni sveglia ha flusso, orari e inputs con orologio", SVEGLIE.every((x) => /\.yml$/.test(x.flusso) && x.ore.length && x.inputs.orologio === "cloudflare"));
verifica("il token non compare mai nei log", !log.join("\n").includes(TOKEN), log.filter((x) => x.includes(TOKEN)).length);
verifica("etichetta dell'ora di Roma", etichetta(aRoma(MATTINO)) === "2026-12-07T10:15");

console.log = logVero;
console.log(ko ? `orologio: ${ko} prove fallite su ${ok + ko}` : `orologio: ${ok} prove superate (ora di Roma d'inverno e d'estate, GitHub che accetta, rifiuta e tace, segreto assente, nessuna doppia partenza)`);
process.exit(ko ? 1 : 0);
