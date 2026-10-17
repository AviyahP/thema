# Are the giants grab bags or wide themes? Declared 15 Oct 2026, before any reading or judging

**Scope:** the 8 area giants of thema_L_x2_O50_rec2fix (giants.tsv) and the 4 O50 giants (themes over 1,000 pathways). Evaluation only; nothing is built or adopted.

## G1, reading

- Each giant is read from its **full member list** by a model reader (in-session subagent, no API).
- The reader gives:
  - a label (at most 10 words);
  - contents with rough shares;
  - a verdict, one of:
    - **one wide theme**: a single broad area a biologist would name, like GO's "metabolic process";
    - **two themes**: two recognisable areas joined;
    - **mixture**: three or more unrelated blocks;
  - an off-topic share.

## G2, blind intruder test at giant level (seed 20261016)

- **Insiders:** direct children of the giant with 10 to 150 pathways. For area giants these come from area_edges.tsv; for O50 giants, from nodes.tsv.
- **Intruder:** a node with 10 to 150 pathways, drawn from O50 themes and non-giant rec2fix areas, with less than 50% of its pathways inside the giant.
- **Items:** 5 per giant. Each item has 5 insiders drawn at random (all of them if the giant has fewer than 5 eligible) plus 1 intruder, shuffled and labelled A-F.
- **Presentation:** full pathway lists with their source. No ids or names.
- **Key:** KEY_DO_NOT_SHARE_giants.json, which stays on the Mac.
- **Judging:** one model judge per item; items from all giants are mixed across batches.

**Per giant:**

| intruder spotted | verdict |
|---|---|
| ≥4 of 5 | coherent wide theme |
| 2-3 of 5 | partial |
| ≤1 of 5 | grab bag |

By chance, 4 or more of 5 happens with p ≈ 0.003.

## Reported

- G1 and G2 per giant, side by side.
- Where they disagree, both are shown; neither overrides the other.

## Amendment, made before any reading or judging

The area giants have no direct-child edges in rec2fix, because giants are outside the view, so the insider rule above gives zero eligible insiders for them.

**Amended insider rule, the same for all 12 giants:** a node is eligible if it

- has 10 to 150 pathways,
- is strictly inside the giant,
- is either an O50 theme or a non-giant rec2fix area, and
- is not strictly inside another eligible node of the same giant (the maximal ones).

Everything else is unchanged.
