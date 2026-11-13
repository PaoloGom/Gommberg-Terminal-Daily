"""Controllo delle schede dei fatti (fonti, date, novità, esito della revisione) prima della pubblicazione.
Uso: python3 controlli_fatti.py <fatti.json> <edizioni.json> <data AAAA-MM-GG> [--prima-della-revisione]
Esce con codice 1 e l'elenco dei problemi se qualcosa non va.

Schema di fatti.json: lista di schede
{"id": "N01", "sezione": "top_story|top_news|catalizzatori|agenda|macro|deep_dive|scommessa"
   (nomi v6 ammessi: notizie=top_news, calendario=catalizzatori, termometri/lettura=macro, approfondimento=deep_dive),
 "tipo": "C" solo per una causa specifica di un movimento (la citazione deve contenere il nesso; nel PDF "(Testata)" in coda),
 "tipo": "U" per un dato ufficiale (dato macro, decisione di banca centrale, asta, comunicato): serve una fonte
   "ufficiali" di fonti.json; l'agenzia solo d'appoggio. Se il sito ufficiale non si raggiunge dopo ricerche vere:
   "ufficiale_cercato": ["ricerca 1", "ricerca 2"] e il dato esce attribuito "(Reuters)".
 "testo": "il fatto come appare nel PDF", "data_evento": "AAAA-MM-GG",
 "novita": "per un tema già uscito: qual è lo sviluppo nuovo (altrimenti null)",
 "fonti": [{"testata": "Reuters", "url": "https://...", "data_pubblicazione": "AAAA-MM-GG", "citazione": "frase originale", "ricerca": "query che ha trovato la pagina (il revisore la riusa)"}],
   in una fonte: "agenzia": "Reuters" se il sito ospita per intero un lancio d'agenzia (fonti.json "agenzie"; vale livello 1,
   nel PDF si cita l'agenzia); "primaria": true se è il documento di chi è parte del fatto (comunicato, deposito, discorso).
 "verifica": "confermato|errato|non_conclusivo" (scritto dal revisore), "nota_revisore": "..."}
Fonti "ufficiali" di fonti.json (BLS, Census, BEA, Fed, Tesoro, Eurostat, Istat, BCE, borse): valgono livello 1, bastano da
 sole. Dati pubblici certi (sezione catalizzatori, mercati, estremo): "fonte_singola": true = una sola fonte non vietata,
 dichiarata nel PDF ("-7,57% (Korea Herald)"); un dato del calendario non si toglie mai.
Registro delle anomalie (passo 2c), nella stessa lista: {"id": "A1", "sezione": "anomalia", "fatto": "PPI sopra le attese,
 10 anni -9 pb", "ricerche": ["treasury yields fall despite PPI", ...], "esito": "C03" | "non chiarita"} (lo controlla
 controlli_contenuti.py).
Scaletta (prima della ricerca mirata): {"id": "S1", "sezione": "scaletta", "moduli": [{"chiave", "tesi", "domanda", "prove": [...],
 "contro"}]} (schema completo in APP_FONTI.md §4). Schede riprese dalla memoria (memoria.py): id "MEM..", campo "ripresa"."""
import datetime as dt, json, os, re, sys
from urllib.parse import urlparse

QUI = os.path.dirname(os.path.abspath(__file__))
fatti_p, indice_p, oggi_s = sys.argv[1], sys.argv[2], sys.argv[3]
prima_revisione = "--prima-della-revisione" in sys.argv
oggi = dt.date.fromisoformat(oggi_s)
F = json.load(open(os.path.join(QUI, "fonti.json"), encoding="utf-8"))
L1, L2, NO = set(F["livello_1"]) | set(F.get("ufficiali", [])), set(F["livello_2"]), set(F["vietate"])
# dati pubblici certi (calendario macro, chiusure e movimenti di mercato): una sola fonte non vietata basta se dichiarata
PUBBLICI = {"catalizzatori", "mercati", "estremo"}


UFF = set(F.get("ufficiali", []))
AGENZIE = {a.lower() for a in F.get("agenzie", [])}


def dominio_ufficiale(url):
    h = (urlparse(url).hostname or "").lower().split(".")
    return any(".".join(h[i:]) in UFF for i in range(len(h) - 1))


def livello(url):
    h = (urlparse(url).hostname or "").lower()
    parti = h.split(".")
    for i in range(len(parti) - 1):
        d = ".".join(parti[i:])
        if d in NO:
            return 0
        if d in L1:
            return 1
        if d in L2:
            return 2
    return 3


voci = json.load(open(indice_p, encoding="utf-8"))
prec = sorted({v["data"] for v in voci if v["data"] < oggi_s})
ultima = dt.date.fromisoformat(prec[-1]) if prec else oggi - dt.timedelta(days=3)
gia_usciti = " | ".join(n for v in voci if v["data"] < oggi_s for n in v.get("notizie", [])).lower()

fatti = json.load(open(fatti_p, encoding="utf-8"))
problemi, avvisi = [], []
# v8.2: il revisore non lavora su fatti.json (vedrebbe le citazioni e le ricopierebbe, prova del 13/11). Riceve
# revisione_incarico.json (fatto e indirizzo, niente citazione) e risponde in revisione.json; qui gli esiti si uniscono.
REV_P = os.path.join(os.path.dirname(os.path.abspath(fatti_p)), "revisione.json")
if not prima_revisione and os.path.exists(REV_P):
    esiti = {str(e.get("id")): e for e in json.load(open(REV_P, encoding="utf-8")) if isinstance(e, dict)}
    for f in fatti:
        e = esiti.get(str(f.get("id")))
        if e:
            f.update({k: e[k] for k in ("trovato", "verifica", "nota_revisore") if k in e})
    json.dump(fatti, open(fatti_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Revisione: uniti {sum(1 for f in fatti if str(f.get('id')) in esiti)} esiti da revisione.json")
ids = [f.get("id") for f in fatti]
if len(ids) != len(set(ids)):
    problemi.append("id duplicati nelle schede")
tutte = fatti
fatti = [f for f in fatti if not f.get("scartata") and f.get("sezione") not in ("anomalia", "prime_pagine", "ricerca", "scaletta")]  # registri: controlli_contenuti.py
ALIAS = {"notizie": "top_news", "calendario": "catalizzatori", "termometri": "macro", "lettura": "macro",
         "approfondimento": "deep_dive", "approfondimenti": "deep_dive"}
for f in fatti:
    i, sez = f.get("id", "?"), ALIAS.get(f.get("sezione", ""), f.get("sezione", ""))
    if f.get("tipo") == "C" and not prima_revisione and f.get("verifica") is None:
        problemi.append(f"{i}: causa (tipo C) non verificata dal revisore")
    fonti = f.get("fonti") or []
    if not f.get("testo") or not f.get("data_evento"):
        problemi.append(f"{i}: mancano testo o data_evento"); continue
    if not fonti:
        problemi.append(f"{i}: nessuna fonte"); continue
    livelli, testate = [], set()
    for s in fonti:
        lv = livello(s.get("url", ""))
        if lv == 0:
            problemi.append(f"{i}: fonte vietata {s.get('url')}")
        # vale chi ha scritto, non chi ospita: lancio d'agenzia ripreso per intero, o documento di chi è parte del fatto
        elif lv > 1 and (str(s.get("agenzia") or "").strip().lower() in AGENZIE or s.get("primaria") is True):
            lv = 1
        if not s.get("url", "").startswith("http") or not s.get("citazione") or not s.get("data_pubblicazione"):
            problemi.append(f"{i}: fonte senza url, citazione o data di pubblicazione ({s.get('testata')})")
        livelli.append(lv); testate.add((s.get("testata") or s.get("url")).lower())
    if f.get("tipo") == "U" or sez == "catalizzatori":
        uff = any(dominio_ufficiale(s.get("url", "")) for s in fonti)
        if not uff:
            cercato = f.get("ufficiale_cercato") or []
            if len(cercato) >= 2:
                avvisi.append(f"{i}: dato ufficiale senza il comunicato (cercato: {'; '.join(cercato[:2])}): "
                              "nel PDF attribuito \"(Testata)\"")
            else:
                problemi.append(f"CERCA {i}: dato ufficiale senza fonte ufficiale (non si toglie): cerca il comunicato (es. \"BLS CPI September "
                                "2026 news release\", \"Eurostat flash estimate euro area inflation\") e aggiungilo alle fonti; "
                                "l'agenzia resta solo d'appoggio. Se dopo 2 ricerche vere non esce: \"ufficiale_cercato\"")
    singola = f.get("fonte_singola") and sez in PUBBLICI and 0 not in livelli
    if singola and 1 not in livelli:
        avvisi.append(f"{i}: fonte singola dichiarata ({next(iter(testate))}): nel PDF \"(Testata)\" in coda al dato")
    # fonti non in elenco (livello 3) valgono come livello 2: servono due fonti indipendenti che dicono lo stesso
    elif not (1 in livelli or sum(1 for x in livelli if x in (2, 3)) >= 2 and len(testate) >= 2):
        if sez == "catalizzatori":
            problemi.append(f"{i}: dato del calendario: cercalo alla fonte ufficiale (fonti.json \"ufficiali\") o, se impossibile, "
                            "\"fonte_singola\": true e \"(Testata)\" nel PDF; mai toglierlo")
        else:
            problemi.append(f"{i}: fonti insufficienti (serve 1 di livello 1 o 2 testate di livello 2; livelli {livelli})")
    ev = dt.date.fromisoformat(f["data_evento"])
    pubs = [dt.date.fromisoformat(s["data_pubblicazione"]) for s in fonti if s.get("data_pubblicazione")]
    if sez == "agenda":
        if ev < oggi:
            problemi.append(f"{i}: evento in agenda già passato ({ev})")
    elif sez in ("top_story", "top_news", "catalizzatori"):
        # Notizie e catalizzatori: l'evento deve essere successivo all'edizione precedente,
        # salvo uno sviluppo nuovo dichiarato e sostenuto da una fonte pubblicata dopo.
        if ev < ultima:
            if not f.get("novita"):
                problemi.append(f"{i}: evento del {ev}, non successivo all'ultima edizione ({ultima}), senza novità dichiarata")
            elif not any(p > ultima or p == oggi for p in pubs):
                problemi.append(f"{i}: novità dichiarata ma nessuna fonte pubblicata dopo l'ultima edizione")
        if pubs and max(pubs) < ev:
            problemi.append(f"{i}: le fonti sono precedenti all'evento ({max(pubs)} < {ev})")
    if pubs and max(pubs) < oggi - dt.timedelta(days=7) and sez != "deep_dive":
        avvisi.append(f"{i}: fonte più recente del {max(pubs)}, oltre 7 giorni")
    if sez in ("top_story", "top_news") and gia_usciti and f["testo"][:40].lower() in gia_usciti:
        problemi.append(f"{i}: titolo identico a una notizia già uscita")
    v = f.get("verifica")
    if not prima_revisione:
        if v == "errato":
            problemi.append(f"{i}: segnato ERRATO dal revisore: {f.get('nota_revisore', '')}")
        if v == "non_conclusivo" and sez in PUBBLICI:
            avvisi.append(f"{i}: dato pubblico non confermato dal revisore: resta con la fonte dichiarata (\"(Testata)\")")
        elif v == "non_conclusivo":
            problemi.append(f"{i}: verifica non conclusiva: togliere il fatto dal PDF o attribuirlo e ripetere la verifica")

# Revisione mirata. Fino al 10/11/2026 il controllo chiedeva un esito per ogni scheda e il revisore, con 25 verifiche a
# disposizione, segnava tutto "confermato" (221 su 221) senza riaprire gli approfondimenti. Ora l'elenco lo fa il codice,
# dalle schede dove un errore costa di più, e il revisore deve scrivere in "trovato" la frase letta sulla pagina aperta.
def _num(t):
    out = set()
    for m in re.findall(r"\d[\d.,]*\d|\d", str(t)):
        m = m.replace(",", ".") if m.count(",") == 1 and m.count(".") == 0 else m.replace(".", "").replace(",", ".") if "," in m else m
        try:
            x = float(m)
        except ValueError:
            continue
        if x >= 10 or "." in m:
            out.add(round(x, 4))
    return out


def da_rivedere(schede, registri, massimo=25):
    tesi = {x for r in registri if r.get("sezione") == "scaletta" for m in r.get("moduli") or [] for x in m.get("schede") or []}
    def classe(f):
        sez = ALIAS.get(f.get("sezione", ""), f.get("sezione", ""))
        scoperti = _num(f.get("testo")) - set().union(*[_num(s.get("citazione")) for s in f.get("fonti") or [{}]])
        return (0 if sez == "top_story" else 1 if f.get("tipo") == "C" else 2 if f.get("id") in tesi else
                3 if scoperti and sez != "agenda" else 4 if sez == "agenda" else 5 if sez == "top_news" else
                6 if sez == "catalizzatori" else 7)
    cand = [f for f in schede if not (str(f.get("id", "")).startswith("MEM") and f.get("verifica") == "confermato")]
    cand = sorted(cand, key=lambda f: (classe(f), f.get("data_evento", "")))
    return [f for f in cand if classe(f) < 7][:massimo]


def _parole(t):
    return set(re.findall(r"[a-zà-ü0-9]+", str(t).lower()))


lista = da_rivedere(fatti, tutte)
if prima_revisione:
    print("REVISIONE: " + ",".join(str(f.get("id")) for f in lista))
    inc = [{"id": f.get("id"), "fatto": f.get("testo"),
            "fonti": [{"testata": s.get("testata"), "url_da_ritrovare_con_una_ricerca": s.get("url"), "ricerca": s.get("ricerca")}
                      for s in f.get("fonti") or []]} for f in lista]
    inc_p = os.path.join(os.path.dirname(os.path.abspath(fatti_p)), "revisione_incarico.json")
    json.dump(inc, open(inc_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Incarico del revisore: {inc_p} (senza citazioni); risposta in revisione.json")
else:
    for f in lista:
        i, v = f.get("id"), f.get("verifica")
        nuove = _parole(f.get("trovato")) - set().union(*[_parole(s.get("citazione")) for s in f.get("fonti") or [{}]])
        if v is None:
            problemi.append(f"{i}: da rivedere (elenco REVISIONE) e senza esito")
        elif v == "confermato" and len(str(f.get("trovato") or "").split()) < 6:
            problemi.append(f"{i}: \"confermato\" senza \"trovato\": il revisore copia la frase letta sulla pagina aperta (parola per parola)")
        elif v == "confermato" and len(nuove) < 6:
            problemi.append(f"{i}: \"trovato\" ricopia la citazione della scheda: il revisore riapre la pagina e scrive la frase "
                            "che contiene il fatto e quella che la segue (ISTRUZIONI §4.7)")
        elif v == "confermato":
            manca = sorted(_num(f.get("testo")) - _num(f.get("trovato")) - set().union(*[_num(s.get("citazione")) for s in f.get("fonti") or [{}]]))
            if manca:
                avvisi.append(f"{i}: numeri del testo che né la citazione né il revisore riportano: {manca[:4]} (calcolati da noi? altrimenti correggi)")

# Ampiezza della ricerca (solo prima della revisione: si recupera cercando, quando costa poco; non blocca mai l'uscita).
# Notizie: top story + 6-8 in prima pagina + riserve. Approfondimenti: fatti propri, oltre ai dati di mercato.
if prima_revisione:
    n_not = sum(1 for f in fatti if ALIAS.get(f.get("sezione", ""), f.get("sezione", "")) in ("top_story", "top_news"))
    n_app = sum(1 for f in fatti if ALIAS.get(f.get("sezione", ""), f.get("sezione", "")) == "deep_dive")
    if n_not < 10:
        problemi.append(f"RICERCA: {n_not} schede di notizie, ne servono almeno 10 (top story, 6-8 in prima pagina, riserve): "
                        "cerca ancora nel flusso dall'ultima edizione (il lunedì anche sabato e domenica) e nei "
                        "resoconti di fine seduta delle agenzie (ISTRUZIONI §6.2)")
    if n_app < 6:
        problemi.append(f"RICERCA: {n_app} schede per gli approfondimenti (sezione \"deep_dive\"), ne servono almeno 6: "
                        "per ogni tesi i fatti che la provano (causa, contesto, chi lo dice, cosa succede dopo), "
                        "non solo i prezzi (ISTRUZIONI §2, \"Un approfondimento = una tesi\")")

# Lettura del mondo (v8.2, prova del 13/11: lette solo Yahoo Finance, TheStreet e Milano Finanza, apertura sbagliata,
# mancati gli attacchi ai siti sauditi e il dollaro a 160 yen). Si controlla prima della scaletta, quando cercare costa poco.
if prima_revisione:
    pp = [f for f in tutte if isinstance(f, dict) and f.get("sezione") == "prime_pagine"]
    r = pp[0] if pp else {}
    lette = [t for t in r.get("testate") or [] if t.get("testata") and (t.get("storie") or t.get("apertura"))]
    glob = [t for t in lette if re.search(r"reuters|bloomberg|financial times|\bft\b|wall street journal|\bwsj\b", t["testata"], re.I)]
    manca = []
    if len(lette) < 4:
        manca.append(f"{len(lette)} testate lette, ne servono 4")
    if len(glob) < 2:
        manca.append("almeno 2 tra Reuters, Bloomberg, Financial Times e Wall Street Journal (bastano i titoli dei risultati di ricerca)")
    if len([x for x in r.get("flusso") or [] if str(x).strip()]) < 5:
        manca.append("almeno 5 titoli nel 'flusso' dall'ultima edizione")
    if "fuori" not in r:
        manca.append("'fuori' (ogni storia in evidenza in 2 letture che non copriamo, col motivo)")
    if manca:
        problemi.append("RICERCA, lettura del mondo (registro prime_pagine, APP_FONTI §4): " + "; ".join(manca))

# Scaletta (ISTRUZIONI §6.2b): prima si decide cosa si vuole dimostrare, poi si cercano le prove. Si scrive prima della
# ricerca mirata; qui si controlla solo che esista e che ogni approfondimento abbia tesi, domanda, prove e smentita.
if prima_revisione:
    sc = [f for f in tutte if isinstance(f, dict) and f.get("sezione") == "scaletta"]
    mod = (sc[0].get("moduli") or []) if sc else []
    if not sc or not mod:
        problemi.append("SCALETTA: manca il registro {\"id\": \"S1\", \"sezione\": \"scaletta\"} con i moduli "
                        "(schema in APP_FONTI.md §4): scrivilo ora dalle tesi che hai scelto")
    for m in mod:
        manca = [k for k in ("tesi", "domanda", "contro") if not str(m.get(k) or "").strip()]
        if not [x for x in m.get("schede") or [] if x in ids]:
            manca.append("schede (gli id delle schede su cui poggia la tesi: il revisore le riapre)")
        if len(m.get("prove") or []) < 4:
            manca.append("prove (almeno 4)")
        if manca:
            problemi.append(f"SCALETTA {m.get('chiave', '?')}: manca {', '.join(manca)}")

print(f"Schede: {len(fatti)} | ultima edizione: {ultima} | avvisi: {len(avvisi)}")
for a in avvisi:
    print("AVVISO: " + a)
if problemi:
    respinti = sorted({p.split(":")[0] for p in problemi if p.split(":")[0] in ids})
    print("PROBLEMI:\n- " + "\n- ".join(problemi))
    print("DA_TOGLIERE: " + ",".join(respinti)); sys.exit(1)
print("OK: schede dei fatti in regola")
