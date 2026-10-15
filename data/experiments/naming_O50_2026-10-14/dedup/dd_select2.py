import sys; sys.path.insert(0, '/home/claude/nm/sample')
from sm_common import *
A = json.load(open('final_names_dedup1.json')); F = A['names']
D = collections.defaultdict(dict)
for s in [0, 1, 2]:
    out = json.load(open(f'raw/dedup2_slot{s}_b01.out.json'))
    assert [o['theme_id'] for o in out] == ['n00337', 'n00666']
    for o in out: D[o['theme_id']][s] = o
for t, cs in D.items():
    nm = [s for s in sorted(cs) if cs[s].get('nameable', True)]
    T = {s: toks(cs[s]['name']) for s in nm}
    best = min(nm, key=lambda s: (-sum(jac(T[s], T[o]) for o in nm if o != s), s))
    F[t] = dict(F[t], name=cs[best]['name'], method=F[t]['method'].replace('+dedup1', '') + '+dedup2',
                candidates_round2=[cs[s]['name'] for s in sorted(cs)])
    print(t, '->', F[t]['name'], [cs[s]['name'] for s in sorted(cs)])
cnt = collections.defaultdict(list)
for t, v in F.items():
    if not v['unnameable']: cnt[norm(v['name'])].append(t)
dups = {k: v for k, v in cnt.items() if len(v) > 1}
json.dump(dict(names=F, duplicates_final=dups), open('final_names_O50_lite_unique.json', 'w'), indent=1)
with open('final_names_O50_lite_unique.tsv', 'w') as fh:
    fh.write('theme_id\tname\tmethod\tunnameable\tduplicate_group\n')
    for t, v in sorted(F.items()):
        g = norm(v['name']) if not v['unnameable'] and norm(v['name']) in dups else ''
        fh.write(f"{t}\t{v.get('name','').replace(chr(9),' ')}\t{v['method']}\t{v['unnameable']}\t{g}\n")
print('remaining duplicates', dups)
print(collections.Counter(v['method'] for v in F.values()))
