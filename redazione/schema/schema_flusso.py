"""Scheda di progetto in PDF: come funziona il Gommberg Terminal Daily, end to end (2 pagine)."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

F = "/usr/share/fonts/truetype/dejavu/"
for n, f in [("Body", "DejaVuSans.ttf"), ("Body-B", "DejaVuSans-Bold.ttf"), ("Cond", "DejaVuSansCondensed.ttf"),
             ("Cond-B", "DejaVuSansCondensed-Bold.ttf"), ("Body-I", "DejaVuSans-Oblique.ttf")]:
    pdfmetrics.registerFont(TTFont(n, F + f))
from reportlab.lib.fonts import addMapping
addMapping("Body", 0, 0, "Body"); addMapping("Body", 1, 0, "Body-B"); addMapping("Body", 0, 1, "Body-I")

ORANGE = colors.HexColor("#F26B1D"); INK = colors.HexColor("#111111"); GREY = colors.HexColor("#5E5A55")
TINT = colors.HexColor("#F5F3F0"); RULE = colors.HexColor("#D9D4CC"); BLUE = colors.HexColor("#1F5FA8")
GREEN = colors.HexColor("#1E7B3A")
W, H = A4
M = 14 * mm

st = {
    "b": ParagraphStyle("b", fontName="Body", fontSize=8.2, leading=11, textColor=INK),
    "s": ParagraphStyle("s", fontName="Body", fontSize=7.4, leading=9.8, textColor=GREY),
    "t": ParagraphStyle("t", fontName="Cond-B", fontSize=9.2, leading=11, textColor=INK),
    "w": ParagraphStyle("w", fontName="Body", fontSize=7.6, leading=10, textColor=colors.white),
}


def para(c, text, x, y_top, w, style="b"):
    p = Paragraph(text, st[style])
    _, h = p.wrap(w, 1000)
    p.drawOn(c, x, y_top - h)
    return h


def masthead(c, pagina, titolo):
    c.setFillColor(INK); c.rect(0, H - 17 * mm, W, 17 * mm, fill=1, stroke=0)
    c.setFillColor(ORANGE); c.rect(0, H - 17.8 * mm, W, 0.8 * mm, fill=1, stroke=0)
    c.setFont("Cond-B", 15); c.setFillColor(ORANGE); c.drawString(M, H - 9.6 * mm, "GOMMBERG")
    gw = pdfmetrics.stringWidth("GOMMBERG", "Cond-B", 15)
    c.setFillColor(colors.white); c.drawString(M + gw + 1.5 * mm, H - 9.6 * mm, "TERMINAL DAILY")
    c.setFont("Cond", 7); c.setFillColor(colors.HexColor("#BDBDBD"))
    c.drawString(M, H - 13.6 * mm, "Scheda di progetto  |  Come funziona, dall'inizio alla fine")
    c.setFont("Cond-B", 8.5); c.setFillColor(colors.white)
    c.drawRightString(W - M, H - 9.6 * mm, "Ottobre 2026")
    c.setFont("Cond-B", 7.5); c.setFillColor(ORANGE)
    c.drawString(M, H - 25 * mm, titolo.upper())
    c.setStrokeColor(RULE); c.setLineWidth(0.5); c.line(M, 11 * mm, W - M, 11 * mm)
    c.setFont("Cond", 6.8); c.setFillColor(GREY)
    c.drawString(M, 7 * mm, "Gommberg Terminal Daily  |  paologom.github.io/Gommberg-Terminal-Daily")
    c.drawRightString(W - M, 7 * mm, f"pag. {pagina} di 2")


def titolo(c, y, t, kicker=None):
    if kicker:
        c.setFont("Cond-B", 7.2); c.setFillColor(ORANGE); c.drawString(M, y, kicker.upper()); y -= 4.6 * mm
    c.setFont("Cond-B", 11); c.setFillColor(INK); c.drawString(M, y, t)
    c.setStrokeColor(ORANGE); c.setLineWidth(0.8); c.line(M, y - 2 * mm, W - M, y - 2 * mm)
    return y - 6 * mm


def freccia(c, x1, y1, x2, y2, col=GREY):
    import math
    c.setStrokeColor(col); c.setFillColor(col); c.setLineWidth(1.1)
    c.line(x1, y1, x2, y2)
    a = math.atan2(y2 - y1, x2 - x1); L = 2.4 * mm
    p = c.beginPath(); p.moveTo(x2, y2)
    p.lineTo(x2 - L * math.cos(a - 0.4), y2 - L * math.sin(a - 0.4))
    p.lineTo(x2 - L * math.cos(a + 0.4), y2 - L * math.sin(a + 0.4)); p.close()
    c.drawPath(p, fill=1, stroke=0)


def blocco(c, x, y_top, w, h, num, tit, testo, fondo=TINT, bordo=ORANGE):
    c.setFillColor(fondo); c.setStrokeColor(fondo); c.rect(x, y_top - h, w, h, fill=1, stroke=0)
    c.setFillColor(bordo); c.rect(x, y_top - h, 1.2 * mm, h, fill=1, stroke=0)
    c.setFont("Cond-B", 15); c.setFillColor(ORANGE); c.drawString(x + 3.5 * mm, y_top - 7 * mm, num)
    c.setFont("Cond-B", 9.2); c.setFillColor(INK); c.drawString(x + 11 * mm, y_top - 6.4 * mm, tit)
    para(c, testo, x + 11 * mm, y_top - 8.6 * mm, w - 13.5 * mm, "s")


def pagina1(c):
    masthead(c, 1, "Il flusso di ogni mattina")
    y = H - 31 * mm
    c.setFont("Body-B", 14); c.setFillColor(INK)
    c.drawString(M, y, "Una rassegna che si scrive, si controlla e si pubblica da sola")
    para(c, "Dal lunedì al venerdì un agente AI (Claude) prepara un PDF di 6 pagine sui mercati globali e lo pubblica "
            "su un sito pubblico. Tutto gira nel cloud di Anthropic: <b>nessun PC deve restare acceso</b>. Paolo riceve "
            "il PDF sul telefono e condivide un solo link, sempre lo stesso.", M, y - 3.5 * mm, W - 2 * M, "b")

    # --- diagramma: 6 blocchi in due colonne a serpentina ---
    top = y - 20 * mm
    bw, bh, gap_x, gap_y = 84 * mm, 27 * mm, 14 * mm, 7 * mm
    xl, xr = M, M + bw + gap_x
    passi = [
        ("1", "Sveglia alle 9:00", "Un'attività programmata (lun-ven, ora di Roma) avvia una sessione di Claude nel "
         "cloud. Nei giorni di borse chiuse (Natale, Capodanno, Venerdì Santo) si ferma da sola."),
        ("2", "Il kit della redazione", "Scarica da GitHub il repository: istruzioni, motore grafico, modello "
         "dell'edizione, controlli, laboratorio della scommessa, archivio di cosa è già uscito."),
        ("3", "Dati e ricerca", "Numeri da FMP e Alpha Vantage (indici, Treasury, petrolio, cambi). Due agenti cercano "
         "notizie e agenda solo su fonti ammesse; ogni fatto ha una scheda con fonte, data e citazione."),
        ("4", "Stesura del PDF", "Scrive le 6 pagine seguendo una struttura fissa; tabelle, variazioni, grafici e "
         "scommessa sono calcolati in codice, mai ricopiati a mano. Niente ripetizioni rispetto a ieri."),
        ("5", "Controlli e revisione", "Controlli automatici su dati, fonti, freschezza, pagine e testata; un revisore "
         "indipendente verifica i fatti sul web. Gli errori si correggono da soli prima di pubblicare."),
        ("6", "Pubblicazione e consegna", "Il PDF va sul sito GitHub Pages (pubblico, aperto anche dal PC aziendale) e "
         "nell'archivio su Claude, poi arriva a Paolo in chat con 3 righe di sintesi. Verso le 9:45-10:00."),
    ]
    pos = []
    for i, (n, t, d) in enumerate(passi):
        riga = i // 2
        x = xl if i % 2 == 0 else xr
        yt = top - riga * (bh + gap_y)
        blocco(c, x, yt, bw, bh, n, t, d)
        pos.append((x, yt))
    for i in range(5):
        (x1, y1), (x2, y2) = pos[i], pos[i + 1]
        if i % 2 == 0:   # sinistra -> destra
            freccia(c, x1 + bw + 1 * mm, y1 - bh / 2, x2 - 1 * mm, y2 - bh / 2, ORANGE)
        else:            # destra -> sinistra in basso (diagonale)
            freccia(c, x1 + bw * 0.25, y1 - bh - 0.8 * mm, x2 + bw * 0.75, y2 + 0.8 * mm, ORANGE)
    y = top - 3 * (bh + gap_y) - 2 * mm

    # --- striscia "dove sta cosa" ---
    y = titolo(c, y - 2 * mm, "Dove sta cosa", "Le quattro parti")
    cols = [
        ("Il sito", "paologom.github.io/<br/>Gommberg-Terminal-Daily", "Ultima edizione in apertura, PDF da sfogliare "
         "e scaricare, archivio di tutte le edizioni. Il link da condividere."),
        ("Il repository", "GitHub: PaoloGom/<br/>Gommberg-Terminal-Daily", "La redazione: istruzioni, programmi, "
         "registro delle fonti e della scommessa. Ogni modifica è tracciata."),
        ("L'archivio Claude", "claude.ai (copia privata)", "Stessa pagina del sito, per Paolo, dentro l'app di Claude."),
        ("L'attività programmata", "Claude, nel cloud", "Parte alle 9:00 lun-ven; prepara, controlla, pubblica e "
         "consegna senza intervento."),
    ]
    cw = (W - 2 * M - 3 * 4 * mm) / 4
    hmax = 0
    for i, (t, sub, d) in enumerate(cols):
        x = M + i * (cw + 4 * mm)
        c.setFillColor(INK); c.rect(x, y - 7 * mm, cw, 7 * mm, fill=1, stroke=0)
        c.setFont("Cond-B", 8.6); c.setFillColor(colors.white); c.drawString(x + 2.5 * mm, y - 4.8 * mm, t)
        h1 = para(c, f"<b>{sub}</b>", x + 1 * mm, y - 9 * mm, cw - 2 * mm, "s")
        h2 = para(c, d, x + 1 * mm, y - 10.5 * mm - h1, cw - 2 * mm, "s")
        hmax = max(hmax, 10.5 * mm + h1 + h2)
    y -= hmax + 10 * mm

    # --- chi fa cosa ---
    y = titolo(c, y, "Chi fa cosa", "Ruoli")
    half = (W - 2 * M - 6 * mm) / 2
    c.setFillColor(TINT); c.rect(M, y - 27 * mm, half, 27 * mm, fill=1, stroke=0)
    c.setFillColor(TINT); c.rect(M + half + 6 * mm, y - 27 * mm, half, 27 * mm, fill=1, stroke=0)
    c.setFont("Cond-B", 9); c.setFillColor(ORANGE)
    c.drawString(M + 3 * mm, y - 5 * mm, "PAOLO (EDITORE)")
    c.drawString(M + half + 9 * mm, y - 5 * mm, "CLAUDE (REDAZIONE)")
    para(c, "- Legge il PDF e condivide il link.<br/>- Chiede modifiche scrivendo a Claude dall'app, anche da "
            "telefono (\"Gommberg: ...\").<br/>- Decide le scelte editoriali e le fonti nuove.", M + 3 * mm, y - 7.5 * mm,
         half - 6 * mm, "s")
    para(c, "- Ogni mattina: ricerca, stesura, controlli, pubblicazione.<br/>- Applica le modifiche richieste al kit "
            "su GitHub: valgono dal giorno dopo.<br/>- Tiene la pagella della scommessa e propone i miglioramenti solo "
            "se i dati li giustificano.", M + half + 9 * mm, y - 7.5 * mm, half - 6 * mm, "s")


def pagina2(c):
    masthead(c, 2, "Cosa c'è dentro e come si tiene in piedi")
    y = H - 31 * mm
    y = titolo(c, y, "Le 6 pagine dell'edizione", "Il prodotto")
    pag = [("1", "Prima pagina", "Ticker di 7 mercati, notizia del giorno, \"In 30 secondi\", stamattina, 8 top news"),
           ("2", "Mercati", "Cruscotto degli indici mondiali, tassi-cambi-materie prime, quadro macro"),
           ("3", "Catalizzatori", "Cosa ha mosso i mercati, agenda della settimana con attese e perché conta"),
           ("4", "Scenari e Treasury", "Scenari per l'evento chiave, mappa dei rischi, approfondimento sui tassi USA"),
           ("5", "Geopolitica e mercati", "Iran, petrolio, euro/dollaro"),
           ("6", "La scommessa", "Previsione della chiusura del venerdì per 7 mercati, pagella, glossario, fonti")]
    tw, th = (W - 2 * M - 2 * 4 * mm) / 3, 19 * mm
    for i, (n, t, d) in enumerate(pag):
        x = M + (i % 3) * (tw + 4 * mm)
        yt = y - (i // 3) * (th + 3.5 * mm)
        blocco(c, x, yt, tw, th, n, t, d)
    y -= 2 * (th + 3.5 * mm) + 4 * mm

    # --- la scommessa: ciclo ---
    y = titolo(c, y, "La scommessa: un piccolo laboratorio scientifico", "Il gran finale")
    fasi = [("LUNEDÌ", "Pronostico", "La redazione sceglie la direzione per 7 mercati; il modello calcola il range in "
             "cui la chiusura cade circa 2 settimane su 3."),
            ("MAR-VEN", "A che punto siamo", "Ogni giorno: dentro il range? sulla strada giusta? La previsione non "
             "cambia."),
            ("LUNEDÌ DOPO", "Verdetto", "1 punto per la direzione, 1 per il range (max 14). Il \"par\" senza abilità è "
             "circa 8,5: conta batterlo."),
            ("OGNI 6 MESI", "Revisione", "Backtest su 12 anni; un metodo nuovo entra solo se supera una soglia "
             "statistica fissata prima.")]
    fw = (W - 2 * M - 3 * 6 * mm) / 4
    fh = 30 * mm
    for i, (k, t, d) in enumerate(fasi):
        x = M + i * (fw + 6 * mm)
        c.setFillColor(INK if i < 3 else BLUE); c.roundRect(x, y - fh, fw, fh, 2 * mm, fill=1, stroke=0)
        c.setFont("Cond-B", 7); c.setFillColor(ORANGE if i < 3 else colors.white); c.drawString(x + 3 * mm, y - 5 * mm, k)
        c.setFont("Cond-B", 9.5); c.setFillColor(colors.white); c.drawString(x + 3 * mm, y - 9.5 * mm, t)
        para(c, d, x + 3 * mm, y - 11.5 * mm, fw - 6 * mm, "w")
        if i < 3:
            freccia(c, x + fw + 0.8 * mm, y - fh / 2, x + fw + 5.2 * mm, y - fh / 2, ORANGE)
    y -= fh + 3 * mm
    para(c, "<b>Cosa dicono 12 anni di dati:</b> nessun metodo testato prevede la direzione della settimana meglio del "
            "caso; il range (volatilità delle ultime 4 settimane) è invece ben calibrato. Per questo il modello misura "
            "l'incertezza e la redazione fa la scommessa: dopo 26 settimane un test dirà se le nostre scelte valgono "
            "più del caso.", M, y, W - 2 * M, "s")
    y -= 20 * mm

    # --- qualità + modifiche + numeri ---
    y = titolo(c, y, "Come si evitano gli errori", "Affidabilità")
    righe = [("Fonti a livelli", "Reuters, AP, Bloomberg, ANSA, Sole 24 Ore e siti ufficiali bastano da soli; gli "
              "altri servono in coppia; blog e aggregatori sono vietati."),
             ("Una scheda per ogni fatto", "Fonte, data dell'evento e citazione: niente scheda, niente notizia."),
             ("Controlli automatici", "Dati fermi o intraday, pagine, trattini, numero e data in testata, edizioni "
              "duplicate, chiusure mancanti per la scommessa."),
             ("Revisore indipendente", "Un secondo agente verifica sul web top story, notizie e agenda; gli errori si "
              "correggono prima di pubblicare, altrimenti si toglie il dettaglio."),
             ("Errata corrige", "Se un errore sfugge, la correzione esce nell'edizione successiva.")]
    for t, d in righe:
        c.setFillColor(ORANGE); c.rect(M, y - 3.2 * mm, 1.6 * mm, 1.6 * mm, fill=1, stroke=0)
        c.setFont("Cond-B", 8.4); c.setFillColor(INK); c.drawString(M + 4 * mm, y - 3.3 * mm, t)
        h = para(c, d, M + 50 * mm, y - 0.9 * mm, W - 2 * M - 50 * mm, "s")
        y -= max(h, 4 * mm) + 2.2 * mm
    y -= 7 * mm

    y = titolo(c, y, "In numeri", "Riepilogo")
    num = [("9:00", "partenza, lun-ven"), ("~10:00", "PDF online e in chat"), ("6", "pagine, struttura fissa"),
           ("0", "PC da tenere accesi"), ("1", "link da condividere")]
    nw = (W - 2 * M) / 5
    for i, (a, b) in enumerate(num):
        x = M + i * nw
        c.setFont("Cond-B", 18); c.setFillColor(ORANGE); c.drawString(x, y - 7 * mm, a)
        c.setFont("Body", 7.2); c.setFillColor(GREY); c.drawString(x, y - 11.5 * mm, b)
    y -= 16 * mm
    para(c, "Solo a scopo informativo: il Gommberg Terminal Daily non è consulenza finanziaria. Le probabilità sono stime "
            "redazionali.", M, y, W - 2 * M, "s")


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "scheda.pdf"
    c = canvas.Canvas(out, pagesize=A4)
    c.setTitle("Gommberg Terminal Daily - Come funziona"); c.setAuthor("Gommberg Terminal Daily")
    pagina1(c); c.showPage(); pagina2(c); c.showPage(); c.save()
    print("ok", out)
