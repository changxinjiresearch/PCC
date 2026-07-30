import csv
import re
import tempfile
import unittest
from pathlib import Path

from src.data.dataset_identity import (
    get_raw_paths,
    load_locked_case_ids,
    locked_case_ids,
    parse_case_id,
    require_raw_paths,
    validate_raw_paths,
)

LOCKED_COHORT_FIXTURE_DIR = (
    Path(__file__).parent / "fixtures" / "locked_cohort"
)
LOCKED_COHORT_CSV = (
    LOCKED_COHORT_FIXTURE_DIR / "direct_target_case_metrics.csv"
)
LOCKED_COHORT_EXPECTED = LOCKED_COHORT_FIXTURE_DIR / "locked_case_ids.txt"


def notebook_parse_case_id(case_id):
    match = re.match(r"(PatientID_\d+)_T(\d+)_to_T(\d+)_(\w+)", case_id)
    if not match:
        raise ValueError(f"Cannot parse case_id: {case_id}")
    return (
        match.group(1),
        int(match.group(2)),
        int(match.group(3)),
        match.group(4),
    )


def notebook_get_raw_paths(case_id, raw_root):
    patient_id, current_timepoint, future_timepoint, modality = (
        notebook_parse_case_id(case_id)
    )
    patient_dir = raw_root / patient_id
    current_dir = patient_dir / f"Timepoint_{current_timepoint}"
    future_dir = patient_dir / f"Timepoint_{future_timepoint}"
    return {
        "case_id": case_id,
        "patient_id": patient_id,
        "cur_tp": current_timepoint,
        "fut_tp": future_timepoint,
        "modality": modality,
        "cur_img": current_dir
        / f"{patient_id}_Timepoint_{current_timepoint}_brain_{modality}.nii",
        "fut_img": future_dir
        / f"{patient_id}_Timepoint_{future_timepoint}_brain_{modality}.nii",
        "cur_mask": current_dir
        / f"{patient_id}_Timepoint_{current_timepoint}_tumorMask.nii",
        "fut_mask": future_dir
        / f"{patient_id}_Timepoint_{future_timepoint}_tumorMask.nii",
    }


def notebook_validate_raw_paths(paths):
    row = {"case_id": paths["case_id"]}
    ok = True
    for key in ["cur_img", "fut_img", "cur_mask", "fut_mask"]:
        exists = paths[key].exists()
        row[key] = str(paths[key])
        row[key + "_exists"] = exists
        if not exists:
            ok = False
    row["all_exists"] = ok
    return row


class DatasetIdentityRegressionTests(unittest.TestCase):
    def test_parse_case_id_matches_notebook(self):
        case_ids = [
            "PatientID_0003_T1_to_T2_t1c",
            "PatientID_0053_T1_to_T3_t1c",
            "PatientID_0003_T1_to_T2_t1c_trailing",
            "PatientID_0003_T1_to_T2_t1c.trailing",
        ]
        for case_id in case_ids:
            self.assertEqual(
                parse_case_id(case_id), notebook_parse_case_id(case_id)
            )

    def test_trailing_text_behavior_matches_notebook(self):
        case_id = "PatientID_0003_T1_to_T2_t1c_extra_text"
        self.assertEqual(
            parse_case_id(case_id),
            notebook_parse_case_id(case_id),
        )
        self.assertEqual(parse_case_id(case_id)[3], "t1c_extra_text")

    def test_invalid_case_id_matches_notebook_error(self):
        with self.assertRaisesRegex(ValueError, "Cannot parse case_id"):
            parse_case_id("invalid")

    def test_raw_paths_match_notebook(self):
        raw_root = Path("/synthetic/MU-Glioma-Post")
        case_id = "PatientID_0008_T4_to_T6_t1c"
        self.assertEqual(
            get_raw_paths(case_id, raw_root),
            notebook_get_raw_paths(case_id, raw_root),
        )

    def test_ordering_and_silent_duplicate_removal_match_notebook(self):
        case_ids = [
            "PatientID_0053_T1_to_T3_t1c",
            "PatientID_0003_T1_to_T2_t1c",
            "PatientID_0053_T1_to_T3_t1c",
        ]
        notebook_result = sorted(set(case_ids))
        self.assertEqual(locked_case_ids(case_ids), notebook_result)

    def test_csv_locked_cohort_matches_notebook_expression(self):
        case_ids = [
            "PatientID_0053_T1_to_T3_t1c",
            "PatientID_0003_T1_to_T2_t1c",
            "PatientID_0053_T1_to_T3_t1c",
        ]
        with tempfile.TemporaryDirectory() as temporary_directory:
            csv_path = Path(temporary_directory) / "case_metrics.csv"
            with csv_path.open("w", newline="") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=["case_id", "dice"])
                writer.writeheader()
                for case_id in case_ids:
                    writer.writerow({"case_id": case_id, "dice": "0.5"})

            self.assertEqual(
                load_locked_case_ids(csv_path),
                sorted(set(case_ids)),
            )

    def test_missing_csv_raises_file_not_found(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            missing_path = Path(temporary_directory) / "missing.csv"
            with self.assertRaises(FileNotFoundError):
                load_locked_case_ids(missing_path)

    def test_missing_case_id_column_raises_key_error(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            csv_path = Path(temporary_directory) / "case_metrics.csv"
            csv_path.write_text("patient_id,dice\nPatientID_0003,0.5\n")
            with self.assertRaisesRegex(KeyError, "case_id"):
                load_locked_case_ids(csv_path)

    def test_empty_cohort_csv_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            csv_path = Path(temporary_directory) / "case_metrics.csv"
            csv_path.write_text("case_id,dice\n")
            self.assertEqual(load_locked_case_ids(csv_path), [])

    def test_validation_reports_present_and_missing_files(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            raw_root = Path(temporary_directory)
            paths = get_raw_paths(
                "PatientID_0003_T1_to_T2_t1c",
                raw_root,
            )
            for key in ("cur_img", "fut_img", "cur_mask"):
                path = paths[key]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()

            result = validate_raw_paths(paths)

            self.assertEqual(result, notebook_validate_raw_paths(paths))
            self.assertTrue(result["cur_img_exists"])
            self.assertTrue(result["fut_img_exists"])
            self.assertTrue(result["cur_mask_exists"])
            self.assertFalse(result["fut_mask_exists"])
            self.assertFalse(result["all_exists"])

    def test_fail_fast_uses_first_missing_file_and_exact_message(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            paths = get_raw_paths(
                "PatientID_0003_T1_to_T2_t1c",
                Path(temporary_directory),
            )
            expected = f"Missing cur_img: {paths['cur_img']}"
            with self.assertRaises(FileNotFoundError) as raised:
                require_raw_paths(paths)
            self.assertEqual(str(raised.exception), expected)

    def test_fail_fast_multiple_missing_files_preserves_notebook_order(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            paths = get_raw_paths(
                "PatientID_0003_T1_to_T2_t1c",
                Path(temporary_directory),
            )
            paths["cur_img"].parent.mkdir(parents=True, exist_ok=True)
            paths["cur_img"].touch()
            expected = f"Missing fut_img: {paths['fut_img']}"
            with self.assertRaises(FileNotFoundError) as raised:
                require_raw_paths(paths)
            self.assertEqual(str(raised.exception), expected)

    def test_fail_fast_returns_none_when_all_files_exist(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            paths = get_raw_paths(
                "PatientID_0003_T1_to_T2_t1c",
                Path(temporary_directory),
            )
            for key in ("cur_img", "fut_img", "cur_mask", "fut_mask"):
                paths[key].parent.mkdir(parents=True, exist_ok=True)
                paths[key].touch()
            self.assertIsNone(require_raw_paths(paths))

    @unittest.skipUnless(
        LOCKED_COHORT_CSV.exists() and LOCKED_COHORT_EXPECTED.exists(),
        "Canonical locked cohort fixture is unavailable; see fixture README.",
    )
    def test_canonical_locked_cohort(self):
        expected = LOCKED_COHORT_EXPECTED.read_text().splitlines()
        self.assertEqual(load_locked_case_ids(LOCKED_COHORT_CSV), expected)


if __name__ == "__main__":
    unittest.main()
