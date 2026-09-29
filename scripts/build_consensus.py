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
import hashlib
import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from thema.data import descriptions as descriptions_table
from thema.data.pathways import PathwayCollection, partition_universe
from thema.embed import centre_and_renormalise
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
#: The membership cutoff. A pathway joins a completed grouping when the share of the grouping's
#: matched copies holding it reaches this.
#:
#: **0.50, adopted 29 Sep 2026** (DECISIONS.md), raised from 0.25. Not chosen on FDR -- every cutoff
#: from 0.25 to 0.50 clears every declared gate, and two independent scramble sets rank them in
#: opposite orders, so FDR cannot separate them. Chosen on what the discarded overlap is made of:
#: 63% of the pathways that stop straddling had a second home below 0.5, and of the 114 strongly
#: included ones that stop, 104 are still in two or more themes with their overlap turned into
#: nesting. The real loss is 10 pathways of 1,842, against straddlers falling from 46% to 29% of
#: those placed and seed stability rising from 0.849 to 0.866.
#:
#: The floors are selected BY this cutoff, not independently of it -- see FLOORS. A build
#: at a cutoff with no floors solved for it refuses to run rather than borrowing another cutoff's.
INCLUSION_CUT = 0.50
MIN_SIZE = 3
RUNS = 100

#: Per-size support floors, keyed by ``(space, inclusion cutoff)``. ``(low, high, floor)``, the
#: strata of the amendment.
#:
#: **A FLOOR BELONGS TO ITS CUTOFF.** The cutoff is applied at completion, before families form, so
#: changing it changes which families exist on both the real and the scrambled side. Measured with
#: the seeds held constant, moving 0.25 -> 0.50 shifts a floor by up to 0.150, which is larger than
#: the seed noise at every stratum. Borrowing another cutoff's floors is not conservative, it is
#: simply wrong, so :func:`threshold_for` raises rather than falling back. Aviyah, 29 Sep.
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
#:
#: Solved IN-ARM: a floor derived against one clustering space does not transfer to another, so the
#: centred build re-solved its own. The raw set is kept because the superseded v0.2 build must stay
#: reproducible.
#:
#: PROVENANCE. ``(centred, 0.25)`` and ``(raw, 0.25)`` are the original calibration, 20 calibration
#: and 10 held-out scrambles. ``(centred, 0.50)`` is the 29 Sep pooled calibration -- **40
#: calibration and 20 held-out scrambles**, held-out FDR 0.00333, every stratum under 0.02, logged
#: in ``data/experiments/inclusion_floors_pooled.json``. The pooled run also re-solved 0.25 and
#: landed within 0.01 of the committed values at every stratum, which is why those are left alone.
#: Keys are ``(space, inclusion cutoff)``. Every stratum at 10 members or more solves below the
#: declared m = 0.33 at every cutoff, so all of them pin to 0.33 through ``max(declared, floor)``;
#: the 0.25 sets keep their finer bands because that is how the original calibration recorded them,
#: and the 0.50 set carries the single 10+ band its own calibration solved. The two are identical in
#: effect and neither is rounded to make them look alike.
FLOORS: dict[tuple[str, float], tuple[tuple[int, int, float], ...]] = {
    ("centred", 0.25): (
        (3, 3, 0.838000), (4, 4, 0.890000), (5, 5, 0.670000), (6, 6, 0.530000), (7, 9, 0.370000),
        (10, 14, 0.101010), (15, 29, 0.020202), (30, 49, 0.020000), (50, 99, 0.020000),
        (100, 199, 0.020000), (200, 10**9, 0.020000),
    ),
    ("raw", 0.25): (
        (3, 3, 0.976744), (4, 4, 0.909091), (5, 5, 0.720000), (6, 6, 0.608247), (7, 9, 0.450000),
        (10, 14, 0.101010), (15, 29, 0.020202), (30, 49, 0.020000), (50, 99, 0.020000),
        (100, 199, 0.020000), (200, 10**9, 0.020000),
    ),
    # Pooled calibration, 29 Sep 2026: 40 calibration + 20 held-out scrambles, held-out FDR 0.00333.
    ("centred", 0.50): (
        (3, 3, 0.880000), (4, 4, 0.930000), (5, 5, 0.600000), (6, 6, 0.400000), (7, 9, 0.270000),
        (10, 10**9, 0.040541),
    ),
}


def floors_from_file(path: Path, inclusion: float) -> tuple[tuple[int, int, float], ...]:
    """Read one cutoff's solved floors out of a calibration report.

    Args:
        path: JSON written by ``scripts/calibrate_inclusion.py``.
        inclusion: Which cutoff's floors to take. The file holds one block per cutoff and taking the
            wrong one is the exact mistake :data:`FLOORS` exists to prevent, so this is explicit.

    Returns:
        ``(low, high, floor)`` per stratum, in stratum order.

    Raises:
        KeyError: If the file holds no block for this cutoff.
        ValueError: If a stratum was dropped, which the caller must not silently treat as passable.
    """
    report = json.loads(path.read_text(encoding="utf-8"))
    key = f"{inclusion:.2f}"
    if key not in report:
        raise KeyError(
            f"{path} holds no floors for inclusion {key}; it has {', '.join(sorted(report))}"
        )
    out: list[tuple[int, int, float]] = []
    for entry in report[key]["strata"]:
        if entry["floor"] is None:
            raise ValueError(
                f"{path}: stratum {entry['stratum']} could not meet the FDR target at inclusion "
                f"{key}, so it is DROPPED. A build must not run as though it passed."
            )
        low, _, high = entry["stratum"].partition("-")
        out.append((int(low), 10**9 if high == "" else int(high), float(entry["floor"])))
    return tuple(out)


def threshold_for(
    size: int,
    space: str = "centred",
    inclusion: float = INCLUSION_CUT,
    floors: tuple[tuple[int, int, float], ...] | None = None,
) -> float:
    """The effective threshold for a family of this size: ``max(declared, floor)``.

    Args:
        size: The family's completed member count.
        space: Which clustering space's floors to use. They are not interchangeable.
        inclusion: Which cutoff's floors to use. Also not interchangeable -- a floor is solved
            against the family population the cutoff produces.
        floors: Explicit floors from :func:`floors_from_file`, overriding the built-in table.

    Returns:
        The support a family of that size must reach.

    Raises:
        KeyError: If no floors were solved for this ``(space, inclusion)``. It REFUSES rather than
            falling back to another cutoff's: the cutoff moves a floor by more than seed noise does,
            so borrowing is wrong rather than merely approximate.
        ValueError: If no stratum covers the size, which would mean the strata are not exhaustive.
    """
    if floors is not None:
        bands: tuple[tuple[int, int, float], ...] = floors
    else:
        try:
            bands = FLOORS[(space, inclusion)]
        except KeyError:
            have = ", ".join(f"({a}, {b})" for a, b in sorted(FLOORS))
            raise KeyError(
                f"no floors solved for space={space!r} inclusion={inclusion}; solved sets are "
                f"{have}. Run scripts/calibrate_inclusion.py at this cutoff, or pass --floors."
            ) from None
    for low, high, floor in bands:
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
    parser.add_argument("--space", choices=("centred", "raw"), default="centred",
                        help="vectors handed to Ward (amendment 2026-09-26)")
    parser.add_argument(
        "--inclusion", type=float, default=INCLUSION_CUT,
        help="membership cutoff; floors must exist for it (see FLOORS) or the build refuses",
    )
    parser.add_argument(
        "--floors", type=Path,
        help="JSON from calibrate_inclusion.py; use the floors solved at THIS --inclusion",
    )
    parser.add_argument("--stray", type=float, default=DEFAULT_STRAY)
    parser.add_argument("--jaccard", type=float, default=DEFAULT_JACCARD)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    root = args.data / "ontology"
    embedded = load_embedded(root / f"v{args.version}", args.data / "pathways.tsv")
    keys = list(embedded.keys)
    n = len(keys)
    # The clustering space. Centred-and-renormalised as of the 2026-09-26 amendment; "raw" is kept
    # callable so the superseded builds remain reproducible from this script.
    universe_mean = None
    matrix = embedded.vectors
    if args.space == "centred":
        matrix, universe_mean = centre_and_renormalise(matrix)
        matrix = np.ascontiguousarray(matrix.astype(np.float32))
    settings = {
        **DEFAULTS, "runs": RUNS, "tol": 0.15, "linkage": "ward",
        "min_size": MIN_SIZE, "theta": THETA,
    }

    floors = None if args.floors is None else floors_from_file(args.floors, args.inclusion)
    if floors is not None:
        print("  floors solved at this cutoff: "
              + ", ".join(f"{low}-{high}:{max(DECLARED_M, f):.4f}"
                          for low, high, f in floors if low <= 9))
    ready = prepare(matrix, n, settings, seed=args.seed)
    pool = score(ready, settings)
    words = ready.present.shape[1] * bits.WORD

    completed: dict[int, np.ndarray] = {}
    for grouping in range(len(pool.groupings)):
        if np.isnan(pool.support[grouping]):
            continue
        candidate, inclusion = family_members([grouping], pool, ready.present, words)
        members = sorted(
            p for p in bits.unpack(candidate) if inclusion.get(p, 0.0) >= args.inclusion
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
        effective = threshold_for(size, args.space, args.inclusion, floors)
        if round(float(support), SUPPORT_DECIMALS) < effective:
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

    # PLACEMENT, reported three ways because "unplaced" alone understates it. A pathway that sits
    # only in a ROOT has been placed by the letter of the algorithm and told a reader almost
    # nothing: the ontology has given it a top-level bucket and no theme within it. Raising the
    # inclusion cutoff moves pathways into that state faster than it moves them out of the build,
    # so a freeze that reports only the strict count hides most of what the cutoff cost.
    roots = {node.id for node in nodes if not node.parents}
    in_nonroot = {key for node in nodes if node.id not in roots for key in node.keys}
    root_only = tuple(sorted(placed - in_nonroot))
    effectively_unplaced = len(unplaced) + len(root_only)
    by_id = {node.id: node for node in nodes}
    largest_root = max(roots, key=lambda r: len(by_id[r].keys), default=None)
    largest_root_direct = 0
    if largest_root is not None:
        covered = {
            key
            for node in nodes
            if largest_root in node.parents
            for key in node.keys
        }
        largest_root_direct = len(set(by_id[largest_root].keys) - covered)

    print(f"  nodes {len(nodes):,}   placed {len(placed):,}   unplaced {len(unplaced):,}")
    print(f"  root-only {len(root_only):,}   effectively unplaced {effectively_unplaced:,}"
          f"   largest root's direct members {largest_root_direct:,}")

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
        "inclusion_threshold": args.inclusion,
        "n_unplaced": len(unplaced),
        "n_root_only": len(root_only),
        "n_effectively_unplaced": effectively_unplaced,
        "largest_root_direct_members": largest_root_direct,
        "floors_calibrated_for_inclusion": (
            args.inclusion if args.floors else INCLUSION_CUT
        ),
        "floors_source": (
            str(args.floors) if args.floors else f"FLOORS[{args.space}, {args.inclusion}]"
        ),
        "floors": [
            [low, high, floor]
            for low, high, floor in (floors or FLOORS[(args.space, args.inclusion)])
        ],
        "calibration": (
            "20 calibration + 10 held-out scrambles, floors solved in-arm; overall held-out "
            "FDR 0.0051 (centred) / 0.0036 (raw)"
        ),
        "space": ("centred-renormalised" if args.space == "centred" else "raw"),
        "universe_mean_sha256_16": (
            hashlib.sha256(universe_mean.tobytes()).hexdigest()[:16]
            if universe_mean is not None else None
        ),
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
