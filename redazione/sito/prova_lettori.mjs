// Collaudo del servizio dei lettori (redazione/sito/lettori.js) senza Cloudflare e senza rete: il codice vero, con un
// database D1 finto sopra SQLite di Node (d1_finto.mjs, Node 22.5 o più) e un'edizione finta al posto dei file statici.
// Lo lancia redazione/collaudo.py; da solo: node redazione/sito/prova_lettori.mjs. Esce con 1 al primo errore.
import { readFileSync } from "node:fs";
import { d1 } from "./d1_finto.mjs";
import worker, { controllaTesto, controllaNome, chiaveNome, pulisciNome, pulisciTesto, sitoDi, LIMITI, NOMI_UNICI } from "./lettori.js";

// ------------------------------------------------------------- orologio finto, edizioni finte
let adesso = Date.parse("2026-11-23T09:00:00Z");
Date.now = () => adesso;
const avanti = (s) => { adesso += s * 1000; };
const EDIZIONI = {
  30: { numero: 30, data: "2026-11-20" },
  31: { numero: 31, data: "2026-11-23" },   // la più recente: il sentiment si vota qui
};
const env = {
  DB: d1(),
  ASSETS: { fetch: async (req) => {
    const u = new URL(req.url), m = /^\/e\/(\d{3})\.json$/.exec(u.pathname);
    if (m && EDIZIONI[+m[1]]) return new Response(JSON.stringify(EDIZIONI[+m[1]]), { headers: { "content-type": "application/json" } });
    if (u.pathname === "/dati/recenti.json") return new Response(JSON.stringify({ totale: 31, edizioni: [{ numero: 31 }, { numero: 30 }] }));
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
const testo = (x) => ({ nome: "Giulia T.", testo: x, gettone: g0 });
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: testo("Troppo presto") });
verifica("gettone di meno di 3 secondi: rifiutato", r.s === 400, r);
avanti(5);
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: testo("Senza origine"), origine: null });
verifica("senza origine: rifiutato", r.s === 403, r);
r = await chiama("POST", "/api/lettori/031/commenti", { corpo: testo("Da un altro sito"), origine: "https://altro.example" });
verifica("da un altro sito: rifiutato", r.s === 403, r);
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
env.DB._db.exec("UPDATE commenti SET creato = '2026-10-01T00:00:00Z'");
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

// i nomi del dado (assets/lettori.js): il servizio li accetta tutti e sono tutti diversi anche per chiave
const sezione = readFileSync(new URL("../../assets/lettori.js", import.meta.url), "utf8");
const dado = [...sezione.slice(sezione.indexOf("var NOMI = ["), sezione.indexOf("function nomeACaso")).matchAll(/"([^"\n]+)"/g)].map((m) => m[1]);
verifica("il dado ha un centinaio di nomi", dado.length >= 90, dado.length);
verifica("ogni nome del dado è accettato dal servizio (lunghezza, lettere, non riservato)", dado.every((x) => !controllaNome(x)), dado.filter((x) => controllaNome(x)));
verifica("i nomi del dado sono tutti diversi anche per chiave", new Set(dado.map(chiaveNome)).size === dado.length, dado.filter((x, i) => dado.findIndex((y) => chiaveNome(y) === chiaveNome(x)) !== i));
verifica("tra i nomi del dado ce ne sono di corti a cui aggiungere il numero di riserva", dado.filter((x) => x.length <= 21 && !controllaNome(x + " 99")).length >= 50, null);

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
verifica("testo enorme: rifiutato subito", r.s === 400 && performance.now() - t0 < 500, [r.s, Math.round(performance.now() - t0)]);
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

console.log(ko ? `Lettori: ${ko} NO su ${ok + ko} prove` : `Lettori: ${ok} prove superate`);
process.exit(ko ? 1 : 0);
