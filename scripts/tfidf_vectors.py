#!/usr/bin/env python3
"""TF-IDF vectors over the SAME descriptions the ontology embeds, for test 3's lexical control.

Test 3 declares this arm **not optional**: "If plain word overlap matches BioLORD in the
zero-overlap band, the embedding is adding nothing over word counting, and that must be known before
the freeze rather than after." The control therefore has to go through the identical pipeline --
same subsamples, same cap, same cutoff, same floors procedure -- with only the vectors changed.

Written with numpy and scipy only. `sentence_transformers` is confined to `src/thema/embed.py` by a
test, and nothing here needs it: TF-IDF is a word count.

**L2-normalised, because the pipeline requires it.** `cluster.distances` raises on non-unit rows,
correctly -- Ward on non-Euclidean input is silently meaningless. Cosine on TF-IDF is the standard
choice anyway, and L2 normalisation is what makes cosine a Euclidean distance.

Usage::

    uv run scripts/tfidf_vectors.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import sparse

from thema.data import descriptions as descriptions_table
from thema.ontology.universe import load_embedded

#: Tokens: lowercase words of three or more characters. Deliberately plain -- the point of the
#: control is "plain word overlap", so stemming or phrase detection would make it something else.
WORD = re.compile(r"[a-z][a-z0-9-]{2,}")

#: Drop terms appearing in more than this share of documents. A term in nearly every description
#: carries no signal and inflates every cosine.
MAX_DOCUMENT_SHARE = 0.5

#: Keep terms appearing in at least this many documents, so hapax noise does not dominate.
MIN_DOCUMENT_COUNT = 3

#: How many dimensions the output keeps. Truncated by document frequency, not by SVD: a dense
#: reduction would be a second modelling choice and the control is meant to be word counting.
MAX_TERMS = 20_000


def main(argv: list[str] | None = None) -> int:
    """Write L2-normalised TF-IDF vectors for the embedded universe.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    embedded = load_embedded(root, args.data / "pathways.tsv")
    keys = list(embedded.keys)
    texts = descriptions_table.read(args.data / "pathway_descriptions.tsv")
    missing = [k for k in keys if not texts.get(k)]
    if missing:
        print(f"  {len(missing)} of {len(keys):,} pathways have no description, e.g. {missing[0]}")

    documents = [WORD.findall((texts.get(k) or "").lower()) for k in keys]
    frequency = Counter()
    for document in documents:
        frequency.update(set(document))
    n = len(keys)
    usable = {
        term for term, count in frequency.items()
        if MIN_DOCUMENT_COUNT <= count <= MAX_DOCUMENT_SHARE * n
    }
    ranked = sorted(usable, key=lambda t: (-frequency[t], t))[:MAX_TERMS]
    index = {term: i for i, term in enumerate(ranked)}
    print(f"  {len(frequency):,} distinct terms, {len(usable):,} usable, "
          f"{len(ranked):,} kept (document frequency {MIN_DOCUMENT_COUNT} to "
          f"{MAX_DOCUMENT_SHARE:.0%})")

    rows, cols, counts = [], [], []
    for row, document in enumerate(documents):
        local = Counter(t for t in document if t in index)
        for term, count in local.items():
            rows.append(row)
            cols.append(index[term])
            counts.append(count)
    matrix = sparse.csr_matrix(
        (np.asarray(counts, dtype=np.float64), (rows, cols)), shape=(n, len(ranked))
    )
    # Smoothed idf, the standard form: log((1 + n) / (1 + df)) + 1, so no term gets weight zero.
    document_frequency = np.asarray((matrix > 0).sum(axis=0), dtype=np.float64).ravel()
    idf = np.log((1.0 + n) / (1.0 + document_frequency)) + 1.0
    # Sublinear tf, also standard: a term repeated ten times is not ten times as informative.
    matrix.data = 1.0 + np.log(matrix.data)
    weighted = matrix @ sparse.diags(idf)
    dense = np.asarray(weighted.todense(), dtype=np.float32)
    norms = np.linalg.norm(dense, axis=1, keepdims=True)
    empty = int((norms.ravel() == 0).sum())
    if empty:
        # A row of zeros cannot be unit length and would break the distance computation. Give it a
        # single arbitrary unit direction and record how many there were, rather than silently
        # dropping a pathway the real build keeps.
        print(f"  {empty} pathway(s) have no usable term and get a placeholder unit vector")
        for row in np.flatnonzero(norms.ravel() == 0):
            dense[row, row % dense.shape[1]] = 1.0
        norms = np.linalg.norm(dense, axis=1, keepdims=True)
    dense /= norms

    out = args.out or (root / "tfidf_vectors.npy")
    part = out.with_suffix(".part.npy")
    np.save(part, dense)
    part.replace(out)
    digest = hashlib.sha256(dense.tobytes()).hexdigest()[:16]
    meta = {
        "n": n, "terms": len(ranked), "sha256_16": digest,
        "min_document_count": MIN_DOCUMENT_COUNT,
        "max_document_share": MAX_DOCUMENT_SHARE,
        "max_terms": MAX_TERMS,
        "empty_rows_given_placeholder": empty,
        "missing_descriptions": len(missing),
        "tf": "sublinear, 1 + log(count)",
        "idf": "smoothed, log((1 + n) / (1 + df)) + 1",
        "normalisation": "L2, required by cluster.distances",
    }
    (out.with_suffix(".json")).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"  {dense.shape} float32, unit rows "
          f"(max |1 - norm| = {float(np.abs(1 - np.linalg.norm(dense, axis=1)).max()):.2e})")
    print(f"  digest {digest}  -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
