"""Independent five-fold future-change predictor from notebook cells 16–17."""

from __future__ import annotations

try:
    import torch
    import torch.nn as nn
except ModuleNotFoundError:  # Allows manifest/preflight tooling without torch.
    torch = None
    nn = None


INPUT_CHANNELS = 2
OUTPUT_CHANNELS = 1
BASE_CHANNELS = 16
EPOCHS = 20
BATCH_SIZE = 8
LEARNING_RATE = 1e-3
POS_WEIGHT_MAX = 50.0
SEED = 42


if nn is not None:
    class ConvBlock(nn.Module):
        def __init__(self, in_channels: int, out_channels: int) -> None:
            super().__init__()
            self.net = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, 3, padding=1),
                nn.BatchNorm2d(out_channels), nn.ReLU(inplace=True),
                nn.Conv2d(out_channels, out_channels, 3, padding=1),
                nn.BatchNorm2d(out_channels), nn.ReLU(inplace=True),
            )

        def forward(self, inputs):
            return self.net(inputs)


    class CrossCaseSmallUNet(nn.Module):
        def __init__(self, in_channels=2, out_channels=1, base=16) -> None:
            super().__init__()
            self.enc1 = ConvBlock(in_channels, base)
            self.enc2 = ConvBlock(base, base * 2)
            self.enc3 = ConvBlock(base * 2, base * 4)
            self.pool = nn.MaxPool2d(2)
            self.mid = ConvBlock(base * 4, base * 8)
            self.up3 = nn.ConvTranspose2d(base * 8, base * 4, 2, stride=2)
            self.dec3 = ConvBlock(base * 8, base * 4)
            self.up2 = nn.ConvTranspose2d(base * 4, base * 2, 2, stride=2)
            self.dec2 = ConvBlock(base * 4, base * 2)
            self.up1 = nn.ConvTranspose2d(base * 2, base, 2, stride=2)
            self.dec1 = ConvBlock(base * 2, base)
            self.out = nn.Conv2d(base, out_channels, 1)

        def forward(self, inputs):
            e1 = self.enc1(inputs)
            e2 = self.enc2(self.pool(e1))
            e3 = self.enc3(self.pool(e2))
            middle = self.mid(self.pool(e3))
            d3 = self.dec3(torch.cat([self.up3(middle), e3], dim=1))
            d2 = self.dec2(torch.cat([self.up2(d3), e2], dim=1))
            d1 = self.dec1(torch.cat([self.up1(d2), e1], dim=1))
            return self.out(d1)


    def dice_loss(logits, targets, eps: float = 1e-6):
        probabilities = torch.sigmoid(logits)
        intersection = (probabilities * targets).sum(dim=(1, 2, 3))
        denominator = probabilities.sum(dim=(1, 2, 3)) + targets.sum(dim=(1, 2, 3))
        return 1 - ((2 * intersection + eps) / (denominator + eps)).mean()
else:
    class CrossCaseSmallUNet:  # pragma: no cover - dependency diagnostic
        def __init__(self, *args, **kwargs):
            raise RuntimeError("PyTorch is required for cross-case prediction")


def calculate_pos_weight(targets) -> float:
    positive = float(targets.sum())
    negative = float(targets.size - positive)
    return min(float(negative / (positive + 1e-8)), POS_WEIGHT_MAX)
