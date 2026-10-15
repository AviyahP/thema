# HiDeF vs THEMA c85: report (reviewer, 2026-10-13)

Pre-registration: PREREG.md. Code: code/hd_struct.py, hd_build.py, hd_score.py. Outputs: structural_output.txt,
score_output.txt, judged/. HiDeF = hidef_L_k4_maxres800 (best on the tuning half, 8 Oct). Giants excluded.

## Structure
| | THEMA c85 | HiDeF k4/800 |
|---|---|---|
| themes (3-999) | 8,241 | 2,444 |
| size 3-6 / 7-15 / 16-40 / 41-100 / 101+ | 859 / 4,609 / 2,400 / 335 / 38 | 1,228 / 768 / 297 / 107 / 44 |
| roots | 962 | 145 |
| themes with 2+ parents not nested in each other | 51% | 20% |
| twins: sibling pairs at J >= 0.5 | 3,337 (405 per 1,000 themes) | 6 (2 per 1,000) |
| any non-nested pair at J >= 0.5 | 9,138 | 17 |
| pathways with 2+ clearly distinct homes | 79% (3+: 54%) | 24% (3+: 4%) |
Correspondence, 1,208 pathways with 2+ distinct homes in both: 43% of HiDeF's distinct homes have a THEMA counterpart at
J >= 0.5; 21% of THEMA's have a HiDeF counterpart.

## Blind judging (100 themes per arm, size-matched to HiDeF's 3-100 distribution, full member lists, no names)
| | HiDeF | THEMA | diff (CI) | declared reading |
|---|---|---|---|---|
| ok (coherent or umbrella) | 91% | 98% | -7 (-14 to -1) | equivalent (under the 10-point bar) |
| coherent | 83% | 84% | -1 | equivalent |
| easy to name | 81% | 87% | -6 (-16 to +4) | equivalent |
| easy or broad name | 95% | 100% | -5 (-10 to -1) | equivalent |
HiDeF's misses are mostly small themes with one or two stray members (core plus misfits) or two unrelated blocks.

## Reading
- Both produce coherent, nameable small themes; THEMA is slightly ahead (CI excludes 0 on ok rate, below the declared bar).
- HiDeF is close to a tree of mostly very small themes: almost no twins, but few facets (a quarter of pathways have a
  second distinct home, against four in five in THEMA).
- THEMA's facets come with redundancy. The J >= 0.5 simulation (12 Oct) kept 75% of pathways with 2+ distinct homes after
  removing the variants, so the overlap arm (O50) should keep THEMA's facets while bringing twins near HiDeF's level.
- Not tested here: whether HiDeF's few facets are better or worse facets than THEMA's.
