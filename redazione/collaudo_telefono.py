#!/usr/bin/env python3
"""Collaudo del sito sul telefono: apre ogni pagina a 320, 360, 393 e 412 px e segnala ciò che esce dallo schermo o dal
proprio riquadro. Da lanciare prima di ogni modifica al sito che va in linea (serve Playwright; non gira nell'attività).
  python3 redazione/collaudo_telefono.py <cartella del sito> [--foto <cartella>]
Nato il 14/11/2026: una modifica alla pagina della scommessa aveva tagliato gli stili per il telefono e nessun controllo
se n'era accorto. Esce con 1 se una pagina ha un problema."""
import asyncio, os, sys, subprocess, time
from playwright.async_api import async_playwright
try:   # caratteri veri al posto di quelli di riserva, dove l'ambiente li offre (senza, le larghezze sono approssimate)
    sys.path.insert(0, os.environ.get("GTD_FONT", "/home/claude/esame")); import fontroute
except Exception:  # noqa: BLE001
    fontroute = None
S=sys.argv[1]; scatta='--foto' in sys.argv; FOTO=sys.argv[sys.argv.index('--foto')+1] if scatta else None
PAG=['', 'scommessa.html', 'glossario.html', 'archivio.html', 'progetto.html', 'numeri.html', '404.html'] + sorted('e/'+f for f in os.listdir(os.path.join(S,'e')) if f.endswith('.html'))[-2:]
JS='''()=>{
 const vw=document.documentElement.clientWidth, out=[];
 const nome=(e)=>{let s=e.tagName.toLowerCase(); if(e.id) s+='#'+e.id; else if(e.className&&typeof e.className==='string') s+='.'+e.className.trim().split(/\\s+/).slice(0,2).join('.'); return s;};
 const scorre=(e)=>{for(let p=e;p&&p!==document.body;p=p.parentElement){const o=getComputedStyle(p).overflowX; if((o==='auto'||o==='scroll'||o==='hidden')&&p.scrollWidth>p.clientWidth+1) return true;} return false;};
 for(const e of document.querySelectorAll('body *')){
   const st=getComputedStyle(e); if(st.display==='none'||st.visibility==='hidden') continue;
   const r=e.getBoundingClientRect(); if(!r.width||!r.height) continue;
   if(r.right>vw+1.5 && !scorre(e)) out.push('FUORI SCHERMO '+nome(e)+' destra='+Math.round(r.right)+' ['+(e.textContent||'').trim().slice(0,40)+']');
   else if(e.children.length===0 || ['B','SPAN','P','H1','H2','H3','H4','LI','DT','DD','A','BUTTON','TD','TH','SMALL','STRONG'].includes(e.tagName)){
     if(e.scrollWidth>e.clientWidth+2 && st.overflowX==='visible' && st.display!=='inline' && e.clientWidth>0) out.push('TESTO ESCE da '+nome(e)+' '+e.scrollWidth+'>'+e.clientWidth+' ['+(e.textContent||'').trim().slice(0,40)+']');
   }
 }
 // testi incollati: un elemento in grassetto subito dopo un numero senza spazio
 return {pagina:document.documentElement.scrollWidth, vw, problemi:[...new Set(out)].slice(0,12)};
}'''
async def main():
    srv=subprocess.Popen([sys.executable,'-m','http.server','8765','--bind','127.0.0.1'],cwd=S,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
    tot=0
    try:
        async with async_playwright() as p:
            b=await p.chromium.launch()
            for w in (320,360,393,412):
                ctx=await b.new_context(viewport={'width':w,'height':850},device_scale_factor=2,is_mobile=True,has_touch=True)
                
                if fontroute: await fontroute.attiva(ctx)
                pg=await ctx.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)[:80]))
                for u in PAG:
                    await pg.goto('http://127.0.0.1:8765/'+u,wait_until='networkidle'); await pg.wait_for_timeout(500)
                    if u=='glossario.html': 
                        r=await pg.evaluate(JS); await pg.click('#tM'); await pg.wait_for_timeout(200); r2=await pg.evaluate(JS); r['problemi']+=r2['problemi']
                    else: r=await pg.evaluate(JS)
                    stato='ok' if not r['problemi'] and r['pagina']<=r['vw'] else 'DA VEDERE'
                    tot+= stato!='ok'
                    print(f"{w} {u or 'home':15} {stato} pagina={r['pagina']}", '' if stato=='ok' else '\n    '+'\n    '.join(r['problemi'][:6]))
                    if scatta and w==393:
                        await pg.screenshot(path=os.path.join(FOTO,(u.replace('/','_').replace('.html','') or 'home')+'.png'), full_page=True)
                if errs: print('  errori JS:', errs[:3])
                await ctx.close()
            await b.close()
    finally: srv.terminate()
    print('PAGINE DA VEDERE:', tot)
    return tot
sys.exit(1 if asyncio.run(main()) else 0)
