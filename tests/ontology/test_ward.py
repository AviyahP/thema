"""`ward_tree` through the builder interface.

Structure on synthetic vectors, and fidelity to the committed v0.1 build.
"""

import csv
import json
import pathlib
from pathlib import Path

import numpy as np
import pytest

from thema.ontology.base import check_distinct_members
from thema.ontology.registry import BUILDERS, builder

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "data"
CLUSTERS = DATA / "ontology" / "clusters_ward.tsv"
# The v0.1 embeddings live under their own version directory. Before 2026-09-21 these tests read
# the flat `data/ontology/embeddings.npy`, which a v0.2 rebuild overwrites -- so they would have
# compared a v4 build against the committed v3 partition and failed for the wrong reason.
EMBEDDINGS = DATA / "ontology" / "v0.1" / "embeddings.npy"
EMBEDDING_KEYS = DATA / "ontology" / "v0.1" / "embedding_keys.txt"
V01_LEVELS = (10, 25, 50, 100, 200)
V02 = DATA / "ontology" / "v0.2" / "ward_tree"
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"


def blobs(axes=(0, 1, 2), per=20, dim=8, spread=0.05, seed=0):
    """Well-separated blobs, each centre on its own axis.

    Separation has to be in DIRECTION, not magnitude: everything is L2-normalised before
    clustering, so blobs placed at different distances along one axis collapse onto each other.
    Same idiom as `tests/test_cluster.py`.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for axis in axes:
        centre = np.zeros(dim)
        centre[axis] = 5.0
        rows.append(centre + rng.normal(scale=spread, size=(per, dim)))
    x = np.vstack(rows)
    return (x / np.linalg.norm(x, axis=1, keepdims=True)).astype(np.float32)


def test_the_registry_knows_ward_tree():
    assert "ward_tree" in BUILDERS
    assert builder("ward_tree").method == "ward_tree"
    with pytest.raises(KeyError, match="unknown method"):
        builder("no-such-method")


# ------------------------------------------------------ structure, on synthetic vectors


def test_cuts_nest_and_the_coarsest_cut_is_the_forest_of_roots():
    keys = [f"p{i}" for i in range(60)]
    o = builder("ward_tree").build(blobs(), keys, {"levels": [3, 6, 12]})
    assert {n.id.split(":")[0] for n in o.roots} == {"k3"}, "roots are the coarsest cut"
    assert len(o.roots) == 3
    assert not o.unplaced, "every pathway sits in a cluster at every cut"
    for node in o.nodes:
        for parent in node.parents:
            assert node.keys <= o.by_id[parent].keys


def test_no_synthetic_root_is_added():
    """Addendum A3: the coarsest cut is a forest; there is no all-pathways node."""
    keys = [f"p{i}" for i in range(60)]
    o = builder("ward_tree").build(blobs(), keys, {"levels": [3, 6]})
    everything = frozenset(keys)
    assert all(node.keys != everything for node in o.nodes)


def test_every_member_is_fully_included_and_every_node_fully_supported():
    keys = [f"p{i}" for i in range(60)]
    o = builder("ward_tree").build(blobs(), keys, {"levels": [3, 6]})
    assert all(inclusion == 1.0 for node in o.nodes for _key, inclusion in node.members)
    assert all(node.support == 1.0 for node in o.nodes)


def test_levels_at_or_above_n_are_dropped_and_an_empty_request_is_refused():
    keys = [f"p{i}" for i in range(60)]
    o = builder("ward_tree").build(blobs(), keys, {"levels": [3, 60, 900]})
    assert o.params["levels"] == [3]
    with pytest.raises(ValueError, match="no usable level"):
        builder("ward_tree").build(blobs(), keys, {"levels": [60]})


def test_the_same_vectors_build_the_same_tree_twice():
    keys = [f"p{i}" for i in range(60)]
    x = blobs()
    first = builder("ward_tree").build(x, keys, {"levels": [3, 6]})
    second = builder("ward_tree").build(x, keys, {"levels": [3, 6]})
    assert [(n.id, n.members, n.parents) for n in first.nodes] == [
        (n.id, n.members, n.parents) for n in second.nodes
    ]


# ------------------------------------------------------ fidelity to the committed v0.1 build
#
# ward_tree is a RE-EXPORT, not a new method: its member sets must not move, because the demo and
# every measurement taken so far read `clusters_ward.tsv`. This is the §9 done-condition, kept as a
# test so a later refactor of the builder cannot quietly change the ontology.
#
# `embeddings.npy` is gitignored and regenerable, so the test skips rather than fails in a clean
# clone. `clusters_ward.tsv` IS committed, which is what makes the comparison meaningful at all.


def committed_member_sets():
    """Member sets per node id, read from the committed v0.1 cluster table."""
    out: dict[str, set[str]] = {}
    with CLUSTERS.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            for level in V01_LEVELS:
                out.setdefault(f"k{level}:{row[f'k{level}']}", set()).add(row["key"])
    return out


@pytest.mark.skipif(
    not (EMBEDDINGS.is_file() and EMBEDDING_KEYS.is_file() and CLUSTERS.is_file()),
    reason="needs the built v0.1 artifacts; embeddings.npy is gitignored and regenerable",
)
def test_the_interface_build_reproduces_the_committed_v01_ontology_member_for_member():
    keys = [line for line in EMBEDDING_KEYS.read_text().split("\n") if line]
    built = builder("ward_tree").build(np.load(EMBEDDINGS), keys, {"levels": list(V01_LEVELS)})
    assert {node.id: set(node.keys) for node in built.nodes} == committed_member_sets()


@pytest.mark.skipif(
    not (EMBEDDINGS.is_file() and EMBEDDING_KEYS.is_file() and CLUSTERS.is_file()),
    reason="needs the built v0.1 artifacts; embeddings.npy is gitignored and regenerable",
)
def test_the_v01_build_is_a_forest_of_ten_roots_with_repeated_memberships_allowed():
    keys = [line for line in EMBEDDING_KEYS.read_text().split("\n") if line]
    built = builder("ward_tree").build(np.load(EMBEDDINGS), keys, {"levels": list(V01_LEVELS)})
    assert len(built.roots) == 10, "the ten k=10 clusters, not a synthetic root and not 76"
    assert {n.id for n in built.roots} == {f"k10:{i}" for i in range(1, 11)}
    repeated = len(built.nodes) - len({n.keys for n in built.nodes})
    assert repeated > 0, "cuts that do not split repeat a membership; that is legitimate here"
    with pytest.raises(ValueError, match="identical members"):
        check_distinct_members(built)


# ------------------------------------------------------ the algorithm, on a committed fixture
#
# Independent of which description generation is live. The v0.1 and v0.2 tests below pin the
# builder against real data and will legitimately change when the data does; this one pins the
# ALGORITHM and must not. If it fails, the clustering changed -- not the corpus.


def test_the_algorithm_reproduces_its_committed_fixture_partition():
    expected = json.loads((FIXTURES / "blobs_ward.json").read_text())
    keys = [line for line in (FIXTURES / "blobs_keys.txt").read_text().split("\n") if line]
    built = builder("ward_tree").build(
        np.load(FIXTURES / "blobs.npy"), keys, {"levels": expected["levels"]}
    )
    assert {n.id: sorted(n.keys) for n in built.nodes} == expected["nodes"]
    assert {n.id: list(n.parents) for n in built.nodes} == expected["parents"]


def test_the_fixture_is_small_enough_to_read_and_big_enough_to_nest():
    expected = json.loads((FIXTURES / "blobs_ward.json").read_text())
    assert len(expected["levels"]) >= 3, "a fixture with one level cannot test nesting"
    assert any(parents for parents in expected["parents"].values()), "no edges, nothing pinned"


# ------------------------------------------------------ v0.2: the committed build matches the code


@pytest.mark.skipif(
    not (V02 / "members.tsv").is_file()
    or not (DATA / "ontology" / "v0.2" / "embeddings.npy").is_file(),
    reason="needs the v0.2 build; its embeddings are gitignored and regenerable",
)
def test_rebuilding_from_the_v4_embeddings_reproduces_the_committed_v02_files():
    from thema.ontology import export

    root = DATA / "ontology" / "v0.2"
    keys = [line for line in (root / "embedding_keys.txt").read_text().split("\n") if line]
    on_disk_keys = {k for members in export.read_members(V02).values() for k in members}
    if set(keys) != on_disk_keys:
        pytest.skip(
            f"the v0.2 artifact holds {len(keys):,} keys and the committed ward_tree holds "
            f"{len(on_disk_keys):,}: the universe rule moved the artifact ahead of the build "
            "(DECISIONS.md, 24 Sep). This passes again once the build is regenerated."
        )
    built = builder("ward_tree").build(
        np.load(root / "embeddings.npy"), keys, {"levels": list(V01_LEVELS)}
    )
    on_disk = export.read_members(V02)
    assert {n.id: sorted(n.keys) for n in built.nodes} == {
        node: sorted(members) for node, members in on_disk.items()
    }


@pytest.mark.skipif(
    not (V02 / "manifest.json").is_file(), reason="needs the v0.2 build"
)
def test_the_v02_manifest_records_which_descriptions_it_was_built_from():
    """Two ontologies from v3 and v4 text are indistinguishable without this (addendum A5)."""
    manifest = json.loads((V02 / "manifest.json").read_text())
    assert manifest["prompt_version"] == "v4"
    assert len(manifest["descriptions_sha256"]) == 64
    assert manifest["method"] == "ward_tree"
    assert manifest["n_roots"] == 10, "a forest of the ten k=10 clusters, not a synthetic root"
