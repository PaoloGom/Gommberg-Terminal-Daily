"""Controllo bloccante: i numeri di ticker, cruscotto e cross-asset nel PDF coincidono con dati.json?
Uso: python3 controlli_numeri.py <pdf> <dati.json>
Per ogni serie di dati.json con "etichette" (nomi delle righe nelle tabelle) cerca nel PDF la riga che inizia con
l'etichetta e confronta il livello (primo numero dopo l'etichetta) e la variazione 1 g (primo numero con segno dopo il
livello) con i valori calcolati da "ultimi". Il ticker si confronta sempre (numeri.TICKER).
Tolleranza: mezza unità dell'ultima cifra stampata (arrotondamento). Esce con 1 a ogni scarto."""
import json, os, re, subprocess, sys

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
import numeri as N  # noqa: E402

NUM = re.compile(r"(?<![\w,.])([+-]?)(\d{1,3}(?:\.\d{3})*(?:,\d+)?|\d+(?:,\d+)?)\s?(%|pb)?")


def valore(seg, s, u):
    x = float(s.replace(".", "").replace(",", "."))
    dec = len(s.split(",")[1]) if "," in s else 0
    return (-x if seg == "-" else x), 0.5 * 10 ** -dec + 1e-9


def attesi(nome, s, oggi):
    if N.ricavato(nome, s, oggi):    # livello ricavato dalla variazione (segnato ~): non è un numero di dati.json
        return None
    u = N.completa(nome, s)          # la chiusura precedente può venire dall'archivio, come nelle tabelle
    if len(u) < 2 or (isinstance(s.get("var"), (int, float)) and str(u[0][0])[:10] < oggi):
        return None
    v0, v1 = u[0][1], u[1][1]
    t = N.tipo_riga(nome, s)
    d = (v0 - v1) * 100 if t == "pb" else (v0 - v1) if t in ("punti", "spread") else (v0 / v1 - 1) * 100
    return v0, d


def main():
    pdf, dati = sys.argv[1], sys.argv[2]
    D = json.load(open(dati, encoding="utf-8"))
    S, OGGI = D["serie"], str(D.get("oggi", "9999"))
    testo = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True).stdout.decode("utf-8", "replace")
    righe = [" ".join(r.split()) for r in testo.split("\n")]
    pagine, _p = [], 1
    for r in testo.split("\n"):              # pdftotext mette un salto pagina in testa alla prima riga di ogni pagina
        _p += r.count("\f")
        pagine.append(_p)
    errori, avvisi, n = [], [], 0
    # Ticker (pag. 1): stringhe identiche a quelle calcolate
    sys.path.insert(0, QUI)
    from edizioni_voce import ticker_dal_pdf
    tk = ticker_dal_pdf(pdf) or []
    try:
        atteso = N.ticker_da_dati(dati)
    except KeyError as e:
        atteso = []; avvisi.append(f"ticker non confrontato: manca la serie {e} in dati.json")
    for (et, v, c), (et2, v2, c2) in zip(atteso, tk):
        n += 1
        if v.replace(" ", "") != v2.replace(" ", "") or c.replace(" ", "") != c2.replace(" ", ""):
            errori.append(f"ticker {et2}: PDF {v2} {c2}, dati.json {v} {c}")
    # Tabelle
    for nome, s in S.items():
        # le righe fisse delle tabelle hanno il nome che dà loro numeri.py: "etichette" serve solo per le righe in più
        fisse = N.righe_fisse()
        for et in s.get("etichette") or ([fisse[nome]] if nome in fisse else []):
            att = attesi(nome, s, OGGI)
            if att is None:
                continue                 # serie senza livello: la riga non entra in tabella
            # le tabelle stanno a pag. 5: tra le righe che portano l'etichetta e un numero vale la prima di quella pagina
            # (così "Kospi 4.968,48" in un testo di prima pagina non viene preso per la riga della tabella)
            idx = [i for i, r in enumerate(righe) if r == et or r.startswith((et + " ", et + "* "))
                   or re.search(rf"(^| ){re.escape(et)}\*? \d", r)]
            idx = [i for i in idx if pagine[i] == 5] or idx
            if not idx:
                avvisi.append(f"{et}: riga non trovata nel PDF"); continue
            v0, d = att
            i = idx[0]
            r = righe[i][righe[i].index(et) + len(et):]
            if not NUM.search(r) and i + 1 < len(righe):   # etichetta su due righe: i numeri stanno nella riga dopo
                r = righe[i + 1]
            toks = [m for m in NUM.finditer(r)]
            if not toks:
                errori.append(f"{et}: nessun numero nella riga"); continue
            n += 1
            lv, tol = valore("", toks[0].group(2), toks[0].group(3))
            if abs(lv - v0) > tol * max(1, 1):
                errori.append(f"{et}: livello {toks[0].group(0)} nel PDF, {v0} in dati.json")
            segn = [m for m in toks[1:] if m.group(1) or m.group(2) in ("0", "0,0", "0,00")]
            segn = [m for m in segn if not re.fullmatch(r"\d{1,2}/\d{1,2}", m.group(0))]
            if not segn:
                errori.append(f"{et}: variazione 1 g non trovata"); continue
            x, tol = valore(segn[0].group(1), segn[0].group(2), segn[0].group(3))
            if abs(x - d) > tol:
                errori.append(f"{et}: 1 g {segn[0].group(0)} nel PDF, {d:+.3f} da dati.json")
    # Le tabelle di pag. 5 sono quelle calcolate da numeri.py (livello, 1 g, 1 sett., da inizio anno o 1 mese): una riga
    # scritta a mano, con valori diversi o con celle vuote dove il dato c'è, si ferma qui.
    try:
        T = N.tabelle_da_dati(dati, silenzioso=True)
    except Exception as e:  # noqa: BLE001
        T = None; avvisi.append(f"tabelle di pag. 5 non ricalcolate ({type(e).__name__}): controlla le serie di dati.json")
    if T:
        piatto = lambda x: re.sub(r"\s+", "", x.replace("&amp;", "&"))
        p5 = [r for r, p in zip(righe, pagine) if p == 5]
        for calc in [(r[0], [r[1], r[3], r[4], r[5]]) for _, rr in T["cruscotto"] for r in rr] + \
                    [(r[0], r[1:5]) for _, rr in T["cross"] for r in rr]:
            et, celle = calc[0].replace("&amp;", "&"), calc[1]
            atteso = piatto(et + "".join(celle))
            n += 1
            if not any(atteso in piatto(r) for r in p5):
                errori.append(f"pag. 5, {et}: nel PDF non c'è la riga calcolata ({' | '.join(celle)}): le tabelle vengono "
                              "da TAB = tabelle_da_dati(\"dati.json\"), come nel modello, mai scritte a mano")
    print(f"Numeri confrontati con dati.json: {n} | scarti: {len(errori)}")
    for a in avvisi[:3]:
        print("AVVISO: " + a)
    for e in errori[:6]:
        print("ERRORE: " + e)
    sys.exit(1 if errori else 0)


if __name__ == "__main__":
    main()
