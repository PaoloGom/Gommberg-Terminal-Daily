"""G-46 / riga G-06: quali schede riconoscerebbe come dato ufficiale autori.ufficiale_di_fatto, oggi e con due varianti.
Sola lettura. Uso: python3 g06_ufficiali.py [AAAA-MM-GG ...]  (default: tutte le schede in redazione/fatti/ dal 16/11)
A = regola di oggi; B = come A ma la cifra a confronto con le attese vale anche senza unità (PMI, fiducia: "51,7 (atteso 51,9)");
C = come B ma su tutte le sezioni di fatti (non solo top_story/top_news), memoria e cause escluse come oggi."""
import glob, json, os, re, sys
R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, R)
import autori as A

NUM = re.compile(r"\d")


def variante(s, tutte, oggi, b=False, c=False):
    if not c:
        r = A.ufficiale_di_fatto(s, tutte, oggi, [])
        if r or not b:
            return r
        if A.sezione(s) not in A.PRIMA_PAGINA or s.get("tipo") in ("C", "U") or not A.si_applica(s):
            return ""
    else:
        if A.sezione(s) in ("agenda", "catalizzatori", "prime_pagine", "scaletta", "anomalia", "ricerca") \
                or s.get("tipo") in ("C", "U") or not A.si_applica(s):
            return ""
        vecchia = A.PRIMA_PAGINA
        A.PRIMA_PAGINA = (A.sezione(s),)
        try:
            r = A.ufficiale_di_fatto(s, tutte, oggi, [])
        finally:
            A.PRIMA_PAGINA = vecchia
        if r:
            return r
    if str(s.get("data_evento"))[:10] > oggi:
        return ""
    t = str(s.get("testo") or "")
    return "B: numero contro le attese (senza unità)" if NUM.search(t) and A._ATTESE.search(t) else ""


giorni = sys.argv[1:] or sorted(os.path.basename(f)[:10] for f in glob.glob(os.path.join(R, "fatti", "2026-11-*.json"))
                                if os.path.basename(f)[:10] >= "2026-11-16")
tot = {"A": 0, "B": 0, "C": 0}
for g in giorni:
    F = json.load(open(os.path.join(R, "fatti", g + ".json"), encoding="utf-8"))
    F = [s for s in F if isinstance(s, dict)]
    for s in F:
        ra, rb, rc = variante(s, F, g), variante(s, F, g, b=True), variante(s, F, g, b=True, c=True)
        for k, r in (("A", ra), ("B", rb), ("C", rc)):
            tot[k] += bool(r)
        if ra or rb or rc:
            print(f"{g} {s.get('id')} [{A.sezione(s)}] A={'x' if ra else '-'} B={'x' if rb else '-'} C={'x' if rc else '-'} | "
                  f"{(rc or rb or ra)[:40]} | {str(s.get('testo'))[:110]}")
print("Totale schede riconosciute:", tot, "su", len(giorni), "giorni")
