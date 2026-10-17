"""Aggiunge a edizioni.json la voce v6 dell'edizione, senza numeri copiati a mano.
Uso:
  python3 edizioni_voce.py --pdf <pdf> --data AAAA-MM-GG --voce voce.json --registro <pronostici/LUNEDI-settimana.json>
         (--stato stato.json | --verdetto verdetto.json | --senza-scommessa) [--sigle sigle.json]
         [--edizioni /home/claude/gtd/edizioni.json] [--uscita altro.json]
voce.json (piccolo, scritto dalla redazione):
  {"titolo": "<h1>", "sommario": ["<3 punti di In 30 secondi>"], "notizie": ["<6-8 titoli>"],
   "temi": ["Fed", "Chip", ...], "approfondimenti": [{"tema": "Tassi", "titolo": "...", "formato": "grafico"}],
   "meccanismi": ["M05"], "parole": ["term premium"], "termometri": [["Fed/tassi", "novità"], ["Iran", "fermo dal 12/10"]],
   "glossario": ["CPI", ...] (facoltativo se c'è --sigle), "errata": [] (facoltativo)}
Calcolati qui: numero (dal calendario), file, nome, pagine (pdfinfo), ticker (letto dal PDF), scommessa (da stato.json o
verdetto.json + registro), ripetizioni (controlli_ripetizioni), glossario (da --sigle, uscita json di controlli_testo).
Rifiuta: numero già presente, data già presente, campi mancanti o fuori elenco. GTD_PROVA=1: stampa la voce senza scrivere.
--sostituisci: solo per rifare la voce della STESSA mattina dopo un nuovo render, se il PDF non è ancora in pdf/ (non pubblicato)."""
import argparse, json, os, re, subprocess, sys

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
import giorni as G  # noqa: E402
import controlli_ripetizioni as CR  # noqa: E402

from controlli_temi import TEMI  # noqa: E402  (elenco chiuso unico, scritto anche in ISTRUZIONI §2)
FORMATI = {"grafico", "tabella", "due_grafici"}
DA_MISURA = {"mezzo": "grafico", "doppio": "due_grafici"}   # il motore v6 scrive la misura del modulo


def esci(msg):
    print("RIFIUTATO: " + msg); sys.exit(1)


def ticker_dal_pdf(pdf):
    """Le 7 caselle del ticker, con le stesse stringhe stampate nel PDF (pag. 1, prime righe dopo la testata)."""
    t = subprocess.run(["pdftotext", "-layout", "-f", "1", "-l", "1", pdf, "-"], capture_output=True).stdout.decode("utf-8")
    righe = [r for r in t.split("\n") if r.strip()]
    for i, r in enumerate(righe[:12]):
        celle = [c.strip() for c in re.split(r"\s{2,}", r.strip())]
        if len(celle) == 7 and i + 2 < len(righe) and all(re.search(r"\b(g|sett)\b", c) for c in
                                                            re.split(r"\s{2,}", righe[i + 2].strip())[:7]):
            val = [c.strip() for c in re.split(r"\s{2,}", righe[i + 1].strip())]
            var = [c.strip() for c in re.split(r"\s{2,}", righe[i + 2].strip())]
            if len(val) == 7 and len(var) == 7:
                return [[a, b, c] for a, b, c in zip(celle, val, var)]
    return None


def scommessa(reg, stato=None, verdetto=None):
    s = reg["strumenti"]
    direz = {k: ("su" if v["previsione_redazione"] > v["base"] else "giù") for k, v in s.items()}
    out = {"settimana": reg["settimana"], "su": len(s)}
    if stato:
        r = stato["righe"]
        out["strada"] = sum(1 for k in s if r[k]["strada_giusta"] is True)
        out["range"] = sum(1 for k in s if r[k]["dentro_range"])
        out["dettaglio"] = [[s[k]["nome"], direz[k], r[k]["strada_giusta"], r[k]["dentro_range"]] for k in s]
    else:
        out["strada"] = out["range"] = None
        out["dettaglio"] = [[s[k]["nome"], direz[k], None, None] for k in s]
    v = None
    if verdetto:
        t = verdetto["totale"]
        sett = next(iter(verdetto["righe"].values()))["settimana"]
        v = {"settimana": sett, "punti": t["punti"], "su": t["su"], "direzione": t["direzione"], "range": t["range"],
             "par": t["par"]}
    return out, v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True); ap.add_argument("--data", required=True)
    ap.add_argument("--voce", required=True); ap.add_argument("--registro")
    ap.add_argument("--stato"); ap.add_argument("--verdetto"); ap.add_argument("--senza-scommessa", action="store_true")
    ap.add_argument("--sigle"); ap.add_argument("--edizioni", default=os.path.join(os.path.dirname(QUI), "edizioni.json"))
    ap.add_argument("--dati", default="/home/claude/lavoro/dati.json", help="dati.json del giorno (data delle chiusure del ticker)")
    ap.add_argument("--uscita"); ap.add_argument("--sostituisci", action="store_true")
    a = ap.parse_args()
    import datetime as dt
    d = dt.date.fromisoformat(a.data)
    if not G.uscita(d):
        esci(f"{a.data} non è un giorno di uscita")
    n = G.numero(d)
    voci = json.load(open(a.edizioni, encoding="utf-8"))
    if a.sostituisci:
        pubblicato = os.path.exists(os.path.join(os.path.dirname(os.path.abspath(a.edizioni)), "pdf", f"{a.data}-gommberg-{n:03d}.pdf"))
        if pubblicato:
            esci("--sostituisci vietato: il PDF di questa edizione è già in pdf/ (pubblicato)")
        voci = [v for v in voci if not (v["numero"] == n and v["data"] == a.data)]
    if any(v["numero"] == n for v in voci):
        esci(f"il numero {n} esiste già in edizioni.json: numero di edizione sbagliato? Segnalalo nel messaggio finale")
    if any(v["data"] == a.data for v in voci):
        esci(f"la data {a.data} esiste già in edizioni.json")
    w = json.load(open(a.voce, encoding="utf-8"))
    for k in ("titolo", "sommario", "notizie", "temi", "approfondimenti"):
        if not w.get(k):
            esci(f"voce.json: manca {k}")
    if len(w["sommario"]) != 3:
        esci("sommario: servono esattamente 3 punti (In 30 secondi)")
    if not 1 <= len(w["notizie"]) <= 8:
        esci("notizie: da 1 a 8 titoli")
    fuori = [t for t in w["temi"] if t not in TEMI]
    if fuori or not 3 <= len(w["temi"]) <= 6:
        esci(f"temi: 3-6 tag dall'elenco chiuso {TEMI} (fuori elenco: {fuori})")
    for x in w["approfondimenti"]:
        x["formato"] = DA_MISURA.get(x.get("formato"), x.get("formato"))
        if set(x) != {"tema", "titolo", "formato"} or x["formato"] not in FORMATI:
            esci(f"approfondimento non valido: {x} (chiavi tema, titolo, formato in {sorted(FORMATI)})")
    mecc = {m["id"] for m in json.load(open(os.path.join(QUI, "meccanismi.json"), encoding="utf-8"))["voci"]}
    ignoti = [m for m in w.get("meccanismi", []) if m not in mecc]
    if ignoti:
        esci(f"meccanismi non in meccanismi.json: {ignoti}")
    testo_libero = json.dumps([w["titolo"], w["sommario"], w["notizie"], w["approfondimenti"]], ensure_ascii=False)
    if re.search(r"<[a-z/]|&amp;|[\u2013\u2014]", testo_libero):
        esci("testo con tag HTML, &amp; o trattini lunghi: scrivi testo semplice (S&P, non &amp;) e solo '-'")

    tk = ticker_dal_pdf(a.pdf)
    if not tk:
        esci("ticker non trovato nella pagina 1 del PDF")
    pagine = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", a.pdf], capture_output=True, text=True).stdout).group(1))
    punteggio, _ = CR.analizza(CR.testo_di(a.pdf))
    if a.sigle:
        gloss = json.load(open(a.sigle, encoding="utf-8")).get("glossario", [])
    else:
        gloss = w.get("glossario", [])

    voce = {"numero": n, "data": a.data, "titolo": w["titolo"], "sommario": w["sommario"],
            "file": f"pdf/{a.data}-gommberg-{n:03d}.pdf", "nome": f"{a.data} Gommberg Terminal Daily #{n:03d}.pdf",
            "pagine": pagine, "notizie": w["notizie"], "ticker": tk}
    if w.get("dek"):
        voce["dek"] = re.sub(r"<[^>]+>", "", w["dek"]).replace("&amp;", "&").strip()
    if os.path.exists(a.dati):
        import numeri as NU
        S = json.load(open(a.dati, encoding="utf-8"))["serie"]
        date = [S[n]["ultimi"][0][0] for _, n, _, _ in NU.TICKER if n in S]
        if date:
            voce["ticker_al"] = max(date)
    if not a.senza_scommessa:
        if not a.registro or not (a.stato or a.verdetto):
            esci("scommessa: servono --registro e --stato (mar-ven) o --verdetto (lunedì); oppure --senza-scommessa")
        reg = json.load(open(a.registro, encoding="utf-8"))
        st = json.load(open(a.stato, encoding="utf-8")) if a.stato and os.path.exists(a.stato) else None  # il lunedì non c'è
        ve = json.load(open(a.verdetto, encoding="utf-8")) if a.verdetto else None
        voce["scommessa"], v = scommessa(reg, st, ve)
        if v:
            voce["verdetto"] = v
        # la domanda della settimana (registro accanto a quello della scommessa) e, in settimana, a che punto è
        dp = os.path.join(os.path.dirname(os.path.abspath(a.registro)), reg["settimana"].split("/")[0] + "-domanda.json")
        if os.path.exists(dp):
            d = json.load(open(dp, encoding="utf-8"))
            voce["domanda"] = {"testo": d["testo"], "prob": d["prob_redazione"], "esito": d.get("esito")}
            ds = os.path.join(os.path.dirname(os.path.abspath(a.stato)) if a.stato else ".", "domanda_stato.json")
            if os.path.exists(ds):
                voce["domanda"]["finora"] = json.load(open(ds, encoding="utf-8")).get("finora")
    voce.update({"temi": w["temi"], "approfondimenti": w["approfondimenti"], "meccanismi": w.get("meccanismi", []),
                 "parole": w.get("parole", []), "ripetizioni": punteggio, "glossario": gloss})
    if w.get("termometri"):
        voce["termometri"] = w["termometri"]
    if w.get("errata"):
        voce["errata"] = w["errata"]

    sc = voce.get("scommessa", {})
    print(f"Voce #{n:03d} {a.data}: {pagine} pagine, {len(tk)} caselle ticker, {len(w['notizie'])} notizie, "
          f"ripetizioni {punteggio}, scommessa strada {sc.get('strada')} range {sc.get('range')} su {sc.get('su')}")
    if os.environ.get("GTD_PROVA") == "1" and not a.uscita:
        print("GTD_PROVA=1: edizioni.json NON scritto"); return
    voci.append(voce)
    dest = a.uscita or a.edizioni
    tmp = dest + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(voci, f, ensure_ascii=False, indent=1)
    os.replace(tmp, dest)
    print(f"Scritto: {dest} ({len(voci)} voci)")


if __name__ == "__main__":
    main()
