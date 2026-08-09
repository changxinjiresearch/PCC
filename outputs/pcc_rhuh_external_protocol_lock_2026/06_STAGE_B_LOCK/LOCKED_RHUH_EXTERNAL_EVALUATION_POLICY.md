
# Locked RHUH external evaluation policy

Primary endpoint is patient-level Dice at fixed threshold 0.5, with `probability >= 0.5`. Secondary metrics are IoU, precision, recall, soft Dice, Brier score, AP/PR-AUC, and predicted positive volume. Target-volume-matched top-k Dice/IoU are labeled `ORACLE_ASSISTED_RETROSPECTIVE_LOCALIZATION` and are not deployment performance. RHUH threshold tuning and unplanned secondary inference are forbidden.
