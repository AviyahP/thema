import sys,os,csv,collections,json; sys.path.insert(0,'.')
exec(open(os.path.expanduser('~/np_build.py')).read().split("ok={k")[0])
x='btm:M205'
print('TITLE:',TITLE.get(x)); print('DESC:',DESC.get(x,'')[:700]); print('render:',render(x))
for k in ('n04672','n05438','n06033'):
    print(f'\n{k} size {len(M[k])} support {sup[k]}:'); print('  ', ' | '.join(render(m) for m in sorted(M[k]) if m!=x))
O=ROOT+'data/ontology/v0.4-leaves/thema_L_x2_O50/'
MO=collections.defaultdict(set)
for r in csv.DictReader(open(O+'members.tsv'),delimiter='\t'): MO[r['node']].add(r['key'])
rm=json.load(open(O+'repair_map.json'))
print('\nO50 themes containing it:',[(k,len(s)) for k,s in MO.items() if x in s])
print('repair_map keys:',list(rm)[:5] if isinstance(rm,dict) else type(rm))
for k in ('n04672','n05438','n06033'):
    best=max(MO,key=lambda o:J(M[k],MO[o])); print(k,'-> best O50',best,len(MO[best]),'J %.2f'%J(M[k],MO[best]), 'contains M205:',x in MO[best])
sz=[len(s) for s in json.load(open(O+'O50_new_themes.json')).values()] if isinstance(json.load(open(O+'O50_new_themes.json')),dict) else None
