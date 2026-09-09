import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from thema.cluster import (
    DEFAULT_CUTS,
    LINKAGES,
    condensed_bytes,
    cut,
    distances,
    size_distribution,
    trees,
)
from thema.embed import l2_normalize

REPO_ROOT = Path(__file__).resolve().parents[1]


# Blobs must be separated in DIRECTION, not in magnitude: everything is put on the unit sphere
# before it is clustered, so three clouds around 0, +5 and -5 would collapse to noise and two
# antipodes. Each centre here is a distinct axis, which survives normalization.
def _blobs(axes=(0, 1, 2), per=20, dim=8, spread=0.05, seed=0):
    rng = np.random.default_rng(seed)
    clouds = []
    for axis in axes:
        centre = np.zeros(dim)
        centre[axis] = 5.0
        clouds.append(centre + rng.normal(0.0, spread, (per, dim)))
    return np.vstack(clouds)


# ------------------------------------------------- the one-module invariant


# The same containment llm.py gives the Anthropic SDK. cluster.py must stay testable without a
# multi-gigabyte install, and a rule nothing checks is a rule that erodes.
def test_sentence_transformers_is_imported_by_exactly_one_file_in_the_repo():
    pattern = re.compile(r"^\s*(?:import sentence_transformers|from sentence_transformers\b)")
    sources = sorted(
        path
        for directory in ("src", "scripts")
        for path in (REPO_ROOT / directory).rglob("*.py")
    )
    importers = [
        str(p.relative_to(REPO_ROOT))
        for p in sources
        if any(pattern.match(line) for line in p.read_text().splitlines())
    ]
    assert importers == ["src/thema/embed.py"], (
        f"the encoder must stay confined to one module; found it in {importers}"
    )


def test_clustering_works_with_the_encoder_made_unavailable():
    program = (
        "import builtins, sys\n"
        "real = builtins.__import__\n"
        "def blocked(name, *a, **k):\n"
        "    if name.split('.')[0] in ('sentence_transformers', 'torch'):\n"
        "        raise ImportError(name)\n"
        "    return real(name, *a, **k)\n"
        "builtins.__import__ = blocked\n"
        "import numpy as np\n"
        "from thema.cluster import distances, trees, cut\n"
        "from thema.embed import l2_normalize\n"
        "v = l2_normalize(np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]))\n"
        "print(len(cut(trees(distances(v))['ward'], 2)))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True, cwd=REPO_ROOT
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "3"


# ------------------------------------------------------------ normalization


def test_normalizing_puts_every_row_on_the_unit_sphere():
    lengths = np.linalg.norm(l2_normalize(_blobs()), axis=1)
    assert np.allclose(lengths, 1.0, atol=1e-5)


# A zero row cannot be normalized. Turning it into NaN would poison every distance it takes part
# in, not just its own, so it is left alone instead.
def test_a_zero_row_survives_normalization_rather_than_becoming_nan():
    out = l2_normalize(np.array([[0.0, 0.0], [3.0, 4.0]]))
    assert not np.isnan(out).any()
    assert np.allclose(out[1], [0.6, 0.8])


# This is the 2024 prototype's silent bug, and the reason distances() checks rather than trusts:
# unnormalized Ward clusters partly by vector magnitude, which tracks text length.
def test_unnormalized_vectors_are_refused_rather_than_silently_clustered():
    with pytest.raises(ValueError, match="not unit length"):
        distances(np.array([[3.0, 4.0], [1.0, 0.0], [0.0, 2.0]]))


def test_fewer_than_two_vectors_is_an_error():
    with pytest.raises(ValueError, match="at least two"):
        distances(l2_normalize(np.array([[1.0, 0.0]])))


# --------------------------------------------------------------- linkages


def test_all_three_linkages_come_from_the_same_distance_matrix():
    condensed = distances(l2_normalize(_blobs()))
    built = trees(condensed)
    assert set(built) == set(LINKAGES)
    for method, tree in built.items():
        assert tree.shape == (len(_blobs()) - 1, 4), f"{method} produced a malformed linkage"


def test_no_linkage_is_privileged_in_the_default_set():
    assert LINKAGES == ("ward", "average", "complete")


def test_every_linkage_recovers_three_well_separated_blobs():
    condensed = distances(l2_normalize(_blobs()))
    for method, tree in trees(condensed).items():
        labels = cut(tree, 3)
        assert len(set(labels)) == 3, f"{method} did not find three clusters"
        # The blobs are 20 apiece and mutually orthogonal; any linkage that splits them unevenly
        # here is broken, not merely different.
        assert size_distribution(labels)["max"] == 20, f"{method} ran one cluster away"


def test_cutting_deeper_never_yields_fewer_clusters():
    tree = trees(distances(l2_normalize(_blobs(per=30))))["ward"]
    counts = [len(set(cut(tree, k))) for k in (2, 5, 10)]
    assert counts == sorted(counts)


# --------------------------------------------------- size distribution


def test_the_size_distribution_reports_the_two_numbers_the_failures_show_up_in():
    labels = np.array([1] * 50 + [2] + [3] + [4])
    spread = size_distribution(labels)
    assert spread["clusters"] == 4
    assert spread["singletons"] == 3, "average linkage's tail of singletons must be visible"
    assert spread["largest_share"] == pytest.approx(50 / 53), "a runaway cluster must be visible"


def test_an_even_split_reports_no_singletons_and_a_small_largest_share():
    spread = size_distribution(np.array([1] * 10 + [2] * 10 + [3] * 10))
    assert spread["singletons"] == 0
    assert spread["largest_share"] == pytest.approx(1 / 3)


# ------------------------------------------------------------- memory


# The one thing here that grows as the square of the input. Measured so a full run's footprint is
# known before it is attempted rather than discovered by an OOM kill.
def test_the_condensed_matrix_footprint_is_quadratic_and_reported_in_bytes():
    assert condensed_bytes(2) == 8
    assert condensed_bytes(1844) == 1844 * 1843 // 2 * 8
    assert condensed_bytes(10817) / 1e6 == pytest.approx(468.0, abs=1.0)


def test_the_default_cuts_span_a_range_rather_than_naming_one_answer():
    assert len(DEFAULT_CUTS) > 1
    assert list(DEFAULT_CUTS) == sorted(DEFAULT_CUTS)


# ---------------------------------------------------- stand-in labelling


# A plumbing run on native prose produces a tree that looks exactly like a real one and is not one.
# The label is structural rather than a note someone remembers to write.
def test_a_run_on_anything_other_than_generated_descriptions_is_marked_a_stand_in():
    from build_ontology import is_stand_in
    from thema.normalize import PROVENANCE

    real = set(PROVENANCE.values())
    assert not is_stand_in("smoke", real), "a normal smoke run is not a stand-in"
    assert not is_stand_in("full", real)
    assert is_stand_in("plumbing", real), "an unrecognised scope is a stand-in"
    assert is_stand_in("smoke", {"native_stand_in"}), "unknown provenance is a stand-in"
    assert is_stand_in("smoke", real | {"native_stand_in"}), "one odd row taints the run"


def test_the_stand_in_warning_leads_the_stamp_so_it_cannot_be_skimmed_past():
    from build_ontology import stamp

    assert stamp("plumbing", "abc123", 400, True).startswith("*** STAND-IN TEXT, NOT A RESULT ***")
    assert "STAND-IN" not in stamp("smoke", "abc123", 1844, False)
