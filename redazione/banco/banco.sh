#!/usr/bin/env bash
# Banco di prova di ogni modifica al kit (regole, controlli, modello, motore). Non lo usa la redazione del mattino.
# Uso: bash redazione/banco/banco.sh [riferimento git, default origin/main]
# 1. Tetti: ISTRUZIONI.md e appendici non crescono oltre il tetto (si comprime prima di aggiungere).
# 2. Confronto: rilancia i controlli del kit di riferimento e del kit modificato sulle stesse edizioni pubblicate;
#    stampa ogni controllo che cambia esito e le misure di stile prima/dopo.
# Lettura: un controllo che diventa ROSSO su edizioni pubblicate è voluto solo se la modifica lo dichiara
# (es. regola più stretta); altrimenti è un falso positivo da correggere prima di pubblicare.
# Esce con 1 se un tetto è superato o se il kit modificato va in errore.
set -u
REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); RIF="${1:-origin/main}"
TETTO_NUCLEO=16384; TETTO_APPENDICI=30720
OUT=$(mktemp -d); trap 'git -C "$REPO" worktree remove --force "$OUT/rif" >/dev/null 2>&1; rm -rf "$OUT"' EXIT
esito=0

n=$(wc -c < "$REPO/redazione/ISTRUZIONI.md"); a=$(cat "$REPO"/redazione/APP_*.md | wc -c)
echo "Tetti: ISTRUZIONI.md $n/$TETTO_NUCLEO byte | appendici $a/$TETTO_APPENDICI byte"
[ "$n" -gt "$TETTO_NUCLEO" ] && { echo "ROSSO: ISTRUZIONI.md oltre il tetto: comprimi prima di aggiungere"; esito=1; }
[ "$a" -gt "$TETTO_APPENDICI" ] && { echo "ROSSO: appendici oltre il tetto: comprimi prima di aggiungere"; esito=1; }

git -C "$REPO" worktree add --detach "$OUT/rif" "$RIF" >/dev/null 2>&1 || { echo "riferimento $RIF non trovato"; exit 1; }
python3 "$REPO/redazione/banco/misure.py" "$OUT/rif/redazione" "$REPO" --json "$OUT/prima.json" >/dev/null
python3 "$REPO/redazione/banco/misure.py" "$REPO/redazione" "$REPO" --json "$OUT/dopo.json" >/dev/null || { echo "ROSSO: il kit modificato va in errore"; exit 1; }

python3 - "$OUT/prima.json" "$OUT/dopo.json" "$RIF" <<'EOF'
import json, sys
prima = {r["numero"]: r for r in json.load(open(sys.argv[1]))}
dopo = {r["numero"]: r for r in json.load(open(sys.argv[2]))}
cambi = {}
for n, d in sorted(dopo.items()):
    p = prima.get(n)
    if not p: continue
    for k, x in d["controlli"].items():
        a, b = p["controlli"].get(k, {}).get("ok"), x["ok"]
        if a != b:
            cambi.setdefault((k, "ok -> ROSSO" if a else "ROSSO -> ok"), []).append((n, x["errori"][:2]))
print(f"Edizioni rilanciate: {len(dopo)} (#{min(dopo):03d}-#{max(dopo):03d}), kit di riferimento: {sys.argv[3]}")
if not cambi:
    print("Esiti dei controlli: nessun cambiamento")
for (k, verso), casi in cambi.items():
    print(f"- {k}: {verso} in {len(casi)} edizioni ({', '.join('#%03d' % n for n, _ in casi)})")
    for n, err in casi[:2]:
        for e in err: print(f"    #{n:03d} {e[:150]}")
chiavi = sorted({k for r in dopo.values() for k, v in r["misure"].items() if isinstance(v, (int, float))})
print("Misure (media sulle edizioni): " + " | ".join(
    f"{k} {sum(r['misure'].get(k, 0) for r in prima.values()) / len(prima):.1f} -> "
    f"{sum(r['misure'].get(k, 0) for r in dopo.values()) / len(dopo):.1f}" for k in chiavi))
EOF
exit $esito
