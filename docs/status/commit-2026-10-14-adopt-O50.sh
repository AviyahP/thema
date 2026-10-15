#!/bin/zsh
set -euo pipefail
cd ~/code/thema

TAG=thema-O50-2026-10-14

git log --format=%s overlap-2026-10 | grep -cFx "Overlap arm: C1 and C3 pass, C2 fails on one pathway, giants 10 to 4, nothing adopted" > /dev/null

git switch overlap-2026-10

git add \
  data/ontology/frozen/working-O50-2026-10-14/all_verdicts_O50.json \
  data/ontology/frozen/working-O50-2026-10-14/CHECKSUMS.sha256 \
  data/ontology/frozen/working-O50-2026-10-14/edges.tsv \
  data/ontology/frozen/working-O50-2026-10-14/excluded_inputs.tsv \
  data/ontology/frozen/working-O50-2026-10-14/floors_L_cal8.json \
  data/ontology/frozen/working-O50-2026-10-14/FROZEN.md \
  data/ontology/frozen/working-O50-2026-10-14/manifest.json \
  data/ontology/frozen/working-O50-2026-10-14/match_to_c85.tsv \
  data/ontology/frozen/working-O50-2026-10-14/members.tsv \
  data/ontology/frozen/working-O50-2026-10-14/nodes.tsv \
  data/ontology/frozen/working-O50-2026-10-14/O50_new_themes.json \
  data/ontology/frozen/working-O50-2026-10-14/repair_map.json \
  data/ontology/frozen/working-O50-2026-10-14/REPORT_o50_eval.md \
  data/ontology/frozen/working-O50-2026-10-14/report.txt \
  data/ontology/frozen/working-O50-2026-10-14/trees_build_log.json \
  data/ontology/frozen/working-O50-2026-10-14/universe.json \
  data/ontology/frozen/working-O50-2026-10-14/unplaced.tsv \
  tests/ontology/test_frozen_baseline.py
git diff --cached --quiet || git commit -m "Freeze O50 as the working version, guarded by the same checksum test as the other two"

git add \
  data/experiments/o50_eval_2026-10-13/c4/C4_01.json \
  data/experiments/o50_eval_2026-10-13/c4/C4_02.json \
  data/experiments/o50_eval_2026-10-13/c4/C4_03.json \
  data/experiments/o50_eval_2026-10-13/c4/C4_04.json \
  data/experiments/o50_eval_2026-10-13/c4/C4_05.json \
  data/experiments/o50_eval_2026-10-13/c4/C4_06.json \
  data/experiments/o50_eval_2026-10-13/c4/C4_07.json \
  data/experiments/o50_eval_2026-10-13/c4/C4_08.json \
  data/experiments/o50_eval_2026-10-13/c4/C4_09.json \
  data/experiments/o50_eval_2026-10-13/c4/C4_10.json \
  data/experiments/o50_eval_2026-10-13/c4/C4_11.json \
  data/experiments/o50_eval_2026-10-13/c4/C4_12.json \
  data/experiments/o50_eval_2026-10-13/c4/C4_13.json \
  data/experiments/o50_eval_2026-10-13/c4/C4_14.json \
  data/experiments/o50_eval_2026-10-13/c4/C4_15.json \
  data/experiments/o50_eval_2026-10-13/c4/C4_16.json \
  data/experiments/o50_eval_2026-10-13/c4/C4_17.json \
  data/experiments/o50_eval_2026-10-13/c4/C4_18.json \
  data/experiments/o50_eval_2026-10-13/c4/C4_19.json \
  data/experiments/o50_eval_2026-10-13/c4/C4_20.json \
  data/experiments/o50_eval_2026-10-13/c4/C4_21.json \
  data/experiments/o50_eval_2026-10-13/c4/C4_22.json \
  data/experiments/o50_eval_2026-10-13/c5/C5_01.json \
  data/experiments/o50_eval_2026-10-13/c5/C5_02.json \
  data/experiments/o50_eval_2026-10-13/c5/C5_03.json \
  data/experiments/o50_eval_2026-10-13/c5/C5_04.json \
  data/experiments/o50_eval_2026-10-13/c5/C5_05.json \
  data/experiments/o50_eval_2026-10-13/c5/C5_06.json \
  data/experiments/o50_eval_2026-10-13/c5/C5_07.json \
  data/experiments/o50_eval_2026-10-13/c5/C5_08.json \
  data/experiments/o50_eval_2026-10-13/c5/C5_09.json \
  data/experiments/o50_eval_2026-10-13/c5/C5_10.json \
  data/experiments/o50_eval_2026-10-13/c5/C5_11.json \
  data/experiments/o50_eval_2026-10-13/c5/C5_12.json \
  data/experiments/o50_eval_2026-10-13/c5/C5_13.json \
  data/experiments/o50_eval_2026-10-13/c5/C5_14.json \
  data/experiments/o50_eval_2026-10-13/c5/C5_15.json \
  data/experiments/o50_eval_2026-10-13/c5/C5_16.json \
  data/experiments/o50_eval_2026-10-13/c5/C5_17.json \
  data/experiments/o50_eval_2026-10-13/c5/C5_18.json \
  data/experiments/o50_eval_2026-10-13/c5/C5_19.json \
  data/experiments/o50_eval_2026-10-13/c5/C5_20.json \
  data/experiments/o50_eval_2026-10-13/code/m205.py \
  data/experiments/o50_eval_2026-10-13/code/o50_c4build.py \
  data/experiments/o50_eval_2026-10-13/code/o50_c5build.py \
  data/experiments/o50_eval_2026-10-13/code/o50_prep.py \
  data/experiments/o50_eval_2026-10-13/code/o50_score.py \
  data/experiments/o50_eval_2026-10-13/judged/C4_01.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C4_02.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C4_03.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C4_04.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C4_05.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C4_06.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C4_07.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C4_08.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C4_09.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C4_10.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C4_11.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C4_12.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C4_13.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C4_14.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C4_15.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C4_16.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C4_17.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C4_18.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C4_19.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C4_20.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C4_21.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C4_22.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C5_01.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C5_02.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C5_03.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C5_04.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C5_05.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C5_06.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C5_07.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C5_08.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C5_09.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C5_10.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C5_11.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C5_12.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C5_13.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C5_14.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C5_15.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C5_16.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C5_17.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C5_18.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C5_19.out.json \
  data/experiments/o50_eval_2026-10-13/judged/C5_20.out.json \
  data/experiments/o50_eval_2026-10-13/PREREG_note.md \
  data/experiments/o50_eval_2026-10-13/REPORT.md \
  data/experiments/o50_eval_2026-10-13/rubric_c4.md \
  data/experiments/o50_eval_2026-10-13/rubric_c5.md \
  data/experiments/o50_eval_2026-10-13/score_output.txt
git diff --cached --quiet || git commit -m "O50 evaluation: C4 passes at 112 not-ok and C5 is won 87 to 33"

git add \
  data/experiments/hidef_eval_2026-10-13/code/hd_build.py \
  data/experiments/hidef_eval_2026-10-13/code/hd_score.py \
  data/experiments/hidef_eval_2026-10-13/code/hd_struct.py \
  data/experiments/hidef_eval_2026-10-13/inputs/Q_01.json \
  data/experiments/hidef_eval_2026-10-13/inputs/Q_02.json \
  data/experiments/hidef_eval_2026-10-13/inputs/Q_03.json \
  data/experiments/hidef_eval_2026-10-13/inputs/Q_04.json \
  data/experiments/hidef_eval_2026-10-13/inputs/Q_05.json \
  data/experiments/hidef_eval_2026-10-13/judged/Q_01.out.json \
  data/experiments/hidef_eval_2026-10-13/judged/Q_02.out.json \
  data/experiments/hidef_eval_2026-10-13/judged/Q_03.out.json \
  data/experiments/hidef_eval_2026-10-13/judged/Q_04.out.json \
  data/experiments/hidef_eval_2026-10-13/judged/Q_05.out.json \
  data/experiments/hidef_eval_2026-10-13/PREREG.md \
  data/experiments/hidef_eval_2026-10-13/REPORT.md \
  data/experiments/hidef_eval_2026-10-13/rubric_hd.md \
  data/experiments/hidef_eval_2026-10-13/score_output.txt \
  data/experiments/hidef_eval_2026-10-13/structural_output.txt \
  data/experiments/reviewer_eval_x2_2026-10-09/o50_facets_output.txt \
  data/experiments/reviewer_eval_x2_2026-10-09/o50_facets.py
git diff --cached --quiet || git commit -m "The HiDeF evaluation and the O50 facet counts"

git add CLAUDE.md DECISIONS.md docs/status/commit-2026-10-14-adopt-O50.sh
git diff --cached --quiet || git commit -m "O50 is the working version; c85 and the 2026-10-09 baseline stay frozen as fallbacks"

git switch leaves-2026-10
git merge --no-ff overlap-2026-10 -m "Merge overlap-2026-10: O50 adopted as the working version"

git tag -a $TAG -m "THEMA working version O50, frozen 2026-10-14: thema_L_x2_O50 on 5,539 atomic pathways. 4,602 themes, 97.57 percent coherent or umbrella, 112 not ok against c85 195, giants 10 down to 4. Differs from c85 in one same-theme cutoff of 0.50 used by consensus AND the stale-merge pass, iterated with chain collapse at 0.85 to a joint fixed point; theta_match unchanged at 0.70. Adopted on criteria declared before the build: C1 pass, C3 pass, C4 pass, C5 won 87 to 33 at p 9e-7. C2 failed on one pathway, btm:M205, accepted as a known exception. The cleanup costs some real facets: c85 won 28 percent of the C5 items and distinct homes fall from 79 to 66 percent. c85 and the 2026-10-09 baseline remain frozen as fallbacks."

git push origin leaves-2026-10
git push origin overlap-2026-10
git push origin $TAG

echo "tag:    $TAG"
echo "commit: $(git rev-list -n 1 $TAG)"
echo "branch: $(git rev-parse --abbrev-ref HEAD)"
