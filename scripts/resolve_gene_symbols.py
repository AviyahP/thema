"""Resolve every source's gene symbols to HGNC ids and write the resolution log.

Reads the four gene-set GMTs from ``data/raw/``, resolves each against the pinned HGNC release,
writes ``data/gene_resolution_log.tsv`` and ``data/gene_resolution_spotcheck.tsv``, and prints a
per-source summary plus a within-source collision check. Both files are committed: they are
provenance, not data, and the ambiguous rows are meant to be adjudicated by hand.
"""

import argparse
import random
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from thema.data.genes import OUTCOMES, GeneResolver, ResolutionReport

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = REPO_ROOT / "data" / "raw"
DEFAULT_LOG = REPO_ROOT / "data" / "gene_resolution_log.tsv"
DEFAULT_SPOTCHECK = REPO_ROOT / "data" / "gene_resolution_spotcheck.tsv"
DEFAULT_ADJUDICATIONS = REPO_ROOT / "data" / "gene_resolution_adjudications.tsv"
HGNC_RELEASE = "2026-07-07"

#: Sampling seed, so the committed spot-check file is byte-stable and does not churn in git.
SPOTCHECK_SEED = 0
SPOTCHECK_PREVIOUS = 20
MAX_PATHWAYS = 5

#: Outcomes whose rows carry pathway context: unsettled, or settled by hand.
_ADJUDICABLE = frozenset({"ambiguous", "adjudicated", "excluded"})

LOG_COLUMNS = (
    "source",
    "original_symbol",
    "outcome",
    "hgnc_id",
    "approved_symbol",
    "match_type",
    "carried_forward",
    "pathways",
    "note",
)

SPOTCHECK_COLUMNS = (
    "tier",
    "source",
    "original_symbol",
    "hgnc_id",
    "approved_symbol",
    "pathways",
    "verified",
    "note",
)


@dataclass(frozen=True, slots=True)
class SourceFile:
    """One gene-set source to resolve.

    Attributes:
        key: Short source name, written to the log's first column.
        filename: GMT filename under the raw data directory.
    """

    key: str
    filename: str


SOURCE_FILES: tuple[SourceFile, ...] = (
    SourceFile("reactome", "ReactomePathways.gmt"),
    SourceFile("hallmark", "h.all.v2026.1.Hs.symbols.gmt"),
    SourceFile("go", "c5.go.bp.v2026.1.Hs.symbols.gmt"),
    SourceFile("btm", "BTM_for_GSEA_20131008.gmt"),
)


def read_gmt(path: Path) -> dict[str, tuple[str, ...]]:
    """Read a GMT, mapping each gene entry to the sets it appears in.

    Every source here is a plain GMT -- set name, a description or id, then the genes -- so the
    same reader covers all four even though column two means different things in each. The
    containing set names are what make an ambiguous symbol adjudicable by biological context.

    Args:
        path: Path to the GMT file.

    Returns:
        Each distinct entry from column three onwards, in first-seen order, mapped to the set
        names containing it.
    """
    entries: dict[str, list[str]] = {}
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 3:
                continue
            name = fields[0].strip()
            for entry in fields[2:]:
                symbol = entry.strip()
                if symbol:
                    entries.setdefault(symbol, []).append(name)
    return {symbol: tuple(names) for symbol, names in entries.items()}


def format_pathways(names: Sequence[str]) -> str:
    """Render the containing set names for a log cell, capped so rows stay readable."""
    if not names:
        return "-"
    shown = "; ".join(names[:MAX_PATHWAYS])
    extra = len(names) - MAX_PATHWAYS
    return f"{shown} (+{extra} more)" if extra > 0 else shown


def log_rows(
    source: str, report: ResolutionReport, pathways: Mapping[str, tuple[str, ...]]
) -> list[tuple[str, ...]]:
    """Render the log rows for one source, omitting clean approved matches.

    Args:
        source: The source key, written to the first column.
        report: The report to render.
        pathways: Entry to containing set names, from :func:`read_gmt`.

    Returns:
        One row per symbol that needs a human's attention, sorted by symbol.
    """
    rows: list[tuple[str, ...]] = []
    for resolution in report.resolutions:
        if resolution.is_clean_approved:
            continue
        ref = resolution.ref
        # Only the hand-adjudicable rows carry the containing sets -- those still ambiguous, and
        # those an adjudication has since settled. Every row carrying them would balloon the file.
        key = resolution.origin or resolution.symbol
        cell = (
            format_pathways(pathways.get(key, ()))
            if resolution.outcome in _ADJUDICABLE
            else "-"
        )
        rows.append(
            (
                source,
                resolution.symbol,
                resolution.outcome,
                ref.hgnc_id if ref else "-",
                ref.approved_symbol if ref else "-",
                ref.match_type if ref else "-",
                ("yes" if ref.carried_forward else "no") if ref else "-",
                cell,
                resolution.note.replace("\t", " ") or "-",
            )
        )
    return sorted(rows, key=lambda row: (row[1], row[2]))


def spotcheck_rows(
    reports: Mapping[str, ResolutionReport],
    pathways: Mapping[str, Mapping[str, tuple[str, ...]]],
) -> list[tuple[str, ...]]:
    """Sample previous- and alias-tier resolutions for hand verification.

    The alias tier is taken in full: it is the weakest evidence the resolver acts on and the
    likeliest to be wrong, and there are few enough to check exhaustively. The previous tier is
    sampled with a fixed seed so the committed file does not churn.

    Args:
        reports: Report per source key.
        pathways: Entry to containing set names, per source key.

    Returns:
        Rows ready to write, alias tier first, each with empty verified and note columns.
    """
    pools: dict[str, list[tuple[str, ...]]] = {"alias": [], "previous": []}
    for source, report in reports.items():
        for resolution in report.resolutions:
            ref = resolution.ref
            if ref is None or ref.match_type not in pools:
                continue
            key = resolution.origin or resolution.symbol
            pools[ref.match_type].append(
                (
                    ref.match_type,
                    source,
                    resolution.symbol,
                    ref.hgnc_id,
                    ref.approved_symbol,
                    format_pathways(pathways[source].get(key, ())),
                    "",
                    "",
                )
            )

    previous = sorted(pools["previous"])
    sampled = random.Random(SPOTCHECK_SEED).sample(
        previous, min(SPOTCHECK_PREVIOUS, len(previous))
    )
    return sorted(pools["alias"]) + sorted(sampled)


def write_tsv(path: Path, columns: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
    """Write a TSV atomically, header first.

    Args:
        path: Destination.
        columns: Header row.
        rows: Rows in final order.
    """
    text = "\n".join(["\t".join(columns), *("\t".join(row) for row in rows)]) + "\n"
    tmp = path.with_name(path.name + ".part")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _table(headers: Sequence[str], rows: Sequence[Sequence[str]], align: str) -> str:
    if not rows:
        return "(no rows)"
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


def render_outcomes(reports: Mapping[str, ResolutionReport], totals: Mapping[str, int]) -> str:
    """Render the per-source outcome table, counts with percentages.

    Args:
        reports: Report per source key.
        totals: Number of resolved entries per source key.

    Returns:
        A formatted table.
    """
    headers = ("SOURCE", "SYMBOLS", *(o.upper() for o in OUTCOMES), "CARRIED")
    rows: list[Sequence[str]] = []
    for source, report in reports.items():
        counts = report.counts
        total = totals[source] or 1
        rows.append(
            (
                source,
                f"{totals[source]:,}",
                *(
                    f"{counts[o]:,} ({counts[o] / total * 100:.1f}%)" if counts[o] else "-"
                    for o in OUTCOMES
                ),
                f"{report.carried_forward:,}",
            )
        )
    return _table(headers, rows, "<" + ">" * (len(headers) - 1))


def render_collisions(reports: Mapping[str, ResolutionReport]) -> str:
    """Report distinct symbols within one source that resolve to the same gene.

    A collision means the source's gene sets silently shrink on deduplication, so this doubles as
    a correctness signal on the resolver: an unexpected pair usually means a bad alias match.

    Args:
        reports: Report per source key.

    Returns:
        A formatted summary, listing every colliding group.
    """
    lines: list[str] = []
    for source, report in reports.items():
        collisions = {
            hgnc_id: symbols
            for hgnc_id, symbols in report.by_hgnc_id().items()
            if len(symbols) > 1
        }
        lines.append(f"{source}: {len(collisions)} colliding gene(s)")
        for hgnc_id, symbols in sorted(collisions.items(), key=lambda kv: kv[1]):
            lines.append(f"    {hgnc_id:<12} {' = '.join(symbols)}")
    return "\n".join(lines)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="resolve_gene_symbols.py",
        description="Resolve source gene symbols to HGNC ids and write the resolution log.",
    )
    parser.add_argument(
        "--raw", type=Path, default=DEFAULT_RAW, help="raw data directory (default: %(default)s)"
    )
    parser.add_argument(
        "--log", type=Path, default=DEFAULT_LOG, help="log destination (default: %(default)s)"
    )
    parser.add_argument(
        "--spotcheck",
        type=Path,
        default=DEFAULT_SPOTCHECK,
        help="spot-check destination (default: %(default)s)",
    )
    parser.add_argument(
        "--adjudications",
        type=Path,
        default=DEFAULT_ADJUDICATIONS,
        help="hand-settled ambiguous cases (default: %(default)s)",
    )
    parser.add_argument(
        "--preview", type=int, default=20, metavar="N", help="log rows to print (default: 20)"
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Resolve every source, write the log and spot-check, and print the summary tables."""
    args = parse_args(argv)
    complete_set = args.raw / f"hgnc_complete_set_{HGNC_RELEASE}.txt"
    withdrawn = args.raw / f"withdrawn_{HGNC_RELEASE}.txt"
    for path in (complete_set, withdrawn):
        if not path.is_file():
            print(
                f"missing {path}; run scripts/download_pathway_data.py --only hgnc",
                file=sys.stderr,
            )
            return 1

    print(f"loading HGNC release {HGNC_RELEASE}...", file=sys.stderr)
    resolver = GeneResolver.from_files(complete_set, withdrawn, args.adjudications)
    if resolver.adjudications:
        print(f"{len(resolver.adjudications)} hand-settled adjudications loaded", file=sys.stderr)

    reports: dict[str, ResolutionReport] = {}
    totals: dict[str, int] = {}
    multi_counts: dict[str, int] = {}
    pathways: dict[str, Mapping[str, tuple[str, ...]]] = {}
    rows: list[tuple[str, ...]] = []

    for source in SOURCE_FILES:
        path = args.raw / source.filename
        if not path.is_file():
            print(f"missing {path}; skipping {source.key}", file=sys.stderr)
            continue
        entries = read_gmt(path)
        pathways[source.key] = entries
        print(f"resolving {source.key} ({len(entries):,} entries)", file=sys.stderr)
        _, report = resolver.resolve_set(entries, source.key)
        reports[source.key] = report
        totals[source.key] = len(report.resolutions)
        multi_counts[source.key] = len(report.multi_mapping_derived)
        rows.extend(log_rows(source.key, report, entries))

    if not reports:
        print("no sources found", file=sys.stderr)
        return 1

    applied = {
        (source, r.symbol)
        for source, report in reports.items()
        for r in report.resolutions
        if r.outcome in {"adjudicated", "excluded"}
    }
    stale = sorted(set(resolver.adjudications) - applied)
    if stale:
        print(
            "warning: adjudications that matched no ambiguous symbol in any source "
            "(the symbol may have been dropped, or now resolves cleanly):",
            file=sys.stderr,
        )
        for key in stale:
            print(f"  {key[0]}/{key[1]}", file=sys.stderr)

    order = {s.key: i for i, s in enumerate(SOURCE_FILES)}
    rows.sort(key=lambda row: (order[row[0]], row[1], row[2]))
    write_tsv(args.log, LOG_COLUMNS, rows)

    spotcheck = spotcheck_rows(reports, pathways)
    write_tsv(args.spotcheck, SPOTCHECK_COLUMNS, spotcheck)

    print()
    print(render_outcomes(reports, totals))
    print()
    print(f"{len(rows):,} log rows written to {args.log}")
    multi_total = sum(multi_counts.values())
    print(
        f"multi-mapping split-derived genes: {multi_total:,}"
        + (
            "  [" + ", ".join(f"{k}={v}" for k, v in multi_counts.items() if v) + "]"
            if multi_total
            else ""
        )
    )

    print()
    print("within-source collisions (distinct symbols resolving to one gene):")
    print(render_collisions(reports))

    print()
    print(f"{len(spotcheck):,} spot-check rows written to {args.spotcheck}")
    print(_table(SPOTCHECK_COLUMNS, spotcheck, "<" * len(SPOTCHECK_COLUMNS)))

    if args.preview:
        print()
        print(f"first {args.preview} rows of {args.log.name}:")
        print(_table(LOG_COLUMNS, rows[: args.preview], "<" * len(LOG_COLUMNS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
