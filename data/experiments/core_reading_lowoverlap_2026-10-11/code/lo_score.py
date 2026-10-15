import sys,json,glob,collections,numpy as np,random; sys.path.insert(0,'.')
from tf_common import ROOT
P=ROOT+'data/experiments/core_reading_lowoverlap_2026-10-11/'
K=json.load(open(P+'inputs/KEY_DO_NOT_SHARE.json')); CK=json.load(open(P+'compare/KEY_DO_NOT_SHARE.json'))
V={}
for f in glob.glob(P+'compare/C_*.out.json'):
    for o in json.load(open(f)): k=CK[o['item_id']]; V[(k['pid'],k['kind'])]=o['verdict']
pids=sorted(K); band=lambda p:int(K[p]['J']*10)
rng=np.random.default_rng(0)
print('band   kind  same partly different | partly-or-diff')
for b in (1,2,3):
    for kind in ('AB','AA'):
        c=collections.Counter(V[(p,kind)] for p in pids if band(p)==b); n=sum(c.values())
        print(f"0.{b}-0.{b+1} {kind}  {c['same']:4d} {c['partly']:5d} {c['different']:5d}     | {100*(c['partly']+c['different'])/n:.0f}%")
    ps=[p for p in pids if band(p)==b]
    ab=np.array([V[(p,'AB')]!='same' for p in ps]); aa=np.array([V[(p,'AA')]!='same' for p in ps])
    abd=np.array([V[(p,'AB')]=='different' for p in ps]); aad=np.array([V[(p,'AA')]=='different' for p in ps])
    bs=[ (ab[ix].mean()-aa[ix].mean()) for ix in (rng.integers(0,len(ps),len(ps)) for _ in range(4000))]
    bsd=[ (abd[ix].mean()-aad[ix].mean()) for ix in (rng.integers(0,len(ps),len(ps)) for _ in range(4000))]
    print(f"   excess partly-or-different {100*(ab.mean()-aa.mean()):+.0f} pts (CI {100*np.percentile(bs,2.5):+.0f} to {100*np.percentile(bs,97.5):+.0f}); excess 'different' {100*(abd.mean()-aad.mean()):+.0f} (CI {100*np.percentile(bsd,2.5):+.0f} to {100*np.percentile(bsd,97.5):+.0f})")
ab=np.array([V[(p,'AB')]!='same' for p in pids]); aa=np.array([V[(p,'AA')]!='same' for p in pids])
print('all: AB %.0f%%  AA(noise) %.0f%%'%(100*ab.mean(),100*aa.mean()))
R={}
for f in glob.glob(P+'raw/R_set*.out.json'):
    for o in json.load(open(f)): R[o['item_id']]=o
random.seed(5)
d=[p for p in pids if V[(p,'AB')]=='different' and V[(p,'AA')]=='same']
print('\nre-read examples (AB different, AA same):',len(d))
for p in random.sample(d,min(6,len(d))):
    print(f" J {K[p]['J']:.2f} core {K[p]['core']}\n   A: {R[p+'A']['theme']} | {R[p+'A']['core_role'][:150]}\n   B: {R[p+'B']['theme']} | {R[p+'B']['core_role'][:150]}")
json.dump({f'{p}|{k}':v for (p,k),v in V.items()},open('/tmp/lo_verdicts.json','w'))
