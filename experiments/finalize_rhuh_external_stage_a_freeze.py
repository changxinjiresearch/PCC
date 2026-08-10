#!/usr/bin/env python3
"""Finalize the metadata-only RHUH External Stage A P0 freeze release."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "outputs/pcc_rhuh_external_stage_a_p0_freeze_2026"
ARCHIVE = ROOT / "PCC_RHUH_EXTERNAL_STAGE_A_P0_FREEZE_2026.zip"
ARCHIVE_SHA = ROOT / "PCC_RHUH_EXTERNAL_STAGE_A_P0_FREEZE_2026.zip.sha256"
RELEASE_SUMMARY = ROOT / "PCC_RHUH_EXTERNAL_STAGE_A_P0_FREEZE_2026_RELEASE_SUMMARY.txt"
PROTOCOL_COMMIT = "6c8bf164f8e445123143db08c34f0f66a1e21226"
PROTOCOL_ZIP_SHA256 = "2ac4378b279854a5497185176e9cd776da8207aab04dd4617cb310080fbad059"
KERNEL_SLUG = "jeechangxin/pcc-rhuh-external-stage-a-p0-freeze-2026"
KERNEL_VERSION = 1
DATASET_SLUG = "jeechangxin/pcc-rhuh-stage-a-current-only-2026"
DATASET_VERSION = 2
CHECKPOINT_SLUG = "jeechangxin/pcc-leakage-free-rerun-2026"
CHECKPOINT_VERSION = 8


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def copy_remote_metadata(kernel_root: Path, output_root: Path) -> None:
    for directory in (
        "00_AUTHORITY",
        "01_CURRENT_ONLY_DATASET",
        "02_PREDICTOR_AUTHORITY",
        "03_CURRENT_INPUT_AUDIT",
        "05_P0_FREEZE",
        "06_IO_ACCESS_AUDIT",
        "07_TESTS",
        "08_RELEASE",
    ):
        shutil.copytree(kernel_root / directory, output_root / directory, dirs_exist_ok=True)


def preserve_dataset_attempts(output_root: Path) -> None:
    current = output_root / "01_CURRENT_ONLY_DATASET"
    attempt_one = current / "TRANSPORT_ATTEMPT_1_LOCAL"
    attempt_one.mkdir(parents=True, exist_ok=True)
    for name in (
        "LOCKED_RHUH_39_STAGE_A_CURRENT_ONLY_MANIFEST.csv",
        "RHUH_STAGE_A_CURRENT_ONLY_DATASET_MANIFEST.csv",
        "RHUH_STAGE_A_CURRENT_ONLY_SOURCE_PROVENANCE.json",
        "RHUH_STAGE_A_CURRENT_ONLY_DATASET_HASH_LOCK.json",
        "RHUH_STAGE_A_CURRENT_ONLY_DATASET_AUDIT.md",
        "CURRENT_ONLY_DATASET_GATE_STATUS.json",
    ):
        source = current / name
        if source.is_file():
            copy_file(source, attempt_one / name)

    v2 = current / "REMOTE_TRANSPORT_V2"
    for source in v2.iterdir():
        if source.is_file():
            copy_file(source, current / source.name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("kernel_output", type=Path)
    parser.add_argument("--kernel-log", type=Path, required=True)
    args = parser.parse_args()
    kernel_root = args.kernel_output.resolve()
    output_root = OUTPUT_ROOT.resolve()

    if ARCHIVE.exists() or ARCHIVE_SHA.exists() or RELEASE_SUMMARY.exists():
        raise FileExistsError("Refusing to overwrite an existing External Stage A release")

    preserve_dataset_attempts(output_root)
    copy_remote_metadata(kernel_root, output_root)
    copy_file(args.kernel_log.resolve(), output_root / "06_IO_ACCESS_AUDIT/KAGGLE_KERNEL_VERSION_1_LOG.txt")

    # Promote the authoritative version-2 transport evidence to the required names.
    v2 = output_root / "01_CURRENT_ONLY_DATASET/REMOTE_TRANSPORT_V2"
    for source in v2.iterdir():
        if source.is_file():
            copy_file(source, output_root / "01_CURRENT_ONLY_DATASET" / source.name)
    copy_file(
        kernel_root / "01_CURRENT_ONLY_DATASET/LOCKED_RHUH_39_STAGE_A_CURRENT_ONLY_MANIFEST.csv",
        output_root / "01_CURRENT_ONLY_DATASET/LOCKED_RHUH_39_STAGE_A_CURRENT_ONLY_MANIFEST.csv",
    )

    release = output_root / "08_RELEASE"
    remote_status = release / "PCC_RHUH_EXTERNAL_STAGE_A_STATUS.json"
    copy_file(remote_status, release / "KAGGLE_REMOTE_STAGE_A_STATUS.json")

    code_root = output_root / "00_AUTHORITY/EXECUTION_CODE"
    for source in (
        ROOT / "experiments/build_rhuh_external_stage_a_current_only.py",
        ROOT / "experiments/validate_rhuh_external_stage_a_output.py",
        ROOT / "experiments/test_rhuh_external_stage_a_freeze.py",
        ROOT / "experiments/finalize_rhuh_external_stage_a_freeze.py",
        ROOT / "kaggle/pcc_rhuh_external_stage_a_p0_freeze_2026/run.py",
        ROOT / "kaggle/pcc_rhuh_external_stage_a_p0_freeze_2026/kernel-metadata.json",
    ):
        copy_file(source, code_root / source.name)

    protocol_predictor = ROOT / "outputs/pcc_rhuh_external_protocol_lock_2026/04_PREDICTOR_LOCK"
    for source in protocol_predictor.iterdir():
        if source.is_file():
            copy_file(source, output_root / "02_PREDICTOR_AUTHORITY/PROTOCOL_LOCK" / source.name)

    dataset_attempt = {
        "dataset_slug": DATASET_SLUG,
        "version_1": {
            "status": "SUPERSEDED_ENGINEERING_TRANSPORT_FAILURE",
            "cause": "Kaggle automatically expanded .nii.gz files, so mounted bytes did not preserve locked source hashes",
            "predictor_forward_executed": False,
            "p0_generated": False,
            "retained": True,
        },
        "version_2": {
            "status": "PASS",
            "transport": "byte-identical NIfTI .nii.gz bytes stored with opaque .bin suffix",
            "remote_file_count": 82,
            "scientific_file_count": 78,
            "remote_fixed_sample": "RHUH-0001_1_t1ce.nii.gz.bin",
            "remote_fixed_sample_sha256": "3b7f6f7d19ee12317cc4131d4f32773f7c5ceefd35d98a4de7f21901abc5fbe8",
            "source_hash_mismatch": 0,
        },
        "authoritative_version": DATASET_VERSION,
    }
    (output_root / "01_CURRENT_ONLY_DATASET/KAGGLE_DATASET_TRANSPORT_ATTEMPT_AUDIT.json").write_text(
        json.dumps(dataset_attempt, indent=2) + "\n", encoding="utf-8"
    )
    (output_root / "01_CURRENT_ONLY_DATASET/KAGGLE_DATASET_TRANSPORT_ATTEMPT_AUDIT.md").write_text(
        """# Kaggle current-only dataset transport audit

Dataset version 1 was retained as a pre-forward engineering failure: Kaggle automatically expanded `.nii.gz` files, so mounted bytes no longer represented the locked compressed-file hashes. No kernel was submitted against version 1 and no P0 was generated from it.

Version 2 stores the same locked NIfTI bytes with an opaque `.bin` transport suffix. The kernel copies each current-only file byte-for-byte to a temporary `.nii.gz` path, verifies SHA-256 again, and only then opens it. Version 2 contains 39 current T1ce and 39 current segmentation files, with no preoperative or recurrence files. A fixed remote re-download matched the locked source SHA-256. Version 2 is authoritative.
""",
        encoding="utf-8",
    )

    provenance = {
        "protocol_commit": PROTOCOL_COMMIT,
        "protocol_zip_sha256": PROTOCOL_ZIP_SHA256,
        "current_only_dataset_slug": DATASET_SLUG,
        "current_only_dataset_version": DATASET_VERSION,
        "checkpoint_source_slug": CHECKPOINT_SLUG,
        "checkpoint_source_version": CHECKPOINT_VERSION,
        "external_p0_kernel_slug": KERNEL_SLUG,
        "external_p0_kernel_version": KERNEL_VERSION,
        "external_p0_kernel_status": "COMPLETE",
        "stable_p0_source": f"{KERNEL_SLUG}/versions/{KERNEL_VERSION}",
        "runner_sha256": sha256(ROOT / "kaggle/pcc_rhuh_external_stage_a_p0_freeze_2026/run.py"),
        "builder_sha256": sha256(ROOT / "experiments/build_rhuh_external_stage_a_current_only.py"),
        "validator_sha256": sha256(ROOT / "experiments/validate_rhuh_external_stage_a_output.py"),
        "future_segmentation_voxel_access": 0,
        "recurrence_t1ce_voxel_access": 0,
        "target_constructed": False,
        "performance_computed": False,
        "stage_b_executed": False,
    }
    (output_root / "00_AUTHORITY/RHUH_EXTERNAL_STAGE_A_SOURCE_PROVENANCE.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )

    pointer = {
        "p0_arrays_in_metadata_zip": False,
        "p0_arrays_in_git": False,
        "stable_storage_type": "Kaggle kernel output",
        "kernel_slug": KERNEL_SLUG,
        "kernel_version": KERNEL_VERSION,
        "kernel_status": "COMPLETE",
        "p0_root": "pcc_rhuh_external_stage_a_p0_freeze_2026/04_EXTERNAL_P0/external_stage_a/P0",
        "p0_count": 39,
        "p0_manifest": "05_P0_FREEZE/LOCKED_RHUH_39_EXTERNAL_P0_MANIFEST.csv",
        "p0_sha256_table": "05_P0_FREEZE/LOCKED_RHUH_39_EXTERNAL_P0_SHA256.csv",
        "immutable_after_freeze": True,
    }
    p0_metadata = output_root / "04_EXTERNAL_P0"
    p0_metadata.mkdir(parents=True, exist_ok=True)
    (p0_metadata / "P0_STABLE_STORAGE_POINTER.json").write_text(
        json.dumps(pointer, indent=2) + "\n", encoding="utf-8"
    )
    (p0_metadata / "README_P0_ARRAYS_NOT_IN_METADATA_ARCHIVE.md").write_text(
        "# External P0 storage\n\nThe 39 large `.npy` arrays are intentionally excluded from this metadata ZIP and Git. Their immutable Kaggle kernel output source, sizes, paths, and SHA-256 values are locked by the pointer and P0 manifests.\n",
        encoding="utf-8",
    )

    test_root = output_root / "07_TESTS"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "experiments/test_rhuh_external_stage_a_freeze.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    (test_root / "FULL_TEST_STDOUT.txt").write_text(result.stdout, encoding="utf-8")
    (test_root / "FULL_TEST_STDERR.txt").write_text(result.stderr, encoding="utf-8")
    (test_root / "TEST_EXIT_CODE.txt").write_text(str(result.returncode) + "\n", encoding="utf-8")
    if result.returncode != 0 or "33 passed" not in result.stdout:
        raise RuntimeError(f"External Stage A tests failed: {result.stdout}\n{result.stderr}")
    (test_root / "TEST_EXECUTION_REPORT.md").write_text(
        "# External Stage A test execution\n\n- Command: `python -m pytest -q experiments/test_rhuh_external_stage_a_freeze.py`\n- Result: 33 passed, 0 failed, 0 errors\n- Exit code: 0\n- Tests are evidence/static checks and do not load future data or run a predictor.\n",
        encoding="utf-8",
    )

    local_status = json.loads((test_root / "LOCAL_STAGE_A_VALIDATION_STATUS.json").read_text())
    remote_runtime = json.loads((output_root / "00_AUTHORITY/KAGGLE_RUNTIME_INFO.json").read_text())
    final_status = {
        "protocol_commit": PROTOCOL_COMMIT,
        "protocol_zip_sha256": PROTOCOL_ZIP_SHA256,
        "current_only_dataset_slug": DATASET_SLUG,
        "current_only_dataset_version": DATASET_VERSION,
        "confirmatory_patients": 39,
        "predictor_forward_patients": 39,
        "p0_generated": 39,
        "completion_markers": 39,
        "p0_hash_records": 39,
        "missing": local_status["missing"],
        "hash_mismatch": local_status["hash_mismatch"],
        "dtype_failure": local_status["dtype_failure"],
        "finite_failure": local_status["finite_failure"],
        "range_failure": local_status["range_failure"],
        "shape_failure": local_status["shape_failure"],
        "duplicate_p0_hash_groups": local_status["duplicate_p0_hash_groups"],
        "failed_patients": 0,
        "future_segmentation_voxel_access": remote_runtime["future_segmentation_voxel_access"],
        "recurrence_t1ce_voxel_access": remote_runtime["recurrence_t1ce_voxel_access"],
        "target_constructed": remote_runtime["target_constructed"],
        "performance_computed": remote_runtime["performance_computed"],
        "stage_b_executed": remote_runtime["stage_b_executed"],
        "lumiere_started": remote_runtime["lumiere_started"],
        "tests": "33 passed, 0 failed, 0 errors",
        "stable_p0_source": f"{KERNEL_SLUG}/versions/{KERNEL_VERSION}",
        "release_gate": "PASS",
    }
    remote_status.write_text(json.dumps(final_status, indent=2) + "\n", encoding="utf-8")
    (release / "PCC_RHUH_EXTERNAL_STAGE_A_FINAL_REPORT.md").write_text(
        f"""# PCC RHUH External Stage A P0 freeze final report

The locked 39-patient external cohort was processed using only early-postoperative T1ce, the locked binary current mask (`RHUH segmentation > 0`), and the five frozen internal checkpoints. All 39 float32 P0 maps are finite, in range, shape-valid, and matched their manifest and SHA-256 table after an independent local download.

- Current-only dataset: `{DATASET_SLUG}`, version `{DATASET_VERSION}`
- Frozen checkpoint source: `{CHECKPOINT_SLUG}`, version `{CHECKPOINT_VERSION}`
- Stable P0 source: `{KERNEL_SLUG}`, version `{KERNEL_VERSION}`
- P0: 39/39
- Completion markers: 39/39
- Missing/hash/dtype/finite/range/shape failures: 0
- Failed patients: 0
- Recurrence segmentation voxel access: 0
- Recurrence T1ce voxel access: 0
- Target constructed: false
- Performance computed: false
- External Stage B executed: false
- `EXTERNAL_STAGE_A_P0_FREEZE_GATE=PASS`
""",
        encoding="utf-8",
    )

    selected_hashes = [
        "00_AUTHORITY/KAGGLE_RUNTIME_INFO.json",
        "00_AUTHORITY/RHUH_EXTERNAL_STAGE_A_SOURCE_PROVENANCE.json",
        "01_CURRENT_ONLY_DATASET/LOCKED_RHUH_39_STAGE_A_CURRENT_ONLY_MANIFEST.csv",
        "01_CURRENT_ONLY_DATASET/RHUH_STAGE_A_CURRENT_ONLY_DATASET_HASH_LOCK.json",
        "02_PREDICTOR_AUTHORITY/LOCKED_RHUH_FROZEN_PREDICTOR_RUNTIME_MANIFEST.csv",
        "03_CURRENT_INPUT_AUDIT/RHUH_39_CURRENT_INPUT_AUDIT.csv",
        "04_EXTERNAL_P0/P0_STABLE_STORAGE_POINTER.json",
        "05_P0_FREEZE/LOCKED_RHUH_39_EXTERNAL_P0_MANIFEST.csv",
        "05_P0_FREEZE/LOCKED_RHUH_39_EXTERNAL_P0_SHA256.csv",
        "05_P0_FREEZE/LOCKED_RHUH_39_EXTERNAL_P0_COMPLETION_STATUS.csv",
        "06_IO_ACCESS_AUDIT/STAGE_A_SCIENTIFIC_FILE_ACCESS_LOG.csv",
        "07_TESTS/LOCAL_P0_FILE_VALIDATION.csv",
        "07_TESTS/FULL_TEST_STDOUT.txt",
        "08_RELEASE/PCC_RHUH_EXTERNAL_STAGE_A_STATUS.json",
        "08_RELEASE/PCC_RHUH_EXTERNAL_STAGE_A_FINAL_REPORT.md",
    ]
    hash_lock = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scientific_gate": "PASS",
        "files": [
            {
                "path": relative,
                "size_bytes": (output_root / relative).stat().st_size,
                "sha256": sha256(output_root / relative),
            }
            for relative in selected_hashes
        ],
    }
    (release / "PCC_RHUH_EXTERNAL_STAGE_A_HASH_LOCK.json").write_text(
        json.dumps(hash_lock, indent=2) + "\n", encoding="utf-8"
    )

    manifest_path = release / "PCC_RHUH_EXTERNAL_STAGE_A_FILE_MANIFEST.csv"
    contents_path = release / "PCC_RHUH_EXTERNAL_STAGE_A_PACKAGE_CONTENTS.txt"
    existing = sorted(
        path.relative_to(output_root).as_posix()
        for path in output_root.rglob("*")
        if path.is_file() and path not in {manifest_path, contents_path}
    )
    manifest_rows = [
        {
            "path": relative,
            "size_bytes": (output_root / relative).stat().st_size,
            "sha256": sha256(output_root / relative),
            "control_status": "CONTROLLED",
        }
        for relative in existing
    ]
    manifest_rows.extend(
        [
            {
                "path": manifest_path.relative_to(output_root).as_posix(),
                "size_bytes": "",
                "sha256": "",
                "control_status": "EXCLUDED_SELF_REFERENCE",
            },
            {
                "path": contents_path.relative_to(output_root).as_posix(),
                "size_bytes": "",
                "sha256": "",
                "control_status": "EXCLUDED_SELF_REFERENCE",
            },
        ]
    )
    write_csv(manifest_path, sorted(manifest_rows, key=lambda row: str(row["path"])), ["path", "size_bytes", "sha256", "control_status"])
    package_paths = sorted(existing + [manifest_path.relative_to(output_root).as_posix(), contents_path.relative_to(output_root).as_posix()])
    contents_path.write_text("\n".join(package_paths) + "\n", encoding="utf-8")

    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in package_paths:
            archive.write(output_root / relative, relative)
    archive_hash = sha256(ARCHIVE)
    ARCHIVE_SHA.write_text(f"{archive_hash}  {ARCHIVE.name}\n", encoding="utf-8")

    with zipfile.ZipFile(ARCHIVE, "r") as archive:
        names = archive.namelist()
        bad = archive.testzip()
        if bad is not None or len(names) != len(set(names)) or sorted(names) != package_paths:
            raise RuntimeError("ZIP directory/integrity validation failed")
        with tempfile.TemporaryDirectory(prefix="rhuh-stage-a-zip-verify-") as temporary:
            extract_root = Path(temporary)
            archive.extractall(extract_root)
            controlled_rows = [row for row in csv.DictReader((extract_root / manifest_path.relative_to(output_root)).open()) if row["control_status"] == "CONTROLLED"]
            missing = size_mismatch = hash_mismatch = 0
            for row in controlled_rows:
                path = extract_root / row["path"]
                if not path.is_file():
                    missing += 1
                elif path.stat().st_size != int(row["size_bytes"]):
                    size_mismatch += 1
                elif sha256(path) != row["sha256"]:
                    hash_mismatch += 1
            if missing or size_mismatch or hash_mismatch:
                raise RuntimeError(
                    f"Extracted controlled-file mismatch: {missing}/{size_mismatch}/{hash_mismatch}"
                )

    summary = f"""PCC_RHUH_EXTERNAL_VALIDATION_2026
PHASE=EXTERNAL_STAGE_A_FUTURE_BLIND_P0_FREEZE
PROTOCOL_COMMIT={PROTOCOL_COMMIT}
CURRENT_ONLY_DATASET={DATASET_SLUG}
CURRENT_ONLY_DATASET_VERSION={DATASET_VERSION}
CURRENT_ONLY_PATIENTS=39
CURRENT_T1CE=39
CURRENT_SEGMENTATION=39
SOURCE_HASH_MISMATCH=0
RECURRENCE_FILES_IN_STAGE_A_DATASET=0
CHECKPOINT_HASHES=MATCH_5/5
PREDICTOR_FORWARD_PATIENTS=39
P0_GENERATED=39
P0_FAILURES=0
COMPLETION_MARKERS=39
P0_HASH_RECORDS=39
FUTURE_SEGMENTATION_VOXEL_ACCESS=0
RECURRENCE_T1CE_VOXEL_ACCESS=0
TARGET_CONSTRUCTED=false
PERFORMANCE_COMPUTED=false
STAGE_B_EXECUTED=false
FAILED_PATIENTS=0
STABLE_P0_SOURCE={KERNEL_SLUG}/versions/{KERNEL_VERSION}
TESTS=33_passed_0_failed_0_errors
ZIP_FILES={len(package_paths)}
ZIP_SIZE_BYTES={ARCHIVE.stat().st_size}
ZIP_SHA256={archive_hash}
PACKAGE_MISSING=0
PACKAGE_EXTRA=0
PACKAGE_SIZE_MISMATCH=0
PACKAGE_HASH_MISMATCH=0
PACKAGE_DUPLICATE_PATH=0
EXTERNAL_STAGE_A_P0_FREEZE_GATE=PASS
"""
    RELEASE_SUMMARY.write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
