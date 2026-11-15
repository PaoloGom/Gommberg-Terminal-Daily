#!/usr/bin/env python3
"""Quanto lavora (e quanto consuma) l'attività del mattino: i numeri della pagina consumi/ del sito.
Non fa parte del giornale e non può fermare l'uscita: esce sempre con 0 e non lancia mai eccezioni. Nessuna chiamata a
modelli o alla rete: costa zero token.

Due file in consumi/:
  registro.json   una riga per edizione, scritta da pubblica.sh: durata, ricerche, fonti lette, schede, testo scritto.
                  Sono indicatori di lavoro, misurati dai file dell'edizione.
  taratura.json   le misure vere dei token (poche, fatte a mano): la sessione di un'edizione, aperta in chat, dà il
                  consumo misurato dal sistema (Skill "explain-usage"); una sessione programmata non può chiederlo da
                  sola (prova del 15/11/2026: "Unknown skill"). Da qui viene il tasso "token pesati al minuto" con cui la
                  pagina stima il consumo di ogni edizione: stima = durata x tasso. Più tarature, stima più solida.

Token pesati = ingresso + 2 x scritti in cache + 0,1 x letti dalla cache + 5 x uscita (il peso con cui li conta il sistema).

Uso:
  consumo.py --indici <N> <AAAA-MM-GG> [fatti.json]     riga dell'edizione appena pubblicata (lo chiama pubblica.sh)
  consumo.py --storico                                   ricostruisce le righe delle edizioni già uscite, dal repository
  consumo.py --taratura <durata_min> "<nota>" < uso.json  aggiunge una misura vera (il JSON di explain-usage su stdin)
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
PESI = {"input": 1, "cacheWrite": 2, "cacheRead": 0.1, "output": 5}
# gruppi del sistema -> voci della pagina (ciò che non è qui: un connettore se comincia per mcp__, altrimenti "altro")
VOCI = {"instructions": "istruzioni", "person": "testo", "claude": "testo", "summary": "testo",
        "WebSearch": "web", "WebFetch": "web", "Agent": "agenti", "Task": "agenti",
        "Bash": "comandi", "Read": "comandi", "Write": "comandi", "Edit": "comandi", "Glob": "comandi", "Grep": "comandi",
        "mcp__container": "comandi", "NotebookEdit": "comandi"}


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


def kb(*percorsi):
    return round(sum(os.path.getsize(p) for p in percorsi if p and os.path.isfile(p)) / 1024)


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
    riga["scritto_kb"] = kb(fatti_p, os.path.join(LAVORO, f"edizione_{data}.py"))
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
    fatte = 0
    for e in ed:
        n, d = e["numero"], e["data"]
        t = uscite.get(n)
        if not t:
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
        riga["scritto_kb"] = kb(fp, os.path.join(REPO, "redazione", "sorgenti", d, "edizione.py"))
        riga["ricostruita"] = True
        metti(riga)
        fatte += 1
    print(f"Consumo: storico ricostruito ({fatte} edizioni)")


def leggi_uso(testo):
    try:
        return json.loads(testo)
    except ValueError:
        pass
    for m in re.finditer(r"\{", testo):
        try:
            ogg, _ = json.JSONDecoder().raw_decode(testo[m.start():])
        except ValueError:
            continue
        if isinstance(ogg, dict) and "tokens" in ogg:
            return ogg
    raise ValueError("nessun JSON con \"tokens\" nell'ingresso")


def taratura(durata, nota, testo):
    uso = leggi_uso(testo)
    tok = {k: int(uso["tokens"].get(k, 0) or 0) for k in PESI}
    if not any(tok.values()):
        raise ValueError("token tutti a zero")
    quote, conn, chiamate = {}, {}, {}
    for g in uso.get("groups") or []:
        nome, q, c = str(g.get("group", "")), float(g.get("percent", 0) or 0), int(g.get("calls", 0) or 0)
        if nome.startswith("mcp__") and nome not in VOCI:
            k = nome[5:].replace("_", " ").strip() or "connettore"
            conn[k] = round(conn.get(k, 0) + q, 1)
            chiamate[k] = chiamate.get(k, 0) + c
            continue
        v = VOCI.get(nome, "altro")
        quote[v] = round(quote.get(v, 0) + q, 1)
        if nome in ("WebSearch", "WebFetch", "Agent", "Task"):
            chiamate[nome] = chiamate.get(nome, 0) + c
    riga = {"giorno": dt.datetime.now(ROMA).date().isoformat(), "nota": nota, "durata_min": float(durata),
            "richieste": int(uso.get("requests", 0) or 0), "token": tok,
            "pesati": round(sum(tok[k] * PESI[k] for k in PESI)), "quote": quote, "connettori": conn, "chiamate": chiamate}
    t = carica("taratura.json") + [riga]
    scrivi("taratura.json", t)
    print(f"Consumo: taratura registrata ({riga['pesati'] / 1e6:.2f} milioni di token pesati in {durata} min; {len(t)} misure)")


if __name__ == "__main__":
    a = sys.argv[1:]
    try:
        if a[:1] == ["--indici"]:
            indici(a[1], a[2], a[3] if len(a) > 3 else os.path.join(LAVORO, "fatti.json"))
        elif a[:1] == ["--storico"]:
            storico()
        elif a[:1] == ["--taratura"]:
            taratura(a[1], a[2] if len(a) > 2 else "", sys.stdin.read())
        else:
            print(__doc__)
    except Exception as e:   # mai un errore verso l'attività: questi numeri sono un di più
        print(f"Consumo: non registrato - {type(e).__name__}: {str(e)[:160]}")
    sys.exit(0)
