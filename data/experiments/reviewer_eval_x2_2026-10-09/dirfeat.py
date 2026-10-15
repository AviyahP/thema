import sys,json; sys.path.insert(0,'.')
from tf_common import *
from scipy.stats import rankdata
X=ROOT+'data/ontology/v0.4-leaves-x2/'
V=np.load(X+'vectors_leaves_centred.npy').astype(np.float32); V/=np.linalg.norm(V,axis=1,keepdims=True)+1e-9
K=open(X+'embedding_keys.txt').read().split(); ix={k:i for i,k in enumerate(K)}
def cen(s):
    E=V[[ix[x] for x in s if x in ix]]; return E.mean(0)
def cos(u,v): return float(u@v/(np.linalg.norm(u)*np.linalg.norm(v)+1e-9))
rows=[]
for p in PAIRS:
    lab=LAB.get(p['id'])
    if lab not in ('twin','facet'): continue
    a,b=p['id'].split('|'); A,B=M[a],M[b]
    P=min(par[a]&par[b],key=lambda x:len(M[x]))
    cP=cen(M[P]); cA=cen(A); cB=cen(B); cC=cen(A&B)
    ao,bo=A-B,B-A
    rows.append(dict(y=lab=='twin',J=p['J'],
      dirP=cos(cA-cP,cB-cP),            # direction of each sibling away from shared parent
      dirC=cos(cA-cC,cB-cC),            # direction away from the shared core
      dirPu=cos(cen(ao)-cP,cen(bo)-cP), # direction of the unique blocks from the parent
      md=min(len(ao),len(bo))))
y=np.array([r['y'] for r in rows]); n1=y.sum(); n0=len(y)-n1
Jv=np.array([r['J'] for r in rows]); band=np.digitize(Jv,[0.5,0.6])
def auc(x,yy):
    rk=rankdata(x); a=yy.sum(); b=len(yy)-a; return (rk[yy].sum()-a*(a+1)/2)/(a*b),a*b
def strat(x):
    num=den=0
    for g in np.unique(band):
        m=band==g; s,w=auc(x[m],y[m]); num+=s*w; den+=w
    return num/den
rng=np.random.default_rng(0); h=rng.random(len(y))<0.5
for k in ['dirP','dirC','dirPu']:
    x=np.array([r[k] for r in rows])
    print(f"{k:<6} AUC(twin = same direction) {auc(x,y)[0]:.3f}  halves {auc(x[h],y[h])[0]:.3f}/{auc(x[~h],y[~h])[0]:.3f}  J-band strat {strat(x):.3f}")
x=np.array([r['dirP'] for r in rows]); md=np.array([r['md'] for r in rows])
qs=np.quantile(x,[0.2,0.4,0.6,0.8])
print('dirP quintiles twin%:',[round(100*y[np.digitize(x,qs)==i].mean(),1) for i in range(5)])
for t in [0.5,0.6,0.7]:
    m=(x>=t)&(md<=2); print(f'dirP>={t} & md<=2: n={m.sum()} precision={100*y[m].mean():.1f}%')
