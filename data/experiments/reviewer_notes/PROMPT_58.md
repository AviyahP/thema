Prompt 58: merge by core, up to the merge only (arms CI and CT). Declared 23 Oct 2026, before any result. Exploratory: no ontology is built, nothing adopted. Design: Aviyah, 23 Oct. This message ends with END OF PROMPT; if that line is missing, stop and say so.

WHY
O50s's near-copies come from comparing versions of one theme on their full sets, wobbly borders included (step 5, 10% rule on completed sets). Aviyah's design compares versions on their CORES instead: each run's cluster is matched at J >= 0.70, its matched copies define a core, and clusters with the same core are one theme. This prompt runs only that far and compares the result with O50s at each of its stages.

Rules: no API calls; do not commit, leave a commit script; never open any KEY_DO_NOT_SHARE* file; do not change frozen folders, cached trees or any existing build; working branch leaves-2026-10; never create, switch or delete branches outside a commit script, not even as a dry run; one heavy job at a time; times in UTC+1. Give the time estimate first; if under 3 h, proceed without waiting; if over, stop and propose a cheaper order.

FIRST: save this prompt verbatim as data/experiments/reviewer_notes/PROMPT_58.md (if not already there), and copy it into DECISIONS.md as "declared before running".

INPUT: frozen O50s (data/ontology/frozen/working-O50s-2026-10-22/): x2 universe, the 200 cached runs, the stored groupings, their J >= 0.70 matched copies and supports, exactly as O50s computes them. Reuse, do not recompute, wherever the cache allows.

SPEC (both arms):
1. Candidates, matching, support: unchanged from O50s (every cluster of 3 or more, stored once as groupings; matched copies at J >= 0.70 on shared pathways, one per run; eligibility at 3 shared; support = runs that found it / runs able to judge it).
2. Core of a grouping: the pathways with inclusion >= 0.9 in its matched copies (inclusion = copies holding the pathway / copies from runs where it was drawn, as in O50s's completion). A grouping whose core has fewer than 3 pathways has no core: count these by size band and leave them out of the themes.
3. Merge by core: in O50s's family order (support descending, then size descending, then key), each unclaimed grouping with a core becomes a seed and absorbs every unclaimed grouping whose core is the same as the SEED's core (compared with the seed only, never with the growing theme, so no chaining):
   - arm CI: identical cores;
   - arm CT: cores that pass O50s's twin test (is_variant, imported, unchanged: each side's private part at most max(2, int(10% of the shared part))).
4. Each theme: support pooled as O50s pools family support (runs that found any of its groupings / runs able to judge any). Pooled copies: one per run, the copy of the highest-support grouping of the theme found in that run. From the pooled copies, recompute inclusions; core = inclusion >= 0.9; members = inclusion >= 0.5.
No gate, no consensus, no repair, no edges.

REPORT (docs/status/2026-10-23-core-merge.md). CI and CT next to O50s at its stages: (s1) groupings, (s2) families before the gate, (s3) the 26,120 gated themes, (s4) after consensus (6,589), (s5) final (5,658).
A. Counts: groupings without a core (by band); themes; groupings per theme (median, maximum); themes per band (3-5, 6-11, 12-24, 25-49, 50-99, 100-199, 200-399, 400-799, 800-1,599, 1,600+); core size as a share of members (median by band).
B. Support: median support by band, and the share of themes at or above 0.05, 0.1, 0.33, by band; CI and CT against s2.
C. Near-copies (the thing consensus and repair fix), per arm and for s2 and s3: non-nested pairs at J >= 0.5 (count, by band of the larger); nested pairs with the smaller holding >= 0.85 of the larger; pairs where the smaller has exactly 1 member outside the larger (the inheritance trigger); and the same three counts restricted to themes passing O50s's stored floors (INDICATIVE ONLY: the floors were calibrated for O50s's families, not for these arms; label it so).
D. Correspondence: share of s5 (final O50s) themes with a CI / CT counterpart at J >= 0.9 and at J >= 0.7, by band; for the 5 O50s giants, the best CI / CT counterpart (J, size) and their cores' sizes.
E. Twenty CI themes and twenty CT themes of 25 or more members, drawn at random (seed 20261023), as "name [source]" member lists with the core marked, in data/experiments/core_merge_2026-10-23/examples/. Do not judge them.

FINAL
Write docs/status/commit-2026-10-23-core-merge.sh, to run after commit-2026-10-23-trim-T1.sh. It commits the code, status note, data/experiments/core_merge_2026-10-23/ and PROMPT_58.md, listing files explicitly, leaving out any file over 50 MB (and saying which), never including any KEY_DO_NOT_SHARE* file. No branch operations; no push of main.

END OF PROMPT. Before starting, give the time estimate. After, give sections A-D as tables and the commit script path.
