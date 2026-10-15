import sys,csv,collections,numpy as np; sys.path.insert(0,'.')
from tf_common import J, ROOT
csv.field_size_limit(10**9)
for name in ('thema_L_x2_c85','thema_L_x2_O50'):
    d=ROOT+f'data/ontology/v0.4-leaves/{name}/'
    M=collections.defaultdict(set)
    for r in csv.DictReader(open(d+'members.tsv'),delimiter='\t'): M[r['node']].add(r['key'])
    sup={r['node']:float(r['support'] or 0) for r in csv.DictReader(open(d+'nodes.tsv'),delimiter='\t')}
    T={k:s for k,s in M.items() if len(s)<1000}
    by=collections.defaultdict(list)
    for k,s in T.items():
        for x in s: by[x].append(k)
    nd=[];nh=[];nt=[]
    for x,ks in by.items():
        ks=sorted(ks,key=lambda k:len(T[k])); mins=[]
        for k in ks:
            if not any(T[m]<T[k] for m in mins): mins.append(k)
        sel=[]
        for k in sorted(mins,key=lambda k:-sup[k]):
            if all(J(T[k],T[s])<0.4 for s in sel): sel.append(k)
        nd.append(len(sel)); nh.append(len(mins)); nt.append(len(ks))
    nd=np.array(nd); nh=np.array(nh); nt=np.array(nt)
    print(f"{name}: themes<1000 {len(T)}; themes per pathway median {np.median(nt):.0f}; homes median {np.median(nh):.0f}; distinct homes 2+ {100*(nd>=2).mean():.0f}%, 3+ {100*(nd>=3).mean():.0f}%, mean {nd.mean():.2f}")
