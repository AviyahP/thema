# O50s roots: blind baseline reading. Declared 18 Oct 2026, before any reading or judging

Evaluation only; nothing feeds into construction. It is the baseline against which prompt 46's top level (areas on the O50s roots) is judged, using the same tests as prompt 44's decision rule.

**Population:** every root of the O50s build (data/ontology/v0.4-leaves/thema_L_x2_O50s/), i.e. every node with no parent in edges.tsv: 261 nodes.

## R1, reading of every root

- Each root is read from its full member list (pathway name and source), with no theme name shown. Roots are given random ids (seed 20261018) and shuffled.
- One verdict per root, same classes as the O50s large-theme reading of 17 Oct:
  - **coherent:** one recognisable biological theme;
  - **linked umbrella:** 2-3 clearly related sub-themes under one recognisable idea;
  - **core with misfits:** a clear core plus 10% or more unrelated members;
  - **unlinked mixture:** unrelated blocks;
  - **incoherent.**
- The reader also gives a short label (up to 8 words) and, for anything other than coherent, a one-line reason.
- **Reported:** the share that is coherent or linked umbrella, overall and by size (≤50, 51-200, 201-1,000, over 1,000). Prompt 44's bar for a top level is 80%; here it is reported against that bar, but there is no pass or fail, because this is a baseline.

## S, small-root test (roots of 50 pathways or fewer)

- **Question:** is the small root a distinct topic, or does it belong as a sub-theme of one of the larger nodes that contain most of it?
- **Containers:** for each small root, the 3 larger O50s nodes (size > root size) with the largest share of the root's pathways inside them; ties broken by smaller size.
- **What the judge sees:**
  - the root's full member list;
  - for each container, labelled P, Q, R in random order: its size and a random sample of up to 40 of its members that are not in the root (all of them if 40 or fewer), seed 20261018. The judge does not see the overlap share.
- **Verdict:** distinct, or belongs under P, Q or R; with confidence high, medium or low; and a one-line reason.
- The letter-to-node key is KEY_DO_NOT_SHARE_O50s_roots.json; it stays on the Mac and is never shown to a judge.
- **Reported:** the count judged distinct; for the others, the overlap share and pathways missing for the container chosen. Prompt 44's bar is that every small root is distinct; it is reported against that bar, with no pass or fail.

## Readers and judges

In-session subagents, no API spend. Batches of about 2,600 lines. Each batch is read independently by one subagent, with these instructions and nothing else about the project.

## Known limits, stated now

- Containers are shown as samples, not full lists, because some are over 2,000 pathways.
- Model readers, not biologists.
