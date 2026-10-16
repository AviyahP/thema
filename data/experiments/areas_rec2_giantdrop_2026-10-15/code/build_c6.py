import csv,collections,os,json,random
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.abspath(HERE+'/..'); T=os.path.abspath(HERE+'/../../../..')
R=T+'/data/ontology/v0.4-leaves/thema_L_x2_O50_rec2/'; F=T+'/data/ontology/frozen/working-O50-2026-10-14/'
csv.field_size_limit(10**9)
def tsv(p): return list(csv.DictReader(open(p),delimiter='\t'))
pname={r['source']+':'+r['source_id']:(r['name'],r['source']) for r in tsv(T+'/data/pathways.tsv')}
areas={r['node']:r for r in tsv(R+'areas.tsv')}
amem=collections.defaultdict(set)
for r in tsv(R+'area_members.tsv'): amem[r['node']].add(r['key'])
omem=collections.defaultdict(set)
for r in tsv(F+'members.tsv'): omem[r['node']].add(r['key'])
U=collections.defaultdict(set)
for e in tsv(R+'area_edges.tsv'): U[e['parent']].add(e['child'])
def umem(u): return {u[6:]} if u.startswith('loose:') else omem[u]
allunits=sorted(set().union(*U.values()))
keep=sorted(a for a in areas if len(amem[a])<=1000 and len(U[a])>=4)
rng=random.Random(20261015)
items=[];key={}
for i,a in enumerate(keep,1):
    us=sorted(U[a]); ins=rng.sample(us,min(5,len(us)))
    pool=[u for u in allunits if u not in U[a] and len(umem(u)&amem[a])<0.5*len(umem(u))]
    intr=rng.choice(pool)
    units=ins+[intr]; rng.shuffle(units)
    letters='ABCDEF'[:len(units)]
    iid=f'C{i:03d}'
    key[iid]={'area':a,'intruder':letters[units.index(intr)],'units':dict(zip(letters,units)),'size':len(amem[a]),'support':float(areas[a]['support']),'n_units':len(us)}
    L=[f'## ITEM {iid}']
    for l,u in zip(letters,units):
        ks=sorted(umem(u),key=lambda k:pname[k][0].lower())
        L.append(f'### Unit {l} ({len(ks)} pathways)')
        L+= [f'- {pname[k][0]} [{pname[k][1]}]' for k in ks]
    items.append((iid,'\n'.join(L)))
json.dump(key,open(OUT+'/KEY_DO_NOT_SHARE_C6.json','w'),indent=1)
os.makedirs(OUT+'/c6_batches',exist_ok=True)
NB=10; sz=[0]*NB; bins=[[] for _ in range(NB)]
for iid,t in sorted(items,key=lambda x:-len(x[1])):
    j=sz.index(min(sz)); bins[j].append((iid,t)); sz[j]+=len(t)
for j,b in enumerate(bins,1):
    b.sort()
    open(f'{OUT}/c6_batches/C6_b{j:02d}.md','w').write('\n\n'.join(t for _,t in b)+'\n')
    print(j,len(b),sz[j-1])
print('items',len(items))
