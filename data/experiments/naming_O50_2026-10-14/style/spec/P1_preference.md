# P1: name preference prompt (naming style pilot)

Each item shows a cluster of human biological pathways (complete member list) and two names for it, A and B. Which name would a biologist find clearer and more useful as a label for this cluster?

- A good label says what the cluster is about as a whole, is true of its members, and is easy to read.
- A name that misstates the members is worse, however well it reads.
- Answer "A", "B" or "equal".

Return one JSON object per item: {"item_id": "...", "choice": "A"|"B"|"equal", "reason": "one short sentence"}
