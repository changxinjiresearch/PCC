"""Final Layer 2R segmentation evaluation metrics.

Purpose
-------
Reproduce the deterministic evaluation logic used by the authoritative
Layer 2R 40-case formal comparison.

Inputs and outputs
------------------
``eval_prob_map`` accepts a probability map and an aligned target mask of
the same shape. The formal experiment uses three-dimensional ``[Z, H, W]``
case volumes, although the metric operations reduce over every array element.
It returns the notebook's fixed-threshold, target-volume top-k, probability
concentration, voxel-count, and probability-summary fields.

Dependencies
------------
NumPy only.

Scientific assumptions
----------------------
The target is the already constructed future-change mask. Canonical formal
Dice and IoU use a target-volume-matched top-k prediction; fixed-threshold
metrics at an inclusive threshold of 0.5 are retained as secondary fields.

Expected behaviour
------------------
Float32 conversion, non-finite replacement, clipping, Boolean casting,
ranking, equations, epsilons, and operation order reproduce authoritative
notebook cells 109 and 110 exactly.

Known limitations
-----------------
The top-k volume is derived from the target. An empty target still selects
one prediction voxel because the notebook clamps ``k`` to at least one.
Ties at the top-k boundary follow NumPy ``argpartition`` behaviour. The
notebook performs no explicit shape, dimensionality, or mode validation.
"""

from __future__ import annotations

import numpy as np


THRESHOLD = 0.5
MAIN_MODE = "topk"
DICE_IOU_EPS = 1e-6
CONCENTRATION_EPS = 1e-8


def dice_binary(
    pred: np.ndarray,
    target: np.ndarray,
    eps: float = DICE_IOU_EPS,
) -> float:
    """Calculate the notebook's smoothed binary Dice score."""
    pred = pred.astype(bool)
    target = target.astype(bool)
    inter = np.logical_and(pred, target).sum()
    denom = pred.sum() + target.sum()
    return float((2 * inter + eps) / (denom + eps))


def iou_binary(
    pred: np.ndarray,
    target: np.ndarray,
    eps: float = DICE_IOU_EPS,
) -> float:
    """Calculate the notebook's smoothed binary intersection over union."""
    pred = pred.astype(bool)
    target = target.astype(bool)
    inter = np.logical_and(pred, target).sum()
    union = np.logical_or(pred, target).sum()
    return float((inter + eps) / (union + eps))


def topk_mask(prob: np.ndarray, k: int) -> np.ndarray:
    """Select the notebook's flattened top-k probability mask."""
    prob = prob.astype(np.float32)
    flat = prob.reshape(-1)
    k = int(k)
    k = max(1, min(k, flat.size))
    idx = np.argpartition(flat, -k)[-k:]
    out = np.zeros_like(flat, dtype=np.uint8)
    out[idx] = 1
    return out.reshape(prob.shape).astype(bool)


def target_focus(
    prob: np.ndarray,
    target: np.ndarray,
    eps: float = CONCENTRATION_EPS,
) -> float:
    """Calculate probability mass inside the target over total mass."""
    prob = prob.astype(np.float32)
    target = target.astype(bool)
    total = float(prob.sum())
    inside = float(prob[target].sum())
    return float(inside / (total + eps))


def log10_ratio(
    prob: np.ndarray,
    target: np.ndarray,
    eps: float = CONCENTRATION_EPS,
) -> float:
    """Calculate the log10 target-to-non-target mean probability ratio."""
    prob = prob.astype(np.float32)
    target = target.astype(bool)
    inside_mean = float(prob[target].mean()) if target.sum() > 0 else 0.0
    outside_mean = (
        float(prob[~target].mean()) if (~target).sum() > 0 else 0.0
    )
    return float(np.log10((inside_mean + eps) / (outside_mean + eps)))


def safe_clip_prob(x: np.ndarray) -> np.ndarray:
    """Apply the notebook's float32 conversion and probability clipping."""
    return np.clip(
        np.nan_to_num(
            x.astype(np.float32),
            nan=0.0,
            posinf=1.0,
            neginf=0.0,
        ),
        0,
        1,
    )


def eval_prob_map(
    prob: np.ndarray,
    target: np.ndarray,
    threshold: float = THRESHOLD,
    main_mode: str = MAIN_MODE,
) -> dict[str, float | int | str]:
    """Evaluate one case probability map exactly as in the formal run."""
    prob = safe_clip_prob(prob)
    target_bool = target.astype(bool)

    pred_fixed = prob >= threshold
    k = int(target_bool.sum())
    pred_topk = topk_mask(prob, k)

    out: dict[str, float | int | str] = {
        "dice_fixed05": dice_binary(pred_fixed, target_bool),
        "iou_fixed05": iou_binary(pred_fixed, target_bool),
        "dice_topk": dice_binary(pred_topk, target_bool),
        "iou_topk": iou_binary(pred_topk, target_bool),
        "target_focus": target_focus(prob, target_bool),
        "log10_ratio": log10_ratio(prob, target_bool),
        "pred_fixed05_voxels": int(pred_fixed.sum()),
        "pred_topk_voxels": int(pred_topk.sum()),
        "target_voxels": int(target_bool.sum()),
        "prob_min": float(prob.min()),
        "prob_max": float(prob.max()),
        "prob_mean": float(prob.mean()),
        "prob_sum": float(prob.sum()),
    }

    if main_mode == "topk":
        out["dice"] = out["dice_topk"]
        out["iou"] = out["iou_topk"]
        out["main_mode"] = "topk"
    else:
        out["dice"] = out["dice_fixed05"]
        out["iou"] = out["iou_fixed05"]
        out["main_mode"] = "fixed05"

    return out
