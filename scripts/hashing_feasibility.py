#!/usr/bin/env python3
"""C7: could one fingerprint at Jaccard >= 0.70 recover a grouping's copies? MEASUREMENT ONLY.

A hash-based shortcut to matching would only work if copies of the same grouping in different runs
are already similar enough to collide at the matching threshold. This measures how similar they
actually are. **Nothing is implemented from it, and no approximate matching is used anywhere in the
build.**

Two readings were asked for:

- **(a) raw sampled members** -- the copies as the runs produced them. Two independent 80% draws
  share about 64% of the universe, so even a perfectly stable group should score near
  0.8 x 0.8 / (1 - 0.2 x 0.2) = 0.67 from sampling alone.
- **(b) completed full-universe members** -- **NOT APPLICABLE.** A4 established that completion does
  not extend a grouping to the full universe: candidates are the union of the matched copies, and
  the unsampled remainder is handled in the inclusion DENOMINATOR, not by assignment. The nearest
  measurable thing is reported instead: the Jaccard between each copy and the family's COMPLETED
  member set, which is what a fingerprint would have to match if it were computed after completion.

Usage::

    uv run scripts/hashing_feasibility.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

#: How many groupings to sample, and the support floor for inclusion in the sample.
SAMPLE = 500
MIN_SUPPORT = 0.5
SAMPLE_SEED = 20261005

#: The matching threshold a fingerprint would have to reproduce.
THRESHOLD = 0.70


def main(argv: list[str] | None = None) -> int:
    """Measure copy-to-copy similarity.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    from build_10770 import INCLUSION_CUT, cut_key
    from cut_trees import MIN_SIZE, THETA, TOL, cap_for, load_run
    from thema.ontology import bitset as bits
    from thema.ontology.recurrent import DEFAULTS, family_members_fast, prepare, score

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--space", default="centred")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    meta = json.loads((root / "universe.json").read_text())
    universe, n = meta["universe_digest"], meta["n_embedded"]
    cap = cap_for(n)
    trees = root / "trees" / f"{args.space}_{universe}"
    runs = [load_run(trees / f"row{r:05d}.npz", n, cap) for r in range(1, 201)]
    settings = {**DEFAULTS, "runs": len(runs), "tol": TOL, "min_size": MIN_SIZE, "theta": THETA}
    ready = prepare(np.zeros((n, 1), dtype=np.float32), n, settings, 0, records=runs)
    pool = score(ready, settings)
    words = ready.present.shape[1] * bits.WORD
    print(f"C7  pool of {len(pool.groupings):,} groupings, 200 runs, "
          f"cut_key {cut_key(cap, INCLUSION_CUT)}")

    eligible = np.flatnonzero(
        ~np.isnan(pool.support) & (np.nan_to_num(pool.support) >= MIN_SUPPORT)
    )
    rng = np.random.default_rng(SAMPLE_SEED)
    picked = rng.choice(eligible, size=min(SAMPLE, len(eligible)), replace=False)
    print(f"  {len(eligible):,} groupings at support >= {MIN_SUPPORT}; "
          f"sampling {len(picked):,} (seed {SAMPLE_SEED})")

    raw: list[float] = []
    completed_vs_copy: list[float] = []
    copies_per = []
    for g in picked:
        blocks = list(pool.copies[g].values())
        copies_per.append(len(blocks))
        if len(blocks) < 2:
            continue
        stack = np.vstack(blocks)
        sizes = np.bitwise_count(stack).sum(axis=1).astype(np.int64)
        # Every distinct pair of copies, which is what a fingerprint would have to collide on.
        for i in range(len(blocks)):
            inter = np.bitwise_count(stack[i + 1:] & stack[i]).sum(axis=1).astype(np.int64)
            union = sizes[i] + sizes[i + 1:] - inter
            raw.extend((inter / np.maximum(union, 1)).tolist())
        full, inclusion = family_members_fast([int(g)], pool, ready.present, words)
        members = sorted(p for p in bits.unpack(full)
                         if inclusion.get(p, 0.0) >= INCLUSION_CUT)
        packed = bits.pack(members, words)
        size_full = len(members)
        inter = np.bitwise_count(stack & packed).sum(axis=1).astype(np.int64)
        union = sizes + size_full - inter
        completed_vs_copy.extend((inter / np.maximum(union, 1)).tolist())

    raw_arr = np.array(raw)
    comp_arr = np.array(completed_vs_copy)
    expected = 0.8 * 0.8 / (1 - 0.2 * 0.2)
    print(f"\n  (a) COPY vs COPY, raw sampled members -- {len(raw_arr):,} pairs")
    print(f"      median {np.median(raw_arr):.3f}   mean {raw_arr.mean():.3f}   "
          f"p10 {np.percentile(raw_arr, 10):.3f}   p90 {np.percentile(raw_arr, 90):.3f}")
    print(f"      share at or above {THRESHOLD}: {float((raw_arr >= THRESHOLD).mean()):.1%}")
    print(f"      sampling-only expectation for a perfectly stable group: {expected:.3f}")
    print(f"\n  (b) COPY vs COMPLETED family set -- {len(comp_arr):,} pairs")
    print("      A4: completion does NOT produce full-universe members, so the literal (b) does")
    print("      not exist. This is the nearest measurable quantity.")
    print(f"      median {np.median(comp_arr):.3f}   mean {comp_arr.mean():.3f}   "
          f"share >= {THRESHOLD}: {float((comp_arr >= THRESHOLD).mean()):.1%}")

    verdict_a = float((raw_arr >= THRESHOLD).mean())
    verdict_b = float((comp_arr >= THRESHOLD).mean())
    print(f"\n  WOULD ONE GLOBAL FINGERPRINT AT JACCARD >= {THRESHOLD} RECOVER TRUE COPIES?")
    print(f"    under (a): {'yes' if verdict_a > 0.9 else 'NO'} -- it would find "
          f"{verdict_a:.1%} of true copy pairs and miss {1 - verdict_a:.1%}")
    print(f"    under (b): {'yes' if verdict_b > 0.9 else 'NO'} -- {verdict_b:.1%} of "
          f"copy-to-completed pairs reach the threshold")
    print("    The build's rule is NOT a plain Jaccard on raw members: it restricts both sides to")
    print("    what the origin run drew, which is exactly the correction a global fingerprint")
    print("    cannot make.")

    report = {
        "sample": int(len(picked)), "sample_seed": SAMPLE_SEED,
        "min_support": MIN_SUPPORT, "threshold": THRESHOLD,
        "copies_per_grouping_median": float(np.median(copies_per)),
        "raw": {"pairs": int(len(raw_arr)), "median": round(float(np.median(raw_arr)), 4),
                "mean": round(float(raw_arr.mean()), 4),
                "p10": round(float(np.percentile(raw_arr, 10)), 4),
                "p90": round(float(np.percentile(raw_arr, 90)), 4),
                "share_at_threshold": round(verdict_a, 4),
                "sampling_only_expectation": round(expected, 4)},
        "copy_vs_completed": {"pairs": int(len(comp_arr)),
                              "median": round(float(np.median(comp_arr)), 4),
                              "share_at_threshold": round(verdict_b, 4)},
        "literal_b_applicable": False,
        "why": "A4: completion unions the matched copies; it does not extend to the full universe",
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"\n  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
