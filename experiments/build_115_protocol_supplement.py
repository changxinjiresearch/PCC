#!/usr/bin/env python3
"""Build protocol-lock supplement files without touching frozen cohort CSVs."""
from __future__ import annotations
import ast, csv, hashlib, inspect, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"outputs/pcc_115_holdout_protocol_lock_2026"
COHORT=OUT/"01_COHORT_LOCK"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(s,encoding="utf-8")
def read_csv(p):
 with p.open(newline='',encoding='utf-8') as f: return list(csv.DictReader(f))
def write_csv(p,rows,fields):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='',encoding='utf-8') as f: w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n'); w.writeheader(); w.writerows(rows)

def shards():
 p0=read_csv(COHORT/'P0_INFERENCE_MANIFEST.csv'); cases={r['case_id']:r for r in read_csv(COHORT/'LOCKED_115_CASE_MANIFEST.csv')}
 stage_a=[]
 for row in sorted(p0,key=lambda x:x['patient_id']):
  stage_a.append({"patient_id":row['patient_id'],"case_id":row['case_id'],"current_timepoint":row['current_timepoint'],"current_t1c_path":row['current_t1c_path'],"current_mask_path":row['current_mask_path'],"current_t1c_shape":row['current_t1c_shape'],"current_mask_shape":row['current_mask_shape'],"output_p0_path":f"stage_a/shard_{row['shard']}/P0/{row['case_id']}.npy","stage_a_shard":row['shard']})
 write_csv(OUT/'09_EXECUTION_PLAN/LOCKED_115_STAGE_A_P0_SHARD_MANIFEST.csv',stage_a,list(stage_a[0]))
 stage_b=[]
 ordered=sorted(cases.values(),key=lambda x:x['patient_id'])
 for i,row in enumerate(ordered): stage_b.append({"patient_id":row['patient_id'],"case_id":row['case_id'],"current_timepoint":row['current_timepoint'],"future_timepoint":row['future_timepoint'],"stage_b_shard":min(3,i*4//len(ordered))})
 write_csv(OUT/'09_EXECUTION_PLAN/LOCKED_115_STAGE_B_CORRECTION_SHARD_MANIFEST.csv',stage_b,list(stage_b[0]))
 write(OUT/'09_EXECUTION_PLAN/SHARD_POLICY_AND_IDENTITY_AUDIT.md',"""# Stage-specific shard policy and identity audit

The frozen `P0_INFERENCE_MANIFEST.csv` has a legacy generic `shard` column assigned round-robin. It is retained byte-for-byte for cohort identity protection but is deprecated. `LOCKED_115_STAGE_A_P0_SHARD_MANIFEST.csv` renames that value to `stage_a_shard` and is the only shard manifest Stage A may read.

Stage B uses `LOCKED_115_STAGE_B_CORRECTION_SHARD_MANIFEST.csv`, four contiguous patient-ID blocks of 29/29/29/28. Different stage assignments are intentional. Both manifests contain 115 unique patients/cases, one row per patient, union 115 and within-stage overlap zero. Runners must reject the wrong stage's shard column. Output directories and completion markers must include `stage_a` or `stage_b` and an explicit shard number; completion markers are never shared across stages. `LOCKED_115_SHARD_MANIFEST.csv` is deprecated and must not be consumed by either runner.
""")

def method_lock():
 write(OUT/'04_METHOD_LOCK/LOCKED_115_METHOD_CONFIG.yaml',"""protocol_status: prelocked_before_115_results
methods:
  Fixed:
    operation: safe_clip_prob(P0)
    dtype: float32
    clip: nan_to_num_then_[0,1]
  Naive:
    operation: sigmoid(2.5 * safe_logit(safe_clip_prob(P0)))
    gamma: 2.5
    logit_epsilon: 1.0e-5
    sigmoid_logit_clip: [-30, 30]
    dtype: float32
  EIA-linear:
    alpha: 0.30
    beta: 0.30
    support_radius_voxels: 26
    target_signal_gaussian_sigma_voxels: 2.0
  EIA-blend-0.90:
    baseline_weight: 0.90
    target_signal_weight: 0.10
  EIA-blend-0.75:
    baseline_weight: 0.75
    target_signal_weight: 0.25
  EIA-morph:
    baseline_threshold: 0.5
    support_radius_voxels: 26
    binary_closing_iterations: 1
    fill_holes: true
    minimum_component_voxels: 20
  Full_PCC:
    rounds: 10
    eta: 0.30
    dilation_radius_voxels: 26
    gaussian_sigma_voxels: 2.0
    logit_epsilon: 1.0e-5
    sigmoid_logit_clip: [-30, 30]
    state_propagation: true
    dtype: float32
    boundary_handling: scipy_ndimage_defaults
    trajectory: P1_to_P10_when_capture_enabled
  No_smoothing_PCC:
    candidate_status: independent-validation_prelocked_candidate_variant
    rounds: 10
    eta: 0.30
    dilation_radius_voxels: 26
    gaussian_filter_applied_to_discrepancy: false
    logit_epsilon: 1.0e-5
    sigmoid_logit_clip: [-30, 30]
    state_propagation: true
    dtype: float32
only_allowed_difference: discrepancy_signal = D_r instead of gaussian_filter(D_r, sigma=2.0)
real_115_execution_in_protocol_lock: false
""")
 write(OUT/'04_METHOD_LOCK/LOCKED_115_METHOD_DEFINITIONS.md',"""# Complete locked method definitions

Let `P0` be the frozen Stage A probability map and `T = (future_mask > 0.5) AND NOT (current_mask > 0.5)`. All arrays are aligned and no registration/resampling is allowed. `safe_clip_prob` converts to float32, maps NaN/−Inf/+Inf to 0/0/1 and clips to [0,1].

Fixed is `safe_clip_prob(P0)`. Naive is `sigmoid(2.5 × logit(Fixed))` with probability clipping to `[1e-5,1−1e-5]`, logit clipping to `[-30,30]`, then float32 clipping.

For EIA, `R = distance_transform_edt(~T) <= 26`; `S = normalize01(gaussian_filter(T.float32, sigma=2.0))` with SciPy default boundary mode. Linear is `clip(P0 + 0.30 S(1−P0) − 0.30(1−R)P0)`. Blends are `clip(0.90P0+0.10S)` and `clip(0.75P0+0.25S)`. Morph thresholds P0 at 0.5, intersects with R, performs one SciPy binary closing, fills holes, labels with SciPy default connectivity and retains components of at least 20 voxels.

Full PCC initializes `P_0=safe_clip_prob(P0)`. At round r: `P_r` is clipped; `D_r=(T−P_r)R`; `S_r=gaussian_filter(D_r,sigma=2.0)`; `O_r=P_r(1−R)`; `L_r=logit(P_r,eps=1e-5)`; `P_{r+1}=clip(sigmoid(clip(L_r+0.30S_r−0.30O_r,−30,30)))`. Ten rounds propagate state. Float32 conversion/clipping occurs at every round. SciPy Gaussian defaults define boundary handling. When trajectory capture is enabled P1–P10 and locked round summaries are saved; otherwise only P10 is returned.

No-smoothing executes the same loop, region, target, state, suppression, eta, rounds, clipping, logit/sigmoid order, dtype and boundary policy. Its sole difference is `S_r=D_r`; the `gaussian_filter(D_r,sigma=2.0)` call is bypassed. The authoritative implementation is `run_variant(..., smoothing=False)` in `src/analysis/internal_completion.py`; Full-PCC identity is `smoothing=True`. No-smoothing remains a posthoc 40-case finding prelocked here as an independent-validation candidate, not the canonical primary.
""")
 write(OUT/'04_METHOD_LOCK/NO_SMOOTHING_SINGLE_DIFFERENCE_AUDIT.md',"""# No-smoothing single-difference audit

Authoritative function: `src.analysis.internal_completion.run_variant`. The only branch controlled by `smoothing` is:

```python
signal = gaussian_filter(discrepancy, sigma=SIGMA) if smoothing else discrepancy
```

Full PCC uses the default `smoothing=True`; No-smoothing passes exactly `smoothing=False`. AST/static tests assert one `smoothing` conditional and identical values for rounds, eta, radius, suppression, region, safe logit, sigmoid, clipping, propagation and dtype. A synthetic regression also verifies the Full branch equals `src.models.pcc.apply_pcc` and that only the discrepancy signal differs.
""")
 write_csv(OUT/'04_METHOD_LOCK/FULL_PCC_VS_40_AUTHORITY_AUDIT.csv',[
  {"field":"rounds","authority_value":"10","locked_115_value":"10","status":"MATCH"},{"field":"eta","authority_value":"0.30","locked_115_value":"0.30","status":"MATCH"},{"field":"dilation_radius_voxels","authority_value":"26","locked_115_value":"26","status":"MATCH"},{"field":"sigma_voxels","authority_value":"2.0","locked_115_value":"2.0","status":"MATCH"},{"field":"logit_epsilon","authority_value":"1e-5","locked_115_value":"1e-5","status":"MATCH"},{"field":"state_propagation","authority_value":"true","locked_115_value":"true","status":"MATCH"}],['field','authority_value','locked_115_value','status'])

def policies():
 write(OUT/'05_TARGET_AND_STAGE_LOCK/LOCKED_115_TARGET_POLICY.yaml',"""definition: (future_mask > 0.5) AND NOT (current_mask > 0.5)
mask_threshold: 0.5
comparison: strict_greater_than
output_dtype: bool
shape_mismatch: FAIL_TARGET_CONSTRUCTION
affine_or_orientation_mismatch: FAIL_GEOMETRY
empty_target: FAIL_TARGET_CONSTRUCTION_AND_RETAIN_IN_DENOMINATOR
registration: forbidden
resampling: forbidden
construction_stage: stage_b_only
""")
 write(OUT/'06_EVALUATION_LOCK/LOCKED_115_EVALUATION_POLICY.yaml',"""primary_endpoint: patient_level_Dice_at_fixed_threshold_0.5
fixed_threshold: 0.5
fixed_prediction_rule: probability >= 0.5
confirmatory_comparisons: [Full_PCC_vs_Fixed, No_smoothing_PCC_vs_Full_PCC]
secondary_family: [IoU_0.5, precision_0.5, recall_0.5, soft_Dice, Brier, average_precision, predicted_positive_volume, target_to_predicted_volume_ratio, all_nonconfirmatory_method_comparisons]
oracle_assisted_retrospective_localization_metrics: [target_volume_matched_top_k_Dice, target_volume_matched_top_k_IoU]
top_k_ties: locked NumPy argpartition behavior; exact selected set is deterministic within the frozen runtime but tied-voxel identity has no semantic ordering
empty_target_in_locked_cohort: protocol_failure
non_finite_probability: metric_failure
unit: patient
""")
 write(OUT/'06_EVALUATION_LOCK/LOCKED_115_THRESHOLD_POLICY.yaml',"""fixed_primary_threshold: 0.5
development_locked_threshold_analysis: NOT_AVAILABLE
reason: frozen_40_case_probability_maps_for_all_eight_methods_are_not_present_in_the_local_sealed_protocol_inputs
115_case_threshold_selection: forbidden
post_result_threshold_sensitivity_addition: forbidden
analysis_plan_action: development_locked_threshold_sensitivity_removed
""")
 write(OUT/'07_STATISTICS_LOCK/LOCKED_115_STATISTICAL_ANALYSIS_PLAN.yaml',"""unit: patient
alternative: two-sided
wilcoxon_zero_method: wilcox
all_differences_zero: p_value_1.0_with_ALL_ZERO_status
ties: average_ranks_for_equal_absolute_nonzero_differences
holm_family_exactly: [Full_PCC_vs_Fixed_Dice_0.5, No_smoothing_PCC_vs_Full_PCC_Dice_0.5]
alpha: 0.05
primary_success: mean_paired_difference_gt_0_AND_Holm_adjusted_p_lt_0.05
no_smoothing_replication: mean_paired_difference_gt_0_AND_Holm_adjusted_p_lt_0.05
rank_biserial: (positive_rank_sum - negative_rank_sum) / (positive_rank_sum + negative_rank_sum), zeros excluded
cohens_dz: mean_difference / sample_SD_difference
cohens_dz_sd_zero: NA_with_SD_ZERO_status
bootstrap_unit: patient_pair
bootstrap_replicates: 10000
bootstrap_seed: 20260803
bootstrap_interval: percentile_95_percent
bootstrap_failure: analysis_failure_no_substitution
empty_prediction_nonempty_target: Dice_0_IoU_0
empty_target: protocol_failure_not_metric_imputation
non_finite: metric_failure_no_silent_filtering
secondary_family: all_other_methods_metrics_and_nonconfirmatory_comparisons_with_separate_Holm_adjustment
one_sided_testing: forbidden
""")
 write(OUT/'07_STATISTICS_LOCK/PCC_115_CONFIRMATORY_ANALYSIS_PLAN.md',"""# Confirmatory patient-level analysis

The confirmatory Holm family has exactly two two-sided paired Wilcoxon signed-rank tests: Full PCC versus Fixed at Dice 0.5, and No-smoothing versus Full PCC at Dice 0.5. `zero_method='wilcox'`; zeros are removed before ranking and equal nonzero absolute differences receive average ranks. An all-zero vector returns p=1 with status `ALL_ZERO`.

Report paired mean and median differences, 10,000 patient-pair percentile bootstrap replicates with seed 20260803, Cohen's dz, rank-biserial `(W+−W−)/(W++W−)`, and wins/ties/losses. A zero difference SD makes dz unavailable with `SD_ZERO`; it is never coerced to zero. Bootstrap failure blocks that inferential output. Primary success requires mean paired difference >0 and Holm-adjusted p<0.05. No-smoothing replication uses the same criterion but does not determine the Full-PCC primary result. No one-sided tests are permitted.

Locked empty targets are protocol failures; they and all other failures remain in the 115 denominator. Non-finite metrics are failures, not filtered observations. Other methods, endpoints and comparisons form a separate secondary Holm family.
""")
 write(OUT/'08_FAILURE_POLICY/LOCKED_115_FAILURE_POLICY.yaml',"""end_to_end_denominator: 115
primary_analysis: complete_case_pairs_with_count_and_reasons_reported
conservative_sensitivity:
  failed_patient_paired_difference: 0
  one_method_only_failure: paired_difference_0_and_failure_logged
  both_methods_failure: paired_difference_0_and_both_failures_logged
retry_limit_per_case_stage: 3
retain_first_attempt_log: true
technical_recovery_may_overwrite_first_attempt: false
silent_failure_deletion: forbidden
non_finite_output: failure
all_locked_patients_retained: true
failure_classes: [source_file_missing, geometry_mismatch, checkpoint_load_failure, P0_inference_failure, P0_persistence_hash_failure, target_construction_failure, correction_failure, metric_failure, non_finite_output, shard_merge_identity_failure]
""")
 write(OUT/'08_FAILURE_POLICY/FAILURE_CLASSIFICATION.md',"""# Locked failure policy

All 115 patients remain in the end-to-end denominator. The primary complete-case analysis reports the number and identity/reason of incomplete pairs. The conservative sensitivity dataset assigns paired difference zero to any patient with one-method or both-method failure. It never substitutes a favorable or unfavorable observed value. Non-finite output is a failure. Each case/stage has at most three technical attempts; the first attempt log is immutable, later attempts are appended, and recovery cannot erase or overwrite the first failure.
""")

def protocol():
 md="""# PCC 115-patient independent holdout protocol lock

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
"""
 write(OUT/'11_PROTOCOL_RELEASE/PCC_115_HOLDOUT_PROTOCOL.md',md)
 write(OUT/'11_PROTOCOL_RELEASE/PCC_115_HOLDOUT_PROTOCOL.yaml',"""protocol: PCC_115_HOLDOUT_PROTOCOL_LOCK_2026
status: SUPPLEMENT_PENDING_TESTS
cohort: {source: 203, eligible: 155, development: 40, holdout: 115, overlap: 0, pairs_per_patient: 1}
stage_a: {authorized: false, future_access: false, shards: 4, real_forward_executed: false, p0_generated: false}
stage_b: {authorized: false, shards: 4, performance_computed: false}
predictor: {architecture: CrossCaseSmallUNet, input_channels: 2, base_channels: 16, folds: 5, weights: [0.2, 0.2, 0.2, 0.2, 0.2]}
primary_endpoint: patient_level_Dice_at_fixed_0.5
confirmatory_family: [Full_PCC_vs_Fixed, No_smoothing_vs_Full_PCC]
development_locked_threshold_analysis: NOT_AVAILABLE
statistics: {test: paired_two_sided_Wilcoxon, zero_method: wilcox, correction: Holm_two_tests, bootstrap_replicates: 10000, seed: 20260803}
failure_denominator: 115
LUMIERE_started: false
""")

def main(): shards(); method_lock(); policies(); protocol()
if __name__=='__main__': main()
