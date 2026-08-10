#!/usr/bin/env python3
"""Build the physically isolated RHUH External Stage A current-only dataset.

This utility performs byte-for-byte copies only. It does not load NIfTI voxel
arrays and never resolves or copies preoperative or recurrence files.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_ROOT = ROOT / "outputs/pcc_rhuh_external_protocol_lock_2026"
LOCKED_MANIFEST = (
    PROTOCOL_ROOT
    / "01_COHORT_LOCK/LOCKED_RHUH_39_EXTERNAL_CONFIRMATORY_CASE_MANIFEST.csv"
)
OUTPUT_ROOT = ROOT / "outputs/pcc_rhuh_external_stage_a_p0_freeze_2026"
DATASET_ROOT = ROOT / "artifacts/pcc_rhuh_stage_a_current_only_2026"
DATASET_SLUG = "jeechangxin/pcc-rhuh-stage-a-current-only-2026"
PROTOCOL_COMMIT = "6c8bf164f8e445123143db08c34f0f66a1e21226"
PROTOCOL_ZIP_SHA256 = "2ac4378b279854a5497185176e9cd776da8207aab04dd4617cb310080fbad059"

CURRENT_MANIFEST_FIELDS = [
    "patient_id",
    "case_id",
    "current_timepoint",
    "current_t1ce_path",
    "current_t1ce_sha256",
    "current_segmentation_path",
    "current_segmentation_sha256",
    "current_mask_mapping",
    "planned_external_p0_relative_path",
]

DATASET_MANIFEST_FIELDS = [
    "patient_id",
    "case_id",
    "file_type",
    "dataset_relative_path",
    "source_relative_path",
    "size_bytes",
    "expected_sha256",
    "copied_sha256",
    "hash_status",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def require_new_directory(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing directory: {path}")
    path.mkdir(parents=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument(
        "--transport-suffix",
        default="",
        help="Optional opaque suffix that prevents host-side archive expansion.",
    )
    parser.add_argument(
        "--audit-subdir",
        default="",
        help="Optional subdirectory below 01_CURRENT_ONLY_DATASET for a retained attempt.",
    )
    args = parser.parse_args()

    dataset_root = args.dataset_root.resolve()
    output_root = args.output_root.resolve()
    require_new_directory(dataset_root)
    output_root.mkdir(parents=True, exist_ok=True)

    protocol_zip = ROOT / "PCC_RHUH_EXTERNAL_PROTOCOL_LOCK_2026.zip"
    if sha256(protocol_zip) != PROTOCOL_ZIP_SHA256:
        raise RuntimeError("Protocol ZIP SHA-256 mismatch")

    with LOCKED_MANIFEST.open(newline="", encoding="utf-8") as handle:
        locked_rows = list(csv.DictReader(handle))
    if len(locked_rows) != 39:
        raise RuntimeError("Locked external cohort is not exactly 39 rows")
    if len({row["patient_id"] for row in locked_rows}) != 39:
        raise RuntimeError("Locked external cohort patient IDs are not unique")
    if len({row["case_id"] for row in locked_rows}) != 39:
        raise RuntimeError("Locked external cohort case IDs are not unique")
    if any(row["patient_id"] == "RHUH-0008" for row in locked_rows):
        raise RuntimeError("Excluded patient RHUH-0008 is present")

    current_rows: list[dict[str, object]] = []
    file_rows: list[dict[str, object]] = []
    for row in locked_rows:
        patient_id = row["patient_id"]
        t1c_source = ROOT / row["current_t1ce_path"]
        seg_source = ROOT / row["current_segmentation_path"]
        t1c_name = t1c_source.name + args.transport_suffix
        seg_name = seg_source.name + args.transport_suffix
        t1c_copy = dataset_root / t1c_name
        seg_copy = dataset_root / seg_name

        for file_type, source, destination, expected in (
            ("CURRENT_T1CE", t1c_source, t1c_copy, row["current_t1ce_sha256"]),
            (
                "CURRENT_SEGMENTATION",
                seg_source,
                seg_copy,
                row["current_segmentation_sha256"],
            ),
        ):
            if not source.is_file():
                raise FileNotFoundError(source)
            source_hash = sha256(source)
            if source_hash != expected:
                raise RuntimeError(f"Locked source hash mismatch: {source}")
            shutil.copyfile(source, destination)
            copied_hash = sha256(destination)
            if copied_hash != source_hash:
                raise RuntimeError(f"Byte-for-byte copy hash mismatch: {destination}")
            file_rows.append(
                {
                    "patient_id": patient_id,
                    "case_id": row["case_id"],
                    "file_type": file_type,
                    "dataset_relative_path": destination.name,
                    "source_relative_path": source.relative_to(ROOT).as_posix(),
                    "size_bytes": destination.stat().st_size,
                    "expected_sha256": expected,
                    "copied_sha256": copied_hash,
                    "hash_status": "MATCH",
                }
            )

        current_rows.append(
            {
                "patient_id": patient_id,
                "case_id": row["case_id"],
                "current_timepoint": row["current_timepoint"],
                "current_t1ce_path": t1c_name,
                "current_t1ce_sha256": row["current_t1ce_sha256"],
                "current_segmentation_path": seg_name,
                "current_segmentation_sha256": row["current_segmentation_sha256"],
                "current_mask_mapping": row["current_mask_mapping"],
                "planned_external_p0_relative_path": row[
                    "planned_external_p0_relative_path"
                ],
            }
        )

    dataset_manifest = dataset_root / "LOCKED_RHUH_39_STAGE_A_CURRENT_ONLY_MANIFEST.csv"
    inventory = dataset_root / "RHUH_STAGE_A_CURRENT_ONLY_DATASET_MANIFEST.csv"
    write_csv(dataset_manifest, current_rows, CURRENT_MANIFEST_FIELDS)
    write_csv(inventory, file_rows, DATASET_MANIFEST_FIELDS)

    provenance = {
        "dataset_slug": DATASET_SLUG,
        "privacy": "private",
        "source_authority": "TCIA RHUH-GBM official NIfTI v1",
        "source_doi": "10.7937/4545-c905",
        "source_license": "CC BY 4.0",
        "source_patients": 40,
        "locked_current_only_patients": 39,
        "excluded_patient": "RHUH-0008",
        "copy_method": "byte-for-byte shutil.copyfile",
        "transport_suffix": args.transport_suffix,
        "nifti_resaved": False,
        "header_rewritten": False,
        "reorientation": False,
        "resampling": False,
        "registration": False,
        "interpolation": False,
        "preoperative_files_included": 0,
        "recurrence_t1ce_files_included": 0,
        "recurrence_segmentation_files_included": 0,
        "target_files_included": 0,
        "performance_files_included": 0,
        "protocol_commit": PROTOCOL_COMMIT,
        "protocol_zip_sha256": PROTOCOL_ZIP_SHA256,
    }
    provenance_path = dataset_root / "RHUH_STAGE_A_CURRENT_ONLY_SOURCE_PROVENANCE.json"
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")

    controlled = []
    for path in sorted(dataset_root.iterdir(), key=lambda item: item.name):
        if path.name in {
            "dataset-metadata.json",
            "RHUH_STAGE_A_CURRENT_ONLY_DATASET_HASH_LOCK.json",
        }:
            continue
        controlled.append(
            {
                "path": path.name,
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    hash_lock = {
        "dataset_slug": DATASET_SLUG,
        "controlled_file_count": len(controlled),
        "self_reference_policy": {
            "RHUH_STAGE_A_CURRENT_ONLY_DATASET_HASH_LOCK.json": "EXCLUDED_SELF_REFERENCE",
            "dataset-metadata.json": "KAGGLE_TRANSPORT_METADATA_NOT_SCIENTIFIC_INPUT",
        },
        "files": controlled,
        "gate": "PASS",
    }
    hash_lock_path = dataset_root / "RHUH_STAGE_A_CURRENT_ONLY_DATASET_HASH_LOCK.json"
    hash_lock_path.write_text(json.dumps(hash_lock, indent=2) + "\n", encoding="utf-8")

    metadata = {
        "title": "PCC RHUH Stage A Current Only 2026",
        "id": DATASET_SLUG,
        "licenses": [{"name": "CC-BY-4.0"}],
    }
    (dataset_root / "dataset-metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )

    current_output = output_root / "01_CURRENT_ONLY_DATASET"
    if args.audit_subdir:
        current_output = current_output / args.audit_subdir
    if current_output.exists():
        raise FileExistsError(f"Refusing to overwrite existing audit directory: {current_output}")
    current_output.mkdir(parents=True)
    for source in (dataset_manifest, inventory, provenance_path, hash_lock_path):
        shutil.copyfile(source, current_output / source.name)

    t1c_rows = [row for row in file_rows if row["file_type"] == "CURRENT_T1CE"]
    seg_rows = [
        row for row in file_rows if row["file_type"] == "CURRENT_SEGMENTATION"
    ]
    mismatch_count = sum(row["hash_status"] != "MATCH" for row in file_rows)
    audit = f"""# RHUH Stage A current-only dataset audit

- Patients: {len(current_rows)}
- Current T1ce files: {len(t1c_rows)}
- Current segmentation files: {len(seg_rows)}
- Source/copy SHA-256 mismatches: {mismatch_count}
- RHUH-0008 present: false
- Preoperative files: 0
- Recurrence T1ce files: 0
- Recurrence segmentation files: 0
- Target files: 0
- Performance files: 0
- NIfTI resave/header rewrite/reorientation/resampling/registration/interpolation: false
- Dataset privacy: private
- `CURRENT_ONLY_DATASET_GATE=PASS`
"""
    (current_output / "RHUH_STAGE_A_CURRENT_ONLY_DATASET_AUDIT.md").write_text(
        audit, encoding="utf-8"
    )
    status = {
        "patients": len(current_rows),
        "current_t1ce_files": len(t1c_rows),
        "current_segmentation_files": len(seg_rows),
        "source_hash_mismatch": mismatch_count,
        "excluded_patient_present": False,
        "preoperative_files": 0,
        "recurrence_t1ce_files": 0,
        "recurrence_segmentation_files": 0,
        "target_files": 0,
        "performance_files": 0,
        "gate": "PASS",
    }
    (current_output / "CURRENT_ONLY_DATASET_GATE_STATUS.json").write_text(
        json.dumps(status, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
