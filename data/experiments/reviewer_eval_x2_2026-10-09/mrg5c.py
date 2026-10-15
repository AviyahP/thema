import sys,json,collections,numpy as np; sys.path.insert(0,'.')
from tf_common import *
G=[set(g) for g in json.load(open('/tmp/mrg5_0.5_complete.json'))]
gid={x:i for i,g in enumerate(G) for x in g}
keep={i:max(g,key=lambda k:(sup[k],len(M[k]))) for i,g in enumerate(G)}
rep=lambda k: keep[gid[k]] if k in gid else k
U={i:set().union(*[M[k] for k in g]) for i,g in enumerate(G)}
MM=dict(M); 
for i in U: MM[keep[i]]=U[i]
nodes=[k for k in N if k not in big and rep(k)==k]
def lowest_containing(p,S,seen=None):
    if S<=MM[rep(p)]: return {rep(p)}
    out=set()
    for q in par[p]: out|=lowest_containing(q,S)
    return out
def newpar(k,mode):
    if k in gid:
        i=gid[k]; ps=set()
        for m in G[i]:
            for p in par[m]:
                if U[i]<=MM[rep(p)]: ps.add(rep(p))
                elif mode=='reattach': ps|=lowest_containing(p,U[i])
        ps.discard(k); return ps
    return {rep(p) for p in par[k]}
def minimal(ps,P):
    # drop parents that are ancestors of other parents
    ancs=lambda x,P: set()
    return ps
def anc_new(P):
    memo={}
    def a(k):
        if k in memo: return memo[k]
        s=set(); memo[k]=s
        for p in P[k]: s|={p}|a(p)
        return s
    return a
def stats(P,label):
    a=anc_new(P)
    np_=collections.Counter(min(len(P[k]),3) for k in P)
    multi=[k for k in P if len(P[k])>=2]
    incomp=[k for k in multi if any(not (x in a(y) or y in a(x)) for x in P[k] for y in P[k] if x<y)]
    # lineage: distinct root sets
    roots=lambda k: {r for r in a(k)|{k} if not P[r]}
    mr=sum(1 for k in P if len(roots(k))>=2)
    print(f"{label:<34} themes {len(P):5d} | 0 parents {np_[0]:4d}  1 parent {np_[1]:5d}  2+ parents {len(multi):5d} ({100*len(multi)/len(P):.0f}%) | parents not nested in each other: {len(incomp)} ({100*len(incomp)/len(P):.0f}%) | reach 2+ top roots: {mr} ({100*mr/len(P):.0f}%)")
P0={k:set(par[k]) for k in N if k not in big}
stats(P0,'BEFORE')
for mode in ('drop','reattach'):
    P={k:newpar(k,mode) for k in nodes}
    # remove transitive redundancy: parent that is ancestor of another parent
    a=anc_new(P)
    P={k:{p for p in ps if not any(p in a(q) for q in ps if q!=p)} for k,ps in P.items()}
    stats(P,f'AFTER merge ({mode} parents)')
    mg=[keep[i] for i in range(len(G))]
    print(f"   merged themes only: 2+ parents {sum(len(P[k])>=2 for k in mg)} of {len(mg)}; before, their members had 2+ parents: {np.mean([np.mean([len(par[m])>=2 for m in G[i]]) for i in range(len(G))])*len(G):.0f}")
print('\n--- why unmerged themes lose 2+ parents ---')
P={k:newpar(k,'reattach') for k in nodes}; a=anc_new(P)
P={k:{p for p in ps if not any(p in a(q) for q in ps if q!=p)} for k,ps in P.items()}
c=collections.Counter()
for k in nodes:
    if k in gid or len(par[k])<2: continue
    if len(P[k])>=2: c['still 2+']+=1; continue
    reps={rep(p) for p in par[k]}
    if len(reps)<len(par[k]) and len(reps)==1: c['all its parents were variants merged into one']+=1
    elif len(reps)<len(par[k]): c['some parents merged, rest now nested/ancestral']+=1
    else: c['parents now nested in each other (after union)']+=1
print(dict(c))
