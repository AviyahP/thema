"""Embed the generated descriptions, build three trees from one distance matrix, and write them out.

The first clustering in this project, and deliberately small: the point is to look at a tree, not
to stand up a framework. No theme naming, no evaluation, no cut is declared the answer.

Three linkages are computed from the SAME distance matrix and reported side by side, because
picking one before looking is how a tree acquires a shape nobody chose. The cluster-size
distribution is printed per linkage and per cut and is the thing to read first: Ward assumes
clusters of broadly similar size, which biology has no obligation to supply, and average linkage's
known failure on uneven density is one enormous cluster plus a tail of singletons. Both look like
an ordinary tree from the outside and both are obvious in the size table.

Every output file states, on its face, the scope it was built from and the sha256 of the
descriptions table behind it. The risk this guards against is not confusing two files; it is
opening a tree in a fortnight and not knowing whether it was built on the smoke subset or on all
10,817. A tree that cannot answer that question is not evidence of anything.
"""

import argparse
import sys
from pathlib import Path

import numpy as np

from thema.cluster import DEFAULT_CUTS, condensed_bytes, cut, distances
from thema.cluster import size_distribution as sizes_of
from thema.cluster import trees as build_trees
from thema.data.pathways import PathwayCollection
from thema.data.tables import (
    SUMMARY_COLUMNS,
    cell,
    print_table,
    sha256_file,
    write_tsv,
)
from thema.embed import BIOLORD_MODEL, BIOLORD_REVISION, embed
from thema.normalize import PROVENANCE

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = REPO_ROOT / "data"

PATHWAY_TABLE = "pathways.tsv"
DESCRIPTIONS_TABLE = "pathway_descriptions.tsv"
DESCRIPTIONS_SUMMARY = "pathway_descriptions_summary.tsv"
ONTOLOGY_DIR = "ontology"
EMBEDDINGS = "embeddings.npy"
EMBEDDING_KEYS = "embedding_keys.txt"
ONTOLOGY_SUMMARY = "ontology_summary.tsv"

#: How many member names each cluster shows in the readable dump before it says how many more.
TREE_PREVIEW = 12


def read_descriptions(table: Path) -> dict[str, str]:
    """Read the generated descriptions out of the committed table.

    Args:
        table: Path to ``pathway_descriptions.tsv``.

    Returns:
        Pathway key to its generated description, in table order.
    """
    lines = table.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    key, text = header.index("key"), header.index("description_generated")
    return {row[key]: row[text] for row in (line.split("\t") for line in lines[1:] if line)}


def read_provenance(table: Path) -> set[str]:
    """Read the distinct ``description_generated_from`` values the table carries.

    Args:
        table: Path to ``pathway_descriptions.tsv``.

    Returns:
        The distinct provenance values found.
    """
    lines = table.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    if "description_generated_from" not in header:
        return set()
    index = header.index("description_generated_from")
    return {row[index] for row in (line.split("\t") for line in lines[1:] if line)}


def is_stand_in(scope: str, provenance: set[str]) -> bool:
    """Whether the clustered text was something other than generated descriptions.

    A plumbing run on native database prose produces a tree that looks exactly like a real one and
    is not one: native registers differ by an order of magnitude across sources, which is the whole
    reason the descriptions are generated. Anything the normalizer did not write is marked, so a
    tree cannot later be mistaken for a result.

    Args:
        scope: What the descriptions summary reported.
        provenance: The distinct ``description_generated_from`` values in the table.

    Returns:
        True when this run must be labelled a stand-in.
    """
    return scope not in ("smoke", "full") or not provenance <= set(PROVENANCE.values())


def read_scope(summary: Path) -> str:
    """Read which scope produced the descriptions table.

    Args:
        summary: Path to ``pathway_descriptions_summary.tsv``.

    Returns:
        ``smoke``, ``full``, or ``unknown`` when the summary is absent or says nothing.
    """
    if not summary.is_file():
        return "unknown"
    for line in summary.read_text(encoding="utf-8").splitlines()[1:]:
        fields = line.split("\t")
        if len(fields) > 2 and fields[0] == "input" and fields[1] == "scope":
            return fields[2]
    return "unknown"


def stamp(scope: str, digest: str, rows: int, stand_in: bool) -> str:
    """Render the provenance line every output file carries.

    Args:
        scope: The descriptions' scope.
        digest: The descriptions table's sha256.
        rows: How many descriptions were clustered.
        stand_in: Whether the clustered text was not generated by the normalizer.

    Returns:
        A one-line stamp, led by the stand-in warning when there is one so it cannot be skimmed
        past in a file header.
    """
    warning = "*** STAND-IN TEXT, NOT A RESULT *** " if stand_in else ""
    return f"{warning}scope={scope} descriptions={rows} sha256={digest[:16]} model={BIOLORD_MODEL}"


def write_clusters(
    path: Path,
    keys: list[str],
    collection: PathwayCollection,
    labels: dict[int, np.ndarray],
    header: str,
) -> None:
    """Write one row per pathway with its cluster id at each cut.

    Args:
        path: Where to write.
        keys: Pathway keys in embedding order.
        collection: The pathways, for source and name.
        labels: Cut size to the labels it produced.
        header: The provenance stamp, written as the first column's name suffix.
    """
    by_key = collection.by_key
    cuts = sorted(labels)
    columns = ("key", "source", "name", *(f"k{k}" for k in cuts), "provenance")
    rows = [
        (
            key,
            by_key[key].source,
            cell(by_key[key].name),
            *(str(labels[k][index]) for k in cuts),
            header if index == 0 else "",
        )
        for index, key in enumerate(keys)
    ]
    write_tsv(path, columns, rows)


def write_tree(
    path: Path,
    keys: list[str],
    collection: PathwayCollection,
    labels: np.ndarray,
    method: str,
    k: int,
    header: str,
) -> None:
    """Write the readable dump of one tree at one cut, largest cluster first.

    Args:
        path: Where to write.
        keys: Pathway keys in embedding order.
        collection: The pathways, for names and sources.
        labels: The cluster labels.
        method: The linkage.
        k: The requested cut.
        header: The provenance stamp.
    """
    by_key = collection.by_key
    members: dict[int, list[str]] = {}
    for key, label in zip(keys, labels, strict=True):
        members.setdefault(int(label), []).append(key)

    lines = [
        f"# {method} linkage, cut at k={k}",
        f"# {header}",
        f"# {len(members)} clusters over {len(keys)} pathways",
        "",
    ]
    for rank, (_label, group) in enumerate(
        sorted(members.items(), key=lambda item: (-len(item[1]), item[0])), start=1
    ):
        by_source: dict[str, int] = {}
        for key in group:
            by_source[by_key[key].source] = by_source.get(by_key[key].source, 0) + 1
        spread = " ".join(f"{s}:{n}" for s, n in sorted(by_source.items()))
        lines.append(f"[{rank:3d}] {len(group):5d} pathways   {spread}")
        for key in sorted(group, key=lambda key: by_key[key].name)[:TREE_PREVIEW]:
            lines.append(f"        {by_key[key].source:9s} {by_key[key].name}")
        if len(group) > TREE_PREVIEW:
            lines.append(f"        ... (+{len(group) - TREE_PREVIEW} more)")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Build the ontology trees."""
    parser = argparse.ArgumentParser(prog="build_ontology.py", description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="data directory")
    parser.add_argument(
        "--cuts",
        type=int,
        nargs="+",
        default=list(DEFAULT_CUTS),
        help="tree depths to cut at (default: %(default)s)",
    )
    parser.add_argument("--model", default=BIOLORD_MODEL, help="encoder (default: %(default)s)")
    parser.add_argument("--revision", default=BIOLORD_REVISION, help="encoder revision")
    args = parser.parse_args(argv)

    pathways = args.data / PATHWAY_TABLE
    table = args.data / DESCRIPTIONS_TABLE
    for path in (pathways, table):
        if not path.is_file():
            print(f"missing input: {path}", file=sys.stderr)
            print("run scripts/normalize_descriptions.py --smoke --submit", file=sys.stderr)
            return 1

    collection = PathwayCollection.from_tsv_text(pathways.read_text(encoding="utf-8"))
    by_key = collection.by_key
    texts = {k: v for k, v in read_descriptions(table).items() if k in by_key and v.strip()}
    keys = sorted(texts)
    if len(keys) < 2:
        print(f"need at least two descriptions to cluster, found {len(keys)}", file=sys.stderr)
        return 1

    digest = sha256_file(table)
    scope = read_scope(args.data / DESCRIPTIONS_SUMMARY)
    provenance = read_provenance(table)
    stand_in = is_stand_in(scope, provenance)
    header = stamp(scope, digest, len(keys), stand_in)
    if stand_in:
        print(
            "WARNING: the clustered text was not produced by the normalizer. This is a plumbing "
            "run and its trees must not be read as a result.",
            file=sys.stderr,
        )
    out = args.data / ONTOLOGY_DIR
    out.mkdir(parents=True, exist_ok=True)

    print(f"\nBUILDING ONTOLOGY  ({header})\n")
    print(f"embedding {len(keys):,} descriptions with {args.model}", file=sys.stderr)
    vectors = embed([texts[k] for k in keys], model=args.model, revision=args.revision)
    np.save(out / EMBEDDINGS, vectors)
    (out / EMBEDDING_KEYS).write_text("\n".join(keys) + "\n", encoding="utf-8")

    # The one thing here that grows as the square of the input, and the reason a full run might not
    # fit where a smoke run does. Measured and reported rather than discovered by an OOM kill.
    print(
        f"distance matrix: {condensed_bytes(len(keys)) / 1e6:,.1f} MB at {len(keys):,}; "
        f"{condensed_bytes(len(collection)) / 1e6:,.1f} MB at {len(collection):,}",
        file=sys.stderr,
    )
    condensed = distances(vectors)
    trees = build_trees(condensed)

    rows: list[tuple[str, ...]] = []
    written: list[Path] = [out / EMBEDDINGS]
    for method, tree in trees.items():
        labels = {k: cut(tree, k) for k in args.cuts if k < len(keys)}
        clusters = out / f"clusters_{method}.tsv"
        write_clusters(clusters, keys, collection, labels, header)
        written.append(clusters)
        for k, label in labels.items():
            write_tree(out / f"tree_{method}_k{k}.txt", keys, collection, label, method, k, header)
            spread = sizes_of(label)
            rows.append(
                (
                    method,
                    str(k),
                    f"{spread['clusters']:.0f}",
                    "/".join(f"{spread[m]:.0f}" for m in ("min", "p10", "median", "p90", "max")),
                    f"{spread['singletons']:.0f}",
                    f"{spread['largest_share']:.1%}",
                )
            )

    print("\nCLUSTER SIZE DISTRIBUTION\n")
    print_table(
        ("linkage", "k", "clusters", "min/p10/med/p90/max", "singletons", "largest share"),
        rows,
        align="<>>>>>",
    )

    summary: list[tuple[str, ...]] = [
        (
            "caveat",
            "text_provenance",
            "STAND-IN" if stand_in else "generated",
            "the clustered text was NOT produced by the normalizer: this is a plumbing check of "
            "the pipeline, not a result, and its trees must not be read as one. Native registers "
            "differ by an order of magnitude across sources, which is what the generated "
            "descriptions exist to remove"
            if stand_in
            else "descriptions written by the normalizer, as intended",
        ),
        (
            "input",
            "description_generated_from",
            ";".join(sorted(provenance)) or "-",
            "provenance values found in the descriptions table",
        ),
        ("input", "scope", scope, "which generation run the descriptions came from"),
        ("input", "description_rows", str(len(keys)), "descriptions clustered"),
        ("input", "collection_rows", str(len(collection)), "pathways in data/pathways.tsv"),
        ("input", "descriptions_sha256", digest, "the table these trees were built from"),
        ("input", "embedding_model", f"{args.model}@{args.revision}", "pinned by revision"),
        ("input", "embedding_dim", str(vectors.shape[1]), ""),
        (
            "input",
            "normalization",
            "l2",
            "unit vectors, so Euclidean distance is monotone in cosine and Ward is legitimate",
        ),
        *(
            (
                "digest",
                path.name,
                sha256_file(path),
                "regenerable from the descriptions table and the pinned encoder; gitignored",
            )
            for path in written
        ),
        (
            "memory",
            "condensed_matrix_mb",
            f"{condensed_bytes(len(keys)) / 1e6:.1f}",
            f"{condensed_bytes(len(collection)) / 1e6:.1f} MB at the full {len(collection):,}; "
            "above roughly 2 GB, ward can be built by fastcluster.linkage_vector from the vectors "
            "directly, which needs no n^2 matrix. average and complete still need one",
        ),
    ]
    for row in rows:
        summary.append(
            ("size", f"{row[0]}_k{row[1]}", row[3], f"clusters={row[2]} largest={row[5]}")
        )
    write_tsv(out / ONTOLOGY_SUMMARY, SUMMARY_COLUMNS, summary)
    print(f"\n{len(trees)} linkages x {len(args.cuts)} cuts -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
