/* Gommberg Terminal Daily - i mercati spiegati in una riga, uguali su tutto il sito.
   GM.nome(etichetta)  -> il nome da mostrare ("MSCI ACWI (ETF)" -> "Mondo")
   GM.spiega(etichetta) -> la spiegazione breve, o "" se il mercato non è in elenco
   GM.segna(elemento, etichetta) -> aggiunge la spiegazione all'elemento (riquadro al passaggio o al tocco)
   Ogni elemento con l'attributo data-mk="etichetta" viene segnato da solo al caricamento. */
(function () {
  "use strict";
  const M = [
    [/acwi|mondo|azionario mondiale|borsa mondiale/i, "Mondo",
      "La borsa mondiale: l'indice MSCI ACWI, circa 2.500 aziende di 47 paesi. È il nostro termometro unico. Qui il suo prezzo in dollari."],
    [/s&(amp;)?p\s*500/i, "S&P 500",
      "Le 500 maggiori aziende quotate negli Stati Uniti: il termometro di Wall Street."],
    [/nasdaq/i, "Nasdaq",
      "La borsa americana dei titoli tecnologici: Apple, Microsoft, Nvidia e le altre."],
    [/stoxx/i, "Euro Stoxx 50",
      "Le 50 maggiori aziende dei paesi dell'euro: il termometro delle borse europee."],
    [/ftse\s*mib/i, "FTSE MIB",
      "Le 40 maggiori aziende quotate a Piazza Affari, Milano."],
    [/ust|treasury/i, "Treasury 10 anni",
      "Il rendimento dei titoli di Stato USA a 10 anni: il tasso di riferimento per mutui e prestiti nel mondo. Sale quando i prezzi dei titoli scendono."],
    [/brent/i, "Brent",
      "Il prezzo del petrolio di riferimento in Europa, in dollari al barile."],
    [/eur\s*\/\s*usd|euro-dollaro/i, "EUR/USD",
      "Quanti dollari servono per comprare un euro. Se sale, l'euro si rafforza."],
    [/\bvix\b/i, "VIX",
      "L'indice della paura: quanto il mercato si aspetta che Wall Street oscilli nel prossimo mese. Sopra 20 c'è tensione."],
    [/\boro\b|gold/i, "Oro",
      "Il prezzo dell'oro in dollari per oncia: il bene rifugio per eccellenza."],
    [/bitcoin/i, "Bitcoin",
      "La criptovaluta più diffusa, in dollari: molto più volatile delle borse."],
  ];
  const trova = (l) => M.find(([re]) => re.test(String(l || "")));
  const nome = (l) => /acwi/i.test(String(l || "")) ? "Mondo" : String(l || "");   // l'unico nome che cambiamo: la sigla diventa una parola
  const spiega = (l) => { const m = trova(l); return m ? m[2] : ""; };

  // un solo riquadro per pagina, tenuto dentro lo schermo
  let tip = null, cur = null;
  function mostra(elm) {
    if (!tip) { tip = document.createElement("div"); tip.className = "gm-tip"; tip.setAttribute("role", "tooltip"); document.body.appendChild(tip); }
    cur = elm; tip.innerHTML = "";
    const b = document.createElement("b"); b.textContent = elm.dataset.mkNome; tip.appendChild(b);
    tip.appendChild(document.createTextNode(" " + elm.dataset.mkSpiega));
    tip.hidden = false;
    const r = elm.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
    let x = r.left + r.width / 2 - w / 2; x = Math.max(8, Math.min(x, window.innerWidth - w - 8));
    let y = r.bottom + 8; if (y + h > window.innerHeight - 8) y = r.top - h - 8;
    tip.style.left = (x + window.scrollX) + "px"; tip.style.top = (y + window.scrollY) + "px";
  }
  function nascondi() { if (tip) tip.hidden = true; cur = null; }
  function segna(elm, l) {
    const s = spiega(l); if (!elm || !s) return;
    elm.dataset.mkNome = nome(l); elm.dataset.mkSpiega = s;
    elm.classList.add("gm-mk"); elm.tabIndex = 0; elm.removeAttribute("title");
    elm.setAttribute("aria-label", nome(l) + ": " + s);
    elm.addEventListener("mouseenter", () => mostra(elm));
    elm.addEventListener("mouseleave", nascondi);
    elm.addEventListener("focus", () => mostra(elm));
    elm.addEventListener("blur", nascondi);
    elm.addEventListener("click", (e) => { if (cur === elm && !tip.hidden) { nascondi(); } else { mostra(elm); } e.stopPropagation(); });
  }
  document.addEventListener("click", nascondi);
  window.addEventListener("scroll", nascondi, { passive: true });

  const css = document.createElement("style");
  css.textContent = ".gm-mk{cursor:help;text-decoration:underline dotted;text-decoration-thickness:1px;text-underline-offset:3px;text-decoration-color:currentColor}" +
    ".gm-mk:focus-visible{outline:2px solid #F26B1D;outline-offset:2px}" +
    ".gm-tip{position:absolute;z-index:50;max-width:290px;padding:9px 11px;background:#141414;color:#FBFAF8;border-top:2px solid #F26B1D;" +
    "font:13px/1.45 'IBM Plex Sans','Helvetica Neue',Arial,sans-serif;box-shadow:0 6px 18px rgba(0,0,0,.18);pointer-events:none}" +
    ".gm-tip b{font-weight:600;color:#F26B1D}";
  document.head.appendChild(css);

  window.GM = { nome, spiega, segna };
  const auto = () => document.querySelectorAll("[data-mk]").forEach((e) => segna(e, e.dataset.mk || e.textContent));
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", auto); else auto();
})();
