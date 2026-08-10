#!/usr/bin/env python3
"""Read-only validation of a downloaded RHUH External Stage A kernel output."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "outputs/pcc_rhuh_external_stage_a_p0_freeze_2026"
PROTOCOL_COMMIT = "6c8bf164f8e445123143db08c34f0f66a1e21226"
PROTOCOL_ZIP_SHA256 = "2ac4378b279854a5497185176e9cd776da8207aab04dd4617cb310080fbad059"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("kernel_output", type=Path)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()
    kernel_root = args.kernel_output.resolve()
    output_root = args.output_root.resolve()

    manifest_path = kernel_root / "05_P0_FREEZE/LOCKED_RHUH_39_EXTERNAL_P0_MANIFEST.csv"
    sha_path = kernel_root / "05_P0_FREEZE/LOCKED_RHUH_39_EXTERNAL_P0_SHA256.csv"
    completion_path = (
        kernel_root / "05_P0_FREEZE/LOCKED_RHUH_39_EXTERNAL_P0_COMPLETION_STATUS.csv"
    )
    access_path = kernel_root / "06_IO_ACCESS_AUDIT/STAGE_A_SCIENTIFIC_FILE_ACCESS_LOG.csv"
    failure_path = kernel_root / "06_IO_ACCESS_AUDIT/STAGE_A_FAILURE_LOG.csv"
    current_audit_path = (
        kernel_root / "01_CURRENT_ONLY_DATASET/RHUH_STAGE_A_REMOTE_CURRENT_FILE_AUDIT.csv"
    )
    checkpoint_path = (
        kernel_root
        / "02_PREDICTOR_AUTHORITY/LOCKED_RHUH_FROZEN_PREDICTOR_RUNTIME_MANIFEST.csv"
    )
    status_path = kernel_root / "08_RELEASE/PCC_RHUH_EXTERNAL_STAGE_A_STATUS.json"
    runtime_path = kernel_root / "00_AUTHORITY/KAGGLE_RUNTIME_INFO.json"

    manifest = read_csv(manifest_path)
    sha_rows = read_csv(sha_path)
    completions = read_csv(completion_path)
    access = read_csv(access_path)
    failures = read_csv(failure_path)
    current_audit = read_csv(current_audit_path)
    checkpoints = read_csv(checkpoint_path)
    status = json.loads(status_path.read_text(encoding="utf-8"))
    runtime = json.loads(runtime_path.read_text(encoding="utf-8"))

    sha_by_case = {row["case_id"]: row for row in sha_rows}
    validation_rows: list[dict[str, object]] = []
    for row in manifest:
        case_id = row["case_id"]
        path = kernel_root / row["p0_relative_path"]
        actual_hash = sha256(path) if path.is_file() else ""
        dtype, shape, finite, minimum, maximum = (
            inspect_p0(path) if path.is_file() else ("", (), False, float("nan"), float("nan"))
        )
        expected_shape = tuple(int(value) for value in row["p0_shape_zhw"].split("x"))
        sha_record = sha_by_case.get(case_id, {})
        marker = kernel_root / f"05_P0_FREEZE/completion/{case_id}.complete.json"
        marker_status = ""
        marker_hash = ""
        if marker.is_file():
            marker_data = json.loads(marker.read_text(encoding="utf-8"))
            marker_status = marker_data.get("status", "")
            marker_hash = marker_data.get("p0_sha256", "")
        validation_rows.append(
            {
                "patient_id": row["patient_id"],
                "case_id": case_id,
                "path": str(path),
                "exists": path.is_file(),
                "size_bytes": path.stat().st_size if path.is_file() else 0,
                "expected_sha256": row["sha256"],
                "computed_sha256": actual_hash,
                "manifest_hash_match": actual_hash == row["sha256"],
                "sha_table_hash_match": actual_hash == sha_record.get("sha256", ""),
                "dtype": dtype,
                "dtype_valid": dtype == "float32",
                "shape": "x".join(str(value) for value in shape),
                "shape_valid": shape == expected_shape,
                "finite": finite,
                "min": minimum,
                "max": maximum,
                "range_valid": finite and minimum >= 0.0 and maximum <= 1.0,
                "completion_marker_exists": marker.is_file(),
                "completion_marker_status": marker_status,
                "completion_marker_hash_match": marker_hash == actual_hash,
            }
        )

    hashes = Counter(row["computed_sha256"] for row in validation_rows if row["computed_sha256"])
    forbidden_path_count = sum(
        any(token in row["path"].lower() for token in ("recurrence", "future", "target", "performance"))
        for row in access
    )
    allowed_types = {"CURRENT_T1CE", "CURRENT_SEGMENTATION", "FROZEN_CHECKPOINT"}
    protocol_zip = ROOT / "PCC_RHUH_EXTERNAL_PROTOCOL_LOCK_2026.zip"
    commit_type = subprocess.run(
        ["git", "cat-file", "-t", PROTOCOL_COMMIT],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    checks = {
        "protocol_zip_sha_match": sha256(protocol_zip) == PROTOCOL_ZIP_SHA256,
        "pre_outcome_commit_match": commit_type.returncode == 0 and commit_type.stdout.strip() == "commit",
        "cohort_39": len(manifest) == 39 and len({r["patient_id"] for r in manifest}) == 39,
        "rhuh_0008_absent": all(r["patient_id"] != "RHUH-0008" for r in manifest),
        "current_t1ce_39": sum(r["file_type"] == "CURRENT_T1CE" for r in current_audit) == 39,
        "current_segmentation_39": sum(r["file_type"] == "CURRENT_SEGMENTATION" for r in current_audit) == 39,
        "current_source_hashes_match": all(r["hash_status"] == "MATCH" for r in current_audit),
        "checkpoint_count_5": len(checkpoints) == 5,
        "checkpoint_hashes_match": all(r["hash_status"] == "MATCH" for r in checkpoints),
        "p0_count_39": len(validation_rows) == 39 and all(r["exists"] for r in validation_rows),
        "p0_unique_cases_39": len({r["case_id"] for r in validation_rows}) == 39,
        "p0_file_hashes_match": all(r["manifest_hash_match"] for r in validation_rows),
        "p0_sha_table_matches": all(r["sha_table_hash_match"] for r in validation_rows),
        "p0_dtype_float32": all(r["dtype_valid"] for r in validation_rows),
        "p0_finite_39": all(r["finite"] for r in validation_rows),
        "p0_range_valid_39": all(r["range_valid"] for r in validation_rows),
        "p0_shape_valid_39": all(r["shape_valid"] for r in validation_rows),
        "completion_markers_39": len(completions) == 39
        and all(r["completion_marker_exists"] for r in validation_rows),
        "completion_marker_hashes_match": all(
            r["completion_marker_hash_match"] for r in validation_rows
        ),
        "duplicate_p0_hash_groups_0": sum(count > 1 for count in hashes.values()) == 0,
        "failure_rows_0": len(failures) == 0,
        "io_types_current_or_checkpoint_only": set(r["file_type"] for r in access) <= allowed_types,
        "forbidden_io_paths_0": forbidden_path_count == 0,
        "future_segmentation_voxel_access_0": runtime["future_segmentation_voxel_access"] == 0,
        "recurrence_t1ce_voxel_access_0": runtime["recurrence_t1ce_voxel_access"] == 0,
        "training_false": runtime["training"] is False,
        "backward_false": runtime["backward"] is False,
        "fine_tuning_false": runtime["fine_tuning"] is False,
        "calibration_false": runtime["calibration"] is False,
        "tta_false": runtime["test_time_adaptation"] is False,
        "target_constructed_false": runtime["target_constructed"] is False,
        "performance_computed_false": runtime["performance_computed"] is False,
        "stage_b_executed_false": runtime["stage_b_executed"] is False,
        "remote_gate_pass": status["gate"] == "PASS",
    }
    gate = "PASS" if all(checks.values()) else "BLOCKED"
    tests = output_root / "07_TESTS"
    write_csv(
        tests / "LOCAL_P0_FILE_VALIDATION.csv",
        validation_rows,
        list(validation_rows[0]),
    )
    local_status = {
        "p0_files": len(validation_rows),
        "unique_patients": len({r["patient_id"] for r in validation_rows}),
        "unique_cases": len({r["case_id"] for r in validation_rows}),
        "missing": sum(not r["exists"] for r in validation_rows),
        "hash_mismatch": sum(not r["manifest_hash_match"] for r in validation_rows),
        "dtype_failure": sum(not r["dtype_valid"] for r in validation_rows),
        "finite_failure": sum(not r["finite"] for r in validation_rows),
        "range_failure": sum(not r["range_valid"] for r in validation_rows),
        "shape_failure": sum(not r["shape_valid"] for r in validation_rows),
        "completion_markers": sum(r["completion_marker_exists"] for r in validation_rows),
        "duplicate_p0_hash_groups": sum(count > 1 for count in hashes.values()),
        "future_segmentation_voxel_access": runtime["future_segmentation_voxel_access"],
        "recurrence_t1ce_voxel_access": runtime["recurrence_t1ce_voxel_access"],
        "target_constructed": runtime["target_constructed"],
        "performance_computed": runtime["performance_computed"],
        "stage_b_executed": runtime["stage_b_executed"],
        "checks": checks,
        "gate": gate,
    }
    (tests / "LOCAL_STAGE_A_VALIDATION_STATUS.json").write_text(
        json.dumps(local_status, indent=2) + "\n", encoding="utf-8"
    )
    (tests / "LOCAL_STAGE_A_VALIDATION_REPORT.md").write_text(
        "# RHUH External Stage A local read-only validation\n\n"
        + "\n".join(f"- {name}: {'PASS' if value else 'FAIL'}" for name, value in checks.items())
        + f"\n\n- `EXTERNAL_STAGE_A_P0_FREEZE_GATE={gate}`\n",
        encoding="utf-8",
    )
    print(json.dumps(local_status, indent=2))
    if gate != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
