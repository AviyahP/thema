import sys,json,glob,collections,numpy as np,random; sys.path.insert(0,'.')
from tf_common import ROOT,LAB
from scipy.stats import rankdata
P=ROOT+'data/experiments/core_reading_pilot_2026-10-11/'
K=json.load(open(P+'inputs/KEY_DO_NOT_SHARE.json')); CK=json.load(open(P+'compare/KEY_DO_NOT_SHARE.json'))
V={}
for f in glob.glob(P+'compare/C1_*.out.json'):
    for o in json.load(open(f)): V[CK[o['item_id']]]=o['verdict']
PI=json.load(open('/tmp/pairinfo.json')); NF=json.load(open('/tmp/name_feats.json'))
pids=sorted(K); sc={'same':0,'partly':1,'different':2}
y=np.array([K[p]['label']=='facet' for p in pids]); x=np.array([sc[V[p]] for p in pids],float)
Jv=np.array([K[p]['J'] for p in pids]); band=np.digitize(Jv,[0.5,0.6])
def auc(x,yy):
    rk=rankdata(x); a=yy.sum(); b=len(yy)-a; return (rk[yy].sum()-a*(a+1)/2)/(a*b),a*b
def strat(x):
    n=d=0
    for g in np.unique(band):
        m=band==g; s,w=auc(x[m],y[m]); n+=s*w; d+=w
    return n/d
h=np.random.default_rng(0).random(300)<0.5
print('verdict by label:'); 
for l in ['twin','facet']: print(' ',l,dict(collections.Counter(V[p] for p in pids if K[p]['label']==l)))
for nm,f in [('core-reading',x),('md (fewer diff = twin)',np.array([PI[K[p]['pair']]['md'] for p in pids],float)),('name cosine N1 (low=facet)',-np.array([NF[K[p]['pair']]['N1a'] for p in pids])),('J (low=facet)',-Jv)]:
    print(f"{nm:<28} AUC {auc(f,y)[0]:.3f} halves {auc(f[h],y[h])[0]:.3f}/{auc(f[~h],y[~h])[0]:.3f} J-band {strat(f):.3f}")
yo=np.array([LAB[K[p]['pair']]=='facet' for p in pids]); m=np.array([LAB[K[p]['pair']] in ('twin','facet') for p in pids])
print('core-reading AUC vs ORIGINAL labels: %.3f'%auc(x[m],yo[m])[0])
# accuracy if different/partly=facet
pred=x>=1; print('rule "partly or different = facet": accuracy %.1f%%, facet recall %.0f%%, twin recall %.0f%%'%(100*(pred==y).mean(),100*pred[y].mean(),100*(~pred[~y]).mean()))
pred2=x>=2; print('rule "different = facet": accuracy %.1f%%, facet recall %.0f%%, twin recall %.0f%%'%(100*(pred2==y).mean(),100*pred2[y].mean(),100*(~pred2[~y]).mean()))
# bootstrap diff vs md
f2=np.array([PI[K[p]['pair']]['md'] for p in pids],float); rng=np.random.default_rng(1); d=[]
for _ in range(3000):
    ix=rng.integers(0,300,300)
    if y[ix].all() or (~y[ix]).all(): continue
    d.append(auc(x[ix],y[ix])[0]-auc(f2[ix],y[ix])[0])
print('core-reading minus md AUC: %.3f (CI %.3f to %.3f)'%(np.mean(d),np.percentile(d,2.5),np.percentile(d,97.5)))
R={}
for f in glob.glob(P+'raw/R1_*.out.json'):
    for o in json.load(open(f)): R[o['item_id']]=o
random.seed(3)
for lab_,ver in [('facet','different'),('twin','same'),('twin','different'),('facet','same')]:
    c=[p for p in pids if K[p]['label']==lab_ and V[p]==ver]
    print(f'\n== label {lab_}, verdict {ver}: {len(c)}')
    for p in random.sample(c,min(2,len(c))): print('  A:',R[p+'x']['theme'],'|',R[p+'x']['core_role'][:160],'\n  B:',R[p+'y']['theme'],'|',R[p+'y']['core_role'][:160])
