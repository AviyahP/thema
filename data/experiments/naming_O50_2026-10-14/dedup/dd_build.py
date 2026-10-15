import sys; sys.path.insert(0, '/home/claude/nm/sample')
from sm_common import *
L = json.load(open('/home/claude/nm/select_lite/final_names_lite.json'))
names, dups = L['names'], L['duplicates']
SC = {t: list(v) for t, v in CF.items()}
groups = [sorted(v) for k, v in sorted(dups.items())]
order = [t for g in groups for t in g]
os.makedirs('inputs', exist_ok=True)
for ci in [0, 1, 2]:
    items = []
    for g in groups:
        for t in g:
            other = [o for o in g if o != t]
            cf = (other + [c for c in CF[t] if c not in other])[:4]
            r = random.Random(seed(f'{t}:{ci+20}'))
            mem = expand(M[t]); r.shuffle(mem)
            cl = [dict(confusable=f'C{j+1}', n_shared=sum((M[t] & M[c]).values()), only_in_theme=expand(M[t] - M[c]),
                       only_in_confusable=expand(M[c] - M[t])) for j, c in enumerate(cf)]
            items.append(dict(theme_id=t, size=sum(M[t].values()), members=mem, confusables=cl,
                              note=f"The name '{names[t]['name']}' is already used by another theme; give a name that distinguishes this theme."))
            SC[t] = cf
    for b in range(0, len(items), 25):
        json.dump(items[b:b+25], open(f'inputs/dedup_slot{ci}_b{b//25+1:02d}.json', 'w'), indent=1)
json.dump(dict(groups=groups, confusables_after_dedup={t: SC[t] for t in order}), open('inputs/dedup_groups.json', 'w'), indent=1)
print('groups', len(groups), 'themes', len(order), 'files per slot', (len(order)+24)//25)
