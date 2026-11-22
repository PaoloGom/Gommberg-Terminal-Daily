#!/usr/bin/env python3
"""Il GOMM (G-14): aggiorna dati/gomm.json con le visite dei giorni completi, lette dai contatori pubblici di GoatCounter.

Le pagine del sito (assets/gomm.js) leggono il file e chiedono al contatore solo i giorni dopo "fino" e il giorno in
corso: così restano poche richieste per lettore anche tra un anno. Il file si allunga di un numero al giorno.
Lo lancia .github/workflows/mattino.yml dal lunedì al venerdì, che poi fa il commit su main; il lunedì recupera anche il
fine settimana. Se il contatore non risponde non scrive nulla (le pagine chiedono i giorni mancanti da sole).
Nessun token: il contatore pubblico non lo chiede.

Uso: python3 redazione/gomm.py [cartella del repository]   esce con 0 anche quando non c'è nulla da aggiungere
"""
import json, os, sys, time, urllib.request
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

GC = "https://gommberg.goatcounter.com/counter/TOTAL.json"
DAL = "2026-10-17"          # primo giorno contato: la settimana base del GOMM è 17-23 ottobre
ROMA = ZoneInfo("Europe/Rome")


def visite(giorno: date):
    """Visite di un giorno. GoatCounter non conta il giorno indicato in "end": si manda il giorno dopo."""
    url = f"{GC}?start={giorno.isoformat()}&end={(giorno + timedelta(days=1)).isoformat()}"
    for prova in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "gommberg-gomm"}), timeout=20) as r:
                return int("".join(c for c in str(json.load(r).get("count", "0")) if c.isdigit()) or 0)
        except urllib.error.HTTPError as e:
            if e.code == 404:       # contatore senza visite in quel periodo
                return 0
        except (OSError, ValueError):
            pass
        time.sleep(2 * (prova + 1))
    return None


def main():
    repo = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), ".."))
    path = os.path.join(repo, "dati", "gomm.json")
    try:
        f = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        f = {}
    if f.get("dal") != DAL or not isinstance(f.get("visite"), list):
        f = {"dal": DAL, "visite": []}
    ieri = datetime.now(ROMA).date() - timedelta(days=1)
    vis = f["visite"]
    giorno = date.fromisoformat(DAL) + timedelta(days=len(vis))
    nuovi = 0
    while giorno <= ieri:
        v = visite(giorno)
        if v is None:
            print(f"GOMM: il contatore non risponde per il {giorno}: mi fermo, i giorni mancanti li chiedono le pagine")
            break
        vis.append(v)
        giorno += timedelta(days=1)
        nuovi += 1
    if not nuovi:
        print("GOMM: niente da aggiungere")
        return 0
    fino = date.fromisoformat(DAL) + timedelta(days=len(vis) - 1)
    uscita = {"nota": "Visite giornaliere del sito dal contatore pubblico di GoatCounter, giorni completi (ora di Roma). "
                      "Le aggiorna redazione/gomm.py ogni mattina dal lunedì al venerdì; i giorni dopo 'fino' le pagine li chiedono al contatore.",
              "dal": DAL, "fino": fino.isoformat(), "visite": vis}
    with open(path, "w", encoding="utf-8") as o:
        o.write(json.dumps(uscita, ensure_ascii=False, indent=2).replace(",\n    ", ", ").replace("[\n    ", "[").replace("\n  ]", "]") + "\n")
    print(f"GOMM: aggiunti {nuovi} giorni, fino al {fino.isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
