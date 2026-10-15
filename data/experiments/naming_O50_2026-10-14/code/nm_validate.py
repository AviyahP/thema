import json, glob, os, sys
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bad = []
n = 0
unn = {0: 0, 1: 0, 2: 0}
for f in sorted(glob.glob(os.path.join(BASE, 'raw', 'namer_slot*.out.json'))):
    base = os.path.basename(f).replace('.out.json', '.json')
    inp = json.load(open(os.path.join(BASE, 'inputs', base)))
    try:
        out = json.load(open(f))
    except Exception as e:
        bad.append((base, 'json ' + str(e))); continue
    ids_in = [t['theme_id'] for t in inp]
    ids_out = [o.get('theme_id') for o in out]
    if ids_in != ids_out:
        bad.append((base, 'ids mismatch')); continue
    for o in out:
        if not isinstance(o.get('nameable'), bool):
            bad.append((base, 'nameable ' + str(o.get('theme_id')))); break
        if o['nameable'] and not (isinstance(o.get('name'), str) and o['name'].strip()):
            bad.append((base, 'empty name ' + o['theme_id'])); break
        if not o['nameable']:
            unn[int(base.split('slot')[1][0])] += 1
    n += 1
print('files ok', n - 0, 'bad', bad)
print('unnameable by slot', unn)
