"""Candidate generation across processes must not change a side's bytes.

`engine_runs` forks a worker pool because Leiden holds the GIL. The argument that this is safe is
structural -- each run reads its own persisted sample, is seeded from its own run index, shares
nothing writable, and `map` preserves order -- but the argument is what a previous version of this
codebase got wrong and paid for, so it is tested rather than trusted.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

REPO = Path(__file__).resolve().parents[1]
REAL_TREES = REPO / "data" / "ontology" / "v0.3" / "trees" / "centred_c54319cdfbbe9eb7"


def _vectors() -> np.ndarray:
    """The centred matrix, through the build's own path.

    Loaded with `engine_vectors` rather than `np.load` on the .npy: the universe invariant is that
    embeddings only ever reach code through the verifying loader, and a test that bypassed it would
    be testing a matrix the build would refuse.

    Returns:
        The ``(n, dim)`` centred unit-vector matrix.
    """
    from build_10770 import engine_vectors

    got = engine_vectors(REPO / "data" / "ontology" / "v0.3", REPO / "data",
                         "centred", "leiden", None, {})
    assert got is not None
    return got


def _same(left: list, right: list) -> None:
    """Assert two run lists are equal field by field.

    Args:
        left: One list of runs.
        right: The other.
    """
    assert len(left) == len(right)
    for index, (a, b) in enumerate(zip(left, right, strict=True)):
        for field in ("present", "clusters", "parent", "leaf_cluster", "sizes",
                      "chain_indptr", "chain_idx"):
            got, want = getattr(a, field), getattr(b, field)
            assert np.array_equal(got, want), f"run {index}, field {field}"


@pytest.mark.skipif(not REAL_TREES.is_dir(), reason="the persisted 10,770 trees are not present")
@pytest.mark.parametrize("engine", ["leiden", "bisect"])
def test_parallel_generation_is_byte_identical_to_serial(engine: str) -> None:
    """Four runs, serially and on three processes.

    Args:
        engine: The engine to generate with.
    """
    from build_10770 import engine_runs
    from cut_trees import cap_for

    n, cap = 10770, cap_for(10770)
    vectors = _vectors()
    assert vectors.shape[0] == n
    labels = [f"row{r:05d}" for r in range(1, 5)]

    serial = engine_runs(REAL_TREES, labels, n, cap, engine, vectors, workers=1)
    parallel = engine_runs(REAL_TREES, labels, n, cap, engine, vectors, workers=3)
    _same(serial, parallel)


@pytest.mark.skipif(not REAL_TREES.is_dir(), reason="the persisted 10,770 trees are not present")
def test_order_is_label_order_not_completion_order() -> None:
    """The slowest run must not end up in the wrong slot.

    Run order is not cosmetic: a run's index seeds its engine and positions it in `present`, so a
    reordered list would silently mis-attribute every candidate.
    """
    from build_10770 import engine_runs
    from cut_trees import cap_for

    n, cap = 10770, cap_for(10770)
    vectors = _vectors()
    labels = [f"row{r:05d}" for r in (1, 2, 3, 4, 5, 6)]
    runs = engine_runs(REAL_TREES, labels, n, cap, "bisect", vectors, workers=4)

    for label, run in zip(labels, runs, strict=True):
        with np.load(REAL_TREES / f"{label}.npz") as handle:
            assert np.array_equal(run.present, handle["present"]), label
