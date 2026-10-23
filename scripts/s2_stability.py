"""PART 2 section F of prompt 55: stability of S2 and O50s across half-builds.

Declared 22 Oct 2026. Evaluation only; nothing is adopted and no verdict is offered.

Runs 1-100 and 101-200 are built independently, **each through its own build's steps** -- O50s's
unrestricted consensus and repair, and S2's sibling-restricted consensus and stale merge -- and the
two halves' final themes are matched at J >= 0.70. The reported figure is the **worse direction**,
because a build that reproduces its own themes in one direction but not the other is not stable.

**The gate has to be transferred to a 100-run half, and how is a real choice.** Six of the
thirteen stored floors are solved rates (0.84 down to 0.030151) and transfer directly. The other
seven are all exactly 0.01, and that value is **not a solved rate**: O50s's own report marks those
strata as decided by the rule-of-three bound, where no scrambled candidate was observed at or above
the cut. On 200 runs a floor of 0.01 means "found by at least 2 runs". On 100 runs the same 0.01
means "found by at least 1 run", which is a different requirement entirely.

Applying the stored floors unchanged was tried first and rejected on measurement grounds, not
taste: it gates **38,811 themes of which 59.5% were found by exactly one run of 100** (38,565 and
60.1% for the other half). A stability figure over that set measures how often single-run noise
repeats, floods both arms equally, and would mask any real difference between them.

So the seven bound floors are transferred as a **run count** -- 2 runs of 100, i.e. 0.02 -- and the
six solved rates are left alone. That gates 15,726 and 15,377. **Both readings are held identical
across the two arms**, so the O50s-against-S2 difference is unaffected by the choice; it is the
absolute rates that move, and they are not comparable with a 200-run build either way.

Matching uses ``scripts/theme_match.best_matches``, the same statistic the RUNS ladder is stated
over. Nothing else here has an existing script.

Usage:
    uv run scripts/s2_stability.py --sides     # compute and cache the two half sides
    uv run scripts/s2_stability.py            # the four half-builds and the match
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

THETA_MATCH = 0.70
THETA_SAME = 0.50
COLLAPSE_SHARE = 0.85
SURVIVOR = "support"
MATCH_AT = 0.70

#: The two halves, as (name, first run, last run).
HALVES: tuple[tuple[str, int, int], ...] = (("1-100", 1, 100), ("101-200", 101, 200))


def side_for(half: str, low: int, high: int, args: argparse.Namespace) -> object:
    """Material for one half of the runs, cached.

    Args:
        half: Half label.
        low: First run.
        high: Last run.
        args: Parsed arguments.

    Returns:
        A :class:`~thema.ontology.v04.Material`.
    """
    from cut_trees import load_run
    from thema.ontology.v04 import NO_CAP, Material, material

    cache = args.out / f"side_{half}.npz"
    meta = json.loads((args.space_root / "universe.json").read_text())
    n = meta["n_embedded"]
    if cache.is_file():
        with np.load(cache) as handle:
            indptr = handle["indptr"]
            vote_keys, vote_vals = handle["vote_keys"], handle["vote_vals"]
            votes = tuple(
                dict(zip(vote_keys[indptr[i]:indptr[i + 1]].tolist(),
                         vote_vals[indptr[i]:indptr[i + 1]].tolist(), strict=True))
                for i in range(len(indptr) - 1))
            got = Material(blocks=handle["blocks"], supports=handle["supports"],
                           selections=votes)
        print(f"  side {half}: {len(got.supports):,} candidates (cached)", flush=True)
        return got

    clock = time.perf_counter()
    trees = args.space_root / "trees" / f"{meta['space']}_{meta['universe_digest']}"
    labels = [f"row{r:05d}" for r in range(low, high + 1)]
    runs = [load_run(trees / f"{label}.npz", n, NO_CAP) for label in labels]
    got = material(runs, n, theta_match=THETA_MATCH, match_split=None)
    from v04_run import save_side
    args.out.mkdir(parents=True, exist_ok=True)
    save_side(cache, got)
    print(f"  side {half}: {len(got.supports):,} candidates from {len(labels)} runs "
          f"({time.perf_counter() - clock:.0f}s)", flush=True)
    return got


def transfer_floors(floors: Sequence[dict], runs: int, full_runs: int = 200
                    ) -> tuple[list[dict], list[str]]:
    """Carry the stored floors to a build with fewer runs.

    A floor that is a solved rate transfers as a rate. A floor sitting at the rule-of-three bound
    (0.01) is not a rate at all -- it encodes "at least two runs of ``full_runs``" -- so it
    transfers as that run count.

    Args:
        floors: The stored floors.
        runs: Runs in this build.
        full_runs: Runs the floors were solved on.

    Returns:
        ``(floors, notes)``.
    """
    BOUND = 0.01
    out, notes = [], []
    for entry in floors:
        value = float(entry["effective"])
        if abs(value - BOUND) < 1e-12 and runs < full_runs:
            needed = BOUND * full_runs                   # the run count the bound encodes
            raised = needed / runs
            out.append(dict(entry, effective=raised))
            notes.append(f"{entry['stratum']}: {value} -> {raised} "
                         f"(hold {needed:.0f} runs, not the rate)")
        else:
            out.append(dict(entry))
    return out, notes


def half_build(style: str, got: object, floors: Sequence[dict],
               strata: Sequence[tuple[int, int]], n: int, keys: Sequence[str]
               ) -> dict[str, frozenset[str]]:
    """One half-build, through one build's own steps.

    Args:
        style: ``"O50s"`` or ``"S2"``.
        got: The half's material.
        floors: The stored floors.
        strata: The stored stratum edges.
        n: Universe size.
        keys: Pathway keys in universe order.

    Returns:
        Theme id to member keys.
    """
    from build_s2 import sibling_predicate
    from thema.ontology import bitset as bits
    from thema.ontology.consensus import consensus
    from thema.ontology.repair import repair_joint
    from thema.ontology.v04 import gate

    keep = np.flatnonzero(gate(got.rows(), floors, strata)).tolist()
    width = got.blocks.shape[1] * bits.WORD
    blocks = [got.blocks[i] for i in keep]
    supports = [float(got.supports[i]) for i in keep]
    inclusions = [got.selections[i] for i in keep]

    restrict = style == "S2"
    pred = sibling_predicate(blocks, n) if restrict else None
    verdict = consensus(blocks, supports, inclusions, width, stray=0.0,
                        jaccard=THETA_SAME, siblings=pred)
    members = [verdict.members[i] for i in range(len(verdict.accepted))]
    kept = [supports[c] for c in verdict.accepted]
    votes = [inclusions[c] for c in verdict.accepted]

    def factory(live: Sequence[np.ndarray]) -> Callable[[int, int], bool]:
        """Rebuild the sibling relation from the current memberships."""
        return sibling_predicate(live, n)

    repaired = repair_joint(members, kept, votes, COLLAPSE_SHARE, THETA_SAME, SURVIVOR,
                            stale_siblings=factory if restrict else None)
    out = {f"h{i:05d}": frozenset(keys[p] for p in bits.unpack(block))
           for i, block in enumerate(repaired.members)}
    print(f"    {style}: gated {len(keep):,} -> consensus {len(members):,} "
          f"-> final {len(out):,}", flush=True)
    return out


def main(argv: list[str] | None = None) -> int:
    """Build both halves through both builds' steps and match them.

    Args:
        argv: Command line.

    Returns:
        0.
    """
    from thema.ontology.universe import load_embedded
    from theme_match import best_matches, summarise

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--frozen", type=Path,
                        default=Path("data/ontology/frozen/working-O50s-2026-10-22"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/S2_vs_O50s_2026-10-22"))
    parser.add_argument("--sides", action="store_true",
                        help="compute and cache the two half sides, then stop")
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    frozen = json.loads((args.frozen / "manifest.json").read_text())
    floors = frozen["floors"]
    strata = [tuple(s) for s in frozen["strata"]]
    keys = list(load_embedded(args.space_root, args.data / "pathways.tsv").keys)

    print("PROMPT 55 PART 2, SECTION F: STABILITY ACROSS HALF-BUILDS.")
    half_floors, notes = transfer_floors(floors, 100)
    print("  the stored floors are transferred to 100 runs: the six solved rates unchanged, the")
    print("  seven rule-of-three bound floors held at their RUN COUNT rather than their rate")
    for line in notes[:2]:
        print(f"    {line}")
    print(f"    ... {len(notes)} strata adjusted; applying the stored floors unchanged instead")
    print("    gates 38,811 and 38,565, of which 59.5% and 60.1% are single-run themes")
    sides = {}
    for half, low, high in HALVES:
        sides[half] = side_for(half, low, high, args)
    if args.sides:
        return 0

    built: dict[str, dict[str, dict[str, frozenset[str]]]] = {"O50s": {}, "S2": {}}
    for half, _low, _high in HALVES:
        print(f"  half {half}", flush=True)
        for style in ("O50s", "S2"):
            built[style][half] = half_build(style, sides[half], half_floors, strata,
                                            len(keys), keys)

    print()
    print("=" * 100)
    print("F. FINAL-THEME MATCH BETWEEN HALF-BUILDS, J >= 0.70, WORSE DIRECTION")
    print("=" * 100)
    rows = []
    print(f"  {'':<10}{'themes 1-100':>14}{'themes 101-200':>16}"
          f"{'1-100 -> 101-200':>19}{'101-200 -> 1-100':>19}{'WORSE':>9}")
    for style in ("O50s", "S2"):
        left, right = built[style]["1-100"], built[style]["101-200"]
        forward = summarise(best_matches(left, right))
        backward = summarise(best_matches(right, left))
        a = forward[f"share_ge_{MATCH_AT:.2f}"]
        b = backward[f"share_ge_{MATCH_AT:.2f}"]
        worse = min(a, b)
        rows.append({"style": style, "themes_first": len(left), "themes_second": len(right),
                     "forward": a, "backward": b, "worse": worse,
                     "forward_median": forward["median"], "backward_median": backward["median"]})
        print(f"  {style:<10}{len(left):>14,}{len(right):>16,}"
              f"{a:>19.4f}{b:>19.4f}{worse:>9.4f}")
    gap = rows[1]["worse"] - rows[0]["worse"]
    print(f"\n  S2 minus O50s on the worse direction: {gap:+.4f}")
    print(f"  {'':<10}{'median J 1-100 -> 101-200':>28}{'median J 101-200 -> 1-100':>28}")
    for row in rows:
        print(f"  {row['style']:<10}{row['forward_median']:>28.4f}"
              f"{row['backward_median']:>28.4f}")
    print()
    (args.out / "section_f.json").write_text(
        json.dumps({"match_at": MATCH_AT, "rows": rows,
                    "floors_note": notes,
                    "floors_rejected": {
                        "stored_unchanged_gated": [38811, 38565],
                        "single_run_share": [0.595, 0.601]}},
                   indent=1) + "\n", encoding="utf-8")
    print(f"  -> {args.out / 'section_f.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
