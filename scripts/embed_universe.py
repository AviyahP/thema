"""Embed a universe with the pinned MedCPT encoder, into its own versioned artifact.

Separate from ``build_ontology.py`` because embedding is a distinct, expensive step whose output
several builds share. **The token check is not decoration.** The previous encoder was loaded with a
128-token window while the median description runs to 231 tokens, so roughly 45% of every
description was discarded silently, for every build and for the confirmatory calibration. This
asserts the window is wide enough BEFORE the time is spent, and refuses to write if it is not.
"""

import argparse
import hashlib
import json
import time
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from thema.data import descriptions as descriptions_table
from thema.data.pathways import PathwayCollection, partition_universe
from thema.embed import (
    MEDCPT_MODEL,
    MEDCPT_REVISION,
    MODEL_MAX_TOKENS,
    embed_medcpt,
    medcpt_token_counts,
)
from thema.ontology.universe import universe_digest


def sha16(path: Path) -> str:
    """First 16 hex characters of a file's sha256."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def main(argv: Sequence[str] | None = None) -> int:
    """Embed the universe and write the artifact.

    Returns:
        0 on success.

    Raises:
        AssertionError: If any description is missing, or any exceeds the encoder's window.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--dry-run", action="store_true", help="check tokens, embed nothing")
    args = parser.parse_args(argv)

    out = args.data / "ontology" / f"v{args.version}"
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8")
    )
    kept, excluded = partition_universe(collection)
    texts = descriptions_table.read(args.data / "pathway_descriptions.tsv")
    keys = sorted(p.key for p in kept)
    missing = [k for k in keys if k not in texts]
    assert not missing, f"{len(missing)} universe pathways have no description"
    print(f"  universe {len(keys):,}   excluded (no genes) {len(excluded)}")

    counts = medcpt_token_counts([texts[k] for k in keys])
    over = sum(1 for c in counts if c > MODEL_MAX_TOKENS)
    print(f"  tokens: median {int(np.median(counts))}  p99 {int(np.quantile(counts, 0.99))}  "
          f"max {max(counts)}  over {MODEL_MAX_TOKENS}: {over}")
    assert over == 0, f"{over} descriptions exceed the {MODEL_MAX_TOKENS}-token window"
    if args.dry_run:
        print("  --dry-run: nothing embedded, nothing written")
        return 0

    start = time.perf_counter()
    vectors = embed_medcpt([texts[k] for k in keys])
    seconds = time.perf_counter() - start
    print(f"  embedded {vectors.shape} in {seconds/60:.1f} min")
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1.0, atol=1e-5)

    out.mkdir(parents=True, exist_ok=True)
    np.save(out / "embeddings.npy", vectors)
    (out / "embedding_keys.txt").write_text("\n".join(keys) + "\n", encoding="utf-8")
    blob = "\n".join(f"{k}\t{texts[k]}" for k in keys).encode("utf-8")
    (out / "universe.json").write_text(
        json.dumps({
            "n_universe": len(keys),
            "n_embedded": len(keys),
            "universe_digest": universe_digest({p.key for p in kept}),
            "rule": "n_genes >= 1",
            "embedder": {
                "id": MEDCPT_MODEL, "revision": MEDCPT_REVISION, "pooling": "cls",
                "max_length": MODEL_MAX_TOKENS,
                "input": "description text only, single segment",
            },
            "embeddings_sha256_16": sha16(out / "embeddings.npy"),
            "descriptions_digest": hashlib.sha256(blob).hexdigest()[:16],
            "embed_seconds": round(seconds, 1),
            "token_max": int(max(counts)),
            "note": "the FULL universe. v0.2 is the 1,850-pathway subset.",
            "dropped": [],
            "superseded_artifacts": [],
        }, indent=1) + "\n",
        encoding="utf-8",
    )
    print(f"  -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
