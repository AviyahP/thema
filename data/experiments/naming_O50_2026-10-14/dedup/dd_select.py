import sys; sys.path.insert(0, '/home/claude/nm/sample')
from sm_common import *
L = json.load(open('/home/claude/nm/select_lite/final_names_lite.json')); names = L['names']
bad = []; D = collections.defaultdict(dict)
for f in sorted(glob.glob('inputs/dedup_slot*_b*.json')):
    inp = [t['theme_id'] for t in json.load(open(f))]
    out = json.load(open(f.replace('inputs/', 'raw/').replace('.json', '.out.json')))
    if [o.get('theme_id') for o in out] != inp or any(not isinstance(o.get('nameable'), bool) or (o['nameable'] and not o.get('name')) for o in out): bad.append(f)
    s = int(f.split('slot')[1][0])
    for o in out: D[o['theme_id']][s] = o
print('invalid files', bad)
new = {}
for t, cs in D.items():
    nm = [s for s in sorted(cs) if cs[s].get('nameable', True)]
    if len(cs) - len(nm) >= 2: new[t] = dict(unnameable=True); continue
    T = {s: toks(cs[s]['name']) for s in nm}
    best = min(nm, key=lambda s: (-sum(jac(T[s], T[o]) for o in nm if o != s), s))
    new[t] = dict(name=cs[best]['name'], cand=best, candidates=[cs[s]['name'] for s in sorted(cs)], old_name=names[t]['name'])
final = {}
for t, v in names.items():
    if t in new:
        if new[t].get('unnameable'): final[t] = dict(unnameable=True, method='dedup_unnameable')
        else: final[t] = dict(unnameable=False, name=new[t]['name'], method=names[t]['method'] + '+dedup1', old_name=new[t]['old_name'], candidates=new[t]['candidates'])
    else: final[t] = v
cnt = collections.defaultdict(list)
for t, v in final.items():
    if not v['unnameable']: cnt[norm(v['name'])].append(t)
dups = {k: v for k, v in cnt.items() if len(v) > 1}
json.dump(dict(names=final, duplicates_after_dedup1=dups), open('final_names_dedup1.json', 'w'), indent=1)
with open('final_names_dedup1.tsv', 'w') as fh:
    fh.write('theme_id\tname\tmethod\tunnameable\tduplicate_group\n')
    for t, v in sorted(final.items()):
        g = norm(v['name']) if not v['unnameable'] and norm(v['name']) in dups else ''
        fh.write(f"{t}\t{v.get('name','').replace(chr(9),' ')}\t{v['method']}\t{v['unnameable']}\t{g}\n")
print('re-asked', len(new), 'became unnameable', sum(1 for v in new.values() if v.get('unnameable')))
print('remaining duplicate groups', len(dups), 'themes', sum(len(v) for v in dups.values()))
for k, v in dups.items(): print(' ', v, k)
import itertools
for t in list(new)[:6]:
    if not new[t].get('unnameable'): print(t, '|', new[t]['old_name'], '->', new[t]['name'])
