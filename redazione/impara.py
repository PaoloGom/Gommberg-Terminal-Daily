#!/usr/bin/env python3
"""Impara cresce con le edizioni (G-54): le parole che il giornale spiega entrano nel manuale da sole, zero token.

Ogni edizione scrive sei parole con la loro spiegazione (campo "parole" del file dell'edizione). Qui si raccolgono:
  - dalle edizioni con i sorgenti archiviati: redazione/sorgenti/AAAA-MM-GG/edizione.py, letto senza eseguirlo (ast);
  - dalle edizioni più vecchie, senza sorgenti: "archivio" di redazione/parole_giornale.json (tratte una volta dai PDF);
sempre e solo per le edizioni pubblicate in edizioni.json. Il risultato è dati/parole.json, che leggono glossario.html,
numeri.html e sito/statico.py. Lo scrive pagine.py a ogni pubblicazione; se qualcosa va storto il file resta com'era.

Il filtro, uguale per il passato e per le edizioni future, senza nessuno che rilegga:
  1. la parola si riconduce a una voce: a una scheda di Impara già scritta a mano (per nome, sigla, nome esteso,
     varianti o descrizione breve, anche al singolare o al plurale, oppure per l'elenco "stesse" di parole_giornale.json)
     oppure a un gruppo di parole del giornale con lo stesso nome; il nome tra parentesi è una variante;
  2. una scheda scritta a mano vince sempre: la parola del giornale porta lì (ricerca, "Nell'ultima edizione", "dove
     l'abbiamo usata") e non aggiunge testo;
  3. una spiegazione vale se supera la FORMA (frase intera da 40 a 300 caratteri, maiuscola in testa e punto in fondo,
     niente HTML, lineette lunghe, domande o esclamazioni) e se NON È DEL GIORNO (niente oggi, ieri, giorni della
     settimana, mesi, anni, "questa settimana", rimandi alle pagine o ad altro del numero);
  4. una parola nuova entra solo se il giornale l'ha spiegata in almeno DUE edizioni con due spiegazioni valide e
     COMPATIBILI (almeno due parole piene in comune): una parola che torna è del mestiere, una parola di un giorno solo
     (un nome, un fatto) aspetta che torni. Vale la spiegazione valida e compatibile più recente: le regole di scrittura
     si stringono nel tempo, e l'ultima è quella scritta con le regole di oggi;
  5. "fuori" di parole_giornale.json toglie a mano una parola o una sola spiegazione ("Parola|AAAA-MM-GG").

Uso: python3 redazione/impara.py [repo]            scrive dati/parole.json (come pagine.py)
     python3 redazione/impara.py [repo] --elenco   stampa ogni spiegazione con il verdetto (entra / non entra e perché)
"""
import ast
import html
import json
import os
import re
import sys
import unicodedata

FILE = "dati/parole.json"
CURA = "redazione/parole_giornale.json"
TIPO = "Dalle edizioni"          # la categoria delle schede nate dal giornale (chip di Impara e briciole delle pagine)
MIN_EDIZIONI = 2
MIN_COMUNI = 2

VUOTE = {"di", "del", "dello", "della", "dei", "degli", "delle", "il", "lo", "la", "i", "gli", "le", "l", "un", "uno",
         "una", "per", "da", "dal", "dalla", "in", "nel", "nella", "a", "al", "alla", "e", "ed", "con", "su", "sul", "d"}
PIENE_NO = {"della", "delle", "dello", "degli", "sulle", "sugli", "sulla", "nelle", "negli", "dalla", "dalle", "quando",
            "quanto", "quella", "quello", "quelli", "questo", "questa", "sono", "viene", "vuol", "dire", "anche", "come",
            "dopo", "prima", "senza", "oltre", "altri", "altre", "molto", "spesso", "solito", "tutti", "tutte", "ciò"}
GIORNO = re.compile(r"\b(oggi|odiern\w*|ieri|domani|stamattina|stamani|stasera|stanotte|stavolta|attualmente|"
                    r"luned[iì]|marted[iì]|mercoled[iì]|gioved[iì]|venerd[iì]|sabato|domenica|"
                    r"gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre|"
                    r"settimana scorsa|questa settimana|quest'anno|l'anno scorso|(?:19|20)\d\d|"
                    r"pag\.|pagina|in questo numero|come detto|vedi|qui sotto|qui sopra|sopra citat\w*)\b", re.I)


def fold(s):
    s = unicodedata.normalize("NFD", str(s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def chiave(s):
    """Il nome ridotto all'osso: minuscole senza accenti, senza parole vuote, ogni parola senza l'ultima vocale
    (vendita e vendite, acquisto e acquisti si incontrano)."""
    w = [x for x in re.split(r"[^a-z0-9&]+", fold(s).replace("’", "'")) if x and x not in VUOTE]
    return " ".join(re.sub(r"[aeiou]$", "", x) if len(x) > 3 else x for x in w)


def nomi(nome):
    """Il nome com'è, senza la parentesi, e ciò che sta nella parentesi: "Differenziale (spread)" vale anche spread."""
    m = re.match(r"^(.*?)\s*\(([^)]*)\)\s*$", nome)
    return [nome.strip()] + ([m.group(1).strip(), m.group(2).strip()] if m else [])


def titolo_di(nome):
    return nomi(nome)[1] if len(nomi(nome)) > 1 else nome.strip()


def pulisci(t):
    return re.sub(r"\s+", " ", html.unescape(str(t or ""))).strip()


def radici(t):
    return {w[:6] for w in re.findall(r"[a-zà-ù]{5,}", t.lower()) if w not in PIENE_NO}


def difetto(d):
    """Perché una spiegazione non vale (testo vuoto se vale)."""
    if not 40 <= len(d) <= 300:
        return f"forma: {len(d)} caratteri (servono da 40 a 300)"
    if not d[0].isupper() or not d.endswith("."):
        return "forma: non è una frase intera (maiuscola in testa, punto in fondo)"
    if re.search(r"[<>–—?!]|&amp;", d):
        return "forma: HTML, lineette lunghe, domande o esclamazioni"
    g = GIORNO.search(d)
    if g:
        return f"del giorno: \"{g.group(0)}\""
    return ""


# ---------------------------------------------------------------- raccolta
def dal_sorgente(path):
    """Il campo "parole" del file dell'edizione, letto senza eseguirlo: [(parola, spiegazione)] o None."""
    try:
        albero = ast.parse(open(path, encoding="utf-8").read())
    except (OSError, SyntaxError, ValueError):
        return None
    for n in ast.walk(albero):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and k.value == "parole":
                    try:
                        x = ast.literal_eval(v)
                    except ValueError:
                        return None
                    return [(str(p[0]), str(p[1])) for p in x if isinstance(p, (list, tuple)) and len(p) >= 2]
    return None


def leggi(repo, rel, vuoto):
    try:
        return json.load(open(os.path.join(repo, rel), encoding="utf-8"))
    except (OSError, ValueError):
        return vuoto


def raccogli(repo, cura):
    """Le spiegazioni delle edizioni pubblicate: [{parola, spiegazione, numero, data, da}]."""
    eds = sorted((e for e in leggi(repo, "edizioni.json", []) if isinstance(e, dict) and e.get("numero") and e.get("data")),
                 key=lambda e: e["numero"])
    arch = cura.get("archivio") or {}
    out = []
    for e in eds:
        coppie, da = dal_sorgente(os.path.join(repo, "redazione", "sorgenti", e["data"], "edizione.py")), "sorgenti"
        if coppie is None and e["data"] in arch:
            coppie, da = arch[e["data"]], "PDF"
        for p, d in coppie or []:
            out.append({"parola": pulisci(p), "spiegazione": pulisci(d), "numero": e["numero"], "data": e["data"], "da": da})
    return out


# ---------------------------------------------------------------- le voci di Impara già scritte
def scritte(repo):
    """Le schede di Impara scritte a mano: {chiave di ogni nome: sigla}. Stessa unione di glossario.html."""
    G = leggi(repo, "redazione/glossario.json", {})
    S = leggi(repo, "redazione/glossario_sito.json", {})
    SV = S.get("voci") or {}
    base = [v for v in G.get("voci") or [] if v.get("sigla") and v.get("breve")]
    note = {v["sigla"] for v in base}
    tutte = base + [{"sigla": k, "breve": v["breve"]} for k, v in SV.items() if k not in note and v.get("breve")]
    idx = {}
    for v in tutte:
        s = SV.get(v["sigla"]) or {}
        for n in [v["sigla"], s.get("titolo"), s.get("esteso"), v["breve"]] + list(v.get("varianti") or []):
            for x in nomi(n) if n else []:
                idx.setdefault(chiave(x), v["sigla"])
    return idx


def calcola(repo):
    """Torna (voci nuove, alias, verdetti). verdetti: una riga per spiegazione, per l'elenco e per chi controlla.
    parole_giornale.json illeggibile è un errore, non un file vuoto: senza archivio sparirebbero le parole di ottobre."""
    p = os.path.join(repo, CURA)
    cura = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    occ = raccogli(repo, cura)
    idx = scritte(repo)
    stesse = {}
    for canone, varianti in (cura.get("stesse") or {}).items():
        for n in [canone] + list(varianti):
            stesse[chiave(n)] = canone
    fuori = {fold(k): v for k, v in (cura.get("fuori") or {}).items()}

    def voce_di(nome):
        """("scritta", sigla) se porta a una scheda scritta a mano, altrimenti ("nuova", chiave del gruppo)."""
        for x in nomi(nome):
            c = stesse.get(chiave(x))
            if c:
                return ("scritta", idx[chiave(c)]) if chiave(c) in idx else ("nuova", chiave(c))
        for x in nomi(nome):
            if chiave(x) in idx:
                return "scritta", idx[chiave(x)]
        return "nuova", chiave(titolo_di(nome))

    gruppi, alias = {}, {}
    for o in occ:
        tipo, k = voce_di(o["parola"])
        o["voce"] = (tipo, k)
        if tipo == "scritta":
            o["verdetto"] = f"porta alla scheda scritta \"{k}\""
            for x in nomi(o["parola"]):
                alias[x] = k
            continue
        gruppi.setdefault(k, []).append(o)

    voci = []
    for k, g in gruppi.items():
        canone = next((c for c in (cura.get("stesse") or {}) if chiave(c) == k), None)
        for o in g:
            o["difetto"] = difetto(o["spiegazione"])
            f = fuori.get(fold(o["parola"]) + "|" + o["data"]) or fuori.get(fold(titolo_di(o["parola"])))
            if f and not o["difetto"]:
                o["difetto"] = "tolta a mano: " + f
        valide = [o for o in g if not o["difetto"]]
        comp = set()
        for i, a in enumerate(valide):
            for b in valide[i + 1:]:
                if a["numero"] != b["numero"] and len(radici(a["spiegazione"]) & radici(b["spiegazione"])) >= MIN_COMUNI:
                    comp.update((id(a), id(b)))
        edizioni = {o["numero"] for o in g}
        scelta = max((o for o in valide if id(o) in comp), key=lambda o: o["numero"], default=None)
        for o in g:
            if o["difetto"]:
                o["verdetto"] = "non entra: " + o["difetto"]
            elif len(edizioni) < MIN_EDIZIONI:
                o["verdetto"] = "non entra (per ora): spiegata in una sola edizione"
            elif id(o) not in comp:
                o["verdetto"] = "non entra: non compatibile con le altre spiegazioni della stessa parola"
            elif o is scelta:
                o["verdetto"] = "ENTRA: è la spiegazione che si mostra"
            else:
                o["verdetto"] = "entra la parola, con la spiegazione più recente"
        if not scelta:
            continue
        # il nome della voce: quello dell'elenco "stesse", altrimenti il più usato dalle edizioni (a pari merito il più recente)
        conta = {}
        for o in g:
            conta.setdefault(fold(titolo_di(o["parola"])), []).append(o)
        titolo = canone or titolo_di(max(conta.values(), key=lambda xs: (len(xs), max(o["numero"] for o in xs)))[-1]["parola"])
        d = scelta["spiegazione"]
        m = re.match(r"^(.{12,90}?)[:;](\s|$)", d)
        breve = (m.group(1) if m else d.rstrip(".")).strip()
        breve = breve[:1].lower() + breve[1:] if not re.match(r"^[A-Z]{2}", breve) else breve
        varianti = sorted({x for o in g for x in nomi(o["parola"]) if fold(x) != fold(titolo)}, key=fold)
        voci.append({"sigla": titolo, "breve": breve, "spiega": d, "varianti": varianti, "da": scelta["numero"]})
        for o in g:
            for x in nomi(o["parola"]):
                alias[x] = titolo
    voci.sort(key=lambda v: fold(v["sigla"]))
    return voci, dict(sorted(alias.items(), key=lambda kv: fold(kv[0]))), occ


def scrivi(repo):
    """Scrive dati/parole.json; torna il numero di voci nuove. Un errore qui non deve mai fermare la pubblicazione:
    chi chiama lo intercetta e il file resta com'era."""
    voci, alias, _ = calcola(repo)
    testo = json.dumps({"tipo": TIPO, "voci": voci, "alias": alias}, ensure_ascii=False, separators=(",", ":")) + "\n"
    p = os.path.join(repo, FILE)
    if not (os.path.exists(p) and open(p, encoding="utf-8").read() == testo):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        tmp = p + ".tmp"
        open(tmp, "w", encoding="utf-8").write(testo)
        os.replace(tmp, p)
    return len(voci)


if __name__ == "__main__":
    arg = [a for a in sys.argv[1:] if not a.startswith("--")]
    repo = os.path.abspath(arg[0] if arg else os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    if "--elenco" in sys.argv:
        voci, alias, occ = calcola(repo)
        for o in occ:
            print(f"{o['data']}  n. {o['numero']:03d}  {o['parola']}  |  {o['spiegazione']}  |  {o['verdetto']}  [{o['da']}]")
        print(f"\n{len(occ)} spiegazioni, {len({fold(o['parola']) for o in occ})} parole diverse; "
              f"{len(voci)} schede nuove; {len(set(alias.values()))} voci di Impara collegate")
    else:
        print(f"Impara: {scrivi(repo)} parole dalle edizioni in {FILE}")
