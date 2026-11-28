#!/usr/bin/env python3
"""G-12, studio dei minuti: la proiezione dei minuti fatturabili al mese da privato (minuti Linux standard equivalenti;
un minuto su ubuntu-slim vale un terzo), flusso per flusso, per un mese normale e uno pesante, passo per passo del piano.
Ogni numero di partenza è dichiarato qui sotto con la sua origine: M = misurato sui giri veri (misura_tabelle.py),
S = stimato, V = da verificare con un giro di prova. Nessuna rete, nessun file scritto.

Uso:  python3 proiezione.py"""
QUOTA = 2000
S3 = 1 / 3                      # un minuto ubuntu-slim in minuti standard (0,002 contro 0,006 dollari: prezzi di GitHub)
E = 22                          # edizioni al mese (giorni feriali)
G = 30                          # giorni al mese

MESI = {
    # rilasci al mese; push sui rami di lavoro che accendono dem.yml; push su prova e anteprima-*; lanci a mano (slim)
    "normale": {"rilasci": 12, "dem_rami": 15, "prove": 6, "a_mano": 9},     # S: 3 rilasci a settimana, una prova a settimana
    "pesante": {"rilasci": 40, "dem_rami": 80, "prove": 16, "a_mano": 30},   # M: 8 rilasci in 16 ore il 27-28/11 x 4 weekend, + 2 a settimana; 15 push/giorno su dem.yml il 27/11
}
TENTATIVI = 1.25                # S: collaudi di GitHub per rilascio (M: 4% di rossi; più i rilanci quando main cambia)
SITO_PER_RILASCIO = 0.8         # M: 14 rilasci su 17 hanno ripubblicato il sito (gli altri toccavano solo la redazione)


def mese(nome, p):
    m = MESI[nome]
    r = {}
    # a) le edizioni
    r["a sito.yml all'edizione"] = E * p["sito"]
    r["a newsletter.yml"] = E * S3
    r["a mattino.yml dopo la pubblicazione"] = E * S3
    # c) a orario
    r["c segnalazioni.yml"] = p["segnalazioni"] * S3
    r["c mattino.yml 10:15 (controllo e GOMM)"] = E * 2 * S3
    r["c sito.yml ripubblicato dal GOMM"] = E * p["sito"] * p["gomm"]
    r["c dem.yml della sera"] = G * S3
    r["c sveglie di riserva di GitHub (passo 1 di G-58)"] = p["riserva"]
    # b) lo sviluppo
    r["b collaudo.yml dal ramo cancello"] = m["rilasci"] * TENTATIVI * p["cancello"]
    r["b sito.yml dopo un rilascio"] = m["rilasci"] * SITO_PER_RILASCIO * p["sito"]
    r["b dem.yml dai rami di lavoro"] = m["dem_rami"] * S3 * p["dem_rami"]
    r["b sito.yml su prova e anteprima-*"] = m["prove"] * p["sito"]
    r["b lanci a mano (newsletter di prova, controlli)"] = m["a_mano"] * S3
    return r


OGGI = {
    "sito": 1.0,          # M: job pubblica, mediana 28 s, massimo 57 s -> 1 minuto standard
    "segnalazioni": 180,  # M+S: 6 giri al giorno di 10 s su slim, quando li dà l'orologio di Cloudflare (oggi GitHub ne fa partire 2,4 al giorno)
    "gomm": 1.0,          # M: un sito.yml in più al giorno feriale
    "riserva": 63.0,      # S (40-99): M sveglie di mattino e dem partite tutte, segnalazioni 2,4 al giorno; ogni job 1 minuto slim anche se la guardia lo ferma
    "cancello": 8.0,      # M 6 (156 s + 154 s il 28/11, 4 CPU); V: da privato 2 CPU, e il job kit è a 24 s dal quarto minuto -> 8 prudente
    "dem_rami": 1.0,
}
PASSI = [
    ("Oggi, con le tre leve", {}),
    ("1. dem.yml solo da main; tempi massimi corti; ogni flusso dichiara i minuti", {"dem_rami": 0.0}),
    ("2. G-58 passo 2: via le sveglie di riserva", {"riserva": 0.0}),
    ("3. segnalazioni solo quando c'è un commento segnalato (+1 giro al giorno di battito)", {"segnalazioni": 30 + 6}),
    ("4. sito.yml (pubblica) su ubuntu-slim", {"sito": 2 * S3}),          # V: 2 minuti slim per prudenza
    ("5. collaudo.yml in un job solo, con cache", {"cancello": 5.0}),     # S: 310 s - 85 s di installazioni e doppio avvio = 4 minuti; 5 prudente
    ("6. (facoltativo) il sito lo pubblica Cloudflare (Workers Builds)", {"sito": 0.0}),
]


def f(x):
    return f"{x:.0f}"


def main():
    p = dict(OGGI)
    print("| passo | mese normale | % quota | mese pesante | % quota |")
    print("|---|---:|---:|---:|---:|")
    stati = []
    for nome, cambia in PASSI:
        p.update(cambia)
        n, pe = sum(mese("normale", p).values()), sum(mese("pesante", p).values())
        stati.append((nome, dict(p)))
        print(f"| {nome} | {f(n)} | {100 * n / QUOTA:.0f}% | {f(pe)} | {100 * pe / QUOTA:.0f}% |")
    for quale in (0, 5):
        nome, pp = stati[quale]
        print(f"\nFlusso per flusso - {nome}")
        print("| classe e flusso | normale | pesante |")
        print("|---|---:|---:|")
        a, b = mese("normale", pp), mese("pesante", pp)
        for k in a:
            print(f"| {k} | {a[k]:.0f} | {b[k]:.0f} |")
        for c in "abc":
            print(f"| **totale {c}** | **{sum(v for k, v in a.items() if k[0] == c):.0f}** | **{sum(v for k, v in b.items() if k[0] == c):.0f}** |")
        print(f"| **totale** | **{sum(a.values()):.0f}** | **{sum(b.values()):.0f}** |")

    # tra un anno e tra tre: le edizioni non crescono, cresce ciò che dipende da quante edizioni ci sono in archivio
    # M (in locale): pagine.py rifà tutto a ogni giro, 0,076 s a edizione; il collaudo lo lancia circa 5 volte
    #   -> +0,38 s a edizione per collaudo, +97 s l'anno (255 edizioni) sul job kit
    # S: il job pubblica (checkout, copia dei file, elenco per Cloudflare) cresce con i file del sito: oggi 446 file e 28 s;
    #   +20 file a edizione -> circa +20 s l'anno (estrapolazione debole: 8 giorni di dati)
    print("\n| orizzonte | file del sito | collaudo dal cancello (min) | sito.yml pubblica (min std) | senza piano: normale / pesante | con il piano (passi 1-5) e pagine.py che rifà solo il nuovo: normale / pesante |")
    print("|---|---:|---:|---:|---:|---:|")
    for anni, etichetta in ((0, "oggi"), (1, "tra un anno"), (3, "tra tre anni")):
        file = 446 + 20 * 255 * anni
        kit = 156 + 97 * anni
        cancello = -(-kit // 60) + 3 + (2 if anni == 0 else 2)        # kit arrotondato + browser 3 + 2 di prudenza per le macchine a 2 CPU
        sito = -(-(28 + 20 * anni) // 60)
        senza = dict(OGGI, cancello=float(cancello), sito=float(sito))
        con = dict(stati[5][1], sito=sito * 2 * S3 if anni else 2 * S3)
        con_n, con_p = sum(mese("normale", con).values()), sum(mese("pesante", con).values())
        print(f"| {etichetta} | {file} | {cancello} | {sito} | {f(sum(mese('normale', senza).values()))} / {f(sum(mese('pesante', senza).values()))} | {f(con_n)} / {f(con_p)} |")


if __name__ == "__main__":
    main()
