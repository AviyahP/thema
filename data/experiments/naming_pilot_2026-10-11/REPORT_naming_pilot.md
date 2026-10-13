# Naming pilot naming-c1 — results (reviewer, 2026-10-11)

Pre-registration: PREREG.md. Algorithm: spec/ALGORITHM.md + prompt templates spec/N1_namer.md, S1_backmatch.md, E2_fit.md,
E3_equivalence.md. Code that built every input and computed every number: code/np_*.py. Raw model outputs: raw/,
selection/*.out.json, eval/*.out.json. Keys (never shown to any judge): */KEY_DO_NOT_SHARE*.json.
Run: in-session subagents of the reviewer session (configured model claude-opus-5-5); 30 namer contexts, 17 selection
contexts, 18 fresh evaluation contexts. No API spend.

## Sample
200 c85 themes (median 13 members, max 83): 150 from sibling families, 50 others. Each has 4 confusables (closest
non-nested siblings by member-centroid cosine; filled from global neighbours for 104 themes with < 4 siblings).

## Results vs pass bars
| bar | result | pass |
|---|---|---|
| P1 back-matching (pick own theme among 5; chance 20%) >= 85% | NEW 91.5% (families 90.0%, others 96.0%) | yes |
| P2 NEW - CENSUS lower CI >= -3 pts | +36.5 pts (95% CI +28.5 to +44.5); CENSUS 55.0% (families 49.3%) | yes |
| P3 member fit >= 0.90 | NEW 0.917 (40% perfect); CENSUS 0.899 (32%) | yes |
| P4 re-run equivalent >= 80% (60 themes) | equivalent 60%, nested 38%, different 2% (1/60) | NO |
| P5 zero duplicates | NEW 0 (after 1 de-dup round for 1 pair); CENSUS 1 duplicate in the same 200 | yes |

- Paired: both right 101, new only 82, old only 9, both wrong 8.
- Selection effect check: unselected candidates were already right 83.2% of the time in selection, so most of the gain
  comes from contrastive naming with full lists, not from picking the best of three.
- Unnameable 0; low-confidence (no candidate passed back-matching) 6 of 200.
- New names are longer: median 8 words (max 10) vs 5. Some read as lists ("X, Y and Z").
- P4: a re-run gives the same theme 98% of the time, but in 38% the judge saw a different emphasis or breadth
  (e.g. "cAMP synthesis and protein kinase A activation" vs "GPCR-driven cAMP synthesis and protein kinase A
  activation"). One true disagreement (MECP2 repression vs MECP2 neuronal regulation).

Side-by-side list of all 200: SIDE_BY_SIDE.md. Per-theme scores: eval/scored_rows.json.

## Status
naming-c1 passes 4 of 5 pre-registered bars and fails reproducibility at the strict "equivalent" level. Decision on
P4 (accept, or test a 5-candidate consensus variant naming-c2 on the 60-theme subset) is Aviyah's.

## naming-c2 test (pre-registered in PREREG_c2.md; same 60 reproducibility themes)
Change: N2 prompt (core + at most one qualifier, no "X, Y and Z" lists) and 5 candidates instead of 3. Two independent
runs (A, B). Note: with 5 candidates "unnameable" was set to a majority (>= 3 of 5); no theme was unnameable.

| measure | c1 (same 60 themes) | c2 |
|---|---|---|
| back-matching (bar 85%) | 90.0% | 80.0% (A 83.3%, B 76.7%) — FAIL |
| member fit (bar 0.90) | 0.924 | 0.908 |
| re-run equivalent, same judges, blind to version (bar 80%) | 58% | 62% — FAIL |
| re-run equivalent or nested | 100% | 97% |
| list-style names | 14/60 | 0/60 |
| median words | 8 | 7 |
| candidates correct in selection | 83.2% (c1, all 200) | 72.2% |

Reading: the single-qualifier rule removed list-style names but cost distinguishability (one qualifier often cannot
separate a theme from all four confusables); 5 candidates did not make reruns converge. Under the same judges c1 and c2
reproduce about equally (58% vs 62% strictly equivalent; 97-100% equivalent or nested).

Decision per the pre-registered fallback: c2 failed P4 (and P1), so the better-scoring version is kept: naming-c1,
with its reproducibility reported honestly (about 60% strictly equivalent, about 98% same theme). Post-hoc note: the
strict E3 judge may cap "equivalent" well below 100% even for near-identical names; no ceiling test was run.

## naming-c1b clean test (pre-registered in PREREG_c1b.md): original N1 prompt, 5 candidates instead of 3
Question (Aviyah): was c2's failure due to the prompt change or to 5 candidates? Same 60 themes; c1's 3 candidates per
run reused, 2 new per run added; all four sets of finals (c1b M/R, c1 M/R) judged together, blind, by fresh judges.

| measure | c1 (3 candidates) | c1b (5 candidates) | difference (95% CI) |
|---|---|---|---|
| back-matching | 87.5% | 90.0% | +2.5 (-1.7 to +6.7) |
| member fit | 0.919 | 0.921 | +0.002 (-0.006 to +0.010) |
| re-run equivalent (bar 80%) | 63% | 65% | +2 (-12 to +13) |
| re-run equivalent or nested | 98% | 100% | |
| identical names across runs | 8/60 | 9/60 | |

Per-candidate back-matching (before selection): c1 prompt 78-84%, new c1b candidates 79.6%; c2 prompt 71-73%.

Reading:
- Aviyah's hypothesis is confirmed for distinguishability: the c2 drop came from the prompt change, not from 5 candidates.
- Candidate count makes no measurable difference: 5 candidates are as good as 3 on every measure.
- Reproducibility stays at about 60-65% strictly equivalent (about 98-100% same theme) whatever the candidate count or
  prompt; neither lever moves it.
Decision per PREREG_c1b: c1b fails the 80% bar and is not >= 10 points better on equivalence, so naming-c1
(3 candidates, the cheaper) remains the adopted version.
