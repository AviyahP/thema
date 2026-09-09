"""Hierarchical clustering over description embeddings: one distance matrix, three linkages.

No linkage is hard-coded, because choosing one before looking is how a tree acquires a shape
nobody chose. All three are computed from the same condensed distance matrix -- seconds of compute
at this scale -- so the comparison holds the representation fixed and varies only the criterion.

Ward is the presumed default. Its variance criterion resists any one cluster running away, which
is what keeps a theme tree readable at a cut. Average linkage is kept for a specific downstream
reason rather than for completeness: it is what the gene-overlap baseline uses
(``docs/eval-plan.md`` section 2), so a later comparison can hold linkage constant and isolate the
representation instead
of confounding representation with linkage. WHICHEVER LINKAGE WINS HERE MUST THEN BE USED ON BOTH
SIDES OF THAT COMPARISON. Complete linkage is the third opinion, and the one whose failure mode
(tight, size-capped clusters) differs most from average's.

The size distribution is the thing to read first. Ward assumes clusters of broadly similar size,
which biology has no obligation to supply; average linkage's known failure on uneven density is one
enormous cluster plus a tail of singletons. Both failures look like a perfectly ordinary tree from
the outside, and both are obvious in the size distribution, which is why it is reported per linkage
and per cut rather than summarised into a score.

Everything here is numpy and scipy. The encoder lives in ``embed.py`` so this module stays testable
on synthetic vectors, with no model download.
"""

from collections.abc import Sequence

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import pdist

#: The three criteria, computed from one distance matrix and reported side by side.
LINKAGES = ("ward", "average", "complete")

#: Where the trees are cut. Several depths rather than one, because a single cut is a claim and a
#: curve is an observation. The brief's declared working range is 30-50 themes.
DEFAULT_CUTS = (10, 25, 50, 100, 200)


def distances(vectors: np.ndarray) -> np.ndarray:
    """Compute the condensed pairwise Euclidean distance matrix.

    Euclidean is the right metric here only because the vectors are unit length: for unit vectors
    it is a monotone function of cosine similarity, which is the similarity the encoder was trained
    to produce. ``embed.l2_normalize`` is what guarantees that, and this function checks it rather
    than trusting it -- Ward on non-Euclidean input is silently meaningless, not an error.

    Args:
        vectors: A ``(n, dim)`` array of unit vectors.

    Returns:
        The condensed distance matrix, ``n * (n - 1) / 2`` entries.

    Raises:
        ValueError: If fewer than two vectors are given, or if they are not unit length.
    """
    if len(vectors) < 2:
        raise ValueError(f"need at least two vectors to cluster, got {len(vectors)}")
    lengths = np.linalg.norm(vectors, axis=1)
    if not np.allclose(lengths, 1.0, atol=1e-4):
        raise ValueError(
            "vectors are not unit length; run embed.l2_normalize first. Ward on unnormalized "
            "vectors clusters partly by magnitude, which tracks text length, and fails silently"
        )
    return pdist(vectors, metric="euclidean")


def condensed_bytes(count: int, itemsize: int = 8) -> int:
    """How much memory the condensed distance matrix for this many observations needs.

    Reported rather than assumed, because the matrix is the one thing here that grows as the square
    of the input and it is the reason a full run might not fit where a smoke run does.

    Args:
        count: How many observations.
        itemsize: Bytes per entry; scipy's pdist returns float64.

    Returns:
        The size in bytes.
    """
    return count * (count - 1) // 2 * itemsize


def trees(condensed: np.ndarray, methods: Sequence[str] = LINKAGES) -> dict[str, np.ndarray]:
    """Build one linkage per criterion from the same distance matrix.

    scipy accepts a condensed matrix for every method including ``ward``, but for ward, centroid
    and median that is only correct when the distances really are Euclidean. They are here, and
    :func:`distances` refuses anything else, so the shortcut is sound rather than merely permitted.

    Args:
        condensed: The condensed distance matrix.
        methods: Which criteria to compute.

    Returns:
        Method name to its linkage matrix.
    """
    return {method: linkage(condensed, method=method) for method in methods}


def cut(tree: np.ndarray, k: int) -> np.ndarray:
    """Cut a tree into at most k clusters.

    Args:
        tree: A linkage matrix.
        k: The requested number of clusters.

    Returns:
        A cluster label per observation, 1-based, as scipy numbers them.
    """
    return fcluster(tree, t=k, criterion="maxclust")


def size_distribution(labels: np.ndarray) -> dict[str, float]:
    """Describe the cluster sizes a cut produced.

    The shape of this, not its average, is what says whether a linkage behaved. ``largest_share``
    and ``singletons`` are the two numbers that catch the known failures: average linkage on uneven
    density gives one huge cluster and a tail of singletons, and both show here immediately.

    Args:
        labels: Cluster labels from :func:`cut`.

    Returns:
        Cluster count, the min/p10/median/p90/max of the sizes, how many are singletons, and what
        share of all observations the largest cluster holds.
    """
    _values, counts = np.unique(labels, return_counts=True)
    sizes = np.sort(counts)
    marks = [float(sizes[int(q * (len(sizes) - 1))]) for q in (0.0, 0.10, 0.50, 0.90, 1.0)]
    return {
        "clusters": float(len(sizes)),
        "min": marks[0],
        "p10": marks[1],
        "median": marks[2],
        "p90": marks[3],
        "max": marks[4],
        "singletons": float(np.sum(counts == 1)),
        "largest_share": float(counts.max() / counts.sum()),
    }
