# Home-fit judging rubric

Each item shows one TARGET pathway (name and a short description) and several GROUPS of other human biological pathways
(G1, G2, ...). Each group is shown as its complete member list; the target itself is not listed in any group.

For each group, decide whether the target pathway belongs in that group, judged by biological meaning:
- "yes": the target clearly fits the group's theme; a biologist would expect to find it there.
- "partly": the target fits one aspect of the group, or fits only loosely.
- "no": the target does not belong; the group's theme is about something else.

Then, considering only the groups you answered "yes" or "partly", judge how they relate as homes for the target:
- "different_aspects": they show different aspects, roles or contexts of the target (e.g. the same pathway seen in
  development vs in disease, or as part of signalling vs of metabolism).
- "same_aspect": they show essentially the same aspect of the target.
- "unrelated": no coherent link between them as homes for this target.
- "na": fewer than two groups were "yes" or "partly".

Read every group in full. Judge by biology, not by shared words.

Return a JSON list with one object per item:
{"item_id": "...", "fit": {"G1": "yes"|"partly"|"no", ...}, "relation": "different_aspects"|"same_aspect"|"unrelated"|"na", "reason": "one short sentence"}
