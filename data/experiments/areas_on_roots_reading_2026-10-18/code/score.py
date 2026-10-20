import csv, json, collections, os
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.abspath(HERE + '/..'); T = os.path.abspath(HERE + '/../../../..')
csv.field_size_limit(10**9)
def tsv(p): return list(csv.DictReader(open(p), delimiter='\t'))
key = json.load(open(OUT + '/KEY_DO_NOT_SHARE_areas_reading.json'))['aid']
R = {key[o['id']]: o for o in json.load(open(OUT + '/A_readings.json'))}
A = {r['node']: r for r in tsv(T + '/data/experiments/areas_on_roots_2026-10-18/areas.tsv')}
M = {n: set(r['members'].split()) for n, r in A.items()}
E = tsv(T + '/data/ontology/v0.4-leaves/thema_L_x2_O50s_roots_areas/edges.tsv')
kids = collections.defaultdict(list)
for e in E:
    if e['child'] in A and e['parent'] in A: kids[e['parent']].append(e['child'])
good = {'coherent', 'broad_domain', 'linked_umbrella'}
print('verdicts', collections.Counter(o['verdict'] for o in R.values()))
ok = sum(R[n]['verdict'] in good for n in A); print('all areas pass', ok, len(A))
def band(s): return '51-200' if s <= 200 else '201-500' if s <= 500 else '501-1000' if s <= 1000 else '>1000'
by = collections.defaultdict(lambda: [0, 0])
for n in A: b = band(len(M[n])); by[b][1] += 1; by[b][0] += R[n]['verdict'] in good
print('by size', dict(by))
roots = [n for n in A if A[n]['root'] == 'true']
print('roots pass', sum(R[n]['verdict'] in good for n in roots), len(roots))
for n in sorted(roots, key=lambda n: -len(M[n])):
    o = R[n]; print(f"ROOT {n} {len(M[n])} {o['verdict']} | {o['label']}")
    if o['verdict'] not in good or len(M[n]) > 1000:
        ks = kids[n]; cov = set()
        for k in sorted(ks, key=lambda k: -len(M[k])):
            ok2 = R[k]['verdict'] in good
            if ok2: cov |= M[k]
            print(f"    child {k} {len(M[k])} {R[k]['verdict']} | {R[k]['label']}")
        print(f"    child areas {len(ks)}, passing {sum(R[k]['verdict'] in good for k in ks)}, cover {round(100*len(cov & M[n])/len(M[n]),1)}% of root")
for n in sorted(A, key=lambda n: -len(M[n])):
    if A[n]['root'] != 'true': print(f"AREA {n} {len(M[n])} {R[n]['verdict']} | {R[n]['label']}")
