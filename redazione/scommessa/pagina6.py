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

from gommberg_engine import P, B, section, tbl, headers, img, box, side_by_side, CW, mm, Spacer

ORDINE = ["acwi", "spx", "sx5e", "ust10", "ust2", "brent", "eurusd"]
DEC = {"acwi": 2, "spx": 2, "sx5e": 2, "ust10": 2, "ust2": 2, "brent": 2, "eurusd": 4}
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre",
        "novembre", "dicembre"]


def ordine(st):
    """Gli strumenti del registro, nell'ordine di sempre (un registro vecchio può averne uno in più)."""
    return [k for k in ORDINE if k in st]


def _par(chiavi):
    """Punteggio atteso senza abilità: 0,68 per il range più la quota di direzione di metodo.json."""
    import json as _j, os as _o
    pd_ = _j.load(open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "metodo.json"), encoding="utf-8"))["par_direzione"]
    return sum(0.68 + pd_.get(k, 0.5) for k in chiavi)


def num(v, d):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def liv(k, v):
    s = num(v, DEC[k])
    return s + " $" if k in ("acwi", "brent") else s + "%" if k.startswith("ust") else s


def gg_mese(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {MESI[d.month - 1]}"


def _regole(chiavi, compatto=False):
    n, par = len(chiavi), num(_par(chiavi), 1)
    if compatto:   # mar-ven: 1-2 righe; le regole complete escono il lunedì
        return box("Le regole del gioco", [
            f"Direzione fissata lunedì per {n} mercati: 1 punto per la direzione, 1 per la chiusura di venerdì nel range "
            f"(massimo {2 * n}, par circa {par}). Regole complete il lunedì."], width=CW * 0.5 - 4 * mm)
    return box("Le regole del gioco", [
        f"Ogni lunedì scegliamo una direzione per {n} mercati; la previsione non cambia fino a venerdì.",
        f"1 punto per la direzione giusta, 1 punto se la chiusura di venerdì cade nel range: massimo {2 * n}.",
        f"Il range contiene la chiusura circa 2 settimane su 3. Senza alcuna abilità si fanno in media circa {par} punti "
        f"(il \"par\"): conta battere il par, non fare {2 * n}.",
    ], width=CW * 0.5 - 4 * mm)


def _pagella(verdetto, pagella, settimana_prec):
    righe = []
    if verdetto:
        t = verdetto["totale"]
        dir_ok = t["direzione"]
        righe.append(f"Settimana {settimana_prec}: <b>{t['punti']} punti su {t['su']}</b> (par {num(t['par'], 1)}); "
                     f"direzione {dir_ok} su {t['su'] // 2}, range {t['range']} su {t['su'] // 2}.")
        note = [r["nota"] for r in verdetto["righe"].values() if r.get("nota")]
        righe += [f"Nota: {n}." for n in sorted(set(note))]
    else:
        righe.append("Prima settimana del metodo nuovo: il primo verdetto arriva lunedì prossimo.")
    if pagella and pagella.get("settimane"):
        righe.append(f"Stagione: {pagella['punti']} punti su {pagella['su']} in {pagella['settimane']} settimane "
                     f"(par {num(pagella['par'], 1)}); chiusure dentro il range: {num(pagella['copertura_range_%'], 0)}% "
                     f"(atteso circa 68%).")
    return box("La pagella", righe, width=CW * 0.5)


def pct(p):
    return f"{round(100 * p)}%"


def _domanda(dom=None, prec=None, finora=None):
    """Riquadro della domanda della settimana: la domanda con la nostra probabilità e quella di riferimento;
    il lunedì anche l'esito della domanda precedente; in settimana a che punto siamo."""
    righe = []
    if prec and prec.get("esito"):
        righe.append(f"Settimana scorsa: \"{esc(prec['testo'])}\" <b>{prec['esito']}</b>"
                     + (f" ({esc(str(prec.get('fonte_esito', '')))})" if prec.get("fonte_esito") else "")
                     + f": avevamo detto {pct(prec['prob_redazione'])}, "
                     + ("giusta." if prec.get("giusta") else "sbagliata."))
    if dom:
        righe.append(f"<b>{esc(dom['testo'])}</b> Per noi: <b>{pct(dom['prob_redazione'])}</b>; "
                     f"riferimento {pct(dom['prob_riferimento'])} ({esc(dom['fonte_riferimento'])}). "
                     f"{esc(dom['motivo'])} Si decide con: {esc(dom['fonte_risoluzione'])}.")
        if finora:
            righe.append(f"Finora: <b>{finora['finora']}</b> (ultimo {esc(str(finora.get('ultimo', '')))} "
                         f"del {esc(str(finora.get('data', '')))}, soglia {esc(str(finora.get('soglia', '')))}).")
    return [box("La domanda della settimana", righe, width=CW), Spacer(1, 4)] if righe else []


def pagina6_lunedi(reg, verdetto, pagella, tesi, grafico="c_forecast.png", settimana_prec=None, domanda=None,
                   domanda_prec=None):
    st = reg["strumenti"]
    ven = reg["settimana"].split("/")[1]
    out = section(f"La scommessa della settimana: dove chiudiamo venerdì {gg_mese(ven)}", "Il gran finale  |  Forecast")
    out += [P(f"<b>La nostra tesi:</b> {esc(tesi)}", "dek"), img(grafico, CW), Spacer(1, 3)]
    rows = [headers("Strumento", f"Chiusura {gg_mese(reg['origine'])}", f"Previsione {gg_mese(ven)}", "Range atteso",
                    "Prob. rialzo*", "Il perché")]
    for k in ordine(st):
        v = st[k]
        p = round(100 * v["prob_rialzo_redazione"])
        rows.append([P(esc(v["nome"]), "cellb"), P(liv(k, v["base"]), "celln"), P(liv(k, v["previsione_redazione"]), "cellb"),
                     P(f"{liv(k, v['range'][0])} - {liv(k, v['range'][1])}", "celln"),
                     P(f"{p}%" + (" (rend.)" if k.startswith("ust") else ""), "celln"),
                     P(esc(v.get("motivo_redazione", "")), "celln")])
    out += [tbl(rows, [27 * mm, 21 * mm, 22 * mm, 30 * mm, 18 * mm, CW - 118 * mm]), Spacer(1, 2),
            P("* Probabilità che venerdì la chiusura sia sopra quella di partenza, implicita nella nostra previsione "
              "(per i Treasury: rialzo del rendimento). Il modello da solo non vede né rialzo né ribasso: la direzione è "
              "la nostra scommessa, il range è il modello (volatilità delle ultime 20 sedute). Metodo e risultati storici "
              "nella scheda del progetto.", "note"), Spacer(1, 4)]
    out += _domanda(domanda, domanda_prec)
    out.append(side_by_side([_regole(ordine(st))], [_pagella(verdetto, pagella, settimana_prec)], CW * 0.5))
    return out


def pagina6_settimana(reg, stato, tesi, grafico="c_forecast.png", venerdi=False, domanda=None, domanda_stato=None):
    st, sr = reg["strumenti"], stato["righe"]
    ven = reg["settimana"].split("/")[1]
    out = section("La scommessa della settimana: a che punto siamo", "Il gran finale  |  Forecast")
    out += [P(f"<b>Il punto:</b> {esc(tesi)}", "dek"), img(grafico, CW), Spacer(1, 3)]
    rows = [headers("Strumento", "Base", "Previsione", "Ultimo", "Var. da base", "Dentro il range?", "On track?")]
    for k in ordine(st):
        v, r = st[k], sr[k]
        var = f"{num(r['var'], 2) if r['var_unita'] == '%' else num(r['var'], 0)}"
        var = ("+" if r["var"] > 0 else "") + var + (" %" if r["var_unita"] == "%" else " pb")
        strada = "-" if r["strada_giusta"] is None else ("Sì" if r["strada_giusta"] else "No")
        rows.append([P(esc(v["nome"]), "cellb"), P(liv(k, v["base"]), "celln"), P(liv(k, v["previsione_redazione"]), "celln"),
                     P(f"{liv(k, r['ultimo'])} <font size=6>({r['data']})</font>", "celln"),
                     P(var if abs(r["var"]) > 1e-12 else "0 pb" if r["var_unita"] == "pb" else "0,00 %", "cell"),
                     P("Sì" if r["dentro_range"] else "No", "celln"), P(strada, "celln")])
    out += [tbl(rows, [27 * mm, 22 * mm, 22 * mm, 33 * mm, 22 * mm, 23 * mm, CW - 149 * mm]), Spacer(1, 2),
            P(f"La previsione non cambia fino a venerdì {gg_mese(ven)}. \"-\": strumento fermo alla chiusura di partenza.",
              "note"), Spacer(1, 4)]
    n = len(ordine(st))
    righe = [f"Dentro il range oggi: {sum(r['dentro_range'] for r in sr.values())} su {n}.",
             f"On track (direzione giusta) oggi: {sum(1 for r in sr.values() if r['strada_giusta'])} su {n}"
             + (": " + ", ".join(esc(st[k]["nome"]) for k in ordine(st) if sr[k]["strada_giusta"]) + "."
                if any(r["strada_giusta"] for r in sr.values()) else ".")]
    if venerdi:
        righe.append("Verdetto lunedì, con le chiusure di stasera.")
    out += _domanda(domanda, None, domanda_stato)
    out.append(side_by_side([_regole(ordine(st), compatto=True)], [box("A che punto siamo", righe, width=CW * 0.5)], CW * 0.5))
    return out
