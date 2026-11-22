/* Gommberg Terminal Daily - il GOMM, la quotazione del Gommberg. Un solo calcolo per tutto il sito (G-14).
   Il GOMM è un indice: la media delle visite degli ultimi 7 giorni, con 100 = media della settimana 17-23 ottobre 2026,
   un decimale. La chiusura è quella dell'ultimo giorno completo; il giorno in corso è provvisorio.
   Dati: dati/gomm.json (giorni completi, aggiornato ogni mattina da redazione/gomm.py) più, per i giorni dopo il file
   e per oggi, i contatori pubblici di GoatCounter: poche richieste anche tra un anno.
   GOMM.carica()            -> Promise di { base, giorni: [{d, v, i}], oggi: {d, v, i} | null, ieri, prima } (o null)
   GOMM.conta(path, a, b)   -> Promise del numero di visite (o eventi) tra i giorni a e b inclusi, null se non risponde
   GOMM.orario(cb)          -> cb(Date del dato, Date del prossimo aggiornamento) appena il contatore manda la scadenza
   GOMM.num(x), GOMM.pct(a, b), GOMM.dt("AAAA-MM-GG")   formattazione italiana e date (mezzogiorno UTC) */
(function () {
  "use strict";
  const GC = "https://gommberg.goatcounter.com/counter/";
  const DAL = "2026-10-17", GIORNI_BASE = 7;            // la settimana base: 17-23 ottobre
  const SRC = (document.currentScript && document.currentScript.src) || location.href;
  const FILE = new URL("../dati/gomm.json", SRC).href;   // lo script sta in assets/

  const iso = (d) => d.toISOString().slice(0, 10);
  const dt = (s) => new Date(s + "T12:00:00Z");
  const piu = (s, n) => { const d = dt(s); d.setUTCDate(d.getUTCDate() + n); return iso(d); };
  const oggiRoma = () => new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Rome" }).format(new Date());
  const num = (x) => Number(x).toLocaleString("it-IT", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const pct = (a, b) => { const c = (a / b - 1) * 100; return (c >= 0 ? "+" : "-") + num(Math.abs(c)) + "%"; };

  // GoatCounter non conta il giorno indicato in "end" (verificato il 21/11/2026): alla richiesta si manda il giorno dopo.
  // Al massimo 6 richieste insieme; un secondo tentativo dopo 800 ms; 404 = contatore senza visite = 0.
  let attive = 0; const coda = [];
  const turno = () => new Promise((ok) => { if (attive < 6) { attive++; ok(); } else coda.push(ok); });
  const libera = () => { const n = coda.shift(); if (n) n(); else attive--; };
  // GoatCounter tiene ogni risposta 4 ore e ne manda la scadenza (Expires): il dato è di 4 ore prima. Vale il più vecchio.
  const VALIDO = 4 * 3600e3; let scade = null; const ascolta = [];
  function segnaOra(r) {
    const e = Date.parse(r.headers.get("expires") || ""), ora = Date.now();
    if (!(e > ora && e <= ora + VALIDO + 60e3) || (scade && e >= scade)) return;
    scade = e; ascolta.forEach((cb) => cb(new Date(e - VALIDO), new Date(e)));
  }
  function chiedi(url) {
    return fetch(url).then((r) => { if (r.ok) segnaOra(r); return r.ok ? r.json() : (r.status === 404 ? { count: "0" } : Promise.reject(r.status)); })
      .then((j) => parseInt(String(j.count || "0").replace(/\D/g, ""), 10) || 0);
  }
  async function conta(path, start, end) {
    const q = []; if (start) q.push("start=" + start); if (end) q.push("end=" + piu(end, 1));
    const url = GC + encodeURIComponent(path) + ".json" + (q.length ? "?" + q.join("&") : "");
    await turno();
    try { return await chiedi(url); }
    catch (e) { try { await new Promise((ok) => setTimeout(ok, 800)); return await chiedi(url); } catch (e2) { return null; } }
    finally { libera(); }
  }
  function orario(cb) { ascolta.push(cb); if (scade) cb(new Date(scade - VALIDO), new Date(scade)); }

  let promessa = null;
  function carica() { return promessa || (promessa = calcola()); }
  async function calcola() {
    const oggi = oggiRoma(), ieri = piu(oggi, -1);
    let dal = DAL, vis = [];
    try {
      const f = await fetch(FILE, { cache: "no-cache" }).then((r) => r.ok ? r.json() : null);
      if (f && f.dal === DAL && Array.isArray(f.visite)) vis = f.visite.slice(0, Math.max(0, (dt(ieri) - dt(DAL)) / 864e5 + 1));
    } catch (e) { vis = []; }
    // i giorni completi che il file non ha ancora (il fine settimana, o il file assente): dal contatore, uno per giorno
    const mancano = []; for (let d = piu(dal, vis.length); d <= ieri; d = piu(d, 1)) mancano.push(d);
    const [extra, vOggi] = await Promise.all([Promise.all(mancano.map((d) => conta("TOTAL", d, d))), conta("TOTAL", oggi, oggi)]);
    vis = vis.concat(extra);
    const base = vis.slice(0, GIORNI_BASE);
    if (base.length < GIORNI_BASE || base.some((x) => x == null)) return null;
    const B = base.reduce((s, x) => s + x, 0) / GIORNI_BASE;
    if (!B) return null;
    const indice = (xs) => xs.some((x) => x == null) ? null : Math.round(xs.reduce((s, x) => s + x, 0) / xs.length / B * 1000) / 10;
    const giorni = vis.map((v, k) => ({ d: piu(dal, k), v: v, i: k >= GIORNI_BASE - 1 ? indice(vis.slice(k - 6, k + 1)) : null }));
    const oggiG = vOggi == null ? null : { d: oggi, v: vOggi, i: indice(vis.slice(-6).concat([vOggi])), p: true };
    const validi = giorni.filter((g) => g.i != null);
    if (validi.length < 2) return null;
    return { base: B, giorni: giorni, oggi: oggiG, ieri: validi[validi.length - 1], prima: validi[validi.length - 2] };
  }

  window.GOMM = { carica, conta, orario, num, pct, dt, iso, piu };
})();
