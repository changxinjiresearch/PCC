"""Thin execution boundary for the final formal Layer 2R workflow.

This module connects the migrated scientific orders without reimplementing
their algorithms. It owns configuration, baseline-provider selection, ordered
case construction, figure callbacks, persistence, and resume-aware selection.

The scientific authority remains cells 109--110 of
``archive/pcc-experiments-original.ipynb``. Real-case regression is required
before scientific equivalence can be claimed.
"""

from __future__ import annotations

import importlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping

import numpy as np
import pandas as pd
import torch

from src.artifacts.management import (
    ArtifactDirectories,
    create_artifact_directories,
    discover_completed_cases,
    persist_experiment_result,
)
from src.data.dataset_identity import get_raw_paths, load_locked_case_ids
from src.models.eia import (
    EIA_ALPHA,
    EIA_BETA,
    EIA_BLEND_LAMBDA_075,
    EIA_BLEND_LAMBDA_090,
)
from src.models.formal_layer2r_baseline import (
    BASE_CHANNELS,
    BASELINE_MAP_FILENAME,
    BATCH_SIZE,
    CHECKPOINT_NAME_TEMPLATE,
    FORMAL_EPOCHS,
    LEARNING_RATE,
    FormalBaselineTrainingResult,
    MiniUNet,
    predict_full_volume,
    save_baseline_probability,
    save_formal_checkpoint,
    seed_formal_run,
    train_case_baseline,
)
from src.models.naive_self_tightening import NAIVE_GAMMA
from src.models.pcc import DILATION_RADIUS, PCC_ETA, PCC_ROUNDS, SIGMA
from src.pipelines.experiment import (
    BaselineProvider,
    CaseRecord,
    ExperimentResult,
    run_experiment,
)
from src.preprocessing.preprocessing import PreprocessedLongitudinalCase
from src.publication.pipeline import PublicationOutputs, collect_publication_outputs
from src.statistics.statistics import summarize_methods, summarize_pairwise
from src.visualization.figures import save_layer2r_formal_figure


BaselineSource = Literal["training", "checkpoint", "saved_map"]


@dataclass(frozen=True)
class FormalRunConfig:
    """Minimal path and execution configuration for a formal Kaggle run."""

    raw_root: Path
    case_metrics_csv: Path
    output_dir: Path
    baseline_source: BaselineSource = "training"
    device: str = "cuda"
    max_new_cases: int | None = 1
    case_ids: tuple[str, ...] = ()
    checkpoint_root: Path | None = None
    baseline_map_root: Path | None = None


@dataclass(frozen=True)
class FormalRunResult:
    """Outputs from one formal orchestration call in notebook stage order."""

    experiment: ExperimentResult
    artifacts: ArtifactDirectories
    publication: PublicationOutputs | None


@dataclass(frozen=True)
class FormalPreflightResult:
    """Non-executing validation result for one formal Kaggle case."""

    selected_case_ids: tuple[str, ...]
    completed_case_ids: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def load_formal_config(path: str | Path) -> FormalRunConfig:
    """Load the intentionally small JSON configuration used by Kaggle."""
    with Path(path).open() as stream:
        values = json.load(stream)
    return FormalRunConfig(
        raw_root=Path(values["raw_root"]),
        case_metrics_csv=Path(values["case_metrics_csv"]),
        output_dir=Path(values["output_dir"]),
        baseline_source=values.get("baseline_source", "training"),
        device=values.get("device", "cuda"),
        max_new_cases=values.get("max_new_cases", 1),
        case_ids=tuple(values.get("case_ids", ())),
        checkpoint_root=(
            Path(values["checkpoint_root"])
            if values.get("checkpoint_root")
            else None
        ),
        baseline_map_root=(
            Path(values["baseline_map_root"])
            if values.get("baseline_map_root")
            else None
        ),
    )


class FormalTrainingProvider:
    """Adapt Order 4R training to the Order 11 provider contract."""

    def __init__(self, device: str) -> None:
        self.device = device
        self.results: dict[str, FormalBaselineTrainingResult] = {}

    def __call__(
        self,
        case_id: str,
        prepared: PreprocessedLongitudinalCase,
    ) -> np.ndarray:
        result = train_case_baseline(
            case_id,
            prepared.current_t1c,
            prepared.current_mask,
            prepared.future_change_target,
            self.device,
        )
        self.results[case_id] = result
        return result.baseline_probability


class FormalCheckpointProvider:
    """Load Order 4R checkpoints and provide float32 baseline maps."""

    def __init__(self, checkpoint_root: str | Path, device: str) -> None:
        self.checkpoint_root = Path(checkpoint_root)
        self.device = device

    def __call__(
        self,
        case_id: str,
        prepared: PreprocessedLongitudinalCase,
    ) -> np.ndarray:
        path = self.checkpoint_root / CHECKPOINT_NAME_TEMPLATE.format(
            case_id=case_id
        )
        checkpoint = torch.load(path, map_location=self.device)
        model = MiniUNet().to(self.device)
        model.load_state_dict(checkpoint["model_state_dict"])
        return predict_full_volume(
            model,
            prepared.current_t1c,
            prepared.current_mask,
            self.device,
        )


class SavedBaselineMapProvider:
    """Load an existing per-case formal baseline for downstream replay."""

    def __init__(self, baseline_map_root: str | Path) -> None:
        self.baseline_map_root = Path(baseline_map_root)

    def __call__(
        self,
        case_id: str,
        prepared: PreprocessedLongitudinalCase,
    ) -> np.ndarray:
        del prepared
        return np.load(
            self.baseline_map_root / case_id / BASELINE_MAP_FILENAME
        ).astype(np.float32)


def build_baseline_provider(config: FormalRunConfig) -> BaselineProvider:
    """Construct the configured provider without changing downstream code."""
    if config.baseline_source == "training":
        return FormalTrainingProvider(config.device)
    if config.baseline_source == "checkpoint":
        if config.checkpoint_root is None:
            raise ValueError("checkpoint_root is required for checkpoint mode")
        return FormalCheckpointProvider(config.checkpoint_root, config.device)
    if config.baseline_source == "saved_map":
        if config.baseline_map_root is None:
            raise ValueError("baseline_map_root is required for saved_map mode")
        return SavedBaselineMapProvider(config.baseline_map_root)
    raise ValueError(f"Unknown baseline_source: {config.baseline_source}")


def _selected_case_ids(
    config: FormalRunConfig,
    completed: set[str],
) -> tuple[str, ...]:
    locked = load_locked_case_ids(config.case_metrics_csv)
    if config.case_ids:
        requested = set(config.case_ids)
        missing = requested.difference(locked)
        if missing:
            raise ValueError(f"Requested cases are not locked: {sorted(missing)}")
        locked = [case_id for case_id in locked if case_id in requested]
    pending = [case_id for case_id in locked if case_id not in completed]
    if config.max_new_cases is not None:
        pending = pending[: config.max_new_cases]
    return tuple(pending)


def _writable_output_error(output_dir: Path) -> str | None:
    if output_dir.exists():
        if not output_dir.is_dir():
            return f"Output path is not a directory: {output_dir}"
        if not os.access(output_dir, os.W_OK):
            return f"Output directory is not writable: {output_dir}"
        return None

    ancestor = output_dir.parent
    while not ancestor.exists() and ancestor != ancestor.parent:
        ancestor = ancestor.parent
    if not ancestor.is_dir() or not os.access(ancestor, os.W_OK):
        return f"Output directory cannot be created under: {ancestor}"
    return None


def preflight_formal_layer2r(config: FormalRunConfig) -> FormalPreflightResult:
    """Validate one-case Kaggle readiness without training or inference."""
    errors: list[str] = []
    required_dependencies = (
        "numpy",
        "pandas",
        "scipy",
        "nibabel",
        "matplotlib",
        "torch",
    )
    for dependency in required_dependencies:
        try:
            importlib.import_module(dependency)
        except Exception as error:
            errors.append(
                f"Cannot import required dependency {dependency}: {error!r}"
            )

    if not config.raw_root.is_dir():
        errors.append(f"Missing raw dataset root: {config.raw_root}")
    if not config.case_metrics_csv.is_file():
        errors.append(f"Missing case metrics CSV: {config.case_metrics_csv}")

    output_error = _writable_output_error(config.output_dir)
    if output_error is not None:
        errors.append(output_error)

    if config.baseline_source == "training":
        if not config.device.startswith("cuda"):
            errors.append("Training mode requires a CUDA device request")
        if not torch.cuda.is_available():
            errors.append("Training mode requires an available CUDA GPU")
    elif config.baseline_source == "checkpoint":
        if config.checkpoint_root is None or not config.checkpoint_root.is_dir():
            errors.append("Checkpoint mode requires an existing checkpoint_root")
    elif config.baseline_source == "saved_map":
        if config.baseline_map_root is None or not config.baseline_map_root.is_dir():
            errors.append("Saved-map mode requires an existing baseline_map_root")
    else:
        errors.append(f"Unknown baseline_source: {config.baseline_source}")

    completed: set[str] = set()
    selected: tuple[str, ...] = ()
    if config.case_metrics_csv.is_file():
        try:
            locked = load_locked_case_ids(config.case_metrics_csv)
            if not locked:
                errors.append("Case metrics CSV contains no locked cases")
            completed = discover_completed_cases(
                config.output_dir / "formal_results"
            )
            selected = _selected_case_ids(config, completed)
            if len(selected) != 1:
                errors.append(
                    "One-case preflight must select exactly one pending locked "
                    f"case; selected {len(selected)}"
                )
        except (KeyError, OSError, ValueError) as error:
            errors.append(f"Invalid case metrics CSV or case selection: {error}")

    if len(selected) == 1 and config.raw_root.is_dir():
        try:
            paths = get_raw_paths(selected[0], config.raw_root)
            for key in ("cur_img", "fut_img", "cur_mask", "fut_mask"):
                if not Path(paths[key]).is_file():
                    errors.append(
                        f"Missing selected-case input {key}: {paths[key]}"
                    )
        except ValueError as error:
            errors.append(f"Invalid selected case identifier: {error}")

    return FormalPreflightResult(
        selected_case_ids=selected,
        completed_case_ids=tuple(sorted(completed)),
        errors=tuple(errors),
    )


def _protocol(config: FormalRunConfig, locked_case_count: int) -> dict[str, object]:
    """Build run metadata; constants remain owned by scientific modules."""
    return {
        "run_name": config.output_dir.name,
        "formal_epochs": FORMAL_EPOCHS,
        "batch_size": BATCH_SIZE,
        "lr": LEARNING_RATE,
        "base_channels": BASE_CHANNELS,
        "device": config.device,
        "max_new_cases_per_batch": config.max_new_cases,
        "locked_cases_n": locked_case_count,
        "target_definition": "future tumour mask AND NOT current tumour mask",
        "main_metric_mode": "topk",
        "threshold": 0.5,
        "baseline_source": config.baseline_source,
        "methods": [
            "fixed_baseline",
            "naive_self_tightening",
            "eia_linear",
            "eia_blend090",
            "eia_blend075",
            "eia_morph",
            "pcc_correction",
        ],
        "pcc_params": {
            "rounds": PCC_ROUNDS,
            "eta": PCC_ETA,
            "dilation_radius": DILATION_RADIUS,
            "sigma": SIGMA,
        },
        "eia_params": {
            "alpha": EIA_ALPHA,
            "beta": EIA_BETA,
            "blend_lambda_090": EIA_BLEND_LAMBDA_090,
            "blend_lambda_075": EIA_BLEND_LAMBDA_075,
        },
        "naive_gamma": NAIVE_GAMMA,
    }


def _figure_callback(directories: ArtifactDirectories):
    def save(case) -> None:
        maps = case.method_maps
        save_layer2r_formal_figure(
            directories.figures / f"Layer2R_formal_{case.case_id}.png",
            case.prepared.current_t1c,
            case.prepared.future_change_target,
            maps["fixed_baseline"],
            maps["eia_linear"],
            maps["eia_blend090"],
            maps["eia_blend075"],
            maps["eia_morph"],
            maps["pcc_correction"],
        )

    return save


def _persist_training_results(
    provider: BaselineProvider,
    directories: ArtifactDirectories,
    protocol: Mapping[str, object],
) -> None:
    if not isinstance(provider, FormalTrainingProvider):
        return
    cohort_history = (
        directories.formal_results / "Layer2R_formal_training_history.csv"
    )
    for case_id, result in provider.results.items():
        case_output = directories.case_outputs / case_id
        case_output.mkdir(parents=True, exist_ok=True)
        history = result.history.copy()
        history["formal_epochs"] = FORMAL_EPOCHS
        history["training_elapsed_sec_total"] = result.elapsed_seconds
        history.to_csv(
            case_output / "baseline_training_history_formal.csv",
            index=False,
        )
        history.to_csv(
            cohort_history,
            mode="a",
            header=not cohort_history.exists(),
            index=False,
        )
        save_formal_checkpoint(
            directories.checkpoints,
            case_id,
            result,
            protocol,
        )
        save_baseline_probability(case_output, result.baseline_probability)


def _attach_training_metadata(
    experiment: ExperimentResult,
    provider: BaselineProvider,
) -> None:
    """Add notebook training fields only when Order 4R trained the baseline."""
    if not isinstance(provider, FormalTrainingProvider):
        return
    for case in experiment.cases:
        training = provider.results.get(case.case_id)
        if training is None:
            continue
        values = {
            "formal_epochs": FORMAL_EPOCHS,
            "baseline_best_dice_topk": training.best_dice_topk,
            "baseline_training_elapsed_sec": training.elapsed_seconds,
        }
        for name, value in values.items():
            case.metrics[name] = value
            experiment.metrics.loc[
                experiment.metrics["case_id"] == case.case_id,
                name,
            ] = value


def _refresh_cumulative_tables(
    directories: ArtifactDirectories,
    locked_case_ids: tuple[str, ...],
) -> None:
    """Refresh notebook cohort tables from the append-only persisted rows."""
    pd.DataFrame({"case_id": locked_case_ids}).to_csv(
        directories.tables / "locked_40_cases.csv",
        index=False,
    )
    metrics_path = (
        directories.formal_results
        / "Layer2R_formal_case_method_metrics.csv"
    )
    if metrics_path.exists():
        summary = summarize_methods(pd.read_csv(metrics_path))
        if summary is not None:
            summary.to_csv(
                directories.formal_results
                / "Layer2R_formal_summary_by_method.csv",
                index=False,
            )
    comparisons_path = (
        directories.formal_results
        / "Layer2R_formal_pairwise_comparisons.csv"
    )
    if comparisons_path.exists():
        summarize_pairwise(pd.read_csv(comparisons_path)).to_csv(
            directories.formal_results
            / "Layer2R_formal_pairwise_summary.csv",
            index=False,
        )


def run_formal_layer2r(
    config: FormalRunConfig,
    *,
    baseline_provider: BaselineProvider | None = None,
) -> FormalRunResult:
    """Execute configured cases through the migrated formal workflow."""
    directories = create_artifact_directories(config.output_dir)
    completed = discover_completed_cases(directories.formal_results)
    locked_case_ids = tuple(load_locked_case_ids(config.case_metrics_csv))
    case_ids = _selected_case_ids(config, completed)
    records = tuple(
        CaseRecord(case_id, get_raw_paths(case_id, config.raw_root))
        for case_id in case_ids
    )
    provider = (
        baseline_provider
        if baseline_provider is not None
        else build_baseline_provider(config)
    )
    locked_count = len(locked_case_ids)
    protocol = _protocol(config, locked_count)
    with (directories.output / "protocol.json").open("w") as stream:
        json.dump(protocol, stream, indent=2)

    seed_formal_run()
    experiment = run_experiment(
        records,
        provider,
        figure_callback=_figure_callback(directories),
    )
    _attach_training_metadata(experiment, provider)
    _persist_training_results(provider, directories, protocol)
    artifacts = persist_experiment_result(experiment, config.output_dir)
    _refresh_cumulative_tables(artifacts, locked_case_ids)

    publication = None
    if not experiment.failures and len(completed | set(case_ids)) == 40:
        publication = collect_publication_outputs(config.output_dir)
    return FormalRunResult(experiment, artifacts, publication)
