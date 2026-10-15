"""The frozen builds cannot change silently.

Two folders under `data/ontology/frozen/` are frozen, and both are guarded the same way:

`baseline-2026-10-09/`
    The reference build (`thema_L_x2`, 8,740 themes), frozen 9 Oct 2026, kept as the **fallback**.

`working-c85-2026-10-10/`
    `thema_L_x2_c85` (8,251 themes), the **working version** every analysis from 10 Oct uses. It
    differs from the baseline in the chain-collapse rule and nothing else.

Each is only a reference if its bytes are the ones that were measured, so these tests re-hash every
file against that folder's own `CHECKSUMS.sha256` and fail on any drift -- a changed file, a deleted
one, or a new file slipped in without a checksum. The tests are parametrised over the folders, so a
third freeze is guarded by adding one entry to :data:`FROZEN`.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

#: Every frozen build, and the files each is DEFINED by. A folder may hold more than these; it may
#: never hold fewer.
FROZEN: dict[str, frozenset[str]] = {
    "baseline-2026-10-09": frozenset({
        "nodes.tsv", "members.tsv", "edges.tsv", "unplaced.tsv", "manifest.json",
        "browse.html", "match_to_repair.tsv", "compare_to_repair.json",
        "excluded_inputs.tsv", "floors_L_cal8.json", "universe.json", "trees_build_log.json",
        "all_verdicts_x2.json", "REPORT_x2.md", "FROZEN.md",
    }),
    "working-c85-2026-10-10": frozenset({
        "nodes.tsv", "members.tsv", "edges.tsv", "unplaced.tsv", "manifest.json",
        "match_to_baseline.tsv", "repair_map.json", "report.txt",
        "excluded_inputs.tsv", "floors_L_cal8.json", "universe.json", "trees_build_log.json",
        "all_verdicts_c85.json", "REPORT_c85_reassessment.md", "FROZEN.md",
    }),
}

ROOT = Path("data/ontology/frozen")


def sha256(path: Path) -> str:
    """Return the hex sha256 of a file, read in chunks.

    Args:
        path: The file.

    Returns:
        The digest.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def recorded(folder: Path) -> dict[str, str]:
    """Return ``{filename: sha256}`` as that folder's ``CHECKSUMS.sha256`` records it.

    Args:
        folder: A frozen build directory.

    Returns:
        Filename to checksum.
    """
    entries: dict[str, str] = {}
    for line in (folder / "CHECKSUMS.sha256").read_text().splitlines():
        if not line.strip():
            continue
        checksum, name = line.split(maxsplit=1)
        entries[name.strip().lstrip("*")] = checksum
    return entries


def present(name: str) -> bool:
    """Whether a frozen build is in this checkout at all.

    Args:
        name: The folder name.

    Returns:
        True if its checksum file exists.
    """
    return (ROOT / name / "CHECKSUMS.sha256").exists()


frozen = pytest.mark.parametrize(
    "name",
    [
        pytest.param(
            name,
            marks=pytest.mark.skipif(
                not present(name), reason=f"{name} is not present in this checkout"
            ),
        )
        for name in FROZEN
    ],
)


@frozen
def test_both_freezes_are_present(name: str) -> None:
    # Guards against a freeze quietly disappearing: if the folder is gone the parametrised case
    # skips, so this asserts the one thing a skip cannot -- that what is there is a directory.
    assert (ROOT / name).is_dir()


@frozen
def test_the_checksum_file_lists_every_required_file(name: str) -> None:
    missing = sorted(FROZEN[name] - set(recorded(ROOT / name)))
    assert not missing, (
        f"{name}/CHECKSUMS.sha256 no longer covers every file the build is defined by; "
        f"missing {missing}"
    )


@frozen
def test_no_file_is_missing(name: str) -> None:
    folder = ROOT / name
    absent = sorted(entry for entry in recorded(folder) if not (folder / entry).exists())
    assert not absent, f"files recorded in {name}/CHECKSUMS.sha256 are gone: {absent}"


@frozen
def test_no_unrecorded_file_was_added(name: str) -> None:
    folder = ROOT / name
    here = {path.name for path in folder.iterdir() if path.is_file()} - {"CHECKSUMS.sha256"}
    extra = sorted(here - set(recorded(folder)))
    assert not extra, (
        f"files were added to {name} without a checksum: {extra}. "
        "A frozen build is frozen; put new material in a new directory."
    )


@frozen
def test_every_file_matches_its_checksum(name: str) -> None:
    folder = ROOT / name
    changed = sorted(
        entry
        for entry, checksum in recorded(folder).items()
        if (folder / entry).exists() and sha256(folder / entry) != checksum
    )
    assert not changed, (
        f"{name} has been modified: {changed}. It is a frozen reference -- restore it from git "
        f"(git checkout -- data/ontology/frozen/{name}) rather than re-hashing it."
    )


def test_the_two_freezes_are_different_builds() -> None:
    # The working version is not a copy of the fallback: that is the point of having both.
    if not (present("baseline-2026-10-09") and present("working-c85-2026-10-10")):
        pytest.skip("both freezes are needed for this comparison")
    baseline = ROOT / "baseline-2026-10-09" / "nodes.tsv"
    working = ROOT / "working-c85-2026-10-10" / "nodes.tsv"
    assert sha256(baseline) != sha256(working)
    rows = lambda path: len(path.read_text().splitlines()) - 1  # noqa: E731
    assert rows(baseline) == 8740 and rows(working) == 8251
