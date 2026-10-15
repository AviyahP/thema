import sys,json,glob,collections,numpy as np,os; sys.path.insert(0,'.')
from tf_common import *
P=ROOT+'data/experiments/homefit_2026-10-12/'
K=json.load(open(P+'inputs/KEY_DO_NOT_SHARE.json'))
O={}
for f in glob.glob(P+'judged/HF_*.out.json'):
    for o in json.load(open(f)): O[o['item_id']]=o
T={k:M[k] for k in N if k not in big}
by=collections.defaultdict(list)
for k,s in T.items():
    for x in s: by[x].append(k)
rows=[]
for i,v in K.items():
    x=v['pathway']; d=[g for g in v['groups'].values() if g['role']=='decoy'][0]['theme']; D=T[d]
    cont=by[x]
    mj=max(J(D,T[t]) for t in cont)
    cin=max(len(D&T[t])/len(D) for t in cont)
    dg=[k for k,g in v['groups'].items() if g['role']=='decoy'][0]; fit=O[i]['fit'][dg]
    sib=any(p in par[d] for t in cont for p in par[t])
    rows.append((mj,cin,fit,len(D),sib))
mj=np.array([r[0] for r in rows]); cin=np.array([r[1] for r in rows]); ft=np.array([r[2] for r in rows])
print('decoy vs themes that DO contain the pathway (any level):')
print(f'  max Jaccard: median {np.median(mj):.2f}; >=0.5: {(mj>=0.5).mean()*100:.0f}%; >=0.4: {(mj>=0.4).mean()*100:.0f}%')
print(f'  share of decoy members inside one theme containing the pathway: median {np.median(cin):.2f}; >=0.8: {(cin>=0.8).mean()*100:.0f}%; =1 (decoy nested in a theme with the pathway): {(cin>=0.999).mean()*100:.0f}%')
print(f'  decoy shares a parent with a theme containing the pathway: {np.mean([r[4] for r in rows])*100:.0f}%')
for lab,m in (('decoy nested/near (>=0.8 inside)',cin>=0.8),('decoy not near (<0.8)',cin<0.8)):
    c=collections.Counter(ft[m]); n=m.sum(); print(f'  {lab}: n={n}, judged yes {c["yes"]}, partly {c["partly"]}, no {c["no"]}')
