"""Build small, auditable index tables for the internal-validity patch."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tagged(path: Path, category: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame.insert(0, "analysis", category)
    column = "audit_source_file" if "source_file" in frame.columns else "source_file"
    frame.insert(1, column, str(path))
    return frame


def build(root: Path) -> None:
    statuses = [
        ("protocol_lock", "COMPLETE", "bbcdd52; config d49043609de3507ec334dcca42f878b1c621300eca17790287e9504bf7313752"),
        ("authoritative_artifact_recovery", "COMPLETE", "Direct Kaggle v8 recovery; four required CSVs plus status/config"),
        ("target_independent_evaluation", "COMPLETE", "8 methods x 40 cases; fixed 0.5, probability, and cross-fitted threshold"),
        ("no_smoothing_robustness", "COMPLETE", "1720 repeats aggregated to n=40 before inference"),
        ("layer1_statistical_reaudit", "COMPLETE", "No model rerun; v1 primary candidate and v1.1 sensitivity"),
        ("layer3_statistical_reaudit", "COMPLETE", "No model rerun; prespecified Holm families"),
        ("cohort_selection_audit", "COMPLETE_WITH_DOCUMENTED_UNKNOWNS", "Historical pre-2026 discovery stages not fully recoverable"),
        ("identity_cross_validation", "COMPLETE", "40 unique patients; manifests and Layer 1/2/3 case sets consistent"),
        ("LUMIERE", "NOT_STARTED_BY_CONTRACT", "External validation expressly excluded"),
    ]
    pd.DataFrame(statuses, columns=["task", "status", "evidence_or_note"]).to_csv(root / "INTERNAL_VALIDITY_PATCH_STATUS.csv", index=False)

    metric_sources = [
        (root / "02_target_independent_evaluation/TARGET_INDEPENDENT_METHOD_SUMMARY.csv", "target_independent"),
        (root / "03_no_smoothing_robustness/NO_SMOOTHING_ROBUSTNESS_SUMMARY.csv", "no_smoothing_robustness"),
        (root / "04_layer1_statistical_reaudit/LAYER1_V1_TWO_SIDED_STATISTICS.csv", "layer1_v1"),
        (root / "04_layer1_statistical_reaudit/LAYER1_V1_1_TWO_SIDED_STATISTICS.csv", "layer1_v1_1_sensitivity"),
        (root / "05_layer3_statistical_reaudit/LAYER3A_REAUDITED_STATISTICS.csv", "layer3a"),
        (root / "05_layer3_statistical_reaudit/LAYER3B_REAUDITED_STATISTICS.csv", "layer3b"),
    ]
    pd.concat([tagged(path, label) for path, label in metric_sources], ignore_index=True, sort=False).to_csv(root / "INTERNAL_VALIDITY_PATCH_MASTER_METRICS.csv", index=False)
    paired_sources = [
        (root / "02_target_independent_evaluation/TARGET_INDEPENDENT_PAIRED_STATISTICS.csv", "target_independent"),
        (root / "03_no_smoothing_robustness/NO_SMOOTHING_ROBUSTNESS_PAIRED_STATISTICS.csv", "no_smoothing_absolute"),
        (root / "03_no_smoothing_robustness/NO_SMOOTHING_DIFFERENCE_IN_DIFFERENCES.csv", "no_smoothing_difference_in_differences"),
    ]
    pd.concat([tagged(path, label) for path, label in paired_sources], ignore_index=True, sort=False).to_csv(root / "INTERNAL_VALIDITY_PATCH_PAIRED_STATISTICS.csv", index=False)

    claim_sources = [
        (root / "04_layer1_statistical_reaudit/LAYER1_CLAIM_SUPPORT_MAP.csv", "layer1"),
        (root / "05_layer3_statistical_reaudit/LAYER3_CLAIM_SUPPORT_MAP.csv", "layer3"),
    ]
    pd.concat([tagged(path, label) for path, label in claim_sources], ignore_index=True, sort=False).to_csv(root / "INTERNAL_CLAIM_EVIDENCE_MAP.csv", index=False)
    # The source-of-truth index points to immutable rows; it never rewrites values.
    truth = pd.concat([tagged(path, label) for path, label in metric_sources], ignore_index=True, sort=False)
    truth.to_csv(root / "INTERNAL_NUMERIC_SOURCE_OF_TRUTH.csv", index=False)

    failed = []
    for path in sorted(root.rglob("FAILED_CASES*.csv")):
        frame = pd.read_csv(path)
        if len(frame):
            frame.insert(0, "source_file", str(path)); failed.append(frame)
    (pd.concat(failed, ignore_index=True, sort=False) if failed else pd.DataFrame(columns=["source_file", "case_id", "error"])).to_csv(root / "INTERNAL_VALIDITY_PATCH_FAILED_CASES.csv", index=False)

    manifest_path = root / "INTERNAL_VALIDITY_PATCH_ARTIFACT_MANIFEST.csv"
    rows = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_file() and path != manifest_path and "_download_shard_" not in str(path) and relative.parts[0] != root.name:
            rows.append({"relative_path": str(relative), "size_bytes": path.stat().st_size, "sha256": sha256(path)})
    pd.DataFrame(rows).to_csv(manifest_path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    build(args.output_root)


if __name__ == "__main__":
    main()
