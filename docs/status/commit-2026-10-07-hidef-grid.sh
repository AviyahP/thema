set -e

git add .gitignore

git commit -m "Ignore the HiDeF grid builds, keep the grid summary" -m "A report-only 4 by 5 parameter sweep, 97 MB across 16 directories, regenerable from the
committed builder in about 40 minutes. The summary with every recall and precision cell is committed
as data/experiments/hidef_grid_2026-10-07.json instead, so every number in the report has a
committed source without carrying the builds."

git add scripts/hidef_grid.py data/experiments/hidef_grid_2026-10-07.json docs/status/2026-10-07-hidef-grid.md docs/status/commit-2026-10-07-hidef-grid.sh

git commit -m "HiDeF at its best: A keeps the fine level on recall, loses it on precision" -m "EXPLORATORY and REPORT ONLY. Twenty settings, k in 5, 10, 15, 30 by maxres in 25, 50, 100, 200,
300, other settings at the existing defaults. Four builds reused, sixteen built. NOTHING HIT THE
10-MINUTE LIMIT, the slowest being 354 seconds, so no setting was skipped and the grid is complete at
20 of 20, in about 40 minutes total.

Scored with exactly the KC2 deciding-table code, imported rather than reimplemented: same source
only, recall banded by the curated set size, precision by the theme size, match at best Jaccard above
0.5. The reuse is the point, since a comparison where HiDeF is measured by a second implementation
of the same measure is not a comparison.

BEST HIDEF BY MEAN RECALL OVER THE EIGHT CELLS IS k equals 5 with maxres 300, at 0.1725, against arm
A at 0.1667 and KC2 at 0.0604. So on that aggregate HiDeF tuned beats A by 0.0058. The grid is
almost perfectly monotone, recall rising with maxres and falling with k, and the winner is the corner
of the grid, so the search is pressed against its own boundary and a wider grid would likely keep
going.

DOES A LEAD AT THE FINE LEVEL SURVIVE? Against the ORACLE, which picks the best HiDeF setting per
cell and is an advantage neither A nor KC2 gets: A leads Reactome 3 to 10 recall 60.6 against 48.5,
ties Reactome 11 to 50 recall at 45.4 exactly, leads GO 3 to 10 recall 14.9 against 9.6 and GO 11 to
50 recall 4.1 against 3.6. So A leads on recall in three of four fine cells and ties the fourth.

IT TRAILS ON PRECISION IN THREE OF FOUR, by 0.2 to 4.2 points, and that is the honest counterweight.
HiDeF at small k produces fewer tighter themes, so a higher share of what it emits matches a curated
set while a much smaller share of curated biology is recovered at all: 2,915 themes against A 6,244.
A does lead Reactome 11 to 50 precision clearly, 44.5 against 34.7.

OUTSIDE THE FINE BANDS BOTH ARE WEAK AND THE PICTURE INVERTS. At Reactome 51 to 200 A leads on both,
7.7 and 22.7 against the oracle 7.7 and 13.2, while KC2 leads recall alone at 11.5. At Reactome 201
to 500 every HiDeF setting scores 33.3 recall and A scores 0.0, but that is ONE curated set of
three, a coin flip reported to one decimal place, and it should not be weighed. Across the two GO
coarse bands nothing reaches 1.2 recall.

The single aggregate HiDeF wins, the eight-cell mean, it wins by being better in the coarse bands
where the denominators are 3 and 33 curated sets, while A is ahead on recall everywhere in the fine
bands where they are 470, 174, 1,906 and 634. A mean over eight cells with denominators spanning 3
to 1,906 is not a measure to decide anything on, and the protocol own rule is cell by cell with
confidence intervals rather than a mean. This grid is report-only and changes nothing declared."

git push
