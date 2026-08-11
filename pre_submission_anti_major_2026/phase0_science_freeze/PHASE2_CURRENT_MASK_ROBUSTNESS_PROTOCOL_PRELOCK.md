# Phase 2 current-mask robustness — protocol skeleton

Role: `POST_PRIMARY_PRESPECIFIED_ROBUSTNESS`, cohorts Internal 113 and RHUH 39. No Phase 0 execution. Use the same frozen five development checkpoints; no retraining, fine-tuning, calibration, TTA, or outcome-based tuning.

Stage A2-mask: current T1c plus perturbed current mask → frozen predictor → perturbed-mask P0 → hash freeze, without future target/performance access. Stage B2-mask then uses the original clean future-added target to evaluate Fixed/P0, Full PCC, and No-smoothing.

Perturbation categories: CLEAN, EROSION_MILD, EROSION_MODERATE, DILATION_MILD, DILATION_MODERATE, BOUNDARY_PERTURBATION. Physical millimetres are preferred; 1 mm and 2 mm are candidates, not yet final. Phase 1 may select the physical implementation only from spacing/geometry/preprocessing, before performance. Boundary algorithm and seed must be deterministic and prelocked.

Metrics are descriptive: Dice@0.5, IoU@0.5, soft Dice, Brier, AP, mean/median, paired change vs CLEAN, 10,000 paired bootstrap CI, wins/ties/losses. No new confirmatory p-value family is authorized.
