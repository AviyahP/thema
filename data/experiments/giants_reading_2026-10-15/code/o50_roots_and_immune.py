import csv,collections,os,statistics as st
HERE=os.path.dirname(os.path.abspath(__file__)); T=os.path.abspath(HERE+'/../../../..')
F=T+'/data/ontology/frozen/working-O50-2026-10-14/'
def tsv(p): return list(csv.DictReader(open(p),delimiter='\t'))
om=collections.defaultdict(set)
for r in tsv(F+'members.tsv'): om[r['node']].add(r['key'])
on={r['node']:r for r in tsv(F+'nodes.tsv')}
giants=sorted([n for n in om if len(om[n])>1000],key=lambda n:-len(om[n]))
roots=[n for n in on if not on[n]['parents'].split()]
small=[n for n in roots if n not in giants]
cov=set().union(*[om[g] for g in giants])
print('O50 roots',len(roots),'small',len(small),'| pathways in no giant',len(set().union(*om.values())-cov))
b=collections.Counter()
for n in small:
    s=om[n]; best=max((len(s&om[g])/len(s),g) for g in giants); m=len(s-om[best[1]])
    if m==0: k='inside a giant (100%)'
    elif best[0]>=.98 and m<=5: k='attach by your rule (>=98%, <=5)'
    elif s<=cov: k='straddles giants (inside their union)'
    else: k='has pathways in no giant'
    b[k]+=1
print(dict(b))
sz=[len(om[n]) for n in small]; print('small root sizes median',st.median(sz),'max',max(sz))
