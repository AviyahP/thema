"""The top of O50s: the stability measure, the item rules and both arms' invariants.

The measure is the part worth testing, because two of its choices change the answer. It scores
against **every** internal dendrogram node, including those above half a draw, which the cached runs
deliberately do not record -- scoring a 2,000-pathway theme against the recorded set alone would cap
its achievable Jaccard and understate exactly the bands the cut depends on. And the AUC counts ties
as half, which matters when thousands of scrambled candidates share one support value.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest

import top_two_arms as tta

TOP = Path("data/ontology/v0.4-leaves/thema_L_x2_O50s_top")
O50S = Path("data/ontology/v0.4-leaves/thema_L_x2_O50s")
REVIEW = Path("data/experiments/top_two_arms_2026-10-17")


def test_bands_are_contiguous_doublings_from_50() -> None:
    assert tta.BANDS[0][0] == tta.FROM_SIZE == 50
    assert tta.BANDS[-1][1] == 10 ** 9
    for (_, high), (low, _) in zip(tta.BANDS, tta.BANDS[1:], strict=False):
        assert low == high + 1
    assert tta.band_of(49) is None
    assert tta.band_of(50) == "50-99"
    assert tta.band_of(10 ** 6) == "1600+"
    assert tta.label(1600, 10 ** 9) == "1600+"


def test_auc_is_one_when_the_populations_do_not_overlap() -> None:
    assert tta.auc([0.5, 0.6, 0.7], [0.1, 0.2]) == pytest.approx(1.0)
    assert tta.auc([0.1, 0.2], [0.5, 0.6, 0.7]) == pytest.approx(0.0)


def test_auc_counts_ties_as_half() -> None:
    """Thousands of scrambled candidates share one support value, so this is not academic."""
    assert tta.auc([1.0, 1.0], [1.0, 1.0]) == pytest.approx(0.5)
    # Four pairs: one tie worth a half, three clear wins, so 3.5 of 4.
    assert tta.auc([1.0, 2.0], [1.0, 0.0]) == pytest.approx(0.875)
    assert tta.auc([1.0], [1.0, 0.0]) == pytest.approx(0.75)


def test_auc_refuses_an_empty_side() -> None:
    assert tta.auc([], [0.1]) is None
    assert tta.auc([0.1], []) is None


def test_quartiles_and_the_empty_case() -> None:
    assert tta.quartiles([1, 2, 3, 4]) == pytest.approx((1.75, 2.5, 3.25))
    assert tta.quartiles([]) == (0.0, 0.0, 0.0)


def test_run_clusters_returns_the_whole_dendrogram_not_only_the_recorded_part() -> None:
    """The choice that changes the large bands: no upper cap on a cluster's size."""
    from scipy.spatial.distance import pdist

    rng = np.random.default_rng(4)
    x = rng.normal(size=(40, 6))
    x /= np.linalg.norm(x, axis=1, keepdims=True)
    full = pdist(x, metric="euclidean")
    sub = np.arange(40)
    block, sizes = tta.run_clusters(full, 40, sub)
    # 39 internal nodes; those of 3 or more members are kept, and the root of 40 is among them.
    assert len(block) == len(sizes)
    assert sizes.max() == 40, "the top of the tree must be scored against, not excluded"
    assert sizes.min() >= tta.MIN_CLUSTER
    assert block.shape[1] == 40
    assert np.allclose(block.sum(axis=1), sizes)
    assert set(np.unique(block)) <= {0.0, 1.0}, "an indicator, so the sets stay disjoint"


def test_stability_is_one_for_a_cluster_the_tree_actually_contains() -> None:
    """A group that IS a dendrogram node scores 1.0 on a run that draws all of it."""
    from scipy.spatial.distance import pdist

    rng = np.random.default_rng(11)
    left = rng.normal(loc=-6.0, scale=0.01, size=(10, 4))
    right = rng.normal(loc=6.0, scale=0.01, size=(10, 4))
    x = np.vstack([left, right])
    x /= np.linalg.norm(x, axis=1, keepdims=True)
    full = pdist(x, metric="euclidean")
    rows = [np.arange(20)]
    got = tta.stability([set(range(10))], full, 20, rows, report=False)
    assert got.shape == (1, 1)
    assert got[0, 0] == pytest.approx(1.0), "the left blob is a node of this tree"


def test_stability_is_low_for_a_group_the_tree_splits() -> None:
    from scipy.spatial.distance import pdist

    rng = np.random.default_rng(12)
    left = rng.normal(loc=-6.0, scale=0.01, size=(10, 4))
    right = rng.normal(loc=6.0, scale=0.01, size=(10, 4))
    x = np.vstack([left, right])
    x /= np.linalg.norm(x, axis=1, keepdims=True)
    full = pdist(x, metric="euclidean")
    rows = [np.arange(20)]
    # Five from each blob: no node of the tree looks like this.
    mixed = set(range(5)) | set(range(10, 15))
    got = tta.stability([mixed], full, 20, rows, report=False)
    assert got[0, 0] < 0.6


needs_stability = pytest.mark.skipif(
    not (TOP / "stability.json").exists(),
    reason="the stability pass has not run")
needs_arms = pytest.mark.skipif(
    not (TOP / "A" / "levels.json").exists() or not (TOP / "B" / "levels.json").exists(),
    reason="the arms are not built")


@needs_stability
def test_the_cut_is_the_first_band_under_the_declared_threshold() -> None:
    got = json.loads((TOP / "stability.json").read_text())
    below = [e for e in got["table"] if e["n_themes"] and e["median"] < got["cut"]]
    assert got["T"] == (below[0]["low"] if below else None)
    assert got["T"] == 50, "every band is under 0.6, so the cut falls at the first one"
    # The premise behind arm B -- that stability falls as themes grow -- is not what was measured.
    medians = [e["median"] for e in got["table"] if e["n_themes"]]
    assert medians != sorted(medians, reverse=True), "the medians are not monotonically falling"
    assert max(medians) == got["table"][4]["median"], "800-1,599 is the most stable band"


@needs_stability
def test_every_band_separates_real_from_scrambled() -> None:
    got = json.loads((TOP / "stability.json").read_text())
    for entry in got["table"]:
        if not entry["n_null"]:
            continue
        assert entry["cut_above_null_p95"] is True, entry["band"]
        assert entry["auc_stability"] == pytest.approx(1.0, abs=1e-6), entry["band"]
        assert entry["auc_support"] == pytest.approx(1.0, abs=1e-6), entry["band"]


@needs_arms
@pytest.mark.parametrize("arm", ["A", "B"])
def test_the_roots_are_exactly_the_nodes_with_no_parent(arm: str) -> None:
    payload = json.loads((TOP / arm / "levels.json").read_text())
    stated = set(payload["roots"])
    assert stated == {node for node, above in payload["parents"].items() if not above}
    with (TOP / arm / "edges.tsv").open(encoding="utf-8") as handle:
        has_parent = {row["child"] for row in csv.DictReader(handle, delimiter="\t")}
    assert stated == set(payload["view"]) - has_parent


@needs_arms
@pytest.mark.parametrize("arm", ["A", "B"])
def test_every_areas_pathway_set_is_the_union_of_its_items(arm: str) -> None:
    import recursive_top_O50 as rt

    payload = json.loads((TOP / arm / "levels.json").read_text())
    _nodes, members = rt.read_build(O50S)
    for node, keys in payload["area_members"].items():
        union: set[str] = set()
        for item in payload["area_units"][node]:
            union |= ({item[len("loose:"):]} if item.startswith("loose:")
                      else set(members[item]))
        assert set(keys) == union, f"{arm}/{node}"


@needs_arms
@pytest.mark.parametrize("arm", ["A", "B"])
def test_the_reviewer_tables_match_the_build(arm: str) -> None:
    payload = json.loads((TOP / arm / "levels.json").read_text())
    folder = REVIEW / arm
    if not (folder / "roots.tsv").exists():
        pytest.skip("the reviewer tables are not written")
    with (folder / "roots.tsv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    assert {r["node"] for r in rows} == set(payload["roots"])
    for row in rows:
        assert len(row["members"].split()) == int(row["size"])
    with (folder / "small_roots.tsv").open(encoding="utf-8") as handle:
        small = list(csv.DictReader(handle, delimiter="\t"))
    assert {r["root"] for r in small} == set(payload["small_roots"])
    for row in small:
        assert int(row["root_size"]) <= tta.SMALL_ROOT
        assert 1 <= int(row["rank"]) <= 3
        assert int(row["container_size"]) > int(row["root_size"])


@needs_arms
def test_arm_b_keeps_its_items_under_the_cut_and_drops_the_rest() -> None:
    import recursive_top_O50 as rt

    cut = json.loads((TOP / "stability.json").read_text())["T"]
    payload = json.loads((TOP / "B" / "levels.json").read_text())
    _nodes, members = rt.read_build(O50S)
    for item in payload["item_ids"]:
        if item.startswith("loose:"):
            continue
        assert len(members[item]) < cut, item
    # Maximality: no item is strictly inside another item.
    held = {i: set(members[i]) for i in payload["item_ids"] if not i.startswith("loose:")}
    for name, mine in held.items():
        assert not any(mine < other for other, _ in
                       ((o, v) for o, v in held.items() if o != name and v > mine)), name


@needs_arms
@pytest.mark.parametrize("arm", ["A", "B"])
def test_giant_areas_are_kept_in_the_view_and_flagged(arm: str) -> None:
    """Both arms were asked to keep them, unlike rec2fix which drops them."""
    payload = json.loads((TOP / arm / "levels.json").read_text())
    assert payload["giants"], "there should be nodes over 1,000 pathways"
    for node in payload["giants"]:
        assert node in set(payload["view"]), f"{arm}/{node} was dropped"
