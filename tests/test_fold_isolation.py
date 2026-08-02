import tempfile
import unittest
from pathlib import Path

from src.pipelines.leakage_free_p0 import CaseIdentity, assert_training_case_ids, build_group_folds, write_locked_fold_manifest


class FoldIsolationTests(unittest.TestCase):
    def setUp(self):
        self.cases = [CaseIdentity(f"P{i}_A", f"P{i}") for i in range(10)] + [CaseIdentity("P0_B", "P0")]

    def test_patient_pairs_never_cross_train_test_boundary(self):
        rows = build_group_folds(self.cases, seed=42)
        for fold in range(1, 6):
            train = {r["patient_id"] for r in rows if r["fold"] == fold and r["split"] == "train"}
            test = {r["patient_id"] for r in rows if r["fold"] == fold and r["split"] == "test"}
            self.assertFalse(train & test)

    def test_every_case_is_test_exactly_once_and_split_is_deterministic(self):
        first = build_group_folds(self.cases, seed=42)
        second = build_group_folds(reversed(self.cases), seed=42)
        self.assertEqual(first, second)
        for case in self.cases:
            self.assertEqual(sum(r["case_id"] == case.case_id and r["split"] == "test" for r in first), 1)

    def test_test_case_cannot_enter_training_dataset(self):
        rows = build_group_folds(self.cases, seed=42)
        test_row = next(r for r in rows if r["split"] == "test")
        self.assertNotIn(test_row["case_id"], assert_training_case_ids(rows, test_row["fold"], test_row["case_id"]))

    def test_locked_manifest_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "LOCKED_FOLD_MANIFEST.csv"
            digest = write_locked_fold_manifest(path, build_group_folds(self.cases))
            self.assertEqual(len(digest), 64)
            with self.assertRaises(FileExistsError):
                write_locked_fold_manifest(path, build_group_folds(self.cases))

    def test_resume_contract_uses_checkpoint_and_completion_markers(self):
        source = Path("src/pipelines/leakage_free_p0.py").read_text()
        self.assertIn("checkpoint.exists() and history_path.exists()", source)
        self.assertIn('P0_COMPLETE.json', source)
        self.assertIn('FOLD_COMPLETE.json', source)


if __name__ == "__main__":
    unittest.main()
