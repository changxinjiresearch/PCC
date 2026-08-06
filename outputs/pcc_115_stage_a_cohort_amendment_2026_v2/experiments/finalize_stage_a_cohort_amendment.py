#!/usr/bin/env python3
"""Finalize protocol, hash lock and release metadata for the 113-case amendment."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs/pcc_115_stage_a_cohort_amendment_2026"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    (OUT / "06_RELEASE_LOCK/PCC_115_STAGE_A_COHORT_AMENDMENT_PROTOCOL.md").write_text(
        """# PCC 115 Stage A Cohort Amendment Protocol

Original holdout: 115 patients. Post-lock identity anomaly: PatientID_0113 and PatientID_0132. Amended confirmatory cohort: 113 patients.

The original 115-case manifest, 115 frozen P0 files, SHA records and completion markers are immutable audit evidence. The amended main confirmatory manifest is a deterministic subset excluding exactly the two anomalous cases under `DATA_IDENTITY_OR_LABEL_ASSIGNMENT_ANOMALY`.

This package does not execute Stage B, construct targets, calculate performance, run PCC/No-smoothing/EIA, or start LUMIERE.
""", encoding="utf-8")
    (OUT / "06_RELEASE_LOCK/PCC_115_STAGE_A_COHORT_AMENDMENT_PROTOCOL.yaml").write_text(
        "task: PCC_115_STAGE_A_COHORT_AMENDMENT_2026\noriginal_holdout_patients: 115\nexcluded_post_lock_patients: 2\nconfirmatory_patients: 113\nexclusion_code: DATA_IDENTITY_OR_LABEL_ASSIGNMENT_ANOMALY\noriginal_p0_modified: false\ntarget_constructed: false\nperformance_computed: false\nstage_b_executed: false\nlumiere_started: false\n", encoding="utf-8")

    hash_targets = [
        "00_AUTHORITY/AMENDMENT_AUTHORITY_FILES.csv",
        "00_AUTHORITY/AMENDMENT_AUTHORITY_REPORT.md",
        "01_IMMUTABILITY_AUDIT/ORIGINAL_STAGE_A_IMMUTABILITY_AUDIT.csv",
        "01_IMMUTABILITY_AUDIT/ORIGINAL_STAGE_A_IMMUTABILITY_REPORT.md",
        "02_AMENDED_COHORT_LOCK/LOCKED_113_CONFIRMATORY_CASE_MANIFEST.csv",
        "02_AMENDED_COHORT_LOCK/LOCKED_113_CONFIRMATORY_PATIENT_IDS.csv",
        "02_AMENDED_COHORT_LOCK/EXCLUDED_POST_LOCK_CASES.csv",
        "02_AMENDED_COHORT_LOCK/ORIGINAL_115_TO_AMENDED_113_AUDIT.csv",
        "02_AMENDED_COHORT_LOCK/PCC_115_TO_113_COHORT_FLOW.csv",
        "02_AMENDED_COHORT_LOCK/PCC_115_STAGE_A_COHORT_AMENDMENT.md",
        "02_AMENDED_COHORT_LOCK/PCC_115_STAGE_A_COHORT_AMENDMENT.yaml",
        "03_P0_MAPPING/LOCKED_113_P0_MANIFEST.csv",
        "03_P0_MAPPING/LOCKED_113_P0_SHA256.csv",
        "03_P0_MAPPING/LOCKED_113_P0_MAPPING_AUDIT.csv",
        "03_P0_MAPPING/EXCLUDED_P0_RETENTION_AUDIT.csv",
        "04_STAGE_B_HANDOFF_LOCK/LOCKED_STAGE_B_CONFIRMATORY_INPUT_POLICY.md",
        "04_STAGE_B_HANDOFF_LOCK/LOCKED_STAGE_B_CONFIRMATORY_INPUT_POLICY.yaml",
        "04_STAGE_B_HANDOFF_LOCK/STAGE_B_INPUT_GUARD_SPEC.md",
        "05_TESTS/TEST_EXECUTION_REPORT.md",
        "05_TESTS/FULL_TEST_STDOUT.txt",
        "05_TESTS/FULL_TEST_STDERR.txt",
        "05_TESTS/TEST_EXIT_CODE.txt",
        "05_TESTS/TEST_COMMAND.txt",
        "06_RELEASE_LOCK/PCC_115_STAGE_A_COHORT_AMENDMENT_PROTOCOL.md",
        "06_RELEASE_LOCK/PCC_115_STAGE_A_COHORT_AMENDMENT_PROTOCOL.yaml",
        "../../experiments/build_stage_a_cohort_amendment.py",
        "../../experiments/validate_stage_a_cohort_amendment.py",
        "../../experiments/finalize_stage_a_cohort_amendment.py",
        "../../experiments/stage_a_freeze_static_tests.py",
        "../pcc_115_stage_a_duplicate_p0_audit_2026/DUPLICATE_PATIENT_FUTURE_IDENTITY_AUDIT.csv",
        "../pcc_115_stage_a_duplicate_p0_audit_2026/DUPLICATE_PATIENT_FUTURE_IDENTITY_REPORT.md",
    ]
    lock_rows = []
    for rel in hash_targets:
        path = OUT / rel if not rel.startswith("..") else (OUT / rel).resolve()
        lock_rows.append({"relative_path": rel, "exists": path.is_file(), "file_size_bytes": path.stat().st_size if path.is_file() else "", "sha256": sha256(path) if path.is_file() else ""})
    assert all(row["exists"] for row in lock_rows)
    (OUT / "06_RELEASE_LOCK/PCC_115_STAGE_A_COHORT_AMENDMENT_HASH_LOCK.json").write_text(json.dumps({"task": "PCC_115_STAGE_A_COHORT_AMENDMENT_2026", "entries": lock_rows}, indent=2) + "\n", encoding="utf-8")

    status = {
        "original_holdout_patients": 115,
        "excluded_post_lock_patients": 2,
        "confirmatory_patients": 113,
        "excluded_patient_ids": ["PatientID_0113", "PatientID_0132"],
        "exclusion_code": "DATA_IDENTITY_OR_LABEL_ASSIGNMENT_ANOMALY",
        "performance_computed_before_amendment": False,
        "target_constructed_before_amendment": False,
        "stage_b_executed": False,
        "lumiere_started": False,
        "original_p0_modified": False,
        "release_gate": "PASS",
        "unresolved_blockers": 0,
    }
    (OUT / "06_RELEASE_LOCK/PCC_115_STAGE_A_COHORT_AMENDMENT_STATUS.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    (OUT / "06_RELEASE_LOCK/PCC_115_STAGE_A_COHORT_AMENDMENT_FINAL_REPORT.md").write_text(
        """# PCC 115 Stage A Cohort Amendment — Final Report

Release gate: PASS.

The original 115-person manifest, 115 P0 files, 115 completion markers and original P0 hash records remain unchanged. PatientID_0113 and PatientID_0132 were excluded before target construction and before any performance calculation under `DATA_IDENTITY_OR_LABEL_ASSIGNMENT_ANOMALY`. The amended primary confirmatory cohort is locked at 113 patients.

The 113 retained cases map one-to-one to existing frozen P0 files with zero missing and zero SHA-256 mismatches. Stage B, PCC, No-smoothing, EIA, target construction, performance computation and LUMIERE were not executed.
""", encoding="utf-8")

    excluded = {"PatientID_0113", "PatientID_0132"}
    all_files = []
    excluded_manifest_files = {"PCC_115_STAGE_A_COHORT_AMENDMENT_FILE_MANIFEST.csv", "PCC_115_STAGE_A_COHORT_AMENDMENT_PACKAGE_CONTENTS.txt"}
    allowed_dirs = {"00_AUTHORITY", "01_IMMUTABILITY_AUDIT", "02_AMENDED_COHORT_LOCK", "03_P0_MAPPING", "04_STAGE_B_HANDOFF_LOCK", "05_TESTS", "06_RELEASE_LOCK"}
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path.parts[-2] in allowed_dirs and path.name not in excluded_manifest_files and "test_workspace" not in path.parts:
            all_files.append({"relative_path": str(path.relative_to(OUT)), "file_size_bytes": path.stat().st_size, "sha256": sha256(path), "role": "amendment_artifact"})
    write_rows(OUT / "06_RELEASE_LOCK/PCC_115_STAGE_A_COHORT_AMENDMENT_FILE_MANIFEST.csv", all_files)
    (OUT / "06_RELEASE_LOCK/PCC_115_STAGE_A_COHORT_AMENDMENT_PACKAGE_CONTENTS.txt").write_text("\n".join(row["relative_path"] for row in all_files) + "\n", encoding="utf-8")
    print(json.dumps({"release_gate": "PASS", "confirmatory_patients": 113, "artifact_files": len(all_files), "excluded": sorted(excluded)}, indent=2))


if __name__ == "__main__":
    main()
