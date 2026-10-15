import sys,json,os,random; sys.path.insert(0,'.')
exec(open(os.path.expanduser('~/np_build.py')).read().split("ok={k")[0])
P=ROOT+'data/experiments/core_reading_lowoverlap_2026-10-11/'
L=json.load(open('/tmp/lo_pairs.json')); rng=random.Random(20261015)
samp=[]
for b in (1,2,3):
    pool=sorted([x for x in L if int(x[2]*10)==b]); samp+=rng.sample(pool,80)
rng.shuffle(samp)
key={};sets={1:[],2:[],3:[]}
for i,(a,b,j) in enumerate(samp):
    if rng.random()<0.5: a,b=b,a
    sh=sorted(render(x) for x in M[a]&M[b]); ea=sorted(render(x) for x in M[a]-M[b]); eb=sorted(render(x) for x in M[b]-M[a])
    pid=f'L{i:03d}'
    for s,(ex,tag) in {1:(ea,'A'),2:(eb,'B'),3:(ea,'A2')}.items():
        r=random.Random(f'{pid}{tag}'); s_=list(sh); e_=list(ex); r.shuffle(s_); r.shuffle(e_)
        sets[s].append(dict(item_id=f'{pid}{tag}',shared=s_,additional=e_))
    key[pid]=dict(a=a,b=b,J=j,core=len(M[a]&M[b]),na=len(ea),nb=len(eb))
for s in sets:
    rng.shuffle(sets[s])
    for b in range(0,240,48): json.dump(sets[s][b:b+48],open(P+f'inputs/R_set{s}_{b//48+1}.json','w'),indent=1)
json.dump(key,open(P+'inputs/KEY_DO_NOT_SHARE.json','w'))
import numpy as np
print('core size median',np.median([v['core'] for v in key.values()]),'extras median',np.median([v['na']+v['nb'] for v in key.values()]))
print(sorted(os.listdir(P+'inputs')))
