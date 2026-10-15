import json,numpy as np,collections
from scipy.stats import rankdata
S={r['id']:r for r in json.load(open('/tmp/tf_static.json'))}
for r in json.load(open('/tmp/tf_runs.json')): S[r['id']].update(r)
R=list(S.values())
DIR=dict(J='T',A1='F',A2='F',A3='F',A4='T',B1='F',B2='F',B3='T',B4='T',C1='F',C2='T',C3='F',C4='T',C5='F',
 D1='F',D2='F',D3='T',D4='F',D5='F',D7='F',E1='T',E2='T',E3='T',E4='T',E5='T',E6='F',E7='T',F1='T',F2='F',F3='T',F4='T',F5='T')
y=np.array([r['y'] for r in R],bool); Jv=np.array([r['J'] for r in R]); fam=np.array([r['fam'] for r in R])
rng=np.random.default_rng(0); half=rng.random(len(R))<0.5
def auc(x,yy):
    m=~np.isnan(x); x,yy=x[m],yy[m]; n1=yy.sum(); n0=len(yy)-n1
    if n1==0 or n0==0: return np.nan,0
    rk=rankdata(x); return (rk[yy].sum()-n1*(n1+1)/2)/(n1*n0), n1*n0
def strat(x,groups):
    num=0;den=0
    for g in np.unique(groups):
        m=groups==g; a,w=auc(x[m],y[m])
        if w: num+=a*w; den+=w
    return num/den if den else np.nan
band=np.digitize(Jv,[0.5,0.6])
out=[]
for k,d in DIR.items():
    x=np.array([r.get(k,np.nan) for r in R],float)
    if d=='F': x=-x
    a,_=auc(x,y); h1,_=auc(x[half],y[half]); h2,_=auc(x[~half],y[~half])
    sb=strat(x,band) if k!='J' else np.nan; sf=strat(x,fam)
    passed = h1>=0.65 and h2>=0.65 and (k=='J' or sb>=0.60)
    out.append((k,d,a,h1,h2,sb,sf,int((~np.isnan(x)).sum()),passed))
print(f"{'feat':<4} dir {'AUC':>5} {'half1':>5} {'half2':>5} {'Jband':>5} {'family':>6} {'n':>5} pass")
for o in out: print(f"{o[0]:<4} {o[1]:>3} {o[2]:.3f} {o[3]:.3f} {o[4]:.3f} {o[5]:.3f} {o[6]:.3f} {o[7]:5d} {o[8]}")
print('\n--- post-hoc diagnostics ---')
import sys
from tf_common import M
Usz=np.array([len(M[r['id'].split('|')[0]]|M[r['id'].split('|')[1]]) for r in R],float)
A1=np.array([r['A1'] for r in R],float); A2=np.array([r['A2'] for r in R],float); C4=np.array([r['C4'] for r in R],float)
print('size |U| (F dir) AUC %.3f'%auc(-Usz,y)[0])
ub=np.digitize(Usz,[15,25,40,70])
print('A1 stratified by |U| bins %.3f ; A2 %.3f ; J %.3f ; C4 %.3f'%(strat(-A1,ub),strat(-A2,ub),strat(Jv,ub),strat(C4,ub)))
jb=band*10+ub
print('A1 stratified by J band x |U| bin %.3f ; C4 %.3f'%(strat(-A1,jb),strat(C4,jb)))
print('\nmin(|a|,|b|) table: n, twin%')
for lo,hi in [(1,1),(2,2),(3,3),(4,5),(6,8),(9,15),(16,1e9)]:
    m=(A1>=lo)&(A1<=hi); print(f"  {lo}-{hi if hi<1e9 else '+'}: n={m.sum():5d} twin%={100*y[m].mean():.1f}")
print('\nJ band x min-diff: twin% (n)')
for b,nm in enumerate(['0.4-0.5','0.5-0.6','0.6-0.7']):
    line=nm+': '
    for lo,hi in [(1,2),(3,5),(6,1e9)]:
        m=(band==b)&(A1>=lo)&(A1<=hi); line+=f" [{lo}-{hi if hi<1e9 else '+'}] {100*y[m].mean():.0f}% ({m.sum()})"
    print(line)
print('\nC4 (centroid cosine A vs B) quantile bins: twin% (n)')
qs=np.quantile(C4,[0.2,0.4,0.6,0.8,0.9])
cb=np.digitize(C4,qs)
for b in range(6):
    m=cb==b; print(f"  bin{b} C4 {C4[m].min():.3f}-{C4[m].max():.3f}: twin% {100*y[m].mean():.1f} (n={m.sum()})")
print('\ncandidate merge rules (post-hoc, descriptive): n, twin% (precision), share of all twins caught (recall)')
rules={'J>=0.65 (old)':Jv>=0.65,'J>=0.6 & mindiff<=2':(Jv>=0.6)&(A1<=2),'J>=0.5 & mindiff<=2':(Jv>=0.5)&(A1<=2),
 'mindiff<=2':A1<=2,'C4>=q90':C4>=qs[4],'C4>=q80':C4>=qs[3],'C4>=q80 & mindiff<=2':(C4>=qs[3])&(A1<=2),'C4>=q60 & mindiff<=2':(C4>=qs[2])&(A1<=2)}
for k,m in rules.items():
    print(f"  {k:<24} n={m.sum():5d} precision={100*y[m].mean():.1f}% recall={100*(y&m).sum()/y.sum():.1f}%  [half1 {100*y[m&half].mean():.1f} / half2 {100*y[m&~half].mean():.1f}]")
