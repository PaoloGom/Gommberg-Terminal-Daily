/* Gommberg Terminal Daily - La Gommunity (G-13): il sentiment di oggi (Toro/Orso, le percentuali compaiono quando voti),
   i commenti con la targhetta del sentiment, le risposte a un livello, i like e Segnala. La stessa sezione in homepage
   (accanto all'edizione) e nelle pagine e/NNN.html. Stile in assets/lettori.css; i dati li tiene il servizio /api/lettori/
   su Cloudflare (nella redazione: sito/lettori.js).

   LETTORI.monta(elemento, edizione)  disegna la sezione dentro l'elemento (un <aside class="lt"> vuoto) per l'edizione
                                      {numero, data}; si richiama a ogni cambio di edizione. Se il servizio non risponde
                                      la pagina resta intera: la sezione dice soltanto che la discussione non si carica.
   Nessuna iscrizione e nessuna email: il nome si scrive in "Firmi come" o si genera con il dado, e lo ricorda il browser,
   come il codice anonimo del lettore (gtd-lettore) che riconosce i suoi commenti, like e voti. Un nome resta di chi l'ha
   usato per primo: mentre lo scegli la sezione chiede al servizio se è libero, e il dado ne propone solo di liberi. */
(function () {
  "use strict";
  var API = "/api/lettori/";
  var LAB = { toro: "Toro", orso: "Orso" };
  var SEGNO = { toro: "▲", orso: "▼" };
  // I nomi del dado (Paolo 22/11): sempre "Nome Cognome", di finanza, italiani e ironici. Tre livelli che si attivano da
  // soli, così il dado non finisce mai e non va mai toccato:
  //   1. NOMI    i giochi di parole scritti a mano ("Massimo Rischio", "Tito Lare"): escono in ordine casuale, senza
  //              ripetersi finché il lettore non li ha visti tutti;
  //   2. PROPRI x COGNOMI   un nome vero più un cognome finanziario ("Wanda Plusvalenza"): migliaia di combinazioni;
  //   3. se sono presi anche quelli, il nome combinato prende un numero romano ("Gino Spread II"), senza fine.
  // Ogni nome è di un solo lettore: il dado chiede al servizio quali sono liberi (dieci per volta) e propone solo quelli.
  // Le liste si possono allungare aggiungendo parole (il collaudo controlla che il servizio le accetti), ma non serve.
  var NOMI = [
    // nomi veri che sono già finanza
    "Massimo Rischio", "Massimo Storico", "Massimo Ribasso", "Massimo Scoperto", "Franco Svizzero", "Franco Fabbrica", "Marco Tedesco",
    "Euro Dollaro", "Euro Forte", "Germano Bund", "Americo Dollaro", "Italo Btp", "Libero Mercato", "Libero Scambio", "Primo Acconto",
    "Secondo Acconto", "Primo Avanzo", "Secondo Mercato", "Quinto Ceduto", "Otto Permille", "Ultimo Prezzo", "Modesto Rendimento",
    "Generoso Dividendo", "Felice Dividendo", "Benedetto Rimbalzo", "Costante Rialzo", "Onesto Guadagno", "Fortunato Rialzo",
    "Tranquillo Bund", "Sereno Variabile", "Placido Listino", "Severo Fisco", "Clemente Fisco", "Amato Fisco", "Candido Bilancio",
    "Fermo Tasso", "Fedele Cassettista", "Salvo Buonfine", "Donato Rimborso", "Angelo Investitore", "Natale Rally", "Orso Bruno",
    "Toro Seduto", "Fido Bancario", "Bonifacio Bancario", "Bonifacio Istantaneo", "Iva Inclusa", "Iva Partita", "Assunta Posizione",
    "Allegra Finanza", "Bianca Centrale", "Serena Seduta", "Costanza Pac", "Costanza Rata", "Speranza Rimbalzo", "Prudenza Bond",
    "Dolores Minus", "Domenica Trader", "Azzurra Chip", "Augusta Paga", "Lina Sterlina", "Lola Cedola", "Bice Francoforte",
    // nome e cognome che letti insieme fanno una parola
    "Tito Lare", "Tito Lodistato", "Vito Alizio", "Ines Igibile", "Ezio Nista", "Pia Zaffari", "Lino Gotto", "Mimmo Biliare",
    "Gastone Naturale", "Pietro Lio", "Remo Contro", "Guido Piano", "Guido Laborsa", "Mino Ranza", "Mina Svalenza", "Lea Sing",
    "Gia Cenza", "Ali Quota", "Catia Stale", "Viola Tilità", "Mirko Economia", "Corrado Corrente", "Carla Dicredito",
    "Federico Riserva", "Zeno Coupon", "Tobia Tax", "Oronzo Lingotto", "Tullio Tulipano", "Ippolito Ipo", "Torquato Tassofisso",
    "Ponzi Schema", "Ugo Gain", "Marce Long",
    // con un nome inglese
    "Max Drawdown", "Mark Tomarket", "Bill Ancio", "Bud Get", "Ray Ting", "Ben Chmark", "Pat Rimonio", "Al Rialzo", "Al Ribasso",
    "Rob Bot", "Ted Spread", "Sigmund Bund", "Margie Call", "Brent Barile", "Juan Yuan", "Zoe Roe", "Cliff Fiscale", "Art Bitraggio",
    "Don Azione", "Lev Erage", "Dan Aro", "Sol Dini", "Sol Vibile", "Val Uta", "Mo Mentum", "Dee Flazione", "Tess Oretto"];
  var PROPRI = ["Gino", "Ugo", "Pina", "Carla", "Aldo", "Rina", "Nino", "Lella", "Tino", "Bruna", "Elio", "Ada", "Ivo", "Olga", "Remo", "Tea",
    "Dino", "Lia", "Enzo", "Mara", "Rocco", "Nora", "Ciro", "Zita", "Wanda", "Furio", "Nives", "Sergio", "Marisa", "Gianni", "Piero",
    "Gilda", "Renzo", "Lucia", "Mimmo", "Tina", "Pippo", "Iole", "Oreste", "Elsa", "Nando", "Ines", "Cesira", "Gastone", "Ofelia",
    "Arturo", "Irma", "Duilio", "Norma", "Ettore", "Vera", "Achille", "Delia", "Saverio", "Flora", "Lalla", "Tullio", "Mirella",
    "Osvaldo", "Ornella", "Egidio", "Amelia", "Rodolfo", "Clelia", "Ottavio", "Dora", "Silvano", "Agata", "Ercole", "Ida"];
  var COGNOMI = ["Spread", "Cedola", "Bund", "Dividendo", "Rimbalzo", "Listino", "Rendimento", "Tasso", "Bilancio", "Portafoglio", "Rally",
    "Ribasso", "Rialzo", "Lingotto", "Benchmark", "Coupon", "Future", "Capitale", "Interesse", "Bonifico", "Scadenza", "Plusvalenza",
    "Mercato", "Bot", "Btp", "Etf", "Pac", "Azionista", "Risparmio", "Budget", "Fatturato", "Ricavi", "Utile", "Saldo", "Deposito",
    "Mutuo", "Rata", "Cambio", "Valuta", "Indice", "Volume", "Derivato", "Opzione", "Margine", "Inflazione", "Euribor", "Rating",
    "Swap", "Hedge", "Cassa", "Borsa", "Titolo", "Azione", "Obbligazione", "Quotazione", "Liquidità", "Volatilità", "Leva", "Fido",
    "Conto", "Assegno", "Cambiale", "Tesoretto", "Zainetto", "Minusvalenza", "Trimestrale", "Guidance", "Outlook", "Asta", "Fixing",
    "Carry", "Yield"];
  var caso = function (a) { return a[Math.floor(Math.random() * a.length)]; };
  function romano(n) {
    var v = [[1000, "M"], [900, "CM"], [500, "D"], [400, "CD"], [100, "C"], [90, "XC"], [50, "L"], [40, "XL"], [10, "X"], [9, "IX"], [5, "V"], [4, "IV"], [1, "I"]], o = "";
    v.forEach(function (c) { while (n >= c[0]) { o += c[1]; n -= c[0]; } });
    return o;
  }
  // Dieci candidati per volta: otto carte del mazzo non ancora viste e due nomi combinati; finito il mazzo, dieci
  // combinati. Quando un'intera decina di combinati risulta presa il livello sale, e da lì portano il numero romano.
  var MAZZO = null, CODA = [], LIVELLO = 1, volo = null;
  function candidati() {
    if (!MAZZO) { MAZZO = NOMI.slice(); for (var i = MAZZO.length - 1; i > 0; i--) { var k = Math.floor(Math.random() * (i + 1)), t = MAZZO[i]; MAZZO[i] = MAZZO[k]; MAZZO[k] = t; } }
    var out = MAZZO.splice(0, 8), giri = 0;
    while (out.length < 10 && giri++ < 200) {
      var n = caso(PROPRI) + " " + caso(COGNOMI) + (LIVELLO > 1 ? " " + romano(Math.min(LIVELLO, 3999)) : "");
      if (out.indexOf(n) < 0 && CODA.indexOf(n) < 0) out.push(n);
    }
    return out;
  }
  var RISERVATI = /redazion|redatt|gommberg|gommellini|amministra|admin|moderat|staff|direttore|direzion/i;   // gli stessi del servizio
  var AV = ["#F6D7C3", "#D9E8DE", "#DCE3F0", "#EADCF0", "#F0E6C8", "#E3DED7"];
  var CUORE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20.5s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7.6a4.3 4.3 0 0 1 7.5 2.7c0 5.6-7.5 10.2-7.5 10.2Z"/></svg>';
  var DADO = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="3"/><circle cx="9" cy="9" r="1.1"/><circle cx="15" cy="15" r="1.1"/><circle cx="15" cy="9" r="1.1"/><circle cx="9" cy="15" r="1.1"/></svg>';
  var el = function (t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
  var q = function (s, r) { return r.querySelector(s); };
  var pad = function (n) { return String(n).padStart(3, "0"); };
  var leggi = function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } };
  var salva = function (k, v) { try { localStorage.setItem(k, v); } catch (e) { /* navigazione privata: resta per questa visita */ } };
  var bottone = function (c, x, act) { var b = el("button", c, x); b.type = "button"; if (act) b.dataset.act = act; return b; };

  function idLettore() {
    var v = leggi("gtd-lettore");
    if (!v || !/^[a-z0-9-]{16,64}$/i.test(v)) {
      if (window.crypto && crypto.randomUUID) v = crypto.randomUUID();
      else { var b = new Uint8Array(16); crypto.getRandomValues(b); v = Array.prototype.map.call(b, function (x) { return x.toString(16).padStart(2, "0"); }).join(""); }
      salva("gtd-lettore", v);
    }
    return v;
  }
  var ID = idLettore();
  function conta(path, title) {   // statistiche anonime (GoatCounter), come il resto del sito; mai nelle anteprime
    var g = window.goatcounter; if (g && g.count) try { g.count({ path: path, title: title, event: true }); } catch (e) {}
  }

  var S = { ed: null, d: null, stato: "attesa", ord: "top", filtro: "tutti", tutti: false, menu: null, re: null, nuovo: null,
            miei: {}, presa: 0, gen: 0, anima: false, nome: leggi("gtd-nome") || "" };
  var R = null;   // la sezione montata

  /* ---------- Il servizio ---------- */
  function api(metodo, percorso, corpo) {
    var h = { "x-lettore": ID }; if (corpo) h["content-type"] = "application/json";
    return fetch(API + percorso, { method: metodo, headers: h, body: corpo ? JSON.stringify(corpo) : undefined, cache: "no-store", credentials: "same-origin" })
      .then(function (r) {
        return r.json().catch(function () { return null; }).then(function (j) {
          if (!r.ok) { var e = new Error((j && j.errore) || "Il servizio non risponde: riprova tra poco."); e.stato = r.status; throw e; }
          return j;
        });
      }, function () { var e = new Error("Connessione assente: riprova tra poco."); e.stato = 0; throw e; });
  }
  // Le scritture portano il gettone della lettura (il server vuole almeno 3 secondi di pagina aperta) e il campo trappola
  function scrivi(percorso, corpo, giro) {
    var attesa = Math.max(0, S.presa + 3300 - Date.now());
    return new Promise(function (ok) { setTimeout(ok, attesa); }).then(function () {
      var c = Object.assign({}, corpo, { gettone: S.d && S.d.gettone, sito: R ? q(".trappola input", R).value : "" });
      return api("POST", percorso, c).catch(function (e) {
        if (e.stato === 400 && /Ricarica/.test(e.message) && !giro) return carica(true).then(function () { return scrivi(percorso, corpo, 1); });
        throw e;
      });
    });
  }
  // Se la lettura non riesce (rete, servizio che si sveglia) si riprova da sola dopo 2, 5, 15 secondi e poi ogni minuto:
  // un intoppo di un attimo non deve lasciare la sezione vuota fino a quando il lettore ricarica la pagina
  var RIPROVA = [2000, 5000, 15000, 60000], tentativi = 0, timerRiprova = null;
  function carica(quieto) {
    var n = S.ed && S.ed.numero, gen = S.gen; if (!n) return Promise.resolve();
    clearTimeout(timerRiprova);
    return api("GET", pad(n)).then(function (d) {
      if (gen !== S.gen) return;
      tentativi = 0; S.d = d; S.presa = Date.now(); S.stato = "pronto"; rendi();
    }, function () {
      if (gen !== S.gen) return;
      if (!quieto || !S.d) { S.stato = S.d ? "pronto" : "fuori"; rendi(); }
      timerRiprova = setTimeout(function () { if (gen === S.gen) carica(true); }, RIPROVA[Math.min(tentativi++, RIPROVA.length - 1)]);
    });
  }

  /* ---------- Aiuti ---------- */
  function albero() {
    var lista = (S.d && S.d.commenti) || [], radici = [], per = {};
    lista.forEach(function (c) { per[c.id] = Object.assign({}, c, { r: [] }); });
    lista.forEach(function (c) { var x = per[c.id]; if (c.padre && per[c.padre]) per[c.padre].r.push(x); else if (!c.padre) radici.push(x); });
    return radici;
  }
  function trova(id) { return ((S.d && S.d.commenti) || []).filter(function (c) { return c.id === id; })[0] || null; }
  function iniziali(n) {
    var p = String(n).replace(/[_.]/g, " ").trim().split(/\s+/).filter(function (w, i) { return i === 0 || !/^(di|de|del|della|delle|dei|da|e|il|la|le|in|con)$/i.test(w); });
    return ((p[0] || "?").charAt(0) + (p.length > 1 ? p[1].charAt(0) : "")).toUpperCase();
  }
  function colore(n) { var h = 0; for (var i = 0; i < n.length; i++) h = (h * 31 + n.charCodeAt(i)) >>> 0; return AV[h % AV.length]; }
  var fmtOra = new Intl.DateTimeFormat("it-IT", { timeZone: "Europe/Rome", hour: "numeric", minute: "2-digit" });
  var fmtGiorno = new Intl.DateTimeFormat("it-IT", { timeZone: "Europe/Rome", day: "numeric", month: "numeric" });
  function quando(iso) {
    var d = new Date(iso); if (isNaN(d)) return "";
    var m = Math.floor((Date.now() - d) / 60000);
    if (m < 1) return "adesso";
    if (m < 60) return m + " min fa";
    if (m < 24 * 60) return Math.floor(m / 60) + " h fa";
    return fmtGiorno.format(d) + " " + fmtOra.format(d);
  }
  function avatar(nome, piccolo) { var a = el("span", "av" + (piccolo ? " av-s" : ""), iniziali(nome)); a.style.background = colore(nome); a.setAttribute("aria-hidden", "true"); return a; }
  function targhetta(v) { return el("span", "tg " + (v === "toro" ? "tg-up" : "tg-down"), SEGNO[v] + " " + LAB[v]); }

  /* ---------- Testata e sentiment ---------- */
  function testata() {
    var x = q(".lt-live", R), v = S.d && S.d.voto, n = S.d ? S.d.lettori || 0 : 0, oggi = v && v.aperto ? " oggi" : "";
    x.hidden = !(S.stato === "pronto" && n > 0);
    q(".lt-live span", R).textContent = (n === 1 ? "1 lettore" : n + " lettori") + oggi;
  }
  function sentiment() {
    var box = q(".lt-sent", R), corpo = q("[data-sent]", R), v = S.d && S.d.voto; corpo.innerHTML = "";
    var tot = v ? v.toro + v.orso : 0;
    box.hidden = S.stato === "pronto" && v && !v.aperto && tot === 0;      // edizione passata senza voti: niente sentiment
    if (S.stato === "fuori") { corpo.appendChild(el("p", "lt-nota", "Il sentiment arriva tra pochi secondi.")); return; }
    if (!v || (v.aperto && !v.mio)) {
      var row = el("div", "sb-row");
      ["toro", "orso"].forEach(function (k) {
        var b = bottone("sb " + (k === "toro" ? "sb-up" : "sb-down"), null, "vota"); b.dataset.v = k; b.disabled = !v;
        b.appendChild(el("b", "", SEGNO[k] + " " + LAB[k])); b.appendChild(el("span", "", k === "toro" ? "rialzista" : "ribassista"));
        row.appendChild(b);
      });
      corpo.appendChild(row);
      corpo.appendChild(el("p", "lt-nota lt-c", "Oggi qual è il tuo sentiment sui mercati? Vota e guarda come la pensa la Gommunity."));
      return;
    }
    // dopo il voto una riga sola: Toro e la sua percentuale, la barra, Orso; sotto i voti e "cambia"
    var pt = tot ? Math.round(v.toro / tot * 100) : 0, po = tot ? 100 - pt : 0;
    var r1 = el("div", "sv"); r1.setAttribute("role", "img"); r1.setAttribute("aria-label", "Toro " + pt + "%, Orso " + po + "%");
    var lt = el("span", "sv-t up"); lt.appendChild(document.createTextNode("▲ Toro ")); lt.appendChild(el("b", "", pt + "%"));
    var bar = el("span", "sv-bar"), u = el("i", "u"), d = el("i", "d"); u.style.width = (S.anima ? 50 : pt) + "%"; bar.appendChild(u); bar.appendChild(d);
    var lo = el("span", "sv-t down"); lo.appendChild(el("b", "", po + "%")); lo.appendChild(document.createTextNode(" Orso ▼"));
    r1.appendChild(lt); r1.appendChild(bar); r1.appendChild(lo); corpo.appendChild(r1);
    if (S.anima) requestAnimationFrame(function () { requestAnimationFrame(function () { u.style.width = pt + "%"; }); });
    S.anima = false;
    var p = el("p", "lt-nota"); p.appendChild(document.createTextNode(tot === 1 ? "1 voto" : tot + " voti"));
    if (v.mio && v.aperto) {
      p.appendChild(document.createTextNode(" · hai votato ")); p.appendChild(el("b", v.mio === "toro" ? "up" : "down", LAB[v.mio]));
      p.appendChild(document.createTextNode(" · ")); p.appendChild(bottone("lt-link", "cambia", "cambia"));
    }
    corpo.appendChild(p);
  }

  /* ---------- I commenti ---------- */
  function azioni(c, radice) {
    var az = el("div", "ca");
    var lk = bottone("lk", null, "like"); lk.dataset.id = c.id; lk.setAttribute("aria-pressed", c.piaciuto ? "true" : "false");
    lk.setAttribute("aria-label", "Mi piace, " + c.piace); lk.innerHTML = CUORE; lk.appendChild(el("span", "", String(c.piace))); az.appendChild(lk);
    var rp = bottone("", "Rispondi", "rispondi"); rp.dataset.id = radice.id; rp.dataset.n = c.nome; if (c !== radice) rp.dataset.cita = "1"; az.appendChild(rp);
    if (!c.mio) {
      if (S.menu === c.id) { var sg = bottone("sg", c.segnalato ? "Segnalato" : "Segnala il commento", "segnala"); sg.dataset.id = c.id; sg.disabled = !!c.segnalato; az.appendChild(sg); }
      else { var mn = bottone("mn", "···", "menu"); mn.dataset.id = c.id; mn.setAttribute("aria-label", "Altre azioni"); az.appendChild(mn); }
    }
    return az;
  }
  function riga(c) {
    var m = el("p", "cm"); m.appendChild(el("b", "cn", c.nome));
    if (c.mio) m.appendChild(el("span", "tu", "TU"));
    if (c.voto) m.appendChild(targhetta(c.voto));
    var t = el("time", "", quando(c.quando)); t.dateTime = c.quando; m.appendChild(t);
    return m;
  }
  function nodo(c) {
    var a = el("article", "cmt" + (c.id === S.nuovo ? " new" : "")); a.dataset.id = c.id;
    a.appendChild(avatar(c.nome));
    var b = el("div", "cb");
    b.appendChild(riga(c)); b.appendChild(el("p", "ct", c.testo)); b.appendChild(azioni(c, c));
    if (c.r.length) {
      var rs = el("div", "rs");
      c.r.forEach(function (r) {
        var x = el("div", "rsp" + (r.id === S.nuovo ? " new" : "")); x.dataset.id = r.id; x.appendChild(avatar(r.nome, true));
        var xb = el("div", "cb"); xb.appendChild(riga(r)); xb.appendChild(el("p", "ct ct-s", r.testo)); xb.appendChild(azioni(r, c));
        x.appendChild(xb); rs.appendChild(x);
      });
      b.appendChild(rs);
    }
    a.appendChild(b);
    return a;
  }
  function commenti() {
    var box = q("[data-list]", R), tutte = albero(), n = ((S.d && S.d.commenti) || []).length; box.innerHTML = "";
    q("[data-count]", R).textContent = S.stato === "pronto" ? String(n) : "";
    R.querySelectorAll("[data-act='ord']").forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.o === S.ord ? "true" : "false"); });
    var conti = { toro: 0, orso: 0 }; tutte.forEach(function (c) { if (c.voto) conti[c.voto]++; });
    R.querySelectorAll("[data-act='filtro']").forEach(function (b) {
      var f = b.dataset.f; b.setAttribute("aria-pressed", f === S.filtro ? "true" : "false");
      b.textContent = f === "tutti" ? "Tutti" : SEGNO[f] + " " + (f === "toro" ? "Tori" : "Orsi") + " · " + conti[f];
    });
    var piu = q("[data-more]", R); piu.hidden = true;
    if (S.stato === "attesa") { box.appendChild(el("p", "lt-vuoto", "Caricamento della discussione...")); return; }
    if (S.stato === "fuori") {
      var f = el("div", "lt-vuoto"); f.appendChild(el("b", "", "La discussione si sta caricando"));
      f.appendChild(document.createTextNode("Riproviamo da soli tra pochi secondi. ")); f.appendChild(bottone("lt-link", "Riprova adesso", "ricarica")); box.appendChild(f); return;
    }
    var lista = tutte.filter(function (c) { return S.filtro === "tutti" || c.voto === S.filtro; });
    if (S.ord === "top") lista.sort(function (x, y) { return (S.miei[y.id] ? 1 : 0) - (S.miei[x.id] ? 1 : 0) || y.piace - x.piace || x.id - y.id; });
    else lista.sort(function (x, y) { return y.id - x.id; });
    if (!lista.length) {
      var v = el("div", "lt-vuoto");
      if (tutte.length) v.appendChild(document.createTextNode("Nessun commento con questo filtro."));
      else { v.appendChild(el("b", "", "Apri tu la discussione")); v.appendChild(document.createTextNode("Nessun commento, per ora: di' la tua sull'edizione.")); }
      box.appendChild(v);
    }
    lista.forEach(function (c, i) { var x = nodo(c); if (i >= 3) x.classList.add("oltre"); box.appendChild(x); });
    piu.hidden = lista.length <= 3 || S.tutti; piu.textContent = "Vedi tutti e " + n + " i commenti";
    R.classList.toggle("lt-tutti", S.tutti);
  }

  /* ---------- Scrivere ---------- */
  function composer() {
    var v = S.d && S.d.voto, ni = q(".cmp-nome", R), lato = q("[data-lato]", R), re = q("[data-re]", R), ta = q("textarea", R), a = q(".cmp .av", R);
    if (document.activeElement !== ni) ni.value = S.nome;
    a.textContent = iniziali(S.nome || "?"); a.style.background = colore(S.nome || "?");
    lato.className = "cmp-lato" + (v && v.mio ? (v.mio === "toro" ? " up" : " down") : "");
    lato.textContent = v && v.mio ? "Commenti da " + SEGNO[v.mio] + " " + LAB[v.mio] : (v && v.aperto ? "Vota il sentiment per mostrarlo accanto al nome" : "");
    re.hidden = !S.re; if (S.re) { var s = re.firstElementChild; s.textContent = "Rispondi a "; s.appendChild(el("b", "", S.re.n)); q(".cmp", R).classList.add("aperto"); }
    ta.placeholder = S.re ? "Scrivi la tua risposta…" : "Di' la tua sull'edizione di oggi…";
    q(".send", R).disabled = S.stato !== "pronto";
  }
  function errore(msg) { var e = q("[data-err]", R); e.textContent = msg || ""; e.hidden = !msg; if (msg) q(".cmp", R).classList.add("aperto"); }
  function nomeValido() {
    var v = (S.nome || "").replace(/\s+/g, " ").trim();
    if (!v) return "Scegli un nome per firmare, o generane uno con il dado.";
    if (v.length < 2 || v.length > 24) return "Il nome va da 2 a 24 caratteri.";
    if (RISERVATI.test(v.replace(/[\s._-]/g, ""))) return "Questo nome è riservato alla redazione: scegline un altro.";
    S.nome = v; return "";
  }
  // Un nome è di un solo lettore: il servizio dice se quello scritto è libero, prima che si scriva il commento.
  // Se il servizio non risponde non si dice nulla: il controllo vero lo fa comunque alla pubblicazione.
  var timerNome = null;
  function nomeLibero(nome) { return api("GET", "nome?n=" + encodeURIComponent(nome)); }
  function verificaNome() {
    clearTimeout(timerNome);
    timerNome = setTimeout(function () {
      var nome = (S.nome || "").replace(/\s+/g, " ").trim(); if (nome.length < 2) return;
      nomeLibero(nome).then(function (j) { if (j && !j.libero && j.messaggio && (S.nome || "").replace(/\s+/g, " ").trim() === nome) errore(j.messaggio); }, function () {});
    }, 600);
  }
  // Il dado: la coda tiene nomi già verificati liberi, così il clic risponde subito; si riempie da sola quando si svuota.
  // Se il servizio non risponde i candidati si propongono lo stesso: il controllo vero resta quello della pubblicazione.
  function rifornisci() {
    if (volo) return volo;
    var soloCombinati = !MAZZO || !MAZZO.length, c = candidati(), fine = function () { volo = null; };
    volo = api("GET", "nome?" + c.map(function (n) { return "n=" + encodeURIComponent(n); }).join("&")).then(function (j) {
      var liberi = (j && j.liberi) || [];
      if (liberi.length) CODA = CODA.concat(liberi); else if (soloCombinati) LIVELLO++;
    }, function () { CODA = CODA.concat(c); }).then(fine, fine);
    return volo;
  }
  function tiraDado(giri) {
    if (CODA.length) {
      var nome = CODA.shift(), ni = q(".cmp-nome", R);
      clearTimeout(timerNome); S.nome = nome; ni.value = nome; errore(""); composer();
      if (CODA.length < 3) rifornisci();
      return;
    }
    rifornisci().then(function () { if (CODA.length || (giri || 0) < 12) tiraDado((giri || 0) + (CODA.length ? 0 : 1)); });
  }
  function contatore() { var n = q("textarea", R).value.length; q("[data-conto]", R).textContent = n > 480 ? (600 - n) + " caratteri" : ""; }
  function invia() {
    var ta = q("textarea", R), x = ta.value.replace(/\n{3,}/g, "\n\n").trim(), send = q(".send", R);
    var msg = nomeValido() || (x ? "" : "Scrivi qualcosa prima di pubblicare.");
    if (msg) { errore(msg); (x ? q(".cmp-nome", R) : ta).focus(); return; }
    if (send.disabled) return;
    errore(""); send.disabled = true; send.textContent = "Invio…";
    var corpo = { nome: S.nome, testo: x }; if (S.re) corpo.padre = S.re.id;
    scrivi(pad(S.ed.numero) + "/commenti", corpo).then(function (j) {
      send.textContent = "Pubblica"; send.disabled = false;
      var c = j && j.commento; if (!c) return;
      salva("gtd-nome", S.nome);
      S.d.commenti.push(c); S.miei[c.id] = true; S.nuovo = c.id; S.filtro = "tutti"; S.re = null;
      ta.value = ""; ta.style.height = ""; contatore(); q(".cmp", R).classList.remove("aperto"); ta.blur();
      conta("lettori-commento", "La Gommunity: commento" + (c.padre ? " (risposta)" : ""));
      rendi();
      var nd = R.querySelector('[data-id="' + c.id + '"]'); if (nd && nd.scrollIntoView) nd.scrollIntoView({ block: "nearest", behavior: "smooth" });
      var id = c.id; setTimeout(function () { if (S.nuovo === id) S.nuovo = null; }, 2000);
    }, function (e) { send.textContent = "Pubblica"; send.disabled = false; errore(e.message); if (e.stato === 409) q(".cmp-nome", R).focus(); });
  }

  /* ---------- Azioni ---------- */
  function vota(k) {
    var v = S.d.voto, prima = JSON.stringify(v);
    if (k) { if (v.mio) v[v.mio]--; v[k]++; v.mio = k; S.anima = true; } else { v[v.mio]--; v.mio = null; }
    rendi();
    scrivi(pad(S.ed.numero) + "/voto", { voto: k }).then(function (j) {
      if (j && j.voto) { S.d.voto = j.voto; rendi(); }
      if (k) conta("lettori-voto", "La Gommunity: sentiment");
    }, function (e) { S.d.voto = JSON.parse(prima); rendi(); avviso(e.message); });
  }
  function piace(id) {
    var c = trova(id); if (!c) return;
    c.piaciuto = !c.piaciuto; c.piace += c.piaciuto ? 1 : -1; rendi();
    scrivi("commenti/" + id + "/piace", {}).then(function (j) { if (j) { c.piace = j.piace; c.piaciuto = j.piaciuto; rendi(); } },
      function (e) { c.piaciuto = !c.piaciuto; c.piace += c.piaciuto ? 1 : -1; rendi(); avviso(e.message); });
  }
  function segnala(id) {
    var c = trova(id); if (!c || c.segnalato) return;
    c.segnalato = true; rendi();
    scrivi("commenti/" + id + "/segnala", {}).then(function (j) {
      S.menu = null;
      if (j && j.nascosto) { S.d.commenti = S.d.commenti.filter(function (x) { return x.id !== id && x.padre !== id; }); avviso("Commento nascosto. Grazie della segnalazione."); }
      else avviso("Segnalazione ricevuta. Grazie.");
      rendi();
    }, function (e) { c.segnalato = false; rendi(); avviso(e.message); });
  }
  var toast = null, tt = null;
  function avviso(msg) {
    if (!toast) { toast = el("div", "lt-toast"); toast.setAttribute("role", "status"); toast.hidden = true; document.body.appendChild(toast); }
    toast.textContent = msg; toast.hidden = false; clearTimeout(tt); tt = setTimeout(function () { toast.hidden = true; }, 2800);
  }

  function rendi() { if (!R || !S.ed) return; testata(); sentiment(); commenti(); composer(); }

  /* ---------- La struttura ---------- */
  function struttura(root) {
    root.innerHTML = "";
    var hd = el("div", "lt-hd"), h = el("h2", "lt-t", "La Gommunity"); h.id = "lt-h"; hd.appendChild(h);
    var live = el("span", "lt-live"); live.appendChild(el("i")); live.appendChild(el("span")); live.hidden = true; hd.appendChild(live);
    root.appendChild(hd);
    var se = el("div", "lt-sent");
    var sc = el("div"); sc.dataset.sent = ""; sc.setAttribute("aria-live", "polite"); se.appendChild(sc); root.appendChild(se);
    var cm = el("div", "lt-cm");
    var bar = el("div", "lt-bar"), h3 = el("h3", "lt-h3", "Commenti "), cn = el("span"); cn.dataset.count = ""; h3.appendChild(cn); bar.appendChild(h3);
    var ord = el("div", "lt-ord"); ord.setAttribute("role", "group"); ord.setAttribute("aria-label", "Ordina i commenti");
    [["top", "Più apprezzati"], ["new", "Più recenti"]].forEach(function (o) { var b = bottone("", o[1], "ord"); b.dataset.o = o[0]; ord.appendChild(b); });
    bar.appendChild(ord); cm.appendChild(bar);
    var fl = el("div", "lt-flt"); fl.setAttribute("role", "group"); fl.setAttribute("aria-label", "Filtra per sentiment");
    ["tutti", "toro", "orso"].forEach(function (f) { var b = bottone("", "", "filtro"); b.dataset.f = f; fl.appendChild(b); });
    cm.appendChild(fl);
    var ls = el("div", "lt-list"); ls.dataset.list = ""; cm.appendChild(ls);
    var more = bottone("lt-more", "", "tutti"); more.dataset.more = ""; more.hidden = true; cm.appendChild(more);
    root.appendChild(cm);
    // scrivere: chi firma (nome o dado), il testo, il sentiment che accompagna il commento
    var form = el("form", "cmp"); form.noValidate = true;
    var re = el("div", "cmp-re"); re.dataset.re = ""; re.hidden = true; re.appendChild(el("span")); re.appendChild(bottone("lt-link", "annulla", "annulla")); form.appendChild(re);
    var chi = el("div", "cmp-chi"); chi.appendChild(avatar("?", true));
    var lb = el("label", "", "Firmi come"); lb.htmlFor = "lt-nome"; chi.appendChild(lb);
    var ni = el("input", "cmp-nome"); ni.id = "lt-nome"; ni.type = "text"; ni.maxLength = 24; ni.placeholder = "Il tuo nome"; ni.autocomplete = "nickname"; chi.appendChild(ni);
    var dado = bottone("cmp-dado", null, "dado"); dado.innerHTML = DADO; dado.setAttribute("aria-label", "Genera un nome a caso"); dado.title = "Genera un nome a caso"; chi.appendChild(dado);
    form.appendChild(chi);
    var tr = el("div", "trappola"); tr.setAttribute("aria-hidden", "true"); var ti = el("input"); ti.type = "text"; ti.name = "sito"; ti.tabIndex = -1; ti.autocomplete = "off"; tr.appendChild(ti); form.appendChild(tr);
    var tl = el("label", "lt-sr", "Il tuo commento"); tl.htmlFor = "lt-testo"; form.appendChild(tl);
    var ta = el("textarea"); ta.id = "lt-testo"; ta.rows = 3; ta.maxLength = 600; form.appendChild(ta);
    var pie = el("div", "cmp-pie"), lato = el("span", "cmp-lato"); lato.dataset.lato = ""; pie.appendChild(lato);
    var dx = el("div", "cmp-dx"), ct = el("span", "cmp-conto"); ct.dataset.conto = ""; dx.appendChild(ct);
    var send = el("button", "send", "Pubblica"); send.type = "submit"; dx.appendChild(send); pie.appendChild(dx); form.appendChild(pie);
    var err = el("p", "cmp-err"); err.dataset.err = ""; err.setAttribute("role", "alert"); err.hidden = true; form.appendChild(err);
    root.appendChild(form);
    var nota = el("p", "lt-regole", "Nessuna iscrizione. Opinioni sì, consigli di acquisto no. ");
    var rg = el("a", "", "Regole"); rg.href = "/regole.html"; nota.appendChild(rg); nota.appendChild(document.createTextNode(" · "));
    var pv = el("a", "", "Privacy"); pv.href = "/privacy.html#lettori"; nota.appendChild(pv); root.appendChild(nota);
    root.setAttribute("aria-labelledby", "lt-h");

    form.addEventListener("submit", function (e) { e.preventDefault(); invia(); });
    // chiusa è una riga sola ("Di' la tua…"); al tocco si apre con chi firma, il dado e Pubblica. Si richiude se lasci vuoto
    form.addEventListener("focusin", function () { form.classList.add("aperto"); if (!CODA.length) rifornisci(); });
    form.addEventListener("focusout", function (e) {
      setTimeout(function () { if (!form.contains(document.activeElement) && !ta.value.trim() && !S.re && q("[data-err]", R).hidden) form.classList.remove("aperto"); }, 150);
    });
    ta.addEventListener("input", function () { ta.style.height = "auto"; ta.style.height = Math.min(ta.scrollHeight + 2, 160) + "px"; errore(""); contatore(); });
    ta.addEventListener("keydown", function (e) { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); invia(); } });
    ni.addEventListener("input", function () { S.nome = ni.value; errore(""); var a = q(".cmp .av", R); a.textContent = iniziali(S.nome || "?"); a.style.background = colore(S.nome || "?"); verificaNome(); });
    root.addEventListener("click", function (e) {
      var b = e.target.closest("[data-act]"); if (!b || !root.contains(b)) return;
      var act = b.dataset.act, id = +b.dataset.id;
      if (act === "vota") vota(b.dataset.v);
      else if (act === "cambia") vota(null);
      else if (act === "like") piace(id);
      else if (act === "menu") { S.menu = id; rendi(); }
      else if (act === "segnala") segnala(id);
      else if (act === "ord") { S.ord = b.dataset.o; rendi(); }
      else if (act === "filtro") { S.filtro = b.dataset.f; rendi(); }
      else if (act === "tutti") { S.tutti = true; rendi(); }
      else if (act === "ricarica") { tentativi = 0; carica(false); }
      else if (act === "rispondi") { S.re = { id: id, n: b.dataset.n }; if (b.dataset.cita && !ta.value) ta.value = "@" + b.dataset.n + " "; rendi(); ta.focus(); }
      else if (act === "annulla") { S.re = null; rendi(); ta.focus(); }
      else if (act === "dado") tiraDado(0);
    });
  }

  var avviato = false;
  function monta(root, ed) {
    if (!root || !ed || !ed.numero) return;
    if (R !== root) { R = root; struttura(root); }
    if (!avviato) {
      avviato = true;
      // con la pagina aperta la discussione si aggiorna da sola (ogni 90 secondi, solo se la pagina è in vista)
      document.addEventListener("visibilitychange", function () { if (document.visibilityState === "visible" && S.stato !== "attesa") { tentativi = 0; carica(true); } });
      setInterval(function () { if (document.visibilityState === "visible" && S.stato === "pronto") carica(true); }, 90000);
    }
    S.gen++; tentativi = 0; S.ed = ed; S.d = null; S.stato = "attesa"; S.miei = {}; S.re = null; S.menu = null; S.tutti = false; S.filtro = "tutti"; S.ord = "top";
    errore(""); rendi(); carica(false);
  }
  window.LETTORI = { monta: monta };
})();
