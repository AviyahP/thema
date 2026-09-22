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

## 2026-09-10 — Batch recovery: a submitted batch must be collectable by a second process

Two recovery attempts on the verifier pilot were killed mid-poll, and the underlying problem was
not the kills. It was that submission and collection lived inside one process: `run_full` submitted
a batch, then blocked in `await_batch` until the provider finished, then read the results. Anything
that ended that process between the two — a kill, a lost terminal, a laptop closing — stranded
results that had already been paid for, with no way to reach them except resubmitting and paying
twice. **A batch is billed when the provider runs it, not when its results are read.**

**`--collect BATCH_ID` on both `normalize_descriptions.py` and `verify_descriptions.py`** drains an
already-submitted batch instead of submitting a new one. It deliberately does not require
`--submit` and is not subject to `--max-dollars`, because it bills nothing new; gating it would be
gating the recovery, not the spend. The collected batch id is recorded in the summary like any
other.

**`--collect` asks rather than waits.** `LLMClient.batch_status` reads the processing status without
blocking; if the batch has not ended, `--collect` says so and returns, and the operator reruns it
later. Blocking was the whole failure: a batch has a 24-hour window, and a process held open across
that window is the thing most likely to die. `await_batch` remains for the submit-and-drain path,
where the process is already committed to waiting.

**An unfinished batch must not look like an empty one.** A test flips the fake's status to
`in_progress` and requires that nothing is written — a table produced from a batch that has not
finished would be a partial table that passes every check about the rows it does contain.

**Operationally: check status with a short-lived command, collect once it is ended.** Polling from a
long-lived process is what failed twice; short commands and a status check do not accumulate risk.

**The honest note.** This capability was described in writing as a hazard while the $12.83
generation batch was in flight, and then not built until after a later run lost results to exactly
it. The generation batch survived on luck. The lesson is that a named, understood failure mode with
no code behind it is not mitigated, and the moment to build the recovery is before the first spend,
not after the first loss.

## 2026-09-10 — A theme built by our own prompt rule: the "Defective X causes Y" cluster

Ward at k=50 on the smoke descriptions produces one cluster of 47 pathways that is 100% Reactome,
33 of them named `Defective <GENE> causes <DISEASE>`. Three measurements say the cluster is held
together by the NAME TEMPLATE rather than by biology, and the mechanism is a rule we wrote.

**The mechanism.** `SYSTEM_PROMPT` (`normalize.py:125`) says *"Begin by repeating the pathway's name
in double quotes, exactly as given."* Reactome names this entire family to a template, so 33 of the
47 descriptions open with a near-identical string, and 22 continue `" describes what` — a phrasing
that does not appear in the top four openings table-wide (`is the` 625, `covers the` 301,
`describes the` 100, `describes how` 90). The rule anchors a description to its subject, which is
what it is for; for a templated family it anchors them all to the SAME subject.

**Test 1 — shared opening.** 33/47 openings echo `"Defective ...` verbatim. 99.2% of all 1,854
descriptions open with a quoted name, so quoting is universal; what is special here is that the
quoted strings are near-identical to each other.

**Test 2 — remove the first sentence and re-embed (the direct test).** All 1,854 re-embedded with
their first sentence stripped, Ward k=50. The Defective family **shatters: 47 members across 17
clusters, the largest holding 11 (23%)**. A size-matched control (the 37-member lipid/lipoprotein
cluster) **holds: 9 clusters, largest 25 (68%)**. Overall partition agreement between the two runs
is 96.2% on random pairs, so stripping first sentences did not destabilise the clustering in
general — it dissolved this cluster specifically.

**Test 3 — gene overlap.** Mean within-cluster gene-set Jaccard is **0.0047, the LOWEST of all 50
clusters**, against a random cross-tree pair background of 0.0034. It is 1.4x background where the
all-cluster median is 0.0225 (6.6x) and the lipid control is 0.0329 (9.7x). Tight in embedding
space, essentially unrelated in genes.

**The honest qualification.** There is a real shared property — these are all inherited disease
pathways, and 14 of the 47 are not named `Defective`. But "inherited disease" is a register, not a
biological process: the cluster spans glycosylation, membrane transport, DNA repair, carbohydrate
metabolism and steroidogenesis, and the gene-set union over it is incoherent. For enrichment
purposes a theme like this cannot carry a claim. Both things are true — the family shares a real
category AND the template amplifies it into a cluster far tighter than its biology warrants.

**This is a source-leakage finding, and belongs in `docs/eval-plan.md` 2c.** That section plans to
measure leakage by predicting the source database from the embedding. This is a worked instance
with a named cause, and it suggests the check should be run per-source-per-name-template rather
than only in aggregate: a single templated family can produce a pure-source cluster without moving
an aggregate leakage score much.

**Constraint recorded for the v4 prompt; nothing changed now.** The requirement to repeat the name
should be decoupled from the requirement to OPEN with it — the name anchors the description
wherever it appears, and the validator's `name_echo` check already tests presence rather than
position. Leading with the biology and placing the name later would keep the anchor and remove the
shared prefix. As with the HTML fix, the stronger form acts on the input rather than the
instruction: a templated name is a property of the source's naming convention, and what the model
copies is what it is shown. Not changed yet because a `PROMPT_VERSION` bump invalidates the cache
and re-charges the full run.

**Method note for whoever repeats this.** `data/ontology/clusters_*.tsv` holds scipy's raw fcluster
label; `tree_*_k*.txt` numbers clusters by RANK, largest first. They are different numbering schemes
and the tree's `[14]` is not label `14`. I read the wrong cluster first because of it.

## 2026-09-14 — Decision rule changed because the instrument failed calibration, not because of a number

The v4 prompt experiment pre-registered its decision rule before any result: **adopt the arm with
the lowest UNAMBIGUOUS-error rate on the fresh 100; if two arms are within 2 points, take the
cheaper one.** That rule depends on an adjudicator to split wrong claims into unambiguous and
arguable, and the adjudicator has now been measured against a hand-labelled split.

**It failed its gate. `adjudicate-v1` agreed with 19 of 27 hand labels (70%), and all eight
disagreements ran in the same direction** -- the human called the claim unambiguous, the adjudicator
called it arguable. Only one of the eight was a row the labeller had flagged as a close call; the
other seven were clear-cut. Its stated bases follow one shape throughout: *"X is incorrect |
However, [a reading under which the sentence survives]"*.

A one-directional error lands exactly on the quantity the rule turns on. An adjudicator that
systematically moves claims from unambiguous to arguable inflates every arm's arguable count and
deflates the number the decision is made on, and it does so by an unknown amount that need not be
equal across arms.

**New rule, fixed before any arm-B or fresh-100 result was seen: decide on RAW WRONG CLAIMS PER 100
as counted by the frozen `verify-v1`. If two arms are within 3 claims, take the cheaper one.**
`verify-v1` needs no adjudicator, has one commit and has never been modified, and produced the v3
baseline and every v4 arm under byte-identical conditions. The adjudicated split is still reported
beside it, marked as coming from an adjudicator that failed its gate in the lenient direction.

**Recorded plainly because the distinction matters to whether this is honest.** The rule changed
because the measuring instrument was measured and found unfit, and the replacement is a coarser
instrument that needed no calibration because nothing about it changed between the arms. It did not
change because anyone disliked a result: the change was made and written down before arm B was
priced, let alone run, and the raw metric it moves to already favoured the same direction (27 -> 16)
under the old instrument.

**The weaker half of the evidence, stated.** The hand labels the gate was measured against were
themselves drafted by a model and then reviewed and accepted by a human, not produced independently.
So 70% agreement is partly two models agreeing, and is an upper bound on what a purely human split
would have given. That makes the gate's verdict -- unfit -- more secure, not less.

## 2026-09-15 — Convention: no writer replaces rows it did not produce

**The rule.** A script that writes a shared output file must either MERGE its own rows into what is
already there, or write to a path namespaced to that run. A dry run or pricing run writes nothing
at all.

**Three instances in three different places, which is what makes it a convention rather than a
maxim.** All three were silent: each produced a file that looked correct.

1. **The adjudication worksheet, blanked by a rerun.** `write_worksheet` ran on every step-3
   invocation and regenerated the file with empty `label` cells, destroying 27 hand labels that had
   cost human attention and could not be regenerated. Caught only because the next report said
   "AGAINST THE 0 HAND-LABELLED ERRORS".

2. **`v4_b.tsv` written by the pricing run as a verbatim copy of arm A.** `repair_arm` returned the
   unmodified base when nothing had been submitted, and the caller wrote it out. The subsequent real
   run saw the file already existed, SKIPPED THE REPAIR ENTIRELY, and verified arm A's text under
   arm B's name -- hitting the text-addressed cache and returning arm A's verdicts at zero cost.
   The result was a complete, plausible arm B scoreline for a pass that never ran. Caught only
   because every cell matched arm A exactly.

3. **`v4_flags.tsv` rewritten with only the current arm**, deleting arm A's 90 flags when arm B was
   scored. Recovered free from the verification ledger, but nothing in the code noticed.

**Made mechanical, not just documented.** `thema.data.tables.merge_tsv` is the one writer for any
file more than one run contributes to: rows are identified by key columns, new rows replace only
their own keys, every other row is kept, and named columns can be marked as belonging to a human so
a regeneration never overwrites them. The three patches above are replaced by calls to it.

**Why this is worth a convention now rather than later.** The demo writes cluster names, enrichment
results and page data from separate scripts into one directory. That is precisely the shape that
produced all three failures, and the third one only surfaced because a number looked too good.

## 2026-09-16 — Two graders on the same text: the rate replicates, the identification does not

Arm B's 100 repaired descriptions were scored twice with the byte-identical `verify-v1` prompt, by
`claude-opus-5` (the grader arm B was repaired against) and by `claude-sonnet-5` (independent).

**The rate replicates. The identification does not.**

| | Opus | Sonnet |
|---|---|---|
| descriptions with a wrong claim | 5 | 4 |

Flagged by both: **1**. Only Opus: 4. Only Sonnet: 3. Neither: 92.

Raw agreement is 93%, which is meaningless here -- 92 of those agreements are both graders saying
"fine" about a clean description, and chance alone gives 91%. **Cohen's kappa is 0.19**: slight, well
above chance but poor. The overlap is 12% of everything either flagged, against 0.2 expected if both
were guessing, so they are detecting something real -- just not the same instances.

**Consequences, and they cut in both directions.**

*The circularity objection against arm B largely fails.* An independent model found FEWER errors (4)
than the grader arm B was optimised against (5). Had arm B's low score been mostly the grader
recognising its own corrections, the independent grader should have found substantially more.

*But the absolute number is not what it appears.* Treating the two gradings as capture-recapture:
each grader detects roughly **22%** of what is present, and the true count is plausibly **14-20 per
100**, not 5. That estimate rests on a single overlapping description and its interval is very wide
-- at an overlap of 2 rather than 1 it would read 9 rather than 14. It is also a floor: the two
graders share a prompt and are both language models, so an error class neither is built to see is
invisible to the method entirely.

**What may be claimed.** Rates, measured consistently: "27 -> 16 -> 8 per 100 on the same pathways,
same grader throughout" is sound, because a grader catching ~22% catches ~22% in every arm and the
ratio survives. **Per-description claims are not sound**: point at a description and say "this one
is wrong" and a second grader would probably disagree. Any such claim needs two graders or a human.

**No human has read any of it.** Every number in this experiment is a model checking a model. The
only route to an absolute rate is a person reading descriptions against gene lists; that was offered
and declined, and the numbers are reported as detections rather than as truth accordingly.

## 2026-09-16 — One round of check-and-repair, and no more

The repair pass fixes what it is shown: it corrected 16 of arm A's 16 flagged claims. The limit is
DETECTION, not repair, and detection is what does not scale.

| | 100 | 1,854 (demo) | 10,817 (full) |
|---|---|---|---|
| generate only | $0.70 | $13 | $75 |
| + one round of grade and repair | $1.86 | $35 | $200 |
| + a second round | $3.02 | $57 | $326 |

The first round takes detected errors from 16 per 100 to 5. A second round costs the same again for
perhaps 5 to 3-4. **One round is adopted; further rounds are rejected on cost per error removed**,
not on whether they work.

A decomposed verifier -- enumerate every gene-level claim, verdict each -- is the untested idea with
the best case behind it: **92% of all 52 wrong claims found across v3 and every v4 arm name a
specific gene**, so checking claims atomically targets essentially the whole error population, and
the task is simple enough that a cheap model might do it (which would cut full-corpus verification
from $111 to $22). Not built. Recorded because it is the obvious next lever if the error rate ever
needs to come down further.

**Union repair applied.** Arm B was repaired against Opus's findings only, so the three errors only
Sonnet found were still in the committed text: `PRDM6` called a methyltransferase, `CDKN1A` listed
among genes driving a cycle it arrests, and SLC12 transporters described as importing potassium when
several export it. All four of Sonnet's flagged descriptions were rewritten for $0.03 and written to
`data/experiments/v4_b_plus.tsv`. The lesson is general: repairing against one grader leaves the
other grader's findings in place, and they are known, named and unfixed until someone acts.

## 2026-09-16 — The overwrite convention was written, then violated the same day

The 2026-09-15 convention says no writer replaces rows it did not produce. A fourth instance
followed within hours, and it is recorded because the convention did not prevent it.

Scoring arm B with a second grader wrote its rows under the SAME `arm` label as the first grader's.
`merge_tsv` behaved exactly as specified -- it merged, replacing only matching keys -- but the
grader was not part of the key, so one arm's label came to hold a blend of two graders' verdicts
reported as one number. Nothing was replaced; the identity was wrong.

**The rule needs its converse: a writer must also identify its rows by everything that makes them
different.** Merging protects against deleting another run's rows; it does nothing when two runs
claim the same identity. Both ledgers were separate, so the blend was recoverable at zero cost, and
it was caught only because the totals disagreed with what the run had just printed -- the same way
three of the four were caught.

## 2026-09-16 — The demo renders the real ontology; everything statistical says "not computed"

`demo/prototype.html` was written against hand-made `THEMES` and `TREE` literals with a banner
saying every figure was illustrative. Those two literals are now filled from
`scripts/export_demo.py`, which reads `data/ontology/clusters_ward.tsv`, `data/pathways.tsv` and
the committed descriptions and writes `demo/ontology.json` plus a `demo/ontology.js` twin. The
shapes are unchanged: the page's contract was the constants, so the export was built to match them
rather than a new shape designed and the page rewritten around it.

**Three ward cuts become three depths: k=10, k=50, k=200.** The cuts are checked to refine one
another before anything is drawn (`check_nested`), because a tree assembled from cuts that crossed
would look like an ordinary tree and be wrong. 260 nodes, 250 of them clickable; depth 0 groups and
is not offered as a theme, matching the prototype.

**A single constant, `NOT_COMPUTED`, stands in every slot nothing has produced.** Enrichment, soft
membership and the three attribution tests are designed and unbuilt, so p-values, FDRs, direction
arrows, membership scores, the enriched count and the BH family all render the words *not computed*
in a distinct style. The alternative -- leaving a plausible figure, or hiding the row -- is
indistinguishable from a real result to any reader, including us in a month.

**Theme labels are the three most distinctive terms in the member names, joined by ` · `.** No
theme has been named; the namer has not been run and is priced separately. The separator is
deliberately not a word, so the label reads as machine output at a glance, and each theme carries a
`provisional label` tag. Alongside it the page shows the member nearest the cluster centre and that
member's own generated description, labelled as one member and not a summary -- a real pathway name
anchors a cluster better than three keywords and costs nothing.

**Two bugs in the prototype's own CSS, found only once real data arrived.** The `.go` rule for the
"Find themes" button also matched the `src go` badge on every GO member row, painting it a solid
accent block with no legible text; the prototype's illustrative data had too few GO rows for it to
be noticed. Scoped to `button.go`. Depth-0 nodes, being disabled, had nothing marking them as
headings once every node's label was machine-generated rather than hand-written prose.

## 2026-09-16 — v4 replicates on a fresh hundred: +10 points, twice

The v4 prompt was confirmed on 100 pathways drawn by the same uniform method with the original
hundred excluded, graded by the byte-identical frozen `verify-v1`. The outcome is the one the
decision rule names: does a description carry at least one `wrong` claim.

| | pilot 100 | fresh 100 |
|---|---|---|
| v3 | 26% | 19% |
| v4 arm A | 16% | 9% |
| difference | +10% [-1, +21] | +10% [+1, +19] |
| exact McNemar p | 0.110 | 0.052 |
| raw wrong claims | 27 -> 16 | 20 -> 9 |

**The replication is the result, not either p-value.** Neither draw clears p<0.05 alone. The same
+10-point effect appearing on two independent hundreds is stronger evidence than one significant
test would have been, and it is what the two-stage design was for. Pooled post hoc across 200
paired pathways -- legitimate, since the samples are independent and the protocol frozen, but NOT
pre-registered and reported as supplementary -- the discordant pairs are 37 only-v3 against 17
only-v4, exact McNemar **p = 0.0091**.

**The baseline moved and the effect did not.** v3 scored 26% on one draw and 19% on the other, a
7-point swing on the thing being improved against. Any single-sample comparison here was always
going to be reading partly the draw; the improvement holding at +10 across both is what separates
the two.

### Arm B: the repair pass, confirmed on fresh data and still undecided

| | pilot 100 | fresh 100 |
|---|---|---|
| arm A (prompt only) | 16% | 9% |
| arm B (prompt + repair) | 5% | 7% |
| A vs B, head to head | +11% [+2, +20], p = 0.027 | +2% [-5, +9], p = 0.791 |
| repair fixed / repair broke | 16 / 5 | 8 / 6 |

**The head-to-head is the number that matters, and it did not replicate.** Arm B beat arm A by 11
points on the pilot and by 2 points on the fresh draw. Pooled across both, 24 repair-fixed against
11 repair-broke over 35 discordant pairs, exact p = 0.041 -- which leans toward the repair helping.

**We cannot say the repair does not help. We also cannot say it does.** Stating either from these
numbers would be overreach. What can be said is that its pilot advantage was not reproduced, and
that the honest interval on fresh data includes zero in both directions.

**The collateral rate is decision-relevant independently of significance.** The repair rewrites
roughly 60 descriptions per 100 and introduces a new wrong claim into 8-10% of what it touches:
fresh, 59 rewritten to fix 8 and break 6; pilot, 65 rewritten to fix 16 and break 5. A mechanism
that damages a tenth of the clean text it rewrites needs a large win to be worth running, and on
fresh data the win was two pathways.

**More of the same test cannot settle it.** McNemar's evidence is the discordant pairs alone, and
the two arms disagree on about 14 pathways per 100. Detecting the fresh split (8:6) at 80% power
needs ~382 discordant pairs, about **2,700 pathways**; even the optimistic pooled split (24:11)
needs ~54 pairs, about **390 pathways**. Another hundred adds fourteen pairs and decides nothing.

**And precision is not the binding constraint -- bias is.** Arm B repairs against `verify-v1`
findings and is then graded by `verify-v1`, so a larger sample under the same protocol measures a
favourable estimate more precisely rather than testing whether the advantage is real. The 2026-09-16
two-grader result is the warning: Opus and Sonnet found similar RATES on the same text and agreed on
which descriptions only once out of four or five. The informative next experiment is therefore a
DIFFERENT grader on fresh arms A and B, not a fourth hundred under the same one.

---

## 2026-09-16 — Four label and baseline defects, found in one afternoon, all one failure

Completing the fresh-100 comparison surfaced four bugs. Every one is the same underlying failure --
**a value that nothing produced rendering as a value** -- and it is the same failure the demo's
`not computed` constant exists to prevent. They are recorded together because the pattern is the
finding; individually each looks like an oversight.

**1. Arm labels omitted the sample.** `label = arm_name if grader == args.model else f"{arm_name}
@{grader}"` carried the grader but not which hundred. Grading arm A on the fresh draw would have
written rows under `"A plain"`, the label already holding 90 pilot flags. Keys are disjoint so
nothing is overwritten, but any count grouped by arm becomes a blend of two experiments over two
hundred pathways. **This is the 2026-09-16 grader blend on a different axis**: the rule that a
writer must identify its rows by everything that makes them different was applied to the grader and
not to the sample. The scheme now lives in one function, `sample_label`, so the next axis has one
place to be added rather than two to be kept in step. The 101 already-written `v3 control` rows were
relabelled `v3 control [fresh]` after asserting every one was a fresh-sample key.

**2. The paired comparison read the wrong baseline file.** `report_stats` called
`carries_wrong(data, "v3", keys)`, which reads the committed `pathway_verification_flags.tsv` --
a file containing **none** of the fresh hundred's keys. On the fresh sample it returned an all-clean
baseline, so McNemar would have compared v4 against a v3 with zero errors and reported v4 as a
regression against nothing. This was the one that would have produced a wrong headline. Fixed, with
a guard that refuses to print a comparison when the baseline is empty.

**3. An arm that was never run rendered as a perfect score.** The first corrected run printed
`v3 19% vs B 0% ... exact McNemar p = 0.000 -- significant` for an arm that does not exist on the
fresh sample. `carries_wrong` returns booleans, and all-False is ambiguous between *scored and
found nothing* and *never scored* -- opposite findings, one of which is a flawless result with a
significant p-value attached. `was_scored` now tests label presence separately.

**4. Arm B's construction hardcoded `"A plain"`.** Arm B is built from arm A's text plus arm A's
flags. On the fresh sample it would have collected the pilot's flags, whose keys are not in the
fresh base at all: the repair would have found nothing to fix and **arm B would have been arm A
under a different name**, silently. Caught by pricing before submission, and confirmed fixed by the
repair pass then finding 59 flagged descriptions -- arm A fresh's own count -- rather than the
pilot's 65.

**What the pattern says.** Three of the four were invisible in the output: they produce a number,
not an error. Only the pricing dry-run caught the fourth before it spent money. The defence that
worked every time was refusing to accept a number without asking which rows it came from.

## 2026-09-16 — The fifth defect: the repair stage could be interrupted but not recovered

A sixth run today was killed between submitting its repair batch and collecting it. Batches are
billed when the provider runs them, not when their results are read, so those 59 completions were
already paid for and stranded.

`--collect ARM=BATCH_ID` exists precisely for this and was added after it happened twice on
2026-09-10. **It reached `verify_arm` and not `repair_arm`.** The repair stage submits its own
batch through the same `run_batch`, is exactly as interruptible, and had none of the recovery — so
the only way forward was to resubmit and pay for the same 59 requests a second time. The flag's own
help text promises that resubmitting "pays for the same batch twice"; the promise did not extend to
this stage.

**This is the first of the day's defects that cost money rather than producing a wrong number.**
The other four rendered something nothing had computed; this one silently removed the option not to
spend.

**The fix names the stage, not just the arm.** `--collect` now accepts `ARM:STAGE=BATCH_ID`, with a
bare `ARM=` still meaning verification. Two stages of one arm are two different things to drain and
must be nameable separately — the same identity rule that produced the sample-label and grader-label
defects. `parse_collect` says which part of a bad value was wrong, because an operator recovering a
stranded batch should not have to guess between a typo'd arm and an unsupported stage.

**An unfinished or unrecoverable batch stops the run.** `repair_arm` reports the status and returns
rather than falling through to a submission. Confirmed on the first recovery attempt, which printed
`repair batch ... is in_progress; rerun this command later` and spent nothing. Resubmission is a
separate, explicit decision, never a fallback.

## 2026-09-18 — CONCLUSION of the v4 prompt experiment: adopt the prompt, treat the repair pass as unproven

Four arms over two independent hundreds, scored by the frozen `verify-v1` protocol. The outcome is
"does this description carry at least one `wrong` claim". Arm labels here are the post-rename ones;
the flags table carries the same labels.

### The numbers

| configuration | rewrites/100 | first 100 | second 100 |
|---|---|---|---|
| v3 (previous prompt) | — | 26% (27 claims) | 19% (20 claims) |
| **A plain** — v4 prompt alone | 0 | 16% | **9%** |
| **B repair (all flags)** — repair on every flag | 59–65 | 5% | 7% |
| **D repair (errors only)** — repair on `wrong` flags only | 9–16 | 2% | **2%** |

Paired McNemar, same pathways, exact test:

```
v3 vs A          first 100   +10% [-1,+21]   p = 0.110
v3 vs A          second 100  +10% [+1,+19]   p = 0.052
v3 vs A          pooled n=200, 37:17 discordant      p = 0.0091   (post hoc)
A  vs B          first 100   +11% [+2,+20]   p = 0.027
A  vs B          second 100  +2%  [-5,+9]    p = 0.791
A  vs D          second 100  +7%  [+2,+12]   p = 0.016     fixed 7, broke 0
B  vs D          second 100  +5%  [-1,+11]   p = 0.180
```

### Conclusion 1 — the v4 prompt is adopted. This is the solid result.

A beat v3 by the same +10 points on two independent samples. Neither sample clears p<0.05 alone
(0.110, 0.052); the replication is the evidence, and the pooled figure is p = 0.0091. The v3
baseline itself moved 7 points between draws (26% → 19%), which is why the stability of the
*difference* matters more than either p-value.

### Conclusion 2 — arm B was defective, not merely worse

B rewrote on every flag, including `unsupported`, which is the verifier saying the gene list does
not support a claim rather than that the claim is false. It therefore rewrote 59 of 100 descriptions
to fix 9. **All 11 descriptions it broke across both samples came from rewriting text that carried
no error; none came from text carrying one.** Its 7 remaining errors on the second hundred are 1 it
never fixed plus 6 it created. The rule it violated was already recorded in this file and applied in
the other repair path. Fixed by making `Arm.repair_kinds` explicit; B's behaviour is preserved so
its published numbers stay reproducible.

### Conclusion 3 — the repair gain is real but mostly NOT transferable

The second hundred's arm A and arm D texts were re-scored by `claude-sonnet-5` under the identical
`verify-v1` prompt. This is the decisive test, because D repairs against what `claude-opus-5` flags
and is then graded by `claude-opus-5`.

| grader | A | D | difference | p |
|---|---|---|---|---|
| opus-5 (the grader D optimises against) | 9% | 2% | +7% [+2,+12] | **0.016** |
| sonnet-5 (independent) | 7% | 5% | +2% [-1,+5] | **0.500** |

**The two graders agree on the rate and not on the instances.** On arm A, opus flagged 9 and sonnet
flagged 7, overlapping on **2** — Jaccard 0.14, **Cohen's kappa 0.19**, the same figure the earlier
two-grader comparison produced. The repair cleared 7 of opus's 9 (78%) and only 2 of sonnet's 7
(29%), because 5 of sonnet's were never flagged by opus and the repair was never asked to touch them.

**Neither grader found the repair made anything worse** — only-D was 0 under both. The repair is
safe; it is simply narrow. Its measured +7 is largely the measurement agreeing with itself, and the
transferable gain is about +2 points.

### What this means for spending

Arm D is not a prompt, it is a three-stage pipeline, and the middle stage is the expensive one:
generation ~$0.0130/pathway, verification ~$0.0078, repair ~$0.0126. Verification must run over
EVERYTHING to find the errors. At 1,854 that is ~$14 to buy roughly two transferable points; at
10,817, ~$84. **Generation alone delivers the replicated 19%→9%; the verify-and-repair stage buys a
further ~2 points by an independent measure and ~7 by its own.** Those are separate purchases and
should be decided separately.

### Recorded limits

- Both hundreds are ~100, so every interval here is wide. The A-vs-D discordant set is 7 pathways.
- `adjudicate-v1` failed its calibration gate (19/27, all 8 disagreements lenient), so the metric
  throughout is raw `wrong` claims by `verify-v1`, not an adjudicated severity split.
- No third grader was run. Two graders at kappa 0.19 bound the instance-level agreement; they do not
  establish a true error rate, and capture-recapture on the earlier pair suggested 14–20 where each
  grader saw 4–5.

## 2026-09-18 — Is the cross-grader trustworthy? Its flags were read, not assumed

The cross-model result rests on `claude-sonnet-5`, a smaller model than the `claude-opus-5` grader
used throughout. The objection is fair on its face -- a weaker judge could simply be noisier -- so
its five remaining `wrong` flags on the repaired second hundred were read and assessed rather than
taken on trust.

**Three of five are genuine**, and all three are the error class v4 exists to prevent: influenza B
described as using dicistronic termination-reinitiation (a calicivirus mechanism via TURBS);
`ADPRM` credited with processing ADP-ribose-1''-phosphate from tRNA splicing (a different enzyme);
`DHX58`/LGP2 described as a cofactor that amplifies RIG-I signalling when it frequently inhibits it.
**Two are weak**: `UHRF1` "not a methyl-CpG reader" is pedantic given its SRA domain, and the `SYT1`
objection is a relevance complaint filed as a factual error.

**So Sonnet is noisier, and that does not rescue the repair pass.** A merely degraded grader would
find a SUBSET of the stronger grader's errors. These sets are nearly disjoint (overlap 2 of 14,
kappa 0.19), and **opus flagged none of the five**. Two graders finding real but different errors
means the true count exceeds what either sees -- which makes a repair driven by one grader's flags
cover an even smaller share of what is there. The finding is strengthened, not weakened.

Recorded precedent: the 2026-09-16 two-grader comparison produced the same kappa, and Sonnet's
unique finds then (`CDKN1A` listed among genes driving a cycle it arrests; SLC12 transporters
described as importing potassium when several export it) were accepted as real and repaired.

**Not established:** a second grader is not ground truth. Both counts are probably undercounts, and
the claim here is about the TRANSFERABILITY of the repair, not about an absolute error rate.

## 2026-09-18 — Where v4's remaining headroom is, and why it is not in the prompt

All 32 `wrong` claims surviving in arm A across both hundreds and both graders were read and
grouped. Two are grader mistakes (one reason ends "actually correct, not an error"). The other 30:

- **confusable gene identity** -- `FBXO5` called securin (it is Emi1; securin is `PTTG1`, caught by
  both graders); `PNOC` rendered "prochineurin", conflating it with prokineticin; `ADPRM` vs
  `ADPRHL2`; myomaker called a micropeptide (myomerger is one); `GPIHBP1` called secreted when it is
  GPI-anchored
- **direction of effect** -- `MN1` coactivator called a corepressor; `TMPRSS6` loss given the wrong
  iron phenotype; leptin and adiponectin called insulin-opposing when they are insulin-sensitizing
- **wrong partner** -- `TRADD`/`TRAF2` assigned to FAS/TRAIL rather than TNFR1; `BMPR1A` routed to
  SMAD2/3 rather than SMAD1/5/8; `TIRAP` placed in IL-1R signalling
- **invention** -- "amelophobic", not a word; miR-21 discussed when it is not in the gene set

**Those four groups are exactly the four bullets v4's PRECISION ON GENE-LEVEL CLAIMS section already
names.** The instruction exists, is specific, and is violated anyway. The failures are recall, not
comprehension, and a v5 restating the same rule more firmly should not be expected to move them.
Prompt text has reached diminishing returns on this axis.

**What v4 did fix, it fixed completely.** Its two structural done-conditions, measured:

| | shared 8-word opening | pathway name verbatim |
|---|---|---|
| v3, all 1,854 | 22/1854 (1%) | 1837/1854 (99%) |
| v4 arm A, first 100 | 0/100 | 28/100 (28%) |
| v4 arm A, second 100 | 0/100 | 34/100 (34%) |

The name rule that inflated the collision metric is gone.

**The headroom that remains, in order of cost:**

1. **A gene-presence check, free and unbuilt.** `validate` checks identifier patterns, references and
   residues but never that a gene NAMED in a description appears in that pathway's gene list. Pure
   string matching, catches the miR-21 class outright. Note it REPORTS rather than gates: `validate`
   feeds the summary, and only unparseable replies trigger a redraw (`PARSE_RETRIES`). It is
   therefore equally useful before or after a generation run and does not block one.
2. **Grounding.** The confusable-identity group is the model working from parametric memory. Supplying
   authoritative per-gene text would attack it at the root. An architecture change, not a prompt
   change, and the only option with real expected return.
3. **The name-free ablation**, queue item 2, still unrun -- and cheaper to argue now that the name
   appears in ~30% of descriptions rather than 99%.

## 2026-09-18 — Adopt v4 and generate; do not optimise first

**Decision: generate the 1,854 under v4 as it stands.**

Three reasons. The prompt is proven -- +10 points replicated on two independent hundreds, pooled
p = 0.0091. Prompt optimisation has low expected return, because the surviving errors are violations
of instructions v4 already contains. And nothing worth doing first blocks generation: the one free
improvement reports rather than gates, so it is equally useful afterwards.

**The alternative, recorded so it is not lost:** grounding is the change with real upside, and it
would warrant regenerating anyway. The cost of proceeding now is that ~$11 is spent twice if
grounding is later built. That is accepted deliberately, against working with 9%-error descriptions
instead of 19%-error ones in the meantime.

**Cost, after reclaiming the 198 already-paid-for v4 descriptions: $10.90 cached, $19.53 ceiling --
below the $20 default, so no raised ceiling is needed.**

## 2026-09-18 — The descriptions table keeps every generation; one reader exposes the current one

Generating under a new prompt used to destroy the previous generation: `pathway_descriptions.tsv`
held one row per pathway and was rewritten whole, so a v4 run would have replaced 1,854 paid-for v3
descriptions, and an interrupted one would have replaced them with a partial set.

- **One row per `(key, prompt_version, model)`, merged, never replaced.** Nothing is deleted. A
  `status` column names the generation consumers read.
- **One reader, `src/thema/data/descriptions.py`.** Six scripts each had their own local reader; with
  several generations in the table each would have silently taken whichever row came last. They now
  delegate. `run_prompt_experiment` pins `BASELINE_VERSION = "v3"` rather than following current --
  otherwise promoting v4 would redraw the fresh-100 sample AND replace the control with the arm it
  is compared against.
- **A partial generation may not supersede a complete one.** `restamp` refuses when the incoming
  generation is smaller, unless `allow_shrink` is passed. An interrupted run is indistinguishable
  from a successful small one to anything reading the table afterwards.
- **`verify_descriptions` now merges both its tables too**, keyed `(key)` and `(key, kind, quote)`.
  It previously rewrote them from the current run's results alone, so verifying a different hundred
  deleted the previous hundred's rows -- and that file is the first hundred's v3 baseline.
- **`--collect` is repeatable.** A full run is chunked at 2,000 and emits one batch id per chunk; a
  single-valued flag could not recover anything past the first chunk, and every request in the rest
  is already billed.

**Two things reclaimed or corrected in the process.** The 200 v4 completions generated during the
experiment were written to `cache/experiment/` while `normalize_descriptions.py` reads
`cache/descriptions/`. They are byte-identical in format -- same fields, plain pathway keys,
`prompt_version='v4'` -- and were copied across after asserting all three. 198 fall inside the smoke
selection, cutting the run from 1,844 to 1,646 and the price from $14.84 to $10.90. Separately, a
reported discrepancy between the smoke selection (1,844) and the table (1,854) was **not drift**:
the committed summary always recorded 1,844 selected plus the `--sample` run's twelve, two of which
overlap. `pathways.tsv`'s sha256 still matches what that summary pinned.

## 2026-09-18 — Master specification logged

`docs/spec/thema-master-spec.md` — product shape and input ladder, pluggable ontology builders
(`ward_tree`, `recurrent_dag`), analysis engine and three-test protocol on a DAG, landing-page
handoff. For the record; nothing in it is authorised until approved section by section.

## 2026-09-18 — Master specification review answered; addendum logged

`docs/spec/addendum-2026-09-18.md` — Aviyah's answers to the spec review. Each supersedes the
corresponding spec text. Not authorised to build.

**One clarification belongs here rather than only in the addendum, because it qualifies the
no-overwrite convention recorded on 2026-09-15.**

`merge_tsv` — merge, never replace — protects **shared tables** where two runs contribute different
rows that must coexist: the descriptions table across prompt generations, the experiment flags table
across arms, graders and samples. It is the wrong semantic for a **versioned build artefact**. A
rebuilt ontology legitimately supersedes its predecessor in full, and merging on a per-build
generated node id would accumulate stale nodes that no run produced and nothing would notice.

**Versioned build artefacts are replace-within-version: build to a temp directory, validate, swap
atomically.** The version in the path is what keeps an older build from being destroyed, which is
the protection merging provides elsewhere.

## 2026-09-18 — `--keys`, and why the smoke scope alone would not have completed the generation

The smoke draw selects 1,844; `pathway_descriptions.tsv` holds 1,854. The difference is the
12-pathway `--sample` run, ten of whose pathways the draw never picked. **The ontology was built on
all 1,854**, so regenerating with `--smoke` alone leaves those ten on v3 — and `read()` returns only
the current generation, so the ontology would silently lose them.

It would not in fact have been silent: `restamp` refuses to let an 1,844-row generation supersede an
1,854-row one, so the run would have stopped with v3 still current after ~$11 was spent. The shrink
guard was written for interrupted runs; it catches a scope mismatch too, which is the better
argument for it.

**`--keys FILE` generates a named list of pathway keys** — a top-up, not a scope. It refuses unknown
keys rather than dropping them, deduplicates without reordering, and obeys the same pricing gate.
New scope `keys`, added to `build_ontology`'s allowlist: a top-up is the same prompt and model
producing real descriptions, so it is a legitimate scope rather than an unknown one.

`data/keys/v4_topup.txt` holds the ten. Two of them already have v4 descriptions (they were in the
experiment's 200), so eight remain. The arithmetic closes: 200 cached + 8 + 1,646 = **1,854**.

## 2026-09-18 — Worked-example datasets: verified, and two candidates rejected

B7 makes rung 3 a hard requirement — the universe must be derived from a deposited count matrix,
never assumed. `scripts/check_demo_datasets.py` checks four things per accession: sequencing rather
than array, accession exists, processed matrix deposited, sample-group labels present.

| accession | contrast | outcome |
|---|---|---|
| `GSE157103` | COVID-19 severity, leukocyte RNA-seq, n=126 | passes — `GSE157103_genes.tpm.tsv.gz` |
| `GSE62944` | TCGA tumour vs matched normal, RNA-seq recount | passes — nine matrices incl. FeatureCounts |
| `GSE129705` | biologic-naive rheumatoid arthritis, whole-blood RNA-seq, n=128 | passes — processed data file |

**Rejected: `GSE93272`** (the prototype's arthritis set) and **`GSE138458`** (the first replacement
offered) — both arrays. An array gives a PLATFORM-derived universe, what the chip carries, not a
DETECTION-derived one. That is the distinction B7 turns on.

**The checker had two bugs that only running it exposed**, both fixed and worth recording because
they are the same failure in different clothes — a heuristic returning a verdict it could not
support. It never checked `Series_type`, so it judged an array against the wrong criterion; and its
filename heuristic hard-rejected `GSE129705_c12-ra-wb-bl-mo3-processed-data-file.txt.gz`, a usable
matrix named unconventionally. It now reports `UNCLEAR — inspect these filenames` instead of `NO`
when nothing matches but non-raw files exist.

## 2026-09-21 — `recurrent_dag`: seven decisions from measuring it on the real build

The algorithm as specified in `thema-master-spec.md` §10 was implemented and measured on the 1,854
build. `docs/spec/addendum-2026-09-21.md` is now the current specification and supersedes §10
wherever they differ. The decisions behind it:

**(a) The null gate compares counts, never a maximum.** §10.6 set `m = max(0.20, 3 x null_max)`,
where `null_max` is the highest support any scrambled grouping reached. Over 43,625 groupings that
is an extreme-value statistic: it measures the luckiest draw, not the property. It returned 0.247,
forcing `m = 0.742` — above the 0.5 ceiling — and reading as "resampling produces recurrent
structure by chance, the method is not discriminating". Counted instead: **0 scrambled groupings
reach m=0.25 against 3,457 real ones**, and no scrambled grouping of 10 or more members reaches even
m=0.10. The entire null signal is 35 groupings of 5-9 members. The same error had already been
caught in the containment diagnostic hours earlier and was still sitting in the null gate.

**(b) Each run's full draw is excluded as a grouping.** §10.2 records every dendrogram node of at
least `min_size`, which includes the root -- the whole 80% draw. It recurs at support 1.0 by
construction, and reappears as a node holding every pathway: exactly the synthetic root that
addendum A3 removed from `ward_tree`.

**(c) The null re-normalises rows after the column permutation.** Permuting each dimension
independently destroys row unit-length, and `cluster.distances` refuses non-unit input -- correctly,
since Ward on non-Euclidean input is silently meaningless. The rows are re-normalised and the
manifest records it. A deviation from §10.6's wording, made because the alternative is a crash or a
meaningless tree.

**(d) Twins are handled by a merge step after thresholding, not by widening the matching.** The
working hypothesis was that boundary pathways fracture a cluster into variant groupings, each too
weak to survive, and that raising `tol` would merge them. Measured, `tol` does the opposite: nodes
go 321 -> 450 and near-twins 40% -> 51% as `tol` goes 0.05 -> 0.20, because more slack admits more
distinct groupings as matches and absorption then seeds more nodes. The merge now happens explicitly
on kept groupings, before the DAG is built, and is where soft membership is produced.

**(e) `m` is chosen from the null count table**, at the lowest `m` where the scrambled count is
approximately zero -- not from a formula over a maximum.

**(f) Whether `tol` is needed at all is under test.** The grid runs tol 0 and 0.05 across five `m`
values on the v4 embeddings. If the two agree, `tol` is dropped and the matching rule becomes
exact-on-shared.

**(g) Per-node cohesion is not measured, and is logged in `docs/debt.md`.** Neither builder reports
whether a node is tight or ragged. Deferred because the grid decides whether this method ships at
all.

## 2026-09-21 — v4 descriptions complete: 1,854, promoted

All 1,854 pathways now carry a v4 description; `restamp` promoted v4 to current and v3 is kept as
`superseded`. The generation took three submissions -- 1,646 in the smoke batch, 8 in a `--keys`
top-up, 15 in a retry -- because two batches returned partial results. The 15 stragglers were the
largest gene lists in the collection (one of 1,351 genes) and failed twice before succeeding.

Total spend for the v4 generation: **~$11**, against the $12 ceiling for the whole experiment.

## 2026-09-21 — Changing the descriptions changed two-thirds of the ontology

The v4 descriptions were embedded with the same encoder and clustered with the same linkage at the
same cuts as v3, over the identical 1,854 pathways in the identical order. Only the text differed.

**ARI between the v3 and v4 ward trees: k=10 0.334, k=30 0.416, k=100 0.367.**

About two-thirds of the co-clustering structure changed. For scale, the encoder-stability experiment
(BioLORD vs Qwen3-Embedding-0.6B on identical text) produced ARI 0.306-0.369 across cuts:
**rewriting the descriptions moved the ontology about as much as swapping the embedding model.**

**Description quality is a primary input, not a finishing step.** Two consequences follow.

**Ontology-level evaluation is now a priority.** Ancestor-pair F1 against Reactome and GO, and
reactome2go recovery (`docs/eval-plan.md` §2a, §2b) are the measurements that would say whether v4's
tree is *better* rather than merely *different*. Neither has ever been run. Until they are, "v4
improved the ontology" is an assumption resting on the descriptions' own error rate, which measures
the text and not the structure.

**Anything measured on a v3 ontology needs re-measuring**, and the eventual 10,817 build will be a
different artifact rather than a larger version of this one.

**Visible consequence.** Both landing-page example cards survive but move: the insulin three tighten
from an 18-pathway node to a 12-pathway one; the NF-kB four, together at every cut under v3, now
split at k=200 and their smallest shared node in the page's exported levels grows from 15 to 36.
Kept at 36 for now; both cards revisited after the DAG decision.

## 2026-09-22 — Matching is two-sided: missing members count, not only extras

The §10 matching rule looked for the smallest cluster CONTAINING every shared member of a grouping,
then counted extras. Anything not fully contained was "not found" before its extras were ever
counted. The rule was therefore one-sided in a way its description did not admit: it tested for
contamination and silently treated dispersal as fatal.

**Measured on the five largest immune-majority groupings: 99 of 100 eligible runs failed as
"missing", zero as "extras".** The extras test — the only test the rule actually describes — never
executed once on any of them. 4,771 groupings in the pool are majority-immune.

**The rule is now two-sided.** Walk the ancestor chains of the grouping's shared members, take the
cluster with the best overlap (ties to the smaller), and require BOTH sides within tolerance:
missing members ≤ `tol x |A_R|`, extras ≤ `tol x |A_R|`.

**What it recovered.** A 221-member node, 96% immune, support 0.42, labelled
`activation · production · interleukin`. This is the theme the one-sided rule rejected in 99 runs
out of 100, and it is the same set whose complement the earlier runaway node was built from.

**Why this was not obvious.** An initial estimate put the change at +2% of matched pairs globally,
and concluded two-sided matching was a correctness fix with no practical effect. That estimate was
taken over whole groupings, where a coherent core is averaged with contamination that moves every
run. Split apart, immune members scatter at 2% and their non-immune companions at 68% -- a 34-fold
difference the aggregate hid completely. **The lesson is the aggregate: a rate over a mixed
population measured the mixture, not either part of it.**

## 2026-09-22 — Member cutoff raised from 0.25 to 0.5, and what it costs

A member is kept when its inclusion — the share of the family's matched copies holding it — is at
least **0.5**, a majority. Previously 0.25.

**Why.** At 0.25 a pathway appearing in a quarter of the evidence became a full member, which let
weakly-attached material accumulate on a theme. It is the complement of two-sided matching: the
match is now permissive enough to recognise a theme despite its contaminants, so membership has to
be strict enough to leave them out. Measured together on the immune theme, they work: the
non-immune members that survive sit at 0.54-1.00, and the 68%-scattering material is gone.

**What it costs, stated plainly.** The cutoff bounds what the DAG can express. A membership below
0.5 can no longer exist — it is dropped, not recorded as weak. On the straddler fixture a pathway
sitting between two groups went from **three nodes at 0.31 / 0.40 / 0.69 to one node at 0.69**.

That matters because soft membership is the method's stated reason for existing: a pathway that is
half one theme and half another should be recorded as both. At a 0.5 cutoff, "half" is the boundary
and anything genuinely balanced falls out. **This is a real trade of expressiveness for tightness,
not a free improvement**, and it is pinned by
`tests/ontology/test_recurrent.py::test_raising_the_member_cutoff_trades_soft_membership_for_tighter_nodes`
so it cannot quietly disappear.

## 2026-09-22 — v4 confirmed as the prompt; the v3/v4 gap was the pathway name

The v3-to-v4 comparison had looked like a regression: rebuilt on v4 text, ancestor-pair F1 against
Reactome fell from 0.2423 to 0.2114. Four text arms, re-embedded in one run and scored with
bootstrap intervals, show that the deficit is not the prompt.

| arm | name verbatim in text | F1 Reactome | F1 GO | reactome2go k=100 | random |
|---|---|---|---|---|---|
| v3 plain | 99% | 0.2423 [0.2231, 0.2661] | 0.2046 [0.1986, 0.2108] | 90.8% [84.2, 97.4] | 0.84% |
| v3 name-stripped | 0% | 0.2090 [0.1925, 0.2262] | 0.2204 [0.2130, 0.2285] | 84.2% [76.3, 92.1] | 0.88% |
| v4 plain | 27% | 0.2114 [0.1932, 0.2299] | 0.1936 [0.1901, 0.1978] | 82.9% [73.7, 90.8] | 0.95% |
| v4 name-added | 100% | 0.2575 [0.2320, 0.2876] | 0.2360 [0.2291, 0.2421] | 90.8% [84.2, 97.4] | 0.74% |

**What the arms say.** v3 repeated the pathway name verbatim in 99% of its descriptions; v4, which
was written to paraphrase rather than restate, does so in 27%. Strip the name from v3 and it falls
to v4's level. Give v4 the name and it beats v3 on both metrics, with non-overlapping intervals on
GO. **The v3 advantage was the name, not the prompt** — and the v3-plain vs v4-plain intervals
overlap, so that comparison was never significant in the first place.

**Decision: v4 is confirmed as the prompt.** The $3.87 stability run is cancelled; it was there to
size a difference that turns out not to exist.

**Name-prepending is not yet adopted.** It is the better text on every number above, but
`name. description` reintroduces the restatement v4 was written to remove, and the ontology is
supposed to cluster on biology rather than on shared vocabulary in titles. Carried as an open
decision, with the card check below as evidence in its favour.

### The landing cards survive it, and tighten

Spec B8: an example card shows the smallest node containing every pathway it lists. Rebuilt under
each arm:

| arm | NF-kB card (4 pathways) | insulin card (3 pathways) |
|---|---|---|
| v3 plain | `k200:11`, 12 pathways | `k100:74`, 11 pathways |
| v4 plain | `k100:6`, 31 pathways | `k100:73`, 12 pathways |
| v4 name-added | `k100:5`, 25 pathways | `k200:185`, 11 pathways |

Both groups hold under all three arms — no card loses a member. Prepending names shrinks the NF-kB
node from 31 to 25 and moves the insulin card a level deeper, to a node of 11. **The cards argue
for name-prepending rather than against it**, which is why the decision is open rather than closed.

## 2026-09-22 — Embedding is deterministic; `v0.1/embeddings.npy` is not reproducible

Re-embedding the same v3 text gave F1 0.2614 in one measurement and 0.2423 in another. Chased to
the bottom, because a metric that moves on its own is not a metric.

**Embedding is deterministic.** The same 50 texts twice: max abs difference **0.000e+00**, bitwise
identical. Reversed batch order: 0.000e+00. Split across two calls at a different batch boundary:
0.000e+00. CPU against MPS: 3.7e-07. `data/ontology/v0.2/embeddings.npy` reproduces from today's
pipeline **bitwise**.

**`data/ontology/v0.1/embeddings.npy` does not.** Against a fresh embedding of v3 text it differs on
**1,839 of 1,854 rows** (median per-row max difference 0.020, diagonal cosine 0.9868). The rows are
correctly aligned — every sampled row's nearest neighbour is itself — so it is not a key-order bug.
The v3 text is byte-identical to its original commit `e03b366`, only one v3 generation has ever
existed, and only one model snapshot is cached, so it is neither the text, nor the table, nor the
weights.

**The 15 rows that DO match are all named `TBA`** — the BTM modules with no meaningful name. So the
v0.1 matrix was produced by a name-handling step that is a no-op when there is no name, and which no
current code path reproduces: not plain text, not `strip_name`, not `name. description`. The file is
untracked, carries no manifest, and predates the versioned layout.

**Resolution.** 0.2614 came from that stale matrix; 0.2423 comes from a re-embedding that reproduces
bitwise, and the four ablation arms above were all embedded in a single run, so they are mutually
comparable whatever v0.1 was. **`v0.1/embeddings.npy` is not to be read by any evaluation, and no metric may be compared
across it** — v0.1's frozen reference is `clusters_ward.tsv`, which is tracked and unchanged.
The one legitimate reader is
`tests/ontology/test_ward.py`, which pairs the matrix with the tree built FROM it to check that
`WardTree` still reproduces `clusters_ward.tsv`. That test is self-consistent — stale matrix,
stale tree — and stays.

## 2026-09-22 — Name-prepending rejected: the gain was circular, and it builds a syntax theme

The `v4 name-added` arm beat every other arm on ancestor-pair F1 and reactome2go recovery
(entry above). **Both references are name-structured**: Reactome's and GO's sibling structure
tracks their naming conventions, so handing the clusterer the pathway name can raise both scores
by teaching it the convention rather than the biology, and neither metric can tell the difference.
Two checks that owe nothing to names were run on `ward_tree` at k=100, plain v4 against
`name. v4`. Same pathways, same gene sets, same names — only the partition differs.

### 1. Gene coherence — no gain

Mean pairwise gene Jaccard within themes. Bootstrap over themes (2,000 resamples); the random
baseline permutes theme labels, preserving the size distribution exactly (200 replicates).

| arm | within-theme Jaccard | bootstrap 95% | size-matched random | ratio |
|---|---|---|---|---|
| v4 plain | 0.03064 | [0.02648, 0.03570] | 0.00272 [0.00255, 0.00296] | 11.3x |
| v4 name-added | 0.02875 | [0.02483, 0.03326] | 0.00272 [0.00251, 0.00299] | 10.6x |

Both partitions are an order of magnitude more gene-coherent than chance, which is the
reassuring half. But **name-prepending is nominally LOWER and the intervals overlap almost
entirely**. On the one axis that cannot be inflated by naming convention, the F1 gain does not
appear at all. (4 of 1,854 pathways have no genes after resolution and score Jaccard 0 against
everything, equally in both arms.)

### 2. Template grouping — flat in aggregate, concentrated in one theme

Share of within-theme pairs whose names share a template phrase (`regulation of`,
`positive/negative regulation`, `process`, `pathway`) and **no content word**.

| arm | template-pair share | bootstrap 95% | random baseline |
|---|---|---|---|
| v4 plain | 0.0638 | [0.0496, 0.0783] | 0.0606 |
| v4 name-added | 0.0768 | [0.0459, 0.1159] | 0.0606 |

As one number this decides nothing — name-added's interval contains plain's value. **The width
is the finding.** It is wide because the effect sits in a few themes instead of spreading over
100, and averaging across 100 themes dilutes it to invisibility. Top 3 themes' share of all
template pairs: plain **10%**, name-added **20%**. The worst theme in each arm is a different
kind of object:

- plain v4, `k100:97`, share 0.31 — osteoblast differentiation, phosphate ion homeostasis, tissue
  remodeling, BMP signalling. Template-heavy titles, but real bone biology.
- name-added, `k100:81`, share **0.93**, 23 members — **22 of them begin "negative regulation
  of"**: actin nucleation, apoptotic signalling, mitophagy, calcineurin, cardiac muscle growth,
  cytoplasmic translation, DNA metabolism, GTPase activity, intracellular transport, membrane
  potential, mitochondrial fission, ion transmembrane transport, nucleotide biosynthesis,
  post-translational modification, potassium transport, nuclear protein export, muscle relaxation,
  striated muscle contraction, transport, tRNA metabolism. **These share no biology. The theme is
  the word "negative".** Under plain v4 the same 23 pathways scatter across **12** themes, each to
  its actual subject.

### Decision

**Name-prepending is rejected.** It buys nothing measurable in gene space and manufactures a theme
that the name-free text does not produce. v0.2 stays on plain v4 description text, which is what it
already uses — no rebuild.

**The methodological point, because it is the second time in this work.** The aggregate template
share would have cleared name-prepending: 0.0768 vs 0.0638, overlapping intervals, "no significant
difference". It is the same error as the immune-scatter rate: **a rate over a mixed population
measures the mixture, not either part of it.** Report the decomposition beside the aggregate, or
the aggregate will hide the failure it is averaging away.
