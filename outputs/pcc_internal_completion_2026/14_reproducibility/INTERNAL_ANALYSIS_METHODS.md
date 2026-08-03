# PCC internal completion methods

`PCC_INTERNAL_COMPLETION_2026` is a new, prespecified analysis package. It is not a reconstruction of the incompletely documented historical downstream experiments.

All Layer 2 analyses start from the 40 held-out P0 maps frozen by `PCC_LEAKAGE_FREE_RERUN_2026`, Kaggle version 8. The predictor, fold checkpoints, case manifest, fold manifest, preprocessing, and P0 maps are not regenerated. For retrospective correction, the canonical probability-map state is updated for ten rounds using the locked error-guided smoothed discrepancy and outside-region suppression terms. No predictor parameters are updated.

The mechanism family changes one named update term at a time and includes a 2×2 factorial identity control. The shuffled-target family uses a deterministic patient-disjoint target derangement fixed before analysis. Imperfect-guidance stochastic or directional repeats are aggregated within each case before inference. Target-construction analyses report both evaluation against the corresponding target definition and secondary evaluation against the original clean target.

The future-image difference map is a retrospective control. It passed a 40-case shape/affine/orientation/spacing gate before execution. It is not a deployable current-only baseline.

The inference unit is the case (`n=40`). Reports include mean, SD, median, IQR, deterministic bootstrap 95% CI (10,000 resamples; seed 20260803), paired two-sided Wilcoxon tests, Holm adjustment within four prespecified comparison families, paired Cohen's dz, and wins/ties/losses.
