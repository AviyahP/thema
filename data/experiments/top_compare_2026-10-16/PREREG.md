# Top-level quality: option 1 (O50 as is) vs option 2 (O50 + areas, giants kept). Declared 16 Oct 2026, before any judging

**Option 1:** the roots of the frozen O50. There are 188: 4 giants plus 184 small roots.
**Option 2:** the roots of thema_L_x2_O50_rec2fix with giants left in. There are 42.

**Labels**, the same source wherever possible:
- O50 themes: dedup names plus overrides.
- The 6 anchor themes and the area roots: root_labels.json, the 15 Oct readers.
- Giants: G1_readings.json, the 15 Oct giant readers.

## Test A: the top-level menu

- Two menus, shown in random order as A and B. Each lists the roots as label plus size in pathways.
- 5 independent model judges each answer:
  - which menu is the better top level for browsing human pathway biology;
  - a 1-5 score per menu for coherence of entries, redundancy (5 = none) and usefulness.

## Test B: per-pathway homes

- 60 random pathways (seed 20261016).
- For each pathway, the judge sees the top-level entries that contain it under each option, as A and B in random order per item.
- The judge picks A, B or tie, with a reason.
- 3 independent judges per item; the per-item verdict is the majority.

**Decision rule:** option 2 is preferred if, excluding ties, it wins more items than it loses with a two-sided sign test p < 0.05. Option 1 is preferred if the reverse holds. Otherwise there is no difference.

**Caveat, stated now:** the labels come from different readers, and option 2's 42 entries are inherently easier to scan than 188. Test A therefore partly measures size; Test B is the fairer test.
