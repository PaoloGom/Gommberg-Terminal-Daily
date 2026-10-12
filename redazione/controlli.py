"""Controlli automatici sul PDF e sull'indice prima della pubblicazione.
Uso: python3 controlli.py "<file pdf>" <percorso edizioni.json> <numero edizione>
Esce con codice 1 e l'elenco dei problemi se qualcosa non va."""
import json, subprocess, sys, re

pdf, indice, numero = sys.argv[1], sys.argv[2], int(sys.argv[3])
problemi = []
info = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
pagine = int(re.search(r"Pages:\s+(\d+)", info).group(1))
if pagine != 6:
    problemi.append(f"Il PDF ha {pagine} pagine invece di 6")
testo = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True).stdout.decode("utf-8")
for ch, nome in (("–", "trattino medio"), ("—", "trattino lungo")):
    if ch in testo:
        problemi.append(f"{testo.count(ch)} x {nome}: usare solo '-'")
for pat in ("TODO", "XXX", "lorem", "None", "nan%", "inf%"):
    if pat in testo:
        problemi.append(f"Testo segnaposto o errore trovato: {pat!r}")
nd = testo.count("n.d.")
if nd > 8:
    problemi.append(f"Troppi dati mancanti: {nd} 'n.d.'")
try:
    voci = json.load(open(indice, encoding="utf-8"))
    nums = [v["numero"] for v in voci]
    if numero not in nums:
        problemi.append(f"edizioni.json non contiene l'edizione {numero}")
    if len(nums) != len(set(nums)):
        problemi.append("edizioni.json ha numeri di edizione duplicati")
    for v in voci:
        for k in ("numero", "data", "titolo", "sommario", "file", "nome", "notizie"):
            if k not in v:
                problemi.append(f"Edizione {v.get('numero')}: manca il campo {k}")
except Exception as e:
    problemi.append(f"edizioni.json non valido: {e}")
print(f"Pagine: {pagine} | n.d.: {nd}")
if problemi:
    print("PROBLEMI:\n- " + "\n- ".join(problemi)); sys.exit(1)
print("OK: nessun problema")
