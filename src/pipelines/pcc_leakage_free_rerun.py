"""Retrospective methods over one immutable leakage-free held-out P0."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
import numpy as np

from src.evaluation.metrics import eval_prob_map
from src.models.eia import apply_eia
from src.models.naive_self_tightening import naive_self_tighten
from src.models.pcc import apply_pcc


@dataclass(frozen=True)
class RetrospectiveCaseResult:
    p0: np.ndarray
    target: np.ndarray
    method_maps: dict[str, np.ndarray]
    trajectory: tuple[np.ndarray, ...]
    round_rows: tuple[dict[str, float | int], ...]
    method_rows: tuple[dict[str, float | str], ...]


def run_retrospective_methods(p0: np.ndarray, target: np.ndarray) -> RetrospectiveCaseResult:
    """Run all methods from exactly the same immutable P0 and clean T."""
    p0 = np.asarray(p0, dtype=np.float32).copy()
    target = np.asarray(target, dtype=np.uint8).copy()
    pcc = apply_pcc(p0, target, capture_trajectory=True)
    eia = apply_eia(p0, target)
    maps = {
        "fixed_baseline": p0.copy(),
        "naive_self_tightening": naive_self_tighten(p0),
        "eia_linear": eia.linear,
        "eia_blend090": eia.blend090,
        "eia_blend075": eia.blend075,
        "eia_morph": eia.morph,
        "pcc_correction": pcc.corrected_probability,
    }
    rows = []
    for index, probability in enumerate(pcc.round_probabilities, start=1):
        metrics = eval_prob_map(probability, target)
        rows.append({**pcc.round_statistics[index - 1], "dice": metrics["dice_topk"], "iou": metrics["iou_topk"]})
    method_rows = tuple(
        {"method": method, **eval_prob_map(probability, target)}
        for method, probability in maps.items()
    )
    return RetrospectiveCaseResult(
        p0, target, maps, pcc.round_probabilities, tuple(rows), method_rows
    )


def persist_retrospective_case(root: Path, case_id: str, result: RetrospectiveCaseResult) -> None:
    """Persist P0, P1..PR, method maps, and atomic per-round statistics."""
    case = root / "cases" / case_id
    case.mkdir(parents=True, exist_ok=True)
    np.save(case / "P0.npy", result.p0.astype(np.float32))
    np.save(case / "target.npy", result.target.astype(np.uint8))
    for index, probability in enumerate(result.trajectory, start=1):
        np.save(case / f"P{index}.npy", probability.astype(np.float32))
    for method, probability in result.method_maps.items():
        np.save(case / f"{method}.npy", probability.astype(np.float32))
    path = case / "pcc_round_trajectory.csv"
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        fieldnames = tuple(result.round_rows[0]) if result.round_rows else ("round",)
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(result.round_rows)
    temporary.replace(path)
    metrics_path = case / "method_metrics.csv"
    metrics_temporary = metrics_path.with_suffix(".csv.tmp")
    with metrics_temporary.open("w", newline="", encoding="utf-8") as stream:
        fieldnames = tuple(result.method_rows[0])
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader(); writer.writerows(result.method_rows)
    metrics_temporary.replace(metrics_path)
    (case / "RETROSPECTIVE_COMPLETE.json").write_text(
        '{"status":"complete","shared_p0":true,"shared_clean_target":true}',
        encoding="utf-8",
    )
