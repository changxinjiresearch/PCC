"""Raw NIfTI loading utilities for the PCC longitudinal cohort.

Purpose
-------
Load MRI volumes and tumour masks while preserving the final Layer 2R
notebook behavior from cell 110 of ``archive/pcc-experiments-original.ipynb``.

Inputs and outputs
------------------
Paths are supplied by the dataset identity module. Raw loading returns a
float32 NumPy array with the original NIfTI affine and header. ZHW loading
also returns the original, pre-transpose shape.

Dependencies
------------
NumPy and nibabel.

Scientific assumptions
----------------------
The notebook treats a three-dimensional array whose first two dimensions are
equal and whose last dimension is smaller as H,W,Z and transposes it to
Z,H,W. All other three-dimensional shapes are retained unchanged.

Known limitations
-----------------
This is a shape heuristic, not affine-based reorientation. The returned
affine and header describe the original NIfTI image and are not rewritten
after a ZHW transpose. Loading does not normalize, binarize, crop, resize, or
resample data.
"""

from __future__ import annotations

from pathlib import Path
from typing import TypeAlias

import nibabel as nib
import numpy as np
from numpy.typing import NDArray


FloatArray: TypeAlias = NDArray[np.float32]
Shape: TypeAlias = tuple[int, ...]
LoadedRawNifti: TypeAlias = tuple[
    FloatArray,
    NDArray[np.floating],
    nib.nifti1.Nifti1Header,
]
LoadedZhwNifti: TypeAlias = tuple[
    FloatArray,
    NDArray[np.floating],
    nib.nifti1.Nifti1Header,
    Shape,
]


def load_nii_raw(path: str | Path) -> LoadedRawNifti:
    """Load one NIfTI exactly as in the final Layer 2R notebook."""
    image = nib.load(str(path))
    array = image.get_fdata(dtype=np.float32)
    return array, image.affine, image.header


def to_zhw(array: np.ndarray) -> FloatArray:
    """Apply the notebook's three-dimensional H,W,Z to Z,H,W heuristic."""
    array = np.asarray(array)
    if array.ndim != 3:
        raise ValueError(f"Expected 3D array, got {array.shape}")
    if array.shape[0] == array.shape[1] and array.shape[-1] < array.shape[0]:
        array = np.transpose(array, (2, 0, 1))
    return array.astype(np.float32)


def load_nii_zhw(path: str | Path) -> LoadedZhwNifti:
    """Load one NIfTI and return ZHW data plus original loading metadata."""
    array, affine, header = load_nii_raw(path)
    array_zhw = to_zhw(array)
    return array_zhw, affine, header, array.shape


def validate_shape_compatibility(*arrays: np.ndarray) -> None:
    """Assert the all-volume shape equality used by notebook smoke cell 101."""
    if not arrays:
        return
    first_shape = arrays[0].shape
    assert all(array.shape == first_shape for array in arrays), (
        "Shape mismatch after ZHW conversion."
    )
