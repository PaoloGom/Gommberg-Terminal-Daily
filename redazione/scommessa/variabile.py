"""Lo strumento della settimana: il settimo mercato della scommessa, scelto ogni lunedì sul tema del momento.

Stesso gioco dei 6 fissi (chiusura di partenza, previsione della redazione, forchetta del modello, on track,
verdetto), con pagella separata. Questo script prepara lo strumento e ne controlla l'ammissibilità:
- serie giornaliera dai nostri dati (FMP o Alpha Vantage) di almeno 60 sedute fino al venerdì di partenza;
- nessun doppione: la correlazione delle variazioni settimanali dell'ultimo anno con ognuno dei 6 fissi deve essere
  sotto 0,7 in valore assoluto (il Nasdaq, che si muove come l'S&P 500, non passa);
- niente singole azioni nella settimana dei loro conti (la forchetta delle ultime 20 sedute sarebbe troppo stretta):
  dichiaralo con --conti-in-settimana se ci sono, e lo script rifiuta.

Uso (dalla cartella redazione/scommessa):
  python3 variabile.py --chiave oro --nome "Oro (future)" --tipo prezzo --unita "$" \
      --serie /home/claude/lavoro/serie_oro.json --motivo "Il rifugio della settimana di Hormuz"
serie_*.json = [["2026-07-01", 3301.2], ...] (chiusure ufficiali, mai la riga di oggi).
Scrive dati/var_<chiave>.csv e dati/var_<chiave>.json (nome, tipo, unità, motivo); poi pronostico.py --variabile var_<chiave>."""
import argparse, csv, datetime as dt, json, os, sys

import numpy as np
import pandas as pd

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
from motore import STRUMENTI, carica, chiusure_settimanali  # noqa: E402

FISSI = [k for k in json.load(open(os.path.join(QUI, "metodo.json"), encoding="utf-8"))["strumenti"]]
SOGLIA_CORR = 0.7


def settimanali(s, tipo):
    w = chiusure_settimanali(s)
    return (np.log(w).diff() if tipo == "prezzo" else w.diff() * 100).dropna()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chiave", required=True); ap.add_argument("--nome", required=True)
    ap.add_argument("--tipo", choices=["prezzo", "tasso"], default="prezzo"); ap.add_argument("--unita", default="")
    ap.add_argument("--serie", required=True); ap.add_argument("--motivo", required=True)
    ap.add_argument("--conti-in-settimana", action="store_true")
    a = ap.parse_args()
    k = "var_" + a.chiave.lower().replace("var_", "")
    if a.chiave in FISSI or k[4:] in FISSI:
        raise SystemExit(f"ERRORE: {a.chiave} è già tra i 6 fissi: sarebbe un doppione")
    if a.conti_in_settimana:
        raise SystemExit("ERRORE: singola azione nella settimana dei suoi conti: la forchetta sarebbe troppo stretta, scegli altro")
    oggi = dt.date.today().isoformat()
    righe = [(d, float(v)) for d, v in json.load(open(a.serie, encoding="utf-8")) if d < oggi]
    if len(righe) < 60:
        raise SystemExit(f"ERRORE: servono almeno 60 sedute di chiusure (ne ho {len(righe)})")
    s = pd.Series({pd.Timestamp(d): v for d, v in righe}).sort_index()
    s = s[s.index.dayofweek < 5]
    wv = settimanali(s, a.tipo).iloc[-52:]
    corr = {}
    for f in FISSI:
        try:
            wf = settimanali(carica(f), STRUMENTI[f]["tipo"])
        except Exception:
            continue
        j = pd.concat([wv, wf], axis=1, join="inner").dropna()
        if len(j) >= 12:
            corr[f] = round(float(j.iloc[:, 0].corr(j.iloc[:, 1])), 2)
    troppo = {f: c for f, c in corr.items() if abs(c) >= SOGLIA_CORR}
    if troppo:
        raise SystemExit(f"ERRORE: doppione di {troppo} (correlazione settimanale >= {SOGLIA_CORR}): scegli un mercato che "
                         "racconti un'altra cosa")
    os.makedirs(os.path.join(QUI, "dati"), exist_ok=True)
    with open(os.path.join(QUI, "dati", k + ".csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["data", "valore"])
        for d, v in s.items():
            w.writerow([d.date().isoformat(), v])
    meta = {"nome": a.nome, "tipo": a.tipo, "unita": a.unita, "motivo_scelta": a.motivo, "correlazioni": corr,
            "sedute": len(s), "ultima": str(s.index[-1].date())}
    json.dump(meta, open(os.path.join(QUI, "dati", k + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"OK {k}: {a.nome}, {len(s)} sedute fino al {s.index[-1].date()}; correlazioni con i fissi {corr}")


if __name__ == "__main__":
    main()
