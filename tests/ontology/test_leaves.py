"""Universe L's rules, on hand-built hierarchies where the answer is checkable by eye.

The one that matters is :func:`test_internal_is_about_the_universe_not_the_source`: a pathway counts
as a summary only if something *in the universe* sits below it. A term with children that were all
excluded by the gene rule is a leaf as far as the build is concerned, and treating it as a summary
would remove a pathway nothing else covers.
"""

from __future__ import annotations

from thema.ontology.leaves import (
    FLAT_SOURCES,
    ancestors,
    internal,
    leaf_universe,
    targets,
)

#: child -> parents. c and d sit under b, b under a; e is unrelated.
EDGES: dict[str, set[str]] = {
    "c": {"b"}, "d": {"b"}, "b": {"a"}, "f": {"a"},
}


def test_ancestors_climbs_transitively() -> None:
    """A child reaches its grandparents, not only its parents."""
    assert ancestors(EDGES, "c") == {"b", "a"}
    assert ancestors(EDGES, "b") == {"a"}
    assert ancestors(EDGES, "a") == set()
    assert ancestors(EDGES, "unknown") == set()


def test_ancestors_survives_a_cycle() -> None:
    """A cycle terminates rather than recursing forever."""
    loop = {"x": {"y"}, "y": {"x"}}
    assert ancestors(loop, "x") == {"x", "y"}


def test_internal_is_about_the_universe_not_the_source() -> None:
    """A parent whose only children are outside the universe is a leaf here."""
    assert internal(EDGES, ["a", "b", "c", "d", "f"]) == {"a", "b"}
    # Drop c and d: b now has nothing below it in the universe, so b is a leaf.
    assert internal(EDGES, ["a", "b", "f"]) == {"a"}
    # Drop b too: a still has f below it.
    assert internal(EDGES, ["a", "f"]) == {"a"}
    # a alone is a leaf.
    assert internal(EDGES, ["a"]) == set()


def test_leaf_universe_keeps_flat_sources_whatever_the_edges_say() -> None:
    """Hallmark and BTM have no hierarchy, so they are never removed as summaries."""
    sources = {"a": "reactome", "b": "reactome", "c": "reactome", "d": "go", "f": "go"}
    kept, counts = leaf_universe(["a", "b", "c", "d", "f"], EDGES, sources)
    assert kept == ["c", "d", "f"]
    assert counts["n_internal"] == 2
    assert counts["n_leaves"] == 3

    # The same hierarchy, but a and b are declared flat: both survive.
    flat = dict(sources, a="hallmark", b="btm")
    kept_flat, _counts = leaf_universe(["a", "b", "c", "d", "f"], EDGES, flat)
    assert kept_flat == ["a", "b", "c", "d", "f"]
    assert {"hallmark", "btm"} == set(FLAT_SOURCES)


def test_leaf_universe_counts_per_source() -> None:
    """The per-source counts the spec asks to be reported add up."""
    sources = {"a": "reactome", "b": "reactome", "c": "reactome", "d": "go", "f": "go"}
    _kept, counts = leaf_universe(["a", "b", "c", "d", "f"], EDGES, sources)
    assert counts["reactome_universe"] == 3
    assert counts["reactome_internal"] == 2
    assert counts["reactome_leaves"] == 1
    assert counts["go_universe"] == 2
    assert counts.get("go_internal", 0) == 0
    assert counts["go_leaves"] == 2


def test_targets_are_leaf_descendants_and_respect_min_size() -> None:
    """A summary's target is its leaves in L, and small targets are dropped."""
    leaves = ["c", "d", "f"]
    got = targets(EDGES, ["a", "b"], leaves, min_size=3)
    # a has all three leaves below it; b has only c and d, so b is dropped at min_size 3.
    assert got == {"a": frozenset({"c", "d", "f"})}
    both = targets(EDGES, ["a", "b"], leaves, min_size=2)
    assert both["b"] == frozenset({"c", "d"})
    assert both["a"] == frozenset({"c", "d", "f"})


def test_targets_ignore_summaries_with_no_leaves() -> None:
    """A summary whose descendants are all themselves summaries gets no target."""
    assert targets(EDGES, ["a", "b"], [], min_size=1) == {}
