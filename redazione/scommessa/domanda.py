"""La domanda della settimana: una scommessa variabile sul tema caldo, con regole fissate il lunedì.

Una sola domanda sì/no, risolvibile con un dato oggettivo entro il venerdì. Due tipi:
- "mercato": una chiusura sopra o sotto una soglia ("Il Brent chiuderà venerdì sopra 110 $?"). La probabilità di
  riferimento la calcola il modello della scommessa (volatilità delle ultime 20 sedute, distribuzione normale, nessuna
  deriva): niente probabilità a occhio.
- "evento": un fatto con una fonte ufficiale di risoluzione (decisione della Fed, un dato contro le attese). La
  probabilità di riferimento va presa da una fonte di mercato con nome e data (es. CME FedWatch) o, se non esiste, 50%.
La redazione dà la sua probabilità (tra 5% e 95%, mai 50%) con un motivo scritto. Il verdetto confronta la redazione
con il riferimento: il punteggio di Brier (più basso è meglio) dice se la nostra opinione ha aggiunto qualcosa.

Uso:
  python3 domanda.py crea  --lunedi 2026-10-19 --file domanda_in.json      # scrive ../pronostici/<lunedi>-domanda.json
  python3 domanda.py stato --lunedi 2026-10-19 --valore 108.2 --data 2026-10-20   # a che punto siamo (solo "mercato")
  python3 domanda.py valuta --lunedi 2026-10-19 --esito si|no --valore 109.4 --fonte "FMP, chiusura 23/10"
domanda_in.json:
  {"tipo": "mercato", "testo": "Il Brent future chiuderà venerdì 23 ottobre sopra 110 $?", "strumento": "brent",
   "soglia": 110.0, "verso": "sopra", "base": 109.86, "data_base": "2026-10-16",
   "prob_redazione": 0.6, "motivo": "...", "fonte_risoluzione": "chiusura del Brent future (FMP) di venerdì 23 ottobre"}
  per "evento" al posto di strumento/soglia/base: "prob_riferimento": 0.47, "fonte_riferimento": "CME FedWatch, 19/10".
Il registro non si cambia in settimana (come la scommessa)."""
import argparse, datetime as dt, json, math, os, sys

QUI = os.path.dirname(os.path.abspath(__file__))
PRON = os.path.join(QUI, "..", "pronostici")
PAGELLA = os.path.join(QUI, "domande.json")


def _phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def prob_modello(strumento, soglia, verso, base, data_base):
    """P(chiusura di venerdì oltre la soglia) dal modello della scommessa (rv20, normale, deriva zero, 5 sedute)."""
    sys.path.insert(0, QUI)
    from motore import STRUMENTI, carica, variazioni_giornaliere, vol_rv
    import pandas as pd
    tipo = STRUMENTI[strumento]["tipo"] if strumento in STRUMENTI else "prezzo"
    s = carica(strumento)
    s = s[s.index <= pd.Timestamp(data_base)]
    sigma = vol_rv(variazioni_giornaliere(s, tipo))   # volatilità settimanale nelle unità della variazione
    x = math.log(soglia / base) if tipo == "prezzo" else (soglia - base) * 100
    p_sopra = 1 - _phi(x / sigma) if sigma > 0 else float(base > soglia)
    return round(p_sopra if verso == "sopra" else 1 - p_sopra, 3), sigma, tipo


def crea(lunedi, f):
    d = json.load(open(f, encoding="utf-8"))
    errori = []
    for k in ("tipo", "testo", "prob_redazione", "motivo", "fonte_risoluzione"):
        if not d.get(k):
            errori.append(f"manca '{k}'")
    p = d.get("prob_redazione") or 0
    if not (0.05 <= p <= 0.95) or abs(p - 0.5) < 0.01:
        errori.append("prob_redazione tra 0,05 e 0,95 e mai 0,5: la domanda chiede un'opinione")
    if not d.get("testo", "").rstrip().endswith("?"):
        errori.append("il testo è una domanda sì/no e finisce con '?'")
    ven = dt.date.fromisoformat(lunedi) + dt.timedelta(days=4)
    if d.get("tipo") == "mercato":
        for k in ("strumento", "soglia", "verso", "base", "data_base"):
            if d.get(k) in (None, ""):
                errori.append(f"tipo mercato: manca '{k}'")
        if not errori:
            d["prob_riferimento"], sigma, tipo = prob_modello(d["strumento"], float(d["soglia"]), d["verso"],
                                                              float(d["base"]), d["data_base"])
            d["fonte_riferimento"] = "modello della scommessa (volatilità delle ultime 20 sedute, nessuna deriva)"
            d["sigma_settimana"] = round(sigma, 6)
            if abs(d["prob_riferimento"] - 0.5) > 0.45:
                errori.append(f"domanda già decisa (modello {d['prob_riferimento']:.0%}): scegli una soglia più vicina")
    elif d.get("tipo") == "evento":
        if d.get("prob_riferimento") is None or not d.get("fonte_riferimento"):
            errori.append("tipo evento: servono prob_riferimento e fonte_riferimento (fonte di mercato con data, o 0.5 "
                          "con fonte_riferimento \"nessun prezzo di mercato\")")
        if not d.get("data_risoluzione") or not (lunedi <= d["data_risoluzione"] <= ven.isoformat()):
            errori.append(f"tipo evento: data_risoluzione dentro la settimana ({lunedi} - {ven})")
    else:
        errori.append("tipo: 'mercato' o 'evento'")
    if errori:
        raise SystemExit("ERRORE domanda: " + "; ".join(errori))
    d.update(lunedi=lunedi, venerdi=ven.isoformat())
    out = os.path.join(PRON, f"{lunedi}-domanda.json")
    if os.path.exists(out):
        raise SystemExit(f"ERRORE: {out} esiste già: la domanda non si cambia in settimana")
    json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Domanda: {d['testo']} | noi {d['prob_redazione']:.0%}, riferimento {d['prob_riferimento']:.0%} "
          f"({d['fonte_riferimento']}) -> {out}")


def carica_reg(lunedi):
    p = os.path.join(PRON, f"{lunedi}-domanda.json")
    if not os.path.exists(p):
        raise SystemExit(f"nessuna domanda per la settimana del {lunedi}")
    return json.load(open(p, encoding="utf-8")), p


def stato(lunedi, valore, data):
    d, _ = carica_reg(lunedi)
    if d["tipo"] != "mercato":
        print(json.dumps({"testo": d["testo"], "finora": None}, ensure_ascii=False)); return
    sopra = valore > d["soglia"]
    finora = sopra if d["verso"] == "sopra" else not sopra
    r = {"testo": d["testo"], "ultimo": valore, "data": data, "soglia": d["soglia"], "finora": "sì" if finora else "no",
         "prob_redazione": d["prob_redazione"]}
    print(json.dumps(r, ensure_ascii=False))


def valuta(lunedi, esito, valore, fonte):
    d, p = carica_reg(lunedi)
    if d.get("esito"):
        raise SystemExit("domanda già valutata")
    e = 1 if esito == "si" else 0
    if d["tipo"] == "mercato" and valore is not None:
        calc = (valore > d["soglia"]) if d["verso"] == "sopra" else (valore < d["soglia"])
        if int(calc) != e:
            raise SystemExit(f"ERRORE: esito '{esito}' incoerente con il valore {valore} e la soglia {d['soglia']}")
    br, brr = (d["prob_redazione"] - e) ** 2, (d["prob_riferimento"] - e) ** 2
    d.update(esito="sì" if e else "no", valore_finale=valore, fonte_esito=fonte, brier=round(br, 4),
             brier_riferimento=round(brr, 4), giusta=(d["prob_redazione"] > 0.5) == bool(e))
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    storia = json.load(open(PAGELLA, encoding="utf-8")) if os.path.exists(PAGELLA) else {"domande": []}
    storia["domande"] = [x for x in storia["domande"] if x["lunedi"] != lunedi] + [
        {k: d[k] for k in ("lunedi", "testo", "prob_redazione", "prob_riferimento", "esito", "giusta", "brier",
                           "brier_riferimento")}]
    n = len(storia["domande"])
    storia["sintesi"] = {"domande": n, "giuste": sum(x["giusta"] for x in storia["domande"]),
                         "brier": round(sum(x["brier"] for x in storia["domande"]) / n, 4),
                         "brier_riferimento": round(sum(x["brier_riferimento"] for x in storia["domande"]) / n, 4)}
    json.dump(storia, open(PAGELLA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    s = storia["sintesi"]
    print(f"Esito: {d['esito']} | {'giusta' if d['giusta'] else 'sbagliata'} | Brier {br:.3f} (riferimento {brr:.3f}) | "
          f"stagione: {s['giuste']} su {s['domande']}, Brier {s['brier']} contro {s['brier_riferimento']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("azione", choices=["crea", "stato", "valuta"])
    ap.add_argument("--lunedi", required=True)
    ap.add_argument("--file"); ap.add_argument("--valore", type=float); ap.add_argument("--data")
    ap.add_argument("--esito", choices=["si", "no"]); ap.add_argument("--fonte", default="")
    a = ap.parse_args()
    if a.azione == "crea":
        crea(a.lunedi, a.file)
    elif a.azione == "stato":
        stato(a.lunedi, a.valore, a.data)
    else:
        valuta(a.lunedi, a.esito, a.valore, a.fonte)
