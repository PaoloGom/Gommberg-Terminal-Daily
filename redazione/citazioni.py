"""Le fonti nel testo del PDF (ISTRUZIONI.md §5, "Come si cita"): l'unico punto in cui la regola diventa codice.
La usano controlli_testo.py (bloccante), controlli_contenuti.py e banco/misure.py: chi cambia la regola cambia
questo file e la riga di §5, insieme, e prova il risultato sul banco (banco/banco.sh).

Regola: la voce è nostra. "(Testata)" in coda solo per la causa di un movimento o una notizia da fonte singola,
con misura: UNA testata per parentesi, UNA parentesi per paragrafo, al massimo MAX_PAGINA parentesi per pagina,
mai un fornitore di dati (i numeri sono nostri). Tutte le fonti restano nelle righe "Fonti" e in fatti.json.

Uso diretto: python3 citazioni.py <pdf>   (stampa misure ed errori; codice 1 se ci sono errori)"""
import json, os, re, subprocess, sys

QUI = os.path.dirname(os.path.abspath(__file__))
_F = json.load(open(os.path.join(QUI, "fonti.json"), encoding="utf-8"))
NOMI = _F.get("nomi", [])
FORNITORI = _F.get("fornitori", ["Alpha Vantage", "FMP", "Financial Modeling Prep"])
MAX_PAGINA = 4


def _alt(nomi):
    return "|".join(sorted((re.escape(n) for n in nomi), key=len, reverse=True))


_NOMI_RX = re.compile(r"(?<![\w&])(?:" + _alt(NOMI) + r")(?![\w&])")
FONTE_PAR = re.compile(r"\([^()]{0,30}(?<![\w&])(?:" + _alt(NOMI) + r")(?![\w&])[^()]{0,40}\)")
FORNITORE_PAR = re.compile(r"\([^()]{0,30}(?<![\w&])(?:" + _alt(FORNITORI) + r")(?![\w&])[^()]{0,40}\)")


def testate(parentesi):
    """Testate distinte dentro una parentesi: il nome più lungo vince ("Il Sole 24 Ore" non conta anche "Sole 24 Ore")."""
    return list(dict.fromkeys(m.group(0) for m in _NOMI_RX.finditer(parentesi)))


def pagine(pdf):
    out = []
    for p in range(1, 7):
        t = subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), pdf, "-"], capture_output=True).stdout.decode("utf-8", "replace")
        if not t.strip() and p > 1:
            break
        out.append(t)
    return out


def paragrafi(testo_pagina):
    """Blocchi separati da una riga vuota (come li restituisce pdftotext senza -layout), spazi normalizzati."""
    return [re.sub(r"\s+", " ", b).strip() for b in re.split(r"\n\s*\n", testo_pagina) if b.strip()]


def esame(pdf):
    """Misure e violazioni della regola. Restituisce (misure, errori)."""
    errori, per_pagina, totale, doppie, fornitori = [], [], 0, 0, 0
    for n, tp in enumerate(pagine(pdf), 1):
        nella_pagina = 0
        for par in paragrafi(tp):
            fp = [m.group(0) for m in FONTE_PAR.finditer(par)]
            fo = [m.group(0) for m in FORNITORE_PAR.finditer(par)]
            for x in fo:
                fornitori += 1
                errori.append(f"pag. {n}: fornitore di dati tra parentesi {x}: i numeri sono nostri, togli la parentesi")
            for x in fp:
                if len(testate(x)) > 1:
                    doppie += 1
                    errori.append(f"pag. {n}: due testate in una parentesi {x}: tieni la più autorevole, l'altra resta in 'Fonti'")
            if len(fp) > 1:
                errori.append(f"pag. {n}: {len(fp)} fonti tra parentesi nello stesso paragrafo ({', '.join(fp)[:70]}): "
                              "una sola, sulla causa o sulla notizia principale")
            nella_pagina += len(fp)
        per_pagina.append(nella_pagina)
        totale += nella_pagina
        if nella_pagina > MAX_PAGINA:
            errori.append(f"pag. {n}: {nella_pagina} fonti tra parentesi (massimo {MAX_PAGINA}): tieni solo cause e notizie "
                          "da fonte singola; dati, comunicati e notizie confermate non ne hanno")
    misure = {"parentesi": totale, "per_pagina": per_pagina, "due_testate": doppie, "fornitori": fornitori}
    return misure, errori


if __name__ == "__main__":
    m, e = esame(sys.argv[1])
    print(f"Fonti tra parentesi: {m['parentesi']} (per pagina {m['per_pagina']}, max {MAX_PAGINA}) | "
          f"due testate: {m['due_testate']} | fornitori: {m['fornitori']}")
    for x in e:
        print("ERRORE: " + x[:180])
    sys.exit(1 if e else 0)
