#!/usr/bin/env bash
# Avvio della redazione: dipendenze, cartella di lavoro, giorno, numero, appendici, riepilogo dell'ultima edizione.
# Uso: bash /home/claude/gtd/redazione/prepara.sh [AAAA-MM-GG]   (data facoltativa, per le prove)
# Variabili: GTD_REPO (default /home/claude/gtd), GTD_LAVORO (default /home/claude/lavoro). Output <= 20 righe.
set -u
REPO="${GTD_REPO:-/home/claude/gtd}"; R="$REPO/redazione"; L="${GTD_LAVORO:-/home/claude/lavoro}"

# 1. Dipendenze (silenziose se già presenti)
MANCA=$(python3 - <<'EOF'
import importlib.util as u
m = {"reportlab": "reportlab", "matplotlib": "matplotlib", "svglib": "svglib", "PIL": "pillow", "pandas": "pandas", "numpy": "numpy"}
print(" ".join(p for k, p in m.items() if u.find_spec(k) is None))
EOF
)
if [ -n "$MANCA" ]; then
  pip install -q --break-system-packages $MANCA >/dev/null 2>&1 || pip install -q $MANCA >/dev/null 2>&1
  DEP="installate: $MANCA"
else
  DEP="ok"
fi
for t in pdftotext pdfinfo pdftoppm qpdf; do command -v $t >/dev/null || DEP="$DEP | MANCA $t (apt-get install -y poppler-utils qpdf)"; done

# 2. Cartella di lavoro con il kit (solo .py e svg/png del kit; i file dell'edizione restano in $L)
mkdir -p "$L"
# file del giorno prima: mai riusarli (dati stantii)
rm -f "$L"/dati.json "$L"/attuali.json "$L"/stato.json "$L"/verdetto.json "$L"/fatti.json "$L"/voce_indice.json "$L"/nuovi.json "$L"/redazione.json "$L"/edizione_20*.py
# kit: tutti i .py tranne lo stub del vecchio modello (il modello in vigore è edizione_modello_v6.py)
NK=0
for f in "$R"/*.py; do
  case "$(basename "$f")" in edizione_modello_20*.py) continue;; esac
  cp -f "$f" "$L"/ && NK=$((NK + 1))
done

# 3. Giorno, numero, appendici, riepilogo (in Python per robustezza)
GTD_DATA="${1:-}" python3 - "$REPO" "$L" "$NK" "$DEP" <<'EOF'
import datetime as dt, json, os, subprocess, sys
from zoneinfo import ZoneInfo
repo, lav, nk, dep = sys.argv[1:5]
sys.path.insert(0, os.path.join(repo, "redazione"))
import giorni as G

ora = dt.datetime.now(ZoneInfo("Europe/Rome"))
oggi = dt.date.fromisoformat(os.environ["GTD_DATA"]) if os.environ.get("GTD_DATA") else ora.date()
GG = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]
n = G.numero(oggi)
out = []
cut = lambda s, k=150: s if len(s) <= k else s[:k - 3] + "..."

if not G.uscita(oggi):
    motivo = "weekend" if oggi.weekday() >= 5 else "festivo (FESTIVI in gommberg_engine.py)"
    print(f"GTD {GG[oggi.weekday()]} {oggi:%d/%m/%Y} ore {ora:%H:%M} Roma: NIENTE EDIZIONE OGGI ({motivo}).")
    print("USCITA (b): manda a Paolo solo la riga \"Oggi borse chiuse: niente Gommberg, ci rivediamo al prossimo giorno di borsa\"; la sessione finisce qui.")
    sys.exit(0)

primo = G.primo_della_settimana(oggi)
lun = G.lunedi(oggi)
out.append(f"GTD {GG[oggi.weekday()]} {oggi:%d/%m/%Y} ore {ora:%H:%M} Roma | edizione #{n:03d} | "
           f"file: {oggi.isoformat()} Gommberg Terminal Daily #{n:03d}.pdf")
out.append(f"Lavoro: {lav} ({nk} .py del kit copiati) | dipendenze: {dep}")

# Appendici da leggere oggi
app = []
if primo:
    app.append("APP_LUNEDI.md (verdetto e pronostico)")
# Festività: giorno dopo una chiusura, chiusure parziali note vicine, dicembre
PARZIALI = {  # borse chiuse solo in parte (da verificare sul calendario ufficiale; dettagli in APP_FESTIVI.md)
    "2026-11-11": "USA: mercato dei Treasury chiuso (Veterans Day), borse aperte",
    "2026-11-26": "USA chiusa (Thanksgiving)", "2026-11-27": "USA: chiusura anticipata",
    "2026-12-24": "Italia e Germania chiuse, USA chiusura anticipata", "2026-12-31": "Italia e Germania chiuse",
    "2026-12-28": "Londra chiusa (Boxing Day)", "2027-01-18": "USA chiusa (Martin Luther King Day)",
    "2027-02-15": "USA chiusa (Presidents' Day)", "2027-03-29": "Europa chiusa (Lunedì dell'Angelo)",
    "2027-05-31": "USA chiusa (Memorial Day)", "2027-06-18": "USA chiusa (Juneteenth)",
    "2027-07-05": "USA chiusa (Independence Day)", "2027-09-06": "USA chiusa (Labor Day)"}
ieri = G.uscita_precedente(oggi)
# chiusure parziali tra l'ultima uscita e i prossimi 4 giorni (servono a cruscotto, calendario e agenda)
vicini = [f"{d[8:]}/{d[5:7]} {t}" for d, t in PARZIALI.items()
          if ieri <= dt.date.fromisoformat(d) <= oggi + dt.timedelta(days=4)]
buco = (oggi - ieri).days > (3 if oggi.weekday() == 0 else 1)
dicembre_mancante = oggi.month == 12 and not any(f.startswith(str(oggi.year + 1)) for f in G.FESTIVI)
if vicini or buco or dicembre_mancante:
    app.append("APP_FESTIVI.md")
out.append("Appendici oggi: " + (", ".join(app) if app else "nessuna") +
           " | se un controllo è rosso: APP_ERRORI.md | se un dato manca: APP_DATI.md")
if vicini:
    out.append("Festività: " + "; ".join(vicini))
if buco:
    out.append(f"Festività: ultima uscita il {ieri:%d/%m}, giorni di borsa saltati in mezzo")
if dicembre_mancante:
    out.append(f"DICEMBRE: aggiungi a FESTIVI le date del {oggi.year + 1} (APP_FESTIVI.md) e dillo nel messaggio finale")

# Scommessa: registro della settimana
reg = os.path.join(repo, "redazione", "pronostici", f"{lun.isoformat()}-settimana.json")
if primo:
    prec = os.path.join(repo, "redazione", "pronostici", f"{(lun - dt.timedelta(days=7)).isoformat()}-settimana.json")
    out.append(f"Scommessa: verdetto su {os.path.basename(prec)} ({'c' + chr(39) + 'è' if os.path.exists(prec) else 'MANCA'}), "
               f"nuovo registro {os.path.basename(reg)} ({'GIÀ ESISTE' if os.path.exists(reg) else 'da creare'})")
else:
    out.append(f"Scommessa: registro {os.path.basename(reg)} ({'ok' if os.path.exists(reg) else 'MANCA: vedi APP_LUNEDI.md'}); "
               f"attuali.json = chiusure ufficiali")

# Ultima edizione
try:
    voci = json.load(open(os.path.join(repo, "edizioni.json"), encoding="utf-8"))
except Exception as e:
    voci = []; out.append(f"edizioni.json illeggibile: {e}")
if voci:
    u = max(voci, key=lambda v: v["numero"])
    if any(v["numero"] == n for v in voci):
        out.append(f"USCITA (c): l'edizione #{n:03d} esiste già in edizioni.json: messaggio \"nessuna edizione: #{n:03d} già pubblicata\", niente da rifare")
    elif u["numero"] != n - 1:
        out.append(f"Numero: ultima edizione #{u['numero']:03d}, oggi #{n:03d}: usa #{n:03d} (giorni.py) e scrivi nel messaggio finale che mancano uscite intermedie")
    out.append(cut(f"Ultima: #{u['numero']:03d} del {u['data']} - {u['titolo']}"))
    nt = u.get("notizie", [])
    for i in range(0, len(nt), 2):
        out.append(cut("  notizie: " + " | ".join(nt[i:i + 2]), 170))
    if u.get("approfondimenti"):
        out.append(cut("  approfondimenti: " + " | ".join(f"{a.get('tema')}: {a.get('titolo')}" for a in u["approfondimenti"]), 220))
    elif u.get("temi_deep_dive"):
        out.append(cut("  deep dive: " + " | ".join(f"{k}: {v}" for k, v in u["temi_deep_dive"].items()), 260))
    if u.get("termometri"):
        out.append(cut("  termometri: " + " | ".join(str(t) for t in u["termometri"]), 170))
    if u.get("temi"):
        out.append("  temi: " + ", ".join(u["temi"]))
    out.append(cut("  sigle spiegate: " + (", ".join(u.get("glossario", [])) or "-") +
                   (" | parole: " + ", ".join(u["parole"]) if u.get("parole") else ""), 170))
    fp = os.path.join(repo, "redazione", "fatti", f"{u['data']}.json")
    if os.path.exists(fp):
        try:
            nf = len([f for f in json.load(open(fp, encoding="utf-8")) if isinstance(f, dict) and not f.get("scartata")])
        except Exception:
            nf = "?"
        out.append(f"Errata: confronta {nf} schede di redazione/fatti/{u['data']}.json con le notizie di oggi")
# artefatti stantii di prove precedenti (file di oggi già nel repository ma edizione non in indice): li sovrascrive pubblica.sh
if not any(v["numero"] == n for v in voci):
    st = [p for p in (f"redazione/fatti/{oggi.isoformat()}.json", f"pdf/{oggi.isoformat()}-gommberg-{n:03d}.pdf")
          if os.path.exists(os.path.join(repo, p))]
    if st:
        out.append("Stantii (di una prova, non in edizioni.json; pubblica.sh li sovrascrive, non leggerli): " + ", ".join(st))
out.append(f"Modello: {lav}/edizione_modello_v6.py -> copialo in {lav}/edizione_{oggi.isoformat()}.py")
print("\n".join(out[:20]))
EOF
