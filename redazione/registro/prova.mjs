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
    const r = { tasks: {}, serate: {}, clic: {}, appunti: {}, rilasci: {}, salute: dati.get("meta/salute") || null, piano: dati.get("meta/piano") || null, capo: dati.get("meta/capo") || null, stato: dati.get("meta/stato") || null };
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
  "tasks/n-festivi-2027": { codice: "G-50", titolo: "Giorni senza edizione del 2027", stato: "pronta", priorita: "low", ordine: 60, finestra: "con-prova", prova: { giorno: "2026-11-27", esito: "da-fare" }, domanda: "", modello: "Sonnet", sforzo: "medium" },
  "tasks/g-testo": { codice: "G-45", titolo: "Il testo regge contro i dati", stato: "in-corso", priorita: "high", ordine: 2, prova: { giorno: "2026-11-27", esito: "da-fare" } },
  "tasks/g-impara": { codice: "G-54", titolo: "Impara cresce da sola", stato: "pronta", priorita: "high", ordine: 3, domanda: "Guarda le pagine", prova: { giorno: "2026-11-27", esito: "da-fare" } },
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
const ctxDi = f => R.contesto(f.raw(), ORA);
const codici = l => l.map(x => (x.v || x).codice);

const VERI = {
  "tasks/g-carta": { codice: "G-19", titolo: "Approvare la bozza di CARTA.md", chi: "Paolo", input: "azione", stato: "da-fare", priorita: "high", ordine: 5, domanda: "Approvi la bozza di CARTA.md? Vedi https://esempio.it/carta." },
  "tasks/n-gommunity-coda": { codice: "G-55", titolo: "La Gommunity: prova della segnalazione", chi: "Paolo", input: "azione", stato: "da-fare", priorita: "high", ordine: 81, domanda: "" },
  "tasks/n-google": { codice: "G-35", titolo: "Farsi trovare su Google", chi: "Paolo", input: "", stato: "in-corso", priorita: "medium", ordine: 75 },
  "tasks/n-orologio": { codice: "G-58", titolo: "Un orologio affidabile", chi: "Claude", input: "azione", stato: "da-fare", priorita: "high", ordine: 7 },
  "tasks/n-dem-auguri": { codice: "G-49", titolo: "Auguri del 19/12", chi: "Insieme", input: "approvazione", stato: "in-corso", priorita: "medium", scadenza: "2026-12-09" },
  "tasks/n-decisione": { codice: "G-61", titolo: "Uscire entro le 8", chi: "Insieme", input: "decisione", stato: "da-fare", priorita: "medium" },
  "tasks/i-asia-eodhd": { codice: "G-41", titolo: "Kospi e Hang Seng", chi: "Claude", stato: "da-fare", priorita: "medium", scadenza: "2026-12-24", ordine: 9 },
  "tasks/i-altro": { codice: "G-42", titolo: "Memoria delle edizioni", chi: "Claude", stato: "da-fare", priorita: "medium", ordine: 8 },
  "tasks/i-1000": { codice: "G-23", titolo: "Crescita verso 1.000 lettori", chi: "Insieme", stato: "da-fare", priorita: "tbd", scadenza: "2027-03-31" }
};
const conCapo = (d, giro = "19:47") => ({ ...d, "meta/capo": { attivita: "trig_finto", giro } });

await caso("dati di oggi senza i campi nuovi: valori prudenti", () => {
  const ctx = ctxDi(dbFinto(OGGI));
  const v = ctx.perCodice.get("G-58");
  uguale(v.livello, "visto"); uguale(v.cosa, "Un orologio affidabile"); uguale(v.lettore, "Da scrivere"); uguale(v.riserva, false);
  uguale(ctx.perCodice.get("G-33").priorita, "high", "priorità numerica vecchia");
  uguale(ctx.perCodice.get("G-07").priorita, "tbd", "stato idea");
  uguale(R.statoVoce(ctx.perCodice.get("G-07"), ctx).testo, "Idea");
  uguale(R.comeSiLavora(ctx.perCodice.get("G-58")), "Da decidere", "modello assente: mai un modello inventato");
});
await caso("la prova sta sulla voce: Aspetta la prova", () => {
  const ctx = ctxDi(dbFinto(OGGI));
  for (const c of ["G-45", "G-54", "G-50"]) uguale(R.statoVoce(ctx.perCodice.get(c), ctx).testo, "Aspetta la prova", c);
  const z = R.zoneOggi(ctx);
  uguale(codici(z.lavoro), ["G-45", "G-50"]);
  const g54 = z.tocca.find(x => x.v.codice === "G-54");
  vero(g54 && !g54.vedere && g54.s.testo === "Aspetta la prova", "la domanda di G-54 resta in Tocca a te, con lo stato scritto, senza Ok");
});
await caso("prova ok, prova ko, e le serate non decidono più lo stato", () => {
  const voce = prova => ({ "tasks/a": { codice: "G-45", titolo: "a", stato: "in-corso", chi: "Claude", prova } });
  let ctx = ctxDi(dbFinto(voce({ giorno: "2026-11-27", esito: "ok" }))); uguale(R.statoVoce(ctx.voci[0], ctx).testo, "Al lavoro");
  ctx = ctxDi(dbFinto(voce({ giorno: "2026-11-27", esito: "ko", nota: "il desk ha tagliato una tabella" })));
  uguale([R.statoVoce(ctx.voci[0], ctx).testo, R.statoVoce(ctx.voci[0], ctx).causa], ["Ferma", "La prova non è andata bene: il desk ha tagliato una tabella"]);
  // una serata con-prova mai aggiornata non tiene più ferma una voce
  ctx = ctxDi(dbFinto({ ...voce(null), "serate/2026-11-25-2": { stato: "con-prova", dopo: { righe: [{ codice: "G-45" }], prova: { giorno: "2026-11-27", esito: "da-fare" } } } }));
  uguale(R.statoVoce(ctx.voci[0], ctx).testo, "Al lavoro"); uguale(R.dietro(ctx).serate.length, 1, "le serate restano come storico");
});
await caso("Tocca a te: regola unica (domanda, chi Paolo, input della pagina di oggi)", () => {
  const ctx = ctxDi(dbFinto(VERI)), z = R.zoneOggi(ctx);
  uguale(codici(z.tocca), ["G-19", "G-55", "G-35", "G-61"]);
  // la regola della pagina di oggi (waits), con la sua normalizzazione di input
  const norm = t => (t.chi === "Paolo" ? "azione" : t.chi === "Claude" ? "" : (["decisione", "approvazione"].includes(t.input) ? t.input : ""));
  const waits = t => ["da-fare", "in-corso"].includes(t.stato) && (["decisione", "azione"].includes(norm(t)) || t.chi === "Paolo" || (norm(t) === "approvazione" && t.stato === "in-corso" && !!t.domanda));
  uguale(codici(z.tocca).sort(), Object.values(VERI).filter(waits).map(t => t.codice).sort(), "stesse voci della pagina di oggi");
  uguale(R.statoVoce(ctx.perCodice.get("G-35"), ctx).testo, "Tocca a te", "chi Paolo in corso");
  const z2 = R.zoneOggi(ctxDi(dbFinto(OGGI)));
  uguale(codici(z2.tocca), ["G-54", "G-19", "G-65"]); uguale(z2.piano, null); uguale(z2.niente, false); uguale(z2.collegato, false);
});
await caso("la domanda resta in Tocca a te anche se la voce è Ferma", () => {
  const ctx = ctxDi(dbFinto({ "tasks/a": { codice: "G-90", titolo: "Token", stato: "da-fare", ferma: "Manca il token", domanda: "Crea il token con i passi pronti" } }));
  const z = R.zoneOggi(ctx);
  uguale(codici(z.tocca), ["G-90"]); uguale(z.tocca[0].s.testo, "Ferma"); uguale(z.tocca[0].s.causa, "Manca il token"); uguale(z.lavoro.length, 0);
});
await caso("nulla da decidere: una riga sola", () => {
  const z = R.zoneOggi(ctxDi(dbFinto({ "tasks/a": { codice: "G-1", titolo: "a", stato: "in-corso", chi: "Claude" } })));
  uguale(z.niente, true); uguale(codici(z.lavoro), ["G-1"]);
});
await caso("capo sviluppo non collegato: niente tasti che lanciano, Togli e appunti restano", async () => {
  const f = dbFinto({ ...OGGI, "meta/piano": { settimana: "2026-11-28", voci: ["G-12"], tolte: [], via: null } });
  const z = R.zoneOggi(ctxDi(f)); uguale(z.collegato, false); vero(z.piano, "il piano si vede");
  const r = await R.premi(dip(f, mcpFinto({ "Claude Code Remote": "ok" })), { tipo: "margine" });
  uguale(r.esito, "coda"); uguale(r.errore, "capo-assente");
  uguale((await R.togli(dip(f, null), "G-12", "2026-11-28")).esito, "scritto");
  uguale(R.zoneOggi(ctxDi(dbFinto(conCapo(OGGI)))).collegato, true);
});
await caso("piano proposto: Togli scrive solo un clic, Via al piano lancia", async () => {
  const f = dbFinto(conCapo({ ...OGGI, "meta/piano": { settimana: "2026-11-28", voci: ["G-12", "G-58"], tolte: [], via: null } }));
  let ctx = ctxDi(f), z = R.zoneOggi(ctx);
  uguale(codici(z.piano.voci), ["G-12", "G-58"]); uguale(R.statoVoce(ctx.perCodice.get("G-12"), ctx).testo, "In piano");
  const m = mcpFinto({ "Claude Code Remote": "ok" });
  const t = await R.togli(dip(f, m), "G-58", "2026-11-28");
  uguale(t.esito, "scritto"); uguale(m.chiamate.length, 0, "Togli non lancia nulla");
  uguale(f.dati.get("meta/piano").tolte, [], "la pagina non scrive mai meta/piano");
  vero(f.scritture.every(s => s.path !== "meta/piano"), "nessuna scrittura su meta/piano");
  ctx = ctxDi(f); z = R.zoneOggi(ctx); uguale(codici(z.piano.voci), ["G-12"], "la voce con un Togli aperto sparisce dal piano");
  uguale(R.statoVoce(ctx.perCodice.get("G-58"), ctx).testo, "Più avanti");
  // il capo sviluppo scarta il Togli: la voce torna e l'esito resta in Oggi
  Object.assign(f.dati.get("clic/" + t.id), { esito: "scartato", nota: "Serve per il rilascio di domenica", chiuso: "2026-11-26T17:50:00+01:00" });
  z = R.zoneOggi(ctxDi(f)); uguale(codici(z.piano.voci), ["G-12", "G-58"]); uguale(z.esiti.map(e => e.testo), ["Non eseguito: Serve per il rilascio di domenica"]);
  const v = await R.premi(dip(f, m), { tipo: "via-piano", piano: "2026-11-28" });
  uguale(v.esito, "partito");
  ctx = ctxDi(f); z = R.zoneOggi(ctx);
  vero(z.piano.clic && z.piano.clic.id === v.id, "il piano mostra il clic, il tasto sparisce");
  uguale(R.statoVoce(ctx.perCodice.get("G-12"), ctx).testo, "In coda");
  uguale(m.chiamate[0].input, { trigger_id: "trig_finto", text: "clic/" + v.id }, "nel testo solo il codice del clic");
  f.dati.get("meta/piano").via = { quando: "x" }; uguale(R.zoneOggi(ctxDi(f)).piano, null);
});
await caso("piano di una settimana passata e mai avviato: va in Dietro le quinte", () => {
  const f = dbFinto(conCapo({ ...OGGI, "meta/piano": { settimana: "2026-11-14", voci: ["G-58"], tolte: [], via: null } }));
  const ctx = ctxDi(f); uguale(R.zoneOggi(ctx).piano, null); uguale(R.statoVoce(ctx.perCodice.get("G-58"), ctx).testo, "Più avanti");
  vero(R.dietro(ctx).scaduto.startsWith("Piano scaduto"), "riga del piano scaduto");
});
await caso("un solo nome del connettore, quello verificato dal vivo", async () => {
  const f = dbFinto(conCapo(OGGI)), m = mcpFinto({ "Claude_Code_Remote": "ok" });
  const r = await R.premi(dip(f, m), { tipo: "margine" });
  uguale(m.chiamate.map(c => c.nome), ["Claude Code Remote"]); vero(r.esito !== "partito", "con un nome diverso non parte");
});
await caso("lancio fallito: il clic resta e va in coda con l'orario del giro", async () => {
  const f = dbFinto(conCapo(OGGI)), m = mcpFinto({ "Claude Code Remote": "tool_error" });
  const r = await R.premi(dip(f, m), { tipo: "ok", voce: "G-54" });
  uguale(r.esito, "coda"); uguale(m.chiamate.length, 1, "un errore vero non prova l'altro nome");
  const c = f.dati.get("clic/" + r.id); uguale(c.esito, "da-eseguire"); uguale(R.statoClic(c, ctxDi(f)).testo, "In coda: parte al giro delle 19:47.");
  const g = dbFinto({ ...OGGI, "meta/capo": { attivita: "t" } });
  vero(!/prossimo giro/.test(R.statoClic(c, ctxDi(g)).testo), "mai prossimo giro senza orario");
});
await caso("mcp assente, o mcp che risponde in ritardo", async () => {
  const f = dbFinto(conCapo(OGGI));
  const r = await R.premi(dip(f, null), { tipo: "margine" });
  uguale(r.esito, "coda"); uguale(r.errore, "mcp-assente"); vero(f.dati.has("clic/" + r.id));
  const m = mcpFinto({ "Claude Code Remote": "ok" });
  const lento = new Promise(res => setTimeout(() => res(m), 30));
  const s = await R.premi({ ...dip(f, null), mcp: lento }, { tipo: "margine" });
  uguale(s.esito, "partito", "il clic aspetta la risposta del connettore");
});
await caso("errori del connettore distinti: il clic non basta ancora", async () => {
  const f = dbFinto(conCapo(OGGI));
  const casi = { needs_reauth: "Ricollega", server_not_connected: "Ricollega", approval_required: "permesso", consent_required: "permesso", not_in_manifest: "permesso", selection_required: "Scegli", blocked_by_policy: "impostazioni" };
  for (const [code, parola] of Object.entries(casi)) {
    const r = await R.premi(dip(f, mcpFinto({ "Claude Code Remote": code, "Claude_Code_Remote": code })), { tipo: "margine" });
    const s = R.statoClic(f.dati.get("clic/" + r.id), ctxDi(f));
    uguale(r.esito, "bloccato", code); vero(s.testo.includes(parola) && s.ripeti && s.testo.includes("19:47"), code + ": " + s.testo);
  }
  const r = await R.premi(dip(f, mcpFinto({ "Claude Code Remote": "cancelled" })), { tipo: "margine" });
  uguale(r.esito, "coda");
});
await caso("esito incerto: niente ritentativi da soli, poi Riprova sullo stesso clic", async () => {
  const f = dbFinto(conCapo(OGGI)), m = mcpFinto({ "Claude Code Remote": "upstream_error" });
  const r = await R.premi(dip(f, m), { tipo: "indietro", voce: "Due rami" });
  uguale(r.esito, "incerto"); uguale(m.chiamate.length, 1);
  const st = R.statoClic(f.dati.get("clic/" + r.id), ctxDi(f)); uguale(st.tipo, "incerto"); uguale(st.riprova, true);
  const prima = [...f.dati.keys()].filter(k => k.startsWith("clic/")).length;
  const r2 = await R.lancia(dip(f, mcpFinto({ "Claude Code Remote": "ok" })), r.id);
  uguale(r2.esito, "partito"); uguale([...f.dati.keys()].filter(k => k.startsWith("clic/")).length, prima, "nessun clic nuovo");
  uguale((await R.premi(dip(f, mcpFinto({ "Claude Code Remote": "server_unavailable" })), { tipo: "margine" })).esito, "incerto");
});
await caso("Partito che non viene preso in carico scade dopo la soglia", async () => {
  const f = dbFinto(conCapo(OGGI));
  const r = await R.premi(dip(f, mcpFinto({ "Claude Code Remote": "ok" })), { tipo: "margine" });
  const c = f.dati.get("clic/" + r.id);
  const tra = min => R.contesto(f.raw(), new Date(ORA.getTime() + min * 60000));
  uguale(R.statoClic(c, tra(R.PRESA_MIN - 1)).tipo, "partito");
  const s = R.statoClic(c, tra(R.PRESA_MIN + 1)); uguale([s.testo, s.riprova], ["Non ancora preso in carico.", true]);
  c.esito = "in-lavoro"; uguale(R.statoClic(c, tra(60)).testo, "Al lavoro.");
});
await caso("lancio riuscito ma non salvato: resta Partito", async () => {
  const f = dbFinto(conCapo(OGGI));
  f.guasti.push({ op: "update", path: "clic/", code: "resource_exhausted" });
  const r = await R.premi(dip(f, mcpFinto({ "Claude Code Remote": "ok" })), { tipo: "ok", voce: "G-19" });
  uguale(r.esito, "partito"); vero(!f.dati.get("clic/" + r.id).lancio, "lancio non salvato");
  const ctx = R.contesto({ ...f.raw(), lanci: { [r.id]: r.lancio } }, ORA);
  uguale(R.statoClic(ctx.clic.find(c => c.id === r.id), ctx).testo, "Partito adesso.");
});
await caso("snapshot in ritardo: l'esito si dice subito e il tasto non torna", async () => {
  const f = dbFinto(conCapo(OGGI));
  const r = await R.premi(dip(f, mcpFinto({ "Claude Code Remote": "ok" })), { tipo: "margine" });
  const vecchio = R.contesto({ ...OGGI, "meta/capo": undefined, capo: { attivita: "t", giro: "19:47" } }, ORA); // snapshot non ancora arrivato
  const s = R.vistaClic(null, r, vecchio); vero(s && s.testo === "Partito adesso.", "esito subito: " + (s && s.testo));
  uguale(R.vistaClic(null, { id: "x", esito: "non-scritto" }, vecchio), null, "clic non scritto: il tasto torna");
  f.dati.get("clic/" + r.id).esito = "eseguito";
  uguale(R.vistaClic(null, r, ctxDi(f)), null, "confermato ed eseguito: il tasto torna, con l'esito in Oggi");
});
await caso("clic non scritto: non si lancia nulla", async () => {
  const f = dbFinto(conCapo(OGGI)), m = mcpFinto({ "Claude Code Remote": "ok" });
  f.guasti.push({ op: "set", path: "clic/", code: "quota_exceeded" });
  const r = await R.premi(dip(f, m), { tipo: "via-piano", piano: "2026-11-28" });
  uguale(r.esito, "non-scritto"); uguale(m.chiamate.length, 0);
  f.guasti.push({ op: "set", path: "clic/", code: "unavailable" });
  uguale((await R.premi(dip(f, m), { tipo: "margine" })).esito, "partito", "unavailable si ritenta una volta sola");
});
await caso("voce Da vedere: Ok e Non ancora, poi esiti in Oggi", async () => {
  const dati = conCapo({ "tasks/g-x": { codice: "G-70", titolo: "Pagine nuove", stato: "pronta", domanda: "Guarda e dimmi", lettore: "Pagine nuove sul sito", anteprima: "https://esempio.it/a", livello: "visto" },
    "tasks/g-y": { codice: "G-71", titolo: "Altro", stato: "pronta", domanda: "Dimmi", anteprima: "javascript:alert(1)" } });
  const f = dbFinto(dati), m = mcpFinto({ "Claude Code Remote": "ok" });
  let z = R.zoneOggi(ctxDi(f));
  uguale(z.tocca.filter(x => x.vedere).map(x => x.v.codice), ["G-70", "G-71"]); uguale(z.tocca[1].v.anteprima, "", "link non https scartato");
  const ok = await R.premi(dip(f, m), { tipo: "ok", voce: "G-70", testo: "va bene" });
  const no = await R.premi(dip(f, m), { tipo: "non-ancora", voce: "G-71" });
  uguale([ok.esito, no.esito], ["partito", "partito"]);
  z = R.zoneOggi(ctxDi(f)); vero(z.tocca.every(x => x.clic), "dopo il clic i tasti spariscono");
  f.dati.get("clic/" + ok.id).esito = "in-lavoro";
  let ctx = ctxDi(f); uguale(R.statoVoce(ctx.perCodice.get("G-70"), ctx).testo, "Tocca a te", "la domanda c'è ancora");
  Object.assign(f.dati.get("clic/" + no.id), { esito: "scartato", nota: "La voce era cambiata" });
  z = R.zoneOggi(ctxDi(f)); uguale(z.tocca.find(x => x.v.codice === "G-71").clic, null);
  uguale(z.esiti.map(e => e.nome + ": " + e.testo), ["Non ancora: Non eseguito: La voce era cambiata"]);
  uguale(R.zoneOggi(R.contesto({ ...f.raw(), chiusi: [no.id] }, ORA)).esiti.length, 0, "chiuso da Paolo");
  uguale(R.zoneOggi(R.contesto(f.raw(), new Date(ORA.getTime() + 25 * 3600000))).esiti.length, 0, "dopo 24 ore");
});
await caso("margine con e senza percentuale", async () => {
  uguale(R.margineTesto("30"), "30%"); uguale(R.margineTesto(" 45 % "), "45%"); uguale(R.margineTesto(""), ""); uguale(R.margineTesto("tanto"), ""); uguale(R.margineTesto("130"), "");
  const f = dbFinto(conCapo(OGGI)), m = mcpFinto({ "Claude Code Remote": "ok" });
  const a = await R.premi(dip(f, m), { tipo: "margine", testo: R.margineTesto("30") });
  uguale(f.dati.get("clic/" + a.id).testo, "30%"); vero(R.zoneOggi(ctxDi(f)).margine, "margine in corso: niente doppio clic");
  Object.assign(f.dati.get("clic/" + a.id), { esito: "eseguito", nota: "Lavorate G-41 e G-58" });
  const z = R.zoneOggi(ctxDi(f)); uguale(z.margine, null); uguale(z.esiti[0].testo, "Fatto: Lavorate G-41 e G-58");
  const b = await R.premi(dip(f, m), { tipo: "margine", testo: R.margineTesto("") }); uguale(f.dati.get("clic/" + b.id).testo, "");
});
await caso("riserva: filtro e coda dopo il margine", async () => {
  const f = dbFinto(conCapo({ ...OGGI, "tasks/g-r": { codice: "G-80", titolo: "Test di scrittura", stato: "da-fare", priorita: "low", riserva: true, ordine: 1 } }));
  uguale(codici(R.elenco(ctxDi(f), "priorita", "riserva")), ["G-80"]); uguale(codici(R.zoneOggi(ctxDi(f)).riserva), ["G-80"]);
  await R.premi(dip(f, mcpFinto({ "Claude Code Remote": "ok" })), { tipo: "margine" });
  const ctx = ctxDi(f); uguale(R.statoVoce(ctx.perCodice.get("G-80"), ctx).testo, "In coda");
});
await caso("appunto: scritto nel database, nessun lancio", async () => {
  const f = dbFinto(OGGI), m = mcpFinto({ "Claude Code Remote": "ok" });
  uguale((await R.aggiungiAppunto(dip(f, m), "   ")).esito, "vuoto");
  const r = await R.aggiungiAppunto(dip(f, m), "La homepage ha troppo spazio");
  uguale(r.esito, "salvato"); uguale(m.chiamate.length, 0);
  const c = f.dati.get("clic/" + r.id); uguale(c.tipo, "appunto"); uguale(c.testo, "La homepage ha troppo spazio");
  uguale(f.dati.get(c.rif).stato, "nuovo"); uguale(R.zoneOggi(ctxDi(f)).appunti.length, 1);
});
await caso("ordinamento per priorità e per ordine di lavoro", () => {
  const ctx = ctxDi(dbFinto(OGGI));
  uguale(codici(R.elenco(ctx, "priorita", "aperte")), ["G-45", "G-54", "G-19", "G-65", "G-58", "G-12", "G-50"]);
  uguale(codici(R.elenco(ctx, "lavoro", "aperte")), ["G-45", "G-54", "G-12", "G-19", "G-65", "G-58", "G-50"]);
  uguale(R.elenco(ctx, "lavoro", "aperte")[0].pos, 1);
});
await caso("scadenze: visibili e, a parità di priorità, prima la più vicina", () => {
  const ctx = ctxDi(dbFinto(VERI));
  const med = R.elenco(ctx, "priorita", "aperte").filter(x => x.v.priorita === "medium").map(x => x.v.codice);
  uguale(med.slice(0, 2), ["G-49", "G-41"], "scadenza 9/12 prima di 24/12, poi senza scadenza");
  uguale(R.elenco(ctx, "priorita", "aperte").find(x => x.v.codice === "G-41").entro, "entro il 24/12");
  const f = dbFinto(conCapo({ ...VERI, "meta/piano": { settimana: "2026-11-28", voci: ["G-41"], tolte: [], via: null } }));
  uguale(R.zoneOggi(ctxDi(f)).piano.voci[0].entro, "entro il 24/12");
});
await caso("i quattro filtri, la ricerca e il conteggio delle aperte", () => {
  const ctx = ctxDi(dbFinto({ ...OGGI, "tasks/g-r": { codice: "G-80", titolo: "r", riserva: true, priorita: "low", decisioni: "- usare il glossario" } }));
  uguale(codici(R.elenco(ctx, "priorita", "idee")), ["G-62", "G-07"]);
  uguale(codici(R.elenco(ctx, "priorita", "fatte")), ["G-33"]);
  uguale(codici(R.elenco(ctx, "priorita", "riserva")), ["G-80"]);
  uguale(R.nAperte(ctx), 8);
  uguale(codici(R.elenco(ctx, "priorita", "aperte", "GLOSSARIO")), ["G-80", "G-07"], "cerca in decisioni e titolo, su tutte le voci");
  uguale(codici(R.elenco(ctx, "lavoro", "fatte", "homepage")), ["G-33"]);
  uguale(codici(R.elenco(ctx, "priorita", "aperte", "Homepage")), ["G-33"], "con una ricerca il filtro non vale");
  const c2 = R.contesto({ tasks: { a: { codice: "G-1", titolo: "Perché sì", stato: "da-fare" }, b: { codice: "G-2", titolo: "b", domanda: "Città nuova?" }, c: { codice: "G-3", titolo: "c", lettore: "Pagine più leggere" }, d: { codice: "G-4", titolo: "d" } } }, ORA);
  uguale(codici(R.elenco(c2, "priorita", "aperte", "perche")), ["G-1"], "senza accenti");
  uguale(codici(R.elenco(c2, "priorita", "aperte", "citta")), ["G-2"], "nella domanda");
  uguale(codici(R.elenco(c2, "priorita", "aperte", "leggere")), ["G-3"], "nel lettore");
  uguale(codici(R.elenco(c2, "priorita", "aperte", "scrivere")), [], "non nel 'Da scrivere' di ripiego");
  uguale(codici(R.elenco(ctx, "priorita", "aperte", "g-65")), ["G-65"], "cerca il codice");
});
await caso("conteggi delle viste: aperte, idee e fatte coprono tutte le voci", () => {
  const ctx = ctxDi(dbFinto(VERI)), n = k => R.elenco(ctx, "priorita", k).length;
  uguale(n("aperte") + n("idee") + n("fatte"), ctx.voci.length);
});
await caso("due scrittori: la pagina non riscrive mai ciò che scrive il capo sviluppo", async () => {
  const f = dbFinto(conCapo({ ...OGGI, "meta/piano": { settimana: "2026-11-28", voci: ["G-12", "G-58"], tolte: [], via: null } }));
  const m = mcpFinto({ "Claude Code Remote": "ok" });
  const vecchio = R.zoneOggi(ctxDi(f)).piano.settimana;
  f.dati.set("meta/piano", { settimana: "2026-12-05", voci: ["G-58"], tolte: [], via: null }); // il capo riscrive il piano
  await R.togli(dip(f, m), "G-58", vecchio);
  await R.premi(dip(f, m), { tipo: "ok", voce: "G-19" });
  await R.aggiungiAppunto(dip(f, m), "x");
  uguale(f.dati.get("meta/piano"), { settimana: "2026-12-05", voci: ["G-58"], tolte: [], via: null }, "piano intatto");
  vero(f.scritture.every(s => /^(clic|appunti)\//.test(s.path)), "scrive solo clic e appunti");
  vero(f.scritture.filter(s => s.op === "update").every(s => Object.keys(s.d).join() === "lancio"), "sui clic aggiorna solo lancio");
    uguale(codici(R.zoneOggi(R.contesto(f.raw(), new Date("2026-12-04T20:00:00+01:00"))).piano.voci), ["G-58"], "il Togli del piano vecchio non vale per il piano nuovo");
});
await caso("valori strani dal database", () => {
  const v = R.normVoce("x", { codice: "G-1", stato: "bloccata", priorita: "urgente", ordine: "", giorno: "26/11/2026", livello: "boh", anteprima: " https://a.it/x\" onerror=x " });
  uguale([v.stato, v.priorita, v.ordine, v.giorno, v.livello, v.anteprima], ["da-fare", "medium", 999, "", "visto", ""]);
  uguale(["javascript:alert(1)", "data:text/html,x", "HTTPS://a.it", "https://a.it\njavascript:x", "https://a.it/ok"].map(u => R.normVoce("x", { anteprima: u }).anteprima), ["", "", "", "", "https://a.it/ok"]);
});
await caso("link nelle domande: solo https, la punteggiatura resta fuori", () => {
  uguale(R.pezziTesto("Vedi https://claude.ai/artifact/CD12. Poi javascript:alert(1) e (https://a.it/x)"),
    [{ testo: "Vedi " }, { link: "https://claude.ai/artifact/CD12" }, { testo: ". Poi javascript:alert(1) e (" }, { link: "https://a.it/x" }, { testo: ")" }]);
});
await caso("fire_trigger riceve solo il codice del clic, mai il testo di Paolo", async () => {
  const f = dbFinto(conCapo(OGGI)), m = mcpFinto({ "Claude Code Remote": "ok" });
  const r = await R.premi(dip(f, m), { tipo: "non-ancora", voce: "G-19", testo: "nota privata" });
  uguale(m.chiamate[0].input, { trigger_id: "trig_finto", text: "clic/" + r.id });
});
await caso("Torna indietro: sull'ultimo rilascio andato in linea", () => {
  const f = dbFinto({ ...OGGI, "meta/salute": { rilasci: [{ esito: "ko", nome: "Rotto", quando: "2026-11-26T10:00:00+01:00" }, { esito: "ok", nome: "Due rami", quando: "2026-11-25T18:48:00+01:00" }] } });
  uguale(R.zoneOggi(ctxDi(f)).ultimo.nome, "Due rami");
});
await caso("ferma con la causa, link della chat, modello e sforzo", () => {
  const ctx = ctxDi(dbFinto({ "tasks/a": { codice: "G-9", titolo: "a", stato: "in-corso", chi: "Claude", ferma: "Manca il token di Cloudflare" } }));
  const s = R.statoVoce(ctx.voci[0], ctx); uguale([s.testo, s.causa], ["Ferma", "Manca il token di Cloudflare"]);
  uguale(R.chatURL("G-65"), "https://claude.ai/new?q=Gommberg%2C%20voce%20G-65%3A%20");
  uguale(R.comeSiLavora(R.normVoce("x", { modello: "Sonnet", sforzo: "medium" })), "Sonnet, sforzo medio");
});
await caso("dietro le quinte: salute, serate, consensi, giornale", async () => {
  const f = dbFinto({ ...conCapo(OGGI), "meta/stato": { lettori: "10 lettori", edizioni: "33 edizioni", prossimo: "venerdì la prova" } });
  await R.premi(dip(f, null), { tipo: "margine", testo: "20%" });
  const d = R.dietro(ctxDi(f));
  uguale(d.vecchia, false, "verifica di 23 ore fa"); uguale(d.serate.length, 2); uguale(d.consensi.length, 1); uguale(d.conta.margine, 1);
  uguale(d.consensi[0].lancio, "coda"); uguale(d.giornale, "10 lettori · 33 edizioni · Prossimo: venerdì la prova");
  f.dati.get("meta/salute").verificato = "2026-11-24T10:00:00+01:00"; uguale(R.dietro(ctxDi(f)).vecchia, true, "verifica di più di 26 ore fa");
});
await caso("clic in lavoro senza segnale: Fermo da, con Riprova", () => {
  const preso = agg => ({ tipo: "margine", esito: "in-lavoro", quando: "2026-11-26T15:00:00Z", preso: { quando: "2026-11-26T15:00:00Z", aggiornato: agg } });
  let f = dbFinto(conCapo({ "clic/c1": preso("2026-11-26T16:40:00Z") })); // 20 minuti fa
  uguale(R.statoClic(f.dati.get("clic/c1"), ctxDi(f)).testo, "Al lavoro.");
  f = dbFinto(conCapo({ "clic/c1": preso("2026-11-26T15:30:00Z") })); // 90 minuti fa
  const s = R.statoClic(f.dati.get("clic/c1"), ctxDi(f)); uguale([s.testo, s.riprova], ["Fermo da 90 minuti: nessun segnale.", true]);
  f = dbFinto(conCapo({ "clic/c1": { tipo: "margine", esito: "in-lavoro", quando: "2026-11-23T17:00:00Z" } })); // sessione morta prima di scrivere preso
  uguale(R.statoClic(f.dati.get("clic/c1"), ctxDi(f)).testo, "Fermo da 3 giorni: nessun segnale.");
});
await caso("un clic aspetta il lavoro in corso, senza la scadenza dei 15 minuti", async () => {
  const f = dbFinto(conCapo({ ...OGGI, "clic/c0": { tipo: "via-piano", esito: "in-lavoro", quando: "2026-11-26T16:00:00Z", preso: { quando: "2026-11-26T16:00:00Z", aggiornato: "2026-11-26T16:50:00Z" } } }));
  const r = await R.premi(dip(f, mcpFinto({ "Claude Code Remote": "ok" })), { tipo: "margine" });
  const tra = min => R.contesto(f.raw(), new Date(ORA.getTime() + min * 60000));
  uguale(R.statoClic(f.dati.get("clic/" + r.id), tra(1)).testo, "In coda: parte appena finisce il lavoro in corso.");
  uguale(R.statoClic(f.dati.get("clic/" + r.id), tra(40)).testo, "In coda: parte appena finisce il lavoro in corso.", "nessuna scadenza mentre l'altro lavora");
  uguale(R.statoClic(f.dati.get("clic/" + r.id), tra(70)).tipo, "non-preso", "l'altro tace da più di 60 minuti: torna la scadenza");
});
await caso("un Togli vale solo per il piano in cui è stato dato", async () => {
  const f = dbFinto(conCapo({ ...OGGI, "meta/piano": { settimana: "2026-11-28", voci: ["G-58", "G-12"], tolte: [], via: null } }));
  await R.togli(dip(f, null), "G-58", "2026-11-28");
  uguale(codici(R.zoneOggi(ctxDi(f)).piano.voci), ["G-12"]);
  f.dati.set("meta/piano", { settimana: "2026-12-05", voci: ["G-58", "G-12"], tolte: [], via: null });
  const ctx = R.contesto(f.raw(), new Date("2026-12-04T20:00:00+01:00"));
  uguale(codici(R.zoneOggi(ctx).piano.voci), ["G-58", "G-12"], "il Togli vecchio non nasconde la voce nel piano nuovo");
  uguale(R.statoVoce(ctx.perCodice.get("G-58"), ctx).testo, "In piano");
});
await caso("Tocca a te compatto: Da vedere in scheda, le altre in righe, scadenze vicine in cima", () => {
  const dati = conCapo({ ...OGGI,
    "tasks/u1": { codice: "G-81", titolo: "Auguri", chi: "Paolo", priorita: "low", ordine: 90, scadenza: "2026-12-09" },
    "tasks/u2": { codice: "G-82", titolo: "Token", chi: "Paolo", priorita: "medium", ordine: 1, scadenza: "2026-12-01" },
    "tasks/u3": { codice: "G-83", titolo: "Lontana", chi: "Paolo", priorita: "low", ordine: 2, scadenza: "2027-01-31" },
    "tasks/v1": { codice: "G-84", titolo: "Pagine", stato: "pronta", domanda: "Guarda", priorita: "low" },
    "meta/piano": { settimana: "2026-11-28", voci: ["G-12"], tolte: [], via: null } });
  const z = R.zoneOggi(ctxDi(dbFinto(dati)));
  uguale(codici(z.vedere), ["G-84"]);
  uguale(codici(z.richieste), ["G-82", "G-81", "G-54", "G-19", "G-65", "G-83"], "entro 14 giorni prima (la più vicina), poi priorità, poi ordine");
  uguale(z.nTocca, 8, "richieste, voci da vedere e piano");
  uguale(R.RICHIESTE_VISIBILI, 5); uguale(R.URGENZA_GIORNI, 14);
});
await caso("l'anteprima trova ancora la riga che sostituisce", () => {
  vero(html.includes("window.claude && window.claude.use ? await window.claude.use(n) : null"), "riga cercata da anteprima.mjs");
});
await caso("la pagina: niente innerHTML, testi lunghi che vanno a capo, niente trattini lunghi", () => {
  vero(!/innerHTML|insertAdjacentHTML|outerHTML/.test(html), "mai HTML costruito da stringhe");
  vero(/overflow-wrap:anywhere/.test(html), "overflow-wrap");
  vero(!/[\u2013\u2014]/.test(html));
  vero(/Tutti i lavori · " \+ R\.nAperte\(ctx\) \+ " aperte"/.test(html), "etichetta con aperte");
});

console.log("\n" + passate + " casi passati, " + fallite + " falliti");
process.exit(fallite ? 1 : 0);
