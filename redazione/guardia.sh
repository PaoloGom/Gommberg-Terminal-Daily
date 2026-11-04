#!/usr/bin/env bash
# Guardia d'avvio: l'attività programmata parte più volte al mattino (8:58, 9:58, 10:58). Solo la prima volta
# utile si fa l'edizione; le altre partenze sono recuperi automatici se la precedente si è fermata.
# Stampa UNA riga:
#   PROCEDI (tentativo N) ...      -> si fa l'edizione (e il diario registra AVVIO)
#   ESCI IN SILENZIO: <motivo>     -> la sessione finisce subito, senza messaggi né file
# Uso: bash /home/claude/gtd/redazione/guardia.sh   (dopo il pull del repository)
REPO="${GTD_REPO:-/home/claude/gtd}"; R="$REPO/redazione"; RAMO="${GTD_DIARIO_RAMO:-diario}"
OGGI_DIARIO=$(TZ=Europe/Rome date +%F)
timeout 60 git -C "$REPO" fetch -q --depth 1 origin +refs/heads/$RAMO:refs/remotes/origin/$RAMO 2>/dev/null
LOG=$(git -C "$REPO" show "refs/remotes/origin/$RAMO:$OGGI_DIARIO.log" 2>/dev/null)
ESITO=$(LOG="$LOG" python3 - "$REPO" <<'EOF'
import datetime as dt, json, os, sys
from zoneinfo import ZoneInfo
repo = sys.argv[1]
sys.path.insert(0, os.path.join(repo, "redazione"))
import giorni as G
ora = dt.datetime.now(ZoneInfo("Europe/Rome"))
oggi = G.oggi()
righe = [r.split(" ", 3) for r in os.environ.get("LOG", "").splitlines() if r.strip()]
avvii = sum(1 for r in righe if len(r) > 2 and r[2] == "AVVIO")
fine = [r for r in righe if len(r) > 2 and r[2] == "FINE"]
n = G.numero(oggi)
try:
    voci = json.load(open(os.path.join(repo, "edizioni.json"), encoding="utf-8"))
except Exception:
    voci = []
if any(v.get("numero") == n and v.get("data") == oggi.isoformat() for v in voci):
    print(f"ESCI IN SILENZIO: l'edizione #{n:03d} del {oggi:%d/%m} è già pubblicata"); sys.exit()
if fine:
    print(f"ESCI IN SILENZIO: la redazione di oggi ha già chiuso ({' '.join(fine[-1][2:])[:120]})"); sys.exit()
if not G.uscita(oggi) and avvii >= 1:
    print("ESCI IN SILENZIO: giorno senza borsa, già gestito dalla prima partenza"); sys.exit()
if righe:
    try:
        h, m, s = map(int, righe[-1][0].split(":"))
        ultima = ora.replace(hour=h, minute=m, second=s, microsecond=0)
        minuti = (ora - ultima).total_seconds() / 60
    except Exception:
        minuti = 999
    if 0 <= minuti < 45:
        print(f"ESCI IN SILENZIO: un'altra sessione sta lavorando (ultimo passo {righe[-1][2]} {minuti:.0f} minuti fa)"); sys.exit()
    ult = " ".join(righe[-1][2:])[:200]
    print(f"PROCEDI (tentativo {avvii + 1}) - recupero: la sessione precedente si è fermata dopo \"{ult}\" alle {righe[-1][0][:5]}. "
          f"Riparti da capo dal passo 0 e scrivi nel messaggio finale \"Edizione di recupero (tentativo {avvii + 1})\"")
else:
    print("PROCEDI (tentativo 1)")
EOF
)
echo "$ESITO"
case "$ESITO" in PROCEDI*) bash "$R/diario.sh" AVVIO "$(echo "$ESITO" | cut -c1-200)" >/dev/null ;; esac
exit 0
