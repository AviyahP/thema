#!/usr/bin/env python3
"""Does chain collapse keep the more stable node? Measured, with a post-hoc alternative. Read-only.

Item 5 of the 9 Oct follow-up. The declared chain rule keeps the **parent's membership** -- the
containing set -- and takes the higher of the two supports. That is a statement about membership, so
the node that survives as a *node* is the parent, whatever its own support was. On the ``n00150``
lattice three of the four collapses at 0.85 absorb a node whose support is higher than the parent's.

Two measurements:

**(a)** Over every chain edge with ratio in ``[0.85, 0.90)``, how often is the absorbed child's
support higher than the surviving parent's.

**(b)** The ``n00150`` lattice under the current survivor rule against a **post-hoc** alternative --
keep the higher-support node, ties to the parent. **Labelled post-hoc: it was written after seeing
that three of four collapses drop the more stable node, so it is not a pre-registered rule and its
result is not evidence for it.**

Nothing is applied. Usage::

    uv run scripts/chain_survivor.py --stats STATS.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

LO, HI = 0.85, 0.90
FOCUS = "n00150"
GIANT = 1000
SHARE = 0.85
MAX_ROUNDS = 50


def main(argv: list[str] | None = None) -> int:
    """Measure 5a and 5b."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.4-leaves")
    parser.add_argument("--build", default="thema_L_repair")
    parser.add_argument("--stats", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    path = root / args.build
    stats = json.loads(args.stats.read_text())["nodes"]
    members: dict[str, set[str]] = defaultdict(set)
    with (path / "members.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    support: dict[str, float] = {}
    with (path / "nodes.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            support[row.get("node") or row.get("id")] = float(row.get("support") or 0.0)
    parents: dict[str, set[str]] = defaultdict(set)
    with (path / "edges.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            parents[row["child"]].add(row["parent"])
    sizes = {n: len(k) for n, k in members.items()}

    def gist(node: str, n: int = 3) -> str:
        """Nearest member names."""
        return "; ".join((stats.get(node, {}).get("nearest") or [])[:n])

    # ---- 5a
    edges = [(c, p, sizes[c] / sizes[p]) for c, ups in parents.items() for p in ups]
    window = [(c, p, r) for c, p, r in edges if LO <= r < HI]
    higher = [(c, p, r) for c, p, r in window if support.get(c, 0) > support.get(p, 0)]
    lower = [(c, p, r) for c, p, r in window if support.get(c, 0) < support.get(p, 0)]
    equal = [(c, p, r) for c, p, r in window if support.get(c, 0) == support.get(p, 0)]
    print(f"5a. CHAIN EDGES with ratio in [{LO}, {HI}): {len(window):,}")
    print(f"    absorbed child's support HIGHER than the surviving parent's: "
          f"{len(higher):,} ({100 * len(higher) / len(window):.1f}%)")
    print(f"    lower:  {len(lower):,} ({100 * len(lower) / len(window):.1f}%)")
    print(f"    equal:  {len(equal):,} ({100 * len(equal) / len(window):.1f}%)")
    gaps = [support.get(c, 0) - support.get(p, 0) for c, p, _r in higher]
    if gaps:
        print(f"    where the child is higher, median gap {np.median(gaps):+.3f}, "
              f"max {max(gaps):+.3f}")
    print(f"    so the declared rule keeps the LESS stable node on "
          f"{100 * len(higher) / len(window):.1f}% of edges in this window")

    # ---- 5b, on the focus lattice
    all_up: set[str] = set()
    frontier = set(parents[FOCUS])
    while frontier:
        all_up |= frontier
        frontier = {u for n in frontier for u in parents.get(n, ())} - all_up
    giants = {a for a in all_up if sizes[a] >= GIANT}
    scope = sorted(all_up - giants, key=lambda a: sizes[a])

    def collapse(keep_higher_support: bool) -> list[tuple[str, str, float, str]]:
        """Run the 0.85 collapse under one survivor rule.

        Args:
            keep_higher_support: Post-hoc alternative when True; the declared rule when False.

        Returns:
            ``(absorbed, survivor, ratio, which_rule_chose)`` per collapse.
        """
        alive = set(scope)
        up = {n: {x for x in parents.get(n, ()) if x in scope} for n in scope}
        down: dict[str, set[str]] = defaultdict(set)
        for n, ups in up.items():
            for q in ups:
                down[q].add(n)
        out: list[tuple[str, str, float, str]] = []
        for _ in range(MAX_ROUNDS):
            doomed: dict[str, tuple[str, float]] = {}
            for child in sorted(alive, key=lambda x: sizes[x]):
                best: tuple[str, int] | None = None
                for parent in up.get(child, ()):
                    if parent not in alive or parent == child:
                        continue
                    if not members[child] < members[parent]:
                        continue
                    if sizes[child] >= SHARE * sizes[parent]:
                        if best is None or sizes[parent] < best[1]:
                            best = (parent, sizes[parent])
                if best is not None:
                    doomed[child] = (best[0], sizes[child] / sizes[best[0]])
            progressed = False
            for c in sorted(doomed, key=lambda x: sizes[x]):
                if c not in alive:
                    continue
                target, ratio = doomed[c]
                while target not in alive:
                    nxt = [t for t in up.get(target, ()) if t in alive]
                    if not nxt:
                        target = None
                        break
                    target = min(nxt, key=lambda t: sizes[t])
                if target is None or target == c:
                    continue
                # Which node survives as a NODE.
                if keep_higher_support and support.get(c, 0) > support.get(target, 0):
                    gone, kept, why = target, c, "child kept (higher support)"
                else:
                    gone, kept, why = c, target, ("parent kept (tie)"
                                                  if keep_higher_support else "parent kept (rule)")
                alive.discard(gone)
                out.append((gone, kept, ratio, why))
                for kid in down.get(gone, ()):
                    up.setdefault(kid, set()).add(kept)
                    down[kept].add(kid)
                progressed = True
            if not progressed:
                break
        return out

    print(f"\n5b. the {FOCUS} lattice at share {SHARE}: {len(scope)} non-giant ancestors")
    results = {}
    for label, flag in (("declared rule (parent's membership survives)", False),
                        ("POST-HOC: keep the higher-support node, tie -> parent", True)):
        got = collapse(flag)
        kept_more_stable = sum(
            1 for gone, kept, _r, _w in got if support.get(kept, 0) >= support.get(gone, 0))
        print(f"\n  {label}")
        print(f"    {len(got)} collapses; the surviving node is the more stable one in "
              f"{kept_more_stable} of {len(got)}")
        for gone, kept, r, why in got:
            print(f"      drops {gone} (support {support.get(gone, 0):.3f}) -> "
                  f"keeps {kept} ({support.get(kept, 0):.3f})  ratio {r:.3f}  [{why}]")
            print(f"        {gist(kept)[:72]}")
        results[label] = [{"dropped": g, "kept": k, "ratio": round(r, 4), "why": w,
                           "dropped_support": support.get(g), "kept_support": support.get(k)}
                          for g, k, r, w in got]

    # ---- 6, the unique-contribution idea, measured not adopted
    six = sorted(parents[FOCUS], key=lambda p: -support.get(p, 0.0))
    print("\n6. UNIQUE-CONTRIBUTION TEST (idea, NOT adopted): remove a fan parent only if every "
          "member it adds is already in a co-parent")
    removable = []
    for p in six:
        added = members[p] - members[FOCUS]
        others = set().union(*(members[q] - members[FOCUS] for q in six if q != p))
        unique = added - others
        print(f"    {p} (support {support.get(p, 0):.3f}) adds {len(added)}, "
              f"{len(unique)} of them unique to it"
              + (f": {sorted(unique)}" if unique else " -> REMOVABLE"))
        if not unique:
            removable.append(p)
    print(f"    removes {len(removable)} of {len(six)} parents"
          + (f": {removable}" if removable else " -- none"))

    report = {"window": [LO, HI], "n_edges_in_window": len(window),
              "child_support_higher": len(higher), "child_support_lower": len(lower),
              "child_support_equal": len(equal),
              "focus": FOCUS, "n_scope": len(scope), "survivor_rules": results,
              "unique_contribution_removable": removable,
              "unique_contribution_note": ("idea recorded, NOT adopted; removes none of "
                                           f"{FOCUS}'s {len(six)} parents")}
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, default=float) + "\n",
                            encoding="utf-8")
        print(f"\n  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
