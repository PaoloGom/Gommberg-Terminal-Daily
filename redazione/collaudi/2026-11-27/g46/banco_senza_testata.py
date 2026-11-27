"""G-46, intervento 1: banco di attacco di controlli_testo.senza_testata. Ogni caso è un pezzo da solo; GIUSTE non devono
fermarsi, SBAGLIATE sì. Stampa falsi allarmi e mancati. Uso: python3 banco_senza_testata.py [<cartella redazione>]"""
import os, sys
R = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, R)
import controlli_testo as T

RIGHE = ["Fonti: Reuters, Bloomberg, Yonhap, Handelsblatt, Korea Times, Korea Herald, Financial Times, Nikkei, Wall Street Journal."]
GIUSTE = [
    "Secondo le indiscrezioni del Financial Times il gruppo valuta un'offerta.",
    "Un'indiscrezione di Bloomberg dà per vicino l'accordo.",
    "Le cifre, pubblicate dal WSJ, indicano indiscrezioni su un taglio dei costi.",
    "Diverse testate, tra cui il Korea Herald, riportano indiscrezioni su un fondo più grande.",
    "La stampa coreana, che cita Yonhap, parla di un fondo più grande.",
    "Circolano indiscrezioni su un'offerta. Lo scrive Bloomberg.",
    "I media riferiscono di un accordo vicino. Lo scrive Reuters, citando due funzionari.",
    "Il gruppo dei media americani Paramount perde il 5%.",
    "I media di Stato cinesi sono stati riorganizzati dal governo.",
    "L'azienda ha presentato il prodotto alla stampa specializzata.",
    "La stampa domestica costa sempre meno con le nuove stampanti.",
    "Secondo il Nikkei, fonti vicine al governo parlano di un rinvio.",
    "Secondo lo Handelsblatt i media tedeschi danno per certo il piano.",
    "Secondo Reuters i vertici ne avrebbero parlato; un resoconto anonimo dà la decisione a dicembre.",
    "Media iraniani riferiscono di mine, ma Bloomberg scrive di non avere conferme.",
    "Secondo tre fonti citate da Reuters l'amministrazione è pronta.",
    "La media mobile a 200 giorni passa sotto il prezzo.",
    "La media nasconde due paesi che vanno in direzioni opposte.",
    "Il Wall Street Journal riporta indiscrezioni su un'offerta.",
    "I giornali di carta perdono lettori da anni.",
    "Il governo, scrive il Korea Times, prepara il fondo, e per la stampa locale conta l'ampliamento.",
    "Le voci di mercato raccolte da Bloomberg indicano un'offerta.",
    "Il bersaglio resta Nvidia, dopo l'indagine riportata dalla stampa americana. A rivelarla per primo è stato il Wall Street Journal.",
    "Il ministero ha convocato i media stranieri per spiegare le sanzioni.",
    "Secondo indiscrezioni di stampa riportate da Bloomberg, il gruppo tratta.",
    "I media americani parlano di un accordo. Lo scrive il Wall Street Journal, citando fonti vicine.",
    "Fonti vicine al dossier danno per certa l'offerta, secondo Reuters.",
    "La stampa tedesca anticipa il piano. L'ha rivelato lo Handelsblatt per primo.",
    "Le banche giapponesi salgono, trascinate dal Nikkei e da un dollaro forte.",
    "I tassi restano fermi, come spiegato dalla BCE nella riunione.",
    "Il governo ha invitato la stampa estera alla conferenza.",
    "I giornali italiani hanno perso copie anche nel 2026.",
]
SBAGLIATE = [
    "La SEC indaga sui conti di Nvidia, riferisce la stampa americana.",
    "Il bersaglio resta Nvidia, dopo l'indagine riportata dalla stampa americana.",
    "Dopo le dimissioni sono arrivate notizie secondo cui era nel mirino.",
    "La stampa coreana lega il rialzo al fondo.",
    "I media americani riferiscono di un accordo vicino.",
    "Secondo i media il gruppo valuta la vendita.",
    "L'offerta è stata anticipata dai media.",
    "Una fonte anonima dà per certo l'accordo.",
    "Fonti vicine al dossier parlano di un rinvio.",
    "Voci di mercato indicano un'offerta imminente.",
    "Secondo i giornali il governo prepara la manovra.",
    "La stampa di settore scrive di un taglio della produzione.",
    "Le indiscrezioni su nuovi dazi pesano sull'Asia.",
    "Tre fonti anonime parlano di 16 economie.",
    "Per la stampa coreana pesano gli acquisti dopo il crollo.",
    "I giornali scrivono di un rimpasto imminente.",
    "Secondo la stampa giapponese la BoJ alzerà i tassi.",
    "Un resoconto anonimo dà la decisione a dicembre.",
    "Stando alla stampa tedesca il governo prepara aiuti.",
    "Secondo quanto riportato dai media locali, l'impianto è fermo.",
    "I media scrivono che Nvidia valuta un'offerta.",
    "Secondo alcuni giornali, il governo prepara un decreto.",
    "Secondo indiscrezioni di stampa il gruppo valuta un'offerta. Il titolo sale del 3% secondo Reuters.",
    "Secondo la stampa americana la SEC indaga. Secondo Reuters il Brent sale.",
    "Le banche cedono, trascinate dal Nikkei, mentre la stampa giapponese parla di una stretta.",
    "Secondo i media la BCE alzerà i tassi, come spiegato dalla BCE stessa a ottobre.",
    "Fonti vicine al governo parlano di un rinvio. Intanto Bloomberg scrive che il petrolio sale.",
    "Voci di mercato indicano un'offerta. Il gruppo, secondo il bilancio, ha liquidità.",
    "Secondo diversi media il piano è pronto.",
    "Un'indiscrezione dà per vicino l'accordo.",
    "Molti giornali scrivono di un rimpasto.",
]
nomi = T.NOMI_BASE + [n for n in T.nomi_da_righe(RIGHE) if n not in T.NOMI_BASE]
ferma = lambda t: bool(T.senza_testata({"moduli.0.testo.0": t}, nomi, RIGHE))   # noqa: E731
falsi = [t for t in GIUSTE if ferma(t)]
mancati = [t for t in SBAGLIATE if not ferma(t)]
print(f"giuste {len(GIUSTE)}, falsi allarmi {len(falsi)}; sbagliate {len(SBAGLIATE)}, mancati {len(mancati)}")
for t in falsi:
    print("  FALSO  ", t)
for t in mancati:
    print("  MANCATO", t)
