# Exclusion 2, and the rebuild on universe L minus every exclusion. 9 Oct 2026

> **Corrected 9 Oct, after the step-3 evaluation.** `go:GO:0010800` was **excluded against the
> declared rule**: the rule asks whether *neither* the name *nor* the description identifies a theme,
> and its name — *positive regulation of peptidyl-threonine phosphorylation* — identifies a specific
> mechanism. The blind judge excluded it on the description alone. It is marked **"reinstate at next
> rebuild"** in `data/excluded_inputs.tsv` and **`thema_L_x2` keeps it excluded**, so every number
> below stands as measured. Effective exclusions are now **22 (19 in universe L)**: exclusion 1's 17
> plus 5 from exclusion 2.
>
> Also corrected: `btm:M248`, the example quoted in the rule itself, was **judged "yes" by the blind
> judges and stays in** — "Several of them converge on mitotic and genome-maintenance functions".
> The rule decides, not the example.
>
> And the 22.5% churn below is **refined** by the reviewer's breakdown in
> `docs/status/2026-10-09-x2-evaluation.md`: it is concentrated in low-support themes (median support
> 0.045 for new themes against 0.685 for identical ones), and **among themes with support ≥ 0.1, 89%
> reproduce; at ≥ 0.5, 91%.** The bare 22.5% was more alarming than the truth.

Declared before any judging (`DECISIONS.md`). **No external API calls**: stage 2 was judged by
Claude Code subagents. The rebuild is `thema_L_x2`.

**Three results.**

1. **Exclusion 2 removes 6 inputs beyond exclusion 1's 17**, so 23 in total, 20 of them in universe
   L. The mechanical screen returned 172 candidates and the blind judges said "no" to 21 — but 15 of
   those 21 were already excluded, so the marginal yield is small.
2. **The rebuild changes almost nothing structurally and almost everything individually.** Band
   counts shift by tens (8,793 → 8,740 themes) and the giant roots go **8 → 10**. But only **15.0%**
   of the new themes are identical to an old one, 62.5% match at Jaccard ≥ 0.70, and **22.5% are
   new**.
3. **That churn is not caused by the removed members.** Comparing against the old themes with the
   excluded keys projected out gives the same figures to within one theme (1,311 against 1,310
   identical). Removing 20 of 5,559 inputs changed the **trees**, and the theme list moved with them.

## Exclusion 2

### The rule, declared before any judging

> Exclude an input set if **neither its source name nor its generated description identifies one
> specific biological theme.** A theme counts if it is a process, system, pathway, mechanism, cell
> type or tissue, or a shared regulator — a TF, motif or target set counts.

### Stage 1 — the mechanical screen

All unnamed ("TBA") BTMs, plus any set whose description contains *no single*, *no coherent*,
*heterogeneous*, *loosely*, *mixed*, *little more than*, *best read*, *rather than a single*, *grab*,
*miscellaneous* or *uncharacterised*. Run over all **10,770** sets.

| source | universe | candidates | unnamed | hedge only | in L |
|---|---:|---:|---:|---:|---:|
| btm | 346 | **95** | 83 | 12 | 95 |
| go | 7,538 | **63** | 0 | 63 | 38 |
| hallmark | 50 | 0 | 0 | 0 | 0 |
| reactome | 2,836 | **14** | 0 | 14 | 13 |
| **total** | **10,770** | **172** | 83 | 89 | 146 |

Which hedge caught them: *mixed* 34, *heterogeneous* 26, *rather than a single* 25, *loosely* 15,
*best read* 14, *no single* 9, *uncharacterised* 3, *grab* 3, *little more than* 1, *no coherent* 1,
*miscellaneous* 1; 60 were caught as unnamed only.

### Stage 2 — blind judging by Claude Code subagents

Ten subagents, up to 18 sets each, against `rubric5_exclusion2.md`. **Judges saw only the name and
the full description** — no genes, no cluster or theme data, none of the reviewer's verdict files,
and they were told not to read any other file in the repository. The batches were checked before
dispatch for node ids, Jaccards and verdict labels; the only hits were ordinary English (*"under the
same regulatory umbrella"*, *"these support antigen recognition"*).

Validation: **172 of 172** verdicts parsed, no malformed lines, no duplicates, nothing missing.

| | |
|---|---:|
| candidates judged | 172 |
| **"no" verdicts** | **21** |
| of those, already excluded by exclusion 1 | 15 |
| **new exclusions** | **6** |

### Counts by source

| source | "no" | in L | new beyond exclusion 1 |
|---|---:|---:|---:|
| btm | 17 | 17 | **2** |
| go | 4 | 1 | **4** |
| **total** | **21** | **18** | **6** |

### The 6 new exclusions, with the deciding sentence

| key | name | in L | deciding sentence |
|---|---|---|---|
| `btm:M137` | TBA | **yes** | "best read as a broad housekeeping module supporting gene expression and genome maintenance, mixing chromatin regulators with unrelated membrane and metabolic enzymes" |
| `btm:M72.1` | TBA | **yes** | "A mixed group of broadly expressed regulators that keep housekeeping functions of the cell running." |
| `go:GO:0009791` | post-embryonic development | no | "covers everything between the end of embryogenesis and the mature organism, with genes spanning morphogen signalling, chromatin, apoptosis, metabolism and DNA repair" |
| `go:GO:0010800` | positive regulation of peptidyl-threonine phosphorylation | **yes** | "The contributors here are heterogeneous rather than a single cascade, spanning receptor signalling, MAPK1, WNK3 cotransport control and ubiquitin and immunity components." |
| `go:GO:0044093` | positive regulation of molecular function | no | "a broad regulatory grouping for processes that switch on or amplify the activity of another molecule rather than a single coherent route" |
| `go:GO:0065009` | regulation of molecular function | no | "a broad regulatory category covering any process that raises or lowers a molecular function, and rather than a single route it gathers the cell's tuning machinery" |

The other 15 "no" verdicts fell on sets already carrying exclusion 1 — M125, M153, M211, M218, M221,
M241, M246, M32.5, M41.0, M41.1, M41.3, M70.0, M72.0, M72.2, M98.1. **Their deciding sentences are
an independent check that exclusion 1 picked the right sets**, since these judges saw no genes and
had never seen the exclusion-1 list. Full text in `data/experiments/exclusion2/list.txt`.

### Borderline calls

**(a) Two exclusion-1 sets the blind judges said *yes* to.** They stay excluded regardless, as the
rule declares, but the disagreement is the honest kind to record:

- **`btm:M184.1`** — judge: *"Its clearest core is a JNK pathway assembly: a mixed-lineage kinase of
  the MAP3K family together with a JNK-interacting scaffold protein organises upstream kinases into
  a complex."* The reviewer had already flagged this one as borderline-but-inside-the-rule ("names a
  JNK core"). A judge reading only the description finds the JNK core and keeps it.
- **`btm:M233`** — judge: *"What they share is a bias toward developmental patterning and
  tissue-specific differentiation programmes, with BMP4 as the signalling anchor."* Also flagged
  borderline by the reviewer ("names a loose shared bias").

So **2 of the 17 exclusion-1 sets would not have been excluded by exclusion 2's rule.** Exclusion 1's
criterion was the *first sentence*; exclusion 2's is the whole name-and-description. Both sets open
by hedging and then name something. Nothing is changed — the declared rule says exclusion 1 stands —
but if the two rules are ever reconciled, these are the two sets where they disagree.

**(b) The 4 GO exclusions deserve a second look**, because GO sets have real names, so a "no" means
the **name** was judged not to identify a theme either:

- `go:GO:0044093` *positive regulation of molecular function* and `go:GO:0065009` *regulation of
  molecular function* — these are GO's top-level regulatory categories. Calling them "not a theme"
  is defensible under the rule and is also the kind of call a biologist might contest.
- `go:GO:0009791` *post-embryonic development* — a real developmental concept, excluded for breadth.
- `go:GO:0010800` *positive regulation of peptidyl-threonine phosphorylation* — the one that **is**
  in L. Its name is a specific molecular event; the judge excluded it on the description, which says
  the contributors are heterogeneous. This is the single call most worth reviewing, because the name
  arguably does identify a mechanism.

Only `go:GO:0010800` of the four is in universe L, so three of the four have no effect on this
rebuild at all.

## The rebuild: `thema_L_x2`

Universe L minus all 23 exclusions: **5,539** pathways (from 5,559 — 20 of the 23 were in L).
Exclusions applied **before** the summary rule, because dropping an input can turn a pathway that
was internal into a leaf.

Settings are `thema_L_repair`'s exactly, and nothing else was changed: Ward, 200 runs, **cal8 floors
reused** (carrying the existing reuse note), repair fixes 1 and 2, chain collapse at **0.90** with
the current survivor rule.

```
real side: 99,951 candidate themes from 5,539 pathways (127s)
floors from regate/floors_L_cal8.json (... || floors: cal8, calibrated on universe 10,770,
                                        reused after the 17-BTM drop)
REPAIR, collapse share 0.9: 9,574 -> 8,740
  fix 2: 640 absorbed in 2 rounds; 474 kept a second support
  fix 1: 194 dropped (58 identical, 136 non-nested) in 2 rounds
  stale pairs before 324, after 0 (asserted)
themes 8,740  roots 121  multi-parent 63.9%  effectively unplaced 0
```

**The floors reuse note propagated automatically** into the new manifest's `floors_source`, which is
what the 9 Oct mechanism was for — nobody had to remember.

**One digest check did fire, and correctly.** My first attempt recorded `universe_digest` as the
digest of the *reduced* universe, and `universe.load_embedded` refused the artifact: *"claims
universe 2bf54077a306b856 but pathways.tsv now gives c54319cdfbbe9eb7"*. That field asserts that the
**source table** has not moved, which is a different claim from "these are the keys". The fix was to
record it correctly — the source digest in `universe_digest`, the reduced one in
`universe_digest_after_exclusions` — **not to add an override.** This does not contradict the 9 Oct
finding that no check guards the floors: that remains true, and is why the floors reuse is recorded
in four places.

## Comparison with `thema_L_repair`

### Themes per size band

| band | `thema_L_repair` | `thema_L_x2` | delta |
|---|---:|---:|---:|
| 3–5 | 483 | 524 | **+41** |
| 6–10 | 2,121 | 2,100 | −21 |
| 11–20 | 4,365 | 4,287 | **−78** |
| 21–50 | 1,568 | 1,550 | −18 |
| 51–100 | 214 | 229 | **+15** |
| 101–300 | 28 | 34 | **+6** |
| 301–1000 | 5 | 6 | +1 |
| 1001+ | 9 | 10 | +1 |
| **total** | **8,793** | **8,740** | **−53** |

The middle improves slightly — 51–100 up 15, 101–300 up 6 — and the 11–20 band loses 78. Small
movements on an 8,700-theme build.

### Roots over 1,000 members

| | roots | over 1,000 | sizes |
|---|---:|---:|---|
| `thema_L_repair` | 124 | **8** | 2614, 2586, 2527, 2261, 2138, 1751, 1444, 1047 |
| `thema_L_x2` | 121 | **10** | 2673, 2522, 2366, 2304, 2047, 2044, 2042, 1433, 1245, 1187 |

**The giants got worse, not better: 8 → 10.** The largest is slightly larger (2,673 against 2,614)
and two more themes crossed 1,000. Excluding incoherent inputs did not dissolve the bags.

### Theme-by-theme mapping

`data/ontology/v0.4-leaves/thema_L_x2/match_to_repair.tsv`, one row per new theme, with both a raw
and a projected comparison.

| | raw | projected |
|---|---:|---:|
| **identical** to an old theme | **1,310 (15.0%)** | 1,311 (15.0%) |
| not identical, Jaccard ≥ 0.70 | 5,465 (62.5%) | 5,466 (62.5%) |
| **new** (nothing at 0.70) | **1,965 (22.5%)** | 1,963 (22.5%) |

"Projected" compares against the old member sets with the excluded keys removed — what "unchanged
apart from losing an excluded input" means. **The two columns are the same to within one theme.**

**So the churn is not the excluded members. It is the trees.** Removing 20 of 5,559 inputs (0.36%)
changes every Ward tree over that universe, and 22.5% of themes have no counterpart at Jaccard 0.70
in the build they replace. The band structure is reproducible to within tens of themes; the
individual theme list is not.

That is a **stability** observation, not an argument against the exclusion, and it was not
measured before. It bears on how much any single build's theme list should be trusted: the shape
survives a small perturbation of the universe, and the specific themes largely do not. Between-half
stability has been measured at 82–85% at Jaccard 0.70 — that is the same build's two halves; this is
two universes differing by 0.36%, and it gives 77.5% at the same threshold.

## The containment claim I was wrong about

Recorded here because the claim appeared in a status file and could have discouraged a rule on a
false ground. I wrote that a chain-survivor rule keeping the higher-support **child** instead of the
containing **parent** would break containment. The reviewer disputed it. **The reviewer is right.**

Tested over the **341** edges in [0.85, 0.90) where the child's support exceeds the parent's — the
edges such a rule would act on. Deleting the parent and keeping the child always leaves a node set
over which `hasse` produces a **valid strict-containment DAG**. Re-stacking is what both repair fixes
already do. So "breaks containment" was wrong.

**What the test does show — a real cost, but not that one:**

| | |
|---|---:|
| edges where the child's support is higher | 341 |
| of those, the parent has another child **not** inside the surviving child | **241 (70.7%)** |
| of those, the parent has no parent either, so that sibling is **orphaned to root** | 7 |
| members only the parent held, which lose their grouping at that level | median 3, max 14 |

Concrete cases:

- delete `n00504` (50, support 0.940), keep `n00001` (44, **1.000**) — one sibling of `n00001` is
  not inside it and must re-parent upward; 6 members only `n00504` held lose their level, including
  *cell migration involved in kidney development*.
- delete `n03987` (27, 0.150), keep `n00183` (24, **0.985**) — one sibling re-parents; 3 members
  lose their level.
- delete `n02867` (28, 0.280), keep `n00184` (25, **0.985**) — same shape.

**No rule is changed.** The chain threshold and the survivor rule are not decided and come after the
re-evaluation, per the plan.

## What this means

**Exclusion 2 was worth running and its marginal yield is small.** 172 candidates, 21 "no", 15 of
which exclusion 1 already caught. The 6 new ones are 2 housekeeping BTMs and 4 broad GO categories,
and only 3 of the 6 are in universe L. If the aim was to remove the inputs that make incoherent
themes, exclusion 1 did most of that work.

**The independent confirmation is the more valuable output.** Judges who saw no genes, no clusters
and no prior verdicts reached "no" on 15 of the 17 exclusion-1 sets from the description alone — and
the 2 they kept are exactly the 2 the reviewer had already flagged as borderline. Two different
criteria, applied blind, agreeing on 15 of 17.

**The rebuild tells us something nobody asked for.** The exclusions did not fix the giants (8 → 10)
and barely moved the bands, but they reshuffled 22.5% of the themes — and the projection test shows
that is the trees moving, not the members leaving. Any claim about a specific theme in a specific
build should be read with that in mind.

Nothing is frozen. **Aviyah decides.**

Written: `data/experiments/exclusion2/` (candidates, all 172 verdicts, the full list, the
validation, the containment test), `data/ontology/v0.4-leaves/thema_L_x2/`
(build, manifest, `match_to_repair.tsv`, `browse.html`), and the 6 new rows in
`data/excluded_inputs.tsv`.
