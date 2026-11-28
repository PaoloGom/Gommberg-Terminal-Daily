#!/usr/bin/env python3
"""I numeri del pannello di controllo (pagina pannello/ del sito): una riga per edizione, scritta a ogni uscita.
Non fa parte del giornale e non può fermare l'uscita: esce sempre con 0 e non lancia mai eccezioni. Nessuna chiamata a
modelli o alla rete: costa zero token.

Tre file in pannello/ (più invii.json, di dem.py):
  registro.json   una riga per edizione, scritta da pubblica.sh. Operatività: avvio, uscita ("ora"), durata. Lavoro:
                  schede dei fatti, fonti citate, ricerche. Qualità: le misure di misure.py (parole, parole per frase "fr",
                  quota di frasi oltre 30 parole "lunghe", gergo, quota di schede con fonte primaria "prim" e di livello 1
                  "l1"). Fonti (autori.py, dalle schede): fatti che poggiano su un solo autore senza fonte primaria
                  "fonte_singola", autori diversi per analisi "autori". Kit: versione delle istruzioni "v" e KB letti a
                  ogni avvio. Dal gancio redazione/gancio_token.py (.claude/settings.json, dopo ogni comando Bash), che
                  legge la trascrizione della sessione e lascia tutto in /tmp/gtd_token.json: il consumo ("token",
                  "pesati", "richieste"; provato il 15/11/2026 in una sessione programmata; token pesati = ingresso +
                  2 x scritti in cache + 0,1 x letti dalla cache + 5 x uscita) le pagine aperte davvero
                  ("aperte", anche quelle poi non citate) e quelle non raggiunte ("fallite", il numero, e
                  "fallite_siti", quali e perché: negata, limite, errore).
  taratura.json   le letture vere della pagina Utilizzo dell'app: quanti punti del limite settimanale sono costati quanti
                  minuti di attività, su quale piano. Da qui il tasso con cui la pagina stima i punti di quel piano. Una lettura con "escluso"
                  (il motivo) resta come traccia ma non entra nel tasso; ogni altra lettura deve avere un piano di piani.json.
  piani.json      a mano, non lo scrive questo file: i piani di Claude in uso, ognuno con "piano" (il nome, lo stesso delle
                  letture di taratura), "dal" (inizio, ISO 8601 con il fuso di Roma, AAAA-MM-GGTHH:MM:SS+01:00; assente nel primo; il collaudo ferma il rilascio se manca,
                  è illeggibile o fuori ordine) e "azzeramento"
                  ({giorno, ora}: venerdì 18:00, ora di Roma, confermato da Paolo il 25/11; la scheda "Quanto pesa il Gommberg su ogni piano"
                  lo scrive). Un'edizione è rapportata al piano in vigore quando è uscita; un piano senza letture di taratura mostra
                  i token e i punti a edizione "da misurare". Un piano può avere una "stima" ({di, rapporto, motivo}: quota = quella
                  del piano "di" per il rapporto): la scheda la scrive come stima finché non ci sono letture vere, poi vince la misura.
                  Cambiare piano = una riga in più, mai una modifica alla pagina.

Uso:
  pannello.py --indici <N> <AAAA-MM-GG> [fatti.json]             riga dell'edizione appena pubblicata (lo chiama pubblica.sh)
  pannello.py --storico                                           aggiunge o completa le edizioni già uscite, dal repository
  pannello.py --taratura <punti> <minuti> <piano> "<nota>" [AAAA-MM-GG]   aggiunge una lettura vera
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
        r = json.load(open(os.path.join(REPO, "pannello", nome), encoding="utf-8"))
        return r if isinstance(r, list) else []
    except Exception:
        return []


def scrivi(nome, righe):
    os.makedirs(os.path.join(REPO, "pannello"), exist_ok=True)
    json.dump(righe, open(os.path.join(REPO, "pannello", nome), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))


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
    out = {"schede": schede, "ricerche": len(ricerche), "fonti": len(url)}
    try:                                             # fonte singola e autori per analisi: la definizione è del controllo
        sys.path.insert(0, QUI)
        import autori
        out.update(autori.conta(fatti))
    except Exception:
        pass
    return out


def dal_gancio(riga):
    """Ciò che il gancio ha letto dalla trascrizione, se ha potuto: i token veri, le pagine aperte e quelle non raggiunte."""
    try:
        g = json.load(open(os.environ.get("GTD_TOKEN", "/tmp/gtd_token.json"), encoding="utf-8"))
        g = g if isinstance(g, dict) else {}
    except Exception:
        return
    try:
        if g.get("esiste") and g.get("richieste") and g.get("pesati"):
            riga.update(richieste=int(g["richieste"]), token=g["token"], pesati=int(g["pesati"]))
    except Exception:                                # un file del gancio scritto male non toglie la riga all'edizione
        pass
    try:
        w = g.get("web")
        if isinstance(w, dict) and isinstance(w.get("fallite"), list):
            fallite = [x for x in w["fallite"] if isinstance(x, dict)]
            siti = []
            for x in fallite:
                s = f"{x.get('sito', '?')} ({x.get('motivo', 'errore')})"
                if s not in siti:
                    siti.append(s)
            riga["fallite"] = len(fallite)
            if isinstance(w.get("pagine"), int):
                riga["aperte"] = max(0, w["pagine"] - len(fallite))
            if siti:
                riga["fallite_siti"] = siti[:12]
    except Exception:
        pass


def versione_e_peso(leggi, elenco):
    """Versione scritta in testa alle istruzioni e KB letti per intero a ogni avvio (istruzioni + pagina modello).
    leggi(percorso) dà i byte di un file del kit, elenco() i nomi in redazione/: dal disco o da un commit."""
    out = {}
    try:
        t = leggi("redazione/ISTRUZIONI.md")
        m = re.search(r"v\d[\d.]*", t.split(b"\n", 1)[0].decode("utf-8", "ignore"))
        if m:
            out["v"] = m.group(0).rstrip(".")
        modelli = [len(leggi("redazione/" + f)) for f in elenco() if re.match(r"edizione_modello.*\.py$", f)]
        out["avvio_kb"] = round((len(t) + (max(modelli) if modelli else 0)) / 1024)
    except Exception:
        pass
    return out


QUALITA = {"parole": "parole", "fr": "fr", ">30": "lunghe", "gergo": "gergo", "prim": "prim", "l1": "l1"}


def qualita(ultime=None):
    """Le misure deterministiche di misure.py, per numero di edizione (tutte, o solo le ultime)."""
    import tempfile
    out = {}
    try:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = f.name
        cmd = [sys.executable, os.path.join(QUI, "misure.py"), "--json", tmp] + (["--ultime", str(ultime)] if ultime else [])
        subprocess.run(cmd, capture_output=True, timeout=120, env={**os.environ, "GTD_REPO": REPO})
        for r in json.load(open(tmp, encoding="utf-8")):
            m = re.match(r"#(\d+)", str(r.get("nome", "")))
            if m:
                out[int(m.group(1))] = {v: r[k] for k, v in QUALITA.items() if isinstance(r.get(k), (int, float))}
        os.remove(tmp)
    except Exception:
        pass
    return out


def metti(riga):
    reg = [x for x in carica("registro.json") if x.get("n") != riga["n"]] + [riga]
    scrivi("registro.json", sorted(reg, key=lambda x: x["n"]))
    return len(reg)


def senza_fonte(ed, fatti_p):
    """Gli approfondimenti dell'edizione che nella riga Fonti non hanno una fonte riconoscibile (comunicato, agenzia, grande
    testata: autori.py): {"senza_fonte": quanti, "senza_fonte_pezzi": [chiavi]}. Lo stesso avviso di controlli_fatti.py."""
    sys.path.insert(0, QUI)
    import autori, desk
    qui = os.getcwd()
    try:
        os.chdir(os.path.dirname(os.path.abspath(ed)))
        C = desk._carica(ed)
    finally:
        os.chdir(qui)
    fatti = json.load(open(fatti_p, encoding="utf-8"))
    pezzi = [p for p, _ in autori.approfondimenti_senza_riconoscibile(autori.righe_degli_approfondimenti(C), fatti)]
    return {"senza_fonte": len(pezzi), "senza_fonte_pezzi": pezzi}


def indici(n, data, fatti_p):
    riga = {"n": int(n), "d": data}
    ora = dt.datetime.now(ROMA)
    riga["ora"] = ora.strftime("%H:%M")
    try:
        primo = min(os.path.getmtime(os.path.join(LAVORO, f)) for f in os.listdir(LAVORO))
        riga["avvio"] = dt.datetime.fromtimestamp(primo, ROMA).strftime("%H:%M")
        riga["durata_min"] = round((ora.timestamp() - primo) / 60)
    except Exception:
        riga["durata_min"] = None
    try:
        riga.update(conta(json.load(open(fatti_p, encoding="utf-8"))))
    except Exception:
        pass
    try:                                             # approfondimenti con soli siti minori nella riga Fonti (avviso, G-46)
        riga.update(senza_fonte(os.path.join(LAVORO, f"edizione_{data}.py"), fatti_p))
    except Exception:
        pass
    riga.update(qualita(ultime=1).get(int(n), {}))
    dal_gancio(riga)
    riga.update(versione_e_peso(lambda f: open(os.path.join(REPO, f), "rb").read(),
                                lambda: os.listdir(os.path.join(REPO, "redazione"))))
    k = metti(riga)
    tok = f"{riga['pesati'] / 1e6:.2f} milioni di token pesati" if riga.get("pesati") else "token non misurati"
    print(f"Consumo: registrato (#{int(n):03d}, {riga.get('durata_min')} min, {tok}; {k} righe)")


def storico():
    """Le edizioni già uscite: durata = ora del commit "Edizione #NNN" meno l'avvio programmato (8:58; 9:00 fino al 13/10),
    solo se l'uscita cade tra le 9:05 e le 10:30 (un'edizione rifatta a mano più tardi non ha una durata nota)."""
    ed = json.load(open(os.path.join(REPO, "edizioni.json"), encoding="utf-8"))
    log = subprocess.run(["git", "-C", REPO, "log", "--reverse", "--format=%H %cI %s", "--grep=^Edizione #"],
                         capture_output=True, text=True).stdout.splitlines()
    uscite, commit = {}, {}
    for r in log:
        m = re.match(r"(\S+) (\S+) Edizione #(\d+) - (\d{4}-\d\d-\d\d)", r)
        if m:
            t = dt.datetime.fromisoformat(m.group(2)).astimezone(ROMA)
            if t.date().isoformat() == m.group(4):          # solo il commit del giorno dell'edizione (non le prove)
                uscite.setdefault(int(m.group(3)), t)
                commit.setdefault(int(m.group(3)), m.group(1))

    def dal_commit(h):
        mostra = lambda f: subprocess.run(["git", "-C", REPO, "show", f"{h}:{f}"], capture_output=True).stdout
        nomi = lambda: subprocess.run(["git", "-C", REPO, "ls-tree", "--name-only", h, "redazione/"], capture_output=True,
                                      text=True).stdout.replace("redazione/", "").split()
        return versione_e_peso(mostra, nomi)
    reg = carica("registro.json")
    q = qualita()
    for x in reg:                                             # righe già presenti: si completa solo ciò che manca
        if "v" not in x and x.get("n") in commit:
            x.update(dal_commit(commit[x["n"]]))
        if "fr" not in x:
            x.update(q.get(x.get("n"), {}))
        if "fonte_singola" not in x:                          # le misure delle fonti, dalle schede in archivio
            try:
                c = conta(json.load(open(os.path.join(REPO, "redazione", "fatti", f"{x.get('d')}.json"), encoding="utf-8")))
                x.update({k: c[k] for k in ("fonte_singola", "autori") if k in c})
            except Exception:
                pass
        if "avvio" not in x and x.get("durata_min") is not None and x.get("ora"):
            h, m = map(int, x["ora"].split(":"))
            a = h * 60 + m - int(x["durata_min"])
            x["avvio"] = f"{a // 60:02d}:{a % 60:02d}"
    scrivi("registro.json", reg)
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
        riga.update(dal_commit(commit[n]))
        riga.update(q.get(n, {}))
        riga["ricostruita"] = True
        metti(riga)
        fatte += 1
    print(f"Consumo: storico, {fatte} edizioni aggiunte")


def taratura(punti, minuti, piano, nota, giorno=None):
    nomi = [x.get("piano") for x in carica("piani.json")]
    if nomi and piano not in nomi:                   # una lettura su un piano che piani.json non conosce la pagina non la userebbe
        raise ValueError(f"piano '{piano}' non in pannello/piani.json ({', '.join(map(str, nomi))})")
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
