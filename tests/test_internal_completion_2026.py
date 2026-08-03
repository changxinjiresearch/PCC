import unittest

import numpy as np
import csv
import tempfile
from pathlib import Path

try:
    from src.analysis.internal_completion import (
        component_count, deranged_donors, fp25_guidance, large_components,
        mixed_guidance, partial_guidance, physical_dilate, physical_erode,
        run_variant, shift_no_wrap,
    )
except ImportError as exc:  # dependency-compatible local collection
    raise unittest.SkipTest(str(exc))


class InternalCompletionProtocolTests(unittest.TestCase):
    def setUp(self):
        self.mask = np.zeros((15, 15, 15), dtype=bool)
        self.mask[5:10, 5:10, 5:10] = True
        self.p0 = np.linspace(0.01, 0.99, self.mask.size, dtype=np.float32).reshape(self.mask.shape)

    def test_factorial_both_off_is_exact_identity(self):
        result = run_variant(self.p0, self.mask, error_guided=False, outside_suppression=False)
        np.testing.assert_array_equal(result.probability, self.p0)

    def test_each_active_term_changes_state(self):
        error = run_variant(self.p0, self.mask, error_guided=True, outside_suppression=False, rounds=2)
        suppression = run_variant(self.p0, self.mask, error_guided=False, outside_suppression=True, rounds=2)
        self.assertFalse(np.array_equal(error.probability, self.p0))
        self.assertFalse(np.array_equal(suppression.probability, self.p0))

    def test_partial_is_deterministic_and_component_preserving(self):
        first, fraction1 = partial_guidance(self.mask, 0.5)
        second, fraction2 = partial_guidance(self.mask, 0.5)
        np.testing.assert_array_equal(first, second)
        self.assertEqual(component_count(first), 1)
        self.assertEqual(fraction1, fraction2)
        self.assertAlmostEqual(fraction1, 0.5, delta=0.01)

    def test_fp_seed_is_deterministic_and_external(self):
        first, added1, short1 = fp25_guidance(self.mask, (1.0, 1.0, 1.0), "case", 20260803)
        second, added2, short2 = fp25_guidance(self.mask, (1.0, 1.0, 1.0), "case", 20260803)
        np.testing.assert_array_equal(first, second)
        self.assertFalse(np.any((first & ~self.mask) & self.mask))
        self.assertEqual((added1, short1), (added2, short2))

    def test_shift_does_not_wrap(self):
        edge = np.zeros((5, 5, 5), dtype=bool); edge[:, :, -1] = True
        shifted = shift_no_wrap(edge, "+x", 3)
        self.assertEqual(int(shifted.sum()), 0)

    def test_mixed_repeat_is_deterministic(self):
        a, details_a = mixed_guidance(self.mask, (1.0, 1.0, 1.0), "case", 20260803, "+x")
        b, details_b = mixed_guidance(self.mask, (1.0, 1.0, 1.0), "case", 20260803, "+x")
        np.testing.assert_array_equal(a, b); self.assertEqual(details_a, details_b)

    def test_physical_target_operations(self):
        dilated = physical_dilate(self.mask, (2.0, 1.0, 1.0), 2.0)
        eroded = physical_erode(self.mask, (2.0, 1.0, 1.0), 2.0)
        self.assertGreater(dilated.sum(), self.mask.sum())
        self.assertLess(eroded.sum(), self.mask.sum())

    def test_large_component_threshold_uses_physical_volume(self):
        retained = large_components(self.mask, (1.0, 1.0, 1.0), 100.0)
        self.assertEqual(int(retained.sum()), 125)
        removed = large_components(self.mask, (1.0, 1.0, 1.0), 126.0)
        self.assertEqual(int(removed.sum()), 0)

    def test_derangement_patient_disjoint_and_deterministic(self):
        cases = [f"c{i}" for i in range(8)]
        volumes = {case: (i + 1) * 100 for i, case in enumerate(cases)}
        patients = {case: f"p{i // 2}" for i, case in enumerate(cases)}
        first = deranged_donors(cases, volumes, patients)
        second = deranged_donors(cases, volumes, patients)
        self.assertEqual(first, second)
        self.assertEqual(set(first), set(cases)); self.assertEqual(set(first.values()), set(cases))
        for recipient, donor in first.items():
            self.assertNotEqual(recipient, donor)
            self.assertNotEqual(patients[recipient], patients[donor])

    def test_atomic_csv_preserves_union_schema(self):
        from experiments.run_internal_completion_2026 import atomic_csv
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "result.csv"
            atomic_csv(path, [{"case_id": "a", "dice": 0.1}, {"case_id": "b", "dice": 0.2, "target_mass": 3.0}])
            with path.open(newline="") as handle:
                rows = list(csv.DictReader(handle))
        self.assertIn("target_mass", rows[0])
        self.assertEqual(rows[1]["target_mass"], "3.0")

    def test_difference_normalization_is_independent_per_image(self):
        import nibabel as nib
        from experiments.run_internal_completion_2026 import normalized_intensity
        affine = np.eye(4)
        values = np.arange(27, dtype=np.float32).reshape(3, 3, 3)
        first = nib.Nifti1Image(values, affine)
        second = nib.Nifti1Image(values * 10, affine)
        np.testing.assert_allclose(normalized_intensity(first), normalized_intensity(second))


if __name__ == "__main__":
    unittest.main()
