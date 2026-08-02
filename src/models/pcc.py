"""Final Layer 2R retrospective PCC correction.

Purpose
-------
Reproduce the deterministic PCC Core used by the authoritative 40-case
Layer 2R formal run.

Inputs and outputs
------------------
``apply_pcc`` accepts a baseline probability map and an already constructed
future-change target. Both have shape ``[Z, H, W]``. It returns the corrected
float32 probability map, the boolean target-derived correction region, and
the float32 smoothed target signal.

Dependencies
------------
NumPy and SciPy.

Scientific assumptions
----------------------
The target is ``future tumour mask AND NOT current tumour mask``. Distances
and Gaussian smoothing operate over all three array axes in voxel units.

Expected behaviour
------------------
The operation order, constants, float32 conversions, clipping, smoothing,
and ten logit-space updates reproduce notebook cell 110.

Known limitations
-----------------
The notebook's formal loop rejects empty targets before calling PCC; this
module implements only the PCC transformation itself. Locked-case regression
against the stored formal baseline, target, and PCC maps remains required.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter


DILATION_RADIUS = 26
SIGMA = 2.0
PCC_ROUNDS = 10
PCC_ETA = 0.30


@dataclass(frozen=True)
class PCCResult:
    """Outputs produced by the authoritative PCC Core."""

    corrected_probability: np.ndarray
    correction_region: np.ndarray
    target_signal: np.ndarray
    round_probabilities: tuple[np.ndarray, ...] = ()
    round_statistics: tuple[dict[str, float | int], ...] = ()


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


def safe_logit(p: np.ndarray, eps: float = 1e-5) -> np.ndarray:
    """Apply the notebook's clipped float32 probability-to-logit operation."""
    p = np.clip(p.astype(np.float32), eps, 1 - eps)
    return np.log(p / (1 - p)).astype(np.float32)


def sigmoid(x: np.ndarray) -> np.ndarray:
    """Apply the notebook's clipped float32 logit-to-probability operation."""
    x = np.clip(x.astype(np.float32), -30, 30)
    return (1.0 / (1.0 + np.exp(-x))).astype(np.float32)


def normalize01(x: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    """Apply the notebook's whole-array float32 min-max normalization."""
    x = x.astype(np.float32)
    mn, mx = float(np.min(x)), float(np.max(x))
    if mx <= mn + eps:
        return np.zeros_like(x, dtype=np.float32)
    return ((x - mn) / (mx - mn + eps)).astype(np.float32)


def make_dilated_region(
    mask_bool: np.ndarray,
    radius: float = DILATION_RADIUS,
) -> np.ndarray:
    """Construct the notebook's 3-D target-derived correction region."""
    mask_bool = mask_bool.astype(bool)
    dist = distance_transform_edt(~mask_bool)
    return dist <= radius


def smooth_mask(
    mask_bool: np.ndarray,
    sigma: float = SIGMA,
) -> np.ndarray:
    """Construct the notebook's normalized 3-D smoothed target signal."""
    x = mask_bool.astype(np.float32)
    x = gaussian_filter(x, sigma=sigma)
    return normalize01(x)


def apply_pcc(
    baseline_probability: np.ndarray,
    future_change_target: np.ndarray,
    *,
    eta: float = PCC_ETA,
    sigma: float = SIGMA,
    dilation_radius: float = DILATION_RADIUS,
    iterations: int = PCC_ROUNDS,
    capture_trajectory: bool = False,
) -> PCCResult:
    """Run the final authoritative Layer 2R PCC update sequence."""
    target_bool = future_change_target.astype(bool)

    fixed_baseline = safe_clip_prob(baseline_probability)

    correction_region = make_dilated_region(
        target_bool,
        radius=dilation_radius,
    )
    target_signal = smooth_mask(target_bool, sigma=sigma)

    pcc = fixed_baseline.copy()
    round_probabilities: list[np.ndarray] = []
    round_statistics: list[dict[str, float | int]] = []

    for _ in range(1, iterations + 1):
        p = safe_clip_prob(pcc)

        residual = (
            (target_bool.astype(np.float32) - p)
            * correction_region.astype(np.float32)
        )

        residual_smooth = gaussian_filter(residual, sigma=sigma)

        background_suppression = (
            (~correction_region).astype(np.float32) * p
        )

        logits = safe_logit(p)
        logits = (
            logits
            + eta * residual_smooth
            - eta * background_suppression
        )
        pcc = safe_clip_prob(sigmoid(logits))

        if capture_trajectory:
            round_probabilities.append(pcc.copy())
            target_float = target_bool.astype(np.float32)
            outside_target = (~target_bool).astype(np.float32)
            round_statistics.append(
                {
                    "round": len(round_probabilities),
                    "residual_mean": float(np.mean(residual)),
                    "residual_abs_mass": float(np.abs(residual).sum()),
                    "correction_mass": float(np.abs(pcc - p).sum()),
                    "target_mass": float((pcc * target_float).sum()),
                    "outside_target_mass": float((pcc * outside_target).sum()),
                }
            )

    return PCCResult(
        corrected_probability=pcc,
        correction_region=correction_region,
        target_signal=target_signal,
        round_probabilities=tuple(round_probabilities),
        round_statistics=tuple(round_statistics),
    )
