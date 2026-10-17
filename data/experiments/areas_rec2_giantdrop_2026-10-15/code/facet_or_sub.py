import csv,collections,os,json,itertools
HERE=os.path.dirname(os.path.abspath(__file__)); D=os.path.abspath(HERE+'/..'); T=os.path.abspath(HERE+'/../../../..')
X=T+'/data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix/'; F=T+'/data/ontology/frozen/working-O50-2026-10-14/'
def tsv(p): return list(csv.DictReader(open(p),delimiter='\t'))
om=collections.defaultdict(set)
for r in tsv(F+'members.tsv'): om[r['node']].add(r['key'])
am=collections.defaultdict(set)
for x in tsv(X+'area_members.tsv'): am[x['node']].add(x['key'])
gi={x['node'] for x in tsv(X+'giants.tsv')}
areas={x['node'] for x in tsv(X+'areas.tsv')}
anch=[x['node'] for x in tsv(X+'anchors.tsv')]
V={a:am[a] for a in areas if a not in gi}
for a in anch: V[a]=om[a]
par=collections.defaultdict(set)
for e in tsv(X+'area_edges.tsv'): par[e['child']].add(e['parent'])
old={r['node']:r['root'] for r in tsv(D+'/roots.tsv')}
inv={v:k for k,v in old.items()}
R61=[n for n in old if n not in ('n03376','b2_00313')]
DOM=['R06','R07','R04','R14','R05','R08','R03','R11','R09','R01','R16','R20','R29','R18','R33','R02']
dom=[inv[r] for r in DOM]
sub=[n for n in R61 if n not in dom]
fac=subc=mix=0
rows=[]
for n in sub:
    s=V[n]
    host=max(dom,key=lambda d:len(s&V[d]))
    inside=len(s&V[host])/len(s)
    out=s-V[host]
    if not out: kind='sub'; second=None; sh=0
    else:
        second=max((d for d in dom if d!=host),key=lambda d:len(out&V[d]))
        sh=len(out&V[second])/len(out)
    # facet if a real second block: >=10% of the node outside host AND >=60% of that outside sits in one other domain
    if (1-inside)>=0.10 and sh>=0.6: kind='FACET'
    elif inside>=0.9: kind='sub-area'
    else: kind='mixed/unclear'
    rows.append((old[n],len(s),old[host],f'{inside:.0%}',old.get(second,'-'),f'{sh:.0%}',kind))
c=collections.Counter(r[-1] for r in rows); print(dict(c))
for r in sorted(rows,key=lambda r:r[-1]): print(' | '.join(map(str,r)))
print('--- unions of domain pairs (pathways):')
sizes=[len(V[a]|V[b]) for a,b in itertools.combinations(dom,2)]
print('pairs',len(sizes),'union <=1000:',sum(x<=1000 for x in sizes),'min',min(sizes),'median',sorted(sizes)[len(sizes)//2])
