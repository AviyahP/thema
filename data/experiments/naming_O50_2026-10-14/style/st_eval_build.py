import sys, csv; sys.path.insert(0, '/home/claude/nm/sample')
from sm_common import *
OLD = {r['theme_id']: r['name'] for r in csv.DictReader(open('/home/claude/nm/dedup/final_names_O50_lite_unique.tsv'), delimiter='\t')}
DD = json.load(open('/home/claude/nm/dedup/inputs/dedup_groups.json'))['confusables_after_dedup']
NEW = {}
for f in sorted(glob.glob('inputs/style_b*.json')):
    inp = [t['theme_id'] for t in json.load(open(f))]
    out = json.load(open(f.replace('inputs/', 'raw/').replace('.json', '.out.json')))
    assert [o['theme_id'] for o in out] == inp, f
    for o in out:
        assert o.get('name'), o['theme_id']; NEW[o['theme_id']] = o
assert set(NEW) == set(SAMPLE)
e1 = []; k1 = {}; e2 = []; k2 = {}; p1 = []; kp = {}
for t in SAMPLE:
    cfs = DD.get(t, CF[t])
    for arm, name in [('OLD', OLD[t]), ('NEW', NEW[t]['name'])]:
        cl = [t] + cfs; r = random.Random(seed(f'{t}:E{arm}')); r.shuffle(cl)
        common = M[cl[0]]
        for c in cl[1:]: common = common & M[c]
        L = 'ABCDE'[:len(cl)]
        iid = f'X{len(e1):04d}'
        e1.append(dict(item_id=iid, name=name, in_all=expand(common), also_in={l: expand(M[c] - common) for l, c in zip(L, cl)}))
        k1[iid] = dict(theme=t, arm=arm, correct=L[cl.index(t)])
        mem = expand(M[t]); r.shuffle(mem)
        jid = f'Y{len(e2):04d}'; e2.append(dict(item_id=jid, name=name, members=mem)); k2[jid] = dict(theme=t, arm=arm, size=len(mem))
rp = random.Random(20261016)
for i, t in enumerate(SAMPLE):
    pair = [('OLD', OLD[t]), ('NEW', NEW[t]['name'])]; rp.shuffle(pair)
    mem = expand(M[t]); random.Random(seed(f'{t}:P')).shuffle(mem)
    iid = f'P{i:03d}'; p1.append(dict(item_id=iid, members=mem, A=pair[0][1], B=pair[1][1])); kp[iid] = dict(theme=t, A=pair[0][0], B=pair[1][0])
random.Random(11).shuffle(e1); random.Random(12).shuffle(e2); random.Random(13).shuffle(p1)
os.makedirs('eval', exist_ok=True); os.makedirs('evalout', exist_ok=True)
for b in range(0, 400, 50):
    json.dump(e1[b:b+50], open(f'eval/E1_{b//50+1:02d}.json', 'w'), indent=1)
    json.dump(e2[b:b+50], open(f'eval/E2_{b//50+1:02d}.json', 'w'), indent=1)
for b in range(0, 200, 50): json.dump(p1[b:b+50], open(f'eval/P1_{b//50+1:02d}.json', 'w'), indent=1)
json.dump(dict(E1=k1, E2=k2, P1=kp), open('eval/KEY_DO_NOT_SHARE_style.json', 'w'))
hs = random.Random(20261017).sample(SAMPLE, 30)
json.dump(dict(new=NEW, h1_themes=hs), open('new_names.json', 'w'), indent=1)
w = [len(NEW[t]['name'].split()) for t in SAMPLE]; wo = [len(OLD[t].split()) for t in SAMPLE]
import statistics
print('median words new', statistics.median(w), 'old', statistics.median(wo), 'unifying=false', sum(not NEW[t].get('unifying', True) for t in SAMPLE))
lst = lambda h: (',' in h) or len(re.findall(r'\band\b', h)) >= 2
print('list-style head new', sum(lst(NEW[t]['head']) for t in SAMPLE), 'old list-style name', sum(lst(OLD[t]) for t in SAMPLE))
for t in SAMPLE[:12]: print(' ', OLD[t], ' ==> ', NEW[t]['name'])
