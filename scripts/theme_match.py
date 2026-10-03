#!/usr/bin/env python3
"""Match the FINAL THEMES of two builds against each other, at Jaccard >= theta.

This is the statistic the RUNS rule has always been about: **the share of final themes that match
at Jaccard >= 0.70 between two builds.** It is NOT the share of the raw grouping pool, which is what
`cut_trees.py --ladder` measured on 2 Oct -- a mis-implementation of this rule, recorded as such in
`DECISIONS.md`.

The unit is a theme, so the comparison is between two finished build directories: completed,
support-gated, consensus-reconciled themes with their exported member lists. Nothing upstream of the
export enters it.

Reported in both directions, because a build with fewer themes can match a build with more while the
reverse fails, and the rule is about agreement rather than coverage. The worse direction is the one
a pass mark applies to.

Usage::

    uv run scripts/theme_match.py data/ontology/v0.2/recurrent_dag_c50 \
                                  data/ontology/v0.2/recurrent_dag_c50_seed1
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

import numpy as np

csv.field_size_limit(1 << 30)

#: The declared Jaccard the rule is stated at, and the thresholds reported alongside it.
THETA = 0.70
REPORT_AT: tuple[float, ...] = (0.50, 0.70, 0.90)


def read_themes(directory: Path) -> dict[str, frozenset[str]]:
    """Read a build's themes and their exported member keys.

    Args:
        directory: A build directory holding ``nodes.tsv`` and ``members.tsv``.

    Returns:
        Theme id to its member pathway keys.
    """
    members: dict[str, set[str]] = defaultdict(set)
    with (directory / "members.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            members[row["node"]].add(row["key"])
    with (directory / "nodes.tsv").open(encoding="utf-8", newline="") as handle:
        nodes = [row["node"] for row in csv.DictReader(handle, delimiter="\t")]
    # Every node must appear in members.tsv; a theme with no members would silently score 0 and
    # drag the share down, so it is an error rather than an empty set.
    missing = [node for node in nodes if not members.get(node)]
    if missing:
        raise ValueError(f"{directory}: {len(missing)} themes have no members, e.g. {missing[0]}")
    return {node: frozenset(members[node]) for node in nodes}


def best_matches(
    left: dict[str, frozenset[str]], right: dict[str, frozenset[str]]
) -> dict[str, float]:
    """Best Jaccard for each left theme against any right theme.

    Exhaustive -- nothing is sampled. Theme sets are packed to 64-bit words and compared with
    popcount rather than as dense boolean arrays: at the 10,770 scale a build has thousands of
    themes over thousands of pathways, and the dense form is 64x the memory traffic for the same
    answer. The frozen build's recorded figures are reproduced either way, and a test pins them.

    Args:
        left: Themes to score.
        right: Themes to score against.

    Returns:
        Left theme id to its best Jaccard.
    """
    keys = sorted({key for members in (*left.values(), *right.values()) for key in members})
    index = {key: i for i, key in enumerate(keys)}
    words = (len(keys) + 63) // 64

    def pack(themes: dict[str, frozenset[str]]) -> np.ndarray:
        out = np.zeros((len(themes), words), dtype=np.uint64)
        for row, members in enumerate(themes.values()):
            for key in members:
                position = index[key]
                out[row, position // 64] |= np.uint64(1) << np.uint64(position % 64)
        return out

    a, b = pack(left), pack(right)
    sizes_a = np.bitwise_count(a).sum(axis=1).astype(np.int64)
    sizes_b = np.bitwise_count(b).sum(axis=1).astype(np.int64)
    out = {}
    for row, name in enumerate(left):
        inter = np.bitwise_count(b & a[row]).sum(axis=1).astype(np.int64)
        union = sizes_a[row] + sizes_b - inter
        out[name] = float(np.max(np.where(union > 0, inter / np.maximum(union, 1), 0.0)))
    return out


def summarise(scores: dict[str, float]) -> dict:
    """Shares at each reported threshold, plus the mean and median.

    Args:
        scores: Theme id to best Jaccard.

    Returns:
        The summary.
    """
    values = list(scores.values())
    return {
        "themes": len(values),
        "mean": round(statistics.fmean(values), 4),
        "median": round(statistics.median(values), 4),
        **{f"share_ge_{t:.2f}": round(sum(v >= t for v in values) / len(values), 4)
           for t in REPORT_AT},
    }


def main(argv: list[str] | None = None) -> int:
    """Report the theme match between two builds.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--theta", type=float, default=THETA)
    parser.add_argument("--pass-mark", type=float, default=0.90)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--dump", type=Path, default=None,
                        help="write per-theme best Jaccard and size, for a post-hoc breakdown "
                             "of which themes failed to match")
    args = parser.parse_args(argv)

    left, right = read_themes(args.left), read_themes(args.right)
    print(f"THEME MATCH  {args.left.name} ({len(left)} themes) vs "
          f"{args.right.name} ({len(right)} themes), theta {args.theta}")

    forward_scores = best_matches(left, right)
    backward_scores = best_matches(right, left)
    forward = summarise(forward_scores)
    backward = summarise(backward_scores)
    if args.dump:
        args.dump.parent.mkdir(parents=True, exist_ok=True)
        with args.dump.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerow(["direction", "theme", "members", "best_jaccard"])
            for label, scores, themes in (("forward", forward_scores, left),
                                          ("backward", backward_scores, right)):
                for theme, score in scores.items():
                    writer.writerow([label, theme, len(themes[theme]), f"{score:.6f}"])
        print(f"  per-theme scores -> {args.dump}")
    key = f"share_ge_{args.theta:.2f}"
    if key not in forward:
        parser.error(f"--theta {args.theta} is not one of the reported thresholds {REPORT_AT}")
    worse = min(forward[key], backward[key])

    print(f"\n  {'direction':<22} {'themes':>7} {'mean':>7} {'median':>7} "
          + " ".join(f"{'>= ' + format(t, '.2f'):>9}" for t in REPORT_AT))
    for label, got in (("forward", forward), ("backward", backward)):
        print(f"  {label:<22} {got['themes']:>7} {got['mean']:>7.3f} {got['median']:>7.3f} "
              + " ".join(f"{got[f'share_ge_{t:.2f}']:>9.1%}" for t in REPORT_AT))
    print(f"\n  matched at >= {args.theta}: worse direction {worse:.1%} against a "
          f"{args.pass_mark:.0%} mark -- {'PASS' if worse >= args.pass_mark else 'FAIL'}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({
            "statistic": "share of FINAL THEMES with a best match at Jaccard >= theta",
            "left": str(args.left), "right": str(args.right),
            "theta": args.theta, "pass_mark": args.pass_mark,
            "forward": forward, "backward": backward,
            "worse_direction": round(worse, 4),
            "exhaustive": True,
        }, indent=2) + "\n", encoding="utf-8")
        print(f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
