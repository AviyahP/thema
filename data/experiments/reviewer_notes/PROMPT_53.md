Prompt 53: O50s restructured as designed (builds S1p and S1s). Declared 22 Oct 2026, before any result. Exploratory: nothing is adopted. The design is Aviyah's (22 Oct); the two chain-survivor arms are both built because she has not yet chosen between them, and she will confirm the version on her return. This message ends with END OF PROMPT; if that line is missing, stop and say so.

WHY
Prompt 52 showed that the J >= 0.5 sibling rule does 95% of its work as "consensus", which runs after the gate but BEFORE any DAG exists: 19,531 merges shrink 26,120 gated themes to 6,589, and 54% of those merges join themes that end up neither siblings nor nested. It also superseded 76 well-supported parents (52-62 runs) covering 74 of the 261 roots. Aviyah's design: the 10% variant merge before the gate (as now); after the gate, build the DAG; then apply the sibling rule (J >= 0.5) only to real siblings and the chain rule (0.85) only to real parent-child pairs, on the DAG.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not change frozen folders, cached trees or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Give the time estimate first; Aviyah is away, so if it is under 5 h, start without waiting; if over, do the build and sections A-B only and stop.

FIRST: save this prompt verbatim as data/experiments/reviewer_notes/PROMPT_53.md (if not already there), and copy it into DECISIONS.md as "declared before running".

SPEC. Start from frozen O50s (data/ontology/frozen/working-O50s-2026-10-22/) exactly: x2 universe, cached trees and sides, stored floors.
1-6. Unchanged: candidates, J >= 0.70 support, completion at 0.5, 10% families, the gate with O50s's floors. The 26,120 gated themes are the input below (as logged in prompt 52). No consensus step.
7. DAG: strict containment over all gated themes (every member of the child in the parent, parent larger), immediate parents only.
8. On the DAG, repeated until nothing changes, rebuilding the DAG after each round:
   a. Chain rule first: a child holding at least 0.85 of an immediate parent's members becomes one node with it. Survivor by arm:
      - S1p: the parent always survives;
      - S1s: the higher support survives; on a tie, or when the parent has no parent, the parent survives (today's rule).
      The survivor's children and parents are re-linked; memberships are not changed.
   b. Sibling rule: siblings = themes sharing at least one immediate parent, or both roots. In today's consensus order (support descending, then size descending, then key), a theme is dropped if an already kept sibling overlaps it at J >= 0.5 and neither contains the other. Memberships are not changed (no inheritance). Non-sibling overlaps of any size are kept.
9. Final edges: strict containment, immediate parents only.
Report the number of rounds and, per round, the chain collapses and sibling drops.

Tests before building: on a fixture, the sibling rule never merges non-siblings and is order-stable; with the consensus step restored and steps 7-8 replaced by today's repair, the code reproduces frozen O50s byte for byte.

REPORT (docs/status/2026-10-22-restructured-S1.md), S1p, S1s and O50s side by side, computed by the same code. Use the existing evaluation scripts where they exist; for any measure without one, say so and how it was computed.
A. Construction: gated themes, chain collapses, sibling drops, final themes; held-out FDR (unchanged at the gate; confirm).
B. Size and shape: themes per band (3-5, 6-11, 12-24, 25-49, 50-99, 100-199, 200-399, 400-799, 800-1,599, 1,600+); roots and roots of 50 or fewer; giants (over 1,280) with sizes; children per node, maximum and median; multi-parent share; mean themes per pathway; levels from a pathway to its root, median and maximum.
C. Duplication: non-nested pairs at J >= 0.5 that remain (by band, and how many are non-siblings); nodes at least 80% inside another node without being its descendant, by pathways missing (0, 1-5, 6-20, 21+).
D. The prompt-52 parents: of the 76 parents consensus superseded, how many survive in each arm, and how many current O50s roots they contain; the two themes that superseded them in O50s (node ids, sizes, whether giants).
E. Agreement and placement: O50s themes with a counterpart at J >= 0.9 (share, by band); the 164 O50s small roots and the roots n01027, n04526, n04670, n04671, n03316, n04672, n04995, n05001 (counterpart J, and whether still a root); summary placement; Reactome median best J; curated recall per band for Reactome and GO (J > 0.5); sibling specificity AUROC.
F. Stability: half-builds from runs 1-100 and 101-200 through the same steps, final-theme match, worse direction, J >= 0.70.
G. Gene coherence per band against size-matched random sets (evaluation only).

FOR THE REVIEWER (do not judge anything yourself), for EACH arm separately, in data/experiments/restructured_S1_2026-10-22/{S1p,S1s}/, only if that arm has 600 roots or fewer:
- R: every root, whatever its size, giants in full; "name [source]" sorted by name; random ids (seed 20261022); batches of about 2,600 lines in read_roots/; a root never split.
- S: for every root of 50 or fewer pathways, as in PREREG_O50s_roots.md (3 largest-share larger containers as P, Q, R in random order, each with its size and up to 40 members not in the root); shares only in the KEY file; batches in small_inputs/.
- KEY_DO_NOT_SHARE_S1.json per arm; roots.tsv per arm.
The 40-per-band theme sample and intruder inputs are NOT prepared now; they wait for Aviyah's choice of arm.

FINAL
- Output builds: data/ontology/v0.4-leaves/thema_L_x2_S1p/ and thema_L_x2_S1s/.
- Write docs/status/commit-2026-10-22-restructured-S1.sh, to run after commit-2026-10-22-merge-relationships.sh. It commits the code, tests, both builds, status note, reviewer folders and PROMPT_53.md, listing files explicitly, leaving out any file over 50 MB (and saying which), never including any KEY_DO_NOT_SHARE* file. No branch operations; no push of main.

END OF PROMPT. Before building, give the time estimate and confirm both tests pass. After everything, give sections A-G as tables for S1p, S1s and O50s, the reviewer batch paths, and the commit script path.
