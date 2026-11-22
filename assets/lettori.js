/* Gommberg Terminal Daily - La parola ai lettori (G-13): domanda del giorno con il voto Toro/Orso, commenti, risposte
   a un livello, like e Segnala. Lo stesso riquadro in homepage (accanto all'edizione) e nelle pagine e/NNN.html.
   Stile in assets/lettori.css; i dati li tiene il servizio /api/lettori/ su Cloudflare (nella redazione: sito/lettori.js).

   LETTORI.monta(elemento, edizione)  disegna il riquadro dentro l'elemento (un <aside class="lt"> vuoto) per quella
                                      edizione: {numero, data, lettori: {domanda, mercato, toro, orso, ieri, esito}}
                                      (la scheda e/NNN.json, scritta da redazione/pagine.py). Si richiama a ogni cambio
                                      di edizione. Se il servizio non risponde, la pagina resta intera: il riquadro
                                      dice soltanto che la discussione non si carica.
   Nessuna iscrizione e nessuna email: il nome si sceglie in "Firmi come" e lo ricorda il browser, come il codice
   anonimo del lettore (gtd-lettore) che serve a riconoscere i propri commenti, like e voti. */
(function () {
  "use strict";
  var API = "/api/lettori/";
  var LAB = { toro: "Toro", orso: "Orso" };
  var ART = { toro: "il Toro", orso: "l'Orso" };
  var NOMI = ["Toro paziente", "Orso prudente", "Cassettista", "Lettore delle 9:45", "Piazza Affari 26", "Spread 106", "Cedola mensile", "Lungo periodo"];
  var RISERVATI = /redazion|gommberg|gommellini|amministra|admin|moderat|staff|direttore/i;   // gli stessi del servizio
  var CUORE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20.5s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7.6a4.3 4.3 0 0 1 7.5 2.7c0 5.6-7.5 10.2-7.5 10.2Z"/></svg>';
  var el = function (t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
  var q = function (s, r) { return r.querySelector(s); };
  var pad = function (n) { return String(n).padStart(3, "0"); };
  var leggi = function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } };
  var salva = function (k, v) { try { localStorage.setItem(k, v); } catch (e) { /* navigazione privata: resta per questa visita */ } };

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

  var S = { ed: null, d: null, stato: "attesa", ord: "top", nome: leggi("gtd-nome"), bozza: "", cambia: false,
            giro: Math.floor(Math.random() * NOMI.length), aperti: {}, nuovo: null, anima: false, miei: {}, presa: 0, timer: null, gen: 0 };
  var VISTE = [];
  var ltd = null, toast = null, tt = null;

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
  function scrivi(percorso, corpo, trappola, giro) {
    var attesa = Math.max(0, S.presa + 3300 - Date.now());
    return new Promise(function (ok) { setTimeout(ok, attesa); }).then(function () {
      var c = Object.assign({}, corpo, { gettone: S.d && S.d.gettone, sito: trappola || "" });
      return api("POST", percorso, c).catch(function (e) {
        if (e.stato === 400 && /Ricarica/.test(e.message) && !giro) return carica(true).then(function () { return scrivi(percorso, corpo, trappola, 1); });
        throw e;
      });
    });
  }
  function carica(quieto) {
    var n = S.ed && S.ed.numero, gen = S.gen; if (!n) return Promise.resolve();
    return api("GET", pad(n)).then(function (d) {
      if (gen !== S.gen) return;
      S.d = d; S.presa = Date.now(); S.stato = "pronto"; rendi();
    }, function () {
      if (gen !== S.gen) return;
      if (!quieto || !S.d) { S.stato = "fuori"; rendi(); }
    });
  }

  /* ---------- I commenti come albero (risposte a un livello) ---------- */
  function albero() {
    var lista = (S.d && S.d.commenti) || [], radici = [], per = {};
    lista.forEach(function (c) { per[c.id] = Object.assign({}, c, { r: [] }); });
    lista.forEach(function (c) { var x = per[c.id]; if (c.padre && per[c.padre]) per[c.padre].r.push(x); else if (!c.padre) radici.push(x); });
    return radici;
  }
  function totale() { return ((S.d && S.d.commenti) || []).length; }
  function ordinati(radici) {
    var a = radici.slice();
    if (S.ord === "top") a.sort(function (x, y) { return (S.miei[y.id] ? 1 : 0) - (S.miei[x.id] ? 1 : 0) || y.piace - x.piace || x.id - y.id; });
    else a.sort(function (x, y) { return y.id - x.id; });
    return a;
  }
  function trova(id) { return ((S.d && S.d.commenti) || []).filter(function (c) { return c.id === id; })[0] || null; }
  function iniziali(n) {
    var tutte = String(n).replace(/[_.]/g, " ").trim().split(/\s+/);
    var p = tutte.filter(function (w, i) { return i === 0 || !/^(di|de|del|della|delle|dei|da|e|il|la|le)$/i.test(w); });
    return ((p[0] || "?").charAt(0) + (p.length > 1 ? p[1].charAt(0) : "")).toUpperCase();
  }
  var fmtOra = new Intl.DateTimeFormat("it-IT", { timeZone: "Europe/Rome", hour: "numeric", minute: "2-digit" });
  var fmtGiorno = new Intl.DateTimeFormat("it-IT", { timeZone: "Europe/Rome", day: "numeric", month: "numeric" });
  function quando(iso) {
    var d = new Date(iso); if (isNaN(d)) return "";
    if (Date.now() - d < 60000) return "adesso";
    return fmtGiorno.format(d) === fmtGiorno.format(new Date()) ? fmtOra.format(d) : fmtGiorno.format(d) + " " + fmtOra.format(d);
  }

  /* ---------- La domanda e il voto: prima due tasti, poi le percentuali ---------- */
  function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }
  function pct(t) { var tot = t.toro + t.orso; var p = tot ? Math.round(t.toro / tot * 100) : 0; return [p, tot ? 100 - p : 0, tot]; }
  function esito(x) {   // "Venerdì l'S&P 500 ha chiuso a +0,8%: ha vinto il Toro." (senza giorno: la seduta della domanda)
    if (!x || !x.var) return "";
    var chi = (x.giorno ? cap(x.giorno) + " l'" : "L'") + (x.mercato || "S&P 500");
    return x.vince === "pari" ? chi + " ha chiuso invariato." : chi + " ha chiuso a " + x.var + ": ha vinto " + ART[x.vince] + ".";
  }
  function voto(vista) {
    var box = q(".lt-q", vista.root), L = S.ed.lettori || {}, v = S.d && S.d.voto;
    var poll = q("[data-poll]", box), ieri = q(".lt-ieri", box);
    poll.innerHTML = "";
    // la verifica del giorno prima: solo se quel giorno qualcuno aveva votato
    var ti = S.d && S.d.ieri, ok = L.ieri && L.ieri.var && ti && ti.toro + ti.orso > 0;
    ieri.hidden = !ok;
    if (ok) {
      var p = pct(ti), giusti = L.ieri.vince === "toro" ? p[0] : L.ieri.vince === "orso" ? p[1] : null;
      ieri.textContent = esito(L.ieri) + " ";
      if (giusti != null) { ieri.appendChild(document.createTextNode("Lo aveva detto il ")); ieri.appendChild(el("b", "", giusti + "%")); ieri.appendChild(document.createTextNode(" dei lettori.")); }
    }
    if (!L.domanda) { box.hidden = true; return; }
    q("[data-q]", box).textContent = L.domanda;
    var tot = v ? v.toro + v.orso : 0;
    // a voto chiuso e senza voti la domanda non si mostra: era di quel giorno
    box.hidden = S.stato === "pronto" && v && !v.aperto && tot === 0;
    if (S.stato !== "pronto" || !v) {
      if (S.stato === "fuori") poll.appendChild(el("p", "vhint", "Il voto non si carica in questo momento."));
      else {
        var row0 = el("div", "vb-row");
        ["toro", "orso"].forEach(function (k) { var b = tasto(k, L); b.disabled = true; row0.appendChild(b); });
        poll.appendChild(row0);
      }
      return;
    }
    if (v.aperto && !v.mio) {
      var row = el("div", "vb-row");
      ["toro", "orso"].forEach(function (k) { row.appendChild(tasto(k, L)); });
      poll.appendChild(row);
      poll.appendChild(el("p", "vhint", "Vota per vedere come la pensano gli altri lettori."));
      return;
    }
    var pp = pct(v), pt = pp[0], po = pp[1];
    var vr = el("div", "vr");
    var r2 = el("div", "vr-row"); r2.setAttribute("role", "img"); r2.setAttribute("aria-label", LAB.toro + " " + pt + "%, " + LAB.orso + " " + po + "%");
    var a = el("span", "up"); a.appendChild(el("b", "", pt + "%")); a.appendChild(document.createTextNode(" " + LAB.toro));
    var b2 = el("span", "down"); b2.appendChild(document.createTextNode(LAB.orso + " ")); b2.appendChild(el("b", "", po + "%"));
    r2.appendChild(a); r2.appendChild(b2); vr.appendChild(r2);
    var bar = el("div", "vr-bar"), u = el("i", "u"), d = el("i", "d");
    u.style.width = (S.anima ? 50 : pt) + "%"; d.style.width = (S.anima ? 50 : po) + "%";
    bar.appendChild(u); bar.appendChild(d); vr.appendChild(bar);
    if (S.anima) requestAnimationFrame(function () { requestAnimationFrame(function () { u.style.width = pt + "%"; d.style.width = po + "%"; }); });
    var n = el("p", "vr-n"); n.appendChild(document.createTextNode(tot === 1 ? "1 voto" : tot + " voti"));
    if (v.mio) { n.appendChild(document.createTextNode(" · hai votato ")); n.appendChild(el("b", v.mio === "toro" ? "up" : "down", LAB[v.mio])); }
    if (v.aperto) { n.appendChild(document.createTextNode(" · ")); var cb = el("button", "", "Cambia"); cb.type = "button"; cb.dataset.act = "cambia"; n.appendChild(cb); }
    else n.appendChild(document.createTextNode(" · " + (L.esito ? esito(L.esito) : "voto chiuso all'apertura di Wall Street")));
    vr.appendChild(n); poll.appendChild(vr);
  }
  function tasto(k, L) {
    var b = el("button", "vb " + (k === "toro" ? "up" : "down")); b.type = "button"; b.dataset.act = "vota"; b.dataset.v = k;
    b.appendChild(el("b", "", (k === "toro" ? "↑ " : "↓ ") + LAB[k])); b.appendChild(el("span", "", L[k] || (k === "toro" ? "sale" : "scende")));
    return b;
  }

  /* ---------- I commenti ---------- */
  function nodo(c, vista, padre) {
    var a = el("article", "cmt" + (c.id === S.nuovo ? " new" : "")); a.dataset.id = c.id;
    var av = el("span", "av", iniziali(c.nome)); av.setAttribute("aria-hidden", "true"); a.appendChild(av);
    var b = el("div", "cb");
    var m = el("p", "cm"); m.appendChild(el("b", "cn", c.nome));
    if (c.voto) m.appendChild(el("span", "st " + (c.voto === "toro" ? "up" : "down"), LAB[c.voto]));
    var t = el("time", "", quando(c.quando)); t.dateTime = c.quando; m.appendChild(t); b.appendChild(m);
    b.appendChild(el("p", "ct", c.testo));   // solo testo: nessun link cliccabile, nessun HTML
    var az = el("p", "ca");
    var lk = el("button", "lk"); lk.type = "button"; lk.dataset.act = "like"; lk.dataset.id = c.id;
    lk.setAttribute("aria-pressed", c.piaciuto ? "true" : "false"); lk.setAttribute("aria-label", "Mi piace: " + c.piace);
    lk.innerHTML = CUORE; lk.appendChild(el("span", "", String(c.piace))); az.appendChild(lk);
    var rp = el("button", "", "Rispondi"); rp.type = "button"; rp.dataset.act = "rispondi"; rp.dataset.id = padre ? padre.id : c.id; rp.dataset.n = c.nome; if (padre) rp.dataset.cita = "1";
    az.appendChild(rp);
    var risposte = !padre && c.r.length ? c.r : null, aperto = risposte && (!vista.compatta || S.aperti[c.id]);
    if (risposte && vista.compatta) {
      var tg = el("button", "", aperto ? "Nascondi le risposte" : (risposte.length === 1 ? "Vedi 1 risposta" : "Vedi " + risposte.length + " risposte"));
      tg.type = "button"; tg.dataset.act = "risposte"; tg.dataset.id = c.id; tg.setAttribute("aria-expanded", aperto ? "true" : "false"); az.appendChild(tg);
    }
    if (!c.mio) {
      var sg = el("button", "sg", c.segnalato ? "Segnalato" : "Segnala"); sg.type = "button"; sg.dataset.act = "segnala"; sg.dataset.id = c.id; sg.disabled = !!c.segnalato;
      sg.title = "Segnala un commento offensivo, falso o pubblicitario: con tre segnalazioni si nasconde"; az.appendChild(sg);
    }
    b.appendChild(az);
    if (aperto) { var rs = el("div", "rs"); risposte.forEach(function (r) { rs.appendChild(nodo(r, vista, c)); }); b.appendChild(rs); }
    a.appendChild(b);
    return a;
  }
  function lista(vista) {
    var box = q("[data-list]", vista.root), tot = totale(), radici = albero(); box.innerHTML = "";
    q("[data-count]", vista.root).textContent = S.stato !== "pronto" ? "" : tot === 0 ? "Nessun commento" : tot === 1 ? "1 commento" : tot + " commenti";
    vista.root.querySelectorAll("[data-act='ord']").forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.o === S.ord ? "true" : "false"); });
    if (S.stato === "attesa") box.appendChild(el("div", "lt-empty", "Caricamento della discussione..."));
    else if (S.stato === "fuori") { var f = el("div", "lt-empty"); f.appendChild(el("b", "", "La discussione non si carica")); f.appendChild(document.createTextNode("Riprova tra qualche minuto: l'edizione si legge lo stesso.")); box.appendChild(f); }
    else if (!radici.length) {
      var v = el("div", "lt-empty"); v.appendChild(el("b", "", "Apri tu la discussione")); v.appendChild(document.createTextNode("Nessun commento, per ora. Di' la tua sull'edizione."));
      box.appendChild(v);
    } else ordinati(radici).forEach(function (c) { box.appendChild(nodo(c, vista, null)); });
    var piu = q("[data-more]", vista.root);
    if (piu) { piu.hidden = radici.length <= 3; piu.textContent = "Vedi tutti i " + tot + " commenti"; }
    var form = q("[data-cmp]", vista.root);
    q(".send", form).disabled = S.stato !== "pronto";
  }
  function nome(vista) {
    var box = q("[data-nome]", vista.root); box.innerHTML = "";
    if (S.nome && !S.cambia) {
      var av = el("span", "av", iniziali(S.nome)); av.setAttribute("aria-hidden", "true"); box.appendChild(av);
      box.appendChild(document.createTextNode("Firmi come ")); box.appendChild(el("b", "", S.nome));
      var cb = el("button", "", "cambia"); cb.type = "button"; cb.dataset.act = "nome"; box.appendChild(cb);
      return;
    }
    var id = "nm-" + (vista.compatta ? "a" : "b");
    var lb = el("label", "", "Firmi come"); lb.htmlFor = id; box.appendChild(lb);
    var i = el("input", "nm-in"); i.type = "text"; i.id = id; i.maxLength = 24; i.value = S.bozza; i.placeholder = "Il tuo nome"; i.autocomplete = "nickname";
    i.addEventListener("input", function () { S.bozza = i.value; errore(vista, ""); });
    i.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); if (fissaNome(vista)) { VISTE.forEach(nome); q("textarea", vista.root).focus(); } } });
    box.appendChild(i);
    var pr = el("button", "", "Proponimene uno"); pr.type = "button"; pr.dataset.act = "proponi"; box.appendChild(pr);
  }
  // Il nome si sceglie una volta: resta finché non lo cambi (lo ricorda il browser)
  function fissaNome(vista) {
    var v = S.bozza.replace(/\s+/g, " ").trim(), msg = "";
    if (!v) msg = "Scegli un nome per firmare: va bene anche un soprannome.";
    else if (v.length < 2) msg = "Il nome va da 2 a 24 caratteri.";
    else if (RISERVATI.test(v.replace(/[\s._-]/g, ""))) msg = "Questo nome è riservato alla redazione: scegline un altro.";
    if (msg) { errore(vista, msg); var i = q(".nm-in", vista.root); if (i) i.focus(); return false; }
    S.nome = v; S.cambia = false; salva("gtd-nome", v); errore(vista, ""); return true;
  }
  function rendi() {
    if (!S.ed) return;
    VISTE.forEach(function (v) { voto(v); lista(v); nome(v); });
    S.anima = false;
    if (ltd) q("[data-ed]", ltd).textContent = "N. " + pad(S.ed.numero);
  }

  /* ---------- Scrivere ---------- */
  function errore(vista, msg) { var e = q("[data-err]", vista.root); e.textContent = msg || ""; e.hidden = !msg; }
  function rispostaA(vista, r) {
    vista.re = r;
    var box = q("[data-re]", vista.root), ta = q("textarea", vista.root);
    box.hidden = !r;
    if (r) { var s = box.firstElementChild; s.textContent = "Rispondi a "; s.appendChild(el("b", "", r.n)); }
    ta.placeholder = r ? "Scrivi una risposta..." : "Di' la tua sull'edizione";
  }
  function invia(vista) {
    var ta = q("textarea", vista.root), x = ta.value.replace(/\n{3,}/g, "\n\n").trim(), send = q(".send", vista.root);
    if (!x) { errore(vista, "Scrivi qualcosa prima di pubblicare."); ta.focus(); return; }
    errore(vista, "");
    if ((!S.nome || S.cambia) && !fissaNome(vista)) return;
    if (send.disabled) return;
    send.disabled = true; send.textContent = "Invio...";
    var corpo = { nome: S.nome, testo: x }; if (vista.re) corpo.padre = vista.re.id;
    scrivi(pad(S.ed.numero) + "/commenti", corpo, q(".trappola input", vista.root).value).then(function (j) {
      var c = j && j.commento; send.textContent = "Pubblica"; send.disabled = false;
      if (!c) return;
      S.d.commenti.push(c); S.miei[c.id] = true; if (c.padre) S.aperti[c.padre] = true;
      S.nuovo = c.id; ta.value = ""; ta.style.height = ""; rispostaA(vista, null);
      conta("lettori-commento", "La parola ai lettori: commento" + (c.padre ? " (risposta)" : ""));
      rendi();
      var nd = vista.root.querySelector('[data-id="' + c.id + '"]');
      if (nd && nd.scrollIntoView) nd.scrollIntoView({ block: "nearest", behavior: "smooth" });
      var id = c.id; setTimeout(function () { if (S.nuovo === id) S.nuovo = null; }, 1900);
    }, function (e) { send.textContent = "Pubblica"; send.disabled = false; errore(vista, e.message); });
  }

  /* ---------- Azioni ---------- */
  function vota(k) {
    var v = S.d.voto, prima = JSON.stringify(v);
    if (k) { if (v.mio) v[v.mio]--; v[k]++; v.mio = k; S.anima = true; } else { v[v.mio]--; v.mio = null; }
    rendi();
    scrivi(pad(S.ed.numero) + "/voto", { voto: k }).then(function (j) {
      if (j && j.voto) { S.d.voto = j.voto; rendi(); }
      if (k) conta("lettori-voto", "La parola ai lettori: voto");
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
      if (j && j.nascosto) {
        S.d.commenti = S.d.commenti.filter(function (x) { return x.id !== id && x.padre !== id; });
        rendi(); avviso("Commento nascosto. Grazie della segnalazione.");
      } else avviso("Segnalazione ricevuta. Grazie.");
    }, function (e) { c.segnalato = false; rendi(); avviso(e.message); });
  }
  function avviso(msg) {
    if (!toast) { toast = el("div", "lt-toast"); toast.setAttribute("role", "status"); toast.hidden = true; document.body.appendChild(toast); }
    toast.textContent = msg; toast.hidden = false; clearTimeout(tt); tt = setTimeout(function () { toast.hidden = true; }, 2800);
  }

  /* ---------- Il pannello della discussione ---------- */
  function apri() { ltd.hidden = false; document.body.style.overflow = "hidden"; rendi(); q("[data-act='chiudi']", ltd).focus(); conta("lettori-apri", "La parola ai lettori: discussione aperta"); }
  function chiudi() {
    if (!ltd || ltd.hidden) return; ltd.hidden = true;
    var v = document.getElementById("viewer"); if (!v || v.hidden) document.body.style.overflow = "";
    var b = VISTE[0] && q("[data-act='apri']", VISTE[0].root); if (b) b.focus();
  }

  /* ---------- La struttura (uguale nel riquadro e nel pannello) ---------- */
  function parti(pannello) {
    var f = document.createDocumentFragment();
    var lq = el("div", "lt-q"); lq.appendChild(el("p", "lt-k", "La domanda di oggi"));
    var ie = el("p", "lt-ieri"); ie.hidden = true; lq.appendChild(ie);
    var h = el("h3", "lt-h"); h.dataset.q = ""; lq.appendChild(h);
    var poll = el("div"); poll.dataset.poll = ""; poll.setAttribute("aria-live", "polite"); lq.appendChild(poll);
    var bar = el("div", "lt-bar"); var ct = el("span"); ct.dataset.count = ""; bar.appendChild(ct);
    var srt = el("span", "srt"); srt.setAttribute("role", "group"); srt.setAttribute("aria-label", "Ordine dei commenti");
    [["top", "Più votati"], ["new", "Recenti"]].forEach(function (o) { var b = el("button", "", o[1]); b.type = "button"; b.dataset.act = "ord"; b.dataset.o = o[0]; srt.appendChild(b); });
    bar.appendChild(srt);
    var ls = el("div", "lt-list"); ls.dataset.list = "";
    if (pannello) { var sc = el("div", "ltd-s"); sc.appendChild(lq); sc.appendChild(bar); sc.appendChild(ls); f.appendChild(sc); }
    else {
      f.appendChild(lq); f.appendChild(bar); f.appendChild(ls);
      var more = el("button", "lt-more"); more.type = "button"; more.dataset.act = "apri"; more.dataset.more = ""; more.hidden = true; f.appendChild(more);
    }
    var form = el("form", "cmp"); form.dataset.cmp = ""; form.noValidate = true;
    var re = el("div", "cmp-re"); re.dataset.re = ""; re.hidden = true; re.appendChild(el("span"));
    var an = el("button", "", "Annulla"); an.type = "button"; an.dataset.act = "annulla"; re.appendChild(an); form.appendChild(re);
    var chi = el("div", "cmp-chi"); chi.dataset.nome = ""; form.appendChild(chi);
    var tr = el("div", "trappola"); tr.setAttribute("aria-hidden", "true");
    var ti = el("input"); ti.type = "text"; ti.name = "sito"; ti.tabIndex = -1; ti.autocomplete = "off"; tr.appendChild(ti); form.appendChild(tr);
    var row = el("div", "cmp-row"), ta = el("textarea"); ta.rows = 1; ta.maxLength = 600; ta.placeholder = "Di' la tua sull'edizione"; ta.setAttribute("aria-label", "Il tuo commento");
    var send = el("button", "send", "Pubblica"); send.type = "submit"; row.appendChild(ta); row.appendChild(send); form.appendChild(row);
    var err = el("p", "cmp-err"); err.dataset.err = ""; err.setAttribute("role", "alert"); err.hidden = true; form.appendChild(err);
    var meta = el("p", "cmp-meta", "Niente iscrizione. Opinioni sì, consigli di acquisto no. ");
    var pv = el("a", "", "Privacy"); pv.href = "/privacy.html#lettori"; meta.appendChild(pv); form.appendChild(meta);
    f.appendChild(form);
    return f;
  }
  function collega(vista) {
    var form = q("[data-cmp]", vista.root), ta = q("textarea", vista.root);
    form.addEventListener("submit", function (e) { e.preventDefault(); invia(vista); });
    ta.addEventListener("input", function () { ta.style.height = "auto"; ta.style.height = Math.min(ta.scrollHeight + 2, 120) + "px"; errore(vista, ""); });
    ta.addEventListener("keydown", function (e) { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); invia(vista); } });
    vista.root.addEventListener("click", function (e) {
      if (vista.root === ltd && e.target === ltd) { chiudi(); return; }
      var b = e.target.closest("[data-act]"); if (!b || !vista.root.contains(b)) return;
      var act = b.dataset.act, id = +b.dataset.id;
      if (act === "vota") vota(b.dataset.v);
      else if (act === "cambia") vota(null);
      else if (act === "like") piace(id);
      else if (act === "segnala") segnala(id);
      else if (act === "risposte") { if (S.aperti[id]) delete S.aperti[id]; else S.aperti[id] = true; rendi(); }
      else if (act === "ord") { S.ord = b.dataset.o; rendi(); }
      else if (act === "rispondi") { rispostaA(vista, { id: id, n: b.dataset.n }); if (b.dataset.cita && !ta.value) ta.value = "@" + b.dataset.n + " "; ta.focus(); }
      else if (act === "annulla") { rispostaA(vista, null); ta.focus(); }
      else if (act === "nome") { S.cambia = true; S.bozza = S.nome || ""; VISTE.forEach(nome); var ni = q(".nm-in", vista.root); if (ni) { ni.focus(); ni.select(); } }
      else if (act === "proponi") { S.giro = (S.giro + 1) % NOMI.length; S.bozza = NOMI[S.giro]; errore(vista, ""); VISTE.forEach(nome); var np = q(".nm-in", vista.root); if (np) { np.focus(); np.select(); } }
      else if (act === "apri") apri();
      else if (act === "chiudi") chiudi();
    });
  }

  function monta(root, ed) {
    if (!root || !ed || !ed.numero) return;
    if (!VISTE.length || VISTE[0].root !== root) {
      root.innerHTML = "";
      var top = el("div", "lt-top"), h = el("h2", "lt-t", "La parola ai lettori"); h.id = "lt-h"; top.appendChild(h);
      var x = el("button", "lt-x", "Espandi"); x.type = "button"; x.dataset.act = "apri"; top.appendChild(x);
      root.appendChild(top); root.appendChild(parti(false)); root.setAttribute("aria-labelledby", "lt-h");
      if (!ltd) {
        ltd = el("div", "ltd"); ltd.hidden = true; ltd.setAttribute("role", "dialog"); ltd.setAttribute("aria-modal", "true"); ltd.setAttribute("aria-labelledby", "ltd-h");
        var p = el("div", "ltd-p"), t = el("div", "ltd-top"), h2 = el("h2"); h2.id = "ltd-h";
        h2.appendChild(document.createTextNode("La parola ai ")); h2.appendChild(el("b", "", "lettori")); var sp = el("span"); sp.dataset.ed = ""; h2.appendChild(sp);
        var cl = el("button", "", "Chiudi"); cl.type = "button"; cl.dataset.act = "chiudi"; t.appendChild(h2); t.appendChild(cl);
        p.appendChild(t); p.appendChild(parti(true)); ltd.appendChild(p); document.body.appendChild(ltd);
        document.addEventListener("keydown", function (e) { var v = document.getElementById("viewer"); if (e.key === "Escape" && !ltd.hidden && (!v || v.hidden)) chiudi(); });
        // con la pagina aperta la discussione si aggiorna da sola (ogni 90 secondi, solo se la pagina è in vista)
        document.addEventListener("visibilitychange", function () { if (document.visibilityState === "visible" && S.stato !== "attesa") carica(true); });
        setInterval(function () { if (document.visibilityState === "visible" && S.stato === "pronto") carica(true); }, 90000);
      }
      VISTE = [{ root: root, compatta: true, re: null }, { root: ltd, compatta: false, re: null }];
      VISTE.forEach(collega);
    }
    S.gen++; S.ed = ed; S.d = null; S.stato = "attesa"; S.aperti = {}; S.miei = {}; S.ord = "top";
    VISTE.forEach(function (v) { rispostaA(v, null); errore(v, ""); });
    rendi(); carica(false);
  }
  window.LETTORI = { monta: monta };
})();
