import csv,collections,os
HERE=os.path.dirname(os.path.abspath(__file__)); T=os.path.abspath(HERE+'/../../../..')
F=T+'/data/ontology/frozen/working-O50-2026-10-14/'
def tsv(p): return list(csv.DictReader(open(p),delimiter='\t'))
om=collections.defaultdict(set)
for r in tsv(F+'members.tsv'): om[r['node']].add(r['key'])
on={r['node']:r for r in tsv(F+'nodes.tsv')}
par={n:set(on[n]['parents'].split()) for n in on}
anc={}
def A(n):
    if n in anc: return anc[n]
    s=set()
    for p in par[n]: s|={p}|A(p)
    anc[n]=s; return s
ng=[n for n in on if len(om[n])<=1000]
idx=collections.defaultdict(set)
for n in ng:
    for k in om[n]: idx[k].add(n)
c=collections.Counter(); ex=[]
for n in ng:
    best=(0,None)
    cnt=collections.Counter(m for k in om[n] for m in idx[k] if m!=n and len(om[m])>len(om[n]))
    for m,i in cnt.items():
        s=i/len(om[n])
        if s>=0.8 and m not in A(n): 
            if s>best[0]: best=(s,m)
    if best[1]:
        c['>=80% inside a larger theme that is NOT its ancestor']+=1
        if s<1: pass
        ex.append((round(best[0],2),n,len(om[n]),best[1],len(om[best[1]])))
print(len(ng),'non-giant themes;',dict(c))
print('of which root themes:',sum(1 for e in ex if not (par[e[1]]-{x for x in on if len(om[x])>1000})))
ex.sort(reverse=True); print(ex[:5])
