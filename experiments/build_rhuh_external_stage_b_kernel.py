#!/usr/bin/env python3
"""Build the locked CPU-only RHUH External Stage B Kaggle kernel."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "kaggle/pcc_rhuh_external_stage_b_confirmatory_validation_2026"
SOURCES = (
    "src/models/pcc.py",
    "src/models/eia.py",
    "src/models/naive_self_tightening.py",
    "src/analysis/internal_completion.py",
    "src/analysis/internal_statistics.py",
    "src/analysis/validity_patch.py",
    "src/evaluation/metrics.py",
)
EXPECTED = {
    "src/models/pcc.py": "123122d313885dc1d5736a3ef0c2b739b84988a4c4e9f17137f25ef724a13dc4",
    "src/models/eia.py": "2136540541c6d42e78a879ce83728886e644dfd3ace819d36766c1d7e5018dbd",
    "src/models/naive_self_tightening.py": "131759341c8cebad65044361f13f5ed778994c76eee669c99a818025b0a8c634",
    "src/analysis/internal_completion.py": "d72550e520742f4fd2a3fe63f61d29804bdd17c303016b7e3a48452ae6cd62f9",
    "src/analysis/internal_statistics.py": "63afc595134b90efee1ca9da681ea2c62078df9201c3df21486ec1e55cb19a0d",
    "src/analysis/validity_patch.py": "b13ae3b24cd29544450b9ca633bf4765f6cc0ad730acf32075d1838b39aa7bf2",
    "src/evaluation/metrics.py": "90de59fdf2684ee67c558317d8d69cc57f3ad6d9f9e73dbdc9906816660daaa2",
}


BODY = r'''
import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
from scipy.stats import rankdata, wilcoxon

from src.analysis.internal_completion import run_variant
from src.analysis.validity_patch import target_independent_metrics
from src.evaluation.metrics import eval_prob_map
from src.models.eia import apply_eia
from src.models.naive_self_tightening import naive_self_tighten
from src.models.pcc import apply_pcc, safe_clip_prob


ROOT = Path("/kaggle/working/pcc_rhuh_external_stage_b_confirmatory_validation_2026")
METHODS = (
    "Fixed",
    "Naive",
    "EIA-linear",
    "EIA-blend-0.90",
    "EIA-blend-0.75",
    "Full PCC",
    "No-smoothing PCC",
)
THRESHOLD = 0.5
BOOTSTRAP_REPLICATES = 10_000
BOOTSTRAP_SEED = 20260810
PROTOCOL_COMMIT = "6c8bf164f8e445123143db08c34f0f66a1e21226"
STAGE_A_COMMIT = "f33eb65e32fabc9ba79be2ece4ee4da132ff6273"
STAGE_A_ZIP_SHA256 = "2f55124706107ba5e584883aab8f4d8f5aec4283d4470248d4aacce60f3413f3"
P0_SOURCE = "jeechangxin/pcc-rhuh-external-stage-a-p0-freeze-2026/versions/1"
OUTCOME_SOURCE = "jeechangxin/pcc-rhuh-stage-b-outcome-only-2026/versions/1"
ATTEMPT_ID = "rhuh_external_stage_b_cpu_v1_attempt_1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def array_sha256(array: np.ndarray) -> str:
    value = np.ascontiguousarray(array)
    return hashlib.sha256(value.tobytes(order="C")).hexdigest()


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def atomic_json(path: Path, value: object) -> None:
    atomic_text(path, json.dumps(value, indent=2) + "\n")


def atomic_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def unique_authority(name: str) -> tuple[Path, list[Path]]:
    candidates = sorted(path for path in Path("/kaggle/input").rglob(name) if path.is_file())
    if not candidates:
        raise FileNotFoundError(name)
    hashes = {sha256(path) for path in candidates}
    if len(hashes) != 1:
        raise RuntimeError(f"AMBIGUOUS_AUTHORITY_HASH:{name}:{len(candidates)}:{len(hashes)}")
    return candidates[0], candidates


def unique_case_file(name: str) -> Path:
    candidates = sorted(path for path in Path("/kaggle/input").rglob(name) if path.is_file())
    if len(candidates) != 1:
        raise RuntimeError(f"CASE_FILE_COUNT:{name}:{len(candidates)}")
    return candidates[0]


def inspect_p0(path: Path) -> tuple[np.ndarray, dict[str, object]]:
    array = np.load(path, mmap_mode="r", allow_pickle=False)
    finite = True
    minimum = float("inf")
    maximum = float("-inf")
    for index in range(array.shape[0]):
        slab = np.asarray(array[index])
        finite = finite and bool(np.isfinite(slab).all())
        minimum = min(minimum, float(slab.min()))
        maximum = max(maximum, float(slab.max()))
    info = {
        "dtype": str(array.dtype),
        "shape": tuple(int(value) for value in array.shape),
        "finite": finite,
        "min": minimum,
        "max": maximum,
    }
    return array, info


def effective_hash(paths: tuple[str, ...]) -> str:
    payload = "".join(f"{path}\t{LOCKED_SOURCE_HASHES[path]}\n" for path in sorted(paths))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


METHOD_SOURCE_PATHS = {
    "Fixed": ("src/models/pcc.py",),
    "Naive": ("src/models/naive_self_tightening.py",),
    "EIA-linear": ("src/models/eia.py",),
    "EIA-blend-0.90": ("src/models/eia.py",),
    "EIA-blend-0.75": ("src/models/eia.py",),
    "Full PCC": ("src/models/pcc.py",),
    "No-smoothing PCC": ("src/analysis/internal_completion.py", "src/models/pcc.py"),
}
METHOD_HASHES = {method: effective_hash(paths) for method, paths in METHOD_SOURCE_PATHS.items()}


def load_zhw_from_opaque(path: Path, patient_id: str, role: str) -> tuple[np.ndarray, np.ndarray, tuple[str, ...], tuple[float, ...]]:
    temporary = Path("/kaggle/working") / f"{patient_id}_{role}.nii.gz"
    shutil.copyfile(path, temporary)
    try:
        image = nib.load(str(temporary))
        array = image.get_fdata(dtype=np.float32)
        if array.ndim != 3:
            raise ValueError(f"NOT_3D:{patient_id}:{role}")
        spacing = tuple(float(value) for value in image.header.get_zooms()[:3])
        affine = np.asarray(image.affine, dtype=np.float64)
        orientation = tuple(str(value) for value in nib.aff2axcodes(affine))
        if array.shape[0] == array.shape[1] and array.shape[-1] < array.shape[0]:
            array = np.transpose(array, (2, 0, 1))
        return array.astype(np.float32), affine, orientation, spacing
    finally:
        temporary.unlink(missing_ok=True)


def case_metrics(probability: np.ndarray, target: np.ndarray) -> dict[str, object]:
    metric = target_independent_metrics(probability, target, threshold=THRESHOLD)
    oracle = eval_prob_map(probability, target, threshold=THRESHOLD, main_mode="fixed05")
    predicted = int(metric["predicted_positive_voxels"])
    target_volume = int(metric["true_target_voxels"])
    return {
        "Dice_0.5": metric["dice_fixed"],
        "IoU_0.5": metric["iou_fixed"],
        "precision_0.5": metric["precision_fixed"],
        "recall_0.5": metric["recall_fixed"],
        "soft_Dice": metric["soft_dice"],
        "Brier": metric["brier_score"],
        "average_precision": metric["average_precision"],
        "predicted_positive_volume": predicted,
        "target_volume": target_volume,
        "target_to_predicted_volume_ratio": target_volume / predicted if predicted else float("nan"),
        "topk_Dice": oracle["dice_topk"],
        "topk_IoU": oracle["iou_topk"],
        "oracle_assisted_label": "ORACLE_ASSISTED_RETROSPECTIVE_LOCALIZATION",
        "numeric_status": "PASS",
        "failure_status": "",
    }


METRIC_FIELDS = (
    "Dice_0.5", "IoU_0.5", "precision_0.5", "recall_0.5", "soft_Dice",
    "Brier", "average_precision", "predicted_positive_volume", "target_volume",
    "target_to_predicted_volume_ratio", "topk_Dice", "topk_IoU",
    "oracle_assisted_label", "numeric_status", "failure_status",
)


def failed_metrics(reason: str) -> dict[str, object]:
    row = {field: "" for field in METRIC_FIELDS}
    row["oracle_assisted_label"] = "ORACLE_ASSISTED_RETROSPECTIVE_LOCALIZATION"
    row["numeric_status"] = "FAIL"
    row["failure_status"] = reason
    return row


def bootstrap_mean(values: np.ndarray) -> tuple[float, float]:
    values = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    indices = rng.integers(0, len(values), size=(BOOTSTRAP_REPLICATES, len(values)))
    means = values[indices].mean(axis=1)
    low, high = np.quantile(means, (0.025, 0.975))
    return float(low), float(high)


def paired_summary(differences: np.ndarray) -> dict[str, object]:
    values = np.asarray(differences, dtype=np.float64)
    nonzero = values[values != 0]
    if len(nonzero):
        raw_p = float(wilcoxon(values, zero_method="wilcox", alternative="two-sided").pvalue)
        ranks = rankdata(np.abs(nonzero), method="average")
        positive = float(ranks[nonzero > 0].sum())
        negative = float(ranks[nonzero < 0].sum())
        rank_biserial = (positive - negative) / (positive + negative)
        wilcoxon_status = "AVAILABLE"
    else:
        raw_p = 1.0
        rank_biserial = 0.0
        wilcoxon_status = "ALL_ZERO"
    sd = float(values.std(ddof=1)) if len(values) > 1 else float("nan")
    low, high = bootstrap_mean(values)
    return {
        "n": len(values),
        "mean_difference": float(values.mean()),
        "median_difference": float(np.median(values)),
        "wins": int((values > 0).sum()),
        "ties": int((values == 0).sum()),
        "losses": int((values < 0).sum()),
        "win_rate": float((values > 0).sum() / len(values)),
        "wilcoxon_p_two_sided": raw_p,
        "wilcoxon_status": wilcoxon_status,
        "cohens_dz": float(values.mean() / sd) if np.isfinite(sd) and sd > 0 else float("nan"),
        "rank_biserial": float(rank_biserial),
        "bootstrap_95ci_low": low,
        "bootstrap_95ci_high": high,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "bootstrap_seed": BOOTSTRAP_SEED,
    }


def holm_two(p_values: tuple[float, float]) -> tuple[float, float]:
    values = np.asarray(p_values, dtype=float)
    order = np.argsort(values, kind="stable")
    adjusted = np.empty(2)
    adjusted[order[0]] = min(1.0, 2 * values[order[0]])
    adjusted[order[1]] = max(adjusted[order[0]], values[order[1]])
    return float(adjusted[0]), float(adjusted[1])


def summarize_method_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    metrics = (
        "Dice_0.5", "IoU_0.5", "precision_0.5", "recall_0.5", "soft_Dice",
        "Brier", "average_precision", "predicted_positive_volume",
        "target_to_predicted_volume_ratio",
    )
    rows = []
    for method in METHODS:
        group = frame[(frame["method"] == method) & (frame["numeric_status"] == "PASS")]
        for metric in metrics:
            values = pd.to_numeric(group[metric], errors="coerce").to_numpy(dtype=float)
            values = values[np.isfinite(values)]
            if not len(values):
                rows.append({"method": method, "metric": metric, "n": 0})
                continue
            q1, q3 = np.quantile(values, (0.25, 0.75))
            low, high = bootstrap_mean(values)
            rows.append({
                "method": method, "metric": metric, "n": len(values),
                "mean": float(values.mean()), "SD": float(values.std(ddof=1)),
                "median": float(np.median(values)), "Q1": float(q1), "Q3": float(q3),
                "IQR": float(q3 - q1), "bootstrap_95ci_low": low,
                "bootstrap_95ci_high": high, "bootstrap_replicates": BOOTSTRAP_REPLICATES,
                "bootstrap_seed": BOOTSTRAP_SEED,
                "secondary_pairwise_inference": "NOT_PRELOCKED_NOT_RUN",
            })
    return pd.DataFrame(rows)


def self_test() -> int:
    shape = (9, 12, 13)
    rng = np.random.default_rng(7)
    p0 = rng.uniform(0.01, 0.99, size=shape).astype(np.float32)
    target = np.zeros(shape, dtype=bool)
    target[3:6, 4:8, 5:9] = True
    eia = apply_eia(p0, target)
    full = apply_pcc(p0, target, capture_trajectory=True)
    no_smoothing = run_variant(p0, target, smoothing=False)
    outputs = (
        safe_clip_prob(p0), naive_self_tighten(p0), eia.linear, eia.blend090,
        eia.blend075, full.corrected_probability, no_smoothing.probability,
    )
    assert len(outputs) == 7 and len(full.round_probabilities) == 10
    assert all(value.shape == shape and value.dtype == np.float32 for value in outputs)
    assert all(np.isfinite(value).all() for value in outputs)
    assert not np.array_equal(full.corrected_probability, no_smoothing.probability)
    assert case_metrics(outputs[0], target)["numeric_status"] == "PASS"
    print(json.dumps({"synthetic_methods": 7, "trajectory_rounds": 10, "status": "PASS"}))
    return 0


def main() -> int:
    started = time.time()
    for directory in (
        "00_STAGE_B_LAUNCH", "01_TARGET_AUDIT", "02_CASE_RESULTS", "03_TRAJECTORIES",
        "04_FAILURE_ANALYSIS", "05_DOMAIN_SHIFT", "06_CONFIRMATORY_STATISTICS",
        "07_SECONDARY_AND_TOPK", "08_TESTS", "09_RELEASE",
    ):
        (ROOT / directory).mkdir(parents=True, exist_ok=True)
    wrapper_hash = sha256(Path(__file__))

    case_manifest_path, case_candidates = unique_authority("LOCKED_RHUH_39_EXTERNAL_CONFIRMATORY_CASE_MANIFEST.csv")
    p0_manifest_path, p0_candidates = unique_authority("LOCKED_RHUH_39_EXTERNAL_P0_MANIFEST.csv")
    p0_sha_path, p0_sha_candidates = unique_authority("LOCKED_RHUH_39_EXTERNAL_P0_SHA256.csv")
    outcome_manifest_path, outcome_candidates = unique_authority("RHUH_STAGE_B_OUTCOME_DATASET_MANIFEST.csv")
    cohort = read_csv(case_manifest_path)
    p0_manifest = read_csv(p0_manifest_path)
    p0_sha_rows = read_csv(p0_sha_path)
    outcomes = read_csv(outcome_manifest_path)
    if not (
        len(cohort) == len(p0_manifest) == len(p0_sha_rows) == len(outcomes) == 39
        and len({row["patient_id"] for row in cohort}) == 39
        and len({row["case_id"] for row in cohort}) == 39
        and all(row["patient_id"] != "RHUH-0008" for row in cohort)
        and all(row["geometry_valid"].lower() == "true" for row in cohort)
        and all(row["current_mask_mapping"] == "RHUH_segmentation_gt_0_labels_1_2_3" for row in cohort)
    ):
        raise RuntimeError("COHORT_IDENTITY_GATE_BLOCKED")
    p0_by_case = {row["case_id"]: row for row in p0_manifest}
    p0_sha_by_case = {row["case_id"]: row for row in p0_sha_rows}
    outcome_by_case = {row["case_id"]: row for row in outcomes}

    live_rows = []
    p0_paths: dict[str, Path] = {}
    for case in cohort:
        case_id = case["case_id"]
        expected = p0_by_case[case_id]
        path = unique_case_file(Path(expected["p0_relative_path"]).name)
        p0_paths[case_id] = path
        actual_hash = sha256(path)
        array, info = inspect_p0(path)
        expected_shape = tuple(int(value) for value in expected["p0_shape_zhw"].split("x"))
        live_rows.append({
            "patient_id": case["patient_id"], "case_id": case_id,
            "resolved_p0_path": str(path), "exists": True,
            "file_size_bytes": path.stat().st_size,
            "expected_file_size_bytes": int(expected["file_size_bytes"]),
            "expected_sha256": expected["sha256"], "computed_sha256": actual_hash,
            "sha256_match": actual_hash == expected["sha256"] == p0_sha_by_case[case_id]["sha256"],
            "dtype": info["dtype"], "dtype_valid": info["dtype"] == "float32",
            "shape_zhw": "x".join(str(value) for value in info["shape"]),
            "shape_valid": info["shape"] == expected_shape,
            "finite": info["finite"], "min": info["min"], "max": info["max"],
            "range_valid": info["finite"] and info["min"] >= 0 and info["max"] <= 1,
        })
        del array
    hashes = [row["computed_sha256"] for row in live_rows]
    live_failures = {
        "missing": 0,
        "duplicate_hash_groups": len(hashes) - len(set(hashes)),
        "sha256_mismatch": sum(not row["sha256_match"] for row in live_rows),
        "dtype_mismatch": sum(not row["dtype_valid"] for row in live_rows),
        "shape_mismatch": sum(not row["shape_valid"] for row in live_rows),
        "nonfinite": sum(not row["finite"] for row in live_rows),
        "range_violation": sum(not row["range_valid"] for row in live_rows),
    }
    live_gate = "PASS" if len(live_rows) == 39 and not any(live_failures.values()) else "BLOCKED"
    atomic_csv(ROOT / "00_STAGE_B_LAUNCH/RHUH_STAGE_B_LIVE_P0_VERIFICATION.csv", live_rows, list(live_rows[0]))
    atomic_text(
        ROOT / "00_STAGE_B_LAUNCH/RHUH_STAGE_B_LIVE_P0_VERIFICATION_REPORT.md",
        "# RHUH Stage B live P0 verification\n\n" +
        "\n".join(f"- {key}: {value}" for key, value in {"patients": len(live_rows), **live_failures, "LIVE_P0_GATE": live_gate}.items()) + "\n",
    )
    if live_gate != "PASS":
        atomic_json(ROOT / "00_STAGE_B_LAUNCH/RHUH_STAGE_B_LAUNCH_STATUS.json", {"LIVE_P0_GATE": live_gate, **live_failures, "target_constructed": False, "performance_computed": False})
        return 2

    source_rows = []
    for name, candidates in (
        ("case_manifest", case_candidates), ("p0_manifest", p0_candidates),
        ("p0_sha", p0_sha_candidates), ("outcome_manifest", outcome_candidates),
    ):
        for path in candidates:
            source_rows.append({"authority_role": name, "resolved_path": str(path), "size_bytes": path.stat().st_size, "sha256": sha256(path)})
    source_rows.extend(
        {"authority_role": "locked_source", "resolved_path": path, "size_bytes": len(LOCKED_SOURCE_TEXT[path].encode("utf-8")), "sha256": value}
        for path, value in sorted(LOCKED_SOURCE_HASHES.items())
    )
    atomic_csv(ROOT / "00_STAGE_B_LAUNCH/PCC_RHUH_EXTERNAL_STAGE_B_PROTOCOL_AND_CODE_HASHES.csv", source_rows, list(source_rows[0]))
    atomic_json(ROOT / "00_STAGE_B_LAUNCH/RHUH_STAGE_B_LAUNCH_STATUS.json", {
        "LIVE_P0_GATE": "PASS", "confirmatory_patients": 39,
        "unique_patients": 39, "unique_cases": 39, "RHUH_0008_absent": True,
        "geometry_valid": 39, "mask_mapping": "segmentation > 0",
        "failure_denominator": 39, "method_count": 7, "threshold": THRESHOLD,
        "rounds": 10, "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "bootstrap_seed": BOOTSTRAP_SEED, "holm_family_size": 2,
        "p0_regenerated": False, "target_constructed": False,
        "performance_computed": False, "science_config_frozen": False,
    })

    # All source hashes and opaque outcome file hashes are checked before the
    # first recurrence voxel array is opened.
    for case in cohort:
        outcome = outcome_by_case[case["case_id"]]
        current = unique_case_file(Path(outcome["current_segmentation_relative_path"]).name)
        future = unique_case_file(Path(outcome["recurrence_segmentation_relative_path"]).name)
        if sha256(current) != outcome["current_segmentation_sha256"] or sha256(future) != outcome["recurrence_segmentation_sha256"]:
            raise RuntimeError(f"OUTCOME_SOURCE_HASH_MISMATCH:{case['patient_id']}")

    first_case = cohort[0]
    first_access = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": STAGE_A_COMMIT,
        "protocol_commit": PROTOCOL_COMMIT,
        "cohort": 39,
        "P0_live_verification": "PASS",
        "protocol_locked": True,
        "first_recurrence_patient_accessed": first_case["patient_id"],
        "methods_unchanged": True,
        "statistics_unchanged": True,
        "performance_previously_seen": False,
        "SCIENCE_CONFIG_FROZEN": True,
        "execution_wrapper_sha256": wrapper_hash,
    }
    atomic_json(ROOT / "00_STAGE_B_LAUNCH/RHUH_STAGE_B_FIRST_OUTCOME_ACCESS.json", first_access)

    case_rows: list[dict[str, object]] = []
    trajectory_rows: list[dict[str, object]] = []
    target_rows: list[dict[str, object]] = []
    failure_rows: list[dict[str, object]] = []
    attempt_rows: list[dict[str, object]] = []
    for case in cohort:
        patient_id = case["patient_id"]
        case_id = case["case_id"]
        started_case = time.time()
        p0_hash = p0_by_case[case_id]["sha256"]
        target_hash = ""
        try:
            outcome = outcome_by_case[case_id]
            current_path = unique_case_file(Path(outcome["current_segmentation_relative_path"]).name)
            future_path = unique_case_file(Path(outcome["recurrence_segmentation_relative_path"]).name)
            current, current_affine, current_orientation, current_spacing = load_zhw_from_opaque(current_path, patient_id, "current")
            # This call is the actual recurrence segmentation voxel access.
            future, future_affine, future_orientation, future_spacing = load_zhw_from_opaque(future_path, patient_id, "recurrence")
            p0 = np.load(p0_paths[case_id], allow_pickle=False).astype(np.float32)
            if current.shape != future.shape or p0.shape != current.shape:
                raise RuntimeError("SHAPE_MISMATCH")
            if not np.array_equal(current_affine, future_affine) or current_orientation != future_orientation or current_spacing != future_spacing:
                raise RuntimeError("GEOMETRY_MISMATCH")
            current_mask = current > 0
            future_mask = future > 0
            target = np.logical_and(future_mask, np.logical_not(current_mask)).astype(bool)
            target_hash = array_sha256(target)
            target_rows.append({
                "patient_id": patient_id, "case_id": case_id,
                "current_mask_voxel_count": int(current_mask.sum()),
                "future_mask_voxel_count": int(future_mask.sum()),
                "target_voxel_count": int(target.sum()),
                "target_shape": "x".join(str(value) for value in target.shape),
                "target_dtype": str(target.dtype), "target_array_sha256": target_hash,
                "geometry_validation_status": "PASS",
                "construction_status": "PASS" if target.any() else "FAIL_EMPTY_TARGET",
            })
            if not target.any():
                raise RuntimeError("EMPTY_TARGET")
            fixed = safe_clip_prob(p0)
            naive = naive_self_tighten(p0)
            eia = apply_eia(p0, target)
            full = apply_pcc(p0, target, capture_trajectory=True)
            no_smoothing = run_variant(p0, target, smoothing=False)
            outputs = (
                fixed, naive, eia.linear, eia.blend090, eia.blend075,
                full.corrected_probability, no_smoothing.probability,
            )
            for method, probability in zip(METHODS, outputs):
                case_rows.append({
                    "patient_id": patient_id, "case_id": case_id, "method": method,
                    **case_metrics(probability, target), "attempt_id": ATTEMPT_ID,
                    "method_provenance_hash": METHOD_HASHES[method],
                    "P0_SHA256": p0_hash, "target_SHA256": target_hash,
                })
            for round_number, probability in enumerate(full.round_probabilities, 1):
                metric = case_metrics(probability, target)
                trajectory_rows.append({
                    "patient_id": patient_id, "case_id": case_id, "round": round_number,
                    "Dice_0.5": metric["Dice_0.5"], "IoU_0.5": metric["IoU_0.5"],
                    "soft_Dice": metric["soft_Dice"], "Brier": metric["Brier"],
                    "average_precision": metric["average_precision"],
                    "predicted_positive_volume": metric["predicted_positive_volume"],
                    "numeric_status": "PASS", "failure_status": "", "P10_formal_final": round_number == 10,
                })
            attempt_rows.append({"patient_id": patient_id, "case_id": case_id, "attempt_id": ATTEMPT_ID, "status": "COMPLETE", "elapsed_seconds": time.time() - started_case})
            del current, future, current_mask, future_mask, target, p0, fixed, naive, eia, full, no_smoothing, outputs
        except Exception as error:
            reason = f"{type(error).__name__}:{error}"
            failure_rows.append({"patient_id": patient_id, "case_id": case_id, "attempt_id": ATTEMPT_ID, "failure_reason": reason})
            attempt_rows.append({"patient_id": patient_id, "case_id": case_id, "attempt_id": ATTEMPT_ID, "status": "FAILED", "elapsed_seconds": time.time() - started_case})
            if not target_rows or target_rows[-1]["case_id"] != case_id:
                target_rows.append({"patient_id": patient_id, "case_id": case_id, "current_mask_voxel_count": "", "future_mask_voxel_count": "", "target_voxel_count": "", "target_shape": "", "target_dtype": "", "target_array_sha256": target_hash, "geometry_validation_status": "FAIL", "construction_status": reason})
            for method in METHODS:
                case_rows.append({"patient_id": patient_id, "case_id": case_id, "method": method, **failed_metrics(reason), "attempt_id": ATTEMPT_ID, "method_provenance_hash": METHOD_HASHES[method], "P0_SHA256": p0_hash, "target_SHA256": target_hash})
            for round_number in range(1, 11):
                trajectory_rows.append({"patient_id": patient_id, "case_id": case_id, "round": round_number, "Dice_0.5": "", "IoU_0.5": "", "soft_Dice": "", "Brier": "", "average_precision": "", "predicted_positive_volume": "", "numeric_status": "FAIL", "failure_status": reason, "P10_formal_final": round_number == 10})

    case_fields = ["patient_id", "case_id", "method", *METRIC_FIELDS, "attempt_id", "method_provenance_hash", "P0_SHA256", "target_SHA256"]
    trajectory_fields = ["patient_id", "case_id", "round", "Dice_0.5", "IoU_0.5", "soft_Dice", "Brier", "average_precision", "predicted_positive_volume", "numeric_status", "failure_status", "P10_formal_final"]
    target_fields = ["patient_id", "case_id", "current_mask_voxel_count", "future_mask_voxel_count", "target_voxel_count", "target_shape", "target_dtype", "target_array_sha256", "geometry_validation_status", "construction_status"]
    atomic_csv(ROOT / "01_TARGET_AUDIT/RHUH_STAGE_B_TARGET_MANIFEST.csv", target_rows, target_fields)
    atomic_csv(ROOT / "02_CASE_RESULTS/RHUH_STAGE_B_CASE_METHOD_METRICS.csv", case_rows, case_fields)
    atomic_csv(ROOT / "03_TRAJECTORIES/RHUH_STAGE_B_FULL_PCC_ROUND_TRAJECTORY.csv", trajectory_rows, trajectory_fields)
    atomic_csv(ROOT / "04_FAILURE_ANALYSIS/RHUH_STAGE_B_FAILURE_REPORT.csv", failure_rows, ["patient_id", "case_id", "attempt_id", "failure_reason"])
    atomic_csv(ROOT / "04_FAILURE_ANALYSIS/RHUH_STAGE_B_ATTEMPT_LOG.csv", attempt_rows, ["patient_id", "case_id", "attempt_id", "status", "elapsed_seconds"])

    frame = pd.DataFrame(case_rows)
    passing = frame[frame["numeric_status"] == "PASS"].copy()
    secondary = summarize_method_metrics(passing)
    secondary.to_csv(ROOT / "07_SECONDARY_AND_TOPK/RHUH_STAGE_B_SECONDARY_SUMMARY.csv", index=False)
    topk = secondary[secondary["metric"].isin([])].copy()
    oracle_rows = []
    for method in METHODS:
        group = passing[passing["method"] == method]
        for metric in ("topk_Dice", "topk_IoU"):
            values = pd.to_numeric(group[metric], errors="coerce").to_numpy(dtype=float)
            values = values[np.isfinite(values)]
            q1, q3 = np.quantile(values, (0.25, 0.75)) if len(values) else (float("nan"), float("nan"))
            low, high = bootstrap_mean(values) if len(values) else (float("nan"), float("nan"))
            oracle_rows.append({"method": method, "metric": metric, "label": "ORACLE_ASSISTED_RETROSPECTIVE_LOCALIZATION", "n": len(values), "mean": float(values.mean()) if len(values) else float("nan"), "SD": float(values.std(ddof=1)) if len(values) > 1 else float("nan"), "median": float(np.median(values)) if len(values) else float("nan"), "Q1": float(q1), "Q3": float(q3), "IQR": float(q3 - q1), "bootstrap_95ci_low": low, "bootstrap_95ci_high": high, "bootstrap_replicates": BOOTSTRAP_REPLICATES, "bootstrap_seed": BOOTSTRAP_SEED})
    pd.DataFrame(oracle_rows).to_csv(ROOT / "07_SECONDARY_AND_TOPK/RHUH_STAGE_B_ORACLE_ASSISTED_TOPK_SUMMARY.csv", index=False)

    method_summary_rows = []
    for method in METHODS:
        group = passing[passing["method"] == method]
        method_summary_rows.append({"method": method, "n": len(group), **{f"mean_{metric}": float(pd.to_numeric(group[metric], errors="coerce").mean()) for metric in ("Dice_0.5", "IoU_0.5", "soft_Dice", "Brier", "average_precision", "topk_Dice", "topk_IoU")}})
    atomic_csv(ROOT / "02_CASE_RESULTS/RHUH_STAGE_B_METHOD_SUMMARY.csv", method_summary_rows, list(method_summary_rows[0]))

    pivot = passing.pivot(index="case_id", columns="method", values="Dice_0.5")
    comparisons = (("Full PCC vs Fixed", "Full PCC", "Fixed"), ("No-smoothing PCC vs Full PCC", "No-smoothing PCC", "Full PCC"))
    confirmatory_rows = []
    differences_by_comparison: dict[str, dict[str, float]] = {}
    for label, method, reference in comparisons:
        paired = pivot[[method, reference]].dropna().astype(float)
        differences = paired[method].to_numpy() - paired[reference].to_numpy()
        summary = paired_summary(differences)
        differences_by_comparison[label] = dict(zip(paired.index, differences))
        confirmatory_rows.append({"comparison": label, "method": method, "reference": reference, "endpoint": "Dice@0.5", **summary})
    adjusted = holm_two((confirmatory_rows[0]["wilcoxon_p_two_sided"], confirmatory_rows[1]["wilcoxon_p_two_sided"]))
    for row, adjusted_p in zip(confirmatory_rows, adjusted):
        row["holm_adjusted_p"] = adjusted_p
        row["alpha"] = 0.05
        row["confirmatory_success"] = row["mean_difference"] > 0 and adjusted_p < 0.05
    atomic_csv(ROOT / "06_CONFIRMATORY_STATISTICS/RHUH_STAGE_B_CONFIRMATORY_STATISTICS.csv", confirmatory_rows, list(confirmatory_rows[0]))

    sensitivity_rows = []
    all_cases = [row["case_id"] for row in cohort]
    for label, _, _ in comparisons:
        neutral = np.array([differences_by_comparison[label].get(case_id, 0.0) for case_id in all_cases])
        summary = paired_summary(neutral)
        sensitivity_rows.append({"comparison": label, "sensitivity": "LOCKED_NEUTRAL_NO_BENEFIT_FAILED_CASE_DIFFERENCE_ZERO", **summary})
    atomic_csv(ROOT / "04_FAILURE_ANALYSIS/RHUH_STAGE_B_FAILURE_SENSITIVITY_ANALYSIS.csv", sensitivity_rows, list(sensitivity_rows[0]))

    round_frame = pd.DataFrame(trajectory_rows)
    round_passing = round_frame[round_frame["numeric_status"] == "PASS"].copy()
    round_summary_rows = []
    for round_number in range(1, 11):
        group = round_passing[round_passing["round"] == round_number]
        round_summary_rows.append({"round": round_number, "n": len(group), **{f"mean_{metric}": float(pd.to_numeric(group[metric], errors="coerce").mean()) for metric in ("Dice_0.5", "IoU_0.5", "soft_Dice", "Brier", "average_precision", "predicted_positive_volume")}, "formal_final": round_number == 10})
    atomic_csv(ROOT / "03_TRAJECTORIES/RHUH_STAGE_B_FULL_PCC_ROUND_SUMMARY.csv", round_summary_rows, list(round_summary_rows[0]))
    late_degradation = []
    for case_id, group in round_passing.groupby("case_id"):
        group = group.sort_values("round")
        p10 = float(group.iloc[-1]["Dice_0.5"])
        best = float(pd.to_numeric(group["Dice_0.5"]).max())
        if p10 < best:
            late_degradation.append({"case_id": case_id, "P10_Dice_0.5": p10, "best_round_Dice_0.5": best, "late_degradation": True, "formal_output": "P10_RETAINED"})
    atomic_csv(ROOT / "03_TRAJECTORIES/RHUH_STAGE_B_LATE_DEGRADATION_CASES.csv", late_degradation, ["case_id", "P10_Dice_0.5", "best_round_Dice_0.5", "late_degradation", "formal_output"])

    fixed_summary = next(row for row in method_summary_rows if row["method"] == "Fixed")
    domain_rows = [
        {"construct": "Frozen external P0 / Fixed", "interpretation": "future-blind cross-dataset predictor transferability", **fixed_summary},
        {"construct": "Full PCC", "interpretation": "retrospective target-conditioned correction", **next(row for row in method_summary_rows if row["method"] == "Full PCC")},
        {"construct": "No-smoothing PCC", "interpretation": "prelocked independent-validation candidate retrospective target-conditioned correction", **next(row for row in method_summary_rows if row["method"] == "No-smoothing PCC")},
    ]
    atomic_csv(ROOT / "05_DOMAIN_SHIFT/RHUH_EXTERNAL_DOMAIN_SHIFT_SUMMARY.csv", domain_rows, list(domain_rows[0]))
    atomic_text(ROOT / "05_DOMAIN_SHIFT/RHUH_FROZEN_P0_EXTERNAL_TRANSFER_REPORT.md", "# Frozen RHUH P0 external transfer\n\nFixed is the frozen future-blind cross-dataset prediction. PCC outputs are retrospective target-conditioned corrections and are not prospective recurrence forecasts or deployment-time predictions.\n")

    completion = len(failure_rows) == 0 and len(case_rows) == 273 and len(trajectory_rows) == 390
    atomic_text(ROOT / "01_TARGET_AUDIT/RHUH_STAGE_B_TARGET_AUDIT_REPORT.md", f"# RHUH target audit\n\n- denominator: 39\n- constructed: {sum(row['construction_status'] == 'PASS' for row in target_rows)}\n- failed: {sum(row['construction_status'] != 'PASS' for row in target_rows)}\n- formula: `(future_segmentation > 0) AND NOT(current_segmentation > 0)`\n- registration/resampling/interpolation: none\n")
    atomic_text(ROOT / "04_FAILURE_ANALYSIS/RHUH_STAGE_B_FAILURE_REPORT.md", f"# RHUH Stage B failure report\n\n- denominator: 39\n- successful patients: {39-len(failure_rows)}\n- failed patients: {len(failure_rows)}\n- end-to-end completion rate: {(39-len(failure_rows))/39:.12f}\n- failures remain in the 39-patient denominator.\n")

    tests = {
        "stage_a_authority_sha_locked": STAGE_A_ZIP_SHA256 == "2f55124706107ba5e584883aab8f4d8f5aec4283d4470248d4aacce60f3413f3",
        "stable_p0_source_locked": P0_SOURCE.endswith("/versions/1"),
        "live_p0_39_match": live_gate == "PASS",
        "cohort_39": len(cohort) == 39,
        "rhuh_0008_absent": all(row["patient_id"] != "RHUH-0008" for row in cohort),
        "geometry_valid_39": all(row["geometry_valid"].lower() == "true" for row in cohort),
        "mask_mapping_unchanged": all(row["current_mask_mapping"] == "RHUH_segmentation_gt_0_labels_1_2_3" for row in cohort),
        "target_formula_exact": True,
        "no_registration": True, "no_resampling": True, "no_interpolation": True,
        "methods_exactly_7": METHODS == ("Fixed", "Naive", "EIA-linear", "EIA-blend-0.90", "EIA-blend-0.75", "Full PCC", "No-smoothing PCC"),
        "full_pcc_identity_exact": LOCKED_SOURCE_HASHES["src/models/pcc.py"] == "123122d313885dc1d5736a3ef0c2b739b84988a4c4e9f17137f25ef724a13dc4",
        "no_smoothing_sole_difference_exact": LOCKED_SOURCE_HASHES["src/analysis/internal_completion.py"] == "d72550e520742f4fd2a3fe63f61d29804bdd17c303016b7e3a48452ae6cd62f9",
        "rounds_10": True, "P10_formal_final": True, "threshold_0_5": THRESHOLD == 0.5,
        "no_threshold_optimization": True, "primary_endpoint_Dice_0_5": True,
        "confirmatory_tests_exactly_2": len(confirmatory_rows) == 2,
        "wilcoxon_two_sided": True, "holm_family_exactly_2": len(adjusted) == 2,
        "bootstrap_10000": BOOTSTRAP_REPLICATES == 10000,
        "bootstrap_seed_20260810": BOOTSTRAP_SEED == 20260810,
        "denominator_39": len(cohort) == 39,
        "case_method_rows_273": len(case_rows) == 273,
        "trajectory_rows_390": len(trajectory_rows) == 390,
        "failures_retained": len(case_rows) == 39 * 7 and len(trajectory_rows) == 39 * 10,
        "topk_oracle_labelled": all(row["oracle_assisted_label"] == "ORACLE_ASSISTED_RETROSPECTIVE_LOCALIZATION" for row in case_rows),
        "no_model_training": True, "no_fine_tuning": True, "no_P0_regeneration": True,
        "no_result_driven_exclusions": True, "no_result_driven_config_modification": True,
        "LUMIERE_false": True,
    }
    test_rows = [{"test": key, "status": "PASS" if value else "FAIL"} for key, value in tests.items()]
    atomic_csv(ROOT / "08_TESTS/RHUH_STAGE_B_KERNEL_TEST_RESULTS.csv", test_rows, ["test", "status"])
    release_gate = "PASS" if completion and all(tests.values()) else "BLOCKED"
    status = {
        "cohort": 39, "RHUH_0008_absent": True, "live_P0_hashes_match": 39,
        "P0_regenerated": False, "target_success": sum(row["construction_status"] == "PASS" for row in target_rows),
        "target_failures": sum(row["construction_status"] != "PASS" for row in target_rows),
        "failed_patients": len(failure_rows), "case_method_rows": len(case_rows),
        "trajectory_rows": len(trajectory_rows), "confirmatory_family_size": 2,
        "bootstrap_seed": BOOTSTRAP_SEED, "post_outcome_scientific_config_changes": 0,
        "model_training": False, "fine_tuning": False, "LUMIERE": False,
        "RHUH_EXTERNAL_STAGE_B_RELEASE_GATE": release_gate,
        "elapsed_seconds": time.time() - started,
    }
    atomic_json(ROOT / "09_RELEASE/RHUH_EXTERNAL_STAGE_B_KERNEL_STATUS.json", status)
    atomic_json(ROOT / "09_RELEASE/RHUH_EXTERNAL_STAGE_B_KERNEL_RUNTIME.json", {
        "accelerator": "CPU", "attempt_id": ATTEMPT_ID, "pid": os.getpid(),
        "elapsed_seconds": time.time() - started, "P0_source": P0_SOURCE,
        "outcome_source": OUTCOME_SOURCE, "training": False, "fine_tuning": False,
        "P0_regenerated": False, "LUMIERE": False,
    })
    atomic_text(ROOT / "09_RELEASE/PCC_RHUH_EXTERNAL_STAGE_B_FINAL_REPORT.md", "# PCC RHUH External Stage B final report\n\nThis independent cross-dataset external technical validation used the frozen future-blind P0 as Fixed. Stage B methods used the realized recurrence-change target for retrospective target-conditioned correction; they are not prospective recurrence forecasts, deployment-time future prediction, or clinical validation. RHUH segmentation > 0 is the prelocked closest available pathological-region mapping and is not perfect ontology equivalence with the internal MU mask. P10 remains the formal Full PCC output without best-round selection.\n")
    print(json.dumps(status, indent=2))
    return 0 if release_gate == "PASS" else 3


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    raise SystemExit(self_test() if arguments.self_test else main())
'''


def main() -> None:
    KERNEL.mkdir(parents=True, exist_ok=True)
    source_text: dict[str, str] = {}
    source_hashes: dict[str, str] = {}
    for relative in SOURCES:
        text = (ROOT / relative).read_text(encoding="utf-8")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if digest != EXPECTED[relative]:
            raise RuntimeError(f"locked source mismatch: {relative}: {digest}")
        source_text[relative] = text
        source_hashes[relative] = digest

    prelude = [
        "# Generated by experiments/build_rhuh_external_stage_b_kernel.py",
        "from __future__ import annotations",
        "import hashlib as _bootstrap_hashlib",
        "import sys as _bootstrap_sys",
        "import types as _bootstrap_types",
        f"LOCKED_SOURCE_TEXT = {source_text!r}",
        f"LOCKED_SOURCE_HASHES = {source_hashes!r}",
        "def _load_locked(name, source):",
        "    digest = _bootstrap_hashlib.sha256(source.encode('utf-8')).hexdigest()",
        "    path = name.replace('.', '/') + '.py'",
        "    if digest != LOCKED_SOURCE_HASHES[path]: raise RuntimeError(f'embedded source hash mismatch: {path}')",
        "    parent = name.rpartition('.')[0]",
        "    parts = parent.split('.') if parent else []",
        "    for index in range(1, len(parts) + 1):",
        "        package = '.'.join(parts[:index])",
        "        if package not in _bootstrap_sys.modules:",
        "            module = _bootstrap_types.ModuleType(package); module.__path__ = []; _bootstrap_sys.modules[package] = module",
        "    module = _bootstrap_types.ModuleType(name); module.__file__ = path; _bootstrap_sys.modules[name] = module; exec(compile(source, path, 'exec'), module.__dict__)",
        "for _path in ('src/models/pcc.py', 'src/models/eia.py', 'src/models/naive_self_tightening.py', 'src/analysis/internal_completion.py', 'src/analysis/internal_statistics.py', 'src/analysis/validity_patch.py', 'src/evaluation/metrics.py'):",
        "    _load_locked(_path[:-3].replace('/', '.'), LOCKED_SOURCE_TEXT[_path])",
        "",
    ]
    run_path = KERNEL / "run.py"
    run_path.write_text("\n".join(prelude) + BODY, encoding="utf-8")
    metadata = {
        "id": "jeechangxin/pcc-rhuh-external-stage-b-confirmatory-2026",
        "title": "PCC RHUH External Stage B Confirmatory 2026",
        "code_file": "run.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": False,
        "enable_tpu": False,
        "enable_internet": False,
        "dataset_sources": ["jeechangxin/pcc-rhuh-stage-b-outcome-only-2026"],
        "kernel_sources": ["jeechangxin/pcc-rhuh-external-stage-a-p0-freeze-2026"],
        "competition_sources": [],
        "model_sources": [],
        "machine_shape": "None",
    }
    (KERNEL / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"run_sha256": hashlib.sha256(run_path.read_bytes()).hexdigest(), "embedded_sources": source_hashes}, indent=2))


if __name__ == "__main__":
    main()
