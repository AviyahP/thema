# Full census: every remaining theme of size 3-100 (2026-10-09)

All 5,603 themes of size 3-100 not covered by samples 1-3 (sample4_rest.json), judged with rubric4.md by 40 reviewer subagents (judged4_rest.json). With samples 1-3 and round-1's full check of the 42 themes over 100, every theme in thema_L_repair has now been judged once.

| band | n | coherent | umbrella | core+misfits | mixture | incoherent | ok |
|---|---|---|---|---|---|---|---|
| 3-5 | 310 | 305 | 2 | 2 | 0 | 1 | 99.0% |
| 6-10 | 1358 | 1237 | 79 | 24 | 9 | 9 | 96.9% |
| 11-20 | 2794 | 2451 | 260 | 50 | 20 | 13 | 97.0% |
| 21-50 | 1003 | 862 | 119 | 12 | 8 | 2 | 97.8% |
| 51-100 | 138 | 107 | 30 | 0 | 1 | 0 | 99.3% |
| all | 5603 | 4962 | 490 | 88 | 38 | 25 | 97.3% |

All themes of size 3-100 (samples 1-3 + census): 8,529 of 8,756 ok (97.4%). Sample estimates (97.2-98.1%) held.

## Where the 151 census problems come from
1. Self-described heterogeneous BTMs (the 17 to be dropped): present in 21 of 25 incoherent themes, 3 mixtures, 17 core+misfits (41 of 151).
2. Gene-specific transcription-regulation sets (e.g. regulation of CDH1, PTEN, PD-L1, RUNX3, PAX3 targets, TF motif sets): they group by the form "transcriptional regulation of gene X" rather than by process. 2 of the 4 other incoherent themes (n07120, n04626) and several mixtures (n06818, n05584, n05407, n08707, n07636).
3. Orphan small terms with no natural home (magnesium transport, protein oligomerization, creatine, inositol transport, NLRP1): a small nested family of grab-bags (n04488, n04261, n07856, n03531, n01731).
4. Developmental-signalling pairs judged strictly as mixtures: Wnt + Notch (58), Notch + Hedgehog (38), MET + TGF-beta + Hippo (32), MET + Hippo (20). A biologist could call these a "developmental/oncogenic signalling" umbrella; the rubric required a specific mechanism.
5. Isolated pairings: kynurenine-NAD + polyamines (28, 24), trophoblast + eye (30), surfactant + Rh transport (21), olfaction + hearing (21), vitamin K + vitamin C (13).

Caveat: judges are LLM subagents reading member names (and, for unnamed BTMs, the generated description and genes); names are not used in construction.
