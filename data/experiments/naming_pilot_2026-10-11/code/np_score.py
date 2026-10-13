import sys,json,glob,re,collections,numpy as np,os; sys.path.insert(0,'.')
from tf_common import EV,ROOT,M
P=ROOT+'data/experiments/naming_pilot_2026-10-11/'
K=json.load(open(P+'eval/KEY_DO_NOT_SHARE_eval.json')); F=json.load(open(P+'selection/final_names.json'))
def outs(pat):
    d={}
    for f in glob.glob(P+pat):
        for o in json.load(open(f)): d[o['item_id']]=o
    return d
o1=outs('eval/E1_*.out.json'); o2=outs('eval/E2_*.out.json'); o3=outs('eval/E3_*.out.json')
samp=json.load(open(P+'inputs/sample_and_confusables.json'))['sample']; G=set(samp[:150])
E1=collections.defaultdict(dict)
for i,v in K['E1'].items(): E1[v['theme']][v['arm']]=int(o1[i]['choice']==v['correct'])
E2=collections.defaultdict(dict)
for i,v in K['E2'].items(): E2[v['theme']][v['arm']]=1-len(set(o2[i].get('misfits',[])))/v['size']
th=sorted(E1); new=np.array([E1[t]['NEW'] for t in th]); cen=np.array([E1[t]['CENSUS'] for t in th])
rng=np.random.default_rng(0); bs=[]
for _ in range(5000):
    ix=rng.integers(0,len(th),len(th)); bs.append(new[ix].mean()-cen[ix].mean())
lo,hi=np.percentile(bs,[2.5,97.5])
fam=np.array([t in G for t in th])
print('E1 back-matching (chance 20%%): NEW %.1f%%  CENSUS %.1f%%  diff %+.1f pts (95%% CI %+.1f to %+.1f)'%(100*new.mean(),100*cen.mean(),100*(new.mean()-cen.mean()),100*lo,100*hi))
print('   sibling-family themes: NEW %.1f%% CENSUS %.1f%% | others: NEW %.1f%% CENSUS %.1f%%'%(100*new[fam].mean(),100*cen[fam].mean(),100*new[~fam].mean(),100*cen[~fam].mean()))
print('   both right %d, NEW only %d, CENSUS only %d, both wrong %d'%(((new==1)&(cen==1)).sum(),((new==1)&(cen==0)).sum(),((new==0)&(cen==1)).sum(),((new==0)&(cen==0)).sum()))
f_new=np.array([E2[t]['NEW'] for t in th]); f_cen=np.array([E2[t]['CENSUS'] for t in th])
print('E2 member fit: NEW mean %.3f (perfect %.0f%%)  CENSUS mean %.3f (perfect %.0f%%)'%(f_new.mean(),100*(f_new==1).mean(),f_cen.mean(),100*(f_cen==1).mean()))
v3=collections.Counter(o['verdict'] for o in o3.values())
print('E3 reproducibility (60):',dict(v3),' equivalent %.0f%%, equivalent+nested %.0f%%'%(100*v3['equivalent']/60,100*(v3['equivalent']+v3['nested'])/60))
def norm(s): return ' '.join(re.sub(r'[^a-z0-9 ]',' ',s.lower()).split())
CEN={}
for l in open(EV+'names_test/theme_names_c85.tsv').read().splitlines()[1:]:
    n,nm=l.split('\t',1); CEN[n]=nm
dn=collections.Counter(norm(F['main'][t]['name']) for t in th); dc=collections.Counter(norm(CEN[t]) for t in th)
print('E4 duplicates among the 200: NEW %d  CENSUS %d (names shared by >1 theme)'%(sum(c>1 for c in dn.values()),sum(c>1 for c in dc.values())))
print('selection: low_confidence %d, unnameable %d; candidates correct in selection 83.2%%'%(sum(F['main'][t].get('low_confidence',False) for t in th),sum(F['main'][t]['unnameable'] for t in th)))
wl=[len(F['main'][t]['name'].split()) for t in th]; wc=[len(CEN[t].split()) for t in th]
print('name length words: NEW median %d (max %d) CENSUS median %d'%(np.median(wl),max(wl),np.median(wc)))
P1=new.mean()>=0.85; P2=lo>=-0.03; P3=f_new.mean()>=0.90; P4=v3['equivalent']/60>=0.80; P5=sum(c>1 for c in dn.values())==0
print('PASS bars: P1 %s P2 %s P3 %s P4 %s P5 %s'%(P1,P2,P3,P4,P5))
rows=[]
for t in th:
    rows.append(dict(theme=t,size=len(M[t]),census=CEN[t],new=F['main'][t]['name'],e1_new=E1[t]['NEW'],e1_census=E1[t]['CENSUS'],fit_new=round(E2[t]['NEW'],3),fit_census=round(E2[t]['CENSUS'],3),n_correct=F['main'][t]['n_correct'],candidates=F['main'][t]['candidates']))
json.dump(rows,open(P+'eval/scored_rows.json','w'),indent=1)
