"""CPU-only protocol-lock preflight for the 115-patient holdout.

This script performs only cohort indexing, deterministic pair selection,
NIfTI geometry/target eligibility checks, P0-manifest construction, and
checkpoint-file hash verification. It never imports torch, loads a model,
creates P0, or computes method metrics.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd

CHECKPOINTS = [
    ("fold_1", "best_training_loss.pt", "bb86bcdbde7e0e4a41f5700efd8c532f2a06d3a3d9bde183f0090238a277b18c"),
    ("fold_2", "best_training_loss.pt", "fb75fc2dc1d6703e22ca7ef260a54a0563a184c5a295c0890279c51cb054e759"),
    ("fold_3", "best_training_loss.pt", "3e2cb75c84fb861b82789d2bf87517ee494c3435e1b06d64c739437dce547107"),
    ("fold_4", "best_training_loss.pt", "28656b1d282fc66e054887166a990810b25d7e6a66d9c21e8f3951868f7291c3"),
    ("fold_5", "best_training_loss.pt", "69250135d3eef595b9244426f511c165f10635e1a56241f8fa372959d874c1f3"),
]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def tp_number(path: Path) -> int:
    match = re.search(r"Timepoint_(\d+)", path.name)
    return int(match.group(1)) if match else -1


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, default=Path("/kaggle/input"))
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.input_root
    out = args.output_root
    out.mkdir(parents=True, exist_ok=True)

    manifests = sorted(root.rglob("LOCKED_CASE_MANIFEST.csv"))
    if not manifests:
        raise RuntimeError("40-case LOCKED_CASE_MANIFEST.csv not found in mounted inputs")
    locked_40 = pd.read_csv(manifests[0])
    locked_patients = set(locked_40["patient_id"].astype(str))
    datasets = sorted(p for p in root.rglob("MU-Glioma-Post") if p.is_dir() and any(p.glob("PatientID_*")))
    if len(datasets) != 1:
        raise RuntimeError(f"expected one MU-Glioma-Post root, found {datasets}")
    dataset = datasets[0]

    all_patients: list[dict[str, object]] = []
    eligible: list[dict[str, object]] = []
    for patient in sorted(dataset.glob("PatientID_*")):
        timepoints = sorted(patient.glob("Timepoint_*"), key=tp_number)
        usable = []
        for timepoint in timepoints:
            t1c = list(timepoint.glob("*_brain_t1c.nii"))
            mask = list(timepoint.glob("*_tumorMask.nii"))
            if len(t1c) == len(mask) == 1:
                usable.append((timepoint, t1c[0], mask[0]))
        all_patients.append({"patient_id": patient.name, "timepoint_count": len(timepoints), "usable_timepoint_count": len(usable)})
        if len(usable) < 2:
            continue
        current, future = usable[0], usable[1]
        images = [nib.load(str(path)) for path in (current[1], current[2], future[2])]
        compatible = all(
            image.shape == images[0].shape
            and np.allclose(image.affine, images[0].affine, rtol=0, atol=1e-5)
            and nib.aff2axcodes(image.affine) == nib.aff2axcodes(images[0].affine)
            for image in images[1:]
        )
        current_mask = images[1].get_fdata() > 0.5
        future_mask = images[2].get_fdata() > 0.5
        target = future_mask & ~current_mask
        case_id = f"{patient.name}_T{tp_number(current[0])}_to_T{tp_number(future[0])}_t1c"
        eligible.append({
            "patient_id": patient.name, "case_id": case_id,
            "current_timepoint": current[0].name, "future_timepoint": future[0].name,
            "current_t1c_path": str(current[1]), "current_mask_path": str(current[2]),
            "future_mask_path": str(future[2]), "current_t1c_shape": str(images[0].shape),
            "current_mask_shape": str(images[1].shape), "future_mask_shape": str(images[2].shape),
            "affine_match": bool(compatible), "orientation_match": bool(nib.aff2axcodes(images[0].affine) == nib.aff2axcodes(images[1].affine) == nib.aff2axcodes(images[2].affine)),
            "spacing_match": bool(np.allclose(images[0].header.get_zooms()[:3], images[1].header.get_zooms()[:3], rtol=0, atol=1e-5) and np.allclose(images[0].header.get_zooms()[:3], images[2].header.get_zooms()[:3], rtol=0, atol=1e-5)),
            "target_nonempty": bool(target.any()), "target_voxel_count": int(target.sum()),
            "current_mask_voxel_count": int(current_mask.sum()), "future_mask_voxel_count": int(future_mask.sum()),
            "pair_selection_rule": "earliest two usable timepoints; patient_id ascending for cohort lock",
            "pair_selection_rank": len(eligible) + 1,
            "overlap_with_locked_40": patient.name in locked_patients,
            "eligibility_status": "ELIGIBLE" if compatible and current_mask.any() and future_mask.any() and target.any() else "INELIGIBLE",
            "exclusion_reason": "" if compatible and current_mask.any() and future_mask.any() and target.any() else "GEOMETRY_OR_EMPTY_MASK_OR_TARGET",
        })

    eligible = sorted(eligible, key=lambda row: str(row["patient_id"]))
    for rank, row in enumerate(eligible, 1):
        row["pair_selection_rank"] = rank
    locked_115 = [row for row in eligible if row["patient_id"] not in locked_patients and row["eligibility_status"] == "ELIGIBLE"]
    if len(locked_115) != 115:
        raise RuntimeError(f"hard cohort blocker: expected 115 remaining eligible patients, found {len(locked_115)}")
    if len({row["patient_id"] for row in locked_115}) != 115:
        raise RuntimeError("hard cohort blocker: patient identity is not unique")

    write_csv(out / "ALL_SOURCE_PATIENTS.csv", all_patients)
    write_csv(out / "ALL_ELIGIBLE_PATIENT_LEVEL_PAIRS.csv", eligible)
    write_csv(out / "LOCKED_115_CASE_MANIFEST.csv", locked_115)
    write_csv(out / "LOCKED_40_PATIENT_IDS.csv", [{"patient_id": x} for x in sorted(locked_patients)])
    p0_rows = []
    for index, row in enumerate(locked_115):
        p0_rows.append({k: row[k] for k in ("patient_id", "case_id", "current_timepoint", "current_t1c_path", "current_mask_path", "current_t1c_shape", "current_mask_shape") } | {"output_p0_path": f"P0/{row['case_id']}.npy", "shard": index % 4})
    write_csv(out / "P0_INFERENCE_MANIFEST.csv", p0_rows)

    checkpoint_rows = []
    for fold, name, expected in CHECKPOINTS:
        matches = sorted(root.rglob(name))
        matches = [p for p in matches if p.is_file()]
        verified = [p for p in matches if digest(p) == expected]
        checkpoint_rows.append({"fold": fold, "file_name": name, "expected_sha256": expected, "matching_paths": ";".join(map(str, verified)), "status": "PASS" if len(verified) == 1 else "FAIL"})
    write_csv(out / "CHECKPOINT_HASH_PRECHECK.csv", checkpoint_rows)
    if not all(row["status"] == "PASS" for row in checkpoint_rows):
        raise RuntimeError("hard checkpoint blocker: one or more frozen checkpoint hashes unavailable or mismatched")
    (out / "PREFLIGHT_STATUS.json").write_text(json.dumps({"status": "PASS", "model_forward_executed": False, "p0_generated": False, "method_metrics_computed": False, "locked_40_patient_count": len(locked_patients), "locked_115_patient_count": len(locked_115), "patient_overlap": len(locked_patients & {row['patient_id'] for row in locked_115})}, indent=2) + "\n")


if __name__ == "__main__":
    main()
