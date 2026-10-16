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
    d = {"acwi": 2, "spx": 0, "sx5e": 0, "ust10": 2, "ust2": 2, "brent": 2, "eurusd": 4}[k]
    s = f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s + ("%" if k.startswith("ust") else "")


def disegna(reg, out, stato=None):
    st = reg["strumenti"]
    fig, ax = plt.subplots(figsize=(LARGO, float(__import__("os").environ.get("GTD_ALTO_GRAFICO", "1.85"))))  # solo impaginazione
    for y, k in enumerate(reversed(ORDINE)):
        v = st[k]
        b, t = v["base"], v["tipo"]
        lo, hi = v["range"]
        s = (x(b, hi, t) - x(b, lo, t)) / 2 or 1.0          # mezza ampiezza del range = 1 unità

        def pos(liv):
            return x(b, liv, t) / s
        ax.plot([pos(lo), pos(hi)], [y, y], color=BAR, lw=8, solid_capstyle="butt", zorder=1)
        ax.plot([0], [y], marker="|", ms=13, color=INK, mew=1.5, zorder=2)
        xa = None
        if stato and k in stato:
            a = stato[k]["ultimo"]
            xa = max(-1.9, min(1.9, pos(a)))
        # estremi del range accanto alla barra; se il cerchio di oggi ci cade vicino, l'estremo va sotto la barra
        for liv, lato in ((lo, -1), (hi, 1)):
            xe = pos(liv)
            testo_e = fmt(liv, k)
            vicino = xe + 0.06 * lato, xe + (0.06 + 0.045 * len(testo_e)) * lato   # spazio dell'etichetta a lato
            if xa is not None and min(vicino) < xa + 0.11 and max(vicino) > xa - 0.11:   # il cerchio la coprirebbe
                ax.annotate(fmt(liv, k), (xe, y), xytext=(0, -6), textcoords="offset points", ha="center", va="top",
                            fontsize=FS_VAL, color="#555555")
            else:
                ax.text(xe + 0.06 * lato, y, fmt(liv, k), ha="left" if lato > 0 else "right", va="center",
                        fontsize=FS_VAL, color="#555555")
        p = v["previsione_redazione"]
        ax.plot([pos(p)], [y], marker="D", ms=6, color=POS if p > b else NEG, zorder=3)
        if xa is not None:
            ax.plot([xa], [y], marker="o", ms=8.5, mfc="none", mec=ORANGE, mew=1.7, zorder=4)
            ax.annotate(fmt(a, k), (xa, y), xytext=(0, 6), textcoords="offset points", ha="center", va="bottom",
                        fontsize=FS_VAL, color="#B4470F", fontweight="bold")
    ax.set_yticks(range(len(ORDINE)))
    ax.set_yticklabels([st[k]["nome"] for k in reversed(ORDINE)], fontsize=7)
    ax.tick_params(axis="y", length=0)
    ax.set_xticks([])
    ax.set_xlim(-2.0, 2.0)
    ax.set_ylim(-0.6, len(ORDINE) - 0.35)
    fig.text(0.01, 0.01, "Barra: range atteso 16-84% (la chiusura di venerdì ci cade circa 2 settimane su 3). Tacca: chiusura di "
             "partenza. Rombo: la nostra previsione." + (" Cerchio: oggi." if stato else ""),
             fontsize=FS_NOTA, color="#555555", ha="left", va="bottom")
    fig.tight_layout(pad=0.4, rect=(0, 0.08, 1, 1))
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
