"""Campi di redazione per i controlli (temi strutturati, quadro, Stamattina, moduli), presi dal dizionario C.
Uso (nella composizione del modello): voce.update(extra_voce.campi(C, voce)). Non sovrascrive campi già scritti dal motore.
edizioni_voce.py li ignora: servono solo a controlli_temi.py e controlli_contenuti.py (voce_indice.json)."""
import re


def _txt(s):
    return re.sub(r"<[^>]+>", "", str(s or "")).replace("&amp;", "&")


def _grafico(g):
    if not isinstance(g, dict):
        return None
    dati = g.get("dati")
    if dati is not None:
        try:
            dati = [[_txt(a), float(b)] for a, b in dati]
        except (TypeError, ValueError):
            dati = None
    x = g.get("x") or []
    serie = [_txt(z[0]) for z in g.get("serie", []) if isinstance(z, (list, tuple)) and z]
    return {"titolo": _txt(g.get("titolo")), "tipo": g.get("tipo"), "soggetto": g.get("soggetto"), "dati": dati,
            # v7.8: firma per riconoscere lo stesso grafico nelle edizioni successive (controlli_contenuti.py)
            "serie": serie, "x0": str(x[0]) if x else None, "x1": str(x[-1]) if x else None,
            "etichette": [a for a, _ in dati] if dati else []}


def agenda(righe):
    """Righe di "In arrivo" per il sito: testo semplice, la riga in grassetto è l'evento chiave.
    Struttura v9: la quinta colonna ("come può muovere i mercati") diventa "muove", una frase per riga."""
    out = []
    for r in righe or []:
        r = list(r) + ["", "", "", ""]
        c = [re.sub(r"\s+", " ", _txt(x)).strip() for x in r[:4]]
        if not c[0] or not c[1]:
            continue
        riga = {"quando": c[0], "evento": c[1], "attese": "" if c[2] in ("-", "") else c[2],
                "perche": c[3], "chiave": "<b>" in str(r[1]) or "<b>" in str(r[0])}
        muove = [re.sub(r"\s+", " ", _txt(x)).strip() for x in re.split(r"<br\s*/?>", str(r[4] or ""))]
        if any(muove):
            riga["muove"] = [x for x in muove if x]
        out.append(riga)
    return out


def campi(C, voce=None):
    voce = voce or {}
    top = C.get("top") or {}
    out = {
        "tema_top": top.get("tema"),
        "temi_in30": list(C.get("in30_temi") or []),
        "temi_notizie": [n.get("tema") or n.get("tag") for n in C.get("notizie", []) if isinstance(n, dict)],
        "quadro": _txt(C.get("quadro")) or None,
        "stamattina": [_txt(s) for s in C.get("stamattina", [])],
        "stamattina_titolo": C.get("stamattina_titolo", "Stamattina"),
        "notizie_testo": [f"{_txt(n.get('titolo'))}. {_txt(n.get('testo'))}" for n in C.get("notizie", []) if isinstance(n, dict)],
        "brevi": [_txt(m.get("breve") or m.get("titolo")) for m in C.get("moduli", [])],
        "agenda": agenda(C.get("agenda", [])),
        # v8.3: le storie in corso (termometri di pag. 2) si archiviano, così domani si aggiornano invece di riscriverle
        "termometri": {"righe": [[_txt(c) for c in r] for r in C.get("termometri", [])], "fermi": _txt(C.get("fermi", ""))}
                      if C.get("termometri") else None,
        "evento_oggi": next((f"{_txt(r[0])} {_txt(r[1])}" for r in C.get("agenda", []) if "<b>" in str(r[1])), None),
        "moduli_redazione": [{
            "chiave": m.get("chiave"), "misura": m.get("misura"), "titolo": _txt(m.get("titolo")),
            "perche": _txt(m.get("perche")), "quindi": _txt(m.get("quindi")),
            "punti": [_txt(p) for p in m.get("punti", [])], "testo": [_txt(p) for p in m.get("testo", [])], "righe": [[_txt(c) for c in r] for r in m.get("righe", [])],
            "grafici": [x for x in (_grafico(m.get("grafico")), _grafico(m.get("grafico2"))) if x]}
            for m in C.get("moduli", [])],
    }
    return {k: v for k, v in out.items() if k not in voce}
