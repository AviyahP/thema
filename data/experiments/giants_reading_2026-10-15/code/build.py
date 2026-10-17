import csv,collections,os,json,random
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.abspath(HERE+'/..'); T=os.path.abspath(HERE+'/../../../..')
X=T+'/data/ontology/v0.4-leaves/thema_L_x2_O50_rec2fix/'; F=T+'/data/ontology/frozen/working-O50-2026-10-14/'
csv.field_size_limit(10**9)
def tsv(p): return list(csv.DictReader(open(p),delimiter='\t'))
pname={r['source']+':'+r['source_id']:(r['name'],r['source']) for r in tsv(T+'/data/pathways.tsv')}
om=collections.defaultdict(set)
for r in tsv(F+'members.tsv'): om[r['node']].add(r['key'])
on={r['node']:r for r in tsv(F+'nodes.tsv')}
am=collections.defaultdict(set)
for x in tsv(X+'area_members.tsv'): am[x['node']].add(x['key'])
agi=[x['node'] for x in tsv(X+'giants.tsv')]
ogi=[n for n in om if len(om[n])>1000]
ech=collections.defaultdict(set)
for e in tsv(X+'area_edges.tsv'): ech[e['parent']].add(e['child'])
def S(n): return am[n] if n in am else ({n[6:]} if n.startswith('loose:') else om[n])
G={g:S(g) for g in agi+ogi}
cands=sorted(set(n for n in om if 10<=len(om[n])<=150 and n not in ogi)|set(a for a in am if a not in agi and 10<=len(am[a])<=150))
kids={}
for g in agi+ogi:
    ins=[c for c in cands if S(c)<=G[g] and c!=g]
    kids[g]=sorted(c for c in ins if not any(c!=d and S(c)<S(d) for d in ins))
pool=sorted(set(n for n in om if 10<=len(om[n])<=150)|set(a for a in am if a not in agi and 10<=len(am[a])<=150))
def render(n):
    ks=sorted(S(n),key=lambda k:pname[k][0].lower())
    return [f'- {pname[k][0]} [{pname[k][1]}]' for k in ks]
# G1 label inputs
order=sorted(G,key=lambda g:-len(G[g]))
gid={g:f'G{i:02d}' for i,g in enumerate(order,1)}
for g in order:
    L=[f'# {gid[g]}  ({len(G[g])} pathways)','']+render(g)
    open(f'{OUT}/label_inputs/{gid[g]}.md','w').write('\n'.join(L)+'\n')
# G2 items
rng=random.Random(20261016); items=[]; key={}
for g in order:
    elig=[c for c in kids[g] if 10<=len(S(c))<=150]
    intr_pool=[n for n in pool if len(S(n)&G[g])<0.5*len(S(n))]
    for j in range(5):
        ins=rng.sample(elig,min(5,len(elig))); intr=rng.choice(intr_pool)
        units=ins+[intr]; rng.shuffle(units); letters='ABCDEF'[:len(units)]
        iid=f'I{len(items)+1:02d}'
        key[iid]={'giant':g,'gid':gid[g],'intruder':letters[units.index(intr)],'units':dict(zip(letters,units)),'n_eligible':len(elig)}
        T_=[f'## ITEM {iid}']
        for l,u in zip(letters,units):
            T_.append(f'### Unit {l} ({len(S(u))} pathways)'); T_+=render(u)
        items.append((iid,'\n'.join(T_)))
rng.shuffle(items)
for b in range(4):
    chunk=sorted(items[b::4])
    open(f'{OUT}/g2_batches/G2_b{b+1}.md','w').write('\n\n'.join(t for _,t in chunk)+'\n')
json.dump(key,open(f'{OUT}/KEY_DO_NOT_SHARE_giants.json','w'),indent=1)
json.dump({gid[g]:{'node':g,'size':len(G[g]),'kind':'area giant' if g in agi else 'O50 giant','eligible_children':len([c for c in kids[g] if 10<=len(S(c))<=150])} for g in order},open(f'{OUT}/giants_index.json','w'),indent=1)
for g in order: print(gid[g],g,len(G[g]),'area' if g in agi else 'O50','eligible children',len([c for c in kids[g] if 10<=len(S(c))<=150]))
