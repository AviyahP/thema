import sys,json,itertools; sys.path.insert(0,'.')
from tf_common import *
import networkx as nx
from scipy.stats import rankdata, spearmanr
PI=json.load(open('/tmp/pairinfo.json'))
G=nx.Graph()
for k,v in PI.items():
    a,b=k.split('|'); G.add_edge(a,b,**v)
fams=[c for c in nx.connected_components(G) if len(c)>=3]
rows=[]
for c in fams:
    H=G.subgraph(c); labs=[d['lab'] for _,_,d in H.edges(data=True) if d['lab'] in ('twin','facet')]
    if not labs: continue
    tw=np.mean([l=='twin' for l in labs])
    sizes=[len(M[n]) for n in c]; U=set().union(*(M[n] for n in c)); I=set.intersection(*(M[n] for n in c))
    mds=[d['md'] for _,_,d in H.edges(data=True)]
    rows.append(dict(n=len(c),tw=tw,ntw=sum(l=='twin' for l in labs),nf=sum(l=='facet' for l in labs),
      expand=len(U)/np.median(sizes), core=len(I)/np.median(sizes), dens=nx.density(H),
      medJ=np.median([d['J'] for _,_,d in H.edges(data=True)]), maxmd=max(mds), medmd=np.median(mds),
      nodes=sorted(c)))
print('families >=3 themes:',len(rows))
tw=np.array([r['tw'] for r in rows])
for k in ['expand','core','dens','medJ','maxmd','medmd','n']:
    x=np.array([r[k] for r in rows],float); print(f"{k:<7} spearman with family twin share: {spearmanr(x,tw)[0]:+.3f}")
allt=np.array([r['tw']==1 for r in rows]); print('all-twin families:',allt.sum(),'of',len(rows))
x=np.array([r['expand'] for r in rows])
qs=np.quantile(x,[0.25,0.5,0.75])
for i in range(4):
    m=np.digitize(x,qs)==i
    print(f" expansion quartile {i+1} ({x[m].min():.2f}-{x[m].max():.2f}): families={m.sum()} all-twin={100*allt[m].mean():.0f}% mean twin share={100*tw[m].mean():.0f}% themes={sum(r['n'] for r,mm in zip(rows,m) if mm)}")
for t in [1.2,1.3,1.4,1.5]:
    m=x<=t; nt=sum(r['ntw'] for r,mm in zip(rows,m) if mm); nf=sum(r['nf'] for r,mm in zip(rows,m) if mm)
    print(f" collapse families with union <= {t} x median member: families={m.sum()} themes={sum(r['n'] for r,mm in zip(rows,m) if mm)} twin edges {nt} facet edges {nf} precision {100*nt/max(1,nt+nf):.0f}%")
json.dump(rows,open('/tmp/famrows.json','w'),default=float)
