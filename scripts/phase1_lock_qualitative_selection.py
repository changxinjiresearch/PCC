"""Create the Phase 1 qualitative selection lock from frozen CSV authorities.

This is selection-only. It reads existing metrics, performs the predeclared
distance-to-frozen-median rule, and writes audit metadata. It does not read
image voxels, run a model, construct a target, execute PCC, or calculate a
scientific performance endpoint.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path.cwd()
OUT = ROOT / "pre_submission_anti_major_2026" / "phase1_zero_risk_high_yield_submission_hardening"
SNAP = Path("/home/changxinjiresearch/pre_phase0_snapshots/pcc_repo_snapshot_20260811/worktree")
LOCK = OUT / "PHASE1_QUALITATIVE_CASE_SELECTION_LOCK.yaml"
TIMESTAMP = "2026-08-11T05:30:59Z"
TAG = "pcc-v2.1.1-science-freeze-20260811"

INTERNAL_METRICS = ROOT / "outputs/pcc_113_stage_b_confirmatory_validation_2026_recovery_v2/03_COMBINED_RESULTS/ALL_CASE_METHOD_METRICS.csv"
INTERNAL_STATS = ROOT / "outputs/pcc_113_stage_b_confirmatory_validation_2026_recovery_v2/04_STATISTICS/CONFIRMATORY_STATISTICS.csv"
RHUH_METRICS = ROOT / "outputs/pcc_rhuh_external_stage_b_confirmatory_validation_2026/02_CASE_RESULTS/RHUH_STAGE_B_CASE_METHOD_METRICS.csv"
RHUH_STATS = ROOT / "outputs/pcc_rhuh_external_stage_b_confirmatory_validation_2026/06_CONFIRMATORY_STATISTICS/RHUH_STAGE_B_CONFIRMATORY_STATISTICS.csv"
CASE_C_AUTHORITY = ROOT / "outputs/pcc_113_stage_b_final_audit_patch_v2_2026/04_PACKAGE_AUDIT/FULL_PCC_TRAJECTORY_INTEGRITY_V2.md"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def select_typical(metrics_path: Path, stats_path: Path) -> tuple[dict, list[dict]]:
    metrics = read_csv(metrics_path)
    per_case: dict[str, dict[str, str | float]] = {}
    for row in metrics:
        if row["method"] not in {"Fixed", "Full PCC"}:
            continue
        case = per_case.setdefault(row["case_id"], {"patient_id": row["patient_id"]})
        case[row["method"]] = float(row["Dice_0.5"])

    h1 = next(row for row in read_csv(stats_path) if row["comparison"] == "Full PCC vs Fixed")
    median = float(h1["median_difference"])
    candidates = []
    for case_id, values in per_case.items():
        improvement = float(values["Full PCC"]) - float(values["Fixed"])
        candidates.append({
            "patient_id": values["patient_id"],
            "case_id": case_id,
            "Fixed_Dice_0.5": format(float(values["Fixed"]), ".17g"),
            "Full_PCC_Dice_0.5": format(float(values["Full PCC"]), ".17g"),
            "improvement": format(improvement, ".17g"),
            "frozen_cohort_median_improvement": format(median, ".17g"),
            "absolute_distance_to_median": format(abs(improvement - median), ".17g"),
        })
    candidates.sort(key=lambda r: (float(r["absolute_distance_to_median"]), str(r["case_id"])))
    selected = candidates[0].copy()
    selected["exact_distance_tie_count"] = sum(
        float(row["absolute_distance_to_median"]) == float(selected["absolute_distance_to_median"])
        for row in candidates
    )
    selected["tie_break_applied"] = selected["exact_distance_tie_count"] > 1
    return selected, candidates


OUT.mkdir(parents=True, exist_ok=True)
internal, internal_candidates = select_typical(INTERNAL_METRICS, INTERNAL_STATS)
rhuh, rhuh_candidates = select_typical(RHUH_METRICS, RHUH_STATS)

case_c_text = CASE_C_AUTHORITY.read_text(encoding="utf-8")
case_c = "PatientID_0242_T1_to_T3_t1c"
if case_c not in case_c_text or "P9-to-P10 decline" not in case_c_text:
    raise RuntimeError("Frozen authority does not uniquely confirm Case C")

candidate_path = OUT / "PHASE1_QUALITATIVE_SELECTION_CANDIDATES.csv"
with candidate_path.open("w", newline="", encoding="utf-8") as stream:
    fields = ["cohort", *internal_candidates[0].keys()]
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for cohort, rows in (("Internal 113", internal_candidates), ("RHUH 39", rhuh_candidates)):
        for row in rows:
            writer.writerow({"cohort": cohort, **row})

lock_text = f"""phase: PCC_PRE_SUBMISSION_ANTI_MAJOR_PHASE1
selection_timestamp_utc: {TIMESTAMP}
science_freeze_tag: {TAG}
source_frozen_metric_files:
  internal_case_metrics:
    path: {INTERNAL_METRICS.relative_to(ROOT)}
    sha256: {digest(INTERNAL_METRICS)}
  internal_confirmatory_statistics:
    path: {INTERNAL_STATS.relative_to(ROOT)}
    sha256: {digest(INTERNAL_STATS)}
  rhuh_case_metrics:
    path: {RHUH_METRICS.relative_to(ROOT)}
    sha256: {digest(RHUH_METRICS)}
  rhuh_confirmatory_statistics:
    path: {RHUH_STATS.relative_to(ROOT)}
    sha256: {digest(RHUH_STATS)}
  case_c_trajectory_authority:
    path: {CASE_C_AUTHORITY.relative_to(ROOT)}
    sha256: {digest(CASE_C_AUTHORITY)}
case_A:
  cohort: Internal 113
  rule: argmin absolute distance between patient Full_PCC_minus_Fixed Dice_0.5 and frozen cohort median improvement
  selected_patient_id: {internal['patient_id']}
  selected_case_id: {internal['case_id']}
  frozen_median_improvement: {internal['frozen_cohort_median_improvement']}
  selected_improvement: {internal['improvement']}
  absolute_distance: {internal['absolute_distance_to_median']}
  exact_distance_tie_count: {internal['exact_distance_tie_count']}
  tie_break_applied: {str(internal['tie_break_applied']).lower()}
case_B:
  cohort: RHUH 39
  rule: argmin absolute distance between patient Full_PCC_minus_Fixed Dice_0.5 and frozen cohort median improvement
  selected_patient_id: {rhuh['patient_id']}
  selected_case_id: {rhuh['case_id']}
  frozen_median_improvement: {rhuh['frozen_cohort_median_improvement']}
  selected_improvement: {rhuh['improvement']}
  absolute_distance: {rhuh['absolute_distance_to_median']}
  exact_distance_tie_count: {rhuh['exact_distance_tie_count']}
  tie_break_applied: {str(rhuh['tie_break_applied']).lower()}
case_C:
  cohort: Internal 113
  rule: use the uniquely frozen P9-to-P10 degradation case; only if unavailable use the unique RHUH No-smoothing loss case
  selected_patient_id: PatientID_0242
  selected_case_id: {case_c}
  authority_status: UNIQUE_EXACT_IDENTITY_RECOVERED
tie_breaking_rules:
  case_selection: case_id ASCII_lexicographic_ascending
  axial_slice: smallest_slice_index
slice_selection_rule: argmax axial future-added-target foreground voxel count; ties choose smallest slice index
display_columns:
  - Current T1c
  - Current mask
  - Frozen P0
  - Future-added target
  - Full PCC P10
  - No-smoothing P10
normalization_rule: per-volume deterministic p1/p99 window over finite nonzero current-T1c voxels; clip to [0,1]; identical rule for every case
probability_scale: fixed_0_to_1_for_all_probability_maps
crop_rule: fixed full 240x240 axial field; no patient-specific crop
output_resolution: 2400x1200_pixels_target_if_rendered
post_lock_case_change_allowed: false
post_lock_slice_change_allowed: false
scientific_inference_from_figure: prohibited
"""
if LOCK.exists() and LOCK.read_text(encoding="utf-8") != lock_text:
    raise RuntimeError("Selection lock already exists with different contents")
LOCK.write_text(lock_text, encoding="utf-8")
(OUT / "PHASE1_QUALITATIVE_CASE_SELECTION_LOCK.yaml.sha256").write_text(
    f"{digest(LOCK)}  {LOCK.name}\n", encoding="utf-8"
)

# This availability audit uses filenames only. It deliberately does not load
# NIfTI or NumPy arrays and does not reconstruct any method map.
rows = []
for label, dataset, patient, case_id in (
    ("A", "MU Internal 113", str(internal["patient_id"]), str(internal["case_id"])),
    ("B", "RHUH external 39", str(rhuh["patient_id"]), str(rhuh["case_id"])),
    ("C", "MU Internal 113", "PatientID_0242", case_c),
):
    names = [p for p in SNAP.rglob("*") if p.is_file() and patient in p.name]
    p0 = [p for p in names if p.suffix == ".npy" and "p0" in p.name.lower()]
    full = [p for p in names if p.suffix == ".npy" and "full" in p.name.lower() and "pcc" in p.name.lower()]
    nosmooth = [p for p in names if p.suffix == ".npy" and ("nosmooth" in p.name.lower() or "no_smoothing" in p.name.lower())]
    rows.append({
        "case": label,
        "dataset": dataset,
        "patient_id": patient,
        "case_id": case_id,
        "selection_reason": "mechanical typical case" if label in {"A", "B"} else "frozen P9-to-P10 degradation case",
        "slice_index": "NOT_COMPUTED_MISSING_FROZEN_MAP_SET",
        "source_image": "PRESENT_IN_PRESERVED_SOURCE" if any("t1c" in p.name.lower() and (p.name.endswith(".nii") or p.name.endswith(".nii.gz")) for p in names) else "REMOTE_OR_NOT_LOCAL",
        "source_mask": "PRESENT_PARTIAL_OR_COMPLETE_IN_PRESERVED_SOURCE" if any("mask" in p.name.lower() or "segmentation" in p.name.lower() for p in names) else "REMOTE_OR_NOT_LOCAL",
        "P0_source": str(p0[0]) if len(p0) == 1 else "MISSING_LOCAL_FROZEN_P0_MAP",
        "PCC_source": str(full[0]) if len(full) == 1 else "MISSING_FROZEN_FULL_PCC_P10_MAP",
        "No_smoothing_source": str(nosmooth[0]) if len(nosmooth) == 1 else "MISSING_FROZEN_NO_SMOOTHING_P10_MAP",
        "source_hashes": "NOT_APPLICABLE_MISSING_COMPLETE_MAP_SET",
        "render_status": "HOLD_MISSING_FROZEN_ARTIFACT",
    })

prov = OUT / "PHASE1_QUALITATIVE_PANEL_PROVENANCE.csv"
with prov.open("w", newline="", encoding="utf-8") as stream:
    writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

(OUT / "PHASE1_QUALITATIVE_MRI_PANEL_CAPTION.md").write_text(
    """# Qualitative MRI panel caption — locked draft

Cases were selected mechanically from frozen outcomes: the internal and RHUH cases minimize absolute distance from their respective frozen median Full PCC-minus-Fixed Dice@0.5 improvement, and the edge case is the uniquely documented internal P9-to-P10 degradation case. The locked slice rule is the axial slice with maximal future-added-target foreground area, with the smallest index resolving ties. Future data are used only for retrospective target construction and visualization; this is not deployment-time inference. The panel is not used for statistical inference.

Rendering status: **HOLD_MISSING_FROZEN_ARTIFACT**. The required frozen Full PCC P10 and No-smoothing P10 probability maps were not found locally. They were intentionally not retained in the Stage B release. Phase 1 did not reconstruct them because doing so would execute PCC, which this protocol forbids.
""",
    encoding="utf-8",
)

print(f"lock={LOCK}")
print(f"lock_sha256={digest(LOCK)}")
print(f"case_A={internal['case_id']}")
print(f"case_B={rhuh['case_id']}")
print(f"case_C={case_c}")
print("panel_status=HOLD_MISSING_FROZEN_ARTIFACT")
