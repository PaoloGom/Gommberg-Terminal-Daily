#!/usr/bin/env python3
"""Le mail straordinarie (DEM): auguri, avvisi sulle pause, sondaggi. Tutto ciò che parte agli iscritti fuori
dall'edizione del mattino passa da qui, con le stesse regole per tutti.

Come funziona (G-17, 22/11/2026). Ogni mail è un file in redazione/dem/, con la data di invio all'inizio del nome
(AAAA-MM-GG-nome.md): il file è la verità. Kit è solo l'esecutore: il workflow .github/workflows/dem.yml, a ogni
cambiamento dei file su main e ogni sera, allinea Kit ai file (crea, aggiorna, riporta in bozza, toglie gli invii).
Una mail parte solo se il file dice "stato: approvata" con l'ok di Paolo. Formato e regole: redazione/dem/LEGGIMI.md.
Zero token: lo lancia GitHub. La chiave di Kit è il segreto KIT_API_KEY e non viene mai stampata.

Uso:   python3 redazione/dem.py                 controlla le regole e che pannello/invii.json sia allineato, senza rete
       python3 redazione/dem.py salva           controlla e riscrive pannello/invii.json (da fare prima di ogni commit)
       python3 redazione/dem.py anteprima NOME  scrive _dem/NOME.html, la mail come la vedrà il lettore
       python3 redazione/dem.py piano           legge Kit e stampa che cosa cambierebbe, senza toccare nulla
       python3 redazione/dem.py sincronizza     allinea Kit ai file (lo fa dem.yml); esce con 1 se c'è da guardare

Esce con 1 quando qualcosa va guardato da Paolo: dem.yml apre allora una segnalazione e GitHub gli manda l'email.
"""
import html
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

QUI = Path(__file__).resolve().parent
sys.path.insert(0, str(QUI))
import giorni  # noqa: E402  calendario delle uscite (FESTIVI letti dal motore)
import newsletter as nl  # noqa: E402  colori, caratteri, cornice e chiamate a Kit: una sola definizione

REPO = QUI.parent
CARTELLA = QUI / "dem"
VISTA = REPO / "pannello" / "invii.json"
ANTEPRIME = REPO / "_dem"
ROMA = ZoneInfo("Europe/Rome")
ETICHETTA = "gommberg-dem-"     # description dell'invio in Kit: lega l'invio al suo file

# Le regole. Si cambiano qui e in LEGGIMI.md, insieme.
MIN_GIORNI = 21           # tra due mail straordinarie (non annullate): al massimo una ogni tre settimane
ORA_DA, ORA_A = 8, 21     # si spedisce tra le 8:00 e le 20:59
FINESTRA = (7, 11)        # nei giorni di uscita, dalle 7:00 alle 10:59 c'è l'edizione: niente mail straordinarie
PROMEMORIA = 10           # giorni prima dell'invio in cui una bozza non approvata diventa da guardare
MARGINE_MIN = 15          # sotto questi minuti dall'invio Kit non si tocca più
PAROLE_AVVISO, PAROLE_MAX = 250, 400
STATI = ("bozza", "approvata", "annullata")
NOME_FILE = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
TRATTINI_LUNGHI = re.compile("[–—]")
FIRMA = "La redazione del Gommberg"

e = html.escape


class Mail:
    """Una mail straordinaria letta dal suo file. errori: la fermano; avvisi: da leggere."""

    def __init__(self, percorso):
        self.percorso = Path(percorso)
        self.nome = self.percorso.stem
        self.campi, self.corpo = {}, ""
        self.errori, self.avvisi = [], []
        self.invio = None           # datetime con il fuso di Roma
        self.blocchi = []
        self._leggi()

    @property
    def etichetta(self):
        return ETICHETTA + self.nome

    def __getitem__(self, k):
        return self.campi.get(k, "")

    def _leggi(self):
        m = NOME_FILE.match(self.percorso.name)
        if not m:
            self.errori.append("il nome deve essere AAAA-MM-GG-nome.md (minuscole, cifre e trattini)")
        testo = self.percorso.read_text(encoding="utf-8").replace("\r\n", "\n")
        parti = re.match(r"^---\n(.*?)\n---\n?(.*)$", testo, re.S)
        if not parti:
            self.errori.append("manca l'intestazione tra le due righe ---")
            return
        for riga in parti.group(1).splitlines():
            if not riga.strip() or riga.lstrip().startswith("#"):
                continue
            if ":" not in riga:
                self.errori.append(f"riga dell'intestazione senza i due punti: {riga.strip()[:40]}")
                continue
            k, v = riga.split(":", 1)
            self.campi[k.strip().lower()] = v.strip()
        self.corpo = parti.group(2).strip()

        for k in ("invio", "stato", "oggetto", "anteprima"):
            if not self[k]:
                self.errori.append(f"manca il campo {k}")
        if self["stato"] and self["stato"] not in STATI:
            self.errori.append(f"stato sconosciuto: {self['stato']} (ammessi: {', '.join(STATI)})")
        try:
            self.invio = datetime.strptime(self["invio"], "%Y-%m-%d %H:%M").replace(tzinfo=ROMA)
        except ValueError:
            if self["invio"]:
                self.errori.append(f"invio non leggibile: {self['invio']} (formato AAAA-MM-GG HH:MM, ora di Roma)")
        if m and self.invio and m.group(1) != self.invio.date().isoformat():
            self.errori.append(f"la data nel nome ({m.group(1)}) non è quella di invio ({self.invio.date().isoformat()})")
        if self["stato"] == "approvata" and not re.match(r"^\S.* \d{4}-\d{2}-\d{2}$", self["ok"]):
            self.errori.append("approvata senza l'ok: serve la riga 'ok: Paolo AAAA-MM-GG'")
        if self["pulsante"] and not re.match(r"^[^|]{2,40}\|\s*https://\S+$", self["pulsante"]):
            self.errori.append("pulsante nel formato 'Testo | https://indirizzo' (testo fino a 40 caratteri)")
        self._regole_testo()
        self.blocchi = self._blocchi()

    def _regole_testo(self):
        if self.invio:
            h = self.invio.hour
            if not ORA_DA <= h < ORA_A:
                self.errori.append(f"ora di invio {self.invio:%H:%M}: si spedisce tra le {ORA_DA}:00 e le {ORA_A - 1}:59")
            if giorni.uscita(self.invio.date()) and FINESTRA[0] <= h < FINESTRA[1]:
                self.errori.append(f"{self.invio:%d/%m} è un giorno di uscita: tra le {FINESTRA[0]}:00 e le "
                                   f"{FINESTRA[1] - 1}:59 c'è l'edizione, scegli un'altra ora")
        o, a = self["oggetto"], self["anteprima"]
        if o and not 8 <= len(o) <= 78:
            self.errori.append(f"oggetto di {len(o)} caratteri (da 8 a 78)")
        if o and (o.isupper() or "!!" in o):
            self.errori.append("oggetto urlato (tutto maiuscolo o punti esclamativi ripetuti)")
        if a and not 20 <= len(a) <= 140:
            self.errori.append(f"anteprima di {len(a)} caratteri (da 20 a 140)")
        tutto = "\n".join(list(self.campi.values()) + [self.corpo])
        if TRATTINI_LUNGHI.search(tutto):
            self.errori.append("trattini lunghi: si usa solo il trattino corto -")
        for url in re.findall(r"\]\(([^)]*)\)", self.corpo + self["nota"]) + re.findall(r"\|\s*(\S+)$", self["pulsante"]):
            if not url.startswith("https://"):
                self.errori.append(f"link non https: {url[:60]}")
        n = len(re.findall(r"\w+", re.sub(r"\]\([^)]*\)", "]", self.corpo)))
        self.parole = n
        if not self.corpo:
            self.errori.append("il testo della mail è vuoto")
        elif n > PAROLE_MAX:
            self.errori.append(f"{n} parole: una mail straordinaria ne ha al massimo {PAROLE_MAX}")
        elif n > PAROLE_AVVISO:
            self.avvisi.append(f"{n} parole: sopra {PAROLE_AVVISO} si legge meno")

    def _blocchi(self):
        """Il testo in blocchi: ('p', testo) ('h', titolo) ('ul', [voci]) ('box', testo) ('sondaggio', domanda, [opzioni])."""
        out, sondaggi = [], 0
        for b in re.split(r"\n\s*\n", self.corpo):
            righe = [r.rstrip() for r in b.strip().splitlines() if r.strip()]
            if not righe:
                continue
            if righe[0].startswith("??"):
                opzioni = [r.lstrip()[2:].strip() for r in righe[1:] if r.lstrip().startswith("- ")]
                sondaggi += 1
                if not 2 <= len(opzioni) <= 5 or len(opzioni) != len(righe) - 1:
                    self.errori.append("sondaggio: la domanda dopo ?? e poi da 2 a 5 risposte, una per riga con '- '")
                if any(len(x) > 90 for x in opzioni):
                    self.errori.append("sondaggio: ogni risposta al massimo 90 caratteri")
                out.append(("sondaggio", righe[0][2:].strip(), opzioni))
            elif righe[0].startswith("## "):
                out.append(("h", righe[0][3:].strip()))
                if len(righe) > 1:
                    out.append(("p", " ".join(righe[1:])))
            elif all(r.lstrip().startswith("- ") for r in righe):
                out.append(("ul", [r.lstrip()[2:].strip() for r in righe]))
            elif all(r.startswith(">") for r in righe):
                out.append(("box", " ".join(r[1:].strip() for r in righe)))
            else:
                out.append(("p", " ".join(r.strip() for r in righe)))
        if sondaggi > 1:
            self.errori.append("un solo sondaggio per mail")
        return out


def leggi_tutte(cartella=CARTELLA):
    return [Mail(p) for p in sorted(Path(cartella).glob("*.md")) if p.name != "LEGGIMI.md"]


def regole_calendario(mail):
    """La regola tra mail diverse: al massimo una ogni MIN_GIORNI giorni (le annullate non contano)."""
    vive = sorted([m for m in mail if m.invio and m["stato"] != "annullata"], key=lambda m: m.invio)
    for a, b in zip(vive, vive[1:]):
        gap = (b.invio.date() - a.invio.date()).days
        if gap < MIN_GIORNI:
            b.errori.append(f"a {gap} giorni da {a.nome}: tra due mail straordinarie almeno {MIN_GIORNI} giorni")


# ------------------------------------------------------------------ composizione dell'email
def in_linea(t):
    """Il testo di una riga: tutto in chiaro, salvo **grassetto** e [link](https://...)."""
    t = e(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return re.sub(r"\[([^\]]+)\]\((https://[^)\s]+)\)",
                  lambda m: f'<a href="{m.group(2)}" style="color:{nl.ARANCIO_TESTO}">{m.group(1)}</a>', t)


def testata_dem(m):
    """La testata sottile dell'email del mattino, con la data di invio a destra al posto delle chiusure."""
    giorno = f"{m.invio.day} {nl.MESI[m.invio.month - 1]} {m.invio.year}".upper() if m.invio else ""
    data = (f'<td class="gt-d" align="right" valign="bottom" style="padding:5px 0 1px;font:700 10px/1.4 {nl.MONO};'
            f'letter-spacing:.05em;color:{nl.TENUE};white-space:nowrap">{e(giorno)}</td>')
    return (f'<tr><td class="gx" style="background:{nl.NERO};border-bottom:3px solid {nl.ARANCIO};padding:15px 28px 10px">'
            f'<a href="{nl.BASE}" style="text-decoration:none;font:900 21px/1 {nl.TITOLI};font-stretch:75%;letter-spacing:.01em;color:#F5F3EF">'
            f'<span style="color:{nl.ARANCIO}">GOMMBERG</span> <span style="font-weight:600">TERMINAL DAILY</span></a>'
            + nl.tabella(f'<tr><td class="gt-m" style="padding:5px 0 0;font:13px/1.4 {nl.FONT};color:{nl.SOFFUSO}">I mercati globali '
                         f'<span style="color:{nl.ARANCIO}">spiegati</span>, ogni mattina in 6 pagine.</td>{data}</tr>')
            + '</td></tr>')


def blocco_html(b, m):
    riga = f'<tr><td class="gx" style="padding:16px 28px 0">'
    if b[0] == "p":
        return f'{riga}<p style="font:16px/1.6 {nl.FONT};color:{nl.INCHIOSTRO};margin:0">{in_linea(b[1])}</p></td></tr>'
    if b[0] == "h":
        return (f'<tr><td class="gx" style="padding:24px 28px 0"><p style="font:700 12px/1.3 {nl.MONO};letter-spacing:.06em;'
                f'text-transform:uppercase;color:{nl.ARANCIO_TESTO};margin:0">{in_linea(b[1])}</p></td></tr>')
    if b[0] == "ul":
        voci = "".join(f'<tr><td valign="top" width="18" style="padding:0 0 8px;font:700 16px/1.6 {nl.FONT};color:{nl.ARANCIO}">&#8226;</td>'
                       f'<td style="padding:0 0 8px;font:16px/1.6 {nl.FONT};color:{nl.INCHIOSTRO}">{in_linea(v)}</td></tr>' for v in b[1])
        return f'{riga}{nl.tabella(voci)}</td></tr>'
    if b[0] == "box":
        return (f'{riga}<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
                f'<td style="background:{nl.PANNELLO};border-left:3px solid {nl.ARANCIO};padding:13px 16px;font:15px/1.5 {nl.FONT};'
                f'color:{nl.INCHIOSTRO}">{in_linea(b[1])}</td></tr></table></td></tr>')
    if b[0] == "sondaggio":
        # Ogni risposta è un link diverso: Kit conta i clic per link (la privacy lo dice già), la pagina ringrazia.
        opzioni = "".join(
            f'<tr><td style="padding:0 0 8px"><a href="{nl.BASE}grazie.html?d={m.nome}&amp;r={k}" style="display:block;'
            f'padding:11px 14px;border:1px solid {nl.FILO};border-radius:3px;background:#FFFFFF;font:700 15px/1.4 {nl.FONT};'
            f'color:{nl.INCHIOSTRO};text-decoration:none">{e(x)}</a></td></tr>' for k, x in enumerate(b[2], 1))
        return (f'<tr><td class="gx" style="padding:22px 28px 0"><table role="presentation" width="100%" cellpadding="0" '
                f'cellspacing="0" border="0"><tr><td style="background:{nl.PANNELLO};border-left:3px solid {nl.ARANCIO};padding:14px 16px 8px">'
                f'<p style="font:700 11px/1.3 {nl.FONT};letter-spacing:.06em;text-transform:uppercase;color:{nl.GRIGIO};margin:0 0 6px">Una domanda, un clic</p>'
                f'<p style="font:700 17px/1.4 {nl.FONT};color:{nl.INCHIOSTRO};margin:0 0 12px">{in_linea(b[1])}</p>'
                f'{nl.tabella(opzioni)}'
                f'</td></tr></table></td></tr>')
    return ""


def componi(m, con_testata=True):
    """Oggetto, anteprima e contenuto HTML: la stessa cornice dell'email del mattino (modello "Gommberg cornice")."""
    pezzi = [testata_dem(m) if con_testata else ""]
    if m["titolo"]:
        pezzi.append(f'<tr><td class="gx" style="padding:26px 28px 2px"><h1 style="font:900 28px/1.15 {nl.TITOLI};font-stretch:80%;'
                     f'letter-spacing:0;word-spacing:.04em;color:{nl.INCHIOSTRO};margin:0">{e(m["titolo"])}</h1></td></tr>')
    pezzi += [blocco_html(b, m) for b in m.blocchi]
    if m["pulsante"]:
        testo, url = [x.strip() for x in m["pulsante"].split("|", 1)]
        pezzi.append(f'<tr><td class="gx" style="padding:22px 28px 0"><table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
                     f'<td bgcolor="{nl.NERO}" style="background:{nl.NERO};border-radius:3px"><a href="{e(url)}" style="display:inline-block;'
                     f'padding:13px 22px;font:700 16px/1 {nl.FONT};color:#FFFFFF;text-decoration:none">{e(testo)}</a></td></tr></table></td></tr>')
    chi, _, ruolo = (m["firma"] or FIRMA).partition("|")
    pezzi.append(f'<tr><td class="gx" style="padding:24px 28px {18 if m["nota"] else 26}px"><p style="font:16px/1.5 {nl.FONT};color:{nl.INCHIOSTRO};margin:0">'
                 f'<b>{e(chi.strip())}</b>' + (f'<br><span style="font-size:14px;color:{nl.GRIGIO}">{e(ruolo.strip())}</span>' if ruolo.strip() else "")
                 + '</p></td></tr>')
    if m["nota"]:  # la postilla: avvisi di servizio, piccola, dopo la firma
        pezzi.append(f'<tr><td class="gx" style="padding:0 28px 22px"><p style="font:13px/1.5 {nl.FONT};color:{nl.GRIGIO};'
                     f'margin:0;padding-top:14px;border-top:1px solid {nl.FILO}">{in_linea(m["nota"])}</p></td></tr>')
    corpo = '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">\n' + "\n".join(p for p in pezzi if p) + "\n</table>"
    return m["oggetto"], m["anteprima"], corpo


# ------------------------------------------------------------------ vista del pannello
def vista(mail):
    """pannello/invii.json: solo ciò che serve alla vista Invii (niente testi). Lo stato del momento (programmata,
    inviata, da approvare) lo calcola la pagina con l'ora di chi guarda: il file cambia solo quando cambiano i file."""
    righe = [{"nome": m.nome, "invio": m.invio.strftime("%Y-%m-%dT%H:%M"), "stato": m["stato"], "oggetto": m["oggetto"],
              "ok": m["ok"], "sondaggio": any(b[0] == "sondaggio" for b in m.blocchi), "parole": m.parole}
             for m in sorted(mail, key=lambda m: m.invio) if m.invio]
    return {"regole": {"min_giorni": MIN_GIORNI, "promemoria_giorni": PROMEMORIA, "ore": f"{ORA_DA}:00-{ORA_A - 1}:59",
                       "finestra_edizione": f"{FINESTRA[0]}:00-{FINESTRA[1] - 1}:59"}, "invii": righe}


def testo_vista(mail):
    return json.dumps(vista(mail), ensure_ascii=False, indent=1) + "\n"


# ------------------------------------------------------------------ allineamento con Kit
def quando(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def stato_kit(b, ora):
    """Da un invio di Kit: {'id', 'send_at', 'partito'}. Partito = spedito o in spedizione: non si tocca più."""
    s = str(b.get("status") or "").lower()
    t = quando(b.get("send_at"))
    if s in ("completed", "sent", "sending", "processing"):
        partito = True
    elif s in ("draft", "scheduled"):
        partito = False
    else:
        partito = bool(t and t <= ora)
    return {"id": b.get("id"), "send_at": t, "partito": partito}


def piano(mail, kit, ora):
    """Che cosa fare in Kit, senza farlo. mail: le mail valide; kit: {etichetta: stato_kit}; ora: adesso (UTC).
    Torna (azioni, guardare): azioni = [(tipo, etichetta, mail o None, motivo)] con tipo in
    crea-bozza, crea-programmata, allinea-bozza, allinea-programmata, elimina, nulla; guardare = frasi per Paolo."""
    azioni, guardare = [], []
    margine = timedelta(minutes=MARGINE_MIN)
    per_etichetta = {m.etichetta: m for m in mail}
    for m in sorted(mail, key=lambda m: m.invio):
        k, st, inv = kit.get(m.etichetta), m["stato"], m.invio.astimezone(timezone.utc)
        if k and k["partito"]:
            azioni.append(("nulla", m.etichetta, m, "già partita"))
            if st == "annullata":
                guardare.append(f"{m.nome}: è annullata ma era già partita")
        elif st == "annullata":
            azioni.append(("elimina", m.etichetta, m, "annullata") if k else ("nulla", m.etichetta, m, "annullata"))
        elif inv - ora < margine and k and k["send_at"] and k["send_at"] > ora:
            azioni.append(("nulla", m.etichetta, m, f"parte tra meno di {MARGINE_MIN} minuti: non si tocca"))
        elif st == "bozza":
            if inv <= ora:
                azioni.append(("nulla", m.etichetta, m, "data passata, mai approvata: non è partita"))
            else:
                azioni.append(("allinea-bozza" if k else "crea-bozza", m.etichetta, m, "bozza (in Kit senza data, da approvare)"))
                if inv - ora <= timedelta(days=PROMEMORIA):
                    guardare.append(f"{m.nome}: è ancora in bozza e la data di invio è {m.invio:%d/%m alle %H:%M}. "
                                    "Senza l'ok non parte")
        else:  # approvata
            if inv - ora < margine:
                azioni.append(("nulla", m.etichetta, m, "non programmata"))
                guardare.append(f"{m.nome}: approvata ma non partita (invio del {m.invio:%d/%m alle %H:%M}, in Kit "
                                + ("in bozza" if k else "assente") + "): spostare la data o controllare in Kit")
            else:
                azioni.append(("allinea-programmata" if k else "crea-programmata", m.etichetta, m,
                               f"programmata per il {m.invio:%d/%m alle %H:%M}"))
    for etichetta, k in sorted(kit.items()):
        if etichetta not in per_etichetta and not k["partito"]:
            azioni.append(("elimina", etichetta, None, "in Kit senza file: il file è stato tolto"))
            guardare.append(f"{etichetta}: in Kit c'era un invio senza file, tolto")
    return azioni, guardare


def invii_dem():
    """Tutti gli invii di Kit con l'etichetta delle mail straordinarie, pagina per pagina."""
    trovati, dopo = {}, None
    for _ in range(50):
        stato, corpo = nl.kit("GET", "/broadcasts?per_page=100" + (f"&after={dopo}" if dopo else ""))
        if stato != 200:
            raise RuntimeError(f"elenco degli invii di Kit non leggibile (HTTP {stato})")
        for b in corpo.get("broadcasts", []):
            if str(b.get("description") or "").startswith(ETICHETTA):
                trovati[b["description"]] = b
        pg = corpo.get("pagination") or {}
        if not pg.get("has_next_page") or not pg.get("end_cursor"):
            break
        dopo = pg["end_cursor"]
    return trovati


def dati_invio(m, programmata, modello, con_testata):
    oggetto, anteprima, corpo = componi(m, con_testata)
    d = {"subject": oggetto, "preview_text": anteprima, "content": corpo, "description": m.etichetta, "public": False,
         "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
         "send_at": m.invio.astimezone(timezone.utc).isoformat(timespec="seconds") if programmata else None}
    if modello:
        d["email_template_id"] = modello
    return d


def esegui_piano(azioni, grezzi):
    """Fa in Kit le azioni del piano. Torna le frasi da guardare (un'azione non riuscita è da guardare)."""
    male = []
    da_fare = [a for a in azioni if a[0] != "nulla"]
    modello, con_testata = nl.modello_edizione() if any(a[2] for a in da_fare) else (None, True)
    for tipo, etichetta, m, motivo in da_fare:
        b = grezzi.get(etichetta) or {}
        if tipo == "elimina":
            stato, _ = nl.kit("DELETE", f"/broadcasts/{b.get('id')}")
            ok = stato in (200, 204, 404)
        else:
            dati = dati_invio(m, tipo.endswith("programmata"), modello, con_testata)
            if tipo.startswith("crea"):
                stato, risposta = nl.kit("POST", "/broadcasts", dati)
                ok = stato in (200, 201)
            else:
                stato, risposta = nl.kit("PUT", f"/broadcasts/{b.get('id')}", dati)
                ok = stato in (200, 201)
                if not ok:  # se Kit non accetta la modifica: si toglie e si rifà (l'invio non è ancora partito)
                    nl.kit("DELETE", f"/broadcasts/{b.get('id')}")
                    stato, risposta = nl.kit("POST", "/broadcasts", dati)
                    ok = stato in (200, 201)
        print(f"  {'ok' if ok else 'NON RIUSCITO'}  {tipo:<20} {etichetta}  ({motivo}; HTTP {stato})")
        if not ok:
            male.append(f"{etichetta}: {tipo} non riuscito in Kit (HTTP {stato})")
    return male


# ------------------------------------------------------------------ comandi
def controlla(scrivi=False, cartella=CARTELLA, vista_file=VISTA):
    mail = leggi_tutte(cartella)
    regole_calendario(mail)
    errori = [f"{m.nome}: {x}" for m in mail for x in m.errori]
    avvisi = [f"{m.nome}: {x}" for m in mail for x in m.avvisi]
    print(f"Mail straordinarie: {len(mail)} file in {Path(cartella).relative_to(REPO) if Path(cartella).is_relative_to(REPO) else cartella}")
    for m in sorted(mail, key=lambda m: (m.invio is None, m.invio or datetime.min.replace(tzinfo=ROMA))):
        quando_ = f"{nl.GIORNI[m.invio.weekday()][:3].lower()} {m.invio:%d/%m/%Y %H:%M}" if m.invio else "data non valida"
        print(f"  {quando_:<22} {m['stato'] or '?':<10} {m['oggetto'][:60]}" + (f"  [ok {m['ok']}]" if m["ok"] else ""))
    for x in avvisi:
        print(f"  AVVISO  {x}")
    for x in errori:
        print(f"  ERRORE  {x}")
    if not errori:
        atteso = testo_vista(mail)
        if scrivi:
            Path(vista_file).parent.mkdir(parents=True, exist_ok=True)
            Path(vista_file).write_text(atteso, encoding="utf-8")
            print(f"  scritto {Path(vista_file).relative_to(REPO) if Path(vista_file).is_relative_to(REPO) else vista_file}")
        elif not Path(vista_file).exists() or Path(vista_file).read_text(encoding="utf-8") != atteso:
            errori.append("pannello/invii.json non è allineato ai file: lancia 'python3 redazione/dem.py salva'")
            print(f"  ERRORE  {errori[-1]}")
    print("DEM: " + ("OK" if not errori else f"{len(errori)} errori"))
    return mail, errori


def anteprima(nome):
    mail = {m.nome: m for m in leggi_tutte()}
    nome = Path(nome).stem
    if nome not in mail:
        sys.exit(f"ERRORE: nessuna mail {nome} in redazione/dem/")
    m = mail[nome]
    oggetto, pre, corpo = componi(m)
    ANTEPRIME.mkdir(exist_ok=True)
    out = ANTEPRIME / f"{nome}.html"
    testa = (f'<div style="font:13px/1.5 Arial,sans-serif;color:#5E5A55;max-width:600px;margin:12px auto">'
             f'<b>Oggetto:</b> {e(oggetto)}<br><b>Anteprima:</b> {e(pre)}<br><b>Invio:</b> {m.invio:%d/%m/%Y %H:%M} - <b>stato:</b> {e(m["stato"])}</div>')
    out.write_text(nl.anteprima_locale(corpo).replace("<body style=\"margin:0;padding:0;background:#FBFAF8\">",
                                                     "<body style=\"margin:0;padding:0;background:#FBFAF8\">" + testa, 1), encoding="utf-8")
    print(f"Anteprima: {out.relative_to(REPO)}" + ("" if not m.errori else "  (attenzione: " + "; ".join(m.errori) + ")"))


def allinea(esegui):
    mail, errori = controlla()
    if errori:
        print("Kit non toccato: prima vanno corretti gli errori dei file.")
        return 1
    ora = datetime.now(timezone.utc)
    grezzi = invii_dem()
    kit = {k: stato_kit(b, ora) for k, b in grezzi.items()}
    azioni, guardare = piano(mail, kit, ora)
    print(f"\nKit: {len(grezzi)} invii delle mail straordinarie. Piano:")
    for tipo, etichetta, m, motivo in azioni:
        print(f"  {tipo:<20} {etichetta}  ({motivo})")
    if esegui:
        print("\nEsecuzione:")
        guardare += esegui_piano(azioni, grezzi)
    for x in guardare:
        print(f"DA GUARDARE: {x}")
    return 1 if guardare else 0


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else "controlla"
    if modo == "controlla":
        sys.exit(1 if controlla()[1] else 0)
    if modo == "salva":
        sys.exit(1 if controlla(scrivi=True)[1] else 0)
    if modo == "anteprima" and len(sys.argv) > 2:
        return anteprima(sys.argv[2])
    if modo in ("piano", "sincronizza"):
        sys.exit(allinea(esegui=modo == "sincronizza"))
    sys.exit(__doc__)


if __name__ == "__main__":
    main()
