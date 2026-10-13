import sys,json,os,re,glob,collections; sys.path.insert(0,'.')
exec(open(os.path.expanduser('~/np_build.py')).read().split("ok={k")[0])
P=ROOT+'data/experiments/naming_pilot_2026-10-11/'
F=json.load(open(P+'selection/final_names.json')); SC=json.load(open(P+'inputs/confusables_after_dedup.json'))
STOP={'a','an','the','of','and','in','to','by','for','via','with','on','from','at'}
def toks(s): return {w for w in re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*",s.lower()) if w not in STOP}
def jac(a,b): return len(a&b)/len(a|b) if a|b else 1.0
def norm(s): return ' '.join(re.sub(r'[^a-z0-9 ]',' ',s.lower()).split())
key=json.load(open(P+'selection/KEY_DO_NOT_SHARE_dedup.json')); ch={o['item_id']:o['choice'] for o in json.load(open(P+'selection/dedup_sel_01.out.json'))}
D=collections.defaultdict(dict)
for s in [0,1,2]:
    for o in json.load(open(P+f'raw/dedup_slot{s}.out.json')): D[o['theme_id']][s]=o
for t,cs in D.items():
    corr={v['cand']:ch[i]==v['correct'] for i,v in key.items() if v['theme']==t}
    pool=[s for s in cs if corr[s]] or list(cs); T={s:toks(cs[s]['name']) for s in cs}
    best=min(pool,key=lambda s:(-sum(jac(T[s],T[o]) for o in cs if o!=s),s))
    F['main'][t].update(name=cs[best]['name'],cand=best,n_correct=sum(corr.values()),low_confidence=not any(corr.values()),dedup_round=1,candidates=[cs[s]['name'] for s in sorted(cs)],correct_flags=[corr[s] for s in sorted(cs)])
dup=collections.Counter(norm(v['name']) for v in F['main'].values()); F['duplicates_after_dedup']={k:c for k,c in dup.items() if c>1}
json.dump(F,open(P+'selection/final_names.json','w'),indent=1)
print('dedup themes',{t:F['main'][t]['name'] for t in D},'remaining dups',F['duplicates_after_dedup'])
CEN={}
for l in open(EV+'names_test/theme_names_c85.tsv').read().splitlines()[1:]:
    n,nm=l.split('\t',1); CEN[n]=nm
samp=json.load(open(P+'inputs/sample_and_confusables.json'))['sample']
os.makedirs(P+'eval',exist_ok=True)
e1=[];k1={};e2=[];k2={}
for t in samp:
    for arm,name in [('NEW',F['main'][t]['name']),('CENSUS',CEN[t])]:
        cl=[t]+SC[t]; r=random.Random(seed(f'{t}:E{arm}')); r.shuffle(cl)
        common=set.intersection(*(M[c] for c in cl)); L='ABCDE'[:len(cl)]
        iid=f'X{len(e1):04d}'; e1.append(dict(item_id=iid,name=name,in_all=sorted(render(k) for k in common),also_in={l:sorted(render(k) for k in M[c]-common) for l,c in zip(L,cl)}))
        k1[iid]=dict(theme=t,arm=arm,correct=L[cl.index(t)])
        mem=[render(k) for k in sorted(M[t])]; r.shuffle(mem)
        jid=f'Y{len(e2):04d}'; e2.append(dict(item_id=jid,name=name,members=mem)); k2[jid]=dict(theme=t,arm=arm,size=len(M[t]))
random.Random(11).shuffle(e1); random.Random(12).shuffle(e2)
for b in range(0,400,50):
    json.dump(e1[b:b+50],open(P+f'eval/E1_{b//50+1:02d}.json','w'),indent=1); json.dump(e2[b:b+50],open(P+f'eval/E2_{b//50+1:02d}.json','w'),indent=1)
rep=json.load(open(P+'inputs/repro_subset.json')); e3=[];k3={}
for i,t in enumerate(rep):
    a,b=F['main'][t]['name'],F['rerun'][t]['name']; r=random.Random(seed(f'{t}:E3'))
    pair=[('main',a),('rerun',b)]; r.shuffle(pair)
    mem=[render(k) for k in sorted(M[t])]; r.shuffle(mem)
    iid=f'Z{i:03d}'; e3.append(dict(item_id=iid,members=mem,name_1=pair[0][1],name_2=pair[1][1])); k3[iid]=dict(theme=t)
for b in range(0,60,30): json.dump(e3[b:b+30],open(P+f'eval/E3_{b//30+1:02d}.json','w'),indent=1)
json.dump(dict(E1=k1,E2=k2,E3=k3),open(P+'eval/KEY_DO_NOT_SHARE_eval.json','w'))
print('E1',len(e1),'E2',len(e2),'E3',len(e3)); print(sorted(os.listdir(P+'eval')))
