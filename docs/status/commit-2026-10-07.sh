set -e

git add .gitignore scripts/stop_engine_jobs.sh

git commit -m "Ignore Test R and naive K caches, and stop those jobs too" -m "Test R score arrays and transfer universes, and the naive K candidate arrays. All regenerable:
the naive K real build is 8.8 seconds from the committed universe and the recorded run seeds, and
the Test R heights alone are 111 MB. stop_engine_jobs.sh now names the Test R drivers too, so one
command stops everything and proves by PID that nothing remains."

git add src/thema/ontology/gap.py tests/ontology/test_gap.py scripts/test_r_heights.py scripts/test_r_pool.py scripts/test_r_transfer.py scripts/test_r_biolord.py scripts/test_r.py

git commit -m "Test R: gap scores from Ward merge heights" -m "EXPLORATORY. New files by requirement, so recurrent.py, cut_trees.py and engines.py stay
untouched and no cached side provenance moves. Stage 1 regenerates each needed Ward tree from its
recorded sample with the same two functions tree_from_subset uses and ASSERTS the result equal to
the persisted tree on both present and clusters; 1,800 trees passed.

score_side was rewritten run-major after the first version projected to hours at the real scale, and
there is an equivalence test against a deliberately naive reference to catch exactly the kind of
silent change that rewrite risks. Nine tests, including the LCA case a naive binary lift gets wrong,
where one node is the ancestor of the other.

test_r_biolord.py exists because the brief asked for the existing embeddings_biolord.npy and that
file is 1854 by 768, the v0.1 and v0.2 universe, so it could not serve the 10,770. BioLORD-2023 is
wired into embed.py and already cached locally, so the matrix is produced with no API spend."

git add docs/spec/test-R-2026-10-07.md docs/status/2026-10-07-test-R.md

git commit -m "Test R result: G_loo is inverted, the floors stay, and the floors transfer" -m "NEITHER GAP VERSION IS PROMISING under criteria declared before any number existed. The per-size
version fails criterion b and nothing else, keeping 52,098 real groupings against the floors 55,055.
The single-t version fails all four.

G_loo is strongly ANTI-PREDICTIVE: AUROC 0.0715 to 0.1116, with scrambled groupings showing LARGER
leave-one-out gaps than real ones at every size. The geometry was right and the population was
backwards. A real small theme sits in a crowded neighbourhood, so dropping a member puts an outsider
right there. A scrambled grouping survives support 0.33 precisely because it is isolated. The score
measures isolation, and real small themes are the dense ones.

What the two gates disagree about has a direction: the 6,672 groupings the floors keep and the gap
rejects are 1.45 times better by the curated proxy than the 3,715 the gap keeps and the floors
reject. At size 3 the floors keep 4,291, the gap keeps 128, and they agree on 15.

THE MOST USEFUL RESULT IS ABOUT THE FLOORS. The 10,770 3-seed floors transfer UNCHANGED to a
different universe size, Reactome-only at 2,836 rows, and to a different encoder, BioLORD over the
same 10,770, with held-out FDR of 0.00126 and 0.00067 against a 0.01 cap. Calibrate-once is already
available without any new score, so a future score has to beat that rather than beat per-dataset
calibration.

I also corrected my own first framing in the status file: I had compared the gap gate against the
fixed cut and reported 70.9 percent kept, where criterion b compares against the floors and the
figure is 94.6 percent, with the damage concentrated at sizes 3 and 4."

git add docs/spec/arm-K-2026-10-07.md docs/spec/eval-protocol-2026-10.md

git commit -m "Arm K spec and Amendment A1, both ON HOLD not cancelled" -m "Copied verbatim from the two messages that replaced an earlier paste cut off mid-sentence, which
was never run: its own integrity line said it would end with END OF PROMPT and it did not, so it was
stopped rather than guessed at.

The spec first paragraph records that the design was motivated by Test R results ALREADY SEEN, the
G_life AUROC of 0.929 to 0.991, so it is not pre-registered. That is the weaker but honest guarantee
available, and stating it is the point.

Both the spec and Amendment A1 are marked ON HOLD in place. The full Arm K and E1 to E4 run was
stopped before any of it started, in favour of a naive K probe with fixed cutoffs, and neither
document is amended by that probe."

git add scripts/naive_k.py scripts/naive_k_report.py src/thema/ontology/mutualrank.py tests/ontology/test_mutualrank.py data/ontology/v0.3x_engines/K_naive/nodes.tsv data/ontology/v0.3x_engines/K_naive/members.tsv data/ontology/v0.3x_engines/K_naive/edges.tsv data/ontology/v0.3x_engines/K_naive/unplaced.tsv data/ontology/v0.3x_engines/K_naive/manifest.json docs/status/2026-10-07-eval-run.md

git commit -m "Naive K: a mutual-rank ladder, excellent themes, and almost no coverage" -m "EXPLORATORY direction probe with cutoffs chosen in advance and not fitted: support 0.33 and
lifetime 2, meaning the group survives while k at least doubles. New module, so the three protected
files stay untouched.

EARLY STOP NOT TRIGGERED. Scramble seed 3001 gives ZERO themes at the declared cutoff against the
real build 593, which is 0.00 percent against a 5 percent rule. At the report-only cutoff 1.5 it
gives 6 against 2,276.

THE QUALITY PROXY IS THE STRIKING RESULT. Share of themes whose best match to a curated set of the
same source exceeds Jaccard 0.5: K at lifetime 2 scores 59.5 percent on Reactome and 25.8 percent on
GO, against arm A 38.6 and 9.0, and against HiDeF maxres 25 at 26.7 and 0.9. On GO that is 29 times
HiDeF. The proxy is not the protocol E1 and must not be read as it, but the gap is not marginal.

THE CATCH IS COVERAGE AND IT IS SEVERE. Those 59.5 percent are 232 themes. The build places 1,410 of
10,770 pathways and leaves 90.6 percent effectively unplaced, against arm A 1.31 percent, and it
produces NO theme between 51 and 500 members. Under the engine rule own gates it would fail G3 by a
factor of eighteen and would have nothing to offer in the two middle bands the engine search exists
to fill.

The engine does propose mid-size structure, 2,569 candidates of 51 to 500 members. Support removes
87 percent of them, their median support being 0.020, and lifetime removes the rest; the mid-size
survivors of the support gate have median lifetime 1.250. Lifetime 2 is a high bar for everything,
since even 3 to 10 candidates that pass support have median lifetime 1.333.

The whole real build is 8.8 seconds at 1.21 GB, against HiDeF 126 seconds and arm A 27.7 minutes
with 3-seed floors.

ONE TOY FINDING IS RECORDED BECAUSE IT CONTRADICTS THE REAL DATA. On a planted fixture of two tight
groups of twelve plus ten noise points, lifetime is INVERTED: noise triples score 42.67 and planted
groups 32.0, because the ratio is the rung after the last match over the first matching rung and a
tiny isolated triple connects at the lowest rung. On the real 10,770 the inversion does not appear.
The toy confounds size with plantedness so it is a warning rather than a verdict, and the test is
written to fail loudly if the toy inversion ever stops holding."

git push
