import sys,json,collections,random,numpy as np,csv; sys.path.insert(0,'.')
from tf_common import *
import networkx as nx
NM={r['node']:r['name'] for r in csv.DictReader(open(EV+'names_test/theme_names_c85.tsv'),delimiter='\t')}
V2=json.load(open('/tmp/v2_labels.json'))
P={frozenset(p['id'].split('|')):p for p in PAIRS}
def complete(sel):
    grp={}; mem={}
    for k in sorted(sel,key=lambda k:-P[k]['J']):
        a,b=tuple(k); ga=grp.get(a,a); gb=grp.get(b,b)
        if ga==gb: continue
        Sa=mem.get(ga,{a}); Sb=mem.get(gb,{b})
        if all(frozenset((x,y)) in sel for x in Sa for y in Sb):
            new=Sa|Sb; g=min(new)
            for x in new: grp[x]=g
            mem.pop(ga,None); mem.pop(gb,None); mem[g]=new
    return list(mem.values())
def single(sel):
    G=nx.Graph(); G.add_edges_from(tuple(k) for k in sel); return [set(c) for c in nx.connected_components(G)]
def lab_stats(groups):
    gid={x:i for i,g in enumerate(groups) for x in g}
    coll=[p for k,p in P.items() if all(x in gid for x in k) and len({gid[x] for x in k})==1]
    o=collections.Counter(LAB.get(p['id']) for p in coll); v=collections.Counter(V2.get(p['id']) for p in coll)
    return len(coll),o,v
nodes=set(N); leaves={k for k in N if not chl[k]}
print('BEFORE: themes',len(N),'leaves',len(leaves),'max depth',max(depth(k) for k in N))
for thr in (0.5,0.6):
  sel={k for k,p in P.items() if p['J']>=thr}
  for link,f in (('complete',complete),('single',single)):
    G=f(sel); rem=sum(len(g)-1 for g in G); sz=collections.Counter(len(g) for g in G)
    n,o,v=lab_stats(G)
    po=o['twin']/(o['twin']+o['facet']); pv=v['twin']/max(1,v['twin']+v['facet'])
    print(f"\nJ>={thr} {link}: groups {len(G)} themes_removed {rem} ({100*rem/len(N):.1f}%) groupsizes {dict(sorted(sz.items())[:8])} max {max(map(len,G))}")
    print(f"  pairs collapsed {n}; orig labels twin {o['twin']} facet {o['facet']} (precision {100*po:.0f}%); full-list labels twin {v['twin']} facet {v['facet']} (precision {100*pv:.0f}%)")
    json.dump([sorted(g) for g in G],open(f'/tmp/mrg5_{thr}_{link}.json','w'))
