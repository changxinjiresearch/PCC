"""Static/evidence tests for the frozen RHUH External Stage A release.

These tests never load RHUH imaging arrays or P0 arrays. They validate the
immutable evidence produced by the authorized current-only inference run.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/pcc_rhuh_external_stage_a_p0_freeze_2026"
PROTOCOL_COMMIT = "6c8bf164f8e445123143db08c34f0f66a1e21226"
PROTOCOL_ZIP_SHA256 = "2ac4378b279854a5497185176e9cd776da8207aab04dd4617cb310080fbad059"
PREPROCESSING_SHA256 = "bf48893deabbb400e6f412b9a53267e55ecb538a4f57daa682ed1350bc2b5624"
ARCHITECTURE_SHA256 = "abce63dc26f6642438540ca80c8f80b992a0a39a39b88a17966dd65806915d08"
FORWARD_SHA256 = "15ca3edd60fb984d0b3bc35bdeaaaf70edf32c246fe006b44fd2d3f0f451a98c"


def rows(relative: str) -> list[dict[str, str]]:
    with (OUT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def runtime() -> dict[str, object]:
    return json.loads((OUT / "00_AUTHORITY/KAGGLE_RUNTIME_INFO.json").read_text())


def validation() -> list[dict[str, str]]:
    return rows("07_TESTS/LOCAL_P0_FILE_VALIDATION.csv")


def test_01_protocol_zip_sha_match() -> None:
    assert hashlib.sha256((ROOT / "PCC_RHUH_EXTERNAL_PROTOCOL_LOCK_2026.zip").read_bytes()).hexdigest() == PROTOCOL_ZIP_SHA256


def test_02_pre_outcome_commit_match() -> None:
    result = subprocess.run(["git", "cat-file", "-t", PROTOCOL_COMMIT], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0 and result.stdout.strip() == "commit"


def test_03_cohort_is_39() -> None:
    manifest = rows("01_CURRENT_ONLY_DATASET/LOCKED_RHUH_39_STAGE_A_CURRENT_ONLY_MANIFEST.csv")
    assert len(manifest) == len({row["patient_id"] for row in manifest}) == 39


def test_04_rhuh_0008_absent() -> None:
    assert all(row["patient_id"] != "RHUH-0008" for row in rows("01_CURRENT_ONLY_DATASET/LOCKED_RHUH_39_STAGE_A_CURRENT_ONLY_MANIFEST.csv"))


def test_05_current_t1ce_count_39() -> None:
    assert sum(row["file_type"] == "CURRENT_T1CE" for row in rows("01_CURRENT_ONLY_DATASET/RHUH_STAGE_A_REMOTE_CURRENT_FILE_AUDIT.csv")) == 39


def test_06_current_segmentation_count_39() -> None:
    assert sum(row["file_type"] == "CURRENT_SEGMENTATION" for row in rows("01_CURRENT_ONLY_DATASET/RHUH_STAGE_A_REMOTE_CURRENT_FILE_AUDIT.csv")) == 39


def test_07_no_recurrence_image_in_dataset() -> None:
    audit = rows("01_CURRENT_ONLY_DATASET/RHUH_STAGE_A_REMOTE_CURRENT_FILE_AUDIT.csv")
    assert not any("recurrence" in row["resolved_path"].lower() and row["file_type"] == "CURRENT_T1CE" for row in audit)


def test_08_no_recurrence_segmentation_in_dataset() -> None:
    audit = rows("01_CURRENT_ONLY_DATASET/RHUH_STAGE_A_REMOTE_CURRENT_FILE_AUDIT.csv")
    assert not any("recurrence" in row["resolved_path"].lower() and row["file_type"] == "CURRENT_SEGMENTATION" for row in audit)


def test_09_current_t1ce_source_hashes_match() -> None:
    assert all(row["hash_status"] == "MATCH" for row in rows("01_CURRENT_ONLY_DATASET/RHUH_STAGE_A_REMOTE_CURRENT_FILE_AUDIT.csv") if row["file_type"] == "CURRENT_T1CE")


def test_10_current_segmentation_source_hashes_match() -> None:
    assert all(row["hash_status"] == "MATCH" for row in rows("01_CURRENT_ONLY_DATASET/RHUH_STAGE_A_REMOTE_CURRENT_FILE_AUDIT.csv") if row["file_type"] == "CURRENT_SEGMENTATION")


def test_11_checkpoint_count_5() -> None:
    assert len(rows("02_PREDICTOR_AUTHORITY/LOCKED_RHUH_FROZEN_PREDICTOR_RUNTIME_MANIFEST.csv")) == 5


def test_12_checkpoint_hashes_match() -> None:
    assert all(row["hash_status"] == "MATCH" for row in rows("02_PREDICTOR_AUTHORITY/LOCKED_RHUH_FROZEN_PREDICTOR_RUNTIME_MANIFEST.csv"))


def test_13_preprocessing_hash_match() -> None:
    assert {row["preprocessing_sha256"] for row in rows("05_P0_FREEZE/LOCKED_RHUH_39_EXTERNAL_P0_MANIFEST.csv")} == {PREPROCESSING_SHA256}


def test_14_architecture_hash_match() -> None:
    assert {row["architecture_sha256"] for row in rows("05_P0_FREEZE/LOCKED_RHUH_39_EXTERNAL_P0_MANIFEST.csv")} == {ARCHITECTURE_SHA256}


def test_15_forward_implementation_hash_match() -> None:
    assert {row["forward_code_sha256"] for row in rows("05_P0_FREEZE/LOCKED_RHUH_39_EXTERNAL_P0_MANIFEST.csv")} == {FORWARD_SHA256}


def test_16_no_training() -> None:
    assert runtime()["training"] is False


def test_17_no_backward() -> None:
    assert runtime()["backward"] is False


def test_18_no_fine_tuning() -> None:
    assert runtime()["fine_tuning"] is False


def test_19_no_calibration() -> None:
    assert runtime()["calibration"] is False


def test_20_no_tta() -> None:
    assert runtime()["test_time_adaptation"] is False


def test_21_p0_count_39() -> None:
    assert len(validation()) == 39 and all(row["exists"] == "True" for row in validation())


def test_22_p0_unique_cases_39() -> None:
    assert len({row["case_id"] for row in validation()}) == 39


def test_23_p0_dtype_float32() -> None:
    assert all(row["dtype_valid"] == "True" for row in validation())


def test_24_p0_finite_39() -> None:
    assert all(row["finite"] == "True" for row in validation())


def test_25_p0_range_valid_39() -> None:
    assert all(row["range_valid"] == "True" for row in validation())


def test_26_p0_shape_valid_39() -> None:
    assert all(row["shape_valid"] == "True" for row in validation())


def test_27_completion_markers_39() -> None:
    assert len(rows("05_P0_FREEZE/LOCKED_RHUH_39_EXTERNAL_P0_COMPLETION_STATUS.csv")) == 39 and all(row["completion_marker_exists"] == "True" for row in validation())


def test_28_p0_sha_records_39_and_match() -> None:
    assert len(rows("05_P0_FREEZE/LOCKED_RHUH_39_EXTERNAL_P0_SHA256.csv")) == 39 and all(row["manifest_hash_match"] == "True" and row["sha_table_hash_match"] == "True" for row in validation())


def test_29_future_segmentation_voxel_access_zero() -> None:
    assert runtime()["future_segmentation_voxel_access"] == 0


def test_30_recurrence_t1ce_voxel_access_zero() -> None:
    assert runtime()["recurrence_t1ce_voxel_access"] == 0


def test_31_target_not_constructed() -> None:
    assert runtime()["target_constructed"] is False


def test_32_performance_not_computed() -> None:
    assert runtime()["performance_computed"] is False


def test_33_stage_b_not_executed() -> None:
    assert runtime()["stage_b_executed"] is False
