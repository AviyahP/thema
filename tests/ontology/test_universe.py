"""Analysis must not reach embeddings except through the verifying loader."""

import hashlib
import json
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
    # embed_universe.py WRITES the artifact -- it is the producer, not a consumer, and the
    # loader's job is to verify what this script produced.
    "scripts/embed_universe.py",
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

# ------------------------------------------- the encoder swap (DECISIONS.md, 24 Sep 2026)


def _artifact(directory: Path, keys: list[str], meta: dict, vectors: np.ndarray) -> Path:
    """Write a versioned artifact the loader will accept or refuse."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "embedding_keys.txt").write_text("\n".join(keys) + "\n", encoding="utf-8")
    np.save(directory / "embeddings.npy", vectors)
    meta.setdefault(
        "embeddings_sha256_16",
        hashlib.sha256((directory / "embeddings.npy").read_bytes()).hexdigest()[:16],
    )
    (directory / "universe.json").write_text(json.dumps(meta), encoding="utf-8")
    return directory


def _real_keys() -> list[str]:
    path = ROOT / "data/ontology/v0.2/embedding_keys.txt"
    return [line for line in path.read_text(encoding="utf-8").split("\n") if line]


def _real_universe_digest() -> str:
    """The WHOLE universe's digest, which is what the loader recomputes -- not the subset's."""
    meta = json.loads((ROOT / "data/ontology/v0.2/universe.json").read_text(encoding="utf-8"))
    return meta["universe_digest"]


def test_a_retired_encoder_is_refused_rather_than_loaded(tmp_path) -> None:
    """BioLORD read 128 tokens of a 231-token description; its vectors must never load again."""
    keys = _real_keys()
    vectors = np.zeros((len(keys), 4), dtype=np.float32)
    vectors[:, 0] = 1.0
    directory = _artifact(
        tmp_path / "v", keys,
        {"universe_digest": _real_universe_digest(),
         "embedder": {"id": "FremyCompany/BioLORD-2023", "revision": "main"}},
        vectors,
    )
    with pytest.raises(ValueError, match="retired encoder"):
        load_embedded(directory, ROOT / "data/pathways.tsv")


def test_vectors_that_do_not_match_their_recorded_hash_are_refused(tmp_path) -> None:
    """The universe digest covers KEYS, so it cannot see the vectors swapped underneath it."""
    keys = _real_keys()
    vectors = np.zeros((len(keys), 4), dtype=np.float32)
    vectors[:, 0] = 1.0
    directory = _artifact(
        tmp_path / "v", keys,
        {"universe_digest": _real_universe_digest(),
         "embedder": {"id": "ncbi/MedCPT-Article-Encoder", "revision": "d05a736"}},
        vectors,
    )
    swapped = np.zeros((len(keys), 4), dtype=np.float32)
    swapped[:, 1] = 1.0
    np.save(directory / "embeddings.npy", swapped)
    with pytest.raises(ValueError, match="not the ones this artifact describes"):
        load_embedded(directory, ROOT / "data/pathways.tsv")


def test_the_committed_artifact_records_a_pinned_encoder() -> None:
    """A frozen ontology needs a reproducible embedder: a commit sha, never a floating ref."""
    meta = json.loads(
        (ROOT / "data/ontology/v0.2/universe.json").read_text(encoding="utf-8")
    )
    embedder = meta["embedder"]
    assert embedder["id"] == "ncbi/MedCPT-Article-Encoder"
    assert len(embedder["revision"]) == 40, "pin to a commit sha, not to 'main'"
    assert embedder["pooling"] == "cls"
    assert embedder["max_length"] == 512


def test_no_description_is_truncated_by_the_encoder_window() -> None:
    """The claim that killed the last artifact was 'nothing truncates', asserted and never checked.

    Checked here on token counts, not on the architecture's advertised window.
    """
    from thema.data import descriptions as descriptions_table
    from thema.embed import MODEL_MAX_TOKENS, medcpt_token_counts

    texts = descriptions_table.read(ROOT / "data/pathway_descriptions.tsv")
    counts = medcpt_token_counts([texts[k] for k in _real_keys()])
    assert max(counts) <= MODEL_MAX_TOKENS, f"max {max(counts)} exceeds {MODEL_MAX_TOKENS}"
