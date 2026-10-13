import csv,collections,json,os,numpy as np
csv.field_size_limit(10**9)
ROOT=os.path.expanduser('~/mnt/thema/')
D=ROOT+'data/ontology/v0.4-leaves/thema_L_x2_c85/'
EV=ROOT+'data/experiments/reviewer_eval_x2_2026-10-09/'
N={r['node']:r for r in csv.DictReader(open(D+'nodes.tsv'),delimiter='\t')}
M=collections.defaultdict(set); INC={}
for r in csv.DictReader(open(D+'members.tsv'),delimiter='\t'):
    M[r['node']].add(r['key']); INC[(r['node'],r['key'])]=float(r['inclusion'] or 'nan')
big={k for k,s in M.items() if len(s)>=1000}
par={k:set(N[k]['parents'].split())-big for k in N}
chl={k:set(N[k]['children'].split()) for k in N}
sup={k:float(N[k]['support']) for k in N}
_am={}
def anc(k):
    if k in _am: return _am[k]
    s=set()
    for p in par[k]: s|={p}|anc(p)
    _am[k]=s; return s
_dm={}
def depth(k):
    if k in _dm: return _dm[k]
    d=0 if not par[k] else 1+max(depth(p) for p in par[k]); _dm[k]=d; return d
def J(x,y): return len(x&y)/len(x|y) if x|y else 1.0
PAIRS=json.load(open(EV+'sibling_pairs_all.json'))
LAB={r['id']:r['verdict'] for r in json.load(open(EV+'judged_sibling_pairs_all.json'))}
