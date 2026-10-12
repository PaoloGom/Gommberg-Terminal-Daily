"""Motore quantitativo della Scommessa della settimana.

Tutto quello che serve per stimare, in modo riproducibile, la distribuzione della chiusura del venerdì:
- caricamento delle serie storiche giornaliere (cartella dati/);
- variazioni settimanali venerdì su venerdì (log-rendimenti per i prezzi, punti base per i rendimenti);
- stimatori della volatilità settimanale;
- quantili della distribuzione prevista e probabilità di rialzo;
- regole di punteggio (quelle per i lettori e quelle "proper" per noi).

Nessuna dipendenza oltre numpy, pandas, scipy. Nessuna informazione dal futuro: ogni funzione che stima
alla data t usa solo dati con data <= t.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
import pandas as pd
from scipy import stats

QUI = os.path.dirname(os.path.abspath(__file__))
DATI = os.environ.get("GOMMBERG_DATI", os.path.join(QUI, "dati"))  # per il backtest: cartella con lo storico completo

# Strumenti della scommessa. tipo "prezzo" = log-rendimenti; tipo "tasso" = variazioni in punti base.
STRUMENTI = {
    "acwi":   {"nome": "MSCI ACWI (ETF)", "file": "acwi.csv", "tipo": "prezzo", "unita": "$"},
    "spx":    {"nome": "S&P 500", "file": "spx.csv", "tipo": "prezzo", "unita": "punti"},
    "sx5e":   {"nome": "Euro Stoxx 50", "file": "sx5e.csv", "tipo": "prezzo", "unita": "punti"},
    "ust10":  {"nome": "Treasury 10 anni", "file": "ust10.csv", "tipo": "tasso", "unita": "%"},
    "ust2":   {"nome": "Treasury 2 anni", "file": "ust2.csv", "tipo": "tasso", "unita": "%"},
    "brent":  {"nome": "Brent future", "file": "brent.csv", "tipo": "prezzo", "unita": "$"},
    "eurusd": {"nome": "EUR/USD", "file": "eurusd.csv", "tipo": "prezzo", "unita": ""},
}

# Livelli dei quantili usati ovunque (il 50% è la previsione puntuale del modello)
QUANTILI = [0.05, 0.10, 0.16, 0.25, 0.50, 0.75, 0.84, 0.90, 0.95]
QL_PINBALL = np.round(np.arange(0.05, 0.951, 0.05), 2)  # 19 livelli: media del pinball = approssimazione del CRPS


def carica(chiave: str) -> pd.Series:
    """Serie giornaliera (indice = data) del livello dello strumento."""
    f = os.path.join(DATI, STRUMENTI[chiave]["file"]) if chiave in STRUMENTI else os.path.join(DATI, chiave + ".csv")
    df = pd.read_csv(f, parse_dates=["data"]).dropna()
    s = df.set_index("data")["valore"].astype(float).sort_index()
    s = s[~s.index.duplicated(keep="last")]
    s = s[s.index.dayofweek < 5]  # niente righe di sabato o domenica
    return s[s > 0] if chiave not in ("ust10", "ust2") else s


def variazioni_giornaliere(s: pd.Series, tipo: str) -> pd.Series:
    """Log-rendimenti per i prezzi, differenze in punti base per i tassi."""
    return (np.log(s).diff() if tipo == "prezzo" else s.diff() * 100).dropna()


def chiusure_settimanali(s: pd.Series) -> pd.Series:
    """Ultima chiusura disponibile di ogni settimana (di norma il venerdì)."""
    return s.groupby(s.index.to_period("W-FRI")).last().pipe(lambda x: x.set_axis(x.index.end_time.normalize()))


def variazione(a: float, b: float, tipo: str) -> float:
    """Variazione da a a b: log-rendimento o punti base."""
    return math.log(b / a) if tipo == "prezzo" else (b - a) * 100


def livello(base: float, x: float, tipo: str) -> float:
    """Livello corrispondente alla variazione x a partire da base."""
    return base * math.exp(x) if tipo == "prezzo" else base + x / 100


# ----------------------------------------------------------------------------------------------
# Stimatori della volatilità settimanale (deviazione standard della variazione a 5 sedute)
# ----------------------------------------------------------------------------------------------
def vol_rv(r: pd.Series, n: int = 20) -> float:
    return float(r.iloc[-n:].std(ddof=1) * math.sqrt(5))


def vol_ewma(r: pd.Series, lam: float = 0.94, n: int = 500) -> float:
    x = r.iloc[-n:].values
    w = lam ** np.arange(len(x) - 1, -1, -1)
    return float(math.sqrt(np.sum(w * x * x) / np.sum(w)) * math.sqrt(5))


def vol_blend(r: pd.Series, lam: float = 0.94, peso_lungo: float = 0.3, n_lungo: int = 756) -> float:
    """EWMA con un ritorno parziale alla media di lungo periodo (la volatilità tende a tornare verso la sua media)."""
    v_breve = vol_ewma(r, lam) ** 2
    v_lungo = (r.iloc[-n_lungo:].std(ddof=1) * math.sqrt(5)) ** 2
    return float(math.sqrt((1 - peso_lungo) * v_breve + peso_lungo * v_lungo))


def sigma_metodo(nome: str, r: pd.Series, vix: float | None = None) -> float:
    """Sigma settimanale per nome di metodo (rv20, rv60, ewma94, ewma97, blend, vix)."""
    if nome.startswith("rv"):
        return vol_rv(r, int(nome[2:]))
    if nome.startswith("ewma"):
        return vol_ewma(r, int(nome[4:]) / 100)
    if nome == "blend":
        return vol_blend(r, 0.94, 0.3)
    if nome == "vix":
        return vol_vix(vix)
    raise ValueError(nome)


def vol_vix(vix: float) -> float:
    """Volatilità implicita del VIX (annua, in %) riportata a una settimana, come log-rendimento."""
    return vix / 100 / math.sqrt(52)


# ----------------------------------------------------------------------------------------------
# Distribuzione prevista
# ----------------------------------------------------------------------------------------------
def quantili_normale(mu: float, sigma: float, livelli=QUANTILI) -> np.ndarray:
    return mu + sigma * stats.norm.ppf(livelli)


def quantili_t(mu: float, sigma: float, nu: float = 5.0, livelli=QUANTILI) -> np.ndarray:
    """Student-t riscalata in modo che la deviazione standard sia sigma (code più spesse della normale)."""
    scala = sigma * math.sqrt((nu - 2) / nu)
    return mu + scala * stats.t.ppf(livelli, nu)


def quantili_empirici(mu: float, sigma: float, z_storici: np.ndarray, livelli=QUANTILI) -> np.ndarray:
    """Simulazione storica filtrata: quantili delle variazioni passate standardizzate dalla loro volatilità ex ante,
    centrati sulla loro mediana (altrimenti la forma reintroduce di nascosto una deriva)."""
    return mu + sigma * (np.quantile(z_storici, livelli) - np.median(z_storici))


def prob_rialzo(mu: float, sigma: float, forma: str = "normale") -> float:
    """P(variazione > 0) per la distribuzione centrata in mu con deviazione standard sigma."""
    if sigma <= 0:
        return 0.5
    if forma == "t5":
        return float(stats.t.cdf(mu / (sigma * math.sqrt(3 / 5)), 5))
    return float(stats.norm.cdf(mu / sigma))


# ----------------------------------------------------------------------------------------------
# Punteggi
# ----------------------------------------------------------------------------------------------
def pinball(y: float, q: np.ndarray, livelli: np.ndarray) -> float:
    """Perdita quantile media (più bassa = meglio). Con 19 livelli equidistanti approssima il CRPS."""
    d = y - q
    return float(np.mean(np.maximum(livelli * d, (livelli - 1) * d)))


def brier(p: float, esito: int) -> float:
    return (p - esito) ** 2


def punti_lettori(base: float, previsione: float, lo: float, hi: float, finale: float) -> tuple[int, int]:
    """Il gioco pubblicato: 1 punto per la direzione giusta, 1 punto se la chiusura cade nel range."""
    direzione = int(np.sign(previsione - base) == np.sign(finale - base) and finale != base)
    dentro = int(lo <= finale <= hi)
    return direzione, dentro


def salva_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=float)
