import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

from src.artifacts.management import (
    FORMAL_METHOD_ORDER,
    create_artifact_directories,
    discover_completed_cases,
    persist_experiment_result,
)
from src.pipelines.experiment import CaseRecord, run_experiment
from src.preprocessing.preprocessing import PreprocessedLongitudinalCase


def prepared_case() -> PreprocessedLongitudinalCase:
    shape = (3, 5, 7)
    current = np.linspace(0, 1, np.prod(shape), dtype=np.float32).reshape(shape)
    current_mask = np.zeros(shape, dtype=np.float32)
    future_mask = np.zeros(shape, dtype=np.uint8)
    target = np.zeros(shape, dtype=np.uint8)
    target[1, 1:4, 2:5] = 1
    future_mask[target.astype(bool)] = 1
    return PreprocessedLongitudinalCase(
        current,
        current_mask,
        future_mask,
        target,
        np.ones(shape, dtype=bool),
    )


def synthetic_preparer(record):
    del record
    return prepared_case()


def synthetic_baseline(case_id, prepared):
    del case_id
    return (0.1 + 0.8 * prepared.current_t1c).astype(np.float32)


def successful_result():
    return run_experiment(
        [CaseRecord("case_a", {})],
        synthetic_baseline,
        case_preparer=synthetic_preparer,
    )


class ArtifactManagementTests(unittest.TestCase):
    def test_persists_available_cell_110_artifacts_and_dtypes(self):
        result = successful_result()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "Layer2R_publication_rebuild_EIA_v1"
            directories = persist_experiment_result(result, root)

            for name in (
                "maps",
                "figures",
                "tables",
                "logs",
                "checkpoints",
                "case_outputs",
                "formal_results",
            ):
                self.assertTrue((root / name).is_dir())

            case_dir = directories.case_outputs / "case_a"
            expected_dtypes = {
                "current_t1c_norm_zhw.npy": np.float32,
                "current_mask_zhw.npy": np.uint8,
                "future_mask_zhw.npy": np.uint8,
                "future_change_target_zhw.npy": np.uint8,
                "baseline_prob_map_formal_float16.npy": np.float16,
                "target_support_R_formal.npy": np.uint8,
                "target_signal_S_formal_float16.npy": np.float16,
                "fixed_baseline_formal_float16.npy": np.float16,
                "naive_self_tightening_formal_float16.npy": np.float16,
                "eia_linear_formal_float16.npy": np.float16,
                "eia_blend090_formal_float16.npy": np.float16,
                "eia_blend075_formal_float16.npy": np.float16,
                "eia_morph_formal_uint8.npy": np.uint8,
                "pcc_correction_formal_float16.npy": np.float16,
            }
            for filename, dtype in expected_dtypes.items():
                self.assertEqual(np.load(case_dir / filename).dtype, dtype)

            with (case_dir / "case_meta.json").open() as stream:
                metadata = json.load(stream)
            self.assertEqual(
                list(metadata),
                [
                    "case_id",
                    "zhw_shape",
                    "cur_mask_voxels",
                    "fut_mask_voxels",
                    "target_voxels",
                    "brain_voxels",
                ],
            )
            self.assertEqual(metadata["zhw_shape"], [3, 5, 7])

            metrics = pd.read_csv(
                directories.formal_results
                / "Layer2R_formal_case_method_metrics.csv"
            )
            self.assertEqual(metrics["method"].tolist(), list(FORMAL_METHOD_ORDER))
            comparisons = pd.read_csv(
                case_dir / "case_pairwise_comparisons_formal.csv"
            )
            self.assertEqual(len(comparisons), 6)
            self.assertEqual(
                (directories.formal_results / "completed_cases.txt")
                .read_text(),
                "case_a\n",
            )

            forbidden = (
                root / "protocol.json",
                directories.formal_results / "RUN_STATUS_LATEST.json",
                case_dir / "baseline_training_history_formal.csv",
                case_dir / "pcc_round_history_formal.csv",
            )
            self.assertTrue(all(not path.exists() for path in forbidden))
            self.assertEqual(list(directories.checkpoints.iterdir()), [])
            self.assertEqual(list(directories.figures.iterdir()), [])

    def test_resume_skips_completed_case_without_duplicate_appends(self):
        result = successful_result()
        with tempfile.TemporaryDirectory() as temporary:
            directories = persist_experiment_result(result, temporary)
            metrics_path = (
                directories.formal_results
                / "Layer2R_formal_case_method_metrics.csv"
            )
            first_metrics = metrics_path.read_text()
            persist_experiment_result(result, temporary)
            self.assertEqual(metrics_path.read_text(), first_metrics)
            self.assertEqual(
                (directories.formal_results / "completed_cases.txt")
                .read_text(),
                "case_a\n",
            )

    def test_resume_uses_seven_method_metrics_and_ignores_bad_csv(self):
        with tempfile.TemporaryDirectory() as temporary:
            directories = create_artifact_directories(temporary)
            rows = [
                {"case_id": "case_metrics", "method": method}
                for method in FORMAL_METHOD_ORDER
            ]
            pd.DataFrame(rows).to_csv(
                directories.formal_results
                / "Layer2R_formal_case_method_metrics.csv",
                index=False,
            )
            self.assertEqual(
                discover_completed_cases(directories.formal_results),
                {"case_metrics"},
            )
            (
                directories.formal_results
                / "Layer2R_formal_case_method_metrics.csv"
            ).write_text("not,a,usable,table\n")
            self.assertEqual(
                discover_completed_cases(directories.formal_results),
                set(),
            )

    def test_failures_append_only_fields_returned_by_order_11(self):
        def failing_preparer(record):
            del record
            raise OSError("unreadable synthetic input")

        result = run_experiment(
            [CaseRecord("case_bad", {})],
            synthetic_baseline,
            case_preparer=failing_preparer,
        )
        with tempfile.TemporaryDirectory() as temporary:
            directories = persist_experiment_result(result, temporary)
            failure_path = directories.formal_results / "failed_cases.csv"
            failure = pd.read_csv(failure_path)
            self.assertEqual(failure.columns.tolist(), ["case_id", "error"])
            self.assertEqual(failure.loc[0, "case_id"], "case_bad")
            self.assertIn("unreadable synthetic input", failure.loc[0, "error"])

            persist_experiment_result(result, temporary)
            self.assertEqual(len(pd.read_csv(failure_path)), 2)

    def test_direct_write_failure_leaves_partial_case_without_completion(self):
        result = successful_result()
        real_save = np.save
        calls = 0

        def fail_on_second_save(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("synthetic partial write")
            return real_save(*args, **kwargs)

        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch(
                "src.artifacts.management.np.save",
                side_effect=fail_on_second_save,
            ):
                with self.assertRaisesRegex(OSError, "partial write"):
                    persist_experiment_result(result, temporary)

            root = Path(temporary)
            case_dir = root / "case_outputs" / "case_a"
            self.assertTrue((case_dir / "current_t1c_norm_zhw.npy").exists())
            self.assertFalse(
                (root / "formal_results" / "completed_cases.txt").exists()
            )


if __name__ == "__main__":
    unittest.main()
