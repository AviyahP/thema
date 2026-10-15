import sys; sys.path.insert(0, '/home/claude/nm/sample')
from sm_common import *
FS = json.load(open(S + 'selected_sample.json'))
out = {}
for t in sorted(C):
    cs = C[t]; nm = [s for s in sorted(cs) if cs[s].get('nameable', True)]
    if len(cs) - len(nm) >= 2:
        out[t] = dict(unnameable=True, rationale=cs[0].get('rationale', ''), method='unnameable'); continue
    if t in FS:
        f = FS[t]; out[t] = dict(unnameable=False, name=f['name'], cand=f['cand'], method='s1_sample', n_correct=f['n_correct'],
                                low_confidence=f['low_confidence'], candidates=f['candidates']); continue
    T = {s: toks(cs[s]['name']) for s in nm}
    best = min(nm, key=lambda s: (-sum(jac(T[s], T[o]) for o in nm if o != s), s))
    out[t] = dict(unnameable=False, name=cs[best]['name'], cand=best, method='medoid_no_s1', n_nameable=len(nm),
                  candidates=[cs[s]['name'] for s in sorted(cs)])
dup = collections.defaultdict(list)
for t, v in out.items():
    if not v['unnameable']: dup[norm(v['name'])].append(t)
dups = {k: v for k, v in dup.items() if len(v) > 1}
json.dump(dict(names=out, duplicates=dups), open('final_names_lite.json', 'w'), indent=1)
with open('final_names_lite.tsv', 'w') as fh:
    fh.write('theme_id\tname\tmethod\tunnameable\tduplicate_group\n')
    for t, v in sorted(out.items()):
        g = norm(v['name']) if not v['unnameable'] and norm(v['name']) in dups else ''
        fh.write(f"{t}\t{v.get('name','').replace(chr(9),' ')}\t{v['method']}\t{v['unnameable']}\t{g}\n")
print('themes', len(out), collections.Counter(v['method'] for v in out.values()))
print('duplicate groups', len(dups), 'themes in them', sum(len(v) for v in dups.values()), 'sizes', collections.Counter(len(v) for v in dups.values()))
for k, v in list(sorted(dups.items(), key=lambda kv: -len(kv[1])))[:8]: print(' ', len(v), k)
