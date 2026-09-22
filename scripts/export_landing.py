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

**Labels are provisional.** Naming has not run. A node is labelled by the two or three most
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

from thema.demo import LABEL_SEPARATOR, distinctive_terms, document_frequency

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = REPO_ROOT / "data"
DEFAULT_OUT = REPO_ROOT / "demo"

PATHWAYS = "pathways.tsv"
DESCRIPTIONS = "pathway_descriptions.tsv"

#: The cuts the page shows: theme, sub-theme, sub-sub-theme, then pathways.
LEVELS = (10, 50, 200)

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


def build(data: Path, version: str, method: str) -> dict[str, object]:
    """Assemble the payload the landing page renders.

    Args:
        data: The data directory.
        version: Ontology version.
        method: Builder method.

    Returns:
        ``manifest``, ``cards`` and ``data`` -- the last being the tree the page walks.
    """
    versioned = data / "ontology" / f"v{version}"
    export_dir = versioned / method
    manifest = json.loads((export_dir / "manifest.json").read_text(encoding="utf-8"))

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

    def gene_union(member_keys: list[str]) -> int:
        union: set[str] = set()
        for key in member_keys:
            union |= genes.get(key, frozenset())
        return len(union)

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

    at_level: dict[int, list[str]] = {
        level: [n for n in members if n.startswith(f"k{level}:")] for level in LEVELS
    }

    def node_obj(node_id: str, depth: int) -> dict[str, object]:
        member_keys = members[node_id]
        out: dict[str, object] = {
            "id": node_id,
            "label": labels[node_id],
            "provisional": True,
            "n": len(member_keys),
            "g": gene_union(member_keys),
        }
        if depth + 1 < len(LEVELS):
            holder = set(member_keys)
            kids = order([n for n in at_level[LEVELS[depth + 1]] if set(members[n]) <= holder])
            out["children"] = [node_obj(k, depth + 1) for k in kids]
        else:
            out["pathways"] = [
                pathway_obj(k) for k in sorted(member_keys, key=lambda k: names[k].lower())
            ]
        return out

    tree = [node_obj(root, 0) for root in order(at_level[LEVELS[0]])]

    by_name: dict[tuple[str, str], str] = {}
    for key, row in pathways.items():
        by_name.setdefault((row["source"], row["name"].lower()), key)
    universe = len(set().union(*genes.values())) if genes else 1
    check_cards(by_name, genes, universe)

    exported_levels = {f"k{level}" for level in LEVELS}
    cards: dict[str, object] = {}
    for card, spec in CARDS.items():
        listed = spec["pathways"]
        assert isinstance(listed, tuple)
        wanted = {by_name[(s, n.lower())] for s, n in listed}
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
            "method": manifest["method"],
            "version": manifest["version"],
            "levels": list(LEVELS),
            "n_pathways": manifest["n_pathways"],
            "collection_rows": manifest["collection_rows"],
            "n_sources": len(sources),
            "sources": sources,
            "prompt_version": manifest["prompt_version"],
            "descriptions_sha256": manifest["descriptions_sha256"],
            "embedder": manifest["embedder"],
            "named": False,
        },
        "cards": cards,
        "data": {"id": "root", "n": manifest["n_pathways"], "children": tree},
    }


def main(argv: list[str] | None = None) -> int:
    """Write ``demo/ontology.js`` for the landing page."""
    parser = argparse.ArgumentParser(prog="export_landing.py", description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--version", default="0.2", help="ontology version (default: %(default)s)")
    parser.add_argument("--method", default="ward_tree")
    args = parser.parse_args(argv)

    export_dir = args.data / "ontology" / f"v{args.version}" / args.method
    if not (export_dir / "manifest.json").is_file():
        print(f"missing input: {export_dir / 'manifest.json'}", file=sys.stderr)
        print("run scripts/build_ontology.py first", file=sys.stderr)
        return 1

    try:
        payload = build(args.data, args.version, args.method)
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

    print(f"\nEXPORTED  v{meta['version']}/{meta['method']}  prompt={meta['prompt_version']}\n")
    print(f"  pathways   {meta['n_pathways']:,} of {meta['collection_rows']:,}")
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
