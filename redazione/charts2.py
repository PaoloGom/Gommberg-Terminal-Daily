import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

for f in ["/usr/share/fonts/opentype/inter/Inter-Regular.otf", "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"]:
    fm.fontManager.addfont(f)
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": "#BBBBBB",
    "axes.labelcolor": "#333333", "xtick.color": "#555555", "ytick.color": "#333333",
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": "#E6E6E6", "grid.linewidth": 0.6, "axes.titlesize": 9,
    "axes.titleweight": "bold", "axes.titlelocation": "left", "svg.fonttype": "path",
})
ORANGE, INK, GREY, BLUE = "#F26B1D", "#111111", "#9A9A9A", "#1F5FA8"
POS, NEG = "#1E7B3A", "#C62828"


def it(x, d=1):
    return f"{x:+.{d}f}".replace(".", ",")


# 1. Performance settimanale degli indici (5-9 ottobre)
perf = [("S&P 500", 1.15), ("Nikkei 225", 1.06), ("Hang Seng", 1.00), ("Dow Jones", 0.9), ("FTSE 100", 0.86),
        ("Nasdaq Comp.", 0.64), ("MSCI ACWI (ETF)", 0.51), ("Russell 2000", -0.9), ("Euro Stoxx 50", -0.96)]
perf = sorted(perf, key=lambda x: x[1])
fig, ax = plt.subplots(figsize=(3.55, 2.6))
ys = range(len(perf))
ax.barh(list(ys), [p[1] for p in perf], color=[POS if p[1] >= 0 else NEG for p in perf], height=0.62)
ax.set_yticks(list(ys)); ax.set_yticklabels([p[0] for p in perf], fontsize=7.2)
for y, (_, v) in zip(ys, perf):
    ax.text(v + (0.05 if v >= 0 else -0.05), y, it(v) + "%", va="center", ha="left" if v >= 0 else "right",
            fontsize=6.8, color=POS if v >= 0 else NEG)
ax.axvline(0, color="#888888", lw=0.7)
ax.set_xlim(-1.6, 1.7); ax.grid(axis="y", visible=False)
ax.set_xticks([-1, 0, 1]); ax.set_xticklabels(["-1%", "0", "+1%"])
ax.set_title("Indici: variazione settimana 5-9 ottobre")
fig.tight_layout(pad=0.4); fig.savefig("c_week.png", dpi=170); fig.savefig("c_week.svg"); plt.close(fig)

# 2. La scommessa: range ±1σ e previsione puntuale, in % dalla chiusura del 9/10
fc = [  # nome, range basso %, range alto %, previsione %
    ("MSCI ACWI (ETF)", -1.6, 1.6, 0.2),
    ("S&P 500", -2.1, 2.1, 0.4),
    ("Euro Stoxx 50", -1.7, 1.7, 0.9),
    ("Brent future", -6.6, 7.1, -2.6),
    ("EUR/USD", -0.7, 0.7, -0.2),
]
fig, ax = plt.subplots(figsize=(7.3, 1.85))
for y, (n, lo, hi, p) in enumerate(reversed(fc)):
    ax.plot([lo, hi], [y, y], color="#D9D9D9", lw=7, solid_capstyle="butt")
    ax.plot([0], [y], marker="|", ms=12, color=INK, mew=1.4)
    ax.plot([p], [y], marker="D", ms=6.5, color=POS if p >= 0 else NEG, zorder=3)
    ax.text(p + (0.45 if p >= 0 else -0.45), y + 0.02, it(p) + "%", ha="left" if p >= 0 else "right", va="center", fontsize=7.2, color=POS if p >= 0 else NEG, weight="bold")
ax.set_yticks(range(len(fc))); ax.set_yticklabels([f[0] for f in reversed(fc)], fontsize=7.5)
ax.axvline(0, color="#888888", lw=0.6, ls=":")
ax.set_xlim(-8, 8); ax.set_ylim(-0.6, len(fc) - 0.15)
ax.set_xticks([-6, -4, -2, 0, 2, 4, 6]); ax.set_xticklabels(["-6%", "-4%", "-2%", "0", "+2%", "+4%", "+6%"])
ax.grid(axis="y", visible=False)
ax.set_title("Previsione al 16/10 (rombo) e range atteso (barra), in % dalla chiusura del 9/10", pad=8)
fig.tight_layout(pad=0.4); fig.savefig("c_forecast.png", dpi=170); fig.savefig("c_forecast.svg"); plt.close(fig)
print("ok")
