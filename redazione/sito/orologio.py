#!/usr/bin/env python3
"""L'orologio dei controlli (G-58), visto da GitHub: legge da gommberg.com/api/orologio lo stato che scrive il Worker
(redazione/sito/orologio.js: le Cron Triggers di Cloudflare che fanno partire i flussi a un'ora precisa).

Lo usa mattino.py (controllo del mattino): una riga "Orologio dei controlli", rossa se l'orologio non è sano. Le
sveglie di riserva di GitHub, che con --guardia lo chiedevano prima di lavorare, le ha tolte il passo 2 di G-58.

"sano" (lo decide il Worker): il segreto GITHUB_ACTIONS_TOKEN c'è, almeno una partenza è riuscita, e l'ultima partenza
dovuta di ogni flusso è andata bene. Nessun segreto passa di qui.

Uso:  python3 redazione/sito/orologio.py
Solo per le prove: GTD_OROLOGIO (un file JSON al posto di gommberg.com/api/orologio) e GTD_BASE (il sito)."""
import json
import os
import sys
import urllib.request

BASE = os.environ.get("GTD_BASE", "https://gommberg.com/").rstrip("/") + "/"


def leggi():
    """Lo stato dell'orologio, o None se non si legge (sito giù, servizio non pubblicato, risposta strana)."""
    try:
        if os.environ.get("GTD_OROLOGIO"):
            j = json.load(open(os.environ["GTD_OROLOGIO"], encoding="utf-8"))
        else:
            r = urllib.request.Request(BASE + "api/orologio", headers={"User-Agent": "controllo-gommberg", "Cache-Control": "no-cache"})
            with urllib.request.urlopen(r, timeout=30) as f:
                j = json.loads(f.read())
        return j if isinstance(j, dict) and isinstance(j.get("sano"), bool) else None
    except Exception:  # noqa: BLE001
        return None


def giudizio(j):
    """(sano, frase per una persona)."""
    if j is None:
        return False, "gommberg.com/api/orologio non risponde: il Worker non è pubblicato con il suo codice, o è giù"
    if j.get("sano"):
        return True, "partenze puntuali: " + "; ".join(f"{s['flusso']} {s['dovuta'] or '-'}" for s in j.get("sveglie", []))
    if j.get("errore"):
        return False, j["errore"]
    if not j.get("segreto"):
        return False, "manca il segreto GITHUB_ACTIONS_TOKEN nel Worker di Cloudflare (passi per Paolo in G-58): l'orologio non fa partire nulla"
    if not j.get("repository"):
        return False, "manca GITHUB_REPOSITORY nel Worker: va ripubblicato il sito da main (sito.yml)"
    male = [f"{s['flusso']} delle {(s.get('dovuta') or '')[11:]} del {(s.get('dovuta') or '')[8:10]}/{(s.get('dovuta') or '')[5:7]}: "
            + ((s.get("esito") or {}).get("stato", "?") + (" - " + s["esito"]["dettaglio"] if (s.get("esito") or {}).get("dettaglio") else ""))
            for s in j.get("sveglie", []) if not s.get("ok")]
    if male:
        return False, "; ".join(male)[:400]
    if not j.get("provato"):
        return False, f"acceso alle {str(j.get('avvio', ''))[11:16]} UTC, ancora nessuna partenza riuscita"
    return False, "non sano"


def main():
    j = leggi()
    sano, frase = giudizio(j)
    print(("OK   " if sano else "NO   ") + "Orologio dei controlli: " + frase)
    return 0 if sano else 1


if __name__ == "__main__":
    sys.exit(main())
