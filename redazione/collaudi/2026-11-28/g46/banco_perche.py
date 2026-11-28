"""G-46, punto 6: l'avviso sui perché della scommessa (controlli_testo.perche_vuoti) sui perché usciti dal 19/10 e su un banco
di perché buoni e vuoti. Stampa avvisi sui buoni (falsi) e silenzi sui vuoti (mancati). Uso: python3 banco_perche.py"""
import glob, json, os, sys
R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, R)
import controlli_testo as T

BUONI = ["La tendenza dell'inflazione a scendere spinge la BCE a tagliare e il Bund a salire",
         "La tendenza al rialzo dei salari tiene alta l'inflazione e i rendimenti",
         "Il rimbalzo del dollaro dopo il dato forte sul lavoro pesa sull'euro",
         "Il recupero dei margini delle raffinerie sostiene il greggio dopo la chiusura di due impianti",
         "Il terzo taglio di fila della BCE spinge giù i rendimenti tedeschi",
         "Con i mercati in attesa di un taglio, il dollaro perde il sostegno dei tassi",
         "Gli investitori che attendono un taglio comprano Treasury e il rendimento scende",
         "La BCE aspetta l'inflazione di dicembre per tagliare: niente spinta al Bund",
         "I future perdono terreno dopo il crollo dei chip asiatici",
         "Il petrolio che scende frena le attese di inflazione prima del CPI",
         "Un rialzo Fed a dicembre sempre più probabile sostiene il dollaro",
         "Colloqui USA-Iran e offerta in eccesso stimata da JPMorgan",
         "Sanzioni russe sospese: il greggio perde premio",
         "Lo stretto di Hormuz resta chiuso: il rischio sulle forniture tiene alto il prezzo",
         "Direzione debole: poggia solo sulla tendenza di fondo"]
VUOTI = ["L'Europa aspetta i conti di Nvidia dopo una settimana forte",
         "Dopo il minimo da maggio aspetta di capire se Wall Street tiene",
         "L'euro recupera un po' dopo una settimana di dollaro forte",
         "Rimbalza dopo la caduta di venerdì, la peggiore da mesi",
         "Gli investitori guardano al dato sull'inflazione",
         "In vista della riunione della Fed",
         "Dopo il rally, consolida i guadagni",
         "Sulla scia di Wall Street",
         "Prosegue la corsa dei titoli tecnologici",
         "Riparte dopo il calo di venerdì",
         "Torna a salire dopo tre sedute in calo",
         "Terza seduta consecutiva in rialzo",
         "Riprende fiato dopo la corsa",
         "Occhi puntati sulla BCE di giovedì",
         "Tutto dipende dalla Fed",
         "Direzione debole, il mercato aspetta la Fed"]
fa = [m for m in BUONI if T.perche_vuoti([("x", m)])]
ma = [m for m in VUOTI if not T.perche_vuoti([("x", m)])]
print(f"banco: buoni {len(BUONI)}, avvisi sui buoni {len(fa)}; vuoti {len(VUOTI)}, mancati {len(ma)}")
for m in fa:
    print("  FALSO  ", m)
for m in ma:
    print("  MANCATO", m)
sei = [(k, "Direzione debole: poggia solo sul mattino") for k in "abcdef"]
print("sei direzioni deboli:", [c for *_, c in T.perche_vuoti(sei)])
n = 0
for f in sorted(glob.glob(os.path.join(R, "pronostici", "2026-1*-settimana.json"))):
    reg = json.load(open(f, encoding="utf-8"))
    mot = [(k, v.get("motivo_redazione", "")) for k, v in reg["strumenti"].items()]
    if any("pronostico pubblicato" in m for _, m in mot):
        continue
    for k, m, c in T.perche_vuoti(mot):
        n += 1
        print(f"  {os.path.basename(f)[:10]} {k}: {m} -> {c}")
print("avvisi sui perché usciti:", n)
