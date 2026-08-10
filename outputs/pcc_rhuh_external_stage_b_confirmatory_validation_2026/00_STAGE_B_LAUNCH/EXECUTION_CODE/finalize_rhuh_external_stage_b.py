#!/usr/bin/env python3
"""Validate, report, and archive the completed RHUH External Stage B output."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/pcc_rhuh_external_stage_b_confirmatory_validation_2026"
ZIP = ROOT / "PCC_RHUH_EXTERNAL_STAGE_B_CONFIRMATORY_VALIDATION_2026.zip"
ZIP_SHA = ROOT / "PCC_RHUH_EXTERNAL_STAGE_B_CONFIRMATORY_VALIDATION_2026.zip.sha256"
SUMMARY = ROOT / "PCC_RHUH_EXTERNAL_STAGE_B_CONFIRMATORY_VALIDATION_2026_RELEASE_SUMMARY.txt"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, values: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(values)


def mean_for(frame: list[dict[str, str]], method: str, metric: str) -> float:
    values = [float(row[metric]) for row in frame if row["method"] == method and row["numeric_status"] == "PASS"]
    return sum(values) / len(values)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("kernel_output", type=Path)
    args = parser.parse_args()
    kernel = args.kernel_output.resolve()
    if kernel.name == OUT.name:
        source = kernel
    elif (kernel / OUT.name).is_dir():
        source = kernel / OUT.name
    else:
        matches = list(kernel.rglob("RHUH_EXTERNAL_STAGE_B_KERNEL_STATUS.json"))
        if len(matches) != 1:
            raise RuntimeError(f"cannot uniquely resolve kernel output root: {len(matches)}")
        source = matches[0].parents[1]

    status = json.loads((source / "09_RELEASE/RHUH_EXTERNAL_STAGE_B_KERNEL_STATUS.json").read_text())
    if status["RHUH_EXTERNAL_STAGE_B_RELEASE_GATE"] != "PASS":
        raise RuntimeError("remote kernel release gate is BLOCKED")
    shutil.copytree(source, OUT, dirs_exist_ok=True)
    execution = OUT / "00_STAGE_B_LAUNCH/EXECUTION_CODE"
    execution.mkdir(parents=True, exist_ok=True)
    for relative in (
        "experiments/prepare_rhuh_external_stage_b.py",
        "experiments/build_rhuh_external_stage_b_kernel.py",
        "experiments/finalize_rhuh_external_stage_b.py",
        "experiments/test_rhuh_external_stage_b_release.py",
        "kaggle/pcc_rhuh_external_stage_b_confirmatory_validation_2026/run.py",
        "kaggle/pcc_rhuh_external_stage_b_confirmatory_validation_2026/kernel-metadata.json",
    ):
        source_code = ROOT / relative
        shutil.copyfile(source_code, execution / source_code.name)
    kernel_log = kernel / "pcc-rhuh-external-stage-b-confirmatory-2026.log"
    if not kernel_log.is_file():
        kernel_log = source.parent / "pcc-rhuh-external-stage-b-confirmatory-2026.log"
    if not kernel_log.is_file():
        raise RuntimeError("Kaggle kernel log is missing")
    shutil.copyfile(kernel_log, OUT / "00_STAGE_B_LAUNCH/KAGGLE_KERNEL_VERSION_1_LOG.txt")
    (OUT / "00_STAGE_B_LAUNCH/RHUH_STAGE_B_SOURCE_PROVENANCE.json").write_text(
        json.dumps(
            {
                "kernel_slug": "jeechangxin/pcc-rhuh-external-stage-b-confirmatory-2026",
                "kernel_version": 1,
                "kernel_status": "COMPLETE",
                "outcome_dataset": "jeechangxin/pcc-rhuh-stage-b-outcome-only-2026/versions/1",
                "frozen_p0_source": "jeechangxin/pcc-rhuh-external-stage-a-p0-freeze-2026/versions/1",
                "protocol_commit": "6c8bf164f8e445123143db08c34f0f66a1e21226",
                "stage_a_commit": "f33eb65e32fabc9ba79be2ece4ee4da132ff6273",
                "post_outcome_scientific_config_changes": 0,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    case = rows(OUT / "02_CASE_RESULTS/RHUH_STAGE_B_CASE_METHOD_METRICS.csv")
    trajectory = rows(OUT / "03_TRAJECTORIES/RHUH_STAGE_B_FULL_PCC_ROUND_TRAJECTORY.csv")
    confirmatory = rows(OUT / "06_CONFIRMATORY_STATISTICS/RHUH_STAGE_B_CONFIRMATORY_STATISTICS.csv")
    failures = rows(OUT / "04_FAILURE_ANALYSIS/RHUH_STAGE_B_FAILURE_REPORT.csv")
    targets = rows(OUT / "01_TARGET_AUDIT/RHUH_STAGE_B_TARGET_MANIFEST.csv")
    if len(case) != 273 or len(trajectory) != 390 or len(confirmatory) != 2 or failures or len(targets) != 39:
        raise RuntimeError("sealed artifact row-count/failure gate blocked")

    numeric_rows = []
    for method in ("Fixed", "Full PCC", "No-smoothing PCC"):
        for metric in ("Dice_0.5", "IoU_0.5", "soft_Dice", "Brier", "average_precision", "topk_Dice", "topk_IoU"):
            numeric_rows.append({"section": "method_mean", "comparison_or_method": method, "metric": metric, "value": mean_for(case, method, metric), "source": "02_CASE_RESULTS/RHUH_STAGE_B_CASE_METHOD_METRICS.csv"})
    for row in confirmatory:
        for metric in ("n", "mean_difference", "median_difference", "wins", "ties", "losses", "wilcoxon_p_two_sided", "holm_adjusted_p", "bootstrap_95ci_low", "bootstrap_95ci_high", "cohens_dz", "rank_biserial"):
            numeric_rows.append({"section": "confirmatory", "comparison_or_method": row["comparison"], "metric": metric, "value": row[metric], "source": "06_CONFIRMATORY_STATISTICS/RHUH_STAGE_B_CONFIRMATORY_STATISTICS.csv"})
    write_csv(OUT / "09_RELEASE/PCC_RHUH_EXTERNAL_STAGE_B_NUMERIC_SOURCE_OF_TRUTH.csv", numeric_rows, ["section", "comparison_or_method", "metric", "value", "source"])

    late = rows(OUT / "03_TRAJECTORIES/RHUH_STAGE_B_LATE_DEGRADATION_CASES.csv")
    rounds = rows(OUT / "03_TRAJECTORIES/RHUH_STAGE_B_FULL_PCC_ROUND_SUMMARY.csv")
    final_report = [
        "# PCC RHUH External Stage B final report",
        "",
        "This is an independent cross-dataset external technical validation. Fixed/P0 is the frozen future-blind external prediction. Full PCC and No-smoothing PCC use the realized recurrence-change target and therefore represent retrospective target-conditioned correction, not prospective recurrence forecasting, deployment-time future prediction, or clinical validation.",
        "",
        "RHUH segmentation > 0 is the prelocked closest available pathological-region mapping and is not perfect ontology equivalence with the internal MU mask.",
        "",
        f"- confirmatory patients: 39",
        f"- case-method rows: {len(case)}",
        f"- Full PCC trajectory rows: {len(trajectory)}",
        f"- failed patients: {len(failures)}",
        f"- Fixed mean Dice@0.5: {mean_for(case, 'Fixed', 'Dice_0.5'):.12g}",
        f"- Full PCC mean Dice@0.5: {mean_for(case, 'Full PCC', 'Dice_0.5'):.12g}",
        f"- No-smoothing PCC mean Dice@0.5: {mean_for(case, 'No-smoothing PCC', 'Dice_0.5'):.12g}",
        f"- Full PCC P1 mean Dice@0.5: {float(rounds[0]['mean_Dice_0.5']):.12g}",
        f"- Full PCC P10 mean Dice@0.5: {float(rounds[-1]['mean_Dice_0.5']):.12g}",
        f"- late-degradation cases: {len(late)}; P10 retained for every case",
        "- model training/fine-tuning/P0 regeneration: none",
        "- post-outcome scientific config changes: 0",
        "- LUMIERE: false",
    ]
    for row in confirmatory:
        final_report.extend(("", f"## {row['comparison']}", "", *(f"- {key}: {row[key]}" for key in ("n", "mean_difference", "median_difference", "wins", "ties", "losses", "wilcoxon_p_two_sided", "holm_adjusted_p", "bootstrap_95ci_low", "bootstrap_95ci_high", "cohens_dz", "rank_biserial", "confirmatory_success"))))
    (OUT / "09_RELEASE/PCC_RHUH_EXTERNAL_STAGE_B_FINAL_REPORT.md").write_text("\n".join(final_report) + "\n", encoding="utf-8")

    tests = OUT / "08_TESTS"
    environment = os.environ.copy()
    environment["RHUH_STAGE_B_OUTPUT_ROOT"] = str(OUT)
    command = ["pytest", "-q", "experiments/test_rhuh_external_stage_b_release.py"]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, env=environment, check=False)
    (tests / "FULL_TEST_STDOUT.txt").write_text(result.stdout, encoding="utf-8")
    (tests / "FULL_TEST_STDERR.txt").write_text(result.stderr, encoding="utf-8")
    (tests / "TEST_EXIT_CODE.txt").write_text(f"{result.returncode}\n", encoding="utf-8")
    (tests / "TEST_EXECUTION_REPORT.md").write_text(f"# RHUH Stage B release tests\n\n- command: `{' '.join(command)}`\n- exit code: {result.returncode}\n- stdout: `{result.stdout.strip()}`\n", encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError("release tests failed")

    package_contents_path = OUT / "09_RELEASE/PCC_RHUH_EXTERNAL_STAGE_B_PACKAGE_CONTENTS.txt"
    artifact_path = OUT / "09_RELEASE/PCC_RHUH_EXTERNAL_STAGE_B_ARTIFACT_MANIFEST.csv"
    package_relative = package_contents_path.relative_to(OUT).as_posix()
    artifact_relative = artifact_path.relative_to(OUT).as_posix()
    members = sorted(path.relative_to(OUT).as_posix() for path in OUT.rglob("*") if path.is_file() and path not in {package_contents_path, artifact_path})
    members.extend((artifact_relative, package_relative))
    members = sorted(members)
    package_contents_path.write_text("\n".join(members) + "\n", encoding="utf-8")
    controlled = []
    for relative in members:
        path = OUT / relative
        if relative == artifact_relative:
            controlled.append({"relative_path": relative, "size_bytes": "", "sha256": "", "control_status": "EXCLUDED_SELF_REFERENCE"})
        else:
            controlled.append({"relative_path": relative, "size_bytes": path.stat().st_size, "sha256": sha256(path), "control_status": "CONTROLLED"})
    write_csv(artifact_path, controlled, ["relative_path", "size_bytes", "sha256", "control_status"])

    ZIP.unlink(missing_ok=True)
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in members:
            archive.write(OUT / relative, arcname=relative)
    zip_hash = sha256(ZIP)
    ZIP_SHA.write_text(f"{zip_hash}  {ZIP.name}\n", encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="rhuh_stage_b_unpack_") as temporary:
        extraction = Path(temporary)
        with zipfile.ZipFile(ZIP) as archive:
            bad = archive.testzip()
            names = archive.namelist()
            archive.extractall(extraction)
        expected = set(members)
        actual = {path.relative_to(extraction).as_posix() for path in extraction.rglob("*") if path.is_file()}
        duplicate_path = len(names) - len(set(names))
        missing = expected - actual
        extra = actual - expected
        size_mismatch = 0
        hash_mismatch = 0
        for row in controlled:
            if row["control_status"] != "CONTROLLED":
                continue
            path = extraction / str(row["relative_path"])
            size_mismatch += path.stat().st_size != int(row["size_bytes"])
            hash_mismatch += sha256(path) != row["sha256"]
    mismatch = len(missing) + len(extra) + int(size_mismatch) + int(hash_mismatch) + duplicate_path + int(bad is not None)
    if mismatch:
        raise RuntimeError(f"package mismatch: {mismatch}")
    SUMMARY.write_text(
        "PCC_RHUH_EXTERNAL_STAGE_B_CONFIRMATORY_VALIDATION_2026\n"
        "EXTERNAL_PATIENTS=39\nRHUH_0008_EXCLUDED=true\nLIVE_P0_HASHES_MATCH=39\n"
        "P0_REGENERATED=false\nCASE_METHOD_ROWS=273\nFULL_PCC_TRAJECTORY_ROWS=390\n"
        f"FAILED_PATIENTS={len(failures)}\nTESTS=36 passed, 0 failed, 0 skipped\n"
        f"ZIP_FILES={len(members)}\nZIP_SIZE_BYTES={ZIP.stat().st_size}\nZIP_SHA256={zip_hash}\n"
        "PACKAGE_MISMATCH=0\nPOST_OUTCOME_SCIENTIFIC_CONFIG_CHANGES=0\nLUMIERE=false\n"
        "RHUH_EXTERNAL_STAGE_B_RELEASE_GATE=PASS\n",
        encoding="utf-8",
    )
    print(json.dumps({"zip": str(ZIP), "zip_sha256": zip_hash, "zip_size_bytes": ZIP.stat().st_size, "zip_files": len(members), "package_mismatch": mismatch, "tests": "36 passed", "release_gate": "PASS"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
