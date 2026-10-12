import datetime as dt
from gommberg_engine import *

OGGI = dt.date(2026, 10, 12)
set_meta(OGGI, "Chiusure al 9 ottobre; mattina del 12 ottobre dove indicato")
story = []

# ======================= PAGINA 1 - PRIMA PAGINA =======================
story += ticker([
    ("MSCI ACWI (ETF)", "160,90 $", "+0,7% g"),
    ("S&amp;P 500", "7.811,54", "+0,6% g"),
    ("EURO STOXX 50", "6.197,10", "+0,6% g"),
    ("UST 10 ANNI", "5,24%", "+2 pb g"),
    ("BRENT FUTURE", "104,72 $", "+0,4% g"),
    ("EUR/USD", "1,1201", "-0,1% g"),
    ("VIX", "14,84", "-0,57 g"),
])
story += [P("TOP STORY", "kicker"),
          P("Hormuz, nessun accordo. Wall Street vicina al record aspetta CPI, banche e TSMC", "h1"),
          P("L'Iran giudica inadeguata la risposta americana e il conflitto si allarga all'Arabia Saudita, eppure i future "
            "USA aprono in rialzo e il petrolio scende sulle forniture di diesel russo. Con il Treasury a 10 anni ai "
            "massimi dal 2002, l'inflazione di mercoledì è il test che conta.", "dek")]

left = [box("In 30 secondi", [
    "Wall Street chiude la settimana a +1,2%, a un soffio dal record, nonostante il 10 anni USA salito fino a "
    "circa il 5,35% (massimo dal 2002).",
    "Questa settimana decidono tre test: CPI USA (mer 14:30), trimestrali delle banche (da martedì) e TSMC (gio).",
    "Iran: Trump esclude attacchi fino al 3 novembre, ma su Hormuz nessun accordo e gli Houthi colpiscono Riad.",
], width=CW * 0.55 - 5 * mm)]
right = [box("Stamattina", [
    "Future USA alle 08:19: S&amp;P 500 +0,56%, Dow +0,84%, Nasdaq 100 +0,45%",
    "Europa alle 09:09: Euro Stoxx 50 +0,76%, Stoxx 600 +0,43%",
    "Asia: Kospi -3,65%, Shanghai -0,50%; Tokyo chiusa",
    "Petrolio alle 08:19: Brent 103,39 $ -1,27%, WTI 90,37 $ -1,61%",
    "EUR/USD 1,1207 alle 09:50",
], width=CW * 0.45)]
story += [Spacer(1, 4), side_by_side(left, right, CW * 0.55)]

story += section("Le notizie del giorno", "Top news")
story.append(news_grid([
    ("Geopolitica", "Iran: risposta USA \"inadeguata\", Hormuz resta chiuso",
     "Tra le 7 condizioni di Teheran c'è la fine del blocco navale USA: secondo l'Iran Washington ne ha accettate solo "
     "alcune, senza dire quali, e lo stretto resta chiuso finché non le accetta tutte. Media il Qatar."),
    ("Energia", "Weekend di fuoco nel Golfo: petroliere colpite, nave fermata dagli USA",
     "Sabato e domenica due petroliere colpite in uscita da Hormuz, una in fiamme. Un caccia USA ha messo fuori uso "
     "un mercantile che violava il blocco: per il CENTCOM 4 navi fermate e 135 respinte dal 14 luglio."),
    ("Petrolio", "Greggio in calo su diesel russo e \"tregua energetica\"",
     "Trump ha annunciato forniture di diesel russo per oltre 4,8 milioni di tonnellate e una tregua energetica "
     "Russia-Ucraina che Mosca non conferma. Brent a 103,39 $ (-1,27%) stamattina."),
    ("Medio Oriente", "Houthi colpiscono l'aeroporto di Riad",
     "Almeno 12 morti, tra cui un cittadino USA, e 309 feriti. Trump valuta di unirsi ai raid sauditi. Il conflitto "
     "tocca le infrastrutture energetiche saudite: rischio al rialzo per il petrolio."),
    ("Asia", "Kospi -3,65%: pioggia di vendite sui chip",
     "Quarta seduta di calo: Samsung -4,39%, SK Hynix -4,52%. Pesano il ribilanciamento degli ETF sui chip, la fine dei "
     "riacquisti di azioni proprie dei due big e l'attacco a Riad. Segnale da non ignorare prima di ASML e TSMC."),
    ("Italia", "Risiko: Intesa insiste su MPS, Tata rilancia su Iveco",
     "Offerta Intesa su MPS da circa 31,4 miliardi € dopo il rilancio del 5/10; CdA di MPS oggi pomeriggio. Tata Motors alza l'offerta su Iveco a "
     "14,40 € per azione (3,91 miliardi €)."),
    ("Cina", "Dazi: tregua prorogata, la UE studia un tetto alle ibride cinesi",
     "La tregua tariffaria USA-Cina è prorogata al 10 gennaio 2027, quindi nessuna scadenza questa settimana. La UE "
     "prepara un tetto di 350.000 ibride cinesi l'anno, che potrebbe scattare dal 1° dicembre (Bloomberg). Mercoledì CPI e bilancia commerciale."),
    ("Fed", "Ultima settimana di discorsi prima del silenzio",
     "Parlano Hammack (oggi), Waller e Bowman; venerdì alle 05:30 (ora di Roma) il presidente Warsh dialoga con la "
     "direttrice dell'FMI Georgieva. Da sabato 17 scatta il periodo di silenzio prima della riunione del 27-28 ottobre."),
]))

story.append(PageBreak())

# ======================= PAGINA 2 - MERCATI =======================
story += section("Cruscotto: come stanno andando i mercati", "Mercati")
dash = dash_table([
    headers("Indice", "Ultimo", "Data", "1 g", "1 sett.", "Da inizio anno"),
    ("Globale", [["MSCI ACWI (ETF, $)", "160,90", "9/10", "+0,7%", "+0,5%", "n.d."]]),
    ("Stati Uniti", [["S&amp;P 500", "7.811,54", "9/10", "+0,6%", "+1,2%", "+14,1%"],
                     ["Nasdaq Composite", "27.366,17", "9/10", "+0,6%", "+0,6%", "+17,7%"],
                     ["Dow Jones", "51.654,95", "9/10", "+0,8%", "+0,9%", "+7,5%"],
                     ["Russell 2000", "2.806,98", "9/10", "+0,5%", "-0,9%", "+13,1%"]]),
    ("Europa", [["Euro Stoxx 50", "6.197,10", "9/10", "+0,6%", "-1,0%", "+6,9%"],
                ["FTSE 100", "10.552,05", "9/10", "+1,1%", "+0,9%", "+6,2%"]]),
    ("Asia", [["Nikkei 225", "69.030,92", "9/10", "0,0%", "+1,1%", "+37,1%"],
              ["Hang Seng", "24.211,36", "9/10", "+1,8%", "+1,0%", "-5,5%"],
              ["Kospi", "6.384,24", "12/10", "-3,7%", "n.d.", "n.d."],
              ["Shanghai Comp.", "3.794,60", "12/10", "-0,5%", "n.d.", "n.d."]]),
], [31 * mm, 18 * mm, 11 * mm, 13 * mm, 14 * mm, 17 * mm])
story.append(side_by_side([dash], [img("c_week.png", CW - 104 * mm - 5 * mm),
                                   P("Fonte: FMP, AP, Alpha Vantage. ACWI = iShares MSCI ACWI, proxy del mercato globale.", "src")],
                          104 * mm + 5 * mm))

story += section("Tassi, cambi, materie prime e volatilità", "Cross-asset")
story.append(dash_table([
    headers("Strumento", "Livello 9/10", "1 g", "1 sett.", "1 mese", "Lettura"),
    ("Tassi USA", [["Treasury 2 anni", "4,80%", "+5 pb", "-3 pb", "+37 pb", "Rialzo Fed a ottobre: probabilità circa 1 su 4"],
                   ["Treasury 10 anni", "5,24%", "+2 pb", "-4 pb", "+41 pb", "Intraday circa 5,35%, massimo dal 2002"],
                   ["Treasury 30 anni", "5,60%", "0 pb", "-3 pb", "+32 pb", "Sopra 5,5%: premio a termine alto"]]),
    ("Cambi", [["EUR/USD", "1,1201", "-0,1%", "-0,5%", "-3,7%", "Minimo intraday 1,1161 il 5/10"]]),
    ("Materie prime", [["Brent future", "104,72 $", "+0,4%", "+2,4%", "+3,5%", "Fisico EIA 125,44 $ il 6/10"],
                       ["WTI future", "91,85 $", "+0,4%", "+0,8%", "n.d.", "Spread Brent-WTI vicino a 13 $"]]),
    ("Volatilità", [["VIX", "14,84", "-0,57", "-0,47", "n.d.", "Mercato poco preoccupato prima del CPI"]]),
], [31 * mm, 20 * mm, 15 * mm, 15 * mm, 16 * mm, CW - 97 * mm]))

story += section("Quadro macro: utili forti contro tassi e petrolio", "Il contesto")
story += [
    P("<b>Utili.</b> LSEG stima per il terzo trimestre una crescita degli utili S&amp;P 500 del 30,6%, con energia "
      "(+123%) e tecnologia (+66,5%) in testa. Le grandi banche sono attese a circa +20%. Il rally però è stretto: "
      "dal 1° settembre l'S&amp;P 500 sale del 2,4%, l'ETF sull'azionario globale (ACWI) solo dello 0,9%."),
    P("<b>Fed.</b> Dopo il rialzo del 16 settembre a 3,75-4,00%, i verbali dicono che la maggior parte dei membri vede "
      "un altro rialzo entro fine anno. Il mercato però ha ridimensionato ottobre: probabilità di un rialzo scesa a circa 1 su 4. I dati "
      "spingono nella direzione opposta: prezzi pagati ISM servizi a 74,0, massimo da luglio 2022, e attese di "
      "inflazione a un anno dei consumatori (Michigan) al 4,7%."),
    P("<b>Energia.</b> A Hormuz il 6 ottobre sono transitate solo 7 navi commerciali contro circa 125 al giorno prima "
      "della guerra (dati Kpler via Reuters). L'export del Medio Oriente regge grazie alle rotte alternative via Golfo "
      "di Oman e Mar Rosso, ed è questo che impedisce al Brent di esplodere."),
    P("<b>Europa.</b> La crisi dei conti francesi ha portato il rendimento dell'OAT decennale vicino al 5% e lo spread "
      "con il Bund a circa 158 punti base il 2 ottobre, massimo dal 2011. La Spagna vota il 29 novembre. Risultato: "
      "Euro Stoxx 50 -1,0% nella settimana mentre Wall Street saliva, ed euro ai minimi da 17 mesi."),
]

story.append(PageBreak())

# ======================= PAGINA 3 - CATALIZZATORI =======================
story += section("La settimana scorsa: cosa ha mosso i mercati", "Catalizzatori conclusi  |  5-9 ottobre")
rows = [headers("Quando", "Evento", "Esito", "Effetto sui mercati")] + [
    [P(a, "cellb"), P(b, "cellb"), P(c, "cell"), P(d, "cell")] for a, b, c, d in [
        ("Lun 5", "ISM servizi (settembre)", "54,9 contro 55,2 atteso; prezzi pagati 74,0, massimo da luglio 2022",
         "Timori d'inflazione: 10 anni verso 5,31%"),
        ("Lun 5", "Euro, Francia e Spagna", "EUR/USD fino a 1,1161 intraday; Sánchez convoca elezioni anticipate per il 29/11",
         "Euro ai minimi da 17 mesi; OAT francese vicino al 5%"),
        ("Mar 6", "Record di Wall Street", "S&amp;P 500 a 7.818,93 (primo record da agosto), Nasdaq a 27.599,79",
         "Spinta da calo dei rendimenti e accordo Constellation-Google"),
        ("Mer 7", "Treasury e asta a 10 anni", "10 anni a circa 5,35% intraday, massimo dal 2002; asta da 39 mld $ al 5,300% con "
         "domanda forte (bid-to-cover 2,77)", "Dopo l'asta 10 anni a circa 5,28%; Russell 2000 -1,3%"),
        ("Mer 7", "Verbali Fed di settembre", "La maggior parte dei membri vede un altro rialzo entro fine anno",
         "Effetto contenuto: tono già atteso"),
        ("Gio 8", "FT su OpenAI", "Ricavi annualizzati circa 20 mld $ più bassi di quanto indicato",
         "Nasdaq -1,3%, Nvidia circa -3%, AMD circa -4%; recupero venerdì"),
        ("Gio 8", "Trump: niente raid sull'Iran prima del 3/11", "Arriva dopo notizie di piani d'attacco pronti",
         "Brent da circa 106 a 101 $ intraday, chiude a 104,28 $ (+4,1%) anche per l'uragano Isaias"),
        ("Ven 9", "Michigan e Delta", "Fiducia 46,3, sotto le attese, e inflazione attesa a 1 anno al 4,7%; Delta taglia le stime "
         "sul caro carburante", "S&amp;P 500 +0,6% comunque, a ridosso del record"),
    ]]
story += [tbl(rows, [14 * mm, 37 * mm, 70 * mm, CW - 121 * mm]), Spacer(1, 5),
          box("La settimana in una riga", [
              "Record dell'S&amp;P 500 e chiusura a +1,2% nonostante il 10 anni al massimo dal 2002, verbali Fed "
              "restrittivi e un giovedì di vendite sull'AI; Brent +2,4% tra attacchi a Hormuz, uragano e la promessa di "
              "Trump; in Europa la crisi francese spinge l'euro ai minimi da 17 mesi."])]

story += section("Questa settimana: agenda e catalizzatori in arrivo", "Week ahead  |  12-16 ottobre")
rows = [headers("Quando (Roma)", "Evento", "Attese", "Perché conta")] + [
    [P(a, "cellb"), P(b, "cell"), P(c, "celln"), P(d, "cell")] for a, b, c, d in [
        ("Lun 12", "Columbus Day (bond USA chiusi); Hammack (Fed) 18:50; LVMH ricavi Q3 a mercati chiusi",
         "-", "Liquidità sottile, il lusso misura la domanda cinese"),
        ("Mar 13", "JPMorgan, Goldman Sachs, Citi, Wells Fargo, J&amp;J, UnitedHealth (prima dell'apertura USA); "
         "CPI Germania 08:00", "Utili delle grandi banche attesi a circa +20%",
         "Apre la stagione: termometro di consumi e mercati"),
        ("Mer 14", "CPI e bilancia commerciale Cina (03:30 e 05:00); ASML; Bank of America, Morgan Stanley, BlackRock",
         "Ordini ASML e commissioni di trading", "Domanda cinese e spesa in macchinari per chip"),
        ("<b>Mer 14, 14:30</b>", "<b>CPI USA settembre</b>; Beige Book alle 20:00",
         "<b>Headline +0,6% m/m, 3,6% a/a; core +0,2% m/m</b>", "<b>Evento n.1:</b> decide Fed, dollaro e tassi"),
        ("Gio 15, 08:00", "<b>TSMC</b> conference call Q3", "Ricavi già noti: 46,7 mld $, record e sopra la guidance (44,6-45,8)",
         "Contano margini e guidance del quarto trimestre: termometro AI"),
        ("Gio 15, 14:30", "PPI, vendite al dettaglio, Philly Fed, sussidi di disoccupazione",
         "PPI +0,5% m/m; vendite +0,3%; Philly Fed 26,5", "Conferma o smentita del CPI"),
        ("Ven 16", "05:30 Warsh con Georgieva (FMI); CPI Eurozona finale; produzione industriale USA 15:15; Truist, Travelers, "
         "M&amp;T; scadenza mensile delle opzioni",
         "Produzione +0,4% m/m", "Volatilità da scadenze tecniche"),
        ("Sab 17", "Inizia il periodo di silenzio Fed prima della riunione del 27-28 ottobre", "-",
         "Ultime parole Fed prima della decisione"),
    ]]
story += [tbl(rows, [22 * mm, 64 * mm, 50 * mm, CW - 136 * mm]), Spacer(1, 2),
          P("Fonti: Reuters/LSEG, CMC Markets, investingLive, calendario Federal Reserve, siti delle società. "
            "CPI headline: sondaggio Reuters 3,6% a/a, alcuni calendari 3,7%.", "note")]

story.append(PageBreak())

# ======================= PAGINA 4 - SCENARI E TREASURY =======================
story += section("Il bivio: scenari per il CPI di mercoledì", "Scenari")
rows = [headers("Scenario", "Prob.*", "Fed", "Treasury", "Azionario", "Dollaro (EUR/USD)")] + [
    [P(a, "cellb"), P(b, "cellb"), P(c, "cell"), P(d, "cell"), P(e, "cell"), P(f, "cell")] for a, b, c, d, e, f in [
        ("In linea<br/>core 0,2% m/m", "50%", "Ottobre fermo, dicembre aperto", "2 anni stabile, curva invariata",
         "Lievemente positivo, record S&amp;P a portata", "Stabile in area 1,12"),
        ("Caldo<br/>core 0,3% o più", "35%", "Rialzo di ottobre torna in gioco", "2 anni in forte salita, 10 anni oltre 5,30%",
         "-1/-2%, più colpiti tech e small cap", "Dollaro più forte, EUR/USD verso 1,11"),
        ("Freddo<br/>core 0,1% o meno", "15%", "Pausa consolidata, dicembre in discussione",
         "Rendimenti in calo su tutta la curva", "+1/+1,5%, rotazione verso i ciclici", "Dollaro più debole, verso 1,13"),
    ]]
story += [tbl(rows, [26 * mm, 13 * mm, 33 * mm, 36 * mm, 35 * mm, CW - 143 * mm]), Spacer(1, 2),
          P("* Stime redazionali soggettive. Rischio spostato verso l'alto: prezzi pagati ISM ai massimi da luglio 2022 "
            "e attese d'inflazione dei consumatori in salita.", "note")]

story += section("Classifica dei rischi della settimana", "Risk map")
rows = [headers("#", "Fattore", "Perché conta", "Direzione più probabile")] + [
    [P(a, "cellb"), P(b, "cellb"), P(c, "cell"), P(d, "cell")] for a, b, c, d in [
        ("1", "CPI USA", "Decide il prezzo del denaro e il dollaro in un colpo solo", "Neutrale, con coda negativa"),
        ("2", "Iran, Hormuz e Arabia Saudita", "Il conflitto si allarga alle infrastrutture energetiche saudite",
         "Stallo, rischio di picchi sul greggio"),
        ("3", "AI: TSMC, ASML, dubbi su OpenAI", "Il rally è concentrato sui titoli AI: il Kospi stamattina mostra la fragilità",
         "Positiva se la guidance di TSMC regge"),
        ("4", "Trimestrali bancarie", "Prima vera verifica della stagione utili", "Positiva, ma attese già alte"),
        ("5", "Francia e debito europeo", "Dibattito sul bilancio francese dal 13/10, voto spagnolo il 29/11",
         "Rischio moderato per euro e spread"),
    ]]
story += [tbl(rows, [8 * mm, 42 * mm, 78 * mm, CW - 128 * mm])]

story += section("Treasury: +40 pb in un mese, ora la Fed pesa solo sul breve", "Deep dive 1  |  Tassi USA")
story.append(two("c_curve.png", P("Fonte: US Treasury par yield curve via Financial Modeling Prep.", "src"),
                 "c_yields.png", P("Fonte: idem. Chiusure giornaliere 8 set - 9 ott.", "src")))
rows = [headers("Scadenza", "9 set", "28 set", "9 ott", "Var. 1 mese", "Var. 2 sett.", "Lettura")] + [
    [P(a, "cellb"), P(b, "cell"), P(c, "cell"), P(d, "cell"), P(e, "cellb"), P(f, "cellb"), P(g, "cell")]
    for a, b, c, d, e, f, g in [
        ("2 anni", "4,43%", "4,92%", "4,80%", "+37 pb", "-12 pb", "Tolto il rialzo Fed di ottobre"),
        ("10 anni", "4,83%", "5,24%", "5,24%", "+41 pb", "0 pb", "Asta forte al 5,300% il 7/10"),
        ("30 anni", "5,28%", "5,56%", "5,60%", "+32 pb", "+4 pb", "Inflazione energetica e deficit"),
        ("Spread 2-10", "40 pb", "32 pb", "44 pb", "+4 pb", "+12 pb", "Irripidimento dal lato breve"),
    ]]
story += [Spacer(1, 3), tbl(rows, [21 * mm, 15 * mm, 15 * mm, 15 * mm, 19 * mm, 19 * mm, CW - 104 * mm]), Spacer(1, 4),
          P("<b>Lettura.</b> In un mese l'intera curva è salita di circa 40 punti base. Nelle ultime due settimane però il "
            "2 anni è sceso mentre il 30 anni è rimasto fermo: il mercato ha tolto il rialzo di ottobre ma non si fida "
            "di un rientro rapido dell'inflazione. L'asta a 10 anni del 7 ottobre, con l'80% assegnato ad acquirenti indiretti (in "
            "gran parte esteri), ha messo un tetto temporaneo. <b>Soglia:</b> un 10 anni stabilmente sopra 5,30-5,35% è il livello "
            "che finora ha frenato l'azionario.")]

story.append(PageBreak())

# ======================= PAGINA 5 - IRAN E PETROLIO =======================
story += section("Iran: tregua elettorale a Washington, escalation nel Golfo", "Deep dive 2  |  Geopolitica")
for t in [
    "<b>Il quadro.</b> Il conflitto con USA e Israele dura dal 28 febbraio. Washington mantiene un blocco navale sui porti "
    "iraniani; Teheran tiene chiuso lo stretto e chiede 7 condizioni per riaprirlo entro 7 giorni.",
    "<b>La novità.</b> L'8 ottobre Trump ha escluso attacchi prima delle midterm del 3 novembre, parlando di discussioni "
    "produttive. Nel weekend però l'Iran ha giudicato inadeguata la controproposta USA, due petroliere sono state "
    "colpite e gli Houthi hanno attaccato l'aeroporto di Riad: Trump valuta di unirsi ai raid sauditi.",
    "<b>Sul terreno.</b> La portaerei USS Theodore Roosevelt potrebbe arrivare nell'area a fine ottobre. Il Tesoro USA "
    "ha sanzionato altre 17 navi della flotta ombra iraniana. Dopo il voto Trump ha definito possibile la ripresa dei "
    "bombardamenti.",
]:
    story.append(B(t))
rows = [headers("Scenario fino al 3 novembre", "Prob.*", "Petrolio", "Borse")] + [
    [P(a, "cellb"), P(b, "cellb"), P(c, "cell"), P(d, "cell")] for a, b, c, d in [
        ("Stallo armato: nessun raid USA, attacchi sporadici in mare", "60%", "Brent future 95-110 $", "Rumore, nessun trend"),
        ("Escalation regionale: Arabia Saudita e infrastrutture energetiche nel mirino", "25%", "Brent future oltre 115 $",
         "Azionario globale -2/-4%, Treasury lunghi sotto pressione"),
        ("Intesa parziale: corridoio o riapertura graduale di Hormuz", "15%", "Calo rapido, -10/-15%",
         "Rally, ciclici ed Europa in testa"),
    ]]
story += [Spacer(1, 3), tbl(rows, [70 * mm, 13 * mm, 38 * mm, CW - 121 * mm]), Spacer(1, 2),
          P("* Stime redazionali soggettive, riviste dopo l'attacco a Riad (escalation da 20% a 25%).", "note")]

story += section("Petrolio: il future dice 105 $, il barile fisico molto di più", "Deep dive 3  |  Energia")
story += chart_text("c_brent.png", [
    B("<b>Future:</b> Brent a 104,72 $ venerdì (+2,4% nella settimana). Stamattina scende a 103,39 $ sul diesel russo. "
      "Il WTI a 91,85 $: lo spread di quasi 13 $, molto sopra la norma, dice che il problema è l'offerta del Golfo."),
    B("<b>Fisico:</b> il 6 ottobre il Brent spot EIA (cargo reali) valeva 125,44 $ contro 100,58 $ del future: un premio "
      "di quasi 25 $ per chi ha bisogno di barili subito."),
    B("<b>Spinte e freni:</b> l'uragano Isaias ha fermato il 63% della produzione del Golfo del Messico; dall'altra parte "
      "G7 e partner rilasceranno fino a 100 milioni di barili di scorte e il Kuwait è al 75% della produzione prebellica."),
], "Grafico: EIA Europe Brent Spot FOB via Alpha Vantage; Brent future da Financial Modeling Prep e Benzinga (12/10, 08:19).")

story += section("EUR/USD: l'euro paga Francia, Spagna e il differenziale dei tassi", "Deep dive 4  |  Cambi")
story += chart_text("c_eurusd.png", [
    B("<b>Livello:</b> 1,1201 venerdì, 1,1207 stamattina. Dal picco di 1,1679 del 21 agosto l'euro perde il 4,1%; il "
      "5 ottobre è sceso fino a 1,1161 in seduta, minimo da 17 mesi."),
    B("<b>Perché:</b> in Europa pesano la crisi dei conti francesi (spread OAT-Bund a 158 pb il 2/10) e il voto spagnolo; "
      "negli USA una Fed che alza i tassi, con il Treasury a 10 anni a 5,24% contro il 3,45% del Bund (5/10)."),
    B("<b>Cosa può invertire il trend:</b> un CPI USA debole, un'intesa sull'Iran o una tregua sul debito europeo."),
], "Grafico: chiusure giornaliere EUR/USD via Alpha Vantage, 25 mag - 9 ott 2026.")

story.append(PageBreak())

# ======================= PAGINA 6 - LA SCOMMESSA =======================
story += section("La scommessa della settimana: dove chiudiamo venerdì 16 ottobre", "Il gran finale  |  Forecast")
story += [P("<b>Il nostro pronostico:</b> settimana moderatamente positiva per le borse, rendimenti quasi fermi, petrolio "
            "in calo ed euro ancora debole. Il CPI di mercoledì è il punto in cui possiamo sbagliare tutto.", "dek"),
          img("c_forecast.png", CW), Spacer(1, 4)]
rows = [headers("Strumento", "Chiusura 9/10", "Previsione 16/10", "Var. prevista", "Range atteso", "Prob. rialzo*",
                "Il perché")] + [
    [P(a, "cellb"), P(b, "cell"), P(c, "cellb"), P(d, "cellb"), P(e, "cell"), P(f, "cell"), P(g, "cell")]
    for a, b, c, d, e, f, g in [
        ("MSCI ACWI (ETF)", "160,90 $", "161,20 $", "+0,2%", "158,3 - 163,5 $", "55%",
         "USA avanti, Europa e Asia frenate da tassi e chip"),
        ("S&amp;P 500", "7.811,54", "7.840", "+0,4%", "7.650 - 7.970", "58%",
         "Banche e TSMC sostengono; nuovo record possibile se il CPI è in linea"),
        ("Euro Stoxx 50", "6.197,10", "6.250", "+0,9%", "6.090 - 6.305", "60%",
         "Recupero dopo la settimana negativa, banche e petrolio in calo"),
        ("Treasury 10 anni", "5,24%", "5,22%", "-2 pb", "5,12 - 5,36%", "45%",
         "Asta forte e greggio in calo compensano un CPI headline alto"),
        ("Treasury 2 anni", "4,80%", "4,78%", "-2 pb", "4,66 - 4,94%", "45%", "Il rialzo di ottobre resta poco probabile"),
        ("Brent future", "104,72 $", "102,00 $", "-2,6%", "98 - 112 $", "35%",
         "Diesel russo e rotte alternative; rischio di picchi dall'Arabia Saudita"),
        ("EUR/USD", "1,1201", "1,1180", "-0,2%", "1,1130 - 1,1270", "40%", "Differenziale dei tassi e Francia pesano ancora"),
    ]]
story += [tbl(rows, [27 * mm, 19 * mm, 21 * mm, 18 * mm, 24 * mm, 17 * mm, CW - 126 * mm]), Spacer(1, 3),
          P("* Probabilità che il valore di venerdì 16 sia sopra la chiusura del 9 ottobre: stima redazionale soggettiva. "
            "Range: per l'S&amp;P 500 la variazione settimanale implicita nel VIX (circa ±2,1%), per gli altri la "
            "volatilità realizzata nelle ultime sedute; in circa due settimane su tre il prezzo resta dentro.", "note"),
          Spacer(1, 4)]
story.append(side_by_side(
    [box("Le regole del gioco", [
        "Il pronostico si fa il lunedì e non si cambia durante la settimana.",
        "Ogni giorno questa pagina mostra a che punto siamo rispetto alla previsione.",
        "Il lunedì successivo arriva il verdetto: direzione giusta o sbagliata e chiusura dentro o fuori dal range.",
    ], width=CW * 0.5 - 4 * mm)],
    [box("La pagella", [
        "Edizione n. 001: primo pronostico, ancora nessun verdetto.",
        "Il primo voto arriva lunedì 19 ottobre con l'edizione n. 006.",
        "Punteggio stagionale: 0 su 0.",
    ], width=CW * 0.5)], CW * 0.5))

story += section("Glossario", "Per chi legge")
story.append(glossary([
    ("pb", "punti base, centesimi di punto percentuale (25 pb = 0,25%)"),
    ("m/m, a/a", "variazione sul mese precedente e sullo stesso mese dell'anno prima"),
    ("CPI, PPI", "inflazione dei prezzi al consumo e alla produzione negli USA"),
    ("Treasury, Bund, OAT", "titoli di Stato di USA, Germania e Francia"),
    ("Spread", "differenza di rendimento tra due titoli, misura del rischio relativo"),
    ("VIX", "volatilità attesa sull'S&amp;P 500 a 30 giorni, il termometro della paura"),
    ("Brent, WTI", "petrolio di riferimento europeo e americano; future = contratto, spot EIA = cargo fisico"),
    ("EPS, guidance", "utile per azione; previsioni che l'azienda dà sui periodi futuri"),
    ("Bid-to-cover", "domande ricevute in un'asta diviso titoli offerti: più alto, più domanda"),
    ("Periodo di silenzio", "giorni prima della riunione in cui i membri Fed non parlano di politica monetaria"),
]))

story += section("Fonti", "Note")
story.append(P("<b>Dati di mercato:</b> Financial Modeling Prep (indici, VIX, Brent, curva Treasury); Alpha Vantage (EUR/USD, "
  "ACWI, Brent spot EIA); AP via La Nación (Dow, Russell, da inizio anno). <b>Notizie:</b> Reuters (via US News, Business "
  "Recorder, The National, Global Banking &amp; Finance), AP/CBS, CNBC, TIME, gCaptain, Gulf News, Korea JoongAng Daily, "
  "TradingKey, Benzinga, Newsquawk, Trading Economics, ANSA, Il Sole 24 Ore, Fortune Italia. "
  "<b>Settimana scorsa:</b> investingLive, Wolf Street, Federal Reserve, BabyPips, Admiral Markets, Stocktwits, AP via Boston "
  "Globe, Political.org, ROIC, Al Jazeera, OE Digital, The Star (TSMC). <b>Agenda:</b> Reuters/LSEG, Saxo, CMC Markets, "
  "investingLive, Cambridge Currencies, Federal Reserve, ROIC.", "src"))

render(nome_file(OGGI), story)
print(nome_file(OGGI))
