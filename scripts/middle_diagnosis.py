#!/usr/bin/env python3
"""C5: why THEMA has no effective middle, measured on the real Ward runs.

C3 and C4 both point at the same thing: THEMA wins at 3-50 members, loses at 51-500, and removing
the pairs HiDeF places in a 51-500 theme flips the GO gap in THEMA's favour. So the question is not
whether the middle is thin but **why candidate groupings of 51-500 members fail**.

Three sections:

- **(a) Theme counts per size band**, every arm, so the thinness is a number.
- **(b) Recurrence failure analysis.** For candidate groupings that fail their support floor, every
  failed (grouping, run) check is classified as **missing members**, **extras over tolerance**, or
  **not eligible**. Mid-size candidates are compared against small ones.
- **(c) Where mid-size candidates are lost**: support gate, size cap, completion, consensus.

**Informational.** Nothing here changes the method, and nothing is tuned.

Usage::

    uv run scripts/middle_diagnosis.py --mode a
    uv run scripts/middle_diagnosis.py --mode bc
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

csv.field_size_limit(1 << 30)

#: Size bands for the theme census.
CENSUS: tuple[tuple[int, int], ...] = (
    (3, 10), (11, 50), (51, 200), (201, 500), (501, 3125), (3126, 10**9),
)

#: The two populations compared in the failure analysis.
MID = (51, 500)
SMALL = (3, 50)

#: How many failing groupings to classify per band.
SAMPLE = 1_000
SAMPLE_SEED = 20261005

ARMS = {
    "THEMA": "recurrent_dag_10770",
    "HiDeF m25": "hidef_10770_k15",
    "HiDeF m50": "hidef_10770_k15_maxres50",
    "HiDeF m100": "hidef_10770_k15_maxres100",
}


def theme_sizes(directory: Path) -> list[int]:
    """Member counts of every theme in a build.

    Args:
        directory: A build directory.

    Returns:
        Sizes, unsorted.
    """
    counts: dict[str, int] = defaultdict(int)
    with (directory / "members.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            counts[row["node"]] += 1
    return list(counts.values())


def main(argv: list[str] | None = None) -> int:
    """Run the census, or the failure analysis and the loss accounting.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("a", "bc"), required=True)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--space", default="centred")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    report: dict = {}

    if args.mode == "a":
        print("C5(a)  THEME COUNTS PER SIZE BAND")
        header = f"  {'arm':<12} " + " ".join(
            f"{f'{lo}-{hi}' if hi < 10**9 else f'{lo}+':>12}" for lo, hi in CENSUS
        ) + f" {'total':>8}"
        print(header)
        census: dict[str, dict] = {}
        for name, directory in ARMS.items():
            path = root / directory
            if not (path / "members.tsv").is_file():
                continue
            sizes = np.array(theme_sizes(path))
            cells = [int(((sizes >= lo) & (sizes <= hi)).sum()) for lo, hi in CENSUS]
            print(f"  {name:<12} " + " ".join(f"{c:>12,}" for c in cells)
                  + f" {len(sizes):>8,}")
            census[name] = {f"{lo}-{hi}": c for (lo, hi), c in zip(CENSUS, cells, strict=True)}
            census[name]["total"] = int(len(sizes))
        report["census"] = census
        mid = {n: c.get("51-200", 0) + c.get("201-500", 0) for n, c in census.items()}
        print("\n  themes of 51-500 members: "
              + ", ".join(f"{n} {v:,}" for n, v in mid.items()))
        share = {n: v / census[n]["total"] for n, v in mid.items()}
        print("  as a share of each arm's themes: "
              + ", ".join(f"{n} {v:.1%}" for n, v in share.items()))
        report["mid_51_500"] = mid
        report["mid_share"] = {k: round(v, 4) for k, v in share.items()}
    else:
        report = _failures(args, root)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"\n  -> {args.out}")
    return 0


def _failures(args: argparse.Namespace, root: Path) -> dict:
    """C5(b) and C5(c): classify failed checks, and account for mid-size losses.

    Args:
        args: Parsed arguments.
        root: The versioned ontology directory.

    Returns:
        The report.
    """
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    from build_10770 import DECLARED_M, INCLUSION_CUT, cut_key, load_material, stratum_of
    from cut_trees import CAP_SHARE, MIN_SIZE, THETA, TOL, cap_for, load_run
    from thema.ontology import bitset as bits
    from thema.ontology.recurrent import DEFAULTS, prepare, score

    meta = json.loads((root / "universe.json").read_text())
    universe, n = meta["universe_digest"], meta["n_embedded"]
    cap = cap_for(n)
    trees = root / "trees" / f"{args.space}_{universe}"
    runs = [load_run(trees / f"row{r:05d}.npz", n, cap) for r in range(1, 201)]
    settings = {**DEFAULTS, "runs": len(runs), "tol": TOL, "min_size": MIN_SIZE, "theta": THETA}
    ready = prepare(np.zeros((n, 1), dtype=np.float32), n, settings, 0, records=runs)
    pool = score(ready, settings)
    sizes = np.bitwise_count(ready.groupings).sum(axis=1).astype(np.int64)
    print(f"C5(b)  pool of {len(sizes):,} groupings from 200 real runs")

    floors = json.loads(
        (trees / "completions" / cut_key(cap, INCLUSION_CUT)
         / "floors_r1-200_n200.json").read_text()
    )
    thresholds = {i: e["effective"] for i, e in enumerate(floors["strata"])}

    report: dict = {"pool": int(len(sizes)), "bands": {}}
    rng = np.random.default_rng(SAMPLE_SEED)
    for label, (low, high) in (("51-500", MID), ("3-50", SMALL)):
        in_band = np.flatnonzero((sizes >= low) & (sizes <= high) & ~np.isnan(pool.support))
        failing = np.array([
            g for g in in_band
            if thresholds[stratum_of(int(sizes[g]))] is not None
            and round(float(pool.support[g]), 6) < thresholds[stratum_of(int(sizes[g]))]
        ])
        picked = (rng.choice(failing, size=min(SAMPLE, len(failing)), replace=False)
                  if len(failing) else failing)
        print(f"\n  {label} members: {len(in_band):,} eligible groupings, "
              f"{len(failing):,} fail their floor, classifying {len(picked):,}")
        missing_votes = extras_votes = ineligible = found = 0
        for g in picked:
            grouping = ready.groupings[g]
            for run in range(len(runs)):
                if run in pool.copies[g]:
                    found += 1
                    continue
                if not ready.eligible_mask[g, run]:
                    ineligible += 1
                    continue
                # Reconstruct the failure the matching rule saw: climb this run's chain to the
                # smallest cluster containing the shared members, then ask which term broke.
                drawn = ready.present[run] & grouping
                shared = bits.count(drawn)
                if not shared:
                    ineligible += 1
                    continue
                best_missing = shared
                chain = ready.records[run]
                start = chain.leaf_cluster[bits.unpack(drawn)[0]] if shared else -1
                at = start
                while at >= 0:
                    cluster = chain.clusters[at]
                    if bits.count(cluster & drawn) == shared:
                        # Every shared member is inside this cluster, so nothing is missing and
                        # the rejection can only have come from the extras term.
                        best_missing = 0
                        break
                    best_missing = shared - bits.count(cluster & drawn)
                    at = int(chain.parent[at])
                if best_missing > 0:
                    missing_votes += 1
                else:
                    extras_votes += 1
        total = missing_votes + extras_votes + ineligible
        print(f"    of {total:,} failed (grouping, run) checks "
              f"({found:,} succeeded and are excluded):")
        for name, value in (("missing members", missing_votes),
                            ("extras over tolerance", extras_votes),
                            ("not eligible", ineligible)):
            print(f"      {name:<24} {value:>9,}  {value / max(total, 1):>6.1%}")
        report["bands"][label] = {
            "eligible_groupings": int(len(in_band)), "failing": int(len(failing)),
            "classified": int(len(picked)), "checks": total, "succeeded": found,
            "missing_members": missing_votes, "extras_over_tol": extras_votes,
            "not_eligible": ineligible,
        }

    print("\nC5(c)  WHERE MID-SIZE CANDIDATES (51-500) ARE LOST")
    material = load_material(
        trees / "completions" / cut_key(cap, INCLUSION_CUT) / "real_r00001-00200.npz"
    )
    comp_sizes = np.bitwise_count(material.blocks).sum(axis=1).astype(np.int64)
    mid_pool = int(((sizes >= MID[0]) & (sizes <= MID[1])).sum())
    mid_completed = int(((comp_sizes >= MID[0]) & (comp_sizes <= MID[1])).sum())
    gated = np.array([
        thresholds[stratum_of(int(s))] is not None
        and round(float(v), 6) >= thresholds[stratum_of(int(s))]
        for s, v in zip(comp_sizes, material.supports, strict=True)
    ])
    mid_gated = int(((comp_sizes >= MID[0]) & (comp_sizes <= MID[1]) & gated).sum())
    final = np.array(theme_sizes(root / ARMS["THEMA"]))
    mid_final = int(((final >= MID[0]) & (final <= MID[1])).sum())
    over_cap = int((comp_sizes > cap).sum())
    print(f"    candidate groupings 51-500 in the pool        {mid_pool:>9,}")
    print(f"    completed families 51-500                     {mid_completed:>9,}")
    print(f"    ... through the support gate                  {mid_gated:>9,}")
    print(f"    ... surviving consensus, in the final build   {mid_final:>9,}")
    print(f"    (completed families over the {cap:,} cap, any size: {over_cap})")
    print(f"    SUPPORT GATE removes {mid_completed - mid_gated:,} of {mid_completed:,} "
          f"({1 - mid_gated / max(mid_completed, 1):.1%}) -- the dominant loss")
    print(f"    CONSENSUS then changes {mid_gated:,} to {mid_final:,}")
    report["losses"] = {
        "pool_51_500": mid_pool, "completed_51_500": mid_completed,
        "through_gate_51_500": mid_gated, "final_51_500": mid_final,
        "completed_over_cap_any_size": over_cap, "size_cap": cap,
        "cap_share": CAP_SHARE, "declared_m": DECLARED_M,
    }
    return report


if __name__ == "__main__":
    raise SystemExit(main())
