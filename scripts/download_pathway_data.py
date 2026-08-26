"""Download THEMA's source pathway data into ``data/raw/``.

Fetches Reactome, Gene Ontology, MSigDB and BTM gene sets, unpacks the archived ones, and writes
a ``VERSIONS.txt`` manifest recording the URL, fetch date, size and sha256 of every artifact.

Re-runs are idempotent: files that already exist are hashed and kept rather than re-fetched, and
the manifest is regenerated in full from whatever is on disk. Uses only the standard library --
``urllib`` with an explicit User-Agent, because the default ``Python-urllib/3.x`` agent is
rejected with HTTP 403 by both reactome.org and release.geneontology.org.
"""

import argparse
import gzip
import hashlib
import http.client
import os
import shutil
import sys
import time
import urllib.error
import urllib.request
import zipfile
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

USER_AGENT = "thema-data-downloader/0.1 (https://github.com/aviyahp/thema)"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEST = REPO_ROOT / "data" / "raw"
MANIFEST_NAME = "VERSIONS.txt"
CHUNK_SIZE = 1 << 16
DEFAULT_TIMEOUT = 60.0
RETRIES = 12  # resumed attempts are cheap; large files are cut short every ~28 MiB in practice
PROGRESS_MIN_BYTES = 4_000_000
PROGRESS_INTERVAL_S = 0.1

REACTOME_BASE = "https://reactome.org/download/current"
REACTOME_VERSION_URL = "https://reactome.org/ContentService/data/database/version"
GO_RELEASE = "2026-08-05"
GO_BASE = f"https://release.geneontology.org/{GO_RELEASE}/ontology"
MSIGDB_RELEASE = "2026.1.Hs"
MSIGDB_BASE = f"https://data.broadinstitute.org/gsea-msigdb/msigdb/release/{MSIGDB_RELEASE}"
BTM_COMMIT = "94d5288af08320670e1337191173649a864602f8"
BTM_BASE = f"https://raw.githubusercontent.com/shuzhao-li/BTM/{BTM_COMMIT}/BTM/datasets"
HGNC_RELEASE = "2026-07-07"
# The doubled `archive/archive` segment is real; the single-segment path 404s.
HGNC_BASE = (
    "https://storage.googleapis.com/public-download-files/hgnc/archive/archive/quarterly/tsv"
)

LICENSE_REACTOME = "CC0 1.0 - Reactome (reactome.org)"
LICENSE_GO = "CC BY 4.0 - Gene Ontology Consortium (geneontology.org)"
LICENSE_MSIGDB = "CC BY 4.0 - Broad Institute / UC San Diego (gsea-msigdb.org)"
LICENSE_BTM = "Li et al. 2014, Nat Immunol 15:195 - public (github.com/shuzhao-li/BTM)"
LICENSE_HGNC = "CC0 1.0 - HGNC / EMBL-EBI (genenames.org)"

GROUPS: tuple[str, ...] = ("reactome", "go", "msigdb", "btm", "hgnc")

Status = Literal["downloaded", "skipped", "failed"]


@dataclass(frozen=True, slots=True)
class Source:
    """One file to fetch into the raw data directory.

    Attributes:
        group: Selector name used by ``--only`` (reactome, go, msigdb, btm).
        name: Final on-disk filename; this is what skip-if-exists checks.
        url: Download URL. For archives this is the archive, not the member.
        license: Short license and attribution string, copied into the manifest.
        unzip_member: If set, ``url`` is a zip and this member is extracted to ``name``.
        expected_bytes: Advisory size of the final file; a mismatch warns, never fails.
        optional: True for sources fetched only when explicitly enabled.
        note: Free-text provenance note recorded in the manifest.
    """

    group: str
    name: str
    url: str
    license: str
    unzip_member: str | None = None
    expected_bytes: int | None = None
    optional: bool = False
    note: str = ""

    @property
    def archive_name(self) -> str:
        """Filename of the downloaded archive; only meaningful when unzipping."""
        return self.url.rsplit("/", 1)[-1]


SOURCES: tuple[Source, ...] = (
    Source(
        group="reactome",
        name="reactome_release.txt",
        url=REACTOME_VERSION_URL,
        license=LICENSE_REACTOME,
        note="Reactome release number resolved from ContentService (expected: 97).",
    ),
    Source(
        group="reactome",
        name="ReactomePathways.txt",
        url=f"{REACTOME_BASE}/ReactomePathways.txt",
        license=LICENSE_REACTOME,
        note="TSV: stable id / pathway name / species.",
    ),
    Source(
        group="reactome",
        name="ReactomePathwaysRelation.txt",
        url=f"{REACTOME_BASE}/ReactomePathwaysRelation.txt",
        license=LICENSE_REACTOME,
        note="TSV: parent id / child id - the curated pathway hierarchy.",
    ),
    Source(
        group="reactome",
        name="ReactomePathways.gmt",
        url=f"{REACTOME_BASE}/ReactomePathways.gmt.zip",
        license=LICENSE_REACTOME,
        unzip_member="ReactomePathways.gmt",
        expected_bytes=1_032_186,
        note="Human pathway gene sets; archive deleted after extraction.",
    ),
    Source(
        group="reactome",
        name="NCBI2Reactome_All_Levels.txt",
        url=f"{REACTOME_BASE}/NCBI2Reactome_All_Levels.txt",
        license=LICENSE_REACTOME,
        note="Entrez gene id / pathway id / URL / pathway name / evidence code / species, at every "
        "level of the hierarchy. Reactome's identifier-level membership: the GMT names members by "
        "display name, which is not unique across entities, so this is the only export that "
        "distinguishes human PBRM1 from influenza PB1. Primary identity source because HGNC's "
        "entrez_id is unique.",
    ),
    Source(
        group="reactome",
        name="Ensembl2Reactome_All_Levels.txt",
        url=f"{REACTOME_BASE}/Ensembl2Reactome_All_Levels.txt",
        license=LICENSE_REACTOME,
        note="Same layout keyed by Ensembl id. Mixed granularity despite the name - ENSG, ENSP and "
        "ENST are all present, so gene-level use must filter to ENSG. Held as a coverage "
        "cross-check on the NCBI export, not as a second source of truth: HGNC's ensembl_gene_id "
        "is not unique.",
    ),
    Source(
        group="reactome",
        name="pathway2summation.txt",
        url=f"{REACTOME_BASE}/pathway2summation.txt",
        license=LICENSE_REACTOME,
        note="Curated pathway descriptions; TSV: Identifier / Name / Summation.",
    ),
    Source(
        group="go",
        name="go-basic.obo",
        url=f"{GO_BASE}/go-basic.obo",
        license=LICENSE_GO,
        expected_bytes=32_227_785,
        note=f"Pinned release directory {GO_RELEASE}, not the floating current alias; "
        "the file's own data-version differs from the directory date.",
    ),
    Source(
        group="msigdb",
        name=f"h.all.v{MSIGDB_RELEASE}.symbols.gmt",
        url=f"{MSIGDB_BASE}/h.all.v{MSIGDB_RELEASE}.symbols.gmt",
        license=LICENSE_MSIGDB,
        expected_bytes=48_686,
        note="Hallmark collection, gene symbols.",
    ),
    Source(
        group="msigdb",
        name=f"c5.go.bp.v{MSIGDB_RELEASE}.symbols.gmt",
        url=f"{MSIGDB_BASE}/c5.go.bp.v{MSIGDB_RELEASE}.symbols.gmt",
        license=LICENSE_MSIGDB,
        expected_bytes=4_872_550,
        note="C5 GO:BP collection, gene symbols.",
    ),
    Source(
        group="msigdb",
        name=f"genesets_v{MSIGDB_RELEASE}.json",
        url=f"{MSIGDB_BASE}/genesets_v{MSIGDB_RELEASE}.json",
        license=LICENSE_MSIGDB,
        expected_bytes=8_545,
        note="Release manifest with collection-level descriptions.",
    ),
    Source(
        group="msigdb",
        name=f"h.all.v{MSIGDB_RELEASE}.json",
        url=f"{MSIGDB_BASE}/h.all.v{MSIGDB_RELEASE}.json",
        license=LICENSE_MSIGDB,
        expected_bytes=73_082,
        note="Per-set metadata: systematicName, pmid, exactSource, msigdbURL. No prose.",
    ),
    Source(
        group="msigdb",
        name=f"c5.go.bp.v{MSIGDB_RELEASE}.json",
        url=f"{MSIGDB_BASE}/c5.go.bp.v{MSIGDB_RELEASE}.json",
        license=LICENSE_MSIGDB,
        expected_bytes=8_127_866,
        note="Per-set metadata; exactSource carries the GO term id for joining to go-basic.obo.",
    ),
    Source(
        group="msigdb",
        name=f"msigdb_v{MSIGDB_RELEASE}.xml",
        url=f"{MSIGDB_BASE}/msigdb_v{MSIGDB_RELEASE}.xml.zip",
        license=LICENSE_MSIGDB,
        unzip_member=f"msigdb_v{MSIGDB_RELEASE}.xml",
        expected_bytes=220_619_850,
        note="Only source of per-gene-set prose (descriptionBrief/descriptionFull); covers all "
        "collections. 65 MB zipped, 221 MB extracted. Disable with --skip-msigdb-xml.",
    ),
    Source(
        group="btm",
        name="BTM_for_GSEA_20131008.gmt",
        url=f"{BTM_BASE}/BTM_for_GSEA_20131008.gmt",
        license=LICENSE_BTM,
        expected_bytes=68_196,
        note=f"Blood transcription modules, pinned to commit {BTM_COMMIT}. Chosen over the "
        "release zip and the tmod R package: maintained by the paper's first author, plain "
        "GMT, no registration, content-addressable by commit.",
    ),
    Source(
        group="hgnc",
        name=f"hgnc_complete_set_{HGNC_RELEASE}.txt",
        url=f"{HGNC_BASE}/hgnc_complete_set_{HGNC_RELEASE}.txt",
        license=LICENSE_HGNC,
        expected_bytes=16_913_890,
        note=f"HGNC nomenclature, pinned to the dated quarterly {HGNC_RELEASE} rather than the "
        "floating tsv/tsv/hgnc_complete_set.txt, which carries no version identifier. 54 "
        "columns; holds Approved records only. prev_symbol/alias_symbol are pipe-delimited "
        "and the date columns drive the derived era lens in src/thema/data/genes.py.",
    ),
    Source(
        group="hgnc",
        name=f"withdrawn_{HGNC_RELEASE}.txt",
        url=f"{HGNC_BASE}/withdrawn_{HGNC_RELEASE}.txt",
        license=LICENSE_HGNC,
        expected_bytes=258_931,
        note="Withdrawn and merged HGNC ids, which are absent from the complete set. The "
        "MERGED_INTO_REPORT(S) column is the merge map used to carry a retired id forward to "
        f"its current one. {HGNC_RELEASE} is the most recent quarterly publishing both files: "
        "withdrawn_2026-07-03.txt does not exist.",
    ),
)


@dataclass(frozen=True, slots=True)
class FileReport:
    """Outcome for one source after a run.

    Attributes:
        source: The spec entry this report describes.
        path: Absolute path to the final file.
        status: What happened to this source during the run.
        size_bytes: Size of the file on disk, or 0 on failure.
        sha256: Hex digest of the file on disk, or the empty string on failure.
        fetched: ISO-8601 UTC timestamp taken from the file's mtime.
        elapsed_s: Wall-clock seconds spent downloading; 0.0 when skipped.
        extra: Additional manifest fields, such as the .obo data-version.
        warning: Non-fatal problem, such as a size differing from the spec.
        error: Failure message when status is "failed".
    """

    source: Source
    path: Path
    status: Status
    size_bytes: int = 0
    sha256: str = ""
    fetched: str = ""
    elapsed_s: float = 0.0
    extra: tuple[tuple[str, str], ...] = ()
    warning: str | None = None
    error: str | None = None


def human_bytes(n: int) -> str:
    """Format a byte count in decimal units, matching the sizes sources publish."""
    if n < 1000:
        return f"{n} B"
    value = float(n)
    for unit in ("kB", "MB", "GB", "TB"):
        value /= 1000.0
        if value < 1000.0:
            return f"{value:.1f} {unit}"
    return f"{value:.1f} PB"


def sha256_file(path: Path, chunk_size: int = CHUNK_SIZE) -> str:
    """Return the hex sha256 digest of a file, read in chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _iso_utc(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _obo_data_version(path: Path, max_lines: int = 40) -> str | None:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for _, line in zip(range(max_lines), handle, strict=False):
            if line.startswith("data-version:"):
                return line.split(":", 1)[1].strip()
    return None


def _extra_fields(source: Source, path: Path) -> tuple[tuple[str, str], ...]:
    if source.name.endswith(".obo"):
        version = _obo_data_version(path)
        return (("data_version", version),) if version else ()
    return ()


def _read_release_number(dest_dir: Path) -> str | None:
    path = dest_dir / "reactome_release.txt"
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    return text or None


def _open_url(
    url: str,
    timeout: float,
    extra_headers: dict[str, str] | None = None,
) -> http.client.HTTPResponse:
    headers = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"} | (extra_headers or {})
    request = urllib.request.Request(url, headers=headers)  # noqa: S310
    return urllib.request.urlopen(request, timeout=timeout)  # noqa: S310


def _full_size(response: http.client.HTTPResponse, offset: int) -> int | None:
    content_range = response.headers.get("Content-Range")
    if content_range and "/" in content_range:
        total = content_range.rsplit("/", 1)[1].strip()
        if total.isdigit():
            return int(total)
    header = response.headers.get("Content-Length")
    if header is not None and header.isdigit():
        return int(header) + offset
    return None


_last_progress: float = 0.0


def _render_progress(name: str, done: int, total: int | None, started: float) -> None:
    global _last_progress
    now = time.monotonic()
    finished = total is not None and done >= total
    if not finished and now - _last_progress < PROGRESS_INTERVAL_S:
        return
    _last_progress = now
    elapsed = max(now - started, 1e-6)
    rate = human_bytes(int(done / elapsed))
    columns = shutil.get_terminal_size((80, 24)).columns
    if total:
        pct = done / total
        head = f"{name}  "
        tail = f" {pct * 100:3.0f}%  {human_bytes(done)} / {human_bytes(total)}  {rate}/s"
        width = columns - len(head) - len(tail) - 3
        if width >= 10:
            filled = int(width * pct)
            line = f"{head}[{'#' * filled}{'.' * (width - filled)}]{tail}"
        else:
            line = f"{head}{tail.lstrip()}"
    else:
        line = f"{name}  {human_bytes(done)}  {rate}/s"
    sys.stderr.write("\r" + line[: columns - 1].ljust(columns - 1))
    sys.stderr.flush()


def _clear_progress() -> None:
    columns = shutil.get_terminal_size((80, 24)).columns
    sys.stderr.write("\r" + " " * (columns - 1) + "\r")
    sys.stderr.flush()


def download(
    url: str,
    dest: Path,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = RETRIES,
    progress: bool = True,
) -> int:
    """Download a URL to ``dest`` atomically and return the number of bytes written.

    Requests a gzip body and decompresses it as it streams, which is what makes reactome.org's
    ~100 MB and ~450 MB mapping exports transferable at all; a truncated gzip stream raises
    ``EOFError`` and is retried rather than silently accepted. Streams to a sibling ``.part`` file
    and renames it into place only after the body length matches what the server advertised, so an
    interrupted or truncated transfer never leaves a
    file that skip-if-exists would later accept. When a transfer is cut short and the server
    supports ranges, the retry resumes from the byte offset reached, guarded by ``If-Range`` on
    the ETag or Last-Modified value so a changed file restarts cleanly instead of splicing two
    releases together.

    Args:
        url: The URL to fetch.
        dest: Final path to write; the temporary file is created alongside it.
        timeout: Per-request socket timeout in seconds.
        retries: Number of attempts before giving up.
        progress: Whether to draw a progress indicator on stderr.

    Returns:
        The number of bytes written to ``dest``.

    Raises:
        OSError: If every attempt fails, or the body is shorter than the advertised length.
    """
    tmp = dest.with_name(dest.name + ".part")
    tmp_gz = dest.with_name(dest.name + ".part.gz")
    tmp.unlink(missing_ok=True)
    tmp_gz.unlink(missing_ok=True)
    last_error: Exception | None = None
    validator: str | None = None
    have = 0
    for attempt in range(1, retries + 1):
        started = time.monotonic()
        shown = False
        try:
            extra: dict[str, str] = {}
            if have and validator:
                extra = {"Range": f"bytes={have}-", "If-Range": validator}
            with _open_url(url, timeout, extra) as response:
                # A gzip body is decompressed as it streams. Byte offsets then refer to the
                # decompressed file while Range would refer to compressed bytes, so a gzip
                # transfer is never resumed -- it restarts, which is also what these servers
                # force by ignoring Range. Content-Length is likewise the compressed length,
                # so it must not be used as the truncation check.
                gzipped = "gzip" in response.headers.get("Content-Encoding", "").lower()
                resuming = not gzipped and getattr(response, "status", 200) == 206
                if not resuming:
                    have = 0
                if validator is None and not gzipped:
                    validator = response.headers.get("ETag") or response.headers.get(
                        "Last-Modified"
                    )
                total = None if gzipped else _full_size(response, have)
                # The compressed body is written to disk as it arrives and decompressed only
                # afterwards. Decompressing inside the read loop makes a slow decompress and a
                # stalled socket the same failure, which is what defeated the 504 MB Ensembl
                # export: the connection was dropping mid-transfer every time.
                target = tmp_gz if gzipped else tmp
                show = progress and sys.stderr.isatty()
                if show and total is not None and total < PROGRESS_MIN_BYTES:
                    show = False
                with target.open("ab" if resuming else "wb") as handle:
                    if resuming:
                        handle.truncate(have)
                    while chunk := response.read(CHUNK_SIZE):
                        handle.write(chunk)
                        have += len(chunk)
                        if show:
                            shown = True
                            _render_progress(dest.name, have, total, started)
                    handle.flush()
                    os.fsync(handle.fileno())
            if gzipped:
                # A truncated gzip stream raises EOFError here rather than yielding a short
                # file, which is the only completeness check available without Content-Length.
                with gzip.open(tmp_gz, "rb") as src, tmp.open("wb") as handle:
                    shutil.copyfileobj(src, handle, CHUNK_SIZE)
                    handle.flush()
                    os.fsync(handle.fileno())
                tmp_gz.unlink(missing_ok=True)
                have = tmp.stat().st_size
            if shown:
                _clear_progress()
            if total is not None and have != total:
                message = f"truncated download: {have} of {total} bytes"
                raise OSError(message)
            tmp.replace(dest)
        except (urllib.error.URLError, http.client.HTTPException, OSError, EOFError) as exc:
            if shown:
                _clear_progress()
            last_error = exc
            tmp_gz.unlink(missing_ok=True)
            if validator is None or not tmp.exists():
                have = 0
                tmp.unlink(missing_ok=True)
            if attempt < retries:
                time.sleep(min(2**attempt, 10))
        except BaseException:
            tmp.unlink(missing_ok=True)
            tmp_gz.unlink(missing_ok=True)
            raise
        else:
            return have
    tmp.unlink(missing_ok=True)
    tmp_gz.unlink(missing_ok=True)
    message = f"failed after {retries} attempts: {url} ({type(last_error).__name__}: {last_error})"
    raise OSError(message) from last_error


def extract_member(archive: Path, member: str, dest: Path) -> int:
    """Extract a single named member from a zip archive to ``dest``, atomically.

    Args:
        archive: Path to the zip file.
        member: Name of the member to extract.
        dest: Final path for the extracted member.

    Returns:
        The number of bytes written to ``dest``.

    Raises:
        KeyError: If the archive does not contain ``member``.
    """
    tmp = dest.with_name(dest.name + ".part")
    try:
        with zipfile.ZipFile(archive) as zf:
            names = zf.namelist()
            if member not in names:
                message = f"{archive.name} has no member {member!r}; contains {names}"
                raise KeyError(message)
            with zf.open(member) as src, tmp.open("wb") as handle:
                shutil.copyfileobj(src, handle, CHUNK_SIZE)
                handle.flush()
                os.fsync(handle.fileno())
        written = tmp.stat().st_size
        tmp.replace(dest)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return written


def _report_for_existing(source: Source, path: Path, status: Status, elapsed: float) -> FileReport:
    stat = path.stat()
    warning = None
    if source.expected_bytes is not None and stat.st_size != source.expected_bytes:
        warning = f"{stat.st_size:,} bytes on disk, spec says {source.expected_bytes:,}"
    return FileReport(
        source=source,
        path=path,
        status=status,
        size_bytes=stat.st_size,
        sha256=sha256_file(path),
        fetched=_iso_utc(stat.st_mtime),
        elapsed_s=elapsed,
        extra=_extra_fields(source, path),
        warning=warning,
    )


def fetch_source(
    source: Source,
    dest_dir: Path,
    *,
    force: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
    progress: bool = True,
) -> FileReport:
    """Fetch one source into ``dest_dir``, skipping it if the final file already exists.

    Existence is checked on the final artifact, never on the archive an artifact was extracted
    from; a zero-byte file counts as missing. Skipped files are still hashed, so the manifest is
    complete regardless of what was downloaded this run.

    Args:
        source: The spec entry to fetch.
        dest_dir: Directory to write into.
        force: Re-download even when the final file already exists.
        timeout: Per-request socket timeout in seconds.
        progress: Whether to draw a progress indicator on stderr.

    Returns:
        A report describing what happened, suitable for the manifest and summary table.
    """
    final = dest_dir / source.name
    if not force and final.is_file() and final.stat().st_size > 0:
        return _report_for_existing(source, final, "skipped", 0.0)

    started = time.monotonic()
    try:
        if source.unzip_member is None:
            download(source.url, final, timeout=timeout, progress=progress)
        else:
            archive = dest_dir / source.archive_name
            try:
                download(source.url, archive, timeout=timeout, progress=progress)
                extract_member(archive, source.unzip_member, final)
            finally:
                archive.unlink(missing_ok=True)
    except (urllib.error.URLError, http.client.HTTPException, OSError, KeyError) as exc:
        return FileReport(source=source, path=final, status="failed", error=str(exc))
    return _report_for_existing(source, final, "downloaded", time.monotonic() - started)


def select_sources(
    groups: Sequence[str],
    *,
    include_msigdb_xml: bool,
    dest_dir: Path,
) -> tuple[tuple[Source, ...], tuple[Source, ...]]:
    """Split the source table into what to fetch and what to merely record.

    Selection governs downloading only. Anything excluded but already present on disk still
    belongs in the manifest, so ``--only go`` does not truncate ``VERSIONS.txt``.

    Args:
        groups: Group names to fetch.
        include_msigdb_xml: Whether optional sources are in the fetch set.
        dest_dir: Directory checked for already-present excluded files.

    Returns:
        A ``(to_fetch, manifest_only)`` pair of source tuples.
    """
    to_fetch = tuple(
        s for s in SOURCES if s.group in groups and (include_msigdb_xml or not s.optional)
    )
    manifest_only = tuple(
        s for s in SOURCES if s not in to_fetch and (dest_dir / s.name).is_file()
    )
    return to_fetch, manifest_only


def _stanza(report: FileReport) -> str:
    source = report.source
    lines = [f"file: {source.name}", f"group: {source.group}", f"url: {source.url}"]
    if source.unzip_member is not None:
        lines.append(f"extracted_from: {source.archive_name} (member: {source.unzip_member})")
    lines.append(f"license: {source.license}")
    lines.append(f"fetched: {report.fetched}")
    lines.append(f"bytes: {report.size_bytes}")
    lines.append(f"sha256: {report.sha256}")
    lines.extend(f"{key}: {value}" for key, value in report.extra)
    if source.note:
        wrapped = _wrap_note(source.note)
        lines.append(f"note: {wrapped}")
    return "\n".join(lines)


def _wrap_note(note: str, width: int = 96) -> str:
    words = note.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return "\n  ".join(lines)


def render_versions(
    reports: Sequence[FileReport],
    *,
    generated: str,
    reactome_release: str | None,
    dest_dir: Path,
) -> str:
    """Render the manifest text for a set of reports.

    The result is a pure function of the source table and the files on disk, so an all-skipped
    re-run produces a complete and byte-identical manifest.

    Args:
        reports: Reports for every source whose file is present on disk.
        generated: ISO-8601 UTC timestamp for the header.
        reactome_release: Resolved Reactome release number, if known.
        dest_dir: Directory scanned for files not covered by the source table.

    Returns:
        The full text of ``VERSIONS.txt``, newline-terminated.
    """
    header = [
        "# THEMA raw data manifest - generated by scripts/download_pathway_data.py",
        f"# generated: {generated}",
        f"# reactome_release: {reactome_release or 'unknown'}",
        f"# go_release_directory: {GO_RELEASE}",
        f"# msigdb_release: {MSIGDB_RELEASE}",
        f"# btm_commit: {BTM_COMMIT}",
        f"# hgnc_release: {HGNC_RELEASE}",
        "#",
        "# One stanza per file, blank-line separated. `fetched` is the file's mtime in UTC.",
        "# Regenerated from disk on every run - safe to delete; re-run the script to rebuild.",
    ]
    body = [_stanza(r) for r in reports if r.status != "failed"]

    known = {s.name for s in SOURCES} | {MANIFEST_NAME}
    unlisted = sorted(p.name for p in dest_dir.iterdir() if p.is_file() and p.name not in known)
    footer = [f"# unlisted files present: {', '.join(unlisted)}"] if unlisted else []

    return "\n".join(["\n".join(header), "", "\n\n".join(body), *footer]) + "\n"


def render_source_table(sources: Sequence[Source]) -> str:
    """Render the source table for ``--list``, without touching the network."""
    headers = ("GROUP", "FILE", "SIZE", "LICENSE")
    rows = [
        (
            s.group,
            s.name,
            human_bytes(s.expected_bytes) if s.expected_bytes else "-",
            s.license,
        )
        for s in sources
    ]
    return _table(headers, rows, align="<<><")


def render_summary(reports: Sequence[FileReport], *, elapsed_s: float, manifest: Path) -> str:
    """Render the end-of-run summary table, counts, and any warnings."""
    headers = ("GROUP", "FILE", "STATUS", "SIZE", "SHA256", "TIME")
    rows = [
        (
            r.source.group,
            r.source.name,
            r.status,
            human_bytes(r.size_bytes) if r.size_bytes else "-",
            r.sha256[:12] or "-",
            f"{r.elapsed_s:.1f}s" if r.elapsed_s else "-",
        )
        for r in reports
    ]
    lines = [_table(headers, rows, align="<<<>><")]

    total = sum(r.size_bytes for r in reports)
    counts = {status: sum(1 for r in reports if r.status == status) for status in
              ("downloaded", "skipped", "failed")}
    lines.append(
        f"{len(reports)} files, {human_bytes(total)} - "
        f"{counts['downloaded']} downloaded, {counts['skipped']} skipped, "
        f"{counts['failed']} failed in {elapsed_s:.1f}s"
    )
    lines.append(f"manifest: {manifest}")

    warnings = [(r.source.name, r.warning) for r in reports if r.warning]
    if warnings:
        lines.append("")
        lines.append("warnings:")
        lines.extend(f"  ! {name}: {text}" for name, text in warnings)

    errors = [(r.source.name, r.error) for r in reports if r.error]
    if errors:
        lines.append("")
        lines.append("errors:")
        lines.extend(f"  x {name}: {text}" for name, text in errors)

    return "\n".join(lines)


def _table(headers: Sequence[str], rows: Sequence[Sequence[str]], align: str) -> str:
    if not rows:
        return "(no files)"
    widths = [max(len(h), *(len(row[i]) for row in rows)) for i, h in enumerate(headers)]
    rule = "  ".join("-" * w for w in widths)
    out = ["  ".join(f"{h:<{w}}" for h, w in zip(headers, widths, strict=True)), rule]
    out.extend(
        "  ".join(
            f"{cell:{a}{w}}" for cell, a, w in zip(row, align, widths, strict=True)
        ).rstrip()
        for row in rows
    )
    return "\n".join(out)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="download_pathway_data.py",
        description="Download THEMA's source pathway data into data/raw/.",
        epilog="Re-runs are idempotent: existing files are hashed and kept, not re-fetched.",
    )
    parser.add_argument(
        "--dest", type=Path, default=DEFAULT_DEST,
        help="destination directory (default: %(default)s)",
    )
    parser.add_argument(
        "--only", action="append", choices=GROUPS, metavar="GROUP", dest="groups",
        help=f"fetch only this group; repeatable. one of: {', '.join(GROUPS)}",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="re-download selected files even if they already exist",
    )
    parser.add_argument(
        "--skip-msigdb-xml", action="store_true",
        help=f"skip msigdb_v{MSIGDB_RELEASE}.xml.zip (65 MB zipped, 221 MB extracted; the only "
             "source of per-gene-set prose descriptions)",
    )
    parser.add_argument(
        "--list", action="store_true", dest="list_only",
        help="print the source table and exit without touching the network",
    )
    parser.add_argument(
        "--timeout", type=float, default=DEFAULT_TIMEOUT, metavar="SECONDS",
        help="per-request socket timeout (default: %(default)s)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Download every selected source, write the manifest, and print a summary table."""
    args = parse_args(argv)
    groups = tuple(args.groups) if args.groups else GROUPS
    include_xml = not args.skip_msigdb_xml

    if args.list_only:
        selected = [
            s for s in SOURCES if s.group in groups and (include_xml or not s.optional)
        ]
        print(render_source_table(selected))
        return 0

    dest_dir: Path = args.dest
    dest_dir.mkdir(parents=True, exist_ok=True)
    to_fetch, manifest_only = select_sources(
        groups, include_msigdb_xml=include_xml, dest_dir=dest_dir
    )

    started = time.monotonic()
    reports: list[FileReport] = []
    for i, source in enumerate(to_fetch, start=1):
        print(f"[{i}/{len(to_fetch)}] {source.name}", file=sys.stderr)
        reports.append(
            fetch_source(source, dest_dir, force=args.force, timeout=args.timeout)
        )
    reports.extend(
        _report_for_existing(s, dest_dir / s.name, "skipped", 0.0) for s in manifest_only
    )
    elapsed = time.monotonic() - started

    # Order by the source table, not by what happened to be selected, so the manifest stays a
    # pure function of (SOURCES, files on disk) rather than of the --only flags used this run.
    order = {source: i for i, source in enumerate(SOURCES)}
    reports.sort(key=lambda r: order[r.source])

    manifest = dest_dir / MANIFEST_NAME
    text = render_versions(
        reports,
        generated=_iso_utc(time.time()),
        reactome_release=_read_release_number(dest_dir),
        dest_dir=dest_dir,
    )
    tmp = manifest.with_name(manifest.name + ".part")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(manifest)

    print(render_summary(reports, elapsed_s=elapsed, manifest=manifest))
    return 1 if any(r.status == "failed" for r in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
