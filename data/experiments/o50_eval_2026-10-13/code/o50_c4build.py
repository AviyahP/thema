import sys,os,csv,collections,json,random; sys.path.insert(0,'.')
exec(open(os.path.expanduser('~/np_build.py')).read().split("ok={k")[0])
P=ROOT+'data/experiments/o50_eval_2026-10-13/'
O=ROOT+'data/ontology/v0.4-leaves/thema_L_x2_O50/'
MO=collections.defaultdict(set)
for r in csv.DictReader(open(O+'members.tsv'),delimiter='\t'): MO[r['node']].add(r['key'])
c85sets={frozenset(s) for s in M.values()}
new=sorted(k for k,s in MO.items() if frozenset(s) not in c85sets)
rng=random.Random(20261013); rng.shuffle(new)
items=[]
for k in new:
    mem=[render(m) for m in sorted(MO[k])]; random.Random('c4'+k).shuffle(mem)
    shown=mem if len(mem)<=200 else mem[:60]
    items.append(dict(id=k,size=len(mem),shown='all' if len(mem)<=200 else 'random 60',members=shown))
B=40
for b in range(0,len(items),B): json.dump(items[b:b+B],open(P+f'c4/C4_{b//B+1:02d}.json','w'),indent=1)
print(len(items),'items in',(len(items)+B-1)//B,'files')
