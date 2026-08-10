#!/usr/bin/env python3
"""Prepare RHUH External Stage B without reading recurrence voxel arrays.

This pre-outcome utility performs the live frozen-P0 gate, locks the 39-case
cohort identity, and creates a byte-preserving outcome-only Kaggle dataset.
It hashes and copies segmentation files as opaque bytes; it never opens a
NIfTI image or constructs a target.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/pcc_rhuh_external_stage_b_confirmatory_validation_2026"
COHORT = (
    ROOT
    / "outputs/pcc_rhuh_external_protocol_lock_2026/01_COHORT_LOCK/"
    "LOCKED_RHUH_39_EXTERNAL_CONFIRMATORY_CASE_MANIFEST.csv"
)
GEOMETRY = (
    ROOT
    / "outputs/pcc_rhuh_external_protocol_lock_2026/02_GEOMETRY_LOCK/"
    "LOCKED_RHUH_39_GEOMETRY_MANIFEST.csv"
)
P0_MANIFEST = (
    ROOT
    / "outputs/pcc_rhuh_external_stage_a_p0_freeze_2026/05_P0_FREEZE/"
    "LOCKED_RHUH_39_EXTERNAL_P0_MANIFEST.csv"
)
P0_SHA = P0_MANIFEST.with_name("LOCKED_RHUH_39_EXTERNAL_P0_SHA256.csv")
STAGE_A_ZIP = ROOT / "PCC_RHUH_EXTERNAL_STAGE_A_P0_FREEZE_2026.zip"
STAGE_A_ZIP_SHA256 = "2f55124706107ba5e584883aab8f4d8f5aec4283d4470248d4aacce60f3413f3"
PROTOCOL_COMMIT = "6c8bf164f8e445123143db08c34f0f66a1e21226"
STAGE_A_COMMIT = "f33eb65e32fabc9ba79be2ece4ee4da132ff6273"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def git_object_is_commit(commit: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-t", commit],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == "commit"


def inspect_p0(path: Path) -> tuple[str, tuple[int, ...], bool, float, float]:
    array = np.load(path, mmap_mode="r", allow_pickle=False)
    finite = True
    minimum = float("inf")
    maximum = float("-inf")
    for index in range(array.shape[0]):
        slab = np.asarray(array[index])
        finite = finite and bool(np.isfinite(slab).all())
        minimum = min(minimum, float(slab.min()))
        maximum = max(maximum, float(slab.max()))
    return str(array.dtype), tuple(array.shape), finite, minimum, maximum


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p0-root", type=Path, required=True)
    parser.add_argument("--dataset-staging", type=Path, required=True)
    args = parser.parse_args()
    p0_root = args.p0_root.resolve()
    staging = args.dataset_staging.resolve()

    cohort = read_csv(COHORT)
    p0_manifest = read_csv(P0_MANIFEST)
    p0_sha_rows = read_csv(P0_SHA)
    geometry = read_csv(GEOMETRY)
    p0_sha_by_case = {row["case_id"]: row for row in p0_sha_rows}
    p0_by_case = {row["case_id"]: row for row in p0_manifest}

    live_rows: list[dict[str, object]] = []
    for case in cohort:
        case_id = case["case_id"]
        expected = p0_by_case.get(case_id, {})
        p0_path = p0_root / expected.get("p0_relative_path", "MISSING")
        exists = p0_path.is_file()
        actual_hash = sha256(p0_path) if exists else ""
        dtype, shape, finite, minimum, maximum = (
            inspect_p0(p0_path)
            if exists
            else ("", (), False, float("nan"), float("nan"))
        )
        expected_shape = tuple(
            int(value) for value in expected.get("p0_shape_zhw", "").split("x") if value
        )
        live_rows.append(
            {
                "patient_id": case["patient_id"],
                "case_id": case_id,
                "resolved_p0_path": str(p0_path),
                "exists": exists,
                "file_size_bytes": p0_path.stat().st_size if exists else 0,
                "expected_file_size_bytes": expected.get("file_size_bytes", ""),
                "expected_sha256": expected.get("sha256", ""),
                "computed_sha256": actual_hash,
                "sha256_match": actual_hash == expected.get("sha256", "")
                and actual_hash == p0_sha_by_case.get(case_id, {}).get("sha256", ""),
                "dtype": dtype,
                "dtype_valid": dtype == "float32",
                "shape_zhw": "x".join(str(value) for value in shape),
                "shape_valid": shape == expected_shape,
                "finite": finite,
                "min": minimum,
                "max": maximum,
                "range_valid": finite and minimum >= 0.0 and maximum <= 1.0,
            }
        )

    live_path = OUT / "00_STAGE_B_LAUNCH/RHUH_STAGE_B_LIVE_P0_VERIFICATION.csv"
    write_csv(live_path, live_rows, list(live_rows[0]))
    hashes = Counter(row["computed_sha256"] for row in live_rows if row["computed_sha256"])
    live_summary = {
        "patients": len({row["patient_id"] for row in live_rows}),
        "p0_files": len(live_rows),
        "missing": sum(not row["exists"] for row in live_rows),
        "duplicate_hash_groups": sum(count > 1 for count in hashes.values()),
        "sha256_mismatch": sum(not row["sha256_match"] for row in live_rows),
        "dtype_mismatch": sum(not row["dtype_valid"] for row in live_rows),
        "shape_mismatch": sum(not row["shape_valid"] for row in live_rows),
        "nonfinite": sum(not row["finite"] for row in live_rows),
        "range_violation": sum(not row["range_valid"] for row in live_rows),
    }
    live_gate = "PASS" if all(
        (
            live_summary["patients"] == 39,
            live_summary["p0_files"] == 39,
            live_summary["missing"] == 0,
            live_summary["duplicate_hash_groups"] == 0,
            live_summary["sha256_mismatch"] == 0,
            live_summary["dtype_mismatch"] == 0,
            live_summary["shape_mismatch"] == 0,
            live_summary["nonfinite"] == 0,
            live_summary["range_violation"] == 0,
        )
    ) else "BLOCKED"
    report = ["# RHUH Stage B live frozen-P0 verification", ""]
    report.extend(f"- {key}: {value}" for key, value in live_summary.items())
    report.append(f"- LIVE_P0_GATE: {live_gate}")
    (live_path.parent / "RHUH_STAGE_B_LIVE_P0_VERIFICATION_REPORT.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )

    geometry_by_patient = {row["patient_id"]: row for row in geometry}
    identity_rows: list[dict[str, object]] = []
    for case in cohort:
        g = geometry_by_patient.get(case["patient_id"], {})
        identity_rows.append(
            {
                "manifest_order": len(identity_rows),
                "patient_id": case["patient_id"],
                "case_id": case["case_id"],
                "RHUH_0008_absent": case["patient_id"] != "RHUH-0008",
                "geometry_valid": case["geometry_valid"].lower() == "true",
                "geometry_audit_status": g.get("all_geometry_valid", g.get("geometry_valid", "")),
                "mask_mapping": case["current_mask_mapping"],
                "failure_denominator": 39,
            }
        )
    identity_path = OUT / "00_STAGE_B_LAUNCH/RHUH_STAGE_B_COHORT_IDENTITY_LOCK.csv"
    write_csv(identity_path, identity_rows, list(identity_rows[0]))

    stage_a_zip_match = STAGE_A_ZIP.is_file() and sha256(STAGE_A_ZIP) == STAGE_A_ZIP_SHA256
    cohort_gate = (
        len(cohort) == 39
        and len({row["patient_id"] for row in cohort}) == 39
        and len({row["case_id"] for row in cohort}) == 39
        and all(row["patient_id"] != "RHUH-0008" for row in cohort)
        and all(row["geometry_valid"].lower() == "true" for row in cohort)
        and all(
            row["current_mask_mapping"] == "RHUH_segmentation_gt_0_labels_1_2_3"
            for row in cohort
        )
    )
    launch_status = {
        "stage_a_authority_zip_sha256": STAGE_A_ZIP_SHA256,
        "stage_a_authority_zip_sha256_match": stage_a_zip_match,
        "protocol_commit": PROTOCOL_COMMIT,
        "protocol_commit_exists": git_object_is_commit(PROTOCOL_COMMIT),
        "stage_a_commit": STAGE_A_COMMIT,
        "stage_a_commit_exists": git_object_is_commit(STAGE_A_COMMIT),
        "stable_p0_source": "jeechangxin/pcc-rhuh-external-stage-a-p0-freeze-2026/versions/1",
        "confirmatory_patients": len(cohort),
        "unique_patient_ids": len({row["patient_id"] for row in cohort}),
        "unique_case_ids": len({row["case_id"] for row in cohort}),
        "excluded_patient_absent": all(row["patient_id"] != "RHUH-0008" for row in cohort),
        "geometry_valid": sum(row["geometry_valid"].lower() == "true" for row in cohort),
        "mask_mapping": "RHUH segmentation > 0 (labels 1, 2, 3)",
        "failure_denominator": 39,
        "live_p0_summary": live_summary,
        "LIVE_P0_GATE": live_gate,
        "COHORT_IDENTITY_GATE": "PASS" if cohort_gate else "BLOCKED",
        "recurrence_segmentation_voxel_arrays_read": 0,
        "target_constructed": False,
        "performance_computed": False,
        "science_config_frozen": False,
    }
    write_json(OUT / "00_STAGE_B_LAUNCH/RHUH_STAGE_B_LAUNCH_STATUS.json", launch_status)

    if not stage_a_zip_match or live_gate != "PASS" or not cohort_gate:
        print(json.dumps(launch_status, indent=2))
        return 1

    if staging.exists() and any(staging.iterdir()):
        raise RuntimeError(f"dataset staging directory is not empty: {staging}")
    (staging / "current_segmentation").mkdir(parents=True, exist_ok=True)
    (staging / "recurrence_segmentation").mkdir(parents=True, exist_ok=True)
    (staging / "manifest").mkdir(parents=True, exist_ok=True)
    (staging / "authority").mkdir(parents=True, exist_ok=True)

    outcome_rows: list[dict[str, object]] = []
    for index, case in enumerate(cohort):
        current_source = ROOT / case["current_segmentation_path"]
        future_source = ROOT / case["future_segmentation_path"]
        current_hash = sha256(current_source)
        future_hash = sha256(future_source)
        if current_hash != case["current_segmentation_sha256"]:
            raise RuntimeError(f"current segmentation hash mismatch: {case['patient_id']}")
        if future_hash != case["future_segmentation_sha256"]:
            raise RuntimeError(f"recurrence segmentation hash mismatch: {case['patient_id']}")
        current_rel = Path("current_segmentation") / f"{case['patient_id']}_current_segmentations.nii.gz.bin"
        future_rel = Path("recurrence_segmentation") / f"{case['patient_id']}_recurrence_segmentations.nii.gz.bin"
        shutil.copyfile(current_source, staging / current_rel)
        shutil.copyfile(future_source, staging / future_rel)
        if sha256(staging / current_rel) != current_hash or sha256(staging / future_rel) != future_hash:
            raise RuntimeError(f"opaque byte copy mismatch: {case['patient_id']}")
        outcome_rows.append(
            {
                "manifest_order": index,
                "patient_id": case["patient_id"],
                "case_id": case["case_id"],
                "current_segmentation_relative_path": current_rel.as_posix(),
                "current_segmentation_size_bytes": current_source.stat().st_size,
                "current_segmentation_sha256": current_hash,
                "recurrence_segmentation_relative_path": future_rel.as_posix(),
                "recurrence_segmentation_size_bytes": future_source.stat().st_size,
                "recurrence_segmentation_sha256": future_hash,
                "mask_mapping": "segmentation > 0",
                "geometry_valid": True,
            }
        )

    runtime_manifest = staging / "manifest/RHUH_STAGE_B_OUTCOME_DATASET_MANIFEST.csv"
    write_csv(runtime_manifest, outcome_rows, list(outcome_rows[0]))
    shutil.copyfile(COHORT, staging / "authority/LOCKED_RHUH_39_EXTERNAL_CONFIRMATORY_CASE_MANIFEST.csv")
    shutil.copyfile(P0_MANIFEST, staging / "authority/LOCKED_RHUH_39_EXTERNAL_P0_MANIFEST.csv")
    shutil.copyfile(P0_SHA, staging / "authority/LOCKED_RHUH_39_EXTERNAL_P0_SHA256.csv")
    for source in (
        ROOT / "outputs/pcc_rhuh_external_protocol_lock_2026/06_STAGE_B_LOCK/LOCKED_RHUH_EXTERNAL_STAGE_B_PROTOCOL.yaml",
        ROOT / "outputs/pcc_rhuh_external_protocol_lock_2026/06_STAGE_B_LOCK/LOCKED_RHUH_EXTERNAL_EVALUATION_POLICY.yaml",
        ROOT / "outputs/pcc_rhuh_external_protocol_lock_2026/07_STATISTICS_LOCK/LOCKED_RHUH_EXTERNAL_STATISTICAL_ANALYSIS_PLAN.yaml",
        ROOT / "outputs/pcc_rhuh_external_protocol_lock_2026/08_FAILURE_LOCK/LOCKED_RHUH_EXTERNAL_FAILURE_POLICY.yaml",
    ):
        shutil.copyfile(source, staging / "authority" / source.name)

    dataset_manifest = OUT / "00_STAGE_B_LAUNCH/RHUH_STAGE_B_OUTCOME_DATASET_MANIFEST.csv"
    write_csv(dataset_manifest, outcome_rows, list(outcome_rows[0]))
    provenance = {
        "dataset_slug": "jeechangxin/pcc-rhuh-stage-b-outcome-only-2026",
        "source": "official RHUH NIfTI v1 files already locked before outcome access",
        "patients": 39,
        "current_segmentation_files": 39,
        "recurrence_segmentation_files": 39,
        "recurrence_t1ce_files": 0,
        "current_t1ce_files": 0,
        "preoperative_files": 0,
        "predictor_checkpoints": 0,
        "byte_preserving_copy": True,
        "nifti_arrays_opened_during_dataset_build": 0,
        "target_constructed_during_dataset_build": False,
        "performance_computed_during_dataset_build": False,
    }
    write_json(staging / "authority/RHUH_STAGE_B_OUTCOME_DATASET_PROVENANCE.json", provenance)
    (OUT / "00_STAGE_B_LAUNCH/RHUH_STAGE_B_OUTCOME_DATASET_PROVENANCE.md").write_text(
        "# RHUH Stage B outcome-only dataset provenance\n\n"
        "The dataset contains byte-for-byte copies of the locked early-postoperative and recurrence segmentation files for the 39-case confirmatory cohort, plus authority manifests and policies. No NIfTI voxel array was opened while building this dataset; no target or performance was computed. It contains no T1ce image, preoperative image, checkpoint, training data, P0, or result file.\n",
        encoding="utf-8",
    )
    print(json.dumps({**launch_status, "outcome_dataset": provenance}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
