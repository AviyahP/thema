import csv,collections,os,json,random
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.abspath(HERE+'/..'); T=os.path.abspath(HERE+'/../../../..')
B=T+'/data/ontology/v0.4-leaves/thema_L_x2_O50s/'
csv.field_size_limit(10**9)
def tsv(p): return list(csv.DictReader(open(p),delimiter='\t'))
pname={r['source']+':'+r['source_id']:(r['name'],r['source']) for r in tsv(T+'/data/pathways.tsv')}
M=collections.defaultdict(set)
for r in tsv(B+'members.tsv'): M[r['node']].add(r['key'])
L=tsv(OUT+'/large_themes.tsv')
rng=random.Random(20261017)
order=[r['node'] for r in L]; rng.shuffle(order)
gid={n:f'T{i:03d}' for i,n in enumerate(order,1)}
status={r['node']:r['status'] for r in L}
def render(n): return [f'- {pname[k][0]} [{pname[k][1]}]' for k in sorted(M[n],key=lambda k:pname[k][0].lower())]
# reading batches ~ 2500 lines
batches=[[]];lines=0
for n in order:
    t=[f'# {gid[n]} ({len(M[n])} pathways)']+render(n)
    if lines+len(t)>2600 and batches[-1]: batches.append([]); lines=0
    batches[-1].append('\n'.join(t)); lines+=len(t)
for i,b in enumerate(batches,1): open(f'{OUT}/read_inputs/R_b{i:02d}.md','w').write('\n\n---\n\n'.join(b)+'\n')
print('reading batches',len(batches))
# intruder items
pool=[n for n in M if 5<=len(M[n])<=150]
items=[];key={};excl=[]
for n in order:
    ins=[c for c in pool if c!=n and M[c]<M[n]]
    ins=[c for c in ins if not any(c!=d and M[c]<M[d] for d in ins)]
    if len(ins)<4: excl.append((gid[n],len(M[n]),len(ins))); continue
    pick=rng.sample(ins,min(5,len(ins)))
    intr=rng.choice([c for c in pool if len(M[c]&M[n])<0.5*len(M[c])])
    units=pick+[intr]; rng.shuffle(units); letters='ABCDEF'[:len(units)]
    iid=f'I{len(items)+1:03d}'
    key[iid]={'theme':n,'gid':gid[n],'status':status[n],'size':len(M[n]),'intruder':letters[units.index(intr)]}
    t=[f'## ITEM {iid}']
    for l,u in zip(letters,units): t.append(f'### Unit {l} ({len(M[u])} pathways)'); t+=render(u)
    items.append('\n'.join(t))
rng.shuffle(items)
nb=max(1,round(sum(x.count('\n') for x in items)/4000))
for j in range(nb): open(f'{OUT}/intruder_inputs/I_b{j+1:02d}.md','w').write('\n\n'.join(items[j::nb])+'\n')
json.dump({'gid':{v:k for k,v in gid.items()},'status':{gid[n]:status[n] for n in order}},open(OUT+'/review_index.json','w'),indent=1)
json.dump(key,open(OUT+'/KEY_DO_NOT_SHARE_O50s_large.json','w'),indent=1)
print('intruder items',len(items),'batches',nb,'excluded',excl)
