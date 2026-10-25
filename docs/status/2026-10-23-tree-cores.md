# Arm K: cores found in the Ward trees. Steps 2-3, two thresholds, three recurrence bars. 23 Oct 2026

Prompt 59, a follow-up quick check at a 50% threshold, and prompt 60's recurrence bars with an
indicative two-seed noise check. Exploratory; **no ontology is built** and nothing is adopted.
**Steps 4, 5 and 6 and sections A, C, D and E are not run.**

**The result, and it is the same at both thresholds: cores recur below 25 pathways and do not recur
above 50.** Arm K fixes prompt 58's problem for small cores -- a median 11 to 29 runs of 200, against
prompt 58's median of *one* -- and fails completely for large ones. Above 200 pathways, essentially
**every** candidate is found in exactly 2 runs and no more, which is to say in nothing but the two
runs that created it.

Loosening the threshold from 70% to 50% admits **5.3 times** as many candidates and roughly doubles
the recurrence below 25 pathways. **It changes nothing above 50.** So the wall is not an artefact of
where the threshold was set.

**Nor is it an artefact of the 2-run placeholder.** At a real bar of 20 runs of 200, 294,749 cores
survive and **the largest is 59 pathways**; the 100-199 band empties completely. Two scrambled seeds
produce recurrent cores too, but all but one of them in 3-5 and 6-11 -- **from 25 pathways up the
scramble is exactly empty at every bar** -- so what arm K finds is real and what it misses is missing
from the data, not from the test. The bars do not clean the output either: redundancy per core is flat across bars, at 44 times
the near-copy rate of O50s's own gated themes.

## What was run, and what was not

| step | state |
|---|---|
| 1 the test, 2 candidates, 3 scoring | **done at cover 0.70 and 0.50**, exact, verified |
| 4 closed cores, 5 members | not run |
| 6 floors | **not run.** Prompt 59 forbade building scramble trees; prompt 60 lifted that for seeds 3001-3002 only, which is a noise check and not a calibration -- step 6 needs ten seeds |
| A, C, D, E | not run |
| B support | **this note** |
| prompt 60: bars at 5, 10, 20 runs; the noise check; examples | **this note**, under "Recurrence bars" |

## The by-construction floor, which must not be read as evidence

**Every candidate is found in at least 2 runs: 921,420 of 921,420 at cover 0.70, and 4,881,836 of
4,881,836 at 0.50 -- 100.00% in both.** A candidate is `C1 & C2` with the intersection covering each
cluster at the threshold; K is therefore wholly drawn in each of those two runs, and its lowest
common ancestor there sits inside C1 (or C2), which it covers at the threshold by construction. So
**the "found in at least 2 runs" placeholder retains every candidate and cannot be used as a
cutoff.** The invariant is asserted in the code and held exactly at both thresholds, which is the
only thing it is good for: a check that the test and the candidate rule agree.

## Candidate counts

| | cover 0.70 | cover 0.50 |
|---|---:|---:|
| clusters of 3+ over 200 runs | 537,024 | 537,024 |
| qualifying cluster pairs | 16,039,739 | **45,507,049** |
| **distinct candidates** | **921,420** | **4,881,836** |
| verification (sample of 2,000 clusters, seed 20261023) | **IDENTICAL** | **IDENTICAL** |

Both are under the prompt's 5,000,000 bound, the 50% arm only just. Counted by chunked sparse
products with an **exact** size window -- a qualifying pair needs `|I| >= cover * max`, so
`max / min <= 1 / cover` -- and checked against an explicit double loop on a random sample: 70% gave
sparse (197 pairs, 170 distinct) against brute (197, 170); 50% gave (613, 542) against (613, 542).

## B. Support, the two thresholds side by side

Median runs found and median support, by band:

| band | 0.70 candidates | 0.70 med runs | 0.70 med support | 0.50 candidates | 0.50 med runs | 0.50 med support |
|---|---:|---:|---:|---:|---:|---:|
| 3-5 | 93,399 | 12 | 0.0707 | 282,412 | **22** | 0.1330 |
| 6-11 | 336,799 | 14 | 0.0700 | 1,480,449 | **29** | 0.1495 |
| 12-24 | 374,187 | 11 | 0.0550 | 1,791,451 | **24** | 0.1200 |
| 25-49 | 94,412 | 3 | 0.0150 | 715,314 | **7** | 0.0350 |
| 50-99 | 15,312 | **2** | 0.0100 | 273,510 | **2** | 0.0100 |
| 100-199 | 5,556 | **2** | 0.0100 | 167,132 | **2** | 0.0100 |
| 200-399 | 507 | **2** | 0.0100 | 89,329 | **2** | 0.0100 |
| 400-799 | 937 | **2** | 0.0100 | 62,922 | **2** | 0.0100 |
| 800-1599 | 311 | **2** | 0.0100 | 19,317 | **2** | 0.0100 |
| ALL | 921,420 | 11 | 0.0550 | 4,881,836 | 17 | 0.0900 |

Runs-found buckets at **cover 0.70**:

| band | 2 | 3-4 | 5-9 | 10-19 | 20-49 | 50+ |
|---|---:|---:|---:|---:|---:|---:|
| 3-5 | 6,843 | 11,793 | 21,559 | 23,200 | 21,306 | 8,698 |
| 6-11 | 13,662 | 33,630 | 73,203 | 89,708 | 88,349 | 38,247 |
| 12-24 | 43,431 | 52,937 | 76,054 | 77,906 | 81,778 | 42,081 |
| 25-49 | 39,716 | 16,822 | 13,631 | 10,692 | 9,788 | 3,763 |
| 50-99 | 13,309 | 618 | 346 | 300 | 651 | 88 |
| 100-199 | 5,355 | 186 | 14 | 1 | 0 | 0 |
| 200-399 | **507** | 0 | 0 | 0 | 0 | 0 |
| 400-799 | **937** | 0 | 0 | 0 | 0 | 0 |
| 800-1599 | **311** | 0 | 0 | 0 | 0 | 0 |
| ALL | 124,071 | 115,986 | 184,807 | 201,807 | 201,872 | 92,877 |

Runs-found buckets at **cover 0.50**:

| band | 2 | 3-4 | 5-9 | 10-19 | 20-49 | 50+ |
|---|---:|---:|---:|---:|---:|---:|
| 3-5 | 7,650 | 17,103 | 40,203 | 63,071 | 95,029 | 59,356 |
| 6-11 | 20,929 | 57,916 | 163,819 | 282,568 | 502,100 | 453,117 |
| 12-24 | 99,983 | 146,601 | 247,754 | 308,631 | 487,467 | 501,015 |
| 25-49 | 153,716 | 115,960 | 132,823 | 114,687 | 104,711 | 93,417 |
| 50-99 | 180,123 | 42,601 | 22,779 | 14,374 | 11,622 | 2,011 |
| 100-199 | 148,373 | 11,783 | 4,478 | 1,606 | 862 | 30 |
| 200-399 | **89,256** | 73 | 0 | 0 | 0 | 0 |
| 400-799 | **62,914** | 8 | 0 | 0 | 0 | 0 |
| 800-1599 | **19,317** | 0 | 0 | 0 | 0 | 0 |
| ALL | 782,261 | 392,045 | 611,856 | 784,937 | 1,201,791 | 1,108,946 |

Share at or above each support, and the median number of runs that judged the candidate:

| band | 0.70 >=0.05 | 0.70 >=0.10 | 0.70 >=0.33 | 0.50 >=0.05 | 0.50 >=0.10 | 0.50 >=0.33 | med judged |
|---|---:|---:|---:|---:|---:|---:|---:|
| 3-5 | 62.5% | 38.0% | 8.4% | 81.6% | 60.8% | 17.8% | 175 |
| 6-11 | 64.2% | 37.6% | 6.8% | 83.6% | 64.5% | 21.1% | 200 |
| 12-24 | 53.9% | 33.1% | 6.9% | 72.4% | 55.2% | 19.7% | 200 |
| 25-49 | 25.7% | 14.4% | 2.2% | 43.7% | 27.7% | 9.0% | 200 |
| 50-99 | 6.8% | 4.8% | 0.0% | 10.2% | 5.0% | 0.3% | 200 |
| 100-199 | **0.0%** | **0.0%** | **0.0%** | 1.5% | 0.5% | 0.0% | 200 |
| 200-399 and above | **0.0%** | **0.0%** | **0.0%** | **0.0%** | **0.0%** | **0.0%** | 200 |

**This is a failure to recur, not a failure to be testable.** Every band is judged by essentially all
200 runs -- median 200, and 175 at 3-5 where a 3-member set sometimes has fewer than 3 pathways
drawn. The large candidates are tested 200 times and found twice.

## What the two thresholds together establish

1. **Arm K's design works below 25 pathways.** Median 11-14 runs at cover 0.70 and 22-29 at 0.50,
   against prompt 58's median of one. A core really does "keep coming back inside clusters that are
   mostly the core" -- for small cores.
2. **It fails above 50 pathways, identically at both thresholds.** Median 2 runs, support 0.0100, and
   **no candidate above 200 pathways reaches support 0.05 at either threshold**. At 0.70 every one of
   the 1,755 candidates above 200 pathways is found in exactly 2 runs; at 0.50, 171,487 of 171,568
   are, which is 99.95%.
3. **The wall is not where the threshold is.** Halving the coverage requirement multiplies candidates
   by 5.3 and doubles small-core recurrence while leaving the large bands untouched. That is the
   strongest evidence yet that the absence is in the resampling rather than in the test.
4. **The 25-49 band is where it breaks**, and it moves a little with the threshold: median 3 runs at
   0.70, 7 at 0.50. So the boundary sits between 25 and 50 pathways and is slightly threshold
   dependent, while everything above 50 is not.

Taken with prompt 58 -- where cores from J >= 0.70 copies had a median of one run above 25 pathways
-- **three different core definitions now agree that there is no recurrent core above about 50
pathways in this resampling.** O50s's large themes and its five giants are not recurrent objects
under any of them.

## Recurrence bars, 5 / 10 / 20 runs of 200 (prompt 60)

Prompt 59's note warned that the 2-run figure is a construction artefact: every candidate is an
intersection of two clusters each at least 70% covered by it, so **every** candidate is found in at
least its own two runs and a 2-run bar retains all 921,420. Prompt 60 asks what survives at real
bars. Nothing is rebuilt -- the candidates and their `found` counts are prompt 59's, unchanged, at
cover 0.70.

### 1a. Retained cores by band

| band | >= 5 runs | >= 10 runs | >= 20 runs |
|---|---:|---:|---:|
| 3-5 | 74,763 | 53,204 | 30,004 |
| 6-11 | 289,507 | 216,304 | 126,596 |
| 12-24 | 277,819 | 201,765 | 123,859 |
| 25-49 | 37,874 | 24,243 | 13,551 |
| 50-99 | 1,385 | 1,039 | 739 |
| 100-199 | 15 | 1 | 0 |
| **TOTAL** | **681,363** | **496,556** | **294,749** |

Of 921,420 candidates, 74% clear 5 runs, 54% clear 10 and 32% clear 20 -- so the bars cut hard in
absolute terms and barely at all in shape. **The band profile is almost scale-invariant**: 12-24 and
6-11 hold 83-85% of the retained cores at every bar, and the 25-49 share moves only from 5.6% to 4.6%.
Raising the bar does not shift where the cores are; it thins all the small bands at once.

### 1b. The ten largest retained cores

| bar | the ten largest, size (runs found) |
|---|---|
| >= 5 runs | 115 (7r), 113 (7r), 113 (10r), 112 (6r), 111 (6r), 111 (5r), 110 (7r), 109 (5r), 109 (5r), 109 (5r) |
| >= 10 runs | 113 (10r), 60 (13r), 59 (25r), 58 (16r), 58 (13r), 58 (36r), 58 (16r), 57 (31r), 57 (11r), 57 (45r) |
| >= 20 runs | 59 (25r), 58 (36r), 57 (31r), 57 (63r), 57 (23r), 57 (27r), 57 (43r), 57 (31r), 57 (20r), 57 (43r)

This is the clearest single statement of the ceiling in the whole arm. **At 10 runs exactly one
retained core exceeds 60 pathways, and at 20 runs none does** -- the largest is 59. The 100-199 band
empties entirely between 5 and 20 runs: 15 cores, then 1, then 0. Every core above 100 pathways is a
5-to-10-run object, which is to say an object seen in at most 5% of the resampling.

### 1c. Pathways covered by at least one retained core

| bar | pathways | share of 5,539 |
|---|---:|---:|
| >= 5 runs | 5,539 | 100.00% |
| >= 10 runs | 5,539 | 100.00% |
| >= 20 runs | 5,537 | 99.96% |

Coverage is not the scarce thing. **Even at 20 runs every pathway but two sits in some recurrent
core**, so the bars do not prune the universe -- they prune the number of ways each pathway is
described. What is missing above 50 pathways is not coverage but any large set that recurs.

### 1d. Redundancy among the retained cores

Counted exactly with prompt 58's counter -- chunked sparse products of the core-by-pathway matrix
with its transpose -- and **verified against an explicit double loop on a random sample of 2,000
cores (seed 20261023) at every bar: all three counts matched exactly, three times out of three.**

| bar | cores | non-nested J >= 0.5 | nested, smaller >= 0.85 | smaller 1 member outside |
|---|---:|---:|---:|---:|
| >= 5 runs | 681,363 | **474,570,657** | 1,340,591 | **229,444,612** |
| >= 10 runs | 496,556 | **351,628,497** | 1,126,931 | **146,364,093** |
| >= 20 runs | 294,749 | **204,223,984** | 767,518 | **69,025,509** |

Non-nested pairs at J >= 0.5, by band of the larger core:

| band | >= 5 runs | >= 10 runs | >= 20 runs |
|---|---:|---:|---:|
| 3-5 | 626,784 | 417,967 | 187,185 |
| 6-11 | 64,675,892 | 49,599,756 | 28,327,663 |
| 12-24 | 327,694,913 | 247,340,601 | 147,553,854 |
| 25-49 | 79,574,105 | 53,273,260 | 27,802,466 |
| 50-99 | 1,998,886 | 996,913 | 352,816 |
| 100-199 | 77 | 0 | 0 |

**Raising the bar does not reduce redundancy; it barely dents it.** Halving the core count from
681,363 to 294,749 (43.3%) leaves 204,223,984 of 474,570,657 non-nested pairs (43.0%) -- the
pairs fall in exact proportion to the objects, so **per core the redundancy is flat**: 696.5
non-nested near-copies per core at 5 runs, 692.9 at 20. For comparison, O50s's 26,120 gated themes carry 409,858
such pairs, or 15.7 per theme. **These cores are 44 times more redundant per object than the gated
themes already are** (696.5 against 15.7), at every bar, so a bar is not a substitute for the merging machinery -- it
removes objects without removing the relation that consensus and repair exist to resolve.

### 2. Noise check -- two scramble seeds

**Indicative only, and not a calibration.** Two seeds cannot estimate the mean that step 6's floor
procedure needs; what they can show is whether scrambled trees yield recurrent cores at all. The
scramble is the one O50s uses -- each embedding dimension shuffled independently across pathways,
rows re-normalised -- and **the 200 subsamples are the real ones, read back from the cached trees'
`present` bitsets**, so the only thing that differs from the real side is the embedding.

**One thing had to be fixed before these numbers meant anything.** The first scramble side was built
from `embeddings.npy`, which on this universe is stored **RAW**; the cached real trees are built from
the centred sidecar `vectors_leaves_centred.npy`. Scrambling the raw space and comparing it against a
real centred one is a comparison of two transformations, and nothing about it fails loudly -- the
trees build, the candidates count, the table fills. It was caught by the repository's own rule that
analysis may not load embeddings except through the verifying loader, and the discarded side differed
materially: 68,670 and 69,409 candidates against 72,307 and 72,429 on the right matrix. Both sides
were rebuilt, and `build_scramble_trees` now **proves** its matrix by rebuilding cached real run 1
from it and requiring the clusters to match exactly (2,681 clusters) before any scrambling happens.

| bar | real | seed 3001 | seed 3002 | mean | scrambled / real |
|---|---:|---:|---:|---:|---:|
| candidates | 921,420 | 72,307 | 72,429 | 72,368.0 | 7.85% |
| >= 5 runs | 681,363 | 29,199 | 29,475 | 29,337.0 | **4.31%** |
| >= 10 runs | 496,556 | 11,507 | 11,597 | 11,552.0 | **2.33%** |
| >= 20 runs | 294,749 | 3,813 | 3,846 | 3,829.5 | **1.30%** |

By band, the mean of the two seeds against the real count:

| band | >=5 real | scram | ratio | >=10 real | scram | ratio | >=20 real | scram | ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3-5 | 74,763 | 25,007.5 | **33.4%** | 53,204 | 10,920.5 | **20.5%** | 30,004 | 3,784.5 | **12.6%** |
| 6-11 | 289,507 | 4,329.0 | 1.5% | 216,304 | 631.5 | 0.3% | 126,596 | 45.0 | 0.0% |
| 12-24 | 277,819 | 0.5 | 0.0002% | 201,765 | 0.0 | 0.0% | 123,859 | 0.0 | 0.0% |
| 25-49 | 37,874 | 0.0 | 0.0% | 24,243 | 0.0 | 0.0% | 13,551 | 0.0 | 0.0% |
| 50-99 | 1,385 | 0.0 | 0.0% | 1,039 | 0.0 | 0.0% | 739 | 0.0 | 0.0% |
| 100-199 | 15 | 0.0 | 0.0% | 1 | 0.0 | 0.0% | 0 | 0.0 | -- |

Three things, all indicative:

1. **Scrambled embeddings do produce recurrent cores, and only tiny ones.** The two seeds agree
   closely (29,199 against 29,475 at 5 runs), and all but one of their retained cores is in 3-5 or
   6-11. The scramble candidate census stops at 12-24 -- 83 candidates on seed 3001 and 71 on 3002,
   out of 72,307 and 72,429 -- and **exactly one of those 154 clears 5 runs**, on one seed.
2. **The 3-5 band is where noise lives.** At 5 runs a third of the real 3-5 count is matched by
   scrambled data, and even at 20 runs an eighth is. A bar alone would not make a 3-5 core
   trustworthy; this is the band the real floors have always had to gate hardest.
3. **From 12 pathways up the scramble is all but empty, and from 25 up it is exactly empty at every
   bar.** One core out of the 58,674 the two seeds retain between them at the 5-run
   bar reaches 12-24, 0.0002% of the real 277,819; at 10 and 20 runs there are none. So the real cores in 12-24 and 25-49 are not a
   resampling artefact -- the mirror image of the finding above: the bands arm K does find are the
   bands noise cannot reach, and they stop at 50 as well.

### What the bars change, and what they do not

Nothing here rescues the large end. **The bars confirm the ceiling rather than move it**: 20-run
cores stop at 59 pathways, the 100-199 band empties, and 50-99 holds 739 cores out of 294,749. They
also show the ceiling is not noise-driven -- above 12 pathways the scrambled side contributes
nothing at any bar -- so the absence of large recurrent cores is a fact about the data under this
resampling, not about the threshold or the null. And they show a bar is not a cleanup: redundancy per
core is flat across bars and 44 times the gated themes', so arm K's output would still need exactly
the machinery O50s already has.

### Twenty examples each, for reading

Twenty cores of 6 or more pathways drawn at random (seed 20261023) from each of three recurrence
groups, as `name [source]` with the runs-found count, in
`data/experiments/tree_cores_2026-10-23/bars/examples/runs_{5-9,10-19,20plus}.md`. Pools were
163,248 / 178,607 / 264,745 cores.

## Cost, measured

| | |
|---|---|
| step 2 at cover 0.70 | 49 s |
| step 3 at cover 0.70 | 1 min 50 s |
| step 2 at cover 0.50 | ~2 min |
| step 3 at cover 0.50 | ~24 min (4.88M candidates) |
| one Ward tree at the x2 scale (4,431 x 768) | **1.46 s** (1.36 s distances, 0.10 s linkage) |
| scramble trees, seeds 3001-3002 only | **10 min 30 s MEASURED** and 50 MB (estimated ~25 min) |
| steps 2-3 on both scramble sides | **1 min 43 s** for all four runs |
| the three bars: 1a-1d, the noise tables, the examples | **6 min 58 s**, of which 6 min 39 s is 1d |
| the discarded first scramble side, rebuilt on the right matrix | **12 min 13 s** paid twice |
| all sixteen seeds 3001-3010 and 4001-4006 | ~3 h 25 and ~380 MB |

**Two seeds would not solve the floors.** Step 6's procedure needs the ten calibration seeds to
estimate a mean, with a rule-of-three substitution where scrambles never pass. Two would only show
whether scrambled trees yield candidates at all, and on the numbers above no floor can rescue a
population whose entire support distribution is a single point at the construction's minimum.

## Outputs

| what | where |
|---|---|
| cover 0.70 census, candidates, scores | `data/experiments/tree_cores_2026-10-23/{candidates_census,step3}.json`, `candidates.npz`, `scored.npz` |
| cover 0.50, the same four | `.../cover50/` |
| the bars, every table above as data | `.../bars/bars.json` |
| twenty examples per recurrence group | `.../bars/examples/runs_{5-9,10-19,20plus}.md` |
| the two scramble sides, steps 2-3 | `.../bars/scramble/seed0300{1,2}/` |

```sh
uv run scripts/tree_cores.py --candidates              # step 2 at cover 0.70
uv run scripts/tree_cores.py --score                   # step 3
uv run scripts/tree_cores.py --candidates --cover 0.50 --out OUT/cover50
uv run scripts/tree_cores.py --score      --cover 0.50 --out OUT/cover50

# prompt 60. The trees first; then steps 2-3 on each side; then the bars.
uv run scripts/tree_core_bars.py --scramble-trees      # 2 x 200 Ward trees, 10 min, 50 MB
uv run scripts/tree_cores.py --candidates --cover 0.70 \
    --scramble-seed 3001 --out OUT/bars/scramble/seed03001
uv run scripts/tree_cores.py --score --cover 0.70 \
    --scramble-seed 3001 --out OUT/bars/scramble/seed03001
uv run scripts/tree_core_bars.py                       # tasks 1, 2 and 3; 7 min
```

**Two things are deliberately not committed**, both regenerable from the commands above:
`cover50/candidates.npz` (129 MB) and the scramble trees (moved 25 Oct to the permanent cache
`data/cache/scramble_trees_x2_centred/`). Everything else
in `tree_cores_2026-10-23/`, including all of `bars/`, is in the repository.

`--trees` is an override on `tree_cores.py` used by both the cluster loader and the scorer, added for
this prompt; with it absent both resolve the cached real-tree directory exactly as before, and the
6-run smoke test still gives 11,875 pairs and 5,181 distinct candidates.
