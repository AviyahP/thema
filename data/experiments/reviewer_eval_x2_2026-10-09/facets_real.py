import sys,json,collections,numpy as np; sys.path.insert(0,'.')
from tf_common import *
G=[set(g) for g in json.load(open('/tmp/mrg5_0.5_complete.json'))]
gid={x:i for i,g in enumerate(G) for x in g}
keep={i:max(g,key=lambda k:(sup[k],len(M[k]))) for i,g in enumerate(G)}
def build(mode):
    if mode=='c85': return {k:M[k] for k in N if k not in big}
    T={}
    for k in N:
        if k in big: continue
        if k in gid:
            i=gid[k]
            if k==keep[i]: T[k]=set().union(*[M[m] for m in G[i]])
        else: T[k]=M[k]
    return T
def homes(T):
    by=collections.defaultdict(list)
    for k,s in T.items():
        for x in s: by[x].append(k)
    out={}
    for x,ks in by.items():
        ks=sorted(ks,key=lambda k:len(T[k]))
        mins=[]
        for k in ks:
            if not any(T[m]<T[k] for m in mins): mins.append(k)
        out[x]=mins
    return out
for mode in ('c85','merged J>=0.5'):
    T=build(mode); H=homes(T)
    n=np.array([len(v) for v in H.values()])
    pj=[]; sep=[]
    for x,v in H.items():
        if len(v)<2: continue
        js=[J(T[a],T[b]) for i,a in enumerate(v) for b in v[i+1:]]
        pj.append(np.median(js)); sep.append(np.mean([j<0.4 for j in js]))
    distinct=[]
    for x,v in H.items():
        # greedy count of homes that are mutually J<0.4 (clearly different themes)
        sel=[]
        for k in sorted(v,key=lambda k:-sup[k]):
            if all(J(T[k],T[s])<0.4 for s in sel): sel.append(k)
        distinct.append(len(sel))
    d=np.array(distinct)
    print(f"{mode:<14} themes {len(T)} | smallest homes per pathway: median {np.median(n):.0f}, mean {n.mean():.1f}, 1 home {100*(n==1).mean():.0f}% | median J between a pathway's homes {np.median(pj):.2f} | clearly distinct homes (pairwise J<0.4): median {np.median(d):.0f}, mean {d.mean():.1f}, >=2: {100*(d>=2).mean():.0f}%, >=3: {100*(d>=3).mean():.0f}%")
