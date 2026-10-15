"""Export a built ontology into the object ``demo/landing.html`` renders.

The landing page is the design mockup, and its ``DATA`` constant is the contract: the export is
built to match it rather than the page being rewritten around a new shape (spec Part C).

Reads the **versioned** export (``data/ontology/v<version>/<method>/``) rather than the flat
``clusters_*.tsv``, so the page can state which ontology and which description generation it shows,
from the manifest rather than from anything typed.

Decisions implemented here, each recorded in an addendum:

- **A1** — written as ``demo/ontology.js`` assigning a global, never fetched. ``fetch`` is blocked
  on ``file://`` and the page must open by double-clicking it.
- **A3** — no synthetic root. The coarsest cut's clusters are the roots, a forest. The wrapper
  object exists only so the detail card has an empty state to describe; it is a view, not a node.
- **A5/A6** — the build line renders from the manifest.
- **B8** — an example card shows the smallest node containing all the pathways it lists.

**Names, when there are any.** ``--names`` takes a TSV of ``theme_id, name, method, unnameable,
duplicate_group`` -- the shape ``naming-c1`` writes. A theme shows its real name only when the namer
produced one AND it is unique. Three kinds of theme keep the keyword label and the amber chip: one
the namer **declined**, one whose name still **collides** with another theme's, and one the naming
run never covered (over 200 members, outside naming-c1's scope). Three different reasons, one honest
signal. The file and its sha256 go in the manifest, so the page can say which names it shows.

**Labels are provisional.** Without names, a node is labelled by the two or three most
distinctive terms in its members' names -- frequency within the node against frequency across the
collection -- joined by a separator no curator would write, and carries ``provisional: true`` so the
page shows the amber chip. Short keyword labels were chosen over central member names: three full
pathway names is more text than a tree row can hold, and truncating them mid-word reads worse than
a term list that is obviously machine-made.

**Card figures are recomputed and asserted.** They come from the gene lists, not the clustering, so
a description change should not move them. If one no longer holds the export fails rather than
shipping a page that states it.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

from thema.data.tables import sha256_file
from thema.demo import (
    LABEL_SEPARATOR,
    distinctive_terms,
    document_frequency,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = REPO_ROOT / "data"
DEFAULT_OUT = REPO_ROOT / "demo"

PATHWAYS = "pathways.tsv"
DESCRIPTIONS = "pathway_descriptions.tsv"

#: The cuts the page shows: theme, sub-theme, sub-sub-theme, then pathways.
LEVELS = (10, 50, 200)

#: How deep the rendered tree goes for a DAG build. The consensus DAG is 17 levels; a page that
#: unfolds all of them is unreadable and, at 5.7 MB of embedded members, slow on a phone.
MAX_TREE_DEPTH = 5

#: The global the page reads.
GLOBAL = "THEMA_LANDING"

#: How many terms a provisional label holds before collision widening.
LABEL_TERMS = 3

#: A term must appear in at least this share of a node's members.
LABEL_FLOOR = 0.03

#: ...and in no more than this share of the whole collection. Without the ceiling every broad node
#: is labelled "signaling · regulation": those words are common enough to dominate a large node's
#: vocabulary and not rare enough for inverse document frequency to demote them.
LABEL_CEILING = 0.05

#: The example cards. SOURCE is part of the key because the insulin card lists two pathways whose
#: names differ only in case -- GO's "regulation of insulin secretion" and Reactome's "Regulation
#: of insulin secretion". Matching on the lowercased name alone collapses them and the card
#: silently loses a member.
CARDS: dict[str, dict[str, object]] = {
    "nfkb": {
        "pathways": (
            ("go", "positive regulation of JNK cascade"),
            ("reactome", "TNFR1-mediated ceramide production"),
            ("reactome", "NIK-->noncanonical NF-kB signaling"),
            ("hallmark", "HALLMARK_TNFA_SIGNALING_VIA_NFKB"),
        ),
        "assert_genes": {
            "positive regulation of JNK cascade": 104,
            "TNFR1-mediated ceramide production": 6,
            "NIK-->noncanonical NF-kB signaling": 46,
            "HALLMARK_TNFA_SIGNALING_VIA_NFKB": 200,
        },
        "assert_max_kappa": 0.04,
        "assert_disjoint_pairs": 2,
    },
    "insulin": {
        "pathways": (
            ("go", "insulin secretion"),
            ("go", "regulation of insulin secretion"),
            ("reactome", "Regulation of insulin secretion"),
        ),
        "assert_genes": {
            "insulin secretion": 204,
            "regulation of insulin secretion": 167,
            "Regulation of insulin secretion": 78,
        },
        "assert_nested": ("regulation of insulin secretion", "insulin secretion"),
        "assert_overlap": ("Regulation of insulin secretion", "insulin secretion", 21, 57),
    },
}


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read a TSV into dicts, tolerating very large cells.

    Args:
        path: The table.

    Returns:
        One dict per row.
    """
    csv.field_size_limit(1 << 30)
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def symbols(cell: str) -> list[str]:
    """Pull plain gene symbols out of a ``HGNC:123=SYM,SYM2;...`` cell.

    The identifiers are half the payload and the page never shows them.

    Args:
        cell: The ``gene_symbols`` cell.

    Returns:
        The symbols in cell order, deduplicated.
    """
    out: list[str] = []
    seen: set[str] = set()
    for binding in cell.split(";"):
        if not binding or binding == "-":
            continue
        ident, _, names = binding.partition("=")
        for name in (names or ident).split(","):
            name = name.strip()
            if name and name not in seen:
                seen.add(name)
                out.append(name)
    return out


def kappa(a: frozenset[str], b: frozenset[str], universe: int) -> float:
    """Cohen's kappa between two gene sets over a shared universe.

    Args:
        a: One gene set.
        b: The other.
        universe: How many genes the collection annotates in total.

    Returns:
        Agreement beyond chance.
    """
    pa, pb = len(a) / universe, len(b) / universe
    observed = (len(a & b) + (universe - len(a | b))) / universe
    expected = pa * pb + (1 - pa) * (1 - pb)
    return (observed - expected) / (1 - expected) if expected < 1 else 1.0


def label_nodes(
    members: dict[str, list[str]], names: dict[str, str]
) -> dict[str, str]:
    """Label every node by the most distinctive terms in its members' names.

    Reuses :mod:`thema.demo`'s labeller, which scores a term by how much of the node carries it
    against how common it is across the whole collection -- so "regulation", which nearly every
    node has, loses to "interferon", which one node has.

    Two nodes sharing a label is worse than a longer label: a reader cannot tell which row they are
    looking at. Collisions are widened twice over -- more terms, and a lower bar for how much of the
    node a term must cover -- because a node whose members share only one common word needs the
    rarer vocabulary to tell it from its twin, and that vocabulary sits below the default floor by
    definition. Nodes holding the SAME pathways are not a collision: a cut that did not split its
    parent produces one, and giving them different labels would assert a difference that is not
    there.

    Args:
        members: Node id to its member pathway keys.
        names: Pathway key to its name.

    Returns:
        Node id to its provisional label.
    """
    background = document_frequency(names.values())
    total = len(names)
    labels = {
        node: LABEL_SEPARATOR.join(
            distinctive_terms(
                [names[key] for key in keys if key in names],
                background,
                total,
                limit=LABEL_TERMS,
                floor=LABEL_FLOOR,
                ceiling=LABEL_CEILING,
            )
        )
        or "unlabelled"
        for node, keys in members.items()
    }
    sets = {node: frozenset(keys) for node, keys in members.items()}
    for limit, floor in ((4, 0.03), (5, 0.02), (6, 0.01), (8, 0.005)):
        taken: dict[str, list[str]] = {}
        for node, label in labels.items():
            taken.setdefault(label, []).append(node)
        clashing = [
            node for group in taken.values() if len({sets[n] for n in group}) > 1 for node in group
        ]
        if not clashing:
            break
        for node in clashing:
            terms = distinctive_terms(
                [names[key] for key in members[node] if key in names],
                background,
                total,
                limit=limit,
                floor=floor,
                ceiling=LABEL_CEILING,
            )
            if terms:
                labels[node] = LABEL_SEPARATOR.join(terms)
    return labels


def read_names_tsv(path: Path) -> tuple[dict[str, str], set[str], set[str], dict[str, int]]:
    """Read a naming-c1 names table into the three categories the page distinguishes.

    Only a theme with a name that is **both** accepted and unique counts as named. The other two
    categories are kept apart rather than merged into "no name", because they are different
    findings: a declined theme says the hierarchy put something unnameable together, while a
    collision says the naming run has not finished.

    Args:
        path: The TSV, with ``theme_id, name, method, unnameable, duplicate_group``.

    Returns:
        ``(named, declined, colliding, methods)`` where ``methods`` counts the ``method`` column.
    """
    named: dict[str, str] = {}
    declined: set[str] = set()
    colliding: set[str] = set()
    methods: dict[str, int] = {}
    for row in read_rows(path):
        node = row["theme_id"]
        methods[row.get("method", "")] = methods.get(row.get("method", ""), 0) + 1
        if row.get("unnameable", "").strip().lower() in ("1", "true", "yes"):
            declined.add(node)
        elif row.get("duplicate_group", "").strip():
            colliding.add(node)
        else:
            named[node] = row["name"]
    return named, declined, colliding, methods


def pairs(items: list[str]) -> list[tuple[str, str]]:
    """Every unordered pair.

    Args:
        items: The items.

    Returns:
        Each pair once.
    """
    return [(items[i], items[j]) for i in range(len(items)) for j in range(i + 1, len(items))]


def check_cards(
    by_name: dict[tuple[str, str], str],
    genes: dict[str, frozenset[str]],
    universe: int,
) -> None:
    """Refuse to export if a verified card figure no longer holds.

    Args:
        by_name: ``(source, lowercased name)`` to pathway key.
        genes: Pathway key to its gene identifiers.
        universe: Distinct genes across the collection.

    Raises:
        ValueError: On the first figure that no longer holds.
    """
    for card, spec in CARDS.items():
        listed = spec["pathways"]
        assert isinstance(listed, tuple)
        keys: dict[str, str] = {}
        for source, name in listed:
            key = by_name.get((source, name.lower()))
            if key is None:
                raise ValueError(f"card {card}: {source}:{name!r} is not in the collection")
            keys[name] = key

        expected_genes = spec.get("assert_genes", {})
        assert isinstance(expected_genes, dict)
        for name, expected in expected_genes.items():
            actual = len(genes[keys[name]])
            if actual != expected:
                raise ValueError(
                    f"card {card}: {name!r} has {actual} genes, the page says {expected}"
                )

        if "assert_max_kappa" in spec:
            worst = max(kappa(genes[a], genes[b], universe) for a, b in pairs(list(keys.values())))
            if worst >= float(spec["assert_max_kappa"]):  # type: ignore[arg-type]
                raise ValueError(
                    f"card {card}: highest pairwise kappa is {worst:.4f}, the page says below "
                    f"{spec['assert_max_kappa']}"
                )
        if "assert_disjoint_pairs" in spec:
            disjoint = sum(1 for a, b in pairs(list(keys.values())) if not genes[a] & genes[b])
            if disjoint != int(spec["assert_disjoint_pairs"]):  # type: ignore[arg-type]
                raise ValueError(
                    f"card {card}: {disjoint} pairs share no gene, the page says "
                    f"{spec['assert_disjoint_pairs']}"
                )
        if "assert_nested" in spec:
            inner, outer = spec["assert_nested"]  # type: ignore[misc]
            if not genes[keys[inner]] <= genes[keys[outer]]:
                raise ValueError(f"card {card}: {inner!r} is no longer wholly inside {outer!r}")
        if "assert_overlap" in spec:
            one, other, shared, fresh = spec["assert_overlap"]  # type: ignore[misc]
            a, b = genes[keys[one]], genes[keys[other]]
            if len(a & b) != shared or len(a - b) != fresh:
                raise ValueError(
                    f"card {card}: {one!r} shares {len(a & b)} and brings {len(a - b)}, the page "
                    f"says {shared} and {fresh}"
                )


def build(
    data: Path,
    version: str,
    method: str,
    build_dir: Path | None = None,
    names_file: Path | None = None,
    overrides_file: Path | None = None,
    payload: str = "deduped",
) -> dict[str, object]:
    """Assemble the payload the landing page renders.

    Args:
        data: The data directory.
        version: Ontology version.
        method: Builder method.
        build_dir: Read the build from this directory instead of ``v<version>/<method>``. Used for a
            frozen build, which does not sit in the versioned layout. None keeps the default.
        names_file: A naming-c1 names TSV. None keeps the old behaviour, which looks for
            ``data/theme_names.tsv``.
        overrides_file: A TSV of hand-edited names applied on top of ``names_file``. Each override
            is marked in the manifest and on the node, because a human-edited name is a different
            claim from a generated one.
        payload: ``"deduped"`` emits each pathway object once into a top-level ``pathways`` map and
            references it by id from the nodes; ``"inline"`` is the original shape, every object
            repeated under every theme that holds it. Deduped is 8x smaller on a DAG build, where a
            multi-parent theme is emitted under each parent; inline is kept so the published page
            can still be regenerated byte-for-byte in the shape it was built from.

    Returns:
        ``manifest``, ``cards`` and ``data`` -- the last being the tree the page walks.
    """
    export_dir = build_dir if build_dir is not None else data / "ontology" / f"v{version}" / method
    manifest = json.loads((export_dir / "manifest.json").read_text(encoding="utf-8"))
    # A build's own manifest does not always carry the collection-level figures; a frozen leaves
    # build records its pathway count as "n" and leaves the universe size to universe.json beside
    # it. Those are read as END-OF-CHAIN fallbacks only, so a manifest that already states a figure
    # keeps it and the existing exports are unchanged.
    universe_meta: dict[str, object] = {}
    for candidate in (export_dir / "universe.json", data / "ontology" / f"v{version}"
                      / "universe.json"):
        if candidate.is_file():
            universe_meta = json.loads(candidate.read_text(encoding="utf-8"))
            break

    members: dict[str, list[str]] = {}
    for row in read_rows(export_dir / "members.tsv"):
        members.setdefault(row["node"], []).append(row["key"])

    pathways = {f"{r['source']}:{r['source_id']}": r for r in read_rows(data / PATHWAYS)}
    names = {key: row["name"] for key, row in pathways.items()}
    genes = {
        key: frozenset(row["genes"].split(";")) if row["genes"] not in ("", "-") else frozenset()
        for key, row in pathways.items()
    }
    text = {
        row["key"]: row["description_generated"]
        for row in read_rows(data / DESCRIPTIONS)
        if row.get("status") == "current"
    }

    labels = label_nodes(members, names)
    # Naming HAS run for recurrent_dag_consensus. A theme with a name uses it and drops the amber
    # chip; a theme the namer DECLINED keeps the chip and says so, because an unnameable theme is a
    # finding about the hierarchy and a keyword label would bury it.
    generated: dict[str, str] = {}
    declined: set[str] = set()
    colliding: set[str] = set()
    naming_methods: dict[str, int] = {}
    edited: dict[str, str] = {}
    if names_file is not None:
        generated, declined, colliding, naming_methods = read_names_tsv(names_file)
        if overrides_file is not None:
            for row in read_rows(overrides_file):
                node = row["theme_id"]
                edited[node] = row["name"]
                generated[node] = row["name"]
                declined.discard(node)
                colliding.discard(node)
    else:
        names_table = data / "theme_names.tsv"
        if names_table.is_file():
            for row in read_rows(names_table):
                if row.get("status") != "current":
                    continue
                if row["nameable"] == "true":
                    generated[row["example_node"]] = row["name"]
                else:
                    declined.add(row["example_node"])

    def gene_union(member_keys: list[str]) -> int:
        union: set[str] = set()
        for key in member_keys:
            union |= genes.get(key, frozenset())
        return len(union)

    pool: dict[str, dict[str, object]] = {}

    def listed(keys: list[str]) -> list[object]:
        """A node's pathway list, in the shape ``payload`` asks for.

        Deduped stores the object once in ``pool`` and leaves an id behind; inline repeats the whole
        object. Either way the ORDER is the same, so the two shapes render identically.
        """
        if payload == "inline":
            return [pathway_obj(key) for key in keys]
        for key in keys:
            if key not in pool:
                pool[key] = pathway_obj(key)
        return list(keys)

    def sort_key(key: str) -> tuple[str, str]:
        """Order pathways by name, then by key.

        The key is the tie-break, and it is not cosmetic. Sorting on the lowercased name alone
        leaves "Gap junction assembly" and "gap junction assembly" tied, and the losers of a tie
        keep whatever order the surrounding ``set`` happened to iterate in -- which Python
        randomises per process, so two runs of this exporter produced different bytes. Adding the
        key makes the order total.
        """
        return (names[key].lower(), key)

    def pathway_obj(key: str) -> dict[str, object]:
        row = pathways[key]
        return {
            "id": key,
            "name": row["name"],
            "source": row["source"],
            "sid": row["source_id"],
            "n": int(row["n_genes"]),
            "genes": symbols(row.get("gene_symbols", "")),
            "curated": (row.get("description_source") or "").strip().lstrip("-") or "",
            "thema": text.get(key, ""),
            "also": [],
        }

    def order(node_ids: list[str]) -> list[str]:
        return sorted(node_ids, key=lambda i: (-len(members[i]), labels[i]))

    # ward_tree is a set of cuts; recurrent_dag carries its own parent edges. A node with several
    # parents is emitted under EACH of them (spec section 19), so this renders the DAG rather than
    # partitioning it. Depth is bounded because the DAG runs 17 deep and a page cannot hold that.
    # A cut-based export (ward_tree) has no parents column at all; reading it as though it did
    # raised KeyError and made the documented default invocation fail outright. Absence means
    # "levelled", so the column is skipped rather than defaulted -- defaulting it to an empty
    # string would populate parents_of and make the DAG test below read the build as a DAG.
    parents_of: dict[str, list[str]] = {}
    for row in read_rows(export_dir / "nodes.tsv"):
        if "parents" not in row:
            continue
        parents_of[row["node"]] = [p for p in row["parents"].replace(",", " ").split() if p]
    children_of: dict[str, list[str]] = {node: [] for node in parents_of}
    for node, above in parents_of.items():
        for parent in above:
            children_of.setdefault(parent, []).append(node)
    levelled = not parents_of

    def node_obj(node_id: str, depth: int) -> dict[str, object]:
        member_keys = members[node_id]
        out: dict[str, object] = {
            "id": node_id,
            "label": generated.get(node_id) or labels[node_id],
            "provisional": node_id not in generated,
            "declined": node_id in declined,
            "edited": node_id in edited,
            "n": len(member_keys),
            "g": gene_union(member_keys),
        }
        if levelled:
            if depth + 1 < len(LEVELS):
                holder = set(member_keys)
                kids = order(
                    [n for n in at_level[LEVELS[depth + 1]] if set(members[n]) <= holder]
                )
                out["children"] = [node_obj(k, depth + 1) for k in kids]
                return out
            out["pathways"] = listed(sorted(member_keys, key=sort_key))
            return out
        kids = order(children_of.get(node_id, []))
        if kids and depth < MAX_TREE_DEPTH:
            out["children"] = [node_obj(k, depth + 1) for k in kids]
            covered = {key for kid in kids for key in members[kid]}
            direct = sorted(set(member_keys) - covered, key=sort_key)
            if direct:
                out["pathways"] = listed(direct)
        else:
            out["pathways"] = listed(sorted(member_keys, key=sort_key))
        return out

    at_level: dict[int, list[str]] = (
        {level: [n for n in members if n.startswith(f"k{level}:")] for level in LEVELS}
        if levelled else {}
    )
    roots = (
        order(at_level[LEVELS[0]]) if levelled
        else order([n for n in parents_of if not parents_of[n]])
    )
    tree = [node_obj(root, 0) for root in roots]

    by_name: dict[tuple[str, str], str] = {}
    for key, row in pathways.items():
        by_name.setdefault((row["source"], row["name"].lower()), key)
    universe = len(set().union(*genes.values())) if genes else 1
    check_cards(by_name, genes, universe)

    exported_levels = {f"k{level}" for level in LEVELS}
    cards: dict[str, object] = {}
    for card, spec in CARDS.items():
        card_pathways = spec["pathways"]
        assert isinstance(card_pathways, tuple)
        wanted = {by_name[(s, n.lower())] for s, n in card_pathways}
        holding = [
            (len(member_keys), node)
            for node, member_keys in members.items()
            if node.split(":")[0] in exported_levels and wanted <= set(member_keys)
        ]
        size, node = min(holding) if holding else (None, None)
        cards[card] = {
            "pathways": sorted(wanted),
            "node": node,
            "node_size": size,
            "node_label": labels[node] if node else None,
        }

    placed = {key for member_keys in members.values() for key in member_keys}
    sources = sorted({pathways[key]["source"] for key in placed})
    return {
        "manifest": {
            "method": manifest.get("method", method),
            "version": manifest.get("version", version),
            "levels": list(LEVELS) if levelled else [],
            "n_pathways": manifest.get(
                "n_pathways",
                manifest.get("n_embedded", manifest.get("n", universe_meta.get("n_embedded"))),
            ),
            "collection_rows": manifest.get(
                "collection_rows", manifest.get("n_universe", universe_meta.get("n_universe"))
            ),
            "n_sources": len(sources),
            "sources": sources,
            # No default. The published build's manifest records no prompt version, and the
            # hardcoded "v4-repaired" meant the page stated one nothing had recorded. Empty is
            # the truth, and the page omits the line rather than printing a blank.
            "prompt_version": manifest.get("prompt_version", ""),
            "descriptions_sha256": manifest.get(
                "descriptions_sha256", manifest.get("descriptions_digest", "")
            ),
            "embedder": manifest.get("embedder", universe_meta.get("embedder")),
            "named": bool(generated),
            "n_named": len(generated),
            "n_declined": len(declined),
            "universe": manifest.get("n_universe", universe_meta.get("n_universe")),
            **(
                {}
                if names_file is None
                else {
                    "names_file": str(names_file).replace("\\", "/"),
                    "names_sha256": sha256_file(names_file),
                    "naming_methods": dict(sorted(naming_methods.items())),
                    "n_colliding": len(colliding),
                    "n_out_of_naming_scope": sum(
                        1
                        for node in members
                        if node not in generated
                        and node not in declined
                        and node not in colliding
                    ),
                    "n_themes": len(members),
                    "n_edited": len(edited),
                    "edited_names": dict(sorted(edited.items())),
                    "overrides_file": (None if overrides_file is None
                                       else str(overrides_file).replace("\\", "/")),
                    "overrides_sha256": (None if overrides_file is None
                                         else sha256_file(overrides_file)),
                }
            ),
            "payload": payload,
        },
        "cards": cards,
        **({} if payload == "inline" else {"pathways": pool}),
        "data": {
            "id": "root",
            "n": manifest.get(
                "n_pathways",
                manifest.get("n_embedded", manifest.get("n", universe_meta.get("n_embedded"))),
            ),
            "children": tree,
        },
    }


def main(argv: list[str] | None = None) -> int:
    """Write ``demo/ontology.js`` for the landing page."""
    parser = argparse.ArgumentParser(prog="export_landing.py", description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--version", default="0.2", help="ontology version (default: %(default)s)")
    # The default is what actually generates the published page. It used to be ward_tree, which
    # raised KeyError on its own nodes.tsv, so the documented default invocation did not work.
    parser.add_argument("--method", default="recurrent_dag_consensus",
                        help="builder directory under the version (default: %(default)s)")
    parser.add_argument("--payload", choices=["deduped", "inline"], default="deduped",
                        help="deduped emits each pathway once and references it by id; inline is "
                             "the original shape and regenerates the published page's own layout "
                             "(default: %(default)s)")
    parser.add_argument("--name-overrides", type=Path, default=None,
                        help="a TSV of hand-edited names applied on top of --names, marked as "
                             "edited in the manifest and on the page")
    parser.add_argument("--build", type=Path, default=None,
                        help="read the build from this directory instead of "
                             "data/ontology/v<version>/<method>. For a frozen build, which does "
                             "not sit in the versioned layout")
    parser.add_argument("--names", type=Path, default=None,
                        help="a naming-c1 names TSV (theme_id, name, method, unnameable, "
                             "duplicate_group). Without it the keyword labels are used, as before")
    args = parser.parse_args(argv)

    export_dir = (
        args.build if args.build is not None
        else args.data / "ontology" / f"v{args.version}" / args.method
    )
    if not (export_dir / "manifest.json").is_file():
        print(f"missing input: {export_dir / 'manifest.json'}", file=sys.stderr)
        print("run scripts/build_ontology.py first", file=sys.stderr)
        return 1
    if args.names is not None and not args.names.is_file():
        print(f"missing names file: {args.names}", file=sys.stderr)
        return 1

    try:
        payload = build(args.data, args.version, args.method, args.build, args.names,
                        args.name_overrides, args.payload)
    except ValueError as exc:
        print(f"refusing to export: {exc}", file=sys.stderr)
        return 1

    meta = payload["manifest"]
    assert isinstance(meta, dict)
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "ontology.js").write_text(
        f"/* Generated by scripts/export_landing.py. Do not edit. */\nwindow.{GLOBAL} = {text};\n",
        encoding="utf-8",
    )

    print(f"\nEXPORTED  v{meta['version']}/{meta['method']}"
          + (f"  prompt={meta['prompt_version']}" if meta["prompt_version"] else "")
          + "\n")
    if meta.get("n_pathways") is not None and meta.get("collection_rows") is not None:
        print(f"  pathways   {meta['n_pathways']:,} of {meta['collection_rows']:,}")
    print(f"  payload    {meta['payload']}"
          + (f"; {len(payload['pathways']):,} pathway objects emitted once"
             if meta["payload"] == "deduped" else "; objects repeated per theme"))
    if args.names is not None:
        print(f"  names      {meta['names_file']}  sha256 {meta['names_sha256'][:16]}")
        if meta.get("n_edited"):
            print(f"  overrides  {meta['overrides_file']}  sha256 "
                  f"{str(meta['overrides_sha256'])[:16]}")
            print(f"             {meta['n_edited']} hand-edited name(s): "
                  f"{', '.join(sorted(meta['edited_names']))}")
        print(f"             {meta['n_named']:,} named of {meta['n_themes']:,} themes; "
              f"provisional: {meta['n_declined']} declined, {meta['n_colliding']} colliding, "
              f"{meta['n_out_of_naming_scope']} out of scope")
        print(f"             methods {meta['naming_methods']}")
    print(f"  sources    {meta['n_sources']}   levels {' -> '.join(f'k={k}' for k in LEVELS)}")
    cards = payload["cards"]
    assert isinstance(cards, dict)
    for name, card in cards.items():
        print(f"  card {name:8s} {card['node']} ({card['node_size']} pathways)")
        print(f"       label: {card['node_label']}")
    print(f"\n  -> {args.out / 'ontology.js'}  ({len(text) / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
