#!/usr/bin/env bash
# Prova generale della v8 con l'attività vera, senza pubblicare. Il ramo principale non viene mai toccato.
#   bash redazione/prova_v8.sh avvio          (dopo `git fetch --depth=60 origin v8 main && git checkout -B v8 origin/v8`)
#   bash redazione/prova_v8.sh chiudi "<pdf>" (alla fine: salva PDF, schede e misure sul ramo prova, sovrascritto a ogni prova)
# avvio: porta nella v8 l'archivio del ramo principale fino all'edizione di IERI (memoria, ripetizioni, scommessa), così
# l'edizione di oggi si rifà da capo e si confronta con quella uscita stamattina.
set -u
REPO="$(git rev-parse --show-toplevel)"; cd "$REPO" || exit 1
OGGI="$(TZ=Europe/Rome date +%F)"; L="${GTD_LAVORO:-/home/claude/lavoro}"
case "${1:-}" in
avvio)
  [ "$(git rev-parse --abbrev-ref HEAD)" = "v8" ] || { echo "PROVA NON POSSIBILE: non sono sul ramo v8"; exit 1; }
  git config user.name "PaoloGom"; git config user.email "PaoloGom@users.noreply.github.com"
  E="$(git log origin/main --format=%H --grep="^Edizione #[0-9]* - ${OGGI}" -1)"
  BASE="origin/main"; [ -n "$E" ] && BASE="${E}^"
  if ! git merge -q --no-edit "$BASE" >/dev/null 2>&1; then
    git merge --abort >/dev/null 2>&1; echo "PROVA NON POSSIBILE: la v8 non si unisce al ramo principale (conflitto)"; exit 1
  fi
  [ -e /home/claude/gtd ] || ln -s "$REPO" /home/claude/gtd
  mkdir -p "$L"; date +%s > "$L/_prova_inizio"
  # Un solo ramo di prova, "prova", sovrascritto a ogni prova: si scrive subito all'avvio, così da fuori si vede se la
  # prova è partita ("Prova avviata") o finita ("Prova ... non pubblicata"). Niente rami nuovi per ogni prova.
  git commit -q --allow-empty -m "Prova avviata ${OGGI} $(TZ=Europe/Rome date +%H:%M)" && git push -q -f origin HEAD:refs/heads/prova 2>/dev/null \
    || echo "AVVISO: segnale di avvio non salvato sul ramo prova"
  echo "PROVA v8 pronta: ramo v8 con l'archivio fino a ieri (base $(git rev-parse --short "$BASE"))."
  echo "Da qui: ISTRUZIONI.md di questo ramo, con GTD_PROVA=1 davanti a pubblica.sh; niente Archivio Claude."
  ;;
chiudi)
  PDF="${2:?pdf}"; D="redazione/collaudi/prova-v8-${OGGI}"; mkdir -p "$D"
  cp -f "$PDF" "$D/prova.pdf"
  for f in fatti.json riempimento.json voce_indice.json testo.json ripetizioni.json dati.json revisione.json desk_proposta.json desk_ok.json; do [ -f "$L/$f" ] && cp -f "$L/$f" "$D/"; done
  T0="$(cat "$L/_prova_inizio" 2>/dev/null || echo 0)"
  { echo "data: $OGGI"; echo "minuti: $(( ( $(date +%s) - T0 ) / 60 ))"; echo "fine: $(TZ=Europe/Rome date +%H:%M)"; } > "$D/tempi.txt"
  git checkout -q -- edizioni.json 2>/dev/null
  git add -f "$D" && git commit -q -m "Prova v8 del ${OGGI} (non pubblicata)" || { echo "Prova: niente da salvare"; exit 1; }
  if git push -q -f origin "HEAD:refs/heads/prova" 2>/dev/null; then echo "Prova: salvata sul ramo prova ($(cat "$D/tempi.txt" | tr '\n' ' '))"
  else echo "Prova: NON salvata (push del ramo di prova rifiutato)"; fi
  ;;
*) echo "uso: prova_v8.sh avvio | chiudi <pdf>"; exit 1;;
esac
