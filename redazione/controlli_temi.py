"""Ripetizioni di TEMA in prima pagina (bloccante). Uso: python3 controlli_temi.py voce_indice.json
Confronta la top story (titolo + dek) con i punti di "In 30 secondi" e con i titoli delle notizie: se condividono
una coppia di parole significative (es. "vendite dettaglio", "wall street", "treasury anni"), lo stesso tema è
raccontato due volte. Regola: "In 30 secondi" = le 3 cose più importanti DOPO la top story; le notizie non
riprendono la top story. Correzione: togli il tema dal punto o dalla notizia e mettici un fatto diverso."""
import json
import re
import sys

STOP = set("""il lo la i gli le un uno una di a da in con su per tra fra e o ma che non più meno al allo alla ai agli
alle del dello della dei degli delle dal dallo dalla dai dagli dalle nel nello nella nei negli nelle sul sullo sulla
sui sugli sulle è sono ha hanno si se come anche ancora dopo prima oggi ieri stamattina mese anno annuo mensile
sopra sotto attese atteso contro sale scende chiude cala salgono scendono resta oltre circa quasi suo sua loro
settembre ottobre agosto novembre dicembre lunedì martedì mercoledì giovedì venerdì usa""".split())


def parole(t):
    t = re.sub(r"<[^>]+>", " ", t.lower())
    return [w for w in re.findall(r"[a-zà-ù]{3,}", t) if w not in STOP]


def coppie(t):
    w = parole(t)
    return {(a, b) for i, a in enumerate(w) for b in w[i + 1:i + 3]}   # coppie vicine (finestra 3)


def main():
    v = json.load(open(sys.argv[1], encoding="utf-8"))
    top = coppie(v.get("titolo", "") + " " + v.get("dek", ""))
    errori = []
    for i, s in enumerate(v.get("sommario", []), 1):
        c = top & coppie(s)
        if c:
            errori.append(f"In 30 secondi, punto {i}: riprende la top story ({', '.join(' '.join(x) for x in sorted(c)[:3])})")
    for i, n in enumerate(v.get("notizie", []), 1):
        c = top & coppie(n)
        if c:
            errori.append(f"Notizia {i:02d} \"{n[:60]}\": riprende la top story ({', '.join(' '.join(x) for x in sorted(c)[:3])})")
    print(f"Temi di prima pagina: {len(errori)} ripetizioni della top story")
    for e in errori:
        print("ERRORE:", e[:200])
    sys.exit(1 if errori else 0)


if __name__ == "__main__":
    main()
