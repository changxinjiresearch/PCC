"""Final formal Layer 2R case-specific baseline training.

Purpose
-------
Reproduce only the per-case two-channel baseline-training lifecycle from the
authoritative 40-case formal runs in notebook cells 109--110 of
``archive/pcc-experiments-original.ipynb``.

Inputs and outputs
------------------
Training consumes aligned ``[Z, H, W]`` arrays: normalized current T1c,
current tumour mask, and future-change target.  It returns the best-epoch
model, a float32 sigmoid probability map in ``[Z, H, W]`` order, the complete
12-epoch history, best top-k Dice, and elapsed training time.

Dependencies
------------
NumPy, pandas, and PyTorch, plus the migrated Order 8 formal metric function.

Scientific assumptions
----------------------
Every case is fitted independently on all of its slices.  The same full-case
future-change target is used for optimization and best-epoch selection.  Run
seeds are set outside each case lifecycle and are deliberately not reset per
case, preserving the notebook's execution-order dependence.

Expected behaviour
------------------
Architecture, PyTorch constructor calls, DataLoader arguments, loss operation
order, mode transitions, gradient operations, strict best-state selection,
slice-wise inference, checkpoint fields, and dtypes follow the final formal
notebook literally.  No thresholding or post-processing is applied to the
baseline probability map.

Known limitations
-----------------
The notebook does not enable deterministic CUDA algorithms or pin every
PyTorch default.  Results therefore depend on the PyTorch/CUDA environment
and on the run-level RNG state.  Interrupted cases restart from epoch one
because optimizer and RNG state are not checkpointed.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

from src.evaluation.metrics import eval_prob_map


SEED = 42
FORMAL_EPOCHS = 12
BATCH_SIZE = 8
LEARNING_RATE = 1e-3
BASE_CHANNELS = 16
INPUT_CHANNELS = 2
OUTPUT_CHANNELS = 1
SOFT_DICE_EPS = 1e-6
POS_WEIGHT_MIN = 1.0
POS_WEIGHT_MAX = 80.0
CHECKPOINT_NAME_TEMPLATE = "{case_id}_baseline_formal_best.pt"
BASELINE_MAP_FILENAME = "baseline_prob_map_formal_float16.npy"


class SliceDataset(Dataset):
    """All Z slices from one authoritative formal Layer 2R case."""

    def __init__(
        self,
        current_t1c: np.ndarray,
        current_mask: np.ndarray,
        target: np.ndarray,
    ) -> None:
        self.current_t1c = current_t1c.astype(np.float32)
        self.current_mask = current_mask.astype(np.float32)
        self.target = target.astype(np.float32)
        self.indices = np.arange(current_t1c.shape[0])

    def __len__(self) -> int:
        return len(self.indices)

    def __getitem__(
        self,
        index: int,
    ) -> tuple[torch.Tensor, torch.Tensor, int]:
        z = self.indices[index]
        x = np.stack(
            [self.current_t1c[z], self.current_mask[z]],
            axis=0,
        ).astype(np.float32)
        y = self.target[z][None, :, :].astype(np.float32)
        return torch.from_numpy(x), torch.from_numpy(y), int(z)


class ConvBlock(nn.Module):
    """The two-convolution block from the final formal MiniUNet."""

    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return self.net(inputs)


class MiniUNet(nn.Module):
    """Exact two-channel MiniUNet used by formal Layer 2R."""

    def __init__(
        self,
        in_channels: int = INPUT_CHANNELS,
        out_channels: int = OUTPUT_CHANNELS,
        base: int = BASE_CHANNELS,
    ) -> None:
        super().__init__()
        self.enc1 = ConvBlock(in_channels, base)
        self.pool1 = nn.MaxPool2d(2)
        self.enc2 = ConvBlock(base, base * 2)
        self.pool2 = nn.MaxPool2d(2)

        self.bottleneck = ConvBlock(base * 2, base * 4)

        self.up2 = nn.ConvTranspose2d(base * 4, base * 2, 2, stride=2)
        self.dec2 = ConvBlock(base * 4, base * 2)

        self.up1 = nn.ConvTranspose2d(base * 2, base, 2, stride=2)
        self.dec1 = ConvBlock(base * 2, base)

        self.out = nn.Conv2d(base, out_channels, 1)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        encoded1 = self.enc1(inputs)
        encoded2 = self.enc2(self.pool1(encoded1))
        bottleneck = self.bottleneck(self.pool2(encoded2))

        decoded2 = self.up2(bottleneck)
        decoded2 = torch.cat([decoded2, encoded2], dim=1)
        decoded2 = self.dec2(decoded2)

        decoded1 = self.up1(decoded2)
        decoded1 = torch.cat([decoded1, encoded1], dim=1)
        decoded1 = self.dec1(decoded1)

        return self.out(decoded1)


def seed_formal_run(seed: int = SEED) -> None:
    """Set the four run-level seeds used at the start of each formal cell."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def soft_dice_loss_from_logits(
    logits: torch.Tensor,
    targets: torch.Tensor,
    eps: float = SOFT_DICE_EPS,
) -> torch.Tensor:
    """Calculate the notebook's batch-mean soft Dice loss."""
    probabilities = torch.sigmoid(logits)
    dimensions = (1, 2, 3)
    intersection = torch.sum(probabilities * targets, dimensions)
    denominator = torch.sum(probabilities, dimensions) + torch.sum(
        targets,
        dimensions,
    )
    dice = (2 * intersection + eps) / (denominator + eps)
    return 1 - dice.mean()


def calculate_pos_weight(target: np.ndarray) -> float:
    """Calculate the case-specific clipped positive BCE weight."""
    positive = float(target.sum())
    negative = float(target.size - target.sum())
    return min(
        POS_WEIGHT_MAX,
        max(POS_WEIGHT_MIN, negative / max(positive, 1.0)),
    )


@torch.no_grad()
def predict_full_volume(
    model: nn.Module,
    current_t1c: np.ndarray,
    current_mask: np.ndarray,
    device: str | torch.device,
) -> np.ndarray:
    """Generate the formal float32 probability map one Z slice at a time."""
    model.eval()
    predictions = np.zeros_like(current_t1c, dtype=np.float32)

    for z in range(current_t1c.shape[0]):
        inputs = np.stack(
            [current_t1c[z], current_mask[z]],
            axis=0,
        )[None].astype(np.float32)
        input_tensor = torch.from_numpy(inputs).to(device)
        logits = model(input_tensor)
        probability = torch.sigmoid(logits).detach().cpu().numpy()[0, 0]
        predictions[z] = probability.astype(np.float32)

    return predictions


@dataclass
class FormalBaselineTrainingResult:
    """The five values returned by the notebook's per-case trainer."""

    model: MiniUNet
    baseline_probability: np.ndarray
    history: pd.DataFrame
    best_dice_topk: float
    elapsed_seconds: float


def train_case_baseline(
    case_id: str,
    current_t1c: np.ndarray,
    current_mask: np.ndarray,
    target: np.ndarray,
    device: str | torch.device,
) -> FormalBaselineTrainingResult:
    """Run the exact 12-epoch formal baseline lifecycle for one case.

    This function deliberately does not seed the RNG.  The authoritative
    notebook seeds once per formal-cell execution, not once per case.
    """
    dataset = SliceDataset(current_t1c, current_mask, target)
    loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0,
    )

    pos_weight_value = calculate_pos_weight(target)
    pos_weight = torch.tensor(
        [pos_weight_value],
        dtype=torch.float32,
        device=device,
    )

    model = MiniUNet(
        in_channels=INPUT_CHANNELS,
        out_channels=OUTPUT_CHANNELS,
        base=BASE_CHANNELS,
    ).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    bce_loss = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    def combined_loss(logits: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        return bce_loss(logits, y) + soft_dice_loss_from_logits(logits, y)

    best_dice_topk = -1.0
    best_state = None
    history: list[dict[str, object]] = []

    start = time.time()

    for epoch in range(1, FORMAL_EPOCHS + 1):
        model.train()
        losses = []

        for inputs, y, _ in loader:
            inputs = inputs.to(device)
            y = y.to(device)

            optimizer.zero_grad()
            logits = model(inputs)
            loss = combined_loss(logits, y)
            loss.backward()
            optimizer.step()

            losses.append(float(loss.item()))

        probability_map = predict_full_volume(
            model,
            current_t1c,
            current_mask,
            device,
        )
        metrics = eval_prob_map(
            probability_map,
            target,
            threshold=0.5,
            main_mode="topk",
        )

        row = {
            "case_id": case_id,
            "epoch": epoch,
            "loss": float(np.mean(losses)),
            "pos_weight": float(pos_weight_value),
            **metrics,
        }
        history.append(row)

        if row["dice_topk"] > best_dice_topk:
            best_dice_topk = row["dice_topk"]
            best_state = {
                key: value.detach().cpu().clone()
                for key, value in model.state_dict().items()
            }

    model.load_state_dict(best_state)
    baseline_probability = predict_full_volume(
        model,
        current_t1c,
        current_mask,
        device,
    )

    elapsed = time.time() - start

    return FormalBaselineTrainingResult(
        model=model,
        baseline_probability=baseline_probability.astype(np.float32),
        history=pd.DataFrame(history),
        best_dice_topk=float(best_dice_topk),
        elapsed_seconds=elapsed,
    )


def checkpoint_filename(case_id: str) -> str:
    """Return the exact per-case formal checkpoint filename."""
    return CHECKPOINT_NAME_TEMPLATE.format(case_id=case_id)


def make_formal_checkpoint(
    case_id: str,
    result: FormalBaselineTrainingResult,
    protocol: Mapping[str, object],
) -> dict[str, object]:
    """Construct the exact mapping written by the formal case loop."""
    return {
        "case_id": case_id,
        "formal_epochs": FORMAL_EPOCHS,
        "model_state_dict": result.model.state_dict(),
        "best_dice_topk": result.best_dice_topk,
        "protocol": protocol,
    }


def save_formal_checkpoint(
    checkpoint_dir: str | Path,
    case_id: str,
    result: FormalBaselineTrainingResult,
    protocol: Mapping[str, object],
) -> Path:
    """Directly overwrite the formal checkpoint exactly as the notebook."""
    path = Path(checkpoint_dir) / checkpoint_filename(case_id)
    torch.save(make_formal_checkpoint(case_id, result, protocol), path)
    return path


def save_baseline_probability(
    case_output_dir: str | Path,
    baseline_probability: np.ndarray,
) -> Path:
    """Save the formal float16 storage copy of the baseline probability."""
    path = Path(case_output_dir) / BASELINE_MAP_FILENAME
    np.save(path, baseline_probability.astype(np.float16))
    return path
