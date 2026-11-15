#!/usr/bin/env python3
"""L'edizione via email. Compone l'email dalla scheda dell'ultima edizione (e/NNN.json) e la passa a Kit, che la spedisce.

Non fa parte del lavoro del mattino e non costa token: lo lancia GitHub (.github/workflows/newsletter.yml) quando
l'edizione arriva sul ramo principale. La chiave di Kit sta nei segreti del repository (KIT_API_KEY): qui non compare mai
e non viene mai stampata.

Uso:   python3 redazione/newsletter.py auto       l'invio vero, solo se l'edizione è di oggi e non è già partita
       python3 redazione/newsletter.py prova      una bozza dentro Kit, senza spedire nulla
       python3 redazione/newsletter.py diagnosi   piano dell'account e modelli di email, senza creare nulla
       python3 redazione/newsletter.py anteprima  scrive l'HTML su newsletter_anteprima.html, senza rete

Regole dell'invio automatico (modo auto):
  1. parte solo l'edizione con la data di oggi (ora di Roma): le edizioni di prova del fine settimana non partono;
  2. ogni numero parte una volta sola: se in Kit esiste già un invio con la stessa etichetta, non si rifà;
  3. l'invio è programmato qualche minuto dopo, il tempo che il sito pubblichi la pagina a cui l'email rimanda.

L'email usa solo i campi base della scheda (numero, data, titolo, dek, sommario, notizie, file): gli stessi di home e feed.
Il link per annullare l'iscrizione e l'indirizzo postale li aggiunge il modello di Kit in fondo: qui non vanno ripetuti.
"""
import html
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parent.parent
BASE = "https://paologom.github.io/Gommberg-Terminal-Daily/"
API = "https://api.kit.com/v4"
ATTESA_MINUTI = 4          # tempo lasciato al sito per pubblicare la pagina dell'edizione
GIORNI = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto",
        "settembre", "ottobre", "novembre", "dicembre"]

# Colori della testata e del sito (assets/sito.css)
NERO, CARTA, INCHIOSTRO, ARANCIO, ARANCIO_TESTO, GRIGIO, FILO = "#0E0E0E", "#FBFAF8", "#141414", "#F26B1D", "#B84A0C", "#5E5A55", "#DEDAD4"
FONT = "Arial, Helvetica, sans-serif"


def ultima_edizione():
    elenco = json.loads((REPO / "edizioni.json").read_text(encoding="utf-8"))
    n = max(int(e["numero"]) for e in elenco)
    return json.loads((REPO / "e" / f"{n:03d}.json").read_text(encoding="utf-8"))


def data_estesa(iso):
    d = date.fromisoformat(iso)
    return f"{GIORNI[d.weekday()]} {d.day} {MESI[d.month - 1]} {d.year}"


def etichetta(ed, prova=False):
    return f"gommberg-{'prova' if prova else 'edizione'}-{int(ed['numero']):03d}"


def componi(ed):
    """Oggetto, riga di anteprima e corpo HTML. Una colonna, stili in linea, niente immagini: regge in ogni casella."""
    e = html.escape
    n = int(ed["numero"])
    pagina = f"{BASE}e/{n:03d}.html"
    pdf = BASE + ed["file"]
    sommario = [s for s in ed.get("sommario") or [] if s]
    notizie = [s for s in ed.get("notizie") or [] if s]
    occhiello = f'font:700 12px/1.3 {FONT};letter-spacing:.08em;text-transform:uppercase;color:{ARANCIO_TESTO};margin:0 0 8px'

    def elenco(voci):
        return "".join(
            f'<tr><td valign="top" style="padding:0 10px 8px 0;font:16px/1.5 {FONT};color:{ARANCIO}">&#9632;</td>'
            f'<td style="padding:0 0 8px;font:16px/1.5 {FONT};color:{INCHIOSTRO}">{e(v)}</td></tr>' for v in voci)

    blocchi = []
    if sommario:
        blocchi.append(f'<p style="{occhiello}">In 30 secondi</p>'
                       f'<table role="presentation" cellpadding="0" cellspacing="0" border="0">{elenco(sommario)}</table>')
    if notizie:
        blocchi.append(f'<p style="{occhiello}">Le notizie del giorno</p>'
                       f'<table role="presentation" cellpadding="0" cellspacing="0" border="0">{elenco(notizie)}</table>')
    sezioni = "".join(f'<tr><td style="padding:22px 28px 0">{b}</td></tr>' for b in blocchi)

    corpo = f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{CARTA}">
<tr><td align="center" style="padding:0 12px 28px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;background:#FFFFFF;border:1px solid {FILO}">
<tr><td style="background:{NERO};border-bottom:3px solid {ARANCIO};padding:18px 28px 14px">
<a href="{BASE}" style="text-decoration:none;font:900 21px/1 'Arial Narrow',{FONT};letter-spacing:.01em;color:#F5F3EF"><span style="color:{ARANCIO}">GOMMBERG</span> <span style="font-weight:600">TERMINAL DAILY</span></a>
</td></tr>
<tr><td style="padding:22px 28px 0">
<p style="font:13px/1.4 {FONT};color:{GRIGIO};margin:0 0 10px">{e(data_estesa(ed["data"]))} - Edizione #{n:03d}</p>
<h1 style="font:700 26px/1.2 {FONT};color:{INCHIOSTRO};margin:0 0 12px">{e(ed["titolo"])}</h1>
<p style="font:16px/1.55 {FONT};color:{INCHIOSTRO};margin:0">{e(ed.get("dek") or "")}</p>
</td></tr>
{sezioni}
<tr><td style="padding:18px 28px 26px">
<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
<td bgcolor="{NERO}" style="background:{NERO};border-radius:3px"><a href="{pagina}" style="display:inline-block;padding:13px 22px;font:700 16px/1 {FONT};color:#FFFFFF;text-decoration:none">Leggi le {int(ed.get("pagine") or 6)} pagine</a></td>
<td style="padding-left:16px;font:14px/1.4 {FONT}"><a href="{pdf}" style="color:{ARANCIO_TESTO}">Apri il PDF</a></td>
</tr></table>
</td></tr>
<tr><td style="border-top:1px solid {FILO};padding:16px 28px 20px;font:13px/1.5 {FONT};color:{GRIGIO}">
<p style="margin:0 0 10px">Te l'hanno inoltrata? <a href="{BASE}" style="color:{ARANCIO_TESTO}">Ricevila anche tu ogni mattina</a>.</p>
<p style="margin:0">Gommberg Terminal Daily è un progetto di Paolo Gommellini. I testi sono generati con l'intelligenza artificiale e pubblicati in automatico, sotto la sua responsabilità editoriale.</p>
</td></tr>
</table>
</td></tr>
</table>"""
    oggetto = f"Gommberg #{n:03d} - {ed['titolo']}"
    anteprima = sommario[0] if sommario else (ed.get("dek") or "")[:140]
    return oggetto, anteprima, corpo


def kit(metodo, percorso, dati=None):
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


def invii_esistenti():
    """Le etichette (description) degli invii già presenti in Kit, per non rifare mai lo stesso numero."""
    stato, corpo = kit("GET", "/broadcasts?per_page=100")
    if stato != 200:
        sys.exit(f"ERRORE: elenco degli invii non leggibile (HTTP {stato}): {json.dumps(corpo, ensure_ascii=False)[:300]}")
    return {b.get("description"): b for b in corpo.get("broadcasts", [])}


def crea(ed, quando, prova):
    oggetto, anteprima, corpo = componi(ed)
    dati = {"subject": oggetto, "preview_text": anteprima, "content": corpo, "description": etichetta(ed, prova),
            "public": False, "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "send_at": quando.isoformat(timespec="seconds") if quando else None}
    stato, risposta = kit("POST", "/broadcasts", dati)
    if stato not in (200, 201):
        sys.exit(f"ERRORE: Kit non ha accettato l'email (HTTP {stato}): {json.dumps(risposta, ensure_ascii=False)[:400]}")
    b = risposta.get("broadcast", {})
    modello = (b.get("email_template") or {}).get("name")
    print(f"OK: {'bozza' if not quando else 'invio programmato'} n. {b.get('id')} - {oggetto} - modello: {modello} - stato: {b.get('status')}")


def main():
    modo = (sys.argv[1] if len(sys.argv) > 1 else "auto").strip() or "auto"
    ed = ultima_edizione()

    if modo == "anteprima":
        oggetto, anteprima, corpo = componi(ed)
        Path("newsletter_anteprima.html").write_text(
            f"<!doctype html><meta charset='utf-8'><title>{html.escape(oggetto)}</title><body style='margin:0'>{corpo}", encoding="utf-8")
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

    if modo == "prova":
        vecchia = invii_esistenti().get(etichetta(ed, prova=True))
        if vecchia and vecchia.get("id"):
            kit("DELETE", f"/broadcasts/{vecchia['id']}")       # una sola bozza di prova per numero
        crea(ed, None, prova=True)
        return

    if modo != "auto":
        sys.exit(f"ERRORE: modo sconosciuto: {modo}")
    oggi = datetime.now(ZoneInfo("Europe/Rome")).date().isoformat()
    if ed["data"] != oggi:
        print(f"Niente invio: l'ultima edizione è del {ed['data']}, oggi è {oggi}.")
        return
    if etichetta(ed) in invii_esistenti():
        print(f"Niente invio: l'edizione #{int(ed['numero']):03d} è già partita.")
        return
    crea(ed, datetime.now(timezone.utc) + timedelta(minutes=ATTESA_MINUTI), prova=False)


if __name__ == "__main__":
    main()
