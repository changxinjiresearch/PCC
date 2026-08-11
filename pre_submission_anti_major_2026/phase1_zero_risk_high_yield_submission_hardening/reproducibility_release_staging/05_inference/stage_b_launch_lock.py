"""Build the immutable, pre-outcome 113-patient Stage B launch lock.

This script only reads authority manifests, source code, and frozen P0 bytes.
It never loads a P0 array and never opens a current/future mask.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import zipfile
from pathlib import Path


PROTOCOL_SHA256 = "34ebddc1a512867f293b30d68c1dc6663a45092dcdcef9c317fd5ca9da239b34"
AMENDMENT_SHA256 = "906eb95e5d97d1b6abadac9e0129b6f33dd384e64e139ad32f1e7d67b4c265f0"
EXCLUDED = {"PatientID_0113", "PatientID_0132"}
EXPECTED_SHARDS = {"0": 29, "1": 27, "2": 29, "3": 28}
METHOD_FILES = [
    "src/models/fixed_baseline.py",
    "src/models/naive_self_tightening.py",
    "src/models/eia.py",
    "src/models/pcc.py",
    "src/analysis/internal_completion.py",
]
EVALUATION_FILES = ["src/evaluation/metrics.py", "src/analysis/validity_patch.py"]
STATISTICS_FILES = ["src/analysis/holdout_statistics.py"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_zip_csv(z: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    with z.open(name) as f:
        return list(csv.DictReader((line.decode("utf-8") for line in f)))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--protocol-zip", type=Path, required=True)
    ap.add_argument("--amendment-zip", type=Path, required=True)
    ap.add_argument("--p0-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    authority = out / "00_STAGE_B_AUTHORITY"
    launch = out / "01_LAUNCH_LOCK"
    if out.exists():
        raise RuntimeError(f"refusing to overwrite existing output: {out}")
    out.mkdir(parents=True)
    authority.mkdir(); launch.mkdir()

    protocol_hash = sha256(args.protocol_zip)
    amendment_hash = sha256(args.amendment_zip)
    if protocol_hash != PROTOCOL_SHA256 or amendment_hash != AMENDMENT_SHA256:
        raise RuntimeError("authority ZIP SHA-256 mismatch")
    with zipfile.ZipFile(args.protocol_zip) as pz, zipfile.ZipFile(args.amendment_zip) as az:
        p_rows = read_zip_csv(pz, "09_EXECUTION_PLAN/LOCKED_115_STAGE_B_CORRECTION_SHARD_MANIFEST.csv")
        c_rows = read_zip_csv(az, "02_AMENDED_COHORT_LOCK/LOCKED_113_CONFIRMATORY_CASE_MANIFEST.csv")
        ids_rows = read_zip_csv(az, "02_AMENDED_COHORT_LOCK/LOCKED_113_CONFIRMATORY_PATIENT_IDS.csv")
        p0_rows = read_zip_csv(az, "03_P0_MAPPING/LOCKED_113_P0_SHA256.csv")
        m40_rows = read_zip_csv(pz, "01_COHORT_LOCK/LOCKED_40_PATIENT_IDS.csv")
        for source, name in [
            (pz, "04_METHOD_LOCK/LOCKED_115_METHOD_CONFIG.yaml"),
            (pz, "04_METHOD_LOCK/LOCKED_115_METHOD_DEFINITIONS.md"),
            (pz, "05_TARGET_AND_STAGE_LOCK/LOCKED_115_TARGET_POLICY.yaml"),
            (pz, "06_EVALUATION_LOCK/LOCKED_115_EVALUATION_POLICY.yaml"),
            (pz, "06_EVALUATION_LOCK/LOCKED_115_THRESHOLD_POLICY.yaml"),
            (pz, "07_STATISTICS_LOCK/LOCKED_115_STATISTICAL_ANALYSIS_PLAN.yaml"),
            (pz, "07_STATISTICS_LOCK/PCC_115_CONFIRMATORY_ANALYSIS_PLAN.md"),
            (pz, "08_FAILURE_POLICY/LOCKED_115_FAILURE_POLICY.yaml"),
            (pz, "04_METHOD_LOCK/METHOD_CODE_HASHES.csv"),
            (pz, "06_EVALUATION_LOCK/EVALUATION_CODE_HASHES.csv"),
            (pz, "07_STATISTICS_LOCK/STATISTICS_CODE_HASHES.csv"),
            (pz, "09_EXECUTION_PLAN/LOCKED_115_STAGE_B_CORRECTION_SHARD_MANIFEST.csv"),
            (az, "02_AMENDED_COHORT_LOCK/LOCKED_113_CONFIRMATORY_CASE_MANIFEST.csv"),
            (az, "02_AMENDED_COHORT_LOCK/LOCKED_113_CONFIRMATORY_PATIENT_IDS.csv"),
            (az, "03_P0_MAPPING/LOCKED_113_P0_MANIFEST.csv"),
            (az, "03_P0_MAPPING/LOCKED_113_P0_SHA256.csv"),
            (az, "02_AMENDED_COHORT_LOCK/EXCLUDED_POST_LOCK_CASES.csv"),
        ]:
            target = authority / Path(name).name
            target.write_bytes(source.read(name))

    ids = [r["patient_id"] for r in c_rows]
    cases = [r["case_id"] for r in c_rows]
    ids_set = set(ids); cases_set = set(cases)
    p0_ids = {r["patient_id"] for r in p0_rows}
    if len(ids) != 113 or len(ids_set) != 113 or len(cases_set) != 113:
        raise RuntimeError("confirmatory identity count failure")
    if EXCLUDED & ids_set or len(p0_rows) != 113 or p0_ids != ids_set:
        raise RuntimeError("exclusion or P0 mapping identity failure")
    locked40 = {r["patient_id"] for r in m40_rows}
    if locked40 & ids_set:
        raise RuntimeError("overlap with locked 40")
    old_by_id = {r["patient_id"]: r for r in p_rows}
    if set(old_by_id) != (ids_set | EXCLUDED):
        raise RuntimeError("old 115 manifest identity failure")
    shard_rows = [{**old_by_id[r["patient_id"]]} for r in c_rows]
    counts = {str(k): sum(r["stage_b_shard"] == str(k) for r in shard_rows) for k in range(4)}
    if counts != EXPECTED_SHARDS:
        raise RuntimeError(f"unexpected deterministic shard counts: {counts}")
    write_csv(authority / "LOCKED_113_STAGE_B_CORRECTION_SHARD_MANIFEST.csv", shard_rows,
              ["patient_id", "case_id", "current_timepoint", "future_timepoint", "stage_b_shard"])

    p0_audit = []
    p0_sha_by_id = {r["patient_id"]: r for r in p0_rows}
    for patient_id in sorted(ids):
        row = p0_sha_by_id[patient_id]
        path = args.p0_root / row["p0_path"]
        actual = sha256(path) if path.exists() else "MISSING"
        p0_audit.append({"patient_id": patient_id, "case_id": row["case_id"], "expected_sha256": row["sha256"], "actual_sha256": actual, "status": "MATCH" if actual == row["sha256"] else "MISMATCH"})
    write_csv(authority / "LOCKED_113_P0_HASH_AUDIT.csv", p0_audit, list(p0_audit[0]))
    if any(r["status"] != "MATCH" for r in p0_audit):
        raise RuntimeError("frozen P0 hash mismatch")

    hash_rows = []
    for role, paths in [("method", METHOD_FILES), ("evaluation", EVALUATION_FILES), ("statistics", STATISTICS_FILES)]:
        for rel in paths:
            path = repo / rel
            hash_rows.append({"role": role, "relative_path": rel, "file_size_bytes": path.stat().st_size, "sha256": sha256(path)})
    write_csv(launch / "PCC_113_STAGE_B_AUTHORITY_HASHES.csv", hash_rows, list(hash_rows[0]))
    write_csv(launch / "PCC_113_STAGE_B_PROTOCOL_CODE_HASHES.csv", hash_rows, list(hash_rows[0]))

    derivation_md = """# PCC 113 Stage B protocol derivation\n\nThis is a mechanical cohort amendment of the locked 115-patient protocol. The only scientific denominator override is 115 -> 113 after the two pre-outcome identity exclusions. Methods, parameters, endpoints, threshold, failure semantics, and statistical plan remain inherited from the verified authority archives.\n\n- original_locked_holdout: 115\n- post_lock_identity_exclusions: 2\n- confirmatory_denominator: 113\n- excluded_ids: PatientID_0113, PatientID_0132\n- performance_seen_before_amendment: false\n- P0_regenerated: false\n- LUMIERE: false\n\nThe Stage B target is `(future_mask > 0.5) AND NOT (current_mask > 0.5)`, without registration or resampling. Fixed threshold is 0.5; Full PCC uses P10; No-smoothing differs only by bypassing the locked Gaussian smoothing of each round discrepancy.\n"""
    (launch / "PCC_113_STAGE_B_PROTOCOL_DERIVATION.md").write_text(derivation_md, encoding="utf-8")
    derivation = {"original_locked_holdout": 115, "post_lock_identity_exclusions": 2, "confirmatory_denominator": 113, "excluded_ids": sorted(EXCLUDED), "performance_seen_before_amendment": False, "P0_regenerated": False, "target_formula": "(future_mask > 0.5) AND NOT (current_mask > 0.5)", "fixed_threshold": 0.5, "full_pcc_rounds": 10, "bootstrap_replicates": 10000, "bootstrap_seed": 20260803, "lumieres_started": False}
    (launch / "PCC_113_STAGE_B_PROTOCOL_DERIVATION.yaml").write_text(json.dumps(derivation, indent=2) + "\n", encoding="utf-8")
    status = {"launch_gate": "PASS", "authority_protocol_sha256": protocol_hash, "authority_amendment_sha256": amendment_hash, "confirmatory_patients": 113, "unique_patient_ids": 113, "unique_case_ids": 113, "excluded_ids_absent": True, "overlap_with_locked_40": 0, "p0_hash_mismatch": 0, "p0_regenerated": False, "shard_counts": counts, "future_masks_read": False, "performance_computed": False, "lumieres_started": False}
    (launch / "PCC_113_STAGE_B_LAUNCH_STATUS.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
