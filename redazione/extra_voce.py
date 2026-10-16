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
    return {"titolo": _txt(g.get("titolo")), "tipo": g.get("tipo"), "soggetto": g.get("soggetto"), "dati": dati}


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
        "evento_oggi": next((f"{_txt(r[0])} {_txt(r[1])}" for r in C.get("agenda", []) if "<b>" in str(r[1])), None),
        "moduli_redazione": [{
            "chiave": m.get("chiave"), "misura": m.get("misura"), "titolo": _txt(m.get("titolo")),
            "perche": _txt(m.get("perche")), "quindi": _txt(m.get("quindi")),
            "punti": [_txt(p) for p in m.get("punti", [])], "righe": [[_txt(c) for c in r] for r in m.get("righe", [])],
            "grafici": [x for x in (_grafico(m.get("grafico")), _grafico(m.get("grafico2"))) if x]}
            for m in C.get("moduli", [])],
    }
    return {k: v for k, v in out.items() if k not in voce}
