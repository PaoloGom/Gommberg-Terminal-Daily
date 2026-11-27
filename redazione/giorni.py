"""Calendario delle uscite (senza importare il motore grafico).
Legge FESTIVI ed EDIZIONE_1 da gommberg_engine.py, così la fonte resta una sola.
Uso da riga di comando: python3 giorni.py [AAAA-MM-GG]  -> stampa uscita, numero, primo giorno della settimana."""
import datetime as dt, os, re, sys

QUI = os.path.dirname(os.path.abspath(__file__))


def _leggi_motore():
    src = open(os.path.join(QUI, "gommberg_engine.py"), encoding="utf-8").read()
    m = re.search(r"^FESTIVI\s*=\s*\{([^}]*)\}", src, re.M)
    festivi = set(re.findall(r"\d{4}-\d{2}-\d{2}", m.group(1))) if m else set()
    e = re.search(r"EDIZIONE_1\s*=.*?date\((\d+),\s*(\d+),\s*(\d+)\)", src)
    ed1 = dt.date(*map(int, e.groups())) if e else dt.date(2026, 10, 12)
    return festivi, ed1


FESTIVI, EDIZIONE_1 = _leggi_motore()


def uscita(d):
    return d.weekday() < 5 and d.isoformat() not in FESTIVI


def numero(d):
    n, x = 0, EDIZIONE_1
    while x <= d:
        n += uscita(x)
        x += dt.timedelta(days=1)
    return n


def primo_della_settimana(d):
    """True se d è il primo giorno di uscita della sua settimana (lunedì, o martedì dopo un lunedì festivo)."""
    lun = d - dt.timedelta(days=d.weekday())
    giorni = [lun + dt.timedelta(days=k) for k in range(5) if uscita(lun + dt.timedelta(days=k))]
    return bool(giorni) and giorni[0] == d


def prova():
    """Data di una prova generale: redazione/PROVA_DATA (una riga AAAA-MM-GG) fa valere quella data per l'edizione.
    Si crea solo per una prova e si toglie subito dopo; senza il file vale l'orologio di Roma."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PROVA_DATA")
    if os.path.exists(p):
        return dt.date.fromisoformat(open(p, encoding="utf-8").read().strip())
    return None


def oggi():
    from zoneinfo import ZoneInfo
    return prova() or dt.datetime.now(ZoneInfo("Europe/Rome")).date()


def lunedi(d):
    return d - dt.timedelta(days=d.weekday())


def uscita_precedente(d):
    x = d - dt.timedelta(days=1)
    while not uscita(x):
        x -= dt.timedelta(days=1)
    return x


# ---------------------------------------------------------------- feste delle borse asiatiche (G-41)
# Giorni feriali senza seduta per ogni mercato di dati.json ("mercato"): servono a sapere se un livello ricavato dalla
# variazione di stamattina poggia davvero sull'ultima seduta di quella borsa (numeri.ultima_seduta) e a riconoscere le
# righe che EODHD scrive a indice fermo. Fuori dall'intervallo verificato (FESTE_VERIFICATE) un giorno feriale non è né
# seduta né festa: il codice non ricava nulla e chiede la chiusura che manca. Si aggiornano come FESTIVI (APP_FESTIVI.md §2):
# il promemoria lo dà prepara.sh, a dicembre e nel mese prima della scadenza.
# HK: circolari HKEX CT/075/25 (2026) e CT/077/26 (2027), lette il 27/11/2026.
# KR: dal 13/10 al 27/11/2026 seduta ogni giorno feriale (EODHD e Investing.com, collaudi/2026-11-27/g41); 25/12 festa di
# legge, 31/12 chiusura di fine anno di KRX (regola fissa: ultimo giorno dell'anno), 1/1/2027 dal calendario 2027 del governo
# (Korea Aerospace Administration, 29/6/2026). Il calendario KRX 2027 esce a metà dicembre: allora il resto del 2027.
FESTE_BORSE = {
    "HK": {"2026-01-01", "2026-02-17", "2026-02-18", "2026-02-19", "2026-04-03", "2026-04-06", "2026-04-07", "2026-05-01",
           "2026-05-25", "2026-06-19", "2026-07-01", "2026-10-01", "2026-10-19", "2026-12-25",
           "2027-01-01", "2027-02-08", "2027-02-09", "2027-03-26", "2027-03-29", "2027-04-05", "2027-05-13", "2027-06-09",
           "2027-07-01", "2027-09-16", "2027-10-01", "2027-10-08", "2027-12-27"},
    "KR": {"2026-12-25", "2026-12-31", "2027-01-01"},
}
FESTE_VERIFICATE = {"HK": ("2026-01-01", "2027-12-31"), "KR": ("2026-10-13", "2027-01-31")}
NOMI_BORSE = {"HK": "Hong Kong", "KR": "Seul"}


def borsa_il(mercato, d):
    """ "festa" (sabato, domenica o festa di quella borsa), "seduta" (giorno feriale verificato senza festa) o None
    (mercato senza calendario o giorno fuori dall'intervallo verificato)."""
    x = dt.date.fromisoformat(str(d)[:10])
    if x.weekday() > 4:
        return "festa"
    dal_al = FESTE_VERIFICATE.get(mercato)
    if not dal_al or not dal_al[0] <= x.isoformat() <= dal_al[1]:
        return None
    return "festa" if x.isoformat() in FESTE_BORSE[mercato] else "seduta"


def promemoria_borse(d):
    """Le righe di prepara.sh quando il calendario di una borsa sta per finire (un mese prima) o, a dicembre, non copre
    l'anno dopo."""
    out = []
    for m, (_, fino) in sorted(FESTE_VERIFICATE.items()):
        if fino < (d + dt.timedelta(days=31)).isoformat() or (d.month == 12 and fino < f"{d.year + 1}-12-31"):
            out.append(f"CALENDARIO BORSE: le feste di {NOMI_BORSE.get(m, m)} sono verificate fino al {fino[8:]}/{fino[5:7]}/{fino[:4]}: "
                       f"aggiungi a FESTE_BORSE in giorni.py le date fino al 31/12/{d.year + 1} dal calendario ufficiale della borsa "
                       "e sposta FESTE_VERIFICATE (APP_FESTIVI.md §2), poi dillo nel messaggio finale")
    return out


if __name__ == "__main__":
    d = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today()
    print(f"{d} uscita={uscita(d)} numero={numero(d)} primo_settimana={primo_della_settimana(d)}")
