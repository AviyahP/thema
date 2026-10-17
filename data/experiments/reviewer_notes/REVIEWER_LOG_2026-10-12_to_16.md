# THEMA reviewer log, 12-16 Oct 2026

This log is for ccode and for future reference, including writing the paper. It summarises what was decided, tested and learned between 12 and 16 Oct 2026, and points to where everything lives.

Where things live:

- **Reviewer files (on the Mac):** `data/experiments/`
- **Prompts:** `data/experiments/reviewer_notes/PROMPT_31..38.md`
- **ccode status notes:** `docs/status/`
- **Declarations:** `DECISIONS.md`
- **Shorter per-topic notes:** the claude.ai project, docs named `claude/thema-*.md`.

## Conventions used throughout

- All LLM work (namers, readers, judges) ran as in-session subagents: no API spend, and evaluation only. No LLM judgement, pathway name or gene enters construction.
- Every test was pre-registered (PREREG file) before any judging. Post-hoc changes are labelled as such.
- Answer keys (`KEY_DO_NOT_SHARE*`) stay on the Mac and are never shown to judges. They are gitignored.
- ccode never commits. It leaves `docs/status/commit-*.sh` scripts, which Aviyah runs.
- Working branch: `leaves-2026-10`. `main` is stale.

---

## 1. Timeline

| date | what happened |
|---|---|
| **12 Oct** | Reviewer handoff to ccode covering 10-12 Oct (`HANDOFF_2026-10-12.md`); c85 confirmed as working version; sibling merge rule (J ≥ 0.6 & md ≤ 2) **superseded**; J ≥ 0.5 merge simulation; **overlap-arm spec** (O50) declared; prompt 31 (freeze c85 + build overlap arm); home-fit test pre-registered |
| **13 Oct** | Home-fit result (NOISE, but confounded control); HiDeF vs c85 evaluation; **O50 evaluated: C1, C3, C4, C5 pass, C2 fails on 1 pathway** (accepted); single-cell facets pilot designed (not run) |
| **14 Oct** | Prompt 32: **O50 adopted and frozen** (`data/ontology/frozen/working-O50-2026-10-14/`, tag `thema-O50-2026-10-14`); offline naming pipeline; N1 namer run started |
| **15 Oct** | N1 complete; S1 sample check; lite selection and dedup gave the official names; landing preview on O50 (prompts 33 and 35); naming style pilot; **areas layer**: prompt 34 (rec) failed, prompt 36 (rec2) failed, giant-drop reading, C6 intruder test, prompt 37 (rec2fix) failed on 63 roots; **giants reading** |
| **16 Oct** | Reassessment: the O50 giants are mostly wide themes; 184 small roots analysed; blind top-level comparison of O50 vs O50 + areas; old 8 Oct matching diagnostic recalled; areas formalised as one recursive operator; **prompt 38 (rec3)** pasted to ccode |

---

## 2. The ontology build: from c85 to O50

### 2.1 Why a single in-build overlap rule (12 Oct)

The build used to carry several cutoffs on the same measure, chosen at different times:

- consensus same-theme J ≥ 0.70;
- stale-merge J ≥ 0.70;
- chain collapse at share ≥ 0.85, applied after the build;
- a proposed post-hoc sibling merge at J ≥ 0.6 & md ≤ 2.

**The sibling merge rule's precision fell under stricter labels:**

| labels | precision |
|---|---|
| names plus samples | 84% |
| name-blind | 70% |
| full lists | 63% |

- Judge calibration dominated: twin share per judge ranged 23-62%.
- No label-free feature reached AUC 0.70.
- Result: **superseded**.

**Simulation of merging siblings at J ≥ 0.5** (`reviewer_eval_x2_2026-10-09/REPORT_merge_J05.md`):

- **Removal:** complete linkage removes 21% of themes. Single linkage chains (a 31-theme NF-kB group) and is rejected.
- **Order dependence:** 839 merged unions then fall within 0.85 of a parent, so the result depends on the order of the passes.
- **Structure:** multi-parent structure survives, 51% → 38%.

**Aviyah's conclusion:** post-hoc passes are incoherent. The rule belongs inside the algorithm: one cutoff for non-nested overlap and one for nesting, iterated together to a fixed point. It was to be tested on a branch, as a real merge (supersede), not as a flag.

### 2.2 The overlap-arm spec (O50), declared 12 Oct

- **Starting point:** the c85 configuration exactly.
- **One cutoff, 0.50:** the same-theme cutoff `T_same` = 0.50 is used both in consensus and in the stale pass.
- **Matching unchanged:** `theta_match` (recurrence) stays at 0.70.
- **Joint fixed point:** chain collapse at 0.85 and stale merge alternate until neither changes anything.
- **Label-free basis of 0.50:** the shared part is at least as large as the two unique parts together.
- **Controls:**
  - a harness proof (0.70 without the loop reproduces c85 byte-identically);
  - O70 as a control;
  - O60, report only.
- **Criteria:**
  - C1: no violating pairs remain;
  - C2: no pathway loses every home under 1,000 members;
  - C3: ≥99% of removed c85 themes have a counterpart at J ≥ 0.5;
  - C4: plausibility no worse than c85;
  - C5: blind usefulness, which O50 must win.

### 2.3 O50 result (13 Oct)

| | c85 | O50 |
|---|---|---|
| themes | 8,251 | **4,602** |
| giants (over 1,000 members) | 10 | **4** (2,332 / 2,018 / 2,015 / 1,412) |
| non-nested pairs at J ≥ 0.5 | 9,138 | 0 |
| multi-parent share (giants excluded) | 51% | 37% |
| pathways with 2+ distinct homes | 79% | 66% (HiDeF: 24%) |

- **O70 is byte-identical to c85,** so every change comes from the cutoff alone. The joint loop is correct but has no effect on its own.
- **C1:** pass.
- **C2:** fails on 1 pathway, btm:M205 (an untitled BTM mixing NF-kB and BMP/TGF-β). **Accepted by Aviyah as an exception.**
- **C3:** pass, 99.64%.
- **C4:** pass. 112 not-ok themes vs 195 in c85; 97.57% ok. Of the 858 new themes, 845 are ok.
- **C5 (120 pathways, blind):** **O50 preferred 87 vs 33** (72.5%, p = 9e-7). It keeps the same contexts without the near-duplicates. In about 28% of decisions c85 kept a real context that O50 lost.
- **Adopted 14 Oct (prompt 32) and frozen.**

**O50 at a glance:**

- 188 roots: the 4 giants plus 184 small roots, 168 of them with ≤50 members.
- 476 themes have only giants as parents.
- Theme sizes:

  | size (members) | themes |
  |---|---:|
  | 3-50 | 4,486 |
  | 51-100 | 95 |
  | 101-200 | 10 |
  | 201-500 | 5 |
  | 501-1,000 | 2 |
  | over 1,000 | 4 |

- Per pathway, the largest non-giant theme above it falls in 11-50 for 1,096 pathways, 51-200 for 2,362, and 201-1,000 for 2,079.
- Plausibility verdicts: coherent 4,072; umbrella 418; core-plus-misfits 66; mixture 36; incoherent 10.

### 2.4 Other evaluations around the arm

- **Home-fit test** (`homefit_2026-10-12/`), asking whether a pathway's multiple homes are real facets:
  - Real homes fit 94.0% vs decoys 95.0%, so the declared reading was NOISE.
  - **The control was confounded:** 85% of the decoys lay inside a larger home of the pathway. The verdict stays on record but does not count against the algorithm.
  - A redo needs out-of-region decoys and a forced choice.
- **HiDeF vs c85** (`hidef_eval_2026-10-13/`):
  - Both builds are coherent: 98% vs 91%, inside the declared equivalence bar.
  - HiDeF is close to a tree: 6 twins, 24% of pathways with distinct homes.
  - THEMA has many facets, and before O50 also heavy redundancy.
- **Single-cell facets pilot:** design only (`claude/thema-pilot-singlecell-facets-design-2026-10-13.md`). Variant A treats genes as items; variant B treats cells as items, giving overlapping sub-states. Not run.

---

## 3. Naming O50 (14-15 Oct)

- **Pipeline:** naming-c1 (`spec/ALGORITHM.md`).
  - N1: 3 candidates per theme, each from the full member list plus confusable neighbours.
  - S1: back-match.
  - Selection: medoid by token Jaccard.
  - Uniqueness pass: re-ask colliding themes with seeds ci+20, then ci+30.
- **N1:**
  - 4,591 themes (3-200 members), 13,773 candidates; 15 themes unnameable.
  - About 58M subagent tokens, 20-40× the old cheap census labels, which back-matched at only 55%.
  - **Lesson: estimate cost before a run.**
- **S1 sample check** (200 themes, seed 20261015):
  - E1, the name picks its own theme among 5: **96.5%** (bar 85%).
  - E2, member fit: **0.924** (bar 0.90).
  - S1 changes the pick in only 6.5% of themes.
- **Aviyah chose "lite" names:** medoid without S1 except for the 200 sample themes. The full back-match is deferred (about 30M tokens).
- **Dedup:** 75 groups covering 154 themes → 0 duplicates after two rounds.
- **Official names file:** `naming_O50_2026-10-14/dedup/final_names_O50_lite_unique.tsv`, plus the hand override in `name_overrides.tsv`:
  - n02960 → "Calcium-phosphate homeostasis and mineralization (vitamin D, phosphate, vitamin K)" (Aviyah).
- **Style pilot** (form "HEAD (parts)"):
  - E1 98.0 vs 97.5;
  - E2 0.952 vs 0.932;
  - preferred 127 vs 60 (p = 1e-6);
  - list-style names fell from 67 of 200 to 0.
  - **Passes on the model judges.**
  - Adoption waits for H1: Aviyah's blind rating of 30 pairs in `style/H1_pairs_for_Aviyah.md`. Parked.
  - Four themes flagged "no unifying idea" look like known mixtures, so the flag could serve as a mixture signal.
- **The 11 themes over 200 members have no official names.** Reviewer labels exist in `roots_without_giants_O50.tsv` and `areas_rec2_giantdrop_2026-10-15/root_labels.json`.

---

## 4. Landing page (15 Oct, prompts 33 and 35)

- **Preview:** `demo/preview-O50/` (landing.html plus ontology.js).
- **Payload deduplicated:** each pathway is emitted once.

  | | raw | gzipped | parse | heap |
  |---|---|---|---|---|
  | before | 104.8 MB | 23.2 MB | 561 ms | 471 MB |
  | after | **12.8 MB** | 3.2 MB | 84 ms | 73 MB |

  `--payload inline` keeps the old output.
- **Fixes:**
  - deterministic tie-break;
  - `--method` default corrected;
  - the hardcoded prompt_version removed;
  - meta charset and viewport added;
  - `--name-overrides` flag, with an "edited" chip on the page.
- **Checks:** 831 tests pass. Headless Chrome at 360/390/768 px shows no overflow.
- **Example cards:** candidates are in `docs/status/2026-10-15-card-candidates.md`, and nothing has been changed yet. Reviewer suggestions:
  - card 1: **n00543**, sperm capacitation / acrosome / zona (2 databases, no shared genes);
  - card 2: **n00217**, zinc homeostasis / import / SLC39 influx (60-73% nested, across databases).

  **Aviyah has not picked yet.**
- **A theme Aviyah questioned:** "Motile cilium axoneme assembly, multiciliogenesis and CSF flow".
  - 13 of 15 members fit.
  - Manchette assembly fits, because its genes are flagellar.
  - Lateral and third ventricle development are weak: phenotype-linked (hydrocephalus) rather than ciliary machinery. Only 3 of 13 and 1 of 5 of their genes are ciliary.

---

## 5. The top level: the areas layer (15-16 Oct)

### 5.1 Motivation

- O50's top had 4 giants, 184 small roots and 476 themes with only giants above them.
- There was little at 200-1,000 members.
- The giants were called "grab bags". **This turned out to be largely wrong (see 5.6).**

### 5.2 Prompt 34: rec, the recursive top

- **Method:** the O50 configuration applied to about 660 units (non-giant roots plus giant-only themes), each represented by the centroid of its members' vectors. Areas map back to pathways as the union of their units.
- **Result: failed.**
  - Held-out FDR failed in strata 3-3 (0.038) and 7-9 (0.026).
  - 5 roots were over 1,000 pathways.
  - Root pairs overlapped up to J 0.71.
- **Positives:** all 476 giant-only themes were re-parented; summary placement rose from 85.3% to 92.8%.
- **About 2/3 of the roots read as sensible areas.**

### 5.3 Prompt 36: rec2, declared as the last try

**Changes** (post hoc, labelled):

- units over 200 pathways became fixed "anchors";
- the overlap cutoffs were measured on pathway sets;
- floors used 20 scramble seeds, with 4 held out.

**Result:**

- **FDR fixed:** overall 0.0043.
- **No duplicate roots:** the highest pair is J 0.49.
- **Failed:** 8 areas over 1,000 (largest 2,618), and one node with 181 children.

### 5.4 Aviyah's giant rule and the C6 test (15 Oct)

**Giant rule** (intended by Aviyah before rec2 but written down after it): areas over 1,000 pathways are giants and are kept out of the view, like O50's giants. Applied to rec2, it leaves 63 roots: 57 areas and 6 anchors.

**C6, blind intruder test** (`areas_rec2_giantdrop_2026-10-15/`, pre-registered):

- Each item shows 5 units of an area plus 1 outsider; the judge picks the odd one out.
- **312 of 335 areas = 93.1%** (bar 70%; chance about 17%).
- The 57 root areas: 51 of 57.

**Root labels (63 roots, model readers):** 29 intuitive, 31 partly, 3 not:

- R02, stress/death/repair/infection;
- R17, axon guidance + cilia + muscle;
- R23, proteostasis + cilia.

**Whole-ontology reading:**

- 33 of 63 roots are ≥80% inside another root but not 100%, so strict containment leaves them as roots.
- The mitochondrial roots are facets: about 48 core OXPHOS pathways shared, each root with a distinct other half. R62 is the core itself.
- **Twin vs nesting clarified for Aviyah:** the 0.5 rule measures sameness (Jaccard over the union), so a small set 98% inside a large one has a low J. For example, 198 shared out of a union of 855 gives J = 0.23.

### 5.5 Prompt 37: rec2fix

**Reviewer audit and correction:**

- The reviewer claimed rec2's area pathway sets were trimmed ("Gap 1"). **That was wrong:** the reviewer used rec2's unit lists, which provenance over-credited (3,247 extra units). rec2's pathway sets were already true unions.
- The rules not being applied at the seams ("Gap 2") was real:
  - anchors were never compared with each other or with areas;
  - no area was collapsed into its own unit;
  - 27 unlinked containments;
  - area_edges listed transitive edges, which inflated the children count.

**Result:**

| | outcome |
|---|---|
| FDR | pass, 0.00429 |
| max direct children | pass, 18 |
| coverage | pass, 99.4% |
| root pairs at J ≥ 0.5 | pass, none (max 0.488) |
| root count | **fail: 63 roots** (42 with the giants left in) |
| seam events | 3 collapses (an area absorbing its dominant unit), 0 merges |
| pathway bands | every pathway has a 201-1,000 node above it |

**Summary placement, with the fair comparison:**

| | placement |
|---|---|
| O50 with its giants | 85.3% |
| **O50 without giants** (the declared fallback) | **54.5%** |
| rec2fix view (areas, giants out) | **75.4%** |
| rec2fix with giants in | 87.4% |

Adding areas never lowers placement; removing giants does. The reviewer had first compared 75.4% against 85.3%, which is apples to oranges.

**Aviyah's near-containment rule:** if a child is ≥98% inside a parent and ≤5 pathways are missing, add the missing pathways to the parent and all its ancestors with evidence score 0, keeping strict containment. Its impact is small:

- O50: 3 themes gain a parent;
- rec2fix: 2 roots go (63 → 61): n03376 under n01279, and b2_00313 under b2_00198.

### 5.6 The giants: grab bags or wide themes? (15 Oct; `giants_reading_2026-10-15/`)

**Design**, pre-registered:

- **G1:** a full-list reading of each of the 12 giants (8 area giants, 4 O50 giants).
- **G2:** a blind intruder test, 5 items per giant. Coherent means the intruder is found in at least 4 of 5 items; by chance p ≈ 0.003.
- **Amendment before any judging:** insiders are the maximal nodes of 10-150 pathways inside the giant.

**Results:**

- **Wide themes (5):**
  - n01420, metabolism, 4/5;
  - b2_00112, metabolism, 4/5;
  - b2_00211, development and reproduction, 4/5;
  - n01845, development and intercellular signalling, 4/5;
  - b2_00076, tissue development, 3/5 (looser).
- **Two themes (4):**
  - n03867, immune + receptor signalling, 5/5;
  - n02670, immune + genome, 5/5;
  - b2_00161, metabolism + neurophysiology, 4/5;
  - b2_00251, neuro + trafficking, 5/5.
- **Mixtures (3):**
  - b2_00147, 2/5;
  - b2_00338, 2/5;
  - b2_00307: 5/5 on the test but a mixture by reading.
- **GO comparison:** GO's top terms are also giants. "Biological regulation" holds 1,402 of our GO pathways, and "cellular process" holds 1,287.

### 5.7 Reassessment (16 Oct)

**O50's 4 giants are not grab bags:** 2 are wide themes and 2 are two-theme unions.

**The two immune giants:**

- n03867 and n02670 share 1,163 pathways, 59% of each (J 0.42): the immune core.
- One adds receptor/ECM/hormone signalling; the other adds nuclear machinery (replication, repair, chromatin, splicing).
- The immune hub joins different neighbours in different runs, so both versions survive: J is below 0.5 and neither is nested in the other.

**The 184 small O50 roots:**

- 113 straddle two or more giants;
- 71 contain pathways that are in no giant (146 such pathways);
- **0** can be attached by the 98%/≤5 rule.

**Blind top-level comparison** (`top_compare_2026-10-16/`, pre-registered):

- **Test A, the menu (5 judges):**
  - option 2 (O50 + areas, giants kept, 42 roots) beats option 1 (O50, 188 roots) **5 to 0**;
  - the judges flag the area giants in option 2 as incoherent;
  - mean scores: coherence 2.0 vs 2.4, redundancy 2.0 vs 1.2, usefulness 3.0 vs 2.0;
  - partly a size effect, as declared in advance.
- **Test B, per-pathway homes (60 pathways × 3 judges):** **30 vs 30**, no difference.
- **Reading:** the areas improve browsability, not pathway placement.

### 5.8 Why the pathway pass lacks 200-1,000 themes

- **8 Oct diagnostic (DECISIONS):** Ward clusters of 60-2,000 recur at J 0.5 but almost never at 0.70; scrambles recur at neither. Median support at 0.5 vs 0.70: 0.26 vs 0.00 for 60-200 members, 0.81 vs 0.05 for 801-2,000.
- **Earlier fixes tried:**
  - match 0.5 for clusters of 50+ (arm MS): +2 themes only;
  - **cal8 floor recalibration:** 51-1,000 themes went from 27 to 196. This is the saved middle layer, and O50 is built on `floors_L_cal8`.
- **c85 vs O50 by size:**

  | size | c85 | O50 |
  |---|---:|---:|
  | 51-100 | 193 | 95 |
  | 101-200 | 28 | 10 |
  | 201-500 | 6 | 5 |
  | 501-1,000 | 4 | 2 |

  The 201-1,000 gap already existed before the O50 merge, so it comes from matching and stability, not merging.
- **Conclusion:** the pathway-level pass cannot make stable groups of 200-1,000 under the 0.70 match. "Option 3" (fixing the matching inside the pathway pass) was effectively tried on 8 Oct and gave little.

### 5.9 How the areas pass differs from the pathway pass

- Its items are fixed themes, represented by centroids. Every theme weighed equally in rec/rec2/rec2fix.
- Recurrence is checked on theme sets, so wobbling edge pathways cannot break a match.
- Themes overlap, so areas overlap too.
- Ward already merges on centroids (size-weighted), so this is not a linkage change.

### 5.10 Formalisation for the paper, and prompt 38 (rec3, 16 Oct)

**One operator T:** resample, Ward, recurrence 0.70, null-calibrated floors (target 0.008, caps 0.02 per stratum and 0.01 overall), consensus, joint twin 0.50 and chain 0.85, strict containment.

**Recursion:**

- level 0 is O50;
- level k+1 is T applied to the maximal level-k nodes with ≤1,000 pathways, each a size-weighted, unsplittable item (Ward continued from fixed clusters, must-link);
- one structure over all nodes, giants included;
- no anchors, no giant drop, no seam special cases;
- stop when a level admits nothing, or when there are ≤60 roots.

**Precedents:** Louvain aggregation (Blondel 2008), constrained Ward, HiDeF (Zheng 2021), NeXO/CliXO (Dutkowski 2013), consensus clustering (Monti 2003), pvclust.

**Arms:** W (size-weighted, primary) and E (equal weight, ablation).

**Accepted if:**

- FDR holds at every level;
- 20-60 roots;
- ≤60 direct children per node;
- summary placement ≥85.3%;
- C6 ≥70%, plus a giant check on any new node over 1,000;
- Aviyah finds the top intuitive.

**If W fails, O50 stays as it is.** Pasted to ccode on 16 Oct; result pending.

---

## 6. Reviewer errors and lessons (be aware when re-reading)

1. **The giants were called "grab bags" from stale numbers.** The blind test shows mostly wide themes. The areas layer was partly motivated by that wrong premise.
2. **"Gap 1" in the rec2fix audit was wrong.** The reviewer read inflated provenance unit lists.
3. **Summary placement was compared apples to oranges** at first: 75.4% against O50 with giants.
4. **"Missing middle layer" was used loosely.** The 51-200 middle was already fixed by cal8; only 200-1,000 is thin.
5. **Option 3 was offered as new** although it had been diagnosed and tried on 8 Oct. Check DECISIONS before proposing.
6. **The reviewer ran read-only git commands on the Mac twice** (`git log` on 15 Oct, `git check-ignore` on 15 Oct), against the rule. Disclosed.
7. **The cost of the N1 naming run (about 58M tokens) was not estimated beforehand.**
8. **The labelling workflow on 15 Oct used the Workflow tool without an explicit opt-in.** Disclosed.

---

## 7. Open items

- **Prompt 38 (rec3):** awaiting ccode. Then the reviewer runs C6, giant checks on any new giants and root labels, and Aviyah judges the top.
- **Commit scripts to run, in order:**
  - commit-2026-10-15-recursive-top-2.sh
  - commit-2026-10-15-areas-rec2fix.sh
  - commit-2026-10-16-areas-rec3.sh (after prompt 38)

  Commit prompt 38's script after the rec2fix one. Prompt 38's script includes `giants_reading_2026-10-15/` and `top_compare_2026-10-16/`. This log, `REVIEWER_LOG_2026-10-12_to_16.md`, is not in any script yet; add it to the next one.
- **Check `naming_pilot_2026-10-11/api_run/example_request.json`:** it was rewritten during the prompt 37 run, probably by a test. Its note says no API call was made.
- **Naming:**
  - H1, Aviyah's 30-pair style rating;
  - the full restyle decision (about 15-20M tokens);
  - the full S1 back-match (about 30M tokens, or about $150-200 by API);
  - names for the 11 themes over 200 members.
- **Landing:**
  - Aviyah picks the example cards (suggested n00543 and n00217);
  - navigation for the giants' long child lists and for the small roots, depending on the rec3 outcome.
- **Later:**
  - a human biologist check;
  - the statistics layer;
  - the single-cell pilot;
  - a home-fit redo with out-of-region decoys;
  - mixture flagging (the style-pilot "no unifying idea" flag is a candidate).

## 8. File index (reviewer folders, `data/experiments/`)

| folder | content |
|---|---|
| `reviewer_notes/` | HANDOFF_2026-10-12, SPEC_overlap_arm, PROMPT_28_original, PROMPT_31-38, this log |
| `reviewer_eval_x2_2026-10-09/` | twin-merge decision record, c85 reassessment, merge J05 simulation |
| `core_reading_*_2026-10-11/`, `whole_reading_2026-10-11/` | facet/variant reading tests |
| `homefit_2026-10-12/` | home-fit test (confounded control) |
| `hidef_eval_2026-10-13/` | HiDeF vs c85 |
| `o50_eval_2026-10-13/` | C4 and C5 for O50 |
| `naming_O50_2026-10-14/` | N1 raw, sample check, select_lite, dedup (official names), style pilot, name_overrides.tsv, roots_without_giants_O50.tsv |
| `areas_rec2_giantdrop_2026-10-15/` | C6 (PREREG, code, judgements, misses), root labels, ROOTS_for_Aviyah.md, audit scripts (rule_audit*, near_containment_impact, facet_or_sub, roots61, giants_read) |
| `giants_reading_2026-10-15/` | G1/G2 giant tests, RESULT_giants.tsv, the O50 roots and immune-overlap script |
| `top_compare_2026-10-16/` | option 1 vs 2 blind comparison |

**Builds:**

- `data/ontology/frozen/working-O50-2026-10-14/` (adopted)
- `data/ontology/frozen/working-c85-2026-10-10/` and the baseline freeze (fallbacks)
- `data/ontology/v0.4-leaves/thema_L_x2_O50_rec/`, `_rec2/`, `_rec2fix/` (experiments, not adopted)
