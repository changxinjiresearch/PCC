"""Run locked, correction-only downstream experiments from frozen v8 P0 maps.

This entry never imports the predictor pipeline and cannot train or regenerate
P0. It currently exposes only the Phase-A RECOVERED_AND_LOCKED sensitivity
grid. Other named downstream families remain unavailable by design.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from src.evaluation.metrics import eval_prob_map
from src.models.pcc import apply_pcc


EXPECTED_CONFIG_HASH = "29111a4d9cb16a2981eec5cbaa193346f9715630a6e81aaf9734805f789a14b6"
EXPECTED_CASE_HASH = "e5ad65359280e002d9bcc4c89211f48840d535b602821ad22db863b88e4656f8"
EXPECTED_FOLD_HASH = "880bd3b2c87c571d5df10342357a8b67c7d6069a2b68a99df0f5dccb783154ec"

CANONICAL = {"iterations": 10, "eta": 0.30, "dilation_radius": 26.0, "sigma": 2.0}
SENSITIVITY = (
    ("rounds_5", {**CANONICAL, "iterations": 5}),
    ("rounds_15", {**CANONICAL, "iterations": 15}),
    ("eta_020", {**CANONICAL, "eta": 0.20}),
    ("eta_040", {**CANONICAL, "eta": 0.40}),
    ("radius_18", {**CANONICAL, "dilation_radius": 18.0}),
    ("radius_34", {**CANONICAL, "dilation_radius": 34.0}),
    ("sigma_1", {**CANONICAL, "sigma": 1.0}),
    ("sigma_3", {**CANONICAL, "sigma": 3.0}),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_frozen_root(root: Path) -> list[str]:
    status = json.loads((root / "FULL_RUN_STATUS.json").read_text())
    required = {
        "status": "COMPLETE", "completed_folds": 5, "completed_p0_cases": 40,
        "completed_retrospective_cases": 40, "failed_cases": 0,
        "config_sha256": EXPECTED_CONFIG_HASH,
        "case_manifest_sha256": EXPECTED_CASE_HASH,
        "fold_manifest_sha256": EXPECTED_FOLD_HASH,
    }
    for key, expected in required.items():
        if status.get(key) != expected:
            raise RuntimeError(f"Frozen status mismatch for {key}: {status.get(key)!r}")
    cases = sorted(path.parent.name for path in (root / "held_out_p0").glob("*/P0_float32.npy"))
    targets = sorted(path.parent.name for path in (root / "retrospective" / "cases").glob("*/target.npy"))
    if len(cases) != 40 or cases != targets:
        raise RuntimeError(f"Frozen P0/target contract mismatch: {len(cases)} / {len(targets)}")
    return cases


def atomic_csv(path: Path, rows: list[dict[str, object]]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    temporary.replace(path)


def run_sensitivity(frozen_root: Path, output_root: Path) -> Path:
    cases = validate_frozen_root(frozen_root)
    destination = output_root / "12_sensitivity"
    case_root = destination / "cases"
    case_root.mkdir(parents=True, exist_ok=True)
    failed: list[dict[str, str]] = []
    for case_id in cases:
        completion = case_root / case_id / "SENSITIVITY_COMPLETE.json"
        metrics_path = case_root / case_id / "sensitivity_metrics.csv"
        if completion.exists() and metrics_path.exists():
            continue
        completion.parent.mkdir(parents=True, exist_ok=True)
        try:
            p0_path = frozen_root / "held_out_p0" / case_id / "P0_float32.npy"
            target_path = frozen_root / "retrospective" / "cases" / case_id / "target.npy"
            p0 = np.load(p0_path, allow_pickle=False)
            target = np.load(target_path, allow_pickle=False)
            if p0.dtype != np.float32 or p0.shape != target.shape or not np.isfinite(p0).all():
                raise RuntimeError("P0/target array contract failed")
            rows: list[dict[str, object]] = []
            for name, parameters in SENSITIVITY:
                corrected = apply_pcc(p0, target, **parameters).corrected_probability
                metrics = eval_prob_map(corrected, target)
                rows.append({
                    "case_id": case_id, "configuration": name,
                    "iterations": parameters["iterations"], "eta": parameters["eta"],
                    "dilation_radius": parameters["dilation_radius"], "sigma": parameters["sigma"],
                    **metrics,
                })
            atomic_csv(metrics_path, rows)
            completion.write_text(json.dumps({
                "status": "complete", "case_id": case_id, "p0_sha256": sha256(p0_path),
                "target_sha256": sha256(target_path), "configurations": len(rows),
                "predictor_retrained": False,
            }, separators=(",", ":")), encoding="utf-8")
        except Exception as exc:
            failed.append({"case_id": case_id, "stage": "sensitivity", "error": repr(exc)})
    all_rows: list[dict[str, str]] = []
    for case_id in cases:
        path = case_root / case_id / "sensitivity_metrics.csv"
        if path.exists():
            with path.open(newline="", encoding="utf-8") as stream:
                all_rows.extend(csv.DictReader(stream))
    if len(all_rows) != 40 * len(SENSITIVITY):
        raise RuntimeError(f"Expected 320 sensitivity rows, found {len(all_rows)}; failures={failed}")
    atomic_csv(destination / "SENSITIVITY_CASE_METRICS.csv", all_rows)
    failed_path = destination / "FAILED_CASES.csv"
    if failed:
        atomic_csv(failed_path, failed)
    else:
        with failed_path.open("w", newline="", encoding="utf-8") as stream:
            csv.writer(stream).writerow(["case_id", "stage", "error"])
    (destination / "SENSITIVITY_STATUS.json").write_text(json.dumps({
        "status": "COMPLETE", "cases": 40, "configurations": len(SENSITIVITY),
        "rows": len(all_rows), "failed_cases": len(failed), "predictor_retrained": False,
        "frozen_source_status_sha256": sha256(frozen_root / "FULL_RUN_STATUS.json"),
    }, indent=2) + "\n", encoding="utf-8")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", choices=["sensitivity"], required=True)
    parser.add_argument("--frozen-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    arguments = parser.parse_args()
    result = run_sensitivity(arguments.frozen_root, arguments.output_root)
    print(json.dumps({"status": "COMPLETE", "output": str(result)}))


if __name__ == "__main__":
    main()
