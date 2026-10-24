"""Merge by core, arms CI and CT. Prompt 58, declared 23 Oct 2026.

Exploratory. **No ontology is built** -- this runs as far as the merge and stops, and
nothing is adopted.

O50s decides that two groupings are versions of one theme by comparing their **completed sets**,
wobbly borders included (step 5's 10% rule). Aviyah's design compares their **cores** instead: a
grouping's matched copies at J >= 0.70 define an inclusion per pathway, the core is the pathways at
inclusion >= 0.9, and groupings with the same core are one theme.

Two arms differ only in what "the same core" means:

``CI``  identical cores.
``CT``  cores that pass O50s's twin test, ``recurrent.is_variant`` imported unchanged.

**The ordering is O50s's, and it is deliberately NOT the core's.** Seeds are taken in support
descending, then the grouping's own **completed-set** size descending, then the completed set's
bitset key -- exactly as ``recurrent.families`` ranks them. Only the merge *test* moves to the core.
That is why this does not simply call ``families`` with the cores as ``member_bits``: that would
rank by core size and core key as well, which would change which grouping seeds each theme. The
shortlist that keeps the CT walk off all-pairs is still the repo's own
``recurrent._variant_shortlist``, built on the cores, because it is documented as a superset of the
rule rather than a filter on it.

**Step 4's pooling is not O50s's.** ``family_members`` unions every copy a run holds of any family
member; this prompt specifies *the copy of the highest-support grouping found in that run*. The
origin convention is kept from O50s: a grouping's own run contributes the grouping's own bitset when
that run has no matched copy.

Usage:
    uv run scripts/core_merge.py --side      # pool, completions and cores, cached
    uv run scripts/core_merge.py             # both arms
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

THETA_MATCH = 0.70
CORE_CUT = 0.90
MEMBER_CUT = 0.50
MIN_CORE = 3


def side(args: argparse.Namespace) -> dict[str, object]:
    """The pool at J >= 0.70, with each grouping's completed set and core.

    Args:
        args: Parsed arguments.

    Returns:
        ``{pool, present, words, completed, cores, support}``.
    """
    from cut_trees import load_run
    from thema.ontology import bitset as bits
    from thema.ontology.recurrent import family_members_fast, prepare, score
    from thema.ontology.v04 import NO_CAP, settings_for

    meta = json.loads((args.space_root / "universe.json").read_text())
    n = meta["n_embedded"]
    trees = args.space_root / "trees" / f"{meta['space']}_{meta['universe_digest']}"
    labels = [f"row{r:05d}" for r in range(1, args.runs + 1)]
    clock = time.perf_counter()
    runs = [load_run(trees / f"{label}.npz", n, NO_CAP) for label in labels]
    conf = settings_for(len(runs), legacy=False, theta_match=THETA_MATCH)
    ready = prepare(np.zeros((n, 1), dtype=np.float32), n, conf, 0, records=list(runs))
    del runs
    pool = score(ready, conf)
    words = ready.present.shape[1] * bits.WORD
    print(f"  pool: {len(pool.groupings):,} groupings at J >= {THETA_MATCH} "
          f"({time.perf_counter() - clock:.0f}s)", flush=True)

    completed: dict[int, np.ndarray] = {}
    cores: dict[int, np.ndarray] = {}
    for g in range(len(pool.groupings)):
        if np.isnan(pool.support[g]):
            continue
        _cand, inclusion = family_members_fast([g], pool, ready.present, words)
        members = sorted(p for p, v in inclusion.items() if v >= MEMBER_CUT)
        core = sorted(p for p, v in inclusion.items() if v >= CORE_CUT)
        completed[g] = bits.pack(members, words)
        cores[g] = bits.pack(core, words)
    print(f"  completions and cores for {len(completed):,} eligible groupings "
          f"({time.perf_counter() - clock:.0f}s)", flush=True)
    return {"pool": pool, "present": ready.present, "eligible_mask": ready.eligible_mask,
            "words": words, "n": n, "completed": completed, "cores": cores, "meta": meta}


def merge(got: dict, arm: str) -> list[tuple[int, list[int]]]:
    """Step 3: seed absorption on cores, in O50s's completed-set order.

    Args:
        got: The side material.
        arm: ``"CI"`` or ``"CT"``.

    Returns:
        ``(seed, groupings including the seed)`` in rank order.
    """
    from thema.ontology import bitset as bits
    from thema.ontology.recurrent import _variant_shortlist, is_variant

    pool, completed, cores = got["pool"], got["completed"], got["cores"]
    core_size = {g: bits.count(cores[g]) for g in completed}
    have = [g for g in completed if core_size[g] >= MIN_CORE]
    support = np.nan_to_num(pool.support, nan=0.0)
    comp_size = {g: bits.count(completed[g]) for g in have}
    # O50s's order, on the COMPLETED set -- support, then its size, then its key.
    ranked = sorted(have, key=lambda g: (-support[g], -comp_size[g], bits.key(completed[g])))

    out: list[tuple[int, list[int]]] = []
    if arm == "CI":
        # Identical cores are an equivalence relation, so the greedy loop reduces to grouping by
        # the core's bytes; the seed is whichever member of the class ranks first.
        seen: dict[bytes, list[int]] = {}
        for g in ranked:
            seen.setdefault(cores[g].tobytes(), []).append(g)
        for g in ranked:
            key = cores[g].tobytes()
            family = seen.get(key)
            if family is None or family[0] != g:
                continue
            out.append((g, list(family)))
            del seen[key]
        return out

    shortlist = _variant_shortlist(have, lambda g: cores[g], core_size)
    claimed: set[int] = set()
    for seed in ranked:
        if seed in claimed:
            continue
        claimed.add(seed)
        taken: list[int] = []
        for other in shortlist.get(seed, ()):
            if other in claimed:
                continue
            if is_variant(cores[seed], cores[other]):
                claimed.add(other)
                taken.append(other)
        out.append((seed, [seed, *taken]))
    return out


def pool_theme(family: list[int], got: dict) -> tuple[np.ndarray, np.ndarray, dict[int, float]]:
    """Step 4: pooled copies, inclusions, core and members for one theme.

    The pooled copy of a run is the copy of the theme's **highest-support** grouping found in that
    run -- not the union O50s takes. A grouping's own origin run contributes the grouping's own
    bitset when that run holds no matched copy, which is O50s's convention in ``family_members``.

    Args:
        family: Grouping indices in the theme.
        got: The side material.

    Returns:
        ``(members bitset, core bitset, inclusion per pathway)``.
    """
    from thema.ontology import bitset as bits

    pool, present, words = got["pool"], got["present"], got["words"]
    support = np.nan_to_num(pool.support, nan=0.0)
    best: dict[int, tuple[float, np.ndarray]] = {}
    for g in family:
        value = float(support[g])
        for run, copy in pool.copies[g].items():
            if run not in best or value > best[run][0]:
                best[run] = (value, copy)
        for run in pool.origins[g]:
            if run not in best:
                best[run] = (value, pool.groupings[g])
    if not best:
        return bits.empty(words), bits.empty(words), {}
    runs = np.array(sorted(best), dtype=np.int64)
    stack = np.vstack([best[int(r)][1] for r in runs])
    candidates = stack[0].copy()
    for block in stack[1:]:
        candidates = candidates | block
    drawn = present[runs]
    inclusion: dict[int, float] = {}
    for p in bits.unpack(candidates):
        word, bit = p // bits.WORD, np.uint64(1) << np.uint64(p % bits.WORD)
        holds = int(np.count_nonzero(stack[:, word] & bit))
        could = int(np.count_nonzero(drawn[:, word] & bit))
        inclusion[p] = min(holds / could, 1.0) if could else 0.0
    members = bits.pack(sorted(p for p, v in inclusion.items() if v >= MEMBER_CUT), words)
    core = bits.pack(sorted(p for p, v in inclusion.items() if v >= CORE_CUT), words)
    return members, core, inclusion


def main(argv: list[str] | None = None) -> int:
    """Build both arms and write them.

    Args:
        argv: Command line.

    Returns:
        0.
    """
    from thema.ontology import bitset as bits
    from thema.ontology.recurrent import family_support

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/core_merge_2026-10-23"))
    parser.add_argument("--runs", type=int, default=200)
    parser.add_argument("--side", action="store_true", help="compute the side and stop")
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    print("PROMPT 58: MERGE BY CORE. Arms CI (identical cores) and CT (twin cores).")
    print("  no gate, no consensus, no repair, no edges -- the merge and nothing after it.")
    got = side(args)
    pool = got["pool"]

    # --- the no-core census -------------------------------------------------------------------
    core_size = {g: bits.count(got["cores"][g]) for g in got["completed"]}
    comp_size = {g: bits.count(got["completed"][g]) for g in got["completed"]}
    nocore = [g for g in got["completed"] if core_size[g] < MIN_CORE]
    print(f"  eligible groupings {len(got['completed']):,}; without a core of "
          f"{MIN_CORE}+ : {len(nocore):,}", flush=True)
    if args.side:
        return 0

    for arm in ("CI", "CT"):
        clock = time.perf_counter()
        families = merge(got, arm)
        print(f"  {arm}: {len(families):,} themes from "
              f"{sum(len(f) for _s, f in families):,} groupings "
              f"({time.perf_counter() - clock:.0f}s)", flush=True)
        rows = []
        members_stack = []
        cores_stack = []
        for seed, family in families:
            members, core, _incl = pool_theme(family, got)
            size = bits.count(members)
            if not size:
                continue
            cores_stack.append(core)
            rows.append({
                "seed": int(seed), "groupings": len(family),
                "size": int(size), "core_size": int(bits.count(core)),
                "support": round(float(family_support(family, pool, got["eligible_mask"])), 6),
                "seed_completed_size": int(comp_size[seed]),
                "seed_core_size": int(core_size[seed]),
            })
            members_stack.append(members)
        stack = np.vstack(members_stack)
        np.savez_compressed(args.out / f"themes_{arm}.npz", members=stack,
                            cores=np.vstack(cores_stack),
                            size=np.array([r["size"] for r in rows], dtype=np.int32),
                            core_size=np.array([r["core_size"] for r in rows], dtype=np.int32),
                            support=np.array([r["support"] for r in rows], dtype=np.float64),
                            groupings=np.array([r["groupings"] for r in rows], dtype=np.int32),
                            seed=np.array([r["seed"] for r in rows], dtype=np.int64))
        print(f"    -> {args.out / f'themes_{arm}.npz'}  ({len(rows):,} themes with members)",
              flush=True)

    census: dict[str, int] = {}
    for g in nocore:
        band = ("3-5" if comp_size[g] <= 5 else "6-11" if comp_size[g] <= 11
                else "12-24" if comp_size[g] <= 24 else "25-49" if comp_size[g] <= 49
                else "50-99" if comp_size[g] <= 99 else "100-199" if comp_size[g] <= 199
                else "200-399" if comp_size[g] <= 399 else "400-799" if comp_size[g] <= 799
                else "800-1599" if comp_size[g] <= 1599 else "1600+")
        census[band] = census.get(band, 0) + 1
    (args.out / "arms.json").write_text(json.dumps({
        "theta_match": THETA_MATCH, "core_cut": CORE_CUT, "member_cut": MEMBER_CUT,
        "min_core": MIN_CORE,
        "n_groupings": int(len(pool.groupings)),
        "n_eligible": len(got["completed"]),
        "n_no_core": len(nocore), "no_core_by_band": census,
        "order": "support desc, then the grouping's own completed-set size desc, then its key",
        "pooling": "per run, the copy of the theme's highest-support grouping found in that run",
    }, indent=1) + "\n", encoding="utf-8")
    print(f"  -> {args.out / 'arms.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
