"""Desk: la riscrittura per il lettore, dopo la revisione dei fatti (v8.3, 13/11/2026; G-45, 24/11/2026).

Chi verifica i fatti non è chi sistema la prosa. Il desk riscrive titoli, attacchi e testi per renderli più chiari, ma
non può aggiungere fatti: il codice accetta una riscrittura solo se non porta cifre, nomi o fonti nuove e se resta
non più lunga del 10% (e non più corta del 40%). Né può spostarne o toglierne: una cifra resta sul suo soggetto, e una
frase che porta un fatto che nessun altro campo dice non sparisce. Una proposta respinta lascia il testo com'era: il desk
non blocca mai.

Uso (cartella di lavoro):
  python3 desk.py estrai <edizione.py>     -> desk_incarico.json  [{"campo", "testo"}]  (lo riceve l'agente desk)
  (l'agente scrive desk_proposta.json      -> [{"campo", "testo"}], solo i campi che migliora)
  python3 desk.py verifica <edizione.py>   -> desk_ok.json (accettate) e l'elenco delle respinte col motivo
Il modello applica desk_ok.json da solo al rendering, e solo ai campi rimasti come il desk li ha letti.
"""
import importlib.util
import json
import os
import re
import sys

INC, PRO, OK = "desk_incarico.json", "desk_proposta.json", "desk_ok.json"


def campi(C):
    """I testi che il desk può riscrivere, con un indirizzo stabile."""
    out = {}
    t = C.get("top") or {}
    for k in ("titolo", "dek"):
        if t.get(k):
            out[f"top.{k}"] = t[k]
    if C.get("quadro"):
        out["quadro"] = C["quadro"]
    for i, x in enumerate(C.get("in30") or []):
        out[f"in30.{i}"] = x
    for i, n in enumerate(C.get("notizie") or []):
        for k in ("titolo", "testo"):
            if isinstance(n, dict) and n.get(k):
                out[f"notizie.{i}.{k}"] = n[k]
    for i, a in enumerate(C.get("agenda") or []):
        if len(a) > 3 and "<b>" not in str(a[3]):
            out[f"agenda.{i}.perche"] = a[3]
    for m in C.get("moduli") or []:
        c = m.get("chiave")
        for k in ("titolo", "perche", "quindi", "numero", "guardare"):
            if m.get(k):
                out[f"moduli.{c}.{k}"] = m[k]
        for k in ("testo", "punti"):
            for j, x in enumerate(m.get(k) or []):
                out[f"moduli.{c}.{k}.{j}"] = x
    return out


def imposta(C, campo, testo):
    p = campo.split(".")
    if p[0] == "top":
        C["top"][p[1]] = testo
    elif p[0] == "quadro":
        C["quadro"] = testo
    elif p[0] == "in30":
        C["in30"][int(p[1])] = testo
    elif p[0] == "notizie":
        C["notizie"][int(p[1])][p[2]] = testo
    elif p[0] == "agenda":
        a = list(C["agenda"][int(p[1])]); a[3] = testo; C["agenda"][int(p[1])] = tuple(a)
    elif p[0] == "moduli":
        m = next(x for x in C["moduli"] if x.get("chiave") == p[1])
        if len(p) == 4:
            m[p[2]][int(p[3])] = testo
        else:
            m[p[2]] = testo


def applica(C, cartella="."):
    """Chiamata dal modello prima del rendering."""
    p = os.path.join(cartella, OK)
    if not os.path.exists(p):
        return 0
    attuali, n = campi(C), 0
    for e in json.load(open(p, encoding="utf-8")):
        if attuali.get(e["campo"]) == e["originale"]:
            imposta(C, e["campo"], e["testo"]); n += 1
    print(f"Desk: {n} riscritture applicate")
    return n


NUM = re.compile(r"\d+(?:[.,]\d+)*")
RIMANDO = re.compile(r"\[\[\w+\]\]")
# Una cifra con la sua unità (o col segno): è di qualcuno, e la riscrittura non può dargliene un altro (G-45: nella prova
# del 23/11 "il listino tecnologico di Hong Kong (-3,8%)" era diventato "Hong Kong perde il 3,8%", con l'Hang Seng a -1,9%).
CIFRA = re.compile(r"([+\-−]?)(\d+(?:[.,]\d+)*)\s?(%|pb\b|punti|\$|dollari|euro|miliardi|milioni)")
VERBI = re.compile(r"^(?:sale|salgono|scende|scendono|cede|cedono|perde|perdono|guadagna|guadagnano|chiude|chiudono|cala|"
                   r"calano|crolla|risale|rimbalza|lascia|segna|tocca|vola|arretra|fanno|fa|scendere|salire|ha|hanno|è|sono)$")
LEGAMI = set("il lo la i gli le l un una uno di del della dello dei degli delle dell a al alla allo ai agli alle all da dal "
             "dalla dai in nel nella nei su sul sulla sui con per tra fra e anche circa quasi oltre più meno".split())
# Dove comincia il gruppo del soggetto: l'articolo o una preposizione articolata che non è un genitivo ("il listino
# tecnologico di Hong Kong", "nel rimbalzo dell'oro"). Prima di lì c'è altro (trovato nel collaudo indipendente del
# 24/11: nella #032 "Ci leggiamo anche il rimbalzo dell'oro (+3,9%)" riscritto in "Nel rimbalzo dell'oro (+3,9%)
# leggiamo" era respinto, perché "ci" e "leggiamo" passavano per soggetto della cifra).
INIZI = set("il lo la i gli le l un una uno nel nella nello nei negli nelle nell sul sulla sullo sui sugli sulle sull "
            "al alla allo ai agli alle all dal dalla dallo dai dagli dalle dall".split())


def _parole(t):
    return re.findall(r"[a-zà-ù&]+|[(),;:.]|\d+(?:[.,]\d+)*", re.sub(r"<[^>]+>", " ", t).lower().replace("'", " "))


def soggetto(t, inizio):
    """Le parole piene di chi fa la cifra che comincia in t[inizio:]: si risale fino all'inizio del suo gruppo (articolo o
    preposizione articolata non genitiva), al verbo o alla punteggiatura; un verbo subito prima della cifra ("Hong Kong
    perde il 3,8%") si salta e il soggetto è prima."""
    pp, out = _parole(t[:inizio]), []
    for w in reversed(pp):
        if w in "(":
            continue
        if w in ",;:.)" or len(out) >= 6:
            if out or w != ")":
                break
            continue
        if VERBI.match(w):
            if out:
                break
            continue
        if w in INIZI and out:
            break
        if w in LEGAMI or w[0].isdigit():
            continue
        out.append(w[:5])
    return set(out)


def cambia_soggetto(orig, nuovo):
    """La prima cifra che nella riscrittura ha perso parole del suo soggetto, o None."""
    for m in CIFRA.finditer(nuovo):
        prima = [soggetto(orig, x.start()) for x in CIFRA.finditer(orig) if x.group(2) == m.group(2)]
        if not prima:
            continue
        ora, pieni = soggetto(nuovo, m.start()), [p for p in prima if p]
        if pieni and all(p - ora for p in pieni):
            persi = sorted(min((p - ora for p in pieni), key=len))
            return f"la cifra {m.group(0).strip()} perde parte del suo soggetto ({', '.join(persi)}...): una cifra resta su chi l'ha fatta"
    return None


def frase_tolta(orig, nuovo, altri):
    """Una frase dell'originale che porta un fatto che non sta né nella riscrittura né in un altro campo (il desk toglie
    echi, non fatti: nella prova del 23/11 era sparito su che cosa indagava la SEC). Torna l'inizio della frase o None."""
    radici = lambda t: {w[:6] for w in re.findall(r"[a-zà-ù]{5,}", re.sub(r"<[^>]+>", " ", t).lower())}
    resta = radici(nuovo) | radici(altri)
    for f in re.split(r"(?<=[.;])\s+", orig):
        r = radici(f)
        if len(r) >= 6 and len(r - resta) >= 0.6 * len(r):
            return f[:60]
    return None


def _nomi(t):
    t = re.sub(r"<[^>]+>", " ", t)
    return set(re.findall(r"(?<=[a-zà-ù0-9,;:)»] )[A-Z][\w&'.-]*", t)) | set(re.findall(r"\(([^)]{2,40})\)", t))


def controlla(orig, nuovo, tutto, campo="", altri=""):
    """Motivo del rifiuto, o None se la riscrittura è accettata. altri = il testo degli altri campi dell'edizione."""
    if isinstance(nuovo, str) and not nuovo.strip() and campo.endswith(".numero"):
        return None   # un "numero" che ripete il resto si toglie
    if not isinstance(nuovo, str) or not nuovo.strip():
        return "vuota"
    extra = set(NUM.findall(nuovo)) - set(NUM.findall(orig))
    if extra:
        return f"cifre nuove {sorted(extra)[:3]}"
    nomi = {x for x in _nomi(nuovo) - _nomi(orig) if x not in tutto}
    if nomi:
        return f"nomi o fonti nuove {sorted(nomi)[:3]}"
    if sorted(RIMANDO.findall(nuovo)) != sorted(RIMANDO.findall(orig)):
        return "rimandi [[...]] cambiati"
    lo, ln = len(orig.split()), len(nuovo.split())
    if lo >= 8 and not (0.6 * lo <= ln <= 1.1 * lo):
        return f"lunghezza {ln} parole contro {lo} (ammesso -40% / +10%)"
    if "—" in nuovo or "–" in nuovo:
        return "trattino lungo"
    motivo = cambia_soggetto(orig, nuovo)
    if motivo:
        return motivo
    tolta = frase_tolta(orig, nuovo, altri)
    if tolta:
        return f"toglie un fatto che nessun altro campo dice (\"{tolta}...\"): il desk toglie echi, non fatti"
    return None


def _carica(ed):
    # L'edizione legge i suoi argomenti da sys.argv: glieli si presta e poi si rimettono quelli di chi chiama. Senza,
    # controlli_testo.py (che passa di qui per il ritmo) perdeva il suo --json e non scriveva più testo.json, il file
    # delle sigle che edizioni_voce.py si aspetta (trovato il 21/11/2026 costruendo la rete del collaudo).
    argv = sys.argv
    sys.argv = [ed, os.getcwd()]
    try:
        spec = importlib.util.spec_from_file_location("edizione_desk", ed)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.argv = argv
    return mod.C


if __name__ == "__main__":
    azione, ed = sys.argv[1], os.path.abspath(sys.argv[2])
    cart = os.getcwd()
    C = _carica(ed)
    os.chdir(cart)
    attuali = campi(C)
    if azione == "estrai":
        json.dump([{"campo": k, "testo": v} for k, v in attuali.items()], open(INC, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"Desk: {len(attuali)} testi in {INC}; proposta attesa in {PRO}")
    elif azione == "verifica":
        tutto = set().union(*[_nomi(v) for v in attuali.values()])
        ok, no = [], []
        for e in json.load(open(PRO, encoding="utf-8")) if os.path.exists(PRO) else []:
            orig = attuali.get(e.get("campo"))
            if orig is None:
                no.append((e.get("campo"), "campo inesistente")); continue
            if e.get("testo") == orig:
                continue
            altri = " ".join(v for k, v in attuali.items() if k != e["campo"])
            motivo = controlla(orig, e.get("testo"), tutto, e["campo"], altri)
            (no.append((e["campo"], motivo)) if motivo else ok.append({"campo": e["campo"], "originale": orig,
                                                                         "testo": e["testo"]}))
        json.dump(ok, open(OK, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"Desk: {len(ok)} riscritture accettate, {len(no)} respinte (restano com'erano)")
        for c, m in no:
            print(f"RESPINTA {c}: {m}")
