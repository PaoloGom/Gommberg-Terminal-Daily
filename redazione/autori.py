"""Chi ha scritto un fatto, e se una scheda è confermata abbastanza. Una sola definizione, usata dal controllo
(controlli_fatti.py) e dalle misure (misure.py, pannello.py): ciò che il controllo chiede e ciò che il pannello conta
sono la stessa cosa.

La regola dei fatti (G-34, decisa da Paolo il 19/11/2026):
  1. la fonte primaria per prima, e basta da sola: il sito di chi produce o decide il fatto (fonti.json "ufficiali")
     o il documento di chi ne è parte ("primaria": true nella fonte: comunicato, deposito, conti, discorso, verbale);
  2. altrimenti due autori diversi. Autore = chi ha scritto, non chi ospita: un'agenzia conta una volta sola, ovunque
     sia ripresa (tre copie Reuters su tre siti sono un autore);
  3. come ultima scelta un solo autore, dichiarato: di livello 1 o agenzia, con in "conferma_cercata" la ricerca in più
     fatta per trovarne un secondo senza riuscirci; nel PDF il fatto esce con "(Testata)".
Fino al 20/11/2026 bastava una fonte di livello 1, e una copia d'agenzia ospitata ovunque valeva livello 1: la scheda
si chiudeva alla prima copia e la redazione smetteva di cercare (da 0 a 12 schede con un solo autore tra #025 e #028).

A chi si applica (si_applica): a tutte le schede dei fatti, tranne
  - i dati pubblici certi (sezioni catalizzatori, mercati, estremo), che hanno la loro regola in controlli_fatti.py;
  - le cause (tipo "C"): sono già la lettura di un autore, attribuita a lui nel PDF con "(Testata)";
  - le schede riprese dalla memoria e confermate dal revisore (id "MEM.."): vale il giudizio di quando sono uscite.

Chi è l'autore di una fonte, nell'ordine:
  a. un'agenzia, se la fonte la nomina: nel campo "agenzia", o nella testata come nome a sé ("Reuters (KFGO)",
     "Investing.com (Reuters)", "KFGO via Reuters"), o nel percorso dell'indirizzo (/notizie/radiocor/);
  b. la testata che la scheda nomina per prima, se è un nome di "stesso_autore" o il nome di un sito degli elenchi di
     fonti.json ("Fortune (Yahoo Finance)" è Fortune, "Teleborsa" su borsaitaliana.it è Teleborsa);
  c. il sito, se fonti.json "stesso_autore" lo lega a un nome (ft.com è il Financial Times);
  d. altrimenti il sito, senza sottodomini e senza suffisso (bbc.com e bbc.co.uk sono "bbc").
Limiti noti, da leggere nel pannello e non nel codice: "primaria": true e la testata sono dichiarazioni della
redazione (un salto delle fonti primarie o delle dichiarate nel pannello è il segnale); due testate dello stesso
editore non legate in "stesso_autore" contano due."""
import json
import os
import re
import unicodedata
from urllib.parse import urlparse

QUI = os.path.dirname(os.path.abspath(__file__))
F = json.load(open(os.path.join(QUI, "fonti.json"), encoding="utf-8"))
UFF = set(F.get("ufficiali", []))
L1, L2, NO = set(F["livello_1"]) | UFF, set(F["livello_2"]), set(F["vietate"])
AGENZIE = {a.lower() for a in F.get("agenzie", [])}
OSPITANO = [x.lower() for x in F.get("ospitano_notizie", [])]
REGISTRI = ("anomalia", "prime_pagine", "ricerca", "scaletta")
PUBBLICI = ("catalizzatori", "mercati", "estremo")
ALIAS = {"notizie": "top_news", "calendario": "catalizzatori", "termometri": "macro", "lettura": "macro",
         "approfondimento": "deep_dive", "approfondimenti": "deep_dive"}
_DOPPI = {"co", "com", "org", "gov", "ac", "go", "or", "ne", "net", "edu"}


def _s(x):
    return x if isinstance(x, str) else ""


def _chiave(nome):
    """Un nome ridotto all'osso per confrontarlo: "Il Sole 24 Ore" -> ilsole24ore, "Investing.com" -> investing."""
    t = unicodedata.normalize("NFKD", _s(nome).lower()).encode("ascii", "ignore").decode()
    t = re.sub(r"\.(com|it|net|org|de|fr|co\.uk|eu)$", "", t.strip())
    return re.sub(r"[^a-z0-9]", "", t)


def _host(url):
    try:
        return (urlparse(_s(url)).hostname or "").lower()
    except ValueError:
        return ""


def _percorso(url):
    try:
        return urlparse(_s(url)).path.lower()
    except ValueError:
        return ""


def _suffissi(url):
    p = _host(url).split(".")
    return [".".join(p[i:]) for i in range(len(p) - 1)]


def ufficiale(url):
    return any(d in UFF for d in _suffissi(url))


def livello(url):
    """0 vietata, 1, 2; 3 = fuori elenco."""
    for d in _suffissi(url):
        if d in NO:
            return 0
        if d in L1:
            return 1
        if d in L2:
            return 2
    return 3


def sito(url):
    """Il sito senza sottodomini: ca.finance.yahoo.com -> yahoo.com, www.koreatimes.co.kr -> koreatimes.co.kr."""
    p = _host(url).split(".")
    n = 3 if len(p) >= 3 and len(p[-1]) == 2 and p[-2] in _DOPPI else 2
    return ".".join(p[-n:]) if len(p) >= 2 else ""


# "stesso_autore": gruppi di nomi e siti che sono un autore solo; il primo nome del gruppo lo rappresenta
_NOME, _SITO, _SCRITTO = {}, {}, {}
for _g in F.get("stesso_autore", []):
    _SCRITTO[_chiave(_g[0])] = _g[0]
    for _x in _g:
        if "." in _x and " " not in _x and _x.lower() == _x:
            _SITO[_x] = _chiave(_g[0])
        else:
            _NOME[_chiave(_x)] = _chiave(_g[0])
for _a in F.get("agenzie", []):
    _NOME.setdefault(_chiave(_a), _chiave(_a))
    _SCRITTO.setdefault(_NOME[_chiave(_a)], _a)
_AG = {_chiave(a): _NOME[_chiave(a)] for a in F.get("agenzie", [])}            # chiave del nome -> agenzia
_AG_RE = re.compile(r"(?<![a-z0-9])(" + "|".join(sorted((re.escape(a) for a in AGENZIE), key=len, reverse=True)) + r")(?![a-z0-9])")
# i nomi dei siti in elenco (fortune, teleborsa...) e l'autore a cui portano
_NOTI = {sito("https://" + d).split(".")[0]: _SITO.get(d, _SITO.get(sito("https://" + d), sito("https://" + d).split(".")[0]))
         for d in sorted(L1 | L2, key=len, reverse=True)}


def _pezzi(testata):
    """La testata nei suoi nomi: "Reuters (via GV Wire)" -> ["Reuters", "GV Wire"]."""
    return [re.sub(r"^via\s+", "", p.strip(), flags=re.I) for p in re.split(r"[()/,;]|\s+via\s+|\s+-\s+", _s(testata)) if p.strip()]


def agenzia(fonte):
    """L'agenzia che ha scritto la pagina, se la fonte lo dice: campo "agenzia", un nome a sé nella testata, o il
    percorso dell'indirizzo (solo per i nomi lunghi: "ap" in un indirizzo non vuol dire nulla)."""
    a = fonte.get("agenzia")
    m = _AG_RE.search(" ".join(_s(x) for x in a).lower() if isinstance(a, list) else _s(a).lower())
    if m:
        return _AG[_chiave(m.group(1))]
    for p in _pezzi(fonte.get("testata")):
        if _chiave(p) in _AG:
            return _AG[_chiave(p)]
    segmenti = {_chiave(x) for x in _percorso(fonte.get("url")).split("/")}
    for k, v in _AG.items():
        if len(k) >= 5 and k in segmenti:
            return v
    return None


def autore(fonte):
    a = agenzia(fonte)
    if a:
        return a
    primo = _chiave((_pezzi(fonte.get("testata")) or [""])[0])
    if primo in _NOME:
        return _NOME[primo]
    if primo in _NOTI:
        return _NOTI[primo]
    for d in _suffissi(fonte.get("url")):
        if d in _SITO:
            return _SITO[d]
    s = sito(fonte.get("url")).split(".")[0]
    return _NOME.get(s, s)


def nome(a):
    """Un autore come si scrive: "reuters" -> "Reuters"; un sito resta com'è."""
    return _SCRITTO.get(a, a)


def ospitata(url):
    """Una pagina di notizie altrui sul sito di un ente ufficiale (le notizie su borsaitaliana.it): non è l'ente che parla."""
    u = re.sub(r"^www\.", "", _host(url)) + _percorso(url)
    return any(x in u for x in OSPITANO)


def primaria(fonte):
    """Il documento di chi è parte del fatto ("primaria": true), o il sito di chi produce il dato. Un lancio d'agenzia
    resta dell'agenzia, anche con "primaria": true e anche sul sito di una borsa."""
    if agenzia(fonte):
        return False
    return fonte.get("primaria") is True or (ufficiale(fonte.get("url")) and not ospitata(fonte.get("url")))


def affidabile(fonte):
    """Livello 1, oppure un lancio d'agenzia su un sito non vietato."""
    lv = livello(fonte.get("url"))
    return lv == 1 or (lv > 1 and agenzia(fonte) is not None)


def sezione(scheda):
    s = _s(scheda.get("sezione"))
    return ALIAS.get(s, s)


def si_applica(scheda):
    """La regola dei due autori vale per questa scheda? (vedi in testa: non per dati pubblici, cause e memoria confermata)"""
    return not (sezione(scheda) in PUBBLICI or scheda.get("tipo") == "C"
                or (_s(scheda.get("id")).startswith("MEM") and scheda.get("verifica") == "confermato"))


def _ricerche(x):
    return {" ".join(re.findall(r"[a-z0-9à-ü]+", s.lower())) for s in (x if isinstance(x, list) else [x]) if isinstance(s, str)} - {""}


def giudizio(scheda):
    """Come una scheda è confermata: {"stato", "autori", "primaria", "affidabile", "dichiarata"}.
    stato: "primaria" | "due_autori" | "singola" (un solo autore, senza primaria) | "senza_fonti".
    dichiarata (conta per "singola"): la scheda porta in "conferma_cercata" una ricerca vera (almeno tre parole) e
    dietro la scheda ci sono almeno due ricerche diverse; oppure è un dato ufficiale di cui si è cercato due volte
    il comunicato ("ufficiale_cercato")."""
    fonti = [s for s in (scheda.get("fonti") if isinstance(scheda.get("fonti"), list) else [])
             if isinstance(s, dict) and livello(s.get("url")) != 0 and _host(s.get("url"))]
    autori = sorted({autore(s) for s in fonti})
    prim = any(primaria(s) for s in fonti)
    cercata = {r for r in _ricerche(scheda.get("conferma_cercata")) if len(r.split()) >= 3}
    dichiarata = bool(cercata) and len(cercata | {r for s in fonti for r in _ricerche(s.get("ricerca"))}) >= 2
    if (scheda.get("tipo") == "U" or sezione(scheda) == "catalizzatori") and len(_ricerche(scheda.get("ufficiale_cercato"))) >= 2:
        dichiarata = True
    stato = "senza_fonti" if not fonti else "primaria" if prim else "due_autori" if len(autori) >= 2 else "singola"
    return {"stato": stato, "autori": autori, "primaria": prim, "dichiarata": dichiarata,
            "affidabile": any(affidabile(s) for s in fonti)}


def schede(fatti):
    """Le schede dei fatti di un registro fatti.json: senza registri di lavoro e senza le scartate."""
    return [f for f in fatti if isinstance(f, dict) and f.get("id") and f.get("fonti") and not f.get("scartata")
            and _s(f.get("sezione")) not in REGISTRI] if isinstance(fatti, list) else []


def conta(fatti):
    """Le due misure del pannello che vengono dalle schede (G-02, misura di G-34):
    fonte_singola = i fatti a cui la regola si applica e che poggiano su un solo autore, dichiarati compresi: è ciò che
                    il controllo ferma con CERCA o lascia passare come ultima scelta (traguardo: zero o quasi);
    autori = autori diversi per analisi, in media: per ogni tesi della scaletta, chi ha scritto le schede su cui poggia."""
    s = schede(fatti)
    out = {"fonte_singola": 0}
    for f in s:
        try:
            out["fonte_singola"] += bool(si_applica(f) and giudizio(f)["stato"] == "singola")
        except Exception:        # una scheda scritta male non toglie la misura alle altre
            pass
    try:
        per_id = {_s(f.get("id")): f for f in s}
        tesi = [m.get("schede") for r in fatti if isinstance(r, dict) and r.get("sezione") == "scaletta"
                for m in (r.get("moduli") if isinstance(r.get("moduli"), list) else []) if isinstance(m, dict)]
        n = [len({autore(x) for i in t if isinstance(i, str) and i in per_id for x in per_id[i].get("fonti") or []
                  if isinstance(x, dict)}) for t in tesi if isinstance(t, list)]
        n = [x for x in n if x]
        if n:
            out["autori"] = round(sum(n) / len(n), 1)
    except Exception:
        pass
    return out


if __name__ == "__main__":      # python3 autori.py <fatti.json>...: lo stato di ogni scheda, per le prove sull'archivio
    import sys
    for p in sys.argv[1:]:
        fatti = json.load(open(p, encoding="utf-8"))
        s = schede(fatti)
        dentro = [f for f in s if si_applica(f)]
        fuori = [(f, giudizio(f)) for f in dentro if giudizio(f)["stato"] == "singola"]
        print(f"{os.path.basename(p)}: {len(s)} schede, {len(dentro)} sotto la regola, con un solo autore {len(fuori)} "
              f"(di cui dichiarate {sum(1 for _, g in fuori if g['dichiarata'])}); pannello {conta(fatti)}")
        for f, g in fuori:
            print(f"   {f.get('id')} {sezione(f)}: {nome(g['autori'][0])}")
