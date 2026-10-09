#!/usr/bin/env python3
"""Why near-duplicate themes survive a 0.70 merge. Diagnosis only -- writes no build.

``thema_L`` has 38.6% of themes with another theme at Jaccard > 0.7, and ``L_cal8`` 66%, although
consensus merges at ``THETA_MERGE`` 0.70. This splits those pairs by kind, re-runs consensus in
memory to see what it actually did, and counts what a merge applied as the very last step would
change. Nothing is written to any ontology directory.

Three measurements:

1. **The split.** A pair at Jaccard > 0.7 is either **nested** -- one theme strictly contains the
   other -- or **non-nested overlapping**. ``consensus.classify`` tests ``Rule.NESTED`` *before* it
   ever computes a Jaccard, so a nested pair is kept deliberately at any similarity: it is an edge
   for ``hasse`` to draw, not a duplicate. Only the non-nested pairs are ones the 0.70 rule was
   supposed to catch.
2. **What consensus did.** Re-running it on the cached gated candidates recovers ``superseded``,
   ``grew`` and ``inherited``, which no build writes out. Growth is the thing to look for: a stack
   theme that grows after acceptance is never re-compared against the themes already beside it.
3. **A final-step merge.** Greedily superseding on the FINAL memberships, lower support first, to
   count how many themes a last-step merge would remove. Counts only.

Usage::

    uv run scripts/twins_diagnosis.py --arm thema_L --arm thema_L_cal8
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

#: The merge threshold under diagnosis.
THETA = 0.70
#: Examples printed per kind.
EXAMPLES = 3


def read_build(path: Path) -> tuple[list[str], list[set[str]], list[float]]:
    """Node ids, member sets and supports.

    Args:
        path: A built ontology directory.

    Returns:
        ``(node ids, member key sets, supports)`` in a stable order.
    """
    members: dict[str, set[str]] = defaultdict(set)
    with (path / "members.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    support: dict[str, float] = {}
    with (path / "nodes.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            node = row.get("node") or row.get("id")
            support[node] = float(row.get("support") or 0.0)
    order = sorted(members)
    return order, [members[n] for n in order], [support.get(n, 0.0) for n in order]


def pairs_above(sets: list[set[str]], theta: float) -> list[tuple[int, int, float]]:
    """Every pair whose Jaccard exceeds ``theta``.

    From an inverted index, so only pairs sharing a member are compared.

    Args:
        sets: Member sets.
        theta: Threshold.

    Returns:
        ``(i, j, jaccard)`` with ``i < j``.
    """
    holders: dict[str, list[int]] = defaultdict(list)
    for index, keys in enumerate(sets):
        for key in keys:
            holders[key].append(index)
    out: list[tuple[int, int, float]] = []
    for index, keys in enumerate(sets):
        for other in {o for k in keys for o in holders[k]}:
            if other <= index:
                continue
            inter = len(keys & sets[other])
            union = len(keys) + len(sets[other]) - inter
            if union and inter / union > theta:
                out.append((index, other, inter / union))
    return out


def final_merge_counts(sets: list[set[str]], supports: list[float],
                       theta: float) -> dict[str, int]:
    """How many themes a greedy last-step merge would remove.

    The rule mirrors ``consensus.classify``: strict containment is kept as hierarchy, and a
    non-nested pair at or above ``theta`` has its lower-support member dropped. Applied to FINAL
    memberships in one pass, lower support considered last, so nothing grows and nothing is
    re-compared.

    Args:
        sets: Final member sets.
        supports: Support per theme.
        theta: Merge threshold.

    Returns:
        Counts only.
    """
    order = sorted(range(len(sets)), key=lambda i: (-supports[i], -len(sets[i])))
    holders: dict[str, list[int]] = defaultdict(list)
    for index, keys in enumerate(sets):
        for key in keys:
            holders[key].append(index)
    alive: set[int] = set()
    dropped_nested = dropped_overlap = 0
    for index in order:
        keys = sets[index]
        verdict = None
        for other in {o for k in keys for o in holders[k]}:
            if other not in alive:
                continue
            kept = sets[other]
            inter = len(keys & kept)
            if not inter:
                continue
            union = len(keys) + len(kept) - inter
            if inter == len(keys) < len(kept) or inter == len(kept) < len(keys):
                continue  # strict containment: hierarchy, never merged
            if union and inter / union >= theta:
                verdict = "overlap" if inter not in (len(keys), len(kept)) else "nested"
                break
        if verdict is None:
            alive.add(index)
        elif verdict == "nested":
            dropped_nested += 1
        else:
            dropped_overlap += 1
    return {"themes_before": len(sets), "themes_after": len(alive),
            "dropped_identical_or_equal": dropped_nested,
            "dropped_non_nested_overlap": dropped_overlap}


def main(argv: list[str] | None = None) -> int:
    """Run the diagnosis for each arm.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.4-leaves")
    parser.add_argument("--arm", action="append", default=["thema_L", "thema_L_cal8"])
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    from thema.data.pathways import PathwayCollection

    root = args.data / "ontology" / f"v{args.version}"
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8"))
    names = {p.key: p.name for p in collection.pathways}

    report: dict[str, object] = {"theta": THETA, "arms": {}}
    for arm in args.arm:
        path = root / arm
        if not (path / "members.tsv").is_file():
            print(f"{arm}: no build at {path}")
            continue
        ids, sets, supports = read_build(path)
        found = pairs_above(sets, THETA)
        nested = [(i, j, v) for i, j, v in found
                  if sets[i] < sets[j] or sets[j] < sets[i]]
        equal = [(i, j, v) for i, j, v in found if sets[i] == sets[j]]
        overlap = [(i, j, v) for i, j, v in found
                   if not (sets[i] <= sets[j] or sets[j] <= sets[i])]
        involved = {x for i, j, _v in found for x in (i, j)}

        print(f"=== {arm}: {len(sets):,} themes ===")
        print(f"  pairs at Jaccard > {THETA}: {len(found):,}")
        print(f"    nested (one strictly contains the other): {len(nested):,}"
              f"   {100 * len(nested) / max(len(found), 1):.1f}%")
        print(f"    identical member sets:                    {len(equal):,}")
        print(f"    NON-NESTED overlapping:                   {len(overlap):,}"
              f"   {100 * len(overlap) / max(len(found), 1):.1f}%")
        print(f"  themes in at least one such pair: {len(involved):,} "
              f"({100 * len(involved) / len(sets):.1f}% of themes)")

        for kind, rows in (("NESTED", nested), ("NON-NESTED OVERLAPPING", overlap),
                           ("IDENTICAL", equal)):
            if not rows:
                continue
            print(f"  {kind} examples:")
            for i, j, value in sorted(rows, key=lambda r: -r[2])[:EXAMPLES]:
                big, small = (i, j) if len(sets[i]) >= len(sets[j]) else (j, i)
                print(f"    J={value:.3f}  {ids[big]} n={len(sets[big])} "
                      f"support={supports[big]:.3f}   vs   {ids[small]} "
                      f"n={len(sets[small])} support={supports[small]:.3f}")
                shared = sorted(sets[big] & sets[small])[:3]
                print(f"       shared: {'; '.join(names.get(k, k) for k in shared)}")
                extra = sorted(sets[big] - sets[small])[:2]
                if extra:
                    print(f"       only in the larger: "
                          f"{'; '.join(names.get(k, k) for k in extra)}")
                only_small = sorted(sets[small] - sets[big])[:2]
                if only_small:
                    print(f"       only in the smaller: "
                          f"{'; '.join(names.get(k, k) for k in only_small)}")

        counts = final_merge_counts(sets, supports, THETA)
        print("  a merge applied as the LAST step, on final memberships:")
        gone = counts["themes_before"] - counts["themes_after"]
        print(f"    {counts['themes_before']:,} -> {counts['themes_after']:,} themes "
              f"({gone:,} removed, {100 * gone / counts['themes_before']:.1f}%)")
        print(f"    of which non-nested overlaps: {counts['dropped_non_nested_overlap']:,}; "
              f"identical/equal: {counts['dropped_identical_or_equal']:,}")
        print()
        report["arms"][arm] = {
            "themes": len(sets), "pairs_above_theta": len(found),
            "nested": len(nested), "identical": len(equal), "non_nested": len(overlap),
            "themes_involved": len(involved),
            "themes_involved_share": round(len(involved) / len(sets), 4),
            "final_merge": counts,
        }

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, default=float) + "\n",
                            encoding="utf-8")
        print(f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
