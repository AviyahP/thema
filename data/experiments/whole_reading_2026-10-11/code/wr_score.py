import sys,json,glob,collections,numpy as np,random; sys.path.insert(0,'.')
from tf_common import ROOT
from scipy.stats import rankdata
E=ROOT+'data/experiments/'
P=E+'whole_reading_2026-10-11/'
K=json.load(open(P+'inputs/KEY_DO_NOT_SHARE.json')); PR=K['pairs']; CK=json.load(open(P+'compare/KEY_DO_NOT_SHARE.json'))
V={};RS={}
for f in glob.glob(P+'compare/W2_*.out.json'):
    for o in json.load(open(f)): p=CK[o['item_id']]['pair']; V[p]=o['verdict']; RS[p]=o['reason']
KH=json.load(open(E+'core_reading_pilot_2026-10-11/inputs/KEY_DO_NOT_SHARE.json')); CH=json.load(open(E+'core_reading_pilot_2026-10-11/compare/KEY_DO_NOT_SHARE.json'))
OH={}
for f in glob.glob(E+'core_reading_pilot_2026-10-11/compare/C1_*.out.json'):
    for o in json.load(open(f)): OH[CH[o['item_id']]]=o['verdict']
OL=json.load(open('/tmp/lo_verdicts.json')) if len(sys.argv)<2 else {}
PI=json.load(open('/tmp/pairinfo.json'))
S={s:sorted(p for p in PR if PR[p]['set']==s) for s in ('HIGH','LOW','SYN')}
rd=lambda ps:np.array([V[p]!='same' for p in ps]); dd=lambda ps:np.array([V[p]=='different' for p in ps])
rng=np.random.default_rng(0)
def ci(a,b=None,n=5000):
    r=[]
    for _ in range(n):
        x=a[rng.integers(0,len(a),len(a))].mean()
        if b is not None: x-=b[rng.integers(0,len(b),len(b))].mean()
        r.append(x)
    return 100*np.percentile(r,2.5),100*np.percentile(r,97.5)
print('set   n  same partly different | partly-or-diff (CI)')
for s,ps in S.items():
    c=collections.Counter(V[p] for p in ps); a=rd(ps); lo,hi=ci(a)
    print(f"{s:<5}{len(ps):4d} {c['same']:5d} {c['partly']:6d} {c['different']:6d}   | {100*a.mean():.1f}% ({lo:.1f}-{hi:.1f})")
H=rd(S['HIGH']); Sy=rd(S['SYN']); L=rd(S['LOW'])
lo,hi=ci(H,Sy); print(f"\nP1 HIGH minus floor: {100*(H.mean()-Sy.mean()):+.1f} pts (CI {lo:+.1f} to {hi:+.1f})")
oh=np.array([OH[p[1:]]!='same' for p in S['HIGH']])
print(f"P2 same 300 pairs: old design {100*oh.mean():.1f}%  new design {100*H.mean():.1f}%")
t=collections.Counter((bool(a),bool(b)) for a,b in zip(oh,H)); print('   old->new (re-read?):',{f'{k[0]}->{k[1]}':v for k,v in sorted(t.items())})
lo,hi=ci(L,Sy); print(f"P3 LOW minus floor: {100*(L.mean()-Sy.mean()):+.1f} pts (CI {lo:+.1f} to {hi:+.1f})")
for b in (1,2,3):
    ps=[p for p in S['LOW'] if int(PR[p]['J']*10)==b]; a=rd(ps); o=np.array([OL[p[1:]+'|AB']!='same' for p in ps])
    print(f"   J 0.{b}-0.{b+1}: new {100*a.mean():.0f}%  old design (same pairs) {100*o.mean():.0f}%  n={len(ps)}")
d=100*(H.mean()-Sy.mean()); lo,hi=ci(H,Sy)
print('\nDeclared reading:', 'REVISED' if (d>=38 and lo>23) else ('CONFIRMED' if d<=30 else 'neither'))
print('\nSecondary — by old label (HIGH):')
for l in ('twin','facet'):
    ps=[p for p in S['HIGH'] if PR[p]['label']==l]; c=collections.Counter(V[p] for p in ps); print(f"  {l}: {dict(c)}  re-read {100*rd(ps).mean():.0f}%")
y=np.array([PR[p]['label']=='facet' for p in S['HIGH']]); sc={'same':0,'partly':1,'different':2}
x=np.array([sc[V[p]] for p in S['HIGH']],float)
md=np.array([PI[KH[p[1:]]['pair']]['md'] for p in S['HIGH']],float)
def auc(f,yy):
    r=rankdata(f); a=yy.sum(); b=len(yy)-a; return (r[yy].sum()-a*(a+1)/2)/(a*b)
xo=np.array([sc[OH[p[1:]]] for p in S['HIGH']],float)
print(f"  AUC vs labels: whole-reading {auc(x,y):.3f}  old core-reading {auc(xo,y):.3f}  md {auc(md,y):.3f}")
print('  re-read by md:',{int(m):f"{100*H[md==m].mean():.0f}% (n={int((md==m).sum())})" for m in sorted(set(md)) if (md==m).sum()>=10})
random.seed(7)
for s in ('HIGH','SYN','LOW'):
    c=[p for p in S[s] if V[p]!='same']; print(f'\n== {s} re-read reasons ({len(c)}):')
    for p in random.sample(c,min(6,len(c))): print(f"  [{V[p]}] J {PR[p]['J']:.2f} {PR[p]['label']}: {RS[p]}")
