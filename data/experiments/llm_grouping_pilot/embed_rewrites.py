import json
from pathlib import Path
import numpy as np
from thema.embed import embed_medcpt, medcpt_token_counts

D = Path(__file__).resolve().parent
out = {}
for arm in ["orig", "neutral", "process", "context"]:
    ids, texts = [], []
    for b in range(16):
        if arm == "orig":
            rows = json.loads((D / f"batch_{b:02d}_desc.json").read_text())
            pairs = [(r["id"], r["description"]) for r in rows]
        else:
            f = D / "rewrites" / f"batch_{b:02d}_{arm}.json"
            if not f.exists():
                continue
            pairs = list(json.loads(f.read_text()).items())
        for i, t in pairs:
            ids.append(i)
            texts.append(t)
    n_tok = medcpt_token_counts(texts)
    vec = embed_medcpt(texts)
    np.savez(D / "rewrites" / f"emb_{arm}.npz", ids=np.array(ids), vec=vec, tokens=np.array(n_tok))
    print(arm, len(ids), "max tokens", max(n_tok))
print("done")
