"""Export the built ontology into the object ``demo/prototype.html`` renders.

The prototype was written against hand-made ``THEMES`` and ``TREE`` literals. This script produces
the same two shapes from ``data/ontology/`` and writes them to ``demo/ontology.json``, plus a
one-line ``demo/ontology.js`` that assigns the same object to a global. The ``.js`` copy exists for
one reason: ``fetch`` is blocked on ``file://`` in every mainstream browser, and the page has to
open by double-clicking it.

Three levels of the ward tree are exported, nested. They really are nested -- ``fcluster`` at
several ``maxclust`` values on one linkage refines rather than reshuffles, and the script checks
that rather than assuming it, because a tree drawn from cuts that crossed would be quietly wrong.

Nothing statistical is exported, because nothing statistical has been computed: enrichment, soft
membership and the three attribution tests are all absent, and every field that would hold one
carries ``not computed``. See ``src/thema/demo.py`` for why that constant exists.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

from thema.data import descriptions as descriptions_table
from thema.demo import (
    LABEL_SEPARATOR,
    NO_DIRECTION,
    NOT_COMPUTED,
    NOT_COMPUTED_CELL,
    distinctive_terms,
    document_frequency,
    medoid,
    provisional_label,
    source_spread,
    uncomputed_tests,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = REPO_ROOT / "data"
DEFAULT_OUT = REPO_ROOT / "demo"

CLUSTERS = "ontology/clusters_ward.tsv"
EMBEDDINGS = "ontology/embeddings.npy"
EMBEDDING_KEYS = "ontology/embedding_keys.txt"
PATHWAYS = "pathways.tsv"
DESCRIPTIONS = "pathway_descriptions.tsv"

#: The three cuts of the ward tree that become depths 0, 1 and 2 on the page. The middle one is
#: the brief's declared working range; the outer two give a reader somewhere to go in each
#: direction without re-cutting.
LEVELS = (10, 50, 200)

#: The global the ``.js`` copy assigns to.
GLOBAL = "THEMA_ONTOLOGY"


def read_clusters(path: Path) -> list[dict[str, str]]:
    """Read the per-pathway cluster assignments.

    Args:
        path: Path to ``clusters_ward.tsv``.

    Returns:
        One row per pathway, in embedding order.
    """
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_column(path: Path, key: str, value: str) -> dict[str, str]:
    """Read two columns of a large TSV into a mapping.

    Args:
        path: The table.
        key: Column to key on.
        value: Column to take.

    Returns:
        Key to value, for every row that has both.
    """
    csv.field_size_limit(1 << 30)
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row[value] for row in csv.DictReader(handle, delimiter="\t")}


def read_genes(path: Path) -> dict[str, frozenset[str]]:
    """Read each pathway's resolved gene set.

    Args:
        path: Path to ``pathways.tsv``.

    Returns:
        Pathway key to its gene identifiers.
    """
    csv.field_size_limit(1 << 30)
    out: dict[str, frozenset[str]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            key = f"{row['source']}:{row['source_id']}"
            genes = row["genes"]
            out[key] = frozenset(genes.split(";")) if genes and genes != "-" else frozenset()
    return out


def check_nested(rows: list[dict[str, str]], levels: tuple[int, ...]) -> None:
    """Fail loudly if the exported cuts do not refine one another.

    Args:
        rows: The cluster table.
        levels: The cuts being exported, coarsest first.

    Raises:
        ValueError: If any cluster at a finer cut spans two clusters at a coarser one.
    """
    for fine, coarse in zip(levels[1:], levels[:-1], strict=True):
        seen: dict[str, str] = {}
        for row in rows:
            got = seen.setdefault(row[f"k{fine}"], row[f"k{coarse}"])
            if got != row[f"k{coarse}"]:
                raise ValueError(
                    f"k={fine} does not refine k={coarse}: cluster {row[f'k{fine}']} spans "
                    f"{got} and {row[f'k{coarse}']}. These cuts cannot be drawn as a tree."
                )


def node_id(level: int, cluster: str) -> str:
    """Name a node by the cut it came from and its label at that cut.

    Args:
        level: The cut size.
        cluster: The scipy cluster label.

    Returns:
        A stable identifier, unique across levels.
    """
    return f"k{level}:{cluster}"


def build(
    rows: list[dict[str, str]],
    genes: dict[str, frozenset[str]],
    descriptions: dict[str, str],
    vectors: np.ndarray,
    levels: tuple[int, ...],
    provenance: str,
    collection_size: int,
) -> dict[str, object]:
    """Assemble the whole export.

    Args:
        rows: The cluster table, in embedding order.
        genes: Pathway key to gene identifiers.
        descriptions: Pathway key to its generated description.
        vectors: The description embeddings, in the same order as ``rows``.
        levels: The cuts to export, coarsest first.
        provenance: The stamp the ontology build wrote onto its files.
        collection_size: How many pathways ``data/pathways.tsv`` holds in total.

    Returns:
        The object the page renders: ``build``, ``summary``, ``tree`` and ``themes``.
    """
    background = document_frequency(row["name"] for row in rows)
    total = len(rows)

    # Members of every cluster at every exported level, plus each cluster's parent one level up.
    members: dict[str, list[int]] = {}
    parent: dict[str, str | None] = {}
    for index, row in enumerate(rows):
        for depth, level in enumerate(levels):
            ident = node_id(level, row[f"k{level}"])
            members.setdefault(ident, []).append(index)
            parent[ident] = (
                None if depth == 0 else node_id(levels[depth - 1], row[f"k{levels[depth - 1]}"])
            )

    children: dict[str, list[str]] = {}
    for ident, above in parent.items():
        if above is not None:
            children.setdefault(above, []).append(ident)

    labels: dict[str, str] = {
        ident: provisional_label([rows[i]["name"] for i in rowset], background, total)
        for ident, rowset in members.items()
    }
    # Three terms is enough to separate most clusters and not all of them: two siblings both
    # labelled "process" are worse than a longer label, because a reader cannot tell which row
    # they are looking at. A collision is widened twice over -- more terms, and a lower bar for how
    # much of the cluster a term must cover -- because a cluster whose members share only one
    # common word needs the rarer vocabulary to tell it from its twin, and that vocabulary sits
    # below the default floor by definition.
    #
    # Two nodes holding the SAME pathways are not a collision. A cut that did not split its parent
    # produces one, and giving the two rows different labels would assert a difference that is not
    # there.
    sets = {ident: frozenset(rowset) for ident, rowset in members.items()}
    for limit, floor in ((4, 0.15), (5, 0.08), (6, 0.03), (8, 0.01)):
        taken: dict[str, list[str]] = {}
        for ident, label in labels.items():
            taken.setdefault(label, []).append(ident)
        clashing = [
            ident
            for group in taken.values()
            if len({sets[i] for i in group}) > 1
            for ident in group
        ]
        if not clashing:
            break
        for ident in clashing:
            terms = distinctive_terms(
                [rows[i]["name"] for i in members[ident]],
                background,
                total,
                limit=limit,
                floor=floor,
            )
            if terms:
                labels[ident] = LABEL_SEPARATOR.join(terms)

    def sort_key(ident: str) -> tuple[int, str]:
        """Order siblings by size, largest first, then by label."""
        return (-len(members[ident]), labels[ident])

    tree: list[dict[str, object]] = []
    themes: dict[str, object] = {}

    def walk(ident: str, depth: int) -> None:
        """Emit a node and then its children, depth first."""
        rowset = members[ident]
        kids = sorted(children.get(ident, []), key=sort_key)
        tree.append(
            {
                # Depth 0 groups the tree and is not itself offered as a theme, matching the
                # prototype; the page disables any node whose id is null.
                "id": None if depth == 0 else ident,
                "node": ident,
                "label": labels[ident],
                "depth": depth,
                "dir": NO_DIRECTION,
                "mag": 0,
                "ct": f"{len(kids)} themes" if depth == 0 else f"{len(rowset):,}",
            }
        )
        if depth > 0:
            themes[ident] = theme(ident, depth, rowset)
        for kid in kids:
            walk(kid, depth + 1)

    def theme(ident: str, depth: int, rowset: list[int]) -> dict[str, object]:
        """Build the detail panel for one node."""
        level = levels[depth]
        centre = medoid(rowset, vectors)
        spread = source_spread(rows[i]["source"] for i in rowset)
        union: set[str] = set()
        for i in rowset:
            union |= genes.get(rows[i]["key"], frozenset())
        above = parent[ident]
        return {
            "name": labels[ident],
            "depth": depth,
            "dir": NO_DIRECTION,
            "provisional": True,
            "metrics": [
                {"k": "pathways", "v": f"{len(rowset):,}"},
                {"k": "genes (union)", "v": f"{len(union):,}"},
                {"k": "FDR", "v": NOT_COMPUTED},
                {"k": "input coverage", "v": NOT_COMPUTED},
            ],
            "blurb": (
                f"{len(rowset):,} pathways from "
                + ", ".join(f"{source} {count}" for source, count in spread)
                + f", covering {len(union):,} distinct genes. "
                "The label above is provisional: it is the three most distinctive terms in the "
                "member names, not a written theme name. No theme has been named or described."
            ),
            "exemplar": {
                "key": rows[centre]["key"],
                "source": rows[centre]["source"],
                "name": rows[centre]["name"],
                "description": descriptions.get(rows[centre]["key"], ""),
            },
            "tests": uncomputed_tests(),
            "members": [
                [
                    rows[i]["source"],
                    rows[i]["name"],
                    NOT_COMPUTED_CELL,
                    NOT_COMPUTED_CELL,
                ]
                for i in sorted(rowset, key=lambda i: rows[i]["name"].lower())
            ],
            "note": (
                f"Cluster {ident.split(':')[1]} of {level} at the k={level} cut of the ward tree"
                + (f", inside {labels[above]}." if above else ".")
                + " Membership is hard at every cut, one pathway to one cluster; the soft "
                "membership the method calls for is not built, so every membership score below "
                "reads as not computed."
            ),
        }

    for root in sorted((i for i, p in parent.items() if p is None), key=sort_key):
        walk(root, 0)

    sources = source_spread(row["source"] for row in rows)
    return {
        "build": {
            "linkage": "ward",
            "levels": list(levels),
            "pathways": total,
            "collection": collection_size,
            "sources": [[source, count] for source, count in sources],
            "nodes": len(tree),
            "themes": len(themes),
            "provenance": provenance,
            "computed": {
                "ontology": True,
                "descriptions": True,
                "enrichment": False,
                "soft_membership": False,
                "attribution": False,
                "theme_names": False,
            },
        },
        "summary": [
            {"n": f"{total:,}", "l": "pathways in ontology"},
            {"n": f"{len(themes):,}", "l": "themes in tree", "small": f"{len(levels)} levels"},
            {"n": f"{len(sources)}", "l": "sources merged"},
            {"n": NOT_COMPUTED, "l": "enriched", "small": "FDR&lt;0.05"},
            {"n": NOT_COMPUTED, "l": "BH family"},
        ],
        "tree": tree,
        "themes": themes,
    }


def main(argv: list[str] | None = None) -> int:
    """Write ``demo/ontology.json`` and its ``.js`` twin."""
    parser = argparse.ArgumentParser(prog="export_demo.py", description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="data directory")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="where the demo lives")
    parser.add_argument(
        "--levels",
        type=int,
        nargs="+",
        default=list(LEVELS),
        help="cuts to export as depths 0..n, coarsest first (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    clusters = args.data / CLUSTERS
    for path in (clusters, args.data / PATHWAYS, args.data / DESCRIPTIONS):
        if not path.is_file():
            print(f"missing input: {path}", file=sys.stderr)
            print("run scripts/build_ontology.py first", file=sys.stderr)
            return 1

    rows = read_clusters(clusters)
    levels = tuple(args.levels)
    missing = [f"k{level}" for level in levels if f"k{level}" not in rows[0]]
    if missing:
        print(f"{clusters} has no {', '.join(missing)} column", file=sys.stderr)
        return 1
    check_nested(rows, levels)

    keys = [line for line in (args.data / EMBEDDING_KEYS).read_text().split("\n") if line]
    if keys != [row["key"] for row in rows]:
        print("embedding_keys.txt is not in the same order as clusters_ward.tsv", file=sys.stderr)
        return 1
    vectors = np.load(args.data / EMBEDDINGS)

    genes = read_genes(args.data / PATHWAYS)
    descriptions = descriptions_table.read(args.data / DESCRIPTIONS)
    collection_size = len(genes)
    provenance = next((row["provenance"] for row in rows if row["provenance"]), "")

    payload = build(rows, genes, descriptions, vectors, levels, provenance, collection_size)

    args.out.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=1)
    (args.out / "ontology.json").write_text(text + "\n", encoding="utf-8")
    (args.out / "ontology.js").write_text(
        f"/* Generated by scripts/export_demo.py. Do not edit. */\nwindow.{GLOBAL} = {text};\n",
        encoding="utf-8",
    )

    meta = payload["build"]
    assert isinstance(meta, dict)
    print(f"\nEXPORTED  ({provenance})\n")
    print(f"  pathways      {meta['pathways']:,} of {meta['collection']:,}")
    print(f"  sources       {', '.join(f'{s} {n}' for s, n in meta['sources'])}")
    print(f"  levels        {' -> '.join(f'k={k}' for k in levels)}")
    print(f"  tree nodes    {meta['nodes']:,} ({meta['themes']:,} clickable)")
    print("  not computed  enrichment, soft membership, attribution, theme names")
    print(f"\n  -> {args.out / 'ontology.json'}  ({len(text) / 1e6:.1f} MB)")
    print(f"  -> {args.out / 'ontology.js'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
