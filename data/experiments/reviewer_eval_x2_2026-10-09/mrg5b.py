import sys,json,collections,random,numpy as np,csv,glob; sys.path.insert(0,'.')
from tf_common import *
NM={r['node']:r['name'] for r in csv.DictReader(open(EV+'names_test/theme_names_c85.tsv'),delimiter='\t')}
G=[set(g) for g in json.load(open('/tmp/mrg5_0.5_complete.json'))]
gid={x:i for i,g in enumerate(G) for x in g}
keep={i:max(g,key=lambda k:(sup[k],len(M[k]))) for i,g in enumerate(G)}
U={i:set().union(*[M[k] for k in g]) for i,g in enumerate(G)}
gr=[len(U[i])/len(M[keep[i]]) for i in U]
print('union size / kept size: median %.2f, 90th %.2f, max %.2f'%(np.median(gr),np.percentile(gr,90),max(gr)))
shared_par=[set.intersection(*[par[k] for k in g]) for g in G]
allpar=[set.union(*[par[k] for k in g]) for g in G]
viol=[[p for p in allpar[i] if not U[i]<=M[p]] for i in range(len(G))]
print('groups with a parent that does not contain the union:',sum(1 for v in viol if v),'of',len(G),'; parent links dropped:',sum(map(len,viol)))
ch=[sum(len(par[k]) for k in g) for g in G]
nch=sum(1 for p in N for c in chl[p])
cc=sum(1 for i in range(len(G)) for p in shared_par[i] if J(U[i],M[p])>=0.85)
print('union theme would itself be within J>=0.85 of a shared parent (chain-collapse candidate):',cc)
lost=sum(len(M[k]-M[keep[i]]) for i,g in enumerate(G) for k in g if k!=keep[i])
pw=set(x for i,g in enumerate(G) for k in g if k!=keep[i] for x in M[k]-M[keep[i]])
print('KEEP-ONE variant: pathway-theme memberships lost',lost,'distinct pathways affected',len(pw))
dropped={k for i,g in enumerate(G) for k in g if k!=keep[i]}
orphan=sum(1 for k in dropped for c in chl[k] if not M[c]<=M[keep[gid[k]]])
print('  children of dropped themes not nested in the kept theme (must re-attach higher):',orphan)
nc_before=collections.Counter()
for p in N: nc_before[p]=len([c for c in chl[p]])
def newkids(p):
    s=set()
    for c in chl[p]: s.add(('g',gid[c]) if c in gid else c)
    return len(s)
inner=[p for p in N if len(chl[p])>=2]
b=np.array([len(chl[p]) for p in inner]); a=np.array([newkids(p) for p in inner])
print('parents with >=2 children:',len(inner),'children per parent median before %.0f after %.0f; mean %.1f -> %.1f; parents left with 1 child: %d'%(np.median(b),np.median(a),b.mean(),a.mean(),(a==1).sum()))
print('themes per giant bucket removed:')
for bk in sorted(big,key=lambda k:-len(M[k])):
    inside=[k for k in N if k not in big and M[k]<=M[bk]]; r=sum(1 for k in inside if k in dropped)
    print(f'  {NM.get(bk,bk)[:55]:<55} {len(inside):5d} themes, {100*r/max(1,len(inside)):.0f}% removed')
# whole-reading HIGH pairs
W=ROOT+'data/experiments/whole_reading_2026-10-11/'; K=json.load(open(W+'inputs/KEY_DO_NOT_SHARE.json')); CK=json.load(open(W+'compare/KEY_DO_NOT_SHARE.json'))
V={}
for f in glob.glob(W+'compare/W2_*.out.json'):
    for o in json.load(open(f)): V[CK[o['item_id']]['pair']]=o['verdict']
for lo,hi in ((0.4,0.5),(0.5,0.6),(0.6,1)):
    ps=[p for p,v in K['pairs'].items() if v['set']=='HIGH' and lo<=v['J']<hi]
    print(f'whole-reading HIGH J {lo}-{hi}: n {len(ps)}, shared pathways used differently {100*np.mean([V[p]!="same" for p in ps]):.0f}%')
random.seed(11)
print('\nexamples (kept name first):')
for i in random.sample(range(len(G)),8)+[max(range(len(G)),key=lambda i:len(G[i]))]:
    g=G[i]; print(' -',' || '.join([NM.get(keep[i],'?')]+[NM.get(k,'?') for k in g if k!=keep[i]]), f'| sizes {[len(M[k]) for k in g]} union {len(U[i])}')
S=[set(g) for g in json.load(open('/tmp/mrg5_0.5_single.json'))]; big1=max(S,key=len)
print('\nlargest SINGLE-linkage chain (%d themes), sample names:'%len(big1)); [print('   ',NM.get(k,'?')) for k in random.sample(sorted(big1),10)]
