import unittest

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from src.statistics.statistics import (
    COMPARATOR_ORDER,
    METHOD_ORDER,
    METHOD_SUMMARY_COLUMNS,
    PAIRWISE_COLUMNS,
    PAIRWISE_SUMMARY_COLUMNS,
    build_pairwise_comparisons,
    summarize_methods,
    summarize_pairwise,
)


def synthetic_metrics():
    values = {
        "case_b": {
            "fixed_baseline": (0.4, 0.3, 0.10, 1.0),
            "naive_self_tightening": (0.5, 0.4, 0.15, 1.1),
            "eia_linear": (0.6, 0.5, 0.20, 1.2),
            "eia_blend090": (0.7, 0.6, 0.25, 1.3),
            "eia_blend075": (0.9, 0.8, 0.30, 1.4),
            "eia_morph": (0.8, 0.7, 0.35, 1.5),
            "pcc_correction": (0.8, 0.7, 0.40, 1.6),
        },
        "case_a": {
            "fixed_baseline": (0.2, 0.1, 0.05, 0.5),
            "naive_self_tightening": (0.3, 0.2, 0.10, 0.6),
            "eia_linear": (0.4, 0.3, 0.15, 0.7),
            "eia_blend090": (0.5, 0.4, 0.20, 0.8),
            "eia_blend075": (0.6, 0.5, 0.25, 0.9),
            "eia_morph": (0.7, 0.6, 0.30, 1.0),
            "pcc_correction": (0.7, 0.6, 0.35, 1.1),
        },
    }
    rows = []
    for case_id, methods in values.items():
        for method in METHOD_ORDER:
            dice, iou, focus, ratio = methods[method]
            rows.append(
                {
                    "case_id": case_id,
                    "method": method,
                    "dice": dice,
                    "iou": iou,
                    "target_focus": focus,
                    "log10_ratio": ratio,
                }
            )
    return pd.DataFrame(rows)


class StatisticalAnalysisRegressionTests(unittest.TestCase):
    def test_authoritative_seven_method_order(self):
        self.assertEqual(
            METHOD_ORDER,
            (
                "fixed_baseline",
                "naive_self_tightening",
                "eia_linear",
                "eia_blend090",
                "eia_blend075",
                "eia_morph",
                "pcc_correction",
            ),
        )
        self.assertEqual(COMPARATOR_ORDER, METHOD_ORDER[:-1])

    def test_literal_per_case_pcc_differences_and_structure(self):
        actual = build_pairwise_comparisons(synthetic_metrics())
        expected_first_case = pd.DataFrame(
            [
                ["case_b", "PCC vs fixed_baseline", 0.4, 0.4, 0.30, 0.6, True, True],
                ["case_b", "PCC vs naive_self_tightening", 0.3, 0.3, 0.25, 0.5, True, True],
                ["case_b", "PCC vs eia_linear", 0.2, 0.2, 0.20, 0.4, True, True],
                ["case_b", "PCC vs eia_blend090", 0.1, 0.1, 0.15, 0.3, True, True],
                ["case_b", "PCC vs eia_blend075", -0.1, -0.1, 0.10, 0.2, False, False],
                ["case_b", "PCC vs eia_morph", 0.0, 0.0, 0.05, 0.1, False, False],
            ],
            columns=PAIRWISE_COLUMNS,
        )
        self.assertEqual(list(actual.columns), list(PAIRWISE_COLUMNS))
        assert_frame_equal(
            actual.iloc[:6].reset_index(drop=True),
            expected_first_case,
        )
        self.assertEqual(actual["pcc_better_dice"].dtype, bool)
        self.assertEqual(actual["pcc_better_iou"].dtype, bool)

    def test_literal_method_aggregation_and_alphabetical_sorting(self):
        actual = summarize_methods(synthetic_metrics())
        self.assertIsNotNone(actual)
        self.assertEqual(list(actual.columns), list(METHOD_SUMMARY_COLUMNS))
        self.assertEqual(
            actual["method"].tolist(),
            sorted(METHOD_ORDER),
        )
        fixed = actual[actual["method"] == "fixed_baseline"].iloc[0]
        self.assertEqual(fixed["n"], 2)
        self.assertEqual(fixed["dice_mean"], (0.4 + 0.2) / 2)
        self.assertEqual(fixed["dice_median"], (0.2 + 0.4) / 2)
        self.assertEqual(fixed["iou_mean"], (0.3 + 0.1) / 2)
        self.assertEqual(fixed["target_focus_mean"], (0.10 + 0.05) / 2)
        self.assertEqual(fixed["log10_ratio_median"], (0.5 + 1.0) / 2)

    def test_literal_pairwise_aggregation_sorting_wins_and_ties(self):
        comparisons = build_pairwise_comparisons(synthetic_metrics())
        actual = summarize_pairwise(comparisons)
        self.assertEqual(
            list(actual.columns),
            list(PAIRWISE_SUMMARY_COLUMNS),
        )
        self.assertEqual(
            actual["comparison"].tolist(),
            sorted(f"PCC vs {method}" for method in COMPARATOR_ORDER),
        )
        morph = actual[actual["comparison"] == "PCC vs eia_morph"].iloc[0]
        self.assertEqual(morph["n"], 2)
        self.assertEqual(morph["dice_mean_diff"], 0.0)
        self.assertEqual(morph["dice_median_diff"], 0.0)
        self.assertEqual(morph["dice_wins"], 0)
        self.assertEqual(morph["iou_wins"], 0)
        self.assertEqual(morph["dice_win_rate"], 0.0)
        blend075 = actual[
            actual["comparison"] == "PCC vs eia_blend075"
        ].iloc[0]
        self.assertEqual(blend075["dice_mean_diff"], 0.0)
        self.assertEqual(blend075["dice_wins"], 1)
        self.assertEqual(blend075["dice_win_rate"], 0.5)

    def test_one_case_all_ties(self):
        rows = [
            {
                "case_id": "only",
                "method": method,
                "dice": 0.5,
                "iou": 0.4,
                "target_focus": 0.3,
                "log10_ratio": 0.2,
            }
            for method in METHOD_ORDER
        ]
        comparisons = build_pairwise_comparisons(pd.DataFrame(rows))
        summary = summarize_pairwise(comparisons)
        self.assertTrue((comparisons["dice_diff"] == 0.0).all())
        self.assertTrue((comparisons["pcc_better_dice"] == False).all())
        self.assertTrue((summary["dice_wins"] == 0).all())
        self.assertTrue((summary["dice_win_rate"] == 0.0).all())

    def test_nan_and_infinity_follow_notebook_pandas_behaviour(self):
        metrics = synthetic_metrics()
        metrics.loc[
            (metrics["case_id"] == "case_b")
            & (metrics["method"] == "fixed_baseline"),
            "dice",
        ] = np.nan
        metrics.loc[
            (metrics["case_id"] == "case_a")
            & (metrics["method"] == "fixed_baseline"),
            "iou",
        ] = np.inf
        comparisons = build_pairwise_comparisons(metrics)
        case_b = comparisons[
            (comparisons["case_id"] == "case_b")
            & (comparisons["comparison"] == "PCC vs fixed_baseline")
        ].iloc[0]
        self.assertTrue(np.isnan(case_b["dice_diff"]))
        self.assertFalse(case_b["pcc_better_dice"])
        method_summary = summarize_methods(metrics)
        fixed = method_summary[
            method_summary["method"] == "fixed_baseline"
        ].iloc[0]
        self.assertEqual(fixed["dice_mean"], 0.2)
        self.assertTrue(np.isinf(fixed["iou_mean"]))

    def test_empty_input_behaviour(self):
        empty_metrics = pd.DataFrame(
            columns=[
                "case_id",
                "method",
                "dice",
                "iou",
                "target_focus",
                "log10_ratio",
            ]
        )
        comparisons = build_pairwise_comparisons(empty_metrics)
        self.assertEqual(list(comparisons.columns), list(PAIRWISE_COLUMNS))
        self.assertTrue(comparisons.empty)
        self.assertIsNone(summarize_methods(empty_metrics))
        pairwise_summary = summarize_pairwise(comparisons)
        self.assertEqual(
            list(pairwise_summary.columns),
            list(PAIRWISE_SUMMARY_COLUMNS),
        )
        self.assertTrue(pairwise_summary.empty)

    def test_malformed_records_raise_notebook_errors(self):
        with self.assertRaises(KeyError):
            build_pairwise_comparisons(pd.DataFrame({"method": []}))

        missing_pcc = synthetic_metrics()
        missing_pcc = missing_pcc[
            ~(
                (missing_pcc["case_id"] == "case_b")
                & (missing_pcc["method"] == "pcc_correction")
            )
        ]
        with self.assertRaises(IndexError):
            build_pairwise_comparisons(missing_pcc)

        with self.assertRaises(KeyError):
            summarize_methods(pd.DataFrame({"case_id": ["case"]}))


if __name__ == "__main__":
    unittest.main()
