"""The demo export: the tree it assembles, and what it refuses to invent."""

import numpy as np
import pytest

import export_demo
from thema.demo import NOT_COMPUTED, NOT_COMPUTED_CELL

LEVELS = (2, 4)


def rows_of(*specs: tuple[str, str, str, str, str]) -> list[dict[str, str]]:
    """Build a cluster table from ``(key, source, name, k2, k4)`` tuples."""
    return [
        {"key": key, "source": source, "name": name, "k2": coarse, "k4": fine, "provenance": ""}
        for key, source, name, coarse, fine in specs
    ]


def vectors_for(count: int) -> np.ndarray:
    """Unit vectors, distinct enough that the medoid is well defined."""
    raw = np.eye(count, 8)[:, :8] + 0.01
    return raw / np.linalg.norm(raw, axis=1, keepdims=True)


SAMPLE = rows_of(
    ("go:1", "go", "interferon alpha response", "1", "1"),
    ("go:2", "go", "interferon beta response", "1", "1"),
    ("reactome:3", "reactome", "neutrophil degranulation", "1", "2"),
    ("btm:4", "btm", "cell cycle checkpoint", "2", "3"),
    ("btm:5", "btm", "cell cycle arrest", "2", "3"),
)


def built(rows: list[dict[str, str]] | None = None) -> dict[str, object]:
    """Run the export over a small synthetic ontology."""
    rows = rows or SAMPLE
    genes = {row["key"]: frozenset({row["key"] + "-g", "shared"}) for row in rows}
    descriptions = {row["key"]: f"description of {row['name']}" for row in rows}
    return export_demo.build(
        rows, genes, descriptions, vectors_for(len(rows)), LEVELS, "stamp", 99
    )


def test_tree_is_depth_first_and_every_pathway_appears_at_every_level() -> None:
    tree = built()["tree"]
    assert isinstance(tree, list)
    assert [n["depth"] for n in tree] == [0, 1, 1, 0, 1]
    assert sum(1 for n in tree if n["depth"] == 0) == 2


def test_depth_zero_is_not_offered_as_a_theme() -> None:
    export = built()
    tree, themes = export["tree"], export["themes"]
    assert isinstance(tree, list) and isinstance(themes, dict)
    assert all(n["id"] is None for n in tree if n["depth"] == 0)
    assert all(n["node"] not in themes for n in tree if n["depth"] == 0)
    assert all(n["id"] in themes for n in tree if n["depth"] > 0)


def test_nothing_statistical_is_invented() -> None:
    """Every field enrichment would fill must say so, at every theme."""
    themes = built()["themes"]
    assert isinstance(themes, dict)
    for theme in themes.values():
        assert theme["dir"] == "na"
        assert [m["v"] for m in theme["metrics"] if m["k"] == "FDR"] == [NOT_COMPUTED]
        assert all(row[2] == NOT_COMPUTED for row in theme["tests"])
        for member in theme["members"]:
            assert member[2] == NOT_COMPUTED_CELL and member[3] == NOT_COMPUTED_CELL


def test_build_flags_say_what_has_not_been_computed() -> None:
    meta = built()["build"]
    assert isinstance(meta, dict)
    assert meta["computed"] == {
        "ontology": True,
        "descriptions": True,
        "enrichment": False,
        "soft_membership": False,
        "attribution": False,
        "theme_names": False,
    }


def test_theme_carries_real_counts_and_a_real_member_description() -> None:
    export = built()
    themes = export["themes"]
    assert isinstance(themes, dict)
    ifn = themes["k4:1"]
    assert [m["v"] for m in ifn["metrics"] if m["k"] == "pathways"] == ["2"]
    # Two members, one private gene each plus one they share.
    assert [m["v"] for m in ifn["metrics"] if m["k"] == "genes (union)"] == ["3"]
    assert ifn["exemplar"]["description"].startswith("description of interferon")


def test_two_nodes_holding_the_same_pathways_keep_the_same_label() -> None:
    """A cut that did not split its parent must not be given a different name."""
    export = built(
        rows_of(
            ("go:1", "go", "interferon alpha response", "1", "1"),
            ("go:2", "go", "interferon beta response", "1", "1"),
            ("btm:3", "btm", "cell cycle checkpoint", "2", "2"),
        )
    )
    tree = export["tree"]
    assert isinstance(tree, list)
    by_node = {n["node"]: n["label"] for n in tree}
    # k2:1 holds both interferon rows and so does its only child k4:1.
    assert by_node["k2:1"] == by_node["k4:1"]


def test_crossing_cuts_are_refused() -> None:
    crossed = rows_of(
        ("a", "go", "one", "1", "1"),
        ("b", "go", "two", "2", "1"),
    )
    with pytest.raises(ValueError, match="does not refine"):
        export_demo.check_nested(crossed, LEVELS)
