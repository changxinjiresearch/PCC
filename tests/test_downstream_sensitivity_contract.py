import unittest
from pathlib import Path

try:
    from experiments.run_pcc_downstream import CANONICAL, SENSITIVITY
except ModuleNotFoundError as error:
    if error.name != "scipy":
        raise
    CANONICAL = None
    SENSITIVITY = None


@unittest.skipIf(SENSITIVITY is None, "SciPy is not installed in the local environment")
class DownstreamSensitivityContractTests(unittest.TestCase):
    def test_grid_changes_exactly_one_canonical_parameter(self):
        self.assertEqual(len(SENSITIVITY), 8)
        self.assertEqual(len({name for name, _ in SENSITIVITY}), 8)
        for _, parameters in SENSITIVITY:
            changed = [key for key in CANONICAL if parameters[key] != CANONICAL[key]]
            self.assertEqual(len(changed), 1)

    def test_grid_is_the_predeclared_historical_grid(self):
        self.assertEqual(
            dict(SENSITIVITY),
            {
                "rounds_5": {**CANONICAL, "iterations": 5},
                "rounds_15": {**CANONICAL, "iterations": 15},
                "eta_020": {**CANONICAL, "eta": 0.20},
                "eta_040": {**CANONICAL, "eta": 0.40},
                "radius_18": {**CANONICAL, "dilation_radius": 18.0},
                "radius_34": {**CANONICAL, "dilation_radius": 34.0},
                "sigma_1": {**CANONICAL, "sigma": 1.0},
                "sigma_3": {**CANONICAL, "sigma": 3.0},
            },
        )

    def test_runner_has_no_predictor_or_training_import(self):
        source = Path("experiments/run_pcc_downstream.py").read_text()
        self.assertNotIn("leakage_free_p0", source)
        self.assertNotIn("optimizer", source.lower())
        self.assertNotIn("backward(", source)


if __name__ == "__main__":
    unittest.main()
