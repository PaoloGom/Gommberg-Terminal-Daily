"""Contesto dei movimenti del giorno: quanto e' grande un movimento rispetto all'ultimo anno, perche' si muovono i tassi.
Uso: python3 contesto.py <dati.json> [--storia <cartella csv>] [--json <uscita>]
Storia: i csv di redazione/scommessa/dati (un anno di chiusure, aggiornati ogni lunedi'), completati con le chiusure di
dati.json successive all'ultima riga. Nessuna chiamata API in piu'. Stampa solo cio' che merita (movimento raro, curva,
scomposizione dei tassi, reazione ai dati macro); nel JSON c'e' tutto.
Le frasi stampate sono MATERIALE per la redazione, gia' in italiano da giornale: si usano riscritte nel testo, mai con
z-score o deviazioni standard (ISTRUZIONI par. 9). Serie facoltativa "Treasury 10 anni reale" in dati.json (mercato UST,
fonte ufficiale via ricerca: tasso reale dei TIPS a 10 anni) per la scomposizione tra crescita e inflazione attesa."""
import csv, datetime as dt, json, os, statistics, sys

QUI = os.path.dirname(os.path.abspath(__file__))
# serie di dati.json -> (csv della storia, tipo di variazione, nome nel testo, femminile)
MAPPA = {"S&P 500": ("spx", "pct", "l'S&P 500"), "Euro Stoxx 50": ("sx5e", "pct", "l'Euro Stoxx 50"),
         "ACWI": ("acwi", "pct", "l'azionario mondiale (ACWI)"), "Brent future": ("brent", "pct", "il Brent"),
         "EUR/USD": ("eurusd", "pct", "l'euro sul dollaro"), "VIX": ("vix", "punti", "il VIX"),
         "Treasury 10 anni": ("ust10", "pb", "il rendimento del Treasury a 10 anni"),
         "Treasury 2 anni": ("ust2", "pb", "il rendimento del Treasury a 2 anni")}
MESI = "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split()
FINESTRA = 250  # sedute di confronto (circa un anno)


def data_it(d, oggi):
    s = f"{d.day} {MESI[d.month - 1]}"
    return s if d.year == oggi.year else f"{s} {d.year}"


def leggi_storia(cartella, chiave):
    p = os.path.join(cartella, chiave + ".csv")
    if not os.path.exists(p):
        return {}
    out = {}
    for r in csv.reader(open(p, encoding="utf-8")):
        try:
            out[dt.date.fromisoformat(r[0])] = float(r[1])
        except (ValueError, IndexError):
            continue  # intestazione
    return out


def mossa(v0, v1, tipo):
    return (v0 / v1 - 1) * 100 if tipo == "pct" else (v0 - v1) * (100 if tipo == "pb" else 1)


def unita(x, tipo):
    s = f"{x:+.1f}".replace(".", ",") if tipo != "pb" else f"{x:+.0f}"
    return s + ("%" if tipo == "pct" else " pb" if tipo == "pb" else " punti")


def analizza(nome, serie, cartella, oggi):
    chiave, tipo, testo = MAPPA[nome]
    st = leggi_storia(cartella, chiave)
    if serie.get("tipo") == "intraday" or not serie.get("ultimi"):
        return None
    for d, v, *_ in serie["ultimi"]:
        d = dt.date.fromisoformat(d)
        if d < oggi and d not in st:  # la riga di oggi e' intraday per definizione; la storia ufficiale prevale
            st[d] = v
    giorni = sorted(st)
    if len(giorni) < 60:
        return None
    mosse = [(giorni[i], mossa(st[giorni[i]], st[giorni[i - 1]], tipo)) for i in range(1, len(giorni))]
    d_ult, m = mosse[-1]
    passato = [x for _, x in mosse[-FINESTRA - 1:-1]]
    sd = statistics.pstdev(passato) or 1e-9
    z = m / sd
    piu_grandi = sum(1 for x in passato if abs(x) >= abs(m))
    ultimo_pari = next((d for d, x in reversed(mosse[:-1]) if x * m > 0 and abs(x) >= abs(m)), None)
    if m == 0:
        frase_da = None
    elif ultimo_pari:
        art = "dall'" if ultimo_pari.day in (1, 8, 11) else "dal "
        frase_da = f"il {'rialzo' if m > 0 else 'calo'} più forte {art}{data_it(ultimo_pari, oggi)}"
    else:
        frase_da = f"il {'rialzo' if m > 0 else 'calo'} più forte da almeno {round((giorni[-1] - giorni[0]).days / 30.4)} mesi"
    rarita = (f"capita circa una seduta su {round(len(passato) / piu_grandi)}" if piu_grandi
              else "non era mai successo nell'ultimo anno")
    zeta = {}
    for i in range(1, len(mosse)):
        prima = [x for _, x in mosse[max(0, i - FINESTRA):i]]
        if len(prima) >= 60:
            zeta[mosse[i][0].isoformat()] = mosse[i][1] / (statistics.pstdev(prima) or 1e-9)
    return {"_z_per_data": zeta, "serie": nome, "seduta": d_ult.isoformat(), "variazione": round(m, 3), "tipo": tipo, "z": round(z, 2),
            "piu_forte_da": ultimo_pari.isoformat() if ultimo_pari else None, "frase_da": frase_da, "rarita": rarita,
            "notevole": abs(z) >= 1.5 or (piu_grandi and len(passato) / piu_grandi >= 10),
            "testo": f"{testo} {unita(m, tipo)} nella seduta del {data_it(d_ult, oggi)}: {frase_da} ({rarita})"}


def ultime_due(serie):
    u = [r for r in serie.get("ultimi", []) if serie.get("tipo") != "intraday"]
    return (u[0][1], u[1][1]) if len(u) >= 2 else None


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    dati = json.load(open(a[0], encoding="utf-8"))
    cartella = a[a.index("--storia") + 1] if "--storia" in a else next(
        (c for c in (os.path.join(QUI, "scommessa", "dati"),
                     os.path.join(os.environ.get("GTD_REPO", "/home/claude/gtd"), "redazione", "scommessa", "dati"))
         if os.path.isdir(c)), "")
    oggi = dt.date.fromisoformat(dati["oggi"])
    S = dati["serie"]
    out = {"movimenti": [], "curva": None, "tassi_reali": None, "macro": []}
    for nome in MAPPA:
        if nome in S:
            r = analizza(nome, S[nome], cartella, oggi)
            if r:
                out["movimenti"].append(r)
    righe = [r["testo"] for r in out["movimenti"] if r["notevole"]]

    n10, n2 = S.get("Treasury 10 anni"), S.get("Treasury 2 anni")
    if n10 and n2 and ultime_due(n10) and ultime_due(n2):
        (a10, b10), (a2, b2) = ultime_due(n10), ultime_due(n2)
        d10, d2 = round((a10 - b10) * 100), round((a2 - b2) * 100)
        dc = d10 - d2
        if abs(dc) >= 3:
            guida = "il lungo" if abs(d10) >= abs(d2) else "il breve"
            forma = "più ripida" if dc > 0 else "più piatta"
            lettura = {("il breve", "più piatta"): "il mercato si aspetta una banca centrale più dura nei prossimi mesi",
                       ("il breve", "più ripida"): "il mercato anticipa tagli dei tassi più vicini",
                       ("il lungo", "più ripida"): "il mercato chiede di più per prestare a lungo (inflazione futura o debito)",
                       ("il lungo", "più piatta"): "il mercato vede crescita e inflazione più basse negli anni a venire"}[(guida, forma)]
            out["curva"] = {"var_10a": d10, "var_2a": d2, "var_differenza": dc, "testo":
                            f"curva dei Treasury {forma} ({dc:+d} pb tra 10 e 2 anni), la muove {guida}: di solito significa che {lettura}"}
            righe.append(out["curva"]["testo"])

    re = S.get("Treasury 10 anni reale")
    if n10 and re and ultime_due(n10) and ultime_due(re):
        (a10, b10), (ar, br) = ultime_due(n10), ultime_due(re)
        dn, dr = round((a10 - b10) * 100), round((ar - br) * 100)
        db = dn - dr
        if dn:
            prev = "inflazione attesa" if abs(db) > abs(dr) else "rendimento reale (crescita e politica monetaria)"
            out["tassi_reali"] = {"var_nominale": dn, "var_reale": dr, "var_inflazione_attesa": db, "testo":
                                  f"il 10 anni USA {dn:+d} pb: {dr:+d} dal rendimento reale e {db:+d} dall'inflazione attesa; "
                                  f"pesa di più la parte di {prev}"}
            righe.append(out["tassi_reali"]["testo"])

    r2 = next((r for r in out["movimenti"] if r["serie"] == "Treasury 2 anni"), None)
    for m in dati.get("macro", []):
        if m.get("dato") is None or m.get("atteso") is None:
            continue
        sc = round(m["dato"] - m["atteso"], 2)
        caldo = (sc > 0) == (m.get("caldo_se", "su") == "su") if sc else None
        voce = {"nome": m["nome"], "scarto": sc, "caldo": caldo}
        z2 = r2["_z_per_data"].get(m.get("data", "")) if r2 else None  # seduta in cui il dato è uscito
        if z2 is not None:
            voce["reazione_2a"] = "forte" if abs(z2) >= 1.5 else "normale" if abs(z2) >= 0.5 else "quasi nulla"
            if caldo is not None and abs(z2) >= 0.5 and (z2 > 0) != caldo:
                voce["reazione_2a"] += (", ma in direzione opposta: rendimenti giù su un dato caldo" if caldo
                                        else ", ma in direzione opposta: rendimenti su su un dato freddo")
                voce["anomalia"] = True
                righe.append(f"ANOMALIA da spiegare (§5, passo 2c): {m['nome']} e reazione del 2 anni in direzione opposta")
        out["macro"].append(voce)
        if sc:
            righe.append(f"{m['nome']}: {str(sc).replace('.', ',')} punti {'sopra' if sc > 0 else 'sotto'} le attese "
                         f"({'più caldo' if caldo else 'più freddo'} del previsto)"
                         + (f"; reazione del 2 anni nella seduta del dato: {voce['reazione_2a']}" if "reazione_2a" in voce
                            else "; reazione del 2 anni: serve \"data\" (AAAA-MM-GG di uscita) nella voce macro"))

    for r in out["movimenti"]:
        r.pop("_z_per_data", None)
    if "--json" in a:
        json.dump(out, open(a[a.index("--json") + 1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("CONTESTO (materiale da riscrivere, non da copiare):" if righe else "CONTESTO: nessun movimento fuori dal normale")
    for r in righe:
        print("- " + r)


if __name__ == "__main__":
    main()
