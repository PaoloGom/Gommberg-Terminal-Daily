#!/usr/bin/env python3
"""Pagine del sito generate da edizioni.json (nessun dato a mano, nessuna chiamata di rete).

Crea, per ogni edizione:
  e/NNN.html  pagina dell'edizione: prima pagina in testo, link al PDF, anteprima ricca su WhatsApp
  e/NNN.png   immagine di anteprima 1200x630 (titolo e chiusure, colori per segno)
e inoltre:
  e/pagine.json  numeri delle edizioni con pagina (il sito la usa per i link da condividere)
  feed.xml       feed RSS delle ultime 30 edizioni
  ultima/index.html  link fisso: porta sempre al PDF dell'ultima edizione

Uso: python3 redazione/pagine.py [cartella del repository]   (default: la cartella sopra a questo file)
Idempotente: rigenera tutto da edizioni.json; i PNG di edizioni già presenti si riscrivono solo se cambiano.
"""
import html, io, json, os, re, sys, unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo
from email.utils import format_datetime
from urllib.parse import quote

BASE = "https://paologom.github.io/Gommberg-Terminal-Daily/"
GC = "https://gommberg.goatcounter.com/count"
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto",
        "settembre", "ottobre", "novembre", "dicembre"]
GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
FONT = "/usr/share/fonts/truetype/dejavu/"
ROMA = ZoneInfo("Europe/Rome")

esc = lambda s: html.escape(str(s or ""), quote=True)


def data_lunga(iso):
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{GIORNI[d.weekday()]} {d.day} {MESI[d.month - 1]} {d.year}"


def nnn(n):
    return f"{int(n):03d}"


# Variazioni con segno esplicito colorate: +1,1%  -9 pb  -0,41  (solo quando il segno c'è)
SEGNO = re.compile(r"(?<![\w.,])([+\-−]\d+(?:[.,]\d+)?(?:\s?(?:%|pb|punti))?)")


def colora(testo):
    out = esc(testo)
    return SEGNO.sub(lambda m: f'<span class="{"down" if m.group(1)[0] in "-−" else "up"}">{m.group(1)}</span>', out)


def segno(s):
    m = re.match(r"\s*([+\-−])?\s*(\d+(?:[.,]\d+)?)", str(s or ""))
    if not m or float(m.group(2).replace(",", ".")) == 0:
        return 0
    return -1 if m.group(1) in ("-", "−") else (1 if m.group(1) == "+" else 0)


# ---------------------------------------------------------------- immagine di anteprima
def anteprima(ed, path):
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1200, 630
    BAR, INK, MUTED, OR = (14, 14, 14), (245, 243, 239), (163, 156, 147), (242, 107, 29)
    UP, DOWN = (60, 203, 127), (255, 106, 92)
    f = lambda nome, s: ImageFont.truetype(FONT + nome, s)
    im = Image.new("RGB", (W, H), BAR)
    d = ImageDraw.Draw(im)
    x = 64
    # testata
    fb = f("DejaVuSans-Bold.ttf", 34)
    d.text((x, 48), "GOMMBERG", font=fb, fill=OR)
    d.text((x + d.textlength("GOMMBERG ", font=fb), 48), "TERMINAL DAILY", font=fb, fill=INK)
    meta = f"N. {nnn(ed['numero'])}  |  {data_lunga(ed['data']).capitalize()}"
    fm = f("DejaVuSansMono.ttf", 22)
    d.text((W - x - d.textlength(meta, font=fm), 58), meta, font=fm, fill=MUTED)
    d.line((x, 112, W - x, 112), fill=(51, 51, 51), width=2)
    # titolo: la dimensione più grande che sta in 4 righe
    titolo = ed.get("titolo", "")
    for size in (60, 54, 48, 44, 40, 36):
        ft = f("DejaVuSans-Bold.ttf", size)
        righe, cur = [], ""
        for w in titolo.split():
            prova = (cur + " " + w).strip()
            if d.textlength(prova, font=ft) <= W - 2 * x:
                cur = prova
            else:
                righe.append(cur); cur = w
        righe.append(cur)
        if len(righe) <= 4:
            break
    y = 150
    for r in righe[:4]:
        d.text((x, y), r, font=ft, fill=INK)
        y += int(size * 1.18)
    # chiusure (fino a 5), colori per segno
    t = ed.get("ticker") or []
    if t:
        fl, fv, fc = f("DejaVuSansMono.ttf", 18), f("DejaVuSans-Bold.ttf", 26), f("DejaVuSansMono-Bold.ttf", 20)
        corti = {"MSCI ACWI (ETF)": "MONDO", "EURO STOXX 50": "STOXX 50", "UST 10 ANNI": "TREASURY 10A", "TREASURY 10 ANNI": "TREASURY 10A", "BRENT FUTURE": "BRENT"}
        cols = t[:5]
        cw = (W - 2 * x) / len(cols)
        y0 = H - 150
        d.line((x, y0 - 22, W - x, y0 - 22), fill=(51, 51, 51), width=2)
        for i, (nome, val, var) in enumerate(cols):
            cx = x + i * cw
            d.text((cx, y0), corti.get(nome, nome), font=fl, fill=MUTED)
            d.text((cx, y0 + 28), val, font=fv, fill=INK)
            g = segno(var)
            d.text((cx, y0 + 66), str(var).replace(" g", ""), font=fc, fill=UP if g > 0 else DOWN if g < 0 else MUTED)
    d.rectangle((0, H - 18, W, H), fill=OR)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    nuovo = buf.getvalue()
    if not (os.path.exists(path) and open(path, "rb").read() == nuovo):
        open(path, "wb").write(nuovo)


# ---------------------------------------------------------------- pagina dell'edizione
CSS = """
:root{--paper:#FAF8F4;--ink:#141414;--muted:#6B655E;--rule:#DEDAD4;--panel:#F1EEE9;--orange:#F26B1D;--orange-ink:#B84A0C;
--bar:#0E0E0E;--bar-ink:#F5F3EF;--bar-muted:#A39C93;--up:#12753D;--down:#C0261C;
--display:"Archivo","Arial Narrow","Helvetica Neue",Arial,sans-serif;--body:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif;
--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#121110;--ink:#EDEAE5;--muted:#A49E96;--rule:#2E2B28;
--panel:#1C1A18;--orange:#FF7A2E;--orange-ink:#FF9A5C;--bar:#050505;--up:#46CF85;--down:#FF7466;color-scheme:dark}}
:root[data-theme="dark"]{--paper:#121110;--ink:#EDEAE5;--muted:#A49E96;--rule:#2E2B28;--panel:#1C1A18;--orange:#FF7A2E;
--orange-ink:#FF9A5C;--bar:#050505;--up:#46CF85;--down:#FF7466;color-scheme:dark}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--body);font-size:17px;line-height:1.6;overflow-x:hidden}
a{color:inherit}.up{color:var(--up);font-weight:500}.down{color:var(--down);font-weight:500}
.wrap{max-width:760px;margin:0 auto;padding-inline:20px}
main{padding-block:36px 56px}
.kicker{font-family:var(--body);font-size:13px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--orange-ink);margin:0 0 8px}
.meta{font-family:var(--mono);font-size:13px;color:var(--muted);margin:0 0 10px}
h1{font-family:var(--display);font-weight:800;font-size:clamp(30px,6vw,44px);line-height:1.08;letter-spacing:-.015em;margin:0 0 14px}
.dek{font-size:18px;color:var(--muted);margin:0 0 22px}
.actions{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 34px}
.btn{display:inline-flex;align-items:center;min-height:44px;padding:0 18px;font-family:var(--mono);font-size:14px;text-decoration:none;border:1px solid var(--ink)}
.btn.lead{background:var(--ink);color:var(--paper)}.btn.ghost{background:transparent;color:var(--ink);cursor:pointer;gap:8px}
.btn svg{width:18px;height:18px;flex:none}
section{margin:0 0 30px}
h2{font-family:var(--body);font-size:13px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--orange-ink);margin:0 0 12px;padding-bottom:8px;border-bottom:1px solid var(--rule)}
ul.brief{list-style:none;margin:0;padding:0}ul.brief li{position:relative;padding-left:20px;margin:0 0 12px}
ul.brief li:before{content:"";position:absolute;left:0;top:.62em;width:8px;height:8px;background:var(--orange)}
ol.news{list-style:none;margin:0;padding:0;counter-reset:n}
ol.news li{counter-increment:n;display:grid;grid-template-columns:40px 1fr;gap:6px;padding:10px 0;border-bottom:1px solid var(--rule);font-family:var(--display);font-weight:700;font-size:18px;line-height:1.3}
ol.news li:before{content:counter(n,decimal-leading-zero);font-family:var(--display);font-weight:800;color:var(--orange);font-size:20px}
.inside{display:grid;gap:10px}.inside div{background:var(--panel);padding:12px 14px}
.inside small{display:block;font-family:var(--mono);font-size:12px;color:var(--orange-ink);text-transform:uppercase;letter-spacing:.04em}
.inside b{font-weight:600}.inside a{display:block;text-decoration:none}.inside small i{float:right;font-style:normal;color:var(--muted);text-transform:none;letter-spacing:0}
.ag{list-style:none;margin:0;padding:0}.ag li{padding:12px 0;border-bottom:1px solid var(--rule)}
.ag li.key{background:var(--panel);box-shadow:inset 3px 0 0 var(--orange);padding-inline:14px 10px}
.ag small{display:block;font-family:var(--mono);font-size:12.5px;color:var(--muted)}
.ag b{display:block;font-family:var(--display);font-weight:700;font-size:18px;line-height:1.3}
.ag+.meta{margin-top:12px}.ag p{margin:4px 0 0;font-size:15px;line-height:1.45}.ag p em{font-style:normal;font-weight:600;color:var(--orange-ink)}
.sigle{display:flex;flex-wrap:wrap;gap:8px}.sigle a{display:inline-block;border:1px solid var(--rule);padding:6px 10px;font-size:14px;color:var(--muted);text-decoration:none;line-height:1.35}
.sigle a b{color:var(--ink);font-weight:600;margin-right:4px}.sigle a:hover{border-color:var(--orange);color:var(--ink)}
.sigle a:after{content:"\203A";margin-left:6px;color:var(--orange-ink);font-weight:600}
.tutte{margin:12px 0 0;font-size:14px}.tutte a{color:var(--orange-ink)}
.pn{display:flex;justify-content:space-between;gap:12px;font-family:var(--mono);font-size:13px;border-top:1px solid var(--rule);padding-top:16px}
.pn a{text-decoration:none;color:var(--muted)}.pn a:hover{color:var(--ink)}
.vote{display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px;margin:0 0 30px;font-size:15px;color:var(--muted)}
.vote button{font-family:var(--mono);font-size:13px;min-height:38px;padding:0 14px;background:transparent;color:var(--ink);border:1px solid var(--rule);cursor:pointer}
.vote .thx{color:var(--ink)}
@media (max-width:520px){.dek{font-size:17px}.btn.lead{flex:1 1 auto;justify-content:center}.btn.ghost{width:46px;padding:0;justify-content:center}.btn.ghost span{display:none}.btn[data-pdf="scaricata"]{display:none}}
"""


# Voto e aperture del PDF, contati come eventi GoatCounter anonimi (un voto per edizione e per browser)
VOTO_JS = """<script>
(function () {
  function conta(o, t) { var g = window.goatcounter; if (g && g.count) { try { g.count(o); } catch (e) {} return; } if ((t || 0) < 20) setTimeout(function () { conta(o, (t || 0) + 1); }, 400); }
  var k = "gtd-voto-NNN", v = null, box = document.getElementById("vote"), q = document.getElementById("voteQ");
  try { v = localStorage.getItem(k); } catch (e) {}
  function fatto() { box.querySelectorAll("button").forEach(function (b) { b.hidden = true; }); q.textContent = "Grazie del voto."; q.className = "thx"; }
  box.hidden = false; if (v) fatto();
  box.addEventListener("click", function (e) {
    var b = e.target.closest("button"); if (!b) return;
    conta({ path: "voto-NNN-" + b.dataset.v, title: "Voto " + b.dataset.v + " n. NNN", event: true });
    conta({ path: "voto-" + b.dataset.v, title: "Voto " + b.dataset.v + " (tutte le edizioni)", event: true });
    try { localStorage.setItem(k, b.dataset.v); } catch (err) {}
    fatto();
  });
  var cp = document.getElementById("copy");
  var wa = document.querySelector('a[href^="https://wa.me/"]');
  if (wa) wa.addEventListener("click", function () { conta({ path: "condividi-tutte", title: "Condivisioni (tutte le edizioni)", event: true }); conta({ path: "condividi-whatsapp-NNN", title: "Condivisione WhatsApp n. NNN", event: true }); });
  if (cp) cp.addEventListener("click", function () {
    conta({ path: "condividi-tutte", title: "Condivisioni (tutte le edizioni)", event: true }); conta({ path: "condividi-link-NNN", title: "Link copiato n. NNN", event: true });
    var u = cp.dataset.url, l = cp.querySelector("span"), ok = function () { l.textContent = "Copiato"; setTimeout(function () { l.textContent = "Copia link"; }, 1800); };
    if (navigator.clipboard) navigator.clipboard.writeText(u).then(ok, function () { prompt("Copia il link:", u); }); else prompt("Copia il link:", u);
  });
  // Da PC "Leggi l'edizione" apre la lettura a schermo intero con lo zoom (sul telefono resta il PDF)
  if (window.matchMedia("(min-width: 901px)").matches) {
    var lead = document.querySelector("a.btn.lead"); if (lead) lead.href = "../?n=" + parseInt("NNN", 10) + "&leggi=1";
  }
  document.querySelectorAll("a[data-pdf]").forEach(function (a) {
    a.addEventListener("click", function () { conta({ path: "pdf-NNN", title: "PDF n. NNN " + a.dataset.pdf + " dalla pagina dell'edizione", event: true }); conta({ path: "pdf-tutte", title: "PDF aperti (tutte le edizioni)", event: true }); });
  });
})();
</script>"""


def ancora(s):
    """Stessa ancora di glossario.html: minuscole, senza accenti, solo lettere e cifre unite da '-'."""
    s = unicodedata.normalize("NFD", str(s).lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return "g-" + re.sub(r"[^a-z0-9]+", "-", s).strip("-")


SVG_WA = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2c-1.5 0-3-.4-4.3-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.3-.4.8-1.4.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5c-.2 0-.4.1-.7.3-.2.3-.9.9-.9 2.2s.9 2.5 1 2.7c.1.2 1.8 2.8 4.4 3.9 1.6.7 2.3.8 3.1.6.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.2-1.2-.1-.1-.3-.2-.5-.3Z"/></svg>')
SVG_LINK = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" d="M10 14a4 4 0 0 0 5.7 0l3.6-3.6a4 4 0 0 0-5.7-5.7L12 6.3M14 10a4 4 0 0 0-5.7 0l-3.6 3.6a4 4 0 0 0 5.7 5.7l1.6-1.6"/></svg>')


GLOSSARIO = {}   # sigla in minuscolo -> (sigla, breve), solo le voci non ovvie; riempito in main()


# ---------------------------------------------------------------- testata, menu e piè di pagina comuni
# Stessi elementi su tutte le pagine del sito (stile in assets/sito.css). root = "" per le pagine
# nella cartella principale, "../" per quelle in e/. attivo = la voce del menu da evidenziare.
# Il menu segue ciò che fa il lettore: legge, cerca, impara, gioca. Chi siamo (progetto e numeri) sta in fondo alla pagina.
MENU = (("", "Ultima edizione"), ("archivio.html", "Archivio"), ("glossario.html", "Impara"), ("scommessa.html", "La scommessa"))
PIEDE = MENU + (("progetto.html", "Chi siamo"),)
RIGA_AI = ("Gommberg Terminal Daily è un progetto di Paolo Gommellini. I testi sono generati con l'intelligenza "
           "artificiale e pubblicati in automatico, sotto la sua responsabilità editoriale.")
LEGALE = ("Rassegna informativa sui mercati: non costituisce consulenza finanziaria né sollecitazione all'investimento. "
          "Le probabilità indicate sono stime redazionali soggettive. Dati e notizie da fonti pubbliche alla data di ciascuna edizione.")


def _href(root, h):
    return (root + h) if h else (root or "./")


def menu(root="", attivo=None):
    voci = []
    for h, t in MENU:
        cur = ' aria-current="page"' if h == attivo else ""
        voci.append(f'<a href="{_href(root, h)}"{cur}>{t}</a>')
    return '<nav class="gn-nav" aria-label="Sezioni del sito">' + "".join(voci) + "</nav>"


def testata(root="", attivo=None):
    return ('<header class="gn-mast"><div class="gn-top"><div class="gn-brand">'
            f'<p class="gn-logo"><a href="{root or "./"}" title="Torna all\'ultima edizione"><b>GOMMBERG</b> <span>TERMINAL DAILY</span></a></p>'
            '<p class="gn-pitch">I mercati globali <em>spiegati</em>, ogni mattina in 6 pagine.</p></div>'
            f'{menu(root, attivo)}</div></header>')


def piede(root="", nota=""):
    link = "".join(f'<a href="{_href(root, h)}">{t}</a>' for h, t in PIEDE)
    return ('<footer class="gf"><div class="gf-in">'
            f'<nav class="gf-links" aria-label="Le pagine del sito">{link}<a href="{root}feed.xml">Feed RSS</a></nav>'
            f'<p class="gf-ai">{RIGA_AI}</p><p class="gf-legal">{LEGALE}{(" " + nota) if nota else ""}</p></div></footer>')


def pagina(ed, prec, succ):
    n = nnn(ed["numero"])
    url = f"{BASE}e/{n}.html"
    data = data_lunga(ed["data"])
    titolo = ed.get("titolo", "")
    # v8.3: l'anteprima (WhatsApp, Google) porta la lettura del giorno, non la fila di cifre del sommario
    desc = ed.get("quadro") or ed.get("dek") or " ".join(ed.get("sommario") or [])[:300]
    pdf = "../" + ed["file"]
    p = []
    a = p.append
    a("<!doctype html>\n<html lang=\"it\">\n<head>\n<meta charset=\"utf-8\">")
    a('<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">')
    a(f"<title>{esc(titolo)} | Gommberg Terminal Daily n. {n}</title>")
    a(f'<meta name="description" content="{esc(desc)}">')
    a(f'<link rel="canonical" href="{url}">')
    for k, v in (("og:type", "article"), ("og:site_name", "Gommberg Terminal Daily"), ("og:title", titolo),
                 ("og:description", f"N. {n} | {data.capitalize()}. {desc}"), ("og:url", url),
                 ("og:image", f"{BASE}e/{n}.png"), ("og:image:width", "1200"), ("og:image:height", "630"),
                 ("og:locale", "it_IT")):
        a(f'<meta property="{k}" content="{esc(v)}">')
    a('<meta name="twitter:card" content="summary_large_image">')
    # dati strutturati per Google: articolo di una testata, firmato dal responsabile editoriale
    ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": titolo[:110], "description": desc,
          "datePublished": ed["data"] + "T08:00:00+01:00", "dateModified": ed["data"] + "T08:00:00+01:00",
          "inLanguage": "it-IT", "url": url, "mainEntityOfPage": url, "image": [f"{BASE}e/{n}.png"],
          "isAccessibleForFree": True, "keywords": ", ".join(ed.get("temi") or []),
          "author": {"@type": "Person", "name": "Paolo Gommellini", "url": BASE + "progetto.html"},
          "publisher": {"@type": "Organization", "name": "Gommberg Terminal Daily", "url": BASE,
                        "logo": {"@type": "ImageObject", "url": BASE + "assets/copertina.png"}}}
    a('<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>")
    a('<meta name="theme-color" content="#0E0E0E">')
    a('<link rel="icon" href="../assets/icona.svg" type="image/svg+xml">')
    a('<link rel="stylesheet" href="../assets/sito.css">')
    a('<link rel="alternate" type="application/rss+xml" title="Gommberg Terminal Daily" href="../feed.xml">')
    a('<link rel="preconnect" href="https://fonts.googleapis.com">')
    a('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..100,500..900&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">')
    a(f"<style>{CSS}</style>")
    a(f'<script data-goatcounter="{GC}" async src="https://gc.zgo.at/count.js"></script>')
    a("</head>\n<body>")
    a(testata("../"))
    a('<main class="wrap">')
    a(f'<p class="kicker">Edizione n. {n}</p><p class="meta">{esc(data.capitalize())} | {ed.get("pagine", 6)} pagine</p>')
    a(f"<h1>{esc(titolo)}</h1>")
    if ed.get("dek"):
        a(f'<p class="dek">{colora(ed["dek"])}</p>')
    a(f'<div class="actions"><a class="btn lead" data-pdf="letta" href="{esc(pdf)}">Leggi l\'edizione</a>'
      f'<a class="btn ghost" data-pdf="scaricata" href="{esc(pdf)}" download="{esc(ed.get("nome", ""))}">Scarica PDF</a>'
      f'<a class="btn ghost" href="https://wa.me/?text={quote(titolo + " " + url)}" target="_blank" rel="noopener" aria-label="Condividi su WhatsApp">{SVG_WA}<span>WhatsApp</span></a>'
      f'<button type="button" class="btn ghost" id="copy" data-url="{esc(url)}" aria-label="Copia il link">{SVG_LINK}<span>Copia link</span></button></div>')
    if ed.get("quadro"):   # v8.3: la versione in due minuti, per chi apre dal telefono
        a('<section><h2>Cosa significa</h2><p>' + colora(ed["quadro"]) + '</p>' +
          (f'<p><b>Da guardare oggi:</b> {esc(ed["evento_oggi"])}</p>' if ed.get("evento_oggi") else "") + '</section>')
    if ed.get("sommario"):
        a('<section><h2>In 30 secondi</h2><ul class="brief">' +
          "".join(f"<li>{colora(s)}</li>" for s in ed["sommario"]) + "</ul></section>")
    if ed.get("notizie"):
        a('<section><h2>Le notizie del giorno</h2><ol class="news">' +
          "".join(f"<li><span>{colora(s)}</span></li>" for s in ed["notizie"]) + "</ol></section>")
    dove = ed.get("dove") if isinstance(ed.get("dove"), dict) else {}
    if ed.get("approfondimenti"):
        pp = dove.get("approfondimenti") or []
        riga = []
        for i, x in enumerate(ed["approfondimenti"]):
            pg = pp[i] if i < len(pp) else None
            dentro = (f'<small>{esc(x.get("tema", ""))}{f"<i>pag. {pg}</i>" if pg else ""}</small>'
                      f'<b>{colora(x.get("titolo", ""))}</b>')
            riga.append(f'<div><a data-pdf="letta" href="{esc(pdf)}#page={pg}">{dentro}</a></div>' if pg else f"<div>{dentro}</div>")
        a(f'<section><h2>{"Analisi e storie" if pp else "Gli approfondimenti"}</h2><div class="inside">' + "".join(riga) + "</div></section>")
    if ed.get("agenda"):   # il calendario: quando, cosa, attese, perché conta e (struttura v9) come può muovere i mercati
        righe = []
        for x in ed["agenda"]:
            perche = re.sub(r"^evento n\.?\s*1\s*:?\s*", "", str(x.get("perche") or ""), flags=re.I)
            perche = perche[:1].upper() + perche[1:]
            t = f'<small>{esc(x.get("quando", ""))}</small><b>{esc(x.get("evento", ""))}</b>'
            if x.get("attese"):
                t += f'<p><em>Attese:</em> {colora(x["attese"])}</p>'
            if perche:
                t += f'<p><em>{"Il più atteso" if x.get("chiave") else "Perché conta"}:</em> {esc(perche)}</p>'
            for m in x.get("muove") or []:
                k, _, v = str(m).partition(":")
                t += f'<p><em>{esc(k)}:</em>{esc(v)}</p>' if v else f"<p>{esc(m)}</p>"
            righe.append(('<li class="key">' if x.get("chiave") else "<li>") + t + "</li>")
        a('<section><h2>In agenda</h2><ul class="ag">' + "".join(righe) + "</ul>" +
          ('<p class="meta">Sopra e sotto: come possono muoversi i mercati, di solito, se il dato esce sopra o sotto le attese.</p>'
           if any(x.get("muove") for x in ed["agenda"]) else "") + "</section>")
    sigle = [GLOSSARIO[s.lower()] for s in dict.fromkeys(ed.get("glossario") or []) if s.lower() in GLOSSARIO]
    if sigle:
        a('<section><h2>Le sigle di questa edizione</h2><div class="sigle">' +
          "".join(f'<a href="../glossario.html#{ancora(s)}"><b>{esc(s)}</b> {esc(b)}</a>' for s, b in sigle) +
          '</div><p class="tutte"><a href="../glossario.html">Tutto il glossario &rsaquo;</a></p></section>')
    nav = []
    nav.append(f'<a href="{nnn(prec["numero"])}.html">&lsaquo; N. {nnn(prec["numero"])}</a>' if prec else "<span></span>")
    nav.append(f'<a href="{nnn(succ["numero"])}.html">N. {nnn(succ["numero"])} &rsaquo;</a>' if succ else '<a href="../">Ultima edizione &rsaquo;</a>')
    a('<div class="vote" id="vote" hidden><span id="voteQ">Ti è stata utile questa edizione?</span>'
      '<button type="button" data-v="si">Sì</button><button type="button" data-v="no">No</button></div>')
    a(f'<div class="pn">{"".join(nav)}</div>')
    a("</main>")
    a(VOTO_JS.replace("NNN", n))
    a(piede("../"))
    a("</body>\n</html>\n")
    return "\n".join(p)


# ---------------------------------------------------------------- feed e link fisso
def feed(eds):
    x = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>',
         "<title>Gommberg Terminal Daily</title>", f"<link>{BASE}</link>",
         "<description>I mercati globali spiegati, ogni mattina in 6 pagine.</description>", "<language>it-it</language>",
         f'<atom:link href="{BASE}feed.xml" rel="self" type="application/rss+xml"/>']
    for ed in eds[:30]:
        n = nnn(ed["numero"])
        quando = datetime.strptime(ed["data"] + " 09:45", "%Y-%m-%d %H:%M").replace(tzinfo=ROMA)
        corpo = ed.get("dek") or " ".join(ed.get("sommario") or [])
        x += ["<item>", f"<title>{esc(ed.get('titolo', ''))}</title>", f"<link>{BASE}e/{n}.html</link>",
              f'<guid isPermaLink="true">{BASE}e/{n}.html</guid>', f"<pubDate>{format_datetime(quando)}</pubDate>",
              f"<description>{esc(corpo)}</description>",
              f'<enclosure url="{BASE}{esc(ed["file"])}" type="application/pdf" length="0"/>', "</item>"]
    x.append("</channel></rss>\n")
    return "\n".join(x)


FISSE = (("", "daily", "1.0"), ("archivio.html", "daily", "0.8"), ("glossario.html", "weekly", "0.8"),
         ("scommessa.html", "weekly", "0.6"), ("numeri.html", "daily", "0.5"), ("progetto.html", "monthly", "0.5"))


def mappa_sito(eds):
    """sitemap.xml: le pagine fisse e una riga per edizione (e/NNN.html), da dare a Google Search Console."""
    oggi = eds[0]["data"] if eds else ""
    r = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for h, f, pr in FISSE:
        r.append(f"<url><loc>{BASE}{h}</loc><lastmod>{oggi}</lastmod><changefreq>{f}</changefreq><priority>{pr}</priority></url>")
    for e in eds:
        r.append(f"<url><loc>{BASE}e/{nnn(e['numero'])}.html</loc><lastmod>{e['data']}</lastmod><changefreq>never</changefreq><priority>0.6</priority></url>")
    r.append("</urlset>")
    return "\n".join(r) + "\n"


def ultima(ed):
    dest = "../" + ed["file"]
    return ("<!doctype html>\n<html lang=\"it\"><head><meta charset=\"utf-8\"><meta name=\"robots\" content=\"noindex\">"
            f"<title>Gommberg Terminal Daily, ultima edizione</title><noscript><meta http-equiv=\"refresh\" content=\"0; url={esc(dest)}\"></noscript>"
            # sempre l'ultima di edizioni.json, anche prima che questa pagina sia rigenerata
            "<script>fetch('../edizioni.json',{cache:'no-store'}).then(r=>r.json()).then(l=>{l=l.filter(e=>e&&e.file)"
            f".sort((a,b)=>b.numero-a.numero);location.replace(l.length?'../'+l[0].file:{json.dumps(dest)})}})"
            f".catch(()=>location.replace({json.dumps(dest)}))</script></head><body><p><a href=\"{esc(dest)}\">"
            "Apri l'ultima edizione</a></p></body></html>\n")


def scrivi(path, testo):
    if os.path.exists(path) and open(path, encoding="utf-8").read() == testo:
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(testo)
    return True


# ---------------------------------------------------------------- dati leggeri per il sito (scalabili negli anni)
# edizioni.json resta l'archivio completo della redazione; il sito legge file piccoli generati da qui:
#   dati/recenti.json  le ultime edizioni complete, per la homepage (peso fisso, non cresce)
#   dati/indice.json   una riga breve per edizione, per l'archivio (circa 150 byte a edizione)
#   dati/cerca.json    il testo per la ricerca, caricato solo quando si cerca
#   dati/storico.json  per ogni edizione solo chiusure e sigle, per Le basi e I numeri
#   e/NNN.json         l'edizione completa, per aprire in homepage un numero vecchio (?n=)
RECENTI = 12


def _num(t):
    try:
        return float(re.sub(r"[^\d,.-]", "", str(t)).replace(".", "").replace(",", "."))
    except ValueError:
        return None


def mondo(ed):
    """Riferimento unico del sito: azionario mondiale (MSCI ACWI) -> [chiusura, variazione del giorno o None]."""
    for r in ed.get("ticker") or []:
        if isinstance(r, (list, tuple)) and len(r) >= 3 and "ACWI" in str(r[0]).upper():
            v = _num(r[1])
            g = None if re.search(r"\(\d+/\d+\)", str(r[2])) else _num(r[2])   # (9/10) = dato ripetuto, mercato chiuso
            return [v, g] if v is not None else None
    return None


def dati_sito(repo, rec):
    os.makedirs(os.path.join(repo, "dati"), exist_ok=True)
    js = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":")) + "\n"
    for ed in rec:
        scrivi(os.path.join(repo, "e", nnn(ed["numero"]) + ".json"), js(ed))
    indice = [{"n": e["numero"], "d": e["data"], "al": e.get("ticker_al") or e["data"], "t": e["titolo"],
               "temi": e.get("temi") or [], "m": mondo(e)} for e in rec]
    cerca = {str(e["numero"]): " | ".join(x for x in [e.get("dek") or "", *(e.get("sommario") or []), *(e.get("notizie") or []),
                                                    *[a.get("titolo", "") for a in e.get("approfondimenti") or [] if isinstance(a, dict)],
                                                    " ".join(e.get("glossario") or [])] if x) for e in rec}
    scrivi(os.path.join(repo, "dati", "indice.json"), js(indice))
    scrivi(os.path.join(repo, "dati", "cerca.json"), js(cerca))
    scrivi(os.path.join(repo, "dati", "recenti.json"), js({"totale": len(rec), "edizioni": rec[:RECENTI]}))
    # numeri della redazione per "Il progetto": fatti verificati e fonti citate, dal registro dei fatti di ogni giorno
    import glob
    giorni, fatti, fonti = 0, 0, 0
    for f in glob.glob(os.path.join(repo, "redazione", "fatti", "*.json")):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        giorni += 1; fatti += len(d); fonti += sum(len(x.get("fonti") or []) for x in d if isinstance(x, dict))
    scrivi(os.path.join(repo, "dati", "redazione.json"), js({"edizioni": len(rec), "giorni_registro": giorni, "fatti": fatti, "fonti": fonti,
                                                             "fatti_al_giorno": round(fatti / giorni) if giorni else 0}))
    campi = ("numero", "data", "ticker_al", "titolo", "file", "ticker", "glossario", "meccanismi", "parole")
    scrivi(os.path.join(repo, "dati", "storico.json"), js([{k: e[k] for k in campi if e.get(k)} for e in rec]))


def main():
    repo = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), ".."))
    eds = [e for e in json.load(open(os.path.join(repo, "edizioni.json"), encoding="utf-8"))
           if e.get("numero") and e.get("data") and e.get("file") and e.get("titolo")]
    eds.sort(key=lambda e: e["numero"])
    try:
        for v in json.load(open(os.path.join(repo, "redazione", "glossario.json"), encoding="utf-8"))["voci"]:
            if not v.get("ovvio") and v.get("sigla") and v.get("breve"):
                GLOSSARIO[v["sigla"].lower()] = (v["sigla"], v["breve"])
    except (OSError, ValueError, KeyError):
        pass
    os.makedirs(os.path.join(repo, "e"), exist_ok=True)
    cambiati = 0
    for i, ed in enumerate(eds):
        prec = eds[i - 1] if i > 0 else None
        succ = eds[i + 1] if i + 1 < len(eds) else None
        cambiati += scrivi(os.path.join(repo, "e", nnn(ed["numero"]) + ".html"), pagina(ed, prec, succ))
        anteprima(ed, os.path.join(repo, "e", nnn(ed["numero"]) + ".png"))
    rec = list(reversed(eds))
    scrivi(os.path.join(repo, "e", "pagine.json"), json.dumps([e["numero"] for e in rec]) + "\n")
    scrivi(os.path.join(repo, "feed.xml"), feed(rec))
    scrivi(os.path.join(repo, "sitemap.xml"), mappa_sito(rec))
    if rec:
        scrivi(os.path.join(repo, "ultima", "index.html"), ultima(rec[0]))
    dati_sito(repo, rec)
    print(f"Pagine: {len(eds)} edizioni ({cambiati} pagine aggiornate), feed.xml, ultima/, dati/")


if __name__ == "__main__":
    main()
