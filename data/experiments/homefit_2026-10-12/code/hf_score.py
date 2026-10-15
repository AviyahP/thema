import json,glob,collections,numpy as np,random,os
P=os.path.expanduser('~/mnt/thema/data/experiments/homefit_2026-10-12/')
K=json.load(open(P+'inputs/KEY_DO_NOT_SHARE.json'))
O={}
for f in glob.glob(P+'judged/HF_*.out.json'):
    for o in json.load(open(f)): O[o['item_id']]=o
ids=sorted(O); rng=np.random.default_rng(0)
fit=lambda v,strict: (v=='yes') if strict else (v in ('yes','partly'))
def rates(strict):
    hr=[];dr=[];hm=[]
    for i in ids:
        g=K[i]['groups']; f=O[i]['fit']
        h=[fit(f[x],strict) for x in g if g[x]['role']=='home']; d=[fit(f[x],strict) for x in g if g[x]['role']=='decoy']
        hm.append(np.mean(h)); dr.append(np.mean(d)); hr+=h
    return np.array(hm),np.array(dr),np.mean(hr)
for strict in (False,True):
    hm,dr,pooled=rates(strict)
    bs=[(hm[ix].mean(),dr[ix].mean()) for ix in (rng.integers(0,100,100) for _ in range(5000))]
    a=np.array(bs); d=a[:,0]-a[:,1]
    lab='strict yes' if strict else 'yes or partly'
    print(f"[{lab}] P1 real homes fit {100*hm.mean():.1f}% (CI {100*np.percentile(a[:,0],2.5):.1f}-{100*np.percentile(a[:,0],97.5):.1f}; pooled over homes {100*pooled:.1f}%) | P2 decoy fit {100*dr.mean():.1f}% (CI {100*np.percentile(a[:,1],2.5):.1f}-{100*np.percentile(a[:,1],97.5):.1f}) | P1-P2 {100*(hm.mean()-dr.mean()):+.1f} (CI {100*np.percentile(d,2.5):+.1f} to {100*np.percentile(d,97.5):+.1f})")
fc=collections.Counter(v for i in ids for x,v in O[i]['fit'].items() if K[i]['groups'][x]['role']=='home'); dc=collections.Counter(O[i]['fit'][x] for i in ids for x in K[i]['groups'] if K[i]['groups'][x]['role']=='decoy')
print('home verdicts',dict(fc),'decoy verdicts',dict(dc))
el=[i for i in ids if sum(fit(O[i]['fit'][x],False) for x in K[i]['groups'] if K[i]['groups'][x]['role']=='home')>=2]
rc=collections.Counter(O[i]['relation'] for i in el); n=len(el)
print(f"P3 pathways with 2+ fitting real homes: {n}; relation {dict(rc)}; different aspects {100*rc['different_aspects']/n:.1f}%")
print('relation over all 100 (judge view incl. decoy if fit):',dict(collections.Counter(O[i]['relation'] for i in ids)))
hm,dr,_=rates(False)
P1,P2=hm.mean(),dr.mean(); a=np.array([(hm[ix].mean()-dr[ix].mean()) for ix in (rng.integers(0,100,100) for _ in range(5000))])
P3=rc['different_aspects']/n
print('DECLARED:', 'REAL FACETS' if (P1>=.8 and P1-P2>=.25 and np.percentile(a,2.5)>0 and P3>=.6) else ('NOISE' if (P1<.6 or np.percentile(a,2.5)<=0) else 'MIXED'))
rows=[(K[i]['groups'][x]['size'],K[i]['groups'][x]['support'],fit(O[i]['fit'][x],False)) for i in ids for x in K[i]['groups'] if K[i]['groups'][x]['role']=='home']
sz=np.array([r[0] for r in rows]); su=np.array([r[1] for r in rows]); ft=np.array([r[2] for r in rows])
for lo,hi in ((3,6),(7,15),(16,40),(41,100)): m=(sz>=lo)&(sz<=hi); print(f'  home size {lo}-{hi}: fit {100*ft[m].mean():.0f}% (n={m.sum()})')
q=np.quantile(su,[1/3,2/3])
for nm,m in (('low support',su<q[0]),('mid',(su>=q[0])&(su<q[1])),('high',su>=q[1])): print(f'  {nm}: fit {100*ft[m].mean():.0f}% (n={m.sum()})')
print('judge-level home fit:',{f'HF_0{b+1}':f"{100*np.mean([fit(O[i]['fit'][x],False) for i in ids[b*20:(b+1)*20] for x in K[i]['groups'] if K[i]['groups'][x]['role']=='home']):.0f}%" for b in range(5)})
random.seed(4)
no=[(i,x) for i in ids for x in K[i]['groups'] if K[i]['groups'][x]['role']=='home' and O[i]['fit'][x]=='no']
print('\nexamples, homes judged no:'); [print('  ',i,O[i]['reason']) for i,x in random.sample(no,min(6,len(no)))]
da=[i for i in el if O[i]['relation']=='different_aspects']; print('\nexamples, different aspects:'); [print('  ',i,O[i]['reason']) for i in random.sample(da,min(6,len(da)))]
sa=[i for i in el if O[i]['relation']!='different_aspects']; print('\nexamples, same/unrelated:'); [print('  ',i,O[i]['relation'],O[i]['reason']) for i in random.sample(sa,min(4,len(sa)))]
