"""Locked generators and PCC variants for PCC_INTERNAL_COMPLETION_2026.

This module never imports or calls the predictor.  All functions operate on
already frozen P0 arrays and guidance masks.  The implementation follows the
protocol locked at commit 3ed97f2 and must not be tuned after observing results.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from itertools import product

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, label

from src.models.pcc import make_dilated_region, safe_clip_prob, safe_logit, sigmoid

ROUNDS = 10
ETA = 0.30
RADIUS = 26.0
SIGMA = 2.0
CONNECTIVITY_26 = np.ones((3, 3, 3), dtype=np.uint8)
FP_SEEDS = (20260803, 20260804, 20260805, 20260806, 20260807)
SHIFT_DIRECTIONS = ("+x", "-x", "+y", "-y", "+z", "-z")


@dataclass(frozen=True)
class VariantResult:
    probability: np.ndarray
    correction_region: np.ndarray


def run_variant(
    p0: np.ndarray,
    guidance: np.ndarray,
    *,
    error_guided: bool = True,
    outside_suppression: bool = True,
    smoothing: bool = True,
    global_discrepancy: bool = False,
    rounds: int = ROUNDS,
) -> VariantResult:
    """Run one prespecified term ablation from the frozen P0."""
    target = guidance.astype(bool)
    region = make_dilated_region(target, radius=RADIUS)
    p = safe_clip_prob(p0).copy()
    if not error_guided and not outside_suppression:
        return VariantResult(p, region)
    for _ in range(rounds):
        current = safe_clip_prob(p)
        discrepancy = target.astype(np.float32) - current
        if not global_discrepancy:
            discrepancy *= region.astype(np.float32)
        signal = gaussian_filter(discrepancy, sigma=SIGMA) if smoothing else discrepancy
        outside = current * (~region).astype(np.float32)
        logits = safe_logit(current)
        if error_guided:
            logits = logits + ETA * signal
        if outside_suppression:
            logits = logits - ETA * outside
        p = safe_clip_prob(sigmoid(logits))
    return VariantResult(p.astype(np.float32), region)


def stable_seed(case_id: str, seed: int) -> int:
    payload = f"{seed}:{case_id}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def component_count(mask: np.ndarray) -> int:
    return int(label(mask.astype(bool), structure=CONNECTIVITY_26)[1])


def partial_guidance(mask: np.ndarray, fraction: float) -> tuple[np.ndarray, float]:
    """Keep the deepest deterministic fraction within every 26-connected component."""
    source = mask.astype(bool)
    components, count = label(source, structure=CONNECTIVITY_26)
    kept = np.zeros_like(source)
    for component_id in range(1, count + 1):
        component = components == component_id
        coordinates = np.argwhere(component)
        requested = max(1, int(round(len(coordinates) * fraction)))
        distances = distance_transform_edt(component)[component]
        # np.lexsort uses the final key as primary: greatest distance, then Z/Y/X.
        order = np.lexsort((coordinates[:, 2], coordinates[:, 1], coordinates[:, 0], -distances))
        selected = coordinates[order[:requested]]
        kept[tuple(selected.T)] = True
    retained = float(kept.sum() / source.sum()) if source.any() else 0.0
    return kept, retained


def fp25_guidance(mask: np.ndarray, spacing_zyx: tuple[float, float, float], case_id: str, seed: int, *, reference_volume: int | None = None) -> tuple[np.ndarray, int, int]:
    """Add locked-seed FP voxels from the physical 5–15 mm external annulus."""
    source = mask.astype(bool)
    distance = distance_transform_edt(~source, sampling=spacing_zyx)
    candidates = np.argwhere((~source) & (distance >= 5.0) & (distance <= 15.0))
    requested = int(round((source.sum() if reference_volume is None else reference_volume) * 0.25))
    take = min(requested, len(candidates))
    rng = np.random.default_rng(stable_seed(case_id, seed))
    chosen = rng.choice(len(candidates), size=take, replace=False) if take else np.array([], dtype=int)
    result = source.copy()
    if take:
        selected = candidates[chosen]
        result[tuple(selected.T)] = True
    return result, take, requested - take


def shift_no_wrap(mask: np.ndarray, direction: str, amount: int = 3) -> np.ndarray:
    """Shift a Z-Y-X mask in one named physical-axis direction without wrap."""
    axis_sign = {"+x": (2, 1), "-x": (2, -1), "+y": (1, 1), "-y": (1, -1), "+z": (0, 1), "-z": (0, -1)}
    axis, sign = axis_sign[direction]
    result = np.zeros_like(mask, dtype=bool)
    source = [slice(None)] * 3
    destination = [slice(None)] * 3
    if sign > 0:
        source[axis] = slice(0, -amount); destination[axis] = slice(amount, None)
    else:
        source[axis] = slice(amount, None); destination[axis] = slice(0, -amount)
    result[tuple(destination)] = mask.astype(bool)[tuple(source)]
    return result


def mixed_guidance(mask: np.ndarray, spacing_zyx: tuple[float, float, float], case_id: str, seed: int, direction: str) -> tuple[np.ndarray, dict[str, float | int | str]]:
    partial, retained = partial_guidance(mask, 0.50)
    with_fp, added, shortfall = fp25_guidance(partial, spacing_zyx, case_id, seed, reference_volume=int(mask.astype(bool).sum()))
    shifted = shift_no_wrap(with_fp, direction, 3)
    return shifted, {"retained_true_target_fraction": retained, "added_false_positive_volume": added, "fp_shortfall": shortfall, "displacement": direction, "seed": seed}


def physical_dilate(mask: np.ndarray, spacing_zyx: tuple[float, float, float], distance_mm: float = 2.0) -> np.ndarray:
    return distance_transform_edt(~mask.astype(bool), sampling=spacing_zyx) <= distance_mm


def physical_erode(mask: np.ndarray, spacing_zyx: tuple[float, float, float], distance_mm: float = 2.0) -> np.ndarray:
    source = mask.astype(bool)
    return source & (distance_transform_edt(source, sampling=spacing_zyx) > distance_mm)


def large_components(mask: np.ndarray, spacing_zyx: tuple[float, float, float], minimum_mm3: float = 100.0) -> np.ndarray:
    components, count = label(mask.astype(bool), structure=CONNECTIVITY_26)
    voxel_volume = float(np.prod(spacing_zyx))
    retained = np.zeros_like(mask, dtype=bool)
    for component_id in range(1, count + 1):
        component = components == component_id
        if float(component.sum()) * voxel_volume >= minimum_mm3:
            retained |= component
    return retained


def deranged_donors(case_ids: list[str], target_volumes: dict[str, int], patient_ids: dict[str, str], seed: int = 20260803) -> dict[str, str]:
    """Find a deterministic minimum-cost patient-disjoint derangement.

    Dynamic programming over bitmasks is infeasible for 40 cases, so this uses
    deterministic minimum-cost bipartite assignment.  SciPy's assignment result
    is deterministic for the fully tie-broken cost matrix.
    """
    from scipy.optimize import linear_sum_assignment

    ordered = sorted(case_ids)
    volumes = np.array([target_volumes[c] for c in ordered], dtype=float)
    ranks = np.argsort(np.argsort(volumes, kind="stable"), kind="stable")
    quartiles = np.minimum(3, (ranks * 4) // len(ordered))
    cost = np.empty((len(ordered), len(ordered)), dtype=np.float64)
    huge = 1e12
    for i, recipient in enumerate(ordered):
        for j, donor in enumerate(ordered):
            if recipient == donor or patient_ids[recipient] == patient_ids[donor]:
                cost[i, j] = huge
                continue
            qdist = abs(int(quartiles[i]) - int(quartiles[j]))
            vdist = abs(np.log1p(volumes[i]) - np.log1p(volumes[j]))
            tie = stable_seed(f"{recipient}:{donor}", seed) / 2**64
            cost[i, j] = qdist * 1e6 + vdist * 1e3 + tie
    rows, columns = linear_sum_assignment(cost)
    mapping = {ordered[i]: ordered[j] for i, j in zip(rows, columns)}
    if len(mapping) != len(ordered) or any(k == v or patient_ids[k] == patient_ids[v] for k, v in mapping.items()):
        raise RuntimeError("Patient-disjoint derangement could not be constructed")
    return mapping
