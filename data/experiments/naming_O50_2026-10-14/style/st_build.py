import sys, csv; sys.path.insert(0, '/home/claude/nm/sample')
from sm_common import *
OLD = {r['theme_id']: r for r in csv.DictReader(open('/home/claude/nm/dedup/final_names_O50_lite_unique.tsv'), delimiter='\t')}
DD = json.load(open('/home/claude/nm/dedup/inputs/dedup_groups.json'))['confusables_after_dedup']
FD = json.load(open('/home/claude/nm/dedup/final_names_O50_lite_unique.json'))['names']
items = []
for t in SAMPLE:
    assert OLD[t]['unnameable'] == 'False'
    cfs = DD.get(t, CF[t])
    r = random.Random(seed(f'{t}:40'))
    mem = expand(M[t]); r.shuffle(mem)
    cf = list(cfs); r.shuffle(cf)
    cl = [dict(confusable=f'C{j+1}', n_shared=sum((M[t] & M[c]).values()), only_in_theme=expand(M[t] - M[c]),
               only_in_confusable=expand(M[c] - M[t])) for j, c in enumerate(cf)]
    cands = FD[t].get('candidates') or [C[t][s]['name'] for s in sorted(C[t])]
    items.append(dict(theme_id=t, size=sum(M[t].values()), current_name=OLD[t]['name'], candidate_names=cands, members=mem, confusables=cl))
os.makedirs('inputs', exist_ok=True); os.makedirs('raw', exist_ok=True)
for b in range(0, len(items), 25):
    json.dump(items[b:b+25], open(f'inputs/style_b{b//25+1:02d}.json', 'w'), indent=1)
print(len(items), 'themes', (len(items)+24)//25, 'files')
