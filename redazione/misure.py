#!/usr/bin/env python3
"""Misure deterministiche di un'edizione (nessuna chiamata web, nessun modello): servono a confrontare due versioni
del kit sugli stessi criteri, invece che a occhio. Non entrano nel lavoro del mattino: le lancia chi modifica il kit.

Uso:
  python3 misure.py                      # tutte le edizioni pubblicate (pdf/, edizioni.json, redazione/fatti/)
  python3 misure.py --ultime 10          # solo le ultime 10
  python3 misure.py --pdf prova.pdf --fatti fatti.json [--voce voce_indice.json] --nome "prova v8"   # un'edizione fuori archivio
  aggiungi --json misure.json per salvare i numeri, --md per la tabella in Markdown.

Colonne (stesso metodo per tutte le edizioni: sono confrontabili tra loro, non sono voti):
  ora      uscita sul sito (dati/uscite.json, altrimenti l'ora del commit "Edizione #NNN")
  parole   parole del PDF
  fr       parole per frase nei paragrafi in prosa (pag. 1 e 3-5; tabelle e titoli esclusi)
  >30      quota di frasi oltre 30 parole
  cifre    numeri ogni 100 parole nei testi
  gergo    termini da addetti ogni 1.000 parole nei testi (elenco GERGO qui sotto: è un termometro, non una regola)
  ()       fonti tra parentesi nel PDF
  not      notizie di pag. 1 | ag = righe d'agenda, ag+ = con le attese
  sch      schede dei fatti | dd = schede degli approfondimenti
  prim     quota di schede con almeno una fonte primaria (ente ufficiale o documento di chi è parte del fatto)
  l1       quota di schede con almeno una fonte primaria, d'agenzia o di livello 1
  mecc     meccanismi di meccanismi.json usati | par = parole di oggi
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

QUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("GTD_REPO") or os.path.dirname(QUI)
F = json.load(open(os.path.join(QUI, "fonti.json"), encoding="utf-8"))
UFF, L1 = set(F.get("ufficiali", [])), set(F.get("livello_1", []))
AGENZIE = {a.lower() for a in F.get("agenzie", [])}
NOMI = sorted(F.get("nomi", []), key=len, reverse=True)
# Parole che un lettore senza studi di finanza non usa. Misurano la densità, non vietano nulla.
GERGO = [r"\bpb\b", r"rendiment", r"\bcurva\b", r"\bspread\b", r"\bfuture\b", r"volatilit", r"difensiv", r"\bciclic",
         r"rifugio", r"\bconsenso\b", r"\bguidance\b", r"prezza(?:no|to|ti|re)?\b", r"\bscont(?:a|ano|ato)\b", r"\brally\b",
         r"rotazione", r"risk-o(?:ff|n)", r"\bfalc[oh]", r"\bcolomb", r"small cap", r"premio per il rischio",
         r"\bscadenz", r"\bmultipl[oi]\b", r"utili attesi", r"\bEPS\b", r"buyback", r"\bcore\b", r"dopo-borsa",
         r"\bintraday\b", r"\bbenchmark\b", r"\bforward\b", r"\bmargin[ei]\b", r"\brimbalz"]
GERGO_RE = re.compile("|".join(GERGO), re.I)
NUM_RE = re.compile(r"\d[\d.,]*")
FONTE_RE = re.compile(r"\((?:" + "|".join(re.escape(n) for n in NOMI) + r")(?:[,;][^)]{0,40})?\)")


def testo_pdf(pdf, prima=None, ultima=None):
    cmd = ["pdftotext"] + (["-f", str(prima)] if prima else []) + (["-l", str(ultima)] if ultima else []) + [pdf, "-"]
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def frasi(t):
    """Frasi dei soli paragrafi in prosa: blocchi separati da una riga vuota, di almeno 12 parole, che finiscono con un punto
    (così restano fuori testate, celle e righe di tabella)."""
    out = []
    for blocco in re.split(r"\n\s*\n", t):
        b = re.sub(r"\s+", " ", blocco).strip()
        if len(b.split()) < 12 or not re.search(r"[.!?»)]$", b):
            continue
        for s in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý«\"])", b):
            p = s.split()
            if len(p) >= 4:
                out.append(p)
    return out


def host_in(url, insieme):
    h = (urlparse(url or "").hostname or "").lower().split(".")
    return any(".".join(h[i:]) in insieme for i in range(len(h) - 1))


def misura_fatti(fatti):
    schede = [f for f in fatti if isinstance(f, dict) and f.get("fonti") and not f.get("scartata")
              and f.get("sezione") not in ("ricerca", "prime_pagine", "scaletta", "anomalia")]
    prim = l1 = 0
    for f in schede:
        fonti = [x for x in f["fonti"] if isinstance(x, dict)]
        p = any(x.get("primaria") or host_in(x.get("url"), UFF) for x in fonti)
        a = any(str(x.get("agenzia", "")).lower() in AGENZIE or host_in(x.get("url"), L1) for x in fonti)
        prim += p
        l1 += p or a
    n = len(schede) or 1
    return {"sch": len(schede), "dd": sum(1 for f in schede if f.get("sezione") == "deep_dive"),
            "prim": round(100 * prim / n), "l1": round(100 * l1 / n)}


def misura(pdf, fatti=None, voce=None, nome="", ora=""):
    tutto = testo_pdf(pdf)
    corpo = testo_pdf(pdf, 1, 1) + " " + testo_pdf(pdf, 3, 5)
    fr = frasi(corpo)
    parole_corpo = sum(len(p) for p in fr) or 1
    testo_fr = " ".join(" ".join(p) for p in fr)
    r = {"nome": nome, "ora": ora, "parole": len(tutto.split()),
         "fr": round(parole_corpo / (len(fr) or 1), 1),
         ">30": round(100 * sum(1 for p in fr if len(p) > 30) / (len(fr) or 1)),
         "cifre": round(100 * len(NUM_RE.findall(testo_fr)) / parole_corpo, 1),
         "gergo": round(1000 * len(GERGO_RE.findall(testo_fr)) / parole_corpo, 1),
         "()": len(FONTE_RE.findall(tutto))}
    v = voce or {}
    ag = v.get("agenda") or []
    attese = lambda a: (a.get("attese") if isinstance(a, dict) else (a[2] if len(a) > 2 else "")) or ""
    r.update({"not": len(v.get("notizie") or []), "ag": len(ag),
              "ag+": sum(1 for a in ag if attese(a).strip() not in ("", "-")),
              "mecc": len(v.get("meccanismi") or []), "par": len(v.get("parole") or [])})
    r.update(misura_fatti(fatti) if fatti else {"sch": "", "dd": "", "prim": "", "l1": ""})
    return r


def ore_uscita():
    ore = {}
    try:
        log = subprocess.run(["git", "-C", REPO, "log", "--all", "--format=%aI %s", "--grep=^Edizione #"], capture_output=True,
                             text=True).stdout
        for riga in reversed(log.splitlines()):          # dal più vecchio: la prima uscita nel giorno dell'edizione
            t, s = riga.split(" ", 1)
            m = re.search(r"#(\d+) - (\d{4}-\d\d-\d\d)", s)
            quando = dt.datetime.fromisoformat(t).astimezone(ZoneInfo("Europe/Rome"))
            if m and int(m.group(1)) not in ore and quando.date().isoformat() == m.group(2):
                ore[int(m.group(1))] = quando.strftime("%H:%M")
    except Exception:
        pass
    return ore


COL = ["nome", "ora", "parole", "fr", ">30", "cifre", "gergo", "()", "not", "ag", "ag+", "sch", "dd", "prim", "l1", "mecc", "par"]


def stampa(righe, md=False):
    if md:
        print("| " + " | ".join(COL) + " |\n|" + "---|" * len(COL))
        for r in righe:
            print("| " + " | ".join(str(r.get(c, "")) for c in COL) + " |")
        return
    larg = {c: max(len(c), *(len(str(r.get(c, ""))) for r in righe)) for c in COL}
    print("  ".join(c.ljust(larg[c]) for c in COL))
    for r in righe:
        print("  ".join(str(r.get(c, "")).ljust(larg[c]) for c in COL))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ultime", type=int)
    ap.add_argument("--pdf"); ap.add_argument("--fatti"); ap.add_argument("--voce"); ap.add_argument("--nome", default="prova")
    ap.add_argument("--json"); ap.add_argument("--md", action="store_true")
    a = ap.parse_args()
    carica = lambda p: json.load(open(p, encoding="utf-8")) if p and os.path.exists(p) else None
    if a.pdf:
        righe = [misura(a.pdf, carica(a.fatti), carica(a.voce), a.nome)]
    else:
        voci = sorted(carica(os.path.join(REPO, "edizioni.json")) or [], key=lambda v: v["numero"])
        ore = ore_uscita()
        righe = []
        for v in voci[-a.ultime:] if a.ultime else voci:
            pdf = os.path.join(REPO, v["file"])
            if not os.path.exists(pdf):
                continue
            fatti = carica(os.path.join(REPO, "redazione", "fatti", v["data"] + ".json"))
            righe.append(misura(pdf, fatti, v, f"#{v['numero']:03d} {v['data'][5:]}", ore.get(v["numero"], "")))
        num = [c for c in COL[2:] if any(isinstance(r.get(c), (int, float)) for r in righe)]
        if len(righe) > 1:
            med = {"nome": "media", "ora": ""}
            for c in num:
                x = [r[c] for r in righe if isinstance(r.get(c), (int, float))]
                med[c] = round(sum(x) / len(x), 1) if x else ""
            righe.append(med)
    stampa(righe, a.md)
    if a.json:
        json.dump(righe, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    sys.exit(main())
