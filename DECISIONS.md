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

## 2026-09-23 — Single-merge order: complete each grouping before building families

Groupings are **completed from their own matched copies before families are built**, so variants
are judged on full member sets rather than on whatever each origin run happened to draw.

**Why the old order needed two merges.** Families were formed on RAW grouping sets, the threshold
applied, and membership recomputed afterwards from the family's pooled copies. Recomputing
membership can turn two non-variant nodes into variants, so a fixed-point merge had to run after
it. That second merge was treating a symptom: the sets being compared were incomplete at the moment
they were compared. Completing first removes the cause, and the merge's no-variant guarantee then
survives to the output because nothing edits a seed's set afterwards.

**Evidence.**

| | |
|---|---|
| cost of completion, ~47k groupings | **4 s** (~0.09 ms each) |
| real groupings that GREW on completion | **30,636 of 47,251 (65%)** |
| scrambled groupings that grew | **3,593 of 57,240 (6%)** |
| pooling discriminator (real ÷ null ratio) | **1.93** (2.89 / 1.50), against 1.32 for the two-merge order at the same min_size |
| variant pairs in the output, no second merge | **0** |
| the 5-9 band | **passes at m=0.30** where the two-merge order could not reach the target below the 0.5 ceiling |

**Completion is itself a discriminator, and that was not the reason for the change.** 65% of real
groupings gain members against 6% of scrambled ones: a real grouping is genuinely incomplete
because its origin run did not draw everything, while a scrambled one has nothing to recover. The
step was adopted to remove the second merge and happened to separate signal from noise as well.

**Variant pairs are 0 by construction, not by luck.** A seed claims every unclaimed variant of its
own set; no two seeds can therefore be variants; and the band threshold only deletes families, which
cannot create one. The one way it could fail is the size window -- `families()` walks only
`2 x max(2, 10% of seed size)` around each seed, and completion can move a set outside it. Measured:
0.

## 2026-09-23 — Size-banded thresholds: one number cannot serve bands that differ 100-fold

`m` is chosen per size band (3-4, 5-9, 10-29, 30+) rather than once for the build.

**Why.** At `min_size` 3 the small and large bands have false rates two orders of magnitude apart.
A single threshold either admits the noise in the small band or discards real themes in the large
one. The min_size control, at tol 0.15 / m 0.33, counting assembled themes:

| min_size | band | real | scrambled | false rate |
|---|---|---|---|---|
| 3 | 3-4 | 157 | **315** | **2.006** |
| 3 | 5-9 | 260 | 21 | 0.081 |
| 3 | 10+ | 174 | **0** | 0.000 |
| 4 | 3-4 | 60 | **217** | **3.617** |
| 4 | 5-9 | 283 | 15 | 0.053 |
| 4 | 10+ | 167 | **0** | 0.000 |
| 5 | 5-9 | 213 | 6 | 0.028 |
| 5 | 10+ | 178 | **0** | 0.000 |

**Recurrence alone carries no signal at 3-4 members.** Swept from m=0.20 to m=0.48, the real and
scrambled counts fall in lockstep -- **285 real against 286 scrambled at m=0.48**, a ratio of 1.00.
No threshold separates them, because raising `m` deletes true and false themes at the same rate.
**Three independent confirmations:** the min_size control above, the two-merge banded sweep, and the
single-merge sweep. The band is not rescuable by thresholding and must be judged another way, or
dropped.

Conversely the 10-29 and 30+ bands produce **zero** scrambled themes at every threshold tested, so
holding them to the small bands' `m` discarded real themes for nothing.

## 2026-09-23 — Tightness test for small themes: recurrence is geometric, cohesion is not

For the 3-4 and 5-9 bands only, a family must also be **tighter than the null's families of the
SAME SIZE** -- centred cohesion above the null's **95th percentile at that size**.

**Why recurrence fails at small sizes.** Any small set of mutual nearest neighbours recurs across
resampling, whether or not it means anything: if four points sit closest to each other, Ward puts
them together in most draws that contain them. Stability at that scale is a property of the
geometry, not of the biology. It is the same reason the scrambled null produces small recurrent
groupings at nearly the real rate -- permuting the dimensions destroys the semantics but leaves a
metric space in which some points are still nearest neighbours.

**Cohesion is not confounded that way**: it asks how tight the set is relative to what tightness
looks like at that size under no structure at all.

| 3-4 band | real | scrambled | ratio |
|---|---|---|---|
| recurrence only, m=0.48 | 285 | 286 | **1.00** |
| recurrence m=0.34 + tightness | 313 | 44 | **0.14** |

**The cut costs nothing real.** Measured per size 3-9, it rejected **zero** real families: the
distributions barely overlap. At size 3 the cut is 0.1153, real themes sit at a median of 0.6402,
and random real pathway sets sit at -0.0119. The cut removes 95% of the null by construction while
leaving the real side intact; the residual false rate is arithmetic, since 5% of a 38,195-family
null pool is still ~44 themes.

Cohesion is on MEAN-CENTRED embeddings (`docs/debt.md`), each side centred on its own matrix --
the null's families live in the permuted space and must be scored there.

## 2026-09-23 — Error target 0.05 -> 0.01, and no band above 0.02

**Why the target moved.** A 5% false-discovery rate is a reasonable price for a one-off analysis,
where the cost of a false positive is one wasted follow-up. **This ontology is frozen and reused**:
every future enrichment run is scored against these themes, so a false theme does not mislead once,
it misleads every analysis that ever touches it. The asymmetry justifies a stricter target than
an ordinary FDR.

**Why the 5% build could not simply be kept.** The joint optimiser maximised real themes subject to
the budget, so it **saturated the constraint exactly -- 60/1201 = 0.0500 in-sample** -- leaving no
margin at all. On a held-out scramble it returned **64/1201 = 0.0533**, above target. The per-band
diagnosis matters: the 3-4 band was stable (44 -> 43) and the drift came from the 5-9 band
(16 -> 21). **The tightness cuts generalised; the failure was an optimisation with zero headroom**,
not an overfitted criterion.

**What changed.** Calibration now uses the **mean scrambled count over five scrambles**, and the
tightness cuts pool all five at each size. A mean over five cannot be gamed by one scramble's
geometry, which is exactly what a single seed permitted.

## 2026-09-23 — Descriptions complete at v4: 10,801 of 10,817

**10,801 / 10,817 (99.85%)**, ~$58 of a $110 ceiling, seven hours over five batch chunks. v3's
1,854 rows are preserved as `superseded`; v4 was promoted only once complete.

**Accuracy held at scale.** verify-v1 on a random 100 of the 8,912 NEWLY described pathways:
**13 wrong claims per 100**, against **16** and **9** on the two smoke-set hundreds. The two earlier
measurements differed by 7 points at identical settings, so 13 sits inside their spread. The sample
was restricted to the new descriptions with a `--keys` flag added to `verify_descriptions.py`;
without it `--pilot` samples the whole table and would have mixed ~17% pre-existing descriptions
into the comparison, making it uninterpretable.

**Failures.** 51 initially, of which only 2 were API errors -- the batches reported 8,961/8,963
succeeded, so 49 were content failures in parsing. 34 truncations and API errors were retried and
**all 34 recovered**; one more (`go:GO:0050994`) was a transient refusal that also recovered.

**The 16 that remain, all one subject:**

```
reactome:R-HSA-168305  Neurotoxicity of clostridium toxins
reactome:R-HSA-5250955 Toxicity of botulinum toxin type B (botB)
reactome:R-HSA-5250958 Toxicity of botulinum toxin type E (botE)
reactome:R-HSA-5250968 Toxicity of botulinum toxin type C (botC)
reactome:R-HSA-5250971 Toxicity of botulinum toxin type G (botG)
reactome:R-HSA-5250981 Toxicity of botulinum toxin type D (botD)
reactome:R-HSA-5250989 Toxicity of botulinum toxin type A (botA)
reactome:R-HSA-5250992 Toxicity of botulinum toxin type F (botF)
reactome:R-HSA-168799  Inhibition of Interferon Synthesis
reactome:R-HSA-9682706 Replication of the SARS-CoV-1 genome
reactome:R-HSA-9682708 Transcription of SARS-CoV-1 sgRNAs
reactome:R-HSA-9683439 Assembly of the SARS-CoV-1 RTC
reactome:R-HSA-9683610 Maturation of nucleoprotein
reactome:R-HSA-9683673 Maturation of protein 3a
reactome:R-HSA-9683686 Maturation of spike protein
reactome:R-HSA-9692913 SARS-CoV-1-mediated effects on programmed cell death
```

**The `v4-scoped` fallback rule.** A refused pathway is retried once under `v4-scoped`: the v4
system prompt plus a clause restricting the answer to the normal cell biology and molecular
mechanism the member genes carry out in human cells, excluding preparation, handling, dosing,
delivery and weaponisation, and asking for the HOST machinery where a pathway is named for a toxin
or virus. Results are written as `prompt_version = v4-scoped`, `status = superseded` -- a recorded
generation of its own, never promoted silently.

**It barely worked: 1 of 16.** Only `Maturation of spike protein` succeeded, and it is the only one
of the sixteen whose NAME describes a host process rather than a toxin, a pathogen genome or an act
of damage. **The refusal tracks the pathway name more than the requested content**, so rewording the
instruction is not the lever. These 16 need a different model, a hand-written description, or
acceptance of a 0.15% gap.

### Open question: may a description contain biology not derivable from its input?

**68 of the 81 verifier flags are `unsupported`, not `wrong`** -- true, textbook biology that simply
is not derivable from the gene list and curated text the verifier was shown. Examples: "Loss of
CARD9 causes inherited susceptibility to invasive fungal infection"; "as in von Willebrand disease
or Bernard-Soulier syndrome"; "elevated HVA:5-HIAA in CSF".

The v4 prompt explicitly invites this -- *"Use your own knowledge of biology freely... Curated
descriptions are often too terse to carry thematic meaning, and adding that context is the point of
this task"* -- because thin GO one-liners cluster badly. So `unsupported` is currently measuring
the prompt working as designed, and the flag rate of 58% is not a quality figure.

**Unresolved, and it should be settled before the verifier's output is used as a quality gate:**
whether added-but-true biology is a feature to be kept (it is what makes thin sources embeddable),
a risk to be bounded (an unsupported claim is unfalsifiable against the source and can be wrong
without the verifier being able to tell), or something to be separated into its own field. The
style test bears on it: swapping curated text for the v4 description keeps only ~4 of 10 nearest
neighbours, so the added context is doing much of the embedding work, not decorating it.

## 2026-09-23 — Universe rule: a pathway with no genes is not in the universe

**DECIDED.** A pathway with `n_genes = 0` is **excluded from the universe**. A pathway with
`n_genes >= 1` **stays**, however small.

**Why.** A set with no genes cannot be a member of a gene set, cannot be tested for enrichment, and
contributes only its text. It would occupy a theme and carry weight in the hierarchy while being
incapable of ever being enriched. Keeping it costs correctness and buys nothing.

**Why small sets stay.** One gene is a real set with a real test. Dropping small sets would remove
most of Reactome's disease pathways and bias every cross-source comparison. Their statistical
treatment is **acknowledged debt** (`docs/debt.md`), not grounds for deletion now.

**The universe: 10,817 -> 10,770.** `data/pathways.tsv` still holds 10,817 rows -- the rule is a
filter applied at build time, not a change to the table, so statements about the TABLE remain true
and statements about the UNIVERSE change.

**The 47, all Reactome, in two kinds:**

| degradation | n | cause |
|---|---|---|
| `empty_after_resolution` | **32** | Reactome lists only pathogen protein names -- `NS`, `1a`, `rep`, and literally "SARS coronavirus, complete genome". Gene resolution **correctly refused** to map them to HGNC. |
| `no_source_members` | **15** | No gene products in Reactome at all: zero human rows in `NCBI2Reactome_All_Levels.txt` and `Ensembl2Reactome_All_Levels.txt`. |

**The resolver is right in every case.** It was checked and is not changed. Independently verified:
of the 443 pathways with 1-2 genes, 410 were that small in the source; the 33 that shrank lost only
pathogen symbols (E. coli, Mtb, influenza, HIV, RSV, SARS, Salmonella) and **no human gene was lost
in any of them**. Those 33 stay.

**Implementation.** `partition_universe()` in `src/thema/data/pathways.py` returns
`(kept, excluded)` -- excluded is RETURNED, not discarded, so a build records which rows it dropped.
`export.write` takes them and writes `n_excluded_no_genes` plus a per-pathway list of
`{key, reason, degradation}` into the manifest. `normalize_descriptions.py --full` applies the
filter, so they are never regenerated.

**Their descriptions are kept, not deleted.** 44 rows held `prompt_version = v4, status = current`;
they are now `status = out_of_universe` -- a status distinct from `superseded`, which means "a newer
generation exists". This means "there is nothing left to describe". `read()` no longer returns them
(10,801 -> 10,757) and `restamp()` was fixed to leave them alone: it previously rewrote every row's
status unconditionally, so the marking would have survived only until the next generation landed.
Pinned by `test_restamp_leaves_out_of_universe_rows_alone`.

**A false field, corrected.** Those rows carried `description_generated_from =
"description+name+genes"` while `genes_shown = 0`. `provenance_of()` keyed off `text_availability`
alone, which describes the TEXT and says nothing about genes. This was a deliberate earlier choice
-- the old test read *"A zero-gene pathway is still `described`, so it is still
description+name+genes; genes_shown carries the fact that no genes were shown"* -- and it is now
withdrawn: the field names what the model was actually given, and the prompt showed
`Input genes: (none)`. `PROVENANCE_NO_GENES` was added, 48 rows corrected (44 keys; 44 v4 + 4 v3).
**No other rows in the table are mislabelled this way**, and no row omits genes it was shown.

## 2026-09-23 — The 13 refused pathways go out as `v4-alt`, and are promoted

Sixteen pathways were refused by the v4 batch. **Three of them — `reactome:R-HSA-168305`,
`reactome:R-HSA-9682708`, `reactome:R-HSA-9683439` — have no genes and are therefore excluded by
the universe rule** (see "Universe rule" above). They are not "deliberately undescribed" and carry
no special case: they are simply not in the universe, so they cannot be unplaced, cannot be
regenerated, and cannot appear in `unplaced.tsv`. An earlier draft of this entry treated them as a
hand-made exception; the universe rule subsumes it and that framing is withdrawn.

**The remaining 13 all have genes and all remain in the universe.** Answers obtained outside the
v4 batch are recorded with `prompt_version = v4-alt`, **the model that actually produced each row
in that row's `model` column**, and `status = superseded`. One row may name a different model from
the next, which is the point: a generation is the record of what one prompt-and-model wrote, and
mixing models under one label would destroy that. Nothing is promoted without a separate decision.
`data/keys/refused_13_prompts.md` carries the exact v4 request per pathway, byte-identical to what
the API received.

### Provenance of the `v4-alt` rows — NOT written by the model that wrote the rest of the table

Stated in full, because a generation is only auditable if how it was made is on the record.

| | |
|---|---|
| produced | 2026-09-23 |
| interface | **ChatGPT web app at chatgpt.com**, Plus account, driven by browser automation. **Not an API call.** |
| model | **`gpt-5-6-thinking`** — slug read from the page's own message metadata, not inferred from a UI label |
| reasoning effort | **High** (the app default), where the Anthropic v4 batch used `output_config.effort = low` |
| isolation | one fresh **temporary** chat per pathway, Unpersonalized, memory/plugins/custom instructions off, nothing saved to history. No pathway shared a context with another. |
| interaction | one user message, one reply. **No follow-ups, no regeneration — the first reply was taken in every case.** |
| input | the system prompt and user block from `data/keys/refused_13_prompts.md`, pasted as one message with a line containing only `---` between them |
| output | every reply came back as `{"description": "..."}` **by instruction only — no JSON schema was enforced and no `max_tokens` was set**. The wrapper was stripped when the TSV was written; nothing else was edited. |
| length | all 13 are **108–123 words** against the 90–150 target |

**One deviation from byte-identity, stated rather than glossed.** The user blocks are byte-identical
to `render_user_message()`. **The system prompt is not:** its hard line-wrapping was re-flowed to one
line per paragraph. No wording changed, both worked examples were kept, and the OUTPUT FORMAT line
was kept as written — but it is a different byte sequence from what the Anthropic batch received.

**Two rows were re-run.** `botA` (`reactome:R-HSA-5250968`) and `botB` (`reactome:R-HSA-5250958`)
had been produced earlier under a different, flattened rendering of the prompt. **Those answers were
discarded** and both were re-run under the procedure above, so all 13 rows come from one identical
procedure.

**Verification:** verify-v1 was run against this generation — **0 of 9 checked, 4 refused by the
verifier**. No further verification; the v4 batch was never verified row by row either.

**PROMOTED to `status = current`.** These 13 are readable. `read()` is now **10,770 — the whole
universe, every pathway described**: 10,757 rows by `claude-opus-5` and 13 by `gpt-5-6-thinking`.
`prompt_version = v4-alt` and the per-row `model` are kept precisely so the table records that
these 13 were written by a different model from the rest; the distinction lives in those columns
rather than in the readability of the row.

**Consequence for `restamp()`, recorded because it is a live hazard.** The readable generation now
spans **two** `prompt_version` values. `restamp(table, columns, "v4")` marks every row whose
version is not `v4` as superseded, so the next promotion would silently demote these 13 and take
`read()` back to 10,757. Nothing in the code prevents it. Either the next promotion names both
versions, or `restamp` is taught to take a set — not done here, and flagged rather than left to be
discovered.

### Undescribed pathways must be UNPLACED, never silently absent

**The bug this fixes.** `unplaced` was computed as `set(embedded keys) - placed`. A pathway with no
description never entered the embedded key set, so it appeared in neither the nodes nor `unplaced`
— it simply vanished from the build, and nothing counted it. A pathway with no current
description would have been indistinguishable from one the method examined and rejected.

`unplaced.tsv` now carries a **`reason`** column, `no_description` or `not_recurrent`, and the
manifest records `n_undescribed` beside `n_unplaced`. Pinned by
`tests/ontology/test_base.py::test_unplaced_says_why_a_pathway_is_absent`.

**Stated plainly, because it is not finished:** `export.write` supports this, and the test pins it,
but **`scripts/build_ontology.py` does not call `export.write` at all** — it still writes the flat
v0.1-style `clusters_ward.tsv`, and every versioned export so far has come from analysis scripts.
Wiring the versioned export into the build CLI (master spec §15.3) remains outstanding, and until
it is done the guarantee holds only where `export.write` is actually called. The 16 undescribed
pathways are not in the 1,854-pathway v0.2 build, so nothing already written is wrong; this matters
for the first build over the full universe.

**Which pathways this now covers.** Not the zero-gene three -- those never enter the universe, so
they can never reach `unplaced`. It covers the **13** refused pathways that DO have genes: their
`v4-alt` rows are `superseded`, so `read()` returns no description for them and they are absent
from the embedded set. Those are the ones that must appear with reason `no_description`.

## 2026-09-23 — Tightness threshold solved from the error rate; percentile formulation withdrawn

**PRE-REGISTERED. Written before the calibration was run.** Recorded here so the result cannot be
graded after the fact.

**What is withdrawn.** The tightness cut was "the null's 95th percentile at the same size". That
admits 5% of scrambled themes **by construction**, so the 3–4 band's false rate was pinned near
0.141 by a constant nobody derived. 95 was conventional. It cannot be defended and it is gone.

**What replaces it.** A threshold solved for from the error rate already declared:

- **Statistic, FIXED:** centred cohesion — mean pairwise cosine of member embeddings after
  subtracting the universe mean embedding. **It may not be changed in response to any result.**
- **Strata:** size 3 and size 4, separately, never pooled.
- **FDR(s,c) = F(s,c) / R(s,c)**, where F is the mean over calibration scrambles of scrambled
  themes of size *s* passing recurrence with cohesion ≥ *c*, and R the real count.
- **c\*(s) = the smallest c with FDR ≤ 0.02**, over **every distinct cohesion value in the null**
  — no grid, no rounding.
- **20 calibration scrambles**, because this is a tail estimate and five is too thin.
- **One evaluation on a fresh held-out scramble set.** Whatever comes out is reported.

**Recurrence for this band is set at the grid floor, m = 0.20**, and this is a consequence of the
finding below rather than a choice: if recurrence carries no information, raising it deletes real
and scrambled themes in equal proportion, leaving FDR unchanged and the real count smaller.

**Failure branches, fixed now:**

| condition | consequence |
|---|---|
| held-out FDR > 0.02 | the 3–4 band is **dropped** from the frozen ontology |
| leave-one-out retained counts span > 20% | the estimate is unstable, the band is **dropped** |

In neither case is the statistic changed, a stratum added, another rule searched for, or the target
relaxed. The build is reported without the band and with an explicit account of what is lost —
including the four glued-theme fixes, all of which are 3–4 members.

### The band rests on geometry, not recurrence — recorded whatever the outcome

**Without the tightness test the 3–4 band is 285 real / 286 scrambled.** Recurrence carries no
information at this size, and the band is decided entirely by cohesion geometry — a different
criterion from the one used above 5 members.

Any small set of mutual nearest neighbours recurs across resampling whether or not it means
anything: at this size stability is a property of the metric space, not of the biology. Every theme
in the band is admitted by geometry alone, and any claim about the band must carry that sentence.

## 2026-09-24 — Threshold structure replaced by an empirical null test

**Full statement in `docs/spec/amendment-2026-09-24.md`. Runs behind it in
`docs/status/2026-09-24-runs-performed.md`. `addendum-2026-09-21.md` is NOT rewritten — it records
the rule that was pre-registered and what it produced, and that history is the point.**

**Decided:** one statistic (support) for every theme, no size bands in the criteria, cohesion
demoted from gate to reported descriptor, selection by **empirical null p-value** conditioned on
size with **one** correction across the build at **q = 0.02**, reporting **BH and BY with their
actual cost**. Matching becomes **Jaccard ≥ theta**, applied identically at every size, with
**theta = 0.70 declared as the primary** and a sensitivity sweep at 0.74, 0.77, 0.80 plus the
current `floor` rule as reference.

### The reasoning chain, including the steps that were discarded

1. The tightness cut began as **the null's 95th percentile** — a constant that admits 5% of the
   null **by construction**, pinning the 3–4 band near FDR 0.141 for reasons nobody derived.
2. It was replaced by **c\*(s) solved from a declared FDR ≤ 0.02**, calibrated on 20 scrambles.
   That failed held-out: 0.0264 at size 3, 0.0220 at size 4.
3. **The failure was procedural, not evidential.** The real and scrambled cohesion distributions
   are **disjoint** — scrambled max 0.1370 against real min 0.2179 at size 3. At any threshold
   between them, all real themes are kept and the false rate is 0.0000 held out.
4. The defect is the **"smallest c"** rule, which takes the worst acceptable point on a plateau
   where real survival is flat at 100%, spending the entire margin for no gain. **Verified:** 77
   null values qualify at size 3, none above the null maximum, so an unbounded grid picks the same
   value. *(An earlier diagnosis blamed the search grid. That was wrong and is recorded as wrong.)*
5. A rule based on the **null's MAXIMUM** was proposed and **withdrawn**: a maximum is the least
   stable statistic in a sample, grows with the number of draws, and **this project had already
   rejected one null gate for exactly that reason** (`3 × null_max` gave m = 0.742 from 35 tiny
   groupings). It is not to be reintroduced.
6. The replacement is a **per-theme empirical null p-value with a single correction**, because it
   **removes every chosen parameter** — four band boundaries, four thresholds, and the cohesion
   gate — leaving only `q`, declared weeks earlier.
7. **Cohesion is demoted from gate to descriptor** because **Ward's objective function is
   within-cluster tightness**: recurrence and cohesion are not independent evidence, and gating on
   both double-counts one signal.
8. `allowed = floor(0.15 × size)` is **zero for sizes 3–6**, so "recurs" meant *exact repetition*
   at small sizes and 15% drift at large ones. The earlier finding **"285 real / 286 scrambled"
   therefore showed only that recurrence-under-exact-repetition is uninformative at this size — not
   that recurrence is.**

### theta is declared, not derived

The Jaccard equivalent to `tol = 0.15` is **a range** (0.7391–0.8095 over sizes 15–30) because
`floor()` is discontinuous, and **a range cannot determine a parameter**. Choosing 0.74 — the
permissive end — *because* it admits the size-3 case would be selecting the value that produces the
desired outcome and calling it a derivation. Proposed in conversation, **refused on those grounds**.

**theta = 0.70 is primary**, justified as a round, interpretable value clear of every size-3
boundary case so no conclusion turns on a tie, and **explicitly not justified by equivalence**.
**Known dependency: the size-3 result is conditional on theta ≤ 0.75.** If a different theta is
adopted after the sensitivity table is seen, **that is a post-hoc choice and must be recorded as
one.**

### Small themes are refinements, not discoveries

**98% of size 3–4 themes sit inside a larger theme** (176/179 at size 3, 132/134 at size 4, against
86% at size 10+). A small theme is therefore not a free-standing discovery but **a claim of finer
structure inside an already-accepted node**, which is part of why such themes clear a
whole-universe null so easily. Recorded; not acted on. See `docs/debt.md`.

### Errors found in this line of work

Recorded rather than quietly fixed.

| error | what it would have caused |
|---|---|
| the 31-side calibration ran on **21 Sep embeddings**, still containing 4 pathways the universe rule excludes | a threshold calibrated on a superseded universe, presented as current. Caught after the run; the margin is far larger than 4 pathways, so the conclusion stands, but the numbers are provisional |
| **`pkill` did not stop the workers** — four survived two `pkill` invocations and kept running after a replacement was launched | six concurrent workers while reporting two, on a machine already being watched for memory pressure. Fixed by killing explicitly by PID and verifying; `pkill` is not to be trusted for this job |
| **`restamp()` rewrote every row's status unconditionally** | the next promotion would have silently demoted the 13 `v4-alt` rows and the 44 `out_of_universe` rows, taking `read()` from 10,770 back to 10,757 with nothing recording the loss |
| **`provenance_of()` keyed off `text_availability` alone** | 48 rows asserting `description+name+genes` while `genes_shown = 0` — a provenance field claiming an input the prompt never carried |

## 2026-09-24 — Recurrence is the only gate; the route there, in full

**The decision is the design from two days ago with two mechanical defects fixed.** Everything
between is recorded below as the route by which that was established, not as progress. Attribution
is given because most of the withdrawn reasoning is the reviewer's, and a record that quietly
loses track of who proposed what is not a record.

### Chronology

**1. Original state.** Recurrence gated every band. The 3–4 band sat at ~14% false rate, flat
across recurrence thresholds — "285 real / 286 scrambled" — read as *recurrence carries no
information at this size*. A tightness test at the null's 95th percentile was bolted onto 3–4 only.

**2. Pre-registered fix.** The percentile was replaced by c\* solved from FDR ≤ 0.02, "smallest
qualifying c", 20 calibration scrambles, 10 held out. **Result: FAIL** — held-out 0.0264 and 0.0220
at sizes 3 and 4. Band dropped under the declared branch.

**3. The distributions were disjoint.** Null max 0.137 against real min 0.218 at size 3. The
failure was **procedural**: "smallest c" lands on the boundary by construction and spends all the
margin. *Claude attributed this to the search grid; the reviewer said the grid was inert and the
rule was the defect; Claude verified the reviewer was right* — 77 qualifying values, none above the
null max, an unbounded grid picks the same c.

**4. Withdrawn (reviewer):** a threshold at the null's **maximum**. A maximum is the least stable
statistic in a sample, and this project had already rejected one null gate on that ground.

**5. Found:** **98% of size 3–4 themes are subsets of a larger theme.** They are refinements inside
accepted structure, not free-standing discoveries.

**6. Found:** `allowed = floor(0.15 × size)` is **ZERO for sizes 3 to 6**. "Recurs" meant exact
repetition at small sizes and 3 members of drift at size 20. So "285/286" showed only that
**recurrence-under-exact-repetition** is uninformative — not that recurrence is.

**7. Redesign (reviewer's, since withdrawn).** One statistic = support; size-conditioned empirical
null; per-theme p-value; BH and BY at q = 0.02; cohesion demoted on the argument that Ward
optimises tightness so cohesion is not independent evidence; Jaccard matching, theta declared 0.70,
sensitivity 0.74 / 0.77 / 0.80 plus the floor rule.

**8. The sweep killed it.**
(a) Support **overlaps heavily at every size** — real and null both run 0.01 to the top.
(b) **BY passes zero themes and BH passes 4,716 on ties**: with no threshold every family is a
hypothesis, m ≈ 16,000, the correction needs p ≈ 1e-7, and an empirical p cannot go below
1/(N+1) ≈ 1e-3.
(c) **theta 0.77 and 0.80 are identical** because Jaccard is discrete at small sizes.

*Two reviewer errors, recorded as such:* demoting cohesion **conflated "the algorithm selects for
X" with "X carries no information"** — the level achieved still discriminates, and the data showed
it; and the per-theme design **multiplied the hypothesis count by ~14 while leaving p-value
resolution fixed.**

**9. Found:** cohesion separates real from scrambled at **every** size, 3 to 200+, once the 30+ bin
is split (30–49, 50–99, 100–199, 200+ all disjoint). **Zero** real themes of 30+ are at risk; the 13
that looked exposed were candidate families of 443–1,045 members.

**10. Found:** a cohesion-only gate **does not select** — 15,783 of 15,783 candidate families pass
at held-out FDR 0.0106. Cohesion distinguishes clusters-from-real-data from
clusters-from-scrambled-data, which is true of every real family; it does not rank real candidates
against each other.

**11. Confirmed:** support at the old band thresholds reproduces **275 / 446 / 75 = 796 exactly**.
The earlier recurrence results stand.

**12. Considered and rejected:** two gates — cohesion for error control, recurrence as a declared
"granularity" parameter. A declared `m` with no anchor is a hand-chosen parameter. And **a cohesion
gate, applied to the null as it must be, removes every null candidate**, so recurrence has nothing
left to be solved from. Cohesion as a gate does not merely fail to select; **it destroys the other
gate's anchor.**

### What was learned

- **Recurrence and cohesion answer different questions.** Recurrence: is this grouping *stable*?
  Cohesion: is this grouping *distinguishable from chance*? Only the first selects.
- **A gate that passes every real candidate is not a gate.** Cohesion is descriptive.
- **Per-theme inference is the wrong instrument here:** the p-value floor is set by the number of
  null draws and cannot reach the correction needed for ~16,000 hypotheses at any feasible compute.
  **Build-level count FDR has no such floor.**
- **The two real defects were mechanical** — a match rule that rounded to zero for small sizes, and
  a threshold rule that sat on the boundary. **Neither was a reason to change the statistic.**
- **"Uniform" means one RULE at every size, with values solved per stratum from a size-matched
  null.** It does not mean one value. Stratification is correct; a different criterion per band is
  what was wrong.

### Decision

**RECURRENCE IS THE ONLY GATE.**

- **Statistic:** support, with **Jaccard matching at theta = 0.70**, declared, applied identically
  to real and scrambled data. theta is **not** chosen by its effect on 3–4; 0.74 and 0.77 are
  reported as sensitivity only.
- **Null:** the scramble through the identical pipeline, size-stratified, **intact** — no cohesion
  filter on either side.
- **Threshold:** `m(size)` solved on calibration scrambles at count-based **FDR ≤ 0.01** (half the
  0.02 ceiling, so there is margin), evaluated **ONCE** on held-out scrambles against **0.02 per
  stratum** and **0.01 overall**. **Never the smallest qualifying value without margin again.**
- **Scrambles:** 20 calibration, 10 held-out, for the confirmatory run.
- **Failure branches, declared now:** a stratum whose held-out rate exceeds 0.02 is **dropped**; the
  overall build must be ≤ 0.01 or **it is not frozen**. **No re-solving after held-out.**

**COHESION IS NOT A GATE.** It is reported per theme as a descriptive number. The spec carries one
sentence: *at every size, no scrambled candidate reaches the tightness of any real one.*

**THE 3–4 BAND** lives or dies on recurrence against the null under Jaccard matching, by the same
rule as every other stratum. **Nothing rescues it if it fails.**

### Amended the same day — the sensitivity arms are dropped

The confirmatory run was launched with three arms (theta 0.70 / 0.74 / 0.80) and killed at ~15
minutes. The clause above says 0.74 and 0.77 "are reported as sensitivity only"; that is withdrawn.

theta is a **declared** parameter. Reporting the result at three values invites reading the three and
preferring one, which is the exact move that was refused when 0.74 was proposed as "the permissive
end of the equivalence range". Sensitivity arms are only meaningful for a parameter that was
*estimated*; for a declared one they are an invitation to re-choose after seeing the outcome.

It is also 3x cheaper — ~8.5 CPU hours against ~26 — but that is not why. If the arms were the right
instrument the cost would be worth paying.

## 2026-09-24 — Cluster naming: bottom-up, then a top-down disambiguation pass

**Decision.** A theme is named from its members and, for an internal node, from its already-named
children — so naming runs **bottom-up**, level by level. A second **top-down** pass then revises any
name that is ambiguous against its parents and siblings.

**Why not top-down.** Naming a parent before its children means naming it from a member list it only
partly explains, and the children then have to be named around whatever the parent claimed. Naming
upward means every internal node is named from names, which is the same summarisation problem one
level up rather than a different one.

**Why the second pass is separate.** Sibling distinctness is not knowable during the bottom-up pass:
a node's siblings under a *different* parent may not be named yet. Folding distinctness into the
first pass would make the result depend on traversal order. The disambiguation pass sees the whole
named DAG and is ordered by longest path from a root, so a multi-parent node waits for all of its
parents.

**Cache keys are content keys, not node ids.** `theme_key(members, child_names)` and
`disambiguation_key(name, parents, siblings)`. Keying on the node id would return a stale name after
a rebuild moved members, silently — the failure would look like a naming error rather than a cache
error.

**Declared limits, not learned ones:** 1–6 words; no source name; no bare category word; no leading
article. A name that cannot meet them is returned as **unnameable with a reason** rather than forced
— an honest gap is worth more than a name the members do not support.

**Structured output returns the whole object only when the keyed field is not a string.** Both
formats therefore key on a boolean (`nameable`, `revise`). This is a property of `extract_text`, and
getting it wrong costs money silently: the first smoke attempt ran 200 calls that all failed to
parse, for roughly $2 and no output, because one of the two clients was built without
`response_key`.

## 2026-09-24 — The description validator's rules existed all along; nothing acted on them

**What happened.** 205 of 10,770 current descriptions carried text appended after a correct
description: a stray `</description>` closing tag, trailing HTML, dangling quote characters, and in
seven cases a whole appended passage — a smartphone review, a fictional gospel preface, Java API
documentation, Zulu-language chatbot output. The worst ran to 12,834 characters against a median of
969. All were `v4`, `claude-opus-5`, `stop_reason: end_turn`: the model closed its tag and kept
generating, and the extractor took everything.

**The part that matters.** `normalize.validate()` already had `html_markup` in `RESIDUE_PATTERNS`
and a 90–150 word `in_range` check. **Both fired on every one of the 205 rows.** No rule was
missing. The rows were written, merged, promoted to current, embedded, clustered, and used to
calibrate E — because the validator only ever *reported*, and the report was a count nobody read.
The 2026-08-29 decision that a failing check is "reported, never repaired" was right about not
repairing silently and was taken to mean the run should proceed regardless. It should not.

**Found by accident.** A naming call returned "Nokia 5 launch and specifications" for a
glycosylation theme. The model was reading its prompt correctly.

**Decision. `normalize_descriptions.py` now REFUSES to write a row the validator rejects.** The
completion stays in the ledger, so nothing paid for is lost and `--keys` can regenerate it, and the
run prints what it refused. Reporting is not a control; a gate is. Tested in
`tests/test_normalize_descriptions.py`.

**Also corrected here:** I twice told Aviyah the validator lacked a markup rule and that the repair
needed a priced regeneration of 66 rows. Both were wrong. The rules existed, the true count was
205, and the repair was free — 152 truncations at the closing tag and 53 markup/quote strips, with
every original kept as `superseded` and every repair written as a new `v4-repaired` row naming the
row it came from.

## 2026-09-24 — The embedder is replaced: BioLORD-2023 out, MedCPT article encoder in

### The error, named

**The 90-150 word band was declared without checking the encoder's window.** That is a reviewer's
error and it is mine to record: `embed.py` carried a comment asserting BioLORD had "a 512-token
window" so "nothing truncates". The architecture does carry 514 positions. The shipped
sentence-transformers config caps `max_seq_length` at **128**, and the cap is what runs. The claim
was made from the model card's architecture and never measured against the loaded object.

**Measured, once it was checked: the median description is 231 tokens and ALL 1,850 exceed 128.
Roughly 45% of every description — around 60 of ~135 words — was discarded before embedding.** The
second half of each description, where the specific mechanism usually sits, was never in the
ontology. Nothing warned: `embed()` is silent and the tokenizer's `194 > 128` goes to stderr from
inside a library call.

Found by accident. A naming call returned "Nokia 5 launch and specifications" for a glycosylation
theme; repairing that description and re-embedding moved its vector by **exactly zero**, because
the appended junk sat past token 128.

### The second error: the wrong kind of embedder

**BioLORD-2023 is a concept/definition embedder.** Its objective aligns short ontology terms with
their definitions, and it was chosen precisely for that ontology-mirroring property (brief D7).
But the input here is not a term or a definition — it is a 135-word paragraph of generated prose.
The model was selected for an objective that matched the *output* we wanted while mismatching the
*input* we feed it, and the window it reads was never examined.

### Consequence for everything already measured

**Every build to date, and E, ran on the first 128 tokens of each description. They are labelled a
truncated-text baseline.** They are not withdrawn: the pipeline, the thresholds, the matching and
families proofs and the 41x speed-up are unaffected, and E2 confirmed the description corruption
changed nothing. But they describe an ontology built on roughly half of each description, and any
claim made from them must say so.

### The replacement

**`ncbi/MedCPT-Article-Encoder`, pinned to `d05a736da4bb84ee4057b7f7999485be6ed85465`.** CLS-token
pooling as the model specifies, `max_length=512`, CPU, description text only as a single segment —
no pathway name, no title field, the same stripping rule as before.

**Basis: a Nature Communications 2026 benchmark of embedders on gene-set / GO-BP functional
descriptions, which places the MedCPT article encoder in the top tier with OpenAI-TE3 and Gemini
when fed free text, with pubmedbert-base-embeddings measured below it.** This is published
evidence, cited as Aviyah supplied it; **no in-project benchmark was run** and none is claimed.
MedCPT is also the right shape for the input: trained on PubMed title+abstract pairs, which are
paragraphs of literature prose.

**OpenAI-TE3 scored higher in that benchmark and was refused.** A frozen ontology needs an embedder
that can be pinned and re-run years later; an API model behind a moving endpoint cannot be, and no
sha can be recorded for it. Reproducibility outranks the margin.

**Checked rather than assumed, this time:** across all 10,770 descriptions the median is **180**
MedCPT tokens and the maximum **247**, so **nothing truncates**, with 265 tokens of headroom at the
worst case. `tests/ontology/test_universe.py` asserts it on token counts, not on the advertised
window.

**Pinned to a commit, not to `main`.** Every earlier manifest records BioLORD as `main`, a floating
reference, so those artifacts cannot be reproduced from their manifests alone. This one can.

**The loader now refuses to load retired vectors.** `universe.py` raises on any artifact recording
a `RETIRED_EMBEDDERS` id, and verifies the vectors on disk against a recorded hash — the universe
digest covers KEYS only and could not see either the description repair or the encoder swap.

### What did NOT change

**Only the vectors.** The selection rule is untouched: recurrence the only gate, declared m = 0.33,
per-size floor solved at FDR <= 0.01, Jaccard theta = 0.70, 20 calibration and 10 held-out
scrambles, single-size strata at 3-6, cohesion descriptive and never a gate. E is re-run under the
identical rule with nothing re-solved.

## 2026-09-24 — Member cutoff reverted to 0.25; the 22 Sep move to 0.5 is withdrawn

**The 22 Sep entry above stands as the record of why 0.5 was tried. It is superseded here, and it
is not rewritten.**

**The decision: the membership cutoff is 0.25.** A member is kept when its inclusion — the share of
the family's matched copies holding it — is at least 0.25.

**Why, measured.** The 31-side calibration computed **both** cutoffs per side (`docs/status/
2026-09-24-runs-performed.md`, which records `membership cutoffs 0.25 and 0.50 both computed per
side`). At **0.50 the small strata failed the declared cap**: size 3 held-out **0.0260** and size 4
held-out **0.0237**, both above the 0.02 ceiling. At **0.25 they passed.** The cutoff was not
chosen on preference; the stricter value could not meet the error target the project had already
declared, and a parameter that fails the declared target is not available whatever its other
merits.

**What 0.5 was bought for, and why it was not enough.** The 22 Sep reasoning was sound in its own
terms — at 0.25 a pathway appearing in a quarter of the evidence becomes a full member, and
majority membership is the complement of permissive two-sided matching. But it costs
expressiveness, and the 22 Sep entry says so explicitly: a straddling pathway went from three nodes
at 0.31/0.40/0.69 to one at 0.69. Soft membership is the method's stated reason for existing. The
measurement then showed the trade also failed on the error target, so it loses on both sides.

**The record was left inconsistent, and that is the actual defect here.** `DEFAULTS
["inclusion_threshold"]` still reads 0.5; the calibration harness and every build since have used
0.25; `docs/status/OPEN.md` listed the cutoff as an open question "blocking the freeze" when it had
been settled. The reversion was made in the runs and never written down. **A decision that exists
only in a script is not a decision**, and the gap is what made it possible to mistake the build for
a bug against the spec. `DEFAULTS` is left at 0.5 deliberately for now: it is the library default
for callers that pass nothing, and changing it is a separate change with its own test, not a line
in a decisions file.

**Consequence for `test_raising_the_member_cutoff_trades_soft_membership_for_tighter_nodes`:** it
pins the *behaviour* — that raising the cutoff trades soft membership for tighter nodes — which
remains true and remains worth pinning. It does not pin the project's chosen value, and is not
withdrawn.

## 2026-09-25 — Greedy consensus before the DAG; the larger theme grows

**Decision: a one-pass consensus step runs after the per-size gate and before `hasse`.** Full rules
in `docs/spec/amendment-2026-09-25.md`, which amends §10.7/§10.8. `hasse` stays strict; `families()`
is untouched.

**Why.** The confirmatory export had 39 roots. Eleven were near-nested pairs broken by one member
landing on opposite sides of the 0.25 cutoff in two different vote populations — `n0610` (302) and
`n0431` (342) share 301 members, and `Signaling by MST1` scored 0.269 in one vote and 0.229 in the
other. Nothing enforced compatibility between accepted clusters. This is the step every consensus
method in phylogenetics has (**Bryant 2003**, "A classification of consensus methods for
phylogenetics"; **Felsenstein 2004**, *Inferring Phylogenies* ch. 30), extended from exact
compatibility to fuzzy voted clusters.

**Two parameters, declared before the run: `STRAY = 0.10`, `JACCARD = 0.70`.** JACCARD is theta,
reused rather than re-chosen so "the same set" means one thing across the method.

**The first attempt failed and the failure is the reason for the final shape.** Rejecting the loser
of each conflict took 39 roots to **108** and stranded **87 pathways**. Support is anti-correlated
with size here — **Spearman −0.583, p = 4e-78**, median support 0.94 at sizes 3–5 against 0.49 at
100+ — so seating by support let 12- and 9-member themes evict the 953- and 503-member umbrellas.
Classical consensus assumes support is comparable across clusters; in THEMA it is confounded with
size. **So the larger theme grows to absorb the sub-theme, and nothing is ever rejected for being
big.** Rule 2 is additive, which is why coverage does not fall.

**Withdrawn:** the `is_variant` allowance band as a consensus rule (it stays correct inside
`families()`), and the minimum-overlap conflict test with its parameter `delta`.

**One clause not in the brief, added deliberately:** identical member sets fall to rule 3 and one is
superseded, rather than rule 1. Rule 1 is satisfied by equality, but two nodes with the same members
get no edge from `hasse` and both remain roots — the defect this pass exists to remove.

**Result.** Roots **39 → 16**, nodes 844 → 808, depth 12 → 17 with median 2 → 4, **0 pathways
unplaced**, held-out FDR **0.0037** against E's 0.0036 with **no floor re-solved**. The sensitivity
grid is flat (roots 15–19, FDR 0.0036–0.0039, unplaced 0 in all nine cells) and on the scrambled
sides the pass does essentially nothing — 0.0 members inherited, 0.018 themes superseded per side.

**Proved to the standard matching and families were held to:** 17 tests covering every rule, the tie
order, a two-level propagation and a rule-3 tie, with `consensus_pairwise` kept callable as the
reference and `vector ≡ pairwise` on the fixtures, 5 random pools and the real side.

## 2026-09-25 — What "frozen" means, and what it does not

Test 9 was given power over this word in advance: *"if the theme-set Jaccard is low, the word
'frozen' is not used, because what would be frozen is a seed and not a finding."* It has now been
run, and the answer is neither yes nor no, so the word is **narrowed rather than used or withheld**.

**Measured** — the 1,850 rebuilt at master seed 1, everything else identical, best-match Jaccard
over themes:

| | pre-consensus | consensus |
|---|---|---|
| mean | 0.845 | **0.841** |
| median | 0.881 | 0.875 |
| matching >= 0.9 | 45.1% | **44.6%** |
| matching >= 0.7 | 84.7% | **84.4%** |
| matching >= 0.5 | 96.7% | **96.5%** |

**"Frozen" applies to the theme set and its nesting.** 97% of themes reappear at Jaccard >= 0.5 and
85% at >= 0.7 under a different subsample seed, at the declared theta. What the build asserts —
that these groups of pathways exist, and that they nest this way — reproduces.

**"Frozen" does NOT apply to exact member lists.** Only **45%** of themes match at >= 0.9, so a
theme's precise boundary moves with the seed. A member list is not a frozen object and must never
be quoted as one. **The uncertainty is already carried per member by `inclusion`**, which is what
that field is for: a member at 0.31 is telling the reader it is a boundary case, and the seed
sensitivity is the same fact measured a second way.

**Consequence for anything written about a build.** A theme may be cited. Its nesting may be cited.
A claim of the form "theme X contains exactly these N pathways" may not be made without the
inclusions beside it. The consensus pass does not change this either way -- it is indistinguishable
from the pre-consensus build on every stability statistic, which is the correct result for a pass
that reconciles themes rather than finding them.

## 2026-09-26 — Ward clusters centred-and-renormalised vectors; RAW is superseded

**Decision: `distances()` receives the universe mean subtracted and each row L2-renormalised.** Full
evidence in `docs/spec/amendment-2026-09-26.md`; the question and its reading were recorded before
any measurement in `docs/spec/open-question-ward-space-2026-09-26.md`.

**This was a new decision, not a correction.** The 21 Sep note centred embeddings **for cohesion
only** and left Ward on raw deliberately. That note is now superseded.

**Mean subtraction alone could not have mattered.** Ward minimises within-cluster variance on squared
Euclidean distances, which are translation-invariant. The operative step is **renormalising after
centring**, which rescales each point by its distance from the universe mean and removes the
embedding's dominant shared direction — standard post-processing for anisotropic spaces, **Mu &
Viswanath 2018, "All-but-the-Top"**.

**Hubness was a measured artefact.** At k = 10, RAW had **25 pathways sitting in 50 to 149
neighbourhoods each, maximum 149**, and they were narrow GO terms rather than central biology.
CENTRED's worst is **36** and none exceeds 50; count skewness falls 4.76 to 0.93 and antihubs 3.0%
to 0.5%.

**CENTRED is at least as good on every DECLARED criterion:** hubness; curated-pair AUROC (better in
7 of 10 gene-overlap bands, Reactome no-shared-gene Cliff's delta **0.632 -> 0.809**); the error
caps (overall held-out FDR **0.0051**, every stratum under 0.02); test 9 stability (0.849 against
0.841); test 2 shape inside the curated range (6.1% roots, depth 12, 23% multi-parent). Cohesion is
a tie, and that comparison is biased toward CENTRED since CENTRED's cohesion is measured in the
space it clustered in.

**One clause of my own reading is withdrawn as mis-specified.** It required CENTRED to be "at least
as good on measurement 3", which compared the two arms **against each other**. No criterion in
`validation-plan.md` does that — the plan's conditions are absolute, and CENTRED meets all of them. A
rule invented for one comparison should not decide it. **The split it pointed at is recorded rather
than argued away:** RAW has 16 roots and depth 17, CENTRED 53 and 12. Part of RAW's depth was hub
glue — **96% of the 959 members of RAW's largest theme have a home of <= 30 members in CENTRED**.

**The eight unnameable RAW themes, traced member by member: five dissolved along the seams the namer
itself named** (n0517 polyamine vs PTM, n0398 Hippo vs MAPK, and three more). **The honest cost is
n0327**: its two nucleotide-transport members gain a 14-member theme, and **its four blood-brain
barrier and drug-response members have no home smaller than 391, at inclusions of 0.25 to 0.43.**
Four pathways moved from a bad small theme to a vague large one. That is the result on the 1,850 and
is to be re-checked on the 10,770.

## 2026-09-27 — Production naming sends BOTH member names and member descriptions

**Decided by Aviyah, on a blind rating.** Recorded verbatim:

> The DAG is built from descriptions only; pathway names never enter the embedding. Theme names are
> written from member names and descriptions together. The two are separate steps: naming runs after
> the structure is fixed and cannot change it. Pilot 27 Sep, 30 leaf themes, three arms blind:
> descriptions-only invents mechanisms from prose (inflammasome, circuits, insulin, AML), names-only
> under-covers and copies member names (4 mechanical failures); both had the fewest failures of
> either kind and won the mixed-source themes.

The first clause is checkable and checked: `scripts/build_ontology.py:268` embeds
`[texts[k] for k in keys]` — the descriptions table and nothing else. No pathway name reaches
`embed()`, so no name influences a distance, a Ward merge, a grouping or an edge.

### The pilot, for the record

Thirty leaf themes of `recurrent_dag_consensus_centred`, seed 20260927, prompt `name-v3`,
`claude-sonnet-5`, each named three times from three views of the same members: names only,
descriptions only, both. Candidates written in a per-theme shuffled A/B/C order with the arm key in
a separate file; nothing in the comparison marked an arm as the incumbent. Stratified 10 pure
GO / 10 pure Reactome / 10 with a BTM or Hallmark member, GO-Reactome mixtures excluded so the
strata stay
disjoint. Ran at **$0.72** against a $0.88 estimate — 90 calls, 136 output tokens each against the
112 the estimator assumed.

**Rating: names 8 clear wins, both 7, descriptions 6, and 9 themes where all three arms agreed.**
Names-only leads on the raw count of wins and is still the arm that was rejected, because the two
losing modes are not equally recoverable.

The four `copies_member` failures were all names-only: `Metanephric collecting duct development`,
`Peroxisomal protein import`, `Glycogen storage diseases` — a theme named by lifting one member's
pathway name, which names the member and not the theme.

The invented mechanisms were all descriptions-only, and all four are **mechanically clean**:
`Inflammasome-driven IL-1 signalling and acute inflammation`,
`Neural circuit control of locomotor behaviour`,
`Insulin regulation of glucose uptake and glycogen synthesis`,
`FLT3 inhibitor resistance mutations in AML`. That is the worse failure of the two: a check can find
a copied name and cannot find an invented mechanism.

**A caveat the pilot cannot remove, and the decision is taken with it stated.** The
descriptions-only arm is not blind to names: of the 152 member descriptions, **26% quote their
pathway's name verbatim and a further 26% carry three quarters of its content words — 53%
together**. The descriptions were generated from the names. So its 6 wins are an upper bound on what
descriptions alone achieve, and its failures are not explained by missing information.

**Separately, and independent of the input question:** every arm named all 30 themes with no
refusals, against 8 unnameable themes in the raw build. That is change 4 of `name-v3` — every member
shown with its inclusion, weak members never alone forcing `nameable: false`.

`name-v3` already sends both, so no prompt changes. What is settled is that it is not to be narrowed
to save tokens. Raw output in `docs/status/input_pilot.md`, arm key in
`docs/status/input_pilot_key.tsv`.

## 2026-09-29 — The inclusion cutoff is 0.50

**Decided by Aviyah.** Membership in a completed grouping now requires inclusion **>= 0.50**, up
from
0.25. This applies from the next build; nothing has been rebuilt or renamed under it yet.

### The criterion that was supposed to decide this could not

Per-cutoff floors were re-solved under the declared procedure (20 calibration scrambles solve, 10
held-out confirm, candidates at every distinct null support value, no grid) at 0.25, 0.33 and 0.50.
Every cutoff clears the 0.01 overall cap and every stratum clears the 0.02 branch.

Then the same calibration was run a second time on an independent scramble set:

| cutoff | seeds 1000-1019 | seeds 1-20 |
|---|---|---|
| 0.25 | 0.00538 | 0.00360 |
| 0.33 | 0.00460 | 0.00420 |
| 0.50 | 0.00248 | 0.00388 |

**Between-seed spread at one cutoff is 0.0018; between-cutoff spread within one seed set is
0.0006.**
The noise is three times the signal, and the two sets rank the cutoffs in OPPOSITE orders -- one
makes 0.50 safest, the other 0.25. An earlier report of a monotone ordering was read off a single
seed set and is **withdrawn**. FDR does not choose the cutoff, and the spec should say so rather
than
implying a statistical basis that does not exist.

The original calibration's scramble seeds are recorded nowhere in the repo, so the committed 0.0051
cannot be reproduced exactly. Seeds 1-20 do reproduce the committed FLOORS closely (size 3: 0.836735
against 0.838; sizes 7-9: 0.370000 exactly), which is evidence the procedure is right even though
the
number is one draw from a distribution with +/- 0.002 of seed noise.

### What decided it instead: what the overlap is made of

At 0.25, 852 of 1,842 placed pathways (46%) have two or more non-nested homes. At 0.50, 529 (29%).
The question is whether the difference is real multi-membership or threshold noise.

- **444 pathways stop straddling. 63% of them had a second home below 0.5** -- placed by a minority
  of the evidence, which is exactly what the higher cutoff exists to remove.
- **121 pathways newly straddle at 0.50**, so this is not pure subtraction.
- 252 pathways had a second home at inclusion >= 0.75. **114 of those (45%) stop straddling** -- not
  because the membership was weak but because a tighter cutoff makes themes nest more often.

**Those 114 were traced individually, and 104 of them (91%) are still in two or more themes at 0.50
-- their overlap became nesting.** The pathway still sits in both biologies; one is now the ancestor
of the other rather than a sibling. **9 fall to a single theme and 1 becomes unplaced: a genuine
loss
of 10 pathways out of 1,842.**

**A claim made in support of 0.25 is withdrawn as false.** It was stated that "nearly half the
multi-membership 0.50 discards sits at inclusion >= 0.75". Raising the cutoff deletes only
memberships BELOW 0.5, so by construction it deletes nothing at 0.75; the figure came from the
histogram of ALL straddler memberships rather than of the discarded ones. The true share of
discarded second-homes at >= 0.75 is 25.7%, and 91% of those survive as nesting. That claim was the
main argument against 0.50 and it did not hold.

### What 0.50 buys and what it costs

**Buys.** Straddlers fall from 46% to 29% of placed pathways and the survivors are enriched for
strong membership (33.8% hold a second home at >= 0.75, against 29.6% at 0.25). Seed stability is
the
best of the three: mean best-match Jaccard **0.866** with 55.7% of themes matching at >= 0.9,
against
0.849 and 46.3% at 0.25.

**Costs.** 767 themes instead of 873, and **unplaced rises from 8 to 27** -- nineteen pathways get
no
home at all. Pass-through parents remain 0 at every cutoff.

**The reason to accept that trade.** Multi-parenthood is the property this ontology has that a tree
does not, so it is worth protecting -- but only where it is semantically true. 0.50 removes the
marginal overlap and keeps or promotes the strong, which is the shape that was wanted.

### Stated limits

**Inclusion measures resampling recurrence, not semantic truth.** A pathway held at 0.9 in two
themes
is robustly dual UNDER THIS METHOD, which is the best proxy available, but no curator has confirmed
those pairs. That confirmation is validation gate 4 (sibling recovery), which is unrun. Every claim
above is about the method's own stability, not about biology.

### Open, and not decided here

**Which floors the 0.50 build runs.** `FLOORS_BY_SPACE` was solved on scrambles at 0.25, and the
cutoff bites at completion -- before families form and before the support gate -- so those floors
were
not calibrated for this cutoff. `recurrent_dag_incl050` (767 themes) uses the committed floors;
`recurrent_dag_cal050` (794 themes) uses floors re-solved at 0.50. **This is a separate decision and
has not been taken.** The two scramble sets disagree with each other about the floors by more than
either disagrees with what is committed, which argues for leaving them alone, but the argument is
not
strong and the question is open.

### Consequence

Adopting 0.50 **supersedes the frozen centred build**. Membership changes at every level, so the 861
`name-v3` names do not transfer and `LEAF_PROMPT_VERSION` cannot carry leaf names over either --
leaf
membership itself changes. A rebuild at 0.50 requires a full renaming run, and `name-v4`'s prompts
are still awaiting review.

## 2026-09-29 — Support floors re-solved on all 60 scrambles, and the committed floors confirmed

**Aviyah's instruction:** rather than pick between two disagreeing scramble sets, pool everything
and
log what comes out. Done, at every cutoff, 60 sides: **40 calibration** (seeds 1-20 and 1000-1019)
and **20 held-out** (seeds 21-30 and 2000-2009), with no held-out seed taking any part in solving.
CPU only, nothing spent. Written to `data/experiments/inclusion_floors_pooled.json`.

### Why a floor cannot simply carry across cutoffs

A floor is not a property of the scrambles. It is solved as the smallest support `c` where
`F(s,c)/R(s,c) <= 0.01` -- scrambled families of size stratum `s` at support `c` over real ones. The
inclusion cutoff is applied at COMPLETION, before families form, so changing it changes which
families exist on both sides. The floors solved at 0.25 answer a question about a different family
population than a 0.50 build produces. Measured, seeds held constant at 1-20:

| stratum | moved by the CUTOFF (0.25 -> 0.50) | moved by the SEEDS (at 0.25) |
|---|---|---|
| 3 | 0.033 | 0.013 |
| 4 | 0.030 | 0.010 |
| 5 | 0.097 | 0.047 |
| 6 | 0.150 | 0.110 |
| 7-9 | 0.090 | 0.006 |

The cutoff effect exceeds seed noise at every stratum, so re-solving per cutoff is required. It is
not a bookkeeping refresh.

### Pooling converges on the committed floors

| stratum | committed | 20 seeds A | 20 seeds B | **pooled 40** | pooled - committed |
|---|---|---|---|---|---|
| 3 | 0.838 | 0.8500 | 0.8367 | **0.8367** | 0.0013 |
| 4 | 0.890 | 0.9000 | 0.9100 | **0.9000** | 0.0100 |
| 5 | 0.670 | 0.6400 | 0.6869 | **0.6600** | 0.0100 |
| 6 | 0.530 | 0.4600 | 0.5700 | **0.5200** | 0.0100 |
| 7-9 | 0.370 | 0.3636 | 0.3700 | **0.3636** | 0.0064 |
| total distance | | 0.1284 | 0.0781 | **0.0376** | |

**Every pooled floor lands within 0.01 of the committed value, and the pooled set is three times
closer to it than either half alone.** The two 20-scramble sets disagreed with each other more than
the pooled set disagrees with what was committed. That is the answer to whether the original
calibration can be trusted: it can. The disagreement was sampling noise in a 20-scramble estimate,
and the committed floors sit where 40 scrambles say they should.

### The pooled floors AT 0.50, which is the adopted cutoff

| stratum | floor | effective `max(0.33, floor)` | held-out FDR |
|---|---|---|---|
| 3 | 0.880000 | 0.880000 | 0.00521 |
| 4 | 0.930000 | 0.930000 | 0.00833 |
| 5 | 0.600000 | 0.600000 | 0.00758 |
| 6 | 0.400000 | 0.400000 | 0.00926 |
| 7-9 | 0.270000 | 0.330000 | 0.00271 |
| 10+ | 0.040541 | 0.330000 | 0.0 |

**Overall held-out FDR 0.00333** against the 0.01 cap, 811 real families against 2.7 scrambled,
every
stratum under the 0.02 branch. Pooled 0.25 gives 0.00416 and pooled 0.33 gives 0.00479, so under the
pooled estimate 0.50 is also the lowest -- but the earlier finding stands that this ordering is
inside seed noise and is not a reason to prefer any cutoff.

**These are LOGGED, not adopted.** `FLOORS_BY_SPACE` is unchanged and still holds the 0.25 floors.
Which floors a 0.50 build runs is still an open decision.

### One stratum remains unpinned

Half-to-half spread after pooling: size 3 is 0.013, size 4 is 0.010, size 5 is 0.047, sizes 7-9 are
0.006 -- but **size 6 is 0.110**, with the two halves at 0.460 and 0.570 bracketing the pooled
0.520.
Forty scrambles narrow that stratum without settling it, and honesty requires saying so rather than
reporting 0.520 as though it were determined. If size 6 ever matters to a conclusion, it needs more
scrambles, not a decision.

### Recorded debt

Each side's family rows are recomputed from scratch every run, so pooling 60 sides cost a full
60-side recomputation rather than adding 30 to the 30 already done. Caching `(size, support)` per
`(seed, cutoff)` would make future pooling additive. Not done; logged so the next enlargement does
not pay the same cost.

## 2026-09-29 — ADOPTED: inclusion 0.50 with the pooled (centred, 0.50) floors

**Aviyah's decision.** The frozen build is now `v0.2.2-subset-1850-c50`
(`data/ontology/v0.2/recurrent_dag_c50`), clustering centred-and-renormalised MedCPT vectors with
membership at inclusion **>= 0.50** and the support floors **solved at that cutoff**:
0.880 / 0.930 / 0.600 / 0.400 at sizes 3 / 4 / 5 / 6, from 40 calibration and 20 held-out scrambles,
held-out FDR **0.00333**. It supersedes `recurrent_dag_consensus_centred`.

The earlier entries recommending 0.25 are **left standing and not rewritten**. What follows records
why that recommendation is replaced.

### The superseded reasoning, and why it fell

The case for 0.25 rested on one claim: that *"nearly half the multi-membership 0.50 discards sits at
inclusion 0.75 or above -- settled, not marginal"*. **It was false.** Raising the cutoff deletes
only
memberships BELOW 0.5, so by construction it deletes nothing at 0.75; the figure had been read off
the histogram of ALL straddler memberships rather than of the discarded ones. The true share of
discarded second-homes at >= 0.75 is 25.7%, and of the 114 strongly-included pathways that stop
straddling, **104 (91%) remain in two or more themes with their overlap turned into nesting** -- the
pathway keeps both biologies, one now the ancestor of the other. Nine fall to a single theme and one
becomes unplaced: a real loss of **10 pathways in 1,842**.

That claim was the whole argument against 0.50, and the recommendation did not survive it.

### What 0.50 is adopted FOR

**Membership now requires majority evidence.** A member at 0.50 was held by at least half the
matched copies of its theme; at 0.25 a quarter sufficed. That is the substantive change, and it is
what the other numbers follow from.

- **Straddlers 852 -> 682.** From 46% of placed pathways to 37%. The survivors are enriched for
  strong membership, and 121 pathways newly straddle, so this is not pure subtraction.
- **Test 9 stability 0.849 -> 0.862**, median 0.889 -> 0.909, matched at >= 0.9 **46.3% -> 53.2%**.
- **Shape stays inside the curated range**: 7.6% roots (Reactome 1%, GO BP 20%), depth 12 (Reactome
  11, GO 16), multi-parent 22.0% (Reactome 1%, GO 31%).

Multi-parenthood is the property this ontology has that a tree does not, so it is worth protecting
-- but only where it is semantically true under the method. 0.50 removes the marginal overlap and
keeps or promotes the strong.

### The cost, shown rather than hidden

| | 0.25 | **0.50** |
|---|---|---|
| themes | 873 | 800 |
| pathways placed | 1,842 | 1,831 |
| **unplaced (strict)** | 8 | **19** |
| **root-only** -- in no theme that has a parent | 53 | **106** |
| **effectively unplaced** -- the sum | 61 | **125** |

**A root-only pathway is placed by the letter of the algorithm and told a reader almost nothing:** a
top-level bucket and no theme within it. Raising the cutoff moves pathways into that state faster
than it moves them out of the build, so reporting only "unplaced 19" would understate the cost by
more than five-fold. All three counts are now written into the manifest
(`n_unplaced`, `n_root_only`, `n_effectively_unplaced`) and into `FROZEN.md`, together with the
largest root's direct-member count (64), so no future reader has to recompute them to see it.

**125 of 1,850 pathways -- 6.8% -- gain nothing usable from this ontology.** That is the honest
headline cost of the cutoff and it is larger than the 10-pathway loss the straddler analysis found,
because the two measure different things: the straddler figure counts overlap destroyed, this counts
readers left with nothing.

### Not re-solved

Theta stays 0.70, declared m stays 0.33, the strata are the amendment's, the consensus parameters
are unchanged, the encoder and its pinned revision are unchanged. **The 861 `name-v3` names are NOT
carried over** -- membership changes at every level, so they refer to themes that no longer exist.
The frozen build is unnamed.

## 2026-09-29 — How many scrambles a floor needs: 40 at 1,850, and 20 was not enough

Measured by resampling the cached calibration sides -- no clustering re-run -- and scored against
the
branch `docs/spec/addendum-2026-09-21.md` already declares: **leave-one-out retained-theme counts
spanning more than 20% of the median means the estimate is unstable and the band is dropped.** The
quantity that matters is not how far the floor moves but **how many real families the resulting
threshold admits**, because that is what a build inherits. 200 resamples per size, inclusion 0.50.

| stratum | k=5 | k=10 | k=20 | k=30 | **k=39, leave-one-out** |
|---|---|---|---|---|---|
| 3 | 88% | 82% | 35% | 21% | **0%** |
| 4 | 60% | 57% | 31% | 21% | **0%** |
| 5 | 15% | 11% | 1.5% | 1.5% | **1.5%** |
| 6 | 48% | 27% | 19% | 6.5% | **0%** |
| 7-9 | 0% | 0% | 0% | 0% | **0%** |
| 10+ | 0% | 0% | 0% | 0% | **0%** |

**Every stratum passes leave-one-out at 40. None of sizes 3 and 4 passed at 20** -- 35% and 31%,
well over the limit. **The original 20-scramble calibration was under-powered at exactly the strata
that carry the most risk**, which is why the two 20-scramble sets disagreed and why pooling to 40
resolved it. `k` equal to the number of sides is deliberately absent from the table: there is one
way
to draw n from n, so its spread is zero by construction and reporting it as stability would be
circular.

**A correction.** Size 6 was earlier called the least determined stratum, on the strength of the two
20-scramble halves giving 0.460 and 0.570. At 40 it is clean -- 0% span, floor 0.400. **Sizes 3
and 4
are the fragile ones**, and the reason is visible: they hold the fewest null families per side (195
and 1,255, against 21,724 at 10+).

### The rule that answers "how many do we need"

**Precision follows the number of null families a stratum holds, not the number of scrambles.** A
floor is solved from counts, so a stratum with more null families gets a better estimate from the
same scramble. That is why 7-9 and 10+ are stable at k=5 while size 3 needs 39.

### Projection to the 10,770 -- an extrapolation, not a measurement

The pool grows 5.82x with the universe, so each scramble carries proportionally more evidence.

| stratum | null families/side at 1,850 | stable at 1,850 | projected at 10,770 |
|---|---|---|---|
| 3 | 195 | k=39 | **7** |
| 4 | 1,255 | k=39 | **7** |
| 6 | 1,620 | k=20 | **3** |
| 5, 7-9, 10+ | 1,670-21,724 | k=5 | **1** |

**`amendment-2026-09-24c`'s declared 10 calibration + 5 held-out at 10,770 is adequate** -- 10
clears
the worst projected requirement of 7 with margin. That declaration was made on reasoning alone and
now has a measurement behind it.

**Labelled as what it is.** This rests on the same assumption the amendment made -- that precision
scales with null-family count -- and **nobody has checked it at 10,770**. The 5-member stratum
passes
at k=5 by a small margin, so the projection should not be trusted below k=3.

`scripts/floor_stability.py` reproduces the whole table from the cache in about six seconds.

## 2026-09-29 — Cohesion of the frozen 0.50 build, the null it was measured against, and why no cohesion threshold is added

**Measured by the reviewer on the frozen `v0.2.2-subset-1850-c50` build, ad hoc, from the same
centred-and-renormalised MedCPT vectors the build clustered.** The code is to be committed as
`scripts/cohesion_reference.py` and this table reproduced from it before this entry is relied on.

**Cohesion** of a theme = mean pairwise cosine among its members in the centred space. It is the
build's own geometry, not gene overlap and not names.

### The build, in shape

800 themes: 61 roots, 513 internal nodes, 287 leaves. Leaves have 3–9 members (median 5). The 61
roots are **three super-domains plus 58 islands**: n0781 (819 members — metabolism, muscle,
neuro, sensory, protein folding, blood pressure), n0552 (301 — immunity, viral, complement,
haemostasis), n0304 (284 — transcription, RNA, cell division, senescence). The islands are 4–62
members, mostly pure GO. Depth to 12, 22% multi-parent, 224 internal nodes with two children and 44
with three or more.

**245 of 513 internal nodes have exactly one child** (parent = child + a median of 3 direct
members; 147 single shells, 46 double, 3 triple). Compared on the superseded 0.25 build: 289 of 588
(49% → 48%), double/triple chains 60/10 → 46/3, mean depth 4.07 → 3.61. **The single-child shape is
a property of the method, not of the cutoff, and 0.50 shortened the chains.** It is recorded as a
shape, not a defect: a parent that is its child plus a few pathways on the same topic is legitimate
biology; the extras did not form their own child because they do not recur as a group. Its one
consequence is for naming: the tightest true name of "child + 3 more" is often the child's own
phrase, which is what the mechanical collision check and re-ask exist for.

### Cohesion by size

| members | themes | median cohesion | p10 |
|---|---|---|---|
| 3–5 | 156 | 0.477 | 0.349 |
| 6–9 | 316 | 0.380 | 0.273 |
| 10–19 | 241 | 0.340 | 0.255 |
| 20–49 | 70 | 0.312 | 0.241 |
| 50–199 | 10 | 0.235 | 0.191 |
| 200+ | 7 | 0.125 | 0.073 |

Leaves: p10 / median / p90 = 0.289 / 0.416 / 0.597 (0.25 build: median 0.415 — unchanged).
All-theme median 0.370 (0.25 build: 0.352).

Cohesion falls with size mechanically. **Any single cosine threshold is therefore a size cap in
disguise.**

Least cohesive leaves: n0640 (0.160: inner cell mass differentiation, response to erythropoietin,
decidualization, primitive erythrocyte differentiation, response to progesterone, structure
maturation), n0518 (0.180: copulation, response to herbicide, protein processing, regulation of
proteolysis, response to genistein, peptide biosynthesis), n0601 (0.187), n0790 (0.204), n0694
(0.210). Most cohesive: n0022 (0.808: four FLT3-inhibitor-resistant mutant sets), n0192 (0.778),
n0031 (0.753: three DNA-replication pathways).

### Two nulls, and which one is informative

**Null 1 — random sets from the actual space.** Random subsets of the 1,850 pathways, same size as
each theme, centred space, 20 draws per leaf and 200 per size stratum (seed 0). Result: **0.000 ±
0.01 at every size.** This is by construction: after centring, the mean cosine over all pairs is
zero. Every theme beats it by an order of magnitude. It answers "is this group better than chance"
with a yes that carries no information, because Ward always groups the nearest things.

**Null 2 — kNN-ball reference.** Pick a random pathway, take its s−1 nearest neighbours in the
centred space, measure the ball's cohesion: the tightest group of size s the space can offer at a
random location. 300 balls per stratum (seed 1). This is the demanding reference: it asks whether
a theme is as related as things get.

| members | kNN-ball p5 | kNN-ball median | themes p10 | themes median | themes below kNN p5 |
|---|---|---|---|---|---|
| 3–5 | 0.268 | 0.440 | 0.349 | **0.477** | 1 of 156 |
| 6–9 | 0.208 | 0.356 | 0.273 | **0.380** | 4 of 316 |
| 10–19 | 0.183 | 0.302 | 0.255 | **0.340** | 1 of 241 |
| 20–49 | 0.136 | 0.243 | 0.241 | **0.312** | 0 of 70 |
| 50–199 | 0.082 | 0.154 | 0.191 | **0.235** | 0 of 10 |
| 200+ | 0.018 | 0.068 | 0.073 | **0.125** | 0 of 7 |

**At every size, the themes are tighter than typical nearest-neighbour balls of the same size, and
6 of 800 fall below the reference's 5th percentile.** Even the 200+ umbrellas are twice as cohesive
as a random 200-ball. The recurrence gate selects groups at least as tight as the space's own
natural neighbourhoods at every scale. This is the measurement behind the claim that the build is
cohesive, and it is a claim about the embedding space, not about biology.

### What a cohesion threshold would do, measured

A cut at cohesion < 0.20, proposed as "too unrelated to stay":

| | 0.25 build | **0.50 build** |
|---|---|---|
| themes removed | 31 | **19** |
| of which roots | 9 | **9** |
| of which every theme ≥ 200 members | 6 of 6 | **7 of 7** |
| of which leaves | 5 | **3** |
| roots after removal | 53 → 158 | **61 → 167** |
| pathways losing their only home | 58 | **87** |

It deletes the top of the tree and leaves the incoherent leaves almost untouched — the five listed
above sit at 0.16–0.21, on the line.

### Decision: no cohesion threshold

1. **A threshold picked by inspection violates the standing rule** that no number in the procedure
   is chosen by its outcome. The support floors are solved against scrambles at a declared FDR;
   "0.20" has no such basis.
2. **It is a size cap, not a relatedness test** (table above), and what it removes is what the
   size already says: the umbrellas.
3. **Against the only informative null, the geometry finds nothing to remove.** The leaves a reader
   would reject ("copulation, response to herbicide, protein processing") are geometrically
   legitimate: the embedder placed those descriptions near each other. That failure is semantic
   and only a reader can see it.

**What judges "too unrelated" instead: the namer's `nameable: false`.** A theme the namer refuses
is shown as an *unnamed umbrella* and never hidden. **Recorded reservation (Aviyah):** she does not
like an LLM verdict acting as the structural filter; it is accepted for now because no measured
geometric rule does the job and every refusal stays visible and auditable.

**Follow-up, declared before the leaf names exist.** After level-0 naming on this build, compare
the cohesion of refused leaves against named ones. If refusals concentrate in the low-cohesion
tail, a **size-aware floor calibrated from those verdicts on the 1,850** may be declared and
applied to the 10,770 — calibrated-then-applied is defensible, picked-by-eye is not. If they do
not concentrate, the idea is closed and this entry says so.

### Reproduction

Inputs: `data/ontology/v0.2/embeddings.npy`, `embedding_keys.txt`, `centre_and_renormalise` from
`thema.embed`, `recurrent_dag_c50/{nodes,members}.tsv` (and `recurrent_dag_consensus_centred` for
the 0.25 column). Seeds: 0 (random sets), 1 (kNN balls). Draws: 20 random sets per leaf, 200
random sets and 300 balls per stratum. Strata: 3–5, 6–9, 10–19, 20–49, 50–199, 200+.

*Amended 2026-09-29.* Reproduced by `scripts/cohesion_reference.py`; the kNN-ball columns above are
the script's (ball p5/median per stratum and 6 of 800 below p5), the ad-hoc figures differed by at
most 0.02 and are superseded. Null 1 spread: sd 0.042 at 3–5, 0.021 at 6–9, below 0.01 above.

## 2026-10-02 — Parent coverage: five attempts, what each cost, and the one conclusion they share

**The fault.** A reviewer read all 215 level-1 names and found one dominant defect: **a parent named
NARROWER than one of its own children**, 16 clear and 12 borderline. Five attempts were made to fix
it. They are recorded together because the useful result is not any one of them but what they
jointly
establish.

### Attempt 1 — permit the parent to reuse a child's name (`name-v6`)

One sentence added to the system prompt: a cluster may take one of its children's names when that is
the tightest true name for it, and the child is then renamed. **It fired 0 times out of 18.**
Permitting reuse does not make the model prefer it; it still wrote a distinct, often narrower, name.

**WITHDRAWN.** The sentence is reverted so the system prompt is byte-identical to `name-v5` (digest
`f3d1f074929df02a`) and the v5 caches stay valid. The version string went back to `name-v5` for the
same reason. The CODE the attempt needed is kept -- the child re-ask, the `same_theme` column,
`--only-nodes`, `--reuse-version` -- because the later attempts use it.

### Attempt 2 — ask the comparison directly, one lenient check

A name-to-name check per parent, no member descriptions: *does each item fall under this name?*
**12 of 18 flagged, 10 covered after one re-ask, 2 unnameable; 11 of 18 outcomes right.** It caught
three of the five cases that had survived everything else.

But it was **lenient**: it passed a child broader than its parent on three nodes while flagging the
identical pattern on a fourth.

### Attempt 3 — define "covered" strictly

The wording was replaced to say an item is covered only if it is a sub-category -- everything it
refers to inside the parent -- and to name the three ways an item fails: broader, partly
overlapping, merely related.

**It flagged 5 of 10 names the reviewer had judged GOOD.** Every false flag was a DIRECT PATHWAY
whose title merely sounds broad: `heart development` under *Heart morphogenesis and chamber
development*. The checker was not malfunctioning -- `heart development` genuinely is broader. The
incompatibility is with how GO titles work: **a term's name describes the term, not the role it
plays in a cluster**, so a cluster of specific cardiac pathways will always hold a member whose
title sounds broader than the cluster.

**The control set is what caught this**, and it is the reason every later attempt ran one.

### Attempt 4 — split the check by item type

Two calls per parent. A CHILD CLUSTER is a name we wrote, so a child broader than its parent is a
real defect: judged strictly. A DIRECT PATHWAY is a title inherited from the source, so its breadth
says nothing about belonging: judged leniently, failing only on different biology. Uncovered is the
union. Titles exactly `TBA` are withheld -- 83 unannotated BTM modules no checker can judge --
and `HALLMARK_X` is shown as `Hallmark: x` to the checker only, never to the namer.

**The split fixed the controls: 1 of 10, down from 5**, and the survivor is a fair call. It is
accepted and is not what fails afterwards.

Step 4 of that attempt had the parent take its uncovered child's name mechanically. **9 fired and
only 3 survived.** Not a bug: the strict call correctly reports the child is then identical to the
parent and fully covered, but the parent has become NARROWER, so its own direct pathways fall
outside. The step meant to rescue these nodes is what condemned them.

### Attempt 5 — widen from the child's name instead of copying it

A second re-ask: *your child is named C, your name must include it fully and also cover these; start
from C and widen only as much as needed.*

**13 fired, 1 accepted. And the 12 rejections are not bad names.** `n0618` widened to *Sterol and
fat-soluble vitamin metabolism* -- the name an earlier attempt had already produced and which was
flagged at the time as the right answer -- and was refused because the child *Bile acid and sterol
homeostasis* is not strictly a sub-category of it. **12 of the 13 failures are the strict CHILD
call, not the lenient pathway call.** The widen step worked; the obstacle moved.

| | lenient | strict | split | split + widen |
|---|---|---|---|---|
| covered first time | 6 | 1 | 2 | 2 |
| covered after re-ask | 10 | 10 | 2 | 2 |
| covered after widen | — | — | — | 1 |
| took a child's name | 0 | 0 | 3 | 0 |
| unnameable | 2 | 7 | 11 | 13 |
| outcomes right, of 18 | 11 | 9 | 11 | 7 |
| good controls falsely flagged, of 10 | — | 5 | 1 | 1 |

### The conclusion all five share

**The fault is usually in the CHILD's name, not the parent's.** `n0262`'s child is called
*Intracellular vesicle transport*, but that child is a specific cluster of vesicle-transport
pathways: its name over-claims for its own contents. No parent name can strictly contain it, because
the child's name describes more than the child holds. The same is true of `n0592`'s *Sensory
transduction across modalities* and `n0474`'s *Regulation of cell-matrix adhesion turnover*.

Every attempt tried to fix this from the parent's side, and each failed differently -- 0 of 18, 3 of
9, 1 of 13. **The mechanism that would work is renaming the over-claiming child. It exists in the
code as the child re-ask, but it only triggers when a parent takes the child's name, which attempts
4 and 5 made first rare and then impossible.**

**Nothing is adopted.** The split checker is accepted on its own merits and the saving fixes below
are permanent, but no enforcement procedure is in force: the best of the five (lenient, 11 of 18) is
also the one with a known leniency defect, and the strict family refuses between 7 and 13 of 18 for
names that are mostly serviceable. The level-1 names currently in `theme_names.tsv` are the
split+widen run's, which includes 13 refusals that this entry says are mostly wrong.

### Two defects fixed along the way, independent of any of this

**The names table could hold several current rows per node.** A row is keyed on `theme_key`, which
changes when a node's children are renamed, so a re-run wrote a new row and `restamp` -- marking by
`prompt_version` alone -- left both current. **35 of 502 nodes had two.** A reader keyed by node
silently got whichever came last, which is how three enforced names appeared never to have been
saved. `restamp` now takes the key each node was written under, supersedes that node's stale rows,
and RAISES if any node would still end with more than one. Plus an assertion at save time: the name
written must be byte-identical to the last name that passed the check. It caught a real case on its
first run.

**`merge_tsv` wiped the file when a column was added.** It kept existing rows only when the stored
header exactly equalled the requested columns, so adding `same_theme` destroyed 2,237 rows of
`theme_names.tsv` -- restored from a backup taken minutes earlier. A header that is a PREFIX of the
requested columns is now a migration: old rows keep their values and the new column starts empty. An
unrelated header still rebuilds, which is deliberate and separately tested.

### Cost

$0.80 for attempt 1, $0.20 + $0.34 + $0.38 + $0.25 for attempts 2 to 5. **$1.97 for the sequence**,
inside every ceiling given. `name-v5` naming in total: $8.81.

## 2026-10-02 — DECLARED BEFORE THE RUN: child-first coverage procedure, and its pass mark

**Written before the procedure was run and before any result was seen.** The five earlier attempts
(entry above) all worked from the parent's side and all failed; they jointly point at the child's
name as the fault. This attempt inverts the order: the over-claiming CHILD is narrowed first, and
only then is the parent re-asked. The pass mark below is fixed now so the result cannot be scored
against a bar chosen after seeing it.

### PROCEDURE, per parent, after it is named with `name-v5`

**a.** Split check: child clusters strict, direct pathways lenient, as already built and accepted
(controls 1 of 10).

**b.** Covered → done.

**c.** For each uncovered CHILD cluster C, **the child goes first**: re-ask C with the `name-v5`
system prompt and C's own data, plus

> Your parent cluster also contains these pathways: *&lt;parent's direct pathway titles&gt;*.
> Give the tightest name true of your own members only.

The new child name must pass the split check against C's own children (where it has any), plus
collision and `invented_word`. Failing any of those, **C keeps its old name** -- a child is not made
worse to rescue its parent.

**d.** Re-ask the parent once, naming prompt and data, children shown under their CURRENT names
(so a child narrowed in step c is what the parent sees), plus

> Your name '&lt;P&gt;' does not cover: *&lt;uncovered items&gt;*. Give the tightest name that
> covers every child cluster and every direct pathway. Keep what your name got right; widen
> only as much as needed.

**e.** Split check again. Covered → done. Still uncovered → the parent and the uncovered child are
recorded `same_theme`, shown merged on the page. If only direct pathways remain uncovered, the
parent is recorded unnameable. A failing name is discarded, never kept.

**No step is tuned after this declaration.** If the procedure needs changing, it is a new procedure
with a new declaration, and this one is recorded as failed.

### EVALUATION

**Sample.** 40 level-1 nodes, drawn at random with a recorded seed, excluding the 18 problem nodes
and the 10 controls -- so the procedure is judged on nodes it was not designed against.

**Read.** The reviewer reads all 40 **blind**: the procedure's output and the `name-v5` name as
candidates A and B in shuffled order, with the node's children and direct pathway titles. The key is
written to a separate file and is not in the status document.

**PASS requires all three:**

1. the procedure's output judged **better or equal on at least 36 of 40**,
2. judged **worse on at most 2**,
3. the 10 controls flagged **at most once**.

**If PASS**, the procedure is adopted for all levels.

**If FAIL**, it is withdrawn, and the fallback is declared here rather than invented later: **keep
the `name-v5` names and show every parent that fails the split check with a visible
"name may not cover all contents" flag.** The flag is a disclosure, not a correction -- the reader
is told what the measurement found and the name is left alone.

### What is NOT in scope of this evaluation

The split checker itself is already accepted and is not re-litigated by this run. Nor is the
`name-v5` prompt, which stays byte-identical at digest `f3d1f074929df02a`.

## 2026-10-02 — DECLARED BEFORE THE BUILD: a size cap stated as a SHARE of the universe

**Aviyah's decision, recorded before step 3 runs.**

### The rule

> **CAP = 2 x the largest share held by a single curated top-level category, excluding Reactome
> "Disease".**

Computed from the measured counts in `scripts/size_cap_reference.py`:

| category | of its mapped universe | share |
|---|---|---|
| Reactome **Signal Transduction** | 469 / 3,233 | **14.5067%** — the reference |
| Reactome Metabolism | 460 / 3,233 | 14.2283% |
| largest GO generic-slim term (small molecule metabolic process) | 348 / 2,838 | 12.2622% |
| Reactome Disease — **EXCLUDED** | 787 / 3,233 | 24.3427% |

**CAP = 2 x 14.5067% = 29.0133% of the universe being built.**

At 10,770 that is **3,125 pathways**. A cluster larger than the cap is not a candidate when clusters
are cut from a Ward tree, applied **identically to real and scrambled trees**, so the support floors
are solved under the same rule they will be applied under.

The GO slim figure is not used in the rule; it is reported because it **agrees** -- 12.3% against
14.5% from a different ontology with a different mapping -- which is what makes the reference
something other than one number from one source.

### Why a share and not a raw count

**Reactome covers 30% of our universe.** 7,537 of 10,770 pathways reach no Reactome top-level
pathway, nearly all of them GO or BTM terms with no `reactome2go` entry. So Signal Transduction's
469 pathways are 469 out of the 3,233 that Reactome can see, not out of 10,770: as a raw count it
understates how much of a complete ontology that category would hold. Read as a share of its own
mapped universe, 14.5%, it says what a curator was willing to call one thing -- and that share is
what transfers to a universe of any size.

A raw count would also have to be re-derived every time the universe changed. A share does not.

### Why Disease is excluded

Reactome's largest top-level pathway is **Disease, 787 pathways, 24.3%** -- which would have set the
cap at 48.7%, nearly half the universe. It is excluded because it is **not one biology**: it is
Reactome's bucket for pathology, cutting across signalling, metabolism, immunity and development
alike. A cap is meant to bound how much biology one theme may claim, and anchoring it on a
cross-cutting container would bound almost nothing. The exclusion is one named category, declared
here with its reason, and not a filter that could be widened after seeing a result.

### Effect on the frozen 1,850 build -- INFORMATION ONLY

29.0133% of 1,850 is **537 members**. Exactly **one** cluster of the frozen
`v0.2.2-subset-1850-c50` build exceeds it: **n0781 at 819 members** -- the 819-member super-domain
the cohesion entry already identifies as the least cohesive theme in the build (0.125 at 200+
members, against a kNN-ball median of 0.068).

**The frozen build is NOT changed.** It keeps its 800 themes and its names. The figure is recorded
so the cap's severity is legible: at the scale we have already inspected, it would have removed one
theme, and that theme is the one every other measurement already flags.

### What the cap does not do

It is a ceiling on candidacy, not a cohesion test and not a recurrence test. A cluster under the cap
still has to pass the support floor for its size band; a cluster over it is simply never offered.
Nothing about the declared pipeline downstream changes: completion at inclusion 0.50, floors solved
on 10 calibration scrambles and confirmed once on 5 held-out, the recurrence gate, greedy consensus
at STRAY 0.10 / JACCARD 0.70, strict Hasse.

---

## 2 Oct 2026 -- The RUNS re-confirmation is a SAMPLED estimate at 10,770, not an exhaustive match

**DECLARED before the measurement ran.** `scripts/cut_trees.py`.

The RUNS ladder asks whether doubling the number of resampling runs still changes which groupings
recur: it matches the grouping pool of one block of runs against the pool of a disjoint block, and
reports the share with a partner at Jaccard >= 0.70. On the 1,850 build this was exhaustive --
roughly 45,000 groupings a side, every pair compared.

**At 10,770 it is not computable exhaustively.** The pools are about **407,000 groupings per 100
runs**, and the comparison is quadratic in the pool and linear in the bitset width:

> 407,420 x 407,420 x 169 words = **2.8 x 10^13 word-operations**, about **7.8 hours per direction**,
> four directions across the two pairs -- over a day of CPU for one re-confirmation, and it has to
> be redone whenever the cap or the cutoff moves.

So the matched share is **estimated from a random sample of the left-hand pool, each sampled
grouping compared against ALL of the right-hand pool**. Only *which* groupings are examined is
approximated; no comparison is approximated.

| parameter | value |
|---|---|
| sample size per direction | **5,000** groupings |
| sample seed | **20261002**, fixed in the script |
| estimator | share of sampled left groupings with a right partner at Jaccard >= theta |
| standard error at a 90% share | **0.42 pp** |
| reported | forward, backward, each with its standard error, and the worse direction |
| exhaustive when | the pool is <= 5,000 -- then the error is reported as 0.0 |

A 0.42 pp standard error sits far inside the margin a 90% pass mark needs: a true 90% reads as
89.2-90.8% at two standard errors, and a true 85% could not be mistaken for a pass. **The figure is
reported with its error and labelled sampled; it is never quoted as if exhaustive.**

### What this does not change

The pass mark is still **>= 90% in the worse direction**, declared before the run, on the two
disjoint pairs the subsample manifest reserves: **1-100 vs 101-200** and **1-200 vs 201-400**. The
sample affects the precision of the answer, not the question or the threshold.

### The superseded figure

`docs/status/OPEN.md` records "100 trees: 89.1%, 200: 91.4%" from the 1,850 work. That measurement
has **no recorded clustering space and no recorded inclusion cutoff** (logged in `docs/debt.md`), and
its dating places it on raw -- not centred -- vectors at inclusion 0.25. **Neither parameter is this
build's.** It is therefore not carried forward, not cited as the 10,770 answer, and the ladder is
measured again from the persisted trees under the current space, cutoff and cap.

---

## 2 Oct 2026 -- The RUNS rule was always about FINAL THEMES. The 2 Oct ladder mis-implemented it.

**Aviyah's note, recorded as the correction of record.** This does not change the rule. It records
what the rule has said since 25 Sep, and that a measurement taken against it on 2 Oct measured the
wrong population.

### The rule, as defined 25 Sep 2026

> **>= 90% of FINAL THEMES matched at Jaccard >= 0.70 between builds from disjoint tree blocks.**

The unit is a **theme**: a completed, support-gated, consensus-reconciled node with its exported
member list. Two builds are compared, each built from its own disjoint block of trees.

### What was measured on 2 Oct, and why it does not bear on the rule

`scripts/cut_trees.py --ladder` matched the **raw grouping pool** of one block of runs against
another's -- every deduplicated Ward cluster at or above three members, before completion, before the
support gate, before consensus. It reported 61.0% and 63.5% at 10,770 and 54.8% and 58.2% on the
1,850, against the 90% mark, and concluded that RUNS = 200 was not confirmed.

**That was a mis-implementation of this rule, not a new rule and not a new threshold.** The 90%
mark was never stated over the grouping pool. The pool contains thousands of clusters one subsample
produced and no other run reproduced -- about half of it, at median support 0.030 -- and the gate
exists to remove exactly those. Measuring the mark against a population that includes them tests
nothing the rule asks about.

**The figures stand as what they are** and are not withdrawn: they correctly describe grouping-pool
agreement, which is a real property of the method and is why `docs/status/2026-10-02-runs-ladder.md`
and the diagnostic are kept. **They are not evidence about RUNS.** No conclusion about RUNS = 200,
in either direction, follows from them.

**Two of my own statements from 2 Oct are wrong and are corrected here, not rewritten.** The entry
above ("The superseded figure") and the `docs/debt.md` entry "The RUNS pass mark has no quantity
attached to it" both assert that the rule never recorded what it was 90% *of*. **It did, on 25 Sep.**
The defect was in the implementation and in my reading of it, not in the rule. The debt entry is
corrected in place with a dated note; this paragraph is the record.

### The closest verified prior evidence

**Test 9 on the frozen 1,850** -- `recurrent_dag_c50` against `recurrent_dag_c50_seed1`, two full
builds, 100 runs each, master seed 0 against seed 1, everything else identical. This is the right
*statistic* on the right *unit*, and the nearest thing on record to the rule's conditions; it differs
in that the two builds draw their own subsamples rather than taking disjoint blocks of one sequence.

Reproduced exactly by `scripts/theme_match.py`, now committed, which also recovers the three figures
already in `OPEN.md` for this build -- mean 0.862, median 0.909, 53.2% at >= 0.9:

| direction | themes | mean | median | >= 0.50 | **>= 0.70** | >= 0.90 |
|---|---|---|---|---|---|---|
| seed 0 -> seed 1 | 800 | 0.862 | 0.909 | 95.8% | **86.9%** | 53.2% |
| seed 1 -> seed 0 | 801 | 0.863 | 0.909 | 96.6% | **85.9%** | 53.3% |

**86.9% is the forward direction, and it is the figure of record.** The **backward direction is
85.9%** and was not previously written down; the worse direction is therefore **85.9%**.

**The frozen build does not reach the 90% mark on the rule's own statistic** -- it is 3.1 points short
forward and 4.1 points short in the worse direction. That is a genuine shortfall against a declared
threshold and it is recorded as one. The rule as quoted does not say which direction the mark applies
to, and that is open.

### What a correct re-measurement requires

Two full builds from disjoint tree blocks -- trees 1-100 and trees 101-200 of the persisted sequence
-- each taken all the way through completion at inclusion 0.50, the per-size support floors, the
recurrence gate, greedy consensus and strict Hasse, then compared with `scripts/theme_match.py`. The
trees are already on disk and the build is `scripts/build_10770.py`; what it lacks is a row-range
option, since it currently builds from rows 1..N. **Not run, and not to be run until Aviyah decides**
the direction question above and whether the mark survives a frozen build that misses it.

---

## 2 Oct 2026 -- The mark applies to the WORSE direction, and it stands unchanged

**Aviyah's decision.** Two questions left open by the correction above are now closed.

**1. Direction.** The rule's ">= 90% of final themes matched at Jaccard >= 0.70" applies to the
**worse of the two directions**. A build with fewer themes can match a build with more while the
reverse fails, and the rule is about agreement, not coverage; taking the worse direction is what
makes it symmetric. So the frozen 1,850's figure under the rule is **85.9%**, not 86.9%.

**2. The 90% mark stands, unchanged.** It is not lowered to accommodate a build that misses it.

### The frozen 1,850 demo build is below the declared stability mark

**It scores 85.9% in the worse direction against a 90% mark, and it is not rebuilt.**

**Why it is below.** The frozen build was built at **RUNS = 100**. Establishing that 100 runs is not
enough is precisely what the ladder exists to do, so 85.9% at 100 runs is **consistent with the
ladder's purpose, not a contradiction of it**. It is evidence for the rung structure, not evidence
against the build's method.

**Why it is not rebuilt.** Its **names depend on its exact clusters**. A theme's name is written from
its members' names and descriptions, and a request is keyed by its member set and its children's
names; rebuilding at a higher RUNS changes the member sets and therefore invalidates the names. The
287 leaf names and 215 level-1 names, and the five coverage evaluations behind them, all refer to
these clusters.

**So it is kept as it is, and the shortfall is stated rather than hidden.** This is a **declared
limitation of the demo**, shown on the demo's landing page: the demo shows an ontology built at 100
resampling runs, whose theme set reproduces at 85.9% against an independent rebuild, below the 90%
stability mark this project declares for a build it would call stable.

A reader of the demo is entitled to that number. `data/experiments/theme_match_c50_seed0_vs_seed1.json`
holds it, `scripts/theme_match.py` reproduces it, and it is not to be omitted from any public
description of the demo.

---

## 2 Oct 2026 -- DECLARED BEFORE THE RUN: RUNS is chosen from FINAL THEMES

**Pre-registration. Written before the measurement ran; nothing below was chosen after seeing a
result.** This replaces the grouping-pool measurement of earlier today, which was a
mis-implementation of the rule and is recorded as such above.

### The procedure

For each rung, **two separate full builds** are run, each from its own disjoint block of persisted
trees, each through the entire declared pipeline:

1. the size cap, **29.0133% of the universe**, applied at cut time;
2. completion at **inclusion 0.50**;
3. support floors solved on the **10 calibration scrambles**, at the **same number of runs as the
   build**;
4. the gate at **max(declared m = 0.33, the per-size floor)**;
5. greedy consensus at **STRAY 0.10 / JACCARD 0.70**;
6. strict Hasse edges.

The two finished theme sets are then matched with `scripts/theme_match.py`.

**Both builds in a rung use the SAME scramble trees for their floors.** The floor is a property of a
size stratum under the null, not of the block being cut, and giving each block its own null would let
the two builds be gated differently -- which would show up as theme disagreement that was really
threshold disagreement.

### The pass rule

> **PASS if >= 90% of final themes have a partner at Jaccard >= 0.70 in the WORSE direction.**

### The rungs, in order

| rung | block A | block B | RUNS if it passes |
|---|---|---|---|
| 1 | trees 1-100 | trees 101-200 | 100 |
| 2 | trees 1-200 | trees 201-400 | 200 |

**RUNS = the smallest passing rung.** **If neither rung passes, stop and report** -- no third rung,
no new trees, and no adjustment to the mark.

### What happens after a rung passes

The confirmatory build runs at that RUNS on trees 1..RUNS, with the floors solved on the 10
calibration scrambles and **confirmed ONCE** on the 5 held-out scrambles: overall FDR <= 0.01, each
stratum <= 0.02, and **nothing re-solved after the held-out set is touched**.

**Nothing is frozen. Aviyah decides.**

---

## 2 Oct 2026 -- The completion stage was reimplemented. Verified byte-identical.

**An implementation change only. NOTHING DECLARED CHANGES** -- not the cap, not the inclusion
cutoff, not the floors, not the strata, not the gate, not the consensus parameters, not theta, not
the pass mark, not the rungs. The same build comes out.

### What changed

`family_members` completes a grouping by walking `for p in bits.unpack(candidates)` and making two
NumPy calls per candidate pathway. Completion runs over the WHOLE pool, so at 10,770 and 100 runs
that is ~277,000 groupings holding roughly 17 million (grouping, candidate) pairs -- about 34 million
NumPy calls, whose per-call overhead dominates the arithmetic entirely.

`family_members_fast` replaces that loop with one vectorised bit-extraction per count, and indexes
the ``(runs, candidates)`` block directly rather than slicing whole rows -- `records_present[runs]`
materialises every word of every run, which is most of the memory traffic at this scale. Same
copies, same union, same `min(holds/could, 1)`, same candidate order. **The original is kept and is
still the default**; `--completion fast` selects the new one.

A sparse run-by-pathway matrix formulation was considered and rejected: the per-grouping copy set is
irreducibly a Python structure, so that form moves the same total bit-work into something harder to
prove equal.

### Verification -- `scripts/verify_completion.py`, which exits non-zero on any disagreement

`prepare` and `score` run ONCE and both implementations consume the same pool, so the comparison is
not between two differently-loaded machines.

| checked | groupings | completed | identical | cached side byte-for-byte |
|---|---|---|---|---|
| the 1,850 universe, 100 runs | 49,700 | 48,266 | **yes** | n/a |
| 10,770 `real_r00001-00100` | 285,260 | 276,725 | **yes** | **yes** |
| 10,770 `seed03001_n100` | 332,429 | 329,392 | **yes** | **yes** |

"Identical" means the completed sets match key-for-key and bitset-for-bitset, and the inclusion
floats are compared for **equality, not within a tolerance** -- an inclusion is rounded and exported,
so a last-bit difference would be a different build. "Byte-for-byte" means the fast path re-cut a
side whose `.npz` had been written by the original and the two files were compared as bytes.

### The speed-up, stated for what was measured

**On the completion stage: 1.8x to 2.2x.** That is the measured result.

**A per-side figure is NOT claimed from this measurement.** The verification timed four stages --
load, prepare, matching, completion -- which sum to 93-99s, where rung 1 measured whole sides at
**195s (real) and 281-339s (scramble)**. So roughly half of a side is in stages the verification did
not time: families (seed absorption), and the family-support and selection pass. The selection pass
calls the same completion function and therefore also speeds up, so the partial four-stage ratio of
1.15-1.33x is neither the true per-side figure nor a bound on it, in either direction. `cut_side` now
records every stage and its peak memory, so the complete split is measured on the next side rather
than inferred from this one.

---

## 2 Oct 2026 -- Two optimisations CONSIDERED AND NOT BUILT, and one cache defect

**Aviyah's decision, on the measurements below. Implementation only; NOTHING DECLARED CHANGES.**

### NOT BUILT: persisting per-(grouping, run) match results

The idea was to store each match answer once and assemble any block's support by counting stored
answers, reusing them across blocks, rungs, the confirmatory build and future re-cuts. **The reuse
is mostly either impossible or already in place.**

**Cross-block reuse is impossible without changing the declared matching rule.** The rule compares a
grouping against a run's clusters using `extras = |C n draw(origin_run(g))| - cover`, where
`origin_run(g)` is the lowest-numbered run **in the block** that recorded `g`. So the answer for a
given (grouping, run) pair depends on which runs are in the block. The ladder's blocks are **disjoint
by construction** -- 1-100 against 101-200 -- so a grouping's origin run is necessarily different in
the two, and nothing computed for one block is valid for the other.

**Rung and confirmatory reuse already exists.** The completion cache keys a finished side on
(space, universe digest, cap, inclusion cutoff, side), and the confirmatory build at RUNS = 200 on
trees 1..200 reads exactly the side labels block A already wrote. It pays nothing for matching today.

**What a store would actually have bought:** an inclusion-cutoff re-cut. Matching precedes
completion, so changing the cutoff invalidates the completion cache while leaving matching unchanged
-- about **175 s per side** of load, prepare and matching, at roughly **1 GB per block** on disk. A
cap change invalidates it entirely, since the cap decides which clusters exist.

**Not built.** One narrow saving on a stage that is not re-run often, against new persisted state in
the most intricate part of the pipeline.

### NOT BUILT: the size filter in matching

**The bound is correct.** Acceptance needs `cover >= theta x union` with `union = shared + extras`,
and `extras >= 0` because a grouping is contained in its origin run's draw, so
`|C n draw(origin)| >= |g n C| = cover`. Hence `cover >= theta x shared`, and since `cover <= |C|`, a
cluster with `|C| < theta x shared` can never be accepted. The subtle part is that the winner is
chosen by greatest cover BEFORE the theta test, so pruning could promote another candidate -- and the
argument that this cannot change the outcome is that a filtered-out winner had
`cover <= |C| < theta x shared <= theta x union` and would have been rejected anyway, while any
promoted candidate has no more cover and is rejected by the same inequality.

**The code disagrees with the argument, and the code was not trusted.** Switching the filter on moved
**34,637 of 49,700 supports** on the real 1,850 pool, and moved them **upward** -- which the argument
says is impossible. The disagreement was not resolved, so the filter is **off by default** behind a
`size_filter` setting, is not used anywhere, and is kept only so the contradiction stays reproducible.
Measured upside was 4.91s to 4.27s at 1,850: about 13% of a stage worth a third of a side.

**What the attempt did establish, and this is worth keeping:** with the filter off, the `matrix`
matching path is now verified **exactly** equal to the `tree` reference on the real 1,850 pool --
support, copy keys, and every copy bitset -- at 4.70s against 239.39s. That equivalence had only ever
been checked on hand-built fixtures of a few dozen points, which is why they passed while the real
pool diverged. **A reference implementation that is only ever exercised on toy inputs is not a
reference.**

### A CACHE DEFECT, recorded because it nearly entered a measurement

The size filter was added to `recurrent.py` **while the rung-2 side-cutting loop was running**. Each
side is a fresh process that imports the module at startup, so a side beginning after the edit was
computed with an unverified change: `seed03002_n200` produced **40,809 families where every clean
side of the same kind produces 428,000-429,000**. The file was indistinguishable from a valid cache
entry, and nothing recorded which code had written it.

Two sides were deleted and recut. **The fix is provenance:** every cached side now carries a
sha256 of `recurrent.py` plus the settings that affect its bytes, and a cache hit whose fingerprint
differs **raises** rather than being consumed. `--allow-stale-cache` is the explicit override, for
use only after two implementations have been proved byte-identical.

**The rule this establishes: do not edit a module while a job that imports it is running.** The
defect was not the filter; it was editing underneath a running measurement.

---

## 2 Oct 2026 -- Seed absorption reimplemented as an exact join. Verified byte-identical.

**Implementation only. NOTHING DECLARED CHANGES** -- not the variant rule, not the allowance, not
the seed order, not the family lists. `families(settings={"families": "joined"})` is now the default
for the 10,770 build; `"indexed"` and `"pairwise"` remain callable, and `"pairwise"` is still the
reference.

### What changed

`_variant_shortlist` precomputed, for every grouping, every grouping it might be a variant of. Three
things were wrong with that at scale, and none of them is the rule:

1. **It computed candidate lists for groupings that never become seeds.** A claimed grouping is
   never a seed and never needs its list; at 1,850 only 19,324 of 48,266 become seeds, so ~60% of the
   work was discarded. The join generates candidates **lazily, per seed**.
2. **It indexed every MEMBER**, so a common pathway carried a posting list of every grouping holding
   it. The join indexes **prefixes only**: 6.3x fewer postings at 1,850, and candidate pairs fall
   from 55.3M to 26.5M.
3. **It verified one pair at a time** in Python. The join verifies a seed's whole candidate block in
   NumPy, using `|A \ B| = |A| - |A n B|`.

**The two-sided prefix filter is exact, and the proof is in `_prefix_index`.** If the prefixes of
`A` and `B` are disjoint under a fixed global order, then all `k_A + 1` members of `A`'s prefix lie
outside `B`, so `|A \ B| > k_A`; since `|A n B| <= |A|`, the rule's allowance cannot reach that, so
the pair is not a variant. Variants therefore always share a prefix element, and `is_variant`'s rule
still decides every surviving pair.

### Verification

| checked | families | identical | cached side byte-for-byte |
|---|---|---|---|
| hand-computed fixture + generated pools | - | **yes** | n/a |
| pools whose overlaps sit only in COMMON pathways | - | **yes** | n/a |
| pools with NON-CONTIGUOUS grouping ids | - | **yes** | n/a |
| the 1,850 universe, 100 runs | 19,324 | **yes** | n/a |
| 10,770 `real_r00001-00200` | 161,852 | **yes** | **yes** |
| 10,770 `seed03001_n200` | 429,261 | **yes** | **yes** |
| `seed03001_n200` re-cut in a NORMAL build and byte-compared | 429,261 | **yes** | **yes** |

"Identical" means the same seeds and the same family LISTS in the same order, not merely the same
partition.

### It failed its first at-scale run, and the gap that hid the bug

The first attempt returned **161,853 families against 161,852** -- one grouping wrongly left
unclaimed. The cause: the posting arrays hold **grouping ids**, which are the sparse keys of the
completed dict, and they were filtered against a **row index** into the stacked block. Every
existing test passed, because they all pass `range(n)` as the candidate list, where a grouping's id
EQUALS its row and the two are indistinguishable. **A test suite that only ever uses contiguous ids
cannot see an id/row confusion.** There is now a test with deliberately sparse ids, carrying
assertions that stop it quietly becoming the contiguous case again.

### Measured, on one 200-run scramble side in a normal build

| | indexed | joined |
|---|---|---|
| families stage | 679.5s | **345.1s** (2.0x) |
| whole side | 977s | **689s** (1.42x) |
| **peak memory** | **21.7 GB** | **8.2 GB** (2.6x less) |

**Peak is the consequential number.** At 21.7 GB a single side nearly filled this 36 GB machine, and
an attempt at two in parallel drove it into swap and stalled both. At 8.2 GB, **three sides fit in
24.6 GB and leave 11.4 GB for the operating system.**

**`families` is still the dominant stage even so** -- 399.5s of a 677.8s side, 59% -- so the join
halved it without displacing it. Matching is 212.4s (31%) and completion, already vectorised, is
30.0s (4%).

---

## 3 Oct 2026 -- RUNS = 200. The declared 90% stability mark is NOT MET, and is NOT changed.

**Aviyah's decision, on the ladder measured 2 Oct.** RUNS = **200**, the best measured rung. The
declared mark stands at **>= 90% of final themes matched at Jaccard >= 0.70 in the worse direction**,
and **the build does not reach it.** The mark is not lowered, and the shortfall is recorded rather
than absorbed.

### The ladder, in full

Each rung is two separate full builds, one per disjoint block of persisted trees, each through the
whole declared pipeline -- cap 29.0133% at cut time, completion at inclusion 0.50, floors solved on
the 10 calibration scrambles at the build's own run count, gate at `max(m = 0.33, floor)`, greedy
consensus at STRAY 0.10 / JACCARD 0.70, strict Hasse -- then matched theme-for-theme by
`scripts/theme_match.py`. The held-out scrambles were NOT read by any ladder block.

**Rung 1 -- trees 1-100 vs 101-200, RUNS = 100 if it passed**

| direction | themes | roots | mean | median | >= 0.50 | **>= 0.70** | >= 0.90 |
|---|---|---|---|---|---|---|---|
| A -> B | 5,408 | 192 | 0.866 | 0.917 | 96.6% | **85.5%** | 55.3% |
| B -> A | 5,404 | 198 | 0.866 | 0.917 | 96.4% | **85.9%** | 55.2% |

**Worse direction 85.5% -- FAIL.**

**Rung 2 -- trees 1-200 vs 201-400, RUNS = 200 if it passed**

| direction | themes | roots | mean | median | >= 0.50 | **>= 0.70** | >= 0.90 |
|---|---|---|---|---|---|---|---|
| A -> B | 6,244 | 203 | 0.878 | 0.923 | 97.1% | **87.9%** | 57.4% |
| B -> A | 6,209 | 209 | 0.881 | 0.929 | 97.9% | **88.5%** | 58.1% |

**Worse direction 87.9% -- FAIL.** No declared rung passes, so the ladder stopped there: no third
rung, no new trees, no change to the mark.

### What the ladder established

**The run count genuinely drives theme stability, and 200 is still not enough.** Doubling the runs
gained **2.4 points** in the worse direction, 85.5% to 87.9%. Three independent measurements now sit
below the mark and close together:

| measurement | runs | worse direction |
|---|---|---|
| frozen 1,850, test 9 (seed 0 vs seed 1) | 100 | 85.9% |
| 10,770, rung 1 | 100 | 85.5% |
| 10,770, rung 2 | 200 | **87.9%** |

The 100-run figures agree to 0.4 points across universes six times apart in size, which is why the
shortfall reads as a property of the method at this run count rather than of either dataset.

**Rung 2 is better on every other axis too**: 6,244 themes against 5,408, and effectively unplaced
down from 379 to 141 (root-only 330 to 117).

**Extrapolation, labelled as such and not acted on:** at 2.4 points per doubling, 400 runs would
land near 89-90% and 800 near 90-91%. That is a line through two points. Rung 3 was **not run**; only
an estimate of its cost was prepared.

### Consequence for the build

RUNS = 200 is adopted as the best measured setting, and any description of a 10,770 build must carry
the figure: **its theme set reproduces at 87.9% against an independent rebuild from disjoint trees,
below the 90% mark this project declares for a build it would call stable.** The same honesty marker
the frozen 1,850 demo carries at 85.9%.

### Also considered and not built

Recorded in full in the entries of 2 Oct: **per-(grouping, run) match storage** -- dropped because
the matching rule reads each grouping's block-dependent origin run, so cross-block reuse is
impossible, while rung and confirmatory reuse already come from the completion cache, leaving only
inclusion-cutoff re-cuts; and the **size filter in matching** -- dropped because the bound is a
correct necessary condition yet switching it on moved 34,637 of 49,700 supports upward, which the
argument says cannot happen, so proof and code disagree and the code is not trusted.

---

## 3 Oct 2026 -- POST-HOC AMENDMENT: gene baselines are held to THEMA's own size cap

**THIS IS POST HOC AND IS RECORDED AS POST HOC.** It was written after seeing that 9 of the 12 gene
baselines beat THEMA on raw recovery while holding most of the universe in a single cluster. A rule
written after seeing the result it adjudicates is weaker evidence than one written before, and
nothing below pretends otherwise.

### The amendment

> **A gene baseline whose largest cluster exceeds 29.0133% of the universe is DEGENERATE and is
> excluded from tests 3 and 4.**

29.0133% is **THEMA's own declared size cap** -- 2x the largest share a single curated top-level
category holds, excluding Reactome Disease (`DECISIONS.md`, 2 Oct). The build is forbidden to offer a
candidate cluster larger than that share. **A baseline is now held to the same ceiling the build is
held to.** The threshold is therefore not chosen to produce an outcome: it is the one number this
project already declared for "too big to be one theme", applied to the comparison instead of only to
the build.

### Why the marks need it

Tests 3 and 4 are stated over **raw recovery**: THEMA's recovery must exceed every gene baseline.
Measured on the frozen 10,770, the winning baseline is `kappa@25`, whose largest cluster holds
**97.3% of the universe**. Its own chance rate is 94-100% and its lift is 1.0x. **A mark on raw
recovery is won by putting everything in one cluster**, so applied literally it produces a failure
that carries no information. `compare_baselines.py` already warned of exactly this in a code comment
-- "the chance rate travels with the winner" -- and the mark did not inherit the caution.

### What it excludes, measured

| arm | largest cluster | |
|---|---|---|
| `kappa@25` | 97.3% | excluded |
| `overlap@25` | 82.4% | excluded |
| `jaccard@25` | 65.4% | excluded |
| `jaccard@50` | 62.6% | excluded |
| `kappa@50` | 56.0% | excluded |
| `ochiai@25` | 44.8% | excluded |
| `jaccard@100` | 43.8% | excluded |
| `overlap@50` | 43.0% | excluded |
| `ochiai@50` | 35.4% | excluded |
| **`ochiai@100`** | 23.1% | **kept** |
| **`kappa@100`** | 23.6% | **kept** |
| **`overlap@100`** | 15.7% | **kept** |

The TF-IDF arms are unaffected: 9.2%, 5.7% and 4.0%.

### Standing

**Verdicts reached under this amendment must be labelled "under the post-hoc baseline amendment"
wherever they are reported**, and are not interchangeable with a verdict under the mark as it was
declared. The mark itself is unchanged; this changes which baselines count as baselines.

---

## 3 Oct 2026 -- DECLARED BEFORE COMPUTATION: the graded specificity measure

**Written before any of it was computed. INFORMATIONAL, NOT A GATE** -- it grades nothing and
licenses nothing. Its purpose is to settle a disagreement the recovery figures cannot: THEMA leads
every arm on recovery and trails the TF-IDF arms on lift, and that happens only because its chance
rate is ~21% against their 0.9-7.8%. Recovery rewards placing a pair together at any grain; lift
rewards a low base rate. **Neither compares arms at the same specificity, and this does.**

### The measure

For every curated pair in tests 3 and 4, and for every band-matched random pair:

**(a) Smallest shared theme size.** The number of members of the smallest theme containing BOTH
pathways; **infinite** when they share none. For a flat clustering arm, the size of their shared
cluster, infinite when they are in different clusters. Smaller is more specific: being put together
in a theme of 8 is a sharper claim than in a theme of 3,000.

**(b) Hop distance, THEMA only.** Let `m(p)` be the smallest theme containing `p`, ties broken by
lowest node id. The hop distance is

> `min over T of [ up(m(a), T) + up(m(b), T) ]`

over themes `T` that are ancestors-or-self of both `m(a)` and `m(b)`, where `up(x, T)` is the fewest
parent-edges from `x` to `T` and `up(x, x) = 0`; **infinite** when no common ancestor exists. So 0
means the two pathways' tightest themes are the same theme, and larger means further apart in the
DAG. Because `members(child)` is a subset of `members(parent)`, any common ancestor does contain
both pathways, so this is a distance between their tightest homes rather than a restatement of
co-membership.

### The null

The **band-matched random-pair null, with the corrected zero-gene band**. The first grid run recorded
every random pair of exactly zero gene overlap as undefined, because `0.0` is falsy in Python and the
code read `jaccard(...) or -1.0`; that emptied the most important band. Fixed, and the zero-gene
cells now carry 84,896-100,346 null pairs each.

### What is reported, per gene-overlap band and per source

For THEMA, the three non-degenerate gene baselines and the TF-IDF arms:

1. **Median smallest shared theme size**, curated against random.
2. **AUROC**: the probability that a curated pair is more specific than a random pair, by smallest
   shared theme size, **ties counted as half**. 0.5 is chance; 1.0 is perfect separation. Computed
   from midranks over the combined sample, so an infinite size on either side is handled as a tie
   among all such pairs rather than dropped.
3. **Recovery at specificity cut-offs**: the share of pairs whose smallest shared theme has **<= 10**,
   **<= 50**, **<= 200** members, **each beside its random-pair rate**. This is recovery and
   specificity in one number, which is the comparison the plan's marks lack.

**No pass mark is attached to any of it, now or later, without a separate dated decision.**

---

## 4 Oct 2026 -- DECLARED BEFORE ANY BUILD: the HiDeF comparison decision rule

**Aviyah's text, copied verbatim as the first step of the run, before HiDeF was installed and
before anything was computed.** It is reproduced exactly as given, including its headings.

> ## §0 Decision rule (declare first, copy into DECISIONS.md before any build)
>
> - Primary metric: specificity AUROC (smallest shared theme size, siblings vs random pairs), as in
>   scripts/specificity_grid.py.
>   - Computed for Reactome siblings and GO siblings separately.
>   - Computed at zero gene overlap (the current headline) and with all overlap bands pooled.
>   - That gives 4 cells per arm.
> - Comparison: paired bootstrap over pairs, 2,000 resamples, seed 0. Report the 95% CI of
>   (HiDeF - THEMA) per cell.
> - Rule:
>   - If THEMA is not significantly better than HiDeF in any of the 4 cells (every CI includes or
>     exceeds 0), and HiDeF's test-4 zero-gene sibling recovery is >= THEMA's minus 2 points on both
>     Reactome and GO, then HiDeF is "at least as good" and we switch engines.
>   - Otherwise THEMA stays, and HiDeF and CliXO are reported as baselines.
> - Everything else (shape, stability, null arm, curated ceiling, fan-out subset, hop distance) is
>   reported, not decisive.
> - Nothing is re-tuned after results are seen. If a HiDeF parameter turns out to matter, report it
>   as a post-hoc sensitivity, labelled as such.

### What this commits us to

**A declared possibility of losing.** The rule is written so that HiDeF can win: if it matches THEMA
on all four AUROC cells and comes within 2 points on zero-gene sibling recovery for both
hierarchies, the engine changes. That is the point of writing it before the build rather than after.

**One primary metric, four cells, and nothing else decisive.** Shape, stability, the null arm, the
curated ceiling, the fan-out subset and hop distance are all reported and none of them can rescue or
sink either arm. This is deliberate: the project has twice had a result re-read through whichever
statistic favoured the preferred answer, and the rule removes that option in advance.

**Parameters are fixed before the run.** HiDeF gets its published defaults and a declared graph
(symmetric kNN on cosine, k = 15); k = 30 is a labelled sensitivity run afterwards, not an
alternative to be chosen between. Any parameter that turns out to matter is reported as a post-hoc
sensitivity and cannot change the verdict.

---

## 5 Oct 2026 -- THE HIDEF VERDICT, under the rule declared on 4 Oct: THEMA STAYS

**The rule was written into this file before HiDeF was installed** (4 Oct, "the HiDeF comparison
decision rule"), and it was written so HiDeF could win. It did not. Full working in
`docs/status/2026-10-04-hidef-comparison.md`.

### The four cells, quoted

Primary metric: specificity AUROC -- smallest shared theme size, siblings against band-matched
random pairs. Paired bootstrap over pairs, 2,000 resamples, seed 0.

| cell | n | THEMA | HiDeF | HiDeF - THEMA | 95% CI | |
|---|---|---|---|---|---|---|
| Reactome siblings, zero gene overlap | 5,753 | **0.8841** | 0.7898 | -0.0943 | [-0.1004, -0.0878] | **THEMA significantly better** |
| Reactome siblings, all bands pooled | 9,396 | **0.8827** | 0.8228 | -0.0599 | [-0.0642, -0.0554] | **THEMA significantly better** |
| GO siblings, zero gene overlap | 19,828 | 0.6959 | **0.7041** | +0.0081 | [+0.0047, +0.0115] | HiDeF ahead |
| GO siblings, all bands pooled | 45,832 | 0.7342 | **0.7516** | +0.0173 | [+0.0152, +0.0196] | HiDeF ahead |

### Test-4 zero-gene sibling recovery, quoted

| hierarchy | THEMA | HiDeF | difference | within the declared 2-point tolerance? |
|---|---|---|---|---|
| Reactome siblings | **89.0%** | 79.1% | **-9.9 points** | **no** |
| GO siblings | 59.2% | **64.4%** | +5.2 points | yes |

### The verdict

> **THEMA STAYS. HiDeF and CliXO are baselines.**

The rule required BOTH that THEMA be not significantly better in any of the four cells AND that
HiDeF's zero-gene recovery be within 2 points on both hierarchies. **Two of four cells have THEMA
significantly better, and HiDeF misses the recovery tolerance on Reactome by 9.9 points.** Either
failure alone decides it.

**CliXO is a baseline in name only: it was never built.** Not on PyPI, no binary in DDOT, and four
plausible source repositories return *Repository not found*. Recorded so the absence is not read as
a result.

### What the verdict does NOT say

**It is not a clean win.** THEMA loses the primary metric on GO in both cells, by small but
interval-excluding margins, and it costs roughly 50x the compute -- 2.1 minutes and 2.13 GB for all
of HiDeF against a cold THEMA build.

> **AMENDED 5 Oct 2026, after Part B. The 50x above is kept as the historical figure** -- it was
> true of the build as originally run and of every cost statement made before today. **It is now
> about 4x.** Measured, end-to-end from the embeddings:
>
> | stage | measured |
> |---|---|
> | 200 Ward trees, 0.58 s each | 116 s (~2 min) |
> | one real side, after the B2 optimisation | 277 s |
> | gate + consensus + Hasse + export | 67 s |
> | **THEMA total** | **~460 s (~7.7 min), 7.8 GB peak** |
> | HiDeF, all of it | 126 s (2.1 min), 2.13 GB peak |
> | **ratio** | **3.7x, reported as ~4x** |
>
> **Plus a one-time calibration per configuration**: ten scramble sides at 406 s each with B2,
> ~4,060 s (~1.1 h), against ~9,590 s (2.7 h) as originally cut. It is one-time because the floors
> are now stored and loaded by `--floors-from`, which refuses if any of n, runs, scramble_rows,
> size_cap, inclusion_cut, universe_digest or space differs -- so *per configuration* is exact, not
> a hedge. Change the universe or the cap and the 1.1 h is owed again.
>
> **The reduction is byte-identical**: all three configurations reproduce the frozen build on nodes,
> members, edges and unplaced. **Nothing about the method, the verdict, or any number above the
> compute line changes** -- this is the same build, produced more cheaply. **And HiDeF rejects the scrambled null completely** (zero
communities on both held-out seeds, each asserted byte-for-byte against the build's own persisted
tree), so noise rejection is not the distinguishing property THEMA was expected to have.

**What THEMA still has that HiDeF does not:** a *quantified* error rate -- held-out FDR 0.00285
overall, 0.0147 worst stratum -- and much finer themes, 6,244 at median size 9 against 472 at median
59, which is what lets it place 25.7% of tight GO sibling pairs in a theme of 10 or fewer where
HiDeF places 0.0%.

**A post-hoc maxres sensitivity, which cannot change the verdict and does not.** At maxres 50 and
100 HiDeF's recovery condition is satisfied (-0.1 and +1.3 points), but THEMA remains significantly
better in both Reactome cells. The sensitivity changes which condition fails, not whether one does.

## 2026-10-06 — Engine search: §0 declared before anything was built

**Written and committed before a single engine ran.** Copied verbatim from Aviyah's brief of 6 Oct
2026, including its headings and emphasis. Nothing below was edited after any result was seen; the
only text I have added is this paragraph, the three clarifications at the end (each marked
**CLARIFICATION** and each a reading of the brief, not a change to it), and the running note of
what was built.

Branch `engines-2026-10`. The frozen build (`recurrent_dag_10770`, tag `v0.3.0-10770-runs200`) and
the naming code are not touched.

### The goal

Find the best ENGINE inside THEMA's framework on the full 10,770. Only "what groupings each run
proposes" changes. Everything downstream stays identical to v0.3:

- the 80% samples (same recorded sample seeds per run)
- 200 runs
- two-sided matching at theta 0.70 on shared members
- completion with inclusion >= 0.5
- consensus (stray 0.10, Jaccard 0.70)
- size cap 3,125 at cut time
- min_size 3
- per-size floors calibrated on scramble seeds 3001-3010
- FDR held out on 4001-4005 (read once): <= 0.01 overall, <= 0.02 per stratum
- containment DAG

Floors do not transfer between engines. Each engine is calibrated on the SAME scramble seeds,
regenerated with the build's function and asserted equal to the persisted ones.

### Arms

- **A. THEMA-Ward:** frozen v0.3, as is.
- **B. THEMA-L:**
  - per run, a symmetric kNN graph (k = 15, cosine, union of directed edges, weight = cosine) on
    that run's sample;
  - one Leiden split (leidenalg, modularity with resolution) at that run's resolution;
  - resolutions are 200 values log-spaced from 0.001 to 100, assigned to runs in a random order
    (seed 0), so runs 1-100 and 101-200 both span the full range;
  - candidates = every community of >= 3 members.
- **C. Pooled:** per run, candidates = that run's Ward tree clusters (existing trees) u that run's
  THEMA-L split (same sample).
- **D. Paris:**
  - per run, scikit-network Paris on the same kNN-15 graph;
  - candidates = every merge of >= 3 members.
- **E. HDBSCAN:**
  - UMAP (20 components, n_neighbors 15, min_dist 0.0, cosine, random_state 0), fitted ONCE on all
    10,770, and once per scramble seed on that seed's full matrix;
  - per run, HDBSCAN (min_cluster_size 3, min_samples 3) on that run's rows;
  - candidates = every cluster of the condensed tree with >= 3 members.
  - Stated limitation: UMAP has seen all pathways, so resampling is weaker for this arm.
- **F. Average linkage (UPGMA):**
  - per run, average-linkage agglomerative clustering on cosine distance of that run's centred
    vectors (fastcluster or scipy; the same samples as Ward);
  - candidates = every merge of >= 3 members;
  - this arm needs its own trees for the real runs and for every scramble seed.
- **References (not candidates):** HiDeF k15 maxres 25 and 50 (existing builds), and the plain
  single Ward tree on all 10,770 with every merge >= 3 as a theme (no sampling, no gate).

### Eligibility gates (a candidate must pass all three)

- **G1:** held-out FDR <= 0.01 overall and <= 0.02 in every stratum.
- **G2:** stability >= THEMA-Ward's minus 2 points. Stability = final-theme match between the build
  from runs 1-100 and the build from runs 101-200, worse direction, Jaccard >= 0.70, computed by
  the same script for every arm.
- **G3:** effectively unplaced <= 5% of pathways.

### Primary scores

- 16 = 4 cells (Reactome siblings and GO siblings x zero gene overlap and pooled) x 4 theme-size
  bands (3-10, 11-50, 51-200, 201-500).
- Each score is the band-restricted specificity AUROC (the C3 method from
  `docs/status/2026-10-05-speed-and-evaluation.md`).
- CIs: paired cluster bootstrap over curated parents, 2,000 resamples, seed 0.
- Margin: 0.02.

### Decision

1. **Dominance.** An eligible arm X is dominated if some eligible arm Y is better than X by > 0.02,
   with the paired CI excluding 0, in at least one score, and is not worse than X by > 0.02 (CI
   excluding 0) in any score.
2. **Among non-dominated arms, max-min.**
   - An arm's shortfall = the largest, over the 16 scores, of (best eligible arm's AUROC - this
     arm's AUROC).
   - The smallest shortfall wins.
   - Ties within 0.01 go to fewer knobs, then to the lower full-build wall time including
     calibration.
3. **The winner is a CANDIDATE only.** Adoption happens after tests 5 and 6 compare it with THEMA
   v0.3 and HiDeF under a separately declared rule. Nothing is frozen.

### Reported, not decisive

- tests 3 and 4 (recovery and lift by band)
- shape against GO and Reactome
- the 4-cell overall AUROC
- hop distance
- themes per size band
- timing including calibration, and peak RAM

**Nothing is re-tuned after results are seen. Any later change is a labelled post-hoc sensitivity.**

### Budget

The total budget is 12 hours. Priority order: B, C, F, D, E. Arms are dropped from the end if over
budget, and the reason reported. Never mix universe sizes.

---

### CLARIFICATION 1, recorded before building: what "the same 80% samples" pins

The brief fixes the samples by their recorded per-run seeds, so every arm sees the identical 200
draws of 8,616 pathways. Arm A's trees are already persisted against those seeds, and every new arm
regenerates the draw from the same seed and asserts it equals the persisted `present` bitset before
clustering anything. An arm that disagrees on a single drawn pathway is a bug, not a result.

### CLARIFICATION 2, recorded before building: Ward records nodes up to HALF the draw

v0.3's Ward path records dendrogram nodes with `min_size <= size <= take // 2` (4,308 of an 8,616
draw), and then the 29.0133% size cap (3,125) is applied at cut time. The half-draw rule is a
property of a dendrogram, not of the framework: it exists because a node above half the draw is
defined by its complement. **For the flat and non-nested arms I apply only min_size 3 and the 3,125
cap**, because there is no complement structure to exclude -- a Leiden community of 5,000 is a
community, not the top of a tree. This is a reading of "candidates = every community of >= 3
members" as written, and it is recorded here so it cannot later look like a choice made to help an
arm. The cap applies to every arm identically.

### CLARIFICATION 3, recorded before building: what the adapter had to change, which is less than expected

"The cluster" in matching is **already** the run's candidate with the highest overlap with the
grouping's shared members, ties toward the smaller: that rule is `_score_matrix`'s, written for the
two-sided change on 2 Oct, and it never walks a tree. `Run.chain_idx` is an inverted index from
pathway to the candidates containing it, which the Ward path happens to build by climbing `parent`;
`Run.parent` and `Run.leaf_cluster` are written but never read by matching. So supporting a flat
partition needs **one new constructor** that builds the inverted index directly, and no change to
matching, completion, consensus or the gate. The regression in §1.2 is therefore a real test of
that claim and not a formality.

### NOTE ON CLARIFICATION 2, added before building and making it moot

The half-draw rule caps a Ward node at `take // 2 = 4,308`, and the declared size cap is **3,125**,
which is smaller. So the cap binds first for every arm and the half-draw rule removes nothing the
cap does not. **Every arm is therefore governed by exactly the same two limits, min_size 3 and
3,125**, and CLARIFICATION 2 describes a difference that does not exist. It is left standing rather
than deleted, because it was written before I checked, and the check is the useful part.

### AMENDMENT, 6 Oct 2026 — made BEFORE ANY BUILD, when no result existed

**Timing, stated plainly because it is what makes this an amendment and not a revision:** at the
moment this arrived, nothing had been built. The adapter existed, the §1.2 regression had passed,
and five engines had been *probed* for per-run cost and candidate count -- no side cut, no floor
solved, no ontology written, no score computed for any arm. **No result of any kind influenced any
clause below, because no result existed.** Copied from Aviyah's message of 6 Oct.

1. **DROP arm E (HDBSCAN).** UMAP fitted on all pathways leaks across resamples and would inflate
   G2.

2. **MODIFY arm B (THEMA-L):** each run uses a LADDER of 10 resolutions, log-spaced over
   0.001-100, **the same ladder for every run**. Candidates = every community of >= 3 members from
   all 10 splits. A grouping is "found in run s" if any community from any of s's 10 splits matches
   it (same theta 0.70 rule). **Arm C (pooled) uses the same ladder.** Reason: with one resolution
   per run, a mid-size group can be found in only ~15% of runs.

3. **ADD arm G, bisecting spherical k-means:** per run, on the unit-normalised centred vectors,
   recursively split every cluster of >= 6 members into 2 with spherical k-means (k-means++ init,
   seed = run index), down to clusters under 6; candidates = every cluster of >= 3 members.
   **ADD arm H, hierarchical Infomap:** ``infomap`` package, multilevel, on the same kNN-15 cosine
   graph, seed = run index; candidates = every module of >= 3 members at every level.

4. **NEW priority order: B, C, G, F, H, D.** Same 12 h budget; drop from the end.

5. **ADD gate G4, biological coherence (declared now):**
   - Data: STRING human v12, combined score >= 700, mapped to the pathway gene symbols.
   - For each final theme: PPI edge density within its gene union vs 100 size-matched random gene
     sets drawn from STRING-covered genes (seed 0); empirical p.
   - Arm statistic: the fraction of themes with p < 0.01, reported per size band.
   - Gate: an arm's fraction must be no more than 5 points below THEMA-Ward's.
   - If STRING can't be obtained on this machine, report "G4 not run" and decide on G1-G3.

6. **LABELLED DIAGNOSTIC, not decisive:** for arm A, count the 51-500 candidates that would pass
   the support gate at theta 0.60 and 0.50.

7. **STOP RULE: one shot.** Whatever the rule selects is the candidate, with no further engine
   rounds. If no arm passes the gates and beats THEMA-Ward under the dominance rule, THEMA v0.3
   stays, and the middle level is handled by offering HiDeF alongside it in the demo toggle.

#### What the amendment changes about the measurement, recorded now

**Clause 2 is the substantive one and it was right.** The first probe of arm B as originally
declared had already shown the failure the clause predicts, before the amendment arrived: one
resolution per run gives a run 62 candidates on average against Ward's 5,274, and a run drawn at
the bottom of the ladder gives **zero** -- resolution 0.0014 produced a single community above the
3,125 cap, so that run proposes nothing at all while still counting in every grouping's eligibility
denominator. Roughly 40% of a log-spaced 0.001-100 ladder sits below 0.1, so arm B as first
declared would have driven support down by construction and failed its floors for a reason that has
nothing to do with Leiden's quality. **Ten resolutions per run fixes that by giving every run the
whole ladder.** The probe is reported in the status file as the evidence, and it is not a result for
any arm: it is a count of candidates, with no side cut and no score computed.

**Clause 1 removes the only arm whose stability was not comparable**, which is the same objection
the original declaration had already recorded as arm E's stated limitation. The `umap-learn` and
`hdbscan` packages were installed before the amendment arrived and are now unused by any declared
arm; they are left installed rather than removed, and `engines.py` keeps the two functions with the
arm marked DROPPED, so the dropped arm stays legible instead of vanishing.

**Clause 7 is a constraint on me, and I record what it forbids:** no second round, no re-tuned
resolution ladder, no "arm B would pass if", no engine added after seeing a score. One shot.

### AMENDMENT 2, 6 Oct 2026 — also BEFORE ANY BUILD

Same timing statement as amendment 1, and it still holds: no side had been cut, no floor solved, no
ontology written, no score computed for any arm when this arrived. Copied from Aviyah's message.

**ADD arm B2 ("persistent THEMA-L"):** identical to arm B (same ladder, same Leiden runs, reused),
but within each run keep only communities that persist across at least 2 adjacent rungs of that
run's ladder (best match Jaccard >= 0.75 on the run's own sample, HiDeF's tau). The surviving
communities are B2's candidates for that run; everything downstream is identical, with its own
calibration. **Priority: right after B.**

**Resulting priority order: B, B2, C, G, F, H, D.** Same 12 h budget; drop from the end.

#### What B2 tests, recorded now

B2 is the one arm that borrows a mechanism from the method it is being compared against. HiDeF's
persistence filter is how HiDeF decides which resolution-sweep communities are real, and arm B as
amended hands recurrence the entire sweep instead. **B2 asks whether persistence-within-a-run and
recurrence-across-runs are doing the same job twice.** If B2 and B score alike, the within-run
filter is redundant given recurrence; if B2 is better, recurrence alone is admitting sweep artefacts
that persistence would have caught. Either answer is worth having, and neither is assumed.

The threshold is 0.75 because that is HiDeF's tau, not because anything here was tuned to it. The
Jaccard is on the run's OWN sample, which is the only set both rungs saw.

### AMENDED BEFORE ANY ENGINE BUILD, 5 Oct

Aviyah's consolidated amendment list, received as a single message after the two above and
**matching them clause for clause** on items 1-8: drop arm E, give arm B a 10-rung ladder per run,
add arm B2 (persistent), add arms G and H, reorder to B, B2, C, G, F, H, D, add gate G4, add the
arm A theta diagnostic, and the one-shot stop rule. Those were already folded in under the two
headings above and are not restated. **Item 9 is new and is recorded here in full.** The heading is
Aviyah's own wording; the date in it is the brief's, and the amendments arrived on 6 Oct by this
machine's clock. Still before any engine build: at the time of writing, one side of one arm was
being cut and no arm had a floor, an ontology or a score.

9. **INTERPRETATION GUIDE (reporting only, not decisive), added before any engine build.** In the
   report, read the results per size band as these contrasts: **A vs B** (engine), **B vs B2**
   (within-run persistence), **HiDeF vs B2** (resampling + calibration). Then state which case
   holds:
   - **(a)** B2 improves 51-500 while keeping A's advantage at <= 50 -> likely candidate;
   - **(b)** B2 loses fine-grained themes vs B -> cross-resolution persistence is too restrictive;
   - **(c)** B ~= B2 -> resampling already does the stability filtering;
   - **(d)** HiDeF still beats B2 at 51-500 -> something structural in HiDeF beyond persistence;
     name the likely cause.

**Item 9 is a reading guide, not a decision rule, and the distinction matters enough to state:** the
candidate is still whatever §0's gates, dominance and max-min select. Case (a) says "likely
candidate" and that phrase does not promote an arm past the gates. If the declared rule and the
guide's cases point different ways, the rule wins and the divergence is reported.

### AMENDMENT 3, 6 Oct 2026 — before any engine build, and it CHANGED THE SETUP

Granularity coverage is a core requirement: fine (3-50) and middle (51-500) themes matter most, the
broad top least. Copied from Aviyah's message.

1. **Before building B/B2/C, verify on the real 10,770 that the ladder spans the full range:** at the
   top rung the median Leiden community size must be <= 5, and at the bottom rung the largest
   community must be >= 3,125. If either fails, widen the ladder's range (keep 10 log-spaced rungs)
   until both hold, and record the final range here as a setup check made before any results.
2. In the report, show per-arm theme counts and the 16 scores with the 3-10, 11-50, 51-200 and
   201-500 bands side by side, and state explicitly for each arm whether it keeps A's fine-level
   (3-50) performance within the margin.
3. Note in the report which arms are deterministic (A, F, D) and which are seeded (B, B2, C, G, H);
   seeds are recorded per run.

#### THE SETUP CHECK, RUN AND FAILED, AND THE RANGE IT CHANGED

**Arm B's build was stopped to run this.** Three sides had been cut (the real side and calibration
scrambles 3001 and 3002); they are cut at the OLD range and are now invalid, and they are being
re-cut. Every process was confirmed terminated by PID before the check ran. **No arm had a floor, an
ontology or a score at any point**, so this is still a setup decision and not a response to a result.

**The declared range [0.001, 100] FAILS the top condition.** Measured on runs 1 and 2 of the real
10,770, at resolution 100 the median community is **12 members**, against the required <= 5. The
bottom condition passes with room to spare: at 0.001 the largest community is all 8,616 drawn
points.

The widening, measured rather than guessed -- each resolution run as a single rung on runs 1 and 2:

| resolution | communities | median | largest | verdict |
|---|---|---|---|---|
| 100 | 682 / 695 | 12 / 12 | 37 / 33 | fails, median too large |
| **300** | **2,302 / 2,287** | **3 / 3** | **17 / 17** | **passes** |
| 1,000 | 7,690 / 7,704 | 1 / 1 | 5 / 5 | passes, but almost every community is a singleton |
| 3,000 | 8,616 / 8,616 | 1 / 1 | 1 / 1 | passes vacuously: total fragmentation |

**FINAL RANGE: 10 rungs log-spaced over [0.001, 300].** Verified PASS on both conditions: median 3
at the top rung, largest 8,616 at the bottom. 300 is chosen as the **smallest** widening that
satisfies the requirement. Going further is worse, not better: at 1,000 the median community is a
single pathway and at 3,000 every community is, so the extra range would be spent on partitions that
propose nothing a size floor of 3 can use. Recording that explicitly because "widen until it holds"
has an upper end where the condition passes vacuously, and stopping at the first range that holds is
the choice that does not smuggle in a tuning decision.

**One honest cost of the widened range, visible in the table above.** Four of the ten rungs
(0.001 through 0.067) give a single community of all 8,616 points, which the 3,125 cap removes --
so those rungs contribute nothing and the arm effectively runs on six. Widening the range made that
worse, not better, because ten rungs now cover five and a half decades instead of five. The
alternative -- moving the bottom up to about 0.1 so all ten rungs do work -- would be a *narrowing*,
which amendment 3 does not authorise, and it would break the bottom condition the amendment sets.
**So the ladder satisfies the declared check and simultaneously wastes 40% of its rungs, and both
things are true and recorded.** It is not re-tuned.

### AMENDMENT 3, SECOND MESSAGE — arm H restored on the budget, 6 Oct, before any result

Aviyah's budget decision, taken on the measured cost table and **before any arm had a score**:

1. **ADD arm H (Infomap) back:** budget B, B2, C, G, H = ~10.7 h, within the 12 h cap. Run it after
   G. This is Aviyah's decision on the budget table, made before any results.
2. Granularity coverage, the ladder span check, and "if B has started, check before continuing".
3. Report all four bands side by side, per-arm theme counts, and whether each arm keeps A's
   fine-level (3-50) performance within the margin.
4. Note which arms are deterministic (A) and which are seeded (B, B2, C, G, H); seeds recorded per
   run.

**Items 2-4 were already in force** under the amendment above and had already been acted on: arm B
was stopped mid-build, every process confirmed dead by PID, the span check run on the real 10,770,
the declared range found to FAIL, the range widened to [0.001, 300] and recorded, and B restarted on
it. Nothing about that sequence changes.

**Item 1 changes the build set, and it is Aviyah's call to make, not mine.** My budget reading
dropped F, H and D because "drop from the end" makes a kept set a prefix of the priority order, and
H sits behind F. I reported that H costs 0.93 h, is the cheapest arm measured, and proposes
candidates concentrated in exactly the mid-size band the search is about -- and then followed the
prefix rule anyway rather than reordering after seeing costs. Aviyah has now authorised the
non-prefix set.

**FINAL BUILD SET: B, B2, C, G, H -- 10.67 h estimated, inside the 12 h cap.**

| arm | engine | estimated |
|---|---|---|
| B | leiden | 2.16 h |
| B2 | leiden_persistent | 2.23 h |
| C | pooled | 2.86 h |
| G | bisect | 2.49 h |
| H | infomap | 0.93 h |
| **total** | | **10.67 h** |

**DROPPED: F (average linkage) and D (Paris).** F costs 7.83 h alone -- 20.44 s per run against
Leiden's 4.64, because `pdist` on 8,616 points is 37M cosine distances and scipy's average linkage
is quadratic on the condensed form -- and adding it would reach 18.5 h. D costs 1.72 h and would
reach 12.39 h, just over the cap; it is dropped as the lower-priority of the two remaining arms.
**Both are dropped on measured cost before any result existed**, and the one thing that would most
cheaply change F's position is `fastcluster`, which the declaration names as an option and which is
not installed. Installing a new clustering dependency to rescue an arm after measuring the arm as
too slow would be a post-hoc change to the setup, so it was not done.

**Determinism, per item 4.** Arm **A is deterministic** given its persisted trees. Arms **B, B2, C,
G and H are seeded**, every seed derived from the run index so a side re-cut later is the same side:
B/B2/C pass the run index as igraph's RNG seed and share one fixed resolution ladder; G seeds
k-means++ as `run_index * 7919 + cluster_index`, so the recursion is reproducible rather than
dependent on the order the queue reached a cluster; H passes the run index as Infomap's seed. Of the
dropped arms, F and D would have been deterministic. Candidate generation also runs across worker
processes, and that cannot change a side: each run reads its own persisted sample, shares nothing
writable, and order is preserved -- asserted byte-identical by test, not argued.

### AMENDMENT 4, 6 Oct 2026 — the ladder's BOTTOM, before any engine result existed

Aviyah's amendment, acting on the waste my own record of amendment 3 had disclosed. Still before any
result: arm B had cut three of sixteen sides and had no floor, no ontology and no score. Those three
sides were cut at the [0.001, 300] range, are invalid under this change, and were moved to
`superseded_range_0.001_300/` -- not deleted -- after every process was confirmed terminated by PID.

**The problem, in Aviyah's words:** the widened ladder wastes 4 of 10 rungs (each gives one community
of the whole draw, removed by the cap), leaving ~4x spacing between useful rungs -- a group whose
scale falls between rungs can fail recurrence for setup reasons, hitting the 51-500 band and B2
hardest.

**The change:** for B, B2 and C, 10 log-spaced rungs from `r_low` to 300, where `r_low` = the largest
resolution at which the largest community is still >= 3,125, read off the existing span check. The
top-rung median <= 5 condition is kept. **Matching rule unchanged: containment in a larger community
does NOT count as recurrence.**

#### r_low, read off the existing span check's own grid

| rung resolution | largest community | reaches 3,125? |
|---|---|---|
| 0.001 | 8,616 | yes |
| 0.0040604 | 8,616 | yes |
| 0.0164869 | 8,616 | yes |
| **0.0669433** | **8,616** | **yes -- the largest such rung** |
| 0.271817 | 1,759 | no |
| 1.10369 | 657 | no |

**r_low = 0.0669433. FINAL RANGE: 10 rungs log-spaced over [0.0669433, 300].** Verified PASS on both
conditions: median 3 at the top rung, 8,616 at the bottom.

**What it bought, measured.** Rung spacing falls from **4.060x to 2.545x**, and the number of rungs
that propose something usable rises from 6 to **9 of 10** -- only the bottom rung is now degenerate,
and it has to be, because the bottom condition is defined as the point where one community still
covers the draw. The new ladder is 0.0669, 0.170, 0.434, 1.10, 2.81, 7.15, 18.2, 46.3, 118, 300.

#### The matching rule, confirmed in code rather than asserted

The amendment restates a rule, so I checked the code implements it instead of taking it on trust.
Two tests now pin it. A 10-member grouping whose only appearance in four other runs is inside a
50-member community gets support **1/5** -- its own run and nothing else -- because the two-sided
Jaccard is 10/50 = 0.2, far below theta. A genuine near copy, 9 of 10 members shared plus one extra
at Jaccard 0.818, gets support **1.0**. Without the two-sided rule a run proposing one huge
community would "find" every grouping it contained, and a coarse engine would score as perfectly
recurrent; that is exactly the failure mode the amendment is guarding, and it is already guarded.

#### The ladder has now been set three times, and that is worth stating plainly

Declared [0.001, 100] -> amendment 3 widened the top to 300 because the median at 100 was 12 against
a required <= 5 -> amendment 4 raised the bottom to 0.0669433 because four rungs proposed nothing.
**Every change was made before any arm had a score, each was driven by a measurement of the setup
rather than of an outcome, and each is recorded here with the number that forced it.** The honest
risk in a sequence like this is that the setup drifts toward whatever will eventually look good;
the protection is that none of the three changes could have been informed by a result, because no
result existed, and the one-shot stop rule means there is no second round in which to use one.

### 6 Oct 2026 — a floors-path bug caught by the no-overwrite convention, and a note on "read once"

**The bug.** `build_10770.py` wrote its solved floors to `cut_key(...)` -- the WARD completions
directory -- rather than `engine_cut_key(..., engine)`. So arm B solved its own floors correctly and
then tried to write them into `cap3125_inc050/floors_r1-200_n200.json`, **which is the frozen
build's calibration record**: the file that already lost `overall_fdr 0.00285` once, on 5 Oct, and
had to be restored from an embedded copy.

**Nothing was lost, because the guard added after that incident refused the write.** The Ward record
still reads `overall_fdr 0.00285` and `3-3 floor 0.79`, verified after the fact. The visible symptom
was different and much milder: arm B's floors were persisted nowhere its own stability half-builds
could find them, so `--floors-from` would have failed on a missing file.

This is the second time in two days that the no-overwrite convention has been the only thing between
a path bug and a destroyed calibration record. It is not a style preference.

Fixed: every `cut_key` call in the driver is now engine-aware, and the manifest records
`floors_file` explicitly so no future reader has to reconstruct the path -- which is itself how
`engine_gates.py` first failed, reconstructing a path from a manifest field (`space`) that holds a
description, `"centred-renormalised"`, where the directory is named for the flag, `centred`.

**The note on "read once", stated because the declaration uses that word.** Fixing this meant
re-running arm B's build, so its held-out confirmation was computed **three times**. All three
produced the identical `overall held-out FDR 0.00189`, because all three read the SAME CACHED
held-out sides and the confirmation is a deterministic function of them -- nothing was re-cut and no
new null was drawn. More importantly, **no choice was made between the three runs**: the floors were
solved once from the ten calibration sides and were not touched, and the only change between runs
was where a file is written. The rule exists to stop a held-out set being consulted, adjusted
against, and consulted again; that did not happen, and recording the three runs is the honest way to
show it did not.

**Arm B's first result, for the record**, since it is now fixed on disk: 3,462 nodes, 88 roots,
**0 unplaced and 0 effectively unplaced** against arm A's 141, held-out FDR 0.00189, worst stratum
0.00969 -- and **strata 3-3 and 4-4 DROPPED**, no floor meeting FDR 0.01 in them, so arm B produces
no theme of three or four members at all. That last fact is a result and is reported, not fixed.

### 6 Oct 2026 — the run stalled at ~19:35Z, and the cause was my own process cleanup

Aviyah reported the Mac sleeping or shutting down around 19:35Z. What the check by PID actually
found: all three job chains alive, the machine up 82 days with no reboot, and the side apparently
being cut having accumulated **1.55 seconds of CPU in 43 minutes at 0.0%** -- wedged, not slow.
Alongside it, **24 worker processes where six were expected, every one with PPID 1**: orphans
reparented to init, 5h27m elapsed on 27s of CPU each.

**The cause is mine.** `ProcessPoolExecutor` children do not die when the parent is signalled. Each
time I stopped a driver by PID -- three times, for amendment 3's span check, amendment 4's ladder
change, and the floors-path fix -- its six spawned workers survived. Each holds a ~1.5 GB similarity
matrix; twenty-four of them on a 36 GB machine exhausted memory, which is what made the Mac sleep
and wedged the running pool. **"One heavy job at a time" was honoured in the foreground and broken
by my own leftovers**, and the rule exists precisely because this machine thrashes.

Two things follow, and the second matters more than the first.

**The fix.** `scripts/stop_engine_jobs.sh` stops drivers and chains, then kills every
`multiprocessing.spawn_main` worker, then proves by PID that nothing remains. Choosing `spawn` over
`fork` -- forced earlier by a macOS BLAS-after-fork crash -- is what makes the workers findable at
all, so one correction enabled the other.

**The lesson about verification.** I had been verifying termination by PID, as instructed, and that
verification was **incomplete rather than wrong**: I checked the PIDs I had started and not the
processes they had started. A check that only looks where it expects to find something is not a
check. The resume therefore verified the 26 cached sides against the current provenance fingerprint
rather than trusting their file names -- 18 valid for arm B, 8 for B2 -- and nothing finished was
redone.

Resumed 20:19:36Z. Nothing declared changed; arm B skipped as complete, B2 continued at seed 3008.

## 2026-10-06 — Evaluation protocol A vs B vs HiDeF, declared 6 Oct 2026

**The protocol is `docs/spec/eval-protocol-2026-10.md`, pasted there verbatim from Aviyah's brief and
not edited.** This entry exists so the declaration has a dated place in the decision record, and so
that the two sections which fix what was known and what will decide are quoted here and cannot be
reconstructed later from memory.

**The engine run stays PAUSED.** Arms C, G and H are untouched: 5 of 18 sides cut for C, none for G
or H, and nothing resumes until this protocol reaches a decision. **This protocol does not amend the
engine rule** (`2026-10-06 — Engine search: §0 declared before anything was built`, with amendments
1-4 and the interpretation guide); that rule still governs C, G and H when they resume, and any
winner among them is re-checked against this protocol afterwards.

**Nothing in test F or E1-E4 has been implemented or computed.** This entry is written before any of
it exists.

**The eight ambiguities I raised are answered in the protocol itself**, as
`## Clarifications 1-8 (declared 6 Oct 2026, before any result of this protocol)` at the end of
`docs/spec/eval-protocol-2026-10.md` -- Aviyah's text, appended verbatim, still before any result,
and it also records that co-expression is not run because ARCHS4 is 7.49 GB against the declared
5 GB limit.

### "Status of knowledge at declaration", quoted verbatim

> **Status of knowledge at declaration.** These results already exist and were seen: Preview 1 and 2
> of the engine run (sibling AUROC for A, B, HiDeF), shape, stability and gates for A, B, B2, and the
> floors in each build's manifest. NOTHING below (test F, E1–E4) has been computed for any arm. Arms
> C, G, H stay paused and untouched. They resume afterwards under the engine rule exactly as
> declared. This protocol does not amend that rule.

### "Final decision rule", quoted verbatim

> ## Final decision rule (A, B, HiDeF)
>
> **Decisive recall cells:**
> - E1 source-only (2 sources × 4 bands);
> - E1 full-restricted (2 × 4);
> - E2 at σ\* (4 bands).
>
> **Rule:**
> 1. A THEMA arm X **beats HiDeF** if all of these hold:
>    - X is better than HiDeF-tuned by > 0.02, with the CI excluding 0, in at least one fine-band
>      cell AND at least one middle-band cell;
>    - X is not worse by > 0.02 (CI excluding 0) in any decisive recall cell;
>    - X is not worse by > 0.02 (CI excluding 0) in E1 source-only precision.
> 2. If both A and B beat HiDeF, the max-min shortfall over the decisive cells chooses. Ties within
>    0.01 go to fewer knobs, then to the faster core build.
> 3. **If neither beats HiDeF**, HiDeF becomes THEMA's engine. THEMA's contribution is then the
>    descriptions, embeddings, naming and statistics layer, plus the Test-F certificate where it
>    applies.
> 4. Nothing is frozen. Aviyah decides. Then arms C, G and H resume under the engine rule, and any
>    winner among them is re-checked against this protocol.

### What is new about this protocol, recorded at declaration

Three things it does that no THEMA evaluation has done before, stated now so they are not later
read as conveniences:

1. **It can conclude against THEMA's engine.** Clause 3 says in terms that if neither A nor B beats
   HiDeF, HiDeF becomes the engine and THEMA's contribution is the layers around it. No prior rule
   in this file had an outcome that replaced the method's core.
2. **It gives HiDeF a tuning budget THEMA never gets** -- a 27-setting grid per universe, selected on
   a held-back tuning half -- and then an **oracle line** on top, HiDeF's best setting per cell
   chosen on the test half. A and B are each one fixed configuration.
3. **It adds planted ground truth**, where recall is measured against sets that are true by
   construction rather than against a curator's hierarchy, and it **declares the limitation in
   advance**: Gaussian geometry may favour Ward, which is why E2 is one of two decisive tests and
   never the only one.

The existing specificity AUROC -- every number reported on 4, 5 and 6 Oct -- is demoted to "also
reported" here. **Recall against curated and planted sets is what decides**, and that is a different
question from the one the AUROC answers.

### Test F, and why it runs first

Test F asks whether the scramble calibration earns its cost, and it can only be asked honestly
before anything else is built, because its answer sets the floor form every later build in the
protocol uses. The manifests already show the floors bind only on small themes, which is what makes
the question live rather than rhetorical. **Its step 2 is a declared second read of the held-out
seeds 4001-4005**, and the protocol labels it as such: no threshold is fitted at the fixed cut, so
every seed is valid test data for it, and the cut is declared here rather than chosen after seeing
the FDR.

## 2026-10-06 22:25:43Z — THEMA v0.4 declared: §0-§2 verbatim, before any build

Copied verbatim from Aviyah's brief of 7 Oct 2026. **Nothing below was computed when this was
written.** Branch `v04-2026-10`; v0.3 stays frozen.

### THE IDEA, as given

> a theme is a group of pathways that stays together across 80% subsamples more often than chance
> allows; themes are stacked by containment. Three knobs: sample fraction 0.8; one match threshold
> θ = 0.70 for both recurrence and merging; the 3-seed floors at the v0.3 target FDR, calibrated
> once and stored.

### §0 DECLARE, verbatim

> §0 DECLARE: copy §0–§2 verbatim into DECISIONS.md, timestamped, before any build.
>
> Scoring: the KC2 deciding-table code with clarification 9, plus clarification 10.
> Cells: Reactome and GO × bands 3–10, 11–50, 51–200; recall and precision.
> Split the curated sets in half (seed 0, stratified by band). All ablation decisions use the
> TUNING half only; the TEST half is used only in §3.
> Margin: 2 points, with a cluster bootstrap CI over curated sets (1,000 resamples, seed 0) that
> must exclude 0.
> Rule: a v0.3 stage is KEPT only if removing it worsens a cell beyond the margin, OR pushes
> held-out FDR (scrambles 4001–4002) over the v0.3 caps, OR drops stability between run halves by
> more than 2 points. Otherwise it is REMOVED.
> Report theme count for every arm. A recall gain that comes with a large rise in theme count is
> flagged, not credited.

### §1 ABLATION, verbatim

> §1 ABLATION, from v0.3 on the 10,770 (cached trees, stored floors). Switch off ONE stage at a
> time:
>
> - size cap;
> - TOL extras-only rule → symmetric Jaccard θ;
> - STRAY;
> - completion;
> - greedy seed absorption → a simple merge at θ;
> - per-size floors → a single floor;
> - strict containment → partial containment ≥ 0.9 (report-only).
>
> Recalibrate the floors only where the gate's input changes, and say so. Table: stage → effect per
> cell, with CI → KEPT or REMOVED, plus wall time.

### §2 BUILD, verbatim

> §2 BUILD a new module, src/thema/ontology/v04.py, with only the KEPT stages; under 500 lines,
> with a one-line justification per stage.
>
> Test: with every stage on, it reproduces v0.3 byte-identically, or explain each difference.
> Calibrate once, store the floors, run one held-out scramble check.
> Output data/ontology/v0.4/thema_10770/ in the v0.3 schema.

### Three readings recorded before building, because each could otherwise look convenient later

**1. The ablations and the BASELINE both use three-seed floors.** §1 says "cached trees, stored
floors", and v0.3's stored floors are ten-seed; the IDEA fixes three-seed floors as one of v0.4's
knobs. Comparing a ten-seed v0.3 against three-seed ablations would confound the floor count with
the stage being removed, so the baseline is rebuilt at three seeds too. Test F measured that three
seeds pass the v0.3 caps (held-out FDR 0.00252 against the ten-seed 0.00285), and it is also what
makes this brief fit its own 6 h limit: at ten seeds the estimate is 7.24 h and the instruction is to
stop.

**2. "TOL extras-only rule → symmetric Jaccard θ" is a NO-OP and is reported, not measured.** The
frozen build already runs the symmetric θ branch; `TOL = 0.15` is used only in the
`theta is None` branch and is inert. That was established on 5 Oct in answer to Part A question 1
and is recorded in this file. Switching it therefore changes nothing, and the ablation table says so
rather than reporting a spurious zero effect as evidence the stage is removable.

**3. Clarification 9 changes every GO number ever reported here.** `parse_obo_terms` reads only
`is_a`, so the 4 Oct HiDeF comparison, the 5 Oct 16 scores, the KC2 deciding table and both HiDeF
grids all used the `is_a`-only closure, which clarification 9 demotes to secondary. The primary
closure has never been computed. v0.4's §3 is therefore **not comparable cell-for-cell with any
earlier GO figure**, and both closures are reported so the discontinuity is visible rather than
silent.

## 2026-10-08 09:02:35Z — v0.4 VERDICT: four of seven stages removed, three kept

The ablation declared on 6 Oct ran on the 10,770 with cached trees and stored floors. Decisions used
the **tuning** half of the curated sets only; the test half was read once afterwards, for §3.
Baseline (all stages on): held-out FDR 0.00241, between-half stability 0.855, 6,229 themes.

| stage removed | themes | held-out FDR | worst stratum | stability | verdict |
|---|---:|---:|---:|---:|---|
| size cap (29.0133% = 3,125) | 6,141 | 0.00237 | 0.0114 | 0.853 | **REMOVED** |
| TOL extras-only rule | — | — | — | — | **ALREADY ABSENT** |
| STRAY (0.10) | 6,192 | 0.00241 | 0.0107 | 0.854 | **REMOVED** |
| completion | 12,045 | 0.00196 | 0.0172 | 0.713 | **KEPT** |
| greedy seed absorption to flat merge at theta | 7,519 | 0.00482 | 0.0130 | 0.854 | **KEPT** |
| per-size floors to one floor | 1,974 | **0.01013** | **0.0500** | 0.793 | **KEPT** |
| strict to partial containment >=0.9 | 6,229 | 0.00241 | 0.0107 | 0.855 | **REMOVED** |

Each KEEP was forced by the declared rule, not by preference. **Completion**: stability falls to
0.713 and two curated cells worsen beyond the 2-point margin with paired CIs excluding zero; its
better FDR arrives with 1.9x the theme count, which the rule flags rather than credits.
**Greedy absorption**: held-out FDR doubles and two cells worsen. **Per-size floors**: four
independent failures at once -- FDR 0.01013 over the 0.01 cap, worst stratum 0.0500 over the 0.02
cap, stability 0.793, four cells worse -- and a single floor also cuts the ontology to 1,974 themes.
This closes Test F and Test R from the other direction: the floors are load-bearing, not merely
affordable.

Every REMOVAL is a case where nothing moved. The size cap, the stage with a whole reference
apparatus behind it, shifts FDR by 0.00004 and stability by 0.002 and worsens no cell, consistent
with the earlier finding that it removes about two candidates per tree. TOL was already inert: it is
read only on the `theta is None` branch, which no build takes.

**v0.4 is therefore v0.3 minus four stages.** `src/thema/ontology/v04.py` is the pipeline with the
removed stages absent rather than switchable. It is proved byte-identical to the frozen
`recurrent_dag_10770` with every stage restored, at two levels -- the side material first (161,852
candidates, membership identical), then all four exported tables. Calibrated once: held-out FDR
**0.00237** on scrambles 4001-4002. Built to `data/ontology/v0.4/thema_10770/`, 6,104 themes.

Two bugs the byte-identity test caught, both of which would have invalidated every §3 number: the
size cap came out 3,124 rather than 3,125 from a truncated share and `int` where v0.3 takes `round`;
and the inclusion column was written as 1.0 for every member, which showed up as every node, edge
and unplaced row identical with 40,501 of 98,599 member rows differing. The same inclusion flaw was
in all seven §1 ablation builds and **does not affect any §1 decision**, because recall, precision,
FDR and stability all read member sets and never that column.

**On the test half, read once: no cell differs from v0.3 beyond the margin in either direction, on
either GO closure.** Stability 0.852 against 0.855. The DAG is 100% gene-monotone on all 8,422
edges. **v0.4 becomes the current core**; v0.3 and `recurrent_dag_10770` stay frozen as the
reference. Full report: `docs/status/2026-10-07-v04.md`.

## 2026-10-08 09:02:35Z — the direction pilot FAILED its pre-declared bar

The pilot asked whether an LLM can tell, from a blinded description alone, which of two pathways is
the broader one. Setup: names and database identifiers hidden, fresh agents writing one "broader"
phrase and up to five "narrower" ones, scored by MedCPT query encoder against the article
embeddings. The bar was declared at **70%** before the run.

**Result: 62.5%** (Reactome 64.0%, GO 61.0%). Below the bar. The pilot does not pass and its
approach is not carried forward on this evidence.

Two findings make the failure worse than the headline. **Leakage: 63% of the GO "broader" phrases
are verbatim the name of a true curated GO ancestor**, although the name was hidden from the model --
so the model is reciting GO vocabulary it memorised rather than reasoning from the description.
Separately, 3.2% of Reactome and 11.2% of GO child descriptions already contain their parent's exact
name, a pre-existing leak in the descriptions themselves.

For contrast, free signals on the same pairs: local embedding density 61%, rank asymmetry 61%, hub
count 58-63%, distance from the corpus centre 44% (inverted). And "the parent has more genes" is
100% on strictly-containing curated pairs, because Reactome unions and GO propagation produce those
sizes -- a leaky baseline for validation, but one that uses only input data. Material at
`data/experiments/direction_pilot/`; the unblinding key is gitignored so the blinding survives a
re-run.

## 2026-10-08 09:02:35Z — pathway NAMES are rejected as a direction signal: double dipping

Name inclusion -- testing whether one pathway's name is a substring of the other's -- scores **99.7%
on GO**, where it applies to 43% of pairs. It is **rejected and will not be used**, in construction
or in scoring.

The reason is that GO names are not independent observations of biology; they are written by the
same curators who built the hierarchy, and they encode its structure deliberately ("regulation of X"
sits under "X" because the curator named it to). Recovering the hierarchy from the names is
recovering the curator's own indexing, so a method using names would score well on the curated
benchmark while learning nothing about the pathways. It is the same circularity as the gene-count
baseline but without the mitigation that gene sets are at least measured data.

This is a standing rule, not a one-off: no scoring or construction path may read pathway names, and
a method that needs them is disqualified rather than discounted. The descriptions are what THEMA
reads, which is why the pre-existing name leak into descriptions (above) is recorded as a defect to
fix rather than an effect to exploit.

## 2026-10-08 09:32:27Z — THE LEAVES EXPERIMENT, declared verbatim before any build

Copied verbatim from `docs/spec/2026-10-08-leaves-experiment.md` (sha256:16 `da8f9a6eacea60a2`), which
Aviyah wrote. **No result below this line existed when it was recorded.** Branch `leaves-2026-10`,
created from main after v0.4 was merged and tagged `v0.4`; v0.3 and v0.4 are untouched.

One thing was run before this entry and is declared here as having been: **universe L itself**, by
`scripts/leaves_universe.py`, because the spec's own last line requires a time estimate first and
the estimate depends on L's size. It computes no experimental result -- only the universe the
experiment runs on, which the spec's step 1 asks to be reported. L has **5,559** pathways
(GO 3,168, Reactome 1,995, Hallmark 50, BTM 346). The spec expected about 5,599; the 40-pathway
difference is in Reactome, whose universe here is 2,836 against the spec's 2,883, and the GO counts
match the spec exactly (4,370 internal of 7,538). The difference is in the universe count, not in
the summary rule.

Test N is **not run**: it costs API spend, and the instruction for this session is no API spend. It
is priced and stopped, as the spec itself requires.

---

> # The leaves experiment: declared 8 Oct 2026, before any result
>
> *Spec for ccode. Exploratory arm. Everything is declared here before any number exists. Any later change is labelled as post hoc.*
>
> ## Why
>
> Curated parents are summaries by construction. A Reactome parent's genes contain every child's (100% of edges), and GO propagates annotations upward. 58% of the GO pathways in the universe (4,370 of 7,538) and 29% of Reactome (848 of 2,883) are such internal nodes. They are large (median 43–51 genes; leaves have a median of 9–10).
>
> Today they are clustered alongside their own children as if they were independent items. The consequences (`docs/spec/2026-10-08-reviewer-monotonicity-notes.md`):
> - general pathways cluster with their general synonyms instead of sitting above their specifics;
> - the same genes appear all over the DAG;
> - there is no middle-level theme for groups like "RTK signalling".
>
> Text-only direction signals have been tried and are weak (about 60%) or contaminated (the LLM pilot: 62.5%, with 63% verbatim GO ancestors).
>
> ## What we are trying to achieve
>
> Build THEMA from the **atomic** pathways only (the leaves), then test whether its themes **recreate the curated summaries** by merging leaves. If they do, THEMA's claim becomes: *"From the atomic pathways of four databases, text alone merges cross-database duplicates and recovers the curated summary structure."* Curated parents are then placed on the theme that recreates them, which gives users general-above-specific without using text direction.
>
> **Leakage statement.** The curated hierarchy is used ONLY to mark which pathways are summaries (internal nodes). It is never used to decide how leaves group. The placement layer (step 6) is display only and is never scored.
>
> ## Design
>
> 1. **Universe L.**
>    - Remove every Reactome pathway with ≥ 1 descendant in the universe (ReactomePathwaysRelation).
>    - Remove every GO term with ≥ 1 descendant in the universe (closure over `is_a`, `part_of`, `regulates`, `positively_regulates`, `negatively_regulates`, as in clarification 9).
>    - Keep all Hallmark and BTM pathways.
>    - Expected size: about 5,599. Report the counts per source.
>    - Sensitivity, counts only: GO internal defined by `is_a` + `part_of` only.
> 2. **Vectors.** The existing MedCPT vectors for L, **re-centred on L** and renormalised, as the protocol does for subsets.
> 3. **Build.**
>    - v0.4 as finalised: kept stages only, 200 runs, 80% subsamples.
>    - Floors: reuse the stored 3-seed floors and check them on ONE held-out scramble of L (seed 4001). If held-out FDR > 0.01 overall or > 0.02 in any stratum, recalibrate on L (seeds 3001–3003) and say so.
>    - Stability between run halves.
>    - Output: `data/ontology/v0.4-leaves/thema_L/`.
> 4. **Baselines on the same L.**
>    - (a) **Full-universe v0.4 restricted to its L members**: keep themes of ≥ 3 after restriction, deduplicated. This answers "does building on leaves beat simply hiding the parents?"
>    - (b) **HiDeF on L**, re-tuned on the TUNING half over k ∈ {3, 4, 5} × maxres ∈ {300, 500, 800}.
> 5. **Answer key.**
>    - For every internal node P (Reactome; GO with full links as primary, `is_a`-only as secondary), the target set is P's leaf descendants in L, kept if ≥ 3.
>    - Split targets in half, seed 0, stratified by band (3–10, 11–50, 51–200, 201–500 leaves).
>    - Any choice uses the TUNING half; the report uses the TEST half.
> 6. **Placement layer (display only, report-only).** Attach each internal pathway to the theme with the highest Jaccard to its leaf set. Report the distribution of that best Jaccard per band.
>
> ## Tests (all on the TEST half; CIs from a cluster bootstrap over targets, 1,000 resamples, seed 0)
>
> - **Primary:** recall and precision of targets per band, per source, at Jaccard > 0.5 (the existing deciding-table code), for L, (a), and (b).
> - Near-pair agreement among leaves (clarification 10).
> - Matched theme count: L cut by support to HiDeF's count.
> - Shape: themes per band, unplaced, multi-parent %, held-out FDR, stability, build time.
> - **Named case:** Reactome "Signaling by Receptor Tyrosine Kinases" (R-HSA-9006934). Report its leaf-set size, the best theme Jaccard in each build, and whether "Signaling by SCF-KIT"'s leaves sit inside that theme.
> - **Scatter:** for each internal pathway, the number of distinct root themes its leaves fall under, for L vs (a).
>
> ## Additional declared tests (added 8 Oct, before any result): can THEMA's TEXT place and name the held-out summaries?
>
> These test the thematic approach directly. The curated hierarchy is used only as the judge. Both tests are REPORTED, not decisive. They run on internal pathways in the TEST half only.
>
> ### Test T: text placement (no API cost)
>
> - Each internal pathway P was never in the build. Represent it by its own MedCPT description vector, centred with L's mean and renormalised.
> - Represent each theme of the leaves build by the centroid of its members' vectors, centred on L and renormalised.
> - **T1 (primary).** Place P on the theme with the highest cosine to P, among all themes of ≥ 3 members, with no size information. Score: Jaccard(P's leaf set, the placed theme's members). Report the median and the share > 0.5, per band and source.
>   - Ceiling: gene placement (the theme whose gene union has the highest Jaccard with P's genes).
>   - Floor: a random theme of the same size as the text-placed one (100 draws, seed 0).
>   - Baseline: the same text procedure on HiDeF-on-L and on baseline (a).
> - **T2.** For P whose leaves ARE recovered (some theme has Jaccard > 0.5 with P's leaf set): top-1 and top-5 accuracy of the text ranking in hitting that theme.
>
> ### Test N: naming from leaves (API cost; PRICED FIRST, Aviyah approves before any call)
>
> - For recovered P, run the current namer on the matching theme. The namer sees leaf members only; P was never in the build.
> - Score: semantic similarity of the generated name to P's held-out name, as a percentile against all GO BP and Reactome pathway names, using the encoders in the existing naming evaluation. Report the share at ≥ 90th and ≥ 98th percentile.
> - **Leakage control (required).** Child names often contain the parent's name (for example "regulation of X" under X). Report separately the themes where NO member name contains P's name as a substring.
> - **Abstention control.** Size-matched random leaf sets; report the abstention rate.
> - Before any call, write the price (dry run) to the status file and STOP for approval.
>
> ## Decision rule (declared now)
>
> The leaves version is preferred if, on the TEST half, it:
> - is **not worse than (a) by more than 2 points** (CI excluding 0) in any 3–10 or 11–50 recall cell; and
> - is **better than (a) by more than 2 points** (CI excluding 0) in at least one 11–50 or 51–200 recall cell; and
> - keeps held-out FDR within the caps.
>
> Otherwise the full-universe v0.4 stays. Nothing is frozen; Aviyah decides.
>
> ## Preservation
>
> - Branch `leaves-2026-10`, created from main after v0.4 is merged and tagged `v0.4`.
> - New files only. The universe filter is a new function or option whose default leaves v0.4's output byte-identical; re-run the byte-identity test.
> - Outputs go to `data/ontology/v0.4-leaves/` and `data/experiments/leaves/`.
> - `v0.3/` and `v0.4/` are untouched.
> - Status: `docs/status/2026-10-08-leaves.md`.
> - Estimate the time first; stop if it is over 3 h.

## 2026-10-08 16:24:41Z — WORKING RULES: the reviewer analyses, ccode writes and runs all code

Relayed by Aviyah and recorded by ccode. Two rules, from now on:

1. **The reviewer only analyses and writes prompts. ccode writes and runs all code.** No parallel
   reviewer scripts.
2. **Everything Aviyah and the reviewer try outside ccode is relayed to ccode to record**, in the
   form the 8 Oct relay took.

The reason is in `docs/status/2026-10-08-reviewer-log.md`: it holds about a dozen results that
nobody can now reproduce, because the scripts lived in `/tmp` on a VM and are gone. One of them -- the
claim that Ward's size weighting lets large diffuse clusters swallow small groups -- had already
shaped a declared experiment (the one-linkage brief) before it was withdrawn. An unreproducible
number that changes a declared experiment costs more than the experiment.

Everything in that log is labelled EXPLORATORY: not declared in advance, not run by ccode, not
reproduced. Any number there that would change a decision must be re-run under the protocol first.

## 2026-10-08 16:24:41Z — EVALUATION: independent coherence is primary, curated agreement is secondary

EXPLORATORY evidence, from the reviewer's 8 Oct work, not reproduced by ccode.

Reactome and GO group pathways on **different axes**, and neither is the only valid one. Reactome
groups by protagonist molecule (a receptor or transcription factor) or by mechanism stage; GO groups
by logical class -- regulation direction x target class, or an abstract form. Text plus Ward regroups
the ERBB family by step type rather than by receptor, which disagrees with Reactome while describing
the same biology.

Mean within-group gene Jaccard, curated against text and LLM groupings:

| | curated | text Ward | LLM | random |
|---|---|---|---|---|
| Reactome | 0.140 | 0.149 | 0.155 | 0.051 |
| GO | 0.028 | 0.032 | 0.041 | 0.009 |

**The text and LLM groups are at least as gene-coherent as the curated groups they disagree with.**
So disagreement with curation is not evidence of error, and a benchmark built only on curated
agreement penalises a valid alternative axis exactly as hard as a wrong answer.

**DECISION: independent coherence -- gene coherence against a size-matched null, and an intruder test
-- becomes the PRIMARY evaluation. Curated recall and precision become SECONDARY.**

This reverses the weighting every evaluation in this repo has used to date, including the v0.4
ablation, the leaves experiment and both threshold grids. Those verdicts are not retracted: each was
decided under the rule in force when it was declared, and each reported its coherence numbers too.
But a future arm is no longer disqualified by curated recall alone, and the intruder test does not
exist yet -- it has to be built before this decision has teeth.

## 2026-10-08 16:24:41Z — ONE-LINKAGE: step 2 for engine C is NOT approved; UPGMA recorded as a candidate

The reviewer's reading of ccode's step 1 report (`docs/status/2026-10-08-one-linkage.md`), with one
withdrawal that matters more than the verdict.

**Engine C is not approved for step 2.** Its 6.4x advantage in nodes of 51-1000 members (1,085
against Ward's 169) is **mostly chaining, not extra levels**: nested near-copies, one node with 72
children after collapsing chain links, and 19 singletons in the cut at 30. ccode's step 1 report
flagged all three symptoms; the reviewer's reading is that they are the whole effect.

**The declared step 1 criterion counted raw tree nodes, which rewards chaining. Recorded as a flaw of
the criterion**, not of the measurement: a criterion that counts nodes cannot distinguish a new level
from a longer chain, and both arms that passed it did so partly on chains.

**WITHDRAWN: the explanation that Ward's size weighting makes large diffuse clusters swallow small
groups.** The raw Ward tree is balanced -- at most 4 children after collapsing, sensible cuts at every
level. **The roots with 100-227 children come from the BUILT DAG, not the tree**: intermediate nodes
fail the gate, and their children attach to the root instead. This withdrawal is why the next test is
the gate rather than the merge rule.

**UPGMA (engine A) is recorded as a candidate alternative engine, to revisit later depending on
results.** On step 1 it had well-formed cuts at every level, the best curated recall of the three
(Reactome 3-10 0.364 against Ward's 0.334), took 0.2 s per tree, and needs no new engine code -- it
is one `method="average"` call on cosine distance. **For now Ward stays unchanged.**

`src/thema/ontology/linkage.py` and its tests stay in the repo: `run_from_merges` is proved
field-for-field identical to `recurrent.tree_from_subset` on Ward's own merges, so it is the adapter
any future non-Ward engine needs, and engine C remains callable for a later attempt.

## 2026-10-09 08:38:47Z — REPAIR ROUTE (a), v3: declared before any result

Aviyah's decision, 8-9 Oct 2026. Exploratory. Base: **L_cal8 settings** -- match threshold 0.70,
floors solved to a 0.008 calibration target, **no 0.33 minimum**. **Ward stays.** Build:
`thema_L_repair`. **No rule for big themes is declared**; that is decided after Aviyah sees the
description in item 4.

**1. FIX: stale merges.** After an accepted theme grows (rule 2 / `STRAY_FLOOR`), it must be
re-compared with the accepted themes, so **no identical or non-nested >0.70 pair survives**.
Equivalently, the 0.70 merge is applied once more as the LAST step, on final memberships.

The defect is diagnosed in `docs/status/2026-10-08-twins-diagnosis.md`: consensus compares only the
newcomer against the stack, so two themes already side by side are never compared again after one of
them grows. In `thema_L`, 822 themes grow and all 10 anomalous pairs -- 3 identical, 7 non-nested
above 0.70 -- involve a grown theme. Growth is live even at `stray=0.0` because `STRAY_FLOOR = 1`
bypasses the share test.

**Implemented as a post-pass in a new module, not as an edit to `consensus.py`.** That file is
load-bearing for v0.4's byte-identity proof against the frozen `recurrent_dag_10770`; changing it in
place would break the one guarantee that makes v0.4 comparable to v0.3. The post-pass is iterated to
a fixed point and the build asserts that no such pair remains.

**2. CHAIN COLLAPSE, in construction.** A child holding **>= 90%** of its parent's members is the
same theme: the two are merged into one node. **Keep the parent's membership; keep the higher
support and record both.** Edges are re-linked and strict containment is preserved. Aviyah's
framing: this is a correctness fix, not cosmetic -- a theme and the-same-theme-plus-one are not two
themes.

**90% is the declared rule.** 80% is reported as well, **and the choice between them is not made
from the results.**

**3. FRESH CHECK OF THE cal8 FLOORS.** The 0.008 calibration target was chosen on 8 Oct *after*
seeing a held-out FDR of 0.01009, and was labelled as such. It is therefore confirmed here on
scramble seeds **never used before** -- 4003, 4004 and 4005, whose trees already exist. Overall and
per-stratum FDR are reported. Caps unchanged: 0.01 overall, 0.02 per stratum.

**4. DESCRIBE THE BIG THEMES, no rule yet.** For every theme of 51+ members in the repaired build:
support, **support at Jaccard 0.5**, gene coherence against a size-matched null, number of children,
and the 7 member names nearest the centroid. A table sorted by size, plus histograms of support and
coherence per band (51-100, 101-300, 301-1000, >1000). **Described, not gated** -- no rule is
declared on this and none is inferred from it.

Reported beside `thema_L` and `L_cal8`: themes per band; roots, root sizes and root children; median
and maximum children; multi-parent share; leaves by the largest theme of 1,000 or fewer they reach;
gene coherence per band; curated recall (secondary, per the 8 Oct decision); the top level with
names; and held-out FDR per stratum including the fresh seeds. Status:
`docs/status/2026-10-09-repair.md`.

## 2026-10-09 11:22:53Z — TRANSCRIBED LATE: the theta grid and the re-gate grid

**These two experiments were declared by Aviyah before any result, and were run that way, but their
declarations were never written into this file.** They existed only in the session prompts, which are
not in the repo. Transcribed here on 9 Oct **after their results were known**, so they must not be
read as pre-registrations: the record of *when* each was declared is the session, not this entry. The
results are in `docs/status/2026-10-08-leaves-theta.md` and `docs/status/2026-10-08-regate.md`.

This is recorded as a process failure of mine. Every other experiment this week was transcribed
before it ran; these two were not, and the gap was found by Aviyah asking whether the documentation
was complete rather than by any check of mine.

### The theta grid, declared 8 Oct before any build

> Split `THETA` into `THETA_MATCH` (recurrence matching and support) and `THETA_MERGE` (merging,
> stays 0.70). Both at 0.70 must give byte-identical v0.4; rerun the byte-identity test.
>
> Arms on L, reusing the cached trees: **M5**, `THETA_MATCH` 0.50 at all sizes; **MS**,
> `THETA_MATCH` 0.70 for clusters under 50 members and 0.50 at 50 or more. Per arm: re-solve floors
> on seeds 3001-3003 and check on held-out 4001; if a cap fails, use 10 seeds 3001-3010 checked on
> 4001+4002. Build; report stability between run halves.
>
> **Decision rule, declared in advance:** prefer the arm with the most themes of 60-800 members,
> among arms meeting ALL of: FDR within caps; 3-10 and 11-50 recall not worse than `thema_L` by more
> than 2 points with a CI excluding 0; gene coherence at least 3x random in every band.

Motivation, from the reviewer's diagnostic: Ward clusters of 60-2,000 members recur at Jaccard 0.5
but almost never at 0.70 (median support 60-200: 0.26 against 0.00; 801-2,000: 0.81 against 0.05),
while scrambled clusters recur at neither.

**Outcome: MS was the only arm meeting the FDR and recall conditions, and it gained 2 themes of
60-800 against `thema_L`'s 23.** M5 failed recall because at 0.50 four of six strata get no solved
floor at all. The coherence condition failed for every arm including the reference, at 1001+.

### The re-gate grid, declared 8 Oct before any result

> Reuse the cached materials, re-gate and build. Match threshold: 0.70 (`thema_L` material), 0.50
> (M5), and 0.70 below 50 / 0.50 at 50 or more (MS). Floor rule: "current" (with the 0.33 minimum)
> and "calibrated" (effective = the solved floor, no minimum). Six arms; only the three "-cal" arms
> are new. Calibration: 10 scramble seeds 3001-3010 and held-out 4001+4002 for every arm. Caps:
> overall at most 0.01, every stratum at most 0.02. Report any cap failure; do not pick floors from
> the held-out side.
>
> **Decision rule, declared in advance:** among arms with FDR within the caps and no loss of small
> themes (3-10 band within 5% of L, clarified mid-run to mean at least 95% of L's count, more being
> fine), prefer the arm with the most themes of 51-1000 members, provided gene coherence in 51-1000
> is at least 3x random and no theme has more than 30 children after collapse.
>
> Two additions, each declared before the result it bears on and labelled in the report: the
> **"-cal8" arms**, floors solved to a 0.008 overall calibration target, added after seeing MS-cal's
> held-out FDR of 0.01009; and **ranking on theme counts AFTER collapsing near-copies** rather than
> raw counts.

**Outcome: no arm met every condition, because the 30-children condition fails for the reference
too.** Setting it aside, `L_cal8` and `MS_cal8` passed the rest. The 0.33 minimum does remove the
middle -- 51-1000 goes from 27 to 196 themes after collapsing -- but opening the gate makes the
widest root worse, 227 children to 585, which refuted the mechanism the grid was built to test.

## 2026-10-09 12:56:26Z — PLAUSIBILITY of thema_L_repair: 97.2% of a sampled build is coherent or a linked umbrella

**EXPLORATORY.** LLM-judge assessments made by the reviewer with Aviyah outside ccode, on
`data/ontology/v0.4-leaves/thema_L_repair`. **Not a declared test, not run under the protocol, and
not reproduced by ccode.** Judges saw member names only -- an independent check, since names are
never used in construction -- but a verdict is a language model's opinion of biological coherence,
not a measurement against a reference. Full write-up:
`docs/status/2026-10-09-reviewer-plausibility.md`; raw files in
`data/experiments/reviewer_sample_2026-10-09/`.

**A 10% sample per size band, seed 20261009, 879 themes, after three judging rounds:**

| verdict | share |
|---|---:|
| coherent, or a linked umbrella | **97.2%** |
| a coherent core with misfits | 1.7% |
| incoherent or an unlinked mixture | **1.1%** |

**Of the 33 sampled themes of 101-1000 members, 29 are coherent and 4 are umbrellas.** **Five of
the eight giant roots are incoherent**, which agrees with the independent gene-coherence measurement
in `docs/status/2026-10-09-giants.md` -- six of the eight are under 3x against a size-matched null,
and one is at 0.68x. Two methods, different evidence, same verdict on the giants.

## 2026-10-09 12:56:26Z — Unnamed TBA BTM modules must be judged with their description and genes

**EXPLORATORY**, same review. 83 BTM modules in the universe are named "TBA" and carry no usable
name. Judging a theme that contains one on names alone is judging it with a hole in it.

Every sampled theme containing a TBA module (102 themes) was re-judged with each module's
**generated description** from `pathway_descriptions.tsv` and its **first genes**. With those,
**22 of 29 previously flagged themes were coherent.**

**Consequence for any future judging, LLM or human: a TBA member must be shown with its description
and genes, or the theme must be excluded from the sample.** Roughly three quarters of the flags
those modules produced were artefacts of the missing name, not of the theme.

## 2026-10-09 12:56:26Z — Umbrella themes separating one level down is the INTENDED DAG behaviour

**EXPLORATORY**, same review. Several themes judged "partial" on names turn out to be **linked
umbrellas**: hemostasis together with eicosanoids, mitochondrial metabolism together with
translation. One level down they **separate into curated-like sub-themes**, with the bridging
pathways sitting under both parents -- which is what multi-parent containment is for.

**This is recorded as correct behaviour, not a defect.** A reader who wants the specific theme finds
it one level down; a reader who wants the connection finds the umbrella. It is also why a flat
"coherent / incoherent" verdict on a DAG node is the wrong question: the 1.1% genuinely incoherent
rate above is only meaningful because round 3 asked separately whether a link exists.

## 2026-10-09 12:56:26Z — FOUR OPEN ISSUES in thema_L_repair, recorded before any rule is chosen

**EXPLORATORY** diagnosis. No rule is declared on any of these and none is inferred.

**(a) The giant roots.** Eight roots of 1,000+ members, five judged incoherent by the reviewer and
six measuring under 3x gene coherence. They share 80-89% of their children with each other and are
the sole parent of 85% of the build.

**(b) Fans: a stable core surrounded by small overlapping low-support variants, propagating upward
as a lattice.** The worked case is `n00150` with six parents, pairwise Jaccard 0.47-0.69 -- all below
the 0.70 merge. Each facet rests on one or two pathways and the other members shuffle between
parents. **No node within three levels contains all six**; instead about twenty small ancestors of
13-35 members each cover one to four of them, then scatter into the giant roots. There is no
platelet-activation node at any level. Many lattice nodes carry support at or below 0.2, which
points at the low cal8 floors.

**(c) Sibling near-twins just under the 0.70 merge.** Themes sharing a parent, neither nested,
sitting at a Jaccard the merge rule cannot see.

**(d) Chain nodes just under the 90% collapse.** A child holding 85-90% of its parent survives the
declared collapse at 0.90.

Issues (b), (c) and (d) are all the same shape: **structure that is redundant by eye and below every
threshold the build applies.** The measured counterpart -- how many edges and pairs actually sit in
those windows, and what each candidate rule would remove -- is
`docs/status/2026-10-09-redundancy-measure.md`, declared before its results and reporting counts
only.

## 2026-10-09 13:08:35Z — SECOND plausibility sample: 98.1%, and the residue traces to 18 heterogeneous BTMs

**EXPLORATORY**, same standing as the first sample: LLM-judge assessments by the reviewer outside
ccode, not declared, not reproduced here. Second 10% sample, seed 20261010, **no overlap with sample
1**, bands 3-100 (101+ were already judged in full). 874 themes, TBA BTM members shown with their
generated description and first ten genes from the start. Files: `REPORT2.md`, `judged2.json`,
`rubric4.md` in `data/experiments/reviewer_sample_2026-10-09/`.

**98.1% coherent or a linked umbrella** (766 coherent, 91 umbrella), against 97.2% in sample 1 after
three rounds. Two samples agreeing is two opinions agreeing and is worth little by itself.

**What the second sample adds is a mechanism for the residue.** All **three** incoherent themes are
built from BTM modules whose own generated descriptions say they are **heterogeneous or
housekeeping**, and **18 of the 83 TBA BTMs describe themselves that way.** So the 1-2% that does not
cohere is not spread thinly through the build; it is concentrated in a nameable, countable set of 18
source pathways.

## 2026-10-09 13:08:35Z — HETEROGENEOUS BTMs: flag or drop is OPEN, not decided

18 of the 83 TBA BTM modules describe themselves as heterogeneous or housekeeping in their own
generated descriptions. A theme built on one of them inherits that: all three incoherent themes in
the second sample came from this set.

**No decision is taken.** Both options stay open and neither is implied by the numbers above:

- **flag** -- keep them in the universe and mark the themes that rest on them, so a reader knows why
  a theme looks mixed;
- **drop** -- remove them from the universe, which changes the universe and therefore invalidates
  every build and every floor calibrated against it.

Recorded so the choice is made deliberately rather than by whichever happens first. Dropping is the
larger act: the universe digest changes, so trees, floors and every comparison in this repo would be
against a different universe.

## 2026-10-09 13:08:35Z — FANS of facet parents are INTENDED DAG behaviour, not redundancy

**Aviyah's decision, 9 Oct 2026.** A fan -- a stable high-support core with several parents, each the
core plus one or two pathways that make it a distinct facet -- is **intended multi-parent DAG
behaviour.** The worked case is `n00150` (7 members, support 0.990) with six parents at support
0.555 to 0.050, which the reviewer named as shape change via G12/13, GPVI-GPCR convergence on PLC,
prostanoid receptors, Rap1 integrin activation, Gq-PLC-IP3, and a BTM platelet-activation group.
Several of those are genuinely different facets of platelet activation, and a DAG that represents
them separately is doing its job.

**Consequence for the measurement: fans are measured and described, and fan-merge is NOT proposed as
a removal rule.** `docs/status/2026-10-09-redundancy-measure.md` reports the 274 fans, their parent
counts and their parents' supports, and does **not** carry a fan-merge candidate. The measurement
that showed a fan merge would cascade -- only 4 of the 17 ancestors above `n00150` staying distinct
-- is kept as evidence about the lattice, not as an argument for merging.

**The sibling near-twin rule is reported against this case specifically**: which of `n00150`'s six
parents it would merge at each Jaccard threshold. A sibling rule that silently collapses declared
facets would be removing intended structure, so the threshold has to be chosen knowing that.

~~One point this leaves open and the report states: `n03581` was judged **not** a distinct facet --
it duplicates `n01638` and `n05989` at Jaccard 0.62 and 0.69.~~ **WITHDRAWN 9 Oct 2026 -- the
reviewer never judged `n03581` not distinct, and ccode's own measurement contradicts it: every one
of the six parents adds at least one pathway no co-parent has. See the correction entry below.** The
sentence that survives the withdrawal is the general one: "fans are intended" is a statement about
the shape, not a guarantee that every parent in every fan is earned -- but it is not evidence
against any particular parent either, and `n03581` was the wrong example.

## 2026-10-09 13:22:15Z — THIRD plausibility sample: 97.6% over 3,153 themes across three samples

**EXPLORATORY**, same standing as the first two: LLM-judge assessments by the reviewer outside
ccode, not declared, not reproduced here. Third sample, seed 20261011, 1,400 themes, no overlap
with samples 1 or 2, bands 3-100, 16 subagents, `rubric4.md`. Files: `REPORT3.md`, `sample3.json`,
`judged3.json`.

**Across all three samples: 3,077 of 3,153 themes (97.6%) coherent or a linked umbrella** -- about
36% of every theme of size 3-100, plus all 42 themes over 100 judged in full in round 1.

**Five of the six incoherent themes contain a self-described heterogeneous BTM**, which is what the
next entry acts on. The sixth is a set of GO "response to drug / ethanol / anesthetic" terms --
genuinely a grab bag, and not attributable to a BTM.

Two corrections from §3 of that report, which supersede what ccode wrote earlier and are recorded
because ccode's version is in this file: the `n00150` lattice has **28 ancestors** (4 giant roots,
24 judged), not the 17 ccode counted *within three levels*; and "no common ancestor within three
levels" holds for all six parents **jointly**, but **four of the six do share `n00918`** within two
to four levels.

## 2026-10-09 13:22:15Z — DROP the 17 self-described heterogeneous TBA BTMs from the next construction

**Aviyah's decision, 9 Oct 2026. This supersedes the earlier entry recording flag-or-drop as open.**

**Rule, declared before applying it:** an unnamed ("TBA") BTM whose generated description -- written
by our own LLM from genes only -- states **in its first sentence** that no single or coherent process
unites the genes, or calls the set heterogeneous or loosely connected.

**The 17 modules:** M125, M153, M184.1, M211, M218, M221, M233, M241, M246, M32.5, M41.0, M41.1,
M41.3, M70.0, M72.0, M72.2, M98.1.

ccode checked all 17 against the rule rather than taking the list on trust: every first sentence
contains "no single process unites", "no coherent biology links", "heterogeneous grouping" or
"loosely connected". All 17 resolve to real keys in `pathways.tsv` and all are named `TBA`.

**The earlier count of 18 came from a looser text pattern; the declared rule gives 17.** Named BTM
M213 "regulation of transcription" matches the words but has a name and a coherent theme, so it
stays. Borderline by content but inside the rule, and kept inside it deliberately: M125 and M233
name a loose shared bias (differentiation, developmental patterning) and M184.1 names a JNK core.

**Recorded as a config list, not an edit to the source table.** `data/excluded_inputs.tsv` carries
`key`, `source`, `excluded_on`, `decided_by`, `rule` and `evidence_first_sentence` for each.
**`data/pathways.tsv` is untouched**, so the source table stays a faithful record of what the four
databases contain and the exclusion stays reversible and auditable.

**Effect when applied:** the 10,770 universe becomes **10,753**; universe L becomes **5,542**.

**On recalibration -- ccode's answer, in the status file and here: a FULL recalibration, not a
fresh-seed re-validation.** The reviewer suggested the cheap check would do. It would not, and the
reason is practical rather than statistical: **the floors' inputs do not exist for the new
universe.** Every tree is built over the universe, so changing the universe changes every real and
every scramble tree, hence every side, hence every support value. A fresh-seed FDR check would mean
applying thresholds solved on the old universe's scrambles to a new universe's -- which is exactly
what the leaves experiment did when it reused v0.4's floors on L, and the 5-5 stratum failed at
0.02715. Once the scramble sides have been rebuilt -- which re-validation also requires -- solving
is seconds of arithmetic, so re-validation is not cheaper than recalibration; it is the same cost
minus the part that makes it correct.

Two riders. The **cal8 0.008 target** is itself a post-hoc choice whose independent confirmation
(fresh seeds 4003-4005, overall 0.00638) was measured on the current universe and **does not carry
over**; it needs redoing on the new one. And the 17 are heterogeneous sets, so they plausibly appear
in a disproportionate share of the weak groupings the floors are fitted to exclude -- the part of the
distribution the calibration is most sensitive to.

## 2026-10-09 14:15:50Z — FLOORS after the 17-BTM drop: REUSE the cal8 floors; do not recalibrate now

**Aviyah's decision, 9 Oct 2026. This overrides ccode's recommendation of a full recalibration**,
which is recorded in `docs/status/2026-10-09-reviewer-plausibility.md` and stands as the argument it
was; the decision is Aviyah's and is taken knowing it.

**Use the existing cal8 floors. Do NOT recalibrate and do NOT run new scrambles now.**

Aviyah's reason: the floors are solved from the **scramble side**, and removing 17 of 10,770 inputs
(**0.16%**) should leave the scramble null essentially unchanged.

**Did the digest check need an override? No.** ccode checked: nothing in the pipeline compares a
floors file's universe against the build's. `scripts/leaves_build.py` reads floors from
`--floors-file` and applies them directly; it records `leaves_digest` and `universe_digest` in the
manifest but never tests them against the floors. `scripts/regate_floors.py` does not test either.
The one real digest check, `universe.load_embedded`, compares the artifact's recorded
`universe_digest` against the digest computed from `pathways.tsv` -- and since `pathways.tsv` is
**not** edited (the 17 are excluded by config in `data/excluded_inputs.tsv`), that check still
passes. So **no override was required, and no code change was made.**

**That is precisely why this is written down three times.** The reuse is silent: no check fires, no
log line appears, nothing in the pipeline would tell a later reader that the floors were calibrated
on a different universe from the build they gate. The three records are the only thing standing
between this decision and an unexplained set of floors six months from now:

- **(a) here, in `DECISIONS.md`**;
- **(b) in the build's own metadata** -- the note is written into
  `data/ontology/v0.4-leaves/regate/floors_L_cal8.json` as `reuse_note`, and appended to that
  record's `source` string, which `leaves_build.py` copies verbatim into every manifest it writes as
  `floors_source`. **So every future build using these floors carries the sentence in its own
  metadata without anyone remembering to add it**, plus
  `data/ontology/v0.4-leaves/README.md` for a human reading the directory;
- **(c) as an open to-do** in `docs/status/2026-10-09-redundancy-measure.md`.

The sentence recorded in every build's metadata: *"floors: cal8, calibrated on universe 10,770,
reused after the 17-BTM drop"*.

**The open to-do, recorded verbatim:** *"Consider re-running scrambles on the current universe and
updating the floors later; until then all builds after the 17-BTM drop use the previous (cal8)
floors."*

## 2026-10-09 14:15:50Z — CORRECTION: `n03581` is a distinct facet; sibling merge stays at 0.70

**Two corrections and one decision, 9 Oct 2026.**

**Correction 1.** The claim that the reviewer judged `n03581` "not distinct" is **wrong and is
withdrawn.** The reviewer never said it; it entered this file through ccode's write-up of a relay.
**Every one of `n00150`'s six parents adds at least one pathway no co-parent has**, which ccode
confirmed by measurement rather than accepting on correction: `n01638` 2 unique, `n03581` 2
(`btm:M32.1`, `btm:M32.8` -- platelet activation (II) and cytoskeletal remodeling), `n04153` 2,
`n05795` 3, `n05989` 1 (`reactome:R-HSA-392517`, Rap1 signalling), `n06563` 3. **None of the six is
at zero.** The phrase has been struck in the entry that carried it and removed from both status
files.

**Correction 2.** REPORT3's "7 rungs at 0.80" on the `n00150` lattice was wrong -- it used
de-duplicated member counts. **ccode's 6 is right**: the seventh edge, `n01879` -> `n08023`, is
32/41 = **0.780**, below a 0.80 threshold. Recorded because ccode flagged the discrepancy and the
reviewer confirmed the error was theirs.

**DECISION: the sibling merge stays at 0.70.** At 0.70 nothing merges in the `n00150` lattice under
either reading of the rule, which is where the build already sits. The measured alternative at 0.60
would delete `n05989` -- the only parent carrying Rap1 -- for recurring less often rather than for
adding nothing.

## 2026-10-09 14:15:50Z — IDEA, NOT ADOPTED: a unique-contribution test for fan parents

Recorded as an idea with its measurement, and **not adopted**. Rule as contemplated: remove a fan
parent **only if every member it adds is already present in a co-parent** -- that is, only if it
contributes nothing no sibling facet already carries.

**On `n00150` it removes none of the six parents.** Unique members added, measured: `n01638` 2,
`n03581` 2, `n04153` 2, `n05795` 3, `n05989` 1, `n06563` 3. Every parent clears the test.

Why it is worth recording even though it removes nothing here: it is the only candidate so far whose
criterion is **what a node contributes** rather than how often it recurs or how much it overlaps. The
support-based tie-break fails on exactly this case -- it would delete `n05989` for having support
0.060 while that parent is the sole carrier of Rap1 signalling. A rule of this shape could not make
that mistake. Whether it is useful at scale is unmeasured: it was run on one fan.

## 2026-10-09 14:15:50Z — FULL CENSUS: every theme of size 3-100 judged once; 97.4%

**EXPLORATORY**, same standing as the samples. `REPORT4.md` and `judged4_rest.json`: all **5,603**
remaining themes of size 3-100, judged with `rubric4.md` by 40 reviewer subagents. With samples 1-3
and round 1's full check of the 42 themes over 100, **every theme in `thema_L_repair` has now been
judged once.**

**8,529 of 8,756 (97.4%)** across bands 3-100. The sample estimates (97.2-98.1%) held, which is the
useful result: the samples were not optimistic.

**Where the 151 census problems come from**, and the second source is new:

1. **the 17 self-described heterogeneous BTMs** -- in 21 of 25 incoherent themes, 3 mixtures and 17
   core+misfits, so **41 of 151**. Already decided: dropped.
2. **gene-specific transcription-regulation and TF-motif sets** -- "regulation of CDH1 / PTEN /
   PD-L1 / RUNX3 / PAX3 targets", motif sets. These **group by form, not by process**: the thing
   their members share is the phrase "transcriptional regulation of gene X", not a mechanism.
   **Recorded as an observation. No action.**
3. orphan small terms with no natural home (magnesium transport, creatine, inositol transport);
4. developmental-signalling pairs judged strictly as mixtures (Wnt + Notch, Notch + Hedgehog) --
   defensible as an umbrella, but the rubric required a specific mechanism;
5. isolated pairings (kynurenine-NAD + polyamines, olfaction + hearing, vitamin K + vitamin C).

Source 2 is a different kind of failure from source 1 and is **not fixable by dropping inputs**: the
sets are individually meaningful and it is the embedding that groups them by their shared wording.
Noted for whenever the text representation is revisited; nothing follows from it now.

## 2026-10-09 15:22:28Z — PLAUSIBILITY means a shared THEME, not shared genes

**Aviyah's decision, 9 Oct 2026.** A theme is plausible when its members share a **theme** -- a
process, system, pathway, mechanism, cell type or tissue, or a shared regulator. **Gene overlap is
reported for information only and is not the criterion.**

This settles something that has been ambiguous all week. Gene coherence against a size-matched null
has been the primary quantitative measure since the 8 Oct decision, and it remains useful -- but it
is **evidence about**, not the **definition of**, plausibility. The reviewer's §7.3 is the reason:
neither resampling support nor gene overlap separates the incoherent clusters from the coherent
ones. A grouping can share genes and no theme, or share a theme and few genes.

Consequence: gene coherence keeps being reported in every build table and is no longer the thing a
build is judged on. Where the two disagree, the theme judgement decides.

## 2026-10-09 15:22:28Z — REGULATORY-SIGNATURE sets are acceptable groupings; no action

**Aviyah's decision, 9 Oct 2026.** TF motif sets, TF target sets and "regulation of transcription of
gene X" sets are **acceptable groupings**. A shared regulator is a theme.

This **supersedes** the observation recorded earlier today, which treated them as the second source
of census failures on the grounds that they "group by form, not by process". Under the definition
above a shared regulator counts, so grouping by regulator is grouping by theme. **No action**: they
are not excluded, not flagged, and not counted against a build.

## 2026-10-09 15:22:28Z — EXCLUSION 2 agreed; the plan is the reviewer's four open items

**Aviyah, 9 Oct 2026.** Exclusion 2 is **agreed** -- the declared rule is the next entry, written
before any judging.

**The plan is the four steps in the reviewer's open items** (`REVIEW_FULL_REPORT.md` §12 items 1-4;
the prompt called this section 15 and the file ends at §13, so this is recorded by content):

1. exclusion 2 -- rule, then a blind run, then append to `data/excluded_inputs.tsv`;
2. the chain-collapse survivor rule -- measure, then decide, **then** decide on 0.85;
3. rebuild with the exclusions and the chosen structural rules, reused floors noted;
4. the giant roots and a recursive top level.

**Explicitly NOT decided, and not to be inferred from any measurement already taken: the chain
threshold, the chain survivor rule, the giant roots, and the recursive top level. They come after
the re-evaluation.** Step 2's measurement exists (62% of edges in [0.85, 0.90) keep the less stable
node); the decision it feeds does not.

## 2026-10-09 15:22:28Z — RECORDED: the reviewer disputes ccode's "keeping the child breaks containment", and the reviewer is right

**ccode's claim was wrong and is withdrawn.** It is recorded here rather than quietly dropped
because it appeared in a status file and could have discouraged a rule on a false ground.

The claim: a chain-collapse survivor rule that keeps the higher-support **child** instead of the
containing **parent** would break containment. The reviewer's dispute (`REVIEW_FULL_REPORT.md` §12
item 0): not shown.

**ccode tested it. The DAG does not become invalid.** Over the 341 edges in [0.85, 0.90) where the
child's support exceeds the parent's -- the edges such a rule would act on -- deleting the parent and
keeping the child always leaves a set of nodes over which `hasse` produces a **valid strict-
containment DAG**. Re-stacking is already what both repair fixes do. So "breaks containment" was
simply wrong.

**What the test does show, which is a cost but not that cost:** in **241 of 341 cases (70.7%)** the
deleted parent has another child that is **not** inside the surviving child, so that sibling must
re-parent upward, skipping a level; in **7** cases the parent has no parent either, so the sibling
would be orphaned to root. And the members only the parent held -- median 3, max 14 -- lose their
grouping at that level.

**No rule is changed.** The concrete cases are in
`docs/status/2026-10-09-exclusion2-rebuild.md` for whenever step 2 is decided.

## 2026-10-09 15:23:11Z — EXCLUSION 2: the declared rule, written BEFORE any judging

**Aviyah's rule, 9 Oct 2026. Recorded here before a single candidate was judged**, and before the
mechanical screen was run.

> **Exclude an input set if NEITHER its source name NOR its generated description identifies one
> specific biological theme.**
>
> A theme counts if it is a **process, system, pathway, mechanism, cell type or tissue, or a shared
> regulator** -- a TF, motif or target set counts.

Worked example of an exclusion, from Aviyah: `btm:M248`, whose description says its members have
"in common little more than a shared place in interaction screens". A shared place in a screen is
not a process, a system, a mechanism, a cell type or a regulator.

**Scope: all 10,770 sets in the universe**, which covers universe L as a subset.

**Two stages, both recorded.**

- **Stage 1, a mechanical screen**, so the candidate set is reproducible and not chosen by eye: all
  unnamed ("TBA") BTMs, plus every set whose description contains any of -- *no single*,
  *no coherent*, *heterogeneous*, *loosely*, *mixed*, *little more than*, *best read*,
  *rather than a single*, *grab*, *miscellaneous*, *uncharacterised*. Candidate counts are reported
  per source.
- **Stage 2, blind judging by Claude Code subagents** -- not an external API, so no spend -- against
  a fixed written rubric. **Judges see ONLY the name and the full description.** No genes, no cluster
  or theme data, and none of the reviewer's verdict files, so the judgement cannot be contaminated by
  how a set happened to cluster. Output per set: yes/no plus **the one sentence that decides it**.

**The 17 exclusion-1 sets stay excluded regardless of what stage 2 says about them.**

Results append to `data/excluded_inputs.tsv` with `rule = exclusion-2`, the deciding sentence as
evidence, and whether the set is in universe L. `data/pathways.tsv` is **not** edited, as for
exclusion 1.

## 2026-10-09 16:25:14Z — STEP 3 DONE: thema_L_x2 evaluates at 97.7%, and the incoherent count falls 44 -> 18

**EXPLORATORY**, same standing as every judging round this week: LLM-judge assessments by the
reviewer with Aviyah using Claude Code subagents, outside ccode, not declared, not reproduced here.
Copy at `docs/status/2026-10-09-x2-evaluation.md`; raw files in
`data/experiments/reviewer_eval_x2_2026-10-09/`.

**All 8,740 themes judged.** 1,310 carried their `thema_L_repair` verdict (identical member sets);
7,430 newly judged with `rubric4_x2.md`, which adds one line: judge by shared biological **theme**,
not by gene overlap -- the 9 Oct definition.

| | `thema_L_repair` | **`thema_L_x2`** |
|---|---|---|
| coherent or linked umbrella | 97.4% | **97.7%** |
| incoherent | 44 | **18** |
| small incoherent | 39 | **8** |

**The 22-cluster family of unnamed housekeeping modules is gone** -- that is exclusion 1 and 2 doing
exactly what they were for. The 8 small incoherent that remain are the drug/ethanol/anesthetic sets
(3), magnesium/creatine orphans (2), a motif-defined BTM, a 5-member leftover-BTM cluster, and a
3-member phosphoinositide cluster.

**A free check worth having: judging noise is about 1%.** For the 5,465 newly judged themes that
match a `thema_L_repair` theme at Jaccard >= 0.7, the two independent judgements agree on
ok/not-ok in 98.9% of cases (36 went ok -> not, 24 not -> ok).

**And the top got worse, which the headline hides.** Every theme over 1,000 members is bad: 10 roots,
9 incoherent and 1 mixture, against `thema_L_repair`'s 9 roots of which 2 were coherent. Between 301
and 1,000, four of six are bad. **The middle -- everything up to 300 members -- is 97.7-100% ok in
every band.** ccode's own structural measurement agrees on the direction: giants went 8 -> 10.

## 2026-10-09 16:25:14Z — EXCLUSION-2 CORRECTION: go:GO:0010800 was excluded against the declared rule

**The rule tests whether NEITHER the name NOR the description identifies a theme.**
`go:GO:0010800`, *positive regulation of peptidyl-threonine phosphorylation*, has a **name that
identifies a specific mechanism**, so the test is not met and it should not have been excluded. The
blind judge excluded it on the description alone ("heterogeneous rather than a single cascade"),
which is half the rule.

ccode flagged this one in `docs/status/2026-10-09-exclusion2-rebuild.md` as "the single call most
worth reviewing, because the name arguably does identify a mechanism", and the reviewer reached the
same conclusion independently.

**Marked, not reversed now.** `data/excluded_inputs.tsv` gains a `status` column; this row reads
*"reinstate at next rebuild"* with the reason. **No rebuild** -- `thema_L_x2` keeps it excluded and
its numbers stand as measured.

| | |
|---|---:|
| rows in `data/excluded_inputs.tsv` | 23 |
| **effective exclusions** | **22** |
| of those, in universe L | **19** |
| marked for reinstatement | 1 |

By rule, of the 22 effective: exclusion 1 **17**, exclusion 2 **5**.

## 2026-10-09 16:25:14Z — btm:M248, the rule's own example, was judged "yes" and STAYS IN

The exclusion-2 rule quoted `btm:M248` as an example of a set to exclude -- "in common little more
than a shared place in interaction screens". **The blind judges kept it**, on the sentence *"Several
of them converge on mitotic and genome-maintenance functions, marking proliferation-linked
processes."*

**The rule decides, not the example.** `btm:M248` stays in the universe. ccode confirmed it was among
the 172 screened candidates and that its verdict was `yes`, so this is the rule being applied, not
an omission.

Worth recording for what it says about the method: an example attached to a rule is an illustration
of intent, and a blind judge applying the rule to the full description can legitimately reach the
opposite verdict on it. The reviewer's §17.1 reads the same module as part of a weak "proliferative
housekeeping and protein turnover" umbrella, which is consistent.

## 2026-10-09 16:25:14Z — The large-theme verdict changes are JUDGING, not structure

**Every large `thema_L_x2` theme has a close counterpart in `thema_L_repair`, at Jaccard 0.72-0.93**
(reviewer's §17.2): metabolism 1,433 <-> 1,405 at J 0.92; immune 814 <-> 826 at 0.92; nuclear genome
789 <-> 800 at 0.93; the giant bags at 0.56-0.91.

**The clusters did not move; the rubric did.** The old large themes were judged under rubric2
(coherent / partial / incoherent); the new ones under rubric4, which requires an umbrella to state a
**specific** link. Metabolism 1,433 went coherent -> incoherent, nuclear genome 789 coherent ->
mixture, immune 814 coherent -> umbrella -- all on the same 40-member random sample from 800-2,600
members. Forty random members of a genuine area look diverse, and the strict rubric penalises that.

**So the "top got worse" figure in the previous entry is two different things and both are true**:
the number of 1,000+ roots really did rise 8 -> 10 (structural, ccode measured it), and the verdicts
on large themes really did fall for rubric reasons (not structural). Neither cancels the other.

One genuine structural loss: `thema_L_repair`'s 1,751-member "development, adhesion, ECM, migration"
theme, judged coherent, **has no clean counterpart in x2.**

## 2026-10-09 16:25:14Z — AREA LEVELS: immune, metabolism and genome exist; signalling, development and neuro do not

A name-keyword check over themes of 80+ members (evaluation only, reviewer's §17.3):

| area | best theme | recall | precision | support | verdict |
|---|---|---:|---:|---:|---|
| immune | `n01014` (814) | 0.88 | 0.46 | 0.805 | **yes** |
| metabolism / transport | `n01438` (1,433) | 0.78 | 0.42 | 0.63 | **yes** |
| genome maintenance / cell division | `n04626` (369) | 0.80 | 0.30 | 0.105 | **yes** |
| signalling | only the giant bags (2,000+) | 0.6-0.7 | ~0.2 | low | **no** |
| development | giants; best clean one is 116 members | 0.18 | 0.67 | | **no** |
| neuro | giants; best clean one is 98 members | 0.23 | 0.61 | | **no** |

Also present: nuclear genome / gene expression (789, support 0.695), RNA processing / translation
(289), RTK signalling (213), DNA repair (181), glycosylation (180), hemostasis + eicosanoids (155).

**Signalling, development and neuro sit inside the giant bags.** The reviewer's working explanation,
explicitly **not yet tested**: these form one continuum in the embedding -- signalling runs through
development, neuro and cancer -- Ward cuts it differently every run, so no stable 300-800-member
sub-area recurs; what recurs rarely is "half the universe", and the 10+ floor at 0.025 admits those
halves as overlapping giants.

That is the case for a recursive top level: cluster the good middle themes into areas rather than
relying on Ward's top splits. **It is not decided** -- it is step 4.

## 2026-10-09 16:25:14Z — STABILITY refined: the 22.5% churn is concentrated in low-support themes

ccode reported that 22.5% of `thema_L_x2`'s themes have no `thema_L_repair` counterpart at Jaccard
0.7, and that the cause was the trees rather than the removed members. The reviewer's breakdown
**refines that in a way that matters**, and ccode's figure alone was more alarming than the truth:

| | |
|---|---:|
| **themes with support >= 0.1 that reproduce** | **89%** |
| themes with support >= 0.5 that reproduce | **91%** |
| median support of **identical** themes | 0.685 |
| median support of **new** themes | **0.045** |

**The churn is almost entirely low-support themes.** Among themes that recur reliably at all, 89-91%
survive a universe change of 0.36% -- which is close to the 82-85% between-half stability measured
within a single build, and this is effectively two independent builds.

Plausibility by match class tells the same story: identical 98.4% ok, matched at J >= 0.7 98.3%, new
95.7% -- the new themes are slightly less plausible and mostly weak.

## 2026-10-09 16:25:14Z — STEP 4 IS PENDING AVIYAH: no decision on the chain rule, the giants, or a recursive top

Recorded so the next session does not infer a decision from the measurements. **Pending Aviyah, with
nothing decided and nothing to be read as decided:**

1. **the chain-collapse threshold** (0.80 / 0.85 / 0.90) -- measured: 550 edges in [0.85, 0.90), no
   distributional valley, the range above 0.90 empty by construction;
2. **the chain survivor rule** -- measured: the declared rule keeps the less stable node on 62% of
   those edges; the alternative was shown not to break containment, at the cost of 241 of 341
   siblings re-parenting upward;
3. **the giant roots** -- 10 of them, all judged bad, sharing most of their children;
4. **a recursive top level** -- clustering the good middle themes into areas instead of using Ward's
   top splits, which §17.3 argues for and nobody has tested.

The measurements for 1 and 2 exist and are in `docs/status/2026-10-09-redundancy-measure.md`. **The
decisions they feed do not.**

## 2026-10-09 16:56:29Z — Baseline frozen 2026-10-09 (thema_L_x2)

**Aviyah's decision, 9 Oct 2026.** `thema_L_x2` is frozen, **exactly as built**, as the baseline
**"THEMA baseline 2026-10-09"**.

> Baseline frozen 2026-10-09 (thema_L_x2). New builds go to new directories and report a comparison
> to the baseline: theme counts by band, match at J >= 0.7, and plausibility where judged.

If work gets tangled, this is what we revert to.

**The frozen copy** is `data/ontology/frozen/baseline-2026-10-09/` -- 18.9 MB, 15 files plus
`CHECKSUMS.sha256`. It holds the build (`nodes.tsv`, `members.tsv`, `edges.tsv`, `unplaced.tsv`,
`manifest.json`, `browse.html`, `match_to_repair.tsv`, `compare_to_repair.json`), the inputs it
depends on (`excluded_inputs.tsv` as of the freeze, `floors_L_cal8.json`, `universe.json`, the
subsample manifest `trees_build_log.json`), the evaluation (`all_verdicts_x2.json`, `REPORT_x2.md`),
and `FROZEN.md` -- the full command line, every parameter, the universe, the code identity, the
headline numbers, and how to rebuild and how to revert.

**It is frozen for real, not by convention.** `tests/ontology/test_frozen_baseline.py` re-hashes
every file against `CHECKSUMS.sha256` on every test run and fails on a changed file, a deleted file,
or a new file added without a checksum. All three were confirmed to fail before this was written.
Files are also mode 444 as a speed bump; git does not preserve that, so the test is the real guard.

**Frozen as built, including the one known error.** `go:GO:0010800` was excluded against the
declared rule and is marked *"reinstate at next rebuild"*, but **this baseline keeps it excluded**,
so every recorded number is exactly what was measured. The baseline stands on **23** exclusions
while **22 (19 in L)** are effective going forward; the next rebuild differs by that one input, and
`FROZEN.md` says so in the universe section rather than quietly reconciling the counts.

**The code.** `HEAD` at build time was `7ba3720703bec06ea9610f4976e7934ee0b69faf`, but the working
tree was **dirty** -- four modified and two untracked scripts -- so that hash alone does not
reproduce the build. `docs/status/commit-2026-10-09-baseline.sh` commits exactly that work and
creates the annotated tag **`thema-baseline-2026-10-09`**, which is the reproducible pointer.
`FROZEN.md` also records the sha256 of the nine sources that ran, so identity is checkable without
the tag.

**One correction found while writing it up.** The browse export needs
`--version 0.4-leaves-x2 --build-version 0.4-leaves` together; `--version 0.4-leaves` alone reads
the wrong `universe.json` and reports 5,559 pathways instead of 5,539. The recorded command was
verified to reproduce the frozen `browse.html` byte-identically, and the trap is written into
`FROZEN.md` rather than left to be rediscovered.

**What this does not decide.** Step 4 -- the chain threshold, the chain survivor rule, what to do
about the giant roots, and whether the top level is built recursively -- is **open and pending
Aviyah**. Freezing a baseline is not choosing any of it.

## 2026-10-09 21:23:27Z — Statistics layer: the reviewer's implementation considerations, recorded

> Statistics layer: reviewer's implementation considerations recorded (testing resolution /
> DAG-structured testing, support weighting, facet-distinctive attribution, giant roots excluded
> from testing, validation). These are possibilities, NOT decisions; decide and declare them when
> the statistics layer is implemented.

Recorded at `docs/plans/2026-10-09-stats-implementation-considerations.md`, copied verbatim from
`data/experiments/reviewer_notes/2026-10-09-stats-implementation-considerations.md`.

**Nothing in it is declared.** The note itself says so in its second line, and it is filed under
`docs/plans/` rather than as a decision for that reason. The existing plan stays authoritative:
`thema-master-spec.md`, `thema-brief.md` section 5 (BASIS / CHILD-UNIQUE / PARENT-BEYOND, BH / BY,
the empirical-FDR audit, planted truth), `thema-soft-membership-plan.md`, and the paper's stats
section. The note only adds what the multi-facet DAG of Oct 2026 raises, chiefly that the BH family
is now 8,740 themes and many more edges rather than the 30-50 the plan was written for.

Each option must be **chosen and declared before results are seen**, per the standing rule.
