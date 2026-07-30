"""Dataset identity utilities for the locked PCC longitudinal cohort.

The behavioral authority is the final Layer 2R implementation in notebook
cell 110, with the diagnostic existence report from cell 100.

This module identifies cases and constructs paths only. It does not load or
preprocess MRI data.
"""

from __future__ import annotations

import csv
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import TypeAlias


CaseIdentity: TypeAlias = tuple[str, int, int, str]
RawCasePaths: TypeAlias = dict[str, str | int | Path]
PathValidation: TypeAlias = dict[str, str | bool]

_RAW_FILE_KEYS = ("cur_img", "fut_img", "cur_mask", "fut_mask")


def parse_case_id(case_id: str) -> CaseIdentity:
    """Return patient, current timepoint, future timepoint, and modality."""
    match = re.match(r"(PatientID_\d+)_T(\d+)_to_T(\d+)_(\w+)", case_id)
    if not match:
        raise ValueError(f"Cannot parse case_id: {case_id}")
    patient_id = match.group(1)
    current_timepoint = int(match.group(2))
    future_timepoint = int(match.group(3))
    modality = match.group(4)
    return patient_id, current_timepoint, future_timepoint, modality


def get_raw_paths(case_id: str, raw_root: Path) -> RawCasePaths:
    """Construct the four raw paths used by the final Layer 2R notebook."""
    patient_id, current_timepoint, future_timepoint, modality = parse_case_id(
        case_id
    )

    patient_dir = raw_root / patient_id
    current_dir = patient_dir / f"Timepoint_{current_timepoint}"
    future_dir = patient_dir / f"Timepoint_{future_timepoint}"

    current_image = (
        current_dir
        / f"{patient_id}_Timepoint_{current_timepoint}_brain_{modality}.nii"
    )
    future_image = (
        future_dir
        / f"{patient_id}_Timepoint_{future_timepoint}_brain_{modality}.nii"
    )
    current_mask = (
        current_dir / f"{patient_id}_Timepoint_{current_timepoint}_tumorMask.nii"
    )
    future_mask = (
        future_dir / f"{patient_id}_Timepoint_{future_timepoint}_tumorMask.nii"
    )

    return {
        "case_id": case_id,
        "patient_id": patient_id,
        "cur_tp": current_timepoint,
        "fut_tp": future_timepoint,
        "modality": modality,
        "cur_img": current_image,
        "fut_img": future_image,
        "cur_mask": current_mask,
        "fut_mask": future_mask,
    }


def locked_case_ids(case_ids: Iterable[str]) -> list[str]:
    """Apply the notebook's duplicate removal and deterministic ordering."""
    return sorted(set(case_ids))


def load_locked_case_ids(case_metrics_csv: Path) -> list[str]:
    """Read case IDs from a metrics CSV and return the locked case order."""
    with case_metrics_csv.open(newline="") as csv_file:
        rows = csv.DictReader(csv_file)
        if rows.fieldnames is None or "case_id" not in rows.fieldnames:
            raise KeyError("case_id")
        return locked_case_ids(row["case_id"] for row in rows)


def validate_raw_paths(paths: Mapping[str, object]) -> PathValidation:
    """Return the per-file existence report used by notebook cell 100."""
    row: PathValidation = {"case_id": str(paths["case_id"])}
    all_exist = True

    for key in _RAW_FILE_KEYS:
        path = Path(paths[key])
        exists = path.exists()
        row[key] = str(path)
        row[key + "_exists"] = exists
        if not exists:
            all_exist = False

    row["all_exists"] = all_exist
    return row


def require_raw_paths(paths: Mapping[str, object]) -> None:
    """Raise on the first missing raw file exactly as notebook cell 110."""
    for key in _RAW_FILE_KEYS:
        path = paths[key]
        if not path.exists():
            raise FileNotFoundError(f"Missing {key}: {path}")
