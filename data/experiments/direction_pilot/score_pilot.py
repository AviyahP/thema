"""Direction pilot scorer (7 Oct 2026, exploratory). Run on the Mac from the repo root:
    .venv/bin/python data/experiments/direction_pilot/score_pilot.py
Reads only; writes data/experiments/direction_pilot/pilot_result.txt. No API calls.
Downloads ncbi/MedCPT-Query-Encoder from Hugging Face on first run (~440 MB)."""
import sys, csv, json, re, collections
from pathlib import Path
import numpy as np, torch
from transformers import AutoTokenizer, AutoModel
sys.path.insert(0, "src")
from thema.ontology.universe import load_embedded
from thema.data.hierarchy import read_reactome_relation
csv.field_size_limit(10**9)
D = Path("data/experiments/direction_pilot")
key = {r["id"]: r for r in csv.DictReader(open(D/"KEY_DO_NOT_SHARE.tsv"), delimiter="\t")}
fields = {x["id"]: x for x in map(json.loads, open(D/"direction_fields_v1.jsonl"))}
pairs = list(csv.DictReader(open(D/"pilot_pairs.tsv"), delimiter="\t"))
# article side = THEMA's stored MedCPT-Article embeddings of the same descriptions (not centred)
e = load_embedded(Path("data/ontology/v0.3"), Path("data/pathways.tsv"))
pos = {k: i for i, k in enumerate(e.keys)}
A = {i: np.asarray(e.vectors[pos[key[i]["key"]]], dtype=np.float32) for i in key}
A = {i: v/np.linalg.norm(v) for i, v in A.items()}
# query side = MedCPT query encoder on the generated phrases
tok = AutoTokenizer.from_pretrained("ncbi/MedCPT-Query-Encoder")
mod = AutoModel.from_pretrained("ncbi/MedCPT-Query-Encoder").eval()
phr = sorted({p for f in fields.values() for p in [f["broader"]] + list(f["narrower"]) if p and p.lower() != "none"})
Q = {}
with torch.no_grad():
    for s in range(0, len(phr), 64):
        b = phr[s:s+64]
        enc = tok(b, truncation=True, padding=True, return_tensors="pt", max_length=64)
        v = mod(**enc).last_hidden_state[:, 0, :].numpy()
        for t, x in zip(b, v): Q[t] = x/np.linalg.norm(x)
def up(c, p):
    b = fields[c]["broader"]; return float(Q[b] @ A[p]) if b in Q else 0.0
def down(p, c):
    ns = [n for n in fields[p]["narrower"] if n in Q]; return max(float(Q[n] @ A[c]) for n in ns) if ns else 0.0
res = collections.defaultdict(list)
for r in pairs:
    c, p, s = r["child_id"], r["parent_id"], r["source"]
    for name, f in (("up + down", lambda a, b: up(a, b) + down(b, a)), ("up only", up), ("down only", lambda a, b: down(b, a))):
        ok = f(c, p) > f(p, c); res[(name, "all")].append(ok); res[(name, s)].append(ok)
out = ["DIRECTION PILOT (exploratory). Accuracy = share of curated child->parent pairs where score(child->parent) > score(parent->child). Chance 50%; free-signal baseline on these pairs: density 61.5%. Pass bar >= 70%.", ""]
for name in ("up + down", "up only", "down only"):
    out.append(f"{name:10}  all {100*np.mean(res[(name,'all')]):5.1f}% (n={len(res[(name,'all')])})   reactome {100*np.mean(res[(name,'reactome')]):5.1f}%   go {100*np.mean(res[(name,'go')]):5.1f}%")
# leakage alarm: broader phrase == name of a curated ancestor (exact, case-insensitive)
rel = read_reactome_relation(Path("data/raw/ReactomePathwaysRelation.txt").read_text().splitlines())
gop = collections.defaultdict(set); gon = {}; cur = None
for line in open("data/raw/go-basic.obo"):
    if line.startswith("["): cur = None
    elif line.startswith("id: GO:"): cur = line[4:].strip()
    elif cur and line.startswith("name: "): gon[cur] = line[6:].strip().lower()
    elif cur:
        m = re.match(r"(?:is_a:|relationship: (?:part_of|regulates|positively_regulates|negatively_regulates)) (GO:\d+)", line)
        if m: gop[cur].add(m.group(1))
rname = {}
for r in csv.DictReader(open("data/pathways.tsv"), delimiter="\t"):
    if r["source"].lower() == "reactome": rname[r["source_id"]] = r["name"].lower()
def anc(src, sid):
    par = gop if src == "go" else rel; seen = set(); st = list(par.get(sid, ()))
    while st:
        a = st.pop()
        if a not in seen: seen.add(a); st.extend(par.get(a, ()))
    return {(gon if src == "go" else rname).get(a, "") for a in seen} - {""}
allnames = {n.lower() for n in rname.values()} | set(gon.values())
alarm = collections.Counter(); tot = collections.Counter()
for i, k in key.items():
    src = k["source"]; b = fields[i]["broader"].strip().lower(); tot[src] += 1
    if b in allnames: alarm[src + " broader == any GO/Reactome name"] += 1
    if src in ("go", "reactome") and b in anc(src, k["key"].split(":", 1)[1]): alarm[src + " broader == a TRUE curated ancestor name"] += 1
out += ["", "LEAKAGE ALARM (exact name matches; not used for scoring):"]
for k2, v in sorted(alarm.items()):
    src = k2.split()[0]; out.append(f"  {k2:45} {v}/{tot[src]} = {100*v/tot[src]:.1f}%")
out.append(f"  pathways per source: {dict(tot)}")
(D/"pilot_result.txt").write_text("\n".join(out) + "\n"); print("\n".join(out))
