import sys,json,os; sys.path.insert(0,'.')
exec(open(os.path.expanduser('~/np_build.py')).read().split("ok={k")[0])
P=ROOT+'data/experiments/naming_pilot_2026-10-11/'
SC=json.load(open(P+'inputs/confusables_after_dedup.json')); rep=json.load(open(P+'inputs/repro_subset.json'))
os.makedirs(P+'c1b/inputs',exist_ok=True)
def namer_item(t,ci):
    r=random.Random(seed(f'{t}:{ci}'))
    mem=[render(k) for k in sorted(M[t])]; r.shuffle(mem)
    cf=list(SC[t]); r.shuffle(cf)
    cl=[dict(confusable=f'C{j+1}',n_shared=len(M[t]&M[c]),only_in_theme=sorted(render(k) for k in M[t]-M[c]),only_in_confusable=sorted(render(k) for k in M[c]-M[t])) for j,c in enumerate(cf)]
    return dict(theme_id=t,size=len(M[t]),members=mem,confusables=cl)
order=list(rep); random.Random(9).shuffle(order)
for run,seeds in [('M',[3,4]),('R',[13,14])]:
    for s in seeds:
        for b in range(2): json.dump([namer_item(t,s) for t in order[b*30:(b+1)*30]],open(P+f'c1b/inputs/c1b{run}_seed{s}_b{b+1}.json','w'),indent=1)
print(sorted(os.listdir(P+'c1b/inputs')))
