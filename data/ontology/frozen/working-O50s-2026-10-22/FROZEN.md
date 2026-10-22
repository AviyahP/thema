# THEMA working version, O50s, frozen 2026-10-22

**Aviyah's decision, 22 Oct 2026.** `thema_L_x2_O50s` is the **WORKING BASELINE**: every analysis
from 22 Oct onwards uses it. **Frozen O50 (14 Oct) is kept as the previous baseline** and is
unchanged, as are `../working-c85-2026-10-10/` and `../baseline-2026-10-09/`. Four separate freezes,
four separate `CHECKSUMS.sha256`, all guarded by the same test.

Frozen exactly as built, copied unchanged from `data/ontology/v0.4-leaves/thema_L_x2_O50s/`.
Nothing here is ever edited: `tests/ontology/test_frozen_baseline.py` re-hashes every frozen folder
on every test run and fails on a changed, deleted or unrecorded file.

---

## 1. Adopted with a known failure, and that is on the record

**The 17 Oct blind reading FAILED the declared 90% bar: 81.4%, against 89.3% for O50's own large
themes.** O50s is adopted anyway, for four stated reasons:

1. its per-size floors are calibrated like every other stratum, not asserted;
2. it raises summary placement from **85.3% to 92.6%** (+173 of 2,370 curated summaries);
3. it adds the **101-1,000 band** -- 87 themes against O50's 17, of which 59 are new at J < 0.7;
4. all work since 17 Oct rests on it.

**The open question, recorded and not resolved:** its new large themes rest on **2 to 4 runs of
200**. Every one of the 59 new themes sits at support 0.0100 to 0.0200. That is a later
minimum-support decision, deliberately not taken here -- the floors admit them, and no minimum
support beyond the floors is applied.

## 2. What it is

| | |
|---|---|
| build | `thema_L_x2_O50s`, built 17 Oct 2026 |
| original location | `data/ontology/v0.4-leaves/thema_L_x2_O50s/` |
| method | `v0.4-leaves`, size strata above 10 (O50s) |
| **difference from O50** | **thirteen size strata instead of six**, so the gate is calibrated per size |
| universe | L minus the 23 listed exclusions, **5,539** atomic pathways |
| universe digest | `c54319cdfbbe9eb7` (x2 trees); leaves digest `97852e70b5a820f0` |
| runs | 200 |
| theta_match | 0.70 |
| theta_same | 0.50, joint fixed point |
| collapse | 0.85, survivor `support` |
| min_size | 3; inclusion cut 0.5 (families only) |
| floors | `floors_o50s.json`: five strata unchanged from frozen cal8, eight solved 17 Oct |
| peak | 1,326 MB |

Strata: (3,3) (4,4) (5,5) (6,6) (7,9) (10,19) (20,39) (40,79) (80,159) (160,319) (320,639)
(640,1279) (1280+).

## 3. Headline numbers

| | O50 | **O50s** |
|---|---:|---:|
| themes | 4,602 | **5,658** |
| roots | 188 | **261** |
| roots of 50 or fewer | 168 (89.4%) | **164 (62.8%)** |
| edges | - | **12,555** |
| multi-parent | 43.7% | **63.3%** |
| children per node, max / median | 283 / 1 | **382 / 2** |
| giants over 1,000 | 4 | **5** |
| summary placement | 85.3% | **92.6%** |
| Reactome median best J | 0.273 | **0.273** |
| themes of 101-1,000 | 17 | **87** (59 new at J < 0.7) |
| small themes (3-50) | 4,486 | **5,305** = 118.3% of O50 |
| **17 Oct reading, large themes** | **89.3%** | **81.4% -- FAILED the 90% bar** |

Giants: `n01843` (2,564), `n02672` (2,172), `n03878` (2,135), `n04994` (2,096), `n01419` (1,603).

Held-out FDR overall **0.00233** over 26,120 real candidates; caps 0.02 per stratum and 0.01
overall; **none over the cap**. In six strata (40-79 upward, and 160-319 onward) the
**rule-of-three bound decided the cut**: no scrambled candidate was observed at or above it, so the
mean count was replaced by 3/10 rather than read as zero.

94.9% of O50's themes (4,367 of 4,602) have an O50s counterpart at J >= 0.9.

## 4. Rebuild, and verify

```sh
uv run scripts/o50s_build.py                 # rebuild O50s into data/ontology/v0.4-leaves/
uv run scripts/o50s_build.py --verify        # harness proof against FROZEN O50, not against O50s
(cd data/ontology/frozen/working-O50s-2026-10-22 && shasum -a 256 -c CHECKSUMS.sha256)
```

**`--verify` proves the harness against frozen O50**, not against this folder: its `--frozen`
default is `../working-O50-2026-10-14` and it runs the frozen six strata and cal8 floors. To verify
O50s itself, rebuild into a new directory and diff `nodes.tsv`, `members.tsv`, `edges.tsv` and
`unplaced.tsv` against this folder. `verify.txt` here is O50s's own build-time record of that
harness proof.

## 5. Revert

To make O50s the working build again after any later change, copy the four tables and
`manifest.json` from this folder back to `data/ontology/v0.4-leaves/thema_L_x2_O50s/`. The folder is
self-describing: `universe.json`, `excluded_inputs.tsv`, `floors_o50s.json` and
`trees_build_log.json` pin the universe, the exclusions, the gate and the trees it was built from.

The checksum file lists bare filenames, as every other freeze here does, so it must be checked
from inside the folder -- the `cd` above is not optional, and the root-level form fails for all four
freezes alike.

Code identity: the tag `thema-O50s-2026-10-22`.
