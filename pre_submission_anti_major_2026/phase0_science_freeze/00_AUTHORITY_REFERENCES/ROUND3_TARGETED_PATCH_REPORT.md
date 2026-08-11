# PCC Scientific Reports Round 3 Targeted Patch V2.1.1

## Scope

This was a manuscript-only corrective patch. V2.1 remained frozen. No model was trained; no P0, target, method output, endpoint or confirmatory statistic was generated or changed; no cohort membership changed; LUMIERE was not run.

## Corrections

1. **Development threshold semantics.** The authority contained two distinct evaluation tokens: `crossfitted_threshold` and `fixed_0.5_and_probability`. The manuscript now reports the uniquely identified fixed-probability-threshold 0.5 Dice means: Fixed 0.228576 (display 0.229), Full PCC 0.275815 (0.276), and no-smoothing 0.326306 (0.326). The prior 0.216/0.326/0.385 values were correctly identified as cross-fitted-threshold Dice and are no longer labelled as threshold 0.5. Supplementary Table S4 now states the evaluation token and separates threshold-dependent Dice from soft Dice, Brier score and average precision.
2. **Supplementary Table S1.** The builder now uses the exact four-column schema and produces nine rows including the header. LibreOffice rendering confirms all three cohort columns are visible.
3. **Supplementary Table S7.** The frozen authority identified `NO_SMOOTHING_PCC` as the exact method token. S7 now contains 12 rows: `FULL_PCC` and `NO_SMOOTHING_PCC` for CLEAN, FP_25, MIXED, PARTIAL_25, PARTIAL_50 and SHIFT_3, all using frozen `dice_topk` values without recomputation.
4. **Footer fields.** Linked sections now share one footer with one `PAGE` field. Main and Supplement OOXML each contain one PAGE instruction; actual visible numbering is sequential.
5. **Figure legends.** Formal legends remain once after the references/declarations. The figure gallery no longer repeats them. Figures 4 and 5 share the final page, with no orphan legend or empty terminal page.
6. **Development selection transparency.** Frozen cohort-selection provenance establishes that the development cohort comprised the first 40 eligible patients under deterministic lexical ordering and a hard limit, not a random sample of all 155 eligible patients. The limitation and potential residual selection bias are now disclosed, and the cohort is explicitly separated from independent confirmation.
7. **Validator.** New checks cover evaluation-label consistency, S1 schema/render, S7 method/condition coverage and provenance, footer PAGE-field duplication, legend duplication, terminal orphan detection, LibreOffice PDF provenance, visible page numbering, and frozen-result regression.

## Frozen science

All 113-patient internal and 39-patient RHUH confirmatory values, P values, Holm-adjusted P values, confidence intervals, Cohen dz values and rank-biserial effects remain identical to V2.1 authorities. Table 2 and the descriptive comparator Table 3 retain exact SHA-256 identity. PCC, no-smoothing, P10, target and P0 definitions are unchanged.

`FROZEN_CONFIRMATORY_SCIENCE_CHANGED=0`

## Result

All targeted semantic, structural, rendering and numeric checks passed. This gate permits independent Round-3 recheck only; it does not assert submission readiness, acceptance or scientific proof.
