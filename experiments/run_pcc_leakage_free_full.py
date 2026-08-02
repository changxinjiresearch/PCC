"""Single canonical entry coordinating leakage-free P0 then retrospective PCC."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import subprocess
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/pcc_leakage_free_canonical.yaml")
    parser.add_argument("--case-manifest")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    command = [sys.executable, "experiments/run_leakage_free_p0.py", "--config", args.config]
    if args.case_manifest:
        command.extend(("--case-manifest", args.case_manifest))
    if args.preflight:
        command.append("--preflight")
    if args.smoke:
        command.extend(("--smoke", "--fold", "1"))
    status = subprocess.run(command, check=False).returncode
    if status:
        return status

    import json
    import nibabel as nib
    import numpy as np
    import yaml
    from src.pipelines.pcc_leakage_free_rerun import (
        persist_retrospective_case,
        run_retrospective_methods,
    )
    from src.preprocessing.current_only_preprocessing import construct_future_change_label

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    output_root = Path(config["output_root"])
    manifest = Path(args.case_manifest) if args.case_manifest else output_root / "LOCKED_CASE_MANIFEST.csv"
    with manifest.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    available = [row for row in rows if (output_root / "held_out_p0" / row["case_id"] / "P0_COMPLETE.json").exists()]
    if not args.smoke and len(available) != len(rows):
        print(json.dumps({"error": "All held-out P0 maps must complete before retrospective correction", "complete": len(available), "expected": len(rows)}, indent=2))
        return 4
    if args.smoke:
        available = available[:1]
    for row in available:
        case_id = row["case_id"]
        p0 = np.load(output_root / "held_out_p0" / case_id / "P0_float32.npy").astype(np.float32)
        current_mask = nib.load(row["current_mask_path"]).get_fdata()
        future_mask = nib.load(row["future_mask_path"]).get_fdata()
        target = np.moveaxis(construct_future_change_label(current_mask, future_mask), -1, 0).astype(np.uint8)
        result = run_retrospective_methods(p0, target)
        persist_retrospective_case(output_root / "retrospective", case_id, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
