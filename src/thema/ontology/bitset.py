"""Membership as fixed-width bit arrays, for the resampling builder.

``recurrent_dag`` asks one question several million times: does this grouping's member set sit
inside that cluster's member set, and by how many extras. Python sets answer it correctly and far
too slowly at ~90,000 groupings judged against 99 runs each. A bit array of ``uint64`` words answers
the same question with three numpy operations and no per-element Python.

Every set here is over the SAME universe -- all ``n`` pathways, in one fixed order -- so a bitset is
comparable with any other without translation. At n = 1,854 that is 30 words, 240 bytes.

``numpy.bitwise_count`` (NumPy >= 2.0) does the population count, so none of the usual lookup-table
or ``unpackbits`` machinery is needed.
"""

from collections.abc import Iterable

import numpy as np

#: Bits per word. ``uint64`` because ``bitwise_count`` is vectorised over it and the word count
#: stays small: one cache line covers eight words.
WORD = 64


def words_for(n: int) -> int:
    """How many words a bitset over ``n`` items needs.

    Args:
        n: Universe size.

    Returns:
        The word count, ``ceil(n / 64)``.
    """
    return (n + WORD - 1) // WORD


def empty(n: int) -> np.ndarray:
    """Build an all-zero bitset over ``n`` items.

    Args:
        n: Universe size.

    Returns:
        A ``uint64`` array of :func:`words_for` length.
    """
    return np.zeros(words_for(n), dtype=np.uint64)


def pack(indices: Iterable[int], n: int) -> np.ndarray:
    """Build a bitset holding the given indices.

    Args:
        indices: Item indices, each ``0 <= i < n``.
        n: Universe size.

    Returns:
        A ``uint64`` bitset.

    Raises:
        IndexError: If an index falls outside the universe. Silently dropping one would make a
            grouping smaller than it is and change its support.
    """
    out = empty(n)
    for index in indices:
        if not 0 <= index < n:
            raise IndexError(f"index {index} outside a universe of {n}")
        out[index // WORD] |= np.uint64(1) << np.uint64(index % WORD)
    return out


def pack_many(groups: Iterable[Iterable[int]], n: int) -> np.ndarray:
    """Pack several index sets into one 2-D bitset matrix.

    Args:
        groups: One iterable of indices per set.
        n: Universe size.

    Returns:
        A ``(len(groups), words_for(n))`` ``uint64`` array, one row per set.
    """
    rows = [pack(g, n) for g in groups]
    return np.vstack(rows) if rows else np.zeros((0, words_for(n)), dtype=np.uint64)


def unpack(bits: np.ndarray) -> list[int]:
    """List the indices a bitset holds, ascending.

    Args:
        bits: A ``uint64`` bitset.

    Returns:
        The set indices.
    """
    out: list[int] = []
    for word_index, word in enumerate(bits):
        value = int(word)
        while value:
            low = value & -value
            out.append(word_index * WORD + low.bit_length() - 1)
            value ^= low
    return out


def count(bits: np.ndarray) -> int:
    """Population count of a bitset, or of every row of a bitset matrix.

    Args:
        bits: A ``uint64`` bitset, or a 2-D array of them.

    Returns:
        The number of set bits. For a 2-D array this is the total across all rows; use
        :func:`count_rows` for a per-row count.
    """
    return int(np.bitwise_count(bits).sum())


def count_rows(bits: np.ndarray) -> np.ndarray:
    """Population count of every row of a bitset matrix.

    Args:
        bits: A ``(rows, words)`` ``uint64`` array.

    Returns:
        An ``int64`` array of per-row counts.
    """
    return np.bitwise_count(bits).sum(axis=1).astype(np.int64)


def contains(outer: np.ndarray, inner: np.ndarray) -> bool:
    """Whether every bit of ``inner`` is set in ``outer``.

    Args:
        outer: The candidate superset.
        inner: The candidate subset.

    Returns:
        True when ``inner`` is a subset of ``outer``, which includes equality.
    """
    return not np.any(inner & ~outer)


def is_strict_subset(inner: np.ndarray, outer: np.ndarray) -> bool:
    """Whether ``inner`` is a subset of ``outer`` and not equal to it.

    The strictness matters for the containment order: the Hasse diagram is built from a strict
    partial order, and equal member sets are merged rather than made parent and child.

    Args:
        inner: The candidate strict subset.
        outer: The candidate strict superset.

    Returns:
        True when ``inner`` is contained in and differs from ``outer``.
    """
    return contains(outer, inner) and bool(np.any(outer & ~inner))


def key(bits: np.ndarray) -> bytes:
    """A hashable, order-stable identity for a bitset.

    Used to deduplicate the grouping pool and to break sort ties reproducibly. ``tobytes`` is exact
    -- two bitsets over the same universe are equal if and only if their bytes are equal -- so this
    is an identity rather than a digest.

    Args:
        bits: A ``uint64`` bitset.

    Returns:
        Its bytes.
    """
    return bits.tobytes()
