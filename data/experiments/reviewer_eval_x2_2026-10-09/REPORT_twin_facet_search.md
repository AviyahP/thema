# Twin vs facet: hypothesis search results (reviewer, 2026-10-10)

Pre-registration: twin_facet_hypotheses_PREREG.md (written before any result).
Scripts: tf_common.py, tf_static.py, tf_runs.py, tf_eval.py. Features: twin_facet_features_*.json.
Labels (LLM judge) used only to score fixed formulas. Trees: v0.4-leaves-x2, 200 runs.

## Variant families (no LLM)
Connected components of the sibling-overlap graph (J >= 0.4): 1,041 families, 5,225 themes, 5,574 edges.
450 are a single pair; 375 have 3-5 themes; 127 have 6-10; 73 have 11-30; 16 have > 30 (largest 82).
410 families mix twin and facet edges; 312 only twin; 319 only facet.

## Results table (AUC in declared direction; pass = >= 0.65 in both halves and J-band-stratified >= 0.60)
```
feat dir   AUC half1 half2 Jband family     n pass
J      T 0.641 0.656 0.626 nan 0.675  5567 False
A1     F 0.700 0.706 0.695 0.676 0.725  5567 True
A2     F 0.710 0.717 0.703 0.664 0.710  5567 True
A3     F 0.490 0.483 0.498 0.522 0.536  5567 False
A4     T 0.406 0.414 0.399 0.353 0.442  5567 False
B1     F 0.528 0.517 0.538 0.511 0.527  5567 False
B2     F 0.506 0.494 0.518 0.487 0.517  5567 False
B3     T 0.502 0.501 0.503 0.514 0.530  5567 False
B4     T 0.485 0.482 0.487 0.482 0.453  5567 False
C1     F 0.627 0.619 0.635 0.642 0.566  5567 False
C2     T 0.550 0.551 0.548 0.583 0.488  5567 False
C3     F 0.617 0.614 0.621 0.639 0.567  5493 False
C4     T 0.669 0.679 0.660 0.604 0.696  5567 True
C5     F 0.626 0.641 0.612 0.598 0.602  5567 False
D1     F 0.615 0.614 0.616 0.600 0.649  5567 False
D2     F 0.554 0.547 0.560 0.564 0.538  5567 False
D3     T 0.522 0.540 0.504 0.523 0.528  5567 False
D4     F 0.594 0.593 0.596 0.614 0.585  5567 False
D5     F 0.521 0.518 0.523 0.517 0.506  5567 False
D7     F 0.505 0.499 0.511 0.500 0.478  5567 False
E1     T 0.557 0.565 0.549 0.543 0.535  5567 False
E2     T 0.558 0.568 0.548 0.541 0.537  5567 False
E3     T 0.496 0.502 0.490 0.493 0.500  5567 False
E4     T 0.514 0.509 0.520 0.516 0.500  5567 False
E5     T 0.514 0.515 0.513 0.504 0.522  5567 False
E6     F 0.534 0.541 0.527 0.521 0.532  5567 False
E7     T 0.626 0.637 0.615 0.527 0.675  5567 False
F1     T 0.571 0.582 0.560 0.588 0.528  5567 False
F2     F 0.603 0.607 0.599 0.615 0.550  5567 False
F3     T 0.539 0.554 0.525 0.546 0.525  5567 False
F4     T 0.565 0.576 0.553 0.580 0.523  5567 False
F5     T 0.593 0.607 0.579 0.567 0.615  5567 False

```

Declared findings that pass: A1 min(|a|,|b|) 0.70, A2 |a|+|b| 0.71, C4 centroid cosine A-B 0.67.
Not supported: inclusion (B), family-graph connectedness (E1/E2 0.56 - "twins are more connected" is weak),
DAG position (D), resampling co-clustering (F, 0.54-0.60).

## Post-hoc diagnostics (labelled post-hoc)
```
--- post-hoc diagnostics ---
size |U| (F dir) AUC 0.662
A1 stratified by |U| bins 0.643 ; A2 0.652 ; J 0.659 ; C4 0.719
A1 stratified by J band x |U| bin 0.604 ; C4 0.666

min(|a|,|b|) table: n, twin%
  1-1: n=   74 twin%=91.9
  2-2: n= 1644 twin%=68.9
  3-3: n= 1886 twin%=52.1
  4-5: n= 1367 twin%=36.4
  6-8: n=  437 twin%=15.1
  9-15: n=  144 twin%=3.5
  16-+: n=   15 twin%=6.7

J band x min-diff: twin% (n)
0.4-0.5:  [1-2] 55% (509) [3-5] 36% (1393) [6-+] 11% (329)
0.5-0.6:  [1-2] 69% (649) [3-5] 49% (1339) [6-+] 15% (209)
0.6-0.7:  [1-2] 84% (560) [3-5] 60% (521) [6-+] 10% (58)

C4 (centroid cosine A vs B) quantile bins: twin% (n)
  bin0 C4 0.671-0.900: twin% 29.1 (n=1114)
  bin1 C4 0.900-0.922: twin% 40.1 (n=1113)
  bin2 C4 0.922-0.939: twin% 50.3 (n=1113)
  bin3 C4 0.939-0.954: twin% 57.2 (n=1113)
  bin4 C4 0.954-0.963: twin% 67.0 (n=557)
  bin5 C4 0.963-0.987: twin% 74.0 (n=557)

candidate merge rules (post-hoc, descriptive): n, twin% (precision), share of all twins caught (recall)
  J>=0.65 (old)            n=  351 precision=72.4% recall=9.2%  [half1 76.0 / half2 68.6]
  J>=0.6 & mindiff<=2      n=  560 precision=83.9% recall=17.1%  [half1 85.9 / half2 81.7]
  J>=0.5 & mindiff<=2      n= 1209 precision=76.1% recall=33.4%  [half1 78.2 / half2 73.8]
  mindiff<=2               n= 1718 precision=69.8% recall=43.6%  [half1 72.1 / half2 67.6]
  C4>=q90                  n=  557 precision=74.0% recall=15.0%  [half1 76.3 / half2 71.4]
  C4>=q80                  n= 1114 precision=70.5% recall=28.5%  [half1 72.5 / half2 68.3]
  C4>=q80 & mindiff<=2     n=  438 precision=88.6% recall=14.1%  [half1 89.7 / half2 87.2]
  C4>=q60 & mindiff<=2     n=  842 precision=81.8% recall=25.0%  [half1 82.9 / half2 80.7]
```

## Reading
- The clearest separator is how many pathways actually differ: with <= 2 differing members on one side, 70% twin
  (84% if J >= 0.6); with >= 6, 85-96% facet. A facet needs a block of distinguishing pathways.
- Principled cutoff without labels: the pipeline's minimum cluster size is 3, so a difference block of <= 2
  cannot be a theme of its own.
- C4 (whole-theme embedding similarity) adds signal beyond overlap and size (0.67 stratified by J band x size).
- Errors at small differences are real facets added by a small block (e.g. selenium vs vitamin B6 in sulfur
  amino acid metabolism; NOTCH1 vs p75NTR proteolysis; cardiac vs skeletal muscle growth).
- Caveat: the judge sees only_A/only_B lists; short lists may bias it toward 'twin'. Judge repeat agreement 87.5%.
- Thresholds read off the tables are partly calibrated on LLM labels; only the min-size-3 argument is label-free.
- Not yet assessed: what transitive merging inside families would do.
