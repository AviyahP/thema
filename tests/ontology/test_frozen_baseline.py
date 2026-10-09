"""The frozen baseline cannot change silently.

`data/ontology/frozen/baseline-2026-10-09/` is the reference build (`thema_L_x2`, frozen 9 Oct
2026). Every later change is built in a new directory and compared against it, and if work gets
tangled it is what we revert to. That only works if the bytes are the ones that were measured, so
these tests re-hash every file against `CHECKSUMS.sha256` and fail on any drift -- a changed file, a
deleted one, or a new file slipped in without a checksum.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

BASELINE = Path("data/ontology/frozen/baseline-2026-10-09")
CHECKSUMS = BASELINE / "CHECKSUMS.sha256"

REQUIRED = frozenset({
    "nodes.tsv",
    "members.tsv",
    "edges.tsv",
    "unplaced.tsv",
    "manifest.json",
    "browse.html",
    "match_to_repair.tsv",
    "compare_to_repair.json",
    "excluded_inputs.tsv",
    "floors_L_cal8.json",
    "universe.json",
    "trees_build_log.json",
    "all_verdicts_x2.json",
    "REPORT_x2.md",
    "FROZEN.md",
})


def sha256(path: Path) -> str:
    """Return the hex sha256 of a file, read in chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def recorded() -> dict[str, str]:
    """Return {filename: sha256} as recorded in CHECKSUMS.sha256."""
    entries: dict[str, str] = {}
    for line in CHECKSUMS.read_text().splitlines():
        if not line.strip():
            continue
        checksum, name = line.split(maxsplit=1)
        entries[name.strip().lstrip("*")] = checksum
    return entries


pytestmark = pytest.mark.skipif(
    not CHECKSUMS.exists(),
    reason="the frozen baseline is not present in this checkout",
)


def test_checksum_file_lists_every_required_file() -> None:
    assert REQUIRED <= set(recorded()), (
        "CHECKSUMS.sha256 no longer covers every file the baseline is defined by; "
        f"missing {sorted(REQUIRED - set(recorded()))}"
    )


def test_no_file_is_missing() -> None:
    absent = sorted(name for name in recorded() if not (BASELINE / name).exists())
    assert not absent, f"files recorded in CHECKSUMS.sha256 are gone from the baseline: {absent}"


def test_no_unrecorded_file_was_added() -> None:
    present = {p.name for p in BASELINE.iterdir() if p.is_file()} - {CHECKSUMS.name}
    extra = sorted(present - set(recorded()))
    assert not extra, (
        "files were added to the frozen baseline without a checksum: "
        f"{extra}. The baseline is frozen; put new material in a new directory."
    )


def test_every_file_matches_its_checksum() -> None:
    changed = sorted(
        name
        for name, checksum in recorded().items()
        if (BASELINE / name).exists() and sha256(BASELINE / name) != checksum
    )
    assert not changed, (
        f"the frozen baseline has been modified: {changed}. "
        "It is the reference every later build is compared against -- restore it from git "
        "(git checkout -- data/ontology/frozen/baseline-2026-10-09) rather than re-hashing it."
    )
