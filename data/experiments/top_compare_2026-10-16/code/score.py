import json,os,collections,math
HERE=os.path.dirname(os.path.abspath(__file__)); D=os.path.abspath(HERE+'/..')
K=json.load(open(D+'/KEY_DO_NOT_SHARE_topcompare.json')); J=json.load(open(D+'/judgements.json'))
print('TEST A')
wins=collections.Counter(); sc=collections.defaultdict(lambda:collections.defaultdict(list))
for j in [k for k in J if k.startswith('A_')]:
    r=J[j]; wins[K['A'][r['better']]]+=1
    for m in 'AB':
        for c,v in r[m].items(): sc[K['A'][m]][c].append(v)
    print(' ',j,'->',K['A'][r['better']],'|',r['reason'][:200])
print(' wins',dict(wins))
for o in sc: print(' ',o,{c:round(sum(v)/len(v),1) for c,v in sc[o].items()})
print('TEST B')
maj=collections.Counter(); per=collections.Counter()
for i in sorted(k for k in K if k.startswith('P')):
    votes=collections.Counter()
    for j in ['B_j1','B_j2','B_j3']:
        p=J[j][i]['pick']; v='tie' if p=='tie' else K[i][p]; votes[v]+=1; per[v]+=1
    top=votes.most_common(1)[0]; m=top[0] if top[1]>=2 else 'tie'
    maj[m]+=1
print(' item majorities',dict(maj),' all votes',dict(per))
w,l=maj['option2'],maj['option1']; n=w+l
p=sum(math.comb(n,k) for k in range(0,min(w,l)+1))/2**n*2 if n else 1
print(f' sign test: option2 {w} vs option1 {l}, two-sided p = {min(p,1):.4f}')
