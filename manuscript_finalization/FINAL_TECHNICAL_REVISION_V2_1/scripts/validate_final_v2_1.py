#!/usr/bin/env python3
"""Portable validation for an unpacked PCC manuscript V2.1 package."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import zipfile
from pathlib import Path


def rows(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    required = [
        "01_PCC_SCIENTIFIC_REPORTS_MANUSCRIPT_V2_1.docx",
        "02_PCC_SCIENTIFIC_REPORTS_MANUSCRIPT_V2_1.pdf",
        "03_PCC_SCIENTIFIC_REPORTS_MANUSCRIPT_V2_1.md",
        "04_PCC_SCIENTIFIC_REPORTS_SUPPLEMENT_V2_1.docx",
        "05_PCC_SCIENTIFIC_REPORTS_SUPPLEMENT_V2_1.pdf",
        "06_PCC_SCIENTIFIC_REPORTS_COVER_LETTER_V2_1.docx",
        "07_RESPONSE_TO_ROUND2_INDEPENDENT_AUDIT.md",
        "V2_1_GATE_STATUS.json",
        "NUMERIC_CLAIM_AUDIT_V2_1.csv",
        "SUPPLEMENT_SECTION_GEOMETRY_AUDIT.csv",
        "SUPPLEMENT_CROSS_REFERENCE_AUDIT_V2_1.csv",
        "TABLES_V2_1/Table3_Target_Access_Comparator_Summary.csv",
        "FIGURES_V2_1/Figure1_V2_1.svg",
        "REPRODUCIBILITY_ARCHIVE/LOCKED_COHORT_CLINICAL_METADATA_LINKAGE_V2_1.csv",
    ]
    checks = []
    for name in required:
        checks.append((f"exists:{name}", (root / name).is_file()))
    status = json.loads((root / "V2_1_GATE_STATUS.json").read_text())
    checks.extend([
        ("gate", status.get("V2_1_GATE") == "PASS_FOR_FINAL_INDEPENDENT_ROUND3_REVIEW"),
        ("numeric", all(row["status"] == "PASS" for row in rows(root / "NUMERIC_CLAIM_AUDIT_V2_1.csv"))),
        ("geometry", all(row["status"] == "PASS" for row in rows(root / "SUPPLEMENT_SECTION_GEOMETRY_AUDIT.csv"))),
        ("crossrefs", all(row["status"] == "PASS" for row in rows(root / "SUPPLEMENT_CROSS_REFERENCE_AUDIT_V2_1.csv"))),
        ("metadata_rows", len(rows(root / "REPRODUCIBILITY_ARCHIVE/LOCKED_COHORT_CLINICAL_METADATA_LINKAGE_V2_1.csv")) == 192),
        ("table3_rows", len(rows(root / "TABLES_V2_1/Table3_Target_Access_Comparator_Summary.csv")) == 7),
    ])
    manuscript = (root / "03_PCC_SCIENTIFIC_REPORTS_MANUSCRIPT_V2_1.md").read_text()
    checks.extend([
        ("no_matched_information", "matched-information" not in manuscript.lower()),
        ("formal_name", "Prediction-Comparison-Correction" in manuscript),
        ("target_semantics", "one-sided, segmentation-derived future-added composite foreground target" in manuscript),
        ("no_replacement_glyph", "\ufffd" not in manuscript and "\ufffe" not in manuscript),
    ])
    with zipfile.ZipFile(root / "01_PCC_SCIENTIFIC_REPORTS_MANUSCRIPT_V2_1.docx") as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
    checks.append(("editable_omml_equation", "<m:oMath" in xml))
    failed = [name for name, ok in checks if not ok]
    print(f"ROOT={root}")
    print(f"CHECKS={len(checks)}")
    print(f"FAILED={len(failed)}")
    for name in failed:
        print(f"FAIL:{name}")
    print("PORTABLE_VALIDATION=" + ("PASS" if not failed else "FAIL"))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
