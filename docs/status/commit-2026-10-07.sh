set -e

git add .gitignore

git commit -m "Ignore preserved side caches: superseded and unprovenanced" -m "Two kinds of side cache are kept on disk and not committed. superseded_range_ holds the
sides cut under the two earlier resolution ranges, before amendments 3 and 4 changed the ladder.
no_provenance_mark holds the one arm A scramble side that had no provenance mark, so its origin
could not be established.

Both are kept rather than deleted because they are the record that those sides existed and what
replaced them, and both are ignored because they are caches either way. The .npz files inside were
already ignored; this adds the stages sidecars and the directories, so git status stops reporting
them as work in progress."

git add scripts/build_10770.py scripts/test_f.py

git commit -m "Test F: gate at a fixed cut with no calibration, and measure what that costs" -m "--fixed-cut gates every stratum at one support with NO calibration, cutting no scramble side
and solving and writing no floor. It is expressed as a solved-shaped list with the same threshold in
every stratum, so the gate, the consensus, the Hasse pass and the manifest all run unchanged and the
only difference from a calibrated build is where the line sits. That is what makes the comparison a
comparison of two thresholds rather than of two code paths.

test_f.py runs steps 2, 4 and 6 and takes every FDR from the build own confirm(), not a
reimplementation. Step 2 is a declared SECOND READ of held-out seeds 4001 to 4005 and is labelled as
such in the output: no threshold is fitted at the fixed cut, so every seed is valid test data for
it, and the cut was declared in the protocol rather than chosen after seeing the FDR. The numbers
bear that out, with calibration-only and held-out-only agreeing to the third decimal in every
stratum. Step 4 solves floors from three seeds, which IS a fit, and confirms them on the same
held-out five, which is reported as a third read.

Step 5 is deferred to E1 and E2 and the report says so: transfer needs the Reactome-only, GO-only,
synthetic and SPECTER2 universes, none of which exist, and clarification 1 floors-transfer override
does not exist either."

git add data/ontology/v0.3/trees/centred_c54319cdfbbe9eb7/completions/cap3125_inc050/seed03003_n200.provenance.json data/ontology/v0.3/trees/centred_c54319cdfbbe9eb7/completions/cap3125_inc050/seed03003_n200.stages.json

git commit -m "Re-cut the one arm A side whose origin could not be established" -m "Of arm A sixteen cached sides, fifteen failed the current provenance fingerprint only in
dimensions that already have a byte-identity proof on record: the two keys I added on 6 Oct,
recurrent_sha256_16 from the B2 optimisation proved byte-identical on 5 Oct, and families indexed to
joined proved byte-identical on 2 Oct. Those fifteen are reused with allow-stale-cache, which exists
for exactly that case.

seed03003_n200 had NO PROVENANCE MARK AT ALL, cached before provenance was recorded. Reusing a side
whose origin cannot be established is the failure the guard was created for after the 2 Oct
corruption, and Test F is deciding whether to keep the FDR machinery, so its FDR numbers have to be
trustworthy. So it was re-cut: 433 s, peak 8.83 GB, 428,579 families.

THE RE-CUT FILE IS BYTE-IDENTICAL TO THE OLD ONE. The old side had been correct all along, and there
was no way to know that without doing the work. The old file is preserved under no_provenance_mark
rather than deleted. Every one of the sixteen sides now either matches the fingerprint exactly or
differs only where a proof exists."

git add data/ontology/v0.3/fixedcut_ward_10770/nodes.tsv data/ontology/v0.3/fixedcut_ward_10770/members.tsv data/ontology/v0.3/fixedcut_ward_10770/edges.tsv data/ontology/v0.3/fixedcut_ward_10770/unplaced.tsv data/ontology/v0.3/fixedcut_ward_10770/manifest.json

git add data/ontology/v0.3x_engines/fixedcut_leiden/nodes.tsv data/ontology/v0.3x_engines/fixedcut_leiden/members.tsv data/ontology/v0.3x_engines/fixedcut_leiden/edges.tsv data/ontology/v0.3x_engines/fixedcut_leiden/unplaced.tsv data/ontology/v0.3x_engines/fixedcut_leiden/manifest.json

git commit -m "The two fixed-cut builds Test F compares against" -m "Arm A at a fixed 0.33 in every stratum gives 7,412 themes against the calibrated build
6,244, and arm B gives 5,079 against 3,462. 94.5% of what A gains and 95.8% of what B gains is in
the 3 to 10 band; arm B 51 to 200 count is identical at 368. So the floors do exactly one job,
suppressing small themes, and the FDR table says what that job is worth.

The calibrated build is a STRICT SUBSET of the fixed-cut build: final-theme match at Jaccard 0.70 is
100.0% forward for arm A and 99.9% for arm B, with the asymmetry entirely in the themes the fixed cut
adds. Calibration is not reshaping the ontology, it is deleting a specific set of small themes, and
step 1 says those are the ones the null also produces.

These two builds exist only as the comparison Test F needs. They are not candidates and nothing
downstream reads them."

git add docs/status/2026-10-07-test-F.md docs/status/commit-2026-10-07.sh

git commit -m "Test F result: floors KEPT for both arms, in the three-seed form" -m "THE FIXED CUT FAILS BOTH ARMS BY A WIDE MARGIN. Arm A overall FDR 0.29881 against a 0.01 cap,
with the 4-member stratum at 2.15928, meaning it admits more than two false families for every real
one. Arm B overall 0.96394, with the 3-member stratum at 7.57169. Above size 6 the declared 0.33
really does already decide, and arm A 10-plus stratum has an FDR of exactly zero across 141,658 real
families, so the protocol was right about where the floors bind. It was wrong about what follows:
below size 6 the fixed cut is not merely imperfect, it is worse than useless, and the floors are
load-bearing precisely where they bind.

THREE SEEDS PASS FOR BOTH ARMS. Arm A held-out FDR 0.00252 against 0.00285 on ten seeds, arm B
0.00215 against 0.00189, both inside the declared caps. One real cost is arm B: with ten seeds it
keeps the 5-member stratum at a floor of 0.970 and with three seeds it drops it, so arm B on three
seeds admits no theme below six members. That narrows the fine band for the arm already weakest
there, and it is a consequence of the cheaper form rather than of the method.

So the declared decision, per arm as clarification 8 requires, and both arms landed in the same
place: Floors KEPT, form three seeds 3001 to 3003, reused across universes where the one-side check
passes.

HIDEF LETS THROUGH NOTHING. Zero communities on a scrambled matrix, in every band, on both null
seeds, so its implied FDR is 0.00000 everywhere and it needs no calibration at all. That is the
sharpest asymmetry Test F produced: the machinery THEMA cannot do without is machinery HiDeF does not
need. The honest caveat is that returning nothing on noise demonstrates specificity and not
sensitivity, and arm B own held-out FDR at its solved floors is 0.00189, also very low. The
difference is that THEMA number is bought with three to ten scramble sides per build and HiDeF is
free.

TIMING. Core build with no calibration 6.5 min for A and 7.1 min for B; with three seeds 27.7 and
37.9 min; with ten seeds 77.0 and 109.7 min; HiDeF 2.1 min with no calibration. Dropping from ten
seeds to three cuts the calibrated build by about 2.9x and moves THEMA from 37 to 52 times HiDeF
cost down to 13 to 18 times.

COST OF THE REST OF THE PROTOCOL, re-estimated with the three-seed form and the universes at their
true sizes rather than at 10,770: about 10 h on this Mac against my 6 Oct estimate of 25 to 35 h, and
about 2.6 h on a 32-core machine. The saving is almost entirely Test F, twelve fewer scramble sides
per universe build across the roughly 34 builds E1, E2 and E3 need. Neither figure includes writing
the code that does not exist, which Test F does not change.

E1 to E4 ARE NOT STARTED. Arms C, G and H stay paused and untouched, the frozen build and the naming
code are untouched, and Aviyah decides what happens next."

git push
