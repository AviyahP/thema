import sys,json,random,hashlib,csv,re,os; sys.path.insert(0,'.')
from tf_common import *
P=ROOT+'data/experiments/naming_pilot_2026-10-11/'; os.makedirs(P+'inputs',exist_ok=True)
X=ROOT+'data/ontology/v0.4-leaves-x2/'
V=np.load(X+'vectors_leaves_centred.npy').astype(np.float32); V/=np.linalg.norm(V,axis=1,keepdims=True)+1e-9
K=open(X+'embedding_keys.txt').read().split(); ix={k:i for i,k in enumerate(K)}
TITLE={}
for r in csv.DictReader(open(D+'members.tsv'),delimiter='\t'): TITLE[r['key']]=r['name']
DESC={}
for r in csv.DictReader(open(ROOT+'data/pathway_descriptions.tsv'),delimiter='\t'):
    if r['key'].startswith('btm:') and r.get('status','') in ('current','ok','',None) or r['key'] not in DESC: DESC[r['key']]=r['description_generated']
def first2(t):
    s=re.split(r'(?<=[.!?])\s+',t.strip()); return ' '.join(s[:2])
def render(k):
    t=TITLE[k]
    if t.strip()=='TBA': return '[untitled BTM module] '+first2(DESC.get(k,''))
    return t
def seed(s): return int(hashlib.sha256(s.encode()).hexdigest()[:8],16)
ok={k for k,s in M.items() if 3<=len(s)<=200}
cen={}
for k in ok:
    e=V[[ix[x] for x in M[k] if x in ix]].mean(0); cen[k]=e/(np.linalg.norm(e)+1e-9)
kids=collections.defaultdict(set)
for k in N:
    for p in par[k]: kids[p].add(k)
def nested(a,b): return M[a]<=M[b] or M[b]<=M[a]
def sibs(t): return {s for p in par[t] for s in kids[p] if s!=t and s in ok and not nested(s,t)}
elig=[k for k in sorted(ok) if len(sibs(k))>=1]
G=set()
for p in PAIRS: G|=set(p['id'].split('|'))
rng=random.Random(20261011)
fam=[k for k in elig if k in G]; rest=[k for k in elig if k not in G]
samp=rng.sample(fam,150)+rng.sample(rest,50)
print('eligible',len(elig),'in graph',len(fam),'rest',len(rest))
allok=sorted(ok); C=np.stack([cen[k] for k in allok])
def confusables(t):
    s=sorted(sibs(t),key=lambda c:-float(cen[c]@cen[t]))[:4]
    if len(s)<4:
        sims=C@cen[t]; n=len(M[t])
        for j in np.argsort(-sims):
            c=allok[j]
            if c==t or c in s or nested(c,t) or not (n/3<=len(M[c])<=3*n): continue
            s.append(c)
            if len(s)==4: break
    return s
items={}
for t in samp:
    cf=confusables(t); items[t]=cf
json.dump({'sample':samp,'confusables':items},open(P+'inputs/sample_and_confusables.json','w'),indent=0)
def namer_item(t,ci):
    r=random.Random(seed(f'{t}:{ci}'))
    mem=[render(k) for k in sorted(M[t])]; r.shuffle(mem)
    cf=list(items[t]); r.shuffle(cf)
    cl=[]
    for j,c in enumerate(cf):
        cl.append(dict(confusable=f'C{j+1}',n_shared=len(M[t]&M[c]),only_in_theme=sorted(render(k) for k in M[t]-M[c]),only_in_confusable=sorted(render(k) for k in M[c]-M[t])))
    return dict(theme_id=t,size=len(M[t]),members=mem,confusables=cl)
def write_batches(tag,themes,slots,bs,off=0):
    for ci in slots:
        for b in range(0,len(themes),bs):
            out=[namer_item(t,ci+off) for t in themes[b:b+bs]]
            json.dump(out,open(P+f'inputs/{tag}_slot{ci}_b{b//bs+1:02d}.json','w'),indent=1)
order=list(samp); random.Random(7).shuffle(order)
write_batches('namer',order,[0,1,2],25)
rep=random.Random(20261013).sample(samp,60)
json.dump(rep,open(P+'inputs/repro_subset.json','w'))
write_batches('rerun',rep,[0,1,2],30,off=10)
print(sorted(os.listdir(P+'inputs'))[:5],len(os.listdir(P+'inputs')))
sz=[len(M[t]) for t in samp]; print('sample size median',np.median(sz),'max',max(sz),'n with <4 sibling confusables',sum(1 for t in samp if len(sibs(t))<4))
