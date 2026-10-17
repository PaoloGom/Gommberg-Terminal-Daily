"""Grafico della Scommessa per pagina 6.

Una riga per strumento, tutte sulla stessa scala di incertezza: la barra è il range 16-84% del modello (scritto in livelli
agli estremi), la tacca nera è la chiusura di venerdì scorso, il rombo la previsione della redazione, il cerchio (se c'è)
il livello di oggi. Così Brent e EUR/USD si leggono con la stessa chiarezza pur muovendosi in misura molto diversa.

Uso: python3 grafico.py <settimana.json> <uscita.png> [stato.json]   ->  <uscita>.png e <uscita>.svg
"""
import json
import math
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7, "axes.unicode_minus": False, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.spines.left": False, "axes.spines.bottom": False, "svg.fonttype": "path"})
INK, POS, NEG, ORANGE, BAR = "#111111", "#1E7B3A", "#B3261E", "#F26B1D", "#D6D6D6"   # colori del motore
LARGO = (210 - 2 * 14) / 25.4     # larghezza utile della pagina in pollici: il PDF lo usa in scala 1:1
FS_VAL, FS_NOTA = 6.8, 6.5
ORDINE = ["acwi", "spx", "sx5e", "ust10", "ust2", "brent", "eurusd"]


def x(base, liv, tipo):
    return math.log(liv / base) if tipo == "prezzo" else (liv - base) * 100


def fmt(v, k):
    d = {"acwi": 2, "spx": 0, "sx5e": 0, "ust10": 2, "ust2": 2, "brent": 2, "eurusd": 4}.get(k, 2)
    s = f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s + ("%" if k.startswith("ust") else "")


def _box(fig, xpx, ypx, w_pt, h_pt):
    k = fig.dpi / 72
    return (xpx - w_pt * k / 2, ypx - h_pt * k / 2, xpx + w_pt * k / 2, ypx + h_pt * k / 2)


def _urta(a, b, pad=1.5):
    return not (a[2] + pad <= b[0] or b[2] + pad <= a[0] or a[3] + pad <= b[1] or b[3] + pad <= a[1])


def _piazza(ax, ostacoli, xy, testo, candidati, **kw):
    """Prova le posizioni candidate (offset in punti, ha, va) nell'ordine dato e tiene la prima che non tocca nessun
    simbolo o etichetta già piazzata e resta nel grafico; se nessuna è libera, quella con meno sovrapposizione.
    Deterministico: stesso input, stesso risultato."""
    fig = ax.figure; r = fig.canvas.get_renderer(); cornice = ax.get_window_extent(r)
    migliore = None
    for dx, dy, ha, va in candidati:
        t = ax.annotate(testo, xy, xytext=(dx, dy), textcoords="offset points", ha=ha, va=va, **kw)
        e = t.get_window_extent(r); bb = (e.x0, e.y0, e.x1, e.y1)
        fuori = bb[0] < cornice.x0 - 40 or bb[2] > cornice.x1 + 40
        n = sum(_urta(bb, o) for o in ostacoli) + (5 if fuori else 0)
        if n == 0:
            ostacoli.append(bb)
            if migliore:
                migliore[0].remove()
            return t
        if migliore is None or n < migliore[1]:
            if migliore:
                migliore[0].remove()
            migliore = (t, n, bb)
        else:
            t.remove()
    ostacoli.append(migliore[2])
    return migliore[0]


def disegna(reg, out, stato=None):
    st = reg["strumenti"]
    fig, ax = plt.subplots(figsize=(LARGO, float(__import__("os").environ.get("GTD_ALTO_GRAFICO", "1.85"))))  # solo impaginazione
    righe = []
    ORD = [k for k in ORDINE if k in st] + [k for k in st if st[k].get("variabile")]   # 6 fissi + quello della settimana
    for y, k in enumerate(reversed(ORD)):
        v = st[k]
        b, t = v["base"], v["tipo"]
        lo, hi = v["range"]
        s = (x(b, hi, t) - x(b, lo, t)) / 2 or 1.0          # mezza ampiezza del range = 1 unità
        pos = (lambda b_, t_, s_: (lambda liv: x(b_, liv, t_) / s_))(b, t, s)
        ax.plot([pos(lo), pos(hi)], [y, y], color=BAR, lw=8, solid_capstyle="butt", zorder=1)
        ax.plot([0], [y], marker="|", ms=13, color=INK, mew=1.5, zorder=2)
        p = v["previsione_redazione"]
        ax.plot([pos(p)], [y], marker="D", ms=6, color=POS if p > b else NEG, zorder=3)
        xa = a = None
        if stato and k in stato:
            a = stato[k]["ultimo"]
            xa = max(-1.9, min(1.9, pos(a)))
            ax.plot([xa], [y], marker="o", ms=8.5, mfc="none", mec=ORANGE, mew=1.7, zorder=4)
        righe.append((y, k, pos(lo), pos(hi), lo, hi, pos(p), xa, a))
    ax.set_yticks(range(len(ORD)))
    ax.set_yticklabels([("★ " if st[k].get("variabile") else "") + st[k]["nome"] for k in reversed(ORD)], fontsize=7)
    ax.tick_params(axis="y", length=0)
    ax.set_xticks([])
    ax.set_xlim(-2.0, 2.0)
    ax.set_ylim(-0.6, len(ORD) - 0.35)
    fig.text(0.01, 0.01, "Barra: range atteso 16-84% (la chiusura di venerdì ci cade circa 2 settimane su 3). Tacca: chiusura di "
             "partenza. Rombo: la nostra previsione." + (" Cerchio: oggi." if stato else ""),
             fontsize=FS_NOTA, color="#555555", ha="left", va="bottom")
    fig.tight_layout(pad=0.4, rect=(0, 0.08, 1, 1))
    fig.canvas.draw()
    # Etichette dopo l'impaginazione: le collisioni si calcolano in pixel contro tacca, rombo, cerchio e le etichette
    # già piazzate (prima gli estremi del range, poi il livello di oggi), sempre nello stesso ordine.
    tr = ax.transData.transform
    ostacoli = []
    for y, k, xl, xh, lo, hi, xp, xa, a in righe:
        ostacoli.append(_box(fig, *tr((0, y)), 3, 13))            # tacca
        ostacoli.append(_box(fig, *tr((xp, y)), 6.5, 6.5))        # rombo
        if xa is not None:
            ostacoli.append(_box(fig, *tr((xa, y)), 10.5, 10.5))  # cerchio
    est = dict(fontsize=FS_VAL, color="#555555")
    for y, k, xl, xh, lo, hi, xp, xa, a in righe:
        _piazza(ax, ostacoli, (xl, y), fmt(lo, k), [(-4, 0, "right", "center"), (0, -7, "center", "top"),
                                                    (0, 7, "center", "bottom"), (-14, 0, "right", "center")], **est)
        _piazza(ax, ostacoli, (xh, y), fmt(hi, k), [(4, 0, "left", "center"), (0, -7, "center", "top"),
                                                    (0, 7, "center", "bottom"), (14, 0, "left", "center")], **est)
    oggi = dict(fontsize=FS_VAL, color="#B4470F", fontweight="bold")
    for y, k, xl, xh, lo, hi, xp, xa, a in righe:
        if xa is None:
            continue
        _piazza(ax, ostacoli, (xa, y), fmt(a, k),
                [(0, 7, "center", "bottom"), (-5, 7, "right", "bottom"), (5, 7, "left", "bottom"),
                 (0, -7, "center", "top"), (-5, -7, "right", "top"), (5, -7, "left", "top"),
                 (-8, 0, "right", "center"), (8, 0, "left", "center")], **oggi)
    import os
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    fig.savefig(out, dpi=170)
    fig.savefig(out[:-4] + ".svg")
    plt.close(fig)


if __name__ == "__main__":
    reg = json.load(open(sys.argv[1], encoding="utf-8"))
    stato = json.load(open(sys.argv[3], encoding="utf-8"))["righe"] if len(sys.argv) > 3 else None
    disegna(reg, sys.argv[2], stato)
    print("ok", sys.argv[2])
