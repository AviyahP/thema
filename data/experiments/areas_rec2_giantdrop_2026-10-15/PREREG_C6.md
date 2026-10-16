# C6, blind intruder test on rec2 with giant areas dropped. Declared 15 Oct 2026, before any judging

**Scope**
- The build is thema_L_x2_O50_rec2, minus the 8 areas over 1,000 pathways (Aviyah's giant-drop rule).
- Every remaining area with at least 4 units is tested: 335 areas.
- The pass rule is the one declared in prompt 34.

**Item (one per area, seed 20261015)**
- **Units of an area:** all units under it (area_edges.tsv).
- **Insiders:** 5 units drawn at random from the area's units. If the area has fewer than 5, all of them are used.
- **Intruder:** 1 unit drawn at random from the units not under the area. It must also have less than 50% of its pathways inside the area's pathway set (declared now; this keeps an intruder from being a near-copy of the area).
- **Presentation:**
  - Units are shuffled and labelled A-F (A-E when there are 4 insiders).
  - Each unit is shown as its full list of pathway names with source, sorted alphabetically.
  - No ids, theme names or labels are shown.
- **Key:** KEY_DO_NOT_SHARE_C6.json. It stays on the Mac and is never shown to judges.

**Judges**
- One model judge per item (in-session subagent, no API spend).
- The judge is asked: "which unit does not belong with the others?". It must pick exactly one, with a one-line reason.

**Pass:** the intruder is spotted in at least 70% of the 335 areas. Chance is about 17%.

**Reported, not gated:**
- the hit rate by area size band and by support band;
- the hit rate on the 57 areas that are top roots;
- a list of the areas where the intruder was missed.
