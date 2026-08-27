"""Build the uniform pathway table from all four sources, and the committed record of that build.

Writes ``data/pathways.tsv`` -- one row per pathway, gitignored and regenerable -- and
``data/pathways_summary.tsv``, which pins its sha256 and records what the build measured. Both
follow the pattern ``scripts/filter_reactome_membership.py`` established.

Two cross-checks in the summary are worth naming, because each catches a way two files can quietly
disagree about the same fact. The first re-checks this build's digest of ``reactome_membership.tsv``
against the digest the cascade committed, so a stale or differently-flagged cascade output cannot be
built on unnoticed. The second compares the symbols this build drops against the symbols
``data/gene_resolution_log.tsv`` records as resolving to nothing: the same resolver over the same
GMTs and the same HGNC release must reach the same verdicts, and if it does not, that is a finding
rather than a detail.
"""

import argparse
import re
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from math import ceil
from pathlib import Path

from thema.data.formats import read_gmt_sets
from thema.data.genes import GeneResolver
from thema.data.pathways import (
    DEGRADATIONS,
    PATHWAY_COLUMNS,
    SOURCES,
    TEXT_AVAILABILITIES,
    Pathway,
    PathwayCollection,
    PathwayInputs,
    btm_identity,
)
from thema.data.tables import SUMMARY_COLUMNS, sha256_file, write_tsv

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = REPO_ROOT / "data" / "raw"
DEFAULT_OUT = REPO_ROOT / "data"

HGNC_RELEASE = "2026-07-07"
GO_RELEASE = "2026-08-05"
MSIGDB_RELEASE = "2026.1.Hs"
BTM_COMMIT = "94d5288af08320670e1337191173649a864602f8"

PATHWAY_TABLE = "pathways.tsv"
SUMMARY_TABLE = "pathways_summary.tsv"
MEMBERSHIP_TABLE = "reactome_membership.tsv"
MEMBERSHIP_SUMMARY = "reactome_membership_summary.tsv"
RESOLUTION_LOG = "gene_resolution_log.tsv"

#: Resolution-log outcomes that produced no gene.
NON_RESOLVING = frozenset({"unmapped", "ambiguous", "excluded", "withdrawn"})

#: Sources whose symbols this build resolves, so their drops can be checked against the committed
#: log. Reactome is absent by design: its membership comes from the cascade, which discards rows the
#: resolver would have kept, so the two are not measuring the same thing.
RESOLVED_SOURCES = ("go", "hallmark", "btm")

# Stated expectations, checked and reported rather than assumed -- the idiom the membership summary
# uses. Where measurement disagrees the summary records FAIL with the measured value, so a
# divergence stays visible instead of silently becoming the new expectation.
#
# Their provenance is recorded in the summary too, and matters: these numbers come from the
# planning-time measurement of this same data, not from an independent source. A pass means the
# build reproduces that measurement, not that either is right.
EXPECT_HUMAN_PATHWAYS = 2883
EXPECT_DUPLICATE_SUMMATIONS = 1
EXPECT_DUPLICATE_NAMES = 11
EXPECT_GO_SETS = 7538
EXPECT_HALLMARK_DESCRIPTIONS = 50
EXPECT_BTM_MODULES = 346
EXPECT_KEY_COLLISIONS = 0
EXPECT_NAME_COLLISIONS = 94
EXPECT_EXACT_NAME_COLLISIONS = 18

EXPECTATION_PROVENANCE = (
    "every expectation below comes from the planning-time measurement of this same data, not from "
    "an independent source - a pass means this build reproduces that measurement, not that it is "
    "correct"
)

_NOT_NAME = re.compile(r"[^a-z0-9 ]+")
_SPACES = re.compile(r"\s+")
_BTM_ID = re.compile(r"^[MS][\d.]*$")


@dataclass(frozen=True, slots=True)
class Check:
    """One stated expectation, with what the build actually measured.

    Attributes:
        key: What was checked, written to the summary's ``key`` column.
        measured: What this build found.
        expected: What it was supposed to find.
        note: Why the expectation is what it is, where that is not self-evident.
    """

    key: str
    measured: str
    expected: str
    note: str = ""

    @property
    def status(self) -> str:
        """``pass`` or ``FAIL``."""
        return "pass" if self.measured == self.expected else "FAIL"

    def row(self) -> tuple[str, str, str, str]:
        """Render this check as a summary row."""
        verdict = f"expected {self.expected} [{self.status}]"
        note = f"{verdict} - {self.note}" if self.note else verdict
        return ("sanity", self.key, self.measured, note)


def percentile(values: Sequence[int], share: float) -> int:
    """Return the nearest-rank percentile of a sequence of counts.

    Args:
        values: The values, in any order.
        share: The percentile as a share, for example 0.9.

    Returns:
        The value at that rank, or 0 if there are none.
    """
    if not values:
        return 0
    ranked = sorted(values)
    return ranked[max(0, min(len(ranked) - 1, ceil(share * len(ranked)) - 1))]


def spread(values: Sequence[int]) -> str:
    """Render a distribution as ``min/p10/median/p90/max``."""
    if not values:
        return "-"
    return "/".join(
        str(v)
        for v in (
            min(values),
            percentile(values, 0.10),
            percentile(values, 0.50),
            percentile(values, 0.90),
            max(values),
        )
    )


def normalized_name(pathway: Pathway) -> str:
    """Reduce a pathway's name to the form a cross-source comparison can use.

    Hallmark publishes ``HALLMARK_TNFA_SIGNALING_VIA_NFKB`` where the others publish prose, so the
    prefix and underscores come off; BTM's module id was already removed by its loader. What
    remains is lowercased and stripped of punctuation.

    Args:
        pathway: The pathway.

    Returns:
        The comparable form of its name.
    """
    name = pathway.name
    if pathway.source == "hallmark":
        name = name.removeprefix("HALLMARK_").replace("_", " ")
    return _SPACES.sub(" ", _NOT_NAME.sub(" ", name.lower())).strip()


def name_collisions(collection: PathwayCollection, normalize: bool) -> int:
    """Count names carried by more than one source.

    Args:
        collection: The pathways.
        normalize: Whether to compare normalized names or the names verbatim.

    Returns:
        How many distinct names appear in two or more sources.
    """
    sources: dict[str, set[str]] = {}
    for pathway in collection:
        key = normalized_name(pathway) if normalize else pathway.name
        sources.setdefault(key, set()).add(pathway.source)
    return sum(1 for owners in sources.values() if len(owners) > 1)


def log_non_resolving(lines: Iterable[str]) -> dict[str, set[str]]:
    """Read the symbols the committed resolution log records as reaching no gene.

    Args:
        lines: Lines of ``data/gene_resolution_log.tsv``, header included.

    Returns:
        Each source mapped to its non-resolving symbols.
    """
    found: dict[str, set[str]] = {}
    for index, line in enumerate(lines):
        if index == 0:
            continue
        fields = line.rstrip("\n").split("\t")
        if len(fields) >= 3 and fields[2] in NON_RESOLVING:
            found.setdefault(fields[0], set()).add(fields[1])
    return found


def dropped_by_source(collection: PathwayCollection, source: str) -> set[str]:
    """Every distinct symbol one source dropped, across all its pathways."""
    return {symbol for p in collection.of_source(source) for symbol in p.dropped_symbols}


def collapsed_members(collection: PathwayCollection, source: str) -> int:
    """How many members a source's gene sets lost to deduplication.

    Two of a source's symbols can reach one gene, so ``n_genes`` is not
    ``len(entries) - n_dropped``. This is the difference, and without it the counts cannot be
    reconciled by anyone reading the summary.

    Args:
        collection: The pathways.
        source: The source key.

    Returns:
        The number of surplus symbols across that source's gene sets.
    """
    return sum(
        len(symbols) - 1
        for pathway in collection.of_source(source)
        for _, symbols in pathway.gene_symbols
        if len(symbols) > 1
    )


def duplicate_summation_ids(lines: Iterable[str]) -> tuple[str, ...]:
    """Identifiers carrying more than one row in ``pathway2summation.txt``."""
    seen: dict[str, int] = {}
    for index, line in enumerate(lines):
        if index == 0:
            continue
        identifier = line.split("\t", 1)[0].strip()
        if identifier:
            seen[identifier] = seen.get(identifier, 0) + 1
    return tuple(sorted(k for k, count in seen.items() if count > 1))


def duplicate_human_names(lines: Iterable[str]) -> int:
    """How many names ``ReactomePathways.txt`` gives to more than one human pathway."""
    seen: dict[str, int] = {}
    for line in lines:
        fields = line.rstrip("\n").split("\t")
        if len(fields) >= 3 and fields[2].strip() == "Homo sapiens":
            name = fields[1].strip()
            seen[name] = seen.get(name, 0) + 1
    return sum(1 for count in seen.values() if count > 1)


def btm_ids_agreeing_with_url(lines: Iterable[str]) -> tuple[int, int]:
    """Check each BTM module id parsed from a set name against the id in its own URL.

    Column two is a ``mummichog.org/BTM/<id>.htm`` link -- the module id re-encoded -- so it
    independently confirms the id parsed out of column one at no cost.

    Args:
        lines: Lines of the BTM GMT.

    Returns:
        How many agreed, and how many sets there were.
    """
    agreed = total = 0
    for gene_set in read_gmt_sets(lines):
        total += 1
        module_id, _, _ = btm_identity(gene_set.name)
        if gene_set.secondary.rsplit("/", 1)[-1].removesuffix(".htm") == module_id:
            agreed += 1
    return agreed, total


def committed_membership_digest(lines: Iterable[str]) -> str:
    """Read the cascade's own digest of ``reactome_membership.tsv`` out of its summary."""
    for line in lines:
        fields = line.rstrip("\n").split("\t")
        if len(fields) >= 3 and fields[0] == "digest" and fields[1] == MEMBERSHIP_TABLE:
            return fields[2]
    return "-"


def sanity_checks(
    collection: PathwayCollection,
    inputs: PathwayInputs,
    membership_digest: str,
    committed_digest: str,
    log: dict[str, set[str]],
) -> list[Check]:
    """Check every stated expectation and report each as measured, pass or fail.

    Args:
        collection: The pathways this build produced.
        inputs: The files it read, for the checks that re-read one.
        membership_digest: This build's digest of the cascade output.
        committed_digest: The digest the cascade committed for the same file.
        log: Non-resolving symbols per source, from the committed resolution log.

    Returns:
        One check per expectation, in report order.
    """
    go = collection.of_source("go")
    btm = collection.of_source("btm")
    agreed, modules = btm_ids_agreeing_with_url(
        inputs.btm_gmt.open(encoding="utf-8", errors="replace")
    )
    duplicates = duplicate_summation_ids(
        inputs.reactome_summations.open(encoding="utf-8", errors="replace")
    )
    checks = [
        Check(
            "cascade output is the one the cascade committed",
            membership_digest[:16],
            committed_digest[:16],
        ),
        Check(
            "reactome human pathways",
            str(len(collection.of_source("reactome"))),
            str(EXPECT_HUMAN_PATHWAYS),
        ),
        Check(
            "reactome duplicate summations",
            f"{len(duplicates)} ({'; '.join(duplicates) or 'none'})",
            f"{EXPECT_DUPLICATE_SUMMATIONS} (R-HSA-166016)",
        ),
        Check(
            "reactome duplicate names",
            str(
                duplicate_human_names(
                    inputs.reactome_names.open(encoding="utf-8", errors="replace")
                )
            ),
            str(EXPECT_DUPLICATE_NAMES),
        ),
        Check(
            "go sets carrying a term id",
            f"{sum(1 for p in go if p.source_id.startswith('GO:'))}/{len(go)}",
            f"{EXPECT_GO_SETS}/{EXPECT_GO_SETS}",
        ),
        Check(
            "go term ids joining the obo",
            f"{sum(1 for p in go if p.description_source_from == 'go_def')}/{len(go)}",
            f"{EXPECT_GO_SETS}/{EXPECT_GO_SETS}",
        ),
        Check(
            "hallmark descriptions found",
            f"{sum(1 for p in collection.of_source('hallmark') if p.description_source)}"
            f"/{len(collection.of_source('hallmark'))}",
            f"{EXPECT_HALLMARK_DESCRIPTIONS}/{EXPECT_HALLMARK_DESCRIPTIONS}",
        ),
        Check(
            "btm module ids parsed",
            f"{sum(1 for p in btm if _BTM_ID.match(p.source_id))}/{len(btm)}",
            f"{EXPECT_BTM_MODULES}/{EXPECT_BTM_MODULES}",
        ),
        Check(
            "btm ids agreeing with the url",
            f"{agreed}/{modules}",
            f"{EXPECT_BTM_MODULES}/{EXPECT_BTM_MODULES}",
        ),
        Check(
            "pathway key collisions",
            str(len(collection) - len(collection.by_key)),
            str(EXPECT_KEY_COLLISIONS),
        ),
        Check(
            "cross-source name collisions",
            str(name_collisions(collection, normalize=True)),
            str(EXPECT_NAME_COLLISIONS),
        ),
        Check(
            "cross-source name collisions, verbatim",
            str(name_collisions(collection, normalize=False)),
            str(EXPECT_EXACT_NAME_COLLISIONS),
            "zero in the source files; these become identical only because BTM's loader strips "
            "the module id its names end in",
        ),
    ]
    for source in RESOLVED_SOURCES:
        built, recorded = dropped_by_source(collection, source), log.get(source, set())
        checks.append(
            Check(
                f"{source} drops agree with the resolution log",
                f"{len(built)} built, {len(recorded)} logged, {len(built ^ recorded)} differing",
                f"{len(built)} built, {len(built)} logged, 0 differing",
            )
        )
    return checks


def build_summary(
    collection: PathwayCollection,
    pathway_digest: str,
    membership_digest: str,
    checks: Sequence[Check],
    html_summations: int,
    obsolete_go: int,
) -> list[tuple[str, str, str, str]]:
    """Assemble the committed record of this run.

    Args:
        collection: The pathways this build produced.
        pathway_digest: sha256 of the regenerable pathway table.
        membership_digest: sha256 of the cascade output this build read.
        checks: The stated expectations, already measured.
        html_summations: Reactome descriptions containing markup.
        obsolete_go: GO sets whose term this release flags obsolete.

    Returns:
        ``(section, key, value, note)`` rows.
    """
    rows: list[tuple[str, str, str, str]] = [
        ("digest", PATHWAY_TABLE, pathway_digest, "sha256 of the regenerable pathway table"),
        (
            "digest", MEMBERSHIP_TABLE, membership_digest,
            "cascade output this build read; pinned in " + MEMBERSHIP_SUMMARY,
        ),
        ("input", "hgnc_release", HGNC_RELEASE, ""),
        ("input", "go_release", GO_RELEASE, "obo data-version releases/2026-07-26"),
        ("input", "msigdb_release", MSIGDB_RELEASE, ""),
        ("input", "btm_commit", BTM_COMMIT, ""),
    ]

    for source in SOURCES:
        rows.append(("source", source, str(len(collection.of_source(source))), ""))
    rows.append(("source", "total", str(len(collection)), ""))

    for source in SOURCES:
        pathways = collection.of_source(source)
        described = [p for p in pathways if p.description_source]
        origin = described[0].description_source_from if described else "none"
        rows.append(
            (
                "description",
                f"{source}/{origin}",
                f"{len(described)}/{len(pathways)}",
                "BTM publishes no machine-readable description" if source == "btm" else "",
            )
        )
        lengths = [len(p.description_source or "") for p in described]
        if lengths:
            rows.append(
                (
                    "description_chars",
                    source,
                    f"{percentile(lengths, 0.10)}/{percentile(lengths, 0.50)}"
                    f"/{percentile(lengths, 0.90)}",
                    "p10/median/p90",
                )
            )

    for source in SOURCES:
        sizes = [p.n_genes for p in collection.of_source(source)]
        rows.append(("size", source, spread(sizes), "min/p10/median/p90/max genes per pathway"))

    for source in SOURCES:
        pathways = collection.of_source(source)
        for value in DEGRADATIONS:
            count = sum(1 for p in pathways if p.degradation == value)
            rows.append(("degradation", f"{source}/{value}", str(count), ""))

    for source in SOURCES:
        pathways = collection.of_source(source)
        for value in TEXT_AVAILABILITIES:
            count = sum(1 for p in pathways if p.text_availability == value)
            rows.append(("text_availability", f"{source}/{value}", str(count), ""))

    for source in SOURCES:
        genes = frozenset().union(*(p.genes for p in collection.of_source(source)))
        rows.append(("genes", source, str(len(genes)), ""))
    rows.append(("genes", "union", str(len(collection.gene_union)), "distinct across all sources"))

    for source in SOURCES:
        dropped = sum(p.n_dropped for p in collection.of_source(source))
        rows.append(("dropped", source, str(dropped), ""))
        rows.append(
            (
                "collapsed",
                source,
                str(collapsed_members(collection, source)),
                "members lost to deduplication; why n_genes is not entries minus dropped",
            )
        )

    rows.extend(
        (
            (
                "quality", "reactome_html", str(html_summations),
                "summations containing markup, kept verbatim as part of the source's register",
            ),
            (
                "quality", "go_obsolete", str(obsolete_go),
                "sets whose GO term this release flags obsolete; the marker is inside the text",
            ),
            (
                "quality", "btm_placeholder",
                str(
                    sum(
                        1
                        for p in collection.of_source("btm")
                        if p.text_availability == "no_usable_text"
                    )
                ),
                'modules named "TBA": no description and no real name',
            ),
        )
    )

    rows.append(
        ("sanity", "expectation provenance", "planning measurement", EXPECTATION_PROVENANCE)
    )
    rows.append(
        (
            "sanity",
            "reactome drops are not checked against the log",
            "by design",
            "the cascade discards rows the resolver would keep; the two do not measure one thing",
        )
    )
    rows.extend(check.row() for check in checks)
    return rows


def inputs_under(raw: Path, out: Path) -> PathwayInputs:
    """Name the ten input files under the given directories."""
    return PathwayInputs(
        reactome_names=raw / "ReactomePathways.txt",
        reactome_membership=out / MEMBERSHIP_TABLE,
        reactome_discards=out / "reactome_membership_discards.tsv",
        reactome_summations=raw / "pathway2summation.txt",
        go_gmt=raw / f"c5.go.bp.v{MSIGDB_RELEASE}.symbols.gmt",
        go_metadata=raw / f"c5.go.bp.v{MSIGDB_RELEASE}.json",
        go_obo=raw / "go-basic.obo",
        hallmark_gmt=raw / f"h.all.v{MSIGDB_RELEASE}.symbols.gmt",
        hallmark_xml=raw / f"msigdb_v{MSIGDB_RELEASE}.xml",
        btm_gmt=raw / "BTM_for_GSEA_20131008.gmt",
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Build the pathway table and its committed summary.

    Args:
        argv: Command-line arguments, or None to read them from ``sys.argv``.

    Returns:
        0 on success, 1 if an input is missing.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW, help="source data directory")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="where tables are written")
    args = parser.parse_args(argv)

    inputs = inputs_under(args.raw, args.out)
    if inputs.missing:
        for path in inputs.missing:
            print(f"missing input: {path}", file=sys.stderr)
        print(
            "run scripts/download_pathway_data.py, then scripts/filter_reactome_membership.py",
            file=sys.stderr,
        )
        return 1

    resolver = GeneResolver.from_files(
        args.raw / f"hgnc_complete_set_{HGNC_RELEASE}.txt",
        args.raw / f"withdrawn_{HGNC_RELEASE}.txt",
        args.out / "gene_resolution_adjudications.tsv",
    )
    collection = PathwayCollection.from_files(inputs, resolver)

    table = args.out / PATHWAY_TABLE
    write_tsv(table, PATHWAY_COLUMNS, collection.to_rows())

    membership_digest = sha256_file(inputs.reactome_membership)
    committed = args.out / MEMBERSHIP_SUMMARY
    committed_digest = "-"
    if committed.is_file():
        committed_digest = committed_membership_digest(committed.open(encoding="utf-8"))
    log_path = args.out / RESOLUTION_LOG
    log = log_non_resolving(log_path.open(encoding="utf-8")) if log_path.is_file() else {}

    checks = sanity_checks(collection, inputs, membership_digest, committed_digest, log)
    html = sum(
        1
        for p in collection.of_source("reactome")
        if p.description_source and re.search(r"</?[a-zA-Z][^>]*>", p.description_source)
    )
    obsolete = sum(
        1
        for p in collection.of_source("go")
        if p.description_source and p.description_source.startswith("OBSOLETE.")
    )
    summary = build_summary(
        collection, sha256_file(table), membership_digest, checks, html, obsolete
    )
    write_tsv(args.out / SUMMARY_TABLE, SUMMARY_COLUMNS, summary)

    print(f"{len(collection)} pathways -> {table}")
    for source in SOURCES:
        pathways = collection.of_source(source)
        described = sum(1 for p in pathways if p.description_source)
        degraded = sum(1 for p in pathways if p.degradation != "ok")
        genes = frozenset().union(*(p.genes for p in pathways))
        print(
            f"  {source:9s} {len(pathways):6d}  described {described:6d}"
            f"  degraded {degraded:4d}  genes {len(genes):6d}"
        )
    failed = [check for check in checks if check.status == "FAIL"]
    for check in failed:
        print(f"  FAIL {check.key}: {check.measured} (expected {check.expected})", file=sys.stderr)
    print(f"{len(checks) - len(failed)}/{len(checks)} sanity checks pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
