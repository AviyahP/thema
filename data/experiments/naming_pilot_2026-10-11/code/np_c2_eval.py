import sys,json,os,glob,re,collections; sys.path.insert(0,'.')
exec(open(os.path.expanduser('~/np_build.py')).read().split("ok={k")[0])
P=ROOT+'data/experiments/naming_pilot_2026-10-11/'
SC=json.load(open(P+'inputs/confusables_after_dedup.json')); rep=json.load(open(P+'inputs/repro_subset.json'))
STOP={'a','an','the','of','and','in','to','by','for','via','with','on','from','at'}
def toks(s): return {w for w in re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*",s.lower()) if w not in STOP}
def jac(a,b): return len(a&b)/len(a|b) if a|b else 1.0
def norm(s): return ' '.join(re.sub(r'[^a-z0-9 ]',' ',s.lower()).split())
FIN={}
for run in 'AB':
    C=collections.defaultdict(dict)
    for f in glob.glob(P+f'c2/raw/c2{run}_slot*_b*.out.json'):
        s=int(f.split('_slot')[1][0])
        for o in json.load(open(f)): C[o['theme_id']][s]=o
    key=json.load(open(P+f'c2/selection/KEY_DO_NOT_SHARE_{run}.json')); ch={}
    for f in glob.glob(P+f'c2/selection/{run}_sel_*.out.json'):
        for o in json.load(open(f)): ch[o['item_id']]=o['choice']
    corr={(v['theme'],v['cand']):ch[i]==v['correct'] for i,v in key.items()}
    out={}
    for t,cs in C.items():
        nm=[s for s in sorted(cs) if cs[s].get('nameable',True)]
        if len(cs)-len(nm)>=3: out[t]=dict(unnameable=True); continue
        pool=[s for s in nm if corr.get((t,s))]; low=not pool; pool=pool or nm
        T={s:toks(cs[s]['name']) for s in nm}
        best=min(pool,key=lambda s:(-sum(jac(T[s],T[o]) for o in nm if o!=s),s))
        out[t]=dict(unnameable=False,name=cs[best]['name'],n_correct=sum(bool(corr.get((t,s))) for s in nm),low_confidence=low,candidates=[cs[s]['name'] for s in sorted(cs)])
    FIN[run]=out
    d=collections.Counter(norm(v['name']) for v in out.values()); print(run,'themes',len(out),'low_conf',sum(v['low_confidence'] for v in out.values()),'dups',{k:c for k,c in d.items() if c>1},'cand correct %.1f%%'%(100*sum(corr.values())/len(corr)))
json.dump(FIN,open(P+'c2/final_names_c2.json','w'),indent=1)
F1=json.load(open(P+'selection/final_names.json'))
os.makedirs(P+'c2/eval',exist_ok=True)
e1=[];k1={};e2=[];k2={}
for t in rep:
    for run in 'AB':
        name=FIN[run][t]['name']; cl=[t]+SC[t]; r=random.Random(seed(f'{t}:E2c{run}')); r.shuffle(cl)
        common=set.intersection(*(M[c] for c in cl)); L='ABCDE'[:len(cl)]
        iid=f'X{len(e1):04d}'; e1.append(dict(item_id=iid,name=name,in_all=sorted(render(k) for k in common),also_in={l:sorted(render(k) for k in M[c]-common) for l,c in zip(L,cl)})); k1[iid]=dict(theme=t,run=run,correct=L[cl.index(t)])
        mem=[render(k) for k in sorted(M[t])]; r.shuffle(mem)
        jid=f'Y{len(e2):04d}'; e2.append(dict(item_id=jid,name=name,members=mem)); k2[jid]=dict(theme=t,run=run,size=len(M[t]))
e3=[];k3={}
for t in rep:
    for ver,(a,b) in [('c2',(FIN['A'][t]['name'],FIN['B'][t]['name'])),('c1',(F1['main'][t]['name'],F1['rerun'][t]['name']))]:
        r=random.Random(seed(f'{t}:E3{ver}')); pair=[a,b]; r.shuffle(pair)
        mem=[render(k) for k in sorted(M[t])]; r.shuffle(mem)
        iid=f'Z{len(e3):03d}'; e3.append(dict(item_id=iid,members=mem,name_1=pair[0],name_2=pair[1])); k3[iid]=dict(theme=t,version=ver)
for L_,s in [(e1,1),(e2,2),(e3,3)]: random.Random(40+s).shuffle(L_)
for b in range(0,120,40): json.dump(e1[b:b+40],open(P+f'c2/eval/E1_{b//40+1:02d}.json','w'),indent=1)
for b in range(0,120,60):
    json.dump(e2[b:b+60],open(P+f'c2/eval/E2_{b//60+1:02d}.json','w'),indent=1); json.dump(e3[b:b+60],open(P+f'c2/eval/E3_{b//60+1:02d}.json','w'),indent=1)
json.dump(dict(E1=k1,E2=k2,E3=k3),open(P+'c2/eval/KEY_DO_NOT_SHARE_eval.json','w'))
print(sorted(os.listdir(P+'c2/eval')))
