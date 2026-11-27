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

# L'ora di uscita dell'edizione (ora di Roma) come la leggono i lettori: un posto solo (G-43). La leggono pagine.py (fascia
# d'iscrizione e invito delle pagine generate, feed, pagine fisse con data-ora-uscita, calendario di benvenuto.html) e
# benvenuto.py (testo della mail di benvenuto e fascia in cui non si spedisce). Se cambia (G-61): qui, poi
# python3 redazione/pagine.py e commit (il collaudo pretende le pagine rigenerate). Restano a mano: la mail di conferma
# in Kit (conferma-mail.txt di G-43) e gli orari veri dei flussi del mattino.
ORA_USCITA = "9:45"


def ora_uscita():
    """(ore, minuti) di ORA_USCITA."""
    h, m = ORA_USCITA.split(":")
    return int(h), int(m)


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


if __name__ == "__main__":
    d = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today()
    print(f"{d} uscita={uscita(d)} numero={numero(d)} primo_settimana={primo_della_settimana(d)}")
