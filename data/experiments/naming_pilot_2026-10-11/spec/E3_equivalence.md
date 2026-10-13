# E3 — reproducibility prompt (naming-c1)

Each item shows a cluster of human biological pathways (complete member list) and two names written for it independently. Do the two names denote the same theme with the same emphasis?
- "equivalent": same theme and same emphasis, wording aside.
- "nested": same theme, but one is clearly broader or narrower, or one adds a distinction the other lacks.
- "different": they describe different themes or emphases.

Return one JSON object per item: {"item_id": "...", "verdict": "equivalent"|"nested"|"different"}
