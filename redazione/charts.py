import datetime as dt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager as fm
from data import *

for f in ["/usr/share/fonts/opentype/inter/Inter-Regular.otf", "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"]:
    fm.fontManager.addfont(f)
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": "#BBBBBB",
    "axes.labelcolor": "#333333", "xtick.color": "#555555", "ytick.color": "#555555",
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": "#E6E6E6", "grid.linewidth": 0.6, "axes.titlesize": 9,
    "axes.titleweight": "bold", "axes.titlelocation": "left", "svg.fonttype": "path",
})
ORANGE, INK, GREY, BLUE = "#F26B1D", "#111111", "#9A9A9A", "#1F5FA8"
W = 3.55


def save(fig, name):
    fig.tight_layout(pad=0.4)
    fig.savefig(name, dpi=170); fig.savefig(name.replace(".png", ".svg"))
    plt.close(fig)


# 1. Curva Treasury: 28 set vs 9 ott
fig, ax = plt.subplots(figsize=(W, 2.25))
labels = list(UST_CURVE_1009.keys())
x = range(len(labels))
ax.plot(x, [UST_CURVE_0928[k] for k in labels], color=GREY, lw=1.4, marker="o", ms=2.5, label="28 set")
ax.plot(x, [UST_CURVE_1009[k] for k in labels], color=ORANGE, lw=1.8, marker="o", ms=2.5, label="9 ott")
ax.set_xticks(list(x)); ax.set_xticklabels(labels, fontsize=7)
ax.set_ylabel("%")
ax.set_title("Curva Treasury: breve giù, lunga ferma")
ax.legend(frameon=False, fontsize=7, loc="lower right")
save(fig, "c_curve.png")

# 2. 2Y/10Y/30Y ultime due settimane
fig, ax = plt.subplots(figsize=(W, 2.25))
d = [dt.date.fromisoformat(r[0]) for r in UST_ALL]
for i, (lab, c) in enumerate([("2 anni", BLUE), ("10 anni", ORANGE), ("30 anni", INK)]):
    ax.plot(d, [r[i + 1] for r in UST_ALL], color=c, lw=1.6, label=lab)
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
ax.set_ylabel("%")
ax.set_title("Treasury 2-10-30 anni: +40 pb in un mese")
ax.set_ylim(4.3, 5.95); ax.legend(frameon=False, fontsize=7, ncol=3, loc="upper left")
save(fig, "c_yields.png")

# 3. Brent spot EIA dalla vigilia della guerra
b = parse(BRENT_SPOT_RAW)
fig, ax = plt.subplots(figsize=(W, 2.25))
ax.plot([p[0] for p in b], [p[1] for p in b], color=INK, lw=1.2)
ax.axvline(dt.date(2026, 2, 28), color=ORANGE, lw=1, ls="--")
ax.text(dt.date(2026, 3, 3), 66, "inizio guerra\n28 feb", fontsize=6.5, color=ORANGE, va="bottom")
ax.axhline(104.72, color=BLUE, lw=0.9, ls=":")
ax.text(dt.date(2026, 5, 25), 106.2, "Brent future 104,72 $ (9 ott)", fontsize=6.5, color=BLUE)
ax.xaxis.set_major_locator(mdates.MonthLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
ax.set_ylabel("$/barile")
ax.set_title("Brent fisico (EIA spot FOB) vs future")
save(fig, "c_brent.png")

# 4. EUR/USD
e = parse(EURUSD_RAW)
fig, ax = plt.subplots(figsize=(W, 2.25))
ax.plot([p[0] for p in e], [p[1] for p in e], color=BLUE, lw=1.4)
ax.annotate("1,1679\n21 ago", xy=(dt.date(2026, 8, 21), 1.1679), xytext=(dt.date(2026, 7, 18), 1.163),
            fontsize=6.5, arrowprops=dict(arrowstyle="-", color=GREY, lw=0.6))
ax.annotate("1,1201\n9 ott", xy=(dt.date(2026, 10, 9), 1.1201), xytext=(dt.date(2026, 9, 10), 1.122),
            fontsize=6.5, arrowprops=dict(arrowstyle="-", color=GREY, lw=0.6))
ax.xaxis.set_major_locator(mdates.MonthLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
ax.set_title("EUR/USD: -4,1% dal picco di agosto")
save(fig, "c_eurusd.png")

