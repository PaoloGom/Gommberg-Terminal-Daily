#!/usr/bin/env python3
"""Collaudo del kit: in un paio di minuti, senza rete e senza modelli, dice se una modifica ha rotto qualcosa, anche lontano
da dove si è messo mano. Si lancia dopo OGNI modifica, prima del commit:   python3 redazione/collaudo.py
È il cancello del rilascio: redazione/rilascia.sh porta il lavoro sul ramo principale solo se esce con 0, e GitHub lo
rilancia a ogni push sul ramo di rilascio (.github/workflows/collaudo.yml). Non fa parte del lavoro del mattino e non
scrive nulla nel repository (lavora in una cartella temporanea), salvo con --atteso e --campione.

Nato il 14/11/2026: la v8.4 aveva lasciato la pagina di riferimento mezza vuota (5 moduli sotto il 90%) e la v8.5 aveva
reso bloccante un controllo che dava 5-6 falsi errori a edizione. Dal 21/11/2026 (G-39) è anche la rete di non
regressione: uno sviluppo su A che cambia Z si vede qui, prima dei lettori.

Cosa controlla:
  1. Sintassi      tutti i .py e i .sh del kit
  2. Avvio         prepara.sh di lunedì, in un giorno qualsiasi e in un giorno senza borsa
  3. Modello       la pagina di riferimento (edizione_modello_v6.py) si impagina in 6 pagine piene e supera i controlli
                   che non dipendono dalle schede del giorno (PDF, riempimento, numeri, scrittura, temi, ripetizioni).
                   Pag. 6 non si giudica sul riempimento: dipende dal registro della scommessa di quella settimana.
  4. Rete          le edizioni campione di redazione/rete/ rifatte dai loro sorgenti con il kit di oggi lungo la catena
                   del mattino (impaginazione, controlli, voce dell'indice) e confrontate con l'atteso: testo del PDF,
                   esito dei controlli, voce di edizioni.json, email della newsletter, numeri del pannello.
                   OGNI differenza ferma il collaudo: o è un guasto, e si corregge, o è voluta, e allora si rilancia con
                   --atteso, che riscrive l'atteso e stampa che cosa è cambiato (va nel commit e nel resoconto del rilascio).
                   Poi l'ultima edizione uscita, se non è già un campione: qui i rossi dei controlli non fermano, dicono
                   che cosa le regole di oggi avrebbero fermato ieri (una regola nuova che ferma un'edizione buona è un
                   falso allarme da correggere).
  5. Sito          pagine.py su una copia: file JSON e XML validi, ultima edizione in testa, nessun link interno rotto;
                   le pagine generate sono identiche a quelle nel repository (se pagine.py cambia, le pagine si
                   rigenerano nello stesso commit); costruisci.py prepara il sito pubblico senza avvisi
  6. Pubblicazione pubblica.sh in modalità prova sulla copia (nessun commit, nessun push)
Esce con 1 se un passo fallisce. --tieni lascia la cartella temporanea per guardare PDF e anteprime.

La rete (redazione/rete/). Un campione è un'edizione vera congelata: sorgenti/ (il testo scritto e i dati di quel
mattino), fatti.json, pagella.json e atteso/ (ciò che deve uscire). rete/mondo/ è il mondo di quei giorni: l'indice delle
edizioni e i registri della scommessa com'erano. Il collaudo rifà ogni campione in un repository "ombra": il kit di
OGGI con il mondo di ALLORA. Così un campione dà lo stesso risultato anche tra un anno, e cambia solo se cambia il kit.
  --campione AAAA-MM-GG   congela come campione un'edizione di redazione/sorgenti/ (deve rifarsi identica al pubblicato)
  --atteso                riscrive l'atteso dei campioni che differiscono: solo per differenze volute
La rete cresce a ogni rilascio: un guasto sfuggito diventa un campione o un controllo in più. Quando il formato
dell'edizione cambia tanto che un campione vecchio non si impagina più, lo si sostituisce con uno nuovo."""
import csv
import datetime as dt
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.dom.minidom

R = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(R)
TMP = tempfile.mkdtemp(prefix="gtd_collaudo_")
ROSSI, NOTE = [], []
sys.path.insert(0, R)
# Le variabili GTD_ di chi lancia il collaudo (GTD_PROVA di rilascia.sh, GTD_REPO di una sessione del mattino...) non devono
# arrivare al kit in prova: il collaudo prova QUESTO repository, e ogni passo dichiara le sue.
for _k in [k for k in os.environ if k.startswith("GTD_")]:
    del os.environ[_k]
import giorni as G  # noqa: E402


def esegui(cmd, cwd=None, env=None, timeout=300):
    e = dict(os.environ, **(env or {}))
    p = subprocess.run(cmd, cwd=cwd, env=e, capture_output=True, text=True, errors="replace", timeout=timeout)
    return p.returncode, (p.stdout + p.stderr)


def esito(nome, ok, dettaglio=""):
    print(f"[{'ok' if ok else 'ROSSO'}] {nome}" + (f": {dettaglio}" if dettaglio else ""))
    if not ok:
        ROSSI.append(nome)


def kit(dest):
    os.makedirs(dest, exist_ok=True)
    for f in glob.glob(os.path.join(R, "*.py")):
        if not os.path.basename(f).startswith("edizione_modello_20"):
            shutil.copy(f, dest)


def serie(chiave, prima_del, n=4):
    p = os.path.join(R, "scommessa", "dati", chiave + ".csv")
    if not os.path.exists(p):
        return []
    r = [(d, float(v)) for d, v in list(csv.reader(open(p, encoding="utf-8")))[1:] if d < prima_del]
    return r[-n:]


def impagina(lav, ed, pdf, reg, repo=None):
    """stato.json (se manca), grafico della scommessa, rendering. Torna (rc, output).
    repo: il repository da cui leggere kit e registri (questo; per un campione della rete, la sua ombra)."""
    repo = repo or REPO
    env = {"GTD_REPO": repo, "GTD_LAVORO": lav}
    sc = os.path.join(repo, "redazione", "scommessa")
    regp = os.path.join(repo, "redazione", "pronostici", reg)
    if not os.path.exists(os.path.join(lav, "stato.json")) and not os.path.exists(os.path.join(lav, "verdetto.json")):
        rc, out = esegui([sys.executable, "valuta.py", "--settimana", regp, "--attuali", os.path.join(lav, "attuali.json"),
                          "--json", os.path.join(lav, "stato.json")], cwd=sc, env=env)
        if rc:
            return rc, "valuta.py: " + out[-300:]
    arg = [sys.executable, "grafico.py", regp, os.path.join(lav, "c_forecast.png")]
    if os.path.exists(os.path.join(lav, "stato.json")):
        arg.append(os.path.join(lav, "stato.json"))
    esegui(arg, cwd=sc, env=dict(env, GTD_ALTO_GRAFICO="2.9"))
    return esegui([sys.executable, ed, lav, pdf], cwd=lav, env=env)


def controlli(lav, pdf, n, extra=(), senza_indice=True, repo=None):
    repo = repo or REPO
    env = {"GTD_REPO": repo, "GTD_LAVORO": lav}
    if senza_indice:
        env["GTD_SENZA_INDICE"] = "1"
    rc, out = esegui(["bash", os.path.join(repo, "redazione", "controlli_tutti.sh"), pdf, str(n), *extra], cwd=lav, env=env)
    stato, perche, ultimo = {}, {}, None
    for riga in out.splitlines():
        m = re.match(r"\[(ok|ROSSO|avviso)\] ([^:(]+)", riga)
        if m:
            ultimo = m.group(2).strip()
            stato[ultimo] = m.group(1)
        elif ultimo and riga.startswith(("ERRORE", "- ")):
            perche.setdefault(ultimo, riga)          # il primo errore di ogni controllo
    controlli.perche = perche
    return stato, out


# ---------------------------------------------------------------- 1. sintassi
def passo_sintassi():
    male = []
    # Anche con i Python meno recenti che si trovano: l'attività può girare su una versione più vecchia di questa, e
    # una sintassi nuova (per esempio una barra rovesciata dentro le graffe di una f-string) lì è un errore.
    interpreti = [sys.executable] + [p for p in (shutil.which("python3.10"), shutil.which("python3.11")) if p]
    for f in sorted(glob.glob(os.path.join(R, "*.py")) + glob.glob(os.path.join(R, "scommessa", "*.py"))):
        for py in interpreti:
            rc, out = esegui([py, "-c", "import ast,sys; ast.parse(open(sys.argv[1], encoding='utf-8').read())", f])
            if rc:
                male.append(os.path.basename(f) + f" ({os.path.basename(py)}): " + out.strip().splitlines()[-1][:80])
                break
    for f in sorted(glob.glob(os.path.join(R, "*.sh"))):
        rc, out = esegui(["bash", "-n", f])
        if rc:
            male.append(os.path.basename(f) + ": " + out.strip()[:80])
    esito("Sintassi", not male, "; ".join(male) or f"tutti i .py e i .sh del kit ({len(interpreti)} versioni di Python)")


# ---------------------------------------------------------------- 2. avvio
def passo_avvio():
    voci = json.load(open(os.path.join(REPO, "edizioni.json"), encoding="utf-8"))
    d = dt.date.fromisoformat(max(v["data"] for v in voci)) + dt.timedelta(days=1)
    lun = next(x for x in (d + dt.timedelta(days=k) for k in range(30)) if x.weekday() == 0 and G.uscita(x))
    mar = next(x for x in (lun + dt.timedelta(days=k) for k in range(1, 30)) if G.uscita(x) and not G.primo_della_settimana(x))
    chiuso = next(x for x in (d + dt.timedelta(days=k) for k in range(400)) if not G.uscita(x))
    male = []
    for nome, giorno, atteso in (("lunedì", lun, "APP_LUNEDI.md"), ("giorno qualsiasi", mar, "edizione #"),
                                 ("senza borsa", chiuso, "NIENTE EDIZIONE")):
        rc, out = esegui(["bash", os.path.join(R, "prepara.sh"), giorno.isoformat()],
                         env={"GTD_REPO": REPO, "GTD_LAVORO": os.path.join(TMP, "avvio")})
        if rc or atteso not in out or "Traceback" in out:
            male.append(f"{nome} {giorno}: manca '{atteso}' ({out.strip().splitlines()[-1][:70] if out.strip() else 'nessuna uscita'})")
        if len(out.splitlines()) > 23:
            male.append(f"{nome}: {len(out.splitlines())} righe (massimo 23)")
    esito("Avvio (prepara.sh)", not male, "; ".join(male) or f"lunedì {lun:%d/%m}, {mar:%d/%m}, chiuso {chiuso:%d/%m}")


# ---------------------------------------------------------------- 3. modello
SERIE = {"ACWI": ("acwi", "USA"), "S&P 500": ("spx", "USA"), "Euro Stoxx 50": ("sx5e", "EU"), "Treasury 10 anni": ("ust10", "UST"),
         "EUR/USD": ("eurusd", "FX"), "Brent future": ("brent", "COMM"), "Oro future": ("oro", "COMM")}
# come si chiamano le stesse serie nelle tabelle del modello: così il controllo dei numeri confronta anche la tabella dei
# mercati con il nastro di prima pagina (il 14/11 il modello aveva l'Euro Stoxx 50 a 6.190,37 nel nastro e 6.162,90 in tabella)
ETICHETTE = {"ACWI": "MSCI ACWI (ETF, $)", "S&P 500": "S&P 500", "Euro Stoxx 50": "Euro Stoxx 50", "Treasury 10 anni": "Treasury 10 anni",
             "EUR/USD": "EUR/USD", "Brent future": "Brent future", "Oro future": "Oro (future, $/oncia)"}
INDIPENDENTI = ["PDF e indice", "Numeri contro dati.json", "Scrittura", "Temi di prima pagina", "Ripetizioni", "Anteprima"]


def passo_modello():
    lav = os.path.join(TMP, "modello")
    kit(lav)
    src = open(os.path.join(R, "edizione_modello_v6.py"), encoding="utf-8").read()
    a, m, g = map(int, re.search(r"^OGGI = dt\.date\((\d+), (\d+), (\d+)\)", src, re.M).groups())
    oggi = dt.date(a, m, g)
    reg = re.search(r'^REG = "([^"]+)"', src, re.M).group(1)
    # dati del giorno ricostruiti dalle serie della scommessa (chiusure vere): bastano al ticker e al controllo dei numeri
    dati = {"oggi": oggi.isoformat(), "ora_roma": "09:05", "macro": [], "serie": {}}
    for nome, (k, mercato) in SERIE.items():
        dati["serie"][nome] = {"mercato": mercato, "tipo": "chiusura", "etichette": [ETICHETTE[nome]],
                               "ultimi": [[d, v, None] for d, v in reversed(serie(k, oggi.isoformat()))]}
    json.dump(dati, open(os.path.join(lav, "dati.json"), "w", encoding="utf-8"), ensure_ascii=False)
    strumenti = json.load(open(os.path.join(R, "pronostici", reg), encoding="utf-8"))["strumenti"]
    att = {k: [s[-1][1], s[-1][0]] for k in strumenti for s in [serie(k, oggi.isoformat())] if s}
    json.dump(att, open(os.path.join(lav, "attuali.json"), "w"))
    fatti = os.path.join(R, "fatti", oggi.isoformat() + ".json")
    if os.path.exists(fatti):
        shutil.copy(fatti, os.path.join(lav, "fatti.json"))
    ed = os.path.join(lav, f"edizione_{oggi.isoformat()}.py")
    shutil.copy(os.path.join(lav, "edizione_modello_v6.py"), ed)
    pdf = os.path.join(lav, "modello.pdf")
    rc, out = impagina(lav, ed, pdf, reg)
    if rc or not os.path.exists(pdf):
        return esito("Modello: impaginazione", False, out.strip().splitlines()[-1][:160] if out.strip() else "nessun PDF")
    pagine = int(re.search(r"Pages:\s+(\d+)", esegui(["pdfinfo", pdf])[1]).group(1))
    esito("Modello: impaginazione", pagine == 6, f"{pagine} pagine")
    riemp = json.load(open(os.path.join(lav, "riempimento.json"), encoding="utf-8"))
    scarsi = [s for s in riemp.get("scarsi", []) if not s.startswith("pag. 6")]
    esito("Modello: pagine e moduli pieni", not scarsi, "; ".join(x[:70] for x in scarsi[:4]) or
          "pag. 1-5 e tutti i moduli (pag. 6 non giudicata: dipende dal registro della settimana)")
    stato, out = controlli(lav, pdf, G.numero(oggi), ["--prima-della-revisione"])
    for nome in INDIPENDENTI:
        chiave = next((k for k in stato if k.startswith(nome)), None)
        if stato.get(chiave) != "ok":
            esito(f"Modello: {nome}", False, controlli.perche.get(chiave, "controllo non eseguito")[:170])
    if all(stato.get(next((k for k in stato if k.startswith(n)), ""), "") == "ok" for n in INDIPENDENTI):
        esito("Modello: controlli", True, ", ".join(INDIPENDENTI) + " (Fatti e Contenuti non giudicati: servono le schede del giorno)")


# ---------------------------------------------------------------- 4. rete di non regressione
RETE = os.path.join(R, "rete")
MONDO = os.path.join(RETE, "mondo")
ATTESO = ("pdf.txt", "controlli.txt", "voce.json", "email.html", "esito.json")


def campioni():
    return sorted(d for d in glob.glob(os.path.join(RETE, "20*")) if os.path.isdir(os.path.join(d, "sorgenti")))


def ombra(camp, dest):
    """Il repository come lo vede un campione: il kit di OGGI (codice e regole) con il mondo di QUEL giorno (indice delle
    edizioni uscite prima, registro della scommessa, pagella)."""
    data = os.path.basename(camp)
    red = os.path.join(dest, "redazione")
    os.makedirs(red)
    for f in os.listdir(R):
        if os.path.isfile(os.path.join(R, f)) and f != "PROVA_DATA":
            shutil.copy(os.path.join(R, f), red)
    shutil.copytree(os.path.join(R, "scommessa"), os.path.join(red, "scommessa"), ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(os.path.join(MONDO, "pronostici"), os.path.join(red, "pronostici"))
    if os.path.exists(os.path.join(camp, "pagella.json")):
        shutil.copy(os.path.join(camp, "pagella.json"), os.path.join(red, "scommessa", "pagella.json"))
    voci = [v for v in json.load(open(os.path.join(MONDO, "edizioni.json"), encoding="utf-8")) if v["data"] < data]
    json.dump(voci, open(os.path.join(dest, "edizioni.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.symlink(os.path.join(REPO, "pdf"), os.path.join(dest, "pdf"))     # i controlli leggono il PDF dell'edizione prima
    return dest


def rifai(src, data, lav, fatti, repo=None):
    """Un'edizione già scritta, impaginata di nuovo dai suoi sorgenti con il kit di oggi. Torna ciò che si può
    confrontare (pagine, testo, moduli scarsi) oppure {"errore": ...}."""
    kit(lav)
    for f in os.listdir(src):
        if os.path.isfile(os.path.join(src, f)):
            shutil.copy(os.path.join(src, f), os.path.join(lav, f"edizione_{data}.py" if f == "edizione.py" else f))
    if os.path.exists(fatti):
        shutil.copy(fatti, os.path.join(lav, "fatti.json"))
    ed = os.path.join(lav, f"edizione_{data}.py")
    reg = re.search(r'^REG = "([^"]+)"', open(ed, encoding="utf-8").read(), re.M).group(1)
    pdf = os.path.join(lav, "edizione.pdf")
    rc, out = impagina(lav, ed, pdf, reg, repo)
    if rc or not os.path.exists(pdf):
        return {"errore": "impaginazione: " + (out.strip().splitlines()[-1][:160] if out.strip() else "nessun PDF")}
    r = {"pdf": pdf, "reg": reg, "pagine": int(re.search(r"Pages:\s+(\d+)", esegui(["pdfinfo", pdf])[1]).group(1)),
         "testo": subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True, errors="replace").stdout}
    try:
        r["scarsi"] = json.load(open(os.path.join(lav, "riempimento.json"), encoding="utf-8")).get("scarsi", [])
    except Exception:  # noqa: BLE001
        r["scarsi"] = None
    return r


def catena(r, data, lav, repo):
    """Il resto del mattino per un campione, nella sua ombra (dove l'edizione non è ancora nell'indice): primo giro di
    controlli (scrive le sigle), voce dell'indice con edizioni_voce.py, controlli finali."""
    n = G.numero(dt.date.fromisoformat(data))
    red = os.path.join(repo, "redazione")
    controlli(lav, r["pdf"], n, repo=repo)
    sc = next((["--" + k, os.path.join(lav, k + ".json")] for k in ("verdetto", "stato")
               if os.path.exists(os.path.join(lav, k + ".json"))), ["--senza-scommessa"])
    indice = os.path.join(repo, "edizioni.json")
    rc, out = esegui([sys.executable, os.path.join(red, "edizioni_voce.py"), "--pdf", r["pdf"], "--data", data,
                      "--voce", os.path.join(lav, "voce_indice.json"), "--registro", os.path.join(red, "pronostici", r["reg"]),
                      "--sigle", os.path.join(lav, "testo.json"), "--dati", os.path.join(lav, "dati.json"),
                      "--edizioni", indice, *sc], env={"GTD_REPO": repo, "GTD_LAVORO": lav})
    voce = next((v for v in json.load(open(indice, encoding="utf-8")) if v["data"] == data), None)
    if rc or not voce:
        r["errore"] = "voce dell'indice: " + (out.strip().splitlines()[-1][:160] if out.strip() else "non scritta")
        return
    r["voce"] = voce
    out = controlli(lav, r["pdf"], n, senza_indice=False, repo=repo)[1]
    r["controlli"] = out.replace(lav, "<lavoro>").replace(repo, "<repo>")


def a_valle(data, n, qualita):
    """Ciò che il resto del sistema ricava da quell'edizione, con il codice di oggi: l'email (newsletter.py dalla scheda
    e/NNN.json del sito) e i numeri del pannello (pannello.py dalle schede dei fatti e da misure.py)."""
    import newsletter as NL
    import pannello as PN
    ed = json.load(open(os.path.join(REPO, "e", f"{n:03d}.json"), encoding="utf-8"))
    fatti = json.load(open(os.path.join(REPO, "redazione", "fatti", data + ".json"), encoding="utf-8"))
    return "\n".join(NL.componi(ed)) + "\n", {**PN.conta(fatti), **qualita.get(n, {})}


def testi(r, data, qualita):
    """I cinque file dell'atteso, come li produce il kit di oggi."""
    js = lambda x: json.dumps(x, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    email, pannello = a_valle(data, r["voce"]["numero"], qualita)
    return {"pdf.txt": r["testo"], "controlli.txt": r["controlli"], "voce.json": js(r["voce"]), "email.html": email,
            "esito.json": js({"pagine": r["pagine"], "moduli_scarsi": r["scarsi"], "pannello": pannello})}


def differenze(camp, trovato):
    """[(file, righe diverse)] tra l'atteso del campione e ciò che esce oggi."""
    import difflib
    out = []
    for nome in ATTESO:
        p = os.path.join(camp, "atteso", nome)
        atteso = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
        if atteso != trovato[nome]:
            d = [x for x in difflib.unified_diff(atteso.splitlines(), trovato[nome].splitlines(), lineterm="", n=0)
                 if x[:1] in "+-" and x[:3] not in ("+++", "---")]
            out.append((nome, d or ["(solo spazi o a capo finali)"]))
    return out


def qualita_pannello():
    try:
        import pannello as PN
        return PN.qualita()
    except Exception:  # noqa: BLE001
        return {}


def prova_campione(camp, qualita, scrivi=False):
    """Rifà un campione e lo confronta con l'atteso. scrivi=True: l'atteso diventa ciò che esce oggi."""
    data = os.path.basename(camp)
    lav = os.path.join(TMP, "rete_" + data)
    repo = ombra(camp, os.path.join(TMP, "ombra_" + data))
    r = rifai(os.path.join(camp, "sorgenti"), data, lav, os.path.join(camp, "fatti.json"), repo)
    if "errore" not in r:
        catena(r, data, lav, repo)
    if "errore" in r:
        esito(f"Rete, campione del {data}", False, r["errore"])
        return None
    trovato = testi(r, data, qualita)
    diff = differenze(camp, trovato)
    if not diff:
        esito(f"Rete, campione del {data}", True, "PDF, controlli, voce dell'indice, email e pannello uguali all'atteso")
        return trovato
    righe = [f"        {nome}: {len(d)} righe diverse" for nome, d in diff]
    for nome, d in diff:
        righe += ["          " + x[:170] for x in d[:8]] + (["          ..."] if len(d) > 8 else [])
    if scrivi:
        os.makedirs(os.path.join(camp, "atteso"), exist_ok=True)
        for nome, _ in diff:
            open(os.path.join(camp, "atteso", nome), "w", encoding="utf-8").write(trovato[nome])
        print(f"[atteso] Rete, campione del {data}: atteso riscritto in " + ", ".join(n for n, _ in diff))
        NOTE.append(f"atteso del {data} riscritto: {', '.join(n for n, _ in diff)}")
    else:
        esito(f"Rete, campione del {data}", False, "diverso dall'atteso in " + ", ".join(n for n, _ in diff) +
              " (guasto: correggi; voluto: rilancia con --atteso)")
    print("\n".join(righe))
    return trovato


def passo_rete():
    cs = campioni()
    if not cs:
        print("[--] Rete: nessun campione in redazione/rete/ (si crea con --campione AAAA-MM-GG)")
    q = qualita_pannello()
    for camp in cs:
        prova_campione(camp, q, scrivi="--atteso" in sys.argv)
    passo_ultima_edizione({os.path.basename(c) for c in cs})


def passo_ultima_edizione(gia_campioni):
    cartelle = sorted(d for d in glob.glob(os.path.join(R, "sorgenti", "20*")) if os.path.exists(os.path.join(d, "edizione.py"))
                      and os.path.exists(os.path.join(d, "dati.json")))
    if not cartelle or os.path.basename(cartelle[-1]) in gia_campioni:
        return
    src = cartelle[-1]
    data = os.path.basename(src)
    lav = os.path.join(TMP, "ultima")
    r = rifai(src, data, lav, os.path.join(R, "fatti", data + ".json"))
    if "errore" in r:
        return esito(f"Ultima edizione ({data})", False, r["errore"])
    esito(f"Ultima edizione ({data}): impaginazione con il kit di oggi", r["pagine"] == 6, f"{r['pagine']} pagine")
    voci = json.load(open(os.path.join(REPO, "edizioni.json"), encoding="utf-8"))
    n = next((v["numero"] for v in voci if v["data"] == data), G.numero(dt.date.fromisoformat(data)))
    stato, out = controlli(lav, r["pdf"], n, senza_indice=not any(v["data"] == data for v in voci))
    rossi = [k for k, v in stato.items() if v == "ROSSO"]
    if rossi:
        print(f"[leggi] Ultima edizione ({data}): le regole di oggi fermerebbero {', '.join(rossi)}:")
        for x in [x for x in out.splitlines() if x.startswith(("ERRORE", "- "))][:8]:
            print("        " + x[:170])
        NOTE.append(f"edizione del {data}: rossi in {', '.join(rossi)}")
    else:
        print(f"[ok] Ultima edizione ({data}): tutti i controlli verdi")


def nuovo_campione(data):
    """Congela come campione un'edizione uscita. Si accetta solo se, rifatta, dà il PDF e la voce pubblicati: così
    l'atteso di partenza è ciò che i lettori hanno visto davvero."""
    src, camp = os.path.join(R, "sorgenti", data), os.path.join(RETE, data)
    voci = json.load(open(os.path.join(REPO, "edizioni.json"), encoding="utf-8"))
    pubblicata = next((v for v in voci if v["data"] == data), None)
    if not os.path.exists(os.path.join(src, "edizione.py")) or not pubblicata:
        sys.exit(f"Campione {data}: mancano i sorgenti in redazione/sorgenti/ o la voce in edizioni.json")
    if os.path.exists(camp):
        sys.exit(f"Campione {data}: esiste già")
    reg = re.search(r'^REG = "([^"]+)"', open(os.path.join(src, "edizione.py"), encoding="utf-8").read(), re.M).group(1)
    os.makedirs(os.path.join(MONDO, "pronostici"), exist_ok=True)
    shutil.copytree(src, os.path.join(camp, "sorgenti"))
    shutil.copy(os.path.join(R, "fatti", data + ".json"), os.path.join(camp, "fatti.json"))
    if os.path.exists(os.path.join(R, "scommessa", "pagella.json")):
        shutil.copy(os.path.join(R, "scommessa", "pagella.json"), os.path.join(camp, "pagella.json"))
    if not os.path.exists(os.path.join(MONDO, "pronostici", reg)):
        shutil.copy(os.path.join(R, "pronostici", reg), os.path.join(MONDO, "pronostici", reg))
    ip = os.path.join(MONDO, "edizioni.json")                 # l'indice del mondo: si allunga, non si riscrive
    mondo = json.load(open(ip, encoding="utf-8")) if os.path.exists(ip) else []
    fino = max([data] + [os.path.basename(c) for c in campioni()])
    mondo += [v for v in voci if v["data"] <= fino and v["numero"] not in {m["numero"] for m in mondo}]
    json.dump(sorted(mondo, key=lambda v: v["numero"]), open(ip, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    trovato = prova_campione(camp, qualita_pannello(), scrivi=True)
    if not trovato:
        shutil.rmtree(camp)
        sys.exit(f"Campione {data}: non si rifà, non congelato")
    testo = subprocess.run(["pdftotext", "-layout", os.path.join(REPO, pubblicata["file"]), "-"], capture_output=True,
                           text=True, errors="replace").stdout
    diversi = [k for k in sorted(set(pubblicata) | set(json.loads(trovato["voce.json"])))
               if pubblicata.get(k) != json.loads(trovato["voce.json"]).get(k)]
    if testo != trovato["pdf.txt"] or diversi:
        shutil.rmtree(camp)
        sys.exit(f"Campione {data}: rifatto oggi NON è uguale al pubblicato (testo del PDF "
                 f"{'uguale' if testo == trovato['pdf.txt'] else 'diverso'}; campi della voce diversi: {diversi or '-'}). "
                 "Non congelato: un campione deve partire da ciò che i lettori hanno visto.")
    print(f"Campione {data}: congelato in redazione/rete/{data}/ (uguale al pubblicato)")


# ---------------------------------------------------------------- 5. sito  e  6. pubblicazione
def passo_sito():
    copia = os.path.join(TMP, "sito")
    shutil.copytree(REPO, copia, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"))
    rc, out = esegui([sys.executable, os.path.join(copia, "redazione", "pagine.py"), copia])
    if rc:
        return esito("Sito: pagine.py", False, out.strip().splitlines()[-1][:160]), copia
    male = []
    for f in glob.glob(os.path.join(copia, "dati", "*.json")) + glob.glob(os.path.join(copia, "e", "*.json")):
        try:
            json.load(open(f, encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            male.append(f"{os.path.relpath(f, copia)}: {e}"[:90])
    for f in ("feed.xml", "sitemap.xml"):
        try:
            xml.dom.minidom.parse(os.path.join(copia, f))
        except Exception as e:  # noqa: BLE001
            male.append(f"{f}: {e}"[:90])
    voci = json.load(open(os.path.join(copia, "edizioni.json"), encoding="utf-8"))
    ultimo = max(v["numero"] for v in voci)
    try:
        if json.load(open(os.path.join(copia, "dati", "recenti.json"), encoding="utf-8"))["edizioni"][0]["numero"] != ultimo:
            male.append(f"dati/recenti.json non parte dal n. {ultimo}")
    except Exception as e:  # noqa: BLE001
        male.append(f"dati/recenti.json: {e}"[:90])
    for ext in ("html", "json", "png"):
        if not os.path.exists(os.path.join(copia, "e", f"{ultimo:03d}.{ext}")):
            male.append(f"manca e/{ultimo:03d}.{ext}")
    # link interni: ogni href/src locale delle pagine fisse e delle ultime 3 edizioni deve esistere
    pagine = glob.glob(os.path.join(copia, "*.html")) + sorted(glob.glob(os.path.join(copia, "e", "*.html")))[-3:]
    rotti = set()
    for p in pagine:
        html = open(p, encoding="utf-8").read()
        html = re.sub(r"<script\b.*?</script>", "", html, flags=re.S)
        for u in re.findall(r"""(?:href|src)=["']([^"'#?]+)""", html):
            if re.match(r"(?:[a-z]+:|//)", u) or "${" in u or "{" in u:
                continue
            u = u.replace("/Gommberg-Terminal-Daily/", "/", 1) if u.startswith("/Gommberg-Terminal-Daily/") else u
            dest = os.path.normpath(os.path.join(copia if u.startswith("/") else os.path.dirname(p), u.lstrip("/")))
            if not (os.path.exists(dest) or os.path.exists(dest + ".html")):
                rotti.add(f"{os.path.relpath(p, copia)} -> {u}")
    male += sorted(rotti)[:5]
    # le domande dei sei mercati della scommessa: una fonte sola per PDF e sito
    try:
        src = open(os.path.join(R, "scommessa", "pagina6.py"), encoding="utf-8").read()
        dom = dict(re.findall(r'"(spx|sx5e|ust10|eurusd|brent|oro)": "([^"]+)"', src[src.index("DOMANDA = {"):src.index("BREVE = {")]))
        js = open(os.path.join(copia, "assets", "mercati.js"), encoding="utf-8").read()
        male += [f"assets/mercati.js: manca la domanda di pag. 6 per {k} ('{q}')" for k, q in dom.items() if q not in js]
        if len(dom) != 6:
            male.append("pagina6.py: DOMANDA non ha i sei mercati fissi")
    except Exception as e:  # noqa: BLE001
        male.append(f"domande dei mercati: {e}"[:90])
    esito("Sito: dati, feed, mappa e link interni", not male, "; ".join(male)[:300] or
          f"{len(pagine)} pagine, ultima edizione n. {ultimo}")
    # punto fisso: le pagine nel repository sono quelle che pagine.py genera oggi da edizioni.json. Se differiscono, o
    # pagine.py è cambiato senza rigenerarle nello stesso commit, o sono state toccate a mano: i lettori vedrebbero il
    # cambiamento solo alla prossima edizione, lontano da chi l'ha fatto.
    import filecmp
    diversi = set()
    for base in ("e", "dati", "ultima", "feed.xml", "sitemap.xml"):
        for radice in (copia, REPO):
            for d, _, files in os.walk(os.path.join(radice, base)) if os.path.isdir(os.path.join(radice, base)) else [(radice, [], [base])]:
                for f in files:
                    rel = os.path.relpath(os.path.join(d, f), radice)
                    a, b = os.path.join(copia, rel), os.path.join(REPO, rel)
                    # le immagini di anteprima (e/NNN.png) devono esserci, ma non si confrontano byte per byte: lo stesso
                    # disegno esce in byte diversi da una versione all'altra della libreria grafica
                    uguali = os.path.exists(a) and os.path.exists(b) and (rel.endswith(".png") or filecmp.cmp(a, b, shallow=False))
                    if not uguali:
                        diversi.add(rel)
    esito("Sito: pagine generate identiche a quelle nel repository", not diversi,
          (f"{len(diversi)} file diversi dopo pagine.py: " + ", ".join(sorted(diversi)[:6]) +
           " (rigenera con python3 redazione/pagine.py e committa)") if diversi else "e/, dati/, ultima/, feed.xml, sitemap.xml")
    # il sito pubblico: costruisci.py dal repository vero (gli serve git), in una cartella nuova
    if os.path.isdir(os.path.join(REPO, ".git")) or os.path.isfile(os.path.join(REPO, ".git")):
        rc, out = esegui([sys.executable, os.path.join(R, "sito", "costruisci.py"), os.path.join(TMP, "_sito")], cwd=REPO)
        avvisi = [x for x in out.splitlines() if "AVVISO" in x or "ERRORE" in x]
        esito("Sito pubblico (costruisci.py)", rc == 0 and not avvisi,
              "; ".join(avvisi)[:300] or (out.strip().splitlines()[0][:120] if rc == 0 and out.strip() else out.strip()[-160:]))
    return copia


def passo_pubblicazione(copia):
    voci = json.load(open(os.path.join(copia, "edizioni.json"), encoding="utf-8"))
    v = max(voci, key=lambda x: x["numero"])
    lav = os.path.join(TMP, "pubblica")
    os.makedirs(lav, exist_ok=True)
    fatti = os.path.join(copia, "redazione", "fatti", v["data"] + ".json")
    if os.path.exists(fatti):
        shutil.copy(fatti, os.path.join(lav, "fatti.json"))
    for nome in (f"edizione_{v['data']}.py", "dati.json"):       # finti sorgenti: devono finire in redazione/sorgenti/
        open(os.path.join(lav, nome), "w").write("{}")
    pdf = os.path.join(lav, "copia.pdf")
    shutil.copy(os.path.join(copia, v["file"]), pdf)
    rc, out = esegui(["bash", os.path.join(copia, "redazione", "pubblica.sh"), pdf, str(v["numero"]), v["data"],
                      os.path.join(lav, "fatti.json")], env={"GTD_REPO": copia, "GTD_PROVA": "1"})
    srg = os.path.join(copia, "redazione", "sorgenti", v["data"])
    ok = rc == 0 and "Sito: PROVA - nessun push" in out and "git push origin main" in out \
        and os.path.exists(os.path.join(srg, "edizione.py")) and os.path.exists(os.path.join(srg, "dati.json"))
    esito("Pubblicazione a secco (pubblica.sh in prova)", ok,
          "comandi git stampati e non eseguiti, sorgenti archiviati" if ok else out.strip().splitlines()[-1][:160])


def main():
    if "--campione" in sys.argv:
        try:
            return nuovo_campione(sys.argv[sys.argv.index("--campione") + 1])
        finally:
            shutil.rmtree(TMP, ignore_errors=True)
    try:
        passo_sintassi()
        passo_avvio()
        passo_modello()
        passo_rete()
        copia = passo_sito()
        if isinstance(copia, str):
            passo_pubblicazione(copia)
    finally:
        if "--tieni" in sys.argv:
            print(f"Cartella di lavoro: {TMP}")
        else:
            shutil.rmtree(TMP, ignore_errors=True)
    if ROSSI:
        print("COLLAUDO: ERRORI in " + "; ".join(ROSSI))
        sys.exit(1)
    print("COLLAUDO: OK" + (f" (da leggere: {'; '.join(NOTE)})" if NOTE else ""))


if __name__ == "__main__":
    main()
