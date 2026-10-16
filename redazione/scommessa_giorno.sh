#!/usr/bin/env bash
# Scommessa da martedì a venerdì (il lunedì: APP_LUNEDI.md). Uso: bash /home/claude/gtd/redazione/scommessa_giorno.sh
# Prima: $GTD_LAVORO/attuali.json con l'ultima CHIUSURA UFFICIALE e la sua data per ogni strumento,
#   es. {"spx": [7830.1, "2026-10-19"]} (chiavi acwi spx sx5e ust10 ust2 brent eurusd; senza chiusura nuova si omette;
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
echo "Scommessa: REG = \"${LUN}-settimana.json\" nel modello; stato.json e c_forecast.png in $L"
