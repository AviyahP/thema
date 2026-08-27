# Decisions

A dated log of design decisions for THEMA — what we chose, and why. Append-only: newest entries
go at the bottom, and superseded decisions stay put with a note pointing at the entry that
replaced them.

Format: `## YYYY-MM-DD — <decision>`, followed by a short rationale.

## 2026-08-21 — Name: THEMA

THEMA = Thematic Hierarchical Enrichment Mapping & Analysis. Chosen because it
says what the tool does, is pronounceable, and is Greek for "theme."
Checked for collisions in bioinformatics, GitHub, and PyPI before adopting.
Rejected: THEMIS (collides with a T-cell gene — our users' own search space),
PANTHEON, CANOPY (weaker descriptions of the tool).

## 2026-08-21 — Project scaffold

- **Python 3.12** (`requires-python = ">=3.12"`) — broadest wheel coverage across the
  bioinformatics stack (numpy, scipy, pandas, statsmodels) while still allowing modern typing
  syntax.
- **uv + hatchling, src layout** — `src/thema/` keeps the installed package distinct from the
  repo root, so tests exercise the built package rather than accidentally importing from cwd.
- **ruff enforces the conventions** — the rule set includes `D` (docstrings, google convention)
  and `ANN` (type annotations) so "type hints everywhere, docstrings on public functions" is
  machine-checked rather than review-only. `tests/` is exempt from both.
- **`uv.lock` is committed** — THEMA is a tool, not a library dependency; reproducible resolution
  matters more than floating versions.

## 2026-08-21 — Architecture: frozen global ontology first (v1), per-experiment clustering later (v2)

The ontology (embed pathway descriptions → hierarchical clustering → LLM
naming) is built ONCE from database content only, touching no experiment
data, then version-frozen. Statistics run against the frozen release.
Rationale: themes defined before any experiment exists make theme-level
enrichment tests exactly as valid as standard ORA — the alternative
(clustering each experiment's significant pathways, then testing those
themes on the same data) is circular ("double dipping", Kriegeskorte et al.
2009, Nat Neurosci 12:535), and no p-value or FDR computed that way controls
anything. Per-experiment adaptive clustering is deferred to v2 as a
qualitative/exploratory feature. Full derivation and literature survey in
docs/brief.md (D2, D4).

## 2026-08-21 — Hierarchical reporting protocol (three tests)

1. BASIS — EVERY node in the tree is tested on all its genes (no
   significance-gated descent: a parent can be diluted below significance by
   cold siblings while a child is genuinely enriched — gating would prune
   real findings). One BH-FDR family across all basis tests. The basis layer
   is the INFERENCE: it decides which nodes are enriched. The tree is the
   REPORTING structure — results summarized top-down with minimal-node
   logic — never a testing gate.

2. CHILD-UNIQUE (attribution) — for every significant child: enrichment test
   + fold enrichment (with interval) on its unique genes (appearing in no
   sibling under the same parent). Contributing → distinct finding, report
   the child. Not contributing → the child's signal lives in shared genes →
   the PARENT is reported as the finding ("common biology"), the child shown
   as shared-driven detail. Construction: conditional re-test per
   fgsea::collapsePathways (Korotkevich et al., bioRxiv 060012) and SetRank
   (Simillion et al. 2017, BMC Bioinformatics 18:151) — never a difference
   of enrichment scores, which has no null distribution.

3. PARENT-BEYOND (attribution) — for every parent of significant children:
   enrichment test + effect size on genes appearing in non-significant
   children but in NO significant child. Contributing → the parent holds
   additional signal beyond its enriched children (e.g. branches too weak to
   clear alone) — report the parent as carrying "more." Construction:
   conditional hyperGTest, GOstats (Falcon & Gentleman 2007, Bioinformatics
   23:257).

Layer rules. Attribution (tests 2–3) decides LABELS, not discoveries — but
labels are still threshold decisions, so attribution p-values receive their
own BH correction across all test-2/test-3 values in a run: a separate
hypothesis family from the basis layer, each family its own unit of
interpretation. Stated caveat: the attribution family's membership is
selected by the basis results; the exact correction for testing within
data-selected families is Benjamini & Bogomolov 2014 (JRSS-B 76:297) — the
planned phase-2 upgrade. Every attribution test is accompanied by an effect
size (small gene sets are underpowered — the reason test 2 never gates a
child's significance, which test 1 decides on the full set). When distinct
children are reported and test 3 shows nothing, the parent appears as a
grouping line with no claim of its own.

## 2026-08-21 — FDR under dependence: BH default, BY switch, permutation audit

(PROVISIONAL — final decision deferred until implementation; revisit at Phase 4)

Honest status of BH on our tree: its guarantee holds under independence or
PRDS (Benjamini & Yekutieli 2001, Ann. Statist. 29:1165); PRDS is NOT proven
for nested overlapping set tests. BH on such families is field standard
(all GO tooling) and empirically robust under positive dependence, but not
theoretically guaranteed here. Policy:

- BH is the default (field-comparable, full power).
- BY available as a switch: guaranteed under ANY dependence, at ~ln(m)
  stringency cost (~7x for ~500 nodes). Kept for users who want a
  theorem-backed number; otherwise dominated by the audit below (worst-case
  insurance is for when measurement is impossible; ours is cheap).
- EMPIRICAL-FDR AUDIT: random gene lists of matched size run through the
  entire tree (~10^3 draws) give the exact joint null of all node statistics
  under the gene-sampling null, dependence included (cf. g:Profiler's
  g:SCS). Agreement with BH validates BH for this tree; disagreement ships
  as the honest number. GSEA tier: same audit by permuting rankings;
  vectorized cost is minutes (v1-stretch).

Known limits, disclosed: (a) calibration is exact under the COMPLETE
gene-sampling null; partial-null spillover (null nodes overlapping truly
enriched ones receive signal through shared genes) is a semantics question
of the competitive null, handled by the attribution layer, stated in the
README; (b) FDR is an average-case guarantee — under strong dependence the
realized false-discovery fraction spreads around it (Owen 2005); (c) Monte
Carlo resolution ~1/draws; (d) the urn-model/co-expression caveat of all
ORA is untouched by any of this (Goeman & Bühlmann 2007, Bioinformatics
23:980); background must be the measured universe (Wijesooriya et al. 2022,
PLoS Comput Biol 18:e1009935); DEG-cutoff dependence avoided by preferring
the ranked-list (GSEA) input tier.

DEFINITIVE CHECK (phase-2 evaluation suite, first item): planted-truth
simulation — synthetic DEG lists with chosen truly-enriched nodes through
the full pipeline; measure realized FDP vs claimed FDR and attribution
error rates, end to end.

## 2026-08-21 — Protocol authorship note

Protocol designed by Aviyah, 21 Aug 2026, converging over five iterations
from a leftover-test draft (topGO elim heritage: Alexa et al. 2006,
Bioinformatics 22:1600). Key simplifications and corrections along the way,
all hers: remove only child-SPECIFIC genes so co-significant siblings'
shared evidence survives; a separate "shared genes" test is unnecessary
(the shared-driven case is inferred from test-2 negatives); attribution
layers need their own multiple-testing correction despite being
descriptive; no significance-gated descent (dilution hides real children);
BH's dependence assumptions challenged → audit-by-permutation policy.

## 2026-08-21 — KEGG: excluded from the public artifact, bring-your-own adapter instead

THEMA's v1 deliverable includes a public, downloadable frozen ontology
containing gene sets — i.e. redistribution. KEGG's data is proprietary
(Kanehisa Laboratories): free to browse academically, restricted to
redistribute; MSigDB flags its KEGG-derived collections with additional
license terms. Shipping KEGG-derived sets in the public artifact would be
exactly the restricted act, so it's excluded — as is BioCarta (similar
terms). Instead, the loader architecture treats sources as pluggable: a
user with KEGG access can run the download with a KEGG option, fetching
under their own acceptance of KEGG's terms, and build a locally-extended
ontology that THEMA never redistributes ("bring-your-own-KEGG"; adapter
itself is v1.1). WikiPathways (CC0, covers much of the same territory) is
the planned v1.1 public addition. Included sources and licenses are
recorded in DATA_LICENSE.md.

## 2026-08-21 — GO restricted to the Biological Process branch

GO is three ontologies in one: Biological Process (BP), Molecular Function
(MF), Cellular Component (CC). THEMA's themes answer "what biology is
happening?" — that is BP's question. MF ("ATP binding") and CC ("nucleus")
describe protein chemistry and location; mixing them into the clustering
would produce category-error themes. The obo parser filters to
namespace: biological_process, and gene sets come from MSigDB's C5:GO:BP
collection only.

## 2026-08-21 — OPEN: embed curated prose as-is vs LLM-normalized (decide in Phase 2)

Curated descriptions differ sharply in register across sources (Reactome
paragraphs, GO one-liners, Hallmark two lines, BTM none). Risk: embeddings
encode style, so raw curated text may cluster partly by SOURCE rather than
biology (Aviyah's catch, 21 Aug 2026). Candidate fix: LLM-normalize all
descriptions to one template, using curated prose as grounding input
(constrains hallucination) rather than as the embedded text. Decision
deferred to a Phase-2 A/B on the 500-pathway set: measure source leakage
(source-prediction accuracy from embeddings; cluster–source stratification)
for as-is vs normalized. Cost of full normalization if chosen: ~10-11k
cached calls, est. $5-15.

## 2026-08-21 — Data download: stdlib urllib, pinned URLs, hashed manifest

`scripts/download_pathway_data.py` fetches all source data into `data/raw/`
(gitignored) and writes `VERSIONS.txt` with URL, fetch date, size and sha256
per file. Four choices worth recording:

**stdlib `urllib`, not httpx/requests.** Keeps `dependencies = []` and leaves
`uv.lock` untouched for what is a one-off acquisition script. The catch: the
default `Python-urllib/3.x` User-Agent is rejected with HTTP 403 by both
reactome.org and release.geneontology.org. Any explicit User-Agent fixes it,
so the script sets one — do not remove it.

**Pinning is per-source, because the sources differ.** GO is pinned to the
dated release directory `2026-08-05` (never `current.geneontology.org`);
note the file's own `data-version` reads `releases/2026-07-26`, and the
script records both. MSigDB is pinned by release string `2026.1.Hs`. BTM is
pinned to a commit SHA. Reactome alone uses `download/current/` — it
publishes no stable per-release path for these files (`download/archive/97/`
exists but does not carry them), so the script instead captures the release
number from ContentService into `reactome_release.txt` and hashes it like
any other artifact.

**BTM source: `github.com/shuzhao-li/BTM`,** file
`BTM/datasets/BTM_for_GSEA_20131008.gmt` at commit `94d5288`. Maintained by
the paper's first author, a plain GMT needing no registration or unpacking,
and content-addressable by commit. Rejected: the release zip `ni.2789-S5.zip`
(a whole tutorial bundle for one file) and the `tmod` R package (needs an R
toolchain).

**`VERSIONS.txt` is a pure function of (source table, files on disk).**
Nothing carries over between runs and nothing re-parses its own prior output:
`fetched` comes from each file's mtime, the Reactome release number is read
back from disk, and GO's data-version is read out of the `.obo`. So an
all-skipped re-run still emits a complete, byte-identical manifest — which
means a plain re-run doubles as a verify pass, and `--only` never truncates
the manifest to the selected group.

Two implementation notes that cost real debugging time. Large transfers from
release.geneontology.org and data.broadinstitute.org are cut short at ~28 MiB;
the length check catches it, and the retry resumes via `Range` guarded by
`If-Range` on the ETag, so a changed file restarts cleanly instead of
splicing two releases together. And `http.client.IncompleteRead` is not an
`OSError` — it must be caught explicitly or a mid-body reset crashes the run.

MSigDB per-gene-set prose lives only in `msigdb_v2026.1.Hs.xml` (221 MB
extracted); the per-collection JSONs carry metadata but no descriptions. The
XML is in the default set — disable with `--skip-msigdb-xml`. Its
`exactSource` field gives each C5 set's GO id, which joins to `go-basic.obo`.

Still open: `DATA_LICENSE.md` (brief §7) is not written yet; `VERSIONS.txt`
now records per-file licenses and is the natural source for it. `VERSIONS.txt`
itself stays gitignored for now — `data/raw/` is excluded as a directory, so
committing it would need the rule rewritten as `data/raw/*` plus a negation.

## 2026-08-24 — Gene identifiers: resolve every source symbol to an HGNC id

All four sources ship symbols, not identifiers, and a union built on symbols
under-counts silently — which matters because a theme's gene set is the union
of its members' genes (D1). Every symbol therefore resolves to an HGNC id
against one pinned release, the dated quarterly `2026-07-07` (HGNC's floating
current-release URL carries no version identifier, so it cannot be pinned by
reference; `2026-07-07` is the most recent quarterly publishing both the
complete set and `withdrawn.txt`, which is needed because the complete set
holds approved records only and `withdrawn.txt` is the sole merge map).
Resolution is two hops: match the symbol with precedence approved > previous >
alias, then validate the resulting id against the release, following a merge
if the record merged. `src/thema/data/genes.py` owns this.

**The resolver refuses rather than guesses.** Ambiguity at the winning tier
returns nothing and is logged with the candidate genes it could not choose
between; a record split across several genes is ambiguous, not a coin flip; a
lower tier is never consulted once a higher one has matched. Those cases are
adjudicated by hand from `data/gene_resolution_log.tsv`, which is committed as
provenance.

One further tier sits below the three symbol tiers: a symbol of the form
`LOC<digits>` is *decoded* rather than matched, since that is NCBI's naming
convention for an uncharacterized locus and the digits are its Entrez Gene id,
which HGNC's complete set already carries. It is a deterministic decoding of a
documented convention rather than a heuristic, and HGNC's Entrez ids are
unique so it cannot be ambiguous; matches are recorded as `match_type=entrez`.
It recovers 30 of BTM's symbols and nothing elsewhere.

**A per-source 2013 "era lens" for BTM was built and then removed**, because
measurement showed its premise was false. Symbol reassignment is real in HGNC
— 229 approved/previous collisions, 102 adopted by their current owner after
2013 — but none of those reach BTM, the only source the lens applied to. BTM's
symbols turn out to come from an Affymetrix annotation build rather than dated
HGNC nomenclature at all (100% of its members are explained by that
vocabulary, and the GMT carries raw `A /// B` probe annotations no HGNC
release has ever emitted), so a dated-nomenclature lens was a category error.
Its only measurable effect was declining four names HGNC approved after 2013.
Removing it also removed the multi-snapshot machinery that existed to serve
it. Multi-mapping probe entries are still split and each component resolved,
flagged in the log so a strict mode can drop them later.

**Non-human and non-gene members are excluded from matching, not from the
record.** Reactome contributes ~396 such entries — 367 pathogen proteins (HIV,
HCMV, RSV, *E. coli*, Mtb), 8 whole-organism genome labels, 14 generic family
labels (`5S rRNA`), 3 isoform labels (`FGFR2b`), 4 unidentifiable. HGNC
registers human genes only, so none resolve. This is correct rather than
lossy: a human experiment cannot measure HIV `gag`, so retaining such members
would enlarge a pathway's gene set with genes that can never match a user's
data — inflating the test's denominator while contributing nothing to its
numerator, and biasing enrichment toward under-detection. Enrichment analysis
restricts gene sets to the measured universe regardless; we do it once at
build time. Every `Pathway` retains its source's original symbols, so nothing
is discarded from the record, and clustering is unaffected because themes are
built from descriptions rather than gene lists.

Seven BTM symbols are pre-genomic cDNA clone-library catalogue numbers —
`DKFZp451A211`, `DKFZp779M0652` (German Cancer Research Center), `FLJ35409`
(NEDO Full-Length Japanese), `KIAA1659` (Kazusa Institute), `MGC31957`,
`MGC5566` (Mammalian Gene Collection), `PRO2012`. Each names a clone rather
than a gene and encodes no identifier to decode, so no resolution route exists
short of a clone-registry or probe-annotation lookup. They are recorded as
unmapped and retired from further recovery attempts.

Two facts about Reactome, established by inspection during this triage and
worth recording because both are counter-intuitive. **A Reactome pathway's
species tag describes its clinical context, not its members' species:**
*Action of antimicrobials* is tagged *Homo sapiens* and its entire membership
is bacterial (`16S rRNA`, `gyrA`, `gyrB`, `mrcB`, `qnr`, `rrsA`), because it
models the bacterial machinery an antibiotic acts on. Species tags therefore
cannot be used to decide whether a member is human. **And unresolvable entries
fall into three distinct kinds**, each needing a different judgment: non-human
proteins (pathogen genes); Reactome Set or Complex *names*, whose member
proteins are usually already listed individually in the same pathway
(`HSP70`); and unreviewed UniProt fragments whose gene-name field holds a
generic string with no HGNC assignment (`IGLV` → A2NXD2, a 117-aa fragment
Reactome labels lambda while UniProt describes it as kappa). Only the first
kind is settled policy; the other two are judged case by case and open items
are tracked in the debt log.

Two further recovery tiers sit below the symbol tiers, each a deterministic
rule rather than an inference. An **isoform strip** removes a trailing `.N` or single trailing lowercase letter
and accepts the result only if the stem resolves at the approved tier
(`FGFR2b`→FGFR2, `ROBO3.1`→ROBO3); nothing is stripped speculatively, and the
stem guard yields zero false positives across all unmapped symbols. And
`data/gene_resolution_adjudications.tsv` is the hand-maintained authority for
ambiguous cases: it overrides the ambiguity refusal *and nothing else* — a
clean tier match is never consulted against it. An Ensembl decode was
considered and rejected: the only members carrying an `ENSG` id are
`7SL RNA (ENSG00000222619)` and `(ENSG00000222639)`, Ensembl-only SRP RNA loci
absent from every column of the HGNC release, so the tier could never fire.
They stay unmapped.

**Collective labels are not expanded, on the correct grounds.** An earlier
rule — expand only if the genes would appear in the input assay — was
withdrawn: enrichment already restricts gene sets to the measured universe, so
a build-time discard merely bakes one assay's assumptions into a frozen
artifact where the per-user restriction would have adapted. The real reason is
uncertainty of reference: a family or Set label (`5S rRNA`, `HSP70`) does not
reliably mean every member, and expanding one asserts membership we cannot
verify.

**Reactome's infection pathways carry short pathogen protein names that
collide with human gene aliases, and pathway context reliably misleads.**
Verified cases: `E1` is HPV18's replication protein (not a ubiquitin-activating
enzyme, despite sitting in interferon pathways), `TRM1` is an HCMV protein
(UniProt F5HC79, not a tRNA methyltransferase), `CVC1`/`CVC2` are HCMV capsid
vertex components. Each was initially misread as human by inference from
neighbouring pathways; each was settled only by opening the record. Unresolved
entries therefore fall into four kinds, not three: non-human proteins; Set or
Complex container names; unassigned UniProt fragments; and human proteins HGNC
does not register (`ACOT7L`, `HSBP2`, both in human metabolic and heat-shock
pathways).

## 2026-08-27 — Pathway loader: one record per pathway, nothing filtered at load

`src/thema/data/pathways.py` turns all four sources into one `Pathway` record — the
input the clusterer embeds. 10,817 pathways: Reactome 2,883, GO:BP 7,538, Hallmark 50,
BTM 346, over a union of 18,984 genes. `scripts/build_pathways.py` writes the
regenerable `data/pathways.tsv` and the committed `data/pathways_summary.tsv` that pins
its sha256, the same pattern as the membership cascade.

**Two description fields, both permanent.** `description_source` holds curated prose as
the source publishes it; `description_generated` is reserved for LLM-normalized prose and
is null everywhere for now. This is the schema the 2026-08-21 OPEN entry needs: the
registers really do differ by an order of magnitude — Reactome summations run to a median
of 809 characters, GO definitions 143, Hallmark 58, BTM none — so embeddings may cluster
partly by source. Holding both fields at once lets the clusterer run twice and the
question be measured rather than argued.

**Nothing is filtered at load time, and that is the load-time rule.** Every pathway is
loaded however degraded, and `degradation` records what happened: `ok`, `depleted`
(>50% of members lost), `empty_after_resolution` (had members, none survived),
`no_source_members` (never had a GMT row at all). The last is deliberately not folded
into the third: never having gene content is a different fact from losing it. Reactome:
2,800 / 36 / 32 / 15; every other source is wholly `ok`. The rationale is that THEMA
clusters on descriptions, so a gene-depleted pathway is still a valid ontology node,
while gene content matters at the enrichment stage — where a zero-gene pathway cannot
reach significance and is excluded there anyway. Filtering here would bake a
statistics-layer judgement into the representation layer, and the two layers do not want
the same rule. The 10–500-gene bound this log records for C5:GO:BP is therefore *not*
applied by the loader either; it belongs to the ontology build, where it can be varied.

**The degradation is not damage.** 65 of the 68 Reactome pathways losing more than half
their members, and 101 of the 110 losing more than a quarter, are in the Infectious
disease subtree — pathogen machinery HGNC cannot register, exactly what the 2026-08-24
non-human-member policy predicts. *Uncoating of the HIV Virion* keeps 1 gene of 8.

**`text_availability` — `described` / `name_only` / `no_usable_text`.** BTM alone is not
`described` (259 / 87). 87 of its modules are named `TBA`, so they carry neither prose nor
a real title and cannot be expanded from a name at all; the split names the three
questions downstream code actually asks. Deliberately no length-graded tier for
Hallmark's terseness: description length is already a number the summary reports, and a
threshold frozen into an enum is worse than the count.

**Per-source description provenance, all confirmed from the files rather than assumed.**
Reactome: `pathway2summation.txt`, 100% coverage. GO: the obo `def:` line, joined through
`exactSource` in `c5.go.bp.<release>.json` — all 7,538 sets carry a GO id and all 7,538
join, so the 221 MB XML is not needed for GO at all. Hallmark: `DESCRIPTION_BRIEF` in
`msigdb_<release>.xml` — chosen not as the richer of two options but as the only prose
that exists, since neither MSigDB JSON has a description field and `DESCRIPTION_FULL` is
empty for all 50. BTM: none exists; its GMT column two is a dead `mummichog.org` URL, the
module id re-encoded.

**MSigDB's XML is not well-formed and cannot be parsed as XML.** Attribute values carry
raw unescaped `<` (`EXACT_SOURCE="Table 3S: fold change (log2) < 0"`), and
`xml.etree.ElementTree` raises `ParseError` on line 330 — `iterparse` included, so
streaming does not rescue it. It is strictly one self-closing `<GENESET/>` per line
(35,361), so `read_msigdb_descriptions` scans attributes line by line and reads the file
in 0.3 s. It matches `STANDARD_NAME` first and skips unwanted lines, because a blanket
attribute scan would materialise every `MEMBERS` list to reach fifty descriptions. The
regression test proves the fixture still defeats `ElementTree` before showing the reader
succeeds, so it fails loudly if MSigDB ever ships a valid file.

**Four smaller decisions, each recorded because the alternative looked reasonable.**
Reactome names come from `ReactomePathways.txt` stripped and from nowhere else — 28 human
names carry trailing whitespace, 11 are shared by two pathways, and the GMT (which
`reactome_membership.tsv` inherits) disambiguates 17 by appending `_<id>`, which would go
straight into an embedding. `R-HSA-166016` has two summation rows and they are joined in
file order, because a plain dict assignment silently keeps the last. BTM's `source_id` is
the module id parsed from the trailing parenthesis, matched as `[MS][\d.]*` because twelve
modules are surface signatures `S0`–`S11` that a pattern of `M\d+` would silently drop;
each parsed id is confirmed against the id in its own URL. And the 124 GO sets whose term
this release flags obsolete are kept verbatim, markers and all — GO writes `obsolete` into
the name and `OBSOLETE.` into the definition, which makes them an unusually clean worked
example of the source-specific token normalization is supposed to erase.

**Two cross-checks, because two files can quietly disagree about one fact.** The build
re-digests `reactome_membership.tsv` and compares it to the digest the cascade committed,
so a stale or differently-flagged cascade output cannot be built on unnoticed. And the
symbols this build drops are compared against those `data/gene_resolution_log.tsv` records
as resolving to nothing — same resolver, same GMTs, same HGNC release, so they must agree.
They do exactly: go 15/15, hallmark 1/1, btm 46/46, zero differing. Reactome is excluded
by design and the summary says so: the cascade discards rows the resolver would keep, so
the two are not measuring one thing.

**The sanity block states where its expectations came from.** Every `expected N` is the
planning-time measurement of this same data, not an independent source, so a `[pass]`
means the build reproduces that measurement — not that the number is right. One summary
row says this, so the block cannot later be read as validation. It has already earned its
keep: the expectation of zero verbatim cross-source name collisions was measured on raw
GMT names and is 18 after loading, because BTM's loader strips the module id its names end
in. 94 collisions after normalizing, 0 in the source files as shipped — the redundancy
THEMA exists to collapse is largely invisible to string matching.

**Two new modules rather than one.** `formats.py` holds the GMT, OBO and MSigDB readers —
the same syntax/semantics seam `genes.py` draws between `parse_complete_set` and
`GeneResolver` — and its readers take `lines: Iterable[str]` rather than `text: str`,
because a 221 MB file should not become a 440 MB string. The OBO reader also carries GO's
`is_a` edges, which nothing uses yet and which the reference-hierarchy evaluation will.
`tables.py` holds `write_tsv`, `sha256_file` and the TSV cell conventions: those helpers
were already copy-pasted across three scripts and had begun to drift, and a fourth copy
would be the one whose byte behaviour is hashed into a committed file. The existing copies
are left untouched and a test pins the two writers against each other byte for byte.
