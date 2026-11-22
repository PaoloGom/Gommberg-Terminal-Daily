// Un database D1 finto sopra SQLite di Node (node:sqlite, Node 22.5 o più): le sole chiamate che usa il servizio dei
// lettori (prepare, bind, first, all, run, batch). Serve al collaudo (prova_lettori.mjs) e alle prove in locale con il
// servizio vero (servi_lettori.mjs). Non va mai su Cloudflare: lì il database è D1.
import { DatabaseSync } from "node:sqlite";

export function d1(file = ":memory:") {
  const db = new DatabaseSync(file);
  const stmt = (sql, arg = []) => ({
    bind: (...a) => stmt(sql, a),
    _esegui() { const s = db.prepare(sql); return /^\s*(select|with)|returning/i.test(sql) ? { rows: s.all(...arg) } : { info: s.run(...arg) }; },
    async first() { const r = this._esegui().rows; return r && r.length ? { ...r[0] } : null; },
    async all() { return { results: (this._esegui().rows || []).map((r) => ({ ...r })) }; },
    async run() { this._esegui(); return { success: true }; },
  });
  return { prepare: (sql) => stmt(sql), batch: async (lista) => { db.exec("BEGIN"); try { const r = lista.map((s) => s._esegui()); db.exec("COMMIT"); return r; } catch (e) { db.exec("ROLLBACK"); throw e; } }, _db: db };
}
