import sys,json,os,glob; sys.path.insert(0,'.')
exec(open(os.path.expanduser('~/np_build.py')).read().split("ok={k")[0])
P=ROOT+'data/experiments/naming_pilot_2026-10-11/'
SC=json.load(open(P+'inputs/confusables_after_dedup.json'))
os.makedirs(P+'c1b/selection',exist_ok=True)
items=[];key={}
for f in sorted(glob.glob(P+'c1b/raw/c1b*_seed*_b*.out.json')):
    run=f.split('/c1b')[-1][0]; s=int(f.split('_seed')[1].split('_')[0])
    for o in json.load(open(f)):
        t=o['theme_id']
        if not o.get('nameable',True): continue
        cl=[t]+SC[t]; r=random.Random(seed(f'{t}:S{s}')); r.shuffle(cl)
        common=set.intersection(*(M[c] for c in cl)); L='ABCDE'[:len(cl)]
        items.append(dict(name=o['name'],in_all=sorted(render(k) for k in common),also_in={l:sorted(render(k) for k in M[c]-common) for l,c in zip(L,cl)}))
        key[len(items)-1]=dict(theme=t,run=run,seed=s,correct=L[cl.index(t)])
idx=list(range(len(items))); random.Random(77).shuffle(idx)
K={};out=[]
for n,i in enumerate(idx):
    iid=f'Q{n:04d}'; it=dict(item_id=iid,**items[i]); out.append(it); K[iid]=key[i]
json.dump(K,open(P+'c1b/selection/KEY_DO_NOT_SHARE.json','w'))
for b in range(0,len(out),48): json.dump(out[b:b+48],open(P+f'c1b/selection/sel_{b//48+1:02d}.json','w'),indent=1)
print(len(out),sorted(os.listdir(P+'c1b/selection')))
