import sys; sys.path.insert(0, '/home/claude/nm/sample')
from sm_common import *
K = json.load(open(S + 'eval/KEY_DO_NOT_SHARE_eval.json')); F = json.load(open(S + 'selected_sample.json'))
e1 = {}; e2 = {}
for f in sorted(glob.glob(S + 'evalout/E1_*.out.json')):
    for o in json.load(open(f)): e1[o['item_id']] = o['choice']
for f in sorted(glob.glob(S + 'evalout/E2_*.out.json')):
    for o in json.load(open(f)): e2[o['item_id']] = o.get('misfits', [])
assert set(e1) == set(K['E1']) and set(e2) == set(K['E2'])
ok = {v['theme']: e1[i] == v['correct'] for i, v in K['E1'].items()}
memb = {}
for i, v in K['E2'].items():
    mem = set(json.load(open(glob.glob(S + 'eval/E2_*.json')[0]))[0]['members']) if False else None
fit = {}; badmis = 0
items2 = {it['item_id']: it for f in glob.glob(S + 'eval/E2_*.json') for it in json.load(open(f))}
for i, v in K['E2'].items():
    mis = [m for m in set(e2[i]) if m in set(items2[i]['members'])]; badmis += len(set(e2[i])) - len(mis)
    fit[v['theme']] = 1 - len(mis) / v['size']
T = sorted(ok); rng = random.Random(0)
def boot(vals):
    xs = []
    for _ in range(5000):
        s = [vals[rng.randrange(len(vals))] for _ in vals]; xs.append(sum(s) / len(s))
    xs.sort(); return xs[124], xs[4874]
a = [float(ok[t]) for t in T]; b = [fit[t] for t in T]
P3 = sum(a) / len(a); P4 = sum(b) / len(b)
print('P3 E1 picks own theme %.1f%% CI %.1f-%.1f' % ((100*P3,) + tuple(100*x for x in boot(a))))
print('P4 E2 mean fit %.3f CI %.3f-%.3f' % ((P4,) + boot(b)), 'misfit texts not found in member list:', badmis)
print('fit==1 share %.1f%%' % (100*sum(x == 1 for x in b)/len(b)))
lc = [t for t in T if F[t]['low_confidence']]
print('E1 by n_correct', {k: '%d/%d' % (sum(ok[t] for t in T if F[t]['n_correct'] == k), sum(1 for t in T if F[t]['n_correct'] == k)) for k in range(4)})
sz = lambda t: sum(M[t].values())
for lo, hi in [(3, 10), (11, 50), (51, 200)]:
    tt = [t for t in T if lo <= sz(t) <= hi]
    print(f'size {lo}-{hi}: n={len(tt)} E1 %.1f%% fit %.3f' % (100*sum(ok[t] for t in tt)/len(tt), sum(fit[t] for t in tt)/len(tt)))
fails = [t for t in T if not ok[t]]
json.dump(dict(P3=P3, P4=P4, e1_fail=[dict(theme=t, name=F[t]['name'], n_correct=F[t]['n_correct']) for t in fails],
               low_fit=[dict(theme=t, name=F[t]['name'], fit=fit[t]) for t in sorted(T, key=lambda t: fit[t])[:10]]),
          open(S + 'scores.json', 'w'), indent=1)
print('E1 fails:'); [print(' ', t, F[t]['n_correct'], F[t]['name']) for t in fails]
print('lowest fit:'); [print(' ', t, '%.2f' % fit[t], sz(t), F[t]['name']) for t in sorted(T, key=lambda t: fit[t])[:8]]
