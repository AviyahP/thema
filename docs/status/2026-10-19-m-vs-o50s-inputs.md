# Is arm M better than O50s below the top? Inputs for a blind comparison. 20 Oct 2026

**One half of the declared decision rule can be answered now, and M passes it: M's unique themes are
*less* redundant than O50s's, 14.9% near-copies against 20.3%.** The other half — whether they read
coherent — is the reviewer's, and the 120 blind items are written.

**The counterweight is support.** M's unique themes are more weakly supported: **41.0% sit at or
below support 0.02 against O50s's 34.4%**. And **all 4,003 of them come from strata that chose
θ = 0.50 or 0.60** — not one from a θ = 0.70 stratum — so they are exactly what prompt 47's
loosening admitted, nothing else.

Evaluation only; nothing is adopted, and **no theme is judged here.**

| the declared rule | status |
|---|---|
| M-unique read coherent or linked umbrella within 10 points of O50s-unique | **the reviewer's** — 120 items in 11 batches |
| M-unique near-copy share (best J ≥ 0.8) no higher than O50s-unique | **PASS — 14.9% against 20.3%** |

## Populations

| band | O50s unique | O50s all | **M unique** | **M all** |
|---|---:|---:|---:|---:|
| 10-19 | 1,148 | 1,886 | **1,386** | 2,125 |
| 20-49 | 1,288 | 1,645 | **1,732** | 2,085 |
| 50-199 | 309 | 334 | **806** | 831 |
| 200+ | 28 | 29 | **79** | 80 |
| **total** | **2,773** | **3,894** | **4,003** | **5,121** |

A theme is unique to its build if its best Jaccard to any theme of the other build is below 0.9.

**M has 1,230 more themes of 10+ pathways, and 1,230 more unique ones** — the extra themes are
almost entirely *not* recognisable in O50s. Read the other way: **O50s has 2,773 themes with no
close counterpart in M either.** The two builds overlap far less than their shared ancestry
suggests, and in the larger bands they barely overlap at all — of M's 831 themes of 50-199, **806
(97%) have no O50s counterpart at 0.9**, and 79 of its 80 themes of 200+.

## A2. Redundancy

Each theme's best Jaccard to **another theme of the same build whose size is within a factor of
1.5** — so a theme is not called a near-copy of something three times its size.

| band | O50s uniq ≥0.8 | median | O50s all ≥0.8 | median | **M uniq ≥0.8** | **median** | M all ≥0.8 | median |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 10-19 | 19.8% | 0.692 | 21.2% | 0.714 | **16.5%** | **0.667** | 18.4% | 0.706 |
| 20-49 | 21.7% | 0.667 | 22.2% | 0.674 | **16.7%** | **0.480** | 18.4% | 0.483 |
| 50-199 | 18.4% | 0.483 | 18.0% | 0.483 | **9.1%** | **0.469** | 9.4% | 0.469 |
| 200+ | **0.0%** | 0.343 | 0.0% | 0.343 | **5.1%** | 0.437 | 5.0% | 0.438 |
| **overall** | **20.3%** | **0.667** | **21.2%** | **0.688** | **14.9%** | **0.477** | **16.8%** | **0.486** |

**M is less redundant in three of the four bands and overall.** The gap widens with size: at 50-199
M's near-copy share is **half** O50s's (9.1% against 18.4%).

**The one band where M is worse is 200+, and the numbers are small**: 4 of 79 M-unique themes against
0 of 28 for O50s. On a strict per-band reading the rule fails there; on the overall reading it
passes comfortably. **The rule as written says "M-unique themes have a near-copy share no higher than
O50s-unique themes", which is the overall comparison, so I read it as a pass and flag the band.**

One caveat on interpretation. M's median best-J is much lower than O50s's (0.477 against 0.667), and
part of that is arithmetic rather than virtue: M spreads 5,121 themes over the same 5,539 pathways,
so the size-matched neighbourhood of any given theme is more crowded but also more varied. The
near-copy *share* is the robust half of this measure; the median should be read as context.

## A3. Support

Each unique theme's support under its own build's gate — M at its stratum's chosen θ, O50s at 0.70 —
with that stratum's floor.

| band | O50s median | O50s ≤0.02 | **M median** | **M ≤0.02** |
|---|---:|---:|---:|---:|
| 10-19 | 0.0950 | **0.0%** | 0.1500 | **0.0%** |
| 20-49 | 0.0150 | 58.1% | 0.0150 | 58.9% |
| 50-199 | 0.0150 | 61.2% | 0.0150 | **71.0%** |
| 200+ | 0.0200 | 57.1% | 0.0150 | **64.6%** |
| **overall** | **0.0450** | **34.4%** | **0.0506** | **41.0%** |

**M's unique themes are more weakly supported**, and the gap is worst exactly where M gains most
themes: in 50-199, **71.0% of M's unique themes sit at or below support 0.02** against O50s's 61.2%.
Support 0.02 is four runs in 200.

**The 10-19 band is the exception in both builds**: 0.0% at or below 0.02, because that stratum's
floor is **0.030151 in O50s and 0.050251 in M** — both above 0.02, so nothing weaker can get in, and
M's is the stricter of the two. Where the floor is **0.01** — every stratum from 20-39 up, in both
builds — the majority of unique themes sit at or just above it.

**A mechanical check worth recording.** Of M's 4,003 unique themes, **2,617 come from strata that
chose θ = 0.50 and 1,386 from the one that chose θ = 0.60. None comes from a θ = 0.70 stratum.**
That is exactly what should happen if M's extra themes are the loosened threshold's doing and nothing
else, and it means the blind reading is a test of θ = 0.50-0.60 recurrence specifically.

## A1. Blind reading inputs

**120 themes: 15 per band per side, every band had enough**, drawn and shuffled under seed 20261019.
Each carries a random id `T001`-`T120` and nothing else — no build label, node id, theme name or
support — and the member lists are **sorted by pathway name**, so the ordering cannot leak the source
either.

| | |
|---|---|
| items | **120** (60 O50s-unique, 60 M-unique) |
| batches | **11**, `data/experiments/m_vs_o50s_2026-10-19/read_inputs/T_b01.md` … `T_b11.md` |
| lines per batch | 729 to 2,835; no theme split across a batch |
| index | `index.json` — id → size only |
| key | `KEY_DO_NOT_SHARE_m_vs_o50s.json` — id → build, node, size, band, support |

| batch | lines | | batch | lines |
|---|---:|---|---|---:|
| `T_b01.md` | 729 | | `T_b07.md` | 1,368 |
| `T_b02.md` | 2,835 | | `T_b08.md` | 2,553 |
| `T_b03.md` | 2,041 | | `T_b09.md` | 2,025 |
| `T_b04.md` | 2,567 | | `T_b10.md` | 2,384 |
| `T_b05.md` | 2,564 | | `T_b11.md` | 1,396 |
| `T_b06.md` | 2,399 | | | |

`T_b02.md` is 2,835 lines, over the nominal 2,600, because a theme is never split and one item in
that batch is large. The key was written once and **is not read again by this session.**

## What this says

**The redundancy half of the rule favours M, clearly and in the direction that was in doubt.** The
worry was that M's extra themes would be near-copies that only just pass. They are measurably *less*
near-copy than O50s's own unique themes — 14.9% against 20.3% overall, and half O50s's rate in the
50-199 band. Whatever else is true of arm M, its extra themes are not duplicates of each other.

**The support half cuts the other way and is not in the rule.** 41.0% of M's unique themes sit at or
below four runs in 200, against O50s's 34.4%, and 71.0% in the band where M gains most. A theme can
be distinct and still thin.

**So the reading is the whole decision now.** If M's unique themes read within 10 points of O50s's,
both declared conditions hold. If they read worse than that, the rule says O50s stays the base and
prompt 47's size-dependent threshold is recorded as a finding — which is where this already stood.

**Nothing is adopted and no theme was judged here.**

## Reproducing this

```sh
uv run scripts/m_vs_o50s_inputs.py     # 4 s
uv run pytest tests/test_m_vs_o50s_inputs.py
```

Outputs: `read_inputs/T_b01.md`…`T_b11.md`, `index.json`, the key, `redundancy.tsv` (9,015 rows,
both builds, every theme of 10+ with its unique flag), `support.tsv` (6,776 rows, the unique themes)
and `measures.json`. No API calls.
