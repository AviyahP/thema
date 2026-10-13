# THEMA naming algorithm naming-c1 (contrastive, 3-candidate, back-match selected) — specification

Written 2026-10-11 by the reviewer, BEFORE the pilot ran. The pilot executes exactly this with in-session subagents;
ccode's API implementation must reproduce it with the same templates (files in this folder) and the same model.

## 0. Model
- Pilot: the reviewer session's model (configured id claude-opus-5-5; serving model recorded in the run log).
- API implementation: the same model id. Temperature: provider default for the pilot; API run must record its setting.
  LLM output is not bit-reproducible; equivalence is tested on metrics (section 6), not on strings.

## 1. Eligible themes
c85 build themes with 3 <= size <= 200 (larger themes need a separate procedure; out of scope for naming-c1).
Giant themes (>= 1,000 members) are never used as parents or confusables.

## 2. Inputs (built by code, deterministic)
- Member rendering: one line per member, "- <title>". A BTM member whose title is "TBA" is rendered as
  "- [untitled BTM module] <first two sentences of its pathway_descriptions.tsv description>".
- Member order: shuffled with seed = sha256(theme_id + ":" + candidate_index) (first 8 hex digits as int).
- Confusables (up to 4), label-free:
  a. candidates = themes that share >= 1 non-giant parent with T, are not nested with T (neither contains the other),
     have size <= 200;
  b. rank by cosine between member centroids (vectors_leaves_centred of the x2 universe, rows L2-normalised, centroid
     = mean, then normalised); take the top 4;
  c. if fewer than 4, fill from all non-nested themes with size in [|T|/3, 3|T|] and <= 200, same ranking.
- For each confusable C: only_in_theme = T - C (all titles), only_in_confusable = C - T (all titles), n_shared.
  Confusable order shuffled with the same seed rule.

## 3. Naming (N1_namer.md)
- 3 independent candidates per theme (candidate_index 0, 1, 2), each from a separate model context that sees no other
  candidate. (Pilot: one subagent per candidate slot per batch of themes; themes treated independently.
  API: one call per theme per candidate.)

## 4. Selection (S1_backmatch.md), deterministic given the judgements
- Each nameable candidate is back-matched once: name + T and its 4 confusables as A-E (order shuffled with
  seed sha256(theme_id + ":S" + candidate_index)), rendered as in_all (intersection of the 5) + also_in per cluster.
  correct = judge picks T. (If T has fewer than 4 confusables, use what exists; chance = 1/(k+1).)
- If >= 2 of 3 candidates say nameable = false: the theme is UNNAMEABLE (report the rationale of candidate 0).
- Otherwise pool = correct nameable candidates; if empty, pool = all nameable candidates and the theme is flagged
  low_confidence.
- Winner = medoid of the pool by token-set Jaccard on lowercased content words (stop words: a, an, the, of, and, in,
  to, by, for, via, with, on, from, at), similarity measured against ALL nameable candidates; ties -> lowest index.
- Confidence shipped with the name: n_correct (0-3) and n_nameable.

## 5. Uniqueness (code)
- Normalise (lowercase, collapse spaces, strip punctuation). If two final names collide, re-run N1 for both themes
  with each other added as a confusable and the line "The name '<name>' is already used by another theme; give a
  name that distinguishes this theme." appended; then re-select (section 4). At most 2 rounds; residual collisions
  are reported, never silently suffixed.

## 6. Evaluation (fresh judges, never used in sections 3-5)
- E1 back-matching (S1_backmatch.md), new re-shuffle seed sha256(theme_id + ":E" + arm).
- E2 member fit (E2_fit.md): fit = 1 - misfits / size.
- E3 reproducibility (E3_equivalence.md): an independent second run of sections 2-4 (new contexts, candidate seeds
  +10) on a subset; compare final names.
- E4 duplicates among final names.
- API-equivalence test for ccode: run sections 2-5 via the API on >= 100 pilot themes; E1 and E2 of the API names must
  be within the pilot's 95% CI (non-inferior by <= 5 points), E3 API-vs-pilot equivalent-or-nested >= 85%.
