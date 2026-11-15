#!/usr/bin/env python3
"""Registro del consumo di token dell'attività automatica: una riga per edizione in consumi/registro.json, che la pagina
consumi/ del sito disegna giorno per giorno. Non fa parte del giornale e non può fermare l'uscita: gira dopo la
pubblicazione e la consegna del PDF, esce sempre con 0 e non lancia mai eccezioni.

Uso (ultimo passo dell'attività, dopo SendUserFile e prima del messaggio finale):
  python3 /home/claude/gtd/redazione/consumo.py <<'JSON'
  {"requests": 180, "tokens": {"input": 24, "cacheWrite": 130772, "cacheRead": 2396876, "output": 15128}, "groups": [...]}
  JSON
Il JSON è quello che la sessione riceve chiamando lo strumento Skill con "explain-usage": il consumo misurato dal sistema
(richieste, token in ingresso, scritti e letti in cache, in uscita) e la quota stimata per gruppo. Qui non si stima nulla.

Token pesati = ingresso + 2 x scritti in cache + 0,1 x letti dalla cache + 5 x uscita: è il metro con cui il sistema pesa
il consumo, e quindi quello che si confronta di giorno in giorno. La quota per gruppo è una stima del sistema (il consumo è
misurato per richiesta, non per strumento).

Variabili: GTD_REPO (default /home/claude/gtd), GTD_LAVORO (default /home/claude/lavoro).
GTD_CONSUMO_RAMO=<ramo>: prova tecnica, la riga va su quel ramo con "prova": true e mai sul ramo principale.
Ultima riga: "Consumo: registrato ..." oppure "Consumo: non registrato - <motivo>"."""
import datetime as dt
import json
import os
import re
import subprocess
import sys
import zoneinfo

REPO = os.environ.get("GTD_REPO", "/home/claude/gtd")
LAVORO = os.environ.get("GTD_LAVORO", "/home/claude/lavoro")
RAMO_PROVA = os.environ.get("GTD_CONSUMO_RAMO", "").strip()
FILE = "consumi/registro.json"
PESI = {"input": 1, "cacheWrite": 2, "cacheRead": 0.1, "output": 5}
# gruppi del sistema -> voci della pagina (ciò che non è qui: un connettore se comincia per mcp__, altrimenti "altro")
VOCI = {"instructions": "istruzioni", "person": "testo", "claude": "testo", "summary": "testo",
        "WebSearch": "web", "WebFetch": "web", "Agent": "agenti", "Task": "agenti",
        "Bash": "comandi", "Read": "comandi", "Write": "comandi", "Edit": "comandi", "Glob": "comandi", "Grep": "comandi",
        "mcp__container": "comandi", "NotebookEdit": "comandi"}


def git(*a, timeout=120):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True, timeout=timeout)


def leggi_json(testo):
    """Il JSON del consumo, anche se incollato con altro testo attorno (si prende il primo oggetto che ha "tokens")."""
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


def riga_da(uso):
    t = uso["tokens"]
    tok = {k: int(t.get(k, 0) or 0) for k in PESI}
    if not any(tok.values()):
        raise ValueError("token tutti a zero")
    voci, conn, chiamate = {}, {}, {}
    for g in uso.get("groups") or []:
        nome, q, c = str(g.get("group", "")), float(g.get("percent", 0) or 0), int(g.get("calls", 0) or 0)
        if nome.startswith("mcp__") and nome not in VOCI:
            n = nome[5:].replace("_", " ").strip() or "connettore"
            conn[n] = round(conn.get(n, 0) + q, 1)
            chiamate[n] = chiamate.get(n, 0) + c
            continue
        v = VOCI.get(nome, "altro")
        voci[v] = round(voci.get(v, 0) + q, 1)
        if nome in ("WebSearch", "WebFetch", "Agent", "Task"):
            chiamate[nome] = chiamate.get(nome, 0) + c
    riga = {"richieste": int(uso.get("requests", 0) or 0), "token": tok,
            "pesati": round(sum(tok[k] * PESI[k] for k in PESI)), "quote": voci, "connettori": conn, "chiamate": chiamate}
    return riga


def edizione():
    """Numero, data e ora di uscita dell'ultima edizione pubblicata; durata dal primo file della cartella di lavoro."""
    out = {}
    try:
        u = json.load(open(os.path.join(REPO, "dati", "uscite.json"), encoding="utf-8"))[-1]
        out.update(n=u["n"], d=u["d"], ora=u.get("ora"))
    except Exception:
        pass
    roma = zoneinfo.ZoneInfo("Europe/Rome")
    ora = dt.datetime.now(roma)
    out.setdefault("d", ora.date().isoformat())
    out["giorno"] = ora.date().isoformat()          # il giorno in cui l'attività è girata (diverso da "d" in una prova)
    try:
        primi = [os.path.getmtime(os.path.join(LAVORO, f)) for f in os.listdir(LAVORO)]
        if primi:
            out["durata_min"] = round((ora.timestamp() - min(primi)) / 60)
    except Exception:
        pass
    return out


def salva(riga):
    p = os.path.join(REPO, FILE)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    try:
        reg = json.load(open(p, encoding="utf-8"))
        assert isinstance(reg, list)
    except Exception:
        reg = []
    reg = [x for x in reg if not (x.get("giorno") == riga.get("giorno") and x.get("n") == riga.get("n")
                                  and bool(x.get("prova")) == bool(riga.get("prova")))]
    reg.append(riga)
    reg.sort(key=lambda x: (x.get("giorno", ""), x.get("n") or 0))
    json.dump(reg, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    return len(reg)


def pubblica(riga):
    ramo = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if os.environ.get("GTD_PROVA") == "1":
        return "scritto, nessun push (GTD_PROVA=1)"
    if RAMO_PROVA:
        dest = RAMO_PROVA
        if dest == "main":
            return "scritto, nessun push (una prova non va sul ramo principale)"
    elif ramo != "main":
        return f"scritto, nessun push (ramo {ramo})"
    else:
        dest = "main"
    git("config", "user.name", "PaoloGom")
    git("config", "user.email", "PaoloGom@users.noreply.github.com")
    git("add", FILE)
    if git("diff", "--cached", "--quiet").returncode == 0:
        return "nessuna novità da pubblicare"
    n = f"#{riga['n']:03d}" if isinstance(riga.get("n"), int) else riga.get("giorno", "")
    if git("commit", "-q", "-m", f"Consumo {n} - {riga.get('d', '')}".strip(), "--", FILE).returncode != 0:
        return "commit non riuscito"
    for i in (1, 2):
        r = git("push", "origin", f"HEAD:{dest}")
        if r.returncode == 0:
            return f"pubblicato su {dest}"
        if dest == "main" and i == 1:
            git("pull", "--rebase", "origin", "main")
    return "push non riuscito: " + (r.stderr.strip().splitlines() or ["?"])[-1][:120]


def main():
    testo = open(sys.argv[1], encoding="utf-8").read() if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]) else sys.stdin.read()
    riga = riga_da(leggi_json(testo))
    riga = {**edizione(), **riga}
    if RAMO_PROVA:
        riga["prova"] = True
    n = salva(riga)
    esito = pubblica(riga)
    milioni = f"{riga['pesati'] / 1e6:.2f}".replace(".", ",")
    print(f"Consumo: registrato ({milioni} milioni di token pesati, {riga['richieste']} richieste; {n} righe; {esito})")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:   # mai un errore verso l'attività: il registro è un di più
        print(f"Consumo: non registrato - {type(e).__name__}: {str(e)[:160]}")
    sys.exit(0)
