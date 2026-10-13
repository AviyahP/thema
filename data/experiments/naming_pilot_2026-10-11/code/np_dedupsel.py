import sys,json,os; sys.path.insert(0,'.')
exec(open(os.path.expanduser('~/np_build.py')).read().split("ok={k")[0])
P=ROOT+'data/experiments/naming_pilot_2026-10-11/'
SC=json.load(open(P+'inputs/confusables_after_dedup.json'))
items=[];key={}
for s in [0,1,2]:
    for o in json.load(open(P+f'raw/dedup_slot{s}.out.json')):
        t=o['theme_id']; cl=[t]+SC[t]; r=random.Random(seed(f'{t}:S{s+20}')); r.shuffle(cl)
        common=set.intersection(*(M[c] for c in cl)); L='ABCDE'[:len(cl)]
        iid=f'D{len(items):03d}'
        items.append(dict(item_id=iid,name=o['name'],in_all=sorted(render(k) for k in common),also_in={l:sorted(render(k) for k in M[c]-common) for l,c in zip(L,cl)}))
        key[iid]=dict(theme=t,cand=s,correct=L[cl.index(t)])
random.Random(5).shuffle(items)
json.dump(items,open(P+'selection/dedup_sel_01.json','w'),indent=1); json.dump(key,open(P+'selection/KEY_DO_NOT_SHARE_dedup.json','w'))
print(len(items))
