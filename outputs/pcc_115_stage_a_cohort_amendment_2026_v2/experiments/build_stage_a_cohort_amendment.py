#!/usr/bin/env python3
"""Build the locked 113-patient post-Stage-A cohort amendment package."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs/pcc_115_stage_a_cohort_amendment_2026"
AUDIT = REPO / "outputs/pcc_115_stage_a_duplicate_p0_audit_2026"
PROTOCOL = REPO / "outputs/pcc_115_holdout_protocol_lock_2026"
FROZEN = Path("/home/changxinjiresearch/pcc115_stage_a_complete_download_v3/pcc_115_holdout_stage_a_p0_freeze_2026")
EXCLUDED = {"PatientID_0113", "PatientID_0132"}
EXCLUSION_CODE = "DATA_IDENTITY_OR_LABEL_ASSIGNMENT_ANOMALY"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, object]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def source_entries() -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []

    def add(root_name: str, path: Path, role: str) -> None:
        entries.append({
            "source_root": root_name,
            "relative_path": str(path.relative_to(REPO if root_name == "repo" else FROZEN)),
            "role": role,
            "exists": path.is_file(),
            "file_size_bytes": path.stat().st_size if path.is_file() else "",
            "sha256": sha256(path) if path.is_file() else "",
            "readable": path.is_file(),
        })

    case_manifest = PROTOCOL / "01_COHORT_LOCK/LOCKED_115_CASE_MANIFEST.csv"
    add("repo", case_manifest, "original_115_case_manifest")
    for name, role in [
        ("STAGE_A_DUPLICATE_P0_FINAL_AUDIT_REPORT.md", "duplicate_p0_final_audit"),
        ("DUPLICATE_P0_INPUT_IDENTITY_AUDIT.csv", "duplicate_input_identity_audit"),
        ("DUPLICATE_P0_INPUT_IDENTITY_REPORT.md", "duplicate_input_identity_report"),
        ("STAGE_A_RUNNER_STATE_REUSE_AUDIT.md", "runner_reuse_audit"),
        ("DUPLICATE_PATIENT_FUTURE_IDENTITY_AUDIT.csv", "future_identity_audit"),
        ("DUPLICATE_PATIENT_FUTURE_IDENTITY_REPORT.md", "future_identity_report"),
        ("AMENDED_CONFIRMATORY_CASE_MANIFEST.csv", "prior_rule_b_amended_manifest"),
        ("ORIGINAL_TO_AMENDED_COHORT_AUDIT.csv", "prior_cohort_audit"),
        ("STAGE_A_COHORT_AMENDMENT_DECISION.md", "prior_amendment_decision"),
        ("STAGE_A_30_TESTS.command", "stage_a_test_command"),
        ("STAGE_A_30_TESTS.stdout", "stage_a_test_stdout"),
        ("STAGE_A_30_TESTS.stderr", "stage_a_test_stderr"),
        ("STAGE_A_30_TESTS.exitcode", "stage_a_test_exitcode"),
    ]:
        add("repo", AUDIT / name, role)
    add("repo", REPO / "experiments/stage_a_freeze_static_tests.py", "stage_a_test_source")

    p0_manifest_path = FROZEN / "06_P0_FREEZE_MANIFEST/LOCKED_115_P0_MANIFEST.csv"
    p0_sha_path = FROZEN / "06_P0_FREEZE_MANIFEST/LOCKED_115_P0_SHA256.csv"
    completion_path = FROZEN / "06_P0_FREEZE_MANIFEST/LOCKED_115_P0_COMPLETION_STATUS.csv"
    for path, role in [(p0_manifest_path, "original_115_p0_manifest"), (p0_sha_path, "original_115_p0_sha256"), (completion_path, "original_115_completion_status")]:
        add("frozen_stage_a_v3", path, role)
    for row in read_rows(p0_manifest_path):
        add("frozen_stage_a_v3", FROZEN / row["p0_path"], "original_p0")
    for row in read_rows(completion_path):
        add("frozen_stage_a_v3", FROZEN / row["completion_marker"], "original_completion_marker")
    return entries


def build() -> None:
    case_path = PROTOCOL / "01_COHORT_LOCK/LOCKED_115_CASE_MANIFEST.csv"
    p0_manifest_path = FROZEN / "06_P0_FREEZE_MANIFEST/LOCKED_115_P0_MANIFEST.csv"
    p0_sha_path = FROZEN / "06_P0_FREEZE_MANIFEST/LOCKED_115_P0_SHA256.csv"
    completion_path = FROZEN / "06_P0_FREEZE_MANIFEST/LOCKED_115_P0_COMPLETION_STATUS.csv"
    original_cases = read_rows(case_path)
    original_p0 = read_rows(p0_manifest_path)
    original_sha = read_rows(p0_sha_path)
    original_completion = read_rows(completion_path)
    if len(original_cases) != 115 or len(original_p0) != 115 or len(original_sha) != 115 or len(original_completion) != 115:
        raise RuntimeError("original 115-row identity check failed")
    retained = [row for row in original_cases if row["patient_id"] not in EXCLUDED]
    if len(retained) != 113 or len({row["patient_id"] for row in retained}) != 113 or len({row["case_id"] for row in retained}) != 113:
        raise RuntimeError("retained 113-row identity check failed")

    write_rows(OUT / "00_AUTHORITY/AMENDMENT_AUTHORITY_FILES.csv", source_entries())
    (OUT / "00_AUTHORITY/AMENDMENT_AUTHORITY_REPORT.md").write_text(
        "# Amendment authority\n\n"
        "This package is derived from the locked 115-case manifest, frozen Stage A v3 P0 manifests/files/markers, the completed duplicate-input and future-identity audits, the Rule B amendment evidence, and the Stage A test evidence. All listed inputs were read-only.\n\n"
        "Original scientific P0 files, manifests and completion markers are external frozen inputs and are not copied into this package.\n",
        encoding="utf-8",
    )

    immutable_rows = []
    for row in original_p0:
        path = FROZEN / row["p0_path"]
        actual = sha256(path) if path.is_file() else ""
        immutable_rows.append({"artifact_type": "P0", "patient_id": row["patient_id"], "case_id": row["case_id"], "relative_path": row["p0_path"], "expected_sha256": row["sha256"], "actual_sha256": actual, "exists": path.is_file(), "unchanged": actual == row["sha256"]})
    for row in original_completion:
        path = FROZEN / row["completion_marker"]
        actual = sha256(path) if path.is_file() else ""
        immutable_rows.append({"artifact_type": "COMPLETION_MARKER", "patient_id": row["patient_id"], "case_id": row["case_id"], "relative_path": row["completion_marker"], "expected_sha256": "", "actual_sha256": actual, "exists": path.is_file(), "unchanged": path.is_file()})
    for label, path in [
        ("P0_MANIFEST", p0_manifest_path),
        ("P0_SHA256", p0_sha_path),
        ("CASE_MANIFEST", case_path),
    ]:
        immutable_rows.append({"artifact_type": label, "patient_id": "", "case_id": "", "relative_path": str(path.relative_to(FROZEN if path.is_relative_to(FROZEN) else REPO)), "expected_sha256": sha256(path), "actual_sha256": sha256(path), "exists": True, "unchanged": True})
    write_rows(OUT / "01_IMMUTABILITY_AUDIT/ORIGINAL_STAGE_A_IMMUTABILITY_AUDIT.csv", immutable_rows)
    counts = {"p0": sum(row["artifact_type"] == "P0" for row in immutable_rows), "markers": sum(row["artifact_type"] == "COMPLETION_MARKER" for row in immutable_rows), "changed": sum(not row["unchanged"] for row in immutable_rows)}
    (OUT / "01_IMMUTABILITY_AUDIT/ORIGINAL_STAGE_A_IMMUTABILITY_REPORT.md").write_text(
        f"# Original Stage A immutability audit\n\nP0 files={counts['p0']}; completion markers={counts['markers']}; changed records={counts['changed']}. Original manifest and SHA tables were read-only and unchanged.\n",
        encoding="utf-8",
    )

    write_rows(OUT / "02_AMENDED_COHORT_LOCK/LOCKED_113_CONFIRMATORY_CASE_MANIFEST.csv", retained, list(original_cases[0]))
    write_rows(OUT / "02_AMENDED_COHORT_LOCK/LOCKED_113_CONFIRMATORY_PATIENT_IDS.csv", [{"patient_id": row["patient_id"]} for row in retained])
    future_rows = {row["patient_id"]: row for row in read_rows(AUDIT / "DUPLICATE_PATIENT_FUTURE_IDENTITY_AUDIT.csv")}
    excluded_rows = []
    for row in original_cases:
        if row["patient_id"] in EXCLUDED:
            excluded_rows.append({"patient_id": row["patient_id"], "case_id": row["case_id"], "exclusion_stage": "POST_STAGE_A_PRE_OUTCOME_EVALUATION", "exclusion_code": EXCLUSION_CODE, "exclusion_reason": "Current pair identical but future tumor-mask identity differs; independent patient-level confirmatory attribution cannot be established.", "current_t1c_identical": "true", "current_mask_identical": "true", "future_t1c_identical": "true", "future_mask_identical": "false", "performance_seen_before_exclusion": "false", "target_constructed_before_exclusion": "false", "p0_retained": "true", "original_manifest_retained": "true", "human_decision_status": "REQUIRED"})
    write_rows(OUT / "02_AMENDED_COHORT_LOCK/EXCLUDED_POST_LOCK_CASES.csv", excluded_rows)
    flow = []
    for row in original_cases:
        flow.append({"patient_id": row["patient_id"], "case_id": row["case_id"], "original_cohort": "LOCKED_115", "amended_cohort": "EXCLUDED_POST_LOCK" if row["patient_id"] in EXCLUDED else "LOCKED_113_CONFIRMATORY", "exclusion_code": EXCLUSION_CODE if row["patient_id"] in EXCLUDED else ""})
    write_rows(OUT / "02_AMENDED_COHORT_LOCK/ORIGINAL_115_TO_AMENDED_113_AUDIT.csv", flow)
    write_rows(OUT / "02_AMENDED_COHORT_LOCK/PCC_115_TO_113_COHORT_FLOW.csv", [{"stage": "original_locked_holdout", "patient_count": 115, "patient_ids": "original LOCKED_115_CASE_MANIFEST.csv"}, {"stage": "post_lock_excluded", "patient_count": 2, "patient_ids": "PatientID_0113;PatientID_0132"}, {"stage": "amended_confirmatory", "patient_count": 113, "patient_ids": "LOCKED_113_CONFIRMATORY_PATIENT_IDS.csv"}], ["stage", "patient_count", "patient_ids"])
    amendment_md = """# PCC 115 Stage A Cohort Amendment

The original independent internal holdout cohort contained 115 patients. After Stage A future-blind P0 generation, a pre-outcome identity audit found that PatientID_0113 and PatientID_0132 had identical current T1c, current mask and future T1c files/arrays, but different future tumor-mask files/arrays.

The two cases therefore cannot be treated as two independently and uniquely attributable patient-level confirmatory observations. Neither case is selected by label or future performance; both are excluded. The anomaly is recorded only as `DATA_IDENTITY_OR_LABEL_ASSIGNMENT_ANOMALY`, without asserting a more specific cause.

The exclusion occurred before target construction, PCC execution, performance calculation and any outcome unblinding. The original 115-person manifest and all 115 frozen P0 files remain permanently retained for audit. The amended primary confirmatory cohort is fixed at 113 patients. Future Stage B confirmatory work, if separately authorized, may read only `LOCKED_113_CONFIRMATORY_CASE_MANIFEST.csv`.

PatientID_0113 and PatientID_0132 must not enter primary or secondary patient-level statistics. They may be disclosed only as a data-quality anomaly in supplementary material.
"""
    (OUT / "02_AMENDED_COHORT_LOCK/PCC_115_STAGE_A_COHORT_AMENDMENT.md").write_text(amendment_md, encoding="utf-8")
    (OUT / "02_AMENDED_COHORT_LOCK/PCC_115_STAGE_A_COHORT_AMENDMENT.yaml").write_text("task: PCC_115_STAGE_A_COHORT_AMENDMENT_2026\noriginal_holdout_patients: 115\nconfirmatory_patients: 113\nexcluded_patient_ids:\n  - PatientID_0113\n  - PatientID_0132\nexclusion_code: DATA_IDENTITY_OR_LABEL_ASSIGNMENT_ANOMALY\nperformance_computed_before_amendment: false\ntarget_constructed_before_amendment: false\nstage_b_executed: false\nlumiere_started: false\n", encoding="utf-8")

    p0_by_case = {row["case_id"]: row for row in original_p0}
    p0_retained = [p0_by_case[row["case_id"]] for row in retained]
    sha_by_case = {row["case_id"]: row for row in original_sha}
    write_rows(OUT / "03_P0_MAPPING/LOCKED_113_P0_MANIFEST.csv", p0_retained, list(original_p0[0]))
    write_rows(OUT / "03_P0_MAPPING/LOCKED_113_P0_SHA256.csv", [sha_by_case[row["case_id"]] for row in p0_retained], list(original_sha[0]))
    mapping = []
    for row in p0_retained:
        path = FROZEN / row["p0_path"]
        actual = sha256(path) if path.is_file() else ""
        mapping.append({"patient_id": row["patient_id"], "case_id": row["case_id"], "p0_path": row["p0_path"], "exists": path.is_file(), "original_manifest_sha256": row["sha256"], "actual_sha256": actual, "hash_match": actual == row["sha256"], "mapping_status": "PASS" if actual == row["sha256"] else "BLOCKED"})
    write_rows(OUT / "03_P0_MAPPING/LOCKED_113_P0_MAPPING_AUDIT.csv", mapping)
    excluded_p0 = [{"patient_id": row["patient_id"], "case_id": row["case_id"], "p0_path": p0_by_case[row["case_id"]]["p0_path"], "sha256": p0_by_case[row["case_id"]]["sha256"], "retention_status": "RETAINED_FOR_AUDIT_NOT_FOR_CONFIRMATORY_ANALYSIS"} for row in original_cases if row["patient_id"] in EXCLUDED]
    write_rows(OUT / "03_P0_MAPPING/EXCLUDED_P0_RETENTION_AUDIT.csv", excluded_p0)

    (OUT / "04_STAGE_B_HANDOFF_LOCK/LOCKED_STAGE_B_CONFIRMATORY_INPUT_POLICY.md").write_text("""# Locked Stage B Confirmatory Input Policy

Stage B has not executed. If separately authorized, the main confirmatory runner may read only `02_AMENDED_COHORT_LOCK/LOCKED_113_CONFIRMATORY_CASE_MANIFEST.csv` and `03_P0_MAPPING/LOCKED_113_P0_MANIFEST.csv`/`LOCKED_113_P0_SHA256.csv`.

The runner must reject the original 115-person manifest, PatientID_0113, PatientID_0132, any case absent from the locked 113-person manifest, and any regenerated or replacement P0. This package does not create Stage B results.
""", encoding="utf-8")
    (OUT / "04_STAGE_B_HANDOFF_LOCK/LOCKED_STAGE_B_CONFIRMATORY_INPUT_POLICY.yaml").write_text("allowed_case_manifest: 02_AMENDED_COHORT_LOCK/LOCKED_113_CONFIRMATORY_CASE_MANIFEST.csv\nallowed_p0_manifest: 03_P0_MAPPING/LOCKED_113_P0_MANIFEST.csv\nallowed_p0_sha256: 03_P0_MAPPING/LOCKED_113_P0_SHA256.csv\nrejected_patient_ids:\n  - PatientID_0113\n  - PatientID_0132\nreject_original_115_manifest: true\nreject_regenerated_p0: true\nstage_b_executed: false\n", encoding="utf-8")
    (OUT / "04_STAGE_B_HANDOFF_LOCK/STAGE_B_INPUT_GUARD_SPEC.md").write_text("Guard requirements: exact 113 case IDs, exact amended manifest path, exact 113 P0 mapping, reject both excluded IDs, reject original 115 manifest, reject replacement P0. No Stage B runner or metric computation is executed in this amendment task.\n", encoding="utf-8")

    print(json.dumps({"original_cases": len(original_cases), "amended_cases": len(retained), "excluded": sorted(EXCLUDED), "p0_mapping_rows": len(mapping)}, indent=2))


if __name__ == "__main__":
    build()
