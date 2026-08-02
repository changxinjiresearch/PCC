import unittest
import numpy as np

from src.preprocessing.current_only_preprocessing import prepare_current_only_inputs


class NoFutureLeakageTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.RandomState(4)
        self.current = rng.uniform(0, 10, (16, 16, 4)).astype(np.float32)
        self.mask = (rng.rand(16, 16, 4) > 0.9).astype(np.uint8)

    def test_future_image_is_not_an_input(self):
        first = prepare_current_only_inputs(self.current, self.mask).model_input_zchw
        changed_future = np.full_like(self.current, 100000)
        second = prepare_current_only_inputs(self.current, self.mask).model_input_zchw
        np.testing.assert_array_equal(first, second)
        self.assertNotIn("future", prepare_current_only_inputs.__code__.co_varnames)
        self.assertEqual(changed_future.shape, self.current.shape)

    def test_future_mask_is_not_an_input(self):
        signature = prepare_current_only_inputs.__code__.co_varnames[:prepare_current_only_inputs.__code__.co_argcount]
        self.assertEqual(signature, ("current_t1c_hwz", "current_mask_hwz"))

    def test_current_only_shape_and_channels(self):
        actual = prepare_current_only_inputs(self.current, self.mask)
        self.assertEqual(actual.model_input_zchw.shape, (4, 2, 16, 16))
        np.testing.assert_array_equal(actual.model_input_zchw[:, 1], np.moveaxis(self.mask > 0.5, -1, 0))


if __name__ == "__main__":
    unittest.main()
