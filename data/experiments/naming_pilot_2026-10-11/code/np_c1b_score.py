import sys,json,glob,re,collections,numpy as np; sys.path.insert(0,'.')
from tf_common import ROOT
P=ROOT+'data/experiments/naming_pilot_2026-10-11/'
K=json.load(open(P+'c1b/eval/KEY_DO_NOT_SHARE_eval.json')); FIN=json.load(open(P+'c1b/final_names_c1b.json'))
def outs(p):
    d={}
    for f in glob.glob(P+p):
        for o in json.load(open(f)): d[o['item_id']]=o
    return d
o1=outs('c1b/eval/E1_*.out.json'); o2=outs('c1b/eval/E2_*.out.json'); o3=outs('c1b/eval/E3_*.out.json')
E1=collections.defaultdict(dict); E2=collections.defaultdict(dict)
for i,v in K['E1'].items(): E1[v['set']][v['theme']]=int(o1[i]['choice']==v['correct'])
for i,v in K['E2'].items(): E2[v['set']][v['theme']]=1-len(set(o2[i].get('misfits',[])))/v['size']
th=sorted(E1['c1_M'])
for s in ['c1b_M','c1b_R','c1_M','c1_R']: print(f"{s}: E1 {100*np.mean([E1[s][t] for t in th]):.1f}%  fit {np.mean([E2[s][t] for t in th]):.3f}")
b=np.array([E1['c1b_M'][t]+E1['c1b_R'][t] for t in th])/2; a=np.array([E1['c1_M'][t]+E1['c1_R'][t] for t in th])/2
fb=np.array([E2['c1b_M'][t]+E2['c1b_R'][t] for t in th])/2; fa=np.array([E2['c1_M'][t]+E2['c1_R'][t] for t in th])/2
rng=np.random.default_rng(0); d=[];df=[]
for _ in range(5000):
    ix=rng.integers(0,60,60); d.append(b[ix].mean()-a[ix].mean()); df.append(fb[ix].mean()-fa[ix].mean())
print('pooled E1: c1b %.1f%% c1 %.1f%% diff %+.1f (CI %+.1f to %+.1f)'%(100*b.mean(),100*a.mean(),100*(b.mean()-a.mean()),100*np.percentile(d,2.5),100*np.percentile(d,97.5)))
print('pooled fit: c1b %.3f c1 %.3f diff %+.3f (CI %+.3f to %+.3f)'%(fb.mean(),fa.mean(),fb.mean()-fa.mean(),np.percentile(df,2.5),np.percentile(df,97.5)))
v=collections.defaultdict(collections.Counter); per=collections.defaultdict(dict)
for i,k in K['E3'].items(): v[k['version']][o3[i]['verdict']]+=1; per[k['version']][k['theme']]=o3[i]['verdict']
for ver in ['c1b','c1']: c=v[ver]; print(f"E3 {ver}: {dict(c)} equivalent {100*c['equivalent']/60:.0f}% eq+nested {100*(c['equivalent']+c['nested'])/60:.0f}%")
eqb=np.array([per['c1b'][t]=='equivalent' for t in th]); eqa=np.array([per['c1'][t]=='equivalent' for t in th]); d3=[]
for _ in range(5000):
    ix=rng.integers(0,60,60); d3.append(eqb[ix].mean()-eqa[ix].mean())
print('E3 equivalent diff c1b-c1 %+.0f pts (CI %+.0f to %+.0f)'%(100*(eqb.mean()-eqa.mean()),100*np.percentile(d3,2.5),100*np.percentile(d3,97.5)))
same=sum(FIN['c1b_M'][t]['name'].lower()==FIN['c1b_R'][t]['name'].lower() for t in th); same1=sum(FIN['c1_M'][t]['name'].lower()==FIN['c1_R'][t]['name'].lower() for t in th)
print('identical final names across runs: c1b %d/60, c1 %d/60'%(same,same1))
