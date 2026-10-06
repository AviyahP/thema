set -e

git add scripts/hidef_grid2.py data/experiments/hidef_grid2_2026-10-07.json docs/status/2026-10-07-hidef-grid.md docs/status/commit-2026-10-07-hidef-grid2.sh

git commit -m "HiDeF grid extended: dropping a 3-set cell reverses the first grid headline" -m "EXPLORATORY and REPORT ONLY. Nine settings, k in 3, 4, 5 by maxres in 300, 500, 800, with
k5 maxres300 reused and eight built. Nothing hit the 10-minute limit, slowest 201 seconds, so nothing
was skipped. Twenty-eight HiDeF settings are now scored in total, all with the KC2 deciding-table
code imported rather than reimplemented. The builds themselves are already gitignored by the first
grid rule; the summary with every cell is committed.

THE SIX-CELL MEAN REVERSES THE FIRST GRID. Dropping Reactome 201 to 500, where there are three
curated sets, arm A leads EVERY ONE of the 28 HiDeF settings, 0.2222 against the best 0.2082. The
first grid reported HiDeF tuned beating A on the eight-cell mean at 0.1725 to 0.1667, and that result
was being produced by the three-set cell. Its instability is now visible directly: across the nine
new settings it reads 33.3, 0.0, 0.0, 33.3, 33.3, 0.0, 33.3, 0.0, 33.3, flipping with maxres at
fixed k and with k at fixed maxres. One cell of three sets switching on and off moved an aggregate
that three reports have quoted.

RECALL IS STILL RISING AT THE NEW EDGE, at every k, and the best setting is again at a boundary. k3
wins both fine recall cells and k equals 3 is the smallest k in the extension, while every k is
still climbing at maxres 800. The honest reading is that HiDeF fine-level recall is bounded by how
many themes it is allowed to emit rather than by a property of the method, and the grid has been
measuring theme count by proxy.

THE ORACLE NOW TAKES GO 3 TO 10 OFF A, 15.6 percent against 14.9, the first fine-level recall cell
any HiDeF configuration has won, and it took a 28-setting search to find it. A still leads Reactome
3 to 10 recall 60.6 against 57.9, where the first grid had that lead at 12.1 points and it is now
2.7, and ties Reactome 11 to 50 at 45.4.

AT MATCHED THEME COUNT, N equals 4,287, A RECALL LEAD DOES NOT SURVIVE. A scores 0.2003 against
HiDeF 0.2082 on the six-cell mean and loses three of four fine recall cells, holding only Reactome 3
to 10 by 0.8 points. A recall lead at full size is substantially a volume effect.

BUT PRECISION GOES THE OTHER WAY AND STRONGLY. At matched count A beats HiDeF in every one of the
six cells, several by large margins: Reactome 11 to 50 at 49.8 against 33.2, Reactome 51 to 200 at
26.7 against 6.0, GO 51 to 200 at 7.9 against 0.7. At equal theme count the two arms are not close
on the same axis. HiDeF recovers slightly more curated sets and A themes are far more often real.
Which matters more is a question about what the ontology is for, and this grid is report-only and
does not answer it.

Truncation was by support with ties broken toward the LARGER theme, so it cannot silently prefer
small themes and flatter the fine bands."

git push
