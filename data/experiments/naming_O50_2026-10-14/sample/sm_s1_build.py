import sys; sys.path.insert(0, '/home/claude/nm/sample')
from sm_common import *
items = []; key = {}
order = sorted((t, s) for t in SAMPLE for s in C[t]); random.Random(99).shuffle(order)
for i, (t, s) in enumerate(order):
    o = C[t][s]
    if not o.get('nameable', True): continue
    iid = f'M{i:04d}'
    it, correct, _ = clusters_item(t, o['name'], f'S{s}', iid); items.append(it); key[iid] = dict(theme=t, cand=s, correct=correct)
os.makedirs(S + 's1', exist_ok=True)
json.dump(key, open(S + 's1/KEY_DO_NOT_SHARE_s1.json', 'w'))
for b in range(0, len(items), 50):
    json.dump(items[b:b+50], open(S + f's1/s1_sel_{b//50+1:02d}.json', 'w'), indent=1)
print('items', len(items), 'files', (len(items)+49)//50, 'unnameable votes in sample', sum(1 for t in SAMPLE for s in C[t] if not C[t][s].get('nameable', True)))
