"""Resolve every source's gene symbols to HGNC ids and write the resolution log.

Reads the four gene-set GMTs from ``data/raw/``, resolves each through the snapshot
:data:`thema.data.genes.SOURCE_SNAPSHOT` assigns it, writes ``data/gene_resolution_log.tsv``, and
prints a per-source summary. The log is committed: it is provenance, not data, and the ambiguous
rows in it are meant to be adjudicated by hand.
"""

import argparse
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from thema.data.genes import (
    CURRENT,
    OUTCOMES,
    SOURCE_SNAPSHOT,
    GeneResolver,
    ResolutionReport,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = REPO_ROOT / "data" / "raw"
DEFAULT_LOG = REPO_ROOT / "data" / "gene_resolution_log.tsv"
HGNC_RELEASE = "2026-07-07"

LOG_COLUMNS = (
    "source",
    "original_symbol",
    "outcome",
    "hgnc_id",
    "approved_symbol",
    "match_type",
    "snapshot",
    "carried_forward",
    "note",
)


@dataclass(frozen=True, slots=True)
class SourceFile:
    """One gene-set source to resolve.

    Attributes:
        key: Key into :data:`thema.data.genes.SOURCE_SNAPSHOT`.
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


def read_gmt_symbols(path: Path) -> tuple[str, ...]:
    """Read the unique gene entries of a GMT, in first-seen order.

    Every source here is a plain GMT -- set name, a description or id, then the genes -- so the
    same reader covers all four even though column two means different things in each.

    Args:
        path: Path to the GMT file.

    Returns:
        Each distinct entry from column three onwards, in the order first encountered.
    """
    seen: dict[str, None] = {}
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            for entry in fields[2:]:
                symbol = entry.strip()
                if symbol:
                    seen.setdefault(symbol, None)
    return tuple(seen)


def log_rows(source: str, report: ResolutionReport) -> list[tuple[str, ...]]:
    """Render the log rows for one source, omitting clean current-approved matches.

    Args:
        source: The source key, written to the first column.
        report: The report to render.

    Returns:
        One row per symbol that needs a human's attention, sorted by symbol.
    """
    rows: list[tuple[str, ...]] = []
    for resolution in report.resolutions:
        if resolution.is_clean_current_approved:
            continue
        ref = resolution.ref
        rows.append(
            (
                source,
                resolution.symbol,
                resolution.outcome,
                ref.hgnc_id if ref else "-",
                ref.approved_symbol if ref else "-",
                ref.match_type if ref else "-",
                ref.snapshot if ref else report.snapshot,
                ("yes" if ref.carried_forward else "no") if ref else "-",
                resolution.note.replace("\t", " ") or "-",
            )
        )
    return sorted(rows, key=lambda row: (row[1], row[2]))


def write_log(path: Path, rows: Sequence[Sequence[str]]) -> None:
    """Write the resolution log atomically, header first.

    Args:
        path: Destination, normally ``data/gene_resolution_log.tsv``.
        rows: Rows in final order.
    """
    text = "\n".join(["\t".join(LOG_COLUMNS), *("\t".join(row) for row in rows)]) + "\n"
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


def render_outcomes(reports: dict[str, ResolutionReport], totals: dict[str, int]) -> str:
    """Render the per-source outcome table, counts with percentages.

    Args:
        reports: Report per source key.
        totals: Number of resolved entries per source key.

    Returns:
        A formatted table.
    """
    headers = ("SOURCE", "SNAPSHOT", "SYMBOLS", *(o.upper() for o in OUTCOMES), "CARRIED")
    rows: list[Sequence[str]] = []
    for source, report in reports.items():
        counts = report.counts
        total = totals[source] or 1
        rows.append(
            (
                source,
                report.snapshot,
                f"{totals[source]:,}",
                *(
                    f"{counts[o]:,} ({counts[o] / total * 100:.1f}%)" if counts[o] else "-"
                    for o in OUTCOMES
                ),
                f"{report.carried_forward:,}",
            )
        )
    return _table(headers, rows, "<<" + ">" * (len(headers) - 2))


def render_era_delta(
    era: ResolutionReport, fallback: ResolutionReport, *, era_label: str
) -> str:
    """Report what reading BTM through its own era actually bought.

    Compares BTM resolved through the derived era lens against the same symbols resolved through
    the current release, which is what the tool would do if the era lens did not exist.

    Args:
        era: BTM resolved through the era lens.
        fallback: The same symbols resolved through ``current``.
        era_label: Label of the era lens, for the heading.

    Returns:
        A formatted summary, including examples of the symbols the two lenses disagree on.
    """
    era_refs = {r.symbol: r for r in era.resolutions}
    now_refs = {r.symbol: r for r in fallback.resolutions}

    different: list[tuple[str, str, str]] = []
    rescued: list[str] = []
    lost: list[str] = []
    for symbol, era_res in era_refs.items():
        now_res = now_refs.get(symbol)
        if now_res is None:
            continue
        era_id = era_res.ref.hgnc_id if era_res.ref else None
        now_id = now_res.ref.hgnc_id if now_res.ref else None
        if era_id and now_id and era_id != now_id:
            era_side = f"{era_id} {era_res.ref.approved_symbol}"
            now_side = f"{now_id} {now_res.ref.approved_symbol}"
            different.append((symbol, era_side, now_side))
        elif era_id and not now_id:
            rescued.append(symbol)
        elif now_id and not era_id:
            lost.append(symbol)

    lines = [
        f"BTM era-lens delta: {era_label} vs {CURRENT}",
        f"  resolved to a DIFFERENT gene : {len(different):,}"
        "   <- symbols current-only resolution gets wrong",
        f"  resolved only by the era lens: {len(rescued):,}",
        f"  resolved only by current     : {len(lost):,}",
    ]
    if different:
        lines.append("")
        lines.append("  first 10 disagreements:")
        lines.append(
            "\n".join(
                f"    {symbol:<16} {era_label}: {era_side:<28} {CURRENT}: {now_side}"
                for symbol, era_side, now_side in sorted(different)[:10]
            )
        )
    if lost:
        lines.append("")
        lines.append(f"  lost by the era lens (first 10): {', '.join(sorted(lost)[:10])}")
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
        "--preview", type=int, default=20, metavar="N", help="log rows to print (default: 20)"
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Resolve every source, write the log, and print the summary tables."""
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

    print("loading HGNC snapshots...", file=sys.stderr)
    resolver = GeneResolver.from_files(complete_set, withdrawn)

    reports: dict[str, ResolutionReport] = {}
    totals: dict[str, int] = {}
    multi_counts: dict[str, int] = {}
    rows: list[tuple[str, ...]] = []
    btm_symbols: tuple[str, ...] = ()

    for source in SOURCE_FILES:
        path = args.raw / source.filename
        if not path.is_file():
            print(f"missing {path}; skipping {source.key}", file=sys.stderr)
            continue
        symbols = read_gmt_symbols(path)
        if source.key == "btm":
            btm_symbols = symbols
        as_of = resolver.snapshot_for(source.key)
        print(f"resolving {source.key} ({len(symbols):,} entries) through {as_of}", file=sys.stderr)
        _, report = resolver.resolve_set(symbols, as_of)
        reports[source.key] = report
        totals[source.key] = len(report.resolutions)
        multi_counts[source.key] = len(report.multi_mapping_derived)
        rows.extend(log_rows(source.key, report))

    if not reports:
        print("no sources found", file=sys.stderr)
        return 1

    order = {s.key: i for i, s in enumerate(SOURCE_FILES)}
    rows.sort(key=lambda row: (order[row[0]], row[1], row[2]))
    write_log(args.log, rows)

    print()
    print(render_outcomes(reports, totals))
    print()
    print(f"{len(rows):,} log rows written to {args.log}")
    multi_total = sum(multi_counts.values())
    print(
        f"multi-mapping ({' /// '.join(['A', 'B'])}) split-derived genes: {multi_total:,}"
        + (
            "  [" + ", ".join(f"{k}={v}" for k, v in multi_counts.items() if v) + "]"
            if multi_total
            else ""
        )
    )

    if btm_symbols and "btm" in reports:
        _, fallback = resolver.resolve_set(btm_symbols, CURRENT)
        print()
        print(render_era_delta(reports["btm"], fallback, era_label=SOURCE_SNAPSHOT["btm"]))

    if args.preview:
        print()
        print(f"first {args.preview} rows of {args.log.name}:")
        print(_table(LOG_COLUMNS, rows[: args.preview], "<" * len(LOG_COLUMNS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
