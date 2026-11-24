import re, sys, json, glob
sys.path.insert(0,'/home/claude/pagella')
from estrai import carica
from rendi import pulisci, riga
ordine=['e-2026-11-16','e-2026-11-17','e-2026-11-18','e-2026-11-19','e-2026-11-20','prova1','prova2','prova3','e-2026-11-23','e-2026-11-24']
nomi={'e-2026-11-16':'#026','e-2026-11-17':'#027','e-2026-11-18':'#028','e-2026-11-19':'#029','e-2026-11-20':'#030','prova1':'prova1','prova2':'prova2','prova3':'prova3','e-2026-11-23':'#031','e-2026-11-24':'#032'}
def corpo(m):
    tx=m.get('testo'); 
    return [riga(p) for p in tx] if isinstance(tx,list) else ([pulisci(tx)] if tx else [])
R={}
allgrams={}
for k in ordine:
    C=carica(f'src/{k}.py'); txt=open(f'txt/{k}.txt').read()
    low=txt.lower()
    mods=C.get('moduli',[])
    voce=len(re.findall(r"\bper noi\b",low)), len(re.findall(r"a nostro avviso",low)), len(re.findall(r"\b(ci leggiamo|leggiamo|ci sembra|ci pare|crediamo|pensiamo|riteniamo|la nostra lettura|secondo noi)\b",low))
    tend=len(re.findall(r"\b(di solito|in genere|spesso|tende a|tendono a|di norma|in generale)\b",low))
    sec=len(re.findall(r"\bsecondo (?!noi)",low))
    titoli=[pulisci(m.get('titolo','')) for m in mods]
    aperture=[(corpo(m)[0] if corpo(m) else '') for m in mods]
    primafrase=[re.split(r'(?<=[.?!])\s',a)[0] for a in aperture]
    dom=sum(1 for p in primafrase if p.endswith('?'))
    due=sum(1 for t in titoli if ':' in t)
    contr=sum(1 for t in titoli if re.search(r"\bnon\b|\bma\b",t.lower()))
    testo_corpo=' '.join(sum((corpo(m) for m in mods),[]))
    frasi=[f for f in re.split(r'(?<=[.?!])\s+',testo_corpo) if f.strip()]
    lens=[len(f.split()) for f in frasi]
    w=re.findall(r"[a-zà-ù0-9%']+",low)
    g=set(zip(*[w[i:] for i in range(5)]))
    allgrams[k]=g
    R[k]=dict(voce=voce,tend=tend,secondo=sec,n_mod=len(mods),dom=dom,duepunti=due,contrasto=contr,
              corte=round(100*sum(1 for l in lens if l<8)/max(1,len(lens))), lunghe=round(100*sum(1 for l in lens if l>30)/max(1,len(lens))),media=round(sum(lens)/max(1,len(lens)),1),
              titoli=titoli, prime=primafrase, perche=[pulisci(m.get('perche',''))[:90] for m in mods], nw=len(w))
print(f"{'ed':8} per-noi a-nostro altre-voci tend secondo | mod dom ':' contr | corte% lunghe% media")
for k in ordine:
    r=R[k]; print(f"{nomi[k]:8} {r['voce'][0]:6} {r['voce'][1]:8} {r['voce'][2]:10} {r['tend']:4} {r['secondo']:7} | {r['n_mod']:3} {r['dom']:3} {r['duepunti']:3} {r['contrasto']:5} | {r['corte']:5} {r['lunghe']:6} {r['media']:5}")
print()
reali=[k for k in ordine if k.startswith('e-')]
print("5-grammi condivisi con l'edizione vera precedente (numero, % dei propri):")
for k in ordine:
    prev=[x for x in reali if x<k and x!=k] if k.startswith('e-') else ['e-2026-11-20']
    if not prev: continue
    p=prev[-1]; c=allgrams[k]&allgrams[p]; tutte=set().union(*[allgrams[x] for x in prev])
    print(f"  {nomi[k]:7} vs {nomi[p]}: {len(c):4} ({100*len(c)/len(allgrams[k]):.1f}%)   vs tutte le precedenti: {len(allgrams[k]&tutte):4}")
print()
for k in ordine:
    print(nomi[k]); 
    for t,p in zip(R[k]['titoli'],R[k]['prime']): print("   T:",t); print("      1a frase:",p[:130])
json.dump({nomi[k]:R[k] for k in ordine},open('conteggi.json','w'),ensure_ascii=False,indent=1)
