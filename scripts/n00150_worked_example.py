#!/usr/bin/env python3
"""The n00150 lattice under each candidate rule, node by node. Read-only.

Item 4 of the 9 Oct addendum. `REPORT3.md` §3 reads this lattice by hand and says what the candidate
rules would do; this measures the same thing on the build so the two can be compared, and lists
**every** affected node rather than a count.

Scope follows REPORT3: **all** ancestors of ``n00150`` at any depth, with the four giant roots
excluded as known bags. Rules, none applied:

- **chain collapse** at 0.80, 0.85 and 0.90 -- a child holding at least the share of its parent's
  members is absorbed into it. Iterated to a fixed point, as the build's own collapse is, because
  collapsing one rung of a staircase exposes the next.
- **sibling merge** at Jaccard 0.6 and 0.7, reported **two ways** because the two readings differ
  sharply here: the strict reading (only pairs that **share a parent**, which is what "sibling"
  means and what the measurement report uses) and the loose reading (**any** pair above the
  threshold, which is what REPORT3 §3 applies to the six parents).

Usage::

    uv run scripts/n00150_worked_example.py --stats STATS.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

FOCUS = "n00150"
#: A root of at least this size is one of the known giant bags, excluded from the lattice.
GIANT = 1000
CHAIN_SHARES = (0.80, 0.85, 0.90)
SIBLING_THETAS = (0.60, 0.70)
MAX_ROUNDS = 50


def main(argv: list[str] | None = None) -> int:
    """Report the lattice and what each rule would do to it."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.4-leaves")
    parser.add_argument("--build", default="thema_L_repair")
    parser.add_argument("--stats", type=Path, required=True)
    parser.add_argument("--focus", default=FOCUS)
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
    sizes = {node: len(keys) for node, keys in members.items()}

    def gist(node: str, n: int = 3) -> str:
        """Nearest member names."""
        return "; ".join((stats.get(node, {}).get("nearest") or [])[:n])

    focus = args.focus
    six = sorted(parents[focus], key=lambda p: -support.get(p, 0.0))

    # Every ancestor at any depth.
    all_up: set[str] = set()
    frontier = set(six)
    while frontier:
        all_up |= frontier
        frontier = {up for node in frontier for up in parents.get(node, ())} - all_up
    giants = sorted((a for a in all_up if sizes[a] >= GIANT), key=lambda a: -sizes[a])
    lattice = sorted((a for a in all_up if a not in giants and a not in six),
                     key=lambda a: sizes[a])

    print(f"WORKED EXAMPLE: the lattice above {focus} ({sizes[focus]} members, "
          f"support {support.get(focus, 0):.3f})")
    print(f"  {len(all_up)} ancestors in total: {len(giants)} giant roots excluded "
          f"({', '.join(giants)}), {len(six)} direct parents, {len(lattice)} lattice nodes")
    print(f"  REPORT3 reports 28 ancestors, 4 giants, 24 judged -- "
          f"here {len(all_up)} / {len(giants)} / {len(six) + len(lattice)}")

    print(f"\n  the {len(six)} direct parents:")
    for p in six:
        print(f"    {p:<9} n={sizes[p]:>3} support={support.get(p, 0):.3f}  {gist(p)}")
    print(f"\n  the {len(lattice)} lattice nodes above them:")
    for a in lattice:
        covers = sum(1 for p in six if members[p] <= members[a])
        print(f"    {a:<9} n={sizes[a]:>4} support={support.get(a, 0):.3f} covers {covers}/6  "
              f"{gist(a)[:66]}")

    scope = six + lattice
    report: dict[str, object] = {
        "focus": focus, "focus_size": sizes[focus], "focus_support": support.get(focus),
        "n_ancestors_total": len(all_up), "giants_excluded": giants,
        "parents": [{"node": p, "size": sizes[p], "support": support.get(p)} for p in six],
        "lattice": [{"node": a, "size": sizes[a], "support": support.get(a),
                     "covers": sum(1 for p in six if members[p] <= members[a])}
                    for a in lattice],
        "rules": {},
    }

    # ----- chain collapse, within the lattice, iterated to a fixed point
    print("\n  CHAIN COLLAPSE -- a child holding >= share of its parent is absorbed, "
          "iterated to a fixed point")
    for share in CHAIN_SHARES:
        alive = set(scope)
        # Children of an absorbed node inherit the surviving parent, so a staircase collapses the
        # whole way up. Without the re-link a rung whose own target is also being absorbed is lost
        # entirely -- that undercounted this lattice by one rung at 0.85 and two at 0.80 against the
        # reviewer's hand count, which is how the bug was found.
        up: dict[str, set[str]] = {n: {x for x in parents.get(n, ()) if x in scope}
                                   for n in scope}
        down: dict[str, set[str]] = defaultdict(set)
        for node, ups in up.items():
            for parent in ups:
                down[parent].add(node)
        absorbed: list[tuple[str, str, float]] = []
        for _ in range(MAX_ROUNDS):
            doomed: dict[str, tuple[str, float]] = {}
            for child in sorted(alive, key=lambda x: sizes[x]):
                best: tuple[str, int] | None = None
                for parent in up.get(child, ()):
                    if parent not in alive or parent == child:
                        continue
                    if not members[child] < members[parent]:
                        continue
                    if sizes[child] >= share * sizes[parent]:
                        if best is None or sizes[parent] < best[1]:
                            best = (parent, sizes[parent])
                if best is not None:
                    doomed[child] = (best[0], sizes[child] / sizes[best[0]])
            # Absorb one round, smallest first, re-linking as we go rather than deferring.
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
                alive.discard(c)
                absorbed.append((c, target, ratio))
                for kid in down.get(c, ()):
                    up.setdefault(kid, set()).add(target)
                    down[target].add(kid)
                progressed = True
            if not progressed:
                break
        gone_parents = [c for c, _p, _r in absorbed if c in six]
        gone_lattice = [c for c, _p, _r in absorbed if c in lattice]
        print(f"    at {share:.2f}: {len(absorbed)} absorbed -- "
              f"{len(gone_lattice)} of {len(lattice)} lattice nodes, "
              f"{len(gone_parents)} of {len(six)} parents")
        for c, p, r in sorted(absorbed, key=lambda t: -t[2]):
            tag = " [PARENT]" if c in six else ""
            print(f"       {c} ({sizes[c]}) -> {p} ({sizes[p]})  ratio {r:.3f}{tag}")
        report["rules"][f"chain_{share:.2f}"] = {
            "absorbed": [{"child": c, "into": p, "ratio": round(r, 4),
                          "is_direct_parent": c in six} for c, p, r in absorbed],
            "n_lattice_removed": len(gone_lattice), "n_parents_removed": len(gone_parents)}

    # ----- sibling merge, both readings
    print("\n  SIBLING MERGE -- the lower-support member of a qualifying pair is dropped")
    for theta in SIBLING_THETAS:
        for strict in (True, False):
            pairs = []
            for i, a in enumerate(scope):
                for b in scope[i + 1:]:
                    sa, sb = members[a], members[b]
                    if sa <= sb or sb <= sa:
                        continue
                    inter = len(sa & sb)
                    if not inter:
                        continue
                    j = inter / (len(sa) + len(sb) - inter)
                    if j < theta:
                        continue
                    siblings = bool(parents.get(a, set()) & parents.get(b, set()))
                    if strict and not siblings:
                        continue
                    pairs.append((j, a, b, siblings))
            gone: set[str] = set()
            for _j, a, b, _s in sorted(pairs, reverse=True):
                if a in gone or b in gone:
                    continue
                gone.add(a if support.get(a, 0) < support.get(b, 0) else b)
            reading = "strict (must share a parent)" if strict else "loose (any pair)"
            print(f"    at J >= {theta:.2f}, {reading}: {len(pairs)} pairs, "
                  f"{len(gone)} dropped -- "
                  f"{len([g for g in gone if g in six])} of {len(six)} parents, "
                  f"{len([g for g in gone if g in lattice])} of {len(lattice)} lattice")
            for j, a, b, s in sorted(pairs, reverse=True):
                lo = a if support.get(a, 0) < support.get(b, 0) else b
                hi = b if lo == a else a
                mark = "" if lo in gone else "   (superseded by an earlier merge)"
                print(f"       {a} / {b}  J={j:.3f}  {'siblings' if s else 'not siblings'}"
                      f" -> drops {lo} (support {support.get(lo, 0):.3f}), "
                      f"keeps {hi} ({support.get(hi, 0):.3f}){mark}")
            report["rules"][f"sibling_{theta:.2f}_{'strict' if strict else 'loose'}"] = {
                "pairs": [{"a": a, "b": b, "jaccard": round(j, 4), "siblings": s}
                          for j, a, b, s in pairs],
                "dropped": sorted(gone),
                "n_parents_dropped": len([g for g in gone if g in six]),
                "n_lattice_dropped": len([g for g in gone if g in lattice])}

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, default=float) + "\n",
                            encoding="utf-8")
        print(f"\n  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
