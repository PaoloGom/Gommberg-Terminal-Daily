/* Gommberg Terminal Daily - la barra "Redazione" (G-51). La aggiunge a ogni pagina redazione/sito/costruisci.py.
   La vede solo Paolo quando è collegato all'area riservata (gommberg.com/redazione/): Pannello, Posta, Esci.
   Per i lettori non fa nulla, nemmeno una richiesta: chiede la sessione al servizio solo se c'è il cookie gtd_red=1,
   che l'accesso scrive accanto al cookie di sessione vero (quello, gli script non lo possono leggere).
   window.gtdRedazione() è la stessa promessa che usa la Gommunity (assets/lettori.js) per la firma della redazione. */
(function () {
  "use strict";
  var POSTA = "https://mail.google.com/mail/u/0/#label/Gommberg";   // la cartella del Gommberg in Gmail (la stessa del pannello)
  if (!window.gtdRedazione) {
    var p = null;
    window.gtdRedazione = function () {
      if (!p) p = !/(?:^|;\s*)gtd_red=1(?:;|$)/.test(document.cookie) ? Promise.resolve(null)
        : fetch("/api/redazione/sessione", { cache: "no-store", credentials: "same-origin" }).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
      return p;
    };
  }
  window.gtdRedazione().then(function (s) {
    if (!s || document.querySelector(".rd-bar")) return;
    var st = document.createElement("style");
    st.textContent = ".rd-bar{background:#000;color:#CFC9C1;border-bottom:1px solid #262422;font:12.5px/1 'IBM Plex Mono',ui-monospace,Menlo,monospace;position:relative;z-index:50}"
      + ".rd-in{max-width:1180px;margin:0 auto;padding:0 24px;height:34px;display:flex;align-items:center;justify-content:space-between;gap:14px}"
      + ".rd-who{display:flex;align-items:center;gap:8px;color:#F5F3EF;white-space:nowrap}.rd-who i{width:7px;height:7px;border-radius:50%;background:#F26B1D}"
      + ".rd-who b{color:#F26B1D;font-weight:500;letter-spacing:.08em}.rd-who span{color:#8E877E}"
      + ".rd-nav{display:flex;align-items:center;gap:20px;white-space:nowrap}"
      + ".rd-nav a,.rd-nav button{color:#E4DFD8;text-decoration:none;display:inline-flex;align-items:center;gap:6px;background:none;border:0;padding:0;font:inherit;cursor:pointer}"
      + ".rd-nav a:hover,.rd-nav button:hover{color:#fff}.rd-nav em{font-style:normal;background:#C0261C;color:#fff;font-size:11px;padding:1px 6px;border-radius:9px}"
      + ".rd-nav .esci{color:#F2A27A}@media (max-width:760px){.rd-in{padding:0 14px;height:36px}.rd-who span{display:none}.rd-nav{gap:16px}}";
    document.head.appendChild(st);
    var bar = document.createElement("div"); bar.className = "rd-bar";
    bar.innerHTML = '<div class="rd-in"><span class="rd-who"><i></i><b>REDAZIONE</b><span>· collegato come Gommberg</span></span>'
      + '<nav class="rd-nav" aria-label="Redazione"><a href="/redazione/">Pannello</a><a target="_blank" rel="noopener">Posta</a><button type="button" class="esci">Esci</button></nav></div>';
    bar.querySelectorAll("a")[1].href = POSTA;
    document.body.insertBefore(bar, document.body.firstChild);
    // le segnalazioni aperte, accanto a Pannello
    fetch("/api/redazione/riepilogo", { cache: "no-store", credentials: "same-origin" }).then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
      if (j && j.guardare) { var em = document.createElement("em"); em.textContent = String(j.guardare); em.title = "Segnalazioni da guardare"; bar.querySelector(".rd-nav a").appendChild(em); }
    }, function () {});
    bar.querySelector(".esci").addEventListener("click", function () {
      fetch("/api/redazione/esci", { method: "POST", headers: { "content-type": "application/json", "x-csrf": s.csrf }, body: "{}", credentials: "same-origin" })
        .then(function () { location.reload(); }, function () { location.reload(); });
    });
  });
})();
