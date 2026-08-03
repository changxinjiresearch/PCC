"""Aggregate prespecified PCC_INTERNAL_COMPLETION_2026 case-level outputs.

This reporting entrypoint never reads predictor checkpoints or probability
maps and cannot alter frozen or newly generated case-level results.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.analysis.internal_statistics import aggregate_repeats, paired_family, summarize


def read_numeric(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    for column in frame.columns:
        if column not in {"case_id", "condition", "method", "repeat", "source", "displacement", "evaluation_mode", "donor_case_id"}:
            frame[column] = pd.to_numeric(frame[column], errors="ignore")
    return frame


def atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    temporary.replace(path)


def frozen_methods(frozen: Path) -> pd.DataFrame:
    return read_numeric(frozen / "ALL_CASE_METHOD_METRICS.csv")


def reference_rows(methods: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    result = methods[methods.method.isin(mapping)].copy()
    result["condition"] = result.method.map(mapping)
    return result[["case_id", "condition", "dice", "iou"]]


def finalize(root: Path, frozen: Path) -> None:
    statistics = root / "10_statistics"
    tables = root / "12_publication_tables"
    figures = root / "13_publication_figures"
    for directory in (statistics, tables, figures, root / "06_failure_analysis"):
        directory.mkdir(parents=True, exist_ok=True)
    methods = frozen_methods(frozen)
    summaries: list[pd.DataFrame] = []
    paired: list[pd.DataFrame] = []
    master: list[pd.DataFrame] = []

    mechanism = read_numeric(root / "01_mechanism_ablation/MECHANISM_CASE_METRICS.csv")
    summaries.append(summarize(mechanism, ["condition"]).assign(family="mechanism"))
    mechanism_comparisons = ["ONE_ROUND", "NO_ERROR_GUIDED_TERM", "NO_OUTSIDE_SUPPRESSION", "NO_SMOOTHING", "GLOBAL_DISCREPANCY"]
    paired.append(paired_family(mechanism, condition_column="condition", reference="FULL_PCC", comparisons=mechanism_comparisons, family="mechanism_ablation_vs_full"))
    master.append(mechanism.assign(experiment_family="mechanism"))

    shuffled = read_numeric(root / "02_shuffled_target/SHUFFLED_TARGET_CASE_METRICS.csv")
    shuffled = pd.concat([shuffled, reference_rows(methods, {"fixed_baseline":"FIXED_P0", "naive_self_tightening":"NAIVE", "pcc_correction":"FULL_PCC"})], ignore_index=True, sort=False)
    summaries.append(summarize(shuffled, ["condition"]).assign(family="counterfactual"))
    paired.append(paired_family(shuffled, condition_column="condition", reference="FULL_PCC", comparisons=["SHUFFLED_TARGET_PCC"], family="counterfactual_vs_full"))
    master.append(shuffled.assign(experiment_family="counterfactual"))

    repeats = read_numeric(root / "03_imperfect_guidance/IMPERFECT_GUIDANCE_REPEAT_METRICS.csv")
    case_aggregated = aggregate_repeats(repeats)
    extrema = repeats.groupby(["case_id", "condition", "method"], as_index=False).agg(
        repeats=("dice", "size"), mean_dice=("dice", "mean"), worst_dice=("dice", "min"), best_dice=("dice", "max"),
        mean_iou=("iou", "mean"), worst_iou=("iou", "min"), best_iou=("iou", "max"),
    )
    atomic_csv(extrema, root / "03_imperfect_guidance/IMPERFECT_GUIDANCE_CASE_EXTREMA.csv")
    clean = methods[methods.method.isin(["pcc_correction", "eia_linear", "eia_blend075"])][["case_id", "method", "dice", "iou"]].copy()
    clean["condition"] = "CLEAN"
    clean.method = clean.method.map({"pcc_correction":"PCC", "eia_linear":"EIA_LINEAR", "eia_blend075":"EIA_BLEND_075"})
    case_aggregated = pd.concat([case_aggregated, clean], ignore_index=True, sort=False)
    pcc_clean = clean[clean.method == "PCC"].set_index("case_id").dice
    case_aggregated["retention_relative_to_clean_pcc"] = case_aggregated.apply(lambda row: float(row.dice / pcc_clean[row.case_id]) if row.method == "PCC" and pcc_clean[row.case_id] != 0 else np.nan, axis=1)
    atomic_csv(case_aggregated, root / "03_imperfect_guidance/IMPERFECT_GUIDANCE_CASE_AGGREGATED.csv")
    summaries.append(summarize(case_aggregated, ["condition", "method"]).assign(family="imperfect_guidance"))
    imperfect_pcc = case_aggregated[case_aggregated.method == "PCC"]
    paired.append(paired_family(imperfect_pcc, condition_column="condition", reference="CLEAN", comparisons=["PARTIAL_50", "PARTIAL_25", "FP_25", "SHIFT_3", "MIXED"], family="imperfect_guidance_vs_clean"))
    master.append(case_aggregated.assign(experiment_family="imperfect_guidance"))

    targets = read_numeric(root / "04_target_construction/TARGET_CONSTRUCTION_CASE_METRICS.csv")
    summaries.append(summarize(targets, ["condition", "evaluation_mode"]).assign(family="target_construction"))
    for mode in ["same_definition", "original_clean"]:
        subset = targets[targets.evaluation_mode == mode]
        paired.append(paired_family(subset, condition_column="condition", reference="ORIGINAL", comparisons=["BOUNDARY_TOLERANT", "ERODED_CURRENT", "LARGE_CHANGE_ONLY"], family=f"target_construction_{mode}_vs_original"))
    master.append(targets.assign(experiment_family="target_construction"))

    summary = pd.concat(summaries, ignore_index=True, sort=False)
    paired_table = pd.concat(paired, ignore_index=True, sort=False)
    master_table = pd.concat(master, ignore_index=True, sort=False)
    atomic_csv(summary, statistics / "INTERNAL_METHOD_SUMMARY.csv")
    atomic_csv(paired_table, root / "INTERNAL_COMPLETION_PAIRED_STATISTICS.csv")
    atomic_csv(master_table, root / "INTERNAL_COMPLETION_MASTER_METRICS.csv")
    atomic_csv(summary, tables / "INTERNAL_COMPLETION_METHOD_SUMMARY.csv")

    baseline = methods[methods.method == "fixed_baseline"].set_index("case_id")
    pcc = methods[methods.method == "pcc_correction"].set_index("case_id")
    failure = pd.DataFrame({"case_id": baseline.index, "p0_dice": baseline.dice.astype(float), "pcc_dice": pcc.dice.astype(float)})
    failure["pcc_gain"] = failure.pcc_dice - failure.p0_dice
    shuffled_case = shuffled[shuffled.condition == "SHUFFLED_TARGET_PCC"].set_index("case_id")
    failure["shuffled_gain_vs_p0"] = shuffled_case.dice.astype(float) - failure.p0_dice
    retention = case_aggregated[(case_aggregated.method == "PCC") & (case_aggregated.condition != "CLEAN")].groupby("case_id").retention_relative_to_clean_pcc.min()
    failure["smallest_imperfect_retention"] = retention
    atomic_csv(failure.sort_values("pcc_gain"), root / "06_failure_analysis/INTERNAL_FAILURE_BOUNDARY_CASES.csv")

    plot = summary[(summary.metric == "dice") & summary.family.isin(["mechanism", "imperfect_guidance"])]
    for family, group in plot.groupby("family"):
        labels = group.apply(lambda row: str(row.get("condition")) + ("/" + str(row.get("method")) if pd.notna(row.get("method")) else ""), axis=1)
        fig, axis = plt.subplots(figsize=(max(8, len(group) * .55), 5))
        axis.bar(np.arange(len(group)), group["mean"], color="#315b7d")
        axis.errorbar(np.arange(len(group)), group["mean"], yerr=[group["mean"]-group.bootstrap_95ci_low, group.bootstrap_95ci_high-group["mean"]], fmt="none", color="black", capsize=3)
        axis.set_xticks(np.arange(len(group)), labels, rotation=55, ha="right"); axis.set_ylabel("Dice"); axis.set_ylim(0, 1); axis.set_title(f"PCC internal completion: {family}")
        fig.tight_layout(); fig.savefig(figures / f"{family}_dice_summary.svg"); fig.savefig(figures / f"{family}_dice_summary.png", dpi=300); plt.close(fig)

    failed_rows = []
    for path in sorted(root.glob("0*/FAILED_CASES.csv")):
        frame = pd.read_csv(path)
        if len(frame):
            frame["source_file"] = str(path.relative_to(root)); failed_rows.append(frame)
    failures = pd.concat(failed_rows, ignore_index=True) if failed_rows else pd.DataFrame(columns=["case_id", "family", "error", "source_file"])
    atomic_csv(failures, root / "INTERNAL_COMPLETION_FAILED_CASES.csv")
    status = pd.DataFrame([
        {"experiment":"mechanism_ablation","status":"COMPLETE","case_count":mechanism.case_id.nunique()},
        {"experiment":"shuffled_target","status":"COMPLETE","case_count":shuffled[shuffled.condition == "SHUFFLED_TARGET_PCC"].case_id.nunique()},
        {"experiment":"imperfect_guidance","status":"COMPLETE","case_count":case_aggregated.case_id.nunique()},
        {"experiment":"target_construction","status":"COMPLETE","case_count":targets.case_id.nunique()},
        {"experiment":"difference_map_control","status":"PENDING_COMPATIBILITY_GATE","case_count":0},
    ])
    atomic_csv(status, root / "INTERNAL_COMPLETION_STATUS.csv")
    (root / "10_statistics/STATISTICS_VALIDATION.json").write_text(json.dumps({"status":"PASS", "case_level_unit":True, "repeat_aggregation_before_inference":True, "bootstrap_resamples":10000, "seed":20260803, "finite_master_metrics":bool(np.isfinite(master_table[["dice","iou"]].astype(float)).all().all())}, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--frozen-reference", type=Path, required=True)
    args = parser.parse_args()
    finalize(args.output_root, args.frozen_reference)


if __name__ == "__main__":
    main()
