import csv,collections,os,itertools
HERE=os.path.dirname(os.path.abspath(__file__)); T=os.path.abspath(HERE+'/../../../..')
R=T+'/data/ontology/v0.4-leaves/thema_L_x2_O50_rec2/'; F=T+'/data/ontology/frozen/working-O50-2026-10-14/'
def tsv(p): return list(csv.DictReader(open(p),delimiter='\t'))
areas={r['node']:r for r in tsv(R+'areas.tsv')}
am=collections.defaultdict(set)
for r in tsv(R+'area_members.tsv'): am[r['node']].add(r['key'])
om=collections.defaultdict(set)
for r in tsv(F+'members.tsv'): om[r['node']].add(r['key'])
anch=[r['node'] for r in tsv(R+'anchors.tsv')]
U=collections.defaultdict(set)
for e in tsv(R+'area_edges.tsv'): U[e['parent']].add(e['child'])
def um(u): return {u[6:]} if u.startswith('loose:') else om[u]
keep=[a for a in areas if len(am[a])<=1000]
def J(a,b): return len(a&b)/len(a|b)
print('1) area vs area (rules applied in build): pairs J>=0.5:',sum(J(am[a],am[b])>=0.5 for a,b in itertools.combinations(keep,2)))
# chain: child area covering >=85% of parent
ch=0
for a in keep:
    for c in areas[a]['children'].split():
        if c in am and len(am[c])>=0.85*len(am[a]): ch+=1
print('   area parent-child chains >=0.85:',ch)
print('2) anchor vs anchor:')
for a,b in itertools.combinations(anch,2):
    i=len(om[a]&om[b]); print(f'   {a}({len(om[a])}) {b}({len(om[b])}) J {J(om[a],om[b]):.2f} inside-smaller {i/min(len(om[a]),len(om[b])):.0%}')
print('3) anchor vs area: J>=0.5:',[(x,a,round(J(om[x],am[a]),2)) for x in anch for a in keep if J(om[x],am[a])>=0.5])
print('   area strictly inside an anchor:',sum(am[a]<=om[x] for x in anch for a in keep),' anchor strictly inside an area:',[(x,a) for x in anch for a in keep if om[x]<=am[a]])
print('   area >=85% covered by one anchor (chain-like):',[(a,len(am[a]),x,f'{len(am[a]&om[x])/len(am[a]):.0%}') for a in keep for x in anch if len(am[a]&om[x])>=0.85*len(am[a])])
print('4) area vs its own units (cross-level): area >=85% covered by a single unit:')
bad=[]
for a in keep:
    best=max(((len(am[a]&um(u))/len(am[a]),u) for u in U[a]),default=(0,None))
    if best[0]>=0.85: bad.append((a,len(am[a]),best[1],len(um(best[1])),round(best[0],2)))
    j=max((J(am[a],um(u)) for u in U[a]),default=0)
print('   ',len(bad),bad[:10])
print('   area twin (J>=0.5) with a unit anywhere in O50:',sum(1 for a in keep if any(J(am[a],om[u])>=0.5 for u in om if len(om[u])>=0.5*len(am[a]) and len(om[u])<=2*len(am[a]))))
