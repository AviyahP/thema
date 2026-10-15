import json, glob, hashlib, random, collections, os, re
NM = '/home/claude/nm/'
S = NM + 'sample/'
STOP = {'a','an','the','of','and','in','to','by','for','via','with','on','from','at'}
def seed(s): return int(hashlib.sha256(s.encode()).hexdigest()[:8], 16)
def toks(s): return {w for w in re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", s.lower()) if w not in STOP}
def jac(a, b): return len(a & b) / len(a | b) if a | b else 1.0
def norm(s): return ' '.join(re.sub(r'[^a-z0-9 ]', ' ', s.lower()).split())
M = {}
for f in sorted(glob.glob(NM + 'inputs/namer_slot0_b*.json')):
    for t in json.load(open(f)): M[t['theme_id']] = collections.Counter(t['members'])
TC = json.load(open(NM + 'inputs/themes_and_confusables.json'))
CF = TC['confusables']
C = collections.defaultdict(dict)
for f in glob.glob(NM + 'raw/namer_slot*_b*.out.json'):
    s = int(f.split('_slot')[1][0])
    for o in json.load(open(f)): C[o['theme_id']][s] = o
SAMPLE = random.Random(20261015).sample(sorted(TC['themes']), 200)
def expand(cnt): return sorted(cnt.elements())
def clusters_item(t, name, seedtag, iid):
    cl = [t] + CF[t]; r = random.Random(seed(f'{t}:{seedtag}')); r.shuffle(cl)
    common = M[cl[0]]
    for c in cl[1:]: common = common & M[c]
    L = 'ABCDE'[:len(cl)]
    item = dict(item_id=iid, name=name, in_all=expand(common),
                also_in={l: expand(M[c] - common) for l, c in zip(L, cl)})
    return item, L[cl.index(t)], r
