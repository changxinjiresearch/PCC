# Top-k Interpretation Boundary

The frozen main Dice and IoU use a target-volume-matched top-k mask. The number of predicted positive voxels is set equal to the observed true target volume. This is an oracle-assisted retrospective localization metric and is not an ordinary deployable segmentation threshold.

It remains valid for the frozen retrospective comparison but must always be labelled as target-volume-assisted. Deployment-oriented or target-volume-independent reporting must instead use the fixed 0.5 results, strictly cross-fitted thresholds, soft Dice, Brier score, and PR-AUC reported here.
