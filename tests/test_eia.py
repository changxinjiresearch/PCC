import unittest

import numpy as np
from scipy.ndimage import (
    binary_closing,
    binary_fill_holes,
    distance_transform_edt,
    gaussian_filter,
    label,
)

from src.models.eia import (
    DILATION_RADIUS,
    EIA_ALPHA,
    EIA_BETA,
    EIA_BLEND_LAMBDA_075,
    EIA_BLEND_LAMBDA_090,
    MIN_COMPONENT_SIZE,
    SIGMA,
    THRESHOLD,
    apply_eia,
)


def notebook_literal_reference(
    baseline,
    target,
    *,
    alpha=0.30,
    beta=0.30,
    blend_lambda_090=0.90,
    blend_lambda_075=0.75,
    dilation_radius=26,
    sigma=2.0,
    threshold=0.5,
    min_component_size=20,
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

    def literal_normalize01(x, eps=1e-8):
        x = x.astype(np.float32)
        mn, mx = float(np.min(x)), float(np.max(x))
        if mx <= mn + eps:
            return np.zeros_like(x, dtype=np.float32)
        return ((x - mn) / (mx - mn + eps)).astype(np.float32)

    target_bool = target.astype(bool)
    fixed_baseline = literal_safe_clip_prob(baseline)

    dist = distance_transform_edt(~target_bool)
    support_region = dist <= dilation_radius

    target_signal = target_bool.astype(np.float32)
    target_signal = gaussian_filter(target_signal, sigma=sigma)
    target_signal = literal_normalize01(target_signal)

    linear = literal_safe_clip_prob(
        fixed_baseline
        + alpha * target_signal * (1.0 - fixed_baseline)
        - beta
        * (~support_region).astype(np.float32)
        * fixed_baseline
    )
    blend090 = literal_safe_clip_prob(
        blend_lambda_090 * fixed_baseline
        + (1.0 - blend_lambda_090) * target_signal
    )
    blend075 = literal_safe_clip_prob(
        blend_lambda_075 * fixed_baseline
        + (1.0 - blend_lambda_075) * target_signal
    )

    baseline_binary = fixed_baseline >= threshold
    morph = np.logical_and(baseline_binary, support_region)
    morph = binary_closing(morph, iterations=1)
    morph = binary_fill_holes(morph)
    labelled, component_count = label(morph)
    keep = np.zeros_like(morph, dtype=bool)
    for component_id in range(1, component_count + 1):
        component = labelled == component_id
        if component.sum() >= min_component_size:
            keep |= component

    return (
        linear,
        blend090,
        blend075,
        keep.astype(np.float32),
        support_region,
        target_signal,
    )


class EIARegressionTests(unittest.TestCase):
    def assert_matches_literal(self, baseline, target, **parameters):
        baseline_original = baseline.copy()
        target_original = target.copy()
        expected = notebook_literal_reference(
            baseline,
            target,
            **parameters,
        )
        actual = apply_eia(baseline, target, **parameters)
        actual_arrays = (
            actual.linear,
            actual.blend090,
            actual.blend075,
            actual.morph,
            actual.support_region,
            actual.target_signal,
        )

        for actual_array, expected_array in zip(
            actual_arrays,
            expected,
            strict=True,
        ):
            np.testing.assert_array_equal(actual_array, expected_array)

        for probability_map in actual_arrays[:4]:
            self.assertEqual(probability_map.dtype, np.dtype(np.float32))
            self.assertEqual(probability_map.shape, baseline.shape)
        self.assertEqual(actual.support_region.dtype, np.dtype(bool))
        self.assertEqual(actual.target_signal.dtype, np.dtype(np.float32))
        np.testing.assert_array_equal(baseline, baseline_original)
        np.testing.assert_array_equal(target, target_original)

    def test_authoritative_constants(self):
        self.assertEqual(DILATION_RADIUS, 26)
        self.assertEqual(SIGMA, 2.0)
        self.assertEqual(EIA_ALPHA, 0.30)
        self.assertEqual(EIA_BETA, 0.30)
        self.assertEqual(EIA_BLEND_LAMBDA_090, 0.90)
        self.assertEqual(EIA_BLEND_LAMBDA_075, 0.75)
        self.assertEqual(THRESHOLD, 0.5)
        self.assertEqual(MIN_COMPONENT_SIZE, 20)

    def test_representative_volume_matches_formal_notebook(self):
        baseline = np.linspace(
            -0.25,
            1.25,
            9 * 10 * 11,
            dtype=np.float64,
        ).reshape(9, 10, 11)
        target = np.zeros(baseline.shape, dtype=np.uint8)
        target[2, 3, 4] = 1
        target[7, 8, 9] = 1
        self.assert_matches_literal(
            baseline,
            target,
            dilation_radius=3,
        )

    def test_nonfinite_baseline_and_nonbinary_target(self):
        baseline = np.full((7, 8, 9), 0.6, dtype=np.float64)
        baseline.ravel()[0] = np.nan
        baseline.ravel()[1] = np.inf
        baseline.ravel()[2] = -np.inf
        target = np.zeros(baseline.shape, dtype=np.int16)
        target[1, 2, 3] = 2
        target[5, 6, 7] = -1
        self.assert_matches_literal(
            baseline,
            target,
            dilation_radius=2,
        )

    def test_morphology_component_size_boundary(self):
        baseline = np.zeros((9, 10, 11), dtype=np.float32)
        baseline[2:5, 2:5, 2:5] = 0.5
        baseline[6:8, 6:8, 6:8] = 1.0
        target = np.ones_like(baseline, dtype=bool)
        self.assert_matches_literal(
            baseline,
            target,
            sigma=0,
            min_component_size=20,
        )

    def test_empty_and_full_targets_preserve_notebook_behavior(self):
        baseline = np.linspace(
            0,
            1,
            6 * 7 * 8,
            dtype=np.float32,
        ).reshape(6, 7, 8)
        for target in [
            np.zeros_like(baseline, dtype=bool),
            np.ones_like(baseline, dtype=bool),
        ]:
            with self.subTest(target_voxels=int(target.sum())):
                self.assert_matches_literal(baseline, target)

    def test_threshold_is_inclusive(self):
        baseline = np.zeros((5, 6, 7), dtype=np.float32)
        baseline[1:4, 1:5, 1:6] = 0.5
        target = np.ones_like(baseline, dtype=bool)
        self.assert_matches_literal(baseline, target, sigma=0)

    def test_custom_parameters_follow_literal_sequence(self):
        rng = np.random.default_rng(20260731)
        baseline = rng.uniform(-1, 2, size=(8, 9, 10))
        target = rng.uniform(size=baseline.shape) > 0.95
        self.assert_matches_literal(
            baseline,
            target,
            alpha=0.17,
            beta=0.23,
            blend_lambda_090=0.81,
            blend_lambda_075=0.64,
            dilation_radius=2.5,
            sigma=1.25,
            threshold=0.4,
            min_component_size=7,
        )

    def test_repeated_execution_is_deterministic(self):
        baseline = np.linspace(0, 1, 7 * 8 * 9).reshape(7, 8, 9)
        target = np.zeros(baseline.shape, dtype=np.uint8)
        target[3, 4, 5] = 1
        first = apply_eia(baseline, target, dilation_radius=2)
        second = apply_eia(baseline, target, dilation_radius=2)
        for first_array, second_array in zip(
            (
                first.linear,
                first.blend090,
                first.blend075,
                first.morph,
                first.support_region,
                first.target_signal,
            ),
            (
                second.linear,
                second.blend090,
                second.blend075,
                second.morph,
                second.support_region,
                second.target_signal,
            ),
            strict=True,
        ):
            np.testing.assert_array_equal(first_array, second_array)

    def test_shape_mismatch_fails_without_hidden_alignment(self):
        baseline = np.zeros((4, 5, 6), dtype=np.float32)
        target = np.zeros((4, 5, 7), dtype=bool)
        with self.assertRaises(ValueError):
            apply_eia(baseline, target)


if __name__ == "__main__":
    unittest.main()
