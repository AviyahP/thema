import sys,json,os,random,collections,numpy as np; sys.path.insert(0,'.')
exec(open(os.path.expanduser('~/np_build.py')).read().split("ok={k")[0])
P=ROOT+'data/experiments/homefit_2026-10-12/'
T={k:M[k] for k in N if k not in big}
by=collections.defaultdict(list)
for k,s in T.items():
    for x in s: by[x].append(k)
def homes(x):
    ks=sorted(by[x],key=lambda k:len(T[k])); mins=[]
    for k in ks:
        if not any(T[m]<T[k] for m in mins): mins.append(k)
    sel=[]
    for k in sorted(mins,key=lambda k:-sup[k]):
        if all(J(T[k],T[s])<0.4 for s in sel): sel.append(k)
    return sel
H={x:homes(x) for x in by}
multi=[x for x,h in H.items() if len(h)>=2]
elig=sorted(x for x in multi if all(len(T[k])<=100 for k in H[x]) and x in ix)
print('pathways with 2+ distinct homes',len(multi),'eligible (all homes <=100)',len(elig),'excluded by cap',len(multi)-len(elig))
rng=random.Random(20261013); S=rng.sample(elig,100)
small=[k for k in T if 3<=len(T[k])<=100]
C=np.stack([ (lambda e:e/(np.linalg.norm(e)+1e-9))(V[[ix[m] for m in T[k] if m in ix]].mean(0)) for k in small])
items=[];key={}
capb=0
for n,x in enumerate(S):
    h=H[x]; 
    if len(h)>4: capb+=1; h=h[:4]
    sims=C@V[ix[x]]; dec=None
    for j in np.argsort(-sims):
        k=small[j]
        if x in T[k]: continue
        if all(J(T[k],T[hh])<0.4 for hh in h): dec=k; break
    groups=[(k,'home') for k in h]+[(dec,'decoy')]
    random.Random(f'hf{x}').shuffle(groups)
    iid=f'H{n:03d}'
    desc=first2(DESC.get(x,''))
    items.append(dict(item_id=iid,target=dict(name=render(x),description=desc),
        groups={f'G{i+1}':sorted((render(m) for m in T[k] if m!=x),key=lambda s:random.Random(iid+s).random()) for i,(k,_) in enumerate(groups)}))
    key[iid]=dict(pathway=x,groups={f'G{i+1}':dict(theme=k,role=r,size=len(T[k]),support=sup[k],cos=float(C[small.index(k)]@V[ix[x]]) if k in small else None) for i,(k,r) in enumerate(groups)})
print('cap 4 binds',capb,'homes per item',collections.Counter(len(v['groups'])-1 for v in key.values()))
for b in range(5): json.dump(items[b*20:(b+1)*20],open(P+f'inputs/HF_{b+1:02d}.json','w'),indent=1)
json.dump(key,open(P+'inputs/KEY_DO_NOT_SHARE.json','w'),indent=1)
sz=[len(g) for it in items for g in it['groups'].values()]; print('group sizes median',np.median(sz),'max',max(sz))
