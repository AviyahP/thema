import csv,collections,os,json
T=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','..','..')
T=os.path.abspath(T)
R=T+'/data/ontology/v0.4-leaves/thema_L_x2_O50_rec2/'; F=T+'/data/ontology/frozen/working-O50-2026-10-14/'
NM=T+'/data/experiments/naming_O50_2026-10-14/'
OUT=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
csv.field_size_limit(10**9)
def tsv(p): return list(csv.DictReader(open(p),delimiter='\t'))
pname={}
for r in tsv(T+'/data/pathways.tsv'): pname[r['source']+':'+r['source_id']]=(r['name'],r['source'],r['n_genes'])
areas={r['node']:r for r in tsv(R+'areas.tsv')}
amem=collections.defaultdict(set)
for r in tsv(R+'area_members.tsv'): amem[r['node']].add(r['key'])
anch={r['node']:r for r in tsv(R+'anchors.tsv')}
omem=collections.defaultdict(set)
for r in tsv(F+'members.tsv'): omem[r['node']].add(r['key'])
for a in anch: amem[a]=omem[a]
names={r['theme_id']:r['name'] for r in tsv(NM+'dedup/final_names_O50_lite_unique.tsv')}
for r in tsv(NM+'name_overrides.tsv') if os.path.exists(NM+'name_overrides.tsv') else []:
    k=list(r.keys()); names[r[k[0]]]=r[k[1]]
U=collections.defaultdict(set)
for e in tsv(R+'area_edges.tsv'): U[e['parent']].add(e['child'])
A={a:set(areas[a]['children'].split()) for a in areas}
CAP=1000
big={a for a in areas if len(amem[a])>CAP}
def desc_units(a):
    s=set()
    for c in A[a]: s|=U[c]|desc_units(c)
    return s
direct={a:(U[a]-desc_units(a)) for a in areas}
par=collections.defaultdict(set)
for a in areas:
    for c in A[a]: par[c].add(a)
keep=[a for a in areas if a not in big]
roots=[a for a in keep if not (par[a]-big)]+list(anch)
def umem(u): return {u[6:]} if u.startswith('loose:') else omem[u]
roots.sort(key=lambda r:-len(amem[r]))
rows=[]
for i,r in enumerate(roots,1):
    rid=f'R{i:02d}'
    kids_a=sorted([c for c in A.get(r,set()) if c not in big],key=lambda c:-len(amem[c]))
    kids_u=sorted(direct.get(r,set()) if r in areas else set(anch[r]['children'].split()),key=lambda u:-len(umem(u)))
    L=[f'# {rid}  ({r})',f'size: {len(amem[r])} pathways; ' + ('anchor (O50 theme)' if r in anch else f'area, {areas[r]["n_units"]} units, support {areas[r]["support"]}'),'']
    L.append(f'## Sub-areas ({len(kids_a)})')
    for c in kids_a: L.append(f'- {c}: {len(amem[c])} pathways')
    L.append(f'## Themes directly under it ({len(kids_u)})')
    for u in kids_u: L.append(f'- {u} ({len(umem(u))}): {names.get(u, pname.get(u[6:],("?",))[0] if u.startswith("loose:") else "[unnamed, >200 members]")}')
    L.append(f'## All member pathways ({len(amem[r])})')
    for k in sorted(amem[r],key=lambda k:pname.get(k,(k,))[0].lower()):
        n=pname.get(k,(k,'?','?')); L.append(f'- {n[0]} [{n[1]}]')
    open(f'{OUT}/inputs/{rid}.md','w').write('\n'.join(L)+'\n')
    rows.append((rid,r,len(amem[r]),'anchor' if r in anch else 'area',len(kids_a),len(kids_u)))
with open(f'{OUT}/roots.tsv','w') as f:
    f.write('root\tnode\tpathways\tkind\tsub_areas\tdirect_themes\n')
    for x in rows: f.write('\t'.join(map(str,x))+'\n')
missing=sum(1 for r in roots for k in amem[r] if k not in pname)
print(len(roots),'roots; missing names',missing)
