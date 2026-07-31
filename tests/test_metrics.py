import unittest

import numpy as np

from src.evaluation.metrics import (
    CONCENTRATION_EPS,
    DICE_IOU_EPS,
    MAIN_MODE,
    THRESHOLD,
    dice_binary,
    eval_prob_map,
    iou_binary,
    topk_mask,
)


def notebook_literal_reference(prob, target, threshold=0.5, main_mode="topk"):
    def literal_dice_binary(pred, gt, eps=1e-6):
        pred = pred.astype(bool)
        gt = gt.astype(bool)
        inter = np.logical_and(pred, gt).sum()
        denom = pred.sum() + gt.sum()
        return float((2 * inter + eps) / (denom + eps))

    def literal_iou_binary(pred, gt, eps=1e-6):
        pred = pred.astype(bool)
        gt = gt.astype(bool)
        inter = np.logical_and(pred, gt).sum()
        union = np.logical_or(pred, gt).sum()
        return float((inter + eps) / (union + eps))

    def literal_topk_mask(values, k):
        values = values.astype(np.float32)
        flat = values.reshape(-1)
        k = int(k)
        k = max(1, min(k, flat.size))
        idx = np.argpartition(flat, -k)[-k:]
        out = np.zeros_like(flat, dtype=np.uint8)
        out[idx] = 1
        return out.reshape(values.shape).astype(bool)

    def literal_target_focus(values, gt, eps=1e-8):
        values = values.astype(np.float32)
        gt = gt.astype(bool)
        total = float(values.sum())
        inside = float(values[gt].sum())
        return float(inside / (total + eps))

    def literal_log10_ratio(values, gt, eps=1e-8):
        values = values.astype(np.float32)
        gt = gt.astype(bool)
        inside_mean = float(values[gt].mean()) if gt.sum() > 0 else 0.0
        outside_mean = (
            float(values[~gt].mean()) if (~gt).sum() > 0 else 0.0
        )
        return float(np.log10((inside_mean + eps) / (outside_mean + eps)))

    prob = np.clip(
        np.nan_to_num(
            prob.astype(np.float32),
            nan=0.0,
            posinf=1.0,
            neginf=0.0,
        ),
        0,
        1,
    )
    gt_bool = target.astype(bool)
    pred_fixed = prob >= threshold
    k = int(gt_bool.sum())
    pred_topk = literal_topk_mask(prob, k)

    out = {
        "dice_fixed05": literal_dice_binary(pred_fixed, gt_bool),
        "iou_fixed05": literal_iou_binary(pred_fixed, gt_bool),
        "dice_topk": literal_dice_binary(pred_topk, gt_bool),
        "iou_topk": literal_iou_binary(pred_topk, gt_bool),
        "target_focus": literal_target_focus(prob, gt_bool),
        "log10_ratio": literal_log10_ratio(prob, gt_bool),
        "pred_fixed05_voxels": int(pred_fixed.sum()),
        "pred_topk_voxels": int(pred_topk.sum()),
        "target_voxels": int(gt_bool.sum()),
        "prob_min": float(prob.min()),
        "prob_max": float(prob.max()),
        "prob_mean": float(prob.mean()),
        "prob_sum": float(prob.sum()),
    }
    if main_mode == "topk":
        out["dice"] = out["dice_topk"]
        out["iou"] = out["iou_topk"]
        out["main_mode"] = "topk"
    else:
        out["dice"] = out["dice_fixed05"]
        out["iou"] = out["iou_fixed05"]
        out["main_mode"] = "fixed05"
    return out


class EvaluationMetricRegressionTests(unittest.TestCase):
    def assert_matches_literal(self, prob, target, **parameters):
        prob_original = prob.copy()
        target_original = target.copy()
        expected = notebook_literal_reference(prob, target, **parameters)
        actual = eval_prob_map(prob, target, **parameters)

        self.assertEqual(list(actual), list(expected))
        self.assertEqual(actual, expected)
        np.testing.assert_array_equal(prob, prob_original)
        np.testing.assert_array_equal(target, target_original)

    def test_authoritative_constants(self):
        self.assertEqual(THRESHOLD, 0.5)
        self.assertEqual(MAIN_MODE, "topk")
        self.assertEqual(DICE_IOU_EPS, 1e-6)
        self.assertEqual(CONCENTRATION_EPS, 1e-8)

    def test_representative_zhw_volume_matches_formal_notebook(self):
        prob = np.linspace(
            -0.25,
            1.25,
            4 * 5 * 6,
            dtype=np.float64,
        ).reshape(4, 5, 6)
        target = np.zeros(prob.shape, dtype=np.uint8)
        target[1, 2, 3] = 1
        target[2, 3, 4] = 1
        target[3, 4, 5] = 1
        self.assert_matches_literal(prob, target)

    def test_nonfinite_probability_and_nonbinary_target(self):
        prob = np.array(
            [np.nan, np.inf, -np.inf, -1.0, 0.5, 2.0],
            dtype=np.float64,
        ).reshape(1, 2, 3)
        target = np.array([0, -1, 0, 2, 0, 0], dtype=np.int16).reshape(
            prob.shape
        )
        self.assert_matches_literal(prob, target)

    def test_fixed_threshold_is_inclusive(self):
        prob = np.array([0.49, 0.5, 0.51], dtype=np.float32)
        target = np.array([0, 1, 1], dtype=np.uint8)
        metrics = eval_prob_map(prob, target)
        self.assertEqual(metrics["pred_fixed05_voxels"], 2)
        self.assert_matches_literal(prob, target)

    def test_empty_target_forces_one_topk_voxel(self):
        prob = np.array([0.1, 0.8, 0.2], dtype=np.float32)
        target = np.zeros_like(prob, dtype=bool)
        metrics = eval_prob_map(prob, target)
        expected_overlap = 1e-6 / (1 + 1e-6)
        self.assertEqual(metrics["pred_topk_voxels"], 1)
        self.assertEqual(metrics["dice_topk"], expected_overlap)
        self.assertEqual(metrics["iou_topk"], expected_overlap)
        self.assert_matches_literal(prob, target)

    def test_binary_empty_and_disjoint_behaviour(self):
        empty = np.zeros(4, dtype=np.uint8)
        foreground = np.array([1, 0, 0, 0], dtype=np.uint8)
        disjoint = np.array([0, 1, 0, 0], dtype=np.uint8)
        self.assertEqual(dice_binary(empty, empty), 1.0)
        self.assertEqual(iou_binary(empty, empty), 1.0)
        expected = 1e-6 / (2 + 1e-6)
        self.assertEqual(dice_binary(foreground, disjoint), expected)
        self.assertEqual(iou_binary(foreground, disjoint), expected)

    def test_topk_clamps_requested_count_to_notebook_bounds(self):
        prob = np.array([0.1, 0.4, 0.2], dtype=np.float64)
        self.assertEqual(int(topk_mask(prob, 0).sum()), 1)
        self.assertEqual(int(topk_mask(prob, 99).sum()), prob.size)

    def test_non_topk_mode_uses_fixed05_without_validation(self):
        prob = np.array([0.2, 0.6, 0.9], dtype=np.float32)
        target = np.array([1, 0, 1], dtype=np.uint8)
        metrics = eval_prob_map(prob, target, main_mode="unexpected")
        self.assertEqual(metrics["main_mode"], "fixed05")
        self.assertEqual(metrics["dice"], metrics["dice_fixed05"])
        self.assertEqual(metrics["iou"], metrics["iou_fixed05"])
        self.assert_matches_literal(
            prob,
            target,
            main_mode="unexpected",
        )

    def test_repeated_execution_is_deterministic(self):
        prob = np.arange(60, dtype=np.float32).reshape(3, 4, 5) / 59
        target = (np.arange(60).reshape(3, 4, 5) % 7 == 0)
        self.assertEqual(
            eval_prob_map(prob, target),
            eval_prob_map(prob, target),
        )


if __name__ == "__main__":
    unittest.main()
