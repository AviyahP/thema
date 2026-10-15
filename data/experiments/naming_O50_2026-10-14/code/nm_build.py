import sys,json,random,hashlib,csv,re,os; sys.path.insert(0,'.')
from tf_common_o50 import *
P=ROOT+'data/experiments/naming_O50_2026-10-14/'; os.makedirs(P+'inputs',exist_ok=True)
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
themes=sorted(ok); items={t:confusables(t) for t in themes}
json.dump({'themes':themes,'confusables':items},open(P+'inputs/themes_and_confusables.json','w'),indent=0)
def namer_item(t,ci):
    r=random.Random(seed(f'{t}:{ci}'))
    mem=[render(k) for k in sorted(M[t])]; r.shuffle(mem)
    cf=list(items[t]); r.shuffle(cf)
    cl=[]
    for j,c in enumerate(cf):
        cl.append(dict(confusable=f'C{j+1}',n_shared=len(M[t]&M[c]),only_in_theme=sorted(render(k) for k in M[t]-M[c]),only_in_confusable=sorted(render(k) for k in M[c]-M[t])))
    return dict(theme_id=t,size=len(M[t]),members=mem,confusables=cl)
order=list(themes); random.Random(7).shuffle(order)
n=0
for ci in (0,1,2):
    for b in range(0,len(order),25):
        json.dump([namer_item(t,ci) for t in order[b:b+25]],open(P+f'inputs/namer_slot{ci}_b{b//25+1:03d}.json','w'),indent=1); n+=1
big200=sorted(k for k,s in M.items() if len(s)>200)
print('O50 themes',len(M),'eligible 3-200',len(themes),'files',n,'| >200 (out of c1 scope):',len(big200),[len(M[k]) for k in big200],'| <4 confusables:',sum(1 for t in themes if len(items[t])<4))
