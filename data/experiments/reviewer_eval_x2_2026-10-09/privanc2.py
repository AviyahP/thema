import csv,collections,json,numpy as np
from scipy.stats import rankdata
csv.field_size_limit(10**9)
D='data/ontology/v0.4-leaves/thema_L_x2_c85/'
N={r['node']:r for r in csv.DictReader(open(D+'nodes.tsv'),delimiter='\t')}
M=collections.defaultdict(set)
for r in csv.DictReader(open(D+'members.tsv'),delimiter='\t'): M[r['node']].add(r['key'])
big={k for k,s in M.items() if len(s)>=1000}
par={k:set(N[k]['parents'].split())-big for k in N}
memo={}
def anc(k):
    if k in memo: return memo[k]
    s=set()
    for p in par[k]: s|={p}|anc(p)
    memo[k]=s; return s
def Jset(x,y): return len(x&y)/len(x|y) if x|y else 1.0
R=json.load(open('data/experiments/reviewer_eval_x2_2026-10-09/judged_sibling_pairs_all.json'))
rows=[]
for r in R:
    if r['verdict'] not in ('twin','facet'): continue
    a,b=r['id'].split('|'); A,B=M[a],M[b]; U=A|B
    ancA,ancB=anc(a),anc(b)
    S=[p for p in par[a]&par[b]]
    if not S: continue
    pa=[p for p in par[a] if p not in ancB]; pb=[p for p in par[b] if p not in ancA]
    def best(ps,other):
        if not ps: return (1.0,1.0,1.0)
        vals=[]
        for p in ps:
            jS=max(Jset(M[p],M[s]) for s in S)
            ctx=max(Jset(M[p]-U,M[s]-U) for s in S)
            cov=len(M[p]&other)/len(other)
            vals.append((jS,ctx,cov))
        return tuple(min(v[i] for v in vals) for i in range(3))
    ba,bb=best(pa,B),best(pb,A)
    rows.append(dict(id=r['id'],y=r['verdict']=='twin',J=r['J'],
      jS_min=min(ba[0],bb[0]),jS_max=max(ba[0],bb[0]),
      ctx_min=min(ba[1],bb[1]),ctx_max=max(ba[1],bb[1]),
      cov_min=min(ba[2],bb[2]),cov_max=max(ba[2],bb[2]),has_both=int(bool(pa) and bool(pb))))
y=np.array([r['y'] for r in rows]); n1=y.sum(); n0=len(y)-n1
def auc(x):
    rk=rankdata(np.array(x,float)); return (rk[y].sum()-n1*(n1+1)/2)/(n1*n0)
print('n',len(rows),'twins',n1)
for k in ['J','jS_min','jS_max','ctx_min','ctx_max','cov_min','cov_max']:
    print(f"{k:<8} AUC(twin high) {auc([r[k] for r in rows]):.3f}")
sub=[r for r in rows if r['has_both']]
print('pairs where both have a private parent:',len(sub))
for name,cond in [('ctx_max<0.3',lambda r:r['ctx_max']<0.3),('ctx_max<0.5',lambda r:r['ctx_max']<0.5),('jS_max<0.5',lambda r:r['jS_max']<0.5),('cov_max<0.8',lambda r:r['cov_max']<0.8),('cov_max<0.6',lambda r:r['cov_max']<0.6)]:
    on=[r for r in rows if cond(r)]
    if on: print(f"{name:<12} n={len(on):5d} facet%={100*sum(not r['y'] for r in on)/len(on):5.1f}")
import statistics as st
for lab,g in [('twin',[r for r in sub if r['y']]),('facet',[r for r in sub if not r['y']])]:
    print(lab,'median jS_max',round(st.median(r['jS_max'] for r in g),2),'ctx_max',round(st.median(r['ctx_max'] for r in g),2),'cov_max',round(st.median(r['cov_max'] for r in g),2))
json.dump(rows,open('/tmp/privanc2_rows.json','w'))
G=json.load(open('data/experiments/reviewer_eval_x2_2026-10-09/twin_groups.json'))
gid={n:i for i,g in enumerate(G) for n in g}
tot=0;same=0
for r in rows:
    a,b=r['id'].split('|'); ancA,ancB=anc(a),anc(b)
    S=par[a]&par[b]
    for x,ao in ((a,ancB),(b,ancA)):
        for p in par[x]:
            if p in ao: continue
            tot+=1
            if p in gid and any(gid.get(s)==gid[p] for s in S): same+=1
print('private parents:',tot,'in same twin family as a shared parent:',same,round(100*same/tot,1),'%')
# depth (longest path to a root) spread per family
dmemo={}
def depth(k):
    if k in dmemo: return dmemo[k]
    d=0 if not par[k] else 1+max(depth(p) for p in par[k]); dmemo[k]=d; return d
spreads=[max(depth(n) for n in g)-min(depth(n) for n in g) for g in G]
import collections as C
print('family depth spread distribution:',sorted(C.Counter(spreads).items()))
print('family size vs spread (median spread for size>=10):',st.median([s for s,g in zip(spreads,G) if len(g)>=10]))
