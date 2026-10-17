"""Messaggio finale a Paolo (max 4 righe), composto dai file: niente da riscrivere a mano.
Uso: python3 messaggio.py --voce /home/claude/lavoro/voce_indice.json --sito "<ultima riga di pubblica.sh>"
Righe: 1 notizia del giorno (titolo di pag. 1) | 2 evento da guardare oggi (riga in grassetto dell'agenda) |
3 la scommessa (on track = direzione giusta finora; nel range) | 4 la riga "Sito: ..." identica a pubblica.sh.
L'Archivio Claude si aggiorna DOPO la consegna e non entra nel messaggio."""
import json, sys

a = sys.argv[1:]
opt = lambda k, d="": a[a.index(k) + 1] if k in a else d
v = json.load(open(opt("--voce", "/home/claude/lavoro/voce_indice.json"), encoding="utf-8"))
sito = opt("--sito").strip() or "Sito: NON aggiornato - esito di pubblica.sh mancante"
righe = [v.get("titolo", "").strip()]
if v.get("evento_oggi"):
    righe.append("Da guardare: " + v["evento_oggi"])
sc = v.get("scommessa") or {}
ve = v.get("verdetto")
num = lambda x: f"{x:g}".replace(".", ",")
if ve:  # lunedì: il verdetto della settimana chiusa, poi il pronostico nuovo
    var = sc.get("variabile", {}).get("nome")
    righe.append(f"Scommessa: verdetto {ve['punti']} punti su {ve['su']} (par {num(ve['par'])}); nuovo pronostico su "
                 f"{sc.get('su', 6)} mercati" + (f" più {var.split(' (')[0].lower()}" if var else ""))
elif sc.get("su") and sc.get("strada") is not None:
    righe.append(f"Scommessa: {sc['strada']}/{sc['su']} on track, {sc.get('range', 0)}/{sc['su']} nel range")
righe.append(sito if sito.startswith("Sito:") else "Sito: " + sito)
print("\n".join(r.replace("–", "-").replace("—", "-") for r in righe if r)[:600])
