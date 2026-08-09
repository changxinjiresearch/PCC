#!/usr/bin/env python3
"""Build the pre-outcome RHUH 39-patient external protocol lock.

Inputs are Phase 0/0B CSV/JSON/YAML authorities, frozen source files, and
checkpoint bytes.  This builder never opens a NIfTI file or executes a model.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

import yaml


REPO = Path("/home/changxinjiresearch/Research/Projects/PCC")
PHASE0 = REPO / "outputs/pcc_rhuh_external_validation_2026"
PHASE0B = REPO / "outputs/pcc_rhuh_external_validation_phase0b_geometry_resolution_2026"
OUT = REPO / "outputs/pcc_rhuh_external_protocol_lock_2026"
ZIP = REPO / "PCC_RHUH_EXTERNAL_PROTOCOL_LOCK_2026.zip"
ZIP_SHA = REPO / "PCC_RHUH_EXTERNAL_PROTOCOL_LOCK_2026.zip.sha256"
SUMMARY = REPO / "PCC_RHUH_EXTERNAL_PROTOCOL_LOCK_2026_RELEASE_SUMMARY.txt"
BUILDER = Path(__file__)

FILE_INV = PHASE0 / "00_DATA_INVENTORY/RHUH_FILE_INVENTORY.csv"
GEOM40 = PHASE0 / "02_PAIR_AND_GEOMETRY/RHUH_LONGITUDINAL_GEOMETRY_AUDIT.csv"
PHASE0_STATUS = PHASE0 / "05_RELEASE/PCC_RHUH_EXTERNAL_VALIDATION_PHASE0_STATUS.json"
AMENDMENT40 = PHASE0B / "03_COHORT_DECISION/RHUH_EXTERNAL_COHORT_AMENDMENT.csv"
PHASE0B_STATUS = PHASE0B / "05_RELEASE/PCC_RHUH_EXTERNAL_VALIDATION_PHASE0B_STATUS.json"
GEOM_POLICY0B = PHASE0B / "03_COHORT_DECISION/RHUH_EXTERNAL_GEOMETRY_POLICY.yaml"
MASK_LOCK0B = PHASE0B / "04_MASK_SEMANTICS/RHUH_EXTERNAL_MASK_SEMANTIC_LOCK.yaml"

MODEL_SOURCE = REPO / "src/models/crosscase_future_predictor.py"
PREPROCESS_SOURCE = REPO / "src/preprocessing/current_only_preprocessing.py"
FORWARD_SOURCE = REPO / "experiments/run_115_stage_a_p0.py"
PREDICTOR_CONFIG = REPO / "outputs/pcc_115_holdout_stage_a_p0_freeze_2026/00_STAGE_A_AUTHORITY/PROTOCOL_LOCK/LOCKED_115_PREDICTOR_CONFIG.yaml"
CHECKPOINT_ROOT = REPO / "outputs/pcc_115_stage_a_duplicate_p0_audit_2026/checkpoints_remote_v8/PCC/full_run_artifacts/folds"
CHECKPOINT_HASHES = {
    "fold_1": "bb86bcdbde7e0e4a41f5700efd8c532f2a06d3a3d9bde183f0090238a277b18c",
    "fold_2": "fb75fc2dc1d6703e22ca7ef260a54a0563a184c5a295c0890279c51cb054e759",
    "fold_3": "3e2cb75c84fb861b82789d2bf87517ee494c3435e1b06d64c739437dce547107",
    "fold_4": "28656b1d282fc66e054887166a990810b25d7e6a66d9c21e8f3951868f7291c3",
    "fold_5": "69250135d3eef595b9244426f511c165f10635e1a56241f8fa372959d874c1f3",
}
SCIENTIFIC_COMMIT = "66269681e4417dccabc68ecaa792d76e19aa5856"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True))


def write_yaml(path: Path, value: Any) -> None:
    write_text(path, yaml.safe_dump(value, sort_keys=False, allow_unicode=True))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def core_grid_equal(row: dict[str, str], a: str, b: str) -> bool:
    return all(row[f"{a}_{key}"] == row[f"{b}_{key}"] for key in ("shape", "spacing", "affine", "orientation", "world_bbox"))


def build_initial() -> None:
    if OUT.exists() or ZIP.exists() or ZIP_SHA.exists() or SUMMARY.exists():
        raise RuntimeError("Refusing to overwrite existing RHUH protocol-lock output")
    for folder in ("00_AUTHORITY", "01_COHORT_LOCK", "02_GEOMETRY_LOCK", "03_MASK_LOCK", "04_PREDICTOR_LOCK", "05_STAGE_A_LOCK", "06_STAGE_B_LOCK", "07_STATISTICS_LOCK", "08_FAILURE_LOCK", "09_INTERPRETATION_BOUNDARY", "10_TESTS", "11_RELEASE"):
        (OUT / folder).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(BUILDER, OUT / "00_AUTHORITY/GENERATE_RHUH_EXTERNAL_PROTOCOL_LOCK.py")

    authorities = [FILE_INV, GEOM40, PHASE0_STATUS, AMENDMENT40, PHASE0B_STATUS, GEOM_POLICY0B, MASK_LOCK0B, MODEL_SOURCE, PREPROCESS_SOURCE, FORWARD_SOURCE, PREDICTOR_CONFIG]
    authority_rows = [{
        "relative_path": str(p.relative_to(REPO)), "size_bytes": p.stat().st_size, "sha256": sha256(p),
        "scientific_role": "phase0_or_phase0b_authority" if p.is_relative_to(PHASE0) or p.is_relative_to(PHASE0B) else "frozen_predictor_authority",
        "exists": "true", "readable": "true",
    } for p in authorities]
    write_csv(OUT / "00_AUTHORITY/RHUH_EXTERNAL_PROTOCOL_AUTHORITY_FILES.csv", authority_rows)
    write_text(OUT / "00_AUTHORITY/RHUH_EXTERNAL_PROTOCOL_AUTHORITY_REPORT.md", """
# RHUH external protocol authorities

The lock is deterministically derived from the accepted Phase 0 official-file inventory and geometry audit, the accepted Phase 0B CASE B cohort amendment, and the frozen internal predictor authorities. All authorities were hash-locked before protocol generation. No NIfTI voxel array, external P0, target, method output, or performance result was read.
""")

    inv = load_csv(FILE_INV)
    amendment = load_csv(AMENDMENT40)
    geom = {r["patient_id"]: r for r in load_csv(GEOM40)}
    include = sorted(r["patient_id"] for r in amendment if r["external_confirmatory_included"] == "true")
    exclude = sorted(r["patient_id"] for r in amendment if r["external_confirmatory_included"] == "false")
    if len(include) != 39 or exclude != ["RHUH-0008"]:
        raise RuntimeError("Accepted Phase 0B cohort authority mismatch")
    idx = {(r["patient_id"], r["timepoint_code"], r["modality"]): r for r in inv}

    cohort_rows = []
    geometry_rows = []
    for patient in include:
        case = f"{patient}_EARLY_POSTOP_TO_RECURRENCE_T1CE"
        cur_t1 = idx[(patient, "1", "t1ce")]
        cur_seg = idx[(patient, "1", "segmentations")]
        fut_t1 = idx[(patient, "2", "t1ce")]
        fut_seg = idx[(patient, "2", "segmentations")]
        g = geom[patient]
        current_internal = core_grid_equal(g, "current_t1ce", "current_seg")
        future_internal = core_grid_equal(g, "future_t1ce", "future_seg")
        longitudinal_t1 = core_grid_equal(g, "current_t1ce", "future_t1ce")
        longitudinal_seg = core_grid_equal(g, "current_seg", "future_seg")
        valid = current_internal and future_internal and longitudinal_t1 and longitudinal_seg
        cohort_rows.append({
            "patient_id": patient, "case_id": case,
            "current_timepoint_code": "1", "current_timepoint": "EARLY_POSTOPERATIVE_LT72H",
            "future_timepoint_code": "2", "future_timepoint": "RECURRENCE_DIAGNOSIS_FOLLOWUP",
            "current_t1ce_path": cur_t1["local_relative_path"], "current_t1ce_sha256": cur_t1["computed_sha256"],
            "current_segmentation_path": cur_seg["local_relative_path"], "current_segmentation_sha256": cur_seg["computed_sha256"],
            "future_t1ce_path": fut_t1["local_relative_path"], "future_t1ce_sha256": fut_t1["computed_sha256"],
            "future_segmentation_path": fut_seg["local_relative_path"], "future_segmentation_sha256": fut_seg["computed_sha256"],
            "current_mask_mapping": "RHUH_segmentation_gt_0_labels_1_2_3",
            "pair_selection_rule": "EARLY_POSTOPERATIVE_TO_RECURRENCE_FOR_ALL_GEOMETRY_ELIGIBLE_PATIENTS",
            "geometry_policy": "RHUH_EXTERNAL_EFFECTIVE_PHYSICAL_GRID_IDENTITY_POLICY",
            "geometry_valid": str(valid).lower(),
            "planned_external_p0_relative_path": f"external_stage_a/P0/{case}.npy",
            "external_p0_status_at_lock": "NOT_GENERATED",
        })
        geometry_rows.append({
            "patient_id": patient, "case_id": case,
            "current_t1ce_vs_current_segmentation_valid": str(current_internal).lower(),
            "recurrence_t1ce_vs_recurrence_segmentation_valid": str(future_internal).lower(),
            "current_vs_recurrence_t1ce_grid_valid": str(longitudinal_t1).lower(),
            "current_vs_recurrence_segmentation_grid_valid": str(longitudinal_seg).lower(),
            "effective_geometry_valid": str(valid).lower(),
            "shape": g["current_t1ce_shape"], "spacing": g["current_t1ce_spacing"],
            "orientation": g["current_t1ce_orientation"], "selected_affine": g["current_t1ce_affine"],
            "world_bbox": g["current_t1ce_world_bbox"],
            "qform_sform_metadata_identical": str(g["all_primary_pair_geometry_match"] == "true").lower(),
            "registration_performed": "false", "resampling_performed": "false", "interpolation_performed": "false",
            "future_voxel_array_read": "false",
        })
    write_csv(OUT / "01_COHORT_LOCK/LOCKED_RHUH_39_EXTERNAL_CONFIRMATORY_CASE_MANIFEST.csv", cohort_rows)
    write_csv(OUT / "01_COHORT_LOCK/LOCKED_RHUH_39_EXTERNAL_PATIENT_IDS.csv", [{"patient_id": p} for p in include])
    write_csv(OUT / "01_COHORT_LOCK/EXCLUDED_RHUH_EXTERNAL_CASES.csv", [{
        "patient_id": "RHUH-0008", "case_id": "RHUH-0008_EARLY_POSTOP_TO_RECURRENCE_T1CE",
        "exclusion_code": "PRE_OUTCOME_GEOMETRY_INCOMPATIBILITY", "exclusion_stage": "PRE_EXTERNAL_STAGE_A_PRE_OUTCOME_ACCESS",
        "exclusion_reason": "Lossless axis permutation/flip cannot place early-postoperative and recurrence files on the same physical voxel grid",
        "external_p0_seen_before_exclusion": "false", "target_constructed_before_exclusion": "false",
        "performance_seen_before_exclusion": "false", "future_segmentation_voxel_array_seen_before_exclusion": "false",
        "original_40_patient_inventory_retained": "true",
    }])
    audit_rows = []
    for patient in sorted({r["patient_id"] for r in amendment}):
        excluded = patient == "RHUH-0008"
        audit_rows.append({
            "patient_id": patient, "original_40_inventory_member": "true",
            "locked_39_confirmatory_member": str(not excluded).lower(),
            "transition": "EXCLUDED" if excluded else "RETAINED",
            "exclusion_code": "PRE_OUTCOME_GEOMETRY_INCOMPATIBILITY" if excluded else "",
            "outcome_access_before_transition": "false", "original_inventory_modified": "false",
        })
    write_csv(OUT / "01_COHORT_LOCK/RHUH_40_TO_39_COHORT_AUDIT.csv", audit_rows)

    geometry_policy = {
        "policy_id": "RHUH_EXTERNAL_EFFECTIVE_PHYSICAL_GRID_IDENTITY_POLICY",
        "scope": "all_locked_external_primary_pairs",
        "required_identity": ["shape", "selected_NIfTI_affine", "voxel_spacing", "orientation", "voxel_center_world_ranges", "world_space_bounds"],
        "allowed": ["header verification", "lossless orientation representation checking"],
        "forbidden": ["registration", "resampling", "interpolation", "case-specific affine repair", "header rewriting to force alignment", "outcome-driven geometry correction"],
        "qform_sform_metadata_policy": "record separately; selected effective physical grid must remain identical",
        "locked_confirmatory_geometry_valid": "39/39",
        "excluded_pre_outcome": ["RHUH-0008"],
        "files_modified": False,
    }
    write_yaml(OUT / "02_GEOMETRY_LOCK/LOCKED_RHUH_EXTERNAL_GEOMETRY_POLICY.yaml", geometry_policy)
    write_text(OUT / "02_GEOMETRY_LOCK/LOCKED_RHUH_EXTERNAL_GEOMETRY_POLICY.md", """
# Locked RHUH external geometry policy

All primary external pairs must have identical effective physical voxel grids between current T1ce/current segmentation, recurrence T1ce/recurrence segmentation, and current/recurrence target grids. Identity requires matching shape, selected NIfTI affine, spacing, orientation, voxel-center ranges, and world bounds. qform/sform metadata differences remain recorded but cannot override a matching selected effective grid.

Header verification and lossless orientation representation checks are allowed. Registration, resampling, interpolation, case-specific affine repair, forced header rewriting, and outcome-driven correction are forbidden. The locked cohort passes effective geometry in 39/39 cases; RHUH-0008 was excluded before outcome access.
""")
    write_csv(OUT / "02_GEOMETRY_LOCK/LOCKED_RHUH_39_GEOMETRY_MANIFEST.csv", geometry_rows)

    mask_policy = {
        "status": "LOCKED_PRE_EXTERNAL_P0",
        "internal_MU_mask": "all non-background labels 1|2|3|4",
        "RHUH_expression": "segmentation > 0",
        "RHUH_labels": {1: "necrosis", 2: "peritumoral / non-enhancing abnormality", 3: "enhancing tumor"},
        "mapping_class": "closest available pathological-region mapping",
        "perfect_ontology_equivalence": False,
        "known_difference": "RHUH has no independent resection-cavity label",
        "forbidden_alternatives_after_lock": ["label 3 only", "labels 1+3", "labels 2+3", "any other result-driven combination"],
        "performance_used_to_select_mapping": False,
        "limitations_disclosure_required": True,
    }
    write_yaml(OUT / "03_MASK_LOCK/LOCKED_RHUH_EXTERNAL_MASK_MAPPING.yaml", mask_policy)
    write_text(OUT / "03_MASK_LOCK/LOCKED_RHUH_EXTERNAL_MASK_MAPPING.md", """
# Locked RHUH external mask mapping

Internal MU-Glioma-Post masks use all non-background labels 1–4. RHUH masks are locked as `segmentation > 0`: label 1 necrosis, label 2 peritumoral/non-enhancing abnormality, and label 3 enhancing tumor. This is the closest available pathological-region mapping, not perfect ontology equivalence, because RHUH lacks an independent resection-cavity label.

The mapping cannot be changed after RHUH results to label 3 only, labels 1+3, labels 2+3, or any other combination. The ontology difference is a predeclared limitation.
""")

    checkpoint_rows = []
    for fold, expected in CHECKPOINT_HASHES.items():
        p = CHECKPOINT_ROOT / fold / "best_training_loss.pt"
        actual = sha256(p)
        checkpoint_rows.append({
            "fold": fold, "checkpoint_path": str(p.relative_to(REPO)),
            "original_kaggle_path": f"/kaggle/input/notebooks/jeechangxin/pcc-leakage-free-rerun-2026/PCC/full_run_artifacts/folds/{fold}/best_training_loss.pt",
            "size_bytes": p.stat().st_size, "expected_sha256": expected, "computed_sha256": actual,
            "hash_status": "MATCH" if actual == expected else "MISMATCH", "ensemble_weight": "0.2",
        })
    write_csv(OUT / "04_PREDICTOR_LOCK/LOCKED_RHUH_FROZEN_PREDICTOR_MANIFEST.csv", checkpoint_rows)
    predictor_policy = {
        "status": "LOCKED_PRE_EXTERNAL_FORWARD",
        "architecture": "2D slice-wise CrossCaseSmallUNet",
        "architecture_parameters": {"input_channels": 2, "output_channels": 1, "base_channels": 16},
        "input_order": ["current_T1ce_normalized", "locked_binary_current_mask"],
        "normalization": "current-volume positive voxels p1/p99, clipped to [0,1]",
        "preprocessing_implementation": {"path": str(PREPROCESS_SOURCE.relative_to(REPO)), "sha256": sha256(PREPROCESS_SOURCE)},
        "architecture_implementation": {"path": str(MODEL_SOURCE.relative_to(REPO)), "sha256": sha256(MODEL_SOURCE)},
        "forward_implementation": {"path": str(FORWARD_SOURCE.relative_to(REPO)), "sha256": sha256(FORWARD_SOURCE)},
        "predictor_config": {"path": str(PREDICTOR_CONFIG.relative_to(REPO)), "sha256": sha256(PREDICTOR_CONFIG)},
        "scientific_git_commit": SCIENTIFIC_COMMIT,
        "checkpoint_count": 5, "checkpoint_hashes_match": all(r["hash_status"] == "MATCH" for r in checkpoint_rows),
        "ensemble": "equal arithmetic mean", "ensemble_weights": [0.2] * 5,
        "preprocessing_storage_dtype": "float16", "formal_forward_tensor_dtype": "float32", "prediction_dtype": "float32",
        "forward_logic": "slice-wise batches; logits -> sigmoid; five predictions -> float32 arithmetic mean",
        "forbidden": ["RHUH training", "fine-tuning", "calibration", "checkpoint selection", "test-time adaptation", "RHUH-specific normalization tuning", "RHUH-specific threshold selection"],
        "predictor_forward_executed_in_protocol_lock": False,
    }
    write_yaml(OUT / "04_PREDICTOR_LOCK/LOCKED_RHUH_FROZEN_PREDICTOR_POLICY.yaml", predictor_policy)
    write_text(OUT / "04_PREDICTOR_LOCK/LOCKED_RHUH_FROZEN_PREDICTOR_POLICY.md", f"""
# Locked RHUH frozen predictor policy

External Stage A may use only the five frozen `CrossCaseSmallUNet(2,1,16)` checkpoints at internal scientific commit `{SCIENTIFIC_COMMIT}`. All 5/5 checkpoint SHA-256 values match. Current-only p1/p99 normalization, two-channel input order, float32 forward logic, sigmoid, and equal 0.2 fold weights are immutable.

RHUH training, fine-tuning, calibration, checkpoint selection, test-time adaptation, RHUH-specific normalization tuning, and threshold selection are forbidden. No predictor was loaded or executed during this lock.
""")

    stage_a = {
        "status": "LOCKED_NOT_EXECUTED", "cohort_manifest": "LOCKED_RHUH_39_EXTERNAL_CONFIRMATORY_CASE_MANIFEST.csv",
        "denominator": 39,
        "allowed_inputs": ["early-postoperative T1ce", "early-postoperative locked current mask", "five frozen checkpoints", "locked current-only preprocessing"],
        "future_information_allowed_before_P0_freeze": ["file identity", "existence", "file SHA-256", "header-level geometry metadata"],
        "forbidden_before_P0_freeze": ["recurrence segmentation voxel arrays", "recurrence-derived target", "recurrence-derived performance"],
        "future_voxel_content_may_not_select_cases": True,
        "per_case_P0_requirements": ["float32", "finite", "range [0,1]", "case identity", "file size", "SHA-256", "completion marker"],
        "stage_a_completion_gate": "39/39 P0 generated, verified, and SHA-256 frozen",
        "stage_b_before_gate": "FORBIDDEN",
        "external_P0_generated_during_lock": False,
    }
    write_yaml(OUT / "05_STAGE_A_LOCK/LOCKED_RHUH_EXTERNAL_STAGE_A_P0_PROTOCOL.yaml", stage_a)
    write_text(OUT / "05_STAGE_A_LOCK/LOCKED_RHUH_EXTERNAL_STAGE_A_P0_PROTOCOL.md", """
# Locked RHUH External Stage A P0 protocol

Stage A reads only early-postoperative T1ce, the locked early-postoperative mask, the five frozen checkpoints, and frozen current-only preprocessing. Recurrence segmentation arrays, targets, and performance are forbidden. Future knowledge is limited to file identity, existence, SHA-256, and header geometry and cannot select cases.

Each of 39 P0 files must be finite float32 in [0,1], linked to one locked case, and frozen with file size, SHA-256, and completion marker. External Stage B is prohibited until 39/39 pass the P0 freeze gate. This protocol lock generated no P0.
""")
    write_text(OUT / "05_STAGE_A_LOCK/RHUH_FUTURE_BLIND_ACCESS_POLICY.md", """
# RHUH future-blind access policy

Before 39/39 P0 freeze, recurrence segmentation voxel arrays and any recurrence-derived target or performance are inaccessible. Only recurrence file identity, existence, SHA-256, and header-level geometry metadata may be known. No future voxel content may affect eligibility, preprocessing, checkpoint choice, parameters, or thresholds.
""")

    methods = {
        "Fixed": {"operation": "safe_clip_prob(P0)", "dtype": "float32"},
        "Naive": {"operation": "sigmoid(2.5 * safe_logit(Fixed))", "gamma": 2.5, "logit_epsilon": 1e-5, "logit_clip": [-30, 30]},
        "EIA-linear": {"alpha": 0.30, "beta": 0.30, "support_radius_voxels": 26, "target_signal_gaussian_sigma_voxels": 2.0},
        "EIA-blend-0.90": {"baseline_weight": 0.90, "target_signal_weight": 0.10},
        "EIA-blend-0.75": {"baseline_weight": 0.75, "target_signal_weight": 0.25},
        "Full PCC": {"rounds": 10, "eta": 0.30, "dilation_radius_voxels": 26, "gaussian_sigma_voxels": 2.0, "formal_final": "P10", "state_propagation": True, "dtype": "float32"},
        "No-smoothing PCC": {"rounds": 10, "eta": 0.30, "dilation_radius_voxels": 26, "smoothing": False, "sole_difference": "S_r = D_r", "formal_final": "P10", "dtype": "float32"},
    }
    stage_b = {
        "status": "LOCKED_NOT_EXECUTED", "prerequisite": "39/39 external P0 SHA-256 frozen",
        "target": "T = (future_mask > 0) AND NOT(current_mask > 0)", "target_dtype": "bool",
        "geometry_prerequisite": "locked effective physical voxel-grid identity", "methods": methods,
        "method_count": 7, "full_internal_ablation": "NOT_RUN",
        "RHUH_specific_parameter_tuning": "FORBIDDEN", "stage_b_executed_during_lock": False,
    }
    write_yaml(OUT / "06_STAGE_B_LOCK/LOCKED_RHUH_EXTERNAL_STAGE_B_PROTOCOL.yaml", stage_b)
    write_text(OUT / "06_STAGE_B_LOCK/LOCKED_RHUH_EXTERNAL_STAGE_B_PROTOCOL.md", """
# Locked RHUH External Stage B protocol

Only after 39/39 P0 SHA-256 freeze may recurrence segmentation arrays be read and `T=(future_mask>0) AND NOT(current_mask>0)` be constructed. The seven methods are Fixed, Naive, EIA-linear, EIA-blend-0.90, EIA-blend-0.75, Full PCC, and No-smoothing PCC. No full internal ablation is run.

Full PCC uses 10 rounds, eta 0.30, radius 26 voxels, sigma 2.0, propagated state, and formal P10 output. No-smoothing has the sole difference `S_r=D_r`. RHUH-specific tuning is forbidden. Stage B was not executed during this lock.
""")
    evaluation = {
        "primary_endpoint": "patient-level Dice at fixed threshold 0.5", "prediction_rule": "probability >= 0.5",
        "secondary": ["IoU@0.5", "precision@0.5", "recall@0.5", "soft Dice", "Brier score", "average precision / PR-AUC", "predicted positive volume"],
        "oracle_assisted": ["target-volume-matched top-k Dice", "target-volume-matched top-k IoU"],
        "oracle_label": "ORACLE_ASSISTED_RETROSPECTIVE_LOCALIZATION", "top_k_is_deployment_performance": False,
        "threshold_tuning_on_RHUH": "FORBIDDEN", "secondary_inferential_tests": "NOT_PRELOCKED_NOT_RUN",
    }
    write_yaml(OUT / "06_STAGE_B_LOCK/LOCKED_RHUH_EXTERNAL_EVALUATION_POLICY.yaml", evaluation)
    write_text(OUT / "06_STAGE_B_LOCK/LOCKED_RHUH_EXTERNAL_EVALUATION_POLICY.md", """
# Locked RHUH external evaluation policy

Primary endpoint is patient-level Dice at fixed threshold 0.5, with `probability >= 0.5`. Secondary metrics are IoU, precision, recall, soft Dice, Brier score, AP/PR-AUC, and predicted positive volume. Target-volume-matched top-k Dice/IoU are labeled `ORACLE_ASSISTED_RETROSPECTIVE_LOCALIZATION` and are not deployment performance. RHUH threshold tuning and unplanned secondary inference are forbidden.
""")

    stats = {
        "unit": "patient", "denominator": 39, "endpoint": "Dice@0.5",
        "confirmatory_family_exactly": ["Full PCC vs Fixed", "No-smoothing PCC vs Full PCC"],
        "test": "paired two-sided Wilcoxon signed-rank", "wilcoxon_zero_method": "wilcox",
        "holm_family_size": 2, "alpha": 0.05,
        "report": ["n", "mean paired difference", "median paired difference", "wins/ties/losses", "raw p", "Holm-adjusted p", "Cohen dz", "rank-biserial", "patient-level paired bootstrap 95% CI"],
        "cohen_dz": "mean paired difference / sample SD of paired differences",
        "rank_biserial": "(positive rank sum - negative rank sum)/(positive rank sum + negative rank sum), zeros excluded",
        "bootstrap": {"unit": "patient pair", "replicates": 10000, "seed": 20260810, "interval": "percentile 95%", "quantiles": [0.025, 0.975]},
        "result_driven_inferential_comparisons": "FORBIDDEN", "seed_change_after_results": "FORBIDDEN",
    }
    write_yaml(OUT / "07_STATISTICS_LOCK/LOCKED_RHUH_EXTERNAL_STATISTICAL_ANALYSIS_PLAN.yaml", stats)
    write_text(OUT / "07_STATISTICS_LOCK/LOCKED_RHUH_EXTERNAL_STATISTICAL_ANALYSIS_PLAN.md", """
# Locked RHUH external statistical analysis plan

Inference is patient-level. The confirmatory family contains exactly Full PCC vs Fixed and No-smoothing PCC vs Full PCC on Dice@0.5. Use paired two-sided Wilcoxon signed-rank (`zero_method=wilcox`), Holm over exactly two hypotheses, alpha 0.05, and report n, paired mean/median differences, wins/ties/losses, raw and adjusted p, Cohen dz, rank-biserial, and paired bootstrap 95% CI.

Bootstrap uses exactly 10,000 patient-pair replicates and seed **20260810**, locked before results. Result-driven comparisons or seed changes are forbidden.
""")

    failure = {
        "locked_denominator": 39, "all_patients_in_end_to_end_status": True,
        "failure_classes": ["geometry", "file access", "frozen predictor compatibility", "numeric failure", "target construction failure", "method failure"],
        "silent_deletion": "FORBIDDEN", "primary_analysis": "complete paired cases with n and reasons reported",
        "end_to_end_completion_rate_denominator": 39, "empty_target": "target construction failure; retain patient in end-to-end denominator",
        "non_finite": "numeric failure; no silent filtering", "cohort_or_parameter_change_to_fix_failure": "FORBIDDEN",
    }
    write_yaml(OUT / "08_FAILURE_LOCK/LOCKED_RHUH_EXTERNAL_FAILURE_POLICY.yaml", failure)
    write_text(OUT / "08_FAILURE_LOCK/LOCKED_RHUH_EXTERNAL_FAILURE_POLICY.md", """
# Locked RHUH external failure policy

The external denominator is 39 and every patient remains in end-to-end status. Geometry, file access, frozen predictor compatibility, numeric, target construction, and method failures must be explicit. Silent deletion is forbidden. Primary inference uses complete paired cases with count and reasons, while end-to-end completion is always reported over 39. Empty targets and non-finite outputs are failures, not metric imputations or grounds for silent removal.
""")
    write_text(OUT / "09_INTERPRETATION_BOUNDARY/LOCKED_RHUH_EXTERNAL_SCIENTIFIC_INTERPRETATION_BOUNDARY.md", """
# Locked scientific interpretation boundary

External Stage A evaluates cross-dataset transfer of a future-blind frozen predictor. External Stage B, only after P0 freeze, evaluates retrospective target-conditioned correction using the true future-change target. Stage B is not prospective recurrence forecasting, deployment-time future prediction, or clinical prediction without future access.

RHUH's missing independent resection-cavity label and the resulting non-perfect mask ontology equivalence are predeclared limitations.
""")

    protocol = {
        "task": "PCC_RHUH_EXTERNAL_VALIDATION_2026", "phase": "PHASE_1_FINAL_EXTERNAL_PROTOCOL_LOCK",
        "source_patients": 40, "excluded_pre_outcome": 1, "confirmatory_patients": 39,
        "excluded_patient": "RHUH-0008", "exclusion_code": "PRE_OUTCOME_GEOMETRY_INCOMPATIBILITY",
        "primary_pair": "early postoperative -> recurrence diagnosis follow-up",
        "geometry_policy": geometry_policy["policy_id"], "mask_mapping": "RHUH segmentation > 0 (labels 1|2|3)",
        "predictor": "frozen internal five-fold CrossCaseSmallUNet ensemble", "stage_a_future_blind": True,
        "stage_b_target": "(future_mask > 0) AND NOT(current_mask > 0)", "methods": list(methods),
        "primary_endpoint": evaluation["primary_endpoint"], "confirmatory_family": stats["confirmatory_family_exactly"],
        "bootstrap_replicates": 10000, "bootstrap_seed": 20260810, "failure_denominator": 39,
        "scientific_definitions_change_after_results": "FORBIDDEN",
    }
    write_yaml(OUT / "11_RELEASE/PCC_RHUH_EXTERNAL_PROTOCOL_LOCK_2026.yaml", protocol)
    write_text(OUT / "11_RELEASE/PCC_RHUH_EXTERNAL_PROTOCOL_LOCK_2026.md", """
# PCC RHUH External Protocol Lock 2026

The official 40-patient RHUH inventory is retained. RHUH-0008 was excluded for pre-outcome geometry incompatibility, leaving exactly 39 early-postoperative→recurrence pairs. Effective geometry identity, all-nonbackground RHUH mask mapping, the frozen five-fold predictor, future-blind Stage A, seven-method retrospective Stage B, threshold 0.5, exactly two confirmatory comparisons, bootstrap seed 20260810, and denominator 39 are now immutable.

No external P0, predictor forward, recurrence segmentation voxel-array access, target, method, or performance result was generated or accessed during this lock.
""")
    status = {
        "source_patients": 40, "excluded_pre_outcome": 1, "confirmatory_patients": 39,
        "excluded_patient": "RHUH-0008", "exclusion_code": "PRE_OUTCOME_GEOMETRY_INCOMPATIBILITY",
        "external_p0_generated": False, "predictor_forward_executed": False,
        "future_voxel_outcome_accessed": False, "recurrence_segmentation_voxel_arrays_read": False,
        "target_constructed": False, "performance_computed": False, "stage_b_executed": False,
        "RHUH_training": False, "fine_tuning": False, "calibration": False, "test_time_adaptation": False,
        "protocol_locked": True, "lumiere_started": False, "PROTOCOL_LOCK_GATE": "PENDING_TESTS",
        "RHUH_EXTERNAL_PRE_OUTCOME_PROTOCOL_COMMIT": "RECORDED_AFTER_SELF_REFERENTIAL_GIT_COMMIT",
    }
    write_json(OUT / "11_RELEASE/PCC_RHUH_EXTERNAL_PROTOCOL_STATUS.json", status)

    test_source = r'''from pathlib import Path
import csv, json, hashlib, yaml

ROOT=Path(__file__).resolve().parents[1]
def rows(rel):
    with (ROOT/rel).open(newline="",encoding="utf-8") as f: return list(csv.DictReader(f))
def y(rel): return yaml.safe_load((ROOT/rel).read_text())
def j(rel): return json.loads((ROOT/rel).read_text())

def test_01_cohort_39(): assert len(rows("01_COHORT_LOCK/LOCKED_RHUH_39_EXTERNAL_CONFIRMATORY_CASE_MANIFEST.csv"))==39
def test_02_unique_patients_39(): assert len({r["patient_id"] for r in rows("01_COHORT_LOCK/LOCKED_RHUH_39_EXTERNAL_CONFIRMATORY_CASE_MANIFEST.csv")})==39
def test_03_unique_pairs_39(): assert len({r["case_id"] for r in rows("01_COHORT_LOCK/LOCKED_RHUH_39_EXTERNAL_CONFIRMATORY_CASE_MANIFEST.csv")})==39
def test_04_only_0008_excluded(): assert [r["patient_id"] for r in rows("01_COHORT_LOCK/EXCLUDED_RHUH_EXTERNAL_CASES.csv")]==["RHUH-0008"]
def test_05_exclusion_pre_outcome():
    r=rows("01_COHORT_LOCK/EXCLUDED_RHUH_EXTERNAL_CASES.csv")[0]; assert r["external_p0_seen_before_exclusion"]==r["target_constructed_before_exclusion"]==r["performance_seen_before_exclusion"]=="false"
def test_06_original_audit_40(): assert len(rows("01_COHORT_LOCK/RHUH_40_TO_39_COHORT_AUDIT.csv"))==40
def test_07_geometry_39(): assert len(rows("02_GEOMETRY_LOCK/LOCKED_RHUH_39_GEOMETRY_MANIFEST.csv"))==39
def test_08_geometry_all_valid(): assert all(r["effective_geometry_valid"]=="true" for r in rows("02_GEOMETRY_LOCK/LOCKED_RHUH_39_GEOMETRY_MANIFEST.csv"))
def test_09_geometry_forbids_transforms(): assert set(y("02_GEOMETRY_LOCK/LOCKED_RHUH_EXTERNAL_GEOMETRY_POLICY.yaml")["forbidden"])=={"registration","resampling","interpolation","case-specific affine repair","header rewriting to force alignment","outcome-driven geometry correction"}
def test_10_mask_mapping(): assert y("03_MASK_LOCK/LOCKED_RHUH_EXTERNAL_MASK_MAPPING.yaml")["RHUH_expression"]=="segmentation > 0"
def test_11_mask_labels(): assert y("03_MASK_LOCK/LOCKED_RHUH_EXTERNAL_MASK_MAPPING.yaml")["RHUH_labels"]=={1:"necrosis",2:"peritumoral / non-enhancing abnormality",3:"enhancing tumor"}
def test_12_checkpoints_5_match():
    r=rows("04_PREDICTOR_LOCK/LOCKED_RHUH_FROZEN_PREDICTOR_MANIFEST.csv"); assert len(r)==5 and all(x["hash_status"]=="MATCH" for x in r)
def test_13_no_training_or_finetuning():
    s=j("11_RELEASE/PCC_RHUH_EXTERNAL_PROTOCOL_STATUS.json"); assert not s["RHUH_training"] and not s["fine_tuning"]
def test_14_no_p0_or_forward():
    s=j("11_RELEASE/PCC_RHUH_EXTERNAL_PROTOCOL_STATUS.json"); assert not s["external_p0_generated"] and not s["predictor_forward_executed"]
def test_15_no_future_voxel_access(): assert not j("11_RELEASE/PCC_RHUH_EXTERNAL_PROTOCOL_STATUS.json")["recurrence_segmentation_voxel_arrays_read"]
def test_16_no_target_or_performance():
    s=j("11_RELEASE/PCC_RHUH_EXTERNAL_PROTOCOL_STATUS.json"); assert not s["target_constructed"] and not s["performance_computed"] and not s["stage_b_executed"]
def test_17_seven_methods(): assert len(y("06_STAGE_B_LOCK/LOCKED_RHUH_EXTERNAL_STAGE_B_PROTOCOL.yaml")["methods"])==7
def test_18_full_pcc_p10(): assert y("06_STAGE_B_LOCK/LOCKED_RHUH_EXTERNAL_STAGE_B_PROTOCOL.yaml")["methods"]["Full PCC"]["formal_final"]=="P10"
def test_19_threshold_point5(): assert y("06_STAGE_B_LOCK/LOCKED_RHUH_EXTERNAL_EVALUATION_POLICY.yaml")["prediction_rule"]=="probability >= 0.5"
def test_20_exactly_two_confirmatory(): assert len(y("07_STATISTICS_LOCK/LOCKED_RHUH_EXTERNAL_STATISTICAL_ANALYSIS_PLAN.yaml")["confirmatory_family_exactly"])==2
def test_21_bootstrap_10000(): assert y("07_STATISTICS_LOCK/LOCKED_RHUH_EXTERNAL_STATISTICAL_ANALYSIS_PLAN.yaml")["bootstrap"]["replicates"]==10000
def test_22_bootstrap_seed(): assert y("07_STATISTICS_LOCK/LOCKED_RHUH_EXTERNAL_STATISTICAL_ANALYSIS_PLAN.yaml")["bootstrap"]["seed"]==20260810
def test_23_failure_denominator_39(): assert y("08_FAILURE_LOCK/LOCKED_RHUH_EXTERNAL_FAILURE_POLICY.yaml")["locked_denominator"]==39
def test_24_no_lumiere(): assert not j("11_RELEASE/PCC_RHUH_EXTERNAL_PROTOCOL_STATUS.json")["lumiere_started"]
'''
    write_text(OUT / "10_TESTS/test_rhuh_external_protocol_lock.py", test_source)
    test_env = dict(os.environ)
    test_env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", str(OUT / "10_TESTS/test_rhuh_external_protocol_lock.py")], cwd=REPO, env=test_env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    write_text(OUT / "10_TESTS/FULL_TEST_STDOUT.txt", proc.stdout)
    write_text(OUT / "10_TESTS/FULL_TEST_STDERR.txt", proc.stderr)
    write_text(OUT / "10_TESTS/TEST_EXIT_CODE.txt", str(proc.returncode))
    if proc.returncode != 0 or "24 passed" not in proc.stdout:
        status["PROTOCOL_LOCK_GATE"] = "BLOCKED"
        write_json(OUT / "11_RELEASE/PCC_RHUH_EXTERNAL_PROTOCOL_STATUS.json", status)
        raise RuntimeError(f"Protocol tests failed: exit={proc.returncode}")
    status["PROTOCOL_LOCK_GATE"] = "PASS"
    write_json(OUT / "11_RELEASE/PCC_RHUH_EXTERNAL_PROTOCOL_STATUS.json", status)
    write_text(OUT / "10_TESTS/PROTOCOL_LOCK_TEST_REPORT.md", """
# RHUH external protocol-lock tests

Command: `python -m pytest -q outputs/pcc_rhuh_external_protocol_lock_2026/10_TESTS/test_rhuh_external_protocol_lock.py`

Result: **24 passed, 0 failed, 0 errors, exit code 0**. Tests are static metadata/hash checks only; they do not load NIfTI arrays, checkpoints, models, P0, targets, or performance results.
""")

    write_text(OUT / "11_RELEASE/PCC_RHUH_EXTERNAL_PROTOCOL_FINAL_REPORT.md", """
# PCC RHUH external protocol final report

The final 39-patient RHUH external protocol is locked before outcome access. Only RHUH-0008 is excluded, for pre-outcome geometry incompatibility. Geometry, mask semantics, frozen predictor identity, Stage A future-blind boundary, seven-method Stage B, endpoints, exactly two confirmatory comparisons, bootstrap seed 20260810, and failure denominator 39 are fixed. Protocol tests: 24 passed.

No external P0, predictor forward, recurrence segmentation voxel-array access, target construction, method execution, performance computation, RHUH training, fine-tuning, or LUMIERE occurred.
""")
    finalize_metadata(protocol_commit=None)


def finalize_metadata(protocol_commit: str | None) -> None:
    record = OUT / "11_RELEASE/RHUH_EXTERNAL_PRE_OUTCOME_PROTOCOL_COMMIT.txt"
    if protocol_commit:
        write_text(record, f"RHUH_EXTERNAL_PRE_OUTCOME_PROTOCOL_COMMIT={protocol_commit}")
    hash_lock_path = OUT / "11_RELEASE/PCC_RHUH_EXTERNAL_PROTOCOL_HASH_LOCK.json"
    file_manifest_path = OUT / "11_RELEASE/PCC_RHUH_EXTERNAL_PROTOCOL_FILE_MANIFEST.csv"
    contents_path = OUT / "11_RELEASE/PCC_RHUH_EXTERNAL_PROTOCOL_PACKAGE_CONTENTS.txt"
    for p in (hash_lock_path, file_manifest_path, contents_path):
        if p.exists():
            p.unlink()
    controlled = sorted(p for p in OUT.rglob("*") if p.is_file())
    key_names = {
        "LOCKED_RHUH_39_EXTERNAL_CONFIRMATORY_CASE_MANIFEST.csv", "LOCKED_RHUH_39_EXTERNAL_PATIENT_IDS.csv", "EXCLUDED_RHUH_EXTERNAL_CASES.csv",
        "LOCKED_RHUH_EXTERNAL_GEOMETRY_POLICY.yaml", "LOCKED_RHUH_39_GEOMETRY_MANIFEST.csv", "LOCKED_RHUH_EXTERNAL_MASK_MAPPING.yaml",
        "LOCKED_RHUH_FROZEN_PREDICTOR_MANIFEST.csv", "LOCKED_RHUH_FROZEN_PREDICTOR_POLICY.yaml", "LOCKED_RHUH_EXTERNAL_STAGE_A_P0_PROTOCOL.yaml",
        "LOCKED_RHUH_EXTERNAL_STAGE_B_PROTOCOL.yaml", "LOCKED_RHUH_EXTERNAL_EVALUATION_POLICY.yaml", "LOCKED_RHUH_EXTERNAL_STATISTICAL_ANALYSIS_PLAN.yaml",
        "LOCKED_RHUH_EXTERNAL_FAILURE_POLICY.yaml", "PCC_RHUH_EXTERNAL_PROTOCOL_LOCK_2026.yaml", "PCC_RHUH_EXTERNAL_PROTOCOL_STATUS.json",
        "FULL_TEST_STDOUT.txt", "TEST_EXIT_CODE.txt", "GENERATE_RHUH_EXTERNAL_PROTOCOL_LOCK.py", "RHUH_EXTERNAL_PRE_OUTCOME_PROTOCOL_COMMIT.txt",
    }
    lock = {
        "algorithm": "SHA-256", "canonical_path_base": "outputs/pcc_rhuh_external_protocol_lock_2026",
        "protocol_commit": protocol_commit or "PENDING_SELF_REFERENTIAL_GIT_COMMIT",
        "files": [{"path": str(p.relative_to(OUT)), "size_bytes": p.stat().st_size, "sha256": sha256(p)} for p in controlled if p.name in key_names],
    }
    write_json(hash_lock_path, lock)
    before_manifest = sorted(p for p in OUT.rglob("*") if p.is_file())
    rows = [{"relative_path": str(p.relative_to(OUT)), "size_bytes": p.stat().st_size, "sha256": sha256(p), "control_status": "CONTROLLED"} for p in before_manifest]
    rows += [
        {"relative_path": str(file_manifest_path.relative_to(OUT)), "size_bytes": "", "sha256": "", "control_status": "EXCLUDED_SELF_REFERENCE"},
        {"relative_path": str(contents_path.relative_to(OUT)), "size_bytes": "", "sha256": "", "control_status": "EXCLUDED_SELF_REFERENCE"},
    ]
    write_csv(file_manifest_path, rows)
    final_files = sorted([*before_manifest, file_manifest_path, contents_path], key=lambda p: str(p.relative_to(OUT)))
    write_text(contents_path, "\n".join(str(p.relative_to(OUT)) for p in final_files))
    for p in (ZIP, ZIP_SHA, SUMMARY):
        if p.exists():
            p.unlink()
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(p for p in OUT.rglob("*") if p.is_file()):
            z.write(p, str(p.relative_to(OUT)))
    digest = sha256(ZIP)
    write_text(ZIP_SHA, f"{digest}  {ZIP.name}")
    with zipfile.ZipFile(ZIP) as z:
        names = z.namelist(); bad = z.testzip()
    expected = [str(p.relative_to(OUT)) for p in sorted(p for p in OUT.rglob("*") if p.is_file())]
    ok = bad is None and names == expected and len(names) == len(set(names))
    status = json.loads((OUT / "11_RELEASE/PCC_RHUH_EXTERNAL_PROTOCOL_STATUS.json").read_text())
    write_text(SUMMARY, f"""
PCC_RHUH_EXTERNAL_VALIDATION_2026
PHASE=1_FINAL_EXTERNAL_PROTOCOL_LOCK
SOURCE_PATIENTS=40
EXCLUDED_PRE_OUTCOME=1
EXCLUDED_PATIENT=RHUH-0008
EXCLUSION_CODE=PRE_OUTCOME_GEOMETRY_INCOMPATIBILITY
CONFIRMATORY_PATIENTS=39
GEOMETRY_VALID=39/39
CHECKPOINT_HASHES=MATCH_5/5
METHODS_LOCKED=7
PRIMARY_THRESHOLD=0.5
CONFIRMATORY_TESTS=2
BOOTSTRAP_REPLICATES=10000
BOOTSTRAP_SEED=20260810
FAILURE_DENOMINATOR=39
PROTOCOL_TESTS=24_passed_0_failed_0_errors
EXTERNAL_P0_GENERATED=false
PREDICTOR_FORWARD_EXECUTED=false
FUTURE_SEGMENTATION_VOXEL_ARRAYS_READ=false
TARGET_CONSTRUCTED=false
PERFORMANCE_COMPUTED=false
STAGE_B_EXECUTED=false
RHUH_TRAINING=false
FINE_TUNING=false
LUMIERE=false
RHUH_EXTERNAL_PRE_OUTCOME_PROTOCOL_COMMIT={protocol_commit or 'PENDING_SELF_REFERENTIAL_GIT_COMMIT'}
ZIP_FILES={len(names)}
ZIP_SIZE_BYTES={ZIP.stat().st_size}
ZIP_SHA256={digest}
PACKAGE_INTEGRITY={'PASS' if ok else 'FAIL'}
PROTOCOL_LOCK_GATE={status['PROTOCOL_LOCK_GATE']}
""")
    if not ok:
        raise RuntimeError("Protocol ZIP validation failed")
    print(json.dumps({"protocol_commit": protocol_commit, "zip": str(ZIP), "zip_sha256": digest, "zip_size": ZIP.stat().st_size, "zip_files": len(names), "package_integrity": "PASS", "gate": status["PROTOCOL_LOCK_GATE"]}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--finalize-commit")
    args = parser.parse_args()
    if args.finalize_commit:
        if not OUT.exists():
            raise RuntimeError("Cannot finalize missing protocol output")
        finalize_metadata(args.finalize_commit)
    else:
        build_initial()


if __name__ == "__main__":
    main()
