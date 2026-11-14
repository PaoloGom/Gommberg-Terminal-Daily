#!/usr/bin/env python3
"""Collaudo a secco del kit: in meno di un minuto, senza rete e senza modelli, dice se una modifica ha rotto qualcosa.
Si lancia dopo OGNI modifica al kit, prima del commit:   python3 redazione/collaudo.py
Non fa parte del lavoro del mattino e non scrive nulla nel repository (lavora in una cartella temporanea).

Nato il 14/11/2026: la v8.4 aveva lasciato la pagina di riferimento mezza vuota (5 moduli sotto il 90%) e la v8.5 aveva
reso bloccante un controllo che dava 5-6 falsi errori a edizione. Nessuno dei due difetti si vedeva senza una prova
con l'attività vera, che costa tempo e token. Questo collaudo li trova entrambi in pochi secondi.

Cosa controlla:
  1. Sintassi      tutti i .py e i .sh del kit
  2. Avvio         prepara.sh di lunedì, in un giorno qualsiasi e in un giorno senza borsa
  3. Modello       la pagina di riferimento (edizione_modello_v6.py) si impagina in 6 pagine piene e supera i controlli
                   che non dipendono dalle schede del giorno (PDF, riempimento, numeri, scrittura, temi, ripetizioni).
                   Pag. 6 non si giudica sul riempimento: dipende dal registro della scommessa di quella settimana.
  4. Edizione vera l'ultima edizione in redazione/sorgenti/ rifatta con il motore di oggi e passata da TUTTI i controlli.
                   I rossi qui non fanno fallire il collaudo: dicono cosa le regole di oggi avrebbero fermato ieri,
                   e vanno letti (una regola nuova che ferma un'edizione buona è un falso allarme da correggere).
  5. Sito          pagine.py su una copia: file JSON e XML validi, ultima edizione in testa, nessun link interno rotto
  6. Pubblicazione pubblica.sh in modalità prova sulla copia (nessun commit, nessun push)
Esce con 1 se un passo da 1 a 3, 5 o 6 fallisce. --tieni lascia la cartella temporanea per guardare PDF e anteprime."""
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


def impagina(lav, ed, pdf, reg):
    """stato.json (se manca), grafico della scommessa, rendering. Torna (rc, output)."""
    env = {"GTD_REPO": REPO, "GTD_LAVORO": lav}
    sc = os.path.join(R, "scommessa")
    regp = os.path.join(R, "pronostici", reg)
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


def controlli(lav, pdf, n, extra=(), senza_indice=True):
    env = {"GTD_REPO": REPO, "GTD_LAVORO": lav}
    if senza_indice:
        env["GTD_SENZA_INDICE"] = "1"
    rc, out = esegui(["bash", os.path.join(R, "controlli_tutti.sh"), pdf, str(n), *extra], cwd=lav, env=env)
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
    for f in sorted(glob.glob(os.path.join(R, "*.py")) + glob.glob(os.path.join(R, "scommessa", "*.py"))):
        rc, out = esegui([sys.executable, "-c", f"import ast,sys; ast.parse(open(sys.argv[1], encoding='utf-8').read())", f])
        if rc:
            male.append(os.path.basename(f) + ": " + out.strip().splitlines()[-1][:80])
    for f in sorted(glob.glob(os.path.join(R, "*.sh"))):
        rc, out = esegui(["bash", "-n", f])
        if rc:
            male.append(os.path.basename(f) + ": " + out.strip()[:80])
    esito("Sintassi", not male, "; ".join(male) or "tutti i .py e i .sh del kit")


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
         "EUR/USD": ("eurusd", "FX"), "Brent future": ("brent", "COMM"), "VIX": ("vix", "USA")}
# come si chiamano le stesse serie nelle tabelle del modello: così il controllo dei numeri confronta anche la tabella dei
# mercati con il nastro di prima pagina (il 14/11 il modello aveva l'Euro Stoxx 50 a 6.190,37 nel nastro e 6.162,90 in tabella)
ETICHETTE = {"ACWI": "MSCI ACWI (ETF, $)", "S&P 500": "S&P 500", "Euro Stoxx 50": "Euro Stoxx 50", "Treasury 10 anni": "Treasury 10 anni",
             "EUR/USD": "EUR/USD", "Brent future": "Brent future", "VIX": "VIX (volatilità attesa)"}
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
    dati["serie"]["VIX"]["tipo_var"] = "punti"
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


# ---------------------------------------------------------------- 4. edizione vera
def passo_edizione_vera():
    cartelle = sorted(d for d in glob.glob(os.path.join(R, "sorgenti", "20*")) if os.path.exists(os.path.join(d, "edizione.py"))
                      and os.path.exists(os.path.join(d, "dati.json")))
    if not cartelle:
        print("[--] Edizione vera: nessun sorgente in redazione/sorgenti/ (si attiva dalla prima uscita con pubblica.sh v8.7)")
        return
    src = cartelle[-1]
    data = os.path.basename(src)
    lav = os.path.join(TMP, "vera")
    kit(lav)
    for f in os.listdir(src):
        shutil.copy(os.path.join(src, f), os.path.join(lav, f"edizione_{data}.py" if f == "edizione.py" else f))
    fatti = os.path.join(R, "fatti", data + ".json")
    if os.path.exists(fatti):
        shutil.copy(fatti, os.path.join(lav, "fatti.json"))
    ed = os.path.join(lav, f"edizione_{data}.py")
    reg = re.search(r'^REG = "([^"]+)"', open(ed, encoding="utf-8").read(), re.M).group(1)
    pdf = os.path.join(lav, "vera.pdf")
    rc, out = impagina(lav, ed, pdf, reg)
    if rc or not os.path.exists(pdf):
        return esito(f"Edizione vera del {data}: impaginazione", False, out.strip().splitlines()[-1][:160] if out.strip() else "nessun PDF")
    pagine = int(re.search(r"Pages:\s+(\d+)", esegui(["pdfinfo", pdf])[1]).group(1))
    esito(f"Edizione vera del {data}: impaginazione con il motore di oggi", pagine == 6, f"{pagine} pagine")
    voci = json.load(open(os.path.join(REPO, "edizioni.json"), encoding="utf-8"))
    n = next((v["numero"] for v in voci if v["data"] == data), G.numero(dt.date.fromisoformat(data)))
    stato, out = controlli(lav, pdf, n, senza_indice=not any(v["data"] == data for v in voci))
    rossi = [k for k, v in stato.items() if v == "ROSSO"]
    if rossi:
        print(f"[leggi] Edizione vera del {data}: le regole di oggi fermerebbero {', '.join(rossi)}:")
        for r in [x for x in out.splitlines() if x.startswith(("ERRORE", "- "))][:8]:
            print("        " + r[:170])
        NOTE.append(f"edizione del {data}: rossi in {', '.join(rossi)}")
    else:
        print(f"[ok] Edizione vera del {data}: tutti i controlli verdi")


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
    esito("Sito: dati, feed, mappa e link interni", not male, "; ".join(male)[:300] or
          f"{len(pagine)} pagine, ultima edizione n. {ultimo}")
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
    try:
        passo_sintassi()
        passo_avvio()
        passo_modello()
        passo_edizione_vera()
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
