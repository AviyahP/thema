import hashlib
import re
from pathlib import Path

import pytest

from download_pathway_data import (
    CHUNK_SIZE,
    DEFAULT_DEST,
    GROUPS,
    MANIFEST_NAME,
    REPO_ROOT,
    SOURCES,
    FileReport,
    Source,
    download,
    human_bytes,
    render_versions,
    sha256_file,
)


def test_sources_are_well_formed() -> None:
    names = [s.name for s in SOURCES]
    assert len(names) == len(set(names)), "duplicate destination filenames in SOURCES"
    for source in SOURCES:
        assert source.group in GROUPS, f"{source.name}: unknown group {source.group!r}"
        assert source.url.startswith("https://"), f"{source.name}: non-https url"
        assert source.license, f"{source.name}: missing license"
        is_zip = source.url.endswith(".zip")
        assert (source.unzip_member is not None) == is_zip, (
            f"{source.name}: unzip_member and .zip url must agree"
        )


def test_human_bytes() -> None:
    assert human_bytes(0) == "0 B"
    assert human_bytes(999) == "999 B"
    assert human_bytes(1000) == "1.0 kB"
    assert human_bytes(32_227_785) == "32.2 MB"


def test_sha256_file(tmp_path: Path) -> None:
    payload = b"THEMA" * (CHUNK_SIZE // 2)  # larger than one chunk, so the loop is exercised
    path = tmp_path / "payload.bin"
    path.write_bytes(payload)
    assert sha256_file(path) == hashlib.sha256(payload).hexdigest()


def _report(tmp_path: Path, source: Source, data: bytes) -> FileReport:
    path = tmp_path / source.name
    path.write_bytes(data)
    return FileReport(
        source=source,
        path=path,
        status="downloaded",
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        fetched="2026-08-21T20:15:40Z",
    )


def test_render_versions_is_deterministic(tmp_path: Path) -> None:
    plain = Source("btm", "plain.gmt", "https://example.org/plain.gmt", "CC0", note="A note.")
    zipped = Source(
        "reactome",
        "zipped.gmt",
        "https://example.org/zipped.gmt.zip",
        "CC0",
        unzip_member="zipped.gmt",
    )
    reports = [_report(tmp_path, plain, b"a\tb\n"), _report(tmp_path, zipped, b"c\td\n")]

    kwargs = {"generated": "2026-08-21T20:15:40Z", "reactome_release": "97", "dest_dir": tmp_path}
    first = render_versions(reports, **kwargs)
    assert render_versions(reports, **kwargs) == first, "manifest rendering is not deterministic"

    stanzas = first.split("\n\n")[1:]
    parsed = [
        dict(line.split(": ", 1) for line in s.splitlines() if not line.startswith((" ", "#")))
        for s in stanzas
        if s.strip() and not s.startswith("#")
    ]
    assert {p["file"] for p in parsed} == {"plain.gmt", "zipped.gmt"}
    for entry in parsed:
        for key in ("group", "url", "license", "fetched", "bytes", "sha256"):
            assert entry.get(key), f"{entry['file']}: missing {key}"
    zipped_entry = next(p for p in parsed if p["file"] == "zipped.gmt")
    assert zipped_entry["extracted_from"] == "zipped.gmt.zip (member: zipped.gmt)"


class _FlakyResponse:
    """Yields one chunk, then dies mid-body the way a reset connection does."""

    headers = {"Content-Length": "999999"}
    status = 200

    def __init__(self) -> None:
        self._served = False

    def read(self, _size: int = -1) -> bytes:
        if self._served:
            raise OSError("connection reset by peer")
        self._served = True
        return b"partial"

    def __enter__(self) -> "_FlakyResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


def test_download_removes_partial_on_failure(tmp_path: Path, monkeypatch) -> None:
    import download_pathway_data as mod

    monkeypatch.setattr(mod, "_open_url", lambda *_args, **_kwargs: _FlakyResponse())
    monkeypatch.setattr(mod.time, "sleep", lambda _s: None)

    dest = tmp_path / "go-basic.obo"
    with pytest.raises(OSError, match="failed after 2 attempts"):
        download("https://example.org/go-basic.obo", dest, retries=2, progress=False)

    assert not dest.exists(), "a failed download must not leave a final file"
    assert list(tmp_path.glob("*.part")) == [], "a failed download must not leave a .part file"


# DATA_LICENSE.md reproduces every file's size and sha256, because data/raw/ (and so VERSIONS.txt)
# is gitignored and the committed licence file is therefore the only record of the frozen release.
# The two can drift once a source release is bumped, so cross-check them whenever raw data is
# present. On a fresh clone it is not, hence the skip.
_LICENSE_ROW = re.compile(r"^\| `([^`]+)` \| ([\d,]+) \| `([0-9a-f]{64})` \|$", re.MULTILINE)


def _parse_manifest(path: Path) -> dict[str, tuple[int, str]]:
    entries: dict[str, tuple[int, str]] = {}
    for stanza in path.read_text(encoding="utf-8").split("\n\n")[1:]:
        lines = [ln for ln in stanza.splitlines() if ln and not ln.startswith(("#", " "))]
        fields = dict(ln.split(": ", 1) for ln in lines if ": " in ln)
        if "file" in fields:
            entries[fields["file"]] = (int(fields["bytes"]), fields["sha256"])
    return entries


def test_data_license_matches_manifest() -> None:
    manifest_path = DEFAULT_DEST / MANIFEST_NAME
    if not manifest_path.is_file():
        pytest.skip(f"no {manifest_path}; run scripts/download_pathway_data.py to check this")

    manifest = _parse_manifest(manifest_path)
    assert manifest, f"{manifest_path} parsed to no entries"

    documented = {
        name: (int(size.replace(",", "")), digest)
        for name, size, digest in _LICENSE_ROW.findall(
            (REPO_ROOT / "DATA_LICENSE.md").read_text(encoding="utf-8")
        )
    }

    assert set(documented) == set(manifest), (
        "DATA_LICENSE.md and VERSIONS.txt cover different files; "
        f"only in DATA_LICENSE.md: {sorted(set(documented) - set(manifest))}, "
        f"only in VERSIONS.txt: {sorted(set(manifest) - set(documented))}"
    )
    for name, expected in manifest.items():
        assert documented[name] == expected, (
            f"{name}: DATA_LICENSE.md says {documented[name]}, VERSIONS.txt says {expected}"
        )
