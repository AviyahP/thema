"""Turn descriptions into vectors, and put them on the unit sphere before anything clusters them.

This is the only module that imports ``sentence_transformers`` or torch, the same containment
``llm.py`` gives the Anthropic SDK and for the same reason: the arithmetic in ``cluster.py`` must
stay testable without a multi-gigabyte install or a model download. ``tests/test_embed.py`` checks
that containment by walking the sources, so it is machine-checked rather than a convention.

Model choice is D7 in ``docs/brief.md``: BioLORD-2023, whose training objective makes embedding
geometry mirror ontology structure, which is exactly this task. Qwen3-Embedding-0.6B is the named
comparison arm and is not built here.

The normalization is not a detail. For unit vectors ||a - b||^2 = 2 - 2*cos(a, b), so Euclidean
distance becomes a monotone function of cosine similarity, and Ward's variance criterion -- which
is defined on Euclidean distance and on nothing else -- becomes legitimate. Without it the distance
partly reflects vector magnitude, and magnitude tracks text length, so the tree would encode how
long a description is alongside what it says. That is the silent bug the 2024 prototype shipped
with, and it is silent precisely because the output still looks like a tree.
"""

from collections.abc import Sequence

import numpy as np

#: BioLORD-2023. Pinned by revision as well as by name, because an unpinned model is an unpinned
#: input and this project pins every other one.
BIOLORD_MODEL = "FremyCompany/BioLORD-2023"

#: The revision to fetch. Set to a commit sha to freeze the weights; ``main`` is a floating
#: reference and is recorded as such in the ontology summary so a run is never silently unpinned.
BIOLORD_REVISION = "main"

#: The comparison arm named in docs/brief.md D7. A strong general-purpose embedder with no
#: biomedical training, so agreement between the two trees is evidence the structure is in the
#: biology rather than in one encoder's idiosyncrasy.
QWEN_MODEL = "Qwen/Qwen3-Embedding-0.6B"
QWEN_REVISION = "main"

#: BioLORD-2023 is a MPNet-family encoder with a 512-token window. Descriptions are written to
#: 90-150 words, roughly 200 tokens, so nothing truncates -- which matters more than it sounds,
#: because a length-dependent cutoff would reintroduce exactly the length bias normalization and
#: L2 normalization both exist to remove.
MODEL_MAX_TOKENS = 512

#: How many descriptions go to the encoder at once.
BATCH_SIZE = 64


def load_model(model: str = BIOLORD_MODEL, revision: str = BIOLORD_REVISION) -> object:
    """Load the sentence-transformer, downloading it on first use.

    Args:
        model: The model id.
        revision: The revision to pin to.

    Returns:
        The loaded model.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model, revision=revision)


def embed(
    texts: Sequence[str],
    model: str = BIOLORD_MODEL,
    revision: str = BIOLORD_REVISION,
    batch_size: int = BATCH_SIZE,
) -> np.ndarray:
    """Embed descriptions, then put them on the unit sphere.

    Normalization happens here rather than being left to the caller, so there is no code path in
    which an unnormalized matrix reaches a linkage. See the module docstring for why that matters.

    Args:
        texts: The descriptions, in the order their pathways will be reported in.
        model: The model id.
        revision: The revision.
        batch_size: How many to encode at once.

    Returns:
        A ``(len(texts), dim)`` float32 array of unit vectors.

    Raises:
        ValueError: If there is nothing to embed.
    """
    if not texts:
        raise ValueError("nothing to embed")
    encoder = load_model(model, revision)
    vectors = encoder.encode(
        list(texts), batch_size=batch_size, convert_to_numpy=True, show_progress_bar=True
    )
    return l2_normalize(np.asarray(vectors, dtype=np.float32))


def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    """Scale every row to unit length.

    Args:
        vectors: A ``(n, dim)`` array.

    Returns:
        The same array with every row scaled to length 1. A zero row is left alone rather than
        producing a division by zero: it cannot be normalized, and turning it into NaN would
        poison every distance it takes part in instead of just its own.
    """
    lengths = np.linalg.norm(vectors, axis=1, keepdims=True)
    return np.asarray(vectors / np.where(lengths == 0, 1.0, lengths), dtype=np.float32)
