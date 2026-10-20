# Small-root nesting diagnostic: result, 18 Oct 2026
Plan declared in PLAN.md before running. x2 universe, 200 persisted subsamples, full Ward dendrograms rebuilt from centred vectors. Per-root table: per_root.tsv (run in the cloud workspace with code/nesting.py, same inputs). Validation: reproduced recurrence (J>=0.70) median 0.015 = build support median 0.015.
1. Small roots are rare groups: build support median 0.015 (3 of 200 runs); mean best-match J per run median 0.37.
2. No recurring parent group: 0/164 recur in >=50% of runs; 162 in <20%.
3. Nesting mostly inside giants: 132/164 nest (>=50% of runs) inside 2+ giants. Best non-giant container: nesting >=50% for 128, but it holds <80% of the root in 105.
4. Recombinations: covered >=90% by the union of 2 other non-giant themes with equal or higher support: 101/164 (40 fully); by 3 themes: 123 (61 fully); by 1 theme: 9.
Answer: a small root is a rare pairing of pieces of 2-3 stable themes; it passes the gate in ~3/200 runs, but no stable group contains it, so it has no strict parent and becomes a root.
