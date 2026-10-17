import json, collections, os
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.abspath(HERE + '/..')
S = {o['id']: o for o in json.load(open(OUT + '/S_judgements.json'))}
K = json.load(open(OUT + '/KEY_DO_NOT_SHARE_O50s_roots.json'))
n = len(S); dist = [k for k, o in S.items() if o['verdict'] == 'distinct']
print('small roots', n, 'distinct', len(dist), round(100 * len(dist) / n, 1))
print('confidence', collections.Counter((o['verdict'] == 'distinct', o['confidence']) for o in S.values()))
rows = []
for k, o in S.items():
    v = o['verdict']
    if v in 'PQR' and v in K[k]['containers']:
        c = K[k]['containers'][v]; best = max(K[k]['containers'].values(), key=lambda x: x['share'])
        rows.append((k, K[k]['size'], c['size'], c['share'], c['missing'], c['node'] == best['node'], o['confidence']))
print('placed under a container', len(rows))
def b(m): return '0' if m == 0 else '1-5' if m <= 5 else '6-20' if m <= 20 else '21+'
print('missing pathways for chosen container', collections.Counter(b(r[4]) for r in rows))
print('chosen container is the highest-share one', sum(r[5] for r in rows), 'of', len(rows))
print('chosen container size', collections.Counter('>1000' if r[2] > 1000 else '201-1000' if r[2] > 200 else '<=200' for r in rows))
print('share of chosen', collections.Counter('>=0.98' if r[3] >= 0.98 else '0.9-0.98' if r[3] >= 0.9 else '0.8-0.9' if r[3] >= 0.8 else '<0.8' for r in rows))
dshare = [max(x['share'] for x in K[k]['containers'].values()) for k in dist]
print('distinct roots: best container share', collections.Counter('>=0.98' if s >= 0.98 else '0.9-0.98' if s >= 0.9 else '0.8-0.9' if s >= 0.8 else '<0.8' for s in dshare))
json.dump({'n': n, 'distinct': len(dist), 'placed': len(rows)}, open(OUT + '/S_summary.json', 'w'))
