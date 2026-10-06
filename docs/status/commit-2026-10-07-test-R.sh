set -e

git add .gitignore scripts/stop_engine_jobs.sh

git commit -m "Ignore Test R score arrays, and stop the Test R jobs too" -m "The heights beside the trees were already covered by the .npz rule; this adds the transfer
universes. Both are regenerable from the persisted trees plus a recorded subsample seed, and the
heights alone are 111 MB.

stop_engine_jobs.sh now also names the Test R drivers, so one command stops everything and proves by
PID that nothing remains. It was written after orphaned worker pools exhausted this machine on
6 Oct, and extending it is cheaper than remembering which patterns to pass."

git add src/thema/ontology/gap.py tests/ontology/test_gap.py

git commit -m "Gap scores from Ward merge heights, in a new module so no provenance moves" -m "EXPLORATORY, for Test R. New file by requirement: recurrent.py, cut_trees.py and engines.py are
untouched, so no cached side provenance fingerprint changes. The heights these scores need are
computed inside tree_from_subset and thrown away, so they are recomputed here rather than by
changing what wrote the trees.

Three scores: h_full, the median height at which a grouping forms over the runs that found it;
G_loo, the leave-one-out gap, how far up an outsider first arrives when one member is dropped; and
G_life, the classic lifetime.

A REWRITE THAT MATTERED. The first score_side looped over grouping-run pairs and called the LCA on
one-element arrays. At the real scale, 73,483 groupings against 200 runs is about five million walks
each costing a few hundred NumPy calls on arrays of length one, and it would have taken hours. It
was killed and rewritten run-major: one pass per run, every qualifying grouping in a single batch,
seven vectorised LCA folds and a short vectorised climb. Scoring went from hours-projected to 17
seconds.

Because that is the kind of rewrite that silently changes an answer, there is an equivalence test: a
deliberately naive reference implementation, one grouping and one run and one walk at a time, on a
fixture with mixed grouping sizes and real 80 percent draws, asserted to match the fast version on
all four outputs including the NaN pattern. Nine tests in total, including the LCA case a naive lift
gets wrong, where one node is the ancestor of the other."

git add scripts/test_r_heights.py scripts/test_r_pool.py scripts/test_r_transfer.py scripts/test_r_biolord.py scripts/test_r.py

git commit -m "Test R drivers: heights, pools, transfer universes and the report" -m "Stage 1 regenerates each needed Ward tree from its recorded sample with the same two functions
tree_from_subset uses, in the same order, and ASSERTS the result equal to the persisted tree on both
present and clusters. 1,800 trees passed. That assertion is the spec own stop condition and it is
not decoration: a height taken from a tree that is not the tree the build used would be measuring a
different dendrogram.

Stage 2 recomputes the pool per side, because G_loo needs only the trees but h_full is defined over
runs where the grouping is FOUND, which is the matching verdict and is not cached. The matched copy
in each run is mapped back to its full-dendrogram node exactly, since the recording rule and the cap
filter are both reproducible.

The transfer driver builds a universe from a subset of the v0.3 rows, recentred and renormalised as
the method would, draws 200 subsamples under the same 80 percent rule, builds its own trees with
heights and scores the real side plus two scramble seeds.

test_r_biolord.py exists because the brief asked for the existing embeddings_biolord.npy and that
file is 1854 by 768, the v0.1 and v0.2 universe, so it cannot serve the 10,770. BioLORD-2023 is
wired into embed.py and already in the local HuggingFace cache, so the matrix is produced locally
with no API spend and written to a new file. BioLORD effective limit is 128 tokens against MedCPT
longer window, so these descriptions are truncated for it, which makes that transfer a harder test
rather than an easier one.

The unit Test R works in is stated in test_r.py docstring and in the report: pool GROUPINGS, not
completed families, because h_full is a property of a grouping and of nothing downstream. Every
number is computed on that unit for the fixed cut, the floors and the gap alike, so the comparison
is internally valid while not being interchangeable with Test F family-level FDR."

git add docs/spec/test-R-2026-10-07.md docs/status/2026-10-07-test-R.md docs/status/commit-2026-10-07-test-R.sh

git commit -m "Test R: G_loo is inverted, the floors stay, and the floors transfer" -m "NEITHER GAP VERSION IS PROMISING, under criteria declared before any number existed. The
per-size version fails criterion b and nothing else, keeping 52,098 real groupings against the
floors 55,055. The single-t version fails all four.

G_loo IS STRONGLY ANTI-PREDICTIVE: AUROC 0.0715 to 0.1116 across sizes 3 to 6, with scrambled
groupings showing LARGER leave-one-out gaps than real ones by about 60 percent at every size. The
mechanism is clean and the geometry was right while the population was backwards. A real small theme
sits in a crowded neighbourhood, so when a member is dropped the nearest outsider is right there and
the gap is small. A scrambled grouping survives support 0.33 precisely because it is isolated, so
its next merge is far away and the gap is large. The score measures isolation, and real small themes
are the dense ones.

What the two gates disagree about has a direction. The 6,672 groupings the floors keep and the gap
rejects are 1.45 times better by the curated-set proxy than the 3,715 the gap keeps and the floors
reject, 11.2 percent against 7.7 percent. At size 3 the floors keep 4,291 and the gap keeps 128, and
the two agree on 15 of them.

A single rule for every size would remove three quarters of the 11 to 50 band, and the removed
groupings are as good as the kept ones, 12.8 percent against 12.0 percent. It separates dense from
sparse, not good from bad.

THE MOST USEFUL RESULT IS ABOUT THE FLOORS, NOT THE GAP. The 10,770 3-seed floors transfer
UNCHANGED to a different universe size, Reactome-only at 2,836 rows, and to a different encoder,
BioLORD over the same 10,770, with held-out FDR of 0.00126 and 0.00067 against a 0.01 cap. So
calibrate-once is already available without any new score, Test F transfer rule is confirmed on two
settings, and a future score has to beat that rather than beat per-dataset calibration.

The side-finding worth following up is G_life, the classic lifetime, which separates real from
scrambled at AUROC 0.929 to 0.991, better than support alone at every size. Arm K is built on it.

I also corrected my own first framing in the status file. I had compared the gap gate against the
fixed cut and reported 70.9 percent kept; criterion b compares against the floors, where it is 94.6
percent, and the damage is concentrated at sizes 3 and 4 rather than general."

git push
