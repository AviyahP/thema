import json,glob,collections,numpy as np,random,os
P=os.path.expanduser('~/mnt/thema/data/experiments/hidef_eval_2026-10-13/')
K=json.load(open(P+'inputs/KEY_DO_NOT_SHARE.json')); O={}
for f in glob.glob(P+'judged/Q_*.out.json'):
    for o in json.load(open(f)): O[o['id']]=o
rng=np.random.default_rng(0)
arms=('HiDeF','THEMA')
A={a:[i for i in sorted(O) if K[i]['arm']==a] for a in arms}
def m(a,f): return np.array([f(O[i]) for i in A[a]],float)
for a in arms:
    print(a,'verdicts',dict(collections.Counter(O[i]['verdict'] for i in A[a])),'| nameability',dict(collections.Counter(O[i]['nameability'] for i in A[a])))
for lab,f in (('ok (coherent or umbrella)',lambda o:o['verdict'] in('coherent','umbrella')),('coherent only',lambda o:o['verdict']=='coherent'),('nameable easy',lambda o:o['nameability']=='easy'),('easy or broad',lambda o:o['nameability']!='hard')):
    h=m('HiDeF',f); t=m('THEMA',f)
    d=[h[rng.integers(0,100,100)].mean()-t[rng.integers(0,100,100)].mean() for _ in range(5000)]
    lo,hi=np.percentile(d,[2.5,97.5]); diff=h.mean()-t.mean()
    verdict='HiDeF better' if diff>=.10 and lo>0 else ('THEMA better' if diff<=-.10 and hi<0 else 'equivalent')
    print(f"{lab:<28} HiDeF {100*h.mean():.0f}%  THEMA {100*t.mean():.0f}%  diff {100*diff:+.0f} (CI {100*lo:+.0f} to {100*hi:+.0f}) -> {verdict}")
print('by size band, ok / easy:')
for a0,b0 in ((3,6),(7,15),(16,40),(41,100)):
    row=[]
    for a in arms:
        ids=[i for i in A[a] if a0<=K[i]['size']<=b0]
        row.append(f"{a} n={len(ids)} ok {100*np.mean([O[i]['verdict'] in('coherent','umbrella') for i in ids]):.0f}% easy {100*np.mean([O[i]['nameability']=='easy' for i in ids]):.0f}%")
    print(f'  {a0}-{b0}: '+' | '.join(row))
random.seed(2)
for a in arms:
    bad=[i for i in A[a] if O[i]['verdict'] not in ('coherent','umbrella')]
    print(f'\n{a} not ok ({len(bad)}):'); [print('  ',K[i]['size'],O[i]['verdict'],'|',O[i]['name'],'|',O[i]['reason'][:110]) for i in bad[:6]]
    print(f'{a} sample names:'); [print('  ',K[i]['size'],O[i]['nameability'],'|',O[i]['name']) for i in random.sample(A[a],6)]
