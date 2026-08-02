"""Fold locking and data-isolation contracts for leakage-free held-out P0."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable, Mapping
import numpy as np

from src.preprocessing.current_only_preprocessing import (
    construct_future_change_label,
    prepare_current_only_inputs,
)


@dataclass(frozen=True)
class CaseIdentity:
    case_id: str
    patient_id: str


def build_group_folds(
    cases: Iterable[CaseIdentity], *, n_splits: int = 5, seed: int = 42
) -> list[dict[str, str | int]]:
    """Deterministically assign whole patients to one held-out fold."""
    cases = sorted(cases, key=lambda value: (value.patient_id, value.case_id))
    patients = sorted({case.patient_id for case in cases})
    if len(patients) < n_splits:
        raise ValueError("Fewer patients than folds")
    shuffled = np.asarray(patients, dtype=object)
    np.random.RandomState(seed).shuffle(shuffled)
    test_groups = [set(group.tolist()) for group in np.array_split(shuffled, n_splits)]
    patient_fold = {
        patient: fold
        for fold, group in enumerate(test_groups, start=1)
        for patient in group
    }
    rows: list[dict[str, str | int]] = []
    for fold in range(1, n_splits + 1):
        for case in cases:
            rows.append({
                "fold": fold,
                "split": "test" if patient_fold[case.patient_id] == fold else "train",
                "case_id": case.case_id,
                "patient_id": case.patient_id,
            })
    validate_fold_isolation(rows, n_splits=n_splits)
    return rows


def validate_fold_isolation(rows: Iterable[Mapping[str, object]], *, n_splits=5) -> None:
    rows = list(rows)
    for fold in range(1, n_splits + 1):
        train = {str(r["patient_id"]) for r in rows if r["fold"] == fold and r["split"] == "train"}
        test = {str(r["patient_id"]) for r in rows if r["fold"] == fold and r["split"] == "test"}
        if train & test:
            raise ValueError(f"Patient leakage in fold {fold}")
    test_counts: dict[str, int] = {}
    for row in rows:
        if row["split"] == "test":
            case_id = str(row["case_id"])
            test_counts[case_id] = test_counts.get(case_id, 0) + 1
    if not test_counts or any(count != 1 for count in test_counts.values()):
        raise ValueError("Every case must be held out exactly once")


def write_locked_fold_manifest(path: Path, rows: list[Mapping[str, object]]) -> str:
    """Write the manifest once and return its SHA-256; never overwrite it."""
    if path.exists():
        raise FileExistsError(f"Locked fold manifest already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("fold", "split", "case_id", "patient_id"))
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)
    return sha256(path.read_bytes()).hexdigest()


def assert_training_case_ids(rows, fold: int, test_case_id: str) -> tuple[str, ...]:
    train = tuple(str(r["case_id"]) for r in rows if r["fold"] == fold and r["split"] == "train")
    if test_case_id in train:
        raise ValueError("Held-out test case entered training dataset")
    return train


def discover_longitudinal_cases(dataset_root: Path, *, limit_patients: int = 40) -> list[dict[str, str]]:
    """Recover cell 14's earliest consecutive usable pair per patient."""
    import re

    def number(path: Path) -> int:
        match = re.search(r"Timepoint_(\d+)", path.name)
        return int(match.group(1)) if match else -1

    rows = []
    for patient in sorted(dataset_root.glob("PatientID_*")):
        usable = []
        for timepoint in sorted(patient.glob("Timepoint_*"), key=number):
            t1c = list(timepoint.glob("*_brain_t1c.nii"))
            mask = list(timepoint.glob("*_tumorMask.nii"))
            if len(t1c) == len(mask) == 1:
                usable.append((number(timepoint), timepoint.name, t1c[0], mask[0]))
        if len(usable) >= 2:
            current, future = usable[0], usable[1]
            rows.append({
                "case_id": f"{patient.name}_T{current[0]}_to_T{future[0]}_t1c",
                "patient_id": patient.name,
                "current_timepoint": current[1],
                "future_timepoint": future[1],
                "current_t1c_path": str(current[2]),
                "current_mask_path": str(current[3]),
                "future_mask_path": str(future[3]),
            })
        if len(rows) == limit_patients:
            break
    return rows


def write_locked_case_manifest(path: Path, rows: list[Mapping[str, object]]) -> str:
    if path.exists():
        raise FileExistsError(f"Locked case manifest already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = (
        "case_id", "patient_id", "current_timepoint", "future_timepoint",
        "current_t1c_path", "current_mask_path", "future_mask_path",
    )
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)
    return sha256(path.read_bytes()).hexdigest()


def run_fold_training(
    case_rows: list[Mapping[str, str]],
    fold_rows: list[Mapping[str, object]],
    fold: int,
    output_root: Path,
    *,
    epochs: int = 20,
    batch_size: int = 8,
    learning_rate: float = 1e-3,
    device: str = "cuda",
    max_test_cases: int | None = None,
    max_train_cases: int | None = None,
) -> None:
    """Train on fold-train targets and persist current-only held-out P0 maps."""
    import random
    import nibabel as nib
    import torch
    from torch.utils.data import DataLoader, Dataset
    from src.models.crosscase_future_predictor import (
        CrossCaseSmallUNet, calculate_pos_weight, dice_loss,
    )

    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    by_id = {row["case_id"]: row for row in case_rows}
    train_ids = [str(row["case_id"]) for row in fold_rows if row["fold"] == fold and row["split"] == "train"]
    test_ids = [str(row["case_id"]) for row in fold_rows if row["fold"] == fold and row["split"] == "test"]
    if max_test_cases is not None:
        test_ids = test_ids[:max_test_cases]
    if max_train_cases is not None:
        train_ids = train_ids[:max_train_cases]
    if set(train_ids) & set(test_ids):
        raise RuntimeError("Train/test case leakage")

    class TrainingSlices(Dataset):
        def __init__(self):
            xs, ys = [], []
            for case_id in train_ids:
                row = by_id[case_id]
                current = nib.load(row["current_t1c_path"]).get_fdata().astype(np.float32)
                current_mask = nib.load(row["current_mask_path"]).get_fdata()
                future_mask = nib.load(row["future_mask_path"]).get_fdata()
                inputs = prepare_current_only_inputs(current, current_mask).model_input_zchw
                label = np.moveaxis(construct_future_change_label(current_mask, future_mask), -1, 0)[:, None]
                keep = (label.reshape(len(label), -1).sum(1) > 0) | (inputs[:, 1].reshape(len(inputs), -1).sum(1) > 0)
                xs.append(inputs[keep]); ys.append(label[keep].astype(np.uint8))
            self.x = np.concatenate(xs); self.y = np.concatenate(ys)

        def __len__(self): return len(self.x)
        def __getitem__(self, index):
            return torch.from_numpy(self.x[index]).float(), torch.from_numpy(self.y[index]).float()

    fold_root = output_root / "folds" / f"fold_{fold}"
    fold_root.mkdir(parents=True, exist_ok=True)
    checkpoint = fold_root / "best_training_loss.pt"
    dataset = TrainingSlices()
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0, pin_memory=torch.cuda.is_available())
    model = CrossCaseSmallUNet().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    pos_weight = calculate_pos_weight(dataset.y)
    bce = torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor([pos_weight], device=device))
    best_loss = float("inf")
    history = []
    for epoch in range(1, epochs + 1):
        model.train(); losses = []
        for inputs, labels in loader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad(); logits = model(inputs)
            loss = 0.5 * bce(logits, labels) + 0.5 * dice_loss(logits, labels)
            loss.backward(); optimizer.step(); losses.append(float(loss.item()))
        mean_loss = float(np.mean(losses))
        history.append((fold, epoch, mean_loss, pos_weight, len(train_ids), len(dataset)))
        if mean_loss < best_loss:
            best_loss = mean_loss
            torch.save(model.state_dict(), checkpoint)
    history_path = fold_root / "training_history.csv"
    with history_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream); writer.writerow(("fold", "epoch", "mean_loss", "pos_weight", "train_cases", "train_slices")); writer.writerows(history)
    model.load_state_dict(torch.load(checkpoint, map_location=device)); model.eval()
    for case_id in test_ids:
        case_root = output_root / "held_out_p0" / case_id
        complete = case_root / "P0_COMPLETE.json"
        if complete.exists():
            continue
        row = by_id[case_id]
        current = nib.load(row["current_t1c_path"]).get_fdata().astype(np.float32)
        current_mask = nib.load(row["current_mask_path"]).get_fdata()
        inputs = prepare_current_only_inputs(current, current_mask).model_input_zchw
        probabilities = []
        with torch.no_grad():
            for start in range(0, len(inputs), batch_size):
                tensor = torch.from_numpy(inputs[start:start + batch_size]).float().to(device)
                probabilities.append(torch.sigmoid(model(tensor)).cpu().numpy()[:, 0])
        p0 = np.concatenate(probabilities).astype(np.float32)
        case_root.mkdir(parents=True, exist_ok=True)
        np.save(case_root / "P0_float32.npy", p0)
        complete.write_text(
            '{"status":"complete","future_information_used":false}',
            encoding="utf-8",
        )
