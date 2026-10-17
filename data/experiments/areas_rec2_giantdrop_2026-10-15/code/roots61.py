import csv,collections,os,json
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
vroots=sorted([n for n in V if not (par[n]-gi)],key=lambda n:-len(V[n]))
old={r['node']:r['root'] for r in tsv(D+'/roots.tsv')}
print('rec2fix roots',len(vroots),'same set as 15 Oct list:',set(vroots)==set(old))
L={x['root']:x for x in json.load(open(D+'/root_labels.json'))}
R61=[n for n in vroots if n not in ('n03376','b2_00313')]
for n in R61:
    best=max(((len(V[n]&V[m])/len(V[n]|V[m]),m) for m in R61 if m!=n))
    ins=max(((len(V[n]&V[m])/len(V[n]),m) for m in R61 if m!=n and len(V[m])>len(V[n])),default=(0,'-'))
    rid=old.get(n,'?')
    print(f"{rid}|{len(V[n])}|{L[rid]['label'] if rid in L else '?'}|J {best[0]:.2f} {old.get(best[1])}|in {ins[0]:.0%} {old.get(ins[1],'-')}")
