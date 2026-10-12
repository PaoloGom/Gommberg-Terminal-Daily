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

# 2. Il grafico della scommessa (c_forecast.png/.svg) NON si fa più qui: lo disegna scommessa/grafico.py (vedi ISTRUZIONI, paragrafo 4).
print("ok")
