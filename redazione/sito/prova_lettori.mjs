// Collaudo del servizio dei lettori (redazione/sito/lettori.js) senza Cloudflare e senza rete: il codice vero, con un
// database D1 finto sopra SQLite di Node (d1_finto.mjs, Node 22.5 o più) e un'edizione finta al posto dei file statici.
// Lo lancia redazione/collaudo.py; da solo: node redazione/sito/prova_lettori.mjs. Esce con 1 al primo errore.
import { readFileSync } from "node:fs";
import { d1 } from "./d1_finto.mjs";
import worker, { controllaTesto, controllaNome, chiaveNome, pulisciNome, pulisciTesto, sitoDi, LIMITI, NOMI_UNICI } from "./lettori.js";
import * as L_ from "./lettori.js";
import servizio from "./servizio.js";
import { AREA, COOKIE, SPIA, usaPrivato, uguali, improntaPassword, verificaImpronta, dispositivo } from "./redazione.js";

// ------------------------------------------------------------- orologio finto, edizioni finte
let adesso = Date.parse("2026-11-23T09:00:00Z");
Date.now = () => adesso;
const avanti = (s) => { adesso += s * 1000; };
const EDIZIONI = {
  30: { numero: 30, data: "2026-11-20" },
  31: { numero: 31, data: "2026-11-23" },   // la più recente: il sentiment si vota qui
};
const PUBBLICI_RED = { "/redazione/glossario.json": "[1]", "/redazione/glossario_sito.json": "[2]", "/redazione/meccanismi.json": "[3]", "/redazione/scommessa/pagella.json": "[4]" };
const env = {
  DB: d1(),
  ASSETS: { fetch: async (req) => {
    const u = new URL(req.url), m = /^\/e\/(\d{3})\.json$/.exec(u.pathname);
    if (m && EDIZIONI[+m[1]]) return new Response(JSON.stringify(EDIZIONI[+m[1]]), { headers: { "content-type": "application/json" } });
    if (u.pathname === "/dati/recenti.json") return new Response(JSON.stringify({ totale: 31, edizioni: [{ numero: 31 }, { numero: 30 }] }));
    // sotto /redazione/ ci sono anche file pubblici che il sito legge (costruisci.py, LETTI): il Worker li deve lasciar passare
    if (u.pathname.startsWith("/redazione/")) return PUBBLICI_RED[u.pathname] ? new Response(PUBBLICI_RED[u.pathname], { status: 200 }) : new Response("pagina 404 del sito", { status: 404 });
    return new Response(m ? "non trovata" : "statico", { status: m ? 404 : 200 });
  } },
};

let ok = 0, ko = 0;
function verifica(nome, cond, dettaglio) {
  if (cond) { ok++; return; }
  ko++; console.log("NO  " + nome + (dettaglio !== undefined ? ": " + JSON.stringify(dettaglio) : ""));
}
const BASE = "https://gommberg.com";
async function chiama(metodo, percorso, { corpo, lettore = "lettore-aaaaaaaaaaaaaaaa", ip = "1.1.1.1", origine = BASE, base = BASE } = {}) {
  const h = { "x-lettore": lettore, "cf-connecting-ip": ip };
  if (origine) h.origin = origine;
  if (corpo) h["content-type"] = "application/json";
  const r = await worker.fetch(new Request(base + percorso, { method: metodo, headers: h, body: corpo ? JSON.stringify(corpo) : undefined }), env);
  let j = null; try { j = await r.clone().json(); } catch (e) { j = await r.text(); }
  return { s: r.status, j };
}

// ------------------------------------------------------------- 1. lettura e file statici
let r = await chiama("GET", "/index.html");
verifica("le pagine non /api/ vanno ai file statici", r.s === 200 && r.j === "statico", r);
r = await chiama("GET", "/api/lettori/030");
verifica("lettura dell'edizione", r.s === 200 && Array.isArray(r.j.commenti) && /^\d{10}\.[0-9a-f]{24}$/.test(r.j.gettone), r);
verifica("sentiment chiuso su un'edizione passata", r.j.voto && r.j.voto.aperto === false, r.j.voto);
const g0 = r.j.gettone;
r = await chiama("GET", "/api/lettori/099");
verifica("edizione inesistente: 404", r.s === 404, r);
r = await chiama("GET", "/api/altro");
verifica("indirizzo sconosciuto: 404", r.s === 404, r);

// ------------------------------------------------------------- 2. difese
{
  let pezzi = 0;
  const flussoL = new ReadableStream({ pull(ctrl) { pezzi++; ctrl.enqueue(new TextEncoder().encode("x".repeat(4096))); } });
  const rl = await worker.fetch(new Request(BASE + "/api/lettori/031/commenti", { method: "POST", duplex: "half", body: flussoL,
    headers: { origin: BASE, "content-type": "application/json", "content-length": "20000000", "x-lettore": "lettore-aaaaaaaaaaaaaaaa", "cf-connecting-ip": "1.1.1.1" } }), env);
  verifica("lettori: un corpo dichiarato di 20 MB si rifiuta con 413 prima di leggerlo", rl.status === 413 && pezzi <= 2, [rl.status, pezzi]);
}
const testo = (x) => ({ nome: "Giulia T.", testo: x, gettone: g0 });
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: testo("Troppo presto") });
verifica("gettone di meno di 3 secondi: rifiutato", r.s === 400, r);
avanti(5);
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: testo("Senza origine"), origine: null });
verifica("senza origine: rifiutato", r.s === 403, r);
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: testo("Da un altro sito"), origine: "https://altro.example" });
verifica("da un altro sito: rifiutato", r.s === 403, r);
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: testo("Stesso nome, schema diverso"), origine: "http://gommberg.com" });
verifica("stesso nome di sito con http: rifiutato (l'origine si confronta intera)", r.s === 403, r);
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: testo("Lettore finto"), lettore: "x" });
verifica("lettore non riconoscibile: rifiutato", r.s === 400, r);
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: { ...testo("Gettone falso"), gettone: "1795000000.000000000000000000000000" } });
verifica("gettone falso: rifiutato", r.s === 400, r);
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: { ...testo("Sono un programma"), sito: "https://spam.example" } });
verifica("campo trappola: risposta finta, nulla salvato", r.s === 200 && r.j.ok === true, r);
for (const [nome, atteso] of [["Redazione", "riservato"], ["Gommberg fan", "riservato"], ["P.Gommellini", "riservato"], ["G", "caratteri"], ["x".repeat(25), "caratteri"]]) {
  r = await chiama("POST", "/api/lettori/031/commenti", { corpo: { nome, testo: "Ciao", gettone: g0 } });
  verifica("nome " + JSON.stringify(nome) + " rifiutato", r.s === 400 && r.j.errore.includes(atteso), r);
}
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: testo("   \n  ") });
verifica("testo vuoto: rifiutato", r.s === 400, r);
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: testo("a".repeat(LIMITI.testo + 1)) });
verifica("testo troppo lungo: rifiutato", r.s === 400, r);
verifica("tre link: rifiutato", !!controllaTesto("vedi https://a.it e www.b.com e c.net/x"), null);
verifica("due link: ammesso", !controllaTesto("vedi https://a.it e www.b.com"), null);
verifica("testo ripulito", pulisciTesto(" a​\r\n\n\n\nb \u0007 ") === "a\n\nb", pulisciTesto(" a​\r\n\n\n\nb \u0007 "));
r = await chiama("GET", "/api/lettori/031");
verifica("nessun commento salvato dai tentativi rifiutati", r.j.commenti.length === 0, r.j.commenti);

// ------------------------------------------------------------- 3. commenti e risposte
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: testo("Sei sedute in rosso: oggi scende.\n\n\n\nSecondo me.") });
verifica("commento pubblicato subito", r.s === 201 && r.j.commento.id && r.j.commento.mio === true && r.j.commento.testo === "Sei sedute in rosso: oggi scende.\n\nSecondo me.", r);
const c1 = r.j.commento.id;
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: testo("Sei sedute in rosso: oggi scende.\n\nSecondo me.") });
verifica("stesso commento due volte: rifiutato", r.s === 429, r);
const B = { lettore: "lettore-bbbbbbbbbbbbbbbb", ip: "2.2.2.2" };
r = await chiama("POST", "/api/lettori/031/commenti", { ...B, corpo: { nome: "Luca R.", testo: "Non sono d'accordo", padre: c1, gettone: g0 } });
verifica("risposta", r.s === 201 && r.j.commento.padre === c1, r);
const c2 = r.j.commento.id;
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: { ...testo("@Luca R. perché?"), padre: c2 } });
verifica("risposta a una risposta: va sotto il commento principale (un livello)", r.s === 201 && r.j.commento.padre === c1, r);
r = await chiama("POST", "/api/lettori/030/commenti", { corpo: { ...testo("Altra edizione"), padre: c1 } });
verifica("risposta a un commento di un'altra edizione: rifiutata", r.s === 404, r);
r = await chiama("GET", "/api/lettori/031", B);
verifica("lettura: tre commenti, il mio riconosciuto", r.j.commenti.length === 3 && r.j.commenti.filter((x) => x.mio).length === 1 && r.j.commenti[1].mio, r.j.commenti);
verifica("lettura: nessun dato tecnico esce", !JSON.stringify(r.j).match(/"(ip|autore|segnalazioni)"/), r.j);

// ------------------------------------------------------------- 4. like
r = await chiama("POST", "/api/lettori/commenti/" + c1 + "/piace", { ...B, corpo: { gettone: g0 } });
verifica("like", r.s === 200 && r.j.piace === 1 && r.j.piaciuto === true, r);
r = await chiama("POST", "/api/lettori/commenti/" + c1 + "/piace", { ...B, corpo: { gettone: g0 } });
verifica("like tolto con il secondo tocco", r.j.piace === 0 && r.j.piaciuto === false, r);
await chiama("POST", "/api/lettori/commenti/" + c1 + "/piace", { ...B, corpo: { gettone: g0 } });
r = await chiama("GET", "/api/lettori/031", B);
verifica("like ricordato al lettore", r.j.commenti.find((x) => x.id === c1).piaciuto === true && r.j.commenti.find((x) => x.id === c1).piace === 1, r.j.commenti);

// ------------------------------------------------------------- 5. sentiment Toro/Orso (si vota sull'edizione più recente, tutto il giorno)
r = await chiama("POST", "/api/lettori/031/voto", { corpo: { voto: "toro", gettone: g0 } });
verifica("voto Toro", r.s === 200 && r.j.voto.toro === 1 && r.j.voto.mio === "toro" && r.j.voto.aperto, r);
r = await chiama("POST", "/api/lettori/031/voto", { corpo: { voto: "orso", gettone: g0 } });
verifica("cambio voto: Orso, un voto solo", r.j.voto.toro === 0 && r.j.voto.orso === 1 && r.j.voto.mio === "orso", r);
await chiama("POST", "/api/lettori/031/voto", { ...B, corpo: { voto: "toro", gettone: g0 } });
r = await chiama("GET", "/api/lettori/031");
verifica("targhetta del sentiment accanto al nome", r.j.commenti.find((x) => x.id === c1).voto === "orso" && r.j.commenti.find((x) => x.id === c2).voto === "toro", r.j.commenti);
verifica("lettori di oggi: chi ha votato o scritto, una volta sola", r.j.lettori === 2, r.j.lettori);
r = await chiama("POST", "/api/lettori/031/voto", { corpo: { voto: "lupo", gettone: g0 } });
verifica("voto non valido", r.s === 400, r);
r = await chiama("POST", "/api/lettori/030/voto", { corpo: { voto: "toro", gettone: g0 } });
verifica("edizione passata: niente voto", r.s === 409, r);
adesso = Date.parse("2026-11-23T22:31:00Z");
const g1 = (await chiama("GET", "/api/lettori/031")).j.gettone; avanti(5);
r = await chiama("POST", "/api/lettori/031/voto", { corpo: { voto: "orso", gettone: g1 } });
verifica("la sera il sentiment è ancora aperto", r.s === 200 && r.j.voto.aperto, r);
r = await chiama("GET", "/api/lettori/031");
verifica("i risultati restano", r.j.voto.toro === 1 && r.j.voto.orso === 1, r.j.voto);

// ------------------------------------------------------------- 6. segnalazioni
r = await chiama("POST", "/api/lettori/commenti/" + c1 + "/segnala", { corpo: { gettone: g1 } });
verifica("non si segnala un proprio commento", r.s === 400, r);
for (const [i, ip] of [["c", "3.3.3.3"], ["d", "3.3.3.3"], ["e", "4.4.4.4"]]) {
  r = await chiama("POST", "/api/lettori/commenti/" + c2 + "/segnala", { lettore: "lettore-" + i.repeat(16), ip, corpo: { gettone: g1 } });
}
r = await chiama("GET", "/api/lettori/031");
verifica("tre segnalazioni da due reti: il commento resta", r.j.commenti.some((x) => x.id === c2), r.j.commenti);
r = await chiama("POST", "/api/lettori/commenti/" + c2 + "/segnala", { lettore: "lettore-ffffffffffffffff", ip: "5.5.5.5", corpo: { gettone: g1 } });
verifica("terza rete: nascosto", r.j.nascosto === true, r);
r = await chiama("GET", "/api/lettori/031");
verifica("il commento nascosto non esce più", !r.j.commenti.some((x) => x.id === c2), r.j.commenti);

// ------------------------------------------------------------- 7. anteprime separate
r = await chiama("GET", "/api/lettori/031", { base: "https://anteprima-g13-gommberg.esempio.workers.dev", origine: null });
verifica("l'anteprima non vede i commenti di gommberg.com", r.s === 200 && r.j.commenti.length === 0, r.j);
r = await chiama("GET", "/api/lettori/030", { base: "https://anteprima-g13-gommberg.esempio.workers.dev", origine: null });
verifica("nell'anteprima il sentiment si vota anche sulle edizioni passate", r.j.voto && r.j.voto.aperto === true, r.j.voto);

// ------------------------------------------------------------- 8. limiti di frequenza
const C = { lettore: "lettore-gggggggggggggggg", ip: "6.6.6.6" };
let ultimo = 0;
for (let i = 0; i < LIMITI.commenti_10min + 1; i++) ultimo = (await chiama("POST", "/api/lettori/031/commenti", { ...C, corpo: { nome: "Veloce", testo: "Commento " + i, gettone: g1 } })).s;
verifica("troppi commenti in 10 minuti: fermato", ultimo === 429, ultimo);
avanti(601);
r = await chiama("POST", "/api/lettori/031/commenti", { ...C, corpo: { nome: "Veloce", testo: "Dopo la pausa", gettone: g1 } });
verifica("dopo 10 minuti si riscrive", r.s === 201, r);

// ------------------------------------------------------------- 9. impronte IP cancellate dopo 30 giorni
// la pulizia è certa: la fa la prima richiesta di ogni giorno, anche una semplice lettura
// (i commenti invecchiati passano a un'edizione di ottobre: sulla 031, che è del 23/11, una data precedente sarebbe un resto
// di un'edizione di test e verrebbe cancellata, vedi in fondo)
env.DB._db.exec("UPDATE commenti SET creato = '2026-10-01T00:00:00Z', ed = 20");
await chiama("GET", "/api/lettori/031");
verifica("nello stesso giorno la pulizia non si ripete", env.DB._db.prepare("SELECT COUNT(*) AS n FROM commenti WHERE ip IS NOT NULL AND creato < '2026-10-24'").get().n > 0, null);
avanti(86400);
await chiama("GET", "/api/lettori/031");
const restano = env.DB._db.prepare("SELECT COUNT(*) AS n FROM commenti WHERE ip IS NOT NULL AND creato < '2026-10-24'").get().n;
verifica("impronte IP oltre i 30 giorni cancellate alla prima richiesta del giorno dopo", restano === 0, restano);

// ------------------------------------------------------------- 10. nomi unici: un nome resta di chi l'ha usato per primo
verifica("l'interruttore dei nomi unici è acceso", NOMI_UNICI === true, NOMI_UNICI);
verifica("stessa chiave per maiuscole, accenti, spazi e punteggiatura", ["luca r", "LÙCA_R", "Luca  R.", "Luca R 🚀", "Ｌｕｃａ Ｒ"].every((x) => chiaveNome(x) === chiaveNome("Luca R.")), ["luca r", "LÙCA_R", "Luca  R.", "Luca R 🚀", "Ｌｕｃａ Ｒ"].map(chiaveNome));
verifica("zero e uno non fanno un nome diverso", chiaveNome("T0ro 1ungo") === chiaveNome("Toro lungo"), chiaveNome("T0ro 1ungo"));
verifica("lettere di un altro alfabeto: rifiutate", !!controllaNome("Lucа R."), controllaNome("Lucа R."));
// trovati dal collaudo indipendente del 22/11: nomi uguali all'occhio, nome riservato aggirato, nomi che sporcano la pagina
for (const [a, b] of [["GiuIia T.", "Giulia T."], ["Giu1ia T.", "Giulia T."], ["Giu!ia T.", "Giulia T."], ["Marnmola", "Mammola"], ["VValter", "Walter"], ["WaIter", "Walter"], ["T0ro sedut0", "Toro seduto"], ["Fabl0", "Fabio"]])
  verifica("uguali all'occhio, stessa chiave: " + a + " e " + b, chiaveNome(a) === chiaveNome(b), [chiaveNome(a), chiaveNome(b)]);
for (const x of ["G\u0131ulia T.", "Giu\u01c0ia T.", "\u0261iulia T.", "Giu|ia T.", "Giulia T. \u25b2 Toro", "T\u0ae6r\u0ae6 sedut\u0ae6", "T\u1d0fr\u1d0f seduto", "T\u00f8ro seduto", "Mammo\u0142a", "Fa\u0185io", "Cesare \u0667\u0667", "Luca \ud83d\ude80", "ab" + "\u0301".repeat(20), "a\ud800b"])
  verifica("carattere non ammesso nel nome: " + JSON.stringify(x), /simboli/.test(controllaNome(pulisciNome(x))), controllaNome(pulisciNome(x)));
for (const x of ["Redaz1one", "Redaz!one", "Redazlone", "Gornmberg", "G0mmberg td", "Adm1n", "Arnministratore", "Paolo Gomme11ini", "Redattore", "La Direzione", "M0derat0re", "Staff"])
  verifica("nome riservato anche travestito: " + x, /riservato/.test(controllaNome(x)), controllaNome(x));
for (const x of ["Niccolò 2000", "L'avevo detto", "Materasso & Co.", "Bolla? Quale bolla", "Lettore delle 9:45", "Elia", "Ilaria B.", "Zio col BTP"])
  verifica("nome normale ammesso: " + x, !controllaNome(x), controllaNome(x));
verifica("caratteri invisibili tolti dal nome", pulisciNome("Lu\u00adca\u2060 \ufe0fR.") === "Luca R.", pulisciNome("Lu\u00adca\u2060 \ufe0fR."));
verifica("gommberg.com con il punto finale è il sito vero", sitoDi(new URL("https://gommberg.com./")) === "gommberg" && sitoDi(new URL("https://x.workers.dev/")) === "prova", null);
verifica("link con estensioni meno comuni contati", !!controllaTesto("vedi t.co/x discord.gg/y bit.do/z"), null);
verifica("nome di soli simboli: rifiutato", !!controllaNome("🚀🚀🚀"), controllaNome("🚀🚀🚀"));
verifica("nome riservato scritto con lo zero: rifiutato", !!controllaNome("G0mmberg"), controllaNome("G0mmberg"));
verifica("nome con accenti e numeri: ammesso", !controllaNome("Niccolò 2000"), controllaNome("Niccolò 2000"));
const g2 = (await chiama("GET", "/api/lettori/031")).j.gettone; avanti(5);
const D = { lettore: "lettore-hhhhhhhhhhhhhhhh", ip: "7.7.7.7" }, E = { lettore: "lettore-iiiiiiiiiiiiiiii", ip: "8.8.8.8" };
r = await chiama("POST", "/api/lettori/031/commenti", { ...D, corpo: { nome: "giulia t", testo: "Mi firmo come lei", gettone: g2 } });
verifica("il nome di un altro lettore: rifiutato, anche scritto diverso", r.s === 409 && /già di un altro lettore/.test(r.j.errore), r);
r = await chiama("POST", "/api/lettori/031/commenti", { ...D, corpo: { nome: "Giulia T. 🚀", testo: "Ci riprovo con una faccina", gettone: g2 } });
verifica("il nome di un altro con un simbolo in più: rifiutato", r.s === 400 && /simboli/.test(r.j.errore), r);
r = await chiama("POST", "/api/lettori/031/commenti", { ...D, corpo: { nome: "GiuIia T.", testo: "Ci riprovo con la I maiuscola", gettone: g2 } });
verifica("il nome di un altro con la I al posto della elle: rifiutato", r.s === 409, r);
r = await chiama("GET", "/api/lettori/nome?n=" + encodeURIComponent("Giu1ia T"), D);
verifica("verifica del nome: preso anche con l'uno al posto della elle", r.j.libero === false, r);
r = await chiama("GET", "/api/lettori/031");
verifica("i commenti con il nome copiato non sono stati salvati", !r.j.commenti.some((x) => /Mi firmo come lei|Ci riprovo/.test(x.testo)), r.j.commenti);
verifica("un commento rifiutato non lascia il nome preso", env.DB._db.prepare("SELECT COUNT(*) AS n FROM nomi WHERE autore != (SELECT autore FROM nomi WHERE chiave = 'glullat') AND chiave LIKE 'glu%'").get().n === 0, null);
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: { nome: "GIULIA T", testo: "Sono sempre io, in maiuscolo", gettone: g2 } });
verifica("chi ha il nome lo riusa, anche scritto diverso", r.s === 201 && r.j.commento.nome === "GIULIA T", r);
r = await chiama("GET", "/api/lettori/nome?n=" + encodeURIComponent("Giulia T."), D);
verifica("verifica del nome: preso", r.s === 200 && r.j.libero === false && r.j.tuo === false && /altro lettore/.test(r.j.messaggio), r);
r = await chiama("GET", "/api/lettori/nome?n=" + encodeURIComponent("Giulia T."));
verifica("verifica del nome: è tuo", r.j.libero === true && r.j.tuo === true, r);
r = await chiama("GET", "/api/lettori/nome?n=" + encodeURIComponent("Orso con ombrello"), D);
verifica("verifica del nome: libero", r.j.libero === true && r.j.tuo === false && r.j.messaggio === "", r);
r = await chiama("GET", "/api/lettori/nome?n=Redazione", D);
verifica("verifica del nome: riservato", r.j.libero === false && /riservato/.test(r.j.messaggio), r);
r = await chiama("GET", "/api/lettori/nome?n=" + encodeURIComponent("Giulia T."), { ...D, base: "https://anteprima-g13-gommberg.esempio.workers.dev", origine: null });
verifica("i nomi delle anteprime sono separati da quelli di gommberg.com", r.j.libero === true, r);
// un lettore tiene per sé LIMITI.nomi_per_lettore nomi; per prenderne un altro uno dei suoi deve essere fermo da un mese
for (const [i, nome] of ["Primo nome", "Secondo nome", "Terzo nome"].entries()) {
  avanti(120);
  r = await chiama("POST", "/api/lettori/031/commenti", { ...D, corpo: { nome, testo: "Cambio firma, giro " + i, gettone: g2 } });
  verifica("nome nuovo dello stesso lettore: " + nome, r.s === 201, r);
}
avanti(120);
r = await chiama("POST", "/api/lettori/031/commenti", { ...D, corpo: { nome: "Quarto nome", testo: "Cambio firma, giro 3", gettone: g2 } });
verifica("il quarto nome subito: rifiutato, con l'elenco dei suoi", r.s === 409 && LIMITI.nomi_per_lettore === 3 && /Primo nome, Secondo nome, Terzo nome/.test(r.j.errore), r);
r = await chiama("GET", "/api/lettori/nome?n=" + encodeURIComponent("Primo nome"), E);
verifica("il primo nome non passa a un altro lettore finché è fresco", r.j.libero === false, r);
r = await chiama("POST", "/api/lettori/031/commenti", { ...D, corpo: { nome: "primo  NOME", testo: "Con uno dei miei nomi si scrive sempre", gettone: g2 } });
verifica("con uno dei propri nomi si continua a scrivere", r.s === 201, r);
avanti((LIMITI.nome_cambio_giorni + 1) * 86400);
const g2b = (await chiama("GET", "/api/lettori/031")).j.gettone; avanti(5);
r = await chiama("POST", "/api/lettori/031/commenti", { ...D, corpo: { nome: "Quarto nome", testo: "Un mese dopo cambio firma", gettone: g2b } });
verifica("dopo un mese il quarto nome si prende", r.s === 201, r);
r = await chiama("GET", "/api/lettori/nome?n=" + encodeURIComponent("Secondo nome"), E);
verifica("e torna libero quello fermo da più tempo", r.j.libero === true, r);
r = await chiama("GET", "/api/lettori/nome?n=" + encodeURIComponent("Quarto nome"), E);
verifica("gli ultimi nomi restano del lettore", r.j.libero === false, r);
// un nome non più usato torna libero dopo LIMITI.nome_giorni
avanti((LIMITI.nome_giorni + 1) * 86400);
const g3 = (await chiama("GET", "/api/lettori/031")).j.gettone; avanti(5);
r = await chiama("POST", "/api/lettori/031/commenti", { ...E, corpo: { nome: "Quarto nome", testo: "Il nome era fermo da mesi", gettone: g3 } });
verifica("un nome fermo da " + LIMITI.nome_giorni + " giorni si può riprendere", r.s === 201, r);
r = await chiama("POST", "/api/lettori/031/commenti", { ...D, corpo: { nome: "Quarto nome", testo: "Torno e lo rivoglio", gettone: g3 } });
verifica("e da quel momento è del nuovo lettore", r.s === 409, r);

// i nomi del dado (assets/lettori.js): il mazzo scritto a mano, i nomi combinati e quelli con il numero romano
const sezione = readFileSync(new URL("../../assets/lettori.js", import.meta.url), "utf8");
const lista = (nome) => { const i = sezione.indexOf("var " + nome + " = ["); return [...sezione.slice(i, sezione.indexOf("];", i)).split("\n").filter((r) => !/^\s*\/\//.test(r)).join("\n").matchAll(/"([^"\n]+)"/g)].map((m) => m[1]); };
const dado = lista("NOMI"), propri = lista("PROPRI"), cognomi = lista("COGNOMI");
verifica("il mazzo del dado ha almeno cento nomi", dado.length >= 100, dado.length);
verifica("ogni nome del mazzo è Nome Cognome: due parole", dado.every((x) => x.split(" ").length === 2), dado.filter((x) => x.split(" ").length !== 2));
verifica("ogni nome del mazzo è accettato dal servizio (lunghezza, lettere, non riservato)", dado.every((x) => !controllaNome(x)), dado.filter((x) => controllaNome(x)));
verifica("i nomi del mazzo sono tutti diversi anche per chiave", new Set(dado.map(chiaveNome)).size === dado.length, dado.filter((x, i) => dado.findIndex((y) => chiaveNome(y) === chiaveNome(x)) !== i));
const combinati = propri.flatMap((a) => cognomi.map((b) => a + " " + b));
verifica("i nomi combinati sono migliaia", combinati.length >= 4000, combinati.length);
verifica("ogni nome combinato è accettato dal servizio, anche con il numero romano", combinati.every((x) => !controllaNome(x) && !controllaNome(x + " II") && !controllaNome(x + " XIV")), combinati.filter((x) => controllaNome(x) || controllaNome(x + " XIV")).slice(0, 5));
verifica("i nomi combinati sono tutti diversi anche per chiave, e diversi con il numero", new Set(combinati.map(chiaveNome)).size === combinati.length && new Set(combinati.map((x) => chiaveNome(x + " II"))).size === combinati.length && chiaveNome("Gino Spread II") !== chiaveNome("Gino Spread III"), null);
// il dado ne chiede dieci per volta e riceve solo quelli che può proporre
// (qui "Quarto nome" è di E; "Giulia T." è scaduto da mesi, quindi di nuovo libero)
r = await chiama("GET", "/api/lettori/nome?" + ["Quarto nome", "QUARTO N0ME", "Massimo Rischio", "massimo  rischio", "Redazione", "Wanda Plusvalenza", "x", "Giulia T."].map((x) => "n=" + encodeURIComponent(x)).join("&"), D);
verifica("più nomi in una richiesta: tornano i liberi, una volta sola, senza presi né riservati", r.s === 200 && JSON.stringify(r.j.liberi) === JSON.stringify(["Massimo Rischio", "Wanda Plusvalenza", "Giulia T."]), r);
r = await chiama("GET", "/api/lettori/nome?" + ["Quarto nome", "Wanda Plusvalenza"].map((x) => "n=" + encodeURIComponent(x)).join("&"), E);
verifica("più nomi in una richiesta: il proprio nome è tra i liberi", JSON.stringify(r.j.liberi) === JSON.stringify(["Quarto nome", "Wanda Plusvalenza"]), r);
r = await chiama("GET", "/api/lettori/nome?" + Array.from({ length: 40 }, (_, i) => "n=" + encodeURIComponent("Gino Spread " + (i + 2))).join("&"), E);
verifica("più nomi in una richiesta: al massimo dodici per volta", r.j.liberi.length === 12, r.j.liberi.length);

// ------------------------------------------------------------- 11. segnalazioni aperte per l'avviso alla redazione
r = await chiama("POST", "/api/lettori/031/commenti", { ...E, corpo: { nome: "Quarto nome", testo: "Commento che qualcuno segnala", gettone: g3 } });
const c9 = r.j.commento.id;
r = await chiama("GET", "/api/lettori/segnalazioni");
verifica("le segnalazioni vecchie non sono più nell'elenco", r.s === 200 && r.j.sito === "gommberg" && r.j.segnalati.length === 0, r);
await chiama("POST", "/api/lettori/commenti/" + c9 + "/segnala", { ...D, corpo: { gettone: g3 } });
r = await chiama("GET", "/api/lettori/segnalazioni", { lettore: "", origine: null });
verifica("una segnalazione: il commento entra nell'elenco, ancora visibile", r.j.segnalati.length === 1 && r.j.segnalati[0].id === c9 && r.j.segnalati[0].ed === 31 && r.j.segnalati[0].reti === 1 && r.j.segnalati[0].nascosto === false, r);
verifica("l'elenco non porta testi, nomi né impronte", JSON.stringify(Object.keys(r.j.segnalati[0]).sort()) === '["ed","id","nascosto","reti","ultima"]', r.j.segnalati[0]);
env.DB._db.exec("UPDATE commenti SET nascosto = 2 WHERE id = " + c9);
r = await chiama("GET", "/api/lettori/segnalazioni");
verifica("tolto dalla redazione: esce dall'elenco", r.j.segnalati.length === 0, r);
r = await chiama("GET", "/api/lettori/segnalazioni", { base: "https://anteprima-g13-gommberg.esempio.workers.dev", origine: null });
verifica("l'elenco delle anteprime è separato", r.j.sito === "prova" && r.j.segnalati.length === 0, r);

// ------------------------------------------------------------- 12. guasti trovati dal collaudo indipendente del 22/11
const g4 = (await chiama("GET", "/api/lettori/031")).j.gettone; avanti(5);
const F = { lettore: "lettore-llllllllllllllll", ip: "9.9.9.9" }, G = { lettore: "lettore-mmmmmmmmmmmmmmmm", ip: "9.9.9.10" };
// testi enormi: rifiutati prima di ripulirli (la pulizia di 150.000 spazi teneva occupato il servizio per 20 secondi)
let t0 = performance.now();
r = await chiama("POST", "/api/lettori/031/commenti", { ...F, corpo: { nome: "Grande", testo: " ".repeat(150000) + "x", gettone: g4 } });
verifica("testo enorme: rifiutato subito (400, o 413 se il corpo supera i 32 KB)", (r.s === 400 || r.s === 413) && performance.now() - t0 < 500, [r.s, Math.round(performance.now() - t0)]);
t0 = performance.now(); pulisciTesto(" ".repeat(5000) + "x");
verifica("la pulizia del testo più lungo ammesso è immediata", performance.now() - t0 < 200, Math.round(performance.now() - t0));
r = await chiama("GET", "/api/lettori/nome?n=" + "a".repeat(5000), F);
verifica("nome enorme nella verifica: non libero, senza errori", r.s === 200 && r.j.libero === false, r);
// origine e corpo malformati: una risposta chiara, non "servizio non disponibile"
r = await chiama("POST", "/api/lettori/031/commenti", { ...F, origine: "null", corpo: { nome: "Grande", testo: "Origine nulla", gettone: g4 } });
verifica("origine \"null\": 403", r.s === 403, r);
r = await worker.fetch(new Request(BASE + "/api/lettori/031/commenti", { method: "POST", headers: { "x-lettore": F.lettore, origin: BASE, "content-type": "application/json" }, body: "null" }), env);
verifica("corpo null: 400", r.status === 400, r.status);
// le risposte sotto un commento tolto non escono più, e non se ne aggiungono
r = await chiama("POST", "/api/lettori/031/commenti", { ...F, corpo: { nome: "Radice", testo: "Commento che la redazione toglierà", gettone: g4 } });
const radice = r.j.commento.id;
r = await chiama("POST", "/api/lettori/031/commenti", { ...G, corpo: { nome: "Rametto", testo: "Risposta al commento che sparirà", padre: radice, gettone: g4 } });
const rametto = r.j.commento.id;
env.DB._db.exec("UPDATE commenti SET nascosto = 2 WHERE id = " + radice);
r = await chiama("GET", "/api/lettori/031");
verifica("tolto il commento, le sue risposte non escono", !r.j.commenti.some((x) => x.id === rametto || x.id === radice), r.j.commenti.map((x) => x.id));
avanti(60);
r = await chiama("POST", "/api/lettori/031/commenti", { ...F, corpo: { nome: "Radice", testo: "Rispondo a una risposta rimasta orfana", padre: rametto, gettone: g4 } });
verifica("niente risposte nuove sotto un commento tolto", r.s === 404, r);
// l'elenco delle segnalazioni: prima i nascosti, poi dalla più recente
const tre = [];
for (const i of [1, 2, 3]) { avanti(61); tre.push((await chiama("POST", "/api/lettori/031/commenti", { ...F, corpo: { nome: "Radice", testo: "Commento da segnalare " + i, gettone: g4 } })).j.commento.id); }
for (const [k, id] of tre.entries()) { avanti(10); await chiama("POST", "/api/lettori/commenti/" + id + "/segnala", { lettore: "lettore-" + String(k).repeat(16), ip: "10.0.0." + k, corpo: { gettone: g4 } }); }
for (const k of [7, 8]) await chiama("POST", "/api/lettori/commenti/" + tre[0] + "/segnala", { lettore: "lettore-" + String(k).repeat(16), ip: "10.0.1." + k, corpo: { gettone: g4 } });
r = await chiama("GET", "/api/lettori/segnalazioni");
verifica("elenco: il nascosto per primo, poi la segnalazione più recente", JSON.stringify(r.j.segnalati.map((x) => x.id)) === JSON.stringify([tre[0], tre[2], tre[1]]) && r.j.segnalati[0].nascosto === true, r.j.segnalati);
let fermate = 0;
for (let i = 0; i < LIMITI.segnala_giorno + 2; i++) fermate += (await chiama("POST", "/api/lettori/commenti/" + tre[1] + "/segnala", { lettore: "lettore-" + String(i).padStart(16, "z"), ip: "10.9.9.9", corpo: { gettone: g4 } })).s === 429;
verifica("una rete sola non manda più di " + LIMITI.segnala_giorno + " segnalazioni al giorno, nemmeno cambiando codice", fermate === 2, fermate);
// richieste nello stesso istante, con il database che risponde con ritardi a caso come D1 vero
env.DB.latenza = 4;
const H = { lettore: "lettore-nnnnnnnnnnnnnnnn", ip: "11.0.0.1" };
let esiti = await Promise.all(Array.from({ length: 20 }, (_, i) => chiama("POST", "/api/lettori/031/commenti", { ...H, corpo: { nome: "Raffica", testo: "Raffica " + i, gettone: g4 } })));
verifica("venti commenti insieme: ne passano al massimo " + LIMITI.commenti_10min, esiti.filter((x) => x.s === 201).length <= LIMITI.commenti_10min, esiti.map((x) => x.s));
avanti(601);
esiti = await Promise.all(Array.from({ length: 5 }, () => chiama("POST", "/api/lettori/031/commenti", { ...H, corpo: { nome: "Raffica", testo: "Lo stesso testo cinque volte", gettone: g4 } })));
verifica("lo stesso testo cinque volte insieme: ne passa uno", esiti.filter((x) => x.s === 201).length === 1, esiti.map((x) => x.s));
let doppi = 0;
for (let giro = 0; giro < 40; giro++) {
  const nome = "Conteso " + giro;
  const quattro = await Promise.all([0, 1, 2, 3].map((k) => chiama("POST", "/api/lettori/031/commenti", { lettore: "lettore-" + ("c" + giro + "k" + k).padStart(16, "y"), ip: "12." + giro + ".0." + k, corpo: { nome: k % 2 ? nome.toUpperCase() : nome, testo: "Lo voglio io " + giro + " " + k, gettone: g4 } })));
  doppi += quattro.filter((x) => x.s === 201).length !== 1;
}
verifica("un nome nuovo chiesto da quattro lettori insieme: lo prende uno solo", doppi === 0, doppi);
esiti = await Promise.all(Array.from({ length: 6 }, () => chiama("POST", "/api/lettori/commenti/" + tre[2] + "/piace", { ...H, corpo: { gettone: g4 } })));
verifica("sei like insieme dallo stesso lettore: nessun errore e il conto è quello vero", esiti.every((x) => x.s === 200) && env.DB._db.prepare("SELECT piace FROM commenti WHERE id = " + tre[2]).get().piace === env.DB._db.prepare("SELECT COUNT(*) AS n FROM piaciuti WHERE commento = " + tre[2]).get().n, esiti.map((x) => x.s));
// il nome scaduto conteso tra il vecchio padrone e un lettore nuovo: mai tutti e due
env.DB.latenza = 0;
const scaduti = [];
for (let giro = 0; giro < 40; giro++) {
  avanti(61);
  const v = { lettore: "lettore-" + ("v" + giro).padStart(16, "w"), ip: "13.0." + giro + ".1" };
  await chiama("POST", "/api/lettori/031/commenti", { ...v, corpo: { nome: "Scaduto " + giro, testo: "Prima che scada " + giro, gettone: g4 } });
  scaduti.push(v);
}
env.DB._db.exec("UPDATE nomi SET usato = '2026-01-01T00:00:00Z', creato = '2026-01-01T00:00:00Z' WHERE nome LIKE 'Scaduto %'");
env.DB._db.exec("UPDATE config SET v = '" + new Date(adesso).toISOString().slice(0, 10) + "' WHERE k = 'pulizia'");   // la pulizia di oggi è già passata: i nomi scaduti sono ancora in tabella
env.DB.latenza = 4; doppi = 0;
for (const [giro, v] of scaduti.entries()) {
  const n2 = { lettore: "lettore-" + ("n" + giro).padStart(16, "q"), ip: "13.1." + giro + ".1" };
  const due = await Promise.all([chiama("POST", "/api/lettori/031/commenti", { ...v, corpo: { nome: "SCADUTO " + giro, testo: "Torno dopo mesi " + giro, gettone: g4 } }),
                                 chiama("POST", "/api/lettori/031/commenti", { ...n2, corpo: { nome: "scaduto " + giro, testo: "Lo prendo io " + giro, gettone: g4 } })]);
  doppi += due.filter((x) => x.s === 201).length !== 1;
}
env.DB.latenza = 0;
verifica("un nome scaduto conteso: lo prende uno solo, mai tutti e due", doppi === 0, doppi);

// ------------------------------------------------------------- le edizioni di test non lasciano commenti né voti
// Sulla 031 (del 23/11) ci sono un commento, un like e un voto del 22/11: vengono da un'edizione di test pubblicata e poi
// tolta. Alla prima lettura del giorno dell'edizione spariscono; ciò che è stato scritto dal 23 in poi resta.
env.DB._db.exec(`INSERT INTO commenti (sito, ed, nome, testo, creato, autore, ip) VALUES ('gommberg', 31, 'Lettrice vera', 'Scritto a edizione uscita', '${new Date(adesso).toISOString().replace(/\.\d{3}Z$/, "Z")}', 'vera-autrice', '5.5.5.6')`);
avanti(301);
const veri = (await chiama("GET", "/api/lettori/031")).j.commenti.length;
env.DB._db.exec("INSERT INTO commenti (sito, ed, nome, testo, creato, autore, ip) VALUES ('gommberg', 31, 'Toro Seduto', 'Test 1', '2026-11-22T20:55:00Z', 'prova-autore', '5.5.5.5')");
const idProva = env.DB._db.prepare("SELECT id FROM commenti WHERE testo = 'Test 1'").get().id;
env.DB._db.exec(`INSERT INTO piaciuti (commento, autore, ip, creato) VALUES (${idProva}, 'prova-autore', '5.5.5.5', '2026-11-22T20:56:00Z')`);
env.DB._db.exec("INSERT INTO voti (sito, ed, autore, voto, ip, creato) VALUES ('gommberg', 31, 'prova-autore', 'toro', '5.5.5.5', '2026-11-22T20:56:00Z')");
const votiPrima = env.DB._db.prepare("SELECT COUNT(*) AS n FROM voti WHERE ed = 31").get().n;
avanti(301);
r = await chiama("GET", "/api/lettori/031");
const conta = (sql) => env.DB._db.prepare(sql).get().n;
verifica("edizione di test: i commenti scritti prima del giorno dell'edizione spariscono", !r.j.commenti.some((x) => x.testo === "Test 1") && conta("SELECT COUNT(*) AS n FROM commenti WHERE testo = 'Test 1'") === 0);
verifica("edizione di test: spariscono anche i like e i voti di quel giorno", conta(`SELECT COUNT(*) AS n FROM piaciuti WHERE commento = ${idProva}`) === 0 && conta("SELECT COUNT(*) AS n FROM voti WHERE ed = 31") === votiPrima - 1);
verifica("edizione di test: ciò che è stato scritto dal giorno dell'edizione resta", r.j.commenti.length === veri && veri > 0, [r.j.commenti.length, veri]);
// Un'edizione di test ancora in linea (la 032, con la data di domani): finché il suo giorno non arriva nulla si tocca
const isoOra = () => new Date(adesso).toISOString().replace(/\.\d{3}Z$/, "Z");
EDIZIONI[32] = { numero: 32, data: new Date(adesso + 86400000).toISOString().slice(0, 10) };
env.DB._db.exec(`INSERT INTO commenti (sito, ed, nome, testo, creato, autore, ip) VALUES ('gommberg', 32, 'Toro Seduto', 'Provo la 032', '${isoOra()}', 'prova-autore', '5.5.5.5')`);
r = await chiama("GET", "/api/lettori/032");
verifica("edizione di test in linea: prima del suo giorno i commenti di prova si vedono", r.s === 200 && r.j.commenti.some((x) => x.testo === "Provo la 032"), r.j);
avanti(86400);
r = await chiama("GET", "/api/lettori/032");
verifica("edizione di test: dal suo giorno i commenti di prova non ci sono più", r.s === 200 && r.j.commenti.length === 0 && conta("SELECT COUNT(*) AS n FROM commenti WHERE ed = 32") === 0, r.j);
verifica("la pulizia delle prove non tocca le altre edizioni", conta("SELECT COUNT(*) AS n FROM commenti WHERE ed = 31") > 0);

await areaRiservata();
console.log(ko ? `Lettori e redazione: ${ko} NO su ${ok + ko} prove` : `Lettori e redazione: ${ok} prove superate`);
process.exit(ko ? 1 : 0);

// ============================================================= l'area riservata della redazione (G-51)
// Accesso, sessioni, tentativi, CSRF, password, pannello protetto, moderazione e firma della redazione; con gli attacchi:
// senza sessione, sessione scaduta o chiusa, cookie manomesso, CSRF mancante o di un'altra sessione, forza bruta, iniezioni
// nei filtri, un lettore che si firma Gommberg o chiama le azioni della redazione.
async function areaRiservata() {
  const UT = "direttore-prova", PW = "una frase lunga di prova per il collaudo";
  env.REDAZIONE_UTENTE = UT; env.REDAZIONE_PASSWORD = PW;
  const FILE = { "index.html": "<!doctype html><title>Area</title><script>var a=1</script><p>AREA-RISERVATA</p>",
                 "accesso.html": "<!doctype html><title>Accesso</title><script>var b=2</script><p>SCHERMATA-DI-ACCESSO</p>",
                 "registro.json": '[{"n":31,"d":"2026-11-23"}]', "invii.json": '{"invii":[]}' };
  usaPrivato(FILE, Object.keys(PUBBLICI_RED));
  verifica("il punto d'ingresso del Worker esporta solo il gestore (Cloudflare rifiuta le costanti)", servizio === worker && typeof servizio.fetch === "function");
  let numIp = 0;
  const nuovoIp = () => "203.0." + Math.floor(++numIp / 250) + "." + (numIp % 250 + 1);
  async function red(metodo, percorso, { corpo, crudo, cookie, csrf, origine = BASE, ip = "9.9.9.9", ua = "Mozilla/5.0 (Windows NT 10.0) Chrome/130", lettore } = {}) {
    const h = { "cf-connecting-ip": ip, "user-agent": ua };
    if (origine) h.origin = origine;
    if (cookie) h.cookie = cookie;
    if (csrf) h["x-csrf"] = csrf;
    if (lettore) h["x-lettore"] = lettore;
    if (corpo || crudo) h["content-type"] = "application/json";
    const r = await worker.fetch(new Request(BASE + percorso, { method: metodo, headers: h, body: crudo != null ? crudo : corpo ? JSON.stringify(corpo) : undefined, redirect: "manual" }), env);
    const testo = await r.text();
    let j = null; try { j = JSON.parse(testo); } catch (e) { j = testo; }
    return { s: r.status, j, h: r.headers, set: r.headers.getSetCookie() };
  }
  const tokenDa = (set) => { const c = set.find((x) => x.startsWith(COOKIE + "=")); return c ? c.split(";")[0].slice(COOKIE.length + 1) : ""; };
  async function entra(o = {}) {
    const r = await red("POST", "/api/redazione/accesso", { corpo: { utente: UT, password: o.password || PW, resta: o.resta !== false }, ip: o.ip || nuovoIp(), ua: o.ua });
    const t = tokenDa(r.set);
    const s = t ? await red("GET", "/api/redazione/sessione", { cookie: COOKIE + "=" + t }) : null;
    return { r, t, cookie: COOKIE + "=" + t, csrf: s && s.j && s.j.csrf };
  }
  const q = (sql) => env.DB._db.prepare(sql).all();

  // ------------------------------------------------- pagine e dati del pannello
  let r = await red("GET", "/redazione");
  verifica("area: /redazione porta a /redazione/", r.s === 301 && r.h.get("location") === "/redazione/", r.s);
  r = await red("GET", "/redazione/");
  verifica("area: senza sessione la schermata di accesso, mai l'area", r.s === 200 && r.j.includes("SCHERMATA-DI-ACCESSO") && !r.j.includes("AREA-RISERVATA"), r.j);
  const csp = r.h.get("content-security-policy") || "", nonce = (/'nonce-([^']+)'/.exec(csp) || [])[1];
  verifica("area: CSP con nonce, e il nonce sugli script della pagina", !!nonce && r.j.includes(`<script nonce="${nonce}">`) && /frame-ancestors 'none'/.test(csp) && /default-src 'none'/.test(csp), csp);
  verifica("area: intestazioni di sicurezza e nessuna cache", r.h.get("cache-control").includes("no-store") && r.h.get("x-frame-options") === "DENY" && r.h.get("x-content-type-options") === "nosniff" && r.h.get("referrer-policy") === "no-referrer" && !!r.h.get("strict-transport-security"));
  const r2 = await red("GET", "/redazione/");
  verifica("area: un nonce nuovo a ogni pagina", !r2.h.get("content-security-policy").includes(nonce));
  // senza sessione un file del pannello risponde come un file che non esiste: stesso stato, stesso corpo (non rivela i nomi)
  const inesistente = await red("GET", "/redazione/non-esiste-davvero.json");
  for (const x of ["/redazione/registro.json", "/redazione/invii.json"]) {
    r = await red("GET", x);
    verifica("pannello: " + x + " senza sessione risponde come un file che non esiste", r.s === 404 && r.s === inesistente.s && r.j === inesistente.j && !JSON.stringify(r.j).includes("2026-11-23"), [r.s, inesistente.s]);
  }
  for (const x of Object.keys(PUBBLICI_RED)) {
    r = await red("GET", x);
    verifica("file pubblici: " + x + " passa dal Worker ai file statici (Impara, Numeri, Scommessa)", r.s === 200 && JSON.stringify(r.j) === PUBBLICI_RED[x], r.s);
  }
  // difesa: i file pubblici e ciò che non è dell'area vanno ai file statici prima di aprire il database (se D1 è giù,
  // Impara, Numeri e Scommessa funzionano lo stesso)
  const rotto = { ...env, DB: { prepare() { throw new Error("D1 giù"); }, batch() { throw new Error("D1 giù"); } } };
  for (const x of [...Object.keys(PUBBLICI_RED), "/redazione/cartella/che/non-esiste.png"]) {
    L_.nuovaIstanza && L_.nuovaIstanza();
    const rr = await worker.fetch(new Request(BASE + x, { headers: { "cf-connecting-ip": "8.8.8.8" } }), rotto);
    verifica("difesa: " + x + " con il database giù va ai file statici", rr.status === (PUBBLICI_RED[x] ? 200 : 404), rr.status);
  }
  L_.nuovaIstanza && L_.nuovaIstanza();
  // con un cookie finto, un file del pannello e un nome inesistente fanno lo stesso lavoro (stesse chiamate a D1)
  let chiamate = 0;
  const contato = { ...env, DB: { prepare: (sql) => { chiamate++; return env.DB.prepare(sql); }, batch: (l) => env.DB.batch(l) } };
  const lavoro = async (u) => { chiamate = 0; const rr = await worker.fetch(new Request(BASE + u, { headers: { cookie: COOKIE + "=" + "A".repeat(43), "cf-connecting-ip": "8.8.8.8" } }), contato); return [rr.status, chiamate]; };
  await lavoro("/redazione/registro.json");
  const [sP, cP] = await lavoro("/redazione/registro.json"), [sN, cN] = await lavoro("/redazione/nome-che-non-esiste.json");
  verifica("tempi: senza sessione, file del pannello e file inesistente fanno lo stesso lavoro", sP === 404 && sN === 404 && cP === cN && cP > 0, [sP, cP, sN, cN]);
  for (const x of ["/redazione/segreti.json", "/redazione/../pannello/registro.json", "/redazione/%2e%2e/redazione.js", "/redazione/index.html.bak", "/redazione/REGISTRO.json"]) {
    r = await red("GET", x);
    verifica("pannello: " + x + " non esiste", r.s === 404 || (r.s === 200 && typeof r.j === "string" && r.j.includes("SCHERMATA-DI-ACCESSO")) || r.j === "statico", [x, r.s]);
  }
  // le anteprime (workers.dev) e ogni altro indirizzo: niente area, niente azioni; i file pubblici sì
  for (const host of ["https://prova-gommberg.paolo.workers.dev", "https://gommberg.com.evil.example"]) {
    const ra = await worker.fetch(new Request(host + "/api/redazione/accesso", { method: "POST", headers: { origin: host, "content-type": "application/json", "cf-connecting-ip": "8.8.4.4" }, body: JSON.stringify({ utente: UT, password: PW }) }), env);
    const rp = await worker.fetch(new Request(host + "/redazione/"), env);
    const rf = await worker.fetch(new Request(host + "/redazione/glossario.json"), env);
    verifica("area: su " + new URL(host).host + " non c'è (né accesso né pagina), i file pubblici sì", ra.status === 404 && rp.status === 404 && !ra.headers.getSetCookie().length && rf.status === 200, [ra.status, rp.status, rf.status]);
  }
  r = await red("POST", "/redazione/registro.json", { corpo: {} });
  verifica("pannello: un POST sulle pagine va ai file statici, mai ai dati", (r.s === 404 || r.s === 405) && !JSON.stringify(r.j).includes("2026-11-23"), r.s);

  // ------------------------------------------------- accesso
  const utenteVecchio = env.REDAZIONE_UTENTE;
  delete env.REDAZIONE_UTENTE;
  r = await red("POST", "/api/redazione/accesso", { corpo: { utente: UT, password: PW }, ip: nuovoIp() });
  verifica("accesso: senza i segreti su Cloudflare è spento", r.s === 503 && /configurato/.test(r.j.errore), r);
  env.REDAZIONE_UTENTE = utenteVecchio; env.REDAZIONE_PASSWORD = "corta";
  r = await red("POST", "/api/redazione/accesso", { corpo: { utente: UT, password: "corta" }, ip: nuovoIp() });
  verifica("accesso: con una password del segreto sotto i 16 caratteri è spento", r.s === 503, r);
  env.REDAZIONE_PASSWORD = PW;
  const ipA = nuovoIp();
  const a1 = await red("POST", "/api/redazione/accesso", { corpo: { utente: UT, password: "sbagliata-ma-lunga-123" }, ip: ipA });
  const a2 = await red("POST", "/api/redazione/accesso", { corpo: { utente: "chi-non-esiste", password: PW }, ip: ipA });
  const a3 = await red("POST", "/api/redazione/accesso", { corpo: { utente: "", password: "" }, ip: ipA });
  verifica("accesso: utente inesistente e password sbagliata danno la stessa risposta", a1.s === 401 && a2.s === 401 && JSON.stringify(a1.j) === JSON.stringify(a2.j) && a3.s === 401 && !a1.set.length, [a1, a2]);
  r = await red("POST", "/api/redazione/accesso", { corpo: { utente: UT, password: PW }, origine: null, ip: nuovoIp() });
  verifica("accesso: senza origine rifiutato", r.s === 403 && !r.set.length, r.s);
  r = await red("POST", "/api/redazione/accesso", { corpo: { utente: UT, password: PW }, origine: "https://gommberg.com.attacco.example", ip: nuovoIp() });
  verifica("accesso: da un altro sito rifiutato", r.s === 403 && !r.set.length, r.s);
  for (const [crudo, atteso] of [["non json", 400], ["[1,2]", 400], ["null", 400], ['{"utente":' + JSON.stringify("x".repeat(9000)) + "}", 413]]) {
    r = await red("POST", "/api/redazione/accesso", { crudo, ip: nuovoIp() });
    verifica("accesso: corpo " + crudo.slice(0, 12) + " rifiutato con " + atteso, r.s === atteso, r.s);
  }
  r = await red("POST", "/api/redazione/accesso", { corpo: { utente: UT, password: PW }, origine: "http://gommberg.com", ip: nuovoIp() });
  verifica("accesso: stesso nome di sito ma schema diverso (http): rifiutato, l'origine si confronta intera", r.s === 403 && !r.set.length, r.s);
  let letto = 0;
  const flusso = () => new ReadableStream({ pull(ctrl) { letto++; ctrl.enqueue(new TextEncoder().encode("x".repeat(4096))); } });
  let rr = await worker.fetch(new Request(BASE + "/api/redazione/accesso", { method: "POST", duplex: "half", body: flusso(),
    headers: { origin: BASE, "content-type": "application/json", "content-length": "20000000", "cf-connecting-ip": nuovoIp() } }), env);
  verifica("accesso: un corpo dichiarato di 20 MB si rifiuta prima di leggerlo (al più il primo pezzo che il runtime prende da sé)", rr.status === 413 && letto <= 2, [rr.status, letto]);
  rr = await worker.fetch(new Request(BASE + "/api/redazione/accesso", { method: "POST", duplex: "half", body: flusso(),
    headers: { origin: BASE, "content-type": "application/json", "cf-connecting-ip": nuovoIp() } }), env);
  verifica("accesso: un corpo senza lunghezza dichiarata si ferma appena supera il limite", rr.status === 413, rr.status);
  r = await red("POST", "/api/redazione/accesso", { corpo: { utente: [UT], password: { p: PW } }, ip: nuovoIp() });
  verifica("accesso: campi che non sono testo non passano", r.s === 401, r.s);
  const e1 = await entra();
  const ck = e1.r.set.find((x) => x.startsWith(COOKIE + "=")) || "", spia = e1.r.set.find((x) => x.startsWith(SPIA + "=")) || "";
  verifica("accesso: entra con nome utente e password", e1.r.s === 200 && e1.t.length === 43 && !!e1.csrf, e1.r);
  verifica("accesso: cookie __Host-, HttpOnly, Secure, SameSite=Strict, Path=/, 90 giorni con Resta collegato",
    /; Path=\/;/.test(ck) && /HttpOnly/.test(ck) && /Secure/.test(ck) && /SameSite=Strict/.test(ck) && /Max-Age=7776000/.test(ck) && !/Domain=/i.test(ck), ck);
  verifica("accesso: il cookie spia per le pagine non è HttpOnly e non contiene segreti", spia.startsWith(SPIA + "=1;") && !/HttpOnly/.test(spia), spia);
  const e2 = await entra({ resta: false, ua: "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) Mobile/15E148 Safari/604.1" });
  verifica("accesso: senza Resta collegato il cookie sparisce alla chiusura del browser", e2.r.s === 200 && !e2.r.set.some((x) => /Max-Age/.test(x)), e2.r.set);
  const dump = JSON.stringify(q("SELECT * FROM sessioni")) + JSON.stringify(q("SELECT * FROM config")) + JSON.stringify(q("SELECT * FROM accessi"));
  verifica("accesso: in D1 né il gettone di sessione né la password", !dump.includes(e1.t) && !dump.includes(e2.t) && !dump.includes(PW) && !dump.includes(UT), "");
  r = await red("GET", "/redazione/", { cookie: e1.cookie });
  verifica("area: con la sessione, allo stesso indirizzo, l'area", r.s === 200 && r.j.includes("AREA-RISERVATA"), r.s);
  r = await red("GET", "/redazione/registro.json", { cookie: e1.cookie });
  verifica("pannello: con la sessione i dati", r.s === 200 && Array.isArray(r.j) && r.j[0].n === 31 && r.h.get("cache-control").includes("no-store"), r);
  r = await red("GET", "/redazione/registro.json", { cookie: "gtd_sessione=" + e1.t });
  verifica("pannello: il gettone giusto con il nome di cookie sbagliato non vale", r.s === 404, r.s);

  // ------------------------------------------------- cookie manomesso, sessione scaduta, CSRF
  const altro = e1.t.slice(0, 42) + (e1.t[42] === "A" ? "B" : "A");
  for (const [nome, c] of [["un carattere cambiato", COOKIE + "=" + altro], ["troppo corto", COOKIE + "=" + e1.t.slice(0, 20)], ["con caratteri strani", COOKIE + "=" + e1.t.slice(0, 40) + "%27--"],
                           ["solo la spia", SPIA + "=1"], ["doppio, il primo falso", COOKIE + "=" + altro + "; " + e1.cookie]]) {
    r = await red("GET", "/api/redazione/sessione", { cookie: c });
    verifica("sessione: cookie " + nome + ": nessun accesso", r.s === 401, r.s);
  }
  r = await red("GET", "/api/redazione/commenti", { lettore: "lettore-aaaaaaaaaaaaaaaa" });
  verifica("redazione: un lettore senza sessione non legge l'elenco", r.s === 401, r.s);
  for (const [percorso, corpo] of [["commenti/1/togli", {}], ["commenti", { ed: 31, testo: "Sono la redazione, giuro" }], ["lettori/blocca", { commento: 1 }], ["edizioni/31/chiudi", {}], ["esci-tutti", {}], ["password/verifica", { attuale: "x" }], ["password", { prova: "1.x", nuova: "y".repeat(20), conferma: "y".repeat(20) }]]) {
    r = await red("POST", "/api/redazione/" + percorso, { corpo, lettore: "lettore-aaaaaaaaaaaaaaaa" });
    verifica("redazione: un lettore non può " + percorso, r.s === 401, r.s);
    r = await red("POST", "/api/redazione/" + percorso, { corpo, cookie: e1.cookie });
    verifica("CSRF: " + percorso + " senza gettone rifiutato", r.s === 403, r.s);
    r = await red("POST", "/api/redazione/" + percorso, { corpo, cookie: e1.cookie, csrf: e2.csrf });
    verifica("CSRF: " + percorso + " con il gettone di un'altra sessione rifiutato", r.s === 403, r.s);
    r = await red("POST", "/api/redazione/" + percorso, { corpo, cookie: e1.cookie, csrf: e1.csrf, origine: "https://altro.example" });
    verifica("CSRF: " + percorso + " da un altro sito rifiutato", r.s === 403, r.s);
  }
  // senza Resta collegato: 12 ore senza uso e la sessione non vale più; con Resta collegato vale, e si rinnova usandola
  avanti(AREA.breve_ore * 3600 + 5);
  r = await red("GET", "/api/redazione/sessione", { cookie: e2.cookie });
  verifica("sessione: senza Resta collegato scade dopo 12 ore senza uso", r.s === 401, r.s);
  r = await red("GET", "/api/redazione/sessione", { cookie: e1.cookie });
  verifica("sessione: con Resta collegato vale ancora, e il cookie si rinnova", r.s === 200 && r.set.some((x) => x.startsWith(COOKIE + "=" + e1.t)), r.s);
  for (let i = 0; i < 2; i++) { avanti(30 * 86400); r = await red("GET", "/api/redazione/sessione", { cookie: e1.cookie }); }
  verifica("sessione: con Resta collegato, usata ogni mese, vale nei 90 giorni dall'accesso", r.s === 200, r.s);
  avanti(30 * 86400);
  r = await red("GET", "/api/redazione/sessione", { cookie: e1.cookie });
  verifica("sessione: con Resta collegato al massimo 90 giorni dall'accesso, anche usandola ogni giorno", r.s === 401, r.s);
  const eB = await entra({ resta: false });
  for (let i = 0; i < 13; i++) { avanti(3600); r = await red("GET", "/api/redazione/sessione", { cookie: eB.cookie }); }
  verifica("sessione: senza Resta collegato al massimo 12 ore dall'accesso, anche usandola ogni ora", r.s === 401, r.s);
  const eC = await entra();
  avanti(AREA.resta_giorni * 86400 - 60);
  avanti(120);
  r = await red("GET", "/api/redazione/sessione", { cookie: eC.cookie });
  verifica("sessione: 90 giorni senza uso e si esce da soli", r.s === 401, r.s);

  // ------------------------------------------------- forza bruta
  const ipB = nuovoIp(), sbaglia = (ip) => red("POST", "/api/redazione/accesso", { corpo: { utente: UT, password: "tentativo-" + Math.random() }, ip });
  for (let i = 0; i < AREA.errori_liberi; i++) await sbaglia(ipB);
  r = await red("POST", "/api/redazione/accesso", { corpo: { utente: UT, password: PW }, ip: ipB });
  verifica("tentativi: dopo 5 errori da una rete si aspetta, anche con la password giusta", r.s === 429 && r.j.attesa > 0 && r.j.attesa <= 60 && !r.set.length, r);
  const righe0 = q("SELECT COUNT(*) AS n FROM accessi")[0].n;
  for (let i = 0; i < 20; i++) await sbaglia(ipB);
  verifica("tentativi: chi aspetta non costa scritture (nessuna riga per ogni tentativo fermato)", q("SELECT COUNT(*) AS n FROM accessi")[0].n === righe0);
  r = await red("POST", "/api/redazione/accesso", { corpo: { utente: UT, password: PW }, ip: nuovoIp() });
  verifica("tentativi: le altre reti non sono ferme", r.s === 200, r.s);
  avanti(61); await sbaglia(ipB);
  r = await sbaglia(ipB);
  verifica("tentativi: l'attesa raddoppia a ogni errore (2 minuti dopo il sesto)", r.s === 429 && r.j.attesa > 60 && r.j.attesa <= 120, r.j);
  avanti(121);
  r = await red("POST", "/api/redazione/accesso", { corpo: { utente: UT, password: PW }, ip: ipB });
  verifica("tentativi: finita l'attesa la password giusta entra e azzera gli errori della rete", r.s === 200 && q("SELECT COUNT(*) AS n FROM accessi WHERE esito = 'errore' AND ip IN (SELECT ip FROM accessi WHERE esito = 'ok' ORDER BY id DESC LIMIT 1)")[0].n === 0, r.s);
  for (let i = 0; i < 12; i++) await sbaglia(ipB);
  avanti(30 * 60); r = await sbaglia(ipB); avanti(30 * 60 + 1);
  r = await sbaglia(ipB);
  verifica("tentativi: l'attesa non supera mai i 60 minuti", r.s === 429 ? r.j.attesa <= 3600 : r.s === 401, r.j);
  avanti(24 * 3600);
  // nessun blocco per tutti: 60 errori da 60 reti in un attimo non chiudono fuori Paolo (prima: 429 per 15 minuti)
  await Promise.all(Array.from({ length: 60 }, () => sbaglia(nuovoIp())));
  const e3 = await entra();
  verifica("tentativi: 60 errori da 60 reti diverse non chiudono fuori chi ha le credenziali giuste", e3.r.s === 200, e3.r.s);
  r = await red("GET", "/api/redazione/riepilogo", { cookie: e3.cookie });
  verifica("tentativi: la Panoramica dice quanti tentativi falliti e da quante reti, nelle ultime 24 ore", r.j.tentativi && r.j.tentativi.n >= 60 && r.j.tentativi.reti >= 60, r.j.tentativi);
  const ipC = nuovoIp();
  for (let i = 0; i < AREA.errori_liberi; i++) await sbaglia(ipC);
  r = await red("GET", "/api/redazione/sicurezza", { cookie: e3.cookie });
  const grC = (r.j.errori || []).filter((x) => x.n === AREA.errori_liberi);
  verifica("sicurezza: gli errori sono raggruppati per rete, con il conto, e gli accessi riusciti restano visibili", grC.length >= 1 && r.j.accessi.every((a) => a.esito !== "errore") && r.j.accessi.some((a) => a.esito === "ok") && r.j.tentativi.n >= 65, [r.j.errori && r.j.errori.length, r.j.tentativi]);
  // la corsa: 300 tentativi insieme dalla stessa rete non passano oltre i 5 liberi (prima ne passavano 11)
  avanti(16 * 60);
  const ipD = nuovoIp();
  env.DB.latenza = 4;
  await Promise.all(Array.from({ length: 300 }, () => sbaglia(ipD)));
  env.DB.latenza = 0;
  const provati = q("SELECT COUNT(*) AS n FROM accessi WHERE esito = 'errore' AND ip = (SELECT ip FROM accessi WHERE esito = 'errore' ORDER BY id DESC LIMIT 1)")[0].n;
  verifica("tentativi: 300 richieste in parallelo dalla stessa rete, al massimo 5 tentativi provati", provati <= AREA.errori_liberi, provati);
  // il messaggio del 429 dice che cosa fare se la rete è condivisa (ufficio, stessa /64)
  const ipM = nuovoIp();
  for (let i = 0; i < AREA.errori_liberi; i++) await sbaglia(ipM);
  r = await sbaglia(ipM);
  verifica("tentativi: il 429 suggerisce un'altra rete (per esempio i dati del telefono)", r.s === 429 && /altra rete/.test(r.j.errore) && /telefono/.test(r.j.errore), r.j);
  // oltre 60 errori da una rete la password giusta entra lo stesso, finita l'attesa (prima: 429 per 24 ore)
  const ipN = nuovoIp(), impN = (await L_.impronta(q("SELECT v FROM config WHERE k = 'segreto'")[0].v, "ip", L_.chiaveRete(ipN)));
  for (let i = 0; i < 70; i++) env.DB._db.exec(`INSERT INTO accessi (quando, esito, dispositivo, luogo, ip) VALUES ('${new Date(adesso - (180 - i) * 60000).toISOString().replace(/\.\d{3}Z$/, "Z")}', 'errore', 'x|pc', NULL, '${impN}')`);
  avanti(61 * 60);
  r = await red("POST", "/api/redazione/accesso", { corpo: { utente: UT, password: PW }, ip: ipN });
  verifica("tentativi: oltre 60 errori da una rete, finita l'attesa (60 minuti) la password giusta entra", r.s === 200, r.s);
  // quanto costa a D1 un tentativo fallito: un indice solo sugli accessi (ogni indice è una riga scritta in più)
  const indici = env.DB._db.prepare("PRAGMA index_list(accessi)").all().map((x) => x.name).filter((x) => !x.startsWith("sqlite_"));
  verifica("D1: sugli accessi un solo indice (ogni indice è una riga scritta in più a ogni tentativo)", indici.length === 1 && indici[0] === "accessi_ip", indici);
  // oltre il tetto giornaliero delle righe di errori, le reti nuove si contano insieme, senza una riga ciascuna
  const tettoVero = AREA.errori_giorno;
  const righeErr = () => q("SELECT COUNT(*) AS n FROM accessi WHERE esito = 'errore'")[0].n;
  if (typeof tettoVero === "number") AREA.errori_giorno = 0;
  const primaR = righeErr(), primaT = (await red("GET", "/api/redazione/riepilogo", { cookie: r.set.length ? COOKIE + "=" + tokenDa(r.set) : "" })).j;
  const reti50 = Array.from({ length: 50 }, () => nuovoIp());
  for (const ip of reti50) await sbaglia(ip);
  avanti(61); await sbaglia(nuovoIp());
  const dopoR = righeErr();
  const sessN = COOKIE + "=" + tokenDa(r.set);
  const dopoT = (await red("GET", "/api/redazione/riepilogo", { cookie: sessN })).j;
  verifica("D1: oltre il tetto, 51 tentativi da 51 reti nuove non scrivono 51 righe (si contano insieme)", dopoR - primaR === 0 && q("SELECT COUNT(*) AS n FROM tentativi_ora")[0].n <= 2, [dopoR - primaR]);
  verifica("D1: oltre il tetto i tentativi si contano lo stesso nella Panoramica", dopoT.tentativi && dopoT.tentativi.n - (primaT.tentativi ? primaT.tentativi.n : 0) >= 51, [primaT.tentativi, dopoT.tentativi]);
  await sbaglia(ipM); r = await sbaglia(ipM);
  verifica("D1: oltre il tetto le reti già viste restano frenate (attesa che raddoppia)", r.s === 429, r.s);
  if (typeof tettoVero === "number") AREA.errori_giorno = tettoVero;

  // ------------------------------------------------- esci, esci da tutti, una sessione alla volta
  const e4 = await entra(), e5 = await entra();
  r = await red("POST", "/api/redazione/esci", { corpo: {}, cookie: e4.cookie, csrf: e4.csrf });
  verifica("esci: chiude la sessione sul server e cancella i cookie", r.s === 200 && r.set.some((x) => x.startsWith(COOKIE + "=;") && /Max-Age=0/.test(x)) && r.set.some((x) => x.startsWith(SPIA + "=;")), r.set);
  r = await red("GET", "/redazione/registro.json", { cookie: e4.cookie });
  verifica("esci: il vecchio cookie non vale più (sessione di un altro rubata dopo l'uscita)", r.s === 404, r.s);
  r = await red("GET", "/api/redazione/sessione", { cookie: e5.cookie });
  verifica("esci: le altre sessioni restano", r.s === 200, r.s);
  r = await red("GET", "/api/redazione/sicurezza", { cookie: e5.cookie });
  const corto = r.j.sessioni.find((x) => !x.questa).id;
  verifica("sicurezza: ultimi accessi, sessioni e regole, senza impronte né gettoni", r.s === 200 && r.j.accessi.length > 0 && r.j.errori.length > 0 && r.j.sessioni.some((x) => x.questa)
    && !JSON.stringify(r.j).includes(e5.t) && !("ip" in r.j.accessi[0]) && r.j.regole.iterazioni === AREA.iterazioni, r.j.sessioni);
  verifica("sicurezza: il dispositivo in parole", dispositivo("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit Version/18.0 Mobile/15E148 Safari/604.1").testo === "Safari su iPhone"
    && dispositivo("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36 Edg/130.0").testo === "Edge su Windows" && dispositivo("curl/8").tipo === "altro");
  r = await red("POST", "/api/redazione/sessioni/" + corto + "/esci", { corpo: {}, cookie: e5.cookie, csrf: e5.csrf });
  verifica("sicurezza: Esci su un altro dispositivo chiude solo quello", r.s === 200 && !r.j.questa && (await red("GET", "/api/redazione/sessione", { cookie: e5.cookie })).s === 200, r);
  const e6 = await entra();
  r = await red("POST", "/api/redazione/esci-tutti", { corpo: {}, cookie: e6.cookie, csrf: e6.csrf });
  const dopo = await Promise.all([e5, e6, e3].map((x) => red("GET", "/api/redazione/sessione", { cookie: x.cookie })));
  verifica("esci da tutti: nessuna sessione vale più, nemmeno questa", r.s === 200 && dopo.every((x) => x.s === 401) && q("SELECT COUNT(*) AS n FROM sessioni")[0].n === 0, dopo.map((x) => x.s));

  // ------------------------------------------------- cambio password e recupero dal segreto
  // mai più di una derivazione PBKDF2 per richiesta (10 ms di CPU sul piano gratuito): il cambio si fa in due passi,
  // verifica della vecchia (prova a tempo) e scrittura della nuova, con impronta e sessioni nello stesso batch
  let derivazioni = 0;
  const deriveVero = crypto.subtle.deriveBits.bind(crypto.subtle);
  crypto.subtle.deriveBits = (...a) => { derivazioni++; return deriveVero(...a); };
  const contaDer = async (f) => { derivazioni = 0; const x = await f(); return [x, derivazioni]; };
  async function cambia(sess, attuale, nuova, conferma = nuova) {
    const v = await red("POST", "/api/redazione/password/verifica", { corpo: { attuale, nuova, conferma }, cookie: sess.cookie, csrf: sess.csrf });
    if (v.s !== 200) return v;
    return red("POST", "/api/redazione/password", { corpo: { prova: v.j.prova, nuova, conferma }, cookie: sess.cookie, csrf: sess.csrf });
  }
  const NUOVA = "un'altra frase lunga, scelta dall'area";
  const p1 = await entra(), p2 = await entra();
  for (const [args, atteso, nome] of [[[PW, "corta"], 400, "troppo corta"], [[PW, NUOVA, NUOVA + "x"], 400, "conferma diversa"], [[PW, PW], 400, "uguale all'attuale"],
                                      [[PW, " ".repeat(20)], 400, "soli spazi"], [[PW, "a".repeat(20)], 400, "un solo carattere ripetuto"],
                                      [["non è questa la password", NUOVA], 403, "attuale sbagliata (403, non 401: la sessione resta)"]]) {
    r = await cambia(p1, ...args);
    verifica("password: " + nome + ": rifiutata", r.s === atteso, r);
  }
  r = await red("POST", "/api/redazione/password", { corpo: { attuale: PW, nuova: NUOVA, conferma: NUOVA }, cookie: p1.cookie, csrf: p1.csrf });
  verifica("password: senza la prova della verifica non si cambia (nemmeno con la password attuale nel corpo)", r.s === 403, r);
  const vAltra = await red("POST", "/api/redazione/password/verifica", { corpo: { attuale: PW, nuova: NUOVA }, cookie: p2.cookie, csrf: p2.csrf });
  r = await red("POST", "/api/redazione/password", { corpo: { prova: vAltra.j.prova, nuova: NUOVA, conferma: NUOVA }, cookie: p1.cookie, csrf: p1.csrf });
  verifica("password: la prova di un'altra sessione non vale", vAltra.s === 200 && r.s === 403, r);
  const vVecchia = await red("POST", "/api/redazione/password/verifica", { corpo: { attuale: PW, nuova: NUOVA }, cookie: p1.cookie, csrf: p1.csrf });
  avanti(301);
  r = await red("POST", "/api/redazione/password", { corpo: { prova: vVecchia.j.prova, nuova: NUOVA, conferma: NUOVA }, cookie: p1.cookie, csrf: p1.csrf });
  verifica("password: la prova scade dopo 5 minuti", r.s === 403, r);
  const pPar = await entra({ ip: "77.7.7.7" });
  env.DB.latenza = 4;
  await Promise.all(Array.from({ length: 300 }, (x, i) => red("POST", "/api/redazione/password/verifica", { corpo: { attuale: "tentativo " + i, nuova: NUOVA }, cookie: pPar.cookie, csrf: pPar.csrf, ip: "77.7.7.7" })));
  env.DB.latenza = 0;
  const provateV = q("SELECT COUNT(*) AS n FROM accessi WHERE esito = 'errore' AND quando = (SELECT MAX(quando) FROM accessi)")[0].n;
  verifica("password: 300 verifiche insieme con una sessione valida provano al massimo 5 password", provateV <= AREA.errori_liberi, provateV);
  const lotti = [], batchVero = env.DB.batch;
  env.DB.batch = async (lista) => { lotti.push(lista.map((x) => x._sql || "")); return batchVero(lista); };
  r = await cambia(p1, PW, NUOVA);
  env.DB.batch = batchVero;
  const cfgPw = JSON.parse(q("SELECT v FROM config WHERE k = 'password'")[0].v);
  verifica("password: cambiata, in D1 solo l'impronta PBKDF2 con sale", r.s === 200 && /^pbkdf2-sha256\$50000\$[A-Za-z0-9_-]{22}\$[A-Za-z0-9_-]{43}$/.test(cfgPw.h) && !JSON.stringify(cfgPw).includes(NUOVA), cfgPw);
  verifica("password: impronta nuova e sessioni nello stesso batch (se il Worker si ferma, o tutto o niente)", lotti.some((l) => l.some((x) => /INSERT INTO config/.test(x)) && l.some((x) => /DELETE FROM sessioni/.test(x))), lotti);
  verifica("password: questa sessione resta, le altre si chiudono", (await red("GET", "/api/redazione/sessione", { cookie: p1.cookie })).s === 200 && (await red("GET", "/api/redazione/sessione", { cookie: p2.cookie })).s === 401);
  const NUOVA2 = "una terza frase, ancora più lunga";
  const vUsata = await red("POST", "/api/redazione/password/verifica", { corpo: { attuale: NUOVA, nuova: "di nuovo una frase lunga" }, cookie: p1.cookie, csrf: p1.csrf });
  let [rv1, d1n] = await contaDer(() => red("POST", "/api/redazione/password/verifica", { corpo: { attuale: NUOVA, nuova: NUOVA2 }, cookie: p1.cookie, csrf: p1.csrf }));
  let [rv2, d2n] = await contaDer(() => red("POST", "/api/redazione/password", { corpo: { prova: rv1.j.prova, nuova: NUOVA2, conferma: NUOVA2 }, cookie: p1.cookie, csrf: p1.csrf }));
  let [rv3, d3n] = await contaDer(() => red("POST", "/api/redazione/accesso", { corpo: { utente: UT, password: NUOVA2 }, ip: nuovoIp() }));
  verifica("CPU: al massimo una derivazione per richiesta (verifica, scrittura, accesso con l'impronta)", rv1.s === 200 && rv2.s === 200 && rv3.s === 200 && d1n <= 1 && d2n <= 1 && d3n <= 1, [rv1.s, rv2.s, rv3.s, d1n, d2n, d3n]);
  r = await red("POST", "/api/redazione/password", { corpo: { prova: vUsata.j.prova, nuova: "di nuovo una frase lunga", conferma: "di nuovo una frase lunga" }, cookie: p1.cookie, csrf: p1.csrf });
  const vScambio = await red("POST", "/api/redazione/password/verifica", { corpo: { attuale: NUOVA2, nuova: "la frase che ho confermato io" }, cookie: p1.cookie, csrf: p1.csrf });
  const rScambio = await red("POST", "/api/redazione/password", { corpo: { prova: vScambio.j.prova, nuova: "un'altra frase messa al suo posto", conferma: "un'altra frase messa al suo posto" }, cookie: p1.cookie, csrf: p1.csrf });
  verifica("password: la prova vale solo per la nuova password controllata nel primo passo", vScambio.s === 200 && rScambio.s === 403, rScambio.s);
  verifica("password: una prova di prima del cambio non vale più", r.s === 403, r);
  crypto.subtle.deriveBits = deriveVero;
  verifica("password: la vecchia non entra più, la nuova sì", (await entra({ password: NUOVA })).r.s === 401 && (await entra({ password: NUOVA2 })).r.s === 200);
  const cfgPw2 = JSON.parse(q("SELECT v FROM config WHERE k = 'password'")[0].v);
  verifica("password: verifica dell'impronta", await verificaImpronta(NUOVA2, cfgPw2.h) && !(await verificaImpronta(NUOVA2 + " ", cfgPw2.h)) && !(await verificaImpronta(NUOVA2, "pbkdf2-sha256$900000$" + cfgPw2.h.split("$").slice(2).join("$"))));
  verifica("password: due impronte della stessa password sono diverse (sale)", (await improntaPassword("stessa password lunga", 1000)) !== (await improntaPassword("stessa password lunga", 1000)));
  verifica("confronto a tempo costante: uguali solo se identici", uguali("abc", "abc") && !uguali("abc", "abd") && !uguali("abc", "abcd") && !uguali("", "a"));
  verifica("CSRF: in D1 il gettone anti-CSRF non c'è (si ricava dal gettone di sessione)", !JSON.stringify(q("SELECT * FROM sessioni")).includes(p1.csrf));
  // Paolo dimentica la password: cambia il segreto REDAZIONE_PASSWORD su Cloudflare (con un valore diverso), e vince il segreto
  const p3 = await entra({ password: NUOVA2 });
  env.REDAZIONE_PASSWORD = "il segreto nuovo, messo da Cloudflare";
  r = await red("GET", "/api/redazione/sessione", { cookie: p3.cookie });
  verifica("recupero: cambiato il segreto, le sessioni di prima non valgono più e spariscono da D1 (e dai Dispositivi collegati)", r.s === 401 && q("SELECT COUNT(*) AS n FROM sessioni")[0].n === 0, [r.s, q("SELECT COUNT(*) AS n FROM sessioni")[0].n]);
  verifica("recupero: la password dell'area non entra più, il segreto nuovo sì", (await entra({ password: NUOVA2 })).r.s === 401 && (await entra({ password: env.REDAZIONE_PASSWORD })).r.s === 200
    && q("SELECT COUNT(*) AS n FROM config WHERE k = 'password'")[0].n === 0);
  env.REDAZIONE_PASSWORD = PW;
  const R1 = await entra();
  verifica("recupero: tornando al segreto di prima si entra con quello (l'impronta vecchia non torna)", R1.r.s === 200);
  // cambia solo il nome utente: le sessioni si chiudono, la password dell'area resta (non torna valido il segreto vecchio)
  const NUOVA3 = "la password scelta dall'area, prima del nome";
  r = await cambia(R1, PW, NUOVA3);
  const pU = await entra({ password: NUOVA3 });
  env.REDAZIONE_UTENTE = "nome-nuovo-di-paolo";
  const rU1 = await red("GET", "/api/redazione/sessione", { cookie: pU.cookie });
  const rU2 = await red("POST", "/api/redazione/accesso", { corpo: { utente: "nome-nuovo-di-paolo", password: PW }, ip: nuovoIp() });
  const rU3 = await red("POST", "/api/redazione/accesso", { corpo: { utente: "nome-nuovo-di-paolo", password: NUOVA3 }, ip: nuovoIp() });
  verifica("utente: cambiato solo il nome, le sessioni si chiudono, la password dell'area resta e il segreto vecchio non torna",
    r.s === 200 && rU1.s === 401 && rU2.s === 401 && rU3.s === 200, [r.s, rU1.s, rU2.s, rU3.s]);
  env.REDAZIONE_UTENTE = UT;
  env.DB._db.exec("DELETE FROM config WHERE k = 'password'"); env.DB._db.exec("DELETE FROM sessioni");
  const R1b = await entra();
  const S1 = { cookie: R1b.cookie, csrf: R1b.csrf };

  // ------------------------------------------------- la Gommunity dalla redazione
  avanti(10);
  const g5 = (await chiama("GET", "/api/lettori/031")).j.gettone; avanti(5);
  const L1 = { lettore: "lettore-redaz-111111111", ip: "21.1.1.1" }, L2 = { lettore: "lettore-redaz-222222222", ip: "21.2.2.2" }, L3 = { lettore: "lettore-redaz-333333333", ip: "21.3.3.3" };
  const scriviL = async (L, nome, testo, extra = {}) => chiama("POST", "/api/lettori/031/commenti", { ...L, corpo: { nome, testo, gettone: g5, ...extra } });
  r = await scriviL(L1, "Wanda Plusvalenza", "Comprate tutto, info su borsa-facile punto xyz 100% garantito");
  const idW = r.j.commento.id;
  r = await scriviL(L2, "Ted Spread", "Rimbalzo su volumi sottili: lo prendo con le pinze. Anche l'_underscore_ e il 50% contano");
  const idT = r.j.commento.id;
  for (const nome of ["Gommberg", "GOMMBERG", "G0mmberg", "Gornmberg", "Gommberg!", "La Redazione", "gommberg.com"]) {
    r = await scriviL(L3, nome, "Mi firmo come la redazione " + nome);
    verifica("firma: un lettore non può firmarsi " + JSON.stringify(nome), r.s === 400 && /riservato/.test(r.j.errore), r);
  }
  r = await scriviL(L3, "Lettore Furbo", "Provo a mettere il badge", { redazione: 1, fissato: "2026-01-01T00:00:00Z" });
  const idF = r.j.commento && r.j.commento.id;
  let pubblica = (await chiama("GET", "/api/lettori/031")).j;
  verifica("firma: i campi redazione e fissato mandati da un lettore non contano", r.s === 201 && pubblica.commenti.find((x) => x.id === idF).redazione === false && !pubblica.commenti.find((x) => x.id === idF).fissato);
  r = await red("POST", "/api/redazione/commenti", { corpo: { ed: 31, testo: "Buongiorno a tutti: oggi Wall Street chiude alle 19." }, ...S1 });
  const idG = r.j.commento.id;
  verifica("firma: la redazione scrive come Gommberg, con il badge", r.s === 201 && r.j.commento.nome === "Gommberg" && r.j.commento.redazione === true);
  r = await red("POST", "/api/redazione/commenti", { corpo: { ed: 31, testo: "Giusto, guardiamo i volumi.", padre: idT }, ...S1 });
  verifica("firma: la redazione risponde a un lettore", r.s === 201 && r.j.commento.padre === idT);
  r = await red("POST", "/api/redazione/commenti", { corpo: { ed: 99, testo: "Edizione che non c'è" }, ...S1 });
  verifica("firma: su un'edizione inesistente no", r.s === 404, r.s);
  pubblica = (await chiama("GET", "/api/lettori/031")).j;
  const gp = pubblica.commenti.find((x) => x.id === idG);
  verifica("firma: i lettori vedono il commento di Gommberg con redazione: true, i loro con false", gp && gp.redazione === true && gp.nome === "Gommberg" && pubblica.commenti.filter((x) => x.redazione).every((x) => x.nome === "Gommberg"));
  r = await chiama("POST", "/api/lettori/commenti/" + idG + "/segnala", { ...L2, corpo: { gettone: g5 } });
  verifica("firma: i commenti della redazione non si nascondono con le segnalazioni", r.s === 200 && r.j.nascosto === false && q("SELECT segnalazioni FROM commenti WHERE id = " + idG)[0].segnalazioni === 0, r);
  // modifica: solo i suoi
  r = await red("POST", "/api/redazione/commenti/" + idT + "/modifica", { corpo: { testo: "Testo cambiato dalla redazione" }, ...S1 });
  verifica("modifica: i commenti dei lettori non si modificano", r.s === 403 && q("SELECT testo FROM commenti WHERE id = " + idT)[0].testo.startsWith("Rimbalzo"), r);
  r = await red("POST", "/api/redazione/commenti/" + idG + "/modifica", { corpo: { testo: "Buongiorno: oggi Wall Street chiude alle 19:00." }, ...S1 });
  verifica("modifica: la redazione modifica i suoi, con la data della modifica", r.s === 200 && r.j.testo.endsWith("19:00.") && !!r.j.modificato);
  r = await red("POST", "/api/redazione/commenti/" + idG + "/modifica", { corpo: { testo: "x".repeat(700) }, ...S1 });
  verifica("modifica: le stesse regole dei commenti (lunghezza)", r.s === 400, r.s);
  // segnalazioni, elenco e filtri
  for (const L of [L2, L3, { lettore: "lettore-redaz-444444444", ip: "21.4.4.4" }]) await chiama("POST", "/api/lettori/commenti/" + idW + "/segnala", { ...L, corpo: { gettone: g5 } });
  verifica("segnalazioni: tre reti nascondono il commento", q("SELECT nascosto FROM commenti WHERE id = " + idW)[0].nascosto === 1);
  r = await red("GET", "/api/redazione/commenti?filtro=guardare", S1);
  verifica("Gommunity: Da guardare mostra il commento nascosto dalle segnalazioni, con il testo", r.s === 200 && r.j.commenti.length >= 1 && r.j.commenti[0].id === idW && r.j.commenti[0].testo.includes("borsa-facile") && r.j.commenti[0].stato === "nascosto", r.j.commenti);
  const tutto = JSON.stringify(r.j) + JSON.stringify((await red("GET", "/api/redazione/commenti", S1)).j);
  const impronte = q("SELECT autore, ip FROM commenti WHERE ip IS NOT NULL LIMIT 5");
  verifica("Gommunity: l'elenco non contiene mai le impronte dei lettori né le reti", impronte.every((x) => !tutto.includes(x.autore) && !tutto.includes(x.ip)));
  r = await red("GET", "/api/redazione/commenti", S1);
  verifica("Gommunity: tutti i commenti, i da guardare per primi, e i conteggi", r.j.commenti[0].id === idW && r.j.conti.tutti >= 5 && r.j.conti.guardare >= 1 && r.j.conti.redazione === 2 && typeof r.j.misure.commenti_7 === "number", r.j.conti);
  r = await red("GET", "/api/redazione/commenti?filtro=redazione", S1);
  verifica("Gommunity: filtro Redazione", r.j.commenti.length === 2 && r.j.commenti.every((x) => x.redazione));
  r = await red("GET", "/api/redazione/commenti?ed=30", S1);
  verifica("Gommunity: filtro per edizione", r.j.commenti.every((x) => x.ed === 30));
  r = await red("GET", "/api/redazione/commenti?q=" + encodeURIComponent("ted"), S1);
  verifica("Gommunity: cerca per nome", r.j.commenti.some((x) => x.id === idT) && r.j.commenti.every((x) => /ted/i.test(x.nome + x.testo)));
  for (const [qq, nome] of [["50%", "il segno %"], ["_underscore_", "il segno _"], ["' OR 1=1 --", "un'iniezione SQL"], ['"); DROP TABLE commenti; --', "un DROP"], ["%", "solo %"], ["\\", "una barra"]]) {
    r = await red("GET", "/api/redazione/commenti?q=" + encodeURIComponent(qq), S1);
    verifica("Gommunity: cerca " + nome + " senza errori e alla lettera", r.s === 200 && r.j.commenti.every((x) => (x.nome + x.testo).toLowerCase().includes(qq.toLowerCase())), [r.s, r.j.commenti && r.j.commenti.length]);
  }
  verifica("Gommunity: dopo le iniezioni la tabella c'è ancora", q("SELECT COUNT(*) AS n FROM commenti")[0].n > 5);
  for (const x of ["filtro=tutto", "ed=1;DROP", "ed=99999", "q=" + "x".repeat(61), "da=-1", "id=abc", "filtro=guardare%27"]) {
    r = await red("GET", "/api/redazione/commenti?" + x, S1);
    verifica("Gommunity: filtro non valido " + x.slice(0, 20) + ": 400", r.s === 400, r.s);
  }
  r = await red("GET", "/api/redazione/commenti?id=" + idW, S1);
  verifica("Gommunity: il link dell'avviso apre un commento solo", r.j.commenti.length === 1 && r.j.commenti[0].id === idW);
  r = await red("GET", "/api/redazione/lettore?commento=" + idW, S1);
  verifica("Gommunity: chi l'ha scritto, con i suoi nomi e senza impronte", r.s === 200 && r.j.nome === "Wanda Plusvalenza" && r.j.nomi.some((x) => x.nome === "Wanda Plusvalenza") && !JSON.stringify(r.j).includes(impronte[0].autore), r.j);
  // azioni
  r = await red("POST", "/api/redazione/commenti/" + idW + "/rimetti", { corpo: {}, ...S1 });
  verifica("rimetti: torna visibile e le segnalazioni si azzerano", r.s === 200 && r.j.stato === "visibile" && (await chiama("GET", "/api/lettori/031")).j.commenti.some((x) => x.id === idW) && q("SELECT COUNT(*) AS n FROM segnalazioni WHERE commento = " + idW)[0].n === 0);
  r = await red("POST", "/api/redazione/commenti/" + idW + "/rimetti", { corpo: {}, ...S1 });
  verifica("rimetti: su un commento già visibile non fa nulla", r.s === 409, r.s);
  r = await red("POST", "/api/redazione/commenti/" + idW + "/togli", { corpo: {}, ...S1 });
  verifica("togli: sparisce per i lettori, resta per la redazione", r.s === 200 && r.j.stato === "tolto" && !(await chiama("GET", "/api/lettori/031")).j.commenti.some((x) => x.id === idW) && (await red("GET", "/api/redazione/commenti?filtro=nascosti", S1)).j.commenti.some((x) => x.id === idW));
  await chiama("POST", "/api/lettori/commenti/" + idT + "/segnala", { ...L3, corpo: { gettone: g5 } });
  r = await red("POST", "/api/redazione/commenti/" + idT + "/azzera", { corpo: {}, ...S1 });
  verifica("azzera: le segnalazioni di un commento visibile si azzerano e lo dice il tempo di decisione", r.s === 200 && q("SELECT segnalazioni, deciso, attesa FROM commenti WHERE id = " + idT)[0].segnalazioni === 0 && q("SELECT attesa FROM commenti WHERE id = " + idT)[0].attesa !== null
    && (await red("GET", "/api/redazione/commenti", S1)).j.misure.decisioni >= 1);
  r = await red("POST", "/api/redazione/commenti/" + idT + "/fissa", { corpo: {}, ...S1 });
  pubblica = (await chiama("GET", "/api/lettori/031")).j;
  verifica("fissa: il commento esce fissato in alto per tutti", r.s === 200 && !!pubblica.commenti.find((x) => x.id === idT).fissato);
  const risposta = pubblica.commenti.find((x) => x.padre === idT);
  r = await red("POST", "/api/redazione/commenti/" + risposta.id + "/fissa", { corpo: {}, ...S1 });
  verifica("fissa: le risposte no", r.s === 400, r.s);
  r = await red("POST", "/api/redazione/commenti/" + idT + "/sgancia", { corpo: {}, ...S1 });
  verifica("sgancia: non più fissato", r.s === 200 && !(await chiama("GET", "/api/lettori/031")).j.commenti.find((x) => x.id === idT).fissato);
  r = await red("POST", "/api/redazione/commenti/999999/togli", { corpo: {}, ...S1 });
  verifica("azioni: su un commento che non c'è, 404", r.s === 404, r.s);
  r = await red("POST", "/api/redazione/commenti/" + idT + "/cancella", { corpo: {}, ...S1 });
  verifica("azioni: un'azione sconosciuta non fa nulla", r.s === 404, r.s);
  // blocco di un lettore: codice del browser e rete
  r = await red("POST", "/api/redazione/lettori/blocca", { corpo: { commento: idW }, ...S1 });
  verifica("blocca: browser e rete", r.s === 200 && r.j.bloccato && r.j.rete, r.j);
  const g6 = (await chiama("GET", "/api/lettori/031", L1)).j.gettone; avanti(5);
  for (const [nome, chi] of [["dal suo browser", L1], ["dalla sua rete, con un altro browser", { lettore: "lettore-redaz-555555555", ip: L1.ip }], ["con il suo browser da un'altra rete", { lettore: L1.lettore, ip: "21.9.9.9" }]]) {
    r = await chiama("POST", "/api/lettori/031/commenti", { ...chi, corpo: { nome: "Nuovo Nome " + nome.length, testo: "Riprovo " + nome, gettone: g6 } });
    verifica("blocca: niente commenti " + nome, r.s === 403, r);
  }
  r = await chiama("POST", "/api/lettori/031/voto", { ...L1, corpo: { voto: "toro", gettone: g6 } });
  const r3 = await chiama("POST", "/api/lettori/commenti/" + idT + "/piace", { ...L1, corpo: { gettone: g6 } });
  const r4 = await chiama("POST", "/api/lettori/commenti/" + idT + "/segnala", { ...L1, corpo: { gettone: g6 } });
  verifica("blocca: niente voti, like e segnalazioni", r.s === 403 && r3.s === 403 && r4.s === 403, [r.s, r3.s, r4.s]);
  r = await chiama("POST", "/api/lettori/031/commenti", { lettore: "lettore-redaz-666666666", ip: "21.6.6.6", corpo: { nome: "Lettrice Libera", testo: "Io scrivo", gettone: g6 } });
  verifica("blocca: gli altri lettori scrivono", r.s === 201, r);
  const scadeRete = q("SELECT scade FROM bloccati WHERE tipo = 'ip' ORDER BY creato DESC LIMIT 1")[0].scade, creatoW = q("SELECT creato FROM commenti WHERE id = " + idW)[0].creato;
  verifica("privacy: il blocco di rete scade 30 giorni dopo il commento (l'impronta della rete non resta oltre)", Date.parse(scadeRete) <= Date.parse(creatoW) + AREA.blocco_rete_giorni * 86400000 + 1000, [scadeRete, creatoW]);
  avanti(AREA.blocco_rete_giorni * 86400 + 60);
  const g7 = (await chiama("GET", "/api/lettori/031", L1)).j.gettone; avanti(5);
  r = await chiama("POST", "/api/lettori/031/commenti", { lettore: "lettore-redaz-777777777", ip: L1.ip, corpo: { nome: "Dopo Un Mese", testo: "Stessa rete, un mese dopo", gettone: g7 } });
  const r5 = await chiama("POST", "/api/lettori/031/commenti", { ...L1, ip: "21.8.8.8", corpo: { nome: "Wanda Plusvalenza", testo: "Il browser bloccato resta bloccato", gettone: g7 } });
  verifica("blocca: la rete si libera dopo 30 giorni, il browser no", r.s === 201 && r5.s === 403, [r.s, r5.s]);
  r = await red("POST", "/api/redazione/lettori/sblocca", { corpo: { commento: idW }, ...S1 });
  const r6 = await chiama("POST", "/api/lettori/031/commenti", { ...L1, ip: "21.8.8.8", corpo: { nome: "Wanda Plusvalenza", testo: "Sbloccata, torno a scrivere", gettone: g7 } });
  verifica("sblocca: il lettore torna a scrivere", r.s === 200 && r6.s === 201, [r.s, r6]);
  r = await red("POST", "/api/redazione/lettori/blocca", { corpo: { commento: idG }, ...S1 });
  verifica("blocca: la redazione non si blocca", r.s === 400, r.s);
  // un commento di prima che le reti fossero IPv4 o /64: l'impronta salvata è dell'indirizzo intero, il blocco di rete è incerto
  env.DB._db.exec("INSERT INTO config (k, v) VALUES ('rete64', '" + new Date(adesso).toISOString().replace(/\.\d{3}Z$/, "Z") + "') ON CONFLICT (k) DO UPDATE SET v = excluded.v");
  env.DB._db.exec("INSERT INTO commenti (sito, ed, nome, testo, creato, autore, ip) VALUES ('gommberg', 31, 'Vecchio Commento', 'Scritto prima', '" + new Date(adesso - 3600000).toISOString().replace(/\.\d{3}Z$/, "Z") + "', 'autore-vecchio', 'impronta-vecchia')");
  const idV = q("SELECT id FROM commenti WHERE autore = 'autore-vecchio'")[0].id;
  r = await red("POST", "/api/redazione/lettori/blocca", { corpo: { commento: idV }, ...S1 });
  verifica("blocca: per un commento di prima della regola /64 la rete è dichiarata incerta, non bloccata", r.s === 200 && r.j.rete === "incerta", r.j);
  // libera un nome
  r = await red("POST", "/api/redazione/nomi/libera", { corpo: { commento: idW, nome: "wanda  plusvalenza" }, ...S1 });
  const r7 = await chiama("POST", "/api/lettori/031/commenti", { ...L2, corpo: { nome: "Wanda Plusvalenza", testo: "Il nome adesso è mio", gettone: g7 } });
  verifica("libera: il nome torna libero e un altro lettore lo prende", r.s === 200 && r.j.liberati === 1 && r7.s === 201, [r.j, r7.s]);
  // chiudere e riaprire una discussione
  r = await red("POST", "/api/redazione/edizioni/31/chiudi", { corpo: {}, ...S1 });
  pubblica = (await chiama("GET", "/api/lettori/031")).j;
  const r8 = await chiama("POST", "/api/lettori/031/commenti", { ...L3, corpo: { nome: "Lettore Furbo", testo: "Scrivo lo stesso", gettone: g7 } });
  const r9 = await red("POST", "/api/redazione/commenti", { corpo: { ed: 31, testo: "La redazione scrive anche a discussione chiusa." }, ...S1 });
  verifica("chiudi: i lettori leggono e non scrivono, la redazione sì", r.s === 200 && pubblica.chiusa === true && r8.s === 409 && r9.s === 201, [pubblica.chiusa, r8.s, r9.s]);
  r = await red("GET", "/api/redazione/discussioni", S1);
  verifica("discussioni: l'elenco per edizione dice quale è chiusa", r.s === 200 && r.j.edizioni.find((x) => x.ed === 31).chiusa && r.j.ultima === 31);
  r = await red("POST", "/api/redazione/edizioni/31/riapri", { corpo: {}, ...S1 });
  const r10 = await chiama("POST", "/api/lettori/031/commenti", { ...L3, corpo: { nome: "Lettore Furbo", testo: "Adesso sì", gettone: g7 } });
  verifica("riapri: i lettori tornano a scrivere", r.s === 200 && r10.s === 201 && (await chiama("GET", "/api/lettori/031")).j.chiusa === false, r10);
  r = await red("GET", "/api/redazione/riepilogo", S1);
  verifica("riepilogo: segnalazioni, commenti e voti di oggi, ultimi commenti", r.s === 200 && r.j.edizione === 31 && typeof r.j.guardare === "number" && r.j.commenti_oggi > 0 && Array.isArray(r.j.ultimi) && r.j.ultimi.length === 3, r.j);
  // una lettura che non va: la pagina dice "accesso richiesto", mai un errore del server con dettagli
  r = await red("GET", "/api/redazione/inesistente", S1);
  verifica("redazione: indirizzo sconosciuto: 404", r.s === 404, r.s);
  r = await red("PUT", "/api/redazione/commenti", S1);
  verifica("redazione: metodo non ammesso: 405", r.s === 405, r.s);
  // la rete è l'IPv4 intero o i primi 64 bit dell'IPv6: con IPv6 ogni casa ha 2^64 indirizzi, e cambiarli non deve
  // aggirare né l'attesa dei tentativi né "Blocca il lettore (browser e rete)"
  const cr = L_.chiaveRete || (() => null);
  verifica("rete: due indirizzi IPv6 della stessa /64 sono la stessa rete, di un'altra /64 no; IPv4 intero",
    cr("2001:db8:1:2:aaaa::1") === cr("2001:0db8:0001:0002:ffff:ffff:ffff:ffff") && cr("2001:db8:1:2::9") !== cr("2001:db8:1:3::9")
    && cr("::ffff:192.0.2.7") === cr("192.0.2.7") && cr("192.0.2.7") !== cr("192.0.2.8") && cr("2001:DB8:1:2::1%eth0") === cr("2001:db8:1:2::1"), [cr("2001:db8:1:2:aaaa::1"), cr("::ffff:192.0.2.7")]);
  for (let i = 0; i < AREA.errori_liberi; i++) await red("POST", "/api/redazione/accesso", { corpo: { utente: UT, password: "sbagliata " + i }, ip: "2001:db8:77:1::" + (i + 1).toString(16) });
  r = await red("POST", "/api/redazione/accesso", { corpo: { utente: UT, password: PW }, ip: "2001:db8:77:1:dead:beef:0:1" });
  verifica("rete: cambiare indirizzo dentro la stessa /64 non azzera l'attesa dei tentativi", r.s === 429, r.s);
  const g8 = (await chiama("GET", "/api/lettori/031")).j.gettone; avanti(5);
  r = await chiama("POST", "/api/lettori/031/commenti", { lettore: "lettore-ipv6-aaaaaaaaa", ip: "2001:db8:99:5::1", corpo: { nome: "Sei Bit", testo: "Scrivo da IPv6", gettone: g8 } });
  await red("POST", "/api/redazione/lettori/blocca", { corpo: { commento: r.j.commento.id }, ...S1 });
  r = await chiama("POST", "/api/lettori/031/commenti", { lettore: "lettore-ipv6-bbbbbbbbb", ip: "2001:db8:99:5:1234:5678:9abc:def0", corpo: { nome: "Altro Browser", testo: "Stessa casa, indirizzo nuovo", gettone: g8 } });
  verifica("rete: un lettore bloccato non rientra cambiando indirizzo IPv6 e browser nella stessa /64", r.s === 403, r);
  // privacy: gli accessi (con l'impronta della rete) si cancellano dopo 30 giorni, come promette privacy.html
  env.DB._db.exec("INSERT INTO accessi (quando, esito, dispositivo, luogo, ip) VALUES ('" + new Date(adesso - 31 * 86400000).toISOString().replace(/\.\d{3}Z$/, "Z") + "', 'ok', 'x|pc', NULL, 'vecchia-impronta')");
  avanti(86400);
  await chiama("GET", "/api/lettori/031");
  verifica("privacy: gli accessi oltre i 30 giorni si cancellano con la pulizia di ogni giorno", q("SELECT COUNT(*) AS n FROM accessi WHERE ip = 'vecchia-impronta'")[0].n === 0);
  // il database già in linea, senza le colonne nuove: si aggiornano da sole alla prima richiesta
  const vecchio = d1();
  vecchio._db.exec(`CREATE TABLE commenti (id INTEGER PRIMARY KEY AUTOINCREMENT, sito TEXT NOT NULL, ed INTEGER NOT NULL, padre INTEGER, nome TEXT NOT NULL,
    testo TEXT NOT NULL, creato TEXT NOT NULL, autore TEXT NOT NULL, ip TEXT, piace INTEGER NOT NULL DEFAULT 0, segnalazioni INTEGER NOT NULL DEFAULT 0, nascosto INTEGER NOT NULL DEFAULT 0)`);
  vecchio._db.exec("INSERT INTO commenti (sito, ed, nome, testo, creato, autore) VALUES ('gommberg', 30, 'Lettore di prima', 'Scritto prima di G-51', '2026-11-20T10:00:00Z', 'x')");
  const nuovo = await import("./lettori.js?schema-vecchio");
  r = await nuovo.default.fetch(new Request(BASE + "/api/lettori/030", { headers: { "x-lettore": "lettore-aaaaaaaaaaaaaaaa", "cf-connecting-ip": "1.1.1.1" } }), { ...env, DB: vecchio });
  const col = vecchio._db.prepare("PRAGMA table_info(commenti)").all().map((x) => x.name);
  const jv = await r.json();
  verifica("schema: sul database già in linea le colonne nuove si aggiungono e i commenti restano", r.status === 200 && ["redazione", "fissato", "modificato", "deciso", "attesa"].every((x) => col.includes(x)) && jv.commenti.length === 1 && jv.commenti[0].redazione === false, col);
}
