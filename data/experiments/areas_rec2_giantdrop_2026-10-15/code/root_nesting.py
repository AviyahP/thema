import csv,collections,os,json
HERE=os.path.dirname(os.path.abspath(__file__)); D=os.path.abspath(HERE+'/..'); T=os.path.abspath(HERE+'/../../../..')
R=T+'/data/ontology/v0.4-leaves/thema_L_x2_O50_rec2/'; F=T+'/data/ontology/frozen/working-O50-2026-10-14/'
def tsv(p): return list(csv.DictReader(open(p),delimiter='\t'))
am=collections.defaultdict(set)
for r in tsv(R+'area_members.tsv'): am[r['node']].add(r['key'])
om=collections.defaultdict(set)
for r in tsv(F+'members.tsv'): om[r['node']].add(r['key'])
roots={r['root']:r['node'] for r in tsv(D+'/roots.tsv')}
S={g:(am[n] if n.startswith('b2_') else om[n]) for g,n in roots.items()}
L={x['root']:x for x in json.load(open(D+'/root_labels.json'))}
cnt=collections.Counter(k for g in S for k in S[g])
rows=[]
for g in sorted(S):
    best=max((len(S[g]&S[h])/len(S[g]),h) for h in S if h!=g)
    own=sum(cnt[k]==1 for k in S[g])/len(S[g])
    rows.append((g,len(S[g]),best[0],best[1],own))
nest=[r for r in rows if r[2]>=0.8]
print('roots >=80% inside another root:',len(nest))
for r in nest: print(f'  {r[0]} ({r[1]}) {r[2]:.0%} inside {r[3]} ({len(S[r[3]])}); own {r[4]:.0%} | {L[r[0]]["label"]}  ->  {L[r[3]]["label"]}')
mid=[r for r in rows if 0.6<=r[2]<0.8]; print('60-80% inside another:',[(r[0],f'{r[2]:.0%}',r[3]) for r in mid])
print('own share (pathways in no other root) median', sorted(r[4] for r in rows)[len(rows)//2])
