import sys,json,os,random,glob; sys.path.insert(0,'.')
exec(open(os.path.expanduser('~/np_build.py')).read().split("ok={k")[0])
P=ROOT+'data/experiments/whole_reading_2026-10-11/'
K=json.load(open(P+'inputs/KEY_DO_NOT_SHARE.json'))
R={}
for f in glob.glob(P+'raw/W_set*.out.json'):
    for r in json.load(open(f)): R[r['item_id']]=r['story']
side={}
for iid,t in K['items'].items(): side[(t['pair'],t['side'])]=iid
rng=random.Random(20261017)
items=[]; key={}
for p,v in K['pairs'].items():
    if v['set']=='SYN':
        A=set(M[v['x']]); B=set(K['syn_members'][p]); sa=R[side[(v['src'],'x')]]; sb=R[side[(p,'y')]]
    else:
        A=set(M[v['x']]); B=set(M[v['y']]); sa=R[side[(p,'x')]]; sb=R[side[(p,'y')]]
    S=A&B
    def lst(Z,seed):
        z=sorted(Z); random.Random(seed).shuffle(z); return [render(m)+(' [shared]' if m in S else '') for m in z]
    sides=[(A,sa),(B,sb)]; sw=rng.random()<0.5
    if sw: sides=sides[::-1]
    items.append(dict(pair=p,swap=sw,X=dict(members=lst(sides[0][0],p+'X'),story=sides[0][1]),Y=dict(members=lst(sides[1][0],p+'Y'),story=sides[1][1])))
rng.shuffle(items)
out=[]
for i,it in enumerate(items):
    cid=f'C{i:04d}'; key[cid]=dict(pair=it['pair'],swap=it['swap'])
    out.append(dict(item_id=cid,X=it['X'],Y=it['Y']))
os.makedirs(P+'compare',exist_ok=True)
for b in range(0,len(out),60): json.dump(out[b:b+60],open(P+f'compare/W2_{b//60+1:02d}.json','w'),indent=1)
json.dump(key,open(P+'compare/KEY_DO_NOT_SHARE.json','w'))
print(len(out),len(R),sorted(os.listdir(P+'compare')))
