"""Naive self-tightening of fixed-baseline probability maps.

Purpose
-------
Reproduce the notebook's deterministic naive correction baseline.

Inputs and outputs
------------------
The public function accepts a NumPy-compatible fixed-baseline probability
map and returns a NumPy float32 probability map with the same shape.

Dependencies
------------
NumPy only.

Scientific assumptions
----------------------
The input is the fixed-baseline probability map. The notebook first converts
it to float32, replaces non-finite values, and clips it to [0, 1]. It then
applies one scaled-logit transformation with ``NAIVE_GAMMA = 2.5``.

Expected behaviour
------------------
Operation order, clipping, epsilon values, float32 conversions, and sigmoid
clipping reproduce the authoritative notebook expression exactly.

Known limitations
-----------------
This module performs no evaluation. Agreement with the 40 formal
fixed-baseline prediction maps and locked cohort remains unverified.
"""

from __future__ import annotations

import numpy as np


NAIVE_GAMMA = 2.5


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


def naive_self_tighten(baseline: np.ndarray) -> np.ndarray:
    """Perform the notebook's single naive self-tightening transformation."""
    fixed_baseline = safe_clip_prob(baseline)
    naive = sigmoid(NAIVE_GAMMA * safe_logit(fixed_baseline))
    return naive
