#!/usr/bin/env python3
"""Gancio di Claude Code (.claude/settings.json, evento PostToolUse su Bash): legge la trascrizione della sessione e
lascia in /tmp/gtd_token.json i token consumati e il lavoro sul web (ricerche fatte, pagine aperte, pagine non
raggiunte), dove pubblica.sh (pannello.py --indici) li raccoglie.
Nessun modello, nessuna rete, nessuna scrittura nel repository. Esce sempre con 0 e non stampa nulla: non può fermare
né disturbare l'attività.

Claude Code passa al gancio, su stdin, un JSON con "transcript_path": il file .jsonl della conversazione, in cui ogni
risposta del modello porta il suo "usage" (token in ingresso, scritti in cache, letti dalla cache, in uscita). Una
risposta può occupare più righe con lo stesso identificativo: si conta una volta sola. Le trascrizioni degli agenti
stanno in altri .jsonl della stessa cartella: si sommano anche quelle.
Token pesati = ingresso + 2 x scritti in cache + 0,1 x letti dalla cache + 5 x uscita.

Il web (G-02): nella stessa trascrizione ogni ricerca e ogni pagina aperta è una chiamata a WebSearch o WebFetch
(blocco "tool_use", con la ricerca o l'indirizzo) seguita dal suo esito (blocco "tool_result" con lo stesso
identificativo; "is_error" se non è riuscita). Una pagina conta come non raggiunta se nessun tentativo sul suo indirizzo
è riuscito; il motivo si legge dal messaggio d'errore: "limite" (troppe richieste), "errore" con il codice se c'è,
"negata" (il sistema dei permessi), altrimenti "errore". Un esito senza "is_error" vale come fallito solo se è un
messaggio breve che comincia con un errore: i riassunti brevi di una pagina sono esiti riusciti. In "web": {"ricerche", "ricerche_fallite", "pagine", "fallite": [{"sito", "motivo",
"testo"}]}. "testo" (l'inizio del messaggio d'errore) resta in /tmp: serve a riconoscere messaggi che oggi non si
conoscono."""
import glob
import json
import os
import re
import sys
from urllib.parse import urlparse

USCITA = os.environ.get("GTD_TOKEN", "/tmp/gtd_token.json")
CAMPI = {"input_tokens": "input", "cache_creation_input_tokens": "cacheWrite", "cache_read_input_tokens": "cacheRead",
         "output_tokens": "output"}
PESI = {"input": 1, "cacheWrite": 2, "cacheRead": 0.1, "output": 5}


def somma(percorsi):
    visti, per_modello = {}, {}
    for p in percorsi:
        try:
            righe = open(p, encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for r in righe:
            if '"usage"' not in r:
                continue
            try:
                j = json.loads(r)
            except ValueError:
                continue
            m = j.get("message") if isinstance(j.get("message"), dict) else {}
            u = m.get("usage")
            if not isinstance(u, dict):
                continue
            visti[m.get("id") or j.get("requestId") or j.get("uuid")] = (m.get("model") or "?", u)   # l'ultima riga vale
    tot = dict.fromkeys(PESI, 0)
    for modello, u in visti.values():
        pm = per_modello.setdefault(modello, dict.fromkeys(PESI, 0))
        for k, v in CAMPI.items():
            n = int(u.get(k) or 0)
            tot[v] += n
            pm[v] += n
    return len(visti), tot, per_modello


WEB = {"WebSearch": "ricerca", "WebFetch": "pagina"}
NEGATA = re.compile(r"permission|haven't granted|not granted|not allowed|blocked by", re.I)
LIMITE = re.compile(r"\b429\b|rate.?limit|too many requests", re.I)
CODICE = re.compile(r"(?:status(?: code)?|HTTP|error|errore)[ :]*([45]\d\d)\b|^([45]\d\d)\b", re.I)
# un esito senza "is_error" vale come fallito solo se è un messaggio breve che COMINCIA con un errore
GUASTO = re.compile(r"^(error\b|request failed|unable to fetch|failed to fetch|fetch failed|[45]\d\d\b)", re.I)


def _pagina(url):
    """Lo stesso indirizzo scritto in modi diversi è la stessa pagina: senza schema, www, frammento e barra finale."""
    return re.sub(r"^https?://(www\.)?", "", url.split("#")[0].strip().lower()).rstrip("/")


def _testo(c):
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(str(x.get("text") or "") if isinstance(x, dict) else str(x) for x in c)
    return ""


def web(percorsi):
    chiamate, esiti = {}, {}
    for p in percorsi:
        try:
            righe = open(p, encoding="utf-8", errors="ignore")
        except OSError:
            continue
        attese = set()
        for r in righe:
            uso = '"tool_use"' in r and ('"WebSearch"' in r or '"WebFetch"' in r)
            if not uso and not ('"tool_result"' in r and any(i in r for i in attese)):
                continue
            try:
                j = json.loads(r)
            except ValueError:
                continue
            m = j.get("message") if isinstance(j.get("message"), dict) else {}
            for b in m.get("content") if isinstance(m.get("content"), list) else []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "tool_use" and b.get("name") in WEB and b.get("id"):
                    i = b.get("input") if isinstance(b.get("input"), dict) else {}
                    chiamate[b["id"]] = (WEB[b["name"]], str(i.get("query") or i.get("url") or ""))
                    attese.add(b["id"])
                elif b.get("type") == "tool_result" and b.get("tool_use_id") in attese:
                    t = " ".join(_testo(b.get("content")).split())
                    esiti[b["tool_use_id"]] = (bool(b.get("is_error")) or (len(t) < 160 and bool(GUASTO.search(t))), t[:160])
                    attese.discard(b["tool_use_id"])
    ricerche = [i for i, (tipo, _) in chiamate.items() if tipo == "ricerca"]
    pagine = {}                                       # indirizzo -> [riuscita almeno una volta, ultimo messaggio d'errore]
    for i, (tipo, cosa) in chiamate.items():
        if tipo == "pagina" and i in esiti:
            p = pagine.setdefault(_pagina(cosa), [False, "", cosa])   # stessa regola di autori.pagina
            p[0] = p[0] or not esiti[i][0]
            p[1] = esiti[i][1] if esiti[i][0] else p[1]
    fallite = []
    for ok, t, url in pagine.values():
        if ok:
            continue
        senza = re.sub(r"https?://\S+", "", t)             # il codice si legge dal messaggio, non dall'indirizzo
        cod = CODICE.search(senza)
        cod = (cod.group(1) or cod.group(2)) if cod else ""
        motivo = ("limite" if cod == "429" or (not cod and LIMITE.search(senza)) else "errore " + cod if cod
                  else "negata" if NEGATA.search(senza) else "errore")
        try:
            sito = re.sub(r"^www\.", "", (urlparse(url).hostname or "?").lower())
        except ValueError:
            sito = "?"
        fallite.append({"sito": sito, "motivo": motivo, "testo": t[:80]})
    return {"ricerche": len(ricerche), "ricerche_fallite": sum(1 for i in ricerche if esiti.get(i, (False,))[0]),
            "pagine": len(pagine), "fallite": fallite, "cercate": [chiamate[i][1] for i in ricerche]}


def _trascrizioni(tp):
    return [tp] + [p for p in glob.glob(os.path.join(os.path.dirname(tp), "**", "*.jsonl"), recursive=True) if p != tp]


def ricerche_fatte():
    """Le ricerche lanciate finora nella sessione (anche dagli agenti), lette adesso dalla trascrizione che il gancio ha
    annotato. None se il gancio non ha ancora girato o la trascrizione non c'è: chi chiede non può concludere nulla.
    La usa controlli_fatti.py per riscontrare le ricerche dichiarate in "conferma_cercata"."""
    try:
        tp = json.load(open(USCITA, encoding="utf-8")).get("trascrizione")
        return web(_trascrizioni(tp))["cercate"] if tp and os.path.isfile(tp) else None
    except Exception:
        return None


def main():
    try:
        ingresso = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        ingresso = {}
    tp = os.path.expanduser(str(ingresso.get("transcript_path") or ""))
    out = {"evento": ingresso.get("hook_event_name"), "trascrizione": tp, "esiste": bool(tp) and os.path.isfile(tp)}
    if out["esiste"]:
        altri = _trascrizioni(tp)[1:]
        n, tot, per_modello = somma([tp] + altri)
        out.update(file=1 + len(altri), richieste=n, token=tot, per_modello=per_modello,
                   pesati=round(sum(tot[k] * PESI[k] for k in PESI)))
        try:                                          # il web non può far perdere i token
            out["web"] = web([tp] + altri)
            out["web"].pop("cercate", None)           # le ricerche si rileggono dalla trascrizione quando servono
        except Exception:
            pass
    json.dump(out, open(USCITA, "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
