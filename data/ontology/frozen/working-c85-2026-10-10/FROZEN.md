# THEMA working version, c85, frozen 2026-10-10

**Aviyah's decision, 10 Oct 2026, recorded 13 Oct.** `thema_L_x2_c85` is the **WORKING VERSION**:
every analysis from 10 Oct onwards uses it. The **2026-10-09 baseline remains frozen as the
fallback** and is unchanged -- `../baseline-2026-10-09/` is a separate, separately checksummed
freeze, and this one does not replace it.

Frozen exactly as built. Nothing here is ever edited:
`tests/ontology/test_frozen_baseline.py` re-hashes both frozen folders against their
`CHECKSUMS.sha256` on every test run and fails on a changed, deleted or unrecorded file.

---

## 1. What it is, and the one thing that differs from the baseline

| | |
|---|---|
| build | `thema_L_x2_c85`, built 9 Oct 2026 |
| original location | `data/ontology/v0.4-leaves/thema_L_x2_c85/` |
| **difference from the baseline** | **the chain-collapse rule, and nothing else** |
| universe | identical: L minus the 23 listed exclusions, **5,539** atomic pathways |
| trees, floors, thresholds, seeds | identical |

**The difference, precisely.** The baseline collapses a parent-child pair when the child holds
**0.90** or more of the parent's members and always **keeps the parent**. This build collapses at
**0.85** and **keeps the higher-support node**, falling back to the parent on a tie or when the
parent is top level. Everything else -- Ward, 200 runs at subsample 0.8, `theta_match` 0.70,
`theta_merge` 0.70, `TOL` 0, `INCLUSION_CUT` 0.50, `TWIN_FRACTION` 0.10, strict containment, the
cal8 floors, the stale-merge pass at 0.70 -- is the baseline's configuration untouched.

**The rule is POST-HOC** and is labelled so wherever it is reported: both the threshold and the
survivor rule were chosen after seeing the n00150 lattice and the 550-pair survivor measurement.

## 2. Build command line

```sh
uv run scripts/leaves_build.py --arm L --version 0.4-leaves-x2 --space leaves_centred_x2 \
    --out-version 0.4-leaves \
    --floors-file data/ontology/v0.4-leaves/regate/floors_L_cal8.json \
    --repair --collapse-share 0.85 --survivor support --directory thema_L_x2_c85
```

Reproduced byte-identically on 13 Oct 2026 by the overlap arm's harness proof, which runs the same
command through the new `--theta-same` / `--joint-fixed-point` code path at its defaults. All four
tables matched. 315 s, 1.3 GB peak.

## 3. Every parameter

| | |
|---|---|
| method | `v0.4`, kept stages: completion, greedy seed absorption, per-size support floors |
| linkage | Ward on cosine distance over centred, renormalised MedCPT vectors |
| runs / subsample | **200** rows, **0.8** |
| `min_size` | 3 |
| `THETA_MATCH` (recurrence) | **0.70** |
| `THETA_MERGE` / same-theme cutoff (consensus) | **0.70** |
| stale-merge pass | **0.70** |
| **chain collapse** | **share 0.85, survivor "support"** |
| `TOL` / `STRAY` | 0.0 / 0.0 (both removed stages in v0.4) |
| `INCLUSION_CUT` | 0.50 |
| containment | strict |
| embedder | `ncbi/MedCPT-Article-Encoder` rev `d05a736da4bb84ee4057b7f7999485be6ed85465`, CLS, 512 tokens |
| floors | cal8, calibrated on the 10,770 universe and **reused**; see the reuse note in `floors_L_cal8.json` |
| repair result | 1,147 collapses (742 kept the child, 405 the parent), 176 stale merges (68 identical, 108 non-nested), 4 and 2 rounds |
| peak | 1,364 MB |

**Open, unchanged from the baseline:** a full floors recalibration on this universe is still a
to-do, not a completed check; `go:GO:0010800` is still excluded against the declared rule and marked
for reinstatement, so this build stands on **23** exclusions while **22** are effective going
forward.

## 4. Headline numbers

| | baseline | **c85** |
|---|---:|---:|
| themes | 8,740 | **8,251** |
| edges | 19,646 | 18,707 |
| roots | 121 | 121 |
| roots over 1,000 members | 10 | **10, unchanged** |
| themes with 2+ parents | 5,581 (63.9%) | 5,345 (64.8%) |
| unplaced | 0 | 0 |
| **plausible (coherent or umbrella)** | 8,543 / 8,740 = **97.75%** | 8,056 / 8,251 = **97.64%** |
| **not ok** | 197 | **195** |

**The plausibility dip is composition, not damage.** The rule removed 805 themes of which 801 were
ok -- near-duplicates of good themes -- and kept 316 that the baseline had never judged, of which
314 are ok. No theme got worse and there are two fewer bad themes. Verdicts for all 8,251 themes are
in `all_verdicts_c85.json`: 7,935 carried from the baseline by identical member set, 316 judged
fresh by the reviewer with rubric 4.

**Facets: none lost, under the corrected definition.** Of the 805 baseline themes absent here, 750
have a surviving counterpart at Jaccard 0.85 or above, 52 at 0.70-0.85, and **3 at 0.68-0.69**:
`n05820` mitochondrial FA and BCAA catabolism (40), `n05176` type I interferon antiviral response
(65), `n05887` Rho GTPase cycles (23). The full argument is `REPORT_c85_reassessment.md`, copied
into this folder.

**What it does not do.** The ten giant roots are untouched. Sibling near-twins remain: a pathway
still sits in a median of 9 mutually non-nested themes, many of them overlapping variants, which
chain collapse cannot reach. That is what the overlap arm of 12 Oct tests.

**The known limit.** **28% of collapse pairs are decided by a support margin under 0.05**, so which
twin survives can differ between builds. This is the reason the baseline stays frozen as the
fallback rather than being retired.

## 5. The code this was built from

The build predates the commit that records it, so the honest pointer is the tag.

| | |
|---|---|
| tag | **`thema-c85-2026-10-10`**, created by `docs/status/commit-2026-10-12-handoff.sh` |
| branch | `leaves-2026-10` |
| rule | `collapse_chains(..., share=0.85, survivor="support")` in `src/thema/ontology/repair.py` |

`git checkout thema-c85-2026-10-10` then the command in section 2. Two things must hold or it is not
this build: `excluded_inputs.tsv` must still list all 23 keys (the copy in this folder is the one to
use), and `universe_digest` must come out `c54319cdfbbe9eb7` with `leaves_digest`
`97852e70b5a820f0`. If either differs, stop -- do not override the check.

## 6. How to revert to it

```sh
shasum -a 256 -c data/ontology/frozen/working-c85-2026-10-10/CHECKSUMS.sha256
mkdir -p data/ontology/v0.4-leaves/thema_L_x2_c85
for f in nodes.tsv members.tsv edges.tsv unplaced.tsv manifest.json match_to_baseline.tsv \
         repair_map.json report.txt; do
  cp data/ontology/frozen/working-c85-2026-10-10/$f data/ontology/v0.4-leaves/thema_L_x2_c85/$f
done
cp data/ontology/frozen/working-c85-2026-10-10/excluded_inputs.tsv data/excluded_inputs.tsv
git checkout thema-c85-2026-10-10
```

Files are mode 444 as a speed bump. Git does not preserve that, so the checksum test is the guard.

## 7. What a new build must report against this one

Theme counts by band, match at Jaccard 0.7 or above, and plausibility where judged. The 2026-10-09
baseline keeps the same requirement; a new build is compared against **both**, because this one is
the working version and that one is the fallback.

**Superseded by this freeze:** the sibling merge rule accepted on 10 Oct (`J >= 0.6 & md <= 2`,
complete linkage) **must not be run** -- its precision fell from 84% to 63% under blind full-list
labels, and the overlap arm of 12 Oct replaces it by moving the overlap rule inside the build.

## 8. Contents

| file | what it is |
|---|---|
| `nodes.tsv`, `members.tsv`, `edges.tsv`, `unplaced.tsv` | the four exported tables |
| `manifest.json` | every parameter as the build recorded it |
| `match_to_baseline.tsv` | every theme mapped to its closest baseline theme |
| `repair_map.json` | which node of each collapsed pair died, and on what support margin |
| `report.txt` | the full measurement report from `scripts/chain_c85_report.py` |
| `excluded_inputs.tsv` | the exclusion list as of the freeze, all 23 keys |
| `floors_L_cal8.json` | the floors record, with the reuse note and the open recalibration to-do |
| `universe.json` | the universe, with digests and source counts |
| `trees_build_log.json` | the subsample manifest: 200 trees, timings, digest |
| `all_verdicts_c85.json` | a verdict for all 8,251 themes, carried or freshly judged |
| `REPORT_c85_reassessment.md` | the reviewer's corrected assessment, verbatim |
| `CHECKSUMS.sha256` | sha256 of every file above |
