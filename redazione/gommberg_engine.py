from reportlab import rl_config
rl_config.useA85 = 0   # niente ASCII85: PDF più leggero
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle, Image, KeepTogether, PageBreak)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping

F = "/usr/share/fonts/truetype/dejavu/"
# Inter OTF (CFF) is not supported by ReportLab TTFont; use DejaVu Sans as body face
pdfmetrics.registerFont(TTFont("Body", F + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("Body-B", F + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Body-I", F + "DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFont(TTFont("Cond", F + "DejaVuSansCondensed.ttf"))
pdfmetrics.registerFont(TTFont("Cond-B", F + "DejaVuSansCondensed-Bold.ttf"))
addMapping("Body", 0, 0, "Body"); addMapping("Body", 1, 0, "Body-B"); addMapping("Body", 0, 1, "Body-I")
addMapping("Cond", 0, 0, "Cond"); addMapping("Cond", 1, 0, "Cond-B")

ORANGE = colors.HexColor("#F26B1D"); INK = colors.HexColor("#111111")
GREY = colors.HexColor("#6B6B6B"); RULE = colors.HexColor("#D0D0D0"); TINT = colors.HexColor("#F5F3F0")
GREEN = colors.HexColor("#1E7B3A"); RED = colors.HexColor("#B3261E")

S = {
    "kicker": ParagraphStyle("k", fontName="Cond-B", fontSize=7.5, textColor=ORANGE, leading=9, spaceBefore=8, spaceAfter=1),
    "h1": ParagraphStyle("h1", fontName="Body-B", fontSize=16.5, leading=19.5, textColor=INK, spaceAfter=4),
    "dek": ParagraphStyle("dek", fontName="Body", fontSize=9, leading=12.5, textColor=GREY, spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName="Cond-B", fontSize=10.5, leading=13, textColor=INK, spaceBefore=7, spaceAfter=3),
    "body": ParagraphStyle("b", fontName="Body", fontSize=8.3, leading=11.6, textColor=INK, spaceAfter=4),
    "bul": ParagraphStyle("bul", fontName="Body", fontSize=8.3, leading=11.6, textColor=INK, leftIndent=9,
                          bulletIndent=0, spaceAfter=2.5, bulletFontName="Body", bulletFontSize=6.5, bulletColor=ORANGE),
    "cell": ParagraphStyle("c", fontName="Cond", fontSize=7.6, leading=9.6, textColor=INK),
    "cellb": ParagraphStyle("cb", fontName="Cond-B", fontSize=7.6, leading=9.6, textColor=INK),
    "hdr": ParagraphStyle("hd", fontName="Cond-B", fontSize=7.2, leading=9, textColor=colors.white),
    "note": ParagraphStyle("n", fontName="Body-I", fontSize=6.8, leading=8.8, textColor=GREY, spaceAfter=3),
    "src": ParagraphStyle("s", fontName="Cond", fontSize=7.3, leading=9.4, textColor=colors.HexColor("#4A4A4A"), spaceAfter=1),
    "celln": ParagraphStyle("cn", fontName="Cond", fontSize=7.6, leading=9.6, textColor=INK),
    "tk_l": ParagraphStyle("tl", fontName="Cond", fontSize=6.6, leading=8, textColor=colors.HexColor("#BDBDBD")),
    "tk_v": ParagraphStyle("tv", fontName="Cond-B", fontSize=9.6, leading=11.5, textColor=colors.white),
    "tk_c": ParagraphStyle("tc", fontName="Cond", fontSize=6.8, leading=8.4, textColor=colors.HexColor("#BDBDBD")),
}
import re
PAGINE = {}   # chiave -> pagina, riempito da ancora() durante il render (v6)
RIM_RE = re.compile(r"\[\[(\w+)\]\]")


def rimandi(t):
    """'[[chiave]]' -> '→ pag. N' (N = pagina dell'ancora omonima)."""
    return RIM_RE.sub(lambda m: f'<font name="Cond-B" color="#B4470F">→ pag. {PAGINE.get(m.group(1), "?")}</font>', t)


POS_L, NEG_L, ZERO_L = "#1E7B3A", "#C62828", "#8A8A8A"   # su fondo chiaro
POS_D, NEG_D, ZERO_D = "#3DDC84", "#FF5A52", "#BDBDBD"   # su fondo scuro (striscia in alto)
VAR_RE = re.compile(r"(?<![\w,.])([+-]\d[\d.,]*(?:/[+-]?\d[\d.,]*)*(?:\s?%|\s?pb)?|0 pb)")


def signcol(t, dark=False):
    """Colora ogni variazione col suo segno: verde se positiva, rosso se negativa, grigio se zero."""
    pos, neg, zero = (POS_D, NEG_D, ZERO_D) if dark else (POS_L, NEG_L, ZERO_L)
    t = rimandi(t)

    def rep(m):
        tok = m.group(1)
        if not re.search(r"[1-9]", tok):
            c = zero
        else:
            c = pos if tok.lstrip()[0] == "+" else neg
        return f'<font color="{c}"><b>{tok}</b></font>'
    return VAR_RE.sub(rep, t)


def P(t, s="body"):
    t = rimandi(t)
    if s in ("cell", "cellb"):
        t = signcol(t)
    elif s == "tk_c":
        t = signcol(t, dark=True)
    return Paragraph(t, S[s])
B = lambda t: Paragraph(t, S["bul"], bulletText="▪")

PW, PH = A4; M = 14 * mm
META = {"data_lunga": "", "data_iso": "", "edizione": 0, "nota_dati": ""}

MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre",
        "ottobre", "novembre", "dicembre"]
GIORNI = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
EDIZIONE_1 = __import__("datetime").date(2026, 10, 12)   # n. 001 = lunedì 12 ottobre 2026


# Giorni senza edizione: borse USA ed europee chiuse insieme (Natale, Capodanno, Venerdì Santo).
# Non contano nella numerazione. Aggiornare ogni anno (vedi ISTRUZIONI, paragrafo 6, punto 0).
FESTIVI = {"2026-12-25", "2027-01-01", "2027-03-26", "2028-04-14"}


def giorno_di_uscita(d):
    return d.weekday() < 5 and d.isoformat() not in FESTIVI


def numero_edizione(d):
    """Numero progressivo = giorni di uscita (lun-ven, esclusi FESTIVI) dal 12/10/2026 al giorno d, estremi inclusi."""
    import datetime as dt
    n, x = 0, EDIZIONE_1
    while x <= d:
        if giorno_di_uscita(x):
            n += 1
        x += dt.timedelta(days=1)
    return n


def set_meta(d, nota_dati):
    META.update(data_lunga=f"{GIORNI[d.weekday()]} {d.day} {MESI[d.month - 1]} {d.year}",
                data_iso=d.isoformat(), edizione=numero_edizione(d), nota_dati=nota_dati)


def nome_file(d):
    return f"{d.isoformat()} Gommberg Terminal Daily #{numero_edizione(d):03d}.pdf"


def page(c, doc):
    c.saveState()
    c.setFillColor(INK); c.rect(0, PH - 17 * mm, PW, 17 * mm, fill=1, stroke=0)
    c.setFillColor(ORANGE); c.rect(0, PH - 17.8 * mm, PW, 0.8 * mm, fill=1, stroke=0)
    c.setFont("Cond-B", 15); c.setFillColor(ORANGE); c.drawString(M, PH - 9.6 * mm, "GOMMBERG")
    gw = pdfmetrics.stringWidth("GOMMBERG", "Cond-B", 15)
    c.setFillColor(colors.white); c.drawString(M + gw + 1.5 * mm, PH - 9.6 * mm, "TERMINAL DAILY")
    c.setFont("Cond", 7); c.setFillColor(colors.HexColor("#BDBDBD"))
    c.drawString(M, PH - 13.6 * mm, "Mercati globali  |  Rassegna quotidiana")
    c.setFont("Cond-B", 8.5); c.setFillColor(colors.white)
    c.drawRightString(PW - M, PH - 9.2 * mm, f"{META['data_lunga']}  |  Edizione n. {META['edizione']:03d}")
    c.setFillColor(colors.HexColor("#BDBDBD")); c.setFont("Cond", 7)
    c.drawRightString(PW - M, PH - 13.2 * mm, META["nota_dati"])
    c.setStrokeColor(RULE); c.setLineWidth(0.5); c.line(M, 11 * mm, PW - M, 11 * mm)
    c.setFont("Cond", 6.8); c.setFillColor(GREY)
    c.drawString(M, 7 * mm, "Solo a scopo informativo, non è consulenza finanziaria. "
                            "Le probabilità sono stime redazionali soggettive.")
    c.drawRightString(PW - M, 7 * mm, f"#{META['edizione']:03d}  |  {META['data_iso']}  |  pag. {doc.page}")
    c.restoreState()


CW = PW - 2 * M


def tbl(rows, widths, header=True, zebra=True):
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    st = [("FONTNAME", (0, 0), (-1, -1), "Cond"), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 4),
          ("RIGHTPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 3),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 3), ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE)]
    if header:
        st += [("BACKGROUND", (0, 0), (-1, 0), INK), ("LINEBELOW", (0, 0), (-1, 0), 1.2, ORANGE)]
    if zebra:
        for i in range(1 if header else 0, len(rows)):
            if i % 2 == 0:
                st.append(("BACKGROUND", (0, i), (-1, i), TINT))
    t.setStyle(TableStyle(st))
    return t


def section(title, kicker=None):
    out = []
    if kicker:
        out.append(P(kicker.upper(), "kicker"))
    out.append(P(title, "h2"))
    out.append(Table([[""]], colWidths=[CW], rowHeights=[0.6], style=[("FONTNAME", (0, 0), (-1, -1), "Cond"),
                                                                       ("LINEABOVE", (0, 0), (-1, -1), 0.8, ORANGE)]))
    out.append(Spacer(1, 3))
    return out


def two(img_l, txt_l, img_r, txt_r):
    w = (CW - 6 * mm) / 2
    il = graphic(img_l, w)
    ir = graphic(img_r, w)
    t = Table([[il, ir], [txt_l, txt_r]], colWidths=[w + 3 * mm, w + 3 * mm])
    t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t




def ticker(items):
    """items = [(etichetta, valore, variazione), ...] - max 7 caselle."""
    cells = [[P(a, "tk_l"), P(b, "tk_v"), P(c, "tk_c")] for a, b, c in items]
    row = [Table([[x] for x in c], style=[("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0),
                                           ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5)]) for c in cells]
    strip = Table([row], colWidths=[CW / len(items)] * len(items))
    strip.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1C1C1C")),
                               ("LEFTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 5),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                               ("LINEAFTER", (0, 0), (-2, -1), 0.4, colors.HexColor("#3A3A3A"))]))
    return [strip, Spacer(1, 9)]


def chart_text(img, bullets, fonte):
    """Grafico a sinistra, punti elenco a destra, riga fonte sotto."""
    w = (CW - 6 * mm) / 2
    t = Table([[graphic(img, w), bullets]], colWidths=[w + 3 * mm, w + 3 * mm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    return [t, P(fonte, "src")]


def graphic(path, width):
    """Grafico vettoriale se esiste il gemello .svg (PDF leggero e nitido), altrimenti PNG."""
    import os
    svg = path[:-4] + ".svg" if path.lower().endswith(".png") else path
    if os.path.exists(svg):
        from svglib.svglib import svg2rlg
        d = svg2rlg(svg)
        s = width / d.width
        d.width, d.height = d.width * s, d.height * s
        d.scale(s, s)
        return d
    from reportlab.lib.utils import ImageReader
    iw, ih = ImageReader(path).getSize()
    return Image(path, width=width, height=width * ih / iw)


def headers(*cols):
    return [P(x, "hdr") for x in cols]


def render(path, story):
    doc = BaseDocTemplate(path, pagesize=A4, leftMargin=M, rightMargin=M, topMargin=22 * mm, bottomMargin=15 * mm,
                          title=f"Gommberg Terminal Daily #{META['edizione']:03d} - {META['data_lunga']}",
                          author="Gommberg Terminal Daily", subject="Rassegna mercati globali")
    frame = Frame(M, 15 * mm, PW - 2 * M, PH - 37 * mm, id="f", leftPadding=0, rightPadding=0, topPadding=0,
                  bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=page)])
    from functools import partial
    from reportlab.pdfgen.canvas import Canvas
    doc.build(story, canvasmaker=partial(Canvas, initialFontName="Body", initialFontSize=8))


# ---------------- Componenti aggiunti (v2) ----------------
S.update({
    "nw_tag": ParagraphStyle("nwt", fontName="Cond-B", fontSize=6.8, leading=8, textColor=ORANGE),
    "nw_t": ParagraphStyle("nwh", fontName="Body-B", fontSize=8.6, leading=10.6, textColor=INK, spaceAfter=1.5),
    "nw_b": ParagraphStyle("nwb", fontName="Body", fontSize=7.6, leading=10, textColor=colors.HexColor("#333333")),
    "num": ParagraphStyle("num", fontName="Cond-B", fontSize=17, leading=18, textColor=ORANGE),
    "box_t": ParagraphStyle("bxt", fontName="Cond-B", fontSize=8, leading=10, textColor=ORANGE, spaceAfter=2),
    "box_b": ParagraphStyle("bxb", fontName="Body", fontSize=8, leading=10.8, textColor=INK, leftIndent=8,
                            bulletIndent=0, spaceAfter=1.5, bulletFontName="Body", bulletFontSize=6, bulletColor=ORANGE),
    "grp": ParagraphStyle("grp", fontName="Cond-B", fontSize=7, leading=8.5, textColor=GREY),
    "big": ParagraphStyle("big", fontName="Body-B", fontSize=11, leading=14, textColor=INK, spaceAfter=3),
})


def news_grid(items, cols=2):
    """items = [(tag, titolo, testo), ...]: griglia numerata stile 'top stories'."""
    w = CW / cols
    cells = []
    for i, (tag, tit, txt) in enumerate(items, 1):
        inner = Table([[P(f"{i:02d}", "num"), [P(tag.upper(), "nw_tag"), P(tit, "nw_t"), P(txt, "nw_b")]]],
                      colWidths=[9 * mm, w - 9 * mm - 4 * mm])
        inner.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                   ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0),
                                   ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
        cells.append(inner)
    rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    if len(rows[-1]) < cols:
        rows[-1] += [""] * (cols - len(rows[-1]))
    t = Table(rows, colWidths=[w] * cols)
    t.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "Cond"), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 2),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE)]))
    return t


def box(title, bullets, width=None, bg=TINT):
    """Riquadro evidenziato con titolo e punti elenco (bullets: lista di stringhe)."""
    content = [P(title.upper(), "box_t")] + [Paragraph(signcol(b), S["box_b"], bulletText="▪") for b in bullets]
    t = Table([[content]], colWidths=[width or CW])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 2.2, ORANGE),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return t


def side_by_side(left, right, lw):
    """Due blocchi affiancati: left/right = liste di flowable, lw = larghezza colonna sinistra."""
    t = Table([[left, right]], colWidths=[lw, CW - lw])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (0, -1), 5 * mm), ("RIGHTPADDING", (1, 0), (1, -1), 0),
                           ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    return t


def dash_table(groups, widths):
    """Cruscotto: groups = [(nome_gruppo, [[c1, c2, ...], ...]), ...]. Prima colonna in grassetto,
    variazioni colorate per segno. La prima riga di groups[0] precedente = intestazioni da headers()."""
    hdr, body = groups[0], groups[1:]
    rows, st = [hdr], [("FONTNAME", (0, 0), (-1, -1), "Cond"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 4),
                       ("RIGHTPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 2.2),
                       ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2), ("BACKGROUND", (0, 0), (-1, 0), INK),
                       ("LINEBELOW", (0, 0), (-1, 0), 1.2, ORANGE)]
    for name, lines in body:
        rows.append([P(name.upper(), "grp")] + [""] * (len(widths) - 1))
        r = len(rows) - 1
        st += [("SPAN", (0, r), (-1, r)), ("BACKGROUND", (0, r), (-1, r), TINT), ("TOPPADDING", (0, r), (-1, r), 3)]
        for ln in lines:
            rows.append([P(ln[0], "cellb")] + [P(x, "cell") for x in ln[1:]])
            st.append(("LINEBELOW", (0, len(rows) - 1), (-1, len(rows) - 1), 0.3, RULE))
    t = Table(rows, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle(st))
    return t


def img(path, width):
    """Grafico a larghezza data (vettoriale se esiste il .svg)."""
    return graphic(path, width)


def glossary(terms, cols=2):
    """terms = [(termine, spiegazione), ...] in griglia compatta."""
    cells = [P(f"<b>{t}</b>: {d}", "src") for t, d in terms]
    rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    if len(rows[-1]) < cols:
        rows[-1] += [""] * (cols - len(rows[-1]))
    t = Table(rows, colWidths=[CW / cols] * cols)
    t.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "Cond"), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    return t


# ================= Componenti v6 (nomi vincolanti: vedi SPEC v6) =================
from reportlab.platypus import CondPageBreak, Flowable

ORANGE_D = colors.HexColor("#B4470F")      # freccia "→" e rimandi
S.update({
    "arrow": ParagraphStyle("ar", fontName="Body-I", fontSize=7.6, leading=10, textColor=colors.HexColor("#4A4A4A"),
                            leftIndent=9, firstLineIndent=-9, spaceBefore=1, spaceAfter=3),
    "idx_p": ParagraphStyle("ixp", fontName="Cond-B", fontSize=7, leading=8.5, textColor=ORANGE),
    "idx_t": ParagraphStyle("ixt", fontName="Cond-B", fontSize=8, leading=9.6, textColor=INK),
    "lett": ParagraphStyle("lt", fontName="Body", fontSize=8, leading=11, textColor=INK),
    "tm_f": ParagraphStyle("tmf", fontName="Cond", fontSize=7.4, leading=9.4, textColor=GREY, spaceBefore=2),
    "deep_t": ParagraphStyle("dt", fontName="Body-B", fontSize=11, leading=13.5, textColor=INK, spaceAfter=3),
})
FRECCIA = f'<font name="Body-B" color="#B4470F">→</font>'

# --- Rimandi automatici: ancora("k") segna dove sta un pezzo; nei testi "[[k]]" diventa "→ pag. N" ---


class _Ancora(Flowable):
    def __init__(self, chiave):
        Flowable.__init__(self); self.chiave = chiave; self.width = self.height = 0

    def draw(self):
        PAGINE[self.chiave] = self.canv.getPageNumber()


def ancora(chiave):
    return _Ancora(chiave)


def pag(chiave):
    """Numero di pagina dell'ancora (al primo passo '?', al secondo il valore vero)."""
    return str(PAGINE.get(chiave, "?"))


def arrow(testo):
    """Riga "→" (max 5 per edizione, max 20 parole): perché non ovvio, etichettato M/C/S nel testo se serve."""
    return Paragraph(f"{FRECCIA}&nbsp;&nbsp;{signcol(testo)}", S["arrow"])


def news_grid(items, cols=2, pad=6):
    """items: tuple (tag, titolo, testo) oppure dict {tag, titolo, testo, rimando="k", freccia="..."}.
    rimando = chiave di ancora() (o testo libero "pag. 4"); freccia = riga → sotto la notizia."""
    w = CW / cols
    cells = []
    for i, it in enumerate(items, 1):
        if not isinstance(it, dict):
            it = dict(zip(("tag", "titolo", "testo"), it))
        txt = it["testo"] + (f" [[{it['rimando']}]]" if it.get("rimando") else "")
        txt = signcol(txt)
        body = [P(it["tag"].upper(), "nw_tag"), Paragraph(signcol(it["titolo"]), S["nw_t"]), Paragraph(txt, S["nw_b"])]
        if it.get("freccia"):
            body.append(arrow(it["freccia"]))
        inner = Table([[P(f"{i:02d}", "num"), body]], colWidths=[9 * mm, w - 9 * mm - 4 * mm])
        inner.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                   ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0),
                                   ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
        cells.append(inner)
    rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    if len(rows[-1]) < cols:
        rows[-1] += [""] * (cols - len(rows[-1]))
    t = Table(rows, colWidths=[w] * cols)
    t.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "Cond"), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 2),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), pad - 1),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), pad), ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE)]))
    return t


class Elastico(Flowable):
    """Riempie la pagina: costruisci(pad) -> flowable; sceglie il pad più grande (fino a pad_max) che lascia
    `riserva` punti per ciò che segue. Usato per la griglia notizie di pag. 1."""

    def __init__(self, costruisci, riserva, pad_min=6, pad_max=16):
        Flowable.__init__(self)
        self.c, self.riserva, self.pmin, self.pmax = costruisci, riserva, pad_min, pad_max

    def wrap(self, aW, aH):
        best = self.c(self.pmin)
        for pd in range(self.pmin, self.pmax + 1):
            f = self.c(pd)
            if f.wrap(aW, aH)[1] > aH - self.riserva:
                break
            best = f
        self.f = best
        self.width, self.height = best.wrap(aW, aH)
        return self.width, self.height

    def draw(self):
        self.f.drawOn(self.canv, 0, 0)


def indice_interno(voci, cols=3):
    """voci = [(pagina, etichetta, titolo), ...]; pagina può essere una chiave di ancora() o un numero."""
    cells = []
    for p_, et, tit in voci:
        n = pag(p_) if isinstance(p_, str) and not p_.isdigit() else p_
        cells.append([P(f"PAG. {n}  |  {et.upper()}", "idx_p"), Paragraph(signcol(tit), S["idx_t"])])
    rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    if len(rows[-1]) < cols:
        rows[-1] += [""] * (cols - len(rows[-1]))
    t = Table(rows, colWidths=[CW / cols] * cols)
    t.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "Cond"), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("BACKGROUND", (0, 0), (-1, -1), TINT), ("LINEABOVE", (0, 0), (-1, 0), 1.2, INK),
                           ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                           ("LINEAFTER", (0, 0), (-2, -1), 0.4, RULE), ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE)]))
    return [P("NELLE PAGINE INTERNE", "kicker"), t]


TEND = {"su": ("▲", "in salita"), "giu": ("▼", "in calo"), "fermo": ("■", "stabile")}


def termometri(righe, fermi=""):
    """righe = [(tema, a_che_punto, ultima_novita, tendenza, cosa_guardare)]; tendenza in TEND ('su','giu','fermo')
    o testo libero. fermi = "Iran (dal 12/10), Francia (dal 13/10)" -> riga finale."""
    rows = [headers("Tema", "A che punto", "Ultima novità", "Tendenza", "Cosa guardare")]
    for tema, punto, nov, tend, guarda in righe:
        s, t = TEND.get(tend, ("", tend))
        rows.append([P(tema, "cellb"), P(punto, "celln"), P(nov, "cell"),
                     P(f'<font color="#B4470F">{s}</font> {t}', "celln"), P(guarda, "celln")])
    out = [tbl(rows, [27 * mm, 38 * mm, 50 * mm, 19 * mm, CW - 134 * mm])]
    if fermi:
        out.append(P(f"<b>Fermi:</b> {fermi}", "tm_f"))
    return out


def lettura(testo):
    """Box compatto 'La lettura' (3-5 righe): il contesto che lega i fatti, solo se aggiunge qualcosa."""
    t = Table([[P("LA LETTURA", "box_t"), Paragraph(signcol(testo), S["lett"])]], colWidths=[24 * mm, CW - 24 * mm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (-1, -1), TINT),
                           ("LINEBEFORE", (0, 0), (0, -1), 2.2, ORANGE), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return t


SORPRESA = {"+": f'<font color="{POS_L}"><b>▲ sopra</b></font>', "-": f'<font color="{NEG_L}"><b>▼ sotto</b></font>',
            "=": f'<font color="{ZERO_L}"><b>● in linea</b></font>', "": ""}


def calendario_ieri(righe):
    """righe = [(quando, evento, dato_contro_attese, sorpresa '+'/'-'/'='/'' , freccia max 8 parole o '')]."""
    rows = [headers("Quando", "Evento", "Dato contro attese", "Sorpresa", "→")]
    for q, ev, dato, sor, fr in righe:
        rows.append([P(q, "cellb"), P(ev, "cellb"), P(dato, "celln"), P(SORPRESA.get(sor, sor), "celln"), P(fr, "celln")])
    return tbl(rows, [24 * mm, 44 * mm, 62 * mm, 17 * mm, CW - 147 * mm])


def agenda(righe):
    """righe = [(quando_roma, evento, attese, perche_conta)], max 10, un evento per riga. <b> per l'evento chiave."""
    rows = [headers("Quando (Roma)", "Evento", "Attese", "Perché conta")]
    for q, ev, att, perc in righe:
        rows.append([P(q, "cellb"), P(ev, "cell"), P(att, "celln"), P(perc, "celln")])
    return tbl(rows, [22 * mm, 62 * mm, 46 * mm, CW - 130 * mm])


# --- Riempimento automatico delle pagine (render_v6 a più passi) ---
AGGIUSTA = {"extra": {}, "respiro": {}, "pagine_resp": {}, "n": 0}
MOLLE = set()


class Respiro(Flowable):
    """Spazio elastico tra blocchi: al secondo passo si allarga per riempire la pagina (max 22 mm ciascuno).
    molla=True: prende da sola tutto lo spazio libero della pagina (note ancorate in fondo)."""

    def __init__(self, base=4, molla=False):
        Flowable.__init__(self)
        self.base, self.molla, self.i = base, molla, AGGIUSTA["n"]; AGGIUSTA["n"] += 1
        if molla:
            MOLLE.add(self.i)
        self.width = 0

    def wrap(self, aW, aH):
        pg = AGGIUSTA["pagine_resp"].get(self.i)
        self.height = self.base + AGGIUSTA["respiro"].get((pg, self.molla), 0) * mm
        return 0, min(self.height, aH)

    def draw(self):
        AGGIUSTA["pagine_resp"][self.i] = self.canv.getPageNumber()


def disegna(spec, extra_mm=0, larghezza_mm=None):
    """spec = nome file (grafico già pronto) oppure dict {"tipo": "linee"|"barre", "file": "c_x.png", ...argomenti}.
    Il motore disegna il grafico e, se serve, lo allunga di extra_mm per riempire la pagina."""
    if isinstance(spec, str):
        return spec
    k = dict(spec); tipo, f = k.pop("tipo"), k.pop("file")
    largo = k.get("largo", 3.55)
    if extra_mm and larghezza_mm:
        k["alto"] = k.get("alto", 2.2) + extra_mm / 25.4 * largo / (larghezza_mm / 25.4)
    {"linee": linee, "barre": barre}[tipo](f, **k)
    return f


def _colonne(testi):
    bul = [[Paragraph(signcol(x), S["bul"], bulletText="▪")] for x in testi]
    t = Table([bul], colWidths=[CW / len(bul)] * len(bul))
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 0)]))
    return t


def approfondimento(tema, titolo, formato, chiave=None, **c):
    """Un pezzo di approfondimento. formato:
       "grafico":     img, punti=[str], fonte   (grafico a sinistra, punti a destra)
       "tabella":     righe=[[intestazioni], ...], larghezze=[mm...], lettura, fonte
       "due_grafici": img_sx, img_dx, fonte_sx, fonte_dx (punti sotto, in colonne)
       Facoltativi in tutti: img_sopra (grafico a tutta larghezza in testa), punti, righe+larghezze (tabella),
       lettura, fonte, freccia (riga →). L'altezza si regola con il parametro alto dei grafici."""
    testa = [ancora(chiave)] if chiave else []
    if chiave and any(isinstance(c.get(x), dict) for x in ("img_sopra", "img", "img_sx")):   # allungabile
        ELASTICI.add(chiave)
    testa += [P(f"APPROFONDIMENTO  |  {tema.upper()}", "kicker"), Paragraph(signcol(titolo), S["deep_t"]),
              Table([[""]], colWidths=[CW], rowHeights=[0.6], style=[("LINEABOVE", (0, 0), (-1, -1), 0.8, ORANGE)]),
              Spacer(1, 3)]
    corpo = []
    ex = AGGIUSTA["extra"].get(chiave, 0)
    wh = (CW - 6 * mm) / 2
    riga = isinstance(c.get("img"), dict) or isinstance(c.get("img_sx"), dict)
    if isinstance(c.get("img_sopra"), dict) and riga:
        ex_sopra, ex = ex * 0.45, ex * 0.55          # spazio extra diviso tra grafico in testa e riga di grafici
    else:
        ex_sopra = ex
    if c.get("img_sopra"):
        corpo += [img(disegna(c["img_sopra"], ex_sopra, CW / mm), CW), Spacer(1, 3)]
    if formato == "grafico":
        w = wh
        t = Table([[graphic(disegna(c["img"], ex, w / mm), w), [Paragraph(signcol(x), S["bul"], bulletText="▪") for x in c["punti"]]]],
                  colWidths=[w + 3 * mm, w + 3 * mm])
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
        corpo.append(t)
    elif formato == "due_grafici":
        corpo += [two(disegna(c["img_sx"], ex, wh / mm), P(c.get("fonte_sx", ""), "src"),
                      disegna(c["img_dx"], ex, wh / mm), P(c.get("fonte_dx", ""), "src")),
                  Spacer(1, 4)]
        if c.get("punti"):
            corpo.append(_colonne(c["punti"]))
    elif formato != "tabella":
        raise ValueError(f"formato sconosciuto: {formato}")
    if c.get("righe"):
        r0, *rr = c["righe"]
        rows = [headers(*r0)] + [[P(x, "cellb" if j == 0 else "cell") for j, x in enumerate(r)] for r in rr]
        corpo += [Spacer(1, 3), tbl(rows, [w * mm for w in c["larghezze"]]), Spacer(1, 3)]
    if c.get("lettura"):
        corpo.append(Paragraph("<b>Lettura.</b> " + signcol(c["lettura"]), S["body"]))
    if c.get("fonte"):
        corpo.append(P(c["fonte"], "src"))
    if c.get("freccia"):
        corpo.append(arrow(c["freccia"]))
    return [CondPageBreak(c.get("spazio", 60) * mm), KeepTogether(testa + corpo), Respiro(6)]


def parole(voci):
    """voci = [(concetto, spiegazione in 1-2 righe)], 2-3 voci: concetti (non sigle) comparsi nel numero."""
    cells = [[P(t.upper(), "box_t"), Paragraph(d, S["nw_b"])] for t, d in voci]
    t = Table([cells], colWidths=[CW / len(cells)] * len(cells))
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (-1, -1), TINT),
                           ("LINEBEFORE", (0, 0), (0, -1), 2.2, ORANGE),
                           ("LINEAFTER", (0, 0), (-2, -1), 1.5, colors.white),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return t


# --- Grafici standard v6 (PNG + SVG gemello, stile del giornale) ---
def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5, "axes.edgecolor": "#BBBBBB",
                         "xtick.color": "#555555", "ytick.color": "#333333", "axes.spines.top": False,
                         "axes.spines.right": False, "axes.grid": True, "grid.color": "#E6E6E6", "grid.linewidth": 0.6,
                         "axes.titlesize": 8.5, "axes.titleweight": "bold", "axes.titlelocation": "left",
                         "svg.fonttype": "path"})
    return plt


def _salva(fig, path):
    fig.tight_layout(pad=0.4); fig.savefig(path, dpi=170); fig.savefig(path[:-4] + ".svg"); fig.clf()


def _it(v, dec=1, unita="%"):
    return (f"{v:+.{dec}f}".replace(".", ",") if v else "0") + unita


def barre(path, dati, titolo, unita="%", dec=1, ordina=True, alto=None, largo=3.55):
    """Barre orizzontali colorate per segno. dati = [(etichetta, valore), ...]."""
    plt = _plt()
    d = sorted(dati, key=lambda x: x[1]) if ordina else list(reversed(dati))
    fig, ax = plt.subplots(figsize=(largo, alto or 0.32 * len(d) + 0.55))
    col = ["#1E7B3A" if v > 0 else "#C62828" if v < 0 else "#8A8A8A" for _, v in d]
    ax.barh(range(len(d)), [v for _, v in d], color=col, height=0.62)
    ax.set_yticks(range(len(d))); ax.set_yticklabels([e for e, _ in d], fontsize=7)
    span = max(abs(v) for _, v in d) or 1
    for y, (_, v) in enumerate(d):
        ax.text(v + (0.03 * span if v >= 0 else -0.03 * span), y, _it(v, dec, unita), va="center",
                ha="left" if v >= 0 else "right", fontsize=6.6, color=col[y])
    lo, hi = min(0, min(v for _, v in d)), max(0, max(v for _, v in d))
    ax.set_xlim(lo - 0.28 * span if lo < 0 else -0.05 * span, hi + 0.28 * span if hi > 0 else 0.05 * span)
    ax.axvline(0, color="#888888", lw=0.7); ax.grid(axis="y", visible=False)
    ax.tick_params(axis="x", labelsize=6.5)
    ax.set_title(titolo)
    _salva(fig, path); plt.close(fig)


def linee(path, x, serie, titolo, unita="", alto=2.2, largo=3.55, zero=False, note=()):
    """Linee nel tempo o per categoria. x = lista di date/etichette; serie = [(nome, [valori], colore)];
    note = [(x, y, testo)] etichette con un punto."""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(largo, alto))
    for nome, v, c in serie:
        if v and isinstance(v[0], tuple):          # serie con date proprie: [(x, y), ...]
            ax.plot([a for a, _ in v], [b for _, b in v], color=c, lw=1.6, label=nome)
        else:
            ax.plot(x, v, color=c, lw=1.6, label=nome)
    if zero:
        ax.axhline(0, color="#888888", lw=0.7)
    for nx, ny, nt in note:
        ax.plot([nx], [ny], "o", color="#F26B1D", ms=3)
        ax.annotate(nt, (nx, ny), xytext=(4, 4), textcoords="offset points", fontsize=6.5, color="#333333")
    if unita:
        ax.set_ylabel(unita)
    if len(serie) > 1:
        ax.legend(frameon=False, fontsize=6.8, loc="best")
    import datetime as _dt
    if not x:
        x = [a for a, _ in serie[0][1]]
    if x and isinstance(x[0], _dt.date):
        import matplotlib.dates as mdates
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
        span = (x[-1] - x[0]).days
        ax.xaxis.set_major_locator(mdates.MonthLocator() if span > 100 else mdates.WeekdayLocator(byweekday=0))
        if span > 100:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.tick_params(labelsize=6.6)
    ax.set_title(titolo)
    _salva(fig, path); plt.close(fig)


# --- Render a due passi (rimandi esatti) con controllo del riempimento delle pagine ---
class _Doc(BaseDocTemplate):
    def handle_pageBegin(self):
        BaseDocTemplate.handle_pageBegin(self)

    def handle_pageEnd(self):
        f = self.frame
        self.liberi.append((self.page, round((f._y - f._y1) / mm)))
        BaseDocTemplate.handle_pageEnd(self)


def render_v6(path, costruisci, riempi=(3, 4, 5), margine=3):
    """costruisci() -> story. Passo 1: impaginazione naturale. Passo 2: le pagine in `riempi` con spazio libero in
    fondo vengono riempite allungando i grafici degli approfondimenti (se descritti come dict) o allargando gli spazi
    Respiro. Passo finale: rimandi "→ pag. N" esatti. Stampa i mm liberi per pagina (obiettivo: 6 pagine, < 10 mm)."""
    from functools import partial
    from reportlab.pdfgen.canvas import Canvas
    AGGIUSTA.update(extra={}, respiro={}, pagine_resp={})

    def passo():
        AGGIUSTA["n"] = 0
        doc = _Doc(path, pagesize=A4, leftMargin=M, rightMargin=M, topMargin=22 * mm, bottomMargin=15 * mm,
                   title=f"Gommberg Terminal Daily #{META['edizione']:03d} - {META['data_lunga']}",
                   author="Gommberg Terminal Daily", subject="Rassegna mercati globali")
        doc.liberi = []
        frame = Frame(M, 15 * mm, PW - 2 * M, PH - 37 * mm, id="f", leftPadding=0, rightPadding=0, topPadding=0,
                      bottomPadding=0)
        doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=page)])
        doc.build(costruisci(), canvasmaker=partial(Canvas, initialFontName="Body", initialFontSize=8))
        return dict(doc.liberi)

    passo()
    liberi = passo()          # secondo passo naturale: rimandi già risolti
    prima = dict(PAGINE)
    elastici = {k: p for k, p in PAGINE.items() if k in ELASTICI}
    for pg, mm_lib in liberi.items():
        if pg not in riempi or mm_lib <= margine:
            continue
        pezzi = [k for k, p in elastici.items() if p == pg]
        if pezzi:
            for k in pezzi:
                AGGIUSTA["extra"][k] = (mm_lib - margine) / len(pezzi)
        else:
            molle = [i for i, p in AGGIUSTA["pagine_resp"].items() if p == pg and i in MOLLE]
            n = sum(1 for p in AGGIUSTA["pagine_resp"].values() if p == pg)
            if molle:
                AGGIUSTA["respiro"][(pg, True)] = (mm_lib - margine) / len(molle)
            elif n:
                AGGIUSTA["respiro"][(pg, False)] = min((mm_lib - margine) / n, 22)
    liberi2 = passo()
    if len(liberi2) != len(liberi) or PAGINE != prima:     # se l'impaginazione cambia, si torna al naturale
        AGGIUSTA.update(extra={}, respiro={})
        liberi2 = passo()
    print("Pagine:", len(liberi2), "| mm liberi in fondo:", ", ".join(f"p{p}={l}" for p, l in liberi2.items()))
    print("Rimandi:", PAGINE)
    return liberi2


ELASTICI = set()   # chiavi degli approfondimenti con almeno un grafico descritto come dict (allungabile)


def bivio(titolo, righe, larghezze, nota, kicker="Scenari"):
    """Il bivio (solo con un evento datato decisivo): righe[0] = intestazioni, poi [scenario, prob, effetti...]."""
    r0, *rr = righe
    rows = [headers(*r0)] + [[P(x, "cellb" if j < 2 else "cell") for j, x in enumerate(r)] for r in rr]
    return [CondPageBreak(45 * mm)] + section(titolo, kicker) + [tbl(rows, [w * mm for w in larghezze]), Spacer(1, 2),
                                                                P(nota, "note")]


def _num(s):
    try:
        return float(s.replace("%", "").replace("+", "").replace(".", "").replace(",", ".").strip())
    except ValueError:
        return None


# ================= Composizione dell'edizione v6: lo script del giorno passa solo i contenuti =================
def edizione_v6(C, stato=None, reg=None, verdetto=None, pagella=None):
    """C = dizionario dei contenuti (vedi edizione_modello_v6.py). Restituisce la story completa (6 pagine)."""
    st = []
    # ---------- Pag. 1 ----------
    st += ticker(C["ticker"])
    t = C["top"]
    st += [P(t.get("kicker", "Top story").upper(), "kicker"), P(t["titolo"], "h1"), P(signcol(t["dek"]), "dek")]
    if t.get("freccia"):
        st.append(arrow(t["freccia"]))
    st += [Spacer(1, 3), side_by_side([box("In 30 secondi", C["in30"], width=CW * 0.56 - 5 * mm)],
                                      [box("Stamattina", C["stamattina"], width=CW * 0.44)], CW * 0.56)]
    st += section("Le notizie del giorno", "Top news")
    voci = [("mercati", "Mercati", C.get("mercati_titolo", "Cruscotto, tassi e temi aperti")),
            ("agenda", "Agenda", C.get("agenda_titolo", "Ieri in calendario e in arrivo"))]
    voci += [(a["chiave"], a["tema"], a.get("breve", a["titolo"])) for a in C["approfondimenti"]]
    if stato and not C["scommessa"].get("lunedi"):
        ok = sum(1 for r in stato["righe"].values() if r["strada_giusta"])
        voci.append(("scommessa", "La scommessa", f"{ok}/7 sulla strada giusta"))
    else:
        voci.append(("scommessa", "La scommessa", C["scommessa"].get("breve", "il pronostico della settimana")))
    idx = indice_interno(voci, cols=3)
    riserva = sum(f.wrap(CW, PH)[1] + f.getSpaceBefore() + f.getSpaceAfter() for f in idx) + 4
    st += [Elastico(lambda pd: news_grid(C["notizie"], pad=pd), riserva), Spacer(1, 2)] + idx + [PageBreak()]
    # ---------- Pag. 2 ----------
    st.append(ancora("mercati"))
    st += section("Cruscotto: come stanno andando i mercati", "Mercati")
    dash = dash_table([headers("Indice", "Ultimo", "Data", "1 g", "1 sett.", "Da inizio anno")] + C["cruscotto"],
                      [31 * mm, 18 * mm, 11 * mm, 13 * mm, 14 * mm, 17 * mm])
    bar = [(r[0].replace("&amp;", "&"), _num(r[4])) for _, rr in C["cruscotto"] for r in rr if _num(r[4]) is not None]
    barre("c_sett.png", bar, C.get("grafico_sett", "Variazione nella settimana"), alto=2.9, largo=2.95)
    st.append(side_by_side([dash], [img("c_sett.png", CW - 109 * mm), P(C["cruscotto_nota"], "src")], 109 * mm))
    st += section("Tassi, cambi, materie prime e volatilità", "Cross-asset")
    st.append(dash_table([headers("Strumento", C.get("cross_data", "Livello"), "1 g", "1 sett.", "1 mese", "Lettura")]
                         + C["cross"], [31 * mm, 20 * mm, 14 * mm, 14 * mm, 15 * mm, CW - 94 * mm]))
    if C.get("cross_nota"):
        st.append(P(C["cross_nota"], "note"))
    st += section("Termometri: i temi aperti", "Termometri")
    st += termometri(C["termometri"], C.get("fermi", ""))
    if C.get("lettura"):
        st += [Spacer(1, 4), lettura(C["lettura"])]
    st.append(PageBreak())
    # ---------- Pag. 3-5: flusso continuo ----------
    st.append(ancora("agenda"))
    st += section(C.get("ieri_titolo", "Ieri in calendario"), C.get("ieri_kicker", "Calendario"))
    st += [calendario_ieri(C["ieri"]), Respiro(2)]
    st += section(C.get("agenda_sezione", "In arrivo"), C.get("agenda_kicker", "Agenda"))
    st.append(agenda(C["agenda"]))
    if C.get("agenda_nota"):
        st.append(P(C["agenda_nota"], "note"))
    if C.get("bivio"):
        st += [Respiro(2)] + bivio(**C["bivio"]) + [Respiro(4)]
    for a in C["approfondimenti"]:
        a = dict(a)
        st += approfondimento(a.pop("tema"), a.pop("titolo"), a.pop("formato"), chiave=a.pop("chiave"),
                              **{k: v for k, v in a.items() if k != "breve"})
    st.append(PageBreak())
    # ---------- Pag. 6 ----------
    import sys as _s, os as _o
    _rep = _o.path.join(_o.environ.get("GTD_REPO", "/home/claude/gtd"), "redazione", "scommessa")
    _s.path.insert(0, _rep if _o.path.isdir(_rep) else _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "scommessa"))
    from pagina6 import pagina6_lunedi, pagina6_settimana
    sc = C["scommessa"]
    if "lunedi" not in sc:
        raise SystemExit('C["scommessa"]["lunedi"] mancante: True il primo giorno di borsa della settimana, altrimenti False')
    if not sc["lunedi"] and stato is None:
        raise SystemExit("Scommessa mar-ven senza stato.json nella cartella di lavoro: lancia prima valuta.py --attuali "
                         "(ISTRUZIONI par. 4). Nessuna pag. 6 del lunedì per sbaglio.")
    st.append(ancora("scommessa"))
    if sc["lunedi"]:
        st += pagina6_lunedi(reg, verdetto, pagella, tesi=sc["tesi"], grafico="c_forecast.png",
                             settimana_prec=sc.get("settimana_prec"))
    else:
        st += pagina6_settimana(reg, stato, tesi=sc["tesi"], grafico="c_forecast.png", venerdi=sc.get("venerdi", False))
    if C.get("parole"):
        st += section("Parole di oggi", "Per chi legge") + [parole(C["parole"])]
    st += [Respiro(2, molla=True)] + section("Fonti", "Note")
    if isinstance(C["fonti"], str):
        st.append(P(C["fonti"], "src"))
    else:   # [(sezione, fonti), ...] -> tabella compatta per sezione
        st.append(tbl([[P(a, "cellb"), P(b, "src")] for a, b in C["fonti"]], [34 * mm, CW - 34 * mm], header=False))
    if C.get("errata"):
        st += section("Errata corrige", "Note") + [P(C["errata"], "src")]
    n_arrow = sum(1 for x in _flat(st) if isinstance(x, Paragraph) and x.style.name == "ar")
    if n_arrow > 5:
        print(f"ATTENZIONE: {n_arrow} righe → (massimo 5)")
    return st


def _flat(items):
    for x in items:
        if isinstance(x, (list, tuple)):
            yield from _flat(x)
        elif isinstance(x, Table):
            for row in x._cellvalues:
                yield from _flat(row)
        elif isinstance(x, KeepTogether):
            yield from _flat(x._content)
        else:
            yield x


def voce_indice(C, stato=None, reg=None, ripetizioni=None):
    """Voce v6 per edizioni.json (campi nuovi generati dal codice)."""
    import re as _re
    d = C["data"]
    pulisci = lambda x: _re.sub(r"<[^>]+>|\[\[\w+\]\]", "", x).replace("&amp;", "&").strip()
    v = {"numero": numero_edizione(d), "data": d.isoformat(), "titolo": pulisci(C["top"]["titolo"]), "dek": pulisci(C["top"]["dek"]),
         "sommario": [pulisci(x) for x in C["in30"]],
         "file": f"pdf/{d.isoformat()}-gommberg-{numero_edizione(d):03d}.pdf", "nome": nome_file(d), "pagine": 6,
         "notizie": [pulisci(n["titolo"]) for n in C["notizie"]],
         "ticker": [[pulisci(a), b, c] for a, b, c in C["ticker"]],
         "temi": C.get("temi", []),
         "approfondimenti": [{"tema": a["tema"], "titolo": pulisci(a["titolo"]), "formato": a["formato"]}
                             for a in C["approfondimenti"]],
         "meccanismi": C.get("meccanismi", []), "parole": [p[0] for p in C.get("parole", [])],
         "glossario": C.get("glossario", []), "errata": C.get("errata"), "ripetizioni": ripetizioni}
    if reg:
        sc = {"settimana": reg["settimana"], "strada": None, "range": None, "su": 7, "dettaglio": []}
        if stato:
            rr = stato["righe"]
            sc["strada"] = sum(1 for r in rr.values() if r["strada_giusta"])
            sc["range"] = sum(1 for r in rr.values() if r["dentro_range"])
            sc["dettaglio"] = [[r["nome"], "su" if r["var"] > 0 else "giù" if r["var"] < 0 else "fermo",
                                r["strada_giusta"], r["dentro_range"]] for r in rr.values()]
        v["scommessa"] = sc
    return v
