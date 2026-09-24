"""Analysis must not reach embeddings except through the verifying loader."""

import re
from pathlib import Path

import numpy as np
import pytest

from thema.ontology.universe import Embedded, load_embedded, universe_digest

ROOT = Path(__file__).resolve().parents[2]

#: The loader itself, and the build script that WRITES the artifact, are allowed to touch it.
ALLOWED = {
    "src/thema/ontology/universe.py",
    "scripts/build_ontology.py",
    # v0.1 is the FROZEN v3-era reference. Its contents are history, not a current claim, and it
    # is deliberately NOT filtered -- filtering it would break the fidelity check it exists for.
    "tests/ontology/test_ward.py",
    # export_demo.py renders the FLAT v0.1-era build (clusters_ward.tsv and its own keys file),
    # which is frozen and deliberately unfiltered. Pointing it at the v0.2 artifact would mix
    # two builds: keys from one, vectors from the other.
    "scripts/export_demo.py",
}

_LOAD = re.compile(r"np\.load\s*\([^)]*embeddings", re.I)
_KEYS = re.compile(r"embedding_keys\.txt")


def _sources() -> list[Path]:
    return [
        p
        for d in ("src", "scripts", "tests")
        for p in (ROOT / d).rglob("*.py")
        if "__pycache__" not in p.parts
    ]


def test_nothing_loads_embeddings_outside_the_verifying_loader() -> None:
    """A rule enforced at one entry point, with a second entry point that bypasses it, is not
    enforced. Two runs were calibrated on a superseded universe before that was noticed."""
    offenders = []
    for path in _sources():
        rel = path.relative_to(ROOT).as_posix()
        if rel in ALLOWED or rel == "tests/ontology/test_universe.py":
            continue
        text = path.read_text(encoding="utf-8")
        if _LOAD.search(text) or _KEYS.search(text):
            offenders.append(rel)
    assert not offenders, (
        "these load embeddings directly instead of thema.ontology.universe.load_embedded: "
        + ", ".join(sorted(offenders))
    )


def test_the_loader_raises_rather_than_filtering(tmp_path: Path) -> None:
    """Silently dropping rows is how a superseded universe goes unnoticed."""
    real_keys = (ROOT / "data/ontology/v0.2/embedding_keys.txt").read_text().split("\n")[:3]
    (tmp_path / "embedding_keys.txt").write_text(
        "\n".join([k for k in real_keys if k] + ["reactome:R-HSA-1222541"]) + "\n",
        encoding="utf-8",
    )
    np.save(tmp_path / "embeddings.npy", np.zeros((4, 8)))
    with pytest.raises(ValueError, match="excludes"):
        load_embedded(tmp_path, ROOT / "data/pathways.tsv")


def test_a_keys_row_mismatch_is_caught(tmp_path: Path) -> None:
    (tmp_path / "embedding_keys.txt").write_text("go:1\ngo:2\n", encoding="utf-8")
    np.save(tmp_path / "embeddings.npy", np.zeros((3, 4)))
    with pytest.raises(ValueError, match="inconsistent with itself"):
        load_embedded(tmp_path, tmp_path / "pathways.tsv")


def test_the_digest_is_order_independent() -> None:
    assert universe_digest({"b", "a"}) == universe_digest({"a", "b"})
    assert universe_digest({"a"}) != universe_digest({"a", "b"})


def test_the_real_artifact_is_the_universe() -> None:
    """The committed v0.2 artifact must hold the universe and nothing else."""
    e = load_embedded(ROOT / "data/ontology/v0.2", ROOT / "data/pathways.tsv")
    assert isinstance(e, Embedded)
    assert len(e.keys) == e.vectors.shape[0] == 1850
