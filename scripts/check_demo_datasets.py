"""Check candidate worked-example datasets against the rung-3 requirement, read-only.

`docs/spec/addendum-2026-09-18.md` B7: rung 3 is a hard requirement for the worked examples, and a
declared or assumed universe is not acceptable. A dataset therefore qualifies only if a PROCESSED
COUNT MATRIX is deposited, so the measured universe can be derived from the data -- the set of genes
detected in the matrix -- rather than assumed from a platform annotation.

This script answers three questions per accession and nothing else:

0. is it sequencing rather than an array -- an array gives a PLATFORM-derived universe (what the
   chip carries), not a DETECTION-derived one, which is the distinction B7 turns on and the reason
   the arthritis array set was dropped;
1. does the accession exist;
2. is a processed count matrix deposited (supplementary file, or a GEO-hosted RNA-seq count table);
3. are sample-group labels present in the metadata, so a contrast can actually be defined.

It downloads nothing but metadata, writes nothing, and spends nothing. It needs network access,
which is why it is written to be run from Aviyah's machine rather than executed here.

    uv run scripts/check_demo_datasets.py GSE157103 GSE62944
    uv run scripts/check_demo_datasets.py --candidates      # the three proposed, with notes
"""

import argparse
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

#: GEO's plain-text metadata view. `targ=self` returns the series record without its samples, which
#: is all that is needed and is two orders of magnitude smaller than `targ=all`.
GEO_TEXT = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={acc}&targ=self&form=text&view=brief"

#: The supplementary-file listing. Separate request because `targ=self` omits it.
GEO_FULL = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={acc}&targ=gsm&form=text&view=brief"

#: Filename fragments that indicate a processed expression matrix rather than raw reads. Matched
#: case-insensitively against supplementary filenames.
MATRIX_HINTS = (
    "count", "counts", "fpkm", "tpm", "rpkm", "cpm", "expression",
    "matrix", "genes.results", "featurecounts", "rsem", "salmon", "kallisto",
    "processed", "normalized", "normalised",
)

#: Fragments that indicate raw reads only. Presence of these alone does not qualify a dataset.
RAW_ONLY = ("fastq", ".sra", "bam", "cel.gz")

#: `!Series_type` values that mean sequencing. An array series is rejected outright: it fails B7
#: for the same reason GSE93272 did, and missing that was this script's own first bug -- GSE138458
#: was reported "no count matrix" when the real objection is that it is a BeadChip.
SEQ_TYPES = ("high throughput sequencing", "sequencing")

#: Metadata fields that usually carry the contrast. Reported so a human can see whether a
#: group label exists at all; this script does not try to parse the contrast itself.
GROUP_FIELDS = ("!Series_overall_design", "!Series_summary", "!Series_type")

#: Proposed candidates. Accessions are BELIEVED CORRECT AND UNVERIFIED -- they were written from
#: memory without network access, and a plausible-looking wrong accession is worse than none. The
#: first thing this script does is tell you whether each one exists.
CANDIDATES: tuple[tuple[str, str, str], ...] = (
    (
        "GSE157103",
        "infection severity -- COVID-19 severe vs moderate, leukocyte RNA-seq",
        "Universe = genes with nonzero counts (or above a stated detection floor) across samples "
        "of the deposited count matrix. Cleanest fit of the three.",
    ),
    (
        "GSE62944",
        "tumour vs normal -- TCGA RNA-seq recount, tumour and matched normal",
        "Universe = genes present in the deposited count matrix. Alternative if this fails: pull "
        "TCGA-BRCA from the GDC directly rather than through GEO.",
    ),
    (
        "GSE129705",
        "autoimmune whole blood -- biologic-naive rheumatoid arthritis, whole-blood RNA-seq, n=128",
        "REPLACES the arthritis array set (GSE93272) and the first replacement offered "
        "(GSE138458), both dropped as arrays: a chip gives a platform-derived universe, not a "
        "detection-derived one. Found by searching GEO rather than from memory. Universe = "
        "genes detected in the "
        "deposited count matrix.",
    ),
)


def fetch(url: str, timeout: float = 30.0) -> str | None:
    """Fetch a URL as text, returning None if it cannot be read.

    Args:
        url: The URL.
        timeout: Seconds to wait.

    Returns:
        The body, or None on any HTTP or network error.
    """
    try:
        with urllib.request.urlopen(url, timeout=timeout) as handle:  # noqa: S310
            return handle.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        print(f"    network error: {exc}", file=sys.stderr)
        return None


def supplementary_files(text: str) -> list[str]:
    """Pull supplementary filenames out of a GEO text record.

    Args:
        text: The record body.

    Returns:
        Every value of a `!*_supplementary_file*` field.
    """
    out: list[str] = []
    for line in text.splitlines():
        if re.match(r"^![A-Za-z]+_supplementary_file", line) and "=" in line:
            value = line.split("=", 1)[1].strip()
            if value and value.upper() != "NONE":
                out.append(value)
    return out


def classify(files: list[str]) -> tuple[list[str], list[str]]:
    """Split supplementary filenames into likely matrices and likely raw-only.

    Args:
        files: Supplementary filenames or URLs.

    Returns:
        The ones that look like a processed matrix, and the ones that look like raw reads.
    """
    matrix = [f for f in files if any(h in f.lower() for h in MATRIX_HINTS)]
    raw = [f for f in files if any(h in f.lower() for h in RAW_ONLY)]
    return matrix, raw


def field(text: str, name: str) -> str:
    """Read one GEO metadata field, joining repeats.

    Args:
        text: The record body.
        name: The field name, including the leading `!`.

    Returns:
        The joined values, or "" if absent.
    """
    vals = [
        line.split("=", 1)[1].strip()
        for line in text.splitlines()
        if line.startswith(name + " ") or line.startswith(name + "=")
        if "=" in line
    ]
    return " | ".join(vals)


def check(acc: str) -> dict[str, object]:
    """Run the three checks for one accession.

    Args:
        acc: A GEO series accession, e.g. ``GSE157103``.

    Returns:
        A record of what was found. ``qualifies`` is True only when all three checks pass.
    """
    print(f"\n{acc}")
    text = fetch(GEO_TEXT.format(acc=urllib.parse.quote(acc)))
    if not text or "!Series_title" not in text:
        print("  1. exists                     NO -- accession not found or not a series")
        return {"acc": acc, "exists": False, "qualifies": False}
    title = field(text, "!Series_title")
    print(f"  1. exists                     yes -- {title[:70]}")

    stype = field(text, "!Series_type")
    is_seq = any(h in stype.lower() for h in SEQ_TYPES)
    print(f"  0. sequencing, not an array   {'yes' if is_seq else 'NO'} -- {stype[:60]}")
    if not is_seq:
        print("  -> rung 3 usable              NO -- an array universe is platform-derived")
        return {"acc": acc, "exists": True, "title": title, "is_seq": False, "qualifies": False}

    full = fetch(GEO_FULL.format(acc=urllib.parse.quote(acc))) or ""
    files = supplementary_files(text) + supplementary_files(full)
    matrix, raw = classify(files)
    # The filename heuristic gives a hint, not a verdict. It has already produced two false
    # negatives on this project's own candidates -- GSE138458 (an array, caught elsewhere) and
    # GSE129705, whose matrix is called "...-processed-data-file.txt.gz". When nothing matches but
    # non-raw files exist, say UNCLEAR and print them, rather than rejecting a usable dataset.
    other = [f for f in files if f not in matrix and f not in raw]
    unclear = not matrix and bool(other)
    if matrix:
        print(f"  2. processed count matrix     yes -- {len(matrix)} candidate file(s)")
        for f in matrix[:5]:
            print(f"       {f.rsplit('/', 1)[-1]}")
    elif unclear:
        print(f"  2. processed count matrix     UNCLEAR -- {len(other)} file(s) match no known "
              "naming pattern; inspect:")
        for f in other[:5]:
            print(f"       {f.rsplit('/', 1)[-1]}")
    else:
        print(f"  2. processed count matrix     NO -- {len(files)} supplementary file(s), "
              f"{len(raw)} look raw-only")

    design = field(text, "!Series_overall_design")
    has_groups = bool(design)
    print(f"  3. sample-group labels        {'yes' if has_groups else 'NO'}")
    if design:
        print(f"       design: {design[:140]}")

    qualifies = is_seq and bool(matrix) and has_groups
    verdict = "YES" if qualifies else ("INSPECT" if (is_seq and unclear and has_groups) else "NO")
    print(f"  -> rung 3 usable              {verdict}")
    return {
        "acc": acc, "exists": True, "title": title, "is_seq": is_seq, "matrix_files": matrix,
        "n_supplementary": len(files), "has_groups": has_groups, "qualifies": qualifies,
        "verdict": verdict,
    }


def main(argv: list[str] | None = None) -> int:
    """Check the accessions named, or the three proposed candidates."""
    parser = argparse.ArgumentParser(
        prog="check_demo_datasets.py", description=__doc__.splitlines()[0]
    )
    parser.add_argument("accession", nargs="*", help="GEO series accessions to check")
    parser.add_argument(
        "--candidates", action="store_true", help="check the three proposed candidates with notes"
    )
    args = parser.parse_args(argv)

    if args.candidates:
        print("PROPOSED CANDIDATES -- accessions written from memory, UNVERIFIED until this runs\n")
        for acc, what, note in CANDIDATES:
            print(f"  {acc}  {what}")
            print(f"      {note}\n")
        accessions = [acc for acc, _w, _n in CANDIDATES]
    elif args.accession:
        accessions = args.accession
    else:
        parser.error("name at least one accession, or pass --candidates")

    results = [check(acc) for acc in accessions]
    ok = [r for r in results if r.get("qualifies")]
    print(f"\n{len(ok)} of {len(results)} qualify for rung 3.")
    if len(ok) < 3:
        print("Fewer than three qualify: ask for replacement candidates rather than relaxing the")
        print("universe rule -- B7 makes a derived universe a hard requirement.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
