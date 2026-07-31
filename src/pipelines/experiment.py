"""Order 11 orchestration for the formal Layer 2R experiment.

Purpose
-------
Compose the already migrated Orders 1--10 without implementing any of their
scientific operations.  Baseline prediction is supplied by an injected
provider; this module never constructs, trains, checkpoints, or
persists a model.

Inputs and outputs
------------------
``run_experiment`` accepts case records and returns all maps, per-case metric
records, descriptive summaries, and failures in memory.  The default case
preparer follows Orders 1--3 from raw NIfTI paths.  Tests and callers with
prepared arrays may inject a preparer.  Visualization is an optional callback
and artifact persistence is intentionally absent.

Scientific assumptions
----------------------
Case identifiers are deduplicated and lexicographically sorted.  Successful
cases use the formal seven-method order from notebook cells 109--110.  An
empty future-change target fails the case before baseline prediction.

Known limitations
-----------------
The baseline provider may train Order 4R, load an Order 4R checkpoint, or load
an existing probability map.  Locked-cohort numerical regression remains
required and belongs outside this CPU-only orchestration smoke path.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np
import pandas as pd

from src.data.dataset_identity import require_raw_paths
from src.data.dataset_loader import load_nii_zhw, validate_shape_compatibility
from src.evaluation.metrics import eval_prob_map
from src.models.eia import EIAResult, apply_eia
from src.models.naive_self_tightening import naive_self_tighten
from src.models.pcc import PCCResult, apply_pcc
from src.preprocessing.preprocessing import (
    PreprocessedLongitudinalCase,
    preprocess_longitudinal_arrays,
)
from src.statistics.statistics import (
    METHOD_ORDER,
    PAIRWISE_COLUMNS,
    PAIRWISE_SUMMARY_COLUMNS,
    build_pairwise_comparisons,
    summarize_methods,
    summarize_pairwise,
)


@dataclass(frozen=True)
class CaseRecord:
    """Identity and Order 1 raw paths for one longitudinal case."""

    case_id: str
    raw_paths: Mapping[str, Any]


class BaselineProvider(Protocol):
    """Injected probability-map provider independent of baseline origin."""

    def __call__(
        self,
        case_id: str,
        prepared: PreprocessedLongitudinalCase,
    ) -> np.ndarray: ...


CasePreparer = Callable[[CaseRecord], PreprocessedLongitudinalCase]


@dataclass(frozen=True)
class CaseResult:
    """All in-memory scientific outputs for one successful case."""

    case_id: str
    prepared: PreprocessedLongitudinalCase
    method_maps: Mapping[str, np.ndarray]
    pcc_result: PCCResult
    eia_result: EIAResult
    metrics: pd.DataFrame


FigureCallback = Callable[[CaseResult], None]
ProgressCallback = Callable[[str, str], None]


@dataclass(frozen=True)
class CaseFailure:
    """One notebook-style case failure without persistence details."""

    case_id: str
    error: Exception


@dataclass(frozen=True)
class ExperimentResult:
    """Complete in-memory outcome of one deterministic cohort run."""

    case_order: tuple[str, ...]
    cases: tuple[CaseResult, ...]
    failures: tuple[CaseFailure, ...]
    metrics: pd.DataFrame
    pairwise_comparisons: pd.DataFrame
    method_summary: pd.DataFrame | None
    pairwise_summary: pd.DataFrame


def prepare_case_from_raw(record: CaseRecord) -> PreprocessedLongitudinalCase:
    """Run the migrated Orders 1--3 raw-data preparation sequence."""
    require_raw_paths(record.raw_paths)
    current_t1c, _, _, _ = load_nii_zhw(Path(record.raw_paths["cur_img"]))
    future_t1c, _, _, _ = load_nii_zhw(Path(record.raw_paths["fut_img"]))
    current_mask, _, _, _ = load_nii_zhw(Path(record.raw_paths["cur_mask"]))
    future_mask, _, _, _ = load_nii_zhw(Path(record.raw_paths["fut_mask"]))
    validate_shape_compatibility(
        current_t1c,
        future_t1c,
        current_mask,
        future_mask,
    )
    return preprocess_longitudinal_arrays(
        current_t1c,
        future_t1c,
        current_mask,
        future_mask,
    )


def _ordered_records(records: Iterable[CaseRecord]) -> list[CaseRecord]:
    """Apply the formal sorted-unique case iteration rule."""
    by_id: dict[str, CaseRecord] = {}
    for record in records:
        by_id.setdefault(record.case_id, record)
    return [by_id[case_id] for case_id in sorted(by_id)]


def run_case(
    record: CaseRecord,
    baseline_provider: BaselineProvider,
    *,
    case_preparer: CasePreparer = prepare_case_from_raw,
    figure_callback: FigureCallback | None = None,
) -> CaseResult:
    """Run one case through Orders 1--9, returning all outputs in memory."""
    prepared = case_preparer(record)
    target = prepared.future_change_target
    if int(target.sum()) <= 0:
        raise ValueError("Future-change target is empty.")

    baseline = np.asarray(baseline_provider(record.case_id, prepared))
    if baseline.shape != target.shape:
        raise ValueError(
            "Baseline and target shapes differ: "
            f"{baseline.shape} != {target.shape}"
        )

    naive = naive_self_tighten(baseline)
    pcc_result = apply_pcc(baseline, target)
    eia_result = apply_eia(baseline, target)

    method_maps = {
        "fixed_baseline": baseline,
        "naive_self_tightening": naive,
        "eia_linear": eia_result.linear,
        "eia_blend090": eia_result.blend090,
        "eia_blend075": eia_result.blend075,
        "eia_morph": eia_result.morph,
        "pcc_correction": pcc_result.corrected_probability,
    }
    rows = []
    for method in METHOD_ORDER:
        rows.append(
            {
                "case_id": record.case_id,
                "method": method,
                **eval_prob_map(method_maps[method], target),
            }
        )

    result = CaseResult(
        case_id=record.case_id,
        prepared=prepared,
        method_maps=method_maps,
        pcc_result=pcc_result,
        eia_result=eia_result,
        metrics=pd.DataFrame(rows),
    )
    if figure_callback is not None:
        figure_callback(result)
    return result


def run_experiment(
    records: Iterable[CaseRecord],
    baseline_provider: BaselineProvider,
    *,
    case_preparer: CasePreparer = prepare_case_from_raw,
    figure_callback: FigureCallback | None = None,
    progress_callback: ProgressCallback | None = None,
) -> ExperimentResult:
    """Run the deterministic cohort loop and Order 10 summaries."""
    ordered = _ordered_records(records)
    cases: list[CaseResult] = []
    failures: list[CaseFailure] = []

    for record in ordered:
        if progress_callback is not None:
            progress_callback("started", record.case_id)
        try:
            case = run_case(
                record,
                baseline_provider,
                case_preparer=case_preparer,
                figure_callback=figure_callback,
            )
        except Exception as error:
            failures.append(CaseFailure(record.case_id, error))
            if progress_callback is not None:
                progress_callback("failed", record.case_id)
            continue
        cases.append(case)
        if progress_callback is not None:
            progress_callback("completed", record.case_id)

    metrics = pd.concat(
        [case.metrics for case in cases],
        ignore_index=True,
    ) if cases else pd.DataFrame(columns=("case_id", "method"))

    if metrics.empty:
        comparisons = pd.DataFrame(columns=PAIRWISE_COLUMNS)
        method_summary = None
        pairwise_summary = pd.DataFrame(columns=PAIRWISE_SUMMARY_COLUMNS)
    else:
        comparisons = build_pairwise_comparisons(metrics)
        method_summary = summarize_methods(metrics)
        pairwise_summary = summarize_pairwise(comparisons)

    return ExperimentResult(
        case_order=tuple(record.case_id for record in ordered),
        cases=tuple(cases),
        failures=tuple(failures),
        metrics=metrics,
        pairwise_comparisons=comparisons,
        method_summary=method_summary,
        pairwise_summary=pairwise_summary,
    )
