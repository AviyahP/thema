import sys,json,os,random; sys.path.insert(0,'.')
exec(open(os.path.expanduser('~/np_build.py')).read().split("ok={k")[0])
P=ROOT+'data/experiments/whole_reading_2026-10-11/'
KH=json.load(open(ROOT+'data/experiments/core_reading_pilot_2026-10-11/inputs/KEY_DO_NOT_SHARE.json'))
KL=json.load(open(ROOT+'data/experiments/core_reading_lowoverlap_2026-10-11/inputs/KEY_DO_NOT_SHARE.json'))
rng=random.Random(20261016)
pairs={}
for pid,v in KH.items(): pairs['H'+pid]=dict(set='HIGH',x=v['side1'],y=v['side2'],J=v['J'],label=v['label'])
for b in (1,2,3):
    ps=sorted(p for p,v in KL.items() if int(v['J']*10)==b)
    for pid in rng.sample(ps,20): pairs['W'+pid]=dict(set='LOW',x=KL[pid]['a'],y=KL[pid]['b'],J=KL[pid]['J'],label='')
syn=rng.sample(sorted(p for p in pairs if pairs[p]['set']=='HIGH'),60)
SYNM={}
for p in syn:
    A=sorted(M[pairs[p]['x']]); k=max(3,round(0.7*len(A))); sub=random.Random('syn'+p).sample(A,k)
    SYNM['S'+p]=sub; pairs['S'+p]=dict(set='SYN',x=pairs[p]['x'],y='A*',J=k/len(A),label='',src=p)
items={1:[],2:[],3:[]}; key={}
def add(s,members,tag):
    iid=f'T{len(key):04d}'; mem=[render(z) for z in members]; random.Random(iid).shuffle(mem)
    items[s].append(dict(item_id=iid,members=mem)); key[iid]=tag
for p,v in pairs.items():
    if v['set'] in ('HIGH','LOW'):
        add(1,sorted(M[v['x']]),dict(pair=p,side='x')); add(2,sorted(M[v['y']]),dict(pair=p,side='y'))
    else:
        add(3,SYNM[p],dict(pair=p,side='y'))
for s in items:
    rng.shuffle(items[s]); bs=50 if s<3 else 30
    for b in range(0,len(items[s]),bs): json.dump(items[s][b:b+bs],open(P+f'inputs/W_set{s}_{b//bs+1:02d}.json','w'),indent=1)
json.dump(dict(pairs=pairs,items=key,syn_members=SYNM),open(P+'inputs/KEY_DO_NOT_SHARE.json','w'))
print({s:len(v) for s,v in items.items()},sorted(os.listdir(P+'inputs')))
