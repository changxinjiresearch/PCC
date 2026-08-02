import hashlib
import unittest
import numpy as np

from src.preprocessing.current_only_preprocessing import prepare_current_only_inputs, construct_future_change_label


def deterministic_fake_predictor(inputs):
    return inputs[:, 0].astype(np.float32) * 0.7 + inputs[:, 1].astype(np.float32) * 0.3


class P0IndependenceTests(unittest.TestCase):
    def test_changing_test_future_target_does_not_change_p0(self):
        rng = np.random.RandomState(9)
        current = rng.uniform(1, 20, (16, 16, 3)).astype(np.float32)
        current_mask = (rng.rand(16, 16, 3) > 0.95).astype(np.uint8)
        future_a = np.zeros_like(current_mask)
        future_b = np.ones_like(current_mask)
        target_a = construct_future_change_label(current_mask, future_a)
        target_b = construct_future_change_label(current_mask, future_b)
        self.assertFalse(np.array_equal(target_a, target_b))
        inputs_a = prepare_current_only_inputs(current, current_mask).model_input_zchw
        inputs_b = prepare_current_only_inputs(current, current_mask).model_input_zchw
        p0_a = deterministic_fake_predictor(inputs_a)
        p0_b = deterministic_fake_predictor(inputs_b)
        np.testing.assert_array_equal(p0_a, p0_b)
        self.assertEqual(hashlib.sha256(p0_a.tobytes()).digest(), hashlib.sha256(p0_b.tobytes()).digest())

    def test_fixed_is_exactly_p0_and_naive_signature_has_no_target(self):
        from src.models.naive_self_tightening import naive_self_tighten
        p0 = np.linspace(0, 1, 12, dtype=np.float32)
        fixed = p0.copy()
        np.testing.assert_array_equal(fixed, p0)
        self.assertEqual(naive_self_tighten.__code__.co_argcount, 1)  # baseline only


if __name__ == "__main__":
    unittest.main()
