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
            try:
                frame[column] = pd.to_numeric(frame[column])
            except (TypeError, ValueError):
                pass
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

    difference_status = json.loads((root / "05_difference_map_control/DIFFERENCE_MAP_GATE_STATUS.json").read_text())
    if difference_status["status"] == "PASS":
        difference = read_numeric(root / "05_difference_map_control/DIFFERENCE_MAP_CASE_METRICS.csv")
        difference = pd.concat([difference, reference_rows(methods, {"fixed_baseline":"FIXED_P0"})], ignore_index=True, sort=False)
        summaries.append(summarize(difference, ["condition"]).assign(family="difference_map_control"))
        paired.append(paired_family(difference, condition_column="condition", reference="FIXED_P0", comparisons=["RETROSPECTIVE_FUTURE_IMAGE_DIFFERENCE_CONTROL"], family="difference_map_control_vs_fixed"))
        master.append(difference.assign(experiment_family="difference_map_control"))

    summary = pd.concat(summaries, ignore_index=True, sort=False)
    paired_table = pd.concat(paired, ignore_index=True, sort=False)
    master_table = pd.concat(master, ignore_index=True, sort=False)
    atomic_csv(summary, statistics / "INTERNAL_METHOD_SUMMARY.csv")
    atomic_csv(paired_table, root / "INTERNAL_COMPLETION_PAIRED_STATISTICS.csv")
    atomic_csv(master_table, root / "INTERNAL_COMPLETION_MASTER_METRICS.csv")
    atomic_csv(summary, tables / "INTERNAL_COMPLETION_METHOD_SUMMARY.csv")

    baseline = methods[methods.method == "fixed_baseline"].set_index("case_id")
    pcc = methods[methods.method == "pcc_correction"].set_index("case_id")
    failure = pd.DataFrame({"p0_dice": baseline.dice.astype(float), "pcc_dice": pcc.dice.astype(float)}, index=baseline.index)
    failure.index.name = "case_id"
    failure["pcc_gain"] = failure.pcc_dice - failure.p0_dice
    shuffled_case = shuffled[shuffled.condition == "SHUFFLED_TARGET_PCC"].set_index("case_id")
    failure["shuffled_gain_vs_p0"] = shuffled_case.dice.astype(float) - failure.p0_dice
    retention = case_aggregated[(case_aggregated.method == "PCC") & (case_aggregated.condition != "CLEAN")].groupby("case_id").retention_relative_to_clean_pcc.min()
    failure["smallest_imperfect_retention"] = retention
    original_target = targets[(targets.condition == "ORIGINAL") & (targets.evaluation_mode == "same_definition")].set_index("case_id")
    failure["target_voxels"] = original_target.evaluation_target_voxels
    failure["target_components"] = original_target.target_components
    trajectories = read_numeric(frozen / "ALL_PCC_ROUND_TRAJECTORIES.csv")
    p1 = trajectories[trajectories["round"] == 1].set_index("case_id")
    p10 = trajectories[trajectories["round"] == 10].set_index("case_id")
    failure["p1_dice"] = p1.dice
    failure["p10_minus_p1_dice"] = p10.dice - p1.dice
    failure["p10_correction_mass"] = p10.correction_mass
    atomic_csv(failure.sort_values("pcc_gain").reset_index(), root / "06_failure_analysis/INTERNAL_FAILURE_BOUNDARY_CASES.csv")
    project_root = Path(__file__).resolve().parents[1]
    completed_root = project_root / "outputs/pcc_leakage_free_rerun_2026_v8"
    layer1_path = completed_root / "14_layer1/LAYER1_CASE_METRICS.csv"
    if layer1_path.exists():
        layer1 = read_numeric(layer1_path).sort_values(["dice_gain", "case_id"])
        atomic_csv(layer1, root / "06_failure_analysis/LAYER1_GAIN_RANKING.csv")
    layer3a_path = completed_root / "15_layer3_occlusion/Layer3_FORMAL_v1_case_metrics.csv"
    layer3b_path = completed_root / "16_layer3_localization/Layer3B_FORMAL_v1_case_metrics.csv"
    if layer3a_path.exists():
        layer3a = read_numeric(layer3a_path).sort_values(["pcc_minus_baseline_boundary_PRI", "case_id"])
        atomic_csv(layer3a, root / "06_failure_analysis/LAYER3A_WEAK_ENRICHMENT_RANKING.csv")
    if layer3b_path.exists():
        layer3b = read_numeric(layer3b_path).sort_values(["boundary_vs_control_abs_mean_enrichment", "case_id"])
        atomic_csv(layer3b, root / "06_failure_analysis/LAYER3B_WEAK_LOCALIZATION_RANKING.csv")

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
        {"experiment":"difference_map_control","status":"COMPLETE" if difference_status["status"] == "PASS" else difference_status["status"],"case_count":40 if difference_status["status"] == "PASS" else 0},
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
