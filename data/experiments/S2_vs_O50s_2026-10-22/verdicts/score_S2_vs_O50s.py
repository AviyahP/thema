import json, math, sys, collections
D = sys.argv[1]
K = json.load(open(D + '/KEY_DO_NOT_SHARE_S2_vs_O50s.json'))
V = json.load(open(D + '/verdicts/verdicts_S2_vs_O50s.json'))
assert set(K) == set(V), 'id mismatch'
GOOD = {'coherent', 'linked_umbrella'}

def wilson(k, n, z=1.96):
    if n == 0: return (float('nan'),) * 2
    p = k / n; d = 1 + z*z/n; c = (p + z*z/(2*n)) / d
    h = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return c - h, c + h

def diff(k1, n1, k2, n2):
    p1, p2 = k1/n1, k2/n2
    l1, u1 = wilson(k1, n1); l2, u2 = wilson(k2, n2)
    d = p1 - p2
    lo = d - math.sqrt((p1-l1)**2 + (u2-p2)**2)
    hi = d + math.sqrt((u1-p1)**2 + (p2-l2)**2)
    return d, lo, hi

def row(name, cnt):
    a = cnt.get('S2', [0, 0]); b = cnt.get('O50s', [0, 0])
    s = f'| {name} | {a[0]}/{a[1]} = {100*a[0]/a[1]:.1f}% | {b[0]}/{b[1]} = {100*b[0]/b[1]:.1f}% |' if a[1] and b[1] else f'| {name} | {a} | {b} |'
    if a[1] and b[1]:
        d, lo, hi = diff(a[0], a[1], b[0], b[1])
        s += f' {100*d:+.1f} [{100*lo:+.1f}, {100*hi:+.1f}] |'
    print(s)

def rbin(n):
    return '<=50' if n <= 50 else '51-200' if n <= 200 else '201-1,280' if n <= 1280 else '>1,280'
def tband(n):
    return '12-24' if n <= 24 else '25-49' if n <= 49 else '50-99' if n <= 99 else '100-199'

out = {}
print('## R: roots that differ (coherent or linked umbrella)\n')
print('| group | S2 | O50s | S2 - O50s, pts [95% CI] |\n|---|---|---|---|')
tot = collections.defaultdict(lambda: [0, 0]); by = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
cls = collections.defaultdict(collections.Counter)
for i, k in K.items():
    if k['kind'] != 'R': continue
    g = V[i]['class'] in GOOD; b = k['build']
    tot[b][0] += g; tot[b][1] += 1
    by[rbin(k['size'])][b][0] += g; by[rbin(k['size'])][b][1] += 1
    cls[b][V[i]['class']] += 1
row('all', tot)
for s in ['<=50', '51-200', '201-1,280', '>1,280']: row(s, by[s])
print('\nclasses:', {b: dict(c) for b, c in cls.items()})

print('\n## T: middle themes that differ (coherent or linked umbrella)\n')
print('| band | S2 | O50s | S2 - O50s, pts [95% CI] |\n|---|---|---|---|')
tot = collections.defaultdict(lambda: [0, 0]); by = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
cls = collections.defaultdict(collections.Counter)
for i, k in K.items():
    if k['kind'] != 'T': continue
    g = V[i]['class'] in GOOD; b = k['build']
    tot[b][0] += g; tot[b][1] += 1
    by[tband(k['size'])][b][0] += g; by[tband(k['size'])][b][1] += 1
    cls[b][V[i]['class']] += 1
row('all', tot)
for s in ['12-24', '25-49', '50-99', '100-199']: row(s, by[s])
print('\nclasses:', {b: dict(c) for b, c in cls.items()})
print('coherent only:', {b: f"{c['coherent']}/{sum(c.values())}" for b, c in cls.items()})

print('\n## I: intruder test (share correct)\n')
print('| band | S2 | O50s | S2 - O50s, pts [95% CI] |\n|---|---|---|---|')
tot = collections.defaultdict(lambda: [0, 0]); by = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
for i, k in K.items():
    if k['kind'] != 'I': continue
    g = V[i]['pick'] == k['intruder']; b = k['build']
    tot[b][0] += g; tot[b][1] += 1
    by[tband(k['size'])][b][0] += g; by[tband(k['size'])][b][1] += 1
row('all', tot)
for s in ['12-24', '25-49', '50-99', '100-199']: row(s, by[s])

print('\n## S: S2 small roots (<=50)\n')
n = 0; dist = 0; conf = collections.Counter(); top = 0; picks = 0; chs = collections.Counter(); miss = collections.Counter(); bestd = collections.Counter()
for i, k in K.items():
    if k['kind'] != 'S': continue
    n += 1; v = V[i]; c = k['containers']
    best = max(c.values(), key=lambda x: x['share'])['share']
    if v['verdict'] == 'distinct':
        dist += 1; conf[v['confidence']] += 1
        bestd['0.9-0.98' if best >= 0.9 else '0.8-0.9' if best >= 0.8 else '<0.8'] += 1
    else:
        picks += 1; ch = c[v['verdict']]
        top += ch['share'] == best
        chs['>=0.9' if ch['share'] >= 0.9 else '0.8-0.9' if ch['share'] >= 0.8 else '<0.8'] += 1
        m = ch['missing']; miss['0' if m == 0 else '1-5' if m <= 5 else '6-20' if m <= 20 else '21+'] += 1
lo, hi = wilson(dist, n)
print(f'distinct: {dist}/{n} = {100*dist/n:.1f}% [{100*lo:.1f}, {100*hi:.1f}]; O50s (18 Oct): 67/164 = 40.9%')
d, lo, hi = diff(dist, n, 67, 164)
print(f'S2 - O50s: {100*d:+.1f} pts [{100*lo:+.1f}, {100*hi:+.1f}]')
print('distinct confidence:', dict(conf), '; best share of distinct ones:', dict(bestd))
print(f'belongs under a container: {picks}; picked the highest-share container: {top}')
print('share of chosen container:', dict(chs), '; missing from chosen:', dict(miss))
