#!/usr/bin/env bash
# Scommessa da martedì a venerdì (il lunedì: APP_LUNEDI.md). Uso: bash /home/claude/gtd/redazione/scommessa_giorno.sh
# Prima: $GTD_LAVORO/attuali.json con l'ultima CHIUSURA UFFICIALE e la sua data per ogni strumento,
#   es. {"spx": [7830.1, "2026-10-19"]} (chiavi acwi spx sx5e ust10 brent eurusd; lo strumento della domanda, se è un altro, in attuali_domanda.json; senza chiusura nuova si omette;
#   data di oggi o orario = valuta.py si ferma). Scrive stato.json e c_forecast.png nella cartella di lavoro.
set -eu
REPO="${GTD_REPO:-/home/claude/gtd}"; R="$REPO/redazione"; L="${GTD_LAVORO:-/home/claude/lavoro}"
LUN=$(python3 -c "import sys,datetime as d;sys.path.insert(0,'$R');import giorni as G;print(G.lunedi(d.date.fromisoformat('${GTD_DATA:-$(date +%F)}')).isoformat())")
REG="$R/pronostici/${LUN}-settimana.json"
[ -f "$REG" ] || { echo "MANCA il registro $REG: vedi APP_LUNEDI.md"; exit 1; }
[ -f "$L/attuali.json" ] || { echo "MANCA $L/attuali.json"; exit 1; }
cd "$R/scommessa"
python3 valuta.py --settimana "$REG" --attuali "$L/attuali.json" --json "$L/stato.json" | tail -3
GTD_ALTO_GRAFICO=2.9 python3 grafico.py "$REG" "$L/c_forecast.png" "$L/stato.json" | tail -1
# Domanda della settimana (tipo mercato): a che punto siamo, dall'ultima chiusura dello strumento in attuali.json
DOM="$R/pronostici/${LUN}-domanda.json"
if [ -f "$DOM" ]; then
  python3 - "$DOM" "$L/attuali.json" "$LUN" "$L/domanda_stato.json" <<'PYEOF'
import json, subprocess, sys
dom, att, lun, out = sys.argv[1:5]
import os
d = json.load(open(dom, encoding="utf-8")); a = json.load(open(att, encoding="utf-8"))
extra = os.path.join(os.path.dirname(att), "attuali_domanda.json")
if os.path.exists(extra):
    a.update(json.load(open(extra, encoding="utf-8")))
if d.get("tipo") == "mercato" and d.get("strumento") in a:
    v, data = a[d["strumento"]]
    r = subprocess.run([sys.executable, "domanda.py", "stato", "--lunedi", lun, "--valore", str(v), "--data", data],
                       capture_output=True, text=True)
    open(out, "w", encoding="utf-8").write(r.stdout)
    print("Domanda:", json.loads(r.stdout).get("finora"), "finora")
elif d.get("tipo") == "mercato":
    print(f"AVVISO domanda: manca {d.get('strumento')} in attuali.json o attuali_domanda.json (serve per 'a che punto siamo')")
PYEOF
fi
echo "Scommessa: REG = \"${LUN}-settimana.json\" nel modello; stato.json e c_forecast.png in $L"
