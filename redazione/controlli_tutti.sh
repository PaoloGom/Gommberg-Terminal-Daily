#!/usr/bin/env bash
# Tutti i controlli del PDF in un colpo, con output corto. Uso:
#   bash /home/claude/gtd/redazione/controlli_tutti.sh "<pdf>" <N> [fatti.json] [--prima-della-revisione]
# Esegue (tutti BLOCCANTI; dentro ognuno le righe AVVISO non bloccano): controlli.py (pagine, trattini, testata,
# edizioni.json) | controlli_fatti.py (schede; senza --prima-della-revisione esige l'esito del revisore) |
# controlli_numeri.py (PDF contro dati.json) | controlli_testo.py (righe →, connettivi, sigle) | controlli_temi.py
# (temi di pag. 1) | controlli_contenuti.py (estremi, perché/quindi, probabilità, record, anomalie, Stamattina, moduli,
# quadro) | controlli_ripetizioni.py (cifra distintiva oltre 2 volte) | anteprima.py (una sola immagine).
# Uscite in $GTD_LAVORO (default /home/claude/lavoro): anteprima.png, testo.json (sigle spiegate), ripetizioni.json.
# Prima di edizioni_voce.py (edizione non ancora in edizioni.json) usa GTD_SENZA_INDICE=1: salta il controllo dell'indice.
set -u
PDF="${1:?pdf}"; N="${2:?numero}"; FATTI="${3:-}"; FASE="${4:-}"
[ "$FATTI" = "--prima-della-revisione" ] && { FASE="$FATTI"; FATTI=""; }
REPO="${GTD_REPO:-/home/claude/gtd}"; R="$REPO/redazione"; L="${GTD_LAVORO:-/home/claude/lavoro}"
FATTI="${FATTI:-$L/fatti.json}"; mkdir -p "$L"
ROSSI=(); TMP=$(mktemp)

passo() {  # passo <nome> <bloccante 1/0> <comando...>
  local nome="$1" blocca="$2"; shift 2
  "$@" >"$TMP" 2>&1; local rc=$?
  local riga; riga=$(grep -vE "^(AVVISO|- |PROBLEMI|DA_TOGLIERE)" "$TMP" | head -1)
  if [ $rc -eq 0 ]; then echo "[ok] $nome: $riga" | cut -c1-160
  elif [ "$blocca" = "1" ]; then echo "[ROSSO] $nome:"; ROSSI+=("$nome")
  else echo "[avviso] $nome: $riga" | cut -c1-160; fi
  { grep -E "^(ERRORE|- |DA_TOGLIERE)" "$TMP"; grep -E "^AVVISO" "$TMP"; } | head -6 | cut -c1-200
  if [ $rc -ne 0 ] && ! grep -qE "^(- |ERRORE)" "$TMP"; then tail -1 "$TMP" | cut -c1-160; fi
}

if [ "${GTD_SENZA_INDICE:-0}" = "1" ]; then
  python3 - "$REPO/edizioni.json" "$N" "$L/_indice_prova.json" <<'EOF'
import json, sys, datetime as dt
v = json.load(open(sys.argv[1], encoding="utf-8")); n = int(sys.argv[2])
if not any(x["numero"] == n for x in v):
    import os; sys.path.insert(0, os.path.join(os.path.dirname(sys.argv[1]), "redazione")); import giorni as G
    d = G.EDIZIONE_1
    while not (G.uscita(d) and G.numero(d) == n): d += dt.timedelta(days=1)
    v.append({"numero": n, "data": d.isoformat(), "titolo": "-", "sommario": [], "file": f"pdf/{d}-gommberg-{n:03d}.pdf",
              "nome": "-", "notizie": []})
json.dump(v, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False)
EOF
  INDICE="$L/_indice_prova.json"
else
  INDICE="$REPO/edizioni.json"
fi
passo "PDF e indice" 1 python3 "$R/controlli.py" "$PDF" "$INDICE" "$N"
DATA=$(python3 -c "import json,sys;print(next((v['data'] for v in json.load(open('$INDICE')) if v['numero']==$N),''))")
if [ -f "$FATTI" ] && [ -n "$DATA" ]; then
  passo "Fatti${FASE:+ (prima della revisione)}" 1 python3 "$R/controlli_fatti.py" "$FATTI" "$REPO/edizioni.json" "$DATA" $FASE
else
  echo "[ROSSO] Fatti: manca $FATTI o la data dell'edizione $N"; ROSSI+=("Fatti")
fi
if [ -f "$L/dati.json" ]; then
  passo "Numeri contro dati.json" 1 python3 "$R/controlli_numeri.py" "$PDF" "$L/dati.json"
else
  echo "[ROSSO] Numeri: manca $L/dati.json (schema di controlli_dati.py, con 'etichette')"; ROSSI+=("Numeri")
fi
passo "Scrittura (→, cause, sigle)" 1 python3 "$R/controlli_testo.py" "$PDF" --json "$L/testo.json"
if [ -f "$L/voce_indice.json" ]; then
  passo "Temi di prima pagina" 1 python3 "$R/controlli_temi.py" "$L/voce_indice.json"
else
  echo "[ROSSO] Temi: manca $L/voce_indice.json (lo scrive il render del modello)"; ROSSI+=("Temi")
fi
passo "Contenuti (estremi, perché, anomalie...)" 1 python3 "$R/controlli_contenuti.py" "$PDF" --voce "$L/voce_indice.json" \
  --dati "$L/dati.json" --fatti "$FATTI" --repo "$REPO"
passo "Ripetizioni" 1 python3 "$R/controlli_ripetizioni.py" "$PDF" --json "$L/ripetizioni.json"
passo "Anteprima" 1 python3 "$R/anteprima.py" "$PDF" "$L/anteprima.png"
rm -f "$TMP"
if [ ${#ROSSI[@]} -eq 0 ]; then
  echo "ESITO: OK - guarda $L/anteprima.png con Read (una sola immagine)"
else
  echo "ESITO: ERRORI in ${ROSSI[*]} - correggi tutto in un giro (APP_ERRORI.md), rigenera, rilancia"; exit 1
fi
