"""Anteprima unica del PDF per il controllo visivo (risparmio token).

Uso: python3 anteprima.py <pdf> <png_uscita> [dpi]
Rende le 6 pagine a bassa risoluzione e le affianca in una griglia 3x2,
cosi' il controllo visivo costa una sola immagine invece di sei.
"""
import subprocess, sys, tempfile, glob, os
from PIL import Image

pdf, out = sys.argv[1], sys.argv[2]
dpi = sys.argv[3] if len(sys.argv) > 3 else "45"
with tempfile.TemporaryDirectory() as d:
    subprocess.run(["pdftoppm", "-r", dpi, "-png", pdf, os.path.join(d, "p")], check=True)
    pagine = [Image.open(p).convert("RGB") for p in sorted(glob.glob(os.path.join(d, "p-*.png")))]
w, h = pagine[0].size
cols = 3
righe = (len(pagine) + cols - 1) // cols
tela = Image.new("RGB", (cols * w + (cols - 1) * 8, righe * h + (righe - 1) * 8), "#888888")
for i, p in enumerate(pagine):
    tela.paste(p, ((i % cols) * (w + 8), (i // cols) * (h + 8)))
tela.save(out, optimize=True)
print(f"{len(pagine)} pagine -> {out} ({tela.size[0]}x{tela.size[1]})")
