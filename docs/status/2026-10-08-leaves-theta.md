# Recurrence threshold for the middle and top: MS is the only qualifying arm, and it gains almost nothing. 8 Oct 2026

Declared verbatim in `DECISIONS.md` before any build. Branch `leaves-2026-10`. Exploratory.
`v0.3`, `v0.4` and `thema_L` untouched; new directories `thema_L_M5` and `thema_L_MS`.

**Confirmed before starting**, as asked: `THETA` is split into `THETA_MATCH` (recurrence matching
and support) and `THETA_MERGE` (merging), and with both at 0.70 the byte-identity test passes — all
four tables identical to the frozen `recurrent_dag_10770`. Arm L also reproduces `thema_L` byte for
byte after the split, which is the tighter check of the two.

**Result.** Neither arm restores the middle.

- **M5** (0.50 everywhere) does create mid-sized themes — **63** of 60–800 members against
  `thema_L`'s 23 — but it **fails the recall condition** decisively, and the reason is structural:
  at `THETA_MATCH` 0.50 **no support floor at all** controls FDR for themes of 3–6 members, so the
  build has **zero themes of 3–5 members**.
- **MS** (0.70 below 50 members, 0.50 at or above) **meets every condition** the rule names, and
  delivers **25** themes of 60–800 against 23. That is +2.

So the reviewer's diagnostic is right about where the structure is, and wrong about what lowering
the threshold buys: the mid-sized clusters do recur at 0.5, but almost none of them survive the rest
of the pipeline, and lowering the threshold globally destroys the small end.

## One correction to the brief's description of the change

The brief says `THETA_MERGE` governs "absorption + consensus". **Absorption does not use a Jaccard
threshold at all.** `recurrent.families` groups by the twin rule — a variant may differ from its
seed by `TWIN_FRACTION` (0.10) of the seed's members — so there is no absorption threshold for the
new constant to set. `THETA_MERGE` reaches consensus only. That is recorded in `v04.py` beside the
constant, and it means the split is narrower than the brief implies: `THETA` only ever did one job,
which is why byte identity was never really at risk.

The per-size arm needed no change to the frozen matcher. `prepare()` does everything that does not
depend on the threshold — the dedup and the eligibility matrix — so the grouping pool is identical
whatever the threshold is, and a grouping's support depends only on the threshold and the grouping
itself. MS therefore runs **one `prepare` and two `score` passes** over the same pool and takes each
grouping's support from the pass matching its own size. That is exactly a per-size threshold, costs
a second `score` rather than a second `prepare`, and touches nothing frozen.

## Floors: the declared fallback was needed, and it worked

| arm | calibration | held-out | overall FDR | per stratum | verdict |
|---|---|---|---|---:|---|
| **MS**, 3 seeds | 3001–3003 | 4001 | 0.00241 | **5-5 at 0.0297** | over the 0.02 cap |
| **MS**, 10-seed fallback | 3001–3010 | 4001+4002 | **0.00138** | worst **5-5 at 0.01366** | **PASSES** |
| **M5**, 3 seeds | 3001–3003 | 4001 | 0.0 / 0.00846 on the two rated strata | **3-3, 4-4, 5-5, 6-6 admit nothing** | see below |

MS's floors: 3-3 0.83, 4-4 0.915, **5-5 0.505**, 6-6/7-9/10+ 0.33.
M5's floors: **3-3 None, 4-4 None, 5-5 None, 6-6 None**, 7-9 0.44, 10+ 0.33.

**The 10-seed fallback fixed exactly what three seeds could not.** `thema_L`'s unresolved 5-5
failure, reported yesterday at 0.0297, is the same stratum — and MS shows why it failed: three
scramble sides average about six null discoveries in that stratum, where ten average thirty, and
the FDR estimate from six counts is too noisy to solve against. **This is a reusable finding:
`thema_L`'s own failing check would very likely pass on ten seeds.** I have not run that, because
`thema_L` is a declared output of yesterday's experiment and re-calibrating it now would be changing
a published build after seeing a result.

**M5's `None` floors are the headline, not a technicality.** A stratum with no solved floor admits
nothing, so M5 has no themes below 7 members. It is not that the floor came out high — it is that
**no support cut-off in those strata reaches FDR ≤ 0.01 at `THETA_MATCH` 0.50.** Apply `thema_L`'s
floors to M5's own side and scramble to see how far off it is:

| stratum | floor | real | null | held-out FDR |
|---|---:|---:|---:|---:|
| 3-3 | 0.84 | 260 | 273.0 | **1.05** |
| 4-4 | 0.925 | 197 | **769.0** | **3.90** |
| 5-5 | 0.425 | 277 | 140.0 | **0.505** |
| 6-6 | 0.33 | 505 | 129.0 | **0.255** |
| 7-9 | 0.33 | 1,213 | 52.0 | 0.043 |
| 10+ | 0.33 | 2,840 | 0.0 | 0.0 |
| **overall** | | | | **0.2576** — 26× the cap |

At stratum 4-4 the scrambles produce **769 recurrent groupings against the real side's 197**: more
false than true. So at 0.50, scrambled data recurs *more* than real data does for small clusters.
The reviewer's diagnostic measured clusters of 60–2,000 members, where scrambles recur at neither
threshold; it does not extend to the small end, and 0.50 there is below the noise floor.

## Themes per size band

| arm | themes | **60–800** | 3–5 | 6–10 | 11–20 | 21–50 | 51–100 | 101–300 | 301–1000 | 1001+ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `thema_L` | 2,815 | 23 | 494 | 1,251 | 751 | 279 | 31 | 3 | 2 | 4 |
| **M5** | 3,314 | **63** | **0** | 1,153 | 1,389 | 674 | 74 | 13 | 5 | 6 |
| **MS** | 2,816 | 25 | 494 | 1,252 | 750 | 280 | 30 | 4 | 2 | 4 |

MS is `thema_L` to within a handful of themes in every band. That near-identity is the experiment's
main negative result, and the next section shows it is genuinely the threshold and not the
calibration.

### Separating the threshold from the calibration

MS used ten calibration seeds and `thema_L` used three, so an MS-against-L comparison confounds the
threshold with the calibration. Cross-applying each arm's floors to each arm's cached side settles
it — gated candidates, before consensus:

| side (its threshold) | floors applied | gated | 60–800 |
|---|---|---:|---:|
| L | L's | 2,905 | 26 |
| L | MS's | 2,904 | 26 |
| MS | L's | 2,909 | **31** |
| MS | MS's | 2,908 | **31** |
| M5 | L's | 5,292 | 76 |
| M5 | MS's | 5,289 | 76 |

**The calibration is worth 1–3 candidates; the threshold is worth everything else.** So MS's +5
gated candidates in 60–800 (26 → 31) is the real effect of the per-size threshold, and it is small.

## Gene coherence — the check that a new mid-sized theme is not a bag of unrelated pathways

Share of member pairs sharing at least one gene, against **size-matched** random sets (the null has
to be size-matched: a 200-member random set has far more sharing pairs than a 5-member one). 150
themes per band, seed 0, 20 null draws each.

| band | `thema_L` | M5 | MS | null |
|---|---:|---:|---:|---:|
| 3–5 | 24.7× | *(no themes)* | 25.1× | 0.029 |
| 6–10 | 20.1× | 19.2× | 20.6× | 0.029 |
| 11–20 | 17.1× | 17.1× | 18.0× | 0.029 |
| 21–50 | 12.4× | 13.3× | 12.6× | 0.029 |
| 51–100 | 7.8× | 8.3× | 7.7× | 0.029 |
| 101–300 | 5.5× | 4.9× | 6.1× | 0.029 |
| 301–1000 | 3.4× | 3.6× | 3.2× | 0.029 |
| **1001+** | **1.4×** | **1.4×** | **1.4×** | 0.029 |

**The mid-sized themes M5 and MS add are coherent**: 51–100 at 8.3× and 101–300 at 4.9× for M5, both
far above chance. So the new middle is not noise — which matters, because it means M5's problem is
its small end and its FDR, not the quality of the themes it gains.

**Every arm fails the rule's coherence condition at the 1001+ band, including `thema_L` itself**
(1.4× against the 3× bar). Those are the 4–6 giant root themes, and in gene terms they are close to
random sets. Read literally, condition (3) therefore disqualifies every arm and the reference, so it
cannot discriminate between them; read as a condition on the bands where the arms differ, it is met
everywhere. **I have not reinterpreted the rule** — both readings are stated, and the 1001+ result
is reported as the finding it is: the top of the hierarchy is not gene-coherent in any arm.

## Inclusion among themes larger than 60 members

| arm | themes > 60 | median member inclusion | share below 0.7 |
|---|---:|---:|---:|
| `thema_L` | 26 | 0.979 | 15.5% |
| **M5** | 66 | **0.914** | **24.4%** |
| MS | 27 | 0.977 | 14.3% |

M5's large themes are measurably looser: a quarter of their members appear in under 70% of the
copies that could have held them, against 15% for the other two. Its extra mid-sized themes are
coherent in genes but less settled in membership.

## Curated recall and precision, TEST half

Secondary (`is_a`-only) closure, as the brief specifies, with the primary closure beside it.

| arm | re 3–10 | re 11–50 | re 51–200 | go 3–10 | go 11–50 |
|---|---|---|---|---|---|
| *secondary* | | | | | |
| `thema_L` | .180/.028 | .281/.041 | .000/.000 | .037/.012 | .007/.003 |
| **M5** | **.082**/.019 | .281/.025 | **.091**/.023 | **.013**/.006 | .014/.002 |
| **MS** | .186/.028 | .281/.041 | **.091**/.029 | .035/.011 | .007/.003 |
| *primary* | | | | | |
| `thema_L` | .245/.032 | .135/.029 | .000/.000 | .064/.025 | .018/.012 |
| **M5** | **.160**/.026 | .154/.020 | .000/.000 | **.031**/.015 | .026/.010 |
| **MS** | .250/.034 | .135/.029 | .000/.000 | .061/.024 | .018/.012 |

Paired deltas against `thema_L`, the rule's condition:

| arm | cell | delta | 95% CI | |
|---|---|---:|---|---|
| **M5** | reactome 3–10 (primary) | **−0.085** | [−0.132, −0.047] | **worse beyond margin** |
| **M5** | go 3–10 (primary) | **−0.033** | [−0.049, −0.016] | **worse beyond margin** |
| **M5** | reactome 3–10 (secondary) | **−0.098** | [−0.149, −0.052] | **worse beyond margin** |
| **M5** | go 3–10 (secondary) | **−0.024** | [−0.039, −0.011] | **worse beyond margin** |
| MS | every 3–10 and 11–50 cell | −0.003 to +0.006 | CIs straddle or touch 0 | **no difference** |

M5 loses the 3–10 band because it has no themes of 3–5 members. Both arms gain the `re 51-200` cell
(0.091 against 0.000 in the secondary closure) — one more curated set recovered — which is the one
place the mid-size themes show up in the curated score at all.

## Shape, stability, named case, cost

| | `thema_L` | M5 | MS |
|---|---|---|---|
| themes | 2,815 | 3,314 | 2,816 |
| roots | 40 | 96 | 45 |
| median root size | 12 | 12 | 11 |
| largest roots | 2392, 2145, 2030, 1289 | 2417, 2144, 1966, 1963 | 2217, 2144, 2005, 1336 |
| multi-parent | 36.9% | 38.4% | 36.8% |
| effectively unplaced | 218 | 134 | 242 |
| **between-half stability** (θ≥0.7, worse direction) | 82.5% | **87.5%** | 82.6% |
| RTK best gene Jaccard | 0.244 (196 members) | 0.250 (43) | **0.266** (179) |

**M5 is the most stable arm**, by 5 points — because it has no small themes, and small themes are
the unstable ones. That is a real property and not an artefact, but it is stability bought by
deleting the band the curated sets mostly live in.

**RTK** improves slightly in MS (0.266 against 0.244) and M5's best match is a much smaller theme
(43 members). **There is still no clean RTK theme in any arm.**

**Cost**, measured on this machine (`nice`, one job at a time):

| | real side | scramble side | build |
|---|---|---|---|
| `thema_L` / MS small groupings (θ 0.70) | 117–126 s | ~165 s | 12 s |
| M5 (θ 0.50) | 138 s | ~165 s | 19 s |
| MS (two `score` passes) | 204 s | ~300 s | 12 s |

M5's whole calibration was 839 s; MS needed the 10-seed fallback, 13 sides, about 57 min. Peak RAM
9.9 GB for MS's main build, 5.1 GB for M5's.

## Example themes

The mid-sized themes are legible. From MS, 51–100 members: *7-methylguanosine mRNA capping; viral
protein processing; regulation of viral entry into host cell; transport of virus* (56, GO 10 +
Reactome 46); and *mitochondrial cluster; pyruvate decarboxylation to acetyl-CoA; L-leucine
catabolic process* (60, four sources). From `thema_L`, 51–100: *heparan sulfate proteoglycan
biosynthetic process; chondroitin sulfate proteoglycan catabolic process; protein O-linked
glycosylation via mannose* (59, GO 11 + Reactome 48). These are cross-database and coherent.

**A flaw specific to M5**, visible in the examples: its 301–1000 band holds three themes of 840, 754
and 414 members that all begin with the same members — *E2F1 targets (Q3); E2F1 targets (Q4); cell
cycle (III); nuclear pore complex* — i.e. redundant nested variants of one theme at different
granularities. Lowering the matching threshold makes more groupings match, so more overlapping
families survive as separate themes, and consensus at 0.70 does not merge them. M5's higher theme
count is partly this duplication, not only new structure. Full examples:
`data/experiments/leaves_theta/theta_report.json`.

## The decision rule, applied

> prefer the arm with the most themes of 60–800 members, among arms that meet ALL of: FDR within
> caps; 3–10 and 11–50 recall not worse than `thema_L` by >2 points (CI excluding 0); gene coherence
> ≥3× random in every band.

| arm | 60–800 themes | FDR within caps | recall not worse | coherence ≥3× every band |
|---|---:|---|---|---|
| `thema_L` | 23 | 5-5 at 0.0297, unresolved | *(reference)* | **no** — 1001+ at 1.4× |
| **M5** | **63** | **no** — four strata have no floor; borrowing L's gives overall 0.2576 | **no** — four cells worse | **no** — 1001+ at 1.4× |
| **MS** | 25 | **yes** — 10-seed fallback, worst 0.01366 | **yes** | **no** — 1001+ at 1.4×; yes in every band where the arms differ |

**MS is the only arm that meets the FDR and recall conditions.** On the literal reading of the
coherence condition no arm qualifies, because the reference fails it too; on the reading where it
applies to the bands the arms differ in, MS qualifies and M5 does not.

**Either way MS is the arm the rule selects, and what it buys is 25 themes of 60–800 against 23.**

## What this means

The brief's premise — that `THETA` 0.70 deletes the middle — is **half right, and the half that is
wrong matters more**. Mid-sized clusters really do recur at 0.5 and not at 0.7, and the themes you
get by admitting them are gene-coherent (51–100 at 8×, 101–300 at 5×). But:

1. **Lowering the threshold only for large clusters recovers almost nothing** (+5 gated candidates,
   +2 final themes). The mid-sized clusters that now match are then removed by the rest of the
   pipeline — absorbed into families, merged by consensus, or failing their stratum's floor — so
   matching was not the binding constraint.
2. **Lowering it everywhere cannot be calibrated.** At 0.50 the scrambles recur more than the real
   data for small clusters, overall FDR 0.2576 against a 0.01 cap, so the small strata get no floor
   and the band the curated sets live in disappears.

The middle of this hierarchy is thin because the Ward trees on these vectors do not contain many
mid-sized clusters that survive resampling *and* are distinguishable from scrambled structure —
not because the matching threshold is set too high. That is consistent with the leaves experiment's
finding that only 8.5% of curated summaries have any theme recreating them, and with the reviewer's
§2c mechanism: general pathways cluster with general pathways, so there is no middle level to find.

If the middle is the goal, the evidence now points at the clustering or the vectors, not at this
threshold. **Aviyah decides.** Nothing is frozen, and `thema_L` is unchanged.

Written: `data/experiments/leaves_theta/theta_report.json`, `scores_test_primary.json`,
`scores_test_secondary.json`, `cross_applied_floors.txt`, `M5_cannot_borrow_L_floors.txt`,
and the builds under `data/ontology/v0.4-leaves/`.
