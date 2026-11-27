"""G-46 / tema delle note "Sopra: ... Sotto: ..." applicato a una chiusura di borsa: le righe dell'agenda di pag. 5 delle
#031-#035 su una chiusura, una seduta corta o una riapertura, con l'ultima colonna (dai sorgenti archiviati, campo agenda).
Sola lettura. Uso: python3 agenda_chiusure.py"""
import ast, glob, os, re
R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SEDUTA = re.compile(r"chiu[sd]|seduta|riapre|orari|Ringraziamento|festa|fest\w+", re.I)
tot = {"righe": 0, "sedute": 0, "schema": 0}
for g in ["2026-11-23", "2026-11-24", "2026-11-25", "2026-11-26", "2026-11-27"]:
    src = open(os.path.join(R, "sorgenti", g, "edizione.py"), encoding="utf-8").read()
    m = re.search(r'"agenda":\s*(\[.*?\n\s*\]),', src, re.S)
    righe = ast.literal_eval(m.group(1)) if m else []
    print(f"== {g}: {len(righe)} righe in arrivo")
    for r in righe:
        tot["righe"] += 1
        quando, evento, attese, perche, come = [re.sub(r"<[^>]+>", "", str(x)) for x in r[:5]]
        if SEDUTA.search(evento):
            tot["sedute"] += 1
            schema = bool(re.search(r"\bSopra\b.*\bSotto\b|Sopra e sotto", come))
            tot["schema"] += schema
            print(f"   {quando:<16} {evento[:45]:<45} attese: {attese[:40]!r} | {'SCHEMA' if schema else 'altro '} | {come[:150]}")
print("Totale:", tot)
