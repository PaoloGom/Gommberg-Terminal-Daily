#!/usr/bin/env python3
"""L'edizione via email. Compone l'email dalla scheda dell'ultima edizione (e/NNN.json) e la passa a Kit, che la spedisce.

Non fa parte del lavoro del mattino e non costa token: lo lancia GitHub (.github/workflows/newsletter.yml) quando
l'edizione arriva sul ramo principale. La chiave di Kit sta nei segreti del repository (KIT_API_KEY): qui non compare mai
e non viene mai stampata.

Uso:   python3 redazione/newsletter.py auto       l'invio vero, solo se l'edizione è di oggi e non è già partita
       python3 redazione/newsletter.py prova      una bozza dentro Kit, senza spedire nulla
       python3 redazione/newsletter.py invio-prova  spedisce subito l'ultima edizione, solo se gli iscritti sono al massimo 3
                                                    (collaudo sugli indirizzi di casa: non blocca l'invio vero dello stesso numero)
       python3 redazione/newsletter.py diagnosi   piano dell'account e modelli di email, senza creare nulla
       python3 redazione/newsletter.py anteprima  scrive l'HTML su newsletter_anteprima.html, senza rete

Regole dell'invio automatico (modo auto):
  1. parte solo l'edizione con la data di oggi (ora di Roma): le edizioni di prova del fine settimana non partono;
  2. ogni numero parte una volta sola: se in Kit esiste già un invio con la stessa etichetta, non si rifà;
  3. l'invio è programmato qualche minuto dopo, il tempo che il sito pubblichi la pagina a cui l'email rimanda;
  4. prima delle 8 di mattina (ora di Roma) non parte nulla: una modifica notturna a un'edizione di prova con la data
     del giorno dopo non deve arrivare ai lettori al posto dell'edizione vera.

L'email legge solo la scheda dell'edizione (titolo, dek, ticker, approfondimenti, dove, evento_oggi, scommessa): zero token.

Com'è fatta (G-15, scelta di Paolo del 21/11/2026): testata sottile con la data delle chiusure, i sei mercati in una
fascia chiara (un colpo d'occhio, non corpo della mail), titolo, sommario in due frasi, pulsante, poi l'indice
dell'edizione, una riga per pagina. La notizia e il suo perché si leggono senza cliccare; il resto è sul sito.

La testata la compone questo script, perché porta una data che cambia ogni giorno. Cornice e piè di pagina (riga
sull'intelligenza artificiale, link per annullare l'iscrizione, indirizzo postale, caratteri del sito, regole per il
telefono) stanno nei modelli caricati a mano in Kit (Broadcasts > Templates):
  "Gommberg cornice"   = redazione/newsletter_cornice.html: lo usa questo script (margine zero, niente testata);
  "Gommberg"           = redazione/newsletter_modello.html con il margine attorno al contenuto: è il predefinito, per
                         l'email di conferma e per ogni email scritta a mano dentro Kit (ha la sua testata).
Se cambia un file, il modello corrispondente in Kit va aggiornato. Se "Gommberg cornice" non esiste in Kit l'invio non
parte, su nessun altro modello (se l'elenco dei modelli non si legge per un guasto momentaneo di Kit, quattro tentativi
a 15 secondi, poi errore "Kit non risponde"): lo script esce con errore, il giro di newsletter.yml diventa rosso e il controllo del
mattino (mattino.py) segnala che l'invio manca. Mai due testate, mai nessuna.
"""
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parent.parent
BASE = "https://gommberg.com/"
API = "https://api.kit.com/v4"
ATTESA_MINUTI = 4          # tempo lasciato al sito per pubblicare la pagina dell'edizione
CORNICE = "Gommberg cornice"    # il modello di Kit per le edizioni: cornice e piè di pagina, la testata la mette lo script
LETTURE = 4                # tentativi per leggere l'elenco dei modelli di Kit (guasto momentaneo: 429, 5xx, rete)
ATTESA_LETTURE = 15        # secondi tra un tentativo e l'altro (il collaudo la azzera)
ORA_MINIMA = 8             # prima di quest'ora (Roma) l'invio automatico non parte
GIORNI = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto",
        "settembre", "ottobre", "novembre", "dicembre"]

# Colori e caratteri del sito (assets/sito.css, index.html). I caratteri del sito li carica la cornice, ma Gmail e Outlook
# non caricano mai caratteri dal web: lì vale il resto della lista, e per molti lettori il resto della lista È l'email.
# Quindi il ripiego si sceglie con la stessa cura (Paolo, 26/11: con Courier New la fascia dei mercati non era professionale):
# i caratteri di sistema del dispositivo (Segoe UI su Windows, San Francisco su Mac e iPhone, Roboto su Android), gli
# stessi che usa l'interfaccia di Gmail. Nell'email non c'è nulla a spaziatura fissa: il suo ripiego sarebbe Courier New.
# Le cifre vanno incolonnate con le cifre tabellari (CIFRE), non con un carattere da macchina da scrivere.
NERO, CARTA, INCHIOSTRO, ARANCIO, ARANCIO_TESTO, GRIGIO, FILO = "#0E0E0E", "#FBFAF8", "#141414", "#F26B1D", "#B84A0C", "#5E5A55", "#DEDAD4"
PANNELLO, TENUE, SOFFUSO = "#F1EEE9", "#A39C93", "#D6D1C9"
SU, GIU = "#12753D", "#C0261C"          # sul chiaro, come nel sito
SISTEMA = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"
FONT = "'IBM Plex Sans'," + SISTEMA
TITOLI = "'Archivo'," + SISTEMA                                   # titolo della notizia: senza il nome stretto, nel ripiego
MARCHIO = "'Archivo','Arial Narrow',sans-serif-condensed," + SISTEMA   # la testata resta stretta anche nel ripiego
CIFRE = "font-variant-numeric:tabular-nums;"                      # numeri della stessa larghezza, incolonnati
ETICHETTA = f"font:700 11px/1.3 {FONT};letter-spacing:.08em;text-transform:uppercase"   # occhielli, pagine, chiusure
# Nomi brevi dei mercati: gli stessi della homepage (index.html, CORTI)
CORTI = {"EURO STOXX 50": "Stoxx 50", "UST 10 ANNI": "Treasury 10a", "TREASURY 10 ANNI": "Treasury 10a", "BRENT FUTURE": "Brent"}


def ultima_edizione():
    elenco = json.loads((REPO / "edizioni.json").read_text(encoding="utf-8"))
    n = max(int(e["numero"]) for e in elenco)
    return json.loads((REPO / "e" / f"{n:03d}.json").read_text(encoding="utf-8"))


def data_estesa(iso):
    d = date.fromisoformat(iso)
    return f"{GIORNI[d.weekday()]} {d.day} {MESI[d.month - 1]} {d.year}"


def etichetta(ed, prova=False):
    return f"gommberg-{'prova' if prova else 'edizione'}-{int(ed['numero']):03d}"


def data_breve(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {MESI[d.month - 1]}"


def tabella(*righe, extra=""):
    return f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"{extra}>' + "".join(righe) + "</table>"


def mercati(ed):
    """I sei mercati della fascia: nome breve, valore, variazione senza segno, verso (+1 su, -1 giù, 0 fermo). Il Mondo resta al sito."""
    out = []
    for nome, valore, var in [v for v in (ed.get("ticker") or []) if len(v) >= 3 and "ACWI" not in str(v[0]).upper()][:6]:
        var = str(var).strip()
        var = var[:-2] if var.endswith(" g") else var
        nudo = var.lstrip("+-−").strip()
        fermo = not re.search(r"[1-9]", nudo)
        verso = 0 if fermo else 1 if var.startswith("+") else -1 if var.startswith(("-", "−")) else 0
        out.append((CORTI.get(str(nome).upper(), str(nome)), str(valore), nudo, verso))
    return out


def testata(ed):
    """La testata sottile: marchio, motto e, a destra nel nero, la data delle chiusure della fascia qui sotto."""
    al = ed.get("ticker_al")
    return testata_con(f"Chiusure del {data_breve(al)}" if al and len(mercati(ed)) >= 3 else "", int(ed.get("pagine") or 6))


def testata_con(destra, pagine=6):
    """La testata di ogni email del Gommberg (anche le mail straordinarie, dem.py): a destra la riga del giorno, se c'è."""
    e = html.escape
    data = (f'<td class="gt-d" align="right" valign="bottom" style="padding:5px 0 1px;{ETICHETTA};font-size:10px;'
            f'color:{TENUE};white-space:nowrap">{e(destra)}</td>' if destra else "")
    return (f'<tr><td class="gx" style="background:{NERO};border-bottom:3px solid {ARANCIO};padding:15px 28px 10px">'
            f'<a href="{BASE}" style="text-decoration:none;font:900 21px/1 {MARCHIO};font-stretch:75%;letter-spacing:.01em;color:#F5F3EF">'
            f'<span style="color:{ARANCIO}">GOMMBERG</span> <span style="font-weight:600">TERMINAL DAILY</span></a>'
            + tabella(f'<tr><td class="gt-m" style="padding:5px 0 0;font:13px/1.4 {FONT};color:{SOFFUSO}">I mercati globali '
                      f'<span style="color:{ARANCIO}">spiegati</span>, ogni mattina in {pagine} pagine.</td>{data}</tr>')
            + '</td></tr>')


def fascia(ed):
    """I mercati sotto la testata, come il nastro di un terminale: sei colonne uguali divise da un filo, in ognuna il nome
    in maiuscoletto grigio, il valore in evidenza e la variazione colorata con il segno (su, giù, fermo). È una fascia, non
    corpo della mail: fondo del pannello del sito. Sul telefono va su due righe da tre (regola nella cornice, classe gm-c)."""
    e = html.escape
    voci = mercati(ed)
    if len(voci) < 3:
        return ""
    celle = []
    for k, (nome, valore, var, verso) in enumerate(voci):
        colore = SU if verso > 0 else GIU if verso < 0 else GRIGIO
        freccia = "&#9650;" if verso > 0 else "&#9660;" if verso < 0 else "="
        filo = "" if k == 0 else f"border-left:1px solid {FILO};"
        celle.append(
            f'<td class="gm-c" valign="top" width="{100 // len(voci)}%" style="{filo}padding:0 0 0 {0 if k == 0 else 10}px">'
            f'<span style="display:block;{ETICHETTA};font-size:10px;letter-spacing:.03em;color:{GRIGIO};white-space:nowrap">{e(nome)}</span>'
            f'<span style="display:block;font:600 14px/1.35 {FONT};{CIFRE}color:{INCHIOSTRO};white-space:nowrap">{e(valore)}</span>'
            f'<span style="display:block;font:600 12px/1.3 {FONT};{CIFRE}color:{colore};white-space:nowrap">'
            f'<span style="font-size:8px;vertical-align:1px">{freccia}</span>&nbsp;{e(var)}</span></td>')
    return (f'<tr><td class="gx" style="background:{PANNELLO};border-bottom:1px solid {FILO};padding:11px 28px 10px">'
            + tabella("<tr>" + "".join(celle) + "</tr>") + '</td></tr>')


def sommario_breve(dek):
    """Il sommario in due frasi: il fatto (la prima) e la lettura (l'ultima). Il resto è nell'edizione."""
    frasi = [f.strip() for f in re.split(r'(?<=[.!?])\s+(?=[A-ZÀ-Ý"«(])', dek or "") if f.strip()]
    return (dek or "").strip() if len(frasi) <= 2 else frasi[0] + " " + frasi[-1]


def minuscola(testo):
    """Dopo i due punti: iniziale minuscola, tranne le sigle (PCE, Pil resta com'è scritto se la seconda lettera è maiuscola)."""
    return testo[:1].lower() + testo[1:] if len(testo) > 1 and testo[1].islower() else testo


def evento(ed):
    """La riga dell'agenda: "Oggi alle 16:00: ..." se l'evento è di oggi, altrimenti il giorno com'è scritto in agenda."""
    m = re.match(r"\s*([A-Za-zì]{3})\s+(\d{1,2})(?:,\s*(\d{1,2}:\d{2}))?\s+(.+?)\s*$", str(ed.get("evento_oggi") or ""))
    if not m:
        return ""
    giorno, numero, ora, cosa = m.groups()
    cosa = minuscola(re.sub(r"\s*\([^)]*\)\s*$", "", cosa))
    if int(numero) == date.fromisoformat(ed["data"]).day:
        return f"Oggi alle {ora}: {cosa}" if ora else f"Oggi: {cosa}"
    return f"{giorno.capitalize()} {numero}{' alle ' + ora if ora else ''}: {cosa}"


def scommessa(ed):
    """La riga della scommessa: il lunedì i pronostici, poi il punteggio; il venerdì si chiude."""
    sc = ed.get("scommessa") or {}
    if not sc:
        return ""
    if sc.get("strada") is None or sc.get("range") is None:
        return "I sei pronostici della settimana"
    punti = int(sc["strada"]) + int(sc["range"])
    testo = f"{punti} punt{'o' if punti == 1 else 'i'} su {2 * int(sc.get('su') or 6)}"
    return testo + (", stasera si chiude" if date.fromisoformat(ed["data"]).weekday() == 4 else " finora")


def indice(ed):
    """Dentro l'edizione: una riga per pagina. Titoli e pagine sono quelli della scheda, scritti dalla redazione."""
    dove = ed.get("dove") or {}
    pagine = dove.get("approfondimenti") or []
    voci = [(pagine[i] if i < len(pagine) else None, a.get("tema") or "", a.get("titolo") or "")
            for i, a in enumerate(ed.get("approfondimenti") or []) if a.get("titolo")]
    if evento(ed):
        voci.append((dove.get("agenda"), "Mercati e agenda", evento(ed)))
    if scommessa(ed):
        voci.append((dove.get("scommessa"), "La scommessa della settimana", scommessa(ed)))
    return voci


def anteprima_locale(corpo):
    """Il contenuto dentro la cornice, per guardarlo in locale senza passare da Kit."""
    cornice = (REPO / "redazione" / "newsletter_cornice.html").read_text(encoding="utf-8")
    return (cornice.replace("{{ message_content }}", corpo).replace("{{ unsubscribe_url }}", "#")
            .replace("{{ address }}", "[indirizzo postale]"))


def componi(ed):
    """Oggetto, riga di anteprima e contenuto HTML. Una colonna, stili in linea, niente immagini: regge in ogni casella."""
    e = html.escape
    n = int(ed["numero"])
    # I link portano alla homepage ferma su QUESTA edizione (?n=), non sull'ultima: chi apre la mail tre giorni dopo
    # trova le pagine di cui parla la mail. Da PC leggi=1 apre subito il lettore a tutto schermo; sul telefono resta
    # la prima pagina del sito con "Leggi l'edizione". ref=email: GoatCounter lo segna come provenienza.
    # Niente link diretto al PDF (Paolo, 16/11): il PDF si apre dal sito, così ogni lettura passa dal sito e si conta.
    pagina = f"{BASE}?n={n}&amp;leggi=1&amp;ref=email"
    occhiello = f'{ETICHETTA};color:{ARANCIO_TESTO};margin:0 0 10px'

    voci = indice(ed)
    righe = "".join(
        f'<tr><td valign="top" width="62" style="padding:11px 0;border-top:1px solid {FILO};{ETICHETTA};line-height:1.9;color:{ARANCIO_TESTO};white-space:nowrap">'
        f'{"Pag. " + str(int(p)) if p else "&nbsp;"}</td>'
        f'<td style="padding:11px 0;border-top:1px solid {FILO}"><span style="display:block;{ETICHETTA};color:{GRIGIO};margin:0 0 3px">{e(tema)}</span>'
        f'<a href="{pagina}" style="font:700 16px/1.35 {FONT};color:{INCHIOSTRO};text-decoration:none">{e(testo)}</a></td></tr>'
        for p, tema, testo in voci)
    dentro = (f'<tr><td class="gx" style="padding:26px 28px 0"><p style="{occhiello}">Dentro l\'edizione di oggi</p>'
              + tabella(righe, extra=f' style="border-bottom:1px solid {FILO}"') + '</td></tr>' if voci else "")

    corpo = f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
{testata(ed)}{fascia(ed)}
<tr><td class="gx" style="padding:24px 28px 0">
<p style="font:13px/1.4 {FONT};color:{GRIGIO};margin:0 0 10px">{e(data_estesa(ed["data"]))} - Edizione #{n:03d}</p>
<h1 style="font:800 28px/1.15 {TITOLI};font-stretch:80%;letter-spacing:-.01em;color:{INCHIOSTRO};margin:0 0 12px">{e(ed["titolo"])}</h1>
<p style="font:16px/1.55 {FONT};color:{INCHIOSTRO};margin:0">{e(sommario_breve(ed.get("dek") or ""))}</p>
</td></tr>
<tr><td class="gx" style="padding:18px 28px 0">
<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
<td bgcolor="{NERO}" style="background:{NERO};border-radius:3px"><a href="{pagina}" style="display:inline-block;padding:13px 22px;font:700 16px/1 {FONT};color:#FFFFFF;text-decoration:none">Leggi le {int(ed.get("pagine") or 6)} pagine</a></td>
</tr></table>
</td></tr>
{dentro}
<tr><td class="gx" style="padding:24px 28px 0">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
<td style="background:{PANNELLO};border-left:3px solid {ARANCIO};padding:13px 16px;font:15px/1.5 {FONT};color:{INCHIOSTRO}"><b>Chiedi al Gommberg.</b> Hai una domanda, o c'è un tema che vorresti vedere approfondito? Rispondi a questa email.</td>
</tr></table>
</td></tr>
<tr><td class="gx" style="padding:16px 28px 18px;font:13px/1.5 {FONT};color:{GRIGIO}">Te l'hanno inoltrata? <a href="{BASE}iscriviti.html" style="color:{ARANCIO_TESTO}">Ricevila anche tu ogni mattina</a>.</td></tr>
</table>"""
    oggetto = f"Gommberg #{n:03d} - {ed['titolo']}"
    temi = [a.get("tema") for a in (ed.get("approfondimenti") or []) if a.get("tema")]
    anteprima = " ".join(x for x in ((f"Dentro: {', '.join(dict.fromkeys(temi))}." if temi else ""), (evento(ed) + "." if evento(ed) else "")) if x)
    return oggetto, anteprima or (ed.get("dek") or "")[:140], corpo


def kit(metodo, percorso, dati=None):
    """Una chiamata a Kit: (stato HTTP, corpo). Se la rete non risponde (indirizzo, timeout, connessione) torna
    (0, {"errore": ...}) come ogni altra risposta non riuscita: chi chiama controlla lo stato, nessun traceback."""
    chiave = os.environ.get("KIT_API_KEY", "").strip()
    if not chiave:
        sys.exit("ERRORE: manca KIT_API_KEY (segreto del repository)")
    richiesta = urllib.request.Request(
        API + percorso, method=metodo,
        data=json.dumps(dati).encode("utf-8") if dati is not None else None,
        headers={"X-Kit-Api-Key": chiave, "Content-Type": "application/json", "Accept": "application/json",
                 "User-Agent": "gommberg-newsletter/1.0"})
    try:
        with urllib.request.urlopen(richiesta, timeout=30) as risposta:
            testo = risposta.read().decode("utf-8")
            return risposta.status, (json.loads(testo) if testo.strip() else {})
    except urllib.error.HTTPError as errore:
        testo = errore.read().decode("utf-8", "replace")
        try:
            return errore.code, json.loads(testo)
        except ValueError:
            return errore.code, {"errore": testo[:300]}
    except (urllib.error.URLError, OSError) as errore:       # URLError e timeout sono OSError
        return 0, {"errore": f"rete: {getattr(errore, 'reason', errore)}"[:300]}


def invii_esistenti():
    """Le etichette (description) degli invii già presenti in Kit, per non rifare mai lo stesso numero."""
    stato, corpo = kit("GET", "/broadcasts?per_page=100")
    if stato != 200:
        sys.exit(f"ERRORE: elenco degli invii non leggibile (HTTP {stato}): {json.dumps(corpo, ensure_ascii=False)[:300]}")
    return {b.get("description"): b for b in corpo.get("broadcasts", [])}


def modello_edizione():
    """L'id del modello "Gommberg cornice" in Kit. L'elenco dei modelli è una lettura: se Kit ha un guasto momentaneo
    (429, 5xx, rete) si riprova a distanza, LETTURE volte. Se l'elenco si legge e la cornice non c'è, l'invio non parte;
    se dopo i tentativi l'elenco non si legge, l'invio non parte lo stesso e l'errore è un altro. Su nessun altro modello:
    l'email uscirebbe con un'altra cornice o con due testate. Solo le letture si ritentano: mai la creazione dell'invio."""
    for tentativo in range(1, LETTURE + 1):
        stato, corpo = kit("GET", "/email_templates")
        if stato == 200:
            nomi = {(m.get("name") or "").strip().lower(): m.get("id") for m in corpo.get("email_templates", [])}
            if CORNICE.lower() not in nomi:
                sys.exit(f'ERRORE: la cornice non c\'è in Kit: modello "{CORNICE}" non trovato nell\'elenco: invio non fatto')
            return nomi[CORNICE.lower()]
        transitorio = stato == 0 or stato == 429 or stato >= 500
        if not transitorio or tentativo == LETTURE:
            break
        time.sleep(ATTESA_LETTURE)
    sys.exit(f"ERRORE: Kit non risponde: elenco dei modelli non leggibile dopo {tentativo} tentativ{'o' if tentativo == 1 else 'i'} "
             f"(HTTP {stato}: {json.dumps(corpo, ensure_ascii=False)[:200]}): invio non fatto, su nessun altro modello")


def crea(ed, quando, prova):
    modello = modello_edizione()
    oggetto, anteprima, corpo = componi(ed)
    dati = {"subject": oggetto, "preview_text": anteprima, "content": corpo, "description": etichetta(ed, prova),
            "public": False, "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "send_at": quando.isoformat(timespec="seconds") if quando else None}
    dati["email_template_id"] = modello
    stato, risposta = kit("POST", "/broadcasts", dati)
    if stato not in (200, 201):
        if stato == 0:   # rete caduta o tempo scaduto DOPO la richiesta: l'invio può esserci lo stesso. Mai un secondo tentativo qui
            sys.exit(f"ERRORE: esito incerto, Kit non ha risposto alla creazione dell'invio: guarda in Kit (Broadcasts) prima di rilanciare. {json.dumps(risposta, ensure_ascii=False)[:300]}")
        sys.exit(f"ERRORE: Kit non ha accettato l'email (HTTP {stato}): {json.dumps(risposta, ensure_ascii=False)[:400]}")
    b = risposta.get("broadcast", {})
    modello = (b.get("email_template") or {}).get("name")
    print(f"OK: {'bozza' if not quando else 'invio programmato'} n. {b.get('id')} - {oggetto} - modello: {modello} - stato: {b.get('status')}")


def main():
    modo = (sys.argv[1] if len(sys.argv) > 1 else "auto").strip() or "auto"
    ed = ultima_edizione()

    if modo == "anteprima":
        oggetto, anteprima, corpo = componi(ed)
        Path("newsletter_anteprima.html").write_text(anteprima_locale(corpo), encoding="utf-8")
        print(f"Anteprima scritta: {oggetto} | {anteprima}")
        return

    if modo == "diagnosi":
        chiave = os.environ.get("KIT_API_KEY", "").strip()      # mai il valore: solo lunghezza e forma
        print(f"Chiave: {len(chiave)} caratteri, forma V4 (kit_...): {'sì' if chiave.startswith('kit_') else 'no'}")
        stato, conto = kit("GET", "/account")
        print(f"Account: HTTP {stato} - piano: {(conto.get('account') or {}).get('plan_type')}")
        stato, modelli = kit("GET", "/email_templates")
        print(f"Modelli: HTTP {stato} - " + "; ".join(
            f"{m.get('id')} {m.get('name')}{' (predefinito)' if m.get('is_default') else ''}" for m in modelli.get("email_templates", [])))
        stato, corpo = kit("GET", "/broadcasts?per_page=100")
        print(f"Invii presenti: HTTP {stato} - {len(corpo.get('broadcasts', []))}")
        return

    if modo in ("prova", "invio-prova"):
        if modo == "invio-prova":
            # Mai gli indirizzi nel registro (è pubblico): solo quanti sono. Oltre 3 iscritti questo modo non spedisce.
            stato, corpo = kit("GET", "/subscribers?status=active&per_page=5")
            quanti = len(corpo.get("subscribers", [])) if stato == 200 else -1
            if not 1 <= quanti <= 3:
                sys.exit(f"ERRORE: invio di prova rifiutato, iscritti attivi: {quanti if quanti >= 0 else 'non leggibili'} (ammessi da 1 a 3)")
            print(f"Invio di prova a {quanti} iscritt{'o' if quanti == 1 else 'i'}")
        vecchia = invii_esistenti().get(etichetta(ed, prova=True))
        if vecchia and vecchia.get("id") and vecchia.get("status") in (None, "draft"):
            kit("DELETE", f"/broadcasts/{vecchia['id']}")       # una sola bozza di prova per numero
        crea(ed, datetime.now(timezone.utc) + timedelta(minutes=1) if modo == "invio-prova" else None, prova=True)
        return

    if modo != "auto":
        sys.exit(f"ERRORE: modo sconosciuto: {modo}")
    adesso = datetime.now(ZoneInfo("Europe/Rome"))
    oggi = adesso.date().isoformat()
    if ed["data"] != oggi:
        print(f"Niente invio: l'ultima edizione è del {ed['data']}, oggi è {oggi}.")
        return
    if adesso.hour < ORA_MINIMA:
        print(f"Niente invio: sono le {adesso:%H:%M}, prima delle {ORA_MINIMA} non parte nulla.")
        return
    if etichetta(ed) in invii_esistenti():
        print(f"Niente invio: l'edizione #{int(ed['numero']):03d} è già partita.")
        return
    crea(ed, datetime.now(timezone.utc) + timedelta(minutes=ATTESA_MINUTI), prova=False)


if __name__ == "__main__":
    main()
