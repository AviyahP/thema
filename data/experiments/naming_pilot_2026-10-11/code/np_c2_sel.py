import sys,json,os,glob; sys.path.insert(0,'.')
exec(open(os.path.expanduser('~/np_build.py')).read().split("ok={k")[0])
P=ROOT+'data/experiments/naming_pilot_2026-10-11/'
SC=json.load(open(P+'inputs/confusables_after_dedup.json'))
os.makedirs(P+'c2/selection',exist_ok=True)
for run,base in [('A',100),('B',110)]:
    C={}
    for f in glob.glob(P+f'c2/raw/c2{run}_slot*_b*.out.json'):
        s=int(f.split('_slot')[1][0])
        for o in json.load(open(f)): C[(o['theme_id'],s)]=o
    items=[];key={}
    order=sorted(C); random.Random(base).shuffle(order)
    for i,(t,s) in enumerate(order):
        o=C[(t,s)]
        if not o.get('nameable',True): continue
        cl=[t]+SC[t]; r=random.Random(seed(f'{t}:S{base+s}')); r.shuffle(cl)
        common=set.intersection(*(M[c] for c in cl)); L='ABCDE'[:len(cl)]
        iid=f'{run}{i:04d}'
        items.append(dict(item_id=iid,name=o['name'],in_all=sorted(render(k) for k in common),also_in={l:sorted(render(k) for k in M[c]-common) for l,c in zip(L,cl)}))
        key[iid]=dict(theme=t,cand=s,correct=L[cl.index(t)])
    json.dump(key,open(P+f'c2/selection/KEY_DO_NOT_SHARE_{run}.json','w'))
    for b in range(0,len(items),50): json.dump(items[b:b+50],open(P+f'c2/selection/{run}_sel_{b//50+1:02d}.json','w'),indent=1)
    print(run,len(items))
