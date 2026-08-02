"""Current-only preprocessing for leakage-free cross-case P0 prediction.

This is a literal migration of notebook cell 14's independent five-fold
preprocessing. Future masks are used only by the separate label constructor;
they are never accepted by the predictor-input function.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class CurrentOnlyInputs:
    current_t1c_normalized: np.ndarray
    current_mask: np.ndarray
    model_input_zchw: np.ndarray


def normalize_current_t1c(image: np.ndarray) -> np.ndarray:
    """Apply cell 14's current-volume-only p1/p99 normalization."""
    image = image.astype(np.float32)
    nonzero = image[image > 0]
    if nonzero.size < 100:
        return np.zeros_like(image, dtype=np.float32)
    p1, p99 = np.percentile(nonzero, [1, 99])
    if p99 <= p1:
        return np.zeros_like(image, dtype=np.float32)
    normalized = np.clip(image, p1, p99)
    normalized = (normalized - p1) / (p99 - p1 + 1e-8)
    return np.clip(normalized, 0, 1).astype(np.float32)


def prepare_current_only_inputs(
    current_t1c_hwz: np.ndarray,
    current_mask_hwz: np.ndarray,
) -> CurrentOnlyInputs:
    """Build the historical two-channel Z,C,H,W predictor input."""
    if current_t1c_hwz.shape != current_mask_hwz.shape:
        raise ValueError("Current T1c and current mask shapes differ")
    normalized = normalize_current_t1c(current_t1c_hwz)
    mask = current_mask_hwz > 0.5
    model_input = np.stack(
        [np.moveaxis(normalized, -1, 0), np.moveaxis(mask, -1, 0)],
        axis=1,
    ).astype(np.float16)
    return CurrentOnlyInputs(normalized, mask, model_input)


def construct_future_change_label(
    current_mask_hwz: np.ndarray,
    future_mask_hwz: np.ndarray,
) -> np.ndarray:
    """Construct training/evaluation T separately from P0 preprocessing."""
    if current_mask_hwz.shape != future_mask_hwz.shape:
        raise ValueError("Current and future mask shapes differ")
    return np.logical_and(future_mask_hwz > 0.5, ~(current_mask_hwz > 0.5))
