"""Read-only orchestration of final Layer 2R publication outputs.

Purpose
-------
Collect and validate the publication-facing outputs produced by migration
Orders 9, 10, and 12.  The authoritative notebook's final formal workflow
uses one figure per lexicographically sorted locked case followed by the
method-summary and pairwise-summary tables.

Inputs and outputs
------------------
``collect_publication_outputs`` accepts the existing
``Layer2R_publication_rebuild_EIA_v1`` output directory and returns an
immutable ``PublicationOutputs`` inventory.  It reads the locked cohort CSV
to establish figure order and validates the two existing summary tables.

Dependencies
------------
The Python standard library and pandas.  Order 9 must already have rendered
the figures, Order 10 must already have produced the summary tables, and
Order 12 must already have persisted the locked cohort and directory layout.

Scientific assumptions
----------------------
The formal cohort contains exactly 40 unique case identifiers.  Case order is
lexicographic, and pandas' default sorted group-key order is retained in both
summary tables.  No scientific values are calculated or compared here.

Expected behaviour
------------------
The returned figure paths follow locked-case order and retain the notebook's
``Layer2R_formal_<case_id>.png`` naming.  Tables are returned in notebook
publication order: method summary, then pairwise summary.  All source files
remain untouched.

Known limitations
-----------------
The notebook defines no standalone manuscript directory, figure numbering,
copy/link operation, or final formal ZIP package.  This module consequently
does not create any output.  It validates table structure and ordering but
does not recompute or numerically verify their scientific contents.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.statistics.statistics import (
    COMPARATOR_ORDER,
    METHOD_ORDER,
    METHOD_SUMMARY_COLUMNS,
    PAIRWISE_SUMMARY_COLUMNS,
)


LOCKED_CASE_COUNT = 40
FIGURE_NAME_TEMPLATE = "Layer2R_formal_{case_id}.png"
PUBLICATION_TABLE_NAMES = (
    "Layer2R_formal_summary_by_method.csv",
    "Layer2R_formal_pairwise_summary.csv",
)


@dataclass(frozen=True)
class PublicationOutputs:
    """Ordered references to the notebook's publication-facing outputs."""

    output_dir: Path
    case_ids: tuple[str, ...]
    figures: tuple[Path, ...]
    tables: tuple[Path, ...]


def _require_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Missing publication input: {path}")


def _read_locked_cases(path: Path) -> tuple[str, ...]:
    _require_file(path)
    frame = pd.read_csv(path)
    if frame.columns.tolist() != ["case_id"]:
        raise ValueError(
            f"Expected locked case columns ['case_id'], got "
            f"{frame.columns.tolist()}"
        )

    case_ids = frame["case_id"].tolist()
    if len(case_ids) != LOCKED_CASE_COUNT:
        raise ValueError(
            f"Expected {LOCKED_CASE_COUNT} locked cases, got {len(case_ids)}"
        )
    if frame["case_id"].isna().any() or any(
        not isinstance(case_id, str) or not case_id
        for case_id in case_ids
    ):
        raise ValueError("Locked case identifiers must be non-empty strings")
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("Locked case identifiers must be unique")
    if case_ids != sorted(case_ids):
        raise ValueError("Locked cases must use notebook lexicographic order")
    return tuple(case_ids)


def _validate_summary_table(
    path: Path,
    expected_columns: tuple[str, ...],
    order_column: str,
    expected_order: tuple[str, ...],
) -> None:
    _require_file(path)
    frame = pd.read_csv(path)
    if frame.columns.tolist() != list(expected_columns):
        raise ValueError(
            f"Unexpected columns in {path}: {frame.columns.tolist()}"
        )
    values = frame[order_column].tolist()
    if values != list(expected_order):
        raise ValueError(
            f"{path.name} must retain notebook {order_column} ordering"
        )
    if frame["n"].tolist() != [LOCKED_CASE_COUNT] * len(frame):
        raise ValueError(
            f"{path.name} must contain all {LOCKED_CASE_COUNT} locked cases"
        )


def collect_publication_outputs(
    output_dir: str | Path,
) -> PublicationOutputs:
    """Validate and inventory existing final Layer 2R publication outputs.

    This function is deliberately read-only: it does not render figures,
    compute statistics, persist artifacts, copy files, or create packages.
    """
    output = Path(output_dir)
    locked_cases_path = output / "tables" / "locked_40_cases.csv"
    case_ids = _read_locked_cases(locked_cases_path)

    figures = tuple(
        output / "figures" / FIGURE_NAME_TEMPLATE.format(case_id=case_id)
        for case_id in case_ids
    )
    for figure in figures:
        _require_file(figure)

    formal_results = output / "formal_results"
    tables = tuple(formal_results / name for name in PUBLICATION_TABLE_NAMES)
    _validate_summary_table(
        tables[0],
        METHOD_SUMMARY_COLUMNS,
        "method",
        tuple(sorted(METHOD_ORDER)),
    )
    _validate_summary_table(
        tables[1],
        PAIRWISE_SUMMARY_COLUMNS,
        "comparison",
        tuple(sorted(f"PCC vs {method}" for method in COMPARATOR_ORDER)),
    )

    return PublicationOutputs(
        output_dir=output,
        case_ids=case_ids,
        figures=figures,
        tables=tables,
    )
