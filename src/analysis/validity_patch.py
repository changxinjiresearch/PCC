"""Locked evaluation utilities for PCC_INTERNAL_VALIDITY_PATCH_2026."""
from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd
from scipy.stats import binomtest, wilcoxon

from src.analysis.internal_statistics import bootstrap_ci, holm_adjust


METHOD_FILES = {
    "FIXED": "P0_REFERENCE",
    "NAIVE": "naive_self_tightening.npy",
    "EIA_LINEAR": "eia_linear.npy",
    "EIA_MORPH": "eia_morph.npy",
    "EIA_BLEND_090": "eia_blend090.npy",
    "EIA_BLEND_075": "eia_blend075.npy",
    "FULL_PCC": "pcc_correction.npy",
}


def average_precision_binary(target: np.ndarray, probability: np.ndarray) -> float:
    """Exact non-interpolated AP; NaN is explicit for an empty target."""
    y = np.asarray(target, dtype=bool).ravel()
    score = np.asarray(probability, dtype=np.float64).ravel()
    positives = int(y.sum())
    if positives == 0:
        return float("nan")
    order = np.argsort(-score, kind="stable")
    sorted_y = y[order]
    cumulative = np.cumsum(sorted_y)
    ranks = np.arange(1, len(y) + 1)
    return float((cumulative[sorted_y] / ranks[sorted_y]).sum() / positives)


def target_independent_metrics(probability: np.ndarray, target: np.ndarray, threshold: float = 0.5) -> dict[str, float | int | str]:
    p = np.asarray(probability, dtype=np.float64)
    y = np.asarray(target, dtype=bool)
    if p.shape != y.shape or not np.isfinite(p).all():
        raise ValueError("Probability/target contract failed")
    pred = p >= threshold
    tp = int((pred & y).sum()); fp = int((pred & ~y).sum()); fn = int((~pred & y).sum()); tn = int((~pred & ~y).sum())
    dice = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 1.0
    iou = tp / (tp + fp + fn) if tp + fp + fn else 1.0
    precision = tp / (tp + fp) if tp + fp else float("nan")
    recall = tp / (tp + fn) if tp + fn else float("nan")
    specificity = tn / (tn + fp) if tn + fp else float("nan")
    soft_dice = float((2 * p[y].sum()) / (p.sum() + y.sum())) if p.sum() + y.sum() else 1.0
    return {
        "threshold": threshold, "dice_fixed": dice, "iou_fixed": iou,
        "precision_fixed": precision, "recall_fixed": recall, "specificity_fixed": specificity,
        "predicted_positive_voxels": int(pred.sum()), "true_target_voxels": int(y.sum()),
        "volume_error_voxels": int(pred.sum()) - int(y.sum()), "soft_dice": soft_dice,
        "brier_score": float(np.mean((p - y.astype(float)) ** 2)),
        "average_precision": average_precision_binary(y, p),
        "average_precision_status": "NOT_APPLICABLE_EMPTY_TARGET" if not y.any() else "AVAILABLE",
        "target_probability_mass": float(p[y].sum()), "outside_target_probability_mass": float(p[~y].sum()),
    }


def threshold_grid_case_dice(probability: np.ndarray, target: np.ndarray, grid: np.ndarray) -> np.ndarray:
    p = np.asarray(probability).ravel(); y = np.asarray(target, dtype=bool).ravel()
    positive=np.sort(p[y]); negative=np.sort(p[~y]); positives=len(positive)
    tp=positives-np.searchsorted(positive,grid,side="left")
    fp=len(negative)-np.searchsorted(negative,grid,side="left")
    fn=positives-tp; denominator=2*tp+fp+fn
    return np.divide(2*tp,denominator,out=np.ones_like(denominator,dtype=float),where=denominator!=0)


def select_crossfit_threshold(training_case_curves: np.ndarray, grid: np.ndarray) -> float:
    means=np.asarray(training_case_curves,dtype=float).mean(axis=0); maximum=means.max()
    return float(grid[np.flatnonzero(np.isclose(means, maximum, rtol=0, atol=1e-15))[0]])


def one_sample_statistics(values: np.ndarray, label: str) -> dict[str, float | int]:
    values=np.asarray(values,dtype=float); values=values[np.isfinite(values)]
    p=1.0 if np.all(values==0) else float(wilcoxon(values,alternative="two-sided",zero_method="wilcox").pvalue)
    low,high=bootstrap_ci(values,label); sd=float(values.std(ddof=1))
    positive=int((values>0).sum()); interval=binomtest(positive,len(values)).proportion_ci(confidence_level=.95,method="exact")
    return {"N":len(values),"mean":float(values.mean()),"SD":sd,"median":float(np.median(values)),"Q1":float(np.quantile(values,.25)),"Q3":float(np.quantile(values,.75)),"bootstrap_95ci_low":low,"bootstrap_95ci_high":high,"wilcoxon_p_two_sided":p,"cohens_dz":float(values.mean()/sd) if sd>0 else 0.0,"positive":positive,"zero":int((values==0).sum()),"negative":int((values<0).sum()),"positive_rate_exact_ci_low":float(interval.low),"positive_rate_exact_ci_high":float(interval.high)}


def apply_holm_by_family(frame: pd.DataFrame, family_column: str = "family") -> pd.DataFrame:
    result=frame.copy(); result["holm_adjusted_p"]=np.nan
    for _,indices in result.groupby(family_column,sort=False).groups.items():
        positions=list(indices); adjusted=holm_adjust(result.loc[positions,"wilcoxon_p_two_sided"].astype(float).tolist())
        result.loc[positions,"holm_adjusted_p"]=adjusted
    return result
