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
import hashlib
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
UNA_AL_MESE = True        # al massimo una mail per mese di calendario (le annullate non contano): lo promette la privacy
MIN_GIORNI = 14           # e comunque almeno 14 giorni tra due mail (niente 31 gennaio e 1 febbraio)
ORA_DA, ORA_A = 8, 21     # si spedisce tra le 8:00 e le 20:59
FINESTRA = (7, 11)        # nei giorni di uscita, dalle 7:00 alle 10:59 c'è l'edizione: niente mail straordinarie
PROMEMORIA = 10           # giorni prima dell'invio in cui una bozza non approvata diventa da guardare
MARGINE_MIN = 15          # sotto questi minuti dall'invio una mail non si crea né si cambia più
MARGINE_RITIRO = 2        # sotto questi minuti un invio non si toglie più (annullarlo prima è sempre possibile)
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

    @property
    def autorizzata(self):
        """Il file autorizza un invio: approvata, con l'ok scritto bene, data leggibile e nome valido. Nel dubbio no."""
        return bool(self["stato"] == "approvata" and re.match(r"^\S.* \d{4}-\d{2}-\d{2}$", self["ok"]) and self.invio
                    and NOME_FILE.match(self.percorso.name))

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
    """Le regole tra mail diverse (le annullate non contano): una per mese di calendario, almeno MIN_GIORNI giorni tra due."""
    vive = sorted([m for m in mail if m.invio and m["stato"] != "annullata"], key=lambda m: m.invio)
    for a, b in zip(vive, vive[1:]):
        gap = (b.invio.date() - a.invio.date()).days
        if UNA_AL_MESE and (a.invio.year, a.invio.month) == (b.invio.year, b.invio.month):
            b.errori.append(f"stesso mese di {a.nome}: al massimo una mail straordinaria al mese")
        elif gap < MIN_GIORNI:
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
    righe = [{"nome": m.nome, "invio": m.invio.strftime("%Y-%m-%dT%H:%M"),
              "utc": m.invio.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "stato": m["stato"], "oggetto": m["oggetto"],
              "ok": m["ok"], "sondaggio": any(b[0] == "sondaggio" for b in m.blocchi), "parole": m.parole}
             for m in sorted(mail, key=lambda m: m.invio) if m.invio]
    return {"regole": {"una_al_mese": UNA_AL_MESE, "min_giorni": MIN_GIORNI, "promemoria_giorni": PROMEMORIA, "ore": f"{ORA_DA}:00-{ORA_A - 1}:59",
                       "finestra_edizione": f"{FINESTRA[0]}:00-{FINESTRA[1] - 1}:59"}, "invii": righe}


def testo_vista(mail):
    return json.dumps(vista(mail), ensure_ascii=False, indent=1) + "\n"


# ------------------------------------------------------------------ allineamento con Kit
# Il principio: in Kit non si modifica mai un invio sul posto. Ogni cambiamento è "togli, verifica che sia tolto, poi crea
# e verifica che Kit abbia registrato quello che volevamo". Se il togliere non riesce non si crea nulla: due invii della
# stessa mail non possono nascere. L'impronta del contenuto sta nella description ("etichetta #impronta"): un invio
# uguale al file non si tocca.
def quando(s):
    if not s:
        return None
    try:
        t = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def stesso_oggetto(kit, nostro):
    """L'oggetto in Kit è il nostro? Tollerante a codifiche HTML, apostrofi tipografici e spazi: Kit può riscriverli.
    Se Kit non lo restituisce, conta l'impronta."""
    if not kit:
        return True
    pulisci = lambda t: re.sub(r"\s+", " ", html.unescape(str(t)).replace("\u2019", "'").replace("\u2018", "'")).strip()
    return pulisci(kit) == pulisci(nostro)


def etichetta_di(descrizione):
    return str(descrizione or "").split(" ")[0]


def impronta_di(descrizione):
    parti = str(descrizione or "").split(" #")
    return parti[1].strip() if len(parti) > 1 else ""


def stato_kit(b, ora):
    """Da un invio di Kit: id, send_at, impronta, partito. Partito = spedito, in spedizione o con l'ora già passata:
    l'ora vince sullo stato dichiarato, così un invio "scheduled" in partenza non si tocca."""
    s = str(b.get("status") or "").lower()
    t = quando(b.get("send_at"))
    partito = s in ("completed", "sent", "sending", "processing") or bool(t and t <= ora)
    return {"id": b.get("id"), "send_at": t, "impronta": impronta_di(b.get("description")), "partito": partito,
            "oggetto": b.get("subject")}


def dati_invio(m, programmata, modello):
    """Ciò che si manda a Kit per la mail m. Una bozza non ha mai una data di invio."""
    oggetto, anteprima, corpo = componi(m, con_testata=True)
    d = {"subject": oggetto, "preview_text": anteprima, "content": corpo, "public": False,
         "send_at": m.invio.astimezone(timezone.utc).isoformat(timespec="seconds") if programmata else None,
         "email_template_id": modello}
    firma = json.dumps([d["subject"], d["preview_text"], d["content"], d["send_at"], modello], ensure_ascii=False)
    d["description"] = f"{m.etichetta} #{hashlib.sha256(firma.encode('utf-8')).hexdigest()[:12]}"
    return d


def piano(mail, kit, ora, modello, solo_ritiri=False):
    """Che cosa fare in Kit, senza farlo.
    mail: tutte le mail lette (anche quelle con errori); kit: {etichetta: [stato_kit, ...]}; ora: adesso (UTC);
    modello: id del modello "Gommberg cornice"; solo_ritiri: True se qualche file ha errori o il modello manca, e allora
    si tolgono gli invii da ritirare ma non si crea né si cambia nulla.
    Torna (azioni, guardare, note). azioni = [(tipo, etichetta, mail o None, motivo, id o None)] con tipo in
    crea-bozza, crea-programmata, rifai-bozza, rifai-programmata (togli l'id, poi crea), elimina, nulla.
    guardare = problemi veri, per Paolo (fanno fallire il giro); note = da leggere, non fanno fallire."""
    azioni, guardare, note = [], [], []
    modifica, ritiro = timedelta(minutes=MARGINE_MIN), timedelta(minutes=MARGINE_RITIRO)
    per_etichetta = {m.etichetta: m for m in mail}
    for et in sorted(set(per_etichetta) | set(kit)):
        m, lista = per_etichetta.get(et), kit.get(et, [])
        vive = sorted([k for k in lista if not k["partito"]], key=lambda k: (k["send_at"] is None, k["send_at"] or ora))
        partita = any(k["partito"] for k in lista)
        valida = bool(m and not m.errori and m.invio and m["stato"] in STATI)
        voluta = (m.invio.astimezone(timezone.utc) if valida and m["stato"] == "approvata" else None)

        # 1. un invio che sta partendo non si tocca più
        if any(k["send_at"] and k["send_at"] - ora <= ritiro for k in vive):
            azioni.append(("nulla", et, m, f"parte tra meno di {MARGINE_RITIRO} minuti: non si tocca", None))
            normale = voluta and len(vive) == 1 and abs((vive[0]["send_at"] - voluta).total_seconds()) < 60
            if not normale:
                guardare.append(f"{et}: in Kit sta per partire e il file non la vuole così: da fermare a mano in Kit, subito")
            continue
        # 2. già partita: ogni copia viva con la stessa etichetta (per esempio un "Duplicate" fatto a mano in Kit) si toglie
        if partita:
            for k in vive:
                azioni.append(("elimina", et, m, "copia di una mail già partita", k["id"]))
                guardare.append(f"{et}: in Kit c'era una copia di una mail già partita, tolta")
            if not vive:
                azioni.append(("nulla", et, m, "già partita", None))
            if m and m["stato"] == "annullata":
                note.append(f"{et}: annullata, ma era già partita")
            continue
        # 3. doppioni in Kit (non dovrebbero esistere): se ne tiene uno, gli altri si tolgono
        for k in vive[1:]:
            azioni.append(("elimina", et, m, "doppione in Kit", k["id"]))
            guardare.append(f"{et}: in Kit c'erano due invii della stessa mail, il doppione è stato tolto")
        k = vive[0] if vive else None
        # 4. file tolto, annullato, illeggibile o senza un ok valido: un invio programmato si ritira (nel dubbio si ritira)
        if m is None:
            if k:
                azioni.append(("elimina", et, None, "file tolto", k["id"]))
                note.append(f"{et}: file tolto, invio tolto da Kit")
            continue
        if m["stato"] == "annullata":
            azioni.append(("elimina", et, m, "annullata", k["id"]) if k else ("nulla", et, m, "annullata", None))
            continue
        if m["stato"] != "bozza" and not m.autorizzata:
            if k and k["send_at"]:
                azioni.append(("elimina", et, m, "il file non autorizza l'invio (stato, ok o data): ritirata", k["id"]))
            else:
                azioni.append(("nulla", et, m, "file da correggere: Kit lasciato com'è", None))
            continue
        if not m.invio:  # una bozza con la data illeggibile
            azioni.append(("elimina", et, m, "bozza con la data illeggibile: ritirata", k["id"]) if k and k["send_at"]
                          else ("nulla", et, m, "file da correggere: Kit lasciato com'è", None))
            continue
        st, inv = m["stato"], m.invio.astimezone(timezone.utc)
        # 5. bozza: in Kit senza data, oppure niente
        if st == "bozza":
            if k and k["send_at"]:  # era programmata: si ritira subito, anche con errori nei file
                if solo_ritiri or inv <= ora:
                    azioni.append(("elimina", et, m, "tornata in bozza: invio ritirato", k["id"]))
                else:
                    azioni.append(("rifai-bozza", et, m, "tornata in bozza: invio ritirato, resta in Kit senza data", k["id"]))
            elif inv <= ora:
                azioni.append(("nulla", et, m, "data passata, mai approvata: non è partita", None))
            elif solo_ritiri:
                azioni.append(("nulla", et, m, "bozza (Kit non aggiornato: ci sono errori da correggere)", None))
            else:
                atteso = dati_invio(m, False, modello)
                if not k:
                    azioni.append(("crea-bozza", et, m, "bozza: in Kit senza data, da approvare", None))
                elif impronta_di(atteso["description"]) != k["impronta"] or not stesso_oggetto(k.get("oggetto"), atteso["subject"]):
                    azioni.append(("rifai-bozza", et, m, "bozza cambiata", k["id"]))
                else:
                    azioni.append(("nulla", et, m, "bozza, uguale in Kit", None))
            if ora < inv <= ora + timedelta(days=PROMEMORIA):
                guardare.append(f"{et}: è ancora in bozza e parte il {m.invio:%d/%m alle %H:%M} solo con l'ok di Paolo")
            continue
        # 6. approvata
        if not valida:
            azioni.append(("nulla", et, m, "approvata ma con errori nel file: Kit lasciato com'è", None))
            continue
        if inv - ora < modifica:
            if not (k and k["send_at"]):
                azioni.append(("nulla", et, m, "non partita", None))
                if ora - inv <= timedelta(days=2):
                    guardare.append(f"{et}: approvata ma non partita (invio del {m.invio:%d/%m alle %H:%M}, in Kit "
                                    + ("in bozza" if k else "assente") + "): scegliere una nuova data")
            else:  # programmata e in partenza: si lascia andare; se il file è cambiato, è tardi per seguirlo
                azioni.append(("nulla", et, m, f"parte tra meno di {MARGINE_MIN} minuti: non si cambia", None))
                uguale = (abs((k["send_at"] - inv).total_seconds()) < 60
                          and (modello is None or impronta_di(dati_invio(m, True, modello)["description"]) == k["impronta"]))
                if not uguale:
                    guardare.append(f"{et}: cambiata a meno di {MARGINE_MIN} minuti dalla partenza (in Kit alle "
                                    f"{k['send_at'].astimezone(ROMA):%H:%M}): parte la versione di prima, salvo fermarla a mano in Kit")
            continue
        if solo_ritiri:
            azioni.append(("nulla", et, m, "approvata (Kit non aggiornato: ci sono errori da correggere)", None))
            continue
        atteso = dati_invio(m, True, modello)
        if not k:
            azioni.append(("crea-programmata", et, m, f"programmata per il {m.invio:%d/%m alle %H:%M}", None))
        elif (impronta_di(atteso["description"]) != k["impronta"] or not k["send_at"]
              or abs((k["send_at"] - inv).total_seconds()) >= 60 or not stesso_oggetto(k.get("oggetto"), atteso["subject"])):
            azioni.append(("rifai-programmata", et, m, f"cambiata: riprogrammata per il {m.invio:%d/%m alle %H:%M}", k["id"]))
        else:
            azioni.append(("nulla", et, m, f"programmata per il {m.invio:%d/%m alle %H:%M}, uguale in Kit", None))
    return azioni, guardare, note


def invii_dem():
    """Gli invii di Kit con l'etichetta delle mail straordinarie, pagina per pagina: {etichetta: [invii]}."""
    trovati = {}
    try:
        invii = nl.leggi_invii(letture=1, massimo=50)       # come prima: nessuna rilettura, nel dubbio si ritira
    except nl.ElencoNonLeggibile as e:
        if e.troppo_lungo:
            raise RuntimeError("elenco degli invii di Kit troppo lungo (oltre 50 pagine): fermo per prudenza")
        raise RuntimeError(f"elenco degli invii di Kit non leggibile (HTTP {e.stato})")
    for b in invii:
        et = etichetta_di(b.get("description"))
        if et.startswith(ETICHETTA):
            trovati.setdefault(et, []).append(b)
    return trovati


def modello_cornice():
    """L'id del modello "Gommberg cornice" in Kit, o None: senza la cornice non si crea nulla."""
    stato, corpo = nl.kit("GET", "/email_templates")
    for t in corpo.get("email_templates", []) if stato == 200 else []:
        if (t.get("name") or "").strip().lower() == nl.CORNICE.lower():
            return t.get("id")
    return None


def esegui_piano(azioni, modello):
    """Fa in Kit le azioni del piano e verifica ogni passo. Torna le frasi da guardare."""
    male = []

    def togli(i):
        stato, _ = nl.kit("DELETE", f"/broadcasts/{i}")
        return stato in (200, 204, 404)

    def crea(m, programmata):
        dati = dati_invio(m, programmata, modello)
        stato, risposta = nl.kit("POST", "/broadcasts", dati)
        b = (risposta or {}).get("broadcast") or {}
        if stato not in (200, 201) or not b.get("id"):
            return f"Kit non ha accettato la mail (HTTP {stato})"
        t, voluto = quando(b.get("send_at")), quando(dati["send_at"])
        giusto = (t is None) if voluto is None else bool(t and abs((t - voluto).total_seconds()) < 60)
        if not giusto:  # Kit non ha registrato la data voluta: l'invio si toglie subito
            tolto = togli(b["id"])
            return (f"Kit ha registrato una data di invio diversa ({b.get('send_at')}): invio "
                    + ("tolto" if tolto else "NON tolto, da togliere a mano in Kit"))
        return ""

    for tipo, et, m, motivo, i in [a for a in azioni if a[0] != "nulla"]:
        if tipo == "elimina":
            esito = "" if togli(i) else "Kit non ha tolto l'invio: da togliere a mano"
        elif tipo.startswith("rifai"):
            esito = crea(m, tipo.endswith("programmata")) if togli(i) else "Kit non ha tolto l'invio vecchio: niente di nuovo creato"
        else:
            esito = crea(m, tipo.endswith("programmata"))
        print(f"  {'ok' if not esito else 'NON RIUSCITO'}  {tipo:<18} {et}  ({motivo})" + (f": {esito}" if esito else ""))
        if esito:
            male.append(f"{et}: {tipo} - {esito}")
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
    guardare = list(errori)
    grezzi = invii_dem()
    modello = modello_cornice()
    ora = datetime.now(timezone.utc)  # dopo le letture di Kit: i margini si misurano sull'ora vera
    kit = {et: [stato_kit(b, ora) for b in lista] for et, lista in grezzi.items()}
    if not modello:
        guardare.append(f'in Kit manca il modello "{nl.CORNICE}": nessuna mail creata o cambiata finché non torna')
    solo_ritiri = bool(errori) or not modello
    if solo_ritiri:
        print("\nSolo ritiri: si tolgono gli invii annullati o tornati in bozza, non si crea né si cambia nulla.")
    azioni, da_guardare, note = piano(mail, kit, ora, modello, solo_ritiri)
    guardare += da_guardare
    print(f"\nKit: {sum(len(v) for v in grezzi.values())} invii delle mail straordinarie. Piano:")
    for tipo, et, m, motivo, i in azioni:
        print(f"  {tipo:<18} {et}  ({motivo})")
    if esegui:
        print("\nEsecuzione:")
        guardare += esegui_piano(azioni, modello)
    for x in note:
        print(f"NOTA: {x}")
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
