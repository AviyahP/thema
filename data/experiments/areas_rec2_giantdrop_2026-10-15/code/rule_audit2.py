import csv,collections,os,itertools
HERE=os.path.dirname(os.path.abspath(__file__)); T=os.path.abspath(HERE+'/../../../..')
R=T+'/data/ontology/v0.4-leaves/thema_L_x2_O50_rec2/'; F=T+'/data/ontology/frozen/working-O50-2026-10-14/'
def tsv(p): return list(csv.DictReader(open(p),delimiter='\t'))
areas={r['node']:r for r in tsv(R+'areas.tsv')}
am=collections.defaultdict(set)
for r in tsv(R+'area_members.tsv'): am[r['node']].add(r['key'])
om=collections.defaultdict(set)
for r in tsv(F+'members.tsv'): om[r['node']].add(r['key'])
on={r['node']:r for r in tsv(F+'nodes.tsv')}
U=collections.defaultdict(set)
for e in tsv(R+'area_edges.tsv'): U[e['parent']].add(e['child'])
def J(a,b): return len(a&b)/len(a|b)
def classify(S,name):
    ks=list(S); nested=non=0; ex=[]
    idx=collections.defaultdict(set)
    for k in ks:
        for p in S[k]: idx[p].add(k)
    seen=set()
    for a in ks:
        cand=collections.Counter(b for p in S[a] for b in idx[p] if b>a)
        for b,i in cand.items():
            j=i/(len(S[a])+len(S[b])-i)
            if j>=0.5:
                if S[a]<=S[b] or S[b]<=S[a]: nested+=1
                else: non+=1; ex.append((round(j,2),a,len(S[a]),b,len(S[b])))
    ex.sort(reverse=True)
    print(f'{name}: pairs J>=0.5 nested {nested}, NOT nested {non}; top: {ex[:6]}')
classify({a:am[a] for a in areas if len(am[a])<=1000},'areas (rec2, giants dropped)')
classify({n:om[n] for n in om if len(om[n])<=1000},'O50 themes (giants excluded)')
# cross-level: area vs a unit under it / not under it
under=over=0; exs=[]
for a in areas:
    if len(am[a])>1000: continue
    for u in om:
        if len(om[u])<0.5*len(am[a]) or len(om[u])>2*len(am[a]) or len(om[u])>1000: continue
        j=J(am[a],om[u])
        if j>=0.5:
            if u in U[a]: under+=1
            else: over+=1; exs.append((round(j,2),a,len(am[a]),u,len(om[u])))
print('area-vs-O50 theme twins J>=0.5: theme under the area',under,'| theme NOT under the area',over, sorted(exs,reverse=True)[:5])
