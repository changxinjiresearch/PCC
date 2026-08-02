"""Kaggle entry for PCC_LEAKAGE_FREE_RERUN_2026 held-out P0 generation.

The entry performs preflight and fold locking locally. GPU training is enabled
only after real case/fold manifests have been created from the mounted data.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from src.pipelines.leakage_free_p0 import (
    CaseIdentity, build_group_folds, discover_longitudinal_cases,
    run_fold_training, write_locked_case_manifest, write_locked_fold_manifest,
)


def load_config(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_cases(path: Path) -> list[CaseIdentity]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    return [CaseIdentity(row["case_id"], row["patient_id"]) for row in rows]


def select_execution_device(*, allow_smoke_cpu_fallback: bool) -> str:
    import torch
    if not torch.cuda.is_available():
        if allow_smoke_cpu_fallback:
            return "cpu"
        raise RuntimeError("CUDA is required for the full five-fold run")
    try:
        probe = torch.nn.Conv2d(1, 1, 1).cuda()
        probe(torch.zeros((1, 1, 2, 2), device="cuda"))
        torch.cuda.synchronize()
        return "cuda"
    except Exception as error:
        if not allow_smoke_cpu_fallback:
            raise RuntimeError(f"Kaggle CUDA compatibility probe failed: {error}") from error
        print(f"CUDA probe failed; smoke-only CPU fallback: {error}")
        return "cpu"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/pcc_leakage_free_canonical.yaml")
    parser.add_argument("--case-manifest")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--fold", type=int)
    parser.add_argument("--gpu-required", action="store_true")
    args = parser.parse_args()
    config = load_config(Path(args.config))
    errors = []
    for module in ("numpy", "scipy", "nibabel", "torch"):
        try:
            __import__(module)
        except Exception as error:
            errors.append(f"{module}: {error!r}")
    output_root = Path(config["output_root"])
    manifest = Path(args.case_manifest) if args.case_manifest else output_root / "LOCKED_CASE_MANIFEST.csv"
    dataset_candidates = []
    discovery_root = Path(config["dataset_discovery_root"])
    if discovery_root.is_dir():
        dataset_candidates = sorted(
            path for path in discovery_root.rglob("MU-Glioma-Post")
            if path.is_dir() and any(path.glob("PatientID_*"))
        )
    if not manifest.is_file() and len(dataset_candidates) != 1:
        errors.append(f"Cannot uniquely discover MU-Glioma-Post dataset: {dataset_candidates}")
    result = {"experiment": config["experiment_name"], "errors": errors}
    print(json.dumps(result, indent=2))
    if errors:
        return 2
    if not manifest.exists():
        case_rows = discover_longitudinal_cases(dataset_candidates[0])
        if len(case_rows) != 40:
            print(json.dumps({"error": f"Expected 40 locked patients, found {len(case_rows)}"}, indent=2))
            return 2
        digest = write_locked_case_manifest(manifest, case_rows)
        print(json.dumps({"case_manifest": str(manifest), "sha256": digest}, indent=2))
    fold_path = Path(config["output_root"]) / "LOCKED_FOLD_MANIFEST.csv"
    if not fold_path.exists():
        digest = write_locked_fold_manifest(
            fold_path,
            build_group_folds(load_cases(manifest), n_splits=5, seed=config["seed"]),
        )
        print(json.dumps({"fold_manifest": str(fold_path), "sha256": digest}, indent=2))
    if args.preflight:
        return 0
    with manifest.open(newline="", encoding="utf-8") as stream:
        case_rows = list(csv.DictReader(stream))
    with fold_path.open(newline="", encoding="utf-8") as stream:
        fold_rows = [{**row, "fold": int(row["fold"])} for row in csv.DictReader(stream)]
    folds = [args.fold] if args.fold else list(range(1, 6))
    device = select_execution_device(
        allow_smoke_cpu_fallback=args.smoke and not args.gpu_required
    )
    for fold in folds:
        run_fold_training(
            case_rows, fold_rows, fold, output_root,
            epochs=2 if args.smoke else config["predictor"]["epochs"],
            batch_size=config["predictor"]["batch_size"],
            learning_rate=config["predictor"]["learning_rate"],
            max_test_cases=1 if args.smoke else None,
            max_train_cases=2 if args.smoke else None,
            device=device,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
