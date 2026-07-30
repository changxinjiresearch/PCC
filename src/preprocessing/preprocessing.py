"""Array preprocessing for final Layer 2R longitudinal PCC experiments.

Purpose
-------
Prepare already-loaded ZHW T1c volumes and tumour masks using the final
Layer 2R behavior in cell 110 of
``archive/pcc-experiments-original.ipynb``.

Inputs and outputs
------------------
Inputs are four equally shaped three-dimensional arrays in Z,H,W order:
current and future T1c images, and current and future tumour masks. The main
entry point returns the normalized current image, binarized masks,
future-change target, and joint current/future brain mask.

Dependencies
------------
NumPy. NIfTI loading and the notebook's H,W,Z to Z,H,W shape heuristic belong
to ``src.data.dataset_loader``.

Scientific assumptions
----------------------
Masks use the strict ``> 0`` threshold. The normalization support is the union
of nonzero voxels in the current and future T1c images. The target is future
tumour not already present in the current tumour mask.

Expected behavior
-----------------
The normalization operation order, percentile call, epsilon, clipping, and
dtype conversion are transcribed from notebook cell 110. Model slices contain
normalized current T1c in channel zero and current tumour mask in channel one.

Known limitations
-----------------
No affine-based orientation, registration, resampling, resizing, padding,
cropping, or non-finite-value handling is performed. Shape compatibility is
checked only after loading and axis conversion have occurred elsewhere.
"""

from __future__ import annotations

from typing import NamedTuple, TypeAlias

import numpy as np
from numpy.typing import NDArray


FloatArray: TypeAlias = NDArray[np.float32]
UInt8Array: TypeAlias = NDArray[np.uint8]
BoolArray: TypeAlias = NDArray[np.bool_]


class PreprocessedLongitudinalCase(NamedTuple):
    """Arrays produced by the final Layer 2R preprocessing sequence."""

    current_t1c: FloatArray
    current_mask: FloatArray
    future_mask: UInt8Array
    future_change_target: UInt8Array
    brain_mask: BoolArray


def robust_normalize(
    img: np.ndarray,
    brain_mask: np.ndarray | None = None,
    p_low: float = 1,
    p_high: float = 99,
    eps: float = 1e-6,
) -> FloatArray:
    """Normalize one image exactly as final Layer 2R notebook cell 110."""
    img = img.astype(np.float32)
    if brain_mask is None:
        brain_mask = img != 0

    vals = img[brain_mask]
    if vals.size < 10:
        return np.zeros_like(img, dtype=np.float32)

    lo, hi = np.percentile(vals, [p_low, p_high])
    if hi <= lo + eps:
        return np.zeros_like(img, dtype=np.float32)

    out = np.clip(img, lo, hi)
    out = (out - lo) / (hi - lo + eps)
    out[~brain_mask] = 0
    return out.astype(np.float32)


def binarize_mask(mask: np.ndarray) -> BoolArray:
    """Apply the final Layer 2R strict-positive tumour-mask threshold."""
    return mask > 0


def make_future_change_target(
    current_mask: np.ndarray,
    future_mask: np.ndarray,
) -> BoolArray:
    """Return future tumour voxels not present in the current tumour mask."""
    return np.logical_and(future_mask, np.logical_not(current_mask))


def preprocess_longitudinal_arrays(
    current_t1c: np.ndarray,
    future_t1c: np.ndarray,
    current_mask: np.ndarray,
    future_mask: np.ndarray,
) -> PreprocessedLongitudinalCase:
    """Apply the complete array-only preparation sequence from cell 110."""
    current_mask = current_mask > 0
    future_mask = future_mask > 0

    target = np.logical_and(future_mask, np.logical_not(current_mask))
    brain_mask = np.logical_or(current_t1c != 0, future_t1c != 0)

    current_t1c = robust_normalize(current_t1c, brain_mask=brain_mask)

    assert (
        current_t1c.shape
        == current_mask.shape
        == future_mask.shape
        == target.shape
    )

    return PreprocessedLongitudinalCase(
        current_t1c=current_t1c,
        current_mask=current_mask.astype(np.float32),
        future_mask=future_mask.astype(np.uint8),
        future_change_target=target.astype(np.uint8),
        brain_mask=brain_mask,
    )


def make_two_channel_slice(
    current_t1c: np.ndarray,
    current_mask: np.ndarray,
    z: int,
) -> FloatArray:
    """Construct one cell-110 model input slice in C,H,W order."""
    return np.stack([current_t1c[z], current_mask[z]], axis=0).astype(np.float32)
