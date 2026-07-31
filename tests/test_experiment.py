import unittest

import numpy as np
from pandas.testing import assert_frame_equal

from src.evaluation.metrics import eval_prob_map
from src.models.eia import apply_eia
from src.models.naive_self_tightening import naive_self_tighten
from src.models.pcc import apply_pcc
from src.pipelines.experiment import CaseRecord, run_case, run_experiment
from src.preprocessing.preprocessing import PreprocessedLongitudinalCase
from src.statistics.statistics import (
    METHOD_ORDER,
    build_pairwise_comparisons,
    summarize_methods,
    summarize_pairwise,
)


def prepared_case(offset=0.0):
    shape = (5, 7, 9)
    current = np.linspace(0, 1, np.prod(shape), dtype=np.float32).reshape(shape)
    current = np.clip(current + offset, 0, 1)
    current_mask = np.zeros(shape, dtype=np.float32)
    future_mask = np.zeros(shape, dtype=np.uint8)
    target = np.zeros(shape, dtype=np.uint8)
    target[2, 2:5, 3:7] = 1
    future_mask[target.astype(bool)] = 1
    return PreprocessedLongitudinalCase(
        current,
        current_mask,
        future_mask,
        target,
        np.ones(shape, dtype=bool),
    )


def synthetic_preparer(record):
    offset = 0.05 if record.case_id.endswith("b") else 0.0
    return prepared_case(offset)


def synthetic_baseline(case_id, prepared):
    del case_id
    return (0.1 + 0.8 * prepared.current_t1c).astype(np.float32)


class ExperimentPipelineTests(unittest.TestCase):
    def test_one_case_matches_direct_orders_five_through_eight(self):
        record = CaseRecord("case_a", {})
        actual = run_case(
            record,
            synthetic_baseline,
            case_preparer=synthetic_preparer,
        )
        target = actual.prepared.future_change_target
        baseline = synthetic_baseline(record.case_id, actual.prepared)
        eia = apply_eia(baseline, target)
        expected_maps = {
            "fixed_baseline": baseline,
            "naive_self_tightening": naive_self_tighten(baseline),
            "eia_linear": eia.linear,
            "eia_blend090": eia.blend090,
            "eia_blend075": eia.blend075,
            "eia_morph": eia.morph,
            "pcc_correction": apply_pcc(baseline, target).corrected_probability,
        }
        self.assertEqual(tuple(actual.method_maps), METHOD_ORDER)
        self.assertEqual(actual.metrics["method"].tolist(), list(METHOD_ORDER))
        for method in METHOD_ORDER:
            np.testing.assert_array_equal(
                actual.method_maps[method],
                expected_maps[method],
            )
            expected_metrics = eval_prob_map(expected_maps[method], target)
            row = actual.metrics[actual.metrics["method"] == method].iloc[0]
            for key, value in expected_metrics.items():
                self.assertEqual(row[key], value)

    def test_cohort_order_summaries_progress_and_optional_figures(self):
        records = [
            CaseRecord("case_b", {}),
            CaseRecord("case_a", {}),
            CaseRecord("case_b", {"duplicate": True}),
        ]
        progress = []
        figures = []
        result = run_experiment(
            records,
            synthetic_baseline,
            case_preparer=synthetic_preparer,
            progress_callback=lambda event, case_id: progress.append((event, case_id)),
            figure_callback=lambda case: figures.append(case.case_id),
        )
        self.assertEqual(result.case_order, ("case_a", "case_b"))
        self.assertEqual(
            tuple(case.case_id for case in result.cases),
            result.case_order,
        )
        self.assertEqual(figures, ["case_a", "case_b"])
        self.assertEqual(
            progress,
            [
                ("started", "case_a"),
                ("completed", "case_a"),
                ("started", "case_b"),
                ("completed", "case_b"),
            ],
        )
        self.assertEqual(len(result.metrics), 14)
        self.assertEqual(len(result.pairwise_comparisons), 12)
        assert_frame_equal(
            result.pairwise_comparisons,
            build_pairwise_comparisons(result.metrics),
        )
        assert_frame_equal(result.method_summary, summarize_methods(result.metrics))
        assert_frame_equal(
            result.pairwise_summary,
            summarize_pairwise(result.pairwise_comparisons),
        )

    def test_failed_case_is_recorded_and_later_case_continues(self):
        def preparer(record):
            if record.case_id == "case_bad":
                raise OSError("unreadable synthetic input")
            return prepared_case()

        result = run_experiment(
            [CaseRecord("case_good", {}), CaseRecord("case_bad", {})],
            synthetic_baseline,
            case_preparer=preparer,
        )
        self.assertEqual(result.case_order, ("case_bad", "case_good"))
        self.assertEqual([case.case_id for case in result.cases], ["case_good"])
        self.assertEqual([failure.case_id for failure in result.failures], ["case_bad"])
        self.assertIsInstance(result.failures[0].error, OSError)
        self.assertEqual(len(result.metrics), 7)

    def test_empty_target_and_baseline_shape_mismatch_fail_before_methods(self):
        empty = prepared_case()
        empty.future_change_target.fill(0)
        with self.assertRaisesRegex(ValueError, "target is empty"):
            run_case(
                CaseRecord("empty", {}),
                synthetic_baseline,
                case_preparer=lambda record: empty,
            )
        with self.assertRaisesRegex(ValueError, "shapes differ"):
            run_case(
                CaseRecord("mismatch", {}),
                lambda case_id, prepared: np.zeros((2, 2, 2)),
                case_preparer=synthetic_preparer,
            )

    def test_no_successes_returns_stable_empty_tables(self):
        result = run_experiment(
            [CaseRecord("bad", {})],
            synthetic_baseline,
            case_preparer=lambda record: (_ for _ in ()).throw(OSError("bad")),
        )
        self.assertTrue(result.metrics.empty)
        self.assertTrue(result.pairwise_comparisons.empty)
        self.assertIsNone(result.method_summary)
        self.assertTrue(result.pairwise_summary.empty)


if __name__ == "__main__":
    unittest.main()
