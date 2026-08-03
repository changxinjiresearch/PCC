# PCC Internal Completion Protocol 2026

## Status and scope

This document prospectively locks `PCC_INTERNAL_COMPLETION_2026`. These are new prespecified 2026 internal analyses, not reconstructions of ambiguously documented historical experiments. No LUMIERE or other external dataset is in scope.

The immutable input authority is Kaggle `jeechangxin/pcc-leakage-free-rerun-2026`, version 8: 40 held-out P0 maps, clean future-change targets, case/fold manifests, canonical metrics, main results and P0–P10 trajectories. Predictor retraining and P0 regeneration are prohibited.

## Canonical correction

For round `r`, `D_r = (T - P_r) * R`, `S_r = GaussianSmooth(D_r, sigma)`, and `O_r = P_r * (1-R)`. The update is `logit(P_(r+1)) = logit(P_r) + eta*S_r - eta*O_r`, followed by sigmoid, clipping and state propagation. Canonical values are 10 rounds, eta 0.30, correction-region radius 26 voxels and Gaussian sigma 2.0 voxels. Evaluation preserves the frozen target-volume-matched top-k implementation.

## Mechanism family

`FULL_PCC` is frozen canonical output and `ONE_ROUND` is frozen P1. New variants remove only the declared term: `NO_ERROR_GUIDED_TERM`, `NO_OUTSIDE_SUPPRESSION`, `NO_SMOOTHING`, and `GLOBAL_DISCREPANCY`. The 2×2 term factorial switches error guidance and outside suppression independently; both off must equal P0 exactly. These names do not claim historical ablation reproduction.

## Shuffled target

A patient-disjoint deterministic derangement uses seed 20260803. Matching minimizes, in order, quartile mismatch, adjacent-quartile distance, absolute log-volume difference and a seeded-hash tie-break. Self-matching is forbidden. Correction uses donor guidance; evaluation uses recipient clean target. Mapping is persisted and hashed before metric interpretation.

## Imperfect guidance

Components use 26-connectivity. Partial targets retain, per component, voxels with greatest Euclidean distance to the component boundary; ties use lexicographic Z-Y-X order. FP-25 samples without replacement from the physical 5–15 mm external annulus using five locked seeds. Shift-3 uses six cardinal directions with clipping and no wrap. Mixed applies Partial-50, then FP-25, then Shift-3, producing 30 repeats per case. Inference uses within-case means, never repeat-level pseudo-replication.

## Target construction

Original target is future mask minus current mask. Boundary-tolerant target excludes a physical 2 mm dilation of current mask. Eroded-current target excludes a physical 2 mm erosion. Large-change-only retains 26-connected original-target components at least 100 mm³. Physical distance uses NIfTI voxel spacing. Each definition is evaluated both against itself and, secondarily, against original clean target. Empty targets remain recorded.

## Difference-map gate

The retrospective future-image difference control runs only when current/future shapes, affine, orientation and spacing agree within the locked tolerance and no undocumented registration is required. Otherwise it is `DATA_REGISTRATION_BLOCKED`. If executable, independently current-only-normalized images form an absolute difference map, Gaussian-smoothed at sigma 2.0 and evaluated with clean-target-volume top-k. It is not a deployment baseline.

## Statistical families

The case is the unit. Bootstrap uses 10,000 resamples and seed 20260803. Paired Wilcoxon tests are two-sided; effect size is paired Cohen's dz. Holm families are: mechanism versus Full, counterfactual versus Full, imperfect guidance versus Clean, and target construction versus Original. Repeated perturbations are aggregated within case first.

## Interpretation boundaries

All negative results and failed cases remain. Parameters, seeds, matching and morphology rules cannot change after protocol lock. New results never mix with old Word values. Layer 3 remains spatial/perturbational evidence. External validation is deferred.
