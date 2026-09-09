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

**Closed 2026-08-29** by *Description normalization* below: normalize, and embed
the generated prose. The as-is arm is not lost -- `description_source` is retained
on every row, so the A/B this entry specifies is still a column away. The $5-15
estimate was optimistic; the measured figure is recorded in the closing entry.

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

## 2026-08-29 — Description normalization: one generated description per pathway, genes always shown

Every pathway gets one LLM-written `description_generated` at a consistent length and register.
The reason is a measurement rather than a worry: native descriptions run to a median of 809 / 143 /
58 / 0 characters across reactome / go / hallmark / btm, so embedding them as shipped risks
clustering by writing style rather than by biology — the exact failure THEMA claims to fix. This
closes the 2026-08-21 OPEN entry. The A/B that entry specified still runs, because
`description_source` is retained on every row and the as-is arm is a column away.

**The model may and should use world knowledge.** Native descriptions are often too terse to carry
thematic signal, and surfacing that context is the reason to use an LLM rather than truncating text.
Where a native description exists it anchors the CONTENT — the result must stay faithful to it — but
the model may extend it.

**One prohibition, and it is narrow: no reference to a specific database entry.** Forbidden are GO /
R-HSA / HALLMARK identifiers and naming another pathway or term as a database object ("the Reactome
pathway X", "the GO term Y"). Describing functional relationships in ordinary biological language is
*wanted* — "a subtype of apoptosis", "part of cell cycle control", "downstream of interferon
signalling" — because that is thematic content, not a recited edge. The reason for the prohibition
is that models have memorised GO and Reactome, and the hierarchy-recovery check is only interpretable
if the descriptions do not state the answer. A mechanical validator flags both families over the
output and reports the count; nothing is silently rewritten, because a rewrite would hide the rate at
which the prompt fails. The validator deliberately does *not* match bare "hallmark": "a hallmark of
cancer" is ordinary English and matching it would make the check useless.

**The source database is not shown to the model.** It must not know whether it is looking at a
Reactome, GO, Hallmark or BTM entry — telling it invites source-specific register, which is precisely
what normalization exists to remove.

**The gene list is shown for every pathway, not only those lacking a description.** It is what the
pathway actually *is* for enrichment purposes, it disambiguates vague names, it grounds the model
against hallucination, and the model may use it to derive thematic context and extend the
description. The full list is always sent: no truncation and no subsetting. The largest set is 2,612
genes, a few thousand tokens, and any truncation rule would hand the model a biased sample of exactly
the pathways where the sample matters most. `genes_shown` records the count on every row, so
"nothing was truncated" is a number rather than a claim.

**Consequence, recorded plainly.** Descriptions written with genes in view partly re-encode gene
overlap, and gene-overlap clustering is our baseline comparator. THEMA v1 is therefore a HYBRID
text-and-membership method, not a pure text method, and must be described that way wherever it is
compared to that baseline.

**Length: 90–130 words, target ~110.** Stated in the prompt, measured by the validator, never
enforced by truncation. The range is set from both ends of the register spread it exists to close. It
sits above GO's 143-character median and Hallmark's 58, so those sources genuinely gain content
instead of being restated; and below Reactome's 809-character median, so Reactome is compressed
rather than left where it is. Normalization means every source moves, not only the poor ones. About
110 words is roughly 150 tokens, inside BioLORD-2023's 512-token window with no truncation for any
pathway — and truncation is the thing to avoid above all, because a length-dependent cutoff would
silently reintroduce exactly the bias this entry exists to remove. It is enough for name, specific
purpose, and general processes in three or four sentences, and short enough that a model with nothing
further to say must stop rather than pad; padding is where filler and hallucination enter, which is
the risk the 87 TBA modules invite. It is a deliberate step up from the 2024 prototype's ~75 words,
which expanded names only and never had to absorb 809 characters of curated prose.

**The prompt asks the model to repeat the pathway name**, so the description stays anchored to its
subject, and the validator checks that it did — a name echo is cheap to measure and its absence is
the earliest sign of drift.

**Provenance on every row**, so a description's inputs can be read off the table rather than inferred:
`description_generated_from` is `description+name+genes` (10,471 rows), `name+genes` (BTM's 259) or
`genes` (BTM's 87 TBA modules), mapping one-to-one from `text_availability`; plus `genes_shown`,
the model id and the prompt version.

**47 Reactome pathways have no genes at all** — 32 `empty_after_resolution`, 15 `no_source_members`.
All 47 are `described`, so they are recorded as `description+name+genes` with `genes_shown = 0`
rather than earning a fourth enum value. The count carries the fact, for the same reason the loader
entry refused a length-graded `text_availability` tier: a number in the summary beats a threshold
frozen into a vocabulary. The summary reports the 47 explicitly so the row cannot be misread.

**The output is COMMITTED, and this is the first build artifact that is.** `data/pathways.tsv` and
`data/reactome_membership.tsv` are gitignored because anyone can regenerate them byte-identically
from pinned inputs. Generated descriptions cannot: they are LLM output, non-reproducible and not
free, and a user cloning THEMA must get them and be able to build on them. The gitignore pattern
therefore applies only to tables that are a deterministic function of pinned inputs, and
`data/pathway_descriptions.tsv` is a committed *input* to the regenerable table rather than a column
inside it — the same shape as `reactome_membership_discards.tsv`. Its summary carries the digest and
the batch ids of the run that produced it, per-source and provenance counts, validator counts and the
length distribution.

**Resumability, because 10,817 calls will be interrupted.** Calls are cached by (pathway key, prompt
version, model), so a rerun regenerates nothing already done and a prompt change invalidates cleanly
rather than silently mixing two prompt versions in one file. The cache is an append-only JSONL ledger
under the already-gitignored `data/cache/`, holding full response metadata — usage, stop reason,
model, request id, batch id — because the committed table alone would discard the token counts the
summary needs to report what the run actually cost.

## 2026-08-29 — Evaluation flagship: low-overlap recovery, not hierarchy recovery

The headline structural claim is no longer hierarchy recovery. It is **low-overlap recovery**: among
pathway pairs curators declare related — reactome2go being the primary source — stratified by
gene-set Jaccard, what fraction does THEMA co-cluster versus gene-overlap clustering? In the
low-overlap band gene-overlap approaches zero by construction, and that gap is the product. A tool
that only recovers pairs which already share genes has automated nothing a Jaccard threshold could
not do.

**Hierarchy recovery demotes to a validity floor**, with two caveats that have to travel with every
number it produces: the curators wrote both the prose and the hierarchy, so recovery is partly "the
text encodes the tree"; and the model has memorised the hierarchy, which is why the normalization
entry above forbids reciting database identifiers at all. A floor is still worth having — failing it
would be disqualifying — but it is not evidence of discovery.

This reorders `docs/eval-plan.md` §2, which currently names reference-hierarchy recovery (2a)
"primary" and cross-database merging (2b) second. The stratification by Jaccard is new to both: 2b as
written asks whether mapped pairs co-cluster more than random pairs, which a gene-overlap baseline
can also pass. Stratifying is what separates the two methods.

**Nothing is built for this now.** It is recorded so the build does not foreclose it — concretely,
that means keeping `description_source` alongside `description_generated`, keeping the full gene sets
per pathway, and keeping the pathway keys stable, all of which the current schema already does.

## 2026-08-29 — `anthropic` as the first runtime dependency, pinned, confined to one module

`anthropic==1.2.0` is now a runtime dependency — the project's first. Pinned exactly rather than
floored, and carried in `uv.lock`, because this phase's output is committed and cannot be regenerated
for free, so the client that produced it should be identifiable rather than "whatever resolved that
day".

**The zero-dependency state was descriptive, not chosen.** Everything until now was file parsing,
which stdlib handles; there was never a dependency worth adding. That changes here because the tool
now calls an external API, and hand-rolling batch submission, polling, result streaming and retry
belongs nowhere near the one phase whose output is committed, costs money and cannot be regenerated
for free. The invariant was also going to end within a phase or two regardless: embedding and
clustering need numpy, scipy and a sentence-transformer model.

**The SDK is confined to `src/thema/llm.py`.** Every other module stays stdlib and testable without
it. Isolation of the third-party surface is the real benefit the zero-dependency state was buying,
and it should survive the state. A test walks the sources and asserts `anthropic` is imported in
exactly one file, so this is machine-checked rather than a convention that quietly erodes — the same
move `tests/test_tables.py` makes for the duplicated TSV writers.

Supersedes the `dependencies = []` invariant referenced in the 2026-08-21 downloader entry. That
entry's other content stands, and `download_pathway_data.py` continues to use stdlib urllib.

## 2026-09-09 — `--smoke`: a stratified 17% subset, and a spend gate on every mode that bills

`data/pathway_descriptions.tsv` has never been generated. Going straight to `--full` would commit
the whole budget before anyone has seen a tree, so `--smoke` generates a reproducible stratified
subset first — enough to build the clusterer against and read a tree, at a fraction of the cost.

**The selection is a function of pinned inputs and a fixed seed, and nothing else.**
`SMOKE_FRACTION = 0.15`, `SMOKE_SEED = 0`, `SMOKE_FLOOR = 3`; each stratum contributes
`max(floor, round(fraction * size))`. Every candidate pool is sorted by pathway key before it is
sampled, so a clean clone draws the same subset — pinned by a test that shuffles the collection and
compares. Measured: **1,844 of 10,817 (17.0%)** — reactome 515/2,883, go 1,209/7,538, hallmark
50/50, btm 70/346, with 29/29 Reactome branches, 19/19 GO strata, 94/94 collision groups, 13 BTM TBA
modules and 19 obsolete GO terms.

**Four stratifications.** Reactome by top-level branch (29, derived from
`ReactomePathwaysRelation.txt`, both endpoints filtered to `R-HSA-`); GO:BP by level-1 branch, plus
one bucket for the 124 obsolete terms GO has detached from the DAG; BTM split into named and `TBA`;
Hallmark not stratified and **drawn whole** — 50 sets against Reactome's 2,883 costs almost nothing
and it is the coarsest, most-used collection there is.

**Correction to an earlier figure: this GO release has 18 level-1 branches, not 34.** `GO:0008150`
has exactly 18 direct `is_a` children in `go-basic.obo` (`data-version: releases/2026-07-26`), and
all 18 carry at least one of our terms. Coverage is 18 of 18. The 34 came from an earlier session
and was never re-derived; 18 is measured.

**The ancestor walk accumulates ALL ancestors inclusively.** A walk returning only terminal roots
intersects the level-1 set emptily — every path ends at `GO:0008150` itself, never at one of its
children — which would collapse all 7,538 GO terms into one stratum while reporting no error, i.e.
silently produce exactly the homogeneous sample stratification exists to prevent. There is a named
regression test.

**Multi-branch nodes are filed into the LARGEST branch they reach, ties broken on lowest id.**
Neither hierarchy is a tree: 33 Reactome pathways reach two roots and 1,630 GO terms reach two or
more level-1 branches. Above the floor, filing into the largest or the smallest gives identical
expected unique-member coverage; they differ only where the floor bites, which is the small
branches. There, filing shared terms into a small pile spends its quota on generalists that also
live in the mega-pile — a branch with 2 unique and 5 shared members yields ~0.9 distinctive
pathways under most-specific and 2 under most-general. Filing into the largest keeps each narrow
branch's quota for the pathways only it has; the shared terms lose nothing, drawn at the same rate
from the mega-pile. **The stratum is a sampling device and must never be read downstream as a
biological classification** — for the 1,663 multi-branch nodes it is one arbitrary choice among
several correct answers. Stated in the docstring, because it is the kind of column that gets
misused later.

**Both members of every cross-source name-collision group are force-included** — 94 groups, 191
members. Without them the redundancy THEMA exists to collapse would be almost absent and the test
could not fail. `normalized_name` and the new `collision_groups` moved from
`scripts/build_pathways.py` into `src/thema/data/pathways.py` so there is one implementation;
`data/pathways_summary.tsv` was verified byte-identical after the move.

**Nothing bills without `--submit`, and `--max-dollars` refuses above a ceiling.** Applied to
`--full` as well as `--smoke`: `--full` is the larger spend and needs the guard more. The price is
**marginal** — computed over requests not already in the ledger — so a rerun after a partial batch
shows what is left to pay for. `DEFAULT_MAX_DOLLARS = 20.00`, the credit on the account when this
was written.

**Two prices are reported, because one of them is a bet.** The system prompt is 1,933 tokens against
about 808 of actual content, and whether the provider's prompt cache holds across a batch of
thousands decides whether it is billed once or 1,842 times. Measured for the smoke run: **$13.43 if
the cache holds, $21.44 if it does not.** The gate checks the uncached figure, because losing that
bet halfway through a batch spends the money without producing the table. Input tokens are measured
through the provider's tokenizer on a seeded random subsample of the actual pending prompts —
unbiased by construction, and free, since token counting is metering rather than inference.

**Cache reuse is real but machine-local.** `--full` after `--smoke` regenerates nothing: `run_full`
filters against the ledger and `collect_batch` appends every succeeded completion, so the 1,844
come back byte-identical for free. But `data/cache/` is gitignored, so a clean clone re-pays; so
does bumping `PROMPT_VERSION` or changing `--model`. Recorded here so it is not rediscovered by
paying twice.

**Also corrected: the length band is 90–150 words, not the 90–130 this log recorded.** `MAX_WORDS`
was widened to 150 in f649b3f and the 2026-08-29 entry was never updated. The code is authoritative.

## 2026-09-09 — Descriptions are checked mechanically, then fact-checked, before anything clusters

Clustering is downstream of text quality, and a bad batch looks exactly like a bad clusterer from
the tree end. Two checks now run between generation and clustering.

**`--report` is mechanical and free.** Word-count distribution, validator hits broken out by kind,
residue and repair counts, all split per source, then ten full descriptions spanning the four
sources and the three provenance values. No API call, so it runs the moment a batch lands and again
after any repair.

**`scripts/verify_descriptions.py` is a model pass, and it is a pipeline step rather than an ad-hoc
one.** It runs on 1,844 now and 10,817 later and its corrections get committed, so it goes through
the same `LLMClient` and `Ledger` as the generator: cached, resumable, priced, reproducible, and
carrying the same `--submit` / `--max-dollars` gate. It bills the API key, not a subscription.

**The verifier sees the name, the curated prose, the gene list and the candidate description — and
never the model that wrote it, or that a model wrote it at all.** The source database is withheld
for the same reason the generator never sees it. It returns claims that are wrong or unsupported,
each with the sentence quoted and a one-line reason. Two kinds, kept apart because they call for
different responses: `wrong` contradicts established biology, `unsupported` may be true but cannot
be reached from the evidence shown. This is the method that caught `SLC31A2` called an iron
transporter (it is a copper transporter) and `SPINT1`/`SPINT2` called proteases (they are protease
*inhibitors*) — neither visible to a pattern-matching validator, neither wrong-looking in a cluster.

**Sequenced, because the second step is the expensive one.** `--pilot N` verifies a seeded random N
and reports the flag rate split by kind and by source with the measured cost per description, then
projects the remainder. Measured through the tokenizer: the verify prompt is 805 system + ~1,369
user tokens, so a **pilot of 100 costs $0.73–0.92** and **all 1,844 costs $13.48–16.94** at batch
rates. The projection is printed as a decision, not taken as a default.

**Repair never happens silently and never on the verifier's word alone.** A flagged description is
regenerated with the specific objection appended to its prompt as a correction instruction; the
rewrite goes back through a *fresh* verification call; if it flags again the ORIGINAL is kept and
both the flag and the failed repair are recorded. Several flags in the twelve-pathway run were
arguable rather than clear-cut, which is exactly why a flag is not allowed to be self-executing.
The three passes use three distinct prompt versions so no pass is ever served another's cached
answer — pinned by a test. `verification_status`, flag count and `repaired` are columns; flagged,
repaired and repair-failed are all counted in the summary.

**Recorded caveat: this is Opus checking Opus, so the rate carries a self-preference bias and is a
lower bound rather than a measurement.** A different verifier would be independent and cheaper but
weaker on exactly the single-gene detail this exists to catch. Reported with the number, in the
summary itself. No model comparison is built now.

## 2026-09-09 — First clustering: numpy/scipy/sentence-transformers, and three linkages not one

Ends the single-dependency state, which the 2026-08-29 entry already anticipated. Pinned exactly
and locked: `numpy==2.3.4`, `scipy==1.16.3`, `sentence-transformers==5.1.2` (which brings torch and
transformers). `sentence_transformers` and torch are confined to `src/thema/embed.py`, checked by
the same pair of tests that confine the Anthropic SDK — a grep over the sources, and an import with
the package made unavailable — so `src/thema/cluster.py` stays testable with no model download.

**BioLORD-2023, pinned by revision**, per D7 in `docs/brief.md`: its training objective makes
embedding geometry mirror ontology structure, which is this task. Qwen3-Embedding-0.6B is the named
comparison arm and is not built.

**L2-normalize, then Euclidean.** For unit vectors `||a-b||^2 = 2 - 2*cos`, so Euclidean distance
is monotone in cosine similarity and Ward's variance criterion — defined on Euclidean distance and
nothing else — is legitimate. Unnormalized, distance partly reflects vector magnitude, and
magnitude tracks text length, so the tree would encode how long a description is alongside what it
says. That is the silent bug the 2024 prototype shipped, silent because the output still looks like
a tree. `embed()` normalizes internally so no code path reaches a linkage unnormalized, and
`distances()` re-checks and raises rather than trusting it.

**No linkage is hard-coded.** Ward, average and complete are computed from the same condensed
distance matrix — seconds of compute — so the comparison holds the representation fixed and varies
only the criterion. Ward is the presumed default; **average is kept for a specific reason: it is
what the gene-overlap baseline uses (`docs/eval-plan.md` §2), so whichever linkage wins here must
then be used on BOTH sides of that comparison**, or representation and linkage are confounded.

**The cluster-size distribution is the headline report**, per linkage per cut: cluster count,
min/p10/median/p90/max, singleton count, and largest-cluster share. Ward assumes clusters of
broadly similar size, which biology has no obligation to supply; average linkage's known failure on
uneven density is one enormous cluster plus a tail of singletons. Both look like an ordinary tree
from the outside. On a 400-pathway plumbing run, average linkage at k=5 put **95.8% of everything
in one cluster** with two singletons, while Ward produced no singletons at any cut.

**That plumbing run used native database prose as a stand-in, not generated descriptions, and its
two halves are not equally trustworthy.** The average-linkage collapse is the more trustworthy
half: it comes from the linkage rule meeting uneven density, which is a property of the criterion
rather than of the specific text, so it is expected to survive the switch to generated
descriptions. A cross-source merge on the same run (GO and BTM T-cell sets landing in one Ward
cluster) is *weaker* evidence and is not recorded as a finding: GO and BTM native prose are written
very differently, and normalising that difference away is precisely what the generated descriptions
are for — so a merge that happens despite the register gap says little about one that happens after
it is closed. `build_ontology.py` marks any such run: when the descriptions table's scope or its
`description_generated_from` values show the text did not come from the normalizer, the summary
leads with a `caveat` row and every tree file header carries `*** STAND-IN TEXT, NOT A RESULT ***`,
so a plumbing tree cannot later be read as a result.

**Memory, measured rather than assumed.** The condensed distance matrix is the only thing that
grows as the square of the input: **13.6 MB at 1,844 and 468 MB at 10,817**, so the full run fits
comfortably and no workaround is needed. Recorded for when it does not: `fastcluster.linkage_vector`
computes Ward directly from the observation vectors in O(n·d) memory with no n² matrix at all. It
supports ward but not average or complete, which would still need the full matrix. Pre-clustering
was considered and **rejected**: it handicaps cross-source merging, which is the thing THEMA exists
to demonstrate.

**Every output states its own provenance on its face.** Each cluster table and each readable tree
dump carries `scope`, the description count, and the sha256 of the descriptions table it was built
from. The risk is not confusing two files; it is opening a tree in a fortnight and not knowing
whether it was built on 1,844 pathways or 10,817. A tree that cannot answer that is not evidence.

## 2026-09-09 — The smoke batch, what it cost, and three defects it exposed

1,844 pathways generated on claude-opus-5 at prompt v3, in two batches
(`msgbatch_01HrmiYN9PUMwFUY9aaq4aNj`, then `msgbatch_01GEexQAvKxUjU4oGkZjW3Ss` for six retries).
**Actual cost $12.83**, against a $13.43 cached estimate and a $21.44 uncached ceiling — the
provider's prompt cache held, 3.9M cache-read tokens against a 1,933-token system prompt, so the
cached figure was the right one to expect and the uncached figure was the right one to gate on.

**Quality is good and the numbers say so.** Length 119/128/135/142/153 words (min/p10/median/p90/max)
against a 90–150 band, so nothing is short and four GO descriptions run 1–3 words long. Across all
1,854 rows: **zero** identifier leaks of any family, zero database references, zero name-echo
failures, zero unexpected stop reasons. The prohibition in the 2026-08-29 entry is holding exactly.

**Defect 1 — six responses died on `max_tokens`.** `MAX_TOKENS` was 4,000 and adaptive thinking
overran it, truncating the JSON mid-string so it could not be parsed at all. Raised to 8,000; it is
not part of the cache key, so the retry re-sent only those six, for $0.08.

**Defect 2 — 46 responses leaked their own envelope into the description, and the existing repair
caught none of them.** 39 ended with an unmatched `"`; 7 were worse — the model escaped a quote,
wrote `"}` *inside* the string value, and kept generating: `"}<br><br>`, `"}What is the effect of
HSP90 inhibition on RSV replication?`, `"}Wait — I must not include escaped issues. Let me re-emit
cleanly.{`. It parses, so only a content check sees it. The old `_TRAILING_ENVELOPE` was anchored at
end-of-string and matched **0 of 46**, because something always followed the false close. It now
cuts from the false close onward, and an unmatched trailing quote is stripped only when the quotes
in the text are unbalanced — descriptions legitimately open with the pathway name in quotes, so
balance is the test rather than position. The cut is deterministic and the prose before it was
intact, so the fix repairs on read rather than regenerating: `envelope_repaired` reports 46.
Note the `<br><br>` in one of them is Reactome markup surviving into generated text, which is
precisely the source-specific token normalization exists to erase.

**The ledger now normalizes on BOTH append and reload.** Repairing only on read would mean the copy
held in memory during a generating run and the copy a resuming run loads are different strings, and
the tables written from each differ byte for byte — the idempotence every other writer here is
tested for. A test appends and reloads and requires the two to be equal; two consecutive rewrites
of the real table are byte-identical.

**Defect 3 — two sanity checks were themselves wrong, and had never run before.** "Every selected
pathway has a description" counted ledger rows inside the collection, which includes the twelve from
`--sample`; that hid six missing rows behind ten extra ones, reporting 1848 against 1844. It now
counts over the selected set. And "genes_shown equals n_genes everywhere" had a false premise:
`genes_shown` counts SYMBOLS while `n_genes` counts identifiers, so the two differ wherever two of a
source's symbols met on one gene (`DDX58`/`RIGI`, `CXCL8`/`IL8`, `ROBO3`/`ROBO3.1` — seven rows).
Truncation would show as shown < genes, which is what it now counts. A check that has never run is
not a check, and both of these were asserting something untrue about correct data.

**The summary's batch ids come from the completions, not from the run that wrote them.** A rerun
retrying six failures would otherwise overwrite the summary with only its own batch id and silently
drop the one that generated the other 1,838.

## 2026-09-09 — A check is only as trustworthy as the set it counts over

Both sanity checks that fired FAIL on the first real batch were themselves wrong, and neither had
ever run before — `data/pathway_descriptions.tsv` had never been generated, so this was their first
execution. Recorded as its own entry because the lesson outlives both bugs.

**The first was counting the wrong population.** "Every selected pathway has a description" compared
the number of ledger rows falling inside the collection against the size of the smoke selection. But
the ledger also holds the twelve completions from the `--sample` model comparison, ten of which are
outside the selection. Six selected pathways had genuinely failed. Ten stale rows minus six real
failures reported **1848 against an expected 1844** — a confusing `+4` where the truth was `-6`. The
stale rows partly cancelled the failures and converted a clear signal into a puzzling one. It now
counts `ledger.get(p.key) is not None` over the SELECTED pathways and nothing else.

**The second was asserting something false about correct data.** "genes_shown equals n_genes
everywhere" — but `genes_shown` counts SYMBOLS and `n_genes` counts identifiers, and the two differ
wherever two of a source's symbols met on one gene. Seven rows do: `DDX58`/`RIGI`, `CXCL8`/`IL8`,
`FASLG`/`TNFSF6`, `ROBO3`/`ROBO3.1`, `PB1`/`PBRM1`, `OR1F12`/`OR1F12P`, `CYorf15A`/`CYorf15B`. That
is exactly the multi-symbol case `Pathway.gene_symbols` was designed to record (2026-08-27), so the
check was contradicting the schema. What it meant to assert is that nothing was truncated, and
truncation is `shown < genes`, which is what it now counts.

**Both now carry a regression test reproducing the exact condition that made them lie** — one over a
fixture holding a stale ledger row outside the selection alongside a batch result that never came
back, the other over a fixture where two symbols meet on one gene. Each test was confirmed to fail
against the original check before being kept; a regression test never run against the bug is a
guess.

**The general rule, which is the part worth keeping.** A check comparing two counts is only as
trustworthy as the set it counts over, and the failure mode is not a wrong number but a *plausible*
one: two errors of opposite sign inside a badly chosen population net out and the check reports
something almost right. Prefer counting over the set the claim is actually about, state that set in
the note, and be suspicious of any check whose measured value is close to expected but not equal.

**A corollary worth stating: the sanity block is now shown by `--report`, not only written to the
summary.** Read back from the committed file rather than recomputed, so what is displayed is what
the file says.

## 2026-09-09 — HTML leaks from the prompt, not from the model's imagination (fix deferred to v4)

`html_markup` is now a residue pattern in the validator, matching `</?[a-zA-Z][^>]*>` — the same
shape `build_pathways.py` already uses to count markup in Reactome summations.

Measured on the smoke batch: **3 of 1,854 raw completions carried HTML, and 0 survive into the
committed table** — all three sat after a false envelope close and were removed by the envelope
repair. Two of the three had markup in their own native description; the third (`go:GO:0019221`)
did not, and produced `<br>--><br>` unprompted. Of the 1,854 prompts in this batch, **203 contained
markup**, so the leak rate among prompts that showed the model markup is 3/203 = **1.5%**.

**No prompt change now.** Bumping `PROMPT_VERSION` invalidates every cached completion and
re-charges the full $12.83 to fix what currently reaches the committed table zero times.

**The fix for v4, and the better form of it.** The obvious move is to forbid HTML in the output.
The better move is to strip HTML from the native description *before it enters the prompt*: the
model is copying markup because we show it markup — 982 Reactome summations carry HTML and
2026-08-27 deliberately kept it verbatim as part of the source's register. Not showing it any is
stronger than telling it not to write any, because a prohibition competes with an example while
removal leaves nothing to copy. Note this trades against the 2026-08-21 OPEN entry's premise that
the native register is preserved for the as-is A/B arm — so strip it on the way into the *prompt*,
not out of `description_source`, which stays verbatim on the row.
