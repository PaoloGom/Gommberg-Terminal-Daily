#!/usr/bin/env python3
"""Le analisi di "Analisi e storie" anche sul sito: una pagina per analisi, dal testo stampato nel PDF (G-64).

Due tempi, perché il testo di un'edizione non cambia più dopo l'uscita ma le pagine del sito sì (stile, menu):
  1. ESTRAZIONE, una volta per edizione: dai sorgenti archiviati (redazione/sorgenti/AAAA-MM-GG/edizione.py, con le
     riscritture del desk di desk_ok.json applicate come fa il motore prima di impaginare) si scrive
     redazione/sorgenti/AAAA-MM-GG/analisi.json (solo dati: testi e grafici come numeri) e si disegnano i grafici
     in e/NNN/<pagina>-<k>.svg (PC) e -m.svg (telefono), con le stesse funzioni del motore. Gira in un processo a parte
     (edizione.py si esegue: cartella di lavoro, moduli, errori restano fuori da pagine.py). Zero token.
  2. PAGINE, a ogni pubblicazione, da analisi.json: e/NNN/<pagina>.html. Le chiama pagine.py (pagina_edizione()).

Indirizzi: e/NNN/<chiave>.html, dove NNN è il numero dell'edizione e <chiave> la "chiave" del modulo in edizione.py
(corea, europa, oro...): unica nell'edizione (il motore la usa per i rimandi), corta, scelta da chi scrive e non dal
titolo, quindi non cambia se il titolo si corregge; la cartella dell'edizione esclude le collisioni tra giorni.

Non blocca mai: sorgente assente = nessuna pagina (le edizioni fino alla n. 025 restano con il solo PDF); sorgente
rotto (errore del sorgente, o estrazione oltre TEMPO secondi) = analisi.json con "errore" e un AVVISO: non si riprova
a ogni pubblicazione, ma si riprova da solo se edizione.py o desk_ok.json cambiano, o con il comando ritenta; un guasto
dell'ambiente (una libreria che manca) non si salva: si riprova alla pubblicazione successiva;
un'analisi che non corrisponde a edizioni.json (titolo diverso) = quella pagina non nasce, le altre sì.

Uso diretto:
  python3 redazione/analisi_sito.py estrai <cartella sorgenti> <repo> <NNN>   (lo lancia pagine.py)
  python3 redazione/analisi_sito.py disegna <analisi.json> <cartella dei grafici>
  python3 redazione/analisi_sito.py ritenta [AAAA-MM-GG ...]   toglie gli errori salvati (tutti, senza date) e rifà le
                                                               pagine con pagine.py
"""
import hashlib
import datetime as dt
import html
import json
import os
import re
import subprocess
import sys

FORMATO = 1                 # cambia se cambia la forma di analisi.json: le estrazioni si rifanno da sole
CSS_V = "2026-11-28b"       # cambia quando cambia assets/analisi.css (il browser riprende il file nuovo)
FILE = "analisi.json"
TEMPO = 60                  # secondi al massimo per estrarre un'edizione (di solito 3-4)
AMBIENTE = 3                # uscita dell'estrazione per un guasto dell'ambiente: non si salva, si riprova
# misure dei grafici (pollici, scala 1:1 come nel PDF): PC a tutta colonna, telefono più stretto con le scritte leggibili
MISURE = (("", 5.6, 2.45), ("-m", 3.5, 2.4))
CAMPI = ("tema", "titolo", "perche", "quindi", "numero", "testo", "guardare", "fonte", "punti", "righe", "misura")
# Il disegno non dipende dalla macchina: gli id dell'SVG nascono da un seme fisso, e le due impostazioni di matplotlib
# da cui dipende la misura delle scritte (e quindi margini e riquadro) sono dichiarate qui invece di essere quelle che
# la macchina si trova. I valori sono quelli con cui sono nati i grafici pubblicati: la macchina della redazione ha una
# matplotlib che parte da 200 e "no_hinting", una matplotlib appena installata (il collaudo su GitHub) parte da 100 e
# "default", e con la stessa versione disegnava il riquadro fino a 2,6 punti più in là. Con questi valori la stessa
# versione ridà gli stessi byte ovunque; tra versioni diverse cambiano solo id e decimi di punto (collaudo.py,
# stesso_grafico). "no_hinting" misura le scritte con le misure del carattere, senza l'arrotondamento ai pixel.
DISEGNO = {"svg.hashsalt": "gommberg", "figure.dpi": 200, "text.hinting": "no_hinting"}


# ---------------------------------------------------------------- 1. estrazione (processo a parte)
def _dati(x):
    """Il grafico come dato JSON: date -> {"$d": iso}, tuple -> liste (si ricostruiscono in _grafico)."""
    if isinstance(x, (dt.date, dt.datetime)):
        return {"$d": x.isoformat()[:10]}
    if isinstance(x, dict):
        return {k: _dati(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_dati(v) for v in x]
    return x


def _da_dati(x):
    if isinstance(x, dict):
        return dt.date.fromisoformat(x["$d"]) if set(x) == {"$d"} else {k: _da_dati(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_da_dati(v) for v in x]
    return x


def slug(chiave, i, usati):
    s = re.sub(r"[^a-z0-9]+", "-", str(chiave or "").lower()).strip("-")[:40] or f"analisi-{i + 1}"
    while s in usati or s.isdigit():
        s += "-" + str(i + 1)
    usati.add(s)
    return s


def estrai(src, repo):
    """Carica edizione.py (senza impaginare), applica il desk, torna il dizionario di analisi.json."""
    import importlib.util
    import shutil
    import tempfile
    lav = os.path.join(tempfile.mkdtemp(prefix="analisi-"), "lavoro")
    shutil.copytree(src, lav)
    os.environ["GTD_REPO"] = repo
    sys.argv = ["edizione.py", lav]                     # edizione.py fa chdir nella cartella di lavoro
    sys.path.insert(0, os.path.join(repo, "redazione"))
    spec = importlib.util.spec_from_file_location("edizione_archiviata", os.path.join(lav, "edizione.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    C = m.C
    import desk
    desk.applica(C, lav)                                # le stesse riscritture accettate che vanno nel PDF
    usati, moduli = set(), []
    for i, mo in enumerate(C.get("moduli") or []):
        s = slug(mo.get("chiave"), i, usati)
        x = {"chiave": mo.get("chiave"), "pagina": s}
        x.update({k: mo[k] for k in CAMPI if mo.get(k) not in (None, "", [])})
        g = []
        for k in ("grafico", "grafico2"):
            if isinstance(mo.get(k), dict) and (k == "grafico" or mo.get("misura") == "doppio"):
                spec_g = {a: b for a, b in mo[k].items() if a not in ("file", "soggetto", "ruolo", "alto", "largo")}
                g.append({"file": f"{s}-{len(g) + 1}", "dati": _dati(spec_g)})
        if g:
            x["grafici"] = g
        moduli.append(x)
    shutil.rmtree(os.path.dirname(lav), ignore_errors=True)
    return {"formato": FORMATO, "data": str(C.get("data"))[:10], "moduli": moduli}


def _svg_pulito(t):
    """SVG uguale a ogni ridisegno (niente data, numeri a due decimali) e più leggero."""
    t = re.sub(r"<metadata>.*?</metadata>\s*", "", t, flags=re.S)
    return re.sub(r"(?<![\d.])([1-9]\d*\.\d\d)\d+", r"\1", t)   # solo da 1 in su: le scale dei caratteri restano esatte


def disegna(dati, cartella, repo):
    """Disegna i grafici di analisi.json in cartella (e/NNN/). Torna le misure (larghezza, altezza) del grafico per PC."""
    import shutil
    import tempfile
    sys.path.insert(0, os.path.join(repo, "redazione"))
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams.update(DISEGNO)
    import gommberg_engine as G
    os.makedirs(cartella, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="grafici-")
    for mo in dati.get("moduli") or []:
        for g in mo.get("grafici") or []:
            spec = _da_dati(g["dati"])
            tipo = spec.pop("tipo")
            for k in ("titolo", "sottotitolo"):
                spec.pop(k, None)
            if tipo == "linee":
                spec["serie"] = [[n, [tuple(p) if isinstance(p, list) else p for p in v], *c] for n, v, *c in spec.get("serie") or []]
            for suff, largo, alto in MISURE:
                a = dict(spec, largo=largo)
                if tipo == "linee":
                    a["alto"] = alto
                elif not suff:
                    a["alto"] = 0.26 * len(a.get("dati") or []) + 0.5
                p = os.path.join(tmp, g["file"] + suff + ".png")
                {"linee": G.linee, "barre": G.barre}[tipo](p, **a)
                svg = open(p[:-4] + ".svg", encoding="utf-8").read()
                open(os.path.join(cartella, g["file"] + suff + ".svg"), "w", encoding="utf-8").write(_svg_pulito(svg))
                if not suff:
                    w, h = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg).groups()
                    g["misure"] = [round(float(w) * 4 / 3), round(float(h) * 4 / 3)]   # pt -> px
    shutil.rmtree(tmp, ignore_errors=True)
    return dati


def _scrivi_json(path, d):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")


def _cli():
    if len(sys.argv) >= 5 and sys.argv[1] == "estrai":
        src, repo, n = sys.argv[2], os.path.abspath(sys.argv[3]), sys.argv[4]
        out = os.path.join(src, FILE)
        try:
            d = estrai(os.path.abspath(src), repo)
        except ImportError as e:      # manca una libreria (o il motore non si carica): colpa dell'ambiente, non del sorgente
            print(f"ambiente: {type(e).__name__}: {e}", file=sys.stderr)
            sys.exit(AMBIENTE)
        try:
            d = disegna(d, os.path.join(repo, "e", n), repo)
        except ImportError as e:
            print(f"ambiente: {type(e).__name__}: {e}", file=sys.stderr)
            sys.exit(AMBIENTE)
        _scrivi_json(os.path.abspath(out), d)
        print(f"analisi: {len(d['moduli'])} da {src}")
    elif len(sys.argv) >= 2 and sys.argv[1] == "ritenta":
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        tolti = 0
        for data in sorted(os.listdir(os.path.join(repo, "redazione", "sorgenti"))):
            p = os.path.join(repo, "redazione", "sorgenti", data, FILE)
            if (len(sys.argv) == 2 or data in sys.argv[2:]) and os.path.isfile(p):
                try:
                    if json.load(open(p, encoding="utf-8")).get("errore"):
                        os.remove(p); tolti += 1
                except ValueError:
                    os.remove(p); tolti += 1
        print(f"errori tolti: {tolti}")
        subprocess.run([sys.executable, os.path.join(repo, "redazione", "pagine.py"), repo])
    elif len(sys.argv) >= 4 and sys.argv[1] == "disegna":
        d = json.load(open(sys.argv[2], encoding="utf-8"))
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        disegna(d, sys.argv[3], repo)
        print("grafici ridisegnati")
    else:
        sys.exit(__doc__)


# ---------------------------------------------------------------- 2. collegamento con edizioni.json
def _piano(t):
    """Testo del motore (marcatura di reportlab, & e entità) -> testo semplice."""
    t = re.sub(r"\[\[\w+\]\]", "", str(t or ""))
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", t))).strip()


def prepara(repo, ed):
    """analisi.json dell'edizione, estratto se manca (in un processo a parte). None se l'edizione non ha sorgenti o
    l'estrazione è fallita. Non solleva mai: stampa un AVVISO."""
    src = os.path.join(repo, "redazione", "sorgenti", ed["data"])
    if not os.path.isfile(os.path.join(src, "edizione.py")):
        return None
    path = os.path.join(src, FILE)
    n = f"{int(ed['numero']):03d}"
    d = None
    try:
        d = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        pass
    impronta = _impronta(src)
    if d and d.get("errore") and d.get("impronta") != impronta:
        d = None                        # il sorgente è cambiato dopo l'errore: si riprova
    if not d or d.get("formato") != FORMATO:
        try:
            r = subprocess.run([sys.executable, os.path.abspath(__file__), "estrai", src, repo, n],
                               capture_output=True, text=True, timeout=TEMPO)
            if r.returncode == AMBIENTE:
                riga = (r.stderr.strip().splitlines() or ["?"])[-1]
                print(f"AVVISO analisi n. {n}: guasto dell'ambiente ({riga[:160]}): nessuna pagina oggi, si riprova alla prossima pubblicazione")
                return None
            if r.returncode:
                riga = (r.stderr.strip().splitlines() or ["uscita " + str(r.returncode)])[-1]
                _scrivi_json(path, {"formato": FORMATO, "errore": riga[:300], "impronta": impronta})
            d = json.load(open(path, encoding="utf-8"))
        except subprocess.TimeoutExpired:
            d = {"formato": FORMATO, "errore": f"estrazione oltre {TEMPO} secondi", "impronta": impronta}
            _scrivi_json(path, d)
        except Exception as e:  # noqa: BLE001
            print(f"AVVISO analisi n. {n}: estrazione non partita ({str(e)[:160]}): si riprova alla prossima pubblicazione")
            return None
    if d.get("errore"):
        print(f"AVVISO analisi n. {n}: sorgente non leggibile ({d['errore'][:160]}): nessuna pagina di analisi; "
              f"si riprova da solo se il sorgente cambia, o con: python3 redazione/analisi_sito.py ritenta {ed['data']}")
        return None
    mancano = [g["file"] for m in d.get("moduli") or [] for g in m.get("grafici") or []
               if not os.path.exists(os.path.join(repo, "e", n, g["file"] + ".svg"))]
    if mancano:    # i grafici si ridisegnano dai dati, senza rieseguire edizione.py
        try:
            subprocess.run([sys.executable, os.path.abspath(__file__), "disegna", path, os.path.join(repo, "e", n)],
                           capture_output=True, text=True, timeout=300, check=True)
        except Exception as e:  # noqa: BLE001
            print(f"AVVISO analisi n. {n}: grafici non ridisegnati ({str(e)[:120]})")
    return d


def _impronta(src):
    """Impronta di ciò che l'estrazione legge (edizione.py, desk_ok.json): se cambia, un errore salvato si riprova."""
    h = hashlib.sha256()
    for f in ("edizione.py", "desk_ok.json"):
        p = os.path.join(src, f)
        h.update(open(p, "rb").read() if os.path.exists(p) else b"-")
    return h.hexdigest()[:16]


def collega(ed, d):
    """[(indice dell'approfondimento in edizioni.json, modulo)] per le analisi che hanno una pagina: stesso posto e
    stesso titolo che in edizioni.json (la voce dell'indice nasce dallo stesso testo); le altre restano solo nel PDF."""
    if not d:
        return []
    voci, out = ed.get("approfondimenti") or [], []
    for i, m in enumerate(d.get("moduli") or []):
        if i < len(voci) and isinstance(voci[i], dict) and _piano(voci[i].get("titolo")) == _piano(m.get("titolo")) \
                and m.get("perche") and (m.get("testo") or m.get("quindi")):
            out.append((i, m))
        else:
            print(f"AVVISO analisi n. {int(ed['numero']):03d}: '{_piano(m.get('titolo'))[:50]}' non corrisponde a edizioni.json: nessuna pagina")
    return out


def indirizzo(ed, m):
    return f"e/{int(ed['numero']):03d}/{m['pagina']}.html"


# ---------------------------------------------------------------- 3. le pagine
def _t(P, s):
    """Testo del motore -> HTML del sito: variazioni colorate come nel PDF, grassetti e corsivi del testo conservati."""
    pezzi = re.split(r"(<b>.*?</b>|<i>.*?</i>)", re.sub(r"\[\[\w+\]\]", "", str(s or "")))
    out = []
    for x in pezzi:
        m = re.fullmatch(r"<([bi])>(.*?)</\1>", x)
        if m:
            out.append(f"<{m.group(1)}>{P.colora(_piano(m.group(2)))}</{m.group(1)}>")
        elif x:
            out.append((" " if x[0].isspace() else "") + P.colora(_piano(x)) + (" " if x[-1].isspace() and x.strip() else ""))
    return re.sub(r"\s+", " ", "".join(out)).strip()


def _descrizione(t, n=158, seguito=()):
    """Una o più frasi intere entro n caratteri. Se la frase di partenza è corta (sotto i 100 caratteri), si aggiungono
    le frasi che seguono nel testo (seguito), finché ci stanno; se le frasi intere fanno meno di 100 caratteri, il testo
    si taglia a una parola intera con i puntini."""
    t = _piano(t)
    if len(t) < 100:
        for f in re.split(r"(?<=[.!?])\s+", " ".join(_piano(x) for x in seguito)):
            if not f or len(t) + len(f) + 1 > n:
                break
            t = (t + " " + f).strip()
    if len(t) <= n:
        return t
    out = ""
    for f in re.split(r"(?<=[.!?])\s+", t):
        if len(out) + len(f) + 1 > n:
            break
        out = (out + " " + f).strip()
    if len(out) < 100:      # la prima frase da sola dice poco: si taglia la seconda a una parola intera
        out = t[:n - 1].rsplit(" ", 1)[0].rstrip(",;:(") + "…"
    return out


def _figura(P, g, n):
    d = g.get("dati") or {}
    tit, sub = _piano(d.get("titolo")), _piano(d.get("sottotitolo"))
    wh = g.get("misure") or [747, 327]
    alt = P.esc(tit + (": " + sub if sub else ""))
    cap = (f'<figcaption><b>{P.colora(tit)}</b>' + (f'<span>{P.esc(sub)}</span>' if sub else "") + '</figcaption>') if tit else ""
    return (f'<figure class="an-fig">{cap}<div class="tela"><picture><source media="(max-width:600px)" srcset="{g["file"]}-m.svg">'
            f'<img src="{g["file"]}.svg" width="{wh[0]}" height="{wh[1]}" alt="{alt}" loading="lazy" decoding="async"></picture></div></figure>')


def _numero(P, t):
    t = _piano(t)
    if not t:
        return ""
    v, sep, r = t.partition(":")
    if not sep or len(v) > 24:
        return f'<div class="an-num solo"><small>Il numero</small><span>{P.colora(t)}</span></div>'
    # una cifra corta ("-1,8%") sta accanto alla frase; una lunga ("1.384 miliardi di won") sopra, a tutta riga
    lunga = " lunga" if len(v.strip()) > 9 else ""
    return f'<div class="an-num{lunga}"><small>Il numero</small><b>{P.colora(v)}</b><span>{P.colora(r.strip())}</span></div>'


def _tabella(P, righe):
    if not righe or len(righe) < 2:
        return ""
    testa = "".join(f"<th>{P.esc(_piano(c))}</th>" for c in righe[0])
    corpo = "".join("<tr>" + "".join(f"<td>{_t(P, c)}</td>" for c in r) + "</tr>" for r in righe[1:])
    return f'<div class="an-tab"><table><thead><tr>{testa}</tr></thead><tbody>{corpo}</tbody></table></div>'


def corpo(P, m, pdf_pag):
    g = m.get("grafici") or []
    par = [f"<p>{_t(P, x)}</p>" for x in m.get("testo") or []]
    c = [_figura(P, g[0], 0)] if g else []
    c += par[:2] + [_numero(P, m.get("numero"))]
    c += [_figura(P, x, 0) for x in g[1:]]
    if m.get("punti"):
        c.append('<ul class="an-punti">' + "".join(f"<li>{_t(P, x)}</li>" for x in m["punti"][:3]) + "</ul>")
    c.append(_tabella(P, m.get("righe")))
    c += par[2:]
    box = (f'<div class="q"><h3>E quindi</h3><p>{_t(P, m.get("quindi"))}</p></div>' if m.get("quindi") else "")
    box += (f'<div class="g"><h3>Da guardare</h3><p>{_t(P, m.get("guardare"))}</p></div>' if m.get("guardare") else "")
    return ('<div class="an-body">' + "".join(c) + "</div>" + (f'<div class="an-box">{box}</div>' if box else "") +
            (f'<p class="an-src">{P.esc(_piano(m.get("fonte")))}</p>' if m.get("fonte") else ""))


JS = """<script>
(function () {
  function conta(o, t) { var g = window.goatcounter; if (g && g.count) { try { g.count(o); } catch (e) {} return; } if ((t || 0) < 20) setTimeout(function () { conta(o, (t || 0) + 1); }, 400); }
  // Da PC "Leggi il giornale" apre la lettura a schermo intero alla pagina dell'analisi (sul telefono resta il PDF)
  if (window.matchMedia("(min-width: 901px)").matches) {
    document.querySelectorAll("a[data-leggi]").forEach(function (a) { a.href = "../../?n=" + parseInt("NNN", 10) + "&leggi=1&p=" + a.dataset.leggi; });
  }
  document.querySelectorAll("a[data-pdf]").forEach(function (a) { a.addEventListener("click", function () {
    conta({ path: "pdf-NNN", title: "PDF n. NNN " + a.dataset.pdf + " dalla pagina di un'analisi", event: true }); conta({ path: "pdf-tutte", title: "PDF aperti (tutte le edizioni)", event: true }); }); });
  document.querySelectorAll('a[href^="https://wa.me/"]').forEach(function (wa) { wa.addEventListener("click", function () { conta({ path: "condividi-tutte", title: "Condivisioni (tutte le edizioni)", event: true }); conta({ path: "condividi-analisi-NNN", title: "Analisi condivisa n. NNN", event: true }); }); });
  document.querySelectorAll("[data-copy]").forEach(function (cp) { cp.addEventListener("click", function () {
    conta({ path: "condividi-tutte", title: "Condivisioni (tutte le edizioni)", event: true });
    var u = cp.dataset.copy, l = cp.querySelector("span") || cp, prima = l.textContent, ok = function () { l.textContent = "Copiato"; setTimeout(function () { l.textContent = prima; }, 1800); };
    if (navigator.clipboard) navigator.clipboard.writeText(u).then(ok, function () { prompt("Copia il link:", u); }); else prompt("Copia il link:", u);
  }); });
})();
</script>"""


def pagina(P, ed, m, i, altre):
    """La pagina di un'analisi. P = il modulo pagine (testata, menu, piè di pagina, stile e GOMM: una fonte sola).
    altre = [(modulo, indirizzo relativo, pag. del PDF)] delle altre analisi dell'edizione."""
    n = P.nnn(ed["numero"])
    rel = indirizzo(ed, m)
    url = P.BASE + rel
    pp = (ed.get("dove") or {}).get("approfondimenti") or [] if isinstance(ed.get("dove"), dict) else []
    pg = pp[i] if i < len(pp) and pp[i] else None
    pdf = "../../" + ed["file"]
    pdf_pg = pdf + (f"#page={pg}" if pg else "")
    titolo, tema = _piano(m.get("titolo")), _piano(m.get("tema"))
    desc = _descrizione(m.get("perche"), seguito=m.get("testo") or [])
    data = P.data_lunga(ed["data"])
    quando = ed["data"] + "T08:00:00+01:00"
    ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": titolo[:110], "description": desc,
          "datePublished": quando, "dateModified": quando, "inLanguage": "it-IT", "url": url, "mainEntityOfPage": url,
          "image": [f"{P.BASE}e/{n}.png"], "isAccessibleForFree": True, "articleSection": tema,
          "isPartOf": {"@type": "PublicationIssue", "issueNumber": str(int(ed["numero"])), "datePublished": ed["data"],
                       "url": f"{P.BASE}e/{n}.html"},
          "author": {"@type": "NewsMediaOrganization", "name": "Gommberg Terminal Daily", "url": P.BASE + "progetto.html"},
          "publisher": {"@type": "Organization", "name": "Gommberg Terminal Daily", "url": P.BASE,
                        "logo": {"@type": "ImageObject", "url": P.BASE + "assets/copertina.png"}}}
    wa = f"https://wa.me/?text={P.quote(titolo + ' ' + url)}"
    altre_html = "".join(f'<li><a href="{h}"><small>{P.esc(_piano(x.get("tema")))}</small><b>{_t(P, x.get("titolo"))}</b></a></li>'
                         for x, h, _ in altre)
    p = []
    a = p.append
    a('<!doctype html>\n<html lang="it">\n<head>\n<meta charset="utf-8">')
    a('<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">')
    a(f"<title>{P.esc(titolo)} | Gommberg Terminal Daily</title>")
    a(f'<meta name="description" content="{P.esc(desc)}">')
    a(f'<link rel="canonical" href="{url}">')
    for k, v in (("og:type", "article"), ("og:site_name", "Gommberg Terminal Daily"), ("og:title", titolo),
                 ("og:description", desc), ("og:url", url), ("og:image", f"{P.BASE}e/{n}.png"),
                 ("og:image:width", "1200"), ("og:image:height", "630"), ("og:locale", "it_IT"),
                 ("article:published_time", quando), ("article:section", tema)):
        a(f'<meta property="{k}" content="{P.esc(v)}">')
    a('<meta name="twitter:card" content="summary_large_image">')
    a('<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>")
    a('<meta name="theme-color" content="#0E0E0E">')
    a('<link rel="icon" href="../../assets/icona.svg?v=2" type="image/svg+xml">')
    a('<link rel="apple-touch-icon" href="../../assets/icona-180.png">')
    a('<link rel="stylesheet" href="../../assets/sito.css">')
    a(f'<link rel="stylesheet" href="../../assets/analisi.css?v={CSS_V}">')
    a('<link rel="alternate" type="application/rss+xml" title="Gommberg Terminal Daily" href="../../feed.xml">')
    a('<link rel="preconnect" href="https://fonts.googleapis.com">')
    a('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..100,500..900&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">')
    a(f"<style>{P.CSS}</style>")
    a(f'<script data-goatcounter="{P.GC}" async src="https://gc.zgo.at/count.js"></script>')
    a("</head>\n<body class=\"pa\">")
    a(P.testata("../../"))
    a(f'<div class="strip"><span>Gommberg n. {n}</span><a data-pdf="letta" data-leggi="{pg or 1}" href="{P.esc(pdf_pg)}">Leggi il giornale &rsaquo;</a></div>')
    a('<main class="wrap">')
    a(f'<p class="bc"><a href="../{n}.html">Edizione n. {n}</a> | {P.esc(data.capitalize())} | Analisi e storie</p>')
    a('<div class="pg"><article class="an">')
    a(f'<p class="kicker">{P.esc(tema)}</p><h1>{_t(P, m.get("titolo"))}</h1><p class="an-dek">{_t(P, m.get("perche"))}</p>')
    a(f'<div class="meta2"><span>{f"Pag. {pg} del giornale" if pg else "Dal giornale"}</span>'
      f'<a class="btn lead" data-pdf="letta" data-leggi="{pg or 1}" href="{P.esc(pdf_pg)}">Leggi il giornale</a>'
      f'<a class="btn ghost" href="{wa}" target="_blank" rel="noopener" aria-label="Condividi su WhatsApp">{P.SVG_WA}<span>WhatsApp</span></a>'
      f'<button type="button" class="btn ghost" data-copy="{P.esc(url)}" aria-label="Copia il link">{P.SVG_LINK}<span>Copia link</span></button></div>')
    a(corpo(P, m, pg))
    a(f'<a class="an-pdf" data-pdf="letta" data-leggi="{pg or 1}" href="{P.esc(pdf_pg)}">Leggila impaginata nel giornale{f", pag. {pg}" if pg else ""} <i>&rsaquo;</i></a>')
    a('</article>')
    a(f'<aside class="rail"><div class="card"><a href="{P.esc(pdf)}" data-pdf="letta" data-leggi="1"><img src="../{n}.png" width="1200" height="630" alt="La prima pagina dell\'edizione n. {n}"></a>'
      f'<small>Il giornale di oggi | n. {n} | {ed.get("pagine", 6)} pagine</small><b>Tutta l\'edizione, impaginata come un quotidiano</b>'
      f'<a class="btn lead" data-pdf="letta" data-leggi="1" href="{P.esc(pdf)}">Leggi l\'edizione</a>'
      f'<a class="btn ghost" data-pdf="scaricata" href="{P.esc(pdf)}" download="{P.esc(ed.get("nome", ""))}">Scarica PDF</a></div>'
      + (f'<section class="altre"><h2>Le altre analisi dell\'edizione</h2><ul>{altre_html}</ul></section>' if altre_html else "") +
      '</aside></div>')
    a(f'<div class="fine"><div class="gc"><p><b>La Gommunity</b>Tori o orsi su questa storia? Se ne parla sotto l\'edizione n. {n}.</p>'
      f'<a class="an-pdf" href="../{n}.html#lt">Di\' la tua <i>&rsaquo;</i></a></div>')
    a(f'<aside class="giornale" aria-label="Il giornale"><a href="{P.esc(pdf)}" data-pdf="letta" data-leggi="1"><img src="../{n}.png" width="1200" height="630" alt="" loading="lazy"></a>'
      f'<div><small>Il giornale | n. {n} | {ed.get("pagine", 6)} pagine</small><b>Tutta l\'edizione, impaginata come un quotidiano</b>'
      '<p>Le analisi con grafici e tabelle, i mercati, l\'agenda e la scommessa della settimana.</p>'
      f'<div class="riga"><a class="btn lead" data-pdf="letta" data-leggi="1" href="{P.esc(pdf)}">Leggi l\'edizione</a>'
      f'<a class="btn ghost" data-pdf="scaricata" href="{P.esc(pdf)}" download="{P.esc(ed.get("nome", ""))}">Scarica PDF</a></div></div></aside>')
    a(P.gomm_box(url, titolo, "../../"))
    a("</div></main>")
    a(JS.replace("NNN", n))
    a(P.gomm_js("../../"))
    a(P.piede("../../"))
    a("</body>\n</html>\n")
    return "\n".join(p)


def pagine_edizione(P, repo, ed):
    """Scrive le pagine delle analisi di un'edizione. Torna {indice dell'approfondimento: indirizzo} (vuoto se nessuna)."""
    try:
        d = prepara(repo, ed)
        coppie = collega(ed, d)
        cartella = os.path.join(repo, "e", f"{int(ed['numero']):03d}")
        vive = {f"{m['pagina']}.html" for _, m in coppie}
        vive |= {g["file"] + suff + ".svg" for _, m in coppie for g in m.get("grafici") or [] for suff, _, _ in MISURE}
        if os.path.isdir(cartella):     # una pagina che non nasce più (titolo cambiato, sorgente rotto) non resta in linea,
            for f in os.listdir(cartella):   # e nemmeno i suoi grafici
                if f.endswith((".html", ".svg")) and f not in vive:
                    os.remove(os.path.join(cartella, f))
        if not coppie:
            return {}
        pp = (ed.get("dove") or {}).get("approfondimenti") or [] if isinstance(ed.get("dove"), dict) else []
        fatte = {}
        for i, m in coppie:
            altre = [(x, f"{x['pagina']}.html", pp[j] if j < len(pp) else None) for j, x in coppie if x is not m]
            P.scrivi(os.path.join(repo, indirizzo(ed, m)), pagina(P, ed, m, i, altre))
            fatte[i] = indirizzo(ed, m)
        return fatte
    except Exception as e:  # noqa: BLE001   (l'edizione esce comunque: senza pagine di analisi)
        print(f"AVVISO analisi n. {int(ed['numero']):03d}: {type(e).__name__}: {str(e)[:160]}")
        return {}


if __name__ == "__main__":
    _cli()
