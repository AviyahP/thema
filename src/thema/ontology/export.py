"""Write an ontology to a versioned directory, validated before it replaces anything.

Layout is ``data/ontology/v<version>/<method>/``, holding ``nodes.tsv``, ``members.tsv``,
``edges.tsv``, ``unplaced.tsv`` and ``manifest.json`` (spec §8).

**Replace-within-version, not merge** (``docs/spec/addendum-2026-09-18.md`` A4). ``merge_tsv``
protects shared tables where two runs contribute rows that must coexist -- the descriptions table
across prompt generations, the experiment flags across arms. A rebuilt ontology is not that: it
supersedes its predecessor in full, and merging on a per-build generated node id would accumulate
stale nodes that no run produced and nothing would notice. The version in the path is what keeps an
older build from being destroyed.

**The swap is not atomic, and says so rather than implying it.** ``write_tsv`` is atomic per file
(a ``.part`` sibling plus ``Path.replace``), but there is no directory-level equivalent:
``os.replace`` on a populated directory fails on POSIX. So the sequence is build to ``.part``, move
any existing ``<dir>`` to ``<dir>.old``, move ``.part`` into place, then remove ``.old``. The window
between the last two moves is short and leaves ``.old`` recoverable, which is the most this can
offer without a transactional filesystem.
"""

import csv
import json
import shutil
from collections.abc import Sequence
from pathlib import Path

from thema.data.tables import write_tsv
from thema.ontology.base import Ontology

NODE_COLUMNS = ("id", "support", "n_members", "n_genes", "label", "provisional")
MEMBER_COLUMNS = ("key", "node", "inclusion", "gene_support")
EDGE_COLUMNS = ("child", "parent")
UNPLACED_COLUMNS = ("key",)

#: Written while the directory is being built, and never seen by a reader: the swap only happens
#: once validation has passed.
PART = ".part"

#: Where the previous build goes during the swap. Removed on success; left behind on a crash, which
#: is the recovery path.
OLD = ".old"


def gene_counts(
    ontology: Ontology, genes: dict[str, frozenset[str]]
) -> dict[str, int]:
    """Count the union of member gene sets per node (spec §7.3 shared post-processing).

    Args:
        ontology: The built ontology.
        genes: Pathway key to its gene identifiers.

    Returns:
        Node id to the size of its gene union.
    """
    return {
        node.id: len(
            set().union(*(genes.get(key, frozenset()) for key in node.keys))
            if node.keys
            else set()
        )
        for node in ontology.nodes
    }


def rows_for(
    ontology: Ontology, genes: dict[str, frozenset[str]]
) -> dict[str, list[tuple[str, ...]]]:
    """Render an ontology as the four tables.

    Args:
        ontology: The built ontology.
        genes: Pathway key to its gene identifiers, for the union counts.

    Returns:
        Table stem to its rows, each already stringified.
    """
    unions = gene_counts(ontology, genes)
    nodes = [
        (
            node.id,
            f"{node.support:.4f}",
            str(len(node.members)),
            str(unions[node.id]),
            # Naming has not run. `label` is null in the contract and empty here; `provisional`
            # says so explicitly rather than leaving a reader to infer it from the blank.
            "",
            "true",
        )
        for node in ontology.nodes
    ]
    members = [
        (key, node.id, f"{inclusion:.4f}", "")
        for node in ontology.nodes
        for key, inclusion in node.members
    ]
    edges = [(child, parent) for child, parent in ontology.edges]
    unplaced = [(key,) for key in ontology.unplaced]
    return {"nodes": nodes, "members": members, "edges": edges, "unplaced": unplaced}


def write(
    ontology: Ontology,
    root: Path,
    version: str,
    genes: dict[str, frozenset[str]],
    manifest: dict[str, object],
    dry_run: bool = False,
) -> Path:
    """Write an ontology to its versioned directory, validated before the swap.

    Args:
        ontology: The built ontology.
        root: The ontology root, normally ``data/ontology``.
        version: Version string, e.g. ``0.2``.
        genes: Pathway key to its gene identifiers.
        manifest: Provenance to record alongside the build's own parameters.
        dry_run: Price and validate without writing anything. Nothing is created, including the
            ``.part`` directory.

    Returns:
        The directory that was written, or would have been.

    Raises:
        ValueError: If the rendered tables disagree with the ontology they came from.
    """
    target = root / f"v{version}" / ontology.method
    tables = rows_for(ontology, genes)
    _validate(ontology, tables)
    if dry_run:
        return target

    part = target.with_name(target.name + PART)
    if part.exists():
        shutil.rmtree(part)
    part.mkdir(parents=True)
    write_tsv(part / "nodes.tsv", NODE_COLUMNS, tables["nodes"])
    write_tsv(part / "members.tsv", MEMBER_COLUMNS, tables["members"])
    write_tsv(part / "edges.tsv", EDGE_COLUMNS, tables["edges"])
    write_tsv(part / "unplaced.tsv", UNPLACED_COLUMNS, tables["unplaced"])
    (part / "manifest.json").write_text(
        json.dumps(
            {
                "method": ontology.method,
                "version": version,
                "params": _jsonable(ontology.params),
                "n_nodes": len(ontology.nodes),
                "n_roots": len(ontology.roots),
                "n_edges": len(ontology.edges),
                "n_unplaced": len(ontology.unplaced),
                **manifest,
            },
            indent=1,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    old = target.with_name(target.name + OLD)
    if old.exists():
        shutil.rmtree(old)
    if target.exists():
        target.rename(old)
    part.rename(target)
    if old.exists():
        shutil.rmtree(old)
    return target


def _validate(ontology: Ontology, tables: dict[str, list[tuple[str, ...]]]) -> None:
    """Check the rendered tables against the ontology before anything is swapped in.

    Raises:
        ValueError: On any disagreement. Catching it here means the previous build is still in
            place; catching it later means it is not.
    """
    if len(tables["nodes"]) != len(ontology.nodes):
        raise ValueError("nodes.tsv row count disagrees with the ontology")
    if len(tables["members"]) != sum(len(node.members) for node in ontology.nodes):
        raise ValueError("members.tsv row count disagrees with the ontology")
    if len(tables["edges"]) != len(ontology.edges):
        raise ValueError("edges.tsv row count disagrees with the ontology")
    if len(tables["unplaced"]) != len(ontology.unplaced):
        raise ValueError("unplaced.tsv row count disagrees with the ontology")
    ids = {row[0] for row in tables["nodes"]}
    for child, parent in tables["edges"]:
        if child not in ids or parent not in ids:
            raise ValueError(f"edges.tsv names a node not in nodes.tsv: {child} -> {parent}")


def _jsonable(params: dict[str, object]) -> dict[str, object]:
    """Render build parameters for the manifest, dropping anything that will not serialise."""
    out: dict[str, object] = {}
    for key, value in params.items():
        if isinstance(value, (str, int, float, bool, type(None))):
            out[key] = value
        elif isinstance(value, (list, tuple)):
            out[key] = [v for v in value if isinstance(v, (str, int, float, bool))]
        elif isinstance(value, dict):
            out[key] = {k: v for k, v in value.items() if isinstance(v, (str, int, float, bool))}
        else:
            out[key] = str(value)
    return out


def read_members(directory: Path) -> dict[str, dict[str, float]]:
    """Read a written ontology's membership back, for comparison.

    Args:
        directory: A versioned method directory.

    Returns:
        Node id to ``{pathway key: inclusion}``.
    """
    out: dict[str, dict[str, float]] = {}
    with (directory / "members.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            out.setdefault(row["node"], {})[row["key"]] = float(row["inclusion"])
    return out


def expected_columns() -> dict[str, Sequence[str]]:
    """The four tables' columns, for tests that pin the contract."""
    return {
        "nodes": NODE_COLUMNS,
        "members": MEMBER_COLUMNS,
        "edges": EDGE_COLUMNS,
        "unplaced": UNPLACED_COLUMNS,
    }
