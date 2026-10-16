import csv,collections,os
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
for x in ['n03376','n03315']: print(x,'O50 parents:',on[x]['parents'][:200])
print('n01279 O50 parents:',on['n01279']['parents'])
# O50 themes strictly inside an area but not linked under it (missing containment edges), excluding units
units=set().union(*U.values())
miss=collections.Counter(); ex=[]
alln=[n for n in om if len(om[n])<=1000]
for a in areas:
    if len(am[a])>1000: continue
    for n in alln:
        if n in U[a]: continue
        if om[n] and om[n]<=am[a] and len(om[n])<len(am[a]):
            # is n under some unit of a (then implied)?
            miss['total']+=1
            if n in units: miss['n is a unit, not linked']+=1; ex.append((a,len(am[a]),n,len(om[n])))
print(dict(miss)); print(ex[:8])
nn=0;nex=[]
for a in areas:
    if len(am[a])>1000: continue
    for u in om:
        if len(om[u])>1000 or u in U[a]: continue
        j=J(am[a],om[u])
        if j>=0.5:
            nested = om[u]<=am[a] or am[a]<=om[u]
            if not nested: nn+=1; nex.append((round(j,2),a,len(am[a]),u,len(om[u]),len(am[a]&om[u])))
print('area vs theme (not under it) J>=0.5 and NOT nested:',nn,sorted(nex,reverse=True)[:8])
