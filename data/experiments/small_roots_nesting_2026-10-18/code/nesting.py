import csv, collections, json, os, sys, time
import numpy as np
from scipy.cluster.hierarchy import linkage
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.abspath(HERE + '/..'); T = os.path.abspath(HERE + '/../../../..')
csv.field_size_limit(10**9)
X2 = T + '/data/ontology/v0.4-leaves-x2/'
keys = [l.strip() for l in open(X2 + 'embedding_keys.txt') if l.strip()]
V = np.load(X2 + 'vectors_leaves_centred.npy').astype(np.float64)
IDX = np.load(X2 + 'subsamples/indices.npy')
assert V.shape[0] == len(keys), (V.shape, len(keys))
pos = {k: i for i, k in enumerate(keys)}
B = T + '/data/ontology/v0.4-leaves/thema_L_x2_O50s/'
M = collections.defaultdict(set)
for r in csv.DictReader(open(B + 'members.tsv'), delimiter='\t'): M[r['node']].add(pos[r['key']])
haspar = {r['child'] for r in csv.DictReader(open(B + 'edges.tsv'), delimiter='\t')}
small = sorted(n for n in M if n not in haspar and len(M[n]) <= 50)
cont = {}
for s in small:
    c = sorted(((len(M[s] & M[p]) / len(M[s]), -len(M[p]), p) for p in M if p != s and len(M[p]) > len(M[s])), reverse=True)[:5]
    cont[s] = [p for _, _, p in c]
cands = sorted({p for s in small for p in cont[s]})
sets = small + cands
NR = int(sys.argv[1]) if len(sys.argv) > 1 else 200
N = len(keys)
ind = np.zeros((len(sets), N), dtype=np.int32)
for i, s in enumerate(sets): ind[i, list(M[s])] = 1
log = open(OUT + '/progress.txt', 'w')
res = {s: {'ownJ': [], 'pg': [], 'nest': {p: [] for p in cont[s]}} for s in small}
t0 = time.time()
for r in range(NR):
    sub = np.sort(IDX[r]); m = len(sub)
    Z = linkage(V[sub], method='ward')
    tot = 2 * m - 1
    par = np.full(tot, -1); size = np.ones(tot)
    cnt = np.zeros((len(sets), tot), dtype=np.int32); cnt[:, :m] = ind[:, sub]
    kids = []
    for k in range(m - 1):
        a, b = int(Z[k, 0]), int(Z[k, 1]); node = m + k
        par[a] = node; par[b] = node; size[node] = size[a] + size[b]
        cnt[:, node] = cnt[:, a] + cnt[:, b]; kids.append((a, b))
    setsz = cnt[:, :m].sum(axis=1)
    inner = np.arange(m, tot)
    best = {}
    for i, s in enumerate(sets):
        if setsz[i] == 0: best[s] = (-1, 0.0); continue
        c = cnt[i, inner]; J = c / (size[inner] + setsz[i] - c); j = int(np.argmax(J)); best[s] = (int(inner[j]), float(J[j]))
    def leaves(node):
        out = []; st = [node]
        while st:
            x = st.pop()
            if x < m: out.append(int(sub[x]))
            else: a, b = kids[x - m]; st += [a, b]
        return out
    def anc(node):
        out = set(); x = node
        while x >= 0: out.add(x); x = par[x]
        return out
    for s in small:
        node, J = best[s]; res[s]['ownJ'].append(J)
        if node < 0: res[s]['pg'].append(None); continue
        x = par[node]
        while x >= 0 and size[x] < 2 * size[node]: x = par[x]
        res[s]['pg'].append(frozenset(leaves(x)) if x >= 0 else None)
        A = anc(node)
        for p in cont[s]:
            pn, pj = best[p]; res[s]['nest'][p].append((pn in A, pj))
    log.write(f'run {r+1}/{NR} {time.time()-t0:.0f}s\n'); log.flush()
def jac(a, b): return len(a & b) / len(a | b)
rows = []
for s in small:
    pgs = [g for g in res[s]['pg'] if g]
    bestc, med = -1, None
    for g in pgs[:200]:
        c = sum(jac(g, h) >= 0.7 for h in pgs)
        if c > bestc: bestc, med = c, g
    dag = max(((jac(med, M[p]), p) for p in M if p != s), default=(0, None)) if med else (0, None)
    dn = dag[1]
    rows.append({'root': s, 'size': len(M[s]),
                 'own_support_J70': round(float(np.mean([j >= 0.7 for j in res[s]['ownJ']])), 3),
                 'own_meanJ': round(float(np.mean(res[s]['ownJ'])), 3),
                 'parent_group_freq': round(bestc / NR, 3), 'parent_group_size': len(med) if med else 0,
                 'pg_size_ratio': round(len(med) / len(M[s]), 2) if med else 0,
                 'pg_best_dag_node': dn, 'pg_best_dag_J': round(dag[0], 3),
                 'pg_dag_node_size': len(M[dn]) if dn else 0,
                 'share_of_root_in_dag_node': round(len(M[s] & M[dn]) / len(M[s]), 3) if dn else 0,
                 'missing_from_dag_node': len(M[s] - M[dn]) if dn else 0,
                 'pg_contains_root_share': round(len(M[s] & med) / len(M[s]), 3) if med else 0,
                 'containers': ';'.join(f"{p}:{len(M[p])}:{round(len(M[s]&M[p])/len(M[s]),2)}:nest{round(float(np.mean([a for a,_ in res[s]['nest'][p]])),2)}:J{round(float(np.mean([b for _,b in res[s]['nest'][p]])),2)}" for p in cont[s])})
with open(OUT + '/per_root.tsv', 'w') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t'); w.writeheader(); w.writerows(rows)
log.write('done\n'); log.close()
