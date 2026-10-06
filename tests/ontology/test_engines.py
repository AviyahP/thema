"""The engines declared on 6 Oct 2026, on fixtures where the right answer is known.

These are not quality tests -- which engine clusters biology better is what the engine search
measures on the real 10,770. They test the three things a wrong engine would get wrong silently:
the graph is the one declared, the candidates are returned as row indices into the sample, and the
whole thing is deterministic, because a side re-cut later must be the same side.
"""

from __future__ import annotations

import numpy as np
import pytest

from thema.ontology import engines


def _blobs(groups: int = 5, per: int = 20, dim: int = 10, seed: int = 0) -> np.ndarray:
    """Unit-length points in well-separated blobs.

    Args:
        groups: Number of blobs.
        per: Points per blob.
        dim: Dimensionality.
        seed: RNG seed.

    Returns:
        A ``(groups * per, dim)`` unit-vector matrix.
    """
    rng = np.random.default_rng(seed)
    centres = np.eye(groups, dim)
    x = np.repeat(centres, per, axis=0) + 0.04 * rng.standard_normal((groups * per, dim))
    return x / np.linalg.norm(x, axis=1, keepdims=True)


def test_knn_graph_is_the_union_and_each_edge_appears_once() -> None:
    """Undirected, deduplicated, i < j, non-negative weights."""
    x = _blobs()
    edges, weight = engines.knn_graph(x, k=5)

    assert edges.shape[1] == 2
    assert (edges[:, 0] < edges[:, 1]).all(), "edges must be stored once, low index first"
    assert len({tuple(e) for e in edges.tolist()}) == len(edges), "no duplicate edge"
    assert (weight >= 0).all(), "a modularity objective is not defined for negative weights"
    # The union of k directed edges per node has between k*m/2 and k*m undirected edges.
    m = x.shape[0]
    assert 5 * m // 2 <= len(edges) <= 5 * m


def test_knn_graph_weight_is_the_cosine_of_the_pair() -> None:
    """The weight is the actual similarity, not a rank or a constant."""
    x = _blobs(groups=3, per=8)
    edges, weight = engines.knn_graph(x, k=4)
    expect = np.einsum("ij,ij->i", x[edges[:, 0]], x[edges[:, 1]])
    assert np.allclose(weight, np.clip(expect, 0.0, None))


def test_knn_graph_handles_fewer_points_than_k() -> None:
    """A tiny sample must not ask for more neighbours than exist."""
    x = _blobs(groups=1, per=4, dim=4)
    edges, _weight = engines.knn_graph(x, k=15)
    assert len(edges) == 6, "4 points fully connected is 6 undirected edges"


def test_resolution_ladder_is_the_amended_ten_rung_ascending_ladder() -> None:
    """10 log-spaced values over the declared range, the SAME ladder for every run."""
    ladder = engines.resolution_ladder()

    assert ladder.shape == (10,), "amendment 1 replaced 200-assigned-to-runs with 10-per-run"
    # 0.0669433, not 0.001: amendment 4 raised the bottom to the largest resolution at which the
    # largest community still reaches the 3,125 cap. Below it every rung gives one community of the
    # whole draw, which the cap removes, so those rungs proposed nothing.
    assert np.isclose(ladder.min(), 0.0669433)
    # 300, not 100: amendment 3's setup check measured a median community of 12 at resolution 100
    # against a required <= 5, and 300 is the smallest widening that passes.
    assert np.isclose(ladder.max(), 300.0)
    assert np.all(np.diff(ladder) > 0), "ascending, so 'adjacent rung' is well defined for B2"
    assert np.array_equal(ladder, engines.resolution_ladder()), "must be deterministic"


def test_leiden_pools_the_whole_ladder_and_is_deterministic() -> None:
    """Arm B proposes the union of all ten splits, deduplicated."""
    pytest.importorskip("leidenalg")
    x = _blobs(groups=5, per=20)
    ladder = engines.resolution_ladder()
    found = engines.leiden_communities(x, ladder, seed=7)

    assert all(isinstance(c, list) for c in found)
    assert len({tuple(c) for c in found}) == len(found), "deduplicated"
    # The blobs must be among the candidates somewhere on the ladder.
    blobs = {frozenset(range(g * 20, (g + 1) * 20)) for g in range(5)}
    assert blobs <= {frozenset(c) for c in found}
    assert engines.leiden_communities(x, ladder, 7) == found


def test_leiden_pooling_beats_any_single_rung() -> None:
    """The amendment's whole point: one rung sees less than the ladder does."""
    pytest.importorskip("leidenalg")
    x = _blobs(groups=5, per=20)
    ladder = engines.resolution_ladder()
    pooled = {tuple(c) for c in engines.leiden_communities(x, ladder, seed=1)}
    for rung in ladder:
        single = {tuple(c) for c in engines.leiden_communities(x, np.array([rung]), seed=1)}
        assert single <= pooled, "pooling must not lose a rung's communities"
    assert len(pooled) > max(
        len(engines.leiden_communities(x, np.array([r]), seed=1)) for r in ladder
    )


def test_a_single_low_resolution_rung_collapses_connected_data() -> None:
    """The failure the amendment fixes, pinned so it cannot quietly return.

    At the bottom of the ladder Leiden gives a few very large communities. Under the original
    one-rung-per-run rule, a run drawn there proposed almost nothing inside the size limits while
    still counting in every grouping's eligibility denominator -- on the real 10,770 the probe
    measured exactly zero usable candidates at resolution 0.0014.

    The fixture must be CONNECTED for this to show. Well-separated blobs make the kNN graph nearly
    disconnected, and modularity keeps disconnected components apart at every resolution, so the
    collapse the amendment is about cannot happen there -- which is itself worth knowing: arm B's
    weakness at low resolution depends on the data being connected, and real embeddings are.
    """
    pytest.importorskip("leidenalg")
    rng = np.random.default_rng(3)
    # One diffuse cloud: a connected kNN graph with no natural partition.
    x = rng.standard_normal((120, 6))
    x /= np.linalg.norm(x, axis=1, keepdims=True)
    low = engines.leiden_communities(x, np.array([engines.RESOLUTION_LO]), seed=1)
    high = engines.leiden_communities(x, np.array([engines.RESOLUTION_HI]), seed=1)

    assert len(low) < len(high), "low resolution must give fewer, larger communities"
    assert max(len(c) for c in low) > max(len(c) for c in high)
    # The point: at the bottom rung almost everything is in one blob, so a size cap removes it and
    # the run contributes nothing.
    assert max(len(c) for c in low) > 0.5 * x.shape[0]


def test_persistent_leiden_keeps_a_subset_and_prefers_the_stable_ones() -> None:
    """Arm B2 filters arm B's candidates; it never invents one."""
    pytest.importorskip("leidenalg")
    x = _blobs(groups=5, per=20)
    ladder = engines.resolution_ladder()
    everything = {tuple(c) for c in engines.leiden_communities(x, ladder, seed=3)}
    persistent = {tuple(c) for c in engines.leiden_persistent(x, ladder, seed=3)}

    assert persistent <= everything, "B2 must be a subset of B on the same run"
    assert persistent, "the well-separated blobs persist across rungs; something must survive"
    blobs = {tuple(range(g * 20, (g + 1) * 20)) for g in range(5)}
    assert blobs <= persistent, "a genuinely stable community must survive the filter"
    assert engines.leiden_persistent(x, ladder, 3) == engines.leiden_persistent(x, ladder, 3)


def test_persistence_tau_is_hidefs_and_a_higher_tau_keeps_less() -> None:
    """The filter is a real threshold, not decoration."""
    pytest.importorskip("leidenalg")
    assert engines.PERSISTENCE_TAU == 0.75
    x = _blobs(groups=6, per=12)
    ladder = engines.resolution_ladder()
    loose = len(engines.leiden_persistent(x, ladder, 2, tau=0.1))
    strict = len(engines.leiden_persistent(x, ladder, 2, tau=1.0))
    assert strict <= loose


def test_bisecting_spherical_kmeans_is_a_hierarchy_that_finds_the_blobs() -> None:
    """Arm G: nested, deterministic, and it recovers separated structure."""
    x = _blobs(groups=4, per=16)
    members, parent = engines.bisecting_spherical_kmeans(x, seed=5)

    assert all(len(m) >= engines.BISECT_MIN_SIZE for m in members)
    assert sorted(members[0]) == list(range(x.shape[0])), "the root is everything"
    for child, up in enumerate(parent.tolist()):
        if up >= 0:
            assert set(members[child]) <= set(members[up]), "nested by construction"
    blobs = {frozenset(range(g * 16, (g + 1) * 16)) for g in range(4)}
    assert blobs <= {frozenset(m) for m in members}
    again, _ = engines.bisecting_spherical_kmeans(x, seed=5)
    assert [sorted(m) for m in members] == [sorted(m) for m in again]


def test_bisecting_stops_below_the_split_floor() -> None:
    """No cluster at or above the floor is left unsplit, and none below is split."""
    x = _blobs(groups=3, per=10)
    members, parent = engines.bisecting_spherical_kmeans(x, seed=1)
    children: dict[int, int] = {}
    for up in parent.tolist():
        if up >= 0:
            children[up] = children.get(up, 0) + 1
    for index, group in enumerate(members):
        if len(group) < engines.BISECT_MIN_SPLIT:
            assert children.get(index, 0) == 0, "a cluster below the floor must be a leaf"


def test_infomap_returns_every_level_of_the_hierarchy() -> None:
    """Arm H: modules at every level, nested, deterministic."""
    pytest.importorskip("infomap")
    x = _blobs(groups=5, per=20)
    found = engines.infomap_modules(x, seed=4)

    assert found, "infomap must find something on well-separated blobs"
    assert len({tuple(c) for c in found}) == len(found), "deduplicated"
    for module in found:
        assert all(0 <= i < x.shape[0] for i in module), "row indices into the sample"
    big = [m for m in found if len(m) >= 3]
    assert big
    assert engines.infomap_modules(x, 4) == found


def test_linkage_candidates_excludes_leaves_and_nests_correctly() -> None:
    """Every merge, with a parent structure whose members really do contain the child's."""
    # Three merges over four points: (0,1), (2,3), then the two together.
    z = np.array([[0.0, 1.0, 0.1, 2.0], [2.0, 3.0, 0.2, 2.0], [4.0, 5.0, 0.9, 4.0]])
    members, parent = engines.linkage_candidates(z, 4)

    assert [sorted(m) for m in members] == [[0, 1], [2, 3], [0, 1, 2, 3]]
    assert parent.tolist() == [2, 2, -1]
    for child, up in enumerate(parent.tolist()):
        if up >= 0:
            assert set(members[child]) <= set(members[up])


def test_average_linkage_is_a_hierarchy_over_the_sample() -> None:
    """UPGMA on cosine distance gives m-1 nested merges, deterministically."""
    x = _blobs(groups=4, per=10)
    members, parent = engines.average_linkage(x)

    assert len(members) == x.shape[0] - 1
    assert sorted(members[-1]) == list(range(x.shape[0])), "the last merge is everything"
    for child, up in enumerate(parent.tolist()):
        if up >= 0:
            assert set(members[child]) <= set(members[up])
    again, _ = engines.average_linkage(x)
    assert [sorted(m) for m in members] == [sorted(m) for m in again]


def test_average_linkage_finds_the_blobs_among_its_merges() -> None:
    """The structure is there to be found, not just well-formed."""
    x = _blobs(groups=4, per=10)
    members, _parent = engines.average_linkage(x)
    blobs = {frozenset(range(g * 10, (g + 1) * 10)) for g in range(4)}
    assert blobs <= {frozenset(m) for m in members}


# ------------------------------------------------- the one-module invariant

# The same containment `llm.py` gives the Anthropic SDK and `embed.py` gives the encoder. Five new
# third-party clustering libraries arrived with the engine search, and the convention exists exactly
# so a later reader can tell what the build depends on by reading one file. A rule nothing checks is
# a rule that erodes.
#: Library -> every file allowed to import it. `igraph` has a second home and the exception is
#: named rather than papered over: `build_hidef.py` runs HiDeF, a THIRD-PARTY BASELINE implemented
#: against its own library's graph type. It is not a THEMA engine and must not import from
#: `engines.py`, or the baseline would stop being independent of the thing it is a baseline for.
ENGINE_LIBRARIES = {
    "leidenalg": ["src/thema/ontology/engines.py"],
    "igraph": ["scripts/build_hidef.py", "src/thema/ontology/engines.py"],
    "sknetwork": ["src/thema/ontology/engines.py"],
    "umap": ["src/thema/ontology/engines.py"],
    "hdbscan": ["src/thema/ontology/engines.py"],
}


@pytest.mark.parametrize("library", sorted(ENGINE_LIBRARIES))
def test_each_engine_library_is_imported_by_exactly_one_file(library: str) -> None:
    """Every clustering library stays inside ``engines.py``, bar one named exception.

    Args:
        library: The top-level module name.
    """
    import pathlib
    import re

    root = pathlib.Path(__file__).resolve().parents[2]
    pattern = re.compile(rf"^\s*(?:import {library}|from {library}\b)")
    importers = sorted(
        str(path.relative_to(root))
        for directory in ("src", "scripts")
        for path in (root / directory).rglob("*.py")
        if any(pattern.match(line) for line in path.read_text().splitlines())
    )
    assert importers == ENGINE_LIBRARIES[library], (
        f"{library} must stay confined to {ENGINE_LIBRARIES[library]}; found it in {importers}"
    )


def test_the_engines_module_imports_nothing_heavy_at_module_level() -> None:
    """Importing ``engines`` must not drag in UMAP, numba or torch.

    Arm E's dependency chain is heavy and slow to import. Every engine library is imported inside
    the function that needs it, so a Ward-only build -- which is still the frozen build -- pays
    nothing for the alternatives being available.
    """
    import subprocess
    import sys

    program = (
        "import sys; import thema.ontology.engines; "
        "heavy = [m for m in ('umap', 'hdbscan', 'numba', 'torch', 'leidenalg', 'sknetwork') "
        "if m in sys.modules]; "
        "print(','.join(heavy))"
    )
    out = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True, check=True
    )
    assert out.stdout.strip() == "", f"engines.py pulled in {out.stdout.strip()} at import time"
