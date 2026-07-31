import unittest

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter

from src.models.pcc import (
    DILATION_RADIUS,
    PCC_ETA,
    PCC_ROUNDS,
    SIGMA,
    apply_pcc,
    make_dilated_region,
    normalize01,
    safe_clip_prob,
    safe_logit,
    sigmoid,
    smooth_mask,
)


def notebook_literal_reference(
    baseline,
    target,
    *,
    eta=0.30,
    sigma=2.0,
    dilation_radius=26,
    iterations=10,
):
    def literal_safe_clip_prob(x):
        return np.clip(
            np.nan_to_num(
                x.astype(np.float32),
                nan=0.0,
                posinf=1.0,
                neginf=0.0,
            ),
            0,
            1,
        )

    def literal_safe_logit(p, eps=1e-5):
        p = np.clip(p.astype(np.float32), eps, 1 - eps)
        return np.log(p / (1 - p)).astype(np.float32)

    def literal_sigmoid(x):
        x = np.clip(x.astype(np.float32), -30, 30)
        return (1.0 / (1.0 + np.exp(-x))).astype(np.float32)

    def literal_normalize01(x, eps=1e-8):
        x = x.astype(np.float32)
        mn, mx = float(np.min(x)), float(np.max(x))
        if mx <= mn + eps:
            return np.zeros_like(x, dtype=np.float32)
        return ((x - mn) / (mx - mn + eps)).astype(np.float32)

    target_bool = target.astype(bool)
    fixed_baseline = literal_safe_clip_prob(baseline)

    dist = distance_transform_edt(~target_bool)
    region = dist <= dilation_radius

    target_signal = target_bool.astype(np.float32)
    target_signal = gaussian_filter(target_signal, sigma=sigma)
    target_signal = literal_normalize01(target_signal)

    pcc = fixed_baseline.copy()
    for _ in range(1, iterations + 1):
        p = literal_safe_clip_prob(pcc)
        residual = (
            (target_bool.astype(np.float32) - p)
            * region.astype(np.float32)
        )
        residual_smooth = gaussian_filter(residual, sigma=sigma)
        background_suppression = (~region).astype(np.float32) * p
        logits = literal_safe_logit(p)
        logits = (
            logits
            + eta * residual_smooth
            - eta * background_suppression
        )
        pcc = literal_safe_clip_prob(literal_sigmoid(logits))

    return pcc, region, target_signal


class PCCRegressionTests(unittest.TestCase):
    def assert_matches_literal(self, baseline, target, **parameters):
        baseline_original = baseline.copy()
        target_original = target.copy()
        expected_pcc, expected_region, expected_signal = (
            notebook_literal_reference(
                baseline,
                target,
                **parameters,
            )
        )
        actual = apply_pcc(baseline, target, **parameters)

        np.testing.assert_array_equal(
            actual.corrected_probability,
            expected_pcc,
        )
        np.testing.assert_array_equal(
            actual.correction_region,
            expected_region,
        )
        np.testing.assert_array_equal(
            actual.target_signal,
            expected_signal,
        )
        self.assertEqual(
            actual.corrected_probability.dtype,
            np.dtype(np.float32),
        )
        self.assertEqual(actual.correction_region.dtype, np.dtype(bool))
        self.assertEqual(actual.target_signal.dtype, np.dtype(np.float32))
        np.testing.assert_array_equal(baseline, baseline_original)
        np.testing.assert_array_equal(target, target_original)

    def test_authoritative_constants(self):
        self.assertEqual(DILATION_RADIUS, 26)
        self.assertEqual(SIGMA, 2.0)
        self.assertEqual(PCC_ROUNDS, 10)
        self.assertEqual(PCC_ETA, 0.30)

    def test_center_target_matches_literal_notebook_sequence(self):
        baseline = np.linspace(
            0,
            1,
            9 * 9 * 9,
            dtype=np.float64,
        ).reshape(9, 9, 9)
        target = np.zeros_like(baseline, dtype=np.uint8)
        target[4, 4, 4] = 1
        self.assert_matches_literal(baseline, target)

    def test_boundary_targets_and_multiple_components(self):
        baseline = np.full((7, 9, 11), 0.5, dtype=np.float32)
        target = np.zeros(baseline.shape, dtype=np.int16)
        target[0, 0, 0] = 2
        target[-1, -1, -1] = -1
        self.assert_matches_literal(
            baseline,
            target,
            dilation_radius=3,
        )

    def test_nonfinite_and_out_of_range_baseline(self):
        baseline = np.linspace(
            -2,
            3,
            5 * 6 * 7,
            dtype=np.float64,
        ).reshape(5, 6, 7)
        baseline.ravel()[0] = np.nan
        baseline.ravel()[1] = np.inf
        baseline.ravel()[2] = -np.inf
        target = np.zeros(baseline.shape, dtype=bool)
        target[2, 3, 4] = True
        self.assert_matches_literal(
            baseline,
            target,
            dilation_radius=2,
        )

    def test_full_target_degenerate_signal_matches_notebook(self):
        baseline = np.full((4, 5, 6), 0.25, dtype=np.float32)
        target = np.ones(baseline.shape, dtype=np.uint8)
        self.assert_matches_literal(baseline, target)

        result = apply_pcc(baseline, target)
        np.testing.assert_array_equal(
            result.target_signal,
            np.zeros_like(baseline, dtype=np.float32),
        )
        self.assertTrue(np.all(result.correction_region))

    def test_smoothed_residual_is_not_remasked_after_filtering(self):
        baseline = np.zeros((13, 13, 13), dtype=np.float32)
        target = np.zeros_like(baseline, dtype=bool)
        target[6, 6, 6] = True

        result = apply_pcc(
            baseline,
            target,
            dilation_radius=0,
            iterations=1,
        )
        self.assertFalse(result.correction_region[6, 6, 7])
        self.assertGreater(result.corrected_probability[6, 6, 7], 1e-5)
        self.assert_matches_literal(
            baseline,
            target,
            dilation_radius=0,
            iterations=1,
        )

    def test_background_suppression_outside_region(self):
        baseline = np.full((13, 13, 13), 0.8, dtype=np.float32)
        target = np.zeros_like(baseline, dtype=bool)
        target[6, 6, 6] = True

        result = apply_pcc(
            baseline,
            target,
            sigma=0,
            dilation_radius=0,
            iterations=1,
        )
        self.assertLess(result.corrected_probability[0, 0, 0], 0.8)
        self.assert_matches_literal(
            baseline,
            target,
            sigma=0,
            dilation_radius=0,
            iterations=1,
        )

    def test_ten_round_call_equals_ten_literal_updates(self):
        rng = np.random.default_rng(20260731)
        baseline = rng.uniform(-0.2, 1.2, size=(6, 7, 8))
        target = rng.uniform(size=baseline.shape) > 0.92
        self.assert_matches_literal(baseline, target)

    def test_helpers_match_literal_operations(self):
        values = np.array(
            [np.nan, -np.inf, -1, 0, 0.5, 1, 2, np.inf],
            dtype=np.float64,
        )
        expected_clipped = np.clip(
            np.nan_to_num(
                values.astype(np.float32),
                nan=0.0,
                posinf=1.0,
                neginf=0.0,
            ),
            0,
            1,
        )
        expected_logit_input = np.clip(
            expected_clipped.astype(np.float32),
            1e-5,
            1 - 1e-5,
        )
        expected_logits = np.log(
            expected_logit_input / (1 - expected_logit_input)
        ).astype(np.float32)
        expected_sigmoid_input = np.clip(
            expected_logits.astype(np.float32),
            -30,
            30,
        )
        expected_sigmoid = (
            1.0 / (1.0 + np.exp(-expected_sigmoid_input))
        ).astype(np.float32)

        np.testing.assert_array_equal(safe_clip_prob(values), expected_clipped)
        np.testing.assert_array_equal(
            safe_logit(expected_clipped),
            expected_logits,
        )
        np.testing.assert_array_equal(
            sigmoid(expected_logits),
            expected_sigmoid,
        )

        target = np.zeros((5, 7, 9), dtype=bool)
        target[2, 3, 4] = True
        expected_region = distance_transform_edt(~target) <= 2
        expected_smoothed = gaussian_filter(
            target.astype(np.float32),
            sigma=1.5,
        )
        expected_signal = normalize01(expected_smoothed)

        np.testing.assert_array_equal(
            make_dilated_region(target, radius=2),
            expected_region,
        )
        np.testing.assert_array_equal(
            smooth_mask(target, sigma=1.5),
            expected_signal,
        )

    def test_repeated_execution_is_deterministic(self):
        baseline = np.linspace(0, 1, 4 * 5 * 6).reshape(4, 5, 6)
        target = np.zeros(baseline.shape, dtype=np.uint8)
        target[1, 2, 3] = 1
        first = apply_pcc(baseline, target)
        second = apply_pcc(baseline, target)

        np.testing.assert_array_equal(
            first.corrected_probability,
            second.corrected_probability,
        )
        np.testing.assert_array_equal(
            first.correction_region,
            second.correction_region,
        )
        np.testing.assert_array_equal(
            first.target_signal,
            second.target_signal,
        )


if __name__ == "__main__":
    unittest.main()
