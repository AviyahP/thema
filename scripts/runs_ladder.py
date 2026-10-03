#!/usr/bin/env python3
"""The RUNS ladder, on FINAL THEMES, exactly as declared in DECISIONS.md on 2 Oct 2026.

Each rung is **two separate full builds**, one per disjoint block of persisted trees, each taken
through the entire declared pipeline -- cap 29.0133% at cut time, completion at inclusion 0.50,
floors solved on the 10 calibration scrambles at the build's own run count, the gate at
``max(m = 0.33, floor)``, greedy consensus at STRAY 0.10 / JACCARD 0.70, strict Hasse -- and then
matched theme-for-theme with :mod:`theme_match`.

> **PASS if >= 90% of final themes have a partner at Jaccard >= 0.70 in the WORSE direction.**

**RUNS is the smallest passing rung. If neither passes, this stops and reports.** It does not try a
third rung, does not build new trees, and does not touch the mark.

Both builds in a rung read the **same** scramble sides for their floors, because a floor is a
property of a size stratum under the null and not of the block being cut.

Each build runs as a SUBPROCESS. One side of this universe peaks around 8.6 GB, so running the
builds in one process would hold two pools' worth of memory for no reason; letting each exit returns
it to the system.

The held-out scrambles are NOT read here. They are confirmed against exactly once, by the
confirmatory build.

Usage::

    uv run scripts/runs_ladder.py
    uv run scripts/runs_ladder.py --rung 1
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from theme_match import REPORT_AT, best_matches, read_themes, summarise

#: The declared rungs: ``(block A, block B, RUNS if it passes)``.
RUNGS: tuple[tuple[tuple[int, int], tuple[int, int], int], ...] = (
    ((1, 100), (101, 200), 100),
    ((1, 200), (201, 400), 200),
)

#: Which completion implementation the sides were cut with, and must be read back with.
COMPLETION = "fast"

#: The declared threshold and mark. Neither is a parameter of this script in any real sense; they
#: are here as named constants so the output can print what it was judged against.
THETA = 0.70
PASS_MARK = 0.90


def build(data: Path, version: str, first: int, last: int, scramble_rows: int) -> Path:
    """Run one full build over a block of trees, as a subprocess.

    Args:
        data: The data directory.
        version: Ontology version.
        first: First tree row, 1-based inclusive.
        last: Last tree row, inclusive.
        scramble_rows: Trees per scramble side, which must equal the build's run count.

    Returns:
        The build directory.

    Raises:
        RuntimeError: If the build fails.
    """
    directory = data / "ontology" / f"v{version}" / f"recurrent_dag_10770_r{first}-{last}"
    command = [
        sys.executable, str(Path(__file__).with_name("build_10770.py")),
        "--data", str(data), "--version", version,
        "--rows", f"{first}-{last}", "--scramble-rows", str(scramble_rows),
        # The sides were cut with the vectorised completion, which is proved byte-identical
        # (DECISIONS.md, 2 Oct). Naming it here is what makes the cached sides reusable: the
        # provenance guard compares the implementation that wrote a side against the one asking
        # for it, and it was right to refuse when this said "original" while the files said "fast".
        "--completion", COMPLETION,
    ]
    print(f"  $ {' '.join(command[1:])}", flush=True)
    start = time.perf_counter()
    done = subprocess.run(command, cwd=Path(__file__).resolve().parents[1], check=False)
    if done.returncode != 0:
        raise RuntimeError(f"build of trees {first}-{last} failed ({done.returncode})")
    print(f"  built trees {first}-{last} in {(time.perf_counter() - start) / 60:.1f} min",
          flush=True)
    return directory


def shape(directory: Path) -> dict:
    """Themes and roots of a finished build.

    Args:
        directory: A build directory.

    Returns:
        Theme and root counts.
    """
    import csv
    csv.field_size_limit(1 << 30)
    with (directory / "nodes.tsv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    return {"themes": len(rows), "roots": sum(1 for r in rows if not r["parents"].strip())}


def judge(left: Path, right: Path) -> dict:
    """Match two finished builds and apply the declared mark to the worse direction.

    Args:
        left: Block A's build directory.
        right: Block B's build directory.

    Returns:
        Both directions, the worse one, and the verdict.
    """
    a, b = read_themes(left), read_themes(right)
    forward, backward = summarise(best_matches(a, b)), summarise(best_matches(b, a))
    key = f"share_ge_{THETA:.2f}"
    worse = min(forward[key], backward[key])
    return {
        "left": str(left), "right": str(right),
        "shape_left": shape(left), "shape_right": shape(right),
        "forward": forward, "backward": backward,
        "worse_direction": round(worse, 4),
        "passes": bool(worse >= PASS_MARK),
    }


def table(result: dict) -> None:
    """Print one rung's table, the same shape as the test-9 check.

    Args:
        result: Output of :func:`judge`.
    """
    print(f"\n  {'direction':<22} {'themes':>7} {'roots':>6} {'mean':>7} {'median':>7} "
          + " ".join(f"{'>= ' + format(t, '.2f'):>9}" for t in REPORT_AT))
    for label, got, sh in (("A -> B", result["forward"], result["shape_left"]),
                           ("B -> A", result["backward"], result["shape_right"])):
        print(f"  {label:<22} {got['themes']:>7} {sh['roots']:>6} {got['mean']:>7.3f} "
              f"{got['median']:>7.3f} "
              + " ".join(f"{got[f'share_ge_{t:.2f}']:>9.1%}" for t in REPORT_AT))
    print(f"\n  WORSE DIRECTION at >= {THETA}: {result['worse_direction']:.1%} against "
          f"{PASS_MARK:.0%} -- {'PASS' if result['passes'] else 'FAIL'}", flush=True)


def main(argv: list[str] | None = None) -> int:
    """Climb the ladder until a rung passes.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status. 0 whether or not a rung passes -- a failing ladder is a result, not an
        error -- and non-zero only if a build could not run.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--rung", type=int, default=0, choices=(0, 1, 2),
                        help="0 climbs from rung 1 until one passes")
    args = parser.parse_args(argv)

    chosen = RUNGS if not args.rung else (RUNGS[args.rung - 1],)
    print(f"RUNS LADDER on FINAL THEMES  theta {THETA}, mark {PASS_MARK:.0%} on the WORSE "
          f"direction, {len(chosen)} rung(s)", flush=True)

    results, runs = [], None
    for (al, ah), (bl, bh) in [(a, b) for a, b, _r in chosen]:
        at = next(r for a, b, r in RUNGS if a == (al, ah) and b == (bl, bh))
        print(f"\n{'=' * 78}\nRUNG: trees {al}-{ah} vs {bl}-{bh}  ->  RUNS = {at} if it passes\n"
              f"{'=' * 78}", flush=True)
        left = build(args.data, args.version, al, ah, at)
        right = build(args.data, args.version, bl, bh, at)
        result = judge(left, right)
        result["rung"] = {"a": f"{al}-{ah}", "b": f"{bl}-{bh}", "runs_if_passing": at}
        table(result)
        results.append(result)
        if result["passes"]:
            runs = at
            print(f"\n  RUNG PASSES. RUNS = {at}, the smallest passing rung.", flush=True)
            break
        remaining = [r for _a, _b, r in chosen if r > at]
        print(f"\n  rung fails. {'climbing to RUNS = ' + str(remaining[0]) if remaining else
                                  'no further rung was attempted in this invocation'}",
              flush=True)

    out = args.data / "ontology" / f"v{args.version}" / "runs_ladder.json"
    out.write_text(json.dumps({
        "statistic": "share of FINAL THEMES with a partner at Jaccard >= theta",
        "declared": "DECISIONS.md, 2 Oct 2026",
        "theta": THETA, "pass_mark": PASS_MARK, "mark_applies_to": "worse direction",
        "completion_implementation": COMPLETION,
        "heldout_read": False,
        "rungs_attempted": [f"{a[0]}-{a[1]} vs {b[0]}-{b[1]}" for a, b, _r in chosen],
        "rungs_declared": [f"{a[0]}-{a[1]} vs {b[0]}-{b[1]}" for a, b, _r in RUNGS],
        "all_declared_rungs_attempted": len(chosen) == len(RUNGS),
        "rungs": results, "runs": runs,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"\n  -> {out}")
    if runs is None and len(chosen) == len(RUNGS):
        print("\n  NO DECLARED RUNG PASSES. Stopping, as declared: no third rung, no new trees, "
              "no change to the mark.\n  Aviyah decides.", flush=True)
    elif runs is None:
        attempted = ", ".join(f"{a[0]}-{a[1]} vs {b[0]}-{b[1]}" for a, b, _r in chosen)
        print(f"\n  the rung(s) attempted here ({attempted}) do not pass. THIS IS NOT A VERDICT "
              f"ON THE LADDER:\n  {len(RUNGS) - len(chosen)} declared rung(s) were not run in "
              f"this invocation.", flush=True)
    else:
        print(f"\n  RUNS = {runs}. The confirmatory build runs on trees 1-{runs} with "
              f"--confirm-heldout.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
