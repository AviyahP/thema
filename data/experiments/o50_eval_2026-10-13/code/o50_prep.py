import sys,os,csv,collections,json,random,numpy as np; sys.path.insert(0,'.')
exec(open(os.path.expanduser('~/np_build.py')).read().split("ok={k")[0])
O=ROOT+'data/ontology/v0.4-leaves/thema_L_x2_O50/'
MO=collections.defaultdict(set)
for r in csv.DictReader(open(O+'members.tsv'),delimiter='\t'): MO[r['node']].add(r['key'])
c85sets={frozenset(s):k for k,s in M.items()}
new=[k for k,s in MO.items() if frozenset(s) not in c85sets]
ident={k:c85sets[frozenset(s)] for k,s in MO.items() if frozenset(s) in c85sets}
print('O50 themes',len(MO),'new',len(new),'identical',len(ident))
sz=np.array([len(MO[k]) for k in new]); print('new sizes: median',np.median(sz),'>100',(sz>100).sum(),'>=1000',(sz>=1000).sum(),'max',sz.max())
V=json.load(open(ROOT+'data/ontology/frozen/working-c85-2026-10-10/all_verdicts_c85.json'))
print('verdict file',type(V),len(V), (list(V.items())[0] if isinstance(V,dict) else V[0]))
# C5 pool
def sets(MM,x): return {k for k,s in MM.items() if x in s and len(s)<200}
Mc={k:s for k,s in M.items()}
ps=sorted(set().union(*[s for s in M.values()]))
diff=[x for x in ps if {frozenset(Mc[k]) for k in sets(Mc,x)}!={frozenset(MO[k]) for k in sets(MO,x)}]
nc=[len(sets(Mc,x)) for x in diff[:400]]; no=[len(sets(MO,x)) for x in diff[:400]]
print('C5 pool (theme sets differ):',len(diff),'of',len(ps),'; themes<200 per pathway c85 median',np.median(nc),'O50',np.median(no))
