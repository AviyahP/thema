import csv, collections, os, json, random
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.abspath(HERE + '/..'); T = os.path.abspath(HERE + '/../../../..')
B = T + '/data/ontology/v0.4-leaves/thema_L_x2_O50s/'
csv.field_size_limit(10**9)
def tsv(p): return list(csv.DictReader(open(p), delimiter='\t'))
pname = {r['source'] + ':' + r['source_id']: (r['name'], r['source']) for r in tsv(T + '/data/pathways.tsv')}
M = collections.defaultdict(set)
for r in tsv(B + 'members.tsv'): M[r['node']].add(r['key'])
has_parent = {r['child'] for r in tsv(B + 'edges.tsv')}
roots = sorted(n for n in M if n not in has_parent)
rng = random.Random(20261018)
order = roots[:]; rng.shuffle(order)
rid = {n: f'R{i:03d}' for i, n in enumerate(order, 1)}
def name(k): return pname[k][0]
def render(keys): return [f'- {pname[k][0]} [{pname[k][1]}]' for k in sorted(keys, key=lambda k: name(k).lower())]
os.makedirs(OUT + '/read_inputs', exist_ok=True); os.makedirs(OUT + '/small_inputs', exist_ok=True)
batches = [[]]; lines = 0
for n in order:
    t = [f'# {rid[n]} ({len(M[n])} pathways)'] + render(M[n])
    if lines + len(t) > 2600 and batches[-1]: batches.append([]); lines = 0
    batches[-1].append('\n'.join(t)); lines += len(t)
for i, b in enumerate(batches, 1): open(f'{OUT}/read_inputs/R_b{i:02d}.md', 'w').write('\n\n---\n\n'.join(b) + '\n')
small = [n for n in order if len(M[n]) <= 50]
key = {}; items = []
for n in small:
    s = M[n]
    cands = [(len(s & M[c]) / len(s), len(M[c]), c) for c in M if c != n and len(M[c]) > len(s)]
    cands.sort(key=lambda x: (-x[0], x[1]))
    top = cands[:3]
    rng.shuffle(top)
    t = [f'## ITEM {rid[n]}', f'### Small theme ({len(s)} pathways)'] + render(s)
    key[rid[n]] = {'root': n, 'size': len(s), 'containers': {}}
    for L, (sh, sz, c) in zip('PQR', top):
        rest = sorted(M[c] - s)
        samp = rest if len(rest) <= 40 else rng.sample(rest, 40)
        t.append(f'### Larger theme {L} ({sz} pathways; sample of {len(samp)} members not in the small theme)')
        t += render(samp)
        key[rid[n]]['containers'][L] = {'node': c, 'size': sz, 'share': round(sh, 4), 'missing': len(s - M[c])}
    items.append('\n'.join(t))
sb = [[]]; lines = 0
for it in items:
    k = it.count('\n') + 1
    if lines + k > 2600 and sb[-1]: sb.append([]); lines = 0
    sb[-1].append(it); lines += k
for i, b in enumerate(sb, 1): open(f'{OUT}/small_inputs/S_b{i:02d}.md', 'w').write('\n\n'.join(b) + '\n')
json.dump({'rid': {v: k for k, v in rid.items()}, 'size': {rid[n]: len(M[n]) for n in order}}, open(OUT + '/roots_index.json', 'w'), indent=1)
json.dump(key, open(OUT + '/KEY_DO_NOT_SHARE_O50s_roots.json', 'w'), indent=1)
print('roots', len(roots), 'read batches', len(batches), 'small', len(small), 'small batches', len(sb))
print('size bands', collections.Counter('<=50' if len(M[n]) <= 50 else '51-200' if len(M[n]) <= 200 else '201-1000' if len(M[n]) <= 1000 else '>1000' for n in roots))
