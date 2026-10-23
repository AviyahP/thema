"""PART 2 section E of prompt 55: sibling specificity AUROC, with CIs.

Declared 22 Oct 2026. Evaluation only; nothing is adopted and no verdict is offered.

**No existing script reports an AUROC**, so the measure is defined here and the definition is part
of the result:

* **Positives** are curator-declared sibling pairs -- two pathways sharing a parent in Reactome's
  relation or in GO -- taken from ``thema.evaluation.sibling_pairs``, in both the unrestricted form
  and the fan-out-capped form, because ``validate_dag`` reports neither alone and the cap is an
  untested judgement.
* **Negatives** are uniform random pathway pairs from the same universe, drawn once with
  ``validate_dag``'s own seed. They are deliberately **not** matched on gene overlap.
  ``validate_dag`` bands its null that way for a recovery rate; matching here would control away
  part of the very signal an AUROC is meant to measure, so the null is plain and this is stated
  rather than buried.
* The **score** of a pair is how many themes contain BOTH pathways. That is the graded form of
  ``validate_dag``'s "the pair shares at least one theme", which is boolean and so cannot be ranked.
* **AUROC** is the rank identity with ties counted as half, reusing ``top_two_arms.auc`` rather than
  a second implementation. 0.5 is chance.
* The **CI** is a percentile bootstrap resampling positives and negatives independently.

A higher AUROC means the build's themes co-locate curator-siblings more specifically than random
pairs. It says nothing about whether the themes read well.

Usage:
    uv run scripts/s2_sibling_auroc.py
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

NULL_DRAWS = 400_000
NULL_SEED = 20261003
BOOTSTRAP = 2_000
BOOTSTRAP_SEED = 20261003


def homes_of(directory: Path) -> dict[str, frozenset[str]]:
    """Pathway key to the themes holding it.

    Args:
        directory: A build directory.

    Returns:
        Key to theme ids.
    """
    got: dict[str, set[str]] = defaultdict(set)
    with (directory / "members.tsv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            got[row["key"]].add(row["node"])
    return {key: frozenset(nodes) for key, nodes in got.items()}


def co_membership(pairs: Sequence[tuple[str, str]],
                  homes: dict[str, frozenset[str]]) -> np.ndarray:
    """How many themes contain both members of each pair.

    Args:
        pairs: Key pairs.
        homes: Key to theme ids.

    Returns:
        One count per pair.
    """
    empty: frozenset[str] = frozenset()
    return np.array([len(homes.get(a, empty) & homes.get(b, empty)) for a, b in pairs],
                    dtype=np.float64)


def auroc_with_ci(positive: np.ndarray, negative: np.ndarray, seed: int
                  ) -> tuple[float | None, float, float]:
    """AUROC and a percentile bootstrap interval.

    Args:
        positive: Scores for curator-sibling pairs.
        negative: Scores for random pairs.
        seed: Bootstrap seed.

    Returns:
        ``(auroc, low, high)``.
    """
    from top_two_arms import auc

    point = auc(positive, negative)
    if point is None:
        return None, 0.0, 0.0
    rng = np.random.default_rng(seed)
    draws = np.empty(BOOTSTRAP, dtype=np.float64)
    for i in range(BOOTSTRAP):
        p = positive[rng.integers(0, len(positive), len(positive))]
        q = negative[rng.integers(0, len(negative), len(negative))]
        value = auc(p, q)
        draws[i] = np.nan if value is None else value
    low, high = np.nanpercentile(draws, [2.5, 97.5])
    return point, float(low), float(high)


def main(argv: list[str] | None = None) -> int:
    """Print the sibling AUROC table for S2 and O50s.

    Args:
        argv: Command line.

    Returns:
        0.
    """
    from compare_baselines import SIBLING_FANOUT
    from thema.data.hierarchy import read_reactome_relation
    from thema.evaluation import sibling_pairs
    from thema.ontology.evalsets import PRIMARY_RELATIONS, go_edges
    from thema.ontology.universe import load_embedded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--space-root", type=Path,
                        default=Path("data/ontology/v0.4-leaves-x2"))
    parser.add_argument("--o50s", type=Path,
                        default=Path("data/ontology/frozen/working-O50s-2026-10-22"))
    parser.add_argument("--s2", type=Path,
                        default=Path("data/ontology/v0.4-leaves/thema_L_x2_S2"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/experiments/S2_vs_O50s_2026-10-22"))
    args = parser.parse_args(argv)

    keys = list(load_embedded(args.space_root, args.data / "pathways.tsv").keys)
    universe = set(keys)
    raw = args.data / "raw"
    relation = read_reactome_relation(
        (raw / "ReactomePathwaysRelation.txt").read_text(encoding="utf-8").splitlines())
    go_parents = go_edges((raw / "go-basic.obo").read_text(encoding="utf-8").splitlines(),
                          PRIMARY_RELATIONS)

    sources = [
        sibling_pairs(relation, "reactome:", "reactome-siblings", "same-curator hierarchy"),
        sibling_pairs(relation, "reactome:", f"reactome-siblings (fan-out<={SIBLING_FANOUT})",
                      "same-curator hierarchy, broad parents dropped",
                      max_children=SIBLING_FANOUT),
        sibling_pairs(go_parents, "go:", "go-siblings", "same-curator hierarchy"),
        sibling_pairs(go_parents, "go:", f"go-siblings (fan-out<={SIBLING_FANOUT})",
                      "same-curator hierarchy, broad parents dropped",
                      max_children=SIBLING_FANOUT),
    ]

    rng = np.random.default_rng(NULL_SEED)
    order = sorted(universe)
    left = rng.integers(0, len(order), size=NULL_DRAWS)
    right = rng.integers(0, len(order), size=NULL_DRAWS)
    keep = left != right
    null_pairs = [(order[int(a)], order[int(b)])
                  for a, b in zip(left[keep], right[keep], strict=True)]
    print("PROMPT 55 PART 2, SECTION E: SIBLING SPECIFICITY AUROC.")
    print(f"  universe {len(universe):,} pathways; "
          f"{len(null_pairs):,} uniform random negative pairs, seed {NULL_SEED}")
    print(f"  bootstrap {BOOTSTRAP:,} resamples, seed {BOOTSTRAP_SEED}; ties count as half")
    print("  the negative pool is NOT matched on gene overlap; see this script's docstring")
    print()

    builds = {name: homes_of(path) for name, path in (("O50s", args.o50s), ("S2", args.s2))}
    rows = []
    print(f"  {'source':<42}{'pairs':>8}" + "".join(
        f"{n + ' AUROC':>16}{'95% CI':>20}" for n in builds))
    for source in sources:
        pairs = [(a, b) for a, b in source.pairs if a in universe and b in universe]
        if len(pairs) < 20:
            print(f"  {source.name:<42}{len(pairs):>8}   too few pairs in the universe")
            continue
        record = {"source": source.name, "pairs": len(pairs)}
        line = f"  {source.name:<42}{len(pairs):>8,}"
        for name, homes in builds.items():
            pos = co_membership(pairs, homes)
            neg = co_membership(null_pairs, homes)
            point, low, high = auroc_with_ci(pos, neg, BOOTSTRAP_SEED)
            record[name] = {"auroc": point, "ci": [low, high],
                            "mean_positive": float(pos.mean()),
                            "mean_negative": float(neg.mean())}
            line += f"{point:>16.4f}{f'[{low:.4f}, {high:.4f}]':>20}"
        rows.append(record)
        print(line, flush=True)
    print()
    print("  mean themes containing both members of a pair")
    print(f"  {'source':<42}" + "".join(
        f"{n + ' siblings':>18}{n + ' random':>18}" for n in builds))
    for record in rows:
        print(f"  {record['source']:<42}" + "".join(
            f"{record[n]['mean_positive']:>18.3f}{record[n]['mean_negative']:>18.3f}"
            for n in builds))
    print()
    print("  difference, S2 minus O50s")
    print(f"  {'source':<42}{'delta AUROC':>14}{'CIs overlap':>14}")
    for record in rows:
        delta = record["S2"]["auroc"] - record["O50s"]["auroc"]
        a, b = record["S2"]["ci"], record["O50s"]["ci"]
        overlap = not (a[0] > b[1] or b[0] > a[1])
        print(f"  {record['source']:<42}{delta:>+14.4f}{str(overlap):>14}")
    print()
    (args.out / "section_e_auroc.json").write_text(
        json.dumps({"null_draws": len(null_pairs), "null_seed": NULL_SEED,
                    "bootstrap": BOOTSTRAP, "rows": rows}, indent=1) + "\n",
        encoding="utf-8")
    print(f"  -> {args.out / 'section_e_auroc.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
