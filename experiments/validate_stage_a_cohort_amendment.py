#!/usr/bin/env python3
"""Bounded validation for the 115-to-113 Stage A cohort amendment."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs/pcc_115_stage_a_cohort_amendment_2026"
PROTOCOL = REPO / "outputs/pcc_115_holdout_protocol_lock_2026"
FROZEN = Path("/home/changxinjiresearch/pcc115_stage_a_complete_download_v3/pcc_115_holdout_stage_a_p0_freeze_2026")
EXCLUDED = {"PatientID_0113", "PatientID_0132"}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    original_case = rows(PROTOCOL / "01_COHORT_LOCK/LOCKED_115_CASE_MANIFEST.csv")
    original_p0 = rows(FROZEN / "06_P0_FREEZE_MANIFEST/LOCKED_115_P0_MANIFEST.csv")
    original_sha = rows(FROZEN / "06_P0_FREEZE_MANIFEST/LOCKED_115_P0_SHA256.csv")
    completion = rows(FROZEN / "06_P0_FREEZE_MANIFEST/LOCKED_115_P0_COMPLETION_STATUS.csv")
    amended = rows(OUT / "02_AMENDED_COHORT_LOCK/LOCKED_113_CONFIRMATORY_CASE_MANIFEST.csv")
    mapping = rows(OUT / "03_P0_MAPPING/LOCKED_113_P0_MAPPING_AUDIT.csv")
    excluded = rows(OUT / "02_AMENDED_COHORT_LOCK/EXCLUDED_POST_LOCK_CASES.csv")
    authority = rows(OUT / "00_AUTHORITY/AMENDMENT_AUTHORITY_FILES.csv")
    assert len(original_case) == 115 and len(original_p0) == 115 and len(original_sha) == 115 and len(completion) == 115
    assert len(amended) == 113 and len({r["patient_id"] for r in amended}) == 113 and len({r["case_id"] for r in amended}) == 113
    assert {r["patient_id"] for r in amended}.isdisjoint(EXCLUDED)
    assert {r["patient_id"] for r in original_case} - {r["patient_id"] for r in amended} == EXCLUDED
    assert len(excluded) == 2 and {r["patient_id"] for r in excluded} == EXCLUDED
    assert all(r["exclusion_code"] == "DATA_IDENTITY_OR_LABEL_ASSIGNMENT_ANOMALY" for r in excluded)
    assert all(r["performance_seen_before_exclusion"] == "false" and r["target_constructed_before_exclusion"] == "false" for r in excluded)
    assert all(r["p0_retained"] == "true" and r["original_manifest_retained"] == "true" for r in excluded)
    dev = {r["patient_id"] for r in rows(PROTOCOL / "01_COHORT_LOCK/LOCKED_40_PATIENT_IDS.csv")}
    assert not dev.intersection({r["patient_id"] for r in amended})
    assert len(mapping) == 113 and all(r["exists"] == "True" and r["hash_match"] == "True" and r["mapping_status"] == "PASS" for r in mapping)
    assert {r["patient_id"] for r in rows(OUT / "03_P0_MAPPING/EXCLUDED_P0_RETENTION_AUDIT.csv")} == EXCLUDED
    immutable = rows(OUT / "01_IMMUTABILITY_AUDIT/ORIGINAL_STAGE_A_IMMUTABILITY_AUDIT.csv")
    assert sum(r["artifact_type"] == "P0" for r in immutable) == 115
    assert sum(r["artifact_type"] == "COMPLETION_MARKER" for r in immutable) == 115
    assert all(r["unchanged"] == "True" for r in immutable)
    future = rows(REPO / "outputs/pcc_115_stage_a_duplicate_p0_audit_2026/DUPLICATE_PATIENT_FUTURE_IDENTITY_AUDIT.csv")
    assert len(future) == 8
    assert (OUT / "04_STAGE_B_HANDOFF_LOCK/LOCKED_STAGE_B_CONFIRMATORY_INPUT_POLICY.yaml").is_file()
    policy = (OUT / "04_STAGE_B_HANDOFF_LOCK/LOCKED_STAGE_B_CONFIRMATORY_INPUT_POLICY.yaml").read_text()
    assert "LOCKED_113_CONFIRMATORY_CASE_MANIFEST.csv" in policy and "PatientID_0113" in policy and "PatientID_0132" in policy
    status = json.loads((FROZEN / "10_STAGE_A_RELEASE/STAGE_A_STATUS.json").read_text())
    runtime = json.loads((FROZEN / "00_STAGE_A_AUTHORITY/GPU_RUNTIME_INFO.json").read_text())
    assert status["target_constructed"] is False and status["performance_computed"] is False and status["stage_b_executed"] is False and status["lumiere_started"] is False
    assert runtime["target_constructed"] is False and runtime["performance_computed"] is False and runtime["stage_b_executed"] is False
    assert not (FROZEN / "stage_b").exists()
    forbidden_result_names = [p.name.lower() for p in FROZEN.rglob("*") if p.is_file() and any(token in p.name.lower() for token in ("method_metrics", "correction_trajectory", "performance"))]
    assert not forbidden_result_names, forbidden_result_names
    source = (REPO / "experiments/stage_a_freeze_static_tests.py").read_text()
    assert "def _stage_b_artifacts" in source and "def test_21_no_stage_b_outputs(): assert not _stage_b_artifacts()" in source
    assert all(r["exists"] == "True" and r["readable"] == "True" for r in authority)
    print(json.dumps({"original_115": True, "amended_113": True, "excluded": sorted(EXCLUDED), "p0_mapping": "PASS", "immutable": "PASS", "stage_b_outputs": False, "target": False, "performance": False, "stage_b": False, "lumiere": False}, indent=2))


if __name__ == "__main__":
    main()
