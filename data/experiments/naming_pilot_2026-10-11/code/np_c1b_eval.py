import sys,json,os,glob,re,collections; sys.path.insert(0,'.')
exec(open(os.path.expanduser('~/np_build.py')).read().split("ok={k")[0])
P=ROOT+'data/experiments/naming_pilot_2026-10-11/'
SC=json.load(open(P+'inputs/confusables_after_dedup.json')); rep=json.load(open(P+'inputs/repro_subset.json'))
STOP={'a','an','the','of','and','in','to','by','for','via','with','on','from','at'}
def toks(s): return {w for w in re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*",s.lower()) if w not in STOP}
def jac(a,b): return len(a&b)/len(a|b) if a|b else 1.0
def norm(s): return ' '.join(re.sub(r'[^a-z0-9 ]',' ',s.lower()).split())
cands=collections.defaultdict(dict); corr={}
for run,pre,keyf,selp in [('M','raw/namer','selection/KEY_DO_NOT_SHARE_main.json','selection/main_sel_*.out.json'),('R','raw/rerun','selection/KEY_DO_NOT_SHARE_rerun.json','selection/rerun_sel_*.out.json')]:
    for f in glob.glob(P+pre+'_slot*_b*.out.json'):
        s=int(f.split('_slot')[1][0])
        for o in json.load(open(f)):
            if o['theme_id'] in rep: cands[(run,o['theme_id'])][s]=o
    key=json.load(open(P+keyf)); ch={}
    for f in glob.glob(P+selp):
        for o in json.load(open(f)): ch[o['item_id']]=o['choice']
    for i,v in key.items(): corr[(run,v['theme'],v['cand'])]=ch[i]==v['correct']
key=json.load(open(P+'c1b/selection/KEY_DO_NOT_SHARE.json')); ch={}
for f in glob.glob(P+'c1b/selection/sel_*.out.json'):
    for o in json.load(open(f)): ch[o['item_id']]=o['choice']
for f in glob.glob(P+'c1b/raw/c1b*_seed*_b*.out.json'):
    run=f.split('/c1b')[-1][0]; s=int(f.split('_seed')[1].split('_')[0]); slot=s%10
    for o in json.load(open(f)): cands[(run,o['theme_id'])][slot]=o
for i,v in key.items(): corr[(v['run'],v['theme'],v['seed']%10)]=ch[i]==v['correct']
def final(run,t,slots):
    cs=cands[(run,t)]; nm=[s for s in slots if cs[s].get('nameable',True)]
    pool=[s for s in nm if corr.get((run,t,s))]; low=not pool; pool=pool or nm
    T={s:toks(cs[s]['name']) for s in nm}
    b=min(pool,key=lambda s:(-sum(jac(T[s],T[o]) for o in nm if o!=s),s))
    return dict(name=cs[b]['name'],low_confidence=low,n_correct=sum(bool(corr.get((run,t,s))) for s in nm))
FIN={}
for run in 'MR':
    for k,sl in [('c1b',range(5)),('c1',range(3))]:
        FIN[f'{k}_{run}']={t:final(run,t,sl) for t in rep}
F1=json.load(open(P+'selection/final_names.json'))
mism=sum(FIN['c1_M'][t]['name']!=F1['main'][t]['name'] for t in rep)+sum(FIN['c1_R'][t]['name']!=F1['rerun'][t]['name'] for t in rep)
print('c1 recomputed finals differing from recorded (expect 0, except dedup themes):',mism)
for k in FIN: d=collections.Counter(norm(v['name']) for v in FIN[k].values()); print(k,'dups',{a:c for a,c in d.items() if c>1},'low_conf',sum(v['low_confidence'] for v in FIN[k].values()))
print('per-candidate correct, new slots 3-4: %.1f%%'%(100*sum(v for (r,t,s),v in corr.items() if s>=3)/sum(1 for (r,t,s) in corr if s>=3)))
print('c1b final == c1 final: M %d/60, R %d/60'%(sum(FIN['c1b_M'][t]['name']==FIN['c1_M'][t]['name'] for t in rep),sum(FIN['c1b_R'][t]['name']==FIN['c1_R'][t]['name'] for t in rep)))
json.dump(FIN,open(P+'c1b/final_names_c1b.json','w'),indent=1)
os.makedirs(P+'c1b/eval',exist_ok=True)
e1=[];k1={};e2=[];k2={}
for t in rep:
    for setn in ['c1b_M','c1b_R','c1_M','c1_R']:
        name=FIN[setn][t]['name']; cl=[t]+SC[t]; r=random.Random(seed(f'{t}:E1b{setn}')); r.shuffle(cl)
        common=set.intersection(*(M[c] for c in cl)); L='ABCDE'[:len(cl)]
        iid=f'X{len(e1):04d}'; e1.append(dict(item_id=iid,name=name,in_all=sorted(render(k) for k in common),also_in={l:sorted(render(k) for k in M[c]-common) for l,c in zip(L,cl)})); k1[iid]=dict(theme=t,set=setn,correct=L[cl.index(t)])
        mem=[render(k) for k in sorted(M[t])]; r.shuffle(mem)
        jid=f'Y{len(e2):04d}'; e2.append(dict(item_id=jid,name=name,members=mem)); k2[jid]=dict(theme=t,set=setn,size=len(M[t]))
e3=[];k3={}
for t in rep:
    for ver in ['c1b','c1']:
        a,b=FIN[f'{ver}_M'][t]['name'],FIN[f'{ver}_R'][t]['name']
        r=random.Random(seed(f'{t}:E3b{ver}')); pair=[a,b]; r.shuffle(pair); mem=[render(k) for k in sorted(M[t])]; r.shuffle(mem)
        iid=f'Z{len(e3):03d}'; e3.append(dict(item_id=iid,members=mem,name_1=pair[0],name_2=pair[1])); k3[iid]=dict(theme=t,version=ver)
for L_,s in [(e1,1),(e2,2),(e3,3)]: random.Random(60+s).shuffle(L_)
for b in range(0,240,40): json.dump(e1[b:b+40],open(P+f'c1b/eval/E1_{b//40+1:02d}.json','w'),indent=1)
for b in range(0,240,60): json.dump(e2[b:b+60],open(P+f'c1b/eval/E2_{b//60+1:02d}.json','w'),indent=1)
for b in range(0,120,60): json.dump(e3[b:b+60],open(P+f'c1b/eval/E3_{b//60+1:02d}.json','w'),indent=1)
json.dump(dict(E1=k1,E2=k2,E3=k3),open(P+'c1b/eval/KEY_DO_NOT_SHARE_eval.json','w'))
print(sorted(os.listdir(P+'c1b/eval')))
