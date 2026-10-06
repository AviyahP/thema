# Where we are — 6 Oct 2026

One page, plain language, covering every result, decision and open question since 3 Oct. Every
number names the file it came from.

## The one-sentence version

THEMA v0.3 is frozen and honest about its shortfalls; HiDeF was compared under a rule declared
first and **THEMA stayed, but not cleanly**; the reason turned out to be **grain**, not quality; a
search for a better clustering engine inside THEMA's framework found one (**arm B, Leiden**) that
fixes the middle without losing much; and that result is good enough that Aviyah has **paused the
engine search** to ask the prior question properly — does THEMA's framework beat HiDeF at all, under
the field's own standard of recall against curated and planted sets.

## What was decided, in order

| when | decision | where |
|---|---|---|
| **3 Oct** | **RUNS = 200. The declared 90% stability mark is NOT met and is NOT changed** — 85.5% at 100 runs, 87.9% at 200. Frozen with the shortfall stated. | `DECISIONS.md` 3 Oct |
| 3 Oct | Gene baselines held to THEMA's own size cap (post-hoc, labelled) | `DECISIONS.md` 3 Oct |
| 3 Oct | The graded specificity measure, declared before computation | `DECISIONS.md` 3 Oct |
| **4 Oct** | The HiDeF comparison rule, declared before any HiDeF build existed | `DECISIONS.md` 4 Oct |
| **5 Oct** | **THE HIDEF VERDICT: THEMA stays.** HiDeF and CliXO are baselines; CliXO is a baseline in name only because it was never obtainable. | `DECISIONS.md` 5 Oct |
| 5 Oct | Compute line amended: THEMA is **~4× HiDeF, not 50×**, after the Part B speed-up. 50× kept as historical. | `DECISIONS.md` 5 Oct |
| **6 Oct** | The engine search §0, then **four amendments**, every one before any arm had a score | `DECISIONS.md` 6 Oct |
| **6 Oct** | **Engine search PAUSED**; the A/B/HiDeF protocol declared and runs first | `docs/spec/eval-protocol-2026-10.md` |

## The results, with their numbers

### THEMA v0.3, as frozen

6,244 themes, 203 roots, 141 effectively unplaced (1.31%), held-out FDR **0.00285** overall and
**0.0147** worst stratum, stability **85.5%** between run halves.
→ `data/ontology/v0.3/recurrent_dag_10770/manifest.json`, `docs/status/2026-10-06-engines.md`

### HiDeF, compared under the 4 Oct rule

THEMA significantly better on both Reactome specificity cells; HiDeF missed the zero-gene recovery
tolerance on Reactome by **9.9 points**. HiDeF rejected the scrambled null completely (zero
communities on both held-out seeds), so **noise rejection is not the distinguishing property THEMA
was expected to have**.
→ `docs/status/2026-10-04-hidef-comparison.md`, `DECISIONS.md` 5 Oct

### What 5 Oct added, and it mostly complicated the verdict

- **The pair bootstrap understated uncertainty ~7×.** The verdict survives the correct cluster
  bootstrap — still 2 of 4 cells — but **Reactome pooled clears zero by 0.0001**.
- **At maxres 50 under the cluster bootstrap, HiDeF would mechanically meet the rule's conditions.**
  Two departures from the declaration at once, so not a verdict; the tooling now refuses to print one.
- **The contest is about GRAIN.** THEMA wins themes of 3–50 members on both hierarchies, HiDeF wins
  51–500 on both, and the sign flips in the same place every time. THEMA has **141** themes of
  51–500 (2.3%); HiDeF has **249** (52.8%).
- **The GO gap is entirely the thin middle.** Of three hypotheses declared before looking, **H1 was
  refuted by its own predicted strata**; **H2 over-explains** — removing the 2,253 pairs HiDeF places
  in a 51–500 theme flips GO from **+0.0081 to −0.0115**.
- **The middle is explained mechanistically.** The support gate removes **99.7%** of 51–500
  candidates, and **80.6%** of their failed checks are *missing members* against 30.3% for small
  groupings: mid-size groups scatter across the other run's clusters.
- **Hashing is not feasible:** one global fingerprint at Jaccard ≥ 0.70 recovers **36.6%** of true
  copy pairs; copies sit at median **0.633** against the **0.667** that 80% sampling alone predicts.
- **A full build went from 2.82 h to 6.0 min cold (28×), byte-identically.**

→ `docs/status/2026-10-05-speed-and-evaluation.md`

### The engine search, as far as it got

| arm | engine | themes | unplaced | held-out FDR | stability | gates |
|---|---|---|---|---|---|---|
| **A** | Ward (v0.3) | 6,244 | 1.31% | 0.00285 | **85.5%** | pass |
| **B** | Leiden, 10-rung ladder | **3,462** | **0%** | **0.00189** | **94.5%** | pass |
| **B2** | B + persistence τ = 0.75 | 706 | **37.1%** | 0.00079 | — | **FAILS G3** |
| C, G, H | pooled / bisect / infomap | — | — | — | — | **paused** |

→ `data/ontology/v0.3x_engines/*/manifest.json`, `docs/status/2026-10-06-engines.md`

**Arm B fixes the middle.** Band-restricted specificity AUROC, paired cluster bootstrap: B wins
**all eight** mid- and coarse-band cells by **+0.025 to +0.154**, every CI clear of zero. Recovery
moves with it — at 201–500 on Reactome, B places **29.9%** of zero-overlap sibling pairs in a shared
theme against A's **8.1%**. The price is **3–10 on Reactome**, where A is better by 0.034 and 0.062
beyond the margin, because B has **no floor reaching FDR ≤ 0.01 in the 3- and 4-member strata** and
cannot build a theme that small. At **11–50 the two are equivalent everywhere**.
→ `docs/status/2026-10-06-engines.md` (PREVIEW)

**And on HiDeF's own primary metric, arm B occupies the position HiDeF failed to reach.** Overall
4-cell AUROC, all theme sizes: B is **never significantly worse than A** (Reactome intervals cross
zero at +0.0004 and +0.0069) where **HiDeF is** (−0.0030, −0.0001), and B is significantly better on
GO pooled. On reactome2go at zero gene overlap, B recovers **85.0% at lift 4.05** against A's
80.0%/3.75 and HiDeF's 77.5%/2.43 — though that band is only 40 pairs.
→ `docs/status/2026-10-06-engines.md` (PREVIEW 2)

**B2 answers its own question emphatically.** Persistence-within-a-run stacked on
recurrence-across-runs is far too restrictive: 759 families through the gate, no stratum below 7
members admitted, **37% of the universe unplaced**. Interpretation-guide case (b), confirmed.

## What was proved rather than asserted

- **The engine adapter is a true generalisation, not a parallel path.** Fed Ward's own candidates on
  four seeds it reproduces `_one_run`'s `Run` **field for field**, and the Ward path now goes through
  it — so the regression means something. The rebuilt frozen build is **byte-identical by sha256 on
  all four TSVs**. → `tests/ontology/test_engine_adapter.py`, `docs/status/2026-10-06-engines.md`
- **Candidate generation across processes cannot change a side**, asserted byte-identical rather than
  argued, including that results come back in label order. → `tests/test_engine_runs.py`
- **Containment is not recurrence.** A 10-member grouping appearing in four other runs only inside a
  50-member community gets support **1/5**; a near-copy at Jaccard 0.818 gets **1.0**.
- **The decision rule itself is tested** on hand-built curves: dominance needs both a significant win
  and no significant loss; an ineligible arm cannot win even when best everywhere.
  → `tests/test_engine_scores.py`

## What went wrong, and what it cost

| fault | consequence | fixed |
|---|---|---|
| **Orphaned worker pools** — killing a driver by PID left its 6 workers alive; three cycles left 24 orphans at ~1.5 GB each | **exhausted a 36 GB machine, the Mac slept, the run stalled ~19:35Z** and a side wedged at 0.0% CPU | `scripts/stop_engine_jobs.sh` kills workers too and proves by PID |
| **Floors written to the Ward directory** | tried to overwrite the frozen build's calibration record — the same file that lost `overall_fdr 0.00285` once on 5 Oct | the no-overwrite guard refused; every `cut_key` is now engine-aware |
| **`cut_trees.py` and `engines.py` not in the provenance fingerprint** | a ladder change altered every Leiden side's bytes while the hashed file was untouched | both now hashed; `engines.py` and the ladder for non-Ward engines only |
| **G1 read from the manifest; G2 scraped stdout** | every FDR came back `nan`; arm A's stability reported as **0.900** when it is **0.855** | both read JSON |
| **`fork` for the worker pool** | children died after BLAS threads existed; a script survived by luck, pytest did not | `spawn` |

**My PID verification was incomplete rather than wrong**: I checked the processes I started and not
the ones they started. A check that only looks where it expects to find something is not a check.

## Open questions

1. **Does THEMA's framework beat HiDeF at all?** The 6 Oct protocol asks this under the field's
   standard, and **clause 3 can conclude that HiDeF becomes THEMA's engine**. No prior rule had an
   outcome that replaced the method's core. → `docs/spec/eval-protocol-2026-10.md`
2. **Arm C costs ~5.9 h more and under the engine rule it consumes G and H.** ~5.5 h remain under the
   12 h cap; G + H together need only ~3.6 h and would fit if C were dropped. Reordering after seeing
   costs is what §0 forbids, so nothing was changed. **Aviyah's call.**
3. **`TOL = 0.15` is inert in the frozen build** — used only in the `theta is None` branch — yet
   recorded in the manifest and `FROZEN.md` as though it governed something.
4. **Reactome pooled clears zero by 0.0001.** The 5 Oct verdict should not rest on one cell that
   close.
5. **Ancestor-pair F1 still does not exist**, specified in the v0.2 plan §14 item 3. It is the metric
   the ontology-learning field uses most. → `docs/spec/related-work.md`
6. **Eight ambiguities in the new protocol**, written down and deliberately not resolved.
   → `docs/status/2026-10-06-engines.md` (FEASIBILITY NOTES)
7. **Co-expression for E4 has no qualifying resource**: ARCHS4 is 7.49 GB against a 5 GB limit.
8. **The engine search never measured F (average linkage) or D (Paris)** — dropped on measured cost
   before any result existed.

---

# COMMIT BLOCKS

I ran no git commands. Every path is named explicitly — no wildcards — because `.gitignore:46`
re-includes `data/ontology/v*/*/*.tsv` and a wildcard would sweep in the completion caches, the
superseded side sets and the HiDeF builds.

## Size check, and what goes to .gitignore instead of a commit

**Nothing proposed for commit exceeds 50 MB.** Largest: `v0.3x_engines/leiden/members.tsv` at
10.35 MB. The 135 proposed data paths total **43.1 MB**.

These are caches and are **excluded from the commits**, per the rule that any cache goes to
`.gitignore`:

| path | size on disk | why |
|---|---|---|
| `…/completions/cap3125_inc050_leiden/` | **598 MB** | per-run completion cache, 18 sides, regenerable from the persisted trees |
| `…/completions/cap3125_inc050_pooled/` | **431 MB** | same, 5 sides |
| `…/completions/cap3125_inc050_leiden_persistent/` | **8.4 MB** | same, 18 sides |
| `…/completions/cap3125_inc050/` | 1.3 GB | arm A's own cache (`*.npz` already ignored by `.gitignore:73`) |
| `data/ontology/v0.3/regression_adapter_10770/` | 7.7 MB | **byte-identical duplicate of the frozen build** — all four TSVs match it by sha256, so committing it adds a second copy of a build already in the repository. The proof is in the report. |
| `data/raw/9606.protein.*.gz` | 103 MB | STRING v12; already ignored by `.gitignore:25` (`data/raw/`) |

The `.npz` files inside those caches are already ignored (`.gitignore:73`), but their
`*.provenance.json` and `*.stages.json` sidecars are **not**, and git would add 96 of them. Block 0
below ignores the engine caches wholesale while **re-including `floors_*.json`**, which are
calibration records rather than caches — the same distinction `.gitignore:68-73` already draws for
the files beside the trees.

**One question I did not resolve.** The existing `.gitignore:77` ignores
`data/ontology/v*/recurrent_dag_10770_r*/` — the ladder half-builds — as regenerable intermediates.
Arm B's and B2's half-builds (`leiden_r1-100` and the other three, 22.1 MB together) are the same
kind of artefact, but they are also the **only on-disk evidence for the G2 stability figures**
(94.5% for B), since that number is computed from them by `theme_match.py` and is not stored in any
manifest. **I propose committing them** and flag the inconsistency with the precedent rather than
deciding it silently.

## 0 — .gitignore

```sh
cat >> .gitignore <<'EOF'

# Engine-search completion caches, 6 Oct. Same rule as the Ward caches above: a side is a
# deterministic function of the persisted trees, the engine and the recorded ladder, and its
# provenance mark records which code wrote it. 598 MB for leiden, 431 MB for pooled.
# The floors files are re-included: a solved floor is a calibration record, not a cache, and the
# one beside the trees is already treated that way.
data/ontology/v*/trees/**/completions/cap*_leiden/
data/ontology/v*/trees/**/completions/cap*_leiden_persistent/
data/ontology/v*/trees/**/completions/cap*_pooled/
data/ontology/v*/trees/**/completions/cap*_bisect/
data/ontology/v*/trees/**/completions/cap*_infomap/
!data/ontology/v*/trees/**/completions/cap*/floors_*.json

# Verification builds that are byte-identical to a build already committed. regression_adapter_10770
# matches recurrent_dag_10770 on all four TSVs by sha256; keeping it would commit a second copy.
data/ontology/v*/regression_adapter_10770/
EOF

git add .gitignore
git commit -m "Ignore engine completion caches, keep the floors records"
```

## a — the adapter and the regression

```sh
git add src/thema/ontology/recurrent.py scripts/cut_trees.py tests/ontology/test_engine_adapter.py

git commit -m "Engine adapter: a run may supply nested clusters or a flat partition" -m "The pipeline was already engine-agnostic, which I did not expect. Three fields of a
Run look tree-shaped and only one is read by matching: chain_indptr with chain_idx
is an INVERTED INDEX from pathway to the candidates containing it, which the Ward
path happens to build by climbing parent, while parent and leaf_cluster are written
and never read. And the selection rule in _score_matrix -- the run candidate with
the greatest overlap with the grouping shared members, ties toward the smaller -- is
already the rule a flat partition needs; it was written for the two-sided change on
2 Oct.

So supporting a flat partition needed ONE new constructor, run_from_candidates, that
builds the inverted index directly, and no change to matching, completion, consensus
or the gate.

cut_trees.load_run now goes through that same constructor, so the Ward path and every
new engine build their candidates with one piece of code. That is what makes the
regression a real test rather than a formality: if Ward kept a private path,
byte-identity would prove nothing.

REGRESSION PASSES, COLD. The real side was re-cut from scratch, not served from
cache, because editing recurrent.py changed its provenance fingerprint and the guard
refused the cached side. The completion material is identical array by array
including dtypes, and all four output TSVs match the frozen build by sha256: nodes
571bfa717e658052, members be8ec31d384086c9, edges d793ab63cf22bc7a, unplaced
83745ba1521ba11f. 6,244 nodes, 203 roots, 141 effectively unplaced, every figure
matching the frozen manifest. 368.6 s, peak 8.22 GB.

Five tests, including the strong one: fed Ward own candidates and nested structure on
four seeds, run_from_candidates reproduces the Run that _one_run builds FIELD FOR
FIELD.

Two more tests pin a rule that amendment 4 restates rather than changes: containment
in a larger community is NOT recurrence. A 10-member grouping appearing in four other
runs only inside a 50-member community gets support 1/5, because the two-sided
Jaccard is 0.2; a near copy at Jaccard 0.818 gets 1.0. Without that, a run proposing
one huge community would find every grouping it contained and a coarse engine would
score as perfectly recurrent."
```

## b — the engines, the driver and the evaluation code

```sh
git add src/thema/ontology/engines.py tests/ontology/test_engines.py pyproject.toml uv.lock

git commit -m "Six clustering engines behind one interface, confined to one module" -m "Leiden on a kNN-15 cosine graph with a 10-rung resolution ladder per run (arm B), the
same filtered to communities that persist across an adjacent rung at the HiDeF tau of
0.75 (B2), Ward unioned with B candidates (C), bisecting spherical k-means (G),
average linkage (F), hierarchical Infomap (H), and Paris (D). Arm E, HDBSCAN on a
UMAP embedding, is DROPPED and its two functions are kept with the arm marked
dropped, so the dropped arm stays legible rather than vanishing.

Every library stays inside this one module with a test per library, the same
containment llm.py gives the Anthropic SDK and embed.py gives the encoder. igraph has
one named exception: build_hidef.py runs HiDeF, a third-party BASELINE implemented
against its own graph type, and it must not import from engines.py or the baseline
would stop being independent of the thing it is a baseline for. A further test
asserts engines.py imports nothing heavy at module level, so a Ward-only build --
still the frozen build -- pays nothing for the alternatives existing.

The resolution ladder was set THREE times, every time before any arm had a score and
every time by a measurement of the setup rather than of an outcome. Declared
0.001 to 100; the top widened to 300 because at 100 the median community is 12
members against a required 5 or fewer; then the bottom raised to 0.0669433, the
largest resolution at which the largest community still reaches the 3,125 cap,
because four of ten rungs below it gave one community of the whole draw and the cap
removed it. Spacing between useful rungs fell from 4.060x to 2.545x and usable rungs
rose from 6 to 9 of 10. DECISIONS.md carries all three with the number that forced
each."

git add scripts/build_10770.py scripts/engine_probe.py scripts/ladder_span_check.py scripts/engine_workers.sh scripts/run_engine_arm.sh scripts/run_all_engine_arms.sh scripts/run_engine_evaluation.sh scripts/stop_engine_jobs.sh tests/test_engine_runs.py

git commit -m "Build any engine through the v0.3 pipeline, cache keyed per engine" -m "--engine swaps what each run proposes and changes nothing else: same samples, same
theta, same completion, same consensus, same cap, same floors procedure. The SAMPLE
is read from the persisted Ward tree rather than regenerated, which is the strongest
form of the same 80% samples -- there is no second code path that could disagree.
Completions are keyed per engine so one engine sides can never be served to another,
and engine arms are written to v0.3x_engines beside v0.3 rather than inside it.

Candidate generation runs on a process pool because Leiden holds the GIL: threads
measured 1.08x on four of them, processes 3.0x on six. SPAWN, not fork, and that was
learned twice -- fork is faster and shares the matrix by copy-on-write, but forking a
parent that has already started BLAS threads, which centring the matrix does, kills
the child on macOS. A standalone script survived it by luck; the same code under
pytest raised BrokenProcessPool immediately. Three tests assert serial and parallel
generation are byte-identical, including that the list comes back in label order
rather than completion order.

TWO GAPS IN THE PROVENANCE GUARD, both found by this work. cut_trees.py is where a
persisted tree becomes a candidate set, and engines.py decides what a non-Ward run
proposes, so both are output-affecting exactly as recurrent.py is, and NEITHER was
hashed. The ladder widening is the proof: it changed every Leiden side bytes while
leaving the one hashed file untouched. Both are now hashed, engines.py and the ladder
only for non-Ward engines, since neither can affect a Ward side and a global hash
would needlessly refuse the frozen build cache. Adding cut_trees.py invalidates every
side cached before today, which is the correct consequence of not having been able to
prove what wrote them.

A THIRD BUG, caught by the no-overwrite convention: solved floors were written to the
WARD completions directory, which is the frozen build calibration record and the same
file that lost overall_fdr 0.00285 once on 5 Oct. The guard refused, the record is
intact and verified, and every cut_key call is now engine-aware. The manifest records
floors_file explicitly so no reader has to reconstruct that path.

stop_engine_jobs.sh exists because of a real failure. Killing a driver by PID left
its six spawned workers alive, reparented to init; three stop cycles accumulated 24
orphans at about 1.5 GB each, which exhausted a 36 GB machine, put the Mac to sleep
and wedged the running pool at 0.0% CPU. The script kills workers too and proves by
PID that nothing remains. My PID verification had been incomplete rather than wrong:
I checked the processes I started and not the ones they started.

engine_workers.sh sizes the pool from genuinely available memory, so a resume on a
warm machine cannot repeat that stall. It cannot change a side bytes, which
tests/test_engine_runs.py asserts for any worker count."

git add scripts/engine_scores.py scripts/engine_gates.py scripts/string_coherence.py scripts/theta_diagnostic.py scripts/engine_report_tables.py scripts/preview_overall.py tests/test_engine_scores.py

git commit -m "The 16 scores, the four gates, and the engine rule applied as declared" -m "The bootstrap is PAIRED and that is not a detail: the resampled curated parents are
drawn once per cell and every arm is scored on the same draw, so a difference between
two arms is a difference on identical data. One consequence is that every pairwise CI
the dominance rule needs comes from subtracting two stored curves, so adding an arm
costs one more curve rather than one more per existing arm.

Nine tests on the rule itself, on hand-built curves where the answer is known:
dominance needs BOTH a significant win and no significant loss; a win inside the 0.02
margin dominates nothing; max-min scores an arm by its worst cell against the best
ELIGIBLE arm, so an ineligible arm score cannot set the bar; and an ineligible arm
cannot win even when it is best everywhere. One test records a fragility rather than
smoothing it: 0.52 minus 0.50 is 0.020000000000000018 in binary floating point, so a
pair a reader would call exactly 0.02 apart can dominate. No tolerance was added,
because choosing one is a tuning decision and the rule forbids tuning, but a verdict
resting on a gap within a hair of 0.02 should be read as a boundary case and said to
be one.

G4 is STRING v12 at combined score 700 or above, and it earns its place because every
other gate and score is computed from the same embeddings the engines cluster: an
engine that exploited a quirk of the embedding could pass all of them. STRING is
independent evidence. The null draws from STRING-COVERED genes only, because drawing
from all pathway genes would compare a theme against sets containing genes STRING has
never seen, which have no edges by construction, and every theme would look enriched.
Densities are sparse submatrices and the null is memoised per gene-set size; the first
version looped over neighbour lists and was far too slow to run.

Two bugs worth naming because both produced plausible wrong numbers rather than
errors. G1 was read from the manifest, which records only heldout_confirmed true and
the FDR in prose, so every arm FDR came back nan; it now reads the floors file,
located by GLOB because the manifest space field holds a description,
centred-renormalised, where the directory is named for the flag, centred. And G2
scraped the printed line from theme_match, which puts the 90% PASS MARK in the same
sentence as the result, reporting arm A stability as 0.900 when it is 0.855; it now
reads the JSON.

theta_diagnostic.py is LABELLED NOT DECISIVE and reports an UPPER BOUND, stated in
its own docstring: the floors are not re-solved at the loosened thetas, and a lower
theta raises support on the scrambled null too, so the real floors would be higher
and fewer candidates would pass.

preview_overall.py is report-only and computes the overall four-cell AUROC and the
reactome2go recovery and lift, neither of which decides anything under the engine
rule."
```

## c — the engine rule, its amendments, and the docs

```sh
git add DECISIONS.md docs/status/2026-10-06-engines.md docs/spec/related-work.md docs/status/2026-10-06-where-we-are.md

git commit -m "Engine search: the rule, four amendments, and what the arms measured" -m "The engine rule fixes the arms, the gates, the 16 scores, the dominance and max-min
rule and the one-shot stop rule, and it was written before a single engine ran. Four
amendments follow and EVERY ONE arrived before any arm had a floor, an ontology or a
score: drop HDBSCAN for resample leakage; give arm B the whole 10-rung ladder per
run; add B2, G and H; add STRING coherence as G4; restore H on the measured budget;
and set the ladder range twice over by measurement. The interpretation guide is
recorded as item 9 and labelled a reading guide, not a decision rule.

ARM B BUILT: 3,462 themes, 0 unplaced against arm A 141, held-out FDR 0.00189, worst
stratum 0.00969, stability 94.5% against arm A 85.5%. Strata 3-3 and 4-4 DROPPED, no
floor meeting FDR 0.01 in them, so arm B produces no theme of three or four members
at all. Reported, not fixed.

ARM B2 BUILT AND FAILS G3: 706 themes and 37.1% of the universe effectively unplaced
against a 5% limit, with strata 3-3 through 6-6 all dropped and 759 families through
the gate. Persistence within a run stacked on recurrence across runs is far too
restrictive. That is the declared answer to whether the two filters do the same job
twice: they do not, recurrence alone is the useful one.

PREVIEW, report only: arm B wins all eight mid and coarse band cells by 0.025 to
0.154 with every CI clear of zero, and recovery moves with it -- at 201 to 500 on
Reactome it places 29.9% of zero-overlap sibling pairs in a shared theme against arm
A 8.1%. The price is 3 to 10 on Reactome, where A is better beyond the margin. At 11
to 50 the two are equivalent everywhere. PREVIEW 2, also report only: on the overall
four-cell AUROC arm B is never significantly worse than A where HiDeF is, and on
reactome2go at zero gene overlap B recovers 85.0% at lift 4.05 against A 80.0% and
HiDeF 77.5%.

THE RUN IS PAUSED at arms C, G and H, with 5 of 18 sides cut for C and none for G or
H, and the resume is DEFERRED until the A vs B vs HiDeF protocol decides.

Three things recorded against myself. My own clarification 2 drew a distinction
between arms that does not exist, since the 3,125 cap is smaller than the Ward
half-draw rule at 4,308, so every arm is governed by the same two limits; it is left
standing with a note because it was written before I checked. My reading of drop from
the end dropped arm H, the cheapest arm measured and the one most focused on the
mid-size band, because a kept set had to be a prefix; I reported that and followed the
rule anyway, and Aviyah then authorised the non-prefix set. And the budget was revised
UPWARD to about 12.2 h against a 12 h cap once the final ladder sides were measured,
then arm C measured at 25 minutes a side rather than 11, which under the declared
order consumes G and H; flagged rather than silently absorbed.

related-work.md gains the field standard for evaluating data-driven ontologies: CliXO
label-permuted nulls with per-size-bin FDR, HiDeF F1 at Jaccard above 0.5 with LFR
planted benchmarks, NeXO and MuSIC external validation of novel terms, and the
ontology-learning taxonomic and ancestor-pair measures. It also records that THEMA has
never run a planted benchmark and that ancestor-pair F1, specified in the v0.2 plan,
still does not exist."
```

## d — the new protocol, as its own commit so its timestamp precedes any result

```sh
git add docs/spec/eval-protocol-2026-10.md

git commit -m "DECLARED BEFORE ANY RESULT: the A vs B vs HiDeF evaluation protocol" -m "Pasted verbatim from Aviyah brief and not edited. Nothing in test F or E1 to E4 has
been implemented or computed for any arm; this commit exists so the declaration has a
timestamp that precedes every number it will later be judged by.

It states its own starting knowledge: previews 1 and 2 of the engine run, shape,
stability and gates for A, B and B2, and the floors in each manifest already existed
and were seen. Arms C, G and H stay paused and untouched and resume afterwards under
the engine rule, which this protocol does not amend.

Three things it does that no THEMA evaluation has done before. It CAN CONCLUDE
AGAINST THEMA OWN ENGINE: clause 3 says that if neither A nor B beats HiDeF then
HiDeF becomes the engine and THEMA contribution is the descriptions, embeddings,
naming and statistics layer. It gives HiDeF a tuning budget THEMA never gets, a
27-setting grid selected on a held-back tuning half, and then an oracle line on top
chosen on the test half, while A and B are each one fixed configuration. And it adds
planted ground truth, where recall is measured against sets true by construction,
with the limitation declared in advance that Gaussian geometry may favour Ward, which
is why E2 is one of two decisive tests and never the only one.

The specificity AUROC that every number reported on 4, 5 and 6 Oct rests on is
demoted to also reported. Recall against curated and planted sets is what decides,
and that is a different question.

Test F runs first and asks whether the scramble calibration earns its cost, because
its answer sets the floor form every later build uses. Its step 2 is a declared second
read of held-out seeds 4001 to 4005, labelled as such: no threshold is fitted at the
fixed cut, so every seed is valid test data for it, and the cut is declared in the
protocol rather than chosen after seeing the FDR."
```

## e — the build outputs

```sh
git add data/ontology/v0.3x_engines/leiden/nodes.tsv data/ontology/v0.3x_engines/leiden/members.tsv data/ontology/v0.3x_engines/leiden/edges.tsv data/ontology/v0.3x_engines/leiden/unplaced.tsv data/ontology/v0.3x_engines/leiden/manifest.json

git add data/ontology/v0.3x_engines/leiden_persistent/nodes.tsv data/ontology/v0.3x_engines/leiden_persistent/members.tsv data/ontology/v0.3x_engines/leiden_persistent/edges.tsv data/ontology/v0.3x_engines/leiden_persistent/unplaced.tsv data/ontology/v0.3x_engines/leiden_persistent/manifest.json

git add data/ontology/v0.3x_engines/leiden_r1-100/nodes.tsv data/ontology/v0.3x_engines/leiden_r1-100/members.tsv data/ontology/v0.3x_engines/leiden_r1-100/edges.tsv data/ontology/v0.3x_engines/leiden_r1-100/unplaced.tsv data/ontology/v0.3x_engines/leiden_r1-100/manifest.json

git add data/ontology/v0.3x_engines/leiden_r101-200/nodes.tsv data/ontology/v0.3x_engines/leiden_r101-200/members.tsv data/ontology/v0.3x_engines/leiden_r101-200/edges.tsv data/ontology/v0.3x_engines/leiden_r101-200/unplaced.tsv data/ontology/v0.3x_engines/leiden_r101-200/manifest.json

git add data/ontology/v0.3x_engines/leiden_persistent_r1-100/nodes.tsv data/ontology/v0.3x_engines/leiden_persistent_r1-100/members.tsv data/ontology/v0.3x_engines/leiden_persistent_r1-100/edges.tsv data/ontology/v0.3x_engines/leiden_persistent_r1-100/unplaced.tsv data/ontology/v0.3x_engines/leiden_persistent_r1-100/manifest.json

git add data/ontology/v0.3x_engines/leiden_persistent_r101-200/nodes.tsv data/ontology/v0.3x_engines/leiden_persistent_r101-200/members.tsv data/ontology/v0.3x_engines/leiden_persistent_r101-200/edges.tsv data/ontology/v0.3x_engines/leiden_persistent_r101-200/unplaced.tsv data/ontology/v0.3x_engines/leiden_persistent_r101-200/manifest.json

git add data/ontology/v0.3/trees/centred_c54319cdfbbe9eb7/completions/cap3125_inc050_leiden/floors_r1-200_n200.json data/ontology/v0.3/trees/centred_c54319cdfbbe9eb7/completions/cap3125_inc050_leiden_persistent/floors_r1-200_n200.json

git add data/ontology/v0.3/trees/centred_c54319cdfbbe9eb7/completions/cap3125_inc050/real_r00001-00200.provenance.json data/ontology/v0.3/trees/centred_c54319cdfbbe9eb7/completions/cap3125_inc050/real_r00001-00200.stages.json data/ontology/v0.3/trees/centred_c54319cdfbbe9eb7/completions/cap3125_inc050/real_r00001-00200.provenance.preadapter.json data/ontology/v0.3/trees/centred_c54319cdfbbe9eb7/completions/cap3125_inc050/real_r00001-00200.stages.preadapter.json

git commit -m "Arm B and B2 builds, their halves, and their solved floors" -m "Two complete engine arms in the v0.3 schema, so the demo can toggle between them,
plus the four stability half-builds the G2 figures are computed from. The halves are
committed because they are the ONLY on-disk evidence for those figures: 94.5% for arm
B against 85.5% for arm A, computed by theme_match.py from these directories and
stored in no manifest. The ladder half-builds at recurrent_dag_10770_r are ignored as
regenerable intermediates, so this is an inconsistency with that precedent and it is
flagged in the report rather than decided silently.

Each arm solved floors are committed as calibration records. Arm B drops strata 3-3
and 4-4 entirely, which is why it cannot build a theme of three or four members, and
arm B2 drops 3-3 through 6-6. Those files are the record of that.

The arm A real side provenance and stage marks are updated because the side was
re-cut through the adapter for the regression, and the pre-adapter marks are kept
alongside as preadapter copies rather than replaced, so both reads of the same side
remain legible.

The completion caches themselves are NOT committed and are added to .gitignore: 598 MB
for leiden, 431 MB for pooled, 8.4 MB for leiden_persistent, every side regenerable
from the persisted trees, the engine and the recorded ladder, and every side carrying
a provenance mark that refuses reuse by different code. regression_adapter_10770 is
also ignored: all four of its TSVs match the frozen build by sha256, so committing it
would add a second copy of a build already in the repository."
```

## push

```sh
git push
```
