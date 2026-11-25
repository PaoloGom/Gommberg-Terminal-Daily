"""G-42, misura 2 a finestra piena (scritta dal secondo agente).
Lato interrogato: la prosa dell'edizione dal sorgente (desk applicato; esclusi tabelle, agenda, fonti, etichette, riga AI).
Lato di riferimento: per ognuna delle 5 edizioni precedenti, il testo intero del PDF (#021-#025 non hanno sorgenti),
letto come flusso unico di parole (a capo ignorati, sillabazioni a fine riga ricucite).
Un 5-gramma conta se ha almeno 2 parole piene. Falsi echi: 5-grammi della prosa presenti in almeno 6 delle 8 edizioni
con sorgente (formule di impaginazione) e quelli presenti nella pagina modello in vigore (contati a parte, misura 1).
Stampa la tabella per edizione e tutti i tratti (5-grammi contigui fusi) con la vigilia e con le 5 precedenti."""
import collections, glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from carica import DATE, NUM, DOPO, edizione, modello
from misura_base import parole, pieno

QUI = os.path.dirname(os.path.abspath(__file__))
PDF = sorted(glob.glob(os.path.join(QUI, "pdftxt", "*.txt")))
PDFD = [os.path.basename(f)[:10] for f in PDF]


def flusso_pdf(f):
    t = open(f, encoding="utf-8").read()
    t = re.sub(r"(\w)-\n(\w)", r"\1\2", t)
    return parole(t)


REF = {d: set(tuple(w[i:i + 5]) for i in range(len(w) - 4)) for d, w in ((PDFD[i], flusso_pdf(f)) for i, f in enumerate(PDF))}
E = {d: edizione(d)[1] for d in DATE}
MV = modello(os.path.join(QUI, "modello_vecchio.py"))[1]
MN = modello(os.path.join(QUI, "modello_nuovo.py"))[1]


def g5(B):
    s = set()
    for c, ty, t in B:
        w = parole(t)
        s |= {tuple(w[i:i + 5]) for i in range(len(w) - 4) if pieno(tuple(w[i:i + 5]))}
    return s


df = collections.Counter(g for d in DATE for g in g5(E[d]))
FISSI = {g for g, c in df.items() if c >= 6}


def tratti(B, comuni):
    out = []
    for campo, tipo, t in B:
        w = parole(t)
        cop = [False] * len(w)
        for i in range(len(w) - 4):
            if tuple(w[i:i + 5]) in comuni:
                cop[i:i + 5] = [True] * 5
        i = 0
        while i < len(w):
            if cop[i]:
                j = i
                while j < len(w) and cop[j]:
                    j += 1
                out.append((campo, " ".join(w[i:j]), j - i))
                i = j
            else:
                i += 1
    return out


R = {}
for d in DATE:
    B = E[d]
    mod = g5(MN if d in DOPO else MV)
    mine = g5(B) - FISSI - mod
    i = PDFD.index(d)
    lag = [len(mine & REF[PDFD[i - l]]) for l in range(1, 6)]
    union = set().union(*[mine & REF[PDFD[i - l]] for l in range(1, 6)])
    vig = mine & REF[PDFD[i - 1]]
    nw = sum(len(parole(b[2])) for b in B)
    tu, tv = tratti(B, union), tratti(B, vig)
    # in quale edizione precedente compare per la prima volta (la più vicina) ogni tratto
    R[d] = dict(lag=lag, union=len(union), parole=nw, tratti=len(tu), parole_tratti=sum(x[2] for x in tu),
                per1000=round(1000 * sum(x[2] for x in tu) / nw, 1), vig_tratti=len(tv), vig_parole=sum(x[2] for x in tv),
                vig_per1000=round(1000 * sum(x[2] for x in tv) / nw, 1), tutti=tu, vigilia=tv)

json.dump(R, open(os.path.join(QUI, "risultati_m2.json"), "w"), ensure_ascii=False, indent=1)
print("falsi echi automatici esclusi:", [" ".join(g) for g in sorted(FISSI)])
print("ed    | lag1 lag2 lag3 lag4 lag5 | unione | tratti parole /1000 | vigilia: tratti parole /1000 | parole")
for d in DATE:
    x = R[d]
    print(f"{NUM[d]} {'dopo ' if d in DOPO else 'prima'}| " + " ".join(f"{v:4}" for v in x["lag"]) +
          f" | {x['union']:6} | {x['tratti']:6} {x['parole_tratti']:6} {x['per1000']:5} | {x['vig_tratti']:6} {x['vig_parole']:6} {x['vig_per1000']:5} | {x['parole']}")
if len(sys.argv) > 1:
    for d in DATE:
        print("\n==", NUM[d], d)
        for c, t, n in sorted(R[d]["tutti"], key=lambda x: -x[2]):
            print(f"   {n:3} {c:28} {t}")
