# Stage-specific shard policy and identity audit

The frozen `P0_INFERENCE_MANIFEST.csv` has a legacy generic `shard` column assigned round-robin. It is retained byte-for-byte for cohort identity protection but is deprecated. `LOCKED_115_STAGE_A_P0_SHARD_MANIFEST.csv` renames that value to `stage_a_shard` and is the only shard manifest Stage A may read.

Stage B uses `LOCKED_115_STAGE_B_CORRECTION_SHARD_MANIFEST.csv`, four contiguous patient-ID blocks of 29/29/29/28. Different stage assignments are intentional. Both manifests contain 115 unique patients/cases, one row per patient, union 115 and within-stage overlap zero. Runners must reject the wrong stage's shard column. Output directories and completion markers must include `stage_a` or `stage_b` and an explicit shard number; completion markers are never shared across stages. `LOCKED_115_SHARD_MANIFEST.csv` is deprecated and must not be consumed by either runner.
