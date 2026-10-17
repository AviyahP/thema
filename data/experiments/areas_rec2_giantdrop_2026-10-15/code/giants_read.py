import csv,collections,os,json
HERE=os.path.dirname(os.path.abspath(__file__)); D=os.path.abspath(HERE+'/..'); T=os.path.abspath(HERE+'/../../../..')
X=T+'/data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix/'; F=T+'/data/ontology/frozen/working-O50-2026-10-14/'
def tsv(p): return list(csv.DictReader(open(p),delimiter='\t'))
om=collections.defaultdict(set)
for r in tsv(F+'members.tsv'): om[r['node']].add(r['key'])
am=collections.defaultdict(set)
for x in tsv(X+'area_members.tsv'): am[x['node']].add(x['key'])
gi=[x['node'] for x in tsv(X+'giants.tsv')]
old={r['node']:r['root'] for r in tsv(D+'/roots.tsv')}
L={x['root']:x['label'] for x in json.load(open(D+'/root_labels.json'))}
def S(n): return am[n] if n in am else om[n]
og=[n for n in om if len(om[n])>1000]
def read(gid,G,tag):
    rows=[]
    for n,r in old.items():
        s=S(n); i=len(s&G)/len(s)
        if i>=0.8: rows.append((len(s),r,i))
    rows.sort(reverse=True)
    cov=set().union(*[S(n) for n,r in old.items() if len(S(n)&G)>=0.8*len(S(n))]) if rows else set()
    print(f'\n{tag} {gid}: {len(G)} pathways; covered by the roots below: {len(cov&G)/len(G):.0%}')
    for sz,r,i in rows: print(f'   {r} ({sz}, {i:.0%} inside): {L[r]}')
for g in sorted(gi,key=lambda g:-len(am[g])): read(g,am[g],'AREA GIANT')
for g in sorted(og,key=lambda g:-len(om[g])): read(g,om[g],'O50 GIANT')
# overlap among area giants
import itertools
print('\narea-giant pair overlaps (J):',sorted([(round(len(am[a]&am[b])/len(am[a]|am[b]),2),a,b) for a,b in itertools.combinations(gi,2)],reverse=True)[:8])
