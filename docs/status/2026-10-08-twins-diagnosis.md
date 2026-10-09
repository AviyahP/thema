# Why near-duplicate themes survive a 0.70 merge. Diagnosis, 8 Oct 2026

Declared 8 Oct. **Diagnosis only — no build was written.** Everything below is read from the cached
`thema_L` and `thema_L_cal8` builds, plus one in-memory re-run of consensus that writes nothing, and
two cost measurements. Reproduce with `uv run scripts/twins_diagnosis.py`.

**The headline corrects something I claimed yesterday.** The 38.6% figure is not a redundancy
measure. **99.0% of `thema_L`'s pairs at Jaccard > 0.7 are nested** — one theme strictly contains the
other — and nesting is what the hierarchy is made of, not duplication. Only **7 pairs** in the whole
build are non-nested overlaps. In the re-gate report I called 66% "the clearest single number against
the `-cal` arms"; that overstated it, and the correct statement is in §1.

## 1. The split

| | `thema_L` | `thema_L_cal8` |
|---|---:|---:|
| themes | 2,815 | 9,609 |
| pairs at Jaccard > 0.7 | 964 | 7,368 |
| **(a) nested** — one strictly contains the other | **954 (99.0%)** | **7,059 (95.8%)** |
| identical member sets | 3 | 98 |
| **(b) non-nested overlapping** | **7 (0.7%)** | **211 (2.9%)** |
| themes in at least one such pair | 1,087 (38.6%) | 6,378 (66.4%) |

So the share of *themes* involved is high (38.6%, 66.4%) while the share of *pairs* that are
genuine duplicates is tiny (0.7%, 2.9%). Those are different quantities and I conflated them
yesterday: a theme counts as "having a near-duplicate" whenever it has a parent or child holding more
than 70% of it, which is a statement about how finely the hierarchy is cut, not about redundancy.

### (a) Nested examples — `thema_L`

| J | larger | smaller | what differs |
|---|---|---|---|
| 0.967 | `n00443` n=61 support 0.950 | `n01548` n=59 support 0.610 | parent adds *enriched in G-protein coupled receptors*, *G protein coupled receptors cluster* to a lipid-metabolism/arachidonate theme |
| 0.964 | `n00479` n=28 support 0.945 | `n00809` n=27 support 0.875 | parent adds *RNA polymerase II transcription initiation surveillance* to a transcription-elongation theme |
| 0.963 | `n02309` n=27 support 0.415 | `n01186` n=26 support 0.735 | parent adds *FGFR1c and Klotho ligand binding and activation* to an FGF/Klotho theme |

These are exactly what a hierarchy should contain: a theme and the same theme plus one more pathway,
at different support. The child is often the *better-supported* of the two (0.735 against 0.415 in
the third row), which is a point in favour of keeping both.

### (b) Non-nested overlapping examples — `thema_L`, all 7 listed in the JSON

| J | A | B | genuinely different content |
|---|---|---|---|
| 0.750 | `n00100` n=14 support 0.995 | `n01671` n=14 support 0.570 | A has *regulation of exit from mitosis*, *APC-Cdc20 mediated degradation of Nek2A*; B has *SCF-beta-TrCP mediated degradation of Emi1*, *Phosphorylation of Emi1* |
| 0.750 | `n01293` n=14 support 0.695 | `n01394` n=14 support 0.665 | A has *negative regulation of systemic arterial blood pressure*, *bradykinin catabolic process*; B has *cGMP biosynthetic process*, *negative regulation of receptor guanylyl cyclase signaling* |
| 0.741 | `n02588` n=24 support 0.360 | `n01408` n=23 support 0.660 | A has *low/high-density lipoprotein particle remodeling*; B has *negative regulation of cholesterol biosynthetic process*, *sterol homeostasis* |

Each pair shares a core and differs at the edges on something substantive — APC/C regulation versus
Emi1 degradation, blood-pressure control versus cGMP signalling. **These are arguably not errors**,
which matters for §3.

### `thema_L_cal8`'s non-nested pairs include a different and worse kind

| J | A | B |
|---|---|---|
| 0.885 | `n04007` **n=2,586** support **0.185** | `n06955` **n=2,452** support **0.050** |
| 0.858 | `n06956` n=1,939 support 0.050 | `n08177` n=1,805 support 0.035 |

Two near-identical 2,500-member themes at support 0.185 and 0.050, both admitted only because the
10+ floor fell from 0.33 to 0.025. This is the redundancy the `-cal` arms really do add, and it is
concentrated in the giant themes rather than spread through the build.

### The 3 identical pairs in `thema_L` should not exist

`consensus.classify` says so in its own comment: *"Identical sets fall to rule 3, where one is
superseded — accepting both would put two nodes with the same members into hasse, which draws no
edge between them and leaves both as roots."* Three pairs in `thema_L` and 98 in `L_cal8` have
identical member sets. §2 explains how.

## 2. Where the 0.70 merge is applied, and why each kind survives

The pipeline order, with the memberships each stage sees:

| stage | memberships it operates on | does 0.70 apply? |
|---|---|---|
| matching / support | run clusters against pooled groupings | yes — `THETA_MATCH`, a *different* knob |
| **completion** | grouping → union of its matched copies, filtered at `INCLUSION_CUT` 0.50 | no |
| **absorption** (`families`) | completed bitsets | **no Jaccard at all** — the twin rule, `TWIN_FRACTION` 0.10 |
| **gate** | family seeds' completed bitsets + support | no |
| **consensus** | **the gated candidates** — post-completion, post-absorption | **yes, `THETA_MERGE` 0.70** |
| **containment** (`hasse`) | consensus's *output* members | no |

So the 0.70 merge runs **once**, on the gated candidate bitsets, before containment. Inside it,
`classify` tests four rules **in this order** (`consensus.py`):

```python
if out_of_a == 0 and out_of_b > 0:        # Rule 1 NESTED  -- returns BEFORE any Jaccard
    return Rule.NESTED, left_is_a
if (strays_b <= stray or out_of_a <= STRAY_FLOOR) and strays_a > stray:
    return Rule.INHERITED, left_is_a       # Rule 2
union = size_a + size_b - bits.count(a & b)
if union and bits.count(a & b) / union >= jaccard:
    return Rule.SUPERSEDED, left_is_a      # Rule 3 -- the actual merge
return Rule.COEXIST, left_is_a             # Rule 4
```

**Why nested pairs survive (kind a): by design, and the Jaccard is never computed.** Rule 1 returns
`NESTED` whenever B is strictly inside A, before control reaches the Jaccard test. A nested pair at
J = 0.99 is treated identically to one at J = 0.05 — both are hierarchy, and `hasse` draws the edge.
This is deliberate and documented. **99% of the pairs in question are in this class, so 99% of the
"near-duplicate" figure is the merge rule working as specified**, not failing.

**Why non-nested pairs survive (kind b): a theme grew after it was accepted, and accepted themes are
never re-compared with each other.** Consensus is greedy over a stack. `_rules_against` tests the
newcomer against *every* accepted theme and drops it if any supersedes it, so at the moment both
members of a pair were accepted their Jaccard was below 0.70. But rule 2 can make an **accepted**
theme grow:

```python
out.members[position] = accepted_block | added     # the theme already on the stack gains members
```

and the loop only ever re-compares *the newcomer* against the stack. **Two themes already side by
side are never compared again after one of them grows.** A pair below 0.70 at comparison time can
therefore be above it in the output — including all the way to identical.

**And growth is live in v0.4, which is not obvious.** v0.4 passes `stray=0.0`, which looks like it
disables rule 2. It does not: the condition is `strays_b <= stray` **or** `out_of_a <= STRAY_FLOOR`,
and `STRAY_FLOOR = 1` is an absolute floor — *"a single member outside is noise at any size"* — that
bypasses the share test entirely. Re-running consensus on `thema_L`'s cached gated candidates
confirms it:

```
accepted 2,815   superseded 90
rules fired: {'nested': 2815, 'inherited': 1290, 'superseded': 90, 'coexist': 0}
themes that GREW after acceptance: 822   (1,392 members gained; median 1, max 40)
IDENTICAL pairs in the output: 3      NON-NESTED >0.70 pairs in the output: 7
of those 10 pairs, how many involve a theme that GREW: 10
```

**All ten anomalous pairs involve a theme that grew.** That is the mechanism, with no residual.

**A correction this forces on an earlier entry.** The v0.4 ablation's `no_stray` arm set `stray=0.0`
and I recorded STRAY as "removed", finding no measurable difference. 1,290 inheritance events still
fire in that configuration. The ablation's *verdict* stands — it compared the baseline against
removing the share rule and found nothing moved — but "STRAY removed" is imprecise: the **share
threshold** was removed and the **one-member floor remains and does the work.** A genuine no-stray
arm would need `STRAY_FLOOR = 0` as well, and has never been run.

## 3. What a merge applied as the very last step would change

Counts only, computed on the cached final memberships: one greedy pass, highest support first,
keeping strict containment as hierarchy and dropping the lower-support member of any non-nested pair
at or above 0.70. No build written.

| | `thema_L` | `thema_L_cal8` |
|---|---:|---:|
| themes before | 2,815 | 9,609 |
| themes after | **2,804** | **9,358** |
| removed | **11 (0.4%)** | **251 (2.6%)** |
| of which non-nested overlaps | 8 | 171 |
| of which identical or equal | 3 | 80 |

**A last-step merge would change almost nothing.** It would remove 11 themes from `thema_L` and 251
from `L_cal8`. It is worth doing for correctness — the 3 identical pairs in `thema_L` are a defect by
the code's own account, and they produce two nodes with the same members that `hasse` cannot order,
leaving both as roots — but it is **not** a fix for the hierarchy's shape. It does not touch the
nested pairs, which are 99% of what the 38.6% figure counts, and it cannot: they are the hierarchy.

The 8 non-nested overlaps it would remove from `thema_L` are the APC/C-versus-Emi1 and
blood-pressure-versus-cGMP pairs in §1(b), which look like real distinctions. On the evidence, a
last-step merge's clear win is the identical pairs; the overlapping ones are a judgement call.

## 4. Cost of the alternative design — estimate only, nothing built

One Ward tree on all leaves as the structure; per-node support = share of the 200 resampled trees
holding a matching node at Jaccard ≥ 0.70 **on present members**; floors calibrated on the existing
scramble trees; unsupported nodes collapsed into their parent, giving a multi-way tree.

**Compute, measured on this machine:**

| step | measured |
|---|---|
| one Ward tree on all 5,559 leaves | **2.4 s**, 3,382 recorded nodes (`min_size` 3, ≤ n/2) |
| load 200 resampled trees | 6.5 s |
| support for one node against 200 runs, via the run's ancestor chain | **3 ms** |
| all 3,382 nodes, real side | **11 s** |
| 12 sides (10 calibration + 2 held out) | **4 min** |
| collapse, export | seconds |
| **compute total** | **≈ 5 minutes** |

**This is about thirty times cheaper than the current pipeline**, and the reason is structural rather
than clever: it scores **3,382 tree nodes** instead of matching a **271,875-grouping pool**. The
existing per-side cost of 126–175 s is almost all pool matching, and this design has no pool.

**One design question the brief leaves open, and it changes what the floor means.** "Calibrate
support floors on the existing scramble trees" has two readings:

- **(i)** keep the real Ward tree as the structure and score its nodes against the *scramble* runs.
  This asks "would real structure recur in noise?" — it will not, so the floors come out very
  permissive and the calibration is close to vacuous.
- **(ii)** build a Ward tree on each scramble's own full data and score *its* nodes against that
  seed's 200 runs. Structure and runs are both scrambled, which is the matched null and the one
  consistent with how every floor in this repo has been calibrated.

(ii) is the right one and costs almost nothing extra — a permutation plus a 2.4 s Ward per seed,
about 30 s for twelve. My 4-minute figure covers either. **I would not run this without (ii)
settled, because (i) would produce floors that pass everything.**

**The real cost is implementation, not compute.** Needed: an adapter that scores arbitrary query
bitsets against a run's recorded clusters restricted to present members (the walk exists inside
`recurrent.score` but is not reachable for external queries); the collapse-into-parent step with a
multi-way tree export; and a correctness proof against the existing matcher on a case where the two
must agree. The floor solver transfers unchanged — `build_10770.solve` takes `(size, support)` rows
and per-node support is exactly that shape.

| | estimate |
|---|---|
| compute | ~5 min |
| new code, tests and the equivalence proof | 2–3 h |
| calibration, build, metrics, report | ~1 h |
| **total** | **3–4 h** |

So it is a cheap experiment to *run* and a moderate one to *write*. It is also the only design
proposed so far that would address the actual shape problem rather than the gate or the merge rule:
collapsing unsupported nodes into their parent produces a multi-way tree directly, with no strict-
containment DAG and therefore none of the 585-child roots, and no near-copies by construction — a
node either survives or is absorbed, so a theme and the-same-theme-plus-one cannot both exist.

## What this means

Three things, in order of how much they change the picture.

1. **The twin problem is much smaller than the 38.6% and 66% figures suggest.** 99% of those pairs
   are parent-child, which is hierarchy. I reported that number yesterday as evidence against the
   `-cal` arms and it does not carry that weight. The genuine duplicates are 7 pairs in `thema_L`
   and 211 in `L_cal8`.
2. **There is a real, small, fixable defect**: 3 identical and 7 non-nested pairs in `thema_L` exist
   because a theme grew after acceptance and accepted themes are never re-compared. A merge applied
   as the last step on final memberships removes them, at a cost of 0.4% of themes. Cheap and
   correct, but not a shape fix.
3. **`stray=0.0` does not disable inheritance**, because `STRAY_FLOOR = 1` bypasses the share test.
   1,290 inheritance events fire in `thema_L`. The `no_stray` ablation's verdict is unaffected but
   its description in `DECISIONS.md` is imprecise, and a true no-stray arm has never been run.

And a negative that is worth stating plainly: **near-copy collapse is not the lever I suggested it
was at the end of the re-gate report.** I wrote that redundancy was the thing to attack next; the
counts here say a merge on final memberships buys 0.4%. If the goal is a navigable hierarchy, the
alternative design in §4 — one tree, collapse unsupported nodes into the parent — attacks the shape
directly and at about a tenth the compute of the current pipeline.

Nothing is frozen. **Aviyah decides.**

Written: `data/experiments/twins/twins.json`, `growth.txt`, `alt_cost.txt`.
