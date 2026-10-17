import json,os,collections
HERE=os.path.dirname(os.path.abspath(__file__)); D=os.path.abspath(HERE+'/..')
idx=json.load(open(D+'/review_index.json')); K=json.load(open(D+'/KEY_DO_NOT_SHARE_O50s_large.json'))
R={x['id']:x for x in json.load(open(D+'/R_readings.json'))}; J=json.load(open(D+'/I_judgements.json'))
st=idx['status']
ok={'coherent','linked umbrella'}
for s in ['new','kept']:
    ids=[g for g in st if st[g]==s]
    c=collections.Counter(R[g]['verdict'] for g in ids)
    good=sum(R[g]['verdict'] in ok for g in ids)
    print(f'R1 {s}: {good}/{len(ids)} = {good/len(ids):.1%} coherent or linked umbrella | {dict(c)}')
    it=[i for i in K if K[i]['status']==s]; hit=sum(J[i]['pick']==K[i]['intruder'] for i in it)
    print(f'R2 {s}: {hit}/{len(it)} = {hit/len(it):.1%}')
print('\nnew themes not passing R1:')
for g in sorted(st):
    if st[g]=='new' and R[g]['verdict'] not in ok: print(' ',g,idx['gid'][g],R[g]['verdict'],'|',R[g]['label'],'|',R[g]['off_topic'])
print('\nR2 misses (new):')
for i in sorted(K):
    if K[i]['status']=='new' and J[i]['pick']!=K[i]['intruder']: print(' ',i,K[i]['gid'],K[i]['size'],R[K[i]['gid']]['verdict'],'|',R[K[i]['gid']]['label'])
print('\nsample of new labels:')
for g in sorted(st)[:200]:
    if st[g]=='new': print(' ',g,R[g]['verdict'][:10],'|',R[g]['label'])
