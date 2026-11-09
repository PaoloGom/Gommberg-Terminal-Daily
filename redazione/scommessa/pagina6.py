"""Pagina 6 (la Scommessa) costruita dai file del laboratorio: nessun numero si scrive a mano.

Nello script dell'edizione, dopo `from gommberg_engine import *`:
    import sys; sys.path.insert(0, "/home/claude/gtd/redazione/scommessa")
    from pagina6 import pagina6_lunedi, pagina6_settimana
    story += pagina6_lunedi(reg, verdetto, pagella, tesi="...", grafico="c_forecast.png")            # lunedì
    story += pagina6_settimana(reg, stato, tesi="...", grafico="c_forecast.png", venerdi=False)     # mar-ven
dove reg = json del registro della settimana, verdetto = json di valuta.py --verdetto (None se non c'è una settimana
precedente), pagella = pagella.json (None se non esiste), stato = json di valuta.py con --attuali.
Dopo queste righe l'edizione aggiunge Glossario e Fonti come sempre.
"""
import datetime as dt
from html import escape as esc

from gommberg_engine import P, B, section, tbl, headers, img, box, side_by_side, box_pari, CW, mm, Spacer
from reportlab.platypus import TableStyle
from reportlab.lib import colors

VAR_BG = colors.HexColor("#FCE7D6")   # riga dello strumento della settimana: lo dice il colore, non il testo
VAR_INK = colors.HexColor("#B84A0C")

ORDINE = ["spx", "sx5e", "ust10", "ust2", "eurusd", "brent", "oro", "acwi"]   # azioni, tassi, valute, materie prime (metodo 1.2); acwi e ust2 solo per i registri vecchi
DEC = {"acwi": 2, "spx": 2, "sx5e": 2, "ust10": 2, "ust2": 2, "brent": 2, "eurusd": 4, "oro": 0}
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre",
        "novembre", "dicembre"]


def ordine(st):
    """Gli strumenti del registro: i fissi nell'ordine di sempre, poi lo strumento della settimana."""
    return [k for k in ORDINE if k in st] + [k for k in st if st[k].get("variabile")]


def fissi(st):
    return [k for k in ordine(st) if not st[k].get("variabile")]


def nome(v):
    return v["nome"]


def evidenzia(t, st, chiavi):
    """Colora la riga dello strumento della settimana (stesso colore della stellina del grafico)."""
    for i, k in enumerate(chiavi, start=1):
        if st[k].get("variabile"):
            t.setStyle(TableStyle([("BACKGROUND", (0, i), (-1, i), VAR_BG), ("LINEBEFORE", (0, i), (0, i), 2.2, VAR_INK)]))
    return t


NOTA_VAR = " Riga arancione e stellina: lo strumento della settimana, scelto sul tema del momento (conto a parte)."


def _par(chiavi):
    """Punteggio atteso senza abilità: 0,68 per il range più la quota di direzione di metodo.json."""
    import json as _j, os as _o
    pd_ = _j.load(open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "metodo.json"), encoding="utf-8"))["par_direzione"]
    return sum(0.68 + pd_.get(k, 0.5) for k in chiavi)


def num(v, d):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def dec(k, v):
    """Decimali secondo la grandezza: così ogni strumento, anche quello della settimana, sta nella sua colonna."""
    if k in DEC:
        return DEC[k]
    a = abs(v)
    return 4 if a < 10 else 2 if a < 1000 else 0


def forchetta(k, lo, hi, unita=None):
    """Range compatto, unità una volta sola: 4.402 - 4.689 $ (mai a capo)."""
    d = dec(k, lo) if k in DEC and abs(lo) < 1000 else dec(k, lo) if k not in DEC else 0
    u = (unita if unita is not None else "$" if k in ("acwi", "brent", "oro") else "%" if k.startswith("ust") else "")
    return f"{num(lo, d)} - {num(hi, d)}" + ("%" if u == "%" else f" {u}" if u else "")


def liv(k, v, unita=None):
    s = num(v, dec(k, v))
    if unita is not None:   # lo strumento della settimana porta la sua unità
        return s + ("%" if unita == "%" else f" {unita}" if unita in ("$", "€") else "")
    return s + " $" if k in ("acwi", "brent", "oro") else s + "%" if k.startswith("ust") else s


def gg_mese(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {MESI[d.month - 1]}"


# ---------------------------------------------------------------------------------------------------------------
# Pagina 6, versione 9/11/2026: un solo tabellone (mercato e la sua domanda, partenza, direzione, forchetta disegnata,
# il perché o a che punto siamo), "Il punto" in tre frasi, due riquadri (Come si gioca; il verdetto o a che punto siamo).
# Ogni dato compare una volta sola. Le domande dei fissi sono testo fisso: nessun token in più per la redazione.
# ---------------------------------------------------------------------------------------------------------------
import math
import re
from reportlab.graphics.shapes import Drawing, Rect, Line, Polygon, String, Circle
from reportlab.platypus import Table
from reportlab.lib.styles import ParagraphStyle
from gommberg_engine import S, GREY, INK, TINT, ORANGE, GREEN, RED, AGGIUSTA

DOMANDA = {"spx": "L'economia e gli utili reggono?", "sx5e": "E l'Europa, casa nostra?",
           "ust10": "Quanto costa il denaro?", "eurusd": "Il dollaro è forte o debole?",
           "brent": "Energia e guerre pesano sui prezzi?", "oro": "Quanta paura c'è?",
           "acwi": "Il mondo intero sale o scende?", "ust2": "Cosa si aspetta dalla Fed?"}
BREVE = {"acwi": "Mondo", "spx": "S&P 500", "sx5e": "Euro Stoxx", "ust10": "Treasury", "ust2": "Treasury 2a",
         "eurusd": "EUR/USD", "brent": "Brent", "oro": "Oro"}
DEC_BARRA = {"spx": 0, "sx5e": 0, "ust10": 2, "ust2": 2, "eurusd": 4, "brent": 2, "oro": 0, "acwi": 2}
VERDE, ROSSO = "#1E7B3A", "#B3261E"
S.setdefault("p6_dom", ParagraphStyle("p6dom", fontName="Cond", fontSize=7.6, leading=9.6, textColor=INK))
S.setdefault("p6_kpi", ParagraphStyle("p6kpi", fontName="Cond-B", fontSize=15, leading=16, textColor=INK))
S.setdefault("p6_kpi_l", ParagraphStyle("p6kpil", fontName="Cond", fontSize=6.8, leading=8.2, textColor=GREY))
S.setdefault("p6_box", ParagraphStyle("p6box", fontName="Body", fontSize=7.9, leading=10.8, textColor=INK, spaceAfter=3))
ETICHETTE = re.compile(r"(Con noi:|Contro:|Da qui a venerdì:|Com'è andata:)")


def _unita(v):
    return v.get("unita") if v.get("variabile") else None


def _nome_domanda(k, v):
    n = v["nome"].replace(" future", "") if not v.get("variabile") else v["nome"]
    d = v.get("motivo_scelta", "") if v.get("variabile") else DOMANDA.get(k, "")
    return P(f"<b>{esc(n)}</b><br/><font color='#6B6B6B' size='6.8'>{esc(d)}</font>", "p6_dom")


def _freccia(v):
    su = v["previsione_redazione"] > v["base"]
    return P(f"<font name='Body-B' color='{VERDE if su else ROSSO}' size='10'>{'↑' if su else '↓'}</font>", "cellb")


def _barra(k, v, w, ultimo=None):
    """La forchetta disegnata: barra = forchetta, tacca = partenza, rombo = nostra previsione, pallino = oggi
    (bianco dentro la forchetta, rosso fuori; oltre la scala resta sul bordo, sempre rosso)."""
    h = 16
    d = Drawing(w, h)
    lo, hi, b = v["range"][0], v["range"][1], v["base"]
    f = (lambda x: math.log(x)) if v["tipo"] == "prezzo" else (lambda x: x)
    span = f(hi) - f(lo)
    a0, a1 = f(lo) - span * 0.25, f(hi) + span * 0.25
    lab = 26
    x0, x1 = lab, w - lab
    X = lambda val: x0 + (f(val) - a0) / (a1 - a0) * (x1 - x0)
    d.add(Rect(X(lo), 5, X(hi) - X(lo), 6, fillColor=colors.HexColor("#D6D6D6"), strokeColor=None))
    d.add(Line(X(b), 2.5, X(b), 13.5, strokeColor=INK, strokeWidth=1.3))
    p = X(v["previsione_redazione"])
    d.add(Polygon([p, 12, p + 3.6, 8, p, 4, p - 3.6, 8], fillColor=GREEN if v["previsione_redazione"] > b else RED,
                  strokeColor=None))
    if ultimo is not None:
        fuori = not (lo <= ultimo <= hi)
        u = max(x0 + 5, min(x1 - 5, X(ultimo)))
        d.add(Circle(u, 8, 2.5, fillColor=colors.HexColor(ROSSO) if fuori else colors.white, strokeColor=INK, strokeWidth=1.1))
    dd = DEC_BARRA.get(k, 4 if abs(lo) < 10 else 2 if abs(lo) < 1000 else 0)
    fm = lambda x: num(x, dd) + ("%" if v["tipo"] == "tasso" else "")
    d.add(String(x0 - 3, 5.6, fm(lo), fontName="Cond", fontSize=6.4, fillColor=GREY, textAnchor="end"))
    d.add(String(x1 + 3, 5.6, fm(hi), fontName="Cond", fontSize=6.4, fillColor=GREY, textAnchor="start"))
    return d


def _testo_punto(etichetta, t):
    t = ETICHETTE.sub(r"<b>\1</b>", esc(t or ""))
    return P(f"<b>{etichetta}</b> {t}", "dek")


def _legenda(reg, oggi=False):
    st = reg["strumenti"]
    var = any(v.get("variabile") for v in st.values())
    return P(f"Partenza: chiusura di venerdì {gg_mese(reg['origine'])}. Barra: la forchetta. Tacca: partenza. "
             "Rombo: la nostra previsione." + (" Pallino: oggi (rosso se fuori dalla forchetta)." if oggi else "")
             + " Per i Treasury la freccia indica il rendimento."
             + (" In arancione lo strumento della settimana, con conto a parte." if var else ""), "note")


def _come_si_gioca(chiavi, compatto=False):
    n, par = len(chiavi), num(_par(chiavi), 1)
    if compatto:
        return ["COME SI GIOCA", P(f"Direzione fissata lunedì per {n} mercati, uno per domanda. Un punto per la direzione, "
                                   f"uno se venerdì la chiusura cade nella forchetta: massimo {2 * n}, chi tira a caso ne fa "
                                   f"{par}.", "p6_box")]
    return ["COME SI GIOCA",
            P(f"{n} domande che muovono tutto il resto, lette in catena: la borsa, il prezzo del denaro, il dollaro, "
              "l'energia, la paura. In arancione, il mercato del momento.", "p6_box"),
            P("La direzione la scegliamo noi; la forchetta è larga quanto l'oscillazione tipica della settimana e contiene "
              f"la chiusura di venerdì circa 2 volte su 3. Un punto per la direzione, uno per la forchetta: massimo {2 * n}, "
              f"chi tira a caso ne fa in media {par}.", "p6_box")]


def _tre(a, b, c, la, lb, lc):
    k = Table([[P(a, "p6_kpi"), P(b, "p6_kpi"), P(c, "p6_kpi")], [P(la, "p6_kpi_l"), P(lb, "p6_kpi_l"), P(lc, "p6_kpi_l")]],
              colWidths=[27 * mm, 24 * mm, 24 * mm])
    k.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 1),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 1), ("VALIGN", (0, 0), (-1, -1), "BOTTOM")]))
    return k


def _segno(ok):
    return f"<font color='{VERDE if ok else ROSSO}'>{'✓' if ok else '✗'}</font>"


def _verdetto(verdetto, settimana_prec, com_e_andata=None):
    if not verdetto:
        return ["IL VERDETTO", P("Prima settimana: il primo verdetto arriva lunedì prossimo.", "p6_box")]
    t = verdetto["totale"]
    n = t["su"] // 2
    segni = [f"{BREVE.get(k, r['nome'])} {_segno(r['punto_direzione'])}{_segno(r['punto_range'])}"
             for k, r in verdetto["righe"].items() if not r.get("variabile")]
    out = [f"IL VERDETTO: SETTIMANA {(settimana_prec or '').upper()}".rstrip(": "),
           _tre(f"{t['punti']}<font size='9' color='#6B6B6B'> su {t['su']}</font>", f"{t['range']} su {n}",
                f"{t['direzione']} su {n}", f"punti (par {num(t['par'], 1)})", "nella forchetta", "direzioni giuste"),
           Spacer(1, 3), P("<font size='6.8' color='#6B6B6B'>direzione / forchetta:</font> " + "  ".join(segni), "p6_box")]
    vv = t.get("variabile")
    if vv:
        out.append(P(f"Della settimana, {esc(vv['nome'])}: {vv['punti']} {'punto' if vv['punti'] == 1 else 'punti'} su 2.", "p6_box"))
    note = sorted({r["nota"] for r in verdetto["righe"].values() if r.get("nota")})
    out += [P(f"Nota: {esc(x)}.", "p6_box") for x in note]
    if com_e_andata:
        out.append(_testo_punto("Com'è andata:", com_e_andata.replace("Com'è andata:", "").strip()))
    return out


def _due_box(sx, dx):
    def cella(x):
        return [P(x[0], "box_t")] + list(x[1:])
    gap, lw = 5 * mm, CW * 0.52
    t = Table([[cella(sx), "", cella(dx)]], colWidths=[lw - gap, gap, CW - lw])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (0, 0), TINT),
                           ("BACKGROUND", (2, 0), (2, 0), TINT), ("LINEBEFORE", (0, 0), (0, 0), 2.2, ORANGE),
                           ("LINEBEFORE", (2, 0), (2, 0), 2.2, ORANGE), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("LEFTPADDING", (1, 0), (1, 0), 0),
                           ("RIGHTPADDING", (1, 0), (1, 0), 0), ("TOPPADDING", (0, 0), (-1, -1), 6),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return t


def _aria(t, n):
    """Il poco spazio rimasto in fondo a pag. 6 (lo misura il motore) va tra le righe del tabellone: max 1,5 mm per riga."""
    extra = min(AGGIUSTA.get("p6_extra_mm", 0) * mm / max(n, 1), 1.5 * mm)
    if extra > 0:
        t.setStyle(TableStyle([("TOPPADDING", (0, 1), (-1, -1), 3 + extra / 2), ("BOTTOMPADDING", (0, 1), (-1, -1), 3 + extra / 2)]))


def pagina6_lunedi(reg, verdetto, pagella, tesi, grafico="c_forecast.png", settimana_prec=None, com_e_andata=None):
    st = reg["strumenti"]
    ven = reg["settimana"].split("/")[1]
    out = section(f"La scommessa della settimana: dove chiudiamo venerdì {gg_mese(ven)}", "Il gran finale  |  Forecast")
    out.append(_testo_punto("La nostra tesi:", tesi))
    wb = 58 * mm
    rows = [headers("Mercato e la sua domanda", "Partenza", "", "Forchetta e nostra previsione", "Il perché")]
    for k in ordine(st):
        v = st[k]
        rows.append([_nome_domanda(k, v), P(liv(k, v["base"], _unita(v)), "celln"), _freccia(v), _barra(k, v, wb),
                     P(esc(v.get("motivo_redazione", "")), "cell")])
    t = tbl(rows, [50 * mm, 16 * mm, 6 * mm, wb, CW - 130 * mm])
    t.setStyle(TableStyle([("VALIGN", (0, 1), (-1, -1), "MIDDLE")]))
    _aria(t, len(rows) - 1)
    out += [evidenzia(t, st, ordine(st)), Spacer(1, 2), _legenda(reg), Spacer(1, 6),
            _due_box(_come_si_gioca(fissi(st)), _verdetto(verdetto, settimana_prec, com_e_andata))]
    return out


def pagina6_settimana(reg, stato, tesi, grafico="c_forecast.png", venerdi=False):
    st, sr = reg["strumenti"], stato["righe"]
    ven = reg["settimana"].split("/")[1]
    out = section("La scommessa della settimana: a che punto siamo", "Il gran finale  |  Forecast")
    out.append(_testo_punto("Il punto:", tesi))
    wb = 54 * mm
    date = sorted({str(sr[k]["data"]) for k in ordine(st)})
    rows = [headers("Mercato e la sua domanda", "Partenza", "", "Forchetta: dove siamo oggi", "Oggi", "Dentro", "On track")]
    for k in ordine(st):
        v, r = st[k], sr[k]
        ok = lambda b: P(f"<font color='{VERDE if b else ROSSO}'><b>{'Sì' if b else 'No'}</b></font>", "celln")
        rows.append([_nome_domanda(k, v), P(liv(k, v["base"], _unita(v)), "celln"), _freccia(v),
                     _barra(k, v, wb, r["ultimo"]), P(liv(k, r["ultimo"], _unita(v)), "celln"), ok(r["dentro_range"]),
                     ok(r["strada_giusta"]) if r["strada_giusta"] is not None else P("-", "celln")])
    t = tbl(rows, [50 * mm, 16 * mm, 6 * mm, wb, 20 * mm, 15 * mm, CW - 161 * mm])
    t.setStyle(TableStyle([("LEFTPADDING", (4, 0), (4, -1), 7)]))
    t.setStyle(TableStyle([("VALIGN", (0, 1), (-1, -1), "MIDDLE")]))
    _aria(t, len(rows) - 1)
    fx = fissi(st)
    n = len(fx)
    dx = ["A CHE PUNTO SIAMO",
          _tre(f"{sum(1 for k in fx if sr[k]['dentro_range'])} su {n}", f"{sum(1 for k in fx if sr[k]['strada_giusta'])} su {n}",
               f"{dt.date.fromisoformat(ven).day} {MESI[dt.date.fromisoformat(ven).month - 1][:3]}", "nella forchetta", "on track", "il verdetto"), Spacer(1, 3)]
    for k in ordine(st):
        if st[k].get("variabile"):
            r = sr[k]
            dx.append(P(f"Della settimana, {esc(st[k]['nome'])}: " + ("nella forchetta" if r["dentro_range"] else "fuori dalla forchetta")
                        + (", on track." if r["strada_giusta"] else "." if r["strada_giusta"] is None else ", direzione contraria."), "p6_box"))
    ult = date[-1] if date else ""
    dx.append(P((f"Ultime chiusure: {gg_mese(ult)}. " if ult else "") + "La previsione non cambia fino a venerdì; \"-\": fermo alla partenza."
                + (" Verdetto lunedì, con le chiusure di stasera." if venerdi else ""), "p6_box"))
    out += [evidenzia(t, st, ordine(st)), Spacer(1, 2), _legenda(reg, oggi=True), Spacer(1, 6),
            _due_box(_come_si_gioca(fx, compatto=True), dx)]
    return out
