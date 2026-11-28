"""G-64 - genera le pagine del mockup (A e B) dal testo vero dell'edizione n. 035 (27/11/2026). Zero token.

Uso (dalla radice del repository):
  python3 redazione/collaudi/2026-11-27/g64/estrai.py . 2026-11-27 redazione/collaudi/2026-11-27/g64/mockup
  python3 redazione/collaudi/2026-11-27/g64/mockup.py
Non tocca pagine.py né le pagine vere: legge e/035.html e scrive solo dentro mockup/.
"""
import html
import json
import os
import re

QUI = os.path.dirname(os.path.abspath(__file__))
M = os.path.join(QUI, "mockup")
RADICE = os.path.abspath(os.path.join(QUI, "..", "..", "..", ".."))
SU = "../../../../../"                       # dal mockup alla radice del sito
D = json.load(open(os.path.join(M, "moduli-2026-11-27.json"), encoding="utf-8"))
E = next(x for x in json.load(open(os.path.join(RADICE, "edizioni.json"), encoding="utf-8")) if x["data"] == D["data"])
NUM = f"{E['numero']:03d}"
PDF = SU + E["file"]
PAG = E["dove"]["approfondimenti"]
SITO = "https://gommberg.com/"
TEMA = """<meta name="robots" content="noindex">
<script>if (/tema=scuro/.test(location.search)) document.documentElement.dataset.theme = "dark";
if (/tema=chiaro/.test(location.search)) document.documentElement.dataset.theme = "light";
if (/misura/.test(location.search)) addEventListener("load", function () { var a = document.querySelector("#analisi, .an"); document.body.dataset.misura = [a ? Math.round(a.getBoundingClientRect().top + scrollY) : -1, document.documentElement.scrollHeight].join(","); });</script>"""
VAR = re.compile(r"(?<![\w,.])([+-]\d+(?:\.\d{3})*(?:,\d+)?\s?(?:%|pb| pb)?)(?![\w])")


def t(s):
    """Testo del sorgente -> HTML, con le variazioni colorate per segno (come il PDF)."""
    s = html.escape(html.unescape(s or ""), quote=False)
    return VAR.sub(lambda m: f'<span class="{"up" if m.group(1)[0] == "+" else "down"}">{m.group(1)}</span>', s)


def figura(g):
    return (f'<figure class="an-fig"><figcaption><b>{t(g["titolo"])}</b><span>{t(g["sottotitolo"])}</span></figcaption>'
            f'<div class="tela"><picture><source media="(max-width:600px)" srcset="{g["svg"][:-4]}-m.svg">'
            f'<img src="{g["svg"]}" alt="{html.escape(g["titolo"])}: {html.escape(g["sottotitolo"])}" loading="lazy"></picture></div></figure>')


def numero(n):
    if not n:
        return ""
    v, _, r = n.partition(":")
    return f'<div class="an-num"><small>Il numero</small><b>{t(v)}</b><span>{t(r.strip())}</span></div>'


def articolo(m, i, h="h3", testa=True):
    g = m["grafici"]
    par = [f"<p>{t(p)}</p>" for p in m["testo"] or []]
    corpo = [figura(g[0])] if g else []
    corpo += par[:2] + [numero(m["numero"])]
    if len(g) > 1:
        corpo.append(figura(g[1]))
    corpo += par[2:]
    k = (f'<p class="an-k"><span>{t(m["tema"])}</span><a data-pdf="letta" href="{PDF}#page={PAG[i]}">pag. {PAG[i]} del giornale</a></p>'
         if testa else "")
    tit = f'<{h} class="an-t">{t(m["titolo"])}</{h}>' if testa else ""
    dek = f'<p class="an-dek">{t(m["perche"])}</p>' if testa else ""
    return (f'<article class="an" id="{m["chiave"]}">{k}{tit}{dek}<div class="an-body">{"".join(corpo)}</div>'
            f'<div class="an-box"><div class="q"><h4>E quindi</h4><p>{t(m["quindi"])}</p></div>'
            f'<div class="g"><h4>Da guardare</h4><p>{t(m["guardare"])}</p></div></div>'
            f'<p class="an-src">{t(m["fonte"])}</p>'
            f'<a class="an-pdf" data-pdf="letta" href="{PDF}#page={PAG[i]}">Leggila impaginata nel giornale, pag. {PAG[i]} <i>&rsaquo;</i></a></article>')


def giornale(extra=""):
    return (f'<aside class="giornale" aria-label="Il giornale di oggi"><a href="{PDF}" data-pdf="letta"><img src="{SU}e/{NUM}.png" alt="Copertina dell\'edizione n. {NUM}"></a>'
            f'<div><small>Il giornale di oggi | n. {NUM} | {E["pagine"]} pagine</small><b>Tutta l\'edizione, impaginata come un quotidiano</b>'
            f'<p>Le analisi con grafici e tabelle, i mercati di ieri, l\'agenda e la scommessa della settimana.{extra}</p>'
            f'<div class="riga"><a class="btn lead" data-pdf="letta" href="{PDF}">Leggi l\'edizione</a>'
            f'<a class="btn ghost" href="{PDF}" download>Scarica PDF</a></div></div></aside>')


def pulisci(h):
    h = h.replace('href="../', f'href="{SU}').replace('src="../', f'src="{SU}')
    h = re.sub(r'<script data-goatcounter[^>]*></script>\n', "", h)
    return h


# ------------------------------------------------------------------ A: testo dentro la pagina dell'edizione
base = open(os.path.join(RADICE, "e", f"{NUM}.html"), encoding="utf-8").read()
a = pulisci(base)
a = a.replace("</head>", f'<link rel="stylesheet" href="analisi.css">\n{TEMA}\n</head>', 1)
sez = re.search(r'<section><h2>Analisi e storie</h2>.*?</section>', a, re.S).group(0)
indice = "".join(f'<li><a href="#{m["chiave"]}"><b>{t(m["titolo"])}</b><small>{t(m["tema"])}</small></a></li>' for m in D["moduli"])
nuova = (f'<section id="analisi"><h2>Analisi e storie</h2><p class="intro">Le {len(D["moduli"])} analisi di oggi, in testo. '
         f'Nel giornale sono alle pag. {PAG[0]}-{PAG[-1]}, impaginate con grafici e tabelle.</p>'
         f'<ol class="an-indice">{indice}</ol>'
         + "".join(articolo(m, i) for i, m in enumerate(D["moduli"]))
         + giornale(' <a href="#lt" style="color:inherit">Di\' la tua nella Gommunity</a>.') + "</section>")
a = a.replace(sez, nuova)
open(os.path.join(M, f"A-edizione-{NUM}.html"), "w", encoding="utf-8").write(a)

# ------------------------------------------------------------------ B: una pagina per ogni analisi
head = base.split("<style>", 1)[1].split("</style>", 1)[0]
B_CSS = """
.wrap{max-width:1180px;padding-inline:24px}
.bc{font-family:var(--mono);font-size:13px;color:var(--muted);margin:0 0 26px}.bc a{color:var(--muted);text-decoration:none;border-bottom:1px solid var(--rule)}
.bc a:hover{color:var(--ink)}
.pg{display:grid;grid-template-columns:minmax(0,700px) 300px;gap:72px;align-items:start;justify-content:space-between}
.pg h1{font-family:var(--display);font-stretch:88%;font-weight:800;font-size:clamp(32px,5.4vw,48px);line-height:1.06;letter-spacing:-.015em;margin:0 0 16px;text-wrap:balance}
.pg .an{border-top:0;padding-top:0}
.meta2{display:flex;flex-wrap:wrap;align-items:center;gap:10px 14px;margin:0 0 30px;padding:12px 0;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}
.meta2 span{font-family:var(--mono);font-size:13px;color:var(--muted);margin-right:auto}
.meta2 .btn.ghost{gap:8px}.meta2 .btn svg{width:18px;height:18px}
.meta2 .btn{min-height:40px;font-size:13.5px}
.rail{position:sticky;top:24px;display:flex;flex-direction:column;gap:26px}
.card{background:var(--bar);color:var(--bar-ink);padding:18px;border-bottom:3px solid var(--orange)}
.card img{display:block;width:100%;height:auto;margin:0 0 14px}
.card small{display:block;font-family:var(--mono);font-size:12px;color:var(--bar-muted);text-transform:uppercase;letter-spacing:.04em}
.card b{display:block;font-family:var(--display);font-stretch:88%;font-weight:800;font-size:21px;line-height:1.15;margin:6px 0 14px}
.card .btn{width:100%;justify-content:center;margin-top:8px}.card .btn.lead{background:var(--orange);border-color:var(--orange);color:#111}
.card .btn.ghost{color:var(--bar-ink);border-color:#5a554f}
.altre h2{margin-bottom:4px}.altre ul{list-style:none;margin:0;padding:0}
.altre li a{display:block;padding:12px 0;border-bottom:1px solid var(--rule);text-decoration:none}
.altre li small{display:block;font-family:var(--body);font-size:12px;font-weight:600;color:var(--orange-ink)}
.altre li b{display:block;font-family:var(--display);font-stretch:90%;font-weight:700;font-size:17px;line-height:1.28;margin-top:2px}
.altre li a:hover b{color:var(--orange-ink)}
.gc{display:flex;flex-wrap:wrap;gap:8px 20px;align-items:center;justify-content:space-between;background:var(--panel);padding:16px 18px;margin:0 0 30px;box-shadow:inset 0 3px 0 var(--orange)}
.gc p{margin:0;font-size:15.5px}.gc b{font-family:var(--display);font-weight:800;font-size:18px;margin-right:6px}
.strip{display:none}
@media (max-width:980px){.pg{grid-template-columns:1fr;gap:10px}.rail{position:static}.rail .card{display:none}
.strip{display:flex;justify-content:space-between;align-items:center;gap:12px;background:var(--panel);font-family:var(--mono);font-size:13px;padding:10px 18px;border-bottom:1px solid var(--rule)}
.strip a{color:var(--orange-ink);text-decoration:none;font-weight:500;white-space:nowrap}}
@media (max-width:520px){.wrap{padding-inline:18px}.meta2 span{width:100%}.meta2 .btn.lead{flex:1 1 auto;justify-content:center}.meta2 .btn.ghost span{display:none}}
"""
WA_SVG = re.search(r"(<svg viewBox=\"0 0 24 24\" aria-hidden=\"true\"><path fill=\"currentColor\".*?</svg>)", base).group(1)
mast, foot = re.search(r"(<header class=\"gn-mast\">.*?</header>)", base, re.S).group(1), re.search(r"(<footer class=\"gf\">.*?</footer>)", base, re.S).group(1)
for i, m in enumerate(D["moduli"]):
    url = f"{SITO}e/{NUM}/{m['chiave']}.html"          # indirizzo proposto: e/035/corea.html
    titolo = html.unescape(m["titolo"])
    ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": titolo, "description": html.unescape(m["perche"]),
          "datePublished": "2026-11-27T08:00:00+01:00", "dateModified": "2026-11-27T08:00:00+01:00", "inLanguage": "it-IT",
          "url": url, "mainEntityOfPage": url, "image": [f"{SITO}e/{NUM}.png"], "isAccessibleForFree": True,
          "articleSection": m["tema"], "isPartOf": {"@type": "PublicationIssue", "issueNumber": E["numero"], "url": f"{SITO}e/{NUM}.html"},
          "author": {"@type": "Organization", "name": "Gommberg Terminal Daily", "url": f"{SITO}progetto.html"},
          "publisher": {"@type": "Organization", "name": "Gommberg Terminal Daily", "url": SITO, "logo": {"@type": "ImageObject", "url": f"{SITO}assets/copertina.png"}}}
    altre = "".join(f'<li><a href="B-analisi-{NUM}-{x["chiave"]}.html"><small>{t(x["tema"])}</small><b>{t(x["titolo"])}</b></a></li>'
                    for x in D["moduli"] if x is not m)
    wa = "https://wa.me/?text=" + re.sub(r"\s", "%20", html.escape(titolo)) + "%20" + url
    pagina = f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{html.escape(titolo)} | Gommberg Terminal Daily</title>
<meta name="description" content="{html.escape(html.unescape(m['perche']))}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article"><meta property="og:title" content="{html.escape(titolo)}"><meta property="og:image" content="{SITO}e/{NUM}.png">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
{TEMA}
<meta name="theme-color" content="#0E0E0E">
<link rel="icon" href="{SU}assets/icona.svg?v=2" type="image/svg+xml">
<link rel="stylesheet" href="{SU}assets/sito.css">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..100,500..900&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{head}{B_CSS}</style>
<link rel="stylesheet" href="analisi.css">
</head>
<body>
{pulisci(mast)}
<div class="strip"><span>Gommberg n. {NUM}</span><a data-pdf="letta" href="{PDF}">Leggi il giornale &rsaquo;</a></div>
<main class="wrap">
<p class="bc"><a href="A-edizione-{NUM}.html">Edizione n. {NUM}</a> | Venerdì 27 novembre 2026 | Analisi e storie</p>
<div class="pg">
<div>
<p class="kicker">{t(m['tema'])}</p>
<h1>{t(m['titolo'])}</h1>
<p class="an-dek">{t(m['perche'])}</p>
<div class="meta2"><span>Pag. {PAG[i]} del giornale | 2 minuti</span><a class="btn lead" data-pdf="letta" href="{PDF}#page={PAG[i]}">Leggi il giornale</a><a class="btn ghost" href="{wa}" target="_blank" rel="noopener" aria-label="Condividi su WhatsApp">{WA_SVG}<span>WhatsApp</span></a></div>
{articolo(m, i, testa=False)}
<div class="gc"><p><b>La Gommunity</b>Tori o orsi su questa storia? Se ne parla sotto l'edizione di oggi.</p><a class="an-pdf" href="A-edizione-{NUM}.html#lt">Di' la tua <i>&rsaquo;</i></a></div>
{giornale()}
</div>
<aside class="rail">
<div class="card"><a href="{PDF}" data-pdf="letta"><img src="{SU}e/{NUM}.png" alt="Copertina dell'edizione n. {NUM}"></a><small>Il giornale di oggi | n. {NUM} | {E['pagine']} pagine</small><b>Tutta l'edizione in 6 pagine, impaginata come un quotidiano</b><a class="btn lead" data-pdf="letta" href="{PDF}">Leggi l'edizione</a><a class="btn ghost" href="{PDF}" download>Scarica PDF</a></div>
<section class="altre"><h2>Le altre analisi di oggi</h2><ul>{altre}</ul></section>
</aside>
</div>
</main>
{pulisci(foot)}
</body>
</html>
"""
    open(os.path.join(M, f"B-analisi-{NUM}-{m['chiave']}.html"), "w", encoding="utf-8").write(pagina)

# B: la pagina dell'edizione resta com'è, ma ogni analisi porta alla sua pagina
b = pulisci(base).replace("</head>", f"{TEMA}\n</head>", 1)
for i, m in enumerate(D["moduli"]):
    b = b.replace(f'<a data-pdf="letta" href="{PDF}#page={PAG[i]}"><small>{m["tema"]}',
                  f'<a href="B-analisi-{NUM}-{m["chiave"]}.html"><small>{m["tema"]}', 1)
b = b.replace("<i>pag. ", "<i>leggi l'analisi | pag. ")
open(os.path.join(M, f"B-edizione-{NUM}.html"), "w", encoding="utf-8").write(b)
print("mockup scritto in", M)
