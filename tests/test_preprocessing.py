import unittest

import numpy as np

from src.preprocessing.preprocessing import (
    binarize_mask,
    make_future_change_target,
    make_two_channel_slice,
    preprocess_longitudinal_arrays,
    robust_normalize,
)


def notebook_robust_normalize(
    img,
    brain_mask=None,
    p_low=1,
    p_high=99,
    eps=1e-6,
):
    img = img.astype(np.float32)
    if brain_mask is None:
        brain_mask = img != 0

    vals = img[brain_mask]
    if vals.size < 10:
        return np.zeros_like(img, dtype=np.float32)

    lo, hi = np.percentile(vals, [p_low, p_high])
    if hi <= lo + eps:
        return np.zeros_like(img, dtype=np.float32)

    out = np.clip(img, lo, hi)
    out = (out - lo) / (hi - lo + eps)
    out[~brain_mask] = 0
    return out.astype(np.float32)


def notebook_preprocess_longitudinal_arrays(
    current_t1c,
    future_t1c,
    current_mask,
    future_mask,
):
    current_mask = current_mask > 0
    future_mask = future_mask > 0

    target = np.logical_and(future_mask, np.logical_not(current_mask))
    brain_mask = np.logical_or(current_t1c != 0, future_t1c != 0)

    current_t1c = notebook_robust_normalize(
        current_t1c,
        brain_mask=brain_mask,
    )

    assert (
        current_t1c.shape
        == current_mask.shape
        == future_mask.shape
        == target.shape
    )

    return (
        current_t1c,
        current_mask.astype(np.float32),
        future_mask.astype(np.uint8),
        target.astype(np.uint8),
        brain_mask,
    )


class PreprocessingRegressionTests(unittest.TestCase):
    def test_robust_normalize_matches_literal_notebook_reference(self):
        image = np.linspace(-3.5, 75.25, 3 * 5 * 7, dtype=np.float64).reshape(
            3,
            5,
            7,
        )
        brain_mask = np.zeros(image.shape, dtype=bool)
        brain_mask[:, 1:5, 1:7] = True

        expected = notebook_robust_normalize(image, brain_mask=brain_mask)
        actual = robust_normalize(image, brain_mask=brain_mask)

        np.testing.assert_array_equal(actual, expected)
        self.assertEqual(actual.dtype, np.dtype(np.float32))

    def test_default_brain_mask_matches_notebook_reference(self):
        image = np.arange(24, dtype=np.int16).reshape(2, 3, 4)

        np.testing.assert_array_equal(
            robust_normalize(image),
            notebook_robust_normalize(image),
        )

    def test_small_support_returns_notebook_zero_array(self):
        image = np.arange(12, dtype=np.float64).reshape(3, 2, 2)
        brain_mask = np.zeros(image.shape, dtype=bool)
        brain_mask.reshape(-1)[:9] = True

        expected = notebook_robust_normalize(image, brain_mask=brain_mask)
        actual = robust_normalize(image, brain_mask=brain_mask)

        np.testing.assert_array_equal(actual, expected)
        self.assertEqual(actual.dtype, np.dtype(np.float32))

    def test_degenerate_percentiles_return_notebook_zero_array(self):
        image = np.full((2, 3, 4), 7.0, dtype=np.float64)

        np.testing.assert_array_equal(
            robust_normalize(image),
            notebook_robust_normalize(image),
        )

    def test_explicit_parameters_preserve_notebook_operation_order(self):
        image = np.linspace(0.25, 80.5, 60, dtype=np.float64).reshape(3, 4, 5)
        brain_mask = image > 2

        expected = notebook_robust_normalize(
            image,
            brain_mask=brain_mask,
            p_low=5,
            p_high=95,
            eps=1e-4,
        )
        actual = robust_normalize(
            image,
            brain_mask=brain_mask,
            p_low=5,
            p_high=95,
            eps=1e-4,
        )

        np.testing.assert_array_equal(actual, expected)

    def test_mask_and_target_operations_match_notebook(self):
        current = np.array(
            [[[-1.0, 0.0], [0.25, 2.0]]],
            dtype=np.float32,
        )
        future = np.array(
            [[[0.0, 0.5], [0.25, -2.0]]],
            dtype=np.float32,
        )

        current_bool = current > 0
        future_bool = future > 0

        np.testing.assert_array_equal(binarize_mask(current), current_bool)
        np.testing.assert_array_equal(
            make_future_change_target(current_bool, future_bool),
            np.logical_and(future_bool, np.logical_not(current_bool)),
        )

    def test_complete_preprocessing_matches_literal_notebook_reference(self):
        current_t1c = np.linspace(
            0,
            90,
            3 * 4 * 5,
            dtype=np.float64,
        ).reshape(3, 4, 5)
        future_t1c = np.zeros((3, 4, 5), dtype=np.float64)
        future_t1c[0, 0, 0] = 1
        current_mask = np.zeros((3, 4, 5), dtype=np.float32)
        future_mask = np.zeros((3, 4, 5), dtype=np.float32)
        current_mask[1, 1, 1] = 0.25
        future_mask[1, 1, 1] = 1
        future_mask[2, 2, 2] = 1

        expected = notebook_preprocess_longitudinal_arrays(
            current_t1c,
            future_t1c,
            current_mask,
            future_mask,
        )
        actual = preprocess_longitudinal_arrays(
            current_t1c,
            future_t1c,
            current_mask,
            future_mask,
        )

        for actual_array, expected_array in zip(actual, expected):
            np.testing.assert_array_equal(actual_array, expected_array)

    def test_shape_mismatch_failure_matches_notebook_reference(self):
        current_t1c = np.zeros((3, 4, 5), dtype=np.float32)
        future_t1c = np.zeros((3, 4, 5), dtype=np.float32)
        current_mask = np.zeros((3, 4, 5), dtype=np.float32)
        future_mask = np.zeros((2, 4, 5), dtype=np.float32)

        with self.assertRaises(Exception) as expected:
            notebook_preprocess_longitudinal_arrays(
                current_t1c,
                future_t1c,
                current_mask,
                future_mask,
            )
        with self.assertRaises(type(expected.exception)) as actual:
            preprocess_longitudinal_arrays(
                current_t1c,
                future_t1c,
                current_mask,
                future_mask,
            )
        self.assertEqual(str(actual.exception), str(expected.exception))

    def test_two_channel_slice_matches_notebook_stack(self):
        current_t1c = np.arange(24, dtype=np.float32).reshape(2, 3, 4)
        current_mask = (current_t1c % 3 == 0).astype(np.float32)

        expected = np.stack(
            [current_t1c[1], current_mask[1]],
            axis=0,
        ).astype(np.float32)
        actual = make_two_channel_slice(current_t1c, current_mask, 1)

        np.testing.assert_array_equal(actual, expected)
        self.assertEqual(actual.shape, (2, 3, 4))
        self.assertEqual(actual.dtype, np.dtype(np.float32))


if __name__ == "__main__":
    unittest.main()
