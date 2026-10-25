"""The one place that knows where the scramble trees live. 25 Oct 2026.

The 16 scramble sides (calibration 3001-3010, held-out 4001-4006) are a **permanent cache**, not an
experiment output. They cost about 5 minutes a seed to build, they are deterministic given the
universe and the clustering matrix, and prompts 60, 64 and 65 all consume them. They are never
overwritten and never rebuilt unless the universe digest or the centred matrix changes.

The folder is read-only on disk and excluded from git. `MANIFEST.md` beside the seeds records what
they are and the command that regenerates them.

Every reader resolves a seed through :func:`trees_for` rather than spelling the path, so moving the
cache again means changing :data:`CACHE` and nothing else.
"""

from __future__ import annotations

from pathlib import Path

#: The cache root, relative to the repository.
CACHE = Path("data/cache/scramble_trees_x2_centred")

#: Trees per side, and the universe they belong to.
RUNS = 200
UNIVERSE_DIGEST = "c54319cdfbbe9eb7"
SPACE = "leaves_centred_x2"

#: The matrix the sides were clustered from, and its digest at the time they were built.
MATRIX = Path("data/ontology/v0.4-leaves-x2/vectors_leaves_centred.npy")
MATRIX_SHA256 = "60ed309f1405d9b983b6545d763aaddf708d97c88862b518a4d302d9ac3582ed"

#: Calibration seeds, then held-out. O50s's sets, and :mod:`o50s_build` is the authority on them.
CALIBRATION = tuple(range(3001, 3011))
HELDOUT = tuple(range(4001, 4007))


def trees_for(seed: int, cache: Path = CACHE) -> Path:
    """The directory holding one scramble side's trees.

    Args:
        seed: Scramble seed.
        cache: Cache root, for a relocated or test cache.

    Returns:
        The directory.

    Raises:
        FileNotFoundError: If the side is absent or incomplete. It **raises rather than returning a
            path that does not work**, because a missing side silently read as empty would change a
            calibration without failing.
    """
    where = cache / f"seed{seed:05d}"
    if not where.is_dir():
        raise FileNotFoundError(
            f"{where} is not in the scramble cache; the 16 sides are listed in "
            f"{cache / 'MANIFEST.md'} and rebuilt with the command it records")
    built = len(list(where.glob("row*.npz")))
    if built < RUNS:
        raise FileNotFoundError(
            f"{where} holds {built} trees, not {RUNS}; the cache is incomplete and a short side "
            f"would quietly weaken the calibration")
    return where


def present(cache: Path = CACHE) -> list[int]:
    """Which seeds the cache holds, complete.

    Args:
        cache: Cache root.

    Returns:
        The seeds, ascending.
    """
    found = []
    for where in sorted(cache.glob("seed*")):
        if len(list(where.glob("row*.npz"))) >= RUNS:
            found.append(int(where.name.removeprefix("seed")))
    return found
