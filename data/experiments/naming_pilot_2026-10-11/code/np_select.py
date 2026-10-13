import sys,json,glob,re,collections,os; sys.path.insert(0,'.')
from tf_common import EV,ROOT
P=ROOT+'data/experiments/naming_pilot_2026-10-11/'
STOP={'a','an','the','of','and','in','to','by','for','via','with','on','from','at'}
def toks(s): return {w for w in re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*",s.lower()) if w not in STOP}
def jac(a,b): return len(a&b)/len(a|b) if a|b else 1.0
def norm(s): return ' '.join(re.sub(r'[^a-z0-9 ]',' ',s.lower()).split())
def select(prefix,run):
    C=collections.defaultdict(dict)
    for f in glob.glob(P+f'raw/{prefix}_slot*_b*.out.json'):
        s=int(f.split('_slot')[1][0])
        for o in json.load(open(f)): C[o['theme_id']][s]=o
    key=json.load(open(P+f'selection/KEY_DO_NOT_SHARE_{run}.json'))
    ch={}
    for f in glob.glob(P+f'selection/{run}_sel_*.out.json'):
        for o in json.load(open(f)): ch[o['item_id']]=o['choice']
    corr={(v['theme'],v['cand']):ch[i]==v['correct'] for i,v in key.items()}
    out={}
    for t,cs in C.items():
        nameable=[s for s in sorted(cs) if cs[s].get('nameable',True)]
        if len(cs)-len(nameable)>=2: out[t]=dict(unnameable=True,rationale=cs[0].get('rationale','')); continue
        pool=[s for s in nameable if corr.get((t,s))]; low=not pool
        if low: pool=nameable
        T={s:toks(cs[s]['name']) for s in nameable}
        best=min(pool,key=lambda s:(-sum(jac(T[s],T[o]) for o in nameable if o!=s),s))
        out[t]=dict(unnameable=False,name=cs[best]['name'],cand=best,n_correct=sum(bool(corr.get((t,s))) for s in nameable),n_nameable=len(nameable),low_confidence=low,
                    candidates=[cs[s]['name'] for s in sorted(cs)],correct_flags=[bool(corr.get((t,s))) for s in sorted(cs)])
    return out
main=select('namer','main'); rerun=select('rerun','rerun')
dup=collections.Counter(norm(v['name']) for v in main.values() if not v['unnameable'])
dups={k:c for k,c in dup.items() if c>1}
json.dump(dict(main=main,rerun=rerun,duplicates=dups),open(P+'selection/final_names.json','w'),indent=1)
print('main themes',len(main),'unnameable',sum(v['unnameable'] for v in main.values()),'low_conf',sum(v.get('low_confidence',False) for v in main.values()))
print('candidate correct rate %.1f%%'%(100*sum(sum(v['correct_flags']) for v in main.values())/sum(len(v['correct_flags']) for v in main.values())))
print('n_correct dist',collections.Counter(v['n_correct'] for v in main.values()))
print('duplicates among finals',dups)
print('rerun themes',len(rerun),'low_conf',sum(v.get('low_confidence',False) for v in rerun.values()))
