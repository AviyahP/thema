import sys,json,os,random,collections,csv; sys.path.insert(0,'.')
exec(open(os.path.expanduser('~/np_build.py')).read().split("ok={k")[0])
P=ROOT+'data/experiments/hidef_eval_2026-10-13/'
HD=ROOT+'data/ontology/v0.4-leaves/hidef_L_k4_maxres800/'
MH=collections.defaultdict(set)
for r in csv.DictReader(open(HD+'members.tsv'),delimiter='\t'):
    MH[r['node']].add(r['key'])
    if r['key'] not in TITLE and r.get('name'): TITLE[r['key']]=r['name']
TH={k:s for k,s in MH.items() if 3<=len(s)<=100}
TT={k:s for k,s in M.items() if k not in big and 3<=len(s)<=100}
bands=[(3,6,51),(7,15,32),(16,40,12),(41,100,5)]
rng=random.Random(20261013); items=[]; key={}
for arm,T in (('HiDeF',TH),('THEMA',TT)):
    for a,b,n in bands:
        pool=sorted(k for k,s in T.items() if a<=len(s)<=b)
        for k in rng.sample(pool,n): items.append((arm,k,T[k]))
rng.shuffle(items); out=[]
for i,(arm,k,s) in enumerate(items):
    iid=f'Q{i:03d}'; mem=[render(m) for m in sorted(s)]; random.Random(iid).shuffle(mem)
    out.append(dict(id=iid,size=len(s),members=mem)); key[iid]=dict(arm=arm,theme=k,size=len(s))
for b in range(5): json.dump(out[b*40:(b+1)*40],open(P+f'inputs/Q_{b+1:02d}.json','w'),indent=1)
json.dump(key,open(P+'inputs/KEY_DO_NOT_SHARE.json','w'),indent=1)
miss=sum(1 for _,_,s in items for m in s if m not in TITLE)
print(len(out),'items; missing titles',miss,'; share above 100: HiDeF',sum(len(s)>100 for s in MH.values() if len(s)<1000)/sum(1 for s in MH.values() if 3<=len(s)<1000),'THEMA',sum(len(s)>100 for k,s in M.items() if k not in big)/sum(1 for k,s in M.items() if k not in big and len(s)>=3))
