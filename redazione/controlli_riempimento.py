"""Riempimento delle pagine e dei moduli, letto dal rendering (riempimento.json, scritto da render_v6).
Uso: python3 controlli_riempimento.py <pdf> [riempimento.json]. Esce con 1 se una pagina ha più di 15 mm vuoti o un
modulo è sotto il 90%: si riempie con fatti e perché verificati (APP_ERRORI.md §2), nei 3 giri come ogni altro controllo."""
import json, os, sys

pdf = os.path.abspath(sys.argv[1])
rep = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.environ.get("GTD_LAVORO", "/home/claude/lavoro"), "riempimento.json")
if not os.path.exists(rep):
    print(f"ERRORE: manca {rep}: rigenera il PDF con il modello (render_v6 lo scrive)"); sys.exit(1)
r = json.load(open(rep, encoding="utf-8"))
if os.path.basename(r.get("pdf", "")) != os.path.basename(pdf):
    print(f"ERRORE: {rep} riguarda un altro PDF ({r.get('pdf')}): rigenera il PDF"); sys.exit(1)
liberi = ", ".join(f"p{p}={v}" for p, v in r["mm_liberi"].items())
if r["scarsi"]:
    print(f"Riempimento: {len(r['scarsi'])} spazi da riempire | mm liberi: {liberi}")
    for x in r["scarsi"]:
        print("ERRORE: " + x + ("" if "troppo pieno" in x else " - aggiungi una prova della scaletta o un fatto della "
              "memoria, con la sua scheda (testo del modulo, riga di tabella, punto, notizia); mai frasi senza scheda"))
    sys.exit(1)
print(f"Riempimento: pagine e moduli pieni | mm liberi: {liberi}")
