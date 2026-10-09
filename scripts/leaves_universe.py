#!/usr/bin/env python3
"""Build universe L and everything the leaves build needs beside it.

Writes a versioned directory that the existing tree builder and v0.4 pipeline can read unchanged:
``universe.json``, ``embeddings.npy``, ``embedding_keys.txt`` and ``subsamples/indices.npy``.

The stored vectors are **already centred on L and renormalised**, which is why the tree builder must
be given a space name outside ``("centred", "tfidf")`` -- those two centre again, and centring twice
is not the protocol. The space is therefore ``leaves_centred``, which also makes the tree directory
self-describing.

``universe_digest`` in the written ``universe.json`` is the FULL universe's digest, not L's. That
field is how :func:`thema.ontology.universe.load_embedded` asserts that ``pathways.tsv`` has not
moved since the artifact was written, which is a claim about the source table and is true. L's own
digest is recorded separately as ``leaves_digest``.

Usage::

    uv run scripts/leaves_universe.py
    uv run scripts/leaves_universe.py --sensitivity     # counts only, is_a + part_of definition
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from thema.data.hierarchy import read_reactome_relation
from thema.data.pathways import PathwayCollection, partition_universe
from thema.embed import centre_and_renormalise
from thema.ontology.evalsets import PRIMARY_RELATIONS, go_edges
from thema.ontology.leaves import internal, leaf_universe
from thema.ontology.universe import load_embedded, universe_digest

#: The master seed and scheme are v0.3's, so the draw is the same procedure on a smaller universe.
MASTER_SEED = 20260925
SUBSAMPLE = 0.8
#: Drawn to 400 rows: 200 for the build and 200 so the halves 1-100 and 101-200 are disjoint.
TOTAL_ROWS = 400
#: The centred-and-renormalised matrix, stored beside the raw one. See the note in main().
VECTORS_CENTRED = "vectors_leaves_centred.npy"
#: The sensitivity definition the spec asks for, counts only.
SENSITIVITY_RELATIONS: tuple[str, ...] = ("is_a", "part_of")


def curated_edges(data: Path, relations: tuple[str, ...]) -> dict[str, set[str]]:
    """Child-to-parent edges over Reactome and GO together, in universe key space.

    Args:
        data: The data directory.
        relations: Which GO relations to follow.

    Returns:
        Child key to parent keys.
    """
    rel = read_reactome_relation(
        (data / "raw" / "ReactomePathwaysRelation.txt").read_text().splitlines())
    edges: dict[str, set[str]] = {f"reactome:{c}": {f"reactome:{p}" for p in ps}
                                  for c, ps in rel.items()}
    for child, ups in go_edges(
            (data / "raw" / "go-basic.obo").read_text().splitlines(), relations).items():
        edges[f"go:{child}"] = {f"go:{p}" for p in ups}
    return edges


def main(argv: list[str] | None = None) -> int:
    """Write universe L, its vectors and its subsamples.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--from-version", default="0.3", help="where the full vectors live")
    parser.add_argument("--version", default="0.4-leaves")
    parser.add_argument("--space", default="leaves_centred")
    parser.add_argument("--rows", type=int, default=TOTAL_ROWS)
    parser.add_argument("--exclude", type=Path, default=None,
                        help="a TSV with a `key` column listing inputs to drop from the universe "
                             "BEFORE the summary rule is applied; data/excluded_inputs.tsv. The "
                             "source table is never edited, so an exclusion is a config choice "
                             "and stays reversible")
    parser.add_argument("--sensitivity", action="store_true",
                        help="also report the is_a + part_of counts; writes nothing extra")
    args = parser.parse_args(argv)

    clock = time.perf_counter()
    source = args.data / "ontology" / f"v{args.from_version}"
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    kept, _excluded = partition_universe(collection)
    sources = {p.key: p.source for p in collection.pathways}
    full_keys = {p.key for p in kept}

    embedded = load_embedded(source, args.data / "pathways.tsv")
    row_of = {key: i for i, key in enumerate(embedded.keys)}

    source_digest = universe_digest(full_keys)   # the UNREDUCED universe, before exclusions
    dropped: set[str] = set()
    if args.exclude is not None and args.exclude.is_file():
        import csv as _csv

        with args.exclude.open() as handle:
            dropped = {row["key"] for row in _csv.DictReader(handle, delimiter="\t")}
        # Excluded BEFORE the summary rule, because dropping an input can turn a pathway that was
        # internal into a leaf: a parent whose only universe descendant was excluded now has none.
        before = len(full_keys)
        full_keys = full_keys - dropped
        print(f"  EXCLUSIONS from {args.exclude}: {len(dropped)} listed, "
              f"{before - len(full_keys)} were in the universe -> {len(full_keys):,} remain")

    edges = curated_edges(args.data, PRIMARY_RELATIONS)
    leaves, counts = leaf_universe(full_keys, edges, sources)
    leaves = [k for k in leaves if k in row_of]

    print(f"UNIVERSE L  from {len(full_keys):,} to {len(leaves):,}")
    for name in sorted({s for s in sources.values()}):
        u = counts.get(f"{name}_universe", 0)
        i = counts.get(f"{name}_internal", 0)
        kept_n = counts.get(f"{name}_leaves", 0)
        if u:
            print(f"  {name:<10} universe {u:>6,}   internal {i:>6,} ({i / u:>5.1%})   "
                  f"leaves {kept_n:>6,}")
    print(f"  {'TOTAL':<10} universe {counts['n_universe']:>6,}   "
          f"internal {counts['n_internal']:>6,}   leaves {counts['n_leaves']:>6,}")

    if args.sensitivity:
        alt = curated_edges(args.data, SENSITIVITY_RELATIONS)
        alt_internal = internal(alt, full_keys)
        go_alt = sum(1 for k in alt_internal if k.startswith("go:"))
        go_primary = counts.get("go_internal", 0)
        print(f"  SENSITIVITY, counts only: GO internal under is_a + part_of = {go_alt:,}, "
              f"against {go_primary:,} under the primary closure "
              f"(difference {go_alt - go_primary:+,})")
        print(f"    universe L would be {len(full_keys) - len(alt_internal & full_keys):,} "
              "under that definition")

    rows = np.array([row_of[k] for k in leaves], dtype=np.int64)
    raw = embedded.vectors[rows]
    vectors, mean = centre_and_renormalise(raw)
    root = args.data / "ontology" / f"v{args.version}"
    (root / "subsamples").mkdir(parents=True, exist_ok=True)
    # embeddings.npy holds the RAW L vectors; the centred matrix is a sidecar. Every consumer then
    # applies exactly ONE centring on L: the tree builder is given the sidecar through --vectors
    # under a space name it does not centre, and build_hidef.py centres embeddings.npy itself. The
    # earlier arrangement -- storing the centred matrix as embeddings.npy -- made build_hidef centre
    # a second time, subtracting a residual mean of norm 0.0062 and comparing two arms that had had
    # different transformations applied. The geometry barely moved (cosine 0.999981) but a baseline
    # is worth nothing if it is not the same transformation.
    np.save(root / "embeddings.npy", raw.astype(np.float32))
    np.save(root / VECTORS_CENTRED, vectors.astype(np.float32))
    (root / "embedding_keys.txt").write_text("\n".join(leaves) + "\n", encoding="utf-8")

    take = int(np.ceil(SUBSAMPLE * len(leaves)))
    rng = np.random.default_rng(MASTER_SEED)
    indices = np.vstack([np.sort(rng.choice(len(leaves), take, replace=False))
                         for _ in range(args.rows)])
    np.save(root / "subsamples" / "indices.npy", indices)
    (root / "subsamples" / "manifest.json").write_text(json.dumps({
        "master_seed": MASTER_SEED, "total": args.rows, "subsample": SUBSAMPLE,
        "n": len(leaves), "take": take, "leaves_digest": universe_digest(set(leaves)),
        "scheme": "v0.3's scheme on universe L: numpy default_rng(master_seed), one sorted "
                  "choice(n, take, replace=False) per row, drawn in order. Row i is tree i. "
                  "Halves 1-100 and 101-200 are disjoint.",
    }, indent=2) + "\n", encoding="utf-8")

    digest = hashlib.sha256((root / "embeddings.npy").read_bytes()).hexdigest()[:16]
    centred_digest = hashlib.sha256((root / VECTORS_CENTRED).read_bytes()).hexdigest()[:16]
    (root / "universe.json").write_text(json.dumps({
        "n_universe": len(full_keys), "n_embedded": len(leaves),
        # universe_digest asserts that pathways.tsv has not moved since this artifact was
        # written, which is what load_embedded checks it against -- so it must be the digest of the
        # UNREDUCED universe even when exclusions are applied. Recording the reduced digest here
        # instead made load_embedded refuse the artifact, correctly: it claimed a universe the
        # source table does not give. The reduced set has its own fields.
        "universe_digest": source_digest,
        "universe_digest_after_exclusions": universe_digest(full_keys),
        "leaves_digest": universe_digest(set(leaves)),
        "rule": "n_genes >= 1, then listed exclusions dropped, then every curated summary removed",
        "exclusions_file": None if args.exclude is None else str(args.exclude),
        "n_excluded": len(dropped),
        "excluded_keys": sorted(dropped),
        "summary_rule": "a pathway with at least one universe descendant over the primary GO "
                        "closure (clarification 9) or ReactomePathwaysRelation; Hallmark and BTM "
                        "are flat and always kept",
        "embedder": embedded.embedder,
        "space": args.space,
        "vectors": "embeddings.npy holds the full universe's RAW MedCPT vectors for L. The "
                   "centred-and-renormalised matrix every build actually clusters is the sidecar "
                   f"{VECTORS_CENTRED}, passed to the tree builder with --vectors; build_hidef "
                   "centres embeddings.npy itself. One centring on L either way.",
        "embeddings_sha256_16": digest,
        "vectors_centred_file": VECTORS_CENTRED,
        "vectors_centred_sha256_16": centred_digest,
        "centre_norm": float(np.linalg.norm(mean)),
        "counts": counts,
        "seconds": round(time.perf_counter() - clock, 1),
    }, indent=2) + "\n", encoding="utf-8")
    print(f"  -> {root}  ({time.perf_counter() - clock:.0f}s)")
    print(f"  vectors {vectors.shape}, subsamples {indices.shape}, take {take:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
