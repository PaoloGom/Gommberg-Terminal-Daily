#!/usr/bin/env python3
"""Quanto lavora (e quanto pesa sul piano) l'attività del mattino: i numeri della pagina consumi/ del sito.
Non fa parte del giornale e non può fermare l'uscita: esce sempre con 0 e non lancia mai eccezioni. Nessuna chiamata a
modelli o alla rete: costa zero token.

Due file in consumi/:
  registro.json   una riga per edizione, scritta da pubblica.sh: durata, schede dei fatti, fonti citate, ricerche.
                  Sono misure, prese dai file dell'edizione.
  taratura.json   le letture vere del consumo: quanti punti del limite settimanale (pagina Utilizzo dell'app) sono
                  costati quanti minuti di attività, su quale piano. Da qui viene il tasso "punti al minuto" con cui la
                  pagina stima il peso di ogni edizione: stima = durata x tasso. Vale il piano dell'ultima lettura.

Perché non i token: un'attività programmata non può leggere i propri token. In chat il sistema li dà (Skill
"explain-usage"); nella sessione di un'attività la skill non esiste, né durante la corsa né riaprendo la sua chat
(due prove il 15/11/2026: "Unknown skill: explain-usage"). L'unica misura vera disponibile è la pagina Utilizzo.

Uso:
  consumo.py --indici <N> <AAAA-MM-GG> [fatti.json]             riga dell'edizione appena pubblicata (lo chiama pubblica.sh)
  consumo.py --storico                                           aggiunge le edizioni già uscite che mancano, dal repository
  consumo.py --taratura <punti> <minuti> <piano> "<nota>" [AAAA-MM-GG]   aggiunge una lettura vera
Variabili: GTD_REPO (default: il repository di questo file), GTD_LAVORO (default /home/claude/lavoro)."""
import datetime as dt
import json
import os
import re
import subprocess
import sys
import zoneinfo

QUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("GTD_REPO") or os.path.dirname(QUI)
LAVORO = os.environ.get("GTD_LAVORO", "/home/claude/lavoro")
ROMA = zoneinfo.ZoneInfo("Europe/Rome")


def carica(nome):
    try:
        r = json.load(open(os.path.join(REPO, "consumi", nome), encoding="utf-8"))
        return r if isinstance(r, list) else []
    except Exception:
        return []


def scrivi(nome, righe):
    os.makedirs(os.path.join(REPO, "consumi"), exist_ok=True)
    json.dump(righe, open(os.path.join(REPO, "consumi", nome), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))


def conta(fatti):
    """Schede, ricerche distinte e pagine distinte del registro dei fatti (qualunque sia la sua forma)."""
    ricerche, url = set(), set()

    def giro(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k == "ricerca" and isinstance(v, str) and v.strip():
                    ricerche.add(v.strip().lower())
                elif k == "ricerche" and isinstance(v, list):
                    ricerche.update(s.strip().lower() for s in v if isinstance(s, str) and s.strip())
                elif k == "url" and isinstance(v, str) and v.startswith("http"):
                    url.add(v.split("#")[0])
                else:
                    giro(v)
        elif isinstance(x, list):
            for y in x:
                giro(y)
    giro(fatti)
    schede = sum(1 for s in fatti if isinstance(s, dict) and s.get("id")) if isinstance(fatti, list) else 0
    return {"schede": schede, "ricerche": len(ricerche), "fonti": len(url)}


def metti(riga):
    reg = [x for x in carica("registro.json") if x.get("n") != riga["n"]] + [riga]
    scrivi("registro.json", sorted(reg, key=lambda x: x["n"]))
    return len(reg)


def indici(n, data, fatti_p):
    riga = {"n": int(n), "d": data}
    ora = dt.datetime.now(ROMA)
    riga["ora"] = ora.strftime("%H:%M")
    try:
        primi = [os.path.getmtime(os.path.join(LAVORO, f)) for f in os.listdir(LAVORO)]
        riga["durata_min"] = round((ora.timestamp() - min(primi)) / 60)
    except Exception:
        riga["durata_min"] = None
    try:
        riga.update(conta(json.load(open(fatti_p, encoding="utf-8"))))
    except Exception:
        pass
    k = metti(riga)
    print(f"Consumo: indicatori registrati (#{int(n):03d}, {riga.get('durata_min')} min, {riga.get('ricerche')} ricerche; {k} righe)")


def storico():
    """Le edizioni già uscite: durata = ora del commit "Edizione #NNN" meno l'avvio programmato (8:58; 9:00 fino al 13/10),
    solo se l'uscita cade tra le 9:05 e le 10:30 (un'edizione rifatta a mano più tardi non ha una durata nota)."""
    ed = json.load(open(os.path.join(REPO, "edizioni.json"), encoding="utf-8"))
    log = subprocess.run(["git", "-C", REPO, "log", "--reverse", "--format=%cI %s", "--grep=^Edizione #"],
                         capture_output=True, text=True).stdout.splitlines()
    uscite = {}
    for r in log:
        m = re.match(r"(\S+) Edizione #(\d+) - (\d{4}-\d\d-\d\d)", r)
        if m:
            t = dt.datetime.fromisoformat(m.group(1)).astimezone(ROMA)
            if t.date().isoformat() == m.group(3):          # solo il commit del giorno dell'edizione (non le prove)
                uscite.setdefault(int(m.group(2)), t)
    fatte, presenti = 0, {x.get("n") for x in carica("registro.json")}
    for e in ed:
        n, d = e["numero"], e["data"]
        t = uscite.get(n)
        if not t or n in presenti:
            continue
        riga = {"n": n, "d": d, "ora": t.strftime("%H:%M"), "durata_min": None}
        avvio = t.replace(hour=9, minute=0) if d < "2026-10-14" else t.replace(hour=8, minute=58)
        if dt.time(9, 5) <= t.time() <= dt.time(10, 30):
            riga["durata_min"] = round((t - avvio).total_seconds() / 60)
        fp = os.path.join(REPO, "redazione", "fatti", f"{d}.json")
        try:
            riga.update(conta(json.load(open(fp, encoding="utf-8"))))
        except Exception:
            pass
        riga["ricostruita"] = True
        metti(riga)
        fatte += 1
    print(f"Consumo: storico, {fatte} edizioni aggiunte")


def taratura(punti, minuti, piano, nota, giorno=None):
    riga = {"giorno": giorno or dt.datetime.now(ROMA).date().isoformat(), "piano": piano, "punti": float(punti),
            "durata_min": float(minuti), "nota": nota}
    if riga["punti"] <= 0 or riga["durata_min"] <= 0:
        raise ValueError("punti e minuti devono essere positivi")
    t = carica("taratura.json") + [riga]
    scrivi("taratura.json", sorted(t, key=lambda x: x["giorno"]))
    print(f"Consumo: taratura registrata ({riga['punti']} punti in {riga['durata_min']:.0f} min, piano {piano}; {len(t)} letture)")


if __name__ == "__main__":
    a = sys.argv[1:]
    try:
        if a[:1] == ["--indici"]:
            indici(a[1], a[2], a[3] if len(a) > 3 else os.path.join(LAVORO, "fatti.json"))
        elif a[:1] == ["--storico"]:
            storico()
        elif a[:1] == ["--taratura"]:
            taratura(a[1], a[2], a[3], a[4] if len(a) > 4 else "", a[5] if len(a) > 5 else None)
        else:
            print(__doc__)
    except Exception as e:   # mai un errore verso l'attività: questi numeri sono un di più
        print(f"Consumo: non registrato - {type(e).__name__}: {str(e)[:160]}")
    sys.exit(0)
