import sys; sys.path.insert(0,'.')
from tf_common import *
import networkx as nx
X=ROOT+'data/ontology/v0.4-leaves-x2/'
V=np.load(X+'vectors_leaves_centred.npy').astype(np.float32)
V/=np.linalg.norm(V,axis=1,keepdims=True)+1e-9
K=open(X+'embedding_keys.txt').read().split(); ix={k:i for i,k in enumerate(K)}
def vecs(s): return V[[ix[x] for x in s if x in ix]]
def mcos_within(E):
    n=len(E)
    if n<2: return np.nan
    S=E@E.T; return (S.sum()-np.trace(S))/(n*(n-1))
def mcos_cross(E1,E2):
    if len(E1)==0 or len(E2)==0: return np.nan
    return float((E1@E2.T).mean())
def cen(E):
    v=E.mean(0); return v/(np.linalg.norm(v)+1e-9)
# theme lookup for D2/D3: index themes by member for fast candidate search
byk=collections.defaultdict(set)
for n,s in M.items():
    if n not in big:
        for k in s: byk[k].add(n)
def best_theme_J(T,exclude=()):
    cand=set()
    for k in T: cand|=byk[k]
    best=0
    for c in cand:
        if c in exclude: continue
        j=J(M[c],T)
        if j>best: best=j
    return best
# family graph
G=nx.Graph()
for p in PAIRS:
    a,b=p['id'].split('|'); G.add_edge(a,b,J=p['J'])
comps=list(nx.connected_components(G)); fid={n:i for i,c in enumerate(comps) for n in c}
comm={}; ebc={}; fmedJ={}; fdens={}
for i,c in enumerate(comps):
    H=G.subgraph(c)
    fmedJ[i]=float(np.median([d['J'] for _,_,d in H.edges(data=True)]))
    fdens[i]=nx.density(H)
    if len(c)>2:
        for ci,cc in enumerate(nx.community.greedy_modularity_communities(H,weight='J')):
            for n in cc: comm[n]=(i,ci)
        for (u,v),val in nx.edge_betweenness_centrality(H,normalized=True).items():
            ebc[frozenset((u,v))]=val
    else:
        for n in c: comm[n]=(i,0)
        u,v=list(c); ebc[frozenset((u,v))]=1.0
rows=[]
for p in PAIRS:
    pid=p['id']; lab=LAB.get(pid)
    if lab not in ('twin','facet'): continue
    a,b=pid.split('|'); A,B=M[a],M[b]; C=A&B; ao=A-B; bo=B-A; U=A|B
    S=min(par[a]&par[b],key=lambda x:len(M[x]))
    f=dict(id=pid,y=int(lab=='twin'),J=p['J'],fam=fid[a])
    f['A1']=min(len(ao),len(bo)); f['A2']=len(ao)+len(bo); f['A3']=min(len(ao),len(bo))/max(len(ao),len(bo)); f['A4']=len(C)
    ia=[INC[(a,k)] for k in ao]; ib=[INC[(b,k)] for k in bo]
    f['B1']=float(np.mean(ia+ib)); f['B2']=min(np.mean(ia),np.mean(ib))
    f['B3']=float(np.mean([INC[(a,k)] for k in C]+[INC[(b,k)] for k in C]))
    f['B4']=float(np.mean([x<0.5 for x in ia+ib]))
    Ea,Eb,EA,EB,EU=vecs(ao),vecs(bo),vecs(A),vecs(B),vecs(U)
    wa,wb,x=mcos_within(Ea),mcos_within(Eb),mcos_cross(Ea,Eb)
    f['C1']=np.nanmean([wa,wb])-x if not np.isnan(x) else np.nan
    f['C2']=float(cen(Ea)@cen(Eb)) if len(Ea) and len(Eb) else np.nan
    # silhouette of a vs b (cosine distance)
    if len(Ea)>=2 and len(Eb)>=2:
        def sil(E1,E2):
            S11=1-E1@E1.T; n=len(E1); ain=(S11.sum(1))/(n-1); bout=(1-E1@E2.T).mean(1)
            return (bout-ain)/np.maximum(ain,bout)
        f['C3']=float(np.mean(np.concatenate([sil(Ea,Eb),sil(Eb,Ea)])))
    else: f['C3']=np.nan
    f['C4']=float(cen(EA)@cen(EB))
    f['C5']=np.nanmean([mcos_within(EA),mcos_within(EB)])-mcos_within(EU)
    def pchild(x,own):
        v=[len(M[c]&own)/len(M[c]) for c in chl[x] if c in M]
        return max(v) if v else 0.0
    f['D1']=min(pchild(a,ao),pchild(b,bo))
    f['D2']=int(best_theme_J(C,exclude=(a,b))>=0.7)
    f['D3']=int(best_theme_J(U,exclude=(a,b,S))>=0.7)
    f['D4']=min(len(chl[a]),len(chl[b])); f['D5']=abs(depth(a)-depth(b)); f['D7']=min(len(par[a]),len(par[b]))
    na,nb=set(G[a])-{b},set(G[b])-{a}
    f['E1']=len(na&nb); f['E2']=J(na,nb) if na|nb else 0.0
    i=fid[a]; f['E3']=len(comps[i]); f['E4']=fdens[i]; f['E5']=int(comm[a]==comm[b])
    f['E6']=ebc[frozenset((a,b))]; f['E7']=p['J']-fmedJ[i]
    rows.append(f)
json.dump(rows,open('/tmp/tf_static.json','w'),default=float)
print(len(rows))
