# THEMA working version, O50, frozen 2026-10-14

**Aviyah's decision, 14 Oct 2026.** `thema_L_x2_O50` is the **WORKING VERSION**: every analysis from
14 Oct onwards uses it. **Two earlier builds stay frozen as fallbacks and are unchanged** --
`../working-c85-2026-10-10/` (the previous working version) and `../baseline-2026-10-09/` (the
original reference). Three separate freezes, three separate `CHECKSUMS.sha256`, all guarded by the
same test.

Frozen exactly as built. Nothing here is ever edited:
`tests/ontology/test_frozen_baseline.py` re-hashes every frozen folder on every test run and fails
on a changed, deleted or unrecorded file.

---

## 1. What it is, and the one thing that differs from c85

| | |
|---|---|
| build | `thema_L_x2_O50`, built 13 Oct 2026 |
| original location | `data/ontology/v0.4-leaves/thema_L_x2_O50/` |
| **difference from c85** | **the same-theme cutoff, and the joint fixed point** |
| universe | identical: L minus the 23 listed exclusions, **5,539** atomic pathways |
| trees, floors, `theta_match`, seeds | identical |

**The difference, precisely.** c85 used a same-theme cutoff of **0.70** in consensus and again, as a
separate constant, in the post-build stale-merge pass. O50 uses **one cutoff of 0.50** in **both**
places and repeats `[chain collapse at 0.85, stale merge at 0.50]` to a **joint fixed point**,
asserting afterwards that no non-nested pair at or above 0.50 and no containment pair at or above
0.85 survive. **`theta_match` -- recurrence -- is untouched at 0.70**: it is a different quantity and
is now a separate parameter.

**The iteration is inert at 0.70 and was proved so.** The O70 control -- c85 plus the joint loop at
the old cutoff -- came out **byte-identical to c85 in all four tables**. So the whole difference
between this build and c85 is the cutoff, not the loop. The loop buys the assertion.

**Why 0.50, and the disclosure that goes with it.** J >= 0.5 is exactly "the shared part is at least
as large as the two unique parts together" -- a label-free basis. The reviewer disclosed that the
idea of lowering the cutoff was motivated after seeing LLM-judged evaluation results; the value was
declared on the label-free basis and **not tuned**, and no LLM judgement enters construction.

## 2. Build command line

```sh
uv run scripts/leaves_build.py --arm L --version 0.4-leaves-x2 --space leaves_centred_x2 \
    --out-version 0.4-leaves \
    --floors-file data/ontology/v0.4-leaves/regate/floors_L_cal8.json \
    --repair --collapse-share 0.85 --survivor support \
    --theta-same 0.50 --joint-fixed-point --directory thema_L_x2_O50
```

94 s, 1.4 GB peak. The harness proof for the same code path -- the defaults, which reproduce c85
byte-identically -- is recorded in `docs/status/2026-10-12-overlap-arm.md`.

## 3. Every parameter

| | |
|---|---|
| method | `v0.4`, kept stages: completion, greedy seed absorption, per-size support floors |
| linkage | Ward on cosine distance over centred, renormalised MedCPT vectors |
| runs / subsample | **200** rows, **0.8** |
| `min_size` | 3 |
| `THETA_MATCH` (recurrence) | **0.70**, unchanged |
| **same-theme cutoff** (consensus **and** the stale pass) | **0.50** |
| **joint fixed point** | **on**; 2 outer rounds, 5 collapse and 3 merge rounds inside |
| chain collapse | share **0.85**, survivor `"support"` |
| `TOL` / `STRAY` | 0.0 / 0.0 (both removed stages in v0.4) |
| `INCLUSION_CUT` | 0.50 |
| containment | strict |
| embedder | `ncbi/MedCPT-Article-Encoder` rev `d05a736da4bb84ee4057b7f7999485be6ed85465`, CLS, 512 tokens |
| floors | cal8, calibrated on the 10,770 universe and **reused**; see the note in `floors_L_cal8.json` |
| repair result | 587 collapses (408 kept the child, 179 the parent), 72 stale merges (35 identical, 37 non-nested) |
| peak | 1,411 MB |

**Open, unchanged from both fallbacks:** a full floors recalibration on this universe is still a
to-do, not a completed check; `go:GO:0010800` is still excluded against the declared rule and marked
for reinstatement, so this build stands on **23** exclusions while **22** are effective going
forward.

## 4. Headline numbers

| | baseline | c85 | **O50** |
|---|---:|---:|---:|
| themes | 8,740 | 8,251 | **4,602** |
| edges | 19,646 | 18,707 | 7,525 |
| roots | 121 | 121 | 188 |
| **roots over 1,000 members** | 10 | 10 | **4** |
| themes with 2+ non-nested parents | 63.9% | 64.8% | **43.7%** |
| the same, giants excluded | -- | 51.2% | **36.8%** |
| reaching 2+ roots, giants excluded | -- | 55.7% | **41.9%** |
| unplaced | 0 | 0 | 0 (4 attach only to a root) |
| **plausible (coherent or umbrella)** | **97.75%** | **97.64%** | **97.57%** |
| **not ok** | 197 | 195 | **112** |

**The plausibility share is flat while the absolute count nearly halves.** 112 not-ok against c85's
195: 99 carried from identical c85 themes plus **13 of the 858 new ones**, so the new themes are
**845 of 858 ok = 98.5%**. The share dips 0.07 points only because the denominator fell faster than
the numerator. Verdicts for all 4,602 themes are in `all_verdicts_O50.json`: **3,744 carried** from
the c85 freeze by identical member set, **858 judged fresh** by the reviewer against rubric 4.

**The giants fall from 10 to 4** -- 2,332, 2,018, 2,015, 1,412 -- the first change in this project
that moves them at all. The remaining four are still grab-bags and are most of the 112 not-ok.

## 5. The criteria it was adopted on

Declared by the reviewer on 12 Oct, before any build
(`data/experiments/reviewer_notes/SPEC_overlap_arm_2026-10-12.md`, copied verbatim into DECISIONS).

| | criterion | owner | result |
|---|---|---|---|
| C1 | no non-nested pair under 1,000 at J >= 0.50, no containment pair at >= 0.85 | ccode | **PASS** -- 0 and 0, against **9,138** such pairs in c85 |
| C2 | no pathway loses all its themes under 1,000 | ccode | **FAIL**, 1 pathway -- **accepted as a known exception** |
| C3 | >= 99% of absent c85 themes have an O50 counterpart at J >= 0.50 | ccode | **PASS** -- 99.64% |
| C4 | plausibility, not-ok <= c85's 195 | reviewer | **PASS** -- 112 |
| C5 | usefulness, blind, O50 must win | reviewer | **WON** -- 87 to 33, p = 9e-7 |

**C2's exception is `btm:M205`**, recorded rather than waived quietly. It is an untitled BTM module
with an NF-kB arm (CHUK, BAG4, ZFAND6) and a BMP/TGF-beta arm (BMPR2, RNF111). Its only small homes
in c85 were three weak TGF-beta/BMP themes (support 0.055-0.105, 10-14 members) that also held two
other BTM modules; at 0.50 those were superseded by tighter TGF-beta/SMAD themes that do not hold it.
A mixed module with half its biology outside TGF-beta is a plausible loose fit. **Aviyah accepted it
on 13 Oct.** It now sits inside three giants only, so a hit on it can be interpreted only through a
bag.

**C5, and what it cost.** 120 pathways, blind, both theme sets shown in full with no names and sides
randomised: O50 preferred **87**, c85 **33**, none equal -- 72.5% of decided items against a 60% bar,
binomial p = 9e-7. O50 wins by giving the same contexts without the near-duplicate repeats. **c85
still won 28% of items**, by keeping a context O50 lost -- a broader CDK4/6-RB theme, ER-phagy,
Gq/PLC calcium -- and the share of pathways with distinct homes falls from 79% to 66%. **The cleanup
costs some real facets.** That is the honest price of this adoption and is why both fallbacks stay
frozen.

## 6. Known limits, carried forward

- **The survivor choice is still partly a coin flip**, though less so: collapse decisions settled by
  a support margin under 0.05 fall from **28.3%** in c85 to **19.4%** here. 587 collapses, 408 of
  which kept the child.
- **Reproducibility between independent builds falls**, 77.1% to **70.2%** matched at J >= 0.7
  against a build on the repair universe. The spec declared this report-only: removing duplicates
  lowers a share-matched measure by construction, which is the same reason criterion (d) was
  withdrawn from the c85 assessment. It is not evidence either way.
- **A pathway sits in a median of 12 fewer themes** under 1,000 members than in c85.
- **The four giants are untouched in kind**, only in number.
- **Placement monotonicity is unchanged and still at chance** (46.1% among curated pairs whose levels
  differ). Nothing in this arm addresses it.

## 7. The code this was built from

| | |
|---|---|
| tag | **`thema-O50-2026-10-14`**, created by `docs/status/commit-2026-10-14-adopt-O50.sh` |
| branch | built on `overlap-2026-10`, merged into `leaves-2026-10` with `--no-ff` |
| the rule | `v04.build(..., theta_same=...)` and `repair.repair_joint()` in `src/thema/ontology/` |
| flags | `scripts/leaves_build.py --theta-same 0.50 --joint-fixed-point` |

`git checkout thema-O50-2026-10-14` then the command in section 2. Two things must hold or it is not
this build: `excluded_inputs.tsv` must still list all 23 keys (the copy in this folder is the one to
use), and `universe_digest` must come out `c54319cdfbbe9eb7` with `leaves_digest`
`97852e70b5a820f0`. If either differs, stop -- do not override the check.

## 8. How to revert to it

```sh
shasum -a 256 -c data/ontology/frozen/working-O50-2026-10-14/CHECKSUMS.sha256
mkdir -p data/ontology/v0.4-leaves/thema_L_x2_O50
for f in nodes.tsv members.tsv edges.tsv unplaced.tsv manifest.json repair_map.json \
         report.txt O50_new_themes.json match_to_c85.tsv; do
  cp data/ontology/frozen/working-O50-2026-10-14/$f data/ontology/v0.4-leaves/thema_L_x2_O50/$f
done
cp data/ontology/frozen/working-O50-2026-10-14/excluded_inputs.tsv data/excluded_inputs.tsv
git checkout thema-O50-2026-10-14
```

Files are mode 444 as a speed bump. Git does not preserve that, so the checksum test is the guard.

## 9. What a new build must report against this one

Theme counts by band, match at Jaccard 0.7 or above, and plausibility where judged -- against **all
three** freezes, because this is the working version and the other two are the fallbacks.

**Superseded, and not to be run:** the sibling merge rule of 10 Oct (`J >= 0.6 & md <= 2`, complete
linkage) is dead twice over -- its precision fell to 63% under blind full-list labels, and this build
moves the overlap rule inside the algorithm, which is what it was a post-hoc substitute for.

## 10. Contents

| file | what it is |
|---|---|
| `nodes.tsv`, `members.tsv`, `edges.tsv`, `unplaced.tsv` | the four exported tables |
| `manifest.json` | every parameter as the build recorded it, `theta_same` and `joint_fixed_point` included |
| `match_to_c85.tsv` | every O50 theme mapped to its closest c85 theme, with an identical flag |
| `O50_new_themes.json` | the 858 themes not identical to any c85 theme, with full member lists -- what C4 judged |
| `repair_map.json` | which node of each collapsed pair died, and on what support margin |
| `report.txt` | the full measurement report from `scripts/overlap_arm_report.py` |
| `excluded_inputs.tsv` | the exclusion list as of the freeze, all 23 keys |
| `floors_L_cal8.json` | the floors record, with the reuse note and the open recalibration to-do |
| `universe.json` | the universe, with digests and source counts |
| `trees_build_log.json` | the subsample manifest: 200 trees, timings, digest |
| `all_verdicts_O50.json` | a verdict for all 4,602 themes: 3,744 carried, 858 judged |
| `REPORT_o50_eval.md` | the reviewer's C4 and C5 report, verbatim |
| `CHECKSUMS.sha256` | sha256 of every file above |
