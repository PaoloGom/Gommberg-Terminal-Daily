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


def attesi(s):
    (_, v0, _), (_, v1, _) = s["ultimi"][0], s["ultimi"][1]
    t = N.tipo_var(s)
    d = (v0 - v1) * 100 if t == "pb" else (v0 - v1) if t == "punti" else (v0 / v1 - 1) * 100
    return v0, d


def main():
    pdf, dati = sys.argv[1], sys.argv[2]
    S = json.load(open(dati, encoding="utf-8"))["serie"]
    testo = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True).stdout.decode("utf-8", "replace")
    righe = [" ".join(r.split()) for r in testo.split("\n")]
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
        for et in s.get("etichette", []):
            idx = [i for i, r in enumerate(righe) if r == et or r.startswith(et + " ") or re.search(rf"(^| ){re.escape(et)} \d", r)]
            if not idx:
                avvisi.append(f"{et}: riga non trovata nel PDF"); continue
            v0, d = attesi(s)
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
    print(f"Numeri confrontati con dati.json: {n} | scarti: {len(errori)}")
    for a in avvisi[:3]:
        print("AVVISO: " + a)
    for e in errori[:6]:
        print("ERRORE: " + e)
    sys.exit(1 if errori else 0)


if __name__ == "__main__":
    main()
