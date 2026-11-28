#!/usr/bin/env bash
# Prova generale con l'attività vera, senza pubblicare. Il ramo principale non viene mai toccato.
#   bash redazione/prova.sh avvio [AAAA-MM-GG] [--ramo <ramo>]   con --ramo prende da solo l'ultimo <ramo> di GitHub (senza,
#                                         prova il ramo dove sei); il commit provato è la sua punta, prima di ogni merge
#   bash redazione/prova.sh chiudi "<pdf>"                   alla fine: salva PDF, schede, sorgenti, misure ed esito sul ramo prova;
#                                         se non salva stampa "PROVA NON SALVATA: <che cosa manca e che cosa fare>" ed esce con 1
#   bash redazione/prova.sh chiudi --non-riuscita "<motivo>"   la prova non è arrivata in fondo: lo scrive sul ramo prova, sopra la
#                                         prova in corso che legge da GitHub (vale da qualunque clone, anche senza i file della sessione)
#   bash redazione/prova.sh esito                            legge dal ramo prova di GitHub l'ultima prova, in JSON:
#                                         {"esito": "in-corso"|"chiusa"|"non-riuscita", "commit", "data", "ramo", ...}
#                                         esce con 0 (chiusa), 2 (in corso), 1 (non riuscita o nessuna prova)
# L'esito di prova.sh dice se la prova è arrivata in fondo e su quale commit; se l'edizione va bene lo decide chi legge il
# PDF (prova.esito nel Registro, ARCHITETTURA.md §5).
# avvio: porta nel ramo in prova l'archivio del ramo principale fino all'edizione di IERI (memoria, ripetizioni,
# scommessa), così l'edizione si rifà da capo. Con una data (un giorno di borsa) la prova vale per quel giorno: serve nel
# fine settimana per provare l'edizione del lunedì. La data vive in redazione/PROVA_DATA, mai committata.
# Il repository è quello in cui sta questo script, seguendo i collegamenti: la sessione lo lancia dalla cartella di lavoro
# come /home/claude/gtd/redazione/prova.sh, e la cartella da cui lo si lancia non conta (G-71: il 28/11/2026 "chiudi",
# lanciato da fuori, cercava il repository nella cartella corrente, non salvava nulla e la prova restava in corso).
set -u
DA="$PWD"; IO="$(readlink -f "${BASH_SOURCE[0]:-}" 2>/dev/null)"
REPO="$([ -f "$IO" ] && git -C "$(dirname "$IO")" rev-parse --show-toplevel 2>/dev/null)"
[ -n "$REPO" ] && cd "$REPO" 2>/dev/null \
  || { echo "PROVA NON POSSIBILE: lo script ${IO:-$0} non sta dentro un repository git (si lancia dal clone: <clone>/redazione/prova.sh)"; exit 1; }
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
  # gli argomenti prima di toccare qualunque ramo: un avvio sbagliato non deve azzerare il ramo di una prova in corso
  if [ -n "$DATA" ]; then
    echo "$DATA" | grep -qE '^20[0-9]{2}-[0-9]{2}-[0-9]{2}$' || { echo "PROVA NON POSSIBILE: data '$DATA' non valida (AAAA-MM-GG)"; exit 1; }
  fi
  # il collegamento da cui il lavoro del mattino raggiunge il kit deve portare a questo repository, non a un altro
  LINK="${GTD_LINK:-/home/claude/gtd}"
  if [ -e "$LINK" ]; then
    [ "$(cd -P "$LINK" 2>/dev/null && pwd -P)" = "$(pwd -P)" ] || { echo "PROVA NON POSSIBILE: $LINK porta a un altro repository ($(readlink -f "$LINK")), non a questo ($REPO)"; exit 1; }
  else
    ln -sfn "$REPO" "$LINK" 2>/dev/null || { echo "PROVA NON POSSIBILE: il collegamento $LINK a questo repository non si crea"; exit 1; }
  fi
  if [ -n "$DA_GITHUB" ]; then
    echo "$DA_GITHUB" | grep -qE '^(main|HEAD|prova)$' && { echo "PROVA NON POSSIBILE: '$DA_GITHUB' non è un ramo da provare"; exit 1; }
    [ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "PROVA NON POSSIBILE: modifiche non salvate in questa copia"; exit 1; }
    git fetch -q --depth=60 origin "+refs/heads/$DA_GITHUB:refs/remotes/origin/$DA_GITHUB" "+refs/heads/main:refs/remotes/origin/main" 2>/dev/null \
      || { echo "PROVA NON POSSIBILE: il ramo '$DA_GITHUB' non si scarica da GitHub"; exit 1; }
    git checkout -q -B "$DA_GITHUB" "origin/$DA_GITHUB" || { echo "PROVA NON POSSIBILE: checkout di '$DA_GITHUB'"; exit 1; }
    RAMO="$DA_GITHUB"
  fi
  case "$RAMO" in main|HEAD|prova) echo "PROVA NON POSSIBILE: sono su '$RAMO', serve il ramo da provare"; exit 1;; esac
  [ -z "$DATA" ] || echo "$DATA" > redazione/PROVA_DATA
  OGGI="$(cat redazione/PROVA_DATA 2>/dev/null || TZ=Europe/Rome date +%F)"
  PROVATO="$(git rev-parse HEAD)"   # il commit provato: la punta del ramo, prima che entri l'archivio del ramo principale
  git config user.name "PaoloGom"; git config user.email "PaoloGom@users.noreply.github.com"
  E="$(git log origin/main --format=%H --grep="^Edizione #[0-9]* - ${OGGI}" -1)"
  BASE="origin/main"; [ -n "$E" ] && BASE="${E}^"
  if ! git merge -q --no-edit "$BASE" >/dev/null 2>&1; then
    git merge --abort >/dev/null 2>&1; echo "PROVA NON POSSIBILE: il ramo $RAMO non si unisce al ramo principale (conflitto)"; exit 1
  fi
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
  # Ogni uscita senza la prova salvata è una riga "PROVA NON SALVATA: <che cosa manca>: <che cosa fare>" e uscita 1: la
  # sessione la riporta, sistema e rilancia, oppure chiude con --non-riuscita. Mai un "niente da salvare" che passa per fatto.
  COME="bash $0 chiudi --non-riuscita \"<motivo>\""
  non_salvata() { echo "PROVA NON SALVATA: $1"; exit 1; }
  esito_json() {  # esito_json <esito> <motivo> <cartella dei file salvati, o "">: l'esito in JSON, letto da "prova.sh esito"
    python3 - "$1" "$2" "$3" "$OGGI" "$RAMO" "$PROVATO" "$MINUTI" "$(TZ=Europe/Rome date +%H:%M)" <<'PY'
import json, os, sys
esito, motivo, cartella, data, ramo, commit, minuti, fine = sys.argv[1:]
d = {"esito": esito, "data": data, "ramo": ramo, "commit": commit, "minuti": int(minuti), "fine": fine,
     "file": sorted(x for x in os.listdir(cartella) if x != "esito.json") if cartella else []}
if motivo:
    d["motivo"] = motivo
json.dump(d, sys.stdout, ensure_ascii=False, indent=1)
PY
  }
  spinta() {  # spinta <uscita di git push>: il motivo del rifiuto in una riga, senza credenziali
    local r; r="$(echo "$1" | grep -iE "error|rejected|denied|fatal" | head -1 | sed -E 's#//[^/@ ]*@#//#g' | cut -c1-120)"; echo "${r:-push rifiutato}"
  }
  if [ "${1:-}" = "--non-riuscita" ]; then
    # La prova in corso si legge dal ramo prova di GitHub (le righe Prova-* dell'avvio) e l'esito le si scrive sopra, senza
    # toccare né il ramo né i file di questa copia: vale dalla sessione della prova e da qualunque altro clone (una sessione
    # caduta la chiude chi aspetta). Una prova già chiusa non si riscrive.
    T="refs/remotes/origin/prova"
    git fetch -q origin "+refs/heads/prova:$T" 2>/dev/null || non_salvata "il ramo prova non si scarica da GitHub: rilancia lo stesso comando"
    MSG="$(git log -1 --format=%B "$T")"
    echo "$MSG" | grep -q '^Prova avviata' || non_salvata "su GitHub non c'è una prova in corso da chiudere (l'ultima: bash $0 esito)"
    campo() { echo "$MSG" | sed -n "s/^Prova-$1: //p" | head -1; }
    OGGI="$(campo Data)"; RAMO="$(campo Ramo)"; PROVATO="$(campo Commit)"
    [ -n "$OGGI" ] && [ -n "$PROVATO" ] || non_salvata "la prova in corso su GitHub non dice data e commit provato: la sostituisce il prossimo avvio"
    MINUTI=$(( ( $(date +%s) - $(git log -1 --format=%ct "$T") ) / 60 ))
    TMPD="$(mktemp -d)"
    C="$({ export GIT_INDEX_FILE="$TMPD/indice"
           B="$(esito_json "non-riuscita" "${2:-senza motivo}" "" | git hash-object -w --stdin)" && [ -n "$B" ] && git read-tree "$T" \
             && git update-index --add --cacheinfo "100644,$B,redazione/collaudi/prova-${OGGI}/esito.json" && A="$(git write-tree)" \
             && git -c user.name="PaoloGom" -c user.email="PaoloGom@users.noreply.github.com" commit-tree "$A" -p "$T" \
                  -m "Prova del ${OGGI} dal ramo ${RAMO} non riuscita"; } 2>/dev/null)"
    rm -rf "$TMPD"
    [ -n "$C" ] || non_salvata "il commit dell'esito non si crea in questa copia ($REPO): rilancia lo stesso comando"
    ERR="$(git push -q origin "$C:refs/heads/prova" 2>&1)" || non_salvata "GitHub non ha preso il ramo prova ($(spinta "$ERR")): rilancia lo stesso comando"
    echo "Prova: non riuscita, scritto sul ramo prova (prova del ${OGGI}, ramo ${RAMO}, commit provato $(echo "$PROVATO" | cut -c1-7))"
    exit 0
  fi
  PDF="${1:-}"; [ -n "$PDF" ] || non_salvata "chiudi vuole il PDF dell'edizione (bash $0 chiudi \"<pdf>\"). Se al PDF non sei arrivato: $COME"
  case "$PDF" in /*) ;; *) PDF="$DA/$PDF";; esac
  OGGI="$(cat redazione/PROVA_DATA 2>/dev/null || TZ=Europe/Rome date +%F)"
  PROVATO="$(cat "$L/_prova_commit" 2>/dev/null)"
  [ -n "$PROVATO" ] || non_salvata "in $L non c'è una prova avviata (manca _prova_commit: l'avvio si fa in questa sessione, con la stessa cartella di lavoro). $COME"
  git merge-base --is-ancestor "$PROVATO" HEAD 2>/dev/null \
    || non_salvata "questa copia ($REPO, ramo $RAMO) non è quella dove è stata avviata la prova (non contiene il commit provato $(echo "$PROVATO" | cut -c1-7)). $COME"
  [ -s "$PDF" ] || non_salvata "il PDF '$PDF' non c'è o è vuoto: rilancia con il percorso del PDF dell'edizione. Se al PDF non sei arrivato: $COME"
  [ -s "$L/edizione_${OGGI}.py" ] || non_salvata "in $L manca edizione_${OGGI}.py, il testo dell'edizione del ${OGGI} (senza, la prova non si può rifare né collaudare): mettilo lì con quel nome e rilancia. Se non c'è: $COME"
  D="redazione/collaudi/prova-${OGGI}"; mkdir -p "$D"
  # la scheda dell'edizione come andrebbe sul sito e la sua pagina in testo: servono a provare il sito senza pubblicare.
  # La voce è quella della data della prova; a un secondo chiudi non è più in edizioni.json (il primo lo ha rimesso
  # com'era) e vale la scheda già salvata.
  python3 - "$D" "$OGGI" <<'PY' 2>/dev/null || { rmdir "$D" 2>/dev/null; non_salvata "in edizioni.json non c'è la voce dell'edizione del ${OGGI} (la scheda del sito): lancia edizioni_voce.py (ISTRUZIONI.md, passo Cancello e consegna), poi di nuovo questo comando. Se non si può: $COME"; }
import json, os, shutil, sys
d, oggi = sys.argv[1:]
f = os.path.join(d, "voce_sito.json")
v = [x for x in json.load(open("edizioni.json", encoding="utf-8")) if x.get("data") == oggi]
if len(v) == 1:
    json.dump(v[0], open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    p = f"e/{v[0]['numero']:03d}.html"
    if os.path.exists(p):
        shutil.copy(p, os.path.join(d, "pagina.html"))
elif not (os.path.exists(f) and json.load(open(f, encoding="utf-8")).get("data") == oggi):
    sys.exit(1)
PY
  git checkout -q -- edizioni.json 2>/dev/null   # la voce della prova non resta nell'indice di questa copia
  cp -f "$PDF" "$D/prova.pdf" || non_salvata "il PDF '$PDF' non si copia in $REPO/$D: rilancia lo stesso comando. Se si ripete: $COME"
  for f in fatti.json riempimento.json voce_indice.json testo.json ripetizioni.json dati.json contesto.json stato.json verdetto.json revisione.json desk_proposta.json desk_ok.json; do [ -f "$L/$f" ] && cp -f "$L/$f" "$D/"; done
  cp -f "$L/edizione_${OGGI}.py" "$D/edizione.py"   # il testo scritto
  for f in redazione/pronostici/*-settimana.json redazione/scommessa/pagella.json; do [ -f "$f" ] && [ -n "$(git status --porcelain "$f")" ] && cp -f "$f" "$D/"; done
  T0="$(cat "$L/_prova_inizio" 2>/dev/null)"; MINUTI=$(( ( $(date +%s) - ${T0:-0} ) / 60 ))
  { echo "data: $OGGI"; echo "ramo: $RAMO"; echo "minuti: $MINUTI"; echo "fine: $(TZ=Europe/Rome date +%H:%M)"; } > "$D/tempi.txt"
  esito_json "chiusa" "" "$D" > "$D/esito.json" && [ -s "$D/esito.json" ] \
    || non_salvata "l'esito non si scrive in $REPO/$D: rilancia lo stesso comando. Se si ripete: $COME"
  # il commit c'è già se un chiudi di prima si è fermato al push: allora si spinge quello
  git add -f "$D" 2>/dev/null && { git diff --cached --quiet || git commit -q -m "Prova del ${OGGI} dal ramo ${RAMO} (non pubblicata)" >/dev/null 2>&1; } \
    || non_salvata "il commit della prova non si crea in $REPO: rilancia lo stesso comando. Se si ripete: $COME"
  ERR="$(git push -q -f origin "HEAD:refs/heads/prova" 2>&1)" \
    || non_salvata "GitHub non ha preso il ramo prova ($(spinta "$ERR")): i file sono pronti in questa copia, rilancia lo stesso comando. Se si ripete: $COME"
  echo "Prova: salvata sul ramo prova ($(cat "$D/tempi.txt" | tr '\n' ' '))"
  ;;
esito)
  # senza --depth: esito legge e basta, e con una profondità accorcerebbe la storia di questa copia (rami senza più base comune)
  git fetch -q origin "+refs/heads/prova:refs/remotes/origin/prova" 2>/dev/null || { echo '{"esito": "nessuna"}'; exit 1; }
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
