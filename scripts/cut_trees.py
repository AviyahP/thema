#!/usr/bin/env python3
"""Load persisted Ward trees, apply the size cap at CUT time, and measure grouping-pool agreement.

The trees were built once and written without a cap, because a cap is a decision about which
dendrogram nodes become candidate clusters -- a cut-time choice. This reads them back, drops every
recorded cluster above the cap, and rebuilds the per-run index the matching loop needs. The same
function is used for real and scrambled sides, so the support floors are solved under exactly the
rule they will be applied under.

**`--ladder` DOES NOT TEST THE RUNS RULE. Do not read its output as if it did.** The rule, as
defined 25 Sep, is ">= 90% of FINAL THEMES matched at Jaccard >= 0.70 between builds from disjoint
tree blocks". What `--ladder` matches is the **raw grouping pool** -- every deduplicated Ward
cluster at or above `min_size`, before completion, before the support gate, before consensus. Half
of that pool is a cluster one subsample produced and no other run reproduced, so the 90% mark means
nothing over it. Measuring the rule needs two full builds compared with `scripts/theme_match.py`;
see `DECISIONS.md`, 2 Oct, "The RUNS rule was always about FINAL THEMES".

What `--ladder` is still good for: grouping-pool agreement is a real property of the method, it is
cheap, and it is what `scripts/ladder_diagnostic.py` breaks down by support. It is kept for that.

`load_run` is the reusable part and carries no such caveat: it is how every caller applies the cap.

Usage::

    uv run scripts/cut_trees.py --ladder     # grouping-pool agreement, NOT the RUNS rule
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from thema.ontology import bitset as bits
from thema.ontology.recurrent import DEFAULTS, Run, prepare, score

#: The declared cap, as a SHARE of the universe. 2 x Reactome Signal Transduction's 469/3,233 =
#: 14.5067%, excluding Disease as a cross-cutting pathology bucket. See DECISIONS.md, 2 Oct.
#: Stated as a share so it transfers to any universe size; the pathway count is derived.
CAP_SHARE = 2 * 469 / 3233

#: Matching parameters of the current setup. theta is the Jaccard the ladder reports at.
THETA = 0.70
TOL = 0.15
MIN_SIZE = 3


def cap_for(n: int) -> int:
    """The cap in pathways for a universe of this size.

    Args:
        n: Universe size.

    Returns:
        Rounded member count. 3,125 at 10,770.
    """
    return round(CAP_SHARE * n)


def load_run(path: Path, n: int, cap: int) -> Run:
    """Read one persisted tree and apply the size cap.

    Clusters above the cap are removed and every derived index is rebuilt from the survivors: the
    parent chain, the per-pathway smallest-cluster pointer and the CSR ancestor chains all carry
    cluster INDICES, so dropping a cluster without renumbering them would silently point the
    matching loop at the wrong cluster.

    Args:
        path: The ``.npz`` written by ``build_trees_10770.py``.
        n: Universe size.
        cap: Largest cluster size that remains a candidate.

    Returns:
        The capped run.
    """
    with np.load(path) as handle:
        present = handle["present"]
        clusters = handle["clusters"]
        sizes = handle["sizes"]
        parent = handle["parent"]
    keep = np.flatnonzero(sizes <= cap)
    if len(keep) == len(sizes):
        renumber = np.arange(len(sizes), dtype=np.int32)
    else:
        renumber = np.full(len(sizes), -1, dtype=np.int32)
        renumber[keep] = np.arange(len(keep), dtype=np.int32)
    kept_clusters = clusters[keep]
    kept_sizes = sizes[keep]
    # A dropped cluster's children must inherit its nearest surviving ancestor, not -1: the chain is
    # what an ancestor walk climbs, and breaking it would make a grouping unmatchable.
    old_parent = parent
    new_parent = np.full(len(keep), -1, dtype=np.int32)
    for position, old in enumerate(keep):
        up = old_parent[old]
        while up >= 0 and renumber[up] < 0:
            up = old_parent[up]
        new_parent[position] = renumber[up] if up >= 0 else -1
    # leaf_cluster and the CSR chains are rebuilt from the surviving clusters directly, which is
    # cheaper and less error-prone than patching the stored ones.
    holders: list[list[int]] = [[] for _ in range(n)]
    for position in range(len(keep)):
        for pathway in bits.unpack(kept_clusters[position]):
            holders[pathway].append(position)
    order = np.argsort(kept_sizes, kind="stable")
    rank = np.empty(len(keep), dtype=np.int64)
    rank[order] = np.arange(len(keep))
    leaf_cluster = np.full(n, -1, dtype=np.int32)
    chain_indptr = np.zeros(n + 1, dtype=np.int64)
    chain: list[int] = []
    for pathway in range(n):
        got = sorted(holders[pathway], key=lambda c: rank[c])
        if got:
            leaf_cluster[pathway] = got[0]
        chain.extend(got)
        chain_indptr[pathway + 1] = len(chain)
    return Run(
        present=present,
        clusters=kept_clusters,
        parent=new_parent,
        leaf_cluster=leaf_cluster,
        sizes=kept_sizes,
        chain_indptr=chain_indptr,
        chain_idx=np.asarray(chain, dtype=np.int32),
    )


#: How many groupings are sampled from each side when estimating the matched share, and the seed.
#: The exhaustive match is quadratic in the pool, and at 10,770 the pool is ~407,000 groupings per
#: 100 runs: 407k x 407k x 169 words is 2.8e13 word-operations, about 7.8 HOURS for one pair. At
#: 1,850 the pools were ~45k and it was merely slow, which is why this only surfaces now.
#:
#: A random sample of the LEFT side against the WHOLE right side is an unbiased estimator of the
#: matched share, and 5,000 draws put the standard error on a 90% proportion at 0.42% -- far inside
#: the margin a 90% pass mark needs. The sample is reported with its error rather than quoted as
#: if exhaustive.
SAMPLE = 5000
SAMPLE_SEED = 20261002


def jaccard_match(
    left: np.ndarray, right: np.ndarray, theta: float, sample: int = SAMPLE
) -> tuple[float, float, int]:
    """Estimate the share of ``left``'s groupings having a ``right`` match at Jaccard >= theta.

    Every sampled grouping is compared against ALL of ``right``, so the only approximation is which
    left-hand groupings are examined. Exhaustive when ``left`` is no larger than the sample.

    Args:
        left: ``(a, words)`` grouping bitsets.
        right: ``(b, words)`` grouping bitsets.
        theta: The Jaccard threshold.
        sample: How many of ``left`` to draw; 0 or more than ``len(left)`` means all of it.

    Returns:
        The matched share, its standard error, and how many were examined. The error is 0.0 when
        the comparison was exhaustive.
    """
    if not len(left) or not len(right):
        return 0.0, 0.0, 0
    rng = np.random.default_rng(SAMPLE_SEED)
    if sample and sample < len(left):
        picked = rng.choice(len(left), size=sample, replace=False)
        exhaustive = False
    else:
        picked = np.arange(len(left))
        exhaustive = True
    sizes_right = np.bitwise_count(right).sum(axis=1).astype(np.int64)
    matched = 0
    for index in picked:
        block = left[index]
        size = int(np.bitwise_count(block).sum())
        inter = np.bitwise_count(right & block).sum(axis=1).astype(np.int64)
        union = size + sizes_right - inter
        best = np.max(np.where(union > 0, inter / np.maximum(union, 1), 0.0))
        matched += best >= theta
    share = matched / len(picked)
    error = 0.0 if exhaustive else float(np.sqrt(share * (1 - share) / len(picked)))
    return share, error, len(picked)


def main(argv: list[str] | None = None) -> int:
    """Re-confirm RUNS from the persisted trees under the current setup.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--space", default="centred")
    parser.add_argument("--ladder", action="store_true")
    parser.add_argument("--pass-mark", type=float, default=0.90)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    universe = json.loads((root / "universe.json").read_text())["universe_digest"]
    n = json.loads((root / "universe.json").read_text())["n_embedded"]
    trees = root / "trees" / f"{args.space}_{universe}"
    cap = cap_for(n)
    print(f"CUTTING  {n:,} pathways, {args.space}, cap {CAP_SHARE:.4%} = {cap:,} pathways")

    if args.ladder:
        pairs = [((1, 100), (101, 200)), ((1, 200), (201, 400))]
        needed = max(b for _a, (_x, b) in pairs)
        have = sorted(trees.glob("row*.npz"))
        if len(have) < needed:
            print(f"  only {len(have)} real trees persisted; need {needed}")
            return 1
        cache: dict[int, Run] = {}

        def pool_for(low: int, high: int) -> np.ndarray:
            runs = []
            for row in range(low, high + 1):
                if row not in cache:
                    cache[row] = load_run(trees / f"row{row:05d}.npz", n, cap)
                runs.append(cache[row])
            # prepare() with records=: the Ward stage is skipped and the dedup and eligibility
            # code is the one every other build uses. A hand-written copy got the Prepared field
            # order wrong on the first attempt, which is the drift this avoids.
            settings = {**DEFAULTS, "runs": len(runs), "tol": TOL,
                        "min_size": MIN_SIZE, "theta": THETA}
            ready = prepare(np.zeros((n, 1), dtype=np.float32), n, settings, 0, records=runs)
            pool = score(ready, settings)
            keep = ~np.isnan(pool.support)
            return ready.groupings[keep]

        print(f"  theta {THETA}, tol {TOL}, reference mark {args.pass_mark:.0%}")
        print("  NOTE: this is the RAW GROUPING POOL, not final themes. The RUNS rule is about "
              "themes;\n        see DECISIONS.md 2 Oct. Do not read a verdict on RUNS from this.",
              flush=True)
        results = []
        for (al, ah), (bl, bh) in pairs:
            start = time.perf_counter()
            left, right = pool_for(al, ah), pool_for(bl, bh)
            forward, fe, fn = jaccard_match(left, right, THETA)
            backward, be, bn = jaccard_match(right, left, THETA)
            both = min(forward, backward)
            results.append({
                "left": f"{al}-{ah}", "right": f"{bl}-{bh}",
                "n_left": int(len(left)), "n_right": int(len(right)),
                "forward": round(forward, 4), "forward_se": round(fe, 5), "forward_n": fn,
                "backward": round(backward, 4), "backward_se": round(be, 5), "backward_n": bn,
                "worse_direction": round(both, 4),
                "seconds": round(time.perf_counter() - start, 1),
            })
            print(f"  {al}-{ah} vs {bl}-{bh}: {len(left):,} vs {len(right):,} groupings, "
                  f"{fn:,} sampled per direction", flush=True)
            print(f"      forward {forward:.1%} +/- {fe:.2%}   backward {backward:.1%} "
                  f"+/- {be:.2%}   worse {both:.1%}   "
                  f"{'over' if both >= args.pass_mark else 'under'} "
                  f"{args.pass_mark:.0%} (reference only)   "
                  f"({time.perf_counter() - start:.0f}s)", flush=True)
        out = trees / "ladder.json"
        out.write_text(json.dumps({
            "space": args.space, "universe_digest": universe, "n": n,
            "cap_share": CAP_SHARE, "cap": cap, "theta": THETA, "tol": TOL,
            "min_size": MIN_SIZE, "pass_mark": args.pass_mark,
            "sample": SAMPLE, "sample_seed": SAMPLE_SEED, "pairs": results,
        }, indent=2) + "\n", encoding="utf-8")
        print(f"  -> {out}")
        worst = min(r["worse_direction"] for r in results)
        print(f"\n  grouping-pool agreement, worst direction {worst:.1%}. This is NOT a "
              f"verdict on RUNS=200:\n  the rule is about final themes -- use "
              f"scripts/theme_match.py on two full builds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
