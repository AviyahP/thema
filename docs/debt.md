# Debt

Things deliberately not done, with enough context to pick them up. Each entry says what it is, why
it was deferred, and what would settle it.

## Per-node cohesion is not measured

*Logged 2026-09-21.*

Neither builder reports how tight a node actually is. `recurrent_dag` carries `support` — how often a
grouping recurred — and `inclusion` per member, but nothing says whether a node's members are close
to each other in embedding space or merely ended up in the same branch. `ward_tree` carries nothing
at all beyond the cut that produced it.

**Why it matters.** Two nodes can have identical support and very different quality: one a tight
cluster, the other a ragged group that happened to survive resampling. A reader browsing the demo
cannot tell them apart, and the naming step will be asked to name both.

**Why deferred.** The tol × m grid decides whether `recurrent_dag` ships at all. Measuring cohesion
on a method that may not ship is work that may not be needed, and it is not required to choose
`m` or `tol`.

**What would settle it.** Mean pairwise cosine within a node against a size-matched random baseline,
reported per node in `nodes.tsv` and surfaced on the node card. The gene-overlap evaluation
(`eval-plan.md` §14 item 2) is the independent check; cohesion is the cheap internal one, and being
internal it is circular on its own — a node is cohesive in the space it was clustered in. It is a
triage signal, not evidence.

## Cohesion must be measured on mean-centred embeddings

*Logged 2026-09-21.*

Measure cohesion on **mean-centred** embeddings -- for the cohesion calculation only, never for the
vectors Ward clusters -- before using it for any decision.

**Why.** BioLORD vectors occupy a narrow cone: mean pairwise cosine over 100 random 1,639-pathway
subsets was 0.2734 with a standard deviation of 0.0009. Against that, the runaway node scored 0.2827
-- z = 10.8, and meaningless, since the node was 88% of the collection and could not have been
anything else. The statistic has almost no dynamic range because every pair starts out similar.
Centring removes the shared component and lets a real difference in tightness show.

**Not yet needed.** It was used once, to confirm the runaway node was not a genuine theme, and the
answer did not rest on it: no grouping within 20 of that size existed in the pool before the merge,
which settled it. The next use -- ranking nodes by quality, or gating the namer -- is the one that
needs the centred version first.

## Statistics engine: umbrella members dominate theme gene unions

*Logged 2026-09-22; **still open** as of 2026-09-23 -- nothing has been implemented and no rule is
adopted in the ontology. **Open question, not a decision.** Nothing is implemented, and no rule is
adopted in the ontology.*

Theme gene unions are dominated by one member in **265 of 391 nodes**; in **93%** the dominant
member does not contain the others, it just outweighs them by size. Open: whether and how this
should affect theme-level statistics. To be discussed before the engine is designed. Candidate
directions noted, none chosen:

- report per-member contributions;
- a leave-largest-out test;
- a different theme gene set than the plain union.

### The measurement behind it

Taken on `data/ontology/v0.2/recurrent_dag_ward_t15_m33/` (ward, tol 0.15, m 0.33, 391 nodes).
A node counts as dominated when its largest member's gene set is more than half the union of all
its members' genes.

| | |
|---|---|
| nodes dominated | 265 of 391 (68%) |
| of those, dominant member IS effectively the whole union (share >= 0.99) | 9 |
| dominant member contains >= 90% of the other members' genes | 19 of 265 (7%) |
| dominant member merely outweighs the others | **246 of 265 (93%)** |
| dominant member's source | GO 204, Reactome 52, Hallmark 9 |

The 7% figure is the one that matters. The obvious explanation for a dominated union is GO's own
hierarchy -- a general term clustering with its specialisations, where the union equalling the
parent is correct arithmetic and not a defect. **That explains only 19 of 265.** In the rest the
large member sits beside the smaller ones without containing them: `n0271`, 7 members, union 237,
dominated 0.81 by "cellular response to starvation" (192 genes), which shares **0%** of its genes
with the other six.

### Why no threshold was adopted

A fixed gene-count cut was measured and rejected as insufficient rather than wrong:

| cut | pathways in build | nodes touched | dominated nodes it would address |
|---|---|---|---|
| 200 | 160 / 1854 | 184 / 391 | 158 / 265 (60%) |
| 300 | 112 / 1854 | 141 / 391 | 128 / 265 (48%) |
| 500 | 62 / 1854 | 95 / 391 | 88 / 265 (33%) |
| 1000 | 21 / 1854 | 32 / 391 | 31 / 265 (12%) |

No fixed count reaches most cases, because the effect is **relative** -- a member's size against
*its own theme's* union -- and a global threshold cannot express that. A relative criterion would
target it better, which is an observation about the shape of the problem, not a proposal.

## A cache of `family_members` output drove the machine into swap

*Logged 2026-09-23. **Fixed**; recorded because the shape of the mistake will recur.*

The first strict-target rebuild cached `family_members()` output for all ~57,000 groupings so that
both membership cutoffs could complete from one pass, instead of recomputing it per cutoff. It ran
the machine out of memory: **swap 31 GB of 32 GB, zero free**, and the job stalled for roughly two
hours producing nothing before it was killed. Even `ps` was timing out by then.

**Why it was so much bigger than it looked.** `family_members()` returns `(candidate bitset,
inclusions)` — and the inclusion dict covers **every candidate**, not just the members that survive
the cutoff. For a large grouping that is hundreds of entries. Across 57,000 groupings, held
simultaneously, it reaches tens of GB. The mental model was "one small tuple per grouping"; the
reality was a dict per grouping over a much larger set than the one being kept.

**The fix is to recompute, not to cache.** Completion costs **~0.09 ms per grouping, about 4 s per
side** — roughly 10 s for two cutoffs. The cache traded gigabytes to save ten seconds. Null sides
now retain only `(size, support, cohesion)` tuples; only the real side keeps member sets, and only
because the build needs them. Peak RSS after the fix: **0.6 GB**, against a run that had been
heading into the tens.

**What to carry forward.** Before caching a per-item result across tens of thousands of items, size
one item first — and size what it actually holds, not what it is named for. The long-running scripts
in this work now print peak RSS per stage, so the next such mistake is visible within a stage
rather than after two silent hours.

## `pathway_descriptions.tsv` will need splitting, at the third live generation

*Logged 2026-09-23. **Decided, not yet acted on.** The trigger is stated so this is picked up on
time rather than under pressure.*

The table holds one row per `(key, prompt_version, model)` and is rewritten whole on every merge,
including a one-row top-up. At two generations (v3 superseded, v4 current) it is 13 MB.

**History growth is NOT the reason to act.** Measured, not estimated:

| | |
|---|---|
| table raw | 13 MB |
| as git stores it (zlib) | 3.9 MB |
| one generation's 10,817 rows, raw | 10.8 MB |
| **the same rows compressed -- what a generation actually costs in history** | **~3.4 MB** |
| measured pack growth over a simulated second generation | +3.8 MB |

Earlier generations delta almost perfectly against the previous commit, so only genuinely new prose
is paid for. Four more generations would add ~15 MB of history. That is not a problem.

**The WORKING FILE is the reason.** It grows ~10.8 MB per generation:

| live generations | file size | note |
|---|---|---|
| 2 (today) | 13 MB | |
| 3 | 24 MB | uncomfortable to diff |
| 4 | 35 MB | |
| **5** | **46 MB** | GitHub warns above 50 MB |
| 9 | ~90 MB | GitHub **blocks** above 100 MB |

Before any limit is reached it is already unpleasant: `git diff` is unusable on a 30 MB TSV, and
`merge_tsv` reads and rewrites the entire file to change one row -- the `go:GO:0050994` retry
rewrote 13 MB to fix a single description.

**Decision: one file per prompt version** -- `pathway_descriptions.v4.tsv`, `.v3.tsv` -- with
`descriptions.read()` reading the current one and `versions()` globbing the directory. **Trigger:
the third LIVE generation**, meaning a third `prompt_version` that consumers read, which includes
`v4-scoped` or `v4-alt` if either is ever promoted.

Why not the alternatives:

- **Compression** (`.tsv.gz`) halves the symptom and makes the file opaque to `git diff`, `grep`
  and eyeballing. The repo already stores it compressed, so nothing is gained in history and the
  auditability that makes this table trustworthy is lost.
- **Git LFS** solves the size ceiling but breaks `grep`/`diff`, adds a dependency and a bandwidth
  quota, and is disproportionate for ~40 MB of text.

**The cost of splitting, stated up front:** `restamp()` and the `status` column currently express
"which generation is current" WITHIN one file. Split, that becomes a naming convention or a pointer
file. That is a real, small piece of work, and it is precisely why this is scheduled for the third
generation rather than improvised at the fifth.

**Unrelated, free:** this repo has never been garbage-collected -- 649 loose objects, no packfiles.
`git gc --aggressive` on a clone took `.git` from 9.8 MB to 4.0 MB.

## Small gene sets are untreated, and they are almost all Reactome

*Logged 2026-09-23. **Open, no action now.** It must not be forgotten before anything is claimed
about cross-source agreement.*

The universe rule keeps every pathway with at least one gene (`DECISIONS.md`, 23 Sep). That is the
right call -- they are real sets with real tests -- but it leaves a large population whose
statistics nothing has yet addressed, and that population is **not distributed evenly across
sources**.

| | count | sources |
|---|---|---|
| fewer than 3 genes (incl. the 47 zero-gene, now excluded) | **490** | all Reactome |
| fewer than 3 genes, in the universe | 443 | all Reactome |
| fewer than 5 genes (incl. zero-gene) | **717** | 714 Reactome, **3 GO** |
| fewer than 5 genes, in the universe | 670 | 667 Reactome, 3 GO |

Smallest set per source: **Reactome 1, GO 4, BTM 8, Hallmark 32.**

**This makes any Reactome-vs-GO comparison confounded by construction**, the `reactome2go` F1
included. Reactome can produce a one-gene set and GO cannot. Any measure sensitive to set size --
gene overlap, Jaccard, kappa, enrichment power -- is therefore partly measuring which database a
pathway came from. A cross-source agreement figure computed without stratifying by size is not
interpretable.

**Where they concentrate.** 478 of the 717 sit under Reactome's **Disease** branch. Of the 308
one-gene sets, **130** are named `Defective X causes Y` and **8** `X variants cause Y` -- 138 under
those two patterns exactly; **244 of 308** match a broader disease-name pattern (`Defective`,
`causes`, `variants`, `mutant`, `deficiency`, `MPS`, `syndrome`, `disease`). So the small-set
population is largely **one gene, one disease** entries, which is a different kind of object from a
50-gene process and probably should not be scored as though it were the same.

*(Three figures here differ from the ones I was given: the "<5 genes" total is 717 rather than 714,
and 3 of them are GO rather than all Reactome -- 714 is the Reactome-only count. The
"Defective/variants" count is 138 under the two named patterns, not 238; 244 matches the broader
disease-name pattern, which is probably what the 238 referred to.)*

**Nothing is proposed yet.** Candidate directions, none chosen: stratify every cross-source metric
by set size; set a minimum size for enrichment reporting while keeping the sets in the ontology;
treat one-gene disease entries as a separate class.

## Support is granular, so BH/BY will lose power

*Logged 2026-09-24. **Open, no action now.***

Support is `runs found / runs eligible` over **100 runs**, so it takes **at most 101 distinct
values**. Under the empirical null test (`docs/spec/amendment-2026-09-24.md`) p-values will
therefore **tie heavily**, and both BH and BY lose power against tied p-values — many themes share
a rank and are accepted or rejected together rather than individually.

**The lever, if power becomes the binding constraint, is the run count.** 100 runs → 101 support
levels; 500 runs → 501. Nothing else in the design changes. Cost scales linearly with runs and
`prepare` is already the expensive stage (~400 s per side at 100 runs), so a 5× increase is a real
decision and not a free one.

Not acted on. Recorded so that, if the correction rejects more than expected, granularity is
checked before the design is blamed.

## Small themes are refinements inside accepted nodes, not free-standing discoveries

*Logged 2026-09-24. **Open, no action now.***

**98% of size 3–4 themes are subsets of a larger theme** — 176/179 at size 3 and 132/134 at size 4,
against 86% at size 10+ (measured on the 1,201-theme build; see
`docs/status/2026-09-24-runs-performed.md` §3).

This means a small theme asserts **finer structure inside a node that has already been accepted**,
not a new grouping in the universe. A null built over the whole universe is therefore answering a
question the theme is not asking: it asks "could this triple arise by chance anywhere?", when the
claim is "these three belong together *within this larger theme*". That is part of why small themes
clear a whole-universe null so easily, and it is a reason the null may be **too lenient** for them
rather than too strict.

**The scrambled side of this comparison has not been measured** — scrambled member sets were not
persisted, so whether scrambled small themes are *also* 98% nested is unknown. Until it is, "the
comparison is not like for like" remains a live possibility rather than a finding.

Candidate direction, none chosen: condition the null on the parent, so a size-3 theme is tested
against scrambled triples *drawn from within a theme of comparable size* rather than from the whole
universe.

## Analysis paths bypass the pipeline's own filters

*Logged 2026-09-24. **A class of error, recorded because it has now happened twice with the same
cause.** Proposal in this entry; not yet implemented.*

**The incidents.** The universe rule excludes 47 zero-gene pathways, 4 of which are in the
1,854-pathway subset. The 31-side tightness calibration ran on embeddings containing all 4. That
was noticed, written up as a caveat — and then **the very next script, the theta sweep, repeated
it exactly.** Noticing an instance does not prevent the next one.

**The cause is structural, not attentional.** `partition_universe()` takes a `PathwayCollection`,
read from `data/pathways.tsv`. Every analysis script instead enters through:

```python
keys = (V / "embedding_keys.txt").read_text().split("\n")
x = np.load(V / "embeddings.npy")
```

There is no `PathwayCollection` anywhere on that path, so **the filter is not merely unused, it is
unreachable**. The pipeline gained a rule that its own analysis code has no way to obey. Anything
written this way will silently use a superseded universe, and the defect is invisible because the
arrays are the right shape and the code runs cleanly.

**The general form:** *a rule enforced at one entry point, while a second entry point exists that
does not pass through it.* Others of this class to watch for — `descriptions.read()` versus reading
the TSV directly; `restamp()`'s status semantics versus a script writing `status` itself;
`export.write`'s validation versus a script writing `members.tsv` by hand. Each is a place where
the guarantee lives in a function rather than in the data.

**Why policing the accessor is not enough.** Scratch and one-off analysis scripts live outside the
repository and cannot be linted, tested, or code-reviewed. A convention they can ignore is not a
guarantee. **The durable fix is to make the ARTIFACT correct**, so that a script which bypasses the
loader still reads the right thing:

1. **Fix the data.** `embeddings.npy` and `embedding_keys.txt` under a version directory should
   contain the universe and nothing else. Dropping 4 rows needs no re-embedding.
2. **Add a verifying loader** (proposed: `src/thema/ontology/universe.py`) that reads those files,
   recomputes the universe from `pathways.tsv`, and **raises** if they disagree — so later drift is
   caught rather than absorbed.
3. **Add a repo test** that fails if any committed file loads an embeddings path outside that
   loader.
4. Record the universe digest in every build manifest, so an artifact can be checked against the
   universe it claims.

Step 1 is what closes the scratch-script hole; steps 2-4 stop it reopening. **Every artifact
currently under `data/ontology/` was built before the rule and contains the 4** — enumerated in
`docs/status/OPEN.md` so none is quoted by accident. `v0.1` is exempt: it is the frozen v3-era
reference and its contents are history, not a current claim.


## Descriptions can end in scraped web text, and nothing checks for it

**66 of 10,770 (0.61%)** carry content appended after a correct description: 64 with HTML tags, one
with a URL and blog timestamp, one with a Nokia 5 smartphone review (`go:GO:0010560`, 10,752
characters against a median of 969). All are v4/opus-5 with `stop_reason: end_turn` -- the model
ran on and the API treated it as a normal completion, output reaching 4,651 tokens against a
typical 330.

**Why it matters:** these descriptions were embedded, so they are in the ontology, and they would
reach the public demo. Found only because a naming call dutifully returned "Nokia 5 launch and
specifications" for a glycosylation theme.

**Why it was missed:** the validator tests content, not shape. It has no length ceiling, no markup
rule, and no test for a second topic starting mid-text. `--report` passed them. The `verify-v1`
fact-check measures truthfulness of the *first* paragraph and would not look at the tail.

**The fix:** regenerate the 66 via `--keys`, and add the three shape rules. Not done.

## 103 descriptions run past the 150-word ceiling

Separate from the corruption above and **not caused by it**: 103 of 10,770 current descriptions sit
outside the declared 90–150 word band, all of them over, ranging **151 to 163 words**. Three of
them were among the repaired rows and were written anyway, because the repair strictly improves
them and the overflow predates it.

This is a generation-quality matter, not a data defect: the descriptions are correct, just long.
Fixing it requires regeneration, which is a priced run, so it is recorded rather than done. The
validator flags them today via `in_range`; the new write gate refuses on `residue` only, so an
over-length row is still written and still reported.


## SUPERSEDED 26 Sep 2026 — "centre for cohesion only"

The 21 Sep note recorded that embeddings were centred for the cohesion statistic and left raw for
Ward, as a deliberate scoping decision. **That is superseded**: Ward now clusters
centred-and-renormalised vectors (`docs/spec/amendment-2026-09-26.md`). Centring is the clustering
input, and cohesion continues to be reported in the clustering space.

## The original calibration's scramble seeds were never recorded

*Logged 2026-09-29. **Open**, and unrecoverable by inspection.*

`FLOORS[centred, 0.25]` and the held-out FDR of **0.0051** that licensed the first freeze came from
"20 calibration + 10 held-out scrambles". **Which scrambles is written nowhere.** The manifest names
the counts and the result; no amendment names the seeds; no committed script drove that run. The
driver existed only as an ad-hoc invocation.

**What it cost.** The 0.0051 cannot be reproduced exactly, only re-derived. Two fresh 20-scramble
sets returned 0.00538 and 0.00360 -- both consistent with the recorded value and with each other
only
in the sense that all three sit inside the seed noise of a 20-scramble estimate, which is about
+/- 0.002. Deciding whether the original run was sound therefore took a 60-side recomputation
rather than a re-run.

**What was recovered.** Pooling 40 calibration scrambles lands every floor within 0.01 of the
committed values, so the original calibration is confirmed as sound. The seeds themselves are not
recovered and cannot be.

**Fixed going forward, not retroactively.** `scripts/calibrate_inclusion.py` takes
`--calibration-seeds` and `--heldout-seeds`, defaults to recorded constants, prints them as
contiguous ranges with a count, and caches every side under
`data/experiments/scramble_sides/{space}_{universe16}/seed{N}.json`. A future calibration is
reproducible from the cache and re-derivable from the seeds.

**The general rule this is an instance of:** a result that licenses a freeze must record every input
that would be needed to reproduce it, and a count is not an input. The same defect would apply to
any run whose driver is an ad-hoc invocation rather than a committed script.

## 83 BTM modules have the title "TBA"

*Logged 2026-09-29. **Open at source**; worked around from naming level 1 onward.*

Eighty-three BTM pathways carry the literal title `TBA` -- unannotated in the source data, not lost
in our loader. They reach **32 themes** of the frozen 0.50 build, **6 of them leaves**: n0508,
n0532, n0573, n0601, n0694, n0756.

**It has already cost a naming verdict.** `n0508` was refused, and its rationale turns partly on a
member the model could not identify -- the leaf's other six members describe respiratory burst and
oxidative killing, and the untitled one could not be shown to belong. The refusal may still be
right; what is certain is that it was made on incomplete evidence.

**Worked around, not fixed.** From level 1 onward a member whose title is `TBA` is rendered by its
description alone, with the description's first sentence standing in for the title. A member with
neither a usable title nor a description is dropped from the prompt rather than shown as a blank.
**The leaves are NOT re-run for this**: they are named and the names have been read and judged, and
re-rendering them would spend money to change prompts whose output is already assessed.

**A consequence worth knowing.** A request is keyed on its members, not on its rendering, so the
six affected leaves keep their cached names while their prompt text would now render differently.
The ledger entry and the prompt that would be sent today are not identical for those six. That is
the price of keying on members, and it is the behaviour that makes level-by-level naming reuse the
ledger at all.

**The real fix is upstream:** BTM modules need titles, either from the source or from a generated
one recorded as generated. Until then every count of "pathways with a usable title" is 83 short.

## The RUNS ladder's 89.1% / 91.4% has no recorded space or cutoff

*Logged 2026-10-02. **Open**, and the measurement is not reusable.*

`docs/status/OPEN.md` states "100 trees per run: 89.1% of groupings match at >= 0.70. 200 gives
91.4%", and that line is the only record. The subsample manifest
(`data/ontology/v0.3/subsamples/manifest.json`) records the master seed, the draw scheme and the
disjoint ladder pairs, but carries **no space and no inclusion cutoff**. No committed script
produced the figures and no spec or decision entry holds them.

**Dating places it outside the current setup.** The subsamples were drawn 25 Sep; centred space was
adopted 26 Sep and inclusion 0.50 on 29 Sep. So the ladder was almost certainly run on RAW vectors
at inclusion 0.25 -- neither parameter of the build it is now being used to justify.

**Consequence.** "RUNS = 200, as the ladder already decided" cannot be relied on as decided. The
10,770 plan re-confirms it from the persisted trees under the current space, cutoff and cap, which
is the only way the number means anything here.

**Same defect as the unrecorded scramble seeds, and the same rule:** a result that licenses a
parameter must record every input needed to reproduce it. A percentage and a tree count are not
inputs. The fix going forward is that the ladder re-run writes its space, cutoff, cap and seeds
beside its result.

## The RUNS pass mark has no quantity attached to it -- WRONG, corrected 2026-10-02

*Logged 2026-10-02. **This entry's premise is false** and it is kept, struck through below, because
the project does not rewrite its own record.*

> **CORRECTION, same day.** The rule DID record its quantity: as defined 25 Sep it is ">= 90% of
> FINAL THEMES matched at Jaccard >= 0.70 between builds from disjoint tree blocks". The 2 Oct
> measurement matched the raw grouping pool instead, which was a **mis-implementation of that rule**,
> not a missing specification. Everything below that reasons from "the quantity was never written
> down" is wrong, including the heading. See `DECISIONS.md`, 2 Oct, "The RUNS rule was always about
> FINAL THEMES". What remains true: the 2 Oct figures do not bear on RUNS, and the correct
> measurement has not been run.
>
> The open debt is now narrower and different: **the frozen 1,850 scores 86.9% forward and 85.9%
> backward on the rule's own statistic** (`scripts/theme_match.py`), so it misses the 90% mark by 3
> to 4 points, and the rule does not say which direction the mark applies to.

*The original entry follows, unaltered:*

The ladder's pass mark -- 90% of groupings matching at Jaccard >= 0.70 -- was carried forward as a
declared threshold, but **what it is 90% *of* was never written down**. Re-measured under the current
setup it fails at both scales, and the frozen 1,850 fails it worse than the 10,770 (54.8% and 58.2%
against 61.0%). The diagnostic shows why: over half the raw grouping pool is a cluster one subsample
produced and no other run reproduced, and the pool is what the share is taken over.

So the threshold and the quantity were specified independently of each other, and the pair is
incoherent: no build this project has ever shipped would pass it.

**What the fix must not be.** Reading a passing number off the post-hoc support breakdown. "95.9% at
or above m = 0.33" is the right shape of answer, but choosing the band after seeing which band passes
is the defect `amendment-2026-09-24b` withdrew and the same one behind the withdrawn straddler claim.

**What it has to be.** A declared statement of what the ladder measures -- which set of groupings,
after which gate -- and a pass mark set against that set, both written before the measurement runs.
Then re-measure. `scripts/cut_trees.py`, `scripts/ladder_control_1850.py` and
`scripts/ladder_diagnostic.py` hold the current numbers; `docs/status/2026-10-02-runs-ladder.md` is
the write-up.

**Same defect, third instance:** the unrecorded scramble seeds, the unrecorded ladder space and
cutoff, and now an unrecorded ladder population. A result that licenses a parameter must record
every input needed to reproduce it -- and "every input" includes what was counted.

## Two 1,850 freeze figures are not reproducible: straddlers, and GO BP's shape

*Logged 2026-10-02. **Open.** Neither blocks the 10,770 build; both block a like-for-like
comparison with the frozen 1,850.*

`scripts/freeze_table.py` now computes the freeze table from a build directory, and reproduces
`FROZEN.md` exactly on nine figures: themes 800, roots 61 (7.6%), multi-parent 176 (22.0%), max
depth 12, median theme size 8, largest theme 819, largest root 64, and all four placement counts
(1,831 / 19 / 106 / 125). Two do not reproduce.

**1. Straddlers.** `FROZEN.md` records **682**; the committed definition -- a pathway in two or more
themes neither of which contains the other, over every exported member row -- counts **1,239** on the
same directory. Variants tried and rejected: homes restricted by inclusion (1,223 at >= 0.5, 971 at
>= 0.75, 656 at >= 1.0), homes restricted to leaves (188), to non-roots (1,045), and pathways under
two or more distinct roots (388). **None is 682.** DAG ancestry and member-set containment agree
exactly on this build, so the DAG is not the problem.

**2. GO BP's shape, in test 2.** `FROZEN.md` records GO BP at **20% roots and 31% multi-parent**;
computed over every non-obsolete BP term in `go-basic.obo` it is **0.0% and 50.8%**, and over the
graph induced on our own GO members it is 60.3% and 9.6%. GO's **depth of 16 does reproduce**, and so
do all three Reactome figures (1.0% roots, depth 11, 1.2% multi-parent against the recorded 1%, 11,
1%). So the GO roots and multi-parent figures come from a third computation that is not recorded.

**Consequence, and why it is not papered over.** The 1,850's test 2 concluded "inside the curated
range on all three". With GO roots at 20% our 7.6% is inside 1-20%; at 0.0% it is outside. **The
verdict turns entirely on an unreproducible number, so `freeze_table.py` prints the figures and
withholds the verdict** rather than inheriting a conclusion it cannot derive. The straddler count is
reported under its stated definition with the 682 discrepancy named.

**Same defect, again:** a figure that licenses a claim must record the computation that produced it.
Both numbers were computed ad hoc with no committed script. The fix going forward is that
`freeze_table.py` is the only thing that produces a freeze table.

## Tests 3 and 4 have pass marks that a degenerate baseline wins

*Logged 2026-10-03. **Open**, and it blocks two gates on the frozen 10,770.*

Both marks are stated over **raw recovery**. Test 3: "THEMA's recovery exceeds every gene baseline
and the random null". Test 4: "not beaten by the gene baselines in the (0,0) band". Applied exactly
as written, **both fail**, and the baseline that beats THEMA is `kappa@25`, whose **largest cluster
holds 97.3% of the universe**.

That arm is one blob. Its own chance rate is 94-100% and its lift is 1.0x, against THEMA's 1.3-4.2x.
**A mark on raw recovery is won by putting everything in one cluster**, so applying it literally
produces a failure that means nothing. Against the non-degenerate arms THEMA is clearly ahead -- GO
siblings at zero gene overlap, THEMA 59.2% against `overlap@100`'s 30.6%, whose largest cluster is
15.7%.

`compare_baselines.py` already anticipated this in a code comment: "The chance rate travels with the
winner. Without it 'D classic 100%' reads as a strong baseline when it is a collapsed blob whose own
null is also near 100%." The mark did not inherit that caution.

**What the fix must not be:** quietly switching the comparison to lift because lift is the statistic
that passes. That is choosing the measure after seeing the result.

**What it has to be:** a declared statement of either (a) the mark on lift, or (b) a non-degeneracy
constraint a baseline must satisfy to count -- `largest_share` is the committed measure and is now
printed for every arm -- written before the tests are re-adjudicated. `scripts/validate_dag.py`
holds the numbers either way.

## Test 3's headline cell holds 8 pairs

*Logged 2026-10-03. **Open.***

The validation plan calls the zero-gene / near-zero-lexical cell **"the headline number"** and makes
it half of test 3's pass condition. On the frozen 10,770 that cell contains **8 pairs**. The frozen
build recovers 75.0% of them and every lexical arm recovers 0.0%, which is the right direction, but
**n = 8 cannot carry a gate** whatever it shows: a single pair moves it by 12.5 points.

The plan predicted "~90 name-controlled pairs at full scale" and that is roughly what exists -- 680
`reactome2go` pairs in the universe, 40 of them at exactly zero gene overlap. The cell is small
because it then takes the **bottom quintile of curated-text overlap** of those 40. The quintile was
declared before the run and is not the problem; the problem is that the plan asked for a conjunction
of two rare conditions and did not check how many pairs survive both.

**Options, all Aviyah's:** widen the lexical band (changes a declared cell), report the cell without
a gate, or move the gate to the full (0,0) band of 40 pairs where THEMA scores 80.0% against a 21.4%
null. **Nothing was changed; the cell is reported at n = 8 with the caveat attached.**
