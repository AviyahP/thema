"""Adjudicate every ``(symbol, pathway)`` row of Reactome's GMT against its identifier exports.

``ReactomePathways.gmt`` names members by display name, and Reactome display names are not unique
across entities -- ``PB1`` is human PBRM1 in two pathways and influenza polymerase PB1 in
twenty-five others. The GMT remains the source of pathway membership; the identifier exports are
used only to decide individual rows.

A five-test cascade runs over every row, and the first test that fires decides it:

======  =========================================================  ==================
test    condition                                                  outcome
======  =========================================================  ==================
0       the symbol resolves to no HGNC record at all               discard
1       the gene's id is paired with *this* pathway in an export   keep ``confirmed``
2       the id appears for *other* R-HSA pathways but not this     discard
3       the id appears *nowhere*, and the symbol was the approved  keep ``gmt_fill``
4       the id appears *nowhere*, matched via a non-approved tier  discard
======  =========================================================  ==================

The asymmetry between tests 2 and 3 is the whole design: **absence of evidence is evidence of
absence only where the evidence would have been visible.** If the exports cover a gene at all, then
their silence about this pathway is a positive statement that the display name meant something
else. If they never mention the gene -- immunoglobulin segments, miRNAs, tRNAs, most pseudogenes --
their silence carries no information, and the official symbol is trusted instead.

One exception is carved out of test 2, for genes HGNC places on the mitochondrial genome: mtDNA
protein, rRNA and tRNA genes are excised from a single polycistronic transcript, so Reactome lists
them jointly as participants in transcript-processing pathways while the identifier exports omit
the proteins there -- which makes test 2's coverage assumption false for this locus specifically.
Such rows keep with provenance ``mtdna_exempt`` rather than ``gmt_fill``, so the unconfirmed keeps
stay individually visible. The exemption is keyed on HGNC's ``location`` field, not on the ``MT-``
symbol prefix: the prefix is a naming convention, the location is the fact the exemption rests on.
"""

import argparse
import csv
import hashlib
import sys
from collections import Counter, defaultdict, deque
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from thema.data.genes import GeneRef, GeneResolver

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = REPO_ROOT / "data" / "raw"
DEFAULT_OUT = REPO_ROOT / "data"
HGNC_RELEASE = "2026-07-07"

#: Root of Reactome's Infectious disease subtree, used only to break down the test-2 discards.
INFECTIOUS_ROOT = "R-HSA-5663205"

#: HGNC's ``location`` value for the mitochondrial genome; the basis of the test-2 exemption.
MITOCHONDRIAL_LOCATION = "mitochondria"

EXPORTS = ("NCBI2Reactome_All_Levels.txt", "Ensembl2Reactome_All_Levels.txt")
EVIDENCE_ALL = frozenset({"TAS", "IEA"})

KEPT_COLUMNS = (
    "pathway_id", "pathway_name", "symbol", "hgnc_id", "approved_symbol",
    "match_type", "provenance",
)
DISCARD_COLUMNS = (
    "pathway_id", "pathway_name", "symbol", "hgnc_id", "match_type", "test", "reason",
)
SUMMARY_COLUMNS = ("section", "key", "value", "note")

TEST_LABELS = {
    0: "discard - symbol resolves to no HGNC record",
    1: "keep confirmed - id paired with this pathway",
    2: "discard - id covered by exports, absent here",
    3: "keep gmt_fill - id absent from exports, approved symbol",
    4: "discard - id absent from exports, non-approved match",
}

# Stated expectations, checked and reported rather than assumed. Where measurement disagrees the
# summary records FAIL with the measured value, so a divergence stays visible instead of silently
# becoming the new expectation.
EXPECT_KEPT_PATHWAYS = {"PB1": {"R-HSA-9932444", "R-HSA-4839726"}}
EXPECT_ALL_DISCARDED = ("SCP", "HN", "P", "NP", "TRS1", "TRM3")
EXPECT_ALL_KEPT_TEST3 = ("MT-TV", "MIR142", "IGKC", "MRPL45")


@dataclass(frozen=True, slots=True)
class Decision:
    """How the cascade ruled on one row.

    Attributes:
        test: Which test fired, 0 through 4.
        keep: Whether the row survives.
        provenance: ``confirmed`` or ``gmt_fill`` for kept rows, empty otherwise.
        reason: Human-readable justification, written to the discard log.
    """

    test: int
    keep: bool
    provenance: str
    reason: str


def classify(
    ref: GeneRef | None,
    pathway_id: str,
    gene_ids: frozenset[str],
    pairs: frozenset[tuple[str, str]] | set[tuple[str, str]],
    covered: frozenset[str] | set[str],
    *,
    mitochondrial: bool = False,
) -> Decision:
    """Apply the five-test cascade to one ``(symbol, pathway)`` row.

    Args:
        ref: The resolved gene, or None if the symbol resolved to nothing.
        pathway_id: Reactome stable id of the pathway the row belongs to.
        gene_ids: The gene's Entrez and Ensembl identifiers, from HGNC.
        pairs: ``(identifier, pathway_id)`` pairs present in the exports.
        covered: Identifiers the exports mention for any R-HSA pathway.
        mitochondrial: Whether HGNC places this gene on the mitochondrial genome, which
            exempts it from test 2. See the module docstring for why.

    Returns:
        The ruling, including which test fired.
    """
    if ref is None:
        return Decision(0, False, "", "symbol resolves to no HGNC record")
    if any((i, pathway_id) in pairs for i in gene_ids):
        return Decision(1, True, "confirmed", "identifier paired with this pathway")

    is_covered = any(i in covered for i in gene_ids)
    if is_covered and not mitochondrial:
        return Decision(
            2, False, "", "gene is covered by the exports but absent from this pathway"
        )
    if ref.match_type == "approved":
        if is_covered:
            return Decision(
                3, True, "mtdna_exempt",
                "mitochondrial locus exempt from test 2; polycistronic transcript",
            )
        return Decision(3, True, "gmt_fill", "gene absent from exports; current approved symbol")
    return Decision(
        4, False, "", f"gene absent from exports; matched via the {ref.match_type} tier"
    )


def load_exports(
    paths: Iterable[Path], evidence: frozenset[str]
) -> tuple[set[tuple[str, str]], set[str]]:
    """Read the identifier exports into the two sets the cascade consults.

    Both files are unioned and restricted to ``R-HSA-`` pathways; a hit in either passes. No ENSG
    pre-filter is applied, because joining on HGNC's ``ensembl_gene_id`` excludes ``ENSP`` and
    ``ENST`` identifiers automatically.

    Args:
        paths: The export files to read.
        evidence: Evidence codes to accept, normally both ``TAS`` and ``IEA``.

    Returns:
        The ``(identifier, pathway_id)`` pairs, and the set of identifiers covered at all.
    """
    pairs: set[tuple[str, str]] = set()
    covered: set[str] = set()
    for path in paths:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                row = line.rstrip("\n").split("\t")
                if len(row) < 6 or not row[1].startswith("R-HSA-") or row[4] not in evidence:
                    continue
                pairs.add((row[0], row[1]))
                covered.add(row[0])
    return pairs, covered


def load_hgnc(path: Path) -> tuple[dict[str, frozenset[str]], dict[str, str], frozenset[str]]:
    """Index HGNC by the identifiers the exports use, by locus type, and by genome.

    Args:
        path: Path to the pinned ``hgnc_complete_set`` TSV.

    Returns:
        HGNC id to its Entrez and Ensembl identifiers, HGNC id to locus type, and the ids
        HGNC places on the mitochondrial genome.
    """
    identifiers: dict[str, set[str]] = defaultdict(set)
    locus: dict[str, str] = {}
    mitochondrial: set[str] = set()
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            hgnc_id = (row.get("hgnc_id") or "").strip()
            if not hgnc_id:
                continue
            locus[hgnc_id] = (row.get("locus_type") or "").strip()
            if (row.get("location") or "").strip() == MITOCHONDRIAL_LOCATION:
                mitochondrial.add(hgnc_id)
            for column in ("entrez_id", "ensembl_gene_id"):
                value = (row.get(column) or "").strip()
                if value:
                    identifiers[hgnc_id].add(value)
    return {k: frozenset(v) for k, v in identifiers.items()}, locus, frozenset(mitochondrial)


def descendants(relation: Path, root: str) -> frozenset[str]:
    """Collect a pathway and every pathway beneath it in Reactome's hierarchy.

    Args:
        relation: Path to ``ReactomePathwaysRelation.txt``.
        root: Stable id to walk down from.

    Returns:
        The root and all of its descendants.
    """
    children: dict[str, list[str]] = defaultdict(list)
    with relation.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            parent, _, child = line.rstrip("\n").partition("\t")
            if parent.startswith("R-HSA-") and child.startswith("R-HSA-"):
                children[parent].append(child)
    seen: set[str] = set()
    queue = deque([root])
    while queue:
        node = queue.popleft()
        if node in seen:
            continue
        seen.add(node)
        queue.extend(children.get(node, ()))
    return frozenset(seen)


def read_gmt_rows(path: Path) -> list[tuple[str, str, str]]:
    """Read the GMT as one row per member, preserving pathway order.

    Args:
        path: Path to ``ReactomePathways.gmt``.

    Returns:
        ``(pathway_id, pathway_name, symbol)`` per membership row.
    """
    rows: list[tuple[str, str, str]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 3:
                continue
            name, pathway_id = fields[0].strip(), fields[1].strip()
            for entry in fields[2:]:
                symbol = entry.strip()
                if symbol:
                    rows.append((pathway_id, name, symbol))
    return rows


def write_tsv(path: Path, columns: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
    """Write a TSV atomically, header first.

    Args:
        path: Destination.
        columns: Header row.
        rows: Rows in final order.
    """
    text = "\n".join(["\t".join(columns), *("\t".join(r) for r in rows)]) + "\n"
    tmp = path.with_name(path.name + ".part")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def sha256_file(path: Path) -> str:
    """Return the hex sha256 digest of a file, read in chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 16):
            digest.update(chunk)
    return digest.hexdigest()


def _sanity(
    rulings: Sequence[tuple[str, str, Decision]],
) -> list[tuple[str, str, str, str]]:
    """Check the stated expectations and report each as measured, pass or fail.

    A divergence is recorded with its measured value rather than being absorbed into a new
    expectation, so a rule change and a spec error stay distinguishable.

    Args:
        rulings: ``(pathway_id, symbol, decision)`` for every row.

    Returns:
        ``(key, measured, expected, status)`` rows for the summary.
    """
    by_symbol: dict[str, list[tuple[str, Decision]]] = defaultdict(list)
    for pathway_id, symbol, decision in rulings:
        by_symbol[symbol].append((pathway_id, decision))

    out: list[tuple[str, str, str, str]] = []
    for symbol, expected_kept in EXPECT_KEPT_PATHWAYS.items():
        rows = by_symbol.get(symbol, [])
        kept = {p for p, d in rows if d.keep}
        status = "pass" if kept == expected_kept else "FAIL"
        out.append((
            f"{symbol} kept in",
            f"{len(kept)} ({'; '.join(sorted(kept)) or 'none'})",
            f"{len(expected_kept)} ({'; '.join(sorted(expected_kept))})",
            status,
        ))
        out.append((
            f"{symbol} discarded in",
            str(len(rows) - len(kept)),
            "25",
            "pass" if len(rows) - len(kept) == 25 else "FAIL",
        ))
    for symbol in EXPECT_ALL_DISCARDED:
        rows = by_symbol.get(symbol, [])
        kept = [p for p, d in rows if d.keep]
        status = "pass" if rows and not kept else "FAIL"
        measured = f"{len(rows)} rows, {len(kept)} kept" + (
            f" ({'; '.join(sorted(kept))})" if kept else ""
        )
        out.append((f"{symbol} all discarded", measured, "0 kept", status))
    for symbol in EXPECT_ALL_KEPT_TEST3:
        rows = by_symbol.get(symbol, [])
        tests = sorted({d.test for _, d in rows})
        status = "pass" if rows and tests == [3] else "FAIL"
        out.append((
            f"{symbol} all kept via test 3",
            f"{len(rows)} rows, tests {tests}",
            "all test 3",
            status,
        ))
    return out


def build_summary(
    rulings: Sequence[tuple[str, str, Decision]],
    refs: dict[str, GeneRef | None],
    locus: dict[str, str],
    infectious: frozenset[str],
    kept_digest: str,
    evidence: frozenset[str],
) -> list[tuple[str, str, str, str]]:
    """Assemble the committed record of this run.

    Args:
        rulings: ``(pathway_id, symbol, decision)`` for every row.
        refs: Resolved gene per symbol.
        locus: HGNC id to locus type.
        infectious: Pathways in the Infectious disease subtree.
        kept_digest: sha256 of the kept-membership table.
        evidence: Evidence codes accepted this run.

    Returns:
        ``(section, key, value, note)`` rows.
    """
    rows: list[tuple[str, str, str, str]] = [
        ("digest", "reactome_membership.tsv", kept_digest, "sha256 of the regenerable kept table"),
        ("input", "hgnc_release", HGNC_RELEASE, ""),
        (
            "input", "evidence_codes", ",".join(sorted(evidence)),
            "TAS+IEA reproduces the shipped GMT",
        ),
        ("input", "gmt_rows", str(len(rulings)), "(symbol, pathway) rows in ReactomePathways.gmt"),
    ]
    tests = Counter(d.test for _, _, d in rulings)
    for test in range(5):
        rows.append(("test", f"{test}", str(tests[test]), TEST_LABELS[test]))
    rows.append(("test", "kept", str(sum(1 for _, _, d in rulings if d.keep)), ""))
    rows.append(("test", "discarded", str(sum(1 for _, _, d in rulings if not d.keep)), ""))

    provenance = Counter(d.provenance for _, _, d in rulings if d.keep)
    for key in ("confirmed", "gmt_fill", "mtdna_exempt"):
        note = (
            "mitochondrial locus exempt from test 2 - unconfirmed keeps, kept visible"
            if key == "mtdna_exempt" else ""
        )
        rows.append(("provenance", key, str(provenance[key]), note))

    fill = Counter(
        locus.get(refs[s].hgnc_id, "?")
        for _, s, d in rulings
        if d.test == 3 and refs.get(s) is not None
    )
    for key, count in fill.most_common():
        rows.append(("test3_locus_type", key, str(count), ""))

    cells: Counter[tuple[str, str]] = Counter()
    for pathway_id, symbol, decision in rulings:
        if decision.test != 2:
            continue
        ref = refs[symbol]
        exact = "exact" if ref is not None and ref.match_type == "approved" else "non-approved"
        where = "infectious" if pathway_id in infectious else "non-infectious"
        cells[(exact, where)] += 1
    for exact in ("exact", "non-approved"):
        for where in ("infectious", "non-infectious"):
            note = (
                "known conservative loss - probable real memberships missing from the "
                "All_Levels rollup, discarded because we prefer to err toward dropping"
                if (exact, where) == ("exact", "non-infectious") else ""
            )
            rows.append(("test2_cell", f"{exact}/{where}", str(cells[(exact, where)]), note))

    for key, measured, expected, status in _sanity(rulings):
        rows.append(("sanity", key, measured, f"expected {expected} [{status}]"))
    return rows


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="filter_reactome_membership.py",
        description="Adjudicate Reactome GMT rows against the identifier exports.",
    )
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW, help="raw data directory")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory")
    parser.add_argument(
        "--evidence",
        choices=("all", "tas"),
        default="all",
        help="evidence codes to accept; 'tas' is the sensitivity slice (default: %(default)s)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the cascade over every GMT row and write the three output tables."""
    args = parse_args(argv)
    raw: Path = args.raw
    evidence = EVIDENCE_ALL if args.evidence == "all" else frozenset({"TAS"})

    required = [
        raw / "ReactomePathways.gmt",
        raw / "ReactomePathwaysRelation.txt",
        raw / f"hgnc_complete_set_{HGNC_RELEASE}.txt",
        *(raw / name for name in EXPORTS),
    ]
    missing = [p for p in required if not p.is_file()]
    if missing:
        for path in missing:
            print(f"missing {path}", file=sys.stderr)
        print("run scripts/download_pathway_data.py", file=sys.stderr)
        return 1

    print("loading HGNC and the identifier exports...", file=sys.stderr)
    identifiers, locus, mitochondrial = load_hgnc(raw / f"hgnc_complete_set_{HGNC_RELEASE}.txt")
    pairs, covered = load_exports((raw / n for n in EXPORTS), evidence)
    infectious = descendants(raw / "ReactomePathwaysRelation.txt", INFECTIOUS_ROOT)
    print(
        f"{len(pairs):,} export pairs, {len(covered):,} covered ids, "
        f"{len(infectious):,} pathways under {INFECTIOUS_ROOT}",
        file=sys.stderr,
    )

    resolver = GeneResolver.from_files(
        raw / f"hgnc_complete_set_{HGNC_RELEASE}.txt",
        raw / f"withdrawn_{HGNC_RELEASE}.txt",
        args.out / "gene_resolution_adjudications.tsv",
    )
    rows = read_gmt_rows(raw / "ReactomePathways.gmt")
    print(f"adjudicating {len(rows):,} membership rows...", file=sys.stderr)

    refs: dict[str, GeneRef | None] = {}
    rulings: list[tuple[str, str, Decision]] = []
    kept: list[tuple[str, ...]] = []
    discarded: list[tuple[str, ...]] = []
    for pathway_id, pathway_name, symbol in rows:
        if symbol not in refs:
            refs[symbol] = resolver.explain(symbol, "reactome").ref
        ref = refs[symbol]
        gene_ids = identifiers.get(ref.hgnc_id, frozenset()) if ref else frozenset()
        decision = classify(
            ref, pathway_id, gene_ids, pairs, covered,
            mitochondrial=ref is not None and ref.hgnc_id in mitochondrial,
        )
        rulings.append((pathway_id, symbol, decision))
        if decision.keep:
            kept.append((
                pathway_id, pathway_name, symbol, ref.hgnc_id, ref.approved_symbol,
                ref.match_type, decision.provenance,
            ))
        else:
            discarded.append((
                pathway_id, pathway_name, symbol, ref.hgnc_id if ref else "-",
                ref.match_type if ref else "-", str(decision.test), decision.reason,
            ))

    kept.sort()
    discarded.sort()
    kept_path = args.out / "reactome_membership.tsv"
    write_tsv(kept_path, KEPT_COLUMNS, kept)
    write_tsv(args.out / "reactome_membership_discards.tsv", DISCARD_COLUMNS, discarded)
    summary = build_summary(
        rulings, refs, locus, infectious, sha256_file(kept_path), evidence
    )
    write_tsv(args.out / "reactome_membership_summary.tsv", SUMMARY_COLUMNS, summary)

    print()
    for section, key, value, note in summary:
        print(f"{section:18} {key:34} {value:>12}  {note}"[:150])
    print()
    print(f"kept {len(kept):,} -> {kept_path}  (gitignored, regenerable)")
    print(f"discarded {len(discarded):,} -> {args.out / 'reactome_membership_discards.tsv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
