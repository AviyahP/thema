import sys,json,csv,collections,numpy as np; sys.path.insert(0,'.')
from tf_common import J, ROOT
csv.field_size_limit(10**9)
def load(d):
    N={r['node']:r for r in csv.DictReader(open(d+'nodes.tsv'),delimiter='\t')}
    M=collections.defaultdict(set)
    for r in csv.DictReader(open(d+'members.tsv'),delimiter='\t'): M[r['node']].add(r['key'])
    return N,M
B={'THEMA c85':ROOT+'data/ontology/v0.4-leaves/thema_L_x2_c85/','HiDeF k4/800':ROOT+'data/ontology/v0.4-leaves/hidef_L_k4_maxres800/'}
D={k:load(v) for k,v in B.items()}
U=set.union(*[set().union(*D[k][1].values()) for k in D]); common=set.intersection(*[set().union(*D[k][1].values()) for k in D])
print('pathways: union',len(U),'common',len(common))
res={}
for name,(N,M) in D.items():
    T={k:s for k,s in M.items() if 3<=len(s)<1000}
    par={k:set(N[k]['parents'].split())&set(T) for k in T}
    kids=collections.defaultdict(set)
    for k in T:
        for p in par[k]: kids[p].add(k)
    bands=[(3,6),(7,15),(16,40),(41,100),(101,999)]
    bc={f'{a}-{b}':sum(a<=len(s)<=b for s in T.values()) for a,b in bands}
    roots=sum(1 for k in T if not par[k])
    def anc(k,memo={}):
        pass
    mp=sum(1 for k in T if len(par[k])>=2 and any(not(T[a]<=T[b] or T[b]<=T[a]) for a in par[k] for b in par[k] if a<b))
    sib=set()
    for p,ks in kids.items():
        ks=sorted(ks)
        for i,a in enumerate(ks):
            for b in ks[i+1:]:
                if not(T[a]<=T[b] or T[b]<=T[a]): sib.add((a,b))
    sj=np.array([J(T[a],T[b]) for a,b in sib])
    by=collections.defaultdict(list)
    for k,s in T.items():
        for x in s: by[x].append(k)
    allnn=0
    seen=set()
    for x,ks in by.items():
        for i,a in enumerate(ks):
            for b in ks[i+1:]:
                pr=(a,b) if a<b else (b,a)
                if pr in seen: continue
                seen.add(pr)
                if not(T[a]<=T[b] or T[b]<=T[a]) and J(T[a],T[b])>=0.5: allnn+=1
    H={}
    for x in common:
        ks=sorted(by.get(x,[]),key=lambda k:len(T[k])); mins=[]
        for k in ks:
            if not any(T[m]<T[k] for m in mins): mins.append(k)
        sel=[]
        for k in sorted(mins,key=lambda k:len(T[k])):
            if all(J(T[k],T[s])<0.4 for s in sel): sel.append(k)
        H[x]=(mins,sel)
    nh=np.array([len(v[0]) for v in H.values()]); nd=np.array([len(v[1]) for v in H.values()])
    t=len(T)/1000
    print(f"\n== {name}: themes {len(T)} (excl. giants), bands {bc}, roots {roots}, 2+ non-nested parents {mp} ({100*mp/len(T):.0f}%)")
    print(f"   sibling pairs {len(sib)}; J>=0.4 {int((sj>=0.4).sum())} ({(sj>=0.4).sum()/t:.0f}/1000 themes), >=0.5 {int((sj>=0.5).sum())} ({(sj>=0.5).sum()/t:.0f}/1000), >=0.6 {int((sj>=0.6).sum())}; any non-nested pair J>=0.5: {allnn} ({allnn/t:.0f}/1000)")
    print(f"   themes in a sibling pair J>=0.5: {len({a for p in sib for a in p if J(T[p[0]],T[p[1]])>=0.5})} ({100*len({a for p in sib for a in p if J(T[p[0]],T[p[1]])>=0.5})/len(T):.0f}%)")
    print(f"   homes per pathway median {np.median(nh):.0f} mean {nh.mean():.2f}; 0 homes {100*(nh==0).mean():.0f}%; distinct homes: 1 {100*(nd==1).mean():.0f}%, 2+ {100*(nd>=2).mean():.0f}%, 3+ {100*(nd>=3).mean():.0f}%, mean {nd.mean():.2f}")
    res[name]=(T,H,by)
(Ta,Ha,ba),(Tb,Hb,bb)=res['THEMA c85'],res['HiDeF k4/800']
both=[x for x in common if len(Ha[x][1])>=2 and len(Hb[x][1])>=2]
def matched(Hs,Tsrc,byo,To,x): return [max([J(Tsrc[h],To[k]) for k in byo.get(x,[])]+[0])>=0.5 for h in Hs[x][1]]
a=[m for x in both for m in matched(Ha,Ta,bb,Tb,x)]; b=[m for x in both for m in matched(Hb,Tb,ba,Ta,x)]
print(f"\npathways with 2+ distinct homes in both: {len(both)} of {len(common)}; THEMA distinct homes matched by a HiDeF theme with the pathway at J>=0.5: {100*np.mean(a):.0f}%; HiDeF distinct homes matched by THEMA: {100*np.mean(b):.0f}%")
json.dump({'hidef_sizes':[len(s) for s in Tb.values()]},open('/tmp/hd_sizes.json','w'))
