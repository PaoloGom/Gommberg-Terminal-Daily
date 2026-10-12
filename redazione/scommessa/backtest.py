"""Backtest dei metodi della Scommessa: quale previsione e quale range avrebbero funzionato meglio, settimana per settimana,
usando ogni volta solo i dati disponibili fino al venerdì di partenza (niente informazioni dal futuro).

Uso: GOMMBERG_DATI=<cartella con lo storico completo> python3 backtest.py [AAAA-MM-GG inizio valutazione]  ->  scrive backtest/risultati_<data>.json e .md
"""
import datetime as dt
import json
import math
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

from motore import (STRUMENTI, QL_PINBALL, carica, variazioni_giornaliere, chiusure_settimanali, vol_rv, vol_ewma,
                    vol_blend, vol_vix, pinball, brier)

QUI = os.path.dirname(os.path.abspath(__file__))
INIZIO = pd.Timestamp(sys.argv[1] if len(sys.argv) > 1 else "2011-01-01")
TAGLIO = pd.Timestamp("2019-12-31")  # due sotto-periodi per la robustezza
MIN_STORIA_Z = 156                    # settimane minime per i quantili empirici (3 anni)
MIN_STORIA_MEDIA = 260                # settimane minime per stimare drift e regressioni (5 anni)


def hac_t(d: np.ndarray, lag: int = 4) -> float:
    """t-statistico di Diebold-Mariano con varianza Newey-West (perdita media differente da zero?)."""
    d = d - 0.0
    n = len(d)
    m = d.mean()
    e = d - m
    v = e @ e / n
    for k in range(1, lag + 1):
        w = 1 - k / (lag + 1)
        v += 2 * w * (e[k:] @ e[:-k]) / n
    return float(m / math.sqrt(v / n)) if v > 0 else 0.0


def esegui(chiave, vix_w=None):
    info = STRUMENTI[chiave]
    tipo = info["tipo"]
    s = carica(chiave)
    r = variazioni_giornaliere(s, tipo)
    w = chiusure_settimanali(s)
    date_w = w.index
    vals = w.values
    righe = []
    for i in range(len(date_w) - 1):
        t, t1 = date_w[i], date_w[i + 1]
        if t < INIZIO - pd.Timedelta(days=400):
            continue
        rr = r[r.index <= t]
        if len(rr) < 800:
            continue
        y = (math.log(vals[i + 1] / vals[i]) if tipo == "prezzo" else (vals[i + 1] - vals[i]) * 100)
        passato = [(math.log(vals[j + 1] / vals[j]) if tipo == "prezzo" else (vals[j + 1] - vals[j]) * 100) for j in range(i)]
        riga = {"t": t, "y": y,
                "ult": passato[-1] if passato else 0.0,
                "mom12": sum(passato[-12:]) if len(passato) >= 12 else 0.0,
                "rv20": vol_rv(rr, 20), "rv60": vol_rv(rr, 60),
                "ewma94": vol_ewma(rr, 0.94), "ewma97": vol_ewma(rr, 0.97),
                "blend": vol_blend(rr, 0.94, 0.3)}
        if vix_w is not None:
            v = vix_w[vix_w.index <= t]
            riga["vix"] = vol_vix(float(v.iloc[-1])) if len(v) else np.nan
        righe.append(riga)
    df = pd.DataFrame(righe).set_index("t")
    return df


def valuta(df, tipo):
    """Confronta stimatori della volatilità, forme della distribuzione e previsioni puntuali."""
    out = {"n_settimane": 0, "volatilita": {}, "media": {}}
    sig_cols = [c for c in ["rv20", "rv60", "ewma94", "ewma97", "blend", "vix"] if c in df.columns]
    # --- previsioni puntuali (stimate su finestra espansiva, solo passato) ---
    ys = df["y"].values
    n = len(df)
    mu = {k: np.zeros(n) for k in ["zero", "drift", "inversione", "momentum"]}
    for i in range(n):
        if i < MIN_STORIA_MEDIA:
            continue
        past = df.iloc[:i]
        mu["drift"][i] = past["y"].mean()
        for nome, col in (("inversione", "ult"), ("momentum", "mom12")):
            x = past[col].values
            yy = past["y"].values
            b = np.polyfit(x, yy, 1) if np.std(x) > 0 else (0, yy.mean())
            mu[nome][i] = b[1] + b[0] * df[col].iloc[i]
    valid = (df.index >= INIZIO) & (np.arange(n) >= MIN_STORIA_MEDIA)
    idx = np.where(valid)[0]
    out["n_settimane"] = int(len(idx))
    out["periodo"] = [str(df.index[idx[0]].date()), str(df.index[idx[-1]].date())]
    y = ys[idx]
    for nome, m in mu.items():
        e = (y - m[idx]) ** 2
        e0 = y ** 2
        r2 = 1 - e.sum() / e0.sum()
        dm = hac_t(e0 - e)  # positivo = meglio della passeggiata casuale
        nz = m[idx] != 0
        hit = float(np.mean(np.sign(m[idx][nz]) == np.sign(y[nz]))) if nz.any() else float("nan")
        out["media"][nome] = {"R2_fuori_campione_%": round(100 * r2, 2), "t_DM_vs_zero": round(dm, 2),
                              "direzione_giusta_%": round(100 * hit, 1) if hit == hit else None}
    out["quota_rialzi_%"] = round(100 * float(np.mean(y > 0)), 1)
    # --- volatilità e forma della distribuzione (con media zero, per isolare l'effetto del range) ---
    for c in sig_cols:
        sig = df[c].values
        z_all = ys / sig
        for forma in ("normale", "t5", "empirica"):
            loss, c68, c90, ok = [], [], [], []
            for i in idx:
                sgm = sig[i]
                if not np.isfinite(sgm) or sgm <= 0:
                    continue
                if forma == "normale":
                    q = sgm * stats.norm.ppf(QL_PINBALL); q16, q84, q05, q95 = sgm * stats.norm.ppf([.16, .84, .05, .95])
                elif forma == "t5":
                    sc = sgm * math.sqrt(3 / 5)
                    q = sc * stats.t.ppf(QL_PINBALL, 5); q16, q84, q05, q95 = sc * stats.t.ppf([.16, .84, .05, .95], 5)
                else:
                    if i < MIN_STORIA_Z:
                        continue
                    z = z_all[:i][np.isfinite(z_all[:i])]
                    med = np.median(z)  # quantili centrati: la forma empirica non deve reintrodurre una deriva
                    q = sgm * (np.quantile(z, QL_PINBALL) - med); q16, q84, q05, q95 = sgm * (np.quantile(z, [.16, .84, .05, .95]) - med)
                loss.append(pinball(ys[i], q, QL_PINBALL))
                c68.append(q16 <= ys[i] <= q84)
                c90.append(q05 <= ys[i] <= q95)
                ok.append(i)
            out.setdefault("_perdite", {})[f"{c}|{forma}"] = (ok, [l / df["rv20"].values[i] for l, i in zip(loss, ok)])  # stessa unità per tutti i metodi: sigma di riferimento
            out["volatilita"][f"{c}|{forma}"] = {
                "perdita_quantile": float(np.mean(loss)), "copertura_68_%": round(100 * np.mean(c68), 1),
                "copertura_90_%": round(100 * np.mean(c90), 1), "_serie": loss, "_idx": ok}
    # test: ogni combinazione contro quella attuale (rv20|normale), su sotto-periodi
    ref = out["volatilita"]["rv20|normale"]
    for k, v in out["volatilita"].items():
        comune = sorted(set(v["_idx"]) & set(ref["_idx"]))
        a = np.array([v["_serie"][v["_idx"].index(i)] for i in comune])
        b = np.array([ref["_serie"][ref["_idx"].index(i)] for i in comune])
        v["miglioramento_vs_attuale_%"] = round(100 * (1 - a.mean() / b.mean()), 2)
        v["t_DM_vs_attuale"] = round(hac_t(b - a), 2)
        date = df.index[comune]
        for nome, msk in (("pre2020", date <= TAGLIO), ("dal2020", date > TAGLIO)):
            v[f"migl_{nome}_%"] = round(100 * (1 - a[msk].mean() / b[msk].mean()), 2) if msk.any() else None
    for v in out["volatilita"].values():
        v.pop("_serie"); v.pop("_idx")
    out["_date"] = [str(d.date()) for d in df.index]
    return out


def main():
    vix = chiusure_settimanali(carica("vix"))
    ris = {"eseguito": dt.datetime.now().isoformat(timespec="minutes"), "inizio_valutazione": str(INIZIO.date()), "strumenti": {}}
    for k in ["spx", "sx5e", "ust10", "ust2", "brent", "eurusd"]:
        df = esegui(k, vix if k == "spx" else None)
        ris["strumenti"][k] = valuta(df, STRUMENTI[k]["tipo"])
        print(k, "ok", ris["strumenti"][k]["n_settimane"])
    # specifica unica: stesso metodo per tutti, test aggregato su perdite in unità di sigma
    cand = set.intersection(*[set(v["_perdite"]) for v in ris["strumenti"].values()])
    unica = {}
    for c in sorted(cand):
        diffs, n_meglio = [], 0
        for v in ris["strumenti"].values():
            ok_r, l_r = v["_perdite"]["rv20|normale"]; ok_c, l_c = v["_perdite"][c]
            mr, mc = dict(zip(ok_r, l_r)), dict(zip(ok_c, l_c))
            comuni = sorted(set(mr) & set(mc))
            d = np.array([mr[i] - mc[i] for i in comuni])
            diffs.append(pd.Series(d, index=[v["_date"][i] for i in comuni]))
            n_meglio += d.mean() > 0
        tot = pd.concat(diffs, axis=1).mean(axis=1).dropna()
        post = tot[tot.index > "2019-12-31"]
        unica[c] = {"strumenti_migliorati": int(n_meglio), "t_DM_aggregato": round(hac_t(tot.values), 2),
                    "t_DM_dal2020": round(hac_t(post.values), 2)}
    ris["specifica_unica"] = unica
    for v in ris["strumenti"].values():
        v.pop("_perdite"); v.pop("_date")
    os.makedirs(os.path.join(QUI, "backtest"), exist_ok=True)
    oggi = dt.date.today().isoformat()
    with open(os.path.join(QUI, "backtest", f"risultati_{oggi}.json"), "w") as f:
        json.dump(ris, f, indent=1)
    print("salvato")


if __name__ == "__main__":
    main()
