import sys,os,csv,collections,json,glob,random,numpy as np; sys.path.insert(0,'.')
from tf_common import ROOT
from scipy.stats import binomtest
P=ROOT+'data/experiments/o50_eval_2026-10-13/'
C85=ROOT+'data/ontology/v0.4-leaves/thema_L_x2_c85/'; O=ROOT+'data/ontology/v0.4-leaves/thema_L_x2_O50/'
def mem(d):
    M=collections.defaultdict(set)
    for r in csv.DictReader(open(d+'members.tsv'),delimiter='\t'): M[r['node']].add(r['key'])
    return M
Mc=mem(C85); MO=mem(O)
V=json.load(open(ROOT+'data/ontology/frozen/working-c85-2026-10-10/all_verdicts_c85.json'))
ok=lambda v:v in ('coherent','umbrella')
c85_bad=sum(1 for v in V.values() if not ok(v['verdict']))
idx={frozenset(s):k for k,s in Mc.items()}
J4={}
for f in glob.glob(P+'judged/C4_*.out.json'):
    for o in json.load(open(f)): J4[o['id']]=o
carried=[k for k,s in MO.items() if frozenset(s) in idx]
cb=sum(1 for k in carried if not ok(V[idx[frozenset(MO[k])]]['verdict']))
nb=sum(1 for k in J4 if not ok(J4[k]['verdict']))
vc=collections.Counter(o['verdict'] for o in J4.values())
print(f"C4: c85 not-ok {c85_bad} of {len(V)} ({100*(1-c85_bad/len(V)):.2f}% ok)")
print(f"    O50: carried {len(carried)} themes, not-ok {cb}; new {len(J4)} judged, not-ok {nb} -> total not-ok {cb+nb} of {len(MO)} ({100*(1-(cb+nb)/len(MO)):.2f}% ok)  -> {'PASS' if cb+nb<=c85_bad else 'FAIL'} (bar <= {c85_bad})")
print('    new-theme verdicts',dict(vc))
sz=lambda k:len(MO[k])
for a,b in ((3,20),(21,50),(51,200),(201,999),(1000,9999)):
    ks=[k for k in J4 if a<=sz(k)<=b]
    if ks: print(f'    new themes {a}-{b}: n={len(ks)} ok {100*np.mean([ok(J4[k]["verdict"]) for k in ks]):.0f}%')
K=json.load(open(P+'c5/KEY_DO_NOT_SHARE.json')); J5={}
for f in glob.glob(P+'judged/C5_*.out.json'):
    for o in json.load(open(f)): J5[o['item_id']]=o
w=collections.Counter()
for i,o in J5.items():
    b=o['better']; w['equal' if b=='equal' else K[i][b]]+=1
dec=w['O50']+w['c85']; p=binomtest(w['O50'],dec,0.5).pvalue if dec else 1
print(f"\nC5: O50 preferred {w['O50']}, c85 preferred {w['c85']}, equal {w['equal']} | O50 share of decided {100*w['O50']/dec:.1f}% (n={dec}), binomial p={p:.2g} -> {'O50 WINS' if w['O50']/dec>=0.6 and p<0.05 else ('c85 WINS' if w['c85']/dec>=0.6 and p<0.05 else 'not won')}")
random.seed(1)
for side in ('O50','c85'):
    ids=[i for i,o in J5.items() if o['better']!='equal' and K[i][o['better']]==side]
    print(f'  reasons when {side} preferred:'); [print('    -',J5[i]['reason'][:200]) for i in random.sample(ids,min(5,len(ids)))]
bad=[k for k in J4 if not ok(J4[k]['verdict'])]
print('\n  new themes not ok, examples:'); [print('    ',sz(k),J4[k]['verdict'],'|',J4[k]['label'],'|',J4[k]['reason'][:120]) for k in random.sample(bad,min(6,len(bad)))]
