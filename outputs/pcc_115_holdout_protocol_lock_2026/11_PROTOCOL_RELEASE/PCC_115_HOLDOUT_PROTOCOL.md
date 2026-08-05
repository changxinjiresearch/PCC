# PCC 115-patient independent holdout protocol lock

## Scope and stage isolation

This package locks identity, code, configuration and analysis before any 115-patient model output. Protocol locking and CPU checkpoint/provenance audit execute no real-case forward, create no P0, compute no method performance and do not start LUMIERE. Stage A requires later authorization and is future-blind. Stage B requires all Stage A P0 files to be atomically saved, hashed and frozen before future masks may be read.

## Cohort

The authority chain contains 203 source patients, 155 patients eligible under the earliest-two-usable-timepoints rule, the frozen first 40 and exactly 115 disjoint holdout patients. Each patient contributes one pair; patient ID, case ID, current/future timepoint, rank and qualification are immutable. The five frozen cohort files are protected by pre/post SHA-256 audit. Future-image paths and source hashes live only in the audit sidecar and never enter the Stage A manifest.

## Predictor and Stage A

The predictor is `CrossCaseSmallUNet`, two input channels ordered current-normalized-T1c then current mask, base width 16, float32 probabilities. Current T1c normalization uses positive voxels p1/p99; mask threshold is >0.5. Five frozen folds are CPU-loaded strictly and averaged with weights 0.2 each. The Stage A runner accepts only the explicit Stage A manifest, checkpoint manifest, output root and stage-A shard. It atomically saves P0, hashes it, records files read and emits stage/shard-specific completion markers. Future/target/later fields are rejected.

## Methods and target

Eight methods are locked: Fixed, Naive, EIA-linear, EIA blends 0.90 and 0.75, EIA-morph, Full PCC and No-smoothing PCC. Exact equations and parameters are in the method lock. Full PCC remains canonical; No-smoothing is an independent-validation prelocked candidate whose sole difference is bypassing Gaussian filtering of the round discrepancy. Stage B target is `(future_mask>0.5) AND NOT (current_mask>0.5)` with bool output, exact shape/geometry, no registration/resampling and nonempty target requirement.

## Evaluation and thresholds

The primary endpoint is patient-level Dice at fixed threshold 0.5. Full PCC versus Fixed is primary; No-smoothing versus Full PCC is the second confirmatory comparison. IoU, precision, recall, soft Dice, Brier, AP and volume metrics are secondary. Target-volume top-k Dice/IoU are explicitly oracle-assisted retrospective localization metrics. Development-locked threshold sensitivity is `NOT_AVAILABLE` because the complete eight-method 40-case probability maps are not in the sealed local inputs; it is removed and cannot be added after viewing 115 results.

## Statistics and failures

The Holm family contains exactly two two-sided paired Wilcoxon tests with `zero_method=wilcox`. Success requires mean paired difference >0 and Holm p<0.05. Patient-level percentile bootstrap uses 10,000 replicates and seed 20260803. Rank-biserial, dz and edge handling are locked in the statistical YAML. All 115 remain in the process denominator; complete-case counts are reported and conservative sensitivity assigns zero paired difference to failed patients. Three attempts maximum, with immutable first logs.

## Shards and release gate

Stage A uses the round-robin assignments frozen in the legacy P0 manifest but exposed only as `stage_a_shard`. Stage B uses four contiguous CPU blocks (29/29/29/28). The two sets may differ and never share manifests, directories or completion markers. PASS requires immutable cohort hashes, five strict checkpoint loads, method identity, synthetic target/evaluation/statistical/failure tests, at least 30 protocol tests, complete hash lock, zero P0, zero 115 performance outputs, no real forward, no LUMIERE and zero blockers. Stage A remains unauthorized after PASS.
