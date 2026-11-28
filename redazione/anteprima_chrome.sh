#!/usr/bin/env bash
# L'anteprima di una voce in locale con Chrome, dalla versione del codice che c'è in questa copia: le immagini che
# Paolo guarda prima dell'Ok (ARCHITETTURA.md §5, il capo sviluppo, punto 3). Non committa e non spinge nulla.
#   bash redazione/anteprima_chrome.sh g<NN> [pagina ...] [--sito <cartella> | --repo]
#     pagina      percorso dentro il sito servito (predefinita: index.html), per esempio archivio.html o e/035.html
#     --sito      serve una cartella già pronta (per esempio _sito di costruisci.py) invece di costruirla
#     --repo      serve il repository così com'è (per le pagine della redazione: newsletter, mail straordinarie)
#   Senza --sito né --repo costruisce il sito pubblico con redazione/sito/costruisci.py --anteprima in una cartella
#   temporanea. Ogni pagina esce in due larghezze (1280 e 390, il telefono) in
#   redazione/collaudi/AAAA-MM-GG/g<NN>/<pagina>-<larghezza>.png (data di Roma); il link da dare a Paolo è la pagina
#   del file su GitHub al commit che lo contiene.
# GTD_CHROME: il Chrome da usare (predefinito il primo tra google-chrome, chromium, chromium-browser); GTD_ALTEZZA:
# l'altezza della finestra (predefinita 2400). Se qualcosa manca stampa "ANTEPRIMA: FERMO - <causa>" ed esce con 1.
set -u
fermo() { echo "ANTEPRIMA: FERMO - $1"; exit 1; }
REPO="$(cd "$(dirname "$0")/.." && pwd)"
VOCE=""; PAGINE=(); SITO=""; DAL_REPO=0
while [ $# -gt 0 ]; do
  case "$1" in
    --sito) SITO="${2:-}"; [ -d "$SITO" ] || fermo "--sito vuole una cartella che esiste"; shift;;
    --repo) DAL_REPO=1;;
    -*) fermo "opzione sconosciuta: $1";;
    *) if [ -z "$VOCE" ]; then VOCE="$1"; else PAGINE+=("$1"); fi;;
  esac
  shift
done
echo "$VOCE" | grep -qE '^g[0-9]+$' || fermo "il primo argomento è la voce, come g66"
[ ${#PAGINE[@]} -gt 0 ] || PAGINE=(index.html)
CHROME="${GTD_CHROME:-$(command -v google-chrome || command -v chromium || command -v chromium-browser)}"
[ -n "$CHROME" ] && [ -x "$CHROME" ] || fermo "manca Chrome (google-chrome o chromium): l'anteprima non si fa a mano, la voce va Ferma"
ALTEZZA="${GTD_ALTEZZA:-2400}"
T=$(mktemp -d); SERVER=""
trap '[ -n "$SERVER" ] && kill "$SERVER" 2>/dev/null; rm -rf "$T"' EXIT
if [ -n "$SITO" ]; then RADICE="$(cd "$SITO" && pwd)"
elif [ "$DAL_REPO" = 1 ]; then RADICE="$REPO"
else
  RADICE="$T/sito"
  python3 "$REPO/redazione/sito/costruisci.py" "$RADICE" --anteprima > "$T/costruisci.txt" 2>&1 || fermo "costruisci.py: $(tail -1 "$T/costruisci.txt")"
fi
for p in "${PAGINE[@]}"; do [ -f "$RADICE/$p" ] || fermo "la pagina $p non c'è nel sito servito"; done
PORTA=$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
python3 -m http.server "$PORTA" --bind 127.0.0.1 --directory "$RADICE" > "$T/server.txt" 2>&1 &
SERVER=$!
python3 - "$PORTA" <<'PY' || fermo "il server locale non risponde"
import sys, time, urllib.request
for _ in range(50):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{sys.argv[1]}/", timeout=1); sys.exit(0)
    except Exception:
        time.sleep(0.2)
sys.exit(1)
PY
DEST="redazione/collaudi/$(TZ=Europe/Rome date +%F)/$VOCE"; mkdir -p "$REPO/$DEST"
FATTE=()
for p in "${PAGINE[@]}"; do
  nome=$(echo "${p%.html}" | tr '/' '_')
  for w in 1280 390; do
    out="$REPO/$DEST/$nome-$w.png"; rm -f "$out"
    timeout 90 "$CHROME" --headless=new --no-sandbox --disable-gpu --hide-scrollbars --virtual-time-budget=5000 \
      --window-size="$w,$ALTEZZA" --screenshot="$out" "http://127.0.0.1:$PORTA/$p" > "$T/chrome.txt" 2>&1
    [ -s "$out" ] || fermo "Chrome non ha salvato $p a $w: $(grep -v '^$' "$T/chrome.txt" | tail -1)"
    FATTE+=("$DEST/$nome-$w.png")
  done
done
echo "ANTEPRIMA: OK - ${#FATTE[@]} immagini in $DEST/ (da committare sul ramo $VOCE):"
printf '  %s\n' "${FATTE[@]}"
