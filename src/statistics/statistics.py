"""Descriptive statistics for the final Layer 2R formal results.

Purpose
-------
Reproduce the deterministic reporting logic in authoritative notebook cells
109 and 110.  The module constructs per-case PCC-minus-comparator records,
method-level summaries, and pairwise summaries from already calculated
per-case metrics.

Inputs and outputs
------------------
All public functions accept long-form pandas ``DataFrame`` objects and return
``DataFrame`` objects, except that ``summarize_methods`` returns ``None`` for
an empty input exactly as the notebook's ``update_summary`` does.  This module
does not discover or persist artifacts.

Dependencies
------------
pandas only.

Scientific assumptions
----------------------
Each formal case has one row for each of the seven authoritative methods.
PCC differences are PCC minus comparator, and a win uses strict greater-than
with no tie tolerance.

Expected behaviour
------------------
Arithmetic, aggregation functions, default pandas group sorting, NaN
handling, dtypes, and output column order follow notebook cells 109 and 110.
No rounding or display formatting is applied.

Known limitations
-----------------
The notebook selects the first matching method row, does not validate
duplicates or non-finite values, and counts unique non-null case identifiers
while aggregating every row.  Those behaviours are intentionally retained.
Regression against the real 40-case stored metric table remains required.
"""

from __future__ import annotations

import pandas as pd


METHOD_ORDER = (
    "fixed_baseline",
    "naive_self_tightening",
    "eia_linear",
    "eia_blend090",
    "eia_blend075",
    "eia_morph",
    "pcc_correction",
)

COMPARATOR_ORDER = METHOD_ORDER[:-1]

PAIRWISE_COLUMNS = (
    "case_id",
    "comparison",
    "dice_diff",
    "iou_diff",
    "target_focus_diff",
    "log10_ratio_diff",
    "pcc_better_dice",
    "pcc_better_iou",
)

METHOD_SUMMARY_COLUMNS = (
    "method",
    "n",
    "dice_mean",
    "dice_median",
    "iou_mean",
    "iou_median",
    "target_focus_mean",
    "target_focus_median",
    "log10_ratio_mean",
    "log10_ratio_median",
)

PAIRWISE_SUMMARY_COLUMNS = (
    "comparison",
    "n",
    "dice_mean_diff",
    "dice_median_diff",
    "dice_wins",
    "iou_mean_diff",
    "iou_median_diff",
    "iou_wins",
    "dice_win_rate",
    "iou_win_rate",
)


def build_pairwise_comparisons(metrics: pd.DataFrame) -> pd.DataFrame:
    """Build the notebook's six PCC-minus-comparator rows per case.

    The notebook performs this operation inside its case loop.  Accepting a
    long-form table is the sole structural wrapper here: cases are processed
    in first-seen order, and each method selection retains the notebook's
    ``iloc[0]`` behaviour.
    """
    comparison_rows = []

    for case_id in metrics["case_id"].drop_duplicates().tolist():
        case_metrics = metrics[metrics["case_id"] == case_id]
        pcc_row = case_metrics[
            case_metrics["method"] == "pcc_correction"
        ].iloc[0].to_dict()

        for method in COMPARATOR_ORDER:
            row = case_metrics[case_metrics["method"] == method].iloc[
                0
            ].to_dict()
            comparison_rows.append(
                {
                    "case_id": case_id,
                    "comparison": f"PCC vs {method}",
                    "dice_diff": pcc_row["dice"] - row["dice"],
                    "iou_diff": pcc_row["iou"] - row["iou"],
                    "target_focus_diff": (
                        pcc_row["target_focus"] - row["target_focus"]
                    ),
                    "log10_ratio_diff": (
                        pcc_row["log10_ratio"] - row["log10_ratio"]
                    ),
                    "pcc_better_dice": bool(
                        pcc_row["dice"] > row["dice"]
                    ),
                    "pcc_better_iou": bool(
                        pcc_row["iou"] > row["iou"]
                    ),
                }
            )

    return pd.DataFrame(comparison_rows, columns=PAIRWISE_COLUMNS)


def summarize_methods(metrics: pd.DataFrame) -> pd.DataFrame | None:
    """Aggregate the notebook's method-level count, means, and medians."""
    if metrics.empty:
        return None

    summary = (
        metrics.groupby("method")
        .agg(
            n=("case_id", "nunique"),
            dice_mean=("dice", "mean"),
            dice_median=("dice", "median"),
            iou_mean=("iou", "mean"),
            iou_median=("iou", "median"),
            target_focus_mean=("target_focus", "mean"),
            target_focus_median=("target_focus", "median"),
            log10_ratio_mean=("log10_ratio", "mean"),
            log10_ratio_median=("log10_ratio", "median"),
        )
        .reset_index()
    )
    return summary.loc[:, METHOD_SUMMARY_COLUMNS]


def summarize_pairwise(comparisons: pd.DataFrame) -> pd.DataFrame:
    """Aggregate paired differences, strict wins, and win rates."""
    summary = (
        comparisons.groupby("comparison")
        .agg(
            n=("case_id", "nunique"),
            dice_mean_diff=("dice_diff", "mean"),
            dice_median_diff=("dice_diff", "median"),
            dice_wins=("pcc_better_dice", "sum"),
            iou_mean_diff=("iou_diff", "mean"),
            iou_median_diff=("iou_diff", "median"),
            iou_wins=("pcc_better_iou", "sum"),
        )
        .reset_index()
    )
    summary["dice_win_rate"] = summary["dice_wins"] / summary["n"]
    summary["iou_win_rate"] = summary["iou_wins"] / summary["n"]
    return summary.loc[:, PAIRWISE_SUMMARY_COLUMNS]
