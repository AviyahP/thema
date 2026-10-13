import sys,json,random,hashlib,glob,os; sys.path.insert(0,'.')
exec(open(os.path.expanduser('~/np_build.py')).read().split("ok={k")[0])
P=ROOT+'data/experiments/naming_pilot_2026-10-11/'
SC=json.load(open(P+'inputs/sample_and_confusables.json'))['confusables']
def bm_item(t,name,seedtag,iid):
    cl=[t]+SC[t]; r=random.Random(seed(f'{t}:{seedtag}')); r.shuffle(cl)
    common=set.intersection(*(M[c] for c in cl))
    letters='ABCDE'[:len(cl)]
    item=dict(item_id=iid,name=name,in_all=sorted(render(k) for k in common),
              also_in={L:sorted(render(k) for k in M[c]-common) for L,c in zip(letters,cl)})
    return item, letters[cl.index(t)]
def load(prefix):
    C={}
    for f in glob.glob(P+f'raw/{prefix}_slot*_b*.out.json'):
        s=int(f.split('_slot')[1][0])
        for o in json.load(open(f)): C[(o['theme_id'],s)]=o
    return C
os.makedirs(P+'selection',exist_ok=True)
for run,prefix,off,bs in [('main','namer',0,50),('rerun','rerun',10,45)]:
    C=load(prefix); items=[];key={}
    rr=random.Random(99+off); order=sorted(C); rr.shuffle(order)
    for i,(t,s) in enumerate(order):
        o=C[(t,s)]
        if not o.get('nameable',True): continue
        iid=f'{run[0].upper()}{i:04d}'
        it,correct=bm_item(t,o['name'],f'S{s+off}',iid); items.append(it); key[iid]=dict(theme=t,cand=s,correct=correct)
    json.dump(key,open(P+f'selection/KEY_DO_NOT_SHARE_{run}.json','w'))
    for b in range(0,len(items),bs):
        json.dump(items[b:b+bs],open(P+f'selection/{run}_sel_{b//bs+1:02d}.json','w'),indent=1)
    print(run,len(items),'items',(len(items)+bs-1)//bs,'files')
