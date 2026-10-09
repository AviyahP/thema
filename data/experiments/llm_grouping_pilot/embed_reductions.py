import json
from pathlib import Path
import numpy as np
from thema.embed import embed_medcpt

D = Path(__file__).resolve().parent
rows = {}
for b in range(16):
    rows.update(json.loads((D / "reductions" / f"batch_{b:02d}_red.json").read_text()))
ids = list(rows)
for arm in ["process", "disease", "tissue", "joined"]:
    if arm == "joined":
        texts = [f'{rows[i]["process"]} {rows[i]["disease"]} {rows[i]["tissue"]}' for i in ids]
    else:
        texts = [rows[i][arm] for i in ids]
    np.savez(D / "reductions" / f"emb_{arm}.npz", ids=np.array(ids), vec=embed_medcpt(texts))
    print(arm, len(ids))
print("done")
