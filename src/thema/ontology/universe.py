"""The one way analysis code should load embeddings: filtered to the universe, and verified.

The universe rule lives in ``partition_universe``, which takes a ``PathwayCollection``. Every
analysis script instead entered through ``np.load(embeddings.npy)`` and a keys file -- a path from
which the filter was not merely unused but UNREACHABLE. Two separate runs were therefore calibrated
on a superseded universe before anyone noticed (``docs/debt.md``).

The durable fix is that the ARTIFACT is correct, so a script that ignores this module still reads
the right thing. This loader is the second line: it recomputes the universe from ``pathways.tsv``
and RAISES if the stored keys disagree, so later drift is caught rather than absorbed.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from thema.data.pathways import PathwayCollection, partition_universe

EMBEDDINGS = "embeddings.npy"
KEYS = "embedding_keys.txt"
UNIVERSE = "universe.json"


@dataclass(frozen=True, slots=True)
class Embedded:
    """Embeddings and their keys, verified against the current universe.

    Attributes:
        keys: Pathway keys, in matrix row order.
        vectors: The embedding matrix.
        digest: The universe digest these were checked against.
        embedder: The encoder that produced the vectors, as ``universe.json`` records it.
    """

    keys: tuple[str, ...]
    vectors: np.ndarray
    digest: str
    embedder: dict | None = None


def universe_digest(keys: set[str]) -> str:
    """A short, order-independent digest of a universe."""
    return hashlib.sha256("\n".join(sorted(keys)).encode("utf-8")).hexdigest()[:16]


def load_embedded(directory: Path, pathways: Path) -> Embedded:
    """Load embeddings for analysis, verified against the universe.

    Args:
        directory: A versioned directory holding ``embeddings.npy`` and ``embedding_keys.txt``.
        pathways: Path to ``pathways.tsv``.

    Returns:
        The keys and vectors.

    Raises:
        ValueError: If the stored keys are not exactly the universe, if the vectors on disk are
            not the ones ``universe.json`` records, or if they were produced by a superseded
            encoder. **It raises rather than filtering**: silently dropping rows is how a
            superseded universe goes unnoticed, and a mismatch means the artifact needs
            rebuilding, not patching at read time.
    """
    keys = [line for line in (directory / KEYS).read_text(encoding="utf-8").split("\n") if line]
    vectors = np.load(directory / EMBEDDINGS)
    if len(keys) != vectors.shape[0]:
        raise ValueError(
            f"{directory}: {len(keys):,} keys but {vectors.shape[0]:,} rows -- the artifact is "
            "inconsistent with itself"
        )
    collection = PathwayCollection.from_tsv_text(pathways.read_text(encoding="utf-8"))
    kept, _excluded = partition_universe(collection)
    universe = {p.key for p in kept}
    stored = set(keys)
    outside = stored - universe
    if outside:
        raise ValueError(
            f"{directory} holds {len(outside)} key(s) the universe rule excludes, e.g. "
            f"{sorted(outside)[:3]}. Rebuild the artifact; do not filter at read time."
        )
    digest = universe_digest(universe)
    recorded = directory / UNIVERSE
    if recorded.is_file():
        claimed = json.loads(recorded.read_text(encoding="utf-8")).get("universe_digest")
        if claimed and claimed != digest:
            raise ValueError(
                f"{recorded} claims universe {claimed} but pathways.tsv now gives {digest}. The "
                "universe moved after this artifact was written."
            )
    embedder = _verify_vectors(directory, recorded)
    return Embedded(tuple(keys), vectors, digest, embedder)


#: Encoders whose vectors must never be loaded for analysis again, and why.
RETIRED_EMBEDDERS: dict[str, str] = {
    "FremyCompany/BioLORD-2023": (
        "loaded with max_seq_length 128, so all 1,850 descriptions were truncated and ~45% of "
        "every one was discarded before embedding (docs/status/2026-09-24-embedding-truncation.md)"
    ),
}


def _verify_vectors(directory: Path, recorded: Path) -> dict | None:
    """Check the vectors on disk are the ones recorded, from an encoder still in use.

    The universe digest covers KEYS. It cannot see a description being repaired or an encoder being
    replaced, and both happened on 24 Sep -- so a build could have sat on retired vectors with every
    key check passing.

    Args:
        directory: The versioned directory.
        recorded: Path to ``universe.json``.

    Returns:
        The recorded embedder block, or None when the artifact predates it.

    Raises:
        ValueError: If the vectors do not match their recorded hash, or came from a retired encoder.
    """
    if not recorded.is_file():
        return None
    meta = json.loads(recorded.read_text(encoding="utf-8"))
    embedder = meta.get("embedder")
    if embedder and embedder.get("id") in RETIRED_EMBEDDERS:
        raise ValueError(
            f"{recorded} records the retired encoder {embedder['id']}: "
            f"{RETIRED_EMBEDDERS[embedder['id']]}. Re-embed; do not analyse these vectors."
        )
    claimed = meta.get("embeddings_sha256_16")
    if claimed:
        actual = hashlib.sha256((directory / EMBEDDINGS).read_bytes()).hexdigest()[:16]
        if actual != claimed:
            raise ValueError(
                f"{directory / EMBEDDINGS} hashes to {actual} but {recorded.name} records "
                f"{claimed}. The vectors on disk are not the ones this artifact describes."
            )
    return embedder
