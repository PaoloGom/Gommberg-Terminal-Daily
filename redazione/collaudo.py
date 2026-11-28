#!/usr/bin/env python3
"""Collaudo del kit: in un paio di minuti, senza rete e senza modelli, dice se una modifica ha rotto qualcosa, anche lontano
da dove si è messo mano. Si lancia dopo OGNI modifica, prima del commit:   python3 redazione/collaudo.py
È il cancello del rilascio: redazione/rilascia.sh porta il lavoro sul ramo principale solo se esce con 0, e GitHub lo
rilancia come cancello finale di pubblica (.github/workflows/collaudo.yml, ramo cancello). Non fa parte del lavoro del mattino e non
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
     Scommessa     il registro misura ogni settimana dalla chiusura vera (partenza = verdetto della settimana prima =
                   serie in scommessa/dati); il lunedì la lettura della settimana ha una fonte sola: pronostico.py
                   accetta lo scenario solo nella forma che pag. 6 stampa, e pag. 6 stampa quello.
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
                   rigenerano nello stesso commit); costruisci.py prepara il sito pubblico senza avvisi; le pagine
                   delle analisi (analisi_sito.py): una per analisi, testo uguale al PDF, link e sitemap, un sorgente
                   rotto che non ferma l'edizione, e un'edizione rifatta da zero che ridà gli stessi file. I grafici
                   si confrontano in ciò che mostrano e non nei byte, che cambiano con la versione di matplotlib: lo
                   stesso verdetto in locale e su GitHub (stesso_grafico, provato da passo_grafici)
  6. Pubblicazione pubblica.sh in modalità prova sulla copia (nessun commit, nessun push); se pagine.py cade l'avviso
                   esce e la pubblicazione prosegue
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
    # I flussi di GitHub: un "#" dentro una condizione non tra virgolette è un commento per YAML e la tronca senza errori
    # (G-57, 23/11: "startsWith(..., 'Edizione #')"). Ogni "if:" deve arrivare intero: parentesi e apici pari.
    try:
        import yaml
    except ImportError:
        yaml = None
        NOTE.append("flussi di GitHub non letti (manca PyYAML)")
    flussi = sorted(glob.glob(os.path.join(REPO, ".github", "workflows", "*.yml")))
    for f in flussi if yaml else []:
        try:
            d = yaml.safe_load(open(f, encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            male.append(os.path.basename(f) + ": YAML non valido, " + str(e).splitlines()[0][:60])
            continue
        conds = []
        for job in (d.get("jobs") or {}).values():
            conds.append(job.get("if"))
            conds += [st.get("if") for st in job.get("steps") or []]
        for c in (str(c) for c in conds if c is not None):
            if c.count("(") != c.count(")") or c.count("'") % 2:
                male.append(os.path.basename(f) + ": condizione troncata (un # non tra virgolette?): " + c[:60])
    esito("Sintassi", not male, "; ".join(male) or f"tutti i .py e i .sh del kit ({len(interpreti)} versioni di Python), {len(flussi) if yaml else 0} flussi di GitHub")


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


def passo_uscite():
    """L'uscita (c) passa da messaggio.py --nessuna: stampa la riga solo per i casi ammessi e con l'errore ricevuto.
    Il 27/11/2026 la corsa del mattino ha rinunciato all'edizione perché aveva pochi fatti verificati."""
    m = [sys.executable, os.path.join(R, "messaggio.py")]
    male = []
    for caso in ("repository", "dati", "pdf", "permesso", "pubblicata"):
        rc, out = esegui(m + ["--nessuna", caso, "--dettaglio", "errore di prova"])
        if rc or not out.startswith("Nessuna edizione oggi: ") or "errore di prova" not in out:
            male.append(f"{caso}: non stampa la riga ({out.strip()[:60]})")
    for nome, arg in (("pochi fatti", ["--nessuna", "pochi fatti verificati", "--dettaglio", "tre giri di raccolta"]),
                      ("motivo vuoto", ["--nessuna"]), ("senza errore", ["--nessuna", "dati"]),
                      ("errore di soli spazi", ["--nessuna", "pdf", "--dettaglio", "  "])):
        rc, out = esegui(m + arg)
        if rc != 1 or "USCITA NON AMMESSA" not in out or "Nessuna edizione oggi" in out or "APP_ERRORI.md" not in out:
            male.append(f"{nome}: doveva fermarsi e dire come si prosegue (codice {rc}: {out.strip()[:60]})")
    esito("Uscite (nessuna edizione solo nei casi ammessi)", not male, "; ".join(male) or "5 casi ammessi, 4 rifiutati")


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
    passa; una testata tra parentesi si ferma ovunque, anche se nuova (la si riconosce dalla riga Fonti), e passa solo con
    l'orario di un livello del mattino; chi dà una causa, nominato nel paragrafo, la copre, e così la nostra lettura
    dichiarata una volta; una sigla che il lettore non conosce vuole le sue parole nella frase, non la parentesi, e detta
    due volte nella stessa frase si ferma; la SEC non si spiega."""
    import controlli_testo as T
    lex = [v for v in json.load(open(os.path.join(R, "glossario.json"), encoding="utf-8"))["lessico"]["voci"] if v.get("blocca")]
    ferma = lambda x: any(re.search(rx, x, re.I) for v in lex for rx in v["evita"])
    calchi = ["Nvidia alza la guida per il quarto trimestre", "la guida per il 2027 delude", "il titolo ridà tutto il rialzo di ieri",
              "Kepler alza il giudizio a «comprare»", "La vendita sull'AI si allarga", "La vendita colpisce Taipei e Seul",
              "il debutto non ferma la vendita dell'AI", "dove i chip pesano meno la vendita si ferma", "se tiene, la vendita è finita",
              "la vendita ha colpito i grandi nomi della tecnologia", "La vendita non ha riguardato solo i chip",
              "Venerdì la vendita si è accelerata con il calo dei listini"]
    giuste = ["Huang valuta un ritorno alla guida di Nvidia", "Cook lascia la guida di Apple", "Nvidia conferma la guidance",
              "Pirelli perde dopo la vendita di un pacchetto da Sinochem", "la vendita delle prime azioni al pubblico",
              "la vendita dei chip alla Cina resta vietata", "il dato ridà fiato alle borse", "le vendite colpiscono Taipei",
              "la vendita di Tim ha pesato sui conti", "le vendite hanno colpito i grandi nomi della tecnologia",
              "Kepler alza il giudizio a buy"]
    sfuggiti = [c for c in calchi if not ferma(c)]
    fermate = [c for c in giuste if ferma(c)]
    g = {v["sigla"]: v for v in json.load(open(os.path.join(R, "glossario.json"), encoding="utf-8"))["voci"]}
    sigla = bool(g.get("guidance", {}).get("ovvio"))            # guidance non è una sigla da spiegare
    nomi = T.NOMI_BASE + T.nomi_da_righe(["Fonti: Kitco, dpa-AFX, Il Sole 24 Ore; chiusure dell'oro future (FMP)."])
    tt = {"a": "Il titolo cede il 3% (Reuters). Il gruppo taglia i costi (Kitco e AFP).",
          "b": "I future del Nasdaq perdono oltre l'1% (Milano Finanza, 07:40).",
          "c": "La Banca del Giappone (BoJ) alza i tassi e l'utile supera le attese (stima LSEG 746,3).",
          "d": "Secondo Reuters la SEC esamina i conti. Il gas sale ad Amsterdam (dpa-AFX)."}
    par = T.fonti_nei_testi(tt, nomi)
    conta = T.per_testata(" ".join(tt.values()), nomi)
    detta = "Per gli operatori sentiti dal Sole 24 Ore l'offerta ha tolto liquidità. Il titolo scende perché il gruppo taglia le stime."
    lunga = "Il titolo scende perché il gruppo taglia le stime. Una frase. Un'altra frase. Ancora una. Lo ha scritto Reuters."
    coperta = not T.connettivi(detta) and not T.connettivi(lunga, T.coperti_da({"x": lunga})) \
        and bool(T.connettivi("Il titolo scende perché il gruppo taglia le stime. A. B. C. D."))
    sg = lambda x: T.sigle("TOP STORY " + x)   # (mai, doppie, spiegate, tra parentesi, due volte)   # noqa: E731
    s1 = sg("Mercoledì esce il PCE, il dato sui prezzi che la Fed guarda di più.")
    s2 = sg("Mercoledì esce il PCE e i mercati aspettano.")
    s3 = sg("L'indice azionario mondiale ACWI (indice azionario mondiale MSCI) perde il 3,5%.")
    s4 = sg("Per l'Agenzia internazionale dell'energia (AIE) l'offerta supera la domanda.")
    s5 = sg("La SEC esamina i conti di Nvidia mentre sale il VIX, l'indice che misura la paura a Wall Street.")
    s6 = sg("Mercoledì esce il PCE (inflazione dei consumi, misura Fed).")
    sigle_ok = (not s1[0] and s1[2] == ["PCE"] and not s1[3]) and bool(s2[0]) and bool(s3[4]) and not (s4[0] or s4[3] or s4[4]) \
        and (not s5[0] and s5[2] == ["VIX"]) and (not s6[0] and s6[3] == ["PCE"] and not s6[4])
    letta = "Per noi il mercato sconta il caso peggiore. Una frase. Un'altra frase. Ancora una. Il titolo scende perché il gruppo taglia le stime."
    nuda = "Il titolo scende perché il gruppo taglia le stime. A. B. C. D."
    voce = not T.connettivi(letta, T.coperti_da({"x": letta})) and not T.coperti_da({"x": nuda}) and bool(T.connettivi(nuda)) \
        and not T.connettivi("Spesso un titolo scende perché il gruppo taglia le stime. A. B. C. D.") \
        and not T.connettivi("prima +0,4% Se l'energia passa a monte Sopra: conferma il dato di ieri e pesa sui titoli di Stato. A. B. C.") \
        and bool(T.connettivi("Sotto il 5,10% il titolo scende perché prevale la paura. A. B. C. D."))
    fonti_ok = par == [("a", "(Reuters)"), ("a", "(Kitco e AFP)"), ("d", "(dpa-AFX)")] and conta == {"Reuters": 1, "Kitco": 1, "AFP": 1, "dpa-AFX": 1}
    # una testata nominata come fonte sta nella riga Fonti del suo pezzo; chi è solo nominato (il Tesoro che fa un'asta) no
    pezzo = lambda ch, apre, perche, fonte: {"chiave": ch, "titolo": ch, "testo": [apre + " Poi il resto."], "perche": perche,  # noqa: E731
                                              "quindi": "Alle 15:30.", "fonte": fonte}
    Cx = {"moduli": [pezzo("a", "Perché l'oro scende? Perché non paga interessi.", "Per Milano Finanza pesa il dollaro.", "Fonti: Kitco."),
                     pezzo("b", "Il titolo cade. Perché proprio oggi? Dipende dai conti.", "Lo scrive Reuters, e il Tesoro mette all'asta i titoli.", "Fonti: Reuters, ANSA."),
                     pezzo("c", "Un rifugio dovrebbe salire quando si ha paura, e invece scende.", "Per gli operatori sentiti dal Sole 24 Ore pesa l'offerta.", "Fonti: Il Sole 24 Ore."),
                     pezzo("d", "La Fed non dovrebbe frenare? Dipende da ciò che guarda.", "Di solito decide sui prezzi.", "Fonti: Federal Reserve.")],
          "top": {"dek": "Secondo Bloomberg il fondo valuta un'offerta."}, "fonti": [("Prima pagina e mercati", "Reuters, ANSA.")]}
    fuori = T.fuori_dalle_fonti(Cx, nomi)
    domande = T.aperture_con_domanda(Cx)
    fonti_ok = fonti_ok and fuori == [("moduli.a.perche", "Milano Finanza"), ("top.dek", "Bloomberg")] and domande == ["a", "b", "d"]
    oro = [v for v in json.load(open(os.path.join(R, "glossario.json"), encoding="utf-8"))["lessico"]["voci"] if "a vendere è chi" in v["termine"]]
    oro_rx = lambda x: any(re.search(rx, x, re.I) for v in oro for rx in v["evita"])   # noqa: E731
    fonti_ok = fonti_ok and bool(oro) and all(oro_rx(x) for x in ("i Treasury fanno da rifugio, l'oro vende", "borse e oro hanno venduto insieme")) \
        and not any(oro_rx(x) for x in ("chi ha comprato oro vende ora le azioni", "le banche centrali hanno venduto oro", "si vende oro per far cassa"))
    ok = not sfuggiti and not fermate and sigla and fonti_ok and coperta and voce and sigle_ok
    esito("Scrittura: lessico di casa, fonti e sigle", ok,
          f"{len(calchi)} calchi fermati, {len(giuste)} frasi giuste passate, testate tra parentesi fermate (anche una nuova), "
          "fonte di un livello del mattino passata, testata nominata e assente dalla riga Fonti fermata, aperture con domanda "
          "contate, \"l'oro vende\" fermato, causa coperta da chi la dà o dalla lettura dichiarata, sigle dette in parole" if ok else
          "; ".join(x for x in (f"calchi non fermati: {sfuggiti}" if sfuggiti else "", f"frasi giuste fermate: {fermate}" if fermate else "",
                                "" if sigla else "guidance è ancora una sigla da spiegare",
                                "" if fonti_ok else f"testate tra parentesi: {par}; conteggio: {conta}; fuori dalle Fonti: {fuori}; domande: {domande}",
                                "" if sigle_ok else f"sigle: {[s1, s2, s3, s4, s5, s6]}",
                                "" if coperta else "chi dà la causa non copre il suo paragrafo, o una causa nuda passa",
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
    eodhd_nd), le fonti non ammesse e le fonti discordi fermano il dato (APP_DATI §2b e §6; caso del 19/11/2026). Più
    due casi sull'età del dato, contata in giorni di uscita (APP_FESTIVI §2)."""
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
    # Un dato fermo da più giorni (G-44): contano i giorni di uscita. Dopo un giorno senza edizione (Natale) la chiusura
    # di tre giorni feriali prima è ancora l'ultima e passa con un avviso; in una settimana qualsiasi è un dato vecchio.
    for nome, giorno, date, passa in (("ultima chiusura prima di Natale, letta il lunedì dopo", "2026-12-28", ("2026-12-23", "2026-12-22"), True),
                                      ("chiusura di tre giorni di uscita prima", "2026-12-14", ("2026-12-09", "2026-12-08"), False)):
        dati = {"oggi": giorno, "ora_roma": "09:05", "macro": [], "serie": {"FTSE MIB": {
            "mercato": "EU", "tipo": "chiusura", "ultimi": [[date[0], 50000, None], [date[1], 50100, None]]}}}
        json.dump(dati, open(f, "w", encoding="utf-8"), ensure_ascii=False)
        out = esegui([sys.executable, os.path.join(R, "controlli_dati.py"), f])[1]
        if any(l.startswith("- FTSE MIB:") for l in out.splitlines()) == passa or (passa and "AVVISO: FTSE MIB: ultimo dato del" not in out):
            sbagliati.append(nome)
    # Una borsa che stamattina ha già chiuso e porta la chiusura di ieri: avviso (chiusa per festività, o manca il dato di
    # oggi). Con la chiusura di oggi, o per un mercato che chiude la sera, nessun avviso.
    for nome, mercato, data, atteso in (("Tokyo ferma a ieri", "JP", "2026-12-10", True), ("Tokyo con la chiusura di oggi", "JP", "2026-12-11", False),
                                        ("Milano con la chiusura di ieri", "EU", "2026-12-10", False)):
        dati = {"oggi": "2026-12-11", "ora_roma": "09:05", "macro": [], "serie": {"Indice di prova": {
            "mercato": mercato, "tipo": "chiusura", "ultimi": [[data, 50000, None], ["2026-12-09", 50100, None]]}}}
        json.dump(dati, open(f, "w", encoding="utf-8"), ensure_ascii=False)
        out = esegui([sys.executable, os.path.join(R, "controlli_dati.py"), f])[1]
        if ("AVVISO: Indice di prova: ultimo dato del" in out) != atteso or "- Indice di prova:" in out:
            sbagliati.append(nome)
    esito("Dati: fonti dell'Euro Stoxx 50", not sbagliati,
          f"{len(casi)} casi (EODHD sempre tra le due fonti, quotazioni dei riquadri e fonti discordi fermate), età del dato "
          "contata in giorni di uscita, borsa asiatica ferma a ieri segnalata"
          if not sbagliati else "sbagliati: " + ", ".join(sbagliati))


# ---------------------------------------------------------------- 3c. tabelle di pag. 5 calcolate dal codice
def passo_tabelle():
    """Le tabelle dei mercati escono da dati.json e dall'archivio delle chiusure, mai scritte a mano (G-05): sui dati veri del
    20/11 i numeri sono quelli pubblicati, nessuna cella "n.d.", il livello di Seul si ricava dalla variazione; senza la
    chiusura di ieri la riga non entra; l'archivio prende le chiusure e mai il dato di stamattina. Con un mercato chiuso
    (G-44) le righe hanno date diverse: intestazione, titoli dei gruppi e note dicono la data di ogni riga e la chiusura
    davvero usata per ogni riferimento, sia quando si ferma un mercato intero (Wall Street) sia quando si ferma una riga
    dentro un gruppo (Tokyo)."""
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
    # Un mercato chiuso: gli stessi dati del 20/11, con le due righe italiane (valori di prova per i riferimenti dello spread)
    base = json.load(open(src, encoding="utf-8"))
    base["serie"]["FTSE MIB"] = {"mercato": "EU", "tipo": "chiusura", "ultimi": [["2026-11-19", 49941, None], ["2026-11-18", 50192, None]]}
    base["serie"]["Spread Italia"] = {"mercato": "EU", "tipo": "chiusura", "ultimi": [["2026-11-19", 106, None], ["2026-11-18", 106, None]],
                                      "rif": {"2026-11-12": 104, "2026-10-19": 101}}

    def chiuso(nome, ferme, senza=()):
        """Le serie in `ferme` restano alla seduta prima, quelle in `senza` mancano: le tabelle e i titoli dei gruppi."""
        dd = json.loads(json.dumps(base))
        for n in ferme:
            dd["serie"][n]["ultimi"] = dd["serie"][n]["ultimi"][1:]
        for n in senza:
            del dd["serie"][n]
        ff = os.path.join(lav, nome + ".json")
        json.dump(dd, open(ff, "w", encoding="utf-8"))
        tt = N.tabelle_da_dati(ff, silenzioso=True)
        return tt, [t for t, _ in tt["cruscotto"]], [t for t, _ in tt["cross"]], {r[0]: r for _, rr in tt["cruscotto"] for r in rr}
    # Wall Street e Treasury chiusi il 19/11: Stati Uniti al 18/11, Europa, cambi e materie prime al 19/11, Asia al 20/11
    U, sx, dx, ru = chiuso("usa_chiusa", ["ACWI", "S&P 500", "Nasdaq", "Russell 2000", "VIX", "Treasury 2 anni", "Treasury 10 anni"])
    if (sx, dx, U["cross_data"]) != (["Mondo e Stati Uniti", "Europa (19/11)", "Asia (20/11)"],
                                     ["Tassi", "Cambi (19/11)", "Materie prime (19/11)", "Volatilità"], "Livello 18/11"):
        male.append(f"Wall Street chiusa, date nei titoli e nell'intestazione: {sx} {dx} {U['cross_data']}")
    if (ru.get("S&amp;P 500") or [""] * 4)[1:4] != ["7.323,63", "18/11", N.var(7323.63, 7340.53)]:
        male.append(f"Wall Street chiusa, S&P 500 fermo alla seduta prima: {ru.get('S&amp;P 500')}")
    if ("1 sett. = su mercoledì 11/11 (Treasury 2 anni e Treasury 10 anni su martedì 10/11; Europa, Spread Italia, EUR/USD e "
            "Materie prime su giovedì 12/11; Asia su venerdì 13/11); da inizio anno = su chiusura 2025.") not in U["cruscotto_nota"]:
        male.append("Wall Street chiusa, la nota non dice la chiusura usata riga per riga: " + U["cruscotto_nota"][:230])
    if not U["cross_nota"].startswith("1 mese = sul 16/10 (Spread Italia, EUR/USD e Materie prime sul 19/10). Spread Italia: dato del 19/11."):
        male.append("Wall Street chiusa, nota di destra: " + U["cross_nota"][:160])
    # Tokyo chiusa stamattina: il Nikkei resta al 19/11 dentro un gruppo che è al 20/11
    K, sx, dx, rk = chiuso("tokyo_chiusa", ["Nikkei 225"])
    if (sx, dx, K["cross_data"]) != (["Mondo e Stati Uniti", "Europa", "Asia (20/11)"], ["Tassi", "Cambi", "Materie prime", "Volatilità"], "Livello 19/11"):
        male.append(f"Tokyo chiusa, date nei titoli e nell'intestazione: {sx} {dx} {K['cross_data']}")
    if (rk.get("Nikkei 225") or [""] * 4)[1:4] != ["59.444,21", "19/11", N.var(59444.21, 59024.28)] \
            or "1 sett. = su giovedì 12/11 (Hang Seng e Kospi su venerdì 13/11)" not in K["cruscotto_nota"] \
            or not K["cruscotto_nota"].endswith(" Nikkei 225: dato del 19/11."):
        male.append(f"Tokyo chiusa, riga o nota: {rk.get('Nikkei 225')} | " + K["cruscotto_nota"][:230])
    # A parità dentro un gruppo vince la data più recente: con Tokyo chiusa e Seul assente il titolo segue Hong Kong
    P, sx, _, _ = chiuso("tokyo_parita", ["Nikkei 225"], senza=["Kospi"])
    if sx[-1] != "Asia (20/11)" or not P["cruscotto_nota"].endswith(" Nikkei 225: dato del 19/11."):
        male.append(f"parità dentro il gruppo Asia: {sx[-1]} | " + P["cruscotto_nota"][-60:])
    # L'intestazione è la data più usata dalle righe, non quella dell'S&P 500: Wall Street chiusa e due righe americane in meno
    M, sx, dx, _ = chiuso("usa_minoranza", ["ACWI", "S&P 500", "Nasdaq", "Russell 2000", "VIX", "Treasury 2 anni", "Treasury 10 anni"],
                          senza=["Nasdaq", "Russell 2000"])
    if (M["cross_data"], sx, dx) != ("Livello 19/11", ["Mondo e Stati Uniti (18/11)", "Europa", "Asia (20/11)"],
                                     ["Tassi (18/11)", "Cambi", "Materie prime", "Volatilità (18/11)"]) \
            or " Spread Italia: dato del 19/11." not in M["cross_nota"]:
        male.append(f"data più usata diversa da quella dell'S&P 500: {M['cross_data']} {sx} {dx} | " + M["cross_nota"][:120])
    # A cavallo d'anno ogni riga dice su quale fine anno è misurata (valori di prova, senza archivio)
    anno = {"oggi": "2027-01-04", "serie": {
        "S&P 500": {"mercato": "USA", "tipo": "chiusura", "ultimi": [["2026-12-31", 7300.0, None], ["2026-12-30", 7280.0, None]],
                    "rif": {"2026-12-24": 7250.0}},
        "Nikkei 225": {"mercato": "JP", "tipo": "chiusura", "ultimi": [["2027-01-04", 58000.0, None], ["2026-12-30", 57500.0, None]],
                       "rif": {"2026-12-28": 57000.0}},
        "Hang Seng": {"mercato": "HK", "tipo": "intraday", "ora": "08:10", "rif": {"2026-12-28": 22000.0},
                      "ultimi": [["2027-01-04", 22500.0, None], ["2026-12-31", 22300.0, None]]}}}
    fa = os.path.join(lav, "anno.json")
    json.dump(anno, open(fa, "w", encoding="utf-8"))
    A = N.tabelle_da_dati(fa, archivio={}, silenzioso=True)
    if ([t for t, _ in A["cruscotto"]], A["cross_data"]) != (["Mondo e Stati Uniti (31/12)", "Asia"], "Livello 4/1") \
            or "da inizio anno = su chiusura 2026 (S&amp;P 500 su chiusura 2025)." not in A["cruscotto_nota"]:
        male.append(f"cavallo d'anno: {[t for t, _ in A['cruscotto']]} {A['cross_data']} | " + A["cruscotto_nota"][:200])
    if (N._al("su", "2026-09-11"), N._al("de", "2026-12-08"), N._al("su", "2026-10-19")) != ("sull'11/9", "dell'8/12", "sul 19/10") \
            or N._elenco(["Mondo e Stati Uniti", "VIX"]) != "Mondo e Stati Uniti, VIX" or N._elenco(["A", "B", "C"]) != "A, B e C":
        male.append("preposizione davanti alla data (sull'11/9, dell'8/12, sul 19/10) o elenco dei nomi")
    esito("Dati: tabelle di pag. 5 calcolate dal codice", not male, "; ".join(male)[:400] or
          "numeri del 20/11 uguali al pubblicato, nessuna n.d., livello ricavato dalla variazione, archivio delle chiusure, "
          "date riga per riga con Wall Street chiusa, con Tokyo chiusa e a cavallo d'anno")


# ---------------------------------------------------------------- 3d. la scommessa: registro e lettura della settimana
def passo_scommessa():
    """Due cose che la rilettura delle edizioni ha trovato rotte e che qui restano controllate.
    Il registro (G-09): ogni settimana si misura dalla chiusura vera. La partenza di un mercato è il verdetto della
    settimana prima, e partenza e verdetto sono i valori delle serie in scommessa/dati: l'Euro Stoxx 50 del 12/10 e del
    19/10/2026 partiva da un dato FMP errato, e una serie corretta dopo deve far rifare il verdetto, non restare diversa.
    La lettura della settimana (G-08): nella n. 026 scenario, tesi di pag. 6 e sei perché erano tre testi che non dicevano
    la stessa cosa. Ora la fonte è una: pronostico.py accetta lo scenario solo come posizione più smentita, lungo quanto
    il riquadro, e pagina6.py stampa quello al posto di una tesi scritta a parte (i registri vecchi restano com'erano)."""
    sc = os.path.join(R, "scommessa")
    alias = {"var_oro": "oro"}                                        # come ALIAS in motore.py
    male = []

    def chiusure(k):
        p = os.path.join(sc, "dati", alias.get(k, k) + ".csv")
        return [(d, float(v)) for d, v in list(csv.reader(open(p, encoding="utf-8")))[1:] if v] if os.path.exists(p) else []

    def alla_data(k, giorno):                                         # l'ultima chiusura fino a quel giorno
        v = [x for d, x in chiusure(k) if d <= giorno]
        return v[-1] if v else None

    prima = {}
    for r in csv.DictReader(open(os.path.join(sc, "registro.csv"), encoding="utf-8")):
        k, lun = alias.get(r["strumento"], r["strumento"]), dt.date.fromisoformat(r["settimana"].split("/")[0])
        base, fin = float(r["base"]), float(r["finale"])
        for cosa, scritto, vero in (("partenza", base, alla_data(k, (lun - dt.timedelta(days=3)).isoformat())),
                                    ("verdetto", fin, alla_data(k, r["data_finale"]))):
            if vero is not None and abs(scritto - vero) > 1e-6:
                male.append(f"registro {r['settimana'][:10]} {k}: {cosa} {scritto}, la serie dice {vero}")
        if k in prima and prima[k][0] == lun - dt.timedelta(days=7) and abs(prima[k][1] - base) > 1e-6:
            male.append(f"registro {r['settimana'][:10]} {k}: parte da {base}, il verdetto della settimana prima era {prima[k][1]}")
        prima[k] = (lun, fin)

    # lo scenario: l'ultimo venerdì che tutte e sei le serie hanno (le serie tengono un anno: niente date fisse)
    fissi = list(json.load(open(os.path.join(sc, "metodo.json"), encoding="utf-8"))["strumenti"])
    comune = min(chiusure(k)[-1][0] for k in fissi)
    ven = max(d for d, _ in chiusure(fissi[0]) if d <= comune and dt.date.fromisoformat(d).weekday() == 4)
    lav = os.path.join(TMP, "scommessa")
    os.makedirs(lav, exist_ok=True)
    red = {k: {"tipo": "fondo", "motivo": f"Che cosa aspetta il mercato {k}"} for k in ("spx", "sx5e", "oro")}
    red.update({k: {"tipo": "scenario", "previsione": alla_data(k, ven) * 1.01, "motivo": f"Il legame tra lo scenario e {k}"}
                for k in fissi if k not in red})
    giusto = "Ci aspettiamo verbali della Fed senza toni nuovi mercoledì, con rendimenti fermi. Ci smentirebbe: un accenno a rialzi più vicini."
    casi = [("posizione e smentita", giusto, True),
            ("un bivio senza smentita", "I conti di martedì decidono la settimana: se reggono le borse recuperano, altrimenti no.", False),
            ("la smentita due volte", giusto + " Ci smentirebbe: anche un dato debole sul lavoro.", False),
            ("più lungo del riquadro", giusto.replace(" Ci smentirebbe:", " Lo diciamo perché " + "il mercato lo ha già messo nei prezzi e " * 3 + "basta. Ci smentirebbe:"), False)]
    reg = os.path.join(lav, (dt.date.fromisoformat(ven) + dt.timedelta(days=3)).isoformat() + "-settimana.json")
    for nome, testo, passa in casi:
        json.dump(dict(red, _scenario=testo), open(os.path.join(lav, "redazione.json"), "w", encoding="utf-8"), ensure_ascii=False)
        rc, out = esegui([sys.executable, "pronostico.py", "--origine", ven, "--redazione", os.path.join(lav, "redazione.json"),
                          "--uscita", os.path.join(lav, nome.split()[0])], cwd=sc)
        if (rc == 0) != passa:
            male.append(f"scenario '{nome}': doveva {'passare' if passa else 'essere rifiutato'} ({out.strip()[-120:]})")
        elif passa:
            shutil.copy(os.path.join(lav, nome.split()[0], os.path.basename(reg)), reg)
    if os.path.exists(reg):
        cod = ("import sys, json; sys.path.insert(0, 'scommessa'); import pagina6, pronostico; n = json.load(open(sys.argv[1])); "
               "print('TESI', int(n.get('schema') == 3 and pagina6.tesi_del_lunedi(n, 'a mano') == n['scenario'] "
               "and pagina6.tesi_del_lunedi(dict(n, schema=2), 'a mano') == 'a mano' "
               "and bool(pagina6.ETICHETTE.fullmatch(pronostico.SMENTITA))))")
        rc, out = esegui([sys.executable, "-c", cod, reg], cwd=R, env={"GTD_REPO": REPO})
        if "TESI 1" not in out:
            male.append("pag. 6 del lunedì non stampa lo scenario del registro nuovo, o cambia la tesi di un registro vecchio: " + out.strip()[-200:])
    esito("Scommessa: registro e lettura della settimana", not male, "; ".join(male)[:500] or
          "partenze e verdetti uguali alle serie e in catena; scenario accettato solo come posizione più smentita in due righe; "
          "il lunedì pag. 6 stampa lo scenario del registro")


# ---------------------------------------------------------------- 3e. newsletter: la cornice o nulla (G-15)
def passo_newsletter():
    """L'email del mattino parte solo con il modello "Gommberg cornice": con un Kit finto che non ce l'ha lo script esce con
    errore e non crea nessun invio (nessun ripiego su un altro modello); con la cornice l'invio ha quel modello. Senza rete."""
    sys.path.insert(0, R)
    import contextlib
    import io
    import newsletter as NL
    radice = os.path.dirname(R)
    ultimo = json.load(open(os.path.join(radice, "edizioni.json"), encoding="utf-8"))[-1]["numero"]
    ed = json.load(open(os.path.join(radice, "e", f"{int(ultimo):03d}.json"), encoding="utf-8"))
    chiamate, vero, vera_attesa = [], NL.kit, NL.ATTESA_LETTURE

    def finto(modelli):
        def k(metodo, percorso, dati=None):
            chiamate.append((metodo, percorso, dati))
            if percorso == "/email_templates":
                return 200, {"email_templates": [{"id": i, "name": n} for i, n in modelli]}
            return 201, {"broadcast": {"id": 1, "email_template": {"name": "x"}}}
        return k
    male = []
    try:
        NL.kit = finto([(1, "Gommberg edizione"), (2, "Gommberg")])
        try:
            NL.crea(ed, None, prova=True)
            male.append("senza la cornice l'invio è partito lo stesso")
        except SystemExit as e:
            if not str(e).startswith("ERRORE"):
                male.append("senza la cornice l'uscita non è un errore")
        if any(c[0] == "POST" for c in chiamate):
            male.append("senza la cornice è stato creato un invio")
        chiamate.clear()
        NL.kit = finto([(1, "Gommberg edizione"), (5, "Gommberg cornice")])
        with contextlib.redirect_stdout(io.StringIO()):
            NL.crea(ed, None, prova=True)
        posts = [c for c in chiamate if c[0] == "POST"]
        if len(posts) != 1 or posts[0][2].get("email_template_id") != 5:
            male.append("con la cornice l'invio non usa la cornice")
        # elenco dei modelli che fallisce (guasto momentaneo di Kit): si riprova, mai si spedisce con un altro modello
        NL.ATTESA_LETTURE = 0

        def guasto(risposte):
            coda = list(risposte)

            def k(metodo, percorso, dati=None):
                chiamate.append((metodo, percorso, dati))
                if percorso == "/email_templates":
                    return coda.pop(0) if len(coda) > 1 else coda[0]
                return 201, {"broadcast": {"id": 1, "email_template": {"name": "x"}}}
            return k
        buono = (200, {"email_templates": [{"id": 5, "name": "Gommberg cornice"}]})
        chiamate.clear()
        NL.kit = guasto([(500, {}), (429, {}), buono])
        with contextlib.redirect_stdout(io.StringIO()):
            NL.crea(ed, None, prova=True)
        posts = [c for c in chiamate if c[0] == "POST"]
        if len(posts) != 1 or posts[0][2].get("email_template_id") != 5 or len([c for c in chiamate if c[0] == "GET"]) != 3:
            male.append("elenco che fallisce due volte e poi risponde: l'invio non parte con la cornice (o l'elenco non è riletto)")
        for nome, risposta in (("risponde sempre 500", (500, {})), ("errore di rete", (0, {"errore": "rete: timeout"}))):
            chiamate.clear()
            NL.kit = guasto([risposta])
            try:
                NL.crea(ed, None, prova=True)
                male.append(f"elenco che {nome}: l'invio è partito lo stesso")
            except SystemExit as e:
                if not str(e).startswith("ERRORE: Kit non risponde"):
                    male.append(f"elenco che {nome}: l'errore non dice che Kit non risponde ({str(e)[:60]})")
            if any(c[0] == "POST" for c in chiamate) or len(chiamate) != NL.LETTURE:
                male.append(f"elenco che {nome}: invio creato o tentativi diversi da {NL.LETTURE}")
        # elenco degli invii che fallisce due volte (503) e poi risponde: l'email parte una volta sola (G-63)
        def kit_invii(risposte):
            coda = list(risposte)

            def k(metodo, percorso, dati=None):
                chiamate.append((metodo, percorso, dati))
                if percorso.startswith("/broadcasts") and metodo == "GET":
                    return coda.pop(0) if len(coda) > 1 else coda[0]
                if percorso == "/email_templates":
                    return 200, {"email_templates": [{"id": 5, "name": "Gommberg cornice"}]}
                return 201, {"broadcast": {"id": 1, "email_template": {"name": "x"}}}
            return k
        vuoto = (200, {"broadcasts": [], "pagination": {"has_next_page": False}})
        chiamate.clear()
        NL.kit = kit_invii([(503, {}), (503, {}), vuoto])
        if NL.invii_esistenti() != {} or len([c for c in chiamate if c[0] == "GET"]) != 3:
            male.append("elenco degli invii che sbaglia due volte e poi risponde: non è riletto")
        chiamate.clear()
        NL.kit = kit_invii([(503, {}), (503, {}), vuoto])
        if NL.etichetta(ed) not in NL.invii_esistenti():      # stessa sequenza di main() in modo auto
            with contextlib.redirect_stdout(io.StringIO()):
                NL.crea(ed, None, prova=False)
        if len([c for c in chiamate if c[0] == "POST"]) != 1:
            male.append("elenco degli invii che sbaglia due volte: l'email non parte una volta sola")
        chiamate.clear()
        NL.kit = kit_invii([(503, {}), (200, {"broadcasts": [{"id": 9, "description": NL.etichetta(ed)}], "pagination": {"has_next_page": False}})])
        if NL.etichetta(ed) not in NL.invii_esistenti():
            male.append("elenco degli invii riletto: l'invio già presente non si vede")
        for nome, risposta in (("risponde sempre 503", (503, {})), ("errore di rete", (0, {"errore": "rete: timeout"}))):
            chiamate.clear()
            NL.kit = kit_invii([risposta])
            try:
                NL.invii_esistenti()
                male.append(f"elenco degli invii che {nome}: non si ferma")
            except SystemExit as e:
                if not str(e).startswith("ERRORE"):
                    male.append(f"elenco degli invii che {nome}: l'uscita non è un errore")
            if len(chiamate) != NL.LETTURE or any(c[0] != "GET" for c in chiamate):
                male.append(f"elenco degli invii che {nome}: tentativi diversi da {NL.LETTURE} o chiamate non di lettura")
        chiamate.clear()
        NL.kit = kit_invii([(401, {})])
        try:
            NL.invii_esistenti()
            male.append("elenco degli invii con errore non transitorio (401): non si ferma")
        except SystemExit:
            pass
        if len(chiamate) != 1:
            male.append("elenco degli invii con 401: riletto senza motivo")
        # l'elenco degli invii ha più pagine: l'invio di oggi nella seconda si vede, l'email non parte due volte (G-69)
        def kit_pagine(pagine, guasti=None):
            """Kit finto a pagine: pagine = {cursore o None: (invii, cursore successivo o None)}; guasti = {cursore: [risposte]}
            date una alla volta prima della pagina vera (per i guasti momentanei a metà elenco)."""
            guasti = {k: list(v) for k, v in (guasti or {}).items()}

            def k(metodo, percorso, dati=None):
                chiamate.append((metodo, percorso, dati))
                if percorso.startswith("/broadcasts") and metodo == "GET":
                    cursore = percorso.split("after=")[1] if "after=" in percorso else None
                    if guasti.get(cursore):
                        return guasti[cursore].pop(0)
                    invii, dopo = pagine[cursore]
                    return 200, {"broadcasts": invii, "pagination": {"has_next_page": bool(dopo), "end_cursor": dopo}}
                if percorso == "/email_templates":
                    return 200, {"email_templates": [{"id": 5, "name": "Gommberg cornice"}]}
                return 201, {"broadcast": {"id": 1, "email_template": {"name": "x"}}}
            return k
        altri = [{"id": i, "description": f"altro-{i}"} for i in range(3)]
        oggi_kit = {"id": 9, "description": NL.etichetta(ed), "status": "scheduled"}
        due_pagine = {None: (altri, "c1"), "c1": ([{"id": 7, "description": "altro-7"}, oggi_kit], None)}
        chiamate.clear()
        NL.kit = kit_pagine(due_pagine)
        trovati = NL.invii_esistenti()
        if NL.etichetta(ed) not in trovati or len(trovati) != 5 or len([c for c in chiamate if c[0] == "GET"]) != 2:
            male.append("elenco degli invii su due pagine: l'invio di oggi nella seconda pagina non si vede")
        chiamate.clear()
        NL.kit = kit_pagine(due_pagine)
        if NL.etichetta(ed) not in NL.invii_esistenti():      # stessa sequenza di main() in modo auto
            with contextlib.redirect_stdout(io.StringIO()):
                NL.crea(ed, None, prova=False)
        if any(c[0] == "POST" for c in chiamate):
            male.append("invio di oggi nella seconda pagina: l'email è partita una seconda volta")
        # guasto momentaneo a metà della seconda pagina: si rilegge quella pagina, la prima non si rilegge, nessun doppione
        chiamate.clear()
        NL.kit = kit_pagine(due_pagine, {"c1": [(503, {}), (0, {"errore": "rete: timeout"})]})
        if NL.etichetta(ed) not in NL.invii_esistenti():
            male.append("guasto a metà della seconda pagina: l'invio di oggi non si vede dopo la rilettura")
        letti = [c[1] for c in chiamate]
        if len(letti) != 4 or letti.count("/broadcasts?per_page=1000&slim=true") != 1 or any(c[0] != "GET" for c in chiamate):
            male.append("guasto a metà della seconda pagina: riletture diverse da quelle attese (pagina 1 una volta, pagina 2 tre)")
        # la seconda pagina muta (sempre 503): errore, nessun invio, mai un elenco a metà preso per completo
        chiamate.clear()
        NL.kit = kit_pagine(due_pagine, {"c1": [(503, {})] * 9})
        try:
            NL.invii_esistenti()
            male.append("seconda pagina sempre in errore: non si ferma")
        except SystemExit as e:
            if not str(e).startswith("ERRORE"):
                male.append("seconda pagina sempre in errore: l'uscita non è un errore")
        if len(chiamate) != 1 + NL.LETTURE:
            male.append(f"seconda pagina sempre in errore: chiamate diverse da 1 + {NL.LETTURE}")
        # troppe pagine: ci si ferma con errore, il caso peggiore resta limitato
        chiamate.clear()
        NL.kit = kit_pagine({None: ([], "x"), "x": ([], "x")})
        try:
            NL.invii_esistenti()
            male.append("elenco di pagine senza fine: non si ferma")
        except SystemExit:
            pass
        if len(chiamate) != NL.MAX_PAGINE:
            male.append(f"elenco di pagine senza fine: pagine lette diverse da {NL.MAX_PAGINE}")
        # risposte fuori forma: "non so" non diventa "non c'è" (collaudo indipendente di G-69): nessun invio, nessun traceback
        pieno = [{"id": 9, "description": NL.etichetta(ed)}]
        fuori_forma = [
            ("corpo vuoto", {None: ({}, None)}),
            ("senza broadcasts", {None: ({"pagination": {"has_next_page": False}}, None)}),
            ("broadcasts null", {None: ({"broadcasts": None, "pagination": {"has_next_page": False}}, None)}),
            ("corpo a lista", {None: ([], None)}),
            ("senza paginazione", {None: ({"broadcasts": []}, None)}),
            ("has_next_page senza cursore", {None: ({"broadcasts": [], "pagination": {"has_next_page": True}}, None)}),
            ("pagina 2 senza broadcasts", {None: ({"broadcasts": [], "pagination": {"has_next_page": True, "end_cursor": "c1"}}, None),
                                            "c1": ({"pagination": {"has_next_page": False}}, None)}),
        ]
        for nome, risposte in fuori_forma:
            chiamate.clear()

            def k_storto(metodo, percorso, dati=None, _r=risposte):
                chiamate.append((metodo, percorso, dati))
                if percorso.startswith("/broadcasts") and metodo == "GET":
                    return 200, _r["c1" if "after=c1" in percorso else None][0]
                return 201, {"broadcast": {"id": 1}}
            NL.kit = k_storto
            try:
                NL.invii_esistenti()
                male.append(f"elenco degli invii ({nome}): preso per leggibile")
            except SystemExit as e:
                if not str(e).startswith("ERRORE"):
                    male.append(f"elenco degli invii ({nome}): uscita non chiara")
            except Exception as e:
                male.append(f"elenco degli invii ({nome}): traceback {type(e).__name__}")
            if any(c[0] == "POST" for c in chiamate):
                male.append(f"elenco degli invii ({nome}): l'email è partita")
        # invii senza la chiave description: "non so", nessun invio; con description null (invio a mano) si legge e si ignora
        def k_desc(elenco):
            def k(metodo, percorso, dati=None):
                chiamate.append((metodo, percorso, dati))
                if percorso.startswith("/broadcasts") and metodo == "GET":
                    return 200, {"broadcasts": elenco, "pagination": {"has_next_page": False}}
                if percorso == "/email_templates":
                    return 200, {"email_templates": [{"id": 5, "name": "Gommberg cornice"}]}
                return 201, {"broadcast": {"id": 1, "email_template": {"name": "x"}}}
            return k
        for nome, elenco, parte in (("senza la chiave description", [{"id": 9, "status": "scheduled"}], False),
                                    ("elemento non dizionario", ["x"], False),
                                    ("description null accanto all'invio di oggi", [{"id": 3, "description": None}, {"id": 9, "description": NL.etichetta(ed)}], False),
                                    ("description null e vuota senza l'invio di oggi", [{"id": 3, "description": None}, {"id": 4, "description": ""}], True)):
            chiamate.clear()
            NL.kit = k_desc(elenco)
            try:
                if NL.etichetta(ed) not in NL.invii_esistenti():      # stessa sequenza di main() in modo auto
                    with contextlib.redirect_stdout(io.StringIO()):
                        NL.crea(ed, None, prova=False)
            except SystemExit as e:
                if not str(e).startswith("ERRORE"):
                    male.append(f"invii {nome}: uscita non chiara")
            posts = len([c for c in chiamate if c[0] == "POST"])
            if posts != (1 if parte else 0):
                male.append(f"invii {nome}: {posts} invii creati invece di {1 if parte else 0}")
        # l'allarme del limite netto, se chiamato, esce con un avviso chiaro
        try:
            NL._tempo_scaduto()
            male.append("allarme del giro: non esce")
        except SystemExit as e:
            if "esito è incerto" not in str(e):
                male.append("allarme del giro: l'avviso non dice dell'esito incerto")
        # dem.py non cambia: la sua lettura resta quella di prima (100 per pagina, nessuna verifica in più)
        chiamate.clear()
        NL.kit = kit_pagine(due_pagine)
        NL.leggi_invii(1, 0)
        if chiamate[0][1] != "/broadcasts?per_page=100":
            male.append("lettura degli invii di dem.py: l'indirizzo è cambiato")
        # la scadenza del giro, con l'orologio finto: nessuna chiamata dopo, nessun invio, la creazione mai
        vero_orologio, vera_scadenza = NL.orologio, NL._scadenza
        try:
            ora = [1000.0]
            NL.orologio = lambda: ora[0]
            NL.avvia_scadenza()
            chiamate.clear()
            base = kit_pagine({None: ([], "c1"), "c1": ([], "c2"), "c2": (pieno, None)})

            def k_lento(metodo, percorso, dati=None):
                if NL.tempo_rimasto() <= 0:      # come kit(): a tempo scaduto non si chiama
                    return 0, {"errore": "scadenza del giro superata", "scaduta": True}
                ora[0] += 300           # ogni lettura costa 5 minuti: la seconda arriva a giro scaduto
                return base(metodo, percorso, dati)
            NL.kit = k_lento
            try:
                NL.invii_esistenti()
                male.append("scadenza del giro: elenco letto oltre il tempo")
            except SystemExit as e:
                if "minuti" not in str(e):
                    male.append(f"scadenza del giro: avviso non chiaro ({str(e)[:80]})")
            # con kit() vero e il tempo finito: nessuna chiamata di rete, stato 0 con "scaduta"
            NL.kit, os.environ["KIT_API_KEY"] = vero, "kit_prova"
            ora[0] = 1000.0 + NL.SCADENZA + 1
            import urllib.request as _ur
            vera_ap = _ur.urlopen
            _ur.urlopen = lambda *a, **k: (_ for _ in ()).throw(AssertionError("chiamata dopo la scadenza"))
            try:
                if NL.kit("POST", "/broadcasts", {})[0] != 0:
                    male.append("scadenza del giro: la creazione dopo la scadenza non è fermata")
            except AssertionError:
                male.append("scadenza del giro: Kit chiamato a tempo scaduto")
            finally:
                _ur.urlopen = vera_ap
            # a tempo quasi finito (meno di 30 s) la creazione non parte
            ora[0] = 1000.0 + NL.SCADENZA - 10
            chiamate.clear()
            NL.kit = kit_pagine(due_pagine)
            try:
                NL.crea(ed, None, prova=False)
                male.append("scadenza del giro: creazione partita con meno di 30 s rimasti")
            except SystemExit:
                pass
            if any(c[0] == "POST" for c in chiamate):
                male.append("scadenza del giro: POST fatto con meno di 30 s rimasti")
        finally:
            NL.orologio, NL._scadenza = vero_orologio, vera_scadenza
            import signal as _sg
            _sg.alarm(0)       # l'allarme di avvia_scadenza() non deve restare armato nel collaudo
        # un errore di rete in kit() è una risposta gestita, non un traceback
        import urllib.error
        import urllib.request
        vera_apertura, chiave = urllib.request.urlopen, os.environ.get("KIT_API_KEY")
        NL.kit, os.environ["KIT_API_KEY"] = vero, "kit_prova"
        try:
            for errore in (urllib.error.URLError("irraggiungibile"), TimeoutError("timeout")):
                def apri(*a, _e=errore, **k):
                    raise _e
                urllib.request.urlopen = apri
                if NL.kit("GET", "/email_templates")[0] != 0:
                    male.append(f"errore di rete ({type(errore).__name__}) in kit(): non è una risposta gestita")
        finally:
            urllib.request.urlopen = vera_apertura
            if chiave is None:
                os.environ.pop("KIT_API_KEY", None)
            else:
                os.environ["KIT_API_KEY"] = chiave
    finally:
        NL.kit = vero
        NL.ATTESA_LETTURE = vera_attesa
    esito("Newsletter: la cornice o nulla", not male, "; ".join(male) or "senza la cornice in Kit l'invio fallisce e non crea nulla; con la cornice la usa; "
          "elenco che si riprende dopo due guasti: parte; elenco muto o rete caduta: 'Kit non risponde', nessun invio, nessun traceback; "
          "elenco degli invii: riletto come i modelli, l'email parte una volta sola, se resta muto l'invio si ferma")


# ---------------------------------------------------------------- 3f. mail straordinarie (G-17)
def passo_dem():
    """Le mail straordinarie: i file veri passano le regole e pannello/invii.json è allineato; le regole fermano i casi
    sbagliati, anche ai confini; il pianificatore decide la cosa giusta in ogni situazione di Kit; l'esecuzione con un Kit
    finto che sbaglia non crea mai doppioni né bozze con una data (senza rete)."""
    rc, out = esegui([sys.executable, os.path.join(R, "dem.py")])
    righe = [l for l in out.splitlines() if "ERRORE" in l]
    esito("Mail straordinarie: file e vista del pannello", rc == 0, "regole rispettate, pannello/invii.json allineato"
          if rc == 0 else "; ".join(righe)[:300])

    sys.path.insert(0, R)
    import contextlib
    import dem
    import io
    from datetime import datetime, timedelta, timezone
    from pathlib import Path as P
    lav, UTC, MOD = P(TMP) / "dem", timezone.utc, 5716428
    sbagliati = []

    def leggi(*file, calendario=False):
        shutil.rmtree(lav, ignore_errors=True)
        lav.mkdir(parents=True)
        for f in file:
            nome, invio, stato, extra, corpo = (list(f) + ["bozza", "", "Testo di prova della redazione."][len(f) - 2:])[:5]
            (lav / nome).write_text(f"---\ninvio: {invio}\nstato: {stato}\noggetto: Oggetto di prova\n"
                                    f"anteprima: Una riga di anteprima abbastanza lunga.\n{extra}---\n{corpo}\n", encoding="utf-8")
        mail = dem.leggi_tutte(lav)
        if calendario:
            dem.regole_calendario(mail)
        return mail

    # 1. le regole, anche ai confini
    OK = "ok: Paolo 2026-12-01\n"
    casi = [("sabato mattina", [("2027-01-16-p.md", "2027-01-16 10:00")], False),
            ("ore 20:59", [("2027-01-16-p.md", "2027-01-16 20:59")], False),
            ("ore 21:00", [("2027-01-16-p.md", "2027-01-16 21:00")], True),
            ("ore 7:59", [("2027-01-16-p.md", "2027-01-16 07:59")], True),
            ("giorno di uscita alle 10:59", [("2027-01-18-p.md", "2027-01-18 10:59")], True),
            ("giorno di uscita alle 11:00", [("2027-01-18-p.md", "2027-01-18 11:00")], False),
            ("festivo (25/12) alle 9:00", [("2026-12-25-p.md", "2026-12-25 09:00")], False),
            ("approvata senza ok", [("2027-01-16-p.md", "2027-01-16 10:00", "approvata")], True),
            ("approvata con ok", [("2027-01-16-p.md", "2027-01-16 10:00", "approvata", OK)], False),
            ("trattino lungo", [("2027-01-16-p.md", "2027-01-16 10:00", "bozza", "", "Una frase — lunga.")], True),
            ("due nello stesso mese", [("2027-01-02-a.md", "2027-01-02 10:00"), ("2027-01-30-b.md", "2027-01-30 10:00")], True),
            ("stesso mese, una annullata", [("2027-01-02-a.md", "2027-01-02 10:00", "annullata"), ("2027-01-30-b.md", "2027-01-30 10:00")], False),
            ("13 giorni a cavallo del mese", [("2027-01-26-a.md", "2027-01-26 18:00"), ("2027-02-08-b.md", "2027-02-08 18:00")], True),
            ("14 giorni a cavallo del mese", [("2027-01-25-a.md", "2027-01-25 18:00"), ("2027-02-08-b.md", "2027-02-08 18:00")], False),
            ("data del nome diversa", [("2027-01-17-p.md", "2027-01-16 10:00")], True),
            ("sondaggio con una risposta", [("2027-01-16-p.md", "2027-01-16 10:00", "bozza", "", "?? Domanda?\n- Una sola")], True),
            ("link non https", [("2027-01-16-p.md", "2027-01-16 10:00", "bozza", "", "Leggi [qui](http://gommberg.com/).")], True)]
    for nome, file, ferma in casi:
        if bool([x for m in leggi(*file, calendario=True) for x in m.errori]) != ferma:
            sbagliati.append(f"regola: {nome}")

    # 2. il pianificatore
    mail = {m.nome[-1]: m for m in leggi(("2027-01-16-a.md", "2027-01-16 10:00", "approvata", OK),
                                         ("2027-02-13-b.md", "2027-02-13 10:00"),
                                         ("2027-03-13-c.md", "2027-03-13 10:00", "annullata"),
                                         ("2027-01-13-e.md", "2027-01-13 18:00"))}
    ET = {x: m.etichetta for x, m in mail.items()}
    ET["o"] = dem.ETICHETTA + "2027-04-01-orfano"
    imp = lambda x, prog: dem.impronta_di(dem.dati_invio(mail[x], prog, MOD)["description"])
    ia = lambda x: mail[x].invio.astimezone(UTC)
    def kk(send=None, partito=False, impronta="vecchia", i=1):
        return {"id": i, "send_at": send, "partito": partito, "impronta": impronta}
    def prova(nome, scelta, kit, ora, attese, n_guardare, solo_ritiri=False):
        azioni, guardare, _ = dem.piano([mail[x] for x in scelta], {ET[x]: v for x, v in kit.items()}, ora, MOD, solo_ritiri)
        fatte = {}
        for a in azioni:
            fatte.setdefault(a[1].rsplit("-", 1)[-1][0] if a[1] != ET["o"] else "o", []).append(a[0])
        trovate = {x: "+".join(v) for x, v in fatte.items()}
        if any(trovate.get(x) != v for x, v in attese.items()) or len(guardare) != n_guardare:
            sbagliati.append(f"piano, {nome}: atteso {attese} e {n_guardare} da guardare, trovato {trovate} e {len(guardare)}")
    ora = datetime(2027, 1, 10, 12, 0, tzinfo=UTC)
    prova("Kit vuoto", "abce", {}, ora, {"a": "crea-programmata", "b": "crea-bozza", "c": "nulla", "e": "crea-bozza"}, 1)
    prova("Kit già allineato", "ab", {"a": [kk(ia("a"), impronta=imp("a", True))], "b": [kk(None, impronta=imp("b", False))]},
          ora, {"a": "nulla", "b": "nulla"}, 0)
    prova("cambi e ritiri", "abc", {"a": [kk(None)], "b": [kk(ia("b"))], "c": [kk(ia("c"))], "o": [kk(datetime(2027, 4, 1, 8, tzinfo=UTC))]},
          ora, {"a": "rifai-programmata", "b": "rifai-bozza", "c": "elimina", "o": "elimina"}, 0)
    prova("testo cambiato, stessa ora", "a", {"a": [kk(ia("a"), impronta="diversa")]}, ora, {"a": "rifai-programmata"}, 0)
    prova("doppione in Kit", "a", {"a": [kk(ia("a"), impronta=imp("a", True), i=1), kk(ia("a"), i=2)]}, ora, {"a": "elimina+nulla"}, 1)
    prova("già partita", "a", {"a": [kk(ia("a") - timedelta(days=1), partito=True)]}, ora, {"a": "nulla"}, 0)
    prova("errori nei file: solo ritiri", "abc", {"b": [kk(ia("b"))], "c": [kk(ia("c"))]}, ora,
          {"a": "nulla", "b": "elimina", "c": "elimina"}, 0, solo_ritiri=True)
    vicino = ia("a") - timedelta(minutes=10)
    prova("in partenza, uguale", "a", {"a": [kk(ia("a"), impronta=imp("a", True))]}, vicino, {"a": "nulla"}, 0)
    prova("in partenza, cambiata", "a", {"a": [kk(ia("a"), impronta="diversa")]}, vicino, {"a": "nulla"}, 1)
    prova("annullata a 10 minuti", "c", {"c": [kk(ia("c"))]}, ia("c") - timedelta(minutes=10), {"c": "elimina"}, 0)
    prova("orfano a 1 minuto", "", {"o": [kk(ora + timedelta(minutes=1))]}, ora, {"o": "nulla"}, 1)
    prova("ora spostata più tardi, Kit a 10 minuti", "a", {"a": [kk(ia("a") - timedelta(hours=2))]},
          ia("a") - timedelta(hours=2, minutes=10), {"a": "rifai-programmata"}, 0)
    prova("ora cambiata a mano in Kit", "a", {"a": [kk(ia("a") + timedelta(hours=3), impronta=imp("a", True))]}, ora, {"a": "rifai-programmata"}, 0)
    prova("già partita con una copia viva", "a", {"a": [kk(ia("a") - timedelta(hours=1), partito=True, i=1), kk(ia("a") + timedelta(days=1), i=2)]},
          ia("a") + timedelta(minutes=5), {"a": "elimina"}, 1)
    prova("approvata non partita, il giorno dopo", "a", {}, ia("a") + timedelta(hours=1), {"a": "nulla"}, 1)
    prova("approvata non partita, dopo 3 giorni", "a", {}, ia("a") + timedelta(days=3), {"a": "nulla"}, 0)
    # nel dubbio si ritira: ok tolto, stato scritto male, data illeggibile, anche con errori nei file
    for nome, extra, stato in (("ok tolto", "", "approvata"), ("stato scritto male", OK, "Bozza"), ("stato sconosciuto", OK, "sospesa")):
        dubbia = leggi(("2027-01-16-a.md", "2027-01-16 10:00", stato, extra))[0]
        azioni, _, _ = dem.piano([dubbia], {dubbia.etichetta: [kk(ia("a"), impronta=imp("a", True))]}, ora, MOD, True)
        if [x[0] for x in azioni] != ["elimina"]:
            sbagliati.append(f"piano, {nome} con l'invio programmato in Kit: va ritirata, trovato {[x[0] for x in azioni]}")
    if not dem.stato_kit({"status": "scheduled", "send_at": "2027-01-01T09:00:00Z"}, ora)["partito"]:
        sbagliati.append("un invio 'scheduled' con l'ora passata va considerato partito")
    if dem.dati_invio(mail["b"], False, MOD)["send_at"] is not None or not dem.dati_invio(mail["a"], True, MOD)["send_at"]:
        sbagliati.append("dati per Kit: una bozza non ha data, una programmata sì")

    # 3. l'esecuzione con un Kit finto che sbaglia di proposito
    vero = dem.nl.kit
    try:
        def finto(risposte):
            chiamate = []
            def kit(metodo, percorso, dati=None):
                chiamate.append((metodo, dati))
                return risposte.get(metodo, (200, {}))
            return kit, chiamate
        def esegui_con(risposte, azioni):
            dem.nl.kit, chiamate = finto(risposte)
            with contextlib.redirect_stdout(io.StringIO()):
                return dem.esegui_piano(azioni, MOD), chiamate
        programmata = {"broadcast": {"id": 9, "send_at": ia("a").isoformat()}}
        male, ch = esegui_con({"DELETE": (500, {}), "POST": (201, programmata)}, [("rifai-programmata", ET["a"], mail["a"], "", 1)])
        if not male or any(c[0] == "POST" for c in ch):
            sbagliati.append("esecuzione: se Kit non toglie l'invio vecchio, non se ne crea uno nuovo")
        male, ch = esegui_con({"POST": (201, {"broadcast": {"id": 9, "send_at": None}})}, [("crea-bozza", ET["b"], mail["b"], "", None)])
        if male or ch[0][1]["send_at"] is not None:
            sbagliati.append("esecuzione: bozza creata senza data")
        male, ch = esegui_con({"POST": (201, {"broadcast": {"id": 9, "send_at": "2027-02-13T09:00:00Z"}})}, [("crea-bozza", ET["b"], mail["b"], "", None)])
        if not male or not any(c[0] == "DELETE" for c in ch):
            sbagliati.append("esecuzione: una bozza che Kit registra con una data va tolta subito")
        male, _ = esegui_con({"POST": (201, programmata)}, [("crea-programmata", ET["a"], mail["a"], "", None)])
        male2, _ = esegui_con({"POST": (422, {})}, [("crea-programmata", ET["a"], mail["a"], "", None)])
        male3, _ = esegui_con({"DELETE": (404, {})}, [("elimina", ET["c"], mail["c"], "", 1)])
        if male or not male2 or male3:
            sbagliati.append("esecuzione: programmata giusta accettata, rifiuto di Kit segnalato, invio già sparito accettato")
        # l'elenco degli invii: due pagine, si tengono solo quelli delle mail straordinarie, raggruppati per etichetta
        pagine = [(200, {"broadcasts": [{"id": 1, "description": ET["a"] + " #x"}, {"id": 2, "description": "gommberg-edizione-031"}],
                         "pagination": {"has_next_page": True, "end_cursor": "c1"}}),
                  (200, {"broadcasts": [{"id": 3, "description": ET["a"] + " #y"}], "pagination": {"has_next_page": False}})]
        dem.nl.kit = lambda metodo, percorso, dati=None: pagine.pop(0)
        trovati = dem.invii_dem()
        if list(trovati) != [ET["a"]] or [b["id"] for b in trovati[ET["a"]]] != [1, 3]:
            sbagliati.append("elenco degli invii di Kit: pagine, filtro o raggruppamento")
    finally:
        dem.nl.kit = vero

    # 4. la composizione: un link per risposta verso la pagina di ringraziamento, nessun segno rimasto
    m = leggi(("2027-01-16-s.md", "2027-01-16 10:00", "bozza", "pulsante: Leggi | https://gommberg.com/\nnota: Postilla.\n",
               "## Titoletto\n\n- uno\n- due\n\n?? Domanda?\n- Prima\n- Seconda\n- Terza\n\n> Riquadro con **grassetto**."))[0]
    corpo = dem.componi(m)[2]
    if corpo.count("grazie.html?d=2027-01-16-s&amp;r=") != 3 or "??" in corpo or "**" in corpo or "{{" in corpo or "Postilla." not in corpo:
        sbagliati.append("composizione: sondaggio, segni o postilla non resi")
    esito("Mail straordinarie: regole, pianificatore, esecuzione e composizione", not sbagliati,
          f"{len(casi)} casi di regole ai confini, 19 situazioni di Kit (nel dubbio si ritira), Kit finto che sbaglia, elenco a pagine, composizione"
          if not sbagliati else "; ".join(sbagliati)[:600])


# ---------------------------------------------------------------- 3g. benvenuto ai nuovi iscritti (G-43)
def passo_benvenuto():
    """La mail di benvenuto: testo in regola e ora di uscita in un posto solo; il giro con un Kit finto che risponde bene,
    che sbaglia (5xx, rete muta, risposte illeggibili o fuori forma, filtro ignorato o cambiato, risposte che mentono,
    invii che non si tolgono) e nei casi difficili (zero nuovi, già salutati, finestra di 7 giorni e accensione, due giri
    nello stesso giorno, giro interrotto a metà, sere saltate per l'orario): mai due mail allo stesso iscritto, mai un
    invio che parte con destinatari diversi dal gruppo, nel dubbio nessun invio (senza rete). Poi la prova dal vivo
    (bozza e prova, con l'iscritto indicato per impronta) dalla riga di comando e dai passi di dem.yml eseguiti qui: mai
    un invio a qualcuno che non sia il solo iscritto dell'impronta, mai un indirizzo in ciò che lo script stampa."""
    rc, out = esegui([sys.executable, os.path.join(R, "benvenuto.py"), "controlla"])
    esito("Benvenuto: testo della mail", rc == 0, out.strip().splitlines()[-1][:200] if out.strip() else "nessuna uscita")

    sys.path.insert(0, R)
    import contextlib
    import copy
    import hashlib
    import io
    import traceback
    from datetime import datetime, timedelta, timezone
    from urllib.parse import parse_qs, urlsplit
    from zoneinfo import ZoneInfo
    import benvenuto as BV
    import giorni as GG
    ROMA, UTC = ZoneInfo("Europe/Rome"), timezone.utc
    SERA = datetime(2026, 12, 2, 19, 30, tzinfo=ROMA)          # un mercoledì alle 19:30, 4 giorni dopo l'accensione
    TUTTI = [{"all": [{"type": "all_subscribers"}], "any": None, "none": None}]
    male, viva, uscite = [], [], []       # viva: la prova dal vivo; uscite: tutto ciò che lo script ha stampato
    ELENCHI = []                          # ogni elenco degli invii chiesto a Kit (deve essere la lettura leggera)

    class Interrotto(BaseException):        # come un giro ucciso: nessuno strato la intercetta
        pass

    class KitFinto:
        """Kit in memoria. Ogni invio ha il filtro VERO (a chi partirebbe) e quello DETTO nelle risposte alle scritture;
        GET /broadcasts/{id} dice il vero. guasti: {"METODO /percorso" (o "/prefisso*"): risposta | eccezione |
        ("dopo", stato, corpo) = l'operazione avviene ma la risposta è quella | lista di questi, uno per chiamata}."""
        def __init__(self, iscritti=(), etichette=(), modelli=((7, "Gommberg"), (5, "Gommberg cornice")), ignora_data=False,
                     nascondi_tag=False):
            self.iscritti = {s["id"]: dict(s) for s in iscritti}
            self.tag, self.membri, self.invii = {}, {}, {}
            self.modelli, self.ignora_data, self.nascondi_tag = list(modelli), ignora_data, nascondi_tag
            self.guasti, self.chiamate, self.prossimo = {}, [], 100
            self.crea_a_tutti = self.crea_mente = self.put_a_tutti = self.put_mente = self.delete_rotto = self.put_rotto = False
            # ritardo: come Kit vero, l'elenco di un'etichetta mostra un'assegnazione solo `ritardo` secondi dopo (sull'orologio
            # dello script); tutti_vuoto: l'elenco con status=all non restituisce mai nulla; per_id: le etichette lette per id
            # dalla parte dell'iscritto si vedono subito (True) o mai (False)
            self.ritardo, self.dato, self.tutti_vuoto, self.per_id = 0, {}, False, True
            for nome, chi in etichette:
                i = self.nuovo_id()
                self.tag[i], self.membri[i] = nome, set(chi)

        def nuovo_id(self):
            self.prossimo += 1
            return self.prossimo

        def guasto(self, metodo, via):
            for k, v in self.guasti.items():
                m, p = k.split(" ", 1)
                if m == metodo and (p == via or (p.endswith("*") and via.startswith(p[:-1]))):
                    if isinstance(v, list):
                        return v.pop(0) if v else None
                    return v
            return None

        def __call__(self, metodo, percorso, dati=None):
            self.chiamate.append((metodo, percorso, copy.deepcopy(dati)))
            via = urlsplit(percorso).path
            g = self.guasto(metodo, via)
            if isinstance(g, BaseException):
                raise g
            if g is not None and g[0] != "dopo":
                return g
            r = self.esegui(metodo, percorso, copy.deepcopy(dati))
            if g is not None:
                if isinstance(g[1], BaseException):
                    raise g[1]
                return g[1], g[2]
            return r

        def esegui(self, metodo, percorso, dati):
            u = urlsplit(percorso)
            via, q = u.path, {k: v[0] for k, v in parse_qs(u.query).items()}
            pg = {"has_previous_page": False, "has_next_page": False, "start_cursor": "a", "end_cursor": "b", "per_page": 500}
            if metodo == "GET" and via == "/email_templates":
                return 200, {"email_templates": [{"id": i, "name": n} for i, n in self.modelli]}
            if metodo == "GET" and via == "/tags":
                return 200, {"tags": [{"id": i, "name": n, "created_at": "2026-11-01T00:00:00Z"} for i, n in self.tag.items()], "pagination": pg}
            if metodo == "POST" and via == "/tags":
                for i, n in self.tag.items():
                    if n.lower() == dati["name"].lower():
                        return 200, {"tag": {"id": i, "name": n, "created_at": "x"}}
                i = self.nuovo_id()
                self.tag[i], self.membri[i] = dati["name"], set()
                return 201, {"tag": {"id": i, "name": dati["name"], "created_at": "x"}}
            if metodo == "GET" and via == "/subscribers":
                out = []
                for s in self.iscritti.values():
                    if q.get("status", "active") != "all" and s["state"] != q.get("status", "active"):
                        continue
                    if "email_address" in q and s.get("email_address") != q["email_address"]:
                        continue
                    if "created_after" in q and not self.ignora_data and s["created_at"][:10] < q["created_after"][:10]:
                        continue
                    tags = [] if self.nascondi_tag else [{"id": i, "name": self.tag[i]} for i, m in self.membri.items() if s["id"] in m]
                    out.append({"id": s["id"], "first_name": None, "email_address": s.get("email_address", f"x{s['id']}@prova.it"),
                                "state": s["state"], "created_at": s["created_at"], "fields": {}, "tags": tags})
                return 200, {"subscribers": out, "pagination": pg}
            m = re.match(r"^/tags/(\d+)/subscribers(?:/(\d+))?$", via)
            if m:
                t = int(m.group(1))
                if t not in self.tag:
                    return 404, {"errors": ["no"]}
                if metodo == "GET":
                    stato = q.get("status", "active")
                    visti = [i for i in sorted(self.membri[t]) if (not self.ritardo or BV.orologio() - self.dato.get((t, i), -10 ** 9) >= self.ritardo)
                             and (stato == "all" or self.iscritti[i]["state"] == stato) and not (stato == "all" and self.tutti_vuoto)]
                    if "include_total_count" in q:
                        pg = dict(pg, total_count=len(visti))
                    return 200, {"subscribers": [{"id": i, "state": self.iscritti[i]["state"], "created_at": self.iscritti[i]["created_at"],
                                                  "tagged_at": "x"} for i in visti], "pagination": pg}
                s = int(m.group(2))
                if s not in self.iscritti:
                    return 404, {"errors": ["no"]}
                if s in self.membri[t]:
                    return 200, {"subscriber": {"id": s}}
                self.membri[t].add(s)
                self.dato[(t, s)] = BV.orologio()
                return 201, {"subscriber": {"id": s}}
            m = re.match(r"^/subscribers/(\d+)/tags$", via)
            if m and metodo == "GET":
                return 200, {"tags": [{"id": i, "name": self.tag[i], "tagged_at": "x"} for i, chi in self.membri.items()
                                      if int(m.group(1)) in chi and self.per_id], "pagination": pg}
            m = re.match(r"^/tags/(\d+)$", via)
            if m and metodo == "DELETE":
                if int(m.group(1)) not in self.tag:
                    return 404, {"errors": ["no"]}
                del self.tag[int(m.group(1))], self.membri[int(m.group(1))]
                return 204, {}
            if metodo == "GET" and via == "/broadcasts":
                ELENCHI.append(percorso)
                return 200, {"broadcasts": [self.vista(b) for b in self.invii.values()], "pagination": pg}
            if metodo == "POST" and via == "/broadcasts":
                i = self.nuovo_id()
                chiesto = dati.get("subscriber_filter")
                b = {"id": i, "subject": dati["subject"], "description": dati["description"], "send_at": dati["send_at"],
                     "email_template": {"id": dati["email_template_id"], "name": "Gommberg cornice"},
                     "vero": TUTTI if (self.crea_a_tutti or self.crea_mente or not chiesto) else chiesto}
                self.invii[i] = b
                return 201, {"broadcast": dict(self.vista(b), subscriber_filter=chiesto if self.crea_mente else b["vero"])}
            m = re.match(r"^/broadcasts/(\d+)$", via)
            if m and int(m.group(1)) in self.invii:
                b = self.invii[int(m.group(1))]
                if metodo == "GET":
                    return 200, {"broadcast": self.vista(b)}
                if metodo == "DELETE":
                    if self.delete_rotto:
                        return 500, {}
                    del self.invii[b["id"]]
                    return 204, {}
                if metodo == "PUT":
                    if self.put_rotto:
                        return 500, {}
                    chiesto = dati.get("subscriber_filter")
                    b["send_at"] = dati.get("send_at")
                    b["vero"] = TUTTI if (self.put_a_tutti or self.put_mente or not chiesto) else chiesto
                    return 200, {"broadcast": dict(self.vista(b), subscriber_filter=chiesto if self.put_mente else b["vero"])}
            if m:
                return 404, {}
            return 404, {"errors": ["percorso sconosciuto"]}

        def vista(self, b):
            return {"id": b["id"], "subject": b["subject"], "description": b["description"], "send_at": b["send_at"],
                    "status": b.get("status") or ("scheduled" if b["send_at"] else "draft"), "email_template": b["email_template"],
                    "subscriber_filter": copy.deepcopy(b["vero"])}

        def posta(self):
            """Quante mail riceve ogni iscritto: ogni invio programmato parte con il suo filtro VERO."""
            conto = {i: 0 for i in self.iscritti}
            for b in self.invii.values():
                if not b.get("send_at"):
                    continue
                voci = (b["vero"] or [{}])[0].get("all") or []
                chi = (self.membri.get(voci[0]["ids"][0], set()) if voci and voci[0].get("type") == "tag"
                       else {i for i, s in self.iscritti.items() if s["state"] == "active"})
                for i in chi:
                    conto[i] += 1
            return conto

        def scritture(self):
            return [c for c in self.chiamate if c[0] != "GET"]

        def invii_scritti(self):
            return [c for c in self.chiamate if c[0] != "GET" and c[1].startswith("/broadcasts")]

    def iscritto(i, ore_fa, stato="active", quando_=None):
        return {"id": i, "state": stato, "created_at": ((quando_ or SERA) - timedelta(hours=ore_fa)).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}

    def giro(kit, adesso=SERA):
        """Un giro di benvenuto.py invia con il Kit finto: (uscita, messaggio). uscita: 0, 'fermo', 'interrotto', 'eccezione'."""
        BV.ferma_scadenza()
        BV.nl.kit = kit
        o = io.StringIO()
        try:
            with contextlib.redirect_stdout(o):
                return BV.giro(esegui=True, adesso=adesso), o.getvalue()
        except BV.Fermo as e:
            uscite.append(str(e))
            return "fermo", str(e)
        except BV.Rimando as e:
            uscite.append(str(e))
            return "rimando", str(e)
        except BV.Avviso as e:
            uscite.append(str(e))
            return "avviso", str(e)
        except Interrotto:
            return "interrotto", ""
        except Exception as e:  # noqa: BLE001
            return "eccezione", f"{type(e).__name__}: {e}"
        finally:
            uscite.append(o.getvalue())

    def vecchi():
        return [iscritto(i, 24 * (40 + i)) for i in range(50, 55)]      # i lettori di prima: mai il benvenuto

    # l'orologio di prova: quello vero più il tempo "passato" nelle pause, che qui non aspettano (un'attesa di minuti
    # dura un istante, ma lo script la vede tutta)
    passato = {"t": 0.0}
    orologio_vero, pausa_vera = BV.orologio, BV.pausa

    def vero_orologio():
        return orologio_vero() + passato["t"]

    def vera_pausa(secondi):
        passato["t"] += max(0, secondi)
    vero, vera_attesa = BV.nl.kit, BV.ATTESA_LETTURE
    BV.ATTESA_LETTURE, BV.orologio, BV.pausa = 0, vero_orologio, vera_pausa
    try:
        # 1. Kit che risponde bene: 2 h, 30 h, 3 giorni fa (dopo l'accensione) ricevono; 5 giorni fa (prima
        #    dell'accensione), i lettori di prima e il non confermato no
        k = KitFinto([iscritto(1, 2), iscritto(2, 30), iscritto(3, 72), iscritto(4, 1, "inactive"), iscritto(5, 24 * 5)] + vecchi())
        r, msg = giro(k)
        attesa = {1: 1, 2: 1, 3: 1, 4: 0, 5: 0, **{i: 0 for i in range(50, 55)}}
        b = list(k.invii.values())
        if r != 0 or len(b) != 1 or k.posta() != attesa:
            male.append(f"giro normale: attese mail a 1, 2 e 3 soli, trovato {k.posta()} ({msg[:80]})")
        else:
            t = datetime.fromisoformat(b[0]["send_at"].replace("Z", "+00:00"))
            if abs((t - SERA - timedelta(minutes=BV.ATTESA_MINUTI)).total_seconds()) > 60 or b[0]["email_template"]["id"] != 5 \
                    or not b[0]["description"].startswith("gommberg-benvenuto-2026-12-02-1930"):
                male.append("invio: ora, cornice o etichetta sbagliate")
        posts = [c for c in k.chiamate if c[0] == "POST" and c[1] == "/broadcasts"]
        if len(posts) != 1 or posts[0][2]["send_at"] is not None:
            male.append("l'invio non nasce in bozza (creazione unica, poi programmazione)")
        elif posts[0][2]["subscriber_filter"] != [{"all": [{"type": "tag", "ids": posts[0][2]["subscriber_filter"][0]["all"][0]["ids"]}], "any": None, "none": None}]:
            male.append("subscriber_filter non nella forma della documentazione (all, any: null, none: null)")      # punto 5
        if posts and (f"alle {GG.ORA_USCITA}" not in posts[0][2]["content"] or "[[" in posts[0][2]["content"]):
            male.append("il testo spedito non ha l'ora di giorni.ORA_USCITA")
        i_post = [n for n, c in enumerate(k.chiamate) if c[0] == "POST" and c[1] == "/broadcasts"]
        i_put = [n for n, c in enumerate(k.chiamate) if c[0] == "PUT"]
        letture = [n for n, c in enumerate(k.chiamate) if c[0] == "GET" and re.match(r"^/broadcasts/\d+$", c[1])]
        if not (i_post and i_put and any(i_post[0] < n < i_put[0] for n in letture) and any(n > i_put[0] for n in letture)):
            male.append("manca la rilettura (GET) della bozza prima della programmazione o dell'invio dopo")          # punto 4
        # 2. secondo giro nello stesso giorno, e le sere dopo (la finestra di 7 giorni li vede ancora): nessun doppione
        for adesso in (SERA + timedelta(minutes=40), SERA + timedelta(days=1), SERA + timedelta(days=5)):
            giro(k, adesso)
        if len(k.invii) != 1 or max(k.posta().values()) > 1:
            male.append(f"giri successivi: {len(k.invii)} invii, posta {k.posta()}")
        # 3. punto 6: chi si iscrive e conferma giorni dopo, o perde giri, lo riceve entro 7 giorni; dopo 7 giorni no
        DOPO = SERA + timedelta(days=20)
        k = KitFinto([iscritto(1, 24 * 6, quando_=DOPO), iscritto(2, 24 * 8, quando_=DOPO)])
        if giro(k, DOPO)[0] != "avviso" or k.posta() != {1: 1, 2: 0}:
            male.append(f"finestra di 7 giorni: posta {k.posta()} (attesa: 6 giorni fa sì, 8 giorni fa no)")
        # 4. zero nuovi iscritti: nessuna scrittura in Kit
        k = KitFinto(vecchi())
        r, msg = giro(k)
        if r != 0 or k.scritture():
            male.append(f"zero nuovi: {len(k.scritture())} scritture in Kit")
        # 5. un iscritto nuovo ma già etichettato, anche se l'elenco non mostra le etichette
        for nascondi in (False, True):
            k = KitFinto([iscritto(1, 30), iscritto(2, 3)], etichette=[("gommberg-benvenuto", {1})], nascondi_tag=nascondi)
            r, msg = giro(k)
            if r != 0 or k.posta() != {1: 0, 2: 1}:
                male.append(f"iscritto già etichettato (etichette {'nascoste' if nascondi else 'visibili'}): posta {k.posta()}")
        # 6. Kit che sbaglia sempre (5xx), non risponde (rete) o risponde in modo illeggibile: fermo, nessuna scrittura
        for nome, risposta in (("risponde 503", (503, {})), ("rete muta", (0, {"errore": "rete: timeout"})),
                               ("200 non JSON", ValueError("Expecting value"))):
            k = KitFinto([iscritto(1, 2)])
            k.guasti["GET /*"] = risposta
            r, msg = giro(k)
            if r != "fermo" or k.scritture() or len(k.chiamate) != BV.LETTURE:
                male.append(f"Kit che {nome}: esito {r}, {len(k.scritture())} scritture, {len(k.chiamate)} chiamate")
        k = KitFinto([iscritto(1, 2)])
        k.guasti["GET /subscribers"] = [(503, {}), (502, {})]
        if giro(k)[0] != 0 or k.posta() != {1: 1}:
            male.append("due guasti momentanei sull'elenco degli iscritti: il giro non si riprende")
        # 7. risposte fuori forma: fermo prima di scrivere
        for nome, via, risposta in (("elenco senza paginazione", "GET /subscribers", (200, {"subscribers": []})),
                                    ("elenco non JSON", "GET /subscribers", (200, "<html>")),
                                    ("iscritto senza etichette", "GET /subscribers", (200, {"subscribers": [{"id": 1, "state": "active", "created_at": "2026-12-02T17:00:00Z"}],
                                                                                           "pagination": {"has_next_page": False}})),
                                    ("etichette senza paginazione", "GET /tags", (200, {"tags": []})),
                                    ("pagina dopo senza cursore", "GET /tags", (200, {"tags": [], "pagination": {"has_next_page": True}}))):
            k = KitFinto([iscritto(1, 2)])
            k.guasti[via] = risposta
            r, msg = giro(k)
            if r != "fermo" or k.scritture():
                male.append(f"risposta fuori forma ({nome}): esito {r}, {len(k.scritture())} scritture")
        # 8. filtro per data ignorato, troppi nuovi, cornice mancante, gruppo già esistente o con un iscritto in più
        k = KitFinto([iscritto(1, 2)] + vecchi(), ignora_data=True)
        if giro(k)[0] != "fermo" or k.scritture():
            male.append("filtro per data ignorato da Kit: il giro non si ferma")
        k = KitFinto([iscritto(i, 5) for i in range(1, BV.MAX_NUOVI + 2)])
        if giro(k)[0] != "fermo" or k.scritture():
            male.append("oltre MAX_NUOVI iscritti nuovi: il giro non si ferma")
        k = KitFinto([iscritto(1, 2)], modelli=((7, "Gommberg"),))
        if giro(k)[0] != "fermo" or k.scritture():
            male.append("senza la cornice in Kit: il giro non si ferma")
        k = KitFinto([iscritto(1, 2)], etichette=[("gommberg-benvenuto-2026-12-02-1930", {50})])
        if giro(k)[0] != "fermo" or k.invii:
            male.append("etichetta del gruppo già esistente: il giro non si ferma")
        def gruppo_in_piu_di(_k):
            def kit(metodo, percorso, dati=None):
                st, corpo = _k(metodo, percorso, dati)
                if metodo == "GET" and re.match(r"^/tags/\d+/subscribers\?", percorso) and "-2026-" in _k.tag.get(int(percorso.split("/")[2]), ""):
                    corpo = dict(corpo, subscribers=corpo["subscribers"] + [{"id": 50}])
                return st, corpo
            return kit
        k = KitFinto([iscritto(1, 2)] + vecchi())
        if giro(gruppo_in_piu_di(k))[0] != "fermo" or k.invii:
            male.append("gruppo in Kit con un iscritto in più del voluto: invio creato lo stesso")
        # 9. la bozza: Kit la registra a tutti (risposta onesta, o risposta che ripete il filtro chiesto: lo dice la
        #    rilettura) -> tolta, mai programmata (punto 4)
        for nome, attr in (("risposta onesta", "crea_a_tutti"), ("risposta che mente", "crea_mente")):
            k = KitFinto([iscritto(1, 2)] + vecchi())
            setattr(k, attr, True)
            r, msg = giro(k)
            if r != "fermo" or k.invii or any(c[0] == "PUT" for c in k.chiamate) or max(k.posta().values()) > 0:
                male.append(f"bozza registrata a tutti ({nome}): non tolta o programmata lo stesso")
        # 10. la creazione dall'esito incerto (nasce ma risponde 0, 500, 200 fuori forma o illeggibile): mai ritentata,
        #     la bozza si trova per etichetta e si toglie; il giro dopo non rimanda
        for nome, g in (("timeout", ("dopo", 0, {"errore": "rete"})), ("500", ("dopo", 500, {})), ("200 fuori forma", ("dopo", 200, {"ok": 1})),
                        ("200 non JSON", ("dopo", ValueError("Expecting value"), None))):
            k = KitFinto([iscritto(1, 2)] + vecchi())
            k.guasti["POST /broadcasts"] = g
            r, msg = giro(k)
            n_post = len([c for c in k.chiamate if c[0] == "POST" and c[1] == "/broadcasts"])
            if r != "fermo" or n_post != 1 or k.invii or any(c[0] == "PUT" for c in k.chiamate):
                male.append(f"creazione con esito incerto ({nome}): esito {r}, {n_post} creazioni, {len(k.invii)} invii rimasti")
            del k.guasti["POST /broadcasts"]
            if any(n == "gommberg-benvenuto" and m for i, n in k.tag.items() for m in [k.membri[i]]):
                male.append(f"creazione con esito incerto ({nome}): qualcuno è stato segnato senza mail")
            giro(k, SERA + timedelta(minutes=30))
            giro(k, SERA + timedelta(minutes=60))
            if len(k.invii) != 1 or k.posta() != {1: 1, **{i: 0 for i in range(50, 55)}}:      # nessuno era segnato: ora una mail, una sola
                male.append(f"dopo una creazione incerta ({nome}): {len(k.invii)} invii, posta {k.posta()} (attesa: una mail al nuovo iscritto)")
        # 11. la programmazione (punti 1, 2, 4): rifiutata, a tutti con risposta onesta o che mente, in timeout con Kit
        #     che cambia il filtro, illeggibile: l'invio si toglie. In timeout ma applicata giusta: parte, una volta
        for nome, prepara, parte in (
                ("422", lambda k: k.guasti.__setitem__("PUT /broadcasts*", (422, {"errors": ["no"]})), False),
                ("a tutti, risposta onesta", lambda k: setattr(k, "put_a_tutti", True), False),
                ("a tutti, risposta che mente", lambda k: setattr(k, "put_mente", True), False),
                ("timeout e filtro cambiato", lambda k: (setattr(k, "put_a_tutti", True), k.guasti.__setitem__("PUT /broadcasts*", ("dopo", 0, {}))), False),
                ("200 non JSON e filtro cambiato", lambda k: (setattr(k, "put_a_tutti", True),
                                                             k.guasti.__setitem__("PUT /broadcasts*", ("dopo", ValueError("x"), None))), False),
                ("200 fuori forma, applicata giusta", lambda k: k.guasti.__setitem__("PUT /broadcasts*", ("dopo", 200, {"x": 1})), True),
                ("timeout, applicata giusta", lambda k: k.guasti.__setitem__("PUT /broadcasts*", ("dopo", 0, {})), True),
                ("timeout e rilettura impossibile", lambda k: k.guasti.__setitem__("PUT /broadcasts*", ("dopo", 0, {})), False)):
            k = KitFinto([iscritto(1, 2)] + vecchi())
            prepara(k)
            if nome == "timeout e rilettura impossibile":     # la prima rilettura (della bozza) va, poi Kit non risponde più
                letture = {"n": 0}

                def rilettura(metodo, percorso, dati=None, _k=k):
                    if metodo == "GET" and re.match(r"^/broadcasts/\d+$", percorso):
                        letture["n"] += 1
                        if letture["n"] > 1:
                            _k.chiamate.append((metodo, percorso, None))
                            return 503, {}
                    return _k(metodo, percorso, dati)
                r, msg = giro(rilettura)
            else:
                r, msg = giro(k)
            atteso = {1: 1 if parte else 0, **{i: 0 for i in range(50, 55)}}
            if k.posta() != atteso or (r == 0) != parte or r == "eccezione":
                male.append(f"programmazione ({nome}): esito {r}, posta {k.posta()} ({msg[:70]})")
        # 12. punto 3: l'invio sbagliato che non si toglie si riporta in bozza; se non si può, URGENTE
        k = KitFinto([iscritto(1, 2)] + vecchi())
        k.put_a_tutti, k.delete_rotto = True, True
        orig = k.esegui

        def put_bozza_giusta(metodo, percorso, dati, _o=orig, _k=k):          # la PUT di ripiego (send_at null) riesce
            if metodo == "PUT" and dati.get("send_at") is None:
                _k.put_a_tutti = False
            return _o(metodo, percorso, dati)
        k.esegui = put_bozza_giusta
        r, msg = giro(k)
        if r != "fermo" or max(k.posta().values()) > 0 or "riportato in bozza" not in msg or "URGENTE" in msg:
            male.append(f"invio sbagliato non tolto: non riportato in bozza ({msg[:80]})")
        k = KitFinto([iscritto(1, 2)] + vecchi())
        k.put_a_tutti, k.delete_rotto = True, True
        orig = k.esegui

        def put_rotta_dopo(metodo, percorso, dati, _o=orig, _k=k):            # anche la PUT di ripiego fallisce
            if metodo == "PUT" and dati.get("send_at") is None:
                return 500, {}
            return _o(metodo, percorso, dati)
        k.esegui = put_rotta_dopo
        r, msg = giro(k)
        if r != "fermo" or "URGENTE" not in msg or "FERMALO A MANO" not in msg:
            male.append(f"invio sbagliato né tolto né in bozza: manca l'URGENTE ({msg[:80]})")
        # 13. giro interrotto a metà: mai due mail, e nessuno segnato senza mail finché l'etichetta permanente non è data
        #     (viene dopo la bozza riletta, subito prima della programmazione)
        def interrompi(k, quando_):
            def kit(metodo, percorso, dati=None):
                if quando_(metodo, percorso, k):
                    raise Interrotto()
                return k(metodo, percorso, dati)
            return kit

        def permanente(metodo, percorso, k, chi):
            return (metodo == "POST" and re.match(rf"^/tags/\d+/subscribers/{chi}$", percorso)
                    and k.tag.get(int(percorso.split("/")[2])) == "gommberg-benvenuto")
        for nome, quando_, attesa in (
                ("durante le etichette del gruppo", lambda m, p, k: m == "POST" and re.match(r"^/tags/\d+/subscribers/2$", p), {1: 1, 2: 1}),
                ("mentre aspetta il gruppo", lambda m, p, k: m == "GET" and re.match(r"^/tags/\d+/subscribers\?", p) and "-2026-" in k.tag.get(int(p.split("/")[2]), ""), {1: 1, 2: 1}),
                ("alla creazione della bozza", lambda m, p, k: m == "POST" and p == "/broadcasts", {1: 1, 2: 1}),
                ("alla rilettura della bozza", lambda m, p, k: m == "GET" and re.match(r"^/broadcasts/\d+$", p), {1: 1, 2: 1}),
                ("alla prima etichetta permanente", lambda m, p, k: permanente(m, p, k, 1), {1: 1, 2: 1}),
                ("tra le due etichette permanenti", lambda m, p, k: permanente(m, p, k, 2), {1: 0, 2: 1}),
                ("alla programmazione", lambda m, p, k: m == "PUT", {1: 0, 2: 0})):
            k = KitFinto([iscritto(1, 3), iscritto(2, 2)])
            r, _ = giro(interrompi(k, quando_))
            prima = dict(k.posta())
            giro(k, SERA + timedelta(minutes=30))
            giro(k, SERA + timedelta(days=1))
            if r != "interrotto" or any(prima.values()) or k.posta() != attesa:
                male.append(f"interrotto {nome}: esito {r}, posta {k.posta()}, attesa {attesa}")
        # 14. orari (punto 7): mai tra le 21 e le 8 né nella fascia dell'edizione; il salto si scrive nel registro e due
        #     sere di fila fermano il giro (segnalazione); un salto sola non è un errore
        for nome, quando_ in (("20:55 (invio alle 21:05)", SERA.replace(hour=20, minute=55)), ("7:30", SERA.replace(hour=7, minute=30)),
                              ("9:00, fascia dell'edizione", SERA.replace(hour=9, minute=0)), ("8:25 (invio alle 8:35)", SERA.replace(hour=8, minute=25)),
                              ("23:00", SERA.replace(hour=23, minute=0))):
            k = KitFinto([iscritto(1, 1)])
            r, msg = giro(k, quando_)
            if r != 0 or k.invii_scritti() or any("/subscribers/" in c[1] for c in k.scritture()) or "saltato per l'orario" not in msg:
                male.append(f"alle {nome}: il giro ha scritto un invio o un'etichetta a un iscritto, o non lo dice nel registro")
        #     due sere saltate: solo la riga nel registro, nessuna scrittura in Kit; il giro dopo spedisce e avvisa chi
        #     aspettava da più di 3 giorni (segnalazione), non chi aspetta da 3 giorni o meno
        k = KitFinto([iscritto(1, 24 * 3 - 1), iscritto(2, 24 * 2)])
        r1, _ = giro(k, SERA.replace(hour=23, minute=0))
        r2, _ = giro(k, (SERA + timedelta(days=1)).replace(hour=23, minute=0))
        if r1 != 0 or r2 != 0 or k.scritture():
            male.append("giri saltati per l'orario: scritture in Kit o uscita diversa da 0")
        r3, msg = giro(k, SERA + timedelta(days=2))
        if r3 != "avviso" or "più di 3 giorni" not in msg or k.posta() != {1: 1, 2: 1}:
            male.append(f"chi aspetta da più di 3 giorni: benvenuto non spedito o nessun avviso ({r3}, {k.posta()})")
        k = KitFinto([iscritto(1, 24 * 3 - 1)])
        if giro(k)[0] != 0:
            male.append("avviso per chi aspetta da meno di 3 giorni")
        k = KitFinto([iscritto(1, 1)])
        if giro(k, SERA.replace(hour=10, minute=31))[0] != 0 or k.posta() != {1: 1}:
            male.append("alle 10:31 (fuori dalla fascia) il benvenuto non parte")
        h, m = GG.ora_uscita()
        da, a = BV.fascia_edizione(SERA.date())
        if (da.hour * 60 + da.minute, a.hour * 60 + a.minute) != (h * 60 + m - 75, h * 60 + m + 45):
            male.append("la fascia dell'edizione non segue giorni.ORA_USCITA")
        # 15. tempo (D1). Con l'orologio finto ogni chiamata a Kit costa i secondi detti: il giro prende in carico solo
        #     gli iscritti che stanno nel tempo, gli altri restano senza nessuna etichetta e li serve il giro dopo; e
        #     nessuno riceve l'etichetta permanente se poi l'invio non viene programmato
        def giro_lento(k, costo, adesso=SERA, n_prima=None):
            """Un giro con Kit che risponde in `costo(metodo, percorso)` secondi: (esito, messaggio)."""
            finto = {"t": 0.0}

            def kit(metodo, percorso, dati=None):
                finto["t"] += costo(metodo, percorso)
                return k(metodo, percorso, dati)
            BV.ferma_scadenza()
            BV.orologio, BV.pausa = (lambda: finto["t"]), (lambda sec: finto.__setitem__("t", finto["t"] + sec))
            o = io.StringIO()
            try:
                BV.avvia_scadenza()
                BV.nl.kit = kit
                with contextlib.redirect_stdout(o):
                    return BV.giro(esegui=True, adesso=adesso), o.getvalue()
            except BV.Fermo as e:
                return "fermo", o.getvalue() + str(e)
            except BV.Rimando as e:
                return "rimando", o.getvalue() + str(e)
            except BV.Avviso as e:
                return "avviso", o.getvalue() + str(e)
            finally:
                uscite.append(o.getvalue())
                BV.ferma_scadenza()
                BV.orologio, BV.pausa = vero_orologio, vera_pausa

        def segnati(k):
            """Chi ha l'etichetta permanente."""
            return set().union(*[m for i, m in k.membri.items() if k.tag[i] == "gommberg-benvenuto"] or [set()])

        def serviti(k):
            return {i for i, n in k.posta().items() if n}

        for nome, secondi, quanti in (("Kit a 1 secondo e 6 nuovi", 1.0, 6), ("Kit a 0,3 secondi e 30 nuovi", 0.3, 30), ("Kit a 0,45 secondi e 39 nuovi", 0.45, 39)):
            k = KitFinto([iscritto(i, i) for i in range(1, quanti + 1)])
            r, msg = giro_lento(k, lambda m, p, _s=secondi: _s)
            if r != 0 or serviti(k) != set(range(1, quanti + 1)) or max(k.posta().values()) != 1 or segnati(k) != serviti(k):
                male.append(f"{nome}: esito {r}, {len(serviti(k))} serviti e {len(segnati(k))} segnati su {quanti} ({msg[-90:]})")
        #     troppi per una sera: una parte stasera (chi aspetta da più tempo), gli altri intatti, il resto le sere dopo
        k = KitFinto([iscritto(i, i) for i in range(1, 31)])
        r, msg = giro_lento(k, lambda m, p: 1.5)
        primi = serviti(k)
        con_etichette = {i for m in k.membri.values() for i in m}
        if r != 0 or not 0 < len(primi) < 30 or primi != set(range(31 - len(primi), 31)) or segnati(k) != primi or con_etichette != primi \
                or "restano candidati per il prossimo giro" not in msg:
            male.append(f"Kit a 1,5 secondi e 30 nuovi: esito {r}, serviti {len(primi)}, segnati {len(segnati(k))}, toccati {len(con_etichette)} ({msg[-90:]})")
        for g in range(1, 4):
            giro_lento(k, lambda m, p: 1.5, SERA + timedelta(days=g))
        if serviti(k) != set(range(1, 31)) or max(k.posta().values()) != 1 or segnati(k) != serviti(k):
            male.append(f"Kit a 1,5 secondi e 30 nuovi, le sere dopo: {len(serviti(k))} serviti su 30, al massimo {max(k.posta().values())} mail a testa")
        #     Kit troppo lento per servire anche uno solo: fermo senza nessuna scrittura
        k = KitFinto([iscritto(1, 2), iscritto(2, 3)])
        r, msg = giro_lento(k, lambda m, p: 20.0)
        if r != "fermo" or k.scritture() or "nemmeno un iscritto" not in msg:
            male.append(f"Kit a 20 secondi: esito {r}, {len(k.scritture())} scritture ({msg[-80:]})")
        #     Kit che rallenta a metà: prima delle etichette permanenti (dopo la bozza) nessuno viene segnato e la bozza
        #     si toglie; durante le etichette permanenti la programmazione non parte (chi è segnato perde la guida, mai due)
        for nome, costo, attesi_segnati in (
                ("alla rilettura della bozza", lambda m, p: 230.0 if m == "GET" and re.match(r"^/broadcasts/\d+$", p) else 0.3, set()),
                ("alla rilettura della bozza, con poco tempo rimasto", lambda m, p: 205.0 if m == "GET" and re.match(r"^/broadcasts/\d+$", p) else 0.3, set()),
                ("mentre aspetta il gruppo", lambda m, p: 205.0 if m == "GET" and re.match(r"^/tags/\d+/subscribers\?status=all&per_page=\d+$", p) else 0.3, set()),
                ("alle etichette permanenti", lambda m, p: 0.3, None)):
            k = KitFinto([iscritto(1, 2), iscritto(2, 3)])
            if attesi_segnati is None:
                def costo(m, p, _k=k):
                    permanente_ = m == "POST" and re.match(r"^/tags/\d+/subscribers/\d+$", p) and _k.tag.get(int(p.split("/")[2])) == "gommberg-benvenuto"
                    return 150.0 if permanente_ else 0.3
            r, msg = giro_lento(k, costo)
            if r != "fermo" or any(k.posta().values()) or k.invii or any(c[0] == "PUT" for c in k.chiamate) \
                    or (attesi_segnati is not None and segnati(k) != attesi_segnati):
                male.append(f"Kit che rallenta {nome}: esito {r}, posta {k.posta()}, {len(k.invii)} invii, segnati {sorted(segnati(k))} ({msg[-80:]})")
            if attesi_segnati is not None:          # nessuno segnato: la sera dopo tutti ricevono la guida, una volta
                giro(k, SERA + timedelta(days=1))
                if k.posta() != {1: 1, 2: 1}:
                    male.append(f"dopo un giro fermato {nome}: posta {k.posta()} (attesa: una mail a testa)")
        #     i conti: lo script si arrende prima che GitHub chiuda il passo, e l'invio parte dopo
        if not (BV.RISERVA + BV.ATTESA_GRUPPO + BV.MARGINE < BV.PASSO < BV.ALLARME < BV.ATTESA_MINUTI * 60) or BV.LAVORO != BV.PASSO - BV.RISERVA:
            male.append("tempi: PASSO deve contenere riserva, attesa del gruppo e margine, e l'invio deve partire dopo l'allarme")
        # 15b. il ritardo di Kit (1): l'elenco del gruppo arriva dopo un po'; il giro aspetta, poi spedisce.
        #      Se non arriva nel tempo che il passo lascia: rimandato, nessuno segnato, e il giro dopo serve tutti
        def letture_gruppo(k):
            return len([c for c in k.chiamate if c[0] == "GET" and re.match(r"^/tags/\d+/subscribers\?status=all&per_page=\d+$", c[1])
                        and "-2026-" in k.tag.get(int(c[1].split("/")[2]), "")])
        k = KitFinto([iscritto(1, 2), iscritto(2, 3)])
        k.ritardo = 18
        r, msg = giro(k)
        if r != 0 or k.posta() != {1: 1, 2: 1} or "con status=all 0 elementi di cui 0 tra gli attesi, con lo stato predefinito 0 di cui 0 tra gli attesi (x4); poi con status=all 2 elementi di cui 2 tra gli attesi" not in msg:
            male.append(f"elenco del gruppo in ritardo: esito {r}, posta {k.posta()} ({msg[-160:]})")
        k = KitFinto([iscritto(1, 2), iscritto(2, 3)])
        k.ritardo = 10 ** 6
        r, msg = giro(k)
        if r != "rimando" or segnati(k) or k.invii or letture_gruppo(k) not in (BV.ATTESA_GRUPPO // BV.PAUSA_GRUPPO, BV.ATTESA_GRUPPO // BV.PAUSA_GRUPPO + 1) or "in ritardo" not in msg \
                or "letta per id dalla parte di un iscritto atteso, l'etichetta c'è" not in msg:
            male.append(f"elenco del gruppo che non arriva: esito {r}, segnati {sorted(segnati(k))}, {len(k.invii)} invii, {letture_gruppo(k)} letture ({msg[-80:]})")
        k.ritardo = 0
        r, msg = giro(k, SERA + timedelta(days=1))
        if r != 0 or k.posta() != {1: 1, 2: 1}:
            male.append(f"dopo un giro rimandato: esito {r}, posta {k.posta()} (attesa: una mail a testa)")
        #      rimandato con qualcuno che aspetta da più di 3 giorni: avviso (non si rimanda in silenzio per sempre)
        k = KitFinto([iscritto(1, 24 * 4)])
        k.ritardo = 10 ** 6
        r, msg = giro(k, SERA + timedelta(days=2))
        if r != "avviso" or segnati(k) or k.invii or "più di 3 giorni" not in msg:
            male.append(f"rimandato con chi aspetta da più di 3 giorni: esito {r} ({msg[-80:]})")
        #      con l'orologio del passo: l'attesa non è di 120 secondi fissi, dura finché il passo lascia tempo (E3). Con
        #      un iscritto e Kit svelto sono più di tre minuti; un elenco che arriva dopo 170 secondi viene aspettato
        k = KitFinto([iscritto(1, 2)])
        k.ritardo = 10 ** 6
        r, msg = giro_lento(k, lambda m, p: 0.2)
        attesa = re.search(r"riletture in (\d+) secondi", msg)
        if r != "rimando" or segnati(k) or not attesa or not 180 <= int(attesa.group(1)) <= BV.LAVORO:
            male.append(f"attesa del gruppo con l'orologio del passo: esito {r}, attesa {attesa.group(1) if attesa else '?'} secondi")
        k = KitFinto([iscritto(1, 2)])
        k.ritardo = 170
        r, msg = giro_lento(k, lambda m, p: 0.2)
        if r != 0 or k.posta() != {1: 1}:
            male.append(f"elenco del gruppo che arriva dopo 170 secondi: esito {r}, posta {k.posta()} ({msg[-100:]})")
        #      l'elenco con status=all che non restituisce mai nulla, mentre quello con lo stato predefinito sì: il gruppo
        #      si riconosce lo stesso, e il riepilogo dice che cosa ha dato ciascuno
        k = KitFinto([iscritto(1, 2), iscritto(2, 3)])
        k.tutti_vuoto = True
        r, msg = giro(k)
        if r != 0 or k.posta() != {1: 1, 2: 1} or "con status=all 0 elementi di cui 0 tra gli attesi, con lo stato predefinito 2 di cui 2 tra gli attesi" not in msg:
            male.append(f"elenco con status=all sempre vuoto: esito {r}, posta {k.posta()} ({msg[-160:]})")
        #      un estraneo visto solo con lo stato predefinito, o solo con status=all, ferma lo stesso
        for solo in ("all", None):
            k = KitFinto([iscritto(1, 2)] + vecchi())

            def estraneo_in_un_elenco(metodo, percorso, dati=None, _k=k, _solo=solo):
                st, corpo = _k(metodo, percorso, dati)
                if metodo == "GET" and re.match(r"^/tags/\d+/subscribers\?", percorso) and "-2026-" in _k.tag.get(int(percorso.split("/")[2]), "") \
                        and ("status=all" in percorso) == (_solo == "all"):
                    corpo = dict(corpo, subscribers=corpo["subscribers"] + [{"id": 50}])
                return st, corpo
            if giro(estraneo_in_un_elenco)[0] != "fermo" or k.invii or segnati(k):
                male.append(f"iscritto estraneo visto solo nell'elenco {'con status=all' if solo else 'con lo stato predefinito'}: il giro non si ferma")
        #      un iscritto nel gruppo che non gli è stato dato non è un ritardo: fermo subito, senza aspettare
        k = KitFinto([iscritto(1, 2)] + vecchi())
        r, msg = giro(gruppo_in_piu_di(k))
        if r != "fermo" or letture_gruppo(k) != 1 or segnati(k) or k.invii:
            male.append(f"iscritto estraneo nel gruppo: esito {r}, {letture_gruppo(k)} riletture")
        #      l'etichetta data ma con una risposta che parla di un altro iscritto: non vale
        k = KitFinto([iscritto(1, 2)] + vecchi())
        k.guasti["POST /tags/*"] = [("dopo", 201, {"subscriber": {"id": 50}})]
        r, msg = giro(k)
        if r != "fermo" or segnati(k) or k.invii:
            male.append(f"etichetta confermata per un altro iscritto: esito {r}")
        #      due giri vicini con gli elenchi di Kit in ritardo (l'etichetta permanente non si vede ancora): il secondo
        #      la trova già data alla scrittura, si ferma e toglie la sua bozza; una mail sola
        k = KitFinto([iscritto(1, 2)], nascondi_tag=True)
        giro(k)

        def permanente_nascosta(metodo, percorso, dati=None, _k=k):
            st, corpo = _k(metodo, percorso, dati)
            if metodo == "GET" and re.match(r"^/tags/\d+/subscribers\?", percorso) and _k.tag.get(int(percorso.split("/")[2])) == "gommberg-benvenuto":
                corpo = dict(corpo, subscribers=[])
            return st, corpo
        r, msg = giro(permanente_nascosta, SERA + timedelta(minutes=1))
        if r != "fermo" or k.posta() != {1: 1} or len(k.invii) != 1 or "l'aveva già" not in msg:
            male.append(f"due giri vicini con gli elenchi in ritardo: esito {r}, posta {k.posta()}, {len(k.invii)} invii")
        # 16. il piano non scrive nulla
        k = KitFinto([iscritto(1, 2), iscritto(2, 3)])
        BV.nl.kit = k
        with contextlib.redirect_stdout(io.StringIO()):
            BV.giro(esegui=False, adesso=SERA)
        if k.scritture():
            male.append("il piano scrive in Kit")
        # 17. la prova dal vivo (bozza e prova), dalla riga di comando come la lancia dem.yml, con l'iscritto di prova
        #     indicato per impronta: mai un invio a destinatari diversi dal solo iscritto dell'impronta, mai un indirizzo
        #     in ciò che lo script stampa o chiede a Kit
        CASA = "casa@prova.it"
        IMPR = "impronta:" + hashlib.sha256(CASA.encode("utf-8")).hexdigest()[:16]
        NESSUNO = {1: 0, 2: 0, **{i: 0 for i in range(50, 55)}}
        SOLO_LUI = {**NESSUNO, 1: 1}

        class OraFerma(datetime):
            ferma = SERA

            @classmethod
            def now(cls, tz=None):
                return cls.ferma.astimezone(tz) if tz else cls.ferma

        def mondo(stato="active", in_piu=()):
            return KitFinto([dict(iscritto(1, 24 * 90, stato), email_address="Casa@Prova.it"), iscritto(2, 3)] + vecchi() + list(in_piu))

        def comando(k, *argomenti, adesso=SERA, via=None, orologio=None, pausa=None, entra=""):
            """benvenuto.py dalla riga di comando (main), con il Kit finto e l'ora ferma: (uscita, tutto ciò che stampa)."""
            BV.ferma_scadenza()
            BV.nl.kit = (via or k)
            OraFerma.ferma = adesso
            BV.datetime, BV.orologio, BV.pausa = OraFerma, (orologio or vero_orologio), (pausa or vera_pausa)
            o, argv, stdin = io.StringIO(), sys.argv, sys.stdin
            sys.argv, sys.stdin = ["benvenuto.py", *argomenti], io.StringIO(entra)
            try:
                with contextlib.redirect_stdout(o), contextlib.redirect_stderr(o):
                    try:
                        BV.main()
                        rc = 0
                    except SystemExit as e:
                        rc = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
                        o.write(e.code if isinstance(e.code, str) else "")
                    except BaseException:  # noqa: BLE001
                        rc = "tracciato"
                        o.write(traceback.format_exc())
            finally:
                BV.ferma_scadenza()
                sys.argv, sys.stdin, BV.datetime, BV.orologio, BV.pausa = argv, stdin, datetime, vero_orologio, vera_pausa
            uscite.append(o.getvalue())
            if k is not None and any("@" in c[1] or "%40" in c[1] or "email_address" in c[1] for c in k.chiamate):
                viva.append(f"{' '.join(argomenti[:1])}: un indirizzo in una richiesta a Kit")
            return rc, o.getvalue()

        def con_bozza(k=None):
            """Un mondo con la bozza di prova già fatta e in ordine: (kit, id del gruppo di prova, id della bozza)."""
            k = k or mondo()
            rc, out = comando(k, "bozza", IMPR)
            g = [i for i, n in k.tag.items() if n == "gommberg-benvenuto-prova-2026-12-02-1930"]
            if rc != 0 or len(g) != 1 or len(k.invii) != 1:
                viva.append(f"bozza di prova non riuscita ({out[-120:]})")
                return k, None, None
            return k, g[0], list(k.invii)[0]

        def fermo_pulito(nome, k, rc, out, atteso="DA GUARDARE", invii=0):
            """Il caso deve finire fermo: uscita 1, nessuna mail a nessuno, nessun invio programmato, gli invii rimasti attesi."""
            if rc != 1 or atteso not in out or any(k.posta().values()) or len(k.invii) != invii or any(b["send_at"] for b in k.invii.values()):
                viva.append(f"{nome}: uscita {rc}, posta {k.posta()}, {len(k.invii)} invii rimasti ({out.strip()[-100:]})")

        #    il piano dalla riga di comando (prova-piano): solo letture, solo conti
        k = KitFinto([dict(iscritto(1, 2), email_address=CASA), iscritto(2, 3)] + vecchi())
        rc, out = comando(k, "piano")
        if rc != 0 or k.scritture() or "2 da salutare" not in out or "Piano: etichetta del gruppo e invio alle 19:40 per 2 iscritti" not in out:
            viva.append(f"piano dalla riga di comando: uscita {rc}, {len(k.scritture())} scritture ({out.strip()[-80:]})")
        # a. l'impronta: la stessa per maiuscole e spazi, calcolata senza ripetere l'indirizzo; senza indirizzo, errore
        rc, out = comando(None, "impronta", entra="  Casa@Prova.IT \n")
        if rc != 0 or out.strip() != IMPR.split(":")[1]:
            viva.append(f"impronta: attesa {IMPR.split(':')[1]}, trovato {out.strip()[:40]}")
        rc, out = comando(None, "impronta", entra="casa\n")
        if rc != 1 or "casa" in out.lower().replace("caso", ""):
            viva.append("impronta senza indirizzo: non si ferma, o ripete ciò che ha letto")
        # b. l'iscritto di prova si indica solo con l'impronta: un indirizzo in chiaro o un'impronta storta non fanno nulla
        for modo in ("bozza", "prova"):
            for nome, chi in (("indirizzo in chiaro", CASA), ("impronta corta", "impronta:3b0d06"), ("impronta vuota", "impronta:"),
                              ("senza prefisso", IMPR.split(":")[1]), ("impronta di nessuno", "impronta:" + "0" * 16)):
                k = mondo()
                rc, out = comando(k, modo, chi)
                fermo_pulito(f"{modo}, {nome}", k, rc, out)
                if k.scritture() or (nome != "impronta di nessuno" and k.chiamate and modo == "bozza" and len(k.chiamate) > 1):
                    viva.append(f"{modo}, {nome}: scritture in Kit o letture oltre la cornice")
            # c. due iscritti attivi con la stessa impronta; l'iscritto non confermato; Kit che ignora il filtro sullo stato
            k = mondo(in_piu=[dict(iscritto(9, 5), email_address="casa@prova.it")])
            rc, out = comando(k, modo, IMPR)
            fermo_pulito(f"{modo}, impronta di due iscritti", k, rc, out, "corrisponde a 2 iscritti")
            k = mondo(stato="inactive")
            rc, out = comando(k, modo, IMPR)
            fermo_pulito(f"{modo}, iscritto non confermato", k, rc, out, "corrisponde a 0 iscritti")
            k2 = mondo()
            k2.guasti["GET /subscribers"] = (200, {"subscribers": [{"id": 1, "state": "inactive", "email_address": CASA, "created_at": "2026-09-01T00:00:00Z"}],
                                                   "pagination": {"has_next_page": False}})
            rc2, out2 = comando(k2, modo, IMPR)
            fermo_pulito(f"{modo}, non confermato restituito lo stesso da Kit", k2, rc2, out2, "fuori forma")
            if k.scritture() or k2.scritture():
                viva.append(f"{modo}: scritture in Kit senza un iscritto di prova certo")
            # d. Kit che non dice gli indirizzi, o risponde con un errore che ne contiene uno: fermo, e l'indirizzo non esce
            for nome, risposta in (("elenco senza indirizzi", (200, {"subscribers": [{"id": 1, "state": "active", "created_at": "x"}], "pagination": {"has_next_page": False}})),
                                   ("errore con un indirizzo", (500, {"errore": f"{CASA} non valido"})),
                                   ("risposta illeggibile con un indirizzo", ValueError(f"Expecting value: {CASA}")),
                                   ("elenco troncato", (200, {"subscribers": [{"id": 1, "state": "active", "email_address": CASA}]}))):
                k = mondo()
                k.guasti["GET /subscribers"] = risposta
                rc, out = comando(k, modo, IMPR)
                fermo_pulito(f"{modo}, {nome}", k, rc, out)
                if k.scritture():
                    viva.append(f"{modo}, {nome}: scritture in Kit")
        # e. un errore imprevisto con dentro un indirizzo: mai un tracciato, mai il testo dell'errore
        vera_impronta = BV.impronta_di

        def impronta_rotta(_):
            raise RuntimeError(f"risposta di Kit: {CASA}")
        BV.impronta_di = impronta_rotta
        try:
            k = mondo()
            rc, out = comando(k, "bozza", IMPR)
        finally:
            BV.impronta_di = vera_impronta
        if rc != 1 or not re.search(r"errore imprevisto \(RuntimeError, \w+\.py riga \d+\)", out) or "Traceback" in out or k.scritture():
            viva.append(f"errore imprevisto: uscita {rc} ({out.strip()[-100:]})")
        # f. la bozza: una sola, per un gruppo di prova nuovo con dentro lui solo, mai programmata; niente etichetta permanente
        k, g, bid = con_bozza()
        out = uscite[-1]
        if g is not None and (k.membri[g] != {1} or k.posta() != NESSUNO or any(c[0] == "PUT" for c in k.chiamate)
                              or any(n == "gommberg-benvenuto" for n in k.tag.values()) or k.invii[bid]["vero"] != [{"all": [{"type": "tag", "ids": [g]}], "any": None, "none": None}]):
            viva.append("bozza: gruppo, filtro o stato diversi dal voluto, o etichetta permanente messa")
        for frase in ("trovato per impronta", "iscritti nel gruppo 1", f"bozza {bid}: creata e riletta da Kit, filtro sul solo gruppo di prova, stato bozza",
                      "gruppo riletto dopo la bozza: iscritti nel gruppo 1", "Che cosa resta in Kit", "non dà l'etichetta permanente", "OK: bozza di prova"):
            if g is not None and frase not in out:
                viva.append(f"riepilogo della bozza senza '{frase}'")
        letture_gruppo = [n for n, c in enumerate(k.chiamate) if g is not None and c[0] == "GET" and c[1].startswith(f"/tags/{g}/subscribers")]
        i_post = [n for n, c in enumerate(k.chiamate) if c[0] == "POST" and c[1] == "/broadcasts"]
        if g is not None and not (len(i_post) == 1 and any(n < i_post[0] for n in letture_gruppo) and any(n > i_post[0] for n in letture_gruppo)):
            viva.append("bozza: il gruppo non è contato in Kit prima e dopo la creazione")
        #    due bozze nello stesso minuto: la seconda non riusa il gruppo
        rc, out = comando(k, "bozza", IMPR)
        if g is not None and (rc != 1 or len(k.invii) != 1):
            viva.append("seconda bozza nello stesso minuto: gruppo riusato o seconda bozza creata")
        # g. Kit che risponde male alla creazione (nasce ma risponde 0, 500, fuori forma, illeggibile; registra a tutti,
        #    anche mentendo) e alla rilettura: la bozza si toglie, e prova dopo non trova nulla da programmare
        for nome, prepara in (("timeout", lambda k: k.guasti.__setitem__("POST /broadcasts", ("dopo", 0, {"errore": "rete"}))),
                              ("500", lambda k: k.guasti.__setitem__("POST /broadcasts", ("dopo", 500, {}))),
                              ("200 fuori forma", lambda k: k.guasti.__setitem__("POST /broadcasts", ("dopo", 200, {"ok": 1}))),
                              ("200 non JSON", lambda k: k.guasti.__setitem__("POST /broadcasts", ("dopo", ValueError(CASA), None))),
                              ("rifiuto 422", lambda k: k.guasti.__setitem__("POST /broadcasts", (422, {"errors": [CASA]}))),
                              ("a tutti, risposta onesta", lambda k: setattr(k, "crea_a_tutti", True)),
                              ("a tutti, risposta che mente", lambda k: setattr(k, "crea_mente", True)),
                              ("rilettura muta", lambda k: k.guasti.__setitem__("GET /broadcasts/*", (503, {}))),
                              ("rilettura illeggibile", lambda k: k.guasti.__setitem__("GET /broadcasts/*", ValueError(CASA))),
                              ("rilettura fuori forma", lambda k: k.guasti.__setitem__("GET /broadcasts/*", (200, {"broadcast": [CASA]})))):
            k = mondo()
            prepara(k)
            rc, out = comando(k, "bozza", IMPR)
            fermo_pulito(f"bozza, creazione ({nome})", k, rc, out)
            if len([c for c in k.chiamate if c[0] == "POST" and c[1] == "/broadcasts"]) != 1 or "può essere rimasto in Kit" not in out:
                viva.append(f"bozza, creazione ({nome}): creazione ritentata, o il riepilogo non dice che cosa può essere rimasto")
            k.guasti.clear()
            rc, out = comando(k, "prova", IMPR)
            fermo_pulito(f"prova dopo una bozza fallita ({nome})", k, rc, out, "nessuna bozza di prova")
        # h. il gruppo che in Kit risulta di 2: prima della bozza (nessuna bozza), dopo la bozza (tolta), prima della
        #    programmazione (non si programma), dopo la programmazione (l'invio si toglie)
        def gruppo_di_due(k, dalla=1, dopo_put=False):
            visto = {"n": 0}

            def kit(metodo, percorso, dati=None):
                st, corpo = k(metodo, percorso, dati)
                di_prova = metodo == "GET" and re.match(r"^/tags/\d+/subscribers\?", percorso) and "-prova-" in k.tag.get(int(percorso.split("/")[2]), "")
                if di_prova and (any(c[0] == "PUT" for c in k.chiamate) if dopo_put else True):
                    visto["n"] += 1
                    if visto["n"] >= dalla and st == 200:
                        corpo = dict(corpo, subscribers=corpo["subscribers"] + [{"id": 2}])
                return st, corpo
            return kit
        k = mondo()
        rc, out = comando(k, "bozza", IMPR, via=gruppo_di_due(k))
        fermo_pulito("bozza, gruppo di 2 prima della creazione", k, rc, out, "ha 2 iscritti invece di 1")
        if k.invii_scritti():
            viva.append("bozza, gruppo di 2 prima della creazione: la bozza è stata creata lo stesso")
        k = mondo()
        rc, out = comando(k, "bozza", IMPR, via=gruppo_di_due(k, dalla=2))
        fermo_pulito("bozza, gruppo di 2 dopo la creazione", k, rc, out, "tolto")
        k, g, bid = con_bozza()
        if g is not None:
            k.membri[g].add(2)
            rc, out = comando(k, "prova", IMPR)
            fermo_pulito("prova, gruppo di 2 prima della programmazione", k, rc, out, "non ha dentro il solo iscritto", invii=1)
            if any(c[0] == "PUT" for c in k.chiamate):
                viva.append("prova, gruppo di 2: programmata lo stesso")
        k, g, bid = con_bozza()
        if g is not None:
            orig = k.esegui

            def cresce_dopo(metodo, percorso, dati, _o=orig, _k=k, _g=g):          # un secondo iscritto entra nel gruppo dopo la programmazione
                r = _o(metodo, percorso, dati)
                if metodo == "PUT" and dati.get("send_at"):
                    _k.membri[_g].add(2)
                return r
            k.esegui = cresce_dopo
            rc, out = comando(k, "prova", IMPR)
            fermo_pulito("prova, gruppo di 2 dopo la programmazione", k, rc, out, "tolto")
        k, g, bid = con_bozza()
        if g is not None:                                                      # il gruppo che dopo la programmazione non si rilegge
            n0 = len(k.chiamate)
            rc, out = comando(k, "prova", IMPR, via=(lambda m, p, d=None, _k=k, _g=g: (_k.chiamate.append((m, p, None)) or (503, {}))
                                                     if m == "GET" and p.startswith(f"/tags/{_g}/subscribers") and any(c[0] == "PUT" for c in _k.chiamate) else _k(m, p, d)))
            fermo_pulito("prova, gruppo non riletto dopo la programmazione", k, rc, out, "tolto")
            dopo_put = [c for c in k.chiamate[n0:] if c[0] == "GET" and c[1].startswith(f"/tags/{g}/subscribers?status=all")]
            if len(dopo_put) != 2:                                             # una prima e una sola dopo: il tempo della pulizia è contato
                viva.append(f"prova: il gruppo dopo la programmazione va letto una volta sola, lette {len(dopo_put) - 1}")
        # i. la prova: senza bozza nulla; con la bozza in ordine programma, rilegge, riconta e la mail va a lui solo
        k = mondo()
        rc, out = comando(k, "prova", IMPR)
        fermo_pulito("prova senza bozza", k, rc, out, "nessuna bozza di prova")
        if k.scritture():
            viva.append("prova senza bozza: scritture in Kit")
        k, g, bid = con_bozza()
        if g is not None:
            n0 = len(k.chiamate)
            rc, out = comando(k, "prova", IMPR)
            t = datetime.fromisoformat((k.invii[bid]["send_at"] or "2000-01-01T00:00:00+00:00").replace("Z", "+00:00")) if bid in k.invii else None
            if rc != 0 or k.posta() != SOLO_LUI or len(k.invii) != 1 or not t or abs((t - SERA - timedelta(minutes=BV.ATTESA_MINUTI)).total_seconds()) > 60 \
                    or any(n == "gommberg-benvenuto" for n in k.tag.values()):
                viva.append(f"prova: uscita {rc}, posta {k.posta()} (attesa: una mail al solo iscritto di prova, {BV.ATTESA_MINUTI} minuti dopo)")
            giro_k = k.chiamate[n0:]
            i_put = [n for n, c in enumerate(giro_k) if c[0] == "PUT"]
            if len(i_put) != 1 or giro_k[i_put[0]][2]["subscriber_filter"] != [{"all": [{"type": "tag", "ids": [g]}], "any": None, "none": None}] \
                    or not any(c[0] == "GET" and c[1] == f"/broadcasts/{bid}" for c in giro_k[i_put[0]:]) \
                    or not any(c[0] == "GET" and c[1].startswith(f"/tags/{g}/subscribers") for c in giro_k[:i_put[0]]) \
                    or not any(c[0] == "GET" and c[1].startswith(f"/tags/{g}/subscribers") for c in giro_k[i_put[0]:]) \
                    or [c for c in giro_k if c[0] not in ("GET", "PUT")]:
                viva.append("prova: programmazione senza filtro sul gruppo, senza rilettura, senza il gruppo contato prima e dopo, o con altre scritture")
            for frase in ("trovato per impronta", "riletta da Kit, filtro sul solo gruppo di prova, stato bozza", "iscritti nel gruppo 1, l'iscritto di prova",
                          f"invio {bid}: programmato per le 19:40 (ora di Roma) e riletto da Kit", "gruppo riletto dopo la programmazione: iscritti nel gruppo 1",
                          "Che cosa resta in Kit", "OK: prova programmata"):
                if frase not in out:
                    viva.append(f"riepilogo della prova senza '{frase}'")
            #    una seconda prova non trova più bozze: nessuna seconda mail
            rc, out = comando(k, "prova", IMPR)
            if rc != 1 or k.posta() != SOLO_LUI:
                viva.append("seconda prova: una seconda mail, o nessun fermo")
        # l. la prova con l'impronta di un altro iscritto, e bozze che non sono di un gruppo di prova con lui solo
        k, g, bid = con_bozza()
        if g is not None:
            rc, out = comando(k, "prova", "impronta:" + hashlib.sha256(b"x2@prova.it").hexdigest()[:16])
            fermo_pulito("prova con l'impronta di un altro iscritto", k, rc, out, "non ha dentro il solo iscritto di questa impronta", invii=1)
            if any(c[0] == "PUT" for c in k.chiamate):
                viva.append("prova con l'impronta di un altro iscritto: programmata lo stesso")
        k, g, bid = con_bozza()
        if g is not None:                    # la bozza di prova che Kit ora mostra con un secondo gruppo nel filtro
            k.invii[bid]["vero"] = [{"all": [{"type": "tag", "ids": [g, g + 1000]}], "any": None, "none": None}]
            rc, out = comando(k, "prova", IMPR)
            fermo_pulito("prova, bozza con due gruppi nel filtro", k, rc, out, "non si programma", invii=1)
            if any(c[0] == "PUT" for c in k.chiamate):
                viva.append("prova, bozza con due gruppi nel filtro: programmata lo stesso")
        k, g, bid = con_bozza()
        if g is not None:                    # una bozza più recente che non è di prova non conta: si programma quella di prova
            i = k.nuovo_id()
            k.invii[i] = {"id": i, "subject": "x", "description": "gommberg-dem-2026-12-03", "send_at": None, "email_template": {"id": 5, "name": "Gommberg cornice"}, "vero": TUTTI}
            rc, out = comando(k, "prova", IMPR)
            if rc != 0 or k.posta() != SOLO_LUI or k.invii[i]["send_at"]:
                viva.append(f"prova con una bozza più recente non di prova: uscita {rc}, posta {k.posta()}")
        for nome, etichette, descrizione, filtro in (
                ("bozza sul gruppo permanente", [("gommberg-benvenuto", {1})], "gommberg-benvenuto-prova-2026-12-02-1930", "tag"),
                ("bozza su un'etichetta di prova con un altro nome", [("gommberg-benvenuto-prova-2026-12-01-1200", {1}), ("gommberg-benvenuto-prova-2026-12-02-1930", {1})],
                 "gommberg-benvenuto-prova-2026-12-02-1930", "tag"),
                ("bozza a tutti", [("gommberg-benvenuto-prova-2026-12-02-1930", {1})], "gommberg-benvenuto-prova-2026-12-02-1930", "tutti"),
                ("bozza con un nome che non è di prova", [("gommberg-benvenuto-prova-x", {1})], "gommberg-benvenuto-prova-x", "tag"),
                ("bozza di una mail straordinaria", [("gommberg-dem-2026-12-02", {1})], "gommberg-dem-2026-12-02", "tag")):
            k = mondo()
            for n, chi in etichette:
                i = k.nuovo_id()
                k.tag[i], k.membri[i] = n, set(chi)
            primo = min(k.tag)
            i = k.nuovo_id()
            k.invii[i] = {"id": i, "subject": "x", "description": descrizione, "send_at": None, "email_template": {"id": 5, "name": "Gommberg cornice"},
                          "vero": TUTTI if filtro == "tutti" else [{"all": [{"type": "tag", "ids": [primo]}], "any": None, "none": None}]}
            rc, out = comando(k, "prova", IMPR)
            fermo_pulito(f"prova, {nome}", k, rc, out, invii=1)
            if k.scritture():
                viva.append(f"prova, {nome}: scritture in Kit")
        # m. Kit che risponde male alla programmazione e alla rilettura: l'invio si toglie (o torna in bozza, o URGENTE);
        #    in timeout ma applicata giusta: parte, a lui solo
        for nome, prepara, parte, atteso in (
                ("422", lambda k: k.guasti.__setitem__("PUT /broadcasts*", (422, {"errors": [CASA]})), False, "tolto"),
                ("a tutti, risposta onesta", lambda k: setattr(k, "put_a_tutti", True), False, "tolto"),
                ("a tutti, risposta che mente", lambda k: setattr(k, "put_mente", True), False, "tolto"),
                ("timeout e filtro cambiato", lambda k: (setattr(k, "put_a_tutti", True), k.guasti.__setitem__("PUT /broadcasts*", ("dopo", 0, {}))), False, "tolto"),
                ("200 non JSON e filtro cambiato", lambda k: (setattr(k, "put_a_tutti", True), k.guasti.__setitem__("PUT /broadcasts*", ("dopo", ValueError(CASA), None))), False, "tolto"),
                ("rilettura muta dopo la programmazione", lambda k: k.guasti.__setitem__("GET /broadcasts/*", [None, (503, {}), (503, {})]), False, "tolto"),
                ("rilettura della bozza muta", lambda k: k.guasti.__setitem__("GET /broadcasts/*", (503, {})), False, "non si programma"),
                ("elenco degli invii illeggibile", lambda k: k.guasti.__setitem__("GET /broadcasts", ValueError(CASA)), False, "DA GUARDARE"),
                ("timeout, applicata giusta", lambda k: k.guasti.__setitem__("PUT /broadcasts*", ("dopo", 0, {})), True, "OK: prova programmata"),
                ("200 fuori forma, applicata giusta", lambda k: k.guasti.__setitem__("PUT /broadcasts*", ("dopo", 200, {"x": 1})), True, "OK: prova programmata")):
            k, g, bid = con_bozza()
            if g is None:
                continue
            prepara(k)
            rc, out = comando(k, "prova", IMPR)
            resta_bozza = nome in ("rilettura della bozza muta", "elenco degli invii illeggibile")
            if parte:
                if rc != 0 or k.posta() != SOLO_LUI or atteso not in out:
                    viva.append(f"prova, programmazione ({nome}): uscita {rc}, posta {k.posta()}")
            else:
                fermo_pulito(f"prova, programmazione ({nome})", k, rc, out, atteso, invii=1 if resta_bozza else 0)
        k, g, bid = con_bozza()
        if g is not None:                    # l'invio sbagliato che non si toglie torna in bozza; se non si può, URGENTE
            k.put_a_tutti, k.delete_rotto = True, True
            orig = k.esegui

            def ripiego_riesce(metodo, percorso, dati, _o=orig, _k=k):
                if metodo == "PUT" and dati.get("send_at") is None:
                    _k.put_a_tutti = False
                return _o(metodo, percorso, dati)
            k.esegui = ripiego_riesce
            rc, out = comando(k, "prova", IMPR)
            fermo_pulito("prova, invio sbagliato non tolto", k, rc, out, "riportato in bozza", invii=1)
        k, g, bid = con_bozza()
        if g is not None:
            k.put_a_tutti, k.delete_rotto = True, True
            orig = k.esegui
            k.esegui = lambda metodo, percorso, dati, _o=orig: (500, {}) if metodo == "PUT" and dati.get("send_at") is None else _o(metodo, percorso, dati)
            rc, out = comando(k, "prova", IMPR)
            if rc != 1 or "URGENTE" not in out or "FERMALO A MANO" not in out or "19:40" not in out:
                viva.append(f"prova, invio sbagliato né tolto né in bozza: manca l'URGENTE con l'ora ({out.strip()[-80:]})")
        # n. orari: le stesse fasce del giro (mai prima delle 8, nella fascia dell'edizione, o con l'invio dopo le 20:59);
        #    fuori orario nemmeno una chiamata a Kit
        for nome, quando_, parte in (("7:55", SERA.replace(hour=7, minute=55), False), ("8:21 (invio alle 8:31)", SERA.replace(hour=8, minute=21), False),
                                     ("9:00", SERA.replace(hour=9, minute=0), False), ("10:29", SERA.replace(hour=10, minute=29), False),
                                     ("20:50 (invio alle 21:00)", SERA.replace(hour=20, minute=50), False), ("23:00", SERA.replace(hour=23, minute=0), False),
                                     ("8:05", SERA.replace(hour=8, minute=5), True), ("10:30", SERA.replace(hour=10, minute=30), True),
                                     ("20:49 (invio alle 20:59)", SERA.replace(hour=20, minute=49), True)):
            k, g, bid = con_bozza()
            if g is None:
                continue
            n0 = len(k.chiamate)
            rc, out = comando(k, "prova", IMPR, adesso=quando_)
            if parte and (rc != 0 or k.posta() != SOLO_LUI):
                viva.append(f"prova alle {nome}: non parte ({out.strip()[-80:]})")
            if not parte and (rc != 1 or "fuori orario" not in out or len(k.chiamate) != n0 or k.posta() != NESSUNO):
                viva.append(f"prova alle {nome}: non si ferma per l'orario, o chiama Kit lo stesso")
        # o. tempo: la programmazione parte solo se resta il tempo per rimediare (altrimenti la bozza si toglie), e dopo
        #    la programmazione il gruppo si riconta solo se resta il tempo per ricontare e togliere (altrimenti si toglie)
        for nome, lenta, atteso, invii in (
                ("Kit sempre lento", lambda m, p: 50.0, "tempo del giro scaduto", 1),
                ("Kit lento al conto del gruppo", lambda m, p: 122.0 if m == "GET" and re.match(r"^/tags/\d+/subscribers", p) else 0.1, "tempo del passo insufficiente", 0),
                ("Kit lento alla programmazione", lambda m, p: 320.0 if m == "PUT" else 0.1, "non resta il tempo per ricontare", 0)):
            k, g, bid = con_bozza()
            if g is None:
                continue
            finto = {"t": 0.0}

            def kit_lento(metodo, percorso, dati=None, _k=k, _l=lenta):
                finto["t"] += _l(metodo, percorso)
                return _k(metodo, percorso, dati)
            rc, out = comando(k, "prova", IMPR, via=kit_lento, orologio=lambda: finto["t"], pausa=lambda sec: finto.__setitem__("t", finto["t"] + sec))
            fermo_pulito(f"prova, {nome}", k, rc, out, atteso, invii=invii)
        #    i conti del tempo: l'invio parte dopo la scadenza del passo (la pulizia finisce sempre prima della partenza);
        #    dopo programmazione e 2 riletture restano le 4 chiamate della pulizia; ricontare il gruppo ne chiede una in più
        T = BV.TEMPO_CHIAMATA
        if BV.ATTESA_MINUTI * 60 <= BV.PASSO or hasattr(BV, "ATTESA_PROVA") or not 7 * T <= BV.RISERVA <= BV.PASSO or BV.RISERVA_GRUPPO < 5 * T:
            viva.append("tempi: l'invio deve partire dopo la scadenza del passo, con il tempo per rileggere, ricontare e togliere")
        # q. il ritardo di Kit nella prova (1): l'elenco del gruppo arriva dopo un po', la bozza aspetta e dice che cosa
        #    ha letto ogni volta (quanti elementi ha restituito Kit e quanti sono tra gli attesi, nei due modi, e l'etichetta
        #    letta per id); se non arriva finché il passo lascia tempo nessuna bozza; nel registro ogni chiamata ha i nomi
        #    dei suoi parametri
        k = mondo()
        k.ritardo = 12
        rc, out = comando(k, "bozza", IMPR)
        if rc != 0 or len(k.invii) != 1 or "con status=all 0 elementi di cui 0 tra gli attesi, con lo stato predefinito 0 di cui 0 tra gli attesi (x3); poi con status=all 1 elemento di cui 1 tra gli attesi, con lo stato predefinito 1 di cui 1 tra gli attesi" not in out \
                or "letta per id dalla parte dell'iscritto di prova, l'etichetta del gruppo c'è" not in out:
            viva.append(f"bozza con l'elenco del gruppo in ritardo: uscita {rc}, {len(k.invii)} bozze ({out.strip()[-120:]})")
        for frase in ("POST /tags 201", "POST /tags/101/subscribers/* 201", "GET /subscribers/*/tags?per_page=500 200", "GET /tags/101/subscribers?status=all&per_page=500 200 x5",
                      "GET /tags/101/subscribers?per_page=500 200 x5", "GET /subscribers?status=active&per_page=500 200", "POST /broadcasts 201", "con il codice HTTP di ognuna"):
            if frase not in out:
                viva.append(f"riepilogo della bozza: nel registro delle chiamate manca '{frase}'")
        k = mondo()
        k.ritardo = 10 ** 6
        rc, out = comando(k, "bozza", IMPR)
        fermo_pulito("bozza con l'elenco del gruppo che non arriva", k, rc, out, "gli elenchi arrivano in ritardo")
        attesa = re.search(r"dopo (\d+) riletture in (\d+) secondi", out)
        if k.invii_scritti() or not attesa or not 180 <= int(attesa.group(2)) <= BV.LAVORO or "letta per id dalla parte di un iscritto atteso, l'etichetta c'è" not in out:
            viva.append(f"bozza con l'elenco del gruppo che non arriva: bozza creata lo stesso, o non ha aspettato finché il passo lasciava tempo ({attesa.group(0) if attesa else '?'})")
        for nome, prepara, frasi in (
                ("status=all sempre vuoto", lambda k: setattr(k, "tutti_vuoto", True), ("con status=all 0 elementi di cui 0 tra gli attesi, con lo stato predefinito 1 di cui 1 tra gli attesi",)),
                ("etichetta non visibile per id", lambda k: setattr(k, "per_id", False), ("l'etichetta del gruppo non c'è",)),
                ("lettura per id muta", lambda k: k.guasti.__setitem__("GET /subscribers/*", (503, {})), ("l'etichetta del gruppo non si legge",))):
            k = mondo()
            prepara(k)
            rc, out = comando(k, "bozza", IMPR)
            if rc != 0 or len(k.invii) != 1 or any(f not in out for f in frasi):
                viva.append(f"bozza, {nome}: uscita {rc}, {len(k.invii)} bozze, o il riepilogo non lo dice")
        k, g, bid = con_bozza()
        if g is not None:                    # alla prova l'elenco torna vuoto: si aspetta finché c'è tempo, poi niente programmazione
            k.ritardo = 10 ** 6
            k.dato[(g, 1)] = BV.orologio()
            rc, out = comando(k, "prova", IMPR)
            fermo_pulito("prova con l'elenco del gruppo vuoto", k, rc, out, "non si programma", invii=1)
            if any(c[0] == "PUT" for c in k.chiamate):
                viva.append("prova con l'elenco del gruppo vuoto: programmata lo stesso")
        #    il registro non scrive mai il valore di un parametro che non sia uno stato, una data o un formato
        for percorso, atteso in (("/subscribers?status=active&email_address=casa%40prova.it&per_page=10", "/subscribers?status=active&email_address&per_page=10"),
                                 ("/tags/7/subscribers/123?x=1", "/tags/7/subscribers/*?x"), ("/broadcasts?per_page=1000&slim=true&after=WzZd", "/broadcasts?per_page=1000&slim=true&after"),
                                 ("/tags/7/subscribers?status=casa@prova.it&created_after=2026-11-28", "/tags/7/subscribers?status&created_after=2026-11-28")):
            if BV.via_di(percorso) != atteso:
                viva.append(f"registro delle chiamate: {percorso.split('?')[0]} scritto come {BV.via_di(percorso)}")
        # r. D2: l'elenco degli invii si chiede solo nella forma leggera (senza il contenuto delle email)
        if not ELENCHI or any("slim=true" not in e for e in ELENCHI):
            viva.append(f"elenco degli invii chiesto senza slim=true ({len([e for e in ELENCHI if 'slim=true' not in e])} volte su {len(ELENCHI)})")
        # s. D4: con due bozze di prova si programma solo l'ultima, e le altre si dicono; una seconda prova non
        #    programma la vecchia
        k = mondo()
        comando(k, "bozza", IMPR, adesso=SERA - timedelta(minutes=5))
        comando(k, "bozza", IMPR)
        ids = sorted(k.invii)
        rc, out = comando(k, "prova", IMPR)
        if len(ids) != 2 or rc != 0 or k.posta() != SOLO_LUI or k.invii[ids[0]]["send_at"] or not k.invii[ids[1]]["send_at"] \
                or f"altre bozze di prova più vecchie, non toccate: {ids[0]}" not in out:
            viva.append(f"due bozze di prova: uscita {rc}, posta {k.posta()} (attesa: programmata solo l'ultima, l'altra detta)")
        rc, out = comando(k, "prova", IMPR)
        if rc != 1 or k.posta() != SOLO_LUI or k.invii[ids[0]]["send_at"] or "già programmato o spedito" not in out or str(ids[0]) not in out:
            viva.append(f"seconda prova con una bozza vecchia in Kit: uscita {rc}, posta {k.posta()} (la vecchia non si programma mai)")
        # t. D5: il limite netto del passo arriva con una chiamata appesa (come l'allarme): lo script dice com'è finita.
        #    Con un invio programmato e non verificato: URGENTE, con l'ora
        for nome, quando_, urgente in (("alla lettura degli iscritti", lambda m, p: m == "GET" and p.startswith("/subscribers"), False),
                                       ("alla rilettura dopo la programmazione", lambda m, p: "PUT" in fatte and m == "GET" and re.match(r"^/broadcasts/\d+$", p), True),
                                       ("al conto del gruppo dopo la programmazione", lambda m, p: "PUT" in fatte and m == "GET" and p.startswith("/tags/"), True),
                                       ("mentre toglie un invio sbagliato", lambda m, p: m == "DELETE", True)):
            k, g, bid = con_bozza()
            if g is None:
                continue
            fatte = set()
            if nome == "mentre toglie un invio sbagliato":
                k.put_a_tutti = True

            def appesa(metodo, percorso, dati=None, _k=k, _q=quando_):
                if _q(metodo, percorso):
                    raise BV.Scaduto()
                r = _k(metodo, percorso, dati)
                fatte.add(metodo)
                return r
            rc, out = comando(k, "prova", IMPR, via=appesa)
            if rc != 1 or "tempo del passo scaduto" not in out or ("URGENTE" in out) != urgente or (urgente and "FERMALO A MANO in Kit prima delle 19:40" not in out) \
                    or "con il codice HTTP di ognuna" not in out:
                viva.append(f"limite netto del passo {nome}: uscita {rc} ({out.strip()[-160:]})")
        #    e nel giro della sera
        k = KitFinto([dict(iscritto(1, 2), email_address=CASA)])
        fatte = set()

        def appesa_sera(metodo, percorso, dati=None, _k=k):
            if "PUT" in fatte and metodo == "GET":
                raise BV.Scaduto()
            r = _k(metodo, percorso, dati)
            fatte.add(metodo)
            return r
        rc, out = comando(k, "invia", via=appesa_sera)
        if rc != 1 or "URGENTE: tempo del passo scaduto" not in out or "prima delle 19:40" not in out:
            viva.append(f"limite netto del passo nel giro della sera: uscita {rc} ({out.strip()[-120:]})")
        #    il giro rimandato per il ritardo di Kit esce con 0 e lo dice
        k = KitFinto([dict(iscritto(1, 2), email_address=CASA)])
        k.ritardo = 10 ** 6
        rc, out = comando(k, "invia")
        if rc != 0 or "rimandato al prossimo giro, nessuno è stato segnato" not in out or k.invii:
            viva.append(f"giro rimandato dalla riga di comando: uscita {rc} ({out.strip()[-120:]})")
        # u. la pulizia (3): toglie le bozze di prova non programmate e le etichette di prova; mai un invio programmato o
        #    spedito, mai un'etichetta o un invio che non sia di prova; finché un invio di prova non è spedito la sua
        #    etichetta resta; nessun iscritto viene tolto
        def mondo_sporco():
            k = mondo()
            cose = {}
            for chiave, nome, chi in (("bozza", "gommberg-benvenuto-prova-2026-12-01-1000", {1}), ("programmato", "gommberg-benvenuto-prova-2026-12-01-1100", {1}),
                                      ("spedito", "gommberg-benvenuto-prova-2026-12-01-1200", {1}), ("orfana", "gommberg-benvenuto-prova-2026-11-28-0956", {1}),
                                      ("permanente", "gommberg-benvenuto", {2}), ("sera", "gommberg-benvenuto-2026-12-01-1930", {2}),
                                      ("quasi", "gommberg-benvenuto-prova-x", {1}), ("quasi2", "gommberg-benvenuto-prova-2026-12-01-1000-bis", {1}),
                                      ("dem", "gommberg-dem-2026-12-02", {1, 2})):
                i = k.nuovo_id()
                k.tag[i], k.membri[i] = nome, set(chi)
                cose[chiave] = i
            for chiave, quando_, stato in (("bozza", None, None), ("programmato", "2026-12-02T18:45:00Z", "scheduled"), ("spedito", "2026-12-01T11:10:00Z", "completed"),
                                           ("sera", "2026-12-01T18:40:00Z", "completed"), ("dem", None, None), ("quasi", None, None)):
                i = k.nuovo_id()
                k.invii[i] = {"id": i, "subject": "x", "description": k.tag[cose[chiave]], "send_at": quando_, "status": stato,
                              "email_template": {"id": 5, "name": "Gommberg cornice"},
                              "vero": [{"all": [{"type": "tag", "ids": [cose[chiave]]}], "any": None, "none": None}]}
                cose["invio " + chiave] = i
            return k, cose
        k, cose = mondo_sporco()
        iscritti_prima = dict(k.iscritti)
        rc, out = comando(k, "pulizia")
        tolte = {c for c in ("bozza", "programmato", "spedito", "orfana", "permanente", "sera", "quasi", "quasi2", "dem") if cose[c] not in k.tag}
        invii_tolti = {c for c in ("bozza", "programmato", "spedito", "sera", "dem", "quasi") if cose["invio " + c] not in k.invii}
        if rc != 0 or tolte != {"bozza", "spedito", "orfana"} or invii_tolti != {"bozza"} or k.iscritti != iscritti_prima \
                or [c for c in k.scritture() if c[0] != "DELETE"]:
            viva.append(f"pulizia: uscita {rc}, etichette tolte {sorted(tolte)}, invii tolti {sorted(invii_tolti)} (attese: bozza, spedito, orfana; bozza)")
        for frase in (f"bozza {cose['invio bozza']} (gommberg-benvenuto-prova-2026-12-01-1000): tolta", "programmato e non ancora spedito (stato scheduled)",
                      "etichetta gommberg-benvenuto-prova-2026-12-01-1100: resta", "etichetta gommberg-benvenuto-prova-2026-11-28-0956: tolta",
                      "spedito, resta nello storico", "resta iscritto", "OK: pulizia fatta, 4 tra bozze ed etichette",
                      "etichetta gommberg-benvenuto-prova-2026-11-28-0956, prima di toccarla: Kit le attribuisce 1 iscritti con status=all, 1 con lo stato predefinito, totale dichiarato 1"):
            if frase not in out:
                viva.append(f"riepilogo della pulizia senza '{frase}'")
        rc, out = comando(k, "pulizia")              # rilanciata: non c'è più nulla da togliere, e l'invio programmato è ancora lì
        if rc != 0 or cose["programmato"] not in k.tag or cose["invio programmato"] not in k.invii or "OK: pulizia fatta, 0 " not in out:
            viva.append(f"pulizia rilanciata: uscita {rc}, o ha toccato l'invio programmato")
        if cose["invio programmato"] in k.invii:
            k.invii[cose["invio programmato"]]["status"] = "completed"      # la mail di prova è partita: ora la sua etichetta si toglie
            rc, out = comando(k, "pulizia")
            if rc != 0 or cose["programmato"] in k.tag or cose["invio programmato"] not in k.invii:
                viva.append("pulizia dopo la partenza della mail di prova: l'etichetta non si toglie, o l'invio spedito è stato toccato")
        #    Kit che risponde male: l'elenco degli invii non letto = nessuna scrittura; una bozza che non si toglie tiene la
        #    sua etichetta; un'etichetta che Kit non toglie: lo dice ed esce con 1; un invio senza stato non si tocca
        for nome, prepara, verifica in (
                ("elenco degli invii non letto", lambda k, c: k.guasti.__setitem__("GET /broadcasts", (503, {})), lambda k, c: not k.scritture()),
                ("elenco delle etichette non letto", lambda k, c: k.guasti.__setitem__("GET /tags", (503, {})), lambda k, c: len(k.tag) == len(c) - 6),
                ("bozza che non si toglie", lambda k, c: setattr(k, "delete_rotto", True), lambda k, c: c["bozza"] in k.tag and c["invio bozza"] in k.invii),
                ("rilettura muta", lambda k, c: k.guasti.__setitem__("GET /broadcasts/*", (503, {})), lambda k, c: c["bozza"] in k.tag and c["spedito"] in k.tag and c["invio bozza"] in k.invii),
                ("etichetta che Kit non toglie", lambda k, c: k.guasti.__setitem__("DELETE /tags/*", (500, {"errore": CASA})), lambda k, c: c["orfana"] in k.tag and c["invio bozza"] not in k.invii),
                ("invio programmato senza stato", lambda k, c: k.invii[c["invio spedito"]].__setitem__("status", "boh"), lambda k, c: c["spedito"] in k.tag)):
            k, cose = mondo_sporco()
            prepara(k, cose)
            rc, out = comando(k, "pulizia")
            intatti = all(cose[c] in k.tag for c in ("programmato", "permanente", "sera", "quasi", "quasi2", "dem")) \
                and all(cose["invio " + c] in k.invii for c in ("programmato", "spedito", "sera", "dem", "quasi"))
            if (rc != 1 and nome != "invio programmato senza stato") or not intatti or not verifica(k, cose):
                viva.append(f"pulizia, {nome}: uscita {rc}, intatti {intatti} ({out.strip()[-120:]})")
        # p. nessun indirizzo in ciò che lo script ha stampato in tutti i casi qui sopra (e nei giri di prima)
        for u in uscite:
            if "@" in u or "prova.it" in u.lower() or "Traceback" in u:
                viva.append(f"un indirizzo o un tracciato in ciò che lo script stampa: ...{u[max(0, u.find('@') - 60):u.find('@') + 20].strip()[:100]}")
                break
    finally:
        BV.ferma_scadenza()
        BV.nl.kit, BV.ATTESA_LETTURE, BV.orologio, BV.pausa = vero, vera_attesa, orologio_vero, pausa_vera

    # il passo nel giro della sera, l'urgenza con la sua segnalazione, il postino delle mail straordinarie che non tocca i benvenuti
    flusso = open(os.path.join(REPO, ".github", "workflows", "dem.yml"), encoding="utf-8").read()
    if "redazione/benvenuto.py" not in flusso or "github.event_name != 'push'" not in flusso:
        male.append("dem.yml: manca il passo Benvenuto (solo nel giro della sera)")
    if "grep -q URGENTE benvenuto.txt" not in flusso:
        male.append("dem.yml: l'URGENTE del benvenuto non apre una segnalazione sua")
    import dem as DM
    if "gommberg-benvenuto-x".startswith(DM.ETICHETTA):
        male.append("dem.py toccherebbe gli invii del benvenuto")
    # punto 9: l'invito all'iscrizione dice come iscriviti.html
    import pagine as PG
    if "La prima pagina" in PG.invito() or "La prima pagina" in open(os.path.join(REPO, "iscriviti.html"), encoding="utf-8").read():
        male.append("l'invito all'iscrizione descrive ancora l'email di prima ('La prima pagina')")
    # l'ora di uscita in un posto solo: nelle pagine fisse ogni "alle H:MM" è segnato (pagine.py lo riscrive da giorni.ORA_USCITA)
    for f in sorted(os.listdir(REPO)):
        if f.endswith(".html"):
            t = open(os.path.join(REPO, f), encoding="utf-8").read()
            t = re.sub(r"<span data-ora-uscita>[^<]*</span>|<meta\b[^>]*\bdata-ora-uscita\b[^>]*>", "", t)
            if re.search(r"\balle \d{1,2}:\d{2}\b", t):
                male.append(f"{f}: un'ora di uscita scritta a mano (segnala con <span data-ora-uscita>)")
    if re.search(r"\d{1,2}:\d{2}", open(os.path.join(R, "benvenuto_mail.html"), encoding="utf-8").read()):
        male.append("benvenuto_mail.html: un orario scritto a mano (si usa [[ORA_USCITA]])")
    esito("Benvenuto: giro con Kit finto, mai due mail, mai a tutti", not male, "; ".join(male)[:700] or
          "giro normale con accensione e finestra di 7 giorni, giri successivi, zero nuovi, già etichettato, 5xx, rete muta, "
          "risposte illeggibili e fuori forma, filtro per data ignorato, troppi, bozza a tutti (anche con risposta che mente) "
          "tolta, creazione incerta cercata e tolta, programmazione sbagliata/incerta riletta e tolta, ripiego in bozza e "
          "URGENTE, giro interrotto in sette punti (nessuno segnato prima delle etichette permanenti), orari e avviso per chi "
          "aspetta da più di 3 giorni, solo gli iscritti che stanno nel tempo (gli altri al giro dopo), Kit che rallenta a metà, "
          "elenco del gruppo in ritardo (aspetta, poi rimanda senza segnare nessuno), iscritto estraneo, due giri vicini, piano")

    # la prova dal vivo lanciata a mano da un ramo (dem.yml, modi "prova-"): i passi del flusso eseguiti qui con un
    # python3 finto che registra come viene chiamato. Solo benvenuto.py piano, bozza o prova; l'impronta arriva da una
    # variabile d'ambiente e non può diventare un comando; gli altri passi restano com'erano
    def passo_del_flusso(nome):
        """(testa, comandi) del passo con quel nome: le righe prima di "run:" e lo script di "run: |"."""
        m = re.search(r"^      - name: " + re.escape(nome) + r"\n((?:        .*\n|\n)*)", flusso, re.M)
        corpo = m.group(1) if m else ""
        r = re.search(r"^        run: \|\n((?:          .*\n|\n)*)", corpo, re.M)
        return (corpo[:r.start()] if r else corpo), "".join(x[10:] if x.strip() else "\n" for x in (r.group(1) if r else "").splitlines(True))

    lav = os.path.join(TMP, "flusso_dem")
    os.makedirs(os.path.join(lav, "bin"), exist_ok=True)
    finto = os.path.join(lav, "bin", "python3")
    with open(finto, "w", encoding="utf-8") as f:
        f.write('#!/bin/sh\nprintf \'%s\\n\' "$#" "$@" >> "$REGISTRO"\necho "uscita del python finto"\nexit "${FINTO_RC:-0}"\n')
    os.chmod(finto, 0o755)

    def lancia(nome, finto_python=True, **amb):
        """Esegue lo script del passo come fa GitHub (bash -e): (uscita, ciò che stampa, come è stato chiamato python3)."""
        d = tempfile.mkdtemp(dir=lav)
        reg, script = os.path.join(d, "registro.txt"), os.path.join(d, "passo.sh")
        open(script, "w", encoding="utf-8").write(passo_del_flusso(nome)[1])
        e = {"PATH": (os.path.join(lav, "bin") + os.pathsep if finto_python else "") + os.environ["PATH"], "REGISTRO": reg,
             "GITHUB_STEP_SUMMARY": os.path.join(d, "riepilogo.md"), "GITHUB_REF": "refs/heads/g43", "GITHUB_EVENT_NAME": "workflow_dispatch"}
        e.update(amb)
        q = subprocess.run(["bash", "-e", script], cwd=d, env=e, capture_output=True, text=True, timeout=60)
        chiamate = open(reg, encoding="utf-8").read().split("\n")[:-1] if os.path.exists(reg) else []
        return q.returncode, q.stdout + q.stderr, chiamate, d

    testa_prova, comandi_prova = passo_del_flusso("Prova del benvenuto")
    if not comandi_prova:
        viva.append("dem.yml: manca il passo 'Prova del benvenuto'")
    else:
        IMP = "3b0d0604b4c1c885"
        for scelto, atteso in (("prova-piano", ["2", "redazione/benvenuto.py", "piano"]),
                               ("prova-bozza", ["3", "redazione/benvenuto.py", "bozza", "impronta:" + IMP]),
                               ("prova-invio", ["3", "redazione/benvenuto.py", "prova", "impronta:" + IMP]),
                               ("prova-pulizia", ["2", "redazione/benvenuto.py", "pulizia"])):
            for ramo in ("refs/heads/g43", "refs/heads/main"):
                rc, out, chiamate, d = lancia("Prova del benvenuto", SCELTO=scelto, IMPRONTA=IMP, GITHUB_REF=ramo)
                if rc != 0 or chiamate != atteso or "uscita del python finto" not in open(os.path.join(d, "riepilogo.md"), encoding="utf-8").read():
                    viva.append(f"dem.yml, {scelto} da {ramo}: python3 chiamato con {chiamate[1:]} (uscita {rc}), o riepilogo vuoto")
        #  senza impronta nell'ambiente (il passo prima non l'ha passata): lo script la riceve vuota e la rifiuta lui
        rc, out, chiamate, d = lancia("Prova del benvenuto", SCELTO="prova-bozza")
        if chiamate != ["3", "redazione/benvenuto.py", "bozza", "impronta:"]:
            viva.append(f"dem.yml, prova-bozza senza impronta: python3 chiamato con {chiamate[1:]}")
        #  l'uscita dello script è quella del passo; ogni altro modo e ogni altro evento non chiamano nulla
        if lancia("Prova del benvenuto", SCELTO="prova-invio", IMPRONTA=IMP, FINTO_RC="1")[0] != 1:
            viva.append("dem.yml: lo script esce con 1 e il passo di prova resta verde")
        for scelto in ("sincronizza", "piano", "controlla", "invia", "prova", "prova-", "prova-tutti", "bozza", "pulizia", ""):
            rc, out, chiamate, d = lancia("Prova del benvenuto", SCELTO=scelto, IMPRONTA=IMP)
            if rc == 0 or chiamate:
                viva.append(f"dem.yml: il passo di prova con modo '{scelto}' chiama python3 o resta verde")
        for evento in ("push", "schedule", "pull_request", ""):
            rc, out, chiamate, d = lancia("Prova del benvenuto", SCELTO="prova-invio", IMPRONTA=IMP, GITHUB_EVENT_NAME=evento)
            if rc == 0 or chiamate:
                viva.append(f"dem.yml: il passo di prova lavora anche con l'evento '{evento}'")
        #  l'impronta non può diventare un comando né un argomento in più, qualunque cosa contenga
        for cattiva in ('x"; touch INIETTATO; echo "', "$(touch INIETTATO)", "`touch INIETTATO`", "a b; touch INIETTATO", "x' -c 'import os", "--help", "x\ninvia"):
            rc, out, chiamate, d = lancia("Prova del benvenuto", SCELTO="prova-invio", IMPRONTA=cattiva)
            if os.path.exists(os.path.join(d, "INIETTATO")) or chiamate[:3] != ["3", "redazione/benvenuto.py", "prova"] \
                    or "\n".join(chiamate[3:]) != "impronta:" + cattiva:
                viva.append(f"dem.yml: l'impronta '{cattiva[:20]}' cambia il comando ({chiamate[:5]})")
        if "${{" in comandi_prova or re.search(r"dem\.py|invia|sincronizza", comandi_prova) \
                or len(re.findall(r"^\s*python3 ", comandi_prova, re.M)) != 1 or "tee -a \"$GITHUB_STEP_SUMMARY\"" not in comandi_prova:
            viva.append("dem.yml: nel passo di prova un valore scritto dentro il comando, un altro script, o nessun riepilogo")
        if "if: env.PROVA_BENVENUTO == 'true'" not in testa_prova or "KIT_API_KEY: ${{ secrets.KIT_API_KEY }}" not in testa_prova:
            viva.append("dem.yml: il passo di prova non è legato a PROVA_BENVENUTO, o non riceve la chiave dall'ambiente")
    #  D3: l'input dell'impronta non sta in nessun "env:" né in nessun comando (il registro stampa in chiaro ciò che sta
    #  in "env:"): lo legge solo il passo che la controlla, dal file dell'evento
    if "inputs.impronta" in flusso or len(re.findall(r'get\("impronta"\)', flusso)) != 1:
        viva.append("dem.yml: l'input dell'impronta è scritto in un 'env:' o in un comando (il registro lo stamperebbe in chiaro)")
    #  D1 e D5: i tempi. Lo script si arrende prima che GitHub chiuda il passo, e il job non chiude i passi
    minuti = {n: int(m.group(1)) if (m := re.search(r"^        timeout-minutes: (\d+)", passo_del_flusso(n)[0], re.M)) else None
              for n in ("Mail straordinarie", "Benvenuto", "Prova del benvenuto")}
    job = re.search(r"^    timeout-minutes: (\d+)", flusso, re.M)
    if None in minuti.values() or not job or minuti["Benvenuto"] != minuti["Prova del benvenuto"] or minuti["Benvenuto"] * 60 < BV.ALLARME + 10 \
            or int(job.group(1)) <= minuti["Mail straordinarie"] + minuti["Benvenuto"]:
        viva.append(f"dem.yml: i minuti dei passi ({minuti}) non contengono i {BV.ALLARME} secondi che lo script si dà, o il job li chiude prima")
    #  PROVA_BENVENUTO: solo lanciando a mano; allora gli altri due lavori non partono, e l'urgenza si segnala anche da un ramo
    if "PROVA_BENVENUTO: ${{ github.event_name == 'workflow_dispatch' && startsWith(github.event.inputs.modo, 'prova-') }}" not in flusso:
        viva.append("dem.yml: PROVA_BENVENUTO non è 'lanciato a mano con un modo prova-'")
    for nome in ("Mail straordinarie", "Benvenuto"):
        if not re.search(r"^        if: .*env\.PROVA_BENVENUTO != 'true'", passo_del_flusso(nome)[0], re.M):
            viva.append(f"dem.yml: il passo '{nome}' parte anche durante la prova del benvenuto")
    if not re.search(r"^        if: failure\(\) && \(github\.ref == 'refs/heads/main' \|\| env\.PROVA_BENVENUTO == 'true'\)", passo_del_flusso("Urgenza benvenuto")[0], re.M):
        viva.append("dem.yml: l'URGENTE di una prova lanciata da un ramo non apre la segnalazione")
    #  l'urgenza: la segnalazione nasce solo se lo script ha scritto URGENTE (gh finto, che registra come viene chiamato)
    gh_finto = os.path.join(lav, "bin", "gh")
    with open(gh_finto, "w", encoding="utf-8") as f:
        f.write('#!/bin/sh\nprintf \'%s\\n\' "$@" >> "$REGISTRO_GH"\n')
    os.chmod(gh_finto, 0o755)
    for testo, apre in (("DA GUARDARE: benvenuto - l'etichetta x in Kit ha 0 iscritti invece di 1: nessun invio\n", False), (None, False),
                        ("DA GUARDARE: benvenuto - URGENTE: invio 7 né tolto né riportato in bozza: FERMALO A MANO in Kit prima delle 19:40\n", True)):
        d = tempfile.mkdtemp(dir=lav)
        if testo is not None:
            open(os.path.join(d, "benvenuto.txt"), "w", encoding="utf-8").write(testo)
        reg = os.path.join(d, "gh.txt")
        script = os.path.join(d, "passo.sh")
        open(script, "w", encoding="utf-8").write(passo_del_flusso("Urgenza benvenuto")[1].replace("${{ github.repository_owner }}", "qualcuno"))
        q = subprocess.run(["bash", "-e", script], cwd=d, env={"PATH": os.path.join(lav, "bin") + os.pathsep + os.environ["PATH"], "REGISTRO_GH": reg},
                           capture_output=True, text=True, timeout=60)
        if q.returncode != 0 or os.path.exists(reg) != apre or (apre and "URGENTE" not in open(os.path.join(d, "urgente.txt"), encoding="utf-8").read()):
            viva.append(f"dem.yml, urgenza del benvenuto: con {'URGENTE' if apre else 'nessun URGENTE'} la segnalazione {'non nasce' if apre else 'nasce lo stesso'}")
    scelte = re.search(r"^        options: \[(.*)\]", flusso, re.M)
    if not scelte or [x.strip() for x in scelte.group(1).split(",")] != ["piano", "sincronizza", "controlla", "prova-piano", "prova-bozza", "prova-invio", "prova-pulizia"] \
            or not re.search(r"^      impronta:\n(?:        .*\n)*?        type: string", flusso, re.M):
        viva.append("dem.yml: i modi di workflow_dispatch non sono piano, sincronizza, controlla e i quattro prova-, o manca l'input impronta")
    #  gli altri passi restano com'erano: da un ramo solo il controllo, e un modo di prova non diventa mai un invio
    for nome, script, casi in (("Benvenuto", "redazione/benvenuto.py", (("sincronizza", "refs/heads/main", "invia"), ("piano", "refs/heads/main", "piano"),
                                                                         ("controlla", "refs/heads/main", "controlla"), ("sincronizza", "refs/heads/g43", "controlla"),
                                                                         ("piano", "refs/heads/g43", "controlla"), ("prova-invio", "refs/heads/main", "controlla"),
                                                                         ("prova-pulizia", "refs/heads/main", "controlla"), ("prova-bozza", "refs/heads/g43", "controlla"))),
                               ("Mail straordinarie", "redazione/dem.py", (("sincronizza", "refs/heads/main", "sincronizza"), ("piano", "refs/heads/main", "piano"),
                                                                           ("sincronizza", "refs/heads/g43", "controlla"), ("piano", "refs/heads/g43", "controlla"),
                                                                           ("prova-invio", "refs/heads/g43", "controlla")))):
        for scelto, ramo, atteso in casi:
            rc, out, chiamate, d = lancia(nome, SCELTO=scelto, GITHUB_REF=ramo)
            if chiamate != ["2", script, atteso]:
                viva.append(f"dem.yml, passo '{nome}' con {scelto} da {ramo}: python3 chiamato con {chiamate[1:]}, atteso {atteso}")
    #  l'impronta fuori dal registro (D3): passa al passo di prova solo se è di 16 esadecimali, e già mascherata; ogni
    #  altro valore (corto, su più righe, un indirizzo) ferma il giro senza comparire in nessuna uscita
    ordine = re.findall(r"^      - name: (.*)$", flusso, re.M)
    if "Impronta fuori dal registro" not in ordine or ordine.index("Impronta fuori dal registro") > ordine.index("Prova del benvenuto") \
            or "${{" in passo_del_flusso("Impronta fuori dal registro")[1] or "env:" in passo_del_flusso("Impronta fuori dal registro")[0]:
        viva.append("dem.yml: l'impronta non è controllata e mascherata prima del passo di prova, o il passo che lo fa la riceve in chiaro")
    else:
        IMP = "3b0d0604b4c1c885"
        for nome, evento, passa in (("un'impronta", {"inputs": {"modo": "prova-bozza", "impronta": IMP}}, IMP),
                                    ("un'impronta in maiuscolo con spazi", {"inputs": {"modo": "prova-invio", "impronta": f"  {IMP.upper()} "}}, IMP),
                                    ("un indirizzo per errore", {"inputs": {"modo": "prova-bozza", "impronta": "casa@prova.it"}}, None),
                                    ("un valore corto", {"inputs": {"modo": "prova-bozza", "impronta": "3b0d06"}}, None),
                                    ("un valore su più righe", {"inputs": {"modo": "prova-invio", "impronta": IMP + "\nsegreto-su-due-righe"}}, None),
                                    ("17 caratteri", {"inputs": {"modo": "prova-invio", "impronta": IMP + "a"}}, None),
                                    ("un valore sbagliato con prova-piano", {"inputs": {"modo": "prova-piano", "impronta": "casa@prova.it"}}, None),
                                    ("nessuna impronta con prova-bozza", {"inputs": {"modo": "prova-bozza", "impronta": ""}}, None),
                                    ("nessuna impronta con prova-piano", {"inputs": {"modo": "prova-piano", "impronta": ""}}, ""),
                                    ("nessuna impronta con prova-pulizia", {"inputs": {"modo": "prova-pulizia"}}, ""),
                                    ("file dell'evento illeggibile", None, "")):
            d = tempfile.mkdtemp(dir=lav)
            ev, amb = os.path.join(d, "evento.json"), os.path.join(d, "ambiente.txt")
            open(ev, "w", encoding="utf-8").write(json.dumps(evento) if evento is not None else "{rotto")
            open(amb, "w", encoding="utf-8").close()
            rc, out, _, d2 = lancia("Impronta fuori dal registro", finto_python=False, GITHUB_EVENT_PATH=ev, GITHUB_ENV=amb)
            scritto = open(amb, encoding="utf-8").read()
            dato = str(((evento or {}).get("inputs") or {}).get("impronta") or "").strip()
            riepilogo = open(os.path.join(d2, "riepilogo.md"), encoding="utf-8").read() if os.path.exists(os.path.join(d2, "riepilogo.md")) else ""
            if passa:
                giusto = rc == 0 and scritto == f"IMPRONTA={passa}\n" and out.split() == [f"::add-mask::{passa}"]
            elif passa == "":
                giusto = rc == 0 and not scritto and not out.strip()
            else:
                giusto = rc == 1 and not scritto and "16 caratteri esadecimali" in out and "16 caratteri esadecimali" in riepilogo \
                    and not any(x and x in out + riepilogo for x in dato.split("\n"))
            if not giusto:
                viva.append(f"dem.yml, impronta fuori dal registro ({nome}): uscita {rc}, ambiente {'scritto' if scritto else 'vuoto'}")
    #  D5 dal vero, con un processo: ogni riga esce subito (se il passo viene chiuso, ciò che è stato fatto è scritto) e
    #  l'allarme ferma lo script con il suo messaggio anche con una chiamata a Kit appesa
    appeso = ("import sys, time\nsys.path.insert(0, sys.argv[1])\nimport benvenuto as B\nB.ALLARME = int(sys.argv[2])\n"
              "def kit(metodo, percorso, dati=None):\n"
              "    if percorso.startswith('/subscribers'):\n        time.sleep(60)\n"
              "    return 200, {'email_templates': [{'id': 5, 'name': 'Gommberg cornice'}]}\n"
              "B.nl.kit = kit\nsys.argv = ['benvenuto.py', 'bozza', 'impronta:3b0d0604b4c1c885']\nB.main()\n")
    senza_aiuti = {k: v for k, v in os.environ.items() if k != "PYTHONUNBUFFERED"}      # come su GitHub: l'uscita va in un tubo
    q = subprocess.Popen([sys.executable, "-c", appeso, R, "2"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=senza_aiuti)
    try:
        out, _ = q.communicate(timeout=30)
        if q.returncode != 1 or "tempo del passo scaduto" not in out or "Traceback" in out or "GET /email_templates 200" not in out:
            viva.append(f"allarme del passo con una chiamata appesa: uscita {q.returncode} ({out.strip()[-120:]})")
    except subprocess.TimeoutExpired:
        q.kill()
        viva.append("allarme del passo con una chiamata appesa: lo script non si è fermato da sé")
    q = subprocess.Popen([sys.executable, "-c", appeso, R, "50"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=senza_aiuti)
    try:
        import select
        pronto = select.select([q.stdout], [], [], 8)[0]
        prima = q.stdout.readline() if pronto else ""
        if "Prova del benvenuto, bozza" not in prima:
            viva.append("le righe dello script non escono subito: se il passo viene chiuso il riepilogo resta vuoto")
    finally:
        q.kill()
        q.wait()
    intestazione = BV.__doc__
    for frase in ("gh workflow run dem.yml --ref RAMO -f modo=prova-piano", "-f modo=prova-bozza -f impronta=", "-f modo=prova-invio -f impronta=",
                  "-f modo=prova-pulizia", "Che cosa resta in Kit dopo la prova", "benvenuto.py impronta", "eventual-consistency"):
        if frase not in intestazione:
            viva.append(f"benvenuto.py: l'intestazione non dice '{frase}'")
    if re.search(r"dal PC|INDIRIZZO\s+prova dal vivo|KIT_API_KEY nell'ambiente", intestazione):
        viva.append("benvenuto.py: l'intestazione parla ancora di una prova dal PC con l'indirizzo")
    esito("Benvenuto: prova dal vivo per impronta, da GitHub", not viva, "; ".join(viva)[:700] or
          "impronta (maiuscole e spazi), indirizzo in chiaro rifiutato, impronta di nessuno, di due, del non confermato; Kit che "
          "risponde male a elenco, creazione, rilettura e programmazione; gruppo di 2 prima e dopo bozza e programmazione; bozze non "
          "di prova; due bozze (solo l'ultima); elenco del gruppo in ritardo; orari; tempo per rimediare; limite netto del passo e "
          "URGENTE; pulizia (solo bozze ed etichette di prova, mai un invio programmato o spedito); elenco degli invii leggero; "
          "nessun indirizzo né tracciato in ciò che stampa o chiede a Kit; in dem.yml i quattro modi prova- chiamano solo "
          "benvenuto.py piano, bozza, prova, pulizia, solo a mano; l'impronta passa solo se di 16 esadecimali e non diventa un comando")


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
def problemi_piani(piani, tarature):
    """Pannello: piani.json e taratura.json devono dire la stessa cosa alla pagina, che non dà errori ma sbaglia piano o
    scarta punti in silenzio. Il file cambia solo a mano, dentro un rilascio: qui lo si ferma. Torna l'elenco dei guasti."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    guasti, vecchio, nomi = [], None, []
    if not isinstance(piani, list) or not piani:
        return ["piani.json non è un elenco di piani"]
    for i, x in enumerate(piani):
        nome = x.get("piano") if isinstance(x, dict) else None
        if not isinstance(nome, str) or not nome.strip():
            guasti.append(f"piani.json, voce {i + 1}: manca il nome del piano")
            continue
        if nomi and nomi[-1] == nome:                      # un piano che ritorna (Pro, Max 5x, Pro) è una riga nuova con il suo "dal"
            guasti.append(f"piani.json: il piano '{nome}' compare due volte di fila (una riga nuova serve solo se il piano cambia)")
        nomi.append(nome)
        dal = x.get("dal")
        if dal is None and i == 0:
            continue                                        # il primo piano vale dall'inizio
        # data e ora complete e il fuso (+01:00): "2026-11-24", "...T9:24", "...T18:00" senza fuso o con Z non passano
        if not isinstance(dal, str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d(?::\d\d)?[+-]\d\d:\d\d", dal):
            guasti.append(f"piani.json, '{nome}': 'dal' ({dal!r}) non è AAAA-MM-GGTHH:MM:SS+HH:MM")
            continue
        try:
            t = datetime.fromisoformat(dal)
        except ValueError:
            guasti.append(f"piani.json, '{nome}': 'dal' ({dal!r}) è una data illeggibile")
            continue
        if t.utcoffset() != t.replace(tzinfo=ZoneInfo("Europe/Rome")).utcoffset():
            guasti.append(f"piani.json, '{nome}': il fuso di 'dal' ({dal}) non è quello di Roma in quel giorno: la pagina legge le prime 16 cifre come ora di Roma")
        if vecchio is not None and t <= vecchio:
            guasti.append(f"piani.json, '{nome}': i piani non sono in ordine di data")
        vecchio = t
    # azzeramento settimanale: giorno e ora scritti bene e confermati (la scheda del pannello li dice a Paolo)
    for i, x in enumerate(piani):
        if not isinstance(x, dict) or not isinstance(x.get("piano"), str):
            continue
        nome, az = x["piano"], x.get("azzeramento")
        if not isinstance(az, dict) or az.get("giorno") not in ("lun", "mar", "mer", "gio", "ven", "sab", "dom") \
                or not isinstance(az.get("ora"), str) or not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", az["ora"]):
            guasti.append(f"piani.json, '{nome}': 'azzeramento' deve avere giorno (lun..dom) e ora (HH:MM)")
        elif az.get("da_confermare"):
            guasti.append(f"piani.json, '{nome}': l'azzeramento è ancora 'da_confermare': la scheda scriverebbe un orario non confermato")
        # stima dichiarata: un rapporto con la sua base e il suo motivo, mai un fattore senza spiegazione, mai a catena
        st = x.get("stima")
        if st is None:
            continue
        di = st.get("di") if isinstance(st, dict) else None
        r = st.get("rapporto") if isinstance(st, dict) else None
        if not isinstance(st, dict) or di not in nomi or di == nome:
            guasti.append(f"piani.json, '{nome}': la 'stima' deve dire su quale altro piano di piani.json si basa ('di')")
        else:
            # catena: la base che è a sua volta una stima è un guasto solo se non ha una misura vera (lettura non esclusa);
            # con una misura la pagina usa quella e il campo "stima" della base resta inerte
            misurato = any(isinstance(t, dict) and t.get("piano") == di and not t.get("escluso") and (t.get("punti") or 0) > 0
                           and (t.get("durata_min") or 0) > 0 for t in (tarature if isinstance(tarature, list) else []))
            if not misurato and any(isinstance(y, dict) and y.get("piano") == di and y.get("stima") is not None for y in piani):
                guasti.append(f"piani.json, '{nome}': la stima si basa su '{di}', che è a sua volta una stima senza misura vera (niente catene)")
        if isinstance(r, bool) or not isinstance(r, (int, float)) or not 0 < r <= 10:
            guasti.append(f"piani.json, '{nome}': il 'rapporto' della stima ({r!r}) non è un numero tra 0 e 10")
        if not isinstance(st, dict) or not isinstance(st.get("motivo"), str) or len(st["motivo"].strip()) < 10:
            guasti.append(f"piani.json, '{nome}': la stima non dice il motivo (perché è una stima, finché cosa vale)")
    for x in tarature if isinstance(tarature, list) else []:
        if isinstance(x, dict) and x.get("piano") not in nomi and not x.get("escluso"):
            guasti.append(f"taratura.json: lettura del {x.get('giorno')} sul piano '{x.get('piano')}', che piani.json non conosce "
                          f"(correggi l'etichetta, o dichiara \"escluso\" con il motivo)")
    return guasti


def passo_pannello():
    """I file veri e i casi sbagliati: ognuno dev'essere fermato."""
    male = []
    try:
        piani = json.load(open(os.path.join(REPO, "pannello", "piani.json"), encoding="utf-8"))
        tarature = json.load(open(os.path.join(REPO, "pannello", "taratura.json"), encoding="utf-8"))
        male += problemi_piani(piani, tarature)
    except (OSError, ValueError) as e:      # file mancante o JSON rotto
        male.append(f"pannello/piani.json o taratura.json: {e}"[:160])
    az = {"giorno": "ven", "ora": "18:00"}
    pro = {"piano": "Pro", "azzeramento": az}
    max5 = {"piano": "Max 5x", "dal": "2026-11-24T18:00:00+01:00", "azzeramento": az}
    stima = {"di": "Pro", "rapporto": 0.2, "motivo": "un quinto del Pro, finché non c'è una misura"}
    sbagliati = [("senza nome", [pro, {"dal": "2026-11-24T18:00:00+01:00"}], []),
                 ("ora senza zero", [pro, dict(max5, dal="2026-11-24T9:24:00+01:00")], []),
                 ("senza fuso", [pro, dict(max5, dal="2026-11-24T18:00")], []),
                 ("solo la data", [pro, dict(max5, dal="2026-11-24")], []),
                 ("data impossibile", [pro, dict(max5, dal="2026-13-45T18:00:00+01:00")], []),
                 ("fuso d'estate sbagliato", [pro, dict(max5, dal="2026-07-01T18:00:00+01:00")], []),
                 ("fuori ordine", [pro, max5, {"piano": "Max 20x", "dal": "2026-11-20T18:00:00+01:00"}], []),
                 ("il secondo senza 'dal'", [pro, {"piano": "Max 5x"}], []),
                 ("lettura di un piano ignoto", [pro, max5], [{"giorno": "2026-11-15", "piano": "Max", "punti": 1, "durata_min": 1}]),
                 ("non è un elenco", {"piano": "Pro"}, []),
                 ("senza azzeramento", [pro, {"piano": "Max 5x", "dal": max5["dal"]}], []),
                 ("azzeramento con giorno sbagliato", [pro, dict(max5, azzeramento={"giorno": "venerdi", "ora": "18:00"})], []),
                 ("azzeramento con ora sbagliata", [pro, dict(max5, azzeramento={"giorno": "ven", "ora": "6pm"})], []),
                 ("azzeramento ancora da confermare", [pro, dict(max5, azzeramento=dict(az, da_confermare=True))], []),
                 ("stima senza motivo", [pro, dict(max5, stima={"di": "Pro", "rapporto": 0.2})], []),
                 ("stima su un piano che non c'è", [pro, dict(max5, stima=dict(stima, di="Max 20x"))], []),
                 ("stima su se stessa", [pro, dict(max5, stima=dict(stima, di="Max 5x"))], []),
                 ("stima con rapporto zero", [pro, dict(max5, stima=dict(stima, rapporto=0))], []),
                 ("stima con rapporto scritto a parole", [pro, dict(max5, stima=dict(stima, rapporto="un quinto"))], []),
                 ("stima a catena", [dict(pro, stima=dict(stima, di="Max 5x")), dict(max5, stima=stima)], []),
                 ("lo stesso piano due volte di fila", [pro, dict(pro, dal="2026-11-20T18:00:00+01:00")], []),
                 ("piano che ritorna senza 'dal'", [pro, max5, dict(pro)], []),
                 ("piano che ritorna fuori ordine", [pro, max5, dict(pro, dal="2026-11-20T18:00:00+01:00")], [])]
    for nome, p, t in sbagliati:
        if not problemi_piani(p, t):
            male.append(f"piani.json: il caso '{nome}' non è fermato")
    ritorno = [pro, dict(max5, stima=stima), dict(pro, dal="2027-01-12T18:00:00+01:00")]
    if problemi_piani(ritorno, []):
        male.append("piani.json: un piano che ritorna (Pro, Max 5x, Pro) con 'dal' in ordine non deve fermare il rilascio")
    lettura = {"giorno": "2026-12-01", "piano": "Max 5x", "punti": 1, "durata_min": 10}
    if problemi_piani([pro, dict(max5, stima=stima), {"piano": "Max 20x", "dal": "2026-12-01T18:00:00+01:00", "azzeramento": az, "stima": dict(stima, di="Max 5x")}], [lettura]):
        male.append("piani.json: una stima su un piano che ha già una misura vera (anche se conserva la sua 'stima') non deve fermare il rilascio")
    if problemi_piani([pro, dict(max5, stima=stima)], []):
        male.append("piani.json: un piano con stima dichiarata (base, rapporto, motivo) non deve fermare il rilascio")
    if problemi_piani([pro, max5], [{"giorno": "2026-11-15", "piano": "Max", "punti": 1, "durata_min": 1, "escluso": "motivo"}]):
        male.append("taratura.json: una lettura dichiarata 'escluso' non deve fermare il rilascio")
    esito("Pannello: piani e taratura", not male, "; ".join(male)[:400] or
          f"piani.json valido (nome, 'dal' con il fuso di Roma, in ordine, azzeramento confermato, stima con base e motivo), ogni lettura di taratura.json su un piano noto o dichiarata esclusa; {len(sbagliati) + 1} casi sbagliati fermati")


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
    # la riga sull'AI: una fonte sola (pagine.RIGA_AI) per sito, PDF e newsletter; il modello in Kit è una copia del file
    try:
        riga = re.search(r'RIGA_AI = \((.*?)\)\n', open(os.path.join(R, "pagine.py"), encoding="utf-8").read(), re.S).group(1)
        riga = "".join(re.findall(r'"([^"]*)"', riga))
        for modello in ("newsletter_modello.html", "newsletter_cornice.html"):
            if riga not in open(os.path.join(R, modello), encoding="utf-8").read():
                male.append(f"{modello}: la riga sull'AI non è quella di pagine.RIGA_AI")
        if "_RIGA_AI" not in open(os.path.join(R, "gommberg_engine.py"), encoding="utf-8").read():
            male.append("gommberg_engine.py: il PDF non usa pagine.RIGA_AI")
    except Exception as e:  # noqa: BLE001
        male.append(f"riga sull'AI: {e}"[:90])
    esito("Sito: dati, feed, mappa e link interni", not male, "; ".join(male)[:300] or
          f"{len(pagine)} pagine, ultima edizione n. {ultimo}")
    # punto fisso: le pagine nel repository sono quelle che pagine.py genera oggi da edizioni.json. Se differiscono, o
    # pagine.py è cambiato senza rigenerarle nello stesso commit, o sono state toccate a mano: i lettori vedrebbero il
    # cambiamento solo alla prossima edizione, lontano da chi l'ha fatto.
    import filecmp
    diversi = set()
    fisse = tuple(sorted(f for f in os.listdir(REPO) if f.endswith(".html")))   # il piè di pagina (pagine.piede_fisse)
    for base in ("e", "dati", "ultima", "feed.xml", "sitemap.xml") + fisse:
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


# --- Lo stesso grafico, da qualunque macchina sia stato disegnato ---
# Un SVG di matplotlib cambia nei byte da una versione all'altra anche quando il disegno è lo stesso: gli id dei
# caratteri e dei ritagli, e il riquadro che si sposta di qualche decimo di punto perché le scritte si misurano un filo
# diverse. Per questo due grafici non si confrontano nei byte ma in ciò che mostrano, e il verdetto è lo stesso su ogni
# macchina: stesse dimensioni; stesse scritte, nello stesso ordine, con gli stessi caratteri (i contorni delle lettere,
# non il loro nome), colore e corpo; stessi segni (linee, barre, punti, tacche, griglia) con la stessa forma, colore e
# tratto; e ogni punto allo stesso posto RISPETTO AGLI ALTRI SEGNI DELLO STESSO ASSE, tacche comprese, cioè allo stesso
# valore: per ogni asse una sola retta deve portare tutti i punti di un disegno su quelli dell'altro. Così un riquadro
# che si sposta o si stringe non conta, e un dato che si sposta rispetto alle tacche sì.
TOL_DATI = 0.1      # punti tipografici: quanto può scostarsi un punto dagli altri (due decimali nell'SVG; visti al più 0,02 pt)
TOL_CORNICE = 2.0   # quanto possono spostarsi riquadro, scritte e legenda (0,7 mm; da matplotlib 3.6 a 3.11 visti al più 0,7 pt)
_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"


def _stile(s):
    return dict(tuple(x.strip() for x in p.split(":", 1)) for p in (s or "").split(";") if ":" in p)


def _percorso(d):
    """Un attributo d: (le lettere dei comandi, i numeri)."""
    return "".join(re.findall(r"[A-Za-z]", d or "")), [float(x) for x in re.findall(_NUM, re.sub(r"[A-Za-z]", " ", d or ""))]


def disegno_svg(testo):
    """Ciò che un SVG di matplotlib mostra: misure, segni nell'ordine in cui sono disegnati e i bordi di ogni riquadro
    (axes_N). Un segno è una scritta (il commento che matplotlib lascia con il testo, i contorni dei caratteri, colore,
    posto e corpo), un percorso (comandi, punti, stile) o un simbolo ripetuto (use: posto, forma e stile del simbolo).
    Id, ritagli e definizioni non entrano."""
    import xml.etree.ElementTree as ET
    radice = ET.fromstring(testo, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True)))
    nome = lambda e: e.tag.rsplit("}", 1)[-1] if isinstance(e.tag, str) else "!"
    forme = {e.get("id"): e for e in radice.iter() if nome(e) == "path" and e.get("id")}

    def forma(e):       # la forma a cui rimanda un <use>
        f = forme.get(next((v for k, v in e.attrib.items() if k.endswith("href")), "").lstrip("#"))
        return None if f is None else _percorso(f.get("d")) + (_stile(f.get("style")),)

    d = {"misure": (radice.get("width"), radice.get("height"), radice.get("viewBox")), "segni": [], "bordi": {}}

    def visita(e, dove, asse):
        n, gid = nome(e), e.get("id") or ""
        if n in ("defs", "metadata", "clipPath", "style"):
            return
        if n == "g" and gid.startswith("text_"):
            g = next((c for c in e if nome(c) == "g"), None)
            tr = re.findall(r"(\w+)\(([^)]*)\)", (g.get("transform") or "") if g is not None else "")
            d["segni"].append({"tipo": "scritta", "dove": dove, "asse": asse, "comandi": "",
                               "testo": next((c.text.strip() for c in e if nome(c) == "!"), ""),
                               "stile": _stile(g.get("style")) if g is not None else {},
                               "punti": [float(x) for k, v in tr if k == "translate" for x in re.findall(_NUM, v)],
                               "corpo": [(k, [float(x) for x in re.findall(_NUM, v)]) for k, v in tr if k != "translate"],
                               "forma": [f[:2] for f in (forma(u) for u in (g.iter() if g is not None else ()) if nome(u) == "use")
                                         if f and f[0]]})          # i contorni dei caratteri (lo spazio non ne ha)
            return
        if n == "g" and gid.startswith("axes_"):
            dove = asse = gid
        elif n == "g" and gid.startswith("legend_"):
            dove = "legenda"
        elif n in ("path", "use"):
            s = {"tipo": n, "dove": dove, "asse": asse, "stile": _stile(e.get("style")), "ritaglio": bool(e.get("clip-path"))}
            if n == "path":
                s["comandi"], s["punti"] = _percorso(e.get("d"))
            else:
                s.update(comandi="", punti=[float(e.get("x") or 0), float(e.get("y") or 0)], forma=forma(e))
            d["segni"].append(s)
            if asse and asse not in d["bordi"] and n == "path" and len(s["punti"]) >= 4:      # il fondo del riquadro
                d["bordi"][asse] = [(min(s["punti"][j::2]), max(s["punti"][j::2])) for j in (0, 1)]
            return
        for c in e:
            visita(c, dove, asse)

    visita(radice, "figura", None)
    return d


def _retta(coppie):
    """La retta x = m*y + c che porta al meglio le y sulle x (minimi quadrati); se i posti stanno tutti in un punto,
    il solo spostamento."""
    n = len(coppie)
    if not n:
        return 1.0, 0.0
    mx, my = sum(x for x, _ in coppie) / n, sum(y for _, y in coppie) / n
    v = sum((y - my) ** 2 for _, y in coppie)
    m = sum((x - mx) * (y - my) for x, y in coppie) / v if v > 1 else 1.0
    return m, mx - m * my


def differenze_svg(a, b, misura=None):
    """Che cosa il disegno b (testo SVG) mostra di diverso dal disegno a; [] se mostrano la stessa cosa.
    misura: se è una lista, riceve gli scarti in punti (scarto, "dati" o "cornice") di ogni coordinata."""
    try:
        A, B = disegno_svg(a), disegno_svg(b)
    except Exception as e:  # noqa: BLE001
        return [f"SVG illeggibile ({type(e).__name__}: {str(e)[:60]})"]
    if A["misure"] != B["misure"]:
        return [f"dimensioni {B['misure'][0]} x {B['misure'][1]} invece di {A['misure'][0]} x {A['misure'][1]}"]
    ta, tb = ([s["testo"] for s in X["segni"] if s["tipo"] == "scritta"] for X in (A, B))
    if ta != tb:
        piu, meno = [f"'{x}'" for x in tb if x not in ta], [f"'{x}'" for x in ta if x not in tb]
        return ["scritte diverse: " + ("; ".join((["in più " + ", ".join(piu[:4])] if piu else []) +
                                                 (["in meno " + ", ".join(meno[:4])] if meno else []))
                                       or "le stesse, in un altro numero o in un altro ordine")]
    firma = lambda s: (s["tipo"], s["dove"], s["asse"], s["comandi"], len(s["punti"]), s["stile"], s.get("ritaglio"))
    if len(A["segni"]) != len(B["segni"]):
        return [f"{len(B['segni'])} segni (linee, barre, punti, tacche, scritte) invece di {len(A['segni'])}"]
    for i, (s, t) in enumerate(zip(A["segni"], B["segni"])):
        if firma(s) != firma(t):
            return [f"il segno n. {i + 1} è un altro per forma, colore o tratto: {t['tipo']} {t['stile']} con {len(t['punti']) // 2} "
                    f"punti invece di {s['tipo']} {s['stile']} con {len(s['punti']) // 2}"]
    if set(A["bordi"]) != {s["asse"] for s in A["segni"] if s["asse"]} or set(B["bordi"]) != set(A["bordi"]):
        return ["riquadro non riconosciuto"]
    out, coppie = [], list(zip(A["segni"], B["segni"]))
    largo = lambda s: s["tipo"] == "scritta" or s["dove"] == "legenda"      # stanno dove le mette la misura delle scritte
    # sul bordo del riquadro in tutti e due i disegni (assi, griglia, soglie da un lato all'altro): segue il bordo
    fermo = lambda k, j, x, y: any(abs(x - p) <= TOL_DATI and abs(y - r) <= TOL_DATI for p, r in zip(A["bordi"][k][j], B["bordi"][k][j]))
    porta = {}
    for k in A["bordi"]:
        sposta = max(abs(x - y) for j in (0, 1) for x, y in zip(A["bordi"][k][j], B["bordi"][k][j]))
        if sposta > TOL_CORNICE:
            out.append(f"il riquadro è spostato di {sposta:.2f} pt")
        for j in (0, 1):    # per ogni asse, la retta che porta su a tutti i segni di b: tacche, griglia, linee, barre, punti
            porta[k, j] = _retta([(x, y) for s, t in coppie if s["asse"] == k and not largo(s)
                                  for x, y in zip(s["punti"][j::2], t["punti"][j::2]) if not fermo(k, j, x, y)])
    stesso = lambda x, y, tol: len(x) == len(y) and all(abs(p - q) <= tol for p, q in zip(x, y))
    peggio = {}
    for i, (s, t) in enumerate(coppie):
        if s["tipo"] == "scritta":
            if [k for k, _ in s["corpo"]] != [k for k, _ in t["corpo"]] or not all(stesso(x, y, 1e-3) for (_, x), (_, y) in zip(s["corpo"], t["corpo"])):
                out.append(f"la scritta '{s['testo']}' ha un altro corpo")
            if [c for c, _ in s["forma"]] != [c for c, _ in t["forma"]] or not all(stesso(x, y, 0.5) for (_, x), (_, y) in zip(s["forma"], t["forma"])):
                out.append(f"la scritta '{s['testo']}' è disegnata con altri caratteri")
        elif s["tipo"] == "use":
            fa, fb = s["forma"], t["forma"]
            if (fa is None) != (fb is None) or (fa and (fa[0] != fb[0] or fa[2] != fb[2] or not stesso(fa[1], fb[1], 0.02))):
                out.append(f"il segno n. {i + 1} (punto o tacca) ha un'altra forma o un'altra misura")
        for q, (x, y) in enumerate(zip(s["punti"], t["punti"])):
            m, c = porta[s["asse"], q % 2] if s["asse"] else (1.0, 0.0)       # fuori dai riquadri c'è solo il fondo della figura
            tol = TOL_CORNICE if largo(s) else TOL_DATI
            scarto = 0.0 if s["asse"] and not largo(s) and fermo(s["asse"], q % 2, x, y) else abs(m * y + c - x)
            if misura is not None:
                misura.append((scarto, "cornice" if largo(s) else "dati"))
            if scarto > tol and scarto > peggio.get(i, (0, None))[0]:
                peggio[i] = (scarto, s)
    for i, (scarto, s) in sorted(peggio.items())[:4]:
        che = f"la scritta '{s['testo']}'" if s["tipo"] == "scritta" else \
            f"il segno n. {i + 1} ({'punto o tacca' if s['tipo'] == 'use' else 'linea o barra'} {s['stile'].get('stroke') or s['stile'].get('fill') or ''})"
        out.append(f"{che} è a {scarto:.2f} pt da dove lo vogliono gli altri segni")
    if len(peggio) > 4:
        out.append(f"e altri {len(peggio) - 4} segni spostati")
    return out


def stesso_grafico(a, b):
    """'' se il file SVG b mostra lo stesso grafico del file a, altrimenti che cosa cambia."""
    if not os.path.isfile(b):
        return "manca"
    return "; ".join(differenze_svg(open(a, encoding="utf-8").read(), open(b, encoding="utf-8").read())[:3])


def passo_analisi(copia):
    """Le pagine delle analisi (G-64, analisi_sito.py) sulla copia di passo_sito: una pagina per ogni analisi delle
    edizioni con sorgenti e nessuna per le altre, testo identico a quello stampato nel PDF, link e mappa del sito; poi,
    su una seconda copia, un sorgente rotto e un titolo che non corrisponde non fermano pagine.py, e un'estrazione
    rifatta da zero con il kit di oggi ridà gli stessi dati, le stesse pagine e gli stessi grafici (questi confrontati
    in ciò che mostrano, non nei byte: stesso_grafico, che passo_grafici mette alla prova)."""
    import html as H
    sys.path.insert(0, os.path.join(copia, "redazione"))
    import analisi_sito as A
    base = "https://gommberg.com/"
    piano = lambda t: re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"</?(?:span|b|i|a|em)\b[^>]*>", "", t)))).strip()
    testo_pdf = lambda f: re.sub(r"\s+", " ", esegui(["pdftotext", f, "-"])[1].replace("­", "")).strip()
    voci = sorted(json.load(open(os.path.join(copia, "edizioni.json"), encoding="utf-8")), key=lambda e: e["numero"])
    mappa = open(os.path.join(copia, "sitemap.xml"), encoding="utf-8").read()
    male, uguali, pezzi, nate, con = [], [], 0, 0, 0
    for ed in voci:
        n = f"{ed['numero']:03d}"
        src = os.path.join(copia, "redazione", "sorgenti", ed["data"])
        cart = os.path.join(copia, "e", n)
        if not os.path.isfile(os.path.join(src, "edizione.py")):
            if os.path.isdir(cart):
                male.append(f"e/{n}/ esiste ma l'edizione non ha sorgenti")
            continue
        con += 1
        try:
            d = json.load(open(os.path.join(src, A.FILE), encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            male.append(f"n. {n}: {A.FILE} illeggibile ({e})"[:90]); continue
        if d.get("errore"):
            male.append(f"n. {n}: estrazione fallita ({d['errore'][:60]})"); continue
        pagina_ed = open(os.path.join(copia, "e", n + ".html"), encoding="utf-8").read()
        pdf = testo_pdf(os.path.join(copia, ed["file"]))
        for i, m in A.collega(ed, d):
            rel = A.indirizzo(ed, m)
            f = os.path.join(copia, rel)
            if not os.path.isfile(f):
                male.append(f"manca {rel}"); continue
            nate += 1
            h = open(f, encoding="utf-8").read()
            vis = piano(re.sub(r"<(script|style)\b.*?</\1>", " ", h, flags=re.S))   # quello che legge chi non esegue il JavaScript
            campi = ([m.get(k) for k in ("titolo", "perche", "quindi", "numero", "guardare", "fonte")] + list(m.get("testo") or [])
                     + list(m.get("punti") or [])[:3] + [c for r in m.get("righe") or [] for c in r])
            for c in [A._piano(x) for x in campi if x]:
                pezzi += 1
                if c not in pdf:
                    male.append(f"{rel}: testo che non è nel PDF: '{c[:40]}'")
                # "Il numero" va in pagina in due pezzi (la cifra grande, poi la frase): i due pezzi, senza i due punti
                if c not in vis and not (c == A._piano(m.get("numero")) and all(x.strip() in vis for x in c.split(":", 1))):
                    male.append(f"{rel}: testo che manca nella pagina: '{c[:40]}'")
            try:
                ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', h, re.S).group(1))
                assert ld["@type"] == "NewsArticle" and ld["headline"] and ld["datePublished"].startswith(ed["data"]) and ld["url"] == base + rel
            except Exception:  # noqa: BLE001
                male.append(f"{rel}: dati strutturati mancanti o sbagliati")
            if f'<link rel="canonical" href="{base + rel}">' not in h:
                male.append(f"{rel}: canonico sbagliato")
            if f"<url><loc>{base + rel}</loc><lastmod>{ed['data']}</lastmod>" not in mappa:
                male.append(f"{rel}: non è nella sitemap con il giorno dell'edizione")
            if f'href="{n}/{m["pagina"]}.html"' not in pagina_ed:
                male.append(f"e/{n}.html non porta a {rel}")
            if "Testi generati con l'intelligenza artificiale" not in h or 'href="../../' + ed["file"] not in h:
                male.append(f"{rel}: manca la riga AI o il rimando al giornale")
            for u in re.findall(r"""(?:href|src|srcset)=["']([^"'#?]+)""", re.sub(r"<script\b.*?</script>", "", h, flags=re.S)):
                if not re.match(r"(?:[a-z]+:|//)", u) and not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(f), u))):
                    male.append(f"{rel} -> {u}: link rotto")
    for loc in re.findall(r"<loc>https://gommberg\.com/(e/\d{3}/[^<]+)</loc>", mappa):
        if not os.path.isfile(os.path.join(copia, loc)):
            male.append(f"sitemap: {loc} non esiste")
    esito("Analisi: una pagina per analisi, testo uguale al PDF", not male and nate > 0,
          "; ".join(dict.fromkeys(male))[:400] or f"{nate} pagine da {con} edizioni con sorgenti, {pezzi} testi uguali nel PDF e nella pagina "
          "(anche senza JavaScript); dati strutturati, canonico, sitemap, link")
    # seconda copia: un sorgente rotto, un titolo che non corrisponde e un'estrazione da rifare da zero
    prova = os.path.join(TMP, "sito_analisi")
    shutil.copytree(copia, prova, ignore=shutil.ignore_patterns("__pycache__"))
    con_src = [e for e in voci if os.path.isfile(os.path.join(prova, "redazione", "sorgenti", e["data"], "edizione.py"))]
    male = []
    if len(con_src) < 4:
        return esito("Analisi: un sorgente rotto non ferma l'edizione", False, "servono almeno 4 edizioni con sorgenti")
    rotta, rifatta, storta, guasta = con_src[-1], con_src[-2], con_src[-3], con_src[-4]
    nr, nf, ns, ng = (f"{e['numero']:03d}" for e in (rotta, rifatta, storta, guasta))
    sr = os.path.join(prova, "redazione", "sorgenti", rotta["data"])
    originale = open(os.path.join(sr, "edizione.py"), encoding="utf-8").read()
    open(os.path.join(sr, "edizione.py"), "a", encoding="utf-8").write("\nC = {\n")      # errore di sintassi
    # un guasto dell'ambiente (una libreria che manca) non si salva come errore: si riprova alla volta successiva
    sg = os.path.join(prova, "redazione", "sorgenti", guasta["data"])
    eg = open(os.path.join(sg, "edizione.py"), encoding="utf-8").read()
    open(os.path.join(sg, "edizione.py"), "w", encoding="utf-8").write("import libreria_che_non_ce_g64  # noqa\n" + eg)
    os.remove(os.path.join(sg, A.FILE))
    os.remove(os.path.join(sr, A.FILE))
    sf = os.path.join(prova, "redazione", "sorgenti", rifatta["data"])
    os.remove(os.path.join(sf, A.FILE))
    shutil.rmtree(os.path.join(prova, "e", nf))
    ed_json = json.load(open(os.path.join(prova, "edizioni.json"), encoding="utf-8"))
    for e in ed_json:
        if e["numero"] == storta["numero"]:
            e["approfondimenti"][0]["titolo"] += " (corretto)"
    json.dump(ed_json, open(os.path.join(prova, "edizioni.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    rc, out = esegui([sys.executable, os.path.join(prova, "redazione", "pagine.py"), prova], timeout=900)
    if rc:
        male.append("pagine.py si è fermato: " + out.strip().splitlines()[-1][:120])
    else:
        if f"AVVISO analisi n. {nr}" not in out:
            male.append(f"nessun avviso per il sorgente rotto del n. {nr}")
        if not json.load(open(os.path.join(sr, A.FILE), encoding="utf-8")).get("errore"):
            male.append("il sorgente rotto non ha lasciato l'errore in analisi.json")
        if os.path.isdir(os.path.join(prova, "e", nr)) and any(f.endswith(".html") for f in os.listdir(os.path.join(prova, "e", nr))):
            male.append(f"e/{nr}/ ha ancora pagine di analisi con il sorgente rotto")
        if "Leggi il testo qui" in open(os.path.join(prova, "e", nr + ".html"), encoding="utf-8").read():
            male.append(f"e/{nr}.html porta a pagine che non esistono")
        if f"e/{nr}/" in open(os.path.join(prova, "sitemap.xml"), encoding="utf-8").read():
            male.append(f"la sitemap ha ancora le pagine del n. {nr}")
        primo = json.load(open(os.path.join(copia, "redazione", "sorgenti", storta["data"], A.FILE), encoding="utf-8"))["moduli"][0]["pagina"]
        if os.path.exists(os.path.join(prova, "e", ns, primo + ".html")) or \
                any(f.startswith(primo + "-") for f in os.listdir(os.path.join(prova, "e", ns))):
            male.append(f"e/{ns}/{primo}.html è nata con un titolo diverso da edizioni.json")
        if len([f for f in os.listdir(os.path.join(prova, "e", ns)) if f.endswith(".html")]) != len(storta["approfondimenti"]) - 1:
            male.append(f"n. {ns}: con un titolo diverso devono restare le altre pagine")
        if os.path.exists(os.path.join(sg, A.FILE)) or "guasto dell'ambiente" not in out:
            male.append(f"n. {ng}: un guasto dell'ambiente è stato salvato come errore del sorgente, o non ha dato l'avviso")
        # rifatto da zero: i dati estratti e le pagine non dipendono dalla macchina e si confrontano byte per byte; i
        # grafici li disegna matplotlib, e si confrontano in ciò che mostrano (stesso_grafico)
        import filecmp
        if not filecmp.cmp(os.path.join(sf, A.FILE), os.path.join(copia, "redazione", "sorgenti", rifatta["data"], A.FILE), shallow=False):
            male.append(f"n. {nf}: {A.FILE} rifatto da zero diverso da quello nel repository")
        ca, cb = os.path.join(copia, "e", nf), os.path.join(prova, "e", nf)
        for f in sorted(set(os.listdir(ca)) | set(os.listdir(cb) if os.path.isdir(cb) else ())):
            a, b = os.path.join(ca, f), os.path.join(cb, f)
            if not os.path.exists(a):
                male.append(f"n. {nf}: e/{nf}/{f} rifatto da zero è un file in più")
            elif not os.path.exists(b):
                male.append(f"n. {nf}: e/{nf}/{f} rifatto da zero manca")
            elif f.endswith(".svg"):
                altro = stesso_grafico(a, b)
                if altro:
                    male.append(f"n. {nf}: e/{nf}/{f} rifatto da zero è un altro grafico ({altro})")
            elif not filecmp.cmp(a, b, shallow=False):
                male.append(f"n. {nf}: e/{nf}/{f} rifatto da zero diverso da quello nel repository")
        # il sorgente rotto si corregge: alla pubblicazione dopo l'errore salvato si riprova da solo e le pagine tornano
        open(os.path.join(sr, "edizione.py"), "w", encoding="utf-8").write(originale)
        rc, out = esegui([sys.executable, os.path.join(prova, "redazione", "pagine.py"), prova], timeout=900)
        n_ok = len(json.load(open(os.path.join(copia, "redazione", "sorgenti", rotta["data"], A.FILE), encoding="utf-8"))["moduli"])
        if rc or not os.path.isdir(os.path.join(prova, "e", nr)) or \
                len([f for f in os.listdir(os.path.join(prova, "e", nr)) if f.endswith(".html")]) != n_ok:
            male.append(f"n. {nr}: corretto il sorgente, le pagine non sono tornate da sole")
    esito("Analisi: un sorgente rotto non ferma l'edizione", not male, "; ".join(male)[:400] or
          f"n. {nr} rotto: avviso, nessuna pagina né link né riga nella sitemap, il resto esce, e corretto il sorgente le pagine "
          f"tornano da sole; n. {ng} con un guasto dell'ambiente: avviso, nessun errore salvato; n. {ns} con un titolo diverso: "
          f"quella pagina e i suoi grafici non restano, le altre sì; n. {nf} rifatto da zero con il kit di oggi: stessi dati e stesse "
          "pagine byte per byte, stessi grafici nel contenuto")


def _grafici_di_prova():
    """Due grafici costruiti come quelli delle analisi (linee con due serie e una soglia, barre) e, per ciascuno, le
    copie sbagliate che il confronto deve vedere: {nome: dati}, [(nome del giusto, nome dello sbagliato, che cosa cambia)]."""
    giorni = [g for g in (dt.date(2026, 11, 2) + dt.timedelta(days=i) for i in range(19)) if g.weekday() < 5]
    linee = {"tipo": "linee", "x": [{"$d": g.isoformat()} for g in giorni], "unita": "%", "soglie": [[5.0, "5%"]],
             "serie": [["10 anni", [5.15, 5.12, 5.13, 4.96, 5.0, 5.0, 4.99, 5.05, 4.98, 4.94, 4.91, 4.95, 4.9, 4.84, 4.86], "#F26B1D"],
                       ["2 anni", [4.77, 4.79, 4.81, 4.65, 4.69, 4.68, 4.7, 4.75, 4.66, 4.62, 4.6, 4.63, 4.58, 4.5, 4.52], "#111111"]]}
    barre = {"tipo": "barre", "ordina": False, "dec": 1, "unita": "%",
             "dati": [["Taiwan (Taiex)", -6.0], ["Corea (Kospi)", -3.6], ["Giappone (Nikkei)", -2.4], ["Cina (Shanghai)", -0.9],
                      ["Hong Kong (Hang Seng)", 0.5]]}
    copia = lambda g: json.loads(json.dumps(g))
    grafici, casi = {"linee": linee, "barre": barre}, []

    def caso(base, nome, che, cambia):
        g = copia(grafici[base]); cambia(g)
        grafici[nome] = g; casi.append((base, nome, che))

    caso("linee", "linee-dato", "un dato a metà serie spostato di 0,002 (da 5,05 a 5,052)", lambda g: g["serie"][0][1].__setitem__(7, 5.052))
    caso("linee", "linee-serie", "una serie tolta", lambda g: g["serie"].pop())
    caso("linee", "linee-nome", "il nome di una serie cambiato", lambda g: g["serie"][1].__setitem__(0, "3 anni"))
    caso("linee", "linee-colore", "il colore di una serie cambiato", lambda g: g["serie"][1].__setitem__(2, "#1F5FA8"))
    caso("linee", "linee-soglia", "la soglia spostata da 5 a 5,01 con la stessa scritta", lambda g: g["soglie"][0].__setitem__(0, 5.01))
    caso("linee", "linee-unita", "l'unità di misura tolta", lambda g: g.pop("unita"))
    caso("barre", "barre-dato", "una barra allungata di 0,02 senza cambiare la sua etichetta (-3,6%)", lambda g: g["dati"][1].__setitem__(1, -3.62))
    caso("barre", "barre-nome", "il nome di una barra cambiato", lambda g: g["dati"][1].__setitem__(0, "Corea (Kosdaq)"))
    caso("barre", "barre-meno", "una barra tolta", lambda g: g["dati"].pop())
    return grafici, casi


def passo_grafici(copia):
    """Il confronto dei grafici (stesso_grafico) dà lo stesso verdetto su ogni macchina ed è un controllo vero.
    1. Verde dove deve: in redazione/rete/grafici/ ogni grafico c'è due volte, <nome>.<versione>.svg, disegnato dagli
       stessi dati con due versioni di matplotlib (diverso nei byte): il confronto deve dirli uguali. Sono file fermi,
       come i campioni della rete: se il confronto torna a dipendere dalla versione, diventa rosso anche in locale.
    2. Rosso dove deve: due grafici costruiti e le loro copie con un dato, una serie, una scritta, un colore cambiati,
       disegnati adesso da analisi_sito.py; più il grafico del telefono al posto di quello per PC e un file che manca."""
    male, gruppi = [], {}
    for f in sorted(glob.glob(os.path.join(RETE, "grafici", "*.svg"))):
        gruppi.setdefault(os.path.basename(f).split(".", 1)[0], []).append(f)
    for ff in gruppi.values():
        for f in ff[1:]:
            altro = stesso_grafico(ff[0], f)
            if open(f, "rb").read() == open(ff[0], "rb").read():
                male.append(f"{os.path.basename(f)} è identico a {os.path.basename(ff[0])}: il campione non prova nulla")
            elif altro:
                male.append(f"{os.path.basename(f)} è {os.path.basename(ff[0])} disegnato da un'altra matplotlib, ma risulta diverso: {altro}")
    if len(gruppi) < 3 or any(len(ff) < 2 for ff in gruppi.values()):
        male.append("in redazione/rete/grafici/ servono almeno tre grafici, ognuno disegnato da due versioni di matplotlib")
    grafici, casi = _grafici_di_prova()
    cart = os.path.join(TMP, "grafici")
    os.makedirs(cart)
    json.dump({"moduli": [{"grafici": [{"file": k, "dati": v} for k, v in grafici.items()]}]},
              open(os.path.join(cart, "grafici.json"), "w", encoding="utf-8"), ensure_ascii=False)
    rc, out = esegui([sys.executable, os.path.join(copia, "redazione", "analisi_sito.py"), "disegna", os.path.join(cart, "grafici.json"), cart])
    if rc:
        return esito("Analisi: il confronto dei grafici", False, "i grafici di prova non si disegnano: " + (out.strip().splitlines() or ["?"])[-1][:200])
    svg = lambda nome, suff="": os.path.join(cart, nome + suff + ".svg")
    for base in ("linee", "barre"):
        for suff in ("", "-m"):
            if stesso_grafico(svg(base, suff), svg(base, suff)):
                male.append(f"{base}{suff}: un grafico risulta diverso da se stesso ({stesso_grafico(svg(base, suff), svg(base, suff))})")
        if not stesso_grafico(svg(base), svg(base, "-m")):
            male.append(f"{base}: il grafico del telefono al posto di quello per PC non è visto")
        if not stesso_grafico(svg(base), svg(base + "-che-non-esiste")):
            male.append(f"{base}: un grafico che manca non è visto")
    for base, nome, che in casi:
        for suff in ("", "-m"):
            if not stesso_grafico(svg(base, suff), svg(nome, suff)):
                male.append(f"{base}{suff}: non è visto {che}")
    versioni = sorted({os.path.basename(f).split(".", 1)[1][:-4] for ff in gruppi.values() for f in ff})
    esito("Analisi: il confronto dei grafici", not male, "; ".join(male)[:500] or
          f"{len(gruppi)} grafici disegnati da matplotlib {', '.join(versioni)}: stesso contenuto con byte diversi; "
          f"{len(casi) + 2} grafici sbagliati apposta visti tutti, su PC e telefono: " + "; ".join(c for _, _, c in casi) +
          "; il grafico del telefono al posto di quello per PC; un file che manca")


def passo_lettori(copia):
    """La Gommunity (G-13): il servizio vero contro un D1 finto (redazione/sito/prova_lettori.mjs, Node 22.5+),
    la sintassi del codice che gira nel browser, la configurazione e l'avviso a Paolo sulle segnalazioni."""
    male = []
    node = shutil.which("node")
    if not node:
        return esito("Lettori: servizio dei commenti", False, "manca Node (serve la 22.5 o più): il servizio non è collaudato")
    rc, out = esegui([node, "--no-warnings", os.path.join(R, "sito", "prova_lettori.mjs")])
    esito("Lettori: servizio dei commenti", rc == 0, out.strip().splitlines()[-1][:200] if out.strip() else f"uscita {rc}")
    for f in sorted(glob.glob(os.path.join(REPO, "assets", "*.js"))) + sorted(glob.glob(os.path.join(R, "sito", "*.js"))) + sorted(glob.glob(os.path.join(R, "sito", "*.mjs"))):
        rc, out = esegui([node, "--check", f])
        if rc:
            male.append(os.path.relpath(f, REPO) + ": " + out.strip().splitlines()[-1][:90])
    # i nomi riservati: la stessa regola nel browser e nel servizio
    rx = [re.search(r"RISERVATI = (/[^/]+/i)", open(f, encoding="utf-8").read()) for f in (os.path.join(REPO, "assets", "lettori.js"), os.path.join(R, "sito", "lettori.js"))]
    if not all(rx) or rx[0].group(1) != rx[1].group(1):
        male.append("nomi riservati diversi tra assets/lettori.js e redazione/sito/lettori.js")
    # la versione dei file nella homepage e nelle edizioni è la stessa (il browser riprende i file nuovi insieme)
    v = re.search(r'LETTORI_V = "([^"]+)"', open(os.path.join(R, "pagine.py"), encoding="utf-8").read()).group(1)
    home = open(os.path.join(REPO, "index.html"), encoding="utf-8").read()
    for f in ("lettori.css", "lettori.js"):
        if f"assets/{f}?v={v}" not in home:
            male.append(f"index.html: assets/{f} senza ?v={v} (pagine.LETTORI_V)")
    # configurazione: solo /api/* passa dal codice, il resto resta statico
    cfg = re.sub(r"^\s*//.*$", "", open(os.path.join(R, "sito", "wrangler.jsonc"), encoding="utf-8").read(), flags=re.M)
    try:
        c = json.loads(cfg)
        if c.get("main") != "lettori.js" or c["assets"].get("run_worker_first") != ["/api/*"] or c["d1_databases"][0]["binding"] != "DB":
            male.append("wrangler.jsonc: main, run_worker_first o il database non sono quelli di lettori.js")
    except Exception as e:  # noqa: BLE001
        male.append(f"wrangler.jsonc: {e}"[:90])
    # la pagina delle regole che la sezione collega esiste
    if "/regole.html" not in open(os.path.join(REPO, "assets", "lettori.js"), encoding="utf-8").read() or not os.path.exists(os.path.join(REPO, "regole.html")):
        male.append("regole.html manca o la sezione non la collega")
    esito("Lettori: codice e configurazione", not male, "; ".join(male)[:300] or "sintassi, nomi riservati, versione dei file, regole e configurazione in ordine")
    # l'avviso a Paolo (segnalazioni.py, lanciato ogni 3 ore da segnalazioni.yml con l'orologio), con un gh finto che
    # registra le chiamate: una segnalazione per commento e mai il testo; riapre e aggiorna; al massimo 5 nuove per giro;
    # un guasto fa fallire il giro solo alle 11 di Roma (o a mano), e nel flusso "| tee" non lo nasconde
    male = []
    script = os.path.join(R, "sito", "segnalazioni.py")
    banco = os.path.join(copia, "_segnalazioni")
    os.makedirs(os.path.join(banco, "bin"), exist_ok=True)
    elenco, fatte, diario, finto = (os.path.join(banco, x) for x in ("elenco.json", "fatte.json", "gh.txt", os.path.join("bin", "gh")))
    open(finto, "w", encoding="utf-8").write('#!/usr/bin/env bash\nprintf "%s\\n" "$*" >> "$GH_DIARIO"\nexit "${GH_ESCE:-0}"\n')
    os.chmod(finto, 0o755)

    def giro(righe, esistenti, *arg, ora="15", esce="0", a_mano=""):
        json.dump({"sito": "gommberg", "segnalati": righe} if righe is not None else "non è un elenco", open(elenco, "w", encoding="utf-8"))
        json.dump(esistenti, open(fatte, "w", encoding="utf-8"))
        open(diario, "w").close()
        rc, out = esegui([sys.executable, script, *arg], env={"GTD_ELENCO": elenco, "GTD_ESISTENTI": fatte, "GTD_ORA": ora, "GH_DIARIO": diario,
                                                              "GH_ESCE": esce, "A_MANO": a_mano, "GITHUB_REPOSITORY_OWNER": "PaoloGom",
                                                              "PATH": os.path.join(banco, "bin") + os.pathsep + os.environ.get("PATH", "")})
        return rc, out, open(diario, encoding="utf-8").read()

    def s(n, nascosto=False, ultima="2026-11-23T09:42:10Z", ed=31):
        return {"id": n, "ed": ed, "reti": 3 if nascosto else 1, "nascosto": nascosto, "ultima": ultima, "testo": "NON-DEVE-USCIRE", "nome": "NON-DEVE-USCIRE"}

    rc, out, gh = giro([s(123), s(7, True, ed=30), {"id": "x"}], [], "--prova")
    if rc or out.count("Farei - Apro: ") != 2 or "commento n. 123 segnalato (edizione n. 031)" not in out or "(edizione n. 030) - nascosto" not in out or "23/11/2026 alle 10:42" not in out or gh:
        male.append("a secco: due commenti segnalati non danno due segnalazioni complete, o tocca GitHub")
    rc, out, gh = giro([s(123), s(7, True, ed=30)], [])
    if rc or gh.count("issue create") != 2 or gh.count("--label gommunity") != 2 or gh.count("--assignee PaoloGom") != 2:
        male.append("due commenti nuovi non aprono due segnalazioni con etichetta e assegnatario")
    if "NON-DEVE-USCIRE" in out + gh:
        male.append("il testo o il nome del commento finisce nella segnalazione")
    gia = [{"number": 41, "title": "La Gommunity: commento n. 123 segnalato (edizione n. 031)", "state": "OPEN", "closedAt": None},
           {"number": 42, "title": "La Gommunity: commento n. 7 segnalato (edizione n. 030)", "state": "CLOSED", "closedAt": "2026-11-22T10:00:00Z"},
           {"number": 43, "title": "La Gommunity: commento n. 12 segnalato (edizione n. 031)", "state": "CLOSED", "closedAt": "2026-11-24T10:00:00Z"},
           {"number": 44, "title": "La Gommunity: commento n. 1234 segnalato (edizione n. 031)", "state": "OPEN", "closedAt": None}]
    rc, out, gh = giro([s(123), s(7, ultima="2026-11-21T09:00:00Z"), s(12)], gia)
    if rc or gh.strip():
        male.append("commenti già avvisati e fermi: non deve fare nulla")
    rc, out, gh = giro([s(123, True), s(7), s(12)], gia)
    if rc or "issue comment 41" not in gh or "issue edit 41" not in gh or "- nascosto" not in gh or "issue reopen 42" not in gh or "issue create" in gh or " 43" in gh or " 44" in gh:
        male.append("nascosto dopo l'avviso o segnalato di nuovo dopo la chiusura: deve aggiornare la 41 e riaprire la 42, e basta")
    rc, out, gh = giro([s(n) for n in range(200, 208)], [])
    if rc or gh.count("issue create") != 5 or out.count("Al prossimo giro") != 3:
        male.append("otto commenti nuovi: 5 segnalazioni in questo giro e 3 al prossimo")
    for righe, esce, cosa in ((None, "0", "elenco illeggibile"), ([s(300)], "1", "GitHub che rifiuta")):
        rc15, out15, gh15 = giro(righe, [], ora="15", esce=esce)
        rc10, _, _ = giro(righe, [], ora="11", esce=esce)
        rc12, _, _ = giro(righe, [], ora="12", esce=esce)     # la riserva di GitHub d'estate passa alle 12:15
        rc14, _, _ = giro(righe, [], ora="14", esce=esce)
        rcm, _, _ = giro(righe, [], ora="15", esce=esce, a_mano="true")
        if rc15 != 0 or rc10 != 1 or rc12 != 1 or rc14 != 0 or rcm != 1 or "::warning::" not in out15:
            male.append(f"{cosa}: avviso nel riepilogo, giro fallito solo tra le 11 e le 14 o a mano (uscite {rc15}, {rc10}, {rc12}, {rc14}, {rcm})")
    flusso = open(os.path.join(REPO, ".github", "workflows", "segnalazioni.yml"), encoding="utf-8").read()
    if "redazione/sito/segnalazioni.py" not in flusso or "issues: write" not in flusso or "orologio:" not in flusso:
        male.append("segnalazioni.yml: non lancia lo script, non lo può lanciare l'orologio o non può aprire segnalazioni")
    if not re.search(r"defaults:\s*\n\s*run:\s*\n\s*shell: bash", flusso) or "A_MANO" not in flusso:
        male.append("segnalazioni.yml: senza 'shell: bash' un giro fallito resta verde; manca A_MANO")
    shutil.rmtree(banco, ignore_errors=True)
    esito("Lettori: avviso sulle segnalazioni", not male, "; ".join(male)[:300] or "una segnalazione per commento e mai il testo; riapre e aggiorna; 5 nuove per giro; un guasto avvisa una volta al giorno")


# ---------------------------------------------------------------- l'orologio dei controlli e i minuti (G-58, G-12)
def passo_orologio():
    """L'orologio dei controlli (redazione/sito/orologio.js, il cron del Worker che lancia i flussi di GitHub) con un
    GitHub finto che accetta, rifiuta e tace, a orari d'inverno e d'estate; la lettura del suo stato (orologio.py: la
    guardia delle sveglie di riserva e la riga del controllo del mattino); i flussi che lancia; la stima dei minuti di
    GitHub (minuti.py) con un GitHub finto; la mappa in ARCHITETTURA.md."""
    node = shutil.which("node")
    if not node:
        return esito("Orologio: partenze dei controlli", False, "manca Node (serve la 22.5 o più): l'orologio non è collaudato")
    rc, out = esegui([node, "--no-warnings", os.path.join(R, "sito", "prova_orologio.mjs")])
    esito("Orologio: partenze dei controlli", rc == 0, (out.strip().splitlines() or [f"uscita {rc}"])[-1][:200] if rc == 0 else out.strip()[-300:])

    male = []
    rc, out = esegui([node, "--input-type=module", "-e", "import { SVEGLIE } from " + json.dumps("file://" + os.path.join(R, "sito", "orologio.js")) + "; console.log(JSON.stringify(SVEGLIE))"])
    try:
        sveglie = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        sveglie = []
        male.append("SVEGLIE di orologio.js non leggibili")
    try:
        import yaml
    except ImportError:
        yaml = None
        NOTE.append("flussi dell'orologio non letti (manca PyYAML)")
    cartella = os.path.join(REPO, ".github", "workflows")
    flussi = {}
    for f in sorted(glob.glob(os.path.join(cartella, "*.yml"))) if yaml else []:
        d = yaml.safe_load(open(f, encoding="utf-8"))
        flussi[os.path.basename(f)] = (d, open(f, encoding="utf-8").read())
    lanciati = {x["flusso"] for x in sveglie}
    for x in sveglie if yaml else []:
        if x["flusso"] not in flussi:
            male.append(f"l'orologio lancia {x['flusso']}, che non esiste")
            continue
        d = flussi[x["flusso"]][0]
        su = d.get("on", d.get(True)) or {}
        inp = ((su.get("workflow_dispatch") or {}).get("inputs") or {}) if isinstance(su, dict) else {}
        for k, v in x["inputs"].items():
            if k not in inp:
                male.append(f"{x['flusso']}: l'orologio passa '{k}', che il flusso non dichiara (GitHub rifiuterebbe con 422)")
            elif inp[k].get("type") == "choice" and v not in inp[k].get("options", []):
                male.append(f"{x['flusso']}: '{k}={v}' non è tra le scelte del flusso")
    for nome, (d, testo) in flussi.items():
        su = d.get("on", d.get(True)) or {}
        if isinstance(su, dict) and "schedule" in su:
            # una sveglia di GitHub resta solo come riserva: la copre l'orologio e ogni job la salta quando l'orologio è sano
            if nome not in lanciati:
                male.append(f"{nome}: sveglia di GitHub che l'orologio non copre")
            for job, j in (d.get("jobs") or {}).items():
                passi = j.get("steps") or []
                if not any(f"orologio.py --guardia {nome}" in str(p.get("run", "")) for p in passi):
                    male.append(f"{nome}, job {job}: sveglia di riserva senza la guardia dell'orologio sul proprio flusso (partirebbe due volte)")
    for nome in ("mattino.yml", "segnalazioni.yml", "dem.yml", "newsletter.yml"):
        for job, j in ((flussi.get(nome) or [{}])[0].get("jobs") or {}).items():
            if j.get("runs-on") != "ubuntu-slim" or int(j.get("timeout-minutes", 99)) > 15:
                male.append(f"{nome}, job {job}: un controllo leggero va su ubuntu-slim con al massimo 15 minuti (G-12)")
        if yaml and nome in flussi and not re.search(r"Minuti di GitHub", flussi[nome][1]):
            male.append(f"{nome}: non dichiara quanti minuti di GitHub costa al mese")
    for job in ("controllo", "gomm"):
        if yaml and "mattino.yml" in flussi and not (((flussi["mattino.yml"][0].get("jobs") or {}).get(job) or {}).get("concurrency") or {}).get("group"):
            male.append(f"mattino.yml, job {job}: senza coda d'attesa (concurrency) due partenze vicine lavorerebbero insieme")
    cfg = json.loads(re.sub(r"^\s*//.*$", "", open(os.path.join(R, "sito", "wrangler.jsonc"), encoding="utf-8").read(), flags=re.M))
    if (cfg.get("triggers") or {}).get("crons") != ["*/15 * * * *"]:
        male.append("wrangler.jsonc: il cron dell'orologio non è un solo '*/15 * * * *'")
    if "GITHUB_REPOSITORY" in json.dumps(cfg.get("vars", {})):
        male.append("wrangler.jsonc: GITHUB_REPOSITORY scritto a mano (lo passa sito.yml)")
    sito = open(os.path.join(cartella, "sito.yml"), encoding="utf-8").read()
    if '--var "GITHUB_REPOSITORY:$REPOSITORY"' not in sito or "REPOSITORY: ${{ github.repository }}" not in sito or '"triggers"' not in sito:
        male.append("sito.yml: non passa il nome del repository all'orologio, o la configurazione di riserva tiene il cron")
    js = open(os.path.join(R, "sito", "orologio.js"), encoding="utf-8").read()
    if re.search(r"PaoloGom|gommberg-terminal-daily", js, re.I):
        male.append("orologio.js: nome del repository scritto nel codice (deve venire da GITHUB_REPOSITORY)")
    esito("Orologio: flussi, cron e configurazione", not male, "; ".join(male)[:400] or
          f"{len(sveglie)} sveglie, ognuna su un flusso che accetta i suoi inputs; ogni sveglia di GitHub rimasta ha la guardia; controlli leggeri su ubuntu-slim; nome del repository solo da sito.yml")

    # la lettura dello stato: la guardia delle sveglie di riserva e la riga del controllo del mattino
    male = []
    banco = os.path.join(TMP, "_orologio")
    os.makedirs(banco, exist_ok=True)
    stato_f = os.path.join(banco, "stato.json")
    sv = [{"flusso": "mattino.yml", "dovuta": "2026-12-07T10:15", "ok": True, "esito": {"stato": "ok", "dettaglio": "GitHub 200"}},
          {"flusso": "dem.yml", "dovuta": "2026-12-06T19:30", "ok": True, "esito": {"stato": "ok", "dettaglio": "GitHub 200"}}]
    dem_ko = [sv[0], dict(sv[1], ok=False, esito={"stato": "errore", "dettaglio": "GitHub risponde 401: Bad credentials"})]
    base = {"sano": False, "segreto": True, "repository": True, "provato": True, "avvio": "2026-12-01T15:00:00Z"}
    # (stato, guardie {flusso: SALTA atteso}, uscita del controllo, frase, prefisso della riga)
    casi = [(dict(base, sano=True, sveglie=sv), {"mattino.yml": "si", "dem.yml": "si", "segnalazioni.yml": "no"}, 0, "partenze puntuali", "OK"),
            (dict(base, sveglie=dem_ko), {"mattino.yml": "si", "dem.yml": "no"}, 1, "401: Bad credentials", "NO"),
            (dict(base, segreto=False, provato=False, avvio=None, sveglie=sv), {"mattino.yml": "no"}, 1, "in attesa del token", "NOTA"),
            (dict(base, segreto=False, sveglie=sv), {"mattino.yml": "no"}, 1, "manca il segreto GITHUB_ACTIONS_TOKEN", "NO"),
            (dict(base, provato=False, sveglie=sv), {"mattino.yml": "no"}, 1, "ancora nessuna partenza riuscita", "NO"),
            (dict(base, sano=True, sveglie=sv, errore="stato non leggibile: D1"), {"mattino.yml": "no"}, 0, "partenze puntuali", "OK"),
            ("non è uno stato", {"mattino.yml": "no"}, 1, "non risponde", "NO"),
            (None, {"mattino.yml": "no"}, 1, "non risponde", "NO")]
    script = os.path.join(R, "sito", "orologio.py")
    for j, guardie, uscita, frase, prefisso in casi:
        if j is None:
            amb = {"GTD_OROLOGIO": os.path.join(banco, "manca.json")}
        else:
            json.dump(j, open(stato_f, "w", encoding="utf-8"))
            amb = {"GTD_OROLOGIO": stato_f}
        for flusso, salta in guardie.items():
            rc, out = esegui([sys.executable, script, "--guardia", flusso], env=amb)
            if rc != 0 or out.strip().splitlines()[0] != "SALTA=" + salta:
                male.append(f"guardia di {flusso}: con {str(j)[:50]} doveva dire SALTA={salta} ({out.strip()[:60]})")
        rc, out = esegui([sys.executable, script], env=amb)
        if rc != uscita or frase not in out or not out.startswith(prefisso):
            male.append(f"controllo: con {str(j)[:40]} doveva uscire {uscita} con '{prefisso} ... {frase}' ({out.strip()[:80]})")
    # il controllo del mattino: in attesa del token una nota, non una riga rossa (niente segnalazione falsa ogni giorno);
    # la riserva di GitHub arrivata tardi controlla lo stesso l'edizione non uscita
    json.dump(dict(base, segreto=False, provato=False, avvio=None, sveglie=sv), open(stato_f, "w", encoding="utf-8"))
    prova = ("import datetime, mattino as m; m.macchina(datetime.date(2026, 12, 7)); "
             "print('NO=' + '|'.join(m.NO)); print('NOTE=' + '|'.join(m.NOTE)); "
             "print('FASCIA=' + ','.join(str(m.in_fascia(o, p)) for o, p in ((10, 'orologio'), (15, 'orologio'), (15, 'schedule'), (22, 'schedule'), (9, 'schedule'), (11, 'workflow_dispatch'))))")
    rc, out = esegui([sys.executable, "-c", prova], cwd=R, env={"GTD_OROLOGIO": stato_f, "GTD_MINUTI": os.path.join(banco, "manca.json")})
    if "NO=\n" not in out + "\n" or "in attesa del token" not in out:
        male.append(f"controllo del mattino: in attesa del token deve essere una nota, non una riga rossa ({out.strip()[-120:]})")
    if "FASCIA=True,False,True,True,False,True" not in out:
        male.append(f"controllo del mattino: la riserva di GitHub in ritardo deve controllare a qualunque ora dalle 10 ({out.strip()[-80:]})")
    json.dump(dict(base, segreto=False, sveglie=sv), open(stato_f, "w", encoding="utf-8"))
    rc, out = esegui([sys.executable, "-c", prova], cwd=R, env={"GTD_OROLOGIO": stato_f, "GTD_MINUTI": os.path.join(banco, "manca.json")})
    if "NO=Orologio dei controlli" not in out:
        male.append("controllo del mattino: segreto visto e poi sparito deve essere una riga rossa")
    esito("Orologio: guardia e controllo del mattino", not male, "; ".join(male)[:400] or
          "ogni riserva guarda solo il suo flusso e lavora a ogni dubbio; in attesa del token una nota, dopo un guasto una riga rossa; la riserva tardiva controlla a qualunque ora dalle 10")

    # la stima dei minuti, con un GitHub finto: arrotondamento, ubuntu-slim a un terzo, job saltati, giri in corso, giri già contati
    male = []
    gh = os.path.join(banco, "github")
    os.makedirs(gh, exist_ok=True)

    def job(nome, inizio, fine, etichetta="ubuntu-24.04", fine_stato="success"):
        return {"name": nome, "started_at": inizio, "completed_at": fine, "conclusion": fine_stato, "labels": [etichetta]}
    json.dump({"workflow_runs": [
        {"id": 1, "path": ".github/workflows/collaudo.yml", "status": "completed"},
        {"id": 2, "path": ".github/workflows/segnalazioni.yml", "status": "completed"},
        {"id": 3, "path": ".github/workflows/mattino.yml", "status": "completed"},
        {"id": 4, "path": ".github/workflows/sito.yml", "status": "in_progress"}]}, open(os.path.join(gh, "runs.json"), "w"))
    json.dump({"jobs": [job("kit", "2026-12-07T10:00:00Z", "2026-12-07T10:04:01Z"), job("sito", "2026-12-07T10:00:00Z", "2026-12-07T10:00:20Z")]}, open(os.path.join(gh, "jobs_1.json"), "w"))
    json.dump({"jobs": [job("avviso", "2026-12-07T10:00:00Z", "2026-12-07T10:00:09Z", "ubuntu-slim")]}, open(os.path.join(gh, "jobs_2.json"), "w"))
    json.dump({"jobs": [job("controllo", "2026-12-07T10:00:00Z", "2026-12-07T10:02:30Z", "ubuntu-slim"), job("gomm", None, None, "ubuntu-slim", "skipped")]}, open(os.path.join(gh, "jobs_3.json"), "w"))
    json.dump({"private": True}, open(os.path.join(gh, "repo.json"), "w"))
    mf = os.path.join(banco, "minuti.json")
    amb = {"GTD_GITHUB": gh, "GTD_MINUTI": mf, "GTD_ADESSO": "2026-12-07T11:00"}
    rc, out = esegui([sys.executable, os.path.join(R, "minuti.py"), "--scrivi"], env=amb)
    try:
        m = json.load(open(mf, encoding="utf-8"))
    except (OSError, ValueError):
        m = {}
    # collaudo: 5 + 1 = 6; segnalazioni: 1/3; mattino: 3/3 = 1; sito in corso: non ancora
    if rc or m.get("minuti") != round(6 + 1 / 3 + 1, 1) or m.get("privato") is not True or set(m.get("giri", {})) != {"1", "2", "3"} or m.get("quota") != 2000:
        male.append(f"stima: attesi 7,3 minuti su 2.000 dai giri 1-3 ({str(m)[:120]}; {out.strip()[:80]})")
    os.remove(os.path.join(gh, "jobs_1.json"))
    rc, out = esegui([sys.executable, os.path.join(R, "minuti.py"), "--scrivi"], env=amb)
    if rc or json.load(open(mf, encoding="utf-8")).get("minuti") != m.get("minuti"):
        male.append("stima: il giorno dopo richiede di nuovo a GitHub i giri già contati")
    import minuti as MIN
    import datetime as _dt
    oggi = _dt.date(2026, 12, 7)
    for caso, atteso in ((dict(m, percentuale=80.0), False), (dict(m, percentuale=74.9), True), (dict(m, percentuale=80.0, privato=False), True),
                         (dict(m, mese="2026-11"), None), ({}, None)):
        if MIN.giudizio(caso, oggi)[0] is not atteso:
            male.append(f"giudizio dei minuti: {str(caso)[:50]} doveva dare {atteso}")
    rc, out = esegui([sys.executable, os.path.join(R, "minuti.py")], env={"GTD_GITHUB": os.path.join(banco, "non-esiste"), "GTD_MINUTI": mf})
    if rc != 0 or "::warning::" not in out:
        male.append("stima: GitHub che non risponde deve dare un avviso, mai un errore")
    esito("Minuti di GitHub: stima e allarme al 75%", not male, "; ".join(male)[:400] or
          "ogni job arrotondato al minuto, ubuntu-slim a un terzo, saltati e in corso esclusi; allarme solo da privato oltre il 75%; i giri contati restano")

    # la mappa: ogni flusso e ogni file dell'orologio stanno in ARCHITETTURA.md
    mappa = open(os.path.join(R, "ARCHITETTURA.md"), encoding="utf-8").read()
    manca = [f for f in sorted(os.listdir(cartella)) if f.endswith(".yml") and f not in mappa]
    manca += [f for f in ("sito/orologio.js", "sito/orologio.py", "minuti.py", "pannello/minuti.json", "GITHUB_ACTIONS_TOKEN", "/api/orologio") if f not in mappa]
    esito("Orologio: mappa in ARCHITETTURA.md", not manca, "mancano: " + ", ".join(manca) if manca else "ogni flusso di GitHub e ogni pezzo dell'orologio è nella mappa")


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
    # pagine.py che cade non ferma la pubblicazione, ma l'avviso deve uscire (prima lo copriva l'esito di awk)
    pg = os.path.join(copia, "redazione", "pagine.py")
    buono = open(pg, encoding="utf-8").read()
    open(pg, "w", encoding="utf-8").write("import sys\nsys.exit('pagine.py rotto apposta dal collaudo')\n")
    try:
        rc, out = esegui(["bash", os.path.join(copia, "redazione", "pubblica.sh"), pdf, str(v["numero"]), v["data"],
                          os.path.join(lav, "fatti.json")], env={"GTD_REPO": copia, "GTD_PROVA": "1"})
    finally:
        open(pg, "w", encoding="utf-8").write(buono)
    ok = rc == 0 and "AVVISO: pagine.py non riuscito" in out and "Sito: PROVA - nessun push" in out
    esito("Pubblicazione: pagine.py che cade", ok, "avviso stampato, la pubblicazione prosegue" if ok else
          ("manca l'avviso" if rc == 0 else "la pubblicazione si è fermata") + ": " +
          ([x for x in out.splitlines() if x.startswith(("Sito:", "AVVISO"))] or ["nessuna riga Sito: né AVVISO"])[-1][:160])


def passo_pubblicazione_ramo(copia):
    """Si pubblica dal ramo principale anche quando la sessione parte senza ramo (un lancio a mano dell'attività: il
    27/11/2026 la #035, pronta e verde, è rimasta fuori così); da un commit fuori dalla linea del ramo principale mai."""
    voci = json.load(open(os.path.join(copia, "edizioni.json"), encoding="utf-8"))
    v = max(voci, key=lambda x: x["numero"])
    base = os.path.join(TMP, "ramo")
    orig, finto, lav = os.path.join(base, "origine.git"), os.path.join(base, "finto"), os.path.join(base, "lavoro")
    os.makedirs(lav)
    shutil.copytree(copia, finto, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", "collaudi", "rete"))
    pdf = os.path.join(lav, "copia.pdf")
    shutil.move(os.path.join(finto, v["file"]), pdf)                # l'edizione di oggi non è ancora nel repository
    fatti = os.path.join(finto, "redazione", "fatti", v["data"] + ".json")
    if os.path.exists(fatti):
        shutil.copy(fatti, os.path.join(lav, "fatti.json"))
    g = lambda *a, dove=finto: esegui(["git", "-c", "user.name=collaudo", "-c", "user.email=collaudo@example.invalid",
                                       "-c", "init.defaultBranch=main", "-c", "advice.detachedHead=false", *a], cwd=dove)
    pubblica = lambda: esegui(["bash", os.path.join(finto, "redazione", "pubblica.sh"), pdf, str(v["numero"]), v["data"],
                               os.path.join(lav, "fatti.json")], env={"GTD_REPO": finto})
    remoto = lambda: g("ls-remote", "origin", "refs/heads/main")[1].split("\t")[0].strip()
    esegui(["git", "-c", "init.defaultBranch=main", "init", "-q", "--bare", orig])
    passi = [g("init", "-q"), g("checkout", "-q", "-B", "main"), g("commit", "-q", "--allow-empty", "-m", "vecchia"),
             g("add", "-A"), g("commit", "-q", "-m", "prima"), g("remote", "add", "origin", orig), g("push", "-q", "origin", "main")]
    if any(rc for rc, _ in passi):
        return esito("Pubblicazione: ramo", False, "repository finto non creato: " + next(o for rc, o in passi if rc).strip()[:120])
    prima = remoto()
    male = []
    # 1. un commit fuori dalla linea del ramo principale, senza ramo: prova forzata, niente sul remoto
    g("checkout", "-q", "--detach"); g("commit", "-q", "--allow-empty", "-m", "fuori linea")
    rc, out = pubblica()
    if rc or "modalità prova forzata" not in out or remoto() != prima:
        male.append("da un commit fuori linea doveva restare in prova (" + (out.strip().splitlines() or ["nessuna uscita"])[-1][:80] + ")")
    g("checkout", "-q", "--", "."); g("clean", "-q", "-fd")
    # 2. senza ramo sul commit del ramo principale, con il main locale rimasto indietro: pubblica davvero
    g("checkout", "-q", "--detach", prima); g("branch", "-q", "-f", "main", prima + "~1")
    rc, out = pubblica()
    testa = g("rev-parse", "HEAD")[1].strip()
    if rc or "PUSH_OK" not in out or "Sito: aggiornato" not in out or remoto() != testa or testa == prima \
            or g("rev-parse", "--abbrev-ref", "HEAD")[1].strip() != "main":
        male.append("senza ramo sul commit del ramo principale doveva pubblicare (" + (out.strip().splitlines() or ["nessuna uscita"])[-1][:100] + ")")
    elif v["file"] not in g("show", "--name-only", "--format=", "HEAD")[1]:
        male.append("il commit pubblicato non contiene il PDF dell'edizione")
    esito("Pubblicazione: ramo (sessione senza ramo)", not male,
          "; ".join(male) or "fuori linea resta in prova; sul commit del ramo principale pubblica, con PUSH_OK verificato sul remoto")


# ---------------------------------------------------------------- 7. i cancelli del rilascio (G-66)
class Banco:
    """Un repository finto con un remoto finto (cartella nuda) in TMP, per provare redazione/rilascia.sh di OGGI senza
    toccare GitHub. Il collaudo dentro il banco è finto (stampa COLLAUDO: OK: il vero è questo); gh è finto e risponde
    con l'esito scritto in self.gh. Sabato sera di default: l'orario non ferma, salvo dove lo si prova."""
    def __init__(self, nome):
        self.base = os.path.join(TMP, "banco_" + nome)
        self.orig, self.rep, self.bin = (os.path.join(self.base, x) for x in ("origine.git", "rep", "bin"))
        self.gh, self.ora, self.log = "success", "6 2000", os.path.join(self.base, "gh.log")
        for d in (self.rep, self.bin):
            os.makedirs(d)
        esegui(["git", "init", "-q", "--bare", "-b", "main", self.orig])
        open(os.path.join(self.bin, "gh"), "w").write('#!/bin/sh\necho "$*" >> "$FINTO_GH_LOG"\n'
                                                       '[ "$FINTO_GH" = rotto ] && { echo "non autenticato" >&2; exit 4; }\n'
                                                       'echo "completed $FINTO_GH 4242"\n')
        os.chmod(os.path.join(self.bin, "gh"), 0o755)
        self.g("init", "-q", "-b", "main")
        self.g("config", "user.name", "collaudo"); self.g("config", "user.email", "collaudo@example.invalid")
        self.g("config", "advice.detachedHead", "false")
        for rel in ("rilascia.sh", "catena.txt", "prova.sh", "sito/costruisci.py"):
            if os.path.exists(os.path.join(R, rel)):
                self.scrivi("redazione/" + rel, open(os.path.join(R, rel), encoding="utf-8").read())
        self.scrivi("redazione/collaudo.py", 'print("COLLAUDO: OK")\n')
        self.scrivi("redazione/STATO.md", "stato\n"); self.scrivi("index.html", "<p>sito</p>\n")
        self.scrivi(".gitignore", "__pycache__/\nredazione/PROVA_DATA\n")
        self.scrivi("redazione/gommberg_engine.py", "# motore finto\n")
        self.g("add", "-A"); self.g("commit", "-q", "-m", "inizio")
        self.g("remote", "add", "origin", self.orig)
        self.g("push", "-q", "origin", "main", "main:rilascio")
        self.inizio = self.remoto("main")

    def g(self, *a):
        return esegui(["git", *a], cwd=self.rep)[1].strip()

    def scrivi(self, rel, testo):
        p = os.path.join(self.rep, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(testo)

    def commit(self, rel, testo, msg):
        self.scrivi(rel, testo); self.g("add", "-A"); self.g("commit", "-q", "-m", msg)
        return self.g("rev-parse", "HEAD")

    def remoto(self, ramo):
        return esegui(["git", "rev-parse", "-q", "--verify", "refs/heads/" + ramo], cwd=self.orig)[1].strip()

    def rilascia(self, *a, prova=False):
        env = {"PATH": self.bin + os.pathsep + os.environ.get("PATH", ""), "GTD_ORA": self.ora, "FINTO_GH": self.gh,
               "FINTO_GH_LOG": self.log}
        if prova:
            env["GTD_PROVA"] = "1"
        try:
            return esegui(["bash", "redazione/rilascia.sh", *a], cwd=self.rep, env=env, timeout=120)
        except subprocess.TimeoutExpired:
            return 124, "rilascia.sh " + " ".join(a) + ": nessuna risposta in 120 secondi"


def ultima(out):
    return (out.strip().splitlines() or ["nessuna uscita"])[-1][:140]


def rilascio_avanti():
    """1. pubblica fermata dal collaudo di GitHub: su GitHub il ramo rilascio resta com'era (non avanti al ramo
    principale), il ramo principale non si tocca, GitHub ha collaudato proprio quell'albero; verde: pubblica e riallinea."""
    b, male = Banco("avanti"), []
    b.g("checkout", "-q", "-B", "rilascio", "origin/rilascio")
    lavoro = b.commit("redazione/STATO.md", "stato nuovo\n", "G-00: lavoro")
    b.gh = "failure"
    rc, out = b.rilascia("pubblica")
    if rc == 0 or "RILASCIO: FERMO" not in out:
        male.append("con GitHub rosso doveva fermarsi (" + ultima(out) + ")")
    if b.remoto("rilascio") != b.inizio or b.remoto("main") != b.inizio:
        male.append("fermo dopo il push: su GitHub il ramo rilascio è andato avanti al ramo principale")
    cancello = b.remoto("cancello")
    if b.g("rev-parse", cancello + "^{tree}") != b.g("rev-parse", "HEAD^{tree}") or cancello not in open(b.log).read():
        male.append("GitHub non ha collaudato l'albero del rilascio (ramo cancello)")
    b.gh = "success"
    rc, out = b.rilascia("pubblica")
    princ = b.remoto("main")
    if rc or princ == b.inizio or b.g("rev-parse", princ + "^{tree}") != b.g("rev-parse", lavoro + "^{tree}"):
        male.append("con GitHub verde doveva pubblicare l'albero collaudato (" + ultima(out) + ")")
    elif b.remoto("rilascio") != princ:
        male.append("dopo il push sul ramo principale il ramo rilascio non è stato riallineato")
    esito("Rilascio: pubblica non lascia rilascio avanti al ramo principale", not male, "; ".join(male) or
          "GitHub rosso: rilascio e main fermi, collaudato l'albero sul ramo cancello; verde: un merge e rilascio = main")


def avvia_sporco():
    """2. avvia rifiuta un ramo rilascio con lavoro che il ramo principale non ha; --ripulisci lo riporta uguale al
    ramo principale senza forzare; con-prova, che il lavoro lo porta apposta, si avvia."""
    b, male = Banco("avvia"), []
    b.g("checkout", "-q", "-B", "rilascio", "origin/rilascio")
    b.commit("redazione/gommberg_engine.py", "# lavoro rimasto\n", "G-00: rimasto")
    b.g("push", "-q", "origin", "rilascio")
    b.g("checkout", "-q", "-B", "con-prova", "origin/main"); b.commit("redazione/STATO.md", "attesa\n", "G-01: attesa")
    b.g("push", "-q", "origin", "con-prova"); b.g("checkout", "-q", "main")
    sporco = b.remoto("rilascio")
    rc, out = b.rilascia("avvia")
    if rc == 0 or "RILASCIO: FERMO" not in out or "--ripulisci" not in out or b.remoto("rilascio") != sporco:
        male.append("doveva fermarsi su un rilascio con lavoro non in linea (" + ultima(out) + ")")
    b.g("checkout", "-q", "main")
    rc, out = b.rilascia("avvia", "--ripulisci")
    pulito = b.remoto("rilascio")
    if rc or b.g("rev-parse", pulito + "^{tree}") != b.g("rev-parse", "origin/main^{tree}"):
        male.append("--ripulisci doveva riportare rilascio uguale al ramo principale (" + ultima(out) + ")")
    elif esegui(["git", "merge-base", "--is-ancestor", sporco, pulito], cwd=b.rep)[0]:
        male.append("--ripulisci ha riscritto la storia di rilascio (push forzato)")
    rc, out = b.rilascia("avvia", "con-prova")
    if rc:
        male.append("con-prova porta lavoro apposta e doveva avviarsi (" + ultima(out) + ")")
    # un pubblica fermato dopo aver unito il commit: rilascio locale avanti, mai da spingere
    b.g("checkout", "-q", "-B", "rilascio", "origin/rilascio"); b.commit("redazione/STATO.md", "unito\n", "G-04: unito in locale")
    su_github = b.remoto("rilascio")
    rc, out = b.rilascia("avvia")
    if rc == 0 or "--ripulisci" not in out or "git push" in out or b.remoto("rilascio") != su_github:
        male.append("con commit solo locali su rilascio doveva fermarsi proponendo --ripulisci, mai il push (" + ultima(out) + ")")
    rc, out = b.rilascia("avvia", "--ripulisci")
    if rc or b.g("rev-parse", "rilascio^{tree}") != b.g("rev-parse", "origin/main^{tree}") or "G-04" in b.g("log", "--format=%s", "origin/rilascio"):
        male.append("--ripulisci doveva ripartire dal rilascio di GitHub senza spingere i commit locali (" + ultima(out) + ")")
    esito("Rilascio: avvia rifiuta un rilascio sporco", not male, "; ".join(male) or
          "rilascio con lavoro non in linea fermato; --ripulisci lo riporta uguale a main senza forzare; con-prova si avvia; "
          "commit solo locali: propone --ripulisci, mai il push")


def annulla_cancelli():
    """3. annulla: mai nella fascia dell'uscita (lun-ven 8:30-10:30 di Roma), mai due volte lo stesso rilascio; dopo,
    il ramo rilascio torna uguale al ramo principale. Un'edizione uscita dopo il rilascio resta."""
    b, male = Banco("annulla"), []
    b.g("checkout", "-q", "-B", "rilascio", "origin/rilascio")
    b.commit("redazione/STATO.md", "rilasciato\n", "G-00: da togliere")
    rc, out = b.rilascia("pubblica")
    if rc:
        return esito("Rilascio: annulla", False, "il rilascio da annullare non è partito: " + ultima(out))
    b.g("checkout", "-q", "-B", "main", "origin/main"); b.commit("edizione.txt", "#036\n", "Edizione #036 - 2026-11-30")
    b.g("push", "-q", "origin", "main"); b.g("checkout", "-q", "rilascio")
    prima = b.remoto("main")
    b.ora = "1 0915"
    rc, out = b.rilascia("annulla")
    if rc == 0 or "RILASCIO: FERMO" not in out or b.remoto("main") != prima:
        male.append("lunedì alle 9:15 doveva fermarsi senza toccare il ramo principale (" + ultima(out) + ")")
    b.ora = "6 2000"
    rc, out = b.rilascia("annulla")
    dopo = b.remoto("main")
    if rc or dopo == prima or b.g("show", dopo + ":redazione/STATO.md") != "stato" or "#036" not in b.g("show", dopo + ":edizione.txt"):
        male.append("di sabato doveva togliere il rilascio e lasciare l'edizione (" + ultima(out) + ")")
    elif b.remoto("rilascio") != dopo or b.g("rev-parse", "rilascio") != dopo:
        male.append("dopo l'annullamento il ramo rilascio non è tornato uguale al ramo principale")
    rc, out = b.rilascia("annulla")
    if rc == 0 or "già annullato" not in out or b.remoto("main") != dopo:
        male.append("un secondo annullamento di fila doveva fermarsi (" + ultima(out) + ")")
    esito("Rilascio: annulla", not male, "; ".join(male) or
          "fermo nella fascia dell'uscita; toglie il rilascio e lascia l'edizione; rilascio = main; il secondo di fila si ferma")


def leggi_catena(testo):
    """Le regole di redazione/catena.txt come le legge rilascia.sh: {tipo: [espressioni]}."""
    reg = {}
    for riga in testo.splitlines():
        p = riga.split()
        if len(p) >= 2 and p[0] in ("catena", "prova", "fuori"):
            reg.setdefault(p[0], []).append(p[1])
    return reg


def in_catena(reg, f, tipi=("catena", "prova")):
    return any(re.search(x, f) for t in tipi for x in reg.get(t, [])) and not any(re.search(x, f) for x in reg.get("fuori", []))


def catena_livello():
    """4. La catena in un file solo, che copre motore, controlli, pubblicazione, newsletter, flussi di GitHub e i
    cancelli stessi; pubblica rifiuta da sé un rilascio che la tocca senza l'Ok di Paolo."""
    male = []
    p = os.path.join(R, "catena.txt")
    reg = leggi_catena(open(p, encoding="utf-8").read()) if os.path.exists(p) else {}
    dentro = ["redazione/gommberg_engine.py", "redazione/controlli_testo.py", "redazione/pubblica.sh", "redazione/newsletter.py",
              "redazione/newsletter_cornice.html", "redazione/rilascia.sh", "redazione/collaudo.py", "redazione/prova.sh",
              "redazione/catena.txt", "redazione/rete/x/atteso/pdf.txt", "redazione/registro/CAPO.md", "redazione/ATTIVITA.md",
              "redazione/ISTRUZIONI.md", ".github/workflows/sito.yml", ".github/workflows/collaudo.yml", ".claude/settings.json",
              "edizioni.json", "dati/recenti.json", "pannello/registro.json"]
    dentro += [os.path.relpath(f, REPO) for f in glob.glob(os.path.join(R, "**", "*.py"), recursive=True) + glob.glob(os.path.join(R, "*.sh"))]
    fuori = ["redazione/STATO.md", "redazione/PROGETTO.md", "redazione/AZIONI.md", "redazione/collaudi/2026-11-27/g66/a.png", "index.html"]
    male += ["fuori dalla catena: " + f for f in sorted(set(dentro)) if not in_catena(reg, f) and not f.startswith("redazione/collaudi/")][:5]
    male += ["nella catena per sbaglio: " + f for f in fuori if in_catena(reg, f)]
    male += ["non vuole la prova: " + f for f in ("redazione/ISTRUZIONI.md", "redazione/controlli_testo.py", "redazione/glossario.json")
             if not in_catena(reg, f, ("prova",))]
    male += ["nascosto fuori dalla catena: " + f for f in (".gitignore", ".mcp.json", ".claude/agents/x.md", ".nojekyll", ".github/dependabot.yml")
             if not in_catena(reg, f)]
    # rilascia.sh le legge con grep -E: una regola che solo Python capisce lo farebbe sbagliare in silenzio
    for t in reg.values():
        for x in t:
            # grep -E esce con 2, oppure sintassi solo di Python ((?..), \d, \s, \w) che grep legge in un altro modo
            if subprocess.run(["grep", "-qE", "--", x], input="x", capture_output=True, text=True).returncode == 2 \
                    or re.search(r"\(\?|\\[dswb]", x):
                male.append("regola non valida per grep -E: " + x)
    b = Banco("catena")
    b.g("checkout", "-q", "-B", "rilascio", "origin/rilascio")
    approvato = b.commit("redazione/gommberg_engine.py", "# motore cambiato\n", "G-00: motore")
    rc, out = b.rilascia("pubblica")
    if rc == 0 or "catena" not in out.splitlines()[-1] or b.remoto("main") != b.inizio:
        male.append("un rilascio del motore senza Ok doveva fermarsi (" + ultima(out) + ")")
    rc, out = b.rilascia("pubblica", "--commit", approvato)
    if rc or b.remoto("main") == b.inizio:
        male.append("con l'Ok doveva pubblicare (" + ultima(out) + ")")
    # senza Ok: un rinomino fuori dalla catena, un file nascosto, un file pubblico con _ in una sottocartella
    for nome, fai in (("rinomino di ISTRUZIONI.md in collaudi/", lambda: (b.g("mv", "redazione/ISTRUZIONI.md", "redazione/collaudi/ISTRUZIONI.md"), b.g("commit", "-q", "-m", "G-00: sposta"))),
                      (".gitignore", lambda: b.commit(".gitignore", "__pycache__/\nredazione/PROVA_DATA\npdf/\n", "G-00: ignora")),
                      ("assets/_x.js (pubblico per costruisci.py)", lambda: b.commit("assets/_x.js", "x\n", "G-00: script"))):
        b.g("checkout", "-q", "-B", "main", "origin/main")
        if nome.startswith("rinomino"):
            b.commit("redazione/ISTRUZIONI.md", "regole\n", "regole"); b.g("push", "-q", "origin", "main")
        b.g("checkout", "-q", "-B", "rilascio", "origin/main"); prima = b.remoto("main")
        fai()
        rc, out = b.rilascia("pubblica")
        if rc == 0 or b.remoto("main") != prima:
            male.append(f"{nome} senza Ok doveva fermarsi (" + ultima(out) + ")")
    # una regola che grep non capisce sul ramo principale: si ferma, non passa con la catena vuota
    b.g("checkout", "-q", "-B", "main", "origin/main")
    b.commit("redazione/catena.txt", open(os.path.join(b.rep, "redazione/catena.txt")).read() + "catena [[:foo:]]\n", "catena rotta")
    b.g("push", "-q", "origin", "main"); b.g("checkout", "-q", "-B", "rilascio", "origin/main"); prima = b.remoto("main")
    b.commit("redazione/gommberg_engine.py", "# motore di nuovo\n", "G-00: motore")
    rc, out = b.rilascia("pubblica")
    if rc == 0 or "regola non valida" not in out or b.remoto("main") != prima:
        male.append("con una regola non valida in catena.txt doveva fermarsi (" + ultima(out) + ")")
    esito("Rilascio: la catena in un file e il cancello dell'Ok", not male, "; ".join(male) or
          f"catena.txt copre {len(set(dentro))} file del kit, i cancelli e i file nascosti, non i file di stato, regole valide per grep; "
          "senza Ok si fermano motore, rinomino fuori dalla catena, .gitignore, assets/_x.js; regola non valida: fermo")


def commit_approvato():
    """5. pubblica --commit: unisce da sé il commit approvato e pubblica esattamente il ramo principale più quello; con
    lavoro non approvato accanto si ferma senza toccare il ramo principale."""
    b, male = Banco("commit"), []
    b.g("checkout", "-q", "-B", "g01", "origin/main")
    approvato = b.commit("redazione/gommberg_engine.py", "# motore approvato\n", "G-01: motore")
    b.g("checkout", "-q", "-B", "rilascio", "origin/rilascio")
    b.g("merge", "-q", "--no-ff", "--no-edit", approvato)
    b.commit("redazione/newsletter.py", "# mai approvato\n", "G-02: di passaggio")
    rc, out = b.rilascia("pubblica", "--commit", approvato[:10])
    if rc == 0 or "esattamente" not in out or b.remoto("main") != b.inizio:
        male.append("con lavoro non approvato accanto doveva fermarsi (" + ultima(out) + ")")
    b.g("reset", "-q", "--hard", "origin/rilascio")
    rc, out = b.rilascia("pubblica", "--commit", approvato[:10])
    princ = b.remoto("main")
    atteso = esegui(["git", "merge-tree", "--write-tree", b.inizio, approvato], cwd=b.rep)[1].split()[0]
    if rc or princ == b.inizio or b.g("rev-parse", princ + "^{tree}") != atteso:
        male.append("da rilascio pulito doveva unire e pubblicare esattamente il commit approvato (" + ultima(out) + ")")
    elif approvato not in b.g("log", "-1", "--format=%B", princ):
        male.append("il merge non nomina il commit approvato")
    esito("Rilascio: pubblica --commit, esattamente il commit approvato", not male, "; ".join(male) or
          "con un commit non approvato accanto si ferma; da rilascio pulito unisce e pubblica main più il commit, e lo nomina")


def prova_automatica():
    """6. prova.sh lanciabile da una sessione: avvio prende da solo il ramo da GitHub, e il ramo prova dice in JSON
    l'esito e il commit provato (in corso, poi chiusa)."""
    b, male = Banco("prova"), []
    lav, link = os.path.join(b.base, "lavoro"), os.path.join(b.base, "gtd")
    b.g("checkout", "-q", "-B", "con-prova", "origin/main")
    provato = b.commit("redazione/ISTRUZIONI.md", "regole nuove\n", "G-03: regole")
    b.g("push", "-q", "origin", "con-prova"); b.g("checkout", "-q", "-B", "con-prova", "origin/main"); b.g("checkout", "-q", "main")
    prova = lambda *a: esegui(["bash", "redazione/prova.sh", *a], cwd=b.rep, env={"GTD_LAVORO": lav, "GTD_LINK": link}, timeout=60)
    def leggi():
        rc, out = prova("esito")
        try:
            return rc, json.loads(out)
        except Exception:  # noqa: BLE001
            return rc, {"uscita": out.strip()[-120:]}
    b.g("checkout", "-q", "con-prova"); locale = b.commit("redazione/STATO.md", "locale\n", "lavoro locale")
    rc, out = prova("avvio", "30/11", "--ramo", "con-prova")
    if rc == 0 or b.g("rev-parse", "con-prova") != locale:
        male.append("un avvio con argomenti sbagliati doveva fermarsi prima di toccare il ramo (" + ultima(out) + ")")
    b.g("checkout", "-q", "main")
    rc, out = prova("avvio", "2026-11-30", "--ramo", "con-prova")
    if rc or b.g("rev-parse", "--abbrev-ref", "HEAD") != "con-prova":
        male.append("avvio --ramo doveva prendere il ramo da GitHub (" + ultima(out) + ")")
    rc, e = leggi()
    if rc != 2 or e.get("esito") != "in-corso" or e.get("commit") != provato:
        male.append(f"a prova avviata l'esito doveva dire in-corso sul commit provato ({e})")
    pdf = os.path.join(b.base, "prova.pdf"); open(pdf, "w").write("%PDF finto")
    rc, out = prova("chiudi", pdf)
    rc2, e = leggi()
    if rc or rc2 != 0 or e.get("esito") != "chiusa" or e.get("commit") != provato or e.get("data") != "2026-11-30" or "prova.pdf" not in e.get("file", []):
        male.append(f"a prova chiusa l'esito doveva dire chiusa, con data, commit provato e PDF ({ultima(out)}; {e})")
    # dopo la prova: unisci e pubblica --dopo-la-prova sul commit provato (lo script legge prova.sh esito)
    b.g("checkout", "-q", "-B", "rilascio", "origin/rilascio")
    rc, out = b.rilascia("unisci", provato)
    rc2, out2 = b.rilascia("pubblica", "--commit", provato, "--dopo-la-prova")
    if rc or rc2 or b.remoto("main") == b.inizio:
        male.append("dopo la prova chiusa sul commit provato, pubblica --dopo-la-prova doveva pubblicare (" + ultima(out + out2) + ")")
    esito("Prova automatica: prova.sh da una sessione", not male, "; ".join(male) or
          "argomenti sbagliati non toccano il ramo; avvio --ramo lo prende da sé; prova.sh esito dice in JSON in-corso e poi "
          "chiusa, con il commit provato; pubblica --dopo-la-prova su quel commit pubblica")


def anteprima_chrome(copia):
    """7. L'anteprima in uno script: serve il sito in locale, Chrome (qui finto: scarica la pagina servita e la salva come
    immagine) in due larghezze, immagini in redazione/collaudi/AAAA-MM-GG/g<NN>/; senza Chrome si ferma."""
    male, base = [], os.path.join(TMP, "anteprima")
    os.makedirs(base)
    finto = os.path.join(base, "chrome")
    open(finto, "w").write("#!/usr/bin/env python3\nimport sys, urllib.request\n"
                           "out = [a.split('=', 1)[1] for a in sys.argv if a.startswith('--screenshot=')][0]\n"
                           "w = [a.split('=', 1)[1] for a in sys.argv if a.startswith('--window-size=')][0]\n"
                           "open(out, 'wb').write(w.encode() + b' ' + urllib.request.urlopen(sys.argv[-1]).read())\n")
    os.chmod(finto, 0o755)
    script = os.path.join(copia, "redazione", "anteprima_chrome.sh")
    rc, out = esegui(["bash", script, "g00", "index.html", "--sito", copia], env={"GTD_CHROME": finto}, timeout=120) \
        if os.path.exists(script) else (1, "manca redazione/anteprima_chrome.sh")
    oggi = subprocess.run(["date", "+%F"], env=dict(os.environ, TZ="Europe/Rome"), capture_output=True, text=True).stdout.strip()
    d = os.path.join(copia, "redazione", "collaudi", oggi, "g00")
    pagina = open(os.path.join(copia, "index.html"), "rb").read()
    for w in ("1280", "390"):
        f = os.path.join(d, f"index-{w}.png")
        if rc or not os.path.exists(f) or open(f, "rb").read() != f"{w},2400 ".encode() + pagina:
            male.append(f"immagine a {w} non salvata dalla pagina servita (" + ultima(out) + ")")
            break
    rc, out = esegui(["bash", script, "g00", "--sito", copia], env={"GTD_CHROME": os.path.join(base, "manca")}, timeout=60)
    if rc == 0 or "ANTEPRIMA: FERMO" not in out:
        male.append("senza Chrome doveva fermarsi (" + ultima(out) + ")")
    shutil.rmtree(d, ignore_errors=True)
    esito("Anteprima con Chrome in uno script", not male, "; ".join(male) or
          "sito servito in locale, due larghezze in redazione/collaudi/<data>/g<NN>/; senza Chrome si ferma")


def rientro_e_messaggi():
    """Dopo annulla la voce rientra così: sul ramo della voce, da main nuovo, revert dell'annullamento più correzione,
    un Ok nuovo, pubblica --commit. E i messaggi che dicono che cosa fare: --ok-di-paolo vecchio, gh rotto (subito, non
    dopo 20 minuti), rosso di GitHub (gh run rerun), --dopo-la-prova senza una prova chiusa su quel commit."""
    b, male = Banco("rientro"), []
    b.g("checkout", "-q", "-B", "g01", "origin/main")
    a = b.commit("redazione/gommberg_engine.py", "# motore con un errore\n", "G-01: motore")
    b.g("checkout", "-q", "-B", "rilascio", "origin/rilascio")
    rc, out = b.rilascia("pubblica", "--ok-di-paolo")
    if rc == 0 or "--commit" not in out.splitlines()[-1]:
        male.append("--ok-di-paolo doveva dire di usare --commit (" + ultima(out) + ")")
    b.gh = "rotto"
    rc, out = b.rilascia("pubblica", "--commit", a)
    if rc == 0 or "gh non risponde" not in out or b.remoto("main") != b.inizio:
        male.append("con gh rotto doveva fermarsi subito con la causa (" + ultima(out) + ")")
    b.g("checkout", "-q", "-B", "rilascio", "origin/rilascio"); b.gh = "failure"
    rc, out = b.rilascia("pubblica", "--commit", a)
    if rc == 0 or "gh run rerun 4242" not in out:
        male.append("con GitHub rosso doveva suggerire gh run rerun (" + ultima(out) + ")")
    b.g("checkout", "-q", "-B", "rilascio", "origin/rilascio"); b.gh = "success"
    rc, out = esegui(["bash", "redazione/rilascia.sh", "pubblica", "--commit", a], cwd=b.rep,
                     env={"TZDIR": os.path.join(b.base, "nessun_fuso"), "PATH": b.bin + os.pathsep + os.environ.get("PATH", ""),
                          "FINTO_GH": "success", "FINTO_GH_LOG": b.log})
    if rc == 0 or "fuso" not in out or b.remoto("main") != b.inizio:
        male.append("senza il fuso di Roma doveva fermarsi (" + ultima(out) + ")")
    rc, out = b.rilascia("pubblica", "--commit", a, "--dopo-la-prova")
    if rc == 0 or "prova" not in out.splitlines()[-1] or b.remoto("main") != b.inizio:
        male.append("--dopo-la-prova senza una prova chiusa su quel commit doveva fermarsi (" + ultima(out) + ")")
    b.g("checkout", "-q", "-B", "rilascio", "origin/rilascio")
    rc, out = b.rilascia("pubblica", "--commit", a)
    rc2, out2 = b.rilascia("annulla")
    if rc or rc2:
        return esito("Rilascio: rientro dopo annulla e messaggi", False, "; ".join(male + ["rilascio o annullamento non riusciti: " + ultima(out + out2)]))
    annullamento = b.remoto("main")
    b.g("fetch", "-q", "origin")
    b.g("checkout", "-q", "-B", "g01", "origin/main"); b.g("revert", "--no-edit", annullamento)
    nuovo = b.commit("redazione/gommberg_engine.py", "# motore corretto\n", "G-01: correzione")
    rc, out = b.rilascia("avvia")
    rc2, out2 = b.rilascia("pubblica", "--commit", nuovo)
    princ = b.remoto("main")
    if rc or rc2 or princ == annullamento or b.g("show", princ + ":redazione/gommberg_engine.py") != "# motore corretto":
        male.append("la voce riproposta (revert dell'annullamento più correzione, Ok nuovo) doveva rientrare (" + ultima(out + out2) + ")")
    esito("Rilascio: rientro dopo annulla e messaggi", not male, "; ".join(male) or
          "--ok-di-paolo indica --commit; senza fuso di Roma fermo; gh rotto ferma subito; rosso: gh run rerun; --dopo-la-prova vuole la prova chiusa; "
          "dopo annulla la voce rientra con revert dell'annullamento, correzione e --commit")


def collaudo_github_cancello():
    """8. Il collaudo di GitHub solo come cancello finale (G-12, leva 2): collaudo.yml parte solo dal ramo su cui
    rilascia.sh pubblica porta il rilascio, e pubblica aspetta proprio quel flusso sullo stesso commit."""
    male = []
    flusso = open(os.path.join(REPO, ".github", "workflows", "collaudo.yml"), encoding="utf-8").read()
    script = open(os.path.join(R, "rilascia.sh"), encoding="utf-8").read()
    m = re.search(r'CANCELLO="([^"]+)"', script)
    rami = re.search(r"\n  push:\s*\n\s*branches:\s*\[([^\]]*)\]", flusso)
    rami = [x.strip().strip("'\"") for x in rami.group(1).split(",")] if rami else []
    if not m or rami != [m.group(1)]:
        male.append(f"collaudo.yml deve partire solo dal ramo del cancello ({m.group(1) if m else '?'}), parte da {rami}")
    if "pull_request" in flusso or "schedule:" in flusso:
        male.append("collaudo.yml ha altri inneschi oltre al cancello e al lancio a mano")
    if "gh run list --workflow collaudo.yml --commit" not in script:
        male.append("pubblica non aspetta più collaudo.yml sullo stesso commit (cancello 5)")
    esito("Rilascio: il collaudo di GitHub solo come cancello finale", not male, "; ".join(male) or
          "collaudo.yml parte solo dal ramo cancello (e a mano); pubblica lo aspetta sullo stesso commit")


def passo_rilascio():
    rilascio_avanti()
    avvia_sporco()
    annulla_cancelli()
    catena_livello()
    commit_approvato()
    prova_automatica()
    collaudo_github_cancello()
    rientro_e_messaggi()


def main():
    if "--campione" in sys.argv:
        try:
            return nuovo_campione(sys.argv[sys.argv.index("--campione") + 1])
        finally:
            shutil.rmtree(TMP, ignore_errors=True)
    try:
        passo_sintassi()
        passo_avvio()
        passo_uscite()
        passo_modello()
        passo_scrittura()
        passo_fonti()
        passo_dati()
        passo_tabelle()
        passo_scommessa()
        passo_newsletter()
        passo_benvenuto()
        passo_dem()
        passo_rete()
        passo_pannello()
        passo_orologio()
        passo_rilascio()
        copia = passo_sito()
        if isinstance(copia, str):
            passo_analisi(copia)
            passo_grafici(copia)
            passo_lettori(copia)
            anteprima_chrome(copia)
            passo_pubblicazione_ramo(copia)
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
