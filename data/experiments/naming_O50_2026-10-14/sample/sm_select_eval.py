import sys; sys.path.insert(0, '/home/claude/nm/sample')
from sm_common import *
key = json.load(open(S + 's1/KEY_DO_NOT_SHARE_s1.json'))
ch = {}; bad = []
for f in sorted(glob.glob(S + 's1out/s1_sel_*.out.json')):
    inp = [i['item_id'] for i in json.load(open(f.replace('s1out', 's1').replace('.out.json', '.json')))]
    out = json.load(open(f))
    if [o['item_id'] for o in out] != inp or any(o.get('choice') not in list('ABCDE') for o in out): bad.append(f)
    for o in out: ch[o['item_id']] = o['choice']
assert not bad and set(ch) == set(key), (bad, len(ch), len(key))
corr = {(v['theme'], v['cand']): ch[i] == v['correct'] for i, v in key.items()}
F = {}
for t in SAMPLE:
    cs = C[t]; nameable = [s for s in sorted(cs) if cs[s].get('nameable', True)]
    if len(cs) - len(nameable) >= 2: F[t] = dict(unnameable=True); continue
    pool = [s for s in nameable if corr.get((t, s))]; low = not pool
    if low: pool = nameable
    T = {s: toks(cs[s]['name']) for s in nameable}
    best = min(pool, key=lambda s: (-sum(jac(T[s], T[o]) for o in nameable if o != s), s))
    F[t] = dict(unnameable=False, name=cs[best]['name'], cand=best, n_correct=sum(bool(corr.get((t, s))) for s in nameable),
                n_nameable=len(nameable), low_confidence=low, candidates=[cs[s]['name'] for s in sorted(cs)],
                correct_flags=[bool(corr.get((t, s))) for s in sorted(cs)])
json.dump(F, open(S + 'selected_sample.json', 'w'), indent=1)
named = [t for t in SAMPLE if not F[t]['unnameable']]
P1 = sum(corr.values()) / len(corr); P2 = sum(not F[t]['low_confidence'] for t in named) / len(named)
print('P1 candidate correct %.1f%% (%d/%d)' % (100*P1, sum(corr.values()), len(corr)))
print('P2 themes with >=1 correct %.1f%%' % (100*P2), 'n_correct dist', collections.Counter(F[t]['n_correct'] for t in named))
e1 = []; k1 = {}; e2 = []; k2 = {}
for t in named:
    it, correct, r = clusters_item(t, F[t]['name'], 'ENEW', f'X{len(e1):04d}')
    e1.append(it); k1[it['item_id']] = dict(theme=t, correct=correct)
    mem = expand(M[t]); r.shuffle(mem)
    jid = f'Y{len(e2):04d}'; e2.append(dict(item_id=jid, name=F[t]['name'], members=mem)); k2[jid] = dict(theme=t, size=len(mem))
random.Random(11).shuffle(e1); random.Random(12).shuffle(e2)
os.makedirs(S + 'eval', exist_ok=True)
for b in range(0, len(e1), 50):
    json.dump(e1[b:b+50], open(S + f'eval/E1_{b//50+1:02d}.json', 'w'), indent=1)
    json.dump(e2[b:b+50], open(S + f'eval/E2_{b//50+1:02d}.json', 'w'), indent=1)
json.dump(dict(E1=k1, E2=k2), open(S + 'eval/KEY_DO_NOT_SHARE_eval.json', 'w'))
dups = {}
for s in range(3):
    cnt = collections.Counter(norm(C[t][s]['name']) for t in C if C[t][s].get('nameable', True) and C[t][s].get('name'))
    dups[s] = (sum(c for c in cnt.values() if c > 1), sum(cnt.values()))
print('dup candidates per slot (in duplicated names / total)', dups)
print('E1', len(e1), 'E2', len(e2))
