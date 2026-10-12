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
POS_L, NEG_L, ZERO_L = "#1E7B3A", "#C62828", "#8A8A8A"   # su fondo chiaro
POS_D, NEG_D, ZERO_D = "#3DDC84", "#FF5A52", "#BDBDBD"   # su fondo scuro (striscia in alto)
VAR_RE = re.compile(r"(?<![\w,.])([+-]\d[\d.,]*(?:/[+-]?\d[\d.,]*)*(?:\s?%|\s?pb)?|0 pb)")


def signcol(t, dark=False):
    """Colora ogni variazione col suo segno: verde se positiva, rosso se negativa, grigio se zero."""
    pos, neg, zero = (POS_D, NEG_D, ZERO_D) if dark else (POS_L, NEG_L, ZERO_L)

    def rep(m):
        tok = m.group(1)
        if not re.search(r"[1-9]", tok):
            c = zero
        else:
            c = pos if tok.lstrip()[0] == "+" else neg
        return f'<font color="{c}"><b>{tok}</b></font>'
    return VAR_RE.sub(rep, t)


def P(t, s="body"):
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
