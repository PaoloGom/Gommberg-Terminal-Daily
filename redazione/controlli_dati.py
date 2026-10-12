"""Controllo dei dati di mercato prima della stesura: dati vecchi, valori fermi, intraday spacciati per chiusure.
Uso: python3 controlli_dati.py <dati.json>
dati.json: {"oggi": "AAAA-MM-GG", "ora_roma": "HH:MM",
  "serie": {"S&P 500": {"mercato": "USA|EU|UK|JP|HK|KR|CN|FX|COMM|UST",
                        "ultimi": [["AAAA-MM-GG", valore, volume_o_null], ...],   # dal più recente, almeno 3
                        "tipo": "chiusura|intraday", "seconda_fonte": valore_o_null}}}
Esce con codice 1 se c'è un problema bloccante."""
import datetime as dt, json, sys

# Ora di chiusura in ora di Roma (CET/CEST): prima di quest'ora il dato di oggi non è una chiusura.
CHIUSURA = {"USA": "22:00", "EU": "17:40", "UK": "17:40", "JP": "08:00", "HK": "10:15", "KR": "08:45",
            "CN": "08:05", "UST": "22:00", "FX": None, "COMM": None}
d = json.load(open(sys.argv[1], encoding="utf-8"))
oggi = dt.date.fromisoformat(d["oggi"]); ora = d["ora_roma"]
problemi, avvisi = [], []
for nome, s in d["serie"].items():
    u = s["ultimi"]
    if len(u) < 2:
        problemi.append(f"{nome}: meno di due osservazioni"); continue
    (d0, v0, vol0), (d1, v1, _) = u[0], u[1]
    d0 = dt.date.fromisoformat(d0)
    giorni_lav = sum(1 for k in range(1, (oggi - d0).days + 1) if (d0 + dt.timedelta(days=k)).weekday() < 5)
    if giorni_lav > 2:
        problemi.append(f"{nome}: ultimo dato del {d0}, vecchio di {giorni_lav} giorni lavorativi (festività? verificare e dichiararlo)")
    elif giorni_lav == 2:
        avvisi.append(f"{nome}: ultimo dato del {d0} (possibile festività: dichiararla nel PDF)")
    ch = CHIUSURA.get(s.get("mercato"))
    if d0 == oggi and ch and ora < ch and s.get("tipo") == "chiusura":
        problemi.append(f"{nome}: dato di oggi segnato come chiusura ma il mercato chiude alle {ch}: è intraday")
    if v0 == v1 and (vol0 in (None, 0) or (isinstance(vol0, (int, float)) and vol0 < 1000)):
        problemi.append(f"{nome}: valore identico alla seduta precedente con volume nullo: dato probabilmente fermo")
    if d0 == oggi and isinstance(vol0, (int, float)) and 0 < vol0 < 1000 and s.get("mercato") not in ("FX", "COMM"):
        avvisi.append(f"{nome}: volume quasi nullo ({vol0}): verificare che il dato sia aggiornato")
    if v1 and abs(v0 / v1 - 1) > 0.08 and s.get("mercato") not in ("COMM",):
        avvisi.append(f"{nome}: variazione giornaliera {100 * (v0 / v1 - 1):+.1f}%: verificare con una seconda fonte")
    sf = s.get("seconda_fonte")
    if sf:
        scarto = abs(v0 / sf - 1)
        if scarto > 0.005:
            problemi.append(f"{nome}: scarto {100 * scarto:.2f}% con la seconda fonte ({v0} contro {sf})")
print(f"Serie controllate: {len(d['serie'])}")
for a in avvisi:
    print("AVVISO: " + a)
if problemi:
    print("PROBLEMI:\n- " + "\n- ".join(problemi)); sys.exit(1)
print("OK: dati coerenti")
