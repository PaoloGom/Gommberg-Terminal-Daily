"""Messaggio finale a Paolo (max 4 righe), composto dai file: niente da riscrivere a mano.
Uso: python3 messaggio.py --voce /home/claude/lavoro/voce_indice.json --sito "<ultima riga di pubblica.sh>"
Righe: 1 notizia del giorno (titolo di pag. 1) | 2 evento da guardare oggi (riga in grassetto dell'agenda) |
3 la scommessa (on track = direzione giusta finora; nel range) | 4 la riga "Sito: ..." identica a pubblica.sh.
Il messaggio non include l archivio online (rimosso).

Uscita (c), nessuna edizione: python3 messaggio.py --nessuna <caso> --dettaglio "<errore ricevuto, parola per parola>"
È l'unica porta per rinunciare a un'edizione in un giorno di borsa: stampa la riga da mandare a Paolo solo per i casi di
CASI; per ogni altro motivo si ferma (codice 1) e dice come si prosegue. Il 27/11/2026 una corsa ha chiuso con "nessuna
edizione" perché la raccolta dava pochi fatti verificati: non è un caso, l'edizione esce con ciò che è verificato."""
import json, sys

a = sys.argv[1:]
opt = lambda k, d="": a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else d

CASI = {  # i soli motivi per cui un giorno di borsa resta senza edizione, ognuno dopo 3 tentativi (ISTRUZIONI, Uscite ammesse)
    "repository": "repository irraggiungibile",
    "dati": "le API dei dati non rispondono",
    "pdf": "PDF impossibile da generare",
    "permesso": "permesso negato a un comando del kit o alla pubblicazione",
    "pubblicata": "edizione già pubblicata",
}
if "--nessuna" in a:
    caso, dett = opt("--nessuna").strip().lower(), " ".join(opt("--dettaglio").split())
    if caso not in CASI:
        print(f"USCITA NON AMMESSA: \"{caso or '(vuoto)'}\" non è un motivo per rinunciare all'edizione. I soli casi: "
              + "; ".join(f"{k} = {v}" for k, v in CASI.items()) + ".\n"
              "Pochi fatti verificati, fonti che non si aprono, ricerche che danno pagine di altre date, cifre che non "
              "tornano tra una fonte e l'altra riducono il contenuto, non cancellano l'edizione: OGGI L'EDIZIONE ESCE.\n"
              "Come si prosegue: APP_ERRORI.md §2 alla voce Dati (una serie che non si riesce a stabilire porta \"nd\", "
              "decide controlli_dati.py e non il confronto con il web), §3 (minimi: ogni sezione esce con ciò che è "
              "verificato; un approfondimento senza fatti dal web si regge su dati di mercato, anomalia del giorno e "
              "memoria) e §4 (finiti i giri si toglie ciò che è rosso e si pubblica il resto).")
        sys.exit(1)
    if not dett:
        print(f"USCITA NON AMMESSA: il caso \"{caso}\" vuole --dettaglio con l'errore ricevuto al terzo tentativo, parola "
              "per parola. Senza un errore da riportare non è questo caso: l'edizione esce (APP_ERRORI.md §3 e §4).")
        sys.exit(1)
    print(f"Nessuna edizione oggi: {CASI[caso]} ({dett})"[:600].replace("–", "-").replace("—", "-"))
    sys.exit(0)

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
