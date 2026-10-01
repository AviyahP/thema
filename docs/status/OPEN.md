# Open state — THEMA

*The single place that says what is running, what is waiting on Aviyah, and what is decided.
Updated by Claude Code whenever something moves. If this disagrees with a chat message, this wins.*

Last updated: 2026-09-29

---

## RUNNING

Nothing. No process, no API call, nothing scheduled.

## WAITING ON AVIYAH

1. **The `name-v5` prompts.** Rendered to `docs/spec/naming-prompt-v5-rendered.md`: the system
   prompt, one real leaf message, one real internal message and one collision re-ask, all from
   `recurrent_dag_c50`. **Nothing runs until these are approved** — `CLAUDE.md` requires the text
   before the spend.
2. **The level-0 price, $2.29.** 287 leaves, `--max-level 0`. Approving the prompts and approving
   the price are separate gates.
3. **Which floors a future cutoff uses**, if the cutoff ever changes again. Settled for 0.50.

## CURRENT BUILD — `v0.2.2-subset-1850-c50` (1,850 SUBSET, not the ontology)

`data/ontology/v0.2/recurrent_dag_c50`, frozen 29 Sep 2026, `FROZEN.md` in the directory.
**Supersedes `recurrent_dag_consensus_centred`**, which used inclusion 0.25.

**800 themes, 61 roots, 1,054 → 905 edges, 22% multi-parent, depth 12, 682 straddlers.**
Centred-and-renormalised MedCPT vectors, 100 runs, theta 0.70, **membership at inclusion ≥ 0.50**,
declared m 0.33 with per-size floors **solved at 0.50** — 0.880 / 0.930 / 0.600 / 0.400 at sizes
3/4/5/6, from 40 calibration and 20 held-out scrambles, **held-out FDR 0.00333**.

**Placement, three ways, because one number hides the cost:** 19 unplaced strictly,
**106 root-only** (in no theme that has a parent), **125 effectively unplaced** — 6.8% of the
universe gains nothing usable. All three are in the manifest and in `FROZEN.md`.

**Test 9:** mean best-match Jaccard 0.862, median 0.909, 53.2% of themes matching at ≥ 0.9. "Frozen"
applies to the theme set and its nesting, not to exact member lists.

**The build is UNNAMED.** The 861 `name-v3` names refer to themes that no longer exist.

## NAMING — plan, level by level

`name-v5` is **one prompt**: the same system prompt for leaves, internal nodes and collision
re-asks. The user message is data with a single line of instruction — title and description only,
no source tags, no inclusion values, no identifiers, no worked examples. A collision is the same
message with one line appended.

`--max-level N` names up to level N and **skips** everything above it. A skip is not a refusal: an
internal node whose children are unnamed is left alone rather than recorded as unnameable, and
because a request is keyed by its members and its children's names, a later run at a higher level
reuses every completion already in the ledger.

| step | scope | price | state |
|---|---|---|---|
| level 0 | 287 leaves | **$2.29** | priced, awaiting approval |
| levels 1+ | 513 internal | ~$2.34 more | after level 0 is read |

## THE LADDER — PAUSED

**100 trees per run: 89.1% of groupings match at ≥ 0.70. 200 gives 91.4%.** RUNS stays at 100 for
the subset builds. The ladder is paused and nothing resumes it without a decision.

## COHESION — measured, no threshold added

`DECISIONS.md`, 29 Sep, reproduced by `scripts/cohesion_reference.py`. Themes are tighter than
random kNN balls of the same size at **every** stratum, so the geometry finds nothing to remove; a
cut at 0.20 would delete the top of the tree and leave the incoherent leaves untouched. What judges
"too unrelated" instead is the namer's `nameable: false`, shown as an unnamed umbrella and never
hidden. **Aviyah's reservation is recorded**: she does not like an LLM verdict acting as the
structural filter, and it is accepted only because no measured geometric rule does the job.

**Follow-up, declared before the leaf names exist:** after level-0 naming, compare the cohesion of
refused leaves against named ones. If refusals concentrate in the low-cohesion tail, a size-aware
floor calibrated from those verdicts may be declared and applied to the 10,770. If they do not, the
idea is closed.

## SCALE — the 10,770 has never been built

Embedded (`data/ontology/v0.3/`, MedCPT, nothing truncated) and priced. The calibration it needs is
**10 calibration + 5 held-out scrambles**, declared in `amendment-2026-09-24c` and now measured: the
worst stratum projects to 7, so 10 clears it. That projection is an extrapolation and is unverified
at scale.

## VALIDATION — gates 3 to 6 unrun

`reactome2go` recovery, sibling recovery, the enrichment task and blind human rating. Gates 3 and 4
are the ones that would show the hierarchy recovers curated structure. **Nothing about the ontology
itself has been validated**; what is measured is the embedding space.

Tests 1 and 2 (name sorting, name DAG) are priced at $9.80 on the old names, with both prompts'
defects named and replacements drafted in `docs/spec/naming-tests-1-2-prompts.md`. Both original
runs used unreviewed prompts and **are not to be cited**.

## SPEND

$232.52 to date. $0.00 since the `name-v3` run on 27 Sep.
