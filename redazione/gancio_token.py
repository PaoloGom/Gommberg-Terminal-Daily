#!/usr/bin/env python3
"""Gancio di Claude Code (.claude/settings.json, evento PostToolUse su Bash): somma i token della sessione dalla sua
trascrizione e li lascia in /tmp/gtd_token.json, dove pubblica.sh (pannello.py --indici) li raccoglie.
Nessun modello, nessuna rete, nessuna scrittura nel repository. Esce sempre con 0 e non stampa nulla: non può fermare
né disturbare l'attività.

Claude Code passa al gancio, su stdin, un JSON con "transcript_path": il file .jsonl della conversazione, in cui ogni
risposta del modello porta il suo "usage" (token in ingresso, scritti in cache, letti dalla cache, in uscita). Una
risposta può occupare più righe con lo stesso identificativo: si conta una volta sola. Le trascrizioni degli agenti
stanno in altri .jsonl della stessa cartella: si sommano anche quelle.
Token pesati = ingresso + 2 x scritti in cache + 0,1 x letti dalla cache + 5 x uscita."""
import glob
import json
import os
import sys

USCITA = "/tmp/gtd_token.json"
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


def main():
    try:
        ingresso = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        ingresso = {}
    tp = os.path.expanduser(str(ingresso.get("transcript_path") or ""))
    out = {"evento": ingresso.get("hook_event_name"), "trascrizione": tp, "esiste": bool(tp) and os.path.isfile(tp)}
    if out["esiste"]:
        cartella = os.path.dirname(tp)
        altri = [p for p in glob.glob(os.path.join(cartella, "**", "*.jsonl"), recursive=True) if p != tp]
        n, tot, per_modello = somma([tp] + altri)
        out.update(file=1 + len(altri), richieste=n, token=tot, per_modello=per_modello,
                   pesati=round(sum(tot[k] * PESI[k] for k in PESI)))
    json.dump(out, open(USCITA, "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
