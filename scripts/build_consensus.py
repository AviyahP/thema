"""Build and export the ontology, with the greedy-consensus pass before ``hasse``.

This is not a second method. It is ``recurrent_dag`` run once on the real side with the rule that
``docs/spec/amendment-2026-09-24c.md`` pre-registered and E confirmed: recurrence the only gate,
declared ``m = 0.33`` at every size, a per-size floor solved from the scramble at FDR <= 0.01, and
the effective threshold ``max(declared, floor)``.

``assemble()`` takes ONE ``m`` and cannot express that, because the threshold now depends on the
family's size. Rather than widen ``assemble`` -- which every earlier build and every test depends
on -- the rule is applied here, on the families the same pipeline produces, and the surviving sets
go through the same ``hasse`` and the same ``export.write``.

The floors are an INPUT, read from the calibration that solved them. They are never recomputed
here: re-solving a threshold at build time against the data being built is the defect
``amendment-2026-09-24b.md`` withdrew.
"""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from thema.data import descriptions as descriptions_table
from thema.data.pathways import PathwayCollection, partition_universe
from thema.ontology import bitset as bits
from thema.ontology import export
from thema.ontology.base import Node, Ontology
from thema.ontology.consensus import DEFAULT_JACCARD, DEFAULT_STRAY, consensus
from thema.ontology.recurrent import (
    DEFAULTS,
    families,
    family_members,
    family_support,
    hasse,
    prepare,
    score,
)
from thema.ontology.universe import load_embedded

#: The locked rule. Declared before the run and not revisable against its result.
DECLARED_M = 0.33

#: Support is compared at the precision the calibration solved its floors in. See :data:`FLOORS`.
SUPPORT_DECIMALS = 6
THETA = 0.70
INCLUSION_CUT = 0.25
MIN_SIZE = 3
RUNS = 100

#: Per-size floors solved on the 20 calibration scrambles at FDR <= 0.01 and confirmed once on the
#: 10 held-out, under the MedCPT vectors. ``(low, high, floor)``, the strata of the amendment.
#: The floors the calibration solved, at the precision it solved them.
#:
#: Support is a ratio of run counts, so a floor is a value like 0.976744 (42/43) -- rounding it to
#: 0.98 raises the bar and silently drops families the calibration admitted. It cost five themes
#: the first time this was written.
#:
#: The calibration reads support from each side's TSV, written at six decimals, so its candidate
#: grid is six-decimal values and the solved floor is one of them. A family whose true support is
#: 10/11 = 0.909090909... is reported as 0.909091 there and admitted; compared at full precision
#: here it would fall just below the same floor and be dropped. :data:`SUPPORT_DECIMALS` keeps the
#: two in the same representation. Two more themes.
FLOORS: tuple[tuple[int, int, float], ...] = (
    (3, 3, 0.976744),
    (4, 4, 0.909091),
    (5, 5, 0.720000),
    (6, 6, 0.608247),
    (7, 9, 0.450000),
    (10, 14, 0.101010),
    (15, 29, 0.020202),
    (30, 49, 0.020000),
    (50, 99, 0.020000),
    (100, 199, 0.020000),
    (200, 10**9, 0.020000),
)


def threshold_for(size: int) -> float:
    """The effective threshold for a family of this size: ``max(declared, floor)``.

    Args:
        size: The family's completed member count.

    Returns:
        The support a family of that size must reach.

    Raises:
        ValueError: If no stratum covers the size, which would mean the strata are not exhaustive.
    """
    for low, high, floor in FLOORS:
        if low <= size <= high:
            return max(DECLARED_M, floor)
    raise ValueError(f"no stratum covers size {size}")


def main(argv: Sequence[str] | None = None) -> int:
    """Build the confirmatory ontology and write it."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.2")
    parser.add_argument("--directory", default="recurrent_dag_consensus")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--stray", type=float, default=DEFAULT_STRAY)
    parser.add_argument("--jaccard", type=float, default=DEFAULT_JACCARD)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    root = args.data / "ontology"
    embedded = load_embedded(root / f"v{args.version}", args.data / "pathways.tsv")
    keys = list(embedded.keys)
    n = len(keys)
    settings = {
        **DEFAULTS, "runs": RUNS, "tol": 0.15, "linkage": "ward",
        "min_size": MIN_SIZE, "theta": THETA,
    }

    ready = prepare(embedded.vectors, n, settings, seed=args.seed)
    pool = score(ready, settings)
    words = ready.present.shape[1] * bits.WORD

    completed: dict[int, np.ndarray] = {}
    for grouping in range(len(pool.groupings)):
        if np.isnan(pool.support[grouping]):
            continue
        candidate, inclusion = family_members([grouping], pool, ready.present, words)
        members = sorted(
            p for p in bits.unpack(candidate) if inclusion.get(p, 0.0) >= INCLUSION_CUT
        )
        if len(members) >= MIN_SIZE:
            completed[grouping] = bits.pack(members, words)

    gated: list[tuple[np.ndarray, float, dict[int, float]]] = []
    for seed_grouping, family in families(list(completed), completed, pool):
        support = family_support(family, pool, ready.eligible_mask)
        if np.isnan(support):
            continue
        member_bits = completed[seed_grouping]
        size = bits.count(member_bits)
        if round(float(support), SUPPORT_DECIMALS) < threshold_for(size):
            continue
        # The SELECTION vote -- the seed's own completed copies, which is what chose the members
        # (addendum step 7). The family vote is a different number, and reporting it was what put
        # inclusions below the cutoff into the confirmatory members.tsv.
        _candidate, selection = family_members([seed_grouping], pool, ready.present, words)
        gated.append((member_bits, float(support), selection))

    print(f"  families through the gate: {len(gated):,}")
    pre_blocks = [block for block, _s, _i in gated]
    pre_roots = sum(1 for p in hasse(pre_blocks) if not p)

    # THE CONSENSUS PASS: reconcile the accepted themes with one another before drawing edges.
    verdict = consensus(
        pre_blocks, [s for _b, s, _i in gated], [i for _b, _s, i in gated], words,
        stray=args.stray, jaccard=args.jaccard,
    )
    print(f"  after consensus: {len(verdict.accepted):,} nodes, {len(verdict.superseded)} "
          f"superseded, {len(verdict.inherited)} members inherited")
    kept = [
        (verdict.members[i], gated[c][1], gated[c][2])
        for i, c in enumerate(verdict.accepted)
    ]
    member_sets = [block for block, _s, _i in kept]
    parents_of = hasse(member_sets)

    ids = [f"n{index:04d}" for index in range(len(kept))]
    nodes = tuple(
        Node(
            id=ids[index],
            parents=tuple(ids[p] for p in parents_of[index]),
            members=tuple(
                (keys[p], round(float(inclusion.get(p, 1.0)), 4))
                for p in sorted(bits.unpack(block))
            ),
            support=round(support, 6),
        )
        for index, (block, support, inclusion) in enumerate(kept)
    )
    placed = {key for node in nodes for key in node.keys}
    unplaced = tuple(k for k in keys if k not in placed)
    print(f"  nodes {len(nodes):,}   placed {len(placed):,}   unplaced {len(unplaced):,}")

    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8")
    )
    by_key = collection.by_key
    _kept_universe, excluded_rows = partition_universe(collection)
    texts = descriptions_table.read(args.data / "pathway_descriptions.tsv")
    universe_meta = json.loads(
        (root / f"v{args.version}" / "universe.json").read_text(encoding="utf-8")
    )

    manifest = {
        "universe_digest": embedded.digest,
        "descriptions_digest": universe_meta.get("descriptions_digest"),
        "embeddings_sha256_16": universe_meta.get("embeddings_sha256_16"),
        "embedder": universe_meta.get("embedder"),
        "n_excluded_no_genes": len(excluded_rows),
        "n_universe": len(_kept_universe),
        "n_embedded": n,
        "rule": "amendment-2026-09-24c: recurrence only; max(declared 0.33, per-size floor)",
        "theta": THETA,
        "declared_m": DECLARED_M,
        "inclusion_threshold": INCLUSION_CUT,
        "floors": [[low, high, floor] for low, high, floor in FLOORS],
        "calibration": "20 calibration + 10 held-out scrambles; overall held-out FDR 0.0036",
        "truncated_text_baseline": False,
        "consensus": {
            "rules": "greedy consensus, spec amendment 2026-09-25 (Bryant 2003; Felsenstein 2004)",
            "stray": args.stray,
            "jaccard": args.jaccard,
            "nodes_before": len(pre_blocks),
            "roots_before": pre_roots,
            "superseded": len(verdict.superseded),
            "inherited_members": len(verdict.inherited),
            "themes_that_grew": len(verdict.grew),
        },
    }
    ontology = Ontology(
        method="recurrent_dag",
        params={**settings, "m": "per-size, see manifest.floors"},
        nodes=nodes,
        unplaced=unplaced,
        manifest=manifest,
    )
    info = {k: (p.source, p.name, p.n_genes) for k, p in by_key.items()}
    written = export.write(
        ontology,
        root,
        args.version,
        {k: p.genes for k, p in by_key.items()},
        manifest,
        dry_run=args.dry_run,
        info=info,
        directory=args.directory,
        undescribed=[k for k in keys if k not in texts],
        excluded=[(p.key, p.source, p.name) for p in excluded_rows],
    )
    print(f"  -> {written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
