import csv,collections,os,sys
HERE=os.path.dirname(os.path.abspath(__file__)); D=os.path.abspath(HERE+'/..'); T=os.path.abspath(HERE+'/../../../..')
R=T+'/data/ontology/v0.4-leaves/thema_L_x2_O50_rec2/'; F=T+'/data/ontology/frozen/working-O50-2026-10-14/'
def tsv(p): return list(csv.DictReader(open(p),delimiter='\t'))
pname={r['source']+':'+r['source_id']:r['name'] for r in tsv(T+'/data/pathways.tsv')}
areas={r['node']:r for r in tsv(R+'areas.tsv')}
am=collections.defaultdict(set)
for r in tsv(R+'area_members.tsv'): am[r['node']].add(r['key'])
om=collections.defaultdict(set)
for r in tsv(F+'members.tsv'): om[r['node']].add(r['key'])
names={r['theme_id']:r['name'] for r in tsv(T+'/data/experiments/naming_O50_2026-10-14/dedup/final_names_O50_lite_unique.tsv')}
U=collections.defaultdict(set)
for e in tsv(R+'area_edges.tsv'): U[e['parent']].add(e['child'])
A={a:set(areas[a]['children'].split()) for a in areas}
roots={r['root']:r['node'] for r in tsv(D+'/roots.tsv')}
def mem(n): return am[n] if n in areas else ({n[6:]} if n.startswith('loose:') else om[n])
def desc(a):
    s=set(A[a])|U[a]
    for c in A[a]: s|=desc(c)
    return s
small,big=roots[sys.argv[1]],roots[sys.argv[2]]
S,B=am[small],am[big]
print(sys.argv[1],small,len(S),'|',sys.argv[2],big,len(B),'| shared',len(S&B),'| strays',len(S-B))
print('strays:',[pname[k] for k in S-B])
db=desc(big)
du=desc(small)
direct_units=U[small]-set().union(*[desc(c) for c in A[small]]) if A[small] else U[small]
print(f'\nDirect children of {sys.argv[1]}: {len(A[small])} sub-areas, {len(direct_units)} themes')
for c in sorted(A[small],key=lambda c:-len(mem(c))):
    print(f'  area {c} ({len(mem(c))}): also under {sys.argv[2]}? {c in db}; inside {sys.argv[2]}: {len(mem(c)&B)}/{len(mem(c))}')
units=sorted(U[small],key=lambda u:-len(mem(u)))
under=sum(u in db for u in units); print(f'\nAll {len(units)} themes under {sys.argv[1]}: {under} are also under {sys.argv[2]}')
for u in units:
    if u not in db: print('  NOT under big:',u,len(mem(u)),names.get(u,u),'| inside big',len(mem(u)&B),'/',len(mem(u)))
