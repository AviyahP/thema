import csv,collections,os
HERE=os.path.dirname(os.path.abspath(__file__)); T=os.path.abspath(HERE+'/../../../..')
X=T+'/data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix/'; F=T+'/data/ontology/frozen/working-O50-2026-10-14/'
def tsv(p): return list(csv.DictReader(open(p),delimiter='\t'))
SHARE,MAXMISS=0.98,5
def near(S):
    idx=collections.defaultdict(set)
    for n,s in S.items():
        for k in s: idx[k].add(n)
    out={}
    for c,s in S.items():
        cnt=collections.Counter(m for k in s for m in idx[k] if m!=c and len(S[m])>len(s))
        hits=[(m,len(s)-i) for m,i in cnt.items() if 0<len(s)-i<=MAXMISS and i>=SHARE*len(s)]
        if hits: out[c]=hits
    return out
# O50
om=collections.defaultdict(set)
for r in tsv(F+'members.tsv'): om[r['node']].add(r['key'])
on={r['node']:r for r in tsv(F+'nodes.tsv')}
giants={n for n in om if len(om[n])>1000}
S={n:om[n] for n in om if n not in giants}
r=near(S)
roots=[n for n in S if not (set(on[n]['parents'].split())-giants)]
print('O50 (giants out): themes that would gain a parent:',len(r),'of',len(S),'| of them O50 roots:',sum(1 for n in r if n in roots),'of',len(roots))
print('   pathways to add (sum of misses, before upward propagation):',sum(min(m for _,m in h) for h in r.values()))
# rec2fix view
am=collections.defaultdict(set)
for x in tsv(X+'area_members.tsv'): am[x['node']].add(x['key'])
gi={x['node'] for x in tsv(X+'giants.tsv')} if os.path.exists(X+'giants.tsv') else set()
areas={x['node']:x for x in tsv(X+'areas.tsv')}
anch=[x['node'] for x in tsv(X+'anchors.tsv')]
V={a:am[a] for a in areas if a not in gi}
for a in anch: V[a]=om[a]
edges=tsv(X+'area_edges.tsv'); par=collections.defaultdict(set)
for e in edges: par[e['child']].add(e['parent'])
vroots=[n for n in V if not (par[n]-gi)]
r2=near({**V})
hit=[n for n in vroots if n in r2]
print('rec2fix view: roots',len(vroots),'| roots that would become children:',len(hit))
for n in sorted(hit,key=lambda n:-len(V[n])): print('   ',n,len(V[n]),'->',[(m,len(V[m]),f'missing {k}') for m,k in r2[n]][:3])
print('giants file found:',bool(gi),len(gi))
print('--- the 63 roots: best container among other view nodes, share inside and pathways missing')
rows=[]
for n in vroots:
    best=None
    for m in V:
        if m==n or len(V[m])<=len(V[n]): continue
        i=len(V[n]&V[m]); 
        if best is None or i>best[0]: best=(i,m)
    if best: rows.append((best[0]/len(V[n]),len(V[n])-best[0],n,len(V[n]),best[1],len(V[best[1]])))
rows.sort(reverse=True)
b=collections.Counter()
for s,miss,*_ in rows:
    b['>=98%' if s>=.98 else '95-98%' if s>=.95 else '90-95%' if s>=.9 else '80-90%' if s>=.8 else '<80%']+=1
print(dict(b))
for x in rows[:14]: print(f'   {x[2]} ({x[3]}) {x[0]:.1%} inside {x[4]} ({x[5]}), missing {x[1]}')
