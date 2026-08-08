"""Final Layer 2R EIA comparison methods.

Purpose
-------
Reproduce the four deterministic EIA comparators used by the authoritative
Layer 2R formal experiment.

Inputs and outputs
------------------
``apply_eia`` accepts a fixed-baseline probability map and an already
constructed future-change target. Both are expected to have the same array
shape. It returns four float32 EIA maps together with the boolean
target-derived support region and float32 smoothed target signal.

Dependencies
------------
NumPy and SciPy.

Scientific assumptions
----------------------
The target is ``future tumour mask AND NOT current tumour mask``. Euclidean
distance, Gaussian smoothing, binary morphology, and connected-component
labelling operate over all three volume axes with SciPy defaults.

Expected behaviour
------------------
Constants, operation order, float32 conversions, clipping, thresholding,
morphology, and component filtering reproduce authoritative notebook cell
110 exactly.

Known limitations
-----------------
This module assumes the caller has constructed the target and aligned it
with the baseline. It performs no evaluation. Locked-cohort regression
against the 40 formal EIA maps remains required.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import (
    binary_closing,
    binary_fill_holes,
    distance_transform_edt,
    gaussian_filter,
    label,
)


DILATION_RADIUS = 26
SIGMA = 2.0
EIA_ALPHA = 0.30
EIA_BETA = 0.30
EIA_BLEND_LAMBDA_090 = 0.90
EIA_BLEND_LAMBDA_075 = 0.75
THRESHOLD = 0.5
MIN_COMPONENT_SIZE = 20


@dataclass(frozen=True)
class EIAResult:
    """Outputs produced by the authoritative EIA comparison methods."""

    linear: np.ndarray
    blend090: np.ndarray
    blend075: np.ndarray
    morph: np.ndarray
    support_region: np.ndarray
    target_signal: np.ndarray


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
    """Construct the notebook's 3-D target-derived EIA support region."""
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


def apply_eia(
    baseline_probability: np.ndarray,
    future_change_target: np.ndarray,
    *,
    alpha: float = EIA_ALPHA,
    beta: float = EIA_BETA,
    blend_lambda_090: float = EIA_BLEND_LAMBDA_090,
    blend_lambda_075: float = EIA_BLEND_LAMBDA_075,
    dilation_radius: float = DILATION_RADIUS,
    sigma: float = SIGMA,
    threshold: float = THRESHOLD,
    min_component_size: int = MIN_COMPONENT_SIZE,
) -> EIAResult:
    """Run all four authoritative Layer 2R EIA comparison methods."""
    target_bool = future_change_target.astype(bool)
    fixed_baseline = safe_clip_prob(baseline_probability)

    support_region = make_dilated_region(
        target_bool,
        radius=dilation_radius,
    )
    target_signal = smooth_mask(target_bool, sigma=sigma)

    linear = safe_clip_prob(
        fixed_baseline
        + alpha * target_signal * (1.0 - fixed_baseline)
        - beta
        * (~support_region).astype(np.float32)
        * fixed_baseline
    )

    blend090 = safe_clip_prob(
        blend_lambda_090 * fixed_baseline
        + (1.0 - blend_lambda_090) * target_signal
    )

    blend075 = safe_clip_prob(
        blend_lambda_075 * fixed_baseline
        + (1.0 - blend_lambda_075) * target_signal
    )

    baseline_binary = fixed_baseline >= threshold
    morph = np.logical_and(baseline_binary, support_region)
    morph = binary_closing(morph, iterations=1)
    morph = binary_fill_holes(morph)
    labelled, component_count = label(morph)
    keep = np.zeros_like(morph, dtype=bool)
    for component_id in range(1, component_count + 1):
        component = labelled == component_id
        if component.sum() >= min_component_size:
            keep |= component

    return EIAResult(
        linear=linear,
        blend090=blend090,
        blend075=blend075,
        morph=keep.astype(np.float32),
        support_region=support_region,
        target_signal=target_signal,
    )
