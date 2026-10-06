set -e

git add src/thema/ontology/kc2.py scripts/kc2_sweep.py scripts/kc2_report.py

git commit -m "KC2: an absolute closeness bar, which repairs KC null rejection" -m "EXPLORATORY. New files only; KC code is imported rather than copied so the two cannot drift.

KC failed its null check for one structural reason: close was the q-th percentile of pairwise
centroid cosines at each level, so it admitted one percent of pairs whatever the data was. The 99th
percentile is 0.307 on the real matrix and 0.086 on a scramble, and one percent of 58 million pairs
is ample for greedy near-cliques to find thousands of groups. A relative threshold is scale-free by
construction and scale-free cannot reject a null.

KC2 changes exactly one thing: close is cosine at or above a single absolute c, identical at every
level. The fine level, the units, the 80 percent join share and the overlap step are unchanged.

The report script bands the two measures differently and on purpose, following the evaluation
protocol clarification 2: recall by the CURATED set size, precision by the THEME size. Banding both
by theme size would make recall unanswerable for any band an arm declines to populate, which is
exactly the case for naive K in the middle."

git add data/ontology/v0.3x_engines/KC2/nodes.tsv data/ontology/v0.3x_engines/KC2/members.tsv data/ontology/v0.3x_engines/KC2/edges.tsv data/ontology/v0.3x_engines/KC2/unplaced.tsv data/ontology/v0.3x_engines/KC2/manifest.json docs/status/2026-10-07-kc2.md docs/status/commit-2026-10-07-kc2.sh

git commit -m "KC2: the null fix works, and KC2 then loses on recall to arm A" -m "THE ABSOLUTE BAR REPAIRS THE DEFECT COMPLETELY. Swept c from 0.100 to 0.400 on scrambles 3001 to
3003 through the identical pipeline. Chosen c is 0.150, the lowest meeting the one percent target, at
a ratio of 0.40 percent against KC 250 percent. At every c of 0.15 or above the scramble mean sits at
4.3 themes and stays there, and 4.3 is exactly the fine level own 4, 5 and 4, so THE MERGE STEP
CONTRIBUTES ZERO SCRAMBLE THEMES at any usable bar. The collapse happens between 0.100 at 261 percent
and 0.125 at 5.6 percent, so the bar matters and 0.15 is not near the edge.

THE BUILD. 622 fine themes, 8,562 units, levels of 499, 35, 8, 3, 2 and 1, giving 1,170 themes in 58
seconds. Bands 523, 246, 299, 53 and 49. Only FIVE of 10,770 pathways are unplaced, against arm A
141. But 85 percent of themes have more than one parent, which is not a hierarchy a reader can hold.

THE DECIDING TABLE SAYS NO. On recall, arm A beats KC2 in seven of eight same-source cells and not
narrowly: Reactome 3 to 10 is 60.6 against 20.2, Reactome 11 to 50 is 45.4 against 12.1, GO 3 to 10
is 14.9 against 3.8. The single cell KC2 wins is Reactome 51 to 200 at 11.5 against 7.7 for both A
and HiDeF, which is the band the exercise was about but is one cell of eight over 26 curated sets.

On precision KC2 is worse than A wherever both populate a band, except GO 3 to 10. Its middle
precision is the weak point: 6.2 percent at Reactome 51 to 200 against A 22.7, and zero at Reactome
201 to 500 and across the GO middle. So its 299 mid-size themes are plentiful and mostly do not
correspond to curated biology.

THE MECHANISM IS THE 85 PERCENT MULTI-PARENT FIGURE. The overlap step adds a unit to every group it
is close to 80 percent of, and repeating that over six levels lets units accumulate into many groups
and groups absorb each other neighbourhoods. That is how it places almost everything and loses its
boundaries: themes of 95 and 498 members span several curated sets and match none at Jaccard above
0.5. The examples show both sides, a clean 59-member cell cycle theme beside a 498-member grab-bag.

naive K still owns fine-level precision at 58.4 and 65.7 percent and still has no middle. HiDeF owns
Reactome 201 to 500 at 33.3 percent recall, on three curated sets.

KC2 repaired exactly the defect it set out to repair, then lost on a measure KC never got far enough
to be tested on. The absolute bar was the right fix and was not the only problem."

git push
