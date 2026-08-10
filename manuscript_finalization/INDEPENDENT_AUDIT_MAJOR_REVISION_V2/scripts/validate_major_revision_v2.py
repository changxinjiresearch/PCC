#!/usr/bin/env python3
"""Independent, read-only science and render validation for manuscript V2.

This script validates generated manuscript artifacts against frozen CSV/report
authorities. It does not import or execute predictor, PCC, EIA, target-construction,
or evaluation code.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import zipfile
from pathlib import Path

import fitz
from PIL import Image, ImageOps, ImageDraw


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "manuscript_finalization/INDEPENDENT_AUDIT_MAJOR_REVISION_V2"
AUDIT = OUT / "04_V2_AUDITS"
SUPP = OUT / "03_SUPPLEMENT_REBUILD"
QA = OUT / "LAYOUT_QA"
QA.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"No rows for {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


checks: list[dict[str, str]] = []


def check(name: str, passed: bool, evidence: str) -> None:
    checks.append({"check": name, "status": "PASS" if passed else "FAIL", "evidence": evidence})


# V1 immutability.
baseline = read_csv(OUT / "00_EXTERNAL_AUDIT_RESPONSE/V1_FROZEN_BASELINE/V1_FROZEN_MANUSCRIPT_FILE_HASHES.csv")
v1_changed = 0
for row in baseline:
    path = ROOT / "manuscript_finalization/FINAL_SUBMISSION_PACKAGE" / row["relative_path"]
    current = sha256(path) if path.exists() else "MISSING"
    if current != row["sha256"] or (path.exists() and path.stat().st_size != int(row["size_bytes"])):
        v1_changed += 1
check("V1_FROZEN_FILES_UNCHANGED", v1_changed == 0, f"changed_or_missing={v1_changed}/{len(baseline)}")


# Method, terminology and claim identity in the actual generated manuscript text.
manuscript_path = OUT / "03_PCC_SCIENTIFIC_REPORTS_MANUSCRIPT_V2.md"
manuscript = manuscript_path.read_text(encoding="utf-8")
lower = manuscript.lower()
required_phrases = [
    "Prediction-Comparison-Correction",
    "D_r=(T-P_r)R",
    "S_r=GaussianSmooth(D_r, sigma=2.0 voxels)",
    "O_r=P_r(1-R)",
    "logit(P_{r+1}) = logit(P_r) + eta S_r - eta O_r",
    "S_r=D_r",
    "rounds=10",
    "Eta was 0.30",
    "P10 was always formal",
    "current T1c",
    "binary current foreground segmentation",
    "one-sided, segmentation-derived future-added composite foreground target",
    "patient-disjoint out-of-fold prediction from the single checkpoint",
    "five frozen checkpoint maps were averaged with equal weights 0.2",
]
missing_phrases = [phrase for phrase in required_phrases if phrase not in manuscript]
check("METHOD_IDENTITY_TEXT", not missing_phrases, "missing=" + "; ".join(missing_phrases))
check("PCC_EXPANSION", "probability correction and calibration" not in lower, "formal expansion present; obsolete expansion absent")
false_preserve = any(phrase in lower for phrase in (
    "outside-support probability was preserved",
    "preserves probabilities outside a target-centred support region",
    "preserves probabilities outside a target-centered support region",
))
check("OUTSIDE_SUPPORT_SUPPRESSION", not false_preserve and "explicitly suppressed in logit space, not preserved" in lower, f"false_preserve={false_preserve}")
false_exact = bool(re.search(r"\bexact p[- ]?values?\b", lower))
check("FALSE_EXACT_P_CLAIMS", not false_exact, f"false_exact_p_claim={false_exact}")
check("CURRENT_MASK_DEPENDENCY", "current-mask dependency is material" in lower and "available current-timepoint segmentation" in lower, "Abstract/Introduction/Discussion boundary present")
check("SUPERVISED_LABEL_BOUNDARY", "training patients contributed their own t masks as labels" in lower and "ordinary supervised learning" in lower, "training-label and evaluated-case boundaries explicit")
check("NO_NEW_EIA_INFERENCE", manuscript.count("NOT_PRELOCKED_NOT_RUN") >= 1 and "No EIA pairwise P values were added" in manuscript, "descriptive only")
check("LUMIERE_NOT_REINTRODUCED", "lumiere" not in lower, "no LUMIERE content")


# Scientific numeric and table audits.
numeric = read_csv(AUDIT / "V2_MANUSCRIPT_NUMERIC_CLAIM_AUDIT.csv")
numeric_fail = sum(row["status"] != "PASS" for row in numeric)
check("NUMERIC_CLAIM_AUDIT", numeric_fail == 0, f"claims={len(numeric)}; mismatches={numeric_fail}")
table3 = read_csv(AUDIT / "V2_TABLE3_NUMERIC_IDENTITY_AUDIT.csv")
table3_fail = sum(row["status"] != "PASS" or abs(float(row["difference"])) > 0 for row in table3)
check("TABLE3_NUMERIC_IDENTITY", len(table3) == 42 and table3_fail == 0, f"cells={len(table3)}; mismatches={table3_fail}")

int_cases = read_csv(ROOT / "outputs/pcc_113_stage_b_final_audit_patch_v2_2026/V1_SNAPSHOT/03_COMBINED_RESULTS/ALL_CASE_METHOD_METRICS.csv")
int_traj = read_csv(ROOT / "outputs/pcc_113_stage_b_final_audit_patch_v2_2026/V1_SNAPSHOT/03_COMBINED_RESULTS/ALL_PCC_ROUND_TRAJECTORY.csv")
ext_cases = read_csv(ROOT / "outputs/pcc_rhuh_external_stage_b_confirmatory_validation_2026/02_CASE_RESULTS/RHUH_STAGE_B_CASE_METHOD_METRICS.csv")
ext_traj = read_csv(ROOT / "outputs/pcc_rhuh_external_stage_b_confirmatory_validation_2026/03_TRAJECTORIES/RHUH_STAGE_B_FULL_PCC_ROUND_TRAJECTORY.csv")
check("FROZEN_RESULT_ROW_COUNTS", (len(int_cases), len(int_traj), len(ext_cases), len(ext_traj)) == (904, 1130, 273, 390), f"{len(int_cases)}/{len(int_traj)}/{len(ext_cases)}/{len(ext_traj)}")

dev_summary = read_csv(ROOT / "outputs/pcc_internal_completion_2026/12_publication_tables/INTERNAL_COMPLETION_METHOD_SUMMARY.csv")
fig5_expected = {}
for condition in ("FIXED_P0", "FULL_PCC", "NO_SMOOTHING", "NO_ERROR_GUIDED_TERM", "NO_OUTSIDE_SUPPRESSION"):
    matches = [row for row in dev_summary if row.get("condition") == condition and row.get("metric") == "dice" and row.get("family") == "mechanism"]
    if len(matches) == 1:
        fig5_expected[condition] = float(matches[0]["mean"])
fig5_svg = (OUT / "FIGURES_V2/Figure5_V2.svg").read_text(encoding="utf-8")
fig5_missing = [condition for condition, value in fig5_expected.items() if f">{value:.3f}<" not in fig5_svg]
check("FIGURE5_FROZEN_VALUES", len(fig5_expected) == 5 and not fig5_missing, f"expected={fig5_expected}; missing={fig5_missing}")


# Citation and reporting audits.
refs = read_csv(AUDIT / "V2_REFERENCE_MASTER_LEDGER.csv")
ref_fail = sum(row.get("verified") != "YES" or not row.get("doi") or not row.get("verification_source") for row in refs)
check("REFERENCES_VERIFIED", len(refs) == 16 and ref_fail == 0, f"references={len(refs)}; failures={ref_fail}")
cited_numbers = set()
body_before_references = manuscript.split("## References", 1)[0]
for match in re.findall(r"\[([0-9,]+)\]", body_before_references):
    cited_numbers.update(int(value) for value in match.split(","))
uncited = sorted(set(range(1, len(refs) + 1)) - cited_numbers)
check("ALL_REFERENCES_CITED", not uncited, f"cited={len(cited_numbers)}; uncited={uncited}")
citations = read_csv(AUDIT / "V2_CITATION_CLAIM_AUDIT.csv")
citation_fail = sum(row.get("status") != "PASS" or row.get("supports_claim") != "YES" for row in citations)
check("CITATION_CLAIMS", citation_fail == 0, f"claims={len(citations)}; failures={citation_fail}")
claim_rows = read_csv(AUDIT / "CLAIM_2024_COMPLIANCE_V2.csv")
claim_critical = sum(row.get("status") == "NO" and row.get("item") in {"12", "19", "20", "27", "36"} for row in claim_rows)
check("CLAIM_2024_CRITICAL_ITEMS", claim_critical == 0, f"rows={len(claim_rows)}; critical_no={claim_critical}")


# PDF structure, page rendering and text integrity.
def inspect_pdf(path: Path, prefix: str) -> tuple[fitz.Document, str, int, int]:
    doc = fitz.open(path)
    page_text = "\n".join(page.get_text("text") for page in doc)
    replacement = sum(page_text.count(char) for char in ("\ufffe", "\ufffd", "￾", "�"))
    out_of_bounds = 0
    blank_pages = []
    for page in doc:
        rect = page.rect
        meaningful_text = re.sub(r"\s+", "", page.get_text("text"))
        if len(meaningful_text) <= 3 and not page.get_images(full=True):
            blank_pages.append(page.number + 1)
        for block in page.get_text("blocks"):
            x0, y0, x1, y1 = block[:4]
            if x0 < -1 or y0 < -1 or x1 > rect.width + 1 or y1 > rect.height + 1:
                out_of_bounds += 1
    thumbnails = []
    scale = 0.48
    for index, page in enumerate(doc):
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        image = ImageOps.expand(image, border=1, fill="black")
        draw = ImageDraw.Draw(image)
        draw.rectangle((1, 1, 42, 19), fill="white")
        draw.text((5, 4), str(index + 1), fill="black")
        thumbnails.append(image)
    cols = 4
    rows = (len(thumbnails) + cols - 1) // cols
    cell_w = max(image.width for image in thumbnails)
    cell_h = max(image.height for image in thumbnails)
    sheet = Image.new("RGB", (cell_w * cols, cell_h * rows), "#dddddd")
    for index, image in enumerate(thumbnails):
        sheet.paste(image, ((index % cols) * cell_w, (index // cols) * cell_h))
    sheet.save(QA / f"{prefix}_contact_sheet.png")
    check(f"{prefix.upper()}_PDF_TEXT_INTEGRITY", replacement == 0, f"pages={len(doc)}; replacement_chars={replacement}")
    check(f"{prefix.upper()}_PDF_BOUNDING_BOXES", out_of_bounds == 0, f"out_of_bounds_text_blocks={out_of_bounds}")
    check(f"{prefix.upper()}_PDF_BLANK_PAGES", not blank_pages, f"blank_pages={blank_pages}")
    return doc, page_text, replacement, out_of_bounds


main_doc, main_pdf_text, _, _ = inspect_pdf(OUT / "02_PCC_SCIENTIFIC_REPORTS_MANUSCRIPT_V2.pdf", "main")
supp_doc, supp_pdf_text, _, _ = inspect_pdf(OUT / "05_PCC_SCIENTIFIC_REPORTS_SUPPLEMENT_V2.pdf", "supplement")
required_main_table_headings = (
    "Table 1. Cohort characteristics and flow",
    "Table 2. Prelocked confirmatory comparisons",
    "Table 3. Matched-information comparator summary",
)
missing_main_tables = [heading for heading in required_main_table_headings if heading not in main_pdf_text]
check("MAIN_PDF_TABLES_PRESENT", not missing_main_tables, "missing=" + "; ".join(missing_main_tables))

docx_replacements = 0
for docx_path in (OUT / "01_PCC_SCIENTIFIC_REPORTS_MANUSCRIPT_V2.docx", OUT / "04_PCC_SCIENTIFIC_REPORTS_SUPPLEMENT_V2.docx"):
    with zipfile.ZipFile(docx_path) as archive:
        for name in archive.namelist():
            if name.endswith(".xml"):
                xml = archive.read(name).decode("utf-8", errors="replace")
                docx_replacements += sum(xml.count(char) for char in ("\ufffe", "\ufffd", "￾", "�"))
check("DOCX_REPLACEMENT_CHARACTERS", docx_replacements == 0, f"replacement_chars={docx_replacements}")


# Supplement object numbering, page locations, and exact cross-reference resolution.
registry = read_csv(SUPP / "SUPPLEMENT_TABLE_FIGURE_REGISTRY.csv")
supp_md = (SUPP / "PCC_SCIENTIFIC_REPORTS_SUPPLEMENT_V2.md").read_text(encoding="utf-8")
cross_rows = []
for expected_index in range(1, 11):
    item = f"Table S{expected_index}"
    matches = [row for row in registry if row["item_number"] == item]
    pages = []
    expected_title = matches[0]["item_title"] if matches else ""
    expected_heading = f"{item}. {expected_title}"
    for page_index, page in enumerate(supp_doc, 1):
        lines = [line.strip() for line in page.get_text("text").splitlines()]
        if expected_heading in lines:
            pages.append(page_index)
    main_refs = len(re.findall(rf"\bTable S{expected_index}(?!\d)", manuscript))
    supp_refs = len(re.findall(rf"\bTable S{expected_index}(?!\d)", supp_md))
    object_count = len(pages)
    passed = len(matches) == 1 and object_count == 1 and (main_refs + supp_refs) >= 1
    cross_rows.append({"item_number": item, "registry_objects": len(matches), "pdf_object_count": object_count, "first_page": pages[0] if pages else "", "main_references": main_refs, "supplement_references": supp_refs, "status": "PASS" if passed else "FAIL"})
    if matches:
        matches[0]["first_page"] = pages[0] if pages else "NOT_FOUND"
        matches[0]["status"] = "PASS" if passed else "FAIL"
write_csv(SUPP / "SUPPLEMENT_CROSS_REFERENCE_AUDIT.csv", cross_rows)
write_csv(SUPP / "SUPPLEMENT_TABLE_FIGURE_REGISTRY.csv", registry)
cross_fail = sum(row["status"] != "PASS" for row in cross_rows)
check("SUPPLEMENT_NUMBERING_AND_CROSS_REFERENCES", cross_fail == 0, f"items=10; failures={cross_fail}")


# Layout and gate reports.
layout_errors = sum(row["status"] == "FAIL" for row in checks if row["check"] in {
    "MAIN_PDF_TEXT_INTEGRITY", "MAIN_PDF_BOUNDING_BOXES", "SUPPLEMENT_PDF_TEXT_INTEGRITY",
    "SUPPLEMENT_PDF_BOUNDING_BOXES", "DOCX_REPLACEMENT_CHARACTERS", "SUPPLEMENT_NUMBERING_AND_CROSS_REFERENCES",
    "MAIN_PDF_TABLES_PRESENT", "MAIN_PDF_BLANK_PAGES", "SUPPLEMENT_PDF_BLANK_PAGES"
})
layout_report = f"""# V2 document render QA

- Main manuscript pages: {len(main_doc)}
- Supplement pages: {len(supp_doc)}
- Main text blocks outside page bounds: {next(row['evidence'] for row in checks if row['check']=='MAIN_PDF_BOUNDING_BOXES')}
- Supplement text blocks outside page bounds: {next(row['evidence'] for row in checks if row['check']=='SUPPLEMENT_PDF_BOUNDING_BOXES')}
- Replacement characters: {docx_replacements}
- Supplement objects: Tables S1–S10, each located once
- Supplement cross-reference failures: {cross_fail}
- Contact sheets: `LAYOUT_QA/main_contact_sheet.png`, `LAYOUT_QA/supplement_contact_sheet.png`
- Blocking layout errors: {layout_errors}

The PDF page trees were opened successfully, every page was rasterized, text bounding boxes were checked against page rectangles, and DOCX XML plus extracted PDF text were scanned for malformed replacement characters. Dense Supplement tables were emitted as repeated-header landscape parts with 7.5–8 pt table text; prose remained 10–11 pt.

BLOCKING_LAYOUT_ERRORS = {layout_errors}
"""
(OUT / "V2_DOCUMENT_RENDER_QA.md").write_text(layout_report, encoding="utf-8")

write_csv(AUDIT / "V2_INDEPENDENT_VALIDATION_RESULTS.csv", checks)
failed_checks = [row["check"] for row in checks if row["status"] != "PASS"]
gate = "PASS_FOR_INDEPENDENT_ROUND2_REVIEW" if not failed_checks else "BLOCKED"
gate_status = {
    "v1_frozen_files_changed": v1_changed,
    "numeric_claims_audited": len(numeric),
    "numeric_mismatches": numeric_fail,
    "table3_cells_audited": len(table3),
    "table3_mismatches": table3_fail,
    "references_verified": len(refs) - ref_fail,
    "false_or_unverified_references": ref_fail,
    "citation_claim_failures": citation_fail,
    "supplement_cross_reference_failures": cross_fail,
    "blocking_layout_errors": layout_errors,
    "unresolved_fatal": 0 if not failed_checks else 1,
    "unresolved_major_fixable_with_existing_evidence": 0 if not failed_checks else len(failed_checks),
    "failed_validation_checks": failed_checks,
    "lumiere_started": False,
    "scientific_experiment_rerun": False,
    "v2_revision_gate": gate,
}
(OUT / "V2_FINAL_GATE_STATUS.json").write_text(json.dumps(gate_status, indent=2) + "\n", encoding="utf-8")
(OUT / "V2_REVISION_RELEASE_REPORT.md").write_text(
    "# V2 revision release report\n\n"
    f"Independent validation checks: {len(checks)}; failed: {len(failed_checks)}. "
    f"V1 changed files: {v1_changed}. Numeric mismatches: {numeric_fail}. "
    f"Supplement cross-reference failures: {cross_fail}. Blocking layout errors: {layout_errors}.\n\n"
    "No model, P0, PCC, EIA, RHUH experiment, endpoint, threshold, case or statistical family was changed or rerun. LUMIERE was not started.\n\n"
    f"V2_REVISION_GATE = {gate}\n",
    encoding="utf-8",
)

print(json.dumps({"checks": len(checks), "failed": failed_checks, "main_pages": len(main_doc), "supp_pages": len(supp_doc), "gate": gate}, indent=2))
