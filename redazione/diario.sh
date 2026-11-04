#!/usr/bin/env bash
# Diario di bordo della redazione: una riga per passo, salvata subito sul ramo `diario` del repository
# (file AAAA-MM-GG.log, ora di Roma). Serve a sapere sempre dove si è fermata una sessione e a coordinare
# i tentativi di recupero (guardia.sh). Non tocca mai la cartella di lavoro né il ramo main.
# Uso: bash /home/claude/gtd/redazione/diario.sh PASSO "nota breve"
#   PASSO: AVVIO, DATI, RICERCA, FATTI, STESURA, CONTROLLI, REVISIONE, PUBBLICA, CONSEGNA, FINE
# Non fallisce mai (exit 0 sempre): un diario non scritto non deve fermare l'edizione.
REPO="${GTD_REPO:-/home/claude/gtd}"; L="${GTD_LAVORO:-/home/claude/lavoro}"
RAMO="${GTD_DIARIO_RAMO:-diario}"; PASSO="${1:-NOTA}"; NOTA="$(echo "${2:-}" | tr '\n' ' ' | cut -c1-300)"
D=$(TZ=Europe/Rome date +%F); T=$(TZ=Europe/Rome date +%H:%M:%S)
SID="${CLAUDE_CODE_SESSION_ID:-sessione}"; SID="${SID:0:8}"
RIGA="$T $SID $PASSO $NOTA"
mkdir -p "$L" 2>/dev/null; echo "$RIGA" >> "$L/diario.log" 2>/dev/null
[ "${GTD_DIARIO_LOCALE:-0}" = "1" ] && { echo "diario (solo locale): $RIGA"; exit 0; }
cd "$REPO" 2>/dev/null || { echo "diario: repository assente"; exit 0; }
export GIT_AUTHOR_NAME=PaoloGom GIT_AUTHOR_EMAIL=PaoloGom@users.noreply.github.com
export GIT_COMMITTER_NAME=PaoloGom GIT_COMMITTER_EMAIL=PaoloGom@users.noreply.github.com
for prova in 1 2 3; do
  IDX=$(mktemp -u)   # solo il nome: l'indice temporaneo lo crea read-tree, mai l'indice del clone
  PADRE=""; PRIMA=""
  if timeout 60 git fetch -q --depth 1 origin +refs/heads/$RAMO:refs/remotes/origin/$RAMO 2>>"$L/diario.err"; then
    PADRE=$(git rev-parse -q --verify refs/remotes/origin/$RAMO 2>/dev/null)
  elif git ls-remote --exit-code origin refs/heads/$RAMO >/dev/null 2>&1; then
    sleep 5; continue   # il ramo esiste ma non si è letto: mai ripartire da un diario vuoto
  fi
  if [ -n "$PADRE" ]; then
    GIT_INDEX_FILE="$IDX" git read-tree "$PADRE"
    PRIMA=$(git show "$PADRE:$D.log" 2>/dev/null)
  else
    GIT_INDEX_FILE="$IDX" git read-tree --empty
  fi
  BLOB=$( { [ -n "$PRIMA" ] && printf '%s\n' "$PRIMA"; printf '%s\n' "$RIGA"; } | git hash-object -w --stdin)
  GIT_INDEX_FILE="$IDX" git update-index --add --cacheinfo 100644,"$BLOB","$D.log"
  ALBERO=$(GIT_INDEX_FILE="$IDX" git write-tree); rm -f "$IDX"
  if [ -n "$PADRE" ]; then C=$(git commit-tree "$ALBERO" -p "$PADRE" -m "diario $D $PASSO")
  else C=$(git commit-tree "$ALBERO" -m "diario $D $PASSO"); fi
  if timeout 60 git push -q origin "$C:refs/heads/$RAMO" 2>>"$L/diario.err"; then
    echo "diario: $RIGA"; exit 0
  fi
  sleep 3
done
echo "diario: NON salvato sul repository (solo locale): $RIGA"
exit 0
