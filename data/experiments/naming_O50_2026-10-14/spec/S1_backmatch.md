# S1 / E1 — back-matching prompt (naming-c1). Used for SELECTION (S1) and, by different fresh judges, for EVALUATION (E1)

Each item shows a NAME and five overlapping clusters of human biological pathways, labelled A to E. You see the pathways common to all five once ("in_all"), then what each cluster contains beyond that ("also_in"). Decide which ONE cluster the name describes best. The clusters overlap heavily, so decide by the pathways that differ. Judge by biological meaning, not by shared words.

Return one JSON object per item: {"item_id": "...", "choice": "A"|"B"|"C"|"D"|"E"}
