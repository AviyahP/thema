import sys, csv, math; sys.path.insert(0, '/home/claude/nm/sample')
from sm_common import *
K = json.load(open('eval/KEY_DO_NOT_SHARE_style.json'))
def load(p, field):
    d = {}
    for f in sorted(glob.glob(f'evalout/{p}_*.out.json')):
        inp = [i['item_id'] for i in json.load(open(f.replace('evalout', 'eval').replace('.out.json', '.json')))]
        out = json.load(open(f)); assert [o['item_id'] for o in out] == inp, f
        for o in out: d[o['item_id']] = o.get(field)
    return d
e1 = load('E1', 'choice'); e2 = load('E2', 'misfits'); p1 = load('P1', 'choice')
assert set(e1) == set(K['E1']) and set(e2) == set(K['E2']) and set(p1) == set(K['P1'])
items2 = {it['item_id']: it for f in glob.glob('eval/E2_*.json') for it in json.load(open(f))}
ok = collections.defaultdict(dict); fit = collections.defaultdict(dict)
for i, v in K['E1'].items(): ok[v['theme']][v['arm']] = float(e1[i] == v['correct'])
for i, v in K['E2'].items():
    mis = [m for m in set(e2[i] or []) if m in set(items2[i]['members'])]
    fit[v['theme']][v['arm']] = 1 - len(mis) / v['size']
T = sorted(ok); rng = random.Random(0)
def boot(vals):
    xs = sorted(sum(vals[rng.randrange(len(vals))] for _ in vals) / len(vals) for _ in range(5000)); return xs[124], xs[4874]
for arm in ['OLD', 'NEW']:
    a = [ok[t][arm] for t in T]; b = [fit[t][arm] for t in T]
    print(arm, 'E1 %.1f%%' % (100*sum(a)/len(a)), 'E2 %.3f' % (sum(b)/len(b)))
d1 = [ok[t]['NEW'] - ok[t]['OLD'] for t in T]; d2 = [fit[t]['NEW'] - fit[t]['OLD'] for t in T]
lo, hi = boot(d1); print('D1 %.1f pts CI %.1f to %.1f' % (100*sum(d1)/len(d1), 100*lo, 100*hi))
lo, hi = boot(d2); print('D2 %.3f CI %.3f to %.3f' % (sum(d2)/len(d2), lo, hi))
new = old = eq = 0
for i, v in K['P1'].items():
    c = p1[i]
    if c == 'equal': eq += 1
    elif v[c] == 'NEW': new += 1
    else: old += 1
n = new + old
from math import comb
p = min(1, 2*sum(comb(n, k) for k in range(max(new, old), n+1)) / 2**n)
print('P1 NEW %d OLD %d equal %d -> NEW share %.1f%% p=%.2g' % (new, old, eq, 100*new/n, p))
print('E1 flips: OLD ok NEW wrong', sum(1 for t in T if ok[t]['OLD'] == 1 and ok[t]['NEW'] == 0), '| OLD wrong NEW ok', sum(1 for t in T if ok[t]['OLD'] == 0 and ok[t]['NEW'] == 1))
NEWN = json.load(open('new_names.json'))['new']
OLD = {r['theme_id']: r['name'] for r in csv.DictReader(open('/home/claude/nm/dedup/final_names_O50_lite_unique.tsv'), delimiter='\t')}
print('unifying=false:', [(t, NEWN[t]['name']) for t in T if not NEWN[t].get('unifying', True)])
print('NEW lost E1:'); [print('  ', OLD[t], '=>', NEWN[t]['name']) for t in T if ok[t]['OLD'] == 1 and ok[t]['NEW'] == 0]
json.dump(dict(E1={t: ok[t] for t in T}, E2={t: fit[t] for t in T}, P1=dict(new=new, old=old, equal=eq, p=p)), open('scores_style.json', 'w'), indent=1)
