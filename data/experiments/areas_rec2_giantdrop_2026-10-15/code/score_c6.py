import json,os,csv,collections
HERE=os.path.dirname(os.path.abspath(__file__)); D=os.path.abspath(HERE+'/..')
K=json.load(open(D+'/KEY_DO_NOT_SHARE_C6.json')); J=json.load(open(D+'/C6_judgements.json'))
roots={r['node'] for r in csv.DictReader(open(D+'/roots.tsv'),delimiter='\t')}
hit={i:J[i]['pick']==K[i]['intruder'] for i in K}
n=len(hit); h=sum(hit.values())
print(f'overall {h}/{n} = {h/n:.1%}  (pass >= 70%)')
def band(s,cuts,lab):
    for c,l in zip(cuts,lab):
        if s<=c: return l
    return lab[-1]
for name,fn in [('size',lambda k:band(k['size'],[50,100,200,500,1000],['<=50','51-100','101-200','201-500','501-1000'])),('support',lambda k:band(k['support'],[0.15,0.4,0.7,1.0],['<=0.15','0.15-0.4','0.4-0.7','0.7-1.0']))]:
    c=collections.defaultdict(lambda:[0,0])
    for i,k in K.items(): b=fn(k); c[b][0]+=hit[i]; c[b][1]+=1
    print(name, {b:f'{x}/{y}={x/y:.0%}' for b,(x,y) in sorted(c.items())})
r=[i for i in K if K[i]['area'] in roots]; print('top roots', sum(hit[i] for i in r),'/',len(r))
conf=collections.defaultdict(lambda:[0,0])
for i in K: conf[J[i]['confidence']][0]+=hit[i]; conf[J[i]['confidence']][1]+=1
print('by confidence',dict(conf))
miss=[(i,K[i]['area'],K[i]['size'],K[i]['support'],J[i]['pick'],K[i]['intruder'],J[i]['reason']) for i in sorted(K) if not hit[i]]
with open(D+'/C6_misses.tsv','w') as f:
    f.write('item\tarea\tsize\tsupport\tpick\tintruder\treason\n')
    for m in miss: f.write('\t'.join(map(str,m))+'\n')
print('misses',len(miss))
for m in miss[:12]: print(m[:6], m[6][:110])
