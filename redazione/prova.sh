#!/usr/bin/env bash
# Prova generale con l'attività vera, senza pubblicare. Il ramo principale non viene mai toccato.
#   bash redazione/prova.sh avvio [AAAA-MM-GG] [--ramo <ramo>]   con --ramo prende da solo l'ultimo <ramo> di GitHub (senza,
#                                         prova il ramo dove sei); il commit provato è la sua punta, prima di ogni merge
#   bash redazione/prova.sh chiudi "<pdf>"                   alla fine: salva PDF, schede, sorgenti, misure ed esito sul ramo prova
#   bash redazione/prova.sh chiudi --non-riuscita "<motivo>"   la prova non è arrivata al PDF: lo dice sul ramo prova
#   bash redazione/prova.sh esito                            legge dal ramo prova di GitHub l'ultima prova, in JSON:
#                                         {"esito": "in-corso"|"chiusa"|"non-riuscita", "commit", "data", "ramo", ...}
#                                         esce con 0 (chiusa), 2 (in corso), 1 (non riuscita o nessuna prova)
# L'esito di prova.sh dice se la prova è arrivata in fondo e su quale commit; se l'edizione va bene lo decide chi legge il
# PDF (prova.esito nel Registro, ARCHITETTURA.md §5).
# avvio: porta nel ramo in prova l'archivio del ramo principale fino all'edizione di IERI (memoria, ripetizioni,
# scommessa), così l'edizione si rifà da capo. Con una data (un giorno di borsa) la prova vale per quel giorno: serve nel
# fine settimana per provare l'edizione del lunedì. La data vive in redazione/PROVA_DATA, mai committata.
set -u
REPO="$(git rev-parse --show-toplevel)"; cd "$REPO" || exit 1
L="${GTD_LAVORO:-/home/claude/lavoro}"
RAMO="$(git rev-parse --abbrev-ref HEAD)"
AZIONE="${1:-}"; shift 2>/dev/null || true
case "$AZIONE" in
avvio)
  DATA=""; DA_GITHUB=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --ramo) DA_GITHUB="${2:-}"; [ -n "$DA_GITHUB" ] || { echo "PROVA NON POSSIBILE: --ramo vuole il nome del ramo"; exit 1; }; shift;;
      *) [ -z "$DATA" ] || { echo "PROVA NON POSSIBILE: argomento in più '$1'"; exit 1; }; DATA="$1";;
    esac
    shift
  done
  if [ -n "$DA_GITHUB" ]; then
    [ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "PROVA NON POSSIBILE: modifiche non salvate in questa copia"; exit 1; }
    git fetch -q --depth=60 origin "+refs/heads/$DA_GITHUB:refs/remotes/origin/$DA_GITHUB" "+refs/heads/main:refs/remotes/origin/main" 2>/dev/null \
      || { echo "PROVA NON POSSIBILE: il ramo '$DA_GITHUB' non si scarica da GitHub"; exit 1; }
    git checkout -q -B "$DA_GITHUB" "origin/$DA_GITHUB" || { echo "PROVA NON POSSIBILE: checkout di '$DA_GITHUB'"; exit 1; }
    RAMO="$DA_GITHUB"
  fi
  case "$RAMO" in main|HEAD|prova) echo "PROVA NON POSSIBILE: sono su '$RAMO', serve il ramo da provare"; exit 1;; esac
  if [ -n "$DATA" ]; then
    echo "$DATA" | grep -qE '^20[0-9]{2}-[0-9]{2}-[0-9]{2}$' || { echo "PROVA NON POSSIBILE: data '$DATA' non valida (AAAA-MM-GG)"; exit 1; }
    echo "$DATA" > redazione/PROVA_DATA
  fi
  OGGI="$(cat redazione/PROVA_DATA 2>/dev/null || TZ=Europe/Rome date +%F)"
  PROVATO="$(git rev-parse HEAD)"   # il commit provato: la punta del ramo, prima che entri l'archivio del ramo principale
  git config user.name "PaoloGom"; git config user.email "PaoloGom@users.noreply.github.com"
  E="$(git log origin/main --format=%H --grep="^Edizione #[0-9]* - ${OGGI}" -1)"
  BASE="origin/main"; [ -n "$E" ] && BASE="${E}^"
  if ! git merge -q --no-edit "$BASE" >/dev/null 2>&1; then
    git merge --abort >/dev/null 2>&1; echo "PROVA NON POSSIBILE: il ramo $RAMO non si unisce al ramo principale (conflitto)"; exit 1
  fi
  LINK="${GTD_LINK:-/home/claude/gtd}"; [ -e "$LINK" ] || ln -s "$REPO" "$LINK"
  mkdir -p "$L"; date +%s > "$L/_prova_inizio"; echo "$PROVATO" > "$L/_prova_commit"
  # Un solo ramo di prova, "prova", sovrascritto a ogni prova: si scrive subito all'avvio, così da fuori si vede se la
  # prova è partita ("Prova avviata") o finita ("Prova ... non pubblicata"). Niente rami nuovi per ogni prova.
  # Le righe Prova-* in fondo al messaggio le legge "prova.sh esito".
  git commit -q --allow-empty -m "Prova avviata ${OGGI} $(TZ=Europe/Rome date +%H:%M) (ramo ${RAMO})

Prova-Data: ${OGGI}
Prova-Ramo: ${RAMO}
Prova-Commit: ${PROVATO}" && git push -q -f origin HEAD:refs/heads/prova 2>/dev/null \
    || echo "AVVISO: segnale di avvio non salvato sul ramo prova"
  echo "PROVA pronta: ramo $RAMO (commit provato $(git rev-parse --short "$PROVATO")) con l'archivio fino a ieri (base $(git rev-parse --short "$BASE")), edizione del ${OGGI}."
  echo "Da qui: ISTRUZIONI.md di questo ramo, con GTD_PROVA=1 davanti a pubblica.sh; niente Archivio Claude."
  ;;
chiudi)
  OGGI="$(cat redazione/PROVA_DATA 2>/dev/null || TZ=Europe/Rome date +%F)"
  D="redazione/collaudi/prova-${OGGI}"; mkdir -p "$D"
  PROVATO="$(cat "$L/_prova_commit" 2>/dev/null || echo "")"
  T0="$(cat "$L/_prova_inizio" 2>/dev/null || echo 0)"; MINUTI=$(( ( $(date +%s) - T0 ) / 60 ))
  scrivi_esito() {  # scrivi_esito <esito> <motivo>: esito.json, letto da "prova.sh esito"
    python3 - "$D/esito.json" "$1" "$2" "$OGGI" "$RAMO" "$PROVATO" "$MINUTI" "$(TZ=Europe/Rome date +%H:%M)" <<'PY'
import json, os, sys
f, esito, motivo, data, ramo, commit, minuti, fine = sys.argv[1:]
d = {"esito": esito, "data": data, "ramo": ramo, "commit": commit, "minuti": int(minuti), "fine": fine,
     "file": sorted(x for x in os.listdir(os.path.dirname(f)) if x != "esito.json")}
if motivo:
    d["motivo"] = motivo
json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
PY
  }
  if [ "${1:-}" = "--non-riuscita" ]; then
    scrivi_esito "non-riuscita" "${2:-senza motivo}"
    git add -f "$D" && git commit -q -m "Prova del ${OGGI} dal ramo ${RAMO} non riuscita" || { echo "Prova: niente da salvare"; exit 1; }
    git push -q -f origin "HEAD:refs/heads/prova" 2>/dev/null && echo "Prova: non riuscita, scritto sul ramo prova" || echo "Prova: NON salvata (push del ramo di prova rifiutato)"
    exit 0
  fi
  PDF="${1:?pdf}"
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
  for f in redazione/pronostici/*-settimana.json redazione/scommessa/pagella.json; do [ -f "$f" ] && [ -n "$(git status --porcelain "$f")" ] && cp -f "$f" "$D/"; done
  { echo "data: $OGGI"; echo "ramo: $RAMO"; echo "minuti: $MINUTI"; echo "fine: $(TZ=Europe/Rome date +%H:%M)"; } > "$D/tempi.txt"
  scrivi_esito "chiusa" ""
  git checkout -q -- edizioni.json 2>/dev/null
  git add -f "$D" && git commit -q -m "Prova del ${OGGI} dal ramo ${RAMO} (non pubblicata)" || { echo "Prova: niente da salvare"; exit 1; }
  if git push -q -f origin "HEAD:refs/heads/prova" 2>/dev/null; then echo "Prova: salvata sul ramo prova ($(cat "$D/tempi.txt" | tr '\n' ' '))"
  else echo "Prova: NON salvata (push del ramo di prova rifiutato)"; fi
  ;;
esito)
  git fetch -q --depth=5 origin "+refs/heads/prova:refs/remotes/origin/prova" 2>/dev/null || { echo '{"esito": "nessuna"}'; exit 1; }
  T="refs/remotes/origin/prova"
  F=$(git show --name-only --format= "$T" | grep -E '^redazione/collaudi/prova-[0-9-]+/esito\.json$' | head -1)
  if [ -n "$F" ]; then
    git show "$T:$F"; echo
    [ "$(git show "$T:$F" | python3 -c 'import json,sys; print(json.load(sys.stdin)["esito"])')" = "chiusa" ] && exit 0 || exit 1
  fi
  MSG=$(git log -1 --format=%B "$T")
  if echo "$MSG" | grep -q '^Prova avviata'; then
    python3 -c 'import json,re,sys; m=sys.argv[1]; g=lambda k: (re.search("^Prova-"+k+": (.*)$", m, re.M) or [None, ""])[1]
print(json.dumps({"esito": "in-corso", "data": g("Data"), "ramo": g("Ramo"), "commit": g("Commit")}, ensure_ascii=False))' "$MSG"
    exit 2
  fi
  echo '{"esito": "nessuna"}'; exit 1
  ;;
*) echo "uso: prova.sh avvio [AAAA-MM-GG] [--ramo <ramo>] | chiudi <pdf> | chiudi --non-riuscita <motivo> | esito"; exit 1;;
esac
