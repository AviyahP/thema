import sys,json,itertools,collections; sys.path.insert(0,'.')
from tf_common import *
F={r['id']:r for r in json.load(open(EV+'twin_facet_features_static.json'))}
pairs={}
for p in PAIRS:
    a,b=p['id'].split('|'); f=F.get(p['id'])
    A,B=M[a],M[b]; md=min(len(A-B),len(B-A))
    pairs[frozenset((a,b))]=dict(id=p['id'],J=p['J'],md=md,lab=LAB.get(p['id']),C4=f['C4'] if f else None)
NT=sum(v['lab']=='twin' for v in pairs.values()); NF=sum(v['lab']=='facet' for v in pairs.values())
rules={'R0 J>=0.65':lambda v:v['J']>=0.65,
 'R1 J>=0.6 & md<=2':lambda v:v['J']>=0.6 and v['md']<=2,
 'R2 J>=0.5 & md<=2':lambda v:v['J']>=0.5 and v['md']<=2,
 'R3 md<=2':lambda v:v['md']<=2}
def single(sel):
    import networkx as nx
    G=nx.Graph(); G.add_edges_from(tuple(k) for k in sel)
    return [set(c) for c in nx.connected_components(G)]
def complete(sel):
    # greedy agglomeration by descending J; merge groups only if every cross pair is selected
    grp={}; members={}
    for k in sorted(sel,key=lambda k:-pairs[k]['J']):
        a,b=tuple(k)
        ga=grp.get(a,a); gb=grp.get(b,b)
        if ga==gb: continue
        Sa=members.get(ga,{a}); Sb=members.get(gb,{b})
        if all(frozenset((x,y)) in sel for x in Sa for y in Sb):
            new=Sa|Sb; g=min(new)
            for x in new: grp[x]=g
            members.pop(ga,None); members.pop(gb,None); members[g]=new
    return list(members.values())
out={}
for name,fn in rules.items():
    sel={k for k,v in pairs.items() if fn(v)}
    for link,f in (('single',single),('complete',complete)):
        groups=f(sel); gid={x:i for i,g in enumerate(groups) for x in g}
        coll=[v for k,v in pairs.items() if all(x in gid for x in k) and len({gid[x] for x in k})==1]
        t=sum(v['lab']=='twin' for v in coll); fc=sum(v['lab']=='facet' for v in coll)
        removed=sum(len(g)-1 for g in groups)
        print(f"{name:<18} {link:<8} selected={len(sel):5d} groups={len(groups):4d} themes_removed={removed:5d} maxgroup={max(map(len,groups)):3d} | twins collapsed {t}/{NT} ({100*t/NT:.1f}%)  facets collapsed {fc}/{NF} ({100*fc/NF:.1f}%)  precision {100*t/(t+fc):.1f}%")
        out[f"{name}|{link}"]=dict(groups=[sorted(g) for g in groups],coll=[v['id'] for v in coll])
json.dump(out,open('/tmp/mrg_out.json','w'))
json.dump({v['id']:v for v in pairs.values()},open('/tmp/pairinfo.json','w'))
