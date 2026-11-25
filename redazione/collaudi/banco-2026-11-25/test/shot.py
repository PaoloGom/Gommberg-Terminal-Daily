import json, sys
from playwright.sync_api import sync_playwright
OUT='/home/claude/out/letture/'
para="Il rendimento del Btp decennale è salito di 12 punti base nella seduta, mentre lo spread con il Bund si è allargato a 128 punti. Gli operatori leggono il movimento come una presa di profitto dopo tre settimane di acquisti, più che come un giudizio sui conti pubblici. "
def md(s):
    return f"# Lo spread torna a salire, ma il mercato non ha paura\n*Presa di profitto dopo tre settimane di acquisti: i conti pubblici non c'entrano, dicono gli operatori.*\n\n{para*2}\n\nNella stessa seduta **Piazza Affari ha chiuso in calo dello 0,8%**, trascinata dalle banche. *Unicredit* e Intesa hanno perso più dell'1%.\n\n## Il numero\n128 punti base: il livello più alto da metà ottobre. **Sopra 140** molti gestori tornerebbero a coprirsi.\n\n---\n\n{para}\n\nFonti: Bloomberg, Mts, Borsa Italiana"
data={"letture":{"2026-11-25":{"giorno":"2026-11-25","titolo":"Lo spread Btp-Bund dopo l'asta di metà mese","nota":"Leggi d'istinto: conta la prima impressione.","testi":[{"sigla":s,"md":md(s)} for s in "ABCDEFGH"],"creato":"2026-11-25T17:00:00Z"},
 "2026-11-24":{"giorno":"2026-11-24","titolo":"prova","testi":[{"sigla":"A","md":"# x"}]}},
 "voti":{"2026-11-25-A":{"lettura":"2026-11-25","sigla":"A","voto":"si","frase":"","quando":"x"},"2026-11-25-B":{"lettura":"2026-11-25","sigla":"B","voto":"no","quando":"x"}}}
fail = len(sys.argv)>1 and sys.argv[1]=='fail'
init = """
window.__D=%s;window.__W=[];
const mk=(c,id)=>({get:async()=>{const x=(__D[c]||{})[id];return{id,exists:!!x,data:()=>x}},
 set:async(d)=>{%s __W.push(['set',c+'/'+id,JSON.parse(JSON.stringify(d))]);(__D[c]=__D[c]||{})[id]=d},
 update:async(d)=>{%s __W.push(['update',c+'/'+id,d]);Object.assign(__D[c][id],d)},delete:async()=>{}});
const col=(c,f)=>({where:(k,o,v)=>col(c,[k,v]),get:async()=>{const docs=Object.entries(__D[c]||{}).filter(([i,x])=>!f||x[f[0]]===f[1]).map(([id,x])=>({id,exists:true,data:()=>x}));return{docs,size:docs.length,empty:!docs.length}},doc:id=>mk(c,id)});
const db={collection:c=>col(c),doc:p=>{const [c,id]=p.split('/');return mk(c,id)}};
window.claude={use:async n=>n==='db'?db:null};
""" % (json.dumps(data), "if(window.__FAIL)throw{code:'invalid_argument'};", "if(window.__FAIL)throw{code:'invalid_argument'};")
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome')
    for w,h,name,scheme in [(1280,900,'1280',"light"),(390,844,'390',"light"),(1280,900,'1280-scuro',"dark")]:
        pg=b.new_page(viewport={'width':w,'height':h},color_scheme=scheme)
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type in('error','warning') else None)
        pg.add_init_script(init)
        pg.goto('file://'+OUT+'index.html');pg.wait_for_timeout(1500)
        pg.screenshot(path=OUT+f'shot-{name}.png')
        if name=='1280':
            pg.screenshot(path=OUT+'shot-1280-intero.png',full_page=True)
            pg.click('.vb.si');pg.wait_for_timeout(300)
            pg.fill('#frase','Il mercato non ha paura');pg.click('.nb.av');pg.wait_for_timeout(300)
            print('writes',pg.evaluate('JSON.stringify(__W)'))
            pg.evaluate('window.__FAIL=true');pg.click('.vb.no');pg.wait_for_timeout(300)
            print('fail state',pg.inner_text('.stato'),pg.get_attribute('.vb.no','aria-pressed'))
            pg.evaluate('window.__FAIL=false')
            for i in range(5):
                pg.click('.vb.si');pg.wait_for_timeout(150);pg.click('.nb.av');pg.wait_for_timeout(200)
            pg.screenshot(path=OUT+'shot-1280-fatto.png')
            print(pg.inner_text('.msg'))
        if name=='390':
            pg.screenshot(path=OUT+'shot-390-intero.png',full_page=True)
        print(name,'errors',errs)
    b.close()
