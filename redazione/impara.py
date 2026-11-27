#!/usr/bin/env python3
"""Impara cresce con le edizioni (G-54): le parole che il giornale spiega arrivano al manuale da sole, zero token.

Ogni edizione scrive sei parole con la loro spiegazione (campo "parole" del file dell'edizione). Qui si raccolgono:
  - dalle edizioni con i sorgenti archiviati: redazione/sorgenti/AAAA-MM-GG/edizione.py, letto senza eseguirlo (ast);
  - dalle edizioni più vecchie, senza sorgenti: "archivio" di redazione/parole_giornale.json (tratte una volta dai PDF);
sempre e solo per le edizioni pubblicate in edizioni.json. Il risultato è dati/parole.json, che leggono glossario.html,
numeri.html e sito/statico.py. Lo scrive pagine.py a ogni pubblicazione.

Che cosa fa da solo il codice, e che cosa no (scelta del 27/11, dopo il collaudo indipendente: 10 definizioni su 12
scelte dal codice andavano corrette, e nessuna regola sulle parole in comune distingue due significati diversi):
  1. DA SOLO: ogni parola del giornale si riconduce a una voce. Se è una scheda di Impara scritta a mano (per nome,
     sigla, nome esteso, varianti o descrizione breve, al singolare o al plurale, o per l'elenco "stesse"), la parola
     porta lì: ricerca, "Nell'ultima edizione", "dove l'abbiamo usata". La scheda scritta a mano vince sempre.
     Le altre parole formano gruppi: due nomi stanno insieme se uno dei due è il nome dell'altro o la sua parentesi
     ("Freno automatico (sidecar)" e "Sidecar"), o se l'elenco "stesse" lo dice.
  2. DA SOLO: ogni spiegazione passa la FORMA (frase intera da 40 a 300 caratteri, maiuscola in testa e punto in fondo,
     niente HTML, lineette lunghe, domande o esclamazioni) e NON È DEL GIORNO (niente oggi, ieri, giorni, mesi, anni,
     rimandi alle pagine); "fuori" toglie a mano una parola (per qualunque suo nome) o una sola spiegazione.
  3. DA SOLO: una parola spiegata in due edizioni con due spiegazioni valide è PRONTA: il codice prepara la proposta
     (python3 redazione/impara.py --proposte: tutte le spiegazioni, i possibili doppioni, il testo da copiare).
  4. A MANO, una volta per parola: una scheda nuova entra in pagina solo quando la sua definizione è CONFERMATA in
     "confermate" di parole_giornale.json (titolo -> breve e spiega). È il canale con cui si correggono le definizioni:
     dati/parole.json è generato e non si ritocca. Se nessuno conferma, Impara non sbaglia: tutto il resto continua.
     Un nome di "confermate" che non trova la sua parola, o una spiegazione di "fuori" ("Parola|data") che nessuna
     edizione ha, è un errore di battitura: come al punto 5, si ferma tutto senza scrivere. "stesse" no: un sinonimo
     preparato prima che il giornale lo usi è legittimo.
  5. Un file d'ingresso che manca o non si legge (edizioni.json, parole_giornale.json, glossario.json,
     glossario_sito.json, un sorgente archiviato rotto) FERMA il passaggio senza scrivere nulla: dati/parole.json resta
     com'era, pagine.py stampa l'avviso e l'edizione esce.

Uso: python3 redazione/impara.py [repo]             scrive dati/parole.json (come pagine.py)
     python3 redazione/impara.py [repo] --elenco    ogni spiegazione con il verdetto (entra / non entra e perché)
     python3 redazione/impara.py [repo] --proposte  le parole pronte che aspettano la conferma, con i possibili doppioni
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
MIN_EDIZIONI = 2                 # una parola che torna è del mestiere: si propone solo dopo due edizioni

VUOTE = {"di", "del", "dello", "della", "dei", "degli", "delle", "il", "lo", "la", "i", "gli", "le", "l", "un", "uno",
         "una", "per", "da", "dal", "dalla", "in", "nel", "nella", "a", "al", "alla", "e", "ed", "con", "su", "sul", "d"}
GIORNO = re.compile(r"\b(oggi|odiern\w*|ieri|domani|stamattina|stamani|stasera|stanotte|stavolta|attualmente|"
                    r"luned[iì]|marted[iì]|mercoled[iì]|gioved[iì]|venerd[iì]|sabato|domenica|"
                    r"gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre|"
                    r"settimana scorsa|questa settimana|quest'anno|l'anno scorso|(?:19|20)\d\d|"
                    r"pag\.|pagina|in questo numero|come detto|vedi|qui sotto|qui sopra|sopra citat\w*)\b", re.I)


class Fermo(Exception):
    """Un file d'ingresso manca o non si legge: il passaggio si ferma senza scrivere nulla."""


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


# ---------------------------------------------------------------- lettura degli ingressi
def leggi(repo, rel, tipo):
    """Un file JSON d'ingresso: se manca, non si legge o non ha la forma attesa, Fermo."""
    p = os.path.join(repo, rel)
    try:
        x = json.load(open(p, encoding="utf-8"))
    except FileNotFoundError:
        raise Fermo(f"{rel} manca") from None
    except (OSError, ValueError) as e:
        raise Fermo(f"{rel} non si legge ({str(e)[:60]})") from None
    if not isinstance(x, tipo):
        raise Fermo(f"{rel}: forma inattesa")
    return x


def dal_sorgente(repo, rel):
    """Il campo "parole" del file dell'edizione, letto senza eseguirlo: [(parola, spiegazione)]; None se il file non
    c'è o non ha il campo (edizione senza sorgente: valgono le parole dell'archivio). Un file rotto è Fermo."""
    path = os.path.join(repo, rel)
    if not os.path.exists(path):
        return None
    try:
        albero = ast.parse(open(path, encoding="utf-8").read())
    except (OSError, SyntaxError, ValueError):
        raise Fermo(f"{rel} non si legge") from None
    for n in ast.walk(albero):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and k.value == "parole":
                    try:
                        x = ast.literal_eval(v)
                    except ValueError:
                        raise Fermo(f"{rel}: il campo parole non è un elenco scritto") from None
                    return coppie_valide(x, rel)
    return None


def coppie_valide(x, dove):
    if not isinstance(x, (list, tuple)) or not all(isinstance(p, (list, tuple)) and len(p) >= 2 and
                                                   isinstance(p[0], str) and isinstance(p[1], str) for p in x):
        raise Fermo(f"{dove}: parole non nella forma [parola, spiegazione]")
    return [(p[0], p[1]) for p in x]


def cura_di(repo):
    """parole_giornale.json controllato: stesse, fuori, archivio, confermate. Ogni forma sbagliata è Fermo."""
    c = leggi(repo, CURA, dict)
    ok = lambda k, t: isinstance(c.get(k, t()), t)
    if not (ok("stesse", dict) and ok("fuori", dict) and ok("archivio", dict) and ok("confermate", dict)):
        raise Fermo(f"{CURA}: stesse, fuori, archivio e confermate devono essere oggetti")
    for k, v in (c.get("stesse") or {}).items():
        if not (isinstance(v, list) and all(isinstance(x, str) and x.strip() for x in v)):
            raise Fermo(f"{CURA}: stesse \"{k}\" deve essere un elenco di nomi")
    if not all(isinstance(v, str) for v in (c.get("fuori") or {}).values()):
        raise Fermo(f"{CURA}: ogni voce di fuori dice il perché in una frase")
    for d, v in (c.get("archivio") or {}).items():
        coppie_valide(v, f"{CURA}, archivio {d}")
    for k, v in (c.get("confermate") or {}).items():
        if not (isinstance(v, dict) and isinstance(v.get("breve"), str) and v["breve"].strip() and isinstance(v.get("spiega"), str)):
            raise Fermo(f"{CURA}: confermate \"{k}\" vuole breve e spiega")
        if difetto(v["spiega"]):
            raise Fermo(f"{CURA}: confermate \"{k}\": {difetto(v['spiega'])}")
    return c


def raccogli(repo, cura):
    """Le spiegazioni delle edizioni pubblicate: [{parola, spiegazione, numero, data, da}]."""
    eds = sorted((e for e in leggi(repo, "edizioni.json", list) if isinstance(e, dict) and e.get("numero") and e.get("data")),
                 key=lambda e: e["numero"])
    arch = cura.get("archivio") or {}
    out = []
    for e in eds:
        coppie, da = dal_sorgente(repo, f"redazione/sorgenti/{e['data']}/edizione.py"), "sorgenti"
        if coppie is None and e["data"] in arch:
            coppie, da = arch[e["data"]], "PDF"
        for p, d in coppie or []:
            out.append({"parola": pulisci(p), "spiegazione": pulisci(d), "numero": e["numero"], "data": e["data"], "da": da})
    return out


# ---------------------------------------------------------------- le voci di Impara già scritte
def scritte(repo):
    """Le schede di Impara scritte a mano: ({chiave di ogni nome: sigla}, {sigla: (nomi, testo)}). Stessa unione di
    glossario.html. I due file si leggono per forza: senza, le parole porterebbero a schede nuove doppie."""
    G = leggi(repo, "redazione/glossario.json", dict)
    S = leggi(repo, "redazione/glossario_sito.json", dict)
    SV = S.get("voci") or {}
    if not isinstance(G.get("voci"), list) or not isinstance(SV, dict):
        raise Fermo("redazione/glossario.json o glossario_sito.json: manca l'elenco delle voci")
    base = [v for v in G["voci"] if isinstance(v, dict) and v.get("sigla") and v.get("breve")]
    note = {v["sigla"] for v in base}
    tutte = base + [{"sigla": k, "breve": v["breve"]} for k, v in SV.items() if k not in note and isinstance(v, dict) and v.get("breve")]
    idx, testi = {}, {}
    for v in tutte:
        s = SV.get(v["sigla"]) or {}
        propri = [n for n in [v["sigla"], s.get("titolo"), s.get("esteso")] + list(v.get("varianti") or []) if n]
        for n in propri + [v["breve"]]:
            for x in nomi(n):
                idx.setdefault(chiave(x), v["sigla"])
        testi[v["sigla"]] = (propri, " ".join([v["breve"], s.get("spiega") or ""]))
    return idx, testi


# ---------------------------------------------------------------- il calcolo
def calcola(repo):
    """Torna (voci nuove, alias, verdetti, gruppi). verdetti: una riga per spiegazione (per l'elenco e per chi
    controlla); gruppi: {titolo: info} di ogni parola nuova, per le proposte."""
    cura = cura_di(repo)
    occ = raccogli(repo, cura)
    idx, testi = scritte(repo)
    conf = cura.get("confermate") or {}
    stesse = {}
    for canone, varianti in list((cura.get("stesse") or {}).items()) + [(c, []) for c in conf]:
        for n in [canone] + list(varianti):
            stesse.setdefault(chiave(n), canone)
    fuori = {fold(k): v for k, v in (cura.get("fuori") or {}).items()}

    def tolta(o):
        """Il perché, se "fuori" toglie la spiegazione: per data con qualunque nome, o la parola per qualunque nome."""
        ns = nomi(o["parola"]) + ([o["canone"]] if o.get("canone") else [])
        return next((fuori[k] for k in [fold(x) + "|" + o["data"] for x in ns] + [fold(x) for x in ns] if k in fuori), "")

    # 1. ogni spiegazione a una voce: scheda scritta, oppure un gruppo di parole nuove (unione per nome e parentesi)
    padre = {}
    def radice(k):
        while padre.setdefault(k, k) != k:
            k = padre[k]
        return k
    alias, nuove = {}, []
    for o in occ:
        ns = nomi(o["parola"])
        canone = next((stesse[chiave(x)] for x in ns if chiave(x) in stesse), None)
        o["canone"] = canone
        sigla = idx.get(chiave(canone)) if canone else next((idx[chiave(x)] for x in ns if chiave(x) in idx), None)
        if sigla:
            o["verdetto"] = f"porta alla scheda scritta \"{sigla}\""
            for x in ns:
                alias[x] = sigla
            continue
        chiavi = [chiave(canone)] if canone else [chiave(x) for x in ns]
        for k in chiavi[1:]:
            padre[radice(k)] = radice(chiavi[0])
        o["chiavi"] = chiavi
        nuove.append(o)
    gruppi_k = {}
    for o in nuove:
        gruppi_k.setdefault(radice(o["chiavi"][0]), []).append(o)

    # 2. ogni gruppo: spiegazioni valide, nome, stato (confermata, pronta, in attesa)
    voci, gruppi = [], {}
    conf_k = {chiave(c): c for c in conf}
    for g in gruppi_k.values():
        canone = next((o["canone"] for o in g if o["canone"]), None)
        conta = {}
        for o in g:
            conta.setdefault(fold(titolo_di(o["parola"])), []).append(o)
        titolo = canone or titolo_di(max(conta.values(), key=lambda xs: (len(xs), max(o["numero"] for o in xs)))[-1]["parola"])
        for o in g:
            o["difetto"] = difetto(o["spiegazione"])
            f = tolta(o)
            if f and not o["difetto"]:
                o["difetto"] = "tolta a mano: " + f
        tolta_tutta = any(fold(x) in fuori for o in g for x in nomi(o["parola"]) + [titolo])
        valide = [o for o in g if not o["difetto"]]
        edizioni, ed_valide = {o["numero"] for o in g}, {o["numero"] for o in valide}
        confermata = conf.get(conf_k.get(chiave(titolo))) if not tolta_tutta else None
        if confermata:
            stato = "confermata"
        elif tolta_tutta:
            stato = "tolta"
        elif len(ed_valide) >= MIN_EDIZIONI:
            stato = "pronta"
        else:
            stato = "attesa"
        for o in g:
            if stato == "confermata":
                o["verdetto"] = f"ENTRA in \"{titolo}\", con la definizione confermata a mano"
            elif o["difetto"]:
                o["verdetto"] = "non entra: " + o["difetto"]
            elif stato == "pronta":
                o["verdetto"] = f"pronta: \"{titolo}\" aspetta la conferma a mano della definizione (--proposte)"
            elif len(edizioni) < MIN_EDIZIONI:
                o["verdetto"] = "non entra (per ora): spiegata in una sola edizione"
            else:
                o["verdetto"] = "non entra (per ora): è l'unica spiegazione valida, ne serve una di un'altra edizione"
        varianti = sorted({x for o in g for x in nomi(o["parola"]) if fold(x) != fold(titolo)}, key=fold)
        gruppi[titolo] = {"stato": stato, "spiegazioni": g, "valide": valide, "varianti": varianti}
        if stato != "confermata":
            continue
        voci.append({"sigla": titolo, "breve": confermata["breve"].strip(), "spiega": confermata["spiega"].strip(),
                     "varianti": varianti, "da": max(o["numero"] for o in g)})
        for o in g:
            for x in nomi(o["parola"]):
                alias[x] = titolo
    # un nome scritto a mano che non trova nulla è un errore di chi scrive il file (una lettera sbagliata in
    # "confermate" farebbe sparire la scheda): Fermo, così la pagina resta com'era e il collaudo lo vede prima
    orfane = [c for c in conf if (gruppi.get(c) or {}).get("stato") != "confermata"]
    if orfane:
        raise Fermo(f"confermate senza la loro parola: {', '.join(orfane)} (nome sbagliato, scheda scritta a mano o fuori)")
    viste = {fold(x) + "|" + o["data"] for o in occ for x in nomi(o["parola"]) + ([o["canone"]] if o.get("canone") else [])}
    sbagliate = [k for k in cura.get("fuori") or {} if "|" in k and fold(k) not in viste]
    if sbagliate:
        raise Fermo(f"fuori senza la sua spiegazione: {', '.join(sbagliate)} (nome o data sbagliati)")
    voci.sort(key=lambda v: fold(v["sigla"]))
    for t, info in gruppi.items():
        info["doppioni"] = doppioni(t, info, gruppi, testi)
    return voci, dict(sorted(alias.items(), key=lambda kv: fold(kv[0]))), occ, gruppi


def doppioni(titolo, info, gruppi, testi):
    """I possibili doppioni di una parola nuova: schede scritte a mano o altre parole nuove con una parola piena del nome
    in comune ("Riserva obbligatoria" e "Riserva minima delle banche"), o il cui testo usa il nome della parola (la
    scheda VIX dice "indice della paura"). Le parole in comune nelle spiegazioni no: in finanza tornano sempre le stesse
    (tassi, banca centrale) e il segnale affogherebbe. È un segnale per chi conferma, non una decisione: il rimedio vero
    è l'elenco "stesse" (o "fuori")."""
    miei = {titolo} | set(info["varianti"])
    parole_nome = {w for n in miei for w in chiave(n).split() if len(w) >= 4}
    out = []
    altri = [(s, ns, t, "scheda scritta") for s, (ns, t) in testi.items()] + \
            [(t, [t] + i["varianti"], " ".join(o["spiegazione"] for o in i["valide"] or i["spiegazioni"]), "parola nuova")
             for t, i in gruppi.items() if t != titolo]
    for nome, ns, t, tipo in altri:
        perche = []
        if parole_nome & {w for n in ns for w in chiave(n).split() if len(w) >= 4}:
            perche.append("nome in comune")
        if any(re.search(r"\b" + re.escape(fold(n)) + r"\b", fold(t)) for n in miei if len(n) >= 5):
            perche.append("il suo testo usa questo nome")
        if perche:
            out.append(f"{nome} ({tipo}: {', '.join(perche)})")
    return out


def scrivi(repo):
    """Scrive dati/parole.json; torna il numero di voci nuove. Se un ingresso manca o non si legge alza Fermo prima di
    scrivere: chi chiama (pagine.py) lo intercetta, stampa l'avviso e il file resta com'era."""
    voci, alias, _, _ = calcola(repo)
    testo = json.dumps({"tipo": TIPO, "voci": voci, "alias": alias}, ensure_ascii=False, separators=(",", ":")) + "\n"
    p = os.path.join(repo, FILE)
    if not (os.path.exists(p) and open(p, encoding="utf-8").read() == testo):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        tmp = p + ".tmp"
        open(tmp, "w", encoding="utf-8").write(testo)
        os.replace(tmp, p)
    return len(voci)


def proposte(gruppi):
    """Le parole pronte, con tutto ciò che serve per confermarle: il testo da copiare in "confermate" è una bozza
    (la spiegazione valida più recente) da rileggere, non una definizione già buona."""
    righe = []
    for t, i in sorted(gruppi.items(), key=lambda kv: fold(kv[0])):
        if i["stato"] != "pronta":
            continue
        righe.append(f"== {t}" + (f"  (anche: {', '.join(i['varianti'])})" if i["varianti"] else ""))
        for o in i["spiegazioni"]:
            righe.append(f"   n. {o['numero']:03d} {o['data']}  {o['spiegazione']}" + (f"  [{o['difetto']}]" if o["difetto"] else ""))
        righe.append("   possibili doppioni: " + ("; ".join(i["doppioni"]) if i["doppioni"] else "nessuno trovato"))
        bozza = max(i["valide"], key=lambda o: o["numero"])["spiegazione"]
        righe.append("   bozza: " + json.dumps({t: {"breve": "", "spiega": bozza}}, ensure_ascii=False)[1:-1])
    return righe


if __name__ == "__main__":
    arg = [a for a in sys.argv[1:] if not a.startswith("--")]
    repo = os.path.abspath(arg[0] if arg else os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    try:
        if "--elenco" in sys.argv or "--proposte" in sys.argv:
            voci, alias, occ, gruppi = calcola(repo)
            if "--elenco" in sys.argv:
                for o in occ:
                    print(f"{o['data']}  n. {o['numero']:03d}  {o['parola']}  |  {o['spiegazione']}  |  {o['verdetto']}  [{o['da']}]")
            else:
                print("\n".join(proposte(gruppi)) or "Nessuna parola pronta da confermare.")
            stati = [i["stato"] for i in gruppi.values()]
            print(f"\n{len(occ)} spiegazioni in {len({o['numero'] for o in occ})} edizioni, {len({fold(o['parola']) for o in occ})} "
                  f"parole diverse; {len(voci)} schede nuove confermate, {stati.count('pronta')} pronte da confermare, "
                  f"{stati.count('attesa')} in attesa, {stati.count('tolta')} tolte; "
                  f"{len(set(alias.values()) - {v['sigla'] for v in voci})} schede scritte a mano collegate")
        else:
            print(f"Impara: {scrivi(repo)} parole dalle edizioni in {FILE}")
    except Fermo as e:
        print(f"AVVISO: Impara non aggiornata ({e}): {FILE} resta com'era", file=sys.stderr)
        sys.exit(1)
