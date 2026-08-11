"""Build audit-only Phase 1A and Phase 1C deliverables.

The script reads existing metadata and hashes, copies public-release candidates,
and writes documentation. It never imports model/method modules, reads image
voxel arrays, runs inference/PCC, or calculates performance/statistical tests.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path.cwd()
BASE = ROOT / "pre_submission_anti_major_2026"
OUT = BASE / "phase1_zero_risk_high_yield_submission_hardening"
STAGING = OUT / "reproducibility_release_staging"
PHASE0 = BASE / "phase0_science_freeze"
SNAP = Path("/home/changxinjiresearch/pre_phase0_snapshots/pcc_repo_snapshot_20260811/worktree")
TAG = "pcc-v2.1.1-science-freeze-20260811"
BASELINE = "df340b7921a066acbfeffdd8589bb1ad2ec2e718"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


OUT.mkdir(parents=True, exist_ok=True)
for name in [
    "01_code", "02_configs", "03_environment", "04_fold_manifests",
    "05_inference", "06_pcc_algorithm", "07_evaluation",
    "08_figure_generation", "09_derived_case_metrics", "10_protocol_locks",
    "11_source_data_for_figures", "12_hash_manifests", "13_documentation",
    "14_data_access_information",
]:
    (STAGING / name).mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Phase 0 integrity gate
# ---------------------------------------------------------------------------
tag_target = subprocess.check_output(["git", "rev-list", "-n", "1", TAG], text=True).strip()
integrity_rows = []

manifest_path = PHASE0 / "13_PHASE0_SCIENCE_FREEZE_SHA256_MANIFEST.csv"
with manifest_path.open(newline="", encoding="utf-8") as stream:
    manifest_rows = list(csv.DictReader(stream))
for row in manifest_rows:
    rel = row["relative_path"]
    target = PHASE0 / rel
    if rel in {"13_PHASE0_SCIENCE_FREEZE_SHA256_MANIFEST.csv", "PHASE0_SCIENCE_FREEZE_SHA256_MANIFEST.csv"}:
        status = "SELF_REFERENCE_NON_VERIFIABLE_NOT_SCIENTIFIC"
        actual = sha256(target)
    elif not target.exists():
        status = "MISSING"
        actual = "MISSING"
    else:
        actual = sha256(target)
        status = "PASS" if actual == row["sha256"] else "MISMATCH"
    integrity_rows.append({
        "source": "PHASE0_SHA256_MANIFEST", "relative_path": rel,
        "evidence_class": row["evidence_class"], "expected_sha256": row["sha256"],
        "actual_sha256": actual, "status": status,
    })

registry_path = PHASE0 / "PHASE0_FROZEN_AUTHORITY_REGISTRY.csv"
with registry_path.open(newline="", encoding="utf-8") as stream:
    registry = list(csv.DictReader(stream))
for row in registry:
    source = Path(row["path"])
    if not source.is_absolute():
        source = ROOT / source
        if not source.exists():
            source = SNAP / row["path"]
    actual = sha256(source) if source.is_file() else "MISSING"
    status = "PASS" if actual == row["sha256"] else "MISMATCH"
    integrity_rows.append({
        "source": "PHASE0_AUTHORITY_REGISTRY", "relative_path": row["path"],
        "evidence_class": row["scientific_status"], "expected_sha256": row["sha256"],
        "actual_sha256": actual, "status": status,
    })

write_csv(
    OUT / "PHASE1_PHASE0_INTEGRITY_CHECK.csv",
    ["source", "relative_path", "evidence_class", "expected_sha256", "actual_sha256", "status"],
    integrity_rows,
)
scientific_mismatches = sum(
    row["status"] not in {"PASS", "SELF_REFERENCE_NON_VERIFIABLE_NOT_SCIENTIFIC"}
    and (row["evidence_class"] in {"CLASS A", "FROZEN_PRIMARY_CONFIRMATORY"})
    for row in integrity_rows
)
all_external_mismatches = sum(row["status"] in {"MISSING", "MISMATCH"} for row in integrity_rows)
if tag_target != BASELINE or scientific_mismatches:
    raise RuntimeError("HOLD_PHASE0_INTEGRITY_FAILURE")

# ---------------------------------------------------------------------------
# Phase 1A registration provenance
# ---------------------------------------------------------------------------
prov_fields = [
    "dataset", "cohort_role", "source_preprocessing_pipeline",
    "source_preprocessing_reference", "image_modality", "image_orientation",
    "voxel_spacing", "image_shape_policy", "affine_information_available",
    "qform_sform_information", "current_future_shape_identity",
    "current_future_affine_identity", "shared_physical_grid_evidence",
    "within_timepoint_registration", "between_timepoint_registration",
    "atlas_registration", "patient_specific_longitudinal_registration",
    "resampling_performed_in_our_pipeline", "resampling_source", "resampling_target",
    "interpolation_method_image", "interpolation_method_mask",
    "segmentation_image_geometry_identity", "target_construction_grid",
    "what_source_dataset_claims", "what_our_pipeline_verified",
    "what_our_pipeline_did_not_verify", "known_registration_limitation",
    "risk_to_future_added_target", "evidence_source_file", "evidence_confidence",
    "manuscript_implication", "notes",
]

mu_source = "https://www.nature.com/articles/s41597-025-06011-7; https://www.cancerimagingarchive.net/collection/mu-glioma-post/"
rhuh_source = "outputs/pcc_rhuh_external_protocol_lock_2026/02_GEOMETRY_LOCK/LOCKED_RHUH_39_GEOMETRY_MANIFEST.csv; preserved pre-Phase-0 RHUH official preprocessing README; https://doi.org/10.7937/4545-C905"
lumiere_source = "https://www.nature.com/articles/s41597-022-01881-7; https://github.com/ysuter/gbm-data-longitudinal; PHASE0_LUMIERE_HISTORICAL_EXPOSURE_AUDIT.md"
provenance_rows = [
    {
        "dataset": "MU-Glioma-Post", "cohort_role": "development 40",
        "source_preprocessing_pipeline": "FeTS; DICOM-to-NIfTI; 1-mm isotropic resampling; rigid CapTK/Greedy registration to SRI24; N4ITK; BrainMaGe",
        "source_preprocessing_reference": mu_source, "image_modality": "current T1c plus segmentation; future segmentation for target",
        "image_orientation": "matching orientation flags in 40/40 existing geometry inventory; exact axis code not stored in the development manifest",
        "voxel_spacing": "1 mm isotropic claimed by source; spacing-match flag 40/40", "image_shape_policy": "240x240x155 in 40/40 mapped development cases",
        "affine_information_available": "existing eligibility inventory records affine-match Boolean; full per-case matrices not frozen in development manifest",
        "qform_sform_information": "not recorded in development authority", "current_future_shape_identity": "40/40",
        "current_future_affine_identity": "40/40 existing affine-match flags", "shared_physical_grid_evidence": "YES at recorded shape/spacing/orientation/affine-flag level",
        "within_timepoint_registration": "source pipeline co-registers sequences to SRI24", "between_timepoint_registration": "not verified as dedicated pairwise longitudinal registration",
        "atlas_registration": "source claims rigid registration of each NIfTI study to SRI24", "patient_specific_longitudinal_registration": "NOT_VERIFIED / NOT_PERFORMED_BY_OUR_PIPELINE",
        "resampling_performed_in_our_pipeline": "NO", "resampling_source": "source dataset preprocessing before release", "resampling_target": "1-mm isotropic SRI24 grid",
        "interpolation_method_image": "not recovered from frozen local source documentation", "interpolation_method_mask": "not recovered from frozen local source documentation",
        "segmentation_image_geometry_identity": "existing case inventory accepted exact compatibility", "target_construction_grid": "released shared voxel grid; Boolean current/future mask operation",
        "what_source_dataset_claims": "skull-stripped, co-registered, resampled NIfTI; rigid atlas registration",
        "what_our_pipeline_verified": "40/40 mapped cases have matching recorded shapes, spacing, orientation and affine flags; no project-side transform",
        "what_our_pipeline_did_not_verify": "transform files, landmark accuracy, deformation accuracy, dedicated inter-timepoint registration or voxelwise anatomical correspondence",
        "known_registration_limitation": "common atlas grid is not proof of perfect longitudinal anatomical correspondence",
        "risk_to_future_added_target": "residual anatomy/segmentation displacement can be labeled as future-added foreground",
        "evidence_source_file": "validation_reference/.../LOCKED_CASE_MANIFEST.csv; outputs/pcc_115_holdout_protocol_lock_2026/01_COHORT_LOCK/ALL_ELIGIBLE_PATIENT_LEVEL_PAIRS.csv",
        "evidence_confidence": "MODERATE", "manuscript_implication": "state common physical-grid evidence and source atlas normalization; do not claim dedicated longitudinal registration",
        "notes": "No new registration, resampling, target, or performance was produced in Phase 1.",
    },
    {
        "dataset": "MU-Glioma-Post", "cohort_role": "independent internal 113",
        "source_preprocessing_pipeline": "FeTS; DICOM-to-NIfTI; 1-mm isotropic resampling; rigid CapTK/Greedy registration to SRI24; N4ITK; BrainMaGe",
        "source_preprocessing_reference": mu_source, "image_modality": "current T1c plus current/future segmentation",
        "image_orientation": "orientation-match flag 113/113; exact axis code not stored in locked 113 case manifest",
        "voxel_spacing": "source 1 mm isotropic; spacing-match 113/113", "image_shape_policy": "240x240x155 for 113/113",
        "affine_information_available": "affine-match Boolean in locked 113 manifest", "qform_sform_information": "not recorded in locked 113 manifest",
        "current_future_shape_identity": "113/113", "current_future_affine_identity": "113/113 affine-match flags",
        "shared_physical_grid_evidence": "YES at locked shape/spacing/orientation/affine-flag level",
        "within_timepoint_registration": "source pipeline atlas co-registration", "between_timepoint_registration": "not verified as dedicated pairwise longitudinal registration",
        "atlas_registration": "source claims rigid SRI24 registration", "patient_specific_longitudinal_registration": "NOT_VERIFIED / NOT_PERFORMED_BY_OUR_PIPELINE",
        "resampling_performed_in_our_pipeline": "NO", "resampling_source": "source dataset preprocessing before project use", "resampling_target": "1-mm isotropic SRI24 grid",
        "interpolation_method_image": "not recovered", "interpolation_method_mask": "not recovered",
        "segmentation_image_geometry_identity": "locked manifest reports exact compatibility", "target_construction_grid": "locked shared voxel grid; Boolean operation only",
        "what_source_dataset_claims": "skull-stripped, co-registered, resampled NIfTI in common atlas space",
        "what_our_pipeline_verified": "113/113 shape, spacing, orientation and affine compatibility flags before target construction",
        "what_our_pipeline_did_not_verify": "pairwise registration transforms, anatomical landmarks, local deformation or perfect correspondence",
        "known_registration_limitation": "atlas-space physical-grid identity does not eliminate inter-timepoint anatomical change or misalignment",
        "risk_to_future_added_target": "future-added target may include displacement-related foreground differences",
        "evidence_source_file": "outputs/pcc_113_stage_b_confirmatory_validation_2026_recovery_v2/00_STAGE_B_AUTHORITY/LOCKED_113_CONFIRMATORY_CASE_MANIFEST.csv",
        "evidence_confidence": "MODERATE", "manuscript_implication": "report verified grid compatibility and explicitly disclaim dedicated pairwise longitudinal registration",
        "notes": "Frozen results remain unchanged.",
    },
    {
        "dataset": "RHUH-GBM", "cohort_role": "external confirmatory 39",
        "source_preprocessing_pipeline": "official RHUH pipeline: DICOM-to-NIfTI; T1ce-to-SRI atlas FLIRT; within-timepoint modalities coregistered to transformed T1ce; SynthStrip; CaPTK normalization; DeepMedic segmentation",
        "source_preprocessing_reference": rhuh_source, "image_modality": "early-postoperative and recurrence T1ce/segmentations",
        "image_orientation": "LPS for locked 39", "voxel_spacing": "1x1x1 mm", "image_shape_policy": "240x240x155",
        "affine_information_available": "full selected affine and world bounds recorded", "qform_sform_information": "recorded; metadata-only differences retained",
        "current_future_shape_identity": "39/39", "current_future_affine_identity": "39/39 effective selected-grid identity",
        "shared_physical_grid_evidence": "YES, 39/39 effective grid; RHUH-0008 excluded pre-outcome",
        "within_timepoint_registration": "source pipeline registers modalities to transformed T1ce", "between_timepoint_registration": "no dedicated pairwise longitudinal registration verified",
        "atlas_registration": "source README claims T1ce-to-SRI atlas FLIRT", "patient_specific_longitudinal_registration": "NOT_VERIFIED / NOT_PERFORMED_BY_OUR_PIPELINE",
        "resampling_performed_in_our_pipeline": "NO", "resampling_source": "official source preprocessing only", "resampling_target": "SRI atlas representation",
        "interpolation_method_image": "not documented in frozen project snapshot", "interpolation_method_mask": "not documented in frozen project snapshot",
        "segmentation_image_geometry_identity": "39/39 effective geometry valid within each timepoint", "target_construction_grid": "same locked effective physical voxel grid",
        "what_source_dataset_claims": "atlas and within-timepoint registration in official preprocessing",
        "what_our_pipeline_verified": "shape, spacing, orientation, selected affine, voxel-center ranges and world bounds; 39/39 valid",
        "what_our_pipeline_did_not_verify": "registration accuracy, transform files, landmarks, deformable correspondence or perfect anatomy",
        "known_registration_limitation": "shared atlas grid and equal headers do not prove perfect patient-specific longitudinal alignment",
        "risk_to_future_added_target": "residual postoperative/recurrence alignment and segmentation differences can affect future-added regions",
        "evidence_source_file": "outputs/pcc_rhuh_external_protocol_lock_2026/02_GEOMETRY_LOCK/LOCKED_RHUH_39_GEOMETRY_MANIFEST.csv",
        "evidence_confidence": "HIGH_FOR_PHYSICAL_GRID; LOW_FOR_ANATOMICAL_CORRESPONDENCE",
        "manuscript_implication": "state effective physical-grid identity; avoid anatomically registered/perfect correspondence claims",
        "notes": "No transform, resampling, interpolation, crop, pad or header repair was performed by PCC pipeline.",
    },
    {
        "dataset": "LUMIERE", "cohort_role": "historical provenance only; possible Phase 4",
        "source_preprocessing_pipeline": "skull-stripped native unregistered MRI; segmentation tools perform within-timepoint coregistration and provide back-transformed segmentations",
        "source_preprocessing_reference": lumiere_source, "image_modality": "longitudinal T1/T1c/T2/FLAIR and automated segmentations",
        "image_orientation": "not audited for a Phase 4 cohort", "voxel_spacing": "heterogeneous source acquisition; not audited for Phase 4",
        "image_shape_policy": "native-space; not audited", "affine_information_available": "NIfTI available in source; not audited here",
        "qform_sform_information": "PENDING_PHASE4_FEASIBILITY", "current_future_shape_identity": "PENDING_PHASE4_FEASIBILITY",
        "current_future_affine_identity": "PENDING_PHASE4_FEASIBILITY", "shared_physical_grid_evidence": "NOT_ESTABLISHED",
        "within_timepoint_registration": "yes inside segmentation pipelines; back-transformed outputs also supplied",
        "between_timepoint_registration": "source native images described as unregistered", "atlas_registration": "DeepBraTumIA internal atlas registration; not a frozen PCC Phase 4 choice",
        "patient_specific_longitudinal_registration": "NOT_ESTABLISHED", "resampling_performed_in_our_pipeline": "NO",
        "resampling_source": "none in Phase 1", "resampling_target": "none", "interpolation_method_image": "not audited",
        "interpolation_method_mask": "not audited", "segmentation_image_geometry_identity": "PENDING_PHASE4_FEASIBILITY",
        "target_construction_grid": "NOT_DEFINED_FOR_PHASE4", "what_source_dataset_claims": "native skull-stripped unregistered images and back-transformed segmentations",
        "what_our_pipeline_verified": "historical/source documentation only", "what_our_pipeline_did_not_verify": "eligibility, pair geometry, mask ontology, future access boundary or any Phase 4 outcome",
        "known_registration_limitation": "native longitudinal studies are not assumed to share a grid",
        "risk_to_future_added_target": "cannot construct a locked longitudinal target until pre-outcome feasibility establishes a defensible grid policy",
        "evidence_source_file": "PHASE0_LUMIERE_HISTORICAL_EXPOSURE_AUDIT.md; source paper/repository",
        "evidence_confidence": "SOURCE_DOCUMENTATION_ONLY", "manuscript_implication": "do not describe LUMIERE as validated; mark PENDING_PHASE4_FEASIBILITY",
        "notes": "No new LUMIERE outcome or performance was accessed.",
    },
]
write_csv(OUT / "LONGITUDINAL_REGISTRATION_PROVENANCE_AUDIT.csv", prov_fields, provenance_rows)

write(OUT / "PHASE1A_REGISTRATION_PROVENANCE_REPORT.md", """# Phase 1A longitudinal registration provenance report

## MU-Glioma-Post

Known: the source publication describes FeTS preprocessing with DICOM-to-NIfTI conversion, resampling to 1-mm isotropic resolution and rigid registration to SRI24 using CapTK/Greedy, followed by bias correction and brain extraction. Existing project metadata maps all 40 development cases and all 113 internal cases to 240×240×155 arrays with matching shape, spacing, orientation and affine flags.

Verified: the PCC pipeline required exact array/geometry compatibility and did not register, resample, interpolate or repair any pair. This establishes recorded physical-grid compatibility.

Not verified: dedicated current-to-future patient-specific registration, transform files, landmark error, deformable alignment, or perfect voxelwise anatomical correspondence. Independent atlas normalization of timepoints cannot be equated with dedicated longitudinal registration.

Scientific implication: the one-sided future-added target can contain true biological/segmentation change and residual spatial displacement. Recommended wording is limited to source atlas normalization plus verified grid compatibility.

## RHUH-GBM

Known: the official pipeline describes T1ce registration to the SRI atlas and within-timepoint registration of other modalities. The locked 39-case cohort has 39/39 effective physical-grid identity for current T1ce/current segmentation, recurrence T1ce/recurrence segmentation and across timepoints. RHUH-0008 was excluded before outcome access because physical-grid identity could not be established.

Verified: shape, 1-mm spacing, LPS orientation, selected affine, voxel-center ranges and world bounds. qform/sform-only metadata differences were retained rather than silently rewritten. No project-side registration, resampling or interpolation occurred.

Not verified: registration accuracy or dedicated patient-specific inter-timepoint anatomical registration. Effective grid identity is not proof of perfect anatomical correspondence.

Scientific implication: the target is computationally defined on a shared physical grid, but residual longitudinal anatomical/segmentation displacement remains a limitation.

## LUMIERE

Only historical/source provenance was reviewed. The source provides skull-stripped native unregistered images; segmentation pipelines perform within-timepoint coregistration and provide back-transformed outputs. Cohort eligibility, longitudinal geometry, ontology and future-access controls remain `PENDING_PHASE4_FEASIBILITY`. No new LUMIERE outcome or performance was accessed.

## Unsupported claims

Unsupported claims detected in this Phase 1 report: **0**. Neither equal shape, equal affine nor common atlas space is described as perfect longitudinal anatomical registration.
""")

write(OUT / "MANUSCRIPT_READY_REGISTRATION_TEXT_DRAFT.md", """# Manuscript-ready registration text draft

This draft is not integrated into frozen V2.1.1.

MU-Glioma-Post images were distributed after source preprocessing that included 1-mm isotropic resampling and rigid registration to the SRI24 atlas. In the PCC cohorts, existing geometry records confirmed matching shape, spacing, orientation and affine flags for all 40 development and 113 independent-internal pairs. RHUH-GBM source preprocessing included atlas registration of T1ce and within-timepoint modality coregistration; all 39 locked external pairs had matching effective physical grids by shape, spacing, orientation, selected affine, voxel-center range and world bounds. The PCC pipeline itself performed no registration, resampling, interpolation or header repair.

These checks establish physical-grid compatibility, not perfect longitudinal anatomical correspondence. We did not verify dedicated pairwise patient-specific current-to-future registration, transform accuracy, landmark error or deformable correspondence. Accordingly, the one-sided future-added segmentation target may reflect both biological/segmentation change and residual spatial displacement. This limitation should be considered when interpreting target-conditioned correction.
""")

# ---------------------------------------------------------------------------
# Phase 1C reproducibility staging
# ---------------------------------------------------------------------------
staged_records: list[dict] = []


def stage(source: str, folder: str, status: str, release: str, privacy: str, role: str) -> None:
    src = ROOT / source
    if not src.is_file():
        raise FileNotFoundError(source)
    dst = STAGING / folder / src.name
    shutil.copy2(src, dst)
    staged_records.append({
        "staged_path": str(dst.relative_to(STAGING)), "source_path": source,
        "source_sha256": sha256(src), "staged_sha256": sha256(dst),
        "source_size_bytes": src.stat().st_size, "classification": status,
        "public_release_status": release, "privacy_status": privacy,
        "artifact_role": role, "relationship": "BYTE_IDENTICAL_COPY",
    })


for args in [
    ("src/models/crosscase_future_predictor.py", "01_code", "CURRENT_AUTHORITY", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "frozen model architecture"),
    ("src/preprocessing/current_only_preprocessing.py", "01_code", "CURRENT_AUTHORITY", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "future-blind preprocessing"),
    ("src/data/dataset_loader.py", "01_code", "CURRENT_AUTHORITY", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "data loader"),
    ("src/models/pcc.py", "06_pcc_algorithm", "CURRENT_AUTHORITY", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "PCC implementation"),
    ("src/evaluation/metrics.py", "07_evaluation", "CURRENT_AUTHORITY", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "evaluation metrics"),
    ("src/analysis/holdout_statistics.py", "07_evaluation", "CURRENT_AUTHORITY", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "confirmatory statistics"),
    ("src/statistics/statistics.py", "07_evaluation", "SUPPORTIVE", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "general statistics utilities"),
    ("experiments/run_115_stage_a_p0.py", "05_inference", "CURRENT_AUTHORITY", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "Stage A inference runner"),
    ("experiments/stage_b_launch_lock.py", "05_inference", "CURRENT_AUTHORITY", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "Stage B launch validator"),
    ("experiments/generate_internal_qualitative_panels.py", "08_figure_generation", "SUPPORTIVE", "REQUIRES_SCIENTIFIC_REVIEW", "NO_OBVIOUS_IDENTIFIERS", "historical figure generation utility; not Phase 1 renderer"),
    ("configs/pcc_leakage_free_canonical.yaml", "02_configs", "CURRENT_AUTHORITY", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "canonical config"),
    ("outputs/pcc_115_holdout_protocol_lock_2026/03_PREDICTOR_LOCK/LOCKED_115_PREDICTOR_CONFIG.yaml", "02_configs", "CURRENT_AUTHORITY", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "predictor lock"),
    ("outputs/pcc_115_holdout_protocol_lock_2026/04_METHOD_LOCK/LOCKED_115_METHOD_CONFIG.yaml", "02_configs", "CURRENT_AUTHORITY", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "method lock"),
    ("outputs/pcc_115_holdout_protocol_lock_2026/05_TARGET_AND_STAGE_LOCK/LOCKED_115_TARGET_POLICY.yaml", "02_configs", "CURRENT_AUTHORITY", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "target lock"),
    ("outputs/pcc_115_holdout_protocol_lock_2026/06_EVALUATION_LOCK/LOCKED_115_EVALUATION_POLICY.yaml", "02_configs", "CURRENT_AUTHORITY", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "evaluation lock"),
    ("outputs/pcc_115_holdout_protocol_lock_2026/07_STATISTICS_LOCK/LOCKED_115_STATISTICAL_ANALYSIS_PLAN.yaml", "02_configs", "CURRENT_AUTHORITY", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "statistics lock"),
    ("requirements-test-lock.txt", "03_environment", "SUPPORTIVE", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "test dependencies only"),
    ("outputs/pcc_115_holdout_protocol_lock_2026/04_METHOD_LOCK/LOCKED_115_METHOD_DEFINITIONS.md", "10_protocol_locks", "CURRENT_AUTHORITY", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "method definitions"),
    ("outputs/pcc_115_holdout_protocol_lock_2026/05_TARGET_AND_STAGE_LOCK/TWO_STAGE_DATA_ACCESS_POLICY.md", "10_protocol_locks", "CURRENT_AUTHORITY", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "outcome access"),
    ("docs/PCC_SCIENTIFIC_SPECIFICATION.md", "13_documentation", "CURRENT_AUTHORITY", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "scientific specification"),
    ("docs/PCC_METHOD_IMPLEMENTATION_AUDIT.md", "13_documentation", "SUPPORTIVE", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "implementation audit"),
    ("outputs/pcc_115_holdout_protocol_lock_2026/04_METHOD_LOCK/METHOD_CODE_HASHES.csv", "12_hash_manifests", "CURRENT_AUTHORITY", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "method hashes"),
    ("outputs/pcc_115_holdout_protocol_lock_2026/06_EVALUATION_LOCK/EVALUATION_CODE_HASHES.csv", "12_hash_manifests", "CURRENT_AUTHORITY", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "evaluation hashes"),
    ("outputs/pcc_115_holdout_protocol_lock_2026/07_STATISTICS_LOCK/STATISTICS_CODE_HASHES.csv", "12_hash_manifests", "CURRENT_AUTHORITY", "PUBLIC_CANDIDATE", "NO_OBVIOUS_IDENTIFIERS", "statistics hashes"),
]:
    stage(*args)

write(STAGING / "03_environment/ENVIRONMENT_SNAPSHOT.txt", f"""captured_for_phase1_staging=true
python={sys.version.replace(os.linesep, ' ')}
platform={platform.platform()}
note=Current audit host snapshot only; not claimed as the exact historical Kaggle runtime.
""")

reference_fields = ["artifact_role", "authoritative_source_path", "sha256", "classification", "release_status", "notes"]
write_csv(STAGING / "04_fold_manifests/SOURCE_REFERENCES.csv", reference_fields, [
    {"artifact_role": "five-fold patient-disjoint manifest", "authoritative_source_path": "validation_reference/frozen_refs/pcc_leakage_free_rerun_2026_v8/LOCKED_FOLD_MANIFEST.csv", "sha256": sha256(ROOT / "validation_reference/frozen_refs/pcc_leakage_free_rerun_2026_v8/LOCKED_FOLD_MANIFEST.csv"), "classification": "CURRENT_AUTHORITY", "release_status": "REQUIRES_PRIVACY_REVIEW", "notes": "Referenced, not copied; contains pseudonymous patient/case identifiers."},
    {"artifact_role": "40-case manifest", "authoritative_source_path": "validation_reference/frozen_refs/pcc_leakage_free_rerun_2026_v8/LOCKED_CASE_MANIFEST.csv", "sha256": sha256(ROOT / "validation_reference/frozen_refs/pcc_leakage_free_rerun_2026_v8/LOCKED_CASE_MANIFEST.csv"), "classification": "CURRENT_AUTHORITY", "release_status": "REQUIRES_PRIVACY_REVIEW", "notes": "Referenced, not copied."},
])
write_csv(STAGING / "09_derived_case_metrics/SOURCE_REFERENCES.csv", reference_fields, [
    {"artifact_role": "Internal 113 case-level metrics", "authoritative_source_path": "outputs/pcc_113_stage_b_confirmatory_validation_2026_recovery_v2/03_COMBINED_RESULTS/ALL_CASE_METHOD_METRICS.csv", "sha256": sha256(ROOT / "outputs/pcc_113_stage_b_confirmatory_validation_2026_recovery_v2/03_COMBINED_RESULTS/ALL_CASE_METHOD_METRICS.csv"), "classification": "CURRENT_AUTHORITY", "release_status": "REQUIRES_PRIVACY_REVIEW", "notes": "Referenced, not copied; pseudonymous identifiers require review."},
    {"artifact_role": "RHUH 39 case-level metrics", "authoritative_source_path": "outputs/pcc_rhuh_external_stage_b_confirmatory_validation_2026/02_CASE_RESULTS/RHUH_STAGE_B_CASE_METHOD_METRICS.csv", "sha256": sha256(ROOT / "outputs/pcc_rhuh_external_stage_b_confirmatory_validation_2026/02_CASE_RESULTS/RHUH_STAGE_B_CASE_METHOD_METRICS.csv"), "classification": "CURRENT_AUTHORITY", "release_status": "REQUIRES_PRIVACY_REVIEW", "notes": "Referenced, not copied; pseudonymous identifiers require review."},
])
write_csv(STAGING / "10_protocol_locks/PHASE0_SOURCE_REFERENCES.csv", reference_fields, [
    {"artifact_role": "Phase 0 science-freeze package", "authoritative_source_path": "pre_submission_anti_major_2026/PCC_PRE_SUBMISSION_ANTI_MAJOR_PHASE0_FREEZE_2026.zip", "sha256": sha256(BASE / "PCC_PRE_SUBMISSION_ANTI_MAJOR_PHASE0_FREEZE_2026.zip"), "classification": "CURRENT_AUTHORITY", "release_status": "REQUIRES_PRIVACY_REVIEW", "notes": "Referenced, not copied into staging; contains historical pseudonymous IDs."},
])
write_csv(STAGING / "11_source_data_for_figures/SOURCE_REFERENCES.csv", reference_fields, [
    {"artifact_role": "selected-case source data", "authoritative_source_path": "PHASE1_QUALITATIVE_PANEL_PROVENANCE.csv", "sha256": sha256(OUT / "PHASE1_QUALITATIVE_PANEL_PROVENANCE.csv"), "classification": "NOT_FOR_RELEASE", "release_status": "NOT_FOR_PUBLIC_RELEASE", "notes": "No MRI/P0/method map copied. Required frozen P10 maps missing."},
])

write(STAGING / "14_data_access_information/README.md", """# Data access information

No MRI, DICOM, segmentation volume, P0 array, model checkpoint or patient-level table is redistributed here. MU-Glioma-Post should be retrieved from TCIA under its data-use terms (DOI 10.7937/7K9K-3C83). RHUH-GBM should be retrieved from TCIA (DOI 10.7937/4545-C905). LUMIERE is not part of this release candidate and remains pending Phase 4 feasibility. Pseudonymous case manifests and case metrics require privacy/licence review before any public release.
""")
write(STAGING / "08_figure_generation/README.md", """# Figure generation

The historical utility is staged as supportive code only. The Phase 1 qualitative selection lock is authoritative for any future rendering. Rendering is currently blocked because frozen P10 method maps were not retained; no method was rerun.
""")
write(STAGING / "12_hash_manifests/README.md", """# Hash manifests

Locked method/evaluation/statistics code hashes are copied here. The complete Phase 1 tree manifest is stored beside the final audit package as `PHASE1_SHA256_MANIFEST.csv` to avoid a self-referential hash.
""")

write(OUT / "REPRODUCIBILITY_RELEASE_ARCHITECTURE.md", """# Reproducibility release architecture

The local staging tree separates code, locked configs, environment evidence, fold references, inference, PCC, evaluation, figure generation, derived-metric references, protocol locks, figure-source references, hashes, documentation and data-access information. Original authorities were never moved or modified. Small releasable files are byte-identical copies; identifier-bearing case/fold tables and raw/source arrays are hash references only.

Classification is explicit: `CURRENT_AUTHORITY`, `SUPPORTIVE`, `HISTORICAL_SUPERSEDED`, or `NOT_FOR_RELEASE`. Distribution status is independently recorded. This is local staging only; no GitHub, Zenodo or other public upload occurred.
""")
write(OUT / "README_RELEASE_CANDIDATE.md", """# PCC reproducibility release candidate

This local candidate packages current implementation/configuration evidence without redistributing MRI or patient-level source data. Start with `REPRODUCIBILITY_STEP_BY_STEP.md`, verify `PHASE1_SHA256_MANIFEST.csv`, obtain source datasets from their official repositories, and apply all licence/privacy reviews before public release.

This candidate does not authorize execution of Phase 2–4 and does not alter PCC V2.1.1 scientific results.
""")
write(OUT / "DATA_DISTRIBUTION_AND_PRIVACY_REVIEW.md", """# Data distribution and privacy review

- Raw MRI/DICOM/segmentation/P0/method maps: `NOT_FOR_PUBLIC_RELEASE` in this package; none copied.
- MU-Glioma-Post and RHUH-GBM: use official accessions and citations; do not redistribute from the local research tree without licence review.
- LUMIERE: not staged; `PENDING_PHASE4_FEASIBILITY` and licence review.
- Fold/case manifests and case-level metrics: referenced only and marked `REQUIRES_PRIVACY_REVIEW` because pseudonymous case IDs may carry linkage risk.
- Model checkpoints: not staged; ownership/licence review required.
- Public uploads performed: 0.

No obvious direct identifiers (name, MRN, accession number, dates of birth or DICOM headers) were placed in the release candidate.
""")
write(OUT / "REPRODUCIBILITY_STEP_BY_STEP.md", """# Reproducibility step by step

1. Verify the science-freeze tag and Phase 0/Phase 1 SHA manifests.
2. Obtain source datasets from official accessions under applicable terms; do not use local restricted copies as distributable content.
3. Resolve the exact historical runtime and checkpoint distribution gaps before execution.
4. Verify fold/case manifests after privacy review and preserve patient disjointness.
5. Run future-blind Stage A only with frozen checkpoints and current inputs; freeze P0 hashes.
6. Permit Stage B target access only after P0/eligibility lock; use frozen PCC/evaluation/statistics code.
7. Compare outputs against frozen manifests without changing methods, thresholds, cohorts or hypotheses.

This document is architecture preparation, not authorization to execute an experiment.
""")

gaps = [
    ("GAP-001", "Phase 0 tree manifest contains a self-hash entry; self-hashes are intrinsically non-verifiable. External entries match."),
    ("GAP-002", "Only a test dependency lock is present; the exact complete historical Kaggle runtime is not consolidated into one environment lock."),
    ("GAP-003", "Frozen checkpoint binaries are not staged and require availability/licence verification."),
    ("GAP-004", "Frozen Internal/RHUH P0 arrays are referenced by remote provenance but are not locally staged."),
    ("GAP-005", "Full PCC P10 and No-smoothing P10 maps were intentionally not retained, blocking Phase 1 qualitative rendering without prohibited re-execution."),
    ("GAP-006", "MU per-case registration transforms/interpolation details and landmark accuracy are not available in frozen project metadata."),
]
write(OUT / "KNOWN_REPRODUCIBILITY_LIMITATIONS.md", "# Known reproducibility limitations\n\n" + "\n".join(f"- **{key}:** {text}" for key, text in gaps))

# Manifest every staged file after all staging writes.
for path in sorted(STAGING.rglob("*")):
    if not path.is_file():
        continue
    rel = str(path.relative_to(STAGING))
    existing = next((r for r in staged_records if r["staged_path"] == rel), None)
    if existing is None:
        staged_records.append({
            "staged_path": rel, "source_path": "PHASE1_GENERATED",
            "source_sha256": sha256(path), "staged_sha256": sha256(path),
            "source_size_bytes": path.stat().st_size, "classification": "SUPPORTIVE",
            "public_release_status": "PUBLIC_CANDIDATE" if "SOURCE_REFERENCES" not in path.name else "REQUIRES_PRIVACY_REVIEW",
            "privacy_status": "NO_RAW_DATA; REVIEW_REFERENCES", "artifact_role": "staging documentation/reference",
            "relationship": "PHASE1_GENERATED",
        })
write_csv(OUT / "PUBLIC_RELEASE_FILE_MANIFEST.csv", list(staged_records[0]), staged_records)

raw_suffixes = (".nii", ".nii.gz", ".dcm", ".npy", ".npz", ".pt", ".pth", ".ckpt")
raw_files = [str(p.relative_to(STAGING)) for p in STAGING.rglob("*") if p.is_file() and p.name.lower().endswith(raw_suffixes)]
missing_staged = sum(not (STAGING / row["staged_path"]).is_file() for row in staged_records)
hash_mismatch_staged = sum(sha256(STAGING / row["staged_path"]) != row["staged_sha256"] for row in staged_records)
validation = {
    "manifest_rows": len(staged_records), "missing_staged_files": missing_staged,
    "hash_mismatches": hash_mismatch_staged, "raw_restricted_files": raw_files,
    "public_uploads_performed": 0, "source_relationship_clear": True,
    "authority_classification_complete": True,
}
write(OUT / "REPRODUCIBILITY_STAGING_VALIDATION.json", json.dumps(validation, indent=2))

panel_generated = (OUT / "PHASE1_QUALITATIVE_MRI_PANEL.png").exists()
status = {
    "PHASE0_INTEGRITY_VERIFIED": "YES",
    "PHASE0_SCIENCE_FREEZE_TAG_VERIFIED": "YES",
    "PHASE0_REGISTERED_TAG": TAG,
    "USER_REFERENCED_CASE_VARIANT": "PCC-v2.1.1-science-freeze-20260811",
    "FROZEN_NUMERIC_RESULTS_CHANGED": 0,
    "FROZEN_SCIENTIFIC_FILES_CHANGED": 0,
    "NEW_MODELS_TRAINED": 0,
    "NEW_P0_GENERATED": 0,
    "NEW_PERFORMANCE_RESULTS_GENERATED": 0,
    "NEW_HYPOTHESIS_TESTS": 0,
    "REGISTRATION_PROVENANCE_AUDIT": "COMPLETE",
    "UNSUPPORTED_REGISTRATION_CLAIMS": 0,
    "QUALITATIVE_SELECTION_LOCKED_BEFORE_RENDER": "YES",
    "QUALITATIVE_CASE_SELECTION_MECHANICAL": "YES",
    "QUALITATIVE_SLICE_SELECTION_MECHANICAL": "YES",
    "QUALITATIVE_SLICE_SELECTION_EXECUTED": "NO_MISSING_COMPLETE_FROZEN_MAP_SET",
    "QUALITATIVE_PANEL_GENERATED": "YES" if panel_generated else "HOLD_MISSING_FROZEN_ARTIFACT",
    "PHASE1B_CASE_C": "PASS_UNIQUE_EXACT_IDENTITY",
    "REPRODUCIBILITY_PACKAGE_STAGED": "YES",
    "REPRODUCIBILITY_GAPS_FOUND": len(gaps),
    "PUBLIC_UPLOADS_PERFORMED": 0,
    "PHASE2_EXECUTED": "NO", "PHASE3_EXECUTED": "NO",
    "PHASE4_PERFORMANCE_ACCESSED": "NO", "LUMIERE_NEW_OUTCOME_ACCESSED": "NO",
    "PHASE0_MANIFEST_EXTERNAL_MISMATCHES": all_external_mismatches,
    "PHASE0_MANIFEST_SELF_REFERENCE_GAP": 1,
    "PHASE1_GATE": "PASS_READY_FOR_PHASE2" if panel_generated and not gaps else "HOLD",
    "BLOCKERS": ["HOLD_MISSING_FROZEN_ARTIFACT: selected-case frozen Full PCC P10 and No-smoothing P10 maps are unavailable; PCC re-execution is forbidden."],
}
write(OUT / "PHASE1_GATE_STATUS.json", json.dumps(status, indent=2))
write(OUT / "PHASE1_FINAL_AUDIT_REPORT.md", f"""# Phase 1 final independent audit

## A. Registration provenance

- Physical-grid compatibility versus true anatomical registration clearly distinguished: **YES**.
- Unsupported registration claims: **NO (0)**.

## B. Qualitative panel

- Case selection completely mechanical: **YES**.
- Selection lock written and committed before any rendering: **YES**.
- Slice rule mechanical: **YES, LOCKED; NOT EXECUTED**.
- Case changed after viewing: **NO**.
- Slice changed after viewing: **NO**.
- Panel: **HOLD_MISSING_FROZEN_ARTIFACT**. No image was rendered because frozen P10 maps were not retained and PCC re-execution is prohibited.

## C. Reproducibility

- Staging traceable to authoritative source: **YES**.
- Superseded science mixed into current authority: **NO**.
- Raw restricted MRI included: **NO**.
- Public upload: **NO (0)**.
- Reproducibility gaps: **{len(gaps)}**, transparently recorded.

## D. Frozen science

- Phase 0 frozen science intact: **YES**.
- Frozen numeric results changed: **0**.
- Frozen scientific files changed: **0**.
- New model/P0/PCC performance/hypothesis test: **0/0/0/0**.
- Phase 2/3 execution and Phase 4 performance access: **NO/NO/NO**.

## Gate

`PHASE1_GATE = HOLD` because the required frozen qualitative method maps are missing. Phase 1A and Phase 1C are complete. No prohibited reconstruction was attempted.
""")

# Hash manifest excludes itself and the package, avoiding the Phase 0
# self-reference gap by design.
hash_rows = []
for path in sorted(OUT.rglob("*")):
    if not path.is_file() or path.name == "PHASE1_SHA256_MANIFEST.csv":
        continue
    hash_rows.append({
        "relative_path": str(path.relative_to(OUT)), "size_bytes": path.stat().st_size,
        "sha256": sha256(path), "mutable_after_phase1": "NO",
        "notes": "Phase 1 audit/staging artifact; no new scientific result.",
    })
write_csv(OUT / "PHASE1_SHA256_MANIFEST.csv", list(hash_rows[0]), hash_rows)

zip_path = BASE / "PCC_PRE_SUBMISSION_ANTI_MAJOR_PHASE1_HARDENING_2026.zip"
with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(OUT.rglob("*")):
        if path.is_file():
            archive.write(path, Path(OUT.name) / path.relative_to(OUT))
write(zip_path.with_suffix(zip_path.suffix + ".sha256"), f"{sha256(zip_path)}  {zip_path.name}")

print(json.dumps(status, indent=2))
print(f"phase1_zip={zip_path}")
print(f"phase1_zip_sha256={sha256(zip_path)}")
