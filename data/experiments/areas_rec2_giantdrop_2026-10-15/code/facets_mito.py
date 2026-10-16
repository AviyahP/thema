import csv,collections,os,itertools,sys
HERE=os.path.dirname(os.path.abspath(__file__)); D=os.path.abspath(HERE+'/..'); T=os.path.abspath(HERE+'/../../../..')
R=T+'/data/ontology/v0.4-leaves/thema_L_x2_O50_rec2/'; F=T+'/data/ontology/frozen/working-O50-2026-10-14/'
csv.field_size_limit(10**9)
def tsv(p): return list(csv.DictReader(open(p),delimiter='\t'))
pname={r['source']+':'+r['source_id']:r['name'] for r in tsv(T+'/data/pathways.tsv')}
amem=collections.defaultdict(set)
for r in tsv(R+'area_members.tsv'): amem[r['node']].add(r['key'])
for r in tsv(F+'members.tsv'): amem.setdefault(r['node'],set())
om=collections.defaultdict(set)
for r in tsv(F+'members.tsv'): om[r['node']].add(r['key'])
roots={r['root']:r['node'] for r in tsv(D+'/roots.tsv')}
G=sys.argv[1].split(',')
S={g:(amem[roots[g]] if roots[g].startswith('b2_') else om[roots[g]]) for g in G}
print('sizes',{g:len(S[g]) for g in G})
print('pair: J / shared / shared as % of smaller')
for a,b in itertools.combinations(G,2):
    i=len(S[a]&S[b]); print(f' {a}-{b}: J {i/len(S[a]|S[b]):.2f}  shared {i}  {i/min(len(S[a]),len(S[b])):.0%} of smaller')
cnt=collections.Counter(k for g in G for k in S[g])
U=set(cnt); print('union',len(U),'in all',sum(v==len(G) for v in cnt.values()),'in >=half',sum(v>=len(G)/2 for v in cnt.values()),'in exactly 1',sum(v==1 for v in cnt.values()))
core=[k for k,v in cnt.items() if v>=len(G)-1]
print('CORE (in all or all-but-one):',len(core)); print('  ', '; '.join(sorted(pname[k] for k in core)[:25]))
for g in G:
    own=sorted(pname[k] for k in S[g] if cnt[k]==1)
    print(f'{g} own {len(own)}/{len(S[g])}:', '; '.join(own[:22]))
