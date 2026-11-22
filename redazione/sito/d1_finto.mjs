// Un database D1 finto sopra SQLite di Node (node:sqlite, Node 22.5 o più): le sole chiamate che usa il servizio dei
// lettori (prepare, bind, first, all, run, batch). Serve al collaudo (prova_lettori.mjs) e alle prove in locale con il
// servizio vero (servi_lettori.mjs). Non va mai su Cloudflare: lì il database è D1.
import { DatabaseSync } from "node:sqlite";

export function d1(file = ":memory:") {
  const db = new DatabaseSync(file);
  // api.latenza (millisecondi, di norma 0): ogni chiamata aspetta un tempo a caso, come le chiamate di rete di D1 vero.
  // Serve alle prove con richieste contemporanee: senza attese le istruzioni di una richiesta non si intrecciano mai.
  const attesa = () => (api.latenza ? new Promise((ok) => setTimeout(ok, Math.random() * api.latenza)) : null);
  const stmt = (sql, arg = []) => ({
    bind: (...a) => stmt(sql, a),
    _esegui() { const s = db.prepare(sql); return /^\s*(select|with)|returning/i.test(sql) ? { rows: s.all(...arg) } : { info: s.run(...arg) }; },
    async first() { await attesa(); const r = this._esegui().rows; return r && r.length ? { ...r[0] } : null; },
    async all() { await attesa(); return { results: (this._esegui().rows || []).map((r) => ({ ...r })) }; },
    async run() { await attesa(); this._esegui(); return { success: true }; },
  });
  const api = { latenza: 0, prepare: (sql) => stmt(sql), batch: async (lista) => { await attesa(); db.exec("BEGIN"); try { const r = lista.map((s) => s._esegui()); db.exec("COMMIT"); return r; } catch (e) { db.exec("ROLLBACK"); throw e; } }, _db: db };
  return api;
}
