Prompt 44: the top of O50s, two arms. Declared 17 Oct 2026, before any result. Exploratory: this adopts nothing. Prompt 42 stays on hold; this replaces it. This message ends with END OF PROMPT; if that line is missing, stop and say so.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not change frozen folders or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Stop if the estimate is over 3 h.

WHY
O50s (prompt 43) fixed the 100-1,000 layer, but it has 261 roots, 164 of them ≤50 pathways. Aviyah wants fewer than 49 thematically coherent roots. Two ways to build the top are tested on the same base, O50s.

ARM A: areas on top of O50s
Run rec2fix's code and rules exactly (equal weight, anchors over 200 pathways, union sets, seam rules, joint fixed point with twin 0.50 and chain 0.85, strict containment, one structure with the giants kept in), with O50s as level 0 instead of O50. Report the unit count.

ARM B: a measured cut, then areas above it
1. **Stability per theme (Hennig 2007 clusterwise Jaccard).** For every final O50s theme of 50 or more pathways, in each of the 200 cached runs:
   - restrict the theme to the pathways present in that run's 80% subsample;
   - take the best Jaccard to any cluster of that run's Ward tree;
   - the theme's stability is the mean of these 200 values.
2. **Bands:** 50-99, 100-199, 200-399, 400-799, 800-1,599, 1,600+. Per band, report the count and the median, 25th and 75th percentile stability.
   **Noise check for this measure:** compute the same stability for scrambled candidates of 50 or more pathways from the cached calibration scrambles (3001-3010), each against its own scramble's 200 runs. Also compute it for all real gated candidates of 50 or more. Per band, report:
   - the scrambled median and 95th percentile;
   - whether 0.6 is above the scrambled 95th percentile;
   - how well each measure separates real from scrambled candidates (AUC), for support and for this stability.
   Report only; this does not change the rule in step 3.
3. **The cut T** is the lower edge of the first band whose median stability is below 0.6. Also report where the cut would fall at 0.75. If no band is below 0.6, there is no cut: report this and skip steps 4-5 of arm B.
4. **Items:** the O50s themes of size below T that are not strictly inside another such theme, plus any pathway in none of them. Every O50s theme of T or more is dropped and kept for comparison only.
5. **Areas pass** on these items, with rec2fix's code and rules except: **no anchors**. Areas over 1,000 pathways are kept and flagged.

BOTH ARMS: noise
Calibrate the floors on 20 item scrambles (3001-3020), then check them on held-out seeds 4002-4005. Target 0.008; caps 0.02 per stratum and 0.01 overall.

REPORT (docs/status/2026-10-17-top-two-arms.md), per arm
1. Held-out FDR per stratum and overall.
2. **Roots:** the count, and each root's id, size and number of children.
3. **Small roots (≤50 pathways):** for each, the 3 larger nodes that contain the largest share of it, with that share and the number of pathways missing.
4. **Duplication, report only:** root pairs with J ≥ 0.5, and roots that are ≥80% inside another node.
5. Children per node, maximum and median; areas over 1,000.
6. Summary placement, against O50s's 92.6%; agreement with Reactome's top level (median best J).
7. Arm B only: the stability table and T; for each dropped theme of T or more, its best-matching area by J.

FOR THE REVIEWER (do not judge them yourself)
Write data/experiments/top_two_arms_2026-10-17/{A,B}/ containing:
- roots.tsv (id, size, full member keys);
- small_roots.tsv (the item 3 table, with the full member keys of the root and of its 3 containing nodes);
- areas.tsv (every area, with its full member keys and the unit ids).

DECISION RULE (declared now; applied after the reviewer checks)
An arm passes only if all hold:
- held-out FDR within the caps;
- fewer than 49 roots;
- blind reading of every root: at least 80% coherent or linked umbrella;
- every small root (≤50) is judged, blind, a distinct topic rather than belonging under one of its 3 containing nodes;
- C6 intruder test on the areas: at least 70%.
Duplication (item 4) is reported, not a gate. If both arms pass, a blind A vs B comparison of the two top levels decides, then Aviyah. If neither passes, nothing is adopted.

FINAL
- Save this prompt verbatim as data/experiments/reviewer_notes/PROMPT_44.md, and copy it into DECISIONS.md as "declared before running", before building.
- Outputs: data/ontology/v0.4-leaves/thema_L_x2_O50s_top/{A,B}/.
- Write docs/status/commit-2026-10-17-top-two-arms.sh, to run after commit-2026-10-17-O50s.sh. It commits the code, tests, builds, status note, reviewer folder and data/experiments/reviewer_notes/PROMPT_44.md. No branch operations; no push of main.

ORDER: arm B steps 1-3 first (stability table and T), and report them. Then arm A, then the rest of arm B.

END OF PROMPT. Before building, give the unit count for arm A and the time estimate. After the build, give:
- the stability table, the noise check and T;
- the FDR summary per arm;
- roots, small roots, placement and Reactome agreement per arm;
- the commit script path.
