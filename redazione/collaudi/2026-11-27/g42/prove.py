"""G-42, prove sulle edizioni vere dal 16 al 27/11: per ogni giorno la memoria che avrebbe visto chi faceva la scaletta
(memoria_AAAA-MM-GG.txt) e che cosa il desk avrebbe visto segnalato sui pezzi usciti quel giorno (desk_AAAA-MM-GG.txt).
Nessuna rete, nessun modello: solo memoria.py sui sorgenti archiviati. Uso: python3 prove.py (dalla radice o da qui)."""
import glob, os, sys
QUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(QUI, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "redazione"))
import datetime as dt  # noqa: E402
import memoria as MEM  # noqa: E402

MEM.REPO = REPO
righe = []
for p in sorted(glob.glob(os.path.join(REPO, "redazione", "sorgenti", "2026-11-*", "edizione.py"))):
    d = os.path.basename(os.path.dirname(p))
    if not ("2026-11-16" <= d <= "2026-11-27"):
        continue
    voci = MEM.ultime(dt.date.fromisoformat(d), repo=REPO)
    t = MEM.testo_memoria(voci)
    open(os.path.join(QUI, f"memoria_{d}.txt"), "w", encoding="utf-8").write(t + "\n")
    letto = MEM._moduli_sorgente(p)
    MEM._desk(letto[1], os.path.join(os.path.dirname(p), "desk_ok.json"))
    seg = [f"{m['chiave']} «{m['titolo']}»: " + ("; ".join(MEM.segnala(m, voci)) or "niente") for m in letto[1]]
    open(os.path.join(QUI, f"desk_{d}.txt"), "w", encoding="utf-8").write("\n".join(seg) + "\n")
    righe.append(f"{d}: memoria {len(t)} caratteri, {len(voci)} pezzi; pezzi del giorno segnalati "
                 f"{sum(1 for x in seg if not x.endswith(': niente'))} su {len(seg)}")
print("\n".join(righe))
