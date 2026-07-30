import ast
import inspect
import unittest
from pathlib import Path

import numpy as np

import src.models.naive_self_tightening as module
from src.models.naive_self_tightening import (
    NAIVE_GAMMA,
    naive_self_tighten,
    safe_clip_prob,
    safe_logit,
    sigmoid,
)


def notebook_literal_reference(baseline):
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

    fixed_baseline = literal_safe_clip_prob(baseline)
    naive = literal_sigmoid(2.5 * literal_safe_logit(fixed_baseline))
    return naive


class NaiveSelfTighteningRegressionTests(unittest.TestCase):
    def assert_matches_literal(self, values):
        original = values.copy()
        expected = notebook_literal_reference(values)
        actual = naive_self_tighten(values)

        np.testing.assert_array_equal(actual, expected)
        self.assertEqual(actual.dtype, np.dtype(np.float32))
        self.assertEqual(actual.shape, values.shape)
        np.testing.assert_array_equal(values, original)

    def test_authoritative_constant(self):
        self.assertEqual(NAIVE_GAMMA, 2.5)

    def test_representative_probabilities_and_exact_boundaries(self):
        values = np.array(
            [0.0, 0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99, 1.0],
            dtype=np.float32,
        )
        self.assert_matches_literal(values)

    def test_values_immediately_near_zero_and_one(self):
        values = np.array(
            [
                np.nextafter(np.float32(0), np.float32(1)),
                np.nextafter(np.float32(1), np.float32(0)),
            ],
            dtype=np.float32,
        )
        self.assert_matches_literal(values)

    def test_deterministic_multidimensional_ramp_preserves_shape(self):
        values = np.linspace(0, 1, 2 * 3 * 4 * 5, dtype=np.float64).reshape(
            2, 3, 4, 5
        )
        self.assert_matches_literal(values)

    def test_exact_dtype_conversion_for_supported_numeric_dtypes(self):
        for dtype in [np.float16, np.float32, np.float64, np.int16, np.bool_]:
            with self.subTest(dtype=dtype):
                values = np.array([0, 0.25, 0.5, 0.75, 1], dtype=dtype)
                self.assert_matches_literal(values)

    def test_input_is_not_mutated(self):
        values = np.array(
            [np.nan, -np.inf, -1.0, 0.5, 2.0, np.inf],
            dtype=np.float64,
        )
        original = values.copy()
        naive_self_tighten(values)
        np.testing.assert_array_equal(values, original)

    def test_repeated_execution_is_deterministic(self):
        values = np.linspace(-1, 2, 101, dtype=np.float32)
        first = naive_self_tighten(values)
        second = naive_self_tighten(values)
        np.testing.assert_array_equal(first, second)

    def test_noncontiguous_sliced_array(self):
        contiguous = np.linspace(-1, 2, 60, dtype=np.float64).reshape(5, 12)
        values = contiguous[:, ::3]
        self.assertFalse(values.flags.c_contiguous)
        self.assert_matches_literal(values)

    def test_empty_arrays(self):
        for shape in [(0,), (0, 3), (2, 0, 4)]:
            with self.subTest(shape=shape):
                self.assert_matches_literal(np.empty(shape, dtype=np.float64))

    def test_nan_positive_and_negative_infinity(self):
        values = np.array([np.nan, np.inf, -np.inf], dtype=np.float64)
        self.assert_matches_literal(values)

        actual = naive_self_tighten(values)
        boundary = naive_self_tighten(
            np.array([0.0, 1.0, 0.0], dtype=np.float32)
        )
        np.testing.assert_array_equal(actual, boundary)

    def test_out_of_range_values(self):
        values = np.array(
            [-np.finfo(np.float64).max, -2.0, -0.01, 1.01, 2.0,
             np.finfo(np.float64).max],
            dtype=np.float64,
        )
        self.assert_matches_literal(values)

    def test_helpers_match_literal_operation_sequence(self):
        values = np.array(
            [np.nan, -np.inf, -1, 0, 1e-6, 0.5, 1 - 1e-6, 1, 2, np.inf],
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
            expected_clipped.astype(np.float32), 1e-5, 1 - 1e-5
        )
        expected_logits = np.log(
            expected_logit_input / (1 - expected_logit_input)
        ).astype(np.float32)
        expected_scaled = 2.5 * expected_logits
        expected_sigmoid_input = np.clip(
            expected_scaled.astype(np.float32), -30, 30
        )
        expected = (
            1.0 / (1.0 + np.exp(-expected_sigmoid_input))
        ).astype(np.float32)

        np.testing.assert_array_equal(safe_clip_prob(values), expected_clipped)
        np.testing.assert_array_equal(
            safe_logit(expected_clipped), expected_logits
        )
        np.testing.assert_array_equal(sigmoid(expected_scaled), expected)
        np.testing.assert_array_equal(naive_self_tighten(values), expected)

    def test_randomized_exact_literal_comparisons(self):
        rng = np.random.default_rng(20260731)
        for dtype in [np.float32, np.float64]:
            with self.subTest(dtype=dtype):
                values = rng.uniform(-2, 3, size=(7, 5, 9)).astype(dtype)
                values.ravel()[::37] = np.nan
                values.ravel()[1::41] = np.inf
                values.ravel()[2::43] = -np.inf
                self.assert_matches_literal(values)

    def test_module_contains_only_the_scoped_transformation(self):
        source = inspect.getsource(module)
        tree = ast.parse(source)
        function_names = {
            node.name for node in tree.body if isinstance(node, ast.FunctionDef)
        }
        self.assertEqual(
            function_names,
            {
                "safe_clip_prob",
                "safe_logit",
                "sigmoid",
                "naive_self_tighten",
            },
        )

        forbidden = {
            "threshold",
            "morphology",
            "iteration",
            "training",
            "pcc",
            "eia",
            "evaluate",
            "visualize",
            "persistence",
        }
        executable_source = "\n".join(
            line for line in source.splitlines() if not line.lstrip().startswith("#")
        ).lower()
        for term in forbidden:
            with self.subTest(term=term):
                self.assertNotIn(term, executable_source)

    def test_no_order_6_module_created(self):
        repository_root = Path(__file__).resolve().parents[1]
        self.assertFalse((repository_root / "src/models/pcc.py").exists())


if __name__ == "__main__":
    unittest.main()
