# Prompt 46 areas: blind reading of all 66 areas. Declared 18 Oct 2026, before any reading

Evaluation only; nothing feeds into construction. Population: every area in data/ontology/v0.4-leaves/thema_L_x2_O50s_roots_areas/ (66 areas, 12 of them roots).

## Reading
- Each area is read from its full member list (pathway name and source), no names, no structure shown. Random ids (seed 20261018), shuffled. Batches of about 2,600 lines; an area larger than that is read alone.
- One verdict per area:
  - **coherent:** one recognisable biological theme;
  - **broad domain:** one recognisable broad biological domain of the kind a textbook chapter or a top-level ontology term covers (for example metabolism, immune system, cell cycle and genome maintenance, development), with many sub-themes that all belong to it;
  - **linked umbrella:** 2-3 clearly related sub-themes under one recognisable idea;
  - **core with misfits:** a clear core plus 10% or more unrelated members;
  - **unlinked mixture:** unrelated blocks with no single domain;
  - **incoherent.**
- Plus a short label (up to 8 words), and for anything other than coherent a one-line reason; for mixtures, the main blocks.
- **Change from the 18 Oct roots reading, declared now:** the class "broad domain" is new. It was added at Aviyah's request, because the earlier classes capped umbrellas at 2-3 sub-themes, which no group of thousands of pathways can meet.

## Reported
- Share of areas that are coherent, broad domain or linked umbrella: overall, for the 12 roots, and by size (51-200, 201-500, 501-1,000, over 1,000). Prompt 46's bar for roots is 80%.
- **Aviyah's structural question, declared now:** a mixture is acceptable if what lies underneath it is a small number of coherent areas. For each root read as a mixture or as core with misfits, report its direct child areas, their verdicts, and the share of the root's pathways that its passing child areas cover.

Readers are in-session subagents with no API spend, each batch read independently.
