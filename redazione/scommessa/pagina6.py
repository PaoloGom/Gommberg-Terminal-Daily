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
    """Gli strumenti del registro: i fissi nell'ordine di sempre, poi lo strumento della settimana."""
    return [k for k in ORDINE if k in st] + [k for k in st if st[k].get("variabile")]


def fissi(st):
    return [k for k in ordine(st) if not st[k].get("variabile")]


def nome(v):
    return ("Della settimana: " if v.get("variabile") else "") + v["nome"]


def _par(chiavi):
    """Punteggio atteso senza abilità: 0,68 per il range più la quota di direzione di metodo.json."""
    import json as _j, os as _o
    pd_ = _j.load(open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "metodo.json"), encoding="utf-8"))["par_direzione"]
    return sum(0.68 + pd_.get(k, 0.5) for k in chiavi)


def num(v, d):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def liv(k, v, unita=None):
    s = num(v, DEC.get(k, 2))
    if unita is not None:   # lo strumento della settimana porta la sua unità
        return s + ("%" if unita == "%" else f" {unita}" if unita in ("$", "€") else "")
    return s + " $" if k in ("acwi", "brent") else s + "%" if k.startswith("ust") else s


def gg_mese(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {MESI[d.month - 1]}"


def _regole(chiavi, compatto=False, variabile=False):
    n, par = len(chiavi), num(_par(chiavi), 1)
    piu = " più lo strumento della settimana (conto a parte)" if variabile else ""
    if compatto:   # mar-ven: 1-2 righe; le regole complete escono il lunedì
        return box("Le regole del gioco", [
            f"Direzione fissata lunedì per {n} mercati{piu}: 1 punto per la direzione, 1 per la chiusura di venerdì nel range "
            f"(massimo {2 * n}, par circa {par}). Regole complete il lunedì."], width=CW * 0.5 - 4 * mm)
    return box("Le regole del gioco", [
        f"Ogni lunedì scegliamo una direzione per {n} mercati{piu}; la previsione non cambia fino a venerdì.",
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
        vv = t.get("variabile")
        if vv:
            righe.append(f"Lo strumento della settimana, {esc(vv['nome'])}: <b>{vv['punti']} punti su 2</b>.")
    else:
        righe.append("Prima settimana del metodo nuovo: il primo verdetto arriva lunedì prossimo.")
    pv = (pagella or {}).get("variabile") or {}
    if pv.get("settimane"):
        righe.append(f"Strumenti della settimana: {pv['punti']} punti su {pv['su']} in {pv['settimane']} settimane "
                     f"(par {num(pv['par'], 1)}).")
    if pagella and pagella.get("settimane"):
        righe.append(f"Stagione: {pagella['punti']} punti su {pagella['su']} in {pagella['settimane']} settimane "
                     f"(par {num(pagella['par'], 1)}); chiusure dentro il range: {num(pagella['copertura_range_%'], 0)}% "
                     f"(atteso circa 68%).")
    return box("La pagella", righe, width=CW * 0.5)


def pagina6_lunedi(reg, verdetto, pagella, tesi, grafico="c_forecast.png", settimana_prec=None):
    st = reg["strumenti"]
    ven = reg["settimana"].split("/")[1]
    out = section(f"La scommessa della settimana: dove chiudiamo venerdì {gg_mese(ven)}", "Il gran finale  |  Forecast")
    out += [P(f"<b>La nostra tesi:</b> {esc(tesi)}", "dek"), img(grafico, CW), Spacer(1, 3)]
    rows = [headers("Strumento", f"Chiusura {gg_mese(reg['origine'])}", f"Previsione {gg_mese(ven)}", "Range atteso",
                    "Prob. rialzo*", "Il perché")]
    for k in ordine(st):
        v = st[k]
        p = round(100 * v["prob_rialzo_redazione"])
        u = v.get("unita") if v.get("variabile") else None
        rows.append([P(esc(nome(v)), "cellb"), P(liv(k, v["base"], u), "celln"), P(liv(k, v["previsione_redazione"], u), "cellb"),
                     P(f"{liv(k, v['range'][0], u)} - {liv(k, v['range'][1], u)}", "celln"),
                     P(f"{p}%" + (" (rend.)" if k.startswith("ust") else ""), "celln"),
                     P(esc((v.get("motivo_scelta", "") + " ") if v.get("variabile") else "") + esc(v.get("motivo_redazione", "")), "celln")])
    out += [tbl(rows, [27 * mm, 21 * mm, 22 * mm, 30 * mm, 18 * mm, CW - 118 * mm]), Spacer(1, 2),
            P("* Probabilità che venerdì la chiusura sia sopra quella di partenza, implicita nella nostra previsione "
              "(per i Treasury: rialzo del rendimento). Il modello da solo non vede né rialzo né ribasso: la direzione è "
              "la nostra scommessa, il range è il modello (volatilità delle ultime 20 sedute). Metodo e risultati storici "
              "nella scheda del progetto.", "note"), Spacer(1, 4)]
    out.append(side_by_side([_regole(fissi(st), variabile=len(fissi(st)) < len(ordine(st)))], [_pagella(verdetto, pagella, settimana_prec)], CW * 0.5))
    return out


def pagina6_settimana(reg, stato, tesi, grafico="c_forecast.png", venerdi=False):
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
        u = v.get("unita") if v.get("variabile") else None
        rows.append([P(esc(nome(v)), "cellb"), P(liv(k, v["base"], u), "celln"), P(liv(k, v["previsione_redazione"], u), "celln"),
                     P(f"{liv(k, r['ultimo'], u)} <font size=6>({r['data']})</font>", "celln"),
                     P(var if abs(r["var"]) > 1e-12 else "0 pb" if r["var_unita"] == "pb" else "0,00 %", "cell"),
                     P("Sì" if r["dentro_range"] else "No", "celln"), P(strada, "celln")])
    out += [tbl(rows, [27 * mm, 22 * mm, 22 * mm, 33 * mm, 22 * mm, 23 * mm, CW - 149 * mm]), Spacer(1, 2),
            P(f"La previsione non cambia fino a venerdì {gg_mese(ven)}. \"-\": strumento fermo alla chiusura di partenza.",
              "note"), Spacer(1, 4)]
    fx = fissi(st); n = len(fx)
    righe = [f"Dentro il range oggi: {sum(sr[k]['dentro_range'] for k in fx)} su {n}.",
             f"On track (direzione giusta) oggi: {sum(1 for k in fx if sr[k]['strada_giusta'])} su {n}"
             + (": " + ", ".join(esc(st[k]["nome"]) for k in fx if sr[k]["strada_giusta"]) + "."
                if any(sr[k]["strada_giusta"] for k in fx) else ".")]
    for k in ordine(st):
        if st[k].get("variabile"):
            r = sr[k]
            righe.append(f"Della settimana, {esc(st[k]['nome'])}: " + ("dentro il range" if r["dentro_range"] else "fuori dal range")
                         + (", on track." if r["strada_giusta"] else "." if r["strada_giusta"] is None else ", direzione contraria."))
    if venerdi:
        righe.append("Verdetto lunedì, con le chiusure di stasera.")
    out.append(side_by_side([_regole(fissi(st), compatto=True, variabile=len(fissi(st)) < len(ordine(st)))], [box("A che punto siamo", righe, width=CW * 0.5)], CW * 0.5))
    return out
