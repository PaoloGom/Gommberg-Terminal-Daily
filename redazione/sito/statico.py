#!/usr/bin/env python3
"""Il sito leggibile anche senza JavaScript: per i motori di ricerca (Google, Bing e chi non esegue il JavaScript).
Lo chiama costruisci.py e scrive SOLO nella cartella del sito pubblico, mai nel repository: la pipeline del mattino
(pubblica.sh, pagine.py) non cambia, e a ogni push su main il sito si ricostruisce con l'ultima edizione (G-35).

1. impara/<parola>.html  una pagina per ogni parola di Impara con la sua spiegazione e una per ogni meccanismo di
   "Come si muovono i mercati": titolo, descrizione e dati strutturati propri, legami tra parole, meccanismi ed
   edizioni. Sono le pagine che rispondono a ricerche come "cos'è lo spread" o "cosa misura il VIX".
2. Contenuto di riserva nelle pagine fisse che si riempiono via JavaScript: al posto di "Caricamento..." c'è già il
   testo vero, con la stessa struttura che il JavaScript poi riscrive. Home: titolo, In 30 secondi, analisi e ultime
   edizioni dell'ultima edizione; Impara: tutte le parole, con il link alla loro pagina; Archivio: tutte le edizioni.
3. sitemap.xml: aggiunge le pagine di Impara a quella generata da pagine.py.

Fonti, tutte nel repository: edizioni.json, redazione/glossario.json, glossario_sito.json, meccanismi.json, e
dati/parole.json (le parole spiegate dalle edizioni, scritte da impara.py: una scheda scritta a mano vince sempre).
Solo libreria standard (gira su GitHub senza installare nulla). Se un dato manca, la pagina resta com'era.
"""
import html
import json
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "redazione"))
import pagine  # noqa: E402  (testata, menu, piè di pagina, stile e ancore: una sola fonte per tutto il sito)

BASE = pagine.BASE
esc = pagine.esc
CARTELLA = "impara"
MESI = pagine.MESI
GG = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]
ORD_AREE = ["Tassi e obbligazioni", "Dati e attese", "Borse", "Valute", "Energia e materie prime", "Commercio"]


def fold(s):
    """Come fold() di glossario.html: minuscole, senza accenti."""
    s = unicodedata.normalize("NFD", str(s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def cap(s):
    s = str(s or "")
    return s[:1].upper() + s[1:]


def leggi(rel, vuoto):
    try:
        return json.loads((REPO / rel).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return vuoto


def corto(testo, n=158):
    """Descrizione per i risultati di ricerca: una o due frasi intere entro n caratteri."""
    t = re.sub(r"\s+", " ", str(testo or "")).strip()
    if len(t) <= n:
        return t
    frasi, out = re.split(r"(?<=[.!?])\s+", t), ""
    for f in frasi:
        if len(out) + len(f) + 1 > n:
            break
        out = (out + " " + f).strip()
    # una frase sola e corta direbbe poco nei risultati: meglio il testo fino al limite, tagliato su una parola
    return out if len(out) >= 100 else t[: n - 1].rsplit(" ", 1)[0].rstrip(",;:") + "…"


# ---------------------------------------------------------------- i dati di Impara (stessa logica di glossario.html)
def dati():
    G = leggi("redazione/glossario.json", {})
    S = leggi("redazione/glossario_sito.json", {})
    M = leggi("redazione/meccanismi.json", {})
    E = [e for e in leggi("edizioni.json", []) if isinstance(e, dict) and e.get("numero") and e.get("data") and e.get("titolo")]
    E.sort(key=lambda e: e["numero"], reverse=True)
    # le analisi con pagina (G-64): pagine.py le segna in dati/indice.json ("a" = [chiave, tema]), da lì l'indirizzo
    AN = {r.get("n"): r.get("a") for r in leggi("dati/indice.json", []) if isinstance(r, dict) and r.get("a")}
    for e in E:
        e["_analisi"] = [(t or k, f"e/{pagine.nnn(e['numero'])}/{k}.html") for k, t in AN.get(e["numero"]) or []]
    SV, SM = S.get("voci") or {}, S.get("meccanismi") or {}
    base = [v for v in G.get("voci") or [] if v.get("sigla") and v.get("breve")]
    note = {v["sigla"] for v in base}
    extra = [{"sigla": k, "breve": v["breve"]} for k, v in SV.items() if k not in note and v.get("breve")]
    parole = []
    for v in base + extra:
        s = SV.get(v["sigla"]) or {}
        parole.append({"sigla": v["sigla"], "slug": pagine.ancora(v["sigla"])[2:], "titolo": s.get("titolo") or v["sigla"],
                       "esteso": s.get("esteso") or "", "tipo": s.get("tipo") or "", "breve": v["breve"],
                       "spiega": s.get("spiega") or "", "esempio": s.get("esempio") or "", "borsa": s.get("borsa") or "",
                       "mecc": s.get("mecc") or "", "fonte": s.get("fonte") or None})
    # le parole spiegate dalle edizioni (dati/parole.json, G-54): senza esempio né "E la borsa?", senza parole vicine
    W = leggi("dati/parole.json", {})
    scritte = {fold(v["sigla"]) for v in parole}
    for v in W.get("voci") or []:
        if v.get("sigla") and v.get("breve") and v.get("spiega") and fold(v["sigla"]) not in scritte:
            parole.append({"sigla": v["sigla"], "slug": pagine.ancora(v["sigla"])[2:], "titolo": v["sigla"],
                           "esteso": " · ".join(v.get("varianti") or []), "tipo": W.get("tipo") or "Dalle edizioni",
                           "breve": v["breve"], "spiega": v["spiega"], "esempio": "", "borsa": "", "mecc": "", "fonte": None,
                           "giornale": True, "varianti": list(v.get("varianti") or [])})
    ALIAS.clear()
    ALIAS.update({k: fold(x) for k, x in (W.get("alias") or {}).items()})
    parole.sort(key=lambda v: fold(v["sigla"]))
    mecc = []
    for m in M.get("voci") or []:
        if not (m.get("id") and m.get("titolo") and m.get("testo")):
            continue
        t = SM.get(m["id"]) or {}
        mecc.append({"id": m["id"], "slug": pagine.ancora(m["titolo"])[2:], "titolo": m["titolo"], "area": m.get("area") or "Altri",
                     "spiega": t.get("spiega") or m["testo"], "esempio": t.get("esempio") or "",
                     "nonvale": t.get("nonvale") or m.get("eccezioni") or ""})
    mecc.sort(key=lambda m: ((ORD_AREE.index(m["area"]) if m["area"] in ORD_AREE else 99), m["id"]))
    # una pagina solo per chi ha una spiegazione vera; indirizzi unici (in caso di doppione, il meccanismo prende il suffisso)
    visti = set()
    for v in parole:
        v["pagina"] = bool(v["spiega"]) and v["slug"] not in visti and bool(v["slug"])
        if v["pagina"]:
            visti.add(v["slug"])
    for m in mecc:
        if m["slug"] in visti:
            m["slug"] += "-" + m["id"].lower()
        visti.add(m["slug"])
    return parole, mecc, E, S.get("tipi") or []


ALIAS = {}   # parola dell'edizione -> voce di Impara (dati/parole.json), riempito da dati()


def verso(x):
    x = str(x)
    return ALIAS.get(x) or ALIAS.get(x.split(" (")[0]) or fold(x).split(" (")[0]


def usata(e, v):
    """L'edizione usa la parola: stessa regola di glossario.html (sigle dell'edizione e parole spiegate, con i loro alias)."""
    f = fold(v["sigla"])
    return any(fold(x) == f for x in e.get("glossario") or []) or any(verso(x) == f for x in e.get("parole") or [])


def quando(e):
    a, m, d = (int(x) for x in e["data"].split("-"))
    return f"{d} {MESI[m - 1]} {a}"


# ---------------------------------------------------------------- pagine di Impara
CSS_IMPARA = """
.bc{font-family:var(--mono);font-size:13px;color:var(--muted);margin:0 0 18px}.bc a{color:var(--orange-ink);text-decoration:none}
.box{background:var(--panel);padding:14px 16px;margin:0 0 30px;box-shadow:inset 3px 0 0 var(--orange)}.box p{margin:0}
ul.rel{list-style:none;margin:0;padding:0}ul.rel li{padding:9px 0;border-bottom:1px solid var(--rule)}
ul.rel a{text-decoration:none;display:block}ul.rel b{font-weight:600}ul.rel small{display:block;font-family:var(--mono);font-size:12.5px;color:var(--muted)}
.fonte{font-size:14px;color:var(--muted)}.fonte a{color:var(--orange-ink)}
"""


def testa(titolo, desc, url, ld):
    p = ["<!doctype html>\n<html lang=\"it\">\n<head>\n<meta charset=\"utf-8\">",
         '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">',
         f"<title>{esc(titolo)}</title>", f'<meta name="description" content="{esc(desc)}">', f'<link rel="canonical" href="{url}">']
    for k, v in (("og:type", "article"), ("og:site_name", "Gommberg Terminal Daily"), ("og:title", titolo), ("og:description", desc),
                 ("og:url", url), ("og:image", BASE + "assets/copertina.png?v=2"), ("og:locale", "it_IT")):
        p.append(f'<meta property="{k}" content="{esc(v)}">')
    p += ['<meta name="twitter:card" content="summary_large_image">',
          '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>",
          '<meta name="theme-color" content="#0E0E0E">', '<link rel="icon" href="../assets/icona.svg?v=2" type="image/svg+xml">',
          '<link rel="apple-touch-icon" href="../assets/icona-180.png">', '<link rel="stylesheet" href="../assets/sito.css">',
          '<link rel="alternate" type="application/rss+xml" title="Gommberg Terminal Daily" href="../feed.xml">',
          '<link rel="preconnect" href="https://fonts.googleapis.com">',
          '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..100,500..900&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">',
          f"<style>{pagine.CSS}{CSS_IMPARA}</style>",
          f'<script data-goatcounter="{pagine.GC}" async src="https://gc.zgo.at/count.js"></script>', "</head>\n<body>",
          pagine.testata("../", "glossario.html"), '<main class="wrap">']
    return p


def coda(p):
    p += [pagine.invito("../"), "</main>", pagine.piede("../"), "</body>\n</html>\n"]
    return "\n".join(p)


def briciole(ld_nome, url):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Gommberg Terminal Daily", "item": BASE},
        {"@type": "ListItem", "position": 2, "name": "Impara", "item": BASE + "glossario.html"},
        {"@type": "ListItem", "position": 3, "name": ld_nome, "item": url}]}


def sez(titolo, corpo):
    return f"<section><h2>{esc(titolo)}</h2>{corpo}</section>"


def elenco_edizioni(eds, n=8):
    righe = "".join(f'<li><a href="../e/{pagine.nnn(e["numero"])}.html"><small>N. {pagine.nnn(e["numero"])} | {quando(e)}</small>'
                    f'<b>{esc(e["titolo"])}</b></a></li>' for e in eds[:n])
    return f'<ul class="rel">{righe}</ul>'


def pagina_parola(v, parole, mecc, eds):
    url = f"{BASE}{CARTELLA}/{v['slug']}.html"
    nome = v["titolo"] + (f" ({v['esteso']})" if v["esteso"] and fold(v["esteso"]) != fold(v["titolo"]) and not v.get("giornale") else "")
    titolo = f"{nome}: cos'è e perché conta per i mercati | Gommberg"
    desc = corto(v["spiega"])
    m = next((x for x in mecc if x["id"] == v["mecc"]), None)
    uso = [e for e in eds if usata(e, v)]
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "DefinedTerm", "name": v["titolo"], "alternateName": (v.get("varianti") if v.get("giornale") else [x for x in (v["sigla"], v["esteso"]) if x and x != v["titolo"]]) or None,
         "description": v["spiega"], "url": url, "inLanguage": "it-IT",
         "inDefinedTermSet": {"@type": "DefinedTermSet", "name": "Impara: le parole dei mercati", "url": BASE + "glossario.html"}},
        briciole(v["titolo"], url)]}
    ld["@graph"][0] = {k: x for k, x in ld["@graph"][0].items() if x is not None}
    p = testa(titolo, desc, url, ld)
    a = p.append
    a(f'<p class="bc"><a href="../glossario.html">Impara</a> &rsaquo; {esc(v["tipo"] or "Le parole dei mercati")}</p>')
    a(f'<p class="kicker">Le parole dei mercati</p><h1>{esc(v["titolo"])}</h1>')
    if v["esteso"] and fold(v["esteso"]) != fold(v["titolo"]):
        a(f'<p class="meta">{esc(v["esteso"])}</p>')
    if not fold(v["spiega"]).startswith(fold(v["breve"])):   # la scheda nata dal giornale comincia già con la sua breve
        a(f'<p class="dek">{esc(cap(v["breve"]))}</p>')
    a(sez("Cos'è" if v.get("giornale") else "Cos'è e perché conta", f"<p>{esc(v['spiega'])}</p>"))
    if v["esempio"]:
        a(sez("Un esempio", f'<div class="box"><p>{esc(v["esempio"])}</p></div>'))
    if v["borsa"]:
        a(sez("E la borsa?", f"<p>{esc(v['borsa'])}</p>"))
    if m:
        a(sez("Il meccanismo", f'<ul class="rel"><li><a href="{m["slug"]}.html"><small>Come si muovono i mercati | {esc(m["area"])}</small>'
                                f'<b>{esc(m["titolo"])}</b></a></li></ul>'))
    fam = [x for x in parole if x["pagina"] and x is not v and not v.get("giornale")
           and ((v["mecc"] and x["mecc"] == v["mecc"]) or (v["tipo"] and x["tipo"] == v["tipo"]))]
    fam.sort(key=lambda x: (x["mecc"] != v["mecc"] or not v["mecc"], fold(x["sigla"])))
    if fam:
        a(sez("Parole vicine", '<div class="sigle">' + "".join(f'<a href="{x["slug"]}.html"><b>{esc(x["titolo"])}</b> {esc(x["breve"])}</a>'
                                                              for x in fam[:8]) + "</div>"))
    if uso:
        a(sez("Dove l'abbiamo usata", elenco_edizioni(uso) + (f'<p class="tutte">In {len(uso)} edizioni del Gommberg.</p>' if len(uso) > 8 else "")))
    f = v["fonte"]
    if isinstance(f, list) and len(f) >= 2 and str(f[1]).startswith("http"):
        a(f'<p class="fonte">Per approfondire: <a href="{esc(f[1])}" rel="noopener" target="_blank">{esc(f[0])}</a></p>')
    a(f'<p class="tutte"><a href="../glossario.html#{pagine.ancora(v["sigla"])}">Tutte le parole di Impara &rsaquo;</a></p>')
    return coda(p)


def pagina_meccanismo(m, parole, mecc, eds):
    url = f"{BASE}{CARTELLA}/{m['slug']}.html"
    titolo = f"{m['titolo']}: come si muovono i mercati | Gommberg"
    desc = corto(m["spiega"])
    figli = [v for v in parole if v["pagina"] and v["mecc"] == m["id"]]
    uso = [e for e in eds if m["id"] in (e.get("meccanismi") or [])]
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Article", "headline": m["titolo"][:110], "description": desc, "url": url, "mainEntityOfPage": url, "inLanguage": "it-IT",
         "isAccessibleForFree": True, "about": m["area"], "image": [BASE + "assets/copertina.png"],
         "author": {"@type": "NewsMediaOrganization", "name": "Gommberg Terminal Daily", "url": BASE + "progetto.html"},
         "publisher": {"@type": "Organization", "name": "Gommberg Terminal Daily", "url": BASE,
                       "logo": {"@type": "ImageObject", "url": BASE + "assets/copertina.png"}}},
        briciole(m["titolo"], url)]}
    p = testa(titolo, desc, url, ld)
    a = p.append
    a(f'<p class="bc"><a href="../glossario.html">Impara</a> &rsaquo; Come si muovono i mercati</p>')
    a(f'<p class="kicker">{esc(m["area"])}</p><h1>{esc(m["titolo"])}</h1>')
    a(sez("Come funziona", f"<p>{esc(m['spiega'])}</p>"))
    if m["esempio"]:
        a(sez("Un esempio", f'<div class="box"><p>{esc(m["esempio"])}</p></div>'))
    if m["nonvale"]:
        a(sez("Quando non vale", f"<p>{esc(m['nonvale'])}</p>"))
    if figli:
        a(sez("Le parole collegate", '<div class="sigle">' + "".join(f'<a href="{x["slug"]}.html"><b>{esc(x["titolo"])}</b> {esc(x["breve"])}</a>'
                                                                     for x in figli) + "</div>"))
    vicini = [x for x in mecc if x is not m and x["area"] == m["area"]]
    if vicini:
        a(sez("Nella stessa area", '<ul class="rel">' + "".join(f'<li><a href="{x["slug"]}.html"><b>{esc(x["titolo"])}</b></a></li>'
                                                                for x in vicini[:6]) + "</ul>"))
    if uso:
        a(sez("Dove l'abbiamo spiegato", elenco_edizioni(uso)))
    a('<p class="tutte"><a href="../glossario.html">Tutte le parole e i meccanismi di Impara &rsaquo;</a></p>')
    return coda(p)


# ---------------------------------------------------------------- contenuto di riserva nelle pagine fisse
def sostituisci(testo, ident, interno):
    """Riscrive il contenuto dell'elemento con id=ident (un elemento senza figli dello stesso tipo). Se non lo trova,
    il testo resta com'era: una pagina rifatta a mano non si rompe, perde solo il contenuto di riserva."""
    rx = re.compile(r'(<(?P<t>[a-z0-9]+)\b[^>]*\bid="' + re.escape(ident) + r'"[^>]*>)(.*?)(</(?P=t)>)', re.S)
    return rx.sub(lambda mt: mt.group(1) + interno + mt.group(4), testo, count=1)


def riserva_home(t, eds):
    if not eds:
        return t
    ed = eds[0]
    t = sostituisci(t, "headline", esc(ed["titolo"]))
    t = sostituisci(t, "brief", "".join(f"<li>{esc(s)}</li>" for s in ed.get("sommario") or []))
    # Analisi e storie: le stesse righe che disegna index.html (al massimo 7; se dispari la prima apre a tutta riga), come link al PDF
    an, pp = (ed.get("approfondimenti") or [])[:7], (ed.get("dove") or {}).get("approfondimenti") or []
    scheda = leggi(f"e/{pagine.nnn(ed['numero'])}.json", {})   # la copia per il sito: ogni analisi con pagina ha "pagina"
    pagine_an = [x.get("pagina") if isinstance(x, dict) else None for x in scheda.get("approfondimenti") or []]
    def riga(i, x):
        pg = pp[i] if i < len(pp) and pp[i] else None
        corpo = (f'<span class="k">{esc(x.get("tema") or "")}</span><span class="go">{pg or ""}</span><span class="t">{esc(x.get("titolo") or "")}</span>')
        apre = ' class="apre"' if i == 0 and len(an) % 2 else ""
        # il testo sul sito (G-64): stesso ordine delle analisi; vale solo se tutte le analisi hanno la pagina
        testo = f'<a class="an-txt" href="{esc(pagine_an[i])}">Leggi il testo qui &rsaquo;</a>' if i < len(pagine_an) and pagine_an[i] else ""
        return (f'<li{apre}><a class="an-row" href="{esc(ed["file"])}#page={pg}">{corpo}</a>{testo}</li>' if pg
                else f'<li{apre}><div class="an-row">{corpo}</div>{testo}</li>')
    t = sostituisci(t, "anList", "".join(riga(i, x) for i, x in enumerate(an)))
    righe = []
    for e in eds[1:6]:
        a, m, d = (int(x) for x in e["data"].split("-"))
        from datetime import date
        g = GG[date(a, m, d).weekday()]
        righe.append(f'<li><a href="e/{pagine.nnn(e["numero"])}.html"><span class="d"><span>{g} {d} {MESI[m - 1][:3]}  #{pagine.nnn(e["numero"])}</span></span>'
                     f'<span class="t">{esc(e["titolo"])}</span></a></li>')
    return sostituisci(t, "wkList", "".join(righe))


def riserva_impara(t, parole):
    gruppi = {}
    for v in parole:
        c = (re.sub(r"[^a-z0-9]", "", fold(v["sigla"])) or "#")[0]
        gruppi.setdefault(c.upper() if c.isalpha() else "#", []).append(v)
    def card(v):
        corpo = f"<b>{esc(v['titolo'])}</b><span>{esc(cap(v['breve']))}</span>"
        return f'<a class="cd" href="{CARTELLA}/{v["slug"]}.html">{corpo}</a>' if v["pagina"] else f'<span class="cd">{corpo}</span>'
    # le schede di riserva sono link (le vere, del JavaScript, sono pulsanti): stesso aspetto, senza sottolineatura
    interno = '<style>#pan a.cd{text-decoration:none;color:inherit}</style>' if gruppi else ""
    interno += "".join(f'<div class="grp" id="L-{l}"><h3>{l}</h3><div class="cards">' + "".join(card(v) for v in vs) + "</div></div>"
                      for l, vs in gruppi.items())
    return sostituisci(t, "pan", interno) if interno else t


def riserva_archivio(t, eds):
    if not eds:
        return t
    def an(e):
        p = e.get("_analisi") or []
        return ('<p class="ax-an"><span>Le analisi: </span>' + " | ".join(f'<a href="{esc(u)}">{esc(t)}</a>' for t, u in p) + "</p>") if p else ""
    righe = "".join(f'<li><a href="e/{pagine.nnn(e["numero"])}.html">N. {pagine.nnn(e["numero"])} | {quando(e)}: {esc(e["titolo"])}</a>{an(e)}</li>' for e in eds)
    return sostituisci(t, "axList", f'<ul class="ax-rows">{righe}</ul>')


def mappa(t, parole, mecc, oggi):
    righe = "".join(f"<url><loc>{BASE}{CARTELLA}/{x['slug']}.html</loc><lastmod>{oggi}</lastmod><changefreq>monthly</changefreq><priority>0.5</priority></url>\n"
                    for x in [v for v in parole if v["pagina"]] + mecc)
    return t.replace("</urlset>", righe + "</urlset>", 1) if "</urlset>" in t and righe else t


# ---------------------------------------------------------------- ingresso
def scrivi_tutto(uscita: Path):
    """Scrive nella cartella del sito pubblico. Torna l'elenco dei file nuovi (relativi), per costruisci.py."""
    parole, mecc, eds, _ = dati()
    nuovi = []
    if parole or mecc:
        (uscita / CARTELLA).mkdir(parents=True, exist_ok=True)
        for v in parole:
            if v["pagina"]:
                (uscita / CARTELLA / f"{v['slug']}.html").write_text(pagina_parola(v, parole, mecc, eds), encoding="utf-8")
                nuovi.append(f"{CARTELLA}/{v['slug']}.html")
        for m in mecc:
            (uscita / CARTELLA / f"{m['slug']}.html").write_text(pagina_meccanismo(m, parole, mecc, eds), encoding="utf-8")
            nuovi.append(f"{CARTELLA}/{m['slug']}.html")
    for nome, fn in (("index.html", lambda t: riserva_home(t, eds)), ("glossario.html", lambda t: riserva_impara(t, parole)),
                     ("archivio.html", lambda t: riserva_archivio(t, eds)),
                     ("sitemap.xml", lambda t: mappa(t, parole, mecc, eds[0]["data"] if eds else ""))):
        f = uscita / nome
        if f.is_file():
            t = f.read_text(encoding="utf-8")
            n = fn(t)
            if n != t:
                f.write_text(n, encoding="utf-8")
    return nuovi


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Uso: python3 redazione/sito/statico.py <cartella del sito pubblico>  (di solito lo chiama costruisci.py)")
    print(f"Pagine di Impara: {len(scrivi_tutto(Path(sys.argv[1]).resolve()))}")
