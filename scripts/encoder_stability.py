"""Ask whether the theme tree is a fact about biology or about one encoder.

Removing about 37 characters from each description moved 48.1% of pathways to a different cluster.
That is enough instability to make the question live: if two unrelated encoders, given the same
text, build the same tree, the structure is in the biology; if they do not, part of what the tree
shows is one model's idiosyncrasy and the write-up has to say so.

BioLORD-2023 is trained so that embedding geometry mirrors ontology structure. Qwen3-Embedding-0.6B
is a strong general-purpose embedder with no biomedical training at all (docs/brief.md D7 names it
as the comparison arm). They share no training objective, so agreement between their trees is not
explained by a shared prior.

Local, no API cost. The first run downloads the Qwen weights.
"""

import argparse
import random
import sys
from pathlib import Path

from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.metrics import adjusted_rand_score

from compare_baselines import auroc, cosine_pairs
from thema.cluster import DEFAULT_CUTS, distances, size_distribution
from thema.data.formats import parse_obo_terms
from thema.data.hierarchy import read_reactome_relation
from thema.data.pathways import PathwayCollection
from thema.data.tables import SUMMARY_COLUMNS, print_table, write_tsv
from thema.embed import BIOLORD_MODEL, BIOLORD_REVISION, QWEN_MODEL, QWEN_REVISION, embed
from thema.evaluation import (
    BANDS,
    QUOTABLE,
    band_label,
    band_of,
    go_parents,
    jaccard,
    sibling_pairs,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = REPO_ROOT / "data"


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


def main(argv: list[str] | None = None) -> int:
    """Compare the trees two encoders build from identical text."""
    parser = argparse.ArgumentParser(
        prog="encoder_stability.py", description=__doc__.splitlines()[0]
    )
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="data directory")
    args = parser.parse_args(argv)

    table = args.data / "pathway_descriptions.tsv"
    if not table.is_file():
        print(f"missing input: {table}", file=sys.stderr)
        return 1
    collection = PathwayCollection.from_tsv_text(
        (args.data / "pathways.tsv").read_text(encoding="utf-8")
    )
    by_key = collection.by_key
    texts = {k: v for k, v in read_descriptions(table).items() if k in by_key and v.strip()}
    keys = sorted(texts)
    corpus = [texts[k] for k in keys]

    print(f"\nENCODER STABILITY  ({len(keys):,} descriptions, identical text to both encoders)\n")
    trees, vecs = {}, {}
    for label, model, revision in (
        ("biolord", BIOLORD_MODEL, BIOLORD_REVISION),
        ("qwen3", QWEN_MODEL, QWEN_REVISION),
    ):
        print(f"embedding with {model}", file=sys.stderr)
        vectors = embed(corpus, model=model, revision=revision)
        vecs[label] = vectors
        trees[label] = (linkage(distances(vectors), "ward"), vectors.shape[1])

    rows: list[tuple[str, ...]] = []
    summary: list[tuple[str, ...]] = [
        ("input", "descriptions", str(len(keys)), "identical text to both encoders"),
        ("input", "biolord", f"{BIOLORD_MODEL}@{BIOLORD_REVISION}", f"dim {trees['biolord'][1]}"),
        ("input", "qwen3", f"{QWEN_MODEL}@{QWEN_REVISION}", f"dim {trees['qwen3'][1]}"),
    ]
    for k in DEFAULT_CUTS:
        if k >= len(keys):
            continue
        bio = fcluster(trees["biolord"][0], t=k, criterion="maxclust")
        qwen = fcluster(trees["qwen3"][0], t=k, criterion="maxclust")
        ari = adjusted_rand_score(bio, qwen)
        b_share = size_distribution(bio)["largest_share"]
        q_share = size_distribution(qwen)["largest_share"]
        b_single = size_distribution(bio)["singletons"]
        q_single = size_distribution(qwen)["singletons"]
        rows.append(
            (
                str(k),
                f"{ari:.3f}",
                f"{b_share:.1%}",
                f"{q_share:.1%}",
                f"{b_single:.0f}",
                f"{q_single:.0f}",
            )
        )
        summary.append(("ari", f"k{k}", f"{ari:.4f}", "adjusted Rand, biolord vs qwen3"))
        summary.append(
            (
                "largest_share",
                f"k{k}",
                f"{b_share:.4f}/{q_share:.4f}",
                "biolord/qwen3",
            )
        )
    print_table(
        ("k", "ARI", "biolord largest", "qwen3 largest", "bio singletons", "qwen singletons"),
        rows,
        align=">>>>>>",
    )

    best = max(float(r[1]) for r in rows)
    print(
        "\nHOW TO READ THIS\n"
        "  These two encoders share no training objective: BioLORD-2023 is trained so embedding\n"
        "  geometry mirrors ontology structure, Qwen3-Embedding-0.6B has no biomedical training.\n"
        "  Agreement between their trees therefore is not explained by a shared prior.\n"
        f"\n  Peak ARI across the cuts is {best:.3f}. For scale: two random partitions score ~0,\n"
        "  identical partitions score 1, and the SAME encoder on the same text with the pathway\n"
        "  name deleted scored 0.348 -- so a value near or below that means the encoder choice\n"
        "  moves the tree about as much as removing the subject of every sentence does.\n"
    )
    # Partition ARI is a harsh metric: it asks whether two trees agree on exact cluster
    # membership. The claim does not rest on that -- it rests on whether curated pairs sit closer
    # together than random pairs of the same gene overlap, which needs no cut at all. If that
    # survives the encoder swap, the finding is about the biology even where the partition is not.
    print("\nDOES THE CLAIM SURVIVE THE ENCODER SWAP? (cut-free, no partition involved)\n")

    raw = args.data / "raw"
    relation = read_reactome_relation(
        (raw / "ReactomePathwaysRelation.txt").read_text(encoding="utf-8").splitlines()
    )
    with (raw / "go-basic.obo").open("r", encoding="utf-8") as handle:
        terms = parse_obo_terms(handle, namespace="biological_process")
    position = {k: i for i, k in enumerate(keys)}
    pathways = [by_key[k] for k in keys]
    sources = {
        "reactome-siblings": sibling_pairs(relation, "reactome:", "r", "c"),
        "go-siblings": sibling_pairs(go_parents(terms), "go:", "g", "c"),
    }

    rng = random.Random(0)
    auc_rows: list[tuple[str, ...]] = []
    for source_name, source in sources.items():
        pairs = [
            (position[a], position[b]) for a, b in source.pairs if a in position and b in position
        ]
        banded: dict[tuple[float, float], list[tuple[int, int]]] = {b: [] for b in BANDS}
        for i, j in pairs:
            value = jaccard(pathways[i], pathways[j])
            if value is not None:
                banded[band_of(value)].append((i, j))
        used = [b for b in reversed(BANDS) if len(banded[b]) >= QUOTABLE]
        controls = {}
        for band in used:
            pool: list[tuple[int, int]] = []
            while len(pool) < 2000:
                i, j = rng.randrange(len(keys)), rng.randrange(len(keys))
                if i == j:
                    continue
                value = jaccard(pathways[i], pathways[j])
                if value is not None and band_of(value) == band:
                    pool.append((i, j))
            controls[band] = pool
        for label in ("biolord", "qwen3"):
            vectors = vecs[label]
            auc_rows.append(
                (
                    f"{source_name} / {label}",
                    *(
                        f"{auroc(cosine_pairs(vectors, banded[b]), cosine_pairs(vectors, controls[b])):.2f}"  # noqa: E501
                        for b in used
                    ),
                )
            )
        for b in used:
            for label in ("biolord", "qwen3"):
                value = auroc(
                    cosine_pairs(vecs[label], banded[b]), cosine_pairs(vecs[label], controls[b])
                )
                summary.append(
                    ("auroc", f"{source_name}/{label}/{band_label(*b)}", f"{value:.4f}", "cut-free")
                )
        if used:
            print_table(
                ("source / encoder", *(band_label(*b) for b in used)),
                [r for r in auc_rows if r[0].startswith(source_name)],
                align="<" + ">" * len(used),
            )
            print()

    out = args.data / "ontology" / "encoder_stability.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_tsv(out, SUMMARY_COLUMNS, summary)
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
