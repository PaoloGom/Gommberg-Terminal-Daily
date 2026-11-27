"""G-46 / tema delle note "indiscrezione senza il nome della testata": le frasi dei PDF #031-#035 che riportano una
notizia attribuita a un soggetto generico ("la stampa americana", "la stampa coreana", "media", "fonti", "indiscrezioni")
o col condizionale da indiscrezione. Per ognuna si guarda a mano se la testata è nominata nella frase. Sola lettura."""
import glob, os, re, subprocess
R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
GENERICO = re.compile(r"(?:la )?stampa (?:americana|coreana|giapponese|cinese|italiana|internazionale|finanziaria|locale)|"
                      r"\bmedia (?:iraniani|americani|locali|cinesi|coreani|statali)|\bindiscrezion\w+|\bfonti (?:anonime|vicine|citate)|"
                      r"\bresoconto anonimo|\bsecondo (?:alcune|diverse|più) fonti|\bnotizie secondo cui", re.I)
for pdf in sorted(glob.glob(os.path.join(R, "..", "pdf", "2026-11-2[3-7]-gommberg-03[1-5].pdf"))):
    t = subprocess.run(["pdftotext", pdf, "-"], capture_output=True).stdout.decode()
    pagine = t.split("\f")
    print(f"== {os.path.basename(pdf)}")
    for n, p in enumerate(pagine, 1):
        p = re.sub(r"(?m)^Fonti?:[^\n]*(?:\n[^\n]+)*", " ", p.split("\nNOTE\n")[0])
        flat = re.sub(r"-\n(?=[a-zà-ù])", "", p)
        flat = re.sub(r"\s+", " ", flat)
        for fr in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ú«])", flat):
            if GENERICO.search(fr):
                print(f"   pag. {n}: {fr.strip()[:230]}")
