import sys,json,os,glob,random; sys.path.insert(0,'.')
exec(open(os.path.expanduser('~/np_build.py')).read().split("ok={k")[0])
P=ROOT+'data/experiments/core_reading_pilot_2026-10-11/'
K=json.load(open(P+'inputs/KEY_DO_NOT_SHARE.json')); R={}
for f in glob.glob(P+'raw/R1_*.out.json'):
    for o in json.load(open(f)): R[o['item_id']]=o
rng=random.Random(515); items=[];key={}
pids=sorted(K); rng.shuffle(pids)
for n,pid in enumerate(pids):
    a,b=K[pid]['side1'],K[pid]['side2']
    sh=[render(x) for x in sorted(M[a]&M[b])]; rng.shuffle(sh)
    rd=[R[pid+'x'],R[pid+'y']]; rng.shuffle(rd)
    iid=f'C{n:03d}'
    items.append(dict(item_id=iid,shared=sh,reading_1=dict(theme=rd[0]['theme'],core_role=rd[0]['core_role']),reading_2=dict(theme=rd[1]['theme'],core_role=rd[1]['core_role'])))
    key[iid]=pid
os.makedirs(P+'compare',exist_ok=True)
for b in range(0,300,60): json.dump(items[b:b+60],open(P+f'compare/C1_{b//60+1:02d}.json','w'),indent=1)
json.dump(key,open(P+'compare/KEY_DO_NOT_SHARE.json','w')); print(len(items))
