import sys; sys.path.insert(0, '/home/claude/nm/sample')
from sm_common import *
F = json.load(open('final_names_dedup1.json'))['names']
G0 = json.load(open('inputs/dedup_groups.json'))['confusables_after_dedup']
grp = ['n00337', 'n00666']
SC = {}
for ci in [0, 1, 2]:
    items = []
    for t in grp:
        other = [o for o in grp if o != t]
        base = G0.get(t, CF[t])
        cf = (other + [c for c in base if c not in other])[:4]
        r = random.Random(seed(f'{t}:{ci+30}'))
        mem = expand(M[t]); r.shuffle(mem)
        cl = [dict(confusable=f'C{j+1}', n_shared=sum((M[t] & M[c]).values()), only_in_theme=expand(M[t] - M[c]),
                   only_in_confusable=expand(M[c] - M[t])) for j, c in enumerate(cf)]
        items.append(dict(theme_id=t, size=sum(M[t].values()), members=mem, confusables=cl,
                          note=f"The name '{F[t]['name']}' is already used by another theme; give a name that distinguishes this theme."))
        SC[t] = cf
    json.dump(items, open(f'inputs/dedup2_slot{ci}_b01.json', 'w'), indent=1)
json.dump(dict(groups=[grp], confusables_after_dedup2=SC), open('inputs/dedup2_groups.json', 'w'), indent=1)
print('ok')
