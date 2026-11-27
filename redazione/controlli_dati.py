"""Controllo dei dati di mercato prima della stesura: dati vecchi, valori fermi, intraday spacciati per chiusure.
Uso: python3 controlli_dati.py <dati.json>
dati.json: {"oggi": "AAAA-MM-GG", "ora_roma": "HH:MM",
  "serie": {"S&P 500": {"mercato": "USA|EU|UK|JP|HK|KR|CN|FX|COMM|UST",
                        "ultimi": [["AAAA-MM-GG", valore, volume_o_null], ...],   # dal più recente, almeno 3
                        "tipo": "chiusura|intraday", "seconda_fonte": valore_o_null}}}
Serie con la sola variazione (seduta asiatica in corso, livello non disponibile): {"mercato": "KR", "tipo": "intraday",
  "var": -8.68, "ora": "08:11", "fonte": "EODHD + Teleborsa", "ultimi": [<ultime chiusure EODHD, con la loro data>]}: il
  livello lo ricava numeri.py dall'ultima seduta vera di quella borsa (APP_DATI §2b e §4). "macro" (facoltativo, per le anomalie):
  [{"nome": "PPI USA a/a", "dato": 6.3, "atteso": 5.3, "caldo_se": "su", "data": "AAAA-MM-GG"}] ("giu" per sussidi
  e disoccupazione; "data" = giorno di uscita, serve a contesto.py per la reazione dei tassi).
Dato non verificabile neanche dal web: {"mercato": "KR", "nd": "<motivo, es. nessuna fonte con orario>", "ultimi": []}
  (ammesso: la riga non entra nella tabella di pag. 5; nel PDF mai "n.d."). Indici obbligatori (controlli_contenuti.py): S&P 500, Nasdaq, Euro Stoxx 50, Nikkei 225, Kospi, Hang Seng.
Esce con codice 1 se c'è un problema bloccante."""
import datetime as dt, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numeri as N  # noqa: E402
import giorni as G  # noqa: E402

from zoneinfo import ZoneInfo

# Chiusura locale di ogni mercato (con un margine per l'asta finale), convertita in ora di Roma per la data di oggi:
# prima di quell'ora il dato di oggi non è una chiusura. Il fuso cambia in date diverse (USA, Europa, Asia senza ora legale).
LOCALE = {"USA": ("America/New_York", "16:15"), "UST": ("America/New_York", "17:00"), "EU": ("Europe/Rome", "17:45"),
          "UK": ("Europe/London", "16:45"), "JP": ("Asia/Tokyo", "15:45"), "HK": ("Asia/Hong_Kong", "16:15"),
          "KR": ("Asia/Seoul", "15:45"), "CN": ("Asia/Shanghai", "15:15"), "FX": None, "COMM": None}
d = json.load(open(sys.argv[1], encoding="utf-8"))
oggi = dt.date.fromisoformat(d["oggi"]); ora = d["ora_roma"]


def chiusura_roma(mercato):
    v = LOCALE.get(mercato)
    if not v:
        return None
    h, m = map(int, v[1].split(":"))
    loc = dt.datetime(oggi.year, oggi.month, oggi.day, h, m, tzinfo=ZoneInfo(v[0]))
    return loc.astimezone(ZoneInfo("Europe/Rome")).strftime("%H:%M")


CHIUSURA = {k: chiusura_roma(k) for k in LOCALE}
problemi, avvisi = [], []
for nome, s in d["serie"].items():
    u = s["ultimi"]
    if not u and s.get("nd"):
        avvisi.append(f"{nome}: non verificato ({s['nd']}): la riga non entra nella tabella di pag. 5; nel PDF mai \"n.d.\""); continue
    futuri = [str(r[0])[:10] for r in u if str(r[0])[:10] > d["oggi"]]
    if futuri:
        problemi.append(f"{nome}: in \"ultimi\" una data dopo oggi ({futuri[0]}): una chiusura non può venire dal futuro, correggi la data")
    chiusa = [str(r[0])[:10] for r in u if str(r[0])[:10] <= d["oggi"] and dt.date.fromisoformat(str(r[0])[:10]).weekday() < 5
              and G.borsa_il(s.get("mercato"), r[0]) == "festa"]
    if chiusa:
        problemi.append(f"{nome}: riga del {chiusa[0]}, ma quel giorno la borsa era chiusa (giorni.py, FESTE_BORSE): non è una "
                        "seduta (EODHD scrive righe anche a indice fermo), toglila")
    if s.get("var") is not None and not (u and str(u[0][0])[:10] >= d["oggi"]):    # stamattina solo la variazione
        base = N.ultima_seduta(nome, s, d["oggi"])
        if not (s.get("fonte") and s.get("ora")):
            problemi.append(f"{nome}: serie con sola variazione senza 'fonte' e 'ora'")
        elif base and not N.ricavato(nome, s, d["oggi"]):
            problemi.append(f"{nome}: serie con sola variazione: serve \"tipo\": \"intraday\" e \"var\" numerica")
        elif not base:
            problemi.append(f"{nome}: solo la variazione di stamattina e {N.manca_base(nome, s, d['oggi'])}. Finché manca, la riga "
                            "resta fuori dalla tabella")
        elif base[0] < N._ieri(d["oggi"]):
            feste = [x for x in N._feriali_tra(base[0], d["oggi"])]
            avvisi.append(f"{nome}: livello ricavato dall'ultima seduta, del {base[0]}: borsa chiusa per festa il "
                          f"{', '.join(feste)} (giorni.py, FESTE_BORSE): dillo nel testo (APP_FESTIVI §2)")
        prec = [r for r in u if str(r[0])[:10] < d["oggi"]]
        if len(prec) >= 2 and prec[0][1] == prec[1][1] and (len(prec[0]) < 3 or prec[0][2] in (None, 0)):
            problemi.append(f"{nome}: chiusura del {prec[0][0]} identica a quella del {prec[1][0]}, senza volume: probabilmente una "
                            "riga a indice fermo, non una seduta (APP_DATI §2b): toglila se quel giorno la borsa era chiusa")
        continue
    if len(u) == 1:
        u = N.completa(nome, s)        # la chiusura precedente la conosce l'archivio (chiusure.csv, scommessa/dati)
    if len(u) < 2:
        problemi.append(f"{nome}: meno di due osservazioni (e l'archivio non ha la chiusura precedente: aggiungila)"); continue
    (d0, v0, vol0), (d1, v1, _) = u[0], u[1]
    d0 = dt.date.fromisoformat(d0)
    # giorni di uscita passati dall'ultimo dato: un giorno senza edizione (borse chiuse insieme) non invecchia il dato
    giorni_lav = sum(1 for k in range(1, (oggi - d0).days + 1) if G.uscita(d0 + dt.timedelta(days=k)))
    if giorni_lav > 2:
        problemi.append(f"{nome}: ultimo dato del {d0}, vecchio di {giorni_lav} giorni di uscita: cerca la chiusura più recente; se il "
                        "mercato è davvero chiuso da più giorni, APP_FESTIVI §2")
    elif giorni_lav == 2:
        avvisi.append(f"{nome}: ultimo dato del {d0} (mercato chiuso ieri? verificalo e dillo nel testo: APP_FESTIVI §2)")
    ch = CHIUSURA.get(s.get("mercato"))
    if d0 == oggi and ch and ora < ch and s.get("tipo") == "chiusura":
        problemi.append(f"{nome}: dato di oggi segnato come chiusura ma il mercato chiude alle {ch}: è intraday")
    if d0 < oggi and ch and ora >= ch and giorni_lav < 2:      # a quest'ora la seduta di oggi è finita (Asia): dov'è?
        avvisi.append(f"{nome}: ultimo dato del {d0}, ma oggi questo mercato ha già chiuso (alle {ch}): se oggi era chiuso per "
                      "festività dillo nel testo (APP_FESTIVI §2), altrimenti prendi la chiusura di oggi")
    if v0 == v1 and (vol0 in (None, 0) or (isinstance(vol0, (int, float)) and vol0 < 1000)):
        problemi.append(f"{nome}: valore identico alla seduta precedente con volume nullo: dato probabilmente fermo")
    if d0 == oggi and isinstance(vol0, (int, float)) and 0 < vol0 < 1000 and s.get("mercato") not in ("FX", "COMM"):
        avvisi.append(f"{nome}: volume quasi nullo ({vol0}): verificare che il dato sia aggiornato")
    vol1 = u[1][2] if len(u[1]) > 2 else None
    if (s.get("mercato") in ("USA", "EU", "UK", "JP", "HK", "KR", "CN") and isinstance(vol0, (int, float))
            and isinstance(vol1, (int, float)) and vol0 > 0 and vol1 > 0 and vol0 < 0.2 * vol1 and not s.get("seconda_fonte")):
        problemi.append(f"{nome}: volume della seduta del {d0} pari al {100 * vol0 / vol1:.0f}% della precedente: chiusura "
                        "probabilmente incompleta (caso Euro Stoxx 50 del 16/10/2026); conferma il livello con una seconda "
                        "fonte ('seconda_fonte') o usa la chiusura precedente dichiarandolo")
    if v1 and abs(v0 / v1 - 1) > 0.08 and s.get("mercato") not in ("COMM",):
        avvisi.append(f"{nome}: variazione giornaliera {100 * (v0 / v1 - 1):+.1f}%: verificare con una seconda fonte")
    sf = s.get("seconda_fonte")
    if sf:
        scarto = abs(v0 / sf - 1)
        if scarto > 0.005:
            problemi.append(f"{nome}: scarto {100 * scarto:.2f}% con la seconda fonte ({v0} contro {sf})")
# Serie che arrivano ogni mattina da una fonte dati verificata (APP_DATI §2b e §6): il connettore è sempre tra le fonti, salvo
# "<api>_nd" (connettore che non risponde), e le sedute già in archivio devono coincidere con quelle verificate.
# Euro Stoxx 50: FMP ^STOXX50E dà chiusure sbagliate quasi ogni giorno (confronto del 10/11/2026 su 20 sedute: scarti fino
# allo 0,8%, anche di segno, mai corretti dopo). EODHD STOXX50E.INDX coincide al centesimo con stoxx.com e dpa-AFX
# (verifica del 21/11/2026, 40 sedute): fonti ammesse e seconda fonte concorde entro lo 0,05%.
# Kospi e Hang Seng: EODHD KS11.INDX e HSI.INDX coincidono al centesimo con lo storico di Investing.com (verifica del
# 27/11/2026, 34 e 33 sedute; l'unica seduta discorde era sbagliata su Investing): EODHD dà le chiusure, la seduta di
# stamattina viene dalle fonti di APP_DATI §6, quindi nessun elenco di fonti ammesse e nessuna seconda fonte obbligatoria.
# Per aggiungere una serie basta una riga qui: fonti ammesse (None = qualunque), fonte da chiamare ogni mattina, seconda
# fonte obbligatoria.
FONTI_AMMESSE = {"Euro Stoxx 50": (("eodhd", "stoxx.com", "dpa-afx", "investing"), "eodhd", True),
                 "Kospi": (None, "eodhd", False), "Hang Seng": (None, "eodhd", False)}
for nome, (ammesse, api, due_fonti) in FONTI_AMMESSE.items():
    s = d["serie"].get(nome)
    if not s or s.get("nd"):
        continue
    fonte = str(s.get("fonte") or "").lower().replace(api + "_nd", "")      # "eodhd_nd" scritto in fonte non è EODHD
    if ammesse and (not any(a in fonte for a in ammesse) or "fmp" in fonte or "modeling" in fonte):
        problemi.append(f"{nome}: \"fonte\" deve nominare le fonti usate, tra {', '.join(ammesse)} (APP_DATI §6): mai FMP né "
                        "le quotazioni nei riquadri delle pagine")
    if (api not in fonte or not s.get("ultimi")) and not s.get(api + "_nd"):
        problemi.append(f"{nome}: mancano le chiusure di {api.upper()}: una chiamata (APP_DATI §2b), le ultime chiusure in "
                        f"\"ultimi\" con la loro data e {api.upper()} in \"fonte\"; se il connettore non risponde \"{api}_nd\": "
                        "\"<motivo>\" e il ripiego di APP_DATI §6")
    if not s.get("ultimi"):
        continue
    altre = fonte.replace(api, "").replace("+", " ").replace(",", " ").strip()
    # solo una riga di oggi dichiarata come presa da EODHD e da nient'altro; senza "fonte" vale il controllo qui sopra
    if not due_fonti and api in fonte and str(s["ultimi"][0][0])[:10] == d["oggi"] and not altre:
        problemi.append(f"{nome}: riga di oggi con la sola fonte {api.upper()}: da {api.upper()} valgono solo le chiusure prima di oggi "
                        "(APP_DATI §2b); la seduta di stamattina viene da APP_DATI §6, con la sua fonte in \"fonte\"")
    if due_fonti:
        sf = s.get("seconda_fonte")
        if not sf and not s.get("fonte_singola"):
            problemi.append(f"{nome}: manca \"seconda_fonte\" (il valore di una seconda fonte indipendente) o \"fonte_singola\": true")
        elif sf and abs(s["ultimi"][0][1] / sf - 1) > 0.0005:
            problemi.append(f"{nome}: le due fonti non concordano entro lo 0,05% ({s['ultimi'][0][1]} contro {sf}): vale il gestore dell'indice")
    # le sedute precedenti devono essere quelle già verificate in archivio: le variazioni poggiano su quelle
    arch = N.storia(nome)
    for g, v, *_ in s["ultimi"][1:] if due_fonti else [r for r in s["ultimi"] if str(r[0])[:10] < d["oggi"]]:
        g = str(g)[:10]
        if g in arch and abs(v / arch[g] - 1) > 0.0005:
            problemi.append(f"{nome}: {g} = {v}, ma la chiusura verificata in archivio è {arch[g]}: "
                            + ("usa quella" if due_fonti else "verifica sul sito della borsa quale delle due è giusta"))
import re  # noqa: E402
for obb, rx in (("S&P 500", r"s&p ?500"), ("Nasdaq", r"nasdaq"), ("Euro Stoxx 50", r"stoxx ?50"), ("Nikkei 225", r"nikkei"),
                ("Kospi", r"kospi|seul|seoul"), ("Hang Seng", r"hang ?seng")):
    if not any(re.search(rx, k, re.I) for k in d["serie"]):
        problemi.append(f"{obb}: indice principale assente (serve l'ultima seduta conclusa; un movimento oltre il 3% va citato)")
# Le righe fisse delle tabelle di pag. 5 (numeri.py le calcola da qui): ogni serie c'è, con il dato o con il motivo per cui manca
for _et, _nome, *_ in [r for _, rr in N.CRUSCOTTO + N.CROSS for r in rr]:
    _nomi = _nome if isinstance(_nome, tuple) else (_nome,)
    if not any(n in d["serie"] for n in _nomi):
        problemi.append(f"{_nomi[0]}: manca la serie (riga della tabella di pag. 5): ultima chiusura dal web (APP_DATI §3); se "
                        "non esce: {\"mercato\": \"..\", \"nd\": \"<motivo>\", \"ultimi\": []} e la riga non entra in tabella")
print(f"Serie controllate: {len(d['serie'])}")
if oggi.weekday() == 0:          # una volta a settimana, per chi tiene la macchina: non blocca e non si corregge al mattino
    for riga in G.calendario_in_scadenza(oggi):
        print("NOTA: " + riga + " (non tocca alla redazione del mattino)")
for a in avvisi:
    print("AVVISO: " + a)
if problemi:
    print("PROBLEMI:\n- " + "\n- ".join(problemi)); sys.exit(1)
print("OK: dati coerenti")
