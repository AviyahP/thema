#!/usr/bin/env python3
"""The 16 primary scores of the engine search, and the declared decision rule over them.

16 = 4 cells (Reactome siblings and GO siblings x zero gene overlap and pooled) x 4 theme-size bands
(3-10, 11-50, 51-200, 201-500). Each score is the band-restricted specificity AUROC, the same
measure the 5 Oct report's C3 used, and the band restriction is what makes arms of different
granularity comparable at all.

**The bootstrap is PAIRED and that is not a detail.** The resampled curated parents are drawn once
per cell and every arm is scored on the same draw, so the difference between two arms is a
difference on identical data. Resampling each arm independently would widen every interval by the
variance of a comparison nobody is making. One consequence is worth stating: because the draws are
shared, every pairwise CI the dominance rule needs comes from subtracting two stored bootstrap
curves, so adding an arm costs one more curve rather than one more curve per existing arm.

Then §0's rule, applied exactly as declared: dominance first, max-min among the survivors.

Usage::

    uv run scripts/engine_scores.py --arm A=recurrent_dag_10770 --arm B=v0.3x_engines/leiden
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

from granularity_bands import SIZE_BANDS, read_arm, smallest_in_band  # noqa: E402
from hidef_decision import (  # noqa: E402
    BOOTSTRAP,
    BOOTSTRAP_SEED,
    EQUIVALENCE_MARGIN,
    NULL_DRAWS,
    NULL_SEED,
    _parent_of,
    auroc_from_ranks,
)
from thema.data.formats import parse_obo_terms  # noqa: E402
from thema.data.hierarchy import read_reactome_relation  # noqa: E402
from thema.data.pathways import PathwayCollection  # noqa: E402
from thema.evaluation import go_parents, jaccard, restrict, sibling_pairs  # noqa: E402
from thema.ontology.universe import load_embedded  # noqa: E402


def bootstrap_curves(
    spec: dict[str, np.ndarray],
    ref: dict[str, np.ndarray],
    groups: list[str],
    index: np.ndarray,
) -> dict[str, np.ndarray]:
    """One bootstrap curve per arm, all arms on the SAME resampled parents.

    Args:
        spec: Arm to per-pair specificity.
        ref: Arm to its sorted null values.
        groups: Curated parent label per pair.
        index: Which pairs are in this cell.

    Returns:
        Arm to a ``(BOOTSTRAP,)`` array of AUROCs.
    """
    buckets: dict[str, list[int]] = defaultdict(list)
    for i in index.tolist():
        buckets[groups[i]].append(i)
    members = [np.array(v, dtype=np.int64) for v in buckets.values()]
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    out = {name: np.empty(BOOTSTRAP) for name in spec}
    for r in range(BOOTSTRAP):
        drawn = rng.integers(0, len(members), size=len(members))
        picked = np.concatenate([members[d] for d in drawn])
        for name in spec:
            out[name][r] = auroc_from_ranks(spec[name][picked], ref[name])
    return out


def reading_of(low: float, high: float) -> str:
    """How a paired interval reads against the declared margin.

    Args:
        low: Lower bound of (other - reference).
        high: Upper bound.

    Returns:
        One of ``"better"``, ``"worse"``, ``"equivalent"``, ``"inconclusive"``.
    """
    if low >= -EQUIVALENCE_MARGIN and high <= EQUIVALENCE_MARGIN:
        return "equivalent"
    if low > 0.0:
        return "better"
    if high < 0.0:
        return "worse"
    return "inconclusive"


def decide(
    arms: list[str],
    scores: dict[str, dict[str, float]],
    curves: dict[str, dict[str, np.ndarray]],
    eligible: list[str],
) -> dict:
    """Apply §0's decision rule: dominance, then max-min among the non-dominated.

    Args:
        arms: Every arm scored.
        scores: Cell key to arm to AUROC.
        curves: Cell key to arm to bootstrap curve.
        eligible: Arms that passed the gates. Only these can dominate or win.

    Returns:
        The verdict, with the working shown.
    """
    cells = list(scores)
    dominated: dict[str, list[str]] = {}
    for x in eligible:
        for y in eligible:
            if x == y:
                continue
            # Y dominates X if Y is better by > margin with the CI excluding 0 somewhere, and
            # nowhere worse by > margin with the CI excluding 0.
            beats, loses = False, False
            for cell in cells:
                diff = curves[cell][y] - curves[cell][x]
                low = float(np.percentile(diff, 2.5))
                high = float(np.percentile(diff, 97.5))
                gap = scores[cell][y] - scores[cell][x]
                if gap > EQUIVALENCE_MARGIN and low > 0.0:
                    beats = True
                if gap < -EQUIVALENCE_MARGIN and high < 0.0:
                    loses = True
            if beats and not loses:
                dominated.setdefault(x, []).append(y)
    surviving = [a for a in eligible if a not in dominated]

    shortfall: dict[str, float] = {}
    worst_cell: dict[str, str] = {}
    for arm in surviving:
        gaps = {c: max(scores[c][b] for b in eligible) - scores[c][arm] for c in cells}
        worst = max(gaps, key=lambda c: gaps[c])
        shortfall[arm] = gaps[worst]
        worst_cell[arm] = worst
    ranked = sorted(surviving, key=lambda a: shortfall[a])
    winner = ranked[0] if ranked else None
    tied = [a for a in ranked if winner and shortfall[a] - shortfall[winner] <= 0.01]
    return {
        "eligible": eligible,
        "dominated": {k: sorted(v) for k, v in dominated.items()},
        "non_dominated": surviving,
        "shortfall": {a: round(shortfall[a], 4) for a in surviving},
        "worst_cell": worst_cell,
        "ranked": ranked,
        "winner": winner,
        "tied_within_0.01": tied,
        "arms_scored": arms,
    }


def main(argv: list[str] | None = None) -> int:
    """Score every arm and apply the rule.

    Args:
        argv: Command-line arguments.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--version", default="0.3")
    parser.add_argument("--arm", action="append", default=[],
                        help="NAME=path, the path relative to data/ontology/ (so an engine arm is "
                             "v0.3x_engines/leiden). Repeatable")
    parser.add_argument("--eligible", default="",
                        help="comma-separated arms that passed the gates; only these can win. "
                             "Default: every arm given, which is only right if all passed")
    parser.add_argument("--reference", default="A",
                        help="arm the printed differences are stated against")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--tsv", type=Path, default=None)
    args = parser.parse_args(argv)

    base = args.data / "ontology"
    root = base / f"v{args.version}"
    wanted = [a.split("=", 1) for a in args.arm]
    arms = {name: read_arm(base / path) for name, path in wanted
            if (base / path / "members.tsv").is_file()}
    missing = [name for name, path in wanted if not (base / path / "members.tsv").is_file()]
    if not arms:
        print("no arm directories found", flush=True)
        return 1
    print(f"ENGINE SCORES  arms: {', '.join(arms)}"
          + (f"   MISSING: {', '.join(missing)}" if missing else ""), flush=True)

    embedded = load_embedded(root, args.data / "pathways.tsv")
    keys = list(embedded.keys)
    present = set(keys)
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8")
    )
    by_key = {p.key: p for p in collection.pathways if p.key in present}

    rng = np.random.default_rng(NULL_SEED)
    ia = rng.integers(0, len(keys), size=NULL_DRAWS)
    ib = rng.integers(0, len(keys), size=NULL_DRAWS)
    keep = ia != ib
    ia, ib = ia[keep], ib[keep]
    null_left = [keys[i] for i in ia]
    null_right = [keys[j] for j in ib]
    gene_null = np.array([
        (lambda v: -1.0 if v is None else v)(jaccard(by_key[a], by_key[b]))
        for a, b in zip(null_left, null_right, strict=True)
    ])
    zero_null = gene_null == 0.0

    raw = args.data / "raw"
    relation = read_reactome_relation(
        (raw / "ReactomePathwaysRelation.txt").read_text(encoding="utf-8").splitlines()
    )
    terms = parse_obo_terms((raw / "go-basic.obo").read_text(encoding="utf-8").splitlines())
    sources = {
        "Reactome": (sibling_pairs(relation, "reactome:", "r", ""), relation, "reactome:"),
        "GO": (sibling_pairs(go_parents(terms), "go:", "g", ""), go_parents(terms), "go:"),
    }

    scores: dict[str, dict[str, float]] = {}
    recovery: dict[str, dict[str, float]] = {}
    curves: dict[str, dict[str, np.ndarray]] = {}
    counts: dict[str, int] = {}
    rows: list[tuple[str, ...]] = []

    for source_name, (source, relation_map, prefix) in sources.items():
        kept = restrict(source, present)
        left = [a for a, _ in kept.pairs]
        right = [b for _, b in kept.pairs]
        gvals = np.array([(lambda v: -1.0 if v is None else v)(
            jaccard(by_key[a], by_key[b])) for a, b in zip(left, right, strict=True)])
        zero = gvals == 0.0
        groups = _parent_of(relation_map, prefix, left, right)
        print(f"\n{'=' * 104}\n{source_name} siblings: {len(left):,} pairs, "
              f"{int(zero.sum()):,} at zero gene overlap\n{'=' * 104}", flush=True)

        for low, high in SIZE_BANDS:
            spec = {n: smallest_in_band(h, s, left, right, low, high)
                    for n, (h, s, _r) in arms.items()}
            nspec = {n: smallest_in_band(h, s, null_left, null_right, low, high)
                     for n, (h, s, _r) in arms.items()}
            for gene_band, mask, nmask in (
                ("zero-gene", zero, zero_null),
                ("pooled", np.ones(len(left), dtype=bool), np.ones(len(ia), dtype=bool)),
            ):
                cell = f"{source_name}|{gene_band}|{low}-{high}"
                idx = np.flatnonzero(mask)
                ref = {n: np.sort(nspec[n][nmask]) for n in arms}
                scores[cell] = {n: auroc_from_ranks(spec[n][mask], ref[n]) for n in arms}
                recovery[cell] = {n: float(np.isfinite(spec[n][mask]).mean()) for n in arms}
                counts[cell] = int(mask.sum())
                curves[cell] = bootstrap_curves(spec, ref, groups, idx)

                print(f"\n  {source_name}, themes {low}-{high}, {gene_band} "
                      f"-- {counts[cell]:,} pairs", flush=True)
                head = f"    {'arm':<6} {'AUROC':>7} {'recov':>7}"
                if args.reference in arms:
                    head += f"   vs {args.reference}: {'diff':>8} {'CI':>20}  reading"
                print(head)
                for n in arms:
                    line = f"    {n:<6} {scores[cell][n]:>7.4f} {recovery[cell][n]:>6.1%}"
                    if args.reference in arms and n != args.reference:
                        diff = curves[cell][n] - curves[cell][args.reference]
                        lo = float(np.percentile(diff, 2.5))
                        hi = float(np.percentile(diff, 97.5))
                        gap = scores[cell][n] - scores[cell][args.reference]
                        read = reading_of(lo, hi)
                        line += f"   {gap:>+8.4f} [{lo:>+8.4f},{hi:>+8.4f}]  {read}"
                        rows.append((source_name, gene_band, f"{low}-{high}", n,
                                     str(counts[cell]), f"{scores[cell][n]:.4f}",
                                     f"{recovery[cell][n]:.4f}",
                                     f"{scores[cell][args.reference]:.4f}",
                                     f"{gap:+.4f}", f"{lo:+.4f}", f"{hi:+.4f}", read))
                    print(line, flush=True)

    eligible = [a.strip() for a in args.eligible.split(",") if a.strip()] or list(arms)
    eligible = [a for a in eligible if a in arms]
    verdict = decide(list(arms), scores, curves, eligible)

    print(f"\n{'=' * 104}\nTHE DECLARED RULE\n{'=' * 104}")
    print(f"  eligible (passed the gates): {', '.join(verdict['eligible']) or 'NONE'}")
    if verdict["dominated"]:
        for x, ys in verdict["dominated"].items():
            print(f"  {x} is DOMINATED by {', '.join(ys)}")
    else:
        print("  no arm is dominated")
    print(f"  non-dominated: {', '.join(verdict['non_dominated']) or 'NONE'}")
    for arm in verdict["ranked"]:
        print(f"    {arm:<6} shortfall {verdict['shortfall'][arm]:+.4f} "
              f"(worst cell {verdict['worst_cell'][arm]})")
    if verdict["winner"] is None:
        print("\n  Under the declared rule, NO ARM PASSES THE GATES.")
    else:
        print(f"\n  Under the declared rule, the candidate is {verdict['winner']}.")
        if len(verdict["tied_within_0.01"]) > 1:
            print(f"  TIED within 0.01: {', '.join(verdict['tied_within_0.01'])} "
                  f"-- broken on knobs, then wall time")

    if args.tsv:
        args.tsv.parent.mkdir(parents=True, exist_ok=True)
        with args.tsv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerow(["source", "gene_band", "size_band", "arm", "n", "auroc", "recovery",
                             "auroc_ref", "diff", "ci_low", "ci_high", "reading"])
            writer.writerows(rows)
        print(f"\n  -> {args.tsv}")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({
            "arms": list(arms), "missing": missing, "reference": args.reference,
            "bootstrap": "paired cluster over curated parents",
            "resamples": BOOTSTRAP, "seed": BOOTSTRAP_SEED,
            "equivalence_margin": EQUIVALENCE_MARGIN,
            "n_pairs": counts,
            "auroc": {c: {a: round(v, 4) for a, v in s.items()} for c, s in scores.items()},
            "recovery": {c: {a: round(v, 4) for a, v in s.items()}
                         for c, s in recovery.items()},
            "ci": {c: {a: [round(float(np.percentile(curves[c][a] - curves[c][args.reference],
                                                     2.5)), 4),
                           round(float(np.percentile(curves[c][a] - curves[c][args.reference],
                                                     97.5)), 4)]
                       for a in arms if a != args.reference} for c in curves},
            "verdict": verdict,
        }, indent=2) + "\n", encoding="utf-8")
        print(f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
