import csv, collections, os, json, random
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.abspath(HERE + '/..'); T = os.path.abspath(HERE + '/../../../..')
csv.field_size_limit(10**9)
def tsv(p): return list(csv.DictReader(open(p), delimiter='\t'))
pname = {r['source'] + ':' + r['source_id']: (r['name'], r['source']) for r in tsv(T + '/data/pathways.tsv')}
A = {r['node']: set(r['members'].split()) for r in tsv(T + '/data/experiments/areas_on_roots_2026-10-18/areas.tsv')}
rng = random.Random(20261018)
order = sorted(A); rng.shuffle(order)
aid = {n: f'A{i:02d}' for i, n in enumerate(order, 1)}
def render(keys): return [f'- {pname[k][0]} [{pname[k][1]}]' for k in sorted(keys, key=lambda k: pname[k][0].lower())]
os.makedirs(OUT + '/read_inputs', exist_ok=True)
batches = [[]]; lines = 0
for n in order:
    t = [f'# {aid[n]} ({len(A[n])} pathways)'] + render(A[n])
    if lines + len(t) > 2600 and batches[-1]: batches.append([]); lines = 0
    batches[-1].append('\n'.join(t)); lines += len(t)
for i, b in enumerate(batches, 1): open(f'{OUT}/read_inputs/A_b{i:02d}.md', 'w').write('\n\n---\n\n'.join(b) + '\n')
json.dump({'aid': {v: k for k, v in aid.items()}}, open(OUT + '/KEY_DO_NOT_SHARE_areas_reading.json', 'w'), indent=1)
print('areas', len(A), 'batches', len(batches), [b.count if False else len(x) for x in batches])
