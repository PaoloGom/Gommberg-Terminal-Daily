#!/usr/bin/env bash
# Prova generale con l'attività vera, senza pubblicare. Il ramo principale non viene mai toccato.
#   bash redazione/prova.sh avvio [AAAA-MM-GG]  (dopo `git fetch --depth=60 origin <ramo> main && git checkout -B <ramo> origin/<ramo>`)
#   bash redazione/prova.sh chiudi "<pdf>"      (alla fine: salva PDF, schede, sorgenti e misure sul ramo prova)
# avvio: porta nel ramo in prova l'archivio del ramo principale fino all'edizione di IERI (memoria, ripetizioni,
# scommessa), così l'edizione si rifà da capo. Con una data (un giorno di borsa) la prova vale per quel giorno: serve nel
# fine settimana per provare l'edizione del lunedì. La data vive in redazione/PROVA_DATA, mai committata.
set -u
REPO="$(git rev-parse --show-toplevel)"; cd "$REPO" || exit 1
L="${GTD_LAVORO:-/home/claude/lavoro}"
RAMO="$(git rev-parse --abbrev-ref HEAD)"
case "${1:-}" in
avvio)
  case "$RAMO" in main|HEAD|prova) echo "PROVA NON POSSIBILE: sono su '$RAMO', serve il ramo da provare"; exit 1;; esac
  if [ -n "${2:-}" ]; then
    echo "$2" | grep -qE '^20[0-9]{2}-[0-9]{2}-[0-9]{2}$' || { echo "PROVA NON POSSIBILE: data '$2' non valida (AAAA-MM-GG)"; exit 1; }
    echo "$2" > redazione/PROVA_DATA
  fi
  OGGI="$(cat redazione/PROVA_DATA 2>/dev/null || TZ=Europe/Rome date +%F)"
  git config user.name "PaoloGom"; git config user.email "PaoloGom@users.noreply.github.com"
  E="$(git log origin/main --format=%H --grep="^Edizione #[0-9]* - ${OGGI}" -1)"
  BASE="origin/main"; [ -n "$E" ] && BASE="${E}^"
  if ! git merge -q --no-edit "$BASE" >/dev/null 2>&1; then
    git merge --abort >/dev/null 2>&1; echo "PROVA NON POSSIBILE: il ramo $RAMO non si unisce al ramo principale (conflitto)"; exit 1
  fi
  [ -e /home/claude/gtd ] || ln -s "$REPO" /home/claude/gtd
  mkdir -p "$L"; date +%s > "$L/_prova_inizio"
  # Un solo ramo di prova, "prova", sovrascritto a ogni prova: si scrive subito all'avvio, così da fuori si vede se la
  # prova è partita ("Prova avviata") o finita ("Prova ... non pubblicata"). Niente rami nuovi per ogni prova.
  git commit -q --allow-empty -m "Prova avviata ${OGGI} $(TZ=Europe/Rome date +%H:%M) (ramo ${RAMO})" && git push -q -f origin HEAD:refs/heads/prova 2>/dev/null \
    || echo "AVVISO: segnale di avvio non salvato sul ramo prova"
  echo "PROVA pronta: ramo $RAMO con l'archivio fino a ieri (base $(git rev-parse --short "$BASE")), edizione del ${OGGI}."
  echo "Da qui: ISTRUZIONI.md di questo ramo, con GTD_PROVA=1 davanti a pubblica.sh; niente Archivio Claude."
  ;;
chiudi)
  OGGI="$(cat redazione/PROVA_DATA 2>/dev/null || TZ=Europe/Rome date +%F)"
  PDF="${2:?pdf}"; D="redazione/collaudi/prova-${OGGI}"; mkdir -p "$D"
  cp -f "$PDF" "$D/prova.pdf"
  for f in fatti.json riempimento.json voce_indice.json testo.json ripetizioni.json dati.json contesto.json stato.json verdetto.json revisione.json desk_proposta.json desk_ok.json; do [ -f "$L/$f" ] && cp -f "$L/$f" "$D/"; done
  [ -f "$L/edizione_${OGGI}.py" ] && cp -f "$L/edizione_${OGGI}.py" "$D/edizione.py"   # il testo scritto: senza, la prova non si può rifare né collaudare
  # la scheda dell'edizione come andrebbe sul sito e la sua pagina in testo: servono a provare il sito senza pubblicare
  python3 - "$D" <<'PY' 2>/dev/null || echo "AVVISO: scheda del sito non salvata"
import json, os, shutil, sys
e = json.load(open("edizioni.json", encoding="utf-8")); v = max(e, key=lambda x: x["numero"])
json.dump(v, open(os.path.join(sys.argv[1], "voce_sito.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
p = f"e/{v['numero']:03d}.html"
if os.path.exists(p):
    shutil.copy(p, os.path.join(sys.argv[1], "pagina.html"))
PY
  for f in pronostici/*-settimana.json scommessa/pagella.json; do [ -f "redazione/$f" ] && [ -n "$(git status --porcelain "redazione/$f")" ] && cp -f "redazione/$f" "$D/"; done
  T0="$(cat "$L/_prova_inizio" 2>/dev/null || echo 0)"
  { echo "data: $OGGI"; echo "ramo: $RAMO"; echo "minuti: $(( ( $(date +%s) - T0 ) / 60 ))"; echo "fine: $(TZ=Europe/Rome date +%H:%M)"; } > "$D/tempi.txt"
  git checkout -q -- edizioni.json 2>/dev/null
  git add -f "$D" && git commit -q -m "Prova del ${OGGI} dal ramo ${RAMO} (non pubblicata)" || { echo "Prova: niente da salvare"; exit 1; }
  if git push -q -f origin "HEAD:refs/heads/prova" 2>/dev/null; then echo "Prova: salvata sul ramo prova ($(cat "$D/tempi.txt" | tr '\n' ' '))"
  else echo "Prova: NON salvata (push del ramo di prova rifiutato)"; fi
  ;;
*) echo "uso: prova.sh avvio [AAAA-MM-GG] | chiudi <pdf>"; exit 1;;
esac
