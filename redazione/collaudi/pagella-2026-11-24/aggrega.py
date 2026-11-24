import json, glob, os, re, statistics as st
M=json.load(open('/home/claude/.riservato/mappe_segrete.json'))
nomi={'e-2026-11-16':'#026','e-2026-11-17':'#027','e-2026-11-18':'#028','e-2026-11-19':'#029','e-2026-11-20':'#030','prova1':'prova1','prova2':'prova2','prova3':'prova3','e-2026-11-23':'#031','e-2026-11-24':'#032'}
ordine=['#026','#027','#028','#029','#030','prova1','prova2','prova3','#031','#032']
voci=['domanda','cause','prove','chiarezza','italiano','titoli','varieta']
G={}
for f in sorted(glob.glob('giudizi/g*.json')):
    g=os.path.basename(f)[:-5]; inv={l:nomi[k] for k,l in M[g].items()}
    d=json.load(open(f)); G[g]=dict(ed={inv[l]:v for l,v in d['edizioni'].items()}, cl=[inv[l] for l in d['classifica']], sg=[inv[l] for l in d['stesso_giorno']['ordine']], sgp=d['stesso_giorno'].get('perche',''), cd=d.get('cosa_distingue',''), vz=[dict(v, sigle=[inv.get(s,s) for s in v.get('sigle',[])]) for v in d.get('vizi_ricorrenti',[])])
json.dump(G,open('giudizi_decodificati.json','w'),ensure_ascii=False,indent=1)
print('lettori:',list(G))
print('\nPOSIZIONE IN CLASSIFICA (1 = migliore)')
print(f"{'':8}"+''.join(f"{g:>5}" for g in G)+'  media')
for e in ordine:
    p=[G[g]['cl'].index(e)+1 for g in G]; print(f"{e:8}"+''.join(f"{x:5}" for x in p)+f"  {st.mean(p):.1f}")
print('\nSTESSO GIORNO:'); [print(' ',g,G[g]['sg']) for g in G]
print('\nVOTI MEDI per voce (media dei lettori) | pensiero prosa totale')
for e in ordine:
    r=[]
    for v in voci:
        x=[G[g]['ed'][e][v] for g in G if G[g]['ed'][e].get(v) is not None]; r.append(st.mean(x) if x else None)
    pen=st.mean(r[:3]); pro=st.mean(r[3:6])
    print(f"{e:8}"+' '.join(f"{(x if x is not None else float('nan')):4.1f}" for x in r)+f" | {pen:.1f} {pro:.1f} {st.mean([x for x in r if x is not None]):.2f}")
print('\nVOTI per lettore (domanda cause prove chiarezza italiano titoli varieta)')
for e in ordine: print(f"{e:8}"+'  '.join(g+':'+''.join(str(G[g]['ed'][e].get(v) if G[g]['ed'][e].get(v) is not None else '-') for v in voci) for g in G))
# verifica citazioni
def norm(s): return re.sub(r'\s+',' ',s.replace('’',"'").replace('“','"').replace('”','"')).strip().lower()
src={nomi[k]:norm(open(f'txt/{k}.txt').read()) for k in nomi}
tot=bad=0
for g in G:
    for e,v in G[g]['ed'].items():
        for it in v.get('punti_forti',[])+v.get('difetti',[]):
            tot+=1; c=norm(it.get('citazione','')).strip('."… ')
            if c[:60] not in src[e]: bad+=1; it['_non_trovata']=True
print(f"\ncitazioni: {tot}, non trovate alla lettera: {bad}")
json.dump(G,open('giudizi_decodificati.json','w'),ensure_ascii=False,indent=1)
