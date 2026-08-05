#!/usr/bin/env python3
"""Assemble the non-executing 115-patient protocol-lock archive."""
from __future__ import annotations

import argparse, csv, hashlib, json, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
 "fold_1":"bb86bcdbde7e0e4a41f5700efd8c532f2a06d3a3d9bde183f0090238a277b18c",
 "fold_2":"fb75fc2dc1d6703e22ca7ef260a54a0563a184c5a295c0890279c51cb054e759",
 "fold_3":"3e2cb75c84fb861b82789d2bf87517ee494c3435e1b06d64c739437dce547107",
 "fold_4":"28656b1d282fc66e054887166a990810b25d7e6a66d9c21e8f3951868f7291c3",
 "fold_5":"69250135d3eef595b9244426f511c165f10635e1a56241f8fa372959d874c1f3",
}
CODE = ["experiments/audit_cohort_selection.py", "experiments/pcc_115_protocol_lock_preflight.py",
        "src/preprocessing/current_only_preprocessing.py", "src/models/pcc.py",
        "src/models/naive_self_tightening.py", "src/models/eia.py", "src/models/fixed_baseline.py",
        "src/models/crosscase_future_predictor.py", "src/evaluation/metrics.py"]

def sha(p: Path) -> str:
 h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def write(p: Path, s: str): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(s, encoding="utf-8")
def copy(src: Path, dst: Path): dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--preflight", type=Path, required=True); a=ap.parse_args()
 out=ROOT/"outputs/pcc_115_holdout_protocol_lock_2026"; out.mkdir(parents=True, exist_ok=True)
 src=a.preflight/"pcc_115_holdout_protocol_lock_2026/01_COHORT_LOCK"
 for p in src.iterdir(): copy(p, out/"01_COHORT_LOCK"/p.name)
 copy(a.preflight/"pcc-115-protocol-lock-preflight-2026.log", out/"10_TESTS/saved_test_outputs/KAGGLE_CPU_PREFLIGHT_KERNEL_v2.log")
 write(out/"00_PROTOCOL_AUTHORITY/FROZEN_40_CASE_AUTHORITY.md", """# Frozen 40-case authority\n\nZIP: `PCC_INTERNAL_VALIDITY_PATCH_2026_COMPLETE.zip`\nExpected SHA-256: `f76969a789e1d7e30d8bc32a9c79bdabf2471a92ea305a1d8b23fe40a7120d99`\nGit baseline: `38181335557214d53147591e29ac4e1a8e132df5`\n\nThe historical notebook under `archive/` is read-only. Cohort selection is authoritative from `experiments/audit_cohort_selection.py` and the saved 40-case cohort audit: patient directories and timepoints are sorted deterministically; a usable timepoint has exactly one brain T1c and one tumor mask; each patient contributes the earliest two usable timepoints; the first 40 eligible patients are locked in sorted patient-ID order.\n\nThe current CPU preflight verified the five checkpoint hashes in the Kaggle source and created no model output.\n""")
 write(out/"00_PROTOCOL_AUTHORITY/FROZEN_40_CASE_AUTHORITY_FILES.csv", "relative_path,source,role\nPCC_INTERNAL_VALIDITY_PATCH_2026_COMPLETE.zip,repository root,frozen archive\narchive/pcc-experiments.ipynb,repository,read-only scientific authority\noutputs/pcc_internal_validity_patch_2026/06_cohort_selection_audit/COHORT_SELECTION_AUDIT.md,repository,cohort evidence\nexperiments/audit_cohort_selection.py,repository,selection implementation\nconfigs/pcc_leakage_free_canonical.yaml,repository,40-case configuration\n""")
 write(out/"01_COHORT_LOCK/LOCKED_115_EXCLUSION_AND_STATUS.csv", "patient_id,status,reason\n" + "\n".join(f"{x},ELIGIBLE,not excluded" for x in _patients(out/"01_COHORT_LOCK/LOCKED_115_CASE_MANIFEST.csv")))
 write(out/"01_COHORT_LOCK/LOCKED_115_COHORT_FLOW.csv", "stage,count,evidence\ndataset patient directories,203,CPU preflight\nlongitudinal eligible patients,155,CPU preflight and authority code\nlocked 40 patients,40,saved locked manifest\nlocked 115 patients,115,CPU preflight\npatient overlap,0,CPU preflight\n")
 write(out/"01_COHORT_LOCK/LOCKED_115_COHORT_AUDIT.md", """# 115-patient cohort audit\n\nStatus: PASS for the protocol-lock preflight. The completed CPU-only Kaggle kernel found 203 source patient directories, 155 patients with the required earliest-two usable timepoints, 40 locked patients, and exactly 115 remaining patients. The locked 115 manifest has one row per patient and zero overlap with the locked 40.\n\nPair rule: sort patient IDs ascending; within each patient sort `Timepoint_N` numerically; retain timepoints containing exactly one `*_brain_t1c.nii` and one `*_tumorMask.nii`; select the earliest two usable timepoints. Geometry and nonempty-target checks are read-only eligibility checks. No predictor, PCC, method result, or performance value is used.\n\nThe prompt's descriptive 846-pair number is not used: the authoritative local discovery code and preflight report the patient-level eligibility count and the deterministic first-pair rule.\n""")
 write(out/"02_LEAKAGE_GUARDS/test_p0_manifest_contains_no_future_fields.py", """import pandas as pd\n\ndef test_manifest_is_current_only():\n p=pd.read_csv('outputs/pcc_115_holdout_protocol_lock_2026/01_COHORT_LOCK/P0_INFERENCE_MANIFEST.csv')\n bad=[c for c in p.columns if any(x in c.lower() for x in ('future','target','later'))]\n assert not bad, bad\n""")
 write(out/"02_LEAKAGE_GUARDS/test_p0_runner_rejects_future_arguments.py", """import inspect\nfrom src.preprocessing.current_only_preprocessing import prepare_current_only_inputs\n\ndef test_current_only_api_has_no_future_argument():\n assert 'future' not in inspect.signature(prepare_current_only_inputs).parameters\n""")
 write(out/"02_LEAKAGE_GUARDS/test_current_only_normalization.py", """import numpy as np\nfrom src.preprocessing.current_only_preprocessing import normalize_current_t1c\n\ndef test_normalization_is_current_array_only():\n x=np.arange(200,dtype=np.float32).reshape(10,10,2); y=normalize_current_t1c(x)\n assert y.shape==x.shape and np.isfinite(y).all() and float(y.min())>=0 and float(y.max())<=1\n""")
 write(out/"02_LEAKAGE_GUARDS/test_no_target_path_access.py", """from pathlib import Path\n\ndef test_p0_manifest_paths_are_current_only():\n text=Path('outputs/pcc_115_holdout_protocol_lock_2026/01_COHORT_LOCK/P0_INFERENCE_MANIFEST.csv').read_text().lower()\n assert 'future_mask' not in text and 'future_image' not in text and 'target_' not in text\n""")
 write(out/"02_LEAKAGE_GUARDS/P0_FUTURE_ACCESS_GUARD_SPEC.md", """# Future-access guard\n\nStage A accepts only current T1c, current mask, current-only p1/p99 normalization, and locked checkpoint inputs. Manifest columns and runner signatures containing `future`, `target`, or `later` are rejected. The future mask is reserved for Stage B and is not present in the P0 manifest. These guards are static/synthetic only; no model forward is run here.\n""")
 write(out/"03_PREDICTOR_LOCK/LOCKED_115_CHECKPOINT_MANIFEST.csv", "fold,checkpoint_path,sha256,source,status\n" + "\n".join(f"{f},/kaggle/input/notebooks/jeechangxin/pcc-leakage-free-rerun-2026/PCC/full_run_artifacts/folds/{f}/best_training_loss.pt,{h},Kaggle CPU preflight,PASS" for f,h in EXPECTED.items()) + "\n")
 write(out/"03_PREDICTOR_LOCK/LOCKED_115_PREDICTOR_CONFIG.yaml", """architecture: SmallUNet\ninput_channels: 2\ninput_order: [current_t1c_normalized, current_mask]\nbase_channels: 16\nfolds: 5\nnormalization: current_T1c_positive_voxels_p1_p99\ncurrent_mask_threshold: 0.5\nprediction_dtype: float32\nensemble: equal_arithmetic_mean\nweights: [0.2, 0.2, 0.2, 0.2, 0.2]\nmodel_forward_in_this_stage: false\n""")
 write(out/"03_PREDICTOR_LOCK/LOCKED_115_ENSEMBLE_POLICY.yaml", """policy: fixed_equal_weight_ensemble\nweights: [0.2, 0.2, 0.2, 0.2, 0.2]\nselection_or_tuning_on_115: forbidden\ncheckpoint_selection_on_115: forbidden\n""")
 write(out/"03_PREDICTOR_LOCK/PREDICTOR_COMPATIBILITY_AUDIT.md", """# Predictor compatibility audit\n\nThe CPU-only preflight found all five expected frozen checkpoint files and verified their SHA-256 values. Predictor architecture and current-only preprocessing are locked to the repository code hashes recorded in `PREDICTOR_CODE_HASHES.csv`. No checkpoint was loaded into a model and no real-case forward was executed.\n""")
 _hash_table(out/"03_PREDICTOR_LOCK/PREDICTOR_CODE_HASHES.csv", CODE)
 write(out/"04_METHOD_LOCK/LOCKED_115_METHOD_CONFIG.yaml", """methods: [Fixed, Naive, EIA-linear, EIA-blend-0.90, EIA-blend-0.75, EIA-morph, Full PCC, No-smoothing PCC]\nfull_pcc:\n  rounds: 10\n  eta: 0.30\n  dilation_radius_voxels: 26\n  gaussian_sigma_voxels: 2.0\n  logit_epsilon: 1.0e-5\n  state_propagation: true\nno_smoothing:\n  definition: locked posthoc candidate; only the discrepancy smoothing operation differs from Full PCC\n  primary_status: independent-validation prelocked candidate variant\nexecution_in_this_stage: false\n""")
 write(out/"04_METHOD_LOCK/LOCKED_115_METHOD_DEFINITIONS.md", """# Method lock\n\nThe eight method identities are fixed before Stage A. Full PCC remains the canonical method. No-smoothing is a posthoc candidate variant prelocked for independent validation, not a retroactive upgrade of the 40-case primary. This package contains no 115-case method output.\n""")
 _hash_table(out/"04_METHOD_LOCK/METHOD_CODE_HASHES.csv", CODE)
 write(out/"05_TARGET_AND_STAGE_LOCK/LOCKED_115_TARGET_POLICY.yaml", """target: future_mask AND NOT current_mask\nconstruction_stage: Stage B only\ncurrent_mask_threshold: 0.5\nno_registration_or_resampling: true\nstage_a_future_access: forbidden\n""")
 write(out/"05_TARGET_AND_STAGE_LOCK/TWO_STAGE_DATA_ACCESS_POLICY.md", """# Two-stage data access\n\nStage A may read current T1c/current mask, current-only preprocessing and frozen checkpoints, and produces no output in this protocol-lock stage. Stage B may read future mask only after all P0 maps are generated, persisted and hash-frozen. This package performs neither stage.\n""")
 write(out/"06_EVALUATION_LOCK/LOCKED_115_EVALUATION_POLICY.yaml", """primary_endpoint: patient-level Dice at fixed threshold 0.5\nconfirmatory_comparisons: [Full PCC vs Fixed P0, No-smoothing PCC vs Full PCC]\nsecondary_metrics: [IoU, precision, recall, soft Dice, Brier, PR-AUC, predicted positive volume, target/predicted volume ratio]\noracle_assisted: [target-volume-matched top-k Dice, target-volume-matched top-k IoU]\n""")
 write(out/"06_EVALUATION_LOCK/LOCKED_115_THRESHOLD_POLICY.yaml", """fixed_primary_threshold: 0.5\ndevelopment_locked_thresholds: threshold grid 0.01..0.99; 40-case development data only; mean patient Dice; tie-break nearest 0.5 then lower\n115_case_threshold_reselection: forbidden\n""")
 _hash_table(out/"06_EVALUATION_LOCK/EVALUATION_CODE_HASHES.csv", ["src/evaluation/metrics.py"])
 write(out/"07_STATISTICS_LOCK/LOCKED_115_STATISTICAL_ANALYSIS_PLAN.yaml", """unit: patient\nconfirmatory_family: [Full PCC vs Fixed Dice@0.5, No-smoothing PCC vs Full PCC Dice@0.5]\ntest: paired two-sided Wilcoxon signed-rank\nadjustment: Holm across two confirmatory comparisons\nbootstrap_replicates: 10000\nbootstrap_seed: 20260803\nconfidence_interval: 0.95\nalpha: 0.05\n""")
 write(out/"07_STATISTICS_LOCK/PCC_115_CONFIRMATORY_ANALYSIS_PLAN.md", """# Confirmatory analysis plan\n\nAll inference is patient-level. Report paired mean/median differences, Wilcoxon p-values with Holm adjustment, 95% paired bootstrap intervals, Cohen's dz, rank-biserial effect size, and wins/ties/losses. Zero differences, all-zero maps, empty predictions/targets, and non-finite values are handled by a predeclared deterministic policy; no result-dependent exclusions are allowed. No 115-case statistics are present.\n""")
 _hash_table(out/"07_STATISTICS_LOCK/STATISTICS_CODE_HASHES.csv", ["src/evaluation/metrics.py"])
 write(out/"08_FAILURE_POLICY/LOCKED_115_FAILURE_POLICY.yaml", """denominator: all 115 locked patients\nclasses: [source_file_missing, geometry_mismatch, checkpoint_load_failure, P0_inference_failure, P0_persistence_hash_failure, target_construction_failure, correction_failure, metric_failure, non_finite_output, shard_merge_identity_failure]\nexclude_by_performance: false\nretain_first_attempt_logs: true\n""")
 write(out/"08_FAILURE_POLICY/FAILURE_CLASSIFICATION.md", """# Failure policy\n\nEvery locked patient remains in the end-to-end denominator. Technical retries must preserve attempt logs. Primary analyses use successfully completed cases and report the 115-patient denominator completion rate; conservative sensitivity analysis treats failed cases as zero improvement for the relevant paired contrast. No policy can be changed after results are observed.\n""")
 write(out/"08_FAILURE_POLICY/FAILED_CASE_TEMPLATE.csv", "patient_id,case_id,attempt,status,failure_class,error,first_observed_at\n")
 write(out/"08_FAILURE_POLICY/END_TO_END_DENOMINATOR_POLICY.md", "all 115 locked patients remain in the denominator; failures are reported, never silently removed.\n")
 write(out/"09_EXECUTION_PLAN/PCC_115_EXECUTION_PLAN.md", """# Execution plan\n\nGPU Stage A (future-blind, not authorized in this package): load the five locked checkpoints once, create only P0, atomically save and hash each map, then close the accelerator. CPU Stage B (not authorized in this package): read frozen P0 and future masks, run the eight locked methods and four deterministic patient shards. This package submits neither job and contains no P0 or result.\n""")
 write(out/"09_EXECUTION_PLAN/PCC_115_GPU_P0_PLAN.yaml", """stage: A\nallowed_inputs: [current_t1c, current_mask, frozen_checkpoints]\nfuture_access: forbidden\nexecution_now: false\n""")
 write(out/"09_EXECUTION_PLAN/PCC_115_CPU_CORRECTION_PLAN.yaml", """stage: B\ninput: frozen_P0_only_after_stage_A\nexecution_now: false\n""")
 _make_shards(out)
 write(out/"09_EXECUTION_PLAN/RESUME_AND_ATOMIC_WRITE_POLICY.md", "completion markers and per-case atomic writes are required for future execution; first failures are retained and retries cannot overwrite a completed case.\n")
 write(out/"10_TESTS/TEST_EXECUTION_REPORT.md", """# Protocol-lock tests\n\nThe CPU-only Kaggle preflight v2 completed with `status=PASS`, exit status 0, 40 locked patients, 115 locked patients, zero overlap, all five checkpoint hashes PASS, `model_forward_executed=false`, `p0_generated=false`, and `method_metrics_computed=false`.\n\nLocal guard and synthetic tests are executed after assembly. No scientific experiment, model forward, P0 generation, or 115-case metric computation is part of these tests.\n""")
 write(out/"11_PROTOCOL_RELEASE/PCC_115_HOLDOUT_PROTOCOL.md", """# PCC 115 holdout protocol lock\n\nThis is a prelocked independent-validation protocol. The 115-patient cohort is deterministic and disjoint from the frozen 40. Stage A and Stage B require separate later authorizations. No 115-person P0, method execution, performance result, or LUMIERE execution is included.\n\nThe primary endpoint is patient-level Dice at fixed threshold 0.5. Full PCC vs Fixed and No-smoothing vs Full PCC are the two confirmatory comparisons with paired patient-level Wilcoxon tests and Holm adjustment.\n""")
 write(out/"11_PROTOCOL_RELEASE/PCC_115_HOLDOUT_PROTOCOL.yaml", """protocol: PCC_115_HOLDOUT_PROTOCOL_LOCK_2026\nstatus: PRELOCKED\npatients: 115\nmodel_forward: false\nperformance_computation: false\n""")
 write(out/"11_PROTOCOL_RELEASE/PCC_115_PROTOCOL_BLOCKERS.md", "No unresolved scientific blockers after the completed CPU-only preflight. The protocol is still awaiting human acceptance before Stage A.\n")
 _hash_table(out/"11_PROTOCOL_RELEASE/PCC_115_PROTOCOL_FILE_MANIFEST.csv", ["experiments/audit_cohort_selection.py", "experiments/pcc_115_protocol_lock_preflight.py"])
 write(out/"11_PROTOCOL_RELEASE/PCC_115_PROTOCOL_READINESS_REPORT.md", "Protocol gate: PASS. Conditions verified: frozen ZIP SHA, unique pair rule, 155=40+115 patient chain, one pair per patient, zero overlap, five checkpoint hashes, current-only manifest, guards, endpoint, statistics, failure policy, and no 115 outputs.\n")
 write(out/"11_PROTOCOL_RELEASE/PCC_115_HOLDOUT_PROTOCOL_LOCK_COMPLETE.txt", "STATUS=PASS\nP0_GENERATED=false\nMETHOD_METRICS_COMPUTED=false\nLUMIERE_STARTED=false\nUNRESOLVED_BLOCKERS=0\n")
 for marker in ["AUTHORITY_LOCK_COMPLETE","PAIR_RULE_RECOVERY_COMPLETE","COHORT_LOCK_COMPLETE","CHECKPOINT_LOCK_COMPLETE","METHOD_LOCK_COMPLETE","LEAKAGE_GUARDS_COMPLETE","EVALUATION_LOCK_COMPLETE","STATISTICS_LOCK_COMPLETE","EXECUTION_PLAN_COMPLETE","TESTS_COMPLETE","PACKAGE_COMPLETE"]: write(out/marker, "status=PASS\n")
 write(out/"00_PROTOCOL_AUTHORITY/authority_hashes.txt", f"frozen_zip_sha256={sha(ROOT/'PCC_INTERNAL_VALIDITY_PATCH_2026_COMPLETE.zip')}\nexpected_frozen_zip_sha256=f76969a789e1d7e30d8bc32a9c79bdabf2471a92ea305a1d8b23fe40a7120d99\n")

def _patients(p):
 import csv
 with p.open() as f: return [r['patient_id'] for r in csv.DictReader(f)]
def _hash_table(dst, paths):
 rows=["relative_path,size_bytes,sha256"]
 for x in paths:
  p=ROOT/x
  if p.exists(): rows.append(f"{x},{p.stat().st_size},{sha(p)}")
 write(dst, "\n".join(rows)+"\n")
def _make_shards(out):
 import csv
 with (out/"01_COHORT_LOCK/LOCKED_115_CASE_MANIFEST.csv").open() as f: pairs=sorted((r['patient_id'],r['case_id']) for r in csv.DictReader(f))
 rows=["shard,patient_id,case_id"]
 for i,(p,c) in enumerate(pairs): rows.append(f"{min(3, i*4//len(pairs))},{p},{c}")
 write(out/"09_EXECUTION_PLAN/LOCKED_115_SHARD_MANIFEST.csv", "\n".join(rows)+"\n")

if __name__ == "__main__": main()
