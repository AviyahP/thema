import csv,collections,os
HERE=os.path.dirname(os.path.abspath(__file__)); D=os.path.abspath(HERE+'/..'); T=os.path.abspath(HERE+'/../../../..')
R=T+'/data/ontology/v0.4-leaves/thema_L_x2_O50_rec2/'; F=T+'/data/ontology/frozen/working-O50-2026-10-14/'
def tsv(p): return list(csv.DictReader(open(p),delimiter='\t'))
areas={r['node']:r for r in tsv(R+'areas.tsv')}
am=collections.defaultdict(set)
for r in tsv(R+'area_members.tsv'): am[r['node']].add(r['key'])
om=collections.defaultdict(set)
for r in tsv(F+'members.tsv'): om[r['node']].add(r['key'])
U=collections.defaultdict(set)
for e in tsv(R+'area_edges.tsv'): U[e['parent']].add(e['child'])
def um(u): return {u[6:]} if u.startswith('loose:') else om[u]
roots={r['root']:r['node'] for r in tsv(D+'/roots.tsv')}
keep=[a for a in areas if len(am[a])<=1000]
def unionU(a): return set().union(*[um(u) for u in U[a]]) if U[a] else set()
extra={a:am[a]-unionU(a) for a in keep}
print('areas whose pathway set has pathways from none of their themes:',sum(1 for a in keep if extra[a]),'of',len(keep))
# recompute 'mostly inside' for roots using theme-union sets
rs={g:(unionU(n) if n in areas else om[n]) for g,n in roots.items()}
print('R43 extra:',len(extra[roots['R43']]),' R43 theme-union inside R04 theme-union:',len(rs['R43']-rs['R04']),'outside')
strict=[];near=[]
for g in sorted(rs):
    for h in rs:
        if h==g or len(rs[h])<=len(rs[g]): continue
        out=len(rs[g]-rs[h])
        if out==0: strict.append((g,h))
for g in sorted(rs):
    best=max((len(rs[g]&rs[h])/len(rs[g]),h) for h in rs if h!=g)
    if best[0]>=0.8: near.append((g,f'{best[0]:.0%}',best[1]))
print('roots strictly inside another root when areas = union of their themes:',len(set(g for g,h in strict)),sorted(set(g for g,h in strict)))
print('roots >=80% inside another (theme-union):',len(near))
