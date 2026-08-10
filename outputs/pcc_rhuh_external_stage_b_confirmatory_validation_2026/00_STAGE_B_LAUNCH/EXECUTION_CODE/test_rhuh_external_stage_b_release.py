#!/usr/bin/env python3
"""Static and artifact tests for the sealed RHUH External Stage B release."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(
    os.environ.get(
        "RHUH_STAGE_B_OUTPUT_ROOT",
        ROOT / "outputs/pcc_rhuh_external_stage_b_confirmatory_validation_2026",
    )
)


def rows(relative: str) -> list[dict[str, str]]:
    with (OUT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def artifacts() -> dict[str, object]:
    case = rows("02_CASE_RESULTS/RHUH_STAGE_B_CASE_METHOD_METRICS.csv")
    trajectory = rows("03_TRAJECTORIES/RHUH_STAGE_B_FULL_PCC_ROUND_TRAJECTORY.csv")
    targets = rows("01_TARGET_AUDIT/RHUH_STAGE_B_TARGET_MANIFEST.csv")
    live = rows("00_STAGE_B_LAUNCH/RHUH_STAGE_B_LIVE_P0_VERIFICATION.csv")
    confirmatory = rows("06_CONFIRMATORY_STATISTICS/RHUH_STAGE_B_CONFIRMATORY_STATISTICS.csv")
    status = json.loads((OUT / "09_RELEASE/RHUH_EXTERNAL_STAGE_B_KERNEL_STATUS.json").read_text())
    return {"case": case, "trajectory": trajectory, "targets": targets, "live": live, "confirmatory": confirmatory, "status": status}


def test_01_stage_a_authority_sha_locked() -> None:
    assert (ROOT / "PCC_RHUH_EXTERNAL_STAGE_A_P0_FREEZE_2026.zip.sha256").read_text().split()[0] == "2f55124706107ba5e584883aab8f4d8f5aec4283d4470248d4aacce60f3413f3"


def test_02_live_p0_rows(artifacts: dict[str, object]) -> None:
    assert len(artifacts["live"]) == 39


def test_03_live_p0_hashes(artifacts: dict[str, object]) -> None:
    assert all(row["sha256_match"] == "True" for row in artifacts["live"])


def test_04_live_p0_dtype(artifacts: dict[str, object]) -> None:
    assert all(row["dtype_valid"] == "True" for row in artifacts["live"])


def test_05_live_p0_shape(artifacts: dict[str, object]) -> None:
    assert all(row["shape_valid"] == "True" for row in artifacts["live"])


def test_06_live_p0_numeric_contract(artifacts: dict[str, object]) -> None:
    assert all(row["finite"] == "True" and row["range_valid"] == "True" for row in artifacts["live"])


def test_07_cohort_39(artifacts: dict[str, object]) -> None:
    assert len({row["patient_id"] for row in artifacts["case"]}) == 39


def test_08_unique_cases_39(artifacts: dict[str, object]) -> None:
    assert len({row["case_id"] for row in artifacts["case"]}) == 39


def test_09_rhuh_0008_absent(artifacts: dict[str, object]) -> None:
    assert all(row["patient_id"] != "RHUH-0008" for row in artifacts["case"])


def test_10_target_rows_39(artifacts: dict[str, object]) -> None:
    assert len(artifacts["targets"]) == 39


def test_11_target_bool(artifacts: dict[str, object]) -> None:
    assert all(row["target_dtype"] == "bool" for row in artifacts["targets"])


def test_12_target_success_39(artifacts: dict[str, object]) -> None:
    assert all(row["construction_status"] == "PASS" for row in artifacts["targets"])


def test_13_case_method_rows_273(artifacts: dict[str, object]) -> None:
    assert len(artifacts["case"]) == 273


def test_14_methods_exactly_7(artifacts: dict[str, object]) -> None:
    assert {row["method"] for row in artifacts["case"]} == {"Fixed", "Naive", "EIA-linear", "EIA-blend-0.90", "EIA-blend-0.75", "Full PCC", "No-smoothing PCC"}


def test_15_each_case_has_7_methods(artifacts: dict[str, object]) -> None:
    counts: dict[str, int] = {}
    for row in artifacts["case"]:
        counts[row["case_id"]] = counts.get(row["case_id"], 0) + 1
    assert set(counts.values()) == {7}


def test_16_numeric_status_pass(artifacts: dict[str, object]) -> None:
    assert all(row["numeric_status"] == "PASS" for row in artifacts["case"])


def test_17_threshold_fixed() -> None:
    text = (ROOT / "outputs/pcc_rhuh_external_protocol_lock_2026/06_STAGE_B_LOCK/LOCKED_RHUH_EXTERNAL_EVALUATION_POLICY.yaml").read_text()
    assert "probability >= 0.5" in text and "FORBIDDEN" in text


def test_18_target_formula_locked() -> None:
    text = (ROOT / "outputs/pcc_rhuh_external_protocol_lock_2026/06_STAGE_B_LOCK/LOCKED_RHUH_EXTERNAL_STAGE_B_PROTOCOL.yaml").read_text()
    assert "future_mask > 0" in text and "NOT(current_mask > 0)" in text


def test_19_trajectory_rows_390(artifacts: dict[str, object]) -> None:
    assert len(artifacts["trajectory"]) == 390


def test_20_rounds_1_to_10(artifacts: dict[str, object]) -> None:
    assert {int(row["round"]) for row in artifacts["trajectory"]} == set(range(1, 11))


def test_21_p10_formal_final(artifacts: dict[str, object]) -> None:
    assert all((row["P10_formal_final"] == "True") == (row["round"] == "10") for row in artifacts["trajectory"])


def test_22_trajectory_numeric_pass(artifacts: dict[str, object]) -> None:
    assert all(row["numeric_status"] == "PASS" for row in artifacts["trajectory"])


def test_23_confirmatory_family_two(artifacts: dict[str, object]) -> None:
    assert len(artifacts["confirmatory"]) == 2


def test_24_confirmatory_labels(artifacts: dict[str, object]) -> None:
    assert [row["comparison"] for row in artifacts["confirmatory"]] == ["Full PCC vs Fixed", "No-smoothing PCC vs Full PCC"]


def test_25_wilcoxon_available(artifacts: dict[str, object]) -> None:
    assert all(row["wilcoxon_status"] in {"AVAILABLE", "ALL_ZERO"} for row in artifacts["confirmatory"])


def test_26_holm_values_valid(artifacts: dict[str, object]) -> None:
    assert all(0 <= float(row["holm_adjusted_p"]) <= 1 for row in artifacts["confirmatory"])


def test_27_bootstrap_10000(artifacts: dict[str, object]) -> None:
    assert all(row["bootstrap_replicates"] == "10000" for row in artifacts["confirmatory"])


def test_28_bootstrap_seed(artifacts: dict[str, object]) -> None:
    assert all(row["bootstrap_seed"] == "20260810" for row in artifacts["confirmatory"])


def test_29_topk_oracle_label(artifacts: dict[str, object]) -> None:
    assert all(row["oracle_assisted_label"] == "ORACLE_ASSISTED_RETROSPECTIVE_LOCALIZATION" for row in artifacts["case"])


def test_30_no_failures() -> None:
    assert len(rows("04_FAILURE_ANALYSIS/RHUH_STAGE_B_FAILURE_REPORT.csv")) == 0


def test_31_p0_not_regenerated(artifacts: dict[str, object]) -> None:
    assert artifacts["status"]["P0_regenerated"] is False


def test_32_no_training(artifacts: dict[str, object]) -> None:
    runtime = json.loads((OUT / "09_RELEASE/RHUH_EXTERNAL_STAGE_B_KERNEL_RUNTIME.json").read_text())
    assert runtime["training"] is False and runtime["fine_tuning"] is False


def test_33_no_result_driven_config_change(artifacts: dict[str, object]) -> None:
    assert artifacts["status"]["post_outcome_scientific_config_changes"] == 0


def test_34_first_outcome_access_record() -> None:
    record = json.loads((OUT / "00_STAGE_B_LAUNCH/RHUH_STAGE_B_FIRST_OUTCOME_ACCESS.json").read_text())
    assert record["P0_live_verification"] == "PASS" and record["SCIENCE_CONFIG_FROZEN"] is True


def test_35_lumiere_false(artifacts: dict[str, object]) -> None:
    assert artifacts["status"]["LUMIERE"] is False


def test_36_kernel_release_gate(artifacts: dict[str, object]) -> None:
    assert artifacts["status"]["RHUH_EXTERNAL_STAGE_B_RELEASE_GATE"] == "PASS"
