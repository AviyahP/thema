# E2 — member-fit prompt (naming-c1)

Each item shows a NAME for a cluster of human biological pathways and the cluster's COMPLETE member list. List every member that does NOT belong under the name, i.e. concerns different biology. A member whose title is worded more broadly or more narrowly than the name still fits if it is part of that theme. Untitled BTM modules are shown by a short description; judge them by that biology.

Return one JSON object per item: {"item_id": "...", "misfits": ["exact member text", ...]}
