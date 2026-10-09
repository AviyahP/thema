# THEMA baseline 2026-10-09

**Frozen by Aviyah, 9 Oct 2026.** This directory is the reference build. Every later change is built
in a **new** directory and reported as a comparison against this one; if work gets tangled, this is
what we revert to. Nothing in here is ever edited: `CHECKSUMS.sha256` covers every file and
`tests/ontology/test_frozen_baseline.py` fails if any byte moves.

The build is `thema_L_x2`, copied here **exactly as built** -- including the one input we know was
excluded in error. See the caveat under *Universe*.

---

## 1. What it is

| | |
|---|---|
| build | `thema_L_x2`, built 9 Oct 2026 16:36 |
| original location | `data/ontology/v0.4-leaves/thema_L_x2/` |
| method | `v0.4` (see `src/thema/ontology/v04.py`) plus the repair post-pass |
| universe | `L` minus listed exclusions -- 5,539 atomic pathways |
| arm | `L` (one match threshold everywhere) |

## 2. Build command line

Four steps, in order. The first two are prerequisites that write into `v0.4-leaves-x2/`; the build
itself writes into `v0.4-leaves/` beside the build it is compared with.

```sh
# 1. the universe: drop the listed exclusions, then remove every curated summary
uv run scripts/leaves_universe.py --version 0.4-leaves-x2 --space leaves_centred_x2 \
    --exclude data/excluded_inputs.tsv

# 2. 200 Ward trees on 80% subsamples of the centred sidecar
uv run scripts/build_trees_10770.py --version 0.4-leaves-x2 --space leaves_centred_x2 \
    --vectors data/ontology/v0.4-leaves-x2/vectors_leaves_centred.npy --rows 1-200

# 3. the build itself
uv run scripts/leaves_build.py --arm L --version 0.4-leaves-x2 --space leaves_centred_x2 \
    --out-version 0.4-leaves \
    --floors-file data/ontology/v0.4-leaves/regate/floors_L_cal8.json \
    --repair --directory thema_L_x2

# 4. the comparison against the previous build
uv run scripts/compare_x2.py --new thema_L_x2 --old thema_L_repair

# 5. per-node support and coherence, then the browser
uv run scripts/repair_node_stats.py --version 0.4-leaves-x2 --space leaves_centred_x2 \
    --build-version 0.4-leaves --build thema_L_x2 \
    --out data/experiments/exclusion2/x2_node_stats.json
uv run scripts/export_browse_leaves.py --version 0.4-leaves-x2 --build-version 0.4-leaves \
    --build thema_L_x2 --stats data/experiments/exclusion2/x2_node_stats.json
```

Both of step 5's scripts need `--version 0.4-leaves-x2` (where the universe, the vectors and the
trees live) **together with** `--build-version 0.4-leaves` (where the build was written). Passing
`--version 0.4-leaves` alone silently reads the wrong `universe.json` and reports 5,559 pathways
instead of 5,539. The command above was **verified to reproduce `browse.html` byte-identically**
before this file was written.

## 3. Every parameter

**Resampling and clustering**

| parameter | value |
|---|---|
| linkage | **Ward**, on cosine distance over centred, renormalised MedCPT vectors |
| runs | **200** (`--rows 1-200`, trees persisted per row) |
| subsample | **0.8** |
| `min_size` | 3 |
| embedder | `ncbi/MedCPT-Article-Encoder`, revision `d05a736da4bb84ee4057b7f7999485be6ed85465`, CLS pooling, 512 tokens, description text only |
| space | `leaves_centred_x2` -- raw vectors stored in `embeddings.npy`, the centred sidecar is what is clustered, so centring happens exactly once |

**Recurrence and membership**

| parameter | value |
|---|---|
| `THETA_MATCH` | **0.70** |
| `TOL` | 0.0 (the extras-only rule is removed in v0.4, not switched off) |
| `INCLUSION_CUT` | **0.50** (`src/thema/ontology/v04.py:80`) |
| `TWIN_FRACTION` | **0.10** (`src/thema/ontology/recurrent.py:101`) -- absorption is the twin rule, not a Jaccard |
| `STRAY` | 0.0 (removed stage) |
| `THETA_MERGE` | **0.70** (absorption and consensus) |
| containment | **strict** (partial containment is a removed stage) |

**Stages**

Kept: completion, greedy seed absorption, per-size support floors.
Removed in v0.4 and absent from the code, not switchable: size cap, TOL extras-only rule, STRAY,
partial containment.

**Floors -- cal8, reused**

Solved to an overall **calibration** target of 0.008 on 10 scramble seeds 3001-3010, confirmed once
on held-out 4001-4002. Held-out caps unchanged at 0.01 overall / 0.02 per stratum. `effective =
floor`, with **no `DECLARED_M` minimum**.

| stratum | floor | calibration FDR | real groupings |
|---:|---:|---:|---:|
| 3-3 | 0.840 | 0.00729 | 804 |
| 4-4 | 0.915 | 0.00696 | 1,090 |
| 5-5 | 0.515 | 0.00778 | 1,455 |
| 6-6 | 0.330 | 0.00652 | 2,193 |
| 7-9 | 0.195 | 0.00774 | 8,026 |
| 10+ | 0.025126 | 0.00574 | 86,996 |

**These floors were calibrated on the 10,770 universe and are REUSED here**, after the 17-BTM drop
and again after exclusion 2. That is Aviyah's decision of 9 Oct: use the existing cal8 floors for
now, do not recalibrate and do not run new scrambles. A fresh-seed check on 4003-4005 against
`thema_L_repair` passed at 0.00638. **A full recalibration on this universe is an open to-do**, not
a completed check -- it is recorded in `floors_L_cal8.json` under `reuse_note` and copied into this
build's manifest as `floors_source`.

**Repair post-pass** (`src/thema/ontology/repair.py`, applied after construction, never inside
`consensus.py` -- that file is load-bearing for v0.4's byte-identity proof)

| | |
|---|---|
| fix 1 -- stale merges | re-merge pairs that crossed `MERGE_JACCARD` **0.70** only after membership grew; iterated to a fixed point (2 rounds). **194 merges** -- 58 identical, 136 overlapping. Asserts zero stale pairs remain. |
| fix 2 -- chain collapse | collapse a parent into which a single child holds `COLLAPSE_SHARE` **0.90** or more of its members; children re-linked; iterated to a fixed point (2 rounds). **640 collapses.** |
| survivor rule | **keep the parent.** The absorbed node is the child. Strict containment still holds afterwards because every surviving set is unchanged. |
| order | collapse first, then merge |

## 4. Universe

| | |
|---|---|
| source table | `data/pathways.tsv`, digest `c54319cdfbbe9eb7` -- **never edited**; exclusions are a config list |
| with at least one gene | 10,770 |
| listed exclusions applied | **23** (19 of them in L), leaving 10,747 |
| curated summaries removed | 5,208 (GO 4,367, Reactome 841; Hallmark and BTM are flat and always kept) |
| **built on** | **5,539 atomic pathways** |
| digest after exclusions | `2bf54077a306b856` |
| leaves digest | `97852e70b5a820f0` |

Sources in L: GO 3,167, Reactome 1,995, BTM 327, Hallmark 50.

**The 23 exclusions.** Exclusion 1 is 17 self-described heterogeneous TBA BTMs. Exclusion 2 is sets
whose source name and generated description both fail to identify one specific biological theme,
judged blind by Claude Code subagents against a written rubric: `btm:M137`, `btm:M72.1`,
`go:GO:0009791`, `go:GO:0010800`, `go:GO:0044093`, `go:GO:0065009`.

> **CAVEAT, recorded on purpose.** `go:GO:0010800` -- *positive regulation of peptidyl-threonine
> phosphorylation* -- was excluded **against the declared rule**. The rule excludes a set only when
> **neither** its name **nor** its description names a theme; this name identifies a specific
> mechanism, so the test is not met. The blind judge saw the description alone. It is marked
> *"reinstate at next rebuild"* in `excluded_inputs.tsv`, and **this baseline keeps it excluded**, so
> every number below is exactly what was measured. **Effective exclusions are therefore 22 (19 in L)
> going forward, while this build stands on 23.** The next rebuild will differ by this one input.
>
> Also on the record: `btm:M248`, the example quoted inside the exclusion-2 rule, was judged **"yes"**
> by the blind judges and **stays in**. The rule decides, not the example.

## 5. Headline numbers

| | |
|---|---|
| **themes** | **8,740** |
| edges | 19,646 |
| roots | 121 |
| **roots over 1,000 members** | **10** |
| themes with 2+ parents | 5,581 (63.9%) |
| unplaced | 0 |
| **plausible (coherent or linked umbrella)** | **8,543 of 8,740 = 97.7%** |

Verdicts over all 8,740 themes (1,310 carried from the `thema_L_repair` judging, 7,430 judged fresh
against rubric 4): coherent 7,819, umbrella 724, core-plus-misfits 128, mixture 51, **incoherent 18**
-- of which 8 are at 300 members or below.

Sizes: 3-5 **524**, 6-10 **2,100**, 11-50 **5,837**, 51-300 **263**, 301-1,000 **6**, 1,001+ **10**.

The ten roots over 1,000: `n06927` (2,673), `n03450` (2,522), `n01935` (2,366), `n05174` (2,304),
`n06304` (2,047), `n03196` (2,044), `n02496` (2,042), `n01438` (1,433), `n03232` (1,245),
`n05450` (1,187).

**What is good and what is not.** The middle is 97.7-100% plausible in every band up to 300 members.
Every theme over 1,000 members is bad -- the giants are gene-incoherent bags, and removing the
exclusions made them slightly worse (8 roots over 1,000 in `thema_L_repair`, 10 here). Three area
levels exist and are usable -- immune `n01014`, metabolism `n01438`, genome / cell division `n04626`
-- while signalling, development and neuro have no area and sit inside the giants. Against
`thema_L_repair`, 89% of themes with support at or above 0.1 reproduce, and 91% at 0.5 and above;
the churn is concentrated in low-support themes (median support 0.045 for new themes against 0.685
for identical ones). **Placement remains a known open failure** and is not fixed here: THEMA does
not reliably put curated parents above their children.

## 6. The code this was built from

| | |
|---|---|
| branch | `leaves-2026-10` |
| `HEAD` at build time | `7ba3720703bec06ea9610f4976e7934ee0b69faf` |
| working tree at build time | **dirty** -- see below |

**Stated plainly: the build was made from `7ba3720` plus uncommitted work**, so that hash alone does
not reproduce it. Four scripts were modified and two were new and untracked when the build ran:
`scripts/leaves_universe.py`, `scripts/leaves_build.py`, `scripts/repair_node_stats.py`,
`scripts/export_browse_leaves.py`, `scripts/compare_x2.py`, `scripts/exclusion2_screen.py`.

`docs/status/commit-2026-10-09-baseline.sh` commits exactly that work and tags the result
**`thema-baseline-2026-10-09`**. **That tag is the reproducible pointer to this build's code**; the
hash above is only where the working tree started. Until the tag exists, the sha256 prefixes below
identify the exact sources that ran:

| file | sha256 (first 16) |
|---|---|
| `src/thema/ontology/v04.py` | `8e1b2f124aaf5fed` |
| `src/thema/ontology/repair.py` | `d2e44059dd80150c` |
| `src/thema/ontology/leaves.py` | `4f89ed132bbc7bbb` |
| `src/thema/ontology/consensus.py` | `78817706eb16ec19` |
| `src/thema/ontology/recurrent.py` | `1d940d410df408a1` |
| `scripts/leaves_build.py` | `0bf204ef629da858` |
| `scripts/leaves_universe.py` | `f9d619d79a10d253` |
| `scripts/build_trees_10770.py` | `6b5ac842d9ada25f` |
| `scripts/compare_x2.py` | `e5b864c881c5b404` |

## 7. How to rebuild it

```sh
git checkout thema-baseline-2026-10-09
```

Then run the four steps in section 2. Two things must hold or the rebuild is not this build:

1. **`excluded_inputs.tsv` must list all 23 keys**, `go:GO:0010800` included. The copy in this
   folder is the one to use. The tracked file will lose that key at the next rebuild by decision, so
   a later checkout of the tag plus the then-current config does **not** reproduce 5,539.
2. **`universe_digest` must come out `c54319cdfbbe9eb7`** and `leaves_digest` `97852e70b5a820f0`.
   If either differs, the source table moved and the comparison is invalid -- stop, do not override
   the check.

Cost: 2.2 s for the distance matrix, 27.9 s for the 200 trees, and roughly 4.1 GB peak for the build
(`peak_mb` 4095.9 as recorded in the manifest).

## 8. How to revert to it

The frozen copy is the authority; nothing needs to be regenerated to get back to it.

```sh
# inspect without touching anything
open data/ontology/frozen/baseline-2026-10-09/browse.html

# verify the freeze is intact (also enforced by the test suite)
shasum -a 256 -c data/ontology/frozen/baseline-2026-10-09/CHECKSUMS.sha256

# restore the working build from the freeze
mkdir -p data/ontology/v0.4-leaves/thema_L_x2
for f in nodes.tsv members.tsv edges.tsv unplaced.tsv manifest.json browse.html \
         match_to_repair.tsv compare_to_repair.json; do
  cp data/ontology/frozen/baseline-2026-10-09/$f data/ontology/v0.4-leaves/thema_L_x2/$f
done
cp data/ontology/frozen/baseline-2026-10-09/excluded_inputs.tsv data/excluded_inputs.tsv

# and the code
git checkout thema-baseline-2026-10-09
```

The files are mode 444 as a speed bump, so copying over them needs an explicit `cp -f` or a
`chmod`. Git does not preserve that, so the checksum test is the real guard.

## 9. What a new build must report against this one

Per the 9 Oct decision: new builds go to **new directories** and report a comparison to this
baseline -- theme counts by band, match at Jaccard 0.7 or above, and plausibility where judged.
`scripts/compare_x2.py --new NEW --old thema_L_x2` produces the first two.

Step 4 -- the chain threshold, the chain survivor rule, what to do about the giant roots, and
whether the top level is built recursively -- is **open and pending Aviyah**. None of it is decided
by this freeze.

## 10. Contents

| file | what it is |
|---|---|
| `nodes.tsv`, `members.tsv`, `edges.tsv`, `unplaced.tsv` | the build's four exported tables |
| `manifest.json` | every parameter as recorded by the build |
| `browse.html` | self-contained browser for the whole DAG |
| `match_to_repair.tsv`, `compare_to_repair.json` | per-theme mapping to `thema_L_repair`, and the summary |
| `excluded_inputs.tsv` | the exclusion list **as of the freeze**, all 23 keys |
| `floors_L_cal8.json` | the floors record, including the reuse note and the open recalibration to-do |
| `universe.json` | the universe this was built on, with digests and source counts |
| `trees_build_log.json` | the subsample manifest -- 200 trees, timings, digest |
| `all_verdicts_x2.json` | the plausibility verdict for all 8,740 themes |
| `REPORT_x2.md` | the reviewer's evaluation of this build |
| `CHECKSUMS.sha256` | sha256 of every file above |
