import json,os,collections
HERE=os.path.dirname(os.path.abspath(__file__)); D=os.path.abspath(HERE+'/..')
K=json.load(open(D+'/KEY_DO_NOT_SHARE_giants.json')); J=json.load(open(D+'/G2_judgements.json'))
G1={x['giant']:x for x in json.load(open(D+'/G1_readings.json'))}; IDX=json.load(open(D+'/giants_index.json'))
hit=collections.Counter(); themes=collections.defaultdict(list)
for i,k in K.items():
    hit[k['gid']]+= J[i]['pick']==k['intruder']; themes[k['gid']].append(J[i].get('shared_theme',''))
rows=[]
for g in sorted(IDX):
    h=hit[g]; v='coherent wide theme' if h>=4 else 'partial' if h>=2 else 'grab bag'
    rows.append((g,IDX[g]['node'],IDX[g]['size'],IDX[g]['kind'],G1[g]['verdict'],G1[g]['label'],G1[g]['off_topic_share'],h,v))
    print(f"{g} {IDX[g]['node']} {IDX[g]['size']} {IDX[g]['kind']} | G1: {G1[g]['verdict']} — {G1[g]['label']} (off-topic {G1[g]['off_topic_share']}) | G2: {h}/5 {v}")
    print('     contents:',G1[g]['contents'][:260]); print('     unifying:',G1[g]['unifying_idea'][:160])
    print('     judges saw shared theme:',' / '.join(t[:50] for t in themes[g]))
print('total hits',sum(hit.values()),'/ 60')
with open(D+'/RESULT_giants.tsv','w') as f:
    f.write('gid\tnode\tsize\tkind\tG1_verdict\tG1_label\toff_topic\tG2_hits\tG2_verdict\n')
    for r in rows: f.write('\t'.join(map(str,r))+'\n')
