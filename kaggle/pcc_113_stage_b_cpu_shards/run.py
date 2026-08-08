"""CPU-only PCC 113 Stage B shard runner.

The runner does not train or call a predictor. It locates the already frozen
P0 bytes, verifies their locked hashes, reads only current/future masks, and
immediately reduces each method map to locked case metrics.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import nibabel as nib
import numpy as np

from src.analysis.internal_completion import run_variant
from src.analysis.validity_patch import target_independent_metrics
from src.evaluation.metrics import eval_prob_map
from src.models.eia import apply_eia
from src.models.naive_self_tightening import naive_self_tighten
from src.models.pcc import apply_pcc, safe_clip_prob


METHODS = ["Fixed", "Naive", "EIA-linear", "EIA-blend-0.90", "EIA-blend-0.75", "EIA-morph", "Full PCC", "No-smoothing PCC"]
ROOT = Path("/kaggle/working/pcc_113_stage_b")
SHARD = int(os.environ.get("PCC_STAGE_B_SHARD", "0"))
ATTEMPT = int(os.environ.get("PCC_STAGE_B_ATTEMPT", "1"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    tmp.replace(path)


def atomic_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def locate(name: str) -> Path:
    candidates = [Path("/kaggle/input") / name, Path("/kaggle/working") / name, Path(name)]
    for p in candidates:
        if p.exists(): return p
    for root in (Path("/kaggle/input"), Path("/kaggle/working")):
        for p in root.rglob(Path(name).name):
            return p
    raise FileNotFoundError(name)


def load_manifest() -> tuple[list[dict], dict[str, dict], dict[str, dict]]:
    shard_path = locate("LOCKED_113_STAGE_B_CORRECTION_SHARD_MANIFEST.csv")
    case_path = locate("LOCKED_113_CONFIRMATORY_CASE_MANIFEST.csv")
    p0_path = locate("LOCKED_113_P0_SHA256.csv")
    with shard_path.open(newline="", encoding="utf-8") as f: shards = list(csv.DictReader(f))
    with case_path.open(newline="", encoding="utf-8") as f: cases = {r["patient_id"]: r for r in csv.DictReader(f)}
    with p0_path.open(newline="", encoding="utf-8") as f: p0 = {r["patient_id"]: r for r in csv.DictReader(f)}
    selected = [r for r in shards if int(r["stage_b_shard"]) == SHARD]
    if len(selected) != {0: 29, 1: 27, 2: 29, 3: 28}[SHARD]: raise RuntimeError("shard identity/count failure")
    return selected, cases, p0


def load_zhw(path: Path) -> tuple[np.ndarray, np.ndarray, tuple[str, ...]]:
    img = nib.load(str(path)); arr = img.get_fdata(dtype=np.float32)
    if arr.ndim != 3: raise ValueError(f"not 3-D: {path}")
    if arr.shape[0] == arr.shape[1] and arr.shape[-1] < arr.shape[0]: arr = np.transpose(arr, (2, 0, 1))
    return arr.astype(np.float32), np.asarray(img.affine), nib.aff2axcodes(img.affine)


def metric_row(prob: np.ndarray, target: np.ndarray) -> dict:
    m = target_independent_metrics(prob, target, threshold=0.5)
    k = int(target.sum()); top = eval_prob_map(prob, target, threshold=0.5, main_mode="fixed05")
    pred_v = int(m["predicted_positive_voxels"]); target_v = int(m["true_target_voxels"])
    return {"Dice_0.5": m["dice_fixed"], "IoU_0.5": m["iou_fixed"], "precision_0.5": m["precision_fixed"], "recall_0.5": m["recall_fixed"], "soft_Dice": m["soft_dice"], "Brier": m["brier_score"], "average_precision": m["average_precision"], "predicted_positive_volume": pred_v, "target_volume": target_v, "target_to_predicted_volume_ratio": (target_v / pred_v if pred_v else float("nan")), "topk_Dice": top["dice_topk"], "topk_IoU": top["iou_topk"], "numeric_status": "PASS", "failure_status": ""}


def failure_row(reason: str) -> dict:
    return {k: ("FAIL" if k == "numeric_status" else reason if k == "failure_status" else "") for k in ["Dice_0.5", "IoU_0.5", "precision_0.5", "recall_0.5", "soft_Dice", "Brier", "average_precision", "predicted_positive_volume", "target_volume", "target_to_predicted_volume_ratio", "topk_Dice", "topk_IoU", "numeric_status", "failure_status"]}


def main() -> int:
    started = time.time(); rows, cases, p0_manifest = load_manifest()
    case_rows: list[dict] = []; trajectory: list[dict] = []; targets: list[dict] = []; failures: list[dict] = []
    metric_fields = ["patient_id", "case_id", "shard", "method", "Dice_0.5", "IoU_0.5", "precision_0.5", "recall_0.5", "soft_Dice", "Brier", "average_precision", "predicted_positive_volume", "target_volume", "target_to_predicted_volume_ratio", "topk_Dice", "topk_IoU", "numeric_status", "failure_status", "attempt_id", "method_code_hash", "P0_hash", "target_hash"]
    for shard_row in rows:
        pid = shard_row["patient_id"]; case_id = shard_row["case_id"]; p0_hash = p0_manifest[pid]["sha256"]
        target_hash = ""; target = None; common_failure = ""
        try:
            c = cases[pid]; p0file = locate(Path(p0_manifest[pid]["p0_path"]).name)
            actual_p0_hash = sha256(p0file)
            if actual_p0_hash != p0_hash: raise RuntimeError("P0_HASH_MISMATCH")
            p0 = np.load(p0file, allow_pickle=False)
            current_file = Path(c["current_mask_path"]); future_file = Path(c["future_mask_path"])
            if not current_file.exists(): current_file = locate(current_file.name)
            if not future_file.exists(): future_file = locate(future_file.name)
            current, ca, co = load_zhw(current_file); future, fa, fo = load_zhw(future_file)
            if current.shape != future.shape or not np.array_equal(ca, fa) or co != fo: raise RuntimeError("GEOMETRY_MISMATCH")
            if p0.shape != current.shape: raise RuntimeError("SHAPE_MISMATCH")
            target = np.logical_and(future > 0.5, np.logical_not(current > 0.5)).astype(bool)
            target_hash = hashlib.sha256(target.tobytes(order="C")).hexdigest()
            targets.append({"patient_id": pid, "case_id": case_id, "target_shape": str(tuple(target.shape)), "target_voxel_count": int(target.sum()), "current_mask_voxel_count": int((current > 0.5).sum()), "future_mask_voxel_count": int((future > 0.5).sum()), "target_array_sha256": target_hash, "geometry_status": "PASS", "construction_status": "PASS" if target.any() else "FAIL_EMPTY_TARGET"})
            if not target.any(): raise RuntimeError("EMPTY_TARGET")
            fixed = safe_clip_prob(p0); naive = naive_self_tighten(p0); eia = apply_eia(p0, target); full = apply_pcc(p0, target, capture_trajectory=True); nosmooth = run_variant(p0, target, smoothing=False)
            outputs = [fixed, naive, eia.linear, eia.blend090, eia.blend075, eia.morph, full.corrected_probability, nosmooth.probability]
            for method, prob in zip(METHODS, outputs):
                mm = metric_row(prob, target); case_rows.append({"patient_id": pid, "case_id": case_id, "shard": SHARD, "method": method, **mm, "attempt_id": f"shard{SHARD}_attempt{ATTEMPT}", "method_code_hash": "locked_method_sources", "P0_hash": p0_hash, "target_hash": target_hash})
            for n, prob in enumerate(full.round_probabilities, 1):
                tm = metric_row(prob, target); trajectory.append({"patient_id": pid, "case_id": case_id, "round": n, "Dice_0.5": tm["Dice_0.5"], "IoU_0.5": tm["IoU_0.5"], "soft_Dice": tm["soft_Dice"], "Brier": tm["Brier"], "average_precision": tm["average_precision"], "predicted_positive_volume": tm["predicted_positive_volume"], "numeric_status": "PASS", "failure_status": ""})
            del p0, current, future, target, fixed, naive, eia, full, nosmooth, outputs
        except Exception as exc:
            common_failure = str(exc); failures.append({"patient_id": pid, "case_id": case_id, "shard": SHARD, "attempt_id": f"shard{SHARD}_attempt{ATTEMPT}", "failure_status": common_failure})
            if not targets or targets[-1].get("patient_id") != pid:
                targets.append({"patient_id": pid, "case_id": case_id, "target_shape": "", "target_voxel_count": "", "current_mask_voxel_count": "", "future_mask_voxel_count": "", "target_array_sha256": target_hash, "geometry_status": "FAIL", "construction_status": common_failure})
            for method in METHODS: case_rows.append({"patient_id": pid, "case_id": case_id, "shard": SHARD, "method": method, **failure_row(common_failure), "attempt_id": f"shard{SHARD}_attempt{ATTEMPT}", "method_code_hash": "locked_method_sources", "P0_hash": p0_hash, "target_hash": target_hash})
            for n in range(1, 11): trajectory.append({"patient_id": pid, "case_id": case_id, "round": n, "Dice_0.5": "", "IoU_0.5": "", "soft_Dice": "", "Brier": "", "average_precision": "", "predicted_positive_volume": "", "numeric_status": "FAIL", "failure_status": common_failure})
    out = ROOT / f"shard_{SHARD}"
    atomic_csv(out / "SHARD_CASE_METHOD_METRICS.csv", case_rows, metric_fields)
    atomic_csv(out / "SHARD_FULL_PCC_TRAJECTORY.csv", trajectory, ["patient_id", "case_id", "round", "Dice_0.5", "IoU_0.5", "soft_Dice", "Brier", "average_precision", "predicted_positive_volume", "numeric_status", "failure_status"])
    atomic_csv(out / "SHARD_TARGET_MANIFEST.csv", targets, list(targets[0]))
    atomic_csv(out / "SHARD_FAILURE_LOG.csv", failures, ["patient_id", "case_id", "shard", "attempt_id", "failure_status"])
    atomic_json(out / "SHARD_RUNTIME_INFO.json", {"shard": SHARD, "attempt": ATTEMPT, "accelerator": "CPU", "pid": os.getpid(), "elapsed_seconds": time.time() - started, "methods": METHODS, "p0_regenerated": False, "model_training": False, "predictor_forward": False, "future_t1c_read": False})
    atomic_json(out / "SHARD_COMPLETION_STATUS.json", {"status": "PASS" if len(case_rows) == len(rows) * 8 else "BLOCKED", "shard": SHARD, "cases": len(rows), "case_method_rows": len(case_rows), "trajectory_rows": len(trajectory), "failures": len(failures), "attempt": ATTEMPT})
    return 0


if __name__ == "__main__": raise SystemExit(main())
