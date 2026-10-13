import sys,json,os; sys.path.insert(0,'.')
exec(open(os.path.expanduser('~/np_build.py')).read().split("ok={k")[0])
P=ROOT+'data/experiments/naming_pilot_2026-10-11/'
F=json.load(open(P+'selection/final_names.json'))
import re
def norm(s): return ' '.join(re.sub(r'[^a-z0-9 ]',' ',s.lower()).split())
SC=json.load(open(P+'inputs/sample_and_confusables.json'))['confusables']
pairs=[[t for t,v in F['main'].items() if not v['unnameable'] and norm(v['name'])==d] for d in F['duplicates']]
print(pairs)
for ci in [0,1,2]:
    items=[]
    for grp in pairs:
        for t in grp:
            other=[o for o in grp if o!=t]
            cf=(other+[c for c in SC[t] if c not in other])[:4]
            r=random.Random(seed(f'{t}:{ci+20}'))
            mem=[render(k) for k in sorted(M[t])]; r.shuffle(mem)
            cl=[dict(confusable=f'C{j+1}',n_shared=len(M[t]&M[c]),only_in_theme=sorted(render(k) for k in M[t]-M[c]),only_in_confusable=sorted(render(k) for k in M[c]-M[t])) for j,c in enumerate(cf)]
            items.append(dict(theme_id=t,size=len(M[t]),members=mem,confusables=cl,note=f"The name '{F['main'][t]['name']}' is already used by another theme; give a name that distinguishes this theme."))
            SC[t]=cf
    json.dump(items,open(P+f'inputs/dedup_slot{ci}.json','w'),indent=1)
json.dump(SC,open(P+'inputs/confusables_after_dedup.json','w'))
