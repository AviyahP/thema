Prompt 34: the recursive top level on O50 (THEMA applied to its own themes), declared 15 Oct 2026 before any result. Adapted from prompt 19, which was never run. This message ends with END OF PROMPT; if that line is missing, stop and say so.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not touch frozen folders; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Before building, estimate the run time and stop if it is over 3 h.

WHY
- In O50 (data/ontology/frozen/working-O50-2026-10-14/), 4 roots are giant grab bags (2,332 / 2,018 / 2,015 / 1,412 members, 140-283 children each), and 97% of pathways sit inside one of them.
- 476 themes have only giants as parents.
- 184 other roots are mostly small themes (168 have 50 members or fewer).
- So there is no area layer. For 20% of pathways, the largest real theme above them has 50 members or fewer.
- A one-off test on 8 Oct (Ward on theme centroids, k = 30 chosen by hand) gave about 30 intuitive areas. This prompt does it properly: the same algorithm one level up, with resampling, recurrence and a scramble null, and k coming from the data.

STEPS
1. Units, from the frozen O50, read-only.
   - Drop the giants (themes with more than 1,000 members).
   - Units = every remaining theme with no non-giant parent: the 184 non-giant roots plus the themes whose parents are all giants. Report the count; expected about 660.
   - Add any pathway that is in no non-giant theme as a unit of its own.
   - Represent each unit by the normalised mean of its members' rows in vectors_leaves_centred (the x2 universe, rows L2-normalised). Record each unit's size in pathways.
2. Level 2 = the O50 configuration, unchanged, on units:
   - 200 runs on 80% subsamples of units, Ward on unit centroids;
   - recurrence matching 0.70 on unit membership;
   - same-theme cutoff 0.50 in consensus and the stale pass;
   - joint fixed point with chain collapse at 0.85;
   - strict containment.
   - Floors are calibrated on unit scrambles (seeds 3001-3010, held out 4001 and 4002) and solved to a 0.008 target.
   - Unit membership may overlap, so a unit can get two areas.
3. Map back.
   - An area's pathway members are the union of its units' members.
   - Add edges area -> unit theme.
   - The giants are not part of the combined DAG; they stay only in the O50 freeze.
4. Repeat steps 2-3 on the level-2 roots only if more than 60 remain. Stop at 20-60 roots.
5. Output: data/ontology/v0.4-leaves/thema_L_x2_O50_rec/ (O50 nodes, plus areas, plus area edges), with a manifest. Adopt nothing.

REPORT (docs/status/2026-10-15-recursive-top-O50.md)
- **Per level:**
  - nodes, sizes in units and in pathways;
  - held-out FDR per stratum;
  - multi-parent share;
  - max and median children per node.
- **The top level:** every root with its size in units and pathways, its child units, and the 10 pathway names nearest its centroid. Names are for judging only.
- **Coverage:**
  - how many of the 476 giant-only themes now have an area parent;
  - roots before and after;
  - per pathway, the largest non-giant ancestor, by band, before and after (today: 51-200 = 2,362; 11-50 = 1,096; 201-1,000 = 2,079).
- **Gene coherence per level** against size-matched random. Report it, do not gate on it; low coherence is expected at the top.
- **Agreement with Reactome's top-level pathways (secondary):** for each, the best area by Jaccard on leaves.
- **Summary placement (display only, report only).** For every curated summary pathway in the 10,747 universe that is not in L, take its leaf descendants in L (the leaves-experiment closure). Report the smallest node containing at least 80% of them:
  - by summary size band;
  - in O50 alone and in the combined DAG;
  - with the share landing on a giant (O50) or on an area (combined).
  This measures whether areas give the summaries a home. Nothing is attached in this prompt.
- **Run time and memory.**

DECISION (declared now)
The recursive top is accepted for further work if:
- held-out FDR is within the caps at level 2;
- the top has 20-60 roots;
- no node has more than 60 children;
- at least 95% of the 476 giant-only themes get an area parent;
- C6 (reviewer, after the build) passes. C6 is a blind intruder test on every area with 4 or more units: 5 random units of the area plus 1 unit from a different area, shuffled, shown as full member lists without names. Pass if judges spot the intruder in at least 70% of areas (chance about 17%).
- Aviyah judges the top level intuitive.

FINAL
- Copy this prompt verbatim into DECISIONS.md as "declared before running", before building.
- Write docs/status/commit-2026-10-15-recursive-top.sh. It commits the code, the tests, the new build folder and the status note on leaves-2026-10, with no branch operations and no push of main.

END OF PROMPT. Before building, confirm in one line:
- the number of units;
- your time estimate.
After the build, give:
- the counts per level and the number of top roots;
- held-out FDR;
- giant-only themes re-parented;
- summary placement before/after;
- the commit script path.
