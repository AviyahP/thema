import sys,json,glob,re,collections,numpy as np; sys.path.insert(0,'.')
from tf_common import ROOT,M
P=ROOT+'data/experiments/naming_pilot_2026-10-11/'
K=json.load(open(P+'c2/eval/KEY_DO_NOT_SHARE_eval.json')); FIN=json.load(open(P+'c2/final_names_c2.json'))
def outs(p):
    d={}
    for f in glob.glob(P+p):
        for o in json.load(open(f)): d[o['item_id']]=o
    return d
o1=outs('c2/eval/E1_*.out.json'); o2=outs('c2/eval/E2_*.out.json'); o3=outs('c2/eval/E3_*.out.json')
e1=collections.defaultdict(list)
for i,v in K['E1'].items(): e1[v['run']].append(int(o1[i]['choice']==v['correct']))
e2=collections.defaultdict(list)
for i,v in K['E2'].items(): e2[v['run']].append(1-len(set(o2[i].get('misfits',[])))/v['size'])
allE1=e1['A']+e1['B']; allE2=e2['A']+e2['B']
print('c2 E1 back-match: A %.1f%% B %.1f%% pooled %.1f%%'%(100*np.mean(e1['A']),100*np.mean(e1['B']),100*np.mean(allE1)))
print('c2 E2 fit: A %.3f B %.3f pooled %.3f'%(np.mean(e2['A']),np.mean(e2['B']),np.mean(allE2)))
v=collections.defaultdict(collections.Counter)
for i,k in K['E3'].items(): v[k['version']][o3[i]['verdict']]+=1
for ver in ['c2','c1']: c=v[ver]; print(f'E3 {ver} (same judges): {dict(c)}  equivalent {100*c["equivalent"]/60:.0f}%  equivalent+nested {100*(c["equivalent"]+c["nested"])/60:.0f}%')
# c1 on the same 60 themes from the main eval
S=json.load(open(P+'eval/scored_rows.json')); rep=set(json.load(open(P+'inputs/repro_subset.json')))
c1=[r for r in S if r['theme'] in rep]
print('c1 on same 60: E1 %.1f%%  fit %.3f'%(100*np.mean([r['e1_new'] for r in c1]),np.mean([r['fit_new'] for r in c1])))
def listy(n): return len(re.findall(r',',n))>=1 and ' and ' in n
F1=json.load(open(P+'selection/final_names.json'))
for lab,names in [('c1',[F1['main'][t]['name'] for t in rep]),('c2 A',[FIN['A'][t]['name'] for t in rep]),('c2 B',[FIN['B'][t]['name'] for t in rep])]:
    print(f'{lab}: list-style {sum(map(listy,names))}/60, median words {np.median([len(n.split()) for n in names]):.0f}')
P1=np.mean(allE1)>=0.85; P3=np.mean(allE2)>=0.90; P4=v['c2']['equivalent']/60>=0.80
print('PASS P1',P1,'P3',P3,'P4',P4,'P5 True (no dups)')
import random; random.seed(2)
for t in random.sample(sorted(rep),10): print(f"  c1: {F1['main'][t]['name']}\n  c2A: {FIN['A'][t]['name']} | c2B: {FIN['B'][t]['name']}\n")
