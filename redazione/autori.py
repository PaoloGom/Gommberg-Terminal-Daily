"""Chi ha scritto un fatto, e se una scheda è confermata abbastanza. Una sola definizione, usata dal controllo
(controlli_fatti.py) e dalle misure (misure.py, pannello.py): ciò che il controllo chiede e ciò che il pannello conta
sono la stessa cosa.

La regola dei fatti (G-34, decisa da Paolo il 19/11/2026):
  1. la fonte primaria per prima, e basta da sola: il sito di chi produce o decide il fatto (fonti.json "ufficiali")
     o il documento di chi ne è parte ("primaria": true nella fonte: comunicato, deposito, conti, discorso, verbale);
  2. altrimenti due autori diversi. Autore = chi ha scritto, non chi ospita: un'agenzia conta una volta sola, ovunque
     sia ripresa (tre copie Reuters su tre siti sono un autore);
  3. come ultima scelta un solo autore, dichiarato: di livello 1 o agenzia, con in "conferma_cercata" la ricerca in più
     fatta per trovarne un secondo senza riuscirci; nel PDF la testata sta nella riga Fonti.
Fino al 20/11/2026 bastava una fonte di livello 1, e una copia d'agenzia ospitata ovunque valeva livello 1: la scheda
si chiudeva alla prima copia e la redazione smetteva di cercare (da 0 a 12 schede con un solo autore tra #025 e #028).

A chi si applica (si_applica): a tutte le schede dei fatti, tranne
  - i dati pubblici certi (sezioni catalizzatori, mercati, estremo), che hanno la loro regola in controlli_fatti.py;
  - le cause (tipo "C"): sono già la lettura di un autore, attribuita a lui nel PDF dentro la frase;
  - le schede riprese dalla memoria e confermate dal revisore (id "MEM.."): vale il giudizio di quando sono uscite.

Chi è l'autore di una fonte, nell'ordine:
  a. un'agenzia, se la fonte la nomina: nel campo "agenzia", o nella testata come nome a sé ("Reuters (KFGO)",
     "Investing.com (Reuters)", "KFGO via Reuters", "Yahoo (Bloomberg News)"), o nel percorso dell'indirizzo
     (/notizie/radiocor/);
  b. la testata ospitata: il nome che la scheda mette per primo, se la testata nomina anche il sito che ospita
     ("Fortune (Yahoo Finance)" è Fortune) o se quel nome sta nell'indirizzo (Teleborsa su borsaitaliana.it/.../teleborsa/);
  c. altrimenti il sito: l'autore a cui fonti.json "stesso_autore" lo lega (ft.com è il Financial Times), il suo nome
     se è un sito in elenco (bbc.com e bbc.co.uk sono "bbc"), il dominio intero se è fuori elenco.
La stessa pagina citata due volte conta una volta.
Limiti noti, da leggere nel pannello e non nel codice: "primaria": true e la testata sono dichiarazioni della
redazione (un salto delle fonti primarie o delle dichiarate nel pannello è il segnale); due testate dello stesso
editore non legate in "stesso_autore" contano due; due siti fuori elenco bastano come due autori, come prima."""
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
_AGENZIE = set(_AG.values())
# parole che accompagnano il nome di un'agenzia senza cambiarlo: "Reuters News", "Thomson Reuters", "da Reuters"
_RIEMPITIVI = {"thomson", "news", "agency", "agenzia", "the", "da", "fonte", "via", "cita", "newswires", "newswire", "su", "di"}


def _pezzi(testata):
    """La testata nei suoi nomi: "Reuters (via GV Wire)" -> ["Reuters", "GV Wire"]."""
    return [p.strip() for p in re.split(r"[()\[\]/,;:|–—]|\s+via\s+|\s+-\s+", _s(testata)) if p.strip()]


def _senza_riempitivi(pezzo):
    return _chiave(" ".join(w for w in pezzo.split() if _chiave(w) not in _RIEMPITIVI))


def pagina(url):
    """Lo stesso indirizzo scritto in modi diversi è la stessa pagina: senza schema, www, frammento e barra finale."""
    return re.sub(r"^https?://(www\.)?", "", _s(url).split("#")[0].strip().lower()).rstrip("/")


def _del_sito(url):
    """L'autore a cui porta il sito."""
    for d in _suffissi(url):
        if d in _SITO:
            return _SITO[d]
    for d in _suffissi(url):
        if d in L1 or d in L2:
            return _NOTI.get(sito("https://" + d).split(".")[0], sito(url))
    return sito(url)


def agenzia(fonte):
    """L'agenzia che ha scritto la pagina, se la fonte lo dice: campo "agenzia", un nome a sé nella testata, o il
    percorso dell'indirizzo (solo per i nomi lunghi: "ap" in un indirizzo non vuol dire nulla)."""
    a = fonte.get("agenzia")
    m = _AG_RE.search(" ".join(_s(x) for x in a).lower() if isinstance(a, list) else _s(a).lower())
    if m:
        return _AG[_chiave(m.group(1))]
    for p in _pezzi(fonte.get("testata")):
        if _senza_riempitivi(p) in _AG:
            return _AG[_senza_riempitivi(p)]
    segmenti = {_chiave(x) for x in _percorso(fonte.get("url")).split("/")}
    for k, v in _AG.items():
        if len(k) >= 5 and k in segmenti:
            return v
    return None


def autore(fonte):
    a = agenzia(fonte)
    if a:
        return a
    url = fonte.get("url")
    ospite, etichetta = _del_sito(url), _chiave(sito(url).split(".")[0])

    def chi(p):
        return _NOME.get(_chiave(p)) or _NOTI.get(_chiave(p)) or _chiave(p)

    def e_il_sito(p):
        k = _chiave(p)
        return chi(p) == ospite or k == etichetta or (len(etichetta) >= 4 and len(k) >= 4 and (k in etichetta or etichetta in k))
    pezzi = _pezzi(fonte.get("testata"))
    if pezzi and _chiave(pezzi[0]) and not e_il_sito(pezzi[0]):
        indirizzo = re.sub(r"[^a-z0-9]", "", _host(url) + _percorso(url))
        if any(e_il_sito(p) for p in pezzi[1:]) or (len(_chiave(pezzi[0])) >= 5 and _chiave(pezzi[0]) in indirizzo):
            return chi(pezzi[0])
    return ospite


def nome(a):
    """Un autore come si scrive: "reuters" -> "Reuters"; un sito resta com'è."""
    return _SCRITTO.get(a, a)


def ospitata(url):
    """Una pagina di notizie altrui sul sito di un ente ufficiale (le notizie su borsaitaliana.it): non è l'ente che parla."""
    u = re.sub(r"^www\.", "", _host(url)) + re.sub(r"/+", "/", _percorso(url))
    return any(x in u for x in OSPITANO)


def primaria(fonte):
    """Il documento di chi è parte del fatto ("primaria": true), o il sito di chi produce il dato. Un lancio d'agenzia
    resta dell'agenzia, anche con "primaria": true e anche sul sito di una borsa."""
    if autore(fonte) in _AGENZIE:
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


_CIFRA = re.compile(r"(?<![\w.,])[+-]?\d+(?:[.,]\d+)*\s?(?:%|pb\b|punti\b|mld\b|mln\b|miliard\w+|milion\w+)")
# un numero uscito e, accanto, quello che ci si aspettava: "+0,4% (atteso +0,8%)", "115,8 mld contro 109,15 attesi". La stima
# di una casa ("stima" con il nome di una banca) è una previsione, non un'attesa del mercato.
_ATTESE = re.compile(r"\d[^.;(]{0,25}\((?:\w+ ){0,2}(?:attes[oaie]|consenso|stime|stima(?!\s+[A-Z])|previst[oaie])\b|"
                     r"\d[^.;]{0,30}?\b(?:contro|rispetto a|sopra|sotto|oltre|meno de|più de)\w*\b[^.;]{0,25}\b(?:attes[oaie]|stime|consenso)\b", re.I)
# senza unità (un indice: "51,7 (atteso 51,9)") vale solo il confronto con il numero atteso scritto accanto
_ATTESE_NUMERO = re.compile(r"\d[^.;(]{0,25}\((?:\w+ ){0,2}(?:attes[oaie]|consenso|stime|stima(?!\s+[A-Z]))\b[^)\d]{0,12}[+-]?\d|"
                            r"\d[^.;]{0,30}?\b(?:contro|rispetto a)\s+(?:i |il |le |l')?[+-]?\d[\d.,]*[^.;\d]{0,12}\b(?:attes[oaie]|stime|consenso)\b")
_VUOTE = {"del", "dei", "per", "con", "non", "una", "gli", "che", "nel", "sul", "dal", "tra", "usa", "della", "delle", "dello",
          "degli", "alla", "alle", "nella", "dati", "dato", "mese", "anno", "annuo", "sul", "sui"}
PRIMA_PAGINA = ("top_story", "top_news")
# le sezioni che non sono un fatto pubblicato come notizia: calendario, agenda, registri e scommessa
NON_NOTIZIE = ("agenda", "catalizzatori", "prime_pagine", "scaletta", "anomalia", "ricerca", "scommessa")


def _cifre(scheda):
    t = scheda.get("testo") if isinstance(scheda, dict) else scheda
    return {re.sub(r"\s", "", c).lstrip("+") for c in _CIFRA.findall(_s(t))}


def _parole(t):
    return {w for w in re.findall(r"[a-zà-ü]{3,}", _s(t).lower()) if w not in _VUOTE}


def ufficiale_di_fatto(scheda, tutte=(), oggi=None, usciti=()):
    """Un dato ufficiale riconosciuto da ciò che la scheda dice, anche quando non lo dichiara con "tipo": "U". Vale per la
    ogni scheda di un fatto già avvenuto (prima pagina, approfondimenti, mercati: ISTRUZIONI §2, "ovunque compaia"), non per
    calendario, agenda e registri (NON_NOTIZIE), né per le cause né per la memoria confermata: (a) la scheda riporta
    le stesse cifre, nello stesso giorno, di una riga del calendario o di una scheda dichiarata U (è lo stesso dato scritto
    due volte); (b) è un numero uscito messo a confronto con le attese: lo pubblica un ente o una società, quindi il suo
    comunicato esiste; una cifra senza unità (un indice) vale solo con il numero atteso scritto accanto; (c) regge una riga del calendario uscito dell'edizione (usciti = [(evento, dato)], da C["ieri"]):
    stessa cifra e stesso evento, solo in prima pagina (PRIMA_PAGINA). Torna il motivo, o "" se non è un dato ufficiale. Non usa elenchi di argomenti."""
    if sezione(scheda) in NON_NOTIZIE or scheda.get("tipo") in ("C", "U") or not si_applica(scheda):
        return ""
    giorno = _s(scheda.get("data_evento"))[:10]
    if oggi and giorno > str(oggi)[:10]:
        return ""          # un evento che deve ancora uscire ha solo le attese
    mie = _cifre(scheda)
    for altra in tutte:
        if altra is scheda or not isinstance(altra, dict) or altra.get("scartata"):
            continue
        calendario = altra.get("tipo") == "U" or sezione(altra) == "catalizzatori"
        if calendario and _s(altra.get("data_evento"))[:10] == giorno and len(mie & _cifre(altra)) >= 2:
            return f"stesse cifre di {altra.get('id', '?')}"
    if (_ATTESE if mie else _ATTESE_NUMERO).search(_s(scheda.get("testo"))):
        return "numero uscito contro le attese"
    if sezione(scheda) not in PRIMA_PAGINA:
        return ""          # (c) solo in prima pagina: fuori, una riga di "ieri" può essere un fatto di mercato (un debutto in borsa)
    mie_parole = _parole(scheda.get("testo"))
    for evento, dato in usciti:
        if mie & _cifre(_s(dato)) and len(mie_parole & _parole(evento)) >= 2:
            return f"riga del calendario: {_s(evento)[:30]}"
    return ""


def _ricerche(x):
    return {" ".join(re.findall(r"[a-z0-9à-ü]+", s.lower())) for s in (x if isinstance(x, list) else [x]) if isinstance(s, str)} - {""}


def giudizio(scheda):
    """Come una scheda è confermata: {"stato", "autori", "primaria", "affidabile", "dichiarata"}.
    stato: "primaria" | "due_autori" | "singola" (un solo autore, senza primaria) | "senza_fonti" (nessuna fonte con un
    indirizzo valido e non vietato).
    dichiarata (conta per "singola"): la scheda porta in "conferma_cercata" una ricerca vera (almeno tre parole) e
    dietro la scheda ci sono almeno due ricerche diverse; oppure è un dato ufficiale di cui si è cercato due volte
    il comunicato ("ufficiale_cercato"). "cercate" = le ricerche dichiarate: controlli_fatti.py le confronta con
    quelle fatte davvero nella sessione, quando il gancio le ha registrate."""
    fonti, viste = [], set()
    for s in scheda.get("fonti") if isinstance(scheda.get("fonti"), list) else []:
        if isinstance(s, dict) and livello(s.get("url")) != 0 and _host(s.get("url")) and pagina(s.get("url")) not in viste:
            viste.add(pagina(s.get("url")))
            fonti.append(s)
    autori = sorted({autore(s) for s in fonti})
    prim = any(primaria(s) for s in fonti)
    cercate = {r for r in _ricerche(scheda.get("conferma_cercata")) if len(r.split()) >= 3}
    if not (cercate and len(cercate | {r for s in fonti for r in _ricerche(s.get("ricerca"))}) >= 2):
        cercate = set()
    if not cercate and (scheda.get("tipo") == "U" or sezione(scheda) == "catalizzatori"):
        u = {r for r in _ricerche(scheda.get("ufficiale_cercato")) if len(r.split()) >= 3}
        cercate = u if len(u) >= 2 else set()
    stato = "senza_fonti" if not fonti else "primaria" if prim else "due_autori" if len(autori) >= 2 else "singola"
    return {"stato": stato, "autori": autori, "primaria": prim, "dichiarata": bool(cercate), "cercate": sorted(cercate),
            "affidabile": any(affidabile(s) for s in fonti)}


def stessa_ricerca(a, b):
    """Due ricerche sono la stessa se una contiene le parole dell'altra, o ne hanno in comune almeno sei su dieci."""
    x, y = set(_ricerche(a).pop().split() if _ricerche(a) else []), set(_ricerche(b).pop().split() if _ricerche(b) else [])
    return bool(x and y) and (x <= y or y <= x or len(x & y) / len(x | y) >= 0.6)


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
