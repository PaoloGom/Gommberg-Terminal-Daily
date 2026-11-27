"""G-46, intervento 3: schede che ufficiale_di_fatto riconosce come dato ufficiale nell'archivio dei fatti dal 14/10, con
autori.py di prima (cartella data come primo argomento) e con quello di oggi; stampa solo le differenze, da leggere a mano.
Uso: python3 g06_archivio.py <cartella redazione di prima>. Le righe di "ieri" non entrano (servono i sorgenti)."""
import glob, importlib.util, json, os, sys
R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def carica(cartella, nome):
    sp = importlib.util.spec_from_file_location(nome, os.path.join(cartella, "autori.py"))
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    return m


prima, oggi = carica(os.path.abspath(sys.argv[1]), "autori_prima"), carica(R, "autori_oggi")
n_p = n_o = 0
for f in sorted(glob.glob(os.path.join(R, "fatti", "2026-*.json"))):
    g = os.path.basename(f)[:10]
    if g < "2026-10-14":
        continue
    F = [s for s in json.load(open(f, encoding="utf-8")) if isinstance(s, dict)]
    for s in F:
        a, b = prima.ufficiale_di_fatto(s, F, g, []), oggi.ufficiale_di_fatto(s, F, g, [])
        n_p += bool(a); n_o += bool(b)
        if bool(a) != bool(b):
            print(f"{g} {s.get('id')} [{s.get('sezione')}] prima={'sì' if a else 'no'} oggi={'sì' if b else 'no'} | {str(s.get('testo'))[:150]}")
print(f"Riconosciute: prima {n_p}, oggi {n_o}")
