import sys,json,os,glob,random; sys.path.insert(0,'.')
exec(open(os.path.expanduser('~/np_build.py')).read().split("ok={k")[0])
P=ROOT+'data/experiments/core_reading_lowoverlap_2026-10-11/'
K=json.load(open(P+'inputs/KEY_DO_NOT_SHARE.json')); R={}
for f in glob.glob(P+'raw/R_set*.out.json'):
    for o in json.load(open(f)): R[o['item_id']]=o
rng=random.Random(616); items=[]
for pid in sorted(K):
    a,b=K[pid]['a'],K[pid]['b']
    for kind,(x,y) in [('AB',('A','B')),('AA',('A','A2'))]:
        sh=sorted(render(z) for z in M[a]&M[b]); rng.shuffle(sh)
        rd=[R[pid+x],R[pid+y]]; rng.shuffle(rd)
        items.append((pid,kind,dict(shared=sh,reading_1=dict(theme=rd[0]['theme'],core_role=rd[0]['core_role']),reading_2=dict(theme=rd[1]['theme'],core_role=rd[1]['core_role']))))
rng.shuffle(items); key={}; out=[]
for n,(pid,kind,it) in enumerate(items):
    iid=f'K{n:03d}'; out.append(dict(item_id=iid,**it)); key[iid]=dict(pid=pid,kind=kind)
os.makedirs(P+'compare',exist_ok=True)
for b in range(0,len(out),60): json.dump(out[b:b+60],open(P+f'compare/C_{b//60+1:02d}.json','w'),indent=1)
json.dump(key,open(P+'compare/KEY_DO_NOT_SHARE.json','w')); print(len(out),sorted(os.listdir(P+'compare')))
