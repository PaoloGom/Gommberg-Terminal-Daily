"""Rende un edizione.py come testo che il lettore legge, senza numero di edizione né indizi su come è stata scritta."""
import sys, html, re
sys.path.insert(0, '/home/claude/pagella')
from estrai import carica

def pulisci(s):
    s = html.unescape(str(s))
    s = re.sub(r'\[\[([^\]]+)\]\]', '(→ pag.)', s)
    s = re.sub(r'<[^>]+>', '', s)
    return s.strip()

def riga(x):
    if isinstance(x, (list, tuple)):
        return ' | '.join(pulisci(i) for i in x if not (isinstance(i, str) and i.startswith('<')))
    if isinstance(x, dict):
        return ' | '.join(f"{pulisci(v)}" for k, v in x.items() if isinstance(v, (str, int, float)))
    return pulisci(x)

def graf(g, out):
    if not isinstance(g, dict): return
    out.append(f"   [Grafico] {pulisci(g.get('titolo',''))} - {pulisci(g.get('sottotitolo',''))}")
    for n in g.get('note', []) or []:
        if isinstance(n, (list, tuple)):
            t = [pulisci(i) for i in n if isinstance(i, str) and not i.startswith('<') and len(i) > 6]
            if t: out.append("      nota sul grafico: " + ' '.join(t))
        elif isinstance(n, str): out.append("      nota sul grafico: " + pulisci(n))
    for e in g.get('eventi', []) or []:
        t = [pulisci(i) for i in (e if isinstance(e, (list, tuple)) else [e]) if isinstance(i, str) and not i.startswith('<') and len(i) > 5]
        if t: out.append("      evento segnato: " + ' '.join(t))

def rendi(path):
    C = carica(path); o = []
    o.append("=== PAGINA 1 ===")
    t = C.get('top', {})
    o += [f"TITOLO DI APERTURA: {pulisci(t.get('titolo',''))}", f"Sommario: {pulisci(t.get('dek',''))}"]
    if t.get('freccia'): o.append("→ " + pulisci(t['freccia']))
    if C.get('quadro'): o.append("Il quadro: " + pulisci(C['quadro']))
    o.append("In 30 secondi:"); o += ["  - " + pulisci(x) for x in C.get('in30', [])]
    if C.get('stamattina'):
        o.append((pulisci(C.get('stamattina_titolo')) if C.get('stamattina_titolo') else "Stamattina") + ":")
        o += ["  - " + riga(x) for x in C['stamattina']]
    o.append("Notizie:")
    for n in C.get('notizie', []):
        o.append(f"  * [{n.get('tag','')}] {pulisci(n.get('titolo',''))}")
        if n.get('testo'): o.append("    " + pulisci(n['testo']))
        if n.get('freccia'): o.append("    → " + pulisci(n['freccia']))
    o.append(""); o.append("=== PAGINE 2-4: ANALISI E STORIE ===")
    for i, m in enumerate(C.get('moduli', []), 1):
        o.append(""); o.append(f"--- Approfondimento {i} ({m.get('misura','')}) - occhiello: {pulisci(m.get('tema',''))} ---")
        o.append("TITOLO: " + pulisci(m.get('titolo','')))
        o.append("[Riquadro accanto al grafico]")
        if m.get('perche'): o.append("  PERCHÉ: " + pulisci(m['perche']))
        if m.get('quindi'): o.append("  E QUINDI: " + pulisci(m['quindi']))
        if m.get('numero'): o.append("  IL NUMERO: " + pulisci(m['numero']))
        graf(m.get('grafico'), o); graf(m.get('grafico2'), o)
        o.append("[Testo]")
        tx = m.get('testo')
        if isinstance(tx, list):
            for p in tx: o.append("   " + riga(p))
        elif tx: o.append("   " + pulisci(tx))
        for p in m.get('punti', []) or []: o.append("   • " + riga(p))
        if m.get('righe'):
            o.append("   [Tabella]")
            for r in m['righe']: o.append("     " + riga(r))
        if m.get('guardare'): o.append("DA GUARDARE: " + pulisci(m['guardare']))
        if m.get('fonte'): o.append(pulisci(m['fonte']))
    o.append(""); o.append("=== PAGINA 5: MERCATI E AGENDA ===")
    if C.get('mercati_titolo'): o.append("Titolo: " + pulisci(C['mercati_titolo']))
    if C.get('lettura'): o.append("La lettura: " + pulisci(C['lettura']))
    if C.get('termometri'):
        o.append("Temi aperti:"); o += ["  - " + riga(x) for x in C['termometri']]
    if C.get('fermi'): o.append("Fermi: " + pulisci(C['fermi']))
    if C.get('ieri'):
        o.append("Ieri:"); o += ["  - " + riga(x) for x in C['ieri']]
    if C.get('agenda'):
        o.append("Agenda:"); o += ["  - " + riga(x) for x in C['agenda'] if riga(x).strip()]
    o.append(""); o.append("=== PAGINA 6: LA SCOMMESSA DELLA SETTIMANA (solo i testi) ===")
    s = C.get('scommessa', {})
    for k, v in s.items():
        if isinstance(v, str) and len(v) > 12 and not v.startswith('<'): o.append(f"{k}: {pulisci(v)}")
        elif isinstance(v, (list, dict)) and v:
            for x in (v if isinstance(v, list) else v.items()): o.append(f"{k}: {riga(x)}")
    if C.get('parole'):
        o.append("Parole di oggi:"); o += ["  - " + riga(x) for x in C['parole']]
    return "\n".join(o)

if __name__ == "__main__":
    print(rendi(sys.argv[1]))
