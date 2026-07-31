from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

try:
    import pandas as pd

    from src.artifacts.management import ArtifactDirectories
    from src.pipelines.experiment import (
        CaseFailure,
        ExperimentResult,
    )
    from src.pipelines.formal_layer2r import (
        FormalRunConfig,
        FormalPreflightResult,
        FormalTrainingProvider,
        SavedBaselineMapProvider,
        _selected_case_ids,
        build_baseline_provider,
        load_formal_config,
        preflight_formal_layer2r,
        run_formal_layer2r,
    )

    DEPENDENCIES_AVAILABLE = True
except ModuleNotFoundError:
    DEPENDENCIES_AVAILABLE = False


def empty_experiment(*, failures=()):
    return ExperimentResult(
        case_order=("case_a",),
        cases=(),
        failures=tuple(failures),
        metrics=pd.DataFrame(columns=("case_id", "method")),
        pairwise_comparisons=pd.DataFrame(),
        method_summary=None,
        pairwise_summary=pd.DataFrame(),
    )


@unittest.skipUnless(
    DEPENDENCIES_AVAILABLE,
    "Formal execution dependencies are unavailable",
)
class FormalLayer2RExecutionTests(unittest.TestCase):
    def config(self, root: Path, **changes) -> FormalRunConfig:
        values = {
            "raw_root": root / "raw",
            "case_metrics_csv": root / "cases.csv",
            "output_dir": root / "output",
            "max_new_cases": 1,
        }
        values.update(changes)
        return FormalRunConfig(**values)

    def make_raw_case(self, config: FormalRunConfig, case_id: str) -> None:
        from src.data.dataset_identity import get_raw_paths

        for key, path in get_raw_paths(case_id, config.raw_root).items():
            if key in ("cur_img", "fut_img", "cur_mask", "fut_mask"):
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                Path(path).touch()

    def test_minimal_config_loads_kaggle_paths_and_defaults(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "raw_root": "/kaggle/input/raw",
                        "case_metrics_csv": "/kaggle/input/cases.csv",
                        "output_dir": "/kaggle/working/run",
                    }
                )
            )
            config = load_formal_config(path)
        self.assertEqual(config.raw_root, Path("/kaggle/input/raw"))
        self.assertEqual(config.baseline_source, "training")
        self.assertEqual(config.device, "cuda")
        self.assertEqual(config.max_new_cases, 1)

    def test_provider_factory_requires_source_specific_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertIsInstance(
                build_baseline_provider(self.config(root)),
                FormalTrainingProvider,
            )
            with self.assertRaisesRegex(ValueError, "checkpoint_root"):
                build_baseline_provider(
                    self.config(root, baseline_source="checkpoint")
                )
            with self.assertRaisesRegex(ValueError, "baseline_map_root"):
                build_baseline_provider(
                    self.config(root, baseline_source="saved_map")
                )

    def test_training_provider_adapts_prepared_case_without_reimplementation(self):
        prepared = mock.Mock()
        prepared.current_t1c = mock.sentinel.current_t1c
        prepared.current_mask = mock.sentinel.current_mask
        prepared.future_change_target = mock.sentinel.target
        expected = np.zeros((1, 2, 3), dtype=np.float32)
        training_result = mock.Mock(baseline_probability=expected)
        provider = FormalTrainingProvider("cuda")
        with mock.patch(
            "src.pipelines.formal_layer2r.train_case_baseline",
            return_value=training_result,
        ) as train:
            actual = provider("case_a", prepared)
        train.assert_called_once_with(
            "case_a",
            mock.sentinel.current_t1c,
            mock.sentinel.current_mask,
            mock.sentinel.target,
            "cuda",
        )
        self.assertIs(actual, expected)
        self.assertIs(provider.results["case_a"], training_result)

    def test_saved_map_provider_preserves_contract_and_float32(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case = root / "case_a"
            case.mkdir()
            expected = np.array([[[0.125, 0.75]]], dtype=np.float16)
            np.save(case / "baseline_prob_map_formal_float16.npy", expected)
            provider = SavedBaselineMapProvider(root)
            actual = provider("case_a", mock.sentinel.prepared)
        self.assertEqual(actual.dtype, np.float32)
        np.testing.assert_array_equal(actual, expected.astype(np.float32))

    def test_case_selection_is_locked_order_filtered_and_resume_aware(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self.config(root, max_new_cases=2)
            pd.DataFrame(
                {"case_id": ["case_c", "case_a", "case_b", "case_a"]}
            ).to_csv(config.case_metrics_csv, index=False)
            selected = _selected_case_ids(config, {"case_a"})
        self.assertEqual(selected, ("case_b", "case_c"))

    def test_preflight_selects_exactly_one_locked_case_without_execution(self):
        case_id = "PatientID_001_T1_to_T2_t1c"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self.config(root)
            config.raw_root.mkdir()
            pd.DataFrame({"case_id": [case_id]}).to_csv(
                config.case_metrics_csv,
                index=False,
            )
            self.make_raw_case(config, case_id)
            with mock.patch(
                "src.pipelines.formal_layer2r.importlib.import_module"
            ), mock.patch(
                "src.pipelines.formal_layer2r.torch.cuda.is_available",
                return_value=True,
            ), mock.patch(
                "src.pipelines.formal_layer2r.train_case_baseline"
            ) as train, mock.patch(
                "src.pipelines.formal_layer2r.predict_full_volume"
            ) as predict, mock.patch(
                "src.pipelines.formal_layer2r.run_experiment"
            ) as experiment:
                result = preflight_formal_layer2r(config)

        self.assertIsInstance(result, FormalPreflightResult)
        self.assertTrue(result.ok)
        self.assertEqual(result.selected_case_ids, (case_id,))
        self.assertEqual(result.completed_case_ids, ())
        train.assert_not_called()
        predict.assert_not_called()
        experiment.assert_not_called()

    def test_preflight_rejects_zero_or_multiple_pending_cases(self):
        cases = (
            "PatientID_001_T1_to_T2_t1c",
            "PatientID_002_T1_to_T2_t1c",
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self.config(root, max_new_cases=None)
            config.raw_root.mkdir()
            pd.DataFrame({"case_id": cases}).to_csv(
                config.case_metrics_csv,
                index=False,
            )
            for case_id in cases:
                self.make_raw_case(config, case_id)
            with mock.patch(
                "src.pipelines.formal_layer2r.importlib.import_module"
            ), mock.patch(
                "src.pipelines.formal_layer2r.torch.cuda.is_available",
                return_value=True,
            ):
                multiple = preflight_formal_layer2r(config)
                config.output_dir.mkdir(parents=True)
                formal_results = config.output_dir / "formal_results"
                formal_results.mkdir()
                (formal_results / "completed_cases.txt").write_text(
                    "\n".join(cases) + "\n"
                )
                zero = preflight_formal_layer2r(config)

        self.assertFalse(multiple.ok)
        self.assertIn("selected 2", " ".join(multiple.errors))
        self.assertFalse(zero.ok)
        self.assertIn("selected 0", " ".join(zero.errors))

    def test_preflight_reports_paths_columns_gpu_and_output_failures(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self.config(root, device="cpu")
            pd.DataFrame({"wrong_column": ["case"]}).to_csv(
                config.case_metrics_csv,
                index=False,
            )
            config.output_dir.touch()
            with mock.patch(
                "src.pipelines.formal_layer2r.importlib.import_module"
            ), mock.patch(
                "src.pipelines.formal_layer2r.torch.cuda.is_available",
                return_value=False,
            ):
                result = preflight_formal_layer2r(config)

        errors = " ".join(result.errors)
        self.assertIn("Missing raw dataset root", errors)
        self.assertIn("not a directory", errors)
        self.assertIn("CUDA device request", errors)
        self.assertIn("available CUDA GPU", errors)
        self.assertIn("case_id", errors)

    def test_runner_invokes_stages_in_order_without_scientific_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self.config(root)
            pd.DataFrame({"case_id": ["case_a"]}).to_csv(
                config.case_metrics_csv,
                index=False,
            )
            directories = ArtifactDirectories(
                config.output_dir,
                config.output_dir / "maps",
                config.output_dir / "figures",
                config.output_dir / "tables",
                config.output_dir / "logs",
                config.output_dir / "checkpoints",
                config.output_dir / "case_outputs",
                config.output_dir / "formal_results",
            )
            for path in directories.__dict__.values():
                path.mkdir(parents=True, exist_ok=True)
            calls = []
            provider = mock.Mock(name="provider")
            experiment = empty_experiment()

            with mock.patch(
                "src.pipelines.formal_layer2r.create_artifact_directories",
                side_effect=lambda path: calls.append("directories") or directories,
            ), mock.patch(
                "src.pipelines.formal_layer2r.discover_completed_cases",
                side_effect=lambda path: calls.append("resume") or set(),
            ), mock.patch(
                "src.pipelines.formal_layer2r.seed_formal_run",
                side_effect=lambda: calls.append("seed"),
            ), mock.patch(
                "src.pipelines.formal_layer2r.run_experiment",
                side_effect=lambda *args, **kwargs: calls.append("experiment")
                or experiment,
            ), mock.patch(
                "src.pipelines.formal_layer2r.persist_experiment_result",
                side_effect=lambda *args: calls.append("artifacts") or directories,
            ), mock.patch(
                "src.pipelines.formal_layer2r._refresh_cumulative_tables",
                side_effect=lambda *args: calls.append("summaries"),
            ):
                result = run_formal_layer2r(
                    config,
                    baseline_provider=provider,
                )

        self.assertIs(result.experiment, experiment)
        self.assertEqual(
            calls,
            [
                "directories",
                "resume",
                "seed",
                "experiment",
                "artifacts",
                "summaries",
            ],
        )

    def test_runner_returns_order_11_failures_to_entry_layer(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self.config(root)
            pd.DataFrame({"case_id": ["case_a"]}).to_csv(
                config.case_metrics_csv,
                index=False,
            )
            failure = CaseFailure("case_a", RuntimeError("provider failed"))
            experiment = empty_experiment(failures=(failure,))
            with mock.patch(
                "src.pipelines.formal_layer2r.run_experiment",
                return_value=experiment,
            ), mock.patch(
                "src.pipelines.formal_layer2r.seed_formal_run"
            ), mock.patch(
                "src.pipelines.formal_layer2r.persist_experiment_result",
                side_effect=lambda result, output: ArtifactDirectories(
                    Path(output),
                    *(Path(output) / name for name in (
                        "maps",
                        "figures",
                        "tables",
                        "logs",
                        "checkpoints",
                        "case_outputs",
                        "formal_results",
                    )),
                ),
            ), mock.patch(
                "src.pipelines.formal_layer2r._refresh_cumulative_tables"
            ):
                result = run_formal_layer2r(
                    config,
                    baseline_provider=mock.Mock(),
                )
        self.assertEqual(result.experiment.failures, (failure,))
        self.assertIsNone(result.publication)


if __name__ == "__main__":
    unittest.main()
