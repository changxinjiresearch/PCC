# Target-independent Evaluation Report

All eight methods were evaluated directly from saved probability maps for all 40 locked cases. The 640-row table contains one fixed-0.5/probability row and one cross-fitted-threshold row per case and method. No metric was inferred from top-k Dice.

At fixed threshold 0.5, mean Dice was: Fixed `0.228576`, Naive `0.228575`, EIA-linear `0.241924`, EIA-morph `0.256500`, EIA-blend-0.90 `0.233558`, EIA-blend-0.75 `0.244298`, Full PCC `0.275815`, and No-smoothing PCC `0.326306`. No-smoothing exceeded Full PCC by mean paired Dice `0.050491` after Holm correction. Full PCC exceeded Fixed by `0.047239`.

With strict fold-level cross-fitting, mean Dice was: Fixed `0.215566`, Naive `0.223329`, EIA-linear `0.397479`, EIA-morph `0.256500`, EIA-blend-0.90 `0.334103`, EIA-blend-0.75 `0.377545`, Full PCC `0.325754`, and No-smoothing PCC `0.385023`. Each held-out fold's method threshold was chosen using only cases from the other four held-out folds over the locked 0.01–0.99 grid; ties selected the smallest threshold.

Threshold-free mean soft Dice was Full PCC `0.269865` and No-smoothing `0.309452`; mean Brier scores were `0.004702` and `0.003853`, respectively. Mean average precision was Fixed `0.229372`, Full PCC `0.373095`, No-smoothing `0.523144`, EIA-linear `0.351718`, EIA-blend-0.90 `0.552789`, and EIA-blend-0.75 `0.612147`. Thus aggressive oracle-like EIA blends remain stronger on PR-AUC and must not be described as inferior to PCC.

All locked targets were non-empty, so average precision was available for all 40 cases. Probability metrics are identical across fixed and cross-fitted rows by definition; they are duplicated only to keep evaluation records self-contained.
