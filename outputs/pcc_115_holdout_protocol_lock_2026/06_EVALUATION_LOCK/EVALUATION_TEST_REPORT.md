# Evaluation synthetic test report

Scope: synthetic arrays only. Tests cover Dice@0.5, IoU@0.5, precision, recall, soft Dice, Brier score, average precision, target-volume top-k, empty prediction, empty target, all-zero probabilities and tied top-k scores. Target-volume top-k is labeled oracle-assisted retrospective localization. Tied scores follow the locked NumPy `argpartition` behavior; repeated calls in the frozen runtime must be identical, while tied voxel identity has no clinical ordering.

Result: PASS. Verified by saved pytest output; relevant checks protocol tests 23–28 pass.
