// Prova della logica del Registro, senza browser e senza dipendenze: node redazione/registro/prova.mjs
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const html = readFileSync(fileURLToPath(new URL("./index.html", import.meta.url)), "utf8");
const pezzi = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
if (pezzi.length !== 1) { console.error("Attesi un solo <script> nella pagina, trovati " + pezzi.length); process.exit(1); }
const ctxVm = vm.createContext({ console, Date, Math, Promise, setTimeout });
vm.runInContext(pezzi[0][1], ctxVm);
const R = ctxVm.Registro;

let passate = 0, fallite = 0;
const caso = async (nome, fn) => {
  try { await fn(); passate++; console.log("ok   " + nome); }
  catch (e) { fallite++; console.log("NO   " + nome + "\n     " + (e && e.message)); }
};
const vero = (c, m) => { if (!c) throw new Error(m || "condizione falsa"); };
const uguale = (a, b, m) => { const x = JSON.stringify(a), y = JSON.stringify(b); if (x !== y) throw new Error((m || "diverso") + ": " + x + " invece di " + y); };

/* ---- Database finto: stesso contratto del db della pagina (doc, collection, get, set, update) ---- */
function dbFinto(iniziale = {}) {
  const dati = new Map(Object.entries(JSON.parse(JSON.stringify(iniziale))));
  const f = { dati, scritture: [], guasti: [], primaDiUpdate: null };
  const guasto = (op, path) => { const i = f.guasti.findIndex(g => g.op === op && path.startsWith(g.path)); if (i < 0) return; const g = f.guasti.splice(i, 1)[0]; throw { code: g.code, message: "finto" }; };
  const doc = path => ({
    path,
    async get() { guasto("get", path); const d = dati.get(path); return { id: path.split("/").pop(), exists: !!d, data: () => (d ? JSON.parse(JSON.stringify(d)) : undefined) }; },
    async set(d) { guasto("set", path); f.scritture.push({ op: "set", path, d }); dati.set(path, JSON.parse(JSON.stringify(d))); },
    async update(d) {
      if (f.primaDiUpdate) { const h = f.primaDiUpdate; f.primaDiUpdate = null; h(path); }
      guasto("update", path);
      if (!dati.has(path)) throw { code: "invalid_argument", message: "non esiste" };
      f.scritture.push({ op: "update", path, d });
      const cur = dati.get(path);
      for (const k in d) cur[k] = (d[k] && typeof d[k] === "object" && !Array.isArray(d[k]) && cur[k] && typeof cur[k] === "object") ? { ...cur[k], ...d[k] } : d[k];
    }
  });
  f.db = { doc, collection: name => ({ doc: id => doc(name + "/" + id) }) };
  f.raw = () => {
    const r = { tasks: {}, serate: {}, clic: {}, appunti: {}, rilasci: {}, salute: dati.get("meta/salute") || null, piano: dati.get("meta/piano") || null };
    for (const [p, d] of dati) { const [c, id] = p.split("/"); if (["tasks", "serate", "clic", "appunti", "rilasci"].includes(c)) r[c][id] = d; }
    return r;
  };
  return f;
}
function mcpFinto(regole) {
  const m = { chiamate: [] };
  m.callTool = async (nome, tool, input) => { m.chiamate.push({ nome, tool, input }); const r = regole[nome]; if (r === "ok") return { payload: { ok: true } }; throw { code: r || "server_not_found", message: "finto" }; };
  return m;
}
let seq = 0;
const dip = (f, mcp) => ({ db: f.db, mcp, ora: () => new Date("2026-11-26T18:00:00+01:00"), nuovoId: () => "t" + (++seq), pausa: async () => {} });
const ORA = new Date("2026-11-26T18:00:00+01:00");

/* ---- Dati di oggi, come sono nel Registro (senza i campi nuovi) ---- */
const OGGI = {
  "tasks/n-registro-nuovo": { codice: "G-65", titolo: "Il Registro nuovo", stato: "in-corso", priorita: "high", ordine: 5, input: "approvazione", domanda: "Premi una volta il tasto della pagina di prova", obiettivo: "Il Registro diventa la pagina di chi dirige", modello: "Opus", sforzo: "high", giorno: "2026-11-27" },
  "tasks/n-festivi-2027": { codice: "G-50", titolo: "Giorni senza edizione del 2027", stato: "pronta", priorita: "low", ordine: 60, finestra: "con-prova", domanda: "", modello: "Sonnet", sforzo: "medium" },
  "tasks/g-testo": { codice: "G-45", titolo: "Il testo regge contro i dati", stato: "in-corso", priorita: "high", ordine: 2 },
  "tasks/g-impara": { codice: "G-54", titolo: "Impara cresce da sola", stato: "pronta", priorita: "high", ordine: 3, domanda: "Guarda le pagine" },
  "tasks/g-carta": { codice: "G-19", titolo: "Approvare la bozza di CARTA.md", stato: "da-fare", priorita: "high", ordine: 5, chi: "Paolo", domanda: "Approvi la bozza?" },
  "tasks/g-orologio": { codice: "G-58", titolo: "Un orologio affidabile", stato: "da-fare", priorita: "high", ordine: 6 },
  "tasks/g-minuti": { codice: "G-12", titolo: "Meno minuti di GitHub", stato: "da-fare", priorita: "medium", ordine: 4 },
  "tasks/g-medium": { codice: "G-62", titolo: "Pubblicare anche su Medium", stato: "da-fare", priorita: "tbd", ordine: 20 },
  "tasks/d-homepage": { codice: "G-33", titolo: "Homepage B", stato: "fatta", priorita: 1, ordine: 50, chiusa: "2026-11-16" },
  "tasks/g-vecchia": { codice: "G-07", titolo: "Glossario", stato: "idea", priorita: 2, ordine: 40 },
  "serate/2026-11-25-2": { stato: "con-prova", ramo: "con-prova", dopo: { righe: [{ codice: "G-45", cosa: "x" }, { codice: "G-54", cosa: "y" }, { codice: "G-50", cosa: "z" }], prova: { giorno: "2026-11-27", esito: "da-fare" } } },
  "serate/2026-11-25": { stato: "in-linea", ramo: "rilascio", dopo: { righe: [{ codice: "G-50", cosa: "Nulla di suo" }] }, fine: { testo: "In linea dalle 18:48", verificato: true } },
  "meta/salute": { verificato: "2026-11-25T18:58:00+01:00", righe: [{ nome: "Edizione", stato: "ok", testo: "#033 pubblicata" }], rilasci: [
    { esito: "ok", nome: "Due rami, pannello, newsletter", quando: "2026-11-25T18:48:00+01:00", testo: "Due collaudi indipendenti · verificato dal vivo da GitHub" },
    { esito: "ok", nome: "Controllo dalla pubblicazione", quando: "2026-11-23T14:20:00+01:00", testo: "Collaudo verde" }] }
};
const conPiano = (extra = {}) => ({ ...OGGI, "meta/piano": { settimana: "2026-11-28", voci: ["G-12", "G-58"], tolte: [], via: null, ...extra }, "meta/capo": { attivita: "trig_finto" } });
const ctxDi = f => R.contesto(f.raw(), ORA);
const codici = l => l.map(x => (x.v || x).codice);

await caso("dati di oggi senza i campi nuovi: valori prudenti", () => {
  const ctx = ctxDi(dbFinto(OGGI));
  const v = ctx.perCodice.get("G-58");
  uguale(v.livello, "visto"); uguale(v.cosa, "Un orologio affidabile"); uguale(v.lettore, "Da scrivere"); uguale(v.riserva, false);
  uguale(ctx.perCodice.get("G-33").priorita, "high", "priorità numerica vecchia");
  uguale(ctx.perCodice.get("G-07").priorita, "tbd", "stato idea");
  uguale(R.statoVoce(ctx.perCodice.get("G-07"), ctx).testo, "Idea");
});
await caso("la serata con la prova mette le sue voci in Aspetta la prova", () => {
  const ctx = ctxDi(dbFinto(OGGI));
  for (const c of ["G-45", "G-54", "G-50"]) uguale(R.statoVoce(ctx.perCodice.get(c), ctx).testo, "Aspetta la prova", c);
  const z = R.zoneOggi(ctx);
  vero(codici(z.lavoro).includes("G-54") && codici(z.lavoro).includes("G-50"), "in Al lavoro");
  vero(!codici(z.vedere).includes("G-54"), "G-54 aspetta la prova, non va in Da vedere");
});
await caso("Tocca a te con i dati di oggi: domande aperte, nessun piano, margine sempre", () => {
  const z = R.zoneOggi(ctxDi(dbFinto(OGGI)));
  uguale(z.piano, null); uguale(codici(z.domande).sort(), ["G-19", "G-65"]); uguale(z.niente, false); uguale(z.margine, null);
  vero(z.ultimo && z.ultimo.nome.startsWith("Due rami") && z.ultimo.verificato === true, "ultimo rilascio verificato");
  vero(z.rilasci[1].verificato === false, "secondo rilascio non dice verificato");
});
await caso("nulla da decidere: una riga sola", () => {
  const z = R.zoneOggi(ctxDi(dbFinto({ "tasks/a": { codice: "G-1", titolo: "a", stato: "in-corso" } })));
  uguale(z.niente, true); uguale(codici(z.lavoro), ["G-1"]); uguale(R.statoVoce(R.contesto({ tasks: { a: { codice: "G-1", stato: "in-corso" } } }, ORA).voci[0], R.contesto({}, ORA)).testo, "Al lavoro");
});
await caso("piano proposto: voci in piano, Togli, Via al piano", async () => {
  const f = dbFinto(conPiano());
  let z = R.zoneOggi(ctxDi(f));
  uguale(codici(z.piano.voci), ["G-12", "G-58"]); uguale(R.statoVoce(ctxDi(f).perCodice.get("G-12"), ctxDi(f)).testo, "In piano");
  const m = mcpFinto({ "Claude Code Remote": "ok" });
  const t = await R.togli(dip(f, m), "G-58", "2026-11-28");
  uguale(t.esito, "tolta"); uguale(f.dati.get("meta/piano").tolte, ["G-58"]); uguale(m.chiamate.length, 0, "Togli non lancia nulla");
  uguale(f.dati.get("clic/" + t.id).tipo, "togli"); uguale(f.dati.get("clic/" + t.id).esito, "da-eseguire");
  z = R.zoneOggi(ctxDi(f)); uguale(codici(z.piano.voci), ["G-12"]);
  const v = await R.premi(dip(f, m), { tipo: "via-piano", piano: "2026-11-28" });
  uguale(v.esito, "partito");
  const ctx = ctxDi(f); z = R.zoneOggi(ctx);
  vero(z.piano.clic && z.piano.clic.id === v.id, "il piano mostra il clic, il tasto sparisce");
  uguale(R.statoVoce(ctx.perCodice.get("G-12"), ctx).testo, "In coda"); uguale(R.statoVoce(ctx.perCodice.get("G-58"), ctx).testo, "Più avanti");
  uguale(m.chiamate[0].input, { trigger_id: "trig_finto", text: "clic/" + v.id }, "nel testo solo il codice del clic");
  // piano avviato dal capo sviluppo: sparisce da Tocca a te
  f.dati.get("meta/piano").via = { quando: "x" }; uguale(R.zoneOggi(ctxDi(f)).piano, null);
});
await caso("lancio riuscito con il secondo nome del connettore", async () => {
  const f = dbFinto(conPiano()), m = mcpFinto({ "Claude_Code_Remote": "ok" });
  const r = await R.premi(dip(f, m), { tipo: "margine" });
  uguale(r.esito, "partito"); uguale(m.chiamate.map(c => c.nome), ["Claude Code Remote", "Claude_Code_Remote"]);
  const c = f.dati.get("clic/" + r.id); uguale(c.lancio.esito, "partito"); uguale(R.statoClic(c, ORA).testo, "Partito adesso.");
});
await caso("lancio fallito: il clic resta e va in coda", async () => {
  const f = dbFinto(conPiano()), m = mcpFinto({ "Claude Code Remote": "tool_error" });
  const r = await R.premi(dip(f, m), { tipo: "ok", voce: "G-54" });
  uguale(r.esito, "coda"); uguale(m.chiamate.length, 1, "un errore vero non prova l'altro nome");
  const c = f.dati.get("clic/" + r.id); uguale(c.esito, "da-eseguire"); uguale(R.statoClic(c, ORA).testo, "In coda: parte al prossimo giro.");
});
await caso("mcp assente o meta/capo assente: in coda", async () => {
  const f = dbFinto(conPiano());
  const r = await R.premi(dip(f, null), { tipo: "margine" });
  uguale(r.esito, "coda"); uguale(r.errore, "mcp-assente"); vero(f.dati.has("clic/" + r.id));
  const g = dbFinto(OGGI), m = mcpFinto({ "Claude Code Remote": "ok" });
  const s = await R.premi(dip(g, m), { tipo: "margine" });
  uguale(s.esito, "coda"); uguale(s.errore, "capo-assente"); uguale(m.chiamate.length, 0);
});
await caso("esito incerto: niente ritentativi da soli, poi Riprova sullo stesso clic", async () => {
  const f = dbFinto(conPiano()), m = mcpFinto({ "Claude Code Remote": "upstream_error" });
  const r = await R.premi(dip(f, m), { tipo: "indietro", voce: "Due rami" });
  uguale(r.esito, "incerto"); uguale(m.chiamate.length, 1);
  const st = R.statoClic(f.dati.get("clic/" + r.id), ORA); uguale(st.tipo, "incerto"); uguale(st.riprova, true);
  const prima = [...f.dati.keys()].filter(k => k.startsWith("clic/")).length;
  m.chiamate.length = 0; const m2 = mcpFinto({ "Claude Code Remote": "ok" });
  const r2 = await R.lancia(dip(f, m2), r.id);
  uguale(r2.esito, "partito"); uguale([...f.dati.keys()].filter(k => k.startsWith("clic/")).length, prima, "nessun clic nuovo");
  const s = await R.premi(dip(f, mcpFinto({ "Claude Code Remote": "server_unavailable" })), { tipo: "margine" }); uguale(s.esito, "incerto");
});
await caso("clic non scritto: non si lancia nulla", async () => {
  const f = dbFinto(conPiano()), m = mcpFinto({ "Claude Code Remote": "ok" });
  f.guasti.push({ op: "set", path: "clic/", code: "quota_exceeded" });
  const r = await R.premi(dip(f, m), { tipo: "via-piano", piano: "2026-11-28" });
  uguale(r.esito, "non-scritto"); uguale(m.chiamate.length, 0);
  f.guasti.push({ op: "set", path: "clic/", code: "unavailable" });
  const s = await R.premi(dip(f, m), { tipo: "margine" }); uguale(s.esito, "partito", "unavailable si ritenta una volta sola");
});
await caso("voce Da vedere: Ok e Non ancora", async () => {
  const dati = { ...conPiano(), "tasks/g-x": { codice: "G-70", titolo: "Pagine nuove", stato: "pronta", domanda: "Guarda e dimmi", lettore: "Pagine nuove sul sito", anteprima: "https://esempio.it/a", livello: "visto" },
    "tasks/g-y": { codice: "G-71", titolo: "Altro", stato: "pronta", domanda: "Dimmi", anteprima: "javascript:alert(1)" } };
  const f = dbFinto(dati), m = mcpFinto({ "Claude Code Remote": "ok" });
  let z = R.zoneOggi(ctxDi(f));
  uguale(codici(z.vedere).sort(), ["G-70", "G-71"]); uguale(z.vedere.find(x => x.v.codice === "G-71").v.anteprima, "", "link non https scartato");
  const ok = await R.premi(dip(f, m), { tipo: "ok", voce: "G-70", testo: "va bene" });
  const no = await R.premi(dip(f, m), { tipo: "non-ancora", voce: "G-71" });
  uguale([ok.esito, no.esito], ["partito", "partito"]);
  z = R.zoneOggi(ctxDi(f));
  vero(z.vedere.every(x => x.clic), "dopo il clic i tasti spariscono");
  uguale(f.dati.get("clic/" + ok.id).testo, "va bene"); uguale(f.dati.get("clic/" + no.id).tipo, "non-ancora");
  // il capo sviluppo esegue: la voce torna senza clic aperto
  f.dati.get("clic/" + no.id).esito = "eseguito"; z = R.zoneOggi(ctxDi(f));
  uguale(z.vedere.find(x => x.v.codice === "G-71").clic, null);
});
await caso("margine con e senza percentuale", async () => {
  uguale(R.margineTesto("30"), "30%"); uguale(R.margineTesto(" 45 % "), "45%"); uguale(R.margineTesto(""), ""); uguale(R.margineTesto("tanto"), ""); uguale(R.margineTesto("130"), "");
  const f = dbFinto(conPiano()), m = mcpFinto({ "Claude Code Remote": "ok" });
  const a = await R.premi(dip(f, m), { tipo: "margine", testo: R.margineTesto("30") });
  uguale(f.dati.get("clic/" + a.id).testo, "30%");
  vero(R.zoneOggi(ctxDi(f)).margine, "margine in corso: niente doppio clic");
  f.dati.get("clic/" + a.id).esito = "eseguito";
  const b = await R.premi(dip(f, m), { tipo: "margine", testo: R.margineTesto("") });
  uguale(f.dati.get("clic/" + b.id).testo, "");
});
await caso("riserva: filtro e coda dopo il margine", async () => {
  const f = dbFinto({ ...conPiano(), "tasks/g-r": { codice: "G-80", titolo: "Test di scrittura", stato: "da-fare", priorita: "low", riserva: true, ordine: 1 } });
  uguale(codici(R.elenco(ctxDi(f), "priorita", "riserva")), ["G-80"]);
  uguale(codici(R.zoneOggi(ctxDi(f)).riserva), ["G-80"]);
  await R.premi(dip(f, mcpFinto({ "Claude Code Remote": "ok" })), { tipo: "margine" });
  const ctx = ctxDi(f); uguale(R.statoVoce(ctx.perCodice.get("G-80"), ctx).testo, "In coda");
});
await caso("appunto: scritto nel database, nessun lancio", async () => {
  const f = dbFinto(OGGI), m = mcpFinto({ "Claude Code Remote": "ok" });
  uguale((await R.aggiungiAppunto(dip(f, m), "   ")).esito, "vuoto");
  const r = await R.aggiungiAppunto(dip(f, m), "La homepage ha troppo spazio");
  uguale(r.esito, "salvato"); uguale(m.chiamate.length, 0);
  const c = f.dati.get("clic/" + r.id); uguale(c.tipo, "appunto"); uguale(c.testo, "La homepage ha troppo spazio");
  const a = f.dati.get(c.rif); uguale(a.stato, "nuovo"); uguale(a.testo, "La homepage ha troppo spazio");
  uguale(R.zoneOggi(ctxDi(f)).appunti.length, 1);
});
await caso("ordinamento per priorità e per ordine di lavoro", () => {
  const ctx = ctxDi(dbFinto(OGGI));
  uguale(codici(R.elenco(ctx, "priorita", "aperte")), ["G-45", "G-54", "G-19", "G-65", "G-58", "G-12", "G-50"]);
  uguale(codici(R.elenco(ctx, "lavoro", "aperte")), ["G-45", "G-54", "G-12", "G-19", "G-65", "G-58", "G-50"]);
  uguale(R.elenco(ctx, "lavoro", "aperte")[0].pos, 1);
});
await caso("i quattro filtri e il conteggio delle aperte", () => {
  const ctx = ctxDi(dbFinto({ ...OGGI, "tasks/g-r": { codice: "G-80", titolo: "r", riserva: true, priorita: "low" } }));
  uguale(codici(R.elenco(ctx, "priorita", "idee")), ["G-62", "G-07"]);
  uguale(codici(R.elenco(ctx, "priorita", "fatte")), ["G-33"]);
  uguale(codici(R.elenco(ctx, "priorita", "riserva")), ["G-80"]);
  uguale(R.nAperte(ctx), 8);
});
await caso("due scrittori: il piano cambia tra lettura e scrittura", async () => {
  // il capo sviluppo riscrive il piano mentre Paolo tocca Togli
  const f = dbFinto(conPiano()), m = mcpFinto({});
  const vecchio = R.zoneOggi(ctxDi(f)).piano.settimana;
  f.dati.set("meta/piano", { settimana: "2026-12-05", voci: ["G-58"], tolte: [], via: null });
  const r = await R.togli(dip(f, m), "G-58", vecchio);
  uguale(r.esito, "cambiato"); uguale(f.dati.get("meta/piano").tolte, [], "nessuna scrittura sul piano nuovo");
  uguale(f.dati.get("clic/" + r.id).esito, "scartato");
  // piano avviato nel frattempo
  const g = dbFinto(conPiano({ via: { quando: "x" } }));
  uguale((await R.togli(dip(g, m), "G-12", "2026-11-28")).esito, "cambiato");
  // un'altra scheda ha tolto un'altra voce: si unisce alla copia fresca, non a quella vecchia
  const h = dbFinto(conPiano());
  h.dati.get("meta/piano").tolte = ["G-12"];
  uguale((await R.togli(dip(h, m), "G-58", "2026-11-28")).esito, "tolta");
  uguale(h.dati.get("meta/piano").tolte, ["G-12", "G-58"]);
  // la pagina scrive solo i campi cambiati, mai la voce intera
  const scritte = [...f.scritture, ...g.scritture, ...h.scritture];
  vero(scritte.every(s => !s.path.startsWith("tasks/")), "la pagina non scrive mai le schede");
  vero(scritte.filter(s => s.path === "meta/piano").every(s => s.op === "update" && Object.keys(s.d).join() === "tolte"), "solo update di tolte");
});
await caso("ferma con la causa e link della chat", () => {
  const ctx = ctxDi(dbFinto({ "tasks/a": { codice: "G-9", titolo: "a", stato: "in-corso", ferma: "Manca il token di Cloudflare" } }));
  const s = R.statoVoce(ctx.voci[0], ctx); uguale([s.testo, s.causa], ["Ferma", "Manca il token di Cloudflare"]);
  uguale(R.chatURL("G-65"), "https://claude.ai/new?q=Gommberg%2C%20voce%20G-65%3A%20");
  uguale(R.comeSiLavora(R.normVoce("x", { modello: "Sonnet", sforzo: "medium" })), "Sonnet, sforzo medio");
});
await caso("dietro le quinte: salute vecchia, serate, consensi", async () => {
  const f = dbFinto(conPiano());
  await R.premi(dip(f, null), { tipo: "margine", testo: "20%" });
  const d = R.dietro(ctxDi(f));
  uguale(d.vecchia, false, "verifica di 23 ore fa"); uguale(d.serate.length, 2);
  f.dati.get("meta/salute").verificato = "2026-11-24T10:00:00+01:00"; uguale(R.dietro(ctxDi(f)).vecchia, true, "verifica di più di 26 ore fa"); uguale(d.consensi.length, 1); uguale(d.conta.margine, 1);
  uguale(d.consensi[0].lancio, "coda");
});
await caso("la pagina non contiene trattini lunghi", () => { vero(!/[–—]/.test(html)); });

console.log("\n" + passate + " casi passati, " + fallite + " falliti");
process.exit(fallite ? 1 : 0);
