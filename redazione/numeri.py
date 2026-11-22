"""Numeri di mercato dal dati.json del giorno (schema di controlli_dati.py): niente cifre scritte a mano.
- ticker_da_dati(path): le 7 caselle del ticker, con livelli e variazioni del giorno calcolati qui.
- fmt(v, dec), var(v0, v1, tipo, dec): formattazione all'italiana con segno esplicito.
Ogni serie di dati.json che entra nel PDF può avere "etichette": [nomi come compaiono nelle tabelle] e "tipo_var":
"pct" (prezzi, default), "pb" (rendimenti, livello in %), "punti" (VIX). controlli_numeri.py li confronta col PDF."""
import json

# (etichetta nel ticker, serie in dati.json, decimali del livello, unità del livello)
TICKER = [("MSCI ACWI (ETF)", "ACWI", 2, " $"), ("S&amp;P 500", "S&P 500", 2, ""), ("EURO STOXX 50", "Euro Stoxx 50", 2, ""),
          ("TREASURY 10 ANNI", "Treasury 10 anni", 2, "%"), ("EUR/USD", "EUR/USD", 4, ""),
          ("BRENT FUTURE", "Brent future", 2, " $"), ("ORO", ("Oro future", "Oro"), 0, " $")]
# Il nastro è il mondo più i sei mercati della scommessa, nello stesso ordine (14/11/2026): l'oro al posto del VIX, perché
# il lettore deve poter seguire in prima pagina ciò su cui scommettiamo. L'oro è il future (GCUSD), lo stesso della
# scommessa. Il VIX resta nella tabella dei mercati di pag. 5.


def fmt(v, dec=2):
    s = f"{abs(v):,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-" if v < 0 else "") + s


def var(v0, v1, tipo="pct", dec=1):
    if tipo == "pb":
        x, u, dec = round((v0 - v1) * 100), " pb", 0
    elif tipo == "punti":
        x, u = v0 - v1, ""
    else:
        x, u = (v0 / v1 - 1) * 100, "%"
    x = round(x, dec)
    return ("+" if x > 0 else "") + (fmt(x, dec) if x != 0 else fmt(0, dec)) + u


def tipo_var(s):
    return s.get("tipo_var") or ("pb" if s.get("mercato") == "UST" else "pct")


def ticker_da_dati(path="dati.json"):
    S = json.load(open(path, encoding="utf-8"))["serie"]
    out = []
    for et, nome, dec, unita in TICKER:
        nomi = nome if isinstance(nome, tuple) else (nome,)
        trovato = next((x for x in nomi if x in S), None)
        if trovato is None:
            raise KeyError(f"dati.json: manca la serie '{nomi[0]}' (serve al nastro di prima pagina)")
        s = S[trovato]
        (_, v0, _), (_, v1, _) = s["ultimi"][0], s["ultimi"][1]
        t = tipo_var(s)
        out.append((et, fmt(v0, dec) + unita, var(v0, v1, t, 2 if t == "punti" else 1) + " g"))
    return out


# ---------------------------------------------------------------- tabelle dei mercati di pag. 5: le calcola il codice
# Fino al 20/11/2026 le celle le scriveva la redazione a mano e, dove non aveva sotto mano la chiusura di una settimana
# prima o quella di fine anno, usciva "n.d." (o "-"), anche per dati che il kit aveva già. Ora la redazione scrive solo le
# serie in dati.json; livelli, variazioni, date e note escono da qui. I riferimenti (una settimana fa, un mese fa, fine anno)
# vengono dall'archivio delle chiusure, che pubblica.sh allunga a ogni edizione: un dato si cerca una volta sola.
import csv as _csv
import datetime as _dt
import os as _os
import sys as _sys

_QUI = _os.path.dirname(_os.path.abspath(__file__))
ARCHIVIO = _os.path.join(_QUI, "chiusure.csv")          # serie,data,valore
# le serie che hanno già il loro archivio giornaliero nella scommessa (scommessa_giorno.sh lo aggiorna)
SCOMMESSA = {"S&P 500": "spx", "Euro Stoxx 50": "sx5e", "Treasury 10 anni": "ust10", "Treasury 2 anni": "ust2",
             "EUR/USD": "eurusd", "Brent future": "brent", "Oro future": "oro", "Oro": "oro", "ACWI": "acwi", "VIX": "vix"}
# righe fisse: (etichetta nel PDF, serie in dati.json, decimali del livello, unità). Un indice in più entra solo il giorno
# in cui fa notizia: la sua serie porta "tabella": "<nome del gruppo>" e "etichette": ["<nome della riga>"].
CRUSCOTTO = [("Mondo e Stati Uniti", [("MSCI ACWI (ETF, $)", "ACWI", 2, ""), ("S&amp;P 500", "S&P 500", 2, ""),
                                      ("Nasdaq Comp.", "Nasdaq", 2, ""), ("Russell 2000", "Russell 2000", 2, "")]),
             ("Europa", [("Euro Stoxx 50", "Euro Stoxx 50", 2, ""), ("FTSE MIB", "FTSE MIB", 0, "")]),
             ("Asia", [("Nikkei 225", "Nikkei 225", 2, ""), ("Hang Seng", "Hang Seng", 2, ""), ("Kospi", "Kospi", 2, "")])]
CROSS = [("Tassi", [("Treasury 2 anni", "Treasury 2 anni", 2, "%"), ("Treasury 10 anni", "Treasury 10 anni", 2, "%"),
                    ("Spread Italia", "Spread Italia", 0, " pb")]),
         ("Cambi", [("EUR/USD", "EUR/USD", 4, "")]),
         ("Materie prime", [("Brent future", "Brent future", 2, " $"), ("Oro (future, $/oncia)", ("Oro future", "Oro"), 2, "")]),
         ("Volatilità", [("VIX (volatilità attesa)", "VIX", 2, "")])]
GIORNI_IT = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]


def righe_fisse():
    """Le serie che dati.json deve avere perché le tabelle di pag. 5 siano complete: {serie: etichetta}."""
    out = {}
    for _, righe in CRUSCOTTO + CROSS:
        for et, nome, _, _ in righe:
            out[nome[0] if isinstance(nome, tuple) else nome] = et.replace("&amp;", "&")
    return out


def tipo_riga(nome, s):
    """Come si legge la variazione: lo spread è un livello in punti base, e la sua variazione è una differenza."""
    return s.get("tipo_var") or {"Spread Italia": "spread", "VIX": "punti"}.get(nome) or tipo_var(s)


def _var(v0, v1, tipo, dec=1):
    if tipo == "spread":
        x = round(v0 - v1)
        return ("+" if x > 0 else "") + fmt(x, 0) + " pb"
    return var(v0, v1, tipo, 2 if tipo == "punti" else dec)


def _archivio(percorso=None):
    out = {}
    p = percorso or ARCHIVIO
    if _os.path.exists(p):
        for r in _csv.DictReader(open(p, encoding="utf-8")):
            try:
                out.setdefault(r["serie"], {})[r["data"]] = float(r["valore"])
            except (KeyError, ValueError, TypeError):
                continue
    return out


def storia(nome, s=None, archivio=None):
    """Le chiusure note di una serie, {data: valore}: archivio della scommessa, archivio delle chiusure, "rif" e "ultimi"
    di dati.json (nell'ordine: ciò che viene dopo vince). Il dato di stamattina di una seduta in corso non è una chiusura,
    ma resta qui perché è il livello della riga: chi cerca un riferimento chiede sempre una data precedente."""
    out = {}
    k = SCOMMESSA.get(nome)
    p = _os.path.join(_QUI, "scommessa", "dati", f"{k}.csv") if k else None
    if p and _os.path.exists(p):
        for r in list(_csv.reader(open(p, encoding="utf-8")))[1:]:
            try:
                out[r[0]] = float(r[1])
            except (IndexError, ValueError):
                continue
    out.update((archivio if archivio is not None else _archivio()).get(nome, {}))
    for d, v in ((s or {}).get("rif") or {}).items():
        if isinstance(v, (int, float)):
            out[str(d)[:10]] = float(v)
    for r in (s or {}).get("ultimi") or []:
        if len(r) >= 2 and isinstance(r[1], (int, float)):
            out[str(r[0])[:10]] = float(r[1])
    return out


def _ieri(d):
    """Il giorno feriale prima di d (AAAA-MM-GG): la seduta precedente, salvo festività."""
    x = _dt.date.fromisoformat(str(d)[:10]) - _dt.timedelta(days=1)
    while x.weekday() > 4:
        x -= _dt.timedelta(days=1)
    return x.isoformat()


def completa(nome, s, archivio=None):
    """"ultimi" con almeno due chiusure quando l'archivio conosce quella della seduta prima: per FTSE MIB, spread e le
    altre serie prese dal web basta scrivere l'ultima chiusura. Vale solo la seduta subito precedente (il giorno feriale
    prima): con una chiusura più vecchia la variazione di un giorno sarebbe sbagliata."""
    u = [list(r) for r in (s.get("ultimi") or [])]
    if len(u) == 1:
        st = storia(nome, s, archivio)
        ieri = _ieri(u[0][0])
        if ieri in st:
            u.append([ieri, st[ieri], None])
    return u


def ricavato(nome, s, oggi, archivio=None):
    """Seduta asiatica di stamattina di cui si conosce solo la variazione ("var", con fonte e ora): il livello si ricava
    dalla chiusura di ieri, se c'è (in "ultimi" o in archivio). Torna (chiusura di ieri, livello ricavato) o None."""
    if s.get("tipo") != "intraday" or not isinstance(s.get("var"), (int, float)):
        return None
    u = s.get("ultimi") or []
    if u and str(u[0][0])[:10] >= str(oggi)[:10]:
        return None                                   # il livello di stamattina c'è: niente da ricavare
    ieri = _ieri(oggi)
    base = storia(nome, s, archivio).get(ieri)
    return (base, base * (1 + s["var"] / 100)) if base else None


def _entro(st, data, giorni=4):
    """La chiusura alla data, o l'ultima nei giorni appena prima (festività): (data, valore) o None."""
    for d in sorted(st, reverse=True):
        if d <= data:
            return (d, st[d]) if (_dt.date.fromisoformat(data) - _dt.date.fromisoformat(d)).days <= giorni else None
    return None


def _gm(d):
    x = _dt.date.fromisoformat(str(d)[:10])
    return f"{x.day}/{x.month}"


def _al(prep, d):
    """ "sul 19/10", "sull'11/9", "al 26/11", "all'8/12": la preposizione articolata davanti a una data (prep = "su" o "a")."""
    x = _dt.date.fromisoformat(str(d)[:10])
    return prep + ("ll'" if x.day in (1, 8, 11) else "l ") + _gm(d)


def _piu_usato(date):
    """La data più frequente; a parità la più recente (così è la riga rimasta indietro a essere detta a parte)."""
    conta = {}
    for d in date:
        conta[d] = conta.get(d, 0) + 1
    return max(conta, key=lambda d: (conta[d], d)) if conta else None


def _elenco(nomi):
    return nomi[0] if len(nomi) == 1 else ", ".join(nomi[:-1]) + " e " + nomi[-1]


def _nome(et):
    """Il nome di una riga dentro una nota: senza la precisazione tra parentesi."""
    return et.split(" (")[0]


def tabelle_da_dati(path="dati.json", archivio=None, silenzioso=False):
    """Le due tabelle di pag. 5 e le loro note, dal dati.json del giorno: {"cruscotto", "cruscotto_nota", "cross_data",
    "cross", "cross_nota", "mancanti"}. Una riga senza livello verificato non entra in tabella (mai "n.d."); un
    riferimento che l'archivio non ha ancora esce "-" e finisce in "mancanti", con la data da cercare una volta sola
    (in dati.json, nella serie: "rif": {"AAAA-MM-GG": valore}).
    Le date. Ogni riga ha la data del suo livello e, per ogni riferimento, la data della chiusura davvero usata: con un
    mercato chiuso le righe non hanno tutte la stessa. Intestazioni e note si scrivono da lì, senza supporre quale mercato
    è avanti o indietro: la data sta nel punto più alto in cui vale per tutti. La data più usata dalle righe delle due
    tabelle va nell'intestazione ("Livello GG/MM"); un gruppo che ne ha un'altra la porta nel titolo; una riga che non ha
    quella del suo gruppo è detta nella nota. Lo stesso per i riferimenti: la data più usata dalle righe dell'intestazione,
    e tra parentesi chi ne usa un'altra (un gruppo intero con il suo nome, altrimenti le righe)."""
    D = json.load(open(path, encoding="utf-8"))
    S = D["serie"]
    arch = archivio if archivio is not None else _archivio()
    mancanti = []

    # I riferimenti sono gli stessi ogni giorno: una settimana = la stessa seduta della settimana prima (il lunedì, con le
    # chiusure di venerdì, è la settimana intera); un mese = lo stesso giorno del mese prima. Se quel giorno era chiuso
    # vale l'ultima chiusura prima. Ogni riga parte dalla data del suo livello.
    def sett_prima(d):
        return (_dt.date.fromisoformat(d) - _dt.timedelta(days=7)).isoformat()

    def mese_prima(d):
        x = _dt.date.fromisoformat(d)
        m, a = (x.month - 1) or 12, x.year - (x.month == 1)
        return _dt.date(a, m, min(x.day, [31, 29 if a % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])).isoformat()
    asia_ora, ricavati = [], []

    def riga(et, nome, dec, unita, terza):
        nomi = nome if isinstance(nome, tuple) else (nome,)
        n = next((x for x in nomi if x in S), None)
        s = S.get(n) if n else None
        ric = ricavato(n, s, D["oggi"], arch) if s else None
        solo_var = bool(s) and s.get("tipo") == "intraday" and isinstance(s.get("var"), (int, float)) and not ric \
            and str((s.get("ultimi") or [["0"]])[0][0])[:10] < D["oggi"]      # stamattina c'è la variazione ma non il livello
        if not s or not (s.get("ultimi") or ric) or solo_var:
            perche = (f"c'è solo la variazione di stamattina e manca la chiusura di ieri ({_gm(_ieri(D['oggi']))}): aggiungila in "
                      "\"ultimi\"" if solo_var else "nessun livello in dati.json")
            mancanti.append(f"{et.replace('&amp;', '&')}: {perche}, la riga non entra in tabella")
            return None
        st = storia(n, s, arch)
        t = tipo_riga(n, s)
        intraday = s.get("tipo") == "intraday"
        if intraday and s.get("ora"):
            asia_ora.append(s["ora"])
        if ric:                                        # livello ricavato dalla variazione: segnato con ~, senza decimali
            d0, v0 = D["oggi"], ric[1]
            g1 = ("+" if s["var"] > 0 else "") + fmt(s["var"], 1) + "%"
            ricavati.append(et)
        else:
            d0, v0 = str(s["ultimi"][0][0])[:10], float(s["ultimi"][0][1])
            u = completa(n, s, arch)
            if len(u) >= 2:
                g1 = _var(v0, float(u[1][1]), t)
            elif isinstance(s.get("var"), (int, float)):
                g1 = ("+" if s["var"] > 0 else "") + fmt(s["var"], 1) + "%"
            else:
                g1 = "-"; mancanti.append(f"{et}: manca la chiusura precedente, del {_gm(_ieri(d0))} (1 g)")
        celle, usate = [], {}                          # usate: la chiusura davvero usata per ogni riferimento
        for che, quando, giorni in (("1 sett.", sett_prima(d0), 4), (terza, mese_prima(d0), 6)):
            if che == "anno":
                base = max((d for d in st if d[:4] < d0[:4] and d >= f"{int(d0[:4]) - 1}-12-20"), default=None)
                x = (base, st[base]) if base else None
                quando = f"{int(d0[:4]) - 1}-12-31"
            else:
                x = _entro(st, quando, giorni)
            if x and x[0] < d0:
                celle.append(_var(v0, x[1], t))
                usate[che] = x[0][:4] if che == "anno" else x[0]     # per l'anno conta di quale anno è la chiusura
            else:
                celle.append("-")
                mancanti.append(f"{et.replace('&amp;', '&')}: manca la chiusura del {_gm(quando)} ({'da inizio anno' if che == 'anno' else che})")
        livello = "~" + fmt(round(v0), 0) if ric else fmt(v0, dec) + unita
        return {"et": et, "data": d0, "usate": usate, "celle": [et + ("*" if intraday else ""), livello, _gm(d0), g1] + celle}

    def gruppi(spec, terza):                            # terza = che cosa c'è nella terza colonna: "anno" o "1 mese"
        out = []
        for titolo, righe in spec:
            rr = [r for r in (riga(et, nome, dec, un, terza) for et, nome, dec, un in righe) if r]
            for n, s in S.items():                          # un indice in più, il giorno in cui fa notizia
                if s.get("tabella") == titolo and n not in righe_fisse():
                    r = riga((s.get("etichette") or [n])[0], n, s.get("decimali", 2), s.get("unita", ""), terza)
                    rr += [r] if r else []
            if rr:
                out.append((titolo, rr))
        return out

    sx, dx = gruppi(CRUSCOTTO, "anno"), gruppi(CROSS, "1 mese")
    rif = _piu_usato([r["data"] for _, rr in sx + dx for r in rr]) or str(D["oggi"])[:10]

    def con_le_date(gr, taglia):
        """Titoli e righe come li impagina il motore, più la frase per le righe con una data diversa dal loro gruppo."""
        tab, fuori = [], {}
        for titolo, rr in gr:
            del_gruppo = _piu_usato([r["data"] for r in rr])
            for r in rr:
                if r["data"] != del_gruppo:
                    fuori.setdefault(r["data"], []).append(_nome(r["et"]))
            tab.append((titolo + (f" ({_gm(del_gruppo)})" if del_gruppo != rif else ""), [taglia(r["celle"]) for r in rr]))
        return tab, "".join(f" {_elenco(nomi)} {_al('a', d)}." for d, nomi in sorted(fuori.items()))

    def riferimento(che, gr, forma, attesa):
        """ "su giovedì 12/11 (Asia su venerdì 13/11)": la data più usata e, tra parentesi, chi ne ha usata un'altra."""
        tutte = [r for _, rr in gr for r in rr if che in r["usate"]]
        base = _piu_usato([r["usate"][che] for r in tutte if r["data"] == rif] or [r["usate"][che] for r in tutte])
        altre = {}
        for titolo, rr in gr:
            con = [r for r in rr if che in r["usate"]]
            for d in dict.fromkeys(r["usate"][che] for r in con):
                quali = [r for r in con if r["usate"][che] == d]
                if d != base:
                    altre.setdefault(d, []).extend([titolo] if len(quali) == len(con) > 1 else [_nome(r["et"]) for r in quali])
        return forma(base or attesa) + (" (" + "; ".join(f"{_elenco(nomi)} {forma(d)}" for d, nomi in sorted(altre.items())) + ")"
                                        if altre else "")

    cruscotto, fuori_sx = con_le_date(sx, lambda c: c)
    cross, fuori_dx = con_le_date(dx, lambda c: [c[0], c[1], c[3], c[4], c[5], "-"])
    asia = any(c[0].endswith("*") for _, rr in cruscotto for c in rr)
    il_giorno = lambda d: f"su {GIORNI_IT[_dt.date.fromisoformat(d).weekday()]} {_gm(d)}"
    nota = (f"1 g = chiusura su chiusura; 1 sett. = {riferimento('1 sett.', sx + dx, il_giorno, sett_prima(rif))}"
            f"; da inizio anno = {riferimento('anno', sx, lambda a: 'su chiusura ' + a, str(int(rif[:4]) - 1))}.")
    if asia:
        nota += " * Asia: dato di stamattina" + (f" (alle {max(asia_ora)})" if asia_ora else "") + "."
    if ricavati:
        nota += " ~ = livello ricavato dalla variazione di stamattina."
    if mancanti and not silenzioso:
        print("TABELLE DI PAG. 5: " + "; ".join(mancanti[:8]) + ". Una chiusura che manca si cerca una volta (APP_DATI §3) e "
              "si scrive in dati.json nella serie: \"rif\": {\"AAAA-MM-GG\": valore}", file=_sys.stderr)
    return {"cruscotto": cruscotto, "cruscotto_nota": nota + fuori_sx, "cross_data": f"Livello {_gm(rif)}", "cross": cross,
            "cross_nota": f"1 mese = {riferimento('1 mese', dx, lambda d: _al('su', d), mese_prima(rif))}.{fuori_dx}"
                          " VIX = volatilità attesa sull'S&amp;P 500.",
            "mancanti": mancanti}


def archivia(path, percorso=None):
    """Aggiunge all'archivio le chiusure del dati.json del giorno che non ha ancora (pubblica.sh, a ogni edizione): solo
    le serie senza un archivio loro nella scommessa, mai il dato di stamattina di una seduta in corso. Torna quante."""
    D = json.load(open(path, encoding="utf-8"))
    p = percorso or ARCHIVIO
    arch = _archivio(p)
    nuove = 0
    for nome, s in D.get("serie", {}).items():
        if nome in SCOMMESSA:
            continue
        righe = [(str(r[0])[:10], r[1]) for r in s.get("ultimi") or [] if len(r) >= 2] + list((s.get("rif") or {}).items())
        for d, v in righe:
            if not isinstance(v, (int, float)) or (s.get("tipo") == "intraday" and d >= D.get("oggi", "9999")):
                continue
            if d not in arch.setdefault(nome, {}):
                arch[nome][d] = float(v); nuove += 1
    if nuove:
        with open(p, "w", encoding="utf-8", newline="") as f:
            w = _csv.writer(f, lineterminator="\n")
            w.writerow(["serie", "data", "valore"])
            for nome in sorted(arch):
                for d in sorted(arch[nome]):
                    w.writerow([nome, d, repr(arch[nome][d]) if arch[nome][d] != int(arch[nome][d]) else int(arch[nome][d])])
    return nuove


if __name__ == "__main__":
    if len(_sys.argv) >= 3 and _sys.argv[1] == "--archivia":
        print(f"Archivio delle chiusure: {archivia(_sys.argv[2], _sys.argv[3] if len(_sys.argv) > 3 else None)} nuove")
    elif len(_sys.argv) >= 2:
        T = tabelle_da_dati(_sys.argv[-1])
        for k in ("cruscotto", "cross"):
            for titolo, righe in T[k]:
                print(titolo)
                for r in righe:
                    print("   " + " | ".join(r))
        print(T["cruscotto_nota"]); print(T["cross_data"], "-", T["cross_nota"])
