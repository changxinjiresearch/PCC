"""Layer 1 Formal v1 fixed-baseline tumour segmentation.

Purpose
-------
Reproduce the fixed Baseline-Seg model used by the notebook's Layer 1 Formal
v1 experiment. The model predicts the current tumour mask from normalized
current T1c slices.

Inputs and outputs
------------------
Inference accepts a NumPy float32 array in Z,C,H,W order with one channel:
normalized current T1c. It returns a NumPy float32 sigmoid probability map
with the same Z,1,H,W shape. Thresholding returns a NumPy boolean array.

Dependencies
------------
PyTorch and NumPy. Dataset identity, NIfTI loading, and preprocessing belong
to Orders 1--3 and are intentionally not implemented here.

Scientific assumptions
----------------------
Inputs have already been normalized according to the authoritative notebook
pipeline. A Formal v1 checkpoint is a mapping containing
``model_state_dict`` and the fold-specific train-calibrated ``threshold``.

Expected behavior
-----------------
Architecture and inference operations are transcribed from notebook cell 74;
the formal checkpoint schema comes from cell 75; loading behavior is
confirmed by downstream cell 82 of
``archive/pcc-experiments-original.ipynb``.

Known limitations
-----------------
This module does not train models or select thresholds. Scientific regression
against the real five fold checkpoints and locked cohort remains necessary.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


INPUT_CHANNELS = 1
OUTPUT_CHANNELS = 1
BASE_CHANNELS = 16
INFERENCE_BATCH_SIZE = 64
FIXED_THRESHOLD = 0.5


class ConvBlock(nn.Module):
    """The two-convolution block used by the Formal v1 baseline."""

    def __init__(self, in_ch: int, out_ch: int) -> None:
        super().__init__()

        self.net = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class SmallUNet2D(nn.Module):
    """Exact Layer 1 Formal v1 Baseline-Seg architecture."""

    def __init__(
        self,
        in_ch: int = INPUT_CHANNELS,
        out_ch: int = OUTPUT_CHANNELS,
        base: int = BASE_CHANNELS,
    ) -> None:
        super().__init__()

        self.enc1 = ConvBlock(in_ch, base)
        self.enc2 = ConvBlock(base, base * 2)
        self.bottleneck = ConvBlock(base * 2, base * 4)

        self.pool = nn.MaxPool2d(2)

        self.up2 = nn.ConvTranspose2d(base * 4, base * 2, 2, stride=2)
        self.dec2 = ConvBlock(base * 4, base * 2)

        self.up1 = nn.ConvTranspose2d(base * 2, base, 2, stride=2)
        self.dec1 = ConvBlock(base * 2, base)

        self.out = nn.Conv2d(base, out_ch, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        b = self.bottleneck(self.pool(e2))

        u2 = self.up2(b)
        if u2.shape[-2:] != e2.shape[-2:]:
            u2 = F.interpolate(
                u2,
                size=e2.shape[-2:],
                mode="bilinear",
                align_corners=False,
            )
        d2 = self.dec2(torch.cat([u2, e2], dim=1))

        u1 = self.up1(d2)
        if u1.shape[-2:] != e1.shape[-2:]:
            u1 = F.interpolate(
                u1,
                size=e1.shape[-2:],
                mode="bilinear",
                align_corners=False,
            )
        d1 = self.dec1(torch.cat([u1, e1], dim=1))

        return self.out(d1)


def build_fixed_baseline(
    device: str | torch.device,
) -> SmallUNet2D:
    """Construct the fixed baseline on the requested inference device."""
    return SmallUNet2D(
        in_ch=INPUT_CHANNELS,
        out_ch=OUTPUT_CHANNELS,
        base=BASE_CHANNELS,
    ).to(device)


def get_threshold_from_checkpoint(
    checkpoint: dict[str, Any],
    default: float = FIXED_THRESHOLD,
) -> float:
    """Read the threshold using the downstream notebook compatibility order."""
    for key in ["threshold", "best_threshold", "selected_threshold", "thr"]:
        if key in checkpoint:
            return float(checkpoint[key])
    return float(default)


def load_fixed_baseline_checkpoint(
    checkpoint_path: str | Path,
    device: str | torch.device,
) -> tuple[SmallUNet2D, float]:
    """Load one Formal v1 fold checkpoint with strict state-dict semantics."""
    checkpoint_path = Path(checkpoint_path)
    assert checkpoint_path.exists(), checkpoint_path

    checkpoint = torch.load(checkpoint_path, map_location=device)
    model = build_fixed_baseline(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    threshold = get_threshold_from_checkpoint(checkpoint, default=FIXED_THRESHOLD)
    return model, threshold


@torch.no_grad()
def predict_prob(
    model: nn.Module,
    inputs: np.ndarray,
    device: str | torch.device,
    batch_size: int = INFERENCE_BATCH_SIZE,
) -> np.ndarray:
    """Generate Formal v1 sigmoid probabilities in input slice order."""
    model.eval()
    parts = []

    for start in range(0, inputs.shape[0], batch_size):
        xb = torch.from_numpy(inputs[start : start + batch_size]).float().to(
            device
        )
        logits = model(xb)
        probs = torch.sigmoid(logits).detach().cpu().numpy()
        parts.append(probs.astype(np.float32))

    return np.concatenate(parts, axis=0)


def threshold_probabilities(
    probabilities: np.ndarray,
    threshold: float,
) -> np.ndarray:
    """Apply the notebook's inclusive binary probability threshold."""
    return probabilities >= threshold
