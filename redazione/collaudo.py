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
     Coerenza      il testo contro dati.json (controlli_coerenza.py) e il desk (desk.py) su frasi vere della prova del 23/11 e
                   delle #031-#032: cifre che cambiano soggetto, versi contrari, rimandi vuoti, ipotesi nei titoli, ragionamento.
     Fonti         la regola dei fatti (autori.py, applicata da controlli_fatti.py) su schede costruite apposta: la
                   primaria basta, un'agenzia ripresa da tre siti è un autore solo, l'ultima scelta va dichiarata; e il
                   gancio (gancio_token.py) su una trascrizione costruita: ricerche, pagine aperte, pagine non raggiunte.
     Dati          controlli_dati.py sull'Euro Stoxx 50 scritto in otto modi: EODHD sempre tra le due fonti, quotazioni
                   dei riquadri e fonti discordi fermate (APP_DATI §2b e §6); Kospi e Hang Seng da EODHD, anche il
                   giorno dopo una festa di quella borsa (il livello ricavato parte dall'ultima seduta vera, mai da
                   una base non certa: EODHD in ritardo, righe a indice fermo, date future fermate).
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
                   rigenerano nello stesso commit); costruisci.py prepara il sito pubblico senza avvisi; Impara cresce
                   con le edizioni (impara.py su casi costruiti: una volta sola aspetta, due volte è pronta ma entra solo
                   confermata a mano, la frase del giorno resta fuori, la scheda scritta a mano vince, fuori vale per
                   ogni nome, i doppioni si segnalano, un ingresso rotto ferma il passaggio e lascia dati/parole.json com'era);
                   le pagine
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


def controlli(lav, pdf, n, extra=(), senza_indice=True, repo=None, env_extra=None):
    repo = repo or REPO
    env = {"GTD_REPO": repo, "GTD_LAVORO": lav, **(env_extra or {})}
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
    # Promemoria di dicembre (G-50): scatta finché FESTIVI_FINO non copre l'anno dopo, tace quando lo copre
    anno = int(G.FESTIVI_FINO[:4]) if G.FESTIVI_FINO else 0
    if not anno:
        male.append("FESTIVI_FINO mancante o illeggibile in gommberg_engine.py: il promemoria di dicembre non sa fin dove arriva l'elenco")
    for nome, anno_g, deve in ((("dicembre scoperto", anno, True), ("dicembre coperto", anno - 1, False)) if anno else ()):
        giorno = next(dt.date(anno_g, 12, k) for k in range(1, 20) if G.uscita(dt.date(anno_g, 12, k)))
        rc, out = esegui(["bash", os.path.join(R, "prepara.sh"), giorno.isoformat()],
                         env={"GTD_REPO": REPO, "GTD_LAVORO": os.path.join(TMP, "avvio")})
        if rc or ("DICEMBRE:" in out) != deve or len(out.splitlines()) > 23:
            male.append(f"{nome} {giorno}: promemoria {'assente' if deve else 'di troppo'} o uscita sbagliata")
    esito("Avvio (prepara.sh)", not male, "; ".join(male) or f"lunedì {lun:%d/%m}, {mar:%d/%m}, chiuso {chiuso:%d/%m}, "
                                                          f"promemoria di dicembre (festivi verificati fino al {G.FESTIVI_FINO})")


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
INDIPENDENTI = ["PDF e indice", "Numeri contro dati.json", "Scrittura", "Temi di prima pagina", "Coerenza", "Ripetizioni", "Anteprima"]


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


# ---------------------------------------------------------------- 3a-bis. il testo regge contro i dati (G-45)
# Il desk: una cifra resta sul suo soggetto. La prima di DESK_NO è la riscrittura vera della prova del 23/11 (con l'Hang
# Seng a -1,9%); poi i rifiuti persi con e9391e8 (preposizione dentro il soggetto, soggetto doppio), la cifra prima del
# soggetto o dopo i due punti, gli scambi e i casi scritti il 25/11 prima di provare la regola. In DESK_PASSA riordini e
# riscritture nominali buone, tra cui l'oro della #032 e "il rimbalzo dell'oro" -> "l'oro rimbalza". Scoperti, perché la
# regola guarda la testa del soggetto, i nomi propri e la proposizione, non i complementi in nomi comuni: "le vendite di
# auto elettriche (+25%)" -> "le vendite di auto salgono del 25%" (un aggettivo che sparisce dopo un complemento),
# "-0,8% per l'euro contro lo yen" -> "l'euro perde lo 0,8% contro il dollaro" (un complemento in minuscolo cambiato).
DESK_NO = [
    ("Nuove strette USA sulla tecnologia per la Cina fanno scendere il listino tecnologico di Hong Kong (-3,8%)",
     "Hong Kong perde il 3,8% per le strette USA sulla tecnologia per la Cina"),
    ("Il listino tecnologico di Hong Kong (-3,8%) guida i ribassi.", "Il listino di Hong Kong perde il 3,8% e guida i ribassi."),
    ("Il listino tecnologico di Hong Kong (-3,8%) guida i ribassi in Asia.", "Hong Kong, con il suo listino tecnologico, perde il 3,8%."),
    ("L'Hang Seng perde l'1,9% e il listino tecnologico di Hong Kong il 3,8%.", "Hong Kong perde il 3,8% e l'Hang Seng l'1,9%."),
    ("-3,8% per il listino tecnologico di Hong Kong, il calo peggiore da aprile.", "Hong Kong perde il 3,8%, il calo peggiore da aprile."),
    ("In Asia il peggiore è il listino tecnologico di Hong Kong: -3,8%.", "In Asia il peggiore è Hong Kong: -3,8%."),
    ("Il listino tecnologico di Hong Kong, che perde il 3,8%, guida i ribassi.", "Hong Kong, che perde il 3,8%, guida i ribassi in Asia."),
    ("Le banche nel listino di Milano perdono il 2,4% sui timori per gli extraprofitti.",
     "Il listino di Milano perde il 2,4% sui timori per gli extraprofitti."),
    ("Le banche nel listino di Milano perdono il 2,4%.", "Milano, con le banche, perde il 2,4%."),
    ("I titoli dei semiconduttori nel Nasdaq (-4,2%) trascinano giù il listino.", "Il Nasdaq perde il 4,2% trascinato dai semiconduttori."),
    ("Le small cap sul listino americano (-2,7%) soffrono i tassi alti.", "Il listino americano perde il 2,7% sui tassi alti."),
    ("Il rame e l'argento salgono del 2% sulla domanda cinese.", "L'argento sale del 2% sulla domanda cinese."),
    ("Il rame e l'argento salgono del 2%.", "Salgono del 2% l'argento e l'oro."),
    ("Il rendimento del decennale americano sale al 4,2% dopo i dati.", "Il rendimento del Bund sale al 4,2% dopo i dati."),
    ("L'oro guadagna il 2,1% e l'argento il 3,4%.", "L'argento guadagna il 2,1% e l'oro il 3,4%."),
    ("Il petrolio WTI cede il 2,3% e il Brent l'1,1%.", "Il Brent cede il 2,3% e il WTI l'1,1%."),
    ("Il decennale italiano sale al 3,6% mentre il Bund resta al 2,6%.", "Il Bund sale al 3,6% mentre il decennale italiano resta al 2,6%."),
    ("Il decennale americano, dopo i dati sull'inflazione, sale al 4,2%.", "Il Bund, dopo i dati sull'inflazione americana, sale al 4,2%."),
    ("Le azioni del lusso nella Borsa di Parigi perdono il 3%.", "La Borsa di Parigi perde il 3%."),
    ("Il comparto bancario di Milano (+2,3%) festeggia i conti.", "Milano sale del 2,3% sui conti delle banche."),
    ("Le auto tedesche a Francoforte cedono il 4%.", "Francoforte cede il 4%."),
    ("L'oro sale dell'1,2% e il platino del 3%.", "Il platino sale dell'1,2% e l'oro del 3%."),
    ("-5,1% per le azioni di Kering, la peggiore del listino.", "Il listino perde il 5,1%, Kering la peggiore."),
    ("Il Nasdaq 100 perde il 2,9% e lo S&P 500 l'1,6%.", "Lo S&P 500 perde il 2,9% e il Nasdaq 100 l'1,6%."),
    ("I titoli dei servizi pubblici nell'Euro Stoxx (+1,1%) reggono.", "L'Euro Stoxx sale dell'1,1%."),
    ("Il decennale greco scende al 3,1%.", "Il decennale scende al 3,1%."),
    ("Il fatturato di Stellantis in Europa cala del 7%.", "Stellantis cala del 7% in Europa."),
    ("Lo yen guadagna lo 0,8% sul dollaro e l'euro lo 0,3%.", "L'euro guadagna lo 0,8% sul dollaro e lo yen lo 0,3%."),
    ("Il rame e il nichel salgono del 3% a Londra.", "Il nichel sale del 3% a Londra."),
    ("Samsung perde il 7% e SK hynix quasi il 6%.", "SK hynix perde il 7% e Samsung quasi il 6%."),
    ("Gli utili delle banche italiane (+18%) battono le attese.", "Le banche italiane guadagnano il 18% e battono le attese."),
    ("Nel trimestre i ricavi di Nvidia salgono del 62%.", "Nel trimestre Nvidia sale del 62%."),
    ("Il listino dei titoli tecnologici di Taiwan: -2,8%.", "Taiwan: -2,8%."),
    ("-1,4% per il Bund a 30 anni, il calo più ampio.", "Il Bund perde l'1,4%, il calo più ampio."),
    ("Gli acquisti di oro delle banche centrali (+20%) sostengono il prezzo.", "L'oro sale del 20% con gli acquisti delle banche centrali."),
    ("Le banche dell'Euro Stoxx (+2,4%) trainano l'indice.", "L'Euro Stoxx sale del 2,4%, trainato dalle banche."),
    ("Il titolo di Intesa sale del 2% e il FTSE MIB dello 0,5%.", "Il FTSE MIB sale del 2% e Intesa dello 0,5%."),
    ("Il gas europeo (+9%) spinge le utility.", "Le utility salgono del 9% spinte dal gas europeo."),
    ("Tokyo, dove Toyota perde il 5%, chiude in calo.", "Tokyo perde il 5% e chiude in calo."),
    ("I rendimenti dei Btp a 10 anni salgono al 3,9%.", "I rendimenti dei Btp salgono al 3,9%."),
    ("L'oro tocca i 4.000 dollari e l'argento i 50 dollari.", "L'argento tocca i 4.000 dollari e l'oro i 50 dollari."),
    ("Il fondo sovrano norvegese possiede l'1,5% di Nestlé.", "Nestlé possiede l'1,5% del fondo sovrano norvegese."),
    ("In Europa il lusso perde il 3,5%, Kering il 6%.", "In Europa Kering perde il 3,5%, il lusso il 6%."),
    ("Le piccole banche regionali americane (-4%) preoccupano.", "Le banche americane perdono il 4% e preoccupano."),
    ("Il Nikkei recupera l'1% dopo il -3% di ieri.", "Il Nikkei perde il 3% dopo l'1% di ieri."),
    # secondo collaudo indipendente (25/11): la cifra dopo i due punti con un complemento prima, la cifra in testa con
    # participio o ausiliare, i livelli senza unità scambiati, la cifra tolta; poi i miei, scritti prima di provarli
    ("Il listino tecnologico di Hong Kong cede alle strette americane: -3,8%.", "Hong Kong cede alle strette americane: -3,8%."),
    ("Il listino tecnologico di Hong Kong è affossato dalle strette USA: -3,8%.", "Hong Kong è affossato dalle strette USA: -3,8%."),
    ("Il listino tecnologico di Hong Kong è affossato dalle strette USA: -3,8%.", "Il listino di Hong Kong è affossato dalle strette USA: -3,8%."),
    ("Il 3,8% lasciato sul terreno dal listino tecnologico di Hong Kong pesa sull'Asia.", "Il 3,8% lasciato sul terreno da Hong Kong pesa sull'Asia."),
    ("Il 3,8% è stato perso dal listino tecnologico di Hong Kong.", "Il 3,8% è stato perso da Hong Kong."),
    ("Il Nikkei chiude a 57.011, l'Hang Seng a 22.219.", "Il Nikkei chiude a 22.219, l'Hang Seng a 57.011."),
    ("L'euro sale a 1,08 sul dollaro e la sterlina a 1,27.", "La sterlina sale a 1,08 sul dollaro e l'euro a 1,27."),
    ("Il Bund rende il 2,3% dopo l'asta di ieri.", "Il Bund sale dopo l'asta di ieri."),
    ("Il comparto bancario di Madrid cede alle vendite sui tassi: -2,1%.", "Madrid cede alle vendite sui tassi: -2,1%."),
    ("Le auto di Francoforte sono affossate dai dazi americani: -3,4%.", "Francoforte è affossata dai dazi americani: -3,4%."),
    ("Il 2,9% lasciato sul terreno dai titoli del lusso di Parigi pesa sull'Europa.", "Il 2,9% lasciato sul terreno da Parigi pesa sull'Europa."),
    ("Il 5% è stato guadagnato dalle banche di Milano.", "Il 5% è stato guadagnato da Milano."),
    ("Il Kospi chiude a 2.580, il Taiex a 22.910.", "Il Taiex chiude a 2.580, il Kospi a 22.910."),
    ("Il cambio euro/dollaro sale a 1,09 e quello euro/sterlina a 0,84.", "Il cambio euro/sterlina sale a 1,09 e quello euro/dollaro a 0,84."),
    ("Il Bund rende il 2,6% mentre il Btp sale.", "Il Bund sale mentre il Btp rende."),
    ("Il Nikkei cede l'1,1% dopo il +2,4% di venerdì.", "Il Nikkei cede il 2,4% dopo l'1,1% di venerdì."),
    ("Il settore tecnologico di Taiwan, colpito dai chip, perde il 4%.", "Taiwan, colpita dai chip, perde il 4%."),
    ("Il rame sale a 9.900 dollari, lo zinco a 2.950 dollari.", "Lo zinco sale a 9.900 dollari, il rame a 2.950 dollari."),
    ("Il Treasury a 30 anni sale al 4,9%, quello a 2 anni scende al 4,1%.", "Il Treasury a 2 anni sale al 4,9%, quello a 30 anni scende al 4,1%."),
    ("Gli ordini dell'industria tedesca calano del 3%: pesano le auto.", "L'industria tedesca cala del 3%: pesano le auto."),
    ("Le small cap del Russell 2000 sono penalizzate dai tassi: -2,2%.", "Il Russell 2000 è penalizzato dai tassi: -2,2%."),
    ("Il 6% perso dalle azioni di Kering è il calo peggiore del lusso.", "Il 6% perso dal lusso è il calo peggiore di Kering."),
    ("Il dollaro australiano scende a 0,64 e quello neozelandese a 0,58.", "Il dollaro neozelandese scende a 0,64 e quello australiano a 0,58."),
    ("L'oro sale del 2% e tocca i 4.100 dollari, mentre l'argento resta a 48 dollari.", "L'oro sale del 2% e resta a 48 dollari, mentre l'argento tocca i 4.100 dollari."),
    ("Le vendite al dettaglio americane salgono dello 0,6%, la fiducia scende a 98,2.", "La fiducia americana sale dello 0,6%, le vendite al dettaglio scendono a 98,2."),
    # quarto collaudo indipendente (27/11): la cifra che si allarga a un secondo soggetto (caso della #034) e le due forme
    # che erano scoperte (il complemento che sparisce dopo la testa, il complemento cambiato dopo la cifra); poi i miei
    ("Il 10 anni scende di 6 pb, il 2 anni scende meno.", "Il 10 anni e il 2 anni scendono di 6 pb."),
    ("Ieri il 2 anni è sceso comunque, e il 10 anni di 6 pb.", "Ieri il 2 anni è sceso comunque, come il 10 anni, di 6 pb."),
    ("Il listino tecnologico di Hong Kong perde il 3,8% per le strette.", "Il listino tecnologico perde il 3,8% per le strette."),
    ("Le banche perdono il 2,4% a Milano dopo la BCE, meno che a Francoforte.", "Le banche perdono il 2,4% a Francoforte dopo la BCE, più che a Milano."),
    ("Il Nasdaq perde il 2%, Wall Street meno.", "Il Nasdaq e Wall Street perdono il 2%."),
    ("L'oro sale dell'1%, l'argento è fermo.", "L'oro e l'argento salgono dell'1%."),
    ("Il Kospi sale del 4% e Samsung tiene.", "Il Kospi e Samsung salgono del 4%."),
    ("Samsung sale del 4,5% a Seul, meno che a Tokyo.", "Samsung sale del 4,5% a Tokyo, più che a Seul."),
    ("Le azioni di Kering a Parigi perdono il 6%.", "Le azioni di Kering perdono il 6%."),
]
DESK_PASSA = [
    ("Ci leggiamo anche il rimbalzo dell'oro (+3,9%): finiscono le vendite per far cassa.",
     "Nel rimbalzo dell'oro (+3,9%) leggiamo la fine delle vendite per far cassa."),
    ("Il rimbalzo dell'oro (+3,9%) racconta la fine delle vendite per fare cassa.",
     "L'oro rimbalza del 3,9%: è finita la stagione delle vendite per fare cassa."),
    ("In Giappone l'inflazione sale al 2,3% e alimenta le attese di rialzo dei tassi",
     "L'inflazione giapponese sale al 2,3% e avvicina il rialzo dei tassi"),
    ("Il cambio euro-dollaro scende dello 0,6% dopo le parole della BCE.", "Dopo le parole della BCE il cambio euro-dollaro scende dello 0,6%."),
    ("Il decennale americano sale al 4,2% dopo i dati sui prezzi alla produzione.",
     "Dopo i dati sui prezzi alla produzione il decennale americano sale al 4,2%."),
    ("L'oro guadagna il 2,1% e l'argento il 3,4% mentre il dollaro si indebolisce.",
     "Mentre il dollaro si indebolisce, l'oro guadagna il 2,1% e l'argento il 3,4%."),
    ("Il listino tecnologico di Hong Kong perde il 3,8% sulle nuove strette americane.",
     "Sulle nuove strette americane il listino tecnologico di Hong Kong perde il 3,8%."),
    ("Sull'indice dei semiconduttori (-4,2%) pesano i conti deludenti di ieri sera.",
     "I conti deludenti di ieri sera pesano sull'indice dei semiconduttori (-4,2%)."),
    ("Le banche europee salgono dell'1,5% grazie alla curva dei tassi più ripida.",
     "Grazie alla curva dei tassi più ripida le banche europee salgono dell'1,5%."),
    ("Anche il Bund tedesco, come il decennale americano, sale al 2,6% in giornata.",
     "In giornata anche il Bund tedesco sale al 2,6%, come il decennale americano."),
    ("Il petrolio Brent cede il 2,3% sulle scorte americane in aumento.", "Le scorte americane in aumento: il petrolio Brent cede il 2,3%."),
    ("Le vendite al dettaglio americane crescono dello 0,4% a ottobre, sopra le attese.",
     "A ottobre le vendite al dettaglio americane crescono dello 0,4%, sopra le attese."),
    ("Il rame e l'alluminio salgono del 2% sulla domanda cinese.", "Sulla domanda cinese il rame e l'alluminio salgono del 2%."),
    ("Il decennale americano, dopo i dati sull'inflazione, sale al 4,2%.", "Dopo i dati sull'inflazione il decennale americano sale al 4,2%."),
    ("Il 3,8% perso dal listino tecnologico di Hong Kong è il calo peggiore da aprile.",
     "Il listino tecnologico di Hong Kong perde il 3,8%, il calo peggiore da aprile."),
    ("Il Nasdaq (-2,1%) chiude la terza seduta in calo.", "Il Nasdaq perde il 2,1%: terza seduta in calo."),
    ("Nvidia perde il 3,2% dopo i conti, e trascina i chip.", "Dopo i conti Nvidia perde il 3,2% e trascina i chip."),
    ("Il calo del Brent (-1,8%) arriva con le scorte in aumento.", "Il Brent scende dell'1,8% con le scorte in aumento."),
    ("Le azioni europee salgono dello 0,9% con le banche in testa.", "Con le banche in testa, le azioni europee salgono dello 0,9%."),
    ("A Tokyo il Nikkei cede l'1,2% sul rafforzamento dello yen.", "Il Nikkei cede l'1,2% a Tokyo sul rafforzamento dello yen."),
    ("Il rendimento del Bund sale di 5 pb al 2,71%.", "Il rendimento del Bund sale al 2,71%, 5 pb in più."),
    ("Microsoft, che vale il 7% dell'indice, perde il 2%.", "Microsoft perde il 2% e vale il 7% dell'indice."),
    ("La crescita dei prezzi alla produzione (+0,4%) supera le attese.", "I prezzi alla produzione crescono dello 0,4%, più delle attese."),
    ("Stamattina il Kospi sale dell'1,5% trainato da Samsung.", "Trainato da Samsung, stamattina il Kospi sale dell'1,5%."),
    ("Il dollaro si rafforza dello 0,7% contro lo yen dopo i dati.", "Dopo i dati il dollaro si rafforza dello 0,7% contro lo yen."),
    ("In ottobre l'inflazione dell'area euro scende al 2,1%.", "L'inflazione dell'area euro scende al 2,1% in ottobre."),
    ("Il guadagno di ASML (+4%) traina il listino olandese.", "ASML guadagna il 4% e traina il listino olandese."),
    ("Il Russell 2000, l'indice delle piccole società, sale del 2,2%.", "Le piccole società del Russell 2000 salgono del 2,2%."),
    ("-2,5% per il FTSE MIB, il peggiore in Europa.", "Il FTSE MIB perde il 2,5%, peggiore in Europa."),
    ("Il prezzo del rame tocca i 10.500 dollari.", "Il rame tocca i 10.500 dollari."),
    ("Il petrolio Brent cede il 2,3% sulle scorte.", "Sulle scorte il Brent cede il 2,3%."),
    ("Nel Dow Jones in calo (-0,4%) pesano i titoli sanitari.", "Il Dow Jones cede lo 0,4%, appesantito dai titoli sanitari."),
    ("Il Treasury a 10 anni resta al 4,91%.", "Il rendimento del Treasury a 10 anni: 4,91%."),
    ("Apple perde l'1,1% dopo il richiamo.", "Dopo il richiamo, Apple perde l'1,1%."),
    ("Il Brent, salito del 3% in settimana, chiude a 82 dollari.", "Il Brent chiude a 82 dollari, salito del 3% in settimana."),
    ("Tesla (+6,2%) vola dopo le consegne.", "Dopo le consegne Tesla vola del 6,2%."),
    ("Le Borse asiatiche chiudono in calo, con Tokyo a -1,1%.", "Le Borse asiatiche chiudono in calo e Tokyo perde l'1,1%."),
    ("Sul mercato dei cambi lo yen si rafforza dello 0,5%.", "Lo yen si rafforza dello 0,5% sul mercato dei cambi."),
    ("L'indice dei prezzi al consumo americano sale del 3,1% su base annua.",
     "Su base annua i prezzi al consumo americani salgono del 3,1%."),
    ("Intesa Sanpaolo guadagna l'1,7% e UniCredit il 2,2%.", "UniCredit guadagna il 2,2% e Intesa Sanpaolo l'1,7%."),
    ("Il VIX, l'indice della paura, scende del 12%.", "L'indice della paura, il VIX, scende del 12%."),
    ("Il dollaro perde lo 0,4% contro l'euro.", "Contro l'euro il dollaro perde lo 0,4%."),
    ("Bitcoin torna sopra i 90.000 dollari (+4%) dopo una lunga settimana di vendite.",
     "Bitcoin sale del 4%, sopra i 90.000 dollari, dopo una lunga settimana di vendite."),
    ("La disoccupazione americana sale al 4,4%, il livello più alto dal 2021.",
     "Il livello più alto dal 2021: la disoccupazione americana sale al 4,4%."),
    ("Per il Kospi un calo del 2,6%, il peggiore dell'Asia.", "Il Kospi cala del 2,6%, il peggiore dell'Asia."),
    ("Le azioni di Novo Nordisk crollano del 18% dopo lo studio.", "Dopo lo studio Novo Nordisk crolla del 18%."),
    ("Le banche nel listino di Milano perdono il 2,4%.", "Nel listino di Milano le banche perdono il 2,4%."),
    ("Il rame e l'argento salgono del 2%.", "Salgono del 2% il rame e l'argento."),
    ("Nel Dow Jones in rialzo (+0,85%) leggiamo una rotazione.", "Il Dow Jones sale dello 0,85%: leggiamo una rotazione."),
    # secondo collaudo indipendente (25/11): due cifre di fila nei rendimenti e nei prezzi; poi i miei
    ("Il Bund a 10 anni rende il 2,31%, 4 punti base in meno di ieri.", "Il rendimento del Bund a 10 anni scende di 4 punti base al 2,31%."),
    ("Il rame tocca i 9.800 dollari a tonnellata, +2,2% in giornata.", "Il rame sale del 2,2% e tocca i 9.800 dollari a tonnellata."),
    ("Nvidia sale del 3% a 140 dollari.", "Nvidia tocca i 140 dollari, +3%."),
    ("Il Btp a 10 anni rende il 3,52%, 6 punti base in più di ieri.", "Il rendimento del Btp a 10 anni sale di 6 punti base al 3,52%."),
    ("L'argento tocca i 52 dollari l'oncia, +3,1% in giornata.", "L'argento sale del 3,1%: tocca i 52 dollari l'oncia."),
    ("Il Nasdaq chiude a 21.450 punti, in calo dell'1,4%.", "Il Nasdaq cede l'1,4% e chiude a 21.450 punti."),
    ("Il cambio euro/yen sale a 162,3 dopo la BoJ.", "Dopo la BoJ l'euro/yen sale a 162,3."),
    ("La sterlina scende a 1,26 sul dollaro dopo i dati sull'inflazione britannica.", "Dopo i dati sull'inflazione britannica la sterlina scende a 1,26 sul dollaro."),
    ("Il Dax, frenato dalle auto, perde lo 0,7%.", "Il Dax perde lo 0,7%, frenato dalle auto."),
    ("Il listino di Madrid è spinto dalle banche: +1,3%.", "Spinto dalle banche, il listino di Madrid sale dell'1,3%."),
    ("Il 2,5% perso dal FTSE MIB è il calo più forte da aprile.", "Il FTSE MIB perde il 2,5%, il calo più forte da aprile."),
    ("Le azioni di Mediobanca salgono del 4,2% sull'offerta di Mps.", "Sull'offerta di Mps Mediobanca sale del 4,2%."),
    ("Il Nikkei chiude a 39.120, l'Hang Seng a 19.870.", "L'Hang Seng chiude a 19.870, il Nikkei a 39.120."),
    ("Il Brent sale dell'1,9% a 74 dollari al barile.", "Il Brent tocca i 74 dollari al barile, +1,9%."),
    ("Il Treasury a 2 anni scende al 4,12%, 8 punti base in meno.", "Il Treasury a 2 anni perde 8 punti base e scende al 4,12%."),
    ("Il bitcoin è sceso sotto i 70.000 dollari: -5%.", "Il bitcoin perde il 5%, sotto i 70.000 dollari."),
    ("Il PIL tedesco cresce dello 0,2% nel trimestre, meno delle attese.", "Nel trimestre il PIL tedesco cresce dello 0,2%, meno delle attese."),
    ("Il petrolio WTI è frenato dalle scorte americane: -1,2%.", "Frenato dalle scorte americane, il WTI cede l'1,2%."),
    ("Il 4% guadagnato da Ferrari arriva dopo i conti.", "Ferrari guadagna il 4% dopo i conti."),
    ("Il rendimento del Bund a 10 anni cala al 2,61%, il livello più basso da ottobre.", "Il Bund a 10 anni rende il 2,61%, il livello più basso da ottobre."),
    # quarto collaudo indipendente (27/11): un aggettivo o un participio dopo il nome della misura, il tempo e la fonte
    # davanti (riscritture vere della #034 e varianti delle edizioni del 26-27/11); poi i miei
    ("Per la Cina il rialzo è di 20 punti sopra il 25% già in vigore.", "Per la Cina il rialzo proposto è di 20 punti sopra il 25% già in vigore."),
    ("Mercoledì il calo del 6,16% è arrivato dopo la vendita a Wall Street.", "Mercoledì il calo complessivo del 6,16% è arrivato dopo la vendita a Wall Street."),
    ("Per Bloomberg il rialzo del 25/11 (+3,5% a 94,61 dollari) viene dagli attacchi in Medio Oriente.",
     "Per Bloomberg il rialzo complessivo del 25/11 (+3,5% a 94,61 dollari) viene dagli attacchi in Medio Oriente."),
    ("Per la BCE il taglio è di 25 pb a dicembre, dicono i mercati.", "Per la BCE il taglio atteso è di 25 pb a dicembre, dicono i mercati."),
    ("Il calo del Nasdaq è del 10% in una settimana.", "Il calo settimanale del Nasdaq è del 10%."),
    ("Samsung perde il 7% a Seul e SK hynix quasi il 6%.", "A Seul Samsung perde il 7% e SK hynix quasi il 6%."),
    ("Il 2 anni scende di 4 pb e il 10 anni di 6 pb.", "Il 10 anni scende di 6 pb e il 2 anni di 4 pb."),
    ("Il Nikkei perde il 2% secondo Reuters.", "Secondo Reuters il Nikkei perde il 2%."),
    ("Il rame e l'argento salgono del 2%.", "L'argento e il rame salgono del 2%."),
]


def passo_coerenza():
    """Casi costruiti con le frasi vere della prova del 23/11, della #031 e della #032, sui prezzi del 20/11 (dati.json del
    campione #031): una cifra che cambia soggetto, un "più del 2%" detto di un -4,6%, un verso contrario alla chiusura, un
    rimando a un pezzo che non ne parla e un'ipotesi nel titolo si fermano; le frasi giuste che gli somigliano passano. Poi
    il ragionamento: l'incarico del revisore porta la frase dell'oro della #031, un "non regge" ferma finché la frase resta
    uguale, e la risposta che manca si dice. Infine il desk: la riscrittura di Hong Kong si respinge, una che toglie un
    fatto unico pure, quelle che riordinano passano."""
    import controlli_coerenza as K
    import desk
    tmp = os.path.join(TMP, "coerenza")
    os.makedirs(tmp, exist_ok=True)
    D = json.load(open(os.path.join(RETE, "2026-11-23", "sorgenti", "dati.json"), encoding="utf-8"))
    M = K.mercati_del_giorno(D)
    ferma = {"hk": "Hong Kong perde il 3,8% per le strette USA sulla tecnologia per la Cina",
             "oro2": "La paura ha preso il posto dell'inflazione. L'oro cede più del 2% e il dollaro quasi non si muove.",
             "brent": "Il Brent scende con le scorte USA, ma il rischio Hormuz lo sostiene",
             "oro_su": "Nel giorno della paura l'oro sale e fa da rifugio.",
             "nikkei": "Il Nikkei chiude a 56.000 punti, il livello più basso da aprile.",
             # quarto collaudo (27/11): la data o il giorno della settimana della seduta si confrontano
             "data_stessa": "Il 23/11 il Kospi è salito del 6,3%.",
             "giorno_stesso": "Lunedì il Kospi sale del 6,3%.",
             # ricollaudo del quarto giro (27/11): l'esenzione vale solo per la proposizione della cifra
             "relativa": "Il Kospi, che ieri aveva chiuso in calo, sale del 6,3%.",
             "confronto": "Il Kospi sale del 6,3% e recupera quasi tutto il crollo di venerdì.",
             "mese_stesso": "Il Kospi sale del 6,3% e torna ai livelli di novembre.",
             "chiude_dopo_aver": "Il Kospi chiude in rialzo del 6,3% dopo aver aperto in calo.",
             "arrivata_a": "Il Kospi sale del 6,3% sulla notizia arrivata a mercati aperti.",
             "verso_imperfetto": "Il Kospi sale mentre gli investitori aspettavano il fondo.",
             "verso_dopo_aver": "Il Kospi sale dopo aver aperto in calo."}
    passa = {"hk_tech": "Nuove strette USA sulla tecnologia per la Cina fanno scendere il listino tecnologico di Hong Kong (-3,8%)",
             "nikkei": "Il Nikkei chiude a 56.436,65 punti (-5,06%), il livello più basso dal 13 aprile.",
             "vix": "Il VIX (volatilità attesa sull'S&P 500) sale del 26,2%.",
             "seul": "Samsung perde il 7% a Seul e SK hynix quasi il 6%.",
             "dollaro": "L'oro scende e il dollaro quasi non si muove.",
             "tassi": "Venerdì il 10 anni è sceso dal 5,04% al 4,92% e il 2 anni di 13 pb.",
             "se": "Se il 10 anni torna sopra il 5,04% la paura non basta più e torna a contare la Fed.",
             "sett": "Per questo il Nasdaq ha perso il 10% in una settimana.",
             "seduta": "Il FTSE MIB chiude a -2,5% dopo aver perso quasi il 3%.",
             "crisi": "La differenza con le crisi in cui l'oro sale sta nell'origine della paura.",
             "nasdaq100": "Il Nasdaq 100 perde il 5,6%.",
             "europa": "L'Europa perde il 7% in cinque sedute.",
             # quarto collaudo (27/11): falsi allarmi sulle edizioni vere del 26 e 27/11. Una cifra che la frase colloca in
             # un altro giorno, in un altro momento della seduta, o che è un livello, non è la chiusura del giorno
             "minimo": "Il Nasdaq è arrivato a perdere il 7,5% e l'S&P 500 il 6,1%, poi gli acquisti hanno ridotto il calo.",
             "altra_data": "A nostro avviso conta l'attesa: il 24/11 il Kospi era salito del 6,3% e il giorno dopo aveva restituito tutto.",
             "giorno_prima": "Il giorno prima il Kospi è salito del 2%.",
             "altro_giorno": "Giovedì il Nasdaq ha perso il 2%.",
             "punti": "Per KED Global il Kospi si avvicina ai 5.000 punti sulla speranza di un accordo."}
    sfuggiti = [k for k, t in ferma.items() if not K.cifre_e_direzioni({k: t}, M)]
    falsi = [f"{k}: {K.cifre_e_direzioni({k: t}, M)[0][:90]}" for k, t in passa.items() if K.cifre_e_direzioni({k: t}, M)]
    fed = {"chiave": "fed", "titolo": "La Fed ha l'inflazione contro e non può soccorrere la borsa",
           "testo": ["Il PCE di mercoledì, atteso a +0,3% sul mese, è il dato che la Fed guarda di più per l'inflazione."]}
    C = {"top": {"titolo": "Wall Street crolla", "dek": ""}, "moduli": [fed], "notizie": [],
         "ieri": [("Gio 19, 14:30", "Indice Philadelphia Fed (novembre)", "6,3 (atteso 20,0)", "-", "[[fed]]")],
         "agenda": [("Mer 25, 14:30", "Prezzi al consumo USA (ottobre)", "+0,3%", "Inflazione", "[[fed]]")]}
    # i mercati e la chiave del pezzo contano come nomi: "→ [[oro]]" da una frase sull'oro porta al pezzo sull'oro (27/11)
    C["moduli"].append({"chiave": "oro", "titolo": "L'oro recupera metà della caduta ma resta lontano dai massimi",
                        "testo": ["Il metallo torna a fare da rifugio."]})
    C["in30"] = ["L'oro ha già riconquistato metà della caduta di questa settimana. [[oro]]"]
    rim = K.rimandi(C)
    rim_ok = len(rim) == 1 and "ieri.0" in rim[0]
    tit_no = K.titoli({"top": {"titolo": "L'oro cala nel giorno della paura, forse per fare cassa"}})
    tit_si = K.titoli({"top": {"titolo": "L'oro cala nel giorno della paura"}})
    # il ragionamento: la frase dell'oro della #031, giudicata "non regge", ferma finché resta uguale
    q = "L'oro, che di solito ripara, è invece caduto insieme alle azioni, e a nostro avviso pesa il dollaro forte."
    C2 = {"top": {"titolo": "Wall Street entra in correzione"}, "quadro": q, "moduli": [], "notizie": []}
    campi = {"quadro": q}
    inc = K.scrivi_incarico(C2, campi, M, tmp)
    rid = next((x["id"] for x in inc["frasi"] if x["frase"] == q), None)
    eur = any(r.startswith("EUR/USD") and "(fermo)" in r for r in inc["prezzi"])
    manca = K.verdetti(campi, tmp)[0]
    json.dump([{"id": x["id"], "esito": "non_regge" if x["id"] == rid else "regge", "nota": "EUR/USD fermo nella seduta",
                "rimedio": "lettura con i prezzi"} for x in inc["frasi"]], open(os.path.join(tmp, K.RISPOSTA), "w"))
    resta = K.verdetti(campi, tmp)[0]
    corretta = K.verdetti({"quadro": "L'oro è caduto insieme alle azioni: a nostro avviso si vende ciò che si può vendere."}, tmp)[0]
    ragiona = bool(rid) and eur and manca and len(resta) == 1 and "lettura con i prezzi" in resta[0] and not corretta
    # il desk (G-45): una cifra resta sul suo soggetto. (originale, riscrittura) in DESK_PASSA si accettano, in DESK_NO si
    # respingono. Poi le riscritture vere accettate nelle edizioni (sorgenti/*/desk_ok.json) restano accettate, e il
    # confronto con dati.json ferma ciò che Coerenza fermerebbe nell'edizione (il desk non deve mai poterla bloccare).
    sbagliati = [f"passa respinta: {o[:50]}" for o, n in DESK_PASSA if desk.controlla(o, n, set())] + \
        [f"cattiva passata: {o[:50]}" for o, n in DESK_NO if not desk.controlla(o, n, set())]
    # Le riscritture vere: un elenco fisso e versionato (rete/desk_vere.json), ognuna con il suo giudizio, lungo il percorso
    # intero di `desk.py verifica` (i nomi dell'edizione, gli altri campi, poi il confronto con Coerenza sul dati.json del
    # giorno, solo dove l'edizione ha ancora il testo che il desk ha letto). Le "buona" passano, le "sbagliata" si
    # respingono. Le riscritture delle edizioni arrivate dopo (sorgenti/*/desk_ok.json fuori dall'elenco) le ha accettate
    # il desk di allora e nessuno le ha giudicate: se il desk di oggi ne respinge una è da leggere, non un rosso (quarto
    # collaudo, 27/11: il glob su tutte le edizioni faceva tornare rosso il cancello del rilascio a ogni edizione nuova).
    import contextlib
    import io
    elenco = json.load(open(os.path.join(RETE, "desk_vere.json"), encoding="utf-8"))
    giudicate = {(e["data"], e["campo"], e["originale"]) for e in elenco}
    edizioni, da_leggere, nuove = {}, [], []
    for f in sorted(glob.glob(os.path.join(R, "sorgenti", "*", "desk_ok.json"))):
        data = os.path.basename(os.path.dirname(f))
        try:
            voci = json.load(open(f, encoding="utf-8"))
        except ValueError:
            voci = None
        for e in voci if isinstance(voci, list) else [None]:
            if not isinstance(e, dict) or not all(isinstance(e.get(k), str) for k in ("campo", "originale", "testo")):
                da_leggere.append(f"{data}: voce di desk_ok.json incompleta o illeggibile, saltata"); continue
            if (data, e["campo"], e["originale"]) not in giudicate:
                nuove.append(dict(e, data=data, giudizio=""))

    def verifica(e):
        cart = os.path.join(R, "sorgenti", e["data"])
        if cart not in edizioni:
            qui = os.getcwd()
            try:
                os.chdir(cart)
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    Ce = desk._carica(os.path.join(cart, "edizione.py"))
            finally:
                os.chdir(qui)
            att = desk.campi(Ce)
            edizioni[cart] = (Ce, att, set().union(*[desk._nomi(v) for v in att.values()]), desk._mercati_del_giorno(cart))
        Ce, att, tutto, Me = edizioni[cart]
        altri = " ".join(v for k, v in att.items() if k != e["campo"])
        return desk.controlla(e["originale"], e["testo"], tutto, e["campo"], altri) or \
            (desk.coerenza_peggiora(Ce, e["campo"], e["testo"], Me) if att.get(e["campo"]) == e["originale"] else None)
    for e in elenco:
        motivo = verifica(e)
        if e["giudizio"] == "buona" and motivo:
            sbagliati.append(f"vera buona respinta {e['data']} {e['campo']}: {motivo[:60]}")
        elif e["giudizio"] == "sbagliata" and not motivo:
            sbagliati.append(f"vera sbagliata accettata {e['data']} {e['campo']}")
    for e in nuove:
        motivo = verifica(e)
        if motivo:
            da_leggere.append(f"{e['data']} {e['campo']}: {motivo[:90]}")
    vere = elenco
    # una proposta malformata è un rifiuto pulito, e un campo fuori misura si respinge subito
    if not desk.controlla("Il Bund rende il 2,3%.", ["x"], set()) or not desk.controlla(5, "x", set()):
        sbagliati.append("proposta malformata accettata")
    enorme = " ".join(f"Il titolo {i} sale del {i},5%." for i in range(300))
    if not desk.controlla(enorme, enorme.replace("sale", "cresce"), set()):
        sbagliati.append("campo fuori misura accettato")
    if desk._nomi("dopo le parole della BCE.") != desk._nomi("dopo le parole della BCE il cambio"):
        sbagliati.append("BCE. e BCE contano come nomi diversi")
    Cd = {"top": {"titolo": "Wall Street crolla", "dek": ""}, "quadro": "Il Brent si muove con le scorte USA.", "moduli": [],
          "notizie": []}
    contro_dati = [desk.coerenza_peggiora(Cd, "quadro", "Il Brent scende con le scorte USA.", M),
                   desk.coerenza_peggiora(Cd, "top.titolo", "Wall Street forse crolla", M),
                   desk.coerenza_peggiora(dict(Cd, quadro=DESK_NO[0][0]), "quadro", DESK_NO[0][1], M)]
    sbagliati += ["dati: verso, ipotesi o Hong Kong passati"] if not all(contro_dati) else []
    sbagliati += ["dati: riordino buono respinto"] if desk.coerenza_peggiora(Cd, "quadro", "Con le scorte USA il Brent si muove.", M) else []
    corto = ("La SEC ha aperto un esame su Nvidia, il titolo che regge la storia dell'intelligenza artificiale nelle borse. "
             "Il titolo ha perso il 14% venerdì e più del 20% in una settimana.")
    lungo = corto.replace(" Il titolo", " Lo staff guarda a possibili problemi contabili nei bilanci. Il titolo")
    tolto = desk.controlla(lungo, corto, set(), altri="")
    eco = desk.controlla(lungo, corto, set(), altri="Lo staff della SEC guarda a possibili problemi contabili nei bilanci.")
    desk_ok = not sbagliati and bool(tolto) and eco is None
    ok = not sfuggiti and not falsi and rim_ok and tit_no and not tit_si and ragiona and desk_ok
    det = (f"{len(ferma)} frasi sbagliate fermate, {len(passa)} giuste passate (cifra che cambia soggetto, \"più del\", verso, "
           "periodo, ipotesi, parentesi); rimando a un pezzo che non ne parla; ipotesi nel titolo; il ragionamento dell'oro della "
           f"#031 fermato finché resta e liberato quando cambia; desk: {len(DESK_NO)} cifre spostate respinte, {len(DESK_PASSA)} "
           f"riscritture buone, {sum(e['giudizio'] == 'buona' for e in vere)} vere buone passate e "
           f"{sum(e['giudizio'] == 'sbagliata' for e in vere)} sbagliate respinte lungo il percorso intero di verifica, verso/ipotesi/cifra contro dati.json "
           "fermati, un fatto unico respinto, un'eco passata, proposte malformate o fuori misura respinte")
    if not ok:
        det = "; ".join(x for x in [
            f"sfuggiti {sfuggiti}" if sfuggiti else "", f"falsi allarmi {falsi[:2]}" if falsi else "",
            "" if rim_ok else f"rimandi {rim[:2]}", "" if tit_no and not tit_si else "titoli",
            "" if ragiona else f"ragionamento (id {rid}, EUR/USD fermo {eur}, manca {bool(manca)}, resta {resta[:1]}, corretta {corretta[:1]})",
            "" if desk_ok else f"desk ({len(sbagliati)} sbagliati: {sbagliati[:3]}, tolto {tolto}, eco {eco})"] if x)
    esito("Coerenza: il testo regge contro i dati", ok, det)
    if da_leggere:
        print(f"[leggi] Coerenza: {len(da_leggere)} riscritture di edizioni fuori da rete/desk_vere.json respinte dal desk di "
              "oggi o incomplete (giudicale e mettile nell'elenco):")
        for x in da_leggere[:8]:
            print("        " + x)
        NOTE.append(f"desk: {len(da_leggere)} riscritture di edizioni nuove respinte dal desk di oggi, da giudicare")


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
    # chi parla senza nome (G-46): "la stampa americana", "notizie secondo cui" e un'indiscrezione senza la testata si fermano;
    # una testata detta come fonte nella frase, o nel pezzo per un'indiscrezione, li copre (casi delle edizioni #031-#035)
    Ca = {"top": {"dek": "Il bersaglio resta Nvidia, dopo l'indagine riportata dalla stampa americana."},
          "notizie": [{"titolo": "La SEC indaga sui conti di Nvidia, riferisce la stampa americana"},
                      {"titolo": "La BCE discute la riserva", "testo": "Secondo Reuters i vertici ne avrebbero parlato; un resoconto anonimo dà la decisione a dicembre."},
                      {"titolo": "Il Brent sale", "testo": "Media iraniani riferiscono di mine, ma Bloomberg scrive di non avere conferme."},
                      {"titolo": "La SEC indaga", "testo": "Secondo la stampa americana la SEC indaga. Secondo Reuters il Brent sale."}],
          "moduli": [pezzo("e", "Le indiscrezioni dicono solo che i risultati sono pronti.", "Secondo tre fonti citate da Reuters i dazi sono pronti.", "Fonti: Reuters."),
                     pezzo("f", "Dopo le dimissioni sono arrivate notizie secondo cui era nel mirino.", "La stampa coreana lo lega al fondo.", "Fonti: Korea Times."),
                     pezzo("g", "Il governo prepara il fondo, scrive il Korea Times.", "Per la stampa locale, come scrive Reuters, conta il fondo.", "Fonti: Korea Times, Reuters."),
                     pezzo("h", "Secondo le indiscrezioni del Financial Times il gruppo valuta un'offerta.", "Secondo il Nikkei fonti vicine al governo parlano di un rinvio.", ""),
                     pezzo("i", "L'azienda ha presentato il prodotto alla stampa specializzata.", "La media mobile passa sotto il prezzo.", ""),
                     pezzo("l", "I media scrivono che il gruppo valuta un'offerta.", "Di solito decide la Fed.", ""),
                     pezzo("m", "Voci di mercato indicano un'offerta imminente.", "Di solito decide la Fed.", ""),
                     pezzo("n", "Secondo indiscrezioni di stampa il gruppo tratta.", "Secondo Reuters il Brent sale.", ""),
                     pezzo("o", "Le banche salgono, trascinate dal Nikkei, mentre la stampa giapponese parla di una stretta.", "Di solito decide la Fed.", ""),
                     pezzo("p", "L'indagine è stata riportata dalla stampa americana. A rivelarla per primo è stato il Wall Street Journal.",
                           "Il ministero ha convocato i media stranieri per spiegare le sanzioni.", ""),
                     pezzo("q", "I media iraniani hanno parlato di un attacco.", "Circolano indiscrezioni su un'offerta. Lo ha scritto Bloomberg.", ""),
                     pezzo("r", "Secondo il Wall Street Journal la BoJ prepara il rialzo. Il governo ha smentito le indiscrezioni.",
                           "Secondo tre fonti citate da Reuters, Tokyo interverrà. Circolano indiscrezioni su un'offerta per Mps.", "")]}
    anon = sorted(d for d, _ in getattr(T, "senza_testata", lambda *a: [])(T.testi(Ca), nomi + ["Nvidia", "Korea Times"], ["Fonti: Nikkei, Korea Times."]))
    anon_ok = anon == sorted(["moduli.1.perche", "moduli.1.testo.0", "moduli.5.testo.0", "moduli.6.testo.0", "moduli.7.testo.0",
                    "moduli.8.testo.0", "moduli.10.testo.0", "moduli.11.perche", "notizie.0.titolo", "notizie.3.testo", "top.dek"]) \
        and bool(T.connettivi("Secondo la stampa coreana il Kospi sale perché arriva il fondo. A. B. C. D.")) \
        and not T.connettivi("Secondo Goldman Sachs il Kospi sale perché arriva il fondo. A. B. C. D.")
    fonti_ok = fonti_ok and anon_ok
    # agenda (G-46): istruzioni e modello dicono la stessa cosa sull'evento senza un numero atteso, che non usa "Sopra/Sotto"
    senza_numero = re.compile(r"senza (?:un )?numero atteso|non ha un numero atteso")
    agenda_ok = all(senza_numero.search(open(os.path.join(R, f), encoding="utf-8").read())
                    for f in ("ISTRUZIONI.md", "edizione_modello_v6.py"))
    fonti_ok = fonti_ok and agenda_ok
    # perché della scommessa (G-46, punto 6): la regola dice che cos'è un motivo e non chiede più "che cosa aspetta" il mercato
    lun = open(os.path.join(R, "APP_LUNEDI.md"), encoding="utf-8").read() + open(os.path.join(R, "scommessa", "pronostico.py"), encoding="utf-8").read()
    lunedi_ok = "Non è un motivo" in lun and not re.search(r"che cosa aspetta", lun)
    fonti_ok = fonti_ok and lunedi_ok
    # perché della scommessa: le forme vuote si fermano, i motivi veri passano (casi dei lunedì 16/11 e 23/11)
    motivi = [("spx", "I future perdono terreno dopo il crollo dei chip asiatici"),
              ("sx5e", "Dopo il minimo da maggio aspetta di capire se Wall Street tiene"),
              ("ust10", "Se la paura cala i Treasury smettono di fare da rifugio e il rendimento risale"),
              ("eurusd", "Un rialzo della Fed a dicembre sempre più probabile sostiene il dollaro"),
              ("brent", "Le scorte americane in aumento tengono basso il greggio"),
              ("oro", "Un rialzo della Fed a dicembre sempre più probabile pesa sull'oro"),
              ("acwi", "Rimbalza dopo la caduta di venerdì, la peggiore da mesi"),
              ("fed", "Con un rialzo già scontato il rendimento a due anni resta fermo"),
              ("vix", "Direzione debole: nessuna causa nelle notizie, poggia solo sulla tendenza di fondo"),
              ("nikkei", "Direzione debole: poggia solo sulla tendenza di fondo dopo il rimbalzo")]
    vuoti = [n for n, *_ in getattr(T, "perche_vuoti", lambda m: [])(motivi)]
    lunedi_ok = vuoti == ["sx5e", "oro", "acwi"]
    fonti_ok = fonti_ok and lunedi_ok
    ok = not sfuggiti and not fermate and sigla and fonti_ok and coperta and voce and sigle_ok
    esito("Scrittura: lessico di casa, fonti e sigle", ok,
          f"{len(calchi)} calchi fermati, {len(giuste)} frasi giuste passate, testate tra parentesi fermate (anche una nuova), "
          "fonte di un livello del mattino passata, testata nominata e assente dalla riga Fonti fermata, aperture con domanda "
          "contate, chi parla senza nome fermato, \"l'oro vende\" fermato, causa coperta da chi la dà o dalla lettura dichiarata, sigle dette in parole" if ok else
          "; ".join(x for x in (f"calchi non fermati: {sfuggiti}" if sfuggiti else "", f"frasi giuste fermate: {fermate}" if fermate else "",
                                "" if sigla else "guidance è ancora una sigla da spiegare",
                                "" if fonti_ok else f"testate tra parentesi: {par}; conteggio: {conta}; fuori dalle Fonti: {fuori}; domande: {domande}; senza nome: {anon}; agenda senza numero atteso nelle istruzioni: {agenda_ok}; perché del lunedì: {lunedi_ok}",
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
        # dati ufficiali riconosciuti anche se non dichiarati (G-06, G-46): due autori non bastano, serve il comunicato
        ("G01", "top_news", [reuters("kfgo.com"), fonte("CNBC", "https://www.cnbc.com/a")],
         {"testo": "Cina, ottobre: vendite al dettaglio +0,4% annuo (atteso +0,8%)"}, "ufficiale"),
        ("G02", "top_news", [reuters("kfgo.com"), fonte("Ufficio di statistica", "https://www.bls.gov/a")],
         {"testo": "Stati Uniti: prezzi al consumo +0,4% sul mese (atteso +0,3%)"}, "passa"),
        ("G03", "top_news", [reuters("kfgo.com"), fonte("CNBC", "https://www.cnbc.com/a")],
         {"testo": "Nvidia riferisce martedì: utile per azione atteso 2,47 $, ricavi attesi circa 108,8 mld $"}, "passa"),
        ("G04", "deep_dive", [reuters("kfgo.com"), fonte("CNBC", "https://www.cnbc.com/a")],
         {"testo": "Cina, ottobre: produzione industriale +4,8% annuo (atteso +5,3%)"}, "ufficiale"),
        # G-46: anche un indice senza unità accanto alle attese (il PMI del #032), ovunque; non il calendario
        ("G09", "top_news", [reuters("kfgo.com"), fonte("investingLive", "https://investinglive.com/a")],
         {"testo": "Nell'area euro l'indice PMI composito resta a 51,7 (atteso 51,9)"}, "ufficiale"),
        # G-46: senza unità serve il numero atteso; la stima di una casa non è un'attesa; il comunicato cercato due volte basta
        ("G11", "top_news", [reuters("kfgo.com"), fonte("CNBC", "https://www.cnbc.com/e")],
         {"testo": "L'indice sale a 51,2, sopra le attese degli operatori"}, "passa"),
        ("G12", "top_news", [reuters("kfgo.com"), fonte("CNBC", "https://www.cnbc.com/f")],
         {"testo": "Il Brent chiude a 92,57 $ con attese di un taglio dell'offerta"}, "passa"),
        ("G13", "top_news", [reuters("kfgo.com"), fonte("CNBC", "https://www.cnbc.com/g")],
         {"testo": "La scadenza del 15 dicembre resta, attesa una proroga"}, "passa"),
        ("G14", "deep_dive", [reuters("kfgo.com"), fonte("CNBC", "https://www.cnbc.com/h")],
         {"testo": "Il PIL crescerà del 2,8% nel 2027 (stima BofA 3,1%)"}, "passa"),
        ("G15", "deep_dive", [reuters("kfgo.com"), fonte("CNBC", "https://www.cnbc.com/i")],
         {"testo": "Occupati non agricoli +165.000 contro i +65.000 attesi"}, "ufficiale"),
        ("G16", "top_news", [reuters("kfgo.com"), fonte("investingLive", "https://investinglive.com/b")],
         {"testo": "Nell'area euro l'indice PMI composito resta a 51,7 (atteso 51,9)",
          "ufficiale_cercato": ["HCOB flash eurozone PMI November 2026 press release", "S&P Global eurozone composite PMI flash November 2026"]}, "passa"),
        ("G17", "deep_dive", [reuters("kfgo.com"), fonte("CNBC", "https://www.cnbc.com/l")],
         {"testo": "Il titolo cede il 2,1% (attese di un taglio dei tassi)"}, "passa"),
        ("G18", "deep_dive", [reuters("kfgo.com"), fonte("CNBC", "https://www.cnbc.com/m")],
         {"testo": "L'indice sale del 4,6%, sopra le attese degli operatori"}, "passa"),
        ("G19", "top_story", [reuters("kfgo.com"), fonte("CNBC", "https://www.cnbc.com/n")],
         {"testo": "Alphabet perde il 12,6% dopo ricavi sotto le attese"}, "ufficiale"),
        ("G10", "agenda", [reuters("kfgo.com"), fonte("CNBC", "https://www.cnbc.com/d")],
         {"testo": "PMI flash dell'area euro lunedì alle 10:00: atteso 51,9 (prima 51,7)", "data_evento": "2026-11-23"}, "passa"),
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
    # fonte riconoscibile sotto ogni approfondimento (G-46, punto 7): comunque sia scritta, un'agenzia, un comunicato o una
    # grande testata bastano; soli siti minori no (casi delle edizioni #028-#035)
    sys.path.insert(0, R)
    import autori as A
    senza = getattr(A, "approfondimenti_senza_riconoscibile", lambda r, f=(): [(p, []) for p, _ in r])
    righe = [("a", "Fonti: Reuters (Business Day), Newsquawk."), ("b", "Fonti: Rigzone (Bloomberg); chiusure del Brent future (FMP)."),
             ("c", "Fonti: SoldiOnline (testo ANSA)."), ("d", "Fonti: comunicato Nvidia (SEC), Aju Press."), ("e", "Fonti: Il Sole 24 Ore."),
             ("f", "Fonti: MF, Kitco."), ("g", "Fonti: Investrade, Schwab."), ("h", "Fonte: FINANCIAL (finchannel)."),
             ("i", "Fonti: FMP (oro future), Alpha Vantage (EUR/USD)."), ("l", "Fonti: The Company Chronicle; chiusure dell'oro future da FMP.")]
    trovati = [p for p, _ in senza(righe)]
    male += [] if trovati == ["g", "h", "l"] else [f"fonte riconoscibile: senza fonte riconoscibile {trovati} (attesi g, h, l)"]
    # l'avviso nel controllo dei fatti, sull'edizione vera del 23/11 (oro con soli Investrade e Schwab): avviso, non errore
    ed = os.path.join(lav, "ed23")
    shutil.rmtree(ed, ignore_errors=True); os.makedirs(ed)
    for f in ("edizione.py", "dati.json", "contesto.json"):
        if os.path.exists(os.path.join(R, "sorgenti", "2026-11-23", f)):
            shutil.copy(os.path.join(R, "sorgenti", "2026-11-23", f), ed)
    shutil.copy(os.path.join(ed, "edizione.py"), os.path.join(ed, "edizione_2026-11-23.py"))
    shutil.copy(os.path.join(R, "fatti", "2026-11-23.json"), os.path.join(ed, "fatti.json"))
    rc, out23 = esegui([sys.executable, os.path.join(R, "controlli_fatti.py"), os.path.join(ed, "fatti.json"),
                        os.path.join(REPO, "edizioni.json"), "2026-11-23"], cwd=ed)
    avv = [l for l in out23.splitlines() if l.startswith("AVVISO: approfondimento")]
    male += [] if len(avv) == 1 and " oro:" in avv[0] and rc == 0 else [f"avviso fonte riconoscibile: {avv} (uscita {rc})"]
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
    """controlli_dati.py su una serie dell'Euro Stoxx 50 scritta in otto modi: EODHD è sempre una delle due fonti (salvo
    eodhd_nd, e allora da solo vale stoxx.com), le fonti non ammesse e le fonti discordi fermano il dato (APP_DATI §2b e §6; caso del 19/11/2026). Più
    due casi sull'età del dato, contata in giorni di uscita (APP_FESTIVI §2)."""
    lav = os.path.join(TMP, "dati")
    os.makedirs(lav, exist_ok=True)
    ultimi = [[d, v, None] for d, v in reversed(serie("sx5e", "2026-11-20"))]
    v0 = ultimi[0][1]
    casi = [("EODHD + dpa-AFX concordi", {"fonte": "EODHD + dpa-AFX", "seconda_fonte": v0}, True),
            ("EODHD da solo", {"fonte": "EODHD", "fonte_singola": True}, True),
            ("EODHD giù, due fonti web", {"fonte": "stoxx.com + dpa-AFX", "seconda_fonte": v0, "eodhd_nd": "non risponde"}, True),
            ("senza EODHD", {"fonte": "dpa-AFX", "fonte_singola": True}, False),
            ("EODHD giù, solo dpa-AFX", {"fonte": "dpa-AFX", "fonte_singola": True, "eodhd_nd": "non risponde"}, False),
            ("EODHD giù, solo stoxx.com", {"fonte": "stoxx.com", "fonte_singola": True, "eodhd_nd": "non risponde"}, True),
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
    # Kospi e Hang Seng (G-41): le chiusure arrivano da EODHD ogni mattina (APP_DATI §2b), con il ripiego se il connettore non
    # risponde; una chiusura EODHD diversa dall'archivio si ferma, come una riga a indice fermo, una data futura o una riga di
    # oggi presa da EODHD. Il giorno dopo una festa di quella borsa (calendario in giorni.py) il livello ricavato parte
    # dall'ultima seduta vera e il controllo lo dice; il martedì in cui EODHD non ha ancora la chiusura di lunedì niente
    # livello ricavato da venerdì: chiede la chiusura che manca, con la sua data. Gira in una copia del kit con un archivio
    # suo, così non dipende dalle chiusure che pubblica.sh aggiunge ogni giorno.
    asia = os.path.join(TMP, "dati_asia")
    kit(asia)
    with open(os.path.join(asia, "chiusure.csv"), "w", encoding="utf-8") as fa:
        fa.write("serie,data,valore\nHang Seng,2026-11-20,22410.8\nHang Seng,2026-11-23,22383.75\n"
                 "Kospi,2026-11-20,4869.96\nKospi,2026-11-23,4708.54\n")
    fk = os.path.join(asia, "dati.json")
    ks = {"mercato": "KR", "tipo": "intraday", "var": 1.2, "ora": "08:10"}
    hk = {"mercato": "HK", "tipo": "chiusura"}
    natale = [["2026-12-24", 5000.0, None], ["2026-12-23", 4950.0, None]]
    for nome, giorno, serie_, passa, deve_dire, non_deve in (
            ("Seul e Hong Kong da EODHD", "2026-11-24", {"Kospi": dict(ks, fonte="EODHD + Teleborsa", ultimi=[["2026-11-23", 4708.54, None], ["2026-11-20", 4869.96, None]]),
                                                         "Hang Seng": dict(hk, fonte="EODHD", ultimi=[["2026-11-23", 22383.74, None], ["2026-11-20", 22410.8, None]])}, True, "", "AVVISO: Kospi"),
            ("Seul senza EODHD", "2026-11-24", {"Kospi": dict(ks, fonte="Teleborsa", ultimi=[])}, False, "mancano le chiusure di EODHD", "zzz"),
            ("Seul con EODHD giù", "2026-11-24", {"Kospi": dict(ks, fonte="Teleborsa", ultimi=[], eodhd_nd="non risponde")}, True, "", "zzz"),
            ("eodhd_nd scritto in fonte", "2026-11-24", {"Kospi": dict(ks, fonte="Teleborsa, eodhd_nd", ultimi=[["2026-11-23", 4708.54, None]])}, False, "mancano le chiusure di EODHD", "zzz"),
            ("Hong Kong diversa dall'archivio", "2026-11-24", {"Hang Seng": dict(hk, fonte="EODHD", ultimi=[["2026-11-23", 22483.74, None], ["2026-11-20", 22410.8, None]])}, False, "in archivio", "zzz"),
            ("Seul il lunedì dopo Natale", "2026-12-28", {"Kospi": dict(ks, fonte="EODHD + Teleborsa", ultimi=natale)}, True,
             "AVVISO: Kospi: livello ricavato dall'ultima seduta, del 2026-12-24: borsa chiusa per festa il 2026-12-25", "zzz"),
            ("Seul il martedì con EODHD in ritardo", "2026-12-15", {"Kospi": dict(ks, fonte="EODHD + Teleborsa", ultimi=[["2026-12-11", 5000.0, None], ["2026-12-10", 4990.0, None]])}, False,
             "manca la chiusura del 14/12, giorno di borsa", "chiusa per festa"),
            ("Seul con EODHD giù e archivio indietro", "2026-11-26", {"Kospi": dict(ks, fonte="Teleborsa", ultimi=[], eodhd_nd="non risponde")}, False,
             "manca la chiusura del 24/11, giorno di borsa", "da EODHD"),
            ("riga EODHD a indice fermo a Natale", "2026-12-28", {"Kospi": dict(ks, fonte="EODHD + Teleborsa", ultimi=[["2026-12-25", 5000.0, None]] + natale)}, False,
             "riga del 2026-12-25, ma quel giorno la borsa era chiusa", "zzz"),
            ("data dopo oggi", "2026-12-28", {"Kospi": dict(ks, fonte="EODHD + Teleborsa", ultimi=[["2026-12-29", 5000.0, None]] + natale)}, False, "una data dopo oggi", "zzz"),
            ("riga di oggi presa da EODHD", "2026-11-24", {"Kospi": dict(ks, tipo="chiusura", fonte="EODHD", var=None, ultimi=[["2026-11-24", 4800.0, None], ["2026-11-23", 4708.54, None]])}, False,
             "riga di oggi con la sola fonte EODHD", "zzz")):
        dati = {"oggi": giorno, "ora_roma": "09:05", "macro": [], "serie": serie_}
        json.dump(dati, open(fk, "w", encoding="utf-8"), ensure_ascii=False)
        out = esegui([sys.executable, os.path.join(asia, "controlli_dati.py"), fk])[1]
        fermo = any(l.startswith(("- Kospi:", "- Hang Seng:")) and "indice principale assente" not in l and "manca la serie" not in l
                    for l in out.splitlines())                    # la serie assente dal caso non conta
        if fermo == passa or deve_dire not in out or non_deve in out:
            sbagliati.append(nome)
    esito("Dati: fonti dell'Euro Stoxx 50, di Seul e di Hong Kong", not sbagliati,
          f"{len(casi)} casi (EODHD sempre tra le due fonti, quotazioni dei riquadri e fonti discordi fermate), età del dato "
          "contata in giorni di uscita, borsa asiatica ferma a ieri segnalata, Seul e Hong Kong da EODHD (anche il giorno "
          "dopo una festa di quella borsa; EODHD in ritardo, righe a indice fermo, date future e riga di oggi fermate)"
          if not sbagliati else "sbagliati: " + ", ".join(sbagliati))


# ---------------------------------------------------------------- 3c. tabelle di pag. 5 calcolate dal codice
def passo_testata():
    """La nota dei dati in testata non si sovrappone mai allo slogan (G-46: #035 del 27/11, 144 caratteri). Corta, sta a destra
    dello slogan in corpo 7; troppo lunga, lo slogan le lascia la riga; oltre la riga intera il corpo scende, non sotto 5,5.
    Le note di tutte le edizioni archiviate prima della #035 restano come erano (slogan visibile)."""
    sys.path.insert(0, R)
    import gommberg_engine as E
    f = getattr(E, "testata_dati", None)
    note = {g: re.search(r'^NOTA_DATI = "(.*)"', open(p, encoding="utf-8").read(), re.M).group(1)
            for p in sorted(glob.glob(os.path.join(R, "sorgenti", "20*", "edizione.py")))
            for g in [os.path.basename(os.path.dirname(p))] if g < "2026-11-27"}
    v35 = "Chiusure al 26 novembre per Europa e Asia di ieri, al 27 novembre per Tokyo, Hong Kong e Seul; Stati Uniti fermi al 25 novembre (Ringraziamento)"
    male = ["manca testata_dati nel motore"] if not f else []
    if f:
        male += [f"{g}: slogan tolto o corpo cambiato" for g, n in note.items() if f(n) != (True, 7)]
        male += [] if f(v35) == (False, 7) else [f"nota della #035: {f(v35)} (atteso slogan tolto, corpo 7)"]
        lunga = f(v35 * 2)
        male += [] if not lunga[0] and 5.5 <= lunga[1] < 7 else [f"nota lunghissima: {lunga}"]
    esito("Testata: la nota dei dati non copre lo slogan", not male,
          f"{len(note)} note archiviate invariate, nota della #035 al posto dello slogan, nota lunghissima in corpo ridotto"
          if not male else "; ".join(male)[:300])


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
    # Il giorno dopo una festa di quella borsa (G-41): il livello ricavato parte dall'ultima seduta vera, scritta in "ultimi"
    # con la sua data (EODHD, APP_DATI §2b), non dal giorno feriale prima, che non è una seduta (lunedì 28/12: Seul è ferma
    # al 24/12; lunedì 4/1: al 30/12). Senza quella chiusura il messaggio chiede l'ultima chiusura con la sua data, mai un
    # giorno preciso; una chiusura più vecchia trovata solo in archivio, o smentita da una più recente, non basta.
    def festa(oggi, kospi, **altre):
        dd = {"oggi": oggi, "serie": {"Kospi": dict({"mercato": "KR", "tipo": "intraday", "ora": "08:10", "fonte": "EODHD + Teleborsa",
                                                      "etichette": ["Kospi"]}, **kospi), **altre}}
        ff = os.path.join(lav, f"festa_{len(os.listdir(lav))}.json")
        json.dump(dd, open(ff, "w", encoding="utf-8"))
        tt = N.tabelle_da_dati(ff, archivio={}, silenzioso=True)
        return {r[0]: r for _, rr in tt["cruscotto"] for r in rr}, tt["mancanti"]
    rif_k = {"2026-12-21": 4900.0, "2025-12-31": 4214.17}
    hk = {"mercato": "HK", "tipo": "chiusura", "ultimi": [["2026-12-24", 22000.0, None], ["2026-12-23", 21900.0, None]],
          "rif": {"2026-12-17": 21800.0, "2025-12-31": 25630.55}}
    for nome, oggi, kospi, livello in (
            ("Natale", "2026-12-28", {"var": 1.0, "ultimi": [["2026-12-24", 5000.0, None], ["2026-12-23", 4950.0, None]], "rif": rif_k}, "~5.050"),
            ("Capodanno", "2027-01-04", {"var": -0.5, "ultimi": [["2026-12-30", 5000.0, None]], "rif": rif_k}, "~4.975")):
        rr, manca = festa(oggi, kospi, **({"Hang Seng": hk} if nome == "Natale" else {}))
        if (rr.get("Kospi*") or ["", ""])[1] != livello or (nome == "Natale" and (rr.get("Hang Seng") or ["", ""])[1] != "22.000,00"):
            male.append(f"dopo {nome}: livello di Seul dall'ultima seduta vera, {livello}: {rr.get('Kospi*')}, {rr.get('Hang Seng')}")
    # base solo in archivio: vale anch'essa, perché il calendario dice che in mezzo c'era solo Natale
    rr, _ = festa("2026-12-28", {"var": 1.0, "ultimi": [], "rif": {"2026-12-24": 5000.0, **rif_k}})
    if (rr.get("Kospi*") or ["", ""])[1] != "~5.050":
        male.append(f"dopo Natale, ultima chiusura solo in archivio: {rr.get('Kospi*')}")
    # una riga a indice fermo (EODHD la scrive il giorno di festa) non è una seduta: il livello parte dal 24/12
    rr, _ = festa("2026-12-28", {"var": 1.0, "ultimi": [["2026-12-25", 4990.0, None]] + [["2026-12-24", 5000.0, None]], "rif": rif_k})
    if (rr.get("Kospi*") or ["", ""])[1] != "~5.050":
        male.append(f"riga a indice fermo il 25/12 presa per una seduta: {rr.get('Kospi*')}")
    for nome, oggi, kospi, chiede in (
            ("EODHD in ritardo (martedì, manca lunedì)", "2026-12-15", {"var": 1.0, "ultimi": [["2026-12-11", 5000.0, None], ["2026-12-10", 4990.0, None]]}, "del 14/12"),
            ("smentita da una più recente", "2026-12-28", {"var": 1.0, "ultimi": [["2026-12-22", 5000.0, None]], "rif": {"2026-12-23": 5010.0}}, "del 24/12"),
            ("vecchia di settimane", "2026-12-28", {"var": 1.0, "ultimi": [["2026-12-01", 5000.0, None]]}, "del 2/12"),
            ("oltre il calendario verificato", "2027-02-10", {"var": 1.0, "ultimi": [["2027-02-05", 5000.0, None]]}, "calendario delle feste")):
        rr, manca = festa(oggi, kospi)
        msg = " ".join(m for m in manca if m.startswith("Kospi"))
        if any(k.startswith("Kospi") for k in rr) or chiede not in msg:
            male.append(f"Seul, base non certa ({nome}): la riga doveva restare fuori e chiedere la chiusura che manca: {msg[:140]}")
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
    for riga in G.calendario_in_scadenza(dt.date.today()):        # promemoria per chi tiene la macchina: non ferma nulla
        print("[leggi] " + riga[0].upper() + riga[1:])
        NOTE.append(riga.split(":")[0])
    esito("Dati: tabelle di pag. 5 calcolate dal codice", not male, "; ".join(male)[:400] or
          "numeri del 20/11 uguali al pubblicato, nessuna n.d., livello ricavato dalla variazione (anche dopo una festa di "
          "quella borsa, dall'ultima seduta vera; mai da una base non certa), archivio delle chiusure, date riga per riga con Wall Street chiusa, con "
          "Tokyo chiusa e a cavallo d'anno")


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
    # un'edizione scritta prima di G-45 non ha l'incarico del ragionamento tra i sorgenti: il ragionamento si salta con un
    # avviso (pubblica.sh archivia coerenza_incarico.json e coerenza.json dal quarto giro di G-45, 27/11)
    prima_g45 = not os.path.exists(os.path.join(src, "coerenza_incarico.json"))
    stato, out = controlli(lav, r["pdf"], n, senza_indice=not any(v["data"] == data for v in voci),
                           env_extra={"GTD_SENZA_RAGIONAMENTO": "1"} if prima_g45 else None)
    if prima_g45:
        print(f"[avviso] Ultima edizione ({data}): scritta senza coerenza_incarico.json (prima di G-45), ragionamento non giudicato")
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


def passo_impara(copia):
    """Impara cresce con le edizioni (G-54): il filtro di impara.py su un mondo costruito, i guasti degli ingressi e
    i dati veri. Ogni caso viene da un difetto trovato (collaudo indipendente del 27/11) e ferma il codice di prima."""
    sys.path.insert(0, R)
    import impara
    mondo, male = os.path.join(TMP, "impara"), []
    os.makedirs(os.path.join(mondo, "redazione"), exist_ok=True)
    os.makedirs(os.path.join(mondo, "dati"), exist_ok=True)
    js = lambda rel, o: json.dump(o, open(os.path.join(mondo, rel), "w", encoding="utf-8"), ensure_ascii=False)
    VIX = "Misura quanta agitazione si aspetta il mercato sull'S&P 500: per questo è detto 'indice della paura'."
    js("redazione/glossario.json", {"voci": [{"sigla": "PPI", "breve": "prezzi alla produzione"},
                                             {"sigla": "VIX", "breve": "volatilità attesa sull'S&P 500"}]})
    js("redazione/glossario_sito.json", {"voci": {"VIX": {"spiega": VIX}}})
    js("edizioni.json", [{"numero": n, "data": f"2026-01-0{n}"} for n in (1, 2, 3)])
    def arch(*ed, fuori=None, conf=None):
        js(impara.CURA, {"stesse": {"Correzione": ["Correzioni di borsa"]}, "fuori": fuori or {}, "confermate": conf or {},
                         "archivio": {f"2026-01-0{n}": p for n, p in ed}})
    def giro(caso):
        try:
            r = tuple(impara.calcola(mondo))
            return r + ({},) * (4 - len(r))
        except Exception as e:  # noqa: BLE001 - il codice di prima non ha le stesse uscite: è un caso fallito, non un crash
            male.append(f"{caso}: {type(e).__name__} {str(e)[:60]}")
            return [], {}, [], {}
    verdetto = lambda occ, parola, n: next((o.get("verdetto", "") for o in occ if o["parola"] == parola and o["numero"] == n), "")
    C1 = ("Correzione", "Un calo di almeno il 10% di un indice dal suo ultimo massimo.")
    C2 = ("Correzioni di borsa", "Un calo dell'indice di almeno il 10% dal massimo più recente.")
    arch((1, [C1, ("Shutdown", "La sospensione dei fondi federali americani per mancanza di un bilancio.")]),
         (2, [("Prezzi alla produzione", "L'indice dei prezzi incassati dalle imprese che producono beni.")]))
    voci, alias, _, _ = giro("una volta sola")
    if voci:
        male.append(f"una parola spiegata una volta sola non deve entrare ({[v['sigla'] for v in voci]})")
    if alias.get("Prezzi alla produzione") != "PPI":
        male.append("la parola di una scheda scritta a mano deve portare lì")
    # due significati diversi con le parole in comune (il premio per il rischio): senza conferma a mano non entra nulla
    P1 = ("Premio di rischio", "Il rendimento in più che gli investitori chiedono per prestare a chi è più rischioso.")
    P2 = ("Premio per il rischio", "Il sovrapprezzo che il mercato paga per il rischio di una guerra che ferma le forniture di petrolio.")
    arch((1, [C1, P1]), (2, [C2, P2]), (3, [("Correzione", "Il calo di oggi porta l'indice al 10% sotto il massimo.")]))
    voci, alias, occ, gruppi = giro("due significati")
    if voci or (gruppi.get("Premio per il rischio") or {}).get("stato") != "pronta" or "pronta" not in verdetto(occ, "Correzioni di borsa", 2):
        male.append(f"due spiegazioni in due edizioni, senza conferma: pronte, non in pagina ({[v['sigla'] for v in voci]})")
    if "del giorno" not in verdetto(occ, "Correzione", 3):
        male.append("la frase del giorno resta fuori")
    DEF = {"breve": "un calo di almeno il 10% dal massimo", "spiega": "Un calo di almeno il 10% dall'ultimo massimo, rivisto a mano."}
    arch((1, [C1, P1]), (2, [C2, P2]), conf={"Correzione": DEF})
    voci, alias, _, _ = giro("confermata")
    if [(v["sigla"], v["spiega"], v["da"]) for v in voci] != [("Correzione", DEF["spiega"], 2)] or alias.get("Correzioni di borsa") != "Correzione":
        male.append(f"confermata a mano: entra con la definizione confermata, non con quella del giornale ({voci})")
    # i doppioni: "Indice della paura" è il VIX (lo dice la sua scheda) e va segnalato a chi conferma
    arch((1, [("Indice della paura", "Misura quanto gli operatori si aspettano che l'S&P 500 si muova nel mese.")]))
    _, _, _, gruppi = giro("doppioni")
    if not any(d.startswith("VIX ") for d in (gruppi.get("Indice della paura") or {}).get("doppioni", [])):
        male.append("Indice della paura: il possibile doppione del VIX va segnalato nella proposta")
    # "fuori" vale per qualunque nome: "Freno automatico (sidecar)" è il Sidecar tolto a mano
    S1 = ("Sidecar", "Una pausa di pochi minuti negli scambi automatici quando un indice si muove troppo.")
    S2 = ("Freno automatico (sidecar)", "Sospende per qualche minuto gli ordini dei programmi quando il mercato corre troppo.")
    arch((1, [S1]), (2, [S2]), fuori={"Sidecar": "prova"})
    voci, _, occ, _ = giro("fuori per nome")
    if voci or not verdetto(occ, S2[0], 2).startswith("non entra: tolta a mano"):
        male.append(f"fuori 'Sidecar' deve togliere anche 'Freno automatico (sidecar)' ({verdetto(occ, S2[0], 2)[:60]})")
    # il messaggio giusto: due edizioni ma una sola spiegazione valida (Circuit breaker), non "non compatibile"
    arch((1, [("Circuit breaker", "Sospensione automatica degli scambi quando un indice scende oltre una soglia.")]),
         (2, [("Circuit breaker", "Sospensione automatica degli scambi: lunedì a San Paolo è durata 30 minuti.")]))
    _, _, occ, _ = giro("messaggio")
    if "unica spiegazione valida" not in verdetto(occ, "Circuit breaker", 1):
        male.append(f"Circuit breaker: il motivo è che resta una sola spiegazione valida ({verdetto(occ, 'Circuit breaker', 1)[:60]})")
    # un nome sbagliato in "confermate" (o una data sbagliata in "fuori"): avviso e nessuna scrittura, la scheda non sparisce
    for caso, kw in (("confermate con un nome sbagliato", {"conf": {"Correzione": DEF, "Corezione": DEF}}),
                     ("fuori con una data sbagliata", {"conf": {"Correzione": DEF}, "fuori": {"Correzione|2026-01-09": "prova"}})):
        arch((1, [C1]), (2, [C2]), **kw)
        try:
            impara.calcola(mondo)
            male.append(f"{caso}: il passaggio deve fermarsi con un avviso, non togliere la scheda in silenzio")
        except Exception as e:  # noqa: BLE001
            if type(e).__name__ != "Fermo":
                male.append(f"{caso}: {type(e).__name__} {str(e)[:60]}")
    # gli ingressi: se uno manca o non si legge, Fermo e nessuna scrittura (né voci in meno, né doppioni)
    arch((1, [C1]), (2, [C2]), conf={"Correzione": DEF})
    uscita = os.path.join(mondo, impara.FILE)
    open(uscita, "w").write("COM'ERA")
    os.makedirs(os.path.join(mondo, "redazione", "sorgenti", "2026-01-03"), exist_ok=True)
    guasti = (("parole_giornale.json mancante", impara.CURA, None), ("glossario.json illeggibile", "redazione/glossario.json", "{ rotto"),
              ("glossario_sito.json illeggibile", "redazione/glossario_sito.json", "{ rotto"),
              ("sorgente rotto", "redazione/sorgenti/2026-01-03/edizione.py", "E = {'parole': [("),
              ("parole non nella forma", "redazione/sorgenti/2026-01-03/edizione.py", "E = {'parole': [(None, 3)]}"))
    for caso, rel, testo in guasti:
        p = os.path.join(mondo, rel)
        prima = open(p, encoding="utf-8").read() if os.path.exists(p) else None
        if testo is None:
            os.remove(p)
        else:
            open(p, "w", encoding="utf-8").write(testo)
        try:
            impara.scrivi(mondo)
            fermo = False
        except Exception as e:  # noqa: BLE001
            fermo = type(e).__name__ == "Fermo"
        if not fermo or open(uscita).read() != "COM'ERA":
            male.append(f"{caso}: il passaggio si ferma con un avviso senza scrivere nulla")
        if prima is None:
            os.remove(p)
        else:
            open(p, "w", encoding="utf-8").write(prima)
    # il guasto nella catena vera: pagine.py resta verde, avvisa, e dati/parole.json resta com'era
    p, cura = os.path.join(copia, "dati", "parole.json"), os.path.join(copia, impara.CURA)
    prima, testo = open(p, encoding="utf-8").read(), open(cura, encoding="utf-8").read()
    os.remove(cura)
    rc, out = esegui([sys.executable, os.path.join(copia, "redazione", "pagine.py"), copia])
    open(cura, "w", encoding="utf-8").write(testo)
    if rc or "AVVISO: parole di Impara" not in out or open(p, encoding="utf-8").read() != prima:
        male.append(f"senza parole_giornale.json pagine.py resta verde, avvisa e lascia dati/parole.json com'era (uscita {rc})")
    # i dati veri: ingressi leggibili, ogni conferma usata, i sinonimi noti uniti
    try:
        voci, alias, _, gruppi = impara.calcola(copia)
        conf = json.load(open(cura, encoding="utf-8")).get("confermate") or {}
        orfane = [c for c in conf if (gruppi.get(c) or {}).get("stato") != "confermata"]
        if orfane:
            male.append(f"confermate senza una parola delle edizioni, o vinte da una scheda scritta: {orfane}")
        if alias.get("Indice della paura") != "VIX":
            male.append("Indice della paura deve portare alla scheda del VIX")
        for a, b in (("Riserva minima delle banche", "Riserva obbligatoria"), ("Rialzo da 50 punti base", "Rialzo da mezzo punto")):
            if a not in (gruppi.get(b) or {}).get("varianti", []):
                male.append(f"{a} deve stare con {b}")
        pronte = sum(1 for i in gruppi.values() if i["stato"] == "pronta")
    except Exception as e:  # noqa: BLE001
        male.append(f"dati veri: {type(e).__name__} {str(e)[:100]}")
        voci, pronte = [], 0
    esito("Sito: Impara cresce con le edizioni", not male, "; ".join(male)[:300] or
          f"{len(voci)} schede dalle edizioni, tutte confermate a mano; {pronte} parole pronte aspettano la conferma "
          f"(impara.py --proposte); nulla entra senza conferma, fuori vale per ogni nome, i doppioni si segnalano, "
          f"un ingresso rotto ferma il passaggio senza scrivere e non ferma l'edizione")


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
    # finti sorgenti: devono finire in redazione/sorgenti/, anche incarico e risposta del ragionamento (G-45)
    for nome in (f"edizione_{v['data']}.py", "dati.json", "coerenza_incarico.json", "coerenza.json"):
        open(os.path.join(lav, nome), "w").write("{}")
    pdf = os.path.join(lav, "copia.pdf")
    shutil.copy(os.path.join(copia, v["file"]), pdf)
    rc, out = esegui(["bash", os.path.join(copia, "redazione", "pubblica.sh"), pdf, str(v["numero"]), v["data"],
                      os.path.join(lav, "fatti.json")], env={"GTD_REPO": copia, "GTD_PROVA": "1"})
    srg = os.path.join(copia, "redazione", "sorgenti", v["data"])
    ok = rc == 0 and "Sito: PROVA - nessun push" in out and "git push origin main" in out \
        and all(os.path.exists(os.path.join(srg, f)) for f in ("edizione.py", "dati.json", "coerenza_incarico.json", "coerenza.json"))
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
        passo_coerenza()
        passo_fonti()
        passo_dati()
        passo_tabelle()
        passo_testata()
        passo_scommessa()
        passo_newsletter()
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
            passo_impara(copia)
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
