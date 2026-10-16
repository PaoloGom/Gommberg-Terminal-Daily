"""Controllo dei dati di mercato prima della stesura: dati vecchi, valori fermi, intraday spacciati per chiusure.
Uso: python3 controlli_dati.py <dati.json>
dati.json: {"oggi": "AAAA-MM-GG", "ora_roma": "HH:MM",
  "serie": {"S&P 500": {"mercato": "USA|EU|UK|JP|HK|KR|CN|FX|COMM|UST",
                        "ultimi": [["AAAA-MM-GG", valore, volume_o_null], ...],   # dal più recente, almeno 3
                        "tipo": "chiusura|intraday", "seconda_fonte": valore_o_null}}}
Serie con la sola variazione (seduta asiatica in corso, livello non disponibile): {"mercato": "KR", "tipo": "intraday",
  "var": -8.68, "ora": "08:11", "fonte": "Teleborsa", "ultimi": []}. "macro" (facoltativo, per le anomalie):
  [{"nome": "PPI USA a/a", "dato": 6.3, "atteso": 5.3, "caldo_se": "su"}] ("giu" per sussidi e disoccupazione).
Indici obbligatori (controlli_contenuti.py): S&P 500, Nasdaq, Euro Stoxx 50, Nikkei 225, Kospi, Hang Seng.
Esce con codice 1 se c'è un problema bloccante."""
import datetime as dt, json, sys

from zoneinfo import ZoneInfo

# Chiusura locale di ogni mercato (con un margine per l'asta finale), convertita in ora di Roma per la data di oggi:
# prima di quell'ora il dato di oggi non è una chiusura. Il fuso cambia in date diverse (USA, Europa, Asia senza ora legale).
LOCALE = {"USA": ("America/New_York", "16:15"), "UST": ("America/New_York", "17:00"), "EU": ("Europe/Rome", "17:45"),
          "UK": ("Europe/London", "16:45"), "JP": ("Asia/Tokyo", "15:45"), "HK": ("Asia/Hong_Kong", "16:15"),
          "KR": ("Asia/Seoul", "15:45"), "CN": ("Asia/Shanghai", "15:15"), "FX": None, "COMM": None}
d = json.load(open(sys.argv[1], encoding="utf-8"))
oggi = dt.date.fromisoformat(d["oggi"]); ora = d["ora_roma"]


def chiusura_roma(mercato):
    v = LOCALE.get(mercato)
    if not v:
        return None
    h, m = map(int, v[1].split(":"))
    loc = dt.datetime(oggi.year, oggi.month, oggi.day, h, m, tzinfo=ZoneInfo(v[0]))
    return loc.astimezone(ZoneInfo("Europe/Rome")).strftime("%H:%M")


CHIUSURA = {k: chiusura_roma(k) for k in LOCALE}
problemi, avvisi = [], []
for nome, s in d["serie"].items():
    u = s["ultimi"]
    if not u and s.get("var") is not None:
        if not (s.get("fonte") and s.get("ora")):
            problemi.append(f"{nome}: serie con sola variazione senza 'fonte' e 'ora'")
        continue
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
import re  # noqa: E402
for obb, rx in (("S&P 500", r"s&p ?500"), ("Nasdaq", r"nasdaq"), ("Euro Stoxx 50", r"stoxx ?50"), ("Nikkei 225", r"nikkei"),
                ("Kospi", r"kospi|seul|seoul"), ("Hang Seng", r"hang ?seng")):
    if not any(re.search(rx, k, re.I) for k in d["serie"]):
        problemi.append(f"{obb}: indice principale assente (serve l'ultima seduta conclusa; un movimento oltre il 3% va citato)")
print(f"Serie controllate: {len(d['serie'])}")
for a in avvisi:
    print("AVVISO: " + a)
if problemi:
    print("PROBLEMI:\n- " + "\n- ".join(problemi)); sys.exit(1)
print("OK: dati coerenti")
