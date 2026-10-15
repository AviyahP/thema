import sys,json,collections,itertools; sys.path.insert(0,'.')
from tf_common import *
kids=collections.defaultdict(set)
for k in N:
    for p in par[k]: kids[p].add(k)
ok={k for k,s in M.items() if 3<=len(s)<=200}
pairs={}
for p,ch in kids.items():
    ch=[c for c in ch if c in ok]
    for a,b in itertools.combinations(sorted(ch),2):
        A,B=M[a],M[b]
        if A<=B or B<=A: continue
        c=len(A&B)
        if c<3: continue
        j=c/len(A|B)
        if 0.1<=j<0.4: pairs[(a,b)]=j
cnt=collections.Counter(int(j*10) for j in pairs.values())
print('sibling pairs with core>=3 by J band:',sorted(cnt.items()))
json.dump([[a,b,j] for (a,b),j in pairs.items()],open('/tmp/lo_pairs.json','w'))
