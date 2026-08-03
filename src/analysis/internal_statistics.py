"""Prespecified case-level statistics for PCC_INTERNAL_COMPLETION_2026."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

BOOTSTRAP_SEED = 20260803
BOOTSTRAP_RESAMPLES = 10_000


def stable_seed(label: str) -> int:
    return int.from_bytes(hashlib.sha256(f"{BOOTSTRAP_SEED}:{label}".encode()).digest()[:8], "big")


def bootstrap_ci(values: np.ndarray, label: str) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(stable_seed(label))
    means = values[rng.integers(0, len(values), size=(BOOTSTRAP_RESAMPLES, len(values)))].mean(axis=1)
    return tuple(float(x) for x in np.quantile(means, [0.025, 0.975]))


def holm_adjust(p_values: list[float]) -> list[float]:
    """Holm adjusted p-values in original order."""
    if not p_values:
        return []
    p = np.asarray(p_values, dtype=float)
    order = np.argsort(p, kind="stable")
    ranked = np.maximum.accumulate((len(p) - np.arange(len(p))) * p[order])
    result = np.empty_like(ranked)
    result[order] = np.minimum(ranked, 1.0)
    return [float(x) for x in result]


def summarize(frame: pd.DataFrame, group_columns: list[str], metrics: tuple[str, ...] = ("dice", "iou")) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for keys, group in frame.groupby(group_columns, dropna=False, sort=True):
        keys = keys if isinstance(keys, tuple) else (keys,)
        base = dict(zip(group_columns, keys))
        for metric in metrics:
            values = group[metric].astype(float).to_numpy()
            low, high = bootstrap_ci(values, ":".join(map(str, keys)) + ":" + metric)
            rows.append({**base, "metric": metric, "N": len(values), "mean": values.mean(), "SD": values.std(ddof=1), "median": np.median(values), "Q1": np.quantile(values, .25), "Q3": np.quantile(values, .75), "bootstrap_95ci_low": low, "bootstrap_95ci_high": high})
    return pd.DataFrame(rows)


def paired_family(frame: pd.DataFrame, *, condition_column: str, reference: str, comparisons: list[str], family: str, metrics: tuple[str, ...] = ("dice", "iou")) -> pd.DataFrame:
    """Pair unique case-level condition results and apply Holm within metric."""
    rows: list[dict[str, object]] = []
    for metric in metrics:
        metric_rows = []
        pivot = frame.pivot(index="case_id", columns=condition_column, values=metric)
        for comparison in comparisons:
            paired = pivot[[comparison, reference]].dropna().astype(float)
            delta = paired[comparison].to_numpy() - paired[reference].to_numpy()
            if len(delta) == 0:
                continue
            p_value = 1.0 if np.all(delta == 0) else float(wilcoxon(delta, zero_method="wilcox", alternative="two-sided").pvalue)
            sd = float(delta.std(ddof=1)) if len(delta) > 1 else float("nan")
            metric_rows.append({"family": family, "metric": metric, "comparison": comparison, "reference": reference, "N": len(delta), "paired_mean_difference": delta.mean(), "paired_median_difference": np.median(delta), "wilcoxon_p": p_value, "paired_cohens_dz": (delta.mean() / sd if sd > 0 else (0.0 if np.all(delta == 0) else float("nan"))), "wins": int((delta > 0).sum()), "ties": int((delta == 0).sum()), "losses": int((delta < 0).sum())})
        adjusted = holm_adjust([row["wilcoxon_p"] for row in metric_rows])
        for row, value in zip(metric_rows, adjusted):
            row["holm_adjusted_p"] = value
        rows.extend(metric_rows)
    return pd.DataFrame(rows)


def aggregate_repeats(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate stochastic/directional repeats within each case before inference."""
    numeric = [column for column in frame.columns if column not in {"case_id", "condition", "method", "repeat", "displacement"} and pd.api.types.is_numeric_dtype(frame[column])]
    return frame.groupby(["case_id", "condition", "method"], as_index=False, dropna=False)[numeric].mean()
