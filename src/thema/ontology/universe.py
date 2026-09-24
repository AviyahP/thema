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
    """

    keys: tuple[str, ...]
    vectors: np.ndarray
    digest: str


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
        ValueError: If the stored keys are not exactly the universe. **It raises rather than
            filtering**: silently dropping rows is how a superseded universe goes unnoticed, and
            a mismatch means the artifact needs rebuilding, not patching at read time.
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
    return Embedded(tuple(keys), vectors, digest)
