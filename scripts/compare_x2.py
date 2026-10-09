#!/usr/bin/env python3
"""Compare an exclusion rebuild against the build it replaces. Read-only apart from the mapping.

The two builds sit over **different universes** -- the rebuild's is the old one minus the excluded
inputs -- so a theme that merely lost an excluded member is not "identical" by a naive set
comparison even though nothing about it really changed. Both comparisons are therefore reported:

- **raw**: the new member set against the old member set as stored;
- **projected**: the new member set against the old set with the excluded keys removed, which is
  what "unchanged apart from losing an excluded input" means.

The projected figure is the honest one for "did the structure survive"; the raw figure is the honest
one for "is this literally the same theme".

Writes ``match_to_repair.tsv`` with one row per new theme. Usage::

    uv run scripts/compare_x2.py --new thema_L_x2 --old thema_L_repair
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

BANDS: tuple[tuple[int, int], ...] = (
    (3, 5), (6, 10), (11, 20), (21, 50), (51, 100), (101, 300), (301, 1000), (1001, 10**9))
MATCH = 0.70
GIANT = 1000


def label(low: int, high: int) -> str:
    """Band label."""
    return f"{low}-{high}" if high < 10**9 else f"{low}+"


def band_of(size: int) -> str:
    """Band for a size."""
    for low, high in BANDS:
        if low <= size <= high:
            return label(low, high)
    return "other"


def read(path: Path) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Members and parent edges.

    Args:
        path: A built ontology directory.

    Returns:
        ``(node -> members, child -> parents)``.
    """
    members: dict[str, set[str]] = defaultdict(set)
    with (path / "members.tsv").open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    parents: dict[str, set[str]] = defaultdict(set)
    if (path / "edges.tsv").is_file():
        with (path / "edges.tsv").open() as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                parents[row["child"]].add(row["parent"])
    return members, parents


def main(argv: list[str] | None = None) -> int:
    """Compare and write the mapping."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.4-leaves")
    parser.add_argument("--new", default="thema_L_x2")
    parser.add_argument("--old", default="thema_L_repair")
    parser.add_argument("--exclusions", type=Path, default=Path("data/excluded_inputs.tsv"))
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    new, new_par = read(root / args.new)
    old, old_par = read(root / args.old)
    with args.exclusions.open() as handle:
        excluded = {row["key"] for row in csv.DictReader(handle, delimiter="\t")}

    print(f"COMPARING {args.new} ({len(new):,} themes) against {args.old} ({len(old):,})")
    print(f"  {len(excluded)} inputs excluded; "
          f"{len({k for s in old.values() for k in s} & excluded)} of them appear in {args.old}")

    print("\n  themes per size band")
    cn, co = Counter(band_of(len(v)) for v in new.values()), \
        Counter(band_of(len(v)) for v in old.values())
    print(f"    {'band':<10}{args.old:>18}{args.new:>14}{'delta':>8}")
    for low, high in BANDS:
        b = label(low, high)
        print(f"    {b:<10}{co.get(b, 0):>18,}{cn.get(b, 0):>14,}"
              f"{cn.get(b, 0) - co.get(b, 0):>+8,}")
    print(f"    {'TOTAL':<10}{len(old):>18,}{len(new):>14,}{len(new) - len(old):>+8,}")

    print(f"\n  roots over {GIANT:,} members")
    for name, mem, par in ((args.old, old, old_par), (args.new, new, new_par)):
        roots = sorted((n for n in mem if not par.get(n)), key=lambda n: -len(mem[n]))
        giants = [len(mem[r]) for r in roots if len(mem[r]) >= GIANT]
        print(f"    {name:<16} {len(roots):>4} roots, {len(giants)} over {GIANT:,}: {giants}")

    # Match every new theme to the best old theme, raw and projected.
    projected = {k: (v - excluded) for k, v in old.items()}
    holders: dict[str, list[str]] = defaultdict(list)
    for node, keys in old.items():
        for key in keys:
            holders[key].append(node)
    rows = []
    for node in sorted(new):
        keys = new[node]
        best_raw = ("", 0.0)
        best_proj = ("", 0.0)
        for other in {o for k in keys for o in holders.get(k, ())}:
            inter = len(keys & old[other])
            union = len(keys) + len(old[other]) - inter
            if union and inter / union > best_raw[1]:
                best_raw = (other, inter / union)
            pinter = len(keys & projected[other])
            punion = len(keys) + len(projected[other]) - pinter
            if punion and pinter / punion > best_proj[1]:
                best_proj = (other, pinter / punion)
        rows.append({
            "new_node": node, "new_size": len(keys),
            "best_old_node": best_raw[0], "jaccard": round(best_raw[1], 4),
            "identical": "yes" if best_raw[0] and keys == old[best_raw[0]] else "no",
            "best_old_node_projected": best_proj[0],
            "jaccard_projected": round(best_proj[1], 4),
            "identical_projected": ("yes" if best_proj[0] and keys == projected[best_proj[0]]
                                    else "no")})

    for which, ident, jac in (("RAW (old set as stored)", "identical", "jaccard"),
                              ("PROJECTED (old set minus excluded inputs)",
                               "identical_projected", "jaccard_projected")):
        same = sum(1 for r in rows if r[ident] == "yes")
        near = sum(1 for r in rows if r[ident] == "no" and r[jac] >= MATCH)
        fresh = len(rows) - same - near
        print(f"\n  {which}")
        print(f"    identical to an old theme:        {same:>6,} ({100 * same / len(rows):.1f}%)")
        print(f"    not identical but Jaccard >= {MATCH}: {near:>6,} "
              f"({100 * near / len(rows):.1f}%)")
        print(f"    new (no old theme at {MATCH}):        {fresh:>6,} "
              f"({100 * fresh / len(rows):.1f}%)")

    destination = args.out or (root / args.new / "match_to_repair.tsv")
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n",
                                fieldnames=["new_node", "best_old_node", "jaccard", "identical",
                                            "new_size", "best_old_node_projected",
                                            "jaccard_projected", "identical_projected"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n  -> {destination}")
    if args.out is None:
        summary = root / args.new / "compare_to_repair.json"
        summary.write_text(json.dumps(
            {"new": args.new, "old": args.old, "n_new": len(new), "n_old": len(old),
             "bands_new": dict(cn), "bands_old": dict(co),
             "n_excluded": len(excluded)}, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
