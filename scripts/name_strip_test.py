"""Measure how much of THEMA's collision-pair score is the pathway name rather than the biology.

The v3 prompt requires every description to open by repeating its pathway name. The cross-source
collision test defines its positives as pathways sharing a name. Both members of every collision
pair therefore carry the same string inside the text being embedded, and the 98.9% co-clustering
rate is inflated by an unknown amount. This script measures the amount by removing the name and
re-running the identical pipeline.

Nothing is paraphrased. The name is deleted and the surrounding words are left as they fall, so the
only difference between the two arms is the presence of the name -- substituting a rewritten
sentence would swap one intervention for another.

The chance rate is printed beside every observed rate, because a rate without one is unreadable: on
the gene-overlap baseline at k=25 a 98.9% co-clustering rate sat against a 94.86% chance rate, which
is a lift of 1x and means nothing at all.
"""

import argparse
import random
import sys
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.metrics import adjusted_rand_score

from thema.cluster import distances
from thema.data.pathways import PathwayCollection, collision_groups
from thema.data.tables import print_table
from thema.embed import embed
from thema.normalize import display_name, strip_name

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = REPO_ROOT / "data"

PATHWAY_TABLE = "pathways.tsv"
DESCRIPTIONS_TABLE = "pathway_descriptions.tsv"

CUTS = (10, 25, 50, 100, 200)
BANDS = ((0.0, 0.0), (0.0, 0.01), (0.01, 0.05), (0.05, 0.15), (0.15, 1.01))
BASELINE_DRAWS = 200_000


def read_descriptions(table: Path) -> dict[str, str]:
    """Read the generated descriptions out of the committed table.

    Args:
        table: Path to ``pathway_descriptions.tsv``.

    Returns:
        Pathway key to its generated description.
    """
    lines = table.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    key, text = header.index("key"), header.index("description_generated")
    return {row[key]: row[text] for row in (line.split("\t") for line in lines[1:] if line)}


def band_of(value: float) -> tuple[float, float]:
    """Which gene-overlap band a Jaccard value falls in."""
    for low, high in BANDS:
        if (low == high == 0.0 and value == 0.0) or (low < value <= high and high > 0):
            return (low, high)
    return BANDS[-1]


def band_label(low: float, high: float) -> str:
    """Render a band for a table."""
    return "exactly 0" if low == high == 0.0 else f"{low:g} < J <= {min(high, 1.0):g}"


def main(argv: list[str] | None = None) -> int:
    """Run the name-strip test."""
    parser = argparse.ArgumentParser(prog="name_strip_test.py", description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="data directory")
    parser.add_argument("--examples", type=int, default=5, help="before/after pairs to print")
    args = parser.parse_args(argv)

    pathways_table = args.data / PATHWAY_TABLE
    descriptions = args.data / DESCRIPTIONS_TABLE
    for path in (pathways_table, descriptions):
        if not path.is_file():
            print(f"missing input: {path}", file=sys.stderr)
            return 1

    collection = PathwayCollection.from_tsv_text(pathways_table.read_text(encoding="utf-8"))
    by_key = collection.by_key
    texts = {k: v for k, v in read_descriptions(descriptions).items() if k in by_key and v.strip()}
    keys = sorted(texts)
    position = {k: i for i, k in enumerate(keys)}

    stripped = {k: strip_name(texts[k], display_name(by_key[k])) for k in keys}
    changed = [k for k in keys if stripped[k] != texts[k]]
    shrunk = [len(texts[k]) - len(stripped[k]) for k in changed]
    print(f"\nNAME STRIP  ({len(keys):,} descriptions)\n")
    print(f"  changed by the strip : {len(changed):,}/{len(keys):,}")
    print(f"  characters removed   : median {int(np.median(shrunk))}, max {max(shrunk)}")
    unchanged = [k for k in keys if stripped[k] == texts[k]]
    print(f"  unchanged            : {len(unchanged)}  {unchanged[:4]}")

    print(f"\n  {args.examples} BEFORE/AFTER PAIRS\n")
    rng = random.Random(0)
    for key in rng.sample(changed, min(args.examples, len(changed))):
        print(f"  {key}  [{by_key[key].source}]  name={display_name(by_key[key])!r}")
        print(f"    before: {texts[key][:150]}")
        print(f"    after : {stripped[key][:150]}")
        print()

    print("re-embedding stripped text with the pinned revision", file=sys.stderr)
    vec_stripped = embed([stripped[k] for k in keys])
    vec_named = embed([texts[k] for k in keys])
    trees = {
        "name-carrying": linkage(distances(vec_named), method="ward"),
        "name-stripped": linkage(distances(vec_stripped), method="ward"),
    }
    labels = {
        arm: {k: fcluster(t, t=k, criterion="maxclust") for k in CUTS} for arm, t in trees.items()
    }

    groups = {
        n: m for n, m in collision_groups(collection).items() if all(p.key in position for p in m)
    }
    rng = random.Random(0)
    rows: list[tuple[str, ...]] = []
    for k in CUTS:
        cells: list[str] = []
        for arm in ("name-carrying", "name-stripped"):
            lab = labels[arm][k]
            together = sum(
                1 for m in groups.values() if len({lab[position[p.key]] for p in m}) == 1
            )
            chance = (
                sum(
                    1
                    for _ in range(BASELINE_DRAWS)
                    if lab[rng.randrange(len(keys))] == lab[rng.randrange(len(keys))]
                )
                / BASELINE_DRAWS
            )
            cells += [
                f"{together}/{len(groups)}",
                f"{together / len(groups):.1%}",
                f"{chance:.2%}",
                f"{(together / len(groups)) / chance:.0f}x",
            ]
        rows.append((str(k), *cells))
    print("\nCOLLISION CO-CLUSTERING, NAME-CARRYING vs NAME-STRIPPED\n")
    print_table(
        ("k", "kept", "rate", "chance", "lift", "stripped", "rate", "chance", "lift"),
        rows,
        align="><>>>>>>>",
    )

    banded: dict[tuple[float, float], list] = {b: [] for b in BANDS}
    for members in groups.values():
        pairs = [
            len(a.genes & b.genes) / len(a.genes | b.genes)
            for i, a in enumerate(members)
            for b in members[i + 1 :]
            if a.source != b.source and a.genes and b.genes
        ]
        if pairs:
            banded[band_of(sum(pairs) / len(pairs))].append(members)

    print("\nBY GENE-OVERLAP BAND (k=50)\n")
    band_rows = []
    for low, high in BANDS:
        members_in = banded[(low, high)]
        if not members_in:
            band_rows.append((band_label(low, high), "0", "-", "-"))
            continue
        cells = []
        for arm in ("name-carrying", "name-stripped"):
            lab = labels[arm][50]
            hit = sum(1 for m in members_in if len({lab[position[p.key]] for p in m}) == 1)
            cells.append(
                f"{hit}/{len(members_in)}"
                if len(members_in) < 10
                else f"{hit / len(members_in):.0%}"
            )
        band_rows.append((band_label(low, high), str(len(members_in)), *cells))
    print_table(("band", "n", "name-carrying", "name-stripped"), band_rows, align="<>>>")

    ari = adjusted_rand_score(labels["name-carrying"][50], labels["name-stripped"][50])
    print(f"\nARI between the two trees at k=50: {ari:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
