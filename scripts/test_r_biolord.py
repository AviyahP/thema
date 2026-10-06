#!/usr/bin/env python3
"""Encode the v0.3 universe's descriptions with BioLORD, for Test R transfer (ii). EXPLORATORY.

The brief asks for "the full 10,770 with the existing embeddings_biolord.npy". **That file is
(1854, 768)** -- the v0.1/v0.2 universe -- so it cannot serve the 10,770, and the matrix has to be
produced. BioLORD-2023 is wired into `embed.py` and already in the local HuggingFace cache, so this
is a local encode with no API spend. Written to a NEW file; nothing is overwritten.

One property worth stating rather than discovering later: BioLORD's effective limit is 128 tokens
(`embed.py:45`) against MedCPT's longer window, so these descriptions are truncated for it. That
makes transfer (ii) a HARDER test than a like-for-like re-embed, not an easier one.

Usage::

    uv run scripts/test_r_biolord.py
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))


def main(argv: list[str] | None = None) -> int:
    """Encode and save.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    from build_trees_10770 import peak_mb
    from thema.data import descriptions as desc
    from thema.embed import BIOLORD_MODEL, embed
    from thema.ontology.universe import load_embedded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--out", type=Path,
                        default=Path("data/ontology/v0.3/embeddings_biolord_10770.npy"))
    args = parser.parse_args(argv)

    if args.out.exists():
        print(f"  {args.out} exists; not overwritten")
        return 0
    root = args.data / "ontology" / f"v{args.version}"
    embedded = load_embedded(root, args.data / "pathways.tsv")
    keys = list(embedded.keys)
    table = desc.read(args.data / "pathway_descriptions.tsv")
    missing = [k for k in keys if k not in table]
    if missing:
        print(f"  STOP: {len(missing)} universe rows have no current description, "
              f"e.g. {missing[:3]}")
        return 1
    texts = [table[k] for k in keys]
    print(f"BIOLORD ENCODE  {len(texts):,} descriptions, model {BIOLORD_MODEL}", flush=True)

    clock = time.perf_counter()
    vectors = embed(texts)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.save(args.out, vectors)
    print(f"  {vectors.shape} in {time.perf_counter() - clock:.0f}s, "
          f"peak {peak_mb():.0f} MB -> {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
