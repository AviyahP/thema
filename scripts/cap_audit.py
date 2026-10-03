#!/usr/bin/env python3
"""Which pipeline step grows a theme past the declared size cap, and how many themes exceed it.

The cap -- 29.0133% of the universe, 3,125 pathways at 10,770 -- is applied **at cut time**, to the
clusters a Ward tree offers as candidates. `cut_trees.load_run` drops every recorded cluster above
it, so no candidate grouping can exceed the cap by construction. Yet the r1-200 build's largest
theme holds 3,336 members. Something downstream grew it.

There are exactly two places it can happen, and this separates them:

1. **Completion.** A family's candidate set is the UNION of the matched copies across runs, not any
   single cluster, and members are then kept at inclusion >= 0.50. A union of several
   under-cap clusters can exceed the cap.
2. **Greedy consensus.** A theme can inherit members from a cluster it supersedes, which grows its
   member set after completion.

Seed absorption cannot: a family's set is its SEED's completed set, not a union over the family.
Strict Hasse cannot: it only draws edges.

**Measurement only. Nothing is changed.** Whether the cap must also hold after consensus is a
declared-rule question and therefore Aviyah's.

Usage::

    uv run scripts/cap_audit.py data/ontology/v0.3/recurrent_dag_10770_r1-200 \
        --side real_r00001-00200
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from build_10770 import DECLARED_M, INCLUSION_CUT, cut_key, load_material, stratum_of
from cut_trees import CAP_SHARE, cap_for
from thema.ontology.universe import load_embedded

csv.field_size_limit(1 << 30)


def themes_of(directory: Path) -> dict[str, set[str]]:
    """The build's exported themes.

    Args:
        directory: A build directory.

    Returns:
        Theme id to member keys.
    """
    out: dict[str, set[str]] = defaultdict(set)
    with (directory / "members.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            out[row["node"]].add(row["key"])
    return dict(out)


def main(argv: list[str] | None = None) -> int:
    """Report where the cap stops holding.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", type=Path)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--space", default="centred")
    parser.add_argument("--side", required=True, help="the cached real side the build was cut from")
    parser.add_argument("--floors", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    root = args.data / "ontology" / f"v{args.version}"
    meta = json.loads((root / "universe.json").read_text())
    universe, n = meta["universe_digest"], meta["n_embedded"]
    cap = cap_for(n)
    keys = list(load_embedded(root, args.data / "pathways.tsv").keys)

    path = (root / "trees" / f"{args.space}_{universe}" / "completions"
            / cut_key(cap, INCLUSION_CUT) / f"{args.side}.npz")
    material = load_material(path)
    sizes = np.bitwise_count(material.blocks).sum(axis=1).astype(np.int64)

    floors = json.loads(args.floors.read_text())
    thresholds = {i: e["effective"] for i, e in enumerate(floors["strata"])}
    keep = np.array([
        thresholds[stratum_of(int(s))] is not None
        and round(float(v), 6) >= thresholds[stratum_of(int(s))]
        for s, v in zip(sizes, material.supports, strict=True)
    ])
    gated = sizes[keep]

    themes = themes_of(args.build)
    theme_sizes = {t: len(m) for t, m in themes.items()}

    print(f"CAP AUDIT  {args.build.name}, cap {CAP_SHARE:.4%} = {cap:,} of {n:,}")
    print(f"  declared m {DECLARED_M}, inclusion {INCLUSION_CUT}\n")
    print(f"  {'stage':<42} {'count':>9} {'over cap':>9} {'largest':>9}")
    rows = [
        ("candidate clusters (cut under the cap)", None, 0, cap),
        ("completed families, before the gate", len(sizes), int((sizes > cap).sum()),
         int(sizes.max()) if len(sizes) else 0),
        ("families through the support gate", len(gated), int((gated > cap).sum()),
         int(gated.max()) if len(gated) else 0),
        ("themes, after consensus and Hasse", len(theme_sizes),
         sum(1 for v in theme_sizes.values() if v > cap), max(theme_sizes.values(), default=0)),
    ]
    for label, count, over, largest in rows:
        shown = f"{count:,}" if count is not None else "by construction"
        print(f"  {label:<42} {shown:>9} {over:>9} {largest:>9,}")

    over_cap = sorted(((v, t) for t, v in theme_sizes.items() if v > cap), reverse=True)
    print(f"\n  THEMES OVER THE CAP: {len(over_cap)} of {len(theme_sizes):,}")
    index = {k: i for i, k in enumerate(keys)}
    report_over = []
    for size, theme in over_cap[:10]:
        want = np.zeros(material.blocks.shape[1], dtype=np.uint64)
        for key in themes[theme]:
            if key in index:
                position = index[key]
                want[position // 64] |= np.uint64(1) << np.uint64(position % 64)
        inter = np.bitwise_count(material.blocks & want).sum(axis=1).astype(np.int64)
        union = sizes + int(np.bitwise_count(want).sum()) - inter
        jaccard = np.where(union > 0, inter / np.maximum(union, 1), 0.0)
        best = int(np.argmax(jaccard))
        exact = bool(jaccard[best] == 1.0)
        report_over.append({
            "theme": theme, "members": size,
            "closest_completed_family_size": int(sizes[best]),
            "jaccard_to_it": round(float(jaccard[best]), 4),
            "identical_to_a_completed_family": exact,
            "grown_by_consensus": size - int(sizes[best]) if not exact else 0,
        })
        print(f"    {theme}  {size:,} members   closest completed family {int(sizes[best]):,} "
              f"(J {jaccard[best]:.3f}){'  IDENTICAL' if exact else ''}")

    verdict = (
        "completion" if int((sizes > cap).sum()) else "consensus"
    ) if over_cap else "the cap holds everywhere"
    print(f"\n  WHERE THE CAP STOPS HOLDING: {verdict}")
    if over_cap and int((sizes > cap).sum()):
        print("    Completion already produces over-cap sets: a family's members are the UNION")
        print("    of its matched copies across runs, and a union of under-cap clusters can")
        print("    exceed the cap. The cap constrains CANDIDACY, where it is declared to apply.")
    print("  NOTHING CHANGED. Whether the cap must also hold after completion and consensus is a")
    print("  change to a declared rule, and therefore Aviyah's decision.")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({
            "build": str(args.build), "cap": cap, "cap_share": CAP_SHARE, "n": n,
            "completed_families": len(sizes),
            "completed_over_cap": int((sizes > cap).sum()),
            "completed_largest": int(sizes.max()) if len(sizes) else 0,
            "gated_families": int(len(gated)),
            "gated_over_cap": int((gated > cap).sum()),
            "themes": len(theme_sizes),
            "themes_over_cap": len(over_cap),
            "largest_theme": max(theme_sizes.values(), default=0),
            "over_cap_detail": report_over,
            "nothing_changed": True,
        }, indent=2) + "\n", encoding="utf-8")
        print(f"\n  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
