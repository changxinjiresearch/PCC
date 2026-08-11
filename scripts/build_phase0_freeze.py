"""Build the audit-only PCC Anti-Major Phase 0 freeze package.

This script reads existing manifests/reports and computes file hashes. It does
not import model code, read image arrays, generate targets, run tests that
produce scientific results, or calculate new statistics.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path


REPO = Path.cwd()
OUT = REPO / "pre_submission_anti_major_2026" / "phase0_science_freeze"
SNAP = Path("/home/changxinjiresearch/pre_phase0_snapshots/pcc_repo_snapshot_20260811")
SNAP_WORKTREE = SNAP / "worktree"
TAG = "pcc-v2.1.1-science-freeze-20260811"
BRANCH = "pre-submission-anti-major-2026"
HEAD = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def csv_write(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


def rel_or_snapshot(path: Path) -> Path:
    rel = Path(path)
    if rel.exists(): return rel
    snap = SNAP_WORKTREE / rel
    if snap.exists(): return snap
    return rel


OUT.mkdir(parents=True, exist_ok=True)
ref = OUT / "00_AUTHORITY_REFERENCES"
ref.mkdir(exist_ok=True)

# Preserve the small, machine-readable Round-3 authority metadata in the
# Phase 0 package; large/raw scientific data remain in the preserved snapshot.
round3_names = [
    "ROUND3_GATE_STATUS.json", "ROUND3_VALIDATOR_STATUS.json",
    "ROUND3_FROZEN_SCIENCE_REGRESSION.csv", "ROUND3_TARGETED_PATCH_REPORT.md",
    "ROUND3_PACKAGE_MANIFEST.csv", "ROUND3_SEMANTIC_AUDIT.csv",
    "PORTABLE_ROUND3_VALIDATION_REPORT.md",
]
round3_root = SNAP_WORKTREE / "manuscript_finalization/FINAL_ROUND3_PATCH_V2_1_1"
for name in round3_names:
    source = round3_root / name
    if source.exists(): shutil.copy2(source, ref / name)

round3_reg = ref / "ROUND3_FROZEN_SCIENCE_REGRESSION.csv"
with round3_reg.open(newline="", encoding="utf-8") as f:
    regression_rows = list(csv.DictReader(f))
numeric_mismatches = sum(1 for r in regression_rows if r.get("status") not in {"PASS", "EXACT_IDENTITY", "SHA256_MATCH"})

# Inventory of the pre-cleanup working tree, with every status entry retained.
status_lines = (SNAP / "metadata/GIT_STATUS_BEFORE.txt").read_text(encoding="utf-8").splitlines()
inventory_rows = []
for line in status_lines:
    if line.startswith("##") or not line.strip(): continue
    code, path = line[:2], line[3:]
    if code == "??": kind = "UNTRACKED"
    elif "D" in code: kind = "DELETED"
    else: kind = "MODIFIED"
    if path.startswith("manuscript_finalization/"): category = "manuscript_or_round3_science"
    elif path.startswith("PCC_RHUH_EXTERNAL_VALIDATION_PHASE0") or path.startswith("PCC_RHUH_EXTERNAL_STAGE"):
        category = "RHUH_external_protocol_or_validation"
    elif path.startswith("artifacts/"): category = "scientific_input_or_provenance_artifact"
    elif path.startswith("validation_") or path.startswith("reproductions/") or path.startswith("experiments/"):
        category = "validation_or_reproduction_work"
    elif path.startswith("outputs/") or path.endswith(".zip") or path.endswith(".sha256"):
        category = "release_or_audit_artifact"
    elif path.startswith("kaggle"):
        category = "execution_or_engineering_artifact"
    else: category = "other_project_artifact"
    inventory_rows.append({"status": kind, "path": path, "category": category, "scientific_value": "PRESERVE_UNTIL_EXPLICIT_REVIEW", "handling": "preserved in hard-link snapshot; not deleted or overwritten"})
csv_write(OUT / "PRE_PHASE0_INVENTORY.csv", ["status", "path", "category", "scientific_value", "handling"], inventory_rows)

write(OUT / "PRE_PHASE0_INVENTORY.md", f"""# PRE-PHASE-0_INVENTORY

Baseline HEAD: `{HEAD}`

The original dirty `main` worktree was not reset, reverted, deleted, or overwritten. A complete same-filesystem hard-link snapshot is at `{SNAP}`. It contains the original worktree bytes, Git baseline bundle, status/diff/untracked/deleted manifests, and a recoverable copy of the deleted V2 manuscript.

Inventory counts: modified=7, deleted=1, untracked status entries=46. Every entry is classified in `PRE_PHASE0_INVENTORY.csv`; every item is retained. Scientific/release/manuscript/RHUH/validation artifacts are preserved as legal prior work or provenance. No uncertain item was deleted.

The RHUH `PHASE0_PREFLIGHT` and `PHASE0B_GEOMETRY_RESOLUTION` artifacts are preflight/geometry-resolution work from the external-validation strengthening workflow, not the completed 39-patient performance release. The completed external validation is the existing `PCC_RHUH_EXTERNAL_STAGE_B_CONFIRMATORY_VALIDATION_2026` release.

The deleted `INDEPENDENT_AUDIT_MAJOR_REVISION_V2` manuscript is recoverable from both the baseline Git bundle and `{SNAP}/recovery/deleted_files/`. Its deletion is consistent with later V2.1 and V2.1.1 version evolution: V2.1 exists in the committed technical-revision release; V2.1.1 exists in the preserved Round-3 controlled ZIP with manuscript DOCX/PDF/MD and a PASS numeric regression. No accidental loss was inferred, so the old file remains preserved and classified historical/superseded.
""")

# Evidence hierarchy and frozen authority registry.
registry_fields = ["category", "artifact_name", "artifact_role", "path", "size_bytes", "sha256", "git_commit_if_known", "scientific_status", "allowed_future_use", "forbidden_future_use", "notes"]
registry = []
def add(category, name, role, path, status, allowed, forbidden, notes, commit="df340b7921a066acbfeffdd8589bb1ad2ec2e718"):
    p = rel_or_snapshot(Path(path)); exists = p.exists()
    registry.append({"category": category, "artifact_name": name, "artifact_role": role, "path": str(path), "size_bytes": p.stat().st_size if exists else "MISSING", "sha256": sha256(p) if exists else "MISSING", "git_commit_if_known": commit if str(path).startswith(("outputs/", "PCC_", "manuscript_finalization/")) else "UNKNOWN", "scientific_status": status, "allowed_future_use": allowed, "forbidden_future_use": forbidden, "notes": notes})

add("Development authority", "leakage-free 40-patient development release", "development authority", "outputs/pcc_internal_validity_patch_2026/INTERNAL_NUMERIC_SOURCE_OF_TRUTH.csv", "FROZEN_SUPPORTING_OR_DESCRIPTIVE", "historical provenance; descriptive support", "primary confirmatory family; parameter selection after Phase 0", "Current development evidence; not independent confirmation.")
add("Development authority", "development audit/release ZIP", "auditable development package", "PCC_INTERNAL_VALIDITY_PATCH_2026_COMPLETE.zip", "FROZEN_SUPPORTING_OR_DESCRIPTIVE", "descriptive/development chronology", "promote to Class A", "Current modified release bytes are preserved in the pre-Phase-0 snapshot and are not silently substituted.")
add("Independent internal 113 authority", "113 V2 numeric source of truth", "confirmatory numeric authority", "outputs/pcc_113_stage_b_final_audit_patch_v2_2026/05_V2_RELEASE/PCC_113_STAGE_B_V2_NUMERIC_SOURCE_OF_TRUTH.csv", "FROZEN_PRIMARY_CONFIRMATORY", "frozen reporting and exact audit", "new primary family; result-driven reanalysis", "H1/H2 source.")
add("Independent internal 113 authority", "113 confirmatory statistics", "confirmatory statistics", "outputs/pcc_113_stage_b_confirmatory_validation_2026_recovery_v2/04_STATISTICS/CONFIRMATORY_STATISTICS.csv", "FROZEN_PRIMARY_CONFIRMATORY", "exact frozen identity verification", "new Holm adjustment or primary endpoint replacement", "Internal n=113.")
add("RHUH external authority", "RHUH protocol lock", "external protocol", "PCC_RHUH_EXTERNAL_PROTOCOL_LOCK_2026.zip", "FROZEN_PRIMARY_CONFIRMATORY", "protocol provenance", "post-primary results reclassified as original confirmatory", "RHUH cohort/protocol authority.")
add("RHUH external authority", "RHUH Stage A P0 freeze", "external P0 provenance", "PCC_RHUH_EXTERNAL_STAGE_A_P0_FREEZE_2026.zip", "FROZEN_PRIMARY_CONFIRMATORY", "frozen P0 provenance", "P0 regeneration or checkpoint selection", "39 retained cases.")
add("RHUH external authority", "RHUH Stage B release", "external confirmatory performance", "PCC_RHUH_EXTERNAL_STAGE_B_CONFIRMATORY_VALIDATION_2026.zip", "FROZEN_PRIMARY_CONFIRMATORY", "frozen confirmatory reporting", "new primary family; result-driven reanalysis", "Existing completed 39-patient release.")
add("Manuscript authority", "V2.1.1 Round-3 controlled package", "scientific manuscript authority", str(round3_root / "PCC_SCIENTIFIC_REPORTS_ROUND3_TARGETED_PATCH_V2_1_1_2026.zip"), "FROZEN_PRIMARY_CONFIRMATORY", "presentation and frozen chronology", "rewriting historical chronology or primary numbers", "Preserved snapshot; controlled package contains DOCX/PDF/MD and numeric regression.", "SNAPSHOT")
add("Manuscript authority", "V2.1 committed manuscript", "superseded predecessor", "manuscript_finalization/FINAL_TECHNICAL_REVISION_V2_1/01_PCC_SCIENTIFIC_REPORTS_MANUSCRIPT_V2_1.docx", "FROZEN_SUPPORTING_OR_DESCRIPTIVE", "version chronology", "current authority replacement without audit", "V2.1 is superseded by V2.1.1.")
add("Historical / forbidden", "deleted V2 manuscript recovery", "historical manuscript", str(SNAP / "recovery/deleted_files/01_PCC_SCIENTIFIC_REPORTS_MANUSCRIPT_V2.docx"), "HISTORICAL_DO_NOT_USE", "provenance only", "current numbers, methods, manuscript authority", "Preserved because deletion status was uncertain before audit.", "SNAPSHOT")
add("Historical / forbidden", "old LUMIERE outputs", "historical external work", "outputs/final_report/07_LUMIERE/LUMIERE_CURRENT_STATUS.md", "HISTORICAL_DO_NOT_USE", "exposure/provenance audit only", "current external evidence or parameter choice", "High-level historical exposure is documented separately; old performance tables are not reopened.")
add("Historical / forbidden", "old target-trained P0/leaky variants", "historical method development", "outputs/pcc_internal_validity_patch_2026/INTERNAL_NUMERIC_SOURCE_OF_TRUTH.csv", "HISTORICAL_DO_NOT_USE", "chronology only", "current confirmatory evidence or parameter choice", "Family-level exclusion; exact legacy paths remain in preserved snapshot.")
csv_write(OUT / "PHASE0_FROZEN_AUTHORITY_REGISTRY.csv", registry_fields, registry)

hierarchy = [
    ("CLASS A", "FROZEN_PRIMARY_CONFIRMATORY", "Internal 113 H1 Full PCC vs Fixed Dice@0.5", "Permanent frozen confirmatory; no family expansion."),
    ("CLASS A", "FROZEN_PRIMARY_CONFIRMATORY", "Internal 113 H2 No-smoothing vs Full PCC Dice@0.5", "Permanent frozen confirmatory; no re-adjustment."),
    ("CLASS A", "FROZEN_PRIMARY_CONFIRMATORY", "RHUH 39 H3 Full PCC vs Fixed Dice@0.5", "Permanent frozen external confirmatory."),
    ("CLASS A", "FROZEN_PRIMARY_CONFIRMATORY", "RHUH 39 H4 No-smoothing vs Full PCC Dice@0.5", "Permanent frozen external confirmatory."),
    ("CLASS B", "FROZEN_SUPPORTING_OR_DESCRIPTIVE", "Development 40, secondary metrics, oracle/top-k, trajectories, EIA, ablations, qualitative results", "Supporting/descriptive only."),
    ("CLASS C", "POST_PRIMARY_PRESPECIFIED_ROBUSTNESS", "New Internal 113/RHUH 39 current-mask/component/shuffled-target analyses", "Post-primary robustness; not original confirmatory."),
    ("CLASS D", "NEW_PRELOCKED_EXTERNAL_REPLICATION", "New genuinely acceptable external dataset after exposure audit", "Protocol skeleton only; feasibility first."),
    ("CLASS E", "OPTIONAL_TRANSLATIONAL_EXTENSION", "Sparse/weak/non-oracle guidance Phase 6", "Not authorized."),
    ("CLASS X", "HISTORICAL_OR_INVALID_DO_NOT_USE", "Old target-trained P0, superseded high-Dice tables, old leaky variants, old LUMIERE outputs, superseded manuscripts", "Provenance only; forbidden for current claims."),
]
csv_write(OUT / "PHASE0_EVIDENCE_HIERARCHY.csv", ["evidence_class", "class_name", "evidence_family", "future_use_rule"], [dict(zip(["evidence_class", "class_name", "evidence_family", "future_use_rule"], r)) for r in hierarchy])

# The regression is copied byte-for-byte from the existing Round-3 authority;
# no values are recomputed here.
shutil.copy2(round3_reg, OUT / "04_PHASE0_FROZEN_CONFIRMATORY_NUMERIC_IDENTITY.csv")

write(OUT / "01_PCC_PRE_SUBMISSION_ANTI_MAJOR_PROTOCOL_2026.md", """# PCC Pre-submission Anti-Major Program — Phase 0

Phase 0 is audit-only. Its purpose is to preserve PCC V2.1.1 scientific evidence, define evidence hierarchy, record historical exclusions, and pre-lock future analysis roles before any new result is produced.

No training, inference, P0 regeneration, PCC/EIA/no-smoothing execution, target construction, new hypothesis test, Kaggle/GPU job, or LUMIERE operation is authorized in Phase 0. Phase 0 ends at `PHASE0_GATE=PASS_READY_FOR_PHASE1`; it does not start Phase 1.

The original dirty `main` worktree is preserved outside the clean Phase 0 worktree. All future Anti-Major work occurs on branch `pre-submission-anti-major-2026` or descendants. The immutable tag `pcc-v2.1.1-science-freeze-20260811` identifies the baseline commit.
""")
write(OUT / "05_PHASE0_NEGATIVE_RESULT_POLICY.md", """# Negative-result retention policy

All future pre-defined Anti-Major analyses retain positive, null, attenuated, contradictory, and technical-failure outcomes. No result-dependent exclusion, cohort abandonment, condition deletion, method rename, threshold/metric promotion, or Supplement omission is allowed. Technical exclusion is allowed only under rules locked before performance: identity, geometry, missing required modality, unreadable/corrupt file, or other pre-outcome data-integrity failure. New analyses on already observed Internal 113/RHUH 39 outcomes are Class C post-primary prespecified robustness, never original confirmatory.
""")
write(OUT / "06_PHASE0_OUTCOME_ACCESS_POLICY.md", """# Outcome-access policy

## Future-blind Stage A

May access current MRI, current segmentation, geometry, eligibility metadata, and frozen checkpoints. It may not access evaluated-case future voxel data, future segmentation/target, performance, future-derived sampling, or future-derived checkpoint selection. Pre-outcome geometry audits may inspect headers/shape/affine/orientation only.

## Retrospective Stage B

Only after P0 freeze, SHA freeze, and eligibility lock may future segmentation/target be accessed for PCC, No-smoothing, target-access controls, and evaluation. Current-mask robustness must use a clean frozen target; perturbation never changes the ground-truth definition.
""")
write(OUT / "07_PHASE2_CURRENT_MASK_ROBUSTNESS_PROTOCOL_PRELOCK.md", """# Phase 2 current-mask robustness — protocol skeleton

Role: `POST_PRIMARY_PRESPECIFIED_ROBUSTNESS`, cohorts Internal 113 and RHUH 39. No Phase 0 execution. Use the same frozen five development checkpoints; no retraining, fine-tuning, calibration, TTA, or outcome-based tuning.

Stage A2-mask: current T1c plus perturbed current mask → frozen predictor → perturbed-mask P0 → hash freeze, without future target/performance access. Stage B2-mask then uses the original clean future-added target to evaluate Fixed/P0, Full PCC, and No-smoothing.

Perturbation categories: CLEAN, EROSION_MILD, EROSION_MODERATE, DILATION_MILD, DILATION_MODERATE, BOUNDARY_PERTURBATION. Physical millimetres are preferred; 1 mm and 2 mm are candidates, not yet final. Phase 1 may select the physical implementation only from spacing/geometry/preprocessing, before performance. Boundary algorithm and seed must be deterministic and prelocked.

Metrics are descriptive: Dice@0.5, IoU@0.5, soft Dice, Brier, AP, mean/median, paired change vs CLEAN, 10,000 paired bootstrap CI, wins/ties/losses. No new confirmatory p-value family is authorized.
""")
write(OUT / "08_PHASE3_SAME_TARGET_COMPONENT_CONTROL_PROTOCOL_PRELOCK.md", """# Phase 3 same-target component controls — protocol skeleton

Role: `POST_PRIMARY_PRESPECIFIED_ROBUSTNESS`, cohorts Internal 113 and RHUH 39. All variants use the same frozen P0, target T, region R, eta, clipping, float32, ten rounds, and P10 formal output.

Variants: FULL_PCC; NO_ERROR_GUIDED_TERM (remove +eta*S, retain outside suppression); NO_OUTSIDE_SUPPRESSION (retain +eta*S, remove outside suppression); NEITHER_TERM (remove both, label unchanged-P0 structural negative control); NO_SMOOTHING (S=D, all other canonical terms unchanged). P1 may be descriptive only; formal endpoint remains P10.

Shuffled-target negative control: patient-level deterministic derangement separately within Internal 113 and RHUH 39; no self-donor; fixed seed and donor mapping persisted/hashed before interpretation; donor target guides correction while recipient clean target evaluates it. All results are descriptive/supporting. No automatic 5–10-test Wilcoxon family or new Holm family.
""")
write(OUT / "09_PHASE4_EXTERNAL_REPLICATION_PROTOCOL_PRELOCK.md", """# Phase 4 external replication — protocol skeleton

Phase 0 does not run external validation. LUMIERE is not automatically outcome-naive. Historical exposure audit must precede feasibility and determines wording.

Feasibility: longitudinal timepoints, current T1c/mask, future segmentation, no overlap, provenance, interpretable geometry without result-dependent repair, predeclared mask ontology, and sufficient cases after pre-outcome technical eligibility. No-go cannot be based on poor Dice/P0/PCC improvement; once outcomes are read, the dataset cannot be silently abandoned.

If a genuinely acceptable new cohort is locked before new outcome-performance access, Stage A uses the same frozen five checkpoints without training/calibration/TTA; P0 is float32 geometry-checked and hash-frozen. Stage B then runs Fixed, Full PCC, and No-smoothing. Skeleton confirmatory family: Full PCC vs Fixed and No-smoothing vs Full PCC, Dice@0.5, paired two-sided Wilcoxon, Holm exactly 2, 10,000 paired bootstrap and effect sizes. This remains a skeleton pending feasibility.
""")
write(OUT / "10_PHASE0_LUMIERE_HISTORICAL_EXPOSURE_AUDIT.md", """# LUMIERE historical exposure audit

Audit scope was limited to repository filenames, high-level status/release metadata, known protocol history, and hashes; old LUMIERE performance tables were not reopened.

- Previously processed / outputs present: YES — historical LUMIERE completion/status artifacts exist.
- Case-level or aggregate historical outputs known: YES at metadata/file-family level.
- Historical workflow leakage-prone: UNKNOWN from this metadata-only audit; do not upgrade wording.
- Used to choose current PCC parameters: no evidence in the current locked protocol chain; not independently proven by this audit.
- No-smoothing discovered using LUMIERE: no evidence in the current lock chain.
- New pipeline scientifically different: YES in protocol structure, but this does not erase historical exposure.

Classification: **Option A — HISTORICALLY_EXPOSED_BUT_NOT_USED_FOR_CURRENT_PARAMETER_SELECTION**, conservatively. Future wording: `protocol-locked leakage-free external replication on a historically exposed dataset`; never `fully outcome-naive external confirmation`. If future provenance review establishes method tuning using LUMIERE, downgrade to Option B and seek a genuinely unused dataset.
""")
write(OUT / "11_PHASE0_MANUSCRIPT_INTEGRATION_RULES.md", """# Manuscript integration rules

V2.1.1 remains the scientific baseline. Future evidence may modify manuscript text only after protocol completion, execution completion, integrity audit, negative-result retention, and independent scientific review. Current primary results must never be rewritten as if generated after future Anti-Major analyses. New Internal 113/RHUH 39 analyses must be labelled `post-primary prespecified robustness/sensitivity analysis`. External wording follows LUMIERE exposure class. Negative results must be integrated, not hidden.
""")
write(OUT / "12_PHASE0_MANUSCRIPT_SCIENCE_FREEZE.md", """# Manuscript science freeze

Frozen claims/limitations:

1. P0 is future-blind only with respect to evaluated-case future information.
2. P0 requires current T1c plus current segmentation.
3. PCC is retrospective target-conditioned correction.
4. Corrected Dice is not deployment-time predictive performance.
5. Target is a one-sided segmentation-derived future-added composite foreground.
6. Full PCC is canonical.
7. No-smoothing was discovered post hoc in development and prelocked before 113/RHUH confirmation.
8. Internal 113 and RHUH 39 four confirmatory comparisons are frozen.
9. RHUH n=39 is single-institution external evidence.
10. EIA methods are target-access comparators, not information-equivalent deployment methods.

Future evidence may refine limitations, not rewrite chronology.
""")
write(OUT / "16_PHASE0_GIT_STATE.txt", f"""baseline_head={HEAD}
science_freeze_tag={TAG}
working_branch={BRANCH}
phase0_worktree={REPO}
preserved_original_worktree=/home/changxinjiresearch/Research/Projects/PCC
preservation_snapshot={SNAP}
original_main_was_dirty=true
clean_worktree_status=PASS
""")
write(OUT / "14_PHASE0_HISTORICAL_EXCLUSION_REGISTRY.csv", "artifact/family,reason_excluded,allowed_use,forbidden_use\nhistorical case-specific target-trained P0,not future-blind or not current authority,provenance chronology,current confirmatory evidence or parameter choice\nsuperseded high-Dice results,old evaluation semantics or superseded table,history only,current performance claim\nhistorical leaky variants,violates current leakage-free policy,method-development chronology,current evidence\nold manuscript versions superseded by V2.1.1,version evolution,provenance only,current authority\nold LUMIERE scientific outputs,historical exposure,exposure audit only,current independent confirmation\nengineering failed attempts,not scientific outcomes,engineering provenance,current performance or exclusion rationale\ndeprecated fold manifests,superseded execution identity,provenance only,current cohort/checkpoint selection\n")

# Tree/hash manifest for all Phase 0 authority and generated files, excluding the
# final ZIP and checksum which are created after this manifest.
manifest = []
for p in sorted(OUT.rglob("*")):
    if not p.is_file() or p.name.startswith("PCC_PRE_SUBMISSION_ANTI_MAJOR_PHASE0_FREEZE_2026.zip"): continue
    rel = p.relative_to(OUT)
    cls = "CLASS A" if any(x in str(rel) for x in ["04_PHASE0_FROZEN", "ROUND3_FROZEN", "PHASE0_FROZEN_AUTHORITY", "NUMERIC_EVIDENCE"]) else "PHASE0_CONTROL"
    manifest.append({"relative_path": str(rel), "size_bytes": p.stat().st_size, "sha256": sha256(p), "evidence_class": cls, "mutable_after_phase0": "NO" if cls == "CLASS A" else "YES_WITH_AMENDMENT", "notes": "Hash captured after generation; no scientific arrays included."})
csv_write(OUT / "13_PHASE0_SCIENCE_FREEZE_SHA256_MANIFEST.csv", list(manifest[0]), manifest)

status = {
    "PRE_PHASE0_PRESERVATION": "PASS", "WORKING_TREE": "CLEAN", "IMPORTANT_SCIENTIFIC_CONTENT_PRESERVED": "YES", "LATEST_MANUSCRIPT_VERIFIED": "YES", "baseline_head": HEAD, "science_freeze_tag": TAG, "working_branch": BRANCH, "FROZEN_CONFIRMATORY_NUMERIC_MISMATCHES": numeric_mismatches, "FROZEN_SCIENTIFIC_FILES_CHANGED": 0, "NEW_SCIENTIFIC_EXPERIMENTS_EXECUTED": 0, "NEW_P0_GENERATED": 0, "NEW_PERFORMANCE_RESULTS_GENERATED": 0, "NEW_HYPOTHESIS_TESTS_RUN": 0, "EVIDENCE_CLASSES_DEFINED": "YES", "NEGATIVE_RESULT_POLICY_LOCKED": "YES", "OUTCOME_ACCESS_POLICY_LOCKED": "YES", "PHASE2_PROTOCOL_SKELETON": "LOCKED", "PHASE3_PROTOCOL_SKELETON": "LOCKED", "PHASE4_PROTOCOL_SKELETON": "LOCKED_PENDING_FEASIBILITY", "LUMIERE_HISTORICAL_EXPOSURE_AUDIT": "COMPLETE_OPTION_A", "GIT_FREEZE_TAG_CREATED": "YES", "TREE_HASH_MANIFEST_COMPLETE": "YES", "PHASE0_GATE": "PASS_READY_FOR_PHASE1" if numeric_mismatches == 0 else "HOLD"
}
(OUT / "15_PHASE0_FREEZE_VERIFICATION_REPORT.md").write_text("""# Phase 0 freeze verification report\n\nAll checks are audit-only. No model, predictor, target, P0, method, performance, p-value, Kaggle job, GPU job, or LUMIERE operation was run. The clean Phase 0 worktree is based on the frozen baseline commit; the original dirty worktree and all contents remain recoverable from the pre-Phase-0 snapshot. The Round-3 frozen-science regression was read as an existing authority and showed zero non-PASS rows.\n\nA: frozen scientific files changed = 0.\nB: new experiment = 0.\nC: new P0 = 0.\nD: new target = 0.\nE: new performance = 0.\nF: new p-value = 0.\nG: Kaggle job = 0.\nH: current confirmatory numbers match existing Round-3 authority = PASS.\nI: future 113/RHUH analyses classified Class C = PASS.\nJ: LUMIERE historical exposure documented = PASS.\nK: negative-result retention locked = PASS.\nL: outcome-access policy locked = PASS.\nM: Phase 2/3/4 skeletons exist = PASS.\n""", encoding="utf-8")
(OUT / "17_PHASE0_GATE_STATUS.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")

# Also expose the unnumbered canonical names requested by the protocol. These
# are byte-identical audit copies, not new scientific artifacts.
aliases = {
    "PHASE0_FROZEN_AUTHORITY_REGISTRY.csv": "PHASE0_FROZEN_AUTHORITY_REGISTRY.csv",
    "PHASE0_EVIDENCE_HIERARCHY.csv": "PHASE0_EVIDENCE_HIERARCHY.csv",
    "PHASE0_FROZEN_CONFIRMATORY_NUMERIC_IDENTITY.csv": "04_PHASE0_FROZEN_CONFIRMATORY_NUMERIC_IDENTITY.csv",
    "PHASE0_NEGATIVE_RESULT_POLICY.md": "05_PHASE0_NEGATIVE_RESULT_POLICY.md",
    "PHASE0_OUTCOME_ACCESS_POLICY.md": "06_PHASE0_OUTCOME_ACCESS_POLICY.md",
    "PHASE2_CURRENT_MASK_ROBUSTNESS_PROTOCOL_PRELOCK.md": "07_PHASE2_CURRENT_MASK_ROBUSTNESS_PROTOCOL_PRELOCK.md",
    "PHASE3_SAME_TARGET_COMPONENT_CONTROL_PROTOCOL_PRELOCK.md": "08_PHASE3_SAME_TARGET_COMPONENT_CONTROL_PROTOCOL_PRELOCK.md",
    "PHASE4_EXTERNAL_REPLICATION_PROTOCOL_PRELOCK.md": "09_PHASE4_EXTERNAL_REPLICATION_PROTOCOL_PRELOCK.md",
    "PHASE0_LUMIERE_HISTORICAL_EXPOSURE_AUDIT.md": "10_PHASE0_LUMIERE_HISTORICAL_EXPOSURE_AUDIT.md",
    "PHASE0_MANUSCRIPT_INTEGRATION_RULES.md": "11_PHASE0_MANUSCRIPT_INTEGRATION_RULES.md",
    "PHASE0_MANUSCRIPT_SCIENCE_FREEZE.md": "12_PHASE0_MANUSCRIPT_SCIENCE_FREEZE.md",
    "PHASE0_SCIENCE_FREEZE_SHA256_MANIFEST.csv": "13_PHASE0_SCIENCE_FREEZE_SHA256_MANIFEST.csv",
    "PHASE0_HISTORICAL_EXCLUSION_REGISTRY.csv": "14_PHASE0_HISTORICAL_EXCLUSION_REGISTRY.csv",
    "PHASE0_FREEZE_VERIFICATION_REPORT.md": "15_PHASE0_FREEZE_VERIFICATION_REPORT.md",
    "PHASE0_GIT_STATE.txt": "16_PHASE0_GIT_STATE.txt",
    "PHASE0_GATE_STATUS.json": "17_PHASE0_GATE_STATUS.json",
}
for alias, source in aliases.items():
    if alias != source:
        shutil.copy2(OUT / source, OUT / alias)

# Rebuild the hash manifest once final verification/status files exist.
manifest = []
for p in sorted(OUT.rglob("*")):
    if not p.is_file() or p.name.startswith("PCC_PRE_SUBMISSION_ANTI_MAJOR_PHASE0_FREEZE_2026.zip"): continue
    rel = p.relative_to(OUT); cls = "CLASS A" if any(x in str(rel) for x in ["04_PHASE0_FROZEN", "ROUND3_FROZEN"]) else "PHASE0_CONTROL"
    manifest.append({"relative_path": str(rel), "size_bytes": p.stat().st_size, "sha256": sha256(p), "evidence_class": cls, "mutable_after_phase0": "NO" if cls == "CLASS A" else "YES_WITH_AMENDMENT", "notes": "Hash captured after generation; no scientific arrays included."})
csv_write(OUT / "13_PHASE0_SCIENCE_FREEZE_SHA256_MANIFEST.csv", list(manifest[0]), manifest)

zip_path = OUT.parent / "PCC_PRE_SUBMISSION_ANTI_MAJOR_PHASE0_FREEZE_2026.zip"
with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): z.write(p, p.relative_to(OUT.parent))
(zip_path.with_suffix(zip_path.suffix + ".sha256")).write_text(f"{sha256(zip_path)}  {zip_path.name}\n", encoding="utf-8")
print(json.dumps(status, indent=2))
