"""Artifact persistence for migrated Layer 2R experiment results.

Purpose
-------
Persist the subset of final formal Layer 2R artifacts from authoritative
notebook cell 110 that is actually returned by the migrated Order 11
pipeline.  This module performs no scientific calculation.

Inputs and outputs
------------------
The public entry point :func:`persist_experiment_result` accepts an Order 11
``ExperimentResult`` and an explicit output root.  Per-case arrays and tables,
cohort tables, completion records, and failure records are written beneath the
notebook's directory layout.  The returned ``ArtifactDirectories`` identifies
that layout.

Dependencies
------------
NumPy and pandas, plus the in-memory result interfaces from Order 11.

Scientific assumptions
----------------------
Array names, casts, method order, direct-write behavior, append behavior, and
resume discovery follow notebook cell 110.  Probability maps are persisted as
float16 because cell 110 explicitly makes that storage conversion; scientific
calculations remain upstream and in memory.

Expected behaviour
------------------
Existing per-case files and cohort summaries are overwritten directly.
Long-form cohort tables, completion lines, and failures are appended directly.
A case is skipped when named in ``completed_cases.txt`` or when its existing
cohort metric rows contain at least seven unique methods.  No writes are
atomic and partial artifacts are deliberately not rolled back.

Known limitations
-----------------
Order 11 does not return training history, model state, checkpoints, raw input
shapes, run protocol, timestamps, elapsed times, figures, or PCC round
history.  This module neither reconstructs nor invents those artifacts.  Its
``case_meta.json`` consequently contains only the cell-110 metadata fields
derivable from ``CaseResult``.  Append retries can duplicate rows exactly as
in the notebook, and a metrics table with seven methods can mark a case
complete even when later artifacts are absent.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.models.pcc import safe_clip_prob
from src.pipelines.experiment import CaseFailure, CaseResult, ExperimentResult


FORMAL_METHOD_ORDER = (
    "fixed_baseline",
    "naive_self_tightening",
    "eia_linear",
    "eia_blend090",
    "eia_blend075",
    "eia_morph",
    "pcc_correction",
)


@dataclass(frozen=True)
class ArtifactDirectories:
    """The exact output subdirectories created by formal notebook cell 110."""

    output: Path
    maps: Path
    figures: Path
    tables: Path
    logs: Path
    checkpoints: Path
    case_outputs: Path
    formal_results: Path


def create_artifact_directories(output_dir: str | Path) -> ArtifactDirectories:
    """Create and return the formal Layer 2R directory layout."""
    output = Path(output_dir)
    directories = ArtifactDirectories(
        output=output,
        maps=output / "maps",
        figures=output / "figures",
        tables=output / "tables",
        logs=output / "logs",
        checkpoints=output / "checkpoints",
        case_outputs=output / "case_outputs",
        formal_results=output / "formal_results",
    )
    for directory in (
        directories.maps,
        directories.figures,
        directories.tables,
        directories.logs,
        directories.checkpoints,
        directories.case_outputs,
        directories.formal_results,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    return directories


def append_dataframe(frame: pd.DataFrame, path: str | Path) -> None:
    """Append a CSV using the notebook's header-if-new-file rule."""
    target = Path(path)
    frame.to_csv(
        target,
        mode="a",
        header=not target.exists(),
        index=False,
    )


def discover_completed_cases(formal_results_dir: str | Path) -> set[str]:
    """Recover completed cases using cell 110's text-and-metrics union."""
    formal_results = Path(formal_results_dir)
    completed_txt = formal_results / "completed_cases.txt"
    metrics_csv = (
        formal_results / "Layer2R_formal_case_method_metrics.csv"
    )
    completed: set[str] = set()

    if completed_txt.exists():
        completed.update(
            line.strip()
            for line in completed_txt.read_text().splitlines()
            if line.strip()
        )

    if metrics_csv.exists():
        try:
            metrics = pd.read_csv(metrics_csv)
            methods_per_case = metrics.groupby("case_id")["method"].nunique()
            completed.update(
                methods_per_case[methods_per_case >= 7].index.tolist()
            )
        except Exception:
            # Cell 110 deliberately ignores an unreadable metrics table.
            pass

    return completed


def _case_metadata(case: CaseResult) -> dict[str, object]:
    prepared = case.prepared
    return {
        "case_id": case.case_id,
        "zhw_shape": list(prepared.current_t1c.shape),
        "cur_mask_voxels": int(prepared.current_mask.sum()),
        "fut_mask_voxels": int(prepared.future_mask.sum()),
        "target_voxels": int(prepared.future_change_target.sum()),
        "brain_voxels": int(prepared.brain_mask.sum()),
    }


def persist_case_result(
    case: CaseResult,
    comparisons: pd.DataFrame,
    directories: ArtifactDirectories,
) -> None:
    """Persist one successful case in cell 110's available write order."""
    case_output = directories.case_outputs / case.case_id
    case_output.mkdir(parents=True, exist_ok=True)
    prepared = case.prepared

    np.save(
        case_output / "current_t1c_norm_zhw.npy",
        prepared.current_t1c.astype(np.float32),
    )
    np.save(
        case_output / "current_mask_zhw.npy",
        prepared.current_mask.astype(np.uint8),
    )
    np.save(
        case_output / "future_mask_zhw.npy",
        prepared.future_mask.astype(np.uint8),
    )
    np.save(
        case_output / "future_change_target_zhw.npy",
        prepared.future_change_target.astype(np.uint8),
    )
    with (case_output / "case_meta.json").open("w") as stream:
        json.dump(_case_metadata(case), stream, indent=2)

    baseline = case.method_maps["fixed_baseline"]
    np.save(
        case_output / "baseline_prob_map_formal_float16.npy",
        np.asarray(baseline).astype(np.float16),
    )
    np.save(
        case_output / "target_support_R_formal.npy",
        case.pcc_result.correction_region.astype(np.uint8),
    )
    np.save(
        case_output / "target_signal_S_formal_float16.npy",
        case.pcc_result.target_signal.astype(np.float16),
    )

    for method in FORMAL_METHOD_ORDER:
        probability = case.method_maps[method]
        if method == "eia_morph":
            persisted = (probability > 0.5).astype(np.uint8)
            filename = f"{method}_formal_uint8.npy"
        else:
            persisted = safe_clip_prob(probability).astype(np.float16)
            filename = f"{method}_formal_float16.npy"
        np.save(case_output / filename, persisted)

    metrics_csv = (
        directories.formal_results
        / "Layer2R_formal_case_method_metrics.csv"
    )
    append_dataframe(case.metrics, metrics_csv)
    case.metrics.to_csv(
        case_output / "case_method_metrics_formal.csv",
        index=False,
    )

    comparisons_csv = (
        directories.formal_results
        / "Layer2R_formal_pairwise_comparisons.csv"
    )
    append_dataframe(comparisons, comparisons_csv)
    comparisons.to_csv(
        case_output / "case_pairwise_comparisons_formal.csv",
        index=False,
    )

    with (
        directories.formal_results / "completed_cases.txt"
    ).open("a") as stream:
        stream.write(case.case_id + "\n")


def persist_case_failure(
    failure: CaseFailure,
    formal_results_dir: str | Path,
) -> None:
    """Append the Order 11 fields available for one failed case."""
    row = pd.DataFrame(
        [{"case_id": failure.case_id, "error": repr(failure.error)}]
    )
    append_dataframe(row, Path(formal_results_dir) / "failed_cases.csv")


def _persist_cohort_tables(
    result: ExperimentResult,
    directories: ArtifactDirectories,
) -> None:
    pd.DataFrame({"case_id": result.case_order}).to_csv(
        directories.tables / "locked_40_cases.csv",
        index=False,
    )
    if result.method_summary is not None:
        result.method_summary.to_csv(
            directories.formal_results
            / "Layer2R_formal_summary_by_method.csv",
            index=False,
        )
    result.pairwise_summary.to_csv(
        directories.formal_results / "Layer2R_formal_pairwise_summary.csv",
        index=False,
    )


def persist_experiment_result(
    result: ExperimentResult,
    output_dir: str | Path,
) -> ArtifactDirectories:
    """Persist all not-yet-completed artifacts returned by Order 11."""
    directories = create_artifact_directories(output_dir)
    completed = discover_completed_cases(directories.formal_results)

    for case in result.cases:
        if case.case_id in completed:
            continue
        comparisons = result.pairwise_comparisons[
            result.pairwise_comparisons["case_id"] == case.case_id
        ]
        persist_case_result(case, comparisons, directories)
        completed.add(case.case_id)

    for failure in result.failures:
        persist_case_failure(failure, directories.formal_results)

    _persist_cohort_tables(result, directories)
    return directories
