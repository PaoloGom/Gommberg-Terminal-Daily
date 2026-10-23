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
        corti = {"MSCI ACWI (ETF)": "ACWI", "EURO STOXX 50": "STOXX 50", "UST 10 ANNI": "UST 10A", "BRENT FUTURE": "BRENT"}
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
.mast{background:var(--bar);color:var(--bar-ink);border-bottom:3px solid var(--orange)}
.mast .wrap{display:flex;justify-content:space-between;align-items:center;gap:16px;padding-block:14px}
.logo{font-family:var(--display);font-weight:800;font-size:22px;letter-spacing:-.01em;text-decoration:none;white-space:nowrap}
.logo b{color:var(--orange)}.logo span{font-weight:600}
.mast nav{font-family:var(--mono);font-size:13px;color:var(--bar-muted)}.mast nav a{text-decoration:none}.mast nav a:hover{color:var(--bar-ink)}
main{padding-block:36px 56px}
.kicker{font-family:var(--body);font-size:13px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--orange-ink);margin:0 0 8px}
.meta{font-family:var(--mono);font-size:13px;color:var(--muted);margin:0 0 10px}
h1{font-family:var(--display);font-weight:800;font-size:clamp(30px,6vw,44px);line-height:1.08;letter-spacing:-.015em;margin:0 0 14px}
.dek{font-size:18px;color:var(--muted);margin:0 0 22px}
.actions{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 34px}
.btn{display:inline-flex;align-items:center;min-height:44px;padding:0 18px;font-family:var(--mono);font-size:14px;text-decoration:none;border:1px solid var(--ink)}
.btn.lead{background:var(--ink);color:var(--paper)}.btn.ghost{background:transparent}
section{margin:0 0 30px}
h2{font-family:var(--body);font-size:13px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--orange-ink);margin:0 0 12px;padding-bottom:8px;border-bottom:1px solid var(--rule)}
ul.brief{list-style:none;margin:0;padding:0}ul.brief li{position:relative;padding-left:20px;margin:0 0 12px}
ul.brief li:before{content:"";position:absolute;left:0;top:.62em;width:8px;height:8px;background:var(--orange)}
ol.news{list-style:none;margin:0;padding:0;counter-reset:n}
ol.news li{counter-increment:n;display:grid;grid-template-columns:40px 1fr;gap:6px;padding:10px 0;border-bottom:1px solid var(--rule);font-family:var(--display);font-weight:700;font-size:18px;line-height:1.3}
ol.news li:before{content:counter(n,decimal-leading-zero);font-family:var(--display);font-weight:800;color:var(--orange);font-size:20px}
.inside{display:grid;gap:10px}.inside div{background:var(--panel);padding:12px 14px}
.inside small{display:block;font-family:var(--mono);font-size:12px;color:var(--orange-ink);text-transform:uppercase;letter-spacing:.04em}
.inside b{font-weight:600}
.sigle{display:flex;flex-wrap:wrap;gap:8px}.sigle a{display:inline-block;border:1px solid var(--rule);padding:6px 10px;font-size:14px;color:var(--muted);text-decoration:none;line-height:1.35}
.sigle a b{color:var(--ink);font-weight:600;margin-right:4px}.sigle a:hover{border-color:var(--orange)}
.tutte{margin:12px 0 0;font-size:14px}.tutte a{color:var(--orange-ink)}
.errata{background:var(--panel);border-left:3px solid var(--orange);padding:12px 14px;font-size:15px}
.pn{display:flex;justify-content:space-between;gap:12px;font-family:var(--mono);font-size:13px;border-top:1px solid var(--rule);padding-top:16px}
.pn a{text-decoration:none;color:var(--muted)}.pn a:hover{color:var(--ink)}
footer{border-top:1px solid var(--rule);padding:22px 0 36px;font-size:13px;color:var(--muted)}
.vote{display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px;margin:0 0 30px;font-size:15px;color:var(--muted)}
.vote button{font-family:var(--mono);font-size:13px;min-height:38px;padding:0 14px;background:transparent;color:var(--ink);border:1px solid var(--rule);cursor:pointer}
.vote .thx{color:var(--ink)}
@media (max-width:520px){.mast nav{display:none}.dek{font-size:17px}.btn{flex:1 1 auto;justify-content:center}}
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
  document.querySelectorAll("a[data-pdf]").forEach(function (a) {
    a.addEventListener("click", function () { conta({ path: "pdf-NNN", title: "PDF n. NNN " + a.dataset.pdf + " dalla pagina dell'edizione", event: true }); conta({ path: "pdf-tutte", title: "PDF aperti (tutte le edizioni)", event: true }); });
  });
})();
</script>"""


def ancora(s):
    """Stessa ancora di basi.html (Glossario): minuscole, senza accenti, solo lettere e cifre unite da '-'."""
    s = unicodedata.normalize("NFD", str(s).lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return "g-" + re.sub(r"[^a-z0-9]+", "-", s).strip("-")


GLOSSARIO = {}   # sigla in minuscolo -> (sigla, breve), solo le voci non ovvie; riempito in main()


def pagina(ed, prec, succ):
    n = nnn(ed["numero"])
    url = f"{BASE}e/{n}.html"
    data = data_lunga(ed["data"])
    titolo = ed.get("titolo", "")
    desc = ed.get("dek") or " ".join(ed.get("sommario") or [])[:300]
    pdf = "../" + ed["file"]
    p = []
    a = p.append
    a("<!doctype html>\n<html lang=\"it\">\n<head>\n<meta charset=\"utf-8\">")
    a('<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">')
    a(f"<title>{esc(titolo)} | Gommberg Terminal Daily n. {n}</title>")
    a(f'<meta name="description" content="{esc(desc)}">')
    a('<meta name="robots" content="noindex, nofollow">')
    a(f'<link rel="canonical" href="{url}">')
    for k, v in (("og:type", "article"), ("og:site_name", "Gommberg Terminal Daily"), ("og:title", titolo),
                 ("og:description", f"N. {n} | {data.capitalize()}. {desc}"), ("og:url", url),
                 ("og:image", f"{BASE}e/{n}.png"), ("og:image:width", "1200"), ("og:image:height", "630"),
                 ("og:locale", "it_IT")):
        a(f'<meta property="{k}" content="{esc(v)}">')
    a('<meta name="twitter:card" content="summary_large_image">')
    a('<meta name="theme-color" content="#0E0E0E">')
    a('<link rel="icon" href="../assets/icona.svg" type="image/svg+xml">')
    a('<link rel="alternate" type="application/rss+xml" title="Gommberg Terminal Daily" href="../feed.xml">')
    a('<link rel="preconnect" href="https://fonts.googleapis.com">')
    a('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..100,500..900&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">')
    a(f"<style>{CSS}</style>")
    a(f'<script data-goatcounter="{GC}" async src="https://gc.zgo.at/count.js"></script>')
    a("</head>\n<body>")
    a('<header class="mast"><div class="wrap"><a class="logo" href="../"><b>GOMMBERG</b> <span>TERMINAL DAILY</span></a>'
      '<nav><a href="../#archivio">Tutte le edizioni</a></nav></div></header>')
    a('<main class="wrap">')
    a(f'<p class="kicker">Edizione n. {n}</p><p class="meta">{esc(data.capitalize())} | {ed.get("pagine", 6)} pagine</p>')
    a(f"<h1>{esc(titolo)}</h1>")
    if ed.get("dek"):
        a(f'<p class="dek">{colora(ed["dek"])}</p>')
    a(f'<div class="actions"><a class="btn lead" data-pdf="letta" href="{esc(pdf)}">Leggi l\'edizione</a>'
      f'<a class="btn ghost" data-pdf="scaricata" href="{esc(pdf)}" download="{esc(ed.get("nome", ""))}">Scarica PDF</a>'
      f'<a class="btn ghost" href="../?n={int(ed["numero"])}">Sfoglia sul sito</a></div>')
    if ed.get("sommario"):
        a('<section><h2>In 30 secondi</h2><ul class="brief">' +
          "".join(f"<li>{colora(s)}</li>" for s in ed["sommario"]) + "</ul></section>")
    if ed.get("notizie"):
        a('<section><h2>Le notizie del giorno</h2><ol class="news">' +
          "".join(f"<li><span>{colora(s)}</span></li>" for s in ed["notizie"]) + "</ol></section>")
    if ed.get("approfondimenti"):
        a('<section><h2>Gli approfondimenti</h2><div class="inside">' +
          "".join(f'<div><small>{esc(x.get("tema", ""))}</small><b>{colora(x.get("titolo", ""))}</b></div>'
                  for x in ed["approfondimenti"]) + "</div></section>")
    sigle = [GLOSSARIO[s.lower()] for s in dict.fromkeys(ed.get("glossario") or []) if s.lower() in GLOSSARIO]
    if sigle:
        a('<section><h2>Le sigle di questa edizione</h2><div class="sigle">' +
          "".join(f'<a href="../basi.html#{ancora(s)}"><b>{esc(s)}</b> {esc(b)}</a>' for s, b in sigle) +
          '</div><p class="tutte"><a href="../basi.html">Tutte le sigle e i meccanismi &rsaquo;</a></p></section>')
    if ed.get("errata"):
        a('<section><p class="errata"><b>Errata corrige.</b> ' + " ".join(colora(x) for x in ed["errata"]) + "</p></section>")
    nav = []
    nav.append(f'<a href="{nnn(prec["numero"])}.html">&lsaquo; N. {nnn(prec["numero"])}</a>' if prec else "<span></span>")
    nav.append(f'<a href="{nnn(succ["numero"])}.html">N. {nnn(succ["numero"])} &rsaquo;</a>' if succ else '<a href="../">Ultima edizione &rsaquo;</a>')
    a('<div class="vote" id="vote" hidden><span id="voteQ">Ti è stata utile questa edizione?</span>'
      '<button type="button" data-v="si">Sì</button><button type="button" data-v="no">No</button></div>')
    a(f'<div class="pn">{"".join(nav)}</div>')
    a("</main>")
    a(VOTO_JS.replace("NNN", n))
    a('<footer><div class="wrap">Gommberg Terminal Daily è una rassegna informativa sui mercati. Non costituisce consulenza '
      "finanziaria né sollecitazione all'investimento. Le probabilità indicate sono stime redazionali soggettive. Dati e notizie "
      "da fonti pubbliche alla data di ciascuna edizione.</div></footer>")
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
    if rec:
        scrivi(os.path.join(repo, "ultima", "index.html"), ultima(rec[0]))
    print(f"Pagine: {len(eds)} edizioni ({cambiati} pagine aggiornate), feed.xml, ultima/")


if __name__ == "__main__":
    main()
