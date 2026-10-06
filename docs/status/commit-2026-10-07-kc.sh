set -e

git add .gitignore

git commit -m "Ignore the KC theme arrays, keep their summaries" -m "The .npz theme arrays regenerate in under three seconds from the committed universe. The .json
summaries beside them hold the counts, the level sizes and the closeness thresholds every number in
the report is read from, so those are re-included."

git add src/thema/ontology/kc.py scripts/kc.py

git commit -m "KC: one mutual-rank filtration, then recursive near-cliques" -m "EXPLORATORY. New module, so recurrent.py, cut_trees.py, engines.py and mutualrank.py stay
untouched.

Two changes from naive K. The fine level drops resampling entirely: naive K scored support over 100
edge-dropout runs and that gate removed 87 percent of its mid-size candidates at median support
0.020, so KC uses one filtration over the full graph and keeps a group on its lifetime, death_k over
birth_k, which is a property of the single nested sequence of graphs. And the middle is built rather
than hoped for: the fine themes become units and are merged recursively by centroid proximity, with
a unit required to be close to most of a group rather than to one member, which is a near-clique
condition and is what stops a chain of pairwise-close units fusing into one blob.

Closeness is a percentile of the pairwise centroid cosines AT THAT LEVEL, recomputed each level
because level one compares mostly single pathways and level three compares groups of groups. That
choice is also the design flaw the run found, and the module docstring and the report both say so."

git add data/ontology/v0.3/kc/real_t1.5_q99_s80.json data/ontology/v0.3/kc/3001_t1.5_q99_s80.json data/ontology/v0.3/kc/3002_t1.5_q99_s80.json data/ontology/v0.3/kc/3003_t1.5_q99_s80.json docs/status/2026-10-07-kc.md docs/status/commit-2026-10-07-kc.sh

git commit -m "KC: EARLY STOP. The merge step cannot reject a null" -m "THE EARLY STOP TRIGGERED AND THE RUN WAS STOPPED THERE. Scrambles 3001 to 3003 give 6,380
themes on average against the real build 2,547, a ratio of 250 percent: the scrambled data produces
two and a half times MORE themes than the real data, against a 5 percent rule. The DAG export, the
sensitivity grid, the quality proxy and the 30 example themes were not computed.

THE FINE LEVEL IS SOUND. One filtration, no sampling, no support. It admits 622 of 1,615 real
candidates and 4 of 80 scrambled ones, and the solved lifetime threshold is 1.5 at a scramble ratio
of 0.70 percent, coinciding with one of the declared fixed values. The whole fine level is 0.9
seconds.

AND ON SHAPE THE REAL BUILD LOOKED LIKE THE BEST THING BUILT HERE: 2,547 themes in 2.8 seconds, with
278 at 51 to 200 and 91 at 201 to 500, so 369 mid-size against HiDeF 249, while also holding 2,104
fine themes against HiDeF 205. That is the profile the engine search has been looking for, which is
why the null check matters so much.

THE MIDDLE IS AN ARTEFACT OF THE MERGE STEP. At 51 to 200 the scramble gives 254 themes against the
real 278, which is 91 percent. Only the 500-plus band is nearly clean, at 4.95 percent, and only
because a scramble has almost nothing that large.

THE MECHANISM IS A DESIGN FLAW RATHER THAN A TUNING PROBLEM. Two things combine. The fine level
filters the noise and then hands almost nothing on, so on a scramble 10,762 of 10,770 units are
single pathways and the level step runs on raw pathways rather than on themes. And closeness is
defined as a PERCENTILE, so it admits one percent of pairs whatever the data is: the 99th percentile
of pairwise centroid cosine is 0.307 on the real matrix and 0.086 on a scramble. A cosine of 0.086
between two random centroids is not closeness in any meaningful sense, but it is the 99th percentile
of that matrix, and one percent of 58 million pairs is 580,000 edges, which is ample for greedy
near-cliques to find thousands of groups.

A relative threshold is scale-free by construction and scale-free is exactly what cannot reject a
null. The join-share condition does not save it either: requiring closeness to 80 percent of a group
is a shape condition on the close graph, and a random graph with 580,000 edges has plenty of dense
subgraphs. None of the three declared sensitivities is an absolute threshold, so none of them
addresses this, which is why the early stop is the right outcome rather than a sweep. What would have
to change is an absolute or null-calibrated closeness floor, applied to the merge step and not only
to the fine level, and that is a different design."

git push
