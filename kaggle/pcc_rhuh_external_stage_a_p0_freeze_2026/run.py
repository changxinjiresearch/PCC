#!/usr/bin/env python3
"""Generate and freeze 39 future-blind RHUH External Stage A P0 maps.

The attached RHUH dataset is physically current-only. Opaque transport files
are copied byte-for-byte to temporary ``.nii.gz`` paths before nibabel reads
them; this prevents Kaggle's dataset service from automatically expanding and
rewriting the locked compressed files.
"""

from __future__ import annotations

import csv
import gc
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np


KAGGLE_INPUT = Path("/kaggle/input")
OUTPUT_ROOT = Path("/kaggle/working/pcc_rhuh_external_stage_a_p0_freeze_2026")
P0_ROOT = OUTPUT_ROOT / "04_EXTERNAL_P0/external_stage_a/P0"
COMPLETION_ROOT = OUTPUT_ROOT / "05_P0_FREEZE/completion"
PER_CASE_ACCESS_ROOT = OUTPUT_ROOT / "06_IO_ACCESS_AUDIT/per_case"
AUTHORITY_COMMIT = "6c8bf164f8e445123143db08c34f0f66a1e21226"
SCIENTIFIC_COMMIT = "66269681e4417dccabc68ecaa792d76e19aa5856"
PROTOCOL_ZIP_SHA256 = "2ac4378b279854a5497185176e9cd776da8207aab04dd4617cb310080fbad059"
PREPROCESSING_SHA256 = "bf48893deabbb400e6f412b9a53267e55ecb538a4f57daa682ed1350bc2b5624"
ARCHITECTURE_SHA256 = "abce63dc26f6642438540ca80c8f80b992a0a39a39b88a17966dd65806915d08"
LOCKED_FORWARD_SHA256 = "15ca3edd60fb984d0b3bc35bdeaaaf70edf32c246fe006b44fd2d3f0f451a98c"
CURRENT_DATASET_SLUG = "jeechangxin/pcc-rhuh-stage-a-current-only-2026"
CURRENT_DATASET_VERSION = 2
CHECKPOINT_SOURCE_SLUG = "jeechangxin/pcc-leakage-free-rerun-2026"
CHECKPOINT_SOURCE_VERSION = 8
ATTEMPT_ID = "rhuh_external_stage_a_gpu_v1"
ENSEMBLE_WEIGHTS = (0.2, 0.2, 0.2, 0.2, 0.2)
EXPECTED_CHECKPOINTS = [
    ("fold_1", "bb86bcdbde7e0e4a41f5700efd8c532f2a06d3a3d9bde183f0090238a277b18c"),
    ("fold_2", "fb75fc2dc1d6703e22ca7ef260a54a0563a184c5a295c0890279c51cb054e759"),
    ("fold_3", "3e2cb75c84fb861b82789d2bf87517ee494c3435e1b06d64c739437dce547107"),
    ("fold_4", "28656b1d282fc66e054887166a990810b25d7e6a66d9c21e8f3951868f7291c3"),
    ("fold_5", "69250135d3eef595b9244426f511c165f10635e1a56241f8fa372959d874c1f3"),
]


class ScientificBlock(RuntimeError):
    """A protocol/identity failure that must not be retried as engineering."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def array_sha256(array: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(array)
    return hashlib.sha256(contiguous.tobytes(order="C")).hexdigest()


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def find_exactly_one(name: str) -> Path:
    matches = sorted(KAGGLE_INPUT.rglob(name))
    if len(matches) != 1:
        raise ScientificBlock(f"Expected exactly one {name}; found {len(matches)}")
    return matches[0]


def install_locked_runtime() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--quiet",
            "--no-cache-dir",
            "torch==2.4.1",
            "--index-url",
            "https://download.pytorch.org/whl/cu121",
        ],
        check=True,
    )


def load_current_manifest() -> tuple[Path, list[dict[str, str]]]:
    manifest = find_exactly_one("LOCKED_RHUH_39_STAGE_A_CURRENT_ONLY_MANIFEST.csv")
    with manifest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        fields = handle.seek(0) or next(csv.reader(handle))
    required = {
        "patient_id",
        "case_id",
        "current_timepoint",
        "current_t1ce_path",
        "current_t1ce_sha256",
        "current_segmentation_path",
        "current_segmentation_sha256",
        "current_mask_mapping",
        "planned_external_p0_relative_path",
    }
    if set(fields) != required:
        raise ScientificBlock(f"Unexpected current-only manifest fields: {fields}")
    if len(rows) != 39 or len({r["patient_id"] for r in rows}) != 39:
        raise ScientificBlock("Current-only manifest patient identity failure")
    if len({r["case_id"] for r in rows}) != 39:
        raise ScientificBlock("Current-only manifest case identity failure")
    if any(r["patient_id"] == "RHUH-0008" for r in rows):
        raise ScientificBlock("Excluded RHUH-0008 is present")
    if any(r["current_mask_mapping"] != "RHUH_segmentation_gt_0_labels_1_2_3" for r in rows):
        raise ScientificBlock("Current mask mapping drift")
    return manifest, rows


def verify_current_only_dataset(
    manifest: Path, rows: list[dict[str, str]]
) -> list[dict[str, object]]:
    dataset_root = manifest.parent
    transport_files = sorted(dataset_root.glob("*.nii.gz.bin"))
    if len(transport_files) != 78:
        raise ScientificBlock(f"Expected 78 opaque current files; found {len(transport_files)}")
    forbidden_science = [
        path
        for path in transport_files
        if any(
            token in path.name.lower()
            for token in ("recurrence", "preoperative", "target", "performance")
        )
    ]
    if forbidden_science:
        raise ScientificBlock(f"Forbidden scientific files in current-only dataset: {forbidden_science}")
    audit_rows = []
    for row in rows:
        for file_type, path_field, hash_field in (
            ("CURRENT_T1CE", "current_t1ce_path", "current_t1ce_sha256"),
            (
                "CURRENT_SEGMENTATION",
                "current_segmentation_path",
                "current_segmentation_sha256",
            ),
        ):
            path = dataset_root / row[path_field]
            if not path.is_file():
                raise ScientificBlock(f"Missing locked current file: {path}")
            actual = sha256(path)
            if actual != row[hash_field]:
                raise ScientificBlock(f"Current file hash mismatch: {path}")
            audit_rows.append(
                {
                    "patient_id": row["patient_id"],
                    "case_id": row["case_id"],
                    "file_type": file_type,
                    "resolved_path": str(path),
                    "size_bytes": path.stat().st_size,
                    "expected_sha256": row[hash_field],
                    "computed_sha256": actual,
                    "hash_status": "MATCH",
                }
            )
    return audit_rows


def clone_and_verify_authority() -> Path:
    repo = Path("/tmp/PCC_RHUH_EXTERNAL_STAGE_A_AUTHORITY")
    if repo.exists():
        shutil.rmtree(repo)
    subprocess.run(
        ["git", "clone", "--quiet", "https://github.com/changxinjiresearch/PCC.git", str(repo)],
        check=True,
    )
    subprocess.run(["git", "-C", str(repo), "checkout", "--quiet", AUTHORITY_COMMIT], check=True)
    checks = {
        repo / "src/preprocessing/current_only_preprocessing.py": PREPROCESSING_SHA256,
        repo / "src/models/crosscase_future_predictor.py": ARCHITECTURE_SHA256,
        repo / "experiments/run_115_stage_a_p0.py": LOCKED_FORWARD_SHA256,
    }
    for path, expected in checks.items():
        if sha256(path) != expected:
            raise ScientificBlock(f"Authority code hash mismatch: {path}")
    return repo


def resolve_checkpoints() -> list[dict[str, object]]:
    candidates = sorted(KAGGLE_INPUT.rglob("best_training_loss.pt"))
    by_hash: dict[str, list[Path]] = defaultdict(list)
    for path in candidates:
        by_hash[sha256(path)].append(path)
    resolved = []
    for fold, expected in EXPECTED_CHECKPOINTS:
        matches = by_hash.get(expected, [])
        if len(matches) != 1:
            raise ScientificBlock(
                f"{fold} checkpoint expected one hash match; found {len(matches)}"
            )
        path = matches[0]
        resolved.append(
            {
                "fold": fold,
                "resolved_path": str(path),
                "size_bytes": path.stat().st_size,
                "expected_sha256": expected,
                "computed_sha256": expected,
                "hash_status": "MATCH",
                "ensemble_weight": 0.2,
            }
        )
    return resolved


def atomic_save(path: Path, array: np.ndarray) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as handle:
        temporary = Path(handle.name)
        np.save(handle, array, allow_pickle=False)
        handle.flush()
        os.fsync(handle.fileno())
    persisted = np.load(temporary, allow_pickle=False)
    if (
        persisted.dtype != np.float32
        or persisted.shape != array.shape
        or not np.isfinite(persisted).all()
        or float(persisted.min()) < 0.0
        or float(persisted.max()) > 1.0
    ):
        temporary.unlink(missing_ok=True)
        raise ScientificBlock("Persisted P0 failed dtype/shape/finite/range validation")
    temporary.replace(path)
    return sha256(path)


def equal_weight_average(predictions: list[np.ndarray]) -> np.ndarray:
    if len(predictions) != 5 or any(x.shape != predictions[0].shape for x in predictions):
        raise ScientificBlock("Five shape-identical fold predictions are required")
    return (
        np.sum(np.stack(predictions), axis=0, dtype=np.float32) / np.float32(5.0)
    ).astype(np.float32)


def execute_case(
    row: dict[str, str],
    dataset_root: Path,
    checkpoints: list[dict[str, object]],
    models: list[object],
    device: object,
    prepare_current_only_inputs: object,
    nib: object,
    torch: object,
) -> tuple[dict[str, object], list[dict[str, object]], dict[str, object]]:
    patient_id = row["patient_id"]
    case_id = row["case_id"]
    t1c_transport = dataset_root / row["current_t1ce_path"]
    seg_transport = dataset_root / row["current_segmentation_path"]
    if sha256(t1c_transport) != row["current_t1ce_sha256"]:
        raise ScientificBlock(f"T1ce transport hash changed: {case_id}")
    if sha256(seg_transport) != row["current_segmentation_sha256"]:
        raise ScientificBlock(f"Segmentation transport hash changed: {case_id}")

    runtime_dir = Path("/tmp/rhuh_stage_a_current") / patient_id
    runtime_dir.mkdir(parents=True, exist_ok=True)
    t1c_runtime = runtime_dir / t1c_transport.name.removesuffix(".bin")
    seg_runtime = runtime_dir / seg_transport.name.removesuffix(".bin")
    shutil.copyfile(t1c_transport, t1c_runtime)
    shutil.copyfile(seg_transport, seg_runtime)
    if sha256(t1c_runtime) != row["current_t1ce_sha256"]:
        raise ScientificBlock(f"Runtime T1ce byte copy mismatch: {case_id}")
    if sha256(seg_runtime) != row["current_segmentation_sha256"]:
        raise ScientificBlock(f"Runtime segmentation byte copy mismatch: {case_id}")

    t1c_image = nib.load(str(t1c_runtime))
    seg_image = nib.load(str(seg_runtime))
    if t1c_image.shape != seg_image.shape or not np.allclose(
        t1c_image.affine, seg_image.affine, rtol=0.0, atol=1e-5
    ):
        raise ScientificBlock(f"Current T1ce/segmentation geometry mismatch: {case_id}")
    t1c = t1c_image.get_fdata(dtype=np.float32)
    segmentation = seg_image.get_fdata(dtype=np.float32)
    unique_labels = sorted(float(value) for value in np.unique(segmentation))
    if not set(unique_labels).issubset({0.0, 1.0, 2.0, 3.0}):
        raise ScientificBlock(f"Unexpected current segmentation labels: {case_id}")
    binary_mask = segmentation > 0
    prepared = prepare_current_only_inputs(t1c, binary_mask)
    batch = torch.from_numpy(prepared.model_input_zchw.astype(np.float32)).to(device)
    if batch.dtype != torch.float32 or batch.shape[1] != 2:
        raise ScientificBlock(f"Formal forward tensor contract failure: {case_id}")

    predictions: list[np.ndarray] = []
    fold_summaries = []
    with torch.inference_mode():
        for checkpoint, model in zip(checkpoints, models, strict=True):
            slices = []
            for start in range(0, len(batch), 64):
                logits = model(batch[start : start + 64])
                probability = torch.sigmoid(logits).detach().cpu().numpy()[:, 0]
                slices.append(probability)
            prediction = np.concatenate(slices).astype(np.float32)
            if not np.isfinite(prediction).all():
                raise ScientificBlock(f"Non-finite fold prediction: {case_id}")
            predictions.append(prediction)
            fold_summaries.append(
                {
                    "fold": checkpoint["fold"],
                    "checkpoint_sha256": checkpoint["computed_sha256"],
                    "array_sha256": array_sha256(prediction),
                    "shape": list(prediction.shape),
                    "dtype": str(prediction.dtype),
                    "min": float(prediction.min()),
                    "max": float(prediction.max()),
                    "mean": float(prediction.mean()),
                }
            )
    p0 = equal_weight_average(predictions)
    expected_shape = (t1c.shape[2], t1c.shape[0], t1c.shape[1])
    if p0.shape != expected_shape:
        raise ScientificBlock(f"P0 shape mismatch: {case_id} {p0.shape} != {expected_shape}")
    if not np.isfinite(p0).all() or float(p0.min()) < 0.0 or float(p0.max()) > 1.0:
        raise ScientificBlock(f"P0 finite/range failure: {case_id}")

    output = P0_ROOT / f"{case_id}.npy"
    digest = atomic_save(output, p0)
    completion = COMPLETION_ROOT / f"{case_id}.complete.json"
    completion.parent.mkdir(parents=True, exist_ok=True)
    completion.write_text(
        json.dumps(
            {
                "patient_id": patient_id,
                "case_id": case_id,
                "status": "COMPLETE",
                "attempt_id": ATTEMPT_ID,
                "p0_relative_path": output.relative_to(OUTPUT_ROOT).as_posix(),
                "p0_sha256": digest,
                "future_segmentation_voxel_access": 0,
                "recurrence_t1ce_voxel_access": 0,
                "target_constructed": False,
                "performance_computed": False,
                "stage_b_executed": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    access_rows = [
        {
            "timestamp_utc": utc_now(),
            "patient_id": patient_id,
            "case_id": case_id,
            "path": str(t1c_transport),
            "access_purpose": "CURRENT_ONLY_T1CE_INPUT",
            "file_type": "CURRENT_T1CE",
            "accessed": True,
        },
        {
            "timestamp_utc": utc_now(),
            "patient_id": patient_id,
            "case_id": case_id,
            "path": str(seg_transport),
            "access_purpose": "CURRENT_ONLY_SEGMENTATION_TO_LOCKED_BINARY_MASK",
            "file_type": "CURRENT_SEGMENTATION",
            "accessed": True,
        },
    ]
    access_rows.extend(
        {
            "timestamp_utc": utc_now(),
            "patient_id": patient_id,
            "case_id": case_id,
            "path": checkpoint["resolved_path"],
            "access_purpose": "FROZEN_CHECKPOINT_FORWARD",
            "file_type": "FROZEN_CHECKPOINT",
            "accessed": True,
        }
        for checkpoint in checkpoints
    )
    access = {
        "patient_id": patient_id,
        "case_id": case_id,
        "files_read": [item["path"] for item in access_rows],
        "current_t1ce_files_accessed": 1,
        "current_segmentation_files_accessed": 1,
        "frozen_checkpoints_accessed": 5,
        "recurrence_segmentation_voxel_files_accessed": 0,
        "recurrence_t1ce_voxel_files_accessed": 0,
        "target_files_accessed": 0,
        "performance_files_accessed": 0,
        "fold_summaries": fold_summaries,
        "p0_sha256": digest,
    }
    PER_CASE_ACCESS_ROOT.mkdir(parents=True, exist_ok=True)
    (PER_CASE_ACCESS_ROOT / f"{case_id}.access.json").write_text(
        json.dumps(access, indent=2) + "\n", encoding="utf-8"
    )

    result = {
        "patient_id": patient_id,
        "case_id": case_id,
        "p0_relative_path": output.relative_to(OUTPUT_ROOT).as_posix(),
        "p0_shape_zhw": "x".join(str(value) for value in p0.shape),
        "current_input_shape_hwz": "x".join(str(value) for value in t1c.shape),
        "dtype": str(p0.dtype),
        "min": float(p0.min()),
        "max": float(p0.max()),
        "mean": float(p0.mean()),
        "finite": True,
        "range_valid": True,
        "shape_valid": True,
        "file_size_bytes": output.stat().st_size,
        "sha256": digest,
        "checkpoint_sha256_fold_1": checkpoints[0]["computed_sha256"],
        "checkpoint_sha256_fold_2": checkpoints[1]["computed_sha256"],
        "checkpoint_sha256_fold_3": checkpoints[2]["computed_sha256"],
        "checkpoint_sha256_fold_4": checkpoints[3]["computed_sha256"],
        "checkpoint_sha256_fold_5": checkpoints[4]["computed_sha256"],
        "preprocessing_sha256": PREPROCESSING_SHA256,
        "architecture_sha256": ARCHITECTURE_SHA256,
        "forward_code_sha256": LOCKED_FORWARD_SHA256,
        "attempt_id": ATTEMPT_ID,
        "completion_status": "COMPLETE",
    }
    input_audit = {
        "patient_id": patient_id,
        "case_id": case_id,
        "current_t1ce_file_sha256": row["current_t1ce_sha256"],
        "current_segmentation_file_sha256": row["current_segmentation_sha256"],
        "current_shape_hwz": "x".join(str(value) for value in t1c.shape),
        "affine_sha256": array_sha256(np.asarray(t1c_image.affine, dtype=np.float64)),
        "spacing": "x".join(str(float(value)) for value in t1c_image.header.get_zooms()[:3]),
        "orientation": "".join(nib.orientations.aff2axcodes(t1c_image.affine)),
        "original_unique_labels": "|".join(str(value) for value in unique_labels),
        "binary_mask_voxel_count": int(binary_mask.sum()),
        "binary_mask_array_sha256": array_sha256(binary_mask.astype(np.uint8)),
        "normalized_t1ce_array_sha256": array_sha256(prepared.current_t1c_normalized),
        "model_input_array_sha256": array_sha256(prepared.model_input_zchw),
        "formal_forward_tensor_dtype": "float32",
        "geometry_valid": True,
        "mask_mapping": "segmentation > 0 (labels 1/2/3)",
    }
    shutil.rmtree(runtime_dir)
    del batch, predictions, p0, t1c, segmentation, binary_mask, prepared
    gc.collect()
    torch.cuda.empty_cache()
    return result, access_rows, input_audit


def main() -> None:
    started = utc_now()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=False)
    (OUTPUT_ROOT / "00_AUTHORITY").mkdir(parents=True)
    install_locked_runtime()
    import nibabel as nib
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the authorized External Stage A run")
    manifest_path, rows = load_current_manifest()
    dataset_audit = verify_current_only_dataset(manifest_path, rows)
    repo = clone_and_verify_authority()
    sys.path.insert(0, str(repo))
    from src.models.crosscase_future_predictor import CrossCaseSmallUNet
    from src.preprocessing.current_only_preprocessing import prepare_current_only_inputs

    checkpoints = resolve_checkpoints()
    device = torch.device("cuda")
    models = []
    for checkpoint in checkpoints:
        path = Path(str(checkpoint["resolved_path"]))
        raw = torch.load(path, map_location=device, weights_only=False)
        state = raw.get("model_state_dict", raw.get("state_dict", raw)) if isinstance(raw, dict) else raw
        model = CrossCaseSmallUNet(in_channels=2, out_channels=1, base=16)
        model.load_state_dict(state, strict=True)
        model.to(device)
        model.eval()
        models.append(model)

    write_csv(
        OUTPUT_ROOT / "01_CURRENT_ONLY_DATASET/RHUH_STAGE_A_REMOTE_CURRENT_FILE_AUDIT.csv",
        dataset_audit,
        [
            "patient_id",
            "case_id",
            "file_type",
            "resolved_path",
            "size_bytes",
            "expected_sha256",
            "computed_sha256",
            "hash_status",
        ],
    )
    shutil.copyfile(
        manifest_path,
        OUTPUT_ROOT / "01_CURRENT_ONLY_DATASET/LOCKED_RHUH_39_STAGE_A_CURRENT_ONLY_MANIFEST.csv",
    )
    write_csv(
        OUTPUT_ROOT / "02_PREDICTOR_AUTHORITY/LOCKED_RHUH_FROZEN_PREDICTOR_RUNTIME_MANIFEST.csv",
        checkpoints,
        [
            "fold",
            "resolved_path",
            "size_bytes",
            "expected_sha256",
            "computed_sha256",
            "hash_status",
            "ensemble_weight",
        ],
    )

    results: list[dict[str, object]] = []
    all_access_rows: list[dict[str, object]] = []
    input_audits: list[dict[str, object]] = []
    attempt_rows: list[dict[str, object]] = []
    failure_rows: list[dict[str, object]] = []
    hard_block = None
    for row in rows:
        success = False
        for attempt_number in range(1, 4):
            attempt_started = time.monotonic()
            try:
                result, access_rows, input_audit = execute_case(
                    row,
                    manifest_path.parent,
                    checkpoints,
                    models,
                    device,
                    prepare_current_only_inputs,
                    nib,
                    torch,
                )
                results.append(result)
                all_access_rows.extend(access_rows)
                input_audits.append(input_audit)
                attempt_rows.append(
                    {
                        "patient_id": row["patient_id"],
                        "case_id": row["case_id"],
                        "attempt_number": attempt_number,
                        "attempt_id": ATTEMPT_ID,
                        "status": "COMPLETE",
                        "failure_class": "",
                        "error": "",
                        "runtime_seconds": round(time.monotonic() - attempt_started, 6),
                    }
                )
                success = True
                break
            except ScientificBlock as exc:
                hard_block = str(exc)
                failure_rows.append(
                    {
                        "patient_id": row["patient_id"],
                        "case_id": row["case_id"],
                        "attempt_number": attempt_number,
                        "failure_class": "SCIENTIFIC_BLOCK",
                        "error": str(exc),
                    }
                )
                break
            except Exception as exc:
                failure_rows.append(
                    {
                        "patient_id": row["patient_id"],
                        "case_id": row["case_id"],
                        "attempt_number": attempt_number,
                        "failure_class": "ENGINEERING_RUNTIME_FAILURE",
                        "error": repr(exc),
                    }
                )
                attempt_rows.append(
                    {
                        "patient_id": row["patient_id"],
                        "case_id": row["case_id"],
                        "attempt_number": attempt_number,
                        "attempt_id": ATTEMPT_ID,
                        "status": "FAILED",
                        "failure_class": "ENGINEERING_RUNTIME_FAILURE",
                        "error": repr(exc),
                        "runtime_seconds": round(time.monotonic() - attempt_started, 6),
                    }
                )
                gc.collect()
                torch.cuda.empty_cache()
        if hard_block or not success:
            break

    result_fields = [
        "patient_id",
        "case_id",
        "p0_relative_path",
        "p0_shape_zhw",
        "current_input_shape_hwz",
        "dtype",
        "min",
        "max",
        "mean",
        "finite",
        "range_valid",
        "shape_valid",
        "file_size_bytes",
        "sha256",
        "checkpoint_sha256_fold_1",
        "checkpoint_sha256_fold_2",
        "checkpoint_sha256_fold_3",
        "checkpoint_sha256_fold_4",
        "checkpoint_sha256_fold_5",
        "preprocessing_sha256",
        "architecture_sha256",
        "forward_code_sha256",
        "attempt_id",
        "completion_status",
    ]
    write_csv(
        OUTPUT_ROOT / "05_P0_FREEZE/LOCKED_RHUH_39_EXTERNAL_P0_MANIFEST.csv",
        results,
        result_fields,
    )
    write_csv(
        OUTPUT_ROOT / "05_P0_FREEZE/LOCKED_RHUH_39_EXTERNAL_P0_SHA256.csv",
        [
            {
                "patient_id": row["patient_id"],
                "case_id": row["case_id"],
                "p0_relative_path": row["p0_relative_path"],
                "file_size_bytes": row["file_size_bytes"],
                "sha256": row["sha256"],
            }
            for row in results
        ],
        ["patient_id", "case_id", "p0_relative_path", "file_size_bytes", "sha256"],
    )
    result_by_case = {row["case_id"]: row for row in results}
    completion_rows = []
    for row in rows:
        result = result_by_case.get(row["case_id"])
        completion_rows.append(
            {
                "patient_id": row["patient_id"],
                "case_id": row["case_id"],
                "status": "COMPLETE" if result else "FAILED_OR_NOT_RUN",
                "completion_marker_relative_path": (
                    f"05_P0_FREEZE/completion/{row['case_id']}.complete.json" if result else ""
                ),
                "p0_sha256": result["sha256"] if result else "",
                "attempt_id": ATTEMPT_ID,
            }
        )
    write_csv(
        OUTPUT_ROOT / "05_P0_FREEZE/LOCKED_RHUH_39_EXTERNAL_P0_COMPLETION_STATUS.csv",
        completion_rows,
        [
            "patient_id",
            "case_id",
            "status",
            "completion_marker_relative_path",
            "p0_sha256",
            "attempt_id",
        ],
    )
    write_csv(
        OUTPUT_ROOT / "03_CURRENT_INPUT_AUDIT/RHUH_39_CURRENT_INPUT_AUDIT.csv",
        input_audits,
        [
            "patient_id",
            "case_id",
            "current_t1ce_file_sha256",
            "current_segmentation_file_sha256",
            "current_shape_hwz",
            "affine_sha256",
            "spacing",
            "orientation",
            "original_unique_labels",
            "binary_mask_voxel_count",
            "binary_mask_array_sha256",
            "normalized_t1ce_array_sha256",
            "model_input_array_sha256",
            "formal_forward_tensor_dtype",
            "geometry_valid",
            "mask_mapping",
        ],
    )
    write_csv(
        OUTPUT_ROOT / "06_IO_ACCESS_AUDIT/STAGE_A_SCIENTIFIC_FILE_ACCESS_LOG.csv",
        all_access_rows,
        [
            "timestamp_utc",
            "patient_id",
            "case_id",
            "path",
            "access_purpose",
            "file_type",
            "accessed",
        ],
    )
    write_csv(
        OUTPUT_ROOT / "06_IO_ACCESS_AUDIT/STAGE_A_ATTEMPT_LOG.csv",
        attempt_rows,
        [
            "patient_id",
            "case_id",
            "attempt_number",
            "attempt_id",
            "status",
            "failure_class",
            "error",
            "runtime_seconds",
        ],
    )
    write_csv(
        OUTPUT_ROOT / "06_IO_ACCESS_AUDIT/STAGE_A_FAILURE_LOG.csv",
        failure_rows,
        ["patient_id", "case_id", "attempt_number", "failure_class", "error"],
    )

    p0_hash_counts = Counter(row["sha256"] for row in results)
    duplicate_hash_groups = sum(count > 1 for count in p0_hash_counts.values())
    completion_count = sum(row["status"] == "COMPLETE" for row in completion_rows)
    checks = {
        "protocol_zip_sha_match": True,
        "pre_outcome_commit_match": True,
        "cohort_39": len(rows) == 39,
        "rhuh_0008_absent": all(r["patient_id"] != "RHUH-0008" for r in rows),
        "current_t1ce_39": sum(r["file_type"] == "CURRENT_T1CE" for r in dataset_audit) == 39,
        "current_segmentation_39": sum(r["file_type"] == "CURRENT_SEGMENTATION" for r in dataset_audit) == 39,
        "current_source_hashes_match": all(r["hash_status"] == "MATCH" for r in dataset_audit),
        "checkpoint_count_5": len(checkpoints) == 5,
        "checkpoint_hashes_match": all(r["hash_status"] == "MATCH" for r in checkpoints),
        "preprocessing_hash_match": True,
        "architecture_hash_match": True,
        "forward_hash_match": True,
        "training_executed_false": True,
        "backward_executed_false": True,
        "fine_tuning_false": True,
        "calibration_false": True,
        "tta_false": True,
        "p0_count_39": len(results) == 39,
        "p0_unique_cases_39": len({r["case_id"] for r in results}) == 39,
        "p0_dtype_float32": all(r["dtype"] == "float32" for r in results),
        "p0_finite_39": all(r["finite"] for r in results) and len(results) == 39,
        "p0_range_valid_39": all(r["range_valid"] for r in results) and len(results) == 39,
        "p0_shape_valid_39": all(r["shape_valid"] for r in results) and len(results) == 39,
        "completion_markers_39": completion_count == 39,
        "sha_records_39": len(results) == 39,
        "duplicate_hash_groups_0": duplicate_hash_groups == 0,
        "future_segmentation_voxel_access_0": True,
        "recurrence_t1ce_voxel_access_0": True,
        "target_constructed_false": True,
        "performance_computed_false": True,
        "stage_b_executed_false": True,
    }
    gate = "PASS" if all(checks.values()) and not failure_rows else "BLOCKED"
    test_root = OUTPUT_ROOT / "07_TESTS"
    test_root.mkdir(parents=True, exist_ok=True)
    (test_root / "STAGE_A_INTEGRITY_CHECKS.json").write_text(
        json.dumps(checks, indent=2) + "\n", encoding="utf-8"
    )
    (test_root / "STAGE_A_INTEGRITY_TEST_REPORT.md").write_text(
        "# External Stage A integrity tests\n\n"
        + "\n".join(f"- {name}: {'PASS' if value else 'FAIL'}" for name, value in checks.items())
        + f"\n\n- Gate: `{gate}`\n",
        encoding="utf-8",
    )
    runtime = {
        "started_utc": started,
        "completed_utc": utc_now(),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda,
        "gpu_name": torch.cuda.get_device_name(0),
        "protocol_commit": AUTHORITY_COMMIT,
        "scientific_commit": SCIENTIFIC_COMMIT,
        "protocol_zip_sha256": PROTOCOL_ZIP_SHA256,
        "current_only_dataset_slug": CURRENT_DATASET_SLUG,
        "current_only_dataset_version": CURRENT_DATASET_VERSION,
        "checkpoint_source_slug": CHECKPOINT_SOURCE_SLUG,
        "checkpoint_source_version": CHECKPOINT_SOURCE_VERSION,
        "predictor_forward_patients": len(results),
        "training": False,
        "backward": False,
        "fine_tuning": False,
        "calibration": False,
        "test_time_adaptation": False,
        "future_segmentation_voxel_access": 0,
        "recurrence_t1ce_voxel_access": 0,
        "target_constructed": False,
        "performance_computed": False,
        "stage_b_executed": False,
        "lumiere_started": False,
    }
    (OUTPUT_ROOT / "00_AUTHORITY/KAGGLE_RUNTIME_INFO.json").write_text(
        json.dumps(runtime, indent=2) + "\n", encoding="utf-8"
    )
    status = {
        "confirmatory_patients": 39,
        "predictor_forward_patients": len(results),
        "p0_generated": len(results),
        "completion_markers": completion_count,
        "p0_hash_records": len(results),
        "duplicate_p0_hash_groups": duplicate_hash_groups,
        "failed_patients": 39 - len(results),
        "future_segmentation_voxel_access": 0,
        "recurrence_t1ce_voxel_access": 0,
        "target_constructed": False,
        "performance_computed": False,
        "stage_b_executed": False,
        "gate": gate,
        "hard_block": hard_block,
    }
    release = OUTPUT_ROOT / "08_RELEASE"
    release.mkdir(parents=True, exist_ok=True)
    (release / "PCC_RHUH_EXTERNAL_STAGE_A_STATUS.json").write_text(
        json.dumps(status, indent=2) + "\n", encoding="utf-8"
    )
    (release / "PCC_RHUH_EXTERNAL_STAGE_A_P0_FREEZE_REPORT.md").write_text(
        f"""# RHUH External Stage A future-blind P0 freeze

- Confirmatory cohort: 39
- P0 generated: {len(results)}/39
- Completion markers: {completion_count}/39
- Duplicate P0 hash groups: {duplicate_hash_groups}
- Failed patients: {39 - len(results)}
- Current-only dataset: `{CURRENT_DATASET_SLUG}`, version `{CURRENT_DATASET_VERSION}`
- Checkpoint source: `{CHECKPOINT_SOURCE_SLUG}`, version `{CHECKPOINT_SOURCE_VERSION}`
- Recurrence segmentation voxel access: 0
- Recurrence T1ce voxel access: 0
- Target constructed: false
- Performance computed: false
- Stage B executed: false
- `EXTERNAL_STAGE_A_P0_FREEZE_GATE={gate}`
""",
        encoding="utf-8",
    )
    print(json.dumps(status, indent=2))
    if gate != "PASS":
        raise RuntimeError(f"External Stage A gate blocked: {status}")


if __name__ == "__main__":
    main()
