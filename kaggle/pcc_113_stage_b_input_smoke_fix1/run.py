"""CPU-only Stage B input smoke test, unpacked-input fix 1.

Only metadata CSV/YAML files and one frozen P0 file's bytes are inspected.
No array is loaded, no NIfTI is opened, no target is constructed, and no
method or metric is called.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


INPUT = Path("/kaggle/input")
WORK = Path("/kaggle/working")
EXCLUDED = {"PatientID_0113", "PatientID_0132"}
EXPECTED_SHARDS = {"0": 29, "1": 27, "2": 29, "3": 28}
REQUIRED = [
    "LOCKED_113_CONFIRMATORY_CASE_MANIFEST.csv",
    "LOCKED_113_P0_MANIFEST.csv",
    "LOCKED_113_P0_SHA256.csv",
    "LOCKED_113_STAGE_B_CORRECTION_SHARD_MANIFEST.csv",
    "LOCKED_STAGE_B_CONFIRMATORY_INPUT_POLICY.yaml",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def find_name(name: str) -> list[Path]:
    return sorted(p for p in INPUT.rglob(name) if p.is_file())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def input_tree(resolved: dict[str, str]) -> str:
    lines = ["/kaggle/input", "resolved required paths:"]
    for key, value in sorted(resolved.items()):
        lines.append(f"{key}: {value}")
    lines.append("top-level mounts:")
    for p in sorted(INPUT.iterdir()):
        lines.append(str(p))
    return "\n".join(lines) + "\n"


def main() -> int:
    checks: dict[str, bool] = {}
    errors: list[str] = []
    resolved: dict[str, str] = {}
    actual_hashes: dict[str, str] = {}
    expected_hashes: dict[str, str] = {}

    expected_manifest_paths = find_name("PCC_113_STAGE_B_INPUT_BUNDLE_MANIFEST.csv")
    if len(expected_manifest_paths) != 1:
        errors.append(f"expected exactly one bundle manifest, found {expected_manifest_paths}")
        expected_rows: list[dict[str, str]] = []
    else:
        expected_rows = read_csv(expected_manifest_paths[0])
        resolved["bundle_manifest"] = str(expected_manifest_paths[0].resolve())
    for row in expected_rows:
        expected_hashes[Path(row["path"]).name] = row["sha256"]

    required_paths: dict[str, list[Path]] = {name: find_name(name) for name in REQUIRED}
    for name, candidates in required_paths.items():
        if len(candidates) != 1:
            errors.append(f"{name}: expected exactly one path, found {candidates}")
            continue
        path = candidates[0]
        resolved[name] = str(path.resolve())
        actual_hashes[name] = sha256(path)
        expected = expected_hashes.get(name)
        if expected is None:
            errors.append(f"{name}: absent from local bundle manifest")
        elif actual_hashes[name] != expected:
            errors.append(f"{name}: SHA-256 mismatch")

    checks["all_required_authority_files_found_exactly_once"] = not any(len(v) != 1 for v in required_paths.values())
    checks["all_authority_hashes_match"] = not any("SHA-256 mismatch" in e for e in errors)

    if all(len(v) == 1 for v in required_paths.values()):
        case_rows = read_csv(required_paths[REQUIRED[0]][0])
        p0_manifest_rows = read_csv(required_paths[REQUIRED[1]][0])
        p0_sha_rows = read_csv(required_paths[REQUIRED[2]][0])
        shard_rows = read_csv(required_paths[REQUIRED[3]][0])
    else:
        case_rows = p0_manifest_rows = p0_sha_rows = shard_rows = []

    patients = {r.get("patient_id", "") for r in case_rows}
    cases = {r.get("case_id", "") for r in case_rows}
    shard_patients = [r.get("patient_id", "") for r in shard_rows]
    shard_counts = {str(k): shard_patients.count(str(k)) for k in range(4)}
    # The shard CSV stores the patient identifier separately; count by its shard field.
    shard_counts = {str(k): sum(r.get("stage_b_shard") == str(k) for r in shard_rows) for k in range(4)}
    checks["confirmatory_patients_113"] = len(case_rows) == 113
    checks["unique_patients_113"] = len(patients) == 113
    checks["unique_cases_113"] = len(cases) == 113
    checks["excluded_ids_zero"] = not (EXCLUDED & patients)
    checks["p0_manifest_rows_113"] = len(p0_manifest_rows) == 113
    checks["p0_sha_rows_113"] = len(p0_sha_rows) == 113
    checks["shard_counts_29_27_29_28"] = shard_counts == EXPECTED_SHARDS
    checks["shard_union_113"] = len(set(shard_patients)) == 113
    checks["shard_overlap_zero"] = len(shard_patients) == len(set(shard_patients))

    sample_row = p0_sha_rows[0] if p0_sha_rows else {}
    sample_name = Path(sample_row.get("p0_path", "")).name
    sample_candidates = find_name(sample_name) if sample_name else []
    if len(sample_candidates) != 1:
        errors.append(f"sample P0: expected exactly one path, found {sample_candidates}")
        checks["selected_p0_exists"] = False
        checks["selected_p0_size_positive"] = False
        checks["selected_p0_hash_match"] = False
    else:
        sample_path = sample_candidates[0]
        resolved["selected_p0"] = str(sample_path.resolve())
        sample_actual = sha256(sample_path)
        actual_hashes["selected_p0"] = sample_actual
        expected_sample = sample_row.get("sha256", "")
        checks["selected_p0_exists"] = sample_path.is_file()
        checks["selected_p0_size_positive"] = sample_path.stat().st_size > 0
        checks["selected_p0_hash_match"] = sample_actual == expected_sample
        if not checks["selected_p0_hash_match"]:
            errors.append("selected P0: SHA-256 mismatch")

    gate = "PASS" if not errors and all(checks.values()) else "BLOCKED"
    report = {
        "smoke_test_fix": "STAGE_B_ENGINEERING_RECOVERY_V2_SMOKE_FIX_1",
        "smoke_test_gate": gate,
        "checks": checks,
        "errors": errors,
        "resolved_paths": resolved,
        "resolved_sha256": actual_hashes,
        "expected_sha256_from_local_bundle_manifest": expected_hashes,
        "shard_counts": shard_counts,
        "input_mounts": sorted(str(p) for p in INPUT.iterdir()),
        "future_mask_access_count": 0,
        "current_mask_access_count": 0,
        "p0_array_load_count": 0,
        "target_constructed": False,
        "performance_computed": False,
        "stage_b_methods_executed": False,
        "lumiere_started": False,
        "dataset_slug": "jeechangxin/pcc-113-stage-b-input-bundle-2026",
        "p0_source_slug": "jeechangxin/pcc-115-holdout-stage-a-p0-freeze-2026",
    }
    (WORK / "KAGGLE_INPUT_DIRECTORY_TREE.txt").write_text(input_tree(resolved), encoding="utf-8")
    (WORK / "STAGE_B_RESOLVED_INPUT_PATHS.yaml").write_text(
        "dataset_slug: jeechangxin/pcc-113-stage-b-input-bundle-2026\n"
        "p0_source_slug: jeechangxin/pcc-115-holdout-stage-a-p0-freeze-2026\n"
        + "resolved_paths:\n"
        + "\n".join(f"  {k}: {v}" for k, v in sorted(resolved.items()))
        + "\n",
        encoding="utf-8",
    )
    (WORK / "STAGE_B_KAGGLE_SOURCE_PROVENANCE.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (WORK / "STAGE_B_KAGGLE_INPUT_SMOKE_TEST_FIX1_STATUS.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (WORK / "STAGE_B_KAGGLE_INPUT_SMOKE_TEST_FIX1_REPORT.md").write_text(
        "# Stage B Kaggle input smoke test — fix 1\n\n"
        + "\n".join([f"- {k}: {v}" for k, v in [
            ("SMOKE_TEST_GATE", gate),
            ("manifest rows", len(case_rows)),
            ("unique patients", len(patients)),
            ("unique cases", len(cases)),
            ("excluded IDs", len(EXCLUDED & patients)),
            ("P0 manifest rows", len(p0_manifest_rows)),
            ("shard counts", shard_counts),
            ("shard union", len(set(shard_patients))),
            ("shard overlap", len(shard_patients) - len(set(shard_patients))),
            ("required authority hashes", "MATCH" if checks["all_authority_hashes_match"] else "MISMATCH"),
            ("future mask access count", 0),
            ("P0 array load count", 0),
            ("target constructed", False),
            ("performance computed", False),
            ("Stage B methods executed", False),
            ("LUMIERE started", False),
        ]]) + "\n",
        encoding="utf-8",
    )
    return 0 if gate == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
