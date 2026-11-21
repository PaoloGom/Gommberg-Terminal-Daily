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
     Fonti         la regola dei fatti (autori.py, applicata da controlli_fatti.py) su schede costruite apposta: la
                   primaria basta, un'agenzia ripresa da tre siti è un autore solo, l'ultima scelta va dichiarata; e il
                   gancio (gancio_token.py) su una trascrizione costruita: ricerche, pagine aperte, pagine non raggiunte.
     Dati          controlli_dati.py sull'Euro Stoxx 50 scritto in sei modi: EODHD sempre tra le due fonti, quotazioni
                   dei riquadri e fonti discordi fermate (APP_DATI §2b e §6).
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
# ... e nemmeno il file che il gancio lascia in /tmp in una sessione vera: qui il gancio non c'è, salvo dove lo si prova
os.environ["GTD_TOKEN"] = os.path.join(TMP, "nessun_gancio.json")
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
         "EUR/USD": ("eurusd", "FX"), "Brent future": ("brent", "COMM"), "Oro future": ("oro", "COMM"),
         "Treasury 2 anni": ("ust2", "UST"), "VIX": ("vix", "USA")}
# Le serie del modello che non hanno un archivio nella scommessa: i livelli pubblicati nella #004 (15/10/2026), con la
# chiusura precedente e quella di una settimana prima ricavate dalle variazioni stampate allora. Valori di prova: servono solo a impaginare il modello,
# le cui tabelle di pag. 5 le calcola numeri.py dal dati.json, come ogni mattina. Il Kospi ha la sola variazione: la riga non entra.
MODELLO_ALTRE = {
    "Nasdaq": ("USA", "chiusura", [["2026-10-14", 26692.87], ["2026-10-13", 27209.86]], {"2026-10-07": 27377.30}),
    "Russell 2000": ("USA", "chiusura", [["2026-10-14", 2729.53], ["2026-10-13", 2782.40]], {"2026-10-07": 2808.16}),
    "FTSE MIB": ("EU", "chiusura", [["2026-10-14", 49753], ["2026-10-13", 50053]], {"2026-10-07": 49753}),
    "Nikkei 225": ("JP", "intraday", [["2026-10-15", 64425.95], ["2026-10-14", 67745.48]], {"2026-10-08": 69052.47}),
    "Hang Seng": ("HK", "intraday", [["2026-10-15", 24010.00], ["2026-10-14", 24326.24]], {"2026-10-08": 24203.63}),
    "Spread Italia": ("EU", "chiusura", [["2026-10-14", 110], ["2026-10-13", 108]], {}),
}
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
        dati["serie"][nome] = {"mercato": mercato, "tipo": "chiusura", **({"etichette": [ETICHETTE[nome]]} if nome in ETICHETTE else {}),
                               "ultimi": [[d, v, None] for d, v in reversed(serie(k, oggi.isoformat()))]}
    for nome, (mercato, tipo, ultimi, rif) in MODELLO_ALTRE.items():
        dati["serie"][nome] = {"mercato": mercato, "tipo": tipo, "ultimi": [[d, v, None] for d, v in ultimi], "rif": rif,
                               **({"ora": "08:11"} if tipo == "intraday" else {})}
    dati["serie"]["Kospi"] = {"mercato": "KR", "tipo": "intraday", "var": -8.7, "ora": "08:11", "fonte": "Teleborsa", "ultimi": []}
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


# ---------------------------------------------------------------- 3a. scrittura: lessico di casa e fonti tra parentesi
def passo_scrittura():
    """Casi costruiti: i calchi dall'inglese trovati nelle edizioni #019-#030 si fermano, l'italiano giusto che gli somiglia
    passa; la stessa testata due volte tra parentesi in un paragrafo si ferma, due testate diverse no; la nostra lettura
    dichiarata una volta copre le cause del suo paragrafo, come una fonte, e senza l'una né l'altra la causa si ferma."""
    import controlli_testo as T
    lex = [v for v in json.load(open(os.path.join(R, "glossario.json"), encoding="utf-8"))["lessico"]["voci"] if v.get("blocca")]
    ferma = lambda x: any(re.search(rx, x, re.I) for v in lex for rx in v["evita"])
    calchi = ["Nvidia alza la guida per il quarto trimestre", "la guida per il 2027 delude", "il titolo ridà tutto il rialzo di ieri",
              "Kepler alza il giudizio a «comprare»", "La vendita sull'AI si allarga", "La vendita colpisce Taipei e Seul",
              "il debutto non ferma la vendita dell'AI", "dove i chip pesano meno la vendita si ferma", "se tiene, la vendita è finita"]
    giuste = ["Huang valuta un ritorno alla guida di Nvidia", "Cook lascia la guida di Apple", "Nvidia conferma la guidance",
              "Pirelli perde dopo la vendita di un pacchetto da Sinochem", "la vendita delle prime azioni al pubblico",
              "la vendita dei chip alla Cina resta vietata", "il dato ridà fiato alle borse", "le vendite colpiscono Taipei",
              "Kepler alza il giudizio a buy"]
    sfuggiti = [c for c in calchi if not ferma(c)]
    fermate = [c for c in giuste if ferma(c)]
    g = {v["sigla"]: v for v in json.load(open(os.path.join(R, "glossario.json"), encoding="utf-8"))["voci"]}
    sigla = bool(g.get("guidance", {}).get("ovvio"))            # guidance non è una sigla da spiegare
    campi = {"a": "Il titolo cede il 3% (Reuters). Il gruppo taglia i costi (Reuters).",
             "b": "Il titolo cede il 3% (Reuters). Per gli analisti pesa il debito (Bloomberg).", "c": "Nessuna fonte qui."}
    rip = T.fonti_ripetute(campi)
    conta = T.per_testata(" ".join(campi.values()))
    lunga = "Il titolo scende perché il gruppo taglia le stime. Una frase. Un'altra frase. Ancora una. E il calo resta (Reuters)."
    coperta = not T.connettivi(lunga, [lunga]) and bool(T.connettivi("Il titolo scende perché il gruppo taglia le stime. A. B. C. D."))
    letta = "Per noi il mercato sconta il caso peggiore. Una frase. Un'altra frase. Ancora una. Il titolo scende perché il gruppo taglia le stime."
    nuda = "Il titolo scende perché il gruppo taglia le stime. A. B. C. D."
    voce = not T.connettivi(letta, T.coperti_da({"x": letta})) and not T.coperti_da({"x": nuda}) and bool(T.connettivi(nuda)) \
        and not T.connettivi("Spesso un titolo scende perché il gruppo taglia le stime. A. B. C. D.") \
        and not T.connettivi("prima +0,4% Se l'energia passa a monte Sopra: conferma il dato di ieri e pesa sui titoli di Stato. A. B. C.") \
        and bool(T.connettivi("Sotto il 5,10% il titolo scende perché prevale la paura. A. B. C. D."))
    ok = not sfuggiti and not fermate and sigla and len(rip) == 1 and rip[0].startswith("a:") and conta == {"Reuters": 3, "Bloomberg": 1} and coperta and voce
    esito("Scrittura: lessico di casa e fonti tra parentesi", ok,
          f"{len(calchi)} calchi fermati, {len(giuste)} frasi giuste passate, stessa testata due volte in un paragrafo fermata, "
          "lettura dichiarata una volta per paragrafo" if ok else
          "; ".join(x for x in (f"calchi non fermati: {sfuggiti}" if sfuggiti else "", f"frasi giuste fermate: {fermate}" if fermate else "",
                                "" if sigla else "guidance è ancora una sigla da spiegare", f"ripetute: {rip}; conteggio: {conta}",
                                "" if coperta else "una parentesi non copre il suo paragrafo",
                                "" if voce else "la lettura dichiarata non copre il suo paragrafo, o una causa nuda passa") if x)[:300])


# ---------------------------------------------------------------- 3b. fonti: la regola dei fatti e il gancio
def passo_fonti():
    lav = os.path.join(TMP, "fonti")
    os.makedirs(lav, exist_ok=True)

    def fonte(testata, url, **k):
        return {"testata": testata, "url": url, "data_pubblicazione": "2026-11-20", "citazione": "frase della pagina",
                "ricerca": "ricerca che ha trovato la pagina", **k}
    reuters = lambda sito: fonte(f"Reuters ({sito})", f"https://{sito}/a", agenzia="Reuters")   # noqa: E731
    kh = fonte("Korea Herald", "https://www.koreaherald.com/a")
    # (id, sezione, fonti, altri campi, che cosa deve fare il controllo: passa | cerca | respinta | ufficiale)
    casi = [
        # la primaria basta da sola
        ("F01", "top_news", [fonte("BLS", "https://www.bls.gov/a")], {}, "passa"),
        ("F02", "top_news", [fonte("Società (comunicato)", "https://www.ariva.de/a", primaria=True)], {}, "passa"),
        ("F03", "top_news", [fonte("Wells Fargo (SEC)", "https://www.sec.gov/a")], {}, "passa"),
        ("F04", "top_news", [fonte("Blog", "https://sito-x.example/a", primaria="true")], {}, "respinta"),
        ("F05", "top_news", [fonte("Reuters", "https://www.reuters.com/a", primaria=True)], {}, "cerca"),
        # un'agenzia conta una volta, comunque sia scritta e ovunque sia ospitata
        ("F10", "top_news", [reuters("kfgo.com"), reuters("investing.com"), fonte("Reuters", "https://www.reuters.com/a")], {}, "cerca"),
        ("F11", "top_story", [fonte("Reuters (KFGO)", "https://kfgo.com/a"), fonte("Investing.com (Reuters)", "https://www.investing.com/a")], {}, "cerca"),
        ("F12", "agenda", [fonte("KFGO via Reuters", "https://kfgo.com/a"), fonte("Yahoo", "https://finance.yahoo.com/a", agenzia="Thomson REUTERS")], {"data_evento": "2026-11-25"}, "cerca"),
        ("F13", "top_news", [reuters("euronext.com")], {}, "cerca"),
        ("F14", "top_news", [fonte("Borsa Italiana", "https://www.borsaitaliana.it/borsa/notizie/radiocor/a.html"),
                             fonte("Il Sole 24 Ore", "https://www.ilsole24ore.com/a")], {}, "cerca"),
        ("F15", "top_news", [fonte("Teleborsa (Borsa Italiana)", "https://www.borsaitaliana.it/borsa/notizie/teleborsa/a.html")], {}, "cerca"),
        ("F16", "top_news", [fonte("Financial Times", "https://www.ft.com/a"), fonte("Financial Times (RTÉ)", "https://www.rte.ie/a")], {}, "cerca"),
        ("F17", "top_news", [fonte("Reuters", "https://www.reuters.com/a"), fonte("ZeroHedge", "https://www.zerohedge.com/a")], {}, "respinta"),
        ("F18", "top_news", [fonte("Reuters", "https://www.reuters.com/a"), fonte("Business Recorder (Thomson Reuters)", "https://www.brecorder.com/a")], {}, "cerca"),
        ("F19", "top_news", [fonte("Bloomberg", "https://www.bloomberg.com/a"), fonte("Yahoo Finance [Bloomberg News]", "https://finance.yahoo.com/a")], {}, "cerca"),
        ("F06", "top_news", [fonte("AP News", "https://apnews.com/article/a", primaria=True)], {}, "cerca"),
        # due autori diversi
        ("F20", "top_news", [reuters("kfgo.com"), fonte("AP (KSAT)", "https://www.ksat.com/a", agenzia="AP")], {}, "passa"),
        ("F21", "top_news", [fonte("Kitco", "https://www.kitco.com/a"), fonte("FXStreet", "https://www.fxstreet.com/a")], {}, "passa"),
        ("F22", "top_news", [fonte("Fortune (Yahoo Finance)", "https://finance.yahoo.com/a"),
                             fonte("TheStreet (Yahoo Finance)", "https://finance.yahoo.com/b")], {}, "passa"),
        ("F23", "top_news", [fonte("Korea Times", "https://www.koreatimes.co.kr/a"), fonte("Korea Herald", "https://www.koreaherald.co.kr/a")], {}, "passa"),
        ("F24", "top_news", [fonte("Yahoo Finance", "https://ca.finance.yahoo.com/a"), fonte("Yahoo", "https://finance.yahoo.com/b")], {}, "respinta"),
        ("F25", "top_news", [fonte("AP Moller-Maersk (comunicato)", "https://www.maersk.com/a"), reuters("kfgo.com")], {}, "passa"),
        ("F26", "top_news", [fonte("Fortune (Yahoo Finance)", "https://finance.yahoo.com/a"), fonte("Yahoo Finance", "http://www.finance.yahoo.com/a/")], {}, "respinta"),
        ("F27", "top_news", [fonte("Fortune", "https://sito-x.example/a"), fonte("TheStreet", "https://sito-x.example/b")], {}, "respinta"),
        ("F28", "top_news", [fonte("The Star", "https://www.thestar.com.my/a"), fonte("Toronto Star", "https://www.thestar.com/a")], {}, "passa"),
        ("F29", "top_news", [fonte("Benzinga (Yahoo Finance)", "https://finance.yahoo.com/a"),
                             fonte("Simply Wall St (Yahoo Finance)", "https://finance.yahoo.com/b")], {}, "passa"),
        # l'ultima scelta: un solo autore affidabile, con la ricerca in più dichiarata
        ("F30", "deep_dive", [kh], {"conferma_cercata": ["samsung sciopero secondo autore"]}, "passa"),
        ("F31", "deep_dive", [kh], {"conferma_cercata": ["Ricerca che ha trovato  la pagina."]}, "cerca"),
        ("F32", "deep_dive", [kh], {"conferma_cercata": "x"}, "cerca"),
        ("F33", "deep_dive", [kh], {"fonte_singola": True}, "cerca"),
        ("F34", "deep_dive", [kh], {"ufficiale_cercato": ["prima ricerca fatta", "seconda ricerca fatta"]}, "cerca"),
        ("F35", "top_news", [fonte("Sito X", "https://sito-x.example/a")], {"conferma_cercata": ["un'altra ricerca vera"]}, "respinta"),
        ("F37", "top_news", [reuters("kfgo.com")], {"tipo": "U", "ufficiale_cercato": ["a", "b"]}, "cerca"),
        ("F36", "deep_dive", [reuters("kfgo.com"), {**reuters("investing.com"), "ricerca": "seconda ricerca fatta apposta"}],
         {"conferma_cercata": ["seconda ricerca fatta apposta"]}, "passa"),
        # a chi non si applica: cause attribuite, memoria già confermata, dati pubblici (regola invariata)
        ("F40", "top_news", [reuters("kfgo.com")], {"tipo": "C"}, "passa"),
        ("MEM-1119-D03", "deep_dive", [reuters("kfgo.com")], {"ripresa": "2026-11-19"}, "passa"),
        ("F42", "mercati", [fonte("Kitco", "https://www.kitco.com/a")], {"fonte_singola": True}, "passa"),
        ("F43", "mercati", [fonte("ANSA", "https://www.ansa.it/a")], {}, "passa"),
        ("F44", "mercati", [fonte("Kitco", "https://www.kitco.com/a")], {}, "respinta"),
        # dati ufficiali di prima pagina riconosciuti anche se non dichiarati (G-06): due autori non bastano, serve il comunicato
        ("G01", "top_news", [reuters("kfgo.com"), fonte("CNBC", "https://www.cnbc.com/a")],
         {"testo": "Cina, ottobre: vendite al dettaglio +0,4% annuo (atteso +0,8%)"}, "ufficiale"),
        ("G02", "top_news", [reuters("kfgo.com"), fonte("Ufficio di statistica", "https://www.bls.gov/a")],
         {"testo": "Stati Uniti: prezzi al consumo +0,4% sul mese (atteso +0,3%)"}, "passa"),
        ("G03", "top_news", [reuters("kfgo.com"), fonte("CNBC", "https://www.cnbc.com/a")],
         {"testo": "Nvidia riferisce martedì: utile per azione atteso 2,47 $, ricavi attesi circa 108,8 mld $"}, "passa"),
        ("G04", "deep_dive", [reuters("kfgo.com"), fonte("CNBC", "https://www.cnbc.com/a")],
         {"testo": "Cina, ottobre: produzione industriale +4,8% annuo (atteso +5,3%)"}, "passa"),
        ("G05", "top_story", [reuters("kfgo.com"), fonte("CNBC", "https://www.cnbc.com/a")],
         {"testo": "Nvidia: ricavi a 115,8 mld $ contro 109,15 attesi", "tipo": "U",
          "ufficiale_cercato": ["Nvidia third quarter results press release", "Nvidia 8-K November 2026 results"]}, "passa"),
        ("G06", "catalizzatori", [fonte("Ufficio di statistica", "https://www.bls.gov/b")],
         {"testo": "Prezzi alla produzione USA: +0,6% sul mese, +3,1% annuo"}, "passa"),
        ("G07", "top_news", [reuters("kfgo.com"), fonte("CNBC", "https://www.cnbc.com/b")],
         {"testo": "I prezzi alla produzione salgono dello 0,6% sul mese e del 3,1% annuo"}, "ufficiale"),
        ("G08", "top_news", [reuters("kfgo.com"), fonte("CNBC", "https://www.cnbc.com/c")],
         {"testo": "Wall Street chiude a +0,6% dopo il dato sui prezzi"}, "passa"),
        # schede scritte male: un problema con il suo id, mai un'eccezione
        ("F50", "top_news", [fonte("Reuters", None)], {}, "respinta"),
        ("F51", "top_news", "https://www.reuters.com/a", {}, "respinta"),
        ("F52", "top_news", [{**kh, "data_pubblicazione": "20/11/2026"}, reuters("kfgo.com")], {}, "respinta"),
        ("F53", "top_news", [fonte("Reuters", "https:/www.reuters.com/a")], {}, "respinta"),
        ("F54", "top_news", [reuters("kfgo.com")], {"testo": 12345}, "respinta"),
    ]
    schede = [{"id": i, "sezione": sez, "testo": f"Fatto di prova {i}", "data_evento": "2026-11-20", "novita": None, "fonti": fo,
               "verifica": "confermato", "trovato": "una frase diversa letta sulla pagina aperta, con quella che segue", **k}
              for i, sez, fo, k, _ in casi] + [None, "voce che non è una scheda"]
    json.dump(schede, open(os.path.join(lav, "fatti.json"), "w", encoding="utf-8"), ensure_ascii=False)
    _, out = esegui([sys.executable, os.path.join(R, "controlli_fatti.py"), os.path.join(lav, "fatti.json"),
                     os.path.join(REPO, "edizioni.json"), "2026-11-23"])
    righe = [r for r in out.splitlines() if r.startswith("- ")]
    nomi = "|".join(re.escape(i) for i, *_ in casi)
    cerca = set(re.findall(nomi, " ".join(r for r in righe if re.match(r"- CERCA (un secondo autore|\(segue\))", r))))
    respinte = {m.group(1) for r in righe for m in [re.match(rf"- ({nomi}):", r)] if m}
    togliere = set(next((r for r in out.splitlines() if r.startswith("DA_TOGLIERE:")), "").split(":", 1)[-1].strip().split(","))
    ufficiali = {m.group(1) for r in righe for m in [re.match(rf"- CERCA ({nomi}): dato ufficiale", r)] if m}
    trovato = {i: "ufficiale" if i in ufficiali else "cerca" if i in cerca else "respinta" if i in respinte else "passa" for i, *_ in casi}
    male = [f"{i}: atteso {att}, esce {trovato[i]}" for i, _, _, _, att in casi if trovato[i] != att]
    male += [f"{i}: va cercata ma sta in DA_TOGLIERE" for i in sorted(cerca & togliere)]
    male += [f"riga oltre 200 byte: {r[:40]}" for r in righe if r.startswith("- CERCA") and len(r.encode()) > 200]
    male += ["eccezione nel controllo"] if "Traceback" in out else []
    # molte schede insieme: le righe restano sotto il taglio di controlli_tutti.sh e nessun id si perde
    molte = [{**schede[5], "id": f"N{k:02d}-con-un-nome-lungo"} for k in range(30)]
    json.dump(molte, open(os.path.join(lav, "molte.json"), "w", encoding="utf-8"), ensure_ascii=False)
    _, out2 = esegui([sys.executable, os.path.join(R, "controlli_fatti.py"), os.path.join(lav, "molte.json"),
                      os.path.join(REPO, "edizioni.json"), "2026-11-23"])
    r2 = [r for r in out2.splitlines() if r.startswith("- CERCA")]
    if any(len(r.encode()) > 200 for r in r2) or len(set(re.findall(r"N\d\d-con-un-nome-lungo", " ".join(r2)))) != 30:
        male.append("con 30 schede le righe CERCA superano i 200 byte o perdono id")
    esito("Fonti: regola dei fatti", not male, "; ".join(male)[:400]
          or f"{len(casi)} casi (primaria, agenzia ripresa da più siti, due autori, ultima scelta dichiarata, dati ufficiali non dichiarati, esenti, schede scritte male)")

    # il gancio, su una trascrizione fatta come quelle di Claude Code: chiamate (tool_use) ed esiti (tool_result)
    def chiama(i, nome, **inp):
        return {"type": "assistant", "message": {"id": "m" + i, "role": "assistant", "model": "prova", "content": [
            {"type": "tool_use", "id": i, "name": nome, "input": inp}], "usage": {"input_tokens": 1, "output_tokens": 1}}}

    def risponde(i, testo, errore=False, lista=True):
        return {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": i, "content": [{"type": "text", "text": testo}] if lista else testo,
             **({"is_error": True} if errore else {})}]}}
    pagina = "testo della pagina " * 40
    tr = [chiama("t1", "WebSearch", query="samsung sciopero secondo autore reuters"), risponde("t1", pagina),
          chiama("t2", "WebFetch", url="https://www.reuters.com/a"), risponde("t2", "La riunione è finita con HTTP 404 e timed out citati nel testo", lista=False),
          chiama("t3", "WebFetch", url="https://www.nasdaq.com/2026/451/a"), risponde("t3", "Request failed with status code 429", True),
          chiama("t4", "WebFetch", url="https://www.websim.it/a"), risponde("t4", "Error: unable to read the page", True),
          chiama("t5", "WebFetch", url="http://websim.it/a/"), risponde("t5", "Error: unable to read the page", True),
          chiama("t6", "WebFetch", url="https://www.fool.com/a"), risponde("t6", "Claude requested permissions to use WebFetch, but you haven't granted it yet.", True),
          chiama("t7", "WebFetch", url="https://www.ansa.it/a"), risponde("t7", "The operation timed out", True),
          chiama("t8", "WebFetch", url="https://www.ansa.it/a"), risponde("t8", pagina),
          chiama("t9", "WebFetch", url="https://finanzen.ch/a"), risponde("t9", "Request failed with status code 403: Forbidden - Access Denied", lista=False),
          chiama("t10", "WebFetch", url="https://www.census.gov/a"), risponde("t10", "Redirect: fetch https://www2.census.gov/a instead"),
          chiama("t11", "Bash", command="echo WebFetch"), risponde("t11", "WebFetch")]
    os.makedirs(os.path.join(lav, "sessione", "subagents"), exist_ok=True)
    open(os.path.join(lav, "sessione", "t.jsonl"), "w", encoding="utf-8").write(
        "riga che non è JSON\n" + "\n".join(json.dumps(x) for x in tr) + "\n")
    ag = [chiama("s1", "WebSearch", query="ricerca dell'agente"), risponde("s1", "Search failed", True),
          chiama("s2", "WebFetch", url="https://www.koreaherald.com/a"), risponde("s2", pagina)]
    open(os.path.join(lav, "sessione", "subagents", "a.jsonl"), "w", encoding="utf-8").write("\n".join(json.dumps(x) for x in ag) + "\n")
    tok = os.path.join(lav, "gtd_token.json")
    p = subprocess.run([sys.executable, os.path.join(R, "gancio_token.py")], capture_output=True, text=True, env=dict(os.environ, GTD_TOKEN=tok),
                       input=json.dumps({"hook_event_name": "PostToolUse", "transcript_path": os.path.join(lav, "sessione", "t.jsonl")}))
    try:
        g = json.load(open(tok, encoding="utf-8"))
        w = g.get("web") or {}
        visto = (w.get("ricerche"), w.get("ricerche_fallite"), w.get("pagine"), sorted((x["sito"], x["motivo"]) for x in w.get("fallite", [])))
    except Exception as e:  # noqa: BLE001
        g, visto = {}, f"{type(e).__name__}: {e}"
    atteso = (2, 1, 8, [("finanzen.ch", "errore 403"), ("fool.com", "negata"), ("nasdaq.com", "limite"), ("websim.it", "errore")])
    import pannello as PN
    riga, sporca = {}, {"n": 1}
    try:
        os.environ["GTD_TOKEN"] = tok
        PN.dal_gancio(riga)
        json.dump({"esiste": True, "richieste": "dieci", "pesati": 5, "web": {"fallite": [None, "a.com"], "pagine": 3}},
                  open(os.path.join(lav, "sporco.json"), "w"))
        os.environ["GTD_TOKEN"] = os.path.join(lav, "sporco.json")
        PN.dal_gancio(sporca)                      # un file del gancio scritto male non lancia eccezioni
        regge = sporca.get("n") == 1
    except Exception:  # noqa: BLE001
        regge = False
    finally:
        os.environ.pop("GTD_TOKEN", None)
    # il riscontro dell'ultima scelta: con il gancio, una ricerca dichiarata ma mai lanciata non passa
    json.dump([{**schede[0], "id": "V1", "fonti": [kh], "conferma_cercata": ["Samsung sciopero: secondo autore"]},
               {**schede[0], "id": "V2", "fonti": [kh], "conferma_cercata": ["non trovato altro"]}],
              open(os.path.join(lav, "dichiarate.json"), "w", encoding="utf-8"), ensure_ascii=False)
    cmd = [sys.executable, os.path.join(R, "controlli_fatti.py"), os.path.join(lav, "dichiarate.json"), os.path.join(REPO, "edizioni.json"), "2026-11-23"]
    con = esegui(cmd, env={"GTD_TOKEN": tok})[1]
    senza = esegui(cmd)[1]
    riscontro = "CERCA V2:" in con and "CERCA V1:" not in con and "CERCA V" not in senza
    ok = p.returncode == 0 and not (p.stdout + p.stderr) and visto == atteso and g.get("richieste") == 13 and regge and riscontro \
        and riga.get("fallite") == 4 and riga.get("aperte") == 4 and len(riga.get("fallite_siti", [])) == 4
    esito("Fonti: gancio (ricerche e pagine non raggiunte)", ok, "4 pagine non raggiunte su 8, 2 ricerche: il pannello le riceve" if ok
          else f"uscita {p.returncode}, visto {visto}, riga {riga}, regge {regge}, riscontro {riscontro}"[:400])


# ---------------------------------------------------------------- 3c. dati: le fonti ammesse dell'Euro Stoxx 50
def passo_dati():
    """controlli_dati.py su una serie dell'Euro Stoxx 50 scritta in sei modi: EODHD è sempre una delle due fonti (salvo
    eodhd_nd), le fonti non ammesse e le fonti discordi fermano il dato (APP_DATI §2b e §6; caso del 19/11/2026)."""
    lav = os.path.join(TMP, "dati")
    os.makedirs(lav, exist_ok=True)
    ultimi = [[d, v, None] for d, v in reversed(serie("sx5e", "2026-11-20"))]
    v0 = ultimi[0][1]
    casi = [("EODHD + dpa-AFX concordi", {"fonte": "EODHD + dpa-AFX", "seconda_fonte": v0}, True),
            ("EODHD da solo", {"fonte": "EODHD", "fonte_singola": True}, True),
            ("EODHD giù, due fonti web", {"fonte": "stoxx.com + dpa-AFX", "seconda_fonte": v0, "eodhd_nd": "non risponde"}, True),
            ("senza EODHD", {"fonte": "dpa-AFX", "fonte_singola": True}, False),
            ("quotazione di un riquadro", {"fonte": "finanzen.at", "fonte_singola": True}, False),
            ("fonti discordi", {"fonte": "EODHD + dpa-AFX", "seconda_fonte": round(v0 * 1.001, 2)}, False)]
    sbagliati = []
    for nome, campi, passa in casi:
        dati = {"oggi": "2026-11-20", "ora_roma": "09:05", "macro": [],
                "serie": {"Euro Stoxx 50": dict({"mercato": "EU", "tipo": "chiusura", "ultimi": ultimi}, **campi)}}
        f = os.path.join(lav, "dati.json")
        json.dump(dati, open(f, "w", encoding="utf-8"), ensure_ascii=False)
        out = esegui([sys.executable, os.path.join(R, "controlli_dati.py"), f])[1]
        fermo = any(l.startswith("- Euro Stoxx 50:") for l in out.splitlines())
        if fermo == passa:
            sbagliati.append(nome)
    esito("Dati: fonti dell'Euro Stoxx 50", not sbagliati,
          f"{len(casi)} casi (EODHD sempre tra le due fonti, quotazioni dei riquadri e fonti discordi fermate)"
          if not sbagliati else "sbagliati: " + ", ".join(sbagliati))


# ---------------------------------------------------------------- 3c. tabelle di pag. 5 calcolate dal codice
def passo_tabelle():
    """Le tabelle dei mercati escono da dati.json e dall'archivio delle chiusure, mai scritte a mano (G-05): sui dati veri del
    20/11 i numeri sono quelli pubblicati, nessuna cella "n.d.", il livello di Seul si ricava dalla variazione; senza la
    chiusura di ieri la riga non entra; l'archivio prende le chiusure e mai il dato di stamattina."""
    import numeri as N
    src = os.path.join(RETE, "2026-11-20", "sorgenti", "dati.json")
    lav = os.path.join(TMP, "tabelle")
    os.makedirs(lav, exist_ok=True)
    T = N.tabelle_da_dati(src, silenzioso=True)
    righe = {r[0]: r for _, rr in T["cruscotto"] + T["cross"] for r in rr}
    male = []
    sp = righe.get("S&amp;P 500") or [""] * 6
    una_sett_fa = dict(serie("spx", "2026-11-13", 9)).get("2026-11-12")           # stessa seduta della settimana prima
    if sp[:4] + sp[5:] != ["S&amp;P 500", "7.175,83", "19/11", "-2,0%", "+4,8%"] or not una_sett_fa or sp[4] != N.var(7175.83, una_sett_fa):
        male.append(f"S&P 500 diverso dal pubblicato (livello, 1 g, anno) o dalla settimana calcolata: {sp}")
    acwi = righe.get("MSCI ACWI (ETF, $)") or [""] * 6
    if "-" in acwi[4:] or acwi[5] != "+4,4%":
        male.append(f"ACWI senza settimana e anno: {acwi}")
    if (righe.get("Kospi*") or ["", ""])[1] != "~4.871" or (righe.get("Treasury 10 anni") or [""] * 3)[1:3] != ["5,04%", "-3 pb"]:
        male.append(f"Kospi ricavato o Treasury: {righe.get('Kospi*')}, {righe.get('Treasury 10 anni')}")
    if any(c == "n.d." for r in righe.values() for c in r) or "su giovedì 12/11 (Asia su venerdì 13/11)" not in T["cruscotto_nota"] or "~ =" not in T["cruscotto_nota"]:
        male.append("una cella n.d. o la nota senza le date di riferimento e il segno ~: " + T["cruscotto_nota"][:120])
    vuoto = N.tabelle_da_dati(src, archivio={}, silenzioso=True)       # senza archivio: Seul non ha la chiusura di ieri
    if any(r[0].startswith("Kospi") for _, rr in vuoto["cruscotto"] for r in rr) or not any("Kospi" in m for m in vuoto["mancanti"]):
        male.append("senza la chiusura di ieri la riga di Seul doveva restare fuori, e dirlo")
    dati = {"oggi": "2026-11-23", "serie": {
        "FTSE MIB": {"mercato": "EU", "tipo": "chiusura", "ultimi": [["2026-11-20", 49500, None]]},
        "Nikkei 225": {"mercato": "JP", "tipo": "intraday", "ultimi": [["2026-11-23", 57000.5, None], ["2026-11-20", 56436.65, None]]},
        "S&P 500": {"mercato": "USA", "tipo": "chiusura", "ultimi": [["2026-11-20", 7200.0, None]]}}}
    f, arch = os.path.join(lav, "dati.json"), os.path.join(lav, "chiusure.csv")
    json.dump(dati, open(f, "w", encoding="utf-8"))
    n1, n2 = N.archivia(f, arch), N.archivia(f, arch)
    scritto = N._archivio(arch)
    if (n1, n2) != (2, 0) or "2026-11-23" in scritto.get("Nikkei 225", {}) or "S&P 500" in scritto or scritto.get("FTSE MIB") != {"2026-11-20": 49500.0}:
        male.append(f"archivio: {n1} e {n2} nuove, {scritto}")
    if len(N.completa("FTSE MIB", {"ultimi": [["2026-11-20", 49500, None]]})) != 2 or len(N.completa("FTSE MIB", {"ultimi": [["2026-11-24", 1, None]]}, {})) != 1:
        male.append("la chiusura precedente si completa solo dalla seduta subito prima")
    esito("Dati: tabelle di pag. 5 calcolate dal codice", not male, "; ".join(male)[:400] or
          "numeri del 20/11 uguali al pubblicato, nessuna n.d., livello ricavato dalla variazione, archivio delle chiusure")


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
        passo_scrittura()
        passo_fonti()
        passo_dati()
        passo_tabelle()
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
