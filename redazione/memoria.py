"""Memoria della redazione: ciò che abbiamo già schedato e verificato nelle edizioni precedenti, pronto da riusare.
Legge redazione/fatti/AAAA-MM-GG.json (le schede archiviate da pubblica.sh) ed edizioni.json. Nessuna chiamata web.
Serve a due cose: la profondità (precedenti, cronologia, numeri già verificati di un tema) e il risparmio (un evento
d'agenda o un fatto di contesto già schedato non si cerca di nuovo).

Uso:
  python3 memoria.py riepilogo [AAAA-MM-GG]            una riga per prepara.sh
  python3 memoria.py agenda [AAAA-MM-GG] [--json F]    eventi futuri già schedati (ora, consenso, fonte)
  python3 memoria.py tema <parola> [<parola>...] [--giorni 45] [--json F]
                                                       fatti già schedati che contengono ALMENO una delle parole,
                                                       gli approfondimenti già usciti sul tema (da non ripetere) e i
                                                       meccanismi di meccanismi.json che spiegano il passaggio
--json F scrive le schede trovate, pronte da unire a fatti.json: id "MEM-<mmgg>-<id d'origine>", "ripresa" = edizione d'origine, esito del
revisore conservato. Una scheda ripresa vale come le altre per i controlli; nel testo è contesto, mai notizia del giorno.
Variabile: GTD_REPO (default /home/claude/gtd)."""
import datetime as dt, glob, json, os, sys, unicodedata

REPO = os.environ.get("GTD_REPO", "/home/claude/gtd")
if not os.path.isdir(os.path.join(REPO, "redazione", "fatti")):
    REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
REGISTRI = {"anomalia", "prime_pagine", "ricerca", "scaletta"}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(s.split())


def archivio(dal, al=None):
    """[(giorno, scheda)] dal più recente, senza registri, scartate ed esiti negativi del revisore."""
    out = []
    for p in sorted(glob.glob(os.path.join(REPO, "redazione", "fatti", "20*.json")), reverse=True):
        try:
            g = dt.date.fromisoformat(os.path.basename(p)[:10])
            schede = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if g < dal or (al and g >= al):
            continue
        for s in schede:
            if (isinstance(s, dict) and s.get("testo") and s.get("data_evento") and s.get("fonti")
                    and s.get("sezione") not in REGISTRI and not s.get("scartata")
                    and s.get("verifica") in (None, "confermato") and not s.get("correzione")):
                out.append((g, s))
    return out


def testata(s):
    f = (s.get("fonti") or [{}])[0]
    return f.get("testata") or "?"


def unici(coppie):
    visti, out = set(), []
    for g, s in coppie:
        k = (s["data_evento"], norm(s["testo"])[:60])
        if k not in visti:
            visti.add(k); out.append((g, s))
    return out


def esporta(coppie, percorso):
    schede = []
    for g, s in coppie:
        c = dict(s); c["id"] = f"MEM-{g:%m%d}-{s.get('id', 'x')}"; c["ripresa"] = g.isoformat()
        schede.append(c)
    json.dump(schede, open(percorso, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Scritte {len(schede)} schede in {percorso}: uniscile a fatti.json (id MEM..), tieni solo quelle che usi")


def riga(g, s, k=190):
    t = " ".join(s["testo"].split())
    t = t if len(t) <= k else t[:k - 3] + "..."
    v = "verificata" if s.get("verifica") == "confermato" else "da riverificare se regge una tesi"
    return f"{s['data_evento'][8:]}/{s['data_evento'][5:7]} | {t} | {testata(s)}, ed. {g:%d/%m} | {v}"


def eventi_futuri(oggi):
    c = [(g, s) for g, s in archivio(oggi - dt.timedelta(days=10), oggi)
         if s.get("sezione") == "agenda" and s["data_evento"] >= oggi.isoformat()]
    return sorted(unici(c), key=lambda x: x[1]["data_evento"])


def approfondimenti(dal):
    try:
        voci = json.load(open(os.path.join(REPO, "edizioni.json"), encoding="utf-8"))
    except Exception:
        return []
    out = []
    for v in sorted(voci, key=lambda x: x["numero"], reverse=True):
        if v.get("data", "") < dal.isoformat():
            continue
        for a in v.get("approfondimenti") or []:
            out.append((v["numero"], v["data"], a.get("tema") or "", a.get("titolo") or ""))
    return out


def meccanismi(parole, quanti=2):
    """I meccanismi di meccanismi.json che toccano il tema: la spiegazione già verificata del passaggio (perché A muove B),
    da dire con le parole del lettore. Prima quelli col tema nel titolo, poi per numero di parole trovate."""
    try:
        voci = json.load(open(os.path.join(REPO, "redazione", "meccanismi.json"), encoding="utf-8"))["voci"]
    except Exception:
        return []
    trovati = []
    for v in voci:
        tit, base = norm(v["titolo"]), norm(" ".join(v.get(k, "") for k in ("titolo", "testo", "quando")))
        n = sum(1 for p in parole if p in base)
        if n:
            trovati.append((-sum(1 for p in parole if p in tit), -n, v["id"], v))
    return [v for *_, v in sorted(trovati, key=lambda x: x[:3])[:quanti]]


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    js = a[a.index("--json") + 1] if "--json" in a else None
    giorni = int(a[a.index("--giorni") + 1]) if "--giorni" in a else 45
    for opz in ("--json", "--giorni"):
        if opz in a:
            i = a.index(opz); del a[i:i + 2]
    cmd, resto = a[0], a[1:]
    date = [x for x in resto if len(x) == 10 and x[4] == "-" and x[7] == "-"]
    oggi = dt.date.fromisoformat(date[0]) if date else dt.date.today()

    if cmd == "riepilogo":
        ev = eventi_futuri(oggi)
        app = approfondimenti(oggi - dt.timedelta(days=9))[:6]
        print(f"Memoria: {len(ev)} eventi futuri già schedati (memoria.py agenda) | approfondimenti recenti: "
              + ("; ".join(f"{t} {d[8:]}/{d[5:7]}" for _, d, t, _ in app) or "-")
              + " | per ogni tesi: memoria.py tema <parole> | storie in corso: memoria.py storie")
    elif cmd == "storie":
        voci = json.load(open(os.path.join(REPO, "edizioni.json"), encoding="utf-8"))
        prec = [v for v in voci if v.get("data", "") < oggi.isoformat() and v.get("termometri")]
        if not prec:
            print("Memoria, storie in corso: nessun termometro archiviato: si scrivono da zero"); return
        v = prec[-1]
        print(f"Memoria, storie in corso (termometri del n. {v['numero']}, {v['data']}): si aggiornano, non si "
              "riscrivono; una storia ferma da 3 edizioni va in 'fermi', poi esce:")
        for r in v["termometri"].get("righe", []):
            print("  " + " | ".join(r))
        if v["termometri"].get("fermi"):
            print("  Fermi: " + v["termometri"]["fermi"])
    elif cmd == "agenda":
        ev = eventi_futuri(oggi)
        if not ev:
            print("Memoria, agenda: nessun evento futuro già schedato: il calendario si cerca per intero"); return
        print(f"Memoria, agenda: {len(ev)} eventi futuri già schedati. Si riusano; si cerca solo ciò che manca "
              "(consenso, ora esatta, eventi nuovi):")
        for g, s in ev[:16]:
            print("  " + riga(g, s, 150))
        if js:
            esporta(ev, js)
    elif cmd == "tema":
        parole = [norm(x) for x in resto if x not in date]
        if not parole:
            print("Uso: memoria.py tema <parola> [<parola>...]"); return
        dal = oggi - dt.timedelta(days=giorni)
        trovati = []
        for g, s in archivio(dal, oggi):
            if s.get("sezione") == "agenda":
                continue
            base = norm(s["testo"] + " " + " ".join(f.get("citazione") or "" for f in s.get("fonti") or []))
            if any(p in base for p in parole):
                trovati.append((g, s))
        trovati = sorted(unici(trovati), key=lambda x: x[1]["data_evento"], reverse=True)
        usciti = [x for x in approfondimenti(dal) if any(p in norm(x[2] + " " + x[3]) for p in parole)]
        if usciti:
            print("Già scritto (la tesi di oggi parte da qui e va oltre, non si ripete):")
            for n, d, t, tit in usciti[:5]:
                print(f"  #{n:03d} {d[8:]}/{d[5:7]} {t}: {tit}")
        mecc = meccanismi(parole)
        if mecc:
            print("Meccanismi che POSSONO servire al passaggio (meccanismi.json). Si usa solo quello che spiega QUESTA tesi, "
                  "con le parole del lettore e come tendenza ('di solito'); uno che non c'entra o che va contro la tesi "
                  "confonde: meglio nessuno. L'id di quelli usati va in C[\"meccanismi\"]:")
            for v in mecc:
                ecc = v.get("eccezioni", "-")
                print(f"  {v['id']} {v['titolo']} (serve per: {v.get('quando', '-')[:90]}): {v['testo'][:240]} | Non vale se: "
                      f"{ecc[:120]}{'...' if len(ecc) > 120 else ''}")
        if not trovati:
            print("Memoria, tema: nessun fatto già schedato con queste parole"); return
        print(f"Memoria, tema: {len(trovati)} fatti già schedati (i più recenti prima). Sono contesto e precedenti, "
              "mai la notizia di oggi:")
        for g, s in trovati[:14]:
            print("  " + riga(g, s))
        if js:
            esporta(trovati[:14], js)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
