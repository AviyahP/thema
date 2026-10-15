import csv,collections,json,numpy as np
csv.field_size_limit(10**9)
D='data/ontology/v0.4-leaves/thema_L_x2_c85/'
N={r['node']:r for r in csv.DictReader(open(D+'nodes.tsv'),delimiter='\t')}
M=collections.defaultdict(set)
for r in csv.DictReader(open(D+'members.tsv'),delimiter='\t'): M[r['node']].add(r['key'])
big={k for k,s in M.items() if len(s)>=1000}
par={k:set(N[k]['parents'].split())-big for k in N}
def anc_depth(k,maxd=99):
    d={};fr={k};lv=0
    while fr and lv<maxd:
        lv+=1;nf=set()
        for x in fr:
            for p in par[x]:
                if p not in d: d[p]=lv; nf.add(p)
        fr=nf
    return d
AD={k:anc_depth(k) for k in N}
def J(x,y): return len(M[x]&M[y])/len(M[x]|M[y])
R=json.load(open('data/experiments/reviewer_eval_x2_2026-10-09/judged_sibling_pairs_all.json'))
rows=[]
for r in R:
    if r['verdict'] not in ('twin','facet'): continue
    a,b=r['id'].split('|')
    Aa,Ab=AD[a],AD[b]
    shared=set(Aa)&set(Ab)
    f=dict(id=r['id'],y=r['verdict']=='twin',J=r['J'])
    for k in (1,2,3):
        pa=[p for p,d in Aa.items() if d<=k and p not in Ab]
        pb=[p for p,d in Ab.items() if d<=k and p not in Aa]
        sk=[p for p in shared if min(Aa[p],Ab[p])<=k] or list(shared)
        def distinct(ps,other,thr):
            out=[]
            for p in ps:
                jmax=max([J(p,s) for s in sk] or [0])
                cov=len(M[p]&M[other])/len(M[other])
                if jmax<thr and cov<0.5: out.append(p)
            return out
        f[f'npriv_min_{k}']=min(len(pa),len(pb))
        f[f'npriv_max_{k}']=max(len(pa),len(pb))
        f[f'both_{k}']=int(bool(pa) and bool(pb))
        f[f'either_{k}']=int(bool(pa) or bool(pb))
        for thr in (0.5,0.7):
            da,db=distinct(pa,b,thr),distinct(pb,a,thr)
            f[f'dboth_{k}_{thr}']=int(bool(da) and bool(db))
            f[f'deither_{k}_{thr}']=int(bool(da) or bool(db))
        al=set(p for p,d in Aa.items() if d<=k); bl=set(p for p,d in Ab.items() if d<=k)
        f[f'ancJ_{k}']=len(al&bl)/len(al|bl) if al|bl else 1
    rows.append(f)
json.dump(rows,open('/tmp/privanc_rows.json','w'))
y=np.array([r['y'] for r in rows])
print('n',len(rows),'twins',y.sum(),'facets',(~y).sum())
def auc(x):
    x=np.array(x,float); o=np.argsort(x,kind='mergesort'); 
    from scipy.stats import rankdata
    rk=rankdata(x); n1=y.sum(); n0=len(y)-n1
    return (rk[y].sum()-n1*(n1+1)/2)/(n1*n0)
keys=[k for k in rows[0] if k not in ('id','y')]
for k in keys:
    x=np.array([r[k] for r in rows],float)
    line=f"{k:<18} AUC(twin high) {auc(x):.3f}"
    if set(np.unique(x))<= {0,1}:
        on=x==1
        line+=f" | flag=1: n={on.sum():5d} facet%={100*(~y[on]).mean() if on.sum() else 0:5.1f} | flag=0: n={(~on).sum():5d} facet%={100*(~y[~on]).mean() if (~on).sum() else 0:5.1f}"
    print(line)
