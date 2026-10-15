# Naming O50 with naming-c1 (reviewer, 2026-10-14, before any naming)

Method: naming-c1 exactly as specified in spec/ALGORITHM.md (copied unchanged from the 11 Oct pilot), applied to the
adopted working build thema_L_x2_O50 (adoption pending formal record by ccode; Aviyah's decision 13-14 Oct).
- Scope: the 4,591 O50 themes with 3-200 members. The 11 themes above 200 members (incl. the 4 giants) are out of
  naming-c1's scope and need a separate procedure, to be specified later.
- Inputs built by code/nm_build.py (the pilot's np_build.py with the build path switched to O50 and all themes
  instead of a sample): confusables by the spec's label-free rule, member/confusable order by the spec's seeds,
  theme order random.Random(7), 25 themes per file per candidate slot, 552 files.
- Namers and judges: in-session subagents of the reviewer session (configured model claude-opus-5-5), no API spend.
  One subagent per file; slots run in separate contexts.
- Selection, uniqueness and evaluation: the pilot's scripts (np_sel, np_select, np_dup, np_dedupsel), adapted only
  in paths.
- Code equivalence (Aviyah, 14 Oct): ccode's offline mode of scripts/name_themes_c1.py must reproduce, from the same
  raw outputs, every input, intermediate and final file byte-identically. Any difference is reported.
- Evaluation after naming, on a random 200 themes (seed 20261014), fresh judges: E1 back-match (pilot 91.5%),
  E2 member fit (pilot 0.917), E4 duplicates (0). E3 reproducibility on 60 themes (pilot 60% equivalent, 98%
  equivalent-or-nested). Non-inferiority to the pilot: E1 and E2 within 5 points.
