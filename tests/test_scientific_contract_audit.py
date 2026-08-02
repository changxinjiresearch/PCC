"""Static regression guards for scientific facts discovered by the rerun audit.

These tests do not endorse the target-conditioned baseline as leakage-free.
They prevent the audit from being invalidated by silently relabelling the
historical implementation.
"""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ScientificContractAuditTests(unittest.TestCase):
    def test_historical_case_baseline_is_explicitly_target_trained(self):
        source = (ROOT / "src/models/formal_layer2r_baseline.py").read_text()
        self.assertIn("dataset = SliceDataset(current_t1c, current_mask, target)", source)
        self.assertIn("loss.backward()", source)
        self.assertIn("optimizer.step()", source)
        self.assertIn("probability_map,\n            target,", source)

    def test_formal_current_normalization_support_uses_future_image(self):
        source = (ROOT / "src/preprocessing/preprocessing.py").read_text()
        self.assertIn(
            "brain_mask = np.logical_or(current_t1c != 0, future_t1c != 0)",
            source,
        )

    def test_pcc_is_map_refinement_with_round_state_propagation(self):
        source = (ROOT / "src/models/pcc.py").read_text()
        self.assertIn("for _ in range(1, iterations + 1):", source)
        self.assertIn("target_bool.astype(np.float32) - p", source)
        self.assertIn("background_suppression", source)
        self.assertIn("pcc = safe_clip_prob(sigmoid(logits))", source)
        self.assertNotIn("optimizer.step", source)
        self.assertNotIn("loss.backward", source)

    def test_naive_module_has_no_target_parameter(self):
        source = (ROOT / "src/models/naive_self_tightening.py").read_text()
        signature = source.split("def naive_self_tighten", 1)[1].split(")", 1)[0]
        self.assertNotIn("target", signature)


if __name__ == "__main__":
    unittest.main()
