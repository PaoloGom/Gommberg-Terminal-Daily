#!/usr/bin/env bash
# Pubblicazione sul sito: copia PDF e registro fatti, commit, push con verifica PUSH_OK (fino a 3 tentativi).
# Uso: bash /home/claude/gtd/redazione/pubblica.sh "<pdf>" <N> <AAAA-MM-GG> [fatti.json]
# Prima: edizioni.json già aggiornato con edizioni_voce.py. Dopo: archivio Claude (Artifact) e messaggio finale.
# GTD_PROVA=1: stampa i comandi git senza eseguirli (né commit né push). GTD_REPO per un'altra copia del repository.
# Ultima riga: "Sito: aggiornato (commit X)" oppure "Sito: NON aggiornato - <errore>".
set -u
PDF="${1:?pdf}"; N="${2:?numero}"; DATA="${3:?data}"; FATTI="${4:-/home/claude/lavoro/fatti.json}"
REPO="${GTD_REPO:-/home/claude/gtd}"; PROVA="${GTD_PROVA:-0}"
NNN=$(printf "%03d" "$N"); DEST="pdf/${DATA}-gommberg-${NNN}.pdf"
fail() { echo "Sito: NON aggiornato - $1"; exit 1; }
run() { if [ "$PROVA" = "1" ]; then echo "[prova] $*"; else "$@"; fi; }

[ -f "$PDF" ] || fail "PDF non trovato: $PDF"
python3 - "$REPO/edizioni.json" "$N" "$DATA" "$DEST" 2>/dev/null <<'EOF' || fail "edizioni.json non pronto (lancia prima edizioni_voce.py)"
import json, sys
p, n, d, f = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
v = [x for x in json.load(open(p, encoding="utf-8")) if x["numero"] == n]
assert len(v) == 1 and v[0]["data"] == d and v[0]["file"] == f, "voce assente, duplicata o incoerente"
EOF

run cp -f "$PDF" "$REPO/$DEST" || fail "copia del PDF"
if [ -f "$FATTI" ]; then run cp -f "$FATTI" "$REPO/redazione/fatti/${DATA}.json"; else echo "AVVISO: $FATTI assente, registro fatti non copiato"; fi
run git -C "$REPO" config user.name "PaoloGom"
run git -C "$REPO" config user.email "PaoloGom@users.noreply.github.com"
# Elenco fisso: mai redazione/collaudi (dati di prova)
run git -C "$REPO" add pdf edizioni.json redazione/pronostici redazione/fatti redazione/scommessa || fail "git add"
if [ "$PROVA" != "1" ] && git -C "$REPO" diff --cached --quiet; then
  echo "AVVISO: niente di nuovo da committare"
else
  run git -C "$REPO" commit -q -m "Edizione #${NNN} - ${DATA}" || fail "git commit"
fi

if [ "$PROVA" = "1" ]; then
  echo "[prova] git push origin main + verifica ls-remote = rev-parse HEAD -> PUSH_OK (fino a 3 tentativi, pull --rebase tra uno e l'altro)"
  echo "Sito: PROVA - nessun push (commit $(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo '?'))"
  exit 0
fi

ERR=""
for i in 1 2 3; do
  OUT=$(git -C "$REPO" push origin main 2>&1); ERR=$(echo "$OUT" | grep -iE "error|rejected|denied|fatal" | head -1)
  if [ "$(git -C "$REPO" ls-remote origin refs/heads/main 2>/dev/null | cut -f1)" = "$(git -C "$REPO" rev-parse HEAD)" ]; then
    echo "PUSH_OK (tentativo $i)"
    echo "Sito: aggiornato (commit $(git -C "$REPO" rev-parse --short HEAD))"
    exit 0
  fi
  echo "Tentativo $i fallito: ${ERR:-verifica ls-remote diversa da HEAD}"
  [ $i -lt 3 ] || break
  PULL=$(git -C "$REPO" pull -q --rebase origin main 2>&1)
  if [ -d "$REPO/.git/rebase-merge" ] || [ -d "$REPO/.git/rebase-apply" ]; then
    git -C "$REPO" rebase --abort >/dev/null 2>&1
    fail "conflitto nel pull --rebase ($(echo "$PULL" | grep -iE "conflict|error" | head -1 | cut -c1-100))"
  fi
done
fail "${ERR:-push non verificato dopo 3 tentativi}"
