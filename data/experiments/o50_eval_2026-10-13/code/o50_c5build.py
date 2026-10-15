import sys,os,csv,collections,json,random,numpy as np; sys.path.insert(0,'.')
exec(open(os.path.expanduser('~/np_build.py')).read().split("ok={k")[0])
P=ROOT+'data/experiments/o50_eval_2026-10-13/'
O=ROOT+'data/ontology/v0.4-leaves/thema_L_x2_O50/'
MO=collections.defaultdict(set)
for r in csv.DictReader(open(O+'members.tsv'),delimiter='\t'): MO[r['node']].add(r['key'])
def sets(MM,x): return sorted((k for k,s in MM.items() if x in s and len(s)<200),key=lambda k:(len(MM[k]),k))
ps=sorted(set().union(*M.values()))
pool=[x for x in ps if {frozenset(M[k]) for k in sets(M,x)}!={frozenset(MO[k]) for k in sets(MO,x)}]
S=random.Random(20261012).sample(pool,120)
items=[];key={}
for n,x in enumerate(S):
    iid=f'U{n:03d}'; sides=[('c85',M,sets(M,x)),('O50',MO,sets(MO,x))]
    sw=random.Random('sw'+x).random()<0.5
    if sw: sides=sides[::-1]
    def show(MM,ks): return [dict(size=len(MM[k]),members=[render(m) for m in sorted(MM[k]) if m!=x]) for k in ks]
    items.append(dict(item_id=iid,target=dict(name=render(x),description=first2(DESC.get(x,''))),A=show(sides[0][1],sides[0][2]),B=show(sides[1][1],sides[1][2])))
    key[iid]=dict(pathway=x,A=sides[0][0],B=sides[1][0],nA=len(sides[0][2]),nB=len(sides[1][2]))
lines=[sum(len(t['members']) for t in it['A']+it['B']) for it in items]
print('pool',len(pool),'| member lines per item median',np.median(lines),'p90',np.percentile(lines,90),'max',max(lines))
print('themes per side: c85 median',np.median([v['nA'] if v['A']=='c85' else v['nB'] for v in key.values()]),'O50 median',np.median([v['nA'] if v['A']=='O50' else v['nB'] for v in key.values()]))
B=6
for b in range(0,120,B): json.dump(items[b:b+B],open(P+f'c5/C5_{b//B+1:02d}.json','w'),indent=1)
json.dump(key,open(P+'c5/KEY_DO_NOT_SHARE.json','w'),indent=1)
