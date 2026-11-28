"""G-64 - Carica C da un edizione.py archiviato, applica il desk, scrive moduli.json e i grafici SVG per il web. Zero token."""
import importlib.util, json, os, sys, shutil
REPO = sys.argv[1]; data = sys.argv[2]; out = sys.argv[3]
src = os.path.join(REPO, "redazione", "sorgenti", data)
import tempfile; lav = os.path.join(tempfile.mkdtemp(), data); shutil.copytree(src, lav)
os.environ["GTD_REPO"] = REPO
sys.argv = ["edizione.py", lav]
spec = importlib.util.spec_from_file_location("ed", os.path.join(lav, "edizione.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
C = m.C
sys.path.insert(0, os.path.join(REPO, "redazione"))
import desk
n = desk.applica(C, lav)
import gommberg_engine as G
os.makedirs(os.path.join(out, "grafici"), exist_ok=True)
moduli = []
for mo in C["moduli"]:
    gg = []
    for k in ("grafico", "grafico2"):
        g = mo.get(k)
        if not isinstance(g, dict):
            continue
        a = dict(g); tipo = a.pop("tipo"); f = a.pop("file")
        for x in ("soggetto", "sottotitolo", "ruolo"):
            a.pop(x, None)
        for suff, lg, al in (("", 5.6, 2.45), ("-m", 3.5, 2.4)):
            b = dict(a); b["largo"] = lg
            if tipo == "linee": b["alto"] = al
            elif suff == "": b["alto"] = 0.26 * len(a["dati"]) + 0.5
            p = os.path.join(out, "grafici", f"{data}-{f[:-4]}{suff}.png")
            {"linee": G.linee, "barre": G.barre}[tipo](p, **b)
            os.remove(p)   # resta solo l'SVG
        gg.append({"titolo": g.get("titolo"), "sottotitolo": g.get("sottotitolo"), "svg": f"grafici/{data}-{f[:-4]}.svg"})
    moduli.append({k: mo.get(k) for k in ("chiave", "tema", "titolo", "misura", "numero", "perche", "quindi", "testo", "guardare", "fonte", "breve")} | {"grafici": gg})
json.dump({"data": data, "top": C["top"], "quadro": C["quadro"], "desk": n, "moduli": moduli}, open(os.path.join(out, f"moduli-{data}.json"), "w"), ensure_ascii=False, indent=1)
print("ok", n, [x["chiave"] for x in moduli])
