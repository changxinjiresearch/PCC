import importlib.util
import unittest
import numpy as np


SCIPY_AVAILABLE = importlib.util.find_spec("scipy") is not None


class RetrospectiveContractStaticTests(unittest.TestCase):
    def test_pcc_and_eia_receive_the_same_p0_and_target(self):
        from pathlib import Path
        source = Path("src/pipelines/pcc_leakage_free_rerun.py").read_text()
        self.assertIn("apply_pcc(p0, target, capture_trajectory=True)", source)
        self.assertIn("apply_eia(p0, target)", source)
        self.assertIn('"fixed_baseline": p0.copy()', source)

    def test_trajectory_capture_does_not_change_update_expression(self):
        from pathlib import Path
        source = Path("src/models/pcc.py").read_text()
        update = source.index("pcc = safe_clip_prob(sigmoid(logits))")
        capture = source.index("if capture_trajectory:", update)
        self.assertLess(update, capture)


@unittest.skipUnless(SCIPY_AVAILABLE, "SciPy is required for canonical PCC")
class PCCTrajectoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from src.models.pcc import apply_pcc
        cls.apply_pcc = staticmethod(apply_pcc)

    def test_final_trajectory_map_equals_canonical_final_map(self):
        rng = np.random.RandomState(11)
        p0 = rng.rand(5, 7, 9).astype(np.float32)
        target = np.zeros_like(p0, dtype=np.uint8)
        target[2, 3, 4] = 1
        canonical = self.apply_pcc(p0, target)
        captured = self.apply_pcc(p0, target, capture_trajectory=True)
        self.assertEqual(len(captured.round_probabilities), 10)
        np.testing.assert_array_equal(captured.corrected_probability, canonical.corrected_probability)
        np.testing.assert_array_equal(captured.round_probabilities[-1], canonical.corrected_probability)

    def test_round_r_plus_one_consumes_round_r(self):
        p0 = np.full((4, 5, 6), 0.25, dtype=np.float32)
        target = np.zeros_like(p0, dtype=np.uint8)
        target[1:3, 2:4, 2:4] = 1
        captured = self.apply_pcc(p0, target, capture_trajectory=True)
        self.assertFalse(np.array_equal(captured.round_probabilities[0], p0))
        self.assertFalse(np.array_equal(captured.round_probabilities[1], captured.round_probabilities[0]))
        one_more = self.apply_pcc(captured.round_probabilities[0], target, iterations=1)
        np.testing.assert_array_equal(one_more.corrected_probability, captured.round_probabilities[1])


if __name__ == "__main__":
    unittest.main()
