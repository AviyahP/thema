import sys,json,os; sys.path.insert(0,'.')
exec(open(os.path.expanduser('~/np_build.py')).read().split("ok={k")[0])
P=ROOT+'data/experiments/core_reading_pilot_2026-10-11/'; os.makedirs(P+'inputs',exist_ok=True)
V2=json.load(open('/tmp/v2_labels.json')); J={p['id']:p['J'] for p in PAIRS}
lab={k:v for k,v in V2.items() if v in ('twin','facet')}
band=lambda j:0 if j<0.5 else (1 if j<0.6 else 2)
rng=random.Random(20261014)
byb={b:[k for k in lab if band(J[k])==b] for b in range(3)}
tot=sum(len(v) for v in byb.values()); quota={b:round(150*len(byb[b])/tot) for b in range(3)}
quota[2]=150-quota[0]-quota[1]
samp=[]
for b in range(3):
    for l in ('twin','facet'):
        pool=sorted(k for k in byb[b] if lab[k]==l); samp+=rng.sample(pool,quota[b])
print('quota',quota,'n',len(samp))
rng.shuffle(samp)
key={};s1=[];s2=[]
for i,k in enumerate(samp):
    a,b=k.split('|')
    if rng.random()<0.5: a,b=b,a
    sh=[render(x) for x in sorted(M[a]&M[b])]; rng.shuffle(sh)
    ea=[render(x) for x in sorted(M[a]-M[b])]; rng.shuffle(ea)
    eb=[render(x) for x in sorted(M[b]-M[a])]; rng.shuffle(eb)
    pid=f'P{i:03d}'
    s1.append(dict(item_id=f'{pid}x',shared=sh,additional=ea)); s2.append(dict(item_id=f'{pid}y',shared=list(reversed(sh)),additional=eb))
    key[pid]=dict(pair=k,side1=a,side2=b,label=lab[k],J=J[k])
rng.shuffle(s1); rng.shuffle(s2)
for b in range(0,300,50):
    json.dump(s1[b:b+50],open(P+f'inputs/R1_s1_{b//50+1:02d}.json','w'),indent=1); json.dump(s2[b:b+50],open(P+f'inputs/R1_s2_{b//50+1:02d}.json','w'),indent=1)
json.dump(key,open(P+'inputs/KEY_DO_NOT_SHARE.json','w'))
import collections; print(collections.Counter((band(v['J']),v['label']) for v in key.values()))
