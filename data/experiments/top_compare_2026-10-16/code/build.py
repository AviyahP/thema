import csv,collections,os,json,random
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.abspath(HERE+'/..'); T=os.path.abspath(HERE+'/../../../..')
X=T+'/data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix/'; F=T+'/data/ontology/frozen/working-O50-2026-10-14/'
E=T+'/data/experiments/'
csv.field_size_limit(10**9)
def tsv(p): return list(csv.DictReader(open(p),delimiter='\t'))
pname={r['source']+':'+r['source_id']:(r['name'],r['source']) for r in tsv(T+'/data/pathways.tsv')}
om=collections.defaultdict(set)
for r in tsv(F+'members.tsv'): om[r['node']].add(r['key'])
on={r['node']:r for r in tsv(F+'nodes.tsv')}
am=collections.defaultdict(set)
for x in tsv(X+'area_members.tsv'): am[x['node']].add(x['key'])
names={r['theme_id']:r['name'] for r in tsv(E+'naming_O50_2026-10-14/dedup/final_names_O50_lite_unique.tsv')}
for r in tsv(E+'naming_O50_2026-10-14/name_overrides.tsv'):
    k=list(r.keys()); names[r[k[0]]]=r[k[1]]
rid={r['node']:r['root'] for r in tsv(E+'areas_rec2_giantdrop_2026-10-15/roots.tsv')}
rl={x['root']:x['label'] for x in json.load(open(E+'areas_rec2_giantdrop_2026-10-15/root_labels.json'))}
gidx=json.load(open(E+'giants_reading_2026-10-15/giants_index.json'))
g1={x['giant']:x['label'] for x in json.load(open(E+'giants_reading_2026-10-15/G1_readings.json'))}
glab={v['node']:g1[k] for k,v in gidx.items()}
def label(n):
    if n in glab: return glab[n]
    if n in rid: return rl[rid[n]]
    if n in names: return names[n]
    return None
def S(n): return am[n] if n in am else om[n]
# option 1 roots
o1=[n for n in on if not on[n]['parents'].split()]
# option 2 roots: combined structure with giants in
gi={x['node'] for x in tsv(X+'giants.tsv')}
areas={x['node'] for x in tsv(X+'areas.tsv')}|gi
anch=[x['node'] for x in tsv(X+'anchors.tsv')]
par=collections.defaultdict(set)
for e in tsv(X+'area_edges.tsv'): par[e['child']].add(e['parent'])
# giants' children are not in area_edges (view excludes giants): a node is a root of option 2 if no node of the combined set strictly contains it
nodes=list(areas)+anch
o2=[n for n in nodes if not any(m!=n and S(n)<S(m) for m in nodes)]
missing=[n for n in o1+o2 if label(n) is None]
print('option1 roots',len(o1),'option2 roots',len(o2),'unlabelled',len(missing),missing[:10])
json.dump({'o1':o1,'o2':o2},open(OUT+'/roots_options.json','w'))
o2=sorted(set(o2)); o1=sorted(set(o1))
print('deduplicated: option1',len(o1),'option2',len(o2))
json.dump({'o1':o1,'o2':o2},open(OUT+'/roots_options.json','w'))
rng=random.Random(20261016)
def menu(rs): return '\n'.join(f'- {label(n)} ({len(S(n))} pathways)' for n in sorted(rs,key=lambda n:-len(S(n))))
key={}
# Test A
flip=rng.random()<0.5
A,B=(o2,o1) if flip else (o1,o2)
key['A']={'A':'option2' if flip else 'option1','B':'option1' if flip else 'option2'}
open(OUT+'/inputs/testA.md','w').write('# Menu A\n\n'+menu(A)+'\n\n# Menu B\n\n'+menu(B)+'\n')
# Test B
allp=sorted(set().union(*[om[n] for n in on]))
sample=rng.sample(allp,60)
L=[]
for i,p in enumerate(sample,1):
    h1=[n for n in o1 if p in S(n)]; h2=[n for n in o2 if p in S(n)]
    f=rng.random()<0.5
    a,b=(h2,h1) if f else (h1,h2)
    iid=f'P{i:02d}'; key[iid]={'A':'option2' if f else 'option1','B':'option1' if f else 'option2','pathway':p}
    L.append(f'## ITEM {iid}\nPathway: {pname[p][0]} [{pname[p][1]}]\n\nA, top-level entries containing it:\n'+'\n'.join(f'- {label(n)} ({len(S(n))} pathways)' for n in sorted(a,key=lambda n:-len(S(n))))+'\n\nB, top-level entries containing it:\n'+'\n'.join(f'- {label(n)} ({len(S(n))} pathways)' for n in sorted(b,key=lambda n:-len(S(n)))))
open(OUT+'/inputs/testB.md','w').write('\n\n'.join(L)+'\n')
json.dump(key,open(OUT+'/KEY_DO_NOT_SHARE_topcompare.json','w'),indent=1)
